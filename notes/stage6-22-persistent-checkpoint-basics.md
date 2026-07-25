# 阶段 6 第 22 节：持久化 checkpoint 基础

本节目标：理解为什么 `MemorySaver` 不适合生产环境，并在当前智能工单 Agent 里实现一个最小但完整的“文件型 checkpoint 快照”能力。

这里的“最小”不是“随便写一点”，而是只解决本节真正要解决的问题：

```text
把某个 thread_id 对应的 LangGraph 线程状态，从内存里拿出来，保存成可长期存在的 UTF-8 JSON 文件。
```

本节暂时不做这些内容：

```text
不直接上 SQLite / Postgres / Redis。
不设计 checkpoint 过期清理。
不做多实例并发锁。
不把文件型快照伪装成完整生产方案。
不替换 LangGraph 内部官方 checkpointer。
```

原因很简单：如果你还没看懂“checkpoint 到底存什么、为什么要能跨进程保存、保存时有什么安全边界”，直接讲数据库选型会变成背名词。

---

## 一、本节在主线里的位置

阶段 5 第 21 节我们学过：

```text
checkpoint + thread_id
```

当时我们做的是：

```text
用户发起工单
-> LangGraph 执行到用户确认节点
-> MemorySaver 记住当前线程状态
-> 后续用同一个 thread_id 恢复
-> 确认后继续创建工单
```

第 22 节不是推翻之前的内容，而是补生产化问题：

```text
如果服务重启了呢？
如果 Python 进程崩了呢？
如果部署了多个 ai-service 实例呢？
如果用户确认动作发生在几分钟后、几小时后呢？
```

`MemorySaver` 只能解决“当前 Python 进程还活着时”的恢复问题。生产环境需要状态能离开进程，进入文件、数据库、Redis、对象存储或其他稳定存储。

所以第 22 节开始进入：

```text
从内存 checkpoint
到持久化 checkpoint
```

---

## 二、基础知识铺垫

### 1. 什么是 checkpoint

checkpoint 可以先理解成：

```text
程序执行到某个关键位置时，把当前状态保存下来。
```

类似你玩游戏时的存档。

游戏存档里可能有：

```text
角色位置
血量
背包
任务进度
地图状态
```

Agent checkpoint 里可能有：

```text
用户原始问题
规范化后的问题
已识别出的意图
已经走过的节点
待确认的工单字段
工具调用结果
错误信息
下一步应该从哪个节点继续
```

没有 checkpoint 的 Agent 更像“一次性脚本”：

```text
从头跑到尾
中间断了就没了
下次只能重新开始
```

有 checkpoint 的 Agent 才能做到：

```text
暂停
恢复
人工确认
多轮继续
失败后排查
流程审计
```

### 2. checkpoint 和 state 的关系

`state` 是当前那一刻的状态。

`checkpoint` 是把某一刻的 `state` 保存下来形成的记录。

可以这样理解：

```text
state：内存里的当前状态
checkpoint：保存下来的状态快照
```

举个智能工单 Agent 的例子：

```python
{
    "user_message": "我要投诉订单 1001，物流一直不动",
    "intent": "ticket_request",
    "ticket_fields": {
        "issue_type": "complaint",
        "order_id": "1001",
        "urgency": "high"
    },
    "pending_ticket_confirmation": {
        "status": "pending",
        "confirmation_id": "..."
    },
    "node_history": [
        "normalize_user_input",
        "classify_intent",
        "decide_ticket_need",
        "extract_ticket_fields",
        "request_ticket_confirmation"
    ]
}
```

这就是一个可以保存的状态。

保存以后，它就变成了 checkpoint 快照。

### 3. thread_id 是什么

`thread_id` 是 LangGraph 用来区分不同会话、不同执行线的 ID。

同一个图可以服务很多用户：

```text
用户 A 的工单流程
用户 B 的工单流程
用户 C 的工单流程
```

这些流程不能混在一起。

所以要有：

```text
thread_id = ticket-thread-A
thread_id = ticket-thread-B
thread_id = ticket-thread-C
```

当你调用：

```python
graph.invoke(state, config={"configurable": {"thread_id": "ticket-thread-A"}})
```

LangGraph 就知道：

```text
这次执行属于 ticket-thread-A。
```

后续你再用同一个 `thread_id`：

