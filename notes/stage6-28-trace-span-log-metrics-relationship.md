# 阶段 6 第 28 节：trace / span / log / metrics 的关系

本节目标：真正理解 `trace`、`span`、`log`、`metrics` 四类观测信号分别回答什么问题、什么时候先看哪一个、它们如何用 `trace_id` / `span_id` / `thread_id` 串起来，并把这个关系落到当前智能工单 Agent 项目里。

这节不是为了堆新功能。

这节是为了把你前面学过的内容串成一张图：

```text
阶段 1：logging 日志、trace_id 请求追踪
阶段 2：模型调用日志、耗时、token
阶段 3：工具调用日志和 trace_id 串联
阶段 5：LangGraph 日志、trace_id 和可观测性
阶段 6 第 26 节：LangSmith tracing 基础
阶段 6 第 27 节：OpenTelemetry 基础
阶段 6 第 28 节：trace / span / log / metrics 的关系
```

如果你只会写日志，但不知道什么时候该看 trace、什么时候该看 metrics，生产排查会很慢。

如果你只会看 trace，但不会看 metrics，就很难判断这是一个用户的个例，还是系统整体开始变差。

如果你只会看 metrics，但不会回到具体日志和 span，就只能知道“有问题”，不知道“哪里有问题”。

---

## 一、本节在主线里的位置

阶段 6 第 26-29 节是一组完整的可观测性基础：

```text
第 26 节：LangSmith tracing 基础
第 27 节：OpenTelemetry 基础
第 28 节：trace / span / log / metrics 的关系
第 29 节：生产日志字段设计
```

第 26 节解决：

```text
LLM / Agent 应用怎么被 LangSmith 看见？
```

第 27 节解决：

```text
通用后端系统怎么用 OpenTelemetry 标准描述 trace/span/context？
```

第 28 节解决：

```text
trace、span、log、metrics 这些信号之间到底怎么配合？
```

第 29 节会继续解决：

```text
生产日志字段应该怎么设计，才能和 trace、metrics 配合？
```

本节做的是承上启下。

---

## 二、官方资料确认

本节参考了 OpenTelemetry 官方文档：

- OpenTelemetry Signals: https://opentelemetry.io/docs/concepts/signals/
- OpenTelemetry Traces: https://opentelemetry.io/docs/concepts/signals/traces/
- OpenTelemetry Metrics: https://opentelemetry.io/docs/concepts/signals/metrics/
- OpenTelemetry Logs: https://opentelemetry.io/docs/concepts/signals/logs/
- OpenTelemetry Logging specification: https://opentelemetry.io/docs/specs/otel/logs/
- OpenTelemetry Context propagation: https://opentelemetry.io/docs/concepts/context-propagation/

官方文档确认了几个关键点：

```text
1. Traces 表示请求穿过应用的路径。
2. Metrics 是运行时捕获的测量值。
3. Logs 是事件记录。
4. Span 是 trace 的基本构建块，表示一个工作单元。
5. Span 可以包含 name、parent span id、时间戳、span context、attributes、events、status 等信息。
6. Metrics 可以用 counter、gauge、histogram 等 instrument 表示。
7. Metrics 的 cardinality 会影响内存和成本，高基数字段要谨慎。
8. OpenTelemetry 可以把现有 logs 和当前 active trace/span 自动关联。
9. 日志可以通过 TraceId 和 SpanId 与对应的 trace/span 直接关联。
10. logs、traces、metrics 可以按时间和执行上下文关联。
```

这说明本节不是随便规定一套说法。

我们是在 OpenTelemetry 的信号模型上，结合当前智能工单 Agent 的业务特点，设计自己的学习版观测关系。

---

## 三、基础知识铺垫

### 1. 什么是观测信号

观测信号就是系统运行时发出来的证据。

英文里常叫：

```text
observability signals
telemetry signals
```

它们不是业务功能本身。

它们是帮你回答：

```text
系统运行得怎么样？
用户请求经历了什么？
哪里慢了？
哪里错了？
错误影响范围有多大？
这是不是偶发？
```

常见四类：

```text
trace
span
log
metrics
```

先给一个非常直观的比喻：

```text
trace   = 一次完整行程路线图
span    = 路线图上的一段路
log     = 路上某个时间点发生的一条记录
metrics = 很多次行程统计出来的数据
```

例如你从家去公司：

```text
trace:
  家 -> 地铁站 -> 地铁 -> 公司楼下 -> 工位

span:
  家 -> 地铁站
  地铁站 -> 公司楼下
  公司楼下 -> 工位

log:
  08:15 进入地铁站
  08:20 地铁晚点
  08:45 到达公司楼下

metrics:
  最近 30 天平均通勤时间
  今天地铁晚点率
  每周迟到次数
```

系统排查也是一样。

### 2. trace 是什么

trace 是一次请求或任务的完整路径。

