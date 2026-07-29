# 阶段 8 第 6 节：MCP Transport

## 本节定位

本节是阶段 8 第 6 节。

前面几节已经学过：

```text
第 3 节：MCP 架构，理解 Host、Client、Server。
第 4 节：MCP 通信基础，理解 JSON-RPC request/response/notification。
第 5 节：MCP 生命周期，理解 initialize、operation、shutdown。
```

这一节解决一个很容易混的问题：

```text
JSON-RPC 消息到底通过什么通道传输？
```

这个“通道”就是 transport。

本节最重要的一句话：

```text
MCP 的 data layer 负责消息语义，例如 JSON-RPC、tools/list、tools/call；transport layer 负责消息传输通道，例如 stdio 和 Streamable HTTP。
```

你可以先这样理解：

```text
data layer 规定“说什么”。
transport layer 规定“怎么传”。
```

同一条 MCP 消息：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

可以通过：

```text
stdio
```

传给本地 MCP Server，也可以通过：

```text
Streamable HTTP
```

传给远程 MCP Server。

消息语义没变。

传输方式变了。

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
Transport 是什么。
data layer 和 transport layer 的区别。
stdio transport 是什么。
为什么本地 MCP Server 常用 stdio。
stdin、stdout、stderr 分别是什么。
为什么 stdout 只能输出合法 MCP 消息。
为什么日志应该写 stderr。
Streamable HTTP transport 是什么。
Streamable HTTP 为什么适合远程 MCP Server。
HTTP POST、GET、SSE 在 MCP transport 里大概承担什么角色。
本地工具和远程服务怎么选择 transport。
Transport 和 JSON-RPC method 为什么不能混。
我们后面为什么先写本地 stdio MCP Server。
```

本节学完后，你应该能看到下面两个说法就立刻知道区别：

```text
tools/list 是 data layer 的 method。
stdio 是 transport layer 的通道。
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
Transport 概念讲解。
stdio 和 Streamable HTTP 对比。
本地/远程 MCP Server 选型讲解。
项目映射。
练习和自测。
README 和进度索引更新。
```

## 官方资料依据

本节参考：

| 资料 | 本节使用点 |
| --- | --- |
| [MCP Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) | MCP 使用 JSON-RPC 编码消息，标准 transport 包括 stdio 和 Streamable HTTP；stdio 的 stdin/stdout/stderr 规则；Streamable HTTP 的 POST、GET、SSE、session、安全要求 |
| [MCP Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture) | data layer 和 transport layer 的区别，本地 MCP Server 常用 STDIO，远程 MCP Server 常用 Streamable HTTP |
| [MCP Lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) | Transport 连接和 lifecycle 的关系，关闭阶段依赖底层 transport |

说明：

```text
本节只讲 Transport 基础和选型。
第 10 节写 Python 最小 MCP Server 时，会真正用到 stdio。
Streamable HTTP 的认证和生产化细节会留到后续安全、配置和可观测性章节。
```

## 基础知识铺垫

### 1. 什么是 Transport

Transport 可以翻译成“传输层”或“传输机制”。

它回答的是：

```text
消息通过什么通道从一方传到另一方？
```

比如你和别人沟通，内容可以一样，但通道可以不同：

```text
面对面说。
打电话。
发微信。
发邮件。
写纸条。
```

你说的话是 data。

你用什么方式传过去是 transport。

MCP 里也是这样。

MCP 消息内容可能是：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

它的传输通道可能是：

```text
stdio：通过本地进程的标准输入输出传。
Streamable HTTP：通过 HTTP 请求和可选 SSE 流传。
```

### 2. data layer 和 transport layer 再分清一次

MCP 分两层：

```text
data layer
transport layer
```

对比：

| 层 | 负责什么 | 例子 |
| --- | --- | --- |
| data layer | 消息结构和语义 | JSON-RPC、initialize、tools/list、tools/call、resources/read、notification |
| transport layer | 消息通道和传输细节 | stdio、Streamable HTTP、连接建立、消息 framing、认证 |

你可以这样记：

```text
data layer 是信的内容。
transport layer 是送信方式。
```

第 4 节学的：

```text
id
method
params
result
error
request
response
notification
```

都偏 data layer。

这一节学的：

```text
stdin
stdout
stderr
HTTP POST
HTTP GET
SSE
MCP endpoint
MCP-Session-Id
Origin 校验
```

都偏 transport layer。

### 3. 为什么 transport 不能和 method 混

初学时容易说出这种话：

```text
tools/list 是不是 stdio？
tools/call 是不是 HTTP？
```

这是混层了。

正确理解：

```text
tools/list 是 MCP data layer method。
stdio 是 transport。
HTTP 是 transport。
```

同一个 `tools/list` 可以通过 stdio 发送：

```text
Host -> 本地子进程 stdin
```

也可以通过 Streamable HTTP 发送：

```text
Host -> HTTP POST https://example.com/mcp
```

所以不要问：

```text
tools/list 是 stdio 还是 HTTP？
```

应该问：

```text
这条 tools/list 消息当前通过哪个 transport 发送？
```

### 4. 为什么 MCP 要支持多种 transport

因为 MCP Server 可能运行在不同位置。

#### 本地 Server

本地 Server 运行在用户机器上。

比如：

```text
读取本地文件。
读取本地项目代码。
操作本地命令行工具。
访问本机开发环境。
```

这种情况下，stdio 很合适。

原因：

```text
不需要开端口。
不需要网络。
启动一个本地子进程即可。
性能好。
调试直接。
适合个人开发环境。
```

#### 远程 Server

远程 Server 运行在公司或云平台上。

比如：

```text
公司订单 MCP Server。
公司工单 MCP Server。
GitHub MCP Server。
Sentry MCP Server。
远程知识库 MCP Server。
```

这种情况下，Streamable HTTP 更合适。

原因：

```text
可以被多个 Client 连接。
可以部署成独立服务。
可以使用标准 HTTP 认证。
可以跨机器访问。
可以支持长连接、流式消息、通知。
```

所以：

```text
本地个人工具：优先 stdio。
远程共享服务：优先 Streamable HTTP。
```

### 5. stdin、stdout、stderr 是什么

stdio transport 依赖标准输入输出。

先把三个概念讲清楚：

| 名称 | 中文理解 | 作用 |
| --- | --- | --- |
| `stdin` | 标准输入 | 程序从这里读输入 |
| `stdout` | 标准输出 | 程序把正常输出写到这里 |
| `stderr` | 标准错误 | 程序把日志、调试、错误信息写到这里 |

你在命令行里运行一个程序：

```powershell
python app.py
```

程序可能：

```text
从 stdin 读一行输入。
往 stdout 打印结果。
往 stderr 打印报错或日志。
```

MCP stdio transport 利用的就是这个机制。

区别是：

```text
stdout 不能随便 print 人类可读日志。
stdout 必须输出合法 MCP JSON-RPC 消息。
stderr 才适合输出日志。
```

这个要求非常重要。

## 本节主题系统讲解

### 1. MCP 标准 transport

MCP 当前标准 transport 主要包括：

```text
stdio
Streamable HTTP
```

官方资料还允许实现自定义 transport，但前提是：

```text
必须保留 MCP 的 JSON-RPC 消息格式和生命周期要求。
```

学习阶段不碰自定义 transport。

我们只需要先掌握：

```text
stdio：本地进程通信。
Streamable HTTP：远程 HTTP 通信。
```

### 2. stdio transport 是什么

stdio transport 的基本结构：

```text
MCP Host
  |
  | 启动子进程
  v
