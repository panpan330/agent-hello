from typing import Literal

from pydantic import BaseModel, Field


KnowledgeBaseEmbeddingMode = Literal["fake", "real"]


class KnowledgeBaseDocumentStatus(BaseModel):
    source: str = Field(min_length=1)
    title: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    file_extension: str = Field(min_length=1)
    doc_type: str | None = None
    business_domain: str | None = None
    permission_group: str | None = None


class KnowledgeBaseStatusResponse(BaseModel):
    documents: list[KnowledgeBaseDocumentStatus]
    document_count: int = Field(ge=0)
    collection_name: str = Field(min_length=1)
    qdrant_base_url: str = Field(min_length=1)
    fake_embedding_dimension: int = Field(gt=0)
    real_embedding_configured: bool
    trace_id: str = Field(min_length=1)


class KnowledgeBaseIngestRequest(BaseModel):
    embedding_mode: KnowledgeBaseEmbeddingMode = Field(default="fake")
    refresh: bool = Field(default=True)
    wait: bool = Field(default=True)
    include_readme: bool = Field(default=False)
    chunk_size: int = Field(default=500, ge=100, le=4000)
    chunk_overlap: int = Field(default=80, ge=0, le=1000)


class KnowledgeBaseIngestResponse(BaseModel):
    embedding_mode: KnowledgeBaseEmbeddingMode
    document_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    vector_count: int = Field(ge=0)
    vector_dimension: int = Field(gt=0)
    collection_name: str = Field(min_length=1)
    replaced_source_count: int = Field(ge=0)
    trace_id: str = Field(min_length=1)