在我们的项目里，一次用户问题可能经历：

```text
FastAPI 接收请求
创建 trace_id
进入 LangGraph Agent
识别意图
RAG 检索
工具调用
Java mock 订单查询
请求用户确认
创建工单
返回答案
```

这条完整路径就是 trace。

trace 回答的问题是：

```text
这次请求经过了哪些步骤？
哪一步失败了？
哪一步最慢？
它调用了哪些下游？
有没有绕路？
有没有走错分支？
```

trace 适合排查：

```text
一次具体请求为什么慢
一次具体请求为什么失败
某个用户反馈的那次到底发生了什么
跨 Python / Java / 模型 / 向量库的链路
```

trace 不适合直接回答：

```text
最近 1 小时错误率是多少？
P95 延迟是多少？
今天总共多少次 ticket_request？
```

这些是 metrics 更擅长的。

### 3. span 是什么

span 是 trace 里的一个工作单元。

trace 是一整条链路。

span 是链路中的一段。

例如：

```text
trace: 用户要求创建工单

span: FastAPI POST /tickets
span: ticket_agent.invoke_thread
span: classify_intent
span: llm.intent_classification
span: extract_ticket_fields
span: request_ticket_confirmation
span: java_ticket_create
```

span 回答的问题是：

```text
这一步叫什么？
它属于哪条 trace？
它的父 span 是谁？
它从什么时候开始？
到什么时候结束？
它耗时多久？
它成功还是失败？
它带了哪些 attributes？
```

如果 trace 是总路线图，span 就是路线图上的每一段路。

### 4. root span 和 child span

一条 trace 里通常有一个 root span。

root span 没有父 span。

例如：

```text
POST /agent/tickets
```

它下面可以有 child span：

```text
ticket_agent.invoke_thread
  classify_intent
    llm.intent_classification
  query_order
    http.client GET /orders/{order_id}
```

父子关系能告诉你：

```text
这个模型调用属于哪次 Agent 执行？
这个 Java API 调用是哪个节点发起的？
这个错误是自己失败，还是下游失败传上来的？
```

### 5. span attributes 是什么

span attributes 是 span 上的结构化字段。

例如：

```text
app.operation = invoke_thread
agent.intent = ticket_request
ticket.creation.status = blocked
rag.citation.count = 2
agent.error_code = ORDER_QUERY_TIMEOUT
```

它们回答：

```text
这一步处理的是什么业务？
它的关键状态是什么？
有什么可筛选字段？
```

attributes 不应该放用户原文、模型完整回答、订单完整结果。

原因和第 26、27 节一样：

```text
敏感
体积大
不适合聚合
不适合筛选
容易造成数据泄漏
```

### 6. log 是什么

log 是某个时间点发生的一条事件记录。

例如：

```text
ticket_agent_started operation=invoke_thread
ticket_agent_finished operation=invoke_thread elapsed_ms=42.13
ticket_agent_failed operation=invoke_thread error_code=ORDER_QUERY_TIMEOUT
```

log 回答的问题是：

```text
某一刻发生了什么？
代码做了什么决定？
错误细节是什么？
当时有哪些上下文字段？
```

log 适合排查：

```text
具体错误原因
条件判断细节
模型输出解析失败原因
工具调用异常栈
fallback 为什么触发
某个节点当时的业务决策
```

log 的缺点：

```text
太多时难找
孤立日志缺少上下级关系
只看日志很难判断整体趋势
日志字段如果不规范，后续搜索很痛苦
```

### 7. structured log 是什么

structured log 是结构化日志。

普通日志可能是：

```text
用户下单失败了
```

结构化日志是：

```json
{
  "event": "ticket_agent_failed",
  "trace_id": "trace-001",
  "thread_id": "ticket-thread-001",
  "operation": "invoke_thread",
  "error_code": "ORDER_QUERY_TIMEOUT",
  "elapsed_ms": 305.13
}
```

结构化日志更适合生产排查。

因为它可以按字段查：

```text
trace_id = trace-001
error_code = ORDER_QUERY_TIMEOUT
operation = invoke_thread
elapsed_ms > 300
```

这就是为什么我们一直强调日志字段。

### 8. metrics 是什么

metrics 是运行时测量数据。

它不是某一次请求的完整细节。

它更像统计指标。

例如：

```text
ticket_agent.invocations 总调用次数
ticket_agent.errors 错误次数
ticket_agent.duration 延迟分布
ticket_agent.node.count 节点数量分布
```

metrics 回答的问题是：

```text
系统整体表现怎么样？
最近 5 分钟错误率有没有升高？
P95 延迟有没有升高？
某个操作调用次数是否异常？
哪类 intent 最常见？
```

metrics 适合：

```text
报警
仪表盘
趋势分析
容量规划
SLO / SLA
对比版本上线前后表现
```

metrics 不适合：

