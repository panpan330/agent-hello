# 阶段 8 第 5 节：MCP 生命周期

## 本节定位

本节是阶段 8 第 5 节。

前面几节我们已经学到：

```text
第 1 节：MCP 是什么。
第 2 节：MCP 和 Tool Calling 的区别。
第 3 节：MCP 架构，理解 Host、Client、Server。
第 4 节：MCP 通信基础，理解 JSON-RPC、request、response、notification。
```

这一节继续往下走：

```text
一个 MCP Client 和 MCP Server 建立连接后，是不是立刻就能 tools/list 或 tools/call？
```

答案是：

```text
不能。
```

MCP 连接有严格的生命周期。

本节最重要的一句话：

```text
MCP 生命周期分为 Initialization、Operation、Shutdown 三个阶段；Client 和 Server 必须先完成初始化、协议版本协商和能力协商，才能进入正常通信阶段。
```

你可以把 MCP 生命周期理解成一套状态机：

```text
未连接
  -> 初始化中
  -> 已初始化
  -> 正常操作
  -> 关闭中
  -> 已关闭
```

后面写 MCP Server 时，如果你不理解生命周期，就容易犯这些错：

```text
一启动就直接调用 tools/list。
Server 还没返回 initialize，Client 就继续发业务请求。
Client 没发 notifications/initialized，Server 就开始发普通业务请求。
没检查协议版本就继续通信。
没看能力协商结果就调用 tools/call。
关闭时不清理连接和子进程。
请求超时后还一直等。
```

本节就是把这些顺序讲清楚。

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
MCP 生命周期为什么存在。
Initialization 初始化阶段做什么。
initialize request 里有什么。
initialize response 里有什么。
notifications/initialized 的作用是什么。
协议版本协商是什么。
能力协商是什么。
Operation 正常操作阶段能做什么。
为什么操作阶段只能使用协商成功的能力。
Shutdown 关闭阶段怎么理解。
stdio 和 HTTP 在关闭上的差异。
请求超时和初始化错误为什么必须处理。
这套生命周期和未来 ai-service 连接 MCP Server 的关系。
```

本节学完后，你应该能看懂并讲出这条顺序：

```text
Client -> initialize request
Server -> initialize response
Client -> notifications/initialized
Client/Server -> normal operations
Client/transport -> shutdown
```

## 本节不做什么

省 token 模式下，本节只做高质量主笔记。

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
生命周期概念讲解。
初始化消息拆解。
版本协商和能力协商讲解。
操作阶段和关闭阶段讲解。
项目映射。
练习和自测。
README 和进度索引更新。
```

## 官方资料依据

本节参考：

