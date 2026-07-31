# 阶段 9 第 16 节：Bad Case 分析：怎么定位 RAG 答错的原因

## 本节定位

本节学习 RAG bad case 分析。

它接在第 14 节检索指标和第 15 节回答质量评测后面：前两节已经能发现“资料有没有找对”和“回答有没有答对”，本节要学习发现问题之后，怎么判断错在哪一层、先查哪里、怎么修。

## 本节学习目标

学完本节，你要能说清楚：

- 什么是 RAG bad case。
- 为什么不能一看到答错就说“模型不行”。
- 怎么把 RAG 错误分到数据、检索、排序、生成、引用、拒答、权限、安全等层。
- 怎么根据检索指标和回答质量 finding 做初步归因。
- 一份 bad case 分析报告应该包含什么。
- 为什么参数调优必须基于 bad case，而不是凭感觉调。

## 本节新增和修改

修改：

```text
projects/ai-service/app/rag/evaluation.py
projects/ai-service/tests/test_rag_evaluation.py
projects/ai-service/app/rag/README.md
projects/ai-service/data/rag_eval/README.md
docs/learning-progress.md
```

新增：

```text
notes/stage9-16-rag-bad-case-analysis.md
```

## 一句话先讲透

RAG bad case 分析的本质是：

```text
把“这个问题答错了”继续拆成“哪一层先出错、证据是什么、应该先改哪里”。
```

不做 bad case 分析，RAG 优化很容易变成乱调参数。

## 基础知识铺垫

### 1. 什么是 bad case

`bad case` 可以理解成：

```text
系统在某个具体样本上的表现不符合预期。
```

在 RAG 里，bad case 不一定只是“回答错了”。

它可能是：

```text
正确资料没有被检索出来。
正确资料被检索出来了，但排得太靠后。
检索结果里噪声太多。
回答漏了关键答案要点。
回答引用了错误来源。
回答引用了 forbidden source。
没有资料时模型编了答案。
无权限时系统没有拒答。
提示注入风险没有阻断。
```

所以 RAG bad case 是一整条链路里的问题，不是单点问题。

### 2. 为什么不能直接说“模型不行”

很多人看到 RAG 答错，第一反应是：

```text
这个模型不行。
```

这往往太粗糙。

因为 RAG 答错可能发生在模型之前。

比如用户问：

```text
质量问题退货邮费谁出？
```

如果检索只找到了：

```text
商品质量问题段落。
```

但没有找到：

```text
运费处理段落。
```

模型就算再强，也很难稳定回答“运费由谁承担”。

这时主要问题不是模型，而是：

```text
检索召回不足。
```

再比如正确资料找到了，但排在第 8，而系统只把 Top-3 给模型。

这时问题可能是：

```text
排序或 top_k 设置问题。
```

再比如资料找对了，模型仍然漏了一个条件。

这时问题才更像：

```text
生成提示词、上下文组织或模型输出问题。
```

所以 bad case 分析的第一原则是：

```text
先分层，再归因，不要直接甩给模型。
```

### 3. RAG 错误要按链路分层

一个典型 RAG 链路可以分成：

```text
数据层
查询理解层
检索层
排序层
过滤和权限层
上下文构造层
生成层
引用层
拒答层
安全层
评测层
```

本节代码里先落地这些常用归因层：

```text
retrieval：检索召回问题。
ranking：排序问题。
generation：生成问题。
citation：引用问题。
refusal：拒答问题。
access_control：权限和禁用来源问题。
security：安全阻断问题。
data / evaluation / unknown：保留给后续扩展。
```

这些层不是为了分类好看。

它们的价值是：

```text
不同层对应不同排查方向和修复手段。
```

### 4. 数据层问题是什么

数据层问题指知识库本身就有问题。

常见情况：

```text
知识库没有这条资料。
资料过期。
资料冲突。
标题或 metadata 写错。
文档结构混乱。
同一事实分散在多个文档，缺少清晰章节。
```

比如用户问：

```text
会员积分怎么兑换？
```

如果知识库根本没有会员积分资料，那么系统正确行为应该是 `no_context`。

