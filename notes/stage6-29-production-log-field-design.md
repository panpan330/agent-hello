# 阶段 6 第 29 节：生产日志字段设计

本节目标：学会从生产排查角度设计日志字段，而不是只会写 `logger.info("xxx")`。

你要能回答这些问题：

```text
1. 生产日志和普通 print 有什么区别？
2. 为什么生产日志要结构化？
3. 一个生产日志事件至少应该有哪些字段？
4. trace_id、span_id、thread_id、actor_id 分别解决什么问题？
5. event_name、operation、status、error_code 怎么命名？
6. INFO、WARNING、ERROR 应该怎么区分？
7. 哪些业务字段可以进日志？
8. 哪些字段绝对不能进日志？
9. 为什么日志可以放 trace_id/thread_id，但 metrics 不建议放？
10. 当前项目如何把这些规则变成可测试的代码？
```

这一节不要求你立刻把项目日志系统改成完整 JSON 日志输出。

这一节先做更基础也更重要的事：

```text
把生产日志字段的设计原则、命名规则、安全边界和可测试模型讲明白。
```

后面如果接入 OpenTelemetry SDK、日志采集器、ELK、Loki、Datadog、Grafana、阿里云 SLS 或其他日志平台，这一节的字段设计都还能继续用。

---

## 一、本节在主线里的位置

阶段 6 里，第 26 到第 30 节是一组完整的可观测性基础：

```text
第 26 节：LangSmith tracing 基础
第 27 节：OpenTelemetry 基础
第 28 节：trace / span / log / metrics 的关系
第 29 节：生产日志字段设计
第 30 节：成本、token 和延迟指标
```

第 28 节解决的是：

```text
trace、span、log、metrics 分别是什么，它们如何配合。
```

第 29 节解决的是：

```text
log 这一类信号具体应该怎么设计字段。
```

你可以这样理解：

```text
第 28 节：告诉你日志在可观测性地图里的位置
第 29 节：告诉你一条真正有用的生产日志长什么样
```

如果日志字段设计不好，后面的监控、告警、排查、审计都会变得很痛苦。

比如你只写：

```text
出错了
```

这不是生产日志。

因为它没有告诉你：

```text
哪次请求出错？
哪个用户或哪条业务会话出错？
哪个 Agent 节点出错？
错误码是什么？
是模型失败、RAG 失败、Java 工具失败，还是确认流程被拦截？
耗时是多少？
这个错误能不能和 trace 对上？
这个错误能不能和 metrics 上的错误率对上？
```

真正的生产日志应该是能被机器检索、过滤、聚合，也能被人快速读懂的事件记录。

---

## 二、官方资料依据

本节参考了 OpenTelemetry 官方资料：

- OpenTelemetry Logs Data Model: https://opentelemetry.io/docs/specs/otel/logs/data-model/
- OpenTelemetry Logging: https://opentelemetry.io/docs/specs/otel/logs/
- Trace Context in non-OTLP Log Formats: https://opentelemetry.io/docs/specs/otel/compatibility/logging_trace_context/
- OpenTelemetry Semantic Conventions: https://opentelemetry.io/docs/concepts/semantic-conventions/
- Semantic conventions for events: https://opentelemetry.io/docs/specs/semconv/general/events/
- OpenTelemetry Metrics cardinality: https://opentelemetry.io/docs/concepts/signals/metrics/

这些资料里有几条对本节很重要：

```text
1. OpenTelemetry 的日志数据模型包含 Timestamp、TraceId、SpanId、SeverityText、SeverityNumber、Body、Resource、Attributes、EventName 等概念。
2. 日志可以通过 TraceId 和 SpanId 与 trace/span 关联。
3. 非 OTLP 的 JSON 日志里，trace_id、span_id、trace_flags 推荐作为顶层字段。
4. EventName 应该稳定地识别事件类型，不能包含动态值。
5. Resource 描述产生日志的实体，例如 service.name、deployment.environment.name。
6. Attributes 描述这一次事件发生时的具体上下文。
7. Metrics 的高基数字段会带来内存和成本问题，所以 trace_id/user_id/raw path 这类字段不能随便放进 metrics。
```

我们当前项目不是直接实现完整 OpenTelemetry SDK。

但我们会借鉴它的模型，把当前智能工单 Agent 的日志字段设计成一个清晰、稳定、可测试的形状。

---

## 三、基础知识铺垫

这一部分非常重要。

如果你只看代码，很容易以为本节只是新增一个 `dict`。

但真正要学的是：

```text
生产日志是一种工程契约。
```

你写的不是一句话，而是一条将来要被搜索、过滤、关联、告警、审计、排查的事件数据。

### 1. 什么是生产日志

生产日志就是系统在线上运行时留下的事件记录。

它的目的不是给开发者临时看看。

它的目的包括：

```text
1. 排查故障
2. 分析错误原因
3. 追踪一次请求
4. 还原关键业务流程
5. 辅助告警分析
6. 支撑审计和安全检查
7. 观察系统是否稳定
8. 给后续问题复盘提供证据
```

所以生产日志不是：

```python
print("进来了")
print("这里执行了")
print("报错了")
```

这些只能算调试输出。

生产日志必须回答：

```text
什么时间？
哪个服务？
哪个事件？
严重程度？
哪次请求？
哪个业务会话？
哪个用户或操作者？
哪个操作？
结果是什么？
失败原因是什么？
耗时多少？
能不能和 trace/span/metrics 对上？
有没有泄露敏感信息？
```

### 2. 普通文本日志的问题

早期我们项目里已经有了日志，比如：

```text
chat_requested message_length=4 history_size=0
```

这比单纯写：

```text
chat requested
```

已经好很多。

因为它至少有：

```text
事件：chat_requested
字段：message_length、history_size
```

但它还是文本日志。

文本日志最大的问题是：

```text
人能看，但机器不一定好查。
```

