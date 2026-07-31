# 阶段 9 第 20 节：RAG 数据更新：增量入库、删除、重新索引

## 本节定位

本节学习 RAG 数据更新。

它接在第 19 节可观测性后面：上一节学会记录一次 RAG 请求发生了什么，本节学习知识库文档变化后，向量库里的数据应该怎么同步更新。

## 本节学习目标

学完本节，你要能说清楚：

- 为什么 RAG 知识库不能只追加写入。
- 什么是增量入库、删除、刷新和重新索引。
- `source`、`doc_id`、`chunk_id` 分别解决什么问题。
- 为什么修改文档时要先删旧 chunks，再写新 chunks。
- 什么时候用增量更新，什么时候需要 full reindex。
- 数据更新为什么会影响缓存、引用、评测和可观测性。

## 本节新增和修改

新增：

```text
projects/ai-service/app/rag/data_update.py
projects/ai-service/tests/test_rag_data_update.py
notes/stage9-20-rag-data-update-incremental-delete-reindex.md
```

修改：

```text
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

## 一句话先讲透

RAG 数据更新的本质是：

```text
当知识库文档发生新增、修改、删除或索引规则变化时，让向量库里的 chunks、metadata、缓存、引用和评测基线同步跟着变化，避免旧知识、重复数据和脏数据继续影响回答。
```

## 基础知识铺垫

### 1. 为什么 RAG 数据会变

企业知识库不是写完就永远不变。

常见变化包括：

```text
退款政策调整。
物流时效更新。
账号安全规则变化。
新增售后流程。
删除过期公告。
内部 SOP 改版。
权限范围调整。
文档分类改变。
```

RAG 系统回答依赖知识库。

所以知识库一变，RAG 的召回、引用、回答、评测结果都可能跟着变。

如果只在第一次建库时入库，以后不处理更新，系统就会逐渐变成：

```text
能跑，但知识越来越旧。
```

### 2. 为什么不能只“追加入库”

初学者很容易这样想：

```text
文档变了，那我再把新文档入库一次就行。
```

这叫只追加。

只追加会带来严重问题。

第一，旧 chunk 还在。

例如旧政策：

```text
退款 7 个工作日到账。
```

新政策：

```text
退款 3 到 5 个工作日到账。
```

如果只追加，新旧两份资料都会留在向量库里。

用户问“退款多久到账”，可能同时召回：

```text
旧 chunk：7 个工作日。
新 chunk：3 到 5 个工作日。
```

模型看到冲突资料，就可能答错。

第二，重复 chunk 会干扰排序。

同一篇文档反复入库，向量库里可能出现多份相似 chunk。

这会导致：

```text
检索结果被重复内容占满。
其他有用资料被挤出 top_k。
rerank 看起来排序正常，但候选本身已经被污染。
```

第三，删除文档不会生效。

如果某篇文档已经下线，但向量库里没有删除对应 points，RAG 还可能继续引用它。

这在企业知识库里很危险。

### 3. 什么是增量入库

增量入库是指只处理变化的数据。

例如：

```text
新增了 A.md。
修改了 B.md。
删除了 C.md。
D.md 没变。
```

增量更新应该做：

```text
A.md：入库新文档。
B.md：删除旧 chunks，再入库新 chunks。
C.md：删除对应 chunks。
D.md：跳过。
```

它的目标是：

```text
减少不必要的 embedding 成本。
减少向量库写入压力。
避免重复数据。
让知识库更新更快。
```

### 4. 什么是刷新 source

刷新 source 指的是：

```text
按某篇文档的 source 删除旧 chunks。
再把这篇文档重新切分、embedding、upsert。
```

修改文档时，通常不建议直接覆盖某几个 chunk。

原因是：

```text
文档内容改了，chunk 切分边界可能变。
原来 3 个 chunks，后来可能变成 4 个 chunks。
原来的第 2 段内容可能移动到第 3 个 chunk。
chunk_id 可能复用，但含义已经变了。
```

所以更稳的做法是：

```text
以 source 为单位删除旧 chunks。
再以当前文档内容生成新 chunks。
```

本项目已有的 `refresh_directory_in_vector_store()` 就体现了这个思想：

```text
先按 source delete。
再 upsert 新 chunks。
```

### 5. 什么是删除文档

删除文档不是删除本地文件这么简单。

RAG 里还要删除向量库中的对应 points。

如果不删，已经入库的 chunks 会继续被召回。

删除通常按 metadata filter 做：

```text
source = "refund-return-policy.md"
```

然后删除：

```text
所有 payload.source 等于这个 source 的 points。
```

本项目已有：

```text
delete_document_from_vector_store(source)
```

它就是按 source 删除向量库 points。

### 6. 什么是重新索引

重新索引是比增量更新更重的操作。

它通常表示：

```text
清空或重建整个 collection。
重新加载所有文档。
重新切分。
重新 embedding。
重新写入向量库。
重新建立索引。
```

什么时候需要重新索引？

常见情况：

```text
chunk_size 改了。
chunk_overlap 改了。
splitter 规则改了。
embedding 模型换了。
embedding 维度变了。
向量距离 metric 改了。
metadata schema 改了。
权限字段设计改了。
collection/index 参数改了。
历史数据污染严重。
```

这些变化会影响所有文档，不适合只更新单篇 source。

### 7. `source` 是什么

在本项目里，`source` 表示文档来源。

例如：

```text
refund-return-policy.md
account-security-faq.md
order-shipping-policy.md
```

它的作用是把 chunks 重新归属到原始文档。

同一篇文档切出来的所有 chunks，都应该带同一个 `source`。

这样你才能：

```text
按 source 删除旧 chunks。
按 source 统计召回来源。
按 source 做引用展示。
按 source 排查 bad case。
```

### 8. `doc_id` 是什么

`doc_id` 通常是文档的稳定业务 ID。

例如：

```text
policy_refund_001
faq_account_security_002
sop_ticket_after_sale_003
```

`source` 可能是文件路径，`doc_id` 更像数据库主键。

真实项目中最好同时有：

```text
doc_id：稳定文档 ID。
source：来源路径或来源标识。
version：文档版本。
updated_at：更新时间。
status：active/deleted/archived。
```

当前项目主要用 `source` 学习更新流程。

后续做真实生产系统时，建议补 `doc_id` 和 `version`。

### 9. `chunk_id` 是什么

`chunk_id` 是 chunk 的稳定标识。

本项目的 chunk_id 规则大致是：

```text
source 基础名 + chunk 序号
```

例如：

```text
refund_return_policy_chunk_0001
refund_return_policy_chunk_0002
```

它的作用是：

```text
向量库 point id 生成。
引用来源定位。
检索结果去重。
可观测性记录。
评测 expected evidence 对齐。
```

但要注意：

```text
chunk_id 稳定不代表 chunk 内容永远不变。
```

如果文档内容修改、切分规则修改，同一个 chunk_id 可能对应新的内容。

所以数据更新时还要考虑：

```text
content_hash。
metadata_hash。
collection_version。
```

### 10. 什么是 document manifest

manifest 可以理解为文档清单。

它记录当前知识库里有哪些文档，以及每篇文档的关键摘要。

本节新增的 manifest 记录：

```text
source。
content_hash。
metadata_hash。
content_chars。
metadata_summary。
manifest_hash。
```

它不存完整文档内容。

它的作用是：

```text
判断哪些文档新增了。
判断哪些文档修改了。
判断哪些文档删除了。
判断哪些文档没变。
为更新计划提供证据。
```

### 11. 为什么要有 content_hash

`content_hash` 是文档内容的 hash。

如果同一个 source 的 content_hash 变了，说明文档正文变了。

正文变了，通常意味着：

```text
需要重新切分。
需要重新 embedding。
需要删除旧 chunks。
需要写入新 chunks。
```

这对应本节的：

```text
refresh_source
```

### 12. 为什么要有 metadata_hash

metadata 也会影响 RAG。

例如：

```text
permission_group 从 customer_service 改成 internal_staff。
business_domain 从 refund 改成 order。
doc_type 从 faq 改成 policy。
visibility 从 public 改成 internal。
```

即使正文没变，只要 metadata 变了，检索和权限过滤结果就可能变。

所以 metadata 变化也应该触发更新。

否则可能出现：

```text
文档内容正确，但权限或业务域过滤错误。
```

### 13. 数据更新和缓存的关系

数据更新会影响缓存。

第 18 节学过检索缓存。

如果文档变了，但缓存还保留旧检索结果，就可能继续返回旧 chunks。

所以数据更新计划应该提示：

```text
哪些 source 变化了。
哪些缓存应该失效。
是否需要清理相关检索缓存。
```

真实项目里，缓存失效可能按：

```text
collection version。
source。
tenant。
permission scope。
cache namespace。
```

当前项目先在 plan 里记录 `cache_invalidation_sources`。

### 14. 数据更新和引用的关系

引用依赖 chunk。

如果某个 chunk 删除或内容变化，旧引用就可能失效。

例如旧回答引用：

```text
chunk_id = refund_return_policy_chunk_0003
```

文档更新后：

```text
chunk_0003 内容变了。
或者这个 chunk 不存在了。
```

那历史回答的引用就不能简单当成当前知识事实。

真实系统要区分：

```text
当前知识库引用。
历史回答引用。
回答生成时的知识库版本。
```

这也是为什么生产 RAG 常需要 collection version 或 knowledge_base_version。

### 15. 数据更新和评测的关系

知识库更新后，评测结果也可能变化。

例如：

```text
新增了退款资料，原来 no_context 的问题现在应该能回答。
删除了旧政策，原来期望证据可能不存在。
修改了物流时效，答案要点也要改。
```

所以数据更新计划里要提示：

```text
should_rerun_evaluation = true
```

这不是说每次都必须跑全部评测。

而是提醒：

```text
知识库变化后，至少要重新评估受影响业务域或 source。
```

### 16. 数据更新和可观测性的关系

第 19 节学过可观测性。

数据更新后，可观测性可以帮助你排查：

```text
更新后 no_context 是否下降。
更新后 citation invalid 是否上升。
更新后某个 source 是否被频繁召回。
更新后 top_score 是否变化。
更新后某个业务域是否变慢。
```

如果没有记录 query、source、chunk_id、score、citation 和 timing，就很难判断更新是否真的改善了效果。

## 本节主题系统讲解

### 1. 第 20 节在阶段 9 里的位置

阶段 9 前面已经学习：

```text
检索质量怎么提升。
排序质量怎么解释。
引用怎么校验。
安全怎么防护。
评测怎么设计。
bad case 怎么分析。
参数怎么调。
性能怎么保护。
可观测性怎么记录。
```

但如果知识库数据本身不能正确更新，前面的能力都会被脏数据拖累。

例如：

```text
旧政策没删，rerank 再强也可能看到冲突资料。
重复 chunk 太多，top_k 再大也可能被重复内容占满。
metadata 过期，权限过滤再完善也会用错字段。
评测集不更新，指标再漂亮也可能不符合最新业务。
```

所以本节补的是 RAG 数据生命周期。

### 2. 当前项目已有的更新能力

项目里已有三个基础函数：

```text
ingest_directory_to_vector_store()
refresh_directory_in_vector_store()
delete_document_from_vector_store()
```

它们分别代表：

```text
全量或初次入库。
按目录刷新，先删 source 再 upsert。
按 source 删除文档。
```

本节没有重写这些执行逻辑。

本节新增的是：

```text
文档变化识别。
更新动作规划。
缓存和评测影响提示。
```

也就是先回答：

```text
应该做什么？
为什么做？
会影响哪些 source？
是否需要清缓存？
是否需要重新评测？
```

再由已有 ingestion 代码去执行。

### 3. 本节新增的核心链路

本节新增链路是：

```text
旧文档列表
-> build_document_manifest()
-> previous manifest

