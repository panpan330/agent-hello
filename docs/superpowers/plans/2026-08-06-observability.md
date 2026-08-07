# 可观测性真实接入 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把可观测性从"纸上设计"升级为真实接入：Python 服务通过 OpenTelemetry SDK 导出真实 span 到本机 OTLP Collector（:4317），LangSmith 条件启用（有 key 才上报），覆盖 HTTP → Agent 图 → LLM → 工具调用的完整链路。

**Architecture:** 新增 `app/core/telemetry.py`（TracerProvider + OTLP exporter + LangSmith 条件初始化统一入口）与 `app/agents/tracing_spans.py`（span 辅助函数）；`main.py` create_app/lifespan 接入初始化；middleware/console_agent_service/LLM 调用/MCP client/Java client 六处埋点；现有 `otel_tracing.py`/`langsmith_tracing.py` 的 plan 数据类保留不动，`to_langgraph_config()` 接入 graph config。

**Tech Stack:** Python 3.12、uv、opentelemetry-sdk、opentelemetry-exporter-otlp、langsmith（新增直接依赖）、FastAPI、LangGraph。

## Global Constraints

- 规格文件：`docs/superpowers/specs/2026-08-06-observability-design.md`（已获用户认可）。
- OTEL 导出目标：本机 Docker OTLP Collector，endpoint `http://localhost:4317`（OTLP/gRPC），service name `ai-service`。
- LangSmith 条件启用：启用条件 = `LANGSMITH_TRACING=true` **且** `LANGSMITH_API_KEY` 非空；任一不满足则跳过，缺 key 记 `langsmith_skipped_no_api_key` 日志。
- 新增依赖（pyproject.toml 声明）：`opentelemetry-sdk`、`opentelemetry-exporter-otlp`、`langsmith`（均为官方库；langsmith 已作为传递依赖存在，需提为直接依赖）。
- 测试约束：自动测试不调用真实模型、不连接真实 Collector/LangSmith（用内存 exporter 或注入 fake）；`Settings(_env_file=None)` 默认 `otel_exporter_otlp_endpoint` 为空/禁用，保证既有 1395 测试全绿且不尝试导出。
- 现有 `otel_tracing.py` / `langsmith_tracing.py` 的 plan 数据类**保留不动**（供学习/测试）；`tracing_spans.py` 是新增的真实 span 适配层。
- Java/前端不改（X-Trace-Id 契约保持，不引入 W3C traceparent）。
- 既有 Python 1395 测试必须全绿；Java 49 tests 全绿；前端 build 通过。
- Git：按项目协作偏好，只有用户明确要求才执行 `git commit`/`git push`；计划中 Commit 步骤默认跳过，仅在用户指示时执行。

---

### Task 1: 配置项与依赖

**Files:**
- Modify: `projects/ai-service/pyproject.toml`（dependencies 追加 3 项）
- Modify: `projects/ai-service/app/core/config.py`（Settings 类，在 `log_level` 附近追加）
- Modify: `projects/ai-service/.env.example`（追加配置说明块）
- Test: `projects/ai-service/tests/test_config.py`

**Interfaces:**
- Consumes: 现有 `Settings` 模式（`resolved_*` 属性）、`get_settings()`
- Produces: `Settings` 新增字段（全部有默认值，`Settings(_env_file=None)` 可用）：
  - `otel_exporter_otlp_endpoint: str = Field(default="")`（空 = 禁用导出，测试环境安全）
  - `otel_service_name: str = Field(default="ai-service")`
  - `langsmith_tracing: bool = Field(default=False)`
  - `langsmith_api_key: str | None = Field(default=None, repr=False)`
- Produces: resolved 属性：
  - `resolved_otel_exporter_otlp_endpoint: str | None`（strip 后非空；空 → None）
  - `resolved_langsmith_api_key: str | None`（strip 后非空；空 → None）
  - `langsmith_enabled: bool`（`langsmith_tracing is True and resolved_langsmith_api_key is not None`）

- [ ] **Step 1: 写失败测试**（追加到 `tests/test_config.py`）

```python
def test_observability_settings_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.otel_exporter_otlp_endpoint == ""
    assert settings.otel_service_name == "ai-service"
    assert settings.langsmith_tracing is False
    assert settings.langsmith_api_key is None
    assert settings.resolved_otel_exporter_otlp_endpoint is None
    assert settings.langsmith_enabled is False


def test_observability_settings_env_overrides() -> None:
    settings = Settings(
        _env_file=None,
        otel_exporter_otlp_endpoint=" http://localhost:4317 ",
        otel_service_name="ai-service-test",
        langsmith_tracing=True,
        langsmith_api_key="ls-key-123",
    )
    assert settings.resolved_otel_exporter_otlp_endpoint == "http://localhost:4317"
    assert settings.otel_service_name == "ai-service-test"
    assert settings.langsmith_enabled is True


def test_langsmith_enabled_requires_both_tracing_and_key() -> None:
    without_key = Settings(_env_file=None, langsmith_tracing=True)
    assert without_key.langsmith_enabled is False

    without_tracing = Settings(_env_file=None, langsmith_api_key="ls-key-123")
    assert without_tracing.langsmith_enabled is False
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_config.py::test_observability_settings_defaults -q`
Expected: FAIL（`AttributeError: 'Settings' object has no attribute 'otel_exporter_otlp_endpoint'`）

