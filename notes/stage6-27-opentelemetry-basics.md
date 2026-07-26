# 阶段 6 第 27 节：OpenTelemetry 基础

本节目标：理解 OpenTelemetry 是什么、为什么生产系统需要它、`trace / span / context propagation / resource / semantic conventions` 分别是什么，并为当前智能工单 Agent 设计一套最小但安全的 OpenTelemetry 风格上下文和 span attributes。

这一节先不安装 OpenTelemetry SDK，不启动 Collector，不真实上报数据。

原因是：

```text
先学清楚概念和字段设计，再接 SDK 和采集链路。
```

如果一开始就安装一堆包，很容易变成：

```text
照着文档复制代码，服务能跑，但不知道 trace 是什么、span 是什么、traceparent 是什么、Collector 又是干什么的。
```

我们这节要先把底层逻辑学明白。

---

## 一、本节在主线里的位置

第 26 节我们学了：

```text
LangSmith tracing 基础
project / trace / run / thread / tags / metadata
Agent 状态如何整理成 LangSmith metadata
哪些字段不能直接进入 tracing
```

第 27 节继续问：

```text
如果以后不用 LangSmith，或者同时用多个观测平台怎么办？
Python AI 服务、Java 服务、向量数据库、网关、任务队列之间怎么串起同一条 trace？
除了 LLM / Agent 调试，还有普通后端服务的链路追踪怎么办？
```

答案就是 OpenTelemetry。

阶段 6 可观测性这一组大概是：

```text
第 26 节：LangSmith tracing 基础
第 27 节：OpenTelemetry 基础
第 28 节：trace / span / log / metrics 的关系
第 29 节：生产日志字段设计
```

第 26 节更偏：

```text
LLM / Agent 调试和评测平台
```

第 27 节更偏：

```text
通用后端可观测性标准
```

这两节不是互相替代，而是互相补充。

---

## 二、官方资料确认

本节参考了 OpenTelemetry 和 W3C 的官方文档：

- OpenTelemetry Traces: https://opentelemetry.io/docs/concepts/signals/traces/
- OpenTelemetry Context propagation: https://opentelemetry.io/docs/concepts/context-propagation/
- OpenTelemetry Python propagation: https://opentelemetry.io/docs/languages/python/propagation/
- OpenTelemetry Python instrumentation: https://opentelemetry.io/docs/languages/python/instrumentation/
- OpenTelemetry Semantic conventions: https://opentelemetry.io/docs/concepts/semantic-conventions/
- OpenTelemetry Resource semantic conventions: https://opentelemetry.io/docs/specs/semconv/resource/
- W3C Trace Context: https://www.w3.org/TR/trace-context/

这些官方资料确认了几个关键事实：

```text
1. span 是 OpenTelemetry trace 的基本构建块。
2. trace 由一组相关 span 组成，这些 span 共享同一个 trace_id。
3. span 有 name、parent span id、开始时间、结束时间、span context、attributes、events、links、status 等信息。
4. context propagation 让跨服务的 traces 能被串成同一条链路。
5. Python 可以用 instrumentation libraries 自动传播 context，也可以手动 inject / extract。
6. OpenTelemetry 用 W3C Trace Context HTTP headers 传播 trace context。
7. traceparent header 包含 version、trace-id、parent-id、trace-flags。
8. trace-id 是 32 位小写十六进制，不能全 0。
9. parent-id 是 16 位小写十六进制，不能全 0。
10. semantic conventions 提供通用字段命名，例如 service.name、service.version。
11. resource attributes 用来描述产生 telemetry 的服务或资源。
```

这些概念会直接进入本节代码和笔记。

---

## 三、基础知识铺垫

### 1. OpenTelemetry 是什么

OpenTelemetry 经常简称 OTel。

它不是一个大模型。

它不是日志平台。

它不是 LangSmith。

它也不是 Prometheus、Grafana、Datadog、Jaeger、Tempo 这类后端系统。

更准确地说：

```text
OpenTelemetry 是一套开源可观测性标准、API、SDK、工具和协议生态。
```

它帮你做的是：

```text
用统一方式生成、传递、收集和导出 traces、metrics、logs 等 telemetry 数据。
```

你可以把它理解成：

```text
应用程序和观测平台之间的通用语言。
```

如果没有 OpenTelemetry，你的系统可能会变成：

```text
Python 服务用一套 tracing SDK
Java 服务用另一套 APM Agent
网关用另一个厂商格式
日志平台有自己的 trace_id
指标平台又有自己的 label 名
```

结果就是：

```text
数据被多个平台锁住
字段命名不一致
跨语言链路串不起来
换平台成本高
团队难以统一规范
```

OpenTelemetry 想解决的是：

```text
不要让可观测性数据绑定死在某个厂商或某个框架上。
```

### 2. 什么是 telemetry

telemetry 可以理解成：

```text
系统运行时自动产生的观测数据。
```

常见 telemetry 包括：

```text
traces
metrics
logs
profiles
```

现在你先记住前三个：

```text
traces  = 一次请求或任务经过了哪些步骤
metrics = 系统状态的数字统计
logs    = 一条条事件记录
```

例如用户点击“创建工单”：

```text
trace:
  这次请求从 FastAPI 到 Agent，再到 Java mock service 的完整链路

metrics:
  工单创建请求数、错误率、平均延迟、P95 延迟

logs:
  ticket_agent_started
  java_ticket_create_started
  ticket_agent_finished
```

OpenTelemetry 的价值不是只收集一种数据，而是让这些数据能关联。

例如：

```text
某次 trace 失败
点进去看到错误 span
再看到对应日志
再看到这段时间错误率上升
```

这就是可观测性数据打通后的价值。

### 3. 为什么 AI 项目也要学 OpenTelemetry

你现在做的是 AI 应用，但它不是孤立的大模型调用。

我们的项目已经包含：

```text
FastAPI Python AI 服务
LangGraph 智能工单 Agent
RAG 检索
Qdrant / Milvus 向量库
Java mock 业务服务
LLM API
工具调用
checkpoint 持久化
```

以后真实生产里还会有：

```text
网关
认证服务
订单服务
工单服务
消息队列
数据库
缓存
部署平台
日志平台
监控平台
```

