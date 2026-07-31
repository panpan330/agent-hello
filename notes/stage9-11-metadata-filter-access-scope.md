# 阶段 9 第 11 节：Metadata Filter：用户、租户、权限、业务域过滤

## 本节定位

本节学习：

```text
RAG 检索时，如何把“当前用户能看哪些资料”变成可执行的 metadata filter。
```

前面我们学了很多检索质量优化：

```text
Query Rewrite：让问题更适合检索。
Multi Query：从多个角度检索。
Hybrid Search：关键词 + 向量融合。
Rerank：召回后重排序。
Context Compression：进入模型前压缩上下文。
Citation Verification：回答后校验引用来源。
```

这些都在提升“相关性”和“可控性”。

但真实项目还有一个更底层的问题：

```text
资料再相关，当前用户没权限看，也不能进入检索结果。
```

这就是本节的主题：Metadata Filter。

## 本节学习目标

学完本节，你要能做到：

1. 能解释什么是 metadata filter。
2. 能说明为什么 RAG 检索必须带权限边界。
3. 能区分用户、租户、权限组、业务域、文档类型、来源。
4. 能说明过滤应该尽量发生在检索侧，而不是只在模型前过滤。
5. 能理解 payload filter / scalar filter 的作用。
6. 能看懂 `RagAccessScope`。
7. 能看懂 `build_access_scope_filter()`。
8. 能看懂 `must`、`must_not`、`match.value`、`match.any`。
9. 能理解为什么 metadata 字段必须先写入向量库 payload/scalar 字段。
10. 能说明 Qdrant 和 Milvus 过滤表达方式不同，但业务过滤语义可以统一建模。
11. 能理解为什么 user_id 更多用于审计和调试，tenant_id / permission_group 才常进入检索过滤。
12. 能说明只靠 prompt 告诉模型“不要看无权限资料”是不安全的。

## 本节新增和修改

本节修改：

