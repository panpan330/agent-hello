# 阶段 9 第 17 节：参数调优：chunk_size、overlap、top_k、score_threshold

## 本节定位

本节学习 RAG 参数调优。

它接在第 16 节 Bad Case 分析后面：上一节学会先判断 RAG 错在哪一层，本节学习根据指标和 bad case 决定该调哪个参数、往哪个方向调、调完有什么风险。

## 本节学习目标

学完本节，你要能说清楚：

- `chunk_size` 是什么，切太大和切太小有什么影响。
- `chunk_overlap` 是什么，为什么需要重叠。
- `top_k` 是什么，为什么不是越大越好。
- `score_threshold` 是什么，为什么不是越高越好。
- 怎么根据 Recall、Precision、MRR、no_context 和 bad case layer 判断调参方向。
- 为什么权限和安全问题不能靠普通参数调优解决。

## 本节新增和修改

修改：

```text
projects/ai-service/app/rag/tuning.py
projects/ai-service/tests/test_rag_tuning.py
projects/ai-service/app/rag/README.md
projects/ai-service/data/rag_eval/README.md
docs/learning-progress.md
```

新增：

```text
notes/stage9-17-rag-parameter-tuning.md
```

## 一句话先讲透

RAG 参数调优的本质是：

```text
根据评测指标和 bad case 证据，判断应该扩大召回、减少噪声、改善排序、补上下文边界，还是修权限和安全边界。
```

参数调优不是凭感觉把数字调大或调小。

## 基础知识铺垫

### 1. 什么是参数调优

参数调优就是调整系统里的关键参数，让系统表现更符合目标。

在传统后端里，你可能调过：

```text
连接池大小。
超时时间。
线程数。
分页大小。
缓存 TTL。
```

这些参数没有绝对正确值。

它们要根据业务、流量、稳定性和性能目标来决定。

RAG 也是一样。

常见参数包括：

```text
chunk_size
chunk_overlap
top_k
score_threshold
rerank_top_n
context budget
cache ttl
timeout
```

本节先聚焦最基础、最常见的四个：

```text
chunk_size
chunk_overlap
top_k
score_threshold
```

同时也会提到：

```text
rerank
prompt
metadata_filter
no_context_gate
security_policy
```

原因是很多 bad case 不是只靠四个参数就能解决。

### 2. 为什么 RAG 参数不能凭感觉调

很多初学者会这样调：

```text
答错了，那就把 top_k 调大。
噪声多了，那就把 threshold 调高。
回答漏内容，那就把 chunk_size 调大。
```

这些方向有时对，但不能直接套。

因为每个参数都有副作用。

比如 `top_k` 调大：

```text
好处：正确资料更容易进入候选结果。
坏处：噪声更多，上下文更长，模型更容易被干扰，成本更高。
```

`score_threshold` 调高：

```text
好处：低质量结果更少，Precision 可能变高。
坏处：相关但分数不高的资料可能被过滤，Recall 可能下降。
```

所以调参要基于证据。

证据来自：

```text
第 14 节检索指标。
第 15 节回答质量评测。
第 16 节 bad case 分层归因。
```

### 3. 什么是 chunk

RAG 不能直接把整本文档都塞给模型。

通常会先把文档切成小块。

每个小块就是一个 `chunk`。

比如一篇退款政策文档可以切成：

```text
chunk 1：适用范围。
chunk 2：七天无理由退货。
chunk 3：质量问题退货。
chunk 4：退款到账时间。
chunk 5：运费处理。
```

检索时，向量库找的通常不是整篇文档，而是一个个 chunk。

所以 chunk 切得好不好，会直接影响检索质量。

### 4. 什么是 chunk_size

`chunk_size` 表示每个 chunk 大概多长。

在当前学习项目里，它通常按字符数理解。

比如：

```text
chunk_size = 200
```

表示每个 chunk 大约 200 个字符。

如果 `chunk_size` 太小：

```text
一个完整规则可能被切碎。
检索命中的 chunk 缺少上下文。
模型看到的资料不完整。
同一个事实分散在多个 chunk。
```

如果 `chunk_size` 太大：

```text
一个 chunk 里混入多个主题。
向量表示变得不够聚焦。
检索命中后带来太多无关内容。
上下文预算消耗更快。
```

所以 chunk_size 的目标不是越大越好，也不是越小越好。