| 资料 | 本节使用点 |
| --- | --- |
| [MCP Lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) | Initialization、Operation、Shutdown，initialize request/response、initialized notification、版本协商、能力协商、超时和初始化错误 |
| [MCP Base Protocol Overview](https://modelcontextprotocol.io/specification/2025-11-25/basic) | MCP 基础协议、JSON-RPC 消息、request/response/notification |
| [MCP Architecture](https://modelcontextprotocol.io/specification/2025-11-25/architecture) | Host 创建 Client、Client 维护 Server 的 stateful session、协议协商和安全边界 |
| [MCP Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) | stdio 和 HTTP 关闭方式的背景，详细 transport 留到第 6 节 |

说明：

```text
本节只讲生命周期逻辑。
stdio 和 Streamable HTTP 的细节会在第 6 节展开。
错误处理的系统设计会在第 13 节展开。
```

## 基础知识铺垫

### 1. 什么叫生命周期

生命周期就是一个对象、连接、任务或服务从开始到结束的完整过程。

你在传统后端里已经见过很多生命周期。

比如 HTTP 请求生命周期：

```text
客户端发请求
-> 服务端接收请求
-> 过滤器/拦截器处理
-> Controller 处理
-> Service 执行业务逻辑
-> Mapper 访问数据库
-> 返回响应
-> 请求结束
```

比如 Spring Bean 生命周期：

```text
创建对象
-> 注入依赖
-> 初始化
-> 使用
-> 销毁
```

比如数据库连接生命周期：

```text
创建连接
-> 认证
-> 执行 SQL
-> 提交或回滚
-> 关闭连接
```

这些生命周期的共同点是：

```text
不能跳步骤。
每一步都有前置条件。
不同阶段允许做的事情不一样。
错误处理方式也不一样。
```

MCP 生命周期也是这个逻辑。

### 2. 为什么连接不能一建立就直接调用工具

假设 MCP Client 一连上 Server 就发：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

看起来好像没问题。

但 Server 可能还不知道：

```text
Client 支持哪个协议版本。
Client 支持哪些能力。
Client 的实现信息是什么。
Client 是否能处理 Server 后续发来的某些请求或通知。
```

Client 也不知道：

```text
Server 支持哪个协议版本。
Server 是否支持 tools。
Server 是否支持 resources。
Server 是否支持 prompts。
Server 是否支持 listChanged。
Server 的实现信息是什么。
```

如果这些都不知道，就直接操作，会有问题。

比如：

```text
Client 调 tools/list，但 Server 根本不支持 tools。
Client 想读 resources，但 Server 没声明 resources。
Client 使用新协议字段，但 Server 只支持旧协议。
Server 发送 list_changed notification，但 Client 没准备好处理。
```

所以 MCP 规定：

```text
正常操作前，必须先初始化和协商。
```

这和传统开发里很像。

你不会在数据库连接还没建立好时就发 SQL。

你也不会在 HTTP token 还没校验时就执行写操作。

### 3. 生命周期解决的核心问题

MCP 生命周期主要解决四个问题。

#### 问题 1：协议版本是否兼容

Client 可能支持：

```text
2025-11-25
```

Server 可能支持：

```text
2025-11-25
```

那可以继续。

如果 Client 支持新版本，Server 只支持旧版本，就要协商。

如果最终没有双方都能接受的版本，就应该断开。

#### 问题 2：双方支持哪些能力

Server 可能支持：

```text
tools
resources
prompts
logging
```

Client 可能支持：

```text
roots
sampling
elicitation
```

双方需要先声明能力。

后续正常操作只能使用已经协商成功的能力。

#### 问题 3：连接状态是否明确

生命周期让双方知道现在处于哪个阶段：

```text
还没初始化。
初始化中。
已经初始化。
正常操作中。
关闭中。
已关闭。
```

不同阶段允许的消息不同。

#### 问题 4：失败时怎么处理

生命周期也要求考虑失败：

```text
协议版本不匹配。
能力协商失败。
初始化 request 超时。
Server 初始化返回 error。
正常操作请求超时。
关闭时 Server 不退出。
```

这些如果不处理，AI 应用就会卡死或暴露错误。

### 4. 先记住完整顺序

先把顺序背熟，再理解细节。

```text
1. Host 创建 MCP Client。
2. Client 建立到 Server 的 transport 连接。
3. Client 发送 initialize request。
4. Server 返回 initialize response。
5. Client 检查协议版本和能力。
6. Client 发送 notifications/initialized。
7. 双方进入 Operation 正常操作阶段。
8. Client 可以发送 tools/list、tools/call、resources/read 等请求。
9. 一方发起关闭。
10. transport 关闭连接或子进程退出。
```

图示：

```text
MCP Client                         MCP Server
    |                                  |
    | -------- initialize -----------> |
    | <------ initialize result ------- |
    | --- notifications/initialized -> |
    |                                  |
    | -------- tools/list -----------> |
    | <------ tools/list result ------- |
    |                                  |
    | -------- tools/call -----------> |
    | <------ tools/call result ------- |
    |                                  |
    | -------- shutdown by transport --|
```

本节所有内容都围绕这张图展开。

## 本节主题系统讲解

### 1. MCP 生命周期三阶段

MCP 生命周期分三段：

| 阶段 | 中文理解 | 主要任务 |
| --- | --- | --- |
| Initialization | 初始化阶段 | 版本协商、能力协商、交换实现信息 |
| Operation | 正常操作阶段 | 按协商能力发送请求、响应和通知 |
| Shutdown | 关闭阶段 | 通过底层 transport 结束连接 |

这三个阶段不能乱序。

正确顺序是：

```text
Initialization -> Operation -> Shutdown
```

错误顺序：

```text
Operation -> Initialization
```

比如一连接就 `tools/call`，就是错误理解。

### 2. Initialization 是什么

Initialization 是 Client 和 Server 的第一次正式交互。

官方要求初始化阶段是两者之间的 first interaction。

这个阶段做三件事：

```text
建立协议版本兼容性。
交换并协商能力。
交换双方实现信息。
```

不要把 Initialization 理解成“连接上了”。

更准确：

```text
transport 连接只是通道建立。
Initialization 是协议会话建立。
```

类比：

```text
TCP 连上服务器，只说明路通了。
登录成功、协议版本匹配、权限确认后，才说明业务会话可用。
```

MCP 也是一样。

### 3. initialize request

初始化由 Client 发起。

Client 发送 `initialize` request。

简化示例：

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

逐字段看：

| 字段 | 含义 |
| --- | --- |
| `jsonrpc` | JSON-RPC 版本 |
| `id` | 本次 initialize 请求编号 |
| `method` | 协议方法，这里是 `initialize` |
| `params.protocolVersion` | Client 支持或希望使用的 MCP 协议版本 |
| `params.capabilities` | Client 声明自己支持的能力 |
| `params.clientInfo` | Client 的实现信息 |

这里要特别注意：

```text
protocolVersion 是 MCP 协议版本，不是你的项目版本。
clientInfo.version 是 Client 实现版本，不是 MCP 协议版本。
```

比如：

```text
protocolVersion = 2025-11-25
clientInfo.version = 1.0.0
```

前者是协议规范版本。

后者是你写的 Client 程序版本。

### 4. initialize response

Server 收到 initialize request 后，要返回自己的协议版本、能力和实现信息。

简化示例：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-11-25",
    "capabilities": {
      "tools": {
        "listChanged": true
      },
      "resources": {},
      "prompts": {}
    },
    "serverInfo": {
      "name": "business-tools-mcp-server",
      "version": "1.0.0"
    }
  }
}
```

逐字段看：

| 字段 | 含义 |
| --- | --- |
| `id` | 对应 Client 的 initialize request |
| `result.protocolVersion` | Server 最终返回的协议版本 |
| `result.capabilities` | Server 声明自己支持的能力 |
| `result.serverInfo` | Server 的实现信息 |

这条 response 表示：

```text
Server 支持 MCP 协议版本 2025-11-25。
Server 支持 tools，且支持工具列表变化通知。
Server 也声明了 resources 和 prompts 能力。
Server 名字是 business-tools-mcp-server。
```

如果 Server 不支持 Client 请求的版本，它可能返回另一个自己支持的版本。

如果 Client 不支持 Server 返回的版本，就应该断开。

### 5. notifications/initialized

初始化成功后，Client 还要发送一个 notification：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

这条消息没有 `id`。

因为它是 notification，不需要 response。

它的含义是：

```text
Client 告诉 Server：初始化流程完成，我已经准备好进入正常操作阶段。
```

这个 notification 很关键。

官方生命周期里明确说：

```text
Client 在 Server 响应 initialize 前，不应该发送除 ping 外的其他请求。
Server 在收到 initialized notification 前，也不应该发送除 ping 和 logging 外的其他请求。
```

不用死背这句话，但要理解它的工程含义：

```text
双方还没完成握手前，不要急着进入正常业务通信。
```

### 6. Version Negotiation 协议版本协商

协议版本协商解决的是：

```text
Client 和 Server 到底按哪一版 MCP 规范说话？
```

比如 Client 发：

```json
{
  "protocolVersion": "2025-11-25"
}
```

Server 如果支持这个版本，可以返回同样版本：

```json
{
  "protocolVersion": "2025-11-25"
}
```

如果 Server 不支持 Client 请求的版本，可能返回自己支持的版本。

然后 Client 要判断：

```text
我是否支持 Server 返回的版本？
```

如果支持：

```text
继续。
```

如果不支持：

```text
断开连接。
```

为什么不能强行继续？

因为不同协议版本可能存在：

```text
字段变化。
能力变化。
语义变化。
错误处理变化。
transport 细节变化。
```

强行继续可能导致：

```text
Client 以为 Server 支持某个字段，但 Server 不认识。
Server 以为 Client 能处理某种通知，但 Client 处理不了。
工具结果结构解释错。
安全策略漏掉。
```

所以版本协商不是形式主义。

它是兼容性边界。

### 7. Capability Negotiation 能力协商

能力协商解决的是：

```text
这次连接里，双方能用哪些功能？
```

Server 能力可能包括：

```text
tools
resources
prompts
logging
completions
tasks
experimental
```

Client 能力可能包括：

```text
roots
sampling
elicitation
tasks
experimental
```

你现在不需要深入每个能力。

阶段 8 目前最重要的是 Server 能力：

| Server capability | 中文理解 | 后续学习 |
| --- | --- | --- |
| `tools` | Server 暴露可调用工具 | 第 7 节 |
| `resources` | Server 暴露可读取资源 | 第 8 节 |
| `prompts` | Server 暴露 prompt 模板 | 第 9 节 |
| `logging` | Server 可以发日志消息 | 第 23 节会联系可观测性 |

能力协商的规则很重要：

```text
Operation 阶段只能使用协商成功的能力。
```

比如 Server 没声明 `tools`：

```text
Client 不应该调用 tools/list 或 tools/call。
```

比如 Server 声明了 `tools`，但没有声明 `resources`：

```text
Client 可以列工具，但不应该读取 resources。
```

这和后端里“接口是否存在”“权限是否具备”很像。

你不能因为自己想调用，就假设对方支持。

### 8. listChanged 和 subscribe 这种子能力

能力里还可能有子能力。

例如：

```json
{
  "tools": {
    "listChanged": true
  }
}
```

这里表示：

```text
Server 支持 tools 能力。
并且工具列表变化时，可以发 list_changed notification。
```

资源能力里可能有：

```json
{
  "resources": {
    "subscribe": true,
    "listChanged": true
  }
}
```

可以理解为：

```text
subscribe：Client 可以订阅资源变化。
listChanged：资源列表变化时 Server 可以通知。
```

本节不展开资源订阅。

你现在只要知道：

```text
capability 不是只有有没有，还可能带子能力。
Host / Client 应该按协商结果决定后续行为。
```

### 9. Operation 正常操作阶段

初始化完成后，进入 Operation 阶段。

这时 Client 和 Server 才能按协商能力正常交换消息。

常见操作：

```text
tools/list
tools/call
resources/list
resources/read
prompts/list
prompts/get
notifications/tools/list_changed
notifications/resources/list_changed
logging
progress
```

Operation 阶段有两个核心约束：

```text
必须遵守协商后的协议版本。
只能使用协商成功的能力。
```

例如：

```text
initialize response 里 Server 声明了 tools。
Client 才能 tools/list。
```

如果 Server 没声明 tools，Client 还去 tools/list，就是 Client 的问题。

这和 Java 后端调用下游接口也很像：

```text
契约里没有这个接口，你不能假装有。
权限里没有这个能力，你不能强行调。
```

### 10. 为什么不能把 initialize 当成普通业务请求

`initialize` 虽然也是 JSON-RPC request，但它不是普通业务请求。

它是会话建立请求。

区别：

| 维度 | initialize | tools/call |
| --- | --- | --- |
| 所在阶段 | Initialization | Operation |
| 作用 | 建立协议会话 | 调用工具 |
| 关注点 | 版本、能力、实现信息 | 工具名、工具参数、工具结果 |
| 能否重复随便发 | 不应该当普通业务方法反复发 | 可按需要多次调用 |

这就像登录接口和业务接口的区别。

登录接口决定你是否进入系统。

业务接口是在进入系统后使用的。

MCP 里：

```text
initialize 决定会话能不能建立。
tools/list、tools/call 是会话建立后的业务能力使用。
```

### 11. Shutdown 关闭阶段

Shutdown 是连接结束阶段。

官方生命周期里说，关闭阶段没有专门定义某个固定 shutdown 消息。

而是通过底层 transport 来表示连接终止。

这点很重要。

也就是说，不要想当然认为一定有：

```text
method = shutdown
```

本节先按两种 transport 简单理解。

#### stdio 场景

stdio 通常是本地进程通信。

Client 可能启动一个本地 MCP Server 子进程。

关闭时通常是：

```text
Client 关闭写入 Server 的输入流。
等待 Server 退出。
如果 Server 没及时退出，发送 SIGTERM。
如果还不退出，再发送 SIGKILL。
```

Windows 上细节可能和 Unix 信号不同，但学习重点是：

```text
关闭 stdio Server，本质上是结束本地进程和输入输出流。
```

#### HTTP 场景

HTTP transport 下，关闭通常通过关闭相关 HTTP 连接来表示。

学习重点：

```text
HTTP 场景的 shutdown 更像关闭网络连接或会话。
```

详细 transport 机制第 6 节讲。

### 12. 请求超时

生命周期里还提到超时。

为什么超时重要？

因为请求可能卡住。

比如：

```text
initialize request 发出去，Server 不回。
tools/call 调用外部系统，外部系统卡住。
Server 正在处理长任务但没有正常反馈。
网络连接异常。
```

如果没有超时，Host 可能一直等。

这会导致：

```text
用户请求卡死。
线程或连接被占用。
Agent 流程无法继续。
资源泄漏。
服务雪崩。
```

所以实现时应该给请求设置超时。

超时后通常要：

```text
停止等待 response。
必要时发送 cancellation notification。
记录日志。
把错误映射成用户可理解的提示。
释放资源。
```

第 13 节错误处理和第 23 节可观测性会继续展开。

现在你先知道：

```text
生命周期不是只讲正常路径，也必须考虑卡住和失败。
```

### 13. 初始化失败

初始化失败常见原因：

```text
协议版本不支持。
必需能力协商失败。
Server 启动失败。
Server 返回 error。
initialize 超时。
transport 连接建立失败。
```

例如协议版本不支持，可能返回：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Unsupported protocol version",
    "data": {
      "supported": ["2024-11-05"],
      "requested": "2025-11-25"
    }
  }
}
```

