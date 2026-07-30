# 阶段 9 第 8 节：真实 Rerank 模型接入

## 本节定位

本节学习：

```text
真实 Rerank 模型怎么接入项目。
```

前一节我们学了 Rerank 进阶：

```text
召回负责找候选。
Rerank 负责对候选重新排序。
```

上一节我们用的是规则版 `RuleBasedReranker`。

它适合学习、测试和兜底。

但真实项目里，经常会接入专门的 rerank 模型。

本节要解决的问题是：

```text
如果有一个真实 rerank 模型 API，项目应该怎么设计 adapter，怎么传 query 和 candidates，怎么解析分数，怎么测试，失败时怎么 fallback？
```

注意，本节不是让你现在必须买某个 rerank 服务。

本节重点是建立工程边界：

```text
真实模型可以接，但自动化测试不能依赖真实模型。
真实模型可能失败，所以必须有 fallback。
真实模型分数是 rerank_score，不能和 retrieval_score 混用。
```

## 本节学习目标

学完本节，你要能做到：

1. 能解释真实 rerank 模型是什么。
2. 能说清楚 rerank 模型和 embedding 模型的区别。
3. 能理解 cross-encoder rerank 的基础思路。
4. 能解释为什么 rerank 输入通常是 `query + candidate documents`。
5. 能理解真实 rerank 模型输出的 `index` 和 `relevance_score`。
6. 能看懂本节新增的 `HttpReranker`。
7. 能解释为什么真实 rerank adapter 不应该直接写死某个业务流程。
8. 能理解为什么自动化测试用 `httpx.MockTransport`，不真实联网。
9. 能解释 `rerank_with_fallback()` 的作用。
10. 能说明真实模型失败时为什么可以退回规则版 rerank。
11. 能理解 rerank 配置为什么独立于 LLM 和 embedding 配置。
12. 能说清楚真实 rerank 接入后还有哪些生产化问题。

## 本节新增和修改

本节修改：

