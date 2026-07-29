# 阶段 8 第 13 节：MCP 错误处理

## 本节定位

前面两节我们已经完成：

```text
第 11 节：MCP Client 调试。
第 12 节：MCP 工具参数校验。
```

第 12 节里你已经看到两个现象：

```text
schema 层参数错误 -> SDK 拦截，result.is_error = true。
业务层校验失败 -> 工具函数正常返回，structured_content.ok = false。
```

这一节继续把错误处理讲清楚。

核心问题是：

```text
MCP Tool 调用失败时，到底应该返回什么？
哪些错误应该是 is_error=true？
哪些错误应该是 ok=false？
哪些错误可以给模型看？
哪些错误只能进日志？
```

一句话总结本节：

```text
MCP 错误处理要先分类：可预期业务失败返回 ok=false，工具无法正常执行才用 is_error=true；任何内部异常都要包装成安全错误，不把原始异常直接暴露给模型。
```

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
协议错误、工具执行错误、业务错误、系统错误有什么区别。
MCP `is_error` 应该什么时候用。
`structured_content.ok=false` 应该什么时候用。
为什么订单不存在不一定应该是工具执行错误。
为什么权限不足通常应该返回安全业务错误。
为什么上游超时更适合工具错误。
为什么未预期异常不能直接抛给模型。
ToolError 在本节里的作用。
错误码 error_code 应该怎么设计。
错误消息 message 应该怎么写才安全。
retryable 字段有什么意义。
为什么测试必须覆盖错误路径。
本节错误处理和后续 Java business service 接入有什么关系。
```

本节新增或修改：

```text
projects/ai-service/app/mcp_servers/tool_error_handling.py
projects/ai-service/app/mcp_servers/minimal_server.py
projects/ai-service/app/mcp_clients/minimal_client.py
projects/ai-service/tests/test_mcp_tool_error_handling.py
projects/ai-service/tests/test_mcp_client_smoke.py
projects/ai-service/tests/test_minimal_mcp_server.py
```

## 本节不做什么

省 token 模式下，本节不扩展到外部系统。

本节不做：

```text
不启动 VMware。
不启动 Docker。
不连接 Qdrant / Milvus。
不连接 MySQL / Redis。
不启动 Java business service。
不调用真实大模型。
不真实查询订单。
不真实创建工单。
不做完整权限体系。
不做 trace_id 日志增强。
不提交 GitHub。
不做敏感信息扫描。
```

本节只做：

```text
新增 simulate_tool_error_handling 教学工具。
模拟成功、业务不存在、权限不足、上游超时、未预期异常五种场景。
用 ok=false 表达可预期业务失败。
用 ToolError 表达工具无法正常执行。
包装内部异常，避免原始异常泄露。
用测试固定错误边界。
```

## 官方资料依据

本节依据：

| 资料 | 本节使用点 |
| --- | --- |
| [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | Tool result、structuredContent、isError 的边界 |
| [MCP Base Protocol](https://modelcontextprotocol.io/specification/2025-11-25/basic) | JSON-RPC request/response/error 基础 |
| [MCP Python SDK 官方仓库](https://github.com/modelcontextprotocol/python-sdk) | `ToolError`、`MCPServer`、`Client(mcp)` |
| [MCP Python SDK 文档](https://py.sdk.modelcontextprotocol.io/) | SDK v2 tool/client 调试写法 |

本项目本地 SDK 行为已经用测试确认：

```text
工具函数返回 {"ok": false, ...} -> result.is_error=false，structured_content 有值。
工具函数 raise ToolError(...) -> result.is_error=true，structured_content=None。
工具函数直接 raise RuntimeError(...) -> SDK 也会包装成 is_error=true，但可能暴露原始异常消息，所以不推荐。
```

## 基础知识铺垫

### 1. 为什么错误处理要先分类

很多初学者一遇到错误就只想：

```text
抛异常。
返回失败。
打印日志。
```

但 AI 工具调用里，这不够。

你必须先判断：

```text
这个错误是不是预期内的业务结果？
这个错误是不是工具无法执行？
这个错误是不是协议层问题？
这个错误是不是系统内部异常？
```

因为不同错误要给不同对象看：

```text
模型需要看到安全、可理解、可行动的信息。
用户只能看到业务上可解释的信息。
日志可以记录更多技术细节。
测试需要固定错误结构。
```

如果分类不清，容易出现两种极端：

```text
把所有错误都当异常抛，导致 Agent 无法稳定恢复。
把所有错误都当普通业务结果返回，导致真正系统故障被掩盖。
```

### 2. MCP 里常见错误可以分四类

本节按四类理解：

```text
协议错误。
参数/schema 错误。
业务错误。
系统/工具执行错误。
```

#### 协议错误

协议错误是 MCP 通信本身不符合协议。

例如：

```text
JSON-RPC 格式错误。
method 不存在。
id 不合法。
initialize 生命周期没走完就调用工具。
请求 params 结构不符合协议。
```

这类错误通常由 MCP SDK 或协议层处理。
我们的业务工具代码不应该把它伪装成订单不存在。

#### 参数/schema 错误

参数/schema 错误是工具调用参数不符合 input_schema。

例如：

```text
缺少必填字段。
priority 不是 low/normal/high。
title 太短。
a 应该是 integer，却传了 string。
```

第 12 节已经学过：

```text
这类错误可能在进入工具函数前被 SDK 拦截。
```

表现通常是：

```text
is_error=true
structured_content=None
```

#### 业务错误

业务错误是工具正常执行了，但业务结果不是成功。

例如：

```text
订单不存在。
用户无权查看订单。
订单不满足创建工单条件。
退款规则不允许当前操作。
用户确认信息不足。
```

这类错误通常不是系统坏了。
它们是业务流程中可预期的结果。

更适合返回：

```json
{
  "ok": false,
  "error_code": "ORDER_NOT_FOUND",
  "message": "没有找到符合条件的订单，请确认订单号是否正确。",
  "retryable": false,
  "details": {
    "safe_reason": "order_not_found"
  }
}
```

也就是：

```text
is_error=false
structured_content.ok=false
```

#### 系统/工具执行错误

系统错误是工具无法正常完成执行。

例如：

```text
Java 服务超时。
数据库连接失败。
Redis 不可用。
上游返回非法 JSON。
内部代码出现未预期异常。
```

这类错误更适合进入工具错误：

```text
is_error=true
structured_content=None
```

但要注意：

```text
不能把原始异常直接暴露给模型。
```

应该包装成安全消息。

### 3. `is_error=true` 表示什么

`is_error=true` 表示：

```text
这次 tool call 没有得到正常工具结果。
```

它适合表达：

```text
工具参数在 schema 层不合法。
工具执行时上游不可用。
工具内部发生未预期异常。
工具无法完成当前请求。
```

它不适合表达所有业务失败。

例如订单不存在：

```text
订单系统正常响应：没找到订单。
```

这在很多业务里是可预期结果。
如果把它也做成 `is_error=true`，Agent 可能误以为工具坏了。

### 4. `ok=false` 表示什么

`ok=false` 是我们在 structured_content 里设计的业务字段。

它表示：

```text
工具函数正常执行了，但业务结果是失败或无法继续。
```

适合：

```text
订单不存在。
权限不足。
参数业务校验未通过。
不满足创建条件。
需要用户补充信息。
需要用户确认。
```

`ok=false` 的好处：

```text
结构稳定。
Agent 可以读取 error_code。
模型可以生成安全解释。
后续流程可以判断是否追问、拒答、转人工。
```

### 5. 为什么不能直接返回原始异常

如果工具代码里直接：

```python
raise RuntimeError("database password invalid for mysql://root:xxx@...")
```

SDK 可能把异常消息包装进工具错误内容。

风险：

```text
泄露数据库地址。
泄露 token/key/password。
泄露内部类名和文件路径。
泄露 Java/Python 调用细节。
让模型拿到不该拿的信息。
让用户看到不该看的技术细节。
```

所以真实工具里应该：

```text
捕获内部异常。
日志里记录详细信息。
返回给模型/Client 的是安全错误码和安全消息。
```

本节用 `ToolError` 包装未预期异常：

```text
INTERNAL_TOOL_ERROR: 工具执行失败，请稍后重试或联系人工处理。
```

而不是返回：

```text
simulated internal dependency failure
```

### 6. ToolError 是什么

本地 MCP Python SDK 中有：

```python
from mcp.server.mcpserver.exceptions import ToolError
```

本节用它表达：

```text
工具无法正常完成执行。
```

例如：

```python
raise ToolError("UPSTREAM_TIMEOUT: 订单服务暂时没有响应，请稍后重试。")
```

Client 看到：

```text
is_error=true
structured_content=None
content 里有安全错误文本
```

学习阶段你先记住：

```text
可预期业务失败：返回 ok=false。
工具执行失败：raise ToolError，且消息必须安全。
```

### 7. error_code 怎么设计

错误码应该给程序读。
不是给人写作文。

建议：

```text
稳定。
大写。
英文。
语义清楚。
低基数。
不要包含动态值。
不要包含用户输入。
```

好的例子：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
INVALID_TOOL_ARGUMENTS
UPSTREAM_TIMEOUT
INTERNAL_TOOL_ERROR
```