```text
直接解释某一个用户为什么失败
查看模型具体输出
查看某次 Java API 返回什么
查看某次工单字段抽取内容
```

这些要回到 trace / span / log。

### 9. counter、gauge、histogram 是什么

metrics 有不同 instrument。

#### Counter

counter 是只增不减的计数。

例如：

```text
ticket_agent.invocations
ticket_agent.errors
llm.calls
tool.query_order.calls
```

适合回答：

```text
发生了多少次？
错误次数是多少？
调用次数是多少？
```

#### Gauge

gauge 是某一刻的当前值。

例如：

```text
active_threads
queue_length
current_memory_usage
```

适合回答：

```text
现在是多少？
```

#### Histogram

histogram 是分布统计。

例如：

```text
ticket_agent.duration
llm.call.duration
rag.retrieve.duration
```

适合回答：

```text
平均耗时是多少？
P95 是多少？
多少请求小于 1 秒？
慢请求集中在哪个区间？
```

我们本节用：

```text
counter   记录调用次数和错误次数
histogram 记录耗时和节点数量分布
```

### 10. 什么是 cardinality

cardinality 是基数。

在 metrics 里，cardinality 指：

```text
某个 metric 的 attributes 组合有多少种不同取值。
```

例如 metric：

```text
ticket_agent.invocations
```

如果 attributes 是：

```text
operation=invoke_thread
intent=ticket_request
status=ok
```

组合数量很有限。

这叫低基数。

如果 attributes 是：

```text
thread_id=ticket-thread-uuid...
trace_id=...
actor_id=user-001
```

每个请求、每个用户、每个会话都可能不同。

这叫高基数。

高基数字段放进 metrics 会导致：

```text
时间序列爆炸
内存成本增加
存储成本增加
查询变慢
仪表盘难维护
```

所以本节代码刻意规定：

```text
metrics 不放 trace_id、span_id、thread_id、actor_id。
```

但 logs 可以放这些字段。

因为 logs 是事件记录，天然按条存储。

trace/span 也可以放这些字段用于关联。

### 11. 为什么 metrics 不放 trace_id

这是生产可观测性里非常重要的一点。

很多初学者会想：

```text
既然 trace_id 可以关联所有东西，那我把 trace_id 也放到 metrics 里不就好了？
```

不应该。

原因：

```text
trace_id 每次请求都不同。
如果放进 metrics attributes，就会为每个请求生成一条新的时间序列。
```

metrics 的价值是聚合。

例如：

```text
ticket_agent.duration{operation=invoke_thread,intent=ticket_request,status=ok}
```

它聚合很多请求。

如果加上：

```text
trace_id=每次都不同
```

它就失去聚合意义。

正确做法：

```text
metrics 看整体趋势。
trace/log 用 trace_id 查单次请求。
```

### 12. correlation 是什么

correlation 是关联。

在可观测性里，它表示：

```text
不同信号之间怎么互相跳转、互相解释。
```

例如：

```text
metrics 发现错误率升高
  -> 找几条 error traces
    -> 打开 trace 看失败 span
      -> 用 trace_id/span_id 查日志
        -> 看具体错误码和上下文
```

或者：

```text
用户提供 trace_id
  -> 查日志定位请求
    -> 打开对应 trace
      -> 看失败 span
        -> 再看 metrics 判断是不是大面积问题
```

这就是信号之间的配合。

### 13. `trace_id`、`span_id`、`thread_id` 的区别

这三个很容易混。

#### trace_id

`trace_id` 表示一次技术链路。

例如：

```text
一次 HTTP 请求从 Python 到 Java 到模型服务。
```

#### span_id

`span_id` 表示链路中的某一个步骤。

例如：

```text
ticket_agent.invoke_thread 这个 span。
```

#### thread_id

`thread_id` 表示业务会话或可恢复流程。

例如：

```text
用户创建工单过程中，中断等待确认，再回来继续。
```

它们的关系：

```text
一次 thread 可能包含多次 trace。
一次 trace 包含多个 span。
一个 span 可以产生多条 log。
metrics 聚合很多 trace/span/log 的结果。
```

### 14. app_trace_id 和 otel_trace_id 的区别

我们项目里有：

```text
X-Trace-Id
```

这可以是：

```text
client-trace-001
```

但 OpenTelemetry 的 trace_id 要求：

```text
32 位十六进制，不能全 0。
```

所以本节代码区分：

```text
app_trace_id  = 当前项目自定义 trace_id
otel_trace_id = OpenTelemetry 标准 trace_id
```

如果 `app_trace_id` 本来合法，可以复用为 `otel_trace_id`。

如果不合法，则：

```text
otel_trace_id 生成新的标准 ID
app_trace_id 仍然进入 logs/span attributes 作为项目关联字段
```

### 15. 为什么 log 可以带 trace_id，metrics 不带

因为 log 和 metric 的用途不同。

log 是事件：

