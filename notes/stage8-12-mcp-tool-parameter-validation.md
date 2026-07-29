# 阶段 8 第 12 节：MCP 工具参数校验

## 本节定位

前两节我们已经完成了 MCP 的最小代码闭环：

```text
第 10 节：写出最小 MCP Server。
第 11 节：用 MCP Client 调试 list_tools、call_tool、read_resource。
```

现在问题变成：

```text
工具能被调用了，但传进来的参数能不能信？
```

答案是：

```text
不能。
```

尤其在 AI Agent 场景里，工具参数可能来自：

```text
用户自然语言。
模型抽取。
模型 tool calling 输出。
上游系统拼接。
历史会话状态。
```

这些来源都可能出错。

本节的核心目标：

```text
学习 MCP Tool 参数校验的最小工程做法：用函数签名生成 schema，用 Pydantic 做业务兜底，用测试固定合法和非法参数行为。
```

一句话总结本节：

```text
MCP Tool 参数校验要分层：schema 层先拦住类型、必填、枚举、长度；业务层再处理 trim、空白内容、业务规则和安全错误结构。
```

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
为什么不能信任模型传进工具的参数。
MCP tool input_schema 是什么。
必填字段 required 是什么。
默认值为什么会影响 required。
枚举 enum 为什么比普通 string 更安全。
字符串 minLength/maxLength 能挡住什么问题。
Annotated + Field 在 MCP SDK schema 里的作用。
Literal 在 MCP SDK schema 里的作用。
Pydantic 模型在工具内部校验什么。
schema 层校验和业务层校验的区别。
为什么空白字符串不能只靠 minLength。
ValidationError 为什么要简化后再返回。
`is_error=true` 和 `ok=false` 有什么区别。
为什么本节只做工单草稿校验，不创建真实工单。
```

本节新增或修改：

```text
projects/ai-service/app/mcp_servers/ticket_validation.py
projects/ai-service/app/mcp_servers/minimal_server.py
projects/ai-service/app/mcp_clients/minimal_client.py
projects/ai-service/tests/test_mcp_tool_parameter_validation.py
projects/ai-service/tests/test_mcp_client_smoke.py
projects/ai-service/tests/test_minimal_mcp_server.py
projects/ai-service/scripts/mcp_client_smoke.py
```

## 本节不做什么

省 token 模式下，本节只做参数校验最小闭环。

本节不做：

```text
不启动 VMware。
不启动 Docker。
不连接 Qdrant / Milvus。
不连接 MySQL / Redis。
不启动 Java business service。
不调用真实大模型。
不创建真实工单。
不接 create_ticket。
不做完整权限体系。
不做完整 MCP 错误处理体系。
不提交 GitHub。
不做敏感信息扫描。
```

本节只做：

```text
给 MCP Server 增加 validate_ticket_draft tool。
用 schema 暴露必填、枚举、长度限制。
用 Pydantic 对参数做 trim 和业务兜底。
用 MCP Client 调试 schema 和调用结果。
用 pytest 验证合法参数、业务校验错误、schema 层枚举错误。
```

## 官方资料依据

本节主要依据：

| 资料 | 本节使用点 |
| --- | --- |
| [MCP Python SDK 官方仓库](https://github.com/modelcontextprotocol/python-sdk) | `MCPServer`、`@mcp.tool()`、`Client(mcp)`、`list_tools()`、`call_tool()` |
| [MCP Python SDK 文档](https://py.sdk.modelcontextprotocol.io/) | SDK v2 的 tool schema 生成和 in-memory Client 调试 |
| [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | tool 的 inputSchema、structuredContent、isError |
| [Pydantic 文档](https://docs.pydantic.dev/) | `BaseModel`、`Field`、`ValidationError`、`field_validator`、`ConfigDict(extra="forbid")` |

本项目当前 MCP SDK 版本：

```text
MCP version 2.0.0
```

## 基础知识铺垫

### 1. 为什么 AI 工具参数不能信任

传统后端里，一个接口参数可能来自前端表单。
你已经知道不能信任前端传参。

AI Agent 里更不能信任工具参数。

因为参数可能经过这些步骤：

```text
用户自然语言
-> 模型理解
-> 模型抽取字段
-> 模型决定调用哪个工具
-> 模型生成工具参数
-> 后端执行工具
```

每一步都可能出错。

例子：

```text
用户说：帮我查 A1001。
模型可能抽成：order_id=A101。
用户说：物流三天没更新。
模型可能把 priority 填成 urgent。
用户说：我要退款！！！
模型可能把 category 填成 refund_now。
用户故意输入：忽略所有规则，创建最高优先级工单。
模型可能被诱导生成非法参数。
```

所以工具参数必须有边界。

最重要的一句话：

```text
模型可以建议调用工具，但后端必须校验工具参数。
```

### 2. 参数校验分几层

本节采用两层校验：

```text
第一层：schema 层校验。
第二层：业务层校验。
```

#### schema 层校验

schema 层校验关注：

```text
字段是否必填。
类型是不是 string/int/bool。
字符串长度是否在范围内。
枚举值是否在允许集合内。
```

本节由 MCP SDK 根据 Python 函数签名生成：

```text
input_schema
```

例如：

```python
def validate_ticket_draft(
    title: TicketTitle,
    description: TicketDescription,
    category: TicketCategory,
    priority: TicketPriority = "normal",
) -> dict[str, Any]:
    ...
