from datetime import datetime, timezone
import logging

import httpx
import pytest

from app.core.exceptions import AppException
from app.core.trace import TRACE_ID_HEADER, reset_trace_id, set_trace_id
from app.schemas.ticket import CreateTicketArgs
from app.services.java_ticket_client import JavaTicketClient


def make_arguments() -> CreateTicketArgs:
    return CreateTicketArgs(
        requester_id="demo_user_001",
        title="订单 A1001 一直未发货",
        description="订单 A1001 已付款一周仍未发货，请帮我处理。",
        category="complaint",
        priority="high",
        related_order_id="A1001",
    )


def test_java_ticket_client_sends_validated_arguments_and_validates_response(
    caplog: pytest.LogCaptureFixture,
) -> None:
    received_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received_request["method"] = request.method
        received_request["path"] = request.url.path
        received_request["body"] = request.content.decode("utf-8")
        received_request["idempotency_key"] = request.headers["Idempotency-Key"]
        received_request["trace_id"] = request.headers[TRACE_ID_HEADER]
        return httpx.Response(
            201,
            json={
                **make_arguments().model_dump(mode="json"),
                "ticket_id": "T1001",
                "created_at": datetime(2026, 7, 12, tzinfo=timezone.utc).isoformat(),
            },
            headers={TRACE_ID_HEADER: "trace-ticket-client-001"},
        )

    caplog.set_level(logging.INFO, logger="app.services.java_ticket_client")
    client = JavaTicketClient(
        base_url="http://java-mock.test",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )
    token = set_trace_id("trace-ticket-client-001")

    try:
        result = client.create_ticket(
            make_arguments(),
            idempotency_key="confirmation-idempotency-001",
        )
    finally:
        reset_trace_id(token)

    assert received_request["method"] == "POST"
    assert received_request["path"] == "/tickets"
    assert "demo_user_001" in str(received_request["body"])
    assert received_request["idempotency_key"] == "confirmation-idempotency-001"
    assert received_request["trace_id"] == "trace-ticket-client-001"
    assert "upstream_trace_id=trace-ticket-client-001" in caplog.text
    assert result.ticket_id == "T1001"
    assert result.created_at == datetime(2026, 7, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("response", "code"),
    [
        (httpx.Response(500), "TOOL_UPSTREAM_ERROR"),
        (httpx.Response(400), "TICKET_UPSTREAM_REJECTED"),
        (httpx.Response(201, content=b"not-json"), "TOOL_RESULT_VALIDATION_FAILED"),
    ],
)
def test_java_ticket_client_maps_untrusted_upstream_failures(
    response: httpx.Response,
    code: str,
) -> None:
    client = JavaTicketClient(
        base_url="http://java-mock.test",
        timeout_seconds=1,
        transport=httpx.MockTransport(lambda request: response),
    )

    with pytest.raises(AppException) as exc_info:
        client.create_ticket(
            make_arguments(),
            idempotency_key="confirmation-idempotency-002",
        )

    assert exc_info.value.code == code


def test_java_ticket_client_maps_order_not_support_ticket_to_user_safe_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "success": False,
                "code": "ORDER_NOT_SUPPORT_TICKET",
                "message": "当前订单不支持创建该类工单。",
            },
            request=request,
        )

    client = JavaTicketClient(
        base_url="http://java-mock.test",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AppException) as exc_info:
        client.create_ticket(
            make_arguments(),
            idempotency_key="confirmation-idempotency-003",
        )

    exc = exc_info.value
    assert exc.code == "ORDER_NOT_SUPPORT_TICKET"
    assert exc.message == "当前订单暂不支持创建这类工单，如需帮助可以联系人工客服。"
    assert exc.status_code == 409


def test_java_ticket_client_maps_idempotency_conflict_to_reconfirm_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "success": False,
                "code": "IDEMPOTENCY_KEY_CONFLICT",
                "message": "同一个幂等键不能用于不同的请求参数。",
            },
            request=request,
        )

    client = JavaTicketClient(
        base_url="http://java-mock.test",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AppException) as exc_info:
        client.create_ticket(
            make_arguments(),
            idempotency_key="confirmation-idempotency-004",
        )

    exc = exc_info.value
    assert exc.code == "IDEMPOTENCY_KEY_CONFLICT"
    assert exc.message == "本次提交和已确认的工单请求不一致，请重新确认后再提交。"
    assert exc.status_code == 409
