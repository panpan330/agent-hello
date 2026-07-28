# 阶段 7 第 10 节：trace_id 串联 Python + Java

## 本节定位

前两节我们分别解决了两个问题。

第 8 节解决：

```text
Python AI 服务调用 Java 时，Java 怎么确认这是可信内部调用？
这次调用代表哪个真实用户？
这次调用属于哪个租户？
```

第 9 节解决：

```text
Java 返回错误码以后，Python AI 服务怎么把机器错误码变成安全用户回答？
哪些错误能告诉用户？
哪些错误必须隐藏内部细节？
```

本节继续往真实工程推进，解决另一个非常关键的问题：

```text
用户说“刚才查询失败了”，我们怎么从用户这句话定位到 Python 日志、Java 日志、数据库/Redis 操作和最终错误？
```

答案就是：

```text
trace_id
```

本节要把一条链路串起来：

```text
用户请求
-> Python FastAPI
-> Python Agent / Tool Client
-> Java Spring Boot
-> MySQL / Redis
-> Java 返回
-> Python 返回用户
```

如果每一层都能看到同一个 `trace_id`，排查问题就会从：

```text
我不知道是哪次请求出错。
```

变成：

```text
我用 trace_id=manual-stage7-10-001 直接过滤日志，就能找到这次请求的完整链路。
```

## 本节学习目标

学完本节，你应该能讲清楚：

```text
1. trace_id 是什么，解决什么问题。
2. trace_id 和 request_id、span_id 的区别。
3. 为什么 AI Agent 比普通 CRUD 更需要 trace_id。
4. Python FastAPI 如何生成、保存、透传 trace_id。
5. Python 调 Java 时为什么必须带 X-Trace-Id。
6. Java 如何把 trace_id 放到响应头、响应体和日志 MDC。
7. 为什么缺少 trace_id 时也应该生成一个用于排查的 trace_id。
8. 如何通过测试验证 trace_id 不丢、不乱。
```

本节代码目标：

```text
Java 新增 TraceFilter
Java 响应头统一返回 X-Trace-Id
Java 日志 MDC 写入 trace_id
Java 异常响应使用过滤器里的 trace_id
Python Java client 日志记录 upstream_trace_id
补充 Python/Java 相关测试
```

本节不做：

```text
完整 OpenTelemetry 接入
分布式 tracing 平台部署
Jaeger / Tempo / Zipkin
复杂 span 结构设计
日志采集系统
真实线上告警
```

这些属于更后面的生产化内容。本节只做最小但真实有用的跨服务 trace_id 串联。

## 基础知识铺垫

### 1. trace_id 是什么

`trace_id` 可以理解为：

```text
一次完整业务链路的追踪编号
```

用户发起一次请求后，这个请求可能经过多个组件：

```text
浏览器
Nginx
Python FastAPI
LangGraph Agent
Java Spring Boot
MySQL
Redis
```

如果每个组件都自己打一份日志，但没有共同编号，你排查时会很痛苦。

比如用户说：

```text
我刚才 9:30 查订单失败了。
```

你只能靠：

```text
时间范围
用户 ID
接口路径
订单号
错误码
```

去猜是哪条日志。

但如果用户响应里带了：

```text
trace_id=manual-stage7-10-001
```

你就可以直接搜：

```text
manual-stage7-10-001
```

找到：

```text
Python 收到请求
Python 判断意图
Python 调用 Java
Java 收到请求
Java 查询订单
Java 返回 ORDER_ACCESS_DENIED
Python 映射成安全回答
Python 返回用户
```

这就是 trace_id 的价值。

### 2. trace_id 不是用户 ID

`trace_id` 不是用户身份。

用户 ID 表示：

```text
谁在操作？
```

trace_id 表示：

```text
哪一次链路？
```

同一个用户可以有很多次请求：

```text
用户 U1001 第一次查订单 -> trace_id=a
用户 U1001 第二次创建工单 -> trace_id=b
用户 U1001 第三次问退款政策 -> trace_id=c
```

所以不能用用户 ID 代替 trace_id。

也不能用 trace_id 判断权限。

权限判断应该看：

```text
user_id
tenant_id
角色/权限
业务数据归属
```

trace_id 只用于：

```text
日志关联
问题排查
链路追踪
客服/开发沟通
```

### 3. trace_id、request_id、span_id 的区别

这三个词经常一起出现，容易混。

可以先这样理解：

