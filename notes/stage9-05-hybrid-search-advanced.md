# 阶段 9 第 5 节：Hybrid Search 进阶：关键词检索 + 向量检索融合

## 本节定位

本节学习 RAG 进阶里的一个核心检索能力：

```text
Hybrid Search，混合检索。
```

前面几节我们已经学了：

```text
第 2 节 Query Rewrite：
把用户原始问题改写成更适合检索的标准 query。

第 3 节 Multi Query：
把一个标准 query 扩展成多个检索角度。

第 4 节 Query Intent：
先判断用户问题到底该走 RAG、Tool、Agent、直接回答、追问还是安全拒答。
```

但只要问题进入 RAG 链路，就马上遇到一个真实工程问题：

```text
到底应该用关键词检索，还是用向量检索？
```

答案通常不是二选一，而是：

```text
关键词检索 + 向量检索一起用，然后把结果融合。
```

这就是 Hybrid Search。

本节不是第一次写 Hybrid Search。项目里在阶段 4 已经有过初版 `hybrid.py`。

本节的重点是把它讲透，并补上真实项目里更重要的一层能力：

```text
让混合检索结果可解释、可调试、可分析。
```

因为 RAG 不是只要能返回几个 chunk 就算完成。你还要能回答：

```text
这个结果为什么排第一？
它是向量检索找到的，还是关键词检索找到的？
两个检索器有没有命中同一个 chunk？
关键词结果是不是太少？
向量结果是不是偏题？
融合权重是不是需要调整？
```

如果答不上来，后面做 RAG 调优、bad case 分析、面试表达都会很虚。

## 本节学习目标

学完本节，你要能做到：

1. 能解释什么是 Hybrid Search。
2. 能说清楚关键词检索和向量检索分别擅长什么、不擅长什么。
3. 能理解为什么只用向量检索不够，只用关键词检索也不够。
4. 能理解召回、精度、噪声之间的关系。
5. 能解释为什么不同检索器的原始分数不能直接相加。
6. 能理解 score 归一化的作用。
7. 能理解加权融合的基本公式。
8. 能解释为什么要用 `chunk_id` 去重。
9. 能看懂 `vector-only`、`keyword-only`、`both` 三类结果。
10. 能看懂本节新增的 `HybridFusionReport`。
11. 能用 debug 输出判断混合检索哪里可能出问题。
12. 能说清楚 Hybrid Search 和 Query Rewrite、Multi Query、Intent Classification、Rerank 的关系。

## 本节新增和修改

本节修改：