比如你想查：

```text
所有 operation=invoke_thread 且 status=failed 且 error_code=ORDER_QUERY_TIMEOUT 的日志
```

如果日志只是自由文本，日志平台只能做字符串匹配。

字符串匹配的问题是：

```text
1. 字段名可能写得不一致
2. 字段值可能格式不一致
3. 无法稳定做类型比较
4. 很难聚合
5. 很难做索引优化
6. 改一次文案可能导致查询失效
```

生产系统更推荐结构化日志。

### 3. 什么是结构化日志

结构化日志就是把日志写成字段明确的数据，而不是一整段自由文本。

普通文本日志：

```text
ticket agent failed code=ORDER_QUERY_TIMEOUT thread=ticket-thread-001 cost=305ms
```

结构化日志：

```json
{
  "event_name": "ticket_agent.workflow.failed",
  "severity_text": "ERROR",
  "trace_id": "8b0e715c76c8423e9dc95b6c8db8409a",
  "span_id": "5fb397be34d26b51",
  "body": "Ticket agent workflow failed.",
  "attributes": {
    "operation": "invoke_thread",
    "status": "failed",
    "thread_id": "ticket-thread-001",
    "error_code": "ORDER_QUERY_TIMEOUT",
    "elapsed_ms": 305.13
  }
}
```

结构化日志的好处是：

```text
1. 每个字段有名字
2. 每个字段有含义
3. 每个字段可以被索引
4. 每个字段可以被过滤
5. 每个字段可以被聚合
6. 字段可以和 trace/span/metrics 关联
7. 字段可以被测试保护
```

生产排查时，结构化日志比一大段字符串可靠得多。

### 4. 日志不是数据库

这是很容易犯错的地方。

很多初学者会觉得：

```text
为了排查方便，我把用户输入、模型回答、订单结果、工单字段都打进日志。
```

这很危险。

日志不是数据库。

日志不是业务数据备份。

日志不是用户隐私存储。

生产日志应该记录：

```text
能帮助定位问题的摘要字段。
```

生产日志不应该记录：

```text
完整用户原文
完整模型回答
完整订单查询结果
完整工单创建参数
手机号
身份证
地址
API Key
Authorization
Cookie
access_token
refresh_token
```

你要记住一句话：

```text
日志字段越有用越好，不是越多越好。
```

字段太少，排查困难。

字段太多，成本高、噪音大、还可能泄露敏感信息。

### 5. 日志是一种事件

一条日志应该对应一个事件。

事件就是：

```text
在某个时间点发生了一件有意义的事。
```

比如：

```text
ticket_agent.workflow.started
ticket_agent.workflow.succeeded
ticket_agent.workflow.failed
ticket_agent.confirmation.required
ticket_agent.tool.call.failed
ticket_agent.llm.output.invalid
```

这些都是事件。

它们有一个共同点：

```text
名字稳定，含义稳定。
```

不要这样命名：

```text
ticket_agent.workflow.failed.ORDER123
ticket_agent.user_10001_failed
ticket_agent.order_202607260001_failed
```

因为这些名字里包含动态值。

动态值应该放到字段里，而不是放到事件名里。

正确做法：

```json
{
  "event_name": "ticket_agent.workflow.failed",
  "attributes": {
    "error_code": "ORDER_QUERY_TIMEOUT",
    "thread_id": "ticket-thread-001"
  }
}
```

为什么事件名不能包含动态值？

因为日志平台会按事件名查询、过滤和聚合。

如果事件名里有订单号、用户 ID、线程 ID，那么每条日志的事件名都可能不一样。

这样会导致：

```text
1. 查询困难
2. 聚合困难
3. 告警规则难写
4. 字段含义不稳定
5. 可观测性数据变成噪音
```

### 6. top-level、resource、attributes 分别是什么

OpenTelemetry 的日志模型可以帮助我们理解字段分层。

本节我们用三个层次：

```text
top-level fields
resource fields
attributes fields
```

#### top-level fields

顶层字段是每条日志最核心的字段。

比如：

```text
timestamp
trace_id
span_id
trace_flags
severity_text
severity_number
event_name
body
```

这些字段非常基础，日志平台通常会优先识别它们。

#### resource fields

resource 描述谁产生了这条日志。

比如：

```text
service.name
service.namespace
service.version
deployment.environment.name
```

它回答的是：

```text
这条日志来自哪个服务、哪个环境、哪个版本？
```

resource 通常相对稳定。

同一个服务实例发出的很多日志，它们的 resource 都差不多。

#### attributes fields

attributes 描述这次事件自己的上下文。

比如：

```text
operation
status
thread_id
actor_id
app_trace_id
agent.intent
ticket.creation_status
error_code
elapsed_ms
```

它回答的是：

```text
这次事件具体发生在什么业务场景里？
```

### 7. body 是给人看的，不是给机器当字段用的

`body` 是日志正文。

它适合写一句简短、稳定、给人看的说明。

比如：

```text
Ticket agent workflow failed.
Ticket agent workflow succeeded.
Ticket agent confirmation is required.
```

不要把 `body` 写成：

```text
用户说：我订单 10001 没收到，手机号是 13800000000，地址是......
```

也不要把一大段 JSON 塞进 `body`。

因为这样会有三个问题：

```text
1. 敏感信息风险高
2. 日志体积大
3. 机器很难稳定查询
```

正确思路是：

```text
body 写稳定描述
attributes 放可查询字段
敏感 payload 不进日志
```

### 8. severity_text 和 severity_number

日志级别不是随便写的。

常见日志级别：

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

本节代码里使用的映射：

```text
DEBUG    -> 5
INFO     -> 9
WARNING  -> 13
ERROR    -> 17
CRITICAL -> 21
```

这个设计来自 OpenTelemetry 的严重程度范围思想：

