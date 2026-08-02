# 阶段 10 第 9 节：请求耗时拆解

## 本节定位

这一节学习 AI 应用生产化里的性能排查基础：

```text
一次请求为什么慢，慢在哪里，应该怎么拆开看。
```

前面已经学了 tracing、日志安全、配置密钥、token 成本。

这一节把注意力放到：

```text
请求耗时。
```

## 本节学习目标

- 理解总耗时、阶段耗时、未归因耗时、瓶颈阶段。
- 理解为什么 AI 请求比普通 CRUD 请求更容易慢。
- 理解 LLM、RAG、rerank、Tool、Java 后端、SSE 各自可能慢在哪里。
- 理解耗时拆解和 trace/span、日志、metric、成本统计的关系。
- 看懂本节新增的 `request_timing.py` 和 middleware 总请求耗时摘要。

## 本节新增和修改

- 新增 `app/core/request_timing.py`。
- 新增 `tests/test_request_timing.py`。
- 修改 `app/middleware/tracing.py`，在 HTTP 请求结束日志里补充瓶颈摘要字段。
- 更新学习进度。

## 一句话先讲透

请求耗时拆解就是：

```text
不要只看一次请求总共用了多久，而要把它拆成 validation、RAG、embedding、vector search、rerank、LLM、tool、Java、serialization、SSE 等阶段，找出真正拖慢请求的那一段。
```

## 基础知识铺垫

### 1. 什么是请求总耗时

请求总耗时就是：

```text
服务端从收到请求开始，到返回响应结束，一共花了多少时间。
```

例如当前 middleware 里已经有：

```text
request_started
request_finished elapsed_ms=123.45
```

这说明：

```text
这次 HTTP 请求整体耗时 123.45 ms。
```

总耗时很重要。

因为用户最终感受到的是：

```text
我等了多久。
```

但是只看总耗时不够。

如果一次请求用了 5000 ms，你只知道：

```text
它很慢。
```

但你不知道：

```text
是模型慢？
是向量库慢？
是 rerank 慢？
是 Java 后端慢？
是 Redis 慢？
是数据库慢？
是网络慢？
是序列化慢？
是等待流式输出慢？
```

这就是为什么要做耗时拆解。

### 2. 什么是阶段耗时

阶段耗时就是：

```text
把一次请求内部拆成多个步骤，每个步骤单独记录耗时。
```

例如一次 RAG 问答可以拆成：

```text
request.validation
rag.query_rewrite
embedding.call
vector.search
rerank.call
context.compression
llm.final_answer
response.serialization
```

每个阶段都有自己的耗时：

```text
request.validation = 5 ms
embedding.call = 120 ms
vector.search = 80 ms
rerank.call = 200 ms
llm.final_answer = 1800 ms
serialization = 10 ms
```

这样你就能看出来：

```text
真正慢的是 llm.final_answer。
```

而不是盲目优化数据库或路由。

### 3. 什么是瓶颈阶段

瓶颈阶段就是：

```text
本次请求里耗时最长、最可能影响整体响应速度的阶段。
```

例如：

```text
vector.search = 100 ms
rerank.call = 300 ms
llm.final_answer = 2500 ms
```

瓶颈就是：

```text
llm.final_answer
```

瓶颈不一定永远固定。

不同请求可能不同：

```text
短问题可能是向量库慢。
长问题可能是 LLM 慢。
复杂 Agent 可能是工具链慢。
Java 后端故障时可能是 java.orders.get 慢。
流式响应可能是 first token 慢。
```

所以瓶颈需要按请求、按接口、按模型、按时间段观察。

### 4. 什么是未归因耗时

未归因耗时就是：

```text
总耗时 - 已记录阶段耗时之和。
```

例如：

```text
总耗时 = 1000 ms
已记录阶段：
  validation = 30 ms
  vector.search = 220 ms
  llm.final_answer = 600 ms

已记录阶段总和 = 850 ms
未归因耗时 = 150 ms
```

未归因耗时说明：

```text
还有一部分时间没有被明确拆出来。
```

它可能来自：

```text
框架调度
依赖注入
中间件
序列化
网络缓冲
日志写入
线程切换
没有被埋点的业务代码
```

未归因耗时不是一定错误。

但如果它很大，就说明：

```text
你的耗时拆解还不够完整。
```

### 5. 为什么 AI 请求比普通 CRUD 更容易慢

普通 CRUD 请求常见流程：

```text
HTTP 请求
参数校验
查数据库
组装响应
返回
```

