# 阶段 10 第 4 节：Python AI 服务 tracing

## 本节定位

前两节已经把 Tracing、`trace_id`、`span`、`event`、`metric` 的概念讲清楚了。

这一节开始把这些概念放回当前项目的 Python AI 服务：

```text
projects/ai-service
```

本节先不接 Jaeger、Grafana Tempo、OpenTelemetry Collector 这类外部平台。

本节先做一件更基础、更适合学习的事：

```text
给 ai-service 内部的主要 AI 链路建立一份清晰的 tracing plan。
```

也就是先明确：

```text
哪些操作应该成为 span。
哪些关键瞬间应该成为 event。
哪些整体趋势应该成为 metric。
哪些字段可以记录。
哪些字段必须禁止记录。
```

## 本节学习目标

学完本节，你要能说清楚：

1. Python AI 服务内部为什么不能只靠接口日志排查问题。
2. `/chat`、`/stream-chat`、RAG 问答、`/tool-chat` 分别应该有哪些 span。
3. LLM、RAG、rerank、Tool、Java 调用、SSE 在 tracing 里各自是什么位置。
4. 为什么 tracing 设计必须提前考虑敏感字段和高基数字段。
5. 本节新增的 `ai_service_tracing.py` 解决了什么问题，暂时没有解决什么问题。

## 本节新增和修改

| 类型 | 内容 |
|---|---|
| 新增代码 | `projects/ai-service/app/core/ai_service_tracing.py` |
| 新增测试 | `projects/ai-service/tests/test_ai_service_tracing.py` |
| 新增笔记 | `notes/stage10-04-python-ai-service-tracing.md` |
| 修改进度 | `docs/learning-progress.md` |
| 手动测试文档 | 无，本节不需要真实模型、数据库、Redis、Qdrant、Milvus 或虚拟机 |

## 一句话先讲透

Python AI 服务 tracing 的核心不是“多打几行日志”，而是把一次 AI 请求拆成稳定、可解释、可排查的 span/event/metric，并且只记录安全的元信息。

## 基础知识铺垫

### 1. Python AI 服务在整个系统里的位置

当前项目不是一个单独的 Python 小脚本。

它已经逐渐变成一个 AI 应用后端。

大致结构是：

```text
用户 / 前端
  -> Python FastAPI ai-service
      -> LLM API
      -> RAG 检索
      -> Rerank 模型
      -> Tool Calling
      -> Java Spring Boot 业务服务
          -> MySQL
          -> Redis
      -> SSE 流式输出
```

Python AI 服务是 AI 能力的编排层。

它不是只负责“调用模型”。

它还负责：

| 职责 | 说明 |
|---|---|
| 接收请求 | FastAPI 接收用户聊天、工具聊天、结构化抽取等请求 |
| 构造 prompt | 把用户输入、历史消息、规则整理成模型请求 |
| 调用 LLM | 请求 OpenAI-compatible 模型 |
| 处理流式输出 | SSE 把模型内容分块返回给客户端 |
| RAG 编排 | query rewrite、embedding、向量检索、rerank、上下文压缩、引用校验 |
| Tool Calling | 让模型提出工具请求，但由后端校验和执行 |
| 调 Java 服务 | 查询订单、创建工单等真实业务能力 |
| 安全兜底 | 参数校验、权限边界、错误码映射、敏感信息不外泄 |

所以 Python AI 服务一旦出问题，原因可能在很多地方。

### 2. 为什么只看 `/chat 200 OK` 不够

传统接口经常这样排查：

```text
POST /chat 200 OK elapsed_ms=3200
```

这能说明：

```text
HTTP 请求成功了。
接口总共花了 3.2 秒。
```

但 AI 应用里，这还远远不够。

你还需要知道：

