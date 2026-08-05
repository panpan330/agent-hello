"""Supervisor graph: top-level orchestrator nesting three worker subgraphs."""

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.multi_agent_states import SupervisorState
from app.agents.supervisor.supervisor_router import SupervisorRoute, SupervisorRouter
from app.agents.ticket_agent import (
    OrderQueryExecutor,
    PolicyRagService,
    TicketCreator,
    ask_clarifying_question_node,
    build_direct_answer_node,
    build_unsupported_answer_node,
    normalize_user_input_node,
)
from app.agents.workers.knowledge_agent import build_knowledge_agent_graph
from app.agents.workers.order_agent import build_order_agent_graph
from app.agents.workers.ticket_worker import build_ticket_worker_graph


logger = logging.getLogger(__name__)

SUPERVISOR_ROUTE_TABLE: dict[SupervisorRoute, str] = {
    SupervisorRoute.KNOWLEDGE_QUESTION: "knowledge_agent",
    SupervisorRoute.ORDER_QUERY: "order_agent",
    SupervisorRoute.TICKET_REQUEST: "ticket_agent",
    SupervisorRoute.SMALLTALK: "build_direct_answer",
    SupervisorRoute.UNSUPPORTED: "build_unsupported_answer",
    SupervisorRoute.UNCLEAR: "ask_clarifying_question",
}


def build_supervisor_graph(
    *,
    router: SupervisorRouter | None = None,
    knowledge_service: PolicyRagService | None = None,
    order_query_executor: OrderQueryExecutor | None = None,
    ticket_creator: TicketCreator | None = None,
    checkpointer: Any | None = None,
    interrupt_confirmation: bool = False,
) -> Any:
    from app.agents.supervisor.supervisor_router import create_supervisor_router

    resolved_router = router or create_supervisor_router()

    knowledge_graph = build_knowledge_agent_graph(knowledge_service)
    order_graph = build_order_agent_graph(order_query_executor)
    ticket_graph = build_ticket_worker_graph(
        ticket_creator,
        interrupt_confirmation=interrupt_confirmation,
    )

    builder = StateGraph(SupervisorState)
    builder.add_node("normalize_user_input", normalize_user_input_node)

    def supervisor_route_node(state: SupervisorState) -> SupervisorState:
        message = state.get("normalized_message") or state.get("user_message", "")
        route = resolved_router.route(message)
        intent = {
            SupervisorRoute.KNOWLEDGE_QUESTION: "policy_question",
            SupervisorRoute.ORDER_QUERY: "order_query",
            SupervisorRoute.TICKET_REQUEST: "ticket_request",
            SupervisorRoute.SMALLTALK: "smalltalk",
            SupervisorRoute.UNSUPPORTED: "unsupported",
            SupervisorRoute.UNCLEAR: "unclear",
        }[route]
        logger.info("supervisor_routed intent=%s worker=%s", intent, SUPERVISOR_ROUTE_TABLE[route])
        return {
            "intent": intent,
            "intent_reason": f"supervisor routed to {route.value}",
            "node_history": ["supervisor_route"],
        }

    builder.add_node("supervisor_route", supervisor_route_node)
    builder.add_node("knowledge_agent", knowledge_graph)
    builder.add_node("order_agent", order_graph)
    builder.add_node("ticket_agent", ticket_graph)
    builder.add_node("build_direct_answer", build_direct_answer_node)
    builder.add_node("build_unsupported_answer", build_unsupported_answer_node)
    builder.add_node("ask_clarifying_question", ask_clarifying_question_node)

    builder.add_edge(START, "normalize_user_input")
    builder.add_edge("normalize_user_input", "supervisor_route")

    def route_after_supervisor(state: SupervisorState) -> str:
        intent = state.get("intent")
        route = {
            "policy_question": SupervisorRoute.KNOWLEDGE_QUESTION,
            "order_query": SupervisorRoute.ORDER_QUERY,
            "ticket_request": SupervisorRoute.TICKET_REQUEST,
            "smalltalk": SupervisorRoute.SMALLTALK,
            "unsupported": SupervisorRoute.UNSUPPORTED,
            "unclear": SupervisorRoute.UNCLEAR,
        }.get(intent, SupervisorRoute.UNCLEAR)
        return SUPERVISOR_ROUTE_TABLE[route]

    builder.add_conditional_edges(
        "supervisor_route",
        route_after_supervisor,
        {node: node for node in SUPERVISOR_ROUTE_TABLE.values()},
    )

    def after_knowledge_agent(state: SupervisorState) -> str:
        if state.get("needs_ticket") is True:
            logger.info(
                "supervisor_knowledge_to_ticket_transfer needs_ticket=true rag_answer_status=%s",
                state.get("rag_answer_status"),
            )
            return "ticket_agent"
        return END

    builder.add_conditional_edges(
        "knowledge_agent",
        after_knowledge_agent,
        {END: END, "ticket_agent": "ticket_agent"},
    )

    builder.add_edge("order_agent", END)
    builder.add_edge("ticket_agent", END)
    builder.add_edge("build_direct_answer", END)
    builder.add_edge("build_unsupported_answer", END)
    builder.add_edge("ask_clarifying_question", END)

    return builder.compile(checkpointer=checkpointer)
