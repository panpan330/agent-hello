# 阶段 9 第 14 节：检索指标：命中率、召回率、Top-K 命中

## 本节定位

本节学习 RAG 检索指标。

它接在第 13 节 RAG 评测集设计后面：上一节先定义“应该找哪些资料、哪些情况应该拒答”，这一节开始学习怎么用指标判断“检索阶段有没有把正确资料找出来”。

## 本节学习目标

学完本节，你要能说清楚：

- 什么是 Top-K。
- 什么是 Hit@K 和 Hit Rate@K。
- 什么是 Recall@K。
- 什么是 Precision@K。
- 什么是 MRR@K。
- 为什么检索指标只评价“找资料”，不评价最终回答。
- 为什么无资料、权限拒答、安全阻断不能和普通回答样本混在一起算检索指标。

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
notes/stage9-14-retrieval-metrics-hit-recall-topk.md
```

## 一句话先讲透

检索指标的本质是：

```text
不看模型最后怎么回答，先看检索器有没有在前 K 条结果里把应该用的资料找出来。
```

如果资料都没找对，后面生成再强也很难稳定答对。

## 基础知识铺垫

### 1. RAG 为什么要单独评测检索

RAG 链路可以简化成：

```text
用户问题
-> 检索资料
-> 把资料交给模型
-> 模型生成回答
```

很多初学者容易只盯着最后回答。

比如用户问：

```text
退货运费谁承担？
```

模型回答：

```text
质量问题或商家原因退货时通常由商家承担，个人原因退货时通常由用户承担。
```

这个答案看起来对。

但我们还要问：

```text
检索阶段找到了退款退货规则吗？
找到了“运费处理”段落吗？
这个回答是不是来自允许使用的资料？
如果没找到资料，模型是不是靠常识猜的？
```

检索评测就是把注意力放在“找资料”这一步。

它回答的问题是：

```text
正确资料有没有进入候选结果。
正确资料排在第几名。
前 K 条里有多少噪声。
应该找的多个资料有没有都找回来。
```

### 2. 什么是候选结果

检索器返回的结果通常不是一条，而是一组候选资料。

比如：

```text
第 1 条：退款退货规则 / 七天无理由退货
第 2 条：退款退货规则 / 运费处理
第 3 条：订单发货规则 / 正常发货时效
```

这些就是候选结果。

候选结果里可能有：

```text
相关资料。
部分相关资料。
噪声资料。
无权限资料。
过期资料。
被安全规则阻断的资料。
```

检索指标一般先关注：

```text
相关资料有没有出现在前 K 条。
```

权限和安全问题也很重要，但它们是另外的评价维度，不能简单当成普通相关性指标。

### 3. 什么是 relevant

`relevant` 的意思是相关。

在检索评测里，一条结果是否 relevant，不是看它语义上好像有点像，而是看它是否命中了评测样本里提前写好的期望资料。

比如评测样本写：

```text
query: 退货运费谁承担？
expected_source: refund-return-policy.md
expected_section: 运费处理
expected_chunk_id: refund_return_policy_chunk_0005
```

那么命中这个 chunk，才是 relevant。

如果检索结果是：

```text
refund-return-policy.md / 七天无理由退货
```

它虽然来自同一个退款文档，但不一定 relevant。

因为问题问的是运费承担，不是七天无理由。

这就是为什么第 13 节要提前设计 expected evidence。

没有 expected evidence，就无法判断检索结果到底算不算 relevant。

### 4. 什么是 Top-K

`Top-K` 表示只看前 K 条结果。

比如：

```text
Top-1：只看第 1 条。
Top-3：只看前 3 条。
Top-5：只看前 5 条。
Top-10：只看前 10 条。
```

RAG 里通常不会只看第 1 条。

原因是：

```text
用户问题可能涉及多个资料。
向量检索的排序不一定完全准确。
后面还有 rerank 和上下文压缩。
模型生成时可能需要多个 chunk 拼起来。
```

但是 K 也不是越大越好。

K 太小：

```text
正确资料可能进不来。
```

K 太大：

```text
噪声变多。
上下文变长。
成本变高。
模型更容易被无关内容干扰。
安全扫描和引用校验压力也会变大。
```

所以 Top-K 是 RAG 里非常核心的参数。

### 5. 什么是 Hit@K

`Hit@K` 用在单个样本上。

它问的是：

```text
前 K 条结果里，有没有至少一条正确资料？
```

如果有，Hit@K = 1。

如果没有，Hit@K = 0。

例子：

```text
query: 退货运费谁承担？
expected_chunk_id: refund_return_policy_chunk_0005
top_3:
  1. refund_return_policy_chunk_0002
  2. refund_return_policy_chunk_0005
  3. order_shipping_policy_chunk_0002
