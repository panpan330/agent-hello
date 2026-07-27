# 阶段 7 第 6 节：创建工单写工具真实化

## 本节定位

第 5 节我们完成的是读操作真实化：

```text
查询订单
-> Java Service
-> MySQL orders 表
```

第 6 节开始做写操作真实化：

```text
创建工单
-> Java Service
-> MySQL tickets 表
-> MySQL ticket_events 表
```

这节的核心不是“插入一条 SQL”。

真正要学的是：

```text
AI Agent 发起写操作时，Java 后端怎样保证它安全、幂等、可追踪、可审计。
```

读操作失败，通常只是查不到或没权限。

写操作失败，可能会造成真实业务影响：

```text
重复创建工单。
创建了一半的数据。
用户没有确认却写入了业务系统。
trace_id 丢失导致无法排查。
模型重复调用导致多次落库。
工单有当前状态但没有历史事件。
```

所以本节是阶段 7 里非常关键的一节。

---

## 一、本节学习目标

学完本节，你应该能讲清楚：

```text
读操作和写操作为什么不一样。
为什么创建工单必须使用事务。
tickets 表为什么保存当前状态。
ticket_events 表为什么保存历史事件。
confirmation_id 为什么要落库。
idempotency_key 为什么要落库并加唯一索引。
request_fingerprint 为什么能判断“同一个幂等键是不是同一个请求”。
DuplicateKeyException 为什么是幂等兜底的一部分。
trace_id 为什么必须进入 tickets 和 ticket_events。
为什么 Service 负责事务和业务校验，而不是 Controller 或 Repository 独自决定。
为什么测试环境仍然用 H2，但真实 smoke 要跑 Windows MySQL。
```

本节完成后，Java 服务具备新的真实能力：

```text
POST /internal/tickets 已经可以把工单写入 MySQL。
同一次幂等请求重复提交会返回同一个工单。
同一个幂等键配不同请求参数会返回 IDEMPOTENCY_KEY_CONFLICT。
创建工单时会同步写 ticket_events 事件。
```

---

## 二、本节先不做什么

本节不提前做这些：

```text
不接 Redis。
不做第 7.5 节传统结构重构。
不切 MyBatis。
不做完整用户表落地。
不做工单状态流转。
不做客服人员分配。
不做后台工单列表。
不让 Python AI 服务切换到 java-business-service。
```

为什么不在本节直接加 Redis？

因为你要先理解：

```text
MySQL 唯一约束是最终兜底。
Redis 只是后续做加速、缓存、限流和更快的幂等判断。
```

如果先上 Redis，容易误以为幂等只靠 Redis。

真实项目里，写操作防重复一定要有数据库兜底。

---

## 三、基础知识铺垫

### 1. 读操作和写操作有什么本质区别

读操作通常不会改变业务数据。

比如：

```text
查询订单。
查询工单。
查询知识库。
查看用户信息。
```

读操作的核心风险是：

```text
查错数据。
越权读取。
返回字段过多。
上游超时。
```

写操作会改变业务系统。

比如：

```text
创建工单。
修改订单状态。
发起退款。
关闭工单。
发送通知。
```

写操作的核心风险更多：

```text
重复写入。
写入一半失败。
没有权限也写入成功。
没有用户确认就执行。
执行后无法追踪是谁触发。
模型重复调用导致业务系统产生多条记录。
```

所以 AI Agent 项目里，写操作一定比读操作更谨慎。

---

### 2. 为什么 AI Agent 写操作更危险

普通后端接口通常由前端明确按钮触发：

```text
用户点击“提交工单”
-> 前端调用后端
-> 后端写库
```

AI Agent 场景里多了一层模型：

```text
用户说一句自然语言
-> 模型判断是否需要创建工单
-> Python 后端校验
-> Java 后端写库
```

模型可能出现这些情况：

```text
理解错用户意思。
重复发起工具调用。
把相似问题当成新问题。
在上下文里被 prompt injection 诱导。
输出参数不稳定。
```

所以我们必须让 Java 后端成为最后的业务保护层：

```text
校验订单归属。
校验是否能创建工单。
校验幂等键。
校验用户确认。
写入 trace_id。
写入事件表。
```

---

### 3. 事务是什么

事务可以先理解成：

```text
一组数据库操作要么一起成功，要么一起失败。
```

本节创建工单不是只写一张表。

它要做：

```text
插入 tickets 当前状态。
插入 ticket_events 创建事件。
```

