# 阶段 9 第 7 节：Rerank 进阶：召回后为什么还要重排序

## 本节定位

本节学习 RAG 检索质量优化里的关键能力：

```text
Rerank，重排序。
```

前面几节我们已经学了：

```text
第 2 节 Query Rewrite：
把用户原始问题改写成更适合检索的 query。

第 3 节 Multi Query：
从一个问题扩展出多个检索角度。

第 4 节 Query Intent：
先判断问题是否应该进入 RAG。

第 5 节 Hybrid Search：
把向量检索和关键词检索融合。

第 6 节 Score / Distance / Similarity：
理解不同检索分数的方向、含义和阈值比较。
```

现在我们已经可以从知识库里召回一批候选 chunk。

但真实 RAG 项目里，召回出来的顺序不一定就是最终最适合给模型的顺序。

这就是本节要解决的问题：

```text
召回结果已经有了，为什么还要再排一次？
```

一句话说：

```text
召回负责“把可能有用的资料找出来”，rerank 负责“在候选资料里重新判断谁最适合回答当前问题”。
```

## 本节学习目标

学完本节，你要能做到：

1. 能解释什么是 rerank。
2. 能说清楚召回和重排序的区别。
3. 能解释为什么向量检索、关键词检索、Hybrid Search 后还需要 rerank。
4. 能理解粗召回、精排、上下文构造之间的分工。
5. 能说清楚 rerank 能解决什么问题，不能解决什么问题。
6. 能区分 `retrieval_score` 和 `rerank_score`。
7. 能看懂当前项目的 `RerankCandidate`、`RerankedChunk`、`RerankScoreBreakdown`。
8. 能理解本节新增的 `RerankReport`。
9. 能理解为什么 rerank 归一化要考虑上一节的 score direction。
10. 能解释为什么本节不接真实 rerank 模型。

## 本节新增和修改

本节新增：

```text
notes/stage9-07-rerank-advanced.md
```

本节修改：

