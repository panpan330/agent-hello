# 阶段 10 第 5 节：Java 业务服务 tracing 对齐

## 本节定位

上一节我们在 Python `ai-service` 里建立了 tracing plan。

这一节继续往下走：

```text
Python AI 服务调用 Java 业务服务时，trace_id 和 tracing 语义怎么对齐。
```

本节重点不是重新学习 Spring Boot 三层架构，也不是重新讲 MyBatis、Redis、Controller、Service 基础。

你已经有传统 Java 后端经验。

本节要学的是：

```text
传统 Java 后端被 AI Agent 调用时，如何成为整条 AI 请求链路里可追踪的一段。
```

## 本节学习目标

学完本节，你要能说清楚：

1. Python 的 `java.orders.get` / `java.tickets.create` span 和 Java 服务内部链路如何对应。
2. Java `TraceFilter` 为什么要读取、生成、返回 `X-Trace-Id`。
3. MDC 是什么，为什么它适合让 Java 日志自动关联 `trace_id`。
4. Java 响应头、统一响应体、错误响应为什么都要带 `trace_id`。
5. Java Controller、Service、Redis、MyBatis、权限校验、幂等为什么都应该纳入 tracing 视角。
6. Java tracing 里哪些字段可以记录，哪些字段不能记录。

## 本节新增和修改

| 类型 | 内容 |
|---|---|
| 修改代码 | `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/trace/TraceFilter.java` |
| 新增代码 | `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/trace/JavaBusinessTracingPlan.java` |
| 新增测试 | `projects/java-business-service/src/test/java/com/panpan/aibusinessservice/JavaBusinessTracingPlanTest.java` |
| 新增测试 | `projects/java-business-service/src/test/java/com/panpan/aibusinessservice/TraceFilterLoggingTest.java` |
| 新增笔记 | `notes/stage10-05-java-business-service-tracing-alignment.md` |
| 修改进度 | `docs/learning-progress.md` |
| 手动测试文档 | 无，本节自动化测试即可，不需要打开虚拟机 |

## 一句话先讲透

Java 业务服务 tracing 对齐，就是让 Python 侧的一个 Java 调用 span，进入 Java 后能继续用同一个 `trace_id` 看到 Filter、Controller、Service、Redis、MyBatis、权限、幂等和错误响应。

## 基础知识铺垫

### 1. 为什么 Java 服务不能只当“普通后端接口”

在传统后端项目里，Java 服务通常面向前端或其他后端系统。

但在当前项目里，Java 服务还有一个新的身份：

```text
它是 AI Agent 的业务工具执行层。
```

例如用户问：

```text
我的订单 A1001 为什么还没发货？
```

完整链路可能是：

```text
用户
  -> Python /tool-chat
    -> LLM 判断需要 query_order
    -> Python 后端校验工具名和参数
    -> Python JavaOrderClient 发起 HTTP 请求
    -> Java /internal/orders/{orderId}
    -> Java 鉴权、限流、查 Redis、查 MyBatis、权限校验
    -> Java 返回订单白名单字段
    -> Python 把工具结果交给模型总结
    -> 用户看到最终中文回答
```

在这条链路里，Java 服务不是孤立的。

它是 Python tracing 里的一个子链路。

Python 侧看到的是：

```text
java.orders.get
```

Java 侧要继续展开：

```text
java.http.request
  java.internal.auth.resolve
  java.rate_limit.check
  java.order.controller.get
  java.order.service.query
    java.redis.order_cache.get
    java.mybatis.orders.select
    java.order.permission.check
```

这就是“对齐”。

### 2. 跨服务 tracing 最重要的不是日志数量，而是同一个 trace_id

如果 Python 和 Java 各自生成自己的请求编号，排查会很痛苦。

比如：

```text
Python trace_id = py-123
Java trace_id = java-789
```

当用户反馈“刚才那次回答错了”，你在 Python 里找到 `py-123`，但 Java 日志里没有这个编号。

你只能靠时间、订单号、用户 ID 去猜。

这会带来几个问题：

