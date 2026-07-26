# 阶段 6 第 25 节：会话过期与清理

本节目标：理解过期、保留、归档、删除的区别，并为当前智能工单 Agent 设计一个最小可测试的 thread / checkpoint 清理计划。

第 24 节我们已经学了：

```text
thread_id 怎么创建
thread_id 怎么绑定 actor_id
active / waiting_confirmation / completed / closed 状态
expires_at 怎么判断过期
恢复前怎么决定 resume_existing / start_new / reject
```

第 25 节继续回答：

```text
过期以后怎么办？
完成以后怎么办？
关闭以后怎么办？
checkpoint 历史会不会一直增长？
哪些数据能删？
哪些数据要留审计？
```

这一节很重要，因为生产系统里只会“保存状态”还不够。

如果没有清理策略，系统会慢慢变成：

```text
checkpoint 越积越多
过期确认还留在热数据里
历史会话和当前会话混在一起
存储成本不断增加
排查时找不到重点
```

---

## 一、本节在主线里的位置

阶段 6 第 22-25 节是一个完整小组：

```text
第 22 节：持久化 checkpoint 基础
第 23 节：checkpoint 存储选型
第 24 节：thread_id 生命周期
第 25 节：会话过期与清理
```

第 22 节解决：

```text
状态怎么保存。
```

第 23 节解决：

```text
状态存到哪里。
```

第 24 节解决：

```text
状态属于谁，什么时候能继续用。
```

第 25 节解决：

```text
状态什么时候不该继续留在热存储里。
```

这四节合起来，才是比较完整的生产化 checkpoint 基础。

---

## 二、官方资料确认

LangGraph 官方 checkpointers 文档提醒：

```text
长对话里 checkpoint 会不断累积。
checkpoint 增长会增加延迟和存储成本。
需要定期 prune old checkpoints 或设置 retention policy。
```

这说明：

```text
清理不是可有可无的优化，而是 checkpoint 生产化的一部分。
```

参考资料：

- LangGraph Persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph Checkpointers: https://docs.langchain.com/oss/python/langgraph/checkpointers

---

## 三、基础知识铺垫

### 1. 什么是过期

过期是：

```text
数据超过有效时间，不再允许作为当前有效状态使用。
```

例如：

```text
等待确认 30 分钟后过期。
普通会话 24 小时后过期。
临时验证码 5 分钟后过期。
```

过期的重点是：

```text
不能再用。
```

但过期不等于马上删除。

### 2. 什么是删除

删除是：

```text
把数据从存储里物理移除。
```

例如：

```text
删除 checkpoint 记录。
删除临时确认状态。
删除旧的会话绑定。
```

删除的重点是：

```text
以后很难或无法再查到。
```

所以删除要谨慎。

尤其是涉及写操作的流程。

### 3. 过期和删除的区别

过期回答：

```text
这条数据还能不能继续用于业务？
```

删除回答：

```text
这条数据还要不要继续保存在系统里？
```

举例：

```text
用户 31 分钟前进入创建工单确认页。
```

如果确认 TTL 是 30 分钟，那么：

```text
这条确认已经过期。
不能继续创建工单。
```

但是你可能还要保留一段时间，用于排查：

```text
用户是什么时候发起的？
系统什么时候要求确认？
为什么后来不能确认？
有没有误触发？
```

所以正确思路是：

```text
先过期，再保留一段时间，最后归档或删除。
```

### 4. 什么是 retention

retention 是保留期。

它表示：

```text
数据即使已经不能继续用于业务，也要保留多久。
```

例如：

```text
完成的工单 thread 保留 7 天。
关闭的 thread 保留 7 天。
过期的确认 thread 先保留 24 小时。
```

保留期的作用：

```text
给排查、审计、用户投诉和回放留窗口。
```

如果保留期太短：

```text
问题发生后查不到。
```

如果保留期太长：

```text
存储成本增加，敏感信息风险增加。
```

### 5. 什么是 archive

archive 是归档。

它表示：

```text
把数据从热路径里移走，但保留必要审计信息。
```

热路径可以理解为：

```text
系统日常运行时经常读写的存储区域。
```

归档区可以理解为：

```text
不参与日常恢复，只用于审计、排查和历史记录。
```

举例：

```text
Postgres checkpoint 表是热存储。
审计表或冷存储是归档。
```

