# 阶段 8 第 7 节：MCP Tools 基础

## 本节定位

本节是阶段 8 第 7 节。

前面几节我们已经把 MCP 的大框架学完一轮：

```text
第 3 节：MCP 架构，知道 Host、Client、Server。
第 4 节：MCP 通信基础，知道 JSON-RPC、request、response、notification。
第 5 节：MCP 生命周期，知道 initialize、operation、shutdown。
第 6 节：MCP Transport，知道 stdio 和 Streamable HTTP。
```

这一节开始进入 MCP Server 暴露的核心能力之一：

```text
Tools
```

本节最重要的一句话：

```text
MCP Tool 是 MCP Server 暴露给 Host 的可执行能力；Host 先用 tools/list 发现工具，再用 tools/call 调用工具。
```

放到我们的项目里，未来很自然的 MCP Tools 是：

```text
query_order
create_ticket
```

但你不能只把 MCP Tool 理解成“一个 Python 函数”。

更准确地说：

```text
MCP Tool 是一个协议层暴露出来的可执行能力。
它有名字、描述、输入 schema、可选输出 schema、返回内容、错误表达和安全边界。
```

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
MCP Tool 是什么。
MCP Tool 和普通函数有什么区别。
MCP Tool 和 HTTP API 有什么区别。
MCP Tool 和 Tool Calling tool 有什么区别。
tools capability 是什么。
tools/list 返回什么。
Tool 的 name、title、description、inputSchema 分别干什么。
为什么工具名和工具描述会影响模型选择。
tools/call 怎么调用工具。
params.name 和 params.arguments 怎么理解。
Tool result 的 content 是什么。
structuredContent 和 outputSchema 是什么。
isError=true 表示什么。
协议错误和工具执行错误怎么分。
query_order 和 create_ticket 未来怎么设计成 MCP Tools。
```

本节学完后，你应该能看到下面消息就知道它在做什么：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "query_order",
    "arguments": {
      "order_id": "A1001"
    }
  }
}
```

它表示：

```text
Client 正在请求 Server 调用 query_order 这个 MCP Tool。
```

## 本节不做什么

省 token 模式下，本节是纯知识点学习。

不做：

```text
不写代码。
不创建手动验证清单。
不启动 VMware。
不启动 Qdrant / Milvus / Redis / MySQL。
不跑业务测试。
不做敏感信息扫描。
不提交 GitHub。
```

本节只做：

```text
MCP Tools 概念讲解。
tools/list 和 tools/call 拆解。
Tool schema 和 result 讲解。
错误、安全和项目映射。
练习和自测。
README 和进度索引更新。
```

## 官方资料依据

本节参考：

