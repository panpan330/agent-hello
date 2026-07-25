# 阶段 6 第 20 节：工具节点错误处理升级

本节目标：让智能工单 Agent 的订单查询工具节点不只是“失败了”，而是能把失败分成清晰类型，并给出后续处理动作。

上一节我们已经完成：

```text
用户问订单
-> LangGraph 路由到 query_order_node
-> 提取订单号
-> QueryOrderArgs 校验参数
-> 调用 query_order 工具
-> JavaOrderClient 调用 Java mock 订单服务
-> 字段白名单映射
-> QueryOrderResult 校验结果
-> 写回 LangGraph state
```

这让 `query_order` 从占位节点变成真实工具节点。

但是只要工具真的接进来了，就一定会遇到失败。

失败可能来自用户：

```text
用户没有提供订单号
用户提供的订单号格式不对
用户给了不存在的订单号
```

失败也可能来自业务服务：

```text
Java 服务没有启动
Java 服务网络连接失败
Java 服务超时
Java 服务返回 500
Java 服务返回了不是 JSON 的内容
Java 服务返回的字段和 QueryOrderResult 不匹配
```

失败还可能来自系统未知异常：

```text
代码里出现未预料的 RuntimeError
依赖对象行为不符合预期
底层库抛了我们没有专门处理的异常
```

如果这些失败都只返回：

```text
工具调用失败，请稍后重试。
```

那对用户、开发者、测试、评测、监控都不够。

真实工程里，我们需要知道：

```text
这次失败属于哪一类？
用户应该补充信息，还是稍后重试？
系统应该记录为服务故障，还是数据契约问题？
后续能不能自动 retry？
这次错误能不能暴露给用户？
```

本节做的事情就是把这些问题结构化。

---

## 一、本节在主线里的位置

阶段 6 是生产化与评测阶段。

前面几节的关系可以这样看：

```text
第 13 节：真实 LLM 意图识别节点
第 14 节：真实 LLM 字段提取节点
第 15 节：Pydantic 校验模型输出
第 16 节：fake LLM 和真实 LLM 双模式
第 17 节：prompt 版本管理
第 18 节：模型输出失败处理
第 19 节：接入真实 query_order 到 LangGraph
第 20 节：工具节点错误处理升级
```

第 18 节处理的是：

```text
模型输出坏了怎么办？
```

第 20 节处理的是：

```text
工具执行坏了怎么办？
```

这两类失败不能混在一起。

模型输出失败通常是：

```text
空输出
非法 JSON
schema 校验失败
模型服务超时
模型配置错误
```

工具执行失败通常是：

```text
参数缺失
参数格式错误
业务对象不存在
业务服务超时
业务服务不可用
工具结果校验失败
未知运行时错误
```

两者都属于 AI 应用生产化问题，但边界不同。

模型输出失败重点保护：

```text
不要相信模型一定返回可用结构
```

工具执行失败重点保护：

```text
不要相信业务工具一定可用，也不要把工具错误粗暴暴露给用户
```

---

## 二、本节学习目标

学完本节，你要能解释清楚：

1. 为什么工具节点不能只保留 `code/message`。

   答案：`code/message` 能说明发生了什么错误，但不一定说明错误属于哪一类、用户下一步该做什么、系统是否应该 retry、是否需要人工或开发排查。生产化 Agent 需要更结构化的失败信号。

2. `code`、`kind`、`action`、`retryable` 分别是什么。

   答案：`code` 是具体错误码，适合日志和接口契约；`kind` 是错误类型，适合统计和评测；`action` 是建议处理动作，适合流程决策；`retryable` 表示这个错误是否适合自动或提示用户稍后重试。

3. 为什么 `ORDER_NOT_FOUND` 不应该被当成系统故障。

   答案：订单不存在通常是用户提供的订单号不对，或者订单确实不存在。它不是 Java 服务坏了，也不是工具代码坏了。正确动作是让用户确认订单号，而不是提示“系统繁忙”。

4. 为什么 `TOOL_TIMEOUT` 和 `TOOL_UPSTREAM_ERROR` 通常是可重试的。

   答案：超时、连接失败、上游 500 往往是临时性服务问题。用户稍后重试或系统后续做自动 retry 都有意义，所以 `retryable=True`。

5. 为什么 `TOOL_RESULT_VALIDATION_FAILED` 不应该直接把原始技术细节返回给用户。

   答案：工具结果校验失败说明业务服务返回的数据和 AI 服务期望契约不一致，属于系统内部问题。原始细节可能包含字段名、内部结构或调试信息，用户不需要看到，应该返回安全文案并让系统排查。

6. 为什么未知异常要收敛成安全失败。

   答案：未知异常可能包含内部堆栈、数据库信息、配置路径、敏感字段。用户侧只能看到通用安全提示，日志里记录错误类型即可。

7. 为什么本节仍然不用真实 Java 服务做自动化测试。

   答案：本节测试的是 LangGraph 工具节点如何处理不同失败，而不是 Java 服务是否启动。用 fake executor 可以稳定制造各种错误场景，测试更快、更可靠。

8. 为什么这些错误分类会服务后续课程。

   答案：后续学习 retry、rate limit、circuit breaker、可观测性、评测报告时，需要知道错误类型、是否可重试和建议动作。没有结构化字段，就只能从文案或日志里猜。

