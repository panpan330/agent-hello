# 阶段 10 第 3 节：trace_id / span / event / metric 的区别

## 本节定位

上一节我们学习了 Tracing 是什么。

这一节继续把 Tracing 里面最容易混淆的四个词讲清楚：

```text
trace_id / span / event / metric
```

这四个词不是同一层东西。

它们分别回答四类问题：

| 概念 | 回答的问题 |
|---|---|
| trace_id | 这是哪一次请求 |
| span | 这次请求经过了哪一段操作 |
| event | 某一段操作里发生了什么关键瞬间 |
| metric | 很多请求汇总后，整体表现怎么样 |

## 本节学习目标

学完本节，你要能说清楚：

1. `trace_id`、`span`、`event`、`metric` 分别是什么。
2. 为什么只有 `trace_id` 不等于完成了 Tracing。
3. 为什么 `span` 适合描述一段有开始和结束的操作。
4. 为什么 `event` 适合描述一个瞬间发生的关键事情。
5. 为什么 `metric` 不是单次请求明细，而是聚合后的趋势数据。
6. 在当前 AI 客服工单系统里，哪些东西应该是 span，哪些应该是 event，哪些应该是 metric。

## 本节新增和修改

| 类型 | 内容 |
|---|---|
| 新增笔记 | `notes/stage10-03-trace-span-event-metric.md` |
| 修改进度 | 更新 `docs/learning-progress.md` |
| 新增业务代码 | 无 |
| 手动测试文档 | 无，纯知识节不需要 |

## 一句话先讲透

`trace_id` 是一次请求的身份证，`span` 是这次请求里的每一段路程，`event` 是某段路程中发生的关键瞬间，`metric` 是把大量请求汇总后得到的可观察指标。

## 基础知识铺垫

### 1. 为什么要把这四个概念分开

在刚开始学习可观测性时，很容易出现一个误解：

```text
只要日志里有 trace_id，就算有 tracing 了。
```

这句话只对了一小部分。

`trace_id` 的确很重要，因为它能把同一次请求的日志串起来。

但它只能告诉你：

```text
这些日志属于同一次请求。
```

它不能直接告诉你：

```text
这次请求经过了哪些步骤？
每一步花了多久？
哪一步失败了？
失败发生在模型调用、RAG 检索、rerank、工具执行、Java 服务，还是数据库？
哪个步骤触发了 fallback？
哪个步骤被限流？
哪个步骤导致 token 成本升高？
```

这些问题需要 `span`、`event`、`metric` 一起配合。

可以先用一个生活化类比理解：

| 类比 | 对应概念 |
|---|---|
| 快递单号 | trace_id |
| 揽收、运输、到站、派送这些阶段 | span |
| 某个时刻发生的异常，比如地址错误、超时、拒收 | event |
| 一天内总派送量、平均时长、超时率、投诉率 | metric |

快递单号很重要，但只有快递单号还不够。

如果用户问：

```text
为什么我的快递慢？
```

你只回答：

```text
你的快递单号是 X。
```

这并不能解决问题。

你需要知道它卡在了哪一段，什么时候发生了什么异常，以及类似问题是不是正在大量出现。

AI 应用也是一样。

### 2. 可观测性到底观察什么

生产系统不是只要能返回结果就行。

真正上线以后，我们要回答这些问题：

| 问题 | 需要的能力 |
|---|---|
| 单个用户这次请求为什么慢 | trace + span |
| 单个用户这次请求为什么失败 | trace + span + event + log |
| 过去 1 小时整体错误率是不是升高 | metric |
| 主模型今天是不是经常 fallback | metric + event |
| RAG 检索是不是经常找不到相关文档 | metric + trace |
| 某个订单查询被拒绝是权限问题还是工具问题 | trace + event |
| 上线新 prompt 后质量有没有下降 | eval + metric + bad case |

这里要注意：

```text
可观测性不是一个单独工具，而是一套看系统运行状态的方法。
```

常见的基础组成包括：

| 类型 | 作用 |
|---|---|
| Logs 日志 | 记录具体发生了什么 |
| Traces 链路 | 记录一次请求经过了哪些步骤 |
| Metrics 指标 | 记录整体趋势和聚合数据 |
| Evaluations 评估 | 判断 AI 回答质量是否符合预期 |