这时 Client 不应该继续发：

```text
tools/list
tools/call
resources/read
```

而应该：

```text
标记该 Server 不可用。
记录初始化失败原因。
不把这个 Server 的能力暴露给模型。
给用户或日志一个安全提示。
必要时降级。
```

放到我们项目里：

```text
如果 business-tools-mcp-server 初始化失败，ai-service 不应该还告诉模型 query_order 可用。
```

否则模型可能选择一个根本不可执行的工具。

### 14. 生命周期和 Host 的关系

第 3 节讲过：

```text
Host 创建和管理多个 Client。
每个 Client 连接一个 Server。
```

生命周期就是 Host 管理 Client 的重要依据。

Host 需要知道每个 Client 的状态：

```text
未连接
初始化中
初始化成功
初始化失败
正常操作中
关闭中
已关闭
```

如果 Host 连接多个 Server：

```text
Order MCP Server
Docs MCP Server
Prompt MCP Server
```

每个连接都有自己的生命周期。

可能出现：

```text
Order Server 初始化成功。
Docs Server 初始化失败。
Prompt Server 还在初始化中。
```

Host 不能把它们混成一个状态。

应该分别处理：

```text
Order tools 可以使用。
Docs resources 暂时不可用。
Prompt templates 暂时不暴露。
```

