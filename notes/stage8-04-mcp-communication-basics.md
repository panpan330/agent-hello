# 阶段 8 第 4 节：MCP 通信基础

## 本节定位

本节是阶段 8 第 4 节。

前面三节我们已经完成：

```text
第 1 节：MCP 是什么。
第 2 节：MCP 和 Tool Calling 的区别。
第 3 节：MCP 架构，理解 Host、Client、Server。
```

这一节进入 MCP 里更底层的一块：

```text
MCP Client 和 MCP Server 到底怎么通信？
```

第 3 节讲的是“谁和谁说话”。

第 4 节讲的是“它们说的话长什么样”。

本节最重要的一句话：

```text
MCP Client 和 MCP Server 之间的消息遵循 JSON-RPC 2.0，主要有 request、response、notification 三类消息。
```

如果你后面要写 Python MCP Server，必须先能看懂下面这种消息：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

它表示：

```text
这是一个 JSON-RPC request。
发送方想调用 method = tools/list。
id = 1 用来匹配后续 response。
params 是本次请求的参数。
```

本节要让你做到：

```text
看到 MCP 消息不慌。
能分清请求、响应、通知。
知道 id、method、params、result、error 分别干什么。
知道 tools/list、tools/call、notifications/tools/list_changed 这类名字怎么读。
知道 MCP 通信和普通 HTTP API 的区别。
```

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
为什么 MCP 使用 JSON-RPC。
JSON 和 JSON-RPC 的区别。
request 是什么。
response 是什么。
notification 是什么。
id 为什么重要。
method 是什么。
params 是什么。
result 和 error 有什么区别。
为什么 notification 没有 id。
tools/list 和 tools/call 分别表示什么。
协议错误和工具执行错误有什么区别。
MCP 通信和普通 HTTP REST API 的区别。
这套通信方式和后续 Python MCP Server 有什么关系。
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
通信概念讲解。
JSON-RPC 消息拆解。
MCP 方法名示例。
项目映射。
练习和自测。
README 和进度索引更新。
```

## 官方资料依据

本节参考：

| 资料 | 本节使用点 |
| --- | --- |
| [MCP Base Protocol Overview](https://modelcontextprotocol.io/specification/2025-11-25/basic) | MCP 消息遵循 JSON-RPC 2.0，request、response、notification、result response、error response 的基础格式 |
| [MCP Lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) | initialize 请求、initialized notification、能力协商、operation 阶段通信 |
| [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | `tools/list`、`tools/call`、`notifications/tools/list_changed`、协议错误和工具执行错误 |
| [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification) | JSON-RPC 的基本通信模型 |

说明：

```text
本节只讲通信基础。
生命周期细节会在第 5 节讲。
transport 细节会在第 6 节讲。
tools 的参数 schema 和返回结果会在第 7 节继续讲。
```

## 基础知识铺垫

### 1. 什么叫“通信协议”

通信协议就是双方约定好的说话规则。

不是只要能传字符串就算协议。

协议要规定：

```text
消息长什么样。
哪些字段必须有。
哪些字段可选。
字段代表什么含义。
请求和响应怎么匹配。
出错时怎么表达。
一方发通知时另一方要不要回复。
```

传统后端里你已经接触过很多协议或约定：

```text
HTTP
REST API
JSON
JDBC 协议
Redis 协议
MySQL 协议
WebSocket
```

比如 HTTP 约定：

```text
GET /orders/A1001 表示读取订单。
POST /tickets 表示创建工单。
200 表示成功。
404 表示资源不存在。
500 表示服务端错误。
Header 里可以放 token、trace_id、content-type。
Body 里可以放 JSON。
```

MCP 也有自己的通信约定。

它使用 JSON-RPC 作为基础消息格式。

你可以先这样理解：

```text
JSON 是数据格式。
JSON-RPC 是基于 JSON 的远程过程调用协议。
MCP 是基于 JSON-RPC 构建的一套 AI 应用连接外部能力的协议。
```

### 2. JSON 和 JSON-RPC 不是一回事

JSON 是一种数据格式。

比如：

```json
{
  "order_id": "A1001",
  "status": "shipping"
}
```

它只说明：

```text
这里有一个对象。
对象里有 order_id 和 status 两个字段。
```

但它不说明：

```text
这是请求还是响应？
要调用什么操作？
这个消息有没有编号？
成功还是失败？
失败错误码是什么？
接收方需不需要回复？
```

JSON-RPC 在 JSON 外面加了一套调用语义。

比如：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

这个就不只是普通 JSON。

它表达的是：

```text
这是 JSON-RPC 2.0 消息。
这是一个请求。
请求编号是 1。
要调用的方法是 tools/list。
参数是空对象。
```

所以学习 MCP 通信时，不要只看 JSON 长什么样。

要看它背后的语义：

```text
这条消息要做什么？
谁发给谁？
对方要不要回复？
后续响应靠什么匹配？
```

### 3. RPC 是什么

RPC 是 Remote Procedure Call，远程过程调用。

你可以理解成：

```text
像调用本地函数一样，请求远程服务执行某个方法。
```

本地函数调用可能是：

```python
query_order(order_id="A1001")
```

RPC 消息里会变成类似：

```json
{
  "method": "query_order",
  "params": {
    "order_id": "A1001"
  }
}
```

当然 MCP 的方法名通常不是直接写 `query_order`。

MCP 协议级方法会是：

```text
tools/list
tools/call
resources/list
resources/read
prompts/list
prompts/get
initialize
```

如果要调用业务工具 `query_order`，通常是在 `tools/call` 的 params 里传：

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

这点很重要。

错误理解：

```text
MCP method 就是业务工具名 query_order。
```

更准确：

```text
MCP method 是协议操作名，例如 tools/call。
业务工具名 query_order 放在 params.name 里。
```

### 4. 为什么 MCP 不直接用普通 REST API

你可能会问：

```text
既然都是通信，为什么不直接用 HTTP REST API？
为什么还要 JSON-RPC？
```

原因是 MCP 不是只做一个固定业务接口。

MCP 要支持：

```text
初始化。
能力协商。
列出工具。
调用工具。
列出资源。
读取资源。
获取 prompt。
通知能力变化。
进度通知。
取消请求。
不同 transport。
Client 和 Server 双向发消息。
```

普通 REST API 更常见的是：

```text
GET /orders/{id}
POST /tickets
PUT /users/{id}
DELETE /files/{id}
```

这种方式适合业务资源建模。

但 MCP 更像一套通用控制协议。

它需要表达：

```text
我要调用一个协议方法。
这是本次调用参数。
这是调用编号。
后续你用同一个编号返回结果或错误。
有些消息只是通知，不需要响应。
```

所以 JSON-RPC 更适合这种“协议方法调用”风格。

注意：

```text
MCP 可以跑在 HTTP transport 上。
但 MCP 消息本身不是普通 REST API 风格。
```

也就是说：

```text
HTTP 可能只是传输通道。
JSON-RPC 才是 MCP data layer 的消息语义。
```

### 5. 请求和响应为什么需要 id

在普通同步 HTTP API 里，你发一个请求，马上等一个响应。

这种情况下，你不太需要自己关心请求编号。

但在协议通信里，尤其是可能有多个并发请求时，需要知道：

```text
这个 response 对应哪个 request？
```

所以 JSON-RPC request 里有 `id`。

例如 Client 连续发两个请求：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/list",
  "params": {}
}
```