本地 MCP Server 进程

Host 写入 Server stdin
Server 从 stdin 读取 JSON-RPC 消息

Server 写入 stdout
Host 从 Server stdout 读取 JSON-RPC 消息

Server 写日志到 stderr
Host 可捕获、转发或忽略 stderr
```

图示：

```text
Host / Client
  |
  | JSON-RPC message
  v
Server stdin

Server stdout
  |
  | JSON-RPC message
  v
Host / Client

Server stderr
  |
  | log / debug / error text
  v
Host log system
```

一句话：

```text
stdio transport 就是 Host 启动本地 MCP Server 子进程，然后通过标准输入输出交换 JSON-RPC 消息。
```

### 3. stdio 的关键规则

stdio transport 有几条非常重要的规则。

#### 规则 1：Client 启动 Server 子进程

在 stdio 模式下，通常是 Client 启动 MCP Server。

例如概念上：

```text
command: python
args: ["server.py"]
```

Host/Client 启动这个命令后，就拿到：

```text
子进程 stdin
子进程 stdout
子进程 stderr
```

#### 规则 2：Server 从 stdin 读 MCP 消息

Host 要发 `initialize`：

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
```

就写到 Server 的 stdin。

Server 从 stdin 读到后，解析成 JSON-RPC request。

#### 规则 3：Server 往 stdout 写 MCP 消息

