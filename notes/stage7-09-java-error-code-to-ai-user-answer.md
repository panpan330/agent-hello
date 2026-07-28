# 阶段 7 第 9 节：Java 错误码到 AI 用户回答

## 本节定位

上一节我们把 Java internal API 的调用边界补强了：

```text
X-Caller 可配置
X-Tenant-Id 必传
trace_id / caller / user_id / tenant_id 做基础格式校验
Java 服务在进入业务逻辑前先校验内部调用身份
```

这解决的是：

```text
Python AI 服务有没有资格调用 Java？
这次调用代表哪个真实用户？
这次调用属于哪个租户？
```

但还有一个非常重要的问题：

```text
Java 服务拒绝请求或出错以后，AI 最终应该怎么告诉用户？
```

Java 业务服务返回的内容通常是机器友好的：

```json
{
  "success": false,
  "code": "ORDER_ACCESS_DENIED",
  "message": "当前用户无权查看或操作该订单。",
  "data": null,
  "trace_id": "manual-stage7-09-001"
}
```

这里的 `code` 很适合程序判断，但不一定适合直接给用户看。

本节要学的不是“怎么写一个 if else”，而是 AI 应用里非常关键的一层：

```text
错误语义翻译层
```

也就是：

```text
Java 机器错误码
-> Python AI 服务内部异常
-> Agent/接口层可控状态
-> 用户能理解、又不泄露内部细节的中文回答
```

## 本节学习目标

学完本节，你应该能讲清楚：

```text
1. 为什么 Java 错误码不能全部直接展示给用户。
2. 为什么 AI 不能自由发挥错误原因。
3. 哪些错误属于用户可理解的业务错误。
4. 哪些错误属于内部系统错误，应该隐藏细节。
5. HTTP 状态码、业务错误码、用户提示语分别负责什么。
6. Python AI 服务为什么要有自己的错误映射层。
7. 为什么错误映射要先于大模型，而不是交给模型随机总结。
8. 如何用测试保证错误码映射稳定。
```

本节代码目标：

```text
新增 app/services/java_error_mapping.py
让 JavaOrderClient 使用统一错误映射
让 JavaTicketClient 使用统一错误映射
补充单元测试
```

本节不提前学习：

```text
完整 Spring Security 登录体系
前端错误提示组件
多语言国际化
复杂客服话术策略
真实线上告警平台
Java/Python 全链路真实集成改造
```

这些后面可以学。本节只把“Java 错误码怎么安全变成 AI 用户回答”这个核心问题讲透。

## 基础知识铺垫

### 1. 错误码是什么

错误码是程序之间沟通失败原因的一种稳定标识。

比如：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
INTERNAL_AUTH_FAILED
IDEMPOTENCY_KEY_CONFLICT
JAVA_SERVICE_ERROR
```

它们比纯文本更稳定。

原因是：

```text
文本容易变。
错误码不应该随便变。
程序可以根据错误码做分支。
日志、监控、测试、告警都可以围绕错误码建立规则。
```

举例：

```text
订单不存在，请确认订单号是否正确。
没有找到订单，请检查订单号。
该订单不存在。
```

这三句话表达的意思差不多，但文本不一样。如果程序靠文本判断，会很脆弱。

但错误码可以稳定成：

```text
ORDER_NOT_FOUND
```

所以在后端工程里，错误码是“机器判断的锚点”。

### 2. 错误码不是用户提示语

这是本节最重要的基础概念之一。

错误码是给程序看的，用户提示语是给人看的。

比如：

```text
INTERNAL_AUTH_FAILED
```

从程序角度看，它很有用：

```text
Python 调 Java 时 internal token 不对
X-Caller 不符合预期
缺少必要 internal header
Java 拒绝了内部调用
```

但如果直接告诉用户：

```text
内部服务鉴权失败。
```

用户会困惑：

```text
什么是内部服务？
什么是鉴权？
是不是我的账号被封了？
是不是系统安全出问题了？
```

更严重的是，这可能泄露内部架构：

```text
存在 internal API
服务之间靠 token 调用
调用方身份校验失败
```

所以用户不应该看到这类内部细节。

用户更适合看到：

```text
订单查询服务暂时不可用，请稍后重试。
```

这句话没有暴露内部实现，但能告诉用户当前该怎么做。

### 3. HTTP 状态码、业务错误码、用户提示语的区别

真实项目里经常会同时出现三层错误信息：

```text
HTTP 状态码
业务错误码
用户提示语
```

它们不是一回事。

HTTP 状态码回答的是：

```text
这次 HTTP 请求在协议层大概属于哪类结果？
```

比如：

```text
200 OK
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Entity
429 Too Many Requests
500 Internal Server Error
502 Bad Gateway
504 Gateway Timeout
```

业务错误码回答的是：

```text
业务上到底发生了什么？
```

比如：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
ORDER_NOT_SUPPORT_TICKET
IDEMPOTENCY_KEY_CONFLICT
```