Server 后面返回：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "resources": []
  }
}
```

你就知道：

```text
这个 response 对应 id = 2 的 resources/list。
```

再返回：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": []
  }
}
```

你也能匹配：

```text
这个 response 对应 id = 1 的 tools/list。
```

所以：

```text
id 不是业务 id。
id 是协议请求 id。
```

不要把它和：

```text
order_id
ticket_id
trace_id
user_id
```

混在一起。

### 6. method 是协议动作名

JSON-RPC request 里的 `method` 表示要执行哪个协议动作。

常见 MCP method：

```text
initialize
tools/list
tools/call
resources/list
resources/read
prompts/list
prompts/get
notifications/initialized
notifications/tools/list_changed
```

你可以把 method 理解为：

```text
这条消息想让对方做什么。
```

例如：

```text
tools/list：列出 Server 提供的工具。
tools/call：调用 Server 上的某个工具。
resources/read：读取某个资源。
prompts/get：获取某个 prompt 模板。
initialize：初始化连接并协商能力。
```

method 名字里有 `/`，可以帮助你理解分类。

```text
tools/list
```

大概读作：

```text
tools 这一类能力里的 list 操作。
```

```text
notifications/tools/list_changed
```

大概读作：

```text
这是 notification 类型，表示 tools 列表发生变化。
```