```python
graph.get_state({"configurable": {"thread_id": "ticket-thread-A"}})
```

它就能拿到这条执行线保存过的状态。

### 4. MemorySaver 是什么

`MemorySaver` 是 LangGraph 提供的一个内存型 checkpointer。

它的特点是：

```text
保存快
配置简单
适合学习
适合单元测试
适合本地 demo
```

但是它的状态存在 Python 进程内存里。

这意味着：

```text
Python 服务重启，状态没了。
进程崩溃，状态没了。
部署两个 Python 实例，A 实例里的状态 B 实例看不到。
容器重建，状态没了。
```

所以它不是生产级持久化方案。

### 5. 什么是持久化

持久化就是：

```text
把数据从易失性存储，保存到更稳定的存储里。
```

易失性存储：

```text
内存
进程里的变量
Python 对象
```

更稳定的存储：

```text
文件
SQLite
Postgres
MySQL
Redis
对象存储
专用 checkpoint store
```

持久化的核心意义不是“看起来更高级”，而是：

```text
程序退出后，数据还在。
服务重启后，能找回状态。
不同请求之间，能共享同一份状态。
出了问题以后，能检查保存过什么。
```

### 6. 为什么本节先用文件，不直接用数据库

文件不是最终生产答案，但它很适合学习第一步。

因为文件能让你直观看到：

```text
到底保存了什么字段
JSON 长什么样
thread_id 怎么变成文件名
中文会不会正确写入
读取时怎么校验
哪些对象不能保存成 JSON
```

数据库选型会放到下一节。

如果这一节直接上 Postgres，你可能会被连接串、表结构、事务、迁移、索引、连接池分散注意力，反而看不清 checkpoint 的本质。

### 7. snapshot 是什么

snapshot 是快照。

它表示：

```text
某一个时间点的数据副本。
```

本节实现的是：

```text
TicketAgentCheckpointSnapshot
```

它不是 LangGraph 内部完整 checkpoint 的全部格式，而是我们项目应用层的一份状态快照。

它主要包含：

```text
schema_version：快照格式版本
thread_id：这份快照属于哪个会话
saved_at：保存时间
metadata：额外说明
values：真正的 Agent state
```

为什么要加 `schema_version`？

因为以后文件格式可能变化。

比如现在保存：

```text
values
metadata
saved_at
```

以后可能要保存：

```text
next node
parent checkpoint id
checkpoint namespace
过期时间
用户 ID
```

没有版本号，旧文件和新代码之间就容易混乱。

### 8. JSON 序列化是什么

序列化就是：

```text
把程序里的对象变成可以保存或传输的格式。
```

Python dict 在内存里是 Python 对象。

JSON 是文本格式。

保存到文件之前，需要：

```python
json.dumps(data)
```

从文件读回来，需要：

```python
json.loads(text)
```

但不是所有 Python 对象都能变成 JSON。

可以自然变成 JSON 的类型：

```text
dict
list
str
int
float
bool
None
```

不能直接变成 JSON 的类型：

```text
object()
文件句柄
数据库连接
函数
类实例
datetime 对象
LangGraph 的某些运行时对象
```

所以本节代码里会明确捕获 `TypeError`，如果 `values` 里混入不能写 JSON 的对象，就返回项目自己的 `AppException`。

### 9. 为什么文件名不能直接用 thread_id

假设用户传入：

```text
../secret
```

如果你直接把它当文件名：

```text
checkpoints/../secret.json
```

路径可能逃出 checkpoint 目录。

这类问题叫：

```text
path traversal
路径穿越
```

本节实现里不会直接使用原始 `thread_id` 做文件名，而是做两件事：

```text
1. 把不安全字符替换成 _
2. 追加原始 thread_id 的 sha256 摘要前 12 位
```

这样既能保留一点可读性，又能降低冲突风险。

例如：

```text
../ticket/thread:001
```

会变成类似：

```text
ticket_thread_001-xxxxxxxxxxxx.json
```

其中后面的摘要来自原始 `thread_id`。

### 10. 为什么读取时还要校验文件内容里的 thread_id

文件名安全不代表文件内容一定正确。

文件可能被：

```text
手工改错
脚本写错
复制错
未来迁移程序处理错
```

所以读取 checkpoint 时不能只相信文件路径，还要看文件内容：

```text
我要读 ticket-thread-001
文件内容里也必须是 ticket-thread-001
```