---

## 三、本节暂时不学什么

本节只升级 `query_order` 工具节点错误处理。

暂时不做：

- 不做真正自动 retry。
- 不做指数退避。
- 不做 circuit breaker。
- 不做 rate limit。
- 不做权限校验。
- 不做写操作确认。
- 不改 Java mock 服务。
- 不启动 VMware Ubuntu。
- 不依赖 Docker。
- 不新增真实数据库。
- 不改 `create_ticket` 写操作节点。
- 不做 LangSmith trace 可视化。
- 不做 OpenTelemetry span。
- 不做前端错误展示。

为什么先不做 retry？

因为 retry 不是简单地“失败就再来一次”。

在做 retry 前必须先知道：

```text
哪些错误可以重试
哪些错误不能重试
重试失败后怎么返回
重试次数怎么控制
重试会不会打爆上游服务
重试会不会导致重复写操作
```

本节先补的是 retry 的前置基础：

```text
retryable 字段
```

---

## 四、基础知识铺垫

### 1. 什么是工具节点错误

工具节点错误是指：

```text
LangGraph 节点在调用外部业务能力或内部工具函数时发生的错误。
```

在当前项目里，`query_order_node` 调用的是订单查询工具。

所以它可能遇到：

```text
订单号缺失
订单号校验失败
query_order 工具抛错
JavaOrderClient 抛错
Java 服务返回错误
工具结果校验失败
未知 Python 异常
```

注意，工具节点错误不是模型输出错误。

模型输出错误发生在：

```text
LLM 返回内容不符合我们要求
```

工具节点错误发生在：

```text
后端要执行真实业务动作时，参数、工具、服务或返回结果出了问题
```

这两类错误都要处理，但分类体系不同。

### 2. 为什么不能只用一个 `except Exception`

最粗糙的写法是：

```python
try:
    result = executor(arguments)
except Exception:
    return "工具调用失败，请稍后重试"
```

这段代码表面上不会崩溃。

但它有严重问题：

```text
订单不存在也变成系统失败
参数格式错误也提示用户稍后重试
Java 服务 500 和返回字段错误无法区分
未知异常可能被悄悄吞掉
后续无法统计失败原因
后续无法决定哪些错误能 retry
测试只能断言一句文案
```

真正的错误处理不是“把异常吞掉”。

真正的错误处理是：

```text
识别错误
分类错误
选择动作
返回安全信息
记录足够排查的信息
保留后续自动化处理的结构化字段
```

### 3. `code` 是什么

`code` 是具体错误码。

比如：

```text
ORDER_ID_REQUIRED
TOOL_ARGUMENTS_VALIDATION_FAILED
ORDER_NOT_FOUND
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TOOL_RESULT_VALIDATION_FAILED
TOOL_CALL_FAILED
```

错误码通常用于：

```text
接口响应
日志搜索
测试断言
后端契约
监控聚合
```

错误码要稳定。

比如 `ORDER_NOT_FOUND` 一旦成为契约，就不要随便改成 `ORDER_NOT_EXIST`。

否则调用方、测试、监控、文档都会受影响。

### 4. `kind` 是什么

`kind` 是错误类型。

它比 `code` 更抽象。

本节新增的类型包括：

```text
missing_order_id
argument_validation
not_found
timeout
upstream_error
result_validation
tool_error
unknown_error
```

为什么需要 `kind`？

因为多个不同错误码可能属于同一种错误类型。

例如以后可能有：

```text
ORDER_SERVICE_502
ORDER_SERVICE_503
ORDER_SERVICE_CONNECTION_FAILED
```

它们具体 `code` 不同，但都可以归为：

```text
upstream_error
```

评测和监控更适合按 `kind` 统计：

```text
订单查询失败中，多少是用户缺参数？
多少是订单不存在？
多少是上游服务不可用？
多少是结果契约不一致？
```

### 5. `action` 是什么

`action` 是建议后续动作。

本节新增：

```text
ask_user_for_order_id
ask_user_to_check_order_id
retry_later
contact_human_support
investigate_system
```

它回答的问题是：

```text
系统知道失败后，下一步应该怎么处理？
```

例如：

```text
missing_order_id
-> ask_user_for_order_id

not_found
-> ask_user_to_check_order_id

timeout
-> retry_later

result_validation
-> investigate_system

unknown_error
-> retry_later
```

注意：本节只是把动作写出来，不是真的执行所有动作。

比如 `retry_later` 只是说明这个错误适合后续重试。

真正自动 retry 会在后面专门学习。

### 6. `retryable` 是什么

`retryable` 表示这个错误是否适合重试。

它是布尔值：

```text
True
False
```

但判断它不能凭感觉。

常见原则是：

```text
用户输入问题通常不可重试
临时网络或上游服务问题通常可重试
内部数据契约问题通常不靠用户重试解决
未知异常要保守处理
```

本节映射如下：

