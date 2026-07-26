# 阶段 6 第 31 节：timeout 超时策略

本节目标：真正理解 timeout 是什么、为什么所有外部调用都必须有 timeout、不同类型 timeout 怎么区分、timeout 发生后应该如何 retry、fallback 和映射稳定错误码。

你要能回答这些问题：

```text
1. timeout 是什么？
2. 为什么不能让外部调用无限等待？
3. connect timeout 是什么？
4. read timeout 是什么？
5. write timeout 是什么？
6. pool timeout 是什么？
7. total timeout / operation timeout 是什么？
8. LLM 调用为什么必须有 timeout？
9. Java 工具调用为什么必须有 timeout？
10. RAG / Qdrant / Milvus / embedding 为什么也要 timeout？
11. 读操作 timeout 和写操作 timeout 为什么不能一样处理？
12. timeout 和 retry 是什么关系？
13. timeout 和 fallback 是什么关系？
14. timeout 发生后为什么要映射成稳定 error_code？
15. 当前智能工单 Agent 如何设计 timeout 策略？
```

这一节不真实调用模型，不打开虚拟机，不启动 Qdrant 或 Milvus。

这一节做的是更基础、更重要的事：

```text
把当前项目里已经零散存在的 timeout，整理成统一的工程策略。
```

---

## 一、本节在主线里的位置

阶段 6 的当前小段落是：

```text
第 28 节：trace / span / log / metrics 的关系
第 29 节：生产日志字段设计
第 30 节：成本、token 和延迟指标
第 31 节：timeout 超时策略
第 32 节：retry 重试策略
第 33 节：rate limit、circuit breaker 和降级
```

第 30 节我们学的是：

```text
如何发现系统慢、贵、异常增长。
```

第 31 节开始进入：

```text
如何保护系统不被慢依赖拖垮。
```

也就是说：

```text
第 30 节：观察问题
第 31 节：限制等待
第 32 节：谨慎重试
第 33 节：限流、熔断、降级
```

timeout 是稳定性保护的第一层。

如果没有 timeout，后面的 retry、fallback、circuit breaker 都很难做对。

因为一个调用如果永远不返回，你根本没有机会执行 retry 或 fallback。

---

## 二、官方资料依据

本节参考了这些官方资料：

- HTTPX Timeouts: https://www.python-httpx.org/advanced/timeouts/
- OpenAI Python API Reference: https://developers.openai.com/api/reference/python/
- Python asyncio timeout: https://docs.python.org/3/library/asyncio-task.html
- urllib3 User Guide Timeouts: https://urllib3.readthedocs.io/en/latest/user-guide.html

这些资料里有几个重要事实：

```text
1. HTTPX 默认会在网络不活跃超过 5 秒时抛 TimeoutException。
2. HTTPX 把 timeout 分成 connect、read、write、pool 四类。
3. OpenAI Python SDK 支持 timeout 参数，可以传 float 或 httpx.Timeout。
4. OpenAI Python SDK 默认 timeout 是 10 分钟，超时时会抛 APITimeoutError。
5. OpenAI Python SDK 默认会对一些错误自动 retry 2 次，包括连接错误、408、409、429 和 5xx。
6. asyncio.timeout() 可以限制等待时间，超时后会把内部取消转换成 TimeoutError。
7. urllib3 支持 float timeout，也支持拆分 connect/read timeout。
```

这些资料说明：

```text
timeout 不是某个库的小功能，而是网络调用、异步任务、HTTP 客户端、大模型 SDK 都必须考虑的基础机制。
```

---

## 三、基础知识铺垫

这一部分是本节最重要的基础。

你以后做任何后端系统、AI 应用、RAG、Agent、微服务调用，都绕不开 timeout。

### 1. timeout 是什么

timeout 就是：

```text
最多等多久。
```

更完整地说：

```text
当一个操作在规定时间内没有完成，系统主动放弃等待，并进入错误处理、重试、降级或返回失败的流程。
```

比如：

```text
调用模型最多等 30 秒
调用 Java 订单服务最多等 5 秒
查询 Qdrant 最多等 5 秒
连接上游服务最多等 1 秒
读取响应最多等 5 秒
```

timeout 的本质不是为了“让调用更快”。

timeout 是为了：

```text
限制最坏情况。
```

正常情况下，一个接口可能 200ms 就返回。

但异常情况下，它可能：

```text
卡住
排队
网络抖动
连接建立不了
响应发到一半停住
上游死锁
模型生成很久
向量库查询卡住
```

timeout 就是告诉系统：

```text
不能无限等。
```

### 2. 为什么不能无限等待

无限等待会带来很多问题。

#### 用户体验变差

用户点击一次按钮，页面一直转圈。