如果文件内容写的是另一个 thread，就要拒绝读取。

这是生产化里很重要的习惯：

```text
持久化数据要自描述，也要可校验。
```

---

## 三、本节主题系统讲解

### 1. 当前项目之前的 checkpoint 链路

第 21 节之前，我们的链路是：

```text
build_checkpointed_ticket_agent_graph()
-> build_ticket_agent_graph(..., checkpointer=MemorySaver())
-> run_ticket_agent_in_thread(..., thread_id=...)
-> graph.invoke(..., config={"configurable": {"thread_id": thread_id}})
-> get_ticket_agent_thread_state(...)
```

这说明当前项目已经具备：

```text
按 thread_id 保存状态
按 thread_id 读取状态
同一个 graph 内恢复执行
不同 thread_id 状态隔离
```

但是保存位置仍然是：

```text
MemorySaver 内存
```

所以服务重启后不能恢复。

### 2. 本节新增的持久化链路

本节新增的是应用层快照链路：

```text
LangGraph MemorySaver 里的当前 state
-> get_ticket_agent_thread_state(graph, thread_id=...)
-> TicketAgentCheckpointSnapshot.create(...)
-> FileTicketAgentCheckpointStore.save(...)
-> UTF-8 JSON 文件
```

读取链路是：

```text
thread_id
-> FileTicketAgentCheckpointStore.load(thread_id)
-> 找到对应 JSON 文件
-> 校验 schema_version
-> 校验 thread_id
-> 校验 values 是 dict
-> 返回 TicketAgentCheckpointSnapshot
```

这条链路让我们第一次把 Agent 状态从内存移动到了磁盘。

### 3. 一份 checkpoint JSON 真实长什么样

假设用户发起了这样一句话：

```text
我要投诉订单 1001，物流一直不动
```

Agent 执行到“请求用户确认创建工单”这一步时，状态里已经有了：

```text
用户原始输入
意图识别结果
工单字段
待确认信息
节点执行历史
写操作安全状态
```

这时如果调用：

```python
save_ticket_agent_checkpoint_snapshot(
    graph,
    thread_id="ticket-thread-persist-001",
    store=store,
    metadata={"checkpoint_kind": "pending_confirmation"},
)
```

落盘后的 JSON 会接近下面这样。

注意：实际字段会随着项目 state 继续演进而变化，下面是为了学习而整理过的示例，但结构和本节实现是一致的。

```json
{
  "metadata": {
    "checkpoint_kind": "pending_confirmation"
  },
  "saved_at": "2026-07-25T08:20:30.123456+00:00",
  "schema_version": "ticket-agent-checkpoint-snapshot:v1",
  "thread_id": "ticket-thread-persist-001",
  "values": {
    "agent_trace_id": "trace-demo-001",
    "user_message": "我要投诉订单 1001，物流一直不动",
    "normalized_message": "我要投诉订单 1001，物流一直不动",
    "intent": "ticket_request",
    "needs_ticket": true,
    "ticket_need_source": "explicit_user_request",
    "ticket_actor_id": "demo_user_001",
    "ticket_fields": {
      "issue_type": "complaint",
      "order_id": "1001",
      "description": "我要投诉订单 1001，物流一直不动",
      "user_request": "投诉处理",
      "urgency": "high",
      "need_human_review": true
    },
    "ticket_fields_complete": true,
    "ticket_confirmation_required": true,
    "pending_ticket_confirmation": {
      "confirmation_id": "ticket-confirmation-1001",
      "status": "pending",
      "message": "确认创建工单：订单 1001，问题类型 complaint，紧急程度 high。",
      "ticket_fields": {
        "issue_type": "complaint",
        "order_id": "1001",
        "description": "我要投诉订单 1001，物流一直不动",
        "user_request": "投诉处理",
        "urgency": "high",
        "need_human_review": true
      }
    },
    "ticket_tool_name": "create_ticket",
    "ticket_tool_access_level": "write",
    "ticket_tool_requires_confirmation": true,
    "ticket_write_safety_status": "confirmation_required",
    "node_history": [
      "normalize_user_input",
      "classify_intent",
      "decide_ticket_need",
      "extract_ticket_fields",
      "request_ticket_confirmation"
    ]
  }
}
```

这份 JSON 可以分成两层看。