```text
projects/ai-service/app/core/config.py
projects/ai-service/.env.example
projects/ai-service/app/rag/rerank.py
projects/ai-service/app/rag/score_interpretation.py
projects/ai-service/tests/test_rag_rerank.py
projects/ai-service/tests/test_rag_score_interpretation.py
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

本节新增：

```text
notes/stage9-08-real-rerank-model-adapter.md
```

本节没有：

- 启动 VMware Ubuntu。
- 启动 Qdrant。
- 启动 Milvus。
- 调用真实 rerank API。
- 调用真实大模型。
- 新增手动测试文档。

原因是本节新增的是 adapter 边界和 MockTransport 测试。

真实调用外部 rerank 服务属于手动 smoke 或后续配置验证，不应该放进自动化测试。

## 一句话先讲透

真实 rerank adapter 的职责是：

```text
把本地候选 chunk 转成 rerank API 请求，把模型返回的 index + relevance_score 转回 RerankedChunk，并在失败时可退回规则版 rerank。
```

它不是：

```text
替代向量库。
替代 Hybrid Search。
替代最终回答生成。
```

它只负责：

```text
对候选重新排序。
```

## 基础知识铺垫

### 1. 真实 rerank 模型是什么

真实 rerank 模型是一类专门做相关性排序的模型。

它通常接收：

```text
query
候选 documents
```

返回：

```text
每个候选和 query 的相关性分数
排序后的候选索引
```

典型输入：

```json
{
  "model": "rerank-model",
  "query": "退款多久到账？",
  "documents": [
    "退款申请条件...",
    "退款到账时间通常为 1 到 3 个工作日...",
    "退货运费规则..."
  ],
  "top_n": 2
}
```

典型输出：

```json
{
  "results": [
    {"index": 1, "relevance_score": 0.93},
    {"index": 0, "relevance_score": 0.41}
  ]
}
```

这里的 `index=1` 表示：

```text
输入 documents 列表里的第 2 个文档。
```

`relevance_score=0.93` 表示：

```text
模型认为这个候选和 query 的相关性分数。
```

### 2. Rerank 模型和 embedding 模型有什么区别

Embedding 模型通常做：

```text
单独把 query 转成向量。
单独把 document 转成向量。
再用向量相似度搜索。
```

它的流程像这样：

```text
query -> query vector
document -> document vector
similarity(query vector, document vector)
```

Rerank 模型通常做：

```text
同时看 query 和 candidate document。
直接判断这一对文本是否相关。
```

流程像这样：

```text
(query, document) -> relevance_score
```

这就是为什么 rerank 通常比单纯向量相似更精细。

因为它不是只比较两个提前算好的向量。

它可以直接看到：

```text
用户到底问什么。
候选文档到底写什么。
两者是否真正对应。
```

### 3. 什么是 cross-encoder

Cross-encoder 是 rerank 里常见的一种模型思路。

它会把：

```text
query + document
```

一起输入模型。

模型在内部同时看两段文本之间的交互关系。

这和 embedding 双塔检索不一样。

Embedding 检索更像：

```text
query 独立编码。
document 独立编码。
最后算相似度。
```

Cross-encoder 更像：

```text
把 query 和 document 放在一起精读。
```

所以它通常更准，但也更慢。

### 4. 为什么不直接用 rerank 替代向量库

因为 rerank 通常不能对全量文档直接跑。

假设知识库有：

```text
100000 个 chunk
```

如果每次用户提问都让 rerank 模型比较：

```text
query + 100000 个 chunk
```

成本和延迟都会非常高。

所以正确做法是：

```text
先用向量检索 / 关键词检索 / Hybrid Search 找出几十个候选。
再让 rerank 模型处理这几十个候选。
```

这就是：

```text
粗召回 + 精排
```

### 5. 为什么 rerank 输入是候选 documents

Rerank 模型不负责从数据库找资料。

它只负责对候选排序。

所以输入需要包括：

```text
query
documents
```

这里的 documents 就是候选 chunk 的正文。

本项目中来自：

```text
RerankCandidate.content
```

### 6. 为什么 rerank 输出 index

很多 rerank API 返回的是：

```text
index
relevance_score
```

而不是完整文档。

原因是：

```text
输入 documents 本来就在客户端。
返回 index 就能定位原始候选。
```

比如：

```text
documents[0] = "退款申请条件..."
documents[1] = "退款到账时间..."
```

模型返回：

```text
index = 1
```

就表示：

```text
它认为 documents[1] 更相关。
```

所以 adapter 必须正确处理 index。

如果 index 越界、重复、不是整数，都应该拒绝。

### 7. 什么是 relevance_score

`relevance_score` 是 rerank 模型给出的相关性分数。

它表达：

```text
这个 candidate document 和 query 有多相关。
```

通常是：

```text
越大越相关。
```

但它不是 vector_score。

也不是 keyword_score。

也不是 hybrid_score。

它属于：

```text
rerank_score
```

所以本节给分数解释层补了：

```text
describe_rerank_score()
```

用来明确：

```text
rerank_score 是检索之后的模型相关性分数。
不能和向量分数、关键词分数、hybrid 分数直接比较。
```

### 8. 为什么真实 rerank 要单独配置

Rerank 模型和 LLM、embedding 模型是不同能力。

LLM 负责：

```text
生成回答。
```

Embedding 负责：

```text
把文本变成向量。
```

Rerank 负责：

```text
对候选重新排序。
```

它们可能来自同一个厂商，也可能来自不同厂商。

所以配置应该独立：

```text
RERANK_PROVIDER
RERANK_MODEL
RERANK_BASE_URL
RERANK_API_KEY
RERANK_TIMEOUT_SECONDS
RERANK_MAX_RETRIES
```

不要硬复用 LLM 配置。

虽然本项目允许 `RERANK_API_KEY` 为空时兜底使用已有 LLM/OpenAI key，但这只是便利。

概念上，rerank 是独立能力。

### 9. 为什么自动化测试不能真实调用 rerank 模型

自动化测试必须稳定。

真实外部模型调用会带来：

- 网络不稳定。
- API key 缺失。
- 供应商限流。
- 费用消耗。
- 响应延迟。
- 模型版本变化。
- 返回细节变化。

如果测试依赖真实模型，就会变成：

```text
代码没坏，但测试因为外部服务失败。
```

所以本节测试用：

```text
httpx.MockTransport
```

模拟 provider 响应。

这能测试 adapter 的请求、解析和 fallback，同时不真实联网。

### 10. 什么是 fallback

Fallback 是失败兜底。

真实 rerank 模型可能失败。

比如：

```text
超时
500
429
网络错误
返回格式异常
```

这时系统不能直接崩掉。

一个常见策略是：

```text
退回规则版 rerank。
```

或者：

```text
退回原始检索顺序。
```

本节选择：

```text
退回 RuleBasedReranker。
```

因为项目里已经有它，而且它可测试、稳定、无外部依赖。

## 本节主题系统讲解

### 1. 本节新增配置

本节在：

```text
projects/ai-service/app/core/config.py
```

新增：

```text
rerank_provider
rerank_model
rerank_base_url
rerank_api_key
rerank_timeout_seconds
rerank_max_retries
```

并在：

```text
projects/ai-service/.env.example
```

补充示例：

```text
RERANK_PROVIDER="http-compatible"
RERANK_MODEL="your-rerank-model"
RERANK_BASE_URL=""
RERANK_API_KEY=""
RERANK_TIMEOUT_SECONDS=10
RERANK_MAX_RETRIES=1
```

这里留空 `RERANK_BASE_URL` 和 `RERANK_API_KEY` 是有意的。

意思是：

```text
默认不真实调用。
需要手动验证时再配置。
```

### 2. `HttpReranker` 是什么

本节新增：

```text
HttpReranker
```

它实现了项目里的 `Reranker` 协议。

也就是说，它可以像 `RuleBasedReranker` 一样被调用：

```python
reranker.rerank(query, candidates, top_k=3)
```

不同的是：

```text
RuleBasedReranker 在本地算分。
HttpReranker 调用外部 HTTP rerank 服务。
```

### 3. `HttpReranker` 的请求格式

本节采用一个通用 HTTP rerank 请求形状：

```json
{
  "model": "rerank-demo",
  "query": "refund arrival",
  "documents": [
    "candidate 1",
    "candidate 2"
  ],
  "top_n": 2,
  "return_documents": false
}
```

这个结构和很多 rerank 服务的概念一致：

- `model`：模型名。
- `query`：用户问题。
- `documents`：候选文档。
- `top_n`：返回前几个。
- `return_documents`：是否返回文档正文。

本项目设置：

```text
return_documents = false
```

因为正文我们本地已经有。

返回 index 就够了。

### 4. `HttpReranker` 的响应格式

本节期待响应：

```json
{
  "results": [
    {"index": 1, "relevance_score": 0.93},
    {"index": 0, "relevance_score": 0.41}
  ]
}
```

然后 adapter 会：

```text
用 index 找回原始 RerankCandidate。
用 relevance_score 作为 rerank_score。
构造 RerankedChunk。
```

### 5. 为什么要校验 provider 响应

外部 provider 返回的数据不能盲信。

必须校验：

- `results` 必须是 list。
- 每个 result 必须是 object。
- `index` 必须是整数。
- `index` 不能越界。
- `index` 不能重复。
- `relevance_score` 必须是数字。

如果不校验，可能导致：

- 排名错乱。
- 拿错候选文档。
- 构造异常对象。
- 后续上下文引用错位。

所以本节新增：

```text
_extract_model_rerank_results()
```

专门做响应解析和校验。

### 6. 为什么 provider 结果还要排序

虽然很多 provider 会返回已排序结果，但 adapter 仍然按：

```text
relevance_score desc
index asc
```

重新排序。

这样可以保证本地行为稳定。

如果 provider 返回顺序不稳定，本地仍然得到确定顺序。

### 7. `rerank_with_fallback()` 是什么

本节新增：

```text
rerank_with_fallback()
```

它的逻辑是：

```text
先调用 primary_reranker。
如果成功，返回真实 rerank 结果。
如果失败，调用 fallback_reranker。
```

默认 fallback 是：

```text
RuleBasedReranker
```

返回结构是：

```text
RerankExecutionResult
```

包含：

```text
results
used_fallback
fallback_reason
elapsed_ms
```

这能让调用方知道：

```text
这次到底用了真实模型，还是走了兜底。
```

### 8. 为什么 fallback_reason 只记录错误类型

本节记录：

```text
fallback_reason = type(exc).__name__
```

而不是直接把完整异常信息返回。

原因是：

```text
外部异常里可能包含 URL、内部信息、供应商返回细节。
```

学习项目里先记录错误类型即可。

真实生产项目可以在安全日志里记录更多内部信息，但不应该直接暴露给用户。

### 9. 为什么保留 RuleBasedReranker

接入真实模型后，规则版仍然有价值。

它至少有 4 个作用：

第一，自动化测试稳定。

第二，真实模型失败时 fallback。

第三，本地开发不用消耗 API 费用。

第四，概念学习时可解释。

所以不是接了真实模型就删除 fake/rule-based。

真实项目里经常需要：

```text
real implementation + fake implementation + fallback implementation
```

### 10. 本节如何继承第 7 节成果

第 7 节新增了：

```text
RerankReport
retrieval_score_meaning
lower-is-better 归一化
```

第 8 节的 `HttpReranker` 也支持：

```text
retrieval_score_meaning
```

这表示：

```text
真实模型输出 rerank_score。
但 score_breakdown 里仍然可以正确解释上游 retrieval_score。
```

比如上游是 Milvus L2 distance，仍然可以传：

```python
describe_milvus_score("L2")
```

这样 debug breakdown 不会误把 distance 大的结果当成更好。

### 11. 本节如何继承第 6 节成果

第 6 节新增了：

```text
RetrievalScoreMeaning
```

本节补了：

```text
describe_rerank_score()
```

它说明：

```text
rerank_score 是模型重排序分数。
方向通常是 higher_is_better。
不能和 vector_score / keyword_score / hybrid_score 直接比较。
```

这让分数体系更完整：

```text
vector score
keyword score
hybrid score
rerank score
```

每种分数都有自己的解释边界。

## 本节代码讲解

### 1. 配置字段

新增配置：

```python
rerank_provider: str = Field(default="http-compatible")
rerank_model: str = Field(default="mock-rerank-model")
rerank_base_url: str | None = Field(default=None)
rerank_api_key: str | None = Field(default=None, repr=False)
rerank_timeout_seconds: float = Field(default=10.0, gt=0)
rerank_max_retries: int = Field(default=1, ge=0, le=3)
```

这里 `repr=False` 用于密钥字段，避免对象打印时泄漏 key。

`rerank_max_retries` 限制在 0 到 3。

因为 rerank 是额外精排步骤，不应该无限重试。

### 2. `resolved_rerank_api_key`

新增：

```python
resolved_rerank_api_key
```

它按顺序读取：

```text
rerank_api_key
llm_api_key
openai_api_key
```

这样做是为了开发便利。

但真实项目里更推荐：

```text
RERANK_API_KEY 独立配置。
```

### 3. `HttpReranker.__init__`

构造函数校验：

```text
base_url 不能为空。
model 不能为空。
timeout_seconds 必须大于 0。
max_retries 必须是非负整数。
```

这些校验都属于边界校验。

原因是：

```text
真实 HTTP adapter 不应该带着明显错误配置跑到请求阶段才失败。
```

### 4. `HttpReranker.from_settings()`

这个方法从 Settings 构造 adapter。

如果没有配置：

```text
RERANK_BASE_URL
```

会直接报错。

这很好。

因为默认情况下我们不真实调用。

只有你明确配置了 base_url，才表示你要使用真实 rerank。

### 5. `HttpReranker.rerank()`

主流程：

```text
校验 query
校验 top_k
空 candidates 直接返回 []
发送 HTTP 请求
解析模型结果
构造 RerankedChunk
```

它没有直接返回 provider 原始 JSON。

原因是：

```text
项目内部应该使用稳定领域模型 RerankedChunk。
```

不要让外部 provider JSON 形状污染内部业务代码。

### 6. `_request_rerank()`

这个函数负责 HTTP 请求。

它使用：

```text
httpx.Client
```

并支持：

```text
timeout
Authorization Bearer
MockTransport
max_retries
```

`MockTransport` 很重要。

它让测试可以模拟：

```text
成功响应
500 错误
非法 index
```

而不需要真实访问网络。

### 7. 哪些状态码会重试

本节对这些情况允许重试：

```text
408
429
5xx
```

含义：

```text
408 请求超时
429 限流
5xx 服务端错误
```

这些通常属于临时失败。

但重试次数有限。

因为 rerank 是成本敏感步骤，不能无限重试。

### 8. `_build_reranked_chunks_from_model_results()`

这个函数把 provider 输出转成项目内部结果。

它会：

```text
通过 index 找 candidate。
用 relevance_score 设置 rerank_score。
保留 retrieval_score。
保留 retrieval_sources。
生成 score_breakdown。
生成 matched_terms。
设置 original_rank 和 rerank_rank。
```

这里要注意：

```text
rerank_score 来自真实模型。
score_breakdown 是本地解释信号。
```

这两个不是同一个来源。

### 9. `rerank_with_fallback()`

这个函数用于安全执行。

它不会让调用方自己写 try/except。

而是统一返回：

```text
RerankExecutionResult
```

这样调用方可以看：

```text
used_fallback
fallback_reason
elapsed_ms
```

这对可观测性有用。

### 10. 本节测试重点

本节新增测试主要覆盖：

```text
HttpReranker 会发送正确请求。
HttpReranker 会把 provider index + relevance_score 转成 RerankedChunk。
HttpReranker.from_settings 会读取 rerank 配置。
provider 返回越界 index 会被拒绝。
provider 失败时 rerank_with_fallback 会退回 RuleBasedReranker。
describe_rerank_score() 能解释 rerank_score。
```

这些测试都不真实联网。

它们验证的是：

```text
adapter 边界。
响应解析。
错误处理。
fallback 行为。
```

## 真实项目接入时要注意什么

### 1. provider schema 可能不同

不同厂商的 rerank API 字段可能不同。

常见字段是：

```text
query
documents
top_n / top_k
return_documents
results.index
results.relevance_score
```

但具体路径、鉴权、字段名、限制都可能不同。

所以本节叫：

```text
HttpReranker
```

而不是写死某个厂商。

如果以后你选定具体 provider，可以基于这个 adapter 调整请求格式。

### 2. 文档长度限制

Rerank 模型通常有输入长度限制。

限制可能包括：

- query 长度。
- 单个 document 长度。
- documents 数量。
- 总 token 数。

所以真实接入时要考虑：

```text
chunk 是否过长。
候选数量是否过多。
是否需要截断。
是否要做 context compression。
```

### 3. 成本和延迟

Rerank 会增加额外调用。

如果每次召回 50 个候选再 rerank，成本和延迟都比直接 top_k 检索更高。

所以要评估：

```text
rerank 带来的质量提升是否值得。
```

常见方式是：

```text
用评测集比较 rerank 前后的 Hit Rate、MRR、答案正确率、引用准确率。
```

### 4. 并发和限流

如果用户并发多，rerank provider 可能限流。

所以要考虑：

- timeout。
- retry。
- rate limit。
- circuit breaker。
- fallback。
- cache。

本节只做了最小的 retry 和 fallback。

后面生产化阶段会继续补更完整的保护。

### 5. 安全问题

Rerank 输入是文档 chunk。

这些 chunk 可能包含：

- 用户隐私。
- 内部政策。
- prompt injection 内容。
- 权限受限内容。

所以真实系统里应该先做：

```text
metadata filter
权限过滤
敏感字段控制
```

再把候选发给外部 rerank provider。

否则可能把不该出站的数据发送给第三方。

### 6. 不要把 rerank 当成最终事实

Rerank 只是排序信号。

它不能保证：

```text
最终回答一定正确。
```

后面仍然需要：

- 上下文构造。
- 引用来源校验。
- 回答质量评测。
- bad case 分析。

Rerank 是质量链路中的一环，不是全部。

## 常见误区

### 误区 1：接入真实 rerank 模型就一定提升

不一定。

真实模型可能不适合你的语言、业务、文档风格或 chunk 粒度。

必须用评测验证。

### 误区 2：真实模型可以替代规则版

不应该完全替代。

规则版仍然适合：

- 自动化测试。
- 本地开发。
- provider 失败 fallback。
- 学习和解释。

### 误区 3：自动化测试可以直接调用真实 API

不应该。

自动化测试要稳定、低成本、可重复。

真实 API 调用应该放在手动 smoke 或单独集成验证里。

### 误区 4：rerank_score 可以和 vector_score 直接比较

不能。

rerank_score 是模型对 query + candidate 的后置相关性评分。

vector_score 是向量检索阶段分数。

它们不是同一个体系。

### 误区 5：provider 返回什么就直接信什么

不应该。

必须校验：

```text
index
relevance_score
results 结构
```

否则可能拿错候选或造成上下文错位。

### 误区 6：fallback 只是可有可无

不对。

真实模型是外部依赖。

外部依赖就可能失败。

没有 fallback，RAG 链路稳定性会变差。

## 本节练习

### 练习 1：解释真实 rerank 模型

问题：

```text
真实 rerank 模型通常接收什么输入，返回什么输出？
```

参考答案：

```text
通常接收 query 和一组候选 documents，返回每个候选的相关性排序结果，常见字段包括 index 和 relevance_score。index 用来定位原始候选，relevance_score 表示模型认为该候选和 query 的相关性。
```

### 练习 2：区分 embedding 和 rerank

问题：

```text
Embedding 检索和 rerank 最大区别是什么？
```

参考答案：

```text
Embedding 检索通常把 query 和 document 分别编码成向量，再用相似度检索；rerank 通常直接同时看 query 和 candidate document，判断这一对文本的相关性，所以更精细但更慢更贵。
```

### 练习 3：解释为什么要 index

问题：

```text
Rerank API 为什么常返回 index，而不是完整文档？
```

参考答案：

```text
因为完整候选文档本来就在客户端，返回 index 就能定位输入 documents 里的原始候选，减少响应体体积，也避免重复传输正文。
```

### 练习 4：解释自动化测试边界

问题：

```text
为什么自动化测试不应该真实调用 rerank 模型？
```

参考答案：

```text
因为真实调用依赖网络、API key、供应商状态、限流、费用和模型版本，测试会不稳定。自动化测试应该用 MockTransport 或 fake reranker 固定 adapter 行为。
```

### 练习 5：解释 fallback

问题：

```text
真实 rerank provider 返回 500 时，系统可以怎么处理？
```

参考答案：

```text
可以记录失败原因，然后退回 RuleBasedReranker 或原始检索顺序。本节项目实现的是 rerank_with_fallback，默认失败后退回规则版 rerank。
```

### 练习 6：解释为什么要独立配置

问题：

```text
为什么 RERANK_MODEL / RERANK_BASE_URL 不应该直接复用 LLM_MODEL / LLM_BASE_URL？
```

参考答案：

```text
因为 LLM、embedding、rerank 是不同能力，可能来自不同模型或不同厂商。独立配置可以避免职责混乱，也方便单独切换、限流、计费和排查。
```

### 练习 7：解释响应校验

问题：

```text
如果 provider 返回 index=9，但本地只有 2 个 candidates，为什么要报错？
```

参考答案：

```text
因为 index 越界会导致拿不到对应候选，或者错误关联文档。必须拒绝这种响应，避免上下文错位。
```

### 练习 8：解释 rerank_score

问题：

```text
rerank_score=0.9 和 hybrid_score=0.9 能不能直接比较？
```

参考答案：

```text
不能。rerank_score 是模型在重排序阶段给 query + candidate 的相关性分数，hybrid_score 是本地融合向量和关键词分数后的召回阶段分数。两者不是同一个分数体系。
```

## 自测题

### 自测 1：真实 rerank adapter 的职责是什么？

参考答案：

```text
把本地 query 和候选 candidates 转成 provider 请求，把 provider 返回的 index 和 relevance_score 转成本地 RerankedChunk，并处理错误和 fallback。
```

### 自测 2：Rerank 模型为什么通常更慢？

参考答案：

```text
因为它通常需要同时处理 query 和每个 candidate document 的文本交互，不能像向量检索那样完全依赖提前建好的向量索引。
```

### 自测 3：为什么 rerank 只处理候选集？

参考答案：

```text
因为全量文档数量太大，直接让 rerank 模型对所有 chunk 打分成本和延迟都不可接受。通常先粗召回，再 rerank 精排。
```

### 自测 4：`HttpReranker` 为什么需要 `model`？

参考答案：

```text
因为同一个 provider 可能提供多个 rerank 模型，请求里需要指定具体使用哪个模型。
```

### 自测 5：`HttpReranker` 为什么要支持 `transport`？

参考答案：

```text
为了测试时注入 httpx.MockTransport，模拟 provider 响应，不真实联网。
```

### 自测 6：`RerankExecutionResult.used_fallback` 表示什么？

参考答案：

```text
表示本次是否因为 primary reranker 失败而使用 fallback reranker。
```

### 自测 7：为什么 fallback_reason 不直接暴露完整异常？

参考答案：

```text
完整异常可能包含内部 URL、供应商细节或敏感信息。学习项目先记录错误类型即可，真实项目可以在安全日志中记录更详细内部信息。
```

### 自测 8：真实 rerank 接入后还需要 RerankReport 吗？

参考答案：

```text
需要。真实模型更需要可观测性，RerankReport 可以记录 top_before、top_after、promoted、dropped 和 debug lines，帮助判断模型是否真的改善排序。
```

### 自测 9：rerank_score 是否一定在 0 到 1？

参考答案：

```text
不一定。不同 provider 的分数范围可能不同。很多服务会返回 0 到 1 的 relevance_score，但不能在所有模型之间直接假设可比。
```

### 自测 10：真实 rerank provider 失败时，是否应该直接中断整个 RAG？

参考答案：

```text
不一定。很多场景可以退回规则版 rerank 或原始检索顺序，保证服务可用性。是否中断要看业务要求和安全要求。
```

### 自测 11：接入真实 rerank 模型后下一步该看什么指标？

参考答案：

```text
要看 rerank 前后正确 chunk 排名、Hit Rate@K、MRR、答案正确率、引用准确率、延迟和成本，而不是只看单条样例。
```

### 自测 12：为什么 provider 返回结果要本地重新排序？

参考答案：

```text
为了保证本地行为稳定。即使 provider 返回顺序不稳定，本地也按 relevance_score 降序和 index 升序得到确定结果。
```

## 面试表达

### 1 分钟版本

```text
真实 rerank 模型通常接收 query 和一组候选 documents，返回每个候选的 index 和 relevance_score。它和 embedding 检索不同，embedding 是先独立编码再算向量相似度，rerank 通常会同时看 query 和 candidate 文本，所以排序更精细，但成本和延迟更高。工程上我会把真实 rerank 封装成 adapter，比如 HttpReranker，内部校验 provider 响应，把结果转成项目统一的 RerankedChunk。自动化测试不用真实 API，而是用 MockTransport。真实 provider 失败时，通过 rerank_with_fallback 退回规则版 rerank，保证链路稳定。
```

### 3 分钟版本

```text
在 RAG 里，真实 rerank 模型应该放在召回之后。向量检索、关键词检索或 Hybrid Search 先从知识库里找出一批候选，比如 top 20，然后 rerank 模型对 query 和每个 candidate document 重新打相关性分数，最后选 rerank 后 top 5 进入上下文。

