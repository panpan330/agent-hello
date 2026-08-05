import json

import pytest
from mcp import Client

from app.core.config import Settings
from app.core.exceptions import AppException
from app.mcp_servers.product_server import (
    BearerAuthMiddleware,
    create_product_mcp_app,
    create_product_mcp_server,
)
from tests.tool_fakes import FakeTicketCreator, make_created_ticket


def _settings(token: str | None = "test-token") -> Settings:
    return Settings(
        _env_file=None,
        mcp_product_auth_token=token,
        tool_confirmation_backend="memory",
    )


def test_product_server_registers_only_business_tools() -> None:
    async def run() -> None:
        server = create_product_mcp_server(_settings())
        async with Client(server) as client:
            tools = await client.list_tools()
        names = [tool.name for tool in tools.tools]
        assert names == ["query_order", "create_ticket"]

    import asyncio

    asyncio.run(run())


def test_product_create_ticket_accepts_16_hex_confirmation_id() -> None:
    server = create_product_mcp_server(_settings())

    async def run() -> None:
        async with Client(server) as client:
            tools = await client.list_tools()
        tool = next(t for t in tools.tools if t.name == "create_ticket")
        confirmation_schema = tool.input_schema["properties"]["confirmation_id"]
        assert confirmation_schema["pattern"] == r"^[a-f0-9]{16,32}$"
        assert "user_confirmed" in tool.input_schema["properties"]

    import asyncio

    asyncio.run(run())


def test_bearer_auth_middleware_rejects_missing_token() -> None:
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    async def ok_endpoint(request: object) -> PlainTextResponse:
        return PlainTextResponse("ok")

    inner = Starlette(routes=[Route("/mcp", ok_endpoint, methods=["GET", "POST"])])
    wrapped = BearerAuthMiddleware(inner, token="test-token")

    from starlette.testclient import TestClient

    client = TestClient(wrapped)
    response = client.post("/mcp", json={})
    assert response.status_code == 401


def test_bearer_auth_middleware_rejects_wrong_token() -> None:
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    async def ok_endpoint(request: object) -> PlainTextResponse:
        return PlainTextResponse("ok")

    inner = Starlette(routes=[Route("/mcp", ok_endpoint, methods=["GET", "POST"])])
    wrapped = BearerAuthMiddleware(inner, token="test-token")
    from starlette.testclient import TestClient

    client = TestClient(wrapped)
    response = client.post(
        "/mcp",
        json={},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401


def test_bearer_auth_middleware_accepts_correct_token() -> None:
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    async def ok_endpoint(request: object) -> PlainTextResponse:
        return PlainTextResponse("ok")

    inner = Starlette(routes=[Route("/mcp", ok_endpoint, methods=["GET", "POST"])])
    wrapped = BearerAuthMiddleware(inner, token="test-token")
    from starlette.testclient import TestClient

    client = TestClient(wrapped)
    response = client.post(
        "/mcp",
        json={},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200


def test_product_app_uses_bearer_middleware() -> None:
    app = create_product_mcp_app(_settings(token="test-token"))
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1, "params": {}},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code in (200, 202)


def test_product_app_allows_local_origin() -> None:
    app = create_product_mcp_app(_settings(token="test-token"))
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1, "params": {}},
        headers={
            "Authorization": "Bearer test-token",
            "Origin": "http://localhost:5173",
        },
    )
    assert response.status_code in (200, 202)


def test_product_app_rejects_non_local_origin() -> None:
    app = create_product_mcp_app(_settings(token="test-token"))
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1, "params": {}},
        headers={
            "Authorization": "Bearer test-token",
            "Origin": "https://evil.example.com",
        },
    )
    assert response.status_code == 403


def test_product_create_ticket_confirmation_unavailable_mapped_to_ok_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from redis.exceptions import ConnectionError as RedisConnectionError

    from app.mcp_servers import product_server

    class _FailingConfirmationStore:
        def require_confirmed(self, confirmation_id: str, *, actor_id: str) -> None:
            raise RedisConnectionError("redis connection refused")

    monkeypatch.setattr(
        product_server,
        "create_tool_confirmation_store",
        lambda: _FailingConfirmationStore(),
    )
    result = product_server._product_create_ticket(
        requester_id="user-1",
        title="测试工单",
        description="测试描述",
        category="refund",
        confirmation_id="a" * 32,
        user_confirmed=True,
    )
    assert result["ok"] is False
    assert result["error_code"] == "TOOL_CONFIRMATION_UNAVAILABLE"
    assert result["ticket"] is None
