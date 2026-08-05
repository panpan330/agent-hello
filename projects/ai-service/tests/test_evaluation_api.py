from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.trace import TRACE_ID_HEADER
from app.routers import evaluation as evaluation_router
from app.routers.evaluation import get_evaluation_actor, get_evaluation_registry_path
from app.routers.evaluation import get_bad_case_registry_path, get_production_regression_history_path
from app.routers.evaluation import _load_or_generate_bad_cases
from app.evaluation.eval_platform import EvalDatasetManifest
from app.agents.eval_suite import run_agent_eval_suites
from app.evaluation.production_regression import run_production_bad_case_regression
from app.services.console_agent_service import ConsoleAgentActor


def test_evaluation_overview_returns_local_registry_run_and_bad_cases(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/ai/evaluation/overview",
        headers={TRACE_ID_HEADER: "trace-eval-overview"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["registry_version"] == "stage10-v1"
    assert len(data["datasets"]) == 3
    assert data["latest_run"]["run_id"] == "local-agent-eval-latest"
    assert data["latest_run"]["dataset_name"] == "agent_eval"
    assert data["latest_run"]["selected_case_count"] > 0
    assert len(data["latest_run"]["suites"]) == 4
    assert data["bad_case_summary"]["record_count"] == len(data["bad_cases"])
    assert data["trace_id"] == "trace-eval-overview"


def test_evaluation_overview_reports_missing_registry(
    app: FastAPI,
    client: TestClient,
    tmp_path: Path,
) -> None:
    app.dependency_overrides[get_evaluation_registry_path] = lambda: tmp_path / "missing.json"

    response = client.get(
        "/api/ai/evaluation/overview",
        headers={TRACE_ID_HEADER: "trace-eval-missing"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "code": "EVALUATION_DATA_NOT_FOUND",
        "message": "本地评估数据文件不存在，无法生成评估看板。",
        "trace_id": "trace-eval-missing",
    }


def test_production_bad_cases_merge_with_generated_local_evaluation_cases(tmp_path: Path) -> None:
    registry_path = tmp_path / "bad_cases.json"
    registry_path.write_text(
        """
        {
          "schema_version": "stage10.bad_case_registry.v1",
          "records": [{
            "id": "bad_production_feedback_stage11_feedback_1_agent_decision",
            "title": "Production feedback",
            "source": "production",
            "task_type": "agent",
            "severity": "medium",
            "status": "regression_added",
            "source_case_id": "feedback_1",
            "failure_layer": "agent_decision",
            "failure_category": "decision",
            "expected_behavior": "Escalate correctly.",
            "actual_behavior": "Did not escalate.",
            "recommended_action": "Adjust policy.",
            "regression_action": "Add a test.",
            "evidence_summary": "feedback_id=1"
          }]
        }
        """,
        encoding="utf-8",
    )
    cases_path = Path(__file__).parents[1] / "data" / "agent_eval" / "agent_cases.json"
    report = run_agent_eval_suites(cases_path)
    dataset = EvalDatasetManifest(
        name="agent_eval",
        version="stage6-v1",
        task_type="agent",
        description="test",
        frozen=True,
        cases_path="data/agent_eval/agent_cases.json",
    )

    records, generated = _load_or_generate_bad_cases(registry_path, run_report=report, dataset=dataset)

    assert generated is True
    assert any(record.source == "production" for record in records)


def test_supervisor_can_run_and_persist_formal_production_regression(
    app: FastAPI,
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    registry_path = tmp_path / "bad_cases.json"
    registry_path.write_text(
        """
        {
          "schema_version": "stage10.bad_case_registry.v1",
          "records": [{
            "id": "bad_production_feedback_stage11_feedback_1_agent_decision",
            "title": "Production feedback",
            "source": "production",
            "task_type": "agent",
            "severity": "medium",
            "status": "regression_added",
            "source_case_id": "feedback_1",
            "failure_layer": "agent_decision",
            "failure_category": "decision",
            "expected_behavior": "Route order questions correctly.",
            "actual_behavior": "The route was incorrect.",
            "recommended_action": "Adjust the decision policy.",
            "regression_action": "Run an intent regression.",
            "evidence_summary": "feedback_id=1",
            "production_regression": {
              "message": "Where is order A1001?",
              "assertion": "intent",
              "expected_intent": "order_query"
            }
          }]
        }
        """,
        encoding="utf-8",
    )
    history_path = tmp_path / "production_regression_runs.json"
    app.dependency_overrides[get_evaluation_actor] = lambda: ConsoleAgentActor(
        user_id="SUP1001", tenant_id="default", roles=("supervisor",)
    )
    app.dependency_overrides[get_bad_case_registry_path] = lambda: registry_path
    app.dependency_overrides[get_production_regression_history_path] = lambda: history_path
    monkeypatch.setattr(
        evaluation_router,
        "run_production_bad_case_regression",
        lambda records: run_production_bad_case_regression(
            records,
            agent_runner=lambda _message: {"intent": "order_query"},
        ),
    )

    response = client.post(
        "/api/ai/evaluation/runs/production-regression",
        headers={TRACE_ID_HEADER: "trace-production-regression"},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is True
    assert response.json()["results"][0]["outcome"] == "passed"
    assert history_path.exists()