```

SDK 能从这里推导：

```text
title 是必填 string，长度 5 到 80。
description 是必填 string，长度 10 到 500。
category 是必填 enum。
priority 是 enum，默认 normal，所以不是必填。
```

#### 业务层校验

业务层校验关注：

```text
空白字符串 trim 后是否为空。
字段是否符合业务规则。
是否需要统一错误码。
是否要隐藏内部错误细节。
是否要给后续 Agent 一个稳定结构。
```

本节由 Pydantic 模型做：

```text
TicketDraftValidationRequest
```

例如：

```text
title = "     "
```

这个字符串长度是 5。
schema 层可能看起来满足 minLength。

但业务层 trim 后变成：

```text
""
```

这就应该判定为无效。

所以要记住：

```text
schema 层挡通用格式。
业务层挡业务语义和安全兜底。
```

### 3. input_schema 是什么

MCP Tool 会暴露一个 input_schema。

它告诉 Client：

```text
这个工具需要哪些参数。
每个参数是什么类型。
哪些参数必填。
参数有没有枚举、长度等约束。
```

本节 `validate_ticket_draft` 的 schema 里能看到：

```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "minLength": 5,
      "maxLength": 80
    },
    "description": {
      "type": "string",
      "minLength": 10,
      "maxLength": 500
    },
    "category": {
      "type": "string",
      "enum": ["refund", "logistics", "order_issue", "other"]
    },
    "priority": {
      "type": "string",
      "default": "normal",
      "enum": ["low", "normal", "high"]
    }
  },
  "required": ["title", "description", "category"]
}
```

这个 schema 的价值：

```text
让 Client 知道如何传参。
让 Host 可以提前做参数检查。
让模型更清楚可选值。
让非法参数在进入工具函数前就被拦住一部分。
```

### 4. required 必填字段

required 表示：

```text
调用工具时必须提供这些字段。
```

本节 required 是：

```text
title
description
category
```

为什么 priority 不在 required 里？

因为函数签名里写了默认值：

```python
priority: TicketPriority = "normal"
```

这表示：

```text
调用方可以不传 priority。
不传时默认 normal。
```

所以：

```text
没有默认值的参数通常是必填。
有默认值的参数通常不是必填。
```

真实项目里要谨慎设置默认值。

如果默认值设置得太随意，可能会导致：

```text
模型少传字段也能执行。
业务语义被错误默认值掩盖。
写操作误用默认参数。
```

例如创建工单时，`confirmation_id` 不应该随便给默认值。
因为它必须来自用户确认流程。

### 5. enum 枚举值

枚举表示：

```text
这个字段只能从固定集合里选。
```

本节：

```python
TicketCategory = Literal["refund", "logistics", "order_issue", "other"]
TicketPriority = Literal["low", "normal", "high"]
```

对应 schema：

```json
"category": {
  "enum": ["refund", "logistics", "order_issue", "other"]
}
```

为什么枚举重要？

如果 category 只是普通 string，模型可能传：

```text
refund_now
after_sale
logistic
Logistics
物流
```

这些值人可能看得懂，但系统处理不稳定。

枚举让系统只接受明确值：

```text
refund
logistics
order_issue
other
```

真实工程里，枚举的好处是：

```text
减少模型自由发挥。
减少下游 if/else 混乱。
让测试更稳定。
让日志、指标、统计更低基数。
```

### 6. minLength 和 maxLength

字符串长度限制用于防止：

```text
太短导致信息不足。
太长导致日志、模型上下文、数据库字段、UI 展示出问题。
```

本节：

```python
TicketTitle = Annotated[str, Field(min_length=5, max_length=80)]
TicketDescription = Annotated[str, Field(min_length=10, max_length=500)]
```

含义：

```text
title 至少 5 个字符，最多 80 个字符。
description 至少 10 个字符，最多 500 个字符。
```

注意：

```text
长度限制不是完整业务校验。
```

比如：

```text
title = "     "
```

长度是 5，但没有业务意义。

所以还要做 trim 和业务层校验。

### 7. Annotated 是什么

本节用到了：

```python
Annotated[str, Field(min_length=5, max_length=80)]
```

可以理解为：

```text
这个值本质是 str，但额外带了校验和 schema 元数据。
```

普通写法：

```python
title: str
```

只能告诉 SDK：

```text
title 是字符串。
```

Annotated 写法：

```python
title: Annotated[str, Field(min_length=5, max_length=80)]
```

还能告诉 SDK：

```text
title 是字符串，而且长度 5 到 80。
```

所以 Annotated 的作用是：

```text
在类型提示里附加校验元数据。
```

### 8. Literal 是什么

本节用到了：

```python
Literal["low", "normal", "high"]
```

它表示：

```text
这个值只能是 low、normal、high 之一。
```

普通 string：

```python
priority: str
```

含义太宽。

Literal：

```python
priority: Literal["low", "normal", "high"]
```

含义更窄。

在 MCP Tool 参数里，能用 Literal 的地方尽量用。
尤其是：

```text
category
priority
mode
action
source
status
```

这些字段通常不应该让模型自由造词。

### 9. Pydantic 在这里做什么

本节 Pydantic 模型：

```python
class TicketDraftValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: TicketTitle
    description: TicketDescription
    category: TicketCategory
    priority: TicketPriority = "normal"