用户不知道：

```text
系统是不是挂了
请求是不是成功了
要不要重新提交
```

这会让用户体验很差。

#### 线程或连接被占住

后端处理一个请求通常会占用：

```text
线程
协程
数据库连接
HTTP 连接
内存
队列槽位
```

如果很多请求都卡住，资源会被耗尽。

#### 故障会放大

假设 Java 服务变慢。

如果 Python AI 服务没有 timeout，就会有越来越多请求卡在 Java 调用上。

结果是：

```text
Java 服务慢
Python 服务也被拖慢
用户请求堆积
更多连接被占住
整个系统变慢
```

这就是故障放大。

#### retry 和 fallback 没有机会执行

如果你一直等，就不会进入异常处理。

也就无法：

```text
retry
fallback
返回安全兜底答案
提示用户稍后重试
记录稳定 error_code
触发告警
```

所以 timeout 是稳定性保护的入口。

### 3. timeout 不是越短越好

很多初学者会想：

```text
既然 timeout 能防卡住，那我设成 1 秒是不是更好？
```

不一定。

timeout 太短会导致：

```text
1. 正常请求被误杀
2. LLM 还没生成完就被取消
3. RAG 查询稍慢就返回无上下文
4. 用户看到更多失败
5. retry 增多，反而让系统更忙
```

timeout 太长会导致：

```text
1. 用户等太久
2. 资源被占住太久
3. 故障扩散更慢但更严重
4. fallback 太晚发生
```

所以 timeout 是权衡。

你要根据：

```text
用户能接受多久
上游正常延迟是多少
P95/P99 延迟是多少
操作是否关键
有没有 fallback
有没有 retry
操作是否写入
```

来设计。

### 4. connect timeout 是什么

connect timeout 是连接超时。

它限制的是：

```text
建立连接最多等多久。
```

比如你的 Python 服务要连接：

```text
http://java-mock-service:8001
```

连接过程可能失败：

```text
DNS 解析慢
目标地址不可达
端口没开
网络不通
连接池没有可用连接
防火墙阻断
```

connect timeout 保护的是：

```text
不要在连接阶段卡太久。
```

connect timeout 通常应该比 read timeout 短。

因为连接建立如果很久都不成功，通常说明网络或服务状态异常。

### 5. read timeout 是什么

read timeout 是读取超时。

它限制的是：

```text
等待响应数据最多等多久。
```

例如：

```text
连接已经建立
请求已经发出
但是上游迟迟不返回响应体
```

这时就是 read timeout 负责限制等待。

LLM 调用里，read timeout 很重要。

因为模型可能：

```text
排队
生成很慢
输出很长
服务端处理很久
```

如果 read timeout 太短，正常的模型响应也可能被取消。

### 6. write timeout 是什么

write timeout 是写入请求数据超时。

它限制的是：

```text
发送请求体最多等多久。
```

比如：

```text
上传大文件
发送大量 JSON
发送很长 prompt
批量写入向量
```

如果请求体很大，写入也可能卡住。

在当前项目里，write timeout 可能涉及：

```text
发送工单创建 JSON
批量写入 Qdrant points
发送 embedding 请求
发送 LLM prompt
```

### 7. pool timeout 是什么

pool timeout 是连接池超时。

它限制的是：

```text
从连接池获取连接最多等多久。
```

如果你的 HTTP client 有连接池，同时有很多请求并发发出，连接池可能不够用。

这时请求不是卡在网络连接，也不是卡在读取响应，而是卡在：

```text
等一个可用连接。
```

这就是 pool timeout。

pool timeout 对高并发系统很重要。

当前项目还不是高并发生产部署，但现在先知道这个概念。

### 8. total timeout / operation timeout 是什么

total timeout 是整个请求的总时间限制。

operation timeout 是更泛化的说法：

```text
某个完整操作最多允许多久。
```

比如：

```text
LLM 意图识别最多 30 秒
订单查询最多 5 秒
RAG 检索最多 5 秒
整个 Agent invoke 最多 60 秒
```

connect/read/write/pool 是更细的网络阶段。

operation timeout 是业务视角的总限制。

在异步 Python 里，`asyncio.timeout()` 就是典型的 operation timeout。

### 9. LLM 为什么必须有 timeout

LLM 是高风险外部依赖。

它可能：

```text
排队
限流
网络慢
生成内容很长
模型服务波动
供应商接口异常
```

如果 LLM 没有 timeout，用户可能一直等。

而且 LLM 调用通常比较贵。

如果再叠加默认 retry，可能会：

```text
等更久
花更多 token 成本
制造更多上游压力
```

当前项目里：

```text
Settings.request_timeout_seconds = 30.0
Settings.llm_max_retries = 2
```

