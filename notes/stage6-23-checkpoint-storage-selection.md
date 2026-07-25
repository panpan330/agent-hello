# 阶段 6 第 23 节：checkpoint 存储选型

本节目标：学会判断 LangGraph checkpoint 应该存在哪里，而不是只记住几个存储名字。

第 22 节我们已经知道：

```text
MemorySaver / InMemorySaver 适合学习和测试。
它把 checkpoint 放在当前 Python 进程内存里。
服务重启、进程崩溃、多实例部署时，内存 checkpoint 会丢失或无法共享。
```

第 23 节要解决的问题是：

```text
如果 MemorySaver 不适合生产，那 checkpoint 应该放到哪里？
```

这节不急着安装数据库，也不急着改代码。原因是：

```text
存储选型是系统设计问题。
你先要知道每种存储解决什么问题、牺牲什么东西、适合什么阶段。
```

本节暂时不做：

```text
不安装 SQLite checkpointer。
不安装 Postgres checkpointer。
不启动 Docker。
不改 LangGraph 编译方式。
不做会话过期清理。
不做 thread_id 生命周期设计。
```

这些会在后续课程里逐步进入。

---

## 一、本节在主线里的位置

阶段 6 第 22-25 节是一组连续内容：

```text
第 22 节：持久化 checkpoint 基础
第 23 节：checkpoint 存储选型
第 24 节：thread_id 生命周期
第 25 节：会话过期与清理
```

第 22 节回答：

```text
为什么 MemorySaver 不够？
checkpoint 落盘后大概长什么样？
保存时要注意哪些边界？
```

第 23 节回答：

```text
存储到底选内存、文件、SQLite、Postgres，还是 Redis？
每种方案适合什么阶段？
当前项目下一步应该怎么选？
```

第 24 节会继续回答：

```text
thread_id 应该怎么生成、绑定、恢复、结束？
```

第 25 节会继续回答：

```text
checkpoint 不能无限增长，应该怎么过期和清理？
```

所以第 23 节是一个承上启下的设计课。

---

## 二、官方资料确认

我在本节开始前查了 LangGraph 官方文档和对应 checkpoint 扩展包信息，避免用旧说法教学。

官方文档当前强调两类 persistence：

```text
checkpointer
store
```

它们不是一回事。

```text
checkpointer：保存单个 thread 的 graph state 快照，用于短期、线程级记忆。
store：保存跨 thread 的应用数据，用于长期记忆、用户偏好、共享事实。
```

官方文档也明确说明：

```text
MemorySaver / InMemorySaver 存在 RAM 里，进程重启后会丢。
生产环境应使用持久化 checkpointer，例如 PostgresSaver。
本地开发可以使用 SqliteSaver。
```

本项目当前环境检查结果：

```text
langgraph.checkpoint.memory    已安装
langgraph.checkpoint.sqlite    未安装
langgraph.checkpoint.postgres  未安装
```

这说明：

```text
当前项目现在能用 MemorySaver。
SQLite / Postgres checkpointer 扩展还没有加入依赖。
本节只做选型学习，不急着引入新依赖。
```

参考资料：

- LangGraph Persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph Checkpointers: https://docs.langchain.com/oss/python/langgraph/checkpointers
- langgraph-checkpoint-sqlite: https://pypi.org/project/langgraph-checkpoint-sqlite/
- langgraph-checkpoint-postgres: https://pypi.org/project/langgraph-checkpoint-postgres/

---

## 三、基础知识铺垫

### 1. 什么叫“存储选型”

存储选型不是问：

```text
哪个数据库最强？
```

而是问：

```text
我的数据是什么？
数据能不能丢？
数据要保存多久？
会不会多实例同时读写？
是否需要事务？
是否需要查询和审计？
运维成本能不能接受？
当前阶段是否真的需要这么复杂？
```

对于 checkpoint，最核心的问题是：

```text
Agent 的执行状态要不要在服务重启后还能恢复？
```

如果答案是“不需要”，内存就够。

如果答案是“需要”，就必须进入持久化存储。

### 2. checkpoint 数据有什么特点