AI 请求可能是：

```text
HTTP 请求
参数校验
构造 prompt
调用 LLM
解析模型输出
检索 RAG
调用 embedding
向量库搜索
rerank
调用工具
请求 Java 后端
再调用 LLM 总结
流式输出
记录 trace/log/metric
```

它比普通 CRUD 多了很多外部依赖：

```text
模型平台
向量数据库
rerank 服务
Java 业务服务
Redis
MySQL
MCP Server
```

外部依赖越多：

```text
网络耗时越不可控。
超时风险越高。
失败点越多。
排查越复杂。
```

所以 AI 应用必须更重视耗时拆解。

### 6. LLM 调用可能慢在哪里

LLM 慢不只是“模型慢”四个字。

它可能慢在：

```text
连接模型服务慢。
模型排队慢。
prompt 太长，输入处理慢。
输出太长，生成慢。
模型本身规格更大，推理慢。
供应商当前负载高。
网络抖动。
SDK 内部重试。
```

如果只看：

```text
llm.call elapsed_ms=5000
```

你还需要结合：

```text
prompt_tokens
completion_tokens
model
provider
retry_count
timeout
cost
```

才能判断为什么慢。

### 7. RAG 检索可能慢在哪里

RAG 通常不只有一个步骤。

它可能包括：

```text
query rewrite
embedding
vector search
metadata filter
hybrid search
rerank
context compression
citation verification
final answer
```

如果 RAG 总耗时 4 秒，不能直接说：

```text
RAG 慢。
```

你要拆开看：

```text
embedding.call = 800 ms
vector.search = 50 ms
rerank.call = 1200 ms
llm.final_answer = 1900 ms
```

这样才知道：

```text
embedding、rerank、最终回答都占比较高。
```

优化方向就不同：

```text
embedding 慢：看批处理、缓存、模型选择、网络。
vector search 慢：看索引、过滤条件、top_k、向量库状态。
rerank 慢：看候选数量、rerank 模型、超时降级。
final answer 慢：看上下文长度、模型选择、输出长度。
```

### 8. Tool Calling 可能慢在哪里

Tool Calling 请求通常可能有两次模型调用：

```text
第一次：模型决定是否调用工具。
工具执行：后端校验、权限、Java 查询。
第二次：模型根据工具结果生成最终回答。
```

所以可以拆成：

```text
llm.tool_decision
tool.validation
tool.execution
java.orders.get
llm.final_answer
```

如果用户说：

```text
查订单很慢。
```

你要知道慢的可能不是 Java 订单接口。

也可能是：

```text
模型决定工具用了很久。
工具结果回传后最终总结用了很久。
```

这就是阶段耗时拆解的价值。

### 9. Java 后端可能慢在哪里

Python 调 Java 时，可能慢在：

```text
Python HTTP client 建连。
Java 网关或过滤器。
内部鉴权。
限流。
Controller。
Service。
Redis。
MyBatis。
MySQL。
权限查询。
幂等检查。
响应序列化。
网络返回。
```

Python 侧能看到：

```text
java.orders.get = 300 ms
```

Java 侧如果也有 trace，就能继续拆：

```text
java.http.request = 300 ms
redis.rate_limit = 5 ms
mybatis.order.select = 120 ms
service.permission_check = 20 ms
```

这就是阶段 10 第 5 节讲的：

```text
Python + Java tracing 对齐。
```

### 10. SSE 流式输出的耗时要怎么看

流式输出和普通响应不一样。

普通响应关注：

```text
整个响应什么时候结束。
```

流式响应还要关注：

```text
首 token 延迟。
两段 chunk 之间间隔。
总流式持续时间。
客户端是否中断。
服务端是否卡住。
```

用户体验上：

```text
首 token 快，用户会觉得系统反应快。
```

即使总输出需要 10 秒，只要 1 秒内开始出字，体验也可能能接受。

所以 SSE 的耗时拆解通常会有：

```text
llm.stream
sse.first_token
sse.stream
sse.client_disconnect
```

本节先不深做 SSE，后面第 16、17 节会专门讲。

### 11. 耗时拆解和 trace/span 的关系

trace 是一次完整请求链路。

span 是链路里的一个阶段。

所以耗时拆解和 span 天然相关：

```text
每个 span 通常都有 start_time、end_time、duration。
```

例如：

```text
trace_id = abc
span http.request = 2000 ms
span llm.call = 1500 ms
span vector.search = 100 ms
span rerank.call = 300 ms
```