```text
这一条日志属于哪个请求？
```

所以它适合带：

```text
trace_id
span_id
thread_id
actor_id
```

metric 是聚合：

```text
这一类请求整体表现怎么样？
```

所以它不适合带每次都不同的字段。

metrics 适合带：

```text
operation
intent
status
error_code
ticket_creation_status
```

这些取值有限，适合分组。

---

## 四、本节主题系统讲解

### 1. 当前项目里的四类信号

当前智能工单 Agent 可以这样映射：

| 信号 | 当前项目里的例子 | 回答什么问题 |
| --- | --- | --- |
| trace | 一次 `/chat` 或 Agent 调用完整链路 | 这次请求走过哪些步骤 |
| span | `ticket_agent.invoke_thread`、`query_order`、`java_ticket_create` | 某一步耗时、状态和属性 |
| log | `ticket_agent_started`、`ticket_agent_finished`、`ticket_agent_failed` | 某个时间点发生什么 |
| metrics | `ticket_agent.invocations`、`ticket_agent.errors`、`ticket_agent.duration` | 整体调用量、错误率、延迟趋势 |

不要把它们混成一团。

### 2. 一次 Agent 请求应该有哪些信号

假设用户说：

```text
订单 A1001 一直没发货，帮我创建工单
```

系统可能生成：

```text
trace:
  trace_id=4bf92f...
  root_operation=invoke_thread
  status=UNSET

span:
  name=ticket_agent.invoke_thread
  span_id=5fb397...
  attributes:
    agent.intent=ticket_request
    ticket.write_safety.status=confirmation_required
    ticket.creation.status=blocked

logs:
  ticket_agent_started
  ticket_agent_finished

metrics:
  ticket_agent.invocations +1
  ticket_agent.duration observe 42.13ms
  ticket_agent.node.count observe 2
```

这些信号分别有自己的用处。

### 3. 如果用户说“刚才失败了”，先看什么

如果是一个用户反馈：

```text
刚才创建工单失败了
```

你优先看：

```text
log -> trace -> span -> metrics
```

原因：

```text
这是一个具体用户的具体请求。
先用 trace_id/thread_id 在日志里找到那次请求。
再打开 trace 看完整路径。
再看失败 span 的 attributes 和 status。
最后看 metrics 判断是不是大面积问题。
```

所以本节代码里：

```python
build_ticket_agent_investigation_steps("one_user_failed")
```

返回顺序就是：

```text
log
trace
span
metric
```

### 4. 如果接口整体变慢，先看什么

如果你发现：

```text
最近 10 分钟 Agent 响应明显变慢
```

你优先看：

```text
metrics -> trace -> span -> log
```

原因：

```text
这是整体趋势问题。
先看 duration histogram，确认 P50/P95/P99 是否变高。
再抽取慢 trace。
再看慢 trace 里哪个 span 慢。
最后看日志解释具体慢的原因。
```

所以本节代码里：

```python
build_ticket_agent_investigation_steps("latency_regression")
```

返回顺序就是：

```text
metric
trace
span
log
```

### 5. 如果错误率升高，先看什么

如果监控报警：

```text
ticket_agent.errors / ticket_agent.invocations 错误率升高
```

优先看：

```text
metrics -> trace -> span -> log
```

原因：

```text
报警来自 metrics。
先确认哪个 operation、intent、error_code 上升。
再找代表性 failing traces。
再看失败 span。
最后看日志确认具体异常细节。
```

错误率问题不是先去翻全量日志。

因为日志太多，容易淹没重点。

### 6. 如果要解释 Agent 为什么这么决策，先看什么

如果问题是：

```text
为什么用户说退款，Agent 却走了工单流程？
为什么没有直接创建工单，而是要求确认？
为什么 RAG 没答上来？
```

优先看：

```text
trace -> span -> log -> metrics
```

原因：

```text
这是单次 Agent 决策路径问题。
先看 trace 路由。
再看 span attributes：intent、last_node、ticket.write_safety.status。
再看日志里的点状事件。
metrics 只用来判断这种决策是否常见。
```

所以本节代码里：

```python
build_ticket_agent_investigation_steps("agent_decision_debug")
```

返回顺序就是：

```text
trace
span
log
metric
```

### 7. 为什么本节新增一个 signals 模块

本节新增：

```text
projects/ai-service/app/agents/observability_signals.py
```

它不是正式的监控系统。

它是学习用的建模模块。

它把一次 Agent 运行整理成：

```text
TicketAgentTraceSignal
TicketAgentSpanSignal
TicketAgentLogSignal
TicketAgentMetricSignal
TicketAgentSignalCorrelation
```

这样你能从代码上看到：

```text
同一份 Agent state，怎么产生不同类型的观测信号。
```

### 8. `TicketAgentSignalCorrelation`

这个类保存关联字段：

```python
app_trace_id
otel_trace_id
span_id
thread_id
actor_id
```

