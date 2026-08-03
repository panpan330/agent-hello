from pathlib import Path

import pytest

from app.agents.eval_suite import AgentEvalRunReport, AgentEvalSuiteReport
from app.evaluation.eval_platform import (
    EvalDatasetRegistry,
    EvalRunContext,
    compare_eval_run_snapshots,
    find_eval_dataset_manifest,
    format_eval_dataset_registry,
    format_eval_regression_report,
    build_agent_eval_run_snapshot,
    load_eval_dataset_registry,
)


REGISTRY_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "evaluation" / "datasets.json"
)


def test_load_eval_dataset_registry_reads_current_local_manifests() -> None:
    registry = load_eval_dataset_registry(REGISTRY_PATH)

    assert registry.registry_version == "stage10-v1"
    assert [dataset.name for dataset in registry.datasets] == [
        "agent_eval",
        "rag_retrieval_eval",
        "rag_answer_eval",
    ]
    agent_dataset = find_eval_dataset_manifest(
        registry,
        name="agent_eval",
        version="stage6-v1",
    )
    assert agent_dataset.cases_path == "data/agent_eval/agent_cases.json"
    assert agent_dataset.frozen is True


def test_format_eval_dataset_registry_is_readable() -> None:
    registry = load_eval_dataset_registry(REGISTRY_PATH)

    lines = format_eval_dataset_registry(registry)

    assert lines[0] == "Evaluation dataset registry"
    assert "registry_version: stage10-v1" in lines
    assert any("agent_eval:stage6-v1" in line for line in lines)
    assert any("baseline=agent_eval_stage6_v1_baseline" in line for line in lines)


def test_eval_dataset_registry_rejects_duplicate_name_and_version() -> None:
    with pytest.raises(ValueError, match="duplicate name/version"):
        EvalDatasetRegistry.model_validate(
            {
                "registry_version": "test",
                "datasets": [
                    {
                        "name": "agent_eval",
                        "version": "v1",
                        "task_type": "agent",
                        "cases_path": "a.json",
                    },
                    {
                        "name": "agent_eval",
                        "version": "v1",
                        "task_type": "agent",
                        "cases_path": "b.json",
                    },
                ],
            }
        )


def test_build_agent_eval_run_snapshot_turns_suite_report_into_platform_snapshot() -> None:
    report = _agent_report(
        passed=True,
        intent_failed=0,
        route_failed=0,
    )
    context = _context(run_id="candidate-001", candidate_version="prompt-v2")

    snapshot = build_agent_eval_run_snapshot(report, context=context)

    assert snapshot.context.run_id == "candidate-001"
    assert snapshot.evaluated_check_count == 20
    assert snapshot.passed_check_count == 20
    assert snapshot.failed_check_count == 0
    assert snapshot.passed is True
    assert snapshot.metric_map()["suite_pass_rate"].value == 1.0
    assert snapshot.metric_map()["check_pass_rate"].value == 1.0
    assert snapshot.metric_map()["failed_checks"].direction == "lower_is_better"


def test_compare_eval_run_snapshots_reports_no_regression_when_candidate_is_equal() -> None:
    baseline = build_agent_eval_run_snapshot(
        _agent_report(passed=True, intent_failed=0, route_failed=0),
        context=_context(run_id="baseline-001", candidate_version="prompt-v1"),
    )
    candidate = build_agent_eval_run_snapshot(
        _agent_report(passed=True, intent_failed=0, route_failed=0),
        context=_context(run_id="candidate-001", candidate_version="prompt-v2"),
    )

    regression = compare_eval_run_snapshots(baseline, candidate)

    assert regression.regressed is False
    assert regression.blocking_reasons == []
    assert all(not metric.regressed for metric in regression.metric_comparisons)


def test_compare_eval_run_snapshots_reports_metric_and_status_regression() -> None:
    baseline = build_agent_eval_run_snapshot(
        _agent_report(passed=True, intent_failed=0, route_failed=0),
        context=_context(run_id="baseline-001", candidate_version="prompt-v1"),
    )
    candidate = build_agent_eval_run_snapshot(
        _agent_report(passed=False, intent_failed=2, route_failed=0),
        context=_context(run_id="candidate-001", candidate_version="prompt-v2"),
    )

    regression = compare_eval_run_snapshots(baseline, candidate)
    lines = format_eval_regression_report(regression)

    assert regression.regressed is True
    assert "metric_regressed:check_pass_rate" in regression.blocking_reasons
    assert "metric_regressed:failed_checks" in regression.blocking_reasons
    assert "overall_status_regressed" in regression.blocking_reasons
    assert "failed_check_count_increased" in regression.blocking_reasons
    assert "regressed: true" in lines


def test_compare_eval_run_snapshots_rejects_different_dataset_versions() -> None:
    baseline = build_agent_eval_run_snapshot(
        _agent_report(passed=True, intent_failed=0, route_failed=0),
        context=_context(
            run_id="baseline-001",
            candidate_version="prompt-v1",
            dataset_version="stage6-v1",
        ),
    )
    candidate = build_agent_eval_run_snapshot(
        _agent_report(passed=True, intent_failed=0, route_failed=0),
        context=_context(
            run_id="candidate-001",
            candidate_version="prompt-v2",
            dataset_version="stage6-v2",
        ),
    )

    with pytest.raises(ValueError, match="different dataset versions"):
        compare_eval_run_snapshots(baseline, candidate)


def _context(
    *,
    run_id: str,
    candidate_version: str,
    dataset_version: str = "stage6-v1",
) -> EvalRunContext:
    return EvalRunContext(
        run_id=run_id,
        dataset_name="agent_eval",
        dataset_version=dataset_version,
        candidate_version=candidate_version,
        model_name="fake",
        prompt_version=candidate_version,
        code_version="local-test",
    )


def _agent_report(
    *,
    passed: bool,
    intent_failed: int,
    route_failed: int,
) -> AgentEvalRunReport:
    suite_reports = [
        _suite_report(
            name="intent",
            case_count=10,
            failed_case_count=intent_failed,
        ),
        _suite_report(
            name="route",
            case_count=10,
            failed_case_count=route_failed,
        ),
    ]
    failed_suite_count = sum(1 for suite in suite_reports if not suite.passed)
    return AgentEvalRunReport(
        cases_path="data/agent_eval/agent_cases.json",
        selected_case_count=10,
        case_filter="all",
        suite_count=2,
        passed_suite_count=2 - failed_suite_count,
        failed_suite_count=failed_suite_count,
        passed=passed,
        suite_reports=suite_reports,
    )


def _suite_report(
    *,
    name: str,
    case_count: int,
    failed_case_count: int,
) -> AgentEvalSuiteReport:
    return AgentEvalSuiteReport(
        name=name,
        title=f"{name} suite",
        case_count=case_count,
        failed_case_count=failed_case_count,
        passed=failed_case_count == 0,
        summary_lines=[],
        bad_case_lines=[],
    )
