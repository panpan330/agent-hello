from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.trace import TRACE_ID_HEADER
from app.routers.evaluation import get_evaluation_registry_path


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