| 想知道的问题 | 只看接口日志能不能知道 |
|---|---|
| prompt 构造是否成功 | 很难 |
| 模型调用花了多久 | 不一定 |
| 模型有没有返回空内容 | 需要单独记录 |
| 是否触发 Tool Calling | 不知道 |
| 工具参数是否通过校验 | 不知道 |
| Python 调 Java 是否超时 | 不知道 |
| Java 是权限拒绝还是订单不存在 | 不知道 |
| RAG 是否检索到有效文档 | 不知道 |
| rerank 是否触发 fallback | 不知道 |
| SSE 是否输出到一半断开 | 不知道 |

所以 Python AI 服务必须把内部链路拆开。

这就是 tracing 的价值。

### 3. Python tracing 不是一上来就接平台

很多人一听到 tracing，就立刻想到：

```text
OpenTelemetry
Jaeger
Zipkin
Grafana Tempo
Prometheus
```

这些工具很重要，但学习时不能直接跳到工具。

原因是：

```text
如果你不知道应该追踪哪些 span，接了平台也只会看到一堆没意义的数据。
```

正确顺序应该是：

1. 先理解一次请求的业务链路。
2. 再决定哪些操作应该是 span。
3. 再决定哪些关键瞬间应该是 event。
4. 再决定哪些整体数据应该是 metric。
5. 再决定哪些字段允许记录、哪些字段禁止记录。
6. 最后才接 OpenTelemetry 或具体观测平台。

本节就是做前 5 步。

### 4. 什么是 tracing plan

本节新增的 `ai_service_tracing.py` 不是完整追踪平台。

它更像一份可以被代码验证的追踪设计图。

它把下面这些东西结构化：

```text
trace_id
flow
root_span
spans
events
metrics
safe attributes
```

例如对于 `/tool-chat`：

```text
http.request
  request.validation
  llm.tool_decision
  tool.validation
  tool.execution
    java.orders.get
  llm.final_answer
```

这不是随便写在笔记里的文字。

它被放进代码和测试里。

好处是：

```text
后面继续开发时，span 名称、边界、安全字段规则不会只停留在口头约定。
```

### 5. 为什么要先做“规划对象”

你可能会问：

```text
为什么不直接把 span 打到 OpenTelemetry？
```

原因有几个。

第一，当前阶段是学习。

先做规划对象能让你看懂 tracing 的结构，不会被 SDK 细节淹没。

第二，当前项目里 AI 链路很多。

如果一上来到处加真实 span，很容易改动过大。

第三，安全字段过滤必须先确定。

AI 应用里最危险的不是“没有日志”，而是“把不该记录的东西记录了”。

第四，后续接平台时可以复用。

今天的 tracing plan，后面可以变成：

```text
OpenTelemetry span attributes
结构化日志字段
metrics labels
告警维度
面试架构说明
```

### 6. 什么是 flow

本节代码里有一个概念叫 `flow`。

它表示 Python AI 服务中的一类请求流程。

当前先定义四类：

| flow | 对应场景 |
|---|---|
| `chat` | 普通聊天 `/chat` |
| `stream_chat` | 流式聊天 `/stream-chat` |
| `rag_answer` | RAG 检索增强问答 |
| `tool_chat` | Tool Calling 聊天 `/tool-chat` |

为什么要有 flow？

因为不同请求的链路不同。

普通聊天主要是：

```text
入口 -> 参数校验 -> prompt 构造 -> LLM 调用
```

RAG 问答会多出：

```text
query rewrite -> embedding -> vector search -> rerank -> context compression
```

Tool Calling 会多出：

```text
模型工具决策 -> 工具校验 -> 工具执行 -> Java 服务调用 -> 最终总结
```

SSE 会多出：

```text
LLM stream -> SSE stream -> 客户端可能断开
```

所以不能所有接口都用同一棵 span 树。

### 7. 什么是安全属性

tracing 里会记录很多属性。

比如：

```text
service.name = ai-service
app.flow = tool_chat
http.route = /tool-chat
llm.model = qwen3.7-plus
tool.name = query_order
vector.store = qdrant
rag.top_k = 8
```

这些是安全元信息。

它们能帮助排查问题，但不会泄露用户正文和内部秘密。

危险属性包括：