| 资料 | 本节使用点 |
| --- | --- |
| [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | Tools 定义、tools capability、tools/list、tools/call、Tool 数据结构、inputSchema、outputSchema、tool result、isError、安全要求 |
| [MCP Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture) | Tools 是 Server 暴露的核心 primitive，Client 先发现再调用，Host 可以整合多个 Server 的工具 |
| [MCP Base Protocol](https://modelcontextprotocol.io/specification/2025-11-25/basic) | JSON-RPC request/response/notification 基础和生命周期背景 |

说明：

```text
本节先讲 MCP Tools 基础。
第 12 节会专门讲工具参数校验。
第 13 节会专门讲 MCP 错误处理。
第 14 节会专门讲 MCP 安全边界。
第 15、16 节会把 query_order 和 create_ticket 真正封装成 MCP Tools。
```

## 基础知识铺垫

### 1. 先回忆 Tool Calling 里的工具

我们前面已经学过 Tool Calling。

Tool Calling 里，应用通常会把工具描述给模型：

```text
工具名
工具描述
参数 schema
```

模型看到工具后，可能输出：

```text
我要调用 query_order。
参数是 order_id=A1001。
```

但真正执行工具的是：

```text
应用后端。
```

不是模型自己执行。

MCP Tool 和这个概念有关系，但不是完全同一层。

可以先这样区分：

```text
Tool Calling tool 是给模型看的工具定义。
MCP Tool 是 MCP Server 暴露给 MCP Client 的工具能力。
```

Host 可以把 MCP Tool 转换成模型可用的 Tool Calling tool。

这就是第 2 节学过的上下游关系。

### 2. MCP Tool 不只是一个函数

你可能会直觉认为：

```text
MCP Tool = 一个 Python 函数。
```

这个理解不够准确。

普通函数可能是：

```python
def query_order(order_id: str) -> dict:
    ...
```

MCP Tool 是协议层暴露的能力，它至少要回答：

```text
工具叫什么？
工具做什么？
工具需要什么参数？
参数格式怎么校验？
调用时用哪个协议方法？
执行结果怎么包装？
失败怎么表达？
这个工具是不是敏感操作？
谁有权限调用？
```

所以 MCP Tool 背后可以是一个函数。

但 MCP Tool 本身不是简单函数。

它是：

```text
函数能力 + 协议描述 + 参数 schema + 返回格式 + 错误表达 + 安全边界。
```

### 3. MCP Tool 和 HTTP API 的区别

HTTP API 可能是：

```http
GET /internal/orders/A1001
```

MCP Tool 调用可能是：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "query_order",
    "arguments": {
      "order_id": "A1001"
    }
  }
}
```

区别：

| 维度 | HTTP API | MCP Tool |
| --- | --- | --- |
| 面向谁 | 普通业务客户端、服务间调用 | AI Host / MCP Client |
| 调用方式 | URL + HTTP method | JSON-RPC method = `tools/call` |
| 能力发现 | 通常靠文档或 OpenAPI | `tools/list` |
| 参数描述 | DTO、OpenAPI、接口文档 | `inputSchema` |
| 返回 | HTTP status + response body | JSON-RPC result/error，工具结果在 result 里 |
| 安全边界 | token、权限、网关、业务校验 | Host 策略 + MCP Server 校验 + 下游业务校验 |

MCP Tool 可以调用 HTTP API。

例如：

```text
MCP Tool: query_order
  -> JavaOrderClient
  -> GET /internal/orders/{order_id}
  -> Java business service
```

所以：

```text
MCP Tool 是 AI 接入层能力。
HTTP API 仍然可以是下游业务接口。
```

### 4. MCP Tool 为什么需要 schema

如果没有 schema，调用工具就会变成：

```text
随便传参数。
Server 自己猜。
模型也不知道参数格式。
Host 也不好校验。
```

这会带来很多问题：

```text
order_id 传成数字还是字符串？
priority 允许哪些值？
related_order_id 是否必填？
description 最长多少？
source 是否允许用户随便传？
写操作是否必须有 confirmation_id？
```

schema 的作用是：

```text
告诉 Client 和 Host 这个工具需要什么参数。
帮助模型理解如何生成参数。
帮助 Server 校验参数。
帮助开发者写测试。
帮助文档和调试工具展示工具契约。
```

所以：

```text
Tool 没有 schema，就没有清晰契约。
```

### 5. 工具名和描述为什么重要

模型选择工具时，很依赖工具名和工具描述。

比如这两个工具名：

```text
do_it
query_order
```

明显后者更清楚。

再比如描述：

```text
处理订单。
```

太模糊。

更好的描述：

```text
查询当前用户有权查看的订单摘要，包括订单状态、物流状态和可展示给客服用户的安全字段。
```

这样模型更容易知道：

```text
什么时候用它。
什么时候不用它。
它能返回什么。
它不能做什么。
```

工具描述写差，会导致：

```text
模型选错工具。
模型不敢选工具。
模型误以为工具能做更多事情。
模型给错参数。
```

所以 MCP Tool 设计不是只写代码。

工具命名和描述也是工程能力。

## 本节主题系统讲解

### 1. MCP Tools 的整体流程

MCP Tool 的完整使用流程：

```text
1. Server 在 initialize response 里声明 tools capability。
2. Client 进入 Operation 阶段。
3. Client 发送 tools/list。
4. Server 返回工具列表。
5. Host 根据工具列表、用户权限和安全策略决定哪些工具可暴露给模型。
6. 模型通过 Tool Calling 选择某个工具。
7. Host 校验工具名、参数、权限、确认策略。
8. Client 发送 tools/call。
9. Server 执行工具。
10. Server 返回 Tool result。
11. Host 校验和过滤结果。
12. Host 把结果交给模型总结。
```

图示：

```text
Host / MCP Client
  |
  | tools/list
  v
MCP Server
  |
  | tools result: query_order, create_ticket
  v
Host tool registry / model tools
  |
  | model tool_call
  v
Host policy check
  |
  | tools/call name=query_order
  v
