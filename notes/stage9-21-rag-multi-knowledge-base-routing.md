# 阶段 9 第 21 节：RAG 多知识库路由

## 本节定位

本节学习 RAG 多知识库路由。

它接在第 20 节数据更新后面：上一节解决“知识库变了怎么更新”，本节解决“用户问题来了以后，应该查哪个知识库，而不是所有资料混在一起查”。

## 本节学习目标

学完本节，你要能说清楚：

- 什么是多知识库路由。
- 为什么不能所有问题都查同一个大知识库。
- 路由、意图识别、metadata filter 的区别。
- collection、business_domain、doc_type、permission_group 在路由中的作用。
- 路由错了会造成哪些 RAG bad case。
- 多知识库路由如何影响缓存、评测、可观测性和权限安全。

## 本节新增和修改

新增：

```text
projects/ai-service/app/rag/knowledge_routing.py
projects/ai-service/tests/test_rag_knowledge_routing.py
notes/stage9-21-rag-multi-knowledge-base-routing.md
```

修改：

```text
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

## 一句话先讲透

RAG 多知识库路由的本质是：

```text
在真正检索之前，先根据用户问题、意图、业务域、文档类型和权限范围，决定应该查哪些知识库，再对选中的知识库做检索和过滤。
```

## 基础知识铺垫

### 1. 什么是知识库

在 RAG 里，知识库不是一个固定技术名词。

它可以表示：

```text
一个业务资料集合。
一个向量数据库 collection。
一个文档目录。
一个文档类型集合。
一套有独立权限边界的知识区域。
```

例如客服场景里可以有：

```text
退款退货政策知识库。
物流发货政策知识库。
账号安全 FAQ 知识库。
售后流程 SOP 知识库。
内部升级处理流程知识库。
```

这些资料如果全部混在一起检索，系统虽然能跑，但质量和安全都会变差。

### 2. 什么是多知识库路由

多知识库路由就是：

```text
用户问题 -> 判断应该查哪个或哪些知识库 -> 再执行检索。
```

例如：

```text
用户问：质量问题退货运费谁承担？
应该查：退款退货政策知识库。

用户问：账号被冻结怎么办？
应该查：账号安全 FAQ 知识库。

用户问：售后换货流程怎么走？
应该查：售后流程 SOP 知识库。

用户问：内部升级审核流程怎么操作？
应该查：内部升级处理流程知识库，但前提是用户有内部权限。
```

它不是最终回答，也不是检索本身。

它是检索前的选择动作。

### 3. 为什么不能所有资料都混在一起检索

如果所有资料都在一个大知识库里，常见问题是：

```text
召回噪声变多。
top_k 被无关文档占满。
rerank 压力变大。
权限边界更容易出错。
缓存 key 更复杂。
评测 bad case 更难归因。
可观测性统计不清楚。
```

例如用户问：

```text
退款多久到账？
```

如果全库检索，可能召回：

```text
退款政策。
物流时效。
账号安全。
售后工单流程。
内部客服 SOP。
```

模型看到太多无关上下文，就更容易答偏。

多知识库路由的目的就是减少这种噪声：

```text
先选对范围，再在范围内检索。
```

### 4. 多知识库路由和 query intent 的区别

query intent 回答的是：

```text
这个问题要走什么大流程？
```

例如：

```text
policy_lookup：查政策类 RAG。
process_lookup：查流程类 RAG。
order_lookup：查订单工具。
ticket_creation：走工单创建 Agent。
smalltalk：直接回答。
unsafe：安全拦截。
unclear：追问。
```

多知识库路由回答的是：

```text
如果这个问题要走 RAG，那具体查哪个知识库？
```

所以两者的关系是：

```text
query intent 先判断是否走 RAG。
knowledge routing 再判断走哪个 RAG 知识库。
```

例如：

```text
订单 A1001 到哪里了？
query intent = order_lookup
不走 RAG，走工具调用。

