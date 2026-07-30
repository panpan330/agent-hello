# 阶段 9 第 6 节：检索分数理解：score、distance、相似度到底怎么看

## 本节定位

本节学习 RAG 检索调优里非常容易被忽略、但真实项目一定会遇到的问题：

```text
检索分数到底代表什么？
```

上一节我们学了 Hybrid Search：

```text
关键词检索 + 向量检索 -> 去重 -> 归一化 -> 加权融合 -> 排序
```

那一节已经开始出现多个分数：

```text
vector_score
keyword_score
hybrid_score
```

但这里有一个关键问题：

```text
这些分数真的能直接比较吗？
```

答案是：

```text
不能直接比较。
```

而且更麻烦的是：

```text
有的分数越大越相关。
有的 distance 越小越相关。
有的字段名字叫 distance，但在某些 metric 下又表现得像 similarity。
有的 score 范围是 -1 到 1。
有的 score 没有固定上限。
有的 threshold 应该用 >=。
有的 threshold 应该用 <=。
```

如果这些概念没学清楚，后面做 `score_threshold`、Hybrid Search 权重、Rerank、评测、bad case 分析时就会靠猜。

本节的核心目标是让你建立一个稳定判断方式：

```text
看到一个检索分数，先问它来自哪里、使用什么 metric、分数方向是什么、阈值应该怎么比较、能不能和别的分数横向比较。
```

## 本节学习目标

学完本节，你要能做到：

1. 能解释 `score`、`distance`、`similarity` 三个词的区别。
2. 能说清楚“越大越相关”和“越小越相关”的差异。
3. 能理解 Cosine、Dot Product、Euclidean/L2、Manhattan 的基础含义。
4. 能解释为什么 Qdrant、Milvus、关键词检索、Hybrid Search 的分数不能混着比较。
5. 能解释为什么 `score_threshold` 不能随便抄别人的值。
6. 能理解为什么同一个阈值换 embedding 模型、换向量库、换 metric 后可能失效。
7. 能看懂本节新增的 `RetrievalScoreMeaning`。
8. 能理解为什么 Milvus L2 阈值是 `score <= threshold`，而 COSINE/IP 是 `score >= threshold`。
9. 能用“分数解释层”的思路讲清楚 RAG 检索调试。
10. 能为后续 Rerank 和评测学习打基础。

## 本节新增和修改

本节新增：

```text
projects/ai-service/app/rag/score_interpretation.py
projects/ai-service/tests/test_rag_score_interpretation.py
notes/stage9-06-retrieval-score-distance-similarity.md
```

本节修改：