不好的例子：

```text
error
fail
A1001_not_found
user_001_access_denied
订单不存在
mysql_192_168_1_2_timeout
```

原因：

```text
错误码要用于测试、日志、指标、Agent 分支判断。
动态值会导致统计和判断混乱。
```

### 8. message 怎么设计

message 是给模型或用户生成回答时参考的。

它应该：

```text
安全。
简短。
可理解。
可行动。
不暴露内部细节。
```

例如：

```text
没有找到符合条件的订单，请确认订单号是否正确。
当前用户无权查看或操作该订单。
订单服务暂时没有响应，请稍后重试。
工具执行失败，请稍后重试或联系人工处理。
```

不要返回：

```text
Java NullPointerException at OrderServiceImpl.java:87
SQL timeout on jdbc:mysql://...
Redis password invalid
internal token mismatch
```

这些应该进日志，不应该给模型自由解释。

### 9. retryable 是什么

本节业务错误结构里有：

```json
"retryable": false
```

它表示：

```text
同样参数重试是否可能成功。
```

例子：

```text
订单不存在：通常 retryable=false。
权限不足：通常 retryable=false。
上游超时：通常 retryable=true 或由外层 retry 策略判断。
限流：通常 retryable=true，但要等待。
参数错误：通常 retryable=false，除非用户修正参数。
```