```text
projects/ai-service/app/rag/rerank.py
projects/ai-service/tests/test_rag_rerank.py
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

本节没有：

- 启动 VMware Ubuntu。
- 启动 Qdrant。
- 启动 Milvus。
- 调用真实 rerank 模型。
- 调用真实大模型。
- 新增手动测试文档。

原因是本节重点是 rerank 的原理、边界、解释报告和分数方向，不需要外部服务。

## 一句话先讲透

Rerank 的核心是：

```text
先用便宜、快、覆盖面大的方法召回一批候选，再用更精细的相关性判断把候选重新排序。
```

更具体一点：

```text
检索阶段问：哪些 chunk 可能相关？
Rerank 阶段问：这些候选 chunk 里，哪些最能回答当前问题？
```

这两个问题不一样。

所以检索分数高，不代表最终一定应该排第一。

## 基础知识铺垫

### 1. 什么是召回

召回就是从大量资料中找出候选。

在 RAG 里，召回通常发生在这里：

```text
用户问题
-> query rewrite
-> multi query
-> vector search / keyword search / hybrid search
-> 候选 chunk
```

召回的目标是：

```text
不要漏掉可能有用的资料。
```

所以召回阶段更看重覆盖面。

它会尽量从海量文档中快速拿到 top_k 或 top_n 个候选。

### 2. 什么是排序

排序就是给候选结果排前后。

在检索系统里，排序可以发生多次。

第一次排序通常来自检索器本身。

比如：

```text
向量数据库按向量相似度排序。
关键词检索按关键词命中分数排序。
Hybrid Search 按融合分数排序。
```

但这个排序只是初步排序。

它不一定真正等于：

```text
最适合回答当前用户问题的顺序。
```

### 3. 什么是 rerank

Rerank 就是：

```text
对已经召回的一批候选结果重新排序。
```

它不是从全量知识库里重新搜索。

它只处理候选集。

典型流程是：

```text
先召回 top 20
-> rerank
-> 选 rerank 后 top 5
-> 放进模型上下文
```

所以 rerank 不是替代检索。

它是检索后的精排阶段。

### 4. 粗召回和精排

真实检索系统经常分两层：

```text
粗召回
精排
```

粗召回负责：

- 快。
- 覆盖面大。
- 从大量数据中捞出候选。
- 可以接受一定噪声。

精排负责：

- 慢一点也可以。
- 只处理少量候选。
- 更精细判断问题和候选的匹配程度。
- 把真正有用的结果排到前面。

RAG 里的 rerank 就是精排的一种。

### 5. 为什么向量检索后还需要 rerank

向量检索擅长语义相似。

但它有几个问题。

第一，相似不等于能回答。

比如用户问：

```text
退款多久到账？
```

向量检索可能召回：

```text
退款申请条件
退款到账时间
退款失败处理
退货运费规则
```

这些都和“退款”相关。

但真正能回答“多久到账”的是：

```text
退款到账时间
```

向量检索可能把“退款申请条件”排得很前，因为主题相似。

Rerank 要进一步判断：

```text
哪个 chunk 更直接回答“多久到账”。
```

第二，向量检索对细粒度条件不一定敏感。

比如：

```text
质量问题退货运费谁承担？
个人原因退货运费谁承担？
```

两句话都和退货运费相关，但条件完全不同。

向量检索可能把两个规则都召回。

Rerank 要把更符合当前条件的 chunk 排前面。

第三，向量检索分数只是召回信号。

它通常不是最终答案相关性评分。

### 6. 为什么关键词检索后还需要 rerank

关键词检索擅长字面命中。

但字面命中也不等于能回答。

比如用户问：

```text
退货运费谁承担？
```

很多 chunk 都可能命中：

```text
退货
运费
承担
```

但它们可能讲不同场景：

```text
质量问题
个人原因
商家发错货
特殊活动
```

关键词检索可能只看命中词，不理解问题真正需要哪个条件。

Rerank 要进一步看：

```text
当前问题里的条件和 chunk 内容是否匹配。
```

### 7. 为什么 Hybrid Search 后还需要 rerank

Hybrid Search 已经比单一路径更强。

它能结合：

```text
向量语义召回
关键词字面召回
```

但 Hybrid Search 仍然是召回和初步融合。

它可能解决：

```text
能不能找到更多可能相关的 chunk。
```

但不一定解决：

```text
哪个 chunk 最适合最终回答。
```

原因是 Hybrid Search 的融合分数通常比较粗。

例如：

```text
hybrid_score = normalized_vector_score * 0.7 + normalized_keyword_score * 0.3
```

这个公式没有真正逐句判断：

```text
这个 chunk 是否直接回答了用户问题。
```

Rerank 的价值就是在候选里做更细的判断。

### 8. Rerank 能解决什么

Rerank 主要能解决排序问题。

比如：

```text
正确 chunk 已经被召回，但排得不够靠前。
```

这时 rerank 有用。

Rerank 还能缓解：

- 向量结果主题相关但答案不直接的问题。
- 关键词结果字面命中但上下文不匹配的问题。
- Hybrid Search 融合分数粗糙的问题。
- 多个候选 chunk 都相关但优先级不同的问题。
- top_k 太大时上下文筛选的问题。

### 9. Rerank 不能解决什么

Rerank 不是万能的。

它不能解决：

```text
正确 chunk 根本没被召回。
```

如果正确资料不在候选集里，rerank 看不到它。

所以：

```text
召回漏了，rerank 救不了。
```

Rerank 也不能解决：

- 知识库没有这条资料。
- 文档内容本身错误。
- metadata 权限过滤把正确资料过滤掉。
- query intent 路由错了。
- 用户问题需要业务工具而不是 RAG。
- 最终生成阶段不遵守引用。

所以排查 RAG 问题时，要先判断：

```text
是召回问题，还是排序问题？
```

### 10. 如何判断是召回问题还是排序问题

一个简单判断方法：

```text
看正确 chunk 是否出现在候选集里。
```

如果没有出现：

```text
召回问题。
```

可能要查：

- Query Rewrite 是否改错。
- Multi Query 是否覆盖不够。
- 向量库是否有数据。
- embedding 是否一致。
- metadata filter 是否过严。
- top_k 是否太小。
- Hybrid Search 是否启用关键词补召回。

如果正确 chunk 出现了，但排得靠后：

```text
排序问题。
```

可能要查：

- 融合权重是否合理。
- score 方向是否理解错。
- rerank 是否启用。
- rerank 模型或规则是否合适。
- 上下文构造是否截断了正确资料。

### 11. Rerank 和 score_threshold 的关系

`score_threshold` 是召回阶段过滤。

Rerank 是候选排序阶段。

如果 threshold 太严，正确 chunk 进不了候选集。

这时 rerank 没机会发挥作用。

如果 threshold 太松，候选集噪声多。

这时 rerank 压力会变大。

所以常见策略是：

```text
召回阶段不要过早杀掉可能有用的结果。
Rerank 阶段再从候选中选更好的。
```

但这不是说 threshold 越松越好。

太松会增加成本和延迟。

真实系统要靠评测找到平衡。

### 12. Rerank 和 top_k 的关系

召回 top_k 和最终上下文 top_k 通常不是一个值。

常见做法：

```text
retrieval_top_k = 20
rerank_top_k = 5
```

意思是：

```text
先多召回一些候选。
再通过 rerank 选出最好的几个。
```

如果召回 top_k 太小，正确 chunk 可能进不来。

如果最终 top_k 太大，上下文噪声会多，token 成本也高。

Rerank 的价值就在于：

```text
允许召回阶段稍微放宽，再在精排阶段收紧。
```

### 13. Rerank 分数和检索分数的区别

检索分数，比如：

```text
vector_score
keyword_score
hybrid_score
```

主要来自召回阶段。

它回答：

```text
检索器为什么把这个 chunk 找出来？
```

Rerank 分数回答：

```text
在这批候选里，这个 chunk 是否更适合回答当前问题？
```

所以：

```text
retrieval_score != rerank_score
```

它们不应该直接混用。

### 14. Rerank 模型是什么

真实项目里，rerank 可以由专门模型完成。

常见形式是：

```text
输入：query + candidate chunk
输出：相关性分数
```

这种模型通常比纯向量检索更精细，因为它可以同时看 query 和 chunk 的文本。

但它也更慢、更贵。

所以通常只给少量候选做 rerank。

### 15. 为什么本节不接真实 rerank 模型

因为我们现在学习的是 rerank 的基础边界。

如果直接接真实模型，你容易只记住 API 调用，而没有理解：

- 召回和精排的分工。
- Rerank 能解决什么。
- Rerank 不能解决什么。
- Rerank 分数和检索分数的区别。
- score direction 对归一化的影响。
- bad case 中怎么判断 rerank 是否有效。

所以本节继续用规则版 reranker。

等这些概念清楚后，再接真实 rerank 模型才有意义。

## 本节主题系统讲解

### 1. 当前项目已有的 rerank 基础

当前文件：

```text
projects/ai-service/app/rag/rerank.py
```

已有核心结构：

```text
RerankCandidate
RerankScoreBreakdown
RerankedChunk
Reranker
RuleBasedReranker
rerank_candidates()
format_reranked_chunks_for_debug()
```

这些结构说明项目已经有了一个学习版 rerank。

它不是调用真实模型，而是用规则评分模拟 rerank 思路。

### 2. `RerankCandidate` 是什么

`RerankCandidate` 是 rerank 的输入。

它表达：

```text
已经被召回出来，等待重新排序的候选 chunk。
```

字段包括：

| 字段 | 含义 |
| --- | --- |
| `chunk_id` | chunk 稳定 ID |
| `content` | chunk 正文 |
| `metadata` | 来源、标题、章节等 |
| `retrieval_score` | 召回阶段分数 |
| `retrieval_sources` | 来自 vector、keyword、hybrid 等 |
| `matched_terms` | 关键词命中的词 |

这里最重要的是：

```text
RerankCandidate 不是从数据库直接来的原始对象。
它是把不同召回来源统一成 rerank 可以处理的输入格式。
```

### 3. 为什么要有多个 make 函数

项目里有：

```text
make_rerank_candidates_from_retrieved_chunks()
make_rerank_candidates_from_keyword_results()
make_rerank_candidates_from_hybrid_results()
```

原因是候选可能来自不同召回器。

向量检索返回：

```text
RetrievedChunk
```

关键词检索返回：

```text
KeywordSearchResult
```

Hybrid Search 返回：

```text
HybridSearchResult
```

Rerank 不应该关心上游具体类型。

它只需要统一的：

```text
RerankCandidate
```

这就是适配层的意义。

### 4. `RerankScoreBreakdown` 是什么

`RerankScoreBreakdown` 是评分拆解。

当前包括：

```text
content_match_score
title_section_match_score
normalized_retrieval_score
source_agreement_score
```

它的作用是让 rerank 可解释。

如果只返回：

```text
rerank_score = 0.82
```

你不知道为什么是 0.82。

有 breakdown 后，你可以看到：

```text
正文匹配多少
标题章节匹配多少
原始检索分数贡献多少
是否多来源共同命中
```

### 5. 当前规则版 rerank 的评分思路

当前权重是：

```text
CONTENT_MATCH_WEIGHT = 0.55
TITLE_SECTION_MATCH_WEIGHT = 0.2
RETRIEVAL_SCORE_WEIGHT = 0.15
SOURCE_AGREEMENT_WEIGHT = 0.1
```

意思是：

```text
更重视 chunk 内容是否直接匹配问题。
其次看标题和章节。
再参考召回阶段分数。
最后给多来源命中一点加分。
```

这很符合 rerank 思路。

因为 rerank 不应该只重复相信检索分数。

如果 rerank 只看 retrieval_score，那它就没有重新排序的意义。

### 6. 为什么 retrieval_score 权重只有 0.15

因为 retrieval_score 是上游信号。

它有价值，但不是最终判断。

如果 retrieval_score 权重太高，rerank 会变成：

```text
基本保持原始检索顺序。
```

这样就无法把“原来排第二但更能回答问题”的 chunk 提上来。

当前规则版把正文匹配放得更重，是为了表达：

```text
Rerank 要更关注候选内容和当前问题的直接关系。
```

### 7. 为什么要记录 original_rank 和 rerank_rank

Rerank 最重要的可观测点之一是：

```text
排名有没有发生变化。
```

所以 `RerankedChunk` 里有：

```text
original_rank
rerank_rank
```

如果：

```text
original_rank = 5
rerank_rank = 1
```

说明 rerank 把原本排第 5 的 chunk 提到了第 1。

这可能是好事。

但也可能是坏事。

要结合评测看它是不是把正确 chunk 提上来了。

### 8. 本节新增 `RerankReport`

本节新增：

```text
RerankReport
```

它是 rerank 的整体报告。

字段包括：

| 字段 | 含义 |
| --- | --- |
| `query` | 本次 rerank 的 query |
| `top_k` | 最终返回多少条 |
| `candidate_count` | 输入候选数量 |
| `returned_count` | rerank 后返回数量 |
| `top_before_chunk_id` | rerank 前排第一的 chunk |
| `top_after_chunk_id` | rerank 后排第一的 chunk |
| `moved_count` | 返回结果里排名发生变化的数量 |
| `promoted_chunk_ids` | 被提升排名的 chunk |
| `dropped_chunk_ids` | 因 top_k 截断没有返回的 chunk |
| `retrieval_score_direction` | 上游检索分数方向 |
| `results` | rerank 后结果 |
| `debug_lines` | 调试输出 |

它回答的是：

```text
这次 rerank 到底改变了什么？
```

### 9. 为什么报告里要有 top_before 和 top_after

这是最直观的 rerank 效果。

如果：

```text
top_before_chunk_id == top_after_chunk_id
```

说明 rerank 没有改变第一名。

这不一定有问题。

可能原始检索第一名本来就很好。

如果：

```text
top_before_chunk_id != top_after_chunk_id
```

说明 rerank 改变了最终最重要的上下文候选。

这时要重点检查：

```text
它是不是把正确 chunk 提上来了？
```

### 10. 为什么报告里要有 promoted_chunk_ids

`promoted_chunk_ids` 表示被提升的 chunk。

例如：

```text
原来第 2，rerank 后第 1。
```

这能帮助你分析：

```text
rerank 具体在帮谁。
```

如果正确 chunk 经常出现在 promoted 里，说明 rerank 对排序有帮助。

如果错误 chunk 经常被 promoted，就说明 rerank 规则或模型有问题。

### 11. 为什么报告里要有 dropped_chunk_ids

Rerank 后通常只返回 top_k。

比如输入 20 个候选，输出 5 个。

被截断的 15 个就是 dropped。

如果正确 chunk 被 dropped，说明：

```text
rerank 把正确资料排出最终上下文了。
```

这就是严重问题。

所以 dropped 不是无关信息。

它对 bad case 分析很重要。

### 12. 本节为什么接入 RetrievalScoreMeaning

上一节我们学了：

```text
有的分数越大越好。
有的 distance 越小越好。
```

当前 rerank 里有一个字段：

```text
normalized_retrieval_score
```

如果上游 retrieval_score 是 Cosine similarity，越大越好。

可以用：

```text
score / max_score
```

但如果上游 retrieval_score 是 L2 distance，越小越好。

就不能这样做。

否则 distance=0.9 会比 distance=0.2 得到更高的归一化分数。

这正好是错的。

所以本节让 `rerank_candidates()` 支持：

```text
retrieval_score_meaning
```

如果传入 lower-is-better 的解释对象，就按距离方向归一化。

### 13. lower-is-better 怎么归一化

假设候选 distance 是：

```text
near = 0.2
far = 0.9
```

L2 下，0.2 更好。

归一化后应该是：

```text
near -> 1
far -> 0
```

本节使用的思路是：

```text
1 - ((score - min_score) / (max_score - min_score))
```

它把最小 distance 映射为 1，把最大 distance 映射为 0。

这符合：

```text
越小越相关。
```

### 14. 为什么默认仍然是 higher-is-better

为了兼容已有项目。

当前大多数路径里，进入 rerank 的 retrieval_score 来自：

```text
vector score
keyword score
hybrid_score
```

这些在当前学习实现里多数是 higher-is-better。

所以默认保持：

```text
higher_is_better
```

只有当你明确知道上游是 L2 distance 这种 lower-is-better 时，才传入：

```text
describe_milvus_score("L2")
```

### 15. Rerank 的 debug line 怎么看

当前 debug line 类似：

```text
1. rerank_score=0.8300 original_rank=2 retrieval_score=0.7200 content_match=0.9000 title_section_match=1.0000 sources=vector source=refund.md section=退款到账 chunk_id=chunk-a matched=退款,到账
```

你要看这些点：

- `rerank_score`：重排后的分数。
- `original_rank`：召回阶段原始排名。
- `retrieval_score`：召回阶段分数。
- `content_match`：正文和 query 匹配程度。
- `title_section_match`：标题/章节匹配程度。
- `sources`：候选来自哪里。
- `chunk_id`：具体是哪条 chunk。
- `matched`：命中了哪些 query 词。

如果 `original_rank=5` 但 rerank 后排第 1，说明 rerank 产生了明显影响。

这时要检查它是不是正确影响。

## 本节代码讲解

### 1. `RerankReport`

新增结构：

```python
class RerankReport(BaseModel):
    query: str
    top_k: int
    candidate_count: int
    returned_count: int
    top_before_chunk_id: str | None
    top_after_chunk_id: str | None
    moved_count: int
    promoted_chunk_ids: list[str]
    dropped_chunk_ids: list[str]
    retrieval_score_direction: str
    results: list[RerankedChunk]
    debug_lines: list[str]