这就是为什么 MCP Client 和 Server 通常一对一。

生命周期状态也更容易隔离。

### 15. 生命周期和 tools/list 的关系

`tools/list` 是 Operation 阶段的操作。

所以正确顺序是：

```text
initialize
-> initialize response
-> notifications/initialized
-> tools/list
```

错误顺序是：

```text
tools/list
-> initialize
```

或者：

```text
initialize
-> tools/list
-> initialize response
```

后者的问题是：

```text
Client 还没确认 Server 初始化结果，就提前发正常业务请求。
```

这会导致状态混乱。

学习阶段可以这样记：

```text
没握手，不列工具。
没协商，不调能力。
没完成 initialized，不进入正常操作。
```

### 16. 生命周期和用户体验

生命周期不只是底层协议问题，也会影响用户体验。

如果 MCP Server 初始化很慢：

```text
用户打开 AI 助手后，工具可能暂时不可用。
```

Host 可以选择：

```text
显示工具正在连接。
先只启用已初始化成功的工具。
对不可用 Server 降级。
给用户返回“订单服务暂时不可用，请稍后再试”。
后台重试连接。
```

如果 Server 正常操作中掉线：

```text
Host 要把对应能力从可用工具列表中移除或标记不可用。
```

如果 shutdown 没处理好：