| 问题 | 后果 |
|---|---|
| 需要靠时间窗口猜测 | 容易误判 |
| 多个用户同时请求 | 日志混在一起 |
| 订单号或用户 ID 不适合直接查日志 | 涉及隐私和权限 |
| Java 服务报错但 Python 只看到 502 | 根因难定位 |

所以跨服务 tracing 的底线是：

```text
同一次请求，Python 和 Java 必须共享同一个 trace_id。
```

### 3. `X-Trace-Id` 的职责

当前项目使用：

```text
X-Trace-Id
```

它是一个 HTTP Header。

职责是：

```text
把 Python 当前请求的 trace_id 传给 Java。
```

Python 侧：

```text
JavaOrderClient / JavaTicketClient
  -> build_trace_headers()
  -> 请求头携带 X-Trace-Id
```

Java 侧：

```text
TraceFilter
  -> 读取 X-Trace-Id
  -> 校验格式
  -> 放入 request attribute
  -> 放入 MDC
  -> 放入响应头
```

这样就形成：

```text
Python trace_id == Java trace_id == Java response trace_id
```

### 4. Java Filter 是什么

Filter 是 Servlet 体系里的请求过滤器。

你可以把它理解成：

```text
请求进入 Controller 前，先经过 Filter。
Controller 返回响应后，也会回到 Filter。
```

它适合做这些通用事情：

| 事情 | 是否适合 Filter |
|---|---|
| 读取或生成 trace_id | 适合 |
| 设置响应头 | 适合 |
| 把 trace_id 放入 MDC | 适合 |
| 记录请求开始和结束 | 适合 |
| 具体业务权限判断 | 不适合，应该在 resolver/service |
| 查询订单 | 不适合，应该在 service/mapper |

当前 Java 服务里：

```text
TraceFilter extends OncePerRequestFilter
```

`OncePerRequestFilter` 的意思是：

```text
保证一次请求通常只执行一次这个 Filter。
```

### 5. MDC 是什么

MDC 全称是：

```text
Mapped Diagnostic Context
```

它是日志框架里的一种“当前线程上下文字段”。

你可以简单理解为：

```text
把 trace_id 放进当前请求线程的日志上下文里。
后续这个线程里打出的日志，都可以自动带上 trace_id。
```

当前 Java 配置里有：

```yaml
logging:
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} %-5level [%logger{36}] trace_id=%X{trace_id} %msg%n"
```

其中：

```text
%X{trace_id}
```

就是从 MDC 里读取 `trace_id`。

本节还让 `TraceFilter` 的请求生命周期日志显式输出：

```text
java_request_started trace_id=...
java_request_finished trace_id=...
```

这样即使某些测试环境没有加载自定义日志 pattern，也能在日志正文里看到 `trace_id`。

### 6. 为什么响应头和响应体都要带 trace_id

Java 服务会在响应头里返回：

```text
X-Trace-Id
```

统一响应体里也有：

```json
{
  "trace_id": "..."
}
```

为什么两边都要有？

| 位置 | 作用 |
|---|---|
| 响应头 `X-Trace-Id` | 给调用方程序读取，方便 Python client 日志记录 `upstream_trace_id` |
| 响应体 `trace_id` | 给错误响应、调试、手动 curl、前端提示使用 |

尤其是错误场景：

```text
Java 返回 ORDER_ACCESS_DENIED
```

Python 需要知道：

```text
这个错误属于哪一次 Java 请求。
```

用户或开发者也可以拿 `trace_id` 去排查日志。

### 7. Controller / Service / Mapper 在 tracing 里的位置

传统三层架构在 tracing 里也有清晰位置。

| Java 层 | tracing 里的意义 |
|---|---|
| Filter | 请求入口，处理 trace_id 和请求生命周期日志 |
| Controller | 接收 HTTP 请求，解析路径和请求体 |
| InternalRequestResolver | 内部鉴权、调用方身份、用户身份、租户、限流 |
| Service | 业务规则、权限、事务、幂等 |
| Cache / Redis | 缓存、幂等、限流 |
| Mapper / MyBatis | 数据库访问 |
| ExceptionHandler | 错误码转统一响应，保留 trace_id |

这说明：

