# 阶段 6 第 30 节：成本、token 和延迟指标

本节目标：真正理解 LLM 应用为什么必须监控 `token`、`成本` 和 `延迟`，并学会把一次模型调用转成可以用于趋势分析、告警和成本控制的 metrics。

你要能回答这些问题：

```text
1. token 是什么？
2. prompt_tokens、completion_tokens、total_tokens 分别是什么？
3. 为什么 token 会影响成本？
4. 为什么 token 会影响延迟？
5. 单次日志里的 elapsed_ms 和 metrics 里的 duration 有什么区别？
6. LLM 调用次数应该用 counter 还是 histogram？
7. LLM 延迟应该用 counter 还是 histogram？
8. token 使用量为什么适合用 histogram？
9. 成本指标为什么不能写死模型价格？
10. metrics attributes 里哪些字段可以放，哪些字段不能放？
11. 为什么 trace_id/thread_id/user_message 不能进 metrics attributes？
12. 当前智能工单 Agent 应该如何设计 LLM 相关指标？
```

这节不真实调用大模型。

这节也不写死任何真实模型价格。

原因很简单：

```text
模型价格会变化，不应该写死在代码和笔记里。
```

本节会用可配置的单价来演示成本估算：

```text
输入 token 单价
输出 token 单价
```

这样你学到的是可迁移的工程方法，而不是背某个模型当前一时的价格表。

---

## 一、本节在主线里的位置

阶段 6 的可观测性小段落是：

```text
第 26 节：LangSmith tracing 基础
第 27 节：OpenTelemetry 基础
第 28 节：trace / span / log / metrics 的关系
第 29 节：生产日志字段设计
第 30 节：成本、token 和延迟指标
```

第 28 节我们讲：

```text
metrics 看整体趋势和聚合表现。
```

第 29 节我们讲：

```text
log 看单次事件细节。
```

第 30 节就是把 metrics 里的 LLM 关键指标讲细：

```text
LLM 调用了多少次？
失败了多少次？
每次调用多慢？
每次用了多少输入 token？
每次生成了多少输出 token？
估算花了多少钱？
这些指标应该按哪些维度拆分？
哪些维度绝对不能放进去？
```

你可以这样理解：

```text
第 29 节：某一次请求怎么排查
第 30 节：整体调用趋势怎么监控
```

如果没有第 30 节，你只能回答：

```text
某一次模型调用用了多少 token。
```

但你不能回答：

```text
最近一小时模型调用量涨了吗？
哪个模型最慢？
哪个 prompt 最耗 token？
哪个 Agent 节点最贵？
错误率有没有升高？
P95 延迟有没有超过阈值？
今天成本是否异常增长？
```

这就是 metrics 的价值。

---

## 二、官方资料依据

本节参考了这些官方资料：

- OpenTelemetry Metrics: https://opentelemetry.io/docs/concepts/signals/metrics/
- OpenTelemetry Metrics API: https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/metrics/api.md
- OpenTelemetry Metrics Data Model: https://opentelemetry.io/docs/specs/otel/metrics/data-model/
- OpenTelemetry GenAI Observability: https://opentelemetry.io/blog/2026/genai-observability/
- OpenTelemetry GenAI attributes registry: https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
- OpenAI Help：prompt tokens 和 completion tokens 区别：https://help.openai.com/en/articles/7127987-what-is-the-difference-between-prompt-tokens-and-completion-tokens
- OpenAI Help：API usage 里包含 token usage：https://help.openai.com/en/articles/6614209-how-do-i-check-my-token-usage

这些资料对本节有几个关键确认：

```text
1. Counter 表示只增不减的累计值。
2. Histogram 适合记录延迟、请求大小、token 数量这类分布。
3. Metrics 用来提供聚合统计，而不是还原某一次请求的完整细节。
4. Metric cardinality 是 attribute 组合数量，高基数字段会增加内存和成本。
5. OTel GenAI 常见核心指标包括 gen_ai.client.operation.duration 和 gen_ai.client.token.usage。
6. gen_ai.client.operation.duration 用 histogram 表示 LLM 调用耗时。
7. gen_ai.client.token.usage 用 histogram 表示 token 消耗，并用 gen_ai.token.type 区分 input/output。
8. prompt tokens 是输入给模型的 token。
9. completion tokens 是模型生成的 token。
10. API 响应通常会在 usage 字段中返回 prompt_tokens、completion_tokens、total_tokens。
```

本节代码借鉴了这些概念，但不会直接接入 OTel SDK。

我们先把“应该记录哪些指标、用什么 instrument、带哪些 attributes、如何避免高基数”做成可测试模型。

---

## 三、基础知识铺垫

这一部分要认真看。

如果不理解 token、成本、延迟和 metrics 的关系，后面你写出来的监控很容易只是“有数据”，但不知道数据有什么用。

### 1. 什么是 token

token 可以先理解成：

```text
模型处理文本时使用的基本计费和计算单位。
```

它不完全等于一个字。

也不完全等于一个词。

英文里，一个 token 可能是：

```text
一个单词
一个单词的一部分
一个标点
一段空格
```

中文里，一个 token 的切分方式取决于具体 tokenizer。

你作为工程开发者，先记住：

```text
模型不是按“字数”工作，而是按 token 工作。
```

为什么要关注 token？

因为 token 同时影响：

```text
1. 上下文能不能塞得下
2. 模型调用成本
3. 模型调用延迟
4. 请求是否会超出模型限制
5. prompt 是否需要优化
6. RAG 检索内容是否过多
7. Agent 是否陷入重复调用
```