```text
缺订单号
-> retryable=False
因为重试同样的输入仍然缺订单号。

订单号格式错误
-> retryable=False
因为需要用户改参数，不是系统自动重试。

订单不存在
-> retryable=False
因为用户需要确认订单号。

工具超时
-> retryable=True
因为稍后可能恢复。

上游服务不可用
-> retryable=True
因为可能是临时故障。

工具结果校验失败
-> retryable=False
因为这更像系统契约问题，需要排查。

未知异常
-> retryable=True
因为用户侧只能提示稍后重试，系统侧要看日志排查。
```

实际生产系统里，`retryable` 还要结合：

```text
工具是否只读
操作是否幂等
失败发生在请求前还是请求后
上游是否有幂等保护
当前服务压力是否过高
```

本节的 `query_order` 是只读查询，所以把超时和上游错误标成可重试比较合理。

### 7. 为什么只读工具更容易 retry

查询订单是只读操作。

重复查询通常不会改变业务数据。

所以它比写操作更适合 retry。

例如：

```text
查订单超时
-> 稍后再查一次通常安全
```

但写操作不同。

例如：

```text
创建工单超时
```

这时候不能马上盲目重试。

因为可能出现：

```text
第一次请求其实已经创建成功
只是响应在路上超时
第二次重试又创建一张重复工单
```

所以写操作 retry 通常必须结合：

```text
idempotency_key
用户确认
查询已创建结果
重试次数限制
```

这也是为什么本节只升级 `query_order`，不直接动 `create_ticket`。

### 8. 什么是用户可见错误和系统内部错误

错误信息有两种读者：

```text
用户
开发者
```

用户需要的是：

```text
我现在该做什么？
```

开发者需要的是：

```text
哪里坏了，怎么排查？
```

这两种信息不能混在一起。

比如 Java 服务返回的数据字段不对，开发者需要知道：

```text
哪个字段缺了
哪个字段类型错了
哪个 schema 校验失败
```

但用户不需要看到：

```text
field logistics_message missing
Pydantic literal_error
internal field mismatch
```

所以本节对 `TOOL_RESULT_VALIDATION_FAILED` 做了安全文案替换：

```text
订单查询服务返回的数据暂时无法处理，请稍后重试或联系人工客服。
```

这句话能让用户知道当前无法处理，但不会泄露内部结构。

### 9. 为什么 `AppException` 还不够

项目里已经有 `AppException`：

```python
class AppException(Exception):
    def __init__(self, code, message, status_code, details=None):
        ...
```

它已经比普通异常强很多。

它有：

```text
code
message
status_code
details
```

但对 Agent 来说还差几层语义：

```text
kind
action
retryable
```

`AppException` 更像底层服务或工具边界的错误表达。

`TicketOrderQueryFailure` 更像 Agent 节点理解后的失败表达。

可以这样区分：

```text
AppException：
工具或服务告诉我发生了什么。

TicketOrderQueryFailure：
Agent 判断这个错误属于什么类型，后续应该怎么处理。
```

这就是“异常”和“失败策略”的区别。

### 10. 为什么要测试未知异常不泄露

未知异常最危险。

因为它可能包含：

```text
数据库连接串
内部路径
字段名
第三方服务响应
配置名
调试信息
```

所以测试里故意制造：

```text
RuntimeError("database password leaked in stack trace")
```

然后断言：

```text
final_answer 里不能出现 database password
```

这个测试不是为了真的有这个错误。

它是在保护一个安全原则：

```text
未知异常不能直接返回给用户。
```

---

## 五、本节主题系统讲解

### 1. 第 19 节的问题在哪里

第 19 节的失败处理大致是：

```text
缺订单号
-> 返回 ORDER_ID_REQUIRED

QueryOrderArgs 校验失败
-> 返回 TOOL_ARGUMENTS_VALIDATION_FAILED

AppException
-> 原样返回 exc.code 和 exc.message

未知 Exception
-> 返回 TOOL_CALL_FAILED
```

这个版本能保证流程不崩溃。

但它不够生产化。

因为 `AppException` 原样返回有两个问题：

```text
不同错误没有被分成 Agent 能理解的类型
部分内部错误不一定适合把原 message 返回给用户
```

例如：

```text
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TOOL_RESULT_VALIDATION_FAILED
```

它们都可能是 `AppException`。

如果只看 `code/message`，后续要做 retry、告警、评测统计就比较困难。

所以第 20 节新增一层：

```text
AppException / Exception
-> classify_ticket_order_query_failure()
-> TicketOrderQueryFailure
-> 写入 state
```

### 2. 新增的核心对象：`TicketOrderQueryFailure`

本节新增：

```python
@dataclass(frozen=True)
class TicketOrderQueryFailure:
    code: str
    kind: TicketOrderQueryFailureKind
    action: TicketOrderQueryFailureAction
    message: str
    retryable: bool
    status_code: int | None = None
```

这个对象不是为了包装得更复杂。

它的价值是把工具错误拆成几层：

```text
code
具体错误码。

kind
错误类型。

action
建议处理动作。

message
用户可见安全文案。

retryable
是否适合重试。

status_code
底层或接口语义上的状态码。
```

如果以后要接监控或评测，可以直接统计：

```text
kind=timeout 的比例
action=retry_later 的比例
retryable=True 的比例
status_code=502 的比例
```

如果没有这些字段，就只能从 `final_answer` 或日志字符串里解析，非常脆弱。