这个字段对 Agent 有用。

例如：

```text
retryable=false -> 不要盲目重试，应该让用户修正或拒答。
retryable=true -> 可以提示稍后重试，或由后端按策略重试。
```

### 10. details 里只能放安全细节

本节业务错误里有：

```json
"details": {
  "safe_reason": "order_not_found"
}
```

`details` 可以帮助 Agent 或前端理解原因。

但它不能放：

```text
SQL。
完整异常堆栈。
内部 token。
用户敏感字段。
Java 内部对象。
数据库连接信息。
```

也就是说：

```text
details 不是内部日志。
details 仍然属于可能被模型看到的工具结果。
```

### 11. 错误处理决策表

真实开发时，最容易纠结的是：

```text
这个错误到底返回 ok=false，还是 is_error=true？
```

可以先用下面这张表判断。

| 场景 | 错误类型 | 建议返回 | 原因 |
| --- | --- | --- | --- |
| 订单不存在 | 业务错误 | `is_error=false` + `ok=false` + `ORDER_NOT_FOUND` | 工具正常执行，业务结论是没找到 |
| 用户无权查看订单 | 业务/权限错误 | `is_error=false` + `ok=false` + `ORDER_ACCESS_DENIED` | 权限不足是可预期业务结果，但消息必须安全 |
| 缺少必填字段 | 参数/schema 错误 | 通常由 SDK 拦截，`is_error=true` | 工具参数不符合 input schema |
| 枚举值非法 | 参数/schema 错误 | 通常由 SDK 拦截，`is_error=true` | 调用方传了 schema 不允许的值 |
| 空白标题、trim 后为空 | 业务校验错误 | `is_error=false` + `ok=false` + `INVALID_TOOL_ARGUMENTS` | 工具函数正常执行，但业务语义无效 |
| 用户未确认写操作 | 业务流程错误 | `is_error=false` + `ok=false` + `USER_CONFIRMATION_REQUIRED` | 不是系统坏了，而是流程缺确认 |
| 幂等键缺失 | 参数/安全错误 | 多数返回 `ok=false` 或在 schema 层拦截 | 写操作安全关键字段缺失，不应继续 |
| Java 服务连接超时 | 系统/工具执行错误 | `is_error=true` + 安全 `UPSTREAM_TIMEOUT` | 没拿到可靠业务结果 |
| Java 返回 500 | 系统/上游错误 | `is_error=true` + 安全 `UPSTREAM_SERVICE_ERROR` | 上游内部故障，不是业务答案 |
| Java 返回非预期字段结构 | 契约/系统错误 | `is_error=true` + 安全 `UPSTREAM_CONTRACT_ERROR` | 下游结果不可信，不能交给 Agent 当业务事实 |
| Python 代码未预期异常 | 内部系统错误 | `is_error=true` + 安全 `INTERNAL_TOOL_ERROR` | 必须隐藏原始异常 |
| MCP method 不存在 | 协议错误 | 由 SDK/协议层返回 JSON-RPC error | 不是业务工具结果 |

这张表背后的判断规则是：

```text
工具拿到了可靠业务结论 -> 通常 structured_content。
业务结论是失败 -> structured_content.ok=false。
工具没有拿到可靠业务结论 -> 通常 is_error=true。
协议本身不合法 -> JSON-RPC/protocol error。
```

再压缩成一句工程判断：

```text
能让 Agent 基于 error_code 做业务下一步的，倾向 ok=false；工具本身没法可信执行完的，倾向 is_error=true。
```

### 12. 错误处理的分层职责

不要把所有错误处理都塞进 MCP tool 函数里。

一个真实工具大致会有几层：

```text
MCP SDK 层
MCP tool 参数层
业务校验层
adapter/client 层
Java business service 层
错误映射层
Agent 决策层
```