```text
projects/ai-service/app/rag/hybrid.py
projects/ai-service/tests/test_rag_hybrid.py
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

本节新增：

```text
notes/stage9-05-hybrid-search-advanced.md
```

本节没有：

- 启动 VMware Ubuntu。
- 启动 Qdrant。
- 启动 Milvus。
- 调用真实大模型。
- 调用真实 embedding 模型。
- 新增手动测试文档。

原因是本节的核心是混合检索融合逻辑和可解释性，不依赖真实外部服务。

## 一句话先讲透

Hybrid Search 的核心思想是：

```text
向量检索负责语义相似，关键词检索负责字面精确命中，然后系统把两路结果去重、归一化、加权、排序，得到更稳的候选上下文。
```

更口语化一点：

```text
向量检索像“理解意思”。
关键词检索像“盯住字眼”。
Hybrid Search 是让两个人同时找资料，然后把他们找到的资料合并排名。
```

## 基础知识铺垫

### 1. RAG 里的检索到底在干什么

RAG 的完整链路可以简化成：

```text
用户问题
-> 检索知识库
-> 拿到相关 chunk
-> 把 chunk 塞给大模型
-> 大模型基于 chunk 生成回答
```

其中“检索知识库”的目标不是直接回答用户。

它的目标是：

```text
从大量文档 chunk 里，找出最可能支撑答案的候选上下文。
```

所以检索质量会直接决定后面的回答质量。

如果检索没把正确资料找出来，大模型再强也容易胡编。

如果检索找出太多无关资料，大模型容易被噪声干扰。

如果检索结果排序不对，真正有用的资料可能被挤到后面，超过上下文窗口时就用不上。

所以 RAG 的检索不是“查一下就行”，而是一个需要设计和调优的工程环节。

### 2. 什么是向量检索

向量检索的基础是 embedding。

embedding 会把文本转换成一组数字：

```text
文本 -> embedding 向量
```

这组数字表达的是文本的语义特征。

比如：

```text
“东西坏了能不能退”
“商品质量问题退货规则”
```

这两句话字面不完全一样，但意思接近。

embedding 模型会尽量让它们的向量在向量空间里更接近。

向量检索做的事情就是：

```text
把用户问题转成向量
-> 在向量数据库里找最相似的文档 chunk 向量
-> 返回 top_k 个候选 chunk
```

向量检索擅长处理：

- 用户口语化表达。
- 同义词、近义表达。
- 语义接近但字面不同的问题。
- 文档措辞和用户提问不完全一致的场景。

例子：

```text
用户问：买的东西坏了，退的话邮费咋算？
文档写：商品质量问题退货运费由商家承担。
```

关键词上，用户没有直接说“商品质量问题”“运费承担”。

但语义上，这两个内容很接近。

向量检索就可能把相关政策 chunk 找出来。

### 3. 向量检索的弱点

向量检索不是万能的。

它常见的弱点有 5 类。

第一，精确编号可能不稳定。

比如：

```text
订单 A1001
工单 T202607300001
SKU 9X-42-B
政策条款 3.2.1
```

这些字符串的意义很多时候不是靠语义，而是靠精确匹配。

如果用户问的是 `A1001`，系统应该精确关注这个编号。

向量检索可能知道它是“订单号”，但不一定能稳定地只找 `A1001` 对应资料。

第二，罕见专有名词可能不稳定。

比如内部系统名、活动名、供应商代号、特殊产品名。

这些词如果 embedding 模型没有充分学过，语义表示可能不准。

第三，短 query 容易语义不完整。

比如：

```text
退款
物流
质保
会员
```

这些 query 太短，向量表示可能很泛。

第四，否定和条件容易被弱化。

比如：

```text
哪些情况不能退款？
哪些订单不支持取消？
```

“不能”“不支持”这种条件对业务规则很关键，但向量相似度有时更关注主题词，比如“退款”“取消”。

第五，相似不等于正确。

向量检索找的是“语义相近”，不是“业务上一定能回答”。

所以向量检索召回的 chunk 可能看起来相关，但并不是用户真正需要的那条规则。

### 4. 什么是关键词检索

关键词检索关注的是：

```text
query 里的词有没有在文档里出现。
```

它可以很简单，比如我们项目现在的 `SimpleKeywordRetriever`：

```text
提取 query 里的关键词
-> 提取 chunk 里的关键词
-> 计算命中了多少关键词
-> 按命中程度排序
```

真实搜索系统里，关键词检索常见算法包括：

```text
TF-IDF
BM25
倒排索引
Elasticsearch
OpenSearch
```

本项目暂时没有引入 Elasticsearch，也没有完整实现 BM25。

但学习上，先用简单关键词检索已经足够理解 Hybrid Search 的核心结构。

关键词检索擅长处理：

- 精确编号。
- 专有名词。
- SKU、订单号、工单号。
- 文档标题、章节名、业务术语。
- 必须字面命中的规则词。

例子：

```text
用户问：A1001 的物流状态是什么？
```

这里 `A1001` 是硬条件。

只靠语义相似是不够的。

关键词检索会天然重视这个字面编号。

### 5. 关键词检索的弱点

关键词检索也不是万能的。

它的弱点主要有 5 类。

第一，用户表达和文档表达不一致时容易漏掉。

比如：

```text
用户说：东西坏了。
文档写：商品质量问题。
```

如果没有同义词扩展，关键词检索可能认为这两个不匹配。

第二，用户口语化时容易漏掉。

```text
邮费咋算
多久能到账
买错了咋退
```

文档里可能写的是：

```text
运费承担
退款到账时间
个人原因退货
```

字面不一样，关键词检索就可能召回不足。

第三，词切分会影响结果。

中文没有天然空格。

如果切词不好，关键词检索可能把“退款到账”拆得不合适。

我们项目现在用的是非常轻量的中文 ngram 方式，不是专业中文分词器。

第四，关键词命中不代表语义正确。

一个 chunk 里出现了“退款”，不代表它能回答“退款多久到账”。

它可能讲的是“退款申请条件”。

第五，关键词检索容易被高频词干扰。

比如“订单”“退款”“用户”“客服”这些词在很多文档里都出现。

如果只看字面命中，可能把很多泛相关资料排上来。

### 6. 为什么要 Hybrid Search

因为两种检索方式刚好互补。

可以把它们这样理解：

| 检索方式 | 擅长 | 容易出问题 |
| --- | --- | --- |
| 向量检索 | 语义相似、口语化、同义表达 | 编号、专有名词、精确条件可能不稳 |
| 关键词检索 | 精确词、编号、标题、术语 | 口语化、同义表达、语义泛化能力弱 |

Hybrid Search 要解决的问题是：

```text
不要把检索质量押在单一路径上。
```

更工程化地说：

```text
向量检索提高语义召回。
关键词检索补齐精确召回。
融合排序减少单一路径失误。
```

### 7. 召回、精度、噪声

学习 Hybrid Search 必须先理解三个词。

第一个是召回。

```text
召回关注：正确资料有没有被找出来。
```

如果正确 chunk 根本没进入候选集，后面 rerank 和大模型都救不了。

第二个是精度。

```text
精度关注：找出来的资料里，有多少是真的相关。
```

如果返回 10 个 chunk，只有 1 个有用，剩下 9 个都是噪声，模型很容易被干扰。

第三个是噪声。

```text
噪声就是看起来相关，但实际不能支撑答案的资料。
```

Hybrid Search 通常会提高召回，但也可能引入更多噪声。

所以真实 RAG 链路里常见组合是：

```text
Hybrid Search 负责多召回
Rerank 负责精排序
Context Compression 负责压缩上下文
Citation Check 负责验证答案来源
```

本节先讲 Hybrid Search，后面才继续讲 score、rerank、引用校验等能力。

### 8. 为什么不能直接把两个分数相加

这是本节非常重要的基础点。

向量检索和关键词检索返回的分数，不一定是同一种含义。

向量检索的分数可能来自：

```text
cosine similarity
dot product
distance 转换后的 score
向量数据库自己的 scoring 规则
```

关键词检索的分数可能来自：

```text
关键词命中比例
TF-IDF
BM25
自定义权重
标题加权
字段加权
```

这两个分数不在同一个尺度上。

比如：

```text
向量分数：0.82
关键词分数：12.7
```

不能说 `12.7` 就一定比 `0.82` 强。

因为它们不是同一个计分体系。

所以融合前通常要做归一化。

### 9. 什么是 score 归一化

归一化就是把不同来源的分数转换到一个相对可比的范围。

我们项目当前用的是简单的最大值归一化：

```text
normalized_score = score / max_score
```

例如向量结果：

```text
chunk-a score = 0.9
chunk-b score = 0.6