我会把 rerank 接入做成独立 adapter，而不是散落在业务逻辑里。配置上独立使用 RERANK_MODEL、RERANK_BASE_URL、RERANK_API_KEY、timeout 和 retry。请求通常包含 model、query、documents、top_n，响应校验 results 里的 index 和 relevance_score。index 必须能对应本地 candidates，不能越界或重复，relevance_score 必须是数字。解析后统一构造成 RerankedChunk，保留 original_rank、rerank_rank、retrieval_score、rerank_score 和 score_breakdown。

自动化测试不能真实调用外部 rerank API，因为会受网络、密钥、限流、费用和模型版本影响，所以我会用 MockTransport 模拟成功、失败和非法响应。真实 provider 可能超时或返回 5xx，因此还要有 fallback，例如退回 RuleBasedReranker。接入后不能只看单条效果，要用评测集比较 rerank 前后的正确 chunk 排名、MRR、Hit Rate、答案正确率、引用准确率、延迟和成本。
```

## 本节小结

本节真正要掌握的是：

```text
真实 rerank 模型是候选精排工具。
它更精细，但更慢更贵。
它应该被封装成 adapter。
它的自动化测试必须 fake。
它失败时必须能 fallback。
它的分数不能和 retrieval_score 混用。
```

本节项目补齐了：

```text
RERANK_* 配置
HttpReranker
RerankModelError
RerankExecutionResult
rerank_with_fallback()
describe_rerank_score()
真实 rerank adapter 的 MockTransport 测试
```

下一节继续：

```text
阶段 9 第 9 节：引用来源校验：回答必须能对应原文
```

下一节会开始处理生成阶段的质量问题：

```text
即使检索和 rerank 都找到了资料，模型生成的回答是否真的来自这些资料？
```

## 参考资料

- Cohere Rerank API：https://docs.cohere.com/reference/rerank
- Jina AI Reranker：https://jina.ai/reranker/
- Voyage AI Rerankers：https://docs.voyageai.com/docs/reranker
- Voyage AI Reranker API：https://docs.voyageai.com/reference/reranker-api