Server 要返回 response：

```json
{"jsonrpc":"2.0","id":1,"result":{}}
```

就写到 stdout。

Host 从 stdout 读取并解析。

#### 规则 4：每条消息用换行分隔

stdio 里，消息是一个个 JSON-RPC request/response/notification。

它们用换行分隔。

所以：

```text
每条 MCP 消息应该是一行。
消息内部不能嵌入换行。
```

如果你输出多行 JSON，Client 可能无法按行正确解析。

#### 规则 5：stdout 只能写合法 MCP 消息

这是最容易踩坑的规则。

Server 不允许往 stdout 写普通日志。

错误例子：

```python
print("server started")
```

如果这个 print 写到 stdout，Host 会尝试把它当成 MCP JSON-RPC 消息解析。

结果可能是：

```text
JSON 解析失败。
协议通信中断。
Client 以为 Server 输出了非法消息。
```

正确做法：

```text
日志写 stderr。
MCP 消息写 stdout。
```

#### 规则 6：stderr 可以写日志

Server 可以把 UTF-8 日志写到 stderr。

比如：

```text
server started
query_order called
Java service timeout
```

Host 可以：

```text
捕获 stderr。
转发到日志系统。
忽略 stderr。
显示给开发者调试。
```

但 Host 不应该简单认为：

```text
stderr 有输出 = Server 一定出错。
```

因为 stderr 也可能只是 info/debug 日志。

### 4. stdio 为什么适合本地 MCP Server

stdio 适合本地 Server，主要因为它简单。

不用：

```text
开 HTTP 端口。
配置域名。
配置 HTTPS。
处理跨域。
处理远程认证。
部署 Web 服务。
考虑公网暴露。
```

只需要：

```text
Host 知道启动命令。
Host 启动子进程。
双方用 stdin/stdout 传 JSON-RPC。
```

适合这些场景：

```text
本地文件系统。
本地项目文档。
本地代码分析。
本地开发工具。
个人机器上的临时工具。
学习阶段的最小 MCP Server。
```

所以我们后续第 10 节会先写本地 stdio MCP Server。

原因不是 stdio 比 HTTP 高级。

而是：

```text
stdio 更适合先理解 MCP 协议本身。
```

它能让你少受部署、认证、网络、SSE 这些干扰。

### 5. stdio 的限制

stdio 也有明显限制。

#### 限制 1：通常只适合本机

stdio 是进程间标准输入输出。

它不适合天然跨机器通信。

如果你要让很多用户都连接公司订单能力，stdio 不合适。

#### 限制 2：通常是一个 Client 对一个本地进程

本地 stdio Server 常见结构是：

```text
一个 Host 启动一个 Server 子进程。
一个 Server 子进程服务这个 Host 里的一个 Client。
```

不适合很多 Client 同时共享同一个进程。

#### 限制 3：stdout 污染会导致协议错误

如果代码里随手写：

```python
print("debug")
```

就可能破坏 stdout 上的 MCP 消息流。

#### 限制 4：认证不是 stdio 的重点

stdio 本地进程通常依赖：

```text
本机权限。
Host 配置。
文件系统权限。
环境变量。
```

不是像远程 HTTP 那样天然用 Bearer token、OAuth、网关认证。

如果要访问远程公司资源，stdio Server 内部仍然要自己处理 token 和下游权限。

### 6. Streamable HTTP transport 是什么

Streamable HTTP 是 MCP 的远程 HTTP transport。

可以先这样理解：

```text
Client 通过 HTTP POST 把 JSON-RPC 消息发给 Server。
Client 也可以通过 HTTP GET 打开 SSE 流，接收 Server 主动发来的消息。
Server 可以返回普通 JSON，也可以用 SSE 流返回多个消息。
```

基本结构：

```text
MCP Client
  |
  | HTTP POST /mcp
  v
Remote MCP Server

MCP Client
  |
  | HTTP GET /mcp
  v
SSE stream from Server
```

它适合远程独立服务。

比如：

```text
https://company.example.com/mcp
https://sentry.example.com/mcp
https://github-mcp.example.com/mcp
```

