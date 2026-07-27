# 阶段 7 第 4 节：MySQL 业务数据模型

## 本节定位

上一节我们新增了：

```text
projects/java-business-service
```

它已经有：

```text
Spring Boot 骨架
internal API
统一 ApiResponse
BusinessErrorCode
InternalRequestResolver
Order / Ticket 领域模型
OrderToolView / TicketToolView
InMemoryOrderRepository
InMemoryTicketRepository
MockMvc 契约测试
```

但数据还在内存里。

内存数据的特点是：

```text
服务重启就没了
不能表达真实业务历史
不能支撑审计
不能支撑事务
不能支撑后续复杂查询
不能作为真实业务事实来源
```

所以阶段 7 第 4 节开始设计 MySQL 业务数据模型。

这节不是 SQL 入门。

你有传统 Java 后端经验，所以本节重点是：

```text
在 AI Agent 调用传统 Java 后端的场景下，用户、订单、工单、工单事件、幂等这些数据应该如何设计。
```

本节先做设计，不马上接 MySQL。

原因是：

```text
先把表的职责、字段、约束、索引、数据流讲清楚。
下一节再接 MySQL 依赖、初始化脚本和 Repository 实现。
```

---

## 一、本节学习目标

学完本节，你要能讲清楚：

1. 为什么本节不急着直接接 MySQL。
2. AI Agent 场景下，数据库表为什么不能直接面向模型设计。
3. MySQL 在 Java 业务服务里的职责是什么。
4. Redis 和 MySQL 在幂等、缓存、限流里的分工。
5. 为什么需要 `users` 表。
6. 为什么 `X-User-Id` 最终要对应真实用户表。
7. 为什么 `orders` 表要包含 `user_id` 和 `tenant_id`。
8. 订单状态和支付状态应该如何落库。
9. 为什么订单表不应该为了模型回答而塞太多展示字段。
10. 为什么需要 `tickets` 表。
11. 工单为什么必须保存 `source=ai_agent`。
12. `confirmation_id` 和 `idempotency_key` 为什么都要保存。
13. 为什么需要 `ticket_events` 表。
14. 工单当前状态和工单历史事件的区别。
15. 幂等键唯一索引为什么是写操作安全的最终兜底。
16. 哪些字段适合建索引。
17. 哪些字段不该随便建索引。
18. 逻辑外键和物理外键怎么取舍。
19. 表结构、Java Domain、Entity、DTO、ToolView 的关系。
20. 下一节如何从表设计进入真实 MySQL 接入。

---

## 二、本节先不做什么

这一节暂时不做：

1. 不修改 `pom.xml` 添加 MySQL 依赖。
2. 不添加 MyBatis / JPA。
3. 不启动 MySQL。
4. 不打开 VMware。
5. 不修改 Java Repository 实现。
6. 不替换内存 Repository。
7. 不修改 Python AI 服务。
8. 不新增 Docker Compose MySQL 服务。

本节只新增：

```text
notes/stage7-04-mysql-business-data-model.md
docs/java-business-database-design.md
```

以及更新索引文档。

这样学习节奏更清楚：

```text
第 3 节：Java 服务骨架和领域模型
第 4 节：MySQL 表设计
第 5 节：真正接入 MySQL
```

---

## 三、基础知识铺垫

### 1. AI Agent 项目里的数据库不是给模型看的

这是本节第一条原则。

数据库表不是给模型直接看的。

数据库表服务于：

```text
业务事实存储
权限判断
事务一致性
审计追踪
幂等兜底
后端查询
数据恢复
```

模型看到的应该是：

```text
Java 后端返回的 Tool-facing DTO
Python 过滤后的工具结果
```

也就是说：

```text
MySQL 表
-> Java Entity / Persistence Model
-> Java Domain Model
-> Java Response DTO
-> Python Pydantic Model
-> Tool Result 白名单
-> 模型总结
```

中间每一层都在收敛字段。

不能让模型直接看到表。

也不能把表字段原封不动返回给 AI 服务。

### 2. 传统 CRUD 表设计为什么还不够

普通后端项目里，你可能会这样想：

```text
用户表
订单表
工单表
```

然后做增删改查。

这当然是基础。

但 AI Agent 场景会多出几个问题。

第一，AI 可能重复触发写操作。

所以工单创建要有：

```text
idempotency_key
```

第二，AI 写操作必须能追踪来源。

所以工单要有：

```text
source
confirmation_id
created_by
trace_id
```

第三，AI 回答错误时要能排查。

所以关键表里要能关联：

```text
trace_id
ticket_event
created_at
updated_at
```