用户提示语回答的是：

```text
用户现在能理解什么？下一步该怎么做？
```

比如：

```text
订单不存在，请确认订单号是否正确。
当前账号无权查看或操作该订单。
当前订单暂不支持创建这类工单，如需帮助可以联系人工客服。
本次提交和已确认的工单请求不一致，请重新确认后再提交。
```

三者关系可以这样理解：

```text
HTTP 状态码：给 HTTP 客户端和网关看的粗分类
业务错误码：给程序分支、日志、监控、测试看的稳定标识
用户提示语：给最终用户看的安全解释
```

### 4. 为什么 AI 不能自由解释错误

你可能会想：

```text
既然最后是 AI 回答用户，那能不能把 Java 错误直接丢给模型，让模型自己总结？
```

不应该。

原因有四个。

第一，模型可能编造原因。

Java 只返回：

```text
ORDER_ACCESS_DENIED
```

模型可能说：

```text
您的账号没有完成实名认证，所以不能查看该订单。
```

但 Java 并没有说是实名认证问题。这就是模型编造。

第二，模型可能泄露内部信息。

如果 prompt 里包含：

```text
INTERNAL_AUTH_FAILED: internal token mismatch
```

模型可能回答：

```text
系统内部 token 校验失败。
```

这不适合给普通用户。

第三，模型输出不稳定。

同一个错误码，今天可能说：

```text
订单不存在。
```

明天可能说：

```text
系统找不到订单记录，可能数据同步失败。
```

但业务错误提示应该稳定。

第四，错误处理属于后端安全边界。

后端必须控制：

```text
哪些信息可以对用户说
哪些信息只能写日志
哪些信息只能给运维和开发看
```

不能把这个权力完全交给模型。

所以正确做法是：

```text
Java 错误码先由 Python 后端映射成安全语义。
模型最多基于安全语义组织语言。
模型不能看到不该暴露的内部错误详情。
```

### 5. 用户可见错误和内部错误

AI 应用里，错误大体可以分成两类。

第一类是用户可见的业务错误。