传统后端通常会强调 logs、traces、metrics。

AI 应用还要额外重视 evaluations，因为模型回答可能 HTTP 成功但语义错误。

### 3. trace_id 是什么

`trace_id` 是一次请求的全局标识。

简单说：

```text
同一次请求，无论它经过 Python、Java、Redis、MySQL、LLM、向量库，只要属于同一条链路，就应该能看到同一个 trace_id。
```

例如用户发起一次聊天请求：

```text
用户：帮我查一下订单 A1001 的物流状态
```

系统内部可能经过：

```text
FastAPI /chat
LLM 判断是否需要工具
Python 执行 query_order
Java business service 查询订单
MySQL 查询订单表
LLM 总结工具结果
SSE 输出回答
```

这些步骤都应该带着同一个 `trace_id`。

这样当用户说“刚才那次回答错了”，你才能按 `trace_id` 找到整条链路。

`trace_id` 的关键特点：

| 特点 | 说明 |
|---|---|
| 全局唯一 | 一次请求一个 trace_id，避免不同请求混在一起 |
| 跨服务传递 | Python 调 Java 时要通过 header 传过去 |
| 不表达步骤 | 它只标识同一次请求，不表示每一步 |
| 不应该包含业务隐私 | 不要把手机号、订单详情、用户问题塞进 trace_id |
| 适合排查单个请求 | 通过它找到这次请求的完整记录 |

### 4. span 是什么

`span` 是一次请求链路中的一段操作。

它有开始时间、结束时间、耗时、名称、状态和属性。

例如：

```text
llm.call
rag.retrieval
vector.search
rerank.call
tool.execution
java.orders.get
db.query
sse.stream
```

这些都可以是 span。

为什么？

因为它们都有明显的开始和结束。

比如 `llm.call`：

```text
开始：准备好请求，调用模型 API
结束：收到模型响应或抛出异常
耗时：1280ms
状态：success / error / timeout
```

比如 `java.orders.get`：

```text
开始：Python 发起 HTTP GET /internal/orders/A1001
结束：Java 返回订单响应
耗时：86ms
状态：success / error
```

span 的关键特点：

| 特点 | 说明 |
|---|---|
| 表示一段操作 | 不是瞬间，而是有持续时间 |
| 可以嵌套 | 根 span 下面可以有多个子 span |
| 可以计算耗时 | 每个 span 都能知道自己花了多久 |
| 可以标记状态 | success、error、timeout、cancelled |
| 可以带属性 | model、route、tool_name、collection、top_k 等 |

### 5. span 为什么要有父子关系

一次 AI 请求不是平铺的一堆步骤，而是有层级关系的。

例如：

```text
POST /chat
  llm.tool_decision
  tool.execution query_order
    java.orders.get
      db.orders.select
  llm.final_answer
  sse.stream
```

这表示：

```text
POST /chat 是整次请求的根 span。
llm.tool_decision 是它下面的一个子 span。
tool.execution query_order 也是它下面的子 span。
java.orders.get 又是 tool.execution 下面的子 span。
db.orders.select 又是 java.orders.get 下面的子 span。
```

父子关系的价值很大。

它能帮助你判断：

| 你想知道的问题 | span 树能怎么回答 |
|---|---|
| 总耗时主要花在哪里 | 看最慢的子 span |
| Java 慢还是模型慢 | 对比 java.orders.get 和 llm.call |
| RAG 慢还是 rerank 慢 | 对比 vector.search 和 rerank.call |
| 工具失败影响了哪个上游流程 | 看 tool.execution 的父 span |
| SSE 输出慢是生成慢还是网络慢 | 看 llm.final_answer 和 sse.stream |

没有 span 树，只靠日志顺序，很难直观看出这些关系。

### 6. event 是什么

`event` 是某个时间点发生的一件关键事情。

它不是一段持续操作，而是一个瞬间。

例如：

```text
prompt_injection_detected
fallback_triggered
retry_attempt
permission_denied
tool_validation_failed
timeout
sse_client_disconnected
```

这些适合做 event。

为什么它们不一定适合做 span？

因为它们通常不是一段需要计算耗时的操作，而是某个时刻发生的状态变化或关键事实。

例如：

