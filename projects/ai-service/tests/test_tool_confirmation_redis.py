from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import Settings
from app.core.exceptions import AppException
from app.schemas.tool_confirmation import ToolConfirmationStatus
from app.tools.tool_confirmation import (
    RedisToolConfirmationStore,
    create_tool_confirmation_store,
)


class FakeRedisClient:
    """Minimal dict-backed redis client with the methods the store uses."""

    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.data[key] = value

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def delete(self, key: str) -> int:
        return 1 if self.data.pop(key, None) is not None else 0

    def scan_iter(self, match: str = "*") -> list[str]:
        prefix = match.rstrip("*")
        return [k for k in self.data if k.startswith(prefix)]

    def expire(self, key: str, seconds: int) -> None:
        return None


def _clock() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_redis_store_register_confirmed_roundtrip() -> None:
    store = RedisToolConfirmationStore(
        FakeRedisClient(),
        clock=_clock,
    )
    record = store.register_confirmed(
        confirmation_id="a" * 16,
        actor_id="user_001",
        tool_name="create_ticket",
        arguments={"title": "t"},
        ttl_seconds=300,
    )
    assert record.confirmation_id == "a" * 16
    assert record.status == ToolConfirmationStatus.CONFIRMED

    verified = store.require_confirmed("a" * 16, actor_id="user_001")
    assert verified.confirmation_id == "a" * 16
    assert store.count() == 1


def test_redis_store_require_confirmed_rejects_unknown() -> None:
    store = RedisToolConfirmationStore(FakeRedisClient(), clock=_clock)
    with pytest.raises(AppException) as exc:
        store.require_confirmed("b" * 16, actor_id="user_001")
    assert exc.value.code == "TOOL_CONFIRMATION_NOT_FOUND"


def test_redis_store_require_confirmed_rejects_wrong_actor() -> None:
    store = RedisToolConfirmationStore(FakeRedisClient(), clock=_clock)
    store.register_confirmed(
        confirmation_id="c" * 16,
        actor_id="user_001",
        tool_name="create_ticket",
        arguments={},
        ttl_seconds=300,
    )
    with pytest.raises(AppException) as exc:
        store.require_confirmed("c" * 16, actor_id="user_002")
    assert exc.value.code == "TOOL_CONFIRMATION_FORBIDDEN"


def test_redis_store_clear_removes_all() -> None:
    store = RedisToolConfirmationStore(FakeRedisClient(), clock=_clock)
    store.register_confirmed(
        confirmation_id="d" * 16,
        actor_id="user_001",
        tool_name="create_ticket",
        arguments={},
        ttl_seconds=300,
    )
    store.clear()
    assert store.count() == 0


def test_create_tool_confirmation_store_returns_memory_by_default() -> None:
    store = create_tool_confirmation_store(Settings(_env_file=None))
    assert store.count() == 0  # memory singleton usable without redis


def test_create_tool_confirmation_store_returns_redis_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = create_tool_confirmation_store(
        Settings(
            _env_file=None,
            tool_confirmation_backend="redis",
            agent_redis_url="redis://redis.example:6379/3",
        )
    )
    assert isinstance(store, RedisToolConfirmationStore)