MCP Server
  |
  | JavaOrderClient
  v
Java business service
```

注意：

```text
tools/list 是发现工具。
tools/call 是调用工具。
模型选择工具不是 MCP Server 自己做的。
Host 仍然负责安全和策略。
```

### 2. tools capability

Server 如果支持工具，必须声明 `tools` capability。

概念上是：

```json
{
  "capabilities": {
    "tools": {
      "listChanged": true
    }
  }
}
```

含义：

```text
Server 支持 MCP Tools。
Server 可以处理 tools/list。
Server 可以处理 tools/call。
listChanged=true 表示工具列表变化时，Server 可以发送通知。
```

如果 Server 没声明 tools：

```text
Client 不应该调用 tools/list。
Client 不应该调用 tools/call。
Host 不应该把这个 Server 当成工具来源。
```

这和第 5 节生命周期里的能力协商是一致的。

### 3. tools/list 是什么

`tools/list` 用来发现 Server 暴露了哪些工具。

请求示例：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {
    "cursor": "optional-cursor-value"
  }
}
```

这里：

```text
method = tools/list。
params.cursor 是可选分页游标。
```

很多简单 Server 工具很少，可能不需要分页。

但协议支持分页，是为了工具列表很大时可扩展。

### 4. tools/list response 返回什么

响应示例：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "query_order",
        "title": "Order Query",
        "description": "查询当前用户有权查看的订单摘要。",
        "inputSchema": {
          "type": "object",
          "properties": {
            "order_id": {
              "type": "string",
              "description": "订单号，例如 A1001"
            }
          },
          "required": ["order_id"]
        }
      }
    ]
  }
}
```

核心字段：

| 字段 | 作用 |
| --- | --- |
| `name` | 工具唯一标识，调用时用它 |
| `title` | 可选展示名称，更偏 UI 显示 |
| `description` | 给 Host、模型和开发者看的功能说明 |
| `inputSchema` | 输入参数 JSON Schema |
| `outputSchema` | 可选输出结构 schema |
| `annotations` | 可选工具行为描述 |
| `icons` | 可选 UI 图标 |
| `execution` | 可选执行相关属性 |

现阶段最重要的是：

```text
name
description
inputSchema
```

### 5. tool.name 怎么设计

工具名是工具的唯一标识。

调用时：

```json
{
  "method": "tools/call",
  "params": {
    "name": "query_order"
  }
}
```

这里的 `query_order` 必须和 tools/list 里返回的 name 对上。

工具名建议：

```text
清楚表达动作。
不要太泛。
不要有空格。
不要用中文。
同一个 Server 内唯一。
区分大小写。
尽量使用 ASCII 字母、数字、下划线、短横线、点。
```

好的例子：

```text
query_order
create_ticket
search_knowledge_base
admin.tools.list
```

不好的例子：

```text
do
handle
工具1
query order
order,query
```

放到我们项目里：

```text
query_order 比 get 更好。
create_ticket 比 submit 更好。
```

因为它们明确表达了业务动作。

### 6. tool.description 怎么写

description 是工具说明。

它不只是给人看，也会影响 Host 或模型如何理解工具。

一个好的 description 应该说明：

```text
工具做什么。
什么时候使用。
输入大概是什么。
输出大概是什么。
限制是什么。
是否只读或写操作。
是否涉及权限。
```

例如 `query_order`：

```text
查询当前用户有权查看的订单摘要，包括订单状态、物流状态和可展示给客服用户的安全字段。仅用于读取订单信息，不会修改业务数据。
```

比下面这种更好：

```text
查询订单。
```

因为它补充了：

```text
权限边界。
返回范围。
只读性质。
```

例如 `create_ticket`：

```text
在用户确认后创建客服工单。该工具会写入业务系统，必须提供用户确认编号、幂等键和完整工单字段。
```

这能提醒 Host 和模型：

```text
这是写操作。
不能随便调用。
需要确认。
需要幂等。
```

### 7. inputSchema 是什么

`inputSchema` 是工具输入参数的 JSON Schema。

例如：

```json
{
  "type": "object",
  "properties": {
    "order_id": {
      "type": "string",
      "description": "订单号，例如 A1001"
    }
  },
  "required": ["order_id"],
  "additionalProperties": false
}
```

它表示：

```text
工具参数必须是 object。
必须有 order_id。
order_id 必须是 string。
不允许多余字段。
```

`inputSchema` 的作用：

```text
帮助 Client 和 Host 理解参数。
帮助模型生成正确 arguments。
帮助 Server 做参数校验。
帮助测试确认契约。
帮助文档展示工具用法。
```

注意：

```text
inputSchema 不是业务权限。
inputSchema 只描述参数形状。
```

用户有没有权限查这个订单，还要业务逻辑判断。

### 8. 无参数工具也要有 inputSchema

如果工具没有参数，也不能把 `inputSchema` 写成 null。

更好的写法：

```json
{
  "type": "object",
  "additionalProperties": false
}
```

含义：

```text
参数必须是空对象。
不接受任何字段。
```

比如：

```text
get_current_time
```

可以没有参数。

但仍然要有合法 schema。

### 9. tools/call 是什么

`tools/call` 用来调用某个 MCP Tool。

请求示例：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "query_order",
    "arguments": {
      "order_id": "A1001"
    }
  }
}
```