```text
trace_id：一次完整链路的总编号
request_id：一次 HTTP 请求的编号
span_id：一次链路里的某个步骤编号
```

举例：

```text
用户请求智能客服查询订单
```

完整链路：

```text
trace_id = T-001
```

里面可能有多个请求：

```text
request_id = R-001：浏览器 -> Python
request_id = R-002：Python -> Java
```

里面还可能有多个 span：

```text
span_id = S-001：FastAPI 接收请求
span_id = S-002：LangGraph classify_intent
span_id = S-003：query_order tool
span_id = S-004：Java OrderService.queryOrder
span_id = S-005：MyBatis 查询 orders
```

在完整 OpenTelemetry 里，通常会有：

```text
trace_id + span_id + parent_span_id
```

但我们现在不提前做完整 tracing。

本节先掌握最关键的：

```text
一条业务链路至少要有一个能跨服务传递的 trace_id。
```

### 4. 为什么 AI Agent 更需要 trace_id

普通 CRUD 请求通常比较短：

```text
HTTP 请求
-> Controller
-> Service
-> Mapper
-> DB
-> 返回
```

AI Agent 请求会复杂很多：

```text
HTTP 请求
-> 意图识别
-> RAG 检索
-> 大模型调用
-> Tool Calling
-> Java 业务服务
-> 用户确认
-> 写操作
-> 状态持久化
-> 最终回答
```

它的特点是：

```text
步骤多
分支多
可能调用外部模型
可能调用多个工具
可能有重试
可能有用户确认
可能有异步恢复
```

如果没有 trace_id，你很难回答：

```text
这次是模型没理解？
还是工具参数错了？
还是 Java 拒绝了？
还是权限不够？
还是 Redis 限流？
还是返回给用户时被错误映射隐藏了？
```

所以 AI 应用的工程能力，不只是会调模型，还要能排查链路。

### 5. trace_id 应该从哪里来

通常有两种来源。

第一种：上游传入。

比如前端或网关已经带了：

```text
X-Trace-Id: client-trace-001
```

Python 应该复用它。

这样前端、网关、Python、Java 都能对上。

第二种：本服务生成。

如果请求没有带 `X-Trace-Id`，Python 就生成一个：

```text
uuid4().hex
```

也就是 32 位小写十六进制字符串，例如：

```text
8b0e715c76c8423e9dc95b6c8db8409a
```

本节 Java 侧也做了类似事情：

```text
如果请求缺少或携带不安全的 X-Trace-Id，Java TraceFilter 会生成一个用于日志和响应头的 trace_id。
```

注意：

```text
生成 trace_id 是为了排查，不等于放宽 internal API 校验。
```

Java internal API 仍然可以要求业务调用必须传 `X-Trace-Id`。

如果调用没传，业务鉴权可以失败；但失败响应和日志依然应该有 trace_id，方便排查。

### 6. 为什么 trace_id 要放响应头

响应体里已经有：

```json
{
  "trace_id": "manual-stage7-10-001"
}
```

为什么还要放响应头？

因为响应头适合基础设施和客户端统一读取。

比如：

```text
前端统一拦截器
网关日志
浏览器 Network 面板
Python httpx response.headers
Java filter
```

都能很方便地读取：

```text
X-Trace-Id
```

响应体适合业务接口返回。

响应头适合通用链路追踪。

最好两者都有，而且值一致。

### 7. 什么是 MDC

MDC 是：

```text
Mapped Diagnostic Context
```

你可以先把它理解成：

```text
当前线程日志里的上下文字段
```

Java Web 请求通常由一个线程处理。

当请求进入 Java 服务时，我们可以把 trace_id 放进 MDC：

```java
MDC.put("trace_id", traceId);
```

之后这个线程里打印日志时，日志格式可以读取：

```text
%X{trace_id}
```

于是日志里就能显示：

```text
trace_id=manual-stage7-10-001
```

请求结束后要清理：

```java
MDC.remove("trace_id");
```

为什么要清理？

因为线程会复用。

如果不清理，下一次请求可能错误地带着上一次请求的 trace_id。

这会导致排查混乱。

### 8. Python 里的 ContextVar 和 Java 的 MDC 类似吗

有点类似，但不完全一样。

Python 当前项目里用：

```python
ContextVar
```

保存当前请求的 trace_id。

核心逻辑在：

```text
projects/ai-service/app/core/trace.py
```

请求进入 FastAPI 时，中间件设置当前 trace_id：

```text
projects/ai-service/app/middleware/tracing.py
```