```text
DEBUG 用于调试
INFO 用于正常事件
WARN/WARNING 用于需要关注但不一定失败的情况
ERROR 用于明确失败
FATAL/CRITICAL 用于严重崩溃级别问题
```

在 Python 里通常叫 `WARNING`。

OpenTelemetry 表格里常见短名是 `WARN`。

所以本节代码允许你传：

```text
WARN
```

然后规范化成：

```text
WARNING
```

### 9. 什么时候用 INFO

`INFO` 表示正常业务事件。

比如：

```text
ticket_agent.workflow.started
ticket_agent.workflow.succeeded
ticket_agent.confirmation.required
```

这些事件不是失败。

它们只是告诉你：

```text
系统发生了一件正常但值得记录的事。
```

注意：

```text
INFO 不是越多越好。
```

如果你把每个变量、每一步循环都打 INFO，生产日志会变成噪音。

INFO 应该记录：

```text
1. 请求开始
2. 请求结束
3. 关键业务状态变化
4. 重要外部调用结果摘要
5. 需要审计的关键动作
```

### 10. 什么时候用 WARNING

`WARNING` 表示需要关注，但不一定是请求失败。

比如：

```text
用户缺少必填字段，需要补充
写操作需要确认，所以被阻止
模型输出格式不完整，但系统成功降级
RAG 没找到上下文，但返回了安全兜底答案
```

WARNING 的特点是：

```text
系统还活着，请求可能也有兜底结果，但这里有值得关注的异常状态。
```

### 11. 什么时候用 ERROR

`ERROR` 表示明确失败。

比如：

```text
Java 订单服务调用超时
模型 API 调用失败
工具执行失败
Pydantic 校验失败后无法恢复
checkpoint 保存失败
```

ERROR 日志一定要有稳定错误码。

例如：

```text
error_code=ORDER_QUERY_TIMEOUT
error_node=query_order
```

不要只写：

```text
error=timeout
```

更不要只写：

```text
出错了
```

稳定错误码的价值是：

```text
1. 可以搜索
2. 可以聚合
3. 可以写告警
4. 可以做错误率统计
5. 可以沉淀故障知识库
```

### 12. trace_id、span_id、thread_id、actor_id 的区别

这几个字段很容易混。

#### trace_id

`trace_id` 是技术链路追踪 ID。

它回答：

```text
这一次请求在系统里经过了哪些服务和操作？
```

在 OpenTelemetry 里，`trace_id` 是 32 位十六进制字符串。

本节生产日志里，顶层 `trace_id` 使用 OpenTelemetry trace id。

#### span_id

`span_id` 是当前操作单元的 ID。

它回答：

```text
这条日志属于 trace 里的哪个操作？
```

比如一个 trace 可能包含：

```text
FastAPI request span
Agent workflow span
LLM classify intent span
Java query order span
RAG retrieve span
```

日志带上 `span_id` 后，你就能从日志跳回具体 span。

#### app_trace_id

我们项目早期有自己的 `X-Trace-Id`。

它在 `app/core/trace.py` 里维护。

为了不和 OpenTelemetry 的 `trace_id` 混淆，本节模型里把它放成：

```text
app_trace_id
```

如果当前项目里它刚好也是合法 OTel trace id，它可能和顶层 `trace_id` 一样。

如果它不是合法 OTel trace id，OpenTelemetry 可能会生成新的 `trace_id`，而 `app_trace_id` 仍然记录项目自己的请求 id。

#### thread_id

`thread_id` 是 LangGraph / checkpoint 的业务会话 ID。

它回答：

```text
这一组多轮对话、多次请求、用户确认流程，属于哪个业务会话？
```

`trace_id` 通常是一次请求。

`thread_id` 可以跨多次请求。

所以智能工单 Agent 里，`thread_id` 非常重要。

#### actor_id

`actor_id` 表示操作者。

它回答：

```text
是谁触发了这个流程？
```

注意：

```text
actor_id 应该是内部稳定 ID，不应该是手机号、邮箱、身份证、真实姓名。
```

如果 actor_id 本身就是敏感信息，就不能直接进日志。

### 13. operation、event_name、status 的区别

这三个字段也很容易混。

#### operation

`operation` 表示当前操作。

比如：

```text
invoke_thread
query_order
create_ticket
classify_intent
extract_ticket_fields
```

它偏向“正在执行什么动作”。

#### event_name

`event_name` 表示发生了什么事件。

比如：

```text
ticket_agent.workflow.started
ticket_agent.workflow.succeeded
ticket_agent.workflow.failed
```

它偏向“这个时间点发生了什么事”。

#### status

`status` 表示结果状态。

比如：

```text
started
succeeded
failed
blocked
fallback
```

它偏向“结果是什么”。

三者可以同时出现：

```json
{
  "event_name": "ticket_agent.workflow.failed",
  "attributes": {
    "operation": "invoke_thread",
    "status": "failed",
    "error_code": "ORDER_QUERY_TIMEOUT"
  }
}
```

这样设计后，你可以查询：

```text
所有 ticket_agent.workflow.failed 事件
所有 operation=invoke_thread 的日志
所有 status=failed 的日志
所有 error_code=ORDER_QUERY_TIMEOUT 的日志
```

### 14. error_code 比 exception message 更重要

异常消息经常不稳定。

比如：

```text
Read timed out
HTTPConnectionPool read timed out
Connection timeout after 5000ms
upstream request timeout
```

不同库、不同版本、不同运行环境，异常消息可能都不一样。

但错误码可以稳定：

```text
ORDER_QUERY_TIMEOUT
LLM_API_KEY_MISSING
MODEL_OUTPUT_INVALID
TICKET_CONFIRMATION_REQUIRED
CHECKPOINT_SAVE_FAILED
```

生产日志里可以有简短异常摘要。

但更重要的是：

```text
error_code
error_node
fallback_used
```