归档后可以从热 checkpoint 中删除大体积 state。

但归档里应该至少保留：

```text
thread_id
actor_id
status
created_at
updated_at
closed/expired/completed reason
ticket_id
trace_id
必要的安全审计字段
```

### 6. 什么是 cleanup

cleanup 是清理。

它不是单一动作，而是一组动作：

```text
找出过期/完成/关闭的 thread
判断是否还在保留期
决定 keep / expire / archive
归档必要信息
删除热 checkpoint
记录清理日志
```

所以 cleanup 不是简单：

```text
delete where expires_at < now
```

这太粗暴。

### 7. 什么是 hot storage

hot storage 是热存储。

可以理解为：

```text
系统运行时频繁读写的数据位置。
```

比如：

```text
当前可恢复 checkpoint
当前等待确认状态
当前活跃 thread binding
```

热存储应该保持：

```text
小
快
当前有效
容易查询
```

如果热存储塞满很多旧 checkpoint，会影响性能和排查效率。

### 8. 什么是 cold storage

cold storage 是冷存储。

可以理解为：

```text
不常访问，但需要长期保存的数据位置。
```

例如：

```text
审计表
归档表
对象存储
压缩日志
历史报告
```

冷存储访问频率低，但可以保留更久。

### 9. 为什么 checkpoint 会越来越多

LangGraph 会在 super-step 边界保存 checkpoint。

一个复杂 Agent 流程可能走很多节点：

```text
normalize_user_input
classify_intent
retrieve_policy
decide_ticket_need
query_order
extract_ticket_fields
request_ticket_confirmation
create_ticket
```

每一步都可能产生 checkpoint。

如果是多轮对话：

```text
用户问 10 轮
每轮走多个节点
```

checkpoint 数量就会持续增长。

所以生产系统必须考虑：

```text
保留多少
保留多久
怎么清理
怎么审计
```

---

## 四、本节主题系统讲解

### 1. 清理策略不是删除策略

清理策略包括：

```text
keep
expire
archive
delete_after_archive
```

其中：

```text
keep：继续保留在热存储。
expire：标记或判断为过期，不允许恢复，但暂时不删除。
archive：需要归档审计信息。
delete_after_archive：归档之后，可以从热 checkpoint 删除。
```

为什么不能只有 delete？

因为真实系统里经常要回答：

```text
用户为什么不能确认了？
这个工单是不是重复创建了？
确认时字段是什么？
这个 thread 是谁的？
什么时候过期的？
```

如果一过期就删，很多问题没法排查。

### 2. 本节采用的清理状态

本节代码里的清理动作是：

```text
keep
expire
archive
```

checkpoint 动作是：

```text
keep
delete_after_archive
```

这两个分开，是为了强调：

```text
thread 决策和 checkpoint 物理删除不是一回事。
```

比如：

```text
action=archive
checkpoint_action=delete_after_archive
```

表示：

```text
先归档必要审计信息。
归档成功后，再从热 checkpoint 中删除。
```

### 3. active thread 的清理

`active` 表示：

```text
线程还在正常会话中。
```

如果没有过期：

```text
action=keep
reason=active_not_expired
checkpoint_action=keep
```

如果已经过期，但还在 grace period 内：

```text
action=expire
reason=expired_active_grace_period
checkpoint_action=keep
```

如果过期后超过 grace period：

```text
action=archive
reason=expired_cleanup_due
checkpoint_action=delete_after_archive
```

这里的 grace period 可以理解为：

```text
过期后的缓冲保留期。
```

### 4. waiting_confirmation 的清理

`waiting_confirmation` 比 `active` 更敏感。

因为它通常表示：

```text
系统正在等待用户确认一个写操作。
```

如果没过期：

```text
action=keep
reason=waiting_confirmation_not_expired
checkpoint_action=keep
```

如果过期但还在 grace period 内：

```text
action=expire
reason=expired_confirmation_grace_period
checkpoint_action=keep
archive_required=True
```

为什么这里 `archive_required=True`？

因为确认过期和写操作有关，应该留下审计线索。

例如：

```text
系统曾经请求用户确认创建工单。
用户没有在 30 分钟内确认。
确认已过期。
```

这类信息对排查很有价值。

如果超过 grace period：

```text
action=archive
reason=expired_cleanup_due
checkpoint_action=delete_after_archive
archive_required=True
```