```text
projects/ai-service/app/rag/milvus_store.py
projects/ai-service/app/rag/documents.py
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

本节没有：

- 启动 VMware Ubuntu。
- 启动 Qdrant。
- 启动 Milvus。
- 调用真实 embedding 模型。
- 调用真实大模型。
- 新增手动测试文档。

原因是本节重点是分数语义和阈值方向，不需要外部服务。

## 一句话先讲透

检索分数不能只看数字大小。

你必须先知道：

```text
这个数字是 similarity，还是 distance？
它来自哪个后端？
它使用什么 metric？
越大越相关，还是越小越相关？
threshold 应该用 >=，还是 <=？
```

如果这个问题不先回答，`score_threshold=0.8` 就只是一个看起来专业但不一定正确的魔法数字。

## 基础知识铺垫

### 1. 什么是 score

`score` 是一个很泛的词。

它只表示：

```text
系统给某个结果打出来的一个数。
```

但它不保证一定是“相似度”。

也不保证一定是“越大越好”。

也不保证不同系统里的 `score=0.8` 含义一样。

在 RAG 里，`score` 可能来自：

- 向量数据库。
- 关键词检索器。
- Hybrid Search 融合公式。
- Rerank 模型。
- 评测脚本。
- 自定义业务规则。

所以看到 `score` 的第一反应不应该是：

```text
0.8 很高。
```

而应该是：

```text
这是哪个系统的 score？
用的是什么 metric？
这个 score 的方向是什么？
```

### 2. 什么是 similarity

`similarity` 是相似度。

它表达的是：

```text
两个对象有多像。
```

通常情况下，相似度是：

```text
越大越相似。
```

比如 Cosine Similarity：

```text
1    表示方向非常接近
0    表示大致正交
-1   表示方向相反
```

在语义检索里，如果两个文本的向量方向接近，通常说明它们语义接近。

所以对于 similarity-style 分数，阈值通常是：

```text
score >= threshold
```

比如：

```text
只保留 score >= 0.8 的结果。
```

### 3. 什么是 distance

`distance` 是距离。

它表达的是：

```text
两个对象离得有多远。
```

通常情况下，距离是：

```text
越小越相似。
```

比如 Euclidean Distance / L2：

```text
0      表示两个向量完全重合
越大   表示离得越远
```

所以对于 distance-style 分数，阈值通常是：

```text
distance <= threshold
```

比如：

```text
只保留 distance <= 0.5 的结果。
```

如果你把 distance 当成 similarity，用 `>=` 过滤，就会把远的结果留下，把近的结果过滤掉。

这就是 RAG 调参里很隐蔽但很严重的错误。

### 4. score、similarity、distance 的关系

可以这样理解：

```text
score 是字段名或泛称。
similarity 是一种“越大越好”的分数含义。
distance 是一种“越小越好”的分数含义。
```

也就是说：

```text
score 不一定是 similarity。
score 也可能是 distance。
```

真实项目里，字段名经常会让人误判。

比如：

```text
Qdrant 返回字段常叫 score。
Milvus 搜索命中里常见字段叫 distance。
```

但你不能只凭字段名判断。

你要看 metric。

如果 metric 是 COSINE/IP，通常是相似度方向。

如果 metric 是 L2/Euclid/Manhattan，通常是距离方向。

### 5. 什么是 metric

`metric` 可以理解为：

```text
用什么规则计算两个向量之间的关系。
```

常见 metric：

```text
Cosine
Dot Product / Inner Product
Euclidean / L2
Manhattan / L1
```

同一批向量，用不同 metric 计算，结果可能不一样。

甚至排序也可能不一样。

所以 metric 不是小配置。

它会直接影响：

- 检索结果排序。
- score 含义。
- threshold 比较方向。
- 结果是否稳定。
- 后续 Hybrid Search 融合。
- RAG 评测指标。

### 6. Cosine Similarity

Cosine 关注的是：

```text
两个向量的方向是否接近。
```

它不太关心向量长度。

在文本 embedding 里，我们经常关心的是语义方向。

比如：

```text
“退款多久到账”
“退款到账时间”
```

这两个表达方向接近。

所以很多文本向量检索会使用 Cosine。

Cosine 的常见理解：

```text
越大越相似。
```

阈值方向：

```text
score >= threshold
```

但注意：

```text
Cosine 的理论范围不代表每个 embedding 模型实际返回都会覆盖完整范围。
```

比如你的知识库里多数候选可能集中在：

```text
0.55 到 0.85
```

另一个模型可能集中在：

```text
0.2 到 0.6
```

所以不能机械地说：

```text
0.8 以上才相关。
```

必须结合模型和数据评测。

### 7. Dot Product / Inner Product

Dot Product 关注的是：

```text
两个向量对应维度相乘再求和。
```

它会受到向量长度影响。

如果向量没有归一化，Dot Product 不只表达方向，还会受 magnitude 影响。

常见理解：

```text
越大越相似。
```

阈值方向：

```text
score >= threshold
```

但它的范围通常不像 Cosine 那样直观。

如果向量经过归一化，Dot Product 和 Cosine 会非常接近。

如果没有归一化，Dot Product 的数值就更依赖模型输出尺度。

所以 Dot Product 的阈值更不能随便照抄。

### 8. Euclidean Distance / L2

Euclidean Distance 关注的是：

```text
两个向量在空间中的直线距离。
```

常见理解：

```text
越小越相似。
```

阈值方向：

```text
distance <= threshold
```

如果两个向量完全一样，L2 distance 通常是 0。

越远，distance 越大。

所以 L2 和 Cosine 最大的思维差异是：

```text
Cosine：大好。
L2：小好。
```

### 9. Manhattan Distance / L1

Manhattan Distance 关注的是：

```text
各个维度差值的绝对值之和。
```

它也是距离。

常见理解：

```text
越小越相似。
```

阈值方向：

```text
distance <= threshold
```

在文本语义检索里，Manhattan 不如 Cosine 常见。

但 Qdrant 支持它，所以我们的解释层也把它归为 `lower_is_better`。

### 10. 为什么分数不能跨后端比较

假设你看到：

```text
Qdrant Cosine score = 0.82
Milvus L2 distance = 0.45
```

不能说：

```text
0.82 比 0.45 大，所以 Qdrant 结果更相关。
```

这是错的。

原因是：

```text
一个是 similarity。
一个是 distance。
方向不同。
```

再比如：

```text
Qdrant Cosine score = 0.82
Milvus COSINE distance/score = 0.80
```

也不能直接说它们完全等价。

因为不同后端可能有：

- 不同向量归一化处理。
- 不同索引算法。
- 不同近似搜索参数。
- 不同返回字段语义。
- 不同版本行为细节。

所以本节新增的解释对象里明确写了：

```text
can_compare_across_backends = False
```

### 11. 为什么分数不能跨 embedding 模型比较

即使后端一样，metric 一样，只要 embedding 模型变了，分数分布也可能变。

比如：

```text
模型 A：
相关 chunk 通常在 0.78 到 0.90
不相关 chunk 通常在 0.45 到 0.65