每层职责不同。

| 层 | 负责什么 | 不应该负责什么 |
| --- | --- | --- |
| MCP SDK 层 | 协议、schema 入参、tool result 包装 | 业务权限判断 |
| MCP tool 参数层 | 必填、类型、枚举、长度 | 数据库查询 |
| 业务校验层 | trim、流程状态、确认信息、幂等字段 | 直接决定模型最终回答 |
| adapter/client 层 | 调 Java、timeout、HTTP 状态、响应解析 | 把 Java 内部错误原样给模型 |
| 错误映射层 | Java 错误码到安全 MCP 结果 | 泄露 Java 堆栈或 SQL |
| Agent 决策层 | 根据 error_code 决定追问、拒答、重试、转人工 | 修改底层业务事实 |

如果职责混乱，就会出现：

```text
MCP tool 里到处 try/except。
Java 500 被当成订单不存在。
权限错误泄露 internal token。
Agent 不知道该追问还是重试。
测试只能测成功路径，错误一改就乱。
```

所以真实项目里建议固定一个错误流：

```text
参数错 -> 参数校验结构。
业务拒绝 -> ok=false + 业务 error_code。
上游不可用 -> ToolError + 安全系统 error_code。
内部异常 -> 日志记录 + INTERNAL_TOOL_ERROR。
```

## 本节主题系统讲解

### 1. 本节新增工具

新增 tool：

```text
simulate_tool_error_handling
```

它有一个参数：

```text
scenario
```

可选值：

```text
success
business_not_found
permission_denied
upstream_timeout
unexpected_failure
```

它的作用不是做真实业务。
它是教学工具，用来模拟不同错误边界。

### 2. 为什么用 scenario 枚举

代码：

```python
ToolErrorScenario = Literal[
    "success",
    "business_not_found",
    "permission_denied",
    "upstream_timeout",
    "unexpected_failure",
]
```

这样 MCP input_schema 会暴露 enum：

```json
"scenario": {
  "enum": [
    "success",
    "business_not_found",
    "permission_denied",
    "upstream_timeout",
    "unexpected_failure"
  ]
}
```

好处：

```text
测试清楚。
Client 调试清楚。
模型不能随便传其他场景。
本节能稳定复现每一种错误。
```

### 3. 成功场景

`success` 返回：

```json
{
  "ok": true,
  "error_code": null,
  "message": "Tool completed successfully.",
  "retryable": false,
  "details": {
    "example_result": "ticket_error_handling_smoke"
  }
}
```

重点：

```text
工具正常执行。
is_error=false。
structured_content.ok=true。
```

### 4. 订单不存在场景

`business_not_found` 返回：

```json
{
  "ok": false,
  "error_code": "ORDER_NOT_FOUND",
  "message": "没有找到符合条件的订单，请确认订单号是否正确。",
  "retryable": false,
  "details": {
    "safe_reason": "order_not_found"
  }
}
```

为什么不用 `ToolError`？

因为：

```text
订单不存在是业务可预期结果。
工具本身正常执行了。
后续 Agent 可以根据 ORDER_NOT_FOUND 提示用户确认订单号。
```

所以它是：

```text
is_error=false
ok=false
```

### 5. 权限不足场景

`permission_denied` 返回：

```json
{
  "ok": false,
  "error_code": "ORDER_ACCESS_DENIED",
  "message": "当前用户无权查看或操作该订单。",
  "retryable": false,
  "details": {
    "safe_reason": "permission_denied"
  }
}
```

权限不足也通常是业务可预期结果。

注意：

```text
不要告诉用户内部权限规则。
不要告诉用户应该伪造哪个 header。
不要告诉模型 internal token。
```

只返回安全解释。

### 6. 上游超时场景

`upstream_timeout` 使用：

```python
raise ToolError("UPSTREAM_TIMEOUT: 订单服务暂时没有响应，请稍后重试。")
```

Client 看到：

```text
is_error=true
structured_content=None
content 包含 UPSTREAM_TIMEOUT
```

为什么这里用 `ToolError`？

因为：

```text
工具无法完成执行。
上游依赖没有给出可靠业务结果。
后续 Agent 不应该把它当成订单不存在或权限不足。
```

上游超时不是业务答案。
它是系统暂时不可用。

### 7. 未预期异常场景

`unexpected_failure` 模拟：

```python
raise RuntimeError("simulated internal dependency failure")
```

但工具不会直接把这个 RuntimeError 抛给 Client。

它会包装成：

```python
raise ToolError(
    "INTERNAL_TOOL_ERROR: 工具执行失败，请稍后重试或联系人工处理。"
) from exc
```

测试确认：

```text
Client 能看到 INTERNAL_TOOL_ERROR。
Client 看不到 simulated internal dependency failure。
```

这就是安全边界。

真实项目里，内部异常应该：