### 3. 新增的错误类型

本节定义：

```python
TicketOrderQueryFailureKind = Literal[
    "missing_order_id",
    "argument_validation",
    "not_found",
    "timeout",
    "upstream_error",
    "result_validation",
    "tool_error",
    "unknown_error",
]
```

逐个解释：

```text
missing_order_id
用户没有提供订单号。

argument_validation
订单号提取到了，但不符合工具参数模型。

not_found
订单不存在。

timeout
调用订单服务超时。

upstream_error
Java 订单服务不可用、连接失败或返回 5xx。

result_validation
订单服务返回了数据，但 AI 服务校验后发现结构不符合契约。

tool_error
工具层已经收敛过的通用错误。

unknown_error
未被识别的普通异常。
```

这些类型不是随便起名。

它们对应真实排查思路：

```text
用户输入问题
业务对象问题
上游服务稳定性问题
数据契约问题
未知代码问题
```

### 4. 新增的处理动作

本节定义：

```python
TicketOrderQueryFailureAction = Literal[
    "ask_user_for_order_id",
    "ask_user_to_check_order_id",
    "retry_later",
    "contact_human_support",
    "investigate_system",
]
```

逐个解释：

```text
ask_user_for_order_id
用户没给订单号，应该追问。

ask_user_to_check_order_id
用户给了订单号，但订单不存在或格式不对，应该让用户检查。

retry_later
大概率是临时故障，可以稍后重试。

contact_human_support
需要人工客服介入。

investigate_system
更像系统内部契约或实现问题，需要开发排查。
```

注意，`action` 不等于马上执行。

当前只是写进 state。

后续可以基于它做：

```text
自动 retry
前端按钮展示
人工客服转接
告警分组
评测统计
```

### 5. `classify_ticket_order_query_failure()` 的作用

本节新增的核心函数：

```python
def classify_ticket_order_query_failure(exc: Exception) -> TicketOrderQueryFailure:
    ...
```

它接收一个异常，返回一个结构化失败对象。

它的逻辑可以概括为：

```text
如果不是 AppException
-> unknown_error

如果 code 是 ORDER_NOT_FOUND
-> not_found

如果 code 是 TOOL_TIMEOUT
-> timeout

如果 code 是 TOOL_UPSTREAM_ERROR
-> upstream_error

如果 code 是 TOOL_RESULT_VALIDATION_FAILED
-> result_validation

如果 code 是 TOOL_CALL_FAILED
-> tool_error

其他 AppException
-> tool_error + contact_human_support
```

这一步是从“异常”到“策略”的转换。

非常重要。

### 6. 参数校验失败为什么不走异常分类函数

`QueryOrderArgs(order_id=order_id)` 校验失败时，确实会抛 `ValidationError`。

但这是 Pydantic 的参数校验异常，不是工具执行异常。

所以本节单独提供：

```python
build_order_query_argument_validation_failure()
```

它返回：

```text
code=TOOL_ARGUMENTS_VALIDATION_FAILED
kind=argument_validation
action=ask_user_to_check_order_id
retryable=False
status_code=422
```

为什么 `status_code=422`？

因为 422 通常表示请求语义可理解，但参数校验不通过。

虽然这里不是 FastAPI 接口直接返回 422，但这个状态码语义能帮助我们表达：

```text
输入格式不符合要求
```

### 7. 缺订单号为什么是 `missing_order_id`

缺订单号不是异常。

用户可能只是还没提供完整信息。

所以它不走 `failed`，而是：

```text
order_query_status = "missing_order_id"
order_query_error_kind = "missing_order_id"
order_query_error_action = "ask_user_for_order_id"
order_query_retryable = False
```

这表达的是：

```text
当前无法查询
原因是缺少必要信息
系统应该追问用户
重复执行同样输入没有意义
```

这比一句“订单号不能为空”更适合 Agent 多轮流程。

### 8. 订单不存在为什么不可重试

`ORDER_NOT_FOUND` 被映射为：

```text
kind = not_found
action = ask_user_to_check_order_id
retryable = False
```

原因是：

```text
同一个订单号再查一次，大概率还是不存在
```

它更像用户提供的信息不正确，或者订单确实不存在。

所以用户下一步应该是：

```text
确认订单号是否正确
```

而不是：

```text
稍后重试
```

### 9. 超时为什么可重试

`TOOL_TIMEOUT` 被映射为：

```text
kind = timeout
action = retry_later
retryable = True
```

超时表示：

```text
请求发出去了，但在规定时间内没有拿到结果。
```

它可能是：

```text
Java 服务慢
网络慢
服务短暂卡住
依赖数据库慢
```

这种问题有临时性。

稍后重试有可能成功。

因为查询订单是只读操作，所以可重试风险较低。

### 10. 上游错误为什么可重试

`TOOL_UPSTREAM_ERROR` 被映射为：

```text
kind = upstream_error
action = retry_later
retryable = True
```

上游错误包括：

```text
连接失败
Java 服务不可用
Java 服务返回 500
Java 服务返回非 200 状态
```

这些通常不是用户能修的。

用户能做的是稍后再试。

系统能做的是：

```text
记录日志
后续接入 retry
后续接入 circuit breaker
后续接入告警
```