耗时拆解可以理解成：

```text
从 trace/span 角度观察性能。
```

本节新增的 `RequestTimingStage` 和 `RequestTimingBreakdown` 还不是完整 OpenTelemetry span。

它更像：

```text
项目内部用于表达阶段耗时的轻量结构。
```

以后接入真实 OTel 时，它可以变成 span 属性或 metric 数据来源。

### 12. 耗时拆解和日志的关系

日志适合记录单次请求：

```text
request_finished elapsed_ms=...
bottleneck_stage=...
bottleneck_elapsed_ms=...
```

优点：

```text
排查某个 trace_id 时容易看。
本地开发也容易看。
不用先搭建复杂监控平台。
```

缺点：

```text
日志不适合大量聚合。
日志查询成本高。
日志字段如果设计不好容易泄露敏感内容。
```

所以本节仍然遵守：

```text
阶段耗时记录只放安全元信息，不放用户原文、prompt、tool_result、API Key。
```

### 13. 耗时拆解和 metric 的关系

metric 适合做趋势：

```text
ai_service.request.duration
ai_service.llm.duration
ai_service.rag.retrieval.duration
ai_service.java.client.duration
```

它可以回答：

```text
过去 5 分钟 p95 延迟是多少？
哪个接口最近变慢？
模型调用平均耗时是否升高？
Java client p99 是否异常？
```

但是 metric 标签要控制基数。

适合做标签：

```text
route
flow
model
provider
status
```

不适合做标签：

```text
trace_id
user_message
order_id
ticket_id
完整 prompt
```

这就是本节 `request_timing.py` 过滤高基数字段的原因。

### 14. 耗时拆解和成本统计的关系

第 8 节讲的是：

```text
一次模型调用用了多少 token，大概花了多少钱。
```

第 9 节讲的是：

```text
一次请求每个阶段用了多少时间。
```

两者结合后，你可以判断：

```text
哪个阶段又慢又贵。
哪个阶段慢但不贵。
哪个阶段贵但不慢。
哪个阶段适合缓存。
哪个阶段适合换模型。
哪个阶段适合降级。
```

例如：

```text
llm.final_answer = 3000 ms, estimated_cost = 0.05
```

这说明它既慢又贵。

优化可能是：

```text
缩短 RAG 上下文。
降低 max_output_tokens。
换更快模型。
增加缓存。
调整 prompt。
```

### 15. 耗时拆解和超时治理的关系

后面会学超时治理。

超时治理需要知道：

```text
每个阶段应该给多少时间预算。
```

如果总超时是 10 秒，你可能会拆：

```text
embedding <= 1s
vector.search <= 500ms
rerank <= 1s
LLM final answer <= 6s
Java tool <= 1s
预留框架和序列化 <= 500ms
```

没有阶段耗时数据，就很难定合理超时。

### 16. 耗时拆解和 fallback 的关系

如果某个阶段太慢，可以 fallback。

例如：

```text
rerank.call 超时：跳过 rerank，用原始检索顺序。
vector.search 超时：返回无资料兜底。
llm.final_answer 超时：返回稍后重试。
Java tool 超时：告诉用户业务系统暂时不可用。
```

但 fallback 不能乱做。

要结合：

```text
阶段耗时
阶段重要性
用户体验
数据安全
写操作幂等
是否允许降级
```

### 17. 本节要形成的判断能力

看到一个慢请求时，不要只说：

```text
模型慢。
系统卡。
网络问题。
```

你要能问：

```text
总耗时是多少？
拆了哪些阶段？
瓶颈阶段是哪一个？
瓶颈占总耗时多少？
未归因耗时是否过大？
是否有外部依赖超时？
是否有重试？
是否有高 token？
是否有 RAG 上下文过长？
是否是流式首 token 慢？
Python 和 Java trace_id 是否能串起来？
```

这就是生产排查思维。

## 本节主题系统讲解

### 1. 当前项目原来的耗时记录

项目原来已经有很多局部耗时：

```text
HTTP middleware request_finished elapsed_ms
LLMChatService llm_chat_succeeded elapsed_ms
RagAnswerService rag_answer_succeeded elapsed_ms
ToolCallingChatService tool_chat_succeeded elapsed_ms
JavaOrderClient java_order_request_finished elapsed_ms
JavaTicketClient java_ticket_create_finished elapsed_ms
```

这说明：

```text
项目已经有总耗时和部分阶段耗时。
```

