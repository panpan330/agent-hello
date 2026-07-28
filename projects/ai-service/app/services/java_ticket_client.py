import logging
from time import perf_counter
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import AppException
from app.core.trace import TRACE_ID_HEADER, build_trace_headers
from app.schemas.ticket import CreateTicketArgs, CreatedTicket
from app.services.java_error_mapping import build_java_error_app_exception


logger = logging.getLogger(__name__)


class JavaTicketClient:
    """HTTP adapter for the ticket-creation API owned by the Java service."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.strip().rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    @classmethod
    def from_settings(cls, settings: Settings) -> "JavaTicketClient":
        return cls(
            base_url=settings.resolved_java_mock_service_base_url,
            timeout_seconds=settings.java_mock_service_timeout_seconds,
        )

    def create_ticket(
        self,
        arguments: CreateTicketArgs,
        *,
        idempotency_key: str,
    ) -> CreatedTicket:
        path = "/tickets"
        start_time = perf_counter()
        logger.info(
            (
                "java_ticket_create_started method=POST path=%s category=%s "
                "priority=%s related_order_id=%s"
            ),
            path,
            arguments.category,
            arguments.priority,
            arguments.related_order_id,
        )
        try:
            with httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.post(
                    path,
                    json=arguments.model_dump(mode="json"),
                    headers={
                        **build_trace_headers(),
                        "Idempotency-Key": idempotency_key,
                    },
                )
        except httpx.TimeoutException as exc:
            elapsed_ms = (perf_counter() - start_time) * 1000
            logger.warning(
                "java_ticket_create_failed method=POST path=%s code=%s elapsed_ms=%.2f",
                path,
                "TOOL_TIMEOUT",
                elapsed_ms,
            )
            raise AppException(
                code="TOOL_TIMEOUT",
                message="创建工单工具调用超时，请稍后重试。",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            elapsed_ms = (perf_counter() - start_time) * 1000
            logger.warning(
                "java_ticket_create_failed method=POST path=%s code=%s elapsed_ms=%.2f",
                path,
                "TOOL_UPSTREAM_ERROR",
                elapsed_ms,
            )
            raise AppException(
                code="TOOL_UPSTREAM_ERROR",
                message="工单业务服务暂时不可用，请稍后重试。",
                status_code=502,
            ) from exc

        elapsed_ms = (perf_counter() - start_time) * 1000
        logger.info(
            (
                "java_ticket_create_finished method=POST path=%s status_code=%s "
                "upstream_trace_id=%s elapsed_ms=%.2f"
            ),
            path,
            response.status_code,
            response.headers.get(TRACE_ID_HEADER, "-"),
            elapsed_ms,
        )

        if response.status_code != 201:
            raise build_java_error_app_exception(
                response,
                operation="ticket_creation",
                fallback_code="TICKET_UPSTREAM_REJECTED",
                fallback_message="工单业务服务拒绝了已经校验过的请求，请联系管理员排查接口契约。",
                fallback_status_code=502,
            )

        try:
            payload: Any = response.json()
        except ValueError as exc:
            raise AppException(
                code="TOOL_RESULT_VALIDATION_FAILED",
                message="工单业务服务返回的 JSON 格式不正确。",
                status_code=502,
            ) from exc

        try:
            ticket = CreatedTicket.model_validate(payload)
        except ValidationError as exc:
            raise AppException(
                code="TOOL_RESULT_VALIDATION_FAILED",
                message="工单业务服务返回的数据不符合约定。",
                status_code=502,
                details=exc.errors(include_url=False),
            ) from exc
        logger.info(
            "java_ticket_create_validated ticket_id=%s category=%s priority=%s",
            ticket.ticket_id,
            ticket.category,
            ticket.priority,
        )
        return ticket
