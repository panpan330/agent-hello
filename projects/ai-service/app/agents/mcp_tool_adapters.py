"""MCP-backed adapters that satisfy the ticket agent's executor/creator protocols."""

from typing import Any

from app.agents.ticket_agent import TicketFields
from app.core.business_context import get_business_context
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.mcp_clients.product_client import McpToolCaller, create_product_mcp_client
from app.schemas.ticket import CreateTicketArgs, CreatedTicket
from app.schemas.tool import QueryOrderArgs, QueryOrderResult
from app.tools.tool_confirmation import create_tool_confirmation_store


CREATE_TICKET_TOOL_NAME = "create_ticket"
QUERY_ORDER_TOOL_NAME = "query_order"


def _resolve_tenant_id(*, injected: str | None) -> str | None:
    """Tenant comes from the executor/creator injection or the business context
    that the console agent service set for the authenticated actor."""
    if injected is not None:
        return injected or None
    return get_business_context()[1]


def _require_ok(payload: dict[str, Any], *, fallback_code: str) -> None:
    if payload.get("ok") is True:
        return
    raise AppException(
        code=payload.get("error_code") or fallback_code,
        message=payload.get("message") or "工具调用失败，请稍后重试。",
        status_code=502,
    )


class McpTicketCreator:
    """TicketCreator that executes create_ticket through the product MCP client."""

    def __init__(
        self,
        caller: McpToolCaller,
        *,
        settings: Settings | None = None,
        user_id: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        self._caller = caller
        self._settings = settings or get_settings()
        self._user_id = user_id
        self._tenant_id = tenant_id

    def create_ticket(
        self,
        arguments: CreateTicketArgs,
        *,
        idempotency_key: str,
    ) -> CreatedTicket:
        # The requester id is the agent's ticket_actor_id (the authenticated
        # user). The tenant comes from the injected value or the business
        # context; both are forwarded to the standalone MCP server so Java
        # ownership checks see the real caller, not the default fallback.
        user_id = self._user_id or arguments.requester_id
        tenant_id = _resolve_tenant_id(injected=self._tenant_id)
        payload = self._caller.call_tool(
            CREATE_TICKET_TOOL_NAME,
            {
                "requester_id": arguments.requester_id,
                "title": arguments.title,
                "description": arguments.description,
                "category": arguments.category.value,
                "priority": arguments.priority.value,
                "related_order_id": arguments.related_order_id,
                "confirmation_id": idempotency_key,
                "user_confirmed": True,
                "user_id": user_id,
                "tenant_id": tenant_id,
            },
        )
        _require_ok(payload, fallback_code="TICKET_CREATION_TOOL_ERROR")
        ticket_payload = payload.get("ticket")
        if not isinstance(ticket_payload, dict):
            raise AppException(
                code="MCP_RESULT_INVALID",
                message="AI 工具服务返回了无法解析的工单结果。",
                status_code=502,
            )
        return CreatedTicket.model_validate(ticket_payload)


def mcp_order_query_executor(
    caller: McpToolCaller,
    *,
    user_id: str | None = None,
    tenant_id: str | None = None,
) -> Any:
    """Return an OrderQueryExecutor (Callable[[QueryOrderArgs], QueryOrderResult]).

    ``user_id``/``tenant_id`` are forwarded to the product MCP server. They can
    be injected at construction (factory style) or, by default, read from the
    business context that the console agent service set for the authenticated
    actor at request time.
    """

    def execute(arguments: QueryOrderArgs) -> QueryOrderResult:
        ctx_user_id, _ = get_business_context()
        forwarded_user_id = user_id or ctx_user_id
        forwarded_tenant_id = _resolve_tenant_id(injected=tenant_id)
        payload = caller.call_tool(
            QUERY_ORDER_TOOL_NAME,
            {
                "order_id": arguments.order_id,
                "user_id": forwarded_user_id,
                "tenant_id": forwarded_tenant_id,
            },
        )
        _require_ok(payload, fallback_code="TOOL_CALL_FAILED")
        result_payload = payload.get("result")
        if not isinstance(result_payload, dict):
            raise AppException(
                code="MCP_RESULT_INVALID",
                message="AI 工具服务返回了无法解析的订单结果。",
                status_code=502,
            )
        return QueryOrderResult.model_validate(result_payload)

    return execute


def create_mcp_ticket_creator(
    settings: Settings | None = None,
    *,
    caller: McpToolCaller | None = None,
    user_id: str | None = None,
    tenant_id: str | None = None,
) -> McpTicketCreator:
    resolved_settings = settings or get_settings()
    return McpTicketCreator(
        caller or create_product_mcp_client(resolved_settings),
        settings=resolved_settings,
        user_id=user_id,
        tenant_id=tenant_id,
    )


def create_mcp_order_query_executor(
    settings: Settings | None = None,
    *,
    caller: McpToolCaller | None = None,
    user_id: str | None = None,
    tenant_id: str | None = None,
) -> Any:
    resolved_settings = settings or get_settings()
    return mcp_order_query_executor(
        caller or create_product_mcp_client(resolved_settings),
        user_id=user_id,
        tenant_id=tenant_id,
    )


def register_ticket_confirmation(
    actor_id: str,
    fields: TicketFields,
    *,
    settings: Settings | None = None,
) -> str:
    """Register the agent's pending confirmation as confirmed in the shared store.

    Returns the confirmation_id that the MCP server will verify.
    """
    from app.agents.ticket_agent import build_pending_ticket_confirmation

    resolved_settings = settings or get_settings()
    confirmation_id = build_pending_ticket_confirmation(fields)["confirmation_id"]
    store = create_tool_confirmation_store(resolved_settings)
    store.register_confirmed(
        confirmation_id=confirmation_id,
        actor_id=actor_id,
        tool_name=CREATE_TICKET_TOOL_NAME,
        arguments=dict(fields),
        ttl_seconds=resolved_settings.tool_confirmation_ttl_seconds,
    )
    return confirmation_id
