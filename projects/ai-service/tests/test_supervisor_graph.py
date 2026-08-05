import pytest

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.agents.supervisor.supervisor_graph import (
    SUPERVISOR_ROUTE_TABLE,
    build_supervisor_graph,
)
from app.agents.supervisor.supervisor_router import (
    FakeLLMSupervisorRouter,
    SupervisorRoute,
)
from tests.rag_fakes import make_retrieved_chunk
from tests.tool_fakes import (
    FakeNoContextPolicyRagService,
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


def test_route_table_maps_all_routes() -> None:
    for route in SupervisorRoute:
        assert route in SUPERVISOR_ROUTE_TABLE


def test_supervisor_routes_order_query_to_order_agent() -> None:
    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.ORDER_QUERY),
        order_query_executor=_order_executor,
    )
    result = graph.invoke({"user_message": "查订单 A1001 物流"})
    assert result["intent"] == "order_query"
    assert "已发货" in (result.get("final_answer") or "")


def test_supervisor_routes_policy_to_knowledge_agent() -> None:
    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.KNOWLEDGE_QUESTION),
        knowledge_service=FakePolicyRagService(
            make_policy_rag_answer(answer="退货政策是 30 天无理由。")
        ),
    )
    result = graph.invoke({"user_message": "退货政策是什么"})
    assert result["rag_answer_status"] == "answered"
    assert "退货政策" in (result.get("final_answer") or "")


def test_supervisor_routes_ticket_to_ticket_agent() -> None:
    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.TICKET_REQUEST),
        ticket_creator=FakeTicketCreator(),
        interrupt_confirmation=False,
    )
    result = graph.invoke(
        {
            "user_message": "申请退款，订单 A1001 破损",
            "ticket_confirmation_approved": True,
            "ticket_fields": {
                "issue_type": "refund",
                "order_id": "A1001",
                "description": "订单破损",
                "user_request": "申请退款",
                "urgency": "high",
                "need_human_review": False,
            },
        }
    )
    assert result["ticket_creation_status"] == "created"
    assert result["created_ticket"]["ticket_id"] is not None


def test_supervisor_smalltalk_builds_direct_answer() -> None:
    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.SMALLTALK)
    )
    result = graph.invoke({"user_message": "你好"})
    assert result["final_answer"] is not None


def test_knowledge_no_context_transfers_to_ticket() -> None:
    """Knowledge 子图 RAG no_context 时，监督层应把流程转给 ticket worker 建工单。"""
    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.KNOWLEDGE_QUESTION),
        knowledge_service=FakeNoContextPolicyRagService(),
        ticket_creator=FakeTicketCreator(),
        interrupt_confirmation=False,
    )
    result = graph.invoke(
        {
            "user_message": "一个知识库没有的问题",
            "ticket_confirmation_approved": True,
            "ticket_fields": {
                "issue_type": "policy_gap",
                "order_id": None,
                "description": "一个知识库没有的问题",
                "user_request": "一个知识库没有的问题",
                "urgency": "medium",
                "need_human_review": True,
            },
        }
    )
    assert result["needs_ticket"] is True
    assert result["rag_answer_status"] == "no_context"
    assert result["ticket_need_source"] == "rag_no_context"
    # 转单语义完整验证：ticket worker 实际创建了 policy_gap 工单
    assert result["created_ticket"] is not None
    assert result["created_ticket"]["category"] == "policy_gap"


def test_ticket_interrupt_pause_and_resume() -> None:
    """interrupt_confirmation=True 时 ticket worker 应暂停并等待确认，resume 后完成建单。"""
    graph = build_supervisor_graph(
        router=FakeLLMSupervisorRouter(SupervisorRoute.TICKET_REQUEST),
        ticket_creator=FakeTicketCreator(),
        interrupt_confirmation=True,
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "supervisor-interrupt-test"}}
    initial = graph.invoke(
        {"user_message": "申请退款，订单 A1001 破损"},
        config=config,
    )
    assert initial.get("__interrupt__")
    resumed = graph.invoke(
        Command(resume={"approved": True}),
        config=config,
    )
    assert resumed.get("ticket_creation_status") == "created"
    assert resumed.get("created_ticket") is not None
