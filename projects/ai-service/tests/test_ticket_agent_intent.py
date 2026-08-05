import logging

import pytest
from langgraph.graph import END, START

from app.agents.ticket_agent import (
    TICKET_AGENT_CONFIRMATION_ROUTES,
    TICKET_AGENT_FIELD_COMPLETION_ROUTES,
    TICKET_AGENT_FIXED_EDGES,
    TICKET_AGENT_INTENT_ROUTES,
    TICKET_AGENT_TICKET_NEED_ROUTES,
    ask_missing_ticket_fields_node,
    ask_clarifying_question_node,
    approve_ticket_confirmation_and_resume,
    build_checkpointed_ticket_agent_graph,
    build_interrupting_ticket_agent_graph,
    build_create_ticket_args_from_fields,
    build_ticket_agent_graph,
    build_ticket_agent_fallback_state,
    build_ticket_agent_observation_metadata,
    build_ticket_confirmation_interrupt_payload,
    build_pending_ticket_confirmation,
    build_missing_ticket_fields_question,
    build_ticket_confirmation_message,
    build_ticket_agent_input,
    build_ticket_agent_thread_config,
    classify_intent_node,
    classify_ticket_intent,
    decide_ticket_need,
    decide_ticket_need_node,
    extract_ticket_fields,
    extract_ticket_fields_node,
    find_missing_ticket_fields,
    get_ticket_confirmation_interrupt_payload,
    get_ticket_agent_thread_state,
    is_ticket_confirmation_resume_approved,
    normalize_user_input_node,
    create_ticket_node,
    retrieve_policy_node,
    request_ticket_confirmation_node,
    request_ticket_confirmation_interrupt_node,
    resume_ticket_confirmation_interrupt,
    resume_ticket_confirmation_interrupt_safely,
    route_by_ticket_confirmation,
    route_by_ticket_fields_complete,
    route_by_intent,
    route_by_ticket_need,
    run_ticket_agent_in_thread,
    run_ticket_agent,
    run_ticket_agent_safely,
    stream_ticket_agent_updates,
    TICKET_AGENT_FALLBACK_ERROR_CODE,
    TICKET_AGENT_FALLBACK_MESSAGE,
    TICKET_CONFIRMATION_INTERRUPT_NOT_FOUND_MESSAGE,
    TICKET_CONFIRMATION_REJECTED_MESSAGE,
    TICKET_CONFIRMATION_NOT_FOUND_MESSAGE,
    TICKET_CREATION_UNEXPECTED_ERROR_CODE,
    TICKET_CREATION_UNEXPECTED_ERROR_MESSAGE,
    TICKET_THREAD_ID_INVALID_ERROR_CODE,
)
from app.core.logging import install_trace_id_log_record_factory
from app.core.exceptions import AppException
from app.core.trace import reset_trace_id, set_trace_id
from app.rag.generator import RAG_NO_CONTEXT_REPLY
from app.schemas.tool import QueryOrderArgs, QueryOrderResult
from tests.tool_fakes import (
    FakeNoContextPolicyRagService,
    FakePolicyRagService,
    FakeTicketCreator,
)


def make_complete_ticket_fields() -> dict[str, object]:
    return {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": True,
    }


def make_ticket_agent_query_order_result(order_id: str = "1001") -> QueryOrderResult:
    return QueryOrderResult(
        order_id=order_id,
        order_status="waiting_shipment",
        payment_status="paid",
        logistics_message="商家已接单，等待仓库发货。",
        latest_event="仓库正在准备出库。",
        can_create_ticket=True,
        source="java_mock_service",
    )


def fake_execute_ticket_order_query(arguments: QueryOrderArgs) -> QueryOrderResult:
    return make_ticket_agent_query_order_result(arguments.order_id)


class BrokenTicketAgentGraph:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def invoke(self, state: object, config: object | None = None) -> object:
        raise self.error


def test_build_ticket_agent_fallback_state_returns_user_safe_state() -> None:
    update = build_ticket_agent_fallback_state(
        node_name="ticket_agent_graph",
        code="DEMO_ERROR",
        message="流程暂时不可用。",
    )

    assert update == {
        "agent_error_code": "DEMO_ERROR",
        "agent_error_message": "流程暂时不可用。",
        "agent_error_node": "ticket_agent_graph",
        "fallback_used": True,
        "final_answer": "流程暂时不可用。",
        "node_history": ["ticket_agent_graph"],
    }


def test_build_ticket_agent_observation_metadata_summarizes_state() -> None:
    metadata = build_ticket_agent_observation_metadata(
        {
            "agent_trace_id": "trace-agent-001",
            "intent": "ticket_request",
            "node_history": ["normalize_user_input", "create_ticket"],
            "fallback_used": True,
            "agent_error_code": "TOOL_UPSTREAM_ERROR",
            "ticket_creation_status": "failed",
        },
        operation="invoke_safe",
        thread_id="ticket-thread-001",
        elapsed_ms=12.345,
    )

    assert metadata == {
        "operation": "invoke_safe",
        "trace_id": "trace-agent-001",
        "thread_id": "ticket-thread-001",
        "intent": "ticket_request",
        "node_count": 2,
        "last_node": "create_ticket",
        "interrupted": False,
        "fallback_used": True,
        "agent_error_code": "TOOL_UPSTREAM_ERROR",
        "ticket_creation_status": "failed",
        "elapsed_ms": 12.35,
    }


def test_ticket_agent_fixed_edges_define_entry_and_finish_points() -> None:
    assert TICKET_AGENT_FIXED_EDGES == (
        (START, "normalize_user_input"),
        ("normalize_user_input", "classify_intent"),
        ("retrieve_policy", "decide_ticket_need"),
        ("query_order", END),
        ("ask_missing_ticket_fields", END),
        ("create_ticket", END),
        ("build_direct_answer", END),
        ("build_unsupported_answer", END),
        ("ask_clarifying_question", END),
    )


def test_ticket_agent_intent_routes_map_intent_to_next_node() -> None:
    assert TICKET_AGENT_INTENT_ROUTES == {
        "policy_question": "retrieve_policy",
        "order_query": "query_order",
        "ticket_request": "decide_ticket_need",
        "smalltalk": "build_direct_answer",
        "unsupported": "build_unsupported_answer",
        "unclear": "ask_clarifying_question",
    }


def test_ticket_agent_ticket_need_routes_map_decision_to_next_node() -> None:
    assert TICKET_AGENT_TICKET_NEED_ROUTES == {
        "create_ticket": "extract_ticket_fields",
        "finish": END,
    }