这不是检索器差。

这是数据覆盖不足。

修复方式也不是调 top_k，而是：

```text
补充知识文档。
修正文档结构。
补齐 metadata。
重新入库。
```

### 5. 检索层问题是什么

检索层问题指：

```text
应该找到的资料没有进入候选结果。
```

第 14 节里，最明显的信号是：

```text
Recall@K = 0
```

或者：

```text
Recall@K < 1
```

比如期望 chunk 是：

```text
refund_return_policy_chunk_0005
```

但 Top-3 全是：

```text
order_shipping_policy_chunk_0002
account_security_faq_chunk_0001
refund_return_policy_chunk_0002
```

说明真正需要的运费处理 chunk 没被找出来。

可能原因包括：

```text
query rewrite 没改好。
embedding 模型不适合业务文本。
chunk 切分太碎或太大。
metadata filter 过严。
score_threshold 过高。
top_k 太小。
向量库数据没更新。
```

### 6. 排序层问题是什么

排序层问题指：

```text
正确资料找到了，但排得不够靠前。
```

比如 Top-5 里：

```text
1. 噪声资料
2. 噪声资料
3. 正确资料
4. 噪声资料
5. 噪声资料
```

Hit@5 是 1。

Recall@5 也可能是 1。

但 MRR 不高，因为第一个正确结果排在第 3。

如果系统只取 Top-2 给模型，正确资料还是进不去。

排序问题常见修复方向：

```text
优化 rerank。
调整 hybrid search 权重。
检查分数归一化。
检查 query rewrite 是否引入噪声。
调整 top_k 和 rerank_top_n。
```

### 7. 生成层问题是什么

生成层问题指：

```text
资料找到了，但最终回答没有正确使用资料。
```

第 15 节里常见 finding 是：

```text
RAG_ANSWER_POINT_MISSING
```

比如期望答案要点有两条：

```text
质量问题或商家原因退货时，运费通常由商家承担。
用户个人原因退货时，运费通常由用户承担。
```

实际回答只说了第一条。

这就是回答不完整。

可能原因包括：

```text
prompt 没要求覆盖条件。
上下文太长，模型忽略部分内容。
上下文压缩丢掉关键句。
模型输出格式不稳定。
答案要点评测规则过于死板。
```

生成层问题不一定靠换模型解决。

经常可以先改：

```text
prompt。
上下文排序。
上下文压缩策略。
回答结构。
```

### 8. 引用层问题是什么

引用层问题指：

```text
回答的引用来源不符合预期。
```

常见 finding：

```text
RAG_ANSWER_EXPECTED_SOURCE_MISSING
RAG_ANSWER_UNEXPECTED_SOURCE
RAG_ANSWER_CITATION_REQUIRED_BUT_MISSING
```

比如用户问退货运费，期望引用：

```text
refund-return-policy.md
```

实际引用：

```text
order-shipping-policy.md
```

这说明回答和引用不一致。

可能原因包括：

```text
检索结果混入噪声。
引用构造使用了错误 chunk。
上下文顺序和 citation source_index 对不上。
模型回答来自一个 chunk，但后端引用了另一个 chunk。
```

引用层问题非常重要，因为企业 RAG 需要可追溯和可审计。

### 9. 拒答层问题是什么

拒答层问题指：

```text
系统该拒答时没有拒答，或者拒答原因不对。
```

常见场景：

```text
无资料时应该 no_context。
问题不清楚时应该 clarify。
无权限时应该 access_denied。
安全风险时应该 security_block。
```

如果期望是：

```text
no_context
```

实际却回答了一个看似合理的答案，就是拒答失败。

如果期望是：

```text
security_block
```

实际只返回：

```text
NO_CONTEXT
```

也有问题。

因为安全阻断被误判成无资料，会掩盖真实风险。

### 10. 权限层问题是什么

权限层问题指：

```text
无权限资料进入了检索或回答链路。
```

第 15 节里一个严重 finding 是：

```text
RAG_ANSWER_FORBIDDEN_SOURCE_USED
```

比如普通客服不能看：

```text
internal-compensation-policy.md
```