模型 B：
相关 chunk 通常在 0.55 到 0.72
不相关 chunk 通常在 0.30 到 0.50
```

如果你从模型 A 抄了：

```text
score_threshold = 0.8
```

放到模型 B 上，可能会把很多正确结果都过滤掉。

所以阈值不是“行业统一常量”。

阈值来自：

```text
模型 + 数据 + metric + 向量库 + 业务问题 + 评测集
```

### 12. 为什么 score_threshold 不能随便设

`score_threshold` 的作用是：

```text
过滤低质量检索结果。
```

但它有两个风险。

第一个风险是太松。

如果 threshold 太松：

```text
很多不相关 chunk 会进入上下文。
```

后果是：

- 模型被噪声干扰。
- 回答可能偏题。
- 引用来源可能不稳定。
- token 成本增加。

第二个风险是太严。

如果 threshold 太严：

```text
正确 chunk 可能被过滤掉。
```

后果是：

- RAG 返回 no-context。
- 模型没有依据。
- 用户明明问的是知识库里有的问题，系统却答不上来。

所以 threshold 调优必须看评测。

不能只凭肉眼看几条样例。

### 13. threshold 的比较方向

这是本节最关键的工程点。

如果是 similarity-style：

```text
保留 score >= threshold
```

如果是 distance-style：

```text
保留 distance <= threshold
```

同样是 `threshold=0.5`，含义完全不同。

Cosine：

```text
score >= 0.5 代表相似度至少 0.5。
```

L2：

```text
distance <= 0.5 代表距离最多 0.5。
```

一个是下限。

一个是上限。

这就是为什么本节代码里要有：

```text
threshold_operator
```

### 14. Qdrant 里的分数理解

项目里的 Qdrant 文件是：

```text
projects/ai-service/app/rag/vector_store.py
```

Qdrant collection 支持：

```text
Cosine
Dot
Euclid
Manhattan
```

这些 metric 的基础方向可以理解为：

| Metric | 类型 | 方向 |
| --- | --- | --- |
| Cosine | similarity | 越大越相关 |
| Dot | similarity | 越大越相关 |
| Euclid | distance | 越小越相关 |
| Manhattan | distance | 越小越相关 |

注意，Qdrant 的返回字段通常叫：

```text
score
```

但 `score` 这个名字不等于一定是 Cosine 相似度。

你必须结合 collection 的 distance metric 看。

### 15. Milvus 里的分数理解

项目里的 Milvus 文件是：

```text
projects/ai-service/app/rag/milvus_store.py
```

Milvus 当前项目支持：

```text
COSINE
IP
L2
```

这些 metric 的方向可以理解为：

| Metric | 类型 | 方向 |
| --- | --- | --- |
| COSINE | similarity | 越大越相关 |
| IP | similarity | 越大越相关 |
| L2 | distance | 越小越相关 |

Milvus 返回结果里常见字段名是：

```text
distance
```

但这也不能只按字段名理解。

对于 L2，它确实是距离方向：

```text
越小越相关。
```

对于 COSINE/IP，它更像相似度方向：

```text
越大越相关。
```

所以本项目之前在 Milvus 阈值过滤里已经有这种逻辑：

```text
L2 用 <=
其他用 >=
```

本节把这件事抽成统一解释层，避免这种判断散落在各处。

### 16. 关键词分数怎么理解

我们项目的关键词检索是学习版本。

文件在：

```text
projects/ai-service/app/rag/hybrid.py
```

关键词分数来自本地规则：

```text
query terms 命中了多少
命中的词权重是多少
chunk 中出现次数是多少
```

当前实现会把分数压到一个学习用范围里：

```text
0 到 1
```

这个分数不是向量相似度。

它只表达：

```text
字面关键词匹配程度。
```

所以：

```text
keyword_score = 0.8
```

不能和：

```text
vector_score = 0.8
```

直接说成“一样相关”。

它们的来源和含义不同。

### 17. Hybrid 分数怎么理解

Hybrid 分数是本地融合后的分数。

它来自：

```text
归一化后的向量分数 * vector_weight
+
归一化后的关键词分数 * keyword_weight
```

它不是向量库返回的原始分数。

也不是关键词检索的原始分数。

它是：

```text
当前项目融合公式下的排序分数。
```

所以：

```text
hybrid_score = 0.86
```

不能直接和：

```text
qdrant score = 0.86
```

比较。

这两个数字虽然看起来一样，但不是同一个计分体系。

### 18. Rerank 分数怎么理解

后面我们会继续学 Rerank。

现在先提前建立概念：

```text
Rerank 分数是排序模型或排序规则重新计算的相关性分数。
```

它通常发生在召回之后。

召回阶段的分数回答：

```text
这个 chunk 是否被某种检索器找到了？
```

Rerank 分数回答：

```text
在这些候选 chunk 里，哪个更适合回答当前问题？
```

所以 rerank_score 也不要和 vector_score 直接比较。

它们处在不同阶段。

## 本节主题系统讲解

### 1. 为什么要做分数解释层

如果没有分数解释层，项目里很容易出现这种代码：

```text
if chunk.score >= score_threshold:
    keep