def test_ticket_agent_field_completion_routes_map_decision_to_next_node() -> None:
    assert TICKET_AGENT_FIELD_COMPLETION_ROUTES == {
        "ask_missing_fields": "ask_missing_ticket_fields",
        "request_confirmation": "request_ticket_confirmation",
    }


def test_ticket_agent_confirmation_routes_map_decision_to_next_node() -> None:
    assert TICKET_AGENT_CONFIRMATION_ROUTES == {
        "execute_create_ticket": "create_ticket",
        "request_confirmation": "request_ticket_confirmation",
        "finish": END,
    }


@pytest.mark.parametrize(
    ("message", "expected_intent"),
    [
        ("退款规则是什么？", "policy_question"),
        ("我的订单 1001 到哪了？", "order_query"),
        ("我要投诉订单 1001，物流一直不动", "ticket_request"),
        ("你好，你能做什么？", "smalltalk"),
        ("帮我直接退款到账", "unsupported"),
        ("有问题", "unclear"),
        ("   ", "unclear"),
    ],
)
def test_classify_ticket_intent_returns_expected_intent(
    message: str,
    expected_intent: str,
) -> None:
    classification = classify_ticket_intent(message)

    assert classification["intent"] == expected_intent
    assert classification["reason"]


def test_normalize_user_input_node_returns_clean_message() -> None:
    update = normalize_user_input_node({"user_message": "  退款规则是什么？  "})

    assert update == {
        "normalized_message": "退款规则是什么？",
        "node_history": ["normalize_user_input"],
    }


def test_classify_intent_node_writes_intent_to_state() -> None:
    update = classify_intent_node({"normalized_message": "我的订单 1001 到哪了？"})

    assert update["intent"] == "order_query"
    assert update["intent_reason"]
    assert update["node_history"] == ["classify_intent"]


def test_route_by_intent_returns_matching_route() -> None:
    assert route_by_intent({"intent": "ticket_request"}) == "ticket_request"


def test_route_by_intent_defaults_to_unclear() -> None:
    assert route_by_intent({}) == "unclear"


def test_decide_ticket_need_returns_true_for_explicit_ticket_request() -> None:
    decision = decide_ticket_need(
        {
            "intent": "ticket_request",
            "normalized_message": "我要投诉订单 1001",
        }
    )

    assert decision == {
        "needs_ticket": True,
        "reason": "用户明确表达了投诉、售后处理或创建工单诉求，需要进入工单流程。",
        "source": "explicit_user_request",
    }


def test_decide_ticket_need_returns_false_when_rag_answered() -> None:
    decision = decide_ticket_need(
        {
            "intent": "policy_question",
            "rag_answer_status": "answered",
        }
    )

    assert decision == {
        "needs_ticket": False,
        "reason": "知识库已给出可引用回答，当前不需要创建工单。",
        "source": "rag_answered",
    }


def test_decide_ticket_need_returns_true_when_rag_has_no_context() -> None:
    decision = decide_ticket_need(
        {
            "intent": "policy_question",
            "rag_answer_status": "no_context",
        }
    )

    assert decision == {
        "needs_ticket": True,
        "reason": "知识库没有找到足够资料，需要进入工单流程记录问题或交给人工处理。",
        "source": "rag_no_context",
    }


def test_decide_ticket_need_node_writes_decision_to_state() -> None:
    update = decide_ticket_need_node(
        {
            "intent": "ticket_request",
            "normalized_message": "我要创建工单",
        }
    )

    assert update == {
        "needs_ticket": True,
        "ticket_need_reason": "用户明确表达了投诉、售后处理或创建工单诉求，需要进入工单流程。",
        "ticket_need_source": "explicit_user_request",
        "node_history": ["decide_ticket_need"],
    }


def test_route_by_ticket_need_returns_create_ticket_when_needed() -> None:
    assert route_by_ticket_need({"needs_ticket": True}) == "create_ticket"


def test_route_by_ticket_need_returns_finish_by_default() -> None:
    assert route_by_ticket_need({}) == "finish"


def test_route_by_ticket_fields_complete_asks_when_fields_incomplete() -> None:
    assert (
        route_by_ticket_fields_complete({"ticket_fields_complete": False})
        == "ask_missing_fields"
    )


def test_route_by_ticket_fields_complete_requests_confirmation_when_complete() -> None:
    assert (
        route_by_ticket_fields_complete({"ticket_fields_complete": True})
        == "request_confirmation"
    )


def test_route_by_ticket_fields_complete_asks_by_default() -> None:
    assert route_by_ticket_fields_complete({}) == "ask_missing_fields"


def test_route_by_ticket_confirmation_executes_only_when_approved() -> None:
    assert (
        route_by_ticket_confirmation({"ticket_confirmation_approved": True})
        == "execute_create_ticket"
    )


def test_route_by_ticket_confirmation_finishes_by_default() -> None:
    assert route_by_ticket_confirmation({}) == "finish"


def test_build_missing_ticket_fields_question_returns_single_field_question() -> None:
    assert build_missing_ticket_fields_question(["order_id"]) == (
        "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。"
    )


def test_build_missing_ticket_fields_question_returns_multi_field_question() -> None:
    question = build_missing_ticket_fields_question(["issue_type", "order_id"])

    assert question.startswith("为了继续创建工单，请补充以下信息：")
    assert "请说明这是退款、物流、投诉，还是其他需要人工处理的问题。" in question
    assert "请补充相关订单号" in question


def test_build_missing_ticket_fields_question_handles_complete_fields() -> None:
    assert build_missing_ticket_fields_question([]) == (
        "工单字段已经完整，后续课程会学习如何请求用户确认。"
    )


def test_extract_ticket_fields_from_explicit_complaint_with_order_id() -> None:
    fields = extract_ticket_fields(
        {
            "normalized_message": "我要投诉订单 1001，物流一直不动",
            "ticket_need_source": "explicit_user_request",
        }
    )

    assert fields == {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": True,
    }


def test_extract_ticket_fields_marks_order_id_missing_for_order_related_issue() -> None:
    fields = extract_ticket_fields(
        {
            "normalized_message": "商品破损，帮我处理",
            "ticket_need_source": "explicit_user_request",
        }
    )

    assert fields["issue_type"] == "complaint"
    assert fields["order_id"] is None
    assert find_missing_ticket_fields(fields) == ["order_id"]


