# Java + Python + AI 学习项目

这个仓库用于长期沉淀 Java 后端转 AI 应用工程的学习记录、项目代码、实验结论和复盘。

当前主线不是纯算法岗，也不是只做提示词，而是：

```text
Java 后端 + Python AI 服务 + LangChain/LangGraph + RAG + Tool Calling + 工程化上线
```

## 学习主线

- Java 后端继续负责业务系统、权限、数据库、稳定 API 和工程化能力。
- Python + FastAPI 负责 AI 服务层。
- LangChain 负责 LLM 调用、RAG、工具调用和结构化输出。
- LangGraph 负责多步骤、可恢复、可审计的 Agent/Workflow 编排。
- 项目重点先收敛到企业知识库 RAG 和智能工单 Agent。

## 仓库结构

```text
docs/      学习路线、进度、上下文和项目规划
notes/     学习笔记、踩坑记录、复盘
projects/ 练习项目、Demo 和完整作品
```

## 核心文档

- [学习上下文](docs/learning-context.md)
- [AI 应用工程学习路线图](docs/ai-application-learning-roadmap.md)
- [学习进度](docs/learning-progress.md)
- [学习资料清单](docs/learning-resources.md)
- [旧版长期进度文档](docs/ai-application-learning-progress.md)

## Python 基础学习笔记索引

| 顺序 | 主题 | 笔记路径 |
| --- | --- | --- |
| 0 | Python 项目环境和 uv | [notes/python-project-environment.md](notes/python-project-environment.md) |
| 1 | 变量和基本类型 | [notes/python-variables-and-types.md](notes/python-variables-and-types.md) |
| 2 | 字符串 | [notes/python-strings.md](notes/python-strings.md) |
| 3 | 列表 | [notes/python-lists.md](notes/python-lists.md) |
| 4 | 字典 | [notes/python-dicts.md](notes/python-dicts.md) |
| 5 | 条件判断 | [notes/python-conditions.md](notes/python-conditions.md) |
| 6 | 循环 | [notes/python-loops.md](notes/python-loops.md) |
| 7 | 函数 | [notes/python-functions.md](notes/python-functions.md) |
| 8 | 模块导入 | [notes/python-imports.md](notes/python-imports.md) |
| 9 | 异常处理 | [notes/python-exceptions.md](notes/python-exceptions.md) |
| 10 | 文件读写和 JSON | [notes/python-files-json.md](notes/python-files-json.md) |
| 11 | 类型提示 | [notes/python-type-hints.md](notes/python-type-hints.md) |
| 12 | 类和对象 | [notes/python-classes.md](notes/python-classes.md) |
| 13 | 元组和集合 | [notes/python-tuples-sets.md](notes/python-tuples-sets.md) |
| 14 | 常用数据处理写法 | [notes/python-data-processing.md](notes/python-data-processing.md) |
| 15 | 函数进阶 | [notes/python-function-advanced.md](notes/python-function-advanced.md) |
| 16 | 标准库基础 | [notes/python-standard-library.md](notes/python-standard-library.md) |
| 17 | 正则表达式 re | [notes/python-regex.md](notes/python-regex.md) |
| 18 | pytest 测试基础 | [notes/python-pytest.md](notes/python-pytest.md) |
| 19 | 调试和报错阅读 | [notes/python-debugging-traceback.md](notes/python-debugging-traceback.md) |
| 20 | HTTP/API 基础 | [notes/python-http-api.md](notes/python-http-api.md) |
| 21 | async/await 异步基础 | [notes/python-async-await.md](notes/python-async-await.md) |
| 22 | Python 基础综合项目 | [notes/python-mini-project.md](notes/python-mini-project.md) |

对应练习代码主要在 [projects/python-basics](projects/python-basics)。

## 阶段 1：Python AI 服务学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | Web 服务、HTTP 和 API 是什么 | [notes/fastapi-stage1-01-web-http-api.md](notes/fastapi-stage1-01-web-http-api.md) | [projects/ai-service](projects/ai-service) |
| 2 | FastAPI 是什么 | [notes/fastapi-stage1-02-what-is-fastapi.md](notes/fastapi-stage1-02-what-is-fastapi.md) | [projects/ai-service](projects/ai-service) |
| 3 | 创建 `ai-service` 项目骨架 | [notes/fastapi-stage1-03-ai-service-project-skeleton.md](notes/fastapi-stage1-03-ai-service-project-skeleton.md) | [projects/ai-service](projects/ai-service) |
| 4 | FastAPI 最小服务 `/health` | [notes/fastapi-stage1-04-health-endpoint.md](notes/fastapi-stage1-04-health-endpoint.md) | [projects/ai-service](projects/ai-service) |
| 5 | router 路由拆分 | [notes/fastapi-stage1-05-router-splitting.md](notes/fastapi-stage1-05-router-splitting.md) | [projects/ai-service](projects/ai-service) |
| 6 | POST、请求体和 JSON | [notes/fastapi-stage1-06-post-body-json.md](notes/fastapi-stage1-06-post-body-json.md) | [projects/ai-service](projects/ai-service) |
| 7 | Pydantic 请求模型 | [notes/fastapi-stage1-07-pydantic-request-model.md](notes/fastapi-stage1-07-pydantic-request-model.md) | [projects/ai-service](projects/ai-service) |
| 8 | Pydantic 响应模型 | [notes/fastapi-stage1-08-pydantic-response-model.md](notes/fastapi-stage1-08-pydantic-response-model.md) | [projects/ai-service](projects/ai-service) |
| 9 | 模拟 `/chat` 接口 | [notes/fastapi-stage1-09-mock-chat-endpoint.md](notes/fastapi-stage1-09-mock-chat-endpoint.md) | [projects/ai-service](projects/ai-service) |
| 10 | 测试 FastAPI 接口 | [notes/fastapi-stage1-10-testing-fastapi-apis.md](notes/fastapi-stage1-10-testing-fastapi-apis.md) | [projects/ai-service](projects/ai-service) |
| 11 | `.env` 配置读取 | [notes/fastapi-stage1-11-env-config.md](notes/fastapi-stage1-11-env-config.md) | [projects/ai-service](projects/ai-service) |
| 12 | `logging` 日志 | [notes/fastapi-stage1-12-logging.md](notes/fastapi-stage1-12-logging.md) | [projects/ai-service](projects/ai-service) |
| 13 | `trace_id` 请求追踪 | [notes/fastapi-stage1-13-trace-id.md](notes/fastapi-stage1-13-trace-id.md) | [projects/ai-service](projects/ai-service) |
| 14 | 统一异常处理 | [notes/fastapi-stage1-14-exception-handling.md](notes/fastapi-stage1-14-exception-handling.md) | [projects/ai-service](projects/ai-service) |
| 15 | CORS 基础 | [notes/fastapi-stage1-15-cors.md](notes/fastapi-stage1-15-cors.md) | [projects/ai-service](projects/ai-service) |
| 16 | 阶段 1 项目整理 | [notes/fastapi-stage1-16-project-summary.md](notes/fastapi-stage1-16-project-summary.md) | [projects/ai-service](projects/ai-service) |