```

这在 Cosine/IP 下可能是对的。

但在 L2 下就是错的。

因为 L2 是：

```text
distance <= threshold
```

所以我们需要把下面这些信息结构化：

```text
backend
metric
raw_score_name
value_kind
direction
threshold_operator
range_hint
can_compare_across_backends
can_compare_across_embedding_models
explanation
threshold_note
```

这就是本节新增的：

```text
RetrievalScoreMeaning
```

### 2. `RetrievalScoreMeaning` 解决什么问题

它不是为了让代码更花。

它解决的是工程里的边界不清问题。

以前你看到：

```text
chunk.score = 0.72
```

你不知道：

- 这是相似度还是距离。
- 越大越好还是越小越好。
- threshold 用 `>=` 还是 `<=`。
- 能不能和 keyword_score 比。
- 能不能和 hybrid_score 比。

现在解释对象会明确告诉你：

```text
backend = "milvus"
metric = "l2"
raw_score_name = "distance"
value_kind = "distance"
direction = "lower_is_better"
threshold_operator = "<="
```

这就让调试变得清楚。

### 3. 为什么字段里要有 backend

`backend` 表示分数来自哪里。

比如：

```text
qdrant
milvus
local_keyword
local_hybrid
```

同样是 `0.8`，不同 backend 的含义不同。

有 backend，日志里就能看出来源。

没有 backend，后面做多向量库对比、Qdrant/Milvus 迁移、Hybrid Search 融合时就容易混乱。

### 4. 为什么字段里要有 metric

`metric` 是分数方向的根。

比如：

```text
cosine -> higher_is_better
l2 -> lower_is_better
```

如果只记录 backend，不记录 metric，也不够。

因为同一个 backend 可以支持多个 metric。

Qdrant 可以用 Cosine，也可以用 Euclid。

Milvus 可以用 COSINE，也可以用 L2。

所以 metric 必须跟分数一起进入解释。

### 5. 为什么字段里要有 raw_score_name

不同后端字段名不一样。

Qdrant 常见字段：

```text
score
```

Milvus 常见字段：

```text
distance
```

本地 Hybrid：

```text
hybrid_score
```

`raw_score_name` 的作用是帮助你理解：

```text
这个数字在原始系统里叫什么。
```

但它不会替代 direction。

因为字段名可能迷惑人。

最终判断还是看 metric 和 direction。

### 6. 为什么字段里要有 value_kind

`value_kind` 表示这个值的类别。

当前支持：

```text
similarity
distance
match_score
weighted_score
rerank_score
unknown
```

它能帮你区分：

```text
向量相似度
向量距离
关键词匹配分数
混合融合分数
重排序分数
```

这对后面做日志、评测、可观测性很重要。

因为不同 kind 不能随便混在同一张图里比较。

### 7. 为什么字段里要有 direction

`direction` 是本节最关键字段。

它只有两种：

```text
higher_is_better
lower_is_better
```

它直接决定排序方式。

如果 direction 是 `higher_is_better`：

```text
排序应该从大到小。
```

如果 direction 是 `lower_is_better`：

```text
排序应该从小到大。
```

这就是本节测试里为什么要覆盖：

```text
sort_scores_by_relevance()
```

### 8. 为什么字段里要有 threshold_operator

`threshold_operator` 直接告诉你过滤条件。

如果是 similarity：

```text
>=
```

如果是 distance：

```text
<=
```

这让阈值逻辑不再靠开发者临时想。

代码可以统一问解释对象：

```text
这个分数怎么过阈值？
```

### 9. 为什么字段里要有 can_compare_across_backends

这个字段默认是：

```text
False
```

意思是：

```text
不要把不同后端的原始分数直接横向比较。
```

例如：

```text
Qdrant Cosine 0.82
Milvus COSINE 0.80
```

即使方向一样，也不要默认完全可比。

更不要把：

```text
Qdrant Cosine 0.82
Milvus L2 0.45
```

放在一起比大小。

### 10. 为什么字段里要有 can_compare_across_embedding_models

这个字段默认也是：

```text
False
```

意思是：

```text
不同 embedding 模型的分数分布不能直接比较。
```

比如你以后换真实 embedding 模型，不能直接沿用旧阈值。

要重新评测。

### 11. 本节新增函数关系

本节新增模块：

```text
projects/ai-service/app/rag/score_interpretation.py
```

核心函数：

```text
describe_qdrant_score()
describe_milvus_score()
describe_keyword_score()
describe_hybrid_score()
is_score_passing_threshold()
filter_scores_by_threshold()
sort_scores_by_relevance()
format_score_meaning_for_debug()
```

可以按三类理解。

第一类，描述分数：

```text
describe_qdrant_score()
describe_milvus_score()
describe_keyword_score()
describe_hybrid_score()
```

第二类，使用分数：

```text
is_score_passing_threshold()
filter_scores_by_threshold()
sort_scores_by_relevance()
```

第三类，调试分数：

```text
format_score_meaning_for_debug()
```

### 12. 为什么要改 Milvus 阈值过滤

原来 Milvus 里有这段逻辑：

```text
if metric_type == "L2":
    score <= threshold