def test_extract_ticket_fields_builds_policy_gap_ticket_from_rag_no_context() -> None:
    fields = extract_ticket_fields(
        {
            "normalized_message": "会员等级政策是什么？",
            "ticket_need_source": "rag_no_context",
            "rag_answer_status": "no_context",
        }
    )

    assert fields == {
        "issue_type": "policy_gap",
        "order_id": None,
        "description": "用户问题：会员等级政策是什么？；知识库未找到足够资料。",
        "user_request": "补充或人工解释知识库未覆盖问题",
        "urgency": "normal",
        "need_human_review": True,
    }
    assert find_missing_ticket_fields(fields) == []


def test_extract_ticket_fields_node_writes_complete_fields_to_state() -> None:
    update = extract_ticket_fields_node(
        {
            "normalized_message": "我要投诉订单 1001，物流一直不动",
            "ticket_need_source": "explicit_user_request",
        }
    )

    assert update["ticket_fields"] == {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": True,
    }
    assert update["missing_ticket_fields"] == []
    assert update["ticket_fields_complete"] is True
    assert update["ticket_field_extraction_source"] == "rule_based"
    assert update["node_history"] == ["extract_ticket_fields"]


def test_extract_ticket_fields_node_writes_missing_fields_to_state() -> None:
    update = extract_ticket_fields_node(
        {
            "normalized_message": "商品破损，帮我处理",
            "ticket_need_source": "explicit_user_request",
        }
    )

    assert update["ticket_fields"]["issue_type"] == "complaint"
    assert update["ticket_fields"]["order_id"] is None
    assert update["missing_ticket_fields"] == ["order_id"]
    assert update["ticket_fields_complete"] is False
    assert "order_id" in update["final_answer"]


def test_ask_missing_ticket_fields_node_writes_question_to_state() -> None:
    update = ask_missing_ticket_fields_node({"missing_ticket_fields": ["order_id"]})

    assert update == {
        "missing_ticket_field_question": (
            "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。"
        ),
        "missing_ticket_field_question_fields": ["order_id"],
        "final_answer": "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。",
        "node_history": ["ask_missing_ticket_fields"],
    }


def test_build_ticket_confirmation_message_includes_key_fields() -> None:
    fields = {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": True,
    }

    message = build_ticket_confirmation_message(fields)

    assert "请确认是否按以下信息创建" in message
    assert "问题类型：投诉/异常处理" in message
    assert "订单号：1001" in message
    assert "问题描述：我要投诉订单 1001，物流一直不动" in message
    assert "用户诉求：投诉处理" in message
    assert "紧急程度：高" in message
    assert "确认创建" in message


def test_build_pending_ticket_confirmation_is_stable_for_same_fields() -> None:
    fields = {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": True,
    }

    first = build_pending_ticket_confirmation(fields)
    second = build_pending_ticket_confirmation(fields)

    assert first["confirmation_id"] == second["confirmation_id"]
    assert first["status"] == "pending"
    assert first["title"] == "待确认工单：投诉/异常处理"
    assert first["ticket_fields"] == fields
    assert first["message"]


def test_request_ticket_confirmation_node_writes_pending_confirmation_to_state() -> None:
    fields = make_complete_ticket_fields()

    update = request_ticket_confirmation_node({"ticket_fields": fields})

    assert update["ticket_confirmation_required"] is True
    assert update["pending_ticket_confirmation"]["status"] == "pending"
    assert update["pending_ticket_confirmation"]["ticket_fields"] == fields
    assert update["ticket_confirmation_message"] == update["final_answer"]
    assert update["node_history"] == ["request_ticket_confirmation"]


def test_build_ticket_confirmation_interrupt_payload_exposes_pending_confirmation() -> None:
    pending_confirmation = build_pending_ticket_confirmation(make_complete_ticket_fields())

    payload = build_ticket_confirmation_interrupt_payload(pending_confirmation)

    assert payload["kind"] == "ticket_confirmation"
    assert payload["confirmation_id"] == pending_confirmation["confirmation_id"]
    assert payload["message"] == pending_confirmation["message"]
    assert payload["pending_ticket_confirmation"] == pending_confirmation


@pytest.mark.parametrize(
    ("resume_value", "expected"),
    [
        (True, True),
        (False, False),
        ({"approved": True}, True),
        ({"approved": False}, False),
        ({}, False),
        ("确认创建", False),
    ],
)
def test_is_ticket_confirmation_resume_approved_parses_supported_values(
    resume_value: object,
    expected: bool,
) -> None:
    assert is_ticket_confirmation_resume_approved(resume_value) is expected


def test_request_ticket_confirmation_interrupt_node_requires_runtime_interrupt() -> None:
    with pytest.raises(RuntimeError, match="Called get_config outside of a runnable context"):
        request_ticket_confirmation_interrupt_node(
            {"ticket_fields": make_complete_ticket_fields()}
        )


def test_build_create_ticket_args_from_fields_maps_agent_fields_to_java_contract() -> None:
    arguments = build_create_ticket_args_from_fields(
        make_complete_ticket_fields(),
        actor_id="demo_user_001",
    )

    assert arguments.requester_id == "demo_user_001"
    assert arguments.title == "投诉/异常处理：订单 1001，投诉处理"
    assert arguments.description == "我要投诉订单 1001，物流一直不动"
    assert arguments.category == "complaint"
    assert arguments.priority == "high"
    assert arguments.related_order_id == "1001"


def test_build_create_ticket_args_from_policy_gap_fields_maps_contract() -> None:
    arguments = build_create_ticket_args_from_fields(
        {
            "issue_type": "policy_gap",
            "order_id": None,
            "description": "用户问题：会员等级政策是什么？；知识库未找到足够资料。",
            "user_request": "补充或人工解释知识库未覆盖问题",
            "urgency": "normal",
            "need_human_review": True,
        },
        actor_id="demo_user_001",
    )

    assert arguments.category == "policy_gap"
    assert arguments.priority == "normal"
    assert arguments.related_order_id is None


def test_create_ticket_node_blocks_without_user_confirmation() -> None:
    creator = FakeTicketCreator()
    update = create_ticket_node(
        {"ticket_fields": make_complete_ticket_fields()},
        creator=creator,
    )

    assert update["ticket_creation_status"] == "blocked"
    assert update["ticket_creation_error_code"] == "TICKET_CONFIRMATION_REQUIRED"
    assert update["ticket_tool_name"] == "create_ticket"
    assert update["ticket_tool_access_level"] == "write"
    assert update["ticket_tool_requires_confirmation"] is True
    assert update["ticket_write_safety_status"] == "confirmation_required"
    assert update["ticket_creation_idempotency_key"] is None
    assert update["final_answer"] == "创建工单前需要先得到用户确认。"
    assert update["node_history"] == ["create_ticket"]
    assert creator.calls == []