### 7. params 是本次请求的参数

`params` 是请求参数。

如果没有参数，可以省略，也可以是空对象，具体看协议定义和 SDK 实现。

例如列出工具：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

调用工具：

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

这里：

```text
method = tools/call 表示我要调用工具。
params.name = query_order 表示要调用哪个工具。
params.arguments.order_id = A1001 表示工具参数。
```

这三层不要混。

### 8. response 只回答 request

response 是对 request 的回复。

如果 request 成功，返回 `result`：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": []
  }
}
```

如果 request 失败，返回 `error`：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params"
  }
}
```

重点：

```text
response 必须能和 request 匹配。
匹配方式就是 id。
成功 response 有 result。
失败 response 有 error。
```

### 9. notification 是单向消息

notification 是通知。

它和 request 最大区别是：

```text
notification 没有 id。
notification 不需要 response。
```

例如初始化完成通知：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

工具列表变化通知：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

为什么 notification 没有 id？

因为它不等回复。

如果有 id，就意味着发送方期待 response。

所以：

```text
有 id：通常是 request。
没 id 且有 method：通常是 notification。
有 id 且有 result/error：是 response。
```

这个判断方法非常实用。

## 本节主题系统讲解

### 1. MCP 的三类基础消息

MCP 基础通信里，你先掌握三类消息：

| 消息类型 | 是否有 `id` | 是否有 `method` | 是否有 `result/error` | 是否需要回复 |
| --- | --- | --- | --- | --- |
| request | 有 | 有 | 没有 | 需要 |
| response | 有 | 没有 | 有 | 不需要再回复 |
| notification | 没有 | 有 | 没有 | 不需要 |

看到一条消息时，先不要急着理解全部字段。

先判断它是哪一类。

#### request

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

判断：

```text
有 id。
有 method。
没有 result/error。
所以它是 request。
```

#### success response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": []
  }
}
```

判断：

```text
有 id。
有 result。
没有 method。
所以它是成功 response。
```

#### error response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params"
  }
}
```

判断：

```text
有 id。
有 error。
没有 method。
所以它是失败 response。
```

#### notification

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

判断：

```text
没有 id。
有 method。
所以它是 notification。
```

这套判断方式比背定义更有用。

### 2. request 的字段拆解

一个典型 request：

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

逐字段看：

| 字段 | 含义 |
| --- | --- |
| `jsonrpc` | 表示 JSON-RPC 版本，这里是 2.0 |
| `id` | 协议请求编号，用来匹配 response |
| `method` | 要调用的协议方法 |
| `params` | 本次方法调用的参数 |

这条消息的含义：

```text
发送方发起一个编号为 2 的请求。
它要执行 tools/call。
它希望调用 query_order 这个工具。
工具参数是 order_id = A1001。
```

注意这里有两个层次：

```text
协议层方法：tools/call
业务工具名：query_order
```

后续我们写 MCP Tool 时一定要分清。

### 3. response 的字段拆解

成功响应：

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

逐字段看：

| 字段 | 含义 |
| --- | --- |
| `jsonrpc` | JSON-RPC 版本 |
| `id` | 对应原 request 的 id |
| `result` | 成功结果 |

这条消息表示：

```text
id = 2 的请求成功了。
返回的是工具调用结果。
isError = false 表示工具执行本身成功。
```

