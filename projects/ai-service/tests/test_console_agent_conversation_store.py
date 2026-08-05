from app.core.config import Settings
from app.schemas.console_agent import ConsoleAgentResponse
from app.services.console_agent_conversation_store import ConsoleAgentConversationStore
from app.services.console_agent_service import ConsoleAgentActor


class FakeRedisPipeline:
    def __init__(self, redis: "FakeRedis") -> None:
        self.redis = redis

    def __enter__(self) -> "FakeRedisPipeline":
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def set(self, key: str, value: str, *, ex: int) -> "FakeRedisPipeline":
        self.redis.values[key] = value
        self.redis.expirations[key] = ex
        return self

    def zadd(self, key: str, values: dict[str, float]) -> "FakeRedisPipeline":
        self.redis.sorted_sets.setdefault(key, {}).update(values)
        return self

    def expire(self, key: str, seconds: int) -> "FakeRedisPipeline":
        self.redis.expirations[key] = seconds
        return self

    def execute(self) -> None:
        pass


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.sorted_sets: dict[str, dict[str, float]] = {}
        self.expirations: dict[str, int] = {}

    def close(self) -> None:
        pass

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def zrevrange(self, key: str, start: int, end: int) -> list[str]:
        values = self.sorted_sets.get(key, {})
        ordered = [item[0] for item in sorted(values.items(), key=lambda item: item[1], reverse=True)]
        return ordered[start : end + 1]

    def zrem(self, key: str, *members: str) -> None:
        values = self.sorted_sets.get(key, {})
        for member in members:
            values.pop(member, None)

    def pipeline(self, *, transaction: bool) -> FakeRedisPipeline:
        assert transaction is True
        return FakeRedisPipeline(self)


def _response(conversation_id: str, reply: str) -> ConsoleAgentResponse:
    return ConsoleAgentResponse(
        reply=reply,
        conversation_id=conversation_id,
        trace_id=f"trace-{conversation_id}",
        route="order_query",
    )


def test_store_persists_only_owner_visible_messages_and_recent_summaries() -> None:
    redis = FakeRedis()
    settings = Settings(
        _env_file=None,
        agent_redis_url="redis://redis.example:6379/0",
        agent_checkpoint_ttl_minutes=45,
        agent_checkpoint_key_prefix="test-agent",
    )
    store = ConsoleAgentConversationStore(settings, client=redis)  # type: ignore[arg-type]
    owner = ConsoleAgentActor(user_id="U1001", tenant_id="default", roles=("customer",))
    another_user = ConsoleAgentActor(user_id="U2001", tenant_id="default", roles=("customer",))

    store.append_exchange(
        actor=owner,
        conversation_id="conversation-001",
        user_message="Please check order A1001.",
        response=_response("conversation-001", "Order A1001 is in transit."),
    )
    store.append_exchange(
        actor=owner,
        conversation_id="conversation-002",
        user_message="I need refund help.",
        response=_response("conversation-002", "I can help with the refund policy."),
    )

    conversation = store.get(actor=owner, conversation_id="conversation-001")

    assert conversation is not None
    assert [message.role for message in conversation.messages] == ["user", "assistant"]
    assert conversation.messages[1].trace_id == "trace-conversation-001"
    assert store.get(actor=another_user, conversation_id="conversation-001") is None
    assert [item.conversation_id for item in store.list_recent(actor=owner, limit=20)] == [
        "conversation-002",
        "conversation-001",
    ]
    assert store.list_recent(actor=another_user, limit=20) == []
    assert set(redis.expirations.values()) == {45 * 60}


def test_store_keeps_existing_transcript_when_appending_new_exchange() -> None:
    redis = FakeRedis()
    store = ConsoleAgentConversationStore(
        Settings(_env_file=None, agent_redis_url="redis://redis.example:6379/0"),
        client=redis,  # type: ignore[arg-type]
    )
    actor = ConsoleAgentActor(user_id="U1001", tenant_id="default", roles=("customer",))

    store.append_exchange(
        actor=actor,
        conversation_id="conversation-001",
        user_message="First question",
        response=_response("conversation-001", "First answer"),
    )
    store.append_exchange(
        actor=actor,
        conversation_id="conversation-001",
        user_message="Second question",
        response=_response("conversation-001", "Second answer"),
    )

    conversation = store.get(actor=actor, conversation_id="conversation-001")

    assert conversation is not None
    assert [message.content for message in conversation.messages] == [
        "First question",
        "First answer",
        "Second question",
        "Second answer",
    ]