为什么要有它？

因为四类信号之间必须能互相跳转。

例如：

```text
日志里有 trace_id、span_id
trace 里有 otel_trace_id
span 里有 span_id 和 attributes
thread_id 关联多轮业务会话
```

本节代码里，日志会带这些字段。

metrics 不带这些字段。

这就是本节最重要的实践之一。

### 9. `TicketAgentTraceSignal`

这个类表示 trace 层面的摘要：

```python
trace_id
app_trace_id
root_operation
thread_id
span_count
status
```

它回答：

```text
这条链路是谁？
它对应哪个项目 trace_id？
它属于哪个业务 thread？
它大概有多少 span？
它状态是不是错误？
```

当前学习代码里 `span_count=1`。

因为我们还没有真正接 OpenTelemetry SDK，也没有收集多个 child span。

以后真实接入后，一条 trace 里会有多个 span。

### 10. `TicketAgentSpanSignal`

这个类表示一个 span：

```python
name
span_id
parent_span_id
status
kind
attributes
```

它来自第 27 节的：

```python
TicketAgentOtelSpanPlan
```

span attributes 包括：

```text
agent.intent
agent.node.last
ticket.creation.status
ticket.write_safety.status
rag.citation.count
app.elapsed_ms
```

这类字段用于理解：

```text
Agent 这一步到底在做什么？
业务状态是什么？
有没有错误？
```

### 11. `TicketAgentLogSignal`

这个类表示一条结构化日志事件：

```python
event_name
severity
message_template
fields
```

例如成功：

```text
ticket_agent_started
ticket_agent_finished
```

失败：

```text
ticket_agent_started
ticket_agent_failed
```

日志字段会带：

```text
trace_id
otel_trace_id
span_id
thread_id
actor_id
operation
intent
error_code
elapsed_ms
```

但不会带：

```text
user_message
final_answer
order_query_result
ticket_fields
```

### 12. `TicketAgentMetricSignal`

这个类表示一个 metric 数据点：

```python
name
kind
value
unit
attributes
description
```

本节生成：

```text
ticket_agent.invocations counter
ticket_agent.errors counter
ticket_agent.duration histogram
ticket_agent.node.count histogram
```

metric attributes 只保留低基数字段：

```text
operation
status
intent
ticket_creation_status
ticket_write_safety_status
rag_answer_status
order_query_status
error_code
```

不保留：

```text
trace_id
span_id
thread_id
actor_id
```

### 13. 本节代码和真实生产系统的区别

本节代码是：

```text
学习建模
```

不是：

```text
正式 telemetry exporter
```

真实系统里：

```text
logs 会进入日志系统
traces/spans 会进入 OTel SDK / Collector / 后端
metrics 会进入 metrics pipeline
```

本节只是先用纯 Python 数据结构表达：

```text
同一次 Agent 运行应该产生哪些信号。
这些信号之间如何关联。
哪些字段适合哪类信号。
排查问题时先看哪个。
```

### 14. 为什么不把所有信息都塞进一种信号

你可能会问：

```text
能不能所有东西都写日志？
```

可以，但不好。

因为：

```text
日志适合细节，不适合趋势。
```

也可能问：

```text
能不能所有东西都塞 span attributes？
```

不行。

因为：

```text
span attributes 适合描述操作，不适合保存大量事件细节。
```

还可能问：

```text
能不能所有东西都做 metrics？
```

更不行。

因为：

```text
metrics 适合聚合，不适合单次请求细节。
```

正确做法是：

```text
不同信号做不同工作。
通过 correlation 把它们关联起来。
```

---

## 五、本节新增代码讲解

### 1. 新增文件

```text
projects/ai-service/app/agents/observability_signals.py
projects/ai-service/tests/test_ticket_agent_observability_signals.py
```

### 2. `ObservabilitySignalType`

代码：

```python
ObservabilitySignalType = Literal["trace", "span", "log", "metric"]
```

它明确本节只讨论四类信号。

这样在排查步骤里，不会随便写成：

```text
tracing
logs
metric
events
```

字段稳定，学习也稳定。

### 3. `TicketAgentSignalCorrelation.log_fields()`

这个方法生成日志应该携带的关联字段：

```python
{
    "trace_id": app_trace_id,
    "otel_trace_id": otel_trace_id,
    "span_id": span_id,
    "thread_id": thread_id,
    "actor_id": actor_id,
}
```

这说明：

```text
日志应该方便你跳到 trace/span，也应该方便你按业务 thread 查。
```

但注意：

```text
这些字段不会进入 metrics attributes。
```

### 4. `build_ticket_agent_observability_signals()`

这个函数是本节核心。

它输入：

```text
Agent state
operation
thread_id
actor_id
traceparent
span_id
elapsed_ms
```

输出：

```text
correlation
trace
span
logs
metrics
```

也就是把同一次 Agent 运行拆成四类观测信号。