checkpoint 不是普通业务表。

普通业务表可能是：

```text
users
orders
tickets
payments
```

checkpoint 保存的是：

```text
Agent 执行过程中的状态快照
```

它有几个特点：

```text
写入频率可能不低：每个 super-step 都可能生成 checkpoint。
同一个 thread 会有多个历史 checkpoint。
数据结构可能比较复杂：state、metadata、next、pending writes。
主要按 thread_id 查询。
可能需要按时间清理。
可能包含敏感业务上下文。
可能用于恢复、调试、time travel、human-in-the-loop。
```

所以 checkpoint 存储不只是“能存 JSON 就行”。

### 3. 什么是持久性

持久性就是：

```text
数据写入后，程序退出或机器重启，数据仍然存在。
```

内存没有持久性。

文件、SQLite、Postgres 有持久性。

Redis 要看配置：

```text
纯内存模式：持久性弱。
RDB/AOF 开启后：持久性增强，但仍要理解丢失窗口和恢复策略。
```

所以不能简单说：

```text
Redis 很快，所以适合存 checkpoint。
```

快不等于可靠。

### 4. 什么是事务

事务可以先理解成：

```text
一组操作要么都成功，要么都失败。
```

比如完整 checkpoint 可能涉及：

```text
写 checkpoints 表
写 checkpoint_writes 表
更新 metadata
更新最新 checkpoint 指针
```

如果只写了一半就失败，恢复时可能出现状态不一致。

这就是为什么 Postgres 这类关系型数据库适合生产 checkpoint：

```text
它有成熟事务能力。
可以保证多张表、多行写入的一致性。
```

### 5. 什么是并发

并发就是：

```text
多个请求或多个进程同时读写同一类数据。
```

Agent 场景里可能出现：

```text
用户连续点击确认按钮。
前端重试提交。
多个 ai-service 实例同时处理同一个 thread。
后台清理任务正在删除旧 checkpoint。
管理员在后台查看 thread 状态。
```

如果存储不支持良好的并发控制，就容易出现：

```text
覆盖写
重复恢复
读到半成品
删除了还在用的 checkpoint
```

### 6. 什么是多实例部署

开发时你可能只有一个 Python 服务：

```text
ai-service 进程 A
```

生产里可能是：

```text
ai-service 进程 A
ai-service 进程 B
ai-service 进程 C
```

前端请求可能这次打到 A，下次打到 B。

如果 checkpoint 只在 A 的内存里，B 根本看不到。

这就是多实例部署下不能依赖内存 checkpoint 的原因。

多实例部署通常要求：

```text
所有实例共享同一份 checkpoint 存储。
```

例如：

```text
Postgres
Redis
共享数据库
共享持久化服务
```

### 7. 什么是 TTL

TTL 是 time to live。

可以理解为：

```text
这条数据最多活多久。
```

比如：

```text
工单确认状态 30 分钟后过期。
临时会话 24 小时后清理。
测试 thread 7 天后删除。
```

Redis 天然适合做 TTL。

Postgres 也能做 TTL，但通常需要：

```text
expires_at 字段
定时任务
定期 delete 或归档
索引
```

文件也能做 TTL，但要自己写扫描和删除逻辑。

### 8. 什么是审计

审计就是：

```text
以后能查清楚发生了什么。
```

对智能工单 Agent 来说，审计可能包括：

```text
用户什么时候发起工单？
系统什么时候要求确认？
用户是否确认？
确认前的字段是什么？
创建工单前是否经过权限检查？
哪个 trace_id 对应这次流程？
哪个 checkpoint 是创建前的状态？
```

如果你要做审计，存储就不能只考虑“能恢复”。

还要考虑：

```text
能不能按时间查？
能不能按 thread_id 查历史？
能不能关联 user_id / ticket_id / trace_id？
能不能导出排查报告？
能不能设置权限？
```

这方面 Postgres 比纯文件和 Redis 更适合。

### 9. 什么是运维成本

运维成本就是：

```text
这个存储系统需要你维护多少东西。
```

内存成本最低：

```text
不需要安装。
不需要配置。
不需要备份。
```

