# 阶段 6 第 24 节：`thread_id` 生命周期

本节目标：把 `thread_id` 从“传给 LangGraph 的一个字符串”升级为“有创建、绑定、恢复、结束、过期规则的会话生命周期对象”。

第 21 节我们已经用过：

```python
{"configurable": {"thread_id": "ticket-thread-001"}}
```

第 22 节我们把 checkpoint 快照落盘。

第 23 节我们学习了 checkpoint 存储选型。

但还有一个问题没有系统讲透：

```text
thread_id 到底从哪里来？
绑定谁？
什么时候继续用？
什么时候不能继续用？
什么时候应该结束？
什么时候应该过期？
```

这就是本节要学的 `thread_id` 生命周期。

---

## 一、本节在主线里的位置

阶段 6 第 22-25 节是一组连续内容：

```text
第 22 节：持久化 checkpoint 基础
第 23 节：checkpoint 存储选型
第 24 节：thread_id 生命周期
第 25 节：会话过期与清理
```

第 22 节关注：

```text
checkpoint 保存什么
```

第 23 节关注：

```text
checkpoint 存在哪里
```

第 24 节关注：

```text
checkpoint 属于谁、什么时候能被继续使用
```

没有第 24 节，系统就容易出现这些问题：

```text
用户 A 恢复到了用户 B 的流程。
已经完成的工单流程又被继续执行。
过期确认还可以创建工单。
刷新页面后到底是继续旧会话还是开新会话没有规则。
thread_id 太长、带路径符号、带空格，后续进数据库或文件时出问题。
```

所以 `thread_id` 生命周期不是小细节，而是生产化 Agent 的安全边界之一。

---

## 二、官方资料确认

本节参考了 LangGraph 官方 persistence 和 checkpointers 文档。

官方文档里有几个关键点：

```text
1. checkpointer 按 thread 保存 graph state。
2. 调用带 checkpointer 的 graph 时，需要在 config.configurable 里传 thread_id。
3. thread_id 是 checkpointer 保存和读取 checkpoint 的关键。
4. 没有 thread_id，checkpointer 无法保存状态，也无法在 interrupt 后恢复。
5. PostgresSaver 存 thread_id 的字段长度有限，官方建议保持在 255 字符以内。
```

这说明：

```text
thread_id 不是普通日志字段。
它是 checkpoint 的主键级概念。
```

参考资料：

- LangGraph Persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph Checkpointers: https://docs.langchain.com/oss/python/langgraph/checkpointers

---

## 三、基础知识铺垫

### 1. 什么是 ID

ID 是 identifier，标识符。

它的作用是：

```text
在很多对象里，准确指出某一个对象。
```

比如：

```text
user_id：标识一个用户
order_id：标识一个订单
ticket_id：标识一个工单
trace_id：标识一次请求链路
thread_id：标识一条 Agent 执行线程
```

ID 的核心要求是：

```text
稳定
唯一或足够唯一
可用于查询
不容易串
有明确归属
```

如果 ID 管理混乱，系统就会混乱。

### 2. 什么是 thread

在 LangGraph 语境里，thread 可以理解为：

```text
一条可持续的 graph 执行线。
```

它不是操作系统线程。

它更像：

```text
一段 Agent 会话流程。
```

例如一个用户发起投诉：

```text
用户：我要投诉订单 1001，物流一直不动
Agent：提取字段
Agent：请求用户确认
用户：确认
Agent：继续创建工单
```

这一整段流程可以属于同一个：

```text
thread_id
```

### 3. `thread_id` 是什么

`thread_id` 是：

```text
LangGraph checkpointer 用来保存和恢复某条执行线状态的 key。
```

调用 graph 时：

```python
graph.invoke(
    state,
    config={"configurable": {"thread_id": "ticket-thread-001"}},
)
```

读取状态时：

```python
graph.get_state(
    {"configurable": {"thread_id": "ticket-thread-001"}}
)
```

恢复 interrupt 时：

```python
graph.invoke(
    Command(resume={"approved": True}),
    config={"configurable": {"thread_id": "ticket-thread-001"}},
)
```

这几个操作必须使用同一个 `thread_id`，LangGraph 才知道：

```text
我要从哪条执行线继续。
```

### 4. `thread_id` 和 `trace_id` 的区别