else:
    score >= threshold
```

这个逻辑本身是对的。

但它的问题是：

```text
分数方向知识写死在 Milvus 文件内部。
```

以后如果别的模块也要判断分数方向，就可能重复写一遍。

重复写就容易写错。

本节改成：

```text
meaning = describe_milvus_score(metric_type)
is_score_passing_threshold(chunk.score, score_threshold, meaning)
```

这样好处是：

- Milvus 继续保持原行为。
- 分数方向由统一解释层提供。
- 测试能直接覆盖解释层。
- 后续 Qdrant/Milvus/Hybrid/Rerank 调试可以共用同一套语言。

### 13. 为什么要改 `RetrievedChunk.score` 描述

原来 `RetrievedChunk.score` 的描述是：

```text
Vector-store similarity score for this query.
```

这句话现在不够准确。

因为如果 Milvus 使用 L2，`score` 里保存的是 distance-style 值。

它不是 similarity。

所以本节改成：

```text
Raw retrieval score or distance returned by the vector store.
```

这不是小文字修改。

它是在修正概念边界。

以后你看到 `RetrievedChunk.score`，要理解为：

```text
原始检索值。
```

至于它是 similarity 还是 distance，要看解释层。

### 14. 这节为什么没有直接改 Qdrant 查询逻辑

Qdrant 的 `score_threshold` 是传给 Qdrant 服务端的。

项目里没有在 Python 本地过滤 Qdrant 分数。

所以本节没有强行改 Qdrant 查询主流程。

但我们仍然提供：

```text
describe_qdrant_score()
```

因为后面做 debug、评测、阈值建议、bad case 分析时，需要解释 Qdrant 的分数方向。

### 15. 这节为什么不改 Hybrid Search 融合公式

上一节已经实现了 Hybrid Search 的融合报告。

这一节不是要重写融合公式。

这一节要先把分数语义讲清楚。

因为 Hybrid Search 里真正危险的是：

```text
把不同来源的分数当成同一种分数。
```

我们已经知道要归一化。

但归一化之前，必须先知道：

```text
原始分数方向是什么。
```

如果一个分数是 lower_is_better，你不能直接按 higher_is_better 去归一化和加权。

当前项目 Hybrid Search 默认接收的是已经按相似度方向排序的向量结果。

后续如果要支持 L2 原始距离进入 Hybrid Search，就需要先做方向转换或统一归一化。

本节先把解释层建好，为后续更复杂融合打基础。

## 本节代码讲解

### 1. `RetrievalScoreMeaning`

核心结构：

```python
class RetrievalScoreMeaning(BaseModel):
    backend: str
    metric: str
    raw_score_name: str
    value_kind: ScoreValueKind
    direction: ScoreDirection
    threshold_operator: ThresholdOperator
    range_hint: str
    can_compare_across_backends: bool = False
    can_compare_across_embedding_models: bool = False
    explanation: str
    threshold_note: str