字段解释：

| 字段 | 含义 |
| --- | --- |
| `method` | 协议方法，固定是 `tools/call` |
| `params.name` | 要调用的工具名 |
| `params.arguments` | 工具参数 |

重点：

```text
tools/call 是 MCP 协议方法。
query_order 是业务工具名。
order_id 是工具业务参数。
```

不要把 `query_order` 写成：

```json
{
  "method": "query_order"
}
```

那就混层了。

### 10. params.arguments 怎么理解

`arguments` 是传给工具的业务参数。

它必须符合工具的 `inputSchema`。

例如工具定义要求：

```json
{
  "required": ["order_id"]
}
```

调用时必须有：

```json
{
  "arguments": {
    "order_id": "A1001"
  }
}
```

如果传：

```json
{
  "arguments": {
    "id": "A1001"
  }
}
```

就不符合 schema。

如果传：

```json
{
  "arguments": {
    "order_id": 1001
  }
}
```

也不符合 string 类型要求。

所以：

```text
arguments 是工具参数。
inputSchema 是 arguments 的契约。
```

### 11. Tool result 的 content

工具调用成功后，返回 result。

示例：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"order_id\":\"A1001\",\"status\":\"shipping\"}"
      }
    ],
    "isError": false
  }
}
```

`content` 是一个数组。

它可以包含不同类型的内容。

常见类型：

```text
text
image
audio
resource_link
resource
```

入门阶段先重点掌握：

```text
text
```

也就是返回文本内容。

为什么 content 是数组？

因为一个工具结果可能包含多个内容块。

比如：

```text
一段文本说明。
一个资源链接。
一张图片。
一个嵌入资源。
```

我们当前项目前期最可能用：

```text
text content
structuredContent
```

### 12. structuredContent 是什么

Tool result 可以有非结构化 `content`，也可以有结构化 `structuredContent`。

示例：

```json
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"order_id\":\"A1001\",\"status\":\"shipping\"}"
      }
    ],
    "structuredContent": {
      "order_id": "A1001",
      "status": "shipping"
    },
    "isError": false
  }
}
```

可以这样理解：

```text
content 更适合给模型或用户作为上下文读取。
structuredContent 更适合程序继续处理和校验。
```

官方也提醒：

```text
structuredContent 是 Server 产生的工具结果数据，不等于 LLM Structured Outputs。
```

也就是说：

```text
MCP structuredContent：工具返回的结构化结果。
LLM Structured Outputs：模型按 schema 生成结构化输出。
```

二者不是一回事。

### 13. outputSchema 是什么

`outputSchema` 是工具输出结构的 schema。

它是可选的。

如果提供了 outputSchema：

```text
Server 应该返回符合 schema 的 structuredContent。
Client 应该校验 structuredContent。
```

例如：

```json
{
  "name": "query_order",
  "description": "查询订单摘要",
  "inputSchema": {
    "type": "object",
    "properties": {
      "order_id": { "type": "string" }
    },
    "required": ["order_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "order_id": { "type": "string" },
      "status": { "type": "string" },
      "logistics_status": { "type": "string" }
    },
    "required": ["order_id", "status"]
  }
}
```

它的好处：

```text
工具返回结果更稳定。
Client 更容易校验。
Host 更容易把结果安全交给模型。
开发和测试更清楚。
```

我们未来做 `query_order` 时，非常适合考虑 outputSchema。

因为订单结果需要严格字段白名单。

### 14. isError 是什么

`isError` 表示工具执行结果是不是业务错误。

成功：

```json
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "订单 A1001 当前正在配送中。"
      }
    ],
    "isError": false
  }
}
```

业务失败：

```json
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "订单不存在或当前用户无权查看。"
      }
    ],
    "isError": true
  }
}
```

注意：

```text
isError=true 仍然在 JSON-RPC result 里。
```

这表示：

```text
协议调用成功了。
工具也被执行了。
但业务执行结果是失败。
```

比如：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
参数业务含义不合法
下游 API 返回可恢复错误
```