但最终回答引用了它。

这是权限问题，不是普通回答质量问题。

修复方向应该先看：

```text
RagAccessScope。
metadata filter。
tenant_id。
permission_group。
visibility。
status。
forbidden_sources。
```

### 11. 安全层问题是什么

安全层问题指：

```text
提示注入、工具诱导、泄露系统提示词等风险没有被正确阻断。
```

比如评测样本期望：

```text
security_block
refusal_reason_codes:
  - PROMPT_INJECTION
```

实际却回答：

```text
可以照做。
```

这是安全层问题。

它的严重程度通常高于普通回答不完整。

修复方向包括：

```text
检查 prompt injection 规则。
检查 metadata 扫描。
检查 blocking severity。
检查工具调用边界。
检查安全 finding 是否在生成前被执行。
```

### 12. 评测层问题是什么

有时候不是系统错，而是评测样本或评测规则写得不好。

比如：

```text
answer_points 写得过于死板，模型同义表达被误判。
expected_chunk_ids 因为重新切分已经变化。
expected_sources 写错。
样本没有写清楚权限上下文。
```

这叫评测层问题。

它提醒我们：

```text
bad case 分析时也要怀疑评测标准本身。
```

不要把所有失败都直接当成系统 bug。

## 本节主题系统讲解

### 1. 本节在阶段 9 里的位置

阶段 9 前面几节建立了很多能力：

```text
检索增强。
排序增强。
引用校验。
上下文压缩。
权限过滤。
安全防护。
评测集。
检索指标。
回答质量评测。
```

第 16 节把这些结果串起来。

它不是重新计算指标。

它是做：

```text
归因。
```

也就是：

```text
根据已有评测结果，推断应该先查哪一层。
```

### 2. 从检索指标到归因

检索指标可以提供这些信号：

```text
Recall@K = 0
Recall@K < 1
first_relevant_rank > 1
Precision@K 很低
no_context 样本返回了检索结果
```

这些信号可以初步映射：

```text
Recall@K = 0 -> retrieval
Recall@K < 1 -> retrieval
first_relevant_rank > 1 -> ranking
Precision@K 低 -> retrieval noise
no_context 返回结果 -> retrieval / no-context boundary
```

注意这只是初步归因。

比如 Recall@K = 0 可能是检索问题，也可能是：

```text
数据根本不存在。
metadata filter 过滤错了。
expected_chunk_id 写错了。
```

所以 bad case 分析给的是“先查方向”，不是最终判决。

### 3. 从回答质量 finding 到归因

回答质量 finding 可以提供这些信号：

```text
RAG_ANSWER_POINT_MISSING
RAG_ANSWER_EXPECTED_SOURCE_MISSING
RAG_ANSWER_FORBIDDEN_SOURCE_USED
RAG_REFUSAL_REASON_MISSING
RAG_ANSWER_BEHAVIOR_MISMATCH
```

这些信号可以初步映射：

```text
RAG_ANSWER_POINT_MISSING -> generation
RAG_ANSWER_EXPECTED_SOURCE_MISSING -> citation
RAG_ANSWER_FORBIDDEN_SOURCE_USED -> access_control
RAG_REFUSAL_REASON_MISSING -> refusal / security / access_control
security_block 期望失败 -> security
```

这样你看到一个失败样本时，就不会只看到一堆错误码，而能把它们转成排查路线。

### 4. primary layer 是什么

一个 bad case 可能有多个原因。

比如：

```text
正确资料没召回。
回答漏了答案要点。
引用来源也错了。
```

这时要选一个 primary layer。

primary layer 表示：

```text
优先排查的层。
```

本节规则里，优先级大致是：

```text
security
access_control
retrieval
ranking
generation
citation
refusal
data
evaluation
unknown
```

为什么安全和权限优先？

因为这类问题通常比普通质量问题更严重。

如果 forbidden source 被引用了，不能先忙着调 prompt。

应该先看权限链路。

### 5. warning 也可以进入 bad case 分析

不是所有问题都是 blocking。

比如：

```text
正确资料在 Top-3 里，但不是第 1。
```