```text
本地 MCP Server 子进程可能残留。
连接可能泄漏。
下次启动可能端口或进程冲突。
```

所以生命周期是工程稳定性的基础。

### 17. 生命周期和安全边界

生命周期还能帮助安全控制。

比如初始化阶段：

```text
Host 可以决定是否允许连接这个 Server。
Host 可以检查 Server 信息。
Host 可以检查 Server 声明的能力。
Host 可以决定哪些能力暴露给模型。
```

Operation 阶段：

```text
Host 只使用协商成功的能力。
Host 按用户权限过滤工具。
Host 对写操作做确认。
Host 对工具结果做脱敏和校验。
```

Shutdown 阶段：

```text
Host 清理连接。
Host 停止暴露该 Server 的能力。
Host 释放资源。
```

所以：

```text
生命周期不是安全的全部，但它给安全控制提供了明确时机。
```

### 18. 生命周期和我们项目的未来映射

未来如果我们把订单工具包装成 MCP Server，可能是：

```text
ai-service Host
  |
  v
MCP Client
  |
  v
business-tools-mcp-server
  |
  v
JavaOrderClient / JavaTicketClient
  |
  v
Java business service
```

启动时：

```text
ai-service 创建 business-tools MCP Client。
Client 建立连接。
Client 发 initialize。
business-tools-mcp-server 返回 protocolVersion 和 tools capability。
Client 发 notifications/initialized。
Client 发 tools/list。
Server 返回 query_order 和 create_ticket。
ai-service 根据权限和安全策略决定是否暴露给模型。
```