## 阶段 2：LLM API 基础调用学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | 什么是 LLM API | [notes/llm-api-stage2-01-what-is-llm-api.md](notes/llm-api-stage2-01-what-is-llm-api.md) | [projects/ai-service](projects/ai-service) |
| 2 | API key 和 `.env` 安全配置 | [notes/llm-api-stage2-02-api-key-env-security.md](notes/llm-api-stage2-02-api-key-env-security.md) | [projects/ai-service](projects/ai-service) |
| 3 | token、上下文窗口、费用基础 | [notes/llm-api-stage2-03-token-context-cost.md](notes/llm-api-stage2-03-token-context-cost.md) | [projects/ai-service](projects/ai-service) |
| 4 | OpenAI-compatible SDK 基础调用方式 | [notes/llm-api-stage2-04-openai-compatible-sdk.md](notes/llm-api-stage2-04-openai-compatible-sdk.md) | [projects/ai-service](projects/ai-service) |
| 5 | messages 是什么：system / user / assistant | [notes/llm-api-stage2-05-messages-roles.md](notes/llm-api-stage2-05-messages-roles.md) | [projects/ai-service](projects/ai-service) |
| 6 | prompt 基础：怎么写清楚任务 | [notes/llm-api-stage2-06-prompt-basics.md](notes/llm-api-stage2-06-prompt-basics.md) | [projects/ai-service](projects/ai-service) |
| 7 | 第一次真实 `/chat` 调用 | [notes/llm-api-stage2-07-real-chat-call.md](notes/llm-api-stage2-07-real-chat-call.md) | [projects/ai-service](projects/ai-service) |
| 8 | 多轮对话基础：历史消息怎么传 | [notes/llm-api-stage2-08-multi-turn-history.md](notes/llm-api-stage2-08-multi-turn-history.md) | [projects/ai-service](projects/ai-service) |
| 9 | timeout 超时 | [notes/llm-api-stage2-09-timeout.md](notes/llm-api-stage2-09-timeout.md) | [projects/ai-service](projects/ai-service) |
| 10 | retry 重试和 rate limit 限流基础 | [notes/llm-api-stage2-10-retry-rate-limit.md](notes/llm-api-stage2-10-retry-rate-limit.md) | [projects/ai-service](projects/ai-service) |
| 11 | 模型调用错误处理 | [notes/llm-api-stage2-11-model-error-handling.md](notes/llm-api-stage2-11-model-error-handling.md) | [projects/ai-service](projects/ai-service) |
| 12 | 模型调用日志：模型名、耗时、trace_id、token | [notes/llm-api-stage2-12-llm-call-logging.md](notes/llm-api-stage2-12-llm-call-logging.md) | [projects/ai-service](projects/ai-service) |
| 13 | streaming 流式输出是什么 | [notes/llm-api-stage2-13-streaming-concept.md](notes/llm-api-stage2-13-streaming-concept.md) | [projects/ai-service](projects/ai-service) |
| 14 | FastAPI `StreamingResponse` 实现 `/stream-chat` | [notes/llm-api-stage2-14-stream-chat-endpoint.md](notes/llm-api-stage2-14-stream-chat-endpoint.md) | [projects/ai-service](projects/ai-service) |
| 15 | 结构化输出是什么 | [notes/llm-api-stage2-15-structured-output-concept.md](notes/llm-api-stage2-15-structured-output-concept.md) | [projects/ai-service](projects/ai-service) |
| 16 | Pydantic 约束结构化输出 | [notes/llm-api-stage2-16-pydantic-structured-output.md](notes/llm-api-stage2-16-pydantic-structured-output.md) | [projects/ai-service](projects/ai-service) |
| 17 | 测试模型调用：mock/fake LLM client | [notes/llm-api-stage2-17-testing-model-calls.md](notes/llm-api-stage2-17-testing-model-calls.md) | [projects/ai-service](projects/ai-service) |
| 18 | 阶段 2 项目整理 | [notes/llm-api-stage2-18-project-summary.md](notes/llm-api-stage2-18-project-summary.md) | [projects/ai-service](projects/ai-service) |