比如：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
ORDER_NOT_SUPPORT_TICKET
TICKET_ALREADY_EXISTS
IDEMPOTENCY_KEY_CONFLICT
TOOL_RATE_LIMITED
```

这些错误用户可以理解，而且用户知道后能采取动作。

例如：

```text
订单不存在 -> 检查订单号
无权查看 -> 换正确账号或联系人工
订单不支持创建工单 -> 联系人工或查看规则
重复工单 -> 不要重复提交
请求过于频繁 -> 稍后再试
```

第二类是内部系统错误。

比如：

```text
INTERNAL_AUTH_FAILED
JAVA_SERVICE_ERROR
IDEMPOTENCY_KEY_REQUIRED
IDEMPOTENCY_KEY_INVALID
TOOL_RESULT_VALIDATION_FAILED
```

这些错误往往说明：

```text
Python 和 Java 之间的契约出问题了
服务配置有问题
服务内部异常
返回结构不符合约定
```

这类错误不应该把细节告诉用户。

用户只需要知道：

```text
服务暂时不可用
请稍后重试
必要时联系人工客服
```

开发和运维则需要通过日志里的：

```text
trace_id
upstream code
HTTP status
调用路径
```

去排查。

### 6. 错误映射层应该放在哪里

在我们的项目里，Java 错误码进入 Python 的位置是：

```text
JavaOrderClient
JavaTicketClient
```

它们是 HTTP adapter，也就是 Python 调 Java 的适配层。

所以错误映射最适合放在：

```text
app/services/java_error_mapping.py
```

原因是：

```text
1. 它离 Java 响应最近，最容易解析 Java 返回体。
2. 它不污染 Agent 流程，Agent 只接收 AppException。
3. 它能被订单查询和工单创建复用。
4. 它能独立测试。
5. 后面 Java 错误码增加时，只需要集中维护。
```

不适合放在 prompt 里。

因为 prompt 是给模型的，不是稳定工程边界。

也不适合散落在多个 client 的 if/else 里。

因为后面错误码越来越多，散落会导致：

```text
同一个错误在不同工具里提示不一致
某些错误忘记隐藏
测试覆盖困难
维护成本升高
```

### 7. 为什么不用 Java 的 message 原样展示

Java 返回体里通常有 `message`：

```json
{
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在，请确认订单号是否正确。"
}
```

看起来可以直接展示。

但我们本节没有直接使用 Java 的 message，而是在 Python 映射层里维护用户安全提示语。

原因是：

```text
Java message 不一定永远是面向最终用户的。
Java message 可能变成面向开发排查的内部描述。
Java message 可能包含数据库、接口、鉴权、配置等内部信息。
Python AI 服务才是最终面向用户的服务，需要控制最终话术。
```

举例：

Java 某次为了排查问题返回：

```json
{
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在，SQL: select * from orders where tenant_id = ..."
}
```

用户不应该看到 SQL。

所以 Python 侧固定映射：

```text
ORDER_NOT_FOUND -> 订单不存在，请确认订单号是否正确。
```

这样即使 Java message 变了，用户提示也不会泄露内部信息。

### 8. 错误映射和日志的关系

用户提示语要克制，但日志不能太少。

给用户：

```text
订单查询服务暂时不可用，请稍后重试。
```

给日志：

```text
trace_id=xxx
operation=order_query
upstream_code=INTERNAL_AUTH_FAILED
status_code=401
path=/internal/orders/A1001
```

本节代码主要完成用户侧安全映射，没有把日志字段继续扩展得很复杂。

后面第 10 节会学：

```text
trace_id 串联 Python + Java
```

到时候会更系统地讲怎么用日志把 Python、Java、MySQL/Redis 串起来排查。

## 本节主题系统讲解

### 1. 本节之前的链路

之前 Python 调 Java 的错误处理大概是：

```text
Java 返回 404
-> Python 判断 status_code == 404
-> 抛 ORDER_NOT_FOUND

Java 返回 500
-> Python 判断 status_code >= 500
-> 抛 TOOL_UPSTREAM_ERROR

Java 返回其他非预期状态
-> Python 抛 TOOL_UPSTREAM_ERROR 或 TICKET_UPSTREAM_REJECTED
```

这个做法能跑，但有明显问题。

第一，只看 HTTP 状态码不够。

比如 Java 可能返回：

```text
403 ORDER_ACCESS_DENIED
401 INTERNAL_AUTH_FAILED
409 IDEMPOTENCY_KEY_CONFLICT
409 ORDER_NOT_SUPPORT_TICKET
422 TICKET_REQUEST_INVALID
```

这些都不是 500，但含义完全不同。

第二，订单查询和工单创建各自写判断，后面会重复。

第三，没有明确区分：

```text
用户可见错误
内部隐藏错误
```

第四，不利于测试。

如果错误映射散落在多个 client 里，后面加一个错误码，就要到处找。

### 2. 本节之后的链路

本节之后，链路变成：

```text
Java 返回非成功响应
-> Python 提取 Java error code
-> java_error_mapping.py 判断这个 code 属于哪类
-> 生成安全 AppException
-> Agent 或接口层用 AppException.message 给用户回答
```

也就是：

```text
Java code 不等于最终用户话术。
Java message 不等于最终用户话术。
Python 映射层负责最终安全语义。
```

### 3. 新增的映射模块

新增文件：

```text
projects/ai-service/app/services/java_error_mapping.py
```

它提供三个核心东西。

第一个是 `JavaErrorMapping`：

```python
@dataclass(frozen=True)
class JavaErrorMapping:
    code: str
    message: str
    status_code: int
