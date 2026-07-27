from fastapi import APIRouter

from app.schemas.health import HealthResponse, ReadinessCheck, ReadinessResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="java-mock-service")


@router.get("/ready", response_model=ReadinessResponse)
def ready() -> ReadinessResponse:
    return ReadinessResponse(
        status="ready",
        service="java-mock-service",
        ready=True,
        checks=[
            ReadinessCheck(
                name="in_memory_order_store",
                status="ok",
                required=True,
                message="In-memory order store is available.",
            ),
            ReadinessCheck(
                name="in_memory_ticket_store",
                status="ok",
                required=True,
                message="In-memory ticket store is available.",
            ),
        ],
    )