AI 应用的问题通常不是一句“模型答错了”就能解释。

可能是：

```text
HTTP 请求没到服务
用户身份没解析出来
Agent 路由错了
RAG 没检索到资料
向量数据库超时
模型调用失败
工具参数校验失败
Java 订单服务返回 500
checkpoint 过期
确认流程被拒绝
```

OpenTelemetry 帮你把这些服务和步骤串起来。

它回答的是：

```text
这次用户请求在整个系统里经历了什么？
```

LangSmith 更擅长回答：

```text
这次 LLM / Agent 运行里模型、prompt、工具、检索表现如何？
```

两个问题都重要。

### 4. OpenTelemetry 为什么叫 vendor-neutral

vendor 指厂商。

vendor-neutral 指：

```text
不绑定某一个厂商。
```

例如你可以用 OpenTelemetry 把 trace 导出到：

```text
Jaeger
Grafana Tempo
Datadog
New Relic
Honeycomb
Elastic APM
OpenTelemetry Collector
标准输出
```

代码里尽量使用 OTel 标准 API 和语义字段。

这样以后换平台时，核心业务代码不用大改。

如果没有这个中间层，你可能会在业务代码里到处写某个厂商 SDK：

```python
vendor_a.start_trace(...)
vendor_a.add_tag(...)
vendor_a.capture_exception(...)
```

以后想换成另一个平台，就要到处改。

OpenTelemetry 的理想方式是：

```text
业务代码用 OTel API 产生 telemetry。
Exporter / Collector 决定这些 telemetry 最终发到哪里。
```

### 5. OpenTelemetry 和 LangSmith 的区别

第 26 节我们已经学过 LangSmith。

现在把二者对比清楚。

| 维度 | LangSmith | OpenTelemetry |
| --- | --- | --- |
| 定位 | LLM / Agent 观测、调试、评测平台 | 通用可观测性标准和生态 |
| 重点 | prompt、模型调用、工具调用、RAG、eval、feedback | 跨服务 trace、span、metrics、logs、context propagation |
| 数据组织 | project、trace、run、thread、metadata、tags | trace、span、resource、attribute、event、status、context |
| 适用对象 | LLM 应用和 Agent 工作流 | 任意后端、前端、移动端、数据库、队列、微服务 |
| 平台绑定 | LangSmith 平台 | 不绑定具体平台 |
| 我们当前用途 | 看 Agent 内部推理链路和评测 | 连接 Python 服务、Java 服务、工具调用、HTTP 链路 |

一句话：

```text
LangSmith 更懂 LLM 应用。
OpenTelemetry 更懂分布式系统。
```

生产 AI 工程里经常两者都需要。

### 6. trace 是什么

trace 是一条完整链路。

例如用户请求：

```text
POST /agent/tickets
```

系统内部可能发生：

```text
FastAPI 接收请求
认证用户
调用 LangGraph Agent
识别意图
提取工单字段
请求用户确认
调用 Java mock 创建工单
返回响应
```

这些步骤应该属于同一条 trace。

trace 的核心特征是：

```text
一组相关 span 共享同一个 trace_id。
```

如果每个服务都生成自己的 trace_id，不传播上下文，你就只能看到一堆孤立片段：

```text
Python 有一条 trace
Java 有一条 trace
向量库有一条 trace
模型调用有一条 trace
```

但你不知道它们是否属于同一个用户请求。

OpenTelemetry 的目标是：

```text
让这些片段共享同一个 trace_id，并用 parent/child 关系组成完整链路。
```

### 7. span 是什么

span 是 trace 里的一个工作单元。

你可以把它理解成：

```text
一段有开始、有结束、有名称、有上下文、有属性的操作。
```

例如：

```text
HTTP POST /chat
ticket_agent.invoke_thread
ticket_agent.classify_intent
llm.intent_classification
rag.retrieve_policy
tool.query_order
http.client GET /orders/{order_id}
```

这些都可以是 span。

span 常见信息包括：

```text
name
trace_id
span_id
parent_span_id
start_time
end_time
attributes
events
status
span_kind
```

本节代码没有真正创建运行时 span。

我们先创建：

```text
TicketAgentOtelSpanPlan
```

它表示：

```text
如果以后接入 OTel SDK，这次 Agent 运行应该创建什么 span，带哪些 attributes，使用什么 trace context。
```

### 8. root span 和 child span

root span 是一条 trace 里最上层的 span。

它没有 parent span。

例如一次 HTTP 请求：

```text
trace_id=abc

root span:
  POST /agent/tickets

child span:
  ticket_agent.invoke_thread

child span:
  llm.intent_classification

child span:
  tool.query_order

child span:
  http.client GET /orders/{order_id}
```

父子关系非常重要。

它能告诉你：

```text
这个 Java 调用是哪个 Agent 节点发起的？
这个模型调用属于哪次 HTTP 请求？
这个错误是根因，还是上游错误导致的结果？
```

### 9. span kind 是什么

OpenTelemetry span kind 用来描述 span 在系统边界里的角色。

常见值：

```text
SERVER
CLIENT
INTERNAL
PRODUCER
CONSUMER
```

简单理解：

```text
SERVER   = 服务端接收请求
CLIENT   = 客户端发出请求
INTERNAL = 服务内部操作
PRODUCER = 生产消息
CONSUMER = 消费消息
```

放到我们的项目：

```text
FastAPI 接收 HTTP 请求             -> SERVER span
Agent 内部执行 invoke_thread       -> INTERNAL span
Python 调 Java mock service        -> CLIENT span
以后向队列发消息                   -> PRODUCER span
以后消费队列消息                   -> CONSUMER span
```

本节的 `TicketAgentOtelSpanPlan` 默认：

```text
span_kind = INTERNAL
```

因为 Agent 执行是 Python 服务内部的一段业务逻辑。

### 10. span attributes 是什么

attributes 是 span 上的 key-value 元数据。

它们用于描述这个 span 正在跟踪的操作。

例如：

```text
app.operation = invoke_thread
agent.intent = ticket_request
agent.node.count = 5
rag.citation.count = 2
ticket.creation.status = blocked
```

attributes 和第 26 节 LangSmith metadata 很像。

区别是：