### 2. prompt_tokens 是什么

`prompt_tokens` 是输入 token。

OpenAI 帮助文档里把它解释为：

```text
输入给模型的 prompt 里的 token 数量。
```

在聊天模型里，prompt 不只是用户那句话。

它通常包括：

```text
system message
developer message
user message
历史对话
工具定义
RAG 检索上下文
JSON schema
输出格式要求
安全规则
```

所以用户只问一句：

```text
帮我查订单
```

真正发给模型的内容可能很长。

特别是在我们的项目里，真实 LLM 节点可能会包含：

```text
工单字段 JSON Schema
Agent 当前上下文
用户消息
输出约束
错误处理规则
```

这些都会算进 prompt_tokens。

### 3. completion_tokens 是什么

`completion_tokens` 是输出 token。

也就是模型生成的 token。

例如模型回答：

```text
请提供订单号，我才能继续为你查询。
```

这段内容会消耗 completion_tokens。

在工具调用场景里，模型输出的 tool call JSON、结构化字段、最终答案，也都可能算作输出 token。

### 4. total_tokens 是什么

`total_tokens` 通常表示：

```text
prompt_tokens + completion_tokens
```

但工程上不要只盯着 total_tokens。

因为输入和输出的价格、优化方向、问题原因经常不同。

比如：

```text
prompt_tokens 很高：
可能是系统提示词太长、RAG 塞太多、历史对话没裁剪、工具定义过多。

completion_tokens 很高：
可能是模型回答太啰嗦、输出格式太长、max_tokens 太宽松、没有要求简洁。
```

如果你只看 total_tokens，就很难判断问题出在输入还是输出。

### 5. token 为什么影响成本

大模型 API 通常按 token 计费。

常见方式是：

```text
输入 token 一个单价
输出 token 一个单价
```

一般写成：

```text
每 100 万 input tokens 多少钱
每 100 万 output tokens 多少钱
```

所以估算成本的公式是：

```text
input_cost = prompt_tokens / 1,000,000 * input_price_per_million
output_cost = completion_tokens / 1,000,000 * output_price_per_million
total_cost = input_cost + output_cost
```

本节代码里用的就是这个公式。

但是注意：

```text
不要把真实模型价格写死在代码里。
```

为什么？

```text
1. 不同 provider 价格不同
2. 同一 provider 不同模型价格不同
3. 同一模型输入/输出价格不同
4. 价格可能随时间变化
5. 企业账号可能有折扣或包量
6. 一些平台有缓存 token、推理 token、批处理 token 等特殊计费
```

所以本节设计 `LLMTokenPricing`，让价格从外部配置传进来。

### 6. token 为什么影响延迟

LLM 延迟通常受这些因素影响：

```text
1. 输入 token 越多，模型需要读的上下文越多。
2. 输出 token 越多，模型生成时间越长。
3. 模型越大，推理通常越慢。
4. 网络和 provider 排队也会影响延迟。
5. 工具调用、RAG、重试也会叠加耗时。
```

你可以先粗略理解：

```text
prompt_tokens 影响模型开始生成前要处理多少内容。
completion_tokens 影响模型需要生成多少内容。
```

所以一个 LLM 应用要同时监控：

```text
duration
input tokens
output tokens
```

如果你只看 duration，不看 token，就不知道慢是不是因为输入太长。

如果你只看 token，不看 duration，就不知道长 prompt 是否真的造成了用户体验问题。

### 7. 日志里的 elapsed_ms 和 metrics 里的 duration 有什么区别

第 29 节日志里有：

```text
elapsed_ms
```

它表示某一次事件的耗时。

比如：

```text
这一次模型调用耗时 1234.57ms。
```

第 30 节 metrics 里有：

```text
gen_ai.client.operation.duration
```

它表示很多次模型调用的耗时分布。

比如你可以看：

```text
P50 延迟
P95 延迟
P99 延迟
最大值
最近 10 分钟是否变慢
不同模型的延迟对比
不同 prompt 的延迟对比
```

所以：

```text
日志 elapsed_ms：回答某一次调用多慢
metrics duration：回答整体调用是否变慢
```

两者都重要，但用途不同。

### 8. 什么是 counter

Counter 是只增不减的累计指标。

你可以把它理解成汽车里程表。

它适合记录：

```text
总请求数
总错误数
总 token 消耗
总成本
总重试次数
总降级次数
```

Counter 不适合记录：

```text
一次请求耗时多少
当前并发数是多少
队列当前长度是多少
```

本节用 counter 记录：

```text
app.llm.client.requests
app.llm.client.errors
app.llm.client.estimated_cost
```

### 9. 什么是 histogram

Histogram 是分布指标。

它适合记录：

```text
延迟
请求大小
响应大小
token 数量
每次调用成本
RAG chunk 数量
Agent 节点数
```

为什么延迟用 histogram？

因为我们不只关心平均值。

平均值可能骗人。

例如 10 次调用：

```text
9 次 100ms
1 次 10s
```

平均值可能看起来还可以，但用户遇到那一次 10s 会觉得系统很慢。

Histogram 可以帮助你看：

```text
P50
P90
P95
P99
```

这些分位数比平均值更适合做延迟监控。

本节用 histogram 记录：

```text
gen_ai.client.operation.duration
gen_ai.client.token.usage
```

### 10. 什么是 gauge

Gauge 表示一个可以上下波动的当前值。