```

正确 chunk 出现在第 2 条。

所以：

```text
Hit@3 = 1
```

如果只看 Top-1：

```text
Hit@1 = 0
```

因为第 1 条不是正确 chunk。

这说明同一个结果，在不同 K 下指标可能不同。

### 6. 什么是 Hit Rate@K

`Hit Rate@K` 用在一组样本上。

它问的是：

```text
所有样本里，有多少比例的样本在前 K 条命中过至少一条正确资料？
```

公式是：

```text
Hit Rate@K = 命中的样本数 / 参与评测的样本数
```

比如有 4 个样本：

```text
样本 A：Hit@3 = 1
样本 B：Hit@3 = 1
样本 C：Hit@3 = 0
样本 D：Hit@3 = 1
```

那么：

```text
Hit Rate@3 = 3 / 4 = 0.75
```

Hit Rate 很直观。

它适合回答：

```text
检索器有没有大概率把正确资料找进候选集？
```

但它也有缺点。

如果一个问题需要找 3 个关键 chunk，只找到 1 个，也算 hit。

所以 Hit Rate 只能说明“至少找到了一个”，不能说明“全部找齐了”。

### 7. 什么是 Recall@K

`Recall@K` 通常翻译成召回率。

它问的是：

```text
应该找回来的正确资料里，前 K 条找回来了多少？
```

公式是：

```text
Recall@K = 前 K 条中命中的正确资料数 / 应该命中的正确资料总数
```

例子：

```text
expected_chunk_ids:
  - A
  - B
  - C

top_5:
  1. A
  2. X
  3. B
  4. Y
  5. Z
```

找回了 A 和 B，没有找回 C。

所以：

```text
Recall@5 = 2 / 3 = 0.6667
```

Recall 适合回答：

```text
应该找的资料是否找全。
```

在 RAG 里，如果答案需要多个事实，Recall 比 Hit 更重要。

因为只 hit 一个 chunk，可能不足以生成完整回答。

### 8. 什么是 Precision@K

`Precision@K` 通常翻译成精确率。

它问的是：

```text
前 K 条结果里，有多少条是真正相关的？
```

公式是：

```text
Precision@K = 前 K 条中相关资料数 / K
```

例子：

```text
top_5:
  1. A relevant
  2. X noise
  3. B relevant
  4. Y noise
  5. Z noise