质量问题退货运费谁承担？
query intent = policy_lookup
走 RAG，再路由到 refund policy 知识库。
```

### 5. 多知识库路由和 metadata filter 的区别

metadata filter 回答的是：

```text
在已经选定的检索范围里，哪些 metadata 条件必须满足？
```

例如：

```text
tenant_id = default
permission_group in customer_service
business_domain in refund
doc_type in policy, faq
status not in archived, deleted
```

路由回答的是：

```text
先查哪个 collection 或知识库。
```

filter 回答的是：

```text
在这个知识库里，再过滤哪些文档。
```

一个简单类比：

```text
路由：先决定去哪家图书馆。
过滤：进了图书馆后，只看某个书架、某个分类、某种权限能看的书。
```

所以路由不能替代 filter，filter 也不能完全替代路由。

### 6. collection 是什么

在向量数据库里，collection 通常表示一组向量数据。

例如：

```text
kb_customer_policy
kb_account_security
kb_customer_process
kb_internal_process
```

不同 collection 可以有不同：

```text
向量维度。
距离度量。
索引参数。
权限边界。
文档类型。
更新频率。
缓存策略。
```

真实项目里，多知识库路由经常会决定：

```text
查哪个 collection。
```

当前项目之前主要使用一个学习用 collection。

本节先用路由模型表达多 collection 思路，不要求你真实创建多个 Qdrant collection。

### 7. business_domain 是什么

business_domain 表示业务领域。

例如：

```text
refund：退款退货。
order：订单。
logistics：物流。
account：账号。
security：安全。
process：流程。
internal：内部处理。
```

它适合做业务层面的筛选。

例如：

```text
退款问题 -> business_domain=refund
物流问题 -> business_domain=logistics
账号安全问题 -> business_domain=account/security
```

business_domain 可以在同一个 collection 内做 filter，也可以帮助选择不同知识库。

### 8. doc_type 是什么

doc_type 表示文档类型。

例如：

```text
policy：政策。
faq：常见问题。
sop：操作规程。
process：流程说明。
internal：内部文档。
```

同一个问题，有时业务域一样，但文档类型不同。

例如：

```text
退款多久到账？
更适合查 policy 或 FAQ。

