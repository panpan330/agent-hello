from pathlib import Path

from fastapi import APIRouter, Depends

from app.core.config import PROJECT_ROOT, Settings, get_settings
from app.core.exceptions import AppException
from app.core.trace import get_trace_id
from app.rag.embeddings import (
    DeterministicHashEmbeddingModel,
    EmbeddingModel,
    OpenAICompatibleEmbeddingModel,
)
from app.rag.ingestion import (
    VectorStoreUpdater,
    ingest_directory_to_vector_store,
    refresh_directory_in_vector_store,
)
from app.rag.loaders import load_documents_from_directory
from app.rag.vector_store import QdrantVectorStore
from app.schemas.knowledge_base import (
    KnowledgeBaseDocumentStatus,
    KnowledgeBaseIngestRequest,
    KnowledgeBaseIngestResponse,
    KnowledgeBaseStatusResponse,
)


router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge-base"])
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "data" / "knowledge_base"


def get_knowledge_base_dir() -> Path:
    return KNOWLEDGE_BASE_DIR


def get_vector_store(settings: Settings = Depends(get_settings)) -> VectorStoreUpdater:
    return QdrantVectorStore.from_settings(settings)


def build_embedding_model(
    request: KnowledgeBaseIngestRequest,
    settings: Settings,
) -> EmbeddingModel:
    if request.embedding_mode == "fake":
        return DeterministicHashEmbeddingModel(dimension=settings.qdrant_vector_size)
    try:
        return OpenAICompatibleEmbeddingModel.from_settings(settings)
    except ValueError as exc:
        raise AppException(
            code="EMBEDDING_API_KEY_MISSING",
            message="Embedding API key 未配置，无法执行真实 embedding 入库。",
            status_code=500,
        ) from exc


@router.get("/status", response_model=KnowledgeBaseStatusResponse)
def knowledge_base_status(
    settings: Settings = Depends(get_settings),
    directory: Path = Depends(get_knowledge_base_dir),
) -> KnowledgeBaseStatusResponse:
    try:
        documents = load_documents_from_directory(directory)
    except NotADirectoryError as exc:
        raise AppException(
            code="KNOWLEDGE_BASE_DIR_NOT_FOUND",
            message="知识库目录不存在，无法读取本地知识文档。",
            status_code=500,
        ) from exc
    document_statuses = [
        KnowledgeBaseDocumentStatus(
            source=str(document.metadata["source"]),
            title=str(document.metadata["title"]),
            file_name=str(document.metadata["file_name"]),
            file_extension=str(document.metadata["file_extension"]),
            doc_type=_optional_str(document.metadata.get("doc_type")),
            business_domain=_optional_str(document.metadata.get("business_domain")),
            permission_group=_optional_str(document.metadata.get("permission_group")),
        )
        for document in documents
    ]
    return KnowledgeBaseStatusResponse(
        documents=document_statuses,
        document_count=len(document_statuses),
        collection_name=settings.qdrant_collection_name,
        qdrant_base_url=settings.resolved_qdrant_base_url,
        fake_embedding_dimension=settings.qdrant_vector_size,
        real_embedding_configured=settings.has_embedding_api_key,
        trace_id=get_trace_id(),
    )


@router.post("/ingest", response_model=KnowledgeBaseIngestResponse)
def ingest_knowledge_base(
    request: KnowledgeBaseIngestRequest,
    settings: Settings = Depends(get_settings),
    directory: Path = Depends(get_knowledge_base_dir),
    vector_store: VectorStoreUpdater = Depends(get_vector_store),
) -> KnowledgeBaseIngestResponse:
    embedding_model = build_embedding_model(request, settings)

    try:
        if request.refresh:
            result = refresh_directory_in_vector_store(
                directory,
                embedding_model=embedding_model,
                vector_store=vector_store,
                include_readme=request.include_readme,
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
                wait=request.wait,
            )
        else:
            result = ingest_directory_to_vector_store(
                directory,
                embedding_model=embedding_model,
                vector_store=vector_store,
                include_readme=request.include_readme,
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
                wait=request.wait,
            )
    except NotADirectoryError as exc:
        raise AppException(
            code="KNOWLEDGE_BASE_DIR_NOT_FOUND",
            message="知识库目录不存在，无法执行入库。",
            status_code=500,
        ) from exc
    except ValueError as exc:
        raise AppException(
            code="KNOWLEDGE_BASE_INGEST_INVALID_CONFIG",
            message=str(exc),
            status_code=400,
        ) from exc

    return KnowledgeBaseIngestResponse(
        embedding_mode=request.embedding_mode,
        document_count=result.document_count,
        chunk_count=result.chunk_count,
        vector_count=result.vector_count,
        vector_dimension=result.vector_dimension,
        collection_name=result.collection_name,
        replaced_source_count=result.replaced_source_count,
        trace_id=get_trace_id(),
    )


def _optional_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None
