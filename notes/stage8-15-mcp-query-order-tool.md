# 阶段 8 第 15 节：把订单查询封装成 MCP Tool

## 本节定位

前面几节我们已经把 MCP tool 的基础能力拆开学过：

```text
第 10 节：能写最小 MCP Server。
第 11 节：能用 MCP Client 调试工具。
第 12 节：知道工具参数不能直接信，要校验。
第 13 节：知道业务错误和系统错误要分开处理。
第 14 节：知道工具调用必须有安全边界。
```

这一节开始把这些知识真正放回项目主线。

本节目标是：

```text
把已有订单查询链路封装成 MCP Tool。
```

也就是从这个已有能力：

```text
QueryOrderArgs
-> fake_order_tool.query_order()
-> JavaOrderClient.get_order()
-> Java business service /orders/{order_id}
-> QueryOrderResult
```

变成 MCP 生态里可发现、可调用、可测试的工具：

```text
MCP Client
-> tools/list 看到 query_order
-> tools/call query_order
-> order_tool.query_order_for_mcp()
-> 复用已有订单查询链路
-> 返回 MCP-safe structured_content
```

一句话总结本节：

```text
把业务能力封装成 MCP Tool，不是把 Java API 简单转发出去，而是在 MCP 层做一层适配：参数契约、只读边界、错误分类、输出白名单和测试替身都要清楚。
```

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
为什么 query_order 适合先封装成 MCP Tool。
MCP Tool adapter 是什么。
为什么 MCP Tool 不应该直接写一大坨业务逻辑。
为什么要复用已有 QueryOrderArgs 和 QueryOrderResult。
为什么订单查询属于 read tool。
只读工具为什么仍然需要权限和输出白名单。
MCP tool 参数 schema 和 Pydantic 业务校验分别负责什么。
为什么 Java 返回的原始订单不能原样交给模型。
为什么 ORDER_NOT_FOUND / ORDER_ACCESS_DENIED 不一定是 MCP is_error。
为什么 TOOL_TIMEOUT / TOOL_UPSTREAM_ERROR 更适合 ToolError。
为什么测试里使用 fake client，而不真实启动 Java 服务。
为什么本节不做真实手动联调。
```

本节新增或修改：

```text
projects/ai-service/app/mcp_servers/order_tool.py
projects/ai-service/app/mcp_servers/minimal_server.py
projects/ai-service/app/mcp_clients/minimal_client.py
projects/ai-service/tests/test_mcp_query_order_tool.py
projects/ai-service/tests/test_mcp_client_smoke.py
projects/ai-service/tests/test_minimal_mcp_server.py
README.md
docs/learning-progress.md
```

## 本节不做什么

省 token 模式下，本节不做真实服务联调。

本节不做：

```text
不启动 VMware。
不启动 Docker。
不启动 MySQL / Redis。
不启动 Java business service。
不真实请求 Java HTTP 接口。
不调用真实大模型。
不做 create_ticket MCP Tool。
不做完整用户身份系统。
不做 MCP OAuth。
```

原因很简单：

```text
本节核心是 MCP Tool adapter 的设计和边界，不是手动跑通 Java 服务。
```

自动化测试会用 fake client 固定行为。

后续如果要真实联调，我会明确告诉你要启动 Java 服务和相关依赖。

## 基础知识铺垫

### 1. 什么是 MCP Tool adapter

adapter 可以翻译成“适配器”。

它的作用是：

```text
把一边的接口形式，转换成另一边需要的接口形式。
```

在本节里，两边分别是：

```text
MCP 世界需要的形式：
tool name、input schema、structured_content、is_error。

项目已有业务代码需要的形式：
QueryOrderArgs、JavaOrderClient、QueryOrderResult、AppException。
```

所以 MCP Tool adapter 做的是：

```text
MCP 参数 -> 项目内部参数模型
项目内部结果 -> MCP 安全返回结构
项目内部错误 -> MCP 可理解的错误结构或 ToolError
```

它不是重新写一套订单查询业务。

它是把已有业务能力接到 MCP 协议入口上。

### 2. 为什么不直接在 MCP tool 函数里写 HTTP 调 Java

最简单粗暴的写法可能是：

```python
@mcp.tool()
def query_order(order_id: str):
    response = httpx.get(f"http://java-service/orders/{order_id}")
    return response.json()