### 7. Streamable HTTP 的 MCP endpoint

Streamable HTTP 要求 Server 提供一个 MCP endpoint。

比如：

```text
https://example.com/mcp
```

这个 endpoint 支持：

```text
POST
GET
```

POST 主要用于：

```text
Client 把 JSON-RPC message 发给 Server。
```

GET 主要用于：

```text
Client 打开 SSE stream，接收 Server 主动发来的消息。
```

不要把它想成传统 REST 风格：

```text
GET /orders/A1001
POST /tickets
```

Streamable HTTP 的 URL 通常是一个统一 MCP endpoint。

具体要做什么，放在 JSON-RPC 的 `method` 里。

比如：

```text
POST /mcp
body.method = tools/list
```

或者：

```text
POST /mcp
body.method = tools/call
body.params.name = query_order
```

### 8. Streamable HTTP 里的 POST

Client 发 MCP 消息给 Server 时，用 HTTP POST。

例如：

```http
POST /mcp
Accept: application/json, text/event-stream
Content-Type: application/json
```

Body 是一个 JSON-RPC message：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

Server 可以选择：

```text
直接返回 application/json，一个 JSON-RPC response。
```

也可以选择：

```text
返回 text/event-stream，用 SSE stream 逐步发送消息。
```

这就是 Streamable HTTP 比普通“一问一答 HTTP”更灵活的地方。

### 9. Streamable HTTP 里的 GET 和 SSE

SSE 是 Server-Sent Events。

它可以让 Server 通过一条 HTTP 连接持续给 Client 推消息。

在 MCP Streamable HTTP 里，Client 可以发：

```http
GET /mcp
Accept: text/event-stream
```

如果 Server 支持，就返回：

```text
Content-Type: text/event-stream
```

然后 Server 可以在这个 stream 上发送：

```text
JSON-RPC request
JSON-RPC notification
```

适合：

```text
Server 主动通知工具列表变化。
Server 推送长任务进度。
Server 发日志。
Server 需要向 Client 侧请求某些能力。
```

这里先记住：

```text
SSE 是 transport 里的流式通道。
notification 是 data layer 里的单向消息。
```

两者不是一回事。

notification 可以通过 SSE 传。

SSE 也可以传其他 JSON-RPC 消息。

### 10. Streamable HTTP 的安全要求

远程 HTTP transport 风险更大。

官方资料特别强调了几个安全点。

#### Origin 校验

Server 应该校验 `Origin` header，防止 DNS rebinding 攻击。

学习阶段不需要深入攻击细节。

你先知道：

```text
远程或本地 HTTP Server 不能随便接受任意网页来源的请求。
```

#### 本地 HTTP Server 应该绑定 localhost

如果本地跑 HTTP MCP Server，应该优先绑定：

```text
127.0.0.1
```

不要随便绑定：

```text
0.0.0.0
```

因为 `0.0.0.0` 会监听所有网卡，可能让局域网或外部机器访问到本地 MCP Server。

这点和你之前在 VMware / Qdrant / Milvus 里见过的端口暴露问题很像。

#### 远程连接需要认证

远程 MCP Server 应该有认证。

比如：

```text
Bearer token
OAuth
API key
自定义 header
网关认证
```

但注意：

```text
认证不等于业务权限。
```

认证解决：

```text
你是谁？
```

业务权限还要解决：

```text
你能不能查这个订单？
你能不能创建这个工单？
你属于哪个租户？
```

所以即使用 Streamable HTTP，阶段 7 的 Java 权限边界仍然不能丢。

### 11. Streamable HTTP 的 session

Streamable HTTP 可以有 session。

Server 在初始化响应时，可能通过 HTTP header 返回：

```text
MCP-Session-Id
```

如果 Server 返回了这个 session id，Client 后续请求要带上它。

可以先这样理解：

```text
MCP-Session-Id 表示这次 Client 和 Server 之间的一组相关交互。
```

它不是：

```text
用户登录 session。
订单 id。
trace_id。
```

它是 MCP transport/session 层面的会话 id。

这点要分清。

如果把 MCP session id 和业务 user session 混起来，会带来安全和排查问题。

### 12. Streamable HTTP 的协议版本 header

HTTP transport 下，Client 后续请求需要带协议版本 header：

```text
MCP-Protocol-Version: 2025-11-25
```