如果只插入 `tickets` 成功，插入 `ticket_events` 失败，会出现：

```text
工单存在。
但没有创建事件。
审计链路断了。
后续排查不知道这张工单怎么来的。
```

如果只插入 `ticket_events` 成功，插入 `tickets` 失败，也不合理：

```text
有事件。
但没有对应工单。
历史记录指向空对象。
```

所以这两个写入必须在同一个事务里。

---

### 4. `@Transactional` 做了什么

本节在 `TicketApplicationService.createTicket(...)` 上加了：

```java
@Transactional
```

它表示：

```text
这个方法里的数据库写操作属于同一个事务。
```

方法执行成功：

```text
事务提交。
tickets 和 ticket_events 都落库。
```

方法抛出异常：

```text
事务回滚。
已经执行过的写入不会留下半成品。
```

为什么事务放在 Service 层？

因为 Service 是业务编排层。

本节链路是：

```text
Controller
-> TicketApplicationService
-> OrderRepository 校验订单
-> TicketRepository 写工单和事件
```

事务边界应该包住“业务动作”，而不只是包住某一条 SQL。

这也符合你熟悉的传统 Spring Boot 风格：

```text
Controller 不管事务。
Service 负责事务。
Mapper/Repository 负责具体 SQL。
```

---

### 5. `tickets` 表保存什么

`tickets` 表保存工单当前状态。

它回答的是：

```text
这张工单现在是什么样？
```

本节落地的关键字段有：

```text
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
request_fingerprint
created_trace_id
created_at
updated_at
```

其中和 AI 写操作关系最密切的是：

```text
source
confirmation_id
idempotency_key
request_fingerprint
created_trace_id
```

这些字段让我们能回答：

```text
这是不是 AI Agent 创建的？
用户是否确认过？
重复请求怎么处理？
这条写操作来自哪次调用链路？
```

---

### 6. `ticket_events` 表保存什么

`ticket_events` 表保存工单历史事件。

它回答的是：

```text
这张工单经历过什么？
```

本节只写一种事件：

```text
created
```

后续可能会有：

```text
assigned
processing
status_changed
closed
comment_added
```

事件表的价值是：

```text
保留历史。
支持审计。
支持排查。
支持以后做客服工作台时间线。
支持 AI 写操作回放。
```

如果只有 `tickets` 表，你只能看到当前状态。

如果有 `ticket_events`，你可以看到状态变化过程。

---

### 7. 为什么需要 `confirmation_id`

`confirmation_id` 是用户确认凭证。

AI Agent 写操作必须先让用户确认。

例如模型准备创建工单时，应该先向用户说：

```text
我将为订单 A1001 创建物流问题工单，标题是“物流太慢”，是否确认？
```

用户确认后，Python AI 服务再携带 `confirmation_id` 调 Java。

Java 落库保存它，是为了以后能证明：

```text
这次写操作不是模型私自执行的。
它对应一次用户确认。
```

本节没有实现完整确认凭证服务。

但已经把字段落库，这是后续补完整确认链路的前提。

---

### 8. 为什么需要 `idempotency_key`

`idempotency_key` 是幂等键。

它解决的问题是：

```text
同一个写请求重复提交时，不能创建多张工单。
```

重复提交可能来自：

```text
网络超时后重试。
前端重复点击。
Python AI 服务重试。
模型重复请求工具。
用户刷新页面。
```

本节 `tickets` 表加了唯一索引：

```sql
UNIQUE KEY uk_tickets_tenant_idempotency (tenant_id, idempotency_key)
```

它表示：

```text
同一个租户下，同一个幂等键只能对应一张工单。
```

这就是 MySQL 层面的最终兜底。

---

### 9. 为什么还需要 `request_fingerprint`

只有 `idempotency_key` 还不够。

因为你还要判断：

```text
同一个幂等键对应的是不是同一个请求。
```

情况 1：同一个幂等键 + 同一个请求参数

```text
应该返回已有工单。
```

情况 2：同一个幂等键 + 不同请求参数

```text
应该返回 IDEMPOTENCY_KEY_CONFLICT。
```

所以本节新增了：

```text
request_fingerprint
```

它是根据这些字段算出来的 SHA-256：

```text
requester_user_id
tenant_id
title
description
category
priority
related_order_id
source
confirmation_id
```

这样后续遇到重复幂等键时，可以比较：

```text
新请求指纹 == 已有请求指纹 -> 返回已有工单
新请求指纹 != 已有请求指纹 -> 幂等键冲突
```

