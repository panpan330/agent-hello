from collections.abc import Mapping
import logging
from time import perf_counter
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import AppException
from app.core.trace import TRACE_ID_HEADER, build_trace_headers
from app.services.java_error_mapping import build_java_error_app_exception


logger = logging.getLogger(__name__)


class JavaOrderClient:
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
    def from_settings(cls, settings: Settings) -> "JavaOrderClient":
        return cls(
            base_url=settings.resolved_java_mock_service_base_url,
            timeout_seconds=settings.java_mock_service_timeout_seconds,
        )

    def get_order(self, order_id: str) -> Mapping[str, Any]:
        path = f"/orders/{order_id}"
        start_time = perf_counter()
        logger.info(
            "java_order_request_started method=GET path=%s order_id=%s",
            path,
            order_id,
        )
        try:
            with httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.get(path, headers=build_trace_headers())
        except httpx.TimeoutException as exc:
            elapsed_ms = (perf_counter() - start_time) * 1000
            logger.warning(
                "java_order_request_failed method=GET path=%s order_id=%s code=%s elapsed_ms=%.2f",
                path,
                order_id,
                "TOOL_TIMEOUT",
                elapsed_ms,
            )
            raise AppException(
                code="TOOL_TIMEOUT",
                message="订单查询工具调用超时，请稍后重试。",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            elapsed_ms = (perf_counter() - start_time) * 1000
            logger.warning(
                "java_order_request_failed method=GET path=%s order_id=%s code=%s elapsed_ms=%.2f",
                path,
                order_id,
                "TOOL_UPSTREAM_ERROR",
                elapsed_ms,
            )
            raise AppException(
                code="TOOL_UPSTREAM_ERROR",
                message="订单查询服务暂时不可用，请稍后重试。",
                status_code=502,
            ) from exc

        elapsed_ms = (perf_counter() - start_time) * 1000
        logger.info(
            (
                "java_order_request_finished method=GET path=%s order_id=%s "
                "status_code=%s upstream_trace_id=%s elapsed_ms=%.2f"
            ),
            path,
            order_id,
            response.status_code,
            response.headers.get(TRACE_ID_HEADER, "-"),
            elapsed_ms,
        )

        if response.status_code != 200:
            raise build_java_error_app_exception(
                response,
                operation="order_query",
                fallback_code="TOOL_UPSTREAM_ERROR",
                fallback_message="订单查询服务返回了无法处理的状态，请稍后重试。",
                fallback_status_code=502,
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise AppException(
                code="TOOL_RESULT_VALIDATION_FAILED",
                message="订单查询服务返回的 JSON 格式不正确。",
                status_code=502,
            ) from exc

        if not isinstance(data, dict):
            raise AppException(
                code="TOOL_RESULT_VALIDATION_FAILED",
                message="订单查询服务返回的数据结构不正确。",
                status_code=502,
            )

        return data