比如：

```text
当前队列长度
当前内存使用
当前在线用户数
当前 in-flight 请求数
```

本节没有实现 gauge。

为什么？

因为本节关注的是：

```text
一次 LLM 调用完成后产生的指标。
```

一次调用完成后，我们更适合记录：

```text
请求数 counter
错误数 counter
耗时 histogram
token histogram
成本 counter
```

如果以后我们监控：

```text
当前正在执行的 LLM 调用数
```

那可以用 up_down_counter 或 gauge。

### 11. 为什么 token usage 用 histogram

这点很容易疑惑。

很多人第一反应是：

```text
token 是累计消耗，应该用 counter。
```

这不是完全错。

如果你想看总 token 消耗，counter 很自然。

但 OTel GenAI 里常见的 `gen_ai.client.token.usage` 是 histogram。

它记录的是：

```text
每一次 LLM 调用用了多少 token。
```

然后你可以看分布：

```text
大多数调用用了多少 input tokens？
P95 的 input tokens 是多少？
哪些 prompt 让 output tokens 变长？
是否有极端超长请求？
```

所以本节采用：

```text
gen_ai.client.token.usage -> histogram
```

并用：

```text
gen_ai.token.type=input
gen_ai.token.type=output
```

区分输入和输出。

### 12. 为什么 token type 只用 input/output

本节先只讲：

```text
input
output
```

也就是：

```text
prompt_tokens -> input
completion_tokens -> output
```

以后你可能还会遇到：

```text
cached input tokens
reasoning output tokens
audio tokens
image tokens
```

这些属于更细的模型计费和语义约定。

当前项目还没到那一步。

本节先把最基础、最通用的输入/输出 token 监控学扎实。

### 13. 什么是 metrics attributes

metrics attributes 是指标标签。

比如：

```text
gen_ai.provider.name=dashscope
gen_ai.request.model=qwen3.7-plus
gen_ai.operation.name=chat
app.llm.task=ticket_intent_classification
prompt.name=ticket_intent_classification
prompt.version=v1
status=ok
```

这些 attributes 的作用是：

```text
让你能按维度拆分指标。
```

例如：

```text
按模型看延迟
按 provider 看错误率
按 prompt 版本看 token 消耗
按 LLM 任务看成本
按 status 看成功/失败调用量
```

### 14. 什么是 cardinality

第 28 节已经讲过 cardinality。

这里再结合 LLM 指标讲一次。

cardinality 是：

```text
某个 metric 的 attribute 组合数量。
```

比如你有一个指标：

```text
gen_ai.client.operation.duration
```

如果 attributes 是：

```text
provider=dashscope
model=qwen3.7-plus
operation=chat
status=ok
```

组合数量很少。

如果你又加了：

```text
trace_id
thread_id
user_message
```

那几乎每次请求都是一个新组合。

这会导致：

```text
1. 指标内存增长
2. 存储成本增长
3. 查询变慢
4. 聚合价值下降
5. 告警规则变得不稳定
```

所以 metrics attributes 必须低基数。

### 15. 哪些 attributes 可以放

当前项目里，比较适合放进 LLM metrics attributes 的字段：

```text
gen_ai.provider.name
gen_ai.request.model
gen_ai.operation.name
app.llm.task
prompt.name
prompt.version
status
error.type
business_domain
```

这些字段有共同特点：

```text
1. 值比较稳定
2. 值的数量有限
3. 适合聚合
4. 不包含敏感 payload
```

例如：

```text
prompt.version=v1
```

它非常适合做对比：

```text
v1 和 v2 哪个 token 更少？
v2 是否让延迟变高？
v2 是否让错误率下降？
```

### 16. 哪些 attributes 不能放

当前项目里，不应该放进 LLM metrics attributes 的字段：

```text
trace_id
span_id
thread_id
session_id
actor_id
user_id
conversation_id
user_message
normalized_message
prompt
messages
final_answer
raw_response
raw_completion
```

原因分两类：

第一类是高基数字段：

```text
trace_id
span_id
thread_id
user_id
conversation_id
```

第二类是敏感或大 payload：

```text
user_message
prompt
messages
final_answer
raw_response
raw_completion
```

这些字段可能适合在受控 trace 或调试环境里看，但不适合进入 metrics attributes。

### 17. provider 和 model 会不会也是高基数

这是一个好问题。

理论上，如果你的系统允许用户随便传 model 名，`model` 也会变成高基数字段。

但在正常生产系统里，model 通常来自后端配置或白名单。

例如：

```text
qwen3.7-plus
gpt-4.1-mini
gpt-4o
embedding-v3
```

数量有限。

所以在当前项目里：

```text
gen_ai.request.model
```

可以作为 metric attribute。

但你要记住：

```text
只有当 model 来自受控配置时，它才适合放进 metrics attributes。
```

### 18. prompt_name 和 prompt_version 为什么适合放

因为 prompt 优化是 LLM 应用的核心工作。

你会经常对比：

```text
同一个任务，不同 prompt 版本的 token 消耗
同一个任务，不同 prompt 版本的延迟
同一个任务，不同 prompt 版本的错误率
```

例如：

```text
prompt.name=ticket_intent_classification
prompt.version=v1
```

和：

```text
prompt.name=ticket_intent_classification
prompt.version=v2
```

这样你就能回答：

```text
新 prompt 是否更省 token？
新 prompt 是否更慢？
新 prompt 是否更容易输出错误 JSON？
```

### 19. 成本指标和账单有什么区别

