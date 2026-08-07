# RAG 体系完善 — 设计规格

> 日期：2026-08-07
> 项目：AI 客服/工单系统（Java 18004 / Python AI 8000 / Vue 5173）
> 目标：完善 RAG 知识库问答体系——A 对话链路真实化收尾、B 高级检索模块（规则+LLM 双实现）统一接线、C 真实检索评测（双模式+结果入库）、D 知识库运营闭环（多 collection + 文档 CRUD + 趋势图扩展）。

## 1. 背景与现状

### 1.1 现状（explore 调查）
- **A 已基本完成**：`ProductionPolicyRagService`（console_agent_service.py:211-251）已是真实 RAG 封装（embedding + Qdrant + rerank + 生成带引用），且已在对话链路注入（多 Agent :286 / 单 Agent :296）；`FakePolicyRagService`（ticket_agent.py:1457）仅作 `create_policy_rag_service()`（:3640）兜底。**缺口**：`retrieve_top_k` 未传 access_scope/权限过滤参数。
- **B 高级模块全部已写好但未接入运行时**（均纯规则、无 LLM 依赖）：
  - `query_rewrite.py`：`RuleBasedQueryRewriter`（:103）+ `QueryRewriter` Protocol（:18）
  - `multi_query.py`：`RuleBasedMultiQueryGenerator`（:150）+ `MultiQueryGenerator` Protocol（:31）
  - `knowledge_routing.py`：`RuleBasedRagKnowledgeRouter`（:75）+ `RagKnowledgeRouter` Protocol（:63）；6 知识库定义 `default_rag_knowledge_bases()`（:184-252），映射 collection `kb_customer_policy`/`kb_account_security`/`kb_customer_process`/`kb_internal_process`
  - `hybrid.py`：`hybrid_retrieve`（:270-318，向量 0.7+关键词 0.3 融合）；`SimpleKeywordRetriever`（:42-84，内存实现，对本地切分 chunks 打分）
  - `citation_verification.py`：`verify_rag_answer_sources`（:85-90，纯规则）
  - `context_compression.py`：`compress_retrieved_context`（:67-72，纯规则，预算 1800/700/160 字符）
- **C 评测现状**：`scripts/rag_retrieval_eval.py` 用 `SimpleKeywordRetriever`（内存/本地切分）；`app/rag/evaluation.py` 有完整指标（Hit@K/Recall@K/Precision@K/MRR@K :784-821）；评测数据 `data/rag_eval/retrieval_cases.json`（12 例）+ `rag_cases.json`（8 例端到端）
- **D 管理现状**：`app/routers/knowledge_base.py` 有 `GET /status`（:56-89）+ `POST /ingest`（:92-144，单 collection）；前端 KnowledgeBaseView 有 Fake/真实入库按钮 + 文档列表；Java `knowledge_documents` 表（schema.sql:142-159）+ `GET /api/knowledge-documents`（KnowledgeDocumentController:30-40）

### 1.2 目标（用户确认的决策）
- **A 仅收尾**：补权限过滤传参 + Fake 标 deprecated
- **B 全部 6 个高级模块**：规则+LLM 双实现（配置开关默认 rule），统一接入 RAG 链路（ProductionPolicyRagService + ask_rag 两处）
- **C 双模式+结果入库**：`--retriever=keyword|vector`，Hit@K/Recall@K 报告 + 结果入库供趋势图
- **D 完整运营闭环**：多 collection + 文档列表/上传/编辑/删除 + 同步 Qdrant + **Java 侧 CRUD 持久化元数据**（用户升级为必做）+ **趋势图 rag_retrieval 扩展**（用户升级为必做）

## 2. 架构与数据流

```
用户提问 → Agent/knowledge_agent（ProductionPolicyRagService）
    → [B] query_rewriter.rewrite → knowledge_router.route(选 collection+filter)
    → [B] multi_query_generator.generate(多查询)
    → [B] hybrid_retrieve 或 retrieve_top_k（按 route.collection_name 构造 store）
    → rerank_with_fallback
    → [B] context_compression.compress
    → generate_answer_with_citations
    → [B] citation_verification.verify（结果进日志/评测）
    → 前端 citations 渲染

[C] 评测脚本 --retriever=vector → 真 Qdrant+真 embedding → Hit@K/Recall@K → runs.json → history 趋势图
[D] 知识库管理：前端 CRUD → Java knowledge_documents 元数据 + Python 落盘 → 同步 Qdrant（多 collection）
```

