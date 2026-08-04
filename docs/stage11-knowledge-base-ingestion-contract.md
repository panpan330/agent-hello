# 阶段 11 知识库管理与入库接口契约

## 1. 职责边界

Java 业务服务负责知识文档元信息和权限可见性：

```text
GET /api/knowledge-documents
```

Python AI 服务负责读取本地知识文件、切分 chunk、生成向量并写入 Qdrant：

```text
GET  /api/knowledge-base/status
POST /api/knowledge-base/ingest
```

前端知识库页面同时调用两边：Java 决定当前用户能看到哪些业务文档，Python 展示本地知识文件和 Qdrant 入库状态。

## 2. Python 状态接口

```text
GET /api/knowledge-base/status
```

返回重点字段：

```text
documents                  本地知识库文件列表
document_count             本地知识文件数量
collection_name            Qdrant collection
qdrant_base_url            Qdrant 地址
fake_embedding_dimension   Fake embedding 维度
real_embedding_configured  是否已配置真实 embedding key
trace_id                   请求追踪 ID
```

## 3. Python 入库接口

```text
POST /api/knowledge-base/ingest
```

请求示例：

```json
{
  "embedding_mode": "fake",
  "refresh": true,
  "wait": true,
  "include_readme": false,
  "chunk_size": 500,
  "chunk_overlap": 80
}
```

`embedding_mode=fake` 不调用真实模型，但会真实写入 Qdrant，适合本地联调。

`embedding_mode=real` 会调用真实 embedding 模型，需要先配置 embedding API Key，适合第 9 节以后做完整真实链路验收。

返回重点字段：

```text
document_count          读取的文档数
chunk_count             切分出的 chunk 数
vector_count            写入的向量数
vector_dimension        向量维度
collection_name         写入的 Qdrant collection
replaced_source_count   refresh=true 时被替换的 source 数
trace_id                请求追踪 ID
```

## 4. 本节验证结果

本节已完成：

```text
Qdrant 地址：http://192.168.88.10:6333
collection：learning_rag_chunks
文档数：4
chunk 数：16
向量数：16
向量维度：8
```

这次验证使用 Fake embedding，所以不会消耗模型 API 额度，但 Qdrant 写入是真实发生的。
