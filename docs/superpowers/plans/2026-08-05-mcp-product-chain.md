# MCP 接入产品主链路 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 MCP 接入产品主链路：新增产品级 MCP server（独立进程、streamable HTTP、Bearer token 认证）与产品级 MCP client，Agent 的 query_order/create_ticket 工具调用改经 MCP 执行，确认凭证跨进程共享（Redis），并以真实联调验收。

**Architecture:** 调用链 `Agent → ProductMcpClient(HTTP) → ProductMcpServer(streamable HTTP :9100) → 复用 app/tools/ 守卫 + Java internal API → MySQL`。产品级 server 用 `MCPServer` + `streamable_http_app()` + ASGI Bearer 中间件；Agent 侧通过注入 MCP 版 executor/creator 接入，既有 LangGraph 图结构、意图识别、回答节点不变。确认凭证通过共享 `ToolConfirmationStore`（memory 默认 / Redis 可选）跨进程校验。

**Tech Stack:** Python 3.12、uv、mcp 2.0.0（`mcp.server.MCPServer`、`streamable_http`、`ClientSession`）、FastAPI/Starlette/uvicorn（已存在）、LangGraph（已存在）、redis-py（已存在）。

## Global Constraints

- 规格文件：`docs/superpowers/specs/2026-08-05-mcp-product-chain-design.md`（已获用户认可）。
- 端口：产品级 MCP server 固定 `127.0.0.1:9100`，streamable-http 路径 `/mcp`；`MCP_PRODUCT_BASE_URL=http://127.0.0.1:9100/mcp`。
- 认证：`MCP_PRODUCT_AUTH_TOKEN`（敏感，`repr=False`，Git 忽略），Bearer token 校验失败返回 401。
- 工具白名单：产品级 server 仅注册 `query_order`、`create_ticket`；`refund_order` 保持禁用。
- 确认凭证格式：产品级 create_ticket 的 `confirmation_id` 参数 pattern 为 `^[a-f0-9]{16,32}$`（兼容 Agent 16 位 hex 与 Redis store 32 位 uuid）。
- 测试约束：自动测试不调用真实模型、不调用真实 Embedding/Rerank API、不写真实业务数据、不依赖真实 Redis（用注入 fake）；`Settings(_env_file=None)` 默认 `tool_confirmation_backend=memory`、`agent_mcp_tools_enabled=False`，保证既有 1288 测试全绿。
- 依赖约束：不新增第三方依赖（不引入 fakeredis；Redis 版 store 测试用注入的 fake redis client）。
- Git：按项目协作偏好（交接文档），只有用户明确要求才执行 `git commit`/`git push`；计划中每个 Commit 步骤默认跳过，仅在用户指示时执行。
- 新功能最低要求：为核心正常路径与关键失败边界补少量自动测试；`uv run pytest -q` 全绿。

---

### Task 1: 配置项与 `.env.example`

**Files:**
- Modify: `projects/ai-service/app/core/config.py`（Settings 类，新增字段在 `mcp_project_resource_root` 之后）
- Modify: `projects/ai-service/.env.example`（在 `MCP_PROJECT_RESOURCE_ROOT=` 后追加）
- Test: `projects/ai-service/tests/test_config.py`

**Interfaces:**
- Produces: `Settings` 新增字段（全部有默认值，测试 `Settings(_env_file=None)` 可用）：
  - `mcp_product_base_url: str = "http://127.0.0.1:9100/mcp"`
  - `mcp_product_auth_token: str | None = Field(default=None, repr=False)`
  - `mcp_product_timeout_seconds: float = Field(default=30, ge=1, le=120)`
  - `mcp_product_retry_count: int = Field(default=2, ge=0, le=5)`
  - `mcp_product_port: int = Field(default=9100, ge=1, le=65535)`
  - `tool_confirmation_backend: str = Field(default="memory")`（枚举校验 memory|redis）
  - `agent_mcp_tools_enabled: bool = Field(default=False)`
- Produces: resolved 属性：
  - `resolved_mcp_product_base_url: str`（strip 后非空，否则默认）
  - `resolved_mcp_product_auth_token: str | None`（strip 后非空）
  - `resolved_tool_confirmation_backend: str`（非法值回退 memory）

- [ ] **Step 1: 写失败测试**（追加到 `tests/test_config.py`）

```python
def test_mcp_product_settings_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.mcp_product_base_url == "http://127.0.0.1:9100/mcp"
    assert settings.mcp_product_port == 9100
    assert settings.mcp_product_timeout_seconds == 30
    assert settings.mcp_product_retry_count == 2
    assert settings.tool_confirmation_backend == "memory"
    assert settings.agent_mcp_tools_enabled is False
    assert settings.resolved_mcp_product_auth_token is None


def test_mcp_product_settings_env_overrides() -> None:
    settings = Settings(
        _env_file=None,
        mcp_product_base_url=" http://127.0.0.1:9200/mcp ",
        mcp_product_auth_token=" secret-token ",
        mcp_product_timeout_seconds=15,
        mcp_product_retry_count=3,
        tool_confirmation_backend="redis",
        agent_mcp_tools_enabled=True,
    )
    assert settings.resolved_mcp_product_base_url == "http://127.0.0.1:9200/mcp"
    assert settings.resolved_mcp_product_auth_token == "secret-token"
    assert settings.resolved_tool_confirmation_backend == "redis"


def test_mcp_product_settings_invalid_backend_falls_back_to_memory() -> None:
    settings = Settings(_env_file=None, tool_confirmation_backend="invalid")
    assert settings.resolved_tool_confirmation_backend == "memory"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_config.py::test_mcp_product_settings_defaults -q`
Expected: FAIL（`AttributeError: 'Settings' object has no attribute 'mcp_product_base_url'`）

- [ ] **Step 3: 实现**（`app/core/config.py`）

在 `mcp_project_resource_root` 字段后追加：

```python
    mcp_product_base_url: str = Field(default="http://127.0.0.1:9100/mcp")
    mcp_product_auth_token: str | None = Field(default=None, repr=False)
    mcp_product_timeout_seconds: float = Field(default=30, ge=1, le=120)
    mcp_product_retry_count: int = Field(default=2, ge=0, le=5)
    mcp_product_port: int = Field(default=9100, ge=1, le=65535)
    tool_confirmation_backend: str = Field(default="memory")
    agent_mcp_tools_enabled: bool = Field(default=False)
```

在 `resolved_mcp_project_resource_root` 属性后追加：

```python
    @property
    def resolved_mcp_product_base_url(self) -> str:
        value = self.mcp_product_base_url.strip()
        return value or "http://127.0.0.1:9100/mcp"

    @property
    def resolved_mcp_product_auth_token(self) -> str | None:
        value = (self.mcp_product_auth_token or "").strip()
        return value or None

    @property
    def resolved_tool_confirmation_backend(self) -> str:
        return self.tool_confirmation_backend if self.tool_confirmation_backend == "redis" else "memory"
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_config.py -q`
Expected: PASS

- [ ] **Step 5: 更新 `.env.example`**（在 `MCP_PROJECT_RESOURCE_ROOT=` 行后追加）