新文档列表
-> build_document_manifest()
-> current manifest

previous + current
-> detect_document_changes()
-> new / modified / deleted / unchanged

changes
-> build_rag_data_update_plan()
-> ingest_new / refresh_source / delete_source / skip / reindex_collection
```

它把“文档变了”变成结构化工程动作。

### 4. new source 怎么处理

如果 source 只存在于 current manifest：

```text
change_type = new
action = ingest_new
```

意思是：

```text
这是一篇新文档，需要切分、embedding、upsert。
```

同时要提醒：

```text
should_invalidate_cache = true
should_rerun_evaluation = true
```

因为新增文档可能让原来无法回答的问题变得可以回答。

### 5. modified source 怎么处理

如果 source 同时存在于 previous 和 current，但 content_hash 或 metadata_hash 变了：

```text
change_type = modified
action = refresh_source
```

意思是：

```text
先删除这个 source 的旧 chunks。
再写入这个 source 的新 chunks。
```

为什么不是直接 upsert？

因为修改后 chunk 数量和 chunk 边界可能变化。

只 upsert 新 chunks，不能保证旧 chunks 全部消失。

### 6. deleted source 怎么处理

如果 source 只存在于 previous manifest：

```text
change_type = deleted
action = delete_source
```

意思是：

```text
这篇文档已经不存在，需要删除向量库中对应 source 的 points。
```

删除也要清缓存和重新评测。

原因是：

```text
旧缓存可能继续引用被删除文档。
评测期望证据可能已经不存在。
```

### 7. unchanged source 怎么处理

如果 source 的 content_hash 和 metadata_hash 都没变：

```text
change_type = unchanged
action = skip
```

意思是：

```text
不用重新 embedding，不用重新写入。
```

这正是增量更新节省成本的地方。

### 8. full reindex 怎么处理

如果是全量重建：

```text
action = reindex_collection
```

它不是针对单个 source。

它表示：

```text
整个 collection 需要重建。
```

本节代码用 `force_reindex=True` 显式触发。

适合场景：

```text
embedding 模型换了。
chunk_size 改了。
metadata schema 改了。
距离度量改了。
索引参数改了。
历史数据污染严重。
```

### 9. 为什么 plan 里要记录 affected_sources

`affected_sources` 表示受影响的 source。

它有几个用途：

```text
给开发者确认更新范围。
给缓存失效使用。
给评测选择受影响 case 使用。
给日志和审计记录使用。
```

如果 affected_sources 异常大，说明本次更新影响范围很广。

这时上线要更谨慎。

### 10. 为什么 plan 里要记录 should_rerun_evaluation

RAG 数据变化后，评测基线可能变化。

所以 plan 里明确记录：

```text
should_rerun_evaluation
```

它提醒你：

```text
更新后不要只看入库成功，还要看回答质量有没有变。
```

尤其是：

```text
核心政策文档修改。
权限字段变化。
删除高频 FAQ。
重新索引整个 collection。
```

这些都应该至少跑一部分回归评测。

### 11. 本节暂时不做什么

本节不真实连接 Qdrant。

原因：

```text
本节重点是学习更新策略，真实 Qdrant 已经在前面阶段跑通过。
```

本节不删除真实 collection。

原因：

```text
删除真实向量库属于高风险操作，学习阶段先用 plan 表达动作。
```

本节不做后台任务调度。

原因：

```text
定时同步、队列、失败重试、断点续传是后续生产化内容。
```

本节不做完整 doc_id/version 系统。

原因：

```text
当前项目先用 source 学会主线，真实项目再补 doc_id、version、updated_at。
```

## 本节代码讲解

### 1. `RagDocumentManifest`

`RagDocumentManifest` 是文档清单。

它包含：

```text
document_count。
manifest_hash。
sources。
entries。
```

每个 entry 记录：

```text
source。
content_hash。
metadata_hash。
content_chars。
metadata_summary。
```

它的作用是给“新旧文档对比”提供稳定依据。

### 2. `build_document_manifest()`

这个函数把一组 `RagDocument` 转成 manifest。

它会：

```text
读取 document.metadata["source"]。
计算 content_hash。
计算 metadata_hash。
拒绝重复 source。
生成整个 manifest_hash。
```

重复 source 必须拒绝。

因为如果两个文档 source 一样，后续按 source 删除或刷新时会产生歧义。

### 3. `detect_document_changes()`

这个函数比较旧 manifest 和新 manifest。

它输出：

```text
new。
modified。
deleted。
unchanged。
```

判断规则：

```text
只在 current 有：new。
只在 previous 有：deleted。
两边都有但 hash 不同：modified。
两边都有且 hash 相同：unchanged。
```

### 4. `build_rag_data_update_plan()`

这个函数把变化转换成动作。

映射关系：

```text
new -> ingest_new
modified -> refresh_source
deleted -> delete_source
unchanged -> skip
force_reindex -> reindex_collection
```

它还会生成：

```text
affected_sources。
cache_invalidation_sources。
action_counts。
should_rerun_evaluation。
```

这让更新不再只是“执行脚本”，而是有计划、有原因、有影响范围。

### 5. `format_rag_data_update_plan()`

这个函数把 plan 转成可读文本。

适合用于：

```text
本地 smoke 输出。
学习调试。
更新前人工确认。
日志摘要。
```

真实项目里可以把 `RagDataUpdatePlan` 直接输出成 JSON，交给后台任务或管理页面展示。

### 6. 本节测试重点

本节测试覆盖：

```text
内容变化和 metadata 变化会改变 manifest_hash。
new/modified/deleted/unchanged 能正确识别。
变化能映射到 ingest_new/refresh_source/delete_source。
unchanged 可以映射为 skip。
force_reindex 会生成 reindex_collection。
重复 source 和空 source 会被拒绝。
```

这些测试不需要真实向量库。

因为它们验证的是“更新规划规则”，不是 Qdrant 的 HTTP 行为。

## 常见误区

### 误区 1：文档更新后再入库一次就行

不行。

只追加会留下旧 chunks，导致新旧知识冲突、重复召回、引用旧资料。

修改文档更稳的方式是按 source 先删旧 chunks，再写新 chunks。

### 误区 2：只看正文变化，不看 metadata 变化

不行。

metadata 会影响权限过滤、业务域过滤、引用展示和评测分组。

正文没变但权限字段变了，也必须更新。

### 误区 3：删除本地文件就等于删除知识库

不是。

向量库里已经写入的 points 不会因为本地文件消失自动删除。

必须执行 delete_source 或 reindex。

### 误区 4：chunk_id 不变就说明不用更新

不一定。

同一个 chunk_id 可能因为文档内容或切分规则变化而对应新内容。

要看 content_hash、metadata_hash 和 collection version。

### 误区 5：每次更新都 full reindex

没必要。

小范围文档变化应该用增量更新，节省 embedding 成本和写入时间。

只有全局规则变化或数据污染严重时，才考虑 full reindex。

### 误区 6：数据更新和评测无关

有关。

知识库变了，RAG 的期望答案、期望证据、召回结果和 no_context 行为都可能变化。

更新后至少要跑受影响范围的评测。

## 本节练习

### 练习 1：为什么修改文档时要先删除旧 chunks？

答案：

因为文档修改后，chunk 数量、chunk 边界和内容都可能变化。如果只 upsert 新 chunks，旧 chunks 可能继续留在向量库里，造成新旧知识冲突和重复召回。按 source 先删再写，可以保证这个 source 对应的是当前文档版本。

### 练习 2：什么情况下应该 full reindex？

答案：

当变化影响整个 collection 时应该 full reindex。例如换 embedding 模型、embedding 维度变化、chunk_size/chunk_overlap 或 splitter 规则变化、metadata schema 改动、距离度量或索引参数变化、历史数据严重污染。

### 练习 3：为什么 metadata 变化也要触发更新？

答案：

因为 metadata 会影响权限过滤、业务域过滤、doc_type 过滤、引用展示、评测分组和可观测性统计。正文没变但 metadata 变了，检索结果和用户可见范围也可能改变。

### 练习 4：`source` 和 `chunk_id` 的区别是什么？

答案：

`source` 表示原始文档来源，一篇文档的多个 chunks 通常有同一个 source。`chunk_id` 表示某个具体 chunk 的标识，用于向量库 point、引用、去重和排查。删除或刷新通常按 source 做，引用和检索结果通常定位到 chunk_id。

### 练习 5：为什么新增文档也可能需要清缓存？

答案：

因为新增文档可能改变原来请求的检索结果。比如之前某个问题没有资料而返回 no_context，新增文档后应该能回答。如果旧缓存还在，系统可能继续返回旧的无上下文结果。

## 自测题

### 自测 1：增量更新一般要识别哪四类文档变化？

答案：

new、modified、deleted、unchanged。

分别对应新增文档、修改文档、删除文档和未变化文档。

### 自测 2：本节把四类变化映射成哪些动作？

答案：

new 映射为 `ingest_new`。

modified 映射为 `refresh_source`。

deleted 映射为 `delete_source`。

unchanged 映射为 `skip`。

如果强制重建，则使用 `reindex_collection`。

### 自测 3：`content_hash` 和 `metadata_hash` 分别解决什么问题？

答案：

`content_hash` 用来判断文档正文是否变化。`metadata_hash` 用来判断权限、业务域、文档类型、状态等 metadata 是否变化。两者任意一个变化，都可能影响 RAG 检索和回答。

### 自测 4：数据更新后为什么要考虑重新评测？

答案：

因为知识库内容变化后，期望答案、期望证据、召回结果、no_context 行为和引用有效性都可能变化。不重新评测，就不知道更新是否改善了效果，或者是否引入了新问题。

### 自测 5：为什么当前项目先做 data update plan，而不是直接删除真实 collection？

答案：

因为本节重点是学习更新策略和影响范围。真实删除 collection 是高风险操作，应该在明确计划、确认影响、具备备份和回滚策略后执行。学习阶段先用 plan 表达动作更安全。

## 本节小结

本节你学到的是 RAG 数据更新的主线：

```text
新增文档：ingest_new。
修改文档：refresh_source，先删旧 chunks 再写新 chunks。
删除文档：delete_source，按 source 删除向量库 points。
规则全局变化：reindex_collection。
未变化文档：skip。
```

还要记住：

```text
数据更新会影响缓存、引用、评测和可观测性。
source 是文档级定位。
chunk_id 是 chunk 级定位。
content_hash 和 metadata_hash 是判断变化的重要证据。
```

下一节学习 RAG 多知识库路由，解决“用户问题应该查哪个知识库，而不是所有资料混在一起检索”的问题。
