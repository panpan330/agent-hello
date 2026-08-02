import logging
from types import SimpleNamespace

import httpx
import pytest
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)

from app.core.config import Settings
from app.core.exceptions import AppException
from app.schemas.chat import ChatMessage, ChatMessageRole
from app.services.llm_service import (
    LLMChatService,
    LLMTokenUsage,
    build_chat_messages,
    extract_stream_delta_content,
    extract_token_usage,
    map_openai_error_to_app_exception,
)
from tests.fakes import (
    FakeChatCompletions as FakeCompletions,
    FakeOpenAICompatibleClient as FakeClient,
    make_status_error,
    make_stream_chunk,
)


def test_build_chat_messages_wraps_user_message_in_clear_prompt() -> None:
    messages = build_chat_messages("解释 API 是什么")

    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert "## 任务\n解释 API 是什么" in messages[1].content
    assert "## 要求" in messages[1].content
    assert "## 输出格式" in messages[1].content
    assert "## 无法完成时" in messages[1].content


def test_build_chat_messages_keeps_history_before_current_user_message() -> None:
    history = [
        ChatMessage(role=ChatMessageRole.USER, content="什么是 API？"),
        ChatMessage(role=ChatMessageRole.ASSISTANT, content="API 是程序之间的接口。"),
    ]

    messages = build_chat_messages("那 FastAPI 呢？", history=history)

    assert messages[0].role == ChatMessageRole.SYSTEM
    assert messages[1:] == [
        ChatMessage(role=ChatMessageRole.USER, content="什么是 API？"),
        ChatMessage(role=ChatMessageRole.ASSISTANT, content="API 是程序之间的接口。"),
        ChatMessage(
            role=ChatMessageRole.USER,
            content=messages[3].content,
        ),
    ]
    assert "## 任务\n那 FastAPI 呢？" in messages[3].content


def test_llm_chat_service_calls_openai_compatible_client() -> None:
    completions = FakeCompletions(content="  模型回复  ")
    service = LLMChatService(
        Settings(llm_api_key="test-key", llm_model="qwen-test", _env_file=None),
        client=FakeClient(completions),
    )

    reply = service.generate_reply("解释 FastAPI")

    assert reply == "模型回复"
    assert len(completions.calls) == 1
    call = completions.calls[0]
    assert call["model"] == "qwen-test"
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["role"] == "user"
    assert "## 任务\n解释 FastAPI" in call["messages"][1]["content"]


def test_llm_chat_service_uses_fast_route_model_for_simple_chat(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.services.llm_service")
    completions = FakeCompletions(content="摘要结果")
    service = LLMChatService(
        Settings(
            llm_api_key="test-key",
            llm_model="qwen-balanced",
            llm_fast_model="qwen-fast",
            llm_route_fast_keywords="摘要",
            _env_file=None,
        ),
        client=FakeClient(completions),
    )

    reply = service.generate_reply("帮我摘要这段文字")

    assert reply == "摘要结果"
    assert completions.calls[0]["model"] == "qwen-fast"
    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "model=qwen-fast" in message
        and "route_tier=fast" in message
        and "route_reason=fast_keyword" in message
        for message in messages
    )


def test_llm_chat_service_sends_history_to_model() -> None:
    completions = FakeCompletions(content="  FastAPI 是 Python Web 框架。  ")
    service = LLMChatService(
        Settings(llm_api_key="test-key", llm_model="qwen-test", _env_file=None),
        client=FakeClient(completions),
    )
    history = [
        ChatMessage(role=ChatMessageRole.USER, content="什么是 API？"),
        ChatMessage(role=ChatMessageRole.ASSISTANT, content="API 是程序之间的接口。"),
    ]

    reply = service.generate_reply("那 FastAPI 呢？", history=history)

    assert reply == "FastAPI 是 Python Web 框架。"
    call = completions.calls[0]
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1] == {"role": "user", "content": "什么是 API？"}
    assert call["messages"][2] == {
        "role": "assistant",
        "content": "API 是程序之间的接口。",
    }
    assert call["messages"][3]["role"] == "user"
    assert "## 任务\n那 FastAPI 呢？" in call["messages"][3]["content"]


def test_extract_token_usage_from_object_usage() -> None:
    completion = SimpleNamespace(
        usage=SimpleNamespace(
            prompt_tokens=12,
            completion_tokens=8,
            total_tokens=20,
        )
    )

    assert extract_token_usage(completion) == LLMTokenUsage(
        prompt_tokens=12,
        completion_tokens=8,
        total_tokens=20,
    )


def test_extract_token_usage_from_dict_usage() -> None:
    completion = SimpleNamespace(
        usage={
            "prompt_tokens": 15,
            "completion_tokens": 6,
            "total_tokens": 21,
        }
    )

    assert extract_token_usage(completion) == LLMTokenUsage(
        prompt_tokens=15,
        completion_tokens=6,
        total_tokens=21,
    )