## 阶段 3：LangChain + Java 工具调用学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | Tool Calling 是什么 | [notes/tool-calling-stage3-01-what-is-tool-calling.md](notes/tool-calling-stage3-01-what-is-tool-calling.md) | [projects/ai-service](projects/ai-service) |
| 2 | 为什么 AI 不能直接操作业务系统 | [notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md](notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md) | [projects/ai-service](projects/ai-service) |
| 3 | 工具参数和 JSON Schema | [notes/tool-calling-stage3-03-tool-parameters-json-schema.md](notes/tool-calling-stage3-03-tool-parameters-json-schema.md) | [projects/ai-service](projects/ai-service) |
| 4 | 结构化输出 vs Tool Calling | [notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md](notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md) | [projects/ai-service](projects/ai-service) |
| 5 | 用 fake tool 模拟查订单 | [notes/tool-calling-stage3-05-fake-query-order-tool.md](notes/tool-calling-stage3-05-fake-query-order-tool.md) | [projects/ai-service](projects/ai-service) |
| 6 | 工具调用结果也要 Pydantic 校验 | [notes/tool-calling-stage3-06-tool-result-pydantic-validation.md](notes/tool-calling-stage3-06-tool-result-pydantic-validation.md) | [projects/ai-service](projects/ai-service) |
| 7 | 工具调用错误处理：超时、404、500 | [notes/tool-calling-stage3-07-tool-error-handling.md](notes/tool-calling-stage3-07-tool-error-handling.md) | [projects/ai-service](projects/ai-service) |
| 8 | 工具调用权限边界 | [notes/tool-calling-stage3-08-tool-permission-boundary.md](notes/tool-calling-stage3-08-tool-permission-boundary.md) | [projects/ai-service](projects/ai-service) |
| 9 | 工具调用幂等性 | [notes/tool-calling-stage3-09-tool-idempotency.md](notes/tool-calling-stage3-09-tool-idempotency.md) | [projects/ai-service](projects/ai-service) |
| 10 | 用 FastAPI 写一个最小 Java mock 业务服务 | [notes/tool-calling-stage3-10-java-mock-service.md](notes/tool-calling-stage3-10-java-mock-service.md) | [projects/java-mock-service](projects/java-mock-service) |
| 11 | Python AI 服务调用 Java mock API | [notes/tool-calling-stage3-11-python-calls-java-mock-api.md](notes/tool-calling-stage3-11-python-calls-java-mock-api.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |
| 12 | 让模型决定是否调用工具 | [notes/tool-calling-stage3-12-model-decides-tool-call.md](notes/tool-calling-stage3-12-model-decides-tool-call.md) | [projects/ai-service](projects/ai-service) |
| 13 | 工具调用结果再交给模型总结 | [notes/tool-calling-stage3-13-tool-result-model-summary.md](notes/tool-calling-stage3-13-tool-result-model-summary.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |
| 14 | 用户确认机制：敏感操作不能直接执行 | [notes/tool-calling-stage3-14-user-confirmation.md](notes/tool-calling-stage3-14-user-confirmation.md) | [projects/ai-service](projects/ai-service) |
| 15 | 创建工单流程：提取字段、确认、调用 Java API | [notes/tool-calling-stage3-15-ticket-creation-workflow.md](notes/tool-calling-stage3-15-ticket-creation-workflow.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |
| 16 | 工具调用日志和 trace_id 串联 | [notes/tool-calling-stage3-16-tool-logging-trace-id.md](notes/tool-calling-stage3-16-tool-logging-trace-id.md) | [projects/ai-service](projects/ai-service) |
| 17 | 工具调用测试：fake Java API / fake tool | [notes/tool-calling-stage3-17-tool-testing-fakes.md](notes/tool-calling-stage3-17-tool-testing-fakes.md) | [projects/ai-service](projects/ai-service) |
| 18 | LangChain 是什么，为什么现在才引入 | [notes/tool-calling-stage3-18-what-is-langchain.md](notes/tool-calling-stage3-18-what-is-langchain.md) | [projects/ai-service](projects/ai-service) |
| 19 | LangChain ChatModel 基础 | [notes/tool-calling-stage3-19-langchain-chatmodel-basics.md](notes/tool-calling-stage3-19-langchain-chatmodel-basics.md) | [projects/ai-service](projects/ai-service) |
| 20 | LangChain Tool 基础 | [notes/tool-calling-stage3-20-langchain-tool-basics.md](notes/tool-calling-stage3-20-langchain-tool-basics.md) | [projects/ai-service](projects/ai-service) |
| 21 | LangChain 结构化输出 | [notes/tool-calling-stage3-21-langchain-structured-output.md](notes/tool-calling-stage3-21-langchain-structured-output.md) | [projects/ai-service](projects/ai-service) |
| 22 | 阶段 3 项目整理 | [notes/tool-calling-stage3-22-project-summary.md](notes/tool-calling-stage3-22-project-summary.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |

## 阶段 4：企业知识库 RAG 学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | RAG 是什么，为什么大模型需要知识库 | [notes/rag-stage4-01-what-is-rag.md](notes/rag-stage4-01-what-is-rag.md) | 待新增 |
| 2 | RAG 完整流程：load -> split -> embed -> store -> retrieve -> generate | [notes/rag-stage4-02-rag-pipeline.md](notes/rag-stage4-02-rag-pipeline.md) | 待新增 |
| 3 | 文档、知识库、chunk、metadata 是什么 | [notes/rag-stage4-03-documents-chunks-metadata.md](notes/rag-stage4-03-documents-chunks-metadata.md) | 待新增 |
| 4 | embedding 是什么：文本怎么变成向量 | [notes/rag-stage4-04-what-is-embedding.md](notes/rag-stage4-04-what-is-embedding.md) | 待新增 |
| 5 | 向量相似度：为什么能用向量找相似内容 | [notes/rag-stage4-05-vector-similarity.md](notes/rag-stage4-05-vector-similarity.md) | 待新增 |
| 6 | 向量数据库是什么，为什么先选 Qdrant | [notes/rag-stage4-06-vector-database-qdrant.md](notes/rag-stage4-06-vector-database-qdrant.md) | 待新增 |
| 7 | Qdrant 基础：collection、point、vector、payload | [notes/rag-stage4-07-qdrant-core-concepts.md](notes/rag-stage4-07-qdrant-core-concepts.md) | 待新增 |
| 8 | 本地启动 Qdrant | [notes/rag-stage4-08-start-qdrant-locally.md](notes/rag-stage4-08-start-qdrant-locally.md) | VMware Ubuntu Docker 已验证 |
| 9 | RAG 项目结构设计 | [notes/rag-stage4-09-rag-project-structure.md](notes/rag-stage4-09-rag-project-structure.md) | [projects/ai-service/app/rag](projects/ai-service/app/rag) |
| 10 | 准备第一批 Markdown/txt 知识文档 | [notes/rag-stage4-10-first-knowledge-documents.md](notes/rag-stage4-10-first-knowledge-documents.md) | [projects/ai-service/data/knowledge_base](projects/ai-service/data/knowledge_base) |
| 11 | 文档加载和文本清洗 | [notes/rag-stage4-11-document-loading-cleaning.md](notes/rag-stage4-11-document-loading-cleaning.md) | [projects/ai-service/app/rag/loaders.py](projects/ai-service/app/rag/loaders.py) |
| 12 | chunk 切分策略：大小、重叠、标题、段落 | [notes/rag-stage4-12-chunk-splitting.md](notes/rag-stage4-12-chunk-splitting.md) | [projects/ai-service/app/rag/splitters.py](projects/ai-service/app/rag/splitters.py) |
| 13 | 生成 embedding 并写入 Qdrant | [notes/rag-stage4-13-embedding-qdrant-ingestion.md](notes/rag-stage4-13-embedding-qdrant-ingestion.md) | [projects/ai-service/app/rag/embeddings.py](projects/ai-service/app/rag/embeddings.py)、[projects/ai-service/app/rag/vector_store.py](projects/ai-service/app/rag/vector_store.py)、[projects/ai-service/app/rag/ingestion.py](projects/ai-service/app/rag/ingestion.py) |
| 14 | metadata 设计：source、title、section、权限字段 | [notes/rag-stage4-14-metadata-design.md](notes/rag-stage4-14-metadata-design.md) | [projects/ai-service/app/rag/metadata.py](projects/ai-service/app/rag/metadata.py) |
| 15 | 基础 top_k 检索 | [notes/rag-stage4-15-basic-top-k-retrieval.md](notes/rag-stage4-15-basic-top-k-retrieval.md) | [projects/ai-service/app/rag/retriever.py](projects/ai-service/app/rag/retriever.py) |
| 16 | payload filter：按文档类型、权限、来源过滤 | [notes/rag-stage4-16-payload-filter.md](notes/rag-stage4-16-payload-filter.md) | [projects/ai-service/app/rag/filters.py](projects/ai-service/app/rag/filters.py) |
| 17 | score_threshold：低相关内容不回答 | [notes/rag-stage4-17-score-threshold.md](notes/rag-stage4-17-score-threshold.md) | [projects/ai-service/app/rag/retriever.py](projects/ai-service/app/rag/retriever.py)、[projects/ai-service/app/rag/vector_store.py](projects/ai-service/app/rag/vector_store.py) |
| 18 | 把检索结果交给模型回答 | [notes/rag-stage4-18-retrieved-context-to-model-answer.md](notes/rag-stage4-18-retrieved-context-to-model-answer.md) | [projects/ai-service/app/rag/generator.py](projects/ai-service/app/rag/generator.py) |
| 19 | 引用来源：回答必须带出处 | [notes/rag-stage4-19-citations.md](notes/rag-stage4-19-citations.md) | [projects/ai-service/app/rag/generator.py](projects/ai-service/app/rag/generator.py) |
| 20 | 无检索结果时怎么处理 | [notes/rag-stage4-20-no-context-handling.md](notes/rag-stage4-20-no-context-handling.md) | [projects/ai-service/app/rag/generator.py](projects/ai-service/app/rag/generator.py) |
| 21 | RAG 错误处理：embedding、向量库、模型调用异常 | [notes/rag-stage4-21-error-handling.md](notes/rag-stage4-21-error-handling.md) | [projects/ai-service/app/rag/errors.py](projects/ai-service/app/rag/errors.py)、[projects/ai-service/app/rag/retriever.py](projects/ai-service/app/rag/retriever.py)、[projects/ai-service/app/rag/ingestion.py](projects/ai-service/app/rag/ingestion.py) |
| 22 | RAG 测试：fake embedding、fake vector store | [notes/rag-stage4-22-rag-testing-fakes.md](notes/rag-stage4-22-rag-testing-fakes.md) | [projects/ai-service/tests/rag_fakes.py](projects/ai-service/tests/rag_fakes.py) |
| 23 | 文档更新、删除、重新入库 | [notes/rag-stage4-23-document-update-delete-reingest.md](notes/rag-stage4-23-document-update-delete-reingest.md) | [projects/ai-service/app/rag/ingestion.py](projects/ai-service/app/rag/ingestion.py)、[projects/ai-service/app/rag/vector_store.py](projects/ai-service/app/rag/vector_store.py) |
| 24 | embedding 模型选择、维度、成本和批量处理 | [notes/rag-stage4-24-embedding-model-dimension-cost-batch.md](notes/rag-stage4-24-embedding-model-dimension-cost-batch.md) | [projects/ai-service/app/rag/embeddings.py](projects/ai-service/app/rag/embeddings.py)、[projects/ai-service/app/core/config.py](projects/ai-service/app/core/config.py) |
| 25 | 检索质量调优：chunk size、overlap、top_k、score_threshold | [notes/rag-stage4-25-retrieval-quality-tuning.md](notes/rag-stage4-25-retrieval-quality-tuning.md) | [projects/ai-service/app/rag/tuning.py](projects/ai-service/app/rag/tuning.py)、[projects/ai-service/scripts/rag_chunk_tuning_preview.py](projects/ai-service/scripts/rag_chunk_tuning_preview.py) |
| 26 | 混合检索：关键词检索 + 向量检索 | [notes/rag-stage4-26-hybrid-search.md](notes/rag-stage4-26-hybrid-search.md) | [projects/ai-service/app/rag/hybrid.py](projects/ai-service/app/rag/hybrid.py)、[projects/ai-service/scripts/rag_keyword_search_preview.py](projects/ai-service/scripts/rag_keyword_search_preview.py) |
| 27 | rerank 重排序是什么 | [notes/rag-stage4-27-rerank.md](notes/rag-stage4-27-rerank.md) | [projects/ai-service/app/rag/rerank.py](projects/ai-service/app/rag/rerank.py)、[projects/ai-service/scripts/rag_rerank_preview.py](projects/ai-service/scripts/rag_rerank_preview.py) |
| 28 | RAG 安全：文档权限、Prompt Injection、敏感信息 | [notes/rag-stage4-28-rag-security.md](notes/rag-stage4-28-rag-security.md) | [projects/ai-service/app/rag/security.py](projects/ai-service/app/rag/security.py)、[projects/ai-service/scripts/rag_security_preview.py](projects/ai-service/scripts/rag_security_preview.py) |
| 29 | RAG 性能：缓存、批处理、超时、降级 | [notes/rag-stage4-29-rag-performance.md](notes/rag-stage4-29-rag-performance.md) | [projects/ai-service/app/rag/performance.py](projects/ai-service/app/rag/performance.py)、[projects/ai-service/scripts/rag_performance_preview.py](projects/ai-service/scripts/rag_performance_preview.py) |
| 30 | 阶段 4 主线项目验收和复盘 | [notes/rag-stage4-30-project-summary.md](notes/rag-stage4-30-project-summary.md) | [projects/ai-service/app/rag](projects/ai-service/app/rag)、[projects/ai-service/tests](projects/ai-service/tests) |
| 31 | Milvus 是什么，和 Qdrant 有什么区别 | [notes/rag-stage4-31-milvus-vs-qdrant.md](notes/rag-stage4-31-milvus-vs-qdrant.md) | 概念对比，无代码改动 |
| 32 | 本地 Docker 启动 Milvus Standalone | [notes/rag-stage4-32-start-milvus-standalone-locally.md](notes/rag-stage4-32-start-milvus-standalone-locally.md) | VMware Ubuntu Docker 已验证 |
| 33 | Milvus 核心概念：collection、schema、field、entity、index | [notes/rag-stage4-33-milvus-core-concepts.md](notes/rag-stage4-33-milvus-core-concepts.md) | 概念讲解，无代码改动 |
| 34 | 用同一批文档写入 Milvus 并做向量检索 | [notes/rag-stage4-34-milvus-ingestion-search.md](notes/rag-stage4-34-milvus-ingestion-search.md) | [projects/ai-service/app/rag/milvus_store.py](projects/ai-service/app/rag/milvus_store.py)、[projects/ai-service/scripts/rag_milvus_smoke.py](projects/ai-service/scripts/rag_milvus_smoke.py) |
| 35 | Milvus metadata/scalar filter 和索引基础 | [notes/rag-stage4-35-milvus-metadata-scalar-filter-index.md](notes/rag-stage4-35-milvus-metadata-scalar-filter-index.md) | [projects/ai-service/app/rag/milvus_store.py](projects/ai-service/app/rag/milvus_store.py)、[projects/ai-service/scripts/rag_milvus_filter_smoke.py](projects/ai-service/scripts/rag_milvus_filter_smoke.py) |
| 36 | Qdrant vs Milvus：什么时候选谁 | [notes/rag-stage4-36-qdrant-vs-milvus-selection.md](notes/rag-stage4-36-qdrant-vs-milvus-selection.md) | 选型讲解，无代码改动 |
| 37 | RAG 检索评测基础 | [notes/rag-stage4-37-rag-retrieval-evaluation-basics.md](notes/rag-stage4-37-rag-retrieval-evaluation-basics.md) | 概念讲解，无代码改动 |
| 38 | 给当前 RAG 项目做一个最小检索评测脚本 | [notes/rag-stage4-38-rag-retrieval-evaluation-script.md](notes/rag-stage4-38-rag-retrieval-evaluation-script.md) | [projects/ai-service/app/rag/evaluation.py](projects/ai-service/app/rag/evaluation.py)、[projects/ai-service/data/rag_eval/retrieval_cases.json](projects/ai-service/data/rag_eval/retrieval_cases.json)、[projects/ai-service/scripts/rag_retrieval_eval.py](projects/ai-service/scripts/rag_retrieval_eval.py) |
| 39 | 企业知识库 RAG 最终收尾复盘 | [notes/rag-stage4-39-final-review.md](notes/rag-stage4-39-final-review.md) | 阶段 4 总复盘，无代码改动 |

## 阶段 5：LangGraph 智能工单 Agent 学习规划

阶段 5 已确定按 26 节推进，目标是做出智能工单 Agent v1。第 1-12 节先学 LangGraph 基础和图执行方式，第 13-22 节接入智能工单业务流程，第 23-26 节补错误处理、日志、测试和项目整理。

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | LangGraph 是什么，为什么现在才学 | [notes/langgraph-stage5-01-what-is-langgraph.md](notes/langgraph-stage5-01-what-is-langgraph.md) | 概念讲解，无代码改动 |
| 2 | LangGraph 和 LangChain / 普通函数流程的区别 | [notes/langgraph-stage5-02-langgraph-vs-langchain-function-flow.md](notes/langgraph-stage5-02-langgraph-vs-langchain-function-flow.md) | 概念讲解，无代码改动 |
| 3 | Agent 流程和状态机基础 | [notes/langgraph-stage5-03-agent-flow-state-machine-basics.md](notes/langgraph-stage5-03-agent-flow-state-machine-basics.md) | 概念讲解，无代码改动 |
| 4 | State 是什么：Agent 为什么需要状态 | [notes/langgraph-stage5-04-state-agent-needs-state.md](notes/langgraph-stage5-04-state-agent-needs-state.md) | 概念讲解，无代码改动 |
| 5 | Reducer 是什么：状态字段怎么合并 | [notes/langgraph-stage5-05-reducer-state-merge.md](notes/langgraph-stage5-05-reducer-state-merge.md) | 概念讲解，无代码改动 |
| 6 | MessagesState：多轮对话消息怎么保存 | [notes/langgraph-stage5-06-messages-state.md](notes/langgraph-stage5-06-messages-state.md) | 概念讲解，无代码改动 |
| 7 | StateGraph 最小图 | [notes/langgraph-stage5-07-stategraph-minimal-graph.md](notes/langgraph-stage5-07-stategraph-minimal-graph.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/scripts/langgraph_minimal_graph_smoke.py](projects/ai-service/scripts/langgraph_minimal_graph_smoke.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 8 | node 节点是什么 | [notes/langgraph-stage5-08-what-is-node.md](notes/langgraph-stage5-08-what-is-node.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 9 | edge 边是什么 | [notes/langgraph-stage5-09-what-is-edge.md](notes/langgraph-stage5-09-what-is-edge.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 10 | conditional edge 条件分支 | [notes/langgraph-stage5-10-conditional-edge.md](notes/langgraph-stage5-10-conditional-edge.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 11 | START / END 和流程结束 | [notes/langgraph-stage5-11-start-end-flow-finish.md](notes/langgraph-stage5-11-start-end-flow-finish.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 12 | graph.invoke / graph.stream：普通执行和流式执行 | [notes/langgraph-stage5-12-invoke-stream.md](notes/langgraph-stage5-12-invoke-stream.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/scripts/langgraph_minimal_graph_smoke.py](projects/ai-service/scripts/langgraph_minimal_graph_smoke.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 13 | 智能工单 Agent 总流程设计 | [notes/langgraph-stage5-13-ticket-agent-overall-design.md](notes/langgraph-stage5-13-ticket-agent-overall-design.md) | 设计笔记，无代码改动 |
| 14 | 意图识别节点 | [notes/langgraph-stage5-14-intent-classification-node.md](notes/langgraph-stage5-14-intent-classification-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 15 | RAG 知识库回答节点 | [notes/langgraph-stage5-15-rag-policy-node.md](notes/langgraph-stage5-15-rag-policy-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 16 | 判断是否需要创建工单 | [notes/langgraph-stage5-16-decide-ticket-need.md](notes/langgraph-stage5-16-decide-ticket-need.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 17 | 工单字段提取节点 | [notes/langgraph-stage5-17-ticket-field-extraction-node.md](notes/langgraph-stage5-17-ticket-field-extraction-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 18 | 缺失字段追问节点 | [notes/langgraph-stage5-18-missing-field-follow-up-node.md](notes/langgraph-stage5-18-missing-field-follow-up-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 19 | 用户确认节点 | [notes/langgraph-stage5-19-ticket-confirmation-node.md](notes/langgraph-stage5-19-ticket-confirmation-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 20 | 调用 Java mock 创建工单节点 | [notes/langgraph-stage5-20-java-mock-create-ticket-node.md](notes/langgraph-stage5-20-java-mock-create-ticket-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/app/schemas/ticket.py](projects/ai-service/app/schemas/ticket.py)、[projects/java-mock-service/app/schemas/ticket.py](projects/java-mock-service/app/schemas/ticket.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py)、[projects/java-mock-service/tests/test_tickets_api.py](projects/java-mock-service/tests/test_tickets_api.py) |
| 21 | checkpoint 和 thread_id：中断、恢复、继续对话 | [notes/langgraph-stage5-21-checkpoint-thread-id.md](notes/langgraph-stage5-21-checkpoint-thread-id.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 22 | interrupt / human-in-the-loop | [notes/langgraph-stage5-22-interrupt-human-in-the-loop.md](notes/langgraph-stage5-22-interrupt-human-in-the-loop.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 23 | 节点错误处理、fallback 和流程兜底 | [notes/langgraph-stage5-23-node-error-fallback.md](notes/langgraph-stage5-23-node-error-fallback.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 24 | LangGraph 日志、trace_id 和可观测性 | [notes/langgraph-stage5-24-observability-trace-logging.md](notes/langgraph-stage5-24-observability-trace-logging.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 25 | LangGraph 测试：fake LLM / fake RAG / fake Java client | [notes/langgraph-stage5-25-agent-testing-fakes.md](notes/langgraph-stage5-25-agent-testing-fakes.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/tool_fakes.py](projects/ai-service/tests/tool_fakes.py)、[projects/ai-service/tests/test_tool_fakes.py](projects/ai-service/tests/test_tool_fakes.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 26 | 阶段 5 项目整理和面试表达 | [notes/langgraph-stage5-26-project-summary-interview.md](notes/langgraph-stage5-26-project-summary-interview.md) | 阶段 5 总复盘，梳理 [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py)、[projects/ai-service/tests/tool_fakes.py](projects/ai-service/tests/tool_fakes.py) |

## 阶段 6：生产化与评测学习规划

阶段 6 固定为 36 节，目标是把已经能运行的 RAG + 智能工单 Agent v1 往真实工程系统推进。这个阶段会补 Agent 评测、真实模型节点、工具链路生产化、持久化 checkpoint、可观测性、稳定性保护、部署编排和阶段复盘。

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | Agent 评测基础：为什么 AI 应用不能只靠感觉判断好坏 | [notes/stage6-01-agent-evaluation-basics.md](notes/stage6-01-agent-evaluation-basics.md) | 概念讲解，无代码改动 |
| 2 | 什么是 eval：测试和评测的区别 | [notes/stage6-02-test-vs-eval.md](notes/stage6-02-test-vs-eval.md) | 概念讲解，无代码改动 |
| 3 | 设计 Agent 测试集 | [notes/stage6-03-agent-eval-dataset-design.md](notes/stage6-03-agent-eval-dataset-design.md) | [projects/ai-service/data/agent_eval/agent_cases.json](projects/ai-service/data/agent_eval/agent_cases.json)、[projects/ai-service/data/agent_eval/README.md](projects/ai-service/data/agent_eval/README.md) |
| 4 | 意图识别评测 | [notes/stage6-04-agent-intent-evaluation.md](notes/stage6-04-agent-intent-evaluation.md) | [projects/ai-service/app/agents/intent_evaluation.py](projects/ai-service/app/agents/intent_evaluation.py)、[projects/ai-service/scripts/agent_intent_eval.py](projects/ai-service/scripts/agent_intent_eval.py)、[projects/ai-service/tests/test_agent_intent_evaluation.py](projects/ai-service/tests/test_agent_intent_evaluation.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py) |
| 5 | 工单字段提取评测 | [notes/stage6-05-agent-ticket-field-evaluation.md](notes/stage6-05-agent-ticket-field-evaluation.md) | [projects/ai-service/app/agents/field_evaluation.py](projects/ai-service/app/agents/field_evaluation.py)、[projects/ai-service/scripts/agent_ticket_field_eval.py](projects/ai-service/scripts/agent_ticket_field_eval.py)、[projects/ai-service/tests/test_agent_field_evaluation.py](projects/ai-service/tests/test_agent_field_evaluation.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py) |
| 6 | Agent 路由评测 | [notes/stage6-06-agent-route-evaluation.md](notes/stage6-06-agent-route-evaluation.md) | [projects/ai-service/app/agents/route_evaluation.py](projects/ai-service/app/agents/route_evaluation.py)、[projects/ai-service/scripts/agent_route_eval.py](projects/ai-service/scripts/agent_route_eval.py)、[projects/ai-service/tests/test_agent_route_evaluation.py](projects/ai-service/tests/test_agent_route_evaluation.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py) |
| 7 | RAG + Agent 组合评测 | [notes/stage6-07-rag-agent-combination-evaluation.md](notes/stage6-07-rag-agent-combination-evaluation.md) | [projects/ai-service/app/agents/rag_agent_evaluation.py](projects/ai-service/app/agents/rag_agent_evaluation.py)、[projects/ai-service/scripts/agent_rag_eval.py](projects/ai-service/scripts/agent_rag_eval.py)、[projects/ai-service/tests/test_agent_rag_evaluation.py](projects/ai-service/tests/test_agent_rag_evaluation.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py) |
| 8 | 评测脚本设计 | [notes/stage6-08-agent-eval-script-design.md](notes/stage6-08-agent-eval-script-design.md) | [projects/ai-service/app/agents/eval_suite.py](projects/ai-service/app/agents/eval_suite.py)、[projects/ai-service/scripts/agent_eval.py](projects/ai-service/scripts/agent_eval.py)、[projects/ai-service/tests/test_agent_eval_suite.py](projects/ai-service/tests/test_agent_eval_suite.py) |
| 9 | 评测报告 | [notes/stage6-09-agent-eval-report.md](notes/stage6-09-agent-eval-report.md) | [projects/ai-service/app/agents/eval_report.py](projects/ai-service/app/agents/eval_report.py)、[projects/ai-service/scripts/agent_eval.py](projects/ai-service/scripts/agent_eval.py)、[projects/ai-service/tests/test_agent_eval_report.py](projects/ai-service/tests/test_agent_eval_report.py)、[projects/ai-service/data/agent_eval/reports/agent_eval_report.md](projects/ai-service/data/agent_eval/reports/agent_eval_report.md) |
| 10 | 坏例分析 | [notes/stage6-10-bad-case-analysis.md](notes/stage6-10-bad-case-analysis.md) | [projects/ai-service/app/agents/bad_case_analysis.py](projects/ai-service/app/agents/bad_case_analysis.py)、[projects/ai-service/scripts/agent_eval.py](projects/ai-service/scripts/agent_eval.py)、[projects/ai-service/tests/test_bad_case_analysis.py](projects/ai-service/tests/test_bad_case_analysis.py)、[projects/ai-service/data/agent_eval/reports/agent_bad_case_analysis.md](projects/ai-service/data/agent_eval/reports/agent_bad_case_analysis.md)、[projects/ai-service/data/agent_eval/reports/bad_case_analysis_sample.md](projects/ai-service/data/agent_eval/reports/bad_case_analysis_sample.md) |
| 11 | 回归评测 | [notes/stage6-11-regression-evaluation.md](notes/stage6-11-regression-evaluation.md) | [projects/ai-service/app/agents/eval_suite.py](projects/ai-service/app/agents/eval_suite.py)、[projects/ai-service/scripts/agent_eval.py](projects/ai-service/scripts/agent_eval.py)、[projects/ai-service/tests/test_agent_eval_suite.py](projects/ai-service/tests/test_agent_eval_suite.py)、[projects/ai-service/data/agent_eval/agent_cases.json](projects/ai-service/data/agent_eval/agent_cases.json)、[projects/ai-service/data/agent_eval/reports/agent_regression_report.md](projects/ai-service/data/agent_eval/reports/agent_regression_report.md)、[projects/ai-service/data/agent_eval/reports/agent_regression_bad_case_analysis.md](projects/ai-service/data/agent_eval/reports/agent_regression_bad_case_analysis.md) |
| 12 | evaluator 类型 | [notes/stage6-12-evaluator-types.md](notes/stage6-12-evaluator-types.md) | 概念讲解，对照 [projects/ai-service/app/agents/intent_evaluation.py](projects/ai-service/app/agents/intent_evaluation.py)、[projects/ai-service/app/agents/field_evaluation.py](projects/ai-service/app/agents/field_evaluation.py)、[projects/ai-service/app/agents/route_evaluation.py](projects/ai-service/app/agents/route_evaluation.py)、[projects/ai-service/app/agents/rag_agent_evaluation.py](projects/ai-service/app/agents/rag_agent_evaluation.py)、[projects/ai-service/app/agents/eval_suite.py](projects/ai-service/app/agents/eval_suite.py)、[projects/ai-service/app/agents/eval_report.py](projects/ai-service/app/agents/eval_report.py)、[projects/ai-service/app/agents/bad_case_analysis.py](projects/ai-service/app/agents/bad_case_analysis.py) |
| 13 | 真实 LLM 意图识别节点 | [notes/stage6-13-real-llm-intent-node.md](notes/stage6-13-real-llm-intent-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_llm_intent.py](projects/ai-service/tests/test_ticket_agent_llm_intent.py)、[projects/ai-service/scripts/ticket_agent_llm_intent_smoke.py](projects/ai-service/scripts/ticket_agent_llm_intent_smoke.py) |
| 14 | 真实 LLM 字段提取节点 | [notes/stage6-14-real-llm-field-extraction-node.md](notes/stage6-14-real-llm-field-extraction-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_llm_fields.py](projects/ai-service/tests/test_ticket_agent_llm_fields.py)、[projects/ai-service/scripts/ticket_agent_llm_field_smoke.py](projects/ai-service/scripts/ticket_agent_llm_field_smoke.py) |
| 15 | Pydantic 校验模型输出 | [notes/stage6-15-pydantic-validate-model-output.md](notes/stage6-15-pydantic-validate-model-output.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_llm_output_validation.py](projects/ai-service/tests/test_ticket_agent_llm_output_validation.py) |
| 16 | fake LLM 和真实 LLM 双模式 | [notes/stage6-16-fake-real-llm-modes.md](notes/stage6-16-fake-real-llm-modes.md) | [projects/ai-service/app/core/config.py](projects/ai-service/app/core/config.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/.env.example](projects/ai-service/.env.example)、[projects/ai-service/tests/test_config.py](projects/ai-service/tests/test_config.py)、[projects/ai-service/tests/test_ticket_agent_llm_modes.py](projects/ai-service/tests/test_ticket_agent_llm_modes.py) |
| 17 | prompt 版本管理 | [notes/stage6-17-prompt-version-management.md](notes/stage6-17-prompt-version-management.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_prompt_versions.py](projects/ai-service/tests/test_ticket_agent_prompt_versions.py)、[projects/ai-service/tests/test_ticket_agent_llm_intent.py](projects/ai-service/tests/test_ticket_agent_llm_intent.py)、[projects/ai-service/tests/test_ticket_agent_llm_fields.py](projects/ai-service/tests/test_ticket_agent_llm_fields.py) |
| 18 | 模型输出失败处理 | [notes/stage6-18-model-output-failure-handling.md](notes/stage6-18-model-output-failure-handling.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_model_output_failure.py](projects/ai-service/tests/test_ticket_agent_model_output_failure.py)、[projects/ai-service/tests/test_ticket_agent_llm_output_validation.py](projects/ai-service/tests/test_ticket_agent_llm_output_validation.py) |
| 19 | 接入真实 `query_order` 到 LangGraph | [notes/stage6-19-query-order-langgraph.md](notes/stage6-19-query-order-langgraph.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/app/tools/fake_order_tool.py](projects/ai-service/app/tools/fake_order_tool.py)、[projects/ai-service/tests/test_ticket_agent_query_order_node.py](projects/ai-service/tests/test_ticket_agent_query_order_node.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 20 | 工具节点错误处理升级 | [notes/stage6-20-tool-node-error-handling.md](notes/stage6-20-tool-node-error-handling.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_query_order_node.py](projects/ai-service/tests/test_ticket_agent_query_order_node.py) |
| 21 | 工具权限和写操作安全回归 | [notes/stage6-21-tool-permission-write-safety-regression.md](notes/stage6-21-tool-permission-write-safety-regression.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/app/tools/tool_registry.py](projects/ai-service/app/tools/tool_registry.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py)、[projects/ai-service/tests/test_tool_registry.py](projects/ai-service/tests/test_tool_registry.py) |
| 22 | 持久化 checkpoint 基础 | [notes/stage6-22-persistent-checkpoint-basics.md](notes/stage6-22-persistent-checkpoint-basics.md) | [projects/ai-service/app/agents/checkpoint_store.py](projects/ai-service/app/agents/checkpoint_store.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_checkpoint_store.py](projects/ai-service/tests/test_ticket_agent_checkpoint_store.py) |
| 23 | checkpoint 存储选型 | [notes/stage6-23-checkpoint-storage-selection.md](notes/stage6-23-checkpoint-storage-selection.md) | 概念讲解，对照 [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/app/agents/checkpoint_store.py](projects/ai-service/app/agents/checkpoint_store.py) |
| 24 | `thread_id` 生命周期 | [notes/stage6-24-thread-id-lifecycle.md](notes/stage6-24-thread-id-lifecycle.md) | [projects/ai-service/app/agents/thread_lifecycle.py](projects/ai-service/app/agents/thread_lifecycle.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_thread_lifecycle.py](projects/ai-service/tests/test_ticket_agent_thread_lifecycle.py) |
| 25 | 会话过期与清理 | [notes/stage6-25-session-expiration-cleanup.md](notes/stage6-25-session-expiration-cleanup.md) | [projects/ai-service/app/agents/thread_cleanup.py](projects/ai-service/app/agents/thread_cleanup.py)、[projects/ai-service/app/agents/thread_lifecycle.py](projects/ai-service/app/agents/thread_lifecycle.py)、[projects/ai-service/tests/test_ticket_agent_thread_cleanup.py](projects/ai-service/tests/test_ticket_agent_thread_cleanup.py) |
| 26 | LangSmith tracing 基础 | [notes/stage6-26-langsmith-tracing-basics.md](notes/stage6-26-langsmith-tracing-basics.md) | [projects/ai-service/app/agents/langsmith_tracing.py](projects/ai-service/app/agents/langsmith_tracing.py)、[projects/ai-service/tests/test_ticket_agent_langsmith_tracing.py](projects/ai-service/tests/test_ticket_agent_langsmith_tracing.py) |
| 27 | OpenTelemetry 基础 | [notes/stage6-27-opentelemetry-basics.md](notes/stage6-27-opentelemetry-basics.md) | [projects/ai-service/app/agents/otel_tracing.py](projects/ai-service/app/agents/otel_tracing.py)、[projects/ai-service/tests/test_ticket_agent_otel_tracing.py](projects/ai-service/tests/test_ticket_agent_otel_tracing.py) |
| 28 | trace/span/log/metrics 的关系 | [notes/stage6-28-trace-span-log-metrics-relationship.md](notes/stage6-28-trace-span-log-metrics-relationship.md) | [projects/ai-service/app/agents/observability_signals.py](projects/ai-service/app/agents/observability_signals.py)、[projects/ai-service/tests/test_ticket_agent_observability_signals.py](projects/ai-service/tests/test_ticket_agent_observability_signals.py) |
| 29 | 生产日志字段设计 | [notes/stage6-29-production-log-field-design.md](notes/stage6-29-production-log-field-design.md) | [projects/ai-service/app/agents/production_logging.py](projects/ai-service/app/agents/production_logging.py)、[projects/ai-service/tests/test_ticket_agent_production_logging.py](projects/ai-service/tests/test_ticket_agent_production_logging.py) |
| 30 | 成本、token 和延迟指标 | [notes/stage6-30-cost-token-latency-metrics.md](notes/stage6-30-cost-token-latency-metrics.md) | [projects/ai-service/app/agents/llm_metrics.py](projects/ai-service/app/agents/llm_metrics.py)、[projects/ai-service/tests/test_ticket_agent_llm_metrics.py](projects/ai-service/tests/test_ticket_agent_llm_metrics.py) |
| 31 | timeout 超时策略 | [notes/stage6-31-timeout-strategy.md](notes/stage6-31-timeout-strategy.md) | [projects/ai-service/app/agents/timeout_strategy.py](projects/ai-service/app/agents/timeout_strategy.py)、[projects/ai-service/tests/test_ticket_agent_timeout_strategy.py](projects/ai-service/tests/test_ticket_agent_timeout_strategy.py) |
| 32 | retry 重试策略 | [notes/stage6-32-retry-strategy.md](notes/stage6-32-retry-strategy.md) | [projects/ai-service/app/agents/retry_strategy.py](projects/ai-service/app/agents/retry_strategy.py)、[projects/ai-service/tests/test_ticket_agent_retry_strategy.py](projects/ai-service/tests/test_ticket_agent_retry_strategy.py) |
| 33 | rate limit、circuit breaker 和降级 | 待新增 | 待新增 |
| 34 | Docker Compose 本地编排 | 待新增 | 待新增 |
| 35 | health check、readiness 和 CI 自动回归 | 待新增 | 待新增 |
| 36 | 阶段 6 项目整理和面试表达 | 待新增 | 待新增 |

## 当前目标

12 周内完成两个能展示的项目：

1. 企业知识库 RAG 系统
2. 智能工单 Agent

第三个项目“业务数据助手”作为加分项，等前两个主项目稳定后再做。

每次继续学习时，优先更新 `docs/learning-progress.md`，再把代码、笔记和复盘分别放入对应目录。
