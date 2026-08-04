from pathlib import Path

from fastapi import APIRouter, Depends

from app.agents.bad_case_analysis import analyze_agent_eval_bad_cases
from app.agents.eval_suite import AgentEvalRunReport, run_agent_eval_suites
from app.core.config import PROJECT_ROOT
from app.core.exceptions import AppException
from app.core.trace import get_trace_id
from app.evaluation.bad_case_registry import (
    BadCaseRecord,
    BadCaseRegistry,
    build_bad_case_record_from_analysis_item,
    build_bad_case_registry_summary,
)
from app.evaluation.eval_platform import (
    EvalDatasetManifest,
    EvalRunContext,
    EvalRunSnapshot,
    build_agent_eval_run_snapshot,
    find_eval_dataset_manifest,
    load_eval_dataset_registry,
)
from app.schemas.evaluation import (
    BadCaseItemView,
    BadCaseSummaryView,
    EvaluationDatasetView,
    EvaluationMetricView,
    EvaluationOverviewResponse,
    EvaluationRunOverview,
    EvaluationSuiteView,
)


router = APIRouter(prefix="/api/ai/evaluation", tags=["evaluation"])
EVALUATION_REGISTRY_PATH = PROJECT_ROOT / "data" / "evaluation" / "datasets.json"
BAD_CASE_REGISTRY_PATH = PROJECT_ROOT / "data" / "evaluation" / "bad_cases.json"


def get_evaluation_registry_path() -> Path:
    return EVALUATION_REGISTRY_PATH


def get_bad_case_registry_path() -> Path:
    return BAD_CASE_REGISTRY_PATH


@router.get("/overview", response_model=EvaluationOverviewResponse)
def evaluation_overview(
    registry_path: Path = Depends(get_evaluation_registry_path),
    bad_case_registry_path: Path = Depends(get_bad_case_registry_path),
) -> EvaluationOverviewResponse:
    try:
        registry = load_eval_dataset_registry(registry_path)
        agent_dataset = find_eval_dataset_manifest(
            registry,
            name="agent_eval",
            version="stage6-v1",
        )
        run_report = run_agent_eval_suites(PROJECT_ROOT / agent_dataset.cases_path)
        snapshot = build_agent_eval_run_snapshot(
            run_report,
            context=EvalRunContext(
                run_id="local-agent-eval-latest",
                dataset_name=agent_dataset.name,
                dataset_version=agent_dataset.version,
                candidate_version="local-working-tree",
                baseline_run_id=agent_dataset.baseline_run_id,
                model_name="fake_or_rule_based",
                prompt_version="local",
                code_version="local-working-tree",
            ),
        )
        bad_cases, generated_from_latest_run = _load_or_generate_bad_cases(
            bad_case_registry_path,
            run_report=run_report,
            dataset=agent_dataset,
        )
    except FileNotFoundError as exc:
        raise AppException(
            code="EVALUATION_DATA_NOT_FOUND",
            message="本地评估数据文件不存在，无法生成评估看板。",
            status_code=500,
        ) from exc
    except ValueError as exc:
        raise AppException(
            code="EVALUATION_DATA_INVALID",
            message=str(exc),
            status_code=500,
        ) from exc

    bad_case_registry = BadCaseRegistry(
        schema_version="stage11.bad_case_registry.view",
        records=bad_cases,
    )
    bad_case_summary = build_bad_case_registry_summary(bad_case_registry)

    return EvaluationOverviewResponse(
        registry_version=registry.registry_version,
        datasets=[_dataset_view(dataset) for dataset in registry.datasets],
        latest_run=_run_overview(snapshot, run_report),
        bad_case_summary=BadCaseSummaryView.model_validate(
            bad_case_summary.model_dump()
        ),
        bad_cases=[_bad_case_view(record) for record in bad_cases],
        generated_from_latest_run=generated_from_latest_run,
        trace_id=get_trace_id(),
    )


def _load_or_generate_bad_cases(
    bad_case_registry_path: Path,
    *,
    run_report: AgentEvalRunReport,
    dataset: EvalDatasetManifest,
) -> tuple[list[BadCaseRecord], bool]:
    bad_case_registry = BadCaseRegistry.model_validate_json(
        bad_case_registry_path.read_text(encoding="utf-8")
    )
    if bad_case_registry.records:
        return bad_case_registry.records, False

    analysis_report = analyze_agent_eval_bad_cases(run_report)
    generated_records = [
        build_bad_case_record_from_analysis_item(
            item,
            discovered_run_id="local-agent-eval-latest",
            dataset_name=dataset.name,
            dataset_version=dataset.version,
        )
        for item in analysis_report.items
    ]
    return generated_records, True


def _dataset_view(dataset: EvalDatasetManifest) -> EvaluationDatasetView:
    return EvaluationDatasetView(
        name=dataset.name,
        version=dataset.version,
        task_type=dataset.task_type,
        description=dataset.description,
        frozen=dataset.frozen,
        baseline_run_id=dataset.baseline_run_id,
        tags=dataset.tags,
    )


def _run_overview(
    snapshot: EvalRunSnapshot,
    run_report: AgentEvalRunReport,
) -> EvaluationRunOverview:
    return EvaluationRunOverview(
        run_id=snapshot.context.run_id,
        dataset_name=snapshot.context.dataset_name,
        dataset_version=snapshot.context.dataset_version,
        candidate_version=snapshot.context.candidate_version,
        model_name=snapshot.context.model_name,
        selected_case_count=run_report.selected_case_count,
        evaluated_check_count=snapshot.evaluated_check_count,
        passed_check_count=snapshot.passed_check_count,
        failed_check_count=snapshot.failed_check_count,
        passed=snapshot.passed,
        metrics=[
            EvaluationMetricView(
                name=metric.name,
                value=metric.value,
                direction=metric.direction,
                display_value=_format_metric_value(metric.name, metric.value),
            )
            for metric in snapshot.metrics
        ],
        suites=[
            EvaluationSuiteView(
                name=suite.name,
                title=suite.title,
                case_count=suite.case_count,
                failed_case_count=suite.failed_case_count,
                passed=suite.passed,
            )
            for suite in run_report.suite_reports
        ],
    )


def _bad_case_view(record: BadCaseRecord) -> BadCaseItemView:
    return BadCaseItemView(
        id=record.id,
        title=record.title,
        source=record.source,
        task_type=record.task_type,
        severity=record.severity,
        status=record.status,
        failure_layer=record.failure_layer,
        failure_category=record.failure_category,
        expected_behavior=record.expected_behavior,
        actual_behavior=record.actual_behavior,
        root_cause=record.root_cause,
        recommended_action=record.recommended_action,
        regression_action=record.regression_action,
        evidence_summary=record.evidence_summary,
        tags=record.tags,
    )


def _format_metric_value(name: str, value: float) -> str:
    if name.endswith("_rate"):
        return f"{value * 100:.1f}%"
    if value.is_integer():
        return str(int(value))
    return f"{value:.4f}"