- [ ] **Step 3: 更新 `pyproject.toml`**（dependencies 列表末尾追加）

```toml
    "langsmith>=0.1.0",
    "opentelemetry-exporter-otlp>=1.24.0",
    "opentelemetry-sdk>=1.24.0",
```

- [ ] **Step 4: 实现 config 字段**（`app/core/config.py`，在 `log_level` 字段后追加）

```python
    otel_exporter_otlp_endpoint: str = Field(default="")
    otel_service_name: str = Field(default="ai-service")
    langsmith_tracing: bool = Field(default=False)
    langsmith_api_key: str | None = Field(default=None, repr=False)
```

在 `resolved_supervisor_router_mode` 属性后追加：

```python
    @property
    def resolved_otel_exporter_otlp_endpoint(self) -> str | None:
        value = self.otel_exporter_otlp_endpoint.strip()
        return value or None

    @property
    def resolved_langsmith_api_key(self) -> str | None:
        value = (self.langsmith_api_key or "").strip()
        return value or None

    @property
    def langsmith_enabled(self) -> bool:
        return self.langsmith_tracing and self.resolved_langsmith_api_key is not None
```

- [ ] **Step 5: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_config.py -q`
Expected: PASS

- [ ] **Step 6: 更新 `.env.example`**（末尾追加）

```text
# 可观测性：OpenTelemetry 真实接入（本机 OTLP Collector :4317）
# 留空 = 禁用 OTEL 导出（测试/无 Collector 环境）
OTEL_EXPORTER_OTLP_ENDPOINT=""
OTEL_SERVICE_NAME="ai-service"
# LangSmith 条件启用：需 LANGSMITH_TRACING=true 且 LANGSMITH_API_KEY 非空
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=""
```

- [ ] **Step 7: 安装依赖并确认**

Run: `cd projects/ai-service && uv sync`
Expected: 依赖安装成功，`uv run pytest tests/test_config.py -q` 全绿

- [ ] **Step 8: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/pyproject.toml projects/ai-service/uv.lock projects/ai-service/app/core/config.py projects/ai-service/.env.example projects/ai-service/tests/test_config.py
git commit -m "feat: add observability settings and otel/langsmith dependencies"
```

---

### Task 2: `app/core/telemetry.py`（统一初始化）

**Files:**
- Create: `projects/ai-service/app/core/telemetry.py`
- Test: `projects/ai-service/tests/test_telemetry.py`（新建）

**Interfaces:**
- Consumes: `Settings`（`resolved_otel_exporter_otlp_endpoint`、`otel_service_name`、`langsmith_enabled`、`resolved_langsmith_api_key`）、`logging`
- Produces:
  - `def setup_telemetry(settings: Settings | None = None) -> None`：初始化 OTEL TracerProvider + OTLP exporter（endpoint 非空时）；配置 LangSmith 环境变量（`langsmith_enabled` 时设 `LANGSMITH_TRACING=true`/`LANGCHAIN_TRACING_V2=true`/`LANGSMITH_API_KEY`/`LANGCHAIN_PROJECT`）；幂等（重复调用不重建）；任何异常记 `telemetry_setup_failed` 日志但不抛出
  - `def get_tracer() -> Tracer`：返回项目 tracer（service name）
  - `def shutdown_telemetry() -> None`：flush + shutdown TracerProvider
  - `def is_telemetry_enabled() -> bool`：endpoint 是否已配置
  - `def get_otel_trace_id() -> str | None`：当前 span 的 OTEL trace_id（hex），无 span 返回 None

- [ ] **Step 1: 写失败测试**（新建 `tests/test_telemetry.py`）

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from app.core.config import Settings
from app.core.telemetry import (
    get_otel_trace_id,
    get_tracer,
    is_telemetry_enabled,
    setup_telemetry,
    shutdown_telemetry,
)


def test_telemetry_disabled_when_endpoint_empty() -> None:
    settings = Settings(_env_file=None)  # otel_exporter_otlp_endpoint=""
    assert is_telemetry_enabled() is False


