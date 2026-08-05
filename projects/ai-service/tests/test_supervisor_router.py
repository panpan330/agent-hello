import pytest

from app.agents.supervisor.supervisor_router import (
    FakeLLMSupervisorRouter,
    LLMSupervisorRouter,
    RuleSupervisorRouter,
    SupervisorRoute,
    SupervisorRouter,
    TICKET_INTENT_TO_SUPERVISOR_ROUTE,
    create_supervisor_router,
)
from app.core.config import Settings

# NOTE(适配说明): 简报原测试从 app.schemas.structured 导入 TicketIntent 并遍历之；
# 但该模块的 TicketIntent 是旧结构化输出功能的 5 值 StrEnum
# (refund/order_query/logistics/complaint/unknown)，与 ticket-agent 的 6 值意图
# (policy_question/order_query/ticket_request/smalltalk/unsupported/unclear)
# 并非同一概念。因此 "映射覆盖全部意图" 断言改为对映射键集合的精确校验
# （语义与简报意图等价），详见 task-3-report.md。


def test_route_enum_has_six_values() -> None:
    values = {route.value for route in SupervisorRoute}
    assert values == {
        "knowledge_question",
        "order_query",
        "ticket_request",
        "smalltalk",
        "unsupported",
        "unclear",
    }


def test_ticket_intent_mapping_covers_all_intents() -> None:
    assert set(TICKET_INTENT_TO_SUPERVISOR_ROUTE) == {
        "policy_question",
        "order_query",
        "ticket_request",
        "smalltalk",
        "unsupported",
        "unclear",
    }


def test_rule_router_classifies_order_query() -> None:
    router = RuleSupervisorRouter()
    assert router.route("查一下我的订单 A1001 物流") == SupervisorRoute.ORDER_QUERY


def test_rule_router_classifies_policy_question() -> None:
    router = RuleSupervisorRouter()
    assert router.route("退货政策是什么") == SupervisorRoute.KNOWLEDGE_QUESTION


def test_rule_router_classifies_ticket_request() -> None:
    router = RuleSupervisorRouter()
    assert router.route("我要申请退款工单") == SupervisorRoute.TICKET_REQUEST


def test_rule_router_falls_back_to_unclear_for_unknown() -> None:
    router = RuleSupervisorRouter()
    assert router.route("今天天气怎么样啊") in {
        SupervisorRoute.UNCLEAR,
        SupervisorRoute.SMALLTALK,
    }


def test_fake_llm_router_returns_configured_route() -> None:
    fake = FakeLLMSupervisorRouter(SupervisorRoute.TICKET_REQUEST)
    router: SupervisorRouter = fake
    assert router.route("anything") == SupervisorRoute.TICKET_REQUEST


def test_create_router_returns_rule_by_default() -> None:
    router = create_supervisor_router(Settings(_env_file=None))
    assert isinstance(router, RuleSupervisorRouter)


def test_create_router_returns_llm_when_configured() -> None:
    router = create_supervisor_router(
        Settings(_env_file=None, supervisor_router_mode="llm")
    )
    assert isinstance(router, LLMSupervisorRouter)