```text
# 产品级 MCP server（独立进程，streamable HTTP）
MCP_PRODUCT_BASE_URL="http://127.0.0.1:9100/mcp"
MCP_PRODUCT_AUTH_TOKEN=""            # 内部 Bearer token，本地开发可留空；生产必须设置
MCP_PRODUCT_TIMEOUT_SECONDS=30
MCP_PRODUCT_RETRY_COUNT=2
MCP_PRODUCT_PORT=9100
# 确认凭证存储后端：memory（默认，测试用）或 redis（多进程共享确认凭证）
TOOL_CONFIRMATION_BACKEND="memory"
# 产品主链路是否经 MCP 调用工具；本地联调/生产设为 true
AGENT_MCP_TOOLS_ENABLED=false
```

- [ ] **Step 6: 跑全量配置测试**

Run: `cd projects/ai-service && uv run pytest tests/test_config.py -q`
Expected: PASS

- [ ] **Step 7: Commit**（按 Global Constraints 仅用户明确要求时执行）

```bash
git add projects/ai-service/app/core/config.py projects/ai-service/.env.example projects/ai-service/tests/test_config.py
git commit -m "feat: add product MCP and confirmation backend settings"
```

---

### Task 2: Redis 版确认存储（`RedisToolConfirmationStore`）与工厂切换

**Files:**
- Modify: `projects/ai-service/app/tools/tool_confirmation.py`（新增 `register_confirmed` 方法到内存版；新增 Redis 版类与工厂）
- Test: `projects/ai-service/tests/test_tool_confirmation_redis.py`（新建）

**Interfaces:**
- Consumes: `Settings.resolved_tool_confirmation_backend`、`Settings.agent_redis_url`、`ToolConfirmationStatus`（`app/schemas/tool_confirmation.py`）、`build_arguments_fingerprint`（`app/tools/idempotency.py`）
- Produces:
  - `ToolConfirmationStore.register_confirmed(*, confirmation_id: str, actor_id: str, tool_name: str, arguments: Mapping[str, Any], ttl_seconds: int) -> ToolConfirmationRecord`（内存版新增；直接登记为 CONFIRMED，不生成新 id）
  - `RedisToolConfirmationStore`：同一接口（create/confirm/require_confirmed/register_confirmed/clear/count），构造签名 `RedisToolConfirmationStore(redis_client: Any, *, key_prefix: str = "ai-service:tool-confirmation", clock: Callable[[], datetime] = utc_now)`
  - `create_tool_confirmation_store(settings: Settings | None = None) -> ToolConfirmationStore | RedisToolConfirmationStore`（按 backend 选择；memory 返回全局内存单例，redis 返回新 Redis 实例）
  - 内存版 `register_confirmed` 的 `confirmation_id` 由调用方提供（16 位 hex 或 32 位 hex 均可）

- [ ] **Step 1: 写失败测试**（新建 `tests/test_tool_confirmation_redis.py`）

```python
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_tool_confirmation_redis.py -q`
Expected: FAIL（`ImportError: cannot import name 'RedisToolConfirmationStore'`）

- [ ] **Step 3: 实现内存版 `register_confirmed`**（`app/tools/tool_confirmation.py`，加到 `ToolConfirmationStore` 类中 `confirm` 方法之后）

```python
    def register_confirmed(
        self,
        *,
        confirmation_id: str,
        actor_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        ttl_seconds: int,
    ) -> ToolConfirmationRecord:
        """Register a confirmation as already confirmed (id supplied by caller)."""
        created_at = self._clock()
        stored_arguments = deepcopy(dict(arguments))
        record = ToolConfirmationRecord(
            confirmation_id=confirmation_id,
            status=ToolConfirmationStatus.CONFIRMED,
            actor_id=actor_id,
            tool_name=tool_name,
            arguments=stored_arguments,
            arguments_fingerprint=build_arguments_fingerprint(
                tool_name,
                stored_arguments,
            ),
            created_at=created_at,
            expires_at=created_at + timedelta(seconds=ttl_seconds),
        )
        with self._lock:
            self._records[record.confirmation_id] = record
        return deepcopy(record)
```

- [ ] **Step 4: 实现 Redis 版 store 与工厂**（`app/tools/tool_confirmation.py` 文件末尾追加）

```python
class RedisToolConfirmationStore:
    """ToolConfirmationStore backed by redis, shared across processes."""

    def __init__(
        self,
        redis_client: Any,
        *,
        key_prefix: str = "ai-service:tool-confirmation",
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix
        self._clock = clock

    def _key(self, confirmation_id: str) -> str:
        return f"{self._key_prefix}:{confirmation_id}"

    def _load(self, confirmation_id: str) -> ToolConfirmationRecord | None:
        raw = self._redis.get(self._key(confirmation_id))
        if raw is None:
            return None
        payload = json.loads(raw)
        return ToolConfirmationRecord(
            confirmation_id=payload["confirmation_id"],
            status=ToolConfirmationStatus(payload["status"]),
            actor_id=payload["actor_id"],
            tool_name=payload["tool_name"],
            arguments=payload["arguments"],
            arguments_fingerprint=payload["arguments_fingerprint"],
            created_at=datetime.fromisoformat(payload["created_at"]),
            expires_at=datetime.fromisoformat(payload["expires_at"]),
        )

    def _store(self, record: ToolConfirmationRecord, ttl_seconds: int) -> None:
        payload = {
            "confirmation_id": record.confirmation_id,
            "status": record.status.value,
            "actor_id": record.actor_id,
            "tool_name": record.tool_name,
            "arguments": record.arguments,
            "arguments_fingerprint": record.arguments_fingerprint,
            "created_at": record.created_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
        }
        self._redis.set(
            self._key(record.confirmation_id),
            json.dumps(payload, ensure_ascii=True),
            ex=ttl_seconds,
        )

    def _require_record(self, confirmation_id: str) -> ToolConfirmationRecord:
        record = self._load(confirmation_id)
        if record is None:
            raise AppException(
                code="TOOL_CONFIRMATION_NOT_FOUND",
                message="确认请求不存在或已失效。",
                status_code=404,
            )
        if self._clock() >= record.expires_at:
            raise AppException(
                code="TOOL_CONFIRMATION_EXPIRED",
                message="确认请求已过期，请重新发起操作。",
                status_code=409,
            )
        return record

    def create(
        self,
        *,
        actor_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        ttl_seconds: int,
    ) -> ToolConfirmationRecord:
        created_at = self._clock()
        record = ToolConfirmationRecord(
            confirmation_id=uuid4().hex,
            status=ToolConfirmationStatus.PENDING,
            actor_id=actor_id,
            tool_name=tool_name,
            arguments=deepcopy(dict(arguments)),
            arguments_fingerprint=build_arguments_fingerprint(tool_name, arguments),
            created_at=created_at,
            expires_at=created_at + timedelta(seconds=ttl_seconds),
        )
        self._store(record, ttl_seconds)
        return deepcopy(record)

    def confirm(
        self,
        confirmation_id: str,
        *,
        actor_id: str,
    ) -> ToolConfirmationRecord:
        record = self._require_record(confirmation_id)
        if record.actor_id != actor_id:
            raise AppException(
                code="TOOL_CONFIRMATION_FORBIDDEN",
                message="当前操作者不能确认其他人的工具请求。",
                status_code=403,
            )
        if record.status == ToolConfirmationStatus.PENDING:
            record = ToolConfirmationRecord(
                confirmation_id=record.confirmation_id,
                status=ToolConfirmationStatus.CONFIRMED,
                actor_id=record.actor_id,
                tool_name=record.tool_name,
                arguments=record.arguments,
                arguments_fingerprint=record.arguments_fingerprint,
                created_at=record.created_at,
                expires_at=record.expires_at,
            )
            self._store(record, ttl_seconds=int((record.expires_at - record.created_at).total_seconds()))
        return deepcopy(record)

    def require_confirmed(
        self,
        confirmation_id: str,
        *,
        actor_id: str,
    ) -> ToolConfirmationRecord:
        record = self._require_record(confirmation_id)
        if record.actor_id != actor_id:
            raise AppException(
                code="TOOL_CONFIRMATION_FORBIDDEN",
                message="当前操作者不能执行其他人的工具请求。",
                status_code=403,
            )
        if record.status != ToolConfirmationStatus.CONFIRMED:
            raise AppException(
                code="TOOL_CONFIRMATION_REQUIRED",
                message="该工具请求尚未获得用户确认。",
                status_code=409,
            )
        return deepcopy(record)

    def register_confirmed(
        self,
        *,
        confirmation_id: str,
        actor_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        ttl_seconds: int,
    ) -> ToolConfirmationRecord:
        created_at = self._clock()
        record = ToolConfirmationRecord(
            confirmation_id=confirmation_id,
            status=ToolConfirmationStatus.CONFIRMED,
            actor_id=actor_id,
            tool_name=tool_name,
            arguments=deepcopy(dict(arguments)),
            arguments_fingerprint=build_arguments_fingerprint(tool_name, arguments),
            created_at=created_at,
            expires_at=created_at + timedelta(seconds=ttl_seconds),
        )
        self._store(record, ttl_seconds)
        return deepcopy(record)

    def clear(self) -> None:
        for key in self._redis.scan_iter(match=f"{self._key_prefix}:*"):
            self._redis.delete(key)

    def count(self) -> int:
        return len(self._redis.scan_iter(match=f"{self._key_prefix}:*"))


def create_tool_confirmation_store(
    settings: Settings | None = None,
) -> ToolConfirmationStore | RedisToolConfirmationStore:
    from app.core.config import get_settings

    resolved_settings = settings or get_settings()
    if resolved_settings.resolved_tool_confirmation_backend == "redis":
        import redis as redis_lib

        redis_client = redis_lib.Redis.from_url(
            resolved_settings.agent_redis_url,
            decode_responses=True,
        )
        return RedisToolConfirmationStore(redis_client)
    return get_tool_confirmation_store()
```