```text
API Key
Authorization
完整 prompt
完整 messages
完整用户输入
完整模型回答
完整 RAG 文档内容
完整工具结果
完整订单详情
工单描述正文
数据库或向量库 token
```

本节代码会把这些字段列入禁止记录集合。

### 8. 高基数字段为什么要避开 metric

metric 用来做聚合统计。

如果 metric 标签里放入：

```text
trace_id
span_id
user_id
order_id
ticket_id
request_id
```

就会出现高基数问题。

高基数意味着：

```text
每个请求、每个用户、每个订单都产生一组新的指标序列。
```

结果是：

```text
指标数量爆炸
存储成本上升
查询变慢
告警难维护
监控平台压力变大
```

所以本节代码单独定义了：

```text
AI_SERVICE_HIGH_CARDINALITY_METRIC_ATTRIBUTE_KEYS
```

它的目的就是提醒：

```text
这些字段可以用于单次 trace 或日志排查，但不适合作为 metric 标签。
```

### 9. span 粒度怎么判断

一个操作适不适合做 span，可以问三个问题：

```text
它是否有明确开始和结束？
它是否可能明显耗时？
它是否是排查问题时的重要边界？
```

如果答案是“是”，它通常适合做 span。

例如：

| 操作 | 是否适合 span | 原因 |
|---|---|---|
| `llm.call` | 适合 | 外部模型调用，可能慢、失败、限流 |
| `vector.search` | 适合 | 外部向量检索，影响 RAG 质量和耗时 |
| `rerank.call` | 适合 | rerank 可能慢、失败、fallback |
| `tool.execution` | 适合 | 后端执行模型请求的工具，是安全边界 |
| `java.orders.get` | 适合 | 跨服务调用，可能超时、权限拒绝 |
| `sse.stream` | 适合 | 流式输出有开始结束，可能中断 |
| `tool_requested` | 不适合 span，更适合 event | 这是某一刻模型提出工具请求 |
| `permission_denied` | 不适合 span，更适合 event | 这是某一刻的权限判断结果 |

### 10. Python tracing 和 Java tracing 的关系

当前第 4 节只做 Python 侧。

下一节会学 Java 侧对齐。

关系应该是：

```text
Python 生成或接收 trace_id
Python 内部 span 记录 AI 编排过程
Python 调 Java 时传递 trace_id
Java 用同一个 trace_id 记录业务服务内部日志和错误响应
```

Python 侧要重点看：

```text
模型、RAG、Tool、SSE
```

Java 侧要重点看：

```text
鉴权、权限、MyBatis、MySQL、Redis、幂等、错误码
```

两边通过 `trace_id` 串起来。

## 本节主题系统讲解

### 1. 当前已有基础

项目里已经有早期 trace 基础：

```text
app/core/trace.py
app/middleware/tracing.py
app/core/logging.py
```

它们做了这些事：

| 文件 | 已有能力 |
|---|---|
| `trace.py` | 生成、读取、设置、重置 `trace_id` |
| `tracing.py` | FastAPI middleware 读取请求头，设置请求级 `trace_id`，响应头返回 `X-Trace-Id` |
| `logging.py` | 给日志记录自动补 `trace_id` 字段 |

这说明项目已经有“同一次请求日志能串起来”的基础。

但是它还缺少：

```text
Python 服务内部 span 划分
不同 AI flow 的 tracing 结构
event 设计
metric 设计
安全属性过滤规则
```

本节新增的 `ai_service_tracing.py` 就是补这一层。

### 2. 普通聊天 `/chat` 的 tracing

普通聊天链路最简单。

合理 span：

```text
http.request
  request.validation
  prompt.build
  llm.call
```

解释：

| span | 作用 |
|---|---|
| `http.request` | 整次接口请求的根 span |
| `request.validation` | Pydantic 请求模型校验 |
| `prompt.build` | 构造适合模型的消息和约束 |
| `llm.call` | 调用 OpenAI-compatible 模型 |

普通聊天的关键 event 可以是：

```text
llm_timeout
fallback_triggered
```

虽然当前项目还没有真正实现模型 fallback，但先把事件设计出来，后面第 11 节学习 fallback 时就能接上。