客服怎么处理退款投诉？
更适合查 SOP 或 process。
```

这就是 doc_type 的价值。

它帮助系统区分：

```text
给用户解释规则。
指导客服操作流程。
查内部处理步骤。
```

### 9. permission_group 是什么

permission_group 表示权限组。

例如：

```text
public
customer_service
internal_staff
admin
```

RAG 不能只考虑相关性，还必须考虑权限。

例如：

```text
普通客服可以看客户服务政策。
内部员工可以看升级处理 SOP。
管理员可以看更高权限资料。
```

如果路由没有权限意识，可能出现：

```text
用户问内部流程。
系统检索到了内部 SOP。
模型把内部处理规则说给无权限用户。
```

这是严重安全问题。

### 10. 逻辑知识库和物理知识库

知识库可以分成逻辑和物理两层理解。

逻辑知识库：

```text
退款政策知识库。
账号安全 FAQ。
售后流程 SOP。
```

物理知识库：

```text
Qdrant collection。
Milvus collection。
数据库表。
对象存储目录。
```

有时一个逻辑知识库对应一个物理 collection。

有时多个逻辑知识库共用一个 collection，只靠 metadata filter 区分。

例如：

```text
customer_policy_refund 和 customer_policy_logistics
都可以在 kb_customer_policy collection 里。
```

本节代码就体现了这种情况：

```text
不同 knowledge_base_id 可以指向同一个 collection_name。
```

### 11. 多知识库路由能解决什么问题

它主要解决：

```text
减少无关召回。
降低 rerank 候选噪声。
让权限边界更清晰。
让缓存命中范围更明确。
让评测按知识库拆分。
让可观测性按知识库统计。
让 bad case 更容易归因。
```

例如：

```text
账号安全问题答错。
```

如果没有路由，你不知道是不是全库噪声影响。

如果有路由记录：

```text
knowledge_base_id=account_security_faq
```

那就能先看账号安全知识库本身的召回和内容质量。

### 12. 多知识库路由不能解决什么问题

它不能替代：

```text
检索质量优化。
rerank。
metadata filter。
权限系统。
引用校验。
Prompt Injection 防护。
评测集。
```

路由只能减少搜索范围。

如果某个知识库内部文档质量差，路由选对了也可能答错。

如果权限字段本身错误，路由也不能完全兜底。

如果用户问题表达模糊，路由可能也需要 fallback 或追问。

### 13. 路由错了会产生哪些 bad case

常见路由 bad case：

```text
应该查退款知识库，却查了物流知识库。
应该查流程 SOP，却查了政策 FAQ。
应该走订单工具，却错误走 RAG。
应该走安全拦截，却查了普通知识库。
应该查内部知识库，但用户无权限。
问题跨多个知识库，但只查了一个。
```

对应后果：

```text
召回不到正确资料。
召回很多噪声。
模型根据错误上下文回答。
引用看起来存在但引用错范围。
权限泄露。
bad case 分析误判为检索或模型问题。
```

### 14. 路由和 fallback

路由不可能永远准确。

有些问题很泛：

```text
你们有哪些政策文档？
```

它没有明显的退款、物流、账号关键词。

这时可以使用 fallback 知识库：

```text
customer_policy_general
```

fallback 的特点是：

```text
覆盖范围更宽。
相关性可能更弱。
需要记录 warning。
后续可观测性要能看出是 fallback。
```

fallback 不是错误，但需要被记录。

因为 fallback 用多了，说明路由规则或知识库设计可能还不够细。

### 15. 路由和缓存的关系

第 18 节学过 RAG 缓存。

多知识库路由会影响 cache key。

安全的检索缓存 key 应该包含：

```text
knowledge_base_id。
collection_name。
business_domains。
doc_types。
permission_groups。
top_k。
score_threshold。
embedding_model。
query_hash。
```

否则可能出现：

```text
同一个 query 在退款知识库的结果，被错误复用到账号安全知识库。
```

所以路由结果必须进入缓存范围。

### 16. 路由和评测的关系

评测集应该覆盖路由。

不只评估：

```text
检索有没有命中。
回答有没有正确。
```

还要评估：

```text
这个问题是否查了正确知识库。
是否错误查了内部知识库。
是否漏查了第二个相关知识库。
fallback 是否合理。
```

否则你可能会看到：

```text
检索指标低。
```

但真正原因是：

```text
路由错了。
```

### 17. 路由和可观测性的关系

第 19 节学过可观测性。

多知识库路由需要记录：

```text
knowledge_base_id。
collection_name。
route_score。
matched_keywords。
route reasons。
route warnings。
payload_filter。
```

这样才能回答：

```text
这次为什么查这个知识库？
有没有 fallback？
有没有多路由？
有没有因为权限过滤掉候选知识库？
```

## 本节主题系统讲解

### 1. 第 21 节在阶段 9 里的位置

阶段 9 前面学过：

```text
query intent：判断问题走哪个大流程。
metadata filter：在检索侧过滤用户、租户、权限、业务域。
bad case analysis：判断错误属于哪一层。
observability：记录排查证据。
data update：维护知识库数据生命周期。
```

本节把这些连接起来：

```text
query intent
-> knowledge routing
-> metadata filter
-> retrieval
-> rerank
-> generation
```

也就是说，knowledge routing 位于：

```text
意图识别之后，真正检索之前。
```

### 2. 本节新增的核心模型

本节新增：

```text
RagKnowledgeBaseDefinition
RagKnowledgeRoute
RagKnowledgeRouteDecision
RuleBasedRagKnowledgeRouter
route_rag_knowledge_bases()
```

它们分别负责：

```text
Definition：定义有哪些知识库。
Route：一次请求选中的单个知识库。
Decision：一次请求完整路由结果。
Router：执行路由规则。
route_rag_knowledge_bases：对外入口。
```

### 3. `RagKnowledgeBaseDefinition` 负责什么

它描述一个知识库。

字段包括：

```text
knowledge_base_id。
collection_name。
display_name。
supported_intents。
business_domains。
doc_types。
permission_groups。
keywords。
priority。
is_fallback。
```

这里的关键是：

```text
一个知识库不只是 collection，它还带业务边界、文档类型边界和权限边界。
```

### 4. 默认知识库目录

本节定义了几个学习用知识库：

```text
customer_policy_refund：退款退货政策。
customer_policy_logistics：订单物流政策。
account_security_faq：账号安全 FAQ。
customer_service_process：客服流程 SOP。
internal_escalation_process：内部升级处理流程。
customer_policy_general：通用政策 fallback。
```

它们是学习版目录，不要求你现在真实创建这些 collection。

重点是理解真实项目会有类似划分。

### 5. 路由规则如何工作

规则版路由做几步：

```text
1. 先拿 query intent。
2. 如果不是 RAG intent，直接不选知识库。
3. 找 supported_intents 匹配的知识库。
4. 用关键词匹配知识库。
5. 用 access_scope 过滤无权限知识库。
6. 生成 route_score。
7. 排序并选择前 max_routes 个。
8. 输出 warnings 和 debug lines。
```

这不是最终生产级 AI 路由器。

它是为了让你先学会路由的工程结构。

### 6. route_score 代表什么

`route_score` 表示这次 query 和某个知识库的匹配程度。

当前学习版主要依据：

```text
intent 是否匹配。
关键词是否命中。
知识库 priority。
是否 fallback。
```

真实项目里还可以加入：

```text
embedding router。
分类模型。
历史点击率。
知识库质量分。
业务规则优先级。
多轮会话上下文。
```

### 7. access_scope 如何影响路由

`access_scope` 会限制：

```text
permission_groups。
business_domains。
doc_types。
tenant_id。
status exclusions。
```

例如用户只有：

```text
permission_groups=["customer_service"]
```

那他不能路由到：

```text
permission_groups=["internal_staff", "admin"]
```

这时路由会记录：

```text
RAG_ROUTE_CANDIDATE_FILTERED_BY_ACCESS_SCOPE
```

这说明有候选知识库因为权限范围被过滤了。

### 8. payload_filter 如何生成

选中知识库后，路由会生成 payload filter。

例如退款政策路由可能生成：

```text
tenant_id = default
permission_group in customer_service
business_domain in refund
doc_type in policy, faq
status not in archived
```

这样检索时就不是“全库乱查”，而是在路由选中的范围内查。

### 9. 多路由什么时候合理

有些问题确实跨知识库。

例如：

```text
账号安全和退款规则分别是什么？
```

它可能需要同时查：

```text
account_security_faq
customer_policy_refund
```

所以路由支持 `max_routes`。

但多路由也有风险：

```text
召回范围扩大。
噪声增加。
成本增加。
回答更复杂。
引用更难解释。
```

因此多路由应该被记录：

```text
RAG_ROUTE_MULTIPLE_KNOWLEDGE_BASES_SELECTED
```

### 10. 本节暂时不做什么

本节不真实创建多个 Qdrant collection。

原因：

```text
重点是先学路由边界，真实 collection 切分属于部署和数据架构问题。
```

本节不接入 LLM 路由器。

原因：

```text
先用规则版把结构学清楚，后续再考虑模型分类或 embedding router。
```

本节不把路由接进完整 RAG pipeline。

原因：

```text
当前阶段还在逐个补 RAG 进阶组件，后续会整理组合边界。
```

## 本节代码讲解

### 1. `RagKnowledgeBaseDefinition`

这个模型定义知识库。

重点字段：

```text
knowledge_base_id：逻辑知识库 ID。
collection_name：物理向量 collection。
supported_intents：支持哪些 query intent。
business_domains：业务域。
doc_types：文档类型。
permission_groups：权限组。
keywords：规则版路由关键词。
is_fallback：是否兜底知识库。
```

它让知识库不再只是一个字符串，而是带边界的结构。

### 2. `RagKnowledgeRoute`

这个模型表示一次请求选中的某个知识库。

它包含：

```text
knowledge_base_id。
collection_name。
route_score。
matched_keywords。
business_domains。
doc_types。
permission_groups。
payload_filter。
reasons。
```

它既告诉系统查哪里，也告诉开发者为什么查这里。

### 3. `RagKnowledgeRouteDecision`

这个模型表示完整路由决策。

它包含：

```text
normalized_query。
intent。
should_use_rag。
selected_route_count。
fallback_used。
no_route_reason。
routes。
warnings。
debug_lines。
```

如果问题不应该走 RAG，比如订单查询，它会返回：

```text
should_use_rag = false
routes = []
warning = RAG_ROUTE_QUERY_INTENT_NOT_RAG
```

### 4. `RuleBasedRagKnowledgeRouter`

这是规则版路由器。

它适合学习：

```text
先判断 intent。
再匹配知识库关键词。
再根据权限过滤。
再排序选择 routes。
```

真实项目可以把这个替换成：

```text
模型分类器。
embedding 相似度路由。
规则 + 模型混合路由。
人工配置的业务路由表。
```

### 5. 本节测试重点

测试覆盖：

```text
退款问题路由到 customer_policy_refund。
流程问题路由到 customer_service_process。
订单查询不走 RAG 路由。
内部知识库会被 customer_service 权限过滤。
泛政策问题会使用 fallback policy。
跨主题问题可以返回多个 route。
自定义知识库目录可以注入。
```

这些测试不真实访问向量库。

因为本节验证的是路由决策，不是检索执行。

## 常见误区

### 误区 1：有 metadata filter 就不需要路由

不对。

filter 是在已选范围内过滤，路由是先选择查哪个知识库。

只有 filter 没有路由，系统仍可能在过大的范围里检索，噪声和成本都会增加。

### 误区 2：路由只看关键词就够了

不够。

关键词是学习版做法。

真实项目还要考虑：

```text
query intent。
权限。
业务域。
多轮上下文。
知识库覆盖范围。
fallback。
评测效果。
```

### 误区 3：路由选中内部知识库就可以直接查

不行。

还必须检查用户权限。

内部知识库不能只靠“问题里有内部两个字”就放行。

### 误区 4：一个问题只能查一个知识库

不一定。

跨主题问题可能需要多路由。

但多路由会增加噪声、成本和引用复杂度，所以要限制 `max_routes` 并记录 warning。

### 误区 5：fallback 知识库就是万能知识库

不是。

fallback 是兜底，不是长期依赖。

如果大量请求都走 fallback，说明路由规则或知识库划分需要优化。

### 误区 6：路由错了就是检索问题

不一定。

如果先查错了知识库，后面的 retrieval、rerank、generation 都会被错误范围影响。

bad case 分析时要单独看 route decision。

## 本节练习

### 练习 1：为什么多知识库路由要放在 query intent 后面？

答案：

因为 query intent 先判断问题是否应该走 RAG。如果问题是订单查询、工单创建、闲聊或安全风险，就不应该进入知识库路由。只有确定是 RAG 类型问题后，才需要继续判断查哪个知识库。

### 练习 2：路由和 metadata filter 的区别是什么？

答案：

路由决定查哪个知识库或 collection，metadata filter 决定在选中的知识库里过滤哪些文档。路由是检索范围选择，filter 是检索条件约束，两者应该配合使用。

### 练习 3：为什么内部知识库路由必须结合权限？

答案：

因为内部知识库可能包含普通用户或普通客服不能看的资料。如果只根据 query 关键词路由到内部知识库，而不检查 permission_group，就可能造成内部资料泄露。

### 练习 4：为什么 fallback 路由要记录 warning？

答案：

因为 fallback 表示系统没有命中更精确的知识库，只能使用更宽泛的范围。它不一定错误，但说明这次检索范围更宽、噪声风险更高，后续应该通过可观测性统计 fallback 是否过多。

### 练习 5：多路由有什么好处和风险？

答案：

好处是可以处理跨主题问题，例如同时涉及账号安全和退款规则。风险是召回范围变大、噪声增加、成本增加、引用更复杂，所以需要限制数量并记录 warning。

## 自测题

### 自测 1：多知识库路由主要解决什么问题？

答案：

它解决用户问题应该查哪个知识库的问题，避免所有资料混在一起检索导致噪声、权限风险和 bad case 难以归因。

### 自测 2：本节路由决策里最重要的几个输出是什么？

答案：

`knowledge_base_id`、`collection_name`、`route_score`、`matched_keywords`、`business_domains`、`doc_types`、`permission_groups`、`payload_filter`、`warnings`。

### 自测 3：为什么路由结果应该进入缓存 key？

答案：

因为同一个 query 在不同知识库里会得到不同检索结果。如果缓存 key 不包含 knowledge_base_id、collection_name、业务域、文档类型和权限范围，就可能把一个知识库的结果错误复用到另一个知识库。

### 自测 4：路由错了会影响后续哪些环节？

答案：

会影响 retrieval、rerank、context compression、generation、citation、evaluation、observability 和 bad case analysis。因为后续所有环节都基于路由选中的检索范围。

### 自测 5：为什么本节没有直接接入真实多个 Qdrant collection？

答案：

因为本节重点是学习多知识库路由的工程边界和结构。真实多个 collection 涉及部署、数据迁移、索引配置和运维成本，适合在理解路由模型后再做。

## 本节小结

本节你学到的是：

```text
query intent 判断是否走 RAG。
knowledge routing 决定查哪个知识库。
metadata filter 在选中的知识库范围内过滤文档。
权限范围必须参与路由。
fallback 和多路由都要被记录。
路由结果会影响缓存、评测、可观测性和 bad case 分析。
```

下一节学习 RAG 与 Agent 的组合边界，重点讲清楚：

```text
RAG 负责查资料，Agent 负责流程决策和工具编排。
```