def test_telemetry_enabled_when_endpoint_configured() -> None:
    settings = Settings(
        _env_file=None,
        otel_exporter_otlp_endpoint="http://localhost:4317",
    )
    setup_telemetry(settings)
    assert is_telemetry_enabled() is True
    tracer = get_tracer()
    assert tracer is not None
    shutdown_telemetry()


def test_setup_is_idempotent() -> None:
    settings = Settings(
        _env_file=None,
        otel_exporter_otlp_endpoint="http://localhost:4317",
    )
    setup_telemetry(settings)
    provider1 = trace.get_tracer_provider()
    setup_telemetry(settings)
    provider2 = trace.get_tracer_provider()
    assert provider1 is provider2
    shutdown_telemetry()


def test_get_otel_trace_id_returns_none_without_span() -> None:
    assert get_otel_trace_id() is None


def test_setup_failure_does_not_raise() -> None:
    # endpoint 指向不可达地址，setup 不应抛异常
    settings = Settings(
        _env_file=None,
        otel_exporter_otlp_endpoint="http://127.0.0.1:1",
    )
    setup_telemetry(settings)  # 不应 raise
    shutdown_telemetry()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_telemetry.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.core.telemetry'`）

- [ ] **Step 3: 实现**（新建 `app/core/telemetry.py`）

```python
"""Telemetry setup: OpenTelemetry SDK + conditional LangSmith tracing."""

import logging
import os
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)

_DEFAULT_SERVICE_NAME = "ai-service"


def _build_resource(service_name: str) -> Resource:
    return Resource.create({"service.name": service_name})


def _configure_langsmith(settings: Settings) -> None:
    """Set LangSmith env vars when the feature is enabled (idempotent)."""
    if not settings.langsmith_enabled:
        return
    api_key = settings.resolved_langsmith_api_key
    if api_key is None:
        return
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", api_key)
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.otel_service_name or _DEFAULT_SERVICE_NAME)
    logger.info(
        "langsmith_tracing_enabled project=%s",
        settings.otel_service_name or _DEFAULT_SERVICE_NAME,
    )


def setup_telemetry(settings: Settings | None = None) -> None:
    """Initialize OTEL SDK and conditional LangSmith tracing.

    Idempotent: calling twice does not rebuild the provider.
    Failures are logged but never raised (service must start regardless).
    """
    resolved_settings = settings or get_settings()
    service_name = resolved_settings.otel_service_name or _DEFAULT_SERVICE_NAME
    endpoint = resolved_settings.resolved_otel_exporter_otlp_endpoint

    if endpoint is None:
        logger.info("otel_export_disabled endpoint not configured")
        return

    try:
        provider = TracerProvider(resource=_build_resource(service_name))
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        logger.info("otel_export_enabled endpoint=%s service_name=%s", endpoint, service_name)
    except Exception:
        logger.exception("otel_setup_failed endpoint=%s", endpoint)
        return

    try:
        _configure_langsmith(resolved_settings)
    except Exception:
        logger.exception("langsmith_setup_failed")


def get_tracer() -> Any:
    return trace.get_tracer(_DEFAULT_SERVICE_NAME)


def shutdown_telemetry() -> None:
    """Flush and shut down the tracer provider (idempotent, never raises)."""
    try:
        provider = trace.get_tracer_provider()
        if isinstance(provider, TracerProvider):
            provider.shutdown()
    except Exception:
        logger.exception("otel_shutdown_failed")


def is_telemetry_enabled() -> bool:
    provider = trace.get_tracer_provider()
    return isinstance(provider, TracerProvider)


def get_otel_trace_id() -> str | None:
    """Return the current span's OTEL trace_id as hex, or None."""
    span = trace.get_current_span()
    if span is None or not span.get_span_context().is_valid:
        return None
    return format(span.get_span_context().trace_id, "032x")
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_telemetry.py -q`
Expected: PASS（注意：`test_telemetry_disabled_when_endpoint_empty` 可能在测试间共享全局 provider 状态——若 `is_telemetry_enabled` 断言受前面测试影响，需要 fixture 重置 provider；如遇此问题，在测试开头 `trace._TRACER_PROVIDER = None` 或使用 `monkeypatch` 重置，报告中说明）