但可靠性也最低。

Postgres 能力强，但需要：

```text
安装部署
连接池
备份
权限
监控
慢查询
容量规划
迁移
```

所以选型不是越强越好，而是要匹配阶段。

---

## 四、本节主题系统讲解

### 1. 先分清 checkpointer 和 store

LangGraph 官方文档把 persistence 分成两类：

```text
checkpointer
store
```

它们解决的问题不同。

#### checkpointer

checkpointer 保存的是：

```text
单个 thread 的 graph state 快照
```

适合：

```text
多轮对话连续性
human-in-the-loop
interrupt 后恢复
time travel
故障恢复
同一个 thread 内的短期记忆
```

当前智能工单 Agent 里的：

```text
pending_ticket_confirmation
node_history
ticket_fields
ticket_confirmation_approved
```

更像 checkpointer 应该管理的状态。

#### store

store 保存的是：

```text
跨 thread 的长期应用数据
```

适合：

```text
用户偏好
用户长期画像
常用地址
长期事实
多个会话共享的记忆
```

例如：

```text
用户 panpan 偏好中文回答。
用户经常查询订单物流。
用户属于客服权限组。
```

这些不应该塞进某一个 thread 的 checkpoint 里。

#### 对比

| 维度 | checkpointer | store |
| --- | --- | --- |
| 保存对象 | graph state 快照 | 应用定义的数据 |
| 范围 | 单个 thread | 跨 thread |
| 常见用途 | 恢复流程、人工确认、time travel | 用户偏好、长期记忆、共享事实 |
| 读取方式 | 通过 `thread_id` | 通过业务 key / namespace |
| 当前项目例子 | 工单流程待确认状态 | 用户长期偏好、权限组信息 |

这点很重要。

不要把所有记忆都叫 checkpoint。

也不要把所有状态都塞进 store。

### 2. 选型候选 1：MemorySaver / InMemorySaver

定位：

```text
内存型 checkpointer。
```

优点：

```text
最简单。
不需要外部服务。
速度快。
适合单元测试。
适合学习 LangGraph。
适合本地最小 demo。
```

缺点：

```text
服务重启后 checkpoint 丢失。
进程崩溃后 checkpoint 丢失。
多个 ai-service 实例之间不能共享。
不能做可靠审计。
不能作为长期恢复方案。
```

适合场景：

```text
学习
测试
本地 demo
短生命周期脚本
不需要跨重启恢复的场景
```

不适合场景：

```text
生产环境
用户确认可能延迟很久的流程
多实例部署
需要审计的写操作流程
```

当前项目用它的原因：

```text
阶段 5 学 checkpoint / interrupt 时，我们先用 MemorySaver 降低学习成本。
```

这不是错。

学习阶段先用简单方案是合理的。

但是到阶段 6 生产化，就要知道它的边界。

### 3. 选型候选 2：文件 JSON 快照

定位：

```text
应用层状态快照，不是完整 LangGraph checkpointer。
```

第 22 节我们实现的就是这个。

优点：

```text
直观。
容易理解。
容易打开文件观察。
适合学习 checkpoint 到底保存了什么。
适合本地排查。
比内存多了一点持久化能力。
```

缺点：

```text
并发能力弱。
多实例共享麻烦。
缺少事务。
查询能力弱。
清理策略要自己写。
不是完整 LangGraph checkpointer。
不适合高并发生产恢复。
```

适合场景：

```text
学习持久化基础。
本地开发观察 state。
生成调试快照。
小规模单机实验。
临时排查某个 thread 状态。
```

不适合场景：

```text
正式生产 checkpoint。
多个 Python 实例共享恢复。
高并发写入。
需要复杂查询和审计。
需要严格事务一致性。
```

你要能说清楚：

```text
文件 JSON 是学习桥梁，不是最终方案。
```

### 4. 选型候选 3：SQLite

定位：

```text
单机文件型关系数据库。
```

SQLite 不是普通 JSON 文件。

它是一个真正的数据库，只是数据库通常就是一个本地文件。

优点：