它的作用是：

```text
让 Server 知道这次 HTTP 请求按哪个 MCP 协议版本处理。
```

这个版本通常应该是 initialize 阶段协商出来的版本。

不要把它和：

```text
应用版本。
API 版本。
模型版本。
```

混在一起。

### 13. stdio 和 Streamable HTTP 对比

| 维度 | stdio | Streamable HTTP |
| --- | --- | --- |
| 运行位置 | 通常本机 | 通常远程，也可本地 |
| 连接方式 | Host 启动 Server 子进程 | Client 连接 HTTP endpoint |
| 消息通道 | stdin/stdout | HTTP POST、GET、可选 SSE |
| 日志 | stderr | HTTP 日志、服务日志、SSE/请求日志 |
| 是否需要端口 | 不需要 | 需要 HTTP endpoint |
| 是否适合多人共享 | 不太适合 | 更适合 |
| 是否适合学习最小 Server | 很适合 | 稍复杂 |
| 认证复杂度 | 本机权限和配置为主 | 需要 HTTP 认证、安全 header、session 管理 |
| 典型场景 | 本地文件、代码、个人工具 | 公司服务、云平台、团队共享 MCP Server |

一句话：

```text
stdio 简单、本地、适合学习和个人工具。
Streamable HTTP 复杂一些，但适合远程共享、认证、多人连接和生产服务。
```

### 14. 本地工具和远程服务怎么选

你可以按下面的判断来选。

#### 选 stdio

如果满足：

```text
Server 跑在本机。
只服务当前 Host。
主要访问本地文件或本地项目。
不需要多人共享。
不想开端口。
学习或调试阶段。
```

优先 stdio。

例子：

```text
读取当前项目 notes/ 文档的 MCP Server。
读取本地 docs/ API 契约的 MCP Server。
本地练习用 Python MCP Server。
```

#### 选 Streamable HTTP

如果满足：

```text
Server 要部署到远程机器。
多个 Host 或多个用户要连接。
需要标准 HTTP 认证。
需要统一运维和监控。
需要更像生产服务。
需要跨机器访问。
```

优先 Streamable HTTP。

例子：

```text
公司订单 MCP Server。
公司工单 MCP Server。
公司知识库 MCP Server。
GitHub 类远程 MCP Server。
Sentry 类远程 MCP Server。
```

### 15. Transport 和 lifecycle 的关系

第 5 节讲过 lifecycle：

```text
Initialization
Operation
Shutdown
```

Transport 和 lifecycle 的关系是：

```text
transport 提供连接通道。
lifecycle 运行在这个通道上。
```

stdio 下：

```text
Host 启动子进程。
通过 stdin/stdout 发 initialize。
进入 Operation。
关闭 stdin 或终止子进程完成 shutdown。
```

Streamable HTTP 下：

```text
Client POST initialize 到 /mcp。
Server 可能返回 MCP-Session-Id。
后续 POST/GET 带 session 和 protocol version。
关闭 HTTP 连接或 DELETE session。
```

所以：

```text
transport 不替代 lifecycle。
lifecycle 也不替代 transport。
```

一个管通道。

一个管连接状态。

### 16. Transport 和我们项目的关系

当前项目还没有 MCP Server。

但后续可以这样规划。

#### 学习阶段

先写：

```text
本地 Python stdio MCP Server
```

它可以暴露：

```text
Tool: echo
Tool: query_order_fake
Resource: 项目 README
Prompt: 客服回答模板
```

先不接真实 Java。

目标是：

```text
把 MCP 协议跑通。
理解 initialize。
理解 tools/list。
理解 tools/call。
理解 stdout 只能输出 MCP 消息。
```

#### 项目集成阶段

再写：

```text
business-tools-mcp-server
```

它可以通过：

```text
JavaOrderClient
JavaTicketClient
```

调用：

```text
Java business service
```

这时仍然可以先用 stdio。

原因：

```text
本地学习简单。
不用部署远程 MCP Server。
不用先处理 HTTP 认证。
```

#### 更真实阶段

如果以后要让多个 Host 连接同一个业务 MCP Server，就可以考虑：

```text
Streamable HTTP MCP Server
```

部署方式可能是：

```text
ai-service Host
  |
  | Streamable HTTP
  v
business-tools-mcp-server
  |
  v
Java business service
```

这时要补：