---

### 10. 为什么要处理 `DuplicateKeyException`

本节代码先查一次幂等键：

```text
SELECT ... FROM tickets WHERE tenant_id = ? AND idempotency_key = ?
```

如果已经存在，就返回已有记录或冲突。

但并发情况下，仍然可能出现：

```text
请求 A 查不到。
请求 B 也查不到。
请求 A 插入成功。
请求 B 插入时撞上唯一索引。
```

这时数据库会抛出重复键异常。

Spring JDBC 把它转换成：

```text
DuplicateKeyException
```

本节捕获它以后，再查一次幂等键。

如果查到了，并且指纹一样：

```text
返回已有工单。
```

如果指纹不一样：

```text
返回 IDEMPOTENCY_KEY_CONFLICT。
```

这就是数据库唯一约束兜底的实际写法。

---

### 11. 为什么 trace_id 要落库

`trace_id` 是排查链路的关键。

一次 AI 写操作可能跨多个系统：

```text
用户请求
-> Python FastAPI
-> LangGraph
-> Tool Calling
-> Java business service
-> MySQL
```

如果写入失败或用户投诉，你要能查：

```text
这张工单来自哪次请求？
Python 侧日志是什么？
Java 侧日志是什么？
MySQL 里是哪条记录？
事件表里有没有创建事件？
```

所以本节写入：

```text
tickets.created_trace_id
ticket_events.trace_id
```

这就是后续第 10 节 trace_id 串联 Python + Java 的基础。

---

### 12. 为什么 event_payload 用 JSON

`ticket_events` 里有：

```text
event_payload JSON NOT NULL
```

事件的类型很多，不同事件需要记录的细节也不一样。

比如创建事件可能记录：

```text
ticket_id
related_order_id
category
priority
confirmation_id
idempotency_key
```

关闭事件可能记录：

```text
close_reason
closed_by
resolution
```

如果每种事件都给表加固定字段，表会很臃肿。

所以事件详情适合用 JSON。

但要注意：

```text
高频查询字段不要只放 JSON。
高频过滤字段应该做成普通列。
```

本节把 `event_type`、`ticket_id`、`trace_id`、`created_at` 做成普通列，就是为了方便查询。

---

## 四、本节主题系统讲解

### 1. 本节完成后的写入链路

完整链路是：

```text
POST /internal/tickets
-> InternalTicketController
-> InternalRequestResolver
-> TicketApplicationService.createTicket
-> validateIdempotencyKey
-> validateRelatedOrder
-> TicketRepository.createIdempotently
-> JdbcTicketRepository
-> tickets
-> ticket_events
-> TicketToolView
-> ApiResponse
```

你可以把它翻译成传统三层：

```text
Controller
-> Service
-> Repository / Mapper
-> MySQL
```

虽然当前目录还不是传统结构，但职责已经很接近传统后端了。

第 7.5 节我们会专门把目录结构和 MyBatis 对齐成你习惯的风格。

---

### 2. Controller 仍然没有写业务逻辑

`InternalTicketController` 的职责仍然是：

```text
接收 JSON 请求体。
接收 Idempotency-Key Header。
解析 internal 请求上下文。
调用 TicketApplicationService。
返回 ApiResponse。
```

它没有直接：

```text
校验订单归属。
计算幂等指纹。
写 tickets 表。
写 ticket_events 表。
处理 DuplicateKeyException。
```

这说明 Controller 边界是干净的。

---

### 3. Service 负责业务编排

`TicketApplicationService` 负责：

```text
校验幂等键格式。
校验关联订单是否存在。
校验订单是否属于当前用户。
校验订单是否支持创建工单。
开启事务。
调用 TicketRepository 写入工单。
返回 TicketToolView。
```

为什么这些不放 Repository？

因为 Repository 只应该知道怎么存取数据。

比如：

```text
插入 tickets。
插入 ticket_events。
按 idempotency_key 查已有记录。
```

但“这个用户能不能基于这个订单创建工单”是业务规则，应该在 Service。

---

### 4. Repository 负责持久化细节

`JdbcTicketRepository` 负责：

```text
生成 ticket_id。
计算 request_fingerprint。
查幂等记录。
插入 tickets。
插入 ticket_events。
处理唯一索引冲突。
把数据库行转成 Ticket。
```

它属于基础设施层。

未来第 7.5 节换 MyBatis 时，它会被：