def test_create_ticket_node_calls_creator_after_confirmation(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.agents.ticket_agent")
    fields = make_complete_ticket_fields()
    pending_confirmation = build_pending_ticket_confirmation(fields)
    creator = FakeTicketCreator()

    update = create_ticket_node(
        {
            "ticket_actor_id": "demo_user_001",
            "ticket_confirmation_approved": True,
            "pending_ticket_confirmation": pending_confirmation,
        },
        creator=creator,
    )

    assert update["ticket_creation_status"] == "created"
    assert update["ticket_creation_args"]["requester_id"] == "demo_user_001"
    assert update["ticket_creation_args"]["category"] == "complaint"
    assert update["ticket_tool_name"] == "create_ticket"
    assert update["ticket_tool_access_level"] == "write"
    assert update["ticket_tool_requires_confirmation"] is True
    assert update["ticket_write_safety_status"] == "authorized"
    assert update["ticket_creation_idempotency_key"] == pending_confirmation[
        "confirmation_id"
    ]
    assert update["created_ticket"]["ticket_id"] == "T1001"
    assert "工单已创建，工单号：T1001" in update["final_answer"]
    assert update["node_history"] == ["create_ticket"]
    assert len(creator.calls) == 1
    assert creator.idempotency_keys == [pending_confirmation["confirmation_id"]]
    assert "ticket_agent_create_ticket_started category=complaint" in caplog.text
    assert "ticket_agent_create_ticket_finished status=created ticket_id=T1001" in caplog.text
    assert "我要投诉订单 1001，物流一直不动" not in caplog.text


def test_create_ticket_node_authorizes_write_tool_before_calling_creator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_write_tool(tool_name: str, *, user_confirmed: bool = False):
        assert tool_name == "create_ticket"
        assert user_confirmed is True
        raise AppException(
            code="TOOL_NOT_ALLOWED",
            message="工具不在允许列表中，后端已拒绝执行。",
            status_code=403,
        )

    fields = make_complete_ticket_fields()
    pending_confirmation = build_pending_ticket_confirmation(fields)
    creator = FakeTicketCreator()
    monkeypatch.setattr(
        "app.agents.ticket_agent.authorize_tool_call",
        reject_write_tool,
    )

    update = create_ticket_node(
        {
            "ticket_actor_id": "demo_user_001",
            "ticket_confirmation_approved": True,
            "pending_ticket_confirmation": pending_confirmation,
        },
        creator=creator,
    )

    assert update["ticket_creation_status"] == "failed"
    assert update["ticket_creation_error_code"] == "TOOL_NOT_ALLOWED"
    assert update["ticket_tool_name"] == "create_ticket"
    assert update["ticket_tool_access_level"] == "write"
    assert update["ticket_tool_requires_confirmation"] is True
    assert update["ticket_write_safety_status"] == "tool_not_allowed"
    assert update["ticket_creation_idempotency_key"] == pending_confirmation[
        "confirmation_id"
    ]
    assert update["final_answer"] == "工具不在允许列表中，后端已拒绝执行。"
    assert creator.calls == []


def test_create_ticket_node_marks_missing_confirmed_fields_as_safety_block() -> None:
    creator = FakeTicketCreator()

    update = create_ticket_node(
        {
            "ticket_confirmation_approved": True,
        },
        creator=creator,
    )

    assert update["ticket_creation_status"] == "failed"
    assert update["ticket_creation_error_code"] == "TICKET_FIELDS_NOT_FOUND"
    assert update["ticket_tool_name"] == "create_ticket"
    assert update["ticket_tool_access_level"] == "write"
    assert update["ticket_tool_requires_confirmation"] is True
    assert update["ticket_write_safety_status"] == "missing_confirmed_fields"
    assert update["ticket_creation_idempotency_key"] is None
    assert creator.calls == []


def test_create_ticket_node_writes_failure_state_when_creator_fails() -> None:
    creator = FakeTicketCreator(
        error=AppException(
            code="TOOL_UPSTREAM_ERROR",
            message="工单业务服务暂时不可用，请稍后重试。",
            status_code=502,
        )
    )

    update = create_ticket_node(
        {
            "ticket_confirmation_approved": True,
            "ticket_fields": make_complete_ticket_fields(),
        },
        creator=creator,
    )

    assert update["ticket_creation_status"] == "failed"
    assert update["ticket_creation_error_code"] == "TOOL_UPSTREAM_ERROR"
    assert update["ticket_tool_name"] == "create_ticket"
    assert update["ticket_tool_access_level"] == "write"
    assert update["ticket_tool_requires_confirmation"] is True
    assert update["ticket_write_safety_status"] == "authorized"
    assert update["ticket_creation_idempotency_key"]
    assert update["final_answer"] == "工单业务服务暂时不可用，请稍后重试。"
    assert update["node_history"] == ["create_ticket"]
    assert update["fallback_used"] is True
    assert update["agent_error_node"] == "create_ticket"


def test_create_ticket_node_returns_safe_fallback_when_creator_crashes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="app.agents.ticket_agent")
    creator = FakeTicketCreator(error=RuntimeError("database password leaked in stack"))

    update = create_ticket_node(
        {
            "ticket_confirmation_approved": True,
            "ticket_fields": make_complete_ticket_fields(),
        },
        creator=creator,
    )

    assert update["ticket_creation_status"] == "failed"
    assert update["ticket_creation_error_code"] == TICKET_CREATION_UNEXPECTED_ERROR_CODE
    assert update["ticket_creation_error_message"] == TICKET_CREATION_UNEXPECTED_ERROR_MESSAGE
    assert update["ticket_tool_name"] == "create_ticket"
    assert update["ticket_tool_access_level"] == "write"
    assert update["ticket_tool_requires_confirmation"] is True
    assert update["ticket_write_safety_status"] == "authorized"
    assert update["ticket_creation_idempotency_key"]
    assert update["agent_error_code"] == TICKET_CREATION_UNEXPECTED_ERROR_CODE
    assert update["final_answer"] == TICKET_CREATION_UNEXPECTED_ERROR_MESSAGE
    assert update["fallback_used"] is True
    assert "database password" not in update["final_answer"]
    assert update["node_history"] == ["create_ticket"]
    assert len(creator.calls) == 1
    assert (
        "ticket_agent_create_ticket_failed code=TICKET_CREATION_UNEXPECTED_ERROR"
        in caplog.text
    )
    assert "error_type=RuntimeError" in caplog.text
    assert "database password" not in caplog.text