```text
LangSmith metadata 更偏 LangSmith 平台里的 trace/run 筛选。
OTel attributes 更偏通用可观测性标准里的 span 描述。
```

attributes 也不能乱放。

它们应该：

```text
短
结构化
稳定命名
低敏感
适合过滤聚合
```

不应该直接放：

```text
用户原始问题
模型完整回答
订单查询完整结果
工单详细描述
知识库 chunk 全文
```

### 11. span events 是什么

span event 是 span 里的某个时间点事件。

它更像：

```text
带时间戳的结构化日志点。
```

例如在一个 Agent span 里：

```text
event: intent_classified
event: tool_call_requested
event: ticket_confirmation_interrupted
event: fallback_used
```

什么时候用 attribute，什么时候用 event？

简单判断：

```text
描述整个操作的状态 -> attribute
描述某个具体时间点发生的事情 -> event
```

例如：

```text
agent.intent = ticket_request
```

适合作为 attribute。

而：

```text
ticket_confirmation_requested at 10:03:21
```

更像 event。

本节先不做 events。

因为我们还没正式接入 OTel SDK。

### 12. span status 是什么

span status 用来表达这个 span 最终状态。

常见：

```text
UNSET
OK
ERROR
```

初学者容易以为成功就应该写 OK。

但在 OTel 里，很多成功 span 可以保持默认的 `UNSET`，只有明确要表达成功状态时才设置 OK。

错误时应该设置：

```text
ERROR
```

本节代码规则很保守：

```text
如果 state 里有 agent_error_code -> ERROR
如果 state 里有 ticket_creation_error_code -> ERROR
如果 ticket_creation_status == failed -> ERROR
否则 -> UNSET
```

这让错误 span 能被观测系统筛出来。

### 13. trace_id 是什么

OpenTelemetry 的 trace_id 是：

```text
32 位十六进制字符串
不能全 0
```

例如：

```text
4bf92f3577b34da6a3ce929d0e0e4736
```

注意：

```text
我们项目自己的 X-Trace-Id 不一定总是合法 OTel trace_id。
```

例如用户传：

```text
X-Trace-Id: client-trace-001
```

这在我们项目日志里可以用。

但它不是合法 OpenTelemetry trace_id。

所以本节代码做了区分：

```text
app.trace_id      = 我们项目自己的 trace_id，可以是 client-trace-001
otel trace_id     = OpenTelemetry 要求的 32 位十六进制 trace_id
```

如果项目 trace_id 本来就是 32 位十六进制，就可以复用。

如果不是，就生成一个新的 OTel trace_id。

这个区别非常重要。

### 14. span_id 是什么

span_id 是：

```text
16 位十六进制字符串
不能全 0
```

trace_id 标识整条链路。

span_id 标识链路中的某一步。

例如：

```text
trace_id = 一次用户请求
span_id  = 这次请求里的 Agent 执行步骤
```

每个 span 都应该有自己的 span_id。

child span 会记录 parent span 的 span_id。

这样观测平台才能知道父子关系。

### 15. traceparent 是什么

`traceparent` 是 W3C Trace Context 里定义的 HTTP header。

格式是：

```text
version-trace-id-parent-id-trace-flags
```

例如：

```text
00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

拆开看：

```text
00                                version
4bf92f3577b34da6a3ce929d0e0e4736  trace-id
00f067aa0ba902b7                  parent-id
01                                trace-flags
```

其中：

```text
trace-id   = 整条 trace 的 ID
parent-id  = 发送方当前 span 的 ID
trace-flags = 标志位，目前最常见的是 sampled 位
```

如果 Python 服务调用 Java 服务，Python 应该把当前 span context 注入到 HTTP header：

```text
traceparent: 00-...-...-01
```

Java 服务收到后，提取这个 header，然后创建自己的 child span。

这样两边就属于同一条 trace。

### 16. trace-flags 和 sampled 是什么

`trace-flags` 是 2 位十六进制。

最常见：

```text
01 = sampled
00 = not sampled
```

sampled 可以简单理解成：

```text
这条 trace 是否应该被采样并上报。
```

为什么需要采样？

因为生产流量可能很大。

如果每个请求、每个 span 都完整上报，可能导致：

```text
性能开销大
存储成本高
观测平台数据太多
真正的问题反而不好找
```

所以生产系统经常会做：

```text
采样
只保留错误 trace
只保留慢请求 trace
按用户或租户采样
按接口或环境采样
```

本节只做 sampled flag 的保留和生成，不讲复杂采样策略。

### 17. context propagation 是什么

context propagation 是上下文传播。

它解决的问题是：

```text
一个请求跨过多个服务后，怎么仍然属于同一条 trace？
```

例如：

```text
浏览器
  -> FastAPI
    -> LangGraph Agent
      -> Java order service
      -> LLM API
      -> Qdrant / Milvus
```

每一层都应该知道：

```text
当前 trace_id 是什么？
当前 parent span 是谁？
我创建的新 span 应该挂在哪个 parent 下面？
```

传播方式通常是：

```text
入口服务 extract context
内部创建 child span
调用下游服务时 inject context
下游服务 extract context
```

本节代码做的是最小手动版：

```text
parse_traceparent()
build_traceparent()
build_otel_trace_context()
```

以后真实项目里，更推荐用 OTel 自动 instrumentation 来做这些。

### 18. Resource 是什么

Resource 描述的是：

```text
产生 telemetry 的实体。
```

最常见就是服务本身。

例如：

```text
service.name = ai-service
service.namespace = java-python-ai
service.version = 0.1.0
deployment.environment.name = local
```

Resource attributes 不应该每个 span 都随便写一套。

它们通常在 SDK 初始化时配置一次。

本节代码用纯函数生成 resource attributes，是为了学习字段设计：

```python
build_ticket_agent_otel_resource_attributes()
```

以后接 SDK 时，这些字段会放到 Resource 配置里。

### 19. Semantic conventions 是什么

semantic conventions 是语义约定。

它解决的是字段命名统一问题。

例如：

```text
service.name
service.version
http.request.method
url.path
db.system.name
```

如果没有约定，不同团队可能会写：

```text
serviceName
service
app_name
application
svc
```

这些在人眼里意思差不多，但机器筛选时不是一回事。

OpenTelemetry 通过 semantic conventions 告诉你：

```text
常见概念应该用什么字段名。
```

本节遵守一个原则：

```text
官方已有语义字段时，用官方字段。
业务自定义字段时，用稳定命名空间。
```

例如：

```text
service.name                 官方语义字段
deployment.environment.name  官方语义字段
app.operation                项目自定义字段
agent.intent                 项目自定义字段
ticket.creation.status       项目自定义字段
rag.citation.count           项目自定义字段
```

### 20. API、SDK、Collector、Exporter、Backend 是什么

OpenTelemetry 生态里经常看到这些词。

它们非常容易混。

#### API

API 是业务代码调用的接口。

例如：

```python
tracer.start_as_current_span(...)
```

API 本身通常不负责真正导出数据。

#### SDK

SDK 是实现采集、处理、采样、导出的运行时。

如果只装 API，不配置 SDK，通常不会真的把数据发出去。

#### Instrumentation

instrumentation 是插桩。

意思是：

```text
给代码加上产生 telemetry 的逻辑。
```

可以手动：

```python
with tracer.start_as_current_span("ticket_agent.invoke_thread"):
    ...