它内部复用第 27 节的：

```python
build_ticket_agent_otel_span_plan()
```

这说明知识是连续的：

```text
第 27 节设计 span plan。
第 28 节把 span plan 和 logs/metrics 关联起来。
```

### 5. `_build_log_signals()`

这个函数生成：

成功时：

```text
ticket_agent_started
ticket_agent_finished
```

失败时：

```text
ticket_agent_started
ticket_agent_failed
```

为什么不只写一条日志？

因为 started 和 finished/failed 是两个不同事件。

它们回答不同问题：

```text
started：请求是否进入了 Agent？
finished/failed：请求最终结果是什么？
```

### 6. `_build_metric_signals()`

这个函数生成：

```text
ticket_agent.invocations
ticket_agent.errors
ticket_agent.duration
ticket_agent.node.count
```

设计原因：

```text
invocations 看调用量
errors 看错误数
duration 看延迟分布
node.count 看 Agent 运行复杂度
```

这些都是聚合指标。

### 7. `_build_low_cardinality_metric_attributes()`

这个函数体现 metrics 的关键规则：

```text
metrics 只保留低基数字段。
```

保留：

```text
operation
status
intent
ticket_creation_status
ticket_write_safety_status
rag_answer_status
order_query_status
```

过滤：

```text
trace_id
span_id
otel_trace_id
thread_id
session_id
actor_id
```

这不是随便做的。

这是为了避免 metrics 时间序列爆炸。

### 8. `build_ticket_agent_investigation_steps()`

这个函数表达排查顺序。

它支持：

```text
one_user_failed
latency_regression
error_rate_regression
agent_decision_debug
```

每种问题的入口不同。

例如：

```text
one_user_failed -> log -> trace -> span -> metric
latency_regression -> metric -> trace -> span -> log
```

这就是本节真正希望你掌握的能力：

```text
不是所有问题都从日志开始。
不是所有问题都从 metrics 开始。
要看问题类型。
```

---

## 六、本节测试讲解

测试文件：

```text
projects/ai-service/tests/test_ticket_agent_observability_signals.py
```

### 1. 四类信号能关联

测试确认：

```text
correlation 有 app_trace_id、otel_trace_id、span_id、thread_id、actor_id
trace 使用 otel_trace_id
span 有 span_id 和 attributes
logs 有 started/finished
metrics 有 invocations/duration/node.count
```

这验证四类信号不是孤立的。

### 2. logs 有关联 ID，但不放敏感 payload

测试确认日志有：

```text
trace_id
otel_trace_id
span_id
thread_id
```

但没有：

```text
user_message
final_answer
order_query_result
```

这符合生产日志安全原则。

### 3. metrics 使用低基数字段

测试确认 metrics 有：

```text
operation
status
intent
ticket_creation_status
ticket_write_safety_status
```

没有：

```text
trace_id
span_id
thread_id
actor_id
```

这是本节最关键的 metrics 测试。

### 4. 错误状态会产生错误日志和错误 counter

当 state 里有：

```text
agent_error_code = ORDER_QUERY_TIMEOUT
```

测试确认：

```text
trace.status = ERROR
span.status = ERROR
ticket_agent_failed log
ticket_agent.errors counter
```

这说明错误能同时进入：

```text
trace/span
log
metrics
```

但每种信号承担不同职责。

### 5. 不同问题有不同排查顺序

测试确认：

```text
latency_regression -> metric, trace, span, log
one_user_failed -> log, trace, span, metric
agent_decision_debug -> trace, span, log, metric
```

这正是本节核心。

---

## 七、常见排查场景

### 场景 1：用户说“刚才失败了”

排查顺序：

```text
1. log
2. trace
3. span
4. metrics
```

具体做法：

```text
用用户提供的时间、trace_id、thread_id 或 actor_id 找日志。
从日志拿到 otel_trace_id 和 span_id。
打开 trace 看完整路径。
看失败 span 的 attributes。
最后看 metrics 判断是否大面积。
```

### 场景 2：报警说错误率升高

排查顺序：

```text
1. metrics
2. trace
3. span
4. log
```

具体做法：

```text
先看 ticket_agent.errors / ticket_agent.invocations。
按 operation、intent、error_code 分组。
找代表性 error trace。
看失败 span。
再读对应日志确认细节。
```

### 场景 3：系统变慢

排查顺序：

```text
1. metrics
2. trace
3. span
4. log
```

具体做法：

```text
先看 ticket_agent.duration 的 P50/P95/P99。
看哪个 operation 或 intent 慢。
抽样慢 trace。
找最慢 span。
看日志解释为什么慢。
```

### 场景 4：Agent 决策不符合预期

排查顺序：

```text
1. trace
2. span
3. log
4. metrics
```

具体做法：