都可能包装成工具执行错误。

### 15. 协议错误和工具执行错误

第 4 节已经讲过，这里结合 Tools 再强调一次。

#### 协议错误

协议错误走 JSON-RPC `error`。

例如：

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "error": {
    "code": -32602,
    "message": "Unknown tool: invalid_tool_name"
  }
}
```

适合：

```text
工具名不存在。
请求结构不符合 CallToolRequest schema。
method 不存在。
协议层无法处理。
```

#### 工具执行错误

工具执行错误走 `result.isError=true`。

例如：

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "订单 A9999 不存在。"
      }
    ],
    "isError": true
  }
}
```

适合：

```text
订单不存在。
用户无权限。
业务字段不合法。
外部 API 返回可理解业务失败。
```

一句话：

```text
协议没走通：error。
工具业务没办成：result.isError=true。
```

### 16. 工具结果要不要直接给模型

不能无脑直接给。

Host 应该先做：

```text
结果 schema 校验。
敏感字段过滤。
错误码映射。
权限二次确认。
日志记录。
trace_id 串联。
```

比如 Java business service 返回了：

```text
internal_debug_message
database_error
phone_number
address
payment_info
```

MCP Server 和 Host 都不能随便把这些交给模型。

所以：

```text
MCP Tool 返回结果，不代表模型可以看到全部原始结果。
```

这和我们阶段 7 做的字段白名单、错误码映射是一致的。

### 17. 安全要求

MCP Tools 官方资料对安全有明确要求。

Server 侧应该：

```text
校验所有工具输入。
实现正确访问控制。
限制工具调用频率。
清洗工具输出。
```

Client/Host 侧应该：

```text
敏感操作前让用户确认。
调用前向用户展示工具输入。
把工具结果交给模型前先校验。
为工具调用设置超时。
记录工具使用日志，用于审计。
```

这些和我们之前学过的 AI 工具安全完全一致。

MCP 不是让工具自动安全。

MCP 只是标准化暴露和调用工具。

安全仍然要自己设计。

### 18. query_order 作为 MCP Tool 怎么设计

未来 `query_order` 可以设计成：

```json
{
  "name": "query_order",
  "title": "Order Query",
  "description": "查询当前用户有权查看的订单摘要，包括订单状态、物流状态和可展示给用户的安全字段。该工具是只读工具，不会修改业务数据。",
  "inputSchema": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "订单号，例如 A1001"
      }
    },
    "required": ["order_id"],
    "additionalProperties": false
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "order_id": { "type": "string" },
      "status": { "type": "string" },
      "logistics_status": { "type": "string" }
    },
    "required": ["order_id", "status"]
  }
}
```

执行链路：

```text
tools/call query_order
-> MCP Server 校验 arguments
-> 读取用户上下文和 trace_id
-> JavaOrderClient
-> Java business service
-> 字段白名单
-> outputSchema 校验
-> Tool result
```

注意：

```text
query_order 是只读工具。
一般不需要用户确认。
但仍然需要权限校验。
```

### 19. create_ticket 作为 MCP Tool 怎么设计

`create_ticket` 是写操作。

它比 `query_order` 风险更高。

概念设计：

```json
{
  "name": "create_ticket",
  "title": "Create Customer Service Ticket",
  "description": "在用户明确确认后创建客服工单。该工具会写入业务系统，必须提供完整工单字段、用户确认编号和幂等键。",
  "inputSchema": {
    "type": "object",
    "properties": {
      "title": { "type": "string" },
      "description": { "type": "string" },
      "category": { "type": "string" },
      "priority": { "type": "string" },
      "related_order_id": { "type": "string" },
      "confirmation_id": { "type": "string" }
    },
    "required": ["title", "description", "category", "priority", "confirmation_id"],
    "additionalProperties": false
  }
}
```