```text
fallback_triggered
```

它表示：

```text
系统决定从主模型切换到备用模型。
```

这个决定发生在某个时刻。

真正耗时的部分，应该是前后的模型调用 span：

```text
llm.call primary_model
event: fallback_triggered
llm.call backup_model
```

再例如：

```text
permission_denied
```

它表示：

```text
Java 服务判断当前用户无权访问订单。
```

权限校验本身可能很快，没必要单独变成一个复杂 span。

但这个事件非常重要，因为它解释了为什么工具没有返回订单数据。

event 的关键特点：

| 特点 | 说明 |
|---|---|
| 表示关键瞬间 | 某个时刻发生的事实 |
| 通常没有持续时间 | 不强调耗时 |
| 常挂在某个 span 上 | 说明这个阶段发生了什么 |
| 适合记录异常、状态变化、关键决策 | fallback、retry、拒绝、校验失败 |
| 不适合塞大正文 | 不要把完整 prompt、完整文档、完整订单放进去 |

### 7. metric 是什么

`metric` 是聚合指标。

它不是为了还原某一次请求的细节，而是为了观察一段时间内系统整体怎么样。

例如：

```text
request_count
error_rate
p95_latency
llm_token_total
llm_cost_total
fallback_rate
rag_hit_rate
tool_failure_rate
rate_limited_count
```

这些都属于 metric。

metric 适合回答：

| 问题 | 指标 |
|---|---|
| 今天请求量多少 | request_count |
| 错误率有没有升高 | error_rate |
| 大部分用户是不是觉得慢 | p95_latency |
| 今天模型花了多少钱 | llm_cost_total |
| 主模型是不是不稳定 | fallback_rate |
| RAG 是否经常检索不到 | rag_empty_result_rate |
| 工具调用是否经常失败 | tool_failure_rate |
| 是否被大量限流 | rate_limited_count |

metric 的核心价值是：

```text
看趋势，看整体，看告警。
```

如果某个小时 `fallback_rate` 从 1% 升到 35%，你不需要先去翻每条日志，就能知道系统有异常。

然后再通过具体 trace 找样本排查原因。

### 8. metric 不是日志，也不是 trace

很多初学者会把 metric 当成“高级日志”。

这个理解不准确。

日志和 trace 偏向明细。

metric 偏向统计。

例如：

```text
某一次请求的 trace_id 是 abc123，LLM 调用耗时 1850ms。
```

这是 trace/span 明细。

而：

```text
过去 5 分钟 llm.call 的 P95 耗时是 3200ms。
```

这是 metric。

metric 不关心某一次请求的完整故事。

它关心一批请求形成的统计结果。

### 9. attributes / tags 是什么

无论是 span、event 还是 metric，通常都会带一些属性。

这些属性也常被叫做 attributes、tags、labels。

例如 span 属性：

```text
span_name = llm.call
model = qwen3.7-plus
provider = aliyun_dashscope_compatible
route = /chat
status = success
elapsed_ms = 1420
```

例如 metric 标签：

```text
metric = llm_request_count
model = qwen3.7-plus
route = /chat
status = success
```

属性的作用是帮助筛选、分组和定位问题。

但属性不是越多越好。

尤其不能把高敏感内容和高基数字段随便放进去。

### 10. 什么是高基数

基数可以理解为“可能出现多少种不同取值”。

低基数字段：

```text
status = success / error
model = qwen3.7-plus / backup-model
route = /chat /rag/query
tool_name = query_order / create_ticket
```

高基数字段：

```text
user_id = 每个用户都不同
trace_id = 每次请求都不同
order_id = 每个订单都不同
prompt = 几乎每次都不同
```

高基数不是一定不能用。

在 trace 或日志里，`trace_id` 是必要的。

但在 metric 标签里，随便使用高基数字段会造成严重问题：

```text
指标数量爆炸
存储成本升高
查询变慢
监控系统压力变大
告警难以维护
```

所以原则是：

| 场景 | 适合放什么 |
|---|---|
| trace/span 属性 | 可以放 trace_id、span_id、tool_name、model、route，敏感字段要谨慎 |
| log 字段 | 可以放 trace_id、错误码、节点名、耗时，不放完整敏感正文 |
| metric 标签 | 放低基数字段，比如 route、model、status、tool_name |
| metric 数值 | 放耗时、次数、token 数、成本、错误数量 |