### 15. elapsed_ms 是日志字段，但趋势应该看 metrics

日志里记录 `elapsed_ms` 很有用。

因为当你排查某一次失败请求时，你想知道：

```text
这一次到底耗时多少？
```

但如果你想知道：

```text
最近 10 分钟 P95 延迟是否升高？
今天整体平均耗时是否变差？
哪个 operation 最慢？
```

那应该看 metrics。

所以：

```text
单次请求细节：日志
整体趋势统计：metrics
```

### 16. 日志可以放高基数字段，但要谨慎

第 28 节我们讲过：

```text
metrics 不要放 trace_id、thread_id、actor_id 这类高基数字段。
```

那日志能不能放？

可以，但要有边界。

日志本来就是一条一条事件记录。

它适合放：

```text
trace_id
span_id
thread_id
error_code
operation
status
```

但日志也不是随便放。

日志里仍然不应该放：

```text
完整用户原文
完整模型回答
完整订单详情
完整工具参数
API Key
Token
密码
Cookie
```

你要区分两类风险：

```text
高基数风险：影响 metrics 成本和聚合
敏感信息风险：影响安全和合规
```

`trace_id` 是高基数，但通常不是敏感 payload，所以可以进日志。

`user_message` 既可能高基数，又可能敏感，所以不应该进生产日志。

---

## 四、本节主题系统讲解

下面进入本节主题：生产日志字段到底怎么设计。

### 1. 本节的日志字段分层

本节我们把字段分为四类：

```text
1. top_level：日志顶层字段
2. resource：产生日志的服务和环境字段
3. attributes：这一次事件的业务上下文字段
4. forbidden：禁止进入生产日志的字段
```

这种分层非常重要。

如果你把所有字段都平铺在一个大字典里，短期也能用，但长期会乱。

比如：

```text
service.name 是服务身份
operation 是事件上下文
error_code 是错误上下文
trace_id 是链路上下文
user_message 是敏感 payload
```

它们不是一类东西。

如果不分类，你就很难判断：

```text
这个字段应该在哪里？
这个字段是否每条日志都有？
这个字段能不能用于聚合？
这个字段是不是敏感？
这个字段应该由业务代码生成，还是由日志采集器补齐？
```

### 2. top-level 字段设计

本节建议的顶层字段：

| 字段 | 是否必须 | 作用 |
| --- | --- | --- |
| `timestamp` | 是 | 日志事件发生时间 |
| `trace_id` | 是 | OpenTelemetry trace id |
| `span_id` | 是 | 当前 span id |
| `trace_flags` | 推荐 | W3C trace flags，例如是否 sampled |
| `severity_text` | 是 | 人能读的日志级别 |
| `severity_number` | 是 | 机器能比较的日志级别 |
| `event_name` | 是 | 稳定事件名 |
| `body` | 是 | 简短人类说明 |

你可以把 top-level 理解成：

```text
日志平台最应该优先识别的字段。
```

这些字段不应该乱命名。

不要今天写：

```text
traceId
```

明天写：

```text
trace_id
```

后天写：

```text
requestTrace
```

字段名不稳定，会让日志检索很难维护。

本节统一用：

```text
trace_id
span_id
trace_flags
severity_text
severity_number
event_name
body
```

### 3. resource 字段设计

resource 描述日志来源。

本节使用：

```text
service.name
service.namespace
service.version
deployment.environment.name
```

对应当前项目：

```text
service.name = ai-service
service.namespace = java-python-ai
service.version = 当前服务版本，可选
deployment.environment.name = local/test/prod 等
```

为什么这些字段不放 attributes？

因为它们描述的是“谁发出的日志”，而不是“这次事件发生了什么”。

同一个服务实例发出的很多日志，resource 基本相同。

### 4. attributes 字段设计

attributes 描述一次事件的上下文。

当前智能工单 Agent 最重要的 attributes：

| 字段 | 作用 |
| --- | --- |
| `operation` | 当前操作 |
| `status` | 事件结果 |
| `app_trace_id` | 项目旧请求追踪 ID |
| `thread_id` | LangGraph 业务会话 ID |
| `actor_id` | 操作者 ID |
| `agent.intent` | Agent 识别出的意图 |
| `agent.node_last` | 最后执行的节点 |
| `agent.node_count` | 节点执行数量 |
| `ticket.creation_status` | 工单创建状态 |
| `ticket.write_safety_status` | 写操作安全状态 |
| `order.query_status` | 订单查询状态 |
| `rag.answer_status` | RAG 回答状态 |
| `error_code` | 稳定错误码 |
| `error_node` | 错误发生节点 |
| `elapsed_ms` | 本次操作耗时 |

这些字段有一个共同点：

```text
它们能帮助你定位问题，但不需要存完整业务 payload。
```

### 5. forbidden 字段设计