max_score = 0.9

chunk-a normalized = 0.9 / 0.9 = 1.0
chunk-b normalized = 0.6 / 0.9 = 0.6667
```

关键词结果：

```text
chunk-c score = 1.0
chunk-d score = 0.8

max_score = 1.0

chunk-c normalized = 1.0
chunk-d normalized = 0.8
```

归一化后，两个检索器内部的相对强弱就更容易融合。

注意：

```text
归一化不是把分数变成绝对真理。
它只是让不同检索器的分数可以进入同一个融合公式。
```

真实系统里还可能使用 min-max、z-score、rank-based、RRF 等融合方式。

我们现在先用简单归一化，是为了把原理学清楚。

### 10. 什么是加权融合

加权融合就是给不同检索器分配权重。

我们项目默认：

```text
vector_weight = 0.7
keyword_weight = 0.3
```

意思是：

```text
默认更相信向量检索的语义相似能力，但也保留关键词检索对精确词的补充。
```

当前融合公式可以理解为：

```text
hybrid_score =
  normalized_vector_score * vector_weight
  + normalized_keyword_score * keyword_weight
```

如果一个 chunk 同时被向量检索和关键词检索找到，它就能同时获得两部分分数。

这通常是一个强信号：

```text
语义上相关，字面上也命中。
```

### 11. 为什么要按 chunk_id 去重

向量检索和关键词检索可能找到同一个 chunk。

如果不去重，就会出现：

```text
结果 1：chunk-a
结果 2：chunk-a
结果 3：chunk-b
```

这会造成两个问题。

第一，浪费上下文窗口。

同一个 chunk 放两次，没有增加信息量。

第二，影响排序和后续生成。

模型可能误以为重复出现的内容更重要。

所以融合时必须用稳定 ID 去重。

我们项目用的是：

```text
chunk_id
```

如果一个 chunk 同时来自向量和关键词，就合并成一个 `HybridSearchResult`，并记录：

```text
retrieval_sources = ["vector", "keyword"]
```

这样既去重，又保留来源信息。

### 12. vector-only、keyword-only、both 是什么

融合后，每个结果可以分成三种来源。

第一种是 `vector-only`：

```text
只有向量检索找到，关键词检索没有找到。
```

这类结果可能说明：

- 用户表达和文档字面不同，但语义接近。
- 关键词提取太弱。
- 也可能是向量检索带来的泛相关噪声。

第二种是 `keyword-only`：

```text
只有关键词检索找到，向量检索没有找到。
```

这类结果可能说明：

- 里面有精确编号、专有名词或业务术语。
- 向量检索对短词、编号、罕见词不敏感。
- 也可能是关键词命中了泛词，实际不够相关。

第三种是 `both`：

```text
向量检索和关键词检索都找到了。
```

这类结果通常更值得关注。

因为它同时满足：

```text
语义接近 + 字面命中
```

但也不能盲信。

如果 query 本身很泛，比如“退款”，很多 chunk 都可能 both 命中。

### 13. Hybrid Search 和前几节的关系

把阶段 9 前几节连起来看：

```text
Query Intent：
判断这个问题是否应该走 RAG。

Query Rewrite：
把用户原始问题改写成更适合检索的标准 query。

Multi Query：
把标准 query 扩展成多个角度，提高召回概率。