### 11. P50 / P95 / P99 是什么

学习 metric 时，经常会看到：

```text
P50 latency
P95 latency
P99 latency
```

它们是分位数。

假设有 100 次请求，按耗时从小到大排序：

| 指标 | 含义 |
|---|---|
| P50 | 第 50 个左右的耗时，中位数水平 |
| P95 | 第 95 个左右的耗时，能反映大部分慢请求体验 |
| P99 | 第 99 个左右的耗时，能反映极端慢请求 |

为什么不用平均值就够了？

因为平均值会掩盖尾部慢请求。

例如 100 次请求：

```text
95 次在 500ms 内完成
5 次花了 15s
```

平均值可能看起来还能接受，但那 5 个用户体验很差。

AI 应用特别需要关注 P95/P99。

原因是模型调用、向量检索、rerank、工具调用、外部 API 都可能出现长尾耗时。

### 12. context propagation 是什么

context propagation 可以理解为“上下文传递”。

在 tracing 里，最重要的上下文包括：

```text
trace_id
span_id
parent_span_id
sampling decision
```

当前项目里，你已经接触过 `X-Trace-Id`。

它的作用是：

```text
Python AI 服务收到请求后生成或读取 trace_id。
Python 调 Java 服务时，把 trace_id 放进请求头。
Java 服务把 trace_id 放进日志 MDC、响应头和错误响应里。
```

以后如果接入标准 OpenTelemetry，还会接触：

```text
traceparent
```

它比 `X-Trace-Id` 更标准，因为它不只传 trace_id，还会传 span_id 等上下文。

这节先不用急着写代码，但要理解原则：

```text
跨服务调用时，追踪上下文必须继续传递，否则链路会断。
```

### 13. sampling 是什么

sampling 是采样。

为什么需要采样？

因为线上系统请求量很大，如果每一次请求都记录完整 trace，成本可能很高。

常见策略：

| 策略 | 说明 |
|---|---|
| 全量采样 | 每次请求都记录，适合本地开发和低流量阶段 |
| 固定比例采样 | 例如只记录 10% 请求 |
| 错误全采样 | 出错请求尽量全部保留 |
| 慢请求采样 | 超过阈值的请求保留 |
| 重要用户或重要接口采样 | 对关键链路提高采样率 |

AI 应用常见做法是：

```text
普通成功请求按比例采样。
失败、超时、fallback、权限拒绝、prompt injection 命中、工具执行失败尽量保留。
```

这样既能控制成本，又能保留排查问题最有价值的数据。

### 14. 安全和隐私边界

Tracing 很有用，但不能因为要排查问题，就什么都记录。

尤其是 AI 应用，输入输出里可能有大量敏感信息。

不要记录：

```text
API Key
Authorization header
完整用户隐私内容
完整 prompt
完整模型回答
完整 RAG 文档正文
完整订单详情
完整工单描述
数据库连接串
内部 token
```

可以记录：

```text
trace_id
span_name
route
model
provider
tool_name
status
error_code
elapsed_ms
token_count
document_count
top_k
rerank_top_n
fallback_used
permission_result
```

一句话：

```text
Tracing 记录的是系统运行线索，不是把用户数据和内部秘密完整复制一份。
```

## 本节主题系统讲解

### 1. 四个概念的边界总表

| 概念 | 属于哪一层 | 关注点 | 是否表示耗时 | 是否用于单次请求排查 | 是否用于整体趋势 |
|---|---|---|---|---|---|
| trace_id | 请求标识 | 这是不是同一次请求 | 否 | 是 | 否 |
| span | 链路片段 | 某一步做了什么、花了多久 | 是 | 是 | 可汇总 |
| event | 关键事件 | 某一刻发生了什么重要事情 | 通常否 | 是 | 可汇总 |
| metric | 聚合指标 | 一批请求整体表现如何 | 聚合后可以 | 否 | 是 |

这张表很重要。

以后你看到一个信息时，可以先问：

```text
它是在标识一次请求？
它是在描述一段操作？
它是在描述一个瞬间事件？
它是在统计很多请求的整体表现？
```

这个判断能帮助你决定它应该放在哪里。