本节明确禁止这些字段直接进入生产日志：

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
messages
raw_response
raw_completion
authorization
cookie
password
prompt
```

同时，字段名包含下面片段也会被拦截：

```text
api_key
access_token
refresh_token
secret
```

为什么要从字段名拦截？

因为自动检查字段名比检查字段值稳定。

比如字段名叫：

```text
api_key
```

那它几乎一定不应该进日志。

字段名叫：

```text
user_message
```

那它也很可能包含敏感信息。

当然，真实生产系统还可以加更强的脱敏和内容扫描。

但在学习阶段，我们先把最基础、最确定的规则做对。

### 6. 当前项目的字段设计原则

当前项目是：

```text
FastAPI Python AI 服务
+ LangGraph 智能工单 Agent
+ RAG
+ Java mock 业务服务
+ LLM API
+ checkpoint
+ tracing
```

所以日志字段要服务于这些排查场景：

```text
1. 用户说某次工单失败了
2. 模型输出格式不对
3. 工具调用失败
4. Java 服务超时
5. RAG 没查到知识
6. 写操作被安全确认拦住
7. checkpoint 会话恢复异常
8. 某个 Agent 节点耗时变长
```

这些场景需要的字段不是一大段用户原文。

它们需要：

```text
trace_id
span_id
thread_id
operation
status
agent.intent
agent.node_last
error_code
elapsed_ms
```

### 7. 一个成功日志应该长什么样

示例：

```json
{
  "timestamp": "2026-07-26T10:20:30.123Z",
  "trace_id": "8b0e715c76c8423e9dc95b6c8db8409a",
  "span_id": "5fb397be34d26b51",
  "trace_flags": "01",
  "severity_text": "INFO",
  "severity_number": 9,
  "event_name": "ticket_agent.workflow.succeeded",
  "body": "Ticket agent workflow succeeded.",
  "resource": {
    "service.name": "ai-service",
    "service.namespace": "java-python-ai",
    "service.version": "0.1.0",
    "deployment.environment.name": "test"
  },
  "attributes": {
    "operation": "invoke_thread",
    "status": "succeeded",
    "app_trace_id": "8b0e715c76c8423e9dc95b6c8db8409a",
    "thread_id": "ticket-thread-001",
    "actor_id": "demo_user_001",
    "agent.intent": "ticket_request",
    "ticket.creation_status": "succeeded",
    "ticket.write_safety_status": "safe",
    "agent.node_last": "create_ticket",
    "elapsed_ms": 42.13
  }
}
```

这条日志好在哪里？

```text
1. 可以按 trace_id 跳到 trace
2. 可以按 span_id 定位具体 span
3. 可以按 thread_id 串起业务会话
4. 可以按 event_name 查所有成功事件
5. 可以按 operation 查某类操作
6. 可以按 status 查结果
7. 可以按 agent.intent 查业务意图
8. 可以按 elapsed_ms 看单次耗时
9. 没有用户原文
10. 没有模型完整回答
11. 没有订单详情
```

### 8. 一个失败日志应该长什么样

示例：

```json
{
  "trace_id": "8b0e715c76c8423e9dc95b6c8db8409a",
  "span_id": "5fb397be34d26b51",
  "trace_flags": "01",
  "severity_text": "ERROR",
  "severity_number": 17,
  "event_name": "ticket_agent.workflow.failed",
  "body": "Ticket agent workflow failed.",
  "resource": {
    "service.name": "ai-service",
    "service.namespace": "java-python-ai",
    "deployment.environment.name": "local"
  },
  "attributes": {
    "operation": "invoke_thread",
    "status": "failed",
    "thread_id": "ticket-thread-001",
    "agent.intent": "order_query",
    "error_code": "ORDER_QUERY_TIMEOUT",
    "error_node": "query_order",
    "agent.fallback_used": true,
    "elapsed_ms": 305.13
  }
}
```

这条失败日志关键在：

```text
error_code
error_node
fallback_used
```

当你看到：

```text
error_code=ORDER_QUERY_TIMEOUT
error_node=query_order
fallback_used=true
```

你就知道：

```text
不是整个 Agent 完全崩了，而是 query_order 节点出现了订单查询超时，并且系统启用了兜底。
```

### 9. 为什么本节没有直接改 app/core/logging.py

当前项目已有：

```text
app/core/logging.py
```

它负责基础 logging 配置：

```text
日志级别
日志格式
trace_id 注入
stdout 输出
```

本节新增的是：

```text
app/agents/production_logging.py
```

它不是替代 `app/core/logging.py`。

它的职责是：

```text
定义智能工单 Agent 生产日志字段应该怎么组织。
```

也就是说：

```text
app/core/logging.py      -> 日志系统怎么输出
production_logging.py   -> Agent 业务日志应该有哪些字段
```

这两个层次不要混。

如果现在直接把整个项目日志改成 JSON，学习负担会变重。

本节先学字段设计，后面再学真正输出、采集、上报。

### 10. 本节和第 28 节的关系

第 28 节讲：

```text
logs 可以带 trace_id/span_id/thread_id，用来和 trace/span 关联。
```

第 29 节把它落成具体字段：

```text
top-level trace_id
top-level span_id
attribute app_trace_id
attribute thread_id
attribute actor_id
```

第 28 节讲：

```text
metrics 不要放高基数字段。
```

第 29 节讲：

```text
日志可以放 trace_id/thread_id 这类排查字段，但不能放敏感 payload。
```

第 28 节讲：

```text
log 是点状事件。
```

第 29 节讲：

```text
点状事件要有稳定 event_name、operation、status、error_code。
```

---

## 五、本节代码讲解

本节新增：

```text
projects/ai-service/app/agents/production_logging.py
projects/ai-service/tests/test_ticket_agent_production_logging.py
```

代码的目标不是让你背 API。

代码的目标是把日志字段设计原则变成可运行、可验证的规则。

### 1. TicketAgentLogFieldSpec

这个类表示一个日志字段说明。

它回答：

```text
字段叫什么？
字段放在哪里？
字段属于哪类？
字段是否必须？
字段为什么存在？
字段示例是什么？
```

核心字段：

```python
@dataclass(frozen=True)
class TicketAgentLogFieldSpec:
    name: str
    placement: TicketAgentLogFieldPlacement
    category: TicketAgentLogFieldCategory
    required: bool
    description: str
    example: LogFieldValue | None = None
```

这里最值得你理解的是 `placement`。

它把字段放到：

```text
top_level
resource
attribute
forbidden
```

这比只写一个字段列表更清晰。

因为字段设计不是只关心“有没有”，还要关心“应该在哪里”。

### 2. TicketAgentProductionLogRecord

这个类表示一条生产日志记录。

它不是直接写到 stdout。

它先在内存里表达一条结构化日志应该长什么样。

核心字段：

```python
@dataclass(frozen=True)
class TicketAgentProductionLogRecord:
    event_name: str
    severity_text: TicketAgentLogSeverity
    severity_number: int
    body: str
    trace_id: str
    span_id: str
    trace_flags: str
    resource: dict[str, LogFieldValue]
    attributes: dict[str, LogFieldValue]
    timestamp: str | None = None