Hybrid Search：
每个 query 可以同时走向量检索和关键词检索，再融合结果。
```

它们不是互相替代。

它们是在 RAG 链路里分工。

一个更完整的链路是：

```text
用户问题
-> 意图识别
-> Query Rewrite
-> Multi Query
-> 向量检索 + 关键词检索
-> 结果融合
-> Rerank
-> 上下文构造
-> 大模型生成
-> 引用校验
```

本节学的是中间这一步：

```text
向量检索 + 关键词检索 -> 结果融合
```

## 本节主题系统讲解

### 1. 当前项目已有的 Hybrid Search 基础

项目里的核心文件是：

```text
projects/ai-service/app/rag/hybrid.py
```

它已经有以下能力：

```text
KeywordSearchResult
SimpleKeywordRetriever
HybridSearchResult
HybridSearchWeights
extract_keyword_terms()
fuse_hybrid_results()
hybrid_retrieve()
```

这些能力可以分成三层。

第一层，关键词检索层。

```text
extract_keyword_terms()
SimpleKeywordRetriever.search()
KeywordSearchResult
```

负责从 query 和 chunk 里抽词，并计算字面命中分数。

第二层，融合层。

```text
fuse_hybrid_results()
HybridSearchResult
HybridSearchWeights
```

负责把向量结果和关键词结果合并。

第三层，编排入口。

```text
hybrid_retrieve()
```

负责先调用向量检索，再调用关键词检索，最后调用融合函数。

本节没有大改这些主流程。

原因是这些代码已经能表达 Hybrid Search 的核心工程结构。

本节补的是：

```text
HybridFusionReport
build_hybrid_fusion_report()
format_hybrid_results_for_debug()
```

也就是“让融合过程可观察、可分析”。

### 2. 当前融合流程

当前项目的融合流程可以用这张文本图理解：

```text
用户 query
   |
   |-- 向量检索 -> vector_chunks
   |
   |-- 关键词检索 -> keyword_results
   |
   v
按 chunk_id 合并
   |
   v
分别对 vector_score / keyword_score 做归一化
   |
   v
按 vector_weight / keyword_weight 加权
   |
   v
得到 hybrid_score
   |
   v