```text
先看走了哪些节点。
再看 agent.intent、ticket.write_safety.status、rag.answer.status。
再读日志里的决策点。
最后看 metrics 判断这种决策是否频繁。
```

### 场景 5：RAG 回答质量下降

可能顺序：

```text
metrics -> traces -> spans -> logs -> eval report
```

你可以看：

```text
rag.answer.status 分布是否变化
rag.citation.count 是否下降
无资料回答比例是否升高
慢 trace 是否集中在向量库
bad case analysis 是否出现新模式
```

这里还要结合阶段 6 前半段的 eval。

因为 RAG 质量下降，不只是 observability 问题，也是评测问题。

---

## 八、容易混淆的点

### 1. trace 和 log 都能看错误，有什么区别

trace 看路径。

log 看事件细节。

例如：

```text
trace 告诉你 query_order span failed。
log 告诉你失败时 error_code=ORDER_QUERY_TIMEOUT，重试策略是什么，fallback 是否触发。
```

### 2. span attributes 和 log fields 有什么区别

span attributes 描述一个操作。

log fields 描述某个事件。

例如：

```text
span attribute:
  agent.intent=ticket_request

log field:
  event_name=ticket_agent_failed
  error_code=ORDER_QUERY_TIMEOUT
```

### 3. metrics 和 logs 都有 error_code，区别是什么

metrics 里的 error_code 用于聚合：

```text
ORDER_QUERY_TIMEOUT 最近 10 分钟发生了多少次？
```

logs 里的 error_code 用于定位：

```text
这一次为什么失败？
```

### 4. trace_id 和 thread_id 谁更重要

不是谁更重要。

它们解决不同问题。

```text
trace_id 解决一次技术链路。
thread_id 解决一段业务会话。
```

如果用户确认工单创建是第二次请求：

```text
两次请求可能是两个 trace_id。
但它们应该共享同一个 thread_id。
```

### 5. LangSmith trace 和 OpenTelemetry trace 是不是同一个

不是完全同一个概念。

LangSmith trace 更偏：

```text
LLM / Agent 运行调试
```

OpenTelemetry trace 更偏：

```text
分布式系统链路追踪
```

它们可以通过：

```text
trace_id
thread_id
metadata
attributes
```

建立关联。

---

## 九、本节练习

### 练习 1：解释四类信号

问题：用自己的话解释 trace、span、log、metrics 分别是什么。

参考答案：

```text
trace 是一次请求或任务的完整路径。
span 是 trace 里的一段工作单元。
log 是某个时间点发生的一条事件记录。
metrics 是很多运行结果聚合出来的测量数据。
```

### 练习 2：判断排查入口

问题：下面场景应该先看什么？

```text
1. 某个用户说刚才工单创建失败。
2. 最近 10 分钟 Agent P95 延迟升高。
3. 系统报警 ticket_agent.errors 增加。
4. 想解释某次 Agent 为什么选择 ticket_request。
```

参考答案：

```text
1. 先看 log，再 trace/span。
2. 先看 metrics，再抽慢 trace。
3. 先看 metrics，再抽 error trace。
4. 先看 trace/span，再看日志。
```

### 练习 3：判断字段应该放在哪里

问题：下面字段适合放 log、span attributes、metric attributes，还是不应该直接放？

```text
trace_id
span_id
thread_id
agent.intent
ticket.creation.status
elapsed_ms
user_message
order_query_result
ticket_agent.duration
```

参考答案：

```text
trace_id -> log，也可以放 span attributes 用于关联；不要放 metric attributes
span_id -> log，也属于 span context；不要放 metric attributes
thread_id -> log/span attributes；不要放 metric attributes
agent.intent -> span attributes，也可以作为低基数 metric attribute
ticket.creation.status -> span attributes，也可以作为低基数 metric attribute
elapsed_ms -> log field，也可以进入 duration histogram
user_message -> 不应该直接放
order_query_result -> 不应该直接放
ticket_agent.duration -> metric
```

### 练习 4：为什么 metrics 不放 thread_id

问题：为什么 `thread_id` 可以出现在日志里，但不应该放进 metric attributes？

参考答案：

```text
thread_id 对每段会话几乎都是不同的，是高基数字段。放进 metrics attributes 会让时间序列数量暴增，增加内存、存储和查询成本。日志是按事件记录，适合带 thread_id 定位具体请求；metrics 是聚合数据，应该只放低基数字段。
```

### 练习 5：读代码判断信号

问题：下面 state 会产生什么关键观测信号？

```python
state = {
    "agent_trace_id": "trace-001",
    "intent": "order_query",
    "order_query_status": "failed",
    "agent_error_code": "ORDER_QUERY_TIMEOUT",
    "agent_error_node": "query_order",
    "fallback_used": True,
    "node_history": ["normalize_user_input", "query_order"],
}
```

参考答案：