第一层是 checkpoint 快照自己的信息：

```text
schema_version
thread_id
saved_at
metadata
values
```

第二层是 Agent 真正的业务状态：

```text
values.user_message
values.intent
values.ticket_fields
values.pending_ticket_confirmation
values.node_history
values.ticket_write_safety_status
```

你要特别注意：

```text
checkpoint 文件不是只存最终答案。
```

它保存的是“流程能继续所需的状态”。

比如当前状态里没有：

```text
created_ticket
ticket_creation_status
```

这是合理的。

因为流程还停在：

```text
等待用户确认
```

还没有真正执行创建工单。

所以 checkpoint 的价值就在这里：

```text
它告诉系统：这个 thread 不是结束了，而是停在了等待确认的位置。
```

### 4. 怎么从 JSON 反推 Agent 现在走到哪一步

拿到上面的 JSON，你可以不看代码，先从几个字段判断当前流程状态。

#### 看 `node_history`

```json
"node_history": [
  "normalize_user_input",
  "classify_intent",
  "decide_ticket_need",
  "extract_ticket_fields",
  "request_ticket_confirmation"
]
```

这说明流程已经走过：

```text
输入规范化
意图识别
判断是否需要工单
提取工单字段
请求用户确认
```

最后一个节点是：

```text
request_ticket_confirmation
```

所以你可以判断：

```text
Agent 当前已经准备好工单字段，正在等用户确认。
```

#### 看 `pending_ticket_confirmation`

```json
"pending_ticket_confirmation": {
  "confirmation_id": "ticket-confirmation-1001",
  "status": "pending"
}
```

这说明：

```text
当前确实有一个待确认动作。
```

如果这个字段不存在，或者是 `null`，就不能直接执行确认恢复。

#### 看 `ticket_write_safety_status`

```json
"ticket_write_safety_status": "confirmation_required"
```

这说明：

```text
写操作还没有获得最终确认。
```

当前正确动作不是直接调用 Java 创建工单，而是等待用户明确确认。

#### 看 `created_ticket`

示例里没有这个字段。

这说明：

```text
还没有调用 create_ticket。
```

如果已经创建成功，后续状态里通常会出现：

```text
created_ticket
ticket_creation_status = "created"
```

这就是用 checkpoint 排查问题的思路：

```text
不是只看报错，而是看状态停在哪一步、缺了什么、下一步该不该继续。
```

### 5. 哪些内容适合放进 checkpoint，哪些不适合

适合放进 checkpoint 的内容一般有 4 类。

#### 第一类：恢复流程必须用到的状态

例如：

```text
thread_id
intent
ticket_fields
pending_ticket_confirmation
ticket_confirmation_approved
node_history
```

没有这些字段，系统就不知道：

```text
当前是谁的流程
走到了哪一步
用户之前提供过什么
是否还需要确认
下一步能不能执行写操作
```

#### 第二类：排查问题需要的低风险信息

例如：

```text
agent_trace_id
ticket_need_source
order_query_status
order_query_error_kind
fallback_used
agent_error_code
```

这些字段对排查很有用。

比如线上用户说：

```text
我明明提供了订单号，为什么还问我要订单号？
```

你可以看 checkpoint 里：

```text
normalized_message 有没有订单号
ticket_fields.order_id 有没有提取出来
order_query_status 是 succeeded 还是 missing_order_id
node_history 走到了哪个节点
```

#### 第三类：可以被 JSON 表示的结构化数据

例如：

```text
字符串
数字
布尔值
列表
字典
null
```

也就是 JSON friendly 数据。

#### 第四类：必要的元信息

例如：

```text
schema_version
saved_at
metadata.checkpoint_kind
```

这些不一定是 Agent 业务状态，但对管理 checkpoint 很重要。

不适合放进 checkpoint 的内容也很重要。

#### 不适合 1：运行时对象

例如：

```text
httpx.Client
数据库连接
文件句柄
函数
类实例
LangGraph 运行时对象
```

这些对象不能稳定写成 JSON，也不应该跨进程恢复。

#### 不适合 2：高敏感信息

例如：

```text
API key
身份证号
完整手机号
银行卡号
密码
访问令牌
```

如果业务确实必须保存敏感字段，也不能随便明文写进 checkpoint。

要考虑：

```text
是否必须保存
是否可以脱敏
是否需要加密
谁能读取
保留多久
删除策略是什么
```