```

它描述一个 Java 错误码映射成 Python `AppException` 后应该是什么样：

```text
code       -> Python 对外暴露的安全错误码
message    -> 用户可见的安全提示
status_code -> Python 接口层返回的 HTTP 状态码
```

第二个是 `USER_SAFE_JAVA_ERROR_MAPPINGS`。

这里放的是用户可以理解的业务错误。

例如：

```python
"ORDER_NOT_FOUND": JavaErrorMapping(
    code="ORDER_NOT_FOUND",
    message="订单不存在，请确认订单号是否正确。",
    status_code=404,
)
```

意思是：

```text
Java 返回 ORDER_NOT_FOUND 时，
Python 可以继续使用 ORDER_NOT_FOUND 这个错误码，
但 message 使用 Python 本地维护的安全提示。
```

第三个是 `build_java_error_app_exception()`。

它负责真正把 Java 响应转成 `AppException`。

核心判断顺序是：

```text
1. 如果 Java code 是用户安全业务错误，按映射表返回。
2. 如果 Java code 是 INTERNAL_AUTH_FAILED / JAVA_SERVICE_ERROR，统一隐藏成 TOOL_UPSTREAM_ERROR。
3. 如果 Java code 是 IDEMPOTENCY_KEY_REQUIRED / IDEMPOTENCY_KEY_INVALID，说明 Python/Java 写接口契约异常，隐藏成 TICKET_UPSTREAM_REJECTED。
4. 如果 HTTP 状态码是 5xx，但没有可识别 code，返回服务暂时不可用。
5. 其他未知错误走调用方提供的 fallback。
```

这个顺序很重要。

因为：

```text
已知业务错误要尽量准确。
内部系统错误要隐藏。
未知错误要保守。
```

### 4. 为什么 `INTERNAL_AUTH_FAILED` 被映射成 `TOOL_UPSTREAM_ERROR`

Java 返回：

```text
INTERNAL_AUTH_FAILED
```

从开发角度看，含义是：

```text
Python 调 Java 的内部鉴权失败。
```

但用户不应该看到：

```text
内部服务鉴权失败。
```

所以 Python 映射成：

```text
TOOL_UPSTREAM_ERROR
订单查询服务暂时不可用，请稍后重试。
```

或者在工单创建场景中：

```text
TOOL_UPSTREAM_ERROR
工单业务服务暂时不可用，请稍后重试。
```

这里的关键点是：

```text
不是所有 Java code 都要保留给用户。
有些 Java code 只应该留在日志、监控和开发排查里。
```

### 5. 为什么 `IDEMPOTENCY_KEY_CONFLICT` 可以告诉用户

`IDEMPOTENCY_KEY_CONFLICT` 表示：

```text
同一个幂等键被用于不同请求参数。
```

这个听起来比较技术，但在用户场景里可以翻译成：

```text
本次提交和已确认的工单请求不一致，请重新确认后再提交。
```

这句话能告诉用户下一步：

```text
重新确认
重新提交
```

但不会讲太多技术细节。

所以我们保留错误码：

```text
IDEMPOTENCY_KEY_CONFLICT
```

但改写 message：

```text
本次提交和已确认的工单请求不一致，请重新确认后再提交。
```

### 6. 为什么 `IDEMPOTENCY_KEY_REQUIRED` 和 `IDEMPOTENCY_KEY_INVALID` 不直接告诉用户

这两个错误说明：

```text
Python 调 Java 写接口时没有带幂等键
或者幂等键格式不符合 Java 约定
```

正常情况下，用户不会直接构造这个请求。

幂等键应该由后端生成和传递。

所以如果出现：

```text
IDEMPOTENCY_KEY_REQUIRED
IDEMPOTENCY_KEY_INVALID
```

更像是：

```text
Python/Java 契约对接错误
```

不应该告诉用户：

```text
你缺少幂等键。
```

用户根本不知道幂等键是什么，也不该由用户修。

所以本节映射成：

```text
TICKET_UPSTREAM_REJECTED
工单业务服务拒绝了已经校验过的请求，请联系管理员排查接口契约。
```

这句话面向的是当前学习项目的调试场景。

如果是正式产品，用户侧可能更克制：

```text
工单提交暂时失败，请稍后重试或联系人工客服。
```

### 7. 订单查询和工单创建为什么共享同一个映射层

订单查询和工单创建是两个不同工具：

```text
query_order
create_ticket
```

但它们都调用 Java 业务服务。

很多错误码是共享的：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
INTERNAL_AUTH_FAILED
JAVA_SERVICE_ERROR
TOOL_RATE_LIMITED
```