按 hybrid_score 排序，返回 top_k
```

这条链路的核心不是复杂，而是边界清楚。

向量检索只负责语义召回。

关键词检索只负责字面召回。

融合函数只负责合并和排序。

报告函数只负责解释和调试。

### 3. `HybridSearchResult` 表达什么

`HybridSearchResult` 是融合后的单条结果。

它不是原始向量结果，也不是原始关键词结果。

它表达的是：

```text
这个 chunk 在混合检索后的最终候选状态。
```

核心字段：

| 字段 | 含义 |
| --- | --- |
| `chunk_id` | chunk 的稳定唯一标识，用于去重 |
| `content` | chunk 正文 |
| `metadata` | 文档来源、章节、业务域、权限组等元数据 |
| `hybrid_score` | 融合后的总分 |
| `vector_score` | 原始向量检索分数，没有向量命中时为 `None` |
| `keyword_score` | 原始关键词检索分数，没有关键词命中时为 `None` |
| `retrieval_sources` | 来源，可能是 `["vector"]`、`["keyword"]` 或 `["vector", "keyword"]` |
| `matched_terms` | 关键词检索命中的词 |

这个模型非常重要。

因为它把“结果是什么”和“结果为什么出现”放在了一起。

真实排查时，你不能只看 content。

还要看：

```text
它是怎么被找出来的。
它的分数来自哪里。
它命中了哪些词。
它属于哪个文档和章节。
```

### 4. 本节新增的 `HybridFusionReport`

本节新增的 `HybridFusionReport` 是融合报告。

它不是给最终用户看的。

它是给开发者、测试、调优、日志和评测系统看的。

它回答的是：

```text
这一次混合检索整体表现怎么样？
```

字段解释：

| 字段 | 作用 |
| --- | --- |
| `top_k` | 最终最多返回多少条 |
| `vector_weight` | 本次向量检索权重 |
| `keyword_weight` | 本次关键词检索权重 |
| `vector_result_count` | 向量检索原始返回数量 |
| `keyword_result_count` | 关键词检索原始返回数量 |
| `fused_result_count` | 融合后最终返回数量 |
| `vector_only_count` | 最终结果里只来自向量检索的数量 |
| `keyword_only_count` | 最终结果里只来自关键词检索的数量 |
| `both_count` | 最终结果里两路都命中的数量 |
| `overlap_chunk_ids` | 两路检索都命中的 chunk_id 列表 |
| `top_chunk_id` | 融合后排第一的 chunk |
| `results` | 融合后的完整结果列表 |
| `debug_lines` | 便于打印和日志查看的调试文本 |

为什么这些字段重要？

因为它们能帮你快速判断检索质量问题在哪一层。

例如：

```text
vector_result_count = 5
keyword_result_count = 0
```

可能说明关键词提取失败、query 太口语化、关键词索引不完整。

再比如：

```text
vector_only_count = 5
keyword_only_count = 0
both_count = 0
```

说明最终结果完全依赖向量检索。

这不一定错，但如果用户问题包含订单号、SKU、条款号，就要警惕。

再比如：

```text
both_count = 3
```

说明两路检索有明显交集。

通常这是一个较强的相关性信号。

### 5. 为什么报告里要记录 overlap

`overlap_chunk_ids` 表示：

```text
向量检索和关键词检索都找到了哪些 chunk。
```

这对判断检索稳定性很有帮助。

如果一个 query 的正确答案 chunk 经常同时出现在两路结果里，说明检索相对稳。

如果正确答案只偶尔被向量检索找到，关键词完全找不到，可能需要：

- 优化文档标题和章节。
- 增加业务关键词。
- 改进 Query Rewrite。
- 优化关键词检索器。

如果正确答案只被关键词找到，向量找不到，可能需要：

- 检查 embedding 模型是否合适。
- 检查 chunk 切分是否过碎或过长。
- 检查 query 是否过短。
- 检查向量库参数和阈值。

### 6. 为什么要有 debug_lines

结构化字段适合程序读。

但开发时，很多时候你需要直接看日志。

所以本节新增：

```text
format_hybrid_results_for_debug()
```

它会把融合结果格式化成类似这样的文本：

```text
1. hybrid_score=0.8667 vector_score=0.6000 keyword_score=1.0000 sources=vector,keyword source=refund.md section=退款到账 chunk_id=chunk-both matched=退款,到账
```

这行信息可以让你一眼看到：

- 排名第几。
- 融合分数是多少。
- 原始向量分数是多少。
- 原始关键词分数是多少。
- 来源是 vector、keyword 还是两者都有。
- 来自哪个文档。
- 来自哪个章节。
- chunk_id 是什么。
- 命中了哪些关键词。

如果只打印 content，很难定位问题。

debug line 的意义是：

```text
把检索结果从“黑盒返回几个片段”，变成“可解释的候选列表”。
```

### 7. 如何用报告分析问题

假设用户问：

```text
质量问题退货运费谁承担？
```

理想情况可能是：

```text
vector_result_count = 5
keyword_result_count = 5
both_count = 2
top_chunk_id = refund_quality_shipping_chunk
```

这说明：

```text
语义检索和关键词检索都认为相关资料在前面。
```

如果出现：

```text
vector_result_count = 5
keyword_result_count = 0
both_count = 0
```

就要看关键词提取是不是没有抽到“质量”“退货”“运费”。

如果出现：

```text
vector_result_count = 0
keyword_result_count = 5
```

就要看向量检索是不是阈值太高、向量库没数据、embedding 维度不匹配、metadata filter 过严。

如果出现：

```text
top_chunk_id 不是正确 chunk
但正确 chunk 在 results 第 3 名
```

说明召回没问题，排序可能有问题。

后面就应该考虑 rerank 或调整融合权重。

如果正确 chunk 根本不在 results 里，就不是排序问题，而是召回问题。

这就是为什么本节要补报告。

### 8. 当前项目的融合策略有什么局限

当前项目是学习型实现，不是完整搜索引擎。

它有几个明确边界。

第一，关键词检索不是 BM25。

当前用的是简单词项命中和权重计算。

它适合理解关键词召回原理，但不等于生产级全文检索。

第二，归一化方式很简单。

当前使用最大值归一化。

它容易理解，但在极端分数分布下可能不够稳。

第三，权重是固定的。

当前默认 `0.7 / 0.3`。

真实系统可能会根据 query 类型动态调整。

比如：

```text
有订单号、SKU、条款号 -> 提高关键词权重。
口语化政策问题 -> 提高向量权重。
```

第四，还没有接 rerank。

Hybrid Search 返回的是候选集。

最终排序质量还可以继续通过 rerank 提升。

第五，还没有形成完整评测闭环。

判断权重好不好，不能靠感觉。

后面要用 eval 数据集、Hit Rate、Recall、MRR、bad case 分析来验证。

### 9. Hybrid Search 后为什么通常还需要 Rerank

Hybrid Search 主要解决：

```text
多路召回。
```

Rerank 主要解决：

```text
候选结果精排序。
```

这两个不是一回事。

Hybrid Search 把可能相关的资料尽量捞出来。

Rerank 再判断：

```text
这些候选 chunk 里，哪些真正最适合回答当前问题？
```

可以这样理解：

```text
Hybrid Search：先把鱼塘里可能有用的资料捞上来。
Rerank：再按和问题的匹配程度重新排队。
```

注意，这里只是比喻，真正实现里就是召回和排序两个阶段。

如果没有 Hybrid Search，Rerank 可能根本看不到正确 chunk。

如果没有 Rerank，Hybrid Search 可能把正确 chunk 找到了，但没有排到足够靠前。

所以真实 RAG 经常是：

```text
Hybrid Search -> Rerank -> Generate
```

## 本节代码讲解

### 1. `HybridFusionReport`

本节新增：

```python
class HybridFusionReport(BaseModel):
    top_k: int = Field(gt=0)
    vector_weight: float = Field(ge=0)
    keyword_weight: float = Field(ge=0)
    vector_result_count: int = Field(ge=0)
    keyword_result_count: int = Field(ge=0)
    fused_result_count: int = Field(ge=0)
    vector_only_count: int = Field(ge=0)
    keyword_only_count: int = Field(ge=0)
    both_count: int = Field(ge=0)
    overlap_chunk_ids: list[str] = Field(default_factory=list)
    top_chunk_id: str | None = None
    results: list[HybridSearchResult] = Field(default_factory=list)
    debug_lines: list[str] = Field(default_factory=list)