这两个很容易混。

`trace_id` 代表：

```text
一次请求链路。
```

比如用户点击一次按钮，前端请求 Python 服务，Python 调 Java 服务，整个链路用同一个 trace_id 串起来。

`thread_id` 代表：

```text
一条 Agent 会话或执行线程。
```

一个 thread 里可能有多次请求。

例如：

```text
请求 1：用户发起工单，trace_id = trace-001，thread_id = ticket-thread-001
请求 2：用户确认创建，trace_id = trace-002，thread_id = ticket-thread-001
请求 3：用户追问进度，trace_id = trace-003，thread_id = ticket-thread-001
```

所以：

```text
trace_id 更短，是一次调用链路。
thread_id 更长，是一段 Agent 流程。
```

不能用 `trace_id` 替代 `thread_id`。

### 5. `thread_id` 和 `user_id / actor_id` 的区别

`user_id / actor_id` 代表：

```text
谁在操作。
```

`thread_id` 代表：

```text
操作的是哪条 Agent 流程。
```

一个用户可以有多个 thread：

```text
thread A：咨询退款政策
thread B：投诉订单 1001
thread C：查询订单 1002
```

所以不能简单用：

```text
thread_id = user_id
```

如果这么做，会导致一个用户所有会话都混在一起。

正确做法是：

```text
thread_id 标识流程
actor_id 标识操作者
thread 绑定 actor_id
恢复时校验 actor_id 是否一致
```

### 6. `thread_id` 和 `session_id` 的区别

`session_id` 通常代表：

```text
浏览器会话、登录会话、客户端会话。
```

它偏前端或认证系统。

`thread_id` 偏 Agent 执行流程。

一个 session 里可以有多个 thread：

```text
session-001
  -> ticket-thread-001
  -> ticket-thread-002
```

一个 thread 也可能跨 session 恢复：

```text
用户今天在电脑上发起工单。
明天在手机上继续确认。
```

这时 session 变了，但如果业务允许，thread 可以恢复。

所以 `session_id` 不能直接等同于 `thread_id`。

### 7. `thread_id` 和 `ticket_id` 的区别

`ticket_id` 是创建成功后的业务工单 ID。

`thread_id` 是创建工单前后 Agent 流程的 ID。

在创建工单之前：

```text
thread_id 已经存在
ticket_id 还不存在
```

比如：

```text
用户发起投诉 -> thread_id = ticket-thread-001
Agent 请求确认 -> thread_id 仍然存在
用户确认后创建工单 -> ticket_id = T1001
```

所以不能用 `ticket_id` 作为创建前的 `thread_id`。

因为创建前根本还没有 `ticket_id`。

### 8. 为什么 `thread_id` 不能由用户随便传

如果用户可以随便传：

```text
ticket-thread-001
ticket-thread-002
ticket-thread-other-user
```

就可能出现：

```text
越权恢复别人的流程
读取别人的上下文
确认别人的写操作
造成状态串线
```

所以生产系统里不能只做：

```text
前端传什么 thread_id，后端就信什么。
```

正确做法是：

```text
后端生成或校验 thread_id。
后端保存 thread_id 和 actor_id 的绑定关系。
恢复前检查当前 actor_id 是否等于绑定 actor_id。
```

### 9. 什么叫生命周期

生命周期就是：

```text
一个对象从创建到消亡的全过程。
```

`thread_id` 的生命周期可以拆成：

```text
创建
绑定
使用
等待
恢复
完成
关闭
过期
清理
```

不是每个 thread 都会走完整路径。

例如：

```text
普通政策问答：创建 -> 使用 -> 完成
工单确认流程：创建 -> 使用 -> 等待确认 -> 恢复 -> 完成
用户放弃流程：创建 -> 使用 -> 等待确认 -> 过期 -> 清理
```

---

## 四、本节主题系统讲解

### 1. `thread_id` 生命周期总图

本节建议当前智能工单 Agent 的生命周期是：

```text
create
-> bind actor/session
-> active
-> waiting_confirmation
-> resume or expire
-> completed / closed
-> cleanup
```

对应状态：

```text
active
waiting_confirmation
completed
closed
expired
```

本节代码里没有把 `expired` 作为持久状态写死，而是通过：

```python
is_ticket_agent_thread_expired(...)
```