如果每个 client 自己写一份映射，就会出现风险：

```text
JavaOrderClient 里 ORDER_ACCESS_DENIED 提示为“无权查看订单”
JavaTicketClient 里 ORDER_ACCESS_DENIED 提示为“权限不足”
另一个地方又提示为“您没有权限”
```

看似差异小，但工程上很危险。

因为后续：

```text
测试不好统一
产品话术不好统一
错误语义不好统计
告警分类不好维护
```

所以共享映射层是更稳的做法。

### 8. Agent 最终回答应该依赖安全 message

我们的 `ticket_agent.py` 里已经有一层工具失败分类：

```text
ORDER_NOT_FOUND -> not_found -> ask_user_to_check_order_id
TOOL_TIMEOUT -> timeout -> retry_later
TOOL_UPSTREAM_ERROR -> upstream_error -> retry_later
TOOL_RESULT_VALIDATION_FAILED -> result_validation -> investigate_system
```

这层分类仍然有价值。

但它应该接收的是已经安全处理过的 `AppException`。

也就是：

```text
Java 原始错误响应
-> Java client 映射成安全 AppException
-> Agent 根据 AppException 决定 final_answer / retryable / action
```

Agent 不应该直接处理 Java 原始响应。

因为 Agent 层的职责是：

```text
根据工具执行结果决定对话流程
```

不是：

```text
解析 Java HTTP 响应体
判断哪些 Java message 可以展示
隐藏 internal auth 细节
```

这就是分层。

## 本节代码讲解

### 1. `JavaErrorMapping`

新增：

```python
@dataclass(frozen=True)
class JavaErrorMapping:
    code: str
    message: str
    status_code: int
```

这段代码不是为了“少写几个字”，而是为了让映射表更清晰。

如果不用它，可能会写成：

```python
"ORDER_NOT_FOUND": ("ORDER_NOT_FOUND", "订单不存在，请确认订单号是否正确。", 404)
```

这种 tuple 看起来短，但阅读时不清楚每个位置代表什么。

使用 dataclass 后：

```python
JavaErrorMapping(
    code="ORDER_NOT_FOUND",
    message="订单不存在，请确认订单号是否正确。",
    status_code=404,
)
```

每个字段的含义都很明确。

`frozen=True` 表示这个对象创建后不应该再被修改。

这适合错误码映射表，因为映射表应该是稳定配置，不应该在运行中被业务逻辑随便改。

### 2. `USER_SAFE_JAVA_ERROR_MAPPINGS`

这个映射表只放用户可理解的错误。

例如：

```python
"ORDER_ACCESS_DENIED": JavaErrorMapping(
    code="ORDER_ACCESS_DENIED",
    message="当前账号无权查看或操作该订单。",
    status_code=403,
)
```

注意这里没有直接使用 Java message。

Python 本地维护 message 的好处是：

```text
用户话术稳定。
不会因为 Java 为了排查问题改 message 而泄露内部细节。
以后可以由 AI 服务统一做多语言、语气、渠道适配。
```

### 3. `extract_java_error_code()`

新增：

```python
def extract_java_error_code(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None

    if not isinstance(payload, dict):
        return None

    code = payload.get("code")
    if isinstance(code, str) and code.strip():
        return code.strip()
    return None
```

这段代码做一件非常基础但重要的事：

```text
从 Java 响应体里提取 code。
```