```text
TicketMapper.java
TicketMapper.xml
TicketServiceImpl
```

这样的结构替换或重组。

但无论用 JdbcTemplate 还是 MyBatis，业务边界不能变：

```text
Service 负责业务和事务。
Mapper 只负责 SQL。
DTO 仍然是字段白名单。
```

---

### 5. 幂等流程

本节的幂等流程是：

```text
收到请求
-> 校验 Idempotency-Key
-> 计算 request_fingerprint
-> 按 tenant_id + idempotency_key 查 tickets
-> 如果存在，比较 request_fingerprint
-> 一样：返回已有工单
-> 不一样：抛 IDEMPOTENCY_KEY_CONFLICT
-> 如果不存在，插入新工单
-> 插入创建事件
-> 返回新工单
```

并发兜底流程是：

```text
先查不到
-> 插入时撞唯一索引
-> 捕获 DuplicateKeyException
-> 再查已有记录
-> 指纹一样返回已有工单
-> 指纹不同返回冲突
```

这就是比“先查再插”更可靠的写法。

---

### 6. 事件写入流程

创建工单时同时插入：

```text
ticket_events.event_type = created
ticket_events.operator_type = ai_agent
ticket_events.operator_id = requester_user_id
ticket_events.trace_id = created_trace_id
```

event_payload 里保存：

```text
ticket_id
related_order_id
category
priority
confirmation_id
idempotency_key
```

这条事件的意义是：

```text
这张工单是 AI Agent 基于哪个请求创建的。
创建时关联哪个订单。
用户确认凭证是什么。
幂等键是什么。
```

这就是写操作可审计。

---

## 五、本节代码变更讲解

### 1. `Ticket` 增加审计字段

`Ticket` 新增：

```text
source
idempotencyKey
createdTraceId
```

原来 `Ticket` 只够表达“工单是什么”。

现在它还要表达：

```text
工单从哪里来。
如何幂等。
对应哪次 trace。
```

这对 AI Agent 写操作非常重要。

---

### 2. `TicketStatus.fromCode`

数据库里保存的是字符串：

```text
created
processing
closed
```

Java 领域模型里是枚举：

```text
TicketStatus.CREATED
TicketStatus.PROCESSING
TicketStatus.CLOSED
```

所以本节给 `TicketStatus` 补了 `fromCode`。

这和第 5 节给订单状态补转换方法是同一个思路。

---

### 3. `TicketRepository` 增加 `traceId`

接口从：

```java
createIdempotently(command, requesterUserId, tenantId, idempotencyKey)
```

变成：

```java
createIdempotently(command, requesterUserId, tenantId, idempotencyKey, traceId)
```

原因：

```text
写入 tickets 和 ticket_events 时必须保存 trace_id。
```

如果 Repository 拿不到 trace_id，就没法把写操作链路落到数据库。

---

### 4. `TicketApplicationService` 加事务

本节给创建工单方法加了：

```java
@Transactional
```

它的学习重点是：

```text
创建工单不是一条 SQL。
它是一个业务动作。
业务动作需要事务。
```

这里的事务包住：

```text
订单校验
工单写入
事件写入
```

后续如果写入中途失败，事务会回滚，避免半成品。

---

### 5. `TicketRequestFingerprint`

这是本节新增的幂等指纹工具。

它把请求关键字段拼起来，然后算 SHA-256。

它解决：

```text
同一个幂等键到底是不是同一个请求。
```

为什么不用 `Objects.hash`？

`Objects.hash` 适合简单内存判断，但它只是 int，碰撞概率更高，也不适合长期落库。

本节用 SHA-256，是更像真实项目的做法。

---

### 6. `TicketRowMapper`

`TicketRowMapper` 把 `tickets` 表一行转换成 `Ticket`。

它负责：

```text
ticket_status 字符串 -> TicketStatus
category 字符串 -> TicketCategory
priority 字符串 -> TicketPriority
created_at -> Instant
```

以后换 MyBatis 时，这部分映射逻辑会变成 MyBatis resultMap 或字段映射。

但原理不变：

```text
数据库表示要转换成 Java 业务对象。
```

---

### 7. `JdbcTicketRepository`

这是本节核心代码。

它完成：

```text
按幂等键查已有工单。
插入 tickets。
插入 ticket_events。
重复键异常兜底。
事件 payload JSON 序列化。
```

你不需要死记每一行代码。

你要真正理解它的结构：