```text
详细写入日志。
对 Client/模型只返回安全错误码和安全消息。
```

### 8. Client smoke 输出怎么读

第 11 节的脚本现在会多输出两个错误处理样例：

```text
simulate_tool_error_handling_business
simulate_tool_error_handling_system
```

业务错误：

```json
{
  "is_error": false,
  "structured_content": {
    "ok": false,
    "error_code": "ORDER_NOT_FOUND"
  }
}
```

系统错误：

```json
{
  "is_error": true,
  "structured_content": null,
  "text_content": [
    "Error executing tool simulate_tool_error_handling: UPSTREAM_TIMEOUT: ..."
  ]
}
```

你要能一眼看出：

```text
业务错误还有 structured_content，Agent 可以读 error_code。
系统错误没有 structured_content，要进入兜底/重试/转人工逻辑。
```

### 9. 测试覆盖了哪些错误边界

新增测试：

```text
tests/test_mcp_tool_error_handling.py
```

覆盖：

```text
schema 暴露 scenario enum。
business_not_found 返回 ok=false 且 is_error=false。
permission_denied 返回安全业务错误。
upstream_timeout 返回 is_error=true 和安全错误消息。
unexpected_failure 被包装成 INTERNAL_TOOL_ERROR，不暴露内部异常文本。
```

这些测试是为了守住四件事：

```text
错误码稳定。
业务错误不被误判为工具崩溃。
系统错误不被误判为业务答案。
内部异常不泄露。
```

## 代码变化讲解

### 1. `tool_error_handling.py`

这个文件是本节核心。

它负责：

```text
定义错误场景枚举。
构造业务错误结构。
模拟不同工具错误处理结果。
包装系统异常。
```

为什么单独放一个文件？

因为错误处理是独立知识点。
如果全部塞到 `minimal_server.py`，server 注册和错误处理逻辑会混在一起。

### 2. `ToolErrorScenario`

代码：

```python
ToolErrorScenario = Literal[
    "success",
    "business_not_found",
    "permission_denied",
    "upstream_timeout",
    "unexpected_failure",
]
```

作用：

```text
让 scenario 参数变成枚举。
让 MCP schema 明确可选场景。
让测试能稳定复现不同错误。
```

### 3. `business_error`

代码：

```python
def business_error(
    *,
    error_code: str,
    message: str,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
```

它统一返回：

```text
ok
error_code
message
retryable
details
```

学习重点：

```text
业务错误也要统一结构。
不要每个工具随便返回一套字段。
```

### 4. `simulate_tool_error_response`

这个函数按 scenario 分支返回或抛错。

它体现本节核心规则：

```text
success -> ok=true。
business_not_found -> ok=false。
permission_denied -> ok=false。
upstream_timeout -> raise ToolError。
unexpected_failure -> catch RuntimeError，再 raise safe ToolError。
```

### 5. `minimal_server.py`

注册新工具：

```python
@mcp.tool()
def simulate_tool_error_handling(scenario: ToolErrorScenario) -> dict[str, Any]:
    """Simulate safe MCP tool success, business errors, and system errors."""
    return simulate_tool_error_response(scenario)
```

它的函数签名暴露 schema。
函数体调用错误处理 helper。
docstring 说明它是教学模拟工具。

### 6. `minimal_client.py`

Client smoke 增加：

```text
business_not_found 调用。
upstream_timeout 调用。
```

这样手动运行脚本时，你能直接对比：

```text
业务错误返回结构。
系统错误返回结构。
```

### 7. `test_mcp_tool_error_handling.py`

这是本节最关键测试文件。

它不是为了测试“模拟函数能不能跑”。
它是为了测试：

```text
错误分类是否稳定。
错误边界是否安全。
错误消息是否不泄露内部细节。
```

真实 Agent 工程里，错误测试和成功测试一样重要。

## 手动验证

本节不单独新增 manual-tasks 文档。
因为不需要启动任何外部服务。