在文件头部补充 import：`import json`（现有 import 中无 json）。

- [ ] **Step 5: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_tool_confirmation_redis.py -q`
Expected: PASS

- [ ] **Step 6: 跑既有确认相关测试确保不回归**

Run: `cd projects/ai-service && uv run pytest tests/test_tool_confirmation_service.py tests/test_tool_confirmation_schema.py -q`
Expected: PASS

- [ ] **Step 7: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/tools/tool_confirmation.py projects/ai-service/tests/test_tool_confirmation_redis.py
git commit -m "feat: add redis-backed tool confirmation store and backend factory"
```

---

### Task 3: 产品级 MCP server（独立进程 + streamable HTTP + Bearer 认证）

**Files:**
- Create: `projects/ai-service/app/mcp_servers/product_server.py`
- Modify: `projects/ai-service/app/mcp_servers/__init__.py`（如需导出）
- Test: `projects/ai-service/tests/test_mcp_product_server.py`（新建）

**Interfaces:**
- Consumes: `Settings`（`resolved_mcp_product_base_url`、`resolved_mcp_product_auth_token`、`resolved_mcp_product_port`）、`order_tool.query_order_for_mcp`、`app.tools.tool_registry.authorize_tool_call`、`app.tools.idempotency.run_idempotent_tool`、`JavaTicketClient`（`app/services/java_ticket_client.py`）、`CreateTicketArgs`/`CreatedTicket`（`app/schemas/ticket.py`）、`create_tool_confirmation_store`（Task 2）
- Produces:
  - `create_product_mcp_server(settings: Settings | None = None) -> MCPServer`：注册 `query_order`、`create_ticket` 两个工具
  - `create_product_mcp_app(settings: Settings | None = None) -> Starlette`：`server.streamable_http_app(streamable_http_path="/mcp")` 外包 Bearer 认证中间件
  - `BearerAuthMiddleware(app: ASGIApp, *, token: str)`：校验 `Authorization: Bearer <token>`，缺失/不匹配返回 401 JSON
  - `main()` / `python -m app.mcp_servers.product_server`：uvicorn 启动 `127.0.0.1:9100`
  - 工具 `query_order(order_id: str) -> dict`：MCP-safe 结构（复用 `order_tool._mcp_query_order_response` 语义，直接返回 `query_order_for_mcp(order_id)` 结果）
  - 工具 `create_ticket(...) -> dict`：参数 `requester_id, title, description, category, priority, related_order_id, confirmation_id (16-32 hex), user_confirmed`；内部 `require_confirmed`（共享 store，actor=requester_id）→ `authorize_tool_call("create_ticket", user_confirmed=True)` → `run_idempotent_tool`（幂等键=confirmation_id）→ `JavaTicketClient.create_ticket` → MCP-safe 结构

- [ ] **Step 1: 写失败测试**（新建 `tests/test_mcp_product_server.py`）

```python
import json

import pytest
from mcp import Client

from app.core.config import Settings
from app.core.exceptions import AppException
from app.mcp_servers.product_server import (
    BearerAuthMiddleware,
    create_product_mcp_app,
    create_product_mcp_server,
)
from tests.tool_fakes import FakeTicketCreator, make_created_ticket


def _settings(token: str | None = "test-token") -> Settings:
    return Settings(
        _env_file=None,
        mcp_product_auth_token=token,
        tool_confirmation_backend="memory",
    )


def test_product_server_registers_only_business_tools() -> None:
    async def run() -> None:
        server = create_product_mcp_server(_settings())
        async with Client(server) as client:
            tools = await client.list_tools()
        names = [tool.name for tool in tools.tools]
        assert names == ["query_order", "create_ticket"]

    import asyncio

    asyncio.run(run())


def test_product_create_ticket_accepts_16_hex_confirmation_id() -> None:
    server = create_product_mcp_server(_settings())

    async def run() -> None:
        async with Client(server) as client:
            tools = await client.list_tools()
        tool = next(t for t in tools.tools if t.name == "create_ticket")
        confirmation_schema = tool.input_schema["properties"]["confirmation_id"]
        assert confirmation_schema["pattern"] == r"^[a-f0-9]{16,32}$"
        assert "user_confirmed" in tool.input_schema["properties"]

    import asyncio

    asyncio.run(run())


def test_bearer_auth_middleware_rejects_missing_token() -> None:
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    async def ok_endpoint(request: object) -> PlainTextResponse:
        return PlainTextResponse("ok")

    inner = Starlette(routes=[Route("/mcp", ok_endpoint, methods=["GET", "POST"])])
    wrapped = BearerAuthMiddleware(inner, token="test-token")

    from starlette.testclient import TestClient

    client = TestClient(wrapped)
    response = client.post("/mcp", json={})
    assert response.status_code == 401


def test_bearer_auth_middleware_rejects_wrong_token() -> None:
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    async def ok_endpoint(request: object) -> PlainTextResponse:
        return PlainTextResponse("ok")

    inner = Starlette(routes=[Route("/mcp", ok_endpoint, methods=["GET", "POST"])])
    wrapped = BearerAuthMiddleware(inner, token="test-token")
    from starlette.testclient import TestClient

    client = TestClient(wrapped)
    response = client.post(
        "/mcp",
        json={},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401


def test_bearer_auth_middleware_accepts_correct_token() -> None:
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    async def ok_endpoint(request: object) -> PlainTextResponse:
        return PlainTextResponse("ok")

    inner = Starlette(routes=[Route("/mcp", ok_endpoint, methods=["GET", "POST"])])
    wrapped = BearerAuthMiddleware(inner, token="test-token")
    from starlette.testclient import TestClient

    client = TestClient(wrapped)
    response = client.post(
        "/mcp",
        json={},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200


def test_product_app_uses_bearer_middleware() -> None:
    app = create_product_mcp_app(_settings(token="test-token"))
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1, "params": {}},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code in (200, 202)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_mcp_product_server.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.mcp_servers.product_server'`）