### 2. 当前项目里的一次请求应该长什么样

以用户问题为例：

```text
我的订单 A1001 为什么还没发货？
```

系统可能执行：

```text
1. FastAPI 接收 /chat 请求
2. 校验请求体
3. 调用模型判断是否需要工具
4. 模型请求 query_order
5. 后端校验工具名和参数
6. Python 调 Java business service
7. Java 做内部鉴权、用户权限校验、订单查询
8. Java 返回订单白名单字段
9. Python 把工具结果交给模型总结
10. SSE 或普通响应返回给用户
```

如果用 trace/span/event/metric 表达，可以是：

```text
trace_id = req_abc123

span: http.request /chat
  span: request.validation
  span: llm.tool_decision
  span: tool.validation
  span: tool.execution query_order
    span: java.orders.get
      span: java.auth.check
      span: db.orders.select
  span: llm.final_answer
  span: sse.stream
```

某些关键瞬间可以是 event：

```text
event: tool_requested
event: tool_validation_passed
event: permission_denied
event: fallback_triggered
event: retry_attempt
event: sse_client_disconnected
```

整体统计可以是 metric：

```text
chat_request_count
chat_error_rate
chat_p95_latency_ms
llm_call_count
llm_token_total
llm_cost_total
tool_execution_failure_rate
java_order_query_p95_latency_ms
```

### 3. trace_id 在当前项目里的职责

当前项目已经有跨 Python 和 Java 的 trace_id 基础。

它的职责是：

```text
把同一次请求在不同模块中的记录串起来。
```

例如：

```text
Python 日志：trace_id=abc tool_execution_started tool_name=query_order
Java 日志：trace_id=abc GET /internal/orders/A1001
Java 响应：trace_id=abc
Python 日志：trace_id=abc tool_execution_finished
```

这样排查时能按 `trace_id=abc` 找到同一条链路。

但这还不是完整 tracing。

因为你还需要知道：

```text
Python 哪个 span 最慢？
Java 哪个 span 最慢？
模型调用是否发生了 fallback？
RAG 是否检索为空？
SSE 是不是中断了？
```

这些要继续用 span、event、metric 补齐。

### 4. span 在当前项目里应该怎么划分

span 不应该过粗，也不应该过细。

过粗的问题：

```text
只有一个 span: /chat
耗时 10s
```

你只知道整个接口慢，不知道哪里慢。

过细的问题：

```text
每一行代码都建一个 span
```

数据太吵，成本高，排查也更困难。

当前项目比较合理的 span 粒度：

| span 名称 | 表示什么 |
|---|---|
| `http.request` | 一次入口请求 |
| `request.validation` | 请求参数校验 |
| `rag.query_rewrite` | 查询改写 |
| `rag.intent_detection` | RAG 查询意图识别 |
| `embedding.call` | embedding 模型调用 |
| `vector.search` | Qdrant/Milvus 向量检索 |
| `hybrid.search` | 混合检索 |
| `rerank.call` | rerank 模型调用 |
| `context.compression` | 上下文压缩 |
| `llm.call` | 大模型调用 |
| `tool.decision` | 模型是否请求工具 |
| `tool.validation` | 后端校验工具名和参数 |
| `tool.execution` | 后端执行工具 |
| `java.orders.get` | Python 调 Java 查订单 |
| `java.tickets.create` | Python 调 Java 创建工单 |
| `db.query` | Java 内部数据库查询 |
| `redis.get` / `redis.set` | Java 内部缓存和幂等操作 |
| `sse.stream` | 流式输出 |

命名要稳定。

不要今天叫 `call_llm`，明天叫 `llm_request`，后天叫 `model_call`。

名称稳定，后面做指标统计、告警和排查才方便。

### 5. event 在当前项目里应该怎么用

event 适合记录关键转折点。

当前项目适合的 event：

| event 名称 | 什么时候记录 |
|---|---|
| `tool_requested` | 模型提出工具调用请求 |
| `tool_validation_failed` | 工具名或参数校验失败 |
| `permission_denied` | Java 服务拒绝用户访问订单或工单 |
| `fallback_triggered` | 主模型失败后切备用模型 |
| `retry_attempt` | 对可重试错误发起重试 |
| `timeout` | 某个阶段超时 |
| `rate_limited` | 请求被限流 |
| `prompt_injection_detected` | 检测到提示词注入风险 |
| `rag_no_relevant_context` | RAG 没找到足够相关上下文 |
| `sse_client_disconnected` | 流式输出时客户端断开 |
| `idempotency_replayed` | 写操作命中幂等结果 |

