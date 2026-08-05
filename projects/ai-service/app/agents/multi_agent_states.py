"""State definitions for the supervisor-worker multi-agent system."""

from operator import add
from typing import Annotated, TypedDict

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
    node_history: Annotated[list[str], add]
    agent_error_code: str | None
    agent_error_message: str | None


class KnowledgeWorkerState(TypedDict, total=False):
    normalized_message: str
    agent_trace_id: str
    intent: TicketIntent
    rag_query: str
    rag_answer_status: str
    rag_citations: list[dict]
    rag_no_context_reason: str | None
    rag_suggestions: list[str]
    needs_ticket: bool
    ticket_need_reason: str
    final_answer: str | None
    node_history: Annotated[list[str], add]


class OrderWorkerState(TypedDict, total=False):
    normalized_message: str
    agent_trace_id: str
    order_query_order_id: str | None
    order_query_status: str
    order_query_result: dict | None
    order_query_error_code: str | None
    order_query_error_message: str | None
    order_query_error_kind: str | None
    order_query_error_action: str | None
    order_query_retryable: bool | None
    order_query_error_status_code: int | None
    final_answer: str | None
    node_history: Annotated[list[str], add]


class TicketWorkerState(TypedDict, total=False):
    normalized_message: str
    agent_trace_id: str
    ticket_fields: dict | None
    missing_ticket_fields: list[str]
    ticket_fields_complete: bool | None
    ticket_need_source: str | None
    ticket_confirmation_required: bool | None
    ticket_confirmation_approved: bool | None
    ticket_confirmation_correction_requested: bool | None
    ticket_confirmation_message: str | None
    pending_ticket_confirmation: dict | None
    ticket_write_safety_status: str | None
    ticket_creation_status: str | None
    ticket_creation_error_code: str | None
    ticket_creation_error_message: str | None
    ticket_creation_idempotency_key: str | None
    created_ticket: dict | None
    final_answer: str | None
    node_history: Annotated[list[str], add]


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
