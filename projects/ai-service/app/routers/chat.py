import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool

from app.core.ai_security_boundary import (
    redact_sensitive_text,
    require_prompt_injection_safe,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException
from app.core.trace import get_trace_id
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.structured import StructuredOutputRequest, StructuredOutputResponse
from app.schemas.tool_decision import ToolDecisionResponse
from app.services.llm_service import LLMChatService, create_llm_chat_service
from app.services.langchain_chat_model_service import (
    LangChainChatModelService,
    create_langchain_chat_model_service,
)
from app.services.langchain_structured_output_service import (
    LangChainStructuredOutputService,
    create_langchain_structured_output_service,
)
from app.services.structured_output_service import (
    StructuredOutputService,
    create_structured_output_service,
)
from app.services.tool_decision_service import (
    ToolDecisionService,
    create_tool_decision_service,
)
from app.services.tool_calling_chat_service import (
    ToolCallingChatService,
    create_tool_calling_chat_service,
)


logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])
SSE_MEDIA_TYPE = "text/event-stream"
SSE_RECONNECT_DELAY_MS = 3000


def get_llm_chat_service(
    settings: Settings = Depends(get_settings),
) -> LLMChatService:
    return create_llm_chat_service(settings)


def get_langchain_chat_model_service(
    settings: Settings = Depends(get_settings),
) -> LangChainChatModelService:
    return create_langchain_chat_model_service(settings)


def get_langchain_structured_output_service(
    settings: Settings = Depends(get_settings),
) -> LangChainStructuredOutputService:
    return create_langchain_structured_output_service(settings)


def get_structured_output_service(
    settings: Settings = Depends(get_settings),
) -> StructuredOutputService:
    return create_structured_output_service(settings)


def get_tool_decision_service(
    settings: Settings = Depends(get_settings),
) -> ToolDecisionService:
    return create_tool_decision_service(settings)


def get_tool_calling_chat_service(
    settings: Settings = Depends(get_settings),
) -> ToolCallingChatService:
    return create_tool_calling_chat_service(settings)


def format_sse_event(
    event: str,
    data: dict[str, object],
    *,
    event_id: str | None = None,
    retry_ms: int | None = None,
) -> str:
    json_data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    lines: list[str] = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    if retry_ms is not None:
        lines.append(f"retry: {retry_ms}")
    lines.append(f"event: {event}")
    lines.append(f"data: {json_data}")
    return "\n".join(lines) + "\n\n"


def format_sse_comment(comment: str) -> str:
    return f": {comment}\n\n"


def build_sse_headers(*, trace_id: str) -> dict[str, str]:
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "X-Trace-Id": trace_id,
    }


def validate_chat_request_security(request: ChatRequest) -> None:
    require_prompt_injection_safe(request.message, source="user")
    for message in request.history:
        require_prompt_injection_safe(message.content, source="history")


async def build_stream_events(
    chunks: Iterator[str],
    *,
    trace_id: str,
    is_disconnected: Callable[[], Awaitable[bool]] | None = None,
    heartbeat_every_chunks: int = 0,
) -> AsyncIterator[str]:
    yield format_sse_event(
        "start",
        {"trace_id": trace_id},
        event_id=f"{trace_id}:0",
        retry_ms=SSE_RECONNECT_DELAY_MS,
    )
    chunk_count = 0
    try:
        async for chunk in iterate_in_threadpool(chunks):
            if is_disconnected is not None and await is_disconnected():
                logger.info(
                    "stream_chat_client_disconnected trace_id=%s chunks=%s",
                    trace_id,
                    chunk_count,
                )
                return

            chunk_count += 1
            yield format_sse_event(
                "message",
                {"content": redact_sensitive_text(chunk)},
                event_id=f"{trace_id}:{chunk_count}",
            )
            if heartbeat_every_chunks > 0 and chunk_count % heartbeat_every_chunks == 0:
                yield format_sse_comment("heartbeat")
    except AppException as exc:
        logger.warning(
            "stream_chat_app_exception code=%s",
            exc.code,
        )
        yield format_sse_event(
            "error",
            {
                "code": exc.code,
                "message": exc.message,
                "trace_id": trace_id,
            },
            event_id=f"{trace_id}:error",
        )
        return
    except Exception:
        logger.exception("stream_chat_unhandled_exception")
        yield format_sse_event(
            "error",
            {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误",
                "trace_id": trace_id,
            },
            event_id=f"{trace_id}:error",
        )
        return

    yield format_sse_event(
        "done",
        {"trace_id": trace_id, "chunks": chunk_count},
        event_id=f"{trace_id}:done",
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service),
) -> ChatResponse:
    validate_chat_request_security(request)
    logger.info(
        "chat_requested message_length=%s history_size=%s",
        len(request.message),
        len(request.history),
    )
    reply = llm_chat_service.generate_reply(
        request.message,
        history=request.history,
    )
    return ChatResponse(reply=redact_sensitive_text(reply))