```text
传统三层不是和 AI tracing 冲突，而是 tracing 要把传统三层中的关键边界标出来。
```

### 8. Java 错误码为什么是 tracing 的一部分

Java 服务会返回业务错误码：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
INTERNAL_AUTH_FAILED
IDEMPOTENCY_KEY_CONFLICT
TOOL_RATE_LIMITED
```

这些错误码不只是给用户看的。

它们也是排查链路的重要事件。

例如：

| 错误码 | tracing 里可以映射成 |
---|---|
| `INTERNAL_AUTH_FAILED` | `internal_auth_failed` event |
| `TOOL_RATE_LIMITED` | `tool_rate_limited` event |
| `ORDER_NOT_FOUND` | `order_not_found` event |
| `ORDER_ACCESS_DENIED` | `order_access_denied` event |
| `IDEMPOTENCY_KEY_CONFLICT` | `idempotency_key_conflict` event |

这样一来，Python 最终看到的不是一段散乱日志，而是：

```text
java.orders.get span 失败
Java 内部 event = order_access_denied
响应 code = ORDER_ACCESS_DENIED
trace_id = 同一个请求编号
```

### 9. AI Agent 调 Java 时的特殊风险

传统后端调用 Java 接口时，调用方通常是确定的后端服务。

AI Agent 调 Java 时，中间多了模型决策。

这带来新风险：

| 风险 | Java tracing 要帮助看到什么 |
|---|---|
| 模型请求了不该请求的工具 | Python `tool.validation` 应拒绝，Java 侧不应被调用 |
| 模型参数提取错误 | Java 侧可能返回 `ORDER_NOT_FOUND` 或 `ORDER_ID_INVALID` |
| 用户无权查看订单 | Java 侧返回 `ORDER_ACCESS_DENIED` |
| 写操作重复提交 | Java 侧幂等命中或冲突 |
| Python 内部 token 配错 | Java 侧 `INTERNAL_AUTH_FAILED` |
| Redis 影响幂等或限流 | Java 侧 Redis span/event 需要能解释 |

所以 Java tracing 不是只看慢不慢。

它还要帮助回答：

```text
模型提出的业务动作有没有被后端安全接住。
```

### 10. Java tracing 不能记录什么

Java 业务服务能看到很多敏感信息。

不能随便进 tracing attributes：

```text
internal token
Authorization
Cookie
idempotency key
完整请求体
工单描述正文
订单完整 payload
用户 ID
客户 ID
手机号
密码
API Key
```

为什么 `idempotency_key` 也不建议记录？

因为它虽然不是密码，但它可能被用于重放识别，也属于高基数业务标识。

更安全的做法是记录：

```text
是否提供幂等键
幂等结果：created / replayed / conflict
错误码
接口 route
HTTP method
service name
upstream python span
```

## 本节主题系统讲解

### 1. Python 和 Java 的 span 对齐关系

第 4 节 Python 侧有：

```text
tool.execution
  java.orders.get
```

这一节 Java 侧继续展开：

```text
java.orders.get
  -> Java HTTP GET /internal/orders/{orderId}
    -> java.http.request
      -> java.internal.auth.resolve
      -> java.rate_limit.check
      -> java.order.controller.get
        -> java.order.service.query
          -> java.redis.order_cache.get
          -> java.mybatis.orders.select
          -> java.order.permission.check
```

创建工单也是一样：

```text
tool.execution
  java.tickets.create
```

Java 侧展开：

```text
java.tickets.create
  -> Java HTTP POST /internal/tickets
    -> java.http.request
      -> java.internal.auth.resolve
      -> java.rate_limit.check
      -> java.ticket.controller.create
        -> java.ticket.request.validation
        -> java.ticket.service.create
          -> java.order.permission.check
          -> java.redis.ticket_idempotency.get
          -> java.mybatis.ticket.select_by_idempotency
          -> java.mybatis.ticket.insert
          -> java.mybatis.ticket_event.insert
          -> java.redis.ticket_idempotency.set