动态判断。

原因是：

```text
过期通常由 expires_at + 当前时间计算出来。
```

如果每次都额外写一个 `expired` 状态，反而要维护：

```text
expires_at 到了以后，谁负责把 status 改成 expired？
如果没改，状态是不是不可信？
```

所以本节采用：

```text
status 表示业务状态。
expires_at 表示过期时间。
is_expired 根据当前时间判断是否过期。
```

### 2. 创建阶段

创建 thread 的时机通常是：

```text
用户开始一个新的 Agent 流程。
```

比如：

```text
用户第一次发起工单。
用户点击“新建咨询”。
用户切换到新的问题。
用户之前的 thread 已经完成或过期。
```

创建时要确定：

```text
thread_id
actor_id
session_id
created_at
updated_at
expires_at
status
```

本节代码：

```python
create_ticket_agent_thread_binding(...)
```

会创建：

```text
TicketAgentThreadBinding
```

它表示：

```text
某个 thread 属于某个 actor，在某个时间创建，当前是什么状态，什么时候过期。
```

### 3. 绑定阶段

创建 `thread_id` 后，不能只把它丢给前端。

后端必须保存绑定关系：

```text
thread_id -> actor_id
thread_id -> session_id
thread_id -> status
thread_id -> expires_at
```

绑定的意义是：

```text
以后恢复时能检查这个 thread 是不是当前用户的。
```

如果没有绑定，系统就无法判断：

```text
这个 thread_id 到底是谁的？
```

本节代码中的绑定对象：

```python
TicketAgentThreadBinding
```

包含：

```text
thread_id
actor_id
session_id
status
created_at
updated_at
expires_at
ticket_id
pending_confirmation_id
```

这里暂时是内存对象和测试模型，不是数据库表。

后续如果做生产存储，可以把它变成：

```text
agent_threads 表
```

### 4. active 阶段

`active` 表示：

```text
thread 正在正常进行，还没有进入待确认、完成或关闭状态。
```

例如用户刚发起请求，Agent 正在处理：

```text
规范化输入
识别意图
检索 RAG
查询订单
提取工单字段
```

这个阶段可以继续使用同一个 `thread_id`。

但是恢复前仍然要检查：

```text
actor_id 是否匹配
是否过期
是否已经完成或关闭
```

### 5. waiting_confirmation 阶段

`waiting_confirmation` 表示：

```text
Agent 已经准备好一个需要用户确认的动作，正在等待用户决定。
```

当前项目里典型场景是：

```text
创建工单前，等待用户确认。
```

进入这个状态时，需要记录：

```text
pending_confirmation_id
updated_at
expires_at
```

为什么等待确认要缩短 TTL？

因为确认是敏感动作前的门。

例如：

```text
用户 3 天前确认页面没关。
3 天后误点确认。
系统直接创建工单。
```

这不合理。

所以等待确认状态应该有更短的过期时间。

本节默认：

```text
普通 thread TTL：24 小时
等待确认 TTL：30 分钟
```

这不是绝对标准，而是教学阶段的保守示例。

真实业务要结合风险调整。

### 6. resume 恢复阶段

恢复不是简单地：

```text
拿到 thread_id 就继续。
```

恢复前应该做决策：

```text
当前 actor 是否是 thread 绑定的 actor？
thread 是否过期？
thread 是否已经 completed？
thread 是否已经 closed？
如果都没问题，是否允许 resume_existing？
```

本节代码：

```python
evaluate_ticket_agent_thread_resume(...)
```

返回：

```text
allowed
reason
action
```

例如：

```text
allowed=True
reason=ok
action=resume_existing
```

表示可以继续旧 thread。

如果 actor 不匹配：

```text
allowed=False
reason=actor_mismatch
action=reject
```

这里用 `reject`，不是 `start_new`。

原因是：

```text
actor 不匹配是安全风险，不能悄悄开新 thread 掩盖问题。
```

如果 thread 过期：

```text
allowed=False
reason=expired
action=start_new
```

这表示可以提示用户：

```text
当前会话已过期，请重新发起。
```

然后创建新 thread。

### 7. completed 完成阶段

`completed` 表示：

```text
这条 Agent 流程已经正常完成。
```

例如：

```text
工单已经创建成功。
最终答案已经返回。
无需继续恢复旧流程。
```