```text
部署简单。
不需要单独启动数据库服务。
支持 SQL。
支持事务。
比 JSON 文件更适合结构化查询。
适合本地开发和单机小工具。
LangGraph 有 SQLite checkpoint 扩展包。
```

缺点：

```text
主要适合单机。
多进程/多实例高并发写入不是它的强项。
网络共享、容器多实例部署会变复杂。
生产扩展性不如 Postgres。
运维能力和权限体系不如服务型数据库。
```

适合场景：

```text
本地开发。
个人工具。
单机部署 demo。
离线评测脚本。
希望比 MemorySaver 更接近真实持久化，但还不想启动 Postgres。
```

不适合场景：

```text
多实例线上服务。
高并发写入。
复杂审计和权限管理。
希望多个服务稳定共享 checkpoint。
```

在当前项目里的位置：

```text
SQLite 可以作为从 MemorySaver 到 Postgres 的过渡练习。
```

但如果目标是最终生产表达，不能只停在 SQLite。

### 5. 选型候选 4：Postgres

定位：

```text
生产级关系型数据库，适合多实例共享、事务、一致性和审计。
```

优点：

```text
持久性强。
事务成熟。
并发能力强。
多实例共享方便。
支持索引和复杂查询。
方便按 thread_id / created_at / user_id / trace_id 查询。
方便做审计、备份、权限和迁移。
LangGraph 有 Postgres checkpoint 扩展包。
```

缺点：

```text
需要部署数据库。
需要连接配置。
需要连接池。
需要备份和监控。
需要理解表结构和索引。
开发环境比 MemorySaver / SQLite 更重。
```

适合场景：

```text
真实生产环境。
多实例 ai-service。
用户确认可能跨分钟或跨小时。
需要可靠恢复。
需要审计写操作。
需要排查历史 checkpoint。
需要后续 Docker Compose 或云部署。
```

不适合场景：

```text
刚学 checkpoint 的第一节。
一次性本地脚本。
完全不需要跨重启恢复的小 demo。
```

当前项目的最终推荐：

```text
智能工单 Agent 如果进入生产化实现，checkpoint 主存储优先选 Postgres。
```

原因：

```text
它能支撑多实例、事务、审计、恢复和长期维护。
```

### 6. 选型候选 5：Redis

定位：

```text
内存型 key-value 存储，常用于缓存、短期会话、限流、分布式锁、TTL 数据。
```

Redis 的特点是：

```text
快。
支持天然 TTL。
适合临时状态。
适合短期会话。
适合高频读写。
```

优点：

```text
延迟低。
设置过期时间很方便。
多个服务实例可以共享。
很适合保存短期 session、临时确认 token、限流计数。
```

缺点：

```text
可靠性取决于持久化配置和部署方式。
审计查询能力不如 Postgres。
复杂事务能力不如关系型数据库。
数据结构长期演进和排查不如 SQL 清晰。
如果只当缓存用，不能作为唯一真实来源。
```

适合场景：

```text
短期会话状态。
确认 token 过期控制。
限流。
临时锁。
高频缓存。
辅助 Postgres 做热点数据。
```

不适合场景：

```text
需要可靠审计的唯一 checkpoint 存储。
需要长期保存完整恢复历史。
需要复杂查询和报表。
```

对当前项目的判断：

```text
Redis 适合后续做会话 TTL、限流、短期确认状态，但不建议作为智能工单 Agent 的唯一权威 checkpoint 存储。
```

如果以后要把 Redis 当 LangGraph checkpointer 用，需要先确认：

```text
是否有稳定 checkpointer 实现。
是否支持完整 LangGraph checkpointer contract。
是否能处理 pending writes。
是否满足恢复一致性。
是否有可靠持久化和备份策略。
```

### 7. 选型候选汇总表