```text
HTTP 认证。
Origin 校验。
MCP-Session-Id。
MCP-Protocol-Version。
日志和 metrics。
限流。
超时。
部署。
```

这些不急。

先把 stdio 学扎实。

### 17. 常见误区

#### 误区 1：stdio 就是普通 print 输出

不对。

stdio transport 里的 stdout 是 MCP 消息通道。

Server 写到 stdout 的内容必须是合法 MCP JSON-RPC 消息。

普通日志应该写 stderr。

#### 误区 2：Streamable HTTP 就是普通 REST API

不准确。

Streamable HTTP 用 HTTP 作为 transport。

但 MCP 操作仍然在 JSON-RPC body 里表达。

不是：

```text
GET /orders/A1001
```

而是：

```text
POST /mcp
body.method = tools/call
body.params.name = query_order
```

#### 误区 3：SSE 就是 notification

不对。

SSE 是 transport 上的流式传输方式。

notification 是 JSON-RPC 消息类型。

notification 可以通过 SSE 传，但 SSE 不等于 notification。

#### 误区 4：本地 HTTP MCP Server 绑定 0.0.0.0 没关系

有风险。

本地 HTTP Server 应该优先绑定 localhost。

绑定 0.0.0.0 可能让局域网其他机器访问到你的 MCP Server。

#### 误区 5：用了 MCP Transport 就不用业务权限

不对。

transport 只解决怎么传。

业务权限仍然要由 Host、MCP Server 和 Java business service 共同控制。

用户能不能查订单，不是 transport 决定的。

### 18. 面试表达：怎么讲 MCP Transport

如果别人问：

```text
MCP transport 是什么？
```

不要只说：

```text
就是 stdio 和 HTTP。
```

更好的回答：

```text
MCP 分 data layer 和 transport layer。data layer 定义 JSON-RPC 消息语义，例如 initialize、tools/list、tools/call；transport layer 定义这些消息通过什么通道传输。MCP 标准 transport 主要有 stdio 和 Streamable HTTP。
```

再补区别：

```text
stdio 用于本地进程通信，Host 通常启动 MCP Server 子进程，通过 stdin/stdout 交换 JSON-RPC 消息，日志应写 stderr，stdout 只能写合法 MCP 消息。它适合本地工具和学习阶段。
```

继续补：

```text
Streamable HTTP 用 HTTP POST/GET 和可选 SSE 承载 MCP 消息，适合远程共享 Server。它支持 HTTP 认证、session、流式服务端消息，但也要注意 Origin 校验、localhost 绑定和 MCP-Session-Id 等安全问题。
```

结合项目：

```text
在我们的项目里，后续会先用 stdio 写本地 Python MCP Server，降低学习复杂度；如果未来要把订单和工单 MCP Server 做成团队共享服务，再考虑 Streamable HTTP，并保留 Java business service 的权限、幂等、错误码和 trace_id 边界。
```

## 本节结论

本节最重要的结论：

```text
Transport 解决 MCP 消息怎么传。
data layer 解决 MCP 消息表达什么。
stdio 是本地进程间通过 stdin/stdout 传 JSON-RPC。
Streamable HTTP 是通过 HTTP POST/GET 和可选 SSE 传 JSON-RPC。
stdout 只能写合法 MCP 消息。
stderr 可以写日志。
本地 MCP Server 常用 stdio。
远程共享 MCP Server 更适合 Streamable HTTP。
```

放到项目里：

```text
阶段 8 后续先学 stdio。
因为我们要先把 MCP Server 的协议、生命周期、tools/list 和 tools/call 跑通。
等本地能力扎实后，再考虑远程 Streamable HTTP。
```

## 本节练习

### 练习 1：data layer 和 transport layer 有什么区别？

参考答案：

```text
data layer 负责 MCP 消息结构和语义，例如 JSON-RPC、initialize、tools/list、tools/call。
transport layer 负责消息传输通道和连接细节，例如 stdio、Streamable HTTP、连接建立、消息 framing 和认证。
```

### 练习 2：stdio transport 里 stdin、stdout、stderr 分别干什么？

参考答案：

```text
stdin 是 Server 读取 MCP JSON-RPC 消息的输入通道。
stdout 是 Server 输出 MCP JSON-RPC 消息的输出通道。
stderr 是 Server 输出日志、调试和错误文本的通道。
```

### 练习 3：为什么 MCP Server 不能随便 `print("started")`？