`create_openai_compatible_client()` 已经把它传给 OpenAI client：

```text
timeout=settings.request_timeout_seconds
max_retries=settings.llm_max_retries
```

本节不是重新写 LLM client。

本节是把这件事放进统一 timeout 策略里。

### 10. Java 工具为什么必须有 timeout

当前智能工单 Agent 会调用 Java mock 服务：

```text
GET /orders/{order_id}
POST /tickets
```

如果 Java 服务慢，Python Agent 不能一直等。

当前项目里：

```text
Settings.java_mock_service_timeout_seconds = 5.0
```

并且 Java client 已经把 timeout 映射成：

```text
TOOL_TIMEOUT
```

这是好的。

本节要补的是：

```text
query_order 和 create_ticket timeout 后不能完全一样处理。
```

因为一个是读，一个是写。

### 11. 读操作 timeout 和写操作 timeout 的区别

读操作通常是：

```text
查询订单
查询知识库
查询向量库
```

读操作一般不会改变业务数据。

读操作 timeout 后，用户稍后重试，通常不会产生重复副作用。

写操作通常是：

```text
创建工单
扣款
发货
修改订单
发送通知
```

写操作会改变业务状态。

写操作 timeout 最麻烦的地方是：

```text
你不知道上游到底有没有写成功。
```

可能发生：

```text
请求已经到达 Java 服务
Java 服务已经创建了工单
但是响应在返回途中超时
Python 端以为失败
```

如果这时你直接重试，可能创建重复工单。

所以写操作 retry 必须考虑：

```text
幂等性
```

当前项目创建工单时已经发送：

```text
Idempotency-Key
```

所以策略上可以说：

```text
创建工单 timeout 后，只有存在幂等键时才允许安全 retry。
```

### 12. 什么是幂等

幂等是：

```text
同一个操作执行一次和执行多次，最终效果一样。
```

例如：

```text
GET /orders/A1001
```

一般是幂等的。

多查几次，订单不会多出来。

但：

```text
POST /tickets
```

默认不是幂等的。

多提交几次，可能创建多个工单。

如果加上：

```text
Idempotency-Key: confirmation-idempotency-001
```

上游服务可以识别这是同一个请求。

这样重复提交时，上游可以返回同一个结果，避免重复创建。

### 13. timeout 和 retry 的关系

timeout 是：

```text
等太久就放弃当前等待。
```

retry 是：

```text
失败后再试一次或几次。
```

它们经常配合，但不是一回事。

你不能因为有 timeout 就一定 retry。

要看：

```text
1. 操作是否幂等
2. 错误是否临时
3. 用户是否能等待
4. retry 是否会增加成本
5. retry 是否会加剧上游压力
6. 是否已经有 fallback
```

LLM timeout 可以 retry，但要小心成本。

订单查询 timeout 可以 retry，因为是读操作。

创建工单 timeout 只有幂等键存在时才考虑 retry。

### 14. timeout 和 fallback 的关系

fallback 是：

```text
主链路失败后，返回一个安全、可解释、不会误导用户的替代结果。
```

例如：

```text
LLM 意图识别超时 -> 使用规则兜底
RAG 检索超时 -> 使用缓存或返回无上下文安全回答
订单查询超时 -> 告诉用户订单查询暂时超时，请稍后重试
创建工单超时 -> 告诉用户稍后查看是否已创建成功，避免重复提交
```

fallback 不等于假装成功。

fallback 的核心是：

```text
诚实、安全、可恢复。
```

### 15. timeout 为什么要映射 error_code

如果 timeout 只保留底层异常：

```text
ReadTimeout
APITimeoutError
TimeoutError
```

上层业务很难统一处理。

不同库的异常名不同：

```text
httpx.ReadTimeout
httpx.ConnectTimeout
openai.APITimeoutError
asyncio TimeoutError
```

所以项目里需要稳定 error_code：

```text
LLM_TIMEOUT
TOOL_TIMEOUT
RAG_VECTOR_STORE_TIMEOUT
RAG_GENERATION_TIMEOUT
EMBEDDING_TIMEOUT
```

稳定 error_code 的价值是：

```text
1. 日志好查
2. metrics 好聚合
3. Agent 分支好判断
4. 用户消息好控制
5. 测试好覆盖
6. 面试表达更清晰
```

---

## 四、本节主题系统讲解

下面把本节的策略系统讲清楚。

### 1. 当前项目已有的 timeout 基础

当前项目已有这些配置：

```text
request_timeout_seconds = 30.0
java_mock_service_timeout_seconds = 5.0
qdrant_timeout_seconds = 5.0
milvus_timeout_seconds = 5.0
```