- [ ] **Step 3: 实现**（新建 `app/mcp_servers/product_server.py`）

```python
"""Product-grade MCP server: streamable HTTP, Bearer auth, business tools only.

Run as a standalone process:

    uv run python -m app.mcp_servers.product_server
"""

import logging
from typing import Any

from mcp.server import MCPServer

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.mcp_servers import order_tool
from app.schemas.ticket import CreateTicketArgs
from app.services.java_ticket_client import JavaTicketClient
from app.tools.idempotency import run_idempotent_tool
from app.tools.tool_confirmation import create_tool_confirmation_store
from app.tools.tool_registry import authorize_tool_call


logger = logging.getLogger(__name__)

CREATE_TICKET_TOOL_NAME = "create_ticket"
QUERY_ORDER_TOOL_NAME = "query_order"

# Confirmation ids come from the agent (16-hex sha256 prefix) or from the
# confirmation store (32-hex uuid), so accept both.
CONFIRMATION_ID_PATTERN = r"^[a-f0-9]{16,32}$"


def _create_ticket_response(
    *,
    ok: bool,
    confirmation_id: str,
    error_code: str | None,
    message: str,
    ticket: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "allowed": True,
        "confirmation_checked": True,
        "confirmation_id": confirmation_id,
        "error_code": error_code,
        "message": message,
        "ticket": ticket,
    }


def _safe_created_ticket(ticket: Any) -> dict[str, Any]:
    return ticket.model_dump(mode="json")


def _product_create_ticket(
    requester_id: str,
    title: str,
    description: str,
    category: str,
    confirmation_id: str,
    priority: str = "normal",
    related_order_id: str | None = None,
    user_confirmed: bool = False,
) -> dict[str, Any]:
    """Create a ticket with confirmation + authorization + idempotency guards."""
    if not user_confirmed:
        return _create_ticket_response(
            ok=False,
            confirmation_id=confirmation_id.strip(),
            error_code="TOOL_CONFIRMATION_REQUIRED",
            message="该工具需要用户确认后才能执行。",
            ticket=None,
        )

    try:
        arguments = CreateTicketArgs(
            requester_id=requester_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            related_order_id=related_order_id,
        )
    except Exception as exc:  # pydantic.ValidationError
        from pydantic import ValidationError

        if not isinstance(exc, ValidationError):
            raise
        return _create_ticket_response(
            ok=False,
            confirmation_id=confirmation_id,
            error_code="INVALID_TOOL_ARGUMENTS",
            message="工单参数不正确，请确认后重新提交。",
            ticket=None,
        )

    store = create_tool_confirmation_store()
    try:
        store.require_confirmed(confirmation_id, actor_id=requester_id)
    except AppException as exc:
        return _create_ticket_response(
            ok=False,
            confirmation_id=confirmation_id,
            error_code=exc.code,
            message=exc.message,
            ticket=None,
        )

    try:
        authorize_tool_call(CREATE_TICKET_TOOL_NAME, user_confirmed=True)
        ticket_creator = JavaTicketClient.from_settings(get_settings())
        ticket = run_idempotent_tool(
            CREATE_TICKET_TOOL_NAME,
            arguments,
            confirmation_id,
            lambda: ticket_creator.create_ticket(
                arguments,
                idempotency_key=confirmation_id,
            ),
        )
    except AppException as exc:
        return _create_ticket_response(
            ok=False,
            confirmation_id=confirmation_id,
            error_code=exc.code,
            message=exc.message,
            ticket=None,
        )
    except Exception as exc:
        logger.warning(
            "product_mcp_create_ticket_failed error_type=%s",
            type(exc).__name__,
            exc_info=True,
        )
        return _create_ticket_response(
            ok=False,
            confirmation_id=confirmation_id,
            error_code="TICKET_CREATION_TOOL_ERROR",
            message="创建工单工具暂时不可用，请稍后重试或联系人工处理。",
            ticket=None,
        )

    logger.info(
        "product_mcp_create_ticket_succeeded confirmation_id=%s ticket_id=%s",
        confirmation_id,
        ticket.ticket_id,
    )
    return _create_ticket_response(
        ok=True,
        confirmation_id=confirmation_id,
        error_code=None,
        message="工单创建成功。",
        ticket=_safe_created_ticket(ticket),
    )


def create_product_mcp_server(
    settings: Settings | None = None,
) -> MCPServer:
    """Create a product-grade MCP server exposing only business tools."""
    resolved_settings = settings or get_settings()
    server = MCPServer(name="ai-service-product-mcp")

    @server.tool()
    def query_order(order_id: str) -> dict[str, Any]:
        """Query a business order through the guarded Java adapter (read-only)."""
        return order_tool.query_order_for_mcp(order_id)

    @server.tool()
    def create_ticket(
        requester_id: str,
        title: str,
        description: str,
        category: str,
        confirmation_id: str,
        priority: str = "normal",
        related_order_id: str | None = None,
        user_confirmed: bool = False,
    ) -> dict[str, Any]:
        """Create a support ticket after user confirmation and idempotency checks."""
        return _product_create_ticket(
            requester_id=requester_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            related_order_id=related_order_id,
            confirmation_id=confirmation_id,
            user_confirmed=user_confirmed,
        )

    return server


class BearerAuthMiddleware:
    """ASGI middleware enforcing a fixed Bearer token on every HTTP request."""

    def __init__(self, app: Any, *, token: str) -> None:
        self.app = app
        self.expected = f"Bearer {token}"

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        authorization = None
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                authorization = value.decode("latin-1")
                break

        if authorization != self.expected:
            from starlette.responses import JSONResponse

            response = JSONResponse(
                {"error": "unauthorized", "message": "missing or invalid bearer token"},
                status_code=401,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def create_product_mcp_app(settings: Settings | None = None) -> Any:
    """Return the streamable HTTP Starlette app wrapped with Bearer auth."""
    resolved_settings = settings or get_settings()
    server = create_product_mcp_server(resolved_settings)
    app = server.streamable_http_app(streamable_http_path="/mcp")
    token = resolved_settings.resolved_mcp_product_auth_token
    if token is not None:
        return BearerAuthMiddleware(app, token=token)
    return app


def main() -> None:
    import uvicorn

    settings = get_settings()
    app = create_product_mcp_app(settings)
    uvicorn.run(app, host="127.0.0.1", port=settings.mcp_product_port)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_mcp_product_server.py -q`
Expected: PASS

- [ ] **Step 5: 手动启动验证（可选，需用户环境）**

Run: `cd projects/ai-service && uv run python -m app.mcp_servers.product_server`
Expected: uvicorn 监听 `127.0.0.1:9100`，日志显示 `Application startup complete`

