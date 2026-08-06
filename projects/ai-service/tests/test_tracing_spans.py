import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from app.agents.tracing_spans import (
    set_span_attributes,
    start_agent_span,
    start_java_span,
    start_llm_span,
    start_tool_span,
)
from app.core.config import Settings
from app.core.telemetry import setup_telemetry, shutdown_telemetry


def _reset_tracer_provider() -> None:
    # trace.set_tracer_provider is global AND guarded by a once-lock
    # (_TRACER_PROVIDER_SET_ONCE): after the first call it no-ops with a warning,
    # so resetting only _TRACER_PROVIDER is not enough. The public API cannot
    # clear the provider (set_tracer_provider(None) raises), so touch privates.
    trace._TRACER_PROVIDER = None  # type: ignore[attr-defined]
    once = getattr(trace, "_TRACER_PROVIDER_SET_ONCE", None)
    if once is not None:
        once._done = False  # type: ignore[attr-defined]


@pytest.fixture(autouse=True)
def reset_tracer_provider() -> None:
    # Reset the global provider state before and after each test so tests are
    # order-independent and each can install a fresh SDK TracerProvider.
    _reset_tracer_provider()
    yield
    _reset_tracer_provider()


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
    assert spans[0].status.status_code == trace.StatusCode.ERROR  # STATUS_ERROR
    exporter.clear()