- [ ] **Step 5: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/core/telemetry.py projects/ai-service/tests/test_telemetry.py
git commit -m "feat: add telemetry setup with OTLP exporter and conditional langsmith"
```

---

### Task 3: `app/agents/tracing_spans.py`（span 辅助函数）

**Files:**
- Create: `projects/ai-service/app/agents/tracing_spans.py`
- Test: `projects/ai-service/tests/test_tracing_spans.py`（新建）

**Interfaces:**
- Consumes: `get_tracer()`（Task 2）、`get_otel_trace_id()`（Task 2）、`otel_tracing.py` 的 `build_ticket_agent_otel_span_attributes`（可选复用，`app/agents/otel_tracing.py:259`）
- Produces（全部为 context manager，span 一定结束，异常不影响业务）：
  - `@contextmanager def start_agent_span(*, intent: str | None = None, thread_id: str | None = None, conversation_id: str | None = None) -> Iterator[None]`：span 名 `agent.invoke`，属性 intent/thread_id/conversation_id/trace_id（现有 X-Trace-Id）
  - `@contextmanager def start_llm_span(*, model: str, provider: str, prompt_name: str | None = None) -> Iterator[None]`：span 名 `llm.call`，属性 model/provider/prompt_name；结束时设 prompt_tokens/completion_tokens/total_tokens（若调用方提供）
  - `@contextmanager def start_tool_span(*, tool_name: str) -> Iterator[None]`：span 名 `tool.call`，属性 tool_name；结束时设 status/error_code
  - `@contextmanager def start_java_span(*, path: str, method: str = "GET") -> Iterator[None]`：span 名 `java.call`，属性 path/method
  - `def set_span_attributes(attributes: dict[str, Any]) -> None`：给当前 span 批量设属性
  - 所有辅助函数在 telemetry 未启用（无 TracerProvider）时返回空 context manager（no-op）

- [ ] **Step 1: 写失败测试**（新建 `tests/test_tracing_spans.py`）

```python
from contextlib import nullcontext

import pytest

from app.agents.tracing_spans import (
    set_span_attributes,
    start_agent_span,
    start_java_span,
    start_llm_span,
    start_tool_span,
)
from app.core.config import Settings
from app.core.telemetry import setup_telemetry, shutdown_telemetry


@pytest.fixture()
def otel_enabled() -> None:
    setup_telemetry(
        Settings(
            _env_file=None,
            otel_exporter_otlp_endpoint="http://localhost:4317",
        )
    )
    yield
    shutdown_telemetry()


def test_start_agent_span_creates_span_with_attributes(otel_enabled: None) -> None:
    from opentelemetry import trace

    with start_agent_span(intent="order_query", thread_id="t-1", conversation_id="c-1"):
        span = trace.get_current_span()
        assert span is not None
        attrs = dict(span.attributes)
        assert attrs["intent"] == "order_query"
        assert attrs["thread_id"] == "t-1"
        assert attrs["conversation_id"] == "c-1"
        assert "trace_id" in attrs


def test_start_llm_span_records_token_usage(otel_enabled: None) -> None:
    from opentelemetry import trace

    with start_llm_span(model="qwen3.7-plus", provider="aliyun-compatible", prompt_name="intent") as span_ctx:
        set_span_attributes(
            {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            }
        )
        span = trace.get_current_span()
        assert dict(span.attributes)["model"] == "qwen3.7-plus"
        assert dict(span.attributes)["total_tokens"] == 150


def test_start_tool_span_sets_status(otel_enabled: None) -> None:
    from opentelemetry import trace

    with start_tool_span(tool_name="query_order"):
        span = trace.get_current_span()
        assert dict(span.attributes)["tool_name"] == "query_order"


def test_spans_are_noop_when_telemetry_disabled() -> None:
    # 未 setup_telemetry（默认无 provider）时辅助函数不抛异常
    with start_agent_span(intent="order_query"):
        pass
    with start_llm_span(model="m", provider="p"):
        pass
    with start_tool_span(tool_name="t"):
        pass
    with start_java_span(path="/internal/orders/A1001"):
        pass


def test_span_ends_on_exception(otel_enabled: None) -> None:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    # 用 SimpleSpanProcessor + 内存 exporter 验证异常时 span 仍结束
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    provider = trace.get_tracer_provider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    with pytest.raises(RuntimeError):
        with start_tool_span(tool_name="boom"):
            raise RuntimeError("boom")

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "tool.call"
    assert spans[0].status.status_code == 2  # STATUS_ERROR
    exporter.clear()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_tracing_spans.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.agents.tracing_spans'`）

- [ ] **Step 3: 实现**（新建 `app/agents/tracing_spans.py`）