```

你要看懂这几个分组：

```text
event_name / severity / body：事件本身
trace_id / span_id / trace_flags：可观测性关联
resource：谁产生的日志
attributes：这次事件的上下文
timestamp：发生时间
```

### 3. to_otel_log_record()

这个方法把对象转成更接近 OpenTelemetry 日志模型的字典。

输出大致是：

```python
{
    "trace_id": ...,
    "span_id": ...,
    "trace_flags": ...,
    "severity_text": ...,
    "severity_number": ...,
    "event_name": ...,
    "body": ...,
    "resource": {...},
    "attributes": {...},
}
```

它的学习价值在于：

```text
你能直观看到生产日志应该分层，而不是所有字段乱堆在一起。
```

### 4. build_ticket_agent_log_field_specs()

这个函数返回字段设计说明。

它相当于当前项目的“日志字段字典”。

比如：

```text
trace_id 是 top_level、correlation、required
service.name 是 resource、resource、required
thread_id 是 attribute、correlation、optional
user_message 是 forbidden、safety
```

真实公司里经常会有类似文档：

```text
日志字段规范
埋点字段规范
可观测性字段规范
```

本节把它写成代码，方便测试。

### 5. validate_ticket_agent_event_name()

这个函数校验事件名。

本节要求事件名：

```text
1. 小写
2. 用点号分层
3. 至少包含一个点
4. 不包含空格
5. 不包含斜杠
6. 不包含动态占位符
```

合法：

```text
ticket_agent.workflow.started
ticket_agent.workflow.succeeded
ticket_agent.workflow.failed
```

非法：

```text
ticket_agent
ticket_agent.workflow.ORDER123
ticket_agent.workflow.{order_id}
ticket_agent.workflow failed
ticket_agent.workflow/failed
```

为什么要这么严？

因为事件名是日志查询的入口。

事件名一旦乱，后面所有查询都会乱。

### 6. normalize_ticket_agent_log_severity()

这个函数处理日志级别。

它做三件事：

```text
1. 如果没传级别，没有错误时默认 INFO。
2. 如果没传级别，有错误时默认 ERROR。
3. 如果传 WARN，规范化成 WARNING。
```

这样设计是为了贴合 Python 项目。

Python logging 常用：

```text
WARNING
```

但很多可观测性资料里会看到：

```text
WARN
```

本节让两者能对上。

### 7. build_ticket_agent_production_log_record()

这是本节最核心的函数。

它负责根据 Agent state 生成一条生产日志记录。

它做了几件事：

```text
1. 校验 event_name
2. 判断 severity
3. 复用上一节 OpenTelemetry span plan
4. 生成 trace_id/span_id/trace_flags
5. 生成 resource 字段
6. 从 Agent state 复制安全摘要字段
7. 添加 thread_id/actor_id/elapsed_ms
8. 拦截敏感字段
9. 返回 TicketAgentProductionLogRecord
```

注意这里的“复用上一节”很重要。

我们没有重新发明 trace/span。

而是复用了：

```text
build_ticket_agent_otel_span_plan()
```

这说明第 27、28、29 节是串起来的。

### 8. TICKET_AGENT_SAFE_STATE_TO_LOG_ATTRIBUTES

这个常量定义哪些 state 字段可以进日志。

比如：

```text
intent -> agent.intent
ticket_creation_status -> ticket.creation_status
order_query_status -> order.query_status
fallback_used -> agent.fallback_used
```

这些都是安全摘要字段。

它们告诉你业务状态，但不包含完整 payload。

比如：

```text
agent.intent = order_query
```

是可以的。

但：

```text
user_message = 我的手机号是 13800000000
```

不可以。

### 9. find_forbidden_ticket_agent_log_fields()

这个函数负责发现禁止字段。

它会递归检查嵌套 dict。

比如：

```python
{
    "attributes": {
        "password": "redacted",
        "nested": {
            "refresh_token": "redacted"
        }
    }
}
```

会发现：

```text
attributes.password
attributes.nested.refresh_token
```

这类测试很重要。

因为敏感信息经常不是顶层出现，而是藏在嵌套结构里。

### 10. 为什么状态里的 user_message 没有被复制

测试里故意放了：

```text
user_message
final_answer
order_query_result
ticket_fields
```

然后验证生产日志里没有这些内容。

这不是多余测试。

这是生产安全边界测试。

真实 AI 应用里，最容易泄露的就是：

```text
用户输入
模型输出
检索结果
工具返回
业务参数
```

所以这类测试必须早早养成习惯。

---

## 六、本节测试重点

本节新增测试文件：

```text
projects/ai-service/tests/test_ticket_agent_production_logging.py
```

测试重点不是为了追求数量。

测试覆盖了生产日志字段设计最关键的边界。

### 测试 1：trace/span 顶层字段

验证：

```text
trace_id
span_id
trace_flags
severity_text
severity_number
event_name
body
attributes.operation
attributes.status
attributes.thread_id
```

这说明日志能和 trace/span 对上。

### 测试 2：resource 和 attributes 分开

验证：

```text
service.name 在 resource
operation 在 attributes
```

这说明字段分类没有乱。

### 测试 3：event_name 校验

验证非法事件名会被拒绝：

```text
ticket_agent
ticket_agent.workflow.ORDER123
ticket_agent.workflow.{order_id}
ticket_agent.workflow failed
ticket_agent.workflow/failed
```

这保护事件名稳定性。

### 测试 4：extra_attributes 拦截敏感字段

验证：

```text
api_key
user_message
```

不能通过额外字段偷偷进日志。

### 测试 5：Agent state 里的敏感 payload 不复制

验证这些字段不会进日志：

```text
user_message
final_answer
order_query_result
ticket_fields
```

这对 AI 应用很重要。

### 测试 6：错误日志有 ERROR 和稳定错误字段

验证：

```text
severity_text=ERROR
severity_number=17
status=failed
error_code=ORDER_QUERY_TIMEOUT
error_node=query_order
fallback_used=true
elapsed_ms=305.13
```

这说明失败日志能用于排查。

### 测试 7：字段规格表覆盖 required/correlation/forbidden

验证字段规范本身没有漏掉关键字段。

### 测试 8：递归发现 forbidden 字段

验证嵌套字段也能被发现。

### 测试 9：severity 规范化

验证：

```text
WARN -> WARNING
无错误默认 INFO
有错误默认 ERROR
非法级别报错
```

---

## 七、本节容易混淆的点

### 1. event_name 和 body 不是一回事

`event_name` 给机器查。

`body` 给人读。

不要把动态信息写进 event_name。

不要把大量业务数据写进 body。

### 2. trace_id 和 thread_id 不是一回事

`trace_id` 偏技术链路。

`thread_id` 偏业务会话。

一次业务会话可能包含多次请求，也就可能包含多个 trace。

### 3. error_code 和 exception message 不是一回事

`error_code` 是稳定分类。

`exception message` 是底层错误说明。

生产排查里，稳定错误码更适合搜索、聚合、告警。

### 4. 日志字段和 metrics attributes 不是一回事

日志可以记录一条请求的 trace_id。

metrics 不应该把 trace_id 当 attribute。

因为 metrics 是聚合数据，高基数字段会让时序数量爆炸。

### 5. 不记录敏感 payload 不等于不能排查

你不需要记录完整用户输入，也能排查很多问题。

你需要的是：

```text
intent
status
error_code
error_node
thread_id
trace_id
elapsed_ms
```

如果确实需要看原始业务数据，应该去有权限控制的业务数据库、审计系统或专门脱敏后的存储，而不是生产日志。

---

## 八、把本节讲给别人听

你可以这样讲：

```text
生产日志不是随便打印字符串，而是结构化事件数据。