完成后通常要记录：

```text
ticket_id
updated_at
status=completed
pending_confirmation_id=None
expires_at=None
```

为什么 completed 后不允许继续 resume？

因为继续旧流程可能造成：

```text
重复创建工单
重复调用工具
用户以为在问新问题，实际接着旧上下文
```

所以本节恢复决策是：

```text
completed -> start_new
```

### 8. closed 关闭阶段

`closed` 表示：

```text
这条 thread 被主动关闭。
```

可能原因：

```text
用户取消创建工单。
用户关闭会话。
客服结束处理。
管理员手动关闭。
系统发现异常后终止。
```

closed 和 completed 的区别：

```text
completed：正常完成。
closed：主动结束，不一定完成业务目标。
```

closed 后也不应该继续恢复。

### 9. expired 过期判断

过期不是一定要写入状态。

它可以由：

```text
expires_at <= now
```

计算出来。

本节代码：

```python
is_ticket_agent_thread_expired(...)
```

如果当前时间已经超过 `expires_at`，就返回 `True`。

过期后恢复决策：

```text
allowed=False
reason=expired
action=start_new
```

这表示：

```text
旧 thread 不再恢复。
用户需要重新开始。
```

第 25 节会继续讲：

```text
过期 thread 怎么清理
checkpoint 怎么删
哪些要归档
哪些要保留审计
```

### 10. thread_id 格式规则

本节对 `thread_id` 做了更严格的校验：

```text
不能为空
不能超过 255 个字符
只能包含字母、数字、下划线、短横线和点
必须以字母或数字开头
```

为什么要限制 255？

因为生产持久化时，某些 checkpointer 的 `thread_id` 字段长度有限。官方文档也提醒使用 PostgresSaver 时要控制 `thread_id` 长度。

为什么不允许 `/`、`\`、`..`？

因为这些字符容易和路径、URL、日志解析、文件名、数据库 key 混在一起。

即使最终存 Postgres，不存文件，也没有必要让 `thread_id` 变成复杂字符串。

好的 `thread_id` 应该：

```text
短
稳定
不含敏感信息
不含路径符号
不直接暴露业务数据
方便存储和查询
```

本节生成的格式类似：

```text
ticket-thread-<uuid hex>
```

例如：

```text
ticket-thread-2f4a7b0d9b1c4b3a94fd8f2e31b6d91a
```

### 11. 前端生成还是后端生成

推荐：

```text
后端生成 thread_id。
```

原因：

```text
后端可以保证格式。
后端可以绑定 actor_id。
后端可以控制生命周期。
后端可以防止用户伪造别人的 thread。
后端可以决定是否复用旧 thread。
```

前端可以保存：

```text
当前 thread_id
```

用于后续请求继续同一条流程。

但前端不应该拥有最终决定权。

前端传回来的 `thread_id` 应该被后端当成：

```text
待验证的恢复线索
```

而不是：

```text
可信事实
```

### 12. 一个用户多个会话怎么处理

一个用户可以同时有多个 thread。

例如：

```text
用户 A：
  thread 1：问退款政策
  thread 2：投诉订单 1001
  thread 3：查询订单 1002