```python
"""Real OTEL span helpers translating the plan dataclasses into actual spans.

The plan dataclasses in otel_tracing.py / langsmith_tracing.py remain for
learning/tests; this module is the production adapter.
"""

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace

from app.core.telemetry import get_otel_trace_id, get_tracer, is_telemetry_enabled
from app.core.trace import get_trace_id


def _current_span() -> Any:
    return trace.get_current_span()


def _set_common_attributes() -> None:
    """Attach the app's X-Trace-Id to the current span for log/span correlation."""
    x_trace_id = get_trace_id()
    if x_trace_id and x_trace_id != "-":
        set_span_attributes({"trace_id": x_trace_id})
    otel_trace_id = get_otel_trace_id()
    if otel_trace_id:
        set_span_attributes({"otel_trace_id": otel_trace_id})


def set_span_attributes(attributes: dict[str, Any]) -> None:
    span = _current_span()
    if span is None or not span.is_recording():
        return
    span.set_attributes(attributes)


@contextmanager
def start_agent_span(
    *,
    intent: str | None = None,
    thread_id: str | None = None,
    conversation_id: str | None = None,
) -> Iterator[None]:
    if not is_telemetry_enabled():
        yield
        return
    tracer = get_tracer()
    with tracer.start_as_current_span("agent.invoke") as span:
        attrs: dict[str, Any] = {}
        if intent is not None:
            attrs["intent"] = intent
        if thread_id is not None:
            attrs["thread_id"] = thread_id
        if conversation_id is not None:
            attrs["conversation_id"] = conversation_id
        span.set_attributes(attrs)
        _set_common_attributes()
        yield


@contextmanager
def start_llm_span(
    *,
    model: str,
    provider: str,
    prompt_name: str | None = None,
) -> Iterator[None]:
    if not is_telemetry_enabled():
        yield
        return
    tracer = get_tracer()
    with tracer.start_as_current_span("llm.call") as span:
        attrs: dict[str, Any] = {"model": model, "provider": provider}
        if prompt_name is not None:
            attrs["prompt_name"] = prompt_name
        span.set_attributes(attrs)
        _set_common_attributes()
        yield


@contextmanager
def start_tool_span(*, tool_name: str) -> Iterator[None]:
    if not is_telemetry_enabled():
        yield
        return
    tracer = get_tracer()
    with tracer.start_as_current_span("tool.call") as span:
        span.set_attribute("tool_name", tool_name)
        _set_common_attributes()
        yield


@contextmanager
def start_java_span(*, path: str, method: str = "GET") -> Iterator[None]:
    if not is_telemetry_enabled():
        yield
        return
    tracer = get_tracer()
    with tracer.start_as_current_span("java.call") as span:
        span.set_attributes({"path": path, "method": method})
        _set_common_attributes()
        yield
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_tracing_spans.py -q`
Expected: PASS（若 `InMemorySpanExporter` 的导入路径有出入，以实际 SDK 版本为准；`ReadableSpan` 未使用则移除 import）

- [ ] **Step 5: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/agents/tracing_spans.py projects/ai-service/tests/test_tracing_spans.py
git commit -m "feat: add otel span helpers for agent/llm/tool/java calls"
```

---

### Task 4: 六处埋点接入

**Files:**
- Modify: `projects/ai-service/app/main.py`（create_app 接入 setup_telemetry、lifespan 接入 shutdown）
- Modify: `projects/ai-service/app/middleware/tracing.py`（HTTP span）
- Modify: `projects/ai-service/app/services/console_agent_service.py`（agent.invoke span + LangGraph config 传 to_langgraph_config()）
- Modify: `projects/ai-service/app/mcp_clients/product_client.py`（tool.call span）
- Modify: `projects/ai-service/app/services/java_order_client.py` 与 `java_ticket_client.py`（java.call span）
- Modify: `projects/ai-service/app/agents/ticket_agent.py`（LLM 调用点 llm.call span，只加 span 不改核心逻辑）
- Test: `projects/ai-service/tests/test_telemetry_integration.py`（新建）

**Interfaces:**
- Consumes: `setup_telemetry`/`shutdown_telemetry`（Task 2）、`start_agent_span`/`start_llm_span`/`start_tool_span`/`start_java_span`（Task 3）、`to_langgraph_config()`（`app/agents/langsmith_tracing.py:65`）、`build_ticket_agent_thread_config`（`app/agents/ticket_agent.py`）
- Produces: 各埋点接入后的可观测行为（span 树：http.request → agent.invoke → tool.call/java.call/llm.call）

- [ ] **Step 1: 写失败测试**（新建 `tests/test_telemetry_integration.py`）

```python
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.agents.tracing_spans import start_agent_span, start_java_span, start_tool_span
from app.core.config import Settings
from app.core.telemetry import setup_telemetry, shutdown_telemetry