```

也可以自动：

```text
FastAPI instrumentation
HTTPX instrumentation
SQLAlchemy instrumentation
```

#### Exporter

Exporter 负责把 telemetry 发出去。

例如：

```text
Console exporter
OTLP exporter
Jaeger exporter
Prometheus exporter
```

#### Collector

Collector 是一个独立进程或服务。

它可以：

```text
接收 telemetry
加工 telemetry
过滤 telemetry
采样 telemetry
转发 telemetry 到不同后端
```

Collector 的好处是：

```text
应用不需要知道最终平台是哪一个。
多个服务可以统一把数据发给 Collector。
Collector 再统一转发到 Jaeger、Tempo、Datadog 等后端。
```

#### Backend

Backend 是最终存储和展示 telemetry 的地方。

例如：

```text
Jaeger
Grafana Tempo
Datadog
Honeycomb
Elastic
```

一句话总结：

```text
API 让你写观测代码。
SDK 让观测代码真的运行。
Instrumentation 自动或手动产生数据。
Exporter 把数据导出。
Collector 负责集中接收和转发。
Backend 负责存储、查询和展示。
```

### 21. 自动插桩和手动插桩

自动插桩：

```text
框架或库帮你自动创建 span、注入和提取 context。
```

例如：

```text
FastAPI 自动生成 SERVER span
HTTPX 自动生成 CLIENT span
SQLAlchemy 自动生成 DB span
```

优点：

```text
接入快
不容易漏掉基础链路
字段更符合生态习惯
```

缺点：

```text
业务语义不够
不知道你的 Agent 节点是什么意思
不知道 ticket_creation_status 是什么
```

手动插桩：

```text
你自己在关键业务代码里创建 span、加 attributes、加 events。
```

优点：

```text
能表达业务语义
能记录 Agent 节点状态
能标记工单创建失败、确认阻断、fallback 等业务概念
```

缺点：

```text
需要设计规范
容易写乱
写太多会污染代码
```

真实项目里通常是：

```text
自动插桩负责基础框架和 HTTP 链路。
手动插桩负责核心业务节点和 AI/Agent 关键步骤。
```

---

## 四、本节主题系统讲解

### 1. 当前项目已有的可观测性能力

当前项目已经有：

```text
X-Trace-Id
请求日志
模型调用日志
工具调用日志
Agent 运行日志
LangSmith metadata / tags 准备
thread_id 生命周期
checkpoint 清理策略
```

这说明我们已经不是从 0 开始。

但是当前还缺：

```text
W3C traceparent 支持
OpenTelemetry trace_id / span_id 格式认知
resource attributes
span attributes 命名规范
span status 设计
未来跨 Python / Java 服务传播 trace context 的准备
```

本节新增模块：

```text
projects/ai-service/app/agents/otel_tracing.py
```

对应测试：

```text
projects/ai-service/tests/test_ticket_agent_otel_tracing.py
```

### 2. 为什么本节不直接安装 OpenTelemetry SDK

可以安装：

```text
opentelemetry-api
opentelemetry-sdk
opentelemetry-instrumentation-fastapi
opentelemetry-exporter-otlp
```

但本节暂时不做。

原因：

```text
1. 这节是基础概念课，不是接入课。
2. 当前项目还没有统一 Collector 和后端。
3. 先设计 attribute 字段，比先上报更重要。
4. 不引入依赖，测试更稳定。
5. 等第 28、29 节把 trace/log/metrics/生产日志字段讲清楚，再接真实 SDK 更合理。
```

所以本节代码是纯函数。

它不会：

```text
调用网络
读取 API key
启动 Collector
向外部平台发送数据
```

它只做：

```text
OpenTelemetry 风格上下文准备。
```

### 3. 本节新增能力总览

新增能力可以分成四组。

第一组：OpenTelemetry ID 规则。

```text
normalize_otel_trace_id()
normalize_otel_span_id()
generate_otel_trace_id()
generate_otel_span_id()
```

第二组：W3C traceparent。

```text
parse_traceparent()
build_traceparent()
build_otel_trace_context()
```

第三组：Agent 资源和 span attributes。

```text
build_ticket_agent_otel_resource_attributes()
build_ticket_agent_otel_span_attributes()
```

第四组：未来接 SDK 前的 span plan。

```text
TicketAgentOtelSpanPlan
build_ticket_agent_otel_span_plan()
```

### 4. 本节和第 26 节的关系

第 26 节：

```text
LangSmith tracing context
tags
metadata
project_name
run_name
```

第 27 节：

```text
OpenTelemetry trace context
traceparent
resource attributes
span attributes
span status
span kind
```

两者都在做“观测上下文”，但输出对象不同。

举例：

```text
LangSmith:
  tags = ["ai-service", "ticket-agent", "env:test"]
  metadata = {"trace_id": "...", "thread_id": "..."}

OpenTelemetry:
  span_name = "ticket_agent.invoke_thread"
  attributes = {"app.trace_id": "...", "agent.intent": "..."}
  traceparent = "00-...-...-01"