### 11. 结果校验失败为什么需要系统排查

`TOOL_RESULT_VALIDATION_FAILED` 被映射为：

```text
kind = result_validation
action = investigate_system
retryable = False
message = 安全文案
```

这类错误说明：

```text
Java 服务有返回
但是返回结构不符合 QueryOrderResult
```

比如：

```text
缺少 order_status
payment_status 枚举值不对
can_create_ticket 不是 bool
logistics_message 不是字符串
返回根结构不是 dict
返回不是合法 JSON
```

这通常不是用户输入能解决的。

它更像：

```text
服务契约变了
字段映射漏了
Java mock 返回异常
AI 服务 schema 没同步
```

所以要让系统排查，而不是让用户不断重试。

### 12. 未知异常为什么用安全兜底

未知异常被映射为：

```text
code = TOOL_CALL_FAILED
kind = unknown_error
action = retry_later
retryable = True
message = 订单查询工具调用失败，请稍后重试或联系人工客服。
```

这有两个目的：

```text
保护用户体验
保护内部细节不泄露
```

真实项目里，未知异常的原始 message 不能直接出现在用户回答里。

因为它可能包含敏感信息。

本节测试专门验证：

```text
RuntimeError("database password leaked in stack trace")
```

不会出现在 `final_answer`。

### 13. 失败状态现在包含哪些字段

第 20 节后，工具失败 state 里会有：

```text
order_query_order_id
order_query_status
order_query_error_code
order_query_error_kind
order_query_error_action
order_query_error_message
order_query_retryable
order_query_error_status_code
agent_error_code
agent_error_message
agent_error_node
fallback_used
final_answer
node_history
```

这些字段可以分成三组：

业务工具组：

```text
order_query_order_id
order_query_status
order_query_error_code
order_query_error_kind
order_query_error_action
order_query_error_message
order_query_retryable
order_query_error_status_code
```

Agent 通用错误组：

```text
agent_error_code
agent_error_message
agent_error_node
fallback_used
```

展示和流程组：

```text
final_answer
node_history
```

这样既能满足订单查询节点自己的业务表达，也能兼容整个 Agent 的通用 fallback 体系。

### 14. 成功状态为什么也写空错误字段

成功时现在写：

```text
order_query_error_code = None
order_query_error_kind = None
order_query_error_action = None
order_query_error_message = None
order_query_retryable = None
order_query_error_status_code = None
```

为什么成功时也要写这些空值？

因为这样 state 的结构更稳定。

调用方看到 `order_query_status=succeeded` 时，可以明确知道：

```text
没有错误
没有错误类型
没有错误动作
不涉及 retryable
没有错误状态码
```

这比字段完全缺失更容易做统一处理。

### 15. 日志为什么要加 kind/action/retryable

本节升级了工具失败日志。

失败日志现在包含：

```text
order_id
code
kind
action
retryable
status_code
error_type
```

日志不是只给人看的。

后续接入日志系统后，可以基于字段搜索和统计：

```text
kind=timeout
action=retry_later
retryable=True
status_code=504
```

这比只搜索“工具调用失败”有用得多。

缺订单号也补了一条日志：

```text
ticket_agent_query_order_missing_order_id message_length=...
```

它不记录用户原文，只记录长度。

这能减少敏感信息进入日志。

---

## 六、本节代码改动讲解

### 1. 新增 `TicketOrderQueryFailureKind`

代码：

```python
TicketOrderQueryFailureKind = Literal[
    "missing_order_id",
    "argument_validation",
    "not_found",
    "timeout",
    "upstream_error",
    "result_validation",
    "tool_error",
    "unknown_error",
]
```

学习重点：

```text
Literal 用来限制可选字符串范围。
```

这样可以减少随手写错字符串的问题。

比如你不能随便写：

```text
time_out
notfound
upstream
```

而应该使用统一约定：

```text
timeout
not_found
upstream_error
```

错误类型稳定后，测试、日志、评测才稳定。

### 2. 新增 `TicketOrderQueryFailureAction`

代码：

```python
TicketOrderQueryFailureAction = Literal[
    "ask_user_for_order_id",
    "ask_user_to_check_order_id",
    "retry_later",
    "contact_human_support",
    "investigate_system",
]
```

学习重点：

```text
错误类型说明发生了什么。
处理动作说明接下来怎么做。
```

不要把这两者混在一起。

例如：

```text
kind=timeout
action=retry_later
```

超时是事实。

稍后重试是策略。

### 3. 新增 `TicketOrderQueryFailure`

代码：

```python
@dataclass(frozen=True)
class TicketOrderQueryFailure:
    code: str
    kind: TicketOrderQueryFailureKind
    action: TicketOrderQueryFailureAction
    message: str
    retryable: bool
    status_code: int | None = None
```

学习重点：

```text
dataclass 用来承载结构化数据。
frozen=True 表示创建后不应该再改。
```

为什么这里适合用 `dataclass`？

因为它只是一个内部策略对象。

它不是 API 请求体。

它不是数据库模型。

它不是 Pydantic 校验入口。

它只是把分类结果打包起来，传给 state 构造函数。

### 4. 新增错误码分组常量

代码类似：

