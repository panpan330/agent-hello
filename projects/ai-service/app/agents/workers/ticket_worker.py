"""Ticket worker subgraph: ticket creation and refund execution worker paths.

Task 8：工单 worker 子图同时承载两条 worker 链——
1. 工单创建链（intent=ticket_request / 非退款）：extract_ticket_fields → 缺字段追问/
   确认 → create_ticket；
2. 退款执行链（intent=refund_request 或 active-refund-collection）：handle_refund_request
   → 缺字段追问/确认 → execute_refund_request。

退款执行链复用 ticket_agent 主图的 handle_refund_request_node /
execute_refund_request_node，使多 Agent supervisor 下 refund_request 的行为与单
Agent 主图一致（收集 order_id+reason → 确认 → 执行 refund_order），而非退化为仅
创建退款工单（规格 4.4：工单 worker 子图原不支持退款意图，故新增退款节点）。
"""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.multi_agent_states import TicketWorkerState
from app.agents.ticket_agent import (
    TICKET_AGENT_CONFIRMATION_ROUTES,
    TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    RefundExecutor,
    TicketCreator,
    ask_missing_ticket_fields_node,
    create_ticket_node,
    execute_refund_request_node,
    extract_ticket_fields_node,
    handle_refund_request_node,
    has_active_refund_collection,
    request_ticket_confirmation_interrupt_node,
    request_ticket_confirmation_node,
    route_by_refund_fields,
    route_by_ticket_confirmation,
)


def route_ticket_worker_entry(state: TicketWorkerState) -> str:
    """入口分流：退款请求走 handle_refund_request 链，其余走工单字段提取链。

    双判别点（intent 或 active-refund-collection 任一命中即退款）：
    - 第一轮：supervisor 已分类 intent=refund_request；
    - 后续轮：supervisor_route_node 的 active-refund-collection 强制
      intent=refund_request，同时顶层 refund_request_active=True + 仍缺字段
      （has_active_refund_collection）兜底，防止 LLM 路由误判偏离退款流程。
    第二判别刻意要求"仍缺字段"：退款字段完整、待确认（missing 为空）时
    refund_request_active 仍为 True，若仅凭裸标志判断会把用户改口的工单诉求
    （如"帮我建个报修工单"）劫持进退款链；与 supervisor 两处 active-collection
    守卫语义一致。
    """
    if (
        state.get("intent") == "refund_request"
        or has_active_refund_collection(state)
    ):
        return "handle_refund_request"
    return "extract_ticket_fields"


TICKET_WORKER_ENTRY_ROUTES = {
    "handle_refund_request": "handle_refund_request",
    "extract_ticket_fields": "extract_ticket_fields",
}

# 退款执行目标节点在本子图中存在后，确认路由表与 ticket_agent 主图的
# TICKET_AGENT_CONFIRMATION_ROUTES 完全一致，直接复用共享表。


def build_ticket_worker_graph(
    ticket_creator: TicketCreator | None = None,
    *,
    refund_executor: RefundExecutor | None = None,
    checkpointer: Any | None = None,
    interrupt_confirmation: bool = False,
) -> Any:
    builder = StateGraph(TicketWorkerState)
    builder.add_conditional_edges(
        START,
        route_ticket_worker_entry,
        TICKET_WORKER_ENTRY_ROUTES,
    )
    builder.add_node(
        "extract_ticket_fields",
        lambda state: extract_ticket_fields_node(state),
    )
    builder.add_node(
        "handle_refund_request",
        lambda state: handle_refund_request_node(state),
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
    builder.add_node(
        "execute_refund_request",
        lambda state: execute_refund_request_node(
            state,
            refund_executor=refund_executor,
        ),
    )
    builder.add_conditional_edges(
        "extract_ticket_fields",
        lambda state: (
            "ask_missing_fields"
            if (state.get("missing_ticket_fields") or [])
            else "request_confirmation"
        ),
        TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    )
    builder.add_conditional_edges(
        "handle_refund_request",
        route_by_refund_fields,
        TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    )
    builder.add_edge("ask_missing_ticket_fields", END)
    builder.add_edge("create_ticket", END)
    builder.add_edge("execute_refund_request", END)
    builder.add_conditional_edges(
        "request_ticket_confirmation",
        route_by_ticket_confirmation,
        TICKET_AGENT_CONFIRMATION_ROUTES,
    )
    return builder.compile(checkpointer=checkpointer)