第四，AI 不能越权查订单。

所以订单和工单都要有：

```text
user_id
tenant_id
```

第五，工单状态变化不能只覆盖当前值。

所以需要：

```text
ticket_events
```

这些不是普通 CRUD 入门里最先讲的内容，但在 AI Agent 接真实业务时很关键。

### 3. MySQL 在本项目里的职责

MySQL 负责长期业务事实。

本项目里 MySQL 应该保存：

```text
用户
订单
工单
工单事件
幂等结果的最终兜底
审计相关字段
```

MySQL 不负责：

```text
prompt
模型输出
RAG chunk
向量检索
LangGraph 状态
短期缓存
高频限流计数
```

其中 RAG 向量数据属于 Qdrant/Milvus。

短期状态和高频计数更适合 Redis。

### 4. MySQL 和 Redis 怎么分工

阶段 7 后面会用 Redis。

但今天要先讲清 MySQL 和 Redis 的分工。

MySQL：

```text
长期事实
强一致业务数据
可恢复数据
事务
唯一约束
审计历史
```

Redis：

```text
短期状态
缓存
限流计数
幂等键快速判断
临时确认状态
分布式锁
```

例如创建工单幂等：

```text
Redis 可以快速记录 idempotency_key -> ticket_id。
MySQL tickets.idempotency_key 唯一索引做最终兜底。
```

为什么不能只靠 Redis？

因为 Redis 数据可能过期，也可能因为配置问题丢失。

工单是长期业务事实，最终必须落 MySQL。

为什么不能只靠 MySQL？

可以只靠 MySQL。

但高并发下，Redis 可以减少重复请求直接打到数据库。

所以更稳的设计是：

```text
Redis 加速。
MySQL 兜底。
```

### 5. 为什么需要 `users` 表

当前 Java 服务用 Header：

```text
X-User-Id
```

模拟真实用户身份。

但真实系统里，`X-User-Id` 不应该只是一个字符串。

它应该对应数据库里的用户。

所以需要：

```text
users
```

用户表至少解决：

```text
用户是否存在
用户属于哪个租户
用户是否启用
用户角色是什么
订单是否属于该用户
工单是谁提交的
```

如果没有用户表，Java 后端只能相信 Header。

但阶段 7 的目标是：

```text
Java 后端不能只相信调用方传来的身份字符串，还要能查到真实用户。
```

### 6. 为什么需要 `tenant_id`

`tenant_id` 表示租户或业务域。

在当前学习项目里可以先用：

```text
default
```

但提前设计 `tenant_id` 有价值。

因为真实业务常常存在：

```text
不同店铺
不同公司
不同业务线
不同客户组织
```

同一个订单号如果在不同租户下可能重复。

同一个用户也可能属于某个租户。

AI Agent 绝不能跨租户泄露数据。

所以用户、订单、工单都建议有：

```text
tenant_id
```

查询订单时至少判断：

```text
orders.user_id = current_user_id
orders.tenant_id = current_tenant_id
```

### 7. `users` 表怎么设计

建议字段：

```text
id
user_id
tenant_id
display_name
role
status
created_at
updated_at
```

其中：

```text
id
-> 数据库内部主键。

user_id
-> 业务用户 ID，对应 X-User-Id。

tenant_id
-> 租户。

display_name
-> 展示名。

role
-> 用户角色，例如 customer、agent、admin。

status
-> enabled、disabled。
```

注意：

```text
id 是数据库内部主键。
user_id 是业务身份。
```

不要把数据库自增 id 暴露给模型。

模型最多需要知道：

```text
当前用户身份已通过后端校验。
```

不应该知道内部主键。

### 8. 为什么订单表要有 `user_id`

订单查询的核心安全问题是：

```text
当前用户能不能查这个订单？
```

这不能交给模型判断。

Java 后端要查：

```sql
SELECT *
FROM orders
WHERE order_id = ?
  AND user_id = ?
  AND tenant_id = ?
```

如果查不到：

可能是订单不存在。

也可能是订单存在但不属于该用户。

为了避免泄露“这个订单是否存在”，真实系统有时会统一返回：

```text
ORDER_NOT_FOUND
```

也可以在内部日志里记录实际是无权限。

当前学习项目为了学习清楚，会区分：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
```

但你要知道真实生产里可以根据安全要求调整。

### 9. `orders` 表怎么设计

建议字段：

```text
id
order_id
tenant_id
user_id
order_status
payment_status
logistics_message
latest_event
can_create_ticket
created_at
updated_at
```

这些字段对应当前 `Order` 领域模型。

其中：

```text
order_status
-> waiting_shipment、shipped、delivered、canceled。