用户请求时：

```text
模型选择 query_order。
Host 校验。
Client 发 tools/call。
MCP Server 调 JavaOrderClient。
JavaOrderClient 调 Java business service。
结果返回。
```

关闭时：

```text
ai-service 停止或重启。
MCP Client 关闭连接。
本地 Server 子进程退出，或 HTTP 连接关闭。
Host 不再暴露该 Server 的工具。
```

### 19. 一张完整状态表

| 状态 | 允许做什么 | 不应该做什么 |
| --- | --- | --- |
| 未连接 | 创建 Client、准备连接配置 | 调 tools/list |
| transport 已连接 | 发 initialize | 直接 tools/call |
| 初始化中 | 等 initialize response，处理版本和能力 | 提前进入正常操作 |
| initialized 已发送 | 进入 Operation | 重新乱发 initialize |
| Operation | 按协商能力正常通信 | 调未协商能力 |
| 关闭中 | 关闭流、连接或子进程 | 发新的业务请求 |
| 已关闭 | 清理状态、标记不可用 | 继续暴露工具 |

这张表后面写代码时很有用。

### 20. 常见误区

#### 误区 1：连接建立等于初始化完成

不对。

transport 连接只是通道建立。

initialize 成功并发送 initialized notification 后，才算协议初始化完成。

