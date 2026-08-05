"""Product-grade MCP server: streamable HTTP, Bearer auth, business tools only.

Run as a standalone process:

    uv run python -m app.mcp_servers.product_server
"""

import logging
from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.mcp_servers import order_tool
from app.schemas.ticket import CreateTicketArgs
from app.services.java_ticket_client import JavaTicketClient
from app.tools.idempotency import run_idempotent_tool
from app.tools.tool_confirmation import create_tool_confirmation_store
from app.tools.tool_registry import authorize_tool_call


logger = logging.getLogger(__name__)

CREATE_TICKET_TOOL_NAME = "create_ticket"
QUERY_ORDER_TOOL_NAME = "query_order"

# Confirmation ids come from the agent (16-hex sha256 prefix) or from the
# confirmation store (32-hex uuid), so accept both.
CONFIRMATION_ID_PATTERN = r"^[a-f0-9]{16,32}$"


def _create_ticket_response(
    *,
    ok: bool,
    confirmation_id: str,
    error_code: str | None,
    message: str,
    ticket: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "allowed": True,
        "confirmation_checked": True,
        "confirmation_id": confirmation_id,
        "error_code": error_code,
        "message": message,
        "ticket": ticket,
    }


def _safe_created_ticket(ticket: Any) -> dict[str, Any]:
    return ticket.model_dump(mode="json")


def _product_create_ticket(
    requester_id: str,
    title: str,
    description: str,
    category: str,
    confirmation_id: str,
    priority: str = "normal",
    related_order_id: str | None = None,
    user_confirmed: bool = False,
) -> dict[str, Any]:
    """Create a ticket with confirmation + authorization + idempotency guards."""
    if not user_confirmed:
        return _create_ticket_response(
            ok=False,
            confirmation_id=confirmation_id.strip(),
            error_code="TOOL_CONFIRMATION_REQUIRED",
            message="该工具需要用户确认后才能执行。",
            ticket=None,
        )

    try:
        arguments = CreateTicketArgs(
            requester_id=requester_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            related_order_id=related_order_id,
        )
    except Exception as exc:  # pydantic.ValidationError
        from pydantic import ValidationError

        if not isinstance(exc, ValidationError):
            raise
        return _create_ticket_response(
            ok=False,
            confirmation_id=confirmation_id,
            error_code="INVALID_TOOL_ARGUMENTS",
            message="工单参数不正确，请确认后重新提交。",
            ticket=None,
        )

    store = create_tool_confirmation_store()
    try:
        store.require_confirmed(confirmation_id, actor_id=requester_id)
    except AppException as exc:
        return _create_ticket_response(
            ok=False,
            confirmation_id=confirmation_id,
            error_code=exc.code,
            message=exc.message,
            ticket=None,
        )

    try:
        authorize_tool_call(CREATE_TICKET_TOOL_NAME, user_confirmed=True)
        ticket_creator = JavaTicketClient.from_settings(get_settings())
        ticket = run_idempotent_tool(
            CREATE_TICKET_TOOL_NAME,
            arguments,
            confirmation_id,
            lambda: ticket_creator.create_ticket(
                arguments,
                idempotency_key=confirmation_id,
            ),
        )
    except AppException as exc:
        return _create_ticket_response(
            ok=False,
            confirmation_id=confirmation_id,
            error_code=exc.code,
            message=exc.message,
            ticket=None,
        )
    except Exception as exc:
        logger.warning(
            "product_mcp_create_ticket_failed error_type=%s",
            type(exc).__name__,
            exc_info=True,
        )
        return _create_ticket_response(
            ok=False,
            confirmation_id=confirmation_id,
            error_code="TICKET_CREATION_TOOL_ERROR",
            message="创建工单工具暂时不可用，请稍后重试或联系人工处理。",
            ticket=None,
        )

    logger.info(
        "product_mcp_create_ticket_succeeded confirmation_id=%s ticket_id=%s",
        confirmation_id,
        ticket.ticket_id,
    )
    return _create_ticket_response(
        ok=True,
        confirmation_id=confirmation_id,
        error_code=None,
        message="工单创建成功。",
        ticket=_safe_created_ticket(ticket),
    )


def create_product_mcp_server(
    settings: Settings | None = None,
) -> MCPServer:
    """Create a product-grade MCP server exposing only business tools."""
    resolved_settings = settings or get_settings()
    server = MCPServer(name="ai-service-product-mcp")

    @server.tool()
    def query_order(order_id: str) -> dict[str, Any]:
        """Query a business order through the guarded Java adapter (read-only)."""
        return order_tool.query_order_for_mcp(order_id)

    @server.tool()
    def create_ticket(
        requester_id: str,
        title: str,
        description: str,
        category: str,
        confirmation_id: Annotated[str, Field(pattern=CONFIRMATION_ID_PATTERN)],
        priority: str = "normal",
        related_order_id: str | None = None,
        user_confirmed: bool = False,
    ) -> dict[str, Any]:
        """Create a support ticket after user confirmation and idempotency checks."""
        return _product_create_ticket(
            requester_id=requester_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            related_order_id=related_order_id,
            confirmation_id=confirmation_id,
            user_confirmed=user_confirmed,
        )

    return server


class BearerAuthMiddleware:
    """ASGI middleware enforcing a fixed Bearer token on every HTTP request."""

    def __init__(self, app: Any, *, token: str) -> None:
        self.app = app
        self.expected = f"Bearer {token}"

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        authorization = None
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                authorization = value.decode("latin-1")
                break

        if authorization != self.expected:
            from starlette.responses import JSONResponse

            response = JSONResponse(
                {"error": "unauthorized", "message": "missing or invalid bearer token"},
                status_code=401,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


class _LazySessionManagerApp:
    """ASGI wrapper that lazily starts the MCP streamable-HTTP session manager.

    mcp 2.0.0's ``streamable_http_app`` initializes its session manager inside
    the Starlette lifespan. Framework servers (uvicorn) run that lifespan, but
    plain ASGI callers that skip lifespan (e.g. ``starlette.testclient.TestClient``
    used without ``with``) would otherwise hit "Task group is not initialized".
    This wrapper starts the manager on the first HTTP request in that case; when
    the manager is already running (lifespan-managed) it simply forwards.
    """

    def __init__(self, app: Any, session_manager: Any) -> None:
        self._app = app
        self._session_manager = session_manager
        self._started = False

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        manager = self._session_manager
        task_group = getattr(manager, "_task_group", None)
        if task_group is None and not self._started:
            self._started = True
            async with manager.run():
                await self._app(scope, receive, send)
            return

        await self._app(scope, receive, send)


def create_product_mcp_app(settings: Settings | None = None) -> Any:
    """Return the streamable HTTP Starlette app wrapped with Bearer auth."""
    resolved_settings = settings or get_settings()
    server = create_product_mcp_server(resolved_settings)

    # mcp 2.0.0: keep DNS-rebinding protection on but allow the starlette
    # TestClient ``testserver`` host, and use stateless HTTP so requests
    # without a prior initialize/session are handled directly.
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", "testserver"],
    )
    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        transport_security=transport_security,
    )
    app = _LazySessionManagerApp(app, server.session_manager)
    token = resolved_settings.resolved_mcp_product_auth_token
    if token is not None:
        return BearerAuthMiddleware(app, token=token)
    return app


def main() -> None:
    import uvicorn

    settings = get_settings()
    app = create_product_mcp_app(settings)
    uvicorn.run(app, host="127.0.0.1", port=settings.mcp_product_port)


if __name__ == "__main__":
    main()