### 3. 流式聊天 `/stream-chat` 的 tracing

流式聊天比普通聊天多一个重要边界：

```text
SSE 输出
```

合理 span：

```text
http.request
  request.validation
  prompt.build
  llm.stream
  sse.stream
```

`llm.stream` 表示服务端从模型获取流式 chunk。

`sse.stream` 表示 Python 服务把 chunk 通过 SSE 返回给客户端。

这两个不能混成一个。

原因是：

| 问题 | 应该看哪个 span |
|---|---|
| 模型首 token 很慢 | `llm.stream` |
| 服务端拿到 chunk 但客户端收不到 | `sse.stream` |
| 客户端主动断开 | `sse.stream` event |
| 模型流中途报错 | `llm.stream` |

流式相关 event：

```text
sse_client_disconnected
stream_error_sent
timeout
```

### 4. RAG 问答的 tracing

RAG 链路是 AI 应用里最容易出问题的部分之一。

合理 span：

```text
http.request
  request.validation
  rag.query_rewrite
  embedding.call
  vector.search
  rerank.call
  context.compression
  llm.final_answer
```

解释：

| span | 排查价值 |
|---|---|
| `rag.query_rewrite` | 看查询改写是否执行、是否异常 |
| `embedding.call` | 看 embedding 模型是否慢、失败、维度异常 |
| `vector.search` | 看 Qdrant/Milvus 检索耗时、top_k、collection |
| `rerank.call` | 看 rerank 是否改变排序、是否 fallback |
| `context.compression` | 看上下文压缩是否过度裁剪 |
| `llm.final_answer` | 看最终模型是否依据上下文回答 |

关键 event：

```text
prompt_injection_detected
rag_no_relevant_context
rerank_fallback_used
citation_verification_failed
```

RAG 的问题经常不是 HTTP 错误，而是质量问题。

例如：

```text
检索为空
检索到无关内容
rerank 把好文档排下去了
上下文压缩删掉了关键句子
模型没有引用来源
```

这些都需要 tracing + eval 一起观察。

### 5. Tool Calling `/tool-chat` 的 tracing

Tool Calling 链路必须特别重视。

原因是：

```text
模型只能提出工具请求，后端必须校验和执行。
```

合理 span：

```text
http.request
  request.validation
  llm.tool_decision
  tool.validation
  tool.execution
    java.orders.get
  llm.final_answer
```

解释：

| span | 排查价值 |
|---|---|
| `llm.tool_decision` | 看模型是否正确请求工具 |
| `tool.validation` | 看工具名和参数是否通过后端校验 |
| `tool.execution` | 看后端是否真的执行工具 |
| `java.orders.get` | 看 Python 调 Java 查订单是否成功 |
| `llm.final_answer` | 看模型是否基于工具结果总结 |

关键 event：

```text
tool_requested
tool_validation_failed
permission_denied
timeout
fallback_triggered
```

这里最重要的理解是：

```text
Tool Calling 的 tracing 不只是性能排查，也是安全边界排查。
```

例如：

| 问题 | tracing 应该能看到什么 |
|---|---|
| 模型请求了不存在的工具 | `tool_validation_failed` |
| 模型参数缺少订单号 | `tool_validation_failed` |
| 用户无权看订单 | `permission_denied` |
| Java 服务超时 | `timeout` on `java.orders.get` |
| 工具成功但模型总结错 | `tool.execution` 成功，`llm.final_answer` 需要排查 |

### 6. 本节为什么没有直接修改 `/chat` 路由

本节没有把 tracing plan 强行塞进所有接口。

这是有意控制边界。

原因是：

```text
当前先建立稳定的追踪设计和安全字段规则。
等第 5 节 Java tracing 对齐、第 6 节 LLM 日志安全、第 9 节耗时拆解学完后，再决定哪些地方真正打点。
```

如果现在立刻大范围改路由、service、RAG、Tool、SSE，容易出现两个问题：

1. 改动太大，不利于学习。
2. 还没学日志安全和耗时拆解，容易记录过多或记录错误字段。