```

这个报告不是给最终用户看的。

它是给开发者做调试、评测、bad case 分析看的。

它能快速回答：

```text
rerank 前后第一名是否变化？
哪些 chunk 被提升？
哪些 chunk 被截断？
输入多少候选，输出多少结果？
上游 retrieval_score 是按什么方向理解的？
```

### 2. `build_rerank_report()`

这个函数先调用：

```text
rerank_candidates()
```

得到真实 rerank 结果。

然后统计：

```text
returned_chunk_ids
promoted_chunk_ids
dropped_chunk_ids
moved_count
top_before_chunk_id
top_after_chunk_id
```

它不重新写一套 rerank 逻辑。

这是一个好习惯：

```text
报告应该解释真实逻辑，而不是复制真实逻辑。
```

如果报告复制了一套排序算法，以后就可能和真实 rerank 不一致。

### 3. `retrieval_score_meaning`

本节给：

```text
Reranker.rerank()
RuleBasedReranker.rerank()
rerank_candidates()
build_rerank_report()
```

都加了可选参数：

```text
retrieval_score_meaning
```

它的作用是告诉 rerank：

```text
上游 retrieval_score 应该按什么方向理解。
```

如果不传，默认按：

```text
higher_is_better
```

如果传：

```python
describe_milvus_score("L2")
```

就按：

```text
lower_is_better
```

归一化。

### 4. `_normalize_score()` 的变化

旧逻辑只适合 higher-is-better：

```text
score / max_score
```

新逻辑多了 lower-is-better 分支：

```text
如果 direction 是 lower_is_better：
    最小值归一化为 1
    最大值归一化为 0