def test_retrieve_policy_node_returns_grounded_rag_answer() -> None:
    update = retrieve_policy_node({"normalized_message": "退款规则是什么？"})

    assert update["rag_query"] == "退款规则是什么？"
    assert update["rag_answer_status"] == "answered"
    assert update["final_answer"] == (
        "根据知识库，退款申请通常需要先核对订单状态和售后条件，"
        "用户可以按退款退货规则提交申请。"
    )
    assert update["rag_citations"][0]["source"] == "refund-return-policy.md"
    assert update["rag_citations"][0]["chunk_id"] == "refund_return_policy_chunk_0001"
    assert update["rag_no_context_reason"] is None
    assert update["rag_suggestions"] == []
    assert update["node_history"] == ["retrieve_policy"]


def test_retrieve_policy_node_returns_no_context_fallback() -> None:
    update = retrieve_policy_node(
        {"normalized_message": "会员等级政策是什么？"},
        service=FakeNoContextPolicyRagService(),
    )

    assert update["rag_query"] == "会员等级政策是什么？"
    assert update["rag_answer_status"] == "no_context"
    assert update["final_answer"] == RAG_NO_CONTEXT_REPLY
    assert update["rag_citations"] == []
    assert update["rag_no_context_reason"] == "no_retrieved_chunks"
    assert update["rag_suggestions"]
    assert update["node_history"] == ["retrieve_policy"]


def test_run_ticket_agent_policy_question_uses_rag_answer_node() -> None:
    result = run_ticket_agent("退款规则是什么？")

    assert result["intent"] == "policy_question"
    assert result["rag_answer_status"] == "answered"
    assert result["needs_ticket"] is False
    assert result["ticket_need_source"] == "rag_answered"
    assert result["rag_citations"][0]["chunk_id"] == "refund_return_policy_chunk_0001"
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "retrieve_policy",
        "decide_ticket_need",
    ]


def test_run_ticket_agent_policy_no_context_enters_ticket_flow() -> None:
    result = run_ticket_agent("会员等级政策是什么？")

    assert result["intent"] == "policy_question"
    assert result["rag_answer_status"] == "no_context"
    assert result["needs_ticket"] is True
    assert result["ticket_need_source"] == "rag_no_context"
    assert result["ticket_fields"] == {
        "issue_type": "policy_gap",
        "order_id": None,
        "description": "用户问题：会员等级政策是什么？；知识库未找到足够资料。",
        "user_request": "补充或人工解释知识库未覆盖问题",
        "urgency": "normal",
        "need_human_review": True,
    }
    assert result["ticket_fields_complete"] is True
    assert result["ticket_confirmation_required"] is True
    assert result["pending_ticket_confirmation"]["status"] == "pending"
    assert (
        result["pending_ticket_confirmation"]["ticket_fields"]
        == result["ticket_fields"]
    )
    assert "请确认是否按以下信息创建" in result["final_answer"]
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "retrieve_policy",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
    ]


def test_run_ticket_agent_missing_order_id_asks_follow_up_question() -> None:
    result = run_ticket_agent("商品破损，帮我处理")

    assert result["intent"] == "ticket_request"
    assert result["needs_ticket"] is True
    assert result["ticket_fields"]["issue_type"] == "complaint"
    assert result["ticket_fields"]["order_id"] is None
    assert result["missing_ticket_fields"] == ["order_id"]
    assert result["ticket_fields_complete"] is False
    assert result["missing_ticket_field_question_fields"] == ["order_id"]
    assert result["final_answer"] == (
        "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。"
    )
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "ask_missing_ticket_fields",
    ]


def test_run_ticket_agent_complete_ticket_fields_requests_confirmation() -> None:
    result = run_ticket_agent("我要投诉订单 1001，物流一直不动")

    assert result["intent"] == "ticket_request"
    assert result["needs_ticket"] is True
    assert result["ticket_fields_complete"] is True
    assert result["ticket_confirmation_required"] is True
    assert result["pending_ticket_confirmation"]["status"] == "pending"
    assert (
        result["pending_ticket_confirmation"]["ticket_fields"]
        == result["ticket_fields"]
    )
    assert "问题类型：投诉/异常处理" in result["final_answer"]
    assert "确认创建" in result["final_answer"]
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
    ]


def test_compiled_graph_node_can_be_invoked_for_node_level_test() -> None:
    graph = build_ticket_agent_graph()

    update = graph.nodes["classify_intent"].invoke({"normalized_message": "你好"})

    assert update["intent"] == "smalltalk"
    assert update["intent_reason"]
    assert update["node_history"] == ["classify_intent"]


def test_build_ticket_agent_graph_uses_injected_fake_rag_service() -> None:
    service = FakePolicyRagService()
    graph = build_ticket_agent_graph(policy_rag_service=service)

    result = graph.invoke(
        {
            "user_message": "退款规则是什么？",
            "node_history": [],
        }
    )

    assert service.queries == ["退款规则是什么？"]
    assert result["intent"] == "policy_question"
    assert result["rag_answer_status"] == "answered"
    assert result["rag_citations"][0]["source"] == "fake-policy.md"
    assert result["needs_ticket"] is False
    assert result["ticket_need_source"] == "rag_answered"
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "retrieve_policy",
        "decide_ticket_need",
    ]


def test_build_ticket_agent_graph_uses_fake_rag_no_context_ticket_flow() -> None:
    service = FakeNoContextPolicyRagService()
    graph = build_ticket_agent_graph(policy_rag_service=service)

    result = graph.invoke(
        {
            "user_message": "会员等级政策是什么？",
            "node_history": [],
        }
    )

    assert service.queries == ["会员等级政策是什么？"]
    assert result["intent"] == "policy_question"
    assert result["rag_answer_status"] == "no_context"
    assert result["needs_ticket"] is True
    assert result["ticket_need_source"] == "rag_no_context"
    assert result["ticket_fields"]["issue_type"] == "policy_gap"
    assert result["ticket_fields_complete"] is True
    assert result["ticket_confirmation_required"] is True
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "retrieve_policy",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
    ]