但问题是：

```text
这些耗时还没有统一结构。
```

所以本节补：

```text
RequestTimingStage
RequestTimingBreakdown
```

它们是统一表达“阶段耗时”的基础。

### 2. 为什么不直接大改所有业务链路

你可能会问：

```text
既然要做耗时拆解，为什么不把 RAG、Tool、Java、LLM 全部重构一遍？
```

原因是：

```text
这会导致本节改动太大。
```

当前阶段的学习目标是先搞懂：

```text
耗时拆解的数据结构和安全边界。
```

如果一节课同时重构所有业务链路，会把重点变成：

```text
大量改代码。
大量修测试。
```

反而不利于理解本节主题。

所以本节采用：

```text
先建立通用工具。
先接入 HTTP 总请求摘要。
后续章节再按需要逐步接入 RAG、Tool、SSE、Java 等阶段。
```

### 3. 新增 `request_timing.py` 的职责

新增文件：

```text
app/core/request_timing.py
```

它负责：

```text
定义阶段耗时结构。
定义请求耗时拆解结构。
计算已测量耗时。
计算未归因耗时。
找出瓶颈阶段。
计算瓶颈占比。
生成安全日志字段。
过滤敏感字段和高基数字段。
根据路由推断 flow。
```

它不负责：

```text
真实调用模型。
真实调用向量库。
真实调用 Java。
写数据库。
发 metric 到监控平台。
接入 OpenTelemetry exporter。
```

职责边界很清楚：

```text
它只是表达和整理耗时数据。
```

### 4. `RequestTimingStage` 表示什么

`RequestTimingStage` 表示：

```text
一次请求里的一个阶段。
```

字段包括：

```text
name
kind
elapsed_ms
status
attributes
```

例如：

```text
name = llm.final_answer
kind = client
elapsed_ms = 600
status = ok
attributes = {"llm.model": "qwen3.7-plus"}
```

`kind` 用来区分：

```text
server：服务端入口或输出阶段。
internal：服务内部计算阶段。
client：调用外部依赖阶段。
```

LLM、向量库、Java 后端都属于 client。

### 5. `RequestTimingBreakdown` 表示什么

`RequestTimingBreakdown` 表示：

```text
一次请求的完整耗时拆解。
```

字段包括：

```text
trace_id
flow
route
method
status
total_elapsed_ms
stages
attributes
```

它还能计算：

```text
measured_elapsed_ms
unaccounted_elapsed_ms
bottleneck_stage
stage_percent()
to_log_fields()
```

也就是说，它不是简单存数据。

它还封装了排查时最常用的几个判断。

### 6. `flow` 为什么重要

`flow` 表示请求类型。

当前本节支持：

```text
chat
stream_chat
rag_answer
tool_chat
health
unknown
```

为什么需要 flow？

因为不同 flow 的阶段不同。

例如：

```text
chat：prompt.build + llm.call
rag_answer：embedding + vector.search + rerank + llm.final_answer
tool_chat：llm.tool_decision + tool.execution + java.orders.get + llm.final_answer
stream_chat：llm.stream + sse.stream
```

如果没有 flow，你很难按类型聚合性能。

### 7. 为什么要过滤敏感字段

耗时记录需要 attributes。

但不能什么都放。

禁止放：

```text
prompt
messages
user_message
query
final_answer
raw_response
tool_result
document_content
chunk_content
api_key
authorization
token
```

这些字段可能泄露隐私、密钥、业务数据或上下文。

耗时拆解只需要：

```text
阶段名
耗时
模型名
provider
route
status
vector.store
retry.count
fallback_used
```

### 8. 为什么要过滤高基数字段

高基数字段是指：

```text
取值非常多、几乎每次请求都不同的字段。
```

比如：

```text
trace_id
span_id
user_id
session_id
thread_id
order_id
ticket_id
request_id
```

这些字段不是一定不能记录。

但不能随便进入 metric 标签或通用耗时 attributes。

本节把它们过滤掉，是为了保持：

```text
耗时字段适合后续转成 metric 或结构化日志。
```

trace_id 本身在 `RequestTimingBreakdown` 顶层保留，不让外部 attributes 覆盖。

### 9. protected fields 的作用

本节定义了 protected fields。

例如：

```text
app.trace_id
app.flow
http.route
http.method
request.status
request.total_elapsed_ms
request.bottleneck_stage
```

外部 attributes 不能覆盖它们。

原因是：