event 的价值不是替代日志。

它更像是在 trace 里标记：

```text
这一步发生了一个需要特别关注的事情。
```

排查时，你能在一条 trace 中很快看到关键转折点。

### 6. metric 在当前项目里应该怎么设计

metric 面向整体趋势。

当前项目后续至少应该关注这些指标：

| 指标 | 说明 |
|---|---|
| `chat_request_count` | 聊天请求总数 |
| `chat_error_rate` | 聊天接口错误率 |
| `chat_latency_p95_ms` | 聊天接口 P95 耗时 |
| `llm_call_count` | 模型调用次数 |
| `llm_latency_p95_ms` | 模型调用 P95 耗时 |
| `llm_prompt_tokens_total` | prompt token 总量 |
| `llm_completion_tokens_total` | completion token 总量 |
| `llm_cost_total` | 模型调用总成本 |
| `rag_retrieval_count` | RAG 检索次数 |
| `rag_empty_result_rate` | 检索为空比例 |
| `rerank_call_count` | rerank 调用次数 |
| `tool_call_count` | 工具调用次数 |
| `tool_failure_rate` | 工具失败率 |
| `java_order_latency_p95_ms` | Java 订单查询 P95 耗时 |
| `fallback_rate` | fallback 触发比例 |
| `rate_limited_count` | 限流次数 |
| `prompt_injection_detected_count` | 注入风险命中次数 |

这些指标以后会用于：

```text
看趋势
做仪表盘
设置告警
观察上线变化
评估成本
辅助容量规划
```

例如：

```text
fallback_rate 突然升高
```

可能说明：

```text
主模型不稳定
主模型被限流
请求超时阈值太短
网络到模型供应商不稳定
```

这时先看 metric 发现异常，再找具体 trace 排查样本。

### 7. 四者如何配合排查问题

假设用户反馈：

```text
刚才 AI 客服查订单很慢，而且最后说不清楚。
```

排查顺序可以是：

1. 用 `trace_id` 找到这次请求。
2. 看 span 树，定位耗时主要在哪个阶段。
3. 看 event，确认是否发生 fallback、权限拒绝、工具校验失败、超时等关键事件。
4. 看日志，补充错误码和异常上下文。
5. 看 metric，判断这是单个请求偶发问题，还是系统整体异常。

例如 trace 显示：

```text
http.request /chat: 12800ms
  llm.tool_decision: 900ms
  tool.execution query_order: 620ms
    java.orders.get: 580ms
  llm.final_answer: 10800ms
    event: fallback_triggered
```

这时你可以判断：

```text
慢主要不是 Java 查询，而是最终总结模型调用慢，并且发生了 fallback。
```

如果 metric 又显示：

```text
fallback_rate 最近 10 分钟从 1% 升到 40%
llm_latency_p95_ms 同时升高
```

就说明这不是用户单次偶发，而可能是模型供应商或模型路由策略问题。

### 8. AI 应用为什么更依赖这些概念

传统后端一般更确定：

```text
请求进来
查数据库
执行业务规则
返回结果
```

AI 应用更不确定：

```text
模型可能直接回答
模型可能请求工具
模型可能参数提错
RAG 可能检索不到
rerank 可能改变排序
工具可能被权限拒绝
模型可能超时或限流
fallback 可能改变回答风格
SSE 可能输出一半断开
```

所以 AI 应用不能只看：

```text
HTTP 200
接口耗时
错误日志
```

还要看：

```text
模型选择
token 消耗
检索质量
工具调用决策
权限边界
fallback
prompt injection
输出安全
用户体验
```

这也是阶段 10 为什么要系统学习可追踪、成本、性能、稳定性、安全、评估、告警和回滚。

### 9. 一个判断规则

以后你不知道某个信息应该放在哪里，可以用这套判断：