#### 不适合 3：可以重新计算且代价很低的数据

有些字段每次都能很快算出来，不一定要存。

例如：

```text
某些临时展示文案
某些中间格式化结果
```

checkpoint 不是垃圾桶，不是所有变量都应该塞进去。

好的 state 设计应该满足：

```text
足够恢复流程
足够排查问题
尽量结构化
尽量少敏感
尽量少临时噪音
```

### 6. 为什么真实生产里还要保存“下一步位置”

本节的应用层快照主要保存：

```text
values
```

也就是 Agent state。

但完整的 LangGraph checkpoint 还会关心：

```text
下一步要执行哪个节点
当前有哪些 pending writes
每个 channel 的版本
父 checkpoint 是谁
interrupt 恢复点在哪里
```

为什么？

因为只知道 state 还不一定够恢复“执行现场”。

举个例子：

```text
用户确认前
state 里有 ticket_fields
```

但是系统还需要知道：

```text
下一步是 request_ticket_confirmation？
还是 create_ticket？
还是已经 END？
```

阶段 5 的测试里我们看过：

```python
snapshot.next
```

这个 `next` 就是 LangGraph 内部用来判断下一步位置的重要信息。

所以本节文件型快照适合学习：

```text
应用状态持久化
JSON 格式
thread_id 安全
状态观察
```

下一步进入真正生产化时，还要继续理解：

```text
完整 checkpointer 不只是保存 values。
```

这也是下一节讲存储选型时必须带着的问题。

### 7. 这是不是完整的生产级 LangGraph checkpointer

还不是。

本节实现的是：

```text
应用层 checkpoint 快照
```

它能做：

```text
保存当前 state
读取当前 state
观察 state 长什么样
验证 JSON 持久化边界
为后续数据库 checkpoint 选型打基础
```

它暂时不能完整替代 LangGraph 内部 checkpointer。

完整 LangGraph checkpointer 还要考虑：

```text
checkpoint id
checkpoint namespace
parent checkpoint
channel versions
pending writes
interrupt resume 信息
并发写入
一致性
事务
多实例共享
```

所以你以后跟别人解释时要讲清楚：

```text
本节不是把生产 checkpoint 一步做到位，而是先把“状态可持久化、格式可校验、文件可读回”的基础打通。
```

### 8. 为什么这个基础仍然很重要

因为很多工程能力都是从这个基础长出来的。

如果你能理解本节，就能继续理解：

```text
为什么要选 SQLite / Postgres / Redis
为什么 thread_id 生命周期要单独设计
为什么会话要过期清理
为什么 checkpoint 文件要有版本号
为什么敏感信息不能随便写进状态
为什么状态字段要尽量 JSON friendly
为什么多实例部署不能依赖内存
```

这比只知道 “LangGraph 有 checkpointer” 更扎实。

### 9. 本节的设计边界

本节的设计边界是：

```text
只做只读/观察型持久化快照
不在自动测试中真实调用模型
不需要启动 Java mock 服务
不需要启动 Qdrant 或 Milvus
不需要打开 VMware Ubuntu
```

也就是说，这节可以纯 Windows 本地跑。

---

## 四、本节代码改动讲解

本节新增了 3 类代码：

```text
checkpoint_store.py
ticket_agent.py 里的两个辅助函数
test_ticket_agent_checkpoint_store.py
```

### 1. `checkpoint_store.py`

文件：

```text
projects/ai-service/app/agents/checkpoint_store.py
```

这个文件专门处理 checkpoint 快照持久化，不把逻辑继续堆到 `ticket_agent.py` 里。

#### `normalize_checkpoint_thread_id`

作用：

```text
去掉 thread_id 前后空格，并拒绝空字符串。
```

为什么需要：

```text
" ticket-thread-001 " 和 "ticket-thread-001" 应该表示同一个线程。
"   " 不能作为线程 ID。
```

这里抛出的是 `AppException`，而不是随便抛一个 `RuntimeError`。

原因是：

```text
这是业务输入错误，要有稳定 error code，方便接口层、日志和测试识别。
```

#### `build_checkpoint_snapshot_filename`

作用：

```text
把 thread_id 转成安全文件名。
```

它做了两件关键事：

```text
1. 把不适合出现在文件名里的字符替换成 _
2. 追加 sha256 摘要，降低不同 thread_id 生成同名文件的风险
```