运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts\mcp_client_smoke.py
```

重点看：

```text
simulate_tool_error_handling 的 input_schema.scenario.enum。
simulate_tool_error_handling_business.is_error=false。
simulate_tool_error_handling_business.structured_content.ok=false。
simulate_tool_error_handling_business.structured_content.error_code=ORDER_NOT_FOUND。
simulate_tool_error_handling_system.is_error=true。
simulate_tool_error_handling_system.structured_content=null。
simulate_tool_error_handling_system.text_content 包含 UPSTREAM_TIMEOUT。
```

运行测试：

```powershell
uv run pytest tests\test_mcp_tool_error_handling.py tests\test_mcp_tool_parameter_validation.py tests\test_mcp_client_smoke.py tests\test_minimal_mcp_server.py
```

预期：

```text
13 passed
```

## 常见误区

### 误区 1：所有失败都应该 `is_error=true`

不对。

业务可预期失败更适合：

```text
is_error=false
structured_content.ok=false
```

例如订单不存在、权限不足、业务条件不满足。

### 误区 2：所有失败都应该 `ok=false`

也不对。

工具执行不了时，比如上游超时、内部异常，更适合：

```text
is_error=true
```

否则 Agent 可能把系统故障误当成业务答案。

### 误区 3：原始异常消息直接返回更方便排查

不对。

排查应该靠日志。
返回给模型和用户的内容必须安全。

### 误区 4：权限错误可以告诉用户哪里没权限

只能说安全范围内的信息。

可以说：

```text
当前用户无权查看或操作该订单。
```

不要说：

```text
因为 X-Internal-Token 不对。
因为 user_id 和 customer_id 不匹配，真实 customer_id 是 C_SECRET。
```

### 误区 5：error_code 可以随便写

不行。

error_code 会被测试、日志、指标、Agent 分支依赖。
必须稳定、低基数、无动态值。

### 误区 6：只要 catch Exception 就安全

不够。

catch 后还要：

```text
日志记录内部细节。
返回安全错误。
不要吞掉严重问题。
不要把所有错误都变成同一个业务失败。
```

本节先做最小安全包装，后面可观测性阶段会继续加强日志和 trace。

## 项目映射

本节的模拟错误，将来会映射到真实 Java business service。

例如：

| Java 返回/异常 | Python/MCP 处理建议 |
| --- | --- |
| `ORDER_NOT_FOUND` | `ok=false`, `error_code=ORDER_NOT_FOUND` |
| `ORDER_ACCESS_DENIED` | `ok=false`, `error_code=ORDER_ACCESS_DENIED` |
| `400/422` 契约错误 | 多数是工具或参数错误，需安全包装 |
| Java 连接超时 | `ToolError("UPSTREAM_TIMEOUT: ...")` |
| Java 500 | `ToolError("UPSTREAM_SERVICE_ERROR: ...")` |
| Python 未预期异常 | 记录日志，返回 `INTERNAL_TOOL_ERROR` |

真实链路应该是：

```text
MCP Client call_tool
-> MCP Server tool
-> 参数校验
-> 调 Java business service
-> Java 错误码映射
-> 业务错误返回 ok=false
-> 系统错误返回 ToolError
-> Agent 根据 error_code/is_error 决定追问、拒答、重试或转人工
```

### 真实 `query_order` 的错误处理草图

以后把订单查询封装成 MCP Tool 时，可以按这个思路：

```text
query_order(order_id, user_id, tenant_id)
```

可能结果：

| Java/Python 情况 | MCP 返回建议 | Agent 下一步 |
| --- | --- | --- |
| 找到订单且有权限 | `ok=true` + 订单白名单字段 | 正常总结回答 |
| 订单不存在 | `ok=false`, `ORDER_NOT_FOUND` | 提示用户确认订单号 |
| 当前用户无权查看 | `ok=false`, `ORDER_ACCESS_DENIED` | 安全拒答，不泄露订单 |
| Java 超时 | `is_error=true`, `UPSTREAM_TIMEOUT` | 兜底提示稍后重试或转人工 |
| Java 返回 500 | `is_error=true`, `UPSTREAM_SERVICE_ERROR` | 兜底，不让模型编造订单状态 |
| Java 返回字段缺失 | `is_error=true`, `UPSTREAM_CONTRACT_ERROR` | 不信任结果，记录日志 |
| Python 映射字段时报错 | `is_error=true`, `INTERNAL_TOOL_ERROR` | 兜底，日志排查 |

这里最重要的是：

```text
订单不存在不是系统故障。
Java 超时不是业务答案。
字段结构不可信不能交给模型总结。
```

### 真实 `create_ticket` 的错误处理草图

创建工单是写操作，比查询订单更严格。

可能结果：

| 场景 | MCP 返回建议 | 原因 |
| --- | --- | --- |
| 用户未确认 | `ok=false`, `USER_CONFIRMATION_REQUIRED` | 写操作必须等用户确认 |
| 幂等键缺失 | `ok=false`, `IDEMPOTENCY_KEY_REQUIRED` 或 schema 拦截 | 防止重复创建 |
| 参数业务校验失败 | `ok=false`, `INVALID_TOOL_ARGUMENTS` | 需要补字段或修正字段 |
| 用户无权为该订单建工单 | `ok=false`, `ORDER_ACCESS_DENIED` | 权限业务拒绝 |
| 工单已创建过 | `ok=false` 或 `ok=true` + existing ticket，取决于业务设计 | 幂等命中，不应重复写 |
| Java 创建成功 | `ok=true` + ticket_id + safe_summary | 可以告诉用户已创建 |
| Java 超时且幂等未知 | `is_error=true`, `UPSTREAM_TIMEOUT` | 不确定是否写入成功，不能让模型承诺 |
| Java 500 | `is_error=true`, `UPSTREAM_SERVICE_ERROR` | 系统故障 |

写操作的关键点：

```text
如果无法确认写操作是否成功，不要让模型说“已经创建成功”。
如果缺少用户确认，不要尝试自动补确认。
如果幂等状态不清楚，不要重复发起写请求。
```

这就是为什么我们前面一直强调：

```text
模型不能直接修改业务系统。
后端必须做确认、幂等、权限和错误兜底。
```

## 反面案例

### 反面案例 1：把业务失败直接抛异常

不好的写法：

```python
if order is None:
    raise ToolError("order not found")
