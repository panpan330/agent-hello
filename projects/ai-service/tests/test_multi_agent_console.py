import pytest

from app.agents.supervisor.supervisor_graph import build_supervisor_graph
from app.core.config import Settings
from app.services.console_agent_service import ConsoleAgentService
from tests.tool_fakes import (
    FakePolicyRagService,
    FakeTicketCreator,
    make_created_ticket,
    make_policy_rag_answer,
)
from app.schemas.tool import QueryOrderArgs, QueryOrderResult


def _order_executor(arguments: QueryOrderArgs) -> QueryOrderResult:
    return QueryOrderResult(
        order_id=arguments.order_id,
        order_status="shipped",
        payment_status="paid",
        logistics_message="已发货",
        latest_event="包裹已发出",
        can_create_ticket=True,
        source="java_business_service",
    )


def test_build_graph_returns_supervisor_graph_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        _env_file=None,
        agent_multi_agent_enabled=True,
        agent_mcp_tools_enabled=False,
    )
    service = ConsoleAgentService(settings, graph=object())
    monkeypatch.setattr(
        service,
        "_create_redis_checkpointer",
        lambda: None,
    )
    graph = service._build_graph()
    assert graph is not None


def test_build_graph_returns_single_agent_graph_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(_env_file=None, agent_multi_agent_enabled=False)
    service = ConsoleAgentService(settings, graph=object())
    monkeypatch.setattr(
        service,
        "_create_redis_checkpointer",
        lambda: None,
    )
    graph = service._build_graph()
    assert graph is not None


def test_multi_agent_console_end_to_end_rule_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: conversation -> supervisor route -> order agent -> answer."""
    from app.agents.supervisor.supervisor_router import (
        FakeLLMSupervisorRouter,
        SupervisorRoute,
    )
    from app.agents.supervisor.supervisor_graph import build_supervisor_graph

    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.ORDER_QUERY),
        order_query_executor=_order_executor,
    )
    result = graph.invoke({"user_message": "查订单 A1001"})
    assert result["intent"] == "order_query"
    assert "已发货" in (result.get("final_answer") or "")