它没有假设 Java 一定返回合法 JSON。

如果 Java 返回：

```text
not-json
```

它返回 `None`。

如果 Java 返回：

```json
["not", "object"]
```

它也返回 `None`。

如果 Java 返回：

```json
{"code": ""}
```

它还是返回 `None`。

这种写法叫做：

```text
防御式解析
```

因为上游服务返回错误时，本身就可能不稳定。

### 4. `build_java_error_app_exception()`

这是本节核心函数。

它的参数包括：

```python
response: httpx.Response
operation: JavaOperation
fallback_code: str
fallback_message: str
fallback_status_code: int
```

其中 `operation` 用来区分场景：

```text
order_query
ticket_creation
```

同样是 `TOOL_UPSTREAM_ERROR`，订单查询和工单创建应该给不同提示：

```text
订单查询服务暂时不可用，请稍后重试。
工单业务服务暂时不可用，请稍后重试。
```

`fallback_*` 是兜底信息。

意思是：

```text
如果 Java 返回的错误码未知，或者响应体无法解析，就使用调用方给出的默认处理。
```

这让 `JavaOrderClient` 和 `JavaTicketClient` 可以共享大部分规则，同时保留自己业务场景的兜底提示。

### 5. `JavaOrderClient` 的变化

之前订单查询里有几段判断：

```python
if response.status_code == 404:
    ...

if response.status_code >= 500:
    ...

if response.status_code != 200:
    ...
```

现在改成：

```python
if response.status_code != 200:
    raise build_java_error_app_exception(
        response,
        operation="order_query",
        fallback_code="TOOL_UPSTREAM_ERROR",
        fallback_message="订单查询服务返回了无法处理的状态，请稍后重试。",
        fallback_status_code=502,
    )
```

这不是简单减少代码。

真正变化是：

```text
订单查询 client 不再自己猜每个 Java 错误码怎么处理。
它把非成功响应交给统一错误映射层。
```

如果 Java 返回：

```text
ORDER_NOT_FOUND
```

映射层返回：

```text
ORDER_NOT_FOUND
订单不存在，请确认订单号是否正确。
404
```

如果 Java 返回：

```text
ORDER_ACCESS_DENIED
```

映射层返回：

```text
ORDER_ACCESS_DENIED
当前账号无权查看或操作该订单。
403
```

如果 Java 返回：

```text
INTERNAL_AUTH_FAILED
```

映射层返回：

```text
TOOL_UPSTREAM_ERROR
订单查询服务暂时不可用，请稍后重试。
502
```

### 6. `JavaTicketClient` 的变化

工单创建之前逻辑是：

```python
if response.status_code >= 500:
    TOOL_UPSTREAM_ERROR

if response.status_code != 201:
    TICKET_UPSTREAM_REJECTED
```

现在改成：

```python
if response.status_code != 201:
    raise build_java_error_app_exception(
        response,
        operation="ticket_creation",
        fallback_code="TICKET_UPSTREAM_REJECTED",
        fallback_message="工单业务服务拒绝了已经校验过的请求，请联系管理员排查接口契约。",
        fallback_status_code=502,
    )
```

这样工单创建能识别更多业务错误。

例如：

```text
ORDER_NOT_SUPPORT_TICKET
-> 当前订单暂不支持创建这类工单，如需帮助可以联系人工客服。
```

```text
IDEMPOTENCY_KEY_CONFLICT
-> 本次提交和已确认的工单请求不一致，请重新确认后再提交。
```

```text
INTERNAL_AUTH_FAILED
-> 工单业务服务暂时不可用，请稍后重试。
```

### 7. 测试重点

本节新增和修改了三类测试。

第一类：直接测映射层。

```text
test_java_error_mapping.py
```

它验证：

```text
能从 Java 统一响应体里提取 code
ORDER_NOT_FOUND 使用 Python 本地安全 message
INTERNAL_AUTH_FAILED 不暴露“鉴权”
IDEMPOTENCY_KEY_REQUIRED 被当成契约问题隐藏
未知错误走 fallback
```

第二类：测订单查询 client。

```text
test_java_order_client.py
```