| 存储 | 持久性 | 并发/多实例 | 查询审计 | TTL | 运维成本 | 推荐用途 |
| --- | --- | --- | --- | --- | --- | --- |
| MemorySaver | 无 | 弱 | 弱 | 无 | 最低 | 学习、测试、本地 demo |
| 文件 JSON | 有，但弱 | 弱 | 弱 | 需自写 | 低 | 学习、调试快照、单机实验 |
| SQLite | 有 | 中等偏单机 | 中等 | 需自写 | 低到中 | 本地开发、单机持久化 |
| Postgres | 强 | 强 | 强 | 需自写 | 中到高 | 生产主 checkpoint |
| Redis | 取决于配置 | 强 | 弱到中 | 强 | 中 | 短期状态、TTL、缓存、辅助存储 |

如果只记一句：

```text
学习用 MemorySaver，观察用文件，单机开发可用 SQLite，生产主存储优先 Postgres，Redis 更适合短期状态和 TTL 辅助。
```

### 8. 当前项目怎么选

当前项目还处在学习主线，但阶段 6 已经进入生产化。

所以建议分三步走。

#### 第一步：当前立即阶段

继续保留：

```text
MemorySaver
文件型 checkpoint 快照
```

用途：

```text
MemorySaver 用于单元测试和当前 LangGraph 运行。
文件型快照用于理解、观察、调试和教学。
```

暂时不马上安装 SQLite/Postgres。

原因：

```text
第 23 节是选型，不是实现。
我们要先把判断标准讲清楚。
```

#### 第二步：下一轮本地持久化练习

可以考虑：

```text
SQLite checkpointer
```

用途：

```text
在不启动外部数据库服务的情况下，体验真正 LangGraph checkpointer 持久化。
```

适合学习：

```text
thread_id 写入数据库
服务重启后恢复
state history
checkpoint list
```

#### 第三步：最终生产化方向

推荐：

```text
PostgresSaver
```

用途：

```text
智能工单 Agent 的权威 checkpoint 存储。
```

原因：

```text
智能工单涉及写操作、用户确认、审计、恢复和多实例部署。
Postgres 更适合作为可靠状态存储。
```

Redis 的位置：

```text
后续可以作为 TTL 辅助、限流、短期确认状态缓存，而不是第一优先的权威 checkpoint 存储。
```

### 9. 为什么不是“全部都存 Postgres”

Postgres 很适合生产主 checkpoint，但不代表所有东西都要进去。

例如：

```text
短期限流计数
几分钟过期的验证码
临时前端状态
高频缓存结果
```

这些可能更适合 Redis。

又比如：

```text
本地学习实验
单元测试
快速构造一个图
```

这些继续用 MemorySaver 就够。

优秀的工程设计不是：

```text
全部用一个最强数据库。
```

而是：

```text
根据数据类型、可靠性要求、访问模式、生命周期选择合适存储。
```

### 10. 为什么不是“Redis 快，所以用 Redis”

Redis 的快是优点，但 checkpoint 选型不能只看速度。

checkpoint 首先要保证：

```text
能恢复
不串线
不丢关键状态
写操作前后可审计
服务重启后仍可用
```

如果一个状态是：

```text
创建工单前的用户确认状态
```

它不仅是“缓存”，还关系到：

```text
是否允许执行写操作
用户是否确认过
确认时字段是什么
失败后能否排查
```

这类状态更适合放在可靠、可审计的存储里。

Redis 可以辅助，但要谨慎当作唯一来源。

### 11. 为什么文件快照不能继续扩成生产方案

第 22 节的文件快照已经做了：

```text
thread_id 安全文件名
UTF-8 JSON
schema_version
文件内容 thread_id 校验
```

这已经很适合学习。

但如果继续往生产扩，会遇到：

```text
多个进程同时写一个文件怎么办？
文件写一半进程挂了怎么办？
怎么按 thread_id 和时间查询？
怎么删除过期数据？
怎么限制谁能读文件？
怎么备份？
怎么迁移格式？
怎么处理上万上百万 checkpoint？
```

这些问题最终会把你推向数据库。

所以文件快照要停在合理位置。

### 12. 选型决策树

你可以按下面顺序判断。

```text
1. 只是单元测试或学习？
   -> MemorySaver。

2. 只是想观察 checkpoint JSON 长什么样？
   -> 文件快照。

3. 想本地跨进程/重启练习，不想启动数据库服务？
   -> SQLite。

4. 要生产、多实例、审计、可靠恢复？
   -> Postgres。

5. 主要是短期状态、TTL、限流或缓存？
   -> Redis。

6. 既要可靠 checkpoint，又要短期 TTL？
   -> Postgres 做权威存储，Redis 做辅助。
```

