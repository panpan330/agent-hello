from dataclasses import dataclass
from typing import Literal, Mapping, TypeAlias

from app.core.config import Settings


SafeConfigValue: TypeAlias = str | int | float | bool
SecretReadinessStatus = Literal["configured", "skipped", "not_configured"]

SECRET_SETTING_NAMES = frozenset(
    {
        "llm_api_key",
        "openai_api_key",
        "embedding_api_key",
        "rerank_api_key",
        "qdrant_api_key",
        "milvus_token",
    }
)


@dataclass(frozen=True)
class SecretConfigurationCheck:
    name: str
    configured: bool
    required: bool
    message: str

    @property
    def readiness_status(self) -> SecretReadinessStatus:
        if not self.required:
            return "skipped"
        return "configured" if self.configured else "not_configured"


def build_safe_settings_snapshot(settings: Settings) -> dict[str, SafeConfigValue]:
    return {
        "app.name": settings.app_name,
        "app.version": settings.app_version,
        "app.log_level": settings.log_level,
        "app.cors_origin_count": len(settings.cors_allowed_origin_list),
        "llm.provider": settings.llm_provider,
        "llm.model": settings.llm_model,
        "llm.fast_model_configured": _has_text(settings.llm_fast_model),
        "llm.balanced_model_configured": _has_text(settings.llm_balanced_model),
        "llm.strong_model_configured": _has_text(settings.llm_strong_model),
        "llm.default_route_tier": settings.llm_default_route_tier,
        "llm.route_long_input_chars": settings.llm_route_long_input_chars,
        "llm.route_fast_keyword_count": len(
            _split_route_keywords(settings.llm_route_fast_keywords)
        ),
        "llm.route_strong_keyword_count": len(
            _split_route_keywords(settings.llm_route_strong_keywords)
        ),
        "llm.base_url_configured": _has_text(settings.resolved_llm_base_url),
        "llm.api_key_configured": settings.has_llm_api_key,
        "llm.request_timeout_seconds": settings.request_timeout_seconds,
        "llm.max_retries": settings.llm_max_retries,
        "llm.max_output_tokens": settings.max_output_tokens,
        "llm.pricing_configured": settings.has_llm_token_pricing,
        "llm.pricing_currency": settings.resolved_llm_pricing_currency,
        "ticket_agent.model_mode": settings.ticket_agent_model_mode,
        "ticket_agent.confirmation_ttl_seconds": settings.tool_confirmation_ttl_seconds,
        "java_mock_service.base_url_configured": _has_text(
            settings.resolved_java_mock_service_base_url
        ),
        "java_mock_service.timeout_seconds": settings.java_mock_service_timeout_seconds,
        "qdrant.base_url_configured": _has_text(settings.resolved_qdrant_base_url),
        "qdrant.collection_name": settings.qdrant_collection_name,
        "qdrant.vector_size": settings.qdrant_vector_size,
        "qdrant.api_key_configured": _has_text(settings.qdrant_api_key),
        "milvus.uri_configured": _has_text(settings.resolved_milvus_uri),
        "milvus.collection_name": settings.milvus_collection_name,
        "milvus.vector_size": settings.milvus_vector_size,
        "milvus.token_configured": _has_text(settings.milvus_token),
        "embedding.provider": settings.embedding_provider,
        "embedding.model": settings.embedding_model,
        "embedding.base_url_configured": _has_text(settings.resolved_embedding_base_url),
        "embedding.api_key_configured": settings.has_embedding_api_key,
        "embedding.dimension": settings.embedding_dimension,
        "embedding.batch_size": settings.embedding_batch_size,
        "embedding.request_dimensions": settings.embedding_request_dimensions,
        "rerank.provider": settings.rerank_provider,
        "rerank.model": settings.rerank_model,
        "rerank.base_url_configured": _has_text(settings.resolved_rerank_base_url),
        "rerank.api_key_configured": settings.has_rerank_api_key,
        "rerank.timeout_seconds": settings.rerank_timeout_seconds,
        "rerank.max_retries": settings.rerank_max_retries,
        "mcp.server_name": settings.resolved_mcp_server_name,
        "mcp.learning_resources_enabled": settings.mcp_enable_learning_resources,
        "mcp.project_resources_enabled": settings.mcp_enable_project_resources,
        "mcp.project_resource_root_configured": (
            settings.resolved_mcp_project_resource_root is not None
        ),
    }


def build_secret_configuration_checks(
    settings: Settings,
) -> list[SecretConfigurationCheck]:
    return [
        SecretConfigurationCheck(
            name="llm_api_key",
            configured=settings.has_llm_api_key,
            required=settings.ticket_agent_model_mode == "real_llm",
            message=(
                "Real LLM mode requires an LLM API key."
                if settings.ticket_agent_model_mode == "real_llm"
                else "LLM API key is not required outside real_llm mode."
            ),
        ),
        SecretConfigurationCheck(
            name="embedding_api_key",
            configured=settings.has_embedding_api_key,
            required=False,
            message="Embedding API key is optional until real embedding calls are enabled.",
        ),
        SecretConfigurationCheck(
            name="rerank_api_key",
            configured=settings.has_rerank_api_key,
            required=False,
            message="Rerank API key is optional until real rerank calls are enabled.",
        ),
        SecretConfigurationCheck(
            name="qdrant_api_key",
            configured=_has_text(settings.qdrant_api_key),
            required=False,
            message="Qdrant API key is optional for local unauthenticated Qdrant.",
        ),
        SecretConfigurationCheck(
            name="milvus_token",
            configured=_has_text(settings.milvus_token),
            required=False,
            message="Milvus token is optional for local unauthenticated Milvus.",
        ),
    ]


def find_raw_secret_setting_names(config_fields: Mapping[str, object]) -> list[str]:
    forbidden: list[str] = []
    for field_name in config_fields:
        normalized = _normalize_config_field_name(field_name)
        if normalized in SECRET_SETTING_NAMES:
            forbidden.append(normalized)
    return sorted(set(forbidden))


def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalize_config_field_name(field_name: str) -> str:
    return field_name.strip().lower().replace("-", "_").replace(".", "_")


def _split_route_keywords(raw_keywords: str) -> list[str]:
    return [
        keyword.strip()
        for keyword in raw_keywords.replace("，", ",").split(",")
        if keyword.strip()
    ]