```

这个类是本节最重要的代码。

它不是业务结果。

它是“分数说明书”。

以后你看到一个检索分数，可以通过它回答：

```text
这个分数来自哪里？
这个分数叫什么？
它是什么类型？
它越大越好还是越小越好？
threshold 应该怎么比较？
它的范围大概是什么？
能不能跨后端比较？
能不能跨 embedding 模型比较？
```

### 2. `describe_qdrant_score()`

这个函数接收 Qdrant distance 名称。

比如：

```python
describe_qdrant_score("Cosine")
describe_qdrant_score("Euclid")
describe_qdrant_score("Dot")
describe_qdrant_score("Manhattan")
```

它返回 `RetrievalScoreMeaning`。

例如 Cosine：

```text
backend = qdrant
metric = cosine
raw_score_name = score
direction = higher_is_better
threshold_operator = >=
```

例如 Euclid：

```text
backend = qdrant
metric = l2
raw_score_name = score
direction = lower_is_better
threshold_operator = <=
```

### 3. `describe_milvus_score()`

这个函数接收 Milvus metric。

比如：

```python
describe_milvus_score("COSINE")
describe_milvus_score("IP")
describe_milvus_score("L2")
```

它同样返回 `RetrievalScoreMeaning`。

例如 L2：

```text
backend = milvus
metric = l2
raw_score_name = distance
direction = lower_is_better
threshold_operator = <=
```

这里最容易学到的点是：

```text
raw_score_name 叫 distance，不代表所有 Milvus metric 都是 lower_is_better。
```

COSINE/IP 仍然是 higher_is_better。

### 4. `describe_keyword_score()`

关键词分数来自本地关键词命中。

它不是向量库分数。

所以解释对象是：

```text
backend = local_keyword
metric = keyword_match
value_kind = match_score
direction = higher_is_better
```

它提醒我们：

```text
keyword_score 只表达关键词匹配强弱。
```

不要把它当成向量相似度。

### 5. `describe_hybrid_score()`

Hybrid 分数来自本地加权融合。

解释对象是：

```text
backend = local_hybrid
metric = weighted_fusion
raw_score_name = hybrid_score
value_kind = weighted_score
direction = higher_is_better
```

它提醒我们：

```text
hybrid_score 是本地公式产物。
```

不要和 Qdrant/Milvus 原始 score 直接比较。

### 6. `is_score_passing_threshold()`

这个函数把阈值比较统一了。

它的逻辑是：

```text
如果 threshold 是 None，直接通过。
如果 direction 是 lower_is_better，用 score <= threshold。
否则用 score >= threshold。
```

这段逻辑非常重要。

因为它把“比较方向”从人脑记忆变成了代码规则。

以后调用方不用自己判断：

```text
这个 metric 到底该 >= 还是 <=？
```

调用方只要传入 `meaning`。

### 7. `sort_scores_by_relevance()`

这个函数用于演示排序方向。

如果是 Cosine：

```text
[0.95, 0.8, 0.6]
```

如果是 L2：

```text
[0.2, 0.6, 0.8]
```

同样是排序，方向完全相反。

这能帮助你从根上理解：

```text
score 不是永远越大越好。
```

### 8. `format_score_meaning_for_debug()`

这个函数用于调试输出。

比如：

```text
milvus/l2 distance=0.3457 direction=lower_is_better threshold_operator=<= threshold=0.5000
```

它的价值是：

```text
日志里不只打印数字，还打印这个数字应该怎么理解。
```

真实项目里，很多 RAG 问题不是缺少日志。

而是日志里只有：

```text
score=0.3457
```

却没有：

```text
这个 0.3457 是好还是坏？
```

### 9. 本节测试重点

本节新增测试：

```text
projects/ai-service/tests/test_rag_score_interpretation.py
```

覆盖：

- Qdrant Cosine 是 higher_is_better。
- Qdrant Euclid 是 lower_is_better。
- Milvus COSINE/IP/L2 的方向。
- threshold 根据方向选择 `>=` 或 `<=`。
- 分数排序根据方向变化。
- keyword/hybrid 本地分数解释。
- debug line 输出。
- 非法 metric 和非法 score 拒绝。

还跑了相关旧测试：

```text
test_rag_milvus_store.py
test_rag_vector_store.py
test_rag_retriever.py
test_rag_hybrid.py
```

目的不是全量回归，而是确认：

```text
新增解释层没有破坏现有向量库、检索器、Hybrid Search 行为。
```

## 结合项目理解

### 1. 当前 Qdrant 路径

当前 Qdrant 查询路径：

```text
retrieve_top_k()
-> embedding_model.embed_texts()
-> QdrantVectorStore.query_similar()
-> Qdrant Query API
-> RetrievedChunk(score=...)
```

Qdrant 的 `score_threshold` 是传给 Qdrant 服务端的。

所以 Python 本地没有过滤逻辑。

但是当我们打印、分析、评估 Qdrant 返回结果时，仍然应该使用：

```text
describe_qdrant_score(distance)
```

### 2. 当前 Milvus 路径

当前 Milvus 查询路径：

```text
MilvusVectorStore.query_similar()
-> client.search()
-> _build_retrieved_chunk()
-> _apply_score_threshold()
-> RetrievedChunk(score=...)
```

Milvus 当前在 Python 本地做 threshold 过滤。

所以本节把 `_apply_score_threshold()` 改成复用：

```text
describe_milvus_score()
is_score_passing_threshold()
```

这让 L2 和 COSINE/IP 的方向判断更清晰。

### 3. 当前 Hybrid Search 路径

当前 Hybrid Search：

```text
vector_chunks = retrieve_top_k(...)
keyword_results = keyword_retriever.search(...)
fuse_hybrid_results(vector_chunks, keyword_results)
```

这里有个很重要的隐含前提：

```text
vector_chunks 里的 score 应该能按越大越好理解。
```

如果未来直接把 L2 distance 原始值传进 Hybrid Search，就必须先做方向转换。

否则低 distance 的好结果会因为数值小而被当成弱结果。

这就是本节对未来的提醒。

### 4. 当前 Rerank 路径

Rerank 现在有自己的 `rerank_score`。

它和 retrieval score 是不同阶段。

后面学 Rerank 进阶时，我们会继续讲：

```text
retrieval_score 是召回阶段信号。
rerank_score 是精排阶段信号。
```

不要混用。

## 常见误区

### 误区 1：看到 score 就默认越大越好

错。

要先看 metric。

Cosine/IP 通常越大越好。

L2/Euclid/Manhattan 通常越小越好。

### 误区 2：字段名叫 distance 就一定越小越好

不一定。

Milvus 命中结果里常见字段名叫 `distance`。

但 COSINE/IP 下仍然是更大表示更相似。

所以字段名不能替代 metric。

### 误区 3：`score_threshold=0.8` 是通用经验

不是。

这个值只在特定模型、特定数据、特定 metric、特定向量库、特定业务下有意义。

换任何一个条件都可能需要重新评测。

### 误区 4：关键词分数和向量分数可以直接相加

不能。

关键词分数是字面匹配。

向量分数是向量 metric 结果。

Hybrid Search 必须考虑归一化、权重和来源。

### 误区 5：Hybrid 分数可以和 Qdrant 分数直接比较

不能。

Hybrid 分数是本地融合公式结果。

Qdrant 分数是向量库原始检索结果。

两者不是同一个体系。

### 误区 6：评测时只看平均 score

不够。

平均 score 可能掩盖问题。

你还要看：

- 正确 chunk 是否进入 top_k。
- 正确 chunk 排第几。
- threshold 过滤了哪些结果。
- bad case 中的 score 分布。
- 不同 query 类型的 score 分布。

## 本节练习

### 练习 1：判断方向

问题：

```text
Milvus 使用 L2 metric，结果 A distance=0.2，结果 B distance=0.8，哪个更相关？
```

参考答案：

```text
结果 A 更相关。L2 是距离，越小越相似，所以 0.2 比 0.8 更近。
```

### 练习 2：判断 threshold

问题：

```text
L2 metric 下，score_threshold=0.5，应该保留 distance >= 0.5 还是 distance <= 0.5？
```

参考答案：

```text
应该保留 distance <= 0.5。因为 L2 是距离，越小越相似，threshold 表示最大可接受距离。
```

### 练习 3：判断方向

问题：

```text
Cosine metric 下，结果 A score=0.82，结果 B score=0.61，哪个更相关？
```

参考答案：

```text
结果 A 更相关。Cosine 是相似度方向，通常越大越相似。
```

### 练习 4：解释为什么不能比较

问题：

```text
Qdrant Cosine score=0.82，Milvus L2 distance=0.4，能不能说 0.82 对应结果更相关？
```

参考答案：

```text
不能。一个是 similarity-style 分数，一个是 distance-style 分数，方向不同、来源不同、metric 不同，不能直接比大小。
```

### 练习 5：解释为什么不能抄阈值

问题：

```text
别人项目里 score_threshold=0.8 效果好，为什么我们不能直接抄？
```

参考答案：

```text
因为阈值依赖 embedding 模型、向量库、metric、数据集、文档切分、业务问题和评测目标。换模型或数据后，分数分布可能完全不同，直接抄可能过滤掉正确结果或放进太多噪声。
```

### 练习 6：解释 keyword_score

问题：

```text
keyword_score=0.8 和 vector_score=0.8 能不能说明两者相关程度一样？
```

参考答案：

```text
不能。keyword_score 来自关键词匹配，vector_score 来自向量检索，它们的计算方式和含义不同。数值一样不代表相关程度一样。
```

### 练习 7：解释本节代码价值

问题：

```text
为什么要新增 RetrievalScoreMeaning，而不是继续在各处写 if metric == "L2"？
```

参考答案：

```text
因为分数方向是跨模块知识。集中到 RetrievalScoreMeaning 后，代码、测试、日志和笔记都使用同一套解释，避免重复判断和不一致。后续接 Qdrant/Milvus 对比、Hybrid Search 调优、Rerank、评测时也能复用。
```

### 练习 8：判断 Hybrid 分数

问题：

```text
hybrid_score=0.9 和 qdrant score=0.9 能不能直接比较？
```

参考答案：

```text
不能。hybrid_score 是本地归一化和加权融合后的分数，qdrant score 是向量库原始检索分数。它们不是同一个计分体系。
```

## 自测题

### 自测 1：score 和 similarity 是一回事吗？

参考答案：

```text
不是。score 只是泛称或字段名，similarity 是具体含义，通常表示越大越相似。score 也可能是 distance。
```

### 自测 2：distance 通常怎么理解？

参考答案：

```text
distance 通常表示距离，越小越相似。L2、Euclid、Manhattan 都属于距离方向。
```

### 自测 3：Cosine 的常见方向是什么？

参考答案：

```text
Cosine 通常是越大越相似，threshold 一般用 score >= threshold。
```

### 自测 4：L2 的常见方向是什么？

参考答案：

```text
L2 是距离，通常越小越相似，threshold 一般用 distance <= threshold。
```

### 自测 5：为什么字段名不能决定分数方向？

参考答案：

```text
因为不同系统字段命名不统一，字段名叫 score 或 distance 都不一定能完整表达语义。真正决定方向的是 metric 和后端约定。
```

### 自测 6：为什么不同 embedding 模型不能共用阈值？

参考答案：

```text
因为不同模型输出向量的分布不同，相关和不相关 chunk 的分数区间也可能不同。阈值必须通过当前模型和当前数据评测得到。
```

### 自测 7：本节 `threshold_operator` 有什么用？

参考答案：

```text
它明确告诉系统 threshold 应该用 >= 还是 <=。similarity-style 分数通常用 >=，distance-style 分数通常用 <=。
```

### 自测 8：`can_compare_across_backends=False` 表示什么？

参考答案：

```text
表示不要把不同后端的原始分数直接横向比较。不同向量库的 metric、索引、归一化和返回语义都可能不同。
```

### 自测 9：Milvus COSINE 和 Milvus L2 的 threshold 比较有什么不同？

参考答案：

```text
COSINE 是相似度方向，用 score >= threshold。L2 是距离方向，用 distance <= threshold。
```

### 自测 10：为什么本节要修改 `RetrievedChunk.score` 的描述？

参考答案：

```text
因为 RetrievedChunk.score 里保存的是向量库返回的原始检索值，它可能是 similarity，也可能是 distance。原来写成 similarity score 不够准确。
```

### 自测 11：如果正确 chunk 被 threshold 过滤掉，说明什么？

参考答案：

```text
说明阈值可能太严，或者分数方向理解错了，也可能是 embedding 模型、metric、chunk 切分或检索参数导致正确 chunk 分数不理想。需要结合评测和 bad case 分析。
```

### 自测 12：如果低质量 chunk 大量进入上下文，threshold 可能有什么问题？

参考答案：

```text
threshold 可能太松，或者方向用错了，也可能只靠 threshold 不够，需要 metadata filter、rerank、context compression 等后续能力。
```

## 面试表达

### 1 分钟版本

```text
RAG 里的检索分数不能只看数字大小。score 只是字段名，它可能代表相似度，也可能代表距离。比如 Cosine 和 IP 通常是越大越相关，而 L2 是距离，通常越小越相关。所以设置 score_threshold 前必须知道后端、metric、分数方向和比较符号。不同向量库、不同 embedding 模型、不同 metric 的原始分数不能直接横向比较，阈值也不能照抄，应该基于当前数据和评测集确定。我在项目里会把这些信息抽成分数解释层，明确 direction、threshold_operator 和可比较边界，避免后续调参误判。
```

### 3 分钟版本

```text
在 RAG 项目里，检索分数是一个很容易被误用的点。很多人看到 score=0.8 就直接认为相关度很高，但这要看分数来自哪里、使用什么 metric。Cosine similarity 和 inner product 通常是越大越相关，L2/Euclidean distance 则是越小越相关。字段名也不能完全相信，比如有些后端字段叫 score，有些字段叫 distance，但真正决定比较方向的是 metric。