```text
projects/ai-service/app/rag/filters.py
projects/ai-service/app/rag/retriever.py
projects/ai-service/app/rag/metadata.py
projects/ai-service/app/rag/milvus_store.py
projects/ai-service/tests/test_rag_filters.py
projects/ai-service/tests/test_rag_retriever.py
projects/ai-service/tests/test_rag_metadata.py
projects/ai-service/tests/test_rag_milvus_store.py
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

本节新增：

```text
notes/stage9-11-metadata-filter-access-scope.md
```

本节没有做：

- 不启动 Qdrant。
- 不启动 Milvus。
- 不启动 VMware。
- 不调用真实 embedding。
- 不调用真实大模型。
- 不写手动测试文档。
- 不做 GitHub 上传。

原因是本节先做可测试的过滤建模和过滤转换，不需要外部服务。

## 一句话先讲透

Metadata Filter 的核心是：

```text
不要先把所有相关资料找出来再想办法隐藏，而是在检索时就把范围限制到当前用户允许看的资料里。
```

它解决的不是：

```text
哪个 chunk 更相关。
```

它解决的是：

```text
哪个 chunk 有资格被当前请求检索到。
```

相关性和权限是两件事。

真实 RAG 必须同时满足：

```text
资料相关
资料可访问
资料安全
资料可追溯
```

## 基础知识铺垫

### 1. 什么是 metadata

metadata 是资料内容之外的结构化描述。

例如一个 chunk 的内容是：

```text
退款审核通过后，通常 1 到 3 个工作日原路退回。
```

它的 metadata 可能是：

```json
{
  "source": "refund-return-policy.md",
  "title": "退款退货规则",
  "doc_type": "policy",
  "business_domain": "refund",
  "permission_group": "customer_service",
  "tenant_id": "default",
  "visibility": "tenant",
  "status": "published"
}
```

content 回答的是：

```text
资料说了什么。
```

metadata 回答的是：

```text
资料从哪里来。
资料属于哪个业务域。
资料是什么类型。
资料属于哪个租户。
资料需要什么权限。
资料现在是否发布。
```

RAG 检索不应该只看 content。

还要看 metadata。

### 2. 什么是 metadata filter

metadata filter 是：

```text
根据 metadata 字段限制检索范围。
```

比如：

```text
只查 tenant_id = default 的资料。
只查 permission_group 属于 customer_service 的资料。
只查 business_domain 属于 refund/order 的资料。
排除 status 属于 archived/deleted 的资料。
```

这些条件不是 prompt。

它们应该进入向量数据库或检索器的过滤条件。

例如 Qdrant payload filter 可能长这样：

```json
{
  "must": [
    {"key": "tenant_id", "match": {"value": "default"}},
    {"key": "permission_group", "match": {"any": ["customer_service"]}}
  ],
  "must_not": [
    {"key": "status", "match": {"any": ["archived", "deleted"]}}
  ]
}
```

意思是：

```text
必须属于 default 租户。
权限组必须是 customer_service。
不能是 archived 或 deleted 状态。
```

### 3. 用户、租户、权限组、业务域分别是什么

这几个词是企业应用里非常常见的概念。

#### 用户 user

用户表示当前请求是谁发起的。

比如：

```text
user_id = U1001
```

它常用于：

```text
审计日志。
权限判断。
个性化数据。
用户私有资料过滤。
```

但注意：

```text
不是所有 RAG 文档都应该直接按 user_id 过滤。
```

很多企业知识库资料不是用户私有的，而是租户共享或部门共享的。

所以本节代码里：

```text
user_id 先作为访问主体记录在 RagAccessScope 中。
真正是否过滤 owner_user_id，要显式传 owner_user_id。
```

这避免误把所有知识库都变成“只查自己创建的资料”。

#### 租户 tenant

租户是多租户系统里的隔离单位。

比如：

```text
tenant_id = company_a
tenant_id = company_b
```

同一个 SaaS 系统服务多个公司时，不同公司的数据必须隔离。

RAG 里如果 tenant 过滤做错，会出现严重问题：

```text
A 公司用户检索到 B 公司知识库。
```

这不是回答质量问题，而是数据隔离事故。

#### 权限组 permission_group

权限组表示资料对哪类角色可见。

比如：

```text
customer_service
internal_staff
manager
public
```

客服可以看客服政策。

内部管理者可以看内部补偿规则。

普通用户只能看公开 FAQ。

RAG 如果不带 permission_group，可能会把内部资料喂给模型。

即使模型最后不说出来，也已经把无权限资料放进上下文了。

这在安全上已经不合格。

#### 业务域 business_domain

业务域表示资料属于哪个业务范围。

比如：

```text
refund
order
logistics
account_security
```

业务域过滤不是纯安全问题，也影响检索质量。

用户问退款问题时，只查 refund 域，通常比全库搜索更干净。

#### 文档类型 doc_type

文档类型表示资料类型。

比如：

```text
policy
faq
process
manual
```

用户问规则，优先查 policy。

用户问操作步骤，优先查 process/manual。

doc_type 既可以做过滤，也可以做排序特征。

#### 来源 source

source 是具体资料来源。

比如：

```text
refund-return-policy.md
order-shipping-policy.md
```

source 过滤常用于：

```text
调试。
限定某份文档。
删除或刷新某份文档。
评测某个知识源。
```

### 4. 为什么不能只在模型前过滤

错误做法：

```text
先从全库检索。
拿到很多 chunks。
再在发给模型前过滤掉无权限 chunks。
```

这比完全不做过滤好，但仍然不够。

原因是：

```text
1. 无权限资料已经被检索系统取出来了。
2. 日志、debug、trace 可能已经记录了无权限资料。
3. rerank 或 compression 可能已经处理了无权限资料。
4. 如果过滤漏了，就会直接进入模型上下文。
5. 检索结果排名会被无权限资料影响。
```

更好的做法是：

```text
检索时就带 metadata filter。
```

也就是：

```text
只在允许范围内做向量相似度搜索。
```

这才是更稳定的权限边界。

### 5. 过滤应该发生在哪里

理想顺序是：

```text
构造访问范围
-> 转成向量库 filter
-> 检索时过滤
-> 必要时本地二次过滤
-> 安全检查
-> rerank / compression / generation
```

注意这里的重点：

```text
权限过滤应该尽量靠前。
```

越靠前越安全。

如果等到模型生成前才过滤，就太晚。

### 6. payload filter 和 scalar filter

不同向量数据库叫法不完全一样。

Qdrant 常说：

```text
payload
payload filter
```

Milvus 常说：

```text
scalar fields
scalar filter expression
```

但业务含义类似：

```text
向量负责相似度。
metadata/scalar 字段负责范围过滤。
```

比如：

```text
embedding 向量判断语义是否相近。
tenant_id 判断是不是当前租户。
permission_group 判断当前用户能不能看。
business_domain 判断是不是当前业务范围。
```

一个成熟 RAG 系统必须把这两类条件组合起来。

## 本节主题系统讲解

### 1. 本节新增的核心设计：RagAccessScope

本节在：

```text
projects/ai-service/app/rag/filters.py
```

新增了：

```python
RagAccessScope
```

它表示一次 RAG 查询的访问范围。

核心字段：

```text
user_id
tenant_id
owner_user_id
permission_groups
business_domains
doc_types
sources
visibilities
statuses
excluded_statuses
```

它不是某一个向量数据库的 API 参数。

它是业务层对象。

意思是：

```text
当前这个用户，在当前请求里，允许检索哪些范围的资料。
```

这样做的好处是：

```text
业务访问范围先统一建模。
再转换成 Qdrant / Milvus / 本地检索能理解的 filter。
```

不要在业务代码里到处拼字典。

### 2. 为什么 user_id 不自动变成 owner_user_id filter

本节设计里有：

```text
user_id
owner_user_id
```

它们不是一回事。

`user_id` 是：

```text
当前请求用户是谁。
```

`owner_user_id` 是：

```text
资料属于哪个用户。
```

有些资料是用户私有的。

例如：

```text
用户自己的订单说明。
用户自己的上传文档。
用户自己的客服记录。
```

这种情况下可以按 owner_user_id 过滤。

但企业知识库通常是共享资料。

如果你把 user_id 自动当作 owner_user_id，可能导致：

```text
用户查不到任何公共知识库资料。
```

所以本节明确区分：

```text
user_id 用于审计和 debug。
owner_user_id 只有明确需要用户私有资料时才进入过滤条件。
```

这是很重要的后端设计习惯。

### 3. `must` 和 `must_not`

本节继续使用 Qdrant 风格的 filter 结构：

```text
must
must_not
should
```

本节主要使用：

```text
must
must_not
```

`must` 表示必须满足。

例如：

```json
{"key": "tenant_id", "match": {"value": "default"}}
```

意思是：

```text
tenant_id 必须等于 default。
```

`must_not` 表示必须不满足。

例如：

```json
{"key": "status", "match": {"any": ["archived", "deleted"]}}
```

意思是：

```text
status 不能是 archived 或 deleted。
```

### 4. `match.value` 和 `match.any`

单值匹配用：

```json
{"match": {"value": "customer_service"}}
```

多值匹配用：

```json
{"match": {"any": ["customer_service", "public"]}}
```

业务含义不同。

`value` 是：

```text
必须等于这个值。
```

`any` 是：

```text
属于这些值中的任意一个。
```

比如当前用户有两个权限组：

```text
customer_service
public
```

那资料 permission_group 只要是其中之一，就可以被检索。

这就是 `match.any` 的价值。

### 5. `build_access_scope_filter()`

这个函数负责：

```text
把 RagAccessScope 转成 payload filter。
```

例如：

```python
scope = RagAccessScope(
    user_id="U1001",
    tenant_id="default",
    permission_groups=["customer_service"],
    business_domains=["refund"],
    excluded_statuses=["archived"],
)
```

会转成：

```json
{
  "must": [
    {"key": "tenant_id", "match": {"value": "default"}},
    {"key": "permission_group", "match": {"any": ["customer_service"]}},
    {"key": "business_domain", "match": {"any": ["refund"]}}
  ],
  "must_not": [
    {"key": "status", "match": {"any": ["archived"]}}
  ]
}
```

这个 filter 可以传给 Qdrant。

也可以被 Milvus adapter 转成 scalar expression。

### 6. `build_payload_filter()` 继续兼容旧写法

之前我们已经有：

```python
build_payload_filter(
    permission_group="customer_service",
    business_domain="refund",
)
```

本节没有废掉它。

而是让它支持：

```text
access_scope
tenant_id
owner_user_id
permission_groups
business_domains
doc_types
sources
visibilities
statuses
excluded_statuses
```

这样旧代码还能用。

新代码也能表达更完整访问范围。

### 7. `retrieve_top_k()` 接收 access_scope

本节修改了：

```text
projects/ai-service/app/rag/retriever.py
```

让：

```python
retrieve_top_k(...)
```

可以接收：

```python
access_scope=RagAccessScope(...)
```

这样调用方不用手动拼 payload filter。

调用方只需要表达业务范围：

```python
RagAccessScope(
    user_id="U1001",
    tenant_id="default",
    permission_groups=["customer_service"],
    business_domains=["refund"],
)
```

retriever 会把它转成向量库 filter。

### 8. metadata 字段必须能入库

只会构造 filter 还不够。

如果你的 payload 里没有这些字段：

```text
tenant_id
permission_group
business_domain
status
```

那过滤条件就没有字段可查。

所以本节也修改了：

```text
projects/ai-service/app/rag/metadata.py
```

把这些可选字段加入 payload 白名单：

```text
tenant_id
owner_user_id
visibility
status
```

注意它们是可选字段，不是必填字段。

因为当前学习文档未必每份都有 tenant_id。

但如果真实项目要做多租户隔离，tenant_id 应该成为必填。

### 9. Milvus 也要知道这些字段

Qdrant 的 payload 是 JSON 风格。

Milvus 需要 schema/scalar field。

所以本节也修改了：

```text
projects/ai-service/app/rag/milvus_store.py
```

让 Milvus 适配器知道这些字段：

```text
tenant_id
owner_user_id
visibility
status
```

并把它们加入：

```text
字符串字段
输出字段
过滤字段
标量索引字段
```

这样后续如果真的用 Milvus，这些字段可以参与 scalar filter。

### 10. `metadata_matches_access_scope()`

本节还新增了本地判断函数：

```python
metadata_matches_access_scope(metadata, scope)
```

它的作用是：

```text
在本地检查某份 metadata 是否符合 access scope。
```

这不是主要生产路径。

主要生产路径还是检索时过滤。

但本地函数有用：

```text
单元测试。
debug。
关键词检索。
二次兜底过滤。
坏例分析。
```

## 本节代码讲解

### 1. `RagAccessScope`

这是本节最重要的代码。

它把分散参数变成一个对象。

以前可能到处传：

```text
tenant_id
permission_group
business_domain
doc_type
source
```

以后可以先构造：

```python
RagAccessScope(...)
```

再交给 retriever。

好处是：

```text
访问边界集中。
字段可校验。
debug 更清楚。
后续扩展更容易。
```

### 2. `build_match_any_condition()`

这个函数处理多值匹配。

比如：

```python
build_match_any_condition(
    "permission_group",
    ["customer_service", "public"],
)
```

得到：

```json
{
  "key": "permission_group",
  "match": {
    "any": ["customer_service", "public"]
  }
}
```

它会去掉重复值，并拒绝空字符串。

### 3. `combine_payload_filters()`

这个函数用来合并多个 filter。

比如：

```text
访问范围 filter
业务临时 filter
调试 source filter
```

合并时要保留：

```text
must
should
must_not
```

这样后续 filter 不会互相覆盖。

### 4. `MetadataFilterReport`

这个报告不是给模型看的。

它是给开发者看的。

它记录：

```text
user_id
tenant_id
applied_fields
payload_filter
debug_lines
```

当用户说“为什么查不到资料”时，这个 report 很有用。

你可以先看：

```text
是不是 tenant_id 限制错了。
是不是 permission_group 太窄了。
是不是 business_domain 不对。
是不是 status 被排除了。
```

### 5. 修改 `retrieve_top_k()`

本节给 `retrieve_top_k()` 增加：

```python
access_scope: RagAccessScope | None = None
```

这样检索调用可以更接近真实项目：

```python
retrieve_top_k(
    query,
    embedding_model=embedding_model,
    vector_store=vector_store,
    access_scope=RagAccessScope(
        user_id="U1001",
        tenant_id="default",
        permission_groups=["customer_service"],
    ),
)
```

这比调用方自己拼 filter 更安全。

## 本节测试讲解

本节测试重点覆盖：

```text
RagAccessScope 字段规范化。
match.any 多值过滤。
访问范围转 payload filter。
access_scope 和旧单字段 filter 合并。
metadata 是否匹配 access scope。
retriever 是否把 scope filter 传给 vector store。
metadata payload 是否保留 tenant_id/owner_user_id/visibility/status。
Milvus filter 是否支持新增字段。
```

这说明本节不是只写概念。

而是把“权限边界”落实到了：

```text
过滤对象。
payload filter。
retriever 调用。
metadata 入库字段。
Milvus scalar 字段。
自动化测试。
```

## 本节练习

### 练习 1：解释概念

问题：

```text
什么是 metadata filter？
```

参考答案：

```text
metadata filter 是根据资料的结构化元数据限制检索范围。
例如按 tenant_id、permission_group、business_domain、doc_type、source、status 过滤。
它的作用是让检索只在当前请求允许的资料范围内进行。
```

### 练习 2：判断对错

问题：

```text
只要 prompt 告诉模型“不要回答无权限内容”，就不需要检索侧权限过滤。对吗？
```

参考答案：

```text
不对。
无权限资料不应该进入检索结果和模型上下文。
只靠 prompt 是不安全的，因为模型可能忽略指令，日志和中间链路也可能已经接触到无权限资料。
权限过滤应该尽量发生在检索侧。
```

### 练习 3：区分 user_id 和 owner_user_id

问题：

```text
user_id 和 owner_user_id 有什么区别？
```

参考答案：

```text
user_id 表示当前请求用户是谁，常用于审计、日志、权限判断。
owner_user_id 表示资料属于哪个用户，只有用户私有资料场景才适合作为检索过滤条件。
不能把 user_id 自动当成 owner_user_id，否则可能导致用户查不到共享知识库资料。
```

### 练习 4：解释 match.any

问题：

```text
permission_group 使用 match.any 有什么意义？
```

参考答案：

```text
当前用户可能拥有多个权限组，例如 customer_service 和 public。
match.any 表示资料 permission_group 只要属于这些允许值之一，就可以被检索。
这比只能匹配单个权限组更符合真实权限系统。
```

### 练习 5：排查问题

问题：

```text
用户反馈“明明有退款文档，但 RAG 查不到”，你会先检查哪些 metadata filter？
```

参考答案：

```text
先看 tenant_id 是否正确。
再看 permission_group 是否包含用户权限。
再看 business_domain 是否限制到了 refund。
再看 doc_type/source 是否过窄。
最后看 status 是否被 excluded_statuses 排除了。
同时查看 MetadataFilterReport 的 applied_fields 和 payload_filter。
```

## 自测题

### 自测 1

问题：

```text
Metadata Filter 解决的是相关性问题还是访问范围问题？
```

答案：

```text
主要解决访问范围问题。
它决定哪些资料有资格参与检索。
相关性由向量相似度、关键词检索、hybrid、rerank 等环节处理。
```

### 自测 2

问题：

```text
为什么 tenant_id 过滤在多租户 RAG 里非常重要？
```

答案：

```text
因为不同租户的数据必须隔离。
如果 tenant_id 过滤缺失或错误，一个租户的用户可能检索到另一个租户的资料，这是严重的数据隔离问题。
```

### 自测 3

问题：

```text
为什么 metadata 字段必须先进入 payload/scalar 字段？
```

答案：

```text
因为向量库只能根据已存储的 payload/scalar 字段过滤。
如果 tenant_id、permission_group、status 没有入库，就无法在检索时按这些字段过滤。
```

### 自测 4

问题：

```text
本节为什么新增 MetadataFilterReport？
```

答案：

```text
因为过滤问题很容易导致“查不到资料”。
报告可以显示当前 user_id、tenant_id、应用了哪些字段、最终 payload_filter 是什么，方便调试权限范围和检索范围。
```

### 自测 5

问题：

```text
权限过滤、RAG Security、Citation Verification 的位置有什么区别？
```

答案：

```text
权限过滤发生在检索侧，决定哪些资料能被检索。
RAG Security 发生在资料进入模型上下文前，检查提示注入和敏感数据等风险。
Citation Verification 发生在回答生成后，检查回答引用是否能追溯到原文。
它们分别保护不同环节，不能互相替代。
```

## 本节小结

本节完成了 RAG 权限过滤的基础工程建模。

你现在应该理解：

```text
相关不代表可访问。
权限过滤应该尽量在检索侧发生。
metadata filter 是 RAG 安全边界的一部分。
RagAccessScope 用来表达当前请求的访问范围。
payload/scalar filter 是把业务访问范围交给向量库执行。
user_id 和 owner_user_id 不能混用。
tenant_id、permission_group、business_domain、status 都是常见过滤字段。
```

阶段 9 到这里已经具备更完整的 RAG 质量和安全链路：

```text
改写问题
-> 多路召回
-> 意图识别
-> 混合检索
-> 分数解释
-> rerank
-> 引用校验
-> 上下文压缩
-> metadata 权限过滤
```

下一节适合学习：

```text
阶段 9 第 12 节：RAG Prompt Injection 防护。
```