```

这就是跨服务 tracing 的核心：

```text
Python 看到 Java 是一个 CLIENT span。
Java 自己看到的是这个 CLIENT span 背后的一棵内部 span 树。
```

### 2. 为什么 Java root span 叫 `java.http.request`

Java 服务入口是 HTTP。

所以 Java 侧的根 span 叫：

```text
java.http.request
```

它对应一次 Java 内部 API 请求。

这个 span 的安全属性包括：

```text
service.name = java-business-service
app.flow = query_order / create_ticket
app.trace_id = ...
http.method = GET / POST
http.route = /internal/orders/{orderId} / /internal/tickets
upstream.python_span = java.orders.get / java.tickets.create
```

注意这里用的是 route 模板：

```text
/internal/orders/{orderId}
```

而不是具体：

```text
/internal/orders/A1001
```

原因是具体订单号是高基数字段，不适合进入 metric 标签。

### 3. `TraceFilter` 本节补了什么

原来 `TraceFilter` 已经做了：

```text
读取 X-Trace-Id
没有 trace_id 时生成
设置响应头 X-Trace-Id
放入 MDC
请求结束后清理 MDC
```

本节补充：

```text
java_request_started trace_id=... method=... path=...
java_request_finished trace_id=... method=... path=... status_code=... elapsed_ms=...
java_request_failed trace_id=... method=... path=... elapsed_ms=...
```

这让 Java 服务入口具备最小请求生命周期日志。

排查时可以先看：

```text
Java 是否收到了请求。
Java 使用的是不是 Python 传来的 trace_id。
Java 最终返回了什么 status_code。
Java 入口总耗时是多少。
```

### 4. `JavaBusinessTracingPlan` 的作用

本节新增：

```text
JavaBusinessTracingPlan
```

它不是外部观测平台。

它是 Java 侧 tracing 设计的代码化表达。

它做了几件事：

| 能力 | 说明 |
|---|---|
| flow 分类 | 区分 `query_order` 和 `create_ticket` |
| span plan | 定义 Java 内部关键 span |
| event plan | 定义内部鉴权失败、限流、订单不存在、权限拒绝、幂等冲突等事件 |
| metric plan | 定义 Java 请求、DB、Redis、订单查询、工单创建等指标 |
| 安全 attributes | 过滤 token、请求体、用户 ID、订单详情、工单描述等敏感信息 |
| metric 低基数 | 过滤 trace_id、order_id、ticket_id、idempotency_key 等高基数字段 |

它的意义和第 4 节 Python `ai_service_tracing.py` 对应。

Python 侧先定义：

```text
java.orders.get
java.tickets.create
```

Java 侧再定义：

```text
这两个 span 进入 Java 后怎么展开。
```

### 5. 订单查询链路的排查方法

如果用户反馈：

```text
AI 查订单说我无权查看，但我觉得我应该能看。
```

排查顺序：

1. 从 Python 日志或响应拿到 `trace_id`。
2. 查 Python `tool_chat` 链路，看是否出现 `java.orders.get`。
3. 查 Java 日志，看同一个 `trace_id` 是否出现 `java_request_started`。
4. 看 Java 响应错误码是否是 `ORDER_ACCESS_DENIED`。
5. 看 Java tracing plan 中对应 event：`order_access_denied`。
6. 继续查 Service 权限判断：`order.visibleTo(context.userId(), context.tenantId())`。

这能区分：

```text
模型没调用工具
Python 没传 trace_id
Java 内部鉴权失败
订单不存在
订单存在但用户无权
Java 正常返回但模型总结错
```

### 6. 创建工单链路的排查方法

如果用户反馈：

```text
AI 说帮我创建工单了，但我没看到工单。
```

排查顺序：

1. 先找 Python 的 `trace_id`。
2. 看 Python 是否真的执行了 `java.tickets.create`。
3. 看 Java 是否收到 `POST /internal/tickets`。
4. 看 Java status_code 是 201、400、409 还是 500。
5. 如果是 400，看是否缺少 `Idempotency-Key`。
6. 如果是 409，看是否是 `IDEMPOTENCY_KEY_CONFLICT` 或 `ORDER_NOT_SUPPORT_TICKET`。
7. 如果是 201，看 `tickets` 和 `ticket_events` 是否记录同一个 trace_id。

当前项目已经在创建工单时把 `context.traceId()` 写入：

```text
Ticket.createdTraceId
ticket_events.trace_id
```

这说明：

```text
trace_id 不只在日志里，也进入了重要业务审计记录。
```

### 7. Java metrics 应该观察什么

本节 plan 里先定义了这些 metric：

```text
java_business.request.count
java_business.request.duration
java_business.db.query.duration
java_business.redis.operation.duration
java_business.order.query.count
java_business.ticket.created.count
java_business.idempotency.replay.count
```

它们分别回答：

| metric | 回答的问题 |
|---|---|
| `java_business.request.count` | Java 内部 API 请求量多少 |
| `java_business.request.duration` | Java 服务整体耗时如何 |
| `java_business.db.query.duration` | MyBatis 查询是否变慢 |
| `java_business.redis.operation.duration` | Redis 操作是否变慢 |
| `java_business.order.query.count` | 订单查询工具被调用多少 |
| `java_business.ticket.created.count` | 工单创建成功多少 |
| `java_business.idempotency.replay.count` | 幂等复用发生多少 |

这些当前只是 plan。

后续真正接监控系统时，可以把它们变成 Prometheus/OpenTelemetry metrics。

### 8. 为什么本节没有给每个 Mapper 真的打 span

本节没有大范围修改 Controller、Service、Mapper。

原因是：

```text
我们现在处在 tracing 对齐学习阶段。
```

这节要先完成：

```text
跨服务 trace_id 对齐
Java 请求生命周期日志
Java 内部 span/event/metric 设计固定
安全字段边界固定
```

等后面学习：

```text
请求耗时拆解
监控指标设计
告警
OpenTelemetry 接入
```

再把这些 plan 接到真实 span/metric 采集上更合适。

如果现在每个 Mapper 都加计时代码，会让本节重点从“对齐”变成“到处打点”，学习主线会散。

## 本节代码讲解

### 1. `TraceFilter` 的请求生命周期日志

文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/trace/TraceFilter.java
```