当前智能工单 Agent 的判断：

```text
学习阶段：MemorySaver + 文件快照。
本地持久化练习：SQLite。
生产目标：Postgres。
短期辅助：Redis。
```

---

## 五、和当前代码的对应关系

当前代码里有：

```python
from langgraph.checkpoint.memory import MemorySaver
```

并且：

```python
def build_checkpointed_ticket_agent_graph(...):
    return build_ticket_agent_graph(
        ...,
        checkpointer=MemorySaver(),
    )
```

这说明：

```text
当前真正参与 LangGraph 恢复的是 MemorySaver。
```

第 22 节新增的：

```python
FileTicketAgentCheckpointStore
TicketAgentCheckpointSnapshot
save_ticket_agent_checkpoint_snapshot
```

作用是：

```text
把当前 thread state 额外保存成应用层 JSON 快照。
```

它们目前不是：

```text
LangGraph 官方 checkpointer 替代实现。
```

所以当前项目状态应该准确描述为：

```text
LangGraph 执行恢复：MemorySaver。
应用层观察快照：文件 JSON。
生产 checkpoint 目标：Postgres。
```

这个表达很重要。

如果你说：

```text
我们已经做了生产级 checkpoint。
```

那是不准确的。

如果你说：

```text
我们已经完成 checkpoint 基础和存储选型，知道当前 MemorySaver 的边界，并明确生产方向是 Postgres。
```

这就是准确表达。

---

## 六、面试和工作中怎么讲

### 1. 30 秒版本

```text
LangGraph checkpoint 是 thread 级 graph state 快照，用于多轮记忆、人工确认、故障恢复和 time travel。学习和测试可以用 MemorySaver，但它存在内存里，服务重启会丢。生产智能工单 Agent 涉及用户确认和写操作审计，所以 checkpoint 主存储更适合放 Postgres；SQLite 适合本地开发，Redis 更适合 TTL、限流和短期状态辅助，不建议直接当唯一权威 checkpoint。
```

### 2. 1 分钟版本

```text
我会先区分 checkpointer 和 store。checkpointer 保存单个 thread 的 graph state，用于恢复当前流程；store 保存跨 thread 的长期应用数据，比如用户偏好。当前项目在学习阶段用 MemorySaver 跑通 interrupt 和确认恢复，又实现了文件型 checkpoint snapshot 来观察 state 落盘格式。但文件快照没有事务、并发和完整 LangGraph checkpointer contract，所以不作为生产方案。生产里我会优先用 PostgresSaver，因为智能工单涉及写操作、确认、审计和多实例部署，Postgres 有事务、索引、备份和查询能力。Redis 可以做短期确认状态、限流或 TTL 辅助，但不作为唯一权威 checkpoint。
```

### 3. 3 分钟版本

```text
LangGraph checkpoint 选型要看数据生命周期和恢复要求。MemorySaver 适合学习和测试，因为它简单、快、无外部依赖，但它保存在进程内存里，重启就丢，多实例之间也无法共享。文件 JSON 快照适合教学和排查，可以直观看到 schema_version、thread_id、saved_at、metadata、values，但它不是完整 LangGraph checkpointer，没有 pending writes、channel versions、并发控制和事务。

SQLite 是一个很好的本地开发过渡方案，它有事务和 SQL 查询能力，不需要启动独立数据库服务，适合单机 demo 和本地持久化练习。但它不是我对多实例生产服务的首选。

如果智能工单 Agent 要生产化，我会优先选择 PostgresSaver。原因是它能作为多个 ai-service 实例共享的权威 checkpoint 存储，支持事务、索引、历史查询、备份、权限和审计。工单创建是写操作，用户确认前后的 state 必须能恢复、能追踪、能解释，所以 Postgres 更合适。

Redis 我会放在辅助位置，比如短期 session、确认 token TTL、限流、分布式锁或热点缓存。它很快，也天然支持过期，但如果作为唯一 checkpoint 存储，要额外评估持久化配置、恢复一致性和 LangGraph checkpointer contract。对当前项目来说，学习阶段继续保留 MemorySaver 和文件快照，后续可以先练 SQLite，再把生产目标切到 Postgres。
```

