"""Tests for the enhanced RAG pipeline (feature switches)."""

from __future__ import annotations

from app.core.config import Settings
from app.rag import pipeline as pipeline_module


def _settings(**overrides) -> Settings:
    base = dict(
        llm_api_key="test-key",
        llm_model="qwen3.7-plus",
        llm_provider="aliyun-compatible",
    )
    base.update(overrides)
    return Settings(_env_file=None, **base)


def _fake_rag_answer() -> object:
    from app.rag.generator import RagAnswer

    return RagAnswer(
        answer="退款政策：七天无理由退货",
        status="answered",
        citations=[],
        no_context_reason=None,
        suggestions=[],
    )


def test_default_path_retrieves_and_generates(monkeypatch) -> None:
    """默认开关全关：走 retrieve_top_k + rerank + generate（与阶段 1 一致）。"""
    settings = _settings()
    calls: list[str] = []
    monkeypatch.setattr(pipeline_module, "_retrieve", lambda q, **kw: calls.append("retrieve") or [])
    monkeypatch.setattr(
        pipeline_module,
        "create_rag_answer_service",
        lambda s: type("Svc", (), {"generate_answer_with_citations": lambda self, q, chunks: (_fake_rag_answer())})(),
    )
    result = pipeline_module.enhanced_rag_answer("退款政策是什么", settings=settings)
    assert result is not None
    assert "retrieve" in calls


def test_rewrite_enabled_calls_rewriter(monkeypatch) -> None:
    """RAG_ENABLE_REWRITE=true：改写后再检索。"""
    settings = _settings(rag_enable_rewrite=True)
    rewritten = {"value": None}

    class FakeRewriter:
        def rewrite(self, query):
            rewritten["value"] = query
            from app.rag.query_rewrite import QueryRewriteResult

            return QueryRewriteResult(
                original_query=query,
                rewritten_query="退货运费由谁承担",
                changed=True,
            )

    import app.rag.pipeline as pipe

    monkeypatch.setattr(pipe, "create_query_rewriter", lambda s: FakeRewriter())
    monkeypatch.setattr(pipe, "_retrieve", lambda q, **kw: [])
    monkeypatch.setattr(
        pipe,
        "create_rag_answer_service",
        lambda s: type("Svc", (), {"generate_answer_with_citations": lambda self, q, chunks: (_fake_rag_answer())})(),
    )
    pipe.enhanced_rag_answer("运费谁出", settings=settings)
    assert rewritten["value"] == "运费谁出"  # rewriter 收到原问


def test_routing_enabled_selects_collection(monkeypatch) -> None:
    """RAG_ENABLE_ROUTING=true：按 route.collection_name 构造 store。"""
    settings = _settings(rag_enable_routing=True)
    captured = {}

    class FakeRouter:
        def route(self, query, **kw):
            from app.rag.knowledge_routing import RagKnowledgeRoute, RagKnowledgeRouteDecision

            return RagKnowledgeRouteDecision(
                normalized_query=query,
                intent="policy_lookup",
                should_use_rag=True,
                selected_route_count=1,
                routes=[
                    RagKnowledgeRoute(
                        knowledge_base_id="customer_policy_refund",
                        collection_name="kb_customer_policy",
                        display_name="refund",
                        route_score=1.0,
                    )
                ],
            )

    import app.rag.pipeline as pipe

    monkeypatch.setattr(pipe, "create_knowledge_router", lambda s: FakeRouter())
    monkeypatch.setattr(pipe, "_retrieve", lambda q, **kw: captured.update(kw) or [])
    monkeypatch.setattr(
        pipe,
        "create_rag_answer_service",
        lambda s: type("Svc", (), {"generate_answer_with_citations": lambda self, q, chunks: (_fake_rag_answer())})(),
    )
    pipe.enhanced_rag_answer("退款政策是什么", settings=settings)
    assert captured.get("collection_name") == "kb_customer_policy"


def test_hybrid_enabled_calls_hybrid(monkeypatch) -> None:
    """RAG_ENABLE_HYBRID=true：走 hybrid 检索。"""
    settings = _settings(rag_enable_hybrid=True)
    called = {"hybrid": False}
    monkeypatch.setattr(pipeline_module, "_hybrid_retrieve", lambda q, **kw: called.__setitem__("hybrid", True) or [])
    monkeypatch.setattr(
        pipeline_module,
        "create_rag_answer_service",
        lambda s: type("Svc", (), {"generate_answer_with_citations": lambda self, q, chunks: (_fake_rag_answer())})(),
    )
    pipeline_module.enhanced_rag_answer("退款政策是什么", settings=settings)
    assert called["hybrid"] is True