日志系统在每条日志里读取当前 trace_id：

```text
projects/ai-service/app/core/logging.py
```

这和 Java MDC 的目标类似：

```text
让同一次请求里的日志自动带上 trace_id。
```

不同点是：

```text
Java MDC 常跟线程绑定。
Python ContextVar 更适合 async/await 场景。
```

你现在不需要深入底层实现，只要记住：

```text
Python 用 ContextVar 保持请求上下文。
Java 用 MDC 保持日志上下文。
```

### 9. trace_id 不能放敏感信息

trace_id 会出现在：

```text
响应头
响应体
日志
错误提示
客服排查记录
监控平台
```

所以 trace_id 不能包含：

```text
手机号
身份证
邮箱
真实姓名
token
API key
密码
详细订单信息
```

trace_id 应该是无业务含义的随机字符串，或者由网关生成的安全追踪编号。

本项目里推荐这种：

```text
8b0e715c76c8423e9dc95b6c8db8409a
```

手动测试时可以用：

```text
manual-stage7-10-001
```

但正式系统里最好由网关或后端生成无意义随机值。

## 本节主题系统讲解

### 1. 本节之前的 trace_id 链路

Python 侧已经有较好的基础：

```text
请求进入 FastAPI
-> trace middleware 读取 X-Trace-Id
-> 没有就生成 trace_id
-> set_trace_id 存进 ContextVar
-> Python 日志自动带 trace_id
-> Python 响应头返回 X-Trace-Id
-> Python 错误响应体返回 trace_id
```

Python 调 Java 时也会带：

```python
build_trace_headers()
```

也就是：

```text
X-Trace-Id: 当前请求 trace_id
```

Java 侧之前也会在响应体里返回：

```json
"trace_id": "..."
```

但 Java 侧还有两个不完整的地方：

```text
1. 响应头没有统一设置 X-Trace-Id。
2. Java 日志没有通过 MDC 自动带 trace_id。
```

所以本节补齐这两个点。

### 2. 本节之后的最小链路

本节之后，链路变成：

```text
用户请求带 X-Trace-Id
-> Python 保存到 ContextVar
-> Python 日志自动带 trace_id
-> Python 调 Java 时带 X-Trace-Id
-> Java TraceFilter 读取 X-Trace-Id
-> Java 响应头设置 X-Trace-Id
-> Java MDC 写入 trace_id
-> Java 响应体仍返回 trace_id
-> Python Java client 日志记录 upstream_trace_id
-> 用户响应仍带 X-Trace-Id
```

用图表示：

```text
X-Trace-Id: manual-stage7-10-001
        |
        v
Python FastAPI logs trace_id=manual-stage7-10-001
        |
        v
httpx -> Java Header X-Trace-Id: manual-stage7-10-001
        |
        v
Java logs trace_id=manual-stage7-10-001
        |
        v
Java response header/body trace_id=manual-stage7-10-001
        |
        v
Python logs upstream_trace_id=manual-stage7-10-001
```

### 3. Java 新增 `TraceFilter`

