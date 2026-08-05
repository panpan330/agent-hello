import hashlib
import json
import logging
from datetime import datetime, timezone
from time import time_ns
from typing import Protocol
from uuid import uuid4
from threading import Lock

from redis import Redis
from redis.exceptions import RedisError
from pydantic import ValidationError

from app.core.ai_security_boundary import redact_sensitive_text
from app.core.config import Settings
from app.schemas.console_agent import (
    ConsoleAgentConversation,
    ConsoleAgentConversationMessage,
    ConsoleAgentConversationSummary,
    ConsoleAgentResponse,
)


logger = logging.getLogger(__name__)
MAX_CONVERSATION_MESSAGES = 100


class ConversationActor(Protocol):
    user_id: str
    tenant_id: str


class ConsoleAgentConversationStore:
    """Redis store for the client-visible transcript, separate from LangGraph checkpoints."""

    def __init__(self, settings: Settings, *, client: Redis | None = None) -> None:
        self._settings = settings
        self._client = client or Redis.from_url(
            settings.resolved_agent_redis_url,
            decode_responses=True,
        )
        self._score_lock = Lock()
        self._last_index_score = 0.0

    def close(self) -> None:
        self._client.close()

    def append_exchange(
        self,
        *,
        actor: ConversationActor,
        conversation_id: str,
        user_message: str,
        response: ConsoleAgentResponse,
    ) -> None:
        conversation = self.get(actor=actor, conversation_id=conversation_id)
        now = datetime.now(timezone.utc)
        messages = list(conversation.messages) if conversation is not None else []
        messages.extend(
            [
                ConsoleAgentConversationMessage(
                    id=uuid4().hex,
                    role="user",
                    content=redact_sensitive_text(user_message),
                    created_at=now,
                ),
                ConsoleAgentConversationMessage(
                    id=uuid4().hex,
                    role="assistant",
                    content=redact_sensitive_text(response.reply),
                    created_at=now,
                    trace_id=response.trace_id,
                    route=response.route,
                    citations=response.citations,
                    suggestions=[redact_sensitive_text(item) for item in response.suggestions],
                    pending_ticket_confirmation=response.pending_ticket_confirmation,
                    created_ticket=response.created_ticket,
                    human_handoff=response.human_handoff,
                ),
            ]
        )
        stored = ConsoleAgentConversation(
            conversation_id=conversation_id,
            title=conversation.title if conversation is not None else _build_title(user_message),
            updated_at=now,
            messages=messages[-MAX_CONVERSATION_MESSAGES:],
        )
        self._save(actor=actor, conversation=stored)

    def list_recent(
        self,
        *,
        actor: ConversationActor,
        limit: int,
    ) -> list[ConsoleAgentConversationSummary]:
        conversation_ids = self._client.zrevrange(self._index_key(actor), 0, limit - 1)
        summaries: list[ConsoleAgentConversationSummary] = []
        stale_ids: list[str] = []
        for conversation_id in conversation_ids:
            conversation = self.get(actor=actor, conversation_id=conversation_id)
            if conversation is None:
                stale_ids.append(conversation_id)
                continue
            summaries.append(
                ConsoleAgentConversationSummary(
                    conversation_id=conversation.conversation_id,
                    title=conversation.title,
                    updated_at=conversation.updated_at,
                )
            )
        if stale_ids:
            self._client.zrem(self._index_key(actor), *stale_ids)
        return summaries

    def set_assistant_feedback(
        self,
        *,
        actor: ConversationActor,
        conversation_id: str,
        trace_id: str,
        rating: str,
        reason: str | None,
    ) -> bool:
        conversation = self.get(actor=actor, conversation_id=conversation_id)
        if conversation is None:
            return False
        messages = list(conversation.messages)
        for index in range(len(messages) - 1, -1, -1):
            message = messages[index]
            if message.role == "assistant" and message.trace_id == trace_id:
                messages[index] = message.model_copy(
                    update={"feedback_rating": rating, "feedback_reason": reason}
                )
                self._save(
                    actor=actor,
                    conversation=conversation.model_copy(
                        update={"messages": messages, "updated_at": datetime.now(timezone.utc)}
                    ),
                )
                return True
        return False

    def get(
        self,
        *,
        actor: ConversationActor,
        conversation_id: str,
    ) -> ConsoleAgentConversation | None:
        raw = self._client.get(self._conversation_key(actor, conversation_id))
        if raw is None:
            return None
        try:
            return ConsoleAgentConversation.model_validate_json(raw)
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("console_agent_conversation_record_invalid error_type=%s", type(exc).__name__)
            return None

    def _save(self, *, actor: ConversationActor, conversation: ConsoleAgentConversation) -> None:
        ttl_seconds = self._settings.agent_checkpoint_ttl_minutes * 60
        conversation_key = self._conversation_key(actor, conversation.conversation_id)
        index_key = self._index_key(actor)
        payload = conversation.model_dump_json()
        with self._client.pipeline(transaction=True) as pipeline:
            pipeline.set(conversation_key, payload, ex=ttl_seconds)
            pipeline.zadd(index_key, {conversation.conversation_id: self._next_index_score()})
            pipeline.expire(index_key, ttl_seconds)
            pipeline.execute()

    def _conversation_key(self, actor: ConversationActor, conversation_id: str) -> str:
        return f"{self._prefix}:conversation:{self._digest(actor, conversation_id)}"

    def _index_key(self, actor: ConversationActor) -> str:
        return f"{self._prefix}:conversation-index:{self._digest(actor)}"

    @property
    def _prefix(self) -> str:
        return self._settings.resolved_agent_checkpoint_key_prefix

    @staticmethod
    def _digest(actor: ConversationActor, conversation_id: str = "") -> str:
        payload = f"{actor.tenant_id}\x1f{actor.user_id}\x1f{conversation_id}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _next_index_score(self) -> float:
        with self._score_lock:
            candidate = time_ns() / 1_000_000_000
            self._last_index_score = max(candidate, self._last_index_score + 0.001)
            return self._last_index_score


def _build_title(user_message: str) -> str:
    normalized = " ".join(redact_sensitive_text(user_message).split())
    return (normalized[:117] + "...") if len(normalized) > 120 else normalized or "新会话"