def test_checkpointed_graph_can_resume_partial_execution_after_classify() -> None:
    graph = build_checkpointed_ticket_agent_graph(ticket_creator=FakeTicketCreator())
    config = build_ticket_agent_thread_config("ticket-partial-001")

    graph.update_state(
        config,
        {
            "user_message": "我要投诉订单 1001，物流一直不动",
            "normalized_message": "我要投诉订单 1001，物流一直不动",
            "intent": "ticket_request",
            "node_history": ["normalize_user_input", "classify_intent"],
        },
        as_node="classify_intent",
    )
    result = graph.invoke(
        None,
        config=config,
        interrupt_after=["extract_ticket_fields"],
    )
    snapshot = graph.get_state(config)

    assert result["needs_ticket"] is True
    assert result["ticket_fields"]["order_id"] == "1001"
    assert result["ticket_fields_complete"] is True
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
    ]
    assert snapshot.next == ("request_ticket_confirmation",)


def test_graph_executes_ticket_creation_when_confirmation_is_approved() -> None:
    creator = FakeTicketCreator()
    graph = build_ticket_agent_graph(ticket_creator=creator)

    result = graph.invoke(
        {
            "user_message": "我要投诉订单 1001，物流一直不动",
            "ticket_actor_id": "demo_user_001",
            "ticket_confirmation_approved": True,
            "node_history": [],
        }
    )

    assert result["ticket_confirmation_required"] is True
    assert result["ticket_creation_status"] == "created"
    assert result["created_ticket"]["ticket_id"] == "T1001"
    assert result["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
        "create_ticket",
    ]
    assert len(creator.calls) == 1


def test_checkpointed_graph_saves_pending_confirmation_by_thread_id() -> None:
    graph = build_checkpointed_ticket_agent_graph(ticket_creator=FakeTicketCreator())

    result = run_ticket_agent_in_thread(
        graph,
        "我要投诉订单 1001，物流一直不动",
        thread_id="ticket-thread-001",
        actor_id="demo_user_001",
    )
    saved_state = get_ticket_agent_thread_state(
        graph,
        thread_id="ticket-thread-001",
    )

    assert result["pending_ticket_confirmation"]["status"] == "pending"
    assert saved_state["pending_ticket_confirmation"] == result[
        "pending_ticket_confirmation"
    ]
    assert saved_state["ticket_actor_id"] == "demo_user_001"
    assert saved_state["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
    ]


def test_checkpointed_graph_resumes_from_confirmation_to_create_ticket() -> None:
    creator = FakeTicketCreator()
    graph = build_checkpointed_ticket_agent_graph(ticket_creator=creator)
    thread_id = "ticket-thread-002"
    run_ticket_agent_in_thread(
        graph,
        "我要投诉订单 1001，物流一直不动",
        thread_id=thread_id,
        actor_id="demo_user_001",
    )

    resumed = approve_ticket_confirmation_and_resume(
        graph,
        thread_id=thread_id,
        actor_id="demo_user_001",
    )

    assert resumed["ticket_confirmation_approved"] is True
    assert resumed["ticket_creation_status"] == "created"
    assert resumed["created_ticket"]["ticket_id"] == "T1001"
    assert resumed["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
        "create_ticket",
    ]
    assert len(creator.calls) == 1


def test_checkpointed_graph_keeps_thread_states_isolated() -> None:
    graph = build_checkpointed_ticket_agent_graph(ticket_creator=FakeTicketCreator())

    run_ticket_agent_in_thread(
        graph,
        "我要投诉订单 1001，物流一直不动",
        thread_id="ticket-thread-isolated-001",
    )
    other_state = get_ticket_agent_thread_state(
        graph,
        thread_id="ticket-thread-isolated-002",
    )

    assert other_state == {}


def test_resume_without_pending_confirmation_returns_business_error() -> None:
    graph = build_checkpointed_ticket_agent_graph(ticket_creator=FakeTicketCreator())

    with pytest.raises(AppException) as exc_info:
        approve_ticket_confirmation_and_resume(
            graph,
            thread_id="ticket-thread-empty",
        )

    assert exc_info.value.code == "TICKET_CONFIRMATION_NOT_FOUND"
    assert exc_info.value.message == TICKET_CONFIRMATION_NOT_FOUND_MESSAGE


def test_interrupting_graph_pauses_for_ticket_confirmation() -> None:
    graph = build_interrupting_ticket_agent_graph(ticket_creator=FakeTicketCreator())

    result = run_ticket_agent_in_thread(
        graph,
        "我要投诉订单 1001，物流一直不动",
        thread_id="ticket-interrupt-001",
        actor_id="demo_user_001",
    )
    payload = get_ticket_confirmation_interrupt_payload(result)
    snapshot = graph.get_state(
        build_ticket_agent_thread_config("ticket-interrupt-001")
    )

    assert payload["kind"] == "ticket_confirmation"
    assert payload["pending_ticket_confirmation"]["status"] == "pending"
    assert "确认创建" in payload["message"]
    assert snapshot.next == ("request_ticket_confirmation",)
    assert snapshot.values["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
    ]


def test_interrupting_graph_resumes_approved_confirmation_to_create_ticket() -> None:
    creator = FakeTicketCreator()
    graph = build_interrupting_ticket_agent_graph(ticket_creator=creator)
    thread_id = "ticket-interrupt-002"
    result = run_ticket_agent_in_thread(
        graph,
        "我要投诉订单 1001，物流一直不动",
        thread_id=thread_id,
        actor_id="demo_user_001",
    )
    payload = get_ticket_confirmation_interrupt_payload(result)

    resumed = resume_ticket_confirmation_interrupt(
        graph,
        thread_id=thread_id,
        approved=True,
        actor_id="demo_user_001",
    )

    assert resumed["ticket_confirmation_approved"] is True
    assert resumed["pending_ticket_confirmation"]["confirmation_id"] == payload[
        "confirmation_id"
    ]
    assert resumed["ticket_creation_status"] == "created"
    assert resumed["created_ticket"]["ticket_id"] == "T1001"
    assert resumed["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
        "create_ticket",
    ]
    assert len(creator.calls) == 1


def test_interrupting_graph_resumes_rejected_confirmation_without_creation() -> None:
    creator = FakeTicketCreator()
    graph = build_interrupting_ticket_agent_graph(ticket_creator=creator)
    thread_id = "ticket-interrupt-003"
    run_ticket_agent_in_thread(
        graph,
        "我要投诉订单 1001，物流一直不动",
        thread_id=thread_id,
        actor_id="demo_user_001",
    )

    resumed = resume_ticket_confirmation_interrupt(
        graph,
        thread_id=thread_id,
        approved=False,
    )

    assert resumed["ticket_confirmation_approved"] is False
    assert resumed["final_answer"] == TICKET_CONFIRMATION_REJECTED_MESSAGE
    assert "ticket_creation_status" not in resumed
    assert creator.calls == []
    assert resumed["node_history"] == [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation",
    ]