- [ ] **Step 6: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/mcp_servers/product_server.py projects/ai-service/tests/test_mcp_product_server.py
git commit -m "feat: add product MCP server with streamable HTTP and bearer auth"
```

---

### Task 4: 产品级 MCP client

**Files:**
- Create: `projects/ai-service/app/mcp_clients/product_client.py`
- Modify: `projects/ai-service/tests/tool_fakes.py`（新增 `FakeMcpToolCaller` 公共 fake）
- Test: `projects/ai-service/tests/test_mcp_product_client.py`（新建）

**Interfaces:**
- Consumes: `Settings`（`resolved_mcp_product_base_url`、`resolved_mcp_product_auth_token`、`mcp_product_timeout_seconds`、`mcp_product_retry_count`）
- Produces:
  - `class McpToolCaller(Protocol)`: `def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]`
  - `class ProductMcpClient`（实现 `McpToolCaller`）: 构造 `ProductMcpClient(base_url: str, auth_token: str | None, *, timeout_seconds: float = 30, retry_count: int = 2)`；方法 `call_tool(tool_name, arguments) -> dict`（同步，内部 `asyncio.run` 驱动 `streamablehttp_client` + `ClientSession`）；`list_tools() -> list[str]`（缓存）
  - `create_product_mcp_client(settings: Settings | None = None) -> ProductMcpClient`
  - 异常映射：连接失败/超时/重试耗尽 → 抛 `AppException`（`MCP_SERVER_UNREACHABLE`，502；超时 `MCP_SERVER_TIMEOUT`，504），供 Agent 失败分类识别
- 说明：`call_tool` 返回 MCP 工具结果：对 `TextContent` 内容做 `json.loads` 解析为 dict；解析失败时抛 `AppException("MCP_RESULT_INVALID")`。

- [ ] **Step 1: 写失败测试**（先给 `tests/tool_fakes.py` 追加 `FakeMcpToolCaller`，再新建 `tests/test_mcp_product_client.py`）

先在 `tests/tool_fakes.py` 末尾追加：

```python
class FakeMcpToolCaller:
    """In-memory McpToolCaller used to test agent adapters without HTTP."""

    def __init__(self, responses: dict[str, dict] | None = None) -> None:
        self.responses: dict[str, dict] = responses or {}
        self.calls: list[tuple[str, dict]] = []

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        self.calls.append((tool_name, arguments))
        if tool_name in self.responses:
            return self.responses[tool_name]
        raise AppException(
            code="MCP_TOOL_NOT_FOUND",
            message=f"tool {tool_name} not available",
            status_code=404,
        )
```

注意：`tests/tool_fakes.py` 顶部需要 `from app.core.exceptions import AppException`（若尚无该 import）。

再新建 `tests/test_mcp_product_client.py`：

```python
import pytest

from app.core.config import Settings
from app.core.exceptions import AppException
from app.mcp_clients.product_client import (
    McpToolCaller,
    ProductMcpClient,
    create_product_mcp_client,
)
from tests.tool_fakes import FakeMcpToolCaller


def test_create_product_mcp_client_from_settings() -> None:
    client = create_product_mcp_client(
        Settings(
            _env_file=None,
            mcp_product_base_url="http://127.0.0.1:9100/mcp",
            mcp_product_auth_token="token",
            mcp_product_timeout_seconds=5,
            mcp_product_retry_count=1,
        )
    )
    assert isinstance(client, ProductMcpClient)
    assert client.base_url == "http://127.0.0.1:9100/mcp"
    assert client.auth_token == "token"
    assert client.timeout_seconds == 5
    assert client.retry_count == 1


def test_mcp_tool_caller_protocol_supports_fake() -> None:
    fake = FakeMcpToolCaller(responses={"query_order": {"ok": True}})
    caller: McpToolCaller = fake
    assert caller.call_tool("query_order", {"order_id": "A1001"}) == {"ok": True}
    assert fake.calls == [("query_order", {"order_id": "A1001"})]
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_mcp_product_client.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.mcp_clients.product_client'`）

- [ ] **Step 3: 实现**（新建 `app/mcp_clients/product_client.py`）

```python
"""Product-grade MCP client used by the ticket agent to call the product MCP server."""

import asyncio
import json
import logging
from typing import Any, Protocol

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException


logger = logging.getLogger(__name__)


class McpToolCaller(Protocol):
    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call an MCP tool and return its parsed result dict."""
        ...


class ProductMcpClient:
    """Synchronous facade over the async streamable HTTP MCP client."""

    def __init__(
        self,
        base_url: str,
        auth_token: str | None,
        *,
        timeout_seconds: float = 30,
        retry_count: int = 2,
    ) -> None:
        self.base_url = base_url.strip().rstrip("/")
        self.auth_token = auth_token
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self._tools_cache: list[str] | None = None

    def _headers(self) -> dict[str, str]:
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.retry_count + 1):
            try:
                return asyncio.run(
                    self._call_tool_async(tool_name, arguments)
                )
            except AppException:
                raise
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "product_mcp_client_retry tool=%s attempt=%s error_type=%s",
                    tool_name,
                    attempt + 1,
                    type(exc).__name__,
                )
        raise AppException(
            code="MCP_SERVER_UNREACHABLE",
            message="AI 工具服务暂时不可用，请稍后再试。",
            status_code=502,
        ) from last_error

    async def _call_tool_async(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        timeout = self.timeout_seconds
        async with streamablehttp_client(
            self.base_url,
            headers=self._headers(),
            timeout=timeout,
        ) as (read_stream, write_stream, _get_session_id):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return self._parse_result(result)

    def _parse_result(self, result: Any) -> dict[str, Any]:
        text_parts: list[str] = []
        for block in result.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
        if not text_parts:
            raise AppException(
                code="MCP_RESULT_INVALID",
                message="AI 工具服务返回了无法解析的结果。",
                status_code=502,
            )
        raw_text = "\n".join(text_parts)
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise AppException(
                code="MCP_RESULT_INVALID",
                message="AI 工具服务返回了无法解析的结果。",
                status_code=502,
            ) from exc
        if not isinstance(parsed, dict):
            raise AppException(
                code="MCP_RESULT_INVALID",
                message="AI 工具服务返回了无法解析的结果。",
                status_code=502,
            )
        return parsed

    def list_tools(self) -> list[str]:
        if self._tools_cache is not None:
            return self._tools_cache
        tools = asyncio.run(self._list_tools_async())
        self._tools_cache = tools
        return tools

    async def _list_tools_async(self) -> list[str]:
        timeout = self.timeout_seconds
        async with streamablehttp_client(
            self.base_url,
            headers=self._headers(),
            timeout=timeout,
        ) as (read_stream, write_stream, _get_session_id):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                listed = await session.list_tools()
                return [tool.name for tool in listed.tools]


def create_product_mcp_client(
    settings: Settings | None = None,
) -> ProductMcpClient:
    resolved_settings = settings or get_settings()
    return ProductMcpClient(
        base_url=resolved_settings.resolved_mcp_product_base_url,
        auth_token=resolved_settings.resolved_mcp_product_auth_token,
        timeout_seconds=resolved_settings.mcp_product_timeout_seconds,
        retry_count=resolved_settings.mcp_product_retry_count,
    )
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_mcp_product_client.py -q`
Expected: PASS