payment_status
-> unpaid、paid、refunded。

logistics_message
-> 给用户看的物流摘要。

latest_event
-> 最新订单事件摘要。

can_create_ticket
-> 是否允许基于该订单创建工单。
```

注意：

订单表不是完整电商订单系统。

本项目只保存 AI 工具链路需要的订单摘要字段。

后续如果要扩展真实电商后端，可以拆更多表：

```text
order_items
payments
shipments
refunds
```

但当前阶段先保持收敛。

### 10. 订单状态为什么用字符串枚举

订单状态可以用：

```text
varchar
tinyint
enum
```

本项目建议先用：

```text
varchar
```

例如：

```text
waiting_shipment
shipped
delivered
canceled
```

原因是：

```text
和 Java enum code 一致。
和 Python Pydantic enum 一致。
读起来直观。
学习阶段更清楚。
```

生产里用 tinyint 也可以。

但要有状态字典和清楚映射。

不要让数据库是：

```text
1, 2, 3
```

Java 是：

```text
WAITING_SHIPMENT, SHIPPED
```

Python 是：

```text
waiting_shipment, shipped
```

最后到处映射不清。

### 11. 为什么需要 `tickets` 表

工单是 AI Agent 写操作的主要成果。

它必须持久化。

`tickets` 表至少回答：

```text
谁创建的工单
哪个租户
关联哪个订单
工单类型是什么
优先级是什么
当前状态是什么
来源是不是 AI Agent
用户确认 ID 是什么
幂等键是什么
创建时 trace_id 是什么
```

这比普通“留言表”更严格。

因为工单是 AI 触发的写操作。

必须能回查：

```text
这个工单为什么创建？
是不是用户确认过？
是不是重复请求？
是哪次 trace 触发的？
```

### 12. `tickets` 表怎么设计

建议字段：

```text
id
ticket_id
tenant_id
requester_user_id
related_order_id
title
description
category
priority
ticket_status
source
confirmation_id
idempotency_key
created_trace_id
created_at
updated_at
```

其中：

```text
ticket_id
-> 业务工单号，例如 T1001。

requester_user_id
-> 提交工单的用户，对应 X-User-Id。

related_order_id
-> 可空，表示关联订单。

source
-> ai_agent / manual / system。

confirmation_id
-> Python AI 服务侧用户确认记录。

idempotency_key
-> 写操作幂等键。

created_trace_id
-> 创建工单时的 trace_id。
```

### 13. `source` 为什么重要

工单来源要记录。

可能来源：

```text
ai_agent
manual
system
```

`ai_agent` 表示：

```text
由 AI Agent 流程创建。
```

`manual` 表示：

```text
人工客服或后台页面创建。
```

`system` 表示：

```text
系统自动规则创建。
```

为什么要记录？

因为后续统计和审计要区分：

```text
AI 创建了多少工单？
AI 创建工单错误率是多少？
哪些工单来自用户确认？
AI 创建的工单是否比人工更多重复？
```

没有 `source`，这些都很难分析。

### 14. `confirmation_id` 为什么要落库

`confirmation_id` 是 Python AI 服务侧用户确认流程的记录。

保存它的价值是：

```text
证明这个写操作不是模型自己直接执行的。
可以回查用户确认过程。
可以和 Python confirmation store / logs 对上。
可以用于面试讲清 Human-in-the-loop。
```

它不能替代幂等键。

它解决的是：

```text
用户是否确认过。
```

幂等键解决的是：

```text
重复请求是否重复写入。
```

所以两个都要保存。

### 15. `idempotency_key` 为什么要唯一

创建工单是写操作。

写操作可能被重复提交：

```text
网络超时后重试
用户重复点击确认
Python client 重试
模型流程重复触发
```

`idempotency_key` 唯一索引用来保证：

```text
同一个写请求不会创建多个工单。
```

MySQL 里建议：

```sql
UNIQUE KEY uk_tickets_idempotency_key (idempotency_key)
```

如果使用多租户，也可以考虑：

```sql
UNIQUE KEY uk_tickets_tenant_idempotency (tenant_id, idempotency_key)
```

本项目建议用：

```text
tenant_id + idempotency_key
```

这样不同租户即使偶然生成相同幂等键，也不会互相影响。

### 16. 为什么需要 `ticket_events` 表

如果只有 `tickets.ticket_status`，只能知道当前状态。

例如：

```text
created
processing
closed
```

但不知道状态怎么来的。

真实工单系统需要历史。

所以需要：

```text
ticket_events
```

事件可以记录：

```text
created
assigned
priority_changed
status_changed
comment_added
closed
```

这样可以回答：

```text
工单什么时候创建？
谁创建？
什么时候分配？
谁处理？
什么时候关闭？
中间发生过什么？
```

AI Agent 项目里尤其重要。

因为如果 AI 创建了错误工单，需要能回溯。

### 17. `ticket_events` 表怎么设计

建议字段：

```text
id
event_id
tenant_id
ticket_id
event_type
event_payload
operator_type
operator_id
trace_id
created_at
```

其中：

```text
event_id
-> 业务事件 ID。