```text
核心字段必须由系统自己计算，不能被调用方传入的 extra attributes 改掉。
```

这和第 6 节 LLM 日志安全、第 7 节配置安全是同一个思想。

### 10. middleware 本节改了什么

本节修改了：

```text
app/middleware/tracing.py
```

原来请求结束日志是：

```text
request_finished method=... path=... status_code=... elapsed_ms=...
```

现在增加：

```text
bottleneck_stage=...
bottleneck_elapsed_ms=...
```

当前阶段只接入了总请求本身，所以瓶颈阶段是：

```text
http.request
```

这看起来很简单，但它有两个价值：

```text
middleware 已经开始使用统一 timing 工具。
后续可以逐步把内部阶段接进来。
```

### 11. 当前版本的边界

当前版本还没有做到：

```text
自动把每个业务函数耗时都塞进同一个 breakdown。
```

原因是这需要更大的上下文传播设计。

例如需要决定：

```text
用 request.state 保存 timing collector？
用 ContextVar 保存当前 request timing？
用 decorator 包阶段？
用 OpenTelemetry span 直接承载？
同步代码和异步代码怎么兼容？
流式响应什么时候结束？
```

这些问题后续可以继续做。

本节先完成：

```text
统一数据形状。
安全字段边界。
middleware 总请求接入。
测试固定行为。
```

## 本节代码讲解

### 1. `RequestTimingStage`

核心代码：

```python
@dataclass(frozen=True)
class RequestTimingStage:
    name: str
    kind: RequestStageKind
    elapsed_ms: float
    status: RequestStageStatus = "ok"
    attributes: dict[str, RequestTimingValue] | None = None
```

它表示一个阶段。

`frozen=True` 表示创建后不希望被随便改。

这适合耗时记录：

```text
记录一旦生成，就应该代表当时事实。
```

### 2. `RequestTimingBreakdown`

它表示一次请求的耗时拆解。

重要属性：

```python
measured_elapsed_ms
unaccounted_elapsed_ms
bottleneck_stage
stage_percent()
to_log_fields()
```

这些属性让调用方不用重复写计算逻辑。

### 3. `build_request_timing_stage`

这个函数负责创建阶段。

它会做：

```text
阶段名安全归一化。
elapsed_ms 校验和四舍五入。
attributes 过滤。
```

如果阶段名为空，会报错。

如果耗时是负数、无穷大、非数字，也会报错。

### 4. `build_request_timing_breakdown`

这个函数负责创建请求级 breakdown。

它会：

```text
解析 trace_id。
规范 method 为大写。
校验 total_elapsed_ms。
复制 stages。
过滤 attributes。
```

如果没有传 trace_id，会尝试复用当前 ContextVar 里的 trace_id。

### 5. `infer_request_timing_flow`

这个函数根据路由推断 flow：

```text
/chat -> chat
/stream-chat -> stream_chat
/rag... -> rag_answer
/tool... -> tool_chat
/health 或 /ready -> health
其他 -> unknown
```

它让 middleware 不需要硬编码很多业务判断。

### 6. `build_total_http_request_timing_breakdown`

这个函数把 HTTP 总请求包装成一个最小 breakdown。

当前阶段只有一个 stage：

```text
http.request
```

它用 status_code 判断：

```text
< 500 -> ok
>= 500 -> error
```

后续如果内部阶段接进来，`http.request` 会成为总阶段，内部还会有更多子阶段。

### 7. middleware 使用方式

请求结束时：

```python
timing = build_total_http_request_timing_breakdown(...)
timing_fields = timing.to_log_fields()
```

然后日志里记录：

```text
elapsed_ms
bottleneck_stage
bottleneck_elapsed_ms
```

注意：

```text
middleware 没有记录用户请求体。
没有记录 Authorization。
没有记录 API Key。
```

这符合前几节的安全要求。

## 常见误区

### 误区 1：看到总耗时高，就直接说模型慢

不一定。

可能是：

```text
RAG 检索慢。
rerank 慢。
Java 后端慢。
工具链慢。
序列化慢。
SSE 首 token 慢。
```

必须拆阶段。

### 误区 2：只记录 LLM 耗时就够了

不够。

AI 请求里 LLM 很重要，但不是唯一阶段。

RAG、Tool、Java、Redis、MySQL 都可能是瓶颈。

### 误区 3：阶段耗时之和必须等于总耗时

不一定。

可能有未归因耗时。

关键是：

```text
未归因耗时不能长期过大。
```