```

这个写法不适合工程项目。

问题很多：

```text
参数校验散落在 MCP 函数里。
Java 调用逻辑重复。
错误码映射重复。
字段白名单容易漏。
测试必须真实依赖 HTTP。
以后 Java 接口变化时，MCP 层也要跟着乱改。
```

当前项目已经有：

```text
app/schemas/tool.py
app/tools/fake_order_tool.py
app/services/java_order_client.py
app/services/java_error_mapping.py
```

所以更好的方式是复用它们。

本节新增的 `order_tool.py` 只做 MCP 适配层：

```text
MCP Tool adapter
-> QueryOrderArgs
-> fake_order_tool.query_order()
-> QueryOrderResult
-> MCP-safe dict
```

这样边界更清楚。

### 3. query_order 为什么适合先封装

`query_order` 是只读工具。

只读工具的特点：

```text
不会改变数据库。
不会创建工单。
不会触发退款。
不会修改订单。
```

所以它比写操作更适合先接 MCP。

但只读不等于无风险。

它仍然有这些风险：

```text
用户越权查询别人的订单。
Java 返回了不该给模型看的字段。
模型根据错误信息暴露内部实现。
订单备注里包含 prompt injection。
```

所以只读工具也要有边界。

本节先处理最核心的：

```text
参数校验。
错误分类。
输出白名单。
测试替身。
```

用户身份、租户、权限的完整传递会在后续工程化里继续完善。

### 4. MCP tool 参数 schema 和 Pydantic 校验的区别

本节 MCP tool 暴露：

```text
query_order(order_id)
```

MCP schema 层看到：

```text
order_id 是 string。
长度 1 到 64。
格式只能是字母、数字、下划线、短横线。
```

这层主要帮助：

```text
模型知道参数长什么样。
MCP SDK 提前拦住明显非法参数。
客户端能看到稳定契约。
```

但我们仍然复用 `QueryOrderArgs`。

原因是：

```text
MCP schema 是协议入口约束。
QueryOrderArgs 是项目内部业务参数模型。
```

这两层不冲突。

更好的工程习惯是：

```text
入口层校验一次，内部边界再校验一次。
```

尤其当一个函数可能被多个入口调用时：

```text
FastAPI 可以调用。
Tool Calling 可以调用。
LangChain Tool 可以调用。
MCP Tool 可以调用。
测试也可以直接调用。
```

内部参数模型可以保证无论从哪个入口进来，业务参数都稳定。

### 5. 为什么复用 QueryOrderResult

`QueryOrderResult` 是订单查询工具的安全输出模型。

它只允许这些字段：

```text
order_id
order_status
payment_status
logistics_message
latest_event
can_create_ticket
source
```

并且配置了：

```text
extra="forbid"
```

意思是：

```text
多出来的字段不允许混进结果模型。
```

Java 原始订单里可能有：

```text
customer_id
customer_phone
customer_id_card
internal_note
debug_stack
raw_sql
```

这些不能直接给模型。

所以当前链路先经过：

```text
map_java_order_to_query_order_payload()
```

它只挑安全字段。

然后再经过：

```text
QueryOrderResult.model_validate()
```

它确认字段类型和枚举值都合法。

这就是输出白名单。

### 6. 业务错误和工具错误怎么分

第 13 节学过错误处理。

本节把它落到真实订单查询。

业务错误：

```text
ORDER_ID_INVALID
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
```

这些错误说明：

```text
工具链路是正常的。
只是这次业务查询不能给出成功订单结果。
```

所以本节把它们返回为：

```text
structured_content.ok = false
is_error = false
```

这样模型可以根据安全错误码回答用户：

```text
订单不存在，请确认订单号。
当前账号无权查看这个订单。
订单号格式不正确。
```

工具错误：

```text
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TOOL_RESULT_VALIDATION_FAILED
TOOL_CALL_FAILED
```

这些说明：

```text
工具没有可靠完成执行。
```

例如：

```text
Java 服务超时。
Java 服务不可用。
Java 返回结构不符合契约。
未知异常。
```

这些更适合变成安全 `ToolError`。

注意：

```text
ToolError 里也不能放内部 HTTP 地址、堆栈、字段细节、数据库信息。
```

只能放安全消息。

### 7. 为什么测试不真实调用 Java

本节是 MCP adapter 的自动化测试。

自动化测试不应该依赖：

```text
Java 服务是否启动。
MySQL 是否启动。
Redis 是否启动。
VMware 网络是否正常。
本机端口是否被占用。
```

这些属于集成环境问题。

如果单元测试依赖这些东西，就会变得：

```text
慢。
不稳定。
难排查。
换机器容易失败。
```

所以本节使用：

```text
FakeOrderLookupClient
```

它模拟 JavaOrderClient：

```text
正常返回订单。
抛出 ORDER_NOT_FOUND。
抛出 ORDER_ACCESS_DENIED。
抛出 TOOL_TIMEOUT。
抛出 TOOL_RESULT_VALIDATION_FAILED。
```

这样可以稳定测试 MCP adapter 的行为。

真实 Java 联调以后可以单独做 smoke。

### 8. 本节和第 14 节安全边界的关系

第 14 节是抽象演示。

第 15 节是真实落地。

对应关系：

| 第 14 节概念 | 第 15 节落地 |
| --- | --- |
| 工具最小暴露 | 只新增 `query_order`，不暴露 `run_raw_sql` |
| 读写分级 | `query_order` 标记为 read，不需要用户确认 |
| 输入校验 | `OrderId` schema + `QueryOrderArgs` |
| 输出白名单 | `map_java_order_to_query_order_payload()` + `QueryOrderResult` |
| 业务错误结构化 | `ORDER_NOT_FOUND` 返回 `ok=false` |
| 系统错误安全包装 | `TOOL_TIMEOUT` 转 `ToolError` |
| 不泄露敏感字段 | 测试确认 `customer_id` 等值不进入 MCP 返回 |

这就是从“概念”到“项目代码”的连接。

## 本节主题系统讲解

### 1. 新增文件 `order_tool.py`

文件：

```text
projects/ai-service/app/mcp_servers/order_tool.py
```

它的定位：

```text
MCP query_order tool adapter。
```

也就是说它不负责：

```text
不直接写 HTTP 请求。
不直接拼 Java URL。
不直接解析 Java 错误码。
不直接返回 Java 原始响应。
```

它负责：

```text
把 MCP 入参变成 QueryOrderArgs。
调用已有 query_order 业务工具。
把 QueryOrderResult 变成 MCP-safe dict。
把 AppException 分成业务错误和工具错误。
```

### 2. `OrderId`

代码：

```python
OrderId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Order id to query, for example A1001.",
    ),
]
```

它的作用是给 MCP tool 参数生成 schema。

模型和客户端可以看到：

```text
order_id 必填。
order_id 是字符串。
长度 1 到 64。
只能包含字母、数字、下划线、短横线。
```

这对模型很重要。

工具 schema 越清楚，模型越不容易传错参数。

但注意：

```text
schema 只是第一层。
```

后面仍然会创建：

```python
QueryOrderArgs(order_id=order_id)
```

这就是内部二次校验。

### 3. `BUSINESS_ORDER_ERROR_CODES`

代码：

```python
BUSINESS_ORDER_ERROR_CODES = {
    "ORDER_ID_INVALID",
    "ORDER_NOT_FOUND",
    "ORDER_ACCESS_DENIED",
}
```

这组错误码表示：

```text
工具执行链路正常，但业务上无法返回订单。
```

所以本节不会把它们转成 `ToolError`。

而是返回：

```json
{
  "ok": false,
  "allowed": true,
  "error_code": "ORDER_NOT_FOUND",
  "message": "订单不存在，请确认订单号是否正确。",
  "result": null
}
```

为什么 `allowed=true`？

因为：

```text
查询这个动作本身允许。
只是业务结果失败。
```

如果是权限不足，也可以理解为：

```text
工具被允许接收这个查询请求，但业务权限判断拒绝返回订单。
```

模型看到后应该解释给用户，而不是重试。

### 4. `_mcp_query_order_response()`

这个函数统一成功和业务失败的返回结构。

核心字段：

```text
ok
allowed
action
action_type
requires_confirmation
error_code
message
retryable
security_checks
result
```

为什么不直接返回 `QueryOrderResult.model_dump()`？

因为 MCP tool 返回给模型的结果最好有上下文。

模型需要知道：

```text
这是不是成功。
这是什么动作。
这是读操作还是写操作。
是否需要用户确认。
有没有错误码。
结果是否已经做过输出白名单。
```

这些信息可以让上层 Agent 更稳定地处理。

### 5. `_invalid_arguments_response()`

如果内部 `QueryOrderArgs` 校验失败，本节返回：

```text
ok=false
allowed=false
error_code=INVALID_TOOL_ARGUMENTS
```

这表示：

```text
参数本身不应该进入业务查询。
```

注意测试里会确认错误详情不包含原始 input。

原因是：

```text
错误详情也可能泄露不该返回的内容。
```

### 6. `_raise_safe_tool_error()`

工具级错误进入这里。

例如：

```text
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TOOL_RESULT_VALIDATION_FAILED
```

本节不会把内部 message 原样抛出。

例如内部可能是：

```text
read timeout: http://java-business-service
字段 customer_id_card 不符合内部契约
```

这些不应该进入模型上下文。

所以统一包装成：

```text
TOOL_TIMEOUT: 订单查询工具调用超时，请稍后重试。
TOOL_RESULT_VALIDATION_FAILED: 订单查询工具暂时不可用，请稍后重试。
```

这就是安全错误包装。

### 7. `query_order_for_mcp()`

这是本节核心函数。

执行顺序：

```text
1. 用 QueryOrderArgs 校验 order_id。
2. 调用已有 run_query_order。
3. 如果成功，把 QueryOrderResult 转成 JSON-safe dict。
4. 如果是业务错误，返回 ok=false。
5. 如果是工具/系统错误，抛出安全 ToolError。
```

伪代码可以这样理解：

```text
validate order_id
try:
    result = query_order(arguments)