它要让一个 chunk 尽量做到：

```text
语义完整。
主题集中。
长度可控。
便于引用。
```

### 5. 什么是 chunk_overlap

`chunk_overlap` 表示相邻 chunk 之间保留多少重复内容。

比如：

```text
chunk_size = 200
chunk_overlap = 40
```

表示切下一个 chunk 时，会和上一个 chunk 重叠一部分内容。

为什么需要 overlap？

因为重要信息可能正好出现在切分边界。

比如：

```text
质量问题或商家原因退货时，运费通常由商家承担。
用户个人原因退货时，运费通常由用户承担。
```

如果切分刚好把两句话分开，模型可能只看到前半句。

overlap 可以缓解边界丢失问题。

但 overlap 也不是越大越好。

overlap 太大：

```text
索引体积变大。
重复内容变多。
检索结果里重复 chunk 变多。
上下文里重复信息变多。
成本上升。
```

### 6. 什么是 top_k

`top_k` 表示检索时取前 K 条结果。

比如：

```text
top_k = 3
```

表示检索器返回最相关的 3 个 chunk。

top_k 太小：

```text
正确资料可能进不来。
多事实问题可能找不全。
Recall 可能低。
```

top_k 太大：

```text
噪声资料变多。
Precision 可能低。
上下文变长。
模型更容易被无关内容干扰。
安全扫描压力更大。
```

top_k 是最常被乱调的参数。

它确实能改善召回，但不能解决所有问题。

### 7. 什么是 score_threshold

`score_threshold` 表示分数阈值。

它决定：

```text
低于某个相关性分数的结果不要。
```

但这里要注意：

不同向量库、不同距离算法的分数方向不同。

有的分数越高越相关。

有的距离越低越相关。

第 6 节我们已经学过 score、distance、similarity 的区别。

本节只讲调优思想：

```text
threshold 越宽松，Recall 可能越高，但噪声更多。
threshold 越严格，Precision 可能越高，但可能误伤正确资料。
```

### 8. Recall 低时怎么想

Recall 低表示：

```text
应该找回来的资料，没有找回来。
```

常见表现：

```text
Recall@K = 0
Recall@K < 1
bad case layer = retrieval
```

这时优先考虑：

```text
top_k 是否太小。
score_threshold 是否太严格。
chunk_size 是否让关键事实难以被检索。
chunk_overlap 是否太小导致边界事实丢失。
query rewrite 是否没有把口语问题改好。
metadata_filter 是否过滤掉了正确资料。
```

调参方向可能是：

```text
适当增大 top_k。
适当降低 score_threshold。
review chunk_size。
review chunk_overlap。
```

但不要立刻同时全部改。

应该一次只改一两个变量，然后用评测集比较。

### 9. Precision 低时怎么想

Precision 低表示：

```text
前 K 条里噪声太多。
```

常见表现：

```text
Precision@K < 0.5
Recall@K 已经可以接受
bad case 里大量 low precision
```

这时优先考虑：

```text
score_threshold 是否太宽松。
top_k 是否太大。
metadata_filter 是否太松。
hybrid 权重是否把噪声推上来。
rerank 是否没有把相关资料排前面。
```

调参方向可能是：

```text
适当提高 score_threshold。
适当降低 top_k。
review rerank。
review metadata_filter。
```

但如果 Recall 同时很低，就不能盲目提高 threshold。

因为这可能让正确资料更难进入候选集。

### 10. MRR 低时怎么想

MRR 低表示：

```text
正确资料找到了，但排得不靠前。
```

常见表现：

```text
Hit Rate@K 高。
Recall@K 还可以。
MRR@K 低。
first_relevant_rank > 1。
bad case layer = ranking。
```

这时优先考虑：

```text
rerank 是否有效。
hybrid fusion 权重是否合理。
query rewrite 是否引入了偏差。
score normalization 是否正确。
```

这类问题不一定靠增大 top_k 解决。

因为正确资料已经在候选里，关键是：

```text
把它排到更前面。
```

### 11. no_context 失败时怎么想

no_context 样本失败表示：

```text
本来知识库没有资料，系统却找出了一些候选资料。
```

这很危险。

因为模型可能基于弱相关资料编答案。

常见调参方向：

```text
提高 score_threshold。
增加 no_context_gate。
加强意图识别。
检查知识库覆盖边界。
```