这个样本可能仍然通过检索评测。

但它是一个风险信号。

因为如果以后 top_k 变小，或者上下文预算更紧，它可能变成真正失败。

所以本节让 warning 也进入 bad case 分析。

这不是说它一定要立刻修。

而是：

```text
它应该被记录和观察。
```

### 6. bad case 报告应该包含什么

一份实用的 bad case 报告至少应该包含：

```text
case_id
query
primary_layer
cause code
severity
evidence
suggested_action
```

其中：

```text
case_id：定位样本。
query：知道用户问了什么。
primary_layer：先查哪一层。
cause code：具体问题类型。
severity：blocking 还是 warning。
evidence：为什么这么判断。
suggested_action：建议下一步查什么。
```

没有 suggested_action 的报告很难指导修复。

### 7. bad case 分析和参数调优的关系

下一节会学习参数调优。

但参数调优必须基于 bad case。

比如：

```text
Recall 低，可能要调 top_k、score_threshold、query rewrite、chunking。
Precision 低，可能要调 threshold、rerank、metadata filter。
MRR 低，可能要调 rerank 或 hybrid 权重。
回答漏要点，可能要调 prompt 或上下文压缩。
权限泄露，不能靠调 top_k，必须修权限过滤。
```

如果不做 bad case 分析，直接调参数，很可能：

```text
解决一个问题，引入另一个问题。
```

比如盲目增大 top_k：

```text
Recall 可能提高。
Precision 可能下降。
噪声可能变多。
上下文成本可能增加。
安全风险面可能扩大。
```

### 8. 本节不提前做的事

本节不做：

```text
真实向量库评测。
真实 LLM 评委。
自动修复参数。
完整可视化报表。
大规模线上日志分析。
```

本节先建立：

```text
bad case 分层归因思路。
```

只有先会分析，后面调参、监控和生产化才不会乱。

## 本节代码讲解

### 1. `RagBadCaseCause`

`RagBadCaseCause` 表示一个具体原因。

它包含：

```text
layer：问题归因层。
severity：blocking 或 warning。
code：稳定错误码。
reason：原因说明。
evidence：判断证据。
suggested_action：建议排查方向。
```

它不是最终真相，而是基于评测结果生成的初步归因。

### 2. `RagBadCaseAnalysis`

`RagBadCaseAnalysis` 表示单个 case 的分析结果。

它包含：

```text
case_id
query
failed
primary_layer
causes
```

如果一个样本有多个原因，`causes` 会保留全部原因，`primary_layer` 只表示优先排查层。

### 3. `analyze_rag_bad_case`

这个函数负责分析单个样本。

它可以接收：

```text
RetrievalEvalCaseResult
RagAnswerQualityResult
```

也可以两个都传。

这样同一个 case 既能结合检索表现，又能结合最终回答表现。

### 4. `analyze_rag_bad_cases`

这个函数负责分析一组样本。

它把：

```text
RetrievalEvalSummary
RagAnswerQualitySummary
```

按 case_id 合并，然后逐个分析。

最后输出：

```text
RagBadCaseReport
```

报告里会统计：

```text
分析了多少 case。
失败或有风险的 case 有多少。
blocking 原因有多少。
各个 layer 出现了多少原因。
```

### 5. 本节测试重点

本节测试覆盖：

```text
Recall 为 0 时归因到 retrieval。
正确资料不在第 1 时归因到 ranking warning。
回答漏要点时归因到 generation。
引用来源错时归因到 citation。
安全阻断失败时优先归因到 security。
汇总报告能统计 layer_counts。
```

这些测试保护的是 bad case 归因规则，而不是 RAG 生成能力。

## 常见误区

### 误区 1：bad case 就是模型答错

不对。

bad case 可能发生在数据、检索、排序、引用、权限、安全等任何一层。

### 误区 2：看到 Recall 低就直接增大 top_k

不一定。

Recall 低可能是 top_k 小，也可能是 query rewrite、chunking、embedding、metadata filter 或数据缺失问题。

### 误区 3：正确资料进了 Top-K 就不用管

不一定。