一条好的生产日志应该有顶层字段、resource 字段和 attributes 字段。
顶层字段放 trace_id、span_id、severity、event_name、body 这些核心信息；
resource 描述日志来自哪个服务、哪个环境、哪个版本；
attributes 描述这次事件的业务上下文，比如 operation、status、thread_id、error_code、elapsed_ms。

event_name 必须稳定，不能包含订单号、用户 ID 这类动态值。
错误日志必须有稳定 error_code，不能只依赖异常文本。
AI 应用尤其要注意日志安全，用户原文、模型完整回答、订单结果、工具参数、API Key、Token 都不能直接进生产日志。

日志可以带 trace_id、span_id、thread_id 用于排查；但 metrics 不能随便带这些高基数字段。
```

如果你能这样讲出来，说明你真正理解了本节。

---

## 九、本节练习

### 练习 1：判断字段应该放在哪里

请判断下面字段应该放在 top-level、resource、attributes，还是 forbidden：

```text
trace_id
span_id
service.name
deployment.environment.name
operation
status
thread_id
error_code
elapsed_ms
user_message
order_query_result
api_key
```

参考答案：

```text
trace_id：top-level
span_id：top-level
service.name：resource
deployment.environment.name：resource
operation：attributes
status：attributes
thread_id：attributes
error_code：attributes
elapsed_ms：attributes
user_message：forbidden
order_query_result：forbidden
api_key：forbidden
```

### 练习 2：判断 event_name 是否合理

下面哪些 event_name 合理？

```text
ticket_agent.workflow.started
ticket_agent.workflow.failed
ticket_agent.workflow.failed.ORDER1001
ticket_agent.user_1001.failed
ticket_agent.tool.call.failed
ticket_agent.workflow failed
```

参考答案：

```text
合理：
ticket_agent.workflow.started
ticket_agent.workflow.failed
ticket_agent.tool.call.failed

不合理：
ticket_agent.workflow.failed.ORDER1001
原因：包含动态订单号。

ticket_agent.user_1001.failed
原因：包含动态用户 ID。

ticket_agent.workflow failed
原因：包含空格，不是稳定点号分层命名。
```

### 练习 3：设计一条工具失败日志

场景：

```text
Agent 调用 Java 订单查询工具失败。
错误码：ORDER_QUERY_TIMEOUT
节点：query_order
operation：query_order
thread_id：ticket-thread-001
耗时：5000.42ms
```

请写出你认为应该有的关键字段。

参考答案：

```json
{
  "event_name": "ticket_agent.tool.call.failed",
  "severity_text": "ERROR",
  "attributes": {
    "operation": "query_order",
    "status": "failed",
    "thread_id": "ticket-thread-001",
    "error_code": "ORDER_QUERY_TIMEOUT",
    "error_node": "query_order",
    "elapsed_ms": 5000.42
  }
}
```

还应该有：

```text
trace_id
span_id
trace_flags
resource.service.name
body
```

### 练习 4：为什么 user_message 不能进生产日志

参考答案：

```text
user_message 是用户原文，可能包含手机号、地址、账号、订单号、身份证、公司内部信息等敏感数据。
生产日志通常会被采集、索引、长期保存，并可能被多人查看。
如果直接记录 user_message，会带来安全、合规和隐私风险。
应该记录 message_length、intent、status、error_code 等摘要字段，而不是完整原文。
```

### 练习 5：为什么 error_code 比异常文本更适合做日志字段

参考答案：

```text
异常文本可能随依赖库、语言、版本、网络环境变化而变化，不适合稳定查询和聚合。
error_code 是业务系统定义的稳定错误分类，适合搜索、告警、统计和复盘。
生产日志可以保留简短异常摘要，但核心排查字段应该优先有 error_code。
```

### 练习 6：设计 WARNING 场景

什么情况下智能工单 Agent 应该记录 WARNING，而不是 ERROR？

参考答案：

```text
当系统没有彻底失败，但出现需要关注的异常状态时，可以用 WARNING。