所以本节是：

```text
先把追踪模型建出来，并用测试固定。
```

后续再逐步接入真实运行路径。

### 7. 本节代码形成的能力

本节新增后，项目具备这些能力：

| 能力 | 说明 |
|---|---|
| flow 分类 | 区分普通聊天、流式聊天、RAG、Tool Chat |
| span plan | 每类 flow 有稳定 span 名称和父子关系 |
| event plan | 每类 flow 有推荐关键事件 |
| metric plan | 每类 flow 有基础指标 |
| 安全属性过滤 | 禁止 prompt、用户正文、API Key 等敏感信息进入 attributes |
| metric 低基数规则 | 防止 trace_id、user_id、order_id 等进入 metric 标签 |
| trace_id 复用 | 可以显式传入 trace_id，也可以复用当前请求上下文里的 trace_id |

### 8. 本节还没有做什么

本节没有做：

```text
接入 OpenTelemetry SDK
接入 Jaeger / Tempo
真实创建 span 并上报
修改所有业务函数打点
真实统计 Prometheus metrics
真实采样策略
真实告警
```

这些不是遗漏。

它们会在后续阶段逐步补。

当前重点是：

```text
让你真正理解 Python AI 服务内部 tracing 应该怎么设计。
```

## 本节代码讲解

### 1. `AiServiceFlow`

文件：

```text
projects/ai-service/app/core/ai_service_tracing.py
```

核心类型：

```text
AiServiceFlow = Literal["chat", "stream_chat", "rag_answer", "tool_chat"]
```

它的作用是把 Python AI 服务的主要请求流程分组。

为什么这样做？

因为不同 flow 的链路不同。

如果不区分 flow，就会出现：

```text
普通聊天也记录 vector.search。
RAG 问答忘记记录 rerank.call。
Tool Chat 忘记记录 java.orders.get。
SSE 问题和 LLM 问题混在一起。
```

### 2. `AiServiceSpanSpec`

它表示一个 span 设计。

关键字段：

| 字段 | 含义 |
|---|---|
| `name` | span 名称，比如 `llm.call` |
| `kind` | span 类型，比如 `SERVER`、`CLIENT`、`INTERNAL` |
| `parent_name` | 父 span 名称，用来表达链路层级 |
| `attributes` | 安全元信息 |
| `status` | 当前预留状态字段，后续可用于 OK / ERROR |

这里的重点不是 dataclass 语法，而是 span 的边界。

例如 `java.orders.get` 的 `parent_name` 是：

```text
tool.execution
```

这说明 Java 调用是工具执行的一部分。

### 3. `AiServiceEventSpec`

它表示一个关键事件设计。

例如：

```text
tool_requested
permission_denied
sse_client_disconnected
rag_no_relevant_context
```

它包含：

| 字段 | 含义 |
|---|---|
| `name` | 事件名 |
| `span_name` | 事件挂在哪个 span 上 |
| `severity` | 事件级别 |
| `attributes` | 事件安全属性 |

这能帮助你理解：

```text
事件不是孤立存在的，它应该挂在某个 span 上。
```

### 4. `AiServiceMetricSpec`

它表示一个指标设计。

例如：

```text
ai_service.request.count
ai_service.request.duration
ai_service.llm.calls
ai_service.tool.calls
ai_service.java.client.duration
ai_service.rag.retrieval.duration
```

这些当前还没有真实上报到 Prometheus。

但它们已经明确了以后要观察什么。

metric 的重点是：

```text
看整体趋势，不是还原某一次请求细节。
```

所以代码会过滤高基数字段。

### 5. `build_ai_service_span_attributes`

这个函数负责构造安全 attributes。

它会放入：

```text
service.name
app.flow
app.operation
app.trace_id
http.route
http.method
llm.model
llm.provider
tool.name
vector.store
vector.collection
rag.top_k
```

它会拒绝：

```text
api_key
authorization
prompt
messages
history
user_message
final_answer
tool_result
document_content
chunk_content
ticket_description
```

