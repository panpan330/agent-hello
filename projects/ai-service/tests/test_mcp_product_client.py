import pytest

from app.core.config import Settings
from app.core.exceptions import AppException
from app.mcp_clients.product_client import (
    McpToolCaller,
    ProductMcpClient,
    create_product_mcp_client,
)
from tests.tool_fakes import FakeMcpToolCaller


def test_create_product_mcp_client_from_settings() -> None:
    client = create_product_mcp_client(
        Settings(
            _env_file=None,
            mcp_product_base_url="http://127.0.0.1:9100/mcp",
            mcp_product_auth_token="token",
            mcp_product_timeout_seconds=5,
            mcp_product_retry_count=1,
        )
    )
    assert isinstance(client, ProductMcpClient)
    assert client.base_url == "http://127.0.0.1:9100/mcp"
    assert client.auth_token == "token"
    assert client.timeout_seconds == 5
    assert client.retry_count == 1


def test_mcp_tool_caller_protocol_supports_fake() -> None:
    fake = FakeMcpToolCaller(responses={"query_order": {"ok": True}})
    caller: McpToolCaller = fake
    assert caller.call_tool("query_order", {"order_id": "A1001"}) == {"ok": True}
    assert fake.calls == [("query_order", {"order_id": "A1001"})]