新增验证：

```text
ORDER_ACCESS_DENIED -> 当前账号无权查看或操作该订单。
INTERNAL_AUTH_FAILED -> 订单查询服务暂时不可用，请稍后重试。
```

第三类：测工单创建 client。

```text
test_java_ticket_client.py
```

新增验证：

```text
ORDER_NOT_SUPPORT_TICKET -> 当前订单暂不支持创建这类工单
IDEMPOTENCY_KEY_CONFLICT -> 重新确认后再提交
```

这些测试不是为了追求数量，而是为了锁住本节最重要的安全边界：

```text
用户能知道该知道的。
用户看不到不该看的。
```

## 常见误区

### 误区 1：HTTP 403 就一定直接告诉用户“无权限”

不一定。

如果 Java 返回：

```text
403 ORDER_ACCESS_DENIED
```

可以告诉用户：

```text
当前账号无权查看或操作该订单。
```

但如果某个系统把 internal token 校验失败也返回成 403，那就不能告诉用户“你的账号无权限”。

所以不能只看 HTTP 状态码。

要结合：

```text
HTTP status
业务 code
操作场景
```

一起判断。

### 误区 2：Java message 已经是中文，所以直接展示

中文不等于安全。

Java message 可能是：

```text
内部服务鉴权失败。
```

也可能是：

```text
orders 表中 tenant_id 不匹配。
```

这些都是中文，但不适合给用户。

### 误区 3：让模型总结错误更灵活

错误处理不应该追求“灵活”。

它应该追求：

```text
稳定
可控
可测试
不泄露
能指导用户下一步
```

模型可以润色安全结果，但不能决定核心错误语义。

### 误区 4：所有 Java 错误码都应该原样保留

不是。

有些错误码可以保留：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
```

有些错误码应该隐藏或转换：

```text
INTERNAL_AUTH_FAILED -> TOOL_UPSTREAM_ERROR
JAVA_SERVICE_ERROR -> TOOL_UPSTREAM_ERROR
IDEMPOTENCY_KEY_REQUIRED -> TICKET_UPSTREAM_REJECTED
```

判断标准是：

```text
这个错误码是否适合出现在用户侧或外部 API 响应里。
```

### 误区 5：错误提示越详细越好

不是。

对用户来说，错误提示应该：

```text
足够理解
足够行动
不过度暴露
```

例如：

```text
当前账号无权查看或操作该订单。
```

这已经足够。

没必要说：

```text
当前 user_id 与 orders.customer_id 不匹配，Java service 返回 403。
```

后一句只适合日志，不适合用户。

## 本节练习

### 练习 1：判断哪些错误可以直接面向用户

下面错误码哪些可以作为用户可见业务错误？哪些应该隐藏成系统暂不可用？

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
INTERNAL_AUTH_FAILED
JAVA_SERVICE_ERROR
ORDER_NOT_SUPPORT_TICKET
IDEMPOTENCY_KEY_REQUIRED
IDEMPOTENCY_KEY_CONFLICT
```

参考答案：

```text
可以面向用户：
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
ORDER_NOT_SUPPORT_TICKET
IDEMPOTENCY_KEY_CONFLICT

应该隐藏或转换：
INTERNAL_AUTH_FAILED
JAVA_SERVICE_ERROR
IDEMPOTENCY_KEY_REQUIRED
```

原因：

```text
前者用户能理解，也能采取下一步动作。
后者更多是服务配置、内部调用、接口契约或系统异常问题，不应该让用户看到内部细节。
```

### 练习 2：设计 `ORDER_ACCESS_DENIED` 的用户提示

Java 返回：

```json
{
  "code": "ORDER_ACCESS_DENIED",
  "message": "当前用户无权查看或操作该订单。"
}
```

你会怎么提示用户？

参考答案：

```text
当前账号无权查看或操作该订单。
```

也可以稍微扩展为：

```text
当前账号无权查看或操作该订单，请确认是否使用了下单账号。
```

但不要说：

```text
user_id 和 customer_id 不匹配。
```

因为这是内部权限规则。

### 练习 3：为什么 `INTERNAL_AUTH_FAILED` 不能告诉用户