## 3. 阶段 1：A 收尾 + C 真实评测

### 3.1 A 收尾
1. `ProductionPolicyRagService.answer_policy_question` 补权限过滤参数：从 settings/请求上下文取 `access_scope`/`permission_group`/`business_domain`/`doc_type`/`source` 传入 `retrieve_top_k`（对话场景默认不限，跟随 `build_payload_filter` 语义）
2. `create_policy_rag_service()`（ticket_agent.py:3640）加 deprecated 注释/docstring："仅测试/兜底使用，生产对话链路由 ProductionPolicyRagService 注入"；不改行为

### 3.2 C 双模式评测
1. `scripts/rag_retrieval_eval.py` 新增 `--retriever=keyword|vector`（默认 keyword 保测试快）：
   - keyword：现有 `SimpleKeywordRetriever(chunks)`（本地切分）
   - vector：`retrieve_top_k(query, embedding_model=OpenAICompatibleEmbeddingModel.from_settings(settings), vector_store=QdrantVectorStore.from_settings(settings), top_k=...)`
2. 输出 Hit@K/Recall@K/Precision@K/MRR@K 摘要 + bad cases（复用 evaluation.py 指标）
3. **结果入库**：`data/evaluation/rag_retrieval_runs.json`（原子写 + 30 条上限，仿 production_regression_runs.json）；`get_rag_retrieval_history_path` 依赖（仿 get_production_regression_history_path :89-90）
4. 配置：`RAG_RETRIEVAL_EVAL_RETRIEVER=keyword|vector`

## 4. 阶段 2：B 高级模块双实现 + 统一接线

### 4.1 新增 LLM 实现类（qwen3.7-plus，规则版 fallback）
| 模块 | LLM 变体 | 失败回退 |
| --- | --- | --- |
| query_rewrite | `LLMQueryRewriter.rewrite(query) -> str`（口语→规范检索问法） | RuleBasedQueryRewriter |
| multi_query | `LLMMultiQueryGenerator.generate(query) -> MultiQueryExpansion`（语义/政策/场景/关键词角度） | RuleBasedMultiQueryGenerator |
| knowledge_routing | `LLMRagKnowledgeRouter.route(query) -> RagKnowledgeRouteDecision`（意图选库） | RuleBasedRagKnowledgeRouter |

工厂：`create_query_rewriter(settings)` / `create_multi_query_generator(settings)` / `create_knowledge_router(settings)`——按 `RAG_ADVANCED_MODE=llm` 选 LLM，否则规则。

### 4.2 SimpleKeywordRetriever 升级（hybrid 需要真库关键词）
- 从真库 chunk 构建关键词索引：从 Qdrant 拉取 collection 全量 payload（或维护本地 chunk 缓存），用同一 CJK bigram/trigram 打分逻辑检索——`hybrid_retrieve` 的"向量+关键词"都基于真库

### 4.3 统一接入 RAG 链路
新增 `enhanced_rag_answer(query, *, settings, access_scope=None)`（`app/rag/pipeline.py` 或并入 rag 包）：
```python
# 1. rewrite → 2. route（选 collection+filter）→ 3. multi_query
# 4. hybrid 或 vector 检索（按 route.collection_name 构造 store，多查询去重合并 top_k）
# 5. rerank → 6. context_compression → 7. generate_answer_with_citations → 8. citation_verification
```
- 接线点：`ProductionPolicyRagService`（对话）+ `ask_rag` 端点（rag.py:65-125）共用 pipeline
- **配置开关**（config.py 新增，默认 rule/off 保测试绿）：
  - `RAG_ADVANCED_MODE=rule|llm`
  - `RAG_ENABLE_REWRITE`/`RAG_ENABLE_MULTI_QUERY`/`RAG_ENABLE_ROUTING`/`RAG_ENABLE_HYBRID`/`RAG_ENABLE_CONTEXT_COMPRESSION`/`RAG_ENABLE_CITATION_VERIFY`（默认 false）
  - `RAG_HYBRID_VECTOR_WEIGHT=0.7`/`RAG_HYBRID_KEYWORD_WEIGHT=0.3`

### 4.4 多 collection 支持（D 复用）
- `QdrantVectorStore.from_settings(settings, collection_name=...)` 扩展按知识库构造；知识路由 6 库映射生效