- [ ] **Step 5: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/mcp_clients/product_client.py projects/ai-service/tests/test_mcp_product_client.py
git commit -m "feat: add product MCP client with retry and result validation"
```

---

### Task 5: Agent 接入（MCP executor/creator 适配 + 确认凭证登记）

**Files:**
- Create: `projects/ai-service/app/agents/mcp_tool_adapters.py`
- Modify: `projects/ai-service/app/services/console_agent_service.py`（graph 构建注入 + 确认登记）
- Test: `projects/ai-service/tests/test_agent_via_mcp.py`（新建）

**Interfaces:**
- Consumes: `ProductMcpClient`/`McpToolCaller`（Task 4）、`TicketCreator`/`OrderQueryExecutor`（`app/agents/ticket_agent.py`）、`CreateTicketArgs`/`CreatedTicket`/`QueryOrderArgs`/`QueryOrderResult`、`build_pending_ticket_confirmation`/`resume_ticket_confirmation_interrupt`（`app/agents/ticket_agent.py`）、`create_tool_confirmation_store`（Task 2）
- Produces:
  - `class McpTicketCreator`（实现 `TicketCreator`）: 构造 `McpTicketCreator(caller: McpToolCaller, *, settings: Settings | None = None)`；`create_ticket(arguments: CreateTicketArgs, *, idempotency_key: str) -> CreatedTicket`：调用 `caller.call_tool("create_ticket", {...})`，解析 `{ok, ticket}` → `CreatedTicket.model_validate`；`ok=False` 时抛 `AppException(error_code, message)`；不可达/无效 → `AppException`（Agent 已有失败分类）
  - `def mcp_order_query_executor(caller: McpToolCaller) -> OrderQueryExecutor`：`Callable[[QueryOrderArgs], QueryOrderResult]`，调用 `caller.call_tool("query_order", {"order_id": ...})`，解析 `{ok, result}` → `QueryOrderResult.model_validate`；`ok=False` 时抛 `AppException`
  - `def register_ticket_confirmation(actor_id: str, fields: TicketFields) -> str`：计算 `confirmation_id = build_pending_ticket_confirmation(fields)["confirmation_id"]`，调 `create_tool_confirmation_store().register_confirmed(confirmation_id=..., actor_id=actor_id, tool_name="create_ticket", arguments=fields, ttl_seconds=settings.tool_confirmation_ttl_seconds)`，返回 confirmation_id
  - `def create_mcp_ticket_creator(settings: Settings | None = None) -> McpTicketCreator`、`def create_mcp_order_query_executor(settings: Settings | None = None) -> OrderQueryExecutor`：默认用 `create_product_mcp_client(settings)`，也接受注入 caller（测试用 Fake）

- [ ] **Step 1: 写失败测试**（新建 `tests/test_agent_via_mcp.py`）

```python
import pytest

from app.agents.mcp_tool_adapters import (
    McpTicketCreator,
    create_mcp_order_query_executor,
    create_mcp_ticket_creator,
    mcp_order_query_executor,
    register_ticket_confirmation,
)
from app.core.config import Settings
from app.core.exceptions import AppException
from app.schemas.ticket import (
    CreateTicketArgs,
    CreatedTicket,
    TicketCategory,
    TicketPriority,
)
from app.schemas.tool import QueryOrderArgs, QueryOrderResult
from tests.tool_fakes import FakeMcpToolCaller


def _settings() -> Settings:
    return Settings(_env_file=None, tool_confirmation_backend="memory")


def test_mcp_ticket_creator_creates_ticket_from_ok_response() -> None:
    caller = FakeMcpToolCaller(
        responses={
            "create_ticket": {
                "ok": True,
                "confirmation_checked": True,
                "confirmation_id": "a" * 16,
                "error_code": None,
                "message": "工单创建成功。",
                "ticket": {
                    "ticket_id": "T1000001",
                    "requester_id": "user_001",
                    "title": "退款申请",
                    "description": "订单破损",
                    "category": "refund",
                    "priority": "high",
                    "related_order_id": "A1001",
                    "created_at": "2026-01-01T00:00:00Z",
                },
            }
        }
    )
    creator = McpTicketCreator(caller, settings=_settings())
    arguments = CreateTicketArgs(
        requester_id="user_001",
        title="退款申请",
        description="订单破损",
        category=TicketCategory.REFUND,
        priority=TicketPriority.HIGH,
        related_order_id="A1001",
    )
    ticket = creator.create_ticket(arguments, idempotency_key="a" * 16)
    assert ticket.ticket_id == "T1000001"
    assert caller.calls[0][0] == "create_ticket"
    assert caller.calls[0][1]["confirmation_id"] == "a" * 16
    assert caller.calls[0][1]["user_confirmed"] is True


def test_mcp_ticket_creator_raises_app_exception_on_ok_false() -> None:
    caller = FakeMcpToolCaller(
        responses={
            "create_ticket": {
                "ok": False,
                "confirmation_checked": True,
                "confirmation_id": "b" * 16,
                "error_code": "ORDER_NOT_FOUND",
                "message": "订单不存在",
                "ticket": None,
            }
        }
    )
    creator = McpTicketCreator(caller, settings=_settings())
    arguments = CreateTicketArgs(
        requester_id="user_001",
        title="t",
        description="d",
        category=TicketCategory.REFUND,
    )
    with pytest.raises(AppException) as exc:
        creator.create_ticket(arguments, idempotency_key="b" * 16)
    assert exc.value.code == "ORDER_NOT_FOUND"


def test_mcp_order_query_executor_parses_result() -> None:
    caller = FakeMcpToolCaller(
        responses={
            "query_order": {
                "ok": True,
                "allowed": True,
                "action": "query_order",
                "action_type": "read",
                "requires_confirmation": False,
                "error_code": None,
                "message": "订单查询成功。",
                "retryable": False,
                "security_checks": {"input_validated": True},
                "result": {
                    "order_id": "A1001",
                    "order_status": "waiting_shipment",
                    "payment_status": "paid",
                    "logistics_message": "商家已接单。",
                    "latest_event": "仓库准备出库。",
                    "can_create_ticket": True,
                    "source": "java_business_service",
                },
            }
        }
    )
    executor = mcp_order_query_executor(caller)
    result = executor(QueryOrderArgs(order_id="A1001"))
    assert isinstance(result, QueryOrderResult)
    assert result.order_id == "A1001"
    assert caller.calls == [("query_order", {"order_id": "A1001"})]


def test_register_ticket_confirmation_registers_confirmed_record() -> None:
    from app.agents.ticket_agent import build_pending_ticket_confirmation

    fields = {
        "issue_type": "refund",
        "order_id": "A1001",
        "description": "订单破损",
        "user_request": "申请退款",
        "urgency": "high",
        "need_human_review": False,
    }
    confirmation_id = register_ticket_confirmation(
        actor_id="user_001",
        fields=fields,
        settings=_settings(),
    )
    expected_id = build_pending_ticket_confirmation(fields)["confirmation_id"]
    assert confirmation_id == expected_id

    from app.tools.tool_confirmation import create_tool_confirmation_store

    store = create_tool_confirmation_store(_settings())
    record = store.require_confirmed(confirmation_id, actor_id="user_001")
    assert record.status.value == "confirmed"


def test_create_mcp_ticket_creator_builds_from_settings() -> None:
    creator = create_mcp_ticket_creator(
        Settings(
            _env_file=None,
            mcp_product_base_url="http://127.0.0.1:9100/mcp",
            mcp_product_auth_token="token",
        )
    )
    assert isinstance(creator, McpTicketCreator)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_agent_via_mcp.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.agents.mcp_tool_adapters'`）