def test_span_parent_child_chain() -> None:
    setup_telemetry(
        Settings(
            _env_file=None,
            otel_exporter_otlp_endpoint="http://localhost:4317",
        )
    )
    provider = trace.get_tracer_provider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    try:
        with start_agent_span(intent="order_query", thread_id="t-1", conversation_id="c-1"):
            with start_tool_span(tool_name="query_order"):
                with start_java_span(path="/internal/orders/A1001", method="GET"):
                    pass
    finally:
        shutdown_telemetry()

    spans = exporter.get_finished_spans()
    by_name = {span.name: span for span in spans}
    assert "agent.invoke" in by_name
    assert "tool.call" in by_name
    assert "java.call" in by_name

    tool_span = by_name["tool.call"]
    agent_span = by_name["agent.invoke"]
    assert tool_span.parent.span_id == agent_span.context.span_id

    java_span = by_name["java.call"]
    assert java_span.parent.span_id == tool_span.context.span_id
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/ai-service && uv run pytest tests/test_telemetry_integration.py -q`
Expected: PASS 或根据实际行为调整（此测试用辅助函数验证 span 层级，辅助函数 Task 3 已实现；若直接通过说明辅助函数正确，继续后续埋点）

- [ ] **Step 3: 接入 main.py**（`app/main.py`）

```python
from app.core.telemetry import setup_telemetry, shutdown_telemetry


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    try:
        yield
    finally:
        shutdown_telemetry()
        app.state.console_agent_service.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    setup_telemetry(settings)
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        lifespan=app_lifespan,
    )
    app.state.console_agent_service = ConsoleAgentService(settings)
    register_exception_handlers(app)
    register_trace_middleware(app)
    ...
```

- [ ] **Step 4: 接入 middleware**（`app/middleware/tracing.py`，在 `trace_request` 函数开头）

```python
from app.agents.tracing_spans import start_agent_span  # noqa: F401（避免循环依赖需放函数内 import）
from app.core.telemetry import is_telemetry_enabled
```

在 `token = set_trace_id(trace_id)` 之后包 span：

```python
        if is_telemetry_enabled():
            from app.agents.tracing_spans import start_http_span

            with start_http_span(
                method=request.method,
                path=request.url.path,
            ):
                return await _call_next_with_span(request, call_next, trace_id, start_time)
        return await _call_next_with_span(request, call_next, trace_id, start_time)
```

注意：middleware 需要新增 `start_http_span` 辅助函数（Task 3 未定义）。请**在 Task 3 的 `tracing_spans.py` 补一个 `start_http_span`**（span 名 `http.request`，属性 method/path），或在 Task 4 中于 middleware 内联创建。建议前者（保持辅助函数集中），在 `tracing_spans.py` 追加：

```python
@contextmanager
def start_http_span(*, method: str, path: str) -> Iterator[None]:
    if not is_telemetry_enabled():
        yield
        return
    tracer = get_tracer()
    with tracer.start_as_current_span("http.request") as span:
        span.set_attributes({"method": method, "path": path})
        _set_common_attributes()
        yield
```

并将 `_call_next_with_span` 定义为现有 `trace_request` 的剩余逻辑（响应处理、日志、header 回写）——为保持行为一致，建议重构：把现有 try/finally 主体提取为内部函数，外层用 span 包住。

- [ ] **Step 5: 接入 console_agent_service**（`app/services/console_agent_service.py`）

在 `reply` 与 `stream_reply` 中包 agent span 并传 LangGraph config：

```python
    def reply(self, *, actor, conversation_id, message, history=None) -> ConsoleAgentResponse:
        thread_id = self._thread_id(actor, conversation_id)
        from app.agents.tracing_spans import start_agent_span
        from app.agents.langsmith_tracing import build_ticket_agent_langsmith_trace_context

        # build_ticket_agent_langsmith_trace_context 需要 state + operation：
        # 最小 state 子集（user_message 即可，metadata 构建容错）；operation="console_agent_reply"
        trace_context = build_ticket_agent_langsmith_trace_context(
            {"user_message": message},
            operation="console_agent_reply",
            thread_id=thread_id,
            actor_id=actor.user_id,
            extra_tags=["console-agent"],
        )
        graph_config = trace_context.to_langgraph_config()
        with start_agent_span(
            intent=None,
            thread_id=thread_id,
            conversation_id=conversation_id,
        ):
            # 现有 reply 主体逻辑（graph.invoke 时把 graph_config 合并进 config）
            ...
```

注意：`build_ticket_agent_langsmith_trace_context` 的签名已确认（`langsmith_tracing.py:196`，需 `state` + `operation` 位置参数，`thread_id`/`actor_id`/`extra_tags` 为关键字）。`graph.invoke` 的 config 合并：`{**build_ticket_agent_thread_config(thread_id), **graph_config}`——两边都含 `configurable.thread_id`（值相同，均为同一 thread_id，无实际冲突；graph_config 在后覆盖，值一致）。`stream_reply` 的 `graph.stream` 同理。保持现有业务逻辑与返回值不变，只加 span 包裹与 config 合并。

- [ ] **Step 6: 接入 product_client**（`app/mcp_clients/product_client.py`，`call_tool` 方法）

```python
    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        from app.agents.tracing_spans import start_tool_span

        with start_tool_span(tool_name=tool_name):
            return self._call_tool_with_retry(tool_name, arguments)
