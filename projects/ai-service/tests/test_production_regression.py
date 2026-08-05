from datetime import datetime, timezone

from app.evaluation.bad_case_registry import BadCaseRecord, ProductionRegressionSpec
from app.evaluation.production_regression import run_production_bad_case_regression
from app.evaluation.production_regression_history import (
    append_production_regression_run,
    load_latest_production_regression_run,
)


def _record(
    record_id: str,
    *,
    spec: ProductionRegressionSpec | None,
) -> BadCaseRecord:
    return BadCaseRecord(
        id=record_id,
        title=f"Production feedback {record_id}",
        source="production",
        task_type="agent",
        severity="medium",
        status="regression_added",
        failure_layer="agent_decision",
        failure_category="incorrect decision",
        expected_behavior="Choose the expected handling path.",
        actual_behavior="The previous answer chose an incorrect path.",
        recommended_action="Adjust the decision policy.",
        regression_action="Run the supervisor-approved regression assertion.",
        evidence_summary="feedback_id=1",
        production_regression=spec,
    )


def test_production_regression_reports_pass_failure_not_ready_and_execution_error() -> None:
    records = [
        _record(
            "bad-intent-pass",
            spec=ProductionRegressionSpec(
                message="Where is order A1001?",
                assertion="intent",
                expected_intent="order_query",
            ),
        ),
        _record(
            "bad-citation-fail",
            spec=ProductionRegressionSpec(
                message="What is the refund policy?",
                assertion="citation_present",
            ),
        ),
        _record("bad-not-ready", spec=None),
        _record(
            "bad-run-error",
            spec=ProductionRegressionSpec(
                message="raise error",
                assertion="ticket_confirmation_required",
            ),
        ),
    ]

    def runner(message: str) -> dict[str, object]:
        if message == "raise error":
            raise RuntimeError("test runner failed")
        if message == "Where is order A1001?":
            return {"intent": "order_query"}
        return {"rag_citations": []}

    run = run_production_bad_case_regression(records, agent_runner=runner)

    assert run.total_case_count == 4
    assert run.passed_case_count == 1
    assert run.failed_case_count == 1
    assert run.not_ready_case_count == 1
    assert run.error_case_count == 1
    assert run.passed is False
    assert [result.outcome for result in run.results] == ["passed", "failed", "not_ready", "error"]


def test_production_regression_history_persists_latest_run(tmp_path) -> None:
    fixed_now = lambda: datetime(2026, 8, 5, tzinfo=timezone.utc)
    run = run_production_bad_case_regression(
        [
            _record(
                "bad-intent-pass",
                spec=ProductionRegressionSpec(
                    message="Where is order A1001?",
                    assertion="intent",
                    expected_intent="order_query",
                ),
            )
        ],
        agent_runner=lambda _message: {"intent": "order_query"},
        now=fixed_now,
    )
    history_path = tmp_path / "production_regression_runs.json"

    append_production_regression_run(history_path, run)
    latest = load_latest_production_regression_run(history_path)

    assert latest is not None
    assert latest.run_id == run.run_id
    assert latest.passed is True