```python
TICKET_ORDER_QUERY_TIMEOUT_CODES = frozenset({"TOOL_TIMEOUT"})
```

为什么用集合？

因为未来可能有多个错误码归为同一类。

例如：

```text
TOOL_TIMEOUT
ORDER_SERVICE_READ_TIMEOUT
ORDER_SERVICE_CONNECT_TIMEOUT
```

都可以归为：

```text
timeout
```

用集合后，分类函数不用改结构，只要扩展集合内容。

### 5. 新增 `classify_ticket_order_query_failure()`

这是本节核心函数。

它把异常映射为失败策略对象。

它的输入是：

```text
Exception
```

输出是：

```text
TicketOrderQueryFailure
```

为什么输入不是 `AppException`？

因为真实节点里可能遇到普通 `Exception`。

所以函数要能处理：

```text
AppException
普通 Exception
```

这让节点代码更简单：

```python
failure = classify_ticket_order_query_failure(exc)
```

### 6. 修改 `build_order_query_missing_order_id_state()`

现在缺订单号返回更多字段：

```text
order_query_error_kind = missing_order_id
order_query_error_action = ask_user_for_order_id
order_query_retryable = False
order_query_error_status_code = None
```

学习重点：

```text
追问也是一种可结构化状态。
```

缺参数不是简单失败。

它是多轮对话里非常常见的中间状态。

### 7. 修改 `build_order_query_failure_state()`

原来传入：

```text
code
message
```

现在传入：

```text
failure: TicketOrderQueryFailure
```

这让函数能一次性写入：

```text
code
kind
action
message
retryable
status_code
```

学习重点：

```text
当参数之间强相关时，用对象封装比传一堆散字段更稳。
```

否则函数签名会越来越长：

```python
build_order_query_failure_state(
    order_id=...,
    code=...,
    kind=...,
    action=...,
    message=...,
    retryable=...,
    status_code=...,
)
```

这种写法容易传错。

### 8. 修改 `query_order_node()`

现在节点失败路径是：

```text
参数校验失败
-> build_order_query_argument_validation_failure()
-> build_order_query_failure_state()

AppException
-> classify_ticket_order_query_failure(exc)
-> build_order_query_failure_state()

Exception
-> classify_ticket_order_query_failure(exc)
-> build_order_query_failure_state()
```

节点不再自己判断每个错误码。

节点只负责：

```text
执行流程
调用分类函数
写 state
记日志
```

错误分类被集中在一个函数里。

这更容易测试，也更容易扩展。

---

## 七、本节测试讲解

本节测试主要新增在：

```text
tests/test_ticket_agent_query_order_node.py
```

### 1. 成功查询测试

成功查询现在额外断言：

```text
order_query_error_kind is None
order_query_error_action is None
order_query_retryable is None
order_query_error_status_code is None
```

这说明成功时不会残留错误状态。

### 2. 缺少订单号测试

缺少订单号现在断言：

```text
order_query_error_kind = missing_order_id
order_query_error_action = ask_user_for_order_id
order_query_retryable = False
```

这保护了追问状态。

### 3. 分类函数测试

测试覆盖：

```text
ORDER_NOT_FOUND
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TOOL_RESULT_VALIDATION_FAILED
普通 RuntimeError
```

这些是工具节点最常见的失败类型。

### 4. 订单不存在节点测试

测试断言：

```text
ORDER_NOT_FOUND
-> not_found
-> ask_user_to_check_order_id
-> retryable=False
```

这保护“用户应检查订单号”的语义。

### 5. 超时节点测试

测试断言：

```text
TOOL_TIMEOUT
-> timeout
-> retry_later
-> retryable=True
```

这为后续 retry 策略打基础。

### 6. 结果校验失败安全文案测试

测试故意让工具抛：

```text
TOOL_RESULT_VALIDATION_FAILED
message="工具返回结果校验失败：internal field mismatch。"
```

然后断言用户回答不包含：

```text
internal field mismatch
```

这保护内部细节不泄露。

### 7. 未知异常安全兜底测试

测试故意让工具抛：

```text
RuntimeError("database password leaked in stack trace")
```

然后断言用户回答不包含：

```text
database password
```

这保护未知异常不泄露敏感信息。

---

## 八、错误分类表

| 场景 | code | kind | action | retryable |
| --- | --- | --- | --- | --- |
| 用户没给订单号 | `ORDER_ID_REQUIRED` | `missing_order_id` | `ask_user_for_order_id` | `False` |
| 订单号参数校验失败 | `TOOL_ARGUMENTS_VALIDATION_FAILED` | `argument_validation` | `ask_user_to_check_order_id` | `False` |
| 订单不存在 | `ORDER_NOT_FOUND` | `not_found` | `ask_user_to_check_order_id` | `False` |
| Java 服务超时 | `TOOL_TIMEOUT` | `timeout` | `retry_later` | `True` |
| Java 服务不可用或 5xx | `TOOL_UPSTREAM_ERROR` | `upstream_error` | `retry_later` | `True` |
| 工具结果结构不符合契约 | `TOOL_RESULT_VALIDATION_FAILED` | `result_validation` | `investigate_system` | `False` |
| 通用工具调用失败 | `TOOL_CALL_FAILED` | `tool_error` | `retry_later` | `True` |
| 未知 Python 异常 | `TOOL_CALL_FAILED` | `unknown_error` | `retry_later` | `True` |