本节新增了三类日志：

```text
java_request_started
java_request_finished
java_request_failed
```

字段包括：

```text
trace_id
method
path
status_code
elapsed_ms
```

这几个字段非常实用。

| 字段 | 作用 |
|---|---|
| `trace_id` | 和 Python 请求关联 |
| `method` | GET / POST |
| `path` | 实际请求路径 |
| `status_code` | Java 最终响应状态 |
| `elapsed_ms` | Java 入口总耗时 |

注意：

```text
TraceFilter 在 finally 中清理 MDC。
```

这是必须的。

因为 Web 容器线程会复用。

如果不清理，下一次请求可能错误地继承上一次请求的 `trace_id`。

### 2. `JavaBusinessFlow`

文件：

```text
JavaBusinessTracingPlan.java
```

本节定义了两个 flow：

```text
QUERY_ORDER
CREATE_TICKET
```

它们分别对应：

| Java flow | HTTP | route | Python upstream span |
|---|---|---|---|
| `QUERY_ORDER` | GET | `/internal/orders/{orderId}` | `java.orders.get` |
| `CREATE_TICKET` | POST | `/internal/tickets` | `java.tickets.create` |

`upstream.python_span` 很关键。

它明确告诉你：

```text
Java 这棵内部 span 树，是从 Python 哪个 span 进入的。
```

### 3. `JavaBusinessSpanSpec`

它描述 Java 内部 span。

关键字段：

```text
name
kind
parentName
attributes
```

例如订单查询里的：

```text
java.mybatis.orders.select
```

它表示：

```text
Java 服务通过 MyBatis 查询 orders 表。
```

它的父 span 是：

```text
java.order.service.query
```

这样就能表达：

```text
数据库查询属于订单服务查询的一部分。
```

### 4. `JavaBusinessEventSpec`

它描述 Java 内部关键事件。

例如：

```text
internal_auth_failed
tool_rate_limited
order_not_found
order_access_denied
ticket_idempotency_replayed
idempotency_key_conflict
transaction_rolled_back
```

这些 event 都能和 Java 业务错误码、异常处理或业务分支对应起来。

例如：