如果长期很大，说明埋点不完整。

### 误区 4：耗时 attributes 里放越多越好

不是。

attributes 只放排查需要的安全元信息。

不要放：

```text
prompt
用户原文
完整回答
工具结果
文档正文
API Key
```

### 误区 5：trace_id 适合做 metric 标签

不适合。

trace_id 每次请求都不同，是高基数字段。

它适合日志和 trace 关联，不适合作为 metric 标签。

### 误区 6：流式响应只看总耗时

流式响应要特别关注：

```text
首 token 延迟
chunk 间隔
总流式时间
客户端中断
```

后续 SSE 生产化会继续学。

## 本节练习

### 练习 1：计算未归因耗时

已知：

```text
total_elapsed_ms = 1200
validation = 20
embedding = 150
vector.search = 80
llm.final_answer = 800
```

未归因耗时是多少？

参考答案：

```text
已记录阶段总和 = 20 + 150 + 80 + 800 = 1050
未归因耗时 = 1200 - 1050 = 150 ms
```

### 练习 2：找瓶颈阶段

已知：

```text
embedding.call = 180 ms
vector.search = 70 ms
rerank.call = 600 ms
llm.final_answer = 900 ms
```

瓶颈阶段是什么？

参考答案：

```text
llm.final_answer。
```

因为它耗时最长。

### 练习 3：为什么不能把 user_message 放进耗时 attributes

参考答案：

```text
因为 user_message 可能包含隐私和业务敏感信息。
耗时拆解只需要阶段名、耗时、状态、模型名、provider 等安全元信息，不需要用户原文。
```

### 练习 4：RAG 慢时应该拆哪些阶段

参考答案：

```text
至少拆 query rewrite、embedding、vector search、metadata filter、rerank、context compression、final answer。
如果有引用校验，也应该单独观察。
```

### 练习 5：Tool Chat 慢时不应该只看什么

参考答案：

```text
不应该只看 Java 后端耗时。
还要看 llm.tool_decision、tool.validation、tool.execution、java.orders.get、llm.final_answer。
```

### 练习 6：为什么耗时拆解能帮助超时治理

参考答案：

```text
因为超时治理需要知道每个阶段通常耗时多少，才能给 embedding、vector search、rerank、LLM、Java 工具等阶段分配合理时间预算。
```

## 自测题

### 自测 1：总耗时和阶段耗时的区别是什么

参考答案：

```text
总耗时表示一次请求从开始到结束一共用了多久。
阶段耗时表示请求内部某个步骤用了多久。
总耗时告诉你慢不慢，阶段耗时告诉你慢在哪里。
```

### 自测 2：什么是瓶颈阶段

参考答案：

```text
瓶颈阶段是本次请求里耗时最长、最可能拖慢整体响应的阶段。
```

### 自测 3：什么是未归因耗时

参考答案：

```text
未归因耗时 = 总耗时 - 已记录阶段耗时之和。
它表示还有一部分时间没有被明确归到某个阶段。
```

### 自测 4：耗时拆解和 trace/span 的关系是什么

参考答案：

```text
trace 表示一次完整请求链路，span 表示链路里的阶段。
每个 span 通常都有自己的 duration，所以耗时拆解本质上就是从 span 角度观察一次请求的性能。
```

### 自测 5：为什么 AI 请求比普通 CRUD 更需要耗时拆解

参考答案：

```text
AI 请求通常包含模型调用、RAG、embedding、向量库、rerank、工具调用、Java 后端、流式输出等多个外部依赖和复杂阶段，任何一个阶段都可能成为瓶颈。
```

### 自测 6：为什么耗时字段要过滤高基数字段

参考答案：

```text
因为 trace_id、user_id、order_id 等字段取值非常多，如果作为 metric 标签会导致指标基数爆炸，增加监控系统压力。
```

## 本节小结

这一节你要记住：

```text
慢请求不能只看总耗时，要拆阶段、找瓶颈、看占比、看未归因耗时。
```

当前项目新增了：

```text
RequestTimingStage
RequestTimingBreakdown
infer_request_timing_flow
build_total_http_request_timing_breakdown
```

并让 HTTP middleware 开始输出：

```text
request_finished ... elapsed_ms=... bottleneck_stage=... bottleneck_elapsed_ms=...
```

这只是耗时拆解的第一步。

后续学习超时、重试、fallback、SSE、监控和告警时，会继续依赖这个思路：

```text
先知道慢在哪里，再决定怎么优化。
```
