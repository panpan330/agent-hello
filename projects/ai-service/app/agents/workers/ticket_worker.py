"""Ticket creation worker subgraph."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.multi_agent_states import TicketWorkerState
from app.agents.ticket_agent import (
    TICKET_AGENT_CONFIRMATION_ROUTES,
    TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    TicketCreator,
    ask_missing_ticket_fields_node,
    create_ticket_node,
    extract_ticket_fields_node,
    request_ticket_confirmation_interrupt_node,
    request_ticket_confirmation_node,
)


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
        TICKET_AGENT_CONFIRMATION_ROUTES,
    )
    return builder.compile(checkpointer=checkpointer)