执行链路：

```text
tools/call create_ticket
-> Host 检查是否已经用户确认
-> MCP Server 校验 arguments
-> 幂等键校验
-> JavaTicketClient
-> Java business service
-> MySQL transaction
-> Redis idempotency/cache
-> Tool result
```

注意：

```text
create_ticket 是写工具。
必须有人类确认。
必须有幂等。
必须有权限。
必须有审计。
```

### 20. tools/list 变化通知

如果 Server 的工具列表会变化，可以声明：

```json
{
  "tools": {
    "listChanged": true
  }
}
```

工具变化时，Server 可以发送：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

Client 收到后通常会：

```text
重新调用 tools/list。
刷新 Host 内部工具列表。
重新决定哪些工具暴露给模型。
```

适合场景：

```text
用户权限变化。
外部系统临时不可用。
某个工具下线。
新增工具。
Server 配置改变。
```

### 21. 常见误区

#### 误区 1：MCP Tool 就是模型直接执行的函数

不对。

模型表达工具调用意图。

Host 决定是否调用。

MCP Client 调 MCP Server。

Server 执行工具逻辑。

#### 误区 2：tools/list 会执行工具

不对。

tools/list 只是发现工具。

tools/call 才是调用工具。

#### 误区 3：工具有 inputSchema 就不用业务校验

不对。

inputSchema 只校验参数形状。

业务校验仍然需要：

```text
权限
租户
订单是否存在
状态是否允许
写操作是否确认
幂等是否通过
```

#### 误区 4：所有错误都用 JSON-RPC error

不对。

协议错误用 JSON-RPC error。

业务执行失败可以用 result.isError=true。

#### 误区 5：description 随便写也没关系

不对。

description 会影响 Host、模型、开发者和调试工具对工具的理解。

描述太模糊会导致模型误用工具。

### 22. 面试表达：怎么讲 MCP Tools

如果别人问：

```text
MCP Tool 是什么？
```

不要只说：

```text
就是工具。
```

更好的回答：

```text
MCP Tool 是 MCP Server 按协议暴露给 MCP Client 的可执行能力。Server 需要在 initialize 阶段声明 tools capability，Client 在 operation 阶段通过 tools/list 发现工具，通过 tools/call 调用工具。
```

再补工具定义：

```text
一个 Tool 定义通常包含 name、title、description、inputSchema，可选 outputSchema、annotations、icons、execution。name 用来唯一定位工具，description 帮助 Host 和模型理解什么时候使用，inputSchema 描述参数契约。
```

再补工程边界：

```text
Tool result 通过 content 返回，也可以有 structuredContent 和 outputSchema。协议错误走 JSON-RPC error，业务执行失败可以走 result.isError=true。敏感写操作必须经过 Host 的用户确认、权限、幂等和审计。
```

结合我们的项目：

```text
在我们的项目里，query_order 适合设计成只读 MCP Tool，内部调用 JavaOrderClient；create_ticket 适合设计成写操作 MCP Tool，必须保留用户确认、幂等键、权限、trace_id 和 Java business service 的业务边界。
```

## 本节结论

本节最重要的结论：

```text
MCP Tool 是 MCP Server 暴露的可执行能力。
Server 通过 tools capability 声明支持工具。
Client 用 tools/list 发现工具。
Client 用 tools/call 调用工具。
Tool 定义的核心是 name、description、inputSchema。
工具返回结果放在 result.content，结构化结果可以放 structuredContent。
业务执行失败可以用 isError=true。
协议错误和工具执行错误要分开。
```

放到项目里：

```text
query_order 未来是只读 MCP Tool。
create_ticket 未来是写操作 MCP Tool。
MCP Tool 内部仍然要复用 JavaOrderClient / JavaTicketClient。
Java business service 仍然负责真实权限、事务、幂等、错误码和数据。
Host 仍然负责是否把工具暴露给模型，以及写操作确认。
```

## 本节练习

### 练习 1：MCP Tool 和普通函数有什么区别？

参考答案：

```text
普通函数只是代码里的可执行逻辑。
MCP Tool 是 MCP Server 按协议暴露的可执行能力，除了背后可能有函数逻辑，还包含工具名、描述、输入 schema、返回格式、错误表达和安全边界。
```

### 练习 2：`tools/list` 和 `tools/call` 有什么区别？