```text
ORDER_ACCESS_DENIED
  -> order_access_denied event
```

### 5. `safeSpanAttributes`

这个方法负责保留安全字段，过滤危险字段。

允许保留：

```text
service.name
app.flow
app.trace_id
http.route
http.method
upstream.python_span
custom.retry_count
custom.cache_hit
```

禁止保留：

```text
internal_token
authorization
idempotency_key
ticket_description
user_id
raw_payload
```

这不是形式主义。

Java 服务离真实业务数据更近，一旦把敏感字段放进 tracing，风险比 Python 层更高。

### 6. `safeMetricAttributes`

metric 标签只保留低基数字段。

允许：

```text
app.flow
http.route
status
```

过滤：

```text
trace_id
order_id
ticket_id
user_id
idempotency_key
internal_token
```

这样后续接 metrics 时，不会因为高基数字段导致监控系统压力过大。

### 7. 本节测试重点

新增测试：

```text
JavaBusinessTracingPlanTest
TraceFilterLoggingTest
```

覆盖：

| 测试 | 目的 |
|---|---|
| `queryOrderPlanAlignsJavaInternalSpansWithPythonClientSpan` | 确认订单查询 Java span 能和 Python `java.orders.get` 对齐 |
| `createTicketPlanCoversValidationTransactionMyBatisRedisAndIdempotency` | 确认创建工单链路覆盖校验、事务、MyBatis、Redis、幂等 |
| `safeSpanAttributesKeepTraceMetadataButOmitSecretsAndSensitivePayloads` | 确认敏感字段不进 span attributes |
| `safeMetricAttributesUseLowCardinalityFieldsOnly` | 确认 metric attributes 不带高基数字段 |
| `traceFilterLogsRequestLifecycleWithTraceId` | 确认 Java 请求入口日志能带 trace_id |

相邻测试也继续覆盖：

```text
InternalOrderControllerTest
InternalTicketControllerTest
```

它们确认已有接口行为没有被破坏。

## 常见误区

### 误区 1：Python 有 trace_id，Java 就不用管了

不对。

Python 只能看到 Java 调用的外部结果。

Java 内部的鉴权、限流、Redis、MyBatis、权限、幂等，需要 Java 自己继续追踪。

### 误区 2：Java 自己生成一个 trace_id 也可以

只有在请求没有传 trace_id 时才可以生成。

如果 Python 已经传了 `X-Trace-Id`，Java 必须复用它。

否则跨服务链路会断。

### 误区 3：MDC 会自动清理

不要这样假设。

当前请求结束后必须清理 MDC。

线程池复用时，如果不清理，可能污染下一次请求日志。

### 误区 4：把 user_id、order_id 放进 metric 标签方便排查

不建议。

这些是高基数字段。

它们适合在单次 trace 或受控日志里谨慎使用，不适合进入 metric 标签。

### 误区 5：Java tracing 只需要看 Controller

不够。

真正影响 AI 工具结果的往往在：

```text
InternalRequestResolver
Service
Redis
MyBatis
权限判断
幂等逻辑
ExceptionHandler
```

### 误区 6：错误响应不用带 trace_id

不对。

错误响应更需要 `trace_id`。

否则 Python 或用户拿到错误后，很难定位 Java 日志。

### 误区 7：Java 业务错误码只是给前端看的

不对。

在 AI Agent 系统里，Java 错误码还是模型回答、Python 错误映射、tracing event、告警分析的重要输入。

## 本节练习

### 练习 1：画出订单查询跨服务链路

请写出用户查询订单时，Python 到 Java 的最小 tracing 链路。

参考答案：

```text
Python:
tool.execution
  java.orders.get

Java:
java.http.request
  java.internal.auth.resolve
  java.rate_limit.check
  java.order.controller.get
    java.order.service.query
      java.redis.order_cache.get
      java.mybatis.orders.select
      java.order.permission.check
```

解释：

Python 的 `java.orders.get` 是跨服务客户端调用。

Java 的 `java.http.request` 是这个调用进入 Java 后的服务端入口。

### 练习 2：为什么 Java 错误响应要带 trace_id

参考答案：

因为错误更需要排查。