这些配置已经被用在：

```text
OpenAI compatible client
JavaOrderClient
JavaTicketClient
QdrantVectorStore
MilvusVectorStore
embedding request
```

也就是说，项目不是完全没有 timeout。

但它们是分散的。

本节把它们整理成：

```text
统一 timeout 策略表。
```

### 2. 本节新增什么

本节新增：

```text
app/agents/timeout_strategy.py
tests/test_ticket_agent_timeout_strategy.py
```

它做的事：

```text
1. 定义 TimeoutBudget
2. 定义 TicketAgentTimeoutPolicy
3. 定义 TimeoutFailure
4. 从 Settings 构建当前 Agent 的 timeout 策略表
5. 分类 httpx / OpenAI / asyncio 风格 timeout
6. 判断 timeout 后是否允许 retry
7. 判断写操作是否需要幂等键
8. 生成适合日志和 metrics 的 timeout 字段
9. 过滤 metrics 里的高基数字段
```

### 3. 本节策略表

本节默认策略包括：

| 策略 key | 依赖 | 操作 | error_code | fallback | retry |
| --- | --- | --- | --- | --- | --- |
| `llm.intent_classification` | LLM | 意图识别 | `LLM_TIMEOUT` | 允许 | 允许 |
| `llm.field_extraction` | LLM | 字段提取 | `LLM_TIMEOUT` | 允许 | 允许 |
| `embedding.create` | embedding | 生成向量 | `EMBEDDING_TIMEOUT` | 不允许 | 允许 |
| `java.query_order` | Java 读工具 | 查询订单 | `TOOL_TIMEOUT` | 允许 | 允许 |
| `java.create_ticket` | Java 写工具 | 创建工单 | `TOOL_TIMEOUT` | 不允许 | 需要幂等键 |
| `qdrant.vector_search` | Qdrant | 向量检索 | `RAG_VECTOR_STORE_TIMEOUT` | 允许 | 允许 |
| `milvus.vector_search` | Milvus | 向量检索 | `RAG_VECTOR_STORE_TIMEOUT` | 允许 | 允许 |
| `rag.generate_answer` | RAG 生成 | 生成答案 | `RAG_GENERATION_TIMEOUT` | 允许 | 允许 |

这个表非常重要。

它不是代码细节。

它是生产化思维。

你要学会对每个外部依赖问：

```text
最多等多久？
超时算什么错误码？
能不能 retry？
能不能 fallback？
如果是写操作，有没有幂等保护？
给用户什么提示？
日志和 metrics 记录什么字段？
```

### 4. 为什么 embedding timeout 不允许 fallback

embedding 是 RAG 入库或检索前的基础步骤。

如果没有向量，后续检索很难正常做。

在某些场景里可以 fallback，比如使用缓存向量。

但当前项目学习阶段还没有完整 embedding cache。

所以本节默认：

```text
embedding timeout -> retry_later
```

不假装有结果。

### 5. 为什么 RAG vector_search timeout 可以 fallback

向量检索超时后，可以有一些降级选择：

```text
1. 使用缓存的检索结果
2. 返回 no_context
3. 返回安全兜底回答
```

这比让整个请求一直卡住更好。

但要注意：

```text
fallback 不能编造知识库内容。
```

如果没查到或查超时，就要诚实告诉用户：

```text
当前知识库暂时不可用，无法基于知识库确认。
```

### 6. 为什么 LLM timeout 可以 fallback

当前智能工单 Agent 有 rule_based / fake_llm / real_llm 双模式。

真实 LLM 节点失败时，很多场景可以使用规则兜底。

例如：

```text
意图识别超时 -> 使用规则识别
字段提取超时 -> 使用规则提取
最终回答超时 -> 返回安全兜底消息
```

这就是：

```text
模型增强，而不是模型单点依赖。
```

AI 应用生产化里，这点很重要。

### 7. 为什么创建工单 timeout 不允许普通 fallback

创建工单是写操作。

超时后不能简单说：

```text
创建失败了，请再点一次。
```

因为它可能已经创建成功，只是响应没回来。

更安全的提示是：

```text
创建工单工具调用超时，请稍后查看是否已创建成功。
```

如果要自动 retry，必须有：

```text
Idempotency-Key
```

所以本节策略是：

```text
requires_idempotency_key=True
```

### 8. timeout metrics 里应该记录什么

timeout 发生后，metrics attributes 应该包含低基数字段：

```text
dependency_kind
operation
timeout_phase
error_code
retryable
fallback_allowed
```

这些字段适合聚合：

```text
哪个依赖 timeout 最多？
哪个 operation timeout 最多？
是 connect timeout 多，还是 read timeout 多？
哪些 timeout 能 fallback？
哪些 timeout 不能 retry？
```