为什么要追加摘要？

因为下面两个 thread_id 清洗后可能很像：

```text
ticket/thread-001
ticket_thread-001
```

如果只替换字符，可能都变成：

```text
ticket_thread-001
```

追加摘要后，它们会变成不同文件。

#### `TicketAgentCheckpointSnapshot`

作用：

```text
表示一份可以保存的 Agent checkpoint 快照。
```

字段含义：

```text
schema_version：快照格式版本
thread_id：所属线程
values：Agent 当前 state
saved_at：保存时间
metadata：额外说明
```

这里用了 `dataclass(frozen=True)`。

你可以先这样理解：

```text
dataclass：帮我们少写初始化代码。
frozen=True：创建后不应该随便改这个对象的字段。
```

它提供了 3 个核心方法：

```text
create：创建快照，同时做 thread_id 和 values 校验
to_json_dict：转换成可以写 JSON 的 dict
from_json_dict：从 JSON dict 还原快照，并校验版本和字段
```

#### `FileTicketAgentCheckpointStore`

作用：

```text
把 TicketAgentCheckpointSnapshot 写入文件，或从文件读回来。
```

核心方法：

```text
build_path(thread_id)：根据 thread_id 得到文件路径
save(snapshot)：保存 JSON 文件
load(thread_id)：读取 JSON 文件，找不到就返回 None
```

`save` 里用：

```python
json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)
```

这里每个参数都有意义：

```text
ensure_ascii=False：中文按 UTF-8 直接保存，不转成 \uXXXX
indent=2：文件更容易人工阅读
sort_keys=True：输出顺序更稳定，方便 diff
```

`load` 里做了几个校验：

```text
文件存在才读
文件必须是合法 JSON
顶层必须是 JSON 对象
schema_version 必须匹配
values 必须是 dict
metadata 必须是 dict
文件里的 thread_id 必须和请求的 thread_id 一致
```

这些校验是本节最重要的工程习惯之一：

```text
持久化数据不能读到什么就信什么。
```

### 2. `ticket_agent.py`

文件：

```text
projects/ai-service/app/agents/ticket_agent.py
```

本节只新增两个学习相关入口，没有改动原有节点逻辑。

#### `build_ticket_agent_checkpoint_snapshot`

作用：

```text
从 LangGraph 当前 thread state 构建一份 TicketAgentCheckpointSnapshot。
```

链路是：

```text
graph + thread_id
-> get_ticket_agent_thread_state(...)
-> TicketAgentCheckpointSnapshot.create(...)
```

它不负责写文件，只负责构建快照对象。

这种拆分很重要：

```text
构建快照是一件事。
保存快照是另一件事。
```

以后如果存储从文件换成 Postgres，这个函数仍然可以复用。

#### `save_ticket_agent_checkpoint_snapshot`

作用：

```text
从图里拿当前 state，构建快照，然后交给 store 保存。
```

链路是：

```text
graph + thread_id + store
-> build_ticket_agent_checkpoint_snapshot(...)
-> store.save(snapshot)
```

注意：

```text
它不直接写死保存目录。
```

调用方传入 `store`，这样测试可以用 `tmp_path`，以后生产代码可以换真实目录或别的存储实现。

这叫：

```text
依赖注入
```

我们之前在 fake LLM、fake RAG、fake Java client 里也多次用过这种思路。

### 3. 测试文件

文件：

```text
projects/ai-service/tests/test_ticket_agent_checkpoint_store.py
```

新增测试重点覆盖：

```text
thread_id 规范化
空 thread_id 拒绝
危险 thread_id 生成安全文件名
UTF-8 JSON 保存和读取
非 JSON 对象拒绝保存
文件内容 thread_id 不匹配时拒绝读取
从 LangGraph 当前线程状态构建快照
把当前线程状态保存成文件再读回
```

测试不是本节讲解重点，但它证明：

```text
这节不是只写概念，而是能运行、能验证、能回归。
```

---

## 五、运行和验证

