# 阶段 9 第 19 节：RAG 可观测性：记录 query、召回、rerank、引用、耗时

## 本节定位

本节学习 RAG 可观测性。

它接在第 18 节缓存、超时、降级之后：上一节解决“慢了或失败了怎么保护系统”，本节解决“慢在哪里、错在哪里、为什么降级、该看什么证据”。

## 本节学习目标

学完本节，你要能说清楚：

- 日志、指标、trace 的区别。
- RAG 链路为什么需要专门的可观测性。
- query、召回、rerank、引用、耗时分别要记录什么。
- 为什么不能把用户原始问题和 chunk 原文随便写进日志。
- 什么是结构化观测事件。
- warning codes 为什么比只写一句日志更利于排查。

## 本节新增和修改

新增：

```text
projects/ai-service/app/rag/observability.py
projects/ai-service/tests/test_rag_observability.py
notes/stage9-19-rag-observability-query-retrieval-rerank-citation-timing.md
```

修改：

```text
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

## 一句话先讲透

RAG 可观测性的本质是：

```text
把一次 RAG 问答从“黑盒回答”变成“可追踪、可排查、可统计、可复盘”的结构化证据链。
```

## 基础知识铺垫

### 1. 什么是可观测性

可观测性不是简单“打印日志”。

它指的是系统运行后，开发者可以通过外部看到足够多的信号，从而判断系统内部发生了什么。

常见问题包括：

```text
这次请求有没有进入 RAG？
原始问题是什么类型？
query 有没有改写？
召回了几个 chunk？
最相关的 chunk 是哪个？
rerank 有没有改变排序？
回答引用是不是有效？
哪一步最慢？
有没有超时？
有没有降级？
是不是权限过滤导致没召回？
```

如果系统没有可观测性，RAG 就会变成黑盒：

```text
用户说答错了，开发者只能猜。
用户说很慢，开发者只能猜。
用户说引用不对，开发者只能猜。
模型偶尔胡说，开发者还是只能猜。
```

真实项目里，不能靠猜。

### 2. 日志、指标、trace 的区别

这三个词经常一起出现，但它们不是一回事。

日志是事件记录。

例如：

```text
trace_id=abc query_hash=xxx retrieved=5 top_chunk=refund_chunk_0001 elapsed_ms=860
```

它适合回答：

```text
某一次请求发生了什么？
这一次请求为什么没有召回？
这一次请求为什么 citation invalid？
```

指标是聚合数值。

例如：

```text
rag_retrieval_latency_p95 = 900ms
rag_no_context_rate = 12%
rag_citation_invalid_count = 37
rag_rerank_fallback_rate = 4%
```

它适合回答：

```text
最近整体变慢了吗？
某个版本上线后 no_context 是否升高？
citation invalid 是否越来越多？
rerank provider 是否经常失败？
```

trace 是调用链路。

例如：

```text
HTTP request
-> query intent
-> query rewrite
-> embedding
-> vector store
-> rerank
-> generation
-> citation verification
```

它适合回答：

```text
一次请求经过了哪些阶段？
每个阶段耗时多少？
哪个 span 失败了？
跨 Python 服务、Java 服务、向量库、模型调用怎么串起来？
```

一句话区分：

```text
日志看单次事件。
指标看整体趋势。
trace 看完整链路。
```

### 3. 为什么 RAG 比普通接口更需要可观测性

普通后端接口的结果通常更确定：

```text
查订单接口：订单存在就返回，不存在就报错。
创建工单接口：参数合法就写库，不合法就拒绝。
```

RAG 的结果更复杂：

```text
检索可能漏召回。
检索可能召回噪声。
rerank 可能把正确资料排后。
上下文压缩可能删掉关键句。
模型可能没有用好上下文。
引用可能指向错误 chunk。
权限过滤可能把用户能看的资料过滤掉。
prompt injection 可能污染上下文。
```

如果没有中间过程记录，最终只看到：

```text
答案错了。
```

但你不知道错在：

```text
query。
retrieval。
ranking。
compression。
generation。
citation。
security。
permission。
performance。
```

所以阶段 9 前面学的 bad case 分析、参数调优、性能保护，都依赖本节的可观测证据。

### 4. RAG 链路应该记录哪些 query 信息

query 是 RAG 的起点。

query 记录不清楚，后面很难排查。

应该记录：

```text
trace_id。
query_hash。
query_preview。
rewritten_query_hash。
rewritten_query_preview。
expanded_query_count。
expanded_query_hashes。
```

为什么要记录 hash？

因为 hash 能帮助你识别“是不是同一个问题”，又不直接暴露完整原文。

例如：

```text
原始问题：我的手机号 13812345678，退款多久到账？
query_hash：一串 sha256。
query_preview：我的手机号 [REDACTED_PHONE]，退款多久到账？
```

这样既能排查，又减少泄露风险。

### 5. 为什么不能随便记录完整 query

用户问题可能包含敏感信息：

```text
手机号。
邮箱。
身份证。
订单号。
地址。
API Key。
内部业务编号。
客户投诉内容。
```

如果把完整 query 写到日志里，日志系统就会变成新的敏感数据仓库。

真实公司里，日志经常会被：

```text
开发人员查看。
测试人员查看。
运维平台采集。
第三方 APM 平台存储。
长时间归档。
导出给排查人员。
```

所以日志不是绝对安全区。

本项目用脱敏预览和 hash，是为了建立正确习惯：

```text
能定位问题，但尽量不泄露原文。
```

### 6. RAG 链路应该记录哪些召回信息

召回是 RAG 的关键证据。

应该记录：

```text
requested_top_k：这次请求想要召回几个。
returned_count：实际返回几个。
observed_count：日志里记录几个。
top_chunk_id：第一名 chunk。
top_score：第一名分数。
source_counts：召回来源分布。
chunks：每个 chunk 的 rank、chunk_id、source、title、section、score、content_hash、content_chars。
```

注意：这里没有记录 chunk 原文。

为什么？

因为 chunk content 可能包含内部知识、客户信息、权限数据。

更安全的做法是记录：

```text
chunk_id。
source。
section。
score。
content_hash。
content_chars。
```

排查时先看结构化信息。如果确实需要看原文，再通过权限受控的后台或本地数据去查。

### 7. 召回记录能排查什么问题

召回记录可以排查：

```text
没有召回任何资料。
召回数量少于 top_k。
top chunk 是否明显不相关。
召回是不是集中在错误 source。
score 是否整体偏低。
同一个 source 是否重复过多。
metadata filter 是否过滤过严。
```

例如：

```text
requested_top_k = 5
returned_count = 1
```

这说明系统本来想拿 5 条资料，但只拿到 1 条。

可能原因：

```text
知识库覆盖不足。
score_threshold 太高。
metadata filter 太严。
query 改写方向不对。
向量库数据没入全。
```

这就能接上第 16 节 bad case 分析和第 17 节参数调优。

### 8. RAG 链路应该记录哪些 rerank 信息

rerank 负责把召回候选重新排序。

应该记录：

```text
candidate_count：进入 rerank 的候选数量。
returned_count：rerank 后返回数量。
top_before_chunk_id：rerank 前第一名。
top_after_chunk_id：rerank 后第一名。
moved_count：排序发生变化的数量。
used_fallback：是否使用 fallback reranker。
fallback_reason：为什么 fallback。
elapsed_ms：rerank 耗时。
chunk_id、original_rank、rerank_rank、retrieval_score、rerank_score。
```

这些信息能回答：

```text
rerank 有没有发挥作用？
rerank 是不是把好资料提到前面？
真实 rerank 模型是不是失败了？
fallback 是否频繁发生？
rerank 是否太慢？
```

如果 `top_before_chunk_id` 和 `top_after_chunk_id` 总是不变，不代表 rerank 没用，但至少说明它对第一名影响不大。

如果 `used_fallback` 经常为 true，说明真实 rerank provider 可能不稳定。

### 9. RAG 链路应该记录哪些引用信息

引用是 RAG 可信度的重要边界。

应该记录：

```text
answer_status。
is_valid。
retrieved_chunk_count。
checked_citation_count。
cited_chunk_count。
missing_citation_count。
answer_support_score。
blocking_finding_count。
warning_finding_count。
finding_codes。
```

这些信息能回答：

```text
回答有没有引用。
引用是否指向真实召回 chunk。
引用数量是否异常。
是否出现 fake chunk_id。
答案和引用文本支撑度是否过低。
引用问题是 blocking 还是 warning。
```

注意：这里记录的是引用校验摘要，不是完整回答全文。

完整回答也可能含有用户信息或业务敏感内容，不能无脑写进日志。

### 10. RAG 链路应该记录哪些耗时信息

耗时要按阶段记录。

常见 stage：

```text
embedding。
vector_store。
rerank。
generation。
security。
```

每个 stage 至少记录：

```text
stage。
elapsed_ms。
timeout_seconds。
status。
```

status 可以是：

```text
ok。
near_timeout。
timed_out。
```

这样可以看出：

```text
这次是正常慢，还是接近超时。
哪个 stage 已经超时。
是否需要触发降级。
性能优化应该先看哪个模块。
```

### 11. 什么是 warning code

warning code 是机器可读的告警原因。

比如本节新增：

```text
RAG_OBS_NO_RETRIEVED_CHUNKS
RAG_OBS_RETRIEVED_LESS_THAN_TOP_K
RAG_OBS_RERANK_USED_FALLBACK
RAG_OBS_CITATION_INVALID
RAG_OBS_NEAR_TIMEOUT
RAG_OBS_TIMED_OUT
```

为什么不用一句中文日志就够了？

因为中文日志适合人看，但不适合系统稳定统计。

warning code 适合：

```text
日志过滤。
指标聚合。
告警规则。
bad case 聚类。
看板统计。
自动化评测归因。
```

例如你可以统计：

```text
最近 24 小时 RAG_OBS_CITATION_INVALID 出现了多少次。
某次版本上线后 RAG_OBS_NO_RETRIEVED_CHUNKS 是否升高。
rerank fallback 是否集中在某个 provider。
```

### 12. 结构化日志为什么比普通字符串更重要

普通日志：

```text
RAG 查询很慢，召回了几个资料，引用好像不太对。
```

这种日志很难被机器稳定分析。

结构化日志：

```json
{
  "trace_id": "trace-rag-001",
  "retrieval": {
    "requested_top_k": 5,
    "returned_count": 1,
    "top_chunk_id": "refund_chunk_0001"
  },
  "warning_codes": ["RAG_OBS_RETRIEVED_LESS_THAN_TOP_K"]
}
```

这种日志可以被日志平台、监控系统和评测脚本直接使用。

本节新增的 `build_safe_rag_log_payload()` 就是在做这个事情。

### 13. 可观测性和隐私安全的边界

可观测性不是记录越多越好。

错误想法：

```text
为了排查方便，把用户 query、chunk 原文、模型完整回答、所有 metadata 都打到日志里。
```

这样短期排查方便，长期会造成数据风险。

更合理的策略：

```text
默认日志记录 hash、id、score、rank、count、status、warning code。
必要时记录脱敏 preview。
敏感原文只在权限受控的排查工具中查看。
日志保留时间要有限。
日志访问要有权限。
高敏字段要脱敏或不记录。
```

你要记住：

```text
日志系统不是数据库，更不是权限系统。
```

### 14. 可观测性和评测的关系

第 13 到第 17 节学了评测、指标、bad case 和调优。

这些能力都需要证据。

可观测性提供的证据包括：

```text
query_hash：同类问题聚合。
retrieved chunks：召回证据。
rerank summary：排序证据。
citation summary：引用证据。
timings：性能证据。
warning codes：快速归因线索。
```

没有这些记录，评测只能离线做。

有了这些记录，真实线上请求也可以沉淀成：

```text
bad case 样本。
评测集候选。
调参依据。
性能优化依据。
安全审计证据。
```

## 本节主题系统讲解

### 1. 第 19 节在阶段 9 里的位置

阶段 9 到这里已经学了很多质量优化能力：

```text
Query Rewrite
Multi Query
Intent Classification
Hybrid Search
Score Interpretation
Rerank
Citation Verification
Context Compression
Metadata Filter
Prompt Injection Defense
Evaluation Dataset
Retrieval Metrics
Answer Quality Evaluation
Bad Case Analysis
Parameter Tuning
Cache/Timeout/Degradation
```

这些能力如果没有可观测性，就很难在线上发挥价值。

例如：

```text
你学会了 bad case 分析，但线上没有记录 retrieval 和 citation，分析不了。
你学会了参数调优，但线上没有记录 score 和 top_k，调不了。
你学会了性能保护，但线上没有记录 stage timing，查不了。
```

所以本节的作用是把前面所有能力串成证据链。

### 2. 本节新增的可观测事件是什么

本节新增 `RagObservabilityEvent`。

它不是业务响应。

它是系统内部用于排查的一条观测事件。

可以理解为：

```text
一次 RAG 请求的结构化快照。
```

它包含：

```text
trace_id。
query observation。
retrieval observation。
rerank observation。
citation observation。
timing observation。
warning_codes。
```

这条事件未来可以输出到：

```text
结构化日志。
本地调试输出。
评测样本生成工具。
Tracing span attributes。
监控指标聚合任务。
```

本节先做学习版结构，不接入外部平台。

### 3. query observation 的边界

query observation 负责记录：

```text
query_hash。
query_preview。
rewritten_query_hash。
rewritten_query_preview。
expanded_query_count。
expanded_query_hashes。
```

它不负责做 query rewrite，也不负责判断 intent。

它只负责：

```text
把已经发生的 query 处理结果记录下来。
```

这样分层比较清楚：

```text
query_rewrite.py：负责改写。
multi_query.py：负责扩展。
query_intent.py：负责分类。
observability.py：负责记录这些步骤留下的证据。
```

### 4. retrieval observation 的边界

retrieval observation 负责记录召回快照。

它记录：

```text
top_k。
returned_count。
source_counts。
chunk_id。
rank。
score。
source/title/section。
content_hash。
content_chars。
```

它不记录 chunk 原文。

这点非常关键。

因为生产日志中的 chunk 原文可能造成：

```text
内部资料泄露。
客户信息泄露。
权限绕过。
日志体积过大。
日志成本上升。
```

如果排查时需要看原文，可以通过 chunk_id 回到知识库里查，而不是直接把原文写进日志。

### 5. rerank observation 的边界

rerank observation 负责记录排序变化。

它记录：

```text
candidate_count。
returned_count。
top_before_chunk_id。
top_after_chunk_id。
moved_count。
used_fallback。
fallback_reason。
elapsed_ms。
每个 reranked chunk 的 original_rank、rerank_rank、retrieval_score、rerank_score。
```

它不负责重新计算 rerank。

它只是把 `rerank.py` 已经产生的 `RerankReport` 和 `RerankExecutionResult` 收集起来。

这能排查：

```text
排序是否明显变化。
真实 rerank 是否失败。
fallback 是否被触发。
rerank 后第一名是否变了。
```

### 6. citation observation 的边界

citation observation 负责记录引用校验摘要。

它来自 `CitationVerificationReport`。

记录内容包括：

```text
answer_status。
is_valid。
checked_citation_count。
missing_citation_count。
answer_support_score。
blocking_finding_count。
warning_finding_count。
finding_codes。
```

它不重新做引用校验。

引用校验仍然是 `citation_verification.py` 的职责。

这种设计避免了职责混乱：

```text
citation_verification.py：判断引用是否有效。
observability.py：记录引用校验结果。
```

### 7. timing observation 的边界

timing observation 负责记录阶段耗时。

它来自第 18 节的 `RagOperationTiming`。

记录：

```text
stage。
elapsed_ms。
timeout_seconds。
status。
```

这个设计让第 18 节和第 19 节衔接起来：

```text
第 18 节判断 ok/near_timeout/timed_out。
第 19 节把这些判断记录进观测事件。
```

### 8. warning codes 的生成逻辑

本节根据事件内容生成 warning codes。

例如：

```text
没有召回 chunks -> RAG_OBS_NO_RETRIEVED_CHUNKS
召回数量少于 top_k -> RAG_OBS_RETRIEVED_LESS_THAN_TOP_K
rerank fallback -> RAG_OBS_RERANK_USED_FALLBACK
引用无效 -> RAG_OBS_CITATION_INVALID
接近超时 -> RAG_OBS_NEAR_TIMEOUT
已经超时 -> RAG_OBS_TIMED_OUT
```

warning code 是轻量诊断线索，不等于最终结论。

例如：

```text
RAG_OBS_RETRIEVED_LESS_THAN_TOP_K
```

可能代表知识库资料不足，也可能代表 filter 太严，也可能代表 score_threshold 太高。

它只是告诉你：

```text
这个请求值得进一步排查召回环节。
```

### 9. safe log payload 的作用

`build_safe_rag_log_payload()` 用来生成更适合写日志的结构。

它的重点是：

```text
保留排查字段。
排除不必要的明细。
不写 chunk 原文。
query 只保留 hash 和脱敏 preview。
额外输出 timed_out_stages 和 near_timeout_stages。
```

这个函数体现了一个工程原则：

```text
内部事件可以结构丰富，真正写日志时还要再过一层安全整理。
```

### 10. 本节暂时不做什么

本节不接入 OpenTelemetry。

原因：

```text
现在先学清楚 RAG 应该记录什么，再学具体平台怎么接。
```

本节不接入 Prometheus。

原因：

```text
指标聚合是下一步工程化工作，本节先把事件结构建立起来。
```

本节不真实上传日志到外部平台。

原因：

```text
学习阶段不应该把用户本地数据发送到第三方系统。
```

本节不改完整 RAG pipeline。

原因：

```text
当前项目的 RAG 进阶模块还在学习组件阶段，本节先提供可复用观测模型。
```

## 本节代码讲解

### 1. `RagObservabilityEvent`

`RagObservabilityEvent` 是本节核心模型。

它聚合：

```text
trace_id
query
retrieval
rerank
citation
timings
total_elapsed_ms
warning_codes
```

你可以把它理解为一次 RAG 请求的“排查快照”。

### 2. `build_rag_observability_event()`

这个函数是本节核心入口。

它接收：

```text
user_query
retrieved_chunks
requested_top_k
rewritten_query
expanded_queries
rerank_report
rerank_execution
citation_report
timings
```

然后统一生成 `RagObservabilityEvent`。

它的重点不是执行 RAG，而是收集证据。

### 3. query 脱敏和 hash

代码里对 query 做了三件事：

```text
生成 sha256 hash。
生成脱敏 preview。
记录 expanded query 的 hash。
```

当前脱敏规则覆盖：

```text
邮箱。
中国大陆手机号。
常见 sk-/ak-/api- 开头的密钥样式。
```

这不是完整 DLP 系统，但足够让你理解日志脱敏的基本思想。

### 4. retrieved chunk 观测

代码记录：

```text
rank
chunk_id
source
title
section
retrieval_score
content_hash
content_chars
```

没有记录：

```text
content 原文。
```

这是本节最重要的安全边界之一。

### 5. `build_safe_rag_log_payload()`

这个函数把事件转成适合日志系统的 dict。

它额外整理：

```text
timed_out_stages。
near_timeout_stages。
```

这样日志平台可以更容易过滤：

```text
找出所有 generation timed_out 的请求。
找出所有 vector_store near_timeout 的请求。
```

### 6. 本节测试重点

本节测试只关注核心行为：

```text
query 脱敏后不出现手机号。
chunk 原文不进入安全日志。
召回数量少于 top_k 会有 warning。
near_timeout/timed_out 会进入 payload。
rerank fallback 和 citation invalid 会进入 warning codes。
```

这些测试不需要真实大模型、Qdrant、Milvus 或外部日志平台。

## 常见误区

### 误区 1：可观测性就是多打日志

不是。

多打日志可能只会增加噪声和泄露风险。

好的可观测性要结构化、可查询、可聚合、可追踪。

### 误区 2：为了排查方便，日志里记录完整 chunk 原文

这很危险。

chunk 可能包含内部资料、权限数据或客户信息。

默认日志应该记录 chunk_id、source、score、hash，而不是原文。

### 误区 3：只记录最终答案就够了

不够。

RAG 答错时，最终答案只能说明结果错了，不能说明为什么错。

你还需要 query、召回、排序、引用和耗时证据。

### 误区 4：warning code 就是最终结论

不是。

warning code 是排查线索。

例如没有召回可能是知识库缺资料，也可能是 filter 太严，也可能是 query 改写失败。

### 误区 5：日志里没有用户隐私就一定安全

不一定。

业务内部资料、权限范围、source 名称、chunk_id、错误码、trace_id 也可能有安全含义。

真实项目还要考虑日志访问权限和保留周期。

### 误区 6：可观测性可以等上线后再补

不建议。

没有可观测性，上线后出现问题会很难排查。

RAG 尤其应该从开发阶段就设计观测字段。

## 本节练习

### 练习 1：为什么 RAG 日志不建议直接记录 chunk 原文？

答案：

因为 chunk 原文可能包含内部知识、客户信息、权限范围内的数据或敏感业务内容。日志系统通常会被多人查看、长期保存、发送到外部平台，如果直接记录原文，可能造成数据泄露。更好的方式是记录 chunk_id、source、section、score、content_hash 和 content_chars，需要看原文时再通过受控权限去查。

### 练习 2：`query_hash` 有什么作用？

答案：

`query_hash` 可以帮助系统识别相同或重复 query，同时避免直接暴露用户原始问题。它适合用于日志聚合、缓存排查、bad case 分组和评测样本归类。

### 练习 3：如果一次请求有 `RAG_OBS_RETRIEVED_LESS_THAN_TOP_K`，一定说明知识库资料不足吗？

答案：

不一定。它只说明实际召回数量少于请求的 top_k。可能原因包括知识库资料不足、metadata filter 太严、score_threshold 太高、query 改写不合适、向量库数据没有入全等。

### 练习 4：为什么 rerank 要记录 `top_before_chunk_id` 和 `top_after_chunk_id`？

答案：

因为这两个字段能看出 rerank 是否改变了第一名结果。如果 rerank 后第一名变了，就需要判断它是不是把更相关的资料提上来了；如果经常不变，也可以进一步评估 rerank 在当前场景中的实际价值。

### 练习 5：为什么 citation observation 不直接重新校验引用？

答案：

因为引用校验应该由 `citation_verification.py` 负责，observability 只负责记录校验结果。这样职责更清晰：一个模块负责判断，一个模块负责观察和记录。

## 自测题

### 自测 1：日志、指标、trace 分别适合回答什么问题？

答案：

日志适合看单次请求发生了什么。指标适合看整体趋势和聚合结果。trace 适合看一次请求经过哪些阶段、每个阶段耗时多少、失败发生在哪个 span。

### 自测 2：RAG 可观测性至少应该覆盖哪五类信息？

答案：

query、召回、rerank、引用、耗时。

更完整一点还可以包括权限过滤、安全检查、缓存命中、降级模式、成本和模型 token 使用量。

### 自测 3：为什么安全日志里可以记录 `content_hash`，但不建议记录 `content`？

答案：

`content_hash` 可以帮助判断内容是否相同，便于排查和去重，但不会直接暴露原文。`content` 原文可能包含敏感信息，直接写日志风险更高。

### 自测 4：`RAG_OBS_CITATION_INVALID` 出现时，下一步应该看什么？

答案：

应该看 citation verification report 的 finding codes、missing_citation_count、checked_citation_count、cited_chunk_count 和 answer_support_score，再结合 retrieved chunks 判断是 fake chunk_id、source_index 错误、metadata 不一致，还是答案与引用支撑度低。

### 自测 5：为什么本节没有直接接入 OpenTelemetry 或 Prometheus？

答案：

因为本节重点是先学清楚 RAG 应该记录哪些信息、这些信息有什么边界和用途。OpenTelemetry、Prometheus 是具体平台和工程接入方式，应该在理解观测字段后再接。

## 本节小结

本节你学到的是：

```text
RAG 可观测性不是多打日志，而是建立结构化证据链。
query 要 hash 和脱敏预览。
retrieval 要记录 rank、chunk_id、source、score，但不直接记录 chunk 原文。
rerank 要记录排序变化和 fallback。
citation 要记录校验摘要和 finding codes。
timing 要记录每个 stage 的耗时和状态。
warning codes 用来快速定位排查方向。
```

到这里，阶段 9 的 RAG 已经具备：

```text
质量优化。
安全防护。
评测分析。
参数调优。
性能保护。
可观测证据。
```

下一节进入 RAG 数据更新，学习知识库文档变化后，如何增量入库、删除和重新索引。