意思是：

```text
必须先保留审计信息，再清掉热 checkpoint。
```

### 5. completed thread 的清理

`completed` 表示：

```text
流程已经正常完成。
```

例如：

```text
工单创建成功。
```

完成后的 thread 不应该继续恢复，但也不应该马上删除。

原因：

```text
完成流程经常需要审计。
可能要排查是否重复创建。
可能要对齐 ticket_id。
可能要追踪用户确认时的字段。
```

所以本节策略是：

```text
completed 在保留期内 keep。
超过保留期后 archive。
归档成功后可以 delete_after_archive。
```

### 6. closed thread 的清理

`closed` 表示：

```text
流程被主动关闭，但不一定完成业务目标。
```

例如：

```text
用户取消创建工单。
客服关闭会话。
系统异常终止。
```

closed 也需要保留一段时间。

原因：

```text
用户可能问为什么取消了。
客服可能需要复盘。
系统可能需要排查异常关闭原因。
```

所以本节策略是：

```text
closed 在保留期内 keep。
超过保留期后 archive。
归档成功后可以 delete_after_archive。
```

### 7. 为什么删除 checkpoint 要在归档之后

checkpoint 里可能有大量上下文：

```text
用户问题
节点历史
工具结果
待确认字段
错误状态
```

热 checkpoint 不适合无限保存。

但如果直接删除，就丢失排查线索。

所以生产清理通常应该是：

```text
1. 生成归档记录
2. 确认归档成功
3. 删除热 checkpoint
4. 写清理日志
```

也就是：

```text
delete_after_archive
```

这个名字故意很明确：

```text
不是现在立刻 delete。
而是归档之后才能 delete。
```

### 8. 本节默认时间策略

本节代码使用默认策略：

```text
expired_thread_grace_seconds = 24 小时
completed_thread_retention_seconds = 7 天
closed_thread_retention_seconds = 7 天
```

这不是行业硬标准。

它只是一个教学阶段的保守示例。

真实系统要根据：

```text
业务风险
合规要求
存储成本
用户体验
排查需要
数据敏感级别
```

来调整。

### 9. 清理任务什么时候跑

清理通常不是用户请求时同步做。

常见方式：

```text
定时任务
后台 worker
cron job
队列消费者
管理脚本
```

例如：

```text
每小时扫描一次过期 waiting_confirmation。
每天凌晨归档完成超过 7 天的 completed thread。
每周清理一次旧 checkpoint。
```

为什么不建议每次请求都大范围清理？

因为：

```text
用户请求应该尽快返回。
大范围扫描可能拖慢接口。
清理失败不应该影响正常问答。
```

### 10. 清理时怎么避免删错正在使用的 thread

核心原则：

```text
只清理明确不该恢复的 thread。
```

清理前要检查：

```text
status
expires_at
updated_at
retention deadline
是否已经归档
是否仍有 pending_confirmation
是否有正在执行的 run
```

本节代码是最小版，只做：

```text
status + expires_at + updated_at + retention policy
```

后续生产实现可以继续补：

```text
分布式锁
任务批次 ID
归档状态字段
清理日志
失败重试
幂等删除
```

---

## 五、本节代码改动讲解

本节新增：

```text
projects/ai-service/app/agents/thread_cleanup.py
projects/ai-service/tests/test_ticket_agent_thread_cleanup.py
```

### 1. `TicketAgentThreadCleanupPolicy`

这个类表示清理策略。

包含：

```text
expired_thread_grace_seconds
completed_thread_retention_seconds
closed_thread_retention_seconds
```

为什么要做成 policy？

因为时间规则不应该散落在代码里。

如果以后业务要求：

```text
完成 thread 保留 30 天。
关闭 thread 保留 15 天。
过期确认保留 48 小时。
```

只要换 policy 即可。

### 2. `TicketAgentThreadCleanupDecision`

这个类表示单个 thread 的清理决策。

字段：

```text
thread_id
status
action
reason
checkpoint_action
archive_required
eligible_at
```

重点是：

```text
action 说明 thread 怎么处理。
checkpoint_action 说明 checkpoint 怎么处理。
reason 说明为什么这么处理。
eligible_at 说明什么时候达到清理条件。
```

这比返回一个简单布尔值好得多。

因为生产排查时你需要知道：