但也要注意：

```text
threshold 太高会误伤正常问题。
```

所以 no_context 调优一定要和正向样本一起回归。

### 12. 回答要点覆盖率低时怎么想

第 15 节里有：

```text
answer_point_coverage
```

如果它低，说明最终回答漏要点。

可能原因包括：

```text
正确资料没找全。
上下文压缩丢掉关键句。
chunk 边界切断了事实。
prompt 没要求覆盖条件。
模型回答太简略。
```

调参方向可能是：

```text
review prompt。
增加 chunk_overlap。
review chunk_size。
review context compression。
```

如果检索指标本来就低，先修检索。

如果检索指标高但回答漏要点，再重点看 prompt 和上下文组织。

### 13. 权限和安全问题不能靠普通参数解决

这是本节最重要的边界之一。

如果 bad case layer 是：

```text
access_control
security
```

不要先调：

```text
top_k
score_threshold
chunk_size
```

权限问题应该查：

```text
metadata_filter
RagAccessScope
tenant_id
permission_group
visibility
forbidden_sources
```

安全问题应该查：

```text
security_policy
prompt injection rules
risk level
blocking severity
metadata scan
```

不能指望模型自己不泄露无权限资料，也不能靠 threshold 解决提示注入。

## 本节主题系统讲解

### 1. 本节在质量闭环里的位置

阶段 9 到这里已经形成了一个链路：

```text
评测集设计
-> 检索指标
-> 回答质量评测
-> bad case 分析
-> 参数调优
```

第 17 节不是孤立讲四个参数。

它是把前面评测结果转成调参建议。

没有评测结果时，调参是猜。

有了评测结果后，调参才有方向。

### 2. 本节的调参输入

本节调参建议来自三类输入：

```text
RetrievalEvalSummary
RagAnswerQualitySummary
RagBadCaseReport
```

`RetrievalEvalSummary` 提供：

```text
Hit Rate@K
Recall@K
Precision@K
MRR@K
no_result_success_rate
```

`RagAnswerQualitySummary` 提供：

```text
answer_point_coverage
citation_pass_rate
refusal_pass_rate
```

`RagBadCaseReport` 提供：

```text
retrieval layer 数量。
ranking layer 数量。
generation layer 数量。
access_control layer 数量。
security layer 数量。
```

这些输入组合起来，就能生成调参建议。

### 3. 调参建议应该包含什么

一个调参建议不能只写：

```text
把 top_k 调大。
```

它至少要包含：

```text
调哪个参数。
往哪个方向调。
优先级。
为什么调。
证据是什么。
预期收益。
风险是什么。
```

比如：

```text
parameter: top_k
direction: increase
priority: high
reason: Recall@K is low
evidence: recall@3=0.0000
expected_benefit: Give retrieval more room to include missing relevant chunks.
risk: Higher top_k can reduce precision and increase context noise.
```

这样你以后看报告时，不只是看到一个命令，而是知道它背后的判断逻辑。

### 4. 低 Recall 的调参逻辑

如果：

```text
Recall@K < 0.8
```

本节会建议：

```text
increase top_k
decrease score_threshold
review chunk_size
```

原因是低 Recall 首先说明：

```text
正确资料没有进入候选集。
```

但这些建议都有风险。

增加 top_k：

```text
可能引入更多噪声。
```

降低 threshold：

```text
可能让弱相关资料进入上下文。
```

调整 chunk_size：

```text
可能需要重新入库，也可能改变 chunk_id。
```

所以建议不是让你立刻全改，而是告诉你优先检查这些方向。

### 5. 低 Precision 的调参逻辑

如果：

```text
Precision@K < 0.5
Recall@K >= 0.8
```

本节会建议：

```text
increase score_threshold
decrease top_k
```

这里有一个关键条件：

```text
Recall@K >= 0.8
```

为什么？

因为如果 Recall 本来就低，还提高 threshold，很可能让正确资料更难被找回。

所以调优顺序是：

```text
先保证能找回来。
再减少噪声。
```

这也是本节代码特意避免“同一场景同时建议提高和降低 threshold”的原因。

### 6. 低 MRR 的调参逻辑

如果：

```text
Hit Rate@K 高
MRR@K 低
```

说明：

```text
正确资料经常能找到，但排得不靠前。
```