```

问题：

```text
Client 会看到 is_error=true。
Agent 可能以为订单工具坏了。
后续不好区分订单不存在和上游故障。
```

更好的写法：

```python
return {
    "ok": False,
    "error_code": "ORDER_NOT_FOUND",
    "message": "没有找到符合条件的订单，请确认订单号是否正确。",
    "retryable": False,
    "details": {"safe_reason": "order_not_found"},
}
```

### 反面案例 2：把系统异常当业务失败

不好的写法：

```python
except TimeoutError:
    return {
        "ok": False,
        "error_code": "ORDER_NOT_FOUND",
        "message": "订单不存在",
    }
```

问题：

```text
Java 服务超时和订单不存在完全不是一回事。
这样会误导用户，也会让系统故障被隐藏。
```

更好的写法：

```python
except TimeoutError as exc:
    raise ToolError("UPSTREAM_TIMEOUT: 订单服务暂时没有响应，请稍后重试。") from exc
```

### 反面案例 3：把内部异常原样返回

不好的写法：

```python
except Exception as exc:
    raise ToolError(str(exc))
```

问题：

```text
str(exc) 可能包含内部路径、SQL、token、Java 错误、数据库地址。
模型和用户都可能看到这些内容。
```

更好的写法：

```python
except Exception as exc:
    logger.exception("query_order tool failed", exc_info=exc)
    raise ToolError("INTERNAL_TOOL_ERROR: 工具执行失败，请稍后重试或联系人工处理。") from exc
```

注意：

```text
本节教学代码没有展开 logging，是为了不偏离 MCP 错误处理主线。
真实项目必须记录日志。
```

### 反面案例 4：错误码包含动态值

不好的错误码：

```text
ORDER_A1001_NOT_FOUND
USER_U1001_DENIED
TIMEOUT_192_168_88_10
```

问题：

```text
错误码变成高基数字段。
日志统计、指标聚合、测试断言都会变差。
还可能泄露用户和环境信息。
```

更好的错误码：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
UPSTREAM_TIMEOUT
```

动态值如果确实需要记录，放日志或安全 details，不要放 error_code。

## 面试表达

如果面试官问：

```text
你们 MCP Tool 的错误处理怎么设计？
```

不要只说：

```text
try catch 一下。
```

可以这样讲：

```text
我会先区分协议错误、参数错误、业务错误和系统错误。协议和 schema 错误通常由 MCP SDK 或参数模型拦截；可预期业务失败，比如订单不存在、权限不足，我不会当成工具崩溃，而是返回 structured_content，里面用 ok=false、稳定 error_code、安全 message 和 retryable 字段表达；如果是 Java 服务超时、500、契约不匹配或 Python 内部异常，就用安全 ToolError 返回 is_error=true，并且不把原始异常暴露给模型。
```

继续补项目落地：

```text
比如 query_order 工具里，ORDER_NOT_FOUND 会返回 ok=false，让 Agent 提示用户确认订单号；ORDER_ACCESS_DENIED 会安全拒答；Java timeout 会返回 UPSTREAM_TIMEOUT，进入重试、降级或转人工；Java 返回字段不符合契约时，我不会让模型总结这个结果，而是作为 UPSTREAM_CONTRACT_ERROR 处理。
```

再补安全意识：

```text
错误消息分两层：日志里保留内部异常和 trace_id，给模型或用户的 tool result 只保留安全错误码和可理解消息，不返回 SQL、token、header、堆栈或内部服务地址。
```

最后补测试：

```text
这类边界我会写测试固定，尤其验证业务错误不是 is_error，系统错误是 is_error，未预期异常不会泄露原始异常文本。
```

这套回答比“我会捕获异常”更像真实工程经验。

## 进一步理解：错误处理不是为了隐藏问题

安全包装错误不等于忽略问题。

错误处理同时服务两个目标：

```text
对外安全。
对内可排查。
```

对外：

```text
模型和用户只看到安全、稳定、可行动的信息。
```

对内：

```text
日志、trace_id、metrics、告警要能定位真实原因。
```

所以真实生产里应该同时有：

```text
safe tool result
structured log
trace_id
error_code metric
upstream status
duration
retry/degradation record
```