参考答案：

```text
如果 print 写到 stdout，Host 会把这行内容当作 MCP JSON-RPC 消息解析。
普通字符串不是合法 MCP 消息，会导致协议解析失败。
日志应该写 stderr，而不是 stdout。
```

### 练习 4：Streamable HTTP 和普通 REST API 最大区别是什么？

参考答案：

```text
Streamable HTTP 用 HTTP 作为传输通道，但 MCP 操作放在 JSON-RPC body 里，例如 method=tools/call。
普通 REST API 通常通过 URL 和 HTTP 方法表达资源操作，例如 GET /orders/A1001。
```

### 练习 5：什么时候优先选 stdio？

参考答案：

```text
当 MCP Server 跑在本机、只服务当前 Host、主要访问本地文件或本地项目、不需要多人共享、不想开端口、处于学习或调试阶段时，优先选 stdio。
```

### 练习 6：什么时候优先选 Streamable HTTP？

参考答案：

```text
当 MCP Server 要远程部署、多个 Host 或多个用户需要连接、需要标准 HTTP 认证、需要统一运维和监控、需要跨机器访问时，优先选 Streamable HTTP。
```

### 练习 7：SSE 和 notification 是不是同一个东西？

参考答案：

```text
不是。
SSE 是 transport 层的服务端推送通道。
notification 是 JSON-RPC data layer 的单向消息类型。
notification 可以通过 SSE 传输，但 SSE 不等于 notification。
```

## 自测题

### 自测 1：`tools/list` 属于 transport layer 吗？

参考答案：

```text
不属于。
tools/list 是 MCP data layer 的 JSON-RPC method。
stdio 或 Streamable HTTP 才属于 transport layer。
```

### 自测 2：同一条 `tools/call` 消息能不能通过不同 transport 发送？

参考答案：

```text
可以。
tools/call 的消息语义属于 data layer。
它可以通过 stdio 传给本地 Server，也可以通过 Streamable HTTP 传给远程 Server。
```

### 自测 3：为什么本地 MCP Server 常用 stdio？

参考答案：

```text
因为 stdio 不需要开端口、不需要网络部署、不需要先处理复杂 HTTP 认证，Host 可以直接启动本地子进程并通过 stdin/stdout 交换 JSON-RPC 消息，适合本地工具和学习阶段。
```

### 自测 4：远程 MCP Server 为什么更适合 Streamable HTTP？

参考答案：

```text
因为 Streamable HTTP 可以跨机器访问，适合独立部署，能服务多个 Client，并能结合 HTTP 认证、session、SSE、网关和监控体系。
```

### 自测 5：本地 HTTP MCP Server 为什么不建议随便绑定 `0.0.0.0`？

参考答案：

```text
因为 0.0.0.0 会监听所有网卡，可能让局域网或外部机器访问到本地 MCP Server。
本地服务应该优先绑定 127.0.0.1，减少暴露面。
```

### 自测 6：`MCP-Session-Id` 是业务用户 session 吗？

参考答案：

```text
不是。
MCP-Session-Id 是 Streamable HTTP transport/session 层面的一组 MCP 交互标识。
它不等于用户登录 session，也不等于 trace_id、order_id。
```

### 自测 7：为什么我们后续先学 stdio，而不是直接学 Streamable HTTP？

参考答案：

```text
因为 stdio 更简单，适合先理解 MCP 协议、生命周期、tools/list、tools/call 和 stdout/stderr 边界。
直接学 Streamable HTTP 会额外引入 HTTP 认证、SSE、session、Origin 校验和部署问题，容易分散注意力。
```

## 本节总结

这一节你要真正记住的是：

```text
MCP 的 JSON-RPC 消息属于 data layer。
stdio 和 Streamable HTTP 属于 transport layer。
stdio 适合本地 MCP Server。
Streamable HTTP 适合远程共享 MCP Server。
stdout 是 MCP 消息通道，stderr 是日志通道。
不要把 method、transport、业务工具名混在一起。
```

后续写 MCP Server 时，尤其要记住：

```text
不要用 stdout 打普通日志。
不要把 tools/list 当 transport。
不要把 Streamable HTTP 当普通 REST。
先用 stdio 把最小 MCP Server 学扎实。
```

下一节学习：

```text
阶段 8 第 7 节：MCP Tools 基础
```