这点非常重要。

AI 应用 tracing 不能只考虑“排查方便”，还要考虑“记录后是否安全”。

### 6. `build_python_ai_service_tracing_plan`

这是本节最核心的函数。

它根据 flow 生成对应的：

```text
root_span
spans
events
metrics
```

比如：

```text
flow="tool_chat"
```

会生成：

```text
http.request
request.validation
llm.tool_decision
tool.validation
tool.execution
java.orders.get
llm.final_answer
```

比如：

```text
flow="rag_answer"
```

会生成：

```text
http.request
request.validation
rag.query_rewrite
embedding.call
vector.search
rerank.call
context.compression
llm.final_answer
```

这就是把前面学的概念真正放进项目代码。

### 7. 本节测试重点

新增测试：

```text
projects/ai-service/tests/test_ai_service_tracing.py
```

主要覆盖：

| 测试点 | 目的 |
|---|---|
| Tool Chat span | 确认模型决策、工具校验、工具执行、Java 调用、最终总结都被纳入 |
| RAG span | 确认 query rewrite、embedding、vector search、rerank、context compression、final answer 都被纳入 |
| SSE span | 确认 `llm.stream` 和 `sse.stream` 分开 |
| 敏感字段过滤 | 确认 prompt、user_message、Authorization 不会进入 attributes |
| metric 低基数 | 确认 metric 不使用 trace_id 等高基数字段 |
| trace_id 复用 | 确认可以复用当前请求上下文里的 trace_id |

测试不真实调用模型。

这符合我们的自动化测试边界：

```text
自动测试验证代码逻辑和安全边界，不依赖外部模型服务。
```

## 常见误区

### 误区 1：Python 里有日志就不需要 tracing

不对。

日志能说明某个时刻发生了什么。

Tracing 要说明一次请求经过了哪些阶段，每个阶段之间有什么关系。

### 误区 2：所有接口用同一套 span

不合适。

普通聊天、RAG、Tool Chat、SSE 的链路不同。

统一成一套 span 会导致不是漏记，就是记录无关信息。

### 误区 3：先接 OpenTelemetry，后面再想记录什么

顺序反了。

应该先理解业务链路和安全边界，再接 SDK 和平台。

否则平台里会出现大量低价值数据。

### 误区 4：为了排查，把 prompt 和用户消息也放进 attributes

这是危险做法。

prompt、用户消息、模型回答、RAG 文档正文、工具结果都可能包含敏感信息。

应记录安全摘要或元信息，而不是完整内容。

### 误区 5：metric 标签越多越好

不对。

metric 标签应优先使用低基数字段。

`trace_id`、`user_id`、`order_id`、`ticket_id` 这类字段不适合作为 metric 标签。

### 误区 6：Tool Calling tracing 只是为了看耗时

不够。

Tool Calling tracing 还要看安全边界：

```text
模型请求了什么工具
后端是否允许
参数是否通过校验
用户是否有权限
工具结果是否被模型正确总结
```

### 误区 7：SSE 慢一定是模型慢

不一定。

可能是：

```text
模型首 token 慢
服务端写 SSE 慢
客户端断开
网络问题
流式中途异常
```

所以 `llm.stream` 和 `sse.stream` 要分开。

## 本节练习

### 练习 1：给 `/chat` 设计 span

请写出普通聊天 `/chat` 的最小 span 树。

参考答案：

```text
http.request
  request.validation
  prompt.build
  llm.call
```

解释：

普通聊天没有 RAG、Tool、Java 调用，核心是入口、校验、prompt 构造和模型调用。

### 练习 2：为什么 `/tool-chat` 要有 `tool.validation`

参考答案：

因为模型只能提出工具请求，不能直接代表后端执行工具。

后端必须校验：

```text
工具名是否允许
参数结构是否合法
工具是否属于当前用户可用范围
写操作是否需要确认
```

所以 `tool.validation` 是 AI Tool Calling 的安全边界。

### 练习 3：下面哪些字段不应该进入 tracing attributes

请判断：