```text
如果它用来串起同一次请求：trace_id
如果它是一段有开始和结束的操作：span
如果它是某一刻发生的关键事实：event
如果它是很多请求汇总后的统计：metric
如果它是详细文本说明或异常堆栈：log
如果它是回答质量判断：eval
```

例如：

| 信息 | 应该放哪里 |
|---|---|
| 这次请求编号是 abc | trace_id |
| LLM 调用花了 2 秒 | span |
| 主模型失败切备用模型 | event |
| 过去 5 分钟错误率 8% | metric |
| Java 返回 ORDER_ACCESS_DENIED | log + event + span status |
| 用户问题完整文本 | 不建议完整放入 trace 属性 |
| prompt 是否越权 | eval 或安全检测结果 |
| 检索 top_k 是 8 | span attribute |
| 今天总 token 成本 | metric |

## 本节代码讲解

本节没有新增业务代码。

但你可以先记住未来实现时大概会出现的结构。

一个 span 可能包含：

```text
trace_id: req_abc123
span_id: span_llm_001
parent_span_id: span_chat_root
name: llm.call
status: success
start_time: 2026-08-01T10:00:00
end_time: 2026-08-01T10:00:01.420
attributes:
  model: qwen3.7-plus
  provider: aliyun
  route: /chat
  prompt_tokens: 1200
  completion_tokens: 180
```

一个 event 可能包含：

```text
trace_id: req_abc123
span_id: span_llm_001
name: fallback_triggered
time: 2026-08-01T10:00:00.700
attributes:
  from_model: primary
  to_model: backup
  reason: timeout
```

一个 metric 可能是：

```text
metric_name: llm_latency_p95_ms
value: 3200
labels:
  model: qwen3.7-plus
  route: /chat
  status: success
time_window: 5m
```

这些不是让你现在死记格式，而是先建立结构感。

后面第 4 节和第 5 节，我们会把这些概念落到 Python AI 服务和 Java 业务服务里。

## 常见误区

### 误区 1：有 trace_id 就等于有完整 tracing

不对。

`trace_id` 只是链路标识。

完整 tracing 还需要 span、事件、状态、耗时、属性和跨服务上下文传递。

### 误区 2：所有东西都应该做成 span

不对。

span 表示一段操作，应该有开始、结束和耗时。

像 `fallback_triggered`、`permission_denied`、`retry_attempt` 这类瞬间发生的关键事实，更适合做 event。

### 误区 3：metric 里可以随便放 trace_id、user_id、order_id

不建议。

metric 标签应该尽量低基数。

`trace_id`、`user_id`、`order_id` 这类高基数字段会导致指标数量膨胀，增加存储和查询压力。

### 误区 4：span 越细越专业

不对。

span 太细会让 trace 变得很吵，排查成本反而升高。

合理原则是：

```text
围绕重要外部调用、耗时阶段、业务边界、安全边界和可能失败的节点建 span。
```

### 误区 5：只记录失败链路

不够。

失败链路当然重要，但成功链路也有价值。

因为你需要知道正常请求是什么样子，才能判断异常请求哪里不正常。

### 误区 6：为了排查方便，把完整 prompt 和模型回答都放进 trace

不应该。

这会带来隐私和安全风险。

更合理的做法是记录安全摘要、长度、token 数、模板版本、模型名、错误码、文档数量、工具名等元信息。

### 误区 7：metric 能替代 trace

不能。

metric 能告诉你整体异常升高。

trace 才能告诉你某一次请求到底发生了什么。

它们是配合关系，不是替代关系。

## 本节练习

### 练习 1：判断下列信息应该属于哪类

请判断下面的信息更适合属于 `trace_id`、`span`、`event` 还是 `metric`。

1. 一次请求的编号是 `req_001`。
2. `llm.call` 花了 1800ms。
3. 主模型超时后切换到备用模型。
4. 过去 5 分钟 `/chat` 的错误率是 3%。
5. `vector.search` 检索出 8 条候选文档。
6. 用户在 SSE 输出过程中断开连接。

参考答案：

1. `trace_id`。它用来标识同一次请求。
2. `span`。`llm.call` 是一段有开始和结束的操作，耗时 1800ms。
3. `event`。fallback 是某一刻发生的关键决策。
4. `metric`。这是聚合后的整体错误率。
5. `span attribute`。`vector.search` 是 span，候选文档数量是这个 span 的属性。
6. `event`。客户端断开是流式输出 span 中的关键瞬间。