```

前端可以展示多个会话入口。

后端要保存：

```text
thread_id
actor_id
session_id
status
updated_at
```

恢复时根据：

```text
用户点击哪个会话
传回哪个 thread_id
当前登录 actor_id 是否匹配
thread 是否过期或关闭
```

决定是否恢复。

### 13. 刷新页面怎么处理

刷新页面通常不应该丢失当前 thread。

常见做法：

```text
前端本地保存当前 thread_id。
刷新后带上 thread_id 请求后端。
后端验证 actor_id 和生命周期。
允许则恢复。
不允许则开新 thread 或提示过期。
```

注意：

```text
刷新恢复是用户体验问题。
恢复校验是安全问题。
```

不能为了体验跳过校验。

### 14. 用户关闭浏览器再回来怎么处理

这要看业务规则。

如果是普通咨询：

```text
24 小时内可以恢复。
```

如果是写操作确认：

```text
30 分钟内可以恢复。
```

如果超过时间：

```text
让用户重新发起。
```

不要让高风险确认长期有效。

### 15. thread_id 和权限安全

`thread_id` 本身不是权限。

它只是一个 ID。

真正的安全要靠：

```text
当前登录用户 actor_id
thread 绑定 actor_id
恢复时校验 actor_id
工具调用权限校验
写操作用户确认
过期判断
```

所以不能说：

```text
用户知道 thread_id，就允许恢复。
```

应该说：

```text
用户知道 thread_id，并且当前身份和绑定身份一致，并且 thread 没过期没结束，才允许恢复。
```

---

## 五、本节代码改动讲解

本节新增：

```text
projects/ai-service/app/agents/thread_lifecycle.py
projects/ai-service/tests/test_ticket_agent_thread_lifecycle.py
```

并轻微修改：

```text
projects/ai-service/app/agents/ticket_agent.py
```

### 1. `thread_lifecycle.py` 的定位

这个文件不直接调用大模型，也不直接调用 LangGraph。

它只负责：

```text
thread_id 生命周期规则。
```

好处是：

```text
规则集中。
容易测试。
不污染 ticket_agent.py。
以后接数据库表时可以复用。
```

### 2. `normalize_ticket_agent_thread_id`

作用：

```text
校验并标准化 thread_id。
```

它会：

```text
去掉前后空格
拒绝空字符串
拒绝超过 255 字符
拒绝不安全字符
```

为什么这段代码值得学？

因为生产系统的 ID 不能只检查“非空”。

后续要进入：

```text
数据库
文件快照
日志
URL
监控系统
```

越早限制格式，后续越少踩坑。

### 3. `generate_ticket_agent_thread_id`

作用：

```text
生成一个安全的新 thread_id。
```

格式：

```text
ticket-thread- + uuid4().hex
```

这里用随机 UUID，而不是把用户 ID、订单号拼进去。

原因是：

```text
thread_id 不应该暴露用户或业务敏感信息。
thread_id 不应该容易被猜到。
thread_id 应该足够唯一。
```

### 4. `TicketAgentThreadBinding`

作用：

```text
记录 thread 和操作者、状态、时间之间的绑定关系。
```

核心字段：

```text
thread_id
actor_id
session_id
status
created_at
updated_at
expires_at
ticket_id
pending_confirmation_id
```

它不是数据库表，但已经很接近未来表结构。

未来如果落库，可能变成：

```text
agent_threads
```

字段大概也是这些。

### 5. `create_ticket_agent_thread_binding`

作用：

```text
创建一个 active 状态的新 thread 绑定。
```

默认 TTL：

```text
24 小时
```

适合普通 Agent 会话。

### 6. `mark_ticket_agent_thread_waiting_confirmation`

作用：

```text
把 thread 从 active 改成 waiting_confirmation。
```

它会记录：

```text
pending_confirmation_id
updated_at
expires_at
```

默认确认 TTL：

```text
30 分钟
```

这体现了一个重要思想：

```text
写操作确认状态应该比普通会话更短。
```

### 7. `complete_ticket_agent_thread`

作用：

```text
把 thread 标记为 completed。
```

创建工单成功后，可以记录：

```text
ticket_id
```

并清掉：

```text
pending_confirmation_id
expires_at
```

完成后不应该再恢复旧流程。

### 8. `close_ticket_agent_thread`

作用：

```text
主动关闭 thread。
```

例如用户取消、客服关闭、系统终止。

closed 和 completed 都不允许继续恢复。

### 9. `is_ticket_agent_thread_expired`

作用：

```text
判断当前时间是否已经超过 expires_at。
```

这个函数把“是否过期”作为计算结果，而不是必须写进 status。

这让规则更清晰：

```text
status 是业务状态。
expires_at 是生命周期时间。
expired 是根据当前时间计算出来的事实。
```

### 10. `evaluate_ticket_agent_thread_resume`

作用：

```text
判断当前请求能不能恢复某个 thread。
```

决策表：

| 情况 | allowed | reason | action |
| --- | --- | --- | --- |
| actor 匹配，未过期，未完成，未关闭 | true | ok | resume_existing |
| actor 不匹配 | false | actor_mismatch | reject |
| 已过期 | false | expired | start_new |
| 已完成 | false | completed | start_new |
| 已关闭 | false | closed | start_new |

这个表非常重要。

它能避免系统变成：

```text
只要有 thread_id 就继续执行。
```

### 11. `ticket_agent.py` 的改动

原来的：

```python
def build_ticket_agent_thread_config(thread_id: str) -> dict[str, Any]:
    normalized_thread_id = thread_id.strip()
    if not normalized_thread_id:
        raise ValueError("thread_id 不能为空。")

    return {"configurable": {"thread_id": normalized_thread_id}}