```

可以把它们理解成：

```text
LangSmith 关注 LLM/Agent 调试视角。
OpenTelemetry 关注通用分布式链路视角。
```

### 5. `OtelTraceParent`

代码：

```python
@dataclass(frozen=True)
class OtelTraceParent:
    version: str
    trace_id: str
    parent_id: str
    trace_flags: str
```

它表示解析后的 `traceparent` header。

例如：

```text
00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

会被解析成：

```text
version = 00
trace_id = 4bf92f3577b34da6a3ce929d0e0e4736
parent_id = 00f067aa0ba902b7
trace_flags = 01
```

它有一个属性：

```python
sampled
```

用于判断最低位是否表示 sampled。

还有：

```python
format()
```

用于重新拼回标准字符串。

### 6. `OtelTraceContext`

代码：

```python
@dataclass(frozen=True)
class OtelTraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    sampled: bool = True
```

它表示当前服务当前 span 的 trace context。

里面的字段含义：

```text
trace_id       当前整条链路 ID
span_id        当前 span ID
parent_span_id 上游 span ID
sampled        是否采样
```

它可以输出：

```python
to_traceparent()
to_headers()
```

注意：

```text
to_headers() 生成的 traceparent 里 parent-id 位置放的是当前 span_id。
```

为什么？

因为你把 header 发给下游服务时，下游看到的 parent 就是你当前这个 span。

### 7. `parse_traceparent()`

这个函数解析 W3C traceparent。

它会拒绝：

```text
格式不对
version 是 ff
trace_id 不是 32 位十六进制
trace_id 全 0
parent_id 不是 16 位十六进制
parent_id 全 0
```

例如合法：

```text
00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

非法：

```text
bad
ff-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
00-00000000000000000000000000000000-00f067aa0ba902b7-01
00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01
```

为什么非法时返回 `None`，而不是抛异常？

因为在真实 HTTP 请求里，外部传来的 tracing header 不可信。

更实用的处理方式是：

```text
能解析就继续上游 trace。
不能解析就开始新的 trace。
```

### 8. `build_traceparent()`

这个函数生成标准 `traceparent`。

例如：

```python
build_traceparent(
    trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
    span_id="00f067aa0ba902b7",
    sampled=False,
)
```

返回：

```text
00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-00
```

它会校验：

```text
trace_id 必须合法
span_id 必须合法
```

如果不合法，抛 `ValueError`。

这是因为：

```text
生成 outgoing header 是我们自己的行为。
我们不能主动生成不合法 header。
```

### 9. `build_otel_trace_context()`

这个函数处理三种场景。

场景一：有合法 incoming traceparent。

```text
复用 incoming trace_id
把 incoming parent-id 作为 parent_span_id
生成或使用当前 span_id
继承 incoming sampled 标志
```

场景二：没有合法 traceparent，但项目自己的 trace_id 是 OTel 合法格式。

```text
复用项目 trace_id 作为 OTel trace_id
生成当前 span_id
没有 parent_span_id
```

场景三：没有合法 traceparent，项目 trace_id 也不是 OTel 格式。

```text
生成新的 OTel trace_id
生成当前 span_id
项目 trace_id 仍然保存在 app.trace_id attribute 里
```

这个设计很现实。

因为我们项目里允许：

```text
X-Trace-Id: client-trace-001
```

但 OTel 需要：

```text
trace_id: 32 位十六进制
```

所以两者不能强行混为一谈。

### 10. `build_ticket_agent_otel_resource_attributes()`

这个函数生成资源属性：

```python
{
    "service.name": "ai-service",
    "service.namespace": "java-python-ai",
    "deployment.environment.name": "local",
    "service.version": "0.1.0",
}
```

这些字段描述：

```text
哪个服务产生了 telemetry？
属于哪个命名空间？
运行在哪个环境？
服务版本是什么？
```

以后真实接 SDK 时，这些字段应该放到 OpenTelemetry Resource。

本节先用函数生成，是为了让你看懂字段设计。

### 11. `build_ticket_agent_otel_span_attributes()`

这是本节核心函数。

它把 Agent state 整理成 OTel span attributes。

核心字段包括：

```text
otel.scope.name
app.component
app.operation
app.trace_id
app.thread_id
app.session_id
app.actor_id
agent.node.count
agent.node.last
agent.intent
ticket.need.source
order.query.status
rag.answer.status
ticket.field_extraction.source
ticket.fields.complete
ticket.confirmation.required
ticket.confirmation.approved
ticket.write_safety.status
ticket.creation.status
agent.error_code
agent.error_node
agent.fallback_used
rag.citation.count
ticket.missing_fields.count
app.elapsed_ms
```

它们都符合本节原则：

```text
短字段
状态字段
计数字段
错误码
内部关联 ID
不保存完整业务 payload
```

### 12. 为什么 attribute key 用点号分层

例如：

```text
agent.intent
agent.node.count
ticket.creation.status
order.query.status
rag.citation.count
```

这样写有几个好处：

```text
一眼能看出字段属于哪个领域
观测平台里可以按前缀搜索
团队容易维护字段规范
避免所有字段都堆成平铺杂项
```

例如你看到：

```text
ticket.creation.status
```

就知道它和工单创建有关。

看到：

```text
rag.citation.count
```

就知道它和 RAG 引用数量有关。

### 13. 为什么自定义 attributes 也要小心

本节支持：

```python
extra_attributes={...}
```

但它不能覆盖核心字段：

```text
app.trace_id
app.thread_id
app.actor_id
service.name
deployment.environment.name
```

原因：

```text
这些字段是可观测性定位的根基。
如果业务调用方能随便覆盖，trace 就不可信。
```

它也不会接收复杂对象：

```python
{"raw_payload": {"too": "large"}}
```

因为 attributes 应该是简单值。

本节只保留：

```text
str
int
float
bool
```

虽然 OTel 支持数组类型 attributes，但当前项目为了安全和学习清晰，先不放数组。

### 14. 为什么继续排除敏感 payload

第 26 节已经强调过。

第 27 节同样适用。

本节排除：

```text
user_message
normalized_message
rag_query
rag_answer
rag_citations
rag_suggestions
final_answer
ticket_fields
ticket_creation_args
created_ticket
order_query_result
pending_ticket_confirmation
```

为什么？

因为这些字段可能包含：

```text
手机号
地址
订单号
投诉内容
工单详情
知识库全文
模型完整回答
内部业务数据
```

OpenTelemetry attributes 不是数据库。

它们用于：

```text
过滤
聚合
定位
排查
```

不用于保存完整用户上下文。

### 15. `TicketAgentOtelSpanPlan`

这个 dataclass 表示：

```text
准备创建一个 OTel span 所需的信息。
```

字段：

```text
span_name
span_kind
status
attributes
trace_context
status_description
```

例如：

```text
span_name = ticket_agent.invoke_thread
span_kind = INTERNAL
status = ERROR
status_description = ORDER_QUERY_TIMEOUT
```

这不是 OpenTelemetry SDK 的真实 Span。

它只是：

```text
未来接 SDK 前的中间表示。
```

为什么这样设计？

因为本节暂时不接 SDK，但我们仍然要把 span 该长什么样设计清楚。

### 16. 如果以后真正接入 SDK，会怎么用

未来可能长这样：

```python
from opentelemetry import trace

