from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, status

from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse, ReadinessCheck, ReadinessResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="ai-service",
        time=_utc_now(),
    )


@router.get("/ready", response_model=ReadinessResponse)
def readiness_check(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    checks = build_ai_service_readiness_checks(settings)
    ready = all(check.status != "not_configured" for check in checks if check.required)
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if ready else "not_ready",
        service="ai-service",
        ready=ready,
        checks=checks,
        time=_utc_now(),
    )


def build_ai_service_readiness_checks(settings: Settings) -> list[ReadinessCheck]:
    checks = [
        ReadinessCheck(
            name="java_mock_service_base_url",
            status="configured"
            if settings.resolved_java_mock_service_base_url
            else "not_configured",
            required=True,
            message="Java mock service base URL is configured.",
        ),
        ReadinessCheck(
            name="ticket_agent_model_mode",
            status="ok",
            required=True,
            message=f"Ticket Agent model mode is {settings.ticket_agent_model_mode}.",
        ),
        ReadinessCheck(
            name="qdrant_base_url",
            status="configured",
            required=False,
            message="Qdrant base URL is configured for RAG workflows.",
        ),
        ReadinessCheck(
            name="milvus_uri",
            status="configured",
            required=False,
            message="Milvus URI is configured for optional Milvus workflows.",
        ),
    ]
    if settings.ticket_agent_model_mode == "real_llm":
        checks.append(
            ReadinessCheck(
                name="llm_api_key",
                status="configured" if settings.has_llm_api_key else "not_configured",
                required=True,
                message="Real LLM mode requires a configured LLM API key.",
            )
        )
    else:
        checks.append(
            ReadinessCheck(
                name="llm_api_key",
                status="skipped",
                required=False,
                message="LLM API key is not required outside real_llm mode.",
            )
        )
    return checks


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
