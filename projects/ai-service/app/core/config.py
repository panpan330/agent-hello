from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

TicketAgentModelMode = Literal["rule_based", "fake_llm", "real_llm"]
LLMDefaultRouteTier = Literal["fast", "balanced", "strong"]


class Settings(BaseSettings):
    app_name: str = Field(default="AI Service")
    app_description: str = Field(
        default="Python AI service for Java + Python + AI learning project."
    )
    app_version: str = Field(default="0.1.0")
    model_name: str = Field(default="mock-chat-model")
    llm_provider: str = Field(default="openai-compatible")
    llm_model: str = Field(default="qwen3.7-plus")
    llm_fast_model: str | None = Field(default=None)
    llm_balanced_model: str | None = Field(default=None)
    llm_strong_model: str | None = Field(default=None)
    llm_default_route_tier: LLMDefaultRouteTier = Field(default="balanced")
    llm_route_long_input_chars: int = Field(default=1200, ge=100, le=20000)
    llm_route_fast_keywords: str = Field(default="翻译,改写,摘要,提取,分类")
    llm_route_strong_keywords: str = Field(
        default="代码审查,架构设计,复杂推理,生产事故,安全分析,SQL优化"
    )
    llm_enable_fallback: bool = Field(default=True)
    llm_fallback_model: str | None = Field(default=None)
    llm_fallback_tier: LLMDefaultRouteTier = Field(default="balanced")
    llm_fallback_error_codes: str = Field(
        default=(
            "LLM_TIMEOUT,LLM_RATE_LIMITED,LLM_PROVIDER_ERROR,"
            "LLM_CONNECTION_ERROR,LLM_PROVIDER_STATUS_ERROR,LLM_CALL_FAILED,"
            "LLM_EMPTY_RESPONSE,LLM_BAD_RESPONSE"
        )
    )
    llm_base_url: str | None = Field(default=None)
    llm_api_key: str | None = Field(default=None, repr=False)
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    llm_total_timeout_seconds: float = Field(default=45.0, gt=0)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    max_output_tokens: int = Field(default=1024, gt=0)
    llm_enable_cost_control: bool = Field(default=True)
    llm_max_input_tokens_per_request: int = Field(default=6000, ge=100)
    llm_max_total_tokens_per_request: int = Field(default=8000, ge=100)
    llm_min_output_tokens: int = Field(default=128, ge=16)
    llm_max_estimated_cost_per_request: float | None = Field(default=None, ge=0)
    llm_disable_fallback_above_total_tokens: int | None = Field(
        default=6000,
        ge=100,
    )
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    rate_limit_client_requests_per_window: int = Field(default=120, ge=0)
    rate_limit_route_requests_per_window: int = Field(default=120, ge=0)
    rate_limit_ai_requests_per_window: int = Field(default=60, ge=0)
    rate_limit_tool_requests_per_window: int = Field(default=30, ge=0)
    rate_limit_excluded_paths: str = Field(default="/health,/ready")
    sse_heartbeat_every_chunks: int = Field(default=2, ge=0, le=100)
    llm_input_cost_per_million_tokens: float | None = Field(default=None, ge=0)
    llm_output_cost_per_million_tokens: float | None = Field(default=None, ge=0)
    llm_pricing_currency: str = Field(default="USD", min_length=1)
    ticket_agent_model_mode: TicketAgentModelMode = Field(default="rule_based")
    java_mock_service_base_url: str = Field(default="http://127.0.0.1:8001")
    java_mock_service_timeout_seconds: float = Field(default=5.0, gt=0)
    qdrant_base_url: str = Field(default="http://127.0.0.1:6333")
    qdrant_collection_name: str = Field(default="learning_rag_chunks")
    qdrant_timeout_seconds: float = Field(default=5.0, gt=0)
    qdrant_vector_size: int = Field(default=8, gt=0)
    qdrant_api_key: str | None = Field(default=None, repr=False)
    milvus_uri: str = Field(default="http://127.0.0.1:19530")
    milvus_collection_name: str = Field(default="learning_rag_chunks_milvus")
    milvus_timeout_seconds: float = Field(default=5.0, gt=0)
    milvus_vector_size: int = Field(default=8, gt=0)
    milvus_token: str | None = Field(default=None, repr=False)
    embedding_provider: str = Field(default="openai-compatible")
    embedding_model: str = Field(default="text-embedding-3-small")
    embedding_base_url: str | None = Field(default=None)
    embedding_api_key: str | None = Field(default=None, repr=False)
    embedding_dimension: int = Field(default=1536, gt=0)
    embedding_batch_size: int = Field(default=64, ge=1, le=256)
    embedding_request_dimensions: bool = Field(default=False)
    rerank_provider: str = Field(default="http-compatible")
    rerank_model: str = Field(default="mock-rerank-model")
    rerank_base_url: str | None = Field(default=None)
    rerank_api_key: str | None = Field(default=None, repr=False)
    rerank_timeout_seconds: float = Field(default=10.0, gt=0)
    rerank_max_retries: int = Field(default=1, ge=0, le=3)
    tool_confirmation_ttl_seconds: int = Field(default=300, ge=30, le=3600)
    mcp_server_name: str = Field(
        default="ai-service-learning-mcp",
        min_length=1,
        max_length=100,
    )
    mcp_enable_learning_resources: bool = Field(default=True)
    mcp_enable_project_resources: bool = Field(default=True)
    mcp_project_resource_root: str | None = Field(default=None)
    log_level: str = Field(default="INFO")
    cors_allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173"
    )
    openai_api_key: str | None = Field(default=None, repr=False)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_allowed_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def has_openai_api_key(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())

    @property
    def resolved_llm_api_key(self) -> str | None:
        for api_key in (self.llm_api_key, self.openai_api_key):
            if api_key and api_key.strip():
                return api_key.strip()
        return None

    @property
    def has_llm_api_key(self) -> bool:
        return self.resolved_llm_api_key is not None

    @property
    def resolved_llm_base_url(self) -> str | None:
        if not self.llm_base_url or not self.llm_base_url.strip():
            return None
        return self.llm_base_url.strip()

    @property
    def resolved_llm_fast_model(self) -> str:
        return self._resolve_llm_tier_model(self.llm_fast_model)

    @property
    def resolved_llm_balanced_model(self) -> str:
        return self._resolve_llm_tier_model(self.llm_balanced_model)

    @property
    def resolved_llm_strong_model(self) -> str:
        return self._resolve_llm_tier_model(self.llm_strong_model)

    def _resolve_llm_tier_model(self, tier_model: str | None) -> str:
        for model in (tier_model, self.llm_model):
            if model and model.strip():
                return model.strip()
        return "qwen3.7-plus"

    @property
    def resolved_llm_fallback_model(self) -> str:
        if self.llm_fallback_model and self.llm_fallback_model.strip():
            return self.llm_fallback_model.strip()
        return self._resolve_llm_tier_model(
            {
                "fast": self.llm_fast_model,
                "balanced": self.llm_balanced_model,
                "strong": self.llm_strong_model,
            }[self.llm_fallback_tier]
        )

    @property
    def has_llm_token_pricing(self) -> bool:
        return (
            self.llm_input_cost_per_million_tokens is not None
            and self.llm_output_cost_per_million_tokens is not None
        )

    @property
    def resolved_llm_pricing_currency(self) -> str:
        return self.llm_pricing_currency.strip() or "USD"

    @property
    def resolved_java_mock_service_base_url(self) -> str:
        return self.java_mock_service_base_url.strip().rstrip("/")

    @property
    def resolved_qdrant_base_url(self) -> str:
        return self.qdrant_base_url.strip().rstrip("/")

    @property
    def resolved_milvus_uri(self) -> str:
        return self.milvus_uri.strip().rstrip("/")

    @property
    def resolved_embedding_api_key(self) -> str | None:
        for api_key in (self.embedding_api_key, self.llm_api_key, self.openai_api_key):
            if api_key and api_key.strip():
                return api_key.strip()
        return None

    @property
    def has_embedding_api_key(self) -> bool:
        return self.resolved_embedding_api_key is not None

    @property
    def resolved_rerank_api_key(self) -> str | None:
        for api_key in (self.rerank_api_key, self.llm_api_key, self.openai_api_key):
            if api_key and api_key.strip():
                return api_key.strip()
        return None

    @property
    def has_rerank_api_key(self) -> bool:
        return self.resolved_rerank_api_key is not None

    @property
    def resolved_rerank_base_url(self) -> str | None:
        if not self.rerank_base_url or not self.rerank_base_url.strip():
            return None
        return self.rerank_base_url.strip().rstrip("/")

    @property
    def resolved_embedding_base_url(self) -> str | None:
        for base_url in (self.embedding_base_url, self.llm_base_url):
            if base_url and base_url.strip():
                return base_url.strip().rstrip("/")
        return None

    @property
    def resolved_mcp_server_name(self) -> str:
        server_name = self.mcp_server_name.strip()
        return server_name or "ai-service-learning-mcp"

    @property
    def resolved_mcp_project_resource_root(self) -> Path | None:
        if not self.mcp_project_resource_root or not self.mcp_project_resource_root.strip():
            return None
        return Path(self.mcp_project_resource_root.strip()).expanduser().resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