本节的成本指标叫：

```text
app.llm.client.estimated_cost
```

注意里面有：

```text
estimated
```

它表示估算成本，不等于最终账单。

为什么？

因为最终账单可能受：

```text
1. provider 官方价格
2. 企业折扣
3. 缓存 token
4. reasoning token
5. 批处理价格
6. 免费额度
7. 汇率
8. 税费
9. 账号级别计费规则
```

影响。

所以工程监控里的成本指标主要用于：

```text
趋势观察
异常发现
成本归因
容量预估
```

不要把它当最终财务账单。

---

## 四、本节主题系统讲解

下面把本节主题系统讲透。

### 1. 当前项目已经有什么基础

当前项目已经有：

```text
app/core/token_usage.py
app/services/llm_service.py
app/agents/ticket_agent.py
```

其中：

```text
app/core/token_usage.py
```

负责粗略估算文本 token，用于预算思维。

比如：

```text
估算输入大概多少 token
设置 max_output_tokens
计算 total_reserved_tokens
```

而：

```text
app/services/llm_service.py
```

里有：

```text
LLMTokenUsage
extract_token_usage()
```

它从模型返回里提取：

```text
prompt_tokens
completion_tokens
total_tokens
```

再看：

```text
app/agents/ticket_agent.py
```

真实 LLM 节点已经会在成功日志里输出：

```text
elapsed_ms
prompt_tokens
completion_tokens
total_tokens
```

所以第 30 节不是从零开始。

第 30 节是在这些基础上继续问：

```text
这些 token 和耗时，如何变成 metrics？
```

### 2. 本节新增什么

本节新增：

```text
app/agents/llm_metrics.py
tests/test_ticket_agent_llm_metrics.py
```

它们负责把一次 LLM 调用转成 metrics measurement。

也就是：

```text
输入：
provider、model、operation、prompt_name、prompt_version、elapsed_ms、usage、pricing

输出：
一组 metric measurement
```

例如一次成功调用：

```text
provider=dashscope
model=qwen3.7-plus
operation=chat
prompt_tokens=1000
completion_tokens=500
elapsed_ms=1234.567
```

会生成：

```text
app.llm.client.requests                         counter
gen_ai.client.operation.duration                histogram
gen_ai.client.token.usage{token.type=input}     histogram
gen_ai.client.token.usage{token.type=output}    histogram
app.llm.client.estimated_cost                   counter
```

### 3. 为什么没有直接接入 OpenTelemetry Meter

本节没有直接写：

```python
meter.create_histogram(...)
meter.create_counter(...)
```

原因是学习顺序。

现在你最需要先掌握：

```text
应该有哪些指标
每个指标用什么 instrument
每个指标是什么单位
每个指标带哪些 attributes
哪些 attributes 要过滤
成本如何估算
token 如何区分 input/output
```

如果现在直接接入 SDK，你会同时面对：

```text
MeterProvider
Exporter
Reader
Collector
OTLP
环境变量
后台线程
测试替换
```

学习焦点会被分散。

所以本节先用 dataclass 表达指标。

后面如果接入真实 OTel Meter，这些 measurement 可以很自然地映射成：

```text
counter.add(value, attributes)
histogram.record(value, attributes)
```

### 4. 本节指标清单

本节定义了 5 个指标：

| 指标名 | 类型 | 单位 | 作用 |
| --- | --- | --- | --- |
| `app.llm.client.requests` | counter | `{request}` | LLM 请求次数 |
| `app.llm.client.errors` | counter | `{error}` | LLM 失败次数 |
| `gen_ai.client.operation.duration` | histogram | `s` | LLM 调用耗时分布 |
| `gen_ai.client.token.usage` | histogram | `{token}` | 每次调用 input/output token 分布 |
| `app.llm.client.estimated_cost` | counter | `USD` | 基于配置单价估算的调用成本 |

其中两个是 GenAI 常见指标：

```text
gen_ai.client.operation.duration
gen_ai.client.token.usage
```

三个是项目自己的辅助指标：

```text
app.llm.client.requests
app.llm.client.errors
app.llm.client.estimated_cost
```

### 5. 为什么 request/error 用 app 前缀

因为这些不是本节引用的核心 GenAI 标准指标。

它们是当前项目为了学习和监控方便加的项目指标。

所以用：

```text
app.llm.client.requests
app.llm.client.errors
app.llm.client.estimated_cost
```

这样命名可以让你一眼知道：

```text
这是我们应用自己定义的指标。
```

而：

```text
gen_ai.client.operation.duration
gen_ai.client.token.usage
```

是跟 GenAI 可观测性语义更接近的指标。

### 6. 为什么 duration 单位用秒，不用毫秒

当前项目里日志习惯用：

```text
elapsed_ms
```

但 OTel GenAI duration 常见单位是：

```text
s
```

所以本节在代码里做了转换：

```text
elapsed_ms / 1000
```

例如：

```text
1234.567ms -> 1.234567s
```

这样做是为了和 OTel GenAI 指标习惯对齐。

你要记住：

```text
日志里用 ms 很直观。
metrics 里跟标准对齐时，duration 常用 s。
```

关键不是 ms 或 s 谁更好。

关键是：

```text
同一个指标的单位必须稳定。
```

### 7. 为什么 token usage 生成两条 measurement

一次 LLM 调用里可能有：

```text
prompt_tokens=1000
completion_tokens=500
```

本节不会生成一个：

```text
total_tokens=1500
```

作为主要 GenAI metric。