```

（将现有重试逻辑提取为 `_call_tool_with_retry`，或用 `with` 包住现有循环。）

- [ ] **Step 7: 接入 java clients**（`java_order_client.py` 的 `get_order` 与 `java_ticket_client.py` 的 `create_ticket`）

```python
    def get_order(self, order_id: str) -> Mapping[str, Any]:
        from app.agents.tracing_spans import start_java_span

        with start_java_span(path=f"/internal/orders/{order_id}", method="GET"):
            # 现有请求逻辑
            ...
```

（`create_ticket` 同理，path="/internal/tickets"，method="POST"。）

- [ ] **Step 8: 接入 LLM 调用**（`app/agents/ticket_agent.py`，`LLMTicketIntentClassifier.classify_intent` 与字段提取/回答的 LLM 调用点）

在 `classify_intent` 的模型调用处包 span：

```python
        from app.agents.tracing_spans import start_llm_span

        with start_llm_span(
            model=self.settings.llm_model,
            provider=self.settings.llm_provider,
            prompt_name=self.prompt_spec.name,
        ):
            completion = self._get_client().chat.completions.create(...)
```

（token 统计已有 `extract_token_usage`，可在 span 内 `set_span_attributes` 记录；其他 LLM 调用点同理。）

- [ ] **Step 9: 跑测试确认通过**

Run: `cd projects/ai-service && uv run pytest tests/test_telemetry_integration.py tests/test_telemetry.py tests/test_tracing_spans.py -q`
Expected: PASS；再跑 `uv run pytest -q` 全量确认既有 1395 无回归（埋点改动不改变业务行为）

- [ ] **Step 10: Commit**（仅用户明确要求时执行）

```bash
git add projects/ai-service/app/
git commit -m "feat: wire otel spans into http/agent/llm/tool/java calls"
```

---

### Task 5: 本机 OTLP Collector 与文档更新

**Files:**
- Create: `docker-compose.otel.yml`（项目根，或在 compose.yml 追加）
- Modify: `docs/project-handoff-for-vibe-coding.md`（第 9 节 LangSmith/OTEL 行 + 第 17 节表格 + 第 16 节已知运行问题）
- Modify: `projects/ai-service/.env.example`（Task 1 已加，如需补启动说明可微调）

**Interfaces:** 无新接口。

- [ ] **Step 1: 创建 Collector 容器定义**（`docker-compose.otel.yml`）

```yaml
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: otel-collector
    ports:
      - "4317:4317"   # OTLP/gRPC
      - "4318:4318"   # OTLP/HTTP
    volumes:
      - ./otel-collector-config.yml:/etc/otelcol-contrib/config.yaml
    command: ["--config=/etc/otelcol-contrib/config.yaml"]
```

- [ ] **Step 2: 创建 Collector 配置**（`otel-collector-config.yml`）

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
exporters:
  debug:
    verbosity: detailed
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
```

（debug exporter 把 span 打到 Collector 控制台，本地验证即可看到完整 trace。）

- [ ] **Step 3: 更新交接文档第 9 节**

将：

```text
| LangSmith / OpenTelemetry | 有学习型适配和本地 trace 设计；未接入真实 LangSmith 或 OTEL Collector。 |
```

改为：

```text
| LangSmith / OpenTelemetry | 已接入真实 OpenTelemetry（本机 OTLP Collector :4317，`app/core/telemetry.py` + `app/agents/tracing_spans.py`）；LangSmith 条件启用（`LANGSMITH_TRACING=true` 且 `LANGSMITH_API_KEY` 非空才上报）。启动：`docker compose -f docker-compose.otel.yml up -d`。 |
```

- [ ] **Step 4: 更新交接文档第 17 节表格**

将：

```text
| LangSmith/OTEL | `app/agents/langsmith_tracing.py`、`otel_tracing.py` | 有适配/学习实现；未配置外部平台。 |
```

改为：

```text
| LangSmith/OTEL | `app/core/telemetry.py`、`app/agents/tracing_spans.py`（真实接入）；`app/agents/langsmith_tracing.py`、`otel_tracing.py`（plan 数据类，学习/测试保留） | 真实 OTEL 已接入（本机 Collector :4317，span 树 http→agent→llm→tool→java）；LangSmith 条件启用（配 key 即上报）。 |
```

- [ ] **Step 5: 更新交接文档第 16 节已知运行问题表**（追加一行）

```text
| OTEL span 未出现在 Collector | 确认已启动 Collector（`docker compose -f docker-compose.otel.yml up -d`）且 `.env` 设了 `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`；Collector 不可达时服务静默降级（日志 `otel_export_failed`），不影响业务。 |
```

