"""Ticket creation worker subgraph."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.multi_agent_states import TicketWorkerState
from app.agents.ticket_agent import (
    TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    TicketCreator,
    ask_missing_ticket_fields_node,
    create_ticket_node,
    extract_ticket_fields_node,
    request_ticket_confirmation_interrupt_node,
    request_ticket_confirmation_node,
)


# 工单 worker 只执行 create_ticket，不处理 refund_request（Task 8 引入 supervisor
# refund 路由时再决定执行节点）；因此不能用共享 TICKET_AGENT_CONFIRMATION_ROUTES
# （其 execute_refund_request 目标节点在本子图中不存在，langgraph 编译校验会拒绝）。
TICKET_WORKER_CONFIRMATION_ROUTES = {
    "execute_create_ticket": "create_ticket",
    "request_confirmation": "request_ticket_confirmation",
    "finish": END,
}


def build_ticket_worker_graph(
    ticket_creator: TicketCreator | None = None,
    *,
    checkpointer: Any | None = None,
    interrupt_confirmation: bool = False,
) -> Any:
    builder = StateGraph(TicketWorkerState)
    builder.add_node(
        "extract_ticket_fields",
        lambda state: extract_ticket_fields_node(state),
    )
    builder.add_node("ask_missing_ticket_fields", ask_missing_ticket_fields_node)
    builder.add_node(
        "request_ticket_confirmation",
        (
            request_ticket_confirmation_interrupt_node
            if interrupt_confirmation
            else request_ticket_confirmation_node
        ),
    )
    builder.add_node(
        "create_ticket",
        lambda state: create_ticket_node(state, creator=ticket_creator),
    )
    builder.add_edge(START, "extract_ticket_fields")
    builder.add_conditional_edges(
        "extract_ticket_fields",
        lambda state: (
            "ask_missing_fields"
            if (state.get("missing_ticket_fields") or [])
            else "request_confirmation"
        ),
        TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    )
    builder.add_edge("ask_missing_ticket_fields", END)
    builder.add_edge("create_ticket", END)
    builder.add_conditional_edges(
        "request_ticket_confirmation",
        lambda state: (
            "execute_create_ticket"
            if state.get("ticket_confirmation_approved") is True
            else "finish"
        ),
        TICKET_WORKER_CONFIRMATION_ROUTES,
    )
    return builder.compile(checkpointer=checkpointer)