except business error:
    return ok=false
except system error:
    raise safe ToolError
return ok=true + safe result
```

它体现了一个很重要的工程原则：

```text
MCP adapter 只做适配，不重新实现业务。
```

### 8. `minimal_server.py` 注册工具

新增：

```python
@mcp.tool()
def query_order(order_id: order_tool.OrderId) -> dict[str, Any]:
    return order_tool.query_order_for_mcp(order_id)
```

这段代码很薄。

它只做两件事：

```text
把 query_order 暴露成 MCP tool。
把调用转交给 order_tool.query_order_for_mcp。
```

为什么工具函数要薄？

因为：

```text
注册层越薄，越容易测试。
安全和业务适配逻辑越集中，越容易维护。
```

### 9. `minimal_client.py` 为什么只 list，不真实 call

本节 MCP debug snapshot 会看到 `query_order` 出现在 tools 列表里。

但默认 smoke 脚本不真实调用 `query_order`。

原因是：

```text
真实调用需要 Java 服务可用。
自动 smoke 不应该因为 Java 没启动而失败。
```

本节通过测试里的 fake adapter 验证 MCP client 能调用。

这比在 smoke 里硬调真实 Java 更稳定。

## 返回结构示例

### 成功

```json
{
  "ok": true,
  "allowed": true,
  "action": "query_order",
  "action_type": "read",
  "requires_confirmation": false,
  "error_code": null,
  "message": "订单查询成功。",
  "retryable": false,
  "security_checks": {
    "input_validated": true,
    "output_allowlist_applied": true,
    "sensitive_fields_returned": false
  },
  "result": {
    "order_id": "A1001",
    "order_status": "waiting_shipment",
    "payment_status": "paid",
    "logistics_message": "商家已接单，等待仓库发货。",
    "latest_event": "仓库正在准备出库。",
    "can_create_ticket": true,
    "source": "java_mock_service"
  }
}
```

### 订单不存在

```json
{
  "ok": false,
  "allowed": true,
  "action": "query_order",
  "action_type": "read",
  "requires_confirmation": false,
  "error_code": "ORDER_NOT_FOUND",
  "message": "订单不存在，请确认订单号是否正确。",
  "result": null
}
```

### 上游超时

```text
ToolError:
TOOL_TIMEOUT: 订单查询工具调用超时，请稍后重试。
```

## 测试部分简讲

新增测试：

```text
projects/ai-service/tests/test_mcp_query_order_tool.py
```

重点覆盖：

```text
MCP schema 暴露 order_id 契约。
query_order_for_mcp 成功返回安全字段。
Java 原始敏感字段不会进入 MCP 返回。
ORDER_NOT_FOUND 返回 ok=false。
ORDER_ACCESS_DENIED 返回 ok=false。
非法 order_id 返回 INVALID_TOOL_ARGUMENTS。
TOOL_TIMEOUT 转安全 ToolError。
TOOL_RESULT_VALIDATION_FAILED 不泄露内部字段细节。
MCP Client 可以通过 fake adapter 调用 query_order。
```

测试里的重点不是“为了写测试而写测试”。

重点是证明三件事：

```text
工具能被 MCP 发现。
工具结果不会泄露敏感字段。
错误边界符合第 13、14 节规则。
```

## 和真实 Java 服务的关系

本节没有改 Java 服务。

但真实链路已经清楚：

```text
MCP query_order
-> order_tool.query_order_for_mcp()
-> fake_order_tool.query_order()
-> JavaOrderClient.get_order()
-> Java business service
```

以后真实联调时，需要关注：

```text
Java 服务地址配置是否正确。
Java 服务是否启动。
MySQL/Redis 是否启动。
X-Trace-Id 是否贯通。
X-User-Id / X-Tenant-Id / X-Internal-Token 是否按契约传递。
Java 返回字段是否符合 Python 的 QueryOrderResult 契约。
```

但这些不是本节自动化测试的责任。

## 本节常见误区

### 误区 1：MCP Tool 就是把 HTTP API 包一层

不准确。

MCP Tool 是 AI 应用能看到的能力入口。

它需要额外考虑：

```text
模型可见描述。
参数 schema。
业务错误结构。
工具错误。
输出给模型的字段。
权限和确认边界。
```

### 误区 2：只读工具不用安全边界

不对。

只读工具不会改数据，但可能泄露数据。

订单查询尤其要注意：

```text
查谁的订单。
能不能看。
返回哪些字段。
错误消息会不会泄露内部细节。
```

### 误区 3：Java 返回什么，MCP 就返回什么

不对。

Java 返回的是业务服务响应。

MCP 返回的是给模型看的工具结果。

中间必须有字段映射和白名单。

### 误区 4：所有 AppException 都返回 ok=false

不对。

业务错误适合 `ok=false`。

系统错误、上游不可用、结果契约异常更适合 `ToolError`。

因为模型不能把系统故障当成正常业务结果继续推理。

### 误区 5：自动测试必须真实启动 Java

不对。

本节测的是 MCP adapter。

adapter 测试应该用 fake client。

真实 Java 联调应该单独做 smoke 或集成测试。

## 本节真正学会了什么

这一节真正的知识点是：

```text
如何把一个已有业务能力工程化地接入 MCP，而不是写一个玩具 demo。
```

关键步骤：

```text
1. 复用已有内部参数模型。
2. 复用已有业务工具链路。
3. 复用已有输出模型做白名单。
4. 在 MCP adapter 层统一返回结构。
5. 区分业务错误和工具错误。
6. 用 fake client 做稳定测试。
7. 只把 query_order 这种受控只读能力暴露出去。
```

你现在应该能讲清楚：

```text
MCP 不是替代 Java 后端，而是让 AI 应用通过标准协议调用受控业务能力。真实业务逻辑仍然在 Java 和已有 Python adapter 里，MCP 层负责把这些能力安全、结构化、可测试地暴露给 AI。
```

## 手动运行方式

本节没有单独手动验证文档。

你可以在 `projects/ai-service` 下运行：

```powershell
uv run pytest tests\test_mcp_query_order_tool.py tests\test_fake_order_tool.py tests\test_mcp_client_smoke.py tests\test_minimal_mcp_server.py
```

也可以看 MCP tool 列表：

```powershell
uv run python scripts\mcp_client_smoke.py
```

注意：

```text
这个 smoke 脚本默认只展示 query_order 已经暴露在 tools/list 里，不真实调用 Java。
```

如果以后要做真实 Java 联调，我会提前告诉你需要启动哪些服务。

## 练习题

### 练习 1：为什么本节新增的是 `order_tool.py`，而不是直接在 `minimal_server.py` 里写全部逻辑？

参考答案：

```text
因为 minimal_server.py 应该主要负责 MCP tool 注册。如果把参数校验、业务调用、错误映射、输出过滤都写在注册函数里，文件会变得混乱，也不利于测试。order_tool.py 作为 adapter 层，可以集中处理 MCP 和项目内部业务链路之间的转换。
```

### 练习 2：为什么 query_order 是 read tool，但仍然要做输出白名单？

参考答案：

```text
因为只读工具虽然不修改数据，但可能泄露数据。Java 原始订单可能包含 customer_id、手机号、身份证、内部备注、调试信息等字段。MCP 返回会进入模型上下文，模型可能把这些字段说给用户，所以必须通过字段映射和 QueryOrderResult 白名单过滤。
```

### 练习 3：ORDER_NOT_FOUND 为什么返回 `ok=false`，而不是直接抛 ToolError？

参考答案：

```text
因为订单不存在是可预期的业务结果，说明工具链路正常，只是业务上没有查到订单。返回 ok=false 和 ORDER_NOT_FOUND 后，模型可以给用户正常解释，让用户检查订单号。ToolError 更适合上游超时、服务不可用、返回结构不符合契约等工具无法可靠执行的情况。
```

### 练习 4：为什么测试里用 `FakeOrderLookupClient`？

参考答案：

```text
因为本节测试的是 MCP adapter 的行为，不是测试 Java 服务是否启动。FakeOrderLookupClient 可以稳定模拟成功、业务错误、超时、结果异常等情况，让测试快速、稳定、不依赖外部服务。
```

### 练习 5：如果 Java 返回了 `customer_phone`，本节 MCP 返回里会有吗？为什么？

参考答案：

```text
不会。已有 `map_java_order_to_query_order_payload()` 只挑选允许返回的字段，`QueryOrderResult` 又使用 `extra="forbid"` 固定输出契约，所以额外敏感字段不会进入 MCP 返回。
```

## 自测题

### 自测 1：MCP Tool adapter 的三件核心工作是什么？

参考答案：

```text
把 MCP 入参转换成项目内部参数模型；把项目内部结果转换成 MCP 安全返回结构；把项目内部错误转换成业务错误结构或安全 ToolError。
```

### 自测 2：本节 query_order 的真实业务调用链路是什么？

参考答案：

```text
MCP query_order -> order_tool.query_order_for_mcp() -> fake_order_tool.query_order() -> JavaOrderClient.get_order() -> Java business service -> QueryOrderResult -> MCP structured_content。
```

### 自测 3：`allowed=true` 但 `ok=false` 可能表示什么？

参考答案：

```text
表示工具动作本身允许执行，但业务结果失败，比如订单不存在或当前账号无权查看订单。这和工具系统故障不同，不一定需要 ToolError。
```

### 自测 4：`TOOL_RESULT_VALIDATION_FAILED` 为什么不把内部字段详情返回给模型？

参考答案：

```text
因为结果校验失败可能包含内部字段名、上游契约细节或敏感字段信息。模型不需要知道这些内部细节，只需要知道订单查询工具暂时不可用。详细信息应该进入日志和测试，不进入模型上下文。
```

### 自测 5：为什么本节 smoke 脚本不默认真实调用 query_order？

参考答案：

```text
因为真实调用需要 Java 服务和依赖环境可用。默认 smoke 应该稳定展示 MCP server 能力，不应该因为外部服务没启动而失败。真实联调应该单独进行。
```

## 面试表达

如果别人问：

```text
你是怎么把订单查询接入 MCP 的？
```

可以这样回答：

```text
我没有把 Java HTTP 接口直接暴露给模型，而是在 Python ai-service 里加了一层 MCP adapter。MCP tool 只暴露 query_order 这个受控只读能力，参数通过 schema 和 QueryOrderArgs 校验，内部复用已有 JavaOrderClient 查询订单，Java 原始返回先映射成 QueryOrderResult 白名单字段，再返回给 MCP structured_content。业务错误如 ORDER_NOT_FOUND、ORDER_ACCESS_DENIED 返回 ok=false，系统错误如超时、上游不可用、结果契约失败会包装成安全 ToolError，不泄露内部细节。
```

如果别人问：

```text
为什么不直接让模型调用 Java 接口？
```

可以这样回答：

```text
模型不能成为业务系统的直接调用方。中间需要 MCP/Python adapter 做工具白名单、参数校验、权限上下文、错误映射和输出过滤。这样 Java 后端仍然保持传统业务边界，AI 只是通过受控工具访问必要能力。
```

## 本节小结

本节完成了阶段 8 的第一个真实 MCP 业务工具：

```text
query_order
```

你需要记住：

```text
MCP Tool 接业务系统时，核心不是“能调通”，而是“调得安全、结构清楚、错误可控、测试稳定”。
```

下一节进入：

```text
阶段 8 第 16 节：把创建工单封装成 MCP Tool
```

下一节会比本节更严格，因为创建工单是写操作，需要用户确认、幂等键和身份传递边界。