ticket_id
-> 关联工单业务 ID。

event_type
-> created、status_changed 等。

event_payload
-> JSON，保存事件细节。

operator_type
-> ai_agent、user、staff、system。

operator_id
-> 操作者 ID。

trace_id
-> 触发事件的链路 ID。
```

事件表最好只追加。

不要随便修改历史事件。

### 18. 为什么事件表用 JSON 字段

不同事件的细节不同。

例如创建事件：

```json
{
  "title": "物流太慢",
  "category": "logistics"
}
```

状态变更事件：

```json
{
  "from": "created",
  "to": "processing"
}
```

评论事件：

```json
{
  "comment": "客服已联系物流。"
}
```

如果每种事件都建一堆列，表会变得很宽。

所以事件明细可以用：

```text
JSON
```

但不要滥用 JSON。

查询条件常用字段仍然要单独列出来：

```text
tenant_id
ticket_id
event_type
created_at
```

### 19. 物理外键和逻辑外键

MySQL 可以加外键：

```sql
FOREIGN KEY (requester_user_id) REFERENCES users(user_id)
```

也可以不加物理外键，只在业务层保证关联。

两种方式都有取舍。

物理外键优点：

```text
数据库强约束
防止脏数据
```

物理外键缺点：

```text
迁移复杂
高并发写入时可能影响性能
跨服务拆库后不适用
```

本项目学习阶段建议：

```text
先用逻辑外键 + 唯一索引 + Java 业务校验。
```

例如：

```text
orders.user_id 对应 users.user_id
tickets.related_order_id 对应 orders.order_id
```

但不强制建物理外键。

这样后续实现更灵活。

### 20. 索引怎么设计

索引服务查询。

不要为了“看起来专业”乱加索引。

本项目常见查询：

```text
根据 user_id + tenant_id 查用户。
根据 order_id + tenant_id 查订单。
根据 user_id + tenant_id + order_id 判断订单归属。
根据 ticket_id + tenant_id 查工单。
根据 tenant_id + idempotency_key 判断幂等。
根据 related_order_id 查该订单相关工单。
根据 ticket_id 查工单事件。
```

所以建议索引：

```text
users: unique(tenant_id, user_id)
orders: unique(tenant_id, order_id)
orders: index(tenant_id, user_id, order_id)
tickets: unique(tenant_id, ticket_id)
tickets: unique(tenant_id, idempotency_key)
tickets: index(tenant_id, requester_user_id, created_at)
tickets: index(tenant_id, related_order_id, category)
ticket_events: unique(tenant_id, event_id)
ticket_events: index(tenant_id, ticket_id, created_at)
```

### 21. 不该乱建哪些索引

不要随便给大文本字段建普通索引。

例如：

```text
description
logistics_message
latest_event
event_payload
```

这些字段不适合普通 B-Tree 索引。

不要给低区分度字段单独建太多索引。

例如：

```text
status
priority
source
```

单独索引可能效果有限。

如果要查：

```text
tenant_id + status + created_at
```

可以考虑组合索引。

索引要围绕真实查询设计。

### 22. 表和 Java 代码怎么对应

当前 Java 里有：

```text
Order
Ticket
OrderRepository
TicketRepository
InMemoryOrderRepository
InMemoryTicketRepository
OrderToolView
TicketToolView
```

后续接 MySQL 时会增加：

```text
UserEntity
OrderEntity
TicketEntity
TicketEventEntity
MySqlOrderRepository
MySqlTicketRepository
```

但不应该删除：

```text
Order
Ticket
OrderToolView
TicketToolView
```

因为：

```text
Entity 面向数据库。
Domain Model 面向业务。
ToolView 面向 AI 服务契约。
```

### 23. AI Agent 写操作的完整数据流

创建工单最终应该是：

```text
用户自然语言
-> Python Agent 提取字段
-> Python 要求用户确认
-> Python 生成 confirmation_id 和 idempotency_key
-> Python 调 Java internal API
-> Java 校验 internal token
-> Java 校验 user_id / tenant_id
-> Java 校验 related_order_id
-> Java 校验 idempotency_key
-> Java 写 tickets
-> Java 写 ticket_events
-> Java 返回 TicketToolView
-> Python 校验响应
-> 模型总结给用户
```

本节设计的表就是为这条链路服务。

### 24. 为什么本节只是设计，不接数据库

因为接数据库会引入新问题：

```text
MySQL 服务怎么启动
连接串怎么配置
schema 怎么初始化
MyBatis/JPA 选哪个
事务怎么写
测试库怎么准备
Docker Compose 怎么加
```

这些都值得单独讲。

如果今天一起做，重点会被冲散。

所以本节只做：

```text
表设计
字段解释
索引解释
DDL 草案
和现有 Java 结构的对应关系
```

下一节再真正接 MySQL。

---

## 四、本节主题系统讲解

### 1. 本节新增的数据库设计文档

本节新增：

```text
docs/java-business-database-design.md
```

这份文档用于后续实现 MySQL 接入。

它包含：

```text
设计原则
表关系
users 表
orders 表
tickets 表
ticket_events 表
DDL 草案
索引说明
Java 代码映射
后续实现顺序
```

它不是最终生产数据库设计。

它是阶段 7 的学习版业务数据模型。

### 2. 表关系总览

本节设计 4 张核心表：

```text
users
orders
tickets
ticket_events
```

关系：

```text
users 1 - N orders
users 1 - N tickets
orders 1 - N tickets
tickets 1 - N ticket_events
```

用文字说：

```text
一个用户可以有多个订单。
一个用户可以创建多个工单。
一个订单可以关联多个工单。
一个工单可以有多个事件。
```

### 3. 为什么不是直接从订单表开始

因为订单权限依赖用户。

如果没有 `users` 表，订单只是一堆数据。

Java 后端无法严肃判断：

```text
当前 X-User-Id 是否真的存在？
用户属于哪个 tenant？
用户状态是否 enabled？
```

所以即使当前 AI 工具重点是订单查询，也要先设计用户表。

### 4. `users` 表设计说明

核心字段：

```text
id
tenant_id
user_id
display_name
role
status
created_at
updated_at
```

建议唯一约束：

```text
unique(tenant_id, user_id)
```

原因：

```text
同一个租户下 user_id 唯一。
不同租户可以有同名 user_id，视业务而定。
```

当前学习项目可以先用：

```text
U1001
U2001
```

对应内存订单里的 ownerUserId。

### 5. `orders` 表设计说明

核心字段：

```text
id
tenant_id
order_id
user_id
order_status
payment_status
logistics_message
latest_event
can_create_ticket
created_at
updated_at
```

重要约束：

```text
unique(tenant_id, order_id)
index(tenant_id, user_id, order_id)
```

`unique(tenant_id, order_id)` 保证订单号在租户内唯一。

`index(tenant_id, user_id, order_id)` 支持权限查询：

```text
当前用户查自己的订单。
```

### 6. `tickets` 表设计说明

核心字段：

```text
id
tenant_id
ticket_id
requester_user_id
related_order_id
title
description
category
priority
ticket_status
source
confirmation_id
idempotency_key
created_trace_id
created_at
updated_at
```

重要约束：

```text
unique(tenant_id, ticket_id)
unique(tenant_id, idempotency_key)
index(tenant_id, requester_user_id, created_at)
index(tenant_id, related_order_id, category)
```

其中最关键的是：

```text
unique(tenant_id, idempotency_key)
```

它是创建工单写操作的 MySQL 兜底保护。

### 7. `ticket_events` 表设计说明

核心字段：

```text
id
tenant_id
event_id
ticket_id
event_type
event_payload
operator_type
operator_id
trace_id
created_at
```

重要约束：

```text
unique(tenant_id, event_id)
index(tenant_id, ticket_id, created_at)
```

事件表用于记录历史，不只是当前状态。

例如创建工单时，可以写一条事件：

```text
event_type = created
operator_type = ai_agent
operator_id = ai-service
trace_id = 当前 X-Trace-Id
```

这样以后排查 AI 创建工单问题时，有链路。

### 8. `ticket_id` 和 `id` 的区别

每张表可以有：

```text
id
```

作为数据库主键。

同时业务上有：

```text
user_id
order_id
ticket_id
event_id
```

作为业务 ID。

区别：

```text
id
-> 数据库内部使用。