```

现在改成：

```python
def build_ticket_agent_thread_config(thread_id: str) -> dict[str, Any]:
    return {
        "configurable": {
            "thread_id": normalize_ticket_agent_thread_id(thread_id),
        }
    }
```

意义是：

```text
所有进入 LangGraph config 的 thread_id 都走同一套生命周期校验。
```

现在不仅拒绝空值，也拒绝：

```text
过长 ID
带路径符号的 ID
不安全格式
```

---

## 六、测试怎么证明这节做对了

本节新增测试：

```text
projects/ai-service/tests/test_ticket_agent_thread_lifecycle.py
```

重点验证：

```text
生成的 thread_id 有安全前缀和安全长度。
normalize 会去掉空格并拒绝空值、不安全字符、过长 ID。
build_ticket_agent_thread_config 会复用生命周期校验。
创建 thread 绑定时会设置 actor、session、status、created_at、updated_at、expires_at。
进入 waiting_confirmation 会缩短 TTL 并记录 pending_confirmation_id。
同 actor 未过期可以恢复。
不同 actor 会被 reject。
过期 thread 要 start_new。
completed / closed thread 不允许 resume。
metadata 是 JSON friendly。
naive datetime 会按 UTC 处理。
```

相关回归测试：

```text
test_ticket_agent_intent.py
test_ticket_agent_checkpoint_store.py
```

用来确认：

```text
更严格的 thread_id 校验没有破坏已有 checkpoint 和 interrupt 流程。
```

---

## 七、当前项目的推荐生命周期设计

当前智能工单 Agent 推荐设计：

### 1. 创建

后端生成：

```text
ticket-thread-<uuid>
```

并保存绑定：

```text
thread_id
actor_id
session_id
status=active
created_at
updated_at
expires_at
```

### 2. 普通执行

所有 graph 调用都带：

```python
{"configurable": {"thread_id": thread_id}}
```

并且每次都校验：

```text
thread_id 格式
actor_id 归属
status
expires_at
```

### 3. 等待确认

当进入创建工单确认：

```text
status=waiting_confirmation
pending_confirmation_id=...
expires_at=now + 30 分钟
```

### 4. 用户确认

恢复前检查：

```text
actor_id 匹配
未过期
status=waiting_confirmation 或 active
pending_confirmation_id 匹配
```

然后再执行：

```text
resume interrupt
创建工单
```

### 5. 创建成功

创建成功后：

```text
status=completed
ticket_id=T1001
pending_confirmation_id=None
expires_at=None
```

### 6. 用户取消

用户取消后：

```text
status=closed
pending_confirmation_id=None
expires_at=None
```

也可以保留审计记录。

### 7. 过期

过期后：

```text
不恢复旧 thread。
提示用户重新发起。
必要时创建新 thread。
```

第 25 节会讲：

```text
怎么定期清理过期 thread 和 checkpoint。
```

---

## 八、常见错误

### 错误 1：把 user_id 当 thread_id

问题：

```text
一个用户多个问题会混在一起。
```

正确做法：

```text
user_id / actor_id 负责归属。
thread_id 负责某一条 Agent 流程。
```

### 错误 2：把 trace_id 当 thread_id

问题：

```text
trace_id 通常每次请求都不同，无法表示一段可恢复流程。
```

正确做法：

```text
trace_id 用于日志追踪。
thread_id 用于 checkpoint 恢复。
```

### 错误 3：前端传什么 thread_id 后端就信什么

问题：

```text
可能越权恢复别人的 thread。
```

正确做法：

```text
后端校验 thread_id 格式、绑定 actor、状态和过期时间。
```

### 错误 4：已完成流程还允许继续恢复

问题：

```text
可能重复调用写操作。
```

正确做法：

```text
completed / closed thread 不允许 resume。
```

### 错误 5：确认状态永不过期

问题：

```text
用户很久以后误点确认，系统还执行写操作。
```

正确做法：

```text
waiting_confirmation 使用更短 TTL。
```

### 错误 6：thread_id 太长或包含不安全字符

问题：

```text
进数据库、日志、文件、URL 时容易出问题。
```

正确做法：

```text
控制长度，限制字符集，后端统一生成。
```

---

## 九、面试和工作中怎么讲

### 1. 30 秒版本

```text
thread_id 是 LangGraph checkpointer 保存和恢复某条执行线程的 key，不等于 user_id、session_id、trace_id 或 ticket_id。生产里不能只相信前端传入的 thread_id，后端要生成或校验 thread_id，并保存它和 actor_id、session_id、status、expires_at 的绑定关系。恢复前要检查归属、状态和过期时间，completed、closed、expired 或 actor 不匹配的 thread 都不能直接恢复。
```

### 2. 1 分钟版本

```text
我会把 thread_id 当成 Agent 流程生命周期对象，而不是普通字符串。创建新流程时后端生成 ticket-thread-UUID，并绑定 actor_id、session_id、created_at、updated_at、expires_at 和 status。普通流程是 active，进入用户确认时变成 waiting_confirmation，并把 TTL 缩短，比如 30 分钟。用户确认恢复时，不是拿 thread_id 就直接 resume，而是先判断 actor 是否匹配、thread 是否过期、是否已经 completed 或 closed。通过这些规则可以避免串线、越权恢复和重复写操作。
```

### 3. 3 分钟版本

```text
LangGraph 的 thread_id 是 checkpointer 保存和读取 checkpoint 的关键。它标识的是一条 graph 执行线，而不是一次请求，也不是一个用户。trace_id 用于一次调用链路追踪，user_id/actor_id 用于身份归属，session_id 用于客户端会话，ticket_id 是工单创建成功后的业务 ID。thread_id 需要单独设计生命周期。