```text
trace.status = ERROR
span.status = ERROR
span.attributes 包含 agent.intent=order_query、agent.error_code=ORDER_QUERY_TIMEOUT、agent.error_node=query_order
logs 包含 ticket_agent_started 和 ticket_agent_failed
ticket_agent.errors counter +1
ticket_agent.invocations counter +1
如果传入 elapsed_ms，还会记录 ticket_agent.duration histogram
metrics attributes 里 status=error，可能带 error_code=ORDER_QUERY_TIMEOUT，但不会带 trace_id/thread_id/span_id
```

### 练习 6：设计排查路径

问题：如果 `ticket_agent.duration` 的 P95 从 300ms 涨到 2s，你怎么排查？

参考答案：

```text
1. 先看 metrics，确认 P95 变慢是否集中在某个 operation 或 intent。
2. 抽取慢 traces。
3. 查看 trace 中哪个 span 最慢，例如 RAG 检索、LLM 调用、Java API 调用。
4. 查看慢 span 的 attributes，比如 rag.answer.status、order.query.status。
5. 用 trace_id/span_id 查日志，看是否有 timeout、retry、fallback、上游错误。
6. 如果是模型或 RAG 质量问题，再结合 eval / bad case analysis。
```

---

## 十、自测题

### 自测 1：trace 和 span 的关系是什么？

答案：

```text
trace 是完整链路，span 是链路中的工作单元。一个 trace 通常包含多个 span，span 之间通过 parent span id 形成父子关系。
```

### 自测 2：log 和 span event 是不是一回事？

答案：

```text
不完全一样。log 是日志系统里的事件记录；span event 是 span 内部带时间戳的事件。它们都能表达某个时间点发生了什么，但所在数据模型不同。
```

### 自测 3：metrics 最适合回答什么问题？

答案：

```text
metrics 最适合回答系统整体趋势问题，例如调用量、错误率、P95 延迟、吞吐量、当前队列长度、资源使用率等。
```

### 自测 4：为什么不能只靠日志？

答案：

```text
日志适合看细节，但不擅长表达完整请求路径和整体趋势。只靠日志很难快速知道哪个 span 慢、错误率是否升高、问题影响范围多大。
```

### 自测 5：为什么不能只靠 metrics？

答案：

```text
metrics 能告诉你整体变差了，但不能直接解释某一次请求具体怎么失败、模型输出什么、工具调用为什么报错。要回到 trace/span/log。
```

### 自测 6：为什么不能把 trace_id 放进 metric attributes？

答案：

```text
trace_id 每次请求都不同，是高基数字段。放进 metric attributes 会导致时间序列爆炸，增加内存、存储和查询成本，并破坏 metrics 的聚合价值。
```

### 自测 7：单用户失败和系统整体变慢，排查入口为什么不同？

答案：

```text
单用户失败是具体请求问题，通常先用日志里的 trace_id/thread_id 定位，再看 trace/span。系统整体变慢是趋势问题，应该先看 metrics 的延迟分布，再抽慢 trace 分析。
```

### 自测 8：thread_id 在可观测性里有什么价值？

答案：

```text
thread_id 表示业务会话或可恢复流程。它可以把多次请求、多条 trace 关联成同一个业务过程，尤其适合 LangGraph checkpoint、用户确认、人机协作等多轮流程。
```

---

## 十一、本节命令

在 `projects/ai-service` 目录运行：

```powershell
uv run pytest tests/test_ticket_agent_observability_signals.py
```

本节当前测试结果：

```text
7 passed
```

提交前还需要运行全量测试：

```powershell
uv run pytest
```

---

## 十二、本节小结

本节你要真正掌握的是：

```text
1. trace 看一次请求的完整路径。
2. span 看路径中的一个工作单元。
3. log 看某个时间点发生的事件和细节。
4. metrics 看系统整体趋势和聚合表现。
5. correlation 让不同信号能互相跳转。
6. 单用户问题通常先看 log/trace。
7. 系统趋势问题通常先看 metrics。
8. metrics 不应该带 trace_id、span_id、thread_id、actor_id 这类高基数字段。
9. logs 可以带关联 ID，但也不能记录敏感 payload。
10. trace_id 解决技术链路，thread_id 解决业务会话。
```

本节完成后，当前项目新增了：

```text
TicketAgentSignalCorrelation
TicketAgentTraceSignal
TicketAgentSpanSignal
TicketAgentLogSignal
TicketAgentMetricSignal
TicketAgentObservabilitySignals
build_ticket_agent_observability_signals()
build_ticket_agent_investigation_steps()
```

下一节进入：

```text
阶段 6 第 29 节：生产日志字段设计
```

下一节会把本节里的 log 继续细化：

```text
生产日志到底要有哪些字段？
trace_id、span_id、thread_id、actor_id、operation、event、error_code、elapsed_ms 应该怎么命名？
哪些字段是必须字段？
哪些字段是可选字段？
哪些字段不能进入日志？
日志级别怎么定？
```