这张表要重点理解。

它以后会影响：

```text
是否 retry
是否让用户补充信息
是否提示人工客服
是否需要开发排查
是否进入监控告警
```

---

## 九、常见误区

### 误区 1：错误码越多越好

不对。

错误码要表达稳定契约。

如果错误码太碎，调用方和监控会很难维护。

更好的方式是：

```text
保留稳定 code
增加 kind/action/retryable 做更高层表达
```

### 误区 2：所有工具失败都可以 retry

不对。

用户没给订单号，retry 没用。

订单号格式错误，retry 没用。

订单不存在，retry 通常没用。

只有超时、上游服务异常这类临时问题更适合 retry。

### 误区 3：只要是 `AppException` 就能原样给用户

不对。

`AppException` 比普通异常结构化，但 message 是否适合用户，还要看错误类型。

结果校验失败这类内部错误，应该返回更安全的用户文案。

### 误区 4：未知异常只要日志记录了就行

不够。

未知异常还要保证：

```text
用户回答安全
state 可判断
测试能覆盖
后续监控能统计
```

### 误区 5：错误处理就是写更多 `except`

不对。

错误处理的核心不是 `except` 数量。

核心是：

```text
分类清楚
动作清楚
边界清楚
信息暴露清楚
测试清楚
```

---

## 十、和后续课程的关系

本节新增的字段会在后面继续用。

### 1. 和 retry 的关系

后面学习 retry 时，可以根据：

```text
order_query_retryable
```

判断是否尝试重试。

不是所有失败都重试。

### 2. 和 rate limit 的关系

如果很多失败都是：

```text
kind=upstream_error
```

说明上游压力或稳定性有问题。

后续可以结合 rate limit 减少打爆服务的风险。

### 3. 和 circuit breaker 的关系

如果短时间大量：

```text
kind=timeout
kind=upstream_error
```

系统可以考虑熔断，暂时不再请求上游，直接返回降级文案。

### 4. 和评测的关系

评测可以检查：

```text
订单不存在时是否 not_found
服务超时时是否 retryable=True
结果校验失败时是否 investigate_system
未知异常是否隐藏内部细节
```

这比只检查 `final_answer` 更可靠。

### 5. 和可观测性的关系

日志和 trace 可以记录：

```text
code
kind
action
retryable
status_code
```

以后排查问题时，可以很快知道：

```text
是用户输入问题多，还是上游服务问题多？
```

---

## 十一、本节练习

### 练习 1：解释 `code` 和 `kind` 的区别

题目：为什么有了 `code`，还要加 `kind`？

参考答案：

`code` 是具体错误码，适合接口契约、日志搜索和测试断言。`kind` 是更抽象的错误类型，适合统计、评测和流程策略。多个不同 `code` 未来可能归为同一个 `kind`，例如多种上游服务错误都可以归为 `upstream_error`。

### 练习 2：解释 `action` 的意义

题目：`action=retry_later` 是不是代表当前代码已经自动 retry 了？

参考答案：

不是。`action` 只是建议处理动作，表示这个错误适合稍后重试。当前代码只是把动作写进 state，真正自动 retry 会在后续课程单独实现。

### 练习 3：判断哪些错误可重试

题目：下面哪些错误适合 `retryable=True`？

```text
ORDER_ID_REQUIRED
ORDER_NOT_FOUND
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TOOL_RESULT_VALIDATION_FAILED
```

参考答案：

`TOOL_TIMEOUT` 和 `TOOL_UPSTREAM_ERROR` 适合 `retryable=True`。缺订单号、订单不存在、结果校验失败都不适合简单重试。

### 练习 4：解释结果校验失败为什么是系统问题

题目：为什么 `TOOL_RESULT_VALIDATION_FAILED` 的 action 是 `investigate_system`？

参考答案：

因为这说明 Java 服务返回的数据和 AI 服务的 `QueryOrderResult` 契约不一致，可能是字段缺失、类型错误、枚举值不匹配或接口契约变化。这不是用户能通过补充信息解决的问题，需要开发者排查系统边界。

### 练习 5：解释未知异常为什么要隐藏原始信息

题目：为什么 `RuntimeError("database password leaked in stack trace")` 不能把原始 message 放进 `final_answer`？

参考答案：

未知异常可能包含内部路径、数据库信息、配置名、字段名或敏感内容。用户只应该看到通用安全提示，原始错误细节应该留在日志里供开发排查，不能直接暴露在用户回答中。

### 练习 6：设计一个新的错误映射

题目：如果以后 Java 订单服务新增错误码 `ORDER_SERVICE_RATE_LIMITED`，你会把它映射成什么？

参考答案：

可以映射为 `kind=upstream_error` 或未来新增 `rate_limited`。如果暂时不新增 kind，可以设置 `action=retry_later`，`retryable=True`，并在后续 rate limit 课程中单独细化。

### 练习 7：为什么本节不用真实 Java 服务测试

题目：为什么本节测试使用 fake executor 抛异常，而不是启动 Java 服务模拟错误？

参考答案：