在智能工单 Agent 里，我会让后端生成 thread_id，例如 ticket-thread-uuid，并创建 thread binding，记录 thread_id、actor_id、session_id、status、created_at、updated_at、expires_at、pending_confirmation_id、ticket_id。active 状态表示流程进行中；waiting_confirmation 表示等待用户确认写操作，这个状态要有更短 TTL；completed 表示流程正常完成，closed 表示主动关闭。过期不一定写成状态，而是通过 expires_at 和当前时间判断。

恢复时必须先做决策：actor_id 不匹配直接 reject；过期、completed、closed 都不继续旧 thread，而是提示用户重新开始或创建新 thread；只有 actor 匹配、未过期、未完成、未关闭时，才允许 resume_existing。这样可以避免用户伪造 thread_id 恢复别人的流程，也能防止已完成流程重复执行写操作。
```

---

## 十、本节练习

### 练习 1：区分几个 ID

问题：

```text
请分别说明 thread_id、trace_id、actor_id、session_id、ticket_id 的作用。
```

参考答案：

```text
thread_id 标识一条 Agent 执行线程，用于 checkpoint 保存和恢复。
trace_id 标识一次请求链路，用于日志追踪。
actor_id 标识当前操作者，用于权限和归属校验。
session_id 标识客户端或登录会话，偏前端/认证。
ticket_id 是工单创建成功后的业务 ID。
```

### 练习 2：判断是否能恢复

问题：

```text
thread 绑定 actor_id=demo_user_001，当前请求 actor_id=other_user，thread_id 正确且未过期，能恢复吗？
```

参考答案：

```text
不能恢复。actor_id 不匹配是安全风险，应该 reject，而不是 start_new 或 resume_existing。因为这可能是用户试图恢复别人的 thread。
```

### 练习 3：等待确认为什么要短 TTL

问题：

```text
为什么 waiting_confirmation 的 TTL 应该比普通 active 会话更短？
```

参考答案：

```text
因为 waiting_confirmation 通常表示写操作前的确认状态，例如创建工单。确认状态如果长期有效，用户很久以后误点或页面被别人使用，都可能触发过期的写操作。缩短 TTL 可以降低误操作和安全风险。
```

### 练习 4：completed thread 是否能继续 resume

问题：

```text
一个 thread 已经 completed，并且已经生成 ticket_id=T1001。用户又带着这个 thread_id 发起确认请求，应该继续恢复吗？
```

参考答案：

```text
不应该。completed 表示流程已经完成，继续恢复可能重复创建工单或重复执行工具。正确做法是拒绝恢复旧流程，并根据业务提示用户已完成或创建新 thread。
```

### 练习 5：为什么不建议 thread_id 包含订单号

问题：

```text
为什么不建议生成 thread_id="ticket-thread-order-1001-user-panpan"？
```

参考答案：

```text
因为 thread_id 可能进入日志、URL、数据库和前端状态，包含订单号或用户名会暴露业务信息，也让 ID 更容易被猜测。更好的做法是使用随机 UUID，业务信息放在受控的 state 或数据库字段里。
```

### 练习 6：刷新页面后怎么恢复

问题：

```text
用户刷新页面后，前端带回旧 thread_id，后端应该检查什么？
```

参考答案：

```text
后端应该检查 thread_id 格式是否合法、是否存在绑定记录、绑定 actor_id 是否等于当前登录用户、thread 是否过期、status 是否允许恢复。如果都通过，才允许恢复旧 thread；否则提示过期、拒绝越权或创建新 thread。
```

---

## 十一、自测问题

### 自测 1：thread_id 是不是用户 ID？

参考答案：

```text
不是。thread_id 标识一条 Agent 执行流程，用户 ID 标识操作者。一个用户可以有多个 thread，一个 thread 应该绑定一个 actor_id 用于恢复时校验归属。
```

### 自测 2：为什么 thread_id 不能用 trace_id 代替？

参考答案：

```text
trace_id 通常表示一次请求链路，每次请求可能都不同；thread_id 表示一段可恢复的 Agent 流程，多个请求可以属于同一个 thread。用 trace_id 代替 thread_id 会导致无法恢复同一条流程。
```

### 自测 3：恢复 thread 前最重要的三个检查是什么？

参考答案：

```text
检查 actor_id 是否匹配，检查 thread 是否过期，检查 status 是否允许恢复。对于写操作确认，还要检查 pending_confirmation_id 是否匹配。
```

### 自测 4：为什么 actor 不匹配时 action 是 reject，而不是 start_new？

参考答案：

```text
actor 不匹配可能表示越权访问或错误串线。如果悄悄 start_new，会掩盖安全问题。正确做法是拒绝，并记录安全相关日志。
```

### 自测 5：为什么过期可以 start_new？

参考答案：

```text
过期通常不是越权，而是生命周期结束。旧 thread 不再安全或不再适合恢复，但用户可以重新发起一个新的流程，所以 action 可以是 start_new。
```

### 自测 6：本节代码为什么使用不可变 dataclass？

参考答案：

```text
TicketAgentThreadBinding 使用 frozen=True，表示创建后不直接修改原对象。状态变化通过 replace 返回新对象，这样更容易测试，也能减少“某处偷偷改了状态”的问题。
```

### 自测 7：下一节为什么要学会话过期与清理？

参考答案：

```text
本节只是能判断一个 thread 是否过期，但过期数据还会留在 checkpoint store 或数据库里。下一节要继续学习怎么清理旧 checkpoint、怎么设计 retention、哪些数据要删除、哪些要保留审计。
```

---

## 十二、本节总结

本节你要真正掌握：

```text
thread_id 是 LangGraph checkpoint 恢复的关键 key。
thread_id 不等于 trace_id、actor_id、session_id 或 ticket_id。
生产系统要后端生成或严格校验 thread_id。
thread_id 必须绑定 actor_id，恢复前必须校验归属。
active、waiting_confirmation、completed、closed、expired 各有明确含义。
等待确认状态应该有更短 TTL。
completed / closed / expired thread 不应该继续恢复。
actor 不匹配要 reject。
thread_id 格式要控制长度和字符集，避免进入 Postgres、文件、URL、日志时出问题。
```

本节代码完成：

```text
生成安全 thread_id。
创建 thread 绑定。
等待确认状态转换。
完成和关闭状态转换。
过期判断。
恢复决策。
build_ticket_agent_thread_config 复用统一 thread_id 校验。
```

下一节：

```text
阶段 6 第 25 节：会话过期与清理
```

下一节会在本节基础上继续讲：

```text
过期 thread 怎么清理
checkpoint 历史怎么保留
确认状态过期后怎么提示
哪些数据需要删除
哪些数据需要保留审计
清理任务怎么设计
```