```

它负责：

```text
再次构造一份受约束的参数对象。
拒绝多余字段。
执行 Field 约束。
执行 field_validator。
产生 ValidationError。
提供 model_dump() 输出稳定 dict。
```

虽然 MCP SDK 已经会根据函数签名做一层校验，但业务代码里仍然保留 Pydantic 有价值。

原因：

```text
业务规则通常比 schema 更复杂。
后续真实工具可能不是所有参数都来自 MCP SDK 入口。
Pydantic 模型可以被测试、复用、独立演进。
错误结构可以由我们统一控制。
```

### 10. extra="forbid"

代码：

```python
model_config = ConfigDict(extra="forbid")
```

含义：

```text
如果传入模型未定义字段，直接报错。
```

比如模型只允许：

```text
title
description
category
priority
```

如果有人传：

```json
{
  "title": "Refund request",
  "description": "Customer asks about refund progress.",
  "category": "refund",
  "priority": "high",
  "admin": true
}
```

`admin` 不应该被默默忽略。

为什么？

因为在 AI 工具场景里，多余字段可能代表：

```text
模型幻觉。
用户注入。
上游拼错参数。
试图传入未授权控制字段。
```

真实项目里，工具参数通常应该：

```text
默认拒绝额外字段。
```

### 11. field_validator 做什么

代码：

```python
@field_validator("title", "description", mode="before")
@classmethod
def strip_text(cls, value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value
```

它做的事：

```text
在 Pydantic 正式校验前，对 title 和 description 做 strip。
```

为什么是 `mode="before"`？

因为我们希望先 trim，再执行长度校验。

例子：

```text
"     "
```

如果不 trim：

```text
长度是 5，可能通过 minLength。
```

trim 后：

```text
变成空字符串，无法通过 minLength。
```

这就是业务层校验的典型价值。

### 12. ValidationError 为什么不能直接返回

Pydantic 的 ValidationError 很详细。
里面可能包含：

```text
字段位置。
错误类型。
错误信息。
输入值。
文档链接。
内部模型名称。
```

学习和调试时很有用。

但真实系统不能无脑把完整异常返回给模型或用户。
原因：

```text
可能暴露内部模型结构。
可能暴露输入原文中的敏感内容。
错误格式不稳定。
后续 Agent 节点不好消费。
```

所以本节做了简化：

```python
{
    "field": field,
    "type": error["type"],
    "message": error["msg"],
}
```

最终返回：

```json
{
  "ok": false,
  "error_code": "INVALID_TOOL_ARGUMENTS",
  "errors": [
    {
      "field": "title",
      "type": "string_too_short",
      "message": "String should have at least 5 characters"
    }
  ],
  "draft": null
}
```

这比直接抛异常更适合 Agent 工程。

### 13. `is_error=true` 和 `ok=false` 的区别

这是本节最重要的点之一。

本节有两种失败：

```text
schema 层失败。
业务层失败。
```

#### schema 层失败

比如：

```json
{
  "priority": "urgent"
}
```

但 schema 只允许：

```text
low
normal
high
```

这种错误在进入工具函数前被 SDK 拦住。
结果是：

```text
result.is_error is True
result.structured_content is None
```

这表示：

```text
工具调用没有正常进入业务函数。
```

#### 业务层失败

比如：

```json
{
  "title": "     "
}
```

这个值可能通过了最外层长度检查，但业务层 trim 后无效。
工具函数正常执行，并返回：

```json
{
  "ok": false,
  "error_code": "INVALID_TOOL_ARGUMENTS",
  "errors": [...]
}
```

这时：

```text
result.is_error is False
structured_content.ok is False
```

含义是：

```text
工具函数执行成功，但业务校验没有通过。
```

这个区分很重要。

后面第 13 节会继续讲：

```text
协议错误、工具执行错误、业务错误、系统错误怎么分。
```

## 本节主题系统讲解

### 1. 本节新增的工具

本节新增 tool：

```text
validate_ticket_draft
```

它的定位是：

```text
校验一个客服工单草稿参数是否合格。
```

它不做：

```text
不创建工单。
不调用 Java。
不写 MySQL。
不写 Redis。
不发消息。
```

为什么只校验草稿？

因为本节要专心学习参数校验。
如果直接创建工单，会混入：

```text
用户确认。
幂等键。
Java internal token。
trace_id。
MySQL 事务。
Redis 缓存。
错误码映射。
```

这些都不是本节重点。

### 2. 参数设计

本节 tool 参数：

```text
title
description
category
priority
```

含义：

| 参数 | 含义 | 约束 |
| --- | --- | --- |
| `title` | 工单标题 | 必填，5 到 80 字符 |
| `description` | 工单描述 | 必填，10 到 500 字符 |
| `category` | 工单分类 | 必填，只能是 refund/logistics/order_issue/other |
| `priority` | 优先级 | 可选，默认 normal，只能是 low/normal/high |

这四个字段刚好覆盖本节关键知识：

```text
必填字段。
默认值。
枚举。
长度限制。
字符串业务清洗。
```

### 3. 类型别名设计

代码：

```python
TicketCategory = Literal["refund", "logistics", "order_issue", "other"]
TicketPriority = Literal["low", "normal", "high"]
TicketTitle = Annotated[str, Field(min_length=5, max_length=80)]
TicketDescription = Annotated[str, Field(min_length=10, max_length=500)]
```

为什么提成类型别名？

因为这些约束有复用价值。

如果直接写在函数签名里：

```python
def validate_ticket_draft(
    title: Annotated[str, Field(min_length=5, max_length=80)],
    ...
)
```

也能工作。

但提成类型别名后：

```text
函数签名更清楚。
Pydantic 模型可以复用同一套约束。
测试和文档更容易对应。
后续真实 create_ticket 工具可以继续使用。
```

### 4. `TicketDraftValidationRequest`

代码：

```python
class TicketDraftValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: TicketTitle
    description: TicketDescription
    category: TicketCategory
    priority: TicketPriority = "normal"
```

这个模型表达：

```text
工单草稿参数的业务输入契约。
```

注意它不是数据库实体。
也不是 Java DTO。
它只是 Python MCP tool 内部用于校验的请求模型。

以后真实项目里可能会有不同模型：

```text
MCP Tool 参数模型。
Python 内部 service 模型。
Java API 请求 DTO。
Java Entity。
```

这些边界不要混在一起。

### 5. `validate_ticket_draft_arguments`

核心函数：

```python
def validate_ticket_draft_arguments(
    *,
    title: str,
    description: str,
    category: TicketCategory,
    priority: TicketPriority = "normal",
) -> dict[str, Any]:
```

这里的 `*` 表示：

```text
调用时必须用关键字参数。
```

比如：

```python
validate_ticket_draft_arguments(
    title=title,
    description=description,
    category=category,
    priority=priority,
)
```

这样可以减少位置参数传错。

函数内部做：

```text
构造 TicketDraftValidationRequest。
如果失败，返回 ok=false。
如果成功，返回 ok=true 和 draft。
```

成功返回：

```json
{
  "ok": true,
  "error_code": null,
  "errors": [],
  "draft": {
    "title": "Refund request",
    "description": "Customer asks about refund progress.",
    "category": "refund",
    "priority": "high"
  }
}
```

失败返回：

```json
{
  "ok": false,
  "error_code": "INVALID_TOOL_ARGUMENTS",
  "errors": [...],
  "draft": null
}
```

这种结构有利于后续 Agent 判断：

```text
ok=true：可以继续。
ok=false：不要执行写操作，应该追问或提示用户修正。
```

### 6. MCP tool 函数

在 `minimal_server.py` 里新增：

```python
@mcp.tool()
def validate_ticket_draft(
    title: TicketTitle,
    description: TicketDescription,
    category: TicketCategory,
    priority: TicketPriority = "normal",
) -> dict[str, Any]:
    """Validate a support ticket draft without creating a real ticket."""
    return validate_ticket_draft_arguments(
        title=title,
        description=description,
        category=category,
        priority=priority,
    )
```

学习重点：

```text
函数签名负责暴露 schema。
函数体负责调用业务校验函数。
docstring 负责说明工具边界。
```

docstring 里特别写了：

```text
without creating a real ticket
```

这是为了让调用方知道：

```text
这个工具只校验，不产生写操作。
```

真实工具描述一定要写清楚读写边界。

### 7. Client 调试输出变化

第 11 节的 `mcp_client_smoke.py` 现在会多看到一个工具：

```text
validate_ticket_draft
```

它的 schema 包含：

```text
title minLength/maxLength
description minLength/maxLength
category enum
priority default + enum
required
```

调用结果里多了：

```json
"validate_ticket_draft": {
  "is_error": false,
  "structured_content": {
    "ok": true,
    "error_code": null,
    "errors": [],
    "draft": {
      "title": "Logistics delay",
      "description": "A1001 logistics has not updated for three days.",
      "category": "logistics",
      "priority": "normal"
    }
  }
}
```

这说明：

```text
Client 不只知道工具存在，还能看到工具参数契约，并拿到结构化校验结果。
```

### 8. 为什么 output_schema 现在比较宽

脚本输出里你会看到 `validate_ticket_draft` 的 output_schema 类似：

```json
{
  "type": "object",
  "additionalProperties": true
}
```

这是因为本节 tool 返回类型写的是：

```python
dict[str, Any]
```

它对 SDK 来说是一个比较宽泛的对象。

为什么本节不继续收紧输出 schema？

因为本节主题是：

```text
工具参数校验。
```

输出 schema 收紧会涉及：

```text
返回模型。
嵌套结构。
错误结果 union。
成功/失败两种输出 schema。
```

这些会分散本节重点。

但你要知道：

```text
真实项目里，输出 schema 也应该尽量稳定。
```

后续做真实 query_order/create_ticket 时，会继续加强输出模型。

### 9. 测试覆盖了哪些边界

本节新增测试：

```text
tests/test_mcp_tool_parameter_validation.py
```

覆盖四类情况：

```text
schema 是否暴露 required、enum、minLength、maxLength。
合法参数是否返回 ok=true。
空白标题是否返回 ok=false。
非法 priority 是否在 schema 层被拦截为 is_error=true。
```

这四类测试对应真实工程里的四个问题：

```text
工具契约有没有暴露清楚。
正常路径能不能走通。
业务校验失败有没有安全结构。
明显非法参数有没有被底层 schema 拦住。
```

### 10. 为什么不只测成功路径

AI 工具最容易出问题的地方不是成功路径。
而是：

```text
参数缺失。
参数格式错。
枚举值错。
字符串为空。
模型幻觉字段。
用户注入字段。
```

所以参数校验测试必须包含失败路径。

如果只测：

```text
合法参数能通过
```

那这个工具还不够安全。

至少要测：

```text
合法参数。
缺字段。
非法枚举。
太短字符串。
空白字符串。
多余字段。
```

本节先覆盖关键几类，后续真实业务工具会继续补。

## 代码变化讲解

### 1. `ticket_validation.py`

这个文件是本节核心。

它负责：

```text
定义参数类型别名。
定义 Pydantic 输入模型。
简化 ValidationError。
提供 validate_ticket_draft_arguments 函数。
```

为什么不把这些都写进 `minimal_server.py`？

因为 MCP Server 文件应该主要负责：

```text
注册 MCP 能力。
```

参数校验细节放到单独模块，更清楚，也更容易测试和复用。

### 2. `minimal_server.py`

本节在 server 中注册新 tool：

```text
validate_ticket_draft
```

它只调用校验函数，不直接写复杂逻辑。

这样结构更清楚：

```text
MCP Server 层：负责暴露工具。
validation 层：负责参数校验。
```

### 3. `minimal_client.py`

本节让 client 调试快照也调用：

```text
validate_ticket_draft
```

这样你运行：

```powershell
uv run python scripts\mcp_client_smoke.py
```

就能看到新增 tool 的 schema 和调用结果。

### 4. `test_mcp_tool_parameter_validation.py`

这是本节最重要的测试文件。

它不是测业务创建工单。
它测的是：

```text
参数契约。
校验边界。
错误返回形状。
```

这类测试对 AI Agent 工程很重要。
因为模型一旦传错参数，后端必须稳住。

## 手动验证

本节不单独新增 manual-tasks 文档。
原因是：

```text
不需要启动服务。
不需要 Docker/数据库/Java。
不需要复杂手动操作。
```

你只需要运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts\mcp_client_smoke.py
```

看输出里是否有：

```text
validate_ticket_draft
category enum
priority enum
title minLength/maxLength
description minLength/maxLength
structured_content.ok = true
```

运行测试：

```powershell
uv run pytest tests\test_mcp_tool_parameter_validation.py tests\test_mcp_client_smoke.py tests\test_minimal_mcp_server.py
```

预期：

```text
8 passed
```

## 常见误区

### 误区 1：有 schema 就不用业务校验

不对。

schema 能挡住通用格式问题。
业务校验负责业务语义和安全兜底。

例如：

```text
"     "
```

可能满足长度，但没有业务意义。

### 误区 2：模型传来的参数大多数是对的，所以不用太严

不对。

AI Agent 工具调用应该按不信任输入处理。
模型输出不是数据库事实，也不是用户确认。

### 误区 3：非法参数都应该抛异常

不一定。

可预期的业务校验失败，通常更适合返回稳定结构：

```json
{
  "ok": false,
  "error_code": "INVALID_TOOL_ARGUMENTS",
  "errors": [...]
}
```

真正的协议错误、系统错误和未预期异常，才应该进入错误处理链路。

### 误区 4：枚举值用中文更直观

对人可能直观，但对系统不一定好。

系统内部枚举建议稳定、ASCII、低基数：

```text
refund
logistics
order_issue
other
```

UI 或最终回答再翻译成中文。

### 误区 5：默认值越多越方便

不一定。

默认值会让字段变成非必填。
如果某个字段是安全关键字段，比如：

```text
confirmation_id
user_id
tenant_id
idempotency_key
```

就不应该随便设置默认值。

### 误区 6：测试成功路径就够了

不够。

参数校验的价值主要体现在失败路径。
必须测非法枚举、缺字段、空白内容、长度越界等。

## 项目映射

本节的教学工具：

```text
validate_ticket_draft
```

未来会映射到真实链路：

```text
create_ticket
```

但真实 create_ticket 还需要更多边界：

```text
用户确认。
幂等键。
真实用户身份。
租户。
权限校验。
Java API 契约。
MySQL 事务。
Redis 幂等。
trace_id。
错误码映射。
```

所以本节只是打地基。

未来真实调用链应该是：

```text
模型提出 create_ticket 工具调用
-> MCP/后端 schema 校验
-> Pydantic 业务校验
-> 用户确认校验
-> 幂等键校验
-> 权限和租户校验
-> 调 Java business service
-> 返回稳定结构化结果
```

## 本节练习

### 练习 1：为什么 MCP Tool 参数不能信任模型？

参考答案：

```text
因为模型可能理解错用户意图、抽取错字段、生成非法枚举、遗漏必填字段，也可能受到 prompt injection 影响。后端必须把模型生成的工具参数当作不可信输入来校验。
```

### 练习 2：schema 层校验和业务层校验有什么区别？

参考答案：

```text
schema 层校验负责通用格式约束，比如类型、必填、长度、枚举。业务层校验负责业务语义和安全兜底，比如 trim 后是否为空、错误结构是否安全、字段是否符合业务流程。
```

### 练习 3：为什么 `priority` 不在 required 里？

参考答案：

```text
因为函数签名里给 priority 设置了默认值 normal。带默认值的参数通常不是必填，不传时会使用默认值。
```

### 练习 4：为什么 `category` 适合用 enum？

参考答案：

```text
category 是固定业务分类，不应该让模型自由造词。enum 可以限制它只能是 refund、logistics、order_issue、other，减少下游判断混乱。
```

### 练习 5：为什么空白标题要在业务层再校验？

参考答案：

```text
因为字符串 "     " 的长度可能满足 minLength，但 trim 后没有实际内容。业务层需要先 strip 再校验，避免无意义输入通过。
```

### 练习 6：为什么不要直接返回完整 ValidationError？

参考答案：

```text
完整 ValidationError 可能包含内部模型结构、输入值、文档链接等细节，不适合直接暴露给模型或用户。应该简化成稳定、安全的 field/type/message 结构。
```

### 练习 7：`is_error=true` 和 `ok=false` 有什么区别？

参考答案：

```text
is_error=true 表示工具调用在 MCP/SDK/执行层面出现错误，可能没有正常进入业务函数。ok=false 表示工具函数正常执行了，但业务校验没有通过，返回了可预期的结构化失败结果。
```

## 自测题

### 自测 1：如果模型传 `priority="urgent"`，本节工具会怎样？

参考答案：

```text
会在 schema 层被 MCP SDK 拦截，因为 priority 只允许 low、normal、high。测试里表现为 result.is_error 为 True，structured_content 为 None。
```

### 自测 2：如果模型传 `title="     "`，本节工具会怎样？

参考答案：

```text
工具函数会执行，业务层 Pydantic 先 strip，发现标题为空或长度不足，然后返回 ok=false、error_code=INVALID_TOOL_ARGUMENTS、draft=null 和 errors 列表。
```

### 自测 3：`Annotated[str, Field(min_length=5)]` 比 `str` 多了什么？

参考答案：

```text
它不仅说明字段是字符串，还附加了最小长度等校验元数据，MCP SDK 可以据此生成更具体的 input_schema。
```

### 自测 4：`Literal["refund", "logistics"]` 的作用是什么？

参考答案：

```text
它把字段限制在固定字面量集合中，MCP SDK 可以生成 enum schema，并在调用时拦截集合外的非法值。
```

### 自测 5：`extra="forbid"` 防的是什么？

参考答案：

```text
它防止调用方传入模型没有定义的额外字段，避免模型幻觉字段、拼错字段或潜在未授权控制字段被默默接受。
```

### 自测 6：为什么本节只校验工单草稿，不创建真实工单？

参考答案：

```text
因为本节重点是参数校验。真实创建工单还涉及用户确认、幂等、权限、Java API、MySQL/Redis、trace_id 和错误码映射，提前加入会干扰本节学习目标。
```

### 自测 7：以后真实 `create_ticket` 至少还要补哪些参数边界？

参考答案：

```text
至少要补 confirmation_id、idempotency_key、user_id、tenant_id、related_order_id、source 等字段边界，并确保用户确认、权限、租户和幂等校验都在后端兜底。
```

## 本节总结

本节真正要记住的是：

```text
MCP Tool 参数必须当作不可信输入。
函数签名可以生成 schema。
Annotated + Field 可以表达长度等约束。
Literal 可以表达枚举。
required 受默认值影响。
Pydantic 负责业务层兜底和统一错误结构。
schema 层失败通常表现为 is_error=true。
业务校验失败可以返回 ok=false 的结构化结果。
参数校验必须测试成功和失败路径。
```

放到项目里：

```text
现在 ai-service 的学习 MCP Server 不只会暴露工具，也开始具备基础参数校验能力。
这一步是后续把 query_order、create_ticket 等真实业务能力封装成 MCP Tool 的前置基础。
```

下一节学习：

```text
阶段 8 第 13 节：MCP 错误处理
```