tracer = trace.get_tracer("app.agents.ticket_agent")

plan = build_ticket_agent_otel_span_plan(
    state,
    operation="invoke_thread",
    thread_id=thread_id,
    actor_id=actor_id,
)

with tracer.start_as_current_span(
    plan.span_name,
    attributes=plan.attributes,
) as span:
    result = graph.invoke(...)
    if plan.status == "ERROR":
        span.set_status(...)
```

如果调用 Java 服务，未来还会把当前 context 注入 HTTP headers：

```text
traceparent: 00-...-...-01
```

然后 Java 服务就能继续同一条 trace。

本节不写这段真实接入代码，是因为：

```text
还没有引入 SDK
还没有 Collector
还没讲第 28 节 trace/span/log/metrics 的关系
还没讲第 29 节生产日志字段设计
```

### 17. 当前项目的映射表

| 当前项目概念 | OpenTelemetry 概念 | 本节字段 |
| --- | --- | --- |
| FastAPI 服务 | Resource / SERVER span | `service.name=ai-service` |
| Agent 运行 | INTERNAL span | `ticket_agent.invoke_thread` |
| 当前请求 ID | 自定义 attribute | `app.trace_id` |
| OTel 链路 ID | trace context | `trace_id` |
| 当前 span ID | trace context | `span_id` |
| 上游 span ID | parent context | `parent_span_id` |
| LangGraph thread | 自定义 attribute | `app.thread_id`、`app.session_id` |
| 用户或调用者 | 自定义 attribute | `app.actor_id` |
| Agent 意图 | 自定义 attribute | `agent.intent` |
| 节点路径摘要 | 自定义 attribute | `agent.node.count`、`agent.node.last` |
| RAG 引用数量 | 自定义 attribute | `rag.citation.count` |
| 工单创建状态 | 自定义 attribute | `ticket.creation.status` |
| 错误码 | span status + attribute | `agent.error_code`、`status=ERROR` |

### 18. 当前项目以后可能的 trace 结构

以后真实接入后，一次完整请求可能长这样：

```text
trace_id=4bf92f3577b34da6a3ce929d0e0e4736

SERVER span: POST /agent/tickets
  INTERNAL span: ticket_agent.invoke_thread
    INTERNAL span: ticket_agent.normalize_user_input
    INTERNAL span: ticket_agent.classify_intent
      CLIENT span: llm.intent_classification
    INTERNAL span: ticket_agent.extract_ticket_fields
      CLIENT span: llm.field_extraction
    INTERNAL span: ticket_agent.request_ticket_confirmation

第二次用户确认：

SERVER span: POST /agent/tickets/{thread_id}/confirm
  INTERNAL span: ticket_agent.resume_interrupt
    CLIENT span: java_ticket_create