而是生成两条：

```text
gen_ai.client.token.usage{gen_ai.token.type=input}  = 1000
gen_ai.client.token.usage{gen_ai.token.type=output} = 500
```

为什么？

因为输入和输出要分开分析。

例如：

```text
input tokens 高：可能是 prompt/RAG/历史上下文太长
output tokens 高：可能是回答太长或 max_tokens 太宽
```

如果你只看 total，就很难判断优化方向。

### 8. total_tokens 还有没有用

有用。

它可以用于：

```text
1. 快速看一次调用总 token
2. 校验 prompt_tokens + completion_tokens 是否等于 total_tokens
3. 做日志展示
4. 做成本估算的辅助检查
```

但在本节 metrics 设计里，主要监控 input/output。

如果想看 total，可以在查询时把 input 和 output 相加。

### 9. 为什么 usage 不完整时不估算成本

如果只有：

```text
total_tokens=1500
```

但没有：

```text
prompt_tokens
completion_tokens
```

那就不知道输入和输出各是多少。

因为输入单价和输出单价可能不同。

这时如果强行估算成本，只能瞎猜。

所以本节代码选择：

```text
usage 不完整 -> 不估算成本
```

这是一种工程上的保守做法。

宁可少报估算成本，也不要给出看似精确但其实不可靠的数字。

### 10. 为什么没有 token usage 时不记录 0

如果 provider 没返回 token usage，你不能记录：

```text
0 tokens
```

因为：

```text
没有返回 usage
```

和：

```text
返回了 usage=0
```

不是一回事。

前者是缺数据。

后者是确实为 0。

本节代码的做法是：

```text
没有 split usage -> 不产生 token usage metric
```

这样不会误导监控。

### 11. 成本估算为什么用 per million tokens

很多模型价格表会写：

```text
每 100 万 tokens 多少钱
```

所以本节代码用：

```text
MILLION_TOKENS = 1_000_000
```

并用：

```text
prompt_tokens * input_price_per_million / 1_000_000
completion_tokens * output_price_per_million / 1_000_000
```

这样更贴近真实模型价格表达方式。

### 12. 为什么成本 metric 是 estimated_cost

本节没有叫：

```text
app.llm.client.cost
```

而是叫：

```text
app.llm.client.estimated_cost
```

这是故意的。

因为它不是最终账单。

它只是根据当前配置单价和 usage 估算出来的工程指标。

如果以后你接入真实 provider 的账单 API，那个数据才更接近财务成本。

工程指标负责：

```text
发现异常
控制趋势
定位来源
辅助优化
```

财务账单负责：

```text
最终结算
```

### 13. 为什么 error.type 用 error_code

OTel 里常见错误属性叫：

```text
error.type
```

当前项目里我们已经有稳定错误码：

```text
LLM_TIMEOUT
LLM_RATE_LIMITED
LLM_API_KEY_MISSING
MODEL_OUTPUT_INVALID
```

所以本节把：

```text
error_code
```

映射成：

```text
error.type
```

这样方便按错误类型统计：

```text
LLM_TIMEOUT 最近 10 分钟是否升高？
LLM_RATE_LIMITED 是否超过阈值？
LLM_API_KEY_MISSING 是否突然出现？
```

### 14. 为什么 status 放进 metrics attributes

本节 attributes 里有：

```text
status=ok
status=error
```

这样可以查询：

```text
总请求数
成功请求数
失败请求数
错误率
```

例如错误率可以理解成：

```text
app.llm.client.errors / app.llm.client.requests
```

或者按 `status` 拆分请求数。

### 15. 本节和第 29 节的边界

第 29 节日志字段里可以有：

```text
trace_id
span_id
thread_id
elapsed_ms
error_code
```

第 30 节 metrics attributes 里不应该有：

```text
trace_id
span_id
thread_id
```

为什么？

因为日志用于定位单次请求。

metrics 用于聚合趋势。

这句话非常重要：

```text
日志为了查得准，可以带请求级 ID。
metrics 为了聚合稳，不能带请求级 ID。
```

---

## 五、本节代码讲解

本节新增：

```text
projects/ai-service/app/agents/llm_metrics.py
projects/ai-service/tests/test_ticket_agent_llm_metrics.py
```

下面只讲对学习有帮助的代码。

### 1. LLMMetricSpec

`LLMMetricSpec` 表示指标规格。

它说明：

```text
指标叫什么
用什么 instrument
单位是什么
描述是什么
必须有哪些 attributes
```

代码：

```python
@dataclass(frozen=True)
class LLMMetricSpec:
    name: str
    kind: LLMMetricInstrumentKind
    unit: str
    description: str
    required_attributes: tuple[str, ...] = ()
```

它的学习价值在于：

```text
指标设计不是只写一个名字。
```

一个指标至少要说明：

```text
name
kind
unit
attributes
```

否则后面接 dashboard 和 alert 时会乱。

### 2. LLMMetricMeasurement

`LLMMetricMeasurement` 表示一次指标观测值。

代码：

```python
@dataclass(frozen=True)
class LLMMetricMeasurement:
    name: str
    kind: LLMMetricInstrumentKind
    value: int | float
    unit: str
    attributes: dict[str, str | int | float | bool]
    description: str
```

它对应真实 OTel SDK 里的两类操作：

```text
counter.add(value, attributes)
histogram.record(value, attributes)
```

本节先不直接调用 SDK，而是先把 measurement 构造出来。

这方便测试。

### 3. LLMTokenUsageSnapshot