如果正确资料排得太靠后，或者噪声太多，仍然可能影响最终回答。

### 误区 4：引用错只是小问题

不是。

引用错会破坏 RAG 的可追溯性和审计能力。

在企业系统里，引用错可能和答错一样严重。

### 误区 5：权限问题可以靠 prompt 解决

不应该。

权限问题必须在检索和上下文进入模型前解决。

不能指望模型自己不泄露无权限资料。

### 误区 6：安全问题和无资料问题可以混在一起

不可以。

`security_block` 和 `no_context` 是不同原因。

混在一起会导致安全风险被掩盖。

### 误区 7：bad case 分析可以完全自动化

目前不建议这么理解。

自动归因能给出初步方向，但真实修复还需要结合日志、样本、检索结果、文档内容和人工判断。

## 本节练习

### 练习 1：判断归因层

题目：

某样本 `Recall@3 = 0`，前 3 条没有任何期望资料。应该优先归因到哪一层？

参考答案：

```text
retrieval
```

原因：

```text
正确资料没有进入候选结果，优先查检索召回、query rewrite、chunking、embedding、metadata filter 和数据覆盖。
```

### 练习 2：判断排序问题

题目：

某样本正确资料在 Top-5 里，但排在第 4。这可能是什么问题？

参考答案：

```text
ranking
```

原因：

```text
正确资料找到了，但排得不够靠前，需要看 rerank、hybrid 权重、分数归一化和 query rewrite。
```

### 练习 3：判断生成问题

题目：

检索命中了正确资料，引用来源也正确，但最终回答漏掉了一个关键答案要点。应该优先查哪一层？

参考答案：

```text
generation
```

可能排查：

```text
prompt 是否要求覆盖条件。
上下文是否太长。
上下文压缩是否丢掉关键句。
模型输出是否太简略。
```

### 练习 4：判断权限问题

题目：

最终回答引用了 `internal-compensation-policy.md`，而它在 `forbidden_sources` 里。应该归因到哪一层？

参考答案：

```text
access_control
```

原因：

```text
禁用来源进入回答链路，优先查权限过滤、tenant、permission_group、visibility 和 forbidden source 逻辑。
```

### 练习 5：判断安全问题

题目：

评测期望 `security_block`，但实际系统回答了知识库里的恶意指令。应该归因到哪一层？

参考答案：

```text
security
```

原因：

```text
提示注入风险没有被正确阻断。
```

## 自测题

### 自测 1：为什么 bad case 分析不能只看最终回答？

答案：

因为最终回答错误可能由数据、检索、排序、上下文、生成、引用、权限或安全等不同层导致。只看最终回答无法定位修复方向。

### 自测 2：`Recall@K = 0` 通常先查什么？

答案：

先查 retrieval 相关问题，包括数据是否存在、chunking、embedding、query rewrite、multi query、metadata filter、top_k 和 score_threshold。

### 自测 3：为什么正确资料排第 3 也值得记录？

答案：

因为它说明排序有风险。如果 top_k 或上下文预算变小，正确资料可能进不了模型上下文。

### 自测 4：`RAG_ANSWER_POINT_MISSING` 通常归因到哪一层？

答案：

通常归因到 generation，但也要进一步检查上下文压缩、prompt 和评测规则是否过于死板。

### 自测 5：为什么 forbidden source 问题优先级高？

答案：

因为它可能意味着无权限资料泄露，属于权限或安全风险，不只是普通回答质量问题。

### 自测 6：bad case 自动归因是不是最终结论？

答案：

不是。它是初步排查方向，最终还要结合日志、检索结果、原文、配置和人工判断。

## 本节小结

本节把 RAG 评测从“发现失败”推进到“定位失败”。

你现在要形成这条排查链：

```text
先看检索指标。
再看回答质量 finding。
再做 bad case 分层归因。
最后根据归因决定修数据、调检索、调排序、改 prompt、修引用、修权限还是修安全。
```

下一节学习：

```text
参数调优：chunk_size、overlap、top_k、score_threshold。
```

到下一节，我们会在 bad case 的基础上学习怎么调参数，而不是凭感觉乱调。