本节只先做：

```text
safe tool result
错误分类测试
```

后面可观测性和真实 Java 接入时再补日志、trace 和 metrics。

## 本节练习

### 练习 1：业务错误和系统错误有什么区别？

参考答案：

```text
业务错误是工具正常执行后得到的可预期业务结果，比如订单不存在、权限不足；系统错误是工具无法正常完成执行，比如上游超时、数据库不可用、内部异常。
```

### 练习 2：订单不存在为什么适合 `ok=false`？

参考答案：

```text
因为订单不存在通常是业务可预期结果，工具本身正常执行并拿到了业务结论。返回 ok=false 和 ORDER_NOT_FOUND 更方便 Agent 提示用户确认订单号。
```

### 练习 3：上游超时为什么适合 `is_error=true`？

参考答案：

```text
因为上游超时表示工具没有拿到可靠业务结果，不能把它当成订单不存在或权限不足。它属于工具执行失败，应进入重试、降级或转人工逻辑。
```

### 练习 4：为什么不能直接返回 RuntimeError 的原始消息？

参考答案：

```text
原始异常可能包含内部类名、文件路径、数据库地址、token、SQL、用户敏感信息等，不应该暴露给模型或用户。应该记录到日志，并返回安全错误码和安全消息。
```

### 练习 5：error_code 应该怎么设计？

参考答案：

```text
error_code 应该稳定、英文、大写、低基数、无动态值，适合测试、日志、指标和 Agent 分支判断，比如 ORDER_NOT_FOUND、ORDER_ACCESS_DENIED、UPSTREAM_TIMEOUT。
```

### 练习 6：message 应该怎么设计？

参考答案：

```text
message 应该安全、简短、可理解、可行动，不暴露内部实现细节。例如“当前用户无权查看或操作该订单”，不要返回 internal token、SQL 或堆栈。
```

### 练习 7：retryable 有什么用？

参考答案：

```text
retryable 帮 Agent 或后端判断同样参数是否值得重试。订单不存在和权限不足通常不应盲目重试，上游超时或限流可能适合稍后重试。
```

## 自测题

### 自测 1：`business_not_found` 场景的 `is_error` 应该是什么？

参考答案：

```text
应该是 false。因为它是业务可预期结果，工具正常执行了，只是 structured_content.ok=false。
```

### 自测 2：`upstream_timeout` 场景的 `structured_content` 应该是什么？

参考答案：

```text
应该是 None/null。因为工具通过 ToolError 返回工具执行错误，Client 看到 is_error=true，不再有正常结构化业务结果。
```

### 自测 3：权限不足应该告诉模型 internal token 错了吗？

参考答案：

```text
不应该。应该返回安全业务错误，例如 ORDER_ACCESS_DENIED 和“当前用户无权查看或操作该订单”，不要暴露 internal token、header 规则或真实权限细节。
```

### 自测 4：为什么 `unexpected_failure` 要包装成 `INTERNAL_TOOL_ERROR`？

参考答案：

```text
因为未预期异常可能包含内部实现细节。包装成 INTERNAL_TOOL_ERROR 可以让 Client 和模型知道工具失败了，同时不泄露原始异常内容。
```

### 自测 5：`ok=false` 是否表示工具崩溃？

参考答案：

```text
不是。ok=false 表示工具正常返回了一个业务失败结果。工具崩溃或无法执行更应该用 is_error=true 表示。
```

### 自测 6：MCP 错误处理和 Java 错误码映射有什么关系？

参考答案：

```text
后续 MCP Tool 调 Java business service 时，Java 的业务错误码要映射成 ok=false 的安全结构；Java 超时、500、契约异常等系统类问题要包装成安全 ToolError 或统一系统错误。
```

### 自测 7：为什么错误路径也必须写测试？

参考答案：

```text
因为 AI Agent 工具最容易出问题的地方就是错误路径。测试能固定错误码、is_error/ok 边界和敏感信息不泄露，防止后续改代码时破坏安全边界。
```

## 本节总结

本节真正要记住的是：

```text
错误处理先分类。
可预期业务失败返回 ok=false。
工具无法执行返回 is_error=true。
原始异常不能直接暴露给模型。
ToolError 可以表达安全的工具执行错误。
error_code 给程序看，message 给模型/用户参考。
details 也必须是安全细节。
错误路径必须写测试。
```

放到项目里：

```text
现在 ai-service 的最小 MCP Server 不只会暴露工具、调试工具和校验参数，也开始具备错误分类能力。
这会直接服务后续真实 query_order/create_ticket MCP Tool：Java 业务错误要安全返回，Java 系统错误要安全包装，Agent 才能稳定决定追问、拒答、重试或转人工。
```

下一节学习：

```text
阶段 8 第 14 节：MCP 安全边界
```