```

这不是为了支持复杂数学。

它是为了避免概念错误：

```text
不要把 distance 大的结果当成更好。
```

### 5. 本节新增测试

本节新增两个重点测试。

第一个测试：

```text
test_rerank_candidates_can_normalize_lower_is_better_retrieval_scores
```

它验证：

```text
L2 distance 0.2 比 0.9 更相关。
```

第二个测试：

```text
test_build_rerank_report_summarizes_rank_changes
```

它验证：

```text
RerankReport 能记录 top_before、top_after、promoted、dropped 和 debug_lines。
```

这两个测试都不是为了模拟真实大模型。

它们是为了固定 rerank 的工程边界。

## 真实项目中的 Rerank 设计

### 1. Rerank 放在哪里

典型位置：

```text
用户问题
-> Query Intent
-> Query Rewrite
-> Multi Query
-> Hybrid Search
-> Rerank
-> Context Compression
-> LLM 生成
-> Citation Check
```

Rerank 一般放在召回之后、上下文构造之前。

原因是：

```text
它要决定哪些 chunk 最值得进入上下文。
```

### 2. Rerank 输入多少候选合适

没有固定值。

常见思路：

```text
先召回 20 到 50 个候选。
再 rerank 取前 3 到 8 个。
```

但这要看：

- 文档 chunk 长度。
- 模型上下文窗口。
- 业务问题复杂度。
- 延迟要求。
- rerank 模型成本。
- 评测集表现。

学习阶段不要死记数字。

要记住原则：

```text
召回候选要足够覆盖，最终上下文要足够干净。
```

### 3. Rerank 会增加成本

真实 rerank 模型通常需要逐个判断：

```text
query + candidate chunk
```

如果候选很多，成本和延迟会上升。

所以 rerank 不是越多越好。

它要和：

- top_k
- cache
- batch
- timeout
- fallback
- 评测收益

一起设计。

### 4. Rerank 失败怎么办

真实项目里 rerank 可能失败。

比如：

- 模型超时。
- 模型服务不可用。
- 输入太长。
- 返回格式异常。
- 成本保护触发。

常见 fallback 是：

```text
使用原始检索顺序。
```

也可以使用：

```text
规则版 rerank
```

作为轻量兜底。

这就是为什么我们现在保留 rule-based reranker。

它不只是学习工具，也可以作为 fallback 思路。

### 5. 如何评估 rerank 有没有用

不能只看单条样例。

应该看评测集。

常见方法：

```text
比较 rerank 前后正确 chunk 的排名。
```

比如：

```text
原始检索 correct chunk 平均排名：6.2
Rerank 后 correct chunk 平均排名：2.1
```

这说明 rerank 有帮助。

还可以看：

- Hit Rate@K 是否提升。
- MRR 是否提升。
- 答案正确率是否提升。
- 引用准确率是否提升。
- no-context 是否减少。
- bad case 是否减少。

### 6. Rerank 可能带来的风险

Rerank 不是一定提升。

它也可能：

- 把正确 chunk 排低。
- 过度偏好表面关键词。
- 被 prompt injection 文档影响。
- 对长 chunk 判断不稳定。
- 增加延迟和成本。
- 和 metadata 权限逻辑耦合不清。

所以 rerank 必须可观测。

本节新增 `RerankReport` 就是为了让它不黑盒。

## 常见误区

### 误区 1：Rerank 可以替代召回

不能。

Rerank 只看候选集。

正确 chunk 没被召回，rerank 就看不到。

### 误区 2：检索分数最高的一定最适合回答

不一定。

检索分数高可能只是主题相似。

Rerank 要判断是否直接回答当前问题。

### 误区 3：Hybrid Search 后就不需要 Rerank

不一定。

Hybrid Search 主要提高召回稳定性。

Rerank 主要提高候选排序质量。

它们是配合关系。

### 误区 4：Rerank 分数可以和向量分数直接比较

不能。

Rerank 分数和向量分数来自不同阶段、不同计算方式。

### 误区 5：Rerank 后只看最终答案

不够。

还要看：

- top_before
- top_after
- promoted
- dropped
- original_rank
- rerank_rank
- score_breakdown

否则很难定位问题。

### 误区 6：Rerank 一定要用大模型

不一定。

Rerank 可以是：

- 规则版。
- 传统机器学习模型。
- Cross-encoder rerank 模型。
- LLM rerank。
- 多信号融合排序。

学习阶段用规则版，是为了先把边界搞清楚。

## 本节练习

### 练习 1：判断问题类型

问题：

```text
正确 chunk 已经在召回结果第 8 名，但最终上下文只取前 5 个，所以回答错了。这是召回问题还是排序问题？
```

参考答案：

```text
更偏排序问题。正确 chunk 已经被召回，但排名太靠后，没有进入最终上下文。可以考虑 rerank、调整融合权重或增加最终上下文 top_k。
```

### 练习 2：判断 Rerank 是否能解决

问题：

```text
知识库里根本没有“特殊活动退款规则”这条资料，rerank 能解决吗？
```

参考答案：

```text
不能。Rerank 只能重新排序已经召回的候选，不能创造知识库里不存在的资料。
```

### 练习 3：解释为什么需要 Rerank

问题：

```text
Hybrid Search 已经融合了关键词和向量结果，为什么还可能需要 rerank？
```

参考答案：

```text
Hybrid Search 主要解决多路召回和初步融合，它不一定能精细判断哪个 chunk 最能直接回答问题。Rerank 在候选集里进一步判断 query 和 chunk 的匹配程度，可以把更直接回答问题的 chunk 提到前面。
```

### 练习 4：区分分数

问题：

```text
retrieval_score 和 rerank_score 有什么区别？
```

参考答案：

```text
retrieval_score 是召回阶段的分数，比如向量相似度、关键词命中分或 hybrid_score。rerank_score 是对候选重新排序后得到的相关性分数。它们处在不同阶段，不能直接混为一谈。
```

### 练习 5：解释 original_rank 和 rerank_rank

问题：

```text
original_rank=6，rerank_rank=2 说明什么？
```

参考答案：

```text
说明这个 chunk 在原始召回里排第 6，但经过 rerank 后排第 2，被明显提升。需要看它是否是正确 chunk，如果是，说明 rerank 有帮助。
```

### 练习 6：解释 dropped

问题：

```text
如果正确 chunk 出现在 dropped_chunk_ids 里，说明什么？
```

参考答案：

```text
说明正确 chunk 被 rerank 后的 top_k 截断掉了，没有进入最终结果。这通常意味着 rerank 排序有问题，或者 top_k 设置太小。
```

### 练习 7：解释 lower-is-better

问题：

```text
L2 distance 进入 rerank 时，为什么不能直接用 score / max_score？
```

参考答案：

```text
因为 L2 是越小越相关。如果直接用 score / max_score，距离越大的结果反而归一化分越高，会把远的结果当成更好。需要按 lower-is-better 的方向反向归一化。
```

### 练习 8：解释本节为什么不接真实模型

问题：

```text
为什么本节仍然用规则版 reranker，而不是直接接真实 rerank 模型？
```

参考答案：

```text
因为本节目标是学清楚 rerank 的位置、作用、边界、分数区别、报告和调试方法。如果直接接模型，容易只学 API 调用，而没有理解召回和精排的本质。真实模型接入适合在这些基础清楚后再做。
```

## 自测题

### 自测 1：Rerank 是什么？

参考答案：

```text
Rerank 是对已经召回的一批候选结果重新排序，让更适合回答当前问题的 chunk 排到前面。
```

### 自测 2：Rerank 替代检索吗？

参考答案：

```text
不替代。检索负责从大量文档中找候选，rerank 只对候选集重新排序。
```

### 自测 3：Rerank 最适合解决什么问题？

参考答案：

```text
最适合解决正确 chunk 已经被召回但排名不够靠前的问题。
```

### 自测 4：Rerank 解决不了什么问题？

参考答案：

```text
解决不了正确资料没有被召回、知识库没有资料、权限过滤错误、意图路由错误、文档内容错误等问题。
```

### 自测 5：为什么召回 top_k 和最终 top_k 可以不同？

参考答案：

```text
召回 top_k 可以更大，用来提高候选覆盖面；最终 top_k 可以更小，用来控制上下文噪声和 token 成本。Rerank 负责从较大的候选集中选出更好的少量结果。
```

### 自测 6：`RerankScoreBreakdown` 有什么价值？

参考答案：

```text
它把 rerank_score 拆成正文匹配、标题章节匹配、归一化检索分数、多来源命中等部分，让重排序结果可解释。
```

### 自测 7：`RerankReport` 有什么价值？

参考答案：

```text
它总结一次 rerank 前后排名变化，包括第一名变化、候选数量、返回数量、被提升 chunk、被截断 chunk 和 debug lines，方便 bad case 分析。
```

### 自测 8：为什么 rerank 要考虑 retrieval_score_direction？

参考答案：

```text
因为上游 retrieval_score 可能是 similarity，也可能是 distance。similarity 通常越大越好，distance 通常越小越好。如果不考虑方向，L2 distance 这类分数会被错误归一化。
```

### 自测 9：规则版 reranker 和真实 rerank 模型有什么区别？

参考答案：

```text
规则版 reranker 用人工规则和权重模拟排序逻辑，便于学习和测试；真实 rerank 模型会直接判断 query 和 candidate 的相关性，通常效果更强但成本和延迟更高。
```

### 自测 10：Rerank 后还需要引用校验吗？

参考答案：

```text
需要。Rerank 只是让候选排序更合理，不能保证最终回答一定严格来自引用内容。后面还需要 citation check 来检查回答和来源是否一致。
```

### 自测 11：Rerank 是否一定提升效果？

参考答案：

```text
不一定。错误的 rerank 规则或模型可能把正确 chunk 排低，所以必须通过评测集和 bad case 分析验证。
```

### 自测 12：Rerank 失败时可以怎么兜底？

参考答案：

```text
可以退回原始检索顺序，也可以使用规则版 reranker 作为轻量兜底，具体要结合业务容忍度、延迟和安全要求设计。
```

## 面试表达

### 1 分钟版本

```text
Rerank 是 RAG 里召回之后的精排步骤。向量检索、关键词检索和 Hybrid Search 主要解决把可能相关的 chunk 找出来，但它们的排序不一定等于最终最能回答问题的顺序。Rerank 会对候选 chunk 重新计算相关性，把更直接回答用户问题的内容排到前面。它适合解决“正确 chunk 已召回但排名靠后”的问题，但不能解决正确 chunk 根本没召回或知识库没有资料的问题。在工程里我会记录 original_rank、rerank_rank、score_breakdown、promoted 和 dropped，避免 rerank 变成黑盒。
```

### 3 分钟版本

```text
在 RAG 系统里，我会把召回和重排序分开看。召回阶段用向量检索、关键词检索或 Hybrid Search 从大量文档里找候选，它的目标是覆盖正确资料；Rerank 阶段只处理这些候选，用更精细的相关性判断重新排序，它的目标是让最能回答当前问题的 chunk 进入最终上下文。

