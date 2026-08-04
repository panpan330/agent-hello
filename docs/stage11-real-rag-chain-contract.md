# 阶段 11 真实 RAG 链路接口契约

## 1. 接口

```text
POST /api/ai/rag/ask
```

请求示例：

```json
{
  "query": "退款多久到账？",
  "candidate_count": 20,
  "top_n": 5,
  "allow_rerank_fallback": false
}
```

默认链路：

```text
query
-> text-embedding-v4
-> Qdrant learning_rag_chunks_v4_1024
-> qwen3-rerank
-> qwen3.7-plus
-> answer + citations + trace_id
```

## 2. 当前真实配置

```text
QDRANT_COLLECTION_NAME=learning_rag_chunks_v4_1024
QDRANT_VECTOR_SIZE=1024
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIMENSION=1024
EMBEDDING_BATCH_SIZE=10
RERANK_MODEL=qwen3-rerank
RERANK_CANDIDATE_COUNT=20
RERANK_TOP_N=5
LLM_MODEL=qwen3.7-plus
```

`text-embedding-v4` 单批文本数量不能超过 10，所以项目固定 `EMBEDDING_BATCH_SIZE=10`。

## 3. 验收结果

本节已完成真实调用验收：

```text
真实 embedding 入库：4 个文档，16 个 chunk，16 条 1024 维向量
真实 RAG 问答：HTTP 200
retrieved_count=16
reranked_count=5
used_rerank_fallback=false
models=text-embedding-v4, qwen3-rerank, qwen3.7-plus
```

前端 AI 客服页已增加回答模式：

```text
Agent           -> POST /api/ai/chat
知识库 RAG       -> POST /api/ai/rag/ask
```

RAG 模式会展示后端返回的引用来源。