本节新增测试：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests/test_ticket_agent_checkpoint_store.py
```

相关回归测试：

```powershell
uv run pytest tests/test_ticket_agent_intent.py tests/test_ticket_agent_query_order_node.py tests/test_tool_registry.py
```

本节不需要：

```text
打开 VMware Ubuntu
启动 Docker
启动 Qdrant
启动 Milvus
启动 Java mock 服务
真实调用大模型
```

因为本节验证的是 Agent state 快照和文件持久化基础。

---

## 六、你应该真正掌握什么

学完本节，你不应该只会说：

```text
我会用 MemorySaver。
```

你应该能说清楚：

```text
MemorySaver 是内存型 checkpointer，适合学习和测试，但生产服务重启后状态会丢失。
checkpoint 本质是某个 thread_id 下的 Agent state 快照。
持久化 checkpoint 是把状态保存到进程外的稳定存储。
保存之前要考虑 JSON 序列化、文件名安全、schema_version、thread_id 校验和错误处理。
本节实现的是应用层文件型 checkpoint 快照，用来打通持久化基础，不是完整生产级 LangGraph checkpointer。
```

如果面试官问：

```text
为什么不能用 MemorySaver 上生产？
```

你可以回答：

```text
MemorySaver 把 checkpoint 放在 Python 进程内存里，服务重启、容器重建、进程崩溃、多实例路由切换都会导致状态不可用。生产环境需要把 checkpoint 放到进程外的持久化存储，比如 SQLite、Postgres、Redis 或官方支持的持久化 checkpointer，并且要考虑 thread_id 生命周期、并发、一致性、过期清理和敏感信息控制。
```

如果面试官问：

```text
你们项目里怎么开始做 checkpoint 持久化？
```

你可以回答：

```text
我先没有直接上数据库，而是实现了一个文件型 checkpoint snapshot store。它把 LangGraph 当前 thread_id 对应的 state 取出来，包装成带 schema_version、thread_id、saved_at、metadata、values 的 JSON 快照，并保存为 UTF-8 文件。文件名会对 thread_id 做安全清洗并追加 hash，读取时会校验 JSON 格式、版本、values 类型和文件内 thread_id。这个实现用于学习和验证持久化边界，后续再进入 SQLite、Postgres、Redis 等选型。
```

---

## 七、常见误区

### 误区 1：有 checkpoint 就等于生产可恢复

不一定。

要看 checkpoint 存在哪里。

```text
存在内存里：进程没了就没了。
存在磁盘/数据库/Redis 里：才有跨进程恢复的可能。
```

### 误区 2：保存 state 就可以不管数据结构

不对。

state 里如果混入不能 JSON 化的对象，就保存不了。

比如：

```text
函数
连接对象
文件对象
复杂运行时对象
```

所以 Agent state 应该尽量保持：

```text
JSON friendly
结构清晰
字段含义稳定
敏感字段受控
```

### 误区 3：thread_id 只是随便起个字符串

不对。

`thread_id` 会影响：

```text
状态隔离
恢复位置
用户会话归属
权限边界
过期清理
日志排查
数据存储 key
```

所以后续第 24 节会专门学习 `thread_id` 生命周期。

### 误区 4：文件型 checkpoint 可以直接当生产方案

一般不建议。

文件方案可以用于：

```text
学习
本地 demo
单机实验
问题复现
小规模内部工具
```

但生产系统通常还要考虑：

```text
并发写入
多实例共享
事务一致性
备份恢复
权限控制
容量增长
查询效率
运维监控
```

这些会进入下一节的存储选型。

---

## 八、本节练习

### 练习 1：解释 MemorySaver 的边界

问题：

```text
为什么 MemorySaver 适合学习和测试，但不适合直接上生产？
```

参考答案：

```text
MemorySaver 把 checkpoint 保存在当前 Python 进程内存里。学习和测试时它配置简单、速度快、没有外部依赖，所以很适合。但生产环境会遇到服务重启、进程崩溃、容器重建、多实例部署等情况，内存状态会丢失或无法共享，所以不适合作为生产持久化方案。
```

### 练习 2：判断哪些值适合写入 JSON checkpoint

问题：

下面哪些值适合直接写入 JSON checkpoint？

```text
1. "ticket_request"
2. {"order_id": "1001", "urgency": "high"}
3. ["normalize_user_input", "classify_intent"]
4. object()
5. 数据库连接对象
6. None
```

参考答案：

```text
适合：1、2、3、6。
不适合：4、5。