因为本节测试目标是验证 LangGraph 节点对不同工具失败的处理逻辑。fake executor 能稳定制造各种异常，不依赖 Docker、网络和 Java 服务状态。真实服务链路可以放到集成测试或 smoke test 中验证。

---

## 十二、自测题

### 自测 1：`TicketOrderQueryFailure` 解决了什么问题？

答案：它把工具失败从简单的 `code/message` 升级成结构化失败策略，包含错误码、错误类型、处理动作、安全消息、是否可重试和状态码。

### 自测 2：`ORDER_NOT_FOUND` 的 kind、action、retryable 分别是什么？

答案：`kind=not_found`，`action=ask_user_to_check_order_id`，`retryable=False`。

### 自测 3：`TOOL_TIMEOUT` 为什么是 `retryable=True`？

答案：超时通常是临时性问题，稍后重试可能成功。当前订单查询是只读工具，重试风险较低。

### 自测 4：`TOOL_RESULT_VALIDATION_FAILED` 为什么不直接用原始 message？

答案：结果校验失败通常包含内部字段或 schema 细节，不适合直接给用户看。应该返回安全文案，并让系统排查。

### 自测 5：缺订单号时为什么 `order_query_status` 仍然是 `missing_order_id`，不是 `failed`？

答案：缺订单号表示信息不足，需要追问用户，并不代表工具执行失败。用 `missing_order_id` 能更准确表达多轮对话状态。

### 自测 6：为什么 `action` 和 `retryable` 要同时存在？

答案：`action` 表示建议怎么处理，`retryable` 专门表示是否适合重试。两者有关联但不完全等价。比如 `investigate_system` 通常不可重试，`retry_later` 通常可重试。

### 自测 7：为什么成功状态也写入空错误字段？

答案：这样 state 结构更稳定。调用方可以明确知道本次成功没有错误类型、错误动作、错误信息和错误状态码，而不是靠字段是否存在来猜。

### 自测 8：本节为什么没有修改 `fake_order_tool.py`？

答案：第 19 节已经让工具层负责调用 Java 服务、字段映射和结果校验。本节重点是 LangGraph 工具节点如何理解并处理工具抛出的异常，所以主要修改 `ticket_agent.py`。

### 自测 9：本节为什么对未知异常设置 `code=TOOL_CALL_FAILED`？

答案：未知异常没有稳定业务错误码。统一收敛成 `TOOL_CALL_FAILED` 可以保护用户回答安全，并给 Agent 一个稳定的失败契约。

### 自测 10：本节为后续哪些内容打基础？

答案：为 retry、rate limit、circuit breaker、日志监控、评测统计、错误报告、人工兜底和后续工具节点安全策略打基础。

---

## 十三、面试表达

如果面试官问：你们的 Agent 工具调用失败怎么处理？

可以这样回答：

```text
我们没有把所有工具异常都粗暴返回成“工具调用失败”。
以订单查询工具节点为例，我们先让底层 JavaOrderClient 和 query_order 工具抛出项目统一的 AppException，
然后在 LangGraph 节点里通过 classify_ticket_order_query_failure 把异常转换成 Agent 能理解的失败策略对象。

这个对象包含 code、kind、action、message、retryable、status_code。
比如 ORDER_NOT_FOUND 会映射成 not_found，action 是让用户检查订单号，不可重试；
TOOL_TIMEOUT 会映射成 timeout，action 是稍后重试，可重试；
TOOL_UPSTREAM_ERROR 会映射成 upstream_error，也可重试；
TOOL_RESULT_VALIDATION_FAILED 会映射成 result_validation，action 是系统排查，并且返回安全文案，不暴露内部字段细节；
未知异常会统一收敛成 TOOL_CALL_FAILED，避免把内部堆栈或敏感信息暴露给用户。

这些字段会写回 LangGraph state，也会进入节点日志。
这样后续做 retry、监控、评测和人工兜底时，不需要解析自然语言文案，而是直接基于结构化字段做决策。
自动化测试里我们用 fake executor 稳定制造不同错误，避免依赖真实 Java 服务和网络状态。
```

这段表达能体现：

```text
异常分层意识
用户输入错误和系统错误的区分
安全信息暴露边界
可重试判断
LangGraph state 设计
测试可控性
生产化演进思路
```

---

## 十四、本节小结

本节完成了订单查询工具节点的错误处理升级。

第 19 节解决的是：

```text
query_order 节点能不能真的调用订单查询工具？
```

第 20 节解决的是：

```text
订单查询工具失败时，Agent 能不能知道失败属于哪一类、下一步该怎么处理？
```

现在工具节点失败状态已经包含：

```text
code
kind
action
message
retryable
status_code
```

这让工具失败从一句模糊文案，变成了可测试、可统计、可扩展、可观测的结构化信号。

你要重点掌握的是：

```text
工具错误处理不是简单捕获异常。
它是把底层异常转换成 Agent 能理解、用户能接受、系统能继续演进的失败策略。
```

下一节进入：

```text
阶段 6 第 21 节：工具权限和写操作安全回归
```

我们会在只读 `query_order` 工具已经可控的基础上，回到更危险的写操作边界，重点复习和加固创建工单这类写操作为什么必须有人类确认、权限边界和安全测试。