def test_extract_token_usage_ignores_missing_or_invalid_values() -> None:
    completion = SimpleNamespace(
        usage={
            "prompt_tokens": "12",
            "completion_tokens": True,
        }
    )

    assert extract_token_usage(completion) == LLMTokenUsage()
    assert extract_token_usage(SimpleNamespace()) == LLMTokenUsage()


def test_extract_stream_delta_content_from_object_chunk() -> None:
    chunk = make_stream_chunk("FastAPI")

    assert extract_stream_delta_content(chunk) == "FastAPI"


def test_extract_stream_delta_content_from_dict_chunk() -> None:
    chunk = {
        "choices": [
            {
                "delta": {
                    "content": " 是 Python Web 框架",
                }
            }
        ]
    }

    assert extract_stream_delta_content(chunk) == " 是 Python Web 框架"


def test_extract_stream_delta_content_ignores_empty_or_missing_content() -> None:
    assert extract_stream_delta_content(make_stream_chunk("")) is None
    assert extract_stream_delta_content(make_stream_chunk(None)) is None
    assert extract_stream_delta_content(SimpleNamespace()) is None


def test_llm_chat_service_logs_success_metadata(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.services.llm_service")
    completions = FakeCompletions(
        content="模型回复",
        usage=SimpleNamespace(
            prompt_tokens=12,
            completion_tokens=7,
            total_tokens=19,
        ),
    )
    service = LLMChatService(
        Settings(
            llm_api_key="test-key",
            llm_provider="test-provider",
            llm_model="qwen-test",
            _env_file=None,
        ),
        client=FakeClient(completions),
    )

    reply = service.generate_reply("解释 FastAPI")

    assert reply == "模型回复"
    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "llm_chat_succeeded provider=test-provider model=qwen-test" in message
        and "elapsed_ms=" in message
        and "prompt_tokens=12" in message
        and "completion_tokens=7" in message
        and "total_tokens=19" in message
        for message in messages
    )
    assert all("解释 FastAPI" not in message for message in messages)
    assert all("test-key" not in message for message in messages)


def test_llm_chat_service_logs_estimated_cost_metadata(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.services.llm_service")
    completions = FakeCompletions(
        content="模型回复",
        usage=SimpleNamespace(
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
        ),
    )
    service = LLMChatService(
        Settings(
            llm_api_key="test-key",
            llm_provider="test-provider",
            llm_model="qwen-test",
            llm_input_cost_per_million_tokens=2.0,
            llm_output_cost_per_million_tokens=6.0,
            llm_pricing_currency="USD",
            _env_file=None,
        ),
        client=FakeClient(completions),
    )

    service.generate_reply("解释 FastAPI")

    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "cost_status=estimated" in message
        and "estimated_cost=0.005" in message
        and "currency=USD" in message
        for message in messages
    )
    assert all("解释 FastAPI" not in message for message in messages)
    assert all("test-key" not in message for message in messages)


def test_llm_chat_service_logs_failure_metadata(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="app.services.llm_service")
    service = LLMChatService(
        Settings(
            llm_api_key="test-key",
            llm_provider="test-provider",
            llm_model="qwen-test",
            _env_file=None,
        ),
        client=FakeClient(FakeCompletions(error=RuntimeError("provider failed"))),
    )

    with pytest.raises(AppException):
        service.generate_reply("解释 FastAPI")

    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "llm_chat_failed code=LLM_CALL_FAILED" in message
        and "provider=test-provider" in message
        and "model=qwen-test" in message
        and "status_code=502" in message
        and "elapsed_ms=" in message
        for message in messages
    )
    assert all("解释 FastAPI" not in message for message in messages)
    assert all("test-key" not in message for message in messages)


def test_llm_chat_service_streams_delta_content_to_chunks() -> None:
    completions = FakeCompletions(
        stream_chunks=[
            make_stream_chunk("FastAPI"),
            make_stream_chunk(" 是"),
            make_stream_chunk(" Python Web 框架。"),
            make_stream_chunk(
                None,
                usage=SimpleNamespace(
                    prompt_tokens=12,
                    completion_tokens=8,
                    total_tokens=20,
                ),
            ),
        ],
    )
    service = LLMChatService(
        Settings(llm_api_key="test-key", llm_model="qwen-test", _env_file=None),
        client=FakeClient(completions),
    )

    chunks = list(service.stream_reply("解释 FastAPI"))

    assert chunks == ["FastAPI", " 是", " Python Web 框架。"]
    assert len(completions.calls) == 1
    call = completions.calls[0]
    assert call["model"] == "qwen-test"
    assert call["stream"] is True
    assert call["stream_options"] == {"include_usage": True}
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["role"] == "user"
    assert "## 任务\n解释 FastAPI" in call["messages"][1]["content"]