#### 误区 2：Server 声明了 tools，模型就一定能用所有工具

不对。

Server 声明 tools 只是说明协议能力存在。

Host 还要根据：

```text
用户权限
租户
工具风险等级
写操作确认策略
模型上下文
```

决定哪些工具暴露给模型。

#### 误区 3：能力协商只是文档说明

不对。

能力协商会影响 Operation 阶段能不能调用某类方法。

Server 没声明 resources，Client 就不应该 resources/read。

#### 误区 4：Shutdown 一定有一个 `shutdown` method

不对。

MCP 生命周期里关闭通常由 transport 表示。

stdio 是关闭流和进程。

HTTP 是关闭相关连接。

#### 误区 5：初始化失败后还能降级调用工具

一般不应该。

如果初始化失败，说明协议会话没有建立成功。

Host 不应该把该 Server 的工具暴露给模型。

可以做的是：

```text
降级为“不使用该 Server”。
返回安全提示。
记录日志。
稍后重试连接。
```

### 21. 面试表达：怎么讲 MCP 生命周期

如果别人问：

```text
MCP Client 和 Server 建立连接后流程是什么？
```

不要只说：

```text
先初始化再调用工具。
```

更好的回答：

```text
MCP 连接有明确生命周期，分为 Initialization、Operation、Shutdown。初始化阶段由 Client 发送 initialize request，里面包含协议版本、Client capabilities 和 clientInfo；Server 返回 initialize response，声明协议版本、Server capabilities 和 serverInfo；初始化成功后 Client 再发送 notifications/initialized，之后才进入正常 Operation 阶段。
```

再补工程边界：

```text
Operation 阶段只能使用协商成功的能力，例如 Server 声明了 tools 才能 tools/list 或 tools/call。关闭阶段没有固定 shutdown method，通常由底层 transport 关闭连接或进程。实现时还要处理版本不匹配、能力协商失败和请求超时。
```

结合项目可以说：

```text
在我们的项目里，ai-service 未来作为 Host，连接 business-tools-mcp-server 时，必须先完成 initialize 和能力协商，确认 Server 支持 tools 后，才能发现 query_order、create_ticket 并暴露给模型；如果初始化失败，就不能让模型继续选择这些工具。
```

这样讲就不是背概念，而是能落到真实工程。

## 本节结论

本节最重要的结论：

```text
MCP 生命周期分为 Initialization、Operation、Shutdown。
Initialization 负责协议版本协商、能力协商和实现信息交换。
Client 先发 initialize request。
Server 返回 initialize response。
Client 再发 notifications/initialized。
之后才进入 Operation 正常通信阶段。
Operation 阶段只能使用协商成功的能力。
Shutdown 通常由底层 transport 关闭连接或进程来表达。
初始化失败、版本不匹配、能力不支持和请求超时都必须处理。
```

放到项目里：

```text
ai-service 未来不能一连接 MCP Server 就直接 tools/list。
必须先 initialize。
必须确认 Server 支持 tools。
必须把初始化失败的 Server 标记为不可用。
必须避免把不可用工具暴露给模型。
```

## 本节练习

### 练习 1：MCP 生命周期分为哪三个阶段？

参考答案：

```text
Initialization、Operation、Shutdown。
Initialization 负责初始化、版本协商和能力协商。
Operation 负责正常协议通信。
Shutdown 负责关闭连接或进程。
```

### 练习 2：为什么不能一连接上就直接 `tools/list`？

参考答案：

```text
因为 Client 和 Server 还没有完成 initialize，没有确认协议版本是否兼容，也没有确认 Server 是否支持 tools 能力。
如果直接 tools/list，可能调用了对方不支持的能力，导致协议状态混乱。
```

### 练习 3：`initialize request` 里通常包含哪些重要信息？

参考答案：

```text
通常包含 protocolVersion、Client capabilities 和 clientInfo。
protocolVersion 表示 Client 支持或希望使用的 MCP 协议版本。
capabilities 表示 Client 支持的能力。
clientInfo 表示 Client 实现信息。
```