当 Java 返回 `ORDER_ACCESS_DENIED`、`ORDER_NOT_FOUND`、`INTERNAL_AUTH_FAILED` 这类错误时，Python 和开发者需要通过同一个 `trace_id` 找到 Java 日志，确认错误发生在哪个阶段。

### 练习 3：下面哪些字段不适合进 Java tracing attributes

请判断：

```text
http.route
http.method
internal_token
idempotency_key
ticket_description
upstream.python_span
service.name
receiver_phone
```

参考答案：

不适合进入：

```text
internal_token
idempotency_key
ticket_description
receiver_phone
```

适合进入：

```text
http.route
http.method
upstream.python_span
service.name
```

原因：

后者是安全元信息，前者涉及密钥、幂等标识、业务正文或个人隐私。

### 练习 4：为什么 `java.mybatis.orders.select` 应该在 `java.order.service.query` 下面

参考答案：

因为 MyBatis 查询是订单查询业务的一部分。

如果数据库慢，应该能从 `java.order.service.query` 下面看到具体慢在 `java.mybatis.orders.select`。

这体现 span 父子关系：

```text
业务操作包含数据库操作。
```

### 练习 5：如果创建工单返回 409，可能对应哪些事件

参考答案：

可能是：

```text
idempotency_key_conflict
order_not_support_ticket
```

在当前 tracing plan 里重点记录：

```text
idempotency_key_conflict
```

业务排查时还要结合响应 code 判断具体原因。

## 自测题

### 自测 1：Java tracing 对齐最重要的一句话是什么

参考答案：

Python 传来的同一个 `trace_id`，进入 Java 后要贯穿 Filter、日志、响应头、响应体、Controller、Service、Redis、MyBatis、权限和错误处理。

### 自测 2：MDC 解决什么问题

参考答案：

MDC 让当前请求线程里的日志能自动带上 `trace_id`，避免每一行日志都手动传递这个字段。

### 自测 3：为什么 Filter 结束时要清理 MDC

参考答案：

因为 Web 容器线程会复用，如果不清理，下一次请求可能继承上一次请求的 `trace_id`，导致日志串线。

### 自测 4：Python 的 `java.orders.get` 和 Java 的 `java.http.request` 是什么关系

参考答案：

`java.orders.get` 是 Python 侧的客户端 span，表示 Python 调 Java 查订单；`java.http.request` 是 Java 侧收到这次 HTTP 请求后的服务端 root span。

### 自测 5：为什么 `order_id` 不适合做 metric 标签

参考答案：

因为每个订单号都可能不同，属于高基数字段。放进 metric 标签会导致指标序列爆炸，增加存储、查询和告警维护成本。

### 自测 6：Java 创建工单为什么要记录 trace_id 到业务审计记录

参考答案：

因为工单创建是写操作，后续需要追溯是谁通过哪次 AI 请求创建的。把 `trace_id` 写入工单和工单事件，可以把线上日志、AI 链路和业务审计串起来。

### 自测 7：Java 返回 `INTERNAL_AUTH_FAILED` 时，Python 应不应该把“内部鉴权失败”直接告诉用户

参考答案：

不应该。

这是内部服务安全细节。Python 应该把它映射成安全的上游错误提示，同时保留 `trace_id` 供开发者排查。

## 本节小结

本节把 Java 业务服务放进了完整 AI tracing 链路里。

你现在应该能说明：

```text
Python 的 java.orders.get / java.tickets.create 是跨服务 CLIENT span。
Java 的 TraceFilter 是服务端入口，负责 trace_id、MDC、响应头和请求生命周期日志。
Java 内部要继续区分鉴权、限流、Controller、Service、Redis、MyBatis、权限、幂等和异常处理。
错误响应、响应头和业务审计都应该保留 trace_id。
Java tracing attributes 要避免 token、请求体、用户 ID、订单详情、工单描述等敏感或高基数字段。
```

下一节是阶段 10 第 6 节：

```text
LLM 调用日志安全
```

它会继续学习：

```text
模型请求、响应、错误、耗时、模型名、token 记录时，如何避免泄露密钥、隐私和完整敏感上下文。
```