### 练习 2：给当前项目设计一个最小 span 树

场景：

```text
用户问订单 A1001 的物流状态，模型请求 query_order，Python 调 Java，Java 查 MySQL，最后模型总结回答。
```

请写出一个最小 span 树。

参考答案：

```text
http.request /chat
  llm.tool_decision
  tool.validation
  tool.execution query_order
    java.orders.get
      db.orders.select
  llm.final_answer
```

解释：

这棵树没有把每一行代码都做成 span，而是抓住了关键边界：

```text
入口请求
模型决策
工具校验
工具执行
跨服务 Java 调用
数据库查询
最终模型总结
```

### 练习 3：哪些字段不适合放进 metric 标签

下面哪些字段不适合放进 metric 标签？

```text
route
model
status
trace_id
user_id
order_id
tool_name
prompt
```

参考答案：

不适合：

```text
trace_id
user_id
order_id
prompt
```

原因：

这些字段基数太高，或者包含敏感内容。

适合：

```text
route
model
status
tool_name
```

原因：

这些字段取值数量相对可控，适合做分组统计。

### 练习 4：为什么 P95 比平均值更适合观察 AI 请求体验

参考答案：

AI 请求容易出现长尾耗时。

例如大部分请求 1 秒完成，但少量请求因为模型、RAG、rerank、工具或网络问题花 15 秒。

平均值可能被摊平，看起来不严重。

P95 能更好反映大部分慢请求用户的体验，因此更适合做性能观察和告警参考。

## 自测题

### 自测 1：一句话解释 trace_id

参考答案：

`trace_id` 是一次请求的全局标识，用来把同一次请求在不同服务、模块和日志中的记录串起来。

### 自测 2：一句话解释 span

参考答案：

`span` 是一次请求链路中的一段有开始和结束的操作，用来记录这个阶段做了什么、花了多久、是否成功。

### 自测 3：一句话解释 event

参考答案：

`event` 是某个 span 中某一刻发生的关键事实，比如 fallback、重试、权限拒绝、工具参数校验失败。

### 自测 4：一句话解释 metric

参考答案：

`metric` 是把大量请求汇总后的指标，用来看整体趋势、性能、错误率、成本和告警。

### 自测 5：为什么不能把完整 prompt 放进 trace 属性

参考答案：

因为完整 prompt 可能包含用户隐私、业务敏感信息、内部策略和系统提示。Tracing 应记录安全元信息，而不是完整复制敏感上下文。

### 自测 6：如果 `/chat` 总耗时 12 秒，你会先看什么

参考答案：

先根据 `trace_id` 找到这次请求，再看 span 树，定位耗时主要集中在哪个 span，比如 `llm.call`、`vector.search`、`rerank.call`、`tool.execution`、`java.orders.get` 或 `sse.stream`。

### 自测 7：如果 fallback_rate 突然升高，你会怎么排查

参考答案：

先通过 metric 确认 fallback_rate 升高的时间范围、模型和接口；再抽样查看具体 trace，观察哪些 span 失败或超时，并查看 `fallback_triggered` event 的原因。

### 自测 8：span 过粗和过细分别有什么问题

参考答案：

span 过粗只能看到整体慢，不知道慢在哪里。

span 过细会产生太多噪声和成本，排查时反而难以抓住重点。

合理做法是围绕重要外部调用、耗时阶段、业务边界、安全边界和可能失败的节点建 span。

## 本节小结

这一节你要真正记住的不是名词，而是边界：

```text
trace_id：标识一次请求。
span：描述一次请求里的阶段。
event：记录某个阶段里的关键瞬间。
metric：统计很多请求后的整体趋势。
```

在 AI 客服工单系统里，这四者会一起工作：

```text
用 trace_id 找到某次请求。
用 span 看它经过了哪些步骤和每步耗时。
用 event 看关键异常和决策。
用 metric 看问题是不是整体性趋势。
```

下一节会进入阶段 10 第 4 节：

```text
Python AI 服务 tracing
```

也就是开始把这些概念放回 `ai-service`，学习 Python 服务内部应该如何设计请求入口、LLM、RAG、rerank、Tool、SSE 等链路追踪。