### 9. timeout metrics 里不能记录什么

不能记录：

```text
trace_id
span_id
thread_id
user_message
prompt
messages
final_answer
raw_response
```

原因仍然是：

```text
高基数
敏感 payload
不适合聚合
```

这些可以进入日志或 trace 的受控字段，但不能进 metrics attributes。

### 10. 本节和后两节的关系

第 31 节讲：

```text
等多久就放弃。
```

第 32 节讲：

```text
放弃后能不能再试，怎么试。
```

第 33 节讲：

```text
如果上游持续不稳定，怎么限流、熔断、降级。
```

所以第 31 节不要提前把 retry 和 circuit breaker 全讲完。

但必须先把它们的边界讲清楚：

```text
timeout 是触发条件之一
retry 是失败后的动作之一
fallback 是失败后的用户体验保护
circuit breaker 是连续失败后的系统保护
```

---

## 五、本节代码讲解

本节新增：

```text
projects/ai-service/app/agents/timeout_strategy.py
projects/ai-service/tests/test_ticket_agent_timeout_strategy.py
```

下面只讲有学习价值的代码。

### 1. TimeoutBudget

`TimeoutBudget` 表示一组 timeout 时间预算。

核心字段：

```python
@dataclass(frozen=True)
class TimeoutBudget:
    total_seconds: float
    connect_seconds: float | None = None
    read_seconds: float | None = None
    write_seconds: float | None = None
    pool_seconds: float | None = None
```

你要理解：

```text
total_seconds 是总预算
connect_seconds 是连接预算
read_seconds 是读取预算
write_seconds 是写入预算
pool_seconds 是连接池等待预算
```

如果没有显式设置阶段预算，代码会根据总预算推导：

```text
connect = total * 0.2
write = total * 0.4
pool = total * 0.1
read = total
```

这不是唯一正确答案。

这是学习项目里的默认策略。

重点是让你看到：

```text
timeout 可以拆阶段，而不是只有一个秒数。
```

### 2. as_httpx_timeout_kwargs()

这个方法把预算转成接近 HTTPX 的 timeout 参数形状：

```python
{
    "timeout": 10.0,
    "connect": 2.0,
    "read": 10.0,
    "write": 4.0,
    "pool": 1.0,
}
```

真实接入时可以进一步构造成：

```python
httpx.Timeout(10.0, connect=2.0, read=10.0, write=4.0, pool=1.0)
```

本节没有直接替换现有 client。

因为当前目标是学习策略，不是大改所有 HTTP 调用。

### 3. TicketAgentTimeoutPolicy

这个类表示某类依赖的 timeout 策略。

核心字段：

```python
@dataclass(frozen=True)
class TicketAgentTimeoutPolicy:
    dependency_kind: TimeoutDependencyKind
    operation: str
    budget: TimeoutBudget
    error_code: str
    status_code: int
    retryable: bool
    max_retries: int
    fallback_allowed: bool
    recovery_action: TimeoutRecoveryAction
    requires_idempotency_key: bool = False
    user_message: str = "外部依赖响应超时，请稍后重试。"
```

它的学习价值在于：

```text
timeout 策略不只是 timeout_seconds。
```

真正的策略要包含：

```text
依赖是谁
操作是什么
预算是多少
错误码是什么
HTTP 状态码是什么
能否 retry
最多 retry 几次
能否 fallback
是否需要幂等键
给用户什么消息
```

### 4. TimeoutFailure

`TimeoutFailure` 表示一次 timeout 失败。

它不是异常本身。

它是把底层异常转成上层业务能理解的结构。

比如：

```text
httpx.ReadTimeout
```

可以转成：

```text
dependency_kind=java_read_tool
operation=query_order
phase=read
error_code=TOOL_TIMEOUT
status_code=504
retryable=true
fallback_allowed=true
```

这样 Agent 就能统一处理。

### 5. classify_timeout_phase()

这个函数识别 timeout 阶段。

它支持：

```text
httpx.ConnectTimeout -> connect
httpx.ReadTimeout -> read
httpx.WriteTimeout -> write
httpx.PoolTimeout -> pool
httpx.TimeoutException -> total
TimeoutError -> operation
类名包含 APITimeoutError -> operation
```

为什么 OpenAI 的 APITimeoutError 归为 operation？

因为它来自 SDK 层的大模型调用超时，不一定暴露到底是 connect 还是 read。

对 Agent 来说，它更像：

```text
模型调用这个完整 operation 超时。
```

### 6. is_timeout_retry_allowed()

这个函数判断能否 retry。

逻辑：

```text
policy.retryable 必须为 True
policy.max_retries 必须大于 0
如果需要幂等键，必须确认 idempotency_key_present=True
```