## 5. 阶段 3：D 知识库运营闭环

### 5.1 多 collection
- collection 管理端点：列出所有知识库 collection + chunk 数 + 状态

### 5.2 文档 CRUD + 同步 Qdrant（Python API + Java 元数据持久化）
| 端点 | 功能 |
| --- | --- |
| `GET /api/knowledge-base/documents` | 文档列表（本地文件 + Java 元数据 + chunk 数） |
| `POST /api/knowledge-base/documents` | 上传（标题/内容/业务域/权限组/目标 collection → 落盘 + Java 元数据 + 同步 Qdrant） |
| `PUT /api/knowledge-base/documents/{id}` | 编辑（改内容 → 重新切分 upsert 删旧 chunk） |
| `DELETE /api/knowledge-base/documents/{id}` | 删除（删文件 + Java 元数据 + 删 Qdrant chunk） |
| `POST /api/knowledge-base/documents/{id}/ingest` | 单独同步到指定 collection |

**Java 侧（必做）**：`KnowledgeDocumentController` 新增 POST/PUT/DELETE 端点持久化 `knowledge_documents` 元数据（`KnowledgeDocumentService` 仿现有 list 模式 + 新 upsert/delete）；Python 侧调 Java 内部接口（仿 java_order_client 模式）或 Python 直连——**跟随项目现状，实现时确认**（Java 持久化元数据，Python 负责文件+Qdrant，两者通过接口协作）。

### 5.3 前端 KnowledgeBaseView 扩展
- 文档表格操作列：编辑 / 删除 / 单独同步；"上传文档"按钮（表单）；编辑弹窗；多 collection 状态展示

### 5.4 趋势图扩展（必做）
- `GET /api/ai/evaluation/history` 加 `rag_retrieval` 序列（hit_rate/recall 随时间）
- 前端趋势图第三条线（RAG 检索质量）

## 6. 测试与验收

### 阶段 1
| 模块 | 测试 |
| --- | --- |
| A 权限过滤 | ProductionPolicyRagService 传参测试（access_scope 透传到 retrieve_top_k） |
| C 双模式 | vector 模式连真库冒烟（keyword 保现有测试快）；结果入库原子写 |

### 阶段 2
| 模块 | 测试 |
| --- | --- |
| LLM 实现类 | 每类单测（fake LLM → 正确输出；异常 → 回退规则） |
| SimpleKeywordRetriever 升级 | 真库 chunk 构建索引后检索正确性 |
| 统一接线 | RAG_ENABLE_* 全开时完整链（mock 各步调用顺序）；默认全关行为与现在一致（回归） |

### 阶段 3
| 模块 | 测试 |
| --- | --- |
| 多 collection | QdrantVectorStore 按 collection 构造；collection 管理端点 |
| CRUD | 上传→同步（chunk 出现）；编辑→重新切分（旧删新增）；删除→清空；幂等 |
| Java | KnowledgeDocumentController POST/PUT/DELETE 测试 |
| 前端 | npm build ✓ |

### 真实验收（Python 8000 + VM Qdrant）
- 阶段 1：`--retriever=vector` 评测 → Hit@K/Recall@K 报告 + runs.json + history 含 rag_retrieval
- 阶段 2：`RAG_ADVANCED_MODE=llm` + 全开关 → 对话"退货运费谁出"走 LLM 改写+混合检索→带引用答案；关掉恢复规则一致
- 阶段 3：上传新文档→Qdrant chunk→对话检索到；编辑/删除→同步生效

## 7. 范围外（YAGNI）
- 多渠道接入 / 语音 / 长期记忆（上轮调研 P2）
- 会话级转人工 / AI 辅助坐席 / 工单自动化规则 / SLA / CSAT / 业务看板（客服与工单运营线，本次不做）

## 8. 风险与开放点
- **LLM 高级模块自动测试**：LLM 实现类单测用 fake LLM；真实链路验收手动/冒烟（与现有自动测试不调真实模型约束一致）
- **SimpleKeywordRetriever 真库索引**：从 Qdrant 拉全量 payload 可能大——需分页/缓存策略（实现时定）
- **Java/Python 元数据协作**：上传走 Java 接口还是 Python 直连——跟随项目现状实现时确认
- **多 collection 数据迁移**：现有单 collection `learning_rag_chunks_v4_1024` 的知识路由映射——阶段 3 决定是否迁移或双写