def test_interrupting_graph_reissues_confirmation_after_ticket_correction() -> None:
    creator = FakeTicketCreator()
    graph = build_interrupting_ticket_agent_graph(ticket_creator=creator)
    thread_id = "ticket-correction-001"
    result = run_ticket_agent_in_thread(
        graph,
        "我要投诉订单 A1001，物流一直没有更新。",
        thread_id=thread_id,
        actor_id="demo_user_001",
    )
    old_confirmation_id = get_ticket_confirmation_interrupt_payload(result)["confirmation_id"]
    corrected_fields = make_complete_ticket_fields() | {
        "order_id": "A1002",
        "description": "订单 A1002 的物流已经三天没有更新。",
        "urgency": "high",
    }

    corrected = resume_ticket_confirmation_interrupt(
        graph,
        thread_id=thread_id,
        approved=False,
        actor_id="demo_user_001",
        corrected_fields=corrected_fields,
    )
    payload = get_ticket_confirmation_interrupt_payload(corrected)

    assert payload["confirmation_id"] != old_confirmation_id
    assert payload["pending_ticket_confirmation"]["ticket_fields"] == corrected_fields
    assert creator.calls == []


def test_interrupting_graph_merges_follow_up_order_id_into_pending_ticket() -> None:
    graph = build_interrupting_ticket_agent_graph(ticket_creator=FakeTicketCreator())
    thread_id = "ticket-follow-up-001"
    initial_message = "我要投诉物流问题，需要人工处理。"

    first_result = run_ticket_agent_in_thread(
        graph,
        initial_message,
        thread_id=thread_id,
        actor_id="demo_user_001",
    )
    assert first_result["missing_ticket_fields"] == ["order_id"]

    follow_up_result = run_ticket_agent_in_thread(
        graph,
        "A1001",
        thread_id=thread_id,
        actor_id="demo_user_001",
    )
    payload = get_ticket_confirmation_interrupt_payload(follow_up_result)
    fields = payload["pending_ticket_confirmation"]["ticket_fields"]

    assert fields["order_id"] == "A1001"
    assert fields["issue_type"] == "complaint"
    assert fields["description"] == initial_message


def test_get_ticket_confirmation_interrupt_payload_requires_interrupt_result() -> None:
    with pytest.raises(AppException) as exc_info:
        get_ticket_confirmation_interrupt_payload({"final_answer": "ok"})

    assert exc_info.value.code == "TICKET_CONFIRMATION_INTERRUPT_NOT_FOUND"
    assert exc_info.value.message == TICKET_CONFIRMATION_INTERRUPT_NOT_FOUND_MESSAGE


def test_resume_ticket_confirmation_interrupt_safely_handles_invalid_thread_id() -> None:
    graph = build_interrupting_ticket_agent_graph(ticket_creator=FakeTicketCreator())

    result = resume_ticket_confirmation_interrupt_safely(
        graph,
        thread_id="   ",
        approved=True,
    )

    assert result["agent_error_code"] == TICKET_THREAD_ID_INVALID_ERROR_CODE
    assert result["agent_error_message"] == "thread_id 不能为空。"
    assert result["agent_error_node"] == "resume_ticket_confirmation_interrupt"
    assert result["fallback_used"] is True
    assert result["final_answer"] == "thread_id 不能为空。"
    assert result["node_history"] == ["resume_ticket_confirmation_interrupt"]


def test_resume_ticket_confirmation_interrupt_safely_handles_unexpected_error() -> None:
    result = resume_ticket_confirmation_interrupt_safely(
        BrokenTicketAgentGraph(RuntimeError("checkpoint store crashed")),
        thread_id="ticket-interrupt-error",
        approved=True,
    )

    assert result["agent_error_code"] == TICKET_AGENT_FALLBACK_ERROR_CODE
    assert result["agent_error_message"] == TICKET_AGENT_FALLBACK_MESSAGE
    assert result["agent_error_node"] == "resume_ticket_confirmation_interrupt"
    assert result["fallback_used"] is True
    assert result["final_answer"] == TICKET_AGENT_FALLBACK_MESSAGE


@pytest.mark.parametrize(
    ("message", "expected_intent", "expected_node_history"),
    [
        (
            "退款规则是什么？",
            "policy_question",
            [
                "normalize_user_input",
                "classify_intent",
                "retrieve_policy",
                "decide_ticket_need",
            ],
        ),
        (
            "我的订单 1001 到哪了？",
            "order_query",
            ["normalize_user_input", "classify_intent", "query_order"],
        ),
        (
            "我要投诉订单 1001",
            "ticket_request",
            [
                "normalize_user_input",
                "classify_intent",
                "decide_ticket_need",
                "extract_ticket_fields",
                "request_ticket_confirmation",
            ],
        ),
        (
            "你好",
            "smalltalk",
            ["normalize_user_input", "classify_intent", "build_direct_answer"],
        ),
        (
            "帮我直接退款到账",
            "unsupported",
            ["normalize_user_input", "classify_intent", "build_unsupported_answer"],
        ),
        (
            "这个怎么办",
            "unclear",
            ["normalize_user_input", "classify_intent", "ask_clarifying_question"],
        ),
    ],
)
def test_run_ticket_agent_routes_to_expected_business_path(
    message: str,
    expected_intent: str,
    expected_node_history: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.agents.ticket_agent.execute_ticket_order_query",
        fake_execute_ticket_order_query,
    )

    result = run_ticket_agent(message)

    assert result["intent"] == expected_intent
    assert result["final_answer"]
    assert result["node_history"] == expected_node_history


def test_run_ticket_agent_safely_returns_normal_result_when_graph_succeeds(
    caplog: pytest.LogCaptureFixture,
) -> None:
    install_trace_id_log_record_factory()
    caplog.set_level(logging.INFO, logger="app.agents.ticket_agent")
    token = set_trace_id("trace-agent-safe-001")

    try:
        result = run_ticket_agent_safely("你好")
    finally:
        reset_trace_id(token)

    assert result["intent"] == "smalltalk"
    assert result["agent_trace_id"] == "trace-agent-safe-001"
    assert result["final_answer"] == (
        "你好，我是智能客服工单助手，可以帮你查询规则、订单和创建客服工单。"
    )
    assert "fallback_used" not in result
    assert (
        "ticket_agent_started operation=invoke_safe thread_id=- actor_id=- message_length=2"
        in caplog.text
    )
    assert "ticket_agent_finished operation=invoke_safe thread_id=-" in caplog.text
    assert "last_node=build_direct_answer" in caplog.text
    assert "你好" not in caplog.text
    trace_ids = [
        record.trace_id
        for record in caplog.records
        if record.name == "app.agents.ticket_agent"
    ]
    assert trace_ids
    assert all(trace_id == "trace-agent-safe-001" for trace_id in trace_ids)