本节会建议：

```text
review rerank
```

这不是四个基础参数之一，但是真实 RAG 里很重要。

原因是：

```text
top_k 解决的是有没有进入候选。
rerank 解决的是候选里的顺序好不好。
```

### 7. no_context 失败的调参逻辑

如果：

```text
no_result_success_rate < 1.0
```

说明：

```text
应该无资料的问题仍然返回了检索结果。
```

本节会建议：

```text
increase score_threshold
review no_context_gate
```

这里 `no_context_gate` 不是普通向量库参数。

它表示：

```text
系统需要一个判断“资料不足，不应该回答”的门槛。
```

这个门槛可能结合：

```text
最高分。
top results 分布。
query intent。
业务域。
安全规则。
```

### 8. 回答质量差的调参逻辑

如果：

```text
average_answer_point_coverage < 0.8
```

本节会建议：

```text
review prompt
increase chunk_overlap
```

原因是回答漏要点可能来自：

```text
prompt 没要求覆盖关键条件。
chunk 边界切断了相邻事实。
上下文组织让模型忽略了某些资料。
```

但如果检索指标也差，应该先修检索。

回答质量建议不能脱离检索指标看。

### 9. bad case layer 的调参逻辑

第 16 节已经能输出 bad case layer。

本节会根据 layer 给建议：

```text
retrieval -> top_k increase
ranking -> rerank review
generation -> prompt review
access_control -> metadata_filter review
security -> security_policy review
```

这里要注意：

```text
access_control 和 security 不是普通调参问题。
```

它们更像边界修复。

所以建议是 review metadata_filter 或 security_policy，而不是调大 top_k。

### 10. 怎么实际执行一次调参

真实项目里建议按这个步骤：

```text
1. 固定一份评测集。
2. 跑当前 baseline。
3. 记录检索指标、回答质量、bad case layer。
4. 根据建议只改一个或少量参数。
5. 重新跑同一份评测集。
6. 对比指标提升和副作用。
7. 如果提升稳定，再保留改动。
```

不要这样做：

```text
同时改 top_k、threshold、chunk_size、prompt、rerank。
```

因为一旦指标变化，你不知道是哪一个改动造成的。

### 11. 本节不做真实调参实验

本节不启动 Qdrant 或 Milvus。

也不真实调用 embedding。

原因是本节目标是：

```text
建立调参判断逻辑。
```

真实调参实验会在后续可以结合真实向量库和评测脚本继续做。

现在先把：

```text
指标 -> bad case -> 调参建议
```

这条链路学清楚。

## 本节代码讲解

### 1. `RagParameterTuningRecommendation`

这个模型表示一条调参建议。

它包含：

```text
parameter
direction
priority
reason
evidence
expected_benefit
risk
```

这让调参建议不是一句空话，而是有证据、有收益、有风险。

### 2. `RagParameterTuningReport`

这个模型表示一组调参建议。

它包含：

```text
recommendation_count
high_priority_count
metric_snapshot
recommendations
```

`metric_snapshot` 会保留当时触发建议的指标，方便以后回看。

### 3. `build_rag_parameter_tuning_report`

这个函数接收：

```text
RetrievalEvalSummary
RagAnswerQualitySummary
RagBadCaseReport
```

然后生成调参建议。

它不会真的修改参数。

它只负责：

```text
根据证据给出建议。
```

真正改配置、跑实验、对比结果，是后续人工或脚本执行的事。

### 4. 本节测试重点

本节测试覆盖：

```text
低 Recall 优先建议增加 top_k、降低 score_threshold、review chunk_size。
低 Precision 且 Recall 可接受时建议提高 score_threshold、降低 top_k。
no_context 失败时建议提高 threshold 和 review no_context_gate。
答案要点覆盖率低时建议 review prompt 和增加 chunk_overlap。
bad case layer 中的 retrieval/security 能生成对应建议。
```

这些测试保护的是调参判断规则。

## 常见误区

### 误区 1：top_k 越大越好

不对。

top_k 变大可能提高 Recall，但也会增加噪声、成本和安全风险。

### 误区 2：score_threshold 越高越好

不对。

threshold 太高会误伤相关资料，导致 Recall 下降。

### 误区 3：Recall 低时先提高 threshold

通常不应该。