失败响应：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "error": {
    "code": -32602,
    "message": "Unknown tool: invalid_tool_name"
  }
}
```

它表示：

```text
id = 2 的请求失败了。
失败是协议层 error。
错误码是 -32602。
错误信息是 Unknown tool。
```

这里先不用背 JSON-RPC 错误码。

你现在先知道：

```text
result 表示协议请求成功。
error 表示协议请求失败。
```

第 13 节 MCP 错误处理会专门展开。

### 4. notification 的字段拆解

notification 示例：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

字段：

| 字段 | 含义 |
| --- | --- |
| `jsonrpc` | JSON-RPC 版本 |
| `method` | 通知类型 |
| `params` | 可选通知参数 |

它没有：

```text
id
result
error
```

因为：

```text
notification 不期待 response。
```

这个例子表示：

```text
Server 通知 Client：我的工具列表变了。
```

Host 收到后可以决定：

```text
重新调用 tools/list。
刷新内部工具列表。
更新可暴露给模型的工具 schema。
```

### 5. request 和 notification 的本质区别

request 和 notification 都有 `method`。

区别在于：

```text
request 要结果。
notification 只通知。
```

对比：

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tools/list"
}
```

这是 request。

因为它有 id，发送方等 response。

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

这是 notification。

因为它没有 id，发送方不等 response。

实际开发里，这个区别很重要。

如果你把 notification 当 request 处理，就会等一个永远不会来的 response。

如果你把 request 当 notification 处理，就会漏掉对方期待的 response。

### 6. MCP 消息方向不是永远 Client -> Server

很多初学者会以为：

```text
Client 永远发 request。
Server 永远回 response。
```

这在很多场景里确实常见。

比如：

```text
Client -> Server: tools/list
Server -> Client: tools/list response
Client -> Server: tools/call
Server -> Client: tools/call response
```

但 MCP 协议层更灵活。

官方基础协议里 request 和 notification 可以从 Client 发给 Server，也可以从 Server 发给 Client。

这是因为 MCP 还有一些 Client Features。

比如 Server 可能需要：

```text
请求 Host 进行 sampling。
请求用户补充信息。
请求 roots 边界信息。
发送日志或进度通知。
```

现阶段你不用深入这些。

你先记住：

```text
常见 Server Features 是 Client 调 Server。
但 MCP 协议不是单纯单向调用，它支持双向消息。
```

这也是 MCP 和普通 REST API 的一个区别。

### 7. initialize 是通信的起点

虽然生命周期会在第 5 节细讲，但通信基础里必须先看懂 initialize。

Client 和 Server 正常操作前，通常要先初始化。

初始化请求长这样：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-11-25",
    "capabilities": {},
    "clientInfo": {
      "name": "ai-service",
      "version": "1.0.0"
    }
  }
}
```

这表示：

```text
Client 告诉 Server：
我支持哪个协议版本。
我具备哪些能力。
我是谁。
```

Server 成功响应可能是：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-11-25",
    "capabilities": {
      "tools": {
        "listChanged": true
      }
    },
    "serverInfo": {
      "name": "business-tools-mcp-server",
      "version": "1.0.0"
    }
  }
}
```

这表示：

```text
Server 接受初始化。
Server 声明自己支持 tools 能力。
Server 支持工具列表变化通知。
```

然后 Client 会发 initialized notification：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

这表示：

```text
Client 通知 Server：初始化完成，可以进入正常操作阶段。
```

先不要被字段吓到。

你只要理解这三步：

```text
Client 发 initialize request。
Server 回 initialize response。
Client 发 initialized notification。
```

### 8. tools/list 怎么看

`tools/list` 用来发现 Server 暴露了哪些工具。

请求：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

逐层解释：

```text
jsonrpc = 2.0：这是 JSON-RPC 2.0 消息。
id = 2：请求编号。
method = tools/list：我要列出工具。
params = {}：本次没有额外参数。
```

