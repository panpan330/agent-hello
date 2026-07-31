# 阶段 9 第 23 节：RAG 生产化验收清单：质量、安全、性能、成本、可观测性

## 本节定位

本节学习 RAG 生产化验收清单。

它接在第 22 节 RAG 与 Agent 边界后面：前面已经学了质量、安全、性能、评测、可观测、数据更新和边界设计，本节把这些能力整理成真实项目上线前可用的检查标准。

## 本节学习目标

学完本节，你要能说清楚：

- RAG 上线前为什么不能只看“接口能跑”。
- 质量、安全、性能、成本、可观测性、数据、Agent 边界分别要验收什么。
- 哪些检查是 release blocker。
- `passed / warning / failed / not_checked` 怎么理解。
- `ready / conditional / blocked` 怎么判断。
- 如何把阶段 9 的各节能力串成一份上线 checklist。

## 本节新增和修改

新增：

```text
projects/ai-service/app/rag/production_readiness.py
projects/ai-service/tests/test_rag_production_readiness.py
notes/stage9-23-rag-production-readiness-checklist.md
```

修改：

```text
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

## 一句话先讲透

RAG 生产化验收的本质是：

```text
上线前用证据证明这个 RAG 功能在质量、安全、性能、成本、可观测、数据更新和系统边界上都可控；没有证据的能力不能当作已经具备。
```

## 基础知识铺垫

### 1. 什么叫生产化

生产化不是“本地能跑”。

生产化表示一个功能可以进入真实使用环境，面对真实用户、真实数据、真实流量和真实故障。

对 RAG 来说，生产化至少要考虑：

```text
用户问题是否能稳定召回正确资料。
回答是否有依据。
引用是否真实。
权限是否正确。
知识库是否能更新。
依赖慢了怎么办。
模型失败怎么办。
成本会不会失控。
出问题后能不能排查。
和 Agent、Tool 的边界是否清楚。
```

如果只看接口能返回 200，那只是“跑通”，不是生产化。

### 2. 为什么 RAG 上线风险比普通接口更复杂

普通接口通常有明确输入输出。

例如：

```text
GET /orders/A1001
```

要么订单存在，要么不存在，要么无权限。

RAG 更复杂，因为它包含多个不确定环节：

```text
用户问题表达不稳定。
query rewrite 可能改错。
embedding 可能不合适。
向量库可能漏召回。
metadata filter 可能过滤错。
rerank 可能排序错。
context compression 可能删掉关键信息。
模型生成可能没用好上下文。
引用可能不一致。
知识库可能过期。
```

所以 RAG 生产化不能靠单点测试。

它需要一组维度共同验收。

### 3. 什么是验收清单

验收清单是上线前用来检查风险的列表。

它不是形式主义。

它的作用是让团队明确：

```text
哪些事情已经有证据。
哪些事情只是感觉可以。
哪些事情还没测。
哪些问题必须修完才能上线。
哪些问题可以带着风险灰度上线。
```

对 RAG 来说，清单最好是结构化的。

例如：

```text
check_id。
category。
requirement。
evidence_examples。
risk_if_missing。
release_blocker。
status。
```

这样才能被测试、记录和复用。

### 4. 什么是 release blocker

release blocker 是发布阻断项。

意思是：

```text
这个检查如果 failed 或 not_checked，就不应该上线。
```

例如：

```text
权限过滤没有验证。
Prompt Injection 没有防护。
引用没有校验。
写工具不需要确认。
数据更新没有删除旧 chunks 的策略。
核心阶段没有超时和降级。
```

这些不是小问题。

如果没做好，可能导致：

```text
越权泄露。
错误业务回答。
无依据编造。
系统拖垮。
错误写入业务系统。
旧知识继续影响用户。
```

所以它们应该阻断上线。

### 5. `passed / warning / failed / not_checked`

本节用四种状态表达每个检查项：

```text
passed：已通过，有证据。
warning：有风险，但可能可接受。
failed：检查失败，需要处理。
not_checked：没有检查或没有证据。
```

这四个状态的关键不是“写哪个词”，而是工程含义。

`passed` 必须有证据。

例如：

```text
测试通过。
评测报告达标。
日志字段已验证。
安全用例已覆盖。
```

`warning` 表示：

```text
不是完全达标，但团队知道风险，并准备接受或灰度观察。
```

`failed` 表示：

```text
已经发现问题。
```

`not_checked` 表示：

```text
不知道有没有问题。
```

在生产化里，`not_checked` 很危险。

因为没证据不能当通过。

### 6. `ready / conditional / blocked`

整体验收报告也需要状态。

本节用：

```text
ready。
conditional。
blocked。
```

`ready` 表示：

```text
所有检查都 passed。
```

`conditional` 表示：

```text
没有阻断项失败或缺失，但还有 warning、非阻断 failed 或 not_checked。
```

它适合：

```text
灰度上线。
低流量上线。
内部试用。
带监控放量。
```

`blocked` 表示：

```text
存在 release blocker failed 或 not_checked。
```

这种情况不应该上线。

### 7. 质量验收要看什么

质量不是“模型回答看起来不错”。

RAG 质量至少要看：

```text
检索指标。
回答质量。
引用有效性。
no_context 行为。
bad case 归因。
参数调优建议。
```

检索指标包括：

```text
Hit@K。
Recall@K。
Precision@K。
MRR@K。
```

回答质量包括：

```text
answer point coverage。
citation pass rate。
refusal pass rate。
forbidden source 检查。
```

引用有效性包括：

```text
citation 是否指向 retrieved chunks。
source_index 是否正确。
chunk_id 是否真实。
source metadata 是否一致。
答案和引用是否有基本支撑。
```

质量验收要解决的问题是：

```text
它能不能答对？
答对时有没有证据？
答不了时会不会胡编？
答错时能不能定位原因？
```

### 8. 安全验收要看什么

RAG 安全不是只靠系统提示词。

安全验收至少包括：

```text
权限过滤。
Prompt Injection 防护。
敏感信息日志保护。
Tool 边界。
禁用敏感工具。
写操作确认。
```

权限过滤要确认：

```text
tenant_id。
permission_group。
business_domain。
doc_type。
visibility。
status。
excluded_statuses。
```

Prompt Injection 要确认：

```text
文档正文扫描。
metadata 扫描。
高风险阻断。
中风险 warning。
blocked reason codes。
```

日志安全要确认：

```text
query preview 脱敏。
不记录 chunk 原文。
不泄露 API Key。
不泄露内部敏感字段。
```

Tool 边界要确认：

```text
read tool 和 write tool 分开。
write tool 需要用户确认。
sensitive tool 禁用或强权限。
模型请求不等于后端授权。
```

### 9. 性能验收要看什么

RAG 链路长，性能验收不能只看总耗时。

要看：

```text
embedding 耗时。
vector store 耗时。
rerank 耗时。
generation 耗时。
security check 耗时。
总耗时。
near_timeout。
timed_out。
```

还要看：

```text
有没有超时。
有没有降级策略。
有没有缓存。
缓存 key 是否安全。
慢请求能不能排查。
依赖失败会不会拖垮服务。
```

性能验收要解决的问题是：

```text
它是不是稳定？
慢在哪里？
失败时能不能可控返回？
```

### 10. 成本验收要看什么

RAG 成本主要来自：

```text
embedding。
向量数据库。
rerank。
LLM prompt tokens。
LLM completion tokens。
重试。
fallback。
日志和监控。
```

成本验收要看：

```text
top_k 是否受控。
rerank candidates 是否受控。
context budget 是否受控。
是否做 context compression。
是否有 cache hit rate。
provider fallback 是否频繁。
重试是否放大成本。
```

成本不是等账单来了再看。

上线前就应该知道：

```text
一次请求大概消耗多少。
最坏情况消耗多少。
高频问题能不能缓存。
模型失败时会不会反复重试。
```

### 11. 可观测性验收要看什么

没有可观测性，就没有生产排查能力。

可观测性至少要记录：

```text
trace_id。
query_hash。
query_preview。
knowledge_base_id。
retrieved chunks snapshot。
rerank summary。
citation summary。
timings。
warning codes。
degradation mode。
```

它要能回答：

```text
这次查了哪个知识库？
召回了什么 chunk？
rerank 是否 fallback？
引用是否有效？
哪一步慢？
有没有 no_context？
有没有安全阻断？
```

注意：

```text
可观测性不是记录越多越好。
```

它必须和安全配合。

能用 id、hash、summary 解决的问题，就不要把原文打到日志里。

### 12. 数据验收要看什么

RAG 的底层是知识库。

数据验收至少包括：

```text
metadata 是否完整。
source 是否唯一。
chunk_id 是否稳定。
chunk_count 是否正确。
文档新增怎么入库。
文档修改怎么 refresh。
文档删除怎么 delete。
什么时候 full reindex。
缓存如何失效。
更新后是否重新评测。
```

数据问题非常容易被误判成模型问题。

例如：

```text
旧政策没删，模型答错。
metadata 权限错，用户看到内部资料。
chunk 切分太差，召回不到关键句。
source 重复，删除时删错范围。
```

所以上线前必须验收数据链路。

### 13. RAG 与 Agent 边界验收要看什么

第 22 节学过边界。

上线前要确认：

```text
政策/流程问题归 RAG。
订单查询归 read tool。
工单创建归 Agent。
写操作需要确认。
禁用敏感工具不会执行。
unsafe 问题先拦截。
RAG 可以作为 Agent 上下文，但不拥有流程。
```

如果边界不清，可能出现：

```text
RAG 查询实时订单。
Agent 不查资料直接回答政策。
模型直接执行写工具。
禁用敏感工具被绕过。
no_context 后错误建工单。
```

### 14. 验收证据应该是什么

验收不能只写：

```text
已完成。
没问题。
看起来可以。
```

应该提供证据。

例如：

```text
pytest 测试结果。
评测报告。
bad case report。
security report。
performance protection report。
observability payload 示例。
data update plan。
agent boundary decision。
人工 review 记录。
灰度监控指标。
```

没有证据的通过没有意义。

### 15. 生产化不是一次性动作

RAG 生产化不是上线前检查一次就结束。

上线后还要持续：

```text
收集 bad case。
更新评测集。
重新跑指标。
分析 warning codes。
观察成本和延迟。
更新知识库。
复盘安全事件。
调整路由和参数。
```

RAG 是一个持续运营的系统，不是一次性脚本。

### 16. 什么是上线证据包

上线证据包是指上线前准备的一组材料。

它用来证明：

```text
这个 RAG 功能不是只在开发者机器上跑通，而是经过了质量、安全、性能、数据和边界验证。
```

一个比较完整的 RAG 上线证据包可以包括：

```text
功能说明。
知识库范围说明。
评测集说明。
检索指标报告。
回答质量报告。
bad case 分析报告。
Prompt Injection 安全测试结果。
权限过滤测试结果。
生产化验收清单报告。
性能和超时策略。
成本估算。
可观测字段说明。
灰度方案。
回滚方案。
```

你以后在工作或面试里可以这样表达：

```text
我们不是只做了一个 RAG demo，而是把上线前证据做成了 checklist，包括质量、安全、性能、成本、可观测和数据更新。
```

### 17. 什么是灰度上线

灰度上线就是不要一次性把功能开放给所有用户。

而是按范围逐步放量：

```text
先本地测试。
再内部测试。
再给少量客服使用。
再给某个业务域使用。
再逐步扩大流量。
最后全量上线。
```

RAG 很适合灰度。

原因是 RAG 的真实问题经常来自真实用户表达：

```text
用户问法很口语。
用户问题跨多个业务域。
用户会夹带订单号。
用户会问知识库没有覆盖的问题。
用户会用很短的问题。
```

这些很难只靠开发阶段全部模拟出来。

灰度上线时要重点看：

```text
no_context rate。
citation invalid rate。
fallback rate。
near_timeout / timed_out。
user negative feedback。
高频 bad case。
成本是否符合预期。
```

### 18. 什么是回滚方案

回滚方案是指上线后如果出问题，如何快速恢复。

RAG 的回滚不只是代码回滚。

可能包括：

```text
关闭真实模型调用。
切回规则版 rerank。
关闭某个知识库路由。
降低 max_routes。
调低 top_k。
禁用某个高风险知识库。
切回旧 collection。
清理错误缓存。
回退知识库版本。
关闭 Agent 写工具。
```

所以生产化验收里要问：

```text
出问题时能不能降级？
能不能关掉高风险能力？
能不能回到上一个知识库版本？
能不能停止写操作？
```

没有回滚方案，上线风险会变得很高。

### 19. 什么是 SLO

SLO 是 Service Level Objective，服务水平目标。

简单说就是：

```text
系统希望达到什么稳定性和性能目标。
```

RAG 可以有这些 SLO：

```text
P95 响应时间小于 3 秒。
no_context rate 低于 10%。
citation invalid rate 低于 1%。
rerank fallback rate 低于 5%。
timed_out rate 低于 0.5%。
核心评测集 Recall@5 高于 0.8。
核心评测集 answer point coverage 高于 0.85。
```

SLO 不一定一开始就非常严格。

但至少要有目标。

没有目标，就很难判断：

```text
当前系统是好还是差？
这次上线是改善还是退化？
某个 warning 是否可接受？
```

### 20. 什么是上线后的持续验收

上线不是结束。

上线后要持续把线上数据反馈回系统。

常见闭环：

```text
线上日志发现 warning。
warning 聚合成 bad case。
bad case 加入评测集。
评测集驱动参数调优。
调优后重新跑报告。
知识库更新后重新评测。
再次灰度上线。
```

这就是 RAG 的持续运营。

真实团队里，RAG 不是“做完就放着”。

它更像：

```text
知识库 + 检索系统 + 模型回答 + 评测体系 + 运营流程。
```

### 21. 哪些角色应该参与验收

RAG 生产化不是只有开发参与。

通常需要：

```text
后端开发：接口、工具、权限、稳定性。
AI 工程师：RAG、prompt、模型、评测。
业务人员：答案是否符合真实政策。
客服人员：话术是否可用、流程是否顺。
安全人员：权限、注入、日志、敏感数据。
测试人员：回归、边界、异常、兼容。
运维或平台人员：监控、告警、成本、发布。
```

学习阶段你不需要真的组织这些角色。

但你要知道真实项目上线时，这些角色关注点不同。

### 22. 小项目和真实项目清单有什么区别

学习项目可以简化。

例如：

```text
不用接真实监控平台。
不用真实 CI/CD 门禁。
不用正式安全审批。
不用大规模压测。
```

但不能省掉思维框架。

学习项目至少要保留：

```text
质量评测。
权限过滤。
Prompt Injection 基础防护。
引用校验。
超时降级。
安全日志。
数据更新策略。
RAG/Agent/Tool 边界。
```

这样你学到的不是玩具 demo，而是可迁移到真实工作的工程方法。

## 本节主题系统讲解

### 1. 第 23 节在阶段 9 里的位置

阶段 9 前面 22 节分别学习了很多单点能力。

本节把它们收束成上线视角：

```text
质量：第 13-17 节。
安全：第 11-12 节和第 22 节。
性能：第 18 节。
可观测：第 19 节。
数据：第 20 节。
路由和边界：第 21-22 节。
```

也就是说，本节不是凭空新增一个清单。

它是在回答：

```text
前面学的这些东西，上线前到底怎么检查？
```

### 2. 本节新增的核心结构

本节新增：

```text
RagProductionReadinessCheck。
RagProductionReadinessAnswer。
RagProductionReadinessFinding。
RagProductionReadinessReport。
```

它们分别表示：

```text
检查项。
某个检查项的验收结果。
没通过或有风险的发现。
整体验收报告。
```

这让生产化验收从文档变成结构化对象。

### 3. 默认清单覆盖哪些类别

默认清单覆盖 7 类：

```text
quality。
security。
performance。
cost。
observability。
data。
agent_boundary。
```

每类都有若干检查项。

例如 quality 有：

```text
retrieval metrics。
answer quality。
citation verification。
bad case process。
```

security 有：

```text
permission filter。
prompt injection。
safe logging。
tool boundaries。
```

这不是最终唯一标准。

真实项目可以根据业务继续扩展。

### 4. 为什么有些是 blocker，有些不是

不是所有问题都必须阻断上线。

例如：

```text
成本 fallback 率偏高。
某个非核心 warning code 还没做看板。
full reindex 文档还不够详细。
```

这些可能允许灰度。

但有些问题必须阻断：

```text
权限过滤没验证。
引用校验没有。
Prompt Injection 没防。
写工具不确认。
核心评测没跑。
数据删除没有策略。
```

因为这些问题可能造成严重质量、安全或业务后果。

### 5. 报告如何判断状态

本节报告规则是：

```text
如果 release_blocker 是 failed 或 not_checked -> blocked。
如果没有 blocker，但存在 warning、failed、not_checked -> conditional。
如果全部 passed -> ready。
```

这个规则很实用。

它避免两种错误：

```text
有阻断风险还上线。
有小 warning 就完全不能灰度。
```

### 6. category_status_counts 的价值

报告里有：

```text
category_status_counts。
```

它能看出风险集中在哪里。

例如：

```text
quality 全 passed。
security 有 failed。
observability 有 warning。
cost not_checked。
```

这比只看总数更有用。

因为不同类别的风险处理方式不同。

### 7. findings 的价值

`findings` 只记录非 passed 检查。

它包含：

```text
check_id。
category。
title。
status。
release_blocker。
evidence。
recommendation。
risk_if_missing。
```

这让团队能直接看到：

```text
问题是什么。
风险是什么。
该怎么处理。
是不是阻断上线。
```

### 8. 本节和前面模块怎么对应

清单不是孤立的。

对应关系如下：

```text
quality.retrieval_metrics -> evaluation.py。
quality.answer_quality -> evaluation.py。
quality.citation_verification -> citation_verification.py。
security.permission_filter -> filters.py。
security.prompt_injection -> security.py。
performance.degradation -> performance.py。
observability.rag_event -> observability.py。
data.update_plan -> data_update.py。
agent_boundary.owner_decision -> agent_boundary.py。
```

这说明项目不是只有笔记，而是已经有对应学习代码支撑验收思路。

### 9. 本节暂时不做什么

本节不接入真实发布平台。

原因：

```text
当前阶段重点是学习验收标准，不是做 CI/CD 发布门禁。
```

本节不强制跑所有阶段测试。

原因：

```text
省 token 模式下只跑本节和相关测试，完整回归可以在上传 GitHub 或阶段复盘时执行。
```

本节不替代人工审核。

原因：

```text
RAG 上线通常还需要产品、业务、安全、客服等角色一起审核。
```

### 10. 如何真正使用这份清单

一份 checklist 不能只放在文档里。

真正使用时，可以按这个流程：

```text
1. 确认本次要上线的 RAG 能力范围。
2. 选择适用的检查项。
3. 给每个检查项补 evidence。
4. 标记 passed / warning / failed / not_checked。
5. 生成 readiness report。
6. 如果 blocked，先修 blocker。
7. 如果 conditional，决定是否灰度以及如何监控。
8. 上线后持续收集 warning 和 bad case。
```

这就是从“知识点”走向“工程流程”。

### 11. 示例：为什么权限过滤没检查会 blocked

假设：

```text
security.permission_filter = not_checked
```

报告会变成：

```text
release_status = blocked
```

原因是权限过滤属于安全边界。

如果没有证据，就不知道：

```text
普通客服会不会看到 internal_staff 文档。
普通租户会不会看到其他租户文档。
deleted 或 archived 文档会不会继续被召回。
```

这种风险不能带着上线。

### 12. 示例：为什么成本 warning 可以 conditional

假设：

```text
cost.provider_fallback = warning
```

它可能表示：

```text
rerank fallback 率高于预期。
```

这不一定立刻阻断上线。

如果其他 blocker 都通过，可以选择：

```text
内部灰度。
限制流量。
加监控。
观察 fallback rate。
后续修 provider 稳定性。
```

所以报告可以是：

```text
release_status = conditional
```

conditional 不是“没事”，而是“带条件和监控上线”。

### 13. 如何把清单接到 CI/CD

真实项目里，readiness report 可以接入发布流程。

例如：

```text
自动跑 pytest。
自动跑 RAG eval。
生成 readiness answers。
如果 release_status=blocked，阻止合并或发布。
如果 conditional，允许灰度但要求审批。
如果 ready，允许正常发布。
```

当前学习项目没有做 CI/CD 门禁。

但本节代码已经把报告结构做好了。

后续如果接入自动化，只需要把证据来源接进来。

### 14. 如何给每个检查项准备 evidence

不同检查项的 evidence 不一样。

质量类：

```text
评测报告。
retrieval metrics。
answer quality summary。
bad case report。
```

安全类：

```text
权限过滤测试。
prompt injection 测试。
安全日志 payload。
tool registry 配置。
```

性能类：

```text
operation timing report。
performance protection report。
timeout 配置。
degradation 测试。
```

成本类：

```text
token budget。
top_k 上限。
context compression report。
fallback rate。
```

可观测性类：

```text
RagObservabilityEvent。
warning codes。
trace_id 示例。
```

数据类：

```text
document manifest。
data update plan。
metadata validation tests。
full reindex 策略。
```

边界类：

```text
RagAgentBoundaryDecision。
tool registry。
用户确认流程测试。
```

### 15. 如何处理 failed 但不是 blocker 的项目

非 blocker failed 不代表可以完全不管。

它表示：

```text
这个问题不会立即阻断上线，但仍然是真实风险。
```

处理方式可以是：

```text
写清楚残余风险。
限制灰度范围。
加监控。
安排修复时间。
准备回滚方案。
```

例如：

```text
某个非核心业务域评测覆盖不足。
某个低频 warning code 还没接入看板。
provider fallback 统计还不够细。
```

这些可以进入 conditional，但不能假装不存在。

### 16. 本节代码和真实生产系统的差距

本节代码是学习版。

它做了：

```text
定义检查项。
定义验收答案。
统计报告。
判断 ready / conditional / blocked。
```

真实生产系统还会补：

```text
读取真实评测报告。
接入 CI/CD。
接入监控平台。
接入发布审批。
记录历史版本。
支持不同环境的清单。
支持负责人和截止时间。
支持风险接受记录。
```

你现在先学核心模型。

后续做真实平台化时，再补这些工程能力。

## 本节代码讲解

### 1. `RagProductionReadinessCheck`

它表示一个检查项。

核心字段：

```text
check_id。
category。
title。
requirement。
evidence_examples。
risk_if_missing。
release_blocker。
```

重点是：

```text
每个检查项都要说清楚要求、证据和缺失风险。
```

### 2. `RagProductionReadinessAnswer`

它表示某个检查项的实际验收结果。

字段：

```text
check_id。
status。
evidence。
notes。
```

比如：

```text
check_id = security.permission_filter
status = passed
evidence = tests/test_rag_filters.py passed
```

### 3. `RagProductionReadinessReport`

它是整体验收报告。

字段包括：

```text
release_status。
checklist_count。
passed_count。
warning_count。
failed_count。
not_checked_count。
blocker_count。
category_status_counts。
blocker_check_ids。
findings。
```

它能回答：

```text
能不能上线？
为什么不能上线？
哪些类别风险最多？
哪些 blocker 没过？
```

### 4. `default_rag_production_readiness_checklist()`

它返回默认清单。

这份清单覆盖：

```text
质量。
安全。
性能。
成本。
可观测性。
数据。
RAG/Agent 边界。
```

真实项目可以在这份清单上增加公司自己的要求。

### 5. `build_rag_production_readiness_report()`

这个函数根据检查答案生成报告。

它会：

```text
校验 check_id 是否存在。
拒绝重复 answer。
把没有回答的检查项标记为 not_checked。
统计各状态数量。
找出 blocker。
生成 findings。
判断 release_status。
```

这就是本节的核心逻辑。

### 6. 本节测试重点

测试覆盖：

```text
默认清单覆盖核心类别。
所有检查 passed 时 release_status=ready。
阻断检查缺失时 blocked。
阻断检查 failed 时 blocked。
非阻断 warning 时 conditional。
未知 check_id 会报错。
重复 answer 会报错。
重复 checklist id 会报错。
```

这些测试验证的是验收规则，不需要真实调用模型或向量库。

## 常见误区

### 误区 1：接口能返回答案就可以上线

不对。

RAG 需要验证召回、回答、引用、权限、安全、性能、数据更新和可观测性。

能返回答案只是最基础的 smoke。

### 误区 2：评测集跑过一次就够了

不够。

知识库更新、参数变化、模型变化、路由变化都会影响结果。

评测集要持续更新和回归。

### 误区 3：没有发现问题就等于通过

不对。

没有检查不等于没有问题。

所以本节把 `not_checked` 单独列出来。

### 误区 4：安全靠 Prompt 就够了

不够。

安全需要权限过滤、Prompt Injection 扫描、日志脱敏、工具权限、用户确认和后端授权。

### 误区 5：warning 可以完全忽略

不应该。

warning 代表已知风险。

它可以允许条件上线，但必须被记录、监控和后续处理。

### 误区 6：成本问题上线后再说

不建议。

RAG 的 embedding、rerank、LLM token、重试和 fallback 都可能放大成本。

上线前至少要有预算和上限。

### 误区 7：可观测性以后再补

不建议。

没有可观测性，上线后出问题很难排查。

RAG 尤其需要记录 query、召回、rerank、引用和耗时。

### 误区 8：RAG 和 Agent 组合只要能跑就行

不够。

必须确认 RAG、Agent、Tool 的职责边界。

否则容易出现模型编造业务数据、RAG 执行流程、写工具绕过确认等问题。

### 误区 9：blocked 就代表项目失败

不是。

blocked 的意义是：

```text
当前不适合上线。
```

它是保护机制，不是坏消息。

发现 blocker 越早，修复成本越低。

### 误区 10：conditional 就等于 ready

不对。

conditional 是带条件放行。

它通常需要：

```text
灰度范围。
监控指标。
负责人。
回滚方案。
后续修复计划。
```

不能把 conditional 当作完全通过。

### 误区 11：上线清单越多越好

不一定。

清单太少会漏风险，太多会变成形式主义。

好的清单应该满足：

```text
覆盖关键风险。
每项能提供证据。
能明确阻断条件。
能指导下一步动作。
```

### 误区 12：RAG 生产化只属于 AI 工程师

不对。

RAG 生产化涉及：

```text
后端服务。
业务知识。
安全权限。
测试评测。
平台监控。
成本管理。
客服使用体验。
```

AI 工程师负责其中一部分，但不是全部。

## 本节练习

### 练习 1：为什么 `not_checked` 不能当作通过？

答案：

因为没有检查就没有证据。生产化要求用证据证明风险可控，`not_checked` 只能说明当前不知道有没有问题，尤其是 release blocker 项目没检查时应该阻断上线。

### 练习 2：列出三个应该作为 RAG release blocker 的检查。

答案：

可以是权限过滤、引用校验、Prompt Injection 防护、核心检索指标、回答质量评测、写操作用户确认、数据删除/更新策略、核心阶段超时降级。它们失败或未检查都可能造成严重质量、安全或业务风险。

### 练习 3：为什么成本也要进入 RAG 验收？

答案：

因为 RAG 可能调用 embedding、rerank 和 LLM，且 top_k、context budget、重试、fallback 都会影响成本。没有成本验收，系统可能在流量上来后账单失控或延迟变高。

### 练习 4：为什么数据更新是生产化清单的一部分？

答案：

因为知识库会变化。没有新增、修改、删除、重新索引策略，旧 chunks、重复 chunks、已删除文档和错误 metadata 会继续影响 RAG 回答。

### 练习 5：`conditional` 状态适合什么场景？

答案：

适合没有 blocker 失败或缺失，但存在 warning、非阻断 failed 或非阻断 not_checked 的场景。可以用于灰度上线、内部试用、低流量上线，但必须保留监控和后续修复计划。

## 自测题

### 自测 1：RAG 生产化验收至少包括哪七类？

答案：

质量、安全、性能、成本、可观测性、数据、RAG/Agent 边界。

### 自测 2：`ready / conditional / blocked` 的区别是什么？

答案：

`ready` 表示所有检查都通过。`conditional` 表示没有阻断项失败或缺失，但还有 warning 或非阻断风险。`blocked` 表示有 release blocker 失败或未检查，不应该上线。

### 自测 3：为什么权限过滤应该是 blocker？

答案：

因为权限过滤失败会造成用户看到无权访问的知识，属于严重安全问题。RAG 的相关性不能高于权限边界。

### 自测 4：为什么可观测性要记录 warning codes？

答案：

warning codes 是机器可读的稳定原因码，适合日志过滤、指标聚合、告警、bad case 归因和持续运营。只写自然语言日志不利于统计。

### 自测 5：生产化验收清单和测试用例是什么关系？

答案：

测试用例是验收证据的一种。生产化清单比测试更宽，它还包括评测报告、安全 review、性能报告、成本预算、观测字段、数据更新策略和人工确认记录等证据。

## 本节小结

本节你学到的是：

```text
RAG 上线前不能只看接口是否能跑。
质量、安全、性能、成本、可观测、数据和边界都要有证据。
release blocker failed 或 not_checked 应该 blocked。
非阻断 warning 可以 conditional，但要记录和跟进。
生产化是持续过程，不是一次性检查。
```

下一节是阶段 9 总复盘和面试表达强化，会把整个 RAG 进阶阶段整理成能力地图、项目表达和面试回答。