Rerank 能解决的是排序问题，比如正确 chunk 已经在 top 20 里，但原始检索只排第 8，而最终上下文只取前 5，这时 rerank 可以把它提上来。它解决不了召回问题，如果正确 chunk 根本没进候选集，rerank 无法凭空找到。

工程上我不会只看 rerank 后答案是否正确，还会记录 original_rank、rerank_rank、top_before、top_after、promoted_chunk_ids、dropped_chunk_ids 和 score_breakdown。这样 bad case 出现时，可以判断 rerank 是帮了忙还是把正确资料排掉了。另外，rerank 使用 retrieval_score 时还要理解上游分数方向，比如 L2 distance 是越小越好，不能按越大越好归一化。真实项目里可以接专门的 rerank 模型，但也要考虑成本、延迟、fallback 和评测收益。
```

## 本节小结

本节真正要掌握的是：

```text
Rerank 不是再检索一次。
Rerank 是对候选结果重新排序。
它主要解决正确资料已召回但排序不够靠前的问题。
它不能解决正确资料没召回的问题。
```

本节代码补了两个重要工程能力：

```text
1. RerankReport：让一次 rerank 的排名变化可解释。
2. retrieval_score_meaning：让 rerank 归一化时尊重上游分数方向。
```

下一节继续：

```text
阶段 9 第 8 节：真实 Rerank 模型接入
```

下一节会在本节理解清楚的基础上，再看真实 rerank 模型应该怎么接、怎么测试、怎么保留 fake 版本、怎么避免自动化测试真实调用模型。
