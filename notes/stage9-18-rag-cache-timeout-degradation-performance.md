# 阶段 9 第 18 节：RAG 缓存、超时、降级和性能优化

## 本节定位

本节学习 RAG 性能保护。

它接在第 17 节参数调优后面：上一节解决“质量不好时怎么调参数”，本节解决“链路变慢、超时、部分依赖不可用时，系统怎么继续稳定工作”。

## 本节学习目标

学完本节，你要能说清楚：

- 为什么 RAG 比普通接口更容易慢。
- 缓存、超时、降级分别解决什么问题。
- 为什么 RAG 缓存必须带上权限、租户、检索参数、模型和集合信息。
- `cache_hit_rate`、`timed_out_stages`、`near_timeout_stages` 分别说明什么。
- 为什么降级不是“随便编一个答案”，而是明确告诉用户当前能力边界。
- 怎么把耗时、缓存统计、降级决策整理成可排查的性能保护报告。

## 本节新增和修改

修改：

```text
projects/ai-service/app/rag/performance.py
projects/ai-service/tests/test_rag_performance.py
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

新增：

```text
notes/stage9-18-rag-cache-timeout-degradation-performance.md
```

## 一句话先讲透

RAG 性能优化不是单纯追求“更快”，而是：

```text
在不破坏权限、安全和回答质量的前提下，用缓存减少重复成本，用超时限制等待时间，用降级保证失败时也有明确、可控、可解释的返回。
```

## 基础知识铺垫

### 1. 为什么 RAG 比普通接口更容易慢

传统后端接口通常是：

```text
收到请求 -> 查数据库/Redis -> 业务处理 -> 返回结果
```

RAG 问答链路通常更长：

```text
用户问题
-> 问题改写或多路查询
-> embedding 向量化
-> 向量数据库检索
-> metadata 权限过滤
-> hybrid search 融合
-> rerank 重排序
-> prompt 拼装
-> 大模型生成
-> 引用校验/安全检查
-> 返回答案
```

链路越长，慢点越多。

每个环节都可能产生延迟：

```text
embedding 模型慢。
向量数据库网络抖动。
召回 top_k 太大。
rerank 候选太多。
prompt 上下文太长。
大模型生成耗时长。
权限过滤导致需要更多候选补位。
外部服务偶发不可用。
```

所以 RAG 性能问题不能只看“总耗时”。必须知道是哪一段慢。

### 2. 性能优化不是越快越好

RAG 的性能优化和普通接口不同，因为它同时影响：

```text
速度。
回答质量。
成本。
权限安全。
用户体验。
系统稳定性。
```

例如：

```text
top_k 调小：速度可能变快，但召回可能变差。
score_threshold 调高：噪声可能减少，但可能误杀有用资料。
rerank 关掉：成本降低，但排序质量可能下降。
缓存时间调长：命中率提高，但可能返回过期知识。
超时时间调短：接口更快失败，但可能把本来能成功的请求打断。
```

所以本节的核心不是“把所有参数调到最快”，而是学会建立一套保护边界：

```text
哪些地方可以缓存。
哪些地方必须限时。
哪些失败可以降级。
哪些情况必须明确拒绝或返回无上下文。
```

### 3. 什么是缓存

缓存就是把某次计算或查询的结果临时保存起来，下次遇到相同条件时直接复用。

在 RAG 里，最常见的是检索结果缓存：

```text
用户问同一个问题
-> 系统发现同样的检索条件以前查过
-> 直接拿上一次的 chunks
-> 少做一次 embedding/向量库检索/rerank
```

缓存可以降低：

```text
响应时间。
外部模型调用次数。
向量数据库压力。
重复问题带来的成本。
```

但缓存也有风险，尤其是 AI 应用里的 RAG 缓存。

### 4. RAG 缓存最重要的是 cache key

缓存不是简单地用用户问题当 key。

错误示例：

```text
key = "退款多久到账？"
```

这样做看似简单，但在真实系统里很危险。

原因是同一个问题，在不同上下文下可能应该拿到不同资料：

```text
不同租户的数据不同。
不同用户权限不同。
不同业务域资料不同。
不同 doc_type 可能代表 FAQ、政策、内部 SOP。
不同 top_k 会影响召回数量。
不同 score_threshold 会影响过滤结果。
不同 embedding 模型可能导致向量空间不同。
不同 collection 版本可能代表知识库版本不同。
```

所以安全的 RAG retrieval cache key 至少要考虑：

```text
query_hash
tenant_id
permission_group
business_domain
doc_type
source
top_k
score_threshold
embedding_model
embedding_dimension
collection_name 或 collection_version
```

本项目目前先做了学习版 cache key，已经包含：

```text
query_hash
top_k
score_threshold
permission_group
business_domain
doc_type
source
embedding_model
embedding_dimension
collection_name
```

这里没有把原始 query 直接放进 key，而是放 `query_hash`。这样做有两个好处：

```text
避免缓存 key 里暴露用户原始问题。
让 key 长度稳定，适合存 Redis、日志和指标。
```

### 5. 什么是 TTL

TTL 是 Time To Live，意思是缓存最多存活多久。

例如：

```text
TTL = 60 秒
```

表示一条缓存从写入开始，最多 60 秒后就过期。

TTL 解决的是“缓存不能永远相信”的问题。

RAG 知识库会更新：

```text
政策变了。
FAQ 改了。
权限变了。
文档删除了。
向量库重新索引了。
```

如果缓存永不过期，系统可能一直使用旧知识。

TTL 越长：

```text
缓存命中率通常越高。
系统成本通常越低。
返回旧数据的风险越高。
```

TTL 越短：

```text
旧数据风险越低。
缓存命中率通常越低。
系统成本可能更高。
```

真实项目一般不会只靠 TTL，还会结合：

```text
知识库版本号。
collection version。
文档更新时间。
权限版本。
主动清理缓存。
```

### 6. 什么是 cache hit rate

`cache_hit_rate` 是缓存命中率。

公式是：

```text
hit_count / (hit_count + miss_count)
```

例子：

```text
命中 20 次，未命中 80 次。
cache_hit_rate = 20 / 100 = 0.2
```

命中率低不一定代表代码错了。

可能原因包括：

```text
用户问题本来就很分散。
query rewrite 让问题变得不稳定。
cache key 组件过多，导致很难命中。
TTL 太短。
知识库更新太频繁。
业务场景不适合缓存。
```

所以看到低命中率时，不应该立刻粗暴扩大缓存，而是先分析场景。

### 7. 什么是超时

超时就是给某个操作设置最长等待时间。

例如：

```text
embedding 最多等 2 秒。
向量数据库检索最多等 1 秒。
rerank 最多等 3 秒。
大模型生成最多等 20 秒。
```

没有超时会导致一个严重问题：

```text
某个下游服务卡住，上游请求也一直卡住，线程/连接/任务不断堆积，最后整个服务被拖垮。
```

RAG 应该做分段超时，而不是只做总超时。

因为只有知道哪一段超时，才能决定怎么处理：

```text
embedding 超时：可能完全无法检索。
向量库超时：可以考虑用缓存。
rerank 超时：可以考虑退回原始召回排序。
generation 超时：可以考虑返回安全资料摘要或提示稍后重试。
security check 超时：不能放行危险答案，宁可拒绝或降级。
```

### 8. 什么是 near timeout

`near_timeout` 是“接近超时”。

例如：

```text
timeout = 1 秒
near_timeout_ratio = 0.8
耗时 >= 0.8 秒，但还没到 1 秒
```

这说明请求虽然成功了，但已经接近风险边界。

为什么要关心它？

因为生产环境里的问题通常不是突然爆炸，而是先出现趋势：

```text
平均耗时变高。
P95 变高。
越来越多请求接近超时。
偶发超时变多。
最终用户开始明显感知变慢。
```

所以 `near_timeout` 是提前预警。

本项目里用：

```text
OK
NEAR_TIMEOUT
TIMED_OUT
```

把一次操作的耗时状态分成三类。

### 9. 什么是降级

降级是指系统在正常链路不可用时，走一个能力更弱但更稳定、更安全的路径。

正常路径可能是：

```text
检索 -> rerank -> 模型生成 -> 引用校验 -> 返回完整回答
```

降级路径可能是：

```text
使用安全的检索缓存。
返回已检索到的资料片段，不让模型继续生成。
返回明确的无上下文/服务暂不可用提示。
```

降级不是偷懒，也不是让模型随便猜。

一个合格的 RAG 降级必须满足：

```text
用户知道系统当前没有完整完成正常流程。
系统不能编造没有依据的内容。
权限和安全边界不能因为降级被绕过。
日志里能记录为什么降级。
后续能统计降级发生频率。
```

### 10. 三种常见 RAG 降级模式

第一种：使用缓存检索结果。

```text
mode = USE_CACHED_RETRIEVAL
```

适合场景：

```text
向量库或 rerank 短暂失败。
系统手里有同一权限范围、同一检索条件下的缓存 chunks。
缓存没有明显过期风险。
```

风险：

```text
cache key 不安全会导致跨用户、跨租户、跨权限泄漏。
缓存太旧可能导致知识不准确。
```

第二种：返回安全兜底资料。

```text
mode = RETURN_SAFE_FALLBACK
```

适合场景：

```text
检索成功了，但模型生成失败。
已有 chunks 经过权限和安全过滤。
系统可以告诉用户“当前无法生成完整回答，但找到了这些资料”。
```

风险：

```text
用户拿到的不是完整自然语言答案。
资料片段可能需要用户自己判断。
```

第三种：返回无上下文结果。

```text
mode = RETURN_NO_CONTEXT
```

适合场景：

```text
没有缓存。
没有安全 chunks。
关键依赖失败。
继续回答会变成无依据猜测。
```

风险：

```text
用户体验变差。
但这比胡编乱造更安全。
```

### 11. 哪些内容不适合随便缓存

RAG 里不建议随便缓存：

```text
包含敏感个人信息的完整回答。
带有用户私有上下文的模型输出。
权限边界不明确的检索结果。
没有知识库版本标记的长期检索结果。
写操作结果。
安全审核未通过的内容。
```

尤其要记住：

```text
读操作可以谨慎缓存。
写操作和权限不清晰的数据不要随便缓存。
```

### 12. 性能保护报告有什么用

真实系统里，性能问题不能只靠感觉排查。

如果用户说“RAG 最近很慢”，你需要回答：

```text
是哪一段慢？
是 embedding 慢，还是向量库慢？
是 rerank 候选太多，还是模型生成太慢？
缓存命中率是多少？
有没有超时？
有没有降级？
降级是用了缓存，还是返回了无上下文？
这些问题的风险是什么？
下一步应该先改什么？
```

这就是性能保护报告的价值。

它把零散证据整理成结构化结论：

```text
timing_count
timed_out_stages
near_timeout_stages
cache_hit_rate
degradation_mode
recommendations
high_priority_count
```

这样以后做日志、Tracing、监控、告警、评测分析时，都有可以复用的结构。

## 本节主题系统讲解

### 1. 第 18 节在阶段 9 里的位置

阶段 9 前面几节主要围绕“质量”：

```text
Query Rewrite：让问题更适合检索。
Multi Query：提高召回覆盖。
Hybrid Search：融合关键词和向量。
Rerank：改善排序。
引用校验：让回答有出处。
Prompt Injection 防护：保护安全边界。
评测集：定义什么叫答得好。
检索指标：衡量召回和排序。
回答质量评测：衡量答案是否覆盖要点。
Bad Case 分析：判断错在哪一层。
参数调优：决定下一步调什么。
```

本节开始补“稳定性和性能”。

因为真实 RAG 不只是要答得准，还要：

```text
请求不能无限等待。
依赖失败不能拖垮系统。
重复请求不能每次都花完整成本。
降级时不能越权、不能胡编、不能让用户误以为答案完整可靠。
```

### 2. 本节的完整保护链路

可以把本节理解成一条性能保护链：

```text
请求进入 RAG
-> 为可缓存的检索结果生成安全 cache key
-> 尝试使用缓存减少重复检索成本
-> 每个关键 stage 都记录耗时和 timeout 状态
-> 如果接近超时，生成性能预警
-> 如果已经超时，选择降级方式
-> 把耗时、缓存和降级信息整理成报告
-> 给出下一步优化建议
```

这条链路不是为了替代 RAG 主流程，而是围绕主流程做保护。

### 3. cache key 负责什么

`build_retrieval_cache_key()` 负责构造检索缓存 key。

它做了几件关键事情：

```text
去掉 query 前后的空格。
拒绝空问题。
校验 top_k、score_threshold、embedding_dimension。
把 query 转成 hash。
把影响检索结果的条件放进 components。
把 components 做稳定 JSON 序列化。
再对序列化内容生成 digest。
最后得到 namespace:digest 形式的 key。
```

它的学习重点不是 hash 算法本身，而是安全边界：

```text
同一个用户问题，只要权限、参数、模型或集合变了，就应该是不同缓存。
```

否则缓存会把一个上下文的结果错误复用到另一个上下文。

### 4. TTL cache 负责什么

`InMemoryTtlCache` 是一个学习用内存缓存。

它支持：

```text
set：写入缓存。
get：读取缓存。
clear：清空缓存。
stats：查看命中、未命中、写入、淘汰、当前数量。
ttl_seconds：控制过期时间。
max_entries：控制最大缓存条数。
```

它不是生产级缓存。

真实项目通常会用：

```text
Redis
Caffeine
本地缓存 + Redis 二级缓存
网关层缓存
专门的向量检索结果缓存
```

本节先用内存版，是为了把缓存基本原理学清楚，避免一上来被 Redis 配置、序列化、分布式一致性分散注意力。

### 5. timing 负责什么

`assess_operation_timing()` 负责判断一个 stage 的耗时状态。

输入：

```text
stage
elapsed_ms
timeout_seconds
near_timeout_ratio
```

输出：

```text
RagOperationTiming
```

状态有三种：

```text
OK：耗时正常。
NEAR_TIMEOUT：接近超时，需要关注。
TIMED_OUT：已经达到或超过超时预算，需要降级或失败处理。
```

这一步能把“感觉慢”变成“哪一段慢、慢到什么程度”。

### 6. degradation decision 负责什么

`choose_degradation_decision()` 负责在失败时选择兜底路径。

当前规则是：

```text
如果有可用检索缓存，优先使用缓存。
否则如果有安全 chunks，返回安全兜底。
否则返回无上下文结果。
```

这个顺序体现了一个原则：

```text
先复用可信证据，再返回有限证据，最后明确拒绝无依据回答。
```

它没有让模型在没有上下文时自由发挥。

这是 RAG 系统非常重要的安全底线。

### 7. performance protection report 负责什么

`build_rag_performance_protection_report()` 把三类证据合并起来：

```text
timings：各 stage 的耗时和超时状态。
cache_stats：缓存命中、未命中、写入、淘汰。
degradation_decision：本次是否降级，以及降级模式是什么。
```

然后输出：

```text
timed_out_stages
near_timeout_stages
cache_hit_rate
degradation_mode
recommendations
```

这些 recommendations 不只是“报错”，而是带有：

```text
area：问题属于 cache、timeout、degradation、retrieval、rerank 还是 generation。
priority：优先级。
reason：为什么给这个建议。
evidence：证据是什么。
suggested_action：建议怎么处理。
risk：这样处理有什么风险。
```

这就让性能排查更像工程决策，而不是凭感觉改参数。

### 8. 为什么 recommendation 里要写 risk

很多性能优化动作都有副作用。

例如：

```text
减少 top_k 可能让召回变差。
提高 score_threshold 可能误杀相关文档。
增加缓存大小会增加内存占用。
延长 TTL 可能返回旧知识。
缩短 timeout 可能让可成功请求提前失败。
使用缓存降级可能带来数据泄漏风险。
```

所以报告只给 `suggested_action` 不够，还要同时写 `risk`。

这能训练你形成生产工程思维：

```text
任何优化都要讲收益，也要讲代价。
```

### 9. 本节暂时不做什么

本节不接入真实 Redis。

原因：

```text
上一阶段已经学过 Redis 接入。
本节重点是 RAG 性能保护模型，不是 Redis 客户端配置。
```

本节不真实调用 embedding、rerank 或大模型。

原因：

```text
性能保护逻辑应该可以通过 fake timing、fake stats 和结构化对象稳定测试。
自动化测试不应该依赖真实模型费用、网络和可用性。
```

本节不做完整监控系统。

原因：

```text
可观测性会放到下一节，专门学习 query、召回、rerank、引用和耗时怎么记录。
```

## 本节代码讲解

### 1. `RagPerformanceProtectionRecommendation`

这个模型表示一条性能保护建议。

核心字段：

```text
area：建议属于哪个区域。
priority：优先级。
reason：为什么提出这个建议。
evidence：证据。
suggested_action：建议动作。
risk：动作风险。
```

这里的关键不是字段多，而是它把“性能问题”变成了可以解释的结构。

例如：

```text
area = timeout
priority = high
reason = vector_store reached its timeout budget
evidence = elapsed_ms=1200, timeout_seconds=1
suggested_action = 设置明确超时并进入降级路径
risk = 超时过严可能拒绝本来能成功的慢请求
```

这样以后无论输出到日志、接口、评测报告还是面试表达，都能说清楚。

### 2. `RagPerformanceProtectionReport`

这个模型表示一次性能分析报告。

它不是单条建议，而是汇总结果：

```text
timing_count：统计了多少个 stage。
timed_out_stages：哪些 stage 已经超时。
near_timeout_stages：哪些 stage 接近超时。
cache_hit_rate：缓存命中率。
degradation_mode：当前采用了哪种降级模式。
recommendation_count：建议数量。
high_priority_count：高优先级建议数量。
recommendations：具体建议列表。
```

它的价值在于把多个来源合并：

```text
耗时证据 + 缓存证据 + 降级证据
```

然后变成一个统一报告。

### 3. `build_rag_performance_protection_report()`

这个函数是本节新增的核心入口。

它做的事情可以拆成四步：

```text
1. 从 timings 里找出 timed_out 和 near_timeout stage。
2. 从 cache_stats 里计算 cache_hit_rate。
3. 根据 timing/cache/degradation 生成建议。
4. 去重后返回结构化 report。
```

重点是它没有直接执行 RAG，也没有真实访问 Redis 或模型。

它只是负责“分析证据并生成建议”。

这是一种很重要的分层：

```text
执行层：负责真正调用向量库、rerank、模型。
观测层：负责记录耗时、缓存统计和降级决策。
分析层：负责把证据变成建议。
```

本节做的是分析层。

### 4. `format_rag_performance_protection_report()`

这个函数把结构化报告转成文本行。

它适合用于：

```text
命令行 smoke 输出。
本地调试。
学习笔记展示。
简单日志。
```

真实项目里更常见的是输出 JSON，再由日志平台、APM、Tracing 系统展示。

### 5. 本节测试看什么

本节测试重点看四类行为：

```text
超时 stage 会产生 timeout 和 degradation 建议。
低 cache_hit_rate 会产生 cache review 建议。
near_timeout 的 rerank 会产生 rerank 优化建议。
safe fallback 降级会产生明确的 degradation 建议。
```

测试不真实调用大模型，也不真实访问向量数据库。

原因是这些测试的目标是验证“性能保护判断规则”，不是验证外部服务可用性。

## 常见误区

### 误区 1：RAG 慢了就把 top_k 调小

不一定。

如果召回本来就差，继续调小 top_k 会让答案更差。

应该先看：

```text
慢的是检索、rerank 还是生成。
Recall 是否已经足够。
候选数量是不是过多。
上下文是不是太长。
```

### 误区 2：缓存 key 只用用户问题

这是非常危险的做法。

RAG 缓存必须考虑权限、租户、业务域、检索参数、模型和集合版本。

否则可能把 A 用户能看的资料缓存给 B 用户。

### 误区 3：缓存命中率低就一定是坏事

不一定。

有些业务问题本来就高度分散，命中率低是正常的。

缓存命中率要结合业务场景、TTL、query rewrite 和用户行为一起看。

### 误区 4：降级就是返回一个模糊话术

不是。

降级要有明确策略：

```text
能安全用缓存就用缓存。
能安全展示资料就展示资料。
都不行就明确说无法根据知识库回答。
```

不能让模型在没有证据时继续编。

### 误区 5：只设置接口总超时就够了

不够。

总超时只能告诉你“整个请求慢了”，但不能告诉你是哪段慢。

RAG 更需要分 stage 记录：

```text
embedding
vector_store
rerank
generation
security
```

这样才能排查和优化。

### 误区 6：性能优化一定会降低质量

也不一定。

合理优化可以同时提升体验和稳定性。

例如：

```text
缓存重复检索结果。
减少无意义重复 embedding。
限制明显过多的 rerank 候选。
给慢依赖加超时。
失败时返回明确边界。
```

问题在于不能盲目优化，要用指标和 bad case 证据指导。

## 本节练习

### 练习 1：为什么 RAG 缓存 key 不能只用用户问题？

答案：

因为同一个用户问题在不同权限、租户、业务域、检索参数、embedding 模型、向量集合版本下，应该得到不同的检索结果。如果只用问题当 key，可能把一个用户或一个权限范围下的资料错误复用给另一个用户，造成越权和数据泄漏。

### 练习 2：`cache_hit_rate = 0.1` 一定说明代码有 bug 吗？

答案：

不一定。它只说明缓存命中率低。原因可能是用户问题本来就分散、TTL 太短、query rewrite 导致 query 不稳定、cache key 组件过细、业务场景不适合缓存，也可能确实是缓存设计有问题。要结合业务和日志判断。

### 练习 3：为什么要区分 `NEAR_TIMEOUT` 和 `TIMED_OUT`？

答案：

`TIMED_OUT` 表示已经超过超时预算，需要立即失败处理或降级。`NEAR_TIMEOUT` 表示还没失败，但已经接近风险边界，适合做预警和优化。区分它们可以提前发现性能趋势，而不是等大量请求失败后再处理。

### 练习 4：如果 rerank 接近超时，你会优先检查什么？

答案：

优先检查 rerank 候选数量是否过多、rerank 模型或服务是否变慢、网络是否不稳定、是否可以减少进入 rerank 的候选、是否需要 batch 或 fallback。不能直接关闭 rerank，因为它可能明显影响排序质量。

### 练习 5：为什么 generation 超时时不能让模型无上下文继续回答？

答案：

因为 RAG 的核心是基于检索证据回答。如果模型生成阶段失败或上下文不可用，还让模型自由回答，就可能产生无依据内容。正确做法是使用安全缓存、返回已检索资料兜底，或明确告诉用户当前无法根据知识库回答。

## 自测题

### 自测 1：RAG 性能保护主要由哪三类机制组成？

答案：

缓存、超时、降级。

缓存减少重复计算和重复检索成本；超时限制每个关键依赖的最长等待时间；降级保证失败时返回可控结果，而不是无限等待或无依据编造。

### 自测 2：`timed_out_stages` 和 `near_timeout_stages` 有什么区别？

答案：

`timed_out_stages` 记录已经达到或超过超时预算的 stage。`near_timeout_stages` 记录尚未超时但接近超时预算的 stage。前者通常需要失败处理或降级，后者通常用于预警和性能优化。

### 自测 3：使用缓存降级时，最大的安全风险是什么？

答案：

最大的风险是缓存 key 不安全导致数据越权。例如没有把 tenant、permission_group、业务域、检索参数、模型和集合版本放进 key，可能把一个用户可见的检索结果返回给另一个无权用户。

### 自测 4：为什么性能报告里的建议要包含 `evidence`？

答案：

因为没有证据的建议很难判断是否可靠。`evidence` 可以说明建议来自哪个耗时、哪个命中率、哪个降级模式或哪个 stage，让排查和优化有依据。

### 自测 5：为什么建议里还要包含 `risk`？

答案：

因为性能优化通常有副作用。比如减少 top_k 可能降低召回，提高 threshold 可能误杀资料，延长 TTL 可能返回旧知识，缩短 timeout 可能提前中断本可成功的请求。写出 risk 可以帮助开发者做更稳妥的工程决策。

## 本节小结

本节你学到的是 RAG 的性能保护思路：

```text
缓存：减少重复成本，但必须守住权限和数据新鲜度。
超时：限制等待时间，但要按 stage 记录，不能只看总耗时。
降级：失败时走可控路径，不能让模型无依据编造。
性能保护报告：把耗时、缓存、降级证据变成可解释建议。
```

到这里，阶段 9 已经从“检索质量优化”扩展到“质量 + 稳定性 + 性能保护”。下一节继续学习 RAG 可观测性，重点是把 query、召回、rerank、引用和耗时记录下来，方便真实排查。