响应：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "query_order",
        "description": "查询当前用户有权查看的订单摘要",
        "inputSchema": {
          "type": "object",
          "properties": {
            "order_id": {
              "type": "string"
            }
          },
          "required": ["order_id"]
        }
      }
    ]
  }
}
```

这表示 Server 暴露了一个工具：

```text
工具名：query_order
用途：查询订单摘要
参数：order_id 是 string，必填
```

Host 拿到这些工具定义后，可能会做：

```text
保存到内部工具表。
转换成模型 API 的 tools schema。
根据用户权限过滤工具。
决定是否暴露给模型。
```

注意：

```text
tools/list 只是发现工具。
它不会执行工具。
```

### 9. tools/call 怎么看

`tools/call` 用来调用某个工具。

请求：

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "query_order",
    "arguments": {
      "order_id": "A1001"
    }
  }
}
```

逐层解释：

```text
method = tools/call：这是协议层工具调用方法。
params.name = query_order：要调用的具体工具名。
params.arguments.order_id = A1001：传给工具的业务参数。
```

响应：

```json
{
  "jsonrpc": "2.0",
  "id": 3,
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

这表示：

```text
id = 3 的 tools/call 请求成功。
工具 query_order 执行成功。
返回了订单摘要。
```

这里要分清三种 id：

```text
JSON-RPC id = 3：协议请求编号。
order_id = A1001：业务订单号。
trace_id：排查链路编号，通常在上下文或元数据里传递。
```

不要把它们混用。

### 10. list_changed notification 怎么看

如果 Server 声明支持 `listChanged`，工具列表变化时可以发通知。

例如：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

它表示：

```text
Server 通知 Client：我的工具列表发生变化。
```

Client 收到后通常不会回复。

因为 notification 不需要 response。

Host 可以选择：

```text
重新调用 tools/list。
刷新模型可用工具列表。
记录日志。
忽略不重要的变化。
```

这个机制很适合工具动态变化的场景。

比如：

```text
某个用户登录后可用工具变了。
某个插件启用或禁用了。
某个 Server 更新后新增了工具。
```

### 11. 协议错误和工具执行错误

这是本节必须提前讲清的重点。

MCP Tools 官方资料里区分两类错误：

```text
Protocol Error
Tool Execution Error
```

中文可以先理解成：

```text
协议错误：这条 MCP 请求本身不合法，或者请求的协议操作无法完成。
工具执行错误：协议请求合法，但工具业务执行失败。
```

#### 协议错误

例子：

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

这类错误说明：

```text
请求结构或协议层面有问题。
比如工具名不存在。
比如参数结构不符合 tools/call 的协议要求。
比如协议版本不匹配。
```

它走的是 JSON-RPC 的 `error`。

#### 工具执行错误

例子：

```json
{
  "jsonrpc": "2.0",
  "id": 4,
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

这类错误说明：

```text
协议层调用成功了。
Server 确实找到了这个工具，也执行了工具逻辑。
但业务结果是失败的。
```

它走的是 JSON-RPC 的 `result`，但结果里 `isError = true`。

这点非常容易混。

你要记住：

```text
JSON-RPC error 表示协议请求失败。
result.isError = true 表示工具业务执行失败。
```

放到我们项目：

```text
invalid_tool_name 更像协议错误。
ORDER_NOT_FOUND 更像工具执行错误。
ORDER_ACCESS_DENIED 更像工具执行错误。
Java service 500 可能会被包装成工具执行错误，也可能在严重情况下变成协议错误，具体取决于 MCP Server 的错误设计。
```

第 13 节会专门设计 MCP 错误处理。

### 12. MCP 通信和 HTTP API 的区别

对比一下你熟悉的 HTTP API。

HTTP REST：

```http
GET /internal/orders/A1001
```

MCP JSON-RPC：

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "query_order",
    "arguments": {
      "order_id": "A1001"
    }
  }
}
```

它们都能表达“查订单”，但抽象层不同。

| 维度 | HTTP REST API | MCP JSON-RPC |
| --- | --- | --- |
| 核心抽象 | 资源 URL 和 HTTP 方法 | 协议 method 和 params |
| 示例 | `GET /orders/A1001` | `tools/call` + `name=query_order` |
| 成功表达 | HTTP 状态码 + body | JSON-RPC `result` |
| 失败表达 | HTTP 状态码 + error body | JSON-RPC `error` 或工具结果 `isError=true` |
| 是否支持 notification | HTTP REST 本身不强调 | JSON-RPC 有单向 notification |
| 使用场景 | 业务 API | AI Host 和 MCP Server 的协议通信 |

注意：

```text
MCP Server 内部仍然可以调用 HTTP REST API。
```

例如：

```text
MCP tools/call query_order
  -> MCP Server 内部调用 JavaOrderClient
  -> JavaOrderClient 发 GET /internal/orders/A1001
  -> Java business service 返回结果