---

## 七、容易混淆的问题

### 1. checkpoint 是不是聊天记录？

不完全是。

聊天记录可能只是：

```text
user message
assistant message
```

checkpoint 保存的是：

```text
graph state
```

它可能包含：

```text
聊天消息
当前节点
工具结果
待确认状态
错误状态
字段提取结果
pending writes
```

所以 checkpoint 比单纯聊天记录更接近“流程执行现场”。

### 2. Postgres 和 store 是不是一回事？

不是。

Postgres 是一种存储系统。

store 是 LangGraph 里的长期记忆抽象。

checkpointer 也可以用 Postgres。

store 也可以用 Postgres。

区别不在于底层数据库名字，而在于：

```text
你保存的是 thread 级 graph state，还是跨 thread 的应用数据。
```

### 3. SQLite 是文件，那和 JSON 文件有什么区别？

SQLite 虽然通常是一个文件，但它是数据库。

它有：

```text
表
索引
SQL
事务
查询能力
并发控制
```

JSON 文件主要是文本快照。

它直观，但数据库能力弱。

所以：

```text
SQLite 文件 != 普通 JSON 文件。
```

### 4. Redis 有持久化，所以能不能直接当生产 checkpoint？

不能直接下结论。

要看：

```text
Redis 是否开启持久化。
丢失窗口是否可接受。
是否有主从和高可用。
是否有完整 LangGraph checkpointer 实现。
是否支持 pending writes 和 state history。
是否满足审计要求。
```

对智能工单这类涉及写操作确认的流程，我会更倾向：

```text
Postgres 做权威 checkpoint。
Redis 做辅助短期状态。
```

### 5. 什么时候需要同时用 Postgres 和 Redis？

当系统既需要：

```text
可靠、可审计、可恢复的 checkpoint
```

又需要：

```text
低延迟、自动过期、高频临时状态
```

就可能同时用。

例如：

```text
Postgres 保存完整 checkpoint。
Redis 保存 30 分钟内的确认 token、限流计数、短期会话缓存。
```

---

## 八、本节练习

### 练习 1：给学习阶段选 checkpoint 存储

问题：

```text
你只是在本地学习 LangGraph interrupt 和 thread_id，不需要服务重启后恢复，应该选什么？
```

参考答案：

```text
选 MemorySaver / InMemorySaver。因为学习阶段最重要的是降低复杂度，它不需要外部服务，写测试也方便。它的缺点是进程重启后状态丢失，但这个场景不要求跨重启恢复，所以可以接受。
```

### 练习 2：给本地持久化练习选存储

问题：

```text
你想在本地练习“服务重启后还能恢复 thread state”，但暂时不想启动 Postgres，应该选什么？
```

参考答案：

```text
可以选 SQLite checkpointer。SQLite 是本地文件型数据库，比 JSON 文件更接近真实数据库，有事务和 SQL 查询能力，又不需要启动独立数据库服务，适合作为 MemorySaver 到 Postgres 之间的过渡练习。
```

### 练习 3：给生产智能工单 Agent 选存储

问题：

```text
智能工单 Agent 要上线，多实例部署，用户确认后会创建真实工单，还要求审计和恢复，checkpoint 主存储应该优先选什么？
```

参考答案：

```text
优先选 Postgres。因为它支持持久化、事务、多实例共享、索引查询、备份、权限和审计。智能工单涉及写操作和用户确认，checkpoint 不能只是临时缓存，需要可靠恢复和可追踪。
```

### 练习 4：判断 Redis 的位置

问题：

```text
Redis 很快，而且支持 TTL，所以它是不是一定适合作为唯一 checkpoint 存储？
```

参考答案：

