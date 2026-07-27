from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "java-mock-service",
    }


def test_ready_returns_ready_with_required_checks(client: TestClient) -> None:
    response = client.get("/ready")
    data = response.json()

    assert response.status_code == 200
    assert data == {
        "status": "ready",
        "service": "java-mock-service",
        "ready": True,
        "checks": [
            {
                "name": "in_memory_order_store",
                "status": "ok",
                "required": True,
                "message": "In-memory order store is available.",
            },
            {
                "name": "in_memory_ticket_store",
                "status": "ok",
                "required": True,
                "message": "In-memory ticket store is available.",
            },
        ],
    }