这体现了本节最重要的边界：

```text
写操作 timeout 不能随便 retry。
```

### 7. build_timeout_failure()

这个函数把 policy 和 timeout phase 转成失败对象。

它会根据：

```text
policy
phase
elapsed_ms
idempotency_key_present
```

生成：

```text
TimeoutFailure
```

后续可以用于：

```text
日志字段
metrics attributes
用户消息
Agent 分支判断
测试断言
```

### 8. sanitize_timeout_metric_attributes()

这个函数过滤 timeout metrics attributes。

它会排除：

```text
trace_id
span_id
thread_id
user_message
prompt
messages
final_answer
raw_response
```

这和第 28、30 节保持一致：

```text
metrics 只放低基数字段。
```

---

## 六、本节测试重点

本节新增测试：

```text
tests/test_ticket_agent_timeout_strategy.py
```

共 13 条。

### 测试 1：TimeoutBudget 推导阶段预算

验证：

```text
total=10
connect=2
read=10
write=4
pool=1
```

### 测试 2：显式阶段预算优先

如果手动传入 connect/read/write/pool，就使用手动值。

### 测试 3：非法 timeout 被拒绝

验证：

```text
0
负数
无限大
```

不能作为 timeout。

### 测试 4：策略表读取现有 Settings

验证：

```text
request_timeout_seconds
java_mock_service_timeout_seconds
qdrant_timeout_seconds
milvus_timeout_seconds
```

都被策略表使用。

### 测试 5：写工具 retry 需要幂等键

验证：

```text
java.create_ticket
requires_idempotency_key=True
没有幂等键不允许 retry
有幂等键才允许 retry
```

### 测试 6：读工具可以直接 retry

验证：

```text
java.query_order
```

作为读操作，不要求幂等键。

### 测试 7：HTTPX timeout 分类

验证：

```text
ConnectTimeout -> connect
ReadTimeout -> read
WriteTimeout -> write
PoolTimeout -> pool
TimeoutException -> total
```

### 测试 8：operation timeout 分类

验证：

```text
TimeoutError -> operation
FakeAPITimeoutError -> operation
RuntimeError -> unknown
```

### 测试 9：生成 LLM timeout failure

验证：

```text
error_code=LLM_TIMEOUT
status_code=504
retryable=true
fallback_allowed=true
elapsed_ms 保留两位
```

### 测试 10：写操作 failure 根据幂等键调整 retryable

验证同一个 timeout：

```text
无幂等键 -> retryable=false
有幂等键 -> retryable=true
```

### 测试 11：向量库 timeout 可以使用缓存或 no_context 降级

验证：

```text
RAG_VECTOR_STORE_TIMEOUT
use_cache_or_return_no_context
```

### 测试 12：timeout metrics 过滤高基数和敏感字段

验证：

```text
trace_id
span_id
thread_id
user_message
prompt
```

不会进入 metrics attributes。

### 测试 13：策略身份和状态码校验

验证：

```text
operation 不能为空
status_code 必须是错误状态码
```

---

## 七、常见排查场景

### 场景 1：LLM timeout 增多

先看 metrics：

```text
error_code=LLM_TIMEOUT
dependency_kind=llm
operation=ticket_intent_classification / ticket_field_extraction
```

再看第 30 节指标：

```text
gen_ai.client.operation.duration
gen_ai.client.token.usage
```

判断：

```text
是模型整体变慢？
是 input tokens 变多？
是 output tokens 变多？
是某个 prompt version 变慢？
```

处理方向：

```text
优化 prompt
减少 RAG 上下文
调整 max_output_tokens
调大合理 timeout
减少 retry
启用更稳的 fallback
```

### 场景 2：Java 订单查询 timeout

看：

```text
dependency_kind=java_read_tool
operation=query_order
error_code=TOOL_TIMEOUT
timeout_phase=connect/read
```

如果 connect timeout 多：

```text
可能是 Java 服务不可达、端口没开、网络问题。
```

如果 read timeout 多：

```text
可能是 Java 服务处理慢、数据库慢、接口阻塞。
```

因为 query_order 是读操作，可以让用户稍后重试。

### 场景 3：创建工单 timeout

看：

```text
dependency_kind=java_write_tool
operation=create_ticket
error_code=TOOL_TIMEOUT
requires_idempotency_key=true
```

这时不能轻易提示用户“再提交一次”。

更安全的是：

```text
请稍后查看是否已创建成功。
```

如果系统要自动 retry，必须确认：

```text
idempotency_key_present=true
```

### 场景 4：Qdrant / Milvus timeout

看：

