from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.trace import TRACE_ID_HEADER
from app.routers.knowledge_base import get_knowledge_base_dir, get_vector_store
from app.services.java_knowledge_document_client import KnowledgeDocumentClient
from tests.rag_fakes import FakeVectorStoreWriter


class FakeKnowledgeDocumentClient:
    def __init__(self) -> None:
        self.upsert_calls: list[dict] = []
        self.delete_calls: list[str] = []

    def upsert_document(self, payload: dict) -> dict:
        self.upsert_calls.append(payload)
        return {**payload, "updated_at": None}

    def delete_document(self, document_id: str) -> bool:
        self.delete_calls.append(document_id)
        return True


def _override_dependencies(
    app: FastAPI,
    tmp_path: Path,
    client: TestClient,
    monkeypatch=None,
) -> tuple[FakeKnowledgeDocumentClient, FakeVectorStoreWriter, FakeKnowledgeDocumentClient]:
    app.dependency_overrides[get_knowledge_base_dir] = lambda: tmp_path
    vector_store = FakeVectorStoreWriter()
    app.dependency_overrides[get_vector_store] = lambda: vector_store

    fake_java = FakeKnowledgeDocumentClient()
    from app.routers import knowledge_base as kb_router

    kb_router.build_java_document_client = lambda settings: fake_java
    if monkeypatch is not None:
        monkeypatch.setattr(kb_router, "build_collection_vector_store", lambda settings, collection_name=None: vector_store)
    return fake_java, vector_store, fake_java


def test_create_document_writes_file_and_syncs(
    app: FastAPI,
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_java, vector_store, _ = _override_dependencies(app, tmp_path, client, monkeypatch)

    response = client.post(
        "/api/knowledge-base/documents",
        headers={TRACE_ID_HEADER: "trace-kb-create"},
        json={
            "document_id": "doc-001",
            "title": "Test Policy",
            "content": "# Test Policy\n\n退款政策七天无理由。",
            "business_domain": "refund",
            "permission_group": "public",
            "doc_type": "policy",
            "collection_name": "kb_customer_policy",
            "embedding_mode": "fake",
            "chunk_size": 220,
            "chunk_overlap": 40,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "doc-001"
    assert (tmp_path / "doc-001.md").exists()
    assert fake_java.upsert_calls
    assert fake_java.upsert_calls[0]["document_id"] == "doc-001"
    assert vector_store.embedded_chunks  # Qdrant 同步发生


def test_update_document_resyncs_and_deletes_old_chunks(
    app: FastAPI,
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_java, vector_store, _ = _override_dependencies(app, tmp_path, client, monkeypatch)

    create = client.post(
        "/api/knowledge-base/documents",
        headers={TRACE_ID_HEADER: "trace-kb-create"},
        json={
            "document_id": "doc-002",
            "title": "Old Title",
            "content": "# Old\n\n旧内容。",
            "business_domain": "refund",
            "permission_group": "public",
            "doc_type": "policy",
            "collection_name": "kb_customer_policy",
            "embedding_mode": "fake",
        },
    )
    assert create.status_code == 200
    old_delete_calls = len(vector_store.delete_calls)

    update = client.put(
        "/api/knowledge-base/documents/doc-002",
        headers={TRACE_ID_HEADER: "trace-kb-update"},
        json={
            "title": "New Title",
            "content": "# New\n\n新内容。",
            "embedding_mode": "fake",
        },
    )
    assert update.status_code == 200
    assert len(vector_store.delete_calls) > old_delete_calls  # 旧 chunk 被删
    assert vector_store.embedded_chunks  # 新 chunk upsert
    assert fake_java.upsert_calls[-1]["chunk_count"] >= 0


def test_delete_document_removes_file_and_metadata(
    app: FastAPI,
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_java, vector_store, _ = _override_dependencies(app, tmp_path, client, monkeypatch)

    create = client.post(
        "/api/knowledge-base/documents",
        headers={TRACE_ID_HEADER: "trace-kb-create"},
        json={
            "document_id": "doc-003",
            "title": "To Delete",
            "content": "# To Delete\n\n内容。",
            "business_domain": "refund",
            "permission_group": "public",
            "doc_type": "policy",
            "collection_name": "kb_customer_policy",
            "embedding_mode": "fake",
        },
    )
    assert create.status_code == 200

    delete = client.delete(
        "/api/knowledge-base/documents/doc-003",
        headers={TRACE_ID_HEADER: "trace-kb-delete"},
    )
    assert delete.status_code == 200
    assert not (tmp_path / "doc-003.md").exists()
    assert fake_java.delete_calls == ["doc-003"]
    assert vector_store.delete_calls  # Qdrant chunk 删除


def test_list_documents_merges_local_and_java_metadata(
    app: FastAPI,
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_java, _, _ = _override_dependencies(app, tmp_path, client, monkeypatch)
    (tmp_path / "existing.md").write_text(
        "# Existing Doc\n\n内容。\n文档类型: policy\n业务领域: refund\n权限组: public\n",
        encoding="utf-8",
    )

    response = client.get(
        "/api/knowledge-base/documents",
        headers={TRACE_ID_HEADER: "trace-kb-list"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_count"] >= 1
    assert any(d["source_file_name"] == "existing.md" for d in data["documents"])
    assert data["trace_id"] == "trace-kb-list"


def test_ingest_document_syncs_single_document(
    app: FastAPI,
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_java, vector_store, _ = _override_dependencies(app, tmp_path, client, monkeypatch)
    (tmp_path / "doc-004.md").write_text(
        "# Doc Four\n\n内容。\n文档类型: policy\n业务领域: refund\n权限组: public\n",
        encoding="utf-8",
    )

    response = client.post(
        "/api/knowledge-base/documents/doc-004/ingest",
        headers={TRACE_ID_HEADER: "trace-kb-ingest-doc"},
        json={"embedding_mode": "fake"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "doc-004"
    assert data["chunk_count"] >= 1
    assert fake_java.upsert_calls
    assert fake_java.upsert_calls[-1]["document_id"] == "doc-004"


def test_document_id_rejects_unsafe_characters(
    app: FastAPI,
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    _, _, _ = _override_dependencies(app, tmp_path, client, monkeypatch)
    # 分号不在白名单 → 422
    response = client.delete(
        "/api/knowledge-base/documents/evil;rm",
        headers={TRACE_ID_HEADER: "trace-kb-traversal"},
    )
    assert response.status_code == 422
    # 路径穿越字符（FastAPI 路由层 404 拦截，不进端点）
    traversal = client.delete(
        "/api/knowledge-base/documents/..%2F..%2Fevil",
        headers={TRACE_ID_HEADER: "trace-kb-traversal"},
    )
    assert traversal.status_code in (404, 422)
    assert traversal.status_code != 200