```text
先判断幂等。
再创建新对象。
再插入主表。
再插入事件表。
如果唯一约束冲突，再回查已有记录。
```

这就是写操作真实化的核心。

---

### 8. `schema.sql`

本节新增：

```text
tickets 表
ticket_events 表
```

关键约束：

```text
UNIQUE KEY uk_tickets_tenant_ticket (tenant_id, ticket_id)
UNIQUE KEY uk_tickets_tenant_idempotency (tenant_id, idempotency_key)
UNIQUE KEY uk_ticket_events_tenant_event (tenant_id, event_id)
```

其中最重要的是：

```text
uk_tickets_tenant_idempotency
```

它是工单创建幂等的 MySQL 兜底。

---

### 9. 测试增强

本节测试不只看接口返回：

```text
HTTP 201
success=true
ticket_id 存在
```

还用 `JdbcTemplate` 直接查测试库：

```text
tickets 里有这张工单。
ticket_events 里有对应 created 事件。
事件 trace_id 等于请求 trace_id。
```

这很重要。

因为写操作测试不能只看响应。

还要看真实副作用是否正确。

---

## 六、本地真实 MySQL 验证

本节已在 Windows MySQL 做 smoke。

当前 MySQL：

```text
MySQL 8.0.41
database: ai_business
```

验证结果：

```text
orders
tickets
ticket_events
```

三张表已存在。

真实调用：

```text
POST http://127.0.0.1:18002/internal/tickets
```

返回：

```text
success=true
ticket_status=created
trace_id=trace-stage7-ticket-smoke
```

MySQL 中查到：

```text
tickets.ticket_status = created
tickets.source = ai_agent
tickets.created_trace_id = trace-stage7-ticket-smoke
ticket_events.event_type = created
ticket_events.operator_type = ai_agent
ticket_events.trace_id = trace-stage7-ticket-smoke
```

这证明本节不是只通过 H2 测试，而是真实 Windows MySQL 也跑通了。

---

## 七、常见误区

### 误区 1：事务只在复杂系统里才需要

不对。

只要一个业务动作包含多次写入，就应该考虑事务。

本节只写两张表：

```text
tickets
ticket_events
```

就已经需要事务。

---

### 误区 2：幂等只需要先查再插

不够。

先查再插在并发下会出问题。

必须配合：

```text
唯一索引
DuplicateKeyException 处理
重复后回查
```

这才更接近真实项目。

---

### 误区 3：事件表是多余的

不对。

如果没有事件表，后续只能看到工单当前状态。

你无法清楚知道：

```text
谁创建的。
什么时候创建的。
哪个 trace 创建的。
是否 AI 创建。
后续状态怎么变化。
```

AI 写操作尤其需要事件表。

---

### 误区 4：Repository 可以决定所有业务规则

不建议。

Repository 负责数据访问。

Service 负责业务编排。

比如：

```text
订单是否属于当前用户。
订单是否允许创建工单。
创建工单要不要事务。
```

这些应该由 Service 负责。

---

### 误区 5：接了 MySQL 就能相信模型

不能。

MySQL 只是保存数据。

安全边界仍然来自：

```text
internal token
user_id
tenant_id
confirmation_id
idempotency_key
Service 业务校验
DTO 白名单
trace_id
```

---

## 八、本节练习

### 练习 1：为什么创建工单需要事务？

参考答案：

```text
因为创建工单至少要写 tickets 和 ticket_events 两张表。
如果只写入 tickets 成功但 ticket_events 失败，就会出现有工单但没有历史事件的半成品。
事务可以保证这组写操作要么一起成功，要么一起失败。
```

### 练习 2：`tickets` 和 `ticket_events` 的职责有什么区别？

参考答案：

```text
tickets 保存工单当前状态，例如当前标题、分类、优先级、状态、创建来源和幂等信息。
ticket_events 保存工单历史事件，例如创建、分配、状态变化、关闭等。
前者回答“现在是什么”，后者回答“经历过什么”。
```

### 练习 3：为什么需要 `idempotency_key` 唯一索引？

参考答案：

```text
因为同一个写请求可能被重复提交。
唯一索引 unique(tenant_id, idempotency_key) 可以保证同一个租户下同一个幂等键只能创建一张工单。
即使多个请求并发到达数据库，MySQL 也能兜底防止重复写入。
```

### 练习 4：为什么还需要 `request_fingerprint`？

参考答案：