```text
为什么这个 thread 被清理？
什么时候该清理？
清理前是否需要归档？
```

### 3. `TicketAgentThreadCleanupPlan`

这个类表示一批 thread 的清理计划。

它提供：

```text
count_by_action()
archive_required_thread_ids()
checkpoint_delete_thread_ids()
```

这让后台清理任务可以先生成计划，再执行动作。

例如：

```text
本次扫描 1000 个 thread
keep 870 个
expire 80 个
archive 50 个
其中 50 个归档后可删除 checkpoint
```

这就很适合写日志和监控。

### 4. `evaluate_ticket_agent_thread_cleanup`

这是本节核心函数。

输入：

```text
TicketAgentThreadBinding
TicketAgentThreadCleanupPolicy
now
```

输出：

```text
TicketAgentThreadCleanupDecision
```

它按状态判断：

```text
active / waiting_confirmation
completed
closed
```

再结合：

```text
expires_at
updated_at
retention_seconds
```

决定：

```text
keep / expire / archive
```

### 5. `build_ticket_agent_thread_cleanup_plan`

这个函数处理一批 thread。

它不会直接删除数据。

它只负责：

```text
生成清理计划。
```

为什么不直接删？

因为生产里更合理的流程是：

```text
先计划
再审计
再执行
再记录结果
```

本节先做计划层，是为了安全。

---

## 六、测试怎么证明这节做对了

本节新增测试：

```text
projects/ai-service/tests/test_ticket_agent_thread_cleanup.py
```

覆盖：

```text
active 未过期时 keep。
waiting_confirmation 过期但在 grace period 内时 expire。
过期超过 grace period 后 archive，并允许归档后删除 checkpoint。
completed 在 retention 内 keep。
completed 超过 retention 后 archive。
closed 超过 retention 后 archive。
批量 cleanup plan 能统计 keep / expire / archive，并列出需要归档和可删除 checkpoint 的 thread_id。
```

相关测试：

```text
test_ticket_agent_thread_lifecycle.py
test_ticket_agent_intent.py
test_ticket_agent_checkpoint_store.py
```

用于确认：

```text
清理策略没有破坏已有 thread 生命周期、checkpoint 和工单流程。
```

---

## 七、当前项目推荐清理设计

当前项目推荐采用：

```text
先做清理计划，不直接删除。
```

### 1. 热存储里保留什么

热存储保留：

```text
active thread
未过期 waiting_confirmation
保留期内 completed thread
保留期内 closed thread
过期但还在 grace period 内的 thread
```

### 2. 什么时候 expire

当：

```text
active / waiting_confirmation 已经过 expires_at
但还没有超过 expired grace period
```

决策：

```text
action=expire
checkpoint_action=keep
```

waiting_confirmation 还要：

```text
archive_required=True
```

### 3. 什么时候 archive

当：

```text
过期 thread 超过 grace period
completed 超过 retention
closed 超过 retention
```

决策：

```text
action=archive
checkpoint_action=delete_after_archive
archive_required=True
```

### 4. 什么时候 delete checkpoint

只有在：

```text
归档完成之后
```

才删除热 checkpoint。

所以删除动作应该叫：

```text
delete_after_archive
```

不是：

```text
delete_now
```

### 5. 过期确认应该怎么提示用户

如果用户带着过期 confirmation 回来：

```text
不能继续创建工单。
```

应该提示类似：

```text
本次工单确认已过期，请重新发起工单创建流程。
```

不要默默恢复旧流程。

不要直接创建工单。

### 6. 清理日志应该记录什么

至少记录：

```text
cleanup_batch_id
thread_id
actor_id
status
action
reason
checkpoint_action
archive_required
eligible_at
created_at
updated_at
expires_at
```

后续阶段学生产日志字段时会继续补。

---

## 八、常见错误

### 错误 1：一过期就物理删除

问题：

```text
排查和审计线索丢失。
```

正确做法：

```text
过期后先禁止恢复，再保留一段 grace period，必要时归档后再删除热 checkpoint。
```

### 错误 2：只清理 completed，不清理 expired

问题：

```text
用户放弃、确认过期、异常关闭的 thread 会越积越多。
```

正确做法：

```text
active 过期、waiting_confirmation 过期、completed、closed 都要有策略。
```

### 错误 3：把 archive 和 delete 混为一谈

问题：

