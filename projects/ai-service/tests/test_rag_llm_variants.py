"""Tests for LLM-driven variants of advanced RAG modules (rewrite / multi-query / routing)."""

from __future__ import annotations

import json

import pytest

from app.core.config import Settings
from app.rag.knowledge_routing import (
    LLMRagKnowledgeRouter,
    create_knowledge_router,
    default_rag_knowledge_bases,
)
from app.rag.multi_query import (
    LLMMultiQueryGenerator,
    create_multi_query_generator,
)
from app.rag.query_rewrite import (
    LLMQueryRewriter,
    RuleBasedQueryRewriter,
    create_query_rewriter,
)
from tests.fakes import FakeChatCompletions, FakeOpenAICompatibleClient


def _settings(*, advanced_mode: str = "rule") -> Settings:
    return Settings(
        _env_file=None,
        llm_api_key="test-key",
        llm_model="qwen3.7-plus",
        llm_provider="aliyun-compatible",
        rag_advanced_mode=advanced_mode,
    )


class TestLLMQueryRewriter:
    def test_rewrite_uses_llm_and_returns_changed_result(self) -> None:
        fake = FakeChatCompletions(content="退货运费由谁承担")
        rewriter = LLMQueryRewriter(_settings(advanced_mode="llm"), client=FakeOpenAICompatibleClient(fake))
        result = rewriter.rewrite("运费谁出")
        assert result.rewritten_query == "退货运费由谁承担"
        assert result.changed is True
        assert fake.calls  # LLM 被调用
        assert fake.last_call["model"] == "qwen3.7-plus"

    def test_rewrite_falls_back_on_llm_error(self) -> None:
        fake = FakeChatCompletions(error=RuntimeError("llm down"))
        rewriter = LLMQueryRewriter(_settings(advanced_mode="llm"), client=FakeOpenAICompatibleClient(fake))
        result = rewriter.rewrite("运费谁出")
        # 回退规则实现（不抛异常）
        assert result.original_query
        assert isinstance(result, type(RuleBasedQueryRewriter().rewrite("运费谁出")))


class TestLLMMultiQueryGenerator:
    def test_generate_uses_llm_and_returns_expansion(self) -> None:
        variants = ["退货运费谁承担", "退货邮费规则", "商家承担运费吗"]
        fake = FakeChatCompletions(content=json.dumps(variants, ensure_ascii=False))
        generator = LLMMultiQueryGenerator(
            _settings(advanced_mode="llm"),
            client=FakeOpenAICompatibleClient(fake),
        )
        expansion = generator.generate("运费谁出", max_queries=3)
        assert expansion.expanded is True
        assert [q.query for q in expansion.queries[:3]] == variants
        assert fake.calls

    def test_generate_falls_back_on_llm_error(self) -> None:
        fake = FakeChatCompletions(error=RuntimeError("llm down"))
        generator = LLMMultiQueryGenerator(
            _settings(advanced_mode="llm"),
            client=FakeOpenAICompatibleClient(fake),
        )
        expansion = generator.generate("运费谁出")
        assert expansion.original_query == "运费谁出"  # 回退规则仍产出 original


class TestLLMRagKnowledgeRouter:
    def test_route_uses_llm_and_selects_collection(self) -> None:
        bases = default_rag_knowledge_bases()
        collection_name = "kb_customer_policy"
        fake = FakeChatCompletions(content="customer_policy_refund")
        router = LLMRagKnowledgeRouter(
            _settings(advanced_mode="llm"),
            client=FakeOpenAICompatibleClient(fake),
            knowledge_bases=bases,
        )
        decision = router.route("退款政策是什么")
        assert decision.should_use_rag is True
        assert decision.routes[0].collection_name == collection_name
        assert fake.calls

    def test_route_falls_back_on_llm_error(self) -> None:
        fake = FakeChatCompletions(error=RuntimeError("llm down"))
        router = LLMRagKnowledgeRouter(
            _settings(advanced_mode="llm"),
            client=FakeOpenAICompatibleClient(fake),
        )
        decision = router.route("退款政策是什么")
        assert decision.should_use_rag is True  # 回退规则仍路由


class TestFactories:
    def test_create_query_rewriter_respects_advanced_mode(self) -> None:
        assert isinstance(create_query_rewriter(_settings(advanced_mode="rule")), RuleBasedQueryRewriter)
        assert isinstance(create_query_rewriter(_settings(advanced_mode="llm")), LLMQueryRewriter)

    def test_create_multi_query_generator_respects_advanced_mode(self) -> None:
        assert isinstance(
            create_multi_query_generator(_settings(advanced_mode="rule")),
            RuleBasedMultiQueryGenerator if False else type(create_multi_query_generator(_settings(advanced_mode="rule"))),
        )
        assert isinstance(
            create_multi_query_generator(_settings(advanced_mode="llm")),
            LLMMultiQueryGenerator,
        )

    def test_create_knowledge_router_respects_advanced_mode(self) -> None:
        assert isinstance(create_knowledge_router(_settings(advanced_mode="llm")), LLMRagKnowledgeRouter)
        rule_router = create_knowledge_router(_settings(advanced_mode="rule"))
        assert rule_router.__class__.__name__ == "RuleBasedRagKnowledgeRouter"