这个类表示一次模型调用的 token usage。

代码：

```python
@dataclass(frozen=True)
class LLMTokenUsageSnapshot:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
```

它还有几个属性：

```text
has_split_usage
computed_total_tokens
total_matches_split
```

这些属性帮助你判断：

```text
有没有输入/输出拆分？
能不能准确估算成本？
total_tokens 是否和 input+output 对得上？
```

### 4. normalize_llm_token_usage()

这个函数可以接收：

```text
dict
对象
None
```

然后统一转成：

```text
LLMTokenUsageSnapshot
```

为什么要这么做？

因为不同 SDK 返回 usage 的形状可能不一样。

有的是：

```python
usage.prompt_tokens
```

有的是：

```python
usage["prompt_tokens"]
```

本节函数把这些差异屏蔽掉。

它还会忽略非法值：

```text
负数
bool
字符串
```

因为 token 数必须是非负整数。

### 5. LLMTokenPricing

这个类表示 token 单价配置。

代码：

```python
@dataclass(frozen=True)
class LLMTokenPricing:
    input_cost_per_million_tokens: float
    output_cost_per_million_tokens: float
    currency: str = "USD"
```

注意它不是固定价格表。

它只是一个配置结构。

你可以给不同 provider/model 配不同价格。

本节测试里用的数字只是示例。

### 6. estimate_llm_call_cost()

这个函数做成本估算。

逻辑是：

```text
没有 pricing -> missing_pricing
没有 prompt/completion 拆分 -> incomplete_usage
有 pricing 且 usage 完整 -> estimated
```

估算公式：

```text
input_cost = prompt_tokens * input_price_per_million / 1_000_000
output_cost = completion_tokens * output_price_per_million / 1_000_000
total_cost = input_cost + output_cost
```

例如：

```text
prompt_tokens=1000
completion_tokens=500
input_price=2.0 / 1M
output_price=6.0 / 1M
```

则：

```text
input_cost = 1000 * 2 / 1_000_000 = 0.002
output_cost = 500 * 6 / 1_000_000 = 0.003
total_cost = 0.005
```

### 7. build_llm_metric_attributes()

这个函数负责构造低基数 attributes。

核心字段：

```text
gen_ai.provider.name
gen_ai.request.model
gen_ai.operation.name
status
app.llm.task
prompt.name
prompt.version
error.type
```

它还会过滤：

```text
trace_id
span_id
thread_id
user_message
prompt
messages
final_answer
raw_response
raw_completion
```

这就是第 28 节和第 29 节的原则在 metrics 里的落地。

### 8. build_llm_call_metrics()

这是本节最核心函数。

它把一次 LLM 调用转成多条 metrics。

成功调用可能生成：

```text
app.llm.client.requests
gen_ai.client.operation.duration
gen_ai.client.token.usage input
gen_ai.client.token.usage output
app.llm.client.estimated_cost
```

失败调用可能生成：

```text
app.llm.client.requests
app.llm.client.errors
gen_ai.client.operation.duration
```

为什么失败时可能没有 token metrics？

因为模型调用失败时，provider 可能根本没有返回 usage。

这时不能假装 token 是 0。

### 9. 为什么 token usage metric 的 value 是单次 token 数

例如：

```text
gen_ai.client.token.usage{gen_ai.token.type=input}=1000
gen_ai.client.token.usage{gen_ai.token.type=output}=500
```

这里的 value 是一次调用的 token 数。

因为 instrument 是 histogram。

它记录的是分布。

如果未来你想看总 token，也可以在后台按时间窗口聚合这些观测值。

### 10. 本节没有记录 prompt 内容

代码里故意过滤：

```text
prompt
messages
user_message
final_answer
raw_response
raw_completion
```

原因：

```text
metrics attributes 不能放大文本，不能放敏感内容，也不能放高基数字段。
```

如果你需要调试 prompt 内容，应在受控 trace 或本地调试环境里看，并且要考虑脱敏和权限。

不要把它放进 metrics。

---

## 六、本节测试重点

本节新增测试：

```text
tests/test_ticket_agent_llm_metrics.py
```

共 12 条。

### 测试 1：normalize 支持 dict 和对象

验证不同 SDK 返回形状都能归一化。

### 测试 2：非法 token 值会被忽略

验证：

```text
负数
bool
字符串
```

不会被当作 token 数。

### 测试 3：成本估算公式正确

验证：

```text
1000 input tokens * 2.0 / 1M = 0.002
500 output tokens * 6.0 / 1M = 0.003
总成本 = 0.005
```

### 测试 4：缺 pricing 或 usage 不完整时不强行估算

验证：

```text
missing_pricing
incomplete_usage
```

### 测试 5：价格不能为负数或无限大

验证成本配置要安全。

### 测试 6：成功调用生成请求、延迟、token、成本指标

验证：

```text
requests counter
duration histogram
token usage input histogram
token usage output histogram
estimated cost counter
```

### 测试 7：错误调用有 error.type

验证：

```text
status=error
error.type=LLM_TIMEOUT
errors counter
duration histogram
```

### 测试 8：高基数和敏感 attributes 被过滤

验证这些字段不会进入 metrics attributes：

```text
trace_id
span_id
thread_id
user_message
prompt
```

### 测试 9：没有 pricing 不产生成本 metric

避免给出不可靠成本。

### 测试 10：只有 total_tokens 不产生 token/cost metrics

因为无法区分 input/output。

### 测试 11：非法 duration 不记录