- [ ] **Step 3: 实现**（新建 `app/agents/mcp_tool_adapters.py`）

```python
"""MCP-backed adapters that satisfy the ticket agent's executor/creator protocols."""

from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.mcp_clients.product_client import McpToolCaller, create_product_mcp_client
from app.schemas.ticket import CreateTicketArgs, CreatedTicket, TicketFields
from app.schemas.tool import QueryOrderArgs, QueryOrderResult
from app.tools.tool_confirmation import create_tool_confirmation_store


CREATE_TICKET_TOOL_NAME = "create_ticket"
QUERY_ORDER_TOOL_NAME = "query_order"


def _require_ok(payload: dict[str, Any], *, fallback_code: str) -> None:
    if payload.get("ok") is True:
        return
    raise AppException(
        code=payload.get("error_code") or fallback_code,
        message=payload.get("message") or "工具调用失败，请稍后重试。",
        status_code=502,
    )


class McpTicketCreator:
    """TicketCreator that executes create_ticket through the product MCP client."""

    def __init__(
        self,
        caller: McpToolCaller,
        *,
        settings: Settings | None = None,
    ) -> None:
        self._caller = caller
        self._settings = settings or get_settings()

    def create_ticket(
        self,
        arguments: CreateTicketArgs,
        *,
        idempotency_key: str,
    ) -> CreatedTicket:
        payload = self._caller.call_tool(
            CREATE_TICKET_TOOL_NAME,
            {
                "requester_id": arguments.requester_id,
                "title": arguments.title,
                "description": arguments.description,
                "category": arguments.category.value,
                "priority": arguments.priority.value,
                "related_order_id": arguments.related_order_id,
                "confirmation_id": idempotency_key,
                "user_confirmed": True,
            },
        )
        _require_ok(payload, fallback_code="TICKET_CREATION_TOOL_ERROR")
        ticket_payload = payload.get("ticket")
        if not isinstance(ticket_payload, dict):
            raise AppException(
                code="MCP_RESULT_INVALID",
                message="AI 工具服务返回了无法解析的工单结果。",
                status_code=502,
            )
        return CreatedTicket.model_validate(ticket_payload)


def mcp_order_query_executor(
    caller: McpToolCaller,
) -> Any:
    """Return an OrderQueryExecutor (Callable[[QueryOrderArgs], QueryOrderResult])."""

    def execute(arguments: QueryOrderArgs) -> QueryOrderResult:
        payload = caller.call_tool(
            QUERY_ORDER_TOOL_NAME,
            {"order_id": arguments.order_id},
        )
        _require_ok(payload, fallback_code="TOOL_CALL_FAILED")
        result_payload = payload.get("result")
        if not isinstance(result_payload, dict):
            raise AppException(
                code="MCP_RESULT_INVALID",
                message="AI 工具服务返回了无法解析的订单结果。",
                status_code=502,
            )
        return QueryOrderResult.model_validate(result_payload)

    return execute


def create_mcp_ticket_creator(
    settings: Settings | None = None,
    *,
    caller: McpToolCaller | None = None,
) -> McpTicketCreator:
    resolved_settings = settings or get_settings()
    return McpTicketCreator(
        caller or create_product_mcp_client(resolved_settings),
        settings=resolved_settings,
    )


def create_mcp_order_query_executor(
    settings: Settings | None = None,
    *,
    caller: McpToolCaller | None = None,
) -> Any:
    resolved_settings = settings or get_settings()
    return mcp_order_query_executor(
        caller or create_product_mcp_client(resolved_settings)
    )


def register_ticket_confirmation(
    actor_id: str,
    fields: TicketFields,
    *,
    settings: Settings | None = None,
) -> str:
    """Register the agent's pending confirmation as confirmed in the shared store.

    Returns the confirmation_id that the MCP server will verify.
    """
    from app.agents.ticket_agent import build_pending_ticket_confirmation

    resolved_settings = settings or get_settings()
    confirmation_id = build_pending_ticket_confirmation(fields)["confirmation_id"]
    store = create_tool_confirmation_store(resolved_settings)
    store.register_confirmed(
        confirmation_id=confirmation_id,
        actor_id=actor_id,
        tool_name=CREATE_TICKET_TOOL_NAME,
        arguments=dict(fields),
        ttl_seconds=resolved_settings.tool_confirmation_ttl_seconds,
    )
    return confirmation_id
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_agent_via_mcp.py -q`
Expected: PASS

- [ ] **Step 5: 改造 `console_agent_service.py` graph 注入**（`graph` 属性，约 229-236 行）

将 graph 构建改为按配置注入 MCP 版：

```python
    def _build_graph(self) -> Any:
        if self.settings.agent_mcp_tools_enabled:
            from app.agents.mcp_tool_adapters import (
                create_mcp_order_query_executor,
                create_mcp_ticket_creator,
            )

            ticket_creator = create_mcp_ticket_creator(self.settings)
            order_query_executor = create_mcp_order_query_executor(self.settings)
        else:
            ticket_creator = JavaTicketClient.from_settings(self.settings)
            order_query_executor = lambda arguments: query_order(arguments, settings=self.settings)
        return build_ticket_agent_graph_for_model_mode(
            ticket_creator=ticket_creator,
            order_query_executor=order_query_executor,
            checkpointer=self._create_redis_checkpointer(),
            interrupt_confirmation=True,
        )
```

并将 `graph` 属性中 `self._graph = build_ticket_agent_graph_for_model_mode(...)` 替换为 `self._graph = self._build_graph()`。

- [ ] **Step 6: 确认登记接入 `decide_ticket_confirmation`**（`console_agent_service.py`，约 421-430 行）

在 `resume_ticket_confirmation_interrupt` 成功后、`_to_response` 前，若 `approved` 为 True 则登记确认凭证：

```python
        tokens = set_business_context(user_id=actor.user_id, tenant_id=actor.tenant_id)
        try:
            state = resume_ticket_confirmation_interrupt(
                self.graph,
                thread_id=thread_id,
                approved=approved,
                actor_id=actor.user_id,
            )
            if approved:
                from app.agents.mcp_tool_adapters import register_ticket_confirmation

                register_ticket_confirmation(
                    actor_id=actor.user_id,
                    fields=fields,
                    settings=self.settings,
                )
        finally:
            reset_business_context(tokens)
```

（`fields` 已在方法中通过 `snapshot.values.get("ticket_fields")` 获得，且已校验为 dict；`register_ticket_confirmation` 的参数类型为 `TicketFields` TypedDict，若静态类型检查报冲突，可在调用处加 `# type: ignore` 或断言。）

- [ ] **Step 7: 跑全部 Agent/MCP 相关测试确认不回归**

Run: `cd projects/ai-service && uv run pytest tests/test_agent_via_mcp.py tests/test_console_agent_api.py tests/test_ticket_agent_intent.py tests/test_mcp_product_server.py -q`
Expected: PASS