Java 返回：

```json
{
  "code": "INTERNAL_AUTH_FAILED",
  "message": "内部服务鉴权失败。"
}
```

为什么不直接展示？

参考答案：

```text
因为这是 Python AI 服务和 Java 业务服务之间的内部调用问题，不是普通用户能修复的问题。
直接展示会让用户困惑，也可能暴露服务间鉴权、internal API、token 等内部架构信息。
更合适的用户提示是：订单查询服务暂时不可用，请稍后重试。
```

### 练习 4：为什么不使用 Java message

Java 返回：

```json
{
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在，SQL 查询未命中 orders 表。"
}
```

Python 应该怎么处理？

参考答案：

```text
Python 应该提取 code=ORDER_NOT_FOUND，但不要展示 Java message。
应该使用 Python 本地维护的安全提示：订单不存在，请确认订单号是否正确。
```

原因：

```text
Java message 可能包含内部排查信息，AI 服务需要控制最终面向用户的话术。
```

### 练习 5：解释错误映射层为什么应该独立成模块

为什么不把所有错误判断都写在 `JavaOrderClient` 和 `JavaTicketClient` 里面？

参考答案：

```text
因为订单查询和工单创建都会遇到 Java 错误码，如果各自写一份判断，会重复、容易不一致，也难测试。
独立成 java_error_mapping.py 后，错误语义集中维护，两个 client 复用，同一个错误码在不同工具里可以保持一致。
```

## 自测题

### 自测 1：HTTP 状态码和业务错误码有什么区别？

参考答案：

```text
HTTP 状态码是协议层粗分类，比如 404、403、500。
业务错误码是业务语义，比如 ORDER_NOT_FOUND、ORDER_ACCESS_DENIED。
同一个 HTTP 状态码下可能有多个业务错误码，所以不能只靠 HTTP 状态码决定最终用户回答。
```

### 自测 2：为什么 AI 不能自由解释 Java 错误？

参考答案：

```text
因为模型可能编造原因、泄露内部信息、输出不稳定。
错误处理属于后端安全边界，应该由确定性代码先把错误映射成安全语义，模型最多基于安全语义组织语言。
```

### 自测 3：`INTERNAL_AUTH_FAILED` 本节映射成什么？

参考答案：

```text
映射成 TOOL_UPSTREAM_ERROR。
订单查询场景提示：订单查询服务暂时不可用，请稍后重试。
工单创建场景提示：工单业务服务暂时不可用，请稍后重试。
```

### 自测 4：为什么 `IDEMPOTENCY_KEY_REQUIRED` 不应该让用户看到？

参考答案：

```text
因为幂等键应该由后端生成和传递，普通用户不应该理解或填写幂等键。
如果 Java 返回缺少幂等键，说明 Python/Java 写接口契约可能有问题，应该隐藏成工单业务服务拒绝请求或提交暂时失败。
```

### 自测 5：本节新增测试最重要验证什么？

参考答案：

```text
验证 Java 错误码能被稳定映射成安全 AppException。
尤其验证两类边界：
用户可见业务错误要准确表达；
内部错误、契约错误、服务错误不能把内部细节泄露给用户。
```

## 本节总结

本节把 Java 错误码处理从“粗略看 HTTP 状态码”推进到了“按错误语义做安全映射”。

现在链路更清晰：

```text
Java 返回机器错误码
-> Python 提取 code
-> java_error_mapping.py 判断是否用户安全
-> 生成 AppException
-> Agent/接口层给出安全中文回答
```

本节最重要的思想是：

```text
错误码是机器语义，不等于用户话术。
Java message 不一定安全，不应该默认直接展示。
模型不能决定错误真相，只能在安全边界内表达。
内部错误要写日志排查，用户侧要克制表达。
```

下一节进入：

```text
阶段 7 第 10 节：trace_id 串联 Python + Java
```

那一节会重点学习：

```text
一次用户请求如何带着同一个 trace_id 穿过 Python AI 服务、Java 业务服务、MySQL/Redis 日志，
让我们能从用户报错一路查到具体服务、具体接口、具体错误码。
```
