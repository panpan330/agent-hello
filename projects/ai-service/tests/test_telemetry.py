from typing import Generator

import pytest
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


@pytest.fixture(autouse=True)
def reset_tracer_provider() -> Generator[None, None, None]:
    # trace.set_tracer_provider is global; reset it so each test starts clean.
    # NOTE: uses the private _TRACER_PROVIDER attribute as the opentelemetry
    # public API does not allow clearing the provider (set_tracer_provider(None) raises).
    trace._TRACER_PROVIDER = None  # type: ignore[attr-defined]
    yield
    trace._TRACER_PROVIDER = None  # type: ignore[attr-defined]


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
