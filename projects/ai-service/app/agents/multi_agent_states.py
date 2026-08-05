"""State definitions for the supervisor-worker multi-agent system."""

from typing import TypedDict

from app.schemas.structured import TicketIntent


class SupervisorState(TypedDict, total=False):
    user_message: str
    normalized_message: str
    agent_trace_id: str
    intent: TicketIntent
    intent_reason: str
    # 跨 Agent 协作字段（knowledge 子图输出，监督层读取）
    rag_answer_status: str
    rag_citations: list[dict]
    needs_ticket: bool
    final_answer: str | None
    node_history: list[str]
    agent_error_code: str | None
    agent_error_message: str | None


class KnowledgeWorkerState(TypedDict, total=False):
    normalized_message: str
    intent: TicketIntent
    rag_query: str
    rag_answer_status: str
    rag_citations: list[dict]
    rag_no_context_reason: str | None
    rag_suggestions: list[str]
    needs_ticket: bool
    ticket_need_reason: str
    final_answer: str | None
    node_history: list[str]


class OrderWorkerState(TypedDict, total=False):
    normalized_message: str
    order_query_order_id: str | None
    order_query_status: str
    order_query_result: dict | None
    order_query_error_code: str | None
    order_query_error_message: str | None
    final_answer: str | None
    node_history: list[str]


class TicketWorkerState(TypedDict, total=False):
    normalized_message: str
    ticket_fields: dict | None
    ticket_confirmation_approved: bool | None
    pending_ticket_confirmation: dict | None
    ticket_creation_status: str | None
    created_ticket: dict | None
    final_answer: str | None
    node_history: list[str]


# Fields a worker subgraph writes back to the supervisor top-level state.
SUPERVISOR_OUTPUT_KEYS = frozenset(
    {
        "final_answer",
        "needs_ticket",
        "rag_answer_status",
        "rag_citations",
        "agent_error_code",
        "agent_error_message",
    }
)
