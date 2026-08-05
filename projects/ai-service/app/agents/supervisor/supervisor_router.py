"""Supervisor routing: rule-based and LLM-based intent routing for the multi-agent system."""

from enum import StrEnum
import logging
from typing import Any, Protocol

from app.agents.ticket_agent import (
    LLMTicketIntentClassifier,
    TICKET_INTENT_CLASSIFICATION_PROMPT,
    classify_ticket_intent,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.schemas.structured import TicketIntent


logger = logging.getLogger(__name__)


class SupervisorRoute(StrEnum):
    KNOWLEDGE_QUESTION = "knowledge_question"
    ORDER_QUERY = "order_query"
    TICKET_REQUEST = "ticket_request"
    SMALLTALK = "smalltalk"
    UNSUPPORTED = "unsupported"
    UNCLEAR = "unclear"


TICKET_INTENT_TO_SUPERVISOR_ROUTE: dict[TicketIntent, SupervisorRoute] = {
    "policy_question": SupervisorRoute.KNOWLEDGE_QUESTION,
    "order_query": SupervisorRoute.ORDER_QUERY,
    "ticket_request": SupervisorRoute.TICKET_REQUEST,
    "smalltalk": SupervisorRoute.SMALLTALK,
    "unsupported": SupervisorRoute.UNSUPPORTED,
    "unclear": SupervisorRoute.UNCLEAR,
}


class SupervisorRouter(Protocol):
    def route(self, message: str) -> SupervisorRoute:
        """Route a user message to a supervisor route."""
        ...


class RuleSupervisorRouter:
    def route(self, message: str) -> SupervisorRoute:
        classification = classify_ticket_intent(message)
        intent = classification["intent"]
        if intent == "unsupported":
            # 规则分类器将天气/写小说等话题判为"超出客服 Agent 安全业务范围"；
            # 监督路由层将其视为无法分配给任何 worker 的请求，回退 UNCLEAR 以引导澄清
            # （对应 test_rule_router_falls_back_to_unclear_for_unknown 的语义）。
            return SupervisorRoute.UNCLEAR
        return TICKET_INTENT_TO_SUPERVISOR_ROUTE.get(
            intent, SupervisorRoute.UNCLEAR
        )


class LLMSupervisorRouter:
    """LLM-based supervisor router. Reuses LLMTicketIntentClassifier for the
    model call, mapping its intent output to a SupervisorRoute."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: Any | None = None,
        prompt_spec: Any = None,
    ) -> None:
        self._settings = settings
        self._classifier = LLMTicketIntentClassifier(
            settings,
            client=client,
            prompt_spec=(
                prompt_spec
                if prompt_spec is not None
                else TICKET_INTENT_CLASSIFICATION_PROMPT
            ),
        )

    def route(self, message: str) -> SupervisorRoute:
        classification = self._classifier.classify_intent(message)
        return TICKET_INTENT_TO_SUPERVISOR_ROUTE.get(
            classification["intent"], SupervisorRoute.UNCLEAR
        )

    def route_with_fallback(self, message: str) -> tuple[SupervisorRoute, str]:
        """Return (route, source) where source is 'llm' or 'rule_fallback'."""
        try:
            return self.route(message), "llm"
        except AppException as exc:
            logger.warning(
                "supervisor_llm_route_failed code=%s falling_back_to_rule",
                exc.code,
            )
            return RuleSupervisorRouter().route(message), "rule_fallback"


class FakeLLMSupervisorRouter:
    def __init__(self, route: SupervisorRoute) -> None:
        self._route = route

    def route(self, message: str) -> SupervisorRoute:
        return self._route


def create_supervisor_router(
    settings: Settings | None = None,
    *,
    client: Any | None = None,
) -> SupervisorRouter:
    resolved_settings = settings or get_settings()
    if resolved_settings.resolved_supervisor_router_mode == "llm":
        return LLMSupervisorRouter(resolved_settings, client=client)
    return RuleSupervisorRouter()