```

前 5 条里有 2 条 relevant。

所以：

```text
Precision@5 = 2 / 5 = 0.4
```

Precision 适合回答：

```text
候选结果里噪声多不多。
```

RAG 里 Precision 太低，会带来几个问题：

```text
上下文里噪声变多。
模型更容易引用无关资料。
Context Compression 压力变大。
Prompt Injection 风险面变大。
```

### 9. Recall 和 Precision 的关系

Recall 和 Precision 经常有拉扯关系。

如果你把 top_k 调大：

```text
Recall 可能提高，因为正确资料更容易进入前 K。
Precision 可能下降，因为噪声也更多。
```

如果你把 score_threshold 调高：

```text
Precision 可能提高，因为低质量结果被过滤。
Recall 可能下降，因为一些正确但分数不高的资料也可能被过滤。
```

这就是为什么 RAG 参数不能凭感觉调。

你需要同时看：

```text
Hit Rate@K
Recall@K
Precision@K
MRR@K
no_context_success_rate
```

不同指标回答不同问题。

### 10. 什么是 MRR@K

`MRR` 是 Mean Reciprocal Rank。

可以先理解成：

```text
正确资料排得越靠前，MRR 越高。
```

单个样本里，先找到第一个 relevant 的排名。

如果第一个 relevant 在第 1 名：

```text
Reciprocal Rank = 1 / 1 = 1.0
```

如果第一个 relevant 在第 2 名：

```text
Reciprocal Rank = 1 / 2 = 0.5
```

如果第一个 relevant 在第 5 名：

```text
Reciprocal Rank = 1 / 5 = 0.2
```

如果前 K 条没有 relevant：

```text
Reciprocal Rank = 0
```

多个样本求平均，就是 MRR@K。

MRR 适合回答：

```text
正确资料是不是排得足够靠前。
```

它比 Hit Rate 更敏感。

因为下面两种情况 Hit@5 都是 1：

```text
正确资料排第 1。
正确资料排第 5。
```

但 MRR 不一样：

```text
第 1 名：1.0
第 5 名：0.2
```

### 11. 无资料样本怎么处理

第 13 节有 `no_context` 样本。

比如：

```text
query: 会员积分怎么兑换？
behavior: no_context
```

这类样本没有 expected_sources。

因为正确行为是：

```text
不要找出看似相关的资料来硬答。
```

所以它不适合参与普通 Hit Rate、Recall、Precision、MRR。

它应该单独看：

```text
no_result_success_rate
```

也就是：

```text
应该无资料的样本，系统是否没有返回候选资料。
```

本项目已有的检索评测逻辑就是这样处理：

```text
普通 answer 样本参与检索指标。
no_context 样本不参与普通检索指标，单独统计 no_result_success_rate。
```

### 12. 权限拒答和安全阻断为什么不直接算普通检索指标

第 13 节还有：

```text
access_denied
security_block
```

这些样本不应该直接混进普通检索指标。

原因是它们的目标不是“找到正确资料并回答”。

权限拒答的目标是：

```text
不要把无权限资料交给模型。
```

安全阻断的目标是：

```text
不要把危险资料当成正常上下文使用。
```

它们应该用专门指标评测，比如：

```text
access_denied_pass_rate
security_block_rate
forbidden_source_leak_count
prompt_injection_block_rate
```

这些会在后续回答质量评测、安全评测和 bad case 分析里继续展开。

本节只把 `answer` 和 `no_context` 样本转换为检索评测样本。

### 13. 检索指标不评价最终回答

这一点必须记住。

检索指标只看：

```text
资料有没有找对。
```

它不看：

```text
模型有没有理解资料。
模型有没有表达清楚。
模型有没有引用准确。
模型有没有拒答合理。
模型有没有幻觉。
```

比如：

```text
Recall@3 = 1.0
```

只能说明：

```text
正确资料在前 3 条里。
```

但模型仍然可能：

```text
漏掉关键条件。
引用错 chunk。
把多个规则混在一起。
回答语气不适合客服场景。
```

所以检索指标是必要条件，不是充分条件。

## 本节主题系统讲解

### 1. 本节把第 13 节和已有检索指标接起来

第 13 节新增了更完整的 RAG 评测样本：

```text
RagEvalCase
RagEvalExpectation
RagEvalAccessContext
```

它们描述的是完整 RAG 行为。

本节已有的检索指标逻辑使用的是：

```text
RetrievalEvalCase
```

它更聚焦，只关心：

```text
query
expected_sources
expected_sections
expected_chunk_ids
expect_no_results
```

所以本节补了一层转换：

```text
RagEvalCase -> RetrievalEvalCase
```

这层转换的意义是：

```text
评测集只维护一份，但可以服务不同评测维度。
```

完整 RAG 评测关注最终行为。

检索评测只抽取其中和资料命中相关的部分。

### 2. 哪些样本能转成检索评测样本

本节转换规则很克制。

可以转换：

```text
answer
no_context
```

`answer` 样本表示：

```text
应该找资料并回答。
```

所以它需要 expected evidence。

如果一个 `answer` 样本只写了答案要点，没有写 expected source、section 或 chunk，它可以用于后续回答质量评测，但不能用于本节检索指标。

`no_context` 样本表示：

```text
当前知识库没有资料，不应该找出候选资料。
```

所以它变成 `expect_no_results=True`。

暂时不转换：

```text
access_denied
security_block
clarify
```

原因是这些不是普通资料命中问题。

它们应该由权限、安全和意图澄清相关评测单独处理。

这样边界更清楚。

### 3. match level 为什么有三层

检索评测支持三种匹配粒度：

```text
chunk_id
section
source
```

优先级是：

```text
chunk_id > section > source
```

如果样本写了 `expected_chunk_ids`，就按 chunk_id 判断。

如果没有 chunk_id，但写了 `expected_sections`，就按 section 判断。

如果只写了 `expected_sources`，就按 source 判断。

这对应了 RAG 项目的不同成熟度：

```text
source：早期稳定，适合粗粒度判断。
section：中等粒度，适合结构化文档。
chunk_id：最精确，适合切分策略稳定后的回归评测。
```

本项目里很多样本已经有 chunk_id。

所以当前优先使用 chunk_id 判断。

### 4. 单条样本怎么计算

假设：

```text
expected_chunk_id = refund_return_policy_chunk_0005
top_k = 3
```

检索返回：

```text
1. refund_return_policy_chunk_0002
2. refund_return_policy_chunk_0005
3. order_shipping_policy_chunk_0002
```

那么：

```text
Hit@3 = 1
Recall@3 = 1 / 1 = 1.0
Precision@3 = 1 / 3 = 0.333333
MRR@3 = 1 / 2 = 0.5
```

这说明：

```text
正确资料找到了。
但是没排第一。
前 3 条里有 2 条噪声。
```

这比一句“通过”更有信息量。

### 5. 一组样本怎么汇总

一组样本会汇总成：

```text
case_count
evaluated_case_count
no_result_case_count
passed_case_count
failed_case_count
hit_rate_at_k
recall_at_k
precision_at_k
mrr_at_k
no_result_success_rate
```

这里要注意：

```text
case_count 包含全部样本。
evaluated_case_count 只包含普通检索指标样本。
no_result_case_count 单独统计无资料样本。
```

这样不会把无资料样本错误混进普通 Recall 和 Precision。

### 6. 怎么读指标组合

只看一个指标容易误判。

如果：

```text
Hit Rate@5 高
Recall@5 低
```

可能说明：

```text
大部分问题至少找到了一个相关资料，但需要多个资料的问题没有找全。
```

如果：

```text
Recall@5 高
Precision@5 低
```

可能说明：

```text
正确资料找到了，但噪声很多。
```

如果：

```text
Hit Rate@5 高
MRR@5 低
```

可能说明：

```text
正确资料在前 5 条里，但排得不靠前。
```

如果：

```text
no_result_success_rate 低
```

可能说明：

```text
无资料问题仍然返回了候选资料，后续模型可能编答案。
```

这就是指标组合的价值。

### 7. 检索指标和参数调优的关系

后面第 17 节会学参数调优。

但你现在已经可以先建立直觉。

如果 Recall 低：

```text
可以考虑增加 top_k。
可以考虑降低 score_threshold。
可以考虑优化 query rewrite。
可以考虑启用 multi query。
可以考虑检查 chunk 切分是否太碎或太大。
```

如果 Precision 低：

```text
可以考虑提高 score_threshold。
可以考虑加强 rerank。
可以考虑优化 metadata filter。
可以考虑减少 top_k。
可以考虑改进 hybrid 权重。
```

如果 MRR 低：

```text
可以考虑优化 rerank。
可以考虑调整 hybrid fusion 权重。
可以考虑检查向量模型或 rerank 模型是否适合业务文本。
```

如果无资料成功率低：

```text
可以考虑提高阈值。
可以考虑增加 no_context 判断。
可以考虑加强意图识别和安全过滤。
```

这些不是本节要马上调的内容。

本节先学会看懂指标。

### 8. 本节不提前做的事

本节不做：

```text
真实 Qdrant / Milvus 检索评测。
真实 embedding 调用。
真实 rerank 模型调用。
LLM-as-judge。
最终回答质量打分。
完整 bad case 分类。
参数自动调优。
```

原因是：

```text
指标基础必须先讲清楚。
```

如果还没理解 Hit、Recall、Precision、MRR，直接上真实评测报告，很容易只看一堆数字却不知道该怎么行动。

## 本节代码讲解

本节代码只补学习目标直接相关的两点。

### 1. `build_retrieval_eval_cases_from_rag_cases`

这个函数负责：

```text
从完整 RAG 评测样本中，抽取可以用于检索指标评测的样本。
```

它会处理：

```text
answer -> 普通 RetrievalEvalCase
no_context -> expect_no_results=True 的 RetrievalEvalCase
```

其中 `answer` 样本必须有 expected evidence。没有期望来源的 answer 样本会被跳过，因为检索指标没有办法判断什么资料算命中。

它会跳过：

```text
access_denied
security_block
clarify
```

这样做的原因是：

```text
检索指标只评价资料命中。
权限拒答、安全阻断和澄清问题应该由专门评测处理。
```

### 2. `format_retrieval_case_metric_breakdown`

这个函数负责把单个样本的指标解释清楚。

它会输出类似：

```text
hit@3: 1 (first_relevant_rank=2)
recall@3: 1/1 = 1.000000
precision@3: 1/3 = 0.333333
mrr@3: 0.500000
```

这不是为了机器计算，而是为了学习和排查。

你以后看检索评测结果时，应该能从这些数字反推：

```text
正确资料有没有出现。
出现了几条。
应该出现几条。
排在第几。
噪声占多少。
```

### 3. 本节测试重点

本节测试没有真实调用模型，也没有启动向量数据库。

测试重点是：

```text
RAG 评测样本能正确转换成检索评测样本。
no_context 样本可以选择是否纳入检索评测。
security_block 样本不会被误当成普通检索样本。
单条检索结果能输出 Hit/Recall/Precision/MRR 公式解释。
```

这些测试保护的是指标解释和评测边界。

## 常见误区

### 误区 1：Hit Rate 高就代表 RAG 好

不一定。

Hit Rate 高只能说明：

```text
至少有一条正确资料进入前 K。
```

它不说明：

```text
资料是否找全。
资料是否排得靠前。
噪声是否很多。
最终回答是否正确。
引用是否一致。
```

### 误区 2：Recall 高就可以放心

不一定。

Recall 高说明正确资料找回来了。

但如果 Precision 很低，说明噪声也很多。

噪声多会影响模型生成，也会增加上下文成本和安全风险。

### 误区 3：Precision 越高越好，所以 top_k 越小越好

不一定。

top_k 太小，Precision 可能看起来高，但 Recall 可能很差。

比如只返回 1 条，刚好相关：

```text
Precision@1 = 1.0
```

但如果答案需要 3 个资料，这个结果仍然不够。

### 误区 4：MRR 和 Hit Rate 差不多

不一样。

Hit Rate 只关心有没有命中。

MRR 关心第一个正确结果排第几。

正确资料排第 1 和排第 5，Hit@5 都是 1，但 MRR 差很多。

### 误区 5：无资料样本也应该参与普通 Recall

不应该。

无资料样本没有 expected evidence。

它应该单独看 no_result_success_rate，而不是混进普通检索指标。

### 误区 6：权限拒答样本应该当成检索失败

不准确。

权限拒答不是普通检索失败。

它关注的是：

```text
无权限资料有没有被挡住。
```

这应该由权限评测或泄露评测处理。

### 误区 7：检索指标能证明最终回答正确

不能。

检索指标只能证明资料找得怎么样。

最终回答还要看：

```text
答案正确性。
引用一致性。
拒答合理性。
是否幻觉。
是否遵守安全边界。
```

这正是下一节要学的内容。

## 本节练习

### 练习 1：计算 Hit@3

题目：

期望 chunk 是 `B`，Top-3 返回：

```text
A, C, B
```

Hit@3 是多少？

参考答案：

```text
Hit@3 = 1
```

因为期望 chunk `B` 出现在前 3 条里。

### 练习 2：计算 Recall@5

题目：

期望 chunk 是：

```text
A, B, C
```

Top-5 返回：

```text
A, X, B, Y, Z
```

Recall@5 是多少？

参考答案：

```text
Recall@5 = 2 / 3 = 0.6667
```

因为 A 和 B 找回来了，C 没找回来。

### 练习 3：计算 Precision@5

题目：

Top-5 返回中，只有 2 条是真相关资料。Precision@5 是多少？

参考答案：

```text
Precision@5 = 2 / 5 = 0.4
```

### 练习 4：计算单个样本的 Reciprocal Rank

题目：

第一个正确资料排在第 4 名，Reciprocal Rank 是多少？

参考答案：

```text
Reciprocal Rank = 1 / 4 = 0.25
```

### 练习 5：判断指标含义

题目：

一个系统 `Hit Rate@5` 很高，但 `MRR@5` 很低，可能说明什么？

参考答案：

```text
说明正确资料经常能进入前 5 条，但排得不够靠前。
```

可能需要关注：

```text
rerank
hybrid fusion 权重
向量模型质量
query rewrite 质量
```

## 自测题

### 自测 1：Top-K 的 K 越大越好吗？

答案：

不是。

K 变大可能提高 Recall，但也可能降低 Precision，引入更多噪声、成本和安全风险。

### 自测 2：Hit@K 和 Hit Rate@K 有什么区别？

答案：

`Hit@K` 是单个样本是否命中，结果通常是 0 或 1。

`Hit Rate@K` 是一组样本的命中比例。

### 自测 3：Recall@K 主要衡量什么？

答案：

它衡量应该找回的正确资料里，前 K 条找回来了多少。

### 自测 4：Precision@K 主要衡量什么？

答案：

它衡量前 K 条检索结果里，有多少条是真正相关的。

### 自测 5：为什么检索指标不能替代回答质量评测？

答案：

因为检索指标只看资料是否找对，不看模型是否正确理解资料、是否引用准确、是否拒答合理、是否产生幻觉。

### 自测 6：为什么 `security_block` 样本不应该直接混进普通检索指标？

答案：

因为它的目标不是找到资料并回答，而是识别安全风险并阻断。

它应该由安全评测指标处理，而不是普通 Hit Rate、Recall、Precision。

## 本节小结

本节学的是 RAG 检索质量的基础指标：

```text
Top-K：看前 K 条。
Hit@K：单个样本前 K 条是否命中至少一个正确资料。
Hit Rate@K：一组样本的命中比例。
Recall@K：应该找的资料找回了多少。
Precision@K：前 K 条里相关资料占多少。
MRR@K：第一个正确资料排得靠不靠前。
```

你现在要形成一个关键判断：

```text
检索指标只能评价检索，不评价最终回答。
```

下一节会继续学习：

```text
回答质量评测：正确性、引用一致性、拒答合理性。
```

到那时，我们会把“资料有没有找对”和“模型有没有答对”分开看。