新增文件：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/common/trace/TraceFilter.java
```

它是一个 Spring Web Filter：

```java
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TraceFilter extends OncePerRequestFilter {
    ...
}
```

`OncePerRequestFilter` 的意思是：

```text
每个 HTTP 请求只执行一次这个过滤器。
```

它适合做：

```text
trace_id 初始化
MDC 初始化
响应头设置
请求结束后的上下文清理
```

`@Order(Ordered.HIGHEST_PRECEDENCE)` 表示：

```text
尽量让它在很早的位置执行。
```

因为 trace_id 应该尽早进入上下文。

如果后面的鉴权、参数校验、业务逻辑出错，日志也能带 trace_id。

### 4. `TraceFilter` 如何解析 trace_id

核心逻辑是：

```java
String traceId = resolveTraceId(request.getHeader(TraceHeaders.TRACE_ID));
```

如果请求头里有合法 trace_id，就复用。

合法规则：

```text
长度 8 到 128
只允许 A-Z a-z 0-9 . _ : -
```

如果没有，或者格式不安全，就生成一个：

```java
UUID.randomUUID().toString().replace("-", "")
```

为什么这里不直接相信任何传入值？

因为响应头和日志里会写入 trace_id。

如果用户传入很奇怪的值，例如换行符、超长字符串、控制字符，就可能影响日志或响应头。

所以 trace_id 虽然不是权限字段，也要做基础格式控制。

### 5. `TraceFilter` 做了哪三件事

第一，把 trace_id 存到 request attribute：

```java
request.setAttribute(TRACE_ID_ATTRIBUTE, traceId);
```

这样后面的异常处理器可以取到统一 trace_id。

第二，设置响应头：

```java
response.setHeader(TraceHeaders.TRACE_ID, traceId);
```

这样调用方可以从响应头拿到 Java 侧确认使用的 trace_id。

第三，写入 MDC：

```java
MDC.put("trace_id", traceId);
```

这样日志格式可以输出：

```text
trace_id=...
```

请求结束后清理：

```java
MDC.remove("trace_id");
```

这一步非常重要。

如果不清理，线程复用后可能污染下一次请求。

### 6. Java 异常处理器为什么改成从 TraceFilter 取值

之前 `GlobalExceptionHandler` 是从 header 取：

```java
request.getHeader(TraceHeaders.TRACE_ID)
```

这有一个问题：

```text
如果请求缺少 X-Trace-Id，异常响应 trace_id 就只能是 "-"
```

本节改成：

```java
TraceFilter.currentTraceId(request)
```

这样即使请求缺少 trace_id，过滤器也会生成一个。

所以错误响应仍然能带：

```text
trace_id=生成值
```

这很重要。

因为最需要排查的情况往往就是错误请求。

如果错误请求没有 trace_id，排查会困难。

### 7. Java 日志格式为什么加 `%X{trace_id}`

新增配置：

```yaml
logging:
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} %-5level [%logger{36}] trace_id=%X{trace_id} %msg%n"
```

这里的：

```text
%X{trace_id}
```

表示从 MDC 里读取 `trace_id`。

所以如果 TraceFilter 写入了：

```java
MDC.put("trace_id", traceId);
```

日志就能显示：

```text
trace_id=manual-stage7-10-001
```

这不是为了好看。

这是为了排查时可以：

```powershell
Select-String -Path app.log -Pattern "manual-stage7-10-001"
```

直接找到相关日志。

### 8. Python Java client 为什么记录 `upstream_trace_id`

Python 调 Java 之后，Java 返回响应头：

```text
X-Trace-Id: manual-stage7-10-001
```

Python client 现在会在完成日志里记录：

```text
upstream_trace_id=manual-stage7-10-001
```

这可以确认：

```text
Python 发过去的 trace_id
Java 实际返回的 trace_id
```

是否一致。

如果不一致，说明链路中间可能有：

```text
请求头没带过去
Java 认为传入 trace_id 不合法并重新生成
网关或代理改了 header
测试代码没有设置 trace_id
```

这比只看“请求成功/失败”更有排查价值。

### 9. 为什么本节不接 OpenTelemetry

项目里之前已经学过一些可观测性和 OTel 概念。

但这一节没有直接接入完整 OpenTelemetry。

原因是：

```text
本节目标是先把最小跨服务 trace_id 链路打通。
```

完整 OTel 还涉及：

```text
traceparent
span_id
parent span
采样
exporter
collector
Jaeger / Tempo
服务拓扑
```

这些东西很有价值，但如果现在全部接入，会让本节主题变散。

学习顺序应该是：

```text
先理解 trace_id 串联
再理解 span
最后接入完整 tracing 平台
```

## 本节代码讲解

### 1. `TraceFilter`

最核心代码：

```java
String traceId = resolveTraceId(request.getHeader(TraceHeaders.TRACE_ID));
request.setAttribute(TRACE_ID_ATTRIBUTE, traceId);
response.setHeader(TraceHeaders.TRACE_ID, traceId);
MDC.put("trace_id", traceId);
try {
    filterChain.doFilter(request, response);
} finally {
    MDC.remove("trace_id");
}
```

这段代码真正表达的是：

```text
请求进入 Java 的第一时间，就确定本次请求使用哪个 trace_id。
无论后面成功还是失败，都把它放到响应头和日志上下文。
请求结束后清理上下文。
```

这里最值得记住的是 `finally`。

因为：

```text
成功要清理。
失败也要清理。
```

否则线程复用时会污染下一个请求。

### 2. `resolveTraceId`

核心代码：

```java
if (incomingTraceId != null) {
    String trimmedTraceId = incomingTraceId.trim();
    if (TRACE_ID_PATTERN.matcher(trimmedTraceId).matches()) {
        return trimmedTraceId;
    }
}
return UUID.randomUUID().toString().replace("-", "");
```

这段代码体现的是：

```text
优先复用上游 trace_id。
但只复用基础格式安全的 trace_id。
没有或不安全时生成新的 trace_id。
```

注意，这不等于 internal API 不要求 trace_id。

`InternalRequestResolver` 仍然会校验：

```text
X-Trace-Id 是否存在
X-Trace-Id 是否符合 internal 调用要求
```

所以：

```text
TraceFilter 负责日志排查上下文。
InternalRequestResolver 负责 internal API 契约和鉴权。
```

这两个职责不同。

### 3. `GlobalExceptionHandler`

之前异常处理器从 header 取 trace_id。

现在从：

```java
TraceFilter.currentTraceId(request)
```

取。

好处是：

```text
如果请求进入了 filter，就一定有用于排查的 trace_id。
错误响应不会轻易出现 trace_id="-"
```

对用户来说，看到 trace_id 后可以告诉客服或开发：

```text
我的错误 trace_id 是 xxx。
```

对开发来说，可以查：

```text
Python 日志
Java 日志
Java 响应头
Java 响应体
```

是否都有同一个值。

### 4. `application.yml` 日志格式

新增：

```yaml
logging:
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} %-5level [%logger{36}] trace_id=%X{trace_id} %msg%n"
```

这个配置不是业务代码，但它对排查很重要。

因为如果只是写入 MDC，却不在日志格式里输出：

```text
MDC 里有 trace_id
但你在控制台看不到
```

所以两者要配套：

```text
TraceFilter 写入 MDC
logging.pattern.console 输出 MDC
```

### 5. Python client 的日志变化

`JavaOrderClient` 完成请求时，现在日志会包含：

```text
upstream_trace_id=...
```

`JavaTicketClient` 也是一样。

这表示：

```text
Python 确认 Java 返回了哪个 trace_id。
```

如果你看到：

```text
Python trace_id=manual-stage7-10-001
upstream_trace_id=manual-stage7-10-001
```

说明 Python 和 Java 在这次调用上对齐。

如果看到：

```text
Python trace_id=manual-stage7-10-001
upstream_trace_id=-
```

说明 Java 没有返回 trace header，或者 Python 调用的不是本节改造后的 Java 服务。

如果看到两个值不同：

```text
Python trace_id=manual-stage7-10-001
upstream_trace_id=8b0e715c76c8423e9dc95b6c8db8409a
```

说明 Java 可能没有接受传入 trace_id，或者认为传入 trace_id 不合法后生成了新值。

### 6. 测试覆盖了什么

Python 侧测试：

```text
test_trace.py
test_java_order_client.py
test_java_ticket_client.py
```

覆盖：

```text
FastAPI 请求会生成/复用 trace_id
Python 日志能共享请求 trace_id
Python 调 Java 时会带 X-Trace-Id
Python client 日志能记录 upstream_trace_id
```

Java 侧测试：

```text
InternalOrderControllerTest
InternalTicketControllerTest
```

覆盖：

```text
成功响应头返回 X-Trace-Id
业务失败响应头返回 X-Trace-Id
缺失 X-Trace-Id 时，Java 仍会生成可排查的响应 trace header
工单创建成功响应头返回 X-Trace-Id
```

这就是本节的最低可用验证。

## 常见误区

### 误区 1：只有出错才需要 trace_id

不对。

成功请求也需要 trace_id。

原因是：

```text
慢请求可能是成功的。
用户投诉“太慢”不一定是失败。
数据不一致可能发生在成功响应后。
一次成功写操作也需要审计。
```

所以成功和失败都应该有 trace_id。

### 误区 2：只在响应体里放 trace_id 就够了

不够。

响应体适合业务调用方读取。

响应头适合：

```text
前端拦截器
网关
浏览器 Network
HTTP client 日志
跨服务调用
```

所以最好响应头和响应体都带。

### 误区 3：trace_id 可以代替权限

不可以。

trace_id 不能证明用户身份。

它只是排查编号。

权限仍然要靠：

```text
user_id
tenant_id
角色
业务归属
Java 后端兜底校验
```

### 误区 4：缺少 trace_id 就直接返回空

不建议。

缺少 trace_id 本身可能就是问题，但错误响应仍然应该有一个生成的 trace_id，方便定位这次失败。

正确思路：

```text
业务契约可以拒绝缺少 X-Trace-Id 的 internal 调用。
但日志和错误响应仍应带一个服务端生成的 trace_id。
```

### 误区 5：trace_id 里放业务信息方便排查

不建议。

比如：

```text
U1001-A1001-phone-138xxxx
```

看似方便，但会造成隐私风险。

trace_id 应该无业务含义。

真正的用户、订单、租户信息应该放在受控日志字段里，并遵守脱敏和权限规则。

## 本节练习

### 练习 1：区分 trace_id、user_id、tenant_id

下面三个字段分别解决什么问题？

```text
trace_id
user_id
tenant_id
```

参考答案：

```text
trace_id：用于串联一次请求或业务链路，方便日志排查。
user_id：表示当前真实用户是谁，用于权限和业务归属判断。
tenant_id：表示当前请求属于哪个租户或业务域，用于多租户隔离。
```

不能混用。

### 练习 2：为什么 Java 响应头也要返回 `X-Trace-Id`

参考答案：

```text
因为响应头可以被 HTTP 客户端、前端拦截器、网关和日志系统统一读取。
响应体里的 trace_id 偏业务，响应头里的 X-Trace-Id 偏基础设施。
两者都带，排查更方便。
```

### 练习 3：为什么 MDC 要在 finally 里清理

参考答案：

```text
Java Web 服务器线程会复用。
如果请求结束后不清理 MDC，下一个请求可能复用同一个线程并错误继承上一次请求的 trace_id。
所以必须在 finally 里 remove。
```

### 练习 4：如果 Python trace_id 和 Java upstream_trace_id 不一致，可能是什么原因

参考答案：

```text
可能原因包括：
Python 没有把 X-Trace-Id 传给 Java；
Java 收到的 X-Trace-Id 格式不合法并重新生成；
中间网关或代理改写了 header；
Python 调用的不是本节改造后的 Java 服务；
测试代码没有设置当前 trace_id。
```

### 练习 5：用户报错时应该让用户提供什么

参考答案：

```text
最关键的是 trace_id。
如果有业务需要，还可以让用户提供订单号、时间范围和操作步骤。
但 trace_id 是定位具体请求日志的第一入口。
```

## 自测题

### 自测 1：trace_id 是不是认证信息？

参考答案：

```text
不是。trace_id 只用于日志关联和链路排查，不能用于判断用户身份，也不能用于权限控制。
```

### 自测 2：本节 Java `TraceFilter` 做了哪三件事？

参考答案：

```text
1. 解析或生成 trace_id，并放到 request attribute。
2. 把 trace_id 写入响应头 X-Trace-Id。
3. 把 trace_id 写入 MDC，让 Java 日志能输出 trace_id，并在 finally 中清理。
```

### 自测 3：为什么缺少 trace_id 的请求仍然要生成 trace_id？

参考答案：

```text
因为这次请求即使被拒绝，也需要排查。
生成 trace_id 不等于放过请求，只是保证错误响应和日志有可搜索的排查编号。
```

### 自测 4：Python 侧用什么保存当前请求 trace_id？

参考答案：

```text
Python 使用 ContextVar 保存当前请求 trace_id。
FastAPI trace middleware 在请求进入时设置，在请求结束时 reset。
```

### 自测 5：完整 OpenTelemetry 和本节 trace_id 有什么关系？

参考答案：

```text
本节 trace_id 是最小跨服务追踪编号。
OpenTelemetry 是更完整的分布式追踪体系，会进一步引入 traceparent、span_id、parent span、采样、exporter 和追踪平台。
应该先理解本节的 trace_id 串联，再学习完整 OTel。
```

## 本节总结

本节把 Python + Java 的排查能力往前推进了一步。

现在我们有了更清晰的链路：

```text
Python 接收/生成 trace_id
-> Python 日志带 trace_id
-> Python 调 Java 带 X-Trace-Id
-> Java TraceFilter 接收/生成 trace_id
-> Java 响应头返回 X-Trace-Id
-> Java MDC 日志输出 trace_id
-> Java 响应体返回 trace_id
-> Python client 日志记录 upstream_trace_id
```

本节最重要的思想是：

```text
trace_id 不解决业务逻辑，但它解决排查入口。
AI Agent 链路越复杂，越需要稳定的追踪编号。
trace_id 不是权限字段，也不能包含敏感信息。
成功和失败都要有 trace_id。
```

下一节进入：

```text
阶段 7 第 11 节：契约测试和集成测试
```

那一节会重点学习：

```text
如何保证 Python client 和 Java API 的契约长期稳定；
哪些测试用 mock，哪些测试用真实 Java；
为什么真实大模型不应该进入自动化测试。
```