```text
以为归档就是删除，或者以为删除就是归档。
```

正确做法：

```text
archive 是保留必要历史信息。
delete 是从热存储移除大体积 checkpoint。
```

### 错误 4：清理任务和用户请求强绑定

问题：

```text
用户请求变慢，清理失败影响正常业务。
```

正确做法：

```text
用定时任务、后台 worker 或管理脚本做清理。
```

### 错误 5：没有 reason

问题：

```text
只知道删了，不知道为什么删。
```

正确做法：

```text
每个清理决策都要有 reason。
```

### 错误 6：没有幂等

问题：

```text
清理任务重试时可能重复归档、重复删除、报错。
```

正确做法：

```text
生产实现要让 archive/delete 幂等。本节先做决策层，后续执行层再补幂等。
```

---

## 九、面试和工作中怎么讲

### 1. 30 秒版本

```text
checkpoint 会随着 Agent super-step 和多轮对话不断增长，所以生产系统必须有 retention 和 cleanup 策略。过期不等于删除，过期只是不能继续恢复；删除前通常要保留一段 grace period，并归档必要审计信息。对智能工单这种涉及写操作确认的流程，waiting_confirmation 过期后不能再创建工单，但要保留审计线索，超过保留期后再归档并从热 checkpoint 删除。
```

### 2. 1 分钟版本

```text
我会把会话清理分成 keep、expire、archive、delete_after_archive。active 和 waiting_confirmation 没过期时保留；过期后先进入 expire，不允许继续恢复，但暂时保留 checkpoint 方便排查；超过 grace period 后进入 archive，先保存 thread_id、actor_id、状态、时间、ticket_id、确认状态等审计字段，归档成功后才从热 checkpoint 删除。completed 和 closed thread 也不能马上删除，要按 retention 保留一段时间，超过后归档。这样可以控制 checkpoint 增长，也能保留必要审计能力。
```

### 3. 3 分钟版本

```text
LangGraph checkpoint 是按 thread 保存的状态快照，长对话和多节点 Agent 会不断产生 checkpoint。如果没有清理策略，checkpoint 表或文件会不断增长，影响存储成本、查询效率和故障排查。

我会先区分过期、保留、归档和删除。过期表示不能继续用于业务恢复，但不等于立刻删除；retention 表示为了排查和审计继续保留多久；archive 表示把必要历史信息移到审计或冷存储；delete_after_archive 表示归档成功后，才从热 checkpoint 删除大体积状态。

在智能工单 Agent 里，active thread 未过期就 keep；waiting_confirmation 是写操作确认状态，过期后不能继续创建工单，但应该留下确认过期的审计线索；completed 表示工单流程已完成，要保留一段时间用于排查重复创建或字段确认；closed 表示用户取消或系统关闭，也要保留一段时间。超过保留期后，再归档并删除热 checkpoint。

本节项目里我把这套规则做成 CleanupPolicy、CleanupDecision 和 CleanupPlan。它们只生成决策，不直接删除数据。这样后台任务可以先计划、记录日志、归档，再执行删除，避免一上来就做危险物理删除。
```

---

## 十、本节练习

### 练习 1：解释过期和删除的区别

问题：

```text
为什么说“过期不等于删除”？
```

参考答案：

```text
过期表示数据不能再作为当前有效状态使用，比如过期确认不能继续创建工单。删除表示把数据从存储中物理移除。过期后可能还要保留一段时间用于排查和审计，所以不能一过期就立刻删除。
```

### 练习 2：waiting_confirmation 过期后应该怎么处理

问题：

```text
用户 40 分钟后才点击创建工单确认按钮，而确认 TTL 是 30 分钟，应该怎么处理？
```

参考答案：

```text
不能继续创建工单。应该提示本次确认已过期，请重新发起流程。同时可以保留或归档这次过期确认的审计信息，例如 thread_id、actor_id、pending_confirmation_id、过期时间和当时的字段摘要。
```

### 练习 3：completed thread 为什么不能马上删除

问题：

```text
工单已经创建成功，为什么 completed thread 还要保留一段时间？
```

参考答案：

```text
因为完成后的流程可能用于排查和审计，例如确认用户是否真的确认、字段是什么、是否重复创建、ticket_id 是什么、创建前后 trace_id 是什么。如果马上删除，后续问题很难查。
```