例如：
1. 用户缺少工单必填字段，需要补充。
2. 写操作需要用户确认，所以暂时阻止。
3. RAG 没有检索到上下文，但系统返回了安全兜底回答。
4. 模型输出不完整，但通过规则兜底恢复。

这些情况不是彻底失败，所以不一定用 ERROR；但它们比普通 INFO 更需要关注。
```

### 练习 7：为什么 metrics 不应该放 trace_id，但日志可以放

参考答案：

```text
metrics 是聚合数据，trace_id 每次请求都不同，放进 metrics attributes 会造成高基数，导致时序数量暴涨、内存成本变高、查询和告警不稳定。

日志是一条一条事件记录，trace_id 的价值是帮助从日志跳到 trace，所以日志可以记录 trace_id。

但日志也不能乱放字段，用户原文、模型回答、订单结果、API Key、Token 等敏感 payload 仍然不能进日志。
```

---

## 十、自测题

### 自测 1：生产日志和 print 最大区别是什么？

答案：

```text
print 主要是临时调试输出，通常没有稳定字段、级别、链路关联和安全规则。
生产日志是结构化事件记录，要能被检索、过滤、聚合、关联 trace/span，并且不能泄露敏感信息。
```

### 自测 2：event_name 为什么不能包含订单号或用户 ID？

答案：

```text
event_name 应该稳定表示事件类型。
订单号、用户 ID 是动态值，如果放进 event_name，会让事件名数量无限增长，导致查询、聚合和告警规则都变得困难。
动态值应该放到 attributes 里，而且敏感动态值还要谨慎或禁止。
```

### 自测 3：resource 字段回答什么问题？

答案：

```text
resource 回答“谁产生了这条日志”。
比如 service.name 表示服务名，deployment.environment.name 表示运行环境，service.version 表示服务版本。
```

### 自测 4：attributes 字段回答什么问题？

答案：

```text
attributes 回答“这一次事件发生时的具体上下文是什么”。
比如 operation、status、thread_id、agent.intent、error_code、elapsed_ms。
```

### 自测 5：ERROR 日志至少应该有哪些错误字段？

答案：

```text
至少应该有 event_name、severity_text=ERROR、severity_number、trace_id、span_id、operation、status=failed、error_code。
如果能提供，还应该有 error_node、elapsed_ms、fallback_used、thread_id。
```

### 自测 6：为什么 body 不应该放大段 JSON？

答案：

```text
body 主要给人读，应该是简短稳定的说明。
大段 JSON 可能包含敏感信息，体积大，也不利于稳定查询。
应该把需要查询的字段放 attributes，把敏感 payload 排除在日志之外。
```

### 自测 7：app_trace_id 和 trace_id 有什么区别？

答案：

```text
trace_id 在本节生产日志里表示 OpenTelemetry trace id，用于和 OTel trace/span 关联。
app_trace_id 表示项目早期自己的 X-Trace-Id 或业务请求追踪 id。
两者可能相同，也可能不同。
```

### 自测 8：thread_id 在日志里有什么价值？

答案：

```text
thread_id 能把多次请求、多轮对话、用户确认、checkpoint 恢复等业务过程串起来。
trace_id 更偏一次技术请求，thread_id 更偏一个业务会话。
智能工单 Agent 这类多轮流程很需要 thread_id。
```

### 自测 9：为什么日志字段设计也要写测试？

答案：

```text
因为日志字段是生产排查契约。
如果没人测试，字段名可能被改乱，敏感字段可能被误打进日志，错误日志可能缺少 error_code，trace_id/span_id 可能丢失。
测试能保护日志字段长期稳定。
```

### 自测 10：本节最重要的一句话是什么？

答案：

```text
生产日志不是随便打印字符串，而是可检索、可关联、可排查、受安全边界保护的结构化事件记录。
```

---

## 十一、本节命令

在 `projects/ai-service` 目录运行：

```powershell
uv run pytest tests/test_ticket_agent_production_logging.py
```

当前专项测试结果：

```text
9 passed
```

提交前还需要运行全量测试：

```powershell
uv run pytest
```

---

## 十二、本节小结

本节你真正要掌握的是：

```text
1. 生产日志是结构化事件记录，不是随便 print。
2. 一条日志应该分 top-level、resource、attributes。
3. event_name 必须稳定，不能包含动态值。
4. body 是给人看的简短说明，不是业务 payload 容器。
5. severity_text 给人看，severity_number 给机器比较。
6. trace_id/span_id 用来关联 OpenTelemetry trace/span。
7. thread_id 用来串联 LangGraph 多轮业务会话。
8. error_code 是错误日志的核心稳定字段。
9. elapsed_ms 可以帮助排查单次慢请求，但趋势统计应该交给 metrics。
10. 用户原文、模型回答、订单结果、工具参数、API Key、Token 不能直接进生产日志。
11. 日志字段设计要写测试，因为它是生产排查契约。
```

本节新增：

```text
TicketAgentLogFieldSpec
TicketAgentProductionLogRecord
build_ticket_agent_log_field_specs()
validate_ticket_agent_event_name()
normalize_ticket_agent_log_severity()
find_forbidden_ticket_agent_log_fields()
build_ticket_agent_production_log_record()
```

下一节进入：

```text
阶段 6 第 30 节：成本、token 和延迟指标
```

下一节会把第 28 节的 metrics 部分继续展开，重点学习：

```text
token 使用量怎么记录
模型调用成本怎么估算
延迟指标怎么设计
counter / histogram 怎么选
哪些字段能放进 metrics attributes
哪些字段不能放进 metrics attributes
```