- [ ] **Step 8: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/agents/mcp_tool_adapters.py projects/ai-service/app/services/console_agent_service.py projects/ai-service/tests/test_agent_via_mcp.py
git commit -m "feat: route ticket agent tool calls through MCP with shared confirmation"
```

---

### Task 6: 文档更新

**Files:**
- Modify: `docs/project-handoff-for-vibe-coding.md`（第 17 节表格 MCP 行 + 第 9 节 MCP 行）
- Modify: `projects/ai-service/.env.example`（Task 1 已加，若需补充说明可微调）

**Interfaces:** 无新接口。

- [ ] **Step 1: 更新交接文档第 9 节**（`docs/project-handoff-for-vibe-coding.md`）

将表格中的 MCP 行：

```text
| MCP | 有 MCP Server 与资源能力；当前 Vue 客服 Agent 未通过 MCP 调外部业务系统。 |
```

改为：

```text
| MCP | 学习型 minimal server 保留；产品主链路新增 product MCP server（streamable HTTP :9100）+ product MCP client，Agent 的 query_order/create_ticket 经 MCP 调用，确认凭证经共享存储校验。 |
```

- [ ] **Step 2: 更新交接文档第 17 节**

将表格中的 MCP 行：

```text
| MCP | `app/mcp_servers`、`app/mcp_clients` | 有资源和 smoke 测试；客服 Agent 未把外部 MCP 工具作为业务工具。 |
```

改为：

```text
| MCP | `app/mcp_servers`（minimal + product）、`app/mcp_clients`（minimal + product） | 学习型 minimal server 保留；产品级 product server（独立进程，streamable HTTP :9100，Bearer token 认证）与 product client 已接入客服 Agent 主链路。启动：`cd projects/ai-service && uv run python -m app.mcp_servers.product_server`。配置：`MCP_PRODUCT_BASE_URL` / `MCP_PRODUCT_AUTH_TOKEN` / `TOOL_CONFIRMATION_BACKEND` / `AGENT_MCP_TOOLS_ENABLED`。 |
```

- [ ] **Step 3: 更新交接文档"已知运行问题"表**（第 16 节，可选）

在表格中追加一行：

```text
| MCP 联调时 Agent 报 `MCP_SERVER_UNREACHABLE` | 未启动 product MCP server：先运行 `uv run python -m app.mcp_servers.product_server`（监听 9100）；或检查 `MCP_PRODUCT_AUTH_TOKEN` 是否与 server 启动环境一致。 |
```

- [ ] **Step 4: 复查文档**（grep 确认无遗留旧表述）

Run: `cd D:\wendang\java+python+ai && grep -n "未通过 MCP\|未把外部 MCP" docs/project-handoff-for-vibe-coding.md`
Expected: 无匹配

- [ ] **Step 5: Commit**（仅用户明确要求时执行）

```bash
git add docs/project-handoff-for-vibe-coding.md
git commit -m "docs: update MCP product chain status in handoff doc"
```

---

### Task 7: 全量回归与真实联调验收

**Files:** 无新文件；运行既有与新增测试。

**Interfaces:** 无。

- [ ] **Step 1: Python 全量测试**

Run: `cd projects/ai-service && uv run pytest -q`
Expected: 全绿（既有 1288 + 新增约 20 项）

- [ ] **Step 2: Java 回归（验证边界未破坏）**

Run: `cd projects/java-business-service && mvn test -q`
Expected: 全绿

- [ ] **Step 3: 前端构建（确认流程无前端改动）**

Run: `cd projects/customer-service-console && npm run build`
Expected: 构建通过

- [ ] **Step 4: 真实联调——订单查询路径**（需 MySQL/Redis/Qdrant/VM 容器/模型 API）

前置：确认 MySQL、Redis、Qdrant 可用（VMware Ubuntu 启动）；`.env` 设置 `TOOL_CONFIRMATION_BACKEND=redis`、`AGENT_MCP_TOOLS_ENABLED=true`、`MCP_PRODUCT_AUTH_TOKEN=<token>`。

按顺序启动：

```powershell
# 终端 1：product MCP server
Set-Location D:\wendang\java+python+ai\projects\ai-service
uv run python -m app.mcp_servers.product_server

# 终端 2：Java
Set-Location D:\wendang\java+python+ai\projects\java-business-service
mvn spring-boot:run

# 终端 3：Python
Set-Location D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

# 终端 4：Vue
Set-Location D:\wendang\java+python+ai\projects\customer-service-console
npm run dev
```

浏览器打开 AI 客服页，输入"查一下我的订单 A1001 物流"，预期：Agent 识别 `order_query` → 经 product MCP server 调 Java 订单接口 → 前端流式展示回答；AI 服务日志出现 `product_mcp_*` 与 Java trace 链。

- [ ] **Step 5: 真实联调——工单创建路径**

浏览器输入"我要申请退款工单，订单 A1001 破损"，预期：Agent 提取字段 → 前端展示确认卡片 → 用户确认 → 确认凭证写入 Redis → 经 product MCP server 调 Java 创建工单 → 工单列表可见；无 token 的 `curl.exe http://127.0.0.1:9100/mcp` 返回 401。

验证点：
1. 无 `Authorization` header 请求 MCP 返回 401。
2. AI 服务日志可看到 `product_mcp_client_*` / `product_mcp_create_ticket_*` 记录。
3. Java 侧出现来自 MCP 调用的工单创建 trace。

- [ ] **Step 6: 结果记录**（联调结论写入交接文档第 16 节"已知运行问题"或本地运行笔记）

---

## Self-Review 记录

**1. Spec coverage（对照 `2026-08-05-mcp-product-chain-design.md`）：**
- 2.1 产品级 server（streamable HTTP :9100、Bearer 认证、白名单 2 工具、复用守卫）→ Task 3
- 2.2 产品级 client（连接/超时/重试/校验/list_tools 缓存）→ Task 4
- 2.3 Agent 改造（两节点经 MCP、图结构不变、lambda 注入）→ Task 5
- 2.4 写操作确认（确认凭证共享、MCP server 校验）→ Task 2 + Task 3 + Task 5
- 2.5 错误处理与降级（不可达/超时/工具错误/配置缺失）→ Task 4（AppException 映射）+ Task 5（Agent 既有失败分类复用）
- 3.1 四个测试文件 → Task 2（test_tool_confirmation_redis）、Task 3（test_mcp_product_server）、Task 4（test_mcp_product_client）、Task 5（test_agent_via_mcp）
- 3.2 真实联调两条路径 → Task 7
- 3.3 质量回归（pytest/mvn/npm）→ Task 7
- 3.4 文档（交接文档第 17 节 + .env.example）→ Task 1 + Task 6
- 4 配置项 4 个 → Task 1（扩展为 7 个，含 port/backend/enabled）

**2. Placeholder scan：** 无 TBD/TODO；所有任务含具体代码与测试。

**3. Type consistency：**
- `McpToolCaller.call_tool(tool_name, arguments) -> dict` 在 Task 4 定义，Task 5 的 `McpTicketCreator`/`mcp_order_query_executor` 一致使用。
- `register_confirmed(*, confirmation_id, actor_id, tool_name, arguments, ttl_seconds)` 在 Task 2 定义（内存版与 Redis 版同签名），Task 5 调用一致。
- `create_tool_confirmation_store(settings)` 返回类型 `ToolConfirmationStore | RedisToolConfirmationStore`，两版均有 `require_confirmed`/`register_confirmed`。
- `confirmation_id` 契约：Agent 侧 16 位 hex（`build_ticket_confirmation_id`）→ 产品级 MCP pattern `^[a-f0-9]{16,32}$`（Task 3）→ `run_idempotent_tool` 幂等键（Task 3）一致。
- `MCP_PRODUCT_AUTH_TOKEN` 命名在 config（Task 1）、server（Task 3）、client（Task 4）、文档（Task 6）全一致。