### 练习 4：archive 和 delete 的顺序

问题：

```text
为什么要先 archive，再 delete checkpoint？
```

参考答案：

```text
因为 checkpoint 里有排查和审计需要的信息。先 archive 可以保留必要历史字段，归档成功后再删除热 checkpoint，既能控制热存储增长，又不会完全丢失审计线索。
```

### 练习 5：设计一个清理策略

问题：

```text
假设普通会话 24 小时过期，确认状态 30 分钟过期，completed 保留 7 天。请写出 expired waiting_confirmation、completed 3 天、completed 10 天分别怎么处理。
```

参考答案：

```text
expired waiting_confirmation：不允许恢复，进入 expire，并保留审计线索；超过 grace period 后归档并删除热 checkpoint。
completed 3 天：还在 7 天保留期内，keep。
completed 10 天：超过 7 天保留期，archive，归档成功后 delete_after_archive。
```

### 练习 6：为什么清理任务要有 reason

问题：

```text
清理决策里为什么要记录 reason？
```

参考答案：

```text
因为后续排查需要知道为什么这个 thread 被保留、过期或归档。没有 reason，就只能看到结果，看不到依据。reason 也方便写日志、做监控和统计。
```

---

## 十一、自测问题

### 自测 1：本节的三个 thread cleanup action 是什么？

参考答案：

```text
keep、expire、archive。keep 表示保留在热存储；expire 表示不允许继续恢复但暂不删除；archive 表示需要归档，归档后可从热 checkpoint 删除。
```

### 自测 2：checkpoint_action 为什么单独存在？

参考答案：

```text
因为 thread 的业务状态处理和 checkpoint 的物理删除不是一回事。一个 thread 可以 action=archive，同时 checkpoint_action=delete_after_archive，表示先归档业务审计信息，再删除热 checkpoint。
```

### 自测 3：为什么 waiting_confirmation 过期时 archive_required=True？

参考答案：

```text
因为 waiting_confirmation 通常对应写操作前确认。它过期后不能继续执行写操作，但应该保留审计线索，说明系统曾请求确认、用户没有在有效期内确认。
```

### 自测 4：清理任务为什么不应该直接写在用户请求里？

参考答案：

```text
因为清理可能扫描大量数据，会拖慢用户请求。清理失败也不应该影响正常业务。更合适的是定时任务、后台 worker 或管理脚本。
```

### 自测 5：completed 和 closed 的清理策略有什么共同点？

参考答案：

```text
它们都不应该继续恢复旧 thread，也都不应该马上删除。应该保留一段 retention 时间用于排查和审计，超过保留期后归档，再从热 checkpoint 删除。
```

### 自测 6：什么是 hot storage？

参考答案：

```text
hot storage 是系统日常运行时频繁读写的数据位置，比如当前可恢复 checkpoint、未过期确认状态和活跃 thread binding。热存储应该保持小、快、当前有效。
```

### 自测 7：本节为什么只生成 cleanup plan，不直接删除文件或数据库记录？

参考答案：

```text
因为删除是高风险动作。先生成 cleanup plan 可以把判断逻辑和执行逻辑分开，便于测试、审计、日志记录和后续实现幂等执行。等策略清楚后，再做真正删除更安全。
```

---

## 十二、本节总结

本节你要真正掌握：

```text
checkpoint 会增长，必须有 retention 和 cleanup。
过期不等于删除。
删除前通常要归档必要审计信息。
active / waiting_confirmation / completed / closed 都需要不同清理策略。
waiting_confirmation 过期后不能继续写操作。
completed 和 closed 要保留一段时间用于审计。
cleanup 决策要包含 action、reason、checkpoint_action、archive_required、eligible_at。
生产清理任务应该后台运行，并且后续要考虑幂等、日志、锁和失败重试。
```

本节代码完成：

```text
TicketAgentThreadCleanupPolicy
TicketAgentThreadCleanupDecision
TicketAgentThreadCleanupPlan
evaluate_ticket_agent_thread_cleanup()
build_ticket_agent_thread_cleanup_plan()
7 条 thread cleanup 测试
```

下一节：

```text
阶段 6 第 26 节：LangSmith tracing 基础
```

下一节会开始进入可观测性：

```text
trace
run
metadata
dataset
experiment
为什么 Agent 需要专门的 tracing
LangSmith 和普通日志的区别
```