```

所以不是 MCP 替代 HTTP。

更准确：

```text
MCP 是 AI 接入层协议。
HTTP REST 仍然可以是下游业务服务协议。
```

### 13. Data layer 和 Transport layer 再放回通信里理解

第 3 节已经提过：

```text
Data layer 管消息语义。
Transport layer 管消息怎么传。
```

本节看到的：

```text
jsonrpc
id
method
params
result
error
notification
tools/list
tools/call
```

都属于 data layer 的重点。

transport layer 关心的是：

```text
这些 JSON-RPC 消息通过 stdio 传？
还是通过 Streamable HTTP 传？
连接如何建立？
HTTP 认证怎么做？
消息边界怎么切？
```

后续第 6 节会讲 transport。

现在先不要混：

```text
tools/list 是 MCP data layer method。
stdio / HTTP 是 transport。
```

同一个 `tools/list`，未来可以在不同 transport 上发送。

### 14. 把一次 query_order 放进 MCP 通信链路

结合当前项目，未来一次订单查询可能是：

```text
1. ai-service 作为 Host。
2. Host 内部创建 MCP Client。
3. MCP Client 连接 business-tools-mcp-server。
4. Client 发 initialize request。
5. Server 回 initialize response，声明支持 tools。
6. Client 发 notifications/initialized。
7. Client 发 tools/list。
8. Server 返回 query_order 工具定义。
9. Host 把 query_order 转成模型 tools schema。
10. 用户问：A1001 订单到哪了？
11. 模型通过 Tool Calling 选择 query_order。
12. Host 校验工具名、参数、用户权限和策略。
13. MCP Client 发 tools/call，name=query_order，arguments.order_id=A1001。
14. MCP Server 内部调用 JavaOrderClient。
15. JavaOrderClient 调 Java business service。
16. Server 把工具结果包装成 MCP tools/call response。
17. Host 把工具结果交回模型总结。
18. 模型生成中文回答。
```

这条链路里，本节重点是：

```text
第 4 到第 8 步的通信基础。
第 13 和第 16 步的 tools/call request/response。
```

本节不重点讲：

```text
模型怎么选择工具。
JavaOrderClient 怎么写。
Java business service 怎么查数据库。
LangGraph 节点怎么流转。
```

这些前面或后面会分别负责。

### 15. 看懂 MCP 消息的 5 步法

以后看到一条 MCP JSON 消息，可以按这个顺序读。

#### 第 1 步：看有没有 `method`

有 `method`，说明它是：

```text
request 或 notification。
```

没有 `method`，但有 `result` 或 `error`，说明它是：

```text
response。
```

#### 第 2 步：看有没有 `id`

有 `id`：

```text
如果同时有 method，就是 request。
如果同时有 result/error，就是 response。
```

没有 `id` 且有 `method`：

```text
notification。
```

#### 第 3 步：看 `method`

判断这是哪类操作：

```text
initialize：初始化。
tools/list：列工具。
tools/call：调工具。
resources/read：读资源。
prompts/get：取 prompt。
notifications/...：通知。
```

#### 第 4 步：看 `params`

判断本次请求参数。

如果是 `tools/call`，重点看：

```text
params.name
params.arguments
```

#### 第 5 步：看 `result` 或 `error`

如果是 response：

```text
有 result：协议请求成功。
有 error：协议请求失败。
result 里 isError=true：工具业务执行失败。
```

这 5 步足够你读懂大部分入门阶段 MCP 消息。

### 16. 当前项目里需要记住的映射

| MCP 通信字段 | 在我们项目里的理解 |
| --- | --- |
| `jsonrpc` | 协议版本标识，不是业务字段 |
| `id` | MCP 请求编号，不是 order_id，也不是 trace_id |
| `method` | MCP 协议方法，例如 `tools/list`、`tools/call` |
| `params.name` | 具体工具名，例如 `query_order` |
| `params.arguments` | 工具业务参数，例如 `order_id` |
| `result` | 协议调用成功结果 |
| `error` | 协议调用失败 |
| `isError` | 工具执行失败标记，不等于 JSON-RPC error |
| `notifications/...` | 单向通知，不需要 response |

这张表非常重要。

后续写代码时，如果你混了这些字段，会出现典型错误：

```text
把 JSON-RPC id 当成订单号。
把 query_order 写成 MCP method。
把业务错误直接包装成 JSON-RPC error。
收到 notification 还等待 response。
把 tools/list 当成工具执行。
```

### 17. 常见误区

#### 误区 1：JSON-RPC 就是 JSON

不对。

JSON 是格式。

JSON-RPC 是协议。

MCP 用 JSON-RPC 来表达请求、响应、通知和错误。

#### 误区 2：`id` 是业务 id

不对。

JSON-RPC 的 `id` 是协议请求编号。

业务 id 应该放在参数里，比如：

```text
params.arguments.order_id
```

#### 误区 3：`method` 应该写成 `query_order`

不准确。

在 MCP Tools 调用里，协议方法是：

```text
tools/call
```

具体工具名是：

```text
params.name = query_order
```

#### 误区 4：所有失败都走 JSON-RPC `error`

不对。

协议错误走 `error`。

工具业务失败可以走：

```text
result.isError = true
```

比如订单不存在、无权限、参数业务含义不合法，往往更适合作为工具执行错误。

#### 误区 5：notification 也要返回 response

不对。

notification 是单向消息。

没有 `id`，也不应该等待 response。

### 18. 面试表达：怎么讲 MCP 通信基础

如果别人问：

```text
MCP Client 和 Server 是怎么通信的？
```

不要只说：

```text
用 JSON。
```

更好的回答：

```text
MCP 的基础通信遵循 JSON-RPC 2.0。Client 和 Server 之间主要交换 request、response 和 notification。request 有 id、method、params，response 用相同 id 返回 result 或 error，notification 没有 id，也不需要回复。
```

再补项目理解：

```text
比如 Host 想发现工具，会通过 MCP Client 发送 method=tools/list 的 request；想调用订单查询工具，会发送 method=tools/call，并在 params.name 里放 query_order，在 params.arguments 里放 order_id。Server 返回 result 表示协议调用成功，如果工具业务失败，可以在 result 里用 isError=true 表达。
```

最后补边界：

```text
MCP 的 JSON-RPC 通信是 AI 接入层协议，不等于下游 Java REST API。MCP Server 内部仍然可以通过 JavaOrderClient 调用 Java business service。
```

这样讲就比较完整。

## 本节结论

本节最重要的结论：

```text
MCP 通信基础是 JSON-RPC 2.0。
request 用 id + method + params 表示一次请求。
response 用相同 id 返回 result 或 error。
notification 有 method 但没有 id，不需要回复。
tools/list 是发现工具。
tools/call 是调用工具。
query_order 是工具名，不是 MCP method。
JSON-RPC id 是协议请求编号，不是业务 id。
协议错误走 error，工具执行错误可以走 result.isError=true。
```

放到项目里：

```text
ai-service 未来作为 Host，会通过 MCP Client 发送 tools/list 和 tools/call。
business-tools-mcp-server 会返回 query_order、create_ticket 等工具定义，并处理工具调用。
MCP Server 内部仍然应该调用 JavaOrderClient / JavaTicketClient，而不是绕过 Java business service。
```

## 本节练习

### 练习 1：判断下面消息类型

题目：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

参考答案：

```text
这是 request。
因为它有 id，也有 method。
它表示发送方请求执行 tools/list，并等待 response。
```

### 练习 2：判断下面消息类型

题目：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": []
  }
}
```