负数耗时不是有效观测值。

### 测试 12：指标规格表记录 instrument 和必需 attributes

保护指标契约不被后续改乱。

---

## 七、常见排查场景

### 场景 1：成本突然升高

先看：

```text
app.llm.client.estimated_cost
```

按这些维度拆：

```text
gen_ai.provider.name
gen_ai.request.model
app.llm.task
prompt.name
prompt.version
```

再看：

```text
gen_ai.client.token.usage
```

区分：

```text
input token 升高
output token 升高
```

如果 input 升高：

```text
检查 prompt、RAG 上下文、历史对话裁剪、工具定义。
```

如果 output 升高：

```text
检查回答是否过长、max_tokens 是否太大、是否缺少简洁输出约束。
```

### 场景 2：延迟突然升高

先看：

```text
gen_ai.client.operation.duration
```

看 P95/P99。

再按：

```text
model
provider
app.llm.task
prompt.version
```

拆分。

如果某个模型明显慢：

```text
可能是模型本身慢、provider 排队、上下文太长。
```

再对比：

```text
gen_ai.client.token.usage
```

判断是不是 token 变多导致慢。

### 场景 3：错误率升高

先看：

```text
app.llm.client.errors / app.llm.client.requests
```

再按：

```text
error.type
model
provider
task
```

拆分。

如果：

```text
error.type=LLM_RATE_LIMITED
```

说明可能是限流或并发过高。

如果：

```text
error.type=LLM_TIMEOUT
```

说明可能是 provider 响应慢、网络慢、上下文过长或超时配置太短。

### 场景 4：某个 prompt 版本上线后变贵

按：

```text
prompt.name
prompt.version
```

对比：

```text
gen_ai.client.token.usage
app.llm.client.estimated_cost
gen_ai.client.operation.duration
```

如果 v2 input tokens 明显更高：

```text
说明 prompt 可能写长了，或者塞了更多 schema/context。
```

如果 v2 output tokens 明显更高：

```text
说明模型输出可能更啰嗦。
```

如果 v2 错误率降低但成本略升：

```text
这是一个工程权衡：更贵但更稳，是否接受要看业务目标。
```

---

## 八、把本节讲给别人听

你可以这样讲：

```text
LLM 应用必须监控 token、成本和延迟，因为 token 决定上下文大小、调用成本和一部分延迟。

prompt_tokens 是输入 token，completion_tokens 是输出 token，total_tokens 通常是两者之和。
输入和输出要分开看，因为它们价格可能不同，优化方向也不同。

LLM 调用次数和错误次数适合用 counter；调用延迟适合用 histogram；token usage 在 GenAI metrics 里常用 histogram，并用 gen_ai.token.type 区分 input 和 output。

成本指标应该叫 estimated_cost，因为它只是根据 token usage 和配置单价估算，不等于最终账单。
模型价格会变化，所以不应该写死在代码里。

metrics attributes 必须低基数，可以放 provider、model、operation、prompt_name、prompt_version、status、error.type；不能放 trace_id、thread_id、user_message、prompt、messages、final_answer 这类高基数或敏感字段。
```

如果你能完整讲出这段，说明你真正理解了本节。

---

## 九、本节练习

### 练习 1：解释三种 token

请解释：

```text
prompt_tokens
completion_tokens
total_tokens
```

参考答案：

```text
prompt_tokens：输入给模型的 token，包括 system prompt、用户消息、历史对话、工具定义、RAG 上下文、JSON schema 等。

completion_tokens：模型生成的 token，包括最终回答、结构化 JSON、工具调用内容等。

total_tokens：通常是 prompt_tokens + completion_tokens，用于快速表示一次调用总 token 消耗。
```

### 练习 2：计算成本

已知：

```text
prompt_tokens = 2000
completion_tokens = 1000
input_price_per_million = 1.5
output_price_per_million = 4.5
```

请计算估算成本。

参考答案：

```text
input_cost = 2000 * 1.5 / 1,000,000 = 0.003
output_cost = 1000 * 4.5 / 1,000,000 = 0.0045
total_cost = 0.003 + 0.0045 = 0.0075
```

### 练习 3：判断指标类型

请判断下面指标应该用 counter、histogram 还是 gauge：

```text
LLM 总请求数
LLM 总错误数
LLM 调用耗时
每次调用 input tokens
当前正在执行的 LLM 调用数
估算总成本
```

参考答案：

```text
LLM 总请求数：counter
LLM 总错误数：counter
LLM 调用耗时：histogram
每次调用 input tokens：histogram
当前正在执行的 LLM 调用数：gauge 或 up_down_counter
估算总成本：counter
```

### 练习 4：判断 metrics attributes 是否合适

下面哪些适合放进 metrics attributes？

```text
gen_ai.provider.name
gen_ai.request.model
prompt.version
trace_id
thread_id
user_message
error.type
prompt
status
```

参考答案：

```text
适合：
gen_ai.provider.name
gen_ai.request.model
prompt.version
error.type
status

不适合：
trace_id：高基数，请求级 ID。
thread_id：高基数，业务会话级 ID。
user_message：敏感 payload，高基数。
prompt：大文本，可能敏感，高基数。
```

### 练习 5：为什么只有 total_tokens 时不应该准确估算成本

参考答案：

```text
因为输入 token 和输出 token 的价格可能不同。
如果只有 total_tokens，不知道其中多少是 prompt_tokens，多少是 completion_tokens，就无法准确套用输入单价和输出单价。
强行估算会产生看似精确但不可靠的结果。
```