```text
dependency_kind=vector_store / milvus
error_code=RAG_VECTOR_STORE_TIMEOUT
recovery_action=use_cache_or_return_no_context
```

处理方向：

```text
使用缓存
降低 top_k
优化过滤条件
检查向量库是否健康
检查虚拟机或 Docker 是否运行
检查网络连接
```

---

## 八、把本节讲给别人听

你可以这样讲：

```text
timeout 是外部调用最多等待多久的限制，它的目的不是让系统变快，而是限制最坏情况，防止一个慢依赖拖垮整个系统。

HTTP 调用里的 timeout 可以拆成 connect、read、write、pool。connect 是建立连接，read 是等待响应数据，write 是发送请求体，pool 是等待连接池。

LLM、Java 工具、Qdrant、Milvus、embedding 这些外部依赖都必须有 timeout。
timeout 发生后不能只看底层异常，而要映射成稳定 error_code，比如 LLM_TIMEOUT、TOOL_TIMEOUT、RAG_VECTOR_STORE_TIMEOUT。

读操作 timeout 和写操作 timeout 不能一样处理。读操作通常可以重试；写操作可能已经成功但响应超时，所以必须有幂等键才能安全重试。

timeout 和 retry、fallback 不是一回事。timeout 是放弃等待，retry 是失败后再试，fallback 是失败后返回安全替代结果。
```

如果你能完整讲出这段，说明你真正理解了本节。

---

## 九、本节练习

### 练习 1：解释四种 HTTPX timeout

请解释：

```text
connect timeout
read timeout
write timeout
pool timeout
```

参考答案：

```text
connect timeout：建立连接最多等待多久，连接不上就超时。

read timeout：连接建立并发送请求后，等待响应数据最多多久。

write timeout：发送请求体时最多等待多久，适合大请求体或网络写入慢的场景。

pool timeout：从连接池获取可用连接最多等待多久，高并发时可能触发。
```

### 练习 2：为什么不能无限等待 LLM

参考答案：

```text
因为 LLM 可能排队、生成很久、网络抖动或服务异常。
无限等待会让用户一直卡住，占用服务资源，也让 fallback 和错误处理没有机会执行。
LLM 调用还可能叠加 retry 和 token 成本，所以必须限制等待时间。
```

### 练习 3：判断读写操作 timeout 后能否直接 retry

请判断：

```text
GET /orders/A1001 超时
POST /tickets 超时且没有 Idempotency-Key
POST /tickets 超时且有 Idempotency-Key
Qdrant vector search 超时
```

参考答案：

```text
GET /orders/A1001：读操作，通常可以 retry。

POST /tickets 没有 Idempotency-Key：写操作，不应该直接 retry，可能重复创建。

POST /tickets 有 Idempotency-Key：可以考虑 retry，因为幂等键可以防止重复创建。

Qdrant vector search：读/检索操作，可以 retry，也可以使用缓存或返回 no_context 降级。
```

### 练习 4：timeout 和 retry 的区别

参考答案：

```text
timeout 是当前操作等待超过限制后放弃。
retry 是失败后重新尝试一次或多次。
timeout 可以触发 retry，但不是所有 timeout 都应该 retry。是否 retry 要看操作是否幂等、是否会增加成本、是否会加重上游压力、是否有 fallback。
```

### 练习 5：timeout 和 fallback 的区别

参考答案：

```text
timeout 是故障触发条件，表示外部依赖没有在规定时间内完成。
fallback 是故障后的替代处理方式，比如使用规则兜底、使用缓存、返回安全提示、返回 no_context。
fallback 不等于假装成功，必须诚实、安全、可恢复。
```

### 练习 6：为什么要把 timeout 映射成 error_code

参考答案：

```text
不同库的 timeout 异常不同，例如 httpx.ReadTimeout、httpx.ConnectTimeout、openai.APITimeoutError、TimeoutError。
如果上层直接依赖这些底层异常，业务处理会很乱。
映射成 LLM_TIMEOUT、TOOL_TIMEOUT、RAG_VECTOR_STORE_TIMEOUT 等稳定 error_code 后，日志、metrics、Agent 分支、测试和用户提示都更稳定。
```

### 练习 7：哪些字段不应该进入 timeout metrics attributes

请判断下面字段是否应该进入 timeout metrics attributes：

```text
dependency_kind
operation
timeout_phase
error_code
trace_id
thread_id
user_message
prompt
fallback_allowed
```

参考答案：

```text
适合：
dependency_kind
operation
timeout_phase
error_code
fallback_allowed

不适合：
trace_id：请求级高基数字段。
thread_id：会话级高基数字段。
user_message：敏感 payload。
prompt：大文本，可能敏感，且高基数。
```

---

## 十、自测题