def test_llm_chat_service_uses_strong_route_model_for_long_stream_input() -> None:
    completions = FakeCompletions(stream_chunks=[make_stream_chunk("回答")])
    service = LLMChatService(
        Settings(
            llm_api_key="test-key",
            llm_model="qwen-balanced",
            llm_strong_model="qwen-strong",
            llm_route_long_input_chars=100,
            _env_file=None,
        ),
        client=FakeClient(completions),
    )

    chunks = list(service.stream_reply("请分析：" + "业务流程" * 40))

    assert chunks == ["回答"]
    assert completions.calls[0]["model"] == "qwen-strong"


def test_llm_chat_service_streams_history_to_model() -> None:
    completions = FakeCompletions(stream_chunks=[make_stream_chunk("回答")])
    service = LLMChatService(
        Settings(llm_api_key="test-key", llm_model="qwen-test", _env_file=None),
        client=FakeClient(completions),
    )
    history = [
        ChatMessage(role=ChatMessageRole.USER, content="什么是 API？"),
        ChatMessage(role=ChatMessageRole.ASSISTANT, content="API 是程序之间的接口。"),
    ]

    chunks = list(service.stream_reply("那 FastAPI 呢？", history=history))

    assert chunks == ["回答"]
    call = completions.calls[0]
    assert call["messages"][1] == {"role": "user", "content": "什么是 API？"}
    assert call["messages"][2] == {
        "role": "assistant",
        "content": "API 是程序之间的接口。",
    }
    assert "## 任务\n那 FastAPI 呢？" in call["messages"][3]["content"]


def test_llm_chat_service_logs_stream_success_metadata(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.services.llm_service")
    completions = FakeCompletions(
        stream_chunks=[
            make_stream_chunk("FastAPI"),
            make_stream_chunk(" 是"),
            make_stream_chunk(
                None,
                usage=SimpleNamespace(
                    prompt_tokens=10,
                    completion_tokens=5,
                    total_tokens=15,
                ),
            ),
        ],
    )
    service = LLMChatService(
        Settings(
            llm_api_key="test-key",
            llm_provider="test-provider",
            llm_model="qwen-test",
            _env_file=None,
        ),
        client=FakeClient(completions),
    )

    chunks = list(service.stream_reply("解释 FastAPI"))

    assert chunks == ["FastAPI", " 是"]
    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "llm_stream_chat_succeeded provider=test-provider model=qwen-test"
        in message
        and "chunks=3" in message
        and "content_chunks=2" in message
        and "prompt_tokens=10" in message
        and "completion_tokens=5" in message
        and "total_tokens=15" in message
        for message in messages
    )
    assert all("解释 FastAPI" not in message for message in messages)
    assert all("test-key" not in message for message in messages)


def test_llm_chat_service_requires_api_key_before_streaming() -> None:
    completions = FakeCompletions(stream_chunks=[make_stream_chunk("不会被调用")])
    service = LLMChatService(
        Settings(llm_api_key="", openai_api_key="", _env_file=None),
        client=FakeClient(completions),
    )

    with pytest.raises(AppException) as exc_info:
        service.stream_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_API_KEY_MISSING"
    assert exc_info.value.status_code == 500
    assert completions.calls == []


def test_llm_chat_service_maps_stream_create_errors() -> None:
    service = LLMChatService(
        Settings(llm_api_key="test-key", _env_file=None),
        client=FakeClient(FakeCompletions(error=RuntimeError("provider failed"))),
    )

    with pytest.raises(AppException) as exc_info:
        service.stream_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_CALL_FAILED"
    assert exc_info.value.status_code == 502


def test_llm_chat_service_maps_stream_iteration_errors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def broken_stream() -> object:
        yield make_stream_chunk("先返回一段")
        raise RuntimeError("stream broken")

    caplog.set_level(logging.WARNING, logger="app.services.llm_service")
    service = LLMChatService(
        Settings(
            llm_api_key="test-key",
            llm_provider="test-provider",
            llm_model="qwen-test",
            _env_file=None,
        ),
        client=FakeClient(FakeCompletions(stream_chunks=broken_stream())),
    )

    stream = service.stream_reply("解释 FastAPI")
    assert next(stream) == "先返回一段"
    with pytest.raises(AppException) as exc_info:
        next(stream)

    assert exc_info.value.code == "LLM_CALL_FAILED"
    assert exc_info.value.status_code == 502
    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "llm_stream_chat_failed code=LLM_CALL_FAILED" in message
        and "provider=test-provider" in message
        and "model=qwen-test" in message
        and "chunks=1" in message
        and "content_chunks=1" in message
        for message in messages
    )
    assert all("解释 FastAPI" not in message for message in messages)
    assert all("test-key" not in message for message in messages)


