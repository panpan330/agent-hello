from app.agents.multi_agent_states import (
    KnowledgeWorkerState,
    OrderWorkerState,
    SupervisorState,
    TicketWorkerState,
    SUPERVISOR_OUTPUT_KEYS,
)


def test_supervisor_state_holds_core_fields() -> None:
    state: SupervisorState = {
        "user_message": "查订单",
        "normalized_message": "查订单",
        "intent": "order_query",
        "final_answer": "订单已发货",
        "node_history": ["normalize_user_input"],
    }
    assert state["intent"] == "order_query"
    assert state["final_answer"] == "订单已发货"


def test_worker_states_hold_their_own_fields() -> None:
    knowledge: KnowledgeWorkerState = {
        "normalized_message": "退货政策",
        "rag_answer_status": "answered",
        "final_answer": "退货政策是...",
    }
    order: OrderWorkerState = {
        "normalized_message": "查订单 A1001",
        "order_query_status": "succeeded",
        "order_query_result": {"order_id": "A1001"},
        "final_answer": "订单已发货",
    }
    ticket: TicketWorkerState = {
        "normalized_message": "申请退款",
        "ticket_confirmation_approved": True,
        "pending_ticket_confirmation": {"confirmation_id": "a" * 32},
        "final_answer": "工单已创建",
    }
    assert knowledge["rag_answer_status"] == "answered"
    assert order["order_query_result"]["order_id"] == "A1001"
    assert ticket["ticket_confirmation_approved"] is True


def test_supervisor_output_keys_contains_final_answer() -> None:
    assert "final_answer" in SUPERVISOR_OUTPUT_KEYS