def test_run_ticket_agent_safely_converts_app_exception_to_fallback_state() -> None:
    result = run_ticket_agent_safely(
        "我要创建工单",
        graph=BrokenTicketAgentGraph(
            AppException(
                code="GRAPH_BUSINESS_ERROR",
                message="业务流程暂时不可用。",
                status_code=409,
            )
        ),
    )

    assert result["agent_error_code"] == "GRAPH_BUSINESS_ERROR"
    assert result["agent_error_message"] == "业务流程暂时不可用。"
    assert result["agent_error_node"] == "ticket_agent_graph"
    assert result["fallback_used"] is True
    assert result["final_answer"] == "业务流程暂时不可用。"


def test_run_ticket_agent_safely_converts_unexpected_error_to_fallback_state(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="app.agents.ticket_agent")
    result = run_ticket_agent_safely(
        "我要创建工单",
        graph=BrokenTicketAgentGraph(RuntimeError("internal stack trace")),
    )

    assert result["agent_error_code"] == TICKET_AGENT_FALLBACK_ERROR_CODE
    assert result["agent_error_message"] == TICKET_AGENT_FALLBACK_MESSAGE
    assert result["agent_error_node"] == "ticket_agent_graph"
    assert result["fallback_used"] is True
    assert result["final_answer"] == TICKET_AGENT_FALLBACK_MESSAGE
    assert "internal stack trace" not in result["final_answer"]
    assert "ticket_agent_failed operation=invoke_safe" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert "internal stack trace" not in caplog.text


def test_stream_ticket_agent_updates_exposes_intent_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.agents.ticket_agent.execute_ticket_order_query",
        fake_execute_ticket_order_query,
    )

    chunks = stream_ticket_agent_updates("我的订单 1001 到哪了？")

    assert chunks[0]["data"] == {
        "normalize_user_input": {
            "normalized_message": "我的订单 1001 到哪了？",
            "node_history": ["normalize_user_input"],
        }
    }
    assert chunks[1]["data"]["classify_intent"]["intent"] == "order_query"
    query_order_update = chunks[2]["data"]["query_order"]
    assert query_order_update["order_query_order_id"] == "1001"
    assert query_order_update["order_query_status"] == "succeeded"
    assert query_order_update["order_query_result"]["order_id"] == "1001"
    assert query_order_update["order_query_result"]["source"] == "java_mock_service"
    assert "查询到订单 1001" in query_order_update["final_answer"]
    assert query_order_update["node_history"] == ["query_order"]


def test_stream_ticket_agent_updates_exposes_rag_answer_update() -> None:
    chunks = stream_ticket_agent_updates("账号安全怎么验证？")

    policy_update = chunks[2]["data"]["retrieve_policy"]
    assert policy_update["rag_answer_status"] == "answered"
    assert policy_update["rag_citations"][0]["source"] == "account-security-faq.md"
    assert policy_update["node_history"] == ["retrieve_policy"]


def test_stream_ticket_agent_updates_exposes_ticket_need_decision() -> None:
    chunks = stream_ticket_agent_updates("退款规则是什么？")

    decision_update = chunks[3]["data"]["decide_ticket_need"]
    assert decision_update == {
        "needs_ticket": False,
        "ticket_need_reason": "知识库已给出可引用回答，当前不需要创建工单。",
        "ticket_need_source": "rag_answered",
        "node_history": ["decide_ticket_need"],
    }


def test_stream_ticket_agent_updates_exposes_ticket_field_extraction() -> None:
    chunks = stream_ticket_agent_updates("我要投诉订单 1001，物流一直不动")

    extraction_update = chunks[3]["data"]["extract_ticket_fields"]
    assert extraction_update["ticket_fields"]["issue_type"] == "complaint"
    assert extraction_update["ticket_fields"]["order_id"] == "1001"
    assert extraction_update["missing_ticket_fields"] == []
    assert extraction_update["ticket_fields_complete"] is True
    assert extraction_update["node_history"] == ["extract_ticket_fields"]


def test_stream_ticket_agent_updates_exposes_ticket_confirmation_request() -> None:
    chunks = stream_ticket_agent_updates("我要投诉订单 1001，物流一直不动")

    confirmation_update = chunks[4]["data"]["request_ticket_confirmation"]
    assert confirmation_update["ticket_confirmation_required"] is True
    assert (
        confirmation_update["pending_ticket_confirmation"]["status"]
        == "pending"
    )
    assert "问题类型：投诉/异常处理" in confirmation_update["final_answer"]
    assert confirmation_update["node_history"] == ["request_ticket_confirmation"]


def test_stream_ticket_agent_updates_exposes_missing_field_question() -> None:
    chunks = stream_ticket_agent_updates("商品破损，帮我处理")

    question_update = chunks[4]["data"]["ask_missing_ticket_fields"]
    assert question_update == {
        "missing_ticket_field_question": (
            "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。"
        ),
        "missing_ticket_field_question_fields": ["order_id"],
        "final_answer": "请补充相关订单号（例如 1001 或 A1001），这样我才能继续为你整理工单。",
        "node_history": ["ask_missing_ticket_fields"],
    }


def test_build_ticket_agent_input_returns_initial_state() -> None:
    token = set_trace_id("trace-agent-input-001")

    try:
        assert build_ticket_agent_input("hello") == {
            "user_message": "hello",
            "agent_trace_id": "trace-agent-input-001",
            "node_history": [],
        }
    finally:
        reset_trace_id(token)


def test_build_ticket_agent_thread_config_requires_non_empty_thread_id() -> None:
    assert build_ticket_agent_thread_config(" ticket-thread-001 ") == {
        "configurable": {"thread_id": "ticket-thread-001"}
    }

    with pytest.raises(ValueError, match="thread_id 不能为空"):
        build_ticket_agent_thread_config("   ")


def test_ask_clarifying_question_node_returns_final_answer() -> None:
    update = ask_clarifying_question_node({})

    assert update == {
        "final_answer": "我还不能确定你要处理的问题，请补充订单号、问题类型或具体诉求。",
        "node_history": ["ask_clarifying_question"],
    }