def test_llm_chat_service_requires_api_key() -> None:
    completions = FakeCompletions(content="不会被调用")
    service = LLMChatService(
        Settings(llm_api_key="", openai_api_key="", _env_file=None),
        client=FakeClient(completions),
    )

    with pytest.raises(AppException) as exc_info:
        service.generate_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_API_KEY_MISSING"
    assert exc_info.value.status_code == 500
    assert completions.calls == []


def test_llm_chat_service_rejects_empty_model_reply() -> None:
    service = LLMChatService(
        Settings(llm_api_key="test-key", _env_file=None),
        client=FakeClient(FakeCompletions(content="   ")),
    )

    with pytest.raises(AppException) as exc_info:
        service.generate_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_EMPTY_RESPONSE"
    assert exc_info.value.status_code == 502


def test_llm_chat_service_wraps_provider_errors() -> None:
    service = LLMChatService(
        Settings(llm_api_key="test-key", _env_file=None),
        client=FakeClient(FakeCompletions(error=RuntimeError("provider failed"))),
    )

    with pytest.raises(AppException) as exc_info:
        service.generate_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_CALL_FAILED"
    assert exc_info.value.status_code == 502


@pytest.mark.parametrize(
    ("error", "expected_code", "expected_status_code"),
    [
        (
            make_status_error(BadRequestError, 400),
            "LLM_BAD_REQUEST",
            502,
        ),
        (
            make_status_error(AuthenticationError, 401),
            "LLM_AUTHENTICATION_FAILED",
            502,
        ),
        (
            make_status_error(PermissionDeniedError, 403),
            "LLM_PERMISSION_DENIED",
            502,
        ),
        (
            make_status_error(NotFoundError, 404),
            "LLM_RESOURCE_NOT_FOUND",
            502,
        ),
        (
            make_status_error(UnprocessableEntityError, 422),
            "LLM_BAD_REQUEST",
            502,
        ),
        (
            make_status_error(InternalServerError, 500),
            "LLM_PROVIDER_ERROR",
            502,
        ),
        (
            APIConnectionError(
                request=httpx.Request(
                    "POST",
                    "https://example.com/chat/completions",
                )
            ),
            "LLM_CONNECTION_ERROR",
            502,
        ),
        (
            make_status_error(APIStatusError, 418),
            "LLM_PROVIDER_STATUS_ERROR",
            502,
        ),
        (
            RuntimeError("provider failed"),
            "LLM_CALL_FAILED",
            502,
        ),
    ],
)
def test_map_openai_error_to_app_exception(
    error: Exception,
    expected_code: str,
    expected_status_code: int,
) -> None:
    app_exception = map_openai_error_to_app_exception(error)

    assert app_exception.code == expected_code
    assert app_exception.status_code == expected_status_code


def test_llm_chat_service_maps_timeout_errors() -> None:
    timeout_error = APITimeoutError(
        request=httpx.Request("POST", "https://example.com/chat/completions")
    )
    service = LLMChatService(
        Settings(
            llm_api_key="test-key",
            request_timeout_seconds=3,
            _env_file=None,
        ),
        client=FakeClient(FakeCompletions(error=timeout_error)),
    )

    with pytest.raises(AppException) as exc_info:
        service.generate_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_TIMEOUT"
    assert exc_info.value.status_code == 504


def test_llm_chat_service_maps_rate_limit_errors() -> None:
    request = httpx.Request("POST", "https://example.com/chat/completions")
    response = httpx.Response(
        status_code=429,
        request=request,
        json={"error": {"message": "Too many requests"}},
    )
    rate_limit_error = RateLimitError(
        "Too many requests",
        response=response,
        body={"error": {"message": "Too many requests"}},
    )
    service = LLMChatService(
        Settings(
            llm_api_key="test-key",
            llm_max_retries=1,
            _env_file=None,
        ),
        client=FakeClient(FakeCompletions(error=rate_limit_error)),
    )

    with pytest.raises(AppException) as exc_info:
        service.generate_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_RATE_LIMITED"
    assert exc_info.value.status_code == 429


def test_llm_chat_service_maps_authentication_errors() -> None:
    service = LLMChatService(
        Settings(llm_api_key="test-key", _env_file=None),
        client=FakeClient(
            FakeCompletions(error=make_status_error(AuthenticationError, 401))
        ),
    )

    with pytest.raises(AppException) as exc_info:
        service.generate_reply("解释 FastAPI")

    assert exc_info.value.code == "LLM_AUTHENTICATION_FAILED"
    assert exc_info.value.status_code == 502