```text
llm.model
http.route
prompt
user_message
tool.name
authorization
vector.collection
document_content
rag.top_k
```

参考答案：

不应该进入：

```text
prompt
user_message
authorization
document_content
```

可以进入：

```text
llm.model
http.route
tool.name
vector.collection
rag.top_k
```

原因：

后者是排查需要的安全元信息，前者可能包含隐私、密钥或大量敏感正文。

### 练习 4：为什么 RAG 要把 `vector.search` 和 `rerank.call` 分开

参考答案：

因为它们解决的问题不同，失败方式也不同。

`vector.search` 负责从向量库召回候选文档。

`rerank.call` 负责对候选文档重新排序。

如果不分开，就无法判断：

```text
是向量检索没找到好文档，
还是 rerank 把好文档排下去了，
还是 rerank 模型本身超时或 fallback。
```

### 练习 5：为什么 metric 不应该带 `trace_id`

参考答案：

`trace_id` 每次请求都不同，属于高基数字段。

如果把它放进 metric 标签，会导致指标序列数量爆炸，增加存储成本和查询压力。

`trace_id` 应用于单次请求排查，不适合用于聚合指标标签。

## 自测题

### 自测 1：Python AI 服务 tracing 的第一步是什么

参考答案：

第一步不是接平台，而是先梳理业务链路，确定哪些操作是 span、哪些关键瞬间是 event、哪些趋势是 metric，以及哪些字段可以安全记录。

### 自测 2：`flow` 在本节代码里代表什么

参考答案：

`flow` 代表 Python AI 服务里的一类请求流程，比如普通聊天、流式聊天、RAG 问答、Tool Chat。不同 flow 对应不同 span 树。

### 自测 3：为什么 `java.orders.get` 是 Python tracing 里的 span

参考答案：

因为它是 Python 调 Java 的跨服务调用，有明确开始和结束，可能耗时、失败、超时或被权限拒绝，是排查 AI 工具链路的重要边界。

### 自测 4：为什么本节不直接接 OpenTelemetry

参考答案：

因为当前学习重点是理解 tracing 设计和安全边界。先把 span/event/metric 结构设计清楚，后续再接 OpenTelemetry 才不会生成低价值或不安全的数据。

### 自测 5：`llm.stream` 和 `sse.stream` 有什么区别

参考答案：

`llm.stream` 表示 Python 服务从模型获取流式内容，`sse.stream` 表示 Python 服务把内容通过 SSE 输出给客户端。模型慢和客户端断开是两个不同问题，所以要分开追踪。

### 自测 6：本节新增代码最重要的安全规则是什么

参考答案：

不要把 API Key、Authorization、完整 prompt、用户消息、模型回答、RAG 文档正文、工具结果、订单详情、工单描述等敏感内容放进 tracing attributes。

### 自测 7：如果用户说工具调用很慢，你应该优先看哪些 span

参考答案：

优先看：

```text
llm.tool_decision
tool.validation
tool.execution
java.orders.get
llm.final_answer
```

这样可以判断慢在模型决策、工具校验、Java 调用，还是最终总结。

## 本节小结

本节完成了 Python AI 服务 tracing 的第一步落地：

```text
不是先接平台，而是先建立清晰、可测试、安全的 tracing plan。
```

你现在应该能说清楚：

```text
/chat 应该追踪 prompt.build 和 llm.call。
/stream-chat 应该区分 llm.stream 和 sse.stream。
RAG 应该追踪 query rewrite、embedding、vector search、rerank、context compression 和 final answer。
/tool-chat 应该追踪 llm.tool_decision、tool.validation、tool.execution、java.orders.get 和 llm.final_answer。
tracing attributes 只能记录安全元信息，不能记录完整敏感内容。
metric 标签要避免高基数字段。
```

下一节是阶段 10 第 5 节：

```text
Java 业务服务 tracing 对齐
```

它会接着本节继续学习：

```text
Python 调 Java 时如何传递 trace_id，
Java 服务如何让日志、错误码、响应头和 Python AI 链路对齐。
```