```

如果第二次请求带着同一个 `traceparent`，它可以接到同一条 trace。

如果没有带，它可能是新 trace，但仍然可以通过：

```text
app.thread_id
app.session_id
```

和上一段业务会话关联。

这就是：

```text
trace_id 负责技术链路。
thread_id 负责业务会话。
```

二者不要混淆。

### 19. `X-Trace-Id` 和 `traceparent` 的关系

我们项目已有：

```text
X-Trace-Id
```

OpenTelemetry 标准使用：

```text
traceparent
tracestate
```

它们不是同一个东西。

对比：

| 字段 | 作用 | 格式 |
| --- | --- | --- |
| `X-Trace-Id` | 当前项目自定义请求关联 ID | 目前允许普通字符串 |
| `traceparent` | W3C 标准 trace context header | 固定 4 段格式 |

以后可以同时保留：

```text
X-Trace-Id   用于项目日志和排查习惯
traceparent  用于 OpenTelemetry 跨服务传播
```

如果 `X-Trace-Id` 是 32 位十六进制，可以作为 OTel trace_id。

如果不是，OTel 生成自己的 trace_id，同时把 `X-Trace-Id` 记录到：

```text
app.trace_id
```

这样日志和 trace 仍然能关联。

### 20. 这一节不学什么

本节不学：

```text
OpenTelemetry SDK 安装
FastAPI 自动插桩
HTTPX 自动插桩
OTLP exporter
OpenTelemetry Collector
Jaeger / Tempo 部署
Prometheus metrics
日志和 trace 自动关联
采样策略
生产脱敏中间件
```

这些都重要，但不是本节重点。

本节重点是：

```text
你看到 OpenTelemetry 这些词时，知道它们在系统里各自解决什么问题。
```

---

## 五、本节新增代码讲解

### 1. ID 校验函数

代码：

```python
normalize_otel_trace_id()
normalize_otel_span_id()
```

它们做：

```text
去空格
转小写
检查长度
检查十六进制
拒绝全 0
```

为什么要拒绝全 0？

因为 W3C Trace Context 明确规定：

```text
trace-id 和 parent-id 全 0 都是非法值。
```

这个细节很重要。

### 2. 生成函数

代码：

```python
generate_otel_trace_id()
generate_otel_span_id()
```

`trace_id` 使用：

```python
uuid4().hex
```

得到 32 位十六进制。

`span_id` 使用：

```python
token_hex(8)
```

得到 16 位十六进制。

为什么 span_id 不是 uuid？

因为 OTel span_id 只需要 8 字节，也就是 16 位 hex。

### 3. traceparent 解析和生成

代码：

```python
parse_traceparent()
build_traceparent()
```

解析函数用于入口：

```text
别人调用我，我读 incoming traceparent。
```

生成函数用于出口：

```text
我调用别人，我写 outgoing traceparent。
```

这是 context propagation 的两个方向：

```text
extract
inject
```

本节没有使用 OTel propagator API，而是手写最小解析，是为了学习。

真实项目优先用官方 instrumentation 和 propagator。

### 4. trace context 构建

代码：

```python
build_otel_trace_context()
```

它体现了一个很重要的生产逻辑：

```text
优先尊重上游传来的 traceparent。
如果没有上游 traceparent，再考虑复用项目 trace_id。
如果项目 trace_id 也不合法，就生成新的 OTel trace_id。
```

这个逻辑避免两个问题：

```text
无视上游 trace，导致链路断开。
强行把非法 X-Trace-Id 当 OTel trace_id，导致 trace context 不合法。
```

### 5. Resource attributes

代码：

```python
build_ticket_agent_otel_resource_attributes()
```

它输出：

```text
service.name
service.namespace
deployment.environment.name
service.version
```

这些字段属于服务级信息。

以后应该在 SDK 初始化时设置一次。

### 6. Span attributes

代码：

```python
build_ticket_agent_otel_span_attributes()
```

它把 Agent state 转成 OTel attributes。

注意字段命名：

```text
app.*     当前应用通用字段
agent.*   Agent 领域字段
ticket.*  工单领域字段
order.*   订单查询字段
rag.*     RAG 字段
```

这比随便写：

```text
intent
status
error
count
```

更清楚。

因为以后一个 span 上可能同时有：

```text
order.query.status
ticket.creation.status
rag.answer.status
```

如果都叫 `status`，你根本不知道哪个 status。

### 7. Span status 推导

代码：

```python
_infer_ticket_agent_span_status()
```

规则：

```text
有 agent_error_code -> ERROR
有 ticket_creation_error_code -> ERROR
ticket_creation_status == failed -> ERROR
否则 -> UNSET
```

为什么不是看到 `fallback_used=True` 就一定 ERROR？

因为 fallback 可能是错误后的结果，也可能是业务兜底策略。

当前项目里更明确的错误信号是：

```text
error_code
failed status
```

所以状态推导先看这些字段。

### 8. Span plan

代码：

```python
build_ticket_agent_otel_span_plan()
```

它组合：

```text
trace_context
span_name
span_kind
status
attributes
```

这样未来接真实 SDK 时，只要把 plan 映射到 SDK 调用即可。

---

## 六、本节测试讲解

测试文件：

```text
projects/ai-service/tests/test_ticket_agent_otel_tracing.py
```

本节测试重点是 5 类。

### 1. OTel ID 格式测试

测试：

```text
trace_id 必须 32 位 hex
span_id 必须 16 位 hex
全 0 不合法
普通字符串不合法
```

这让你真正记住 OTel ID 不是随便一个字符串。

### 2. traceparent 测试

测试：

```text
合法 traceparent 能解析
非法 traceparent 被拒绝
build_traceparent 能生成标准 header
```

这对应 W3C Trace Context。

### 3. context propagation 测试

测试：

```text
incoming traceparent 合法时，复用 trace_id 和 parent_span_id
outgoing headers 使用当前 span_id
sampled 标志跟随 incoming traceparent
```

这是跨服务链路追踪最核心的逻辑。

### 4. resource 和 span attributes 测试

测试：

```text
service.name 等 resource 字段正确
Agent 安全摘要字段进入 attributes
节点数量、最后节点、RAG 引用数量、缺失字段数量正确
```

这些字段决定以后排查是否方便。

### 5. 安全边界测试

测试确认：

```text
用户原始消息不进 attributes
模型回答不进 attributes
工单字段不进 attributes
订单结果不进 attributes
复杂对象不进 attributes
核心字段不能被 extra_attributes 覆盖
非法 thread_id 会被拒绝
```

这和第 26 节保持同一条安全原则。

---

## 七、本节练习

### 练习 1：解释 OpenTelemetry 是什么

问题：用自己的话解释 OpenTelemetry 是什么，它是不是一个观测平台？

参考答案：

```text
OpenTelemetry 是一套开源可观测性标准、API、SDK、工具和协议生态，用来统一生成、传播、收集和导出 traces、metrics、logs 等 telemetry 数据。
它本身不是某一个观测平台。它可以把数据导出到 Jaeger、Tempo、Datadog、Elastic 等不同后端。
```

### 练习 2：解释 trace 和 span 的关系

问题：trace 和 span 有什么区别？

参考答案：

```text
trace 是一次完整请求或任务的链路。
span 是 trace 里的一个工作单元。
多个 span 共享同一个 trace_id，并通过 parent_span_id 形成父子关系。
trace 是整体，span 是步骤。
```

### 练习 3：判断 span kind

问题：下面操作分别应该是什么 span kind？

```text
FastAPI 接收用户 HTTP 请求
Agent 内部执行 invoke_thread
Python 服务调用 Java order service
向消息队列发送一条任务消息
从消息队列消费一条任务消息
```

参考答案：

```text
FastAPI 接收用户 HTTP 请求 -> SERVER
Agent 内部执行 invoke_thread -> INTERNAL
Python 服务调用 Java order service -> CLIENT
向消息队列发送一条任务消息 -> PRODUCER
从消息队列消费一条任务消息 -> CONSUMER
```

### 练习 4：拆解 traceparent

问题：拆解下面这个 traceparent。

```text
00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

参考答案：

```text
version = 00
trace-id = 4bf92f3577b34da6a3ce929d0e0e4736
parent-id = 00f067aa0ba902b7
trace-flags = 01
```

解释：

```text
trace-id 表示整条链路。
parent-id 表示发送方当前 span。
01 通常表示 sampled。
```

### 练习 5：判断字段应该放在哪里

问题：下面字段适合放 resource attributes、span attributes，还是不应该直接放？