### 练习 6：为什么 duration 用 histogram

参考答案：

```text
因为延迟不是只看总和或平均值，而是要看分布。
Histogram 可以支持 P50、P95、P99 等分位数分析，帮助发现少数慢请求和整体延迟退化。
```

### 练习 7：如何排查 prompt 新版本变贵

参考答案：

```text
先按 prompt.name 和 prompt.version 拆分 app.llm.client.estimated_cost。
再看 gen_ai.client.token.usage，区分 input 和 output。
如果 input tokens 升高，检查 prompt、RAG 上下文、历史消息、schema 是否变长。
如果 output tokens 升高，检查输出约束和 max_tokens。
还要对比错误率和效果，判断成本升高是否换来了更稳定的输出。
```

---

## 十、自测题

### 自测 1：token 为什么是 LLM 应用必须监控的指标？

答案：

```text
因为 token 同时影响上下文限制、调用成本、调用延迟和 prompt 优化方向。
如果不监控 token，就很难发现 prompt 变长、RAG 塞太多、输出过长或 Agent 循环调用等问题。
```

### 自测 2：prompt_tokens 高通常说明什么？

答案：

```text
通常说明输入给模型的内容很多，可能是系统提示词长、RAG 上下文多、历史对话没裁剪、工具定义太多、JSON Schema 太复杂。
```

### 自测 3：completion_tokens 高通常说明什么？

答案：

```text
通常说明模型输出很多，可能是回答过长、结构化输出太复杂、max_tokens 设置太宽、缺少简洁输出约束。
```

### 自测 4：为什么成本指标叫 estimated_cost？

答案：

```text
因为它只是根据 token usage 和配置单价估算出来的工程指标，不等于最终账单。
最终账单还可能受折扣、缓存 token、reasoning token、批处理、免费额度、汇率、税费等因素影响。
```

### 自测 5：为什么模型价格不能写死在代码里？

答案：

```text
因为模型价格会随 provider、模型、账号、折扣、时间和计费规则变化。
写死价格会让成本估算过期，应该通过配置或价格表服务传入。
```

### 自测 6：LLM 调用耗时为什么用秒作为 metrics 单位？

答案：

```text
为了和 OTel GenAI duration 指标常见单位对齐，gen_ai.client.operation.duration 使用 s。
当前项目日志里可以继续用 elapsed_ms，但转成 metrics 时要统一单位。
```

### 自测 7：metrics attributes 为什么不能放 trace_id？

答案：

```text
trace_id 每次请求几乎都不同，是高基数字段。
放进 metrics attributes 会导致 attribute 组合数量暴涨，增加内存、存储和查询成本，还会破坏聚合价值。
trace_id 应该放在日志和 trace 里，用于单次请求排查。
```

### 自测 8：gen_ai.token.type 的作用是什么？

答案：

```text
它用于区分 token usage 是输入 token 还是输出 token。
本节用 input 表示 prompt_tokens，用 output 表示 completion_tokens。
```

### 自测 9：没有 usage 时为什么不能记录 0 tokens？

答案：

```text
没有 usage 表示 provider 没返回 token 使用量；0 tokens 表示明确使用了 0 个 token。
这两者含义不同。
缺数据时不应该伪造成 0，否则会误导监控结果。
```

### 自测 10：本节最重要的一句话是什么？

答案：

```text
LLM metrics 要用低基数字段聚合 token、成本和延迟趋势，而不是记录某一次请求的完整上下文。
```

---

## 十一、本节命令

在 `projects/ai-service` 目录运行：

```powershell
uv run pytest tests/test_ticket_agent_llm_metrics.py
```

当前专项测试结果：

```text
12 passed
```

提交前还需要运行全量测试：

```powershell
uv run pytest
```

---

## 十二、本节小结

本节你真正要掌握的是：

```text
1. token 是模型处理文本的基本计费和计算单位。
2. prompt_tokens 是输入 token，completion_tokens 是输出 token，total_tokens 通常是两者之和。
3. 输入 token 和输出 token 要分开看，因为价格和优化方向不同。
4. LLM 成本估算公式是 tokens / 1,000,000 * 每百万 token 单价。
5. 成本指标应该是 estimated_cost，不等于最终账单。
6. 模型价格不能写死在代码里，应该从配置传入。
7. 请求数和错误数适合 counter。
8. 调用耗时和每次 token 使用量适合 histogram。
9. duration metrics 使用秒，日志 elapsed_ms 可以继续使用毫秒。
10. metrics attributes 必须低基数。
11. provider、model、operation、prompt_version、status、error.type 适合放 attributes。
12. trace_id、span_id、thread_id、user_message、prompt、final_answer 不适合放 metrics attributes。
```

本节新增：

```text
LLMMetricSpec
LLMMetricMeasurement
LLMTokenUsageSnapshot
LLMTokenPricing
LLMEstimatedCost
build_llm_metric_specs()
normalize_llm_token_usage()
estimate_llm_call_cost()
build_llm_metric_attributes()
build_llm_call_metrics()
```

下一节进入：

```text
阶段 6 第 31 节：timeout 超时策略
```

下一节会继续生产化主题，重点学习：

```text
为什么 LLM、RAG、Java 工具、数据库、HTTP 请求都必须有 timeout
连接超时和读取超时有什么区别
模型调用超时应该如何兜底
工具调用超时如何映射成稳定 error_code
timeout 和 retry、circuit breaker 的边界
```
