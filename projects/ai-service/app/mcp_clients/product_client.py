"""Product-grade MCP client used by the ticket agent to call the product MCP server."""

import asyncio
import json
import logging
from typing import Any, Protocol

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException


logger = logging.getLogger(__name__)


class McpToolCaller(Protocol):
    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call an MCP tool and return its parsed result dict."""
        ...


class ProductMcpClient:
    """Synchronous facade over the async streamable HTTP MCP client."""

    def __init__(
        self,
        base_url: str,
        auth_token: str | None,
        *,
        timeout_seconds: float = 30,
        retry_count: int = 2,
    ) -> None:
        self.base_url = base_url.strip().rstrip("/")
        self.auth_token = auth_token
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self._tools_cache: list[str] | None = None

    def _headers(self) -> dict[str, str]:
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def _build_http_client(self) -> httpx2.AsyncClient:
        return create_mcp_http_client(
            headers=self._headers(),
            timeout=httpx2.Timeout(self.timeout_seconds),
        )

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.retry_count + 1):
            try:
                return asyncio.run(
                    self._call_tool_async(tool_name, arguments)
                )
            except AppException:
                raise
            except Exception as exc:
                last_error = exc
                if isinstance(exc, (TimeoutError, httpx2.TimeoutException)):
                    raise AppException(
                        code="MCP_SERVER_TIMEOUT",
                        message="AI 工具服务响应超时，请稍后再试。",
                        status_code=504,
                    ) from exc
                logger.warning(
                    "product_mcp_client_retry tool=%s attempt=%s error_type=%s",
                    tool_name,
                    attempt + 1,
                    type(exc).__name__,
                )
        raise AppException(
            code="MCP_SERVER_UNREACHABLE",
            message="AI 工具服务暂时不可用，请稍后再试。",
            status_code=502,
        ) from last_error

    async def _call_tool_async(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        http_client = self._build_http_client()
        async with http_client:
            async with streamable_http_client(
                self.base_url,
                http_client=http_client,
            ) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    return self._parse_result(result)

    def _parse_result(self, result: Any) -> dict[str, Any]:
        text_parts: list[str] = []
        for block in result.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
        if not text_parts:
            raise AppException(
                code="MCP_RESULT_INVALID",
                message="AI 工具服务返回了无法解析的结果。",
                status_code=502,
            )
        raw_text = "\n".join(text_parts)
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise AppException(
                code="MCP_RESULT_INVALID",
                message="AI 工具服务返回了无法解析的结果。",
                status_code=502,
            ) from exc
        if not isinstance(parsed, dict):
            raise AppException(
                code="MCP_RESULT_INVALID",
                message="AI 工具服务返回了无法解析的结果。",
                status_code=502,
            )
        return parsed

    def list_tools(self) -> list[str]:
        if self._tools_cache is not None:
            return self._tools_cache
        tools = asyncio.run(self._list_tools_async())
        self._tools_cache = tools
        return tools

    async def _list_tools_async(self) -> list[str]:
        http_client = self._build_http_client()
        async with http_client:
            async with streamable_http_client(
                self.base_url,
                http_client=http_client,
            ) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    return [tool.name for tool in listed.tools]


def create_product_mcp_client(
    settings: Settings | None = None,
) -> ProductMcpClient:
    resolved_settings = settings or get_settings()
    return ProductMcpClient(
        base_url=resolved_settings.resolved_mcp_product_base_url,
        auth_token=resolved_settings.resolved_mcp_product_auth_token,
        timeout_seconds=resolved_settings.mcp_product_timeout_seconds,
        retry_count=resolved_settings.mcp_product_retry_count,
    )