字符串、字典、列表、None 都是 JSON friendly 类型。object() 和数据库连接对象是 Python 运行时对象，不能直接序列化成 JSON，也不应该进入 checkpoint state。
```

### 练习 3：为什么文件名要做安全处理

问题：

如果直接把用户传入的 `thread_id` 当作文件名，可能有什么风险？

参考答案：

```text
可能出现路径穿越风险。例如 thread_id 是 "../secret" 时，如果代码直接拼接路径，就可能写到 checkpoint 目录之外。除此之外，不同操作系统对文件名合法字符也有限制，冒号、斜杠、反斜杠等字符可能导致路径异常。所以要把不安全字符替换掉，并且追加 hash 降低重名风险。
```

### 练习 4：解释 schema_version 的意义

问题：

为什么 checkpoint 文件里要放 `schema_version`？

参考答案：

```text
因为 checkpoint 文件格式以后可能变化。当前版本可能只保存 values、metadata、saved_at；以后可能增加 next node、过期时间、用户 ID、checkpoint id 等字段。schema_version 可以让读取代码知道当前文件属于哪个格式版本，从而拒绝不支持的旧格式或做迁移处理。
```

### 练习 5：解释本节的保存链路

问题：

用自己的话解释本节 `save_ticket_agent_checkpoint_snapshot` 的执行过程。

参考答案：

```text
它先根据 graph 和 thread_id 调用 get_ticket_agent_thread_state，拿到当前 LangGraph 线程状态。然后用 TicketAgentCheckpointSnapshot.create 把状态包装成带版本、thread_id、保存时间和 metadata 的快照对象。最后把这个快照交给 FileTicketAgentCheckpointStore.save 写成 UTF-8 JSON 文件。
```

---

## 九、自测问题

### 自测 1：checkpoint 和普通日志有什么区别？

参考答案：

```text
日志主要用于记录发生过什么，方便排查和观测；checkpoint 主要用于保存可恢复的程序状态，让流程后续能继续执行。日志通常是追加式事件记录，checkpoint 更像某一刻的状态快照。
```

### 自测 2：为什么读取 checkpoint 时要校验文件中的 thread_id？

参考答案：

```text
因为文件名和文件内容可能不一致。文件可能被手工改错、复制错或未来迁移脚本写错。如果请求读取 ticket-thread-001，但文件内容里是 ticket-thread-002，继续使用会造成会话状态串线，所以必须拒绝。
```

### 自测 3：本节的文件型快照为什么还不能叫完整生产级方案？

参考答案：

```text
因为它只保存应用层 state 快照，没有实现完整 LangGraph checkpointer 所需的 checkpoint id、parent checkpoint、channel versions、pending writes、并发控制、多实例共享和事务一致性。它适合学习、观察和打基础，不适合作为完整生产方案。
```

### 自测 4：如果 Agent state 里保存了用户手机号、身份证号或 API key，会有什么问题？

参考答案：

```text
checkpoint 是持久化数据，保存后可能长期存在。如果把敏感信息直接写进去，会带来数据泄露、合规和权限控制问题。生产环境要控制 state 字段，必要时脱敏、加密、限制访问或避免保存敏感值。
```

### 自测 5：为什么下一节要学 checkpoint 存储选型？

参考答案：

```text
因为不同存储解决的问题不一样。SQLite 适合单机轻量持久化，Postgres 适合生产多实例和事务查询，Redis 适合低延迟和 TTL，但持久性与一致性要单独评估。理解选型后，才能根据真实系统需求决定 checkpoint 应该放哪里。
```

---

## 十、本节总结

本节完成了从“内存 checkpoint”到“持久化 checkpoint 基础”的第一步。

你现在应该明白：

```text
MemorySaver 保存在线程内存里，适合学习测试，不适合生产。
持久化 checkpoint 的本质是把 Agent state 保存到进程外。
thread_id 是 checkpoint 隔离和恢复的关键。
JSON 快照要考虑 schema_version、UTF-8、序列化、文件名安全和内容校验。
本节文件型 store 是学习和验证持久化边界，不是最终生产架构。
```

下一节：

```text
阶段 6 第 23 节：checkpoint 存储选型
```

下一节会比较：

```text
MemorySaver
文件
SQLite
Postgres
Redis
```

重点不是背哪个更高级，而是学会根据：

```text
单机/多实例
是否需要事务
是否需要 TTL
恢复可靠性
查询审计
运维复杂度
```

做合理选择。