Recall 低说明资料找不回来，提高 threshold 可能让问题更严重。

### 误区 4：Precision 低时直接降低 top_k

要看 Recall。

如果 Recall 已经低，降低 top_k 可能让正确资料更难进入候选。

### 误区 5：chunk_overlap 越大越稳

不对。

overlap 太大会增加重复内容、索引体积和噪声。

### 误区 6：权限和安全问题可以靠调 threshold 解决

不对。

权限要靠 metadata filter 和 access scope。

安全要靠 security policy 和防护链路。

### 误区 7：一次改很多参数效率更高

不建议。

一次改很多参数，评测结果变化后无法判断是哪一个参数起作用。

## 本节练习

### 练习 1：低 Recall 怎么调

题目：

评测结果：

```text
Recall@3 = 0.3
Precision@3 = 0.6
```

应该优先考虑哪些方向？

参考答案：

```text
优先考虑 increase top_k、decrease score_threshold、review chunk_size/chunk_overlap。
```

原因：

```text
Recall 低说明正确资料没有充分进入候选集，先解决找不回来的问题。
```

### 练习 2：低 Precision 怎么调

题目：

评测结果：

```text
Recall@5 = 0.9
Precision@5 = 0.3
```

应该优先考虑哪些方向？

参考答案：

```text
可以考虑 increase score_threshold、decrease top_k、review rerank 和 metadata_filter。
```

原因：

```text
Recall 已经可以接受，但 Precision 低说明噪声太多。
```

### 练习 3：低 MRR 怎么调

题目：

评测结果：

```text
Hit Rate@5 = 0.9
MRR@5 = 0.35
```

说明什么？应该优先看什么？

参考答案：

```text
说明正确资料经常能进入前 5，但排得不靠前。
```

应该优先看：

```text
rerank、hybrid fusion 权重、score normalization、query rewrite。
```

### 练习 4：no_context 失败怎么调

题目：

无资料样本经常返回检索结果，应该看哪些方向？

参考答案：

```text
increase score_threshold
review no_context_gate
review intent routing
review 知识库覆盖边界
```

原因：

```text
系统需要更可靠地判断“没有足够资料，不应该回答”。
```

### 练习 5：权限 bad case 怎么调

题目：

bad case layer 是 `access_control`，最终回答引用了 forbidden source。应该调 top_k 吗？

参考答案：

```text
不应该优先调 top_k。
```

应该先查：

```text
metadata_filter
RagAccessScope
tenant_id
permission_group
visibility
forbidden_sources
```

## 自测题

### 自测 1：为什么参数调优必须基于评测集？

答案：

因为没有固定评测集，就无法判断调参前后到底变好了还是变坏了，也无法发现某个参数是否只改善了少数样本却伤害了其他样本。

### 自测 2：`chunk_size` 太小可能带来什么问题？

答案：

关键事实可能被切碎，检索命中的 chunk 缺少上下文，模型看到的信息不完整。

### 自测 3：`chunk_overlap` 太大有什么问题？

答案：

会增加索引体积、重复内容、检索噪声和上下文成本。

### 自测 4：为什么低 Recall 时不能盲目提高 `score_threshold`？

答案：

因为 Recall 低说明正确资料已经难以进入候选，提高 threshold 可能继续过滤掉相关资料。

### 自测 5：为什么低 Precision 时也不能盲目降低 `top_k`？

答案：

如果 Recall 也低，降低 top_k 会让正确资料更难进入候选。要先看 Recall 是否已经可以接受。

### 自测 6：bad case layer 是 `security` 时，应该优先查什么？

答案：

应该优先查 security_policy、prompt injection rules、risk level、blocking severity 和安全防护链路，而不是普通 top_k 或 threshold。

## 本节小结

本节把第 14、15、16 节的评测结果转成调参建议。

你现在要记住：

```text
Recall 低：先扩大召回或检查切分。
Precision 低：在 Recall 可接受时减少噪声。
MRR 低：重点看排序和 rerank。
no_context 失败：看 threshold 和 no_context gate。
回答漏要点：看 prompt、chunk 边界和上下文组织。
权限和安全失败：不要靠普通参数调优，先修边界。
```

下一节学习：

```text
RAG 缓存、超时、降级和性能优化。
```

到下一节，我们会从“质量优化”进一步进入“真实服务可用性和性能保护”。
