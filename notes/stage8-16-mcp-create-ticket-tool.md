# 阶段 8 第 16 节：把创建工单封装成 MCP Tool

## 本节定位

上一节我们完成了：

```text
阶段 8 第 15 节：把订单查询封装成 MCP Tool。
```

`query_order` 是只读工具。

这一节进入更重要的一类工具：

```text
写操作工具。
```

本节要把已有的创建工单链路封装成 MCP Tool：

```text
MCP create_ticket
-> ticket_tool.create_ticket_for_mcp()
-> CreateTicketArgs
-> user_confirmed / confirmation_id 检查
-> run_idempotent_tool()
-> TicketCreator / JavaTicketClient
-> CreatedTicket
-> MCP-safe structured_content
```

一句话总结本节：

```text
创建工单是写操作，MCP adapter 不能只负责“调通 Java”，还必须负责确认边界、幂等边界、参数契约、业务错误结构化和系统错误安全包装。
```

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
为什么 create_ticket 是 write tool。
write tool 和 read tool 的风险有什么不同。
为什么模型不能直接创建工单。
为什么用户确认必须在写操作之前。
confirmation_id 是什么。
Idempotency-Key 是什么。
confirmation_id 和 Idempotency-Key 的区别是什么。
为什么当前项目可以用 confirmation_id 作为幂等键。
MCP adapter 为什么要调用 authorize_tool_call。
CreateTicketArgs 在 MCP 写工具中的作用。
CreatedTicket 为什么不能原样全部返回给模型。
TICKET_ALREADY_EXISTS 为什么是业务错误。
IDEMPOTENCY_KEY_CONFLICT 为什么不是普通系统故障。
TOOL_TIMEOUT 为什么要包装成安全 ToolError。
为什么写操作测试必须证明“未确认不会调用 creator”。
为什么本节测试继续用 fake client，不真实调用 Java。
```

本节新增或修改：

```text
projects/ai-service/app/mcp_servers/ticket_tool.py
projects/ai-service/app/mcp_servers/minimal_server.py
projects/ai-service/tests/test_mcp_create_ticket_tool.py
projects/ai-service/tests/test_mcp_client_smoke.py
projects/ai-service/tests/test_minimal_mcp_server.py
README.md
docs/learning-progress.md
```

## 本节不做什么

省 token 模式下，本节仍然不做外部服务联调。

本节不做：

```text
不启动 VMware。
不启动 Docker。
不启动 MySQL / Redis。
不启动 Java business service。
不真实请求 Java POST /tickets。
不调用真实大模型。
不做完整 MCP OAuth。
不把真实登录用户体系接进来。
不把 confirmation store 和 MCP tool 做完整生产级绑定。
```

本节先完成最小但完整的 MCP 写操作边界：

```text
必须确认。
必须有 confirmation_id。
确认后使用 confirmation_id 做幂等键。
复用已有 JavaTicketClient 这类 creator。
只返回安全字段。
```

## 基础知识铺垫

### 1. 什么是写操作工具

写操作工具是会改变真实业务状态的工具。

例如：

```text
create_ticket
cancel_order
update_address
refund_order
reset_password
```

这些工具和只读工具不一样。

只读工具主要风险是：

```text
越权读取。
敏感字段泄露。
错误信息泄露。
```

写操作工具除了这些风险，还会带来：

```text
误创建。
重复创建。
错误修改。
不可逆业务影响。
用户没确认但系统已经执行。
模型误判意图导致错误写入。
超时后用户重复提交导致重复工单。
```

所以写工具要更严格。

### 2. 为什么模型不能直接创建工单

模型可以做很多事情：

```text
理解用户意图。
整理工单标题。
总结工单描述。
判断分类和优先级。
提出要创建工单。
```

但模型不能直接决定：

```text
现在就写入业务系统。
```

原因是：

```text
模型可能理解错。
用户可能只是问问。
上下文可能被污染。
RAG 文档可能有 prompt injection。
用户可能没有看到最终工单内容。
```

所以正确边界是：

```text
模型提出计划。
后端生成确认内容。
用户确认。
后端执行写操作。
```

模型是建议者。

后端是执行裁决者。

用户确认是写入前的最后人工边界。

### 3. 用户确认解决什么问题

用户确认解决的是：

```text
这次写操作是不是用户明确同意的。
```

例如模型整理出：

```text
标题：订单 A1001 一直未发货
描述：订单 A1001 已付款一周仍未发货，请帮我处理。
分类：complaint
优先级：high
关联订单：A1001
```

用户需要有机会看到这些内容。

如果用户说：

```text
确认创建。
```

后端才允许进入写操作。

如果用户没有确认，后端应该返回：

```text
TOOL_CONFIRMATION_REQUIRED
```

这不是模型礼貌问题。

这是业务安全边界。

### 4. confirmation_id 是什么

`confirmation_id` 可以理解为：

```text
某次用户确认的编号。
```

它通常绑定：

```text
确认人。
工具名。
工具参数。
过期时间。
确认状态。
```

在已有项目里，确认流程已经出现过：

```text
用户请求创建工单。
后端生成待确认记录。
用户确认这个记录。
执行时根据 confirmation_id 取回已确认的参数。
```

所以 `confirmation_id` 的核心作用是：

```text
证明这次写操作不是模型直接发起的，而是来自某个被用户确认过的计划。
```

本节 MCP adapter 做的是最小版本：

```text
要求 user_confirmed=true。
要求 confirmation_id 符合 32 位十六进制格式。
用 confirmation_id 作为本次写操作的确认凭据和幂等键。
```

生产级实现还要把它和确认记录存储严格绑定。

### 5. Idempotency-Key 是什么

Idempotency-Key 可以理解为：

```text
防重复提交的请求编号。
```

它解决的是另一个问题：

```text
同一次写操作，因为网络超时、重试、用户重复点击，可能被提交多次。
```

没有幂等键时：

```text
第一次请求创建了工单，但响应超时。
用户或系统重试。
第二次又创建一个工单。
```

结果就是重复工单。

有幂等键时：

```text
第一次请求 key=abc，创建 T1001。
第二次还是 key=abc，参数也一样。
系统返回同一个结果 T1001，不重复创建。
```

如果同一个幂等键配了不同参数：

```text
第一次 key=abc，标题是“订单未发货”。
第二次 key=abc，标题变成“申请退款”。
```

系统应该拒绝：

```text
IDEMPOTENCY_KEY_CONFLICT
```

因为同一个幂等键不能代表两个不同写操作。

### 6. confirmation_id 和 Idempotency-Key 的区别

这两个概念容易混。

它们解决的问题不同：

| 概念 | 解决的问题 | 关注点 |
| --- | --- | --- |
| `confirmation_id` | 用户是否确认过 | 人和意图 |
| `Idempotency-Key` | 重复提交是否会重复写 | 请求和结果 |

一句话区分：

```text
confirmation_id 证明“用户同意过这件事”。
Idempotency-Key 保证“这件事重复提交也只做一次”。
```

当前项目为了简单：

```text
使用 confirmation_id 作为 idempotency_key。
```

这在学习项目里是合理的，因为：

```text
一次确认对应一次写操作。
同一次确认重复执行，应该拿到同一个结果。
同一个确认改了参数，应该冲突。
```

生产系统也可以这么做，但必须保证：

```text
confirmation_id 真正绑定用户、工具和参数。
```

### 7. 为什么创建工单需要幂等

创建工单是典型写操作。

写操作常见问题：

```text
请求发出后服务端已经写入，但客户端没收到响应。
客户端以为失败，再发一次。
模型或编排层遇到 timeout 后重试。
用户重复点击确认。
网络抖动导致代理重发。
```

如果没有幂等，系统可能创建多条重复工单。

工单重复看起来不严重，但在真实业务里会带来：

```text
客服重复处理。
用户收到多次通知。
工单统计异常。
后续退款或投诉流程重复触发。
```

所以写操作的基本工程习惯是：

```text
能幂等就必须幂等。
```

### 8. 为什么 CreatedTicket 不能原样全部返回给模型

Java 返回的 `CreatedTicket` 包含：

```text
ticket_id
requester_id
title
description
category
priority
related_order_id
created_at
```

不是所有字段都必须返回给模型。

例如：

```text
requester_id 是内部用户标识。
description 可能包含用户手机号、地址、身份证、隐私描述。
```

模型最终回答通常只需要：

```text
ticket_id
title
category
priority
related_order_id
created_at
```

所以本节新增：

```text
sanitize_created_ticket()
```

它只返回最小安全字段。

这就是写操作的输出白名单。

### 9. 业务错误和工具错误怎么分

本节业务错误包括：

```text
ORDER_NOT_SUPPORT_TICKET
TICKET_ALREADY_EXISTS
TICKET_REQUEST_INVALID
IDEMPOTENCY_KEY_CONFLICT
```

这些说明：

```text
工具链路可以正常工作，但业务上拒绝或无法完成这次创建。
```

所以返回：

```text
ok=false
is_error=false
```

工具错误包括：

```text
TOOL_TIMEOUT
TOOL_UPSTREAM_ERROR
TOOL_RESULT_VALIDATION_FAILED
未知异常
```

这些说明：

```text
工具执行没有可靠完成。
```

所以包装成安全 `ToolError`。

写操作的 timeout 要特别谨慎。

因为超时不代表一定没写入。

所以本节 timeout 消息会提醒：

```text
已使用幂等键保护，请稍后查询结果或重试同一确认。
```

这比简单说“失败了”更准确。

### 10. 为什么本节不真实调用 Java

本节测试目标是：

```text
MCP 写操作 adapter 的边界是否正确。
```

不是真实验证：

```text
Java 服务是否启动。
MySQL 是否可用。
Redis 是否可用。
VMware 网络是否正常。
```

所以测试使用：

```text
FakeTicketCreator
```

它可以稳定模拟：

```text
创建成功。
业务错误。
超时。
结果异常。
未知异常。
```

这样可以证明：

```text
未确认时不会调用 creator。
确认后才调用 creator。
同一个 confirmation_id 只执行一次。
同 key 不同参数会冲突。
内部错误不会泄露给模型。
```

这些才是本节重点。

## 本节主题系统讲解

### 1. 新增文件 `ticket_tool.py`

文件：

```text
projects/ai-service/app/mcp_servers/ticket_tool.py
```

它的定位：

```text
MCP create_ticket tool adapter。
```

它不直接关心：

```text
HTTP 怎么调用 Java。
Java 怎么写 MySQL。
Redis 怎么存幂等。
前端怎么展示确认弹窗。
```

它只关心：

```text
MCP 入参是否符合创建工单契约。
这次写操作是否已确认。
幂等键是否可用。
如何调用已有 creator。
如何把结果安全返回给模型。
如何把错误安全分类。
```

### 2. 输入类型别名

本节定义：

```text
RequesterId
TicketTitle
TicketDescription
RelatedOrderId
ConfirmationId
```

这些类型别名主要用于 MCP schema。

例如：

```python
ConfirmationId = Annotated[
    str,
    Field(pattern=r"^[a-f0-9]{32}$")
]
```

这会让 MCP tool schema 明确告诉客户端：

```text
confirmation_id 必须是 32 位小写十六进制字符串。
```

这样模型和 MCP client 都能看到参数规则。

### 3. `McpCreateTicketRequest`

这个模型是 MCP 层的请求模型。

它包含：

```text
requester_id
title
description
category
confirmation_id
priority
related_order_id
user_confirmed
```

为什么不用 `CreateTicketArgs` 直接当 MCP 请求？

因为 MCP 请求比 Java 创建工单参数多两个边界字段：

```text
confirmation_id
user_confirmed
```

`CreateTicketArgs` 是给 Java 的业务命令。

`McpCreateTicketRequest` 是给 MCP 写工具的执行请求。

这两个模型职责不同。

### 4. `TicketCreator` 协议

代码定义：

```text
TicketCreator.create_ticket(arguments, idempotency_key)
```

这个协议让 MCP adapter 不依赖具体 Java client。

生产时可以用：

```text
JavaTicketClient
```

测试时可以用：

```text
FakeTicketCreator
```

这就是依赖倒置。

好处是：

```text
测试不需要启动 Java。
MCP adapter 可以独立验证。
真实 client 仍然复用已有实现。
```

### 5. `sanitize_created_ticket()`

这个函数只返回：

```text
ticket_id
title
category
priority
related_order_id
created_at
```

它故意不返回：

```text
requester_id
description
```

原因是：

```text
模型最终只需要知道工单创建成功和核心摘要。
```

`description` 可能很长，也可能包含用户隐私。

`requester_id` 是内部身份字段。

所以不返回。

这就是第 14 节输出白名单在写操作上的落地。

### 6. `create_ticket_for_mcp()` 执行顺序

核心顺序：

```text
1. 如果 user_confirmed=false，直接拒绝，不调用 creator。
2. 校验 MCP 请求参数。
3. 构造 CreateTicketArgs。
4. authorize_tool_call("create_ticket", user_confirmed=True)。
5. 使用 confirmation_id 作为幂等键。
6. 调用 creator.create_ticket()。
7. 成功后返回安全 ticket 字段。
8. 业务错误返回 ok=false。
9. 系统错误包装成安全 ToolError。
```

这个顺序很重要。

尤其第一步：

```text
未确认直接拒绝。
```

测试也专门证明：

```text
creator.calls == []
```

也就是没有任何真实写入。

### 7. 为什么先检查 `user_confirmed`

如果用户没确认，本节直接返回：

```text
TOOL_CONFIRMATION_REQUIRED
```

这比先执行参数校验更贴近安全思路。

因为写操作最重要的前置条件是：

```text
用户有没有确认。
```

没有确认，就不进入业务执行。

### 8. 为什么还要调用 `authorize_tool_call`

即使前面已经判断了 `user_confirmed=true`，仍然调用：

```text
authorize_tool_call("create_ticket", user_confirmed=True)
```

这是为了复用工具注册表里的规则。

注册表中 `create_ticket` 是：

```text
access_level=WRITE
requires_confirmation=True
enabled=True
```

如果以后配置改成禁用，或者规则变严，MCP adapter 不应该绕过。

这体现了：

```text
安全规则集中管理。
入口层复用规则。
```

### 9. 幂等执行怎么落地

本节调用：

```text
run_idempotent_tool(
    "create_ticket",
    arguments,
    request.confirmation_id,
    lambda: ticket_creator.create_ticket(...),
)
```

这里把：

```text
confirmation_id
```

作为：

```text
idempotency_key
```

结果是：

```text
同一个 confirmation_id + 同一组参数 -> 返回同一个结果，不重复创建。
同一个 confirmation_id + 不同参数 -> IDEMPOTENCY_KEY_CONFLICT。
```

测试里已经固定这两个行为。

### 10. MCP schema 里的 enum 为什么出现在 `$defs`

本节测试发现：

```text
TicketCategory
TicketPriority
```

这类 `StrEnum` 在 MCP input schema 里不是直接写在：

```text
properties.category.enum
```

而是写在：

```text
$defs.TicketCategory.enum
properties.category.$ref
```

这仍然是标准 JSON Schema。

意思是：

```text
category 引用 $defs 里定义的枚举。
```

你需要知道：

```text
JSON Schema 既可以内联 enum，也可以用 $ref 引用定义。
```

两种都正常。

## 返回结构示例

### 未确认

```json
{
  "ok": false,
  "allowed": false,
  "action": "create_ticket",
  "action_type": "write",
  "requires_confirmation": true,
  "confirmation_checked": false,
  "error_code": "TOOL_CONFIRMATION_REQUIRED",
  "message": "创建工单是写操作，必须先拿到用户确认，本次请求不会执行。",
  "ticket": null
}
```

### 创建成功

```json
{
  "ok": true,
  "allowed": true,
  "action": "create_ticket",
  "action_type": "write",
  "requires_confirmation": true,
  "confirmation_checked": true,
  "confirmation_id": "9f4d0b2f5b0c4f2a9d6c8b1e0a3f7c11",
  "message": "工单创建成功。",
  "ticket": {
    "ticket_id": "T1001",
    "title": "订单 A1001 一直未发货",
    "category": "complaint",
    "priority": "high",
    "related_order_id": "A1001",
    "created_at": "2026-07-12T10:00:00+00:00"
  }
}
```

### 幂等冲突

```json
{
  "ok": false,
  "allowed": true,
  "error_code": "IDEMPOTENCY_KEY_CONFLICT",
  "message": "同一个幂等键不能用于不同的工具调用参数。",
  "ticket": null
}
```

### 超时

```text
ToolError:
TOOL_TIMEOUT: 创建工单工具响应超时，已使用幂等键保护，请稍后查询结果或重试同一确认。
```

## 测试部分简讲

新增测试：

```text
projects/ai-service/tests/test_mcp_create_ticket_tool.py
```

重点覆盖：

```text
create_ticket tool schema 暴露写操作参数契约。
未确认时返回 TOOL_CONFIRMATION_REQUIRED。
未确认时不会调用 FakeTicketCreator。
确认后可以创建工单。
confirmation_id 会作为幂等键传给 creator。
同一 confirmation_id 重复调用只执行一次。
同一 confirmation_id 不同参数返回 IDEMPOTENCY_KEY_CONFLICT。
非法参数返回 INVALID_TOOL_ARGUMENTS。
TICKET_ALREADY_EXISTS 返回 ok=false。
TOOL_TIMEOUT 包装成安全 ToolError。
TOOL_RESULT_VALIDATION_FAILED 不泄露内部字段。
未知异常不泄露内部堆栈信息。
MCP Client 可以通过 fake adapter 调用 create_ticket。
返回内容不包含 requester_id 和 description 中的敏感值。
```

本节测试最重要的是：

```text
证明写操作没有确认不会执行。
```

这比成功创建更重要。

因为 AI 写工具最怕的是：

```text
模型误触发真实写入。
```

## 和当前项目的关系

当前项目已经有完整工单链路：

```text
TicketWorkflowService
-> plan_ticket()
-> confirmation_service
-> execute_confirmed_ticket()
-> JavaTicketClient
```

本节新增的 MCP adapter 不替代这条链路。

它是在 MCP 学习阶段做一个最小写工具封装：

```text
create_ticket_for_mcp()
```

它复用了：

```text
CreateTicketArgs
CreatedTicket
JavaTicketClient
authorize_tool_call
run_idempotent_tool
```

这说明 MCP 接入不应该另起一套业务规则。

而应该复用已有的：

```text
参数模型。
权限规则。
幂等机制。
Java client。
输出白名单。
错误映射。
```

## 常见误区

### 误区 1：有 confirmation_id 就等于可以执行

不完全对。

生产系统里必须确认：

```text
confirmation_id 是否存在。
是否属于当前用户。
是否属于 create_ticket。
参数是否匹配。
是否已经确认。
是否过期。
```

本节是最小 MCP adapter，先用 `user_confirmed + confirmation_id` 表达边界。

### 误区 2：幂等键就是防止所有错误

不对。

幂等键只解决：

```text
同一写操作重复提交。
```

它不解决：

```text
权限问题。
参数错误。
用户没确认。
业务不允许创建。
```

### 误区 3：超时就是创建失败

不一定。

写操作超时时，可能出现：

```text
服务端已经写入，但客户端没收到响应。
```

所以本节错误消息不会简单说“创建失败”，而是提醒：

```text
已使用幂等键保护，请稍后查询结果或重试同一确认。
```

### 误区 4：CreatedTicket 可以全部返回给模型

不应该默认这么做。

返回给模型的数据应该最小化。

本节不返回：

```text
requester_id
description
```

这是为了减少内部身份和用户隐私重复进入模型上下文。

### 误区 5：测试只需要测成功

写操作测试最重要的是失败路径。

必须测试：

```text
未确认不会执行。
幂等不会重复执行。
幂等冲突会拒绝。
内部错误不会泄露。
```

## 本节真正学会了什么

这一节真正学到的是：

```text
MCP 写操作工具的工程边界。
```

你现在应该能讲清楚：

```text
read tool 可以先关注查询和输出过滤。
write tool 必须额外关注用户确认、幂等、审计和执行状态不确定问题。
```

本节代码体现的原则：

```text
模型不能直接写。
未确认不执行。
确认 ID 绑定幂等执行。
同一确认重复执行不重复写。
同一确认不同参数要冲突。
业务错误 ok=false。
系统错误 ToolError。
输出字段最小化。
测试必须证明边界。
```

## 手动运行方式

本节不需要单独手动验证文档。

你可以在 `projects/ai-service` 下运行：

```powershell
uv run pytest tests\test_mcp_create_ticket_tool.py tests\test_java_ticket_client.py tests\test_tool_fakes.py tests\test_mcp_client_smoke.py tests\test_minimal_mcp_server.py
```

也可以看 MCP tools 列表：

```powershell
uv run python scripts\mcp_client_smoke.py
```

注意：

```text
smoke 脚本默认只展示 create_ticket 已经出现在 tools/list 里，不真实创建工单。
```

真实联调需要启动 Java 服务和依赖环境，本节不需要。

## 练习题

### 练习 1：为什么 create_ticket 必须要求用户确认？

参考答案：

```text
因为 create_ticket 会写入业务系统，可能创建真实工单。模型可能误解用户意图，也可能被上下文或 prompt injection 影响。用户确认能让用户在写入前看到最终工单内容，确认这件事确实要执行。
```

### 练习 2：confirmation_id 和 Idempotency-Key 有什么区别？

参考答案：

```text
confirmation_id 证明用户确认过某个写操作计划，解决“用户是否同意”的问题。Idempotency-Key 保证同一个写请求重复提交时不会重复写入，解决“重复提交是否重复执行”的问题。当前项目用 confirmation_id 作为幂等键，是因为一次确认对应一次写操作。
```

### 练习 3：为什么未确认时要测试 creator.calls 为空？

参考答案：

```text
因为写操作安全的关键不是返回了什么文案，而是后端确实没有执行写入。creator.calls 为空可以证明未确认请求没有进入真实 creator 执行路径。
```

### 练习 4：为什么同一个 confirmation_id 不同参数要拒绝？

参考答案：

```text
因为同一个 confirmation_id 只能代表用户确认过的一组固定参数。如果第二次使用同一个 confirmation_id 但参数变了，就说明确认内容和执行内容不一致，应该返回 IDEMPOTENCY_KEY_CONFLICT，要求重新确认。
```

### 练习 5：为什么 CreatedTicket 不返回 description？

参考答案：

```text
description 可能包含用户隐私或很长的原始问题描述，模型最终回答通常不需要重复它。MCP 工具返回应该最小化，只返回创建成功所需的 ticket_id、标题、分类、优先级、关联订单和创建时间。
```

## 自测题

### 自测 1：写操作 MCP tool 至少要有哪些边界？

参考答案：

```text
参数校验、用户确认、工具授权、幂等键、业务错误结构化、系统错误安全包装、输出白名单、测试证明未确认不执行。
```

### 自测 2：`TOOL_TIMEOUT` 在创建工单时为什么不能简单说“失败了”？

参考答案：

```text
因为写操作超时可能是响应超时，而不是服务端没有写入。服务端可能已经创建了工单，只是客户端没收到响应。应该结合幂等键，提示稍后查询结果或使用同一确认重试，避免重复创建。
```

### 自测 3：`TICKET_ALREADY_EXISTS` 应该是业务错误还是 ToolError？

参考答案：

```text
它是业务错误。说明工具链路正常，但业务系统认为已经存在相似工单，不应该再创建。适合返回 ok=false，让模型向用户解释，而不是作为系统故障处理。
```

### 自测 4：为什么 MCP adapter 要复用 `authorize_tool_call`？

参考答案：

```text
因为工具是否启用、是否需要确认、访问级别这些规则应该集中在工具注册表里。MCP adapter 复用 authorize_tool_call，可以避免每个入口自己写一套安全规则。
```

### 自测 5：为什么本节不真实启动 Java 服务？

参考答案：

```text
因为本节目标是测试 MCP 写操作 adapter 的边界，不是测试外部服务环境。用 FakeTicketCreator 可以稳定验证确认、幂等、错误包装和输出过滤。真实 Java 联调应放在单独 smoke 或集成测试里。
```

## 面试表达

如果别人问：

```text
AI 创建工单怎么保证不会乱写？
```

可以回答：

```text
我不会让模型直接写业务系统。模型只能提出创建工单计划，真正执行 create_ticket 前，后端会检查用户确认状态和 confirmation_id。确认通过后，使用 confirmation_id 作为幂等键调用 JavaTicketClient 创建工单，避免超时或重试导致重复创建。业务错误返回结构化 ok=false，系统错误包装成安全 ToolError，返回给模型的工单字段也做了白名单过滤，不返回内部 requester_id 或完整 description。
```

如果别人问：

```text
幂等键为什么重要？
```

可以回答：

```text
创建工单属于写操作，超时后无法简单判断服务端是否已经写入。如果没有幂等键，重试可能创建重复工单。使用幂等键后，同一确认和同一参数重复执行会复用同一个结果；同一幂等键配不同参数会拒绝，避免确认内容和执行内容不一致。
```

## 本节小结

本节完成了阶段 8 的第一个 MCP 写操作工具：

```text
create_ticket
```

和第 15 节相比，本节多了几个关键边界：

```text
用户确认。
confirmation_id。
幂等执行。
写操作 timeout 的状态不确定处理。
更严格的输出白名单。
```

下一节进入：

```text
阶段 8 第 17 节：MCP Resource 接入项目文档
```

从下一节开始，我们会把项目里的文档、契约、学习资料映射成 MCP Resource，让 MCP 不只暴露 tool，也能暴露可读取的项目上下文。