### 自测 1：timeout 的核心目的是什么？

答案：

```text
timeout 的核心目的是限制最坏等待时间，防止外部依赖卡住后拖垮当前服务，并让系统有机会进入 retry、fallback、错误映射和告警流程。
```

### 自测 2：connect timeout 和 read timeout 最大区别是什么？

答案：

```text
connect timeout 发生在建立连接阶段，表示连接目标服务超时。
read timeout 发生在连接建立并发送请求后，等待响应数据超时。
```

### 自测 3：为什么写操作 timeout 比读操作 timeout 更危险？

答案：

```text
因为写操作可能已经在上游执行成功，只是响应返回超时。
如果客户端不知道结果就直接重试，可能造成重复写入，比如重复创建工单。
所以写操作 retry 必须考虑幂等键。
```

### 自测 4：Idempotency-Key 的作用是什么？

答案：

```text
Idempotency-Key 用来标识同一次写请求。
如果客户端因为 timeout 重试，上游可以根据同一个幂等键识别重复请求，返回同一结果或避免重复执行写入。
```

### 自测 5：为什么 LLM_TIMEOUT 可以 fallback？

答案：

```text
因为当前 Agent 可以用规则兜底或返回安全提示。
模型是增强能力，不应该成为唯一可用路径。
LLM 超时后 fallback 能保护用户体验，并避免整个流程完全卡死。
```

### 自测 6：为什么 RAG 检索 timeout 可以返回 no_context？

答案：

```text
因为向量库检索失败时，系统不能编造知识库内容。
如果没有缓存可用，可以诚实返回无上下文或安全兜底答案，这比无限等待或编造结果更安全。
```

### 自测 7：为什么 timeout metrics 不能带 trace_id？

答案：

```text
trace_id 每次请求几乎都不同，是高基数字段。
放进 metrics attributes 会导致时序数量膨胀，增加内存和存储成本，破坏聚合价值。
trace_id 应该放进日志和 trace，用于单次请求排查。
```

### 自测 8：timeout、retry、fallback 三者关系是什么？

答案：

```text
timeout 是等待超过限制后的失败触发条件。
retry 是失败后再试一次或多次。
fallback 是失败后返回安全替代结果。
timeout 可以触发 retry 或 fallback，但不是所有 timeout 都应该 retry，也不是所有 timeout 都能 fallback。
```

### 自测 9：本节为什么没有直接大改所有 HTTP client？

答案：

```text
因为本节学习重点是统一 timeout 策略，而不是一次性重构所有外部调用。
当前项目已有具体 timeout 配置和异常映射，本节先把策略、错误码、retry/fallback 边界和测试模型建立起来。
后续如果接入更细粒度 httpx.Timeout，可以复用本节 TimeoutBudget。
```

### 自测 10：本节最重要的一句话是什么？

答案：

```text
timeout 不是简单设置一个秒数，而是为每类外部依赖设计等待预算、错误码、重试边界、降级动作和用户提示。
```

---

## 十一、本节命令

在 `projects/ai-service` 目录运行：

```powershell
uv run pytest tests/test_ticket_agent_timeout_strategy.py
```

当前专项测试结果：

```text
13 passed
```

提交前还需要运行全量测试：

```powershell
uv run pytest
```

---

## 十二、本节小结

本节你真正要掌握的是：

```text
1. timeout 是最多等待多久，不是让调用更快，而是限制最坏情况。
2. 外部调用没有 timeout 会拖垮资源、用户体验和故障恢复。
3. HTTP timeout 可以拆成 connect、read、write、pool。
4. operation timeout 是业务操作总等待限制。
5. LLM、Java 工具、Qdrant、Milvus、embedding 都必须有 timeout。
6. 读操作 timeout 通常可以 retry。
7. 写操作 timeout 不能随便 retry，必须考虑幂等键。
8. timeout 后要映射稳定 error_code。
9. timeout 可以触发 retry 或 fallback，但三者不是一回事。
10. metrics 里只能放低基数字段，不能放 trace_id/thread_id/user_message/prompt。
```

本节新增：

```text
TimeoutBudget
TicketAgentTimeoutPolicy
TimeoutFailure
build_timeout_budget()
build_ticket_agent_timeout_policies()
classify_timeout_phase()
build_timeout_failure()
is_timeout_retry_allowed()
sanitize_timeout_metric_attributes()
```

下一节进入：

```text
阶段 6 第 32 节：retry 重试策略
```

下一节会继续讲：

```text
哪些错误可以 retry
哪些错误不能 retry
指数退避是什么
jitter 是什么
retry budget 是什么
为什么 retry 可能放大故障
LLM retry 和工具 retry 有什么不同
写操作 retry 如何依赖幂等键
```