参考答案：

```text
这是成功 response。
因为它有 id，有 result，没有 method。
它对应 id = 1 的 request。
```

### 练习 3：判断下面消息类型

题目：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

参考答案：

```text
这是 notification。
因为它有 method，但没有 id。
它是单向通知，不需要 response。
```

### 练习 4：下面这个 tools/call 里，协议方法和业务工具名分别是什么？

题目：

```json
{
  "jsonrpc": "2.0",
  "id": 3,
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
业务工具名是 query_order。
业务参数是 order_id = A1001。
id = 3 是 JSON-RPC 请求编号，不是订单号。
```

### 练习 5：协议错误和工具执行错误有什么区别？

参考答案：

```text
协议错误表示 MCP 请求本身失败，例如 method 不存在、工具名不存在、参数结构不符合协议要求，通常走 JSON-RPC error。
工具执行错误表示协议请求成功到达并执行了工具，但业务执行失败，例如订单不存在、无权限、业务参数不合法，通常可以走 result.isError=true。
```

### 练习 6：为什么 notification 没有 id？

参考答案：

```text
因为 notification 是单向消息，不期待 response。
id 的作用是匹配 request 和 response。
如果 notification 有 id，就意味着发送方期待回复，这和 notification 的语义冲突。
```

### 练习 7：MCP 通信和 Java REST API 是什么关系？