### 练习 4：`initialize response` 里通常包含哪些重要信息？

参考答案：

```text
通常包含 protocolVersion、Server capabilities 和 serverInfo。
protocolVersion 表示 Server 最终返回的协议版本。
capabilities 表示 Server 支持的能力，例如 tools、resources、prompts。
serverInfo 表示 Server 实现信息。
```

### 练习 5：`notifications/initialized` 的作用是什么？

参考答案：

```text
它是 Client 在 initialize 成功后发送的 notification，用来告诉 Server：初始化流程完成，Client 已准备好进入正常操作阶段。
它没有 id，也不需要 response。
```

### 练习 6：如果 Server 没声明 `tools` 能力，Client 能不能 `tools/call`？

参考答案：

```text
不应该。
Operation 阶段只能使用协商成功的能力。
如果 Server 没声明 tools，Client 就不应该调用 tools/list 或 tools/call。
```

### 练习 7：初始化失败后 Host 应该怎么处理？

参考答案：

```text
Host 应该标记该 MCP Server 不可用，记录失败原因，不把该 Server 的工具、资源或 prompt 暴露给模型。
必要时可以降级、提示用户稍后再试，或者后台重试连接。
```

## 自测题

### 自测 1：transport 连接建立是否等于 MCP 初始化完成？

参考答案：

```text
不等于。
transport 连接只是通信通道建立。
MCP 初始化完成还需要 initialize request、initialize response，以及 Client 发送 notifications/initialized。
```

### 自测 2：`protocolVersion` 和 `clientInfo.version` 是不是同一个东西？

参考答案：

```text
不是。
protocolVersion 是 MCP 协议规范版本。
clientInfo.version 是 Client 程序自身版本。
```

### 自测 3：Operation 阶段最重要的两个约束是什么？

参考答案：

```text
必须遵守协商后的协议版本。
只能使用协商成功的能力。
```

### 自测 4：MCP Shutdown 一定要发送 `method=shutdown` 吗？

参考答案：

```text
不一定，也不应该想当然认为有固定 shutdown method。
MCP 生命周期里关闭通常由底层 transport 表示，例如 stdio 关闭输入流和进程，HTTP 关闭相关连接。
```

### 自测 5：如果 `business-tools-mcp-server` 初始化失败，模型还能选择 `query_order` 吗？

参考答案：

```text
不应该。
Host 不应该把初始化失败的 Server 提供的工具暴露给模型。
否则模型会选择一个实际不可执行的工具，导致用户体验和系统状态都变差。
```

### 自测 6：能力协商里的 `listChanged` 表示什么？

参考答案：

```text
它表示某类列表发生变化时，Server 可以发送对应的 list_changed notification。
例如 tools.listChanged=true 表示工具列表变化时 Server 可以通知 Client。
```

### 自测 7：为什么生命周期和安全边界有关？

参考答案：

```text
因为 Host 可以在初始化阶段决定是否允许连接 Server、检查 Server 声明的能力，并在 Operation 阶段只使用协商成功且经过权限策略过滤的能力。
生命周期给连接、能力暴露、工具调用和关闭清理提供了明确控制时机。
```

## 本节总结

这一节你要真正记住的是：

```text
MCP 不是连接上就能调工具。
MCP 连接先进入 Initialization，完成版本协商、能力协商和 initialized 通知后，才进入 Operation。
Operation 阶段只能使用协商成功的能力。
Shutdown 阶段通常由 transport 关闭连接或进程。
```

以后看到 MCP Client 连接 Server，你要先问：

```text
initialize 发了吗？
initialize response 成功了吗？
protocolVersion 兼容吗？
Server capabilities 里有没有我要用的能力？
notifications/initialized 发了吗？
当前 Client 状态是不是 Operation？
超时和初始化失败怎么处理？
```

下一节学习：

```text
阶段 8 第 6 节：MCP Transport
```