@router.post("/langchain-chat", response_model=ChatResponse)
def langchain_chat(
    request: ChatRequest,
    langchain_chat_model_service: LangChainChatModelService = Depends(
        get_langchain_chat_model_service
    ),
) -> ChatResponse:
    validate_chat_request_security(request)
    logger.info(
        "langchain_chat_requested message_length=%s history_size=%s",
        len(request.message),
        len(request.history),
    )
    reply = langchain_chat_model_service.generate_reply(
        request.message,
        history=request.history,
    )
    return ChatResponse(reply=redact_sensitive_text(reply))


@router.post("/stream-chat")
def stream_chat(
    request: Request,
    chat_request: ChatRequest,
    settings: Settings = Depends(get_settings),
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service),
) -> StreamingResponse:
    validate_chat_request_security(chat_request)
    logger.info(
        "stream_chat_requested message_length=%s history_size=%s",
        len(chat_request.message),
        len(chat_request.history),
    )
    chunks = llm_chat_service.stream_reply(
        chat_request.message,
        history=chat_request.history,
    )
    trace_id = get_trace_id()
    return StreamingResponse(
        build_stream_events(
            chunks,
            trace_id=trace_id,
            is_disconnected=request.is_disconnected,
            heartbeat_every_chunks=settings.sse_heartbeat_every_chunks,
        ),
        media_type=SSE_MEDIA_TYPE,
        headers=build_sse_headers(trace_id=trace_id),
    )


@router.post("/extract-ticket", response_model=StructuredOutputResponse)
def extract_ticket(
    request: StructuredOutputRequest,
    structured_output_service: StructuredOutputService = Depends(
        get_structured_output_service
    ),
) -> StructuredOutputResponse:
    require_prompt_injection_safe(request.message, source="user")
    logger.info(
        "extract_ticket_requested message_length=%s",
        len(request.message),
    )
    extraction = structured_output_service.extract_ticket(request.message)
    return StructuredOutputResponse(extraction=extraction)


@router.post("/langchain-extract-ticket", response_model=StructuredOutputResponse)
def langchain_extract_ticket(
    request: StructuredOutputRequest,
    langchain_structured_output_service: LangChainStructuredOutputService = Depends(
        get_langchain_structured_output_service
    ),
) -> StructuredOutputResponse:
    require_prompt_injection_safe(request.message, source="user")
    logger.info(
        "langchain_extract_ticket_requested message_length=%s",
        len(request.message),
    )
    extraction = langchain_structured_output_service.extract_ticket(request.message)
    return StructuredOutputResponse(extraction=extraction)


@router.post("/tool-decision", response_model=ToolDecisionResponse)
def tool_decision(
    request: ChatRequest,
    tool_decision_service: ToolDecisionService = Depends(get_tool_decision_service),
) -> ToolDecisionResponse:
    validate_chat_request_security(request)
    logger.info(
        "tool_decision_requested message_length=%s history_size=%s",
        len(request.message),
        len(request.history),
    )
    return tool_decision_service.decide(
        request.message,
        history=request.history,
    )


@router.post("/tool-chat", response_model=ChatResponse)
def tool_chat(
    request: ChatRequest,
    tool_calling_chat_service: ToolCallingChatService = Depends(
        get_tool_calling_chat_service
    ),
) -> ChatResponse:
    validate_chat_request_security(request)
    logger.info(
        "tool_chat_requested message_length=%s history_size=%s",
        len(request.message),
        len(request.history),
    )
    reply = tool_calling_chat_service.generate_reply(
        request.message,
        history=request.history,
    )
    return ChatResponse(reply=redact_sensitive_text(reply))