参考答案：

```text
tools/list 用来发现 Server 暴露了哪些工具，不执行工具。
tools/call 用来调用某个具体工具，工具名放在 params.name，工具参数放在 params.arguments。
```

### 练习 3：下面这个调用里，协议方法、工具名、业务参数分别是什么？

题目：

```json
{
  "method": "tools/call",
  "params": {
    "name": "query_order",
    "arguments": {
      "order_id": "A1001"
    }
  }
}
```

参考答案：

```text
协议方法是 tools/call。
工具名是 query_order。
业务参数是 order_id=A1001。
```

### 练习 4：为什么工具必须有 inputSchema？

参考答案：

```text
inputSchema 定义工具参数契约，帮助 Client、Host、模型、Server 和测试理解参数结构。
没有 inputSchema，参数就容易变成随便传、随便猜，无法稳定校验。
```

### 练习 5：`isError=true` 表示什么？

参考答案：

```text
它表示 JSON-RPC 协议请求成功到达并执行了工具，但工具业务执行结果失败。
例如订单不存在、用户无权限、业务参数不合法，都可能用 result.isError=true 表达。
```

### 练习 6：为什么 `create_ticket` 比 `query_order` 风险更高？

参考答案：

```text
query_order 是只读工具，主要读取用户有权查看的信息。
create_ticket 是写操作，会修改业务系统或创建新数据，所以必须有用户确认、幂等、权限、审计和更严格的错误处理。
```

### 练习 7：工具描述为什么不能随便写？

参考答案：

```text
工具描述会影响 Host、模型和开发者对工具用途的理解。
描述太模糊会导致模型选错工具、误以为工具能做更多事情，或者在该使用工具时不使用工具。
```

## 自测题

### 自测 1：Server 没声明 tools capability，Client 能不能 tools/list？

参考答案：

```text
不应该。
Server 必须在 initialize response 里声明 tools capability，Client 才应该在 Operation 阶段调用 tools/list 或 tools/call。
```

### 自测 2：`query_order` 应该写在 `method` 里吗？

参考答案：

```text
不应该。
MCP 协议方法应该是 tools/call。
query_order 是工具名，应该写在 params.name 里。
```

### 自测 3：inputSchema 能不能替代权限校验？

参考答案：

```text
不能。
inputSchema 只校验参数形状。
用户有没有权限查订单、能不能创建工单，仍然需要 Host、MCP Server 和 Java business service 做业务权限校验。
```

### 自测 4：Tool result 的 content 为什么是数组？

参考答案：

```text
因为一个工具结果可能包含多个内容块，例如文本、图片、资源链接或嵌入资源。
数组结构可以支持多种内容组合。
```

### 自测 5：structuredContent 和 LLM Structured Outputs 是一回事吗？

参考答案：

```text
不是。
structuredContent 是 MCP Tool 返回的结构化工具结果。
LLM Structured Outputs 是模型按 schema 生成结构化输出。
一个来自工具 Server，一个来自模型。
```

### 自测 6：订单不存在应该走 JSON-RPC error 还是 result.isError=true？

参考答案：

```text
通常更适合 result.isError=true。
因为请求结构是合法的，工具也执行了，只是业务结果失败。
JSON-RPC error 更适合未知工具、请求结构错误、协议层错误。
```

### 自测 7：`query_order` 作为 MCP Tool 内部能不能直接查 MySQL？

参考答案：

```text
不建议。
在我们的项目里，它应该复用 JavaOrderClient 调 Java business service。
Java business service 负责真实权限、MyBatis、MySQL、Redis、错误码、事务和 trace_id。
MCP Tool 不应该绕过这些业务边界。
```

## 本节总结

这一节你要真正记住的是：

```text
MCP Tool 是协议层暴露的可执行能力，不只是一个函数。
tools/list 发现工具。
tools/call 调用工具。
name 定位工具。
description 解释工具。
inputSchema 约束参数。
content 返回结果。
structuredContent 返回结构化结果。
isError=true 表达工具业务执行失败。
```

后续写代码时，尤其要记住：

```text
工具名要清楚。
工具描述要准确。
参数 schema 要严格。
只读工具和写工具要分级。
写操作必须有人类确认。
MCP Tool 不能绕过 Java business service 的真实业务边界。
```

下一节学习：

```text
阶段 8 第 8 节：MCP Resources 基础
```