```

这里用了 Pydantic `BaseModel`。

原因是报告不是随便拼一个 dict。

它是一个稳定结构。

稳定结构的好处是：

- 字段清楚。
- 类型清楚。
- 测试容易写。
- 日志和 API 后续都可以复用。
- 不容易漏字段。
- 不容易把负数 count 这种非法状态混进去。

`Field(ge=0)` 表示这个数必须大于等于 0。

`Field(gt=0)` 表示必须大于 0。

所以：

```text
count 可以是 0。
top_k 不能是 0。
```

这就是业务含义。

### 2. `build_hybrid_fusion_report()`

这个函数做三件事。

第一，复用原来的融合函数：

```python
results = fuse_hybrid_results(...)
```

这说明报告不重新发明一套排序逻辑。

它必须和真实返回结果保持一致。

第二，统计来源集合：

```python
vector_chunk_ids = {chunk.chunk_id for chunk in vector_chunks}
keyword_chunk_ids = {result.chunk_id for result in keyword_results}
returned_chunk_ids = {result.chunk_id for result in results}
```

这里用 set 是为了做集合运算。

比如：

```text
vector_chunk_ids - keyword_chunk_ids
```

表示只在向量结果里出现的 chunk。

```text
keyword_chunk_ids - vector_chunk_ids
```

表示只在关键词结果里出现的 chunk。

```text
vector_chunk_ids & keyword_chunk_ids
```

表示两路都命中的 chunk。

第三，生成报告：

```python
HybridFusionReport(...)
```

注意几个 count 都只统计最终返回结果里的来源情况：

```python
vector_only_count=len((vector_chunk_ids - keyword_chunk_ids) & returned_chunk_ids)
keyword_only_count=len((keyword_chunk_ids - vector_chunk_ids) & returned_chunk_ids)
both_count=len((vector_chunk_ids & keyword_chunk_ids) & returned_chunk_ids)
```

为什么要和 `returned_chunk_ids` 取交集？

因为原始检索可能拿到了很多候选，但最终只返回 top_k。

报告最关心的是：

```text
最终交给后续链路的结果构成是什么。
```

所以 count 应该看最终返回结果，而不是所有原始候选。

### 3. `format_hybrid_results_for_debug()`

这个函数把结构化结果转换成便于阅读的调试行。

它不会改变检索结果。

它只是让你更容易看懂。

核心信息包括：

```text
排名
hybrid_score
vector_score
keyword_score
sources
source
section
chunk_id
matched terms
```

为什么 `matched_terms[:6]` 只取前 6 个？

因为 debug line 是给日志看的。

如果匹配词太多，日志会变得很长，反而不容易读。

为什么 score 为 `None` 时输出 `"none"`？

因为有些结果只来自一路检索。

比如 `keyword-only` 没有 vector score。

这时输出：

```text
vector_score=none
```

比空字符串更清楚。

### 4. 本节测试重点

本节测试没有真实调用模型，也没有真实连接向量数据库。

测试重点是融合逻辑和报告结构。

新增测试主要确认：

```text
build_hybrid_fusion_report() 能正确统计 vector-only / keyword-only / both。
format_hybrid_results_for_debug() 能输出关键调试字段。
```

这类测试的价值是：

```text
以后改融合权重、改排序规则、接 rerank 或改日志时，能及时发现基础契约被破坏。
```

注意，本节测试不是为了验证“搜索效果一定好”。

因为搜索效果需要评测集和真实数据。

本节测试验证的是：

```text
混合检索融合规则按照预期工作。
融合报告没有算错。
调试输出包含必要信息。
```

## 你要能讲给别人听

如果别人问你：

```text
为什么 RAG 里要做 Hybrid Search？
```

你可以这样回答：

```text
因为向量检索和关键词检索解决的是不同问题。向量检索擅长语义相似，能处理用户口语化和同义表达；关键词检索擅长精确词、编号、专有名词和业务术语。只用向量容易漏掉精确条件，只用关键词容易漏掉语义相近但字面不同的问题。Hybrid Search 会把两路结果按 chunk_id 去重，并对不同分数做归一化和加权融合，从而提高召回稳定性。真实项目里还要记录每条结果来自 vector、keyword 还是两者都有，方便调试和调权。
```

如果别人问你：

```text
Hybrid Search 是不是一定比向量检索好？
```

你不能简单说“一定好”。

更准确的回答是：

```text
它通常能提升召回稳定性，尤其是同时存在口语化问题和精确关键词的业务场景。但它也可能引入更多噪声，所以后面通常还要配合 rerank、score threshold、metadata filter 和评测集调优。是否更好要用实际评测数据验证。
```

## 常见误区

### 误区 1：Hybrid Search 就是把两个结果列表拼起来

不对。

简单拼接会有重复、分数不可比、排序混乱的问题。

Hybrid Search 至少要考虑：

```text
去重
分数归一化
加权融合
排序规则
来源记录
调试信息
```

### 误区 2：关键词检索过时了

不对。

在订单号、SKU、条款号、专有名词、业务术语场景里，关键词检索仍然很重要。

很多真实 RAG 系统不是向量检索替代关键词检索，而是把两者结合。

### 误区 3：向量分数和关键词分数可以直接比较

不对。

不同检索器的分数含义不同。

融合前必须考虑尺度问题。

### 误区 4：both 命中的结果一定正确

不一定。

`both` 是强信号，但不是最终真理。

如果 query 很泛，很多 chunk 都可能同时命中。

后面仍然需要 rerank 和评测。

### 误区 5：融合权重靠感觉调

不应该。

学习阶段可以先用默认权重理解原理。

真实项目里要用评测集看指标变化，比如 Hit Rate、Recall、MRR、答案正确率。

## 本节练习

### 练习 1：判断检索方式

问题：

```text
用户问：订单 A1001 的物流到哪了？
```

这个问题更需要向量检索还是关键词检索？为什么？

参考答案：

```text
更需要关键词检索或业务工具调用。因为 A1001 是精确订单号，必须精确定位。向量检索可以理解“物流状态”这个语义，但不适合单独承担订单号精确匹配。真实项目里这类问题通常应该走 Tool Calling 查询订单，而不是纯 RAG。
```

### 练习 2：判断检索方式

问题：

```text
用户问：东西坏了，退货邮费谁出？
```

这个问题为什么适合向量检索？

参考答案：

```text
因为用户表达比较口语化，“东西坏了”“邮费谁出”和文档里的“商品质量问题”“运费承担”字面不完全一样，但语义接近。向量检索能根据语义相似找到政策 chunk。
```

### 练习 3：解释分数归一化

问题：

```text
为什么不能把 vector_score=0.8 和 keyword_score=12 直接相加？
```

参考答案：

```text
因为它们来自不同计分体系，含义和尺度不一样。vector_score 可能是相似度，keyword_score 可能是关键词命中或 BM25 分数。12 不一定比 0.8 更相关。融合前需要归一化或使用其他融合策略。
```

### 练习 4：解释 chunk_id 去重

问题：

```text
为什么融合时要按 chunk_id 去重？
```

参考答案：

```text
因为向量检索和关键词检索可能返回同一个 chunk。如果不去重，同一段内容会重复占用上下文窗口，还可能影响排序和模型判断。按 chunk_id 合并后，既能避免重复，又能记录它同时来自 vector 和 keyword。
```

### 练习 5：解读报告

问题：

```text
vector_result_count = 5
keyword_result_count = 5
vector_only_count = 4
keyword_only_count = 1
both_count = 0
```

这可能说明什么？

参考答案：

```text
说明两路检索几乎没有交集，最终结果来源比较分散。可能是 query 表达和文档字面差异大，也可能是关键词提取、向量召回、metadata filter 或权重设置存在问题。不能只看最终有 5 条结果，还要检查正确 chunk 是否被召回、两路结果是否偏题。
```

### 练习 6：判断是否需要 rerank

问题：

```text
如果正确 chunk 已经在 Hybrid Search 结果里，但排在第 5 名，这属于召回问题还是排序问题？
```

参考答案：

```text
更偏排序问题。因为正确 chunk 已经被召回了，但没有排到足够靠前。后面可以考虑调整融合权重、改排序规则或接入 rerank。
```

### 练习 7：设计权重

问题：

```text
如果 query 里包含 SKU、订单号、条款编号，你会倾向提高 vector_weight 还是 keyword_weight？
```

参考答案：

```text
倾向提高 keyword_weight。因为这些是精确匹配信号，关键词检索更适合处理。但如果问题同时有复杂语义，仍然不能完全关闭向量检索。
```

### 练习 8：解释 debug 行

问题：

```text
debug 行里 sources=vector,keyword 代表什么？
```

参考答案：

```text
代表这个 chunk 同时被向量检索和关键词检索找到。它通常是更强的相关性信号，因为它既语义相近，又有关键词命中。
```

## 自测题

### 自测 1：Hybrid Search 是什么？

参考答案：

```text
Hybrid Search 是把向量检索和关键词检索结合起来的检索方式。它通常会分别执行语义召回和字面召回，然后对结果去重、归一化、加权融合和排序，得到最终候选 chunk。
```

### 自测 2：向量检索最擅长什么？

参考答案：

```text
向量检索最擅长语义相似，尤其是用户表达口语化、同义表达、文档措辞和问题不完全一致的场景。
```

### 自测 3：关键词检索最擅长什么？

参考答案：

```text
关键词检索最擅长精确词、编号、专有名词、业务术语、标题和章节名等需要字面命中的场景。
```

### 自测 4：为什么 Hybrid Search 可能引入噪声？

参考答案：

```text
因为它从多路检索器召回候选，召回范围变大后，不相关或弱相关 chunk 也可能进入结果。召回提升不等于最终答案一定更准，所以后面还需要 rerank、过滤和评测。
```

### 自测 5：`HybridFusionReport` 是给谁看的？

参考答案：

```text
主要给开发者、测试、调优、日志和评测系统看。它不是最终用户回答，而是帮助我们理解一次混合检索的来源构成、分数、重叠和排序情况。
```

### 自测 6：`top_chunk_id` 有什么用？

参考答案：

```text
它记录融合后排名第一的 chunk_id，方便快速观察这次检索最相信哪条资料。如果 top_chunk_id 经常不是期望 chunk，就要检查召回和排序策略。
```

### 自测 7：为什么 `vector_score` 可能是 `None`？

参考答案：

```text
因为某条结果可能只来自关键词检索，没有被向量检索召回。这类结果就是 keyword-only。
```

### 自测 8：为什么 `keyword_score` 可能是 `None`？

参考答案：

```text
因为某条结果可能只来自向量检索，没有被关键词检索召回。这类结果就是 vector-only。
```

### 自测 9：如果 correct chunk 不在 Hybrid Search 结果里，下一步该优先查什么？

参考答案：

```text
优先查召回问题。要看向量库是否有数据、embedding 是否一致、metadata filter 是否过严、query rewrite 是否改错、关键词提取是否失败、top_k 是否太小。
```

### 自测 10：如果 correct chunk 在结果里但排名靠后，下一步该优先查什么？

参考答案：

```text
优先查排序问题。可以检查融合权重、分数归一化、排序规则，并考虑接入 rerank。
```

### 自测 11：Hybrid Search 和 Multi Query 的区别是什么？

参考答案：

```text
Multi Query 是从一个问题生成多个检索 query，解决表达角度不足的问题。Hybrid Search 是对每个 query 使用多种检索方式，比如向量检索和关键词检索，解决单一检索器能力不足的问题。
```

### 自测 12：Hybrid Search 是否能替代 Rerank？

参考答案：

```text
不能。Hybrid Search 主要负责多路召回和初步融合，Rerank 负责在候选结果中做更精细的相关性排序。两者通常是配合关系。
```

## 面试表达

### 1 分钟版本

```text
在 RAG 项目里，我不会只依赖向量检索。向量检索适合语义相似，但对订单号、SKU、专有名词和精确条款不一定稳定；关键词检索适合精确命中，但对口语化和同义表达不够好。所以我会做 Hybrid Search，把向量结果和关键词结果按 chunk_id 去重，对不同检索器的分数做归一化，再按权重融合排序。同时我会记录结果来源，比如 vector-only、keyword-only、both，以及 top chunk 和 debug line，方便后续调权、rerank 和 bad case 分析。
```

### 3 分钟版本

```text
RAG 的检索质量不能只看最终有没有返回结果，而要看正确资料是否被召回、排序是否靠前、噪声是否可控。向量检索和关键词检索解决的问题不同。向量检索通过 embedding 找语义相似，适合用户口语化问题；关键词检索通过字面匹配找精确词，适合订单号、SKU、条款号、业务术语等场景。