- [ ] **Step 6: 复查文档**

Run: `cd D:\wendang\java+python+ai && grep -n "未接入真实 LangSmith 或 OTEL Collector" docs/project-handoff-for-vibe-coding.md`
Expected: 无匹配

- [ ] **Step 7: Commit**（仅用户明确要求时执行）

```bash
git add docker-compose.otel.yml otel-collector-config.yml docs/project-handoff-for-vibe-coding.md
git commit -m "docs: add otel collector compose and update observability status"
```

---

### Task 6: 全量回归与真实 trace 验证

**Files:** 无新文件；运行既有与新增测试。

**Interfaces:** 无。

- [ ] **Step 1: Python 全量测试**

Run: `cd projects/ai-service && uv run pytest -q`
Expected: 全绿（既有 1395 + 新增）

- [ ] **Step 2: Java 回归（验证边界未破坏）**

Run: `cd projects/java-business-service && mvn test -q`
Expected: BUILD SUCCESS

- [ ] **Step 3: 前端构建（预期无前端改动）**

Run: `cd projects/customer-service-console && npm run build`
Expected: 构建通过

- [ ] **Step 4: 启动 Collector 并验证**

```powershell
cd D:\wendang\java+python+ai
docker compose -f docker-compose.otel.yml up -d
docker compose -f docker-compose.otel.yml logs -f   # 观察 span 输出
```

- [ ] **Step 5: 真实 trace 验证**（需 MySQL/Redis/Qdrant/Java/模型 API）

`.env` 设 `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`（若 Task 1 留空需改），重启 Python 服务。发起真实对话（如"查订单 A1001 物流"），验证点：

1. Collector 日志中出现完整 span 树：`http.request` → `agent.invoke` → `tool.call` → `java.call`。
2. 每个 span 带 `trace_id` attribute，与 AI 服务日志中的 X-Trace-Id 一致（交叉检索）。
3. LangSmith 条件启用：未配 key 时服务正常启动、无报错、无 LangSmith 上报；配 key 后（如有）LangGraph 上报 Agent 执行 trace。

- [ ] **Step 6: 结果记录**（联调结论写入交接文档第 16 节或本地运行笔记）

---

## Self-Review 记录

**1. Spec coverage（对照 `2026-08-06-observability-design.md`）：**
- 2.1 文件组织（telemetry.py / tracing_spans.py / main.py / middleware / 各埋点）→ Task 2/3/4
- 2.2 关键决策（plan 保留、初始化失败不阻断、LangSmith 双条件）→ Task 1（配置）+ Task 2（实现）
- 3.1 span 清单 6 类 → Task 3（辅助函数）+ Task 4（六处埋点）
- 3.2 trace 关联（X-Trace-Id 保留、trace_id attribute）→ Task 3（`_set_common_attributes`）
- 3.3 数据流示例 → Task 4（埋点层级）+ Task 6（真实验证）
- 3.4 错误处理（Collector 不可达降级、LangSmith 跳过、span 辅助函数 try/finally）→ Task 2/3/4
- 4.1 三个测试文件 → Task 2（test_telemetry）、Task 3（test_tracing_spans）、Task 4（test_telemetry_integration）
- 4.2 真实 trace 验证 → Task 6
- 4.3 质量回归（pytest/mvn/npm）→ Task 6
- 4.4 文档（交接文档 9/17/16 + .env.example）→ Task 1 + Task 5
- 5 配置项 4 个 → Task 1

**2. Placeholder scan：** 无 TBD/TODO；所有任务含具体代码与测试。Task 4 标注"start_http_span 需在 Task 3 补"（已在 tracing_spans.py 追加 `start_http_span`）——这是实现期适配提示，非占位符。`build_ticket_agent_langsmith_trace_context` 签名已核实（需 state + operation），计划中调用已按真实签名修正。

**3. Type consistency：**
- `setup_telemetry`/`get_tracer`/`shutdown_telemetry`/`is_telemetry_enabled`/`get_otel_trace_id` 在 Task 2 定义，Task 3/4/6 使用一致。
- `start_agent_span`/`start_llm_span`/`start_tool_span`/`start_java_span`/`set_span_attributes` 在 Task 3 定义，Task 4 埋点使用一致；`start_http_span` 在 Task 4 中补充定义（提示放 Task 3 文件）。
- 配置字段 `otel_exporter_otlp_endpoint`/`otel_service_name`/`langsmith_tracing`/`langsmith_api_key` 及 resolved 属性在 Task 1 定义，Task 2/4/6 使用一致。
- LangSmith 条件启用语义：`langsmith_enabled`（开关 + key 双条件）在 Task 1 定义，Task 2 `_configure_langsmith` 使用一致。