参考答案：

```text
MCP 通信是 AI Host 和 MCP Server 之间的协议层通信。
Java REST API 是 MCP Server 或 Python client 调用真实业务服务时使用的下游业务接口。
MCP 不替代 Java REST API，MCP Server 内部仍然可以通过 JavaOrderClient 调 Java business service。
```

## 自测题

### 自测 1：下面这个 `id` 是不是订单号？

题目：

```json
{
  "jsonrpc": "2.0",
  "id": 1001,
  "method": "tools/list"
}
```

参考答案：

```text
不是。
这里的 id 是 JSON-RPC 请求编号，用来匹配 response。
订单号应该放在业务参数里，例如 params.arguments.order_id。
```

### 自测 2：`tools/list` 会不会执行工具？

参考答案：

```text
不会。
tools/list 只是列出 Server 暴露了哪些工具。
真正调用工具的是 tools/call。
```

### 自测 3：如果要调用 `query_order`，MCP method 应该写什么？

参考答案：

```text
MCP method 应该是 tools/call。
query_order 应该放在 params.name 里。
order_id 应该放在 params.arguments 里。
```

### 自测 4：成功 response 一定表示业务成功吗？

参考答案：

```text
不一定。
成功 response 的 result 表示协议请求成功。
如果是工具调用，result 里还可能有 isError=true，表示工具业务执行失败。
```

### 自测 5：为什么不能收到 notification 后等待 response？

参考答案：

```text
因为 notification 没有 id，不期待 response。
如果接收方还等待 response，程序可能会一直挂起或出现状态错误。
```

### 自测 6：`initialize` 的作用是什么？

参考答案：

```text
initialize 是 Client 和 Server 正常操作前的初始化请求。
它用于协议版本协商、能力协商和交换双方实现信息。
初始化成功后，Client 会发送 notifications/initialized，表示可以进入正常操作阶段。
```

### 自测 7：如果 Server 返回 JSON-RPC `error`，Host 应该直接交给模型吗？

参考答案：

```text
通常不应该直接原样交给模型。
Host 应该先判断错误类型，记录日志，做安全映射和用户可见信息处理。
协议错误往往不适合直接暴露给用户。
后续第 13 节会专门学习 MCP 错误处理。
```

## 本节总结

这一节要真正记住的是：

```text
MCP 通信不是随便传 JSON，而是基于 JSON-RPC 2.0 的结构化协议通信。
request 有 id、method、params。
response 用相同 id 返回 result 或 error。
notification 有 method 但没有 id，不需要回复。
tools/list 用来发现工具。
tools/call 用来调用工具。
业务工具名放在 params.name。
工具业务参数放在 params.arguments。
```

你以后看到 MCP 消息，先按这个顺序读：

```text
1. 看有没有 method。
2. 看有没有 id。
3. 判断 request / response / notification。
4. 看 method 是什么协议操作。
5. 看 params、result 或 error。
```

下一节学习：

```text
阶段 8 第 5 节：MCP 生命周期
```