```text
不一定。Redis 很适合短期状态、TTL、限流和缓存，但作为唯一 checkpoint 存储要评估持久化配置、数据丢失窗口、恢复一致性、审计能力和是否有完整 LangGraph checkpointer 实现。对智能工单这种涉及写操作确认的场景，更建议 Postgres 做权威 checkpoint，Redis 做辅助。
```

### 练习 5：区分 checkpointer 和 store

问题：

```text
“用户偏好中文回答”应该放 checkpointer 还是 store？“当前工单流程等待确认”应该放 checkpointer 还是 store？
```

参考答案：

```text
“用户偏好中文回答”是跨 thread 的长期用户偏好，应该放 store 或业务用户配置表。“当前工单流程等待确认”属于某个 thread 的 graph state，应该由 checkpointer 保存。
```

---

## 九、自测问题

### 自测 1：为什么 MemorySaver 不适合生产？

参考答案：

```text
因为它把 checkpoint 保存在当前 Python 进程内存里。服务重启、进程崩溃、容器重建或多实例路由切换时，状态会丢失或无法共享，所以不适合需要可靠恢复的生产环境。
```

### 自测 2：为什么文件 JSON 快照不是完整 LangGraph checkpointer？

参考答案：

```text
因为文件 JSON 快照主要保存应用层 values，方便学习和观察。完整 LangGraph checkpointer 还需要处理 checkpoint id、checkpoint namespace、channel versions、pending writes、state history、并发和一致性等内容。
```

### 自测 3：Postgres 为什么更适合生产 checkpoint？

参考答案：

```text
因为 Postgres 有成熟事务、持久化、索引、查询、备份、权限和并发能力。多个 ai-service 实例可以共享同一个 Postgres checkpoint 存储，并且能支持审计和历史排查。
```

### 自测 4：SQLite 的主要定位是什么？

参考答案：

```text
SQLite 适合本地开发、单机 demo、个人工具和从 MemorySaver 过渡到生产数据库前的练习。它比 JSON 文件更像数据库，但不适合作为多实例高并发生产服务的首选。
```

### 自测 5：Redis 在当前项目里的合理位置是什么？

参考答案：

```text
Redis 更适合作为短期状态、TTL、限流、确认 token、热点缓存或辅助存储。对智能工单 Agent 的权威 checkpoint，更推荐 Postgres。
```

### 自测 6：如果一个系统既有 Postgres 又有 Redis，怎么分工？

参考答案：

```text
Postgres 保存可靠、可审计、可恢复的权威数据，例如完整 checkpoint、工单记录、确认历史。Redis 保存短期、高频、可过期的数据，例如限流计数、短期确认 token、缓存结果。
```

### 自测 7：checkpoint 存储选型最重要的判断维度有哪些？

参考答案：

```text
要看是否需要跨重启恢复、是否多实例部署、是否需要事务、是否需要审计查询、是否需要 TTL、数据能否丢、保存多久、运维复杂度能否接受。
```

---

## 十、本节总结

本节你要掌握的不是某个数据库命令，而是一套判断方法：

```text
MemorySaver：学习、测试、本地 demo。
文件 JSON：观察和理解 checkpoint，调试快照。
SQLite：本地持久化练习，单机轻量数据库。
Postgres：生产主 checkpoint，适合多实例、事务、审计和可靠恢复。
Redis：短期状态、TTL、缓存、限流和辅助能力。
```

当前项目的推荐路径：

```text
现在：MemorySaver + 文件快照。
后续本地练习：SQLite。
生产目标：Postgres。
辅助能力：Redis。
```

你现在应该能解释：

```text
为什么不能直接用 MemorySaver 上生产。
为什么文件 JSON 只是学习桥梁。
为什么 SQLite 适合本地过渡。
为什么 Postgres 是智能工单 Agent 的生产 checkpoint 首选。
为什么 Redis 快但不一定适合做唯一权威 checkpoint。
```

下一节：

```text
阶段 6 第 24 节：thread_id 生命周期
```

下一节会讲：

```text
thread_id 怎么生成
怎么绑定用户/会话/工单
什么时候创建
什么时候恢复
什么时候结束
怎么避免串线
怎么设计过期和清理的前置规则
```