ticket_id
-> 对业务和用户可见。
```

AI 服务应该看到：

```text
ticket_id
```

不应该依赖：

```text
id
```

### 9. 工单 ID 怎么生成

学习阶段可以先简单生成：

```text
T1001
T1002
```

真实系统可以考虑：

```text
数据库序列
雪花 ID
号段服务
业务前缀 + 日期 + 序列
```

例如：

```text
T202607270001
```

本节不实现 ID 生成器。

但表结构预留：

```text
ticket_id varchar(64)
```

### 10. 工单状态怎么设计

建议状态：

```text
created
processing
closed
```

当前先保持少量状态。

不要一开始设计太复杂：

```text
new
assigned
accepted
pending_user
pending_vendor
resolved
rejected
closed
reopened
```

复杂状态后续可以扩展。

阶段 7 当前重点是：

```text
AI Agent 创建工单后，Java 后端能保存并返回稳定结果。
```

### 11. 工单类型和优先级怎么设计

当前类型：

```text
refund
order_query
logistics
complaint
policy_gap
```

当前优先级：

```text
low
normal
high
```

这些和现有 Java enum、Python Pydantic enum 对齐。

这很重要。

如果数据库、Java、Python 三边枚举不一致，会导致：

```text
模型提取字段正确
Python 校验通过
Java 入库失败
```

或者：

```text
Java 入库成功
Python 无法解析返回结果
```

所以枚举要统一。

### 12. `can_create_ticket` 要不要存在订单表

可以存在。

它表示：

```text
当前订单是否允许创建客服工单。
```

但要注意：

```text
can_create_ticket 是简化字段。
```

真实系统里它可能由多种规则计算：

```text
订单状态
售后期限
是否已取消
是否已退款
用户角色
风控状态
是否已有未关闭工单
```

当前学习阶段可以先落一个布尔字段。

后续复杂化时，可以改成规则计算。

### 13. 幂等键应该保存多久

工单表里的 `idempotency_key` 会长期保存。

原因：

```text
它和工单创建事实绑定。
```

Redis 里的幂等键可以有 TTL。

例如：

```text
10 分钟
30 分钟
1 小时
```

Redis 过期后，MySQL 唯一约束仍然能防止同一个 key 再次创建新工单。

但业务上是否允许很久之后用同一 key 再提交，取决于设计。

学习阶段先简单处理：

```text
idempotency_key 长期唯一。
```

### 14. `created_trace_id` 为什么要入库

trace_id 通常在日志里。

那为什么工单表还要保存？

因为工单是重要业务结果。

保存 `created_trace_id` 可以快速从业务记录回到链路日志。

例如用户投诉：

```text
为什么 AI 给我创建了这个工单？
```

我们可以从 `tickets.created_trace_id` 找到：

```text
Python 请求日志
LangGraph 节点历史
工具调用日志
Java Controller 日志
Java Service 日志
```

这对 AI 系统排查很重要。

### 15. DDL 草案不是最终代码

本节文档里会给 DDL 草案。

DDL 是：

```text
CREATE TABLE ...
```

但它还不是实际运行脚本。

下一节真正接 MySQL 时，才会决定：

```text
schema.sql
Flyway
Liquibase
MyBatis 初始化
Docker init script
```

本节只先把设计想清楚。

### 16. 当前 Java 内存模型怎么映射到表

当前：

```text
Order.ownerUserId
Order.tenantId
Order.orderStatus
Order.paymentStatus
Order.logisticsMessage
Order.latestEvent
Order.canCreateTicket
```

映射到：

```text
orders.user_id
orders.tenant_id
orders.order_status
orders.payment_status
orders.logistics_message
orders.latest_event
orders.can_create_ticket
```

当前：

```text
Ticket.ticketId
Ticket.requesterUserId
Ticket.tenantId
Ticket.ticketStatus
Ticket.title
Ticket.description
Ticket.category
Ticket.priority
Ticket.relatedOrderId
Ticket.confirmationId
Ticket.createdAt
```

映射到：

```text
tickets.ticket_id
tickets.requester_user_id
tickets.tenant_id
tickets.ticket_status
tickets.title
tickets.description
tickets.category
tickets.priority
tickets.related_order_id
tickets.confirmation_id
tickets.created_at
```

新增：

```text
tickets.idempotency_key
tickets.created_trace_id
```

这些来自 internal API Header 和 AI 工具链路。

### 17. 后续 Repository 怎么替换

当前是：

```text
InMemoryOrderRepository
InMemoryTicketRepository
```

后续会变成：

```text
MySqlOrderRepository
MySqlTicketRepository
```

如果用 MyBatis，可能是：

```text
OrderMapper
TicketMapper
TicketEventMapper
```

但应用层仍然依赖：

```text
OrderRepository
TicketRepository
```

这就是第 3 节提前抽接口的价值。

### 18. 契约测试后续怎么变化

现在测试的是内存实现。

后续接 MySQL 后，测试要增加：

```text
表初始化
测试数据插入
订单查询从 MySQL 读取
创建工单写入 MySQL
同一 idempotency_key 重复请求返回同一 ticket_id
idempotency_key 冲突返回 409
ticket_events 写入 created 事件
```

但测试仍然不调用真实大模型。

因为这是 Java 业务服务契约测试。

### 19. 本节对项目的实际改变

本节新增：

```text
notes/stage7-04-mysql-business-data-model.md
docs/java-business-database-design.md
```

本节更新：

```text
README.md
docs/learning-progress.md
projects/java-business-service/README.md
```

本节没有修改 Java 运行代码。

---

## 五、本节数据库设计速记

### 1. 四张核心表

```text
users
orders
tickets
ticket_events
```

### 2. 用户表

解决：

```text
X-User-Id 对应真实用户。
用户属于哪个租户。
用户是否启用。
用户是什么角色。
```

### 3. 订单表

解决：

```text
订单事实。
订单属于谁。
订单属于哪个租户。
订单状态和支付状态。
订单是否能创建工单。
```

### 4. 工单表

解决：

```text
AI 创建工单的持久化事实。
用户确认 ID。
幂等键。
trace_id。
当前工单状态。
```

### 5. 工单事件表

解决：

```text
工单历史。
审计。
状态变化。
AI 创建工单的可追溯性。
```

### 6. 最重要的唯一索引

```text
users: unique(tenant_id, user_id)
orders: unique(tenant_id, order_id)
tickets: unique(tenant_id, ticket_id)
tickets: unique(tenant_id, idempotency_key)
ticket_events: unique(tenant_id, event_id)
```

### 7. 最重要的查询索引

```text
orders: index(tenant_id, user_id, order_id)
tickets: index(tenant_id, requester_user_id, created_at)
tickets: index(tenant_id, related_order_id, category)
ticket_events: index(tenant_id, ticket_id, created_at)
```

### 8. 最重要的 AI Agent 字段

```text
tickets.source
tickets.confirmation_id
tickets.idempotency_key
tickets.created_trace_id
ticket_events.operator_type
ticket_events.trace_id
```

---

## 六、常见误区

### 误区 1：表结构就是给模型看的

不对。

表结构给 Java 后端保存业务事实。

模型只能看到白名单工具结果。

### 误区 2：有 Redis 幂等就不需要 MySQL 唯一约束

不对。

Redis 是加速层。

MySQL 唯一约束是最终兜底。

### 误区 3：工单只需要一张当前状态表

不够。

真实工单需要事件历史。

否则无法审计和回溯。

### 误区 4：`confirmation_id` 和 `idempotency_key` 可以只留一个

不对。

`confirmation_id` 证明用户确认。

`idempotency_key` 防重复写入。

### 误区 5：所有字段都应该建索引

不对。

索引会增加写入成本和存储成本。

索引应该围绕查询模式设计。

### 误区 6：数据库自增 id 可以直接给 AI 服务用

不推荐。

AI 服务应该使用业务 ID，例如 `order_id`、`ticket_id`。

数据库内部 id 不应该成为外部契约。

### 误区 7：订单不存在和无权限永远要区分返回

不一定。

学习阶段为了理解可以区分。

生产系统为了避免泄露订单是否存在，有时会统一返回“不存在或无权访问”。

---

## 七、本节练习

### 练习 1：为什么本节不急着直接接 MySQL？

参考答案：

```text
因为接 MySQL 会同时引入依赖、连接配置、初始化脚本、Repository 实现、事务、测试数据和 Docker 编排等问题。本节先把表职责、字段、索引、约束和 AI Agent 相关字段设计清楚，下一节再实现更稳。
```

### 练习 2：为什么数据库表不能直接给模型看？

参考答案：

```text
数据库表包含内部主键、权限字段、审计字段、敏感字段和不适合用户可见的业务细节。模型只应该看到 Java DTO 和 Python 白名单过滤后的最小工具结果，不能直接依赖表结构。
```

### 练习 3：为什么 `orders` 表需要 `user_id` 和 `tenant_id`？

参考答案：

```text
因为订单查询必须校验当前用户和当前租户是否有权查看该订单。user_id 表示订单所属用户，tenant_id 表示租户边界，Java 后端根据它们防止越权查询和跨租户数据泄露。
```

### 练习 4：为什么 `tickets` 表要保存 `source`？

参考答案：

```text
source 用来区分工单来源，例如 ai_agent、manual、system。这样可以统计 AI 创建了多少工单、排查 AI 创建工单的问题，也能在审计时区分人工创建和 AI 创建。
```

### 练习 5：`confirmation_id` 和 `idempotency_key` 分别解决什么问题？

参考答案：

```text
confirmation_id 解决用户是否确认过这个 AI 工具计划；idempotency_key 解决同一个写请求重复提交时不要重复创建工单。一个是用户确认凭证，一个是写操作防重复控制。
```

### 练习 6：为什么需要 `ticket_events` 表？

参考答案：

```text
tickets 表只保存工单当前状态，不足以表达历史。ticket_events 用来记录创建、分配、状态变化、关闭等事件，支持审计、回溯和排查 AI 创建工单的完整过程。
```

### 练习 7：为什么 `unique(tenant_id, idempotency_key)` 很重要？

参考答案：

```text
它是创建工单幂等的 MySQL 兜底约束。同一租户下同一个幂等键不能创建多个工单，即使 Redis 失效或并发请求穿透到数据库，MySQL 唯一约束也能防止重复写入。
```

### 练习 8：为什么不建议给 `description`、`event_payload` 这类字段随便建普通索引？

参考答案：

```text
这些字段通常是长文本或 JSON，不适合普通 B-Tree 索引。普通索引会增加存储和写入成本，而且未必能支持有效查询。索引应该围绕 tenant_id、user_id、order_id、ticket_id、created_at 等高频查询字段设计。
```

---

## 八、自测问题

### 自测 1：本节设计了哪四张核心表？

答案：

```text
users、orders、tickets、ticket_events。
```

### 自测 2：MySQL 和 Redis 在幂等上的分工是什么？

答案：

```text
Redis 用于快速判断和短期缓存幂等结果，减少重复请求打到数据库；MySQL 通过 tickets 表中的 tenant_id + idempotency_key 唯一索引做最终兜底，保证不会重复创建工单。
```

### 自测 3：工单表里最能体现 AI Agent 写操作来源的字段有哪些？

答案：

```text
source、confirmation_id、idempotency_key、created_trace_id。这些字段能说明工单是否由 AI Agent 创建、是否经过用户确认、如何防重复、对应哪条请求链路。
```

### 自测 4：为什么需要 `ticket_events.operator_type`？

答案：

```text
operator_type 用来表示事件操作者类型，例如 ai_agent、user、staff、system。它能区分事件是 AI 触发、用户触发、人工客服触发还是系统规则触发。
```

### 自测 5：为什么不建议让 Python AI 服务依赖数据库自增 `id`？

答案：

```text
数据库自增 id 是内部持久化主键，不是稳定外部契约。Python AI 服务应该依赖 order_id、ticket_id 这类业务 ID，避免暴露内部结构并降低数据库改造对外部服务的影响。
```

### 自测 6：本节为什么没有修改 Java 运行代码？

答案：

```text
因为本节目标是表设计和数据模型学习，还没有进入 MySQL 接入。先把字段、索引、约束和表关系讲清楚，下一节再修改 pom、配置、Repository 和测试，更容易理解每一步变化。
```

### 自测 7：下一节应该学什么？

答案：

```text
下一节应该学习 Spring Boot 接入 MySQL，也就是添加 MySQL 依赖、配置数据源、准备初始化 SQL、实现 MySQL Repository，并让订单查询从数据库读取。
```

---

## 九、本节总结

这一节没有急着写数据库连接代码。

这是刻意的。

因为真实业务服务不是“先把 MySQL 连上就完事”。

你要先知道：

```text
用户、订单、工单、工单事件分别保存什么。
哪些字段服务权限。
哪些字段服务 AI Agent 审计。
哪些字段服务幂等。
哪些字段服务 trace 排查。
哪些字段不能暴露给模型。
哪些索引支撑真实查询。
```

本节最重要的结论：

```text
MySQL 保存长期业务事实。
Redis 后续负责短期状态、缓存、限流和幂等加速。
Java 后端通过表结构、唯一约束、业务校验和 DTO 白名单，把 AI Agent 的工具调用变成可控业务动作。
```

本节新增：

```text
docs/java-business-database-design.md
notes/stage7-04-mysql-business-data-model.md
```

下一节进入：

```text
阶段 7 第 5 节：Spring Boot 接入 MySQL，订单查询读工具真实化第一步
```

下一节会开始改 Java 代码：

```text
添加 MySQL 相关依赖
配置数据源
准备 schema / seed 数据
实现 MySQL 订单 Repository
让 GET /internal/orders/{order_id} 从 MySQL 查询
补测试
```