所以我会在工程里显式建一个 score interpretation 层，把 backend、metric、raw_score_name、value_kind、direction、threshold_operator、range_hint、是否可跨后端比较、是否可跨模型比较都结构化记录下来。这样设置 threshold 时，不是到处写 if metric == L2，而是通过统一解释对象决定用 >= 还是 <=。

另外我不会把 Qdrant、Milvus、keyword_score、hybrid_score、rerank_score 混着比较。关键词分数是字面匹配，向量分数来自 metric，hybrid 分数是本地归一化加权结果，rerank 分数是精排阶段结果。它们处在不同计分体系里。真正调优时要结合评测集，看正确 chunk 是否进入 top_k、排序是否靠前、threshold 是否误杀正确结果，而不是凭一个分数拍脑袋。
```

## 本节小结

本节要记住的核心不是某个固定阈值。

本节真正要建立的是判断框架：

```text
看到检索分数：
1. 先问 backend。
2. 再问 metric。
3. 再问 value_kind。
4. 再问 direction。
5. 再问 threshold_operator。
6. 最后才考虑 threshold 数值。
```

当前项目新增了：

```text
score_interpretation.py
RetrievalScoreMeaning
describe_qdrant_score()
describe_milvus_score()
describe_keyword_score()
describe_hybrid_score()
is_score_passing_threshold()
```

并且把 Milvus 的 threshold 过滤改成复用统一解释层。

这为后续学习打下基础：

```text
Rerank 进阶
真实 Rerank 模型接入
引用来源校验
RAG 评测集
检索指标
bad case 分析
参数调优
```

下一节继续：

```text
阶段 9 第 7 节：Rerank 进阶：召回后为什么还要重排序
```

下一节会回答：

```text
既然向量检索、关键词检索、Hybrid Search 都已经能返回结果了，为什么还要多一步 rerank？
```

## 参考资料

本节概念参考了官方文档中关于 metric 方向的说明：

- Qdrant Similarity Search：https://qdrant.tech/documentation/search/search/
- Qdrant Distance Metrics Course：https://qdrant.tech/course/essentials/day-1/distance-metrics/
- Milvus Metric Types：https://milvus.io/docs/v2.6.x/metric.md
- Milvus Range Search：https://milvus.io/docs/range-search.md