```text
idempotency_key 只能说明“这是同一个幂等键”，不能说明请求参数是否完全相同。
request_fingerprint 根据用户、租户、标题、描述、分类、优先级、关联订单、来源和 confirmation_id 计算。
如果同一个幂等键对应相同指纹，返回已有工单；如果对应不同指纹，返回 IDEMPOTENCY_KEY_CONFLICT。
```

### 练习 5：为什么 `trace_id` 要写入数据库？

参考答案：

```text
因为 AI 写操作跨 Python、模型调用、Java 和 MySQL。
trace_id 写入 tickets 和 ticket_events 后，可以把一次用户请求、Python 日志、Java 日志和数据库记录串起来，方便排查和审计。
```

### 练习 6：为什么本节测试要查数据库，而不只看 HTTP 响应？

参考答案：

```text
创建工单是写操作，HTTP 响应成功不一定代表数据库副作用正确。
测试直接查询 tickets 和 ticket_events，可以确认工单主记录和创建事件都真的写入了，并且 trace_id 等关键字段正确。
```

### 练习 7：为什么本节还不切 MyBatis？

参考答案：

```text
因为阶段 7 已经规划在第 7.5 节统一做 Java 服务结构传统化重构，并把 JdbcTemplate 切到 MyBatis。
本节先集中学习写操作、事务、幂等和事件表，避免在同一节同时做大规模目录迁移和技术栈替换。
```

### 练习 8：如果插入 tickets 成功、插入 ticket_events 失败，事务应该怎么处理？

参考答案：

```text
事务应该回滚，让 tickets 的插入也撤销。
这样不会留下“有工单但没有创建事件”的半成品数据。
```

---

## 九、自测问题

### 自测 1：本节真实化的是读操作还是写操作？

答案：

```text
写操作。具体是 POST /internal/tickets 创建工单，把工单写入 MySQL tickets 表，并写入 ticket_events 创建事件。
```

### 自测 2：本节创建工单的完整链路是什么？

答案：

```text
InternalTicketController -> TicketApplicationService -> OrderRepository 校验关联订单 -> TicketRepository -> JdbcTicketRepository -> tickets 表和 ticket_events 表。
```

### 自测 3：同一个幂等键重复提交相同请求应该返回什么？

答案：

```text
应该返回已有工单，而不是创建新工单。
```

### 自测 4：同一个幂等键提交不同请求应该返回什么？

答案：

```text
应该返回 IDEMPOTENCY_KEY_CONFLICT，表示这个幂等键已经被另一个请求参数使用过。
```

### 自测 5：本节哪个字段证明工单是 AI Agent 创建的？

答案：

```text
tickets.source 和 ticket_events.operator_type。
本节创建工单时它们都是 ai_agent。
```

### 自测 6：本节哪个字段证明写操作经过用户确认？

答案：

```text
confirmation_id。
它作为用户确认凭证落在 tickets 表里，也进入 ticket_events 的 event_payload。
```

### 自测 7：本节哪个 MySQL 约束是幂等最终兜底？

答案：

```text
UNIQUE KEY uk_tickets_tenant_idempotency (tenant_id, idempotency_key)。
```

### 自测 8：下一节学什么？

答案：

```text
下一节是阶段 7 第 7 节：Redis 幂等、缓存和限流。
它会在 MySQL 兜底的基础上，引入 Redis 做更快的幂等判断、订单查询缓存和工具调用限流。
```

---

## 十、本节总结

本节把创建工单从内存写入推进到了真实 MySQL 写入。

核心成果：

```text
tickets 表已落地。
ticket_events 表已落地。
POST /internal/tickets 已经写入 MySQL。
创建工单使用 @Transactional。
idempotency_key 通过唯一索引做数据库兜底。
request_fingerprint 用来区分相同幂等键下的相同请求和冲突请求。
ticket_events 记录 created 事件。
trace_id 已写入 tickets 和 ticket_events。
自动化测试验证数据库副作用。
真实 Windows MySQL smoke 已通过。
```

你现在应该能讲清楚：

```text
AI Agent 写操作不是让模型想写就写。
Python 负责工具调用编排。
Java Service 负责业务校验、事务、幂等和权限边界。
MySQL 负责保存长期业务事实，并用唯一索引做最终兜底。
事件表负责审计和历史追踪。
```

下一节进入：

```text
阶段 7 第 7 节：Redis 幂等、缓存和限流
```

第 7 节之后，会按我们已经记下的安排进入：

```text
阶段 7 第 7.5 节：Java 服务结构传统化重构 + MyBatis
```