所以我会把两者结合成 Hybrid Search。实现上，先分别拿到 vector_chunks 和 keyword_results，然后用 chunk_id 合并重复 chunk。由于两种检索器的原始分数不在同一个尺度上，不能直接相加，需要先做归一化，再按 vector_weight 和 keyword_weight 加权得到 hybrid_score。对于两路都命中的 chunk，会保留 retrieval_sources=["vector", "keyword"]，这是一个较强相关性信号。

真实项目里我还会补可解释报告，比如 vector_result_count、keyword_result_count、vector_only_count、keyword_only_count、both_count、overlap_chunk_ids 和 debug_lines。这样做的价值是，当 RAG 答错时，可以判断是召回问题、排序问题、权重问题、关键词提取问题，还是 metadata filter 过严。Hybrid Search 后面通常还会接 rerank 和评测集，用数据验证权重和排序效果。
```

## 本节小结

本节真正要掌握的不是多写了几个字段。

你要掌握的是这套思维：

```text
RAG 检索不是单一路径。
向量检索和关键词检索各有优势。
融合前必须处理去重、分数尺度和权重。
融合后必须保留来源和调试信息。
只有可解释，后面才谈得上调优。
```

当前项目已经具备：

```text
关键词检索
向量检索结果融合
HybridFusionReport
debug-friendly 输出
相关自动化测试
```

下一节继续学习：

```text
阶段 9 第 6 节：检索分数理解：score、distance、相似度到底怎么看
```

下一节会把本节已经碰到但没有彻底展开的问题讲清楚：

```text
为什么不同向量数据库的分数方向不同？
为什么有的分数越大越相似，有的 distance 越小越相似？
为什么 score_threshold 不能乱设？
为什么同一个阈值换模型、换库、换 distance metric 后可能完全失效？
```