```text
service.name
deployment.environment.name
agent.intent
ticket.creation.status
user_message
final_answer
order_query_result
rag.citation.count
app.elapsed_ms
```

参考答案：

```text
service.name -> resource attributes
deployment.environment.name -> resource attributes
agent.intent -> span attributes
ticket.creation.status -> span attributes
user_message -> 不应该直接放
final_answer -> 不应该直接放
order_query_result -> 不应该直接放
rag.citation.count -> span attributes
app.elapsed_ms -> span attributes
```

解释：

```text
resource attributes 描述服务本身。
span attributes 描述某一次操作。
用户原文、模型完整回答、订单查询完整结果可能包含敏感信息，不应直接进入 attributes。
```

### 练习 6：解释 `X-Trace-Id` 和 `traceparent` 的区别

问题：我们的 `X-Trace-Id` 和 W3C `traceparent` 是不是一回事？

参考答案：

```text
不是。X-Trace-Id 是当前项目自定义请求关联 ID，可以是普通字符串。traceparent 是 W3C Trace Context 标准 header，有固定格式，包含 version、trace-id、parent-id、trace-flags。
如果 X-Trace-Id 是合法 32 位十六进制，可以复用为 OTel trace_id；如果不是，就应该生成新的 OTel trace_id，同时把 X-Trace-Id 保存在 app.trace_id attribute 里用于日志关联。
```

### 练习 7：设计一次跨服务链路

问题：用户请求 Python AI 服务，Python 调 Java mock service 查订单。你会如何传播 trace context？

参考答案：

```text
1. Python 服务入口读取 incoming traceparent。
2. 如果合法，复用 trace_id，创建 Python 当前 span。
3. Agent 执行 query_order 时创建 client span。
4. Python 调 Java mock service 时，在 HTTP headers 里注入 traceparent。
5. Java mock service 收到后 extract traceparent，创建自己的 server span。
6. 这样 Python 和 Java 的 span 共享同一个 trace_id，并形成父子关系。
```

---

## 八、自测题

### 自测 1：OpenTelemetry 是不是 LangSmith 的替代品？

答案：

```text
不是。OpenTelemetry 是通用可观测性标准和生态，LangSmith 是 LLM / Agent 观测、调试和评测平台。二者可以同时使用：OpenTelemetry 负责跨服务链路，LangSmith 负责 LLM/Agent 细节。
```

### 自测 2：span attributes 可以放任意对象吗？

答案：

```text
不应该。OTel attributes 应该是简单、稳定、低敏感的 key-value 数据。当前项目先只允许 str、int、float、bool，不放复杂对象、用户原文、模型回答、订单结果和工单详情。
```

### 自测 3：trace_id 和 span_id 的长度分别是多少？

答案：

```text
OpenTelemetry trace_id 是 32 位十六进制字符串。
span_id 是 16 位十六进制字符串。
二者都不能全 0。
```

### 自测 4：为什么 incoming traceparent 不合法时不应该继续用？

答案：

```text
因为不合法 traceparent 无法保证符合 W3C Trace Context，继续使用会污染链路追踪。正确做法是忽略它，创建新的 trace context。
```

### 自测 5：Resource attributes 和 span attributes 的区别是什么？

答案：

```text
Resource attributes 描述产生 telemetry 的服务或资源，例如 service.name、service.version、deployment.environment.name。
Span attributes 描述某一次操作，例如 agent.intent、ticket.creation.status、rag.citation.count。
```

### 自测 6：为什么 Agent span 默认用 INTERNAL？

答案：

```text
因为 Agent 执行是 Python AI 服务内部的一段业务流程，不是接收外部请求的 SERVER span，也不是调用下游服务的 CLIENT span。FastAPI 请求入口通常是 SERVER span，调用 Java 或模型 API 通常是 CLIENT span。
```

### 自测 7：OpenTelemetry Collector 是做什么的？

答案：

```text
Collector 是独立的 telemetry 接收和转发组件。应用可以把 traces、metrics、logs 发给 Collector，Collector 再统一做过滤、加工、采样和转发到 Jaeger、Tempo、Datadog 等后端。
```

### 自测 8：为什么这节不直接安装 SDK？

答案：

```text
因为本节目标是先理解 OpenTelemetry 的基础概念、ID 格式、traceparent、resource attributes、span attributes 和安全字段边界。直接安装 SDK 容易变成只会复制接入代码，不理解底层模型。
```

---

## 九、本节命令

在 `projects/ai-service` 目录运行：

```powershell
uv run pytest tests/test_ticket_agent_otel_tracing.py
```

本节当前测试结果：

```text
13 passed
```

提交前仍需要运行全量测试：

```powershell
uv run pytest
```

---

## 十、本节小结

本节你要真正掌握的是：

```text
1. OpenTelemetry 是通用可观测性标准，不是某个具体平台。
2. trace 是完整链路，span 是链路中的一步。
3. span 通过 trace_id、span_id、parent_span_id 形成层级。
4. traceparent 是 W3C 标准 HTTP header，用来跨服务传播 trace context。
5. Resource attributes 描述服务本身。
6. Span attributes 描述一次操作。
7. Semantic conventions 解决字段命名统一问题。
8. 自动插桩负责基础链路，手动插桩负责业务语义。
9. LangSmith 更偏 LLM/Agent 调试，OpenTelemetry 更偏分布式系统追踪。
10. 自定义 attributes 必须有安全边界，不能保存完整用户和业务 payload。
```

本节之后，当前项目已经具备：

```text
项目自定义 X-Trace-Id
LangSmith tracing 上下文准备
OpenTelemetry traceparent 解析和生成
OpenTelemetry trace_id / span_id 校验
OpenTelemetry resource attributes 设计
OpenTelemetry span attributes 设计
Agent span plan 准备
敏感 payload 排除策略
```

下一节进入：

```text
阶段 6 第 28 节：trace / span / log / metrics 的关系
```

下一节会把你现在学过的日志、LangSmith tracing、OpenTelemetry trace、metrics 放到一张完整图里讲清楚：

```text
一次请求应该怎么查？
一个错误应该怎么看日志？
一个接口变慢应该怎么看 span？
一个系统整体变差应该怎么看 metrics？
这些数据怎么用 trace_id 串起来？
```
