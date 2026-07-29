# 阶段 8 第 10 节：Python 最小 MCP Server

## 本节定位

前面第 1 到第 9 节，我们一直在学 MCP 的概念层：

```text
MCP 是什么
MCP 和 Tool Calling 的区别
MCP 架构
MCP 通信基础
MCP 生命周期
MCP transport
MCP Tools
MCP Resources
MCP Prompts
```

这一节开始进入代码层：

```text
用 Python SDK 写第一个真正能被 MCP Client 调用的 MCP Server。
```

本节的核心目标不是做复杂业务，而是把 MCP Server 的最小骨架跑通：

```text
Server 有名字。
Server 暴露 tools。
Server 暴露 resource。
Client 能发现 tool。
Client 能调用 tool。
Client 能读取 resource。
自动化测试不调用真实大模型，也不依赖 Docker、Java、Qdrant、Milvus。
```

一句话总结本节：

```text
MCP Server 是按 MCP 协议暴露能力的一端；Python SDK 帮我们把普通 Python 函数注册成 MCP tool/resource，并负责协议层的消息处理。
```

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
为什么 MCP Server 不等于 FastAPI Server。
为什么这节先写最小 server，而不是直接封装真实订单查询。
MCP Python SDK 里的 MCPServer 对象是什么。
@mcp.tool() 做了什么。
@mcp.resource(...) 做了什么。
函数参数类型提示为什么重要。
函数 docstring 为什么会影响工具描述。
tool 返回值为什么会变成 structured_content。
resource URI 为什么要有稳定命名。
stdio transport 下为什么不能随便 print 到 stdout。
为什么测试可以用 in-memory Client，不需要真实启动一个外部进程。
```

你还应该能看懂本节新增代码：

```text
projects/ai-service/app/mcp_servers/minimal_server.py
projects/ai-service/tests/test_minimal_mcp_server.py
projects/ai-service/pyproject.toml
```

## 本节不做什么

省 token 模式下，本节只做最小闭环，不提前扩大战线。

本节不做：

```text
不把 query_order 封装成 MCP Tool。
不调用 Java business service。
不接 MySQL / Redis。
不接 Qdrant / Milvus。
不启动 VMware。
不调用真实大模型。
不做 MCP Client 工程封装。
不做参数安全校验体系。
不做复杂错误映射。
不提交 GitHub。
不做敏感信息扫描。
```

这些后面会学：

```text
第 11 节：MCP Client 调试
第 12 节：工具参数校验
第 13 节：MCP 错误处理
第 14 节：MCP 安全边界
第 15 节：把订单查询封装成 MCP Tool
```

## 官方资料依据

本节依据 MCP 官方 Python SDK v2 写法：

| 资料 | 本节使用点 |
| --- | --- |
| [MCP Python SDK 官方仓库](https://github.com/modelcontextprotocol/python-sdk) | `MCPServer`、`@mcp.tool()`、`@mcp.resource(...)`、`Client(mcp)`、`uv add "mcp[cli]"` |
| [MCP Python SDK 文档](https://py.sdk.modelcontextprotocol.io/) | SDK v2 基础 API、in-memory client 调试方式、CLI dev/run 入口 |
| [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture) | Host、Client、Server 的职责边界 |
| [MCP Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) | stdio transport 下 stdout/stderr 的基本边界 |

说明：

```text
MCP Python SDK 当前使用 v2 风格。
本项目通过 uv 添加 mcp[cli] 依赖，安装结果是 mcp==2.0.0。
```

## 基础知识铺垫

### 1. 什么是 MCP Server

MCP Server 不是“大模型服务”。
MCP Server 也不是“业务服务本身”。

MCP Server 是：

```text
一个按 MCP 协议向 MCP Client 暴露能力的服务端。
```

它暴露的能力主要有三类：

```text
Tools：可执行动作。
Resources：可读取资料。
Prompts：可复用消息模板。
```

放到我们项目里：

```text
query_order 未来可以是 Tool。
create_ticket 未来可以是 Tool。
README、API 契约、学习笔记未来可以是 Resource。
customer_reply、ticket_summary 未来可以是 Prompt。
```

但本节先不接这些真实业务，只写最小例子：

```text
echo tool
add tool
learning://hello/{name} resource
```

为什么先写这种小例子？

因为你现在要先真正理解：

```text
一个普通 Python 函数如何被 MCP 暴露出去。
Client 如何发现它。
Client 如何调用它。
SDK 如何把函数参数和返回值转成协议里的结构。
```

如果第一节代码就直接接 Java、权限、trace_id、异常处理，你会被业务细节淹没，看不清 MCP Server 本身的骨架。

### 2. MCP Server 和 FastAPI Server 有什么区别

你已经学过 FastAPI，所以容易把 MCP Server 理解成另一个 HTTP API 服务。
这个理解只对了一小部分。

FastAPI 的核心是：

```text
浏览器、前端、curl、其他服务
通过 HTTP URL 调用接口。
```

典型 FastAPI 接口：

```text
GET /health
POST /chat
POST /tickets
```

MCP Server 的核心是：

```text
MCP Host 里的 MCP Client
通过 MCP 协议调用 Server 暴露的 tool/resource/prompt。
```

典型 MCP 方法：

```text
initialize
tools/list
tools/call
resources/read
prompts/get
```

对比：

| 维度 | FastAPI Server | MCP Server |
| --- | --- | --- |
| 面向谁 | HTTP 调用方，常见是前端或后端服务 | MCP Client，常见在 AI Host 内部 |
| 主要暴露方式 | URL + HTTP method | tool/resource/prompt |
| 常见调用 | `GET /orders/A1001` | `tools/call name=query_order` |
| 协议重点 | HTTP request/response | JSON-RPC + MCP 生命周期 |
| 适合表达 | 业务 API | AI 可发现、可调用的能力集合 |

一句话：

```text
FastAPI 主要暴露 HTTP API。
MCP Server 主要暴露 AI Host 可发现和可调用的工具生态能力。
```

后面我们可以用 HTTP transport 运行 MCP Server。
但即使用 HTTP transport，MCP Server 仍然不是普通 REST API。
它跑的是 MCP 协议方法，不是随便设计一堆 REST URL。

### 3. MCP Server 和 Java business service 的关系

我们项目现在已经有真实 Java business service。
它负责：

```text
订单查询
工单创建
MyBatis
MySQL
Redis
internal token
用户身份
租户
错误码
trace_id
```

未来 MCP Server 可以放在 Python AI 服务侧，把 Java 的业务能力包装成 MCP Tool：

```text
MCP Client
-> MCP Server tool: query_order
-> Python adapter
-> Java business service GET /internal/orders/{order_id}
-> Java 返回结果
-> Python 白名单映射和校验
-> MCP tool result
```

注意边界：

```text
MCP Server 不应该取代 Java business service。
MCP Server 只是把业务服务能力按 MCP 协议暴露给 AI Host。
```

Java 仍然是业务事实和数据写入的权威系统。
MCP Server 是协议适配层和安全边界层。

### 4. Python SDK 帮我们做了什么

如果完全手写 MCP Server，你需要自己处理：

```text
JSON-RPC 消息解析。
initialize 生命周期。
tools/list 返回格式。
tools/call 参数解析。
resources/read URI 匹配。
错误格式。
transport 读写。
```

Python SDK 帮我们封装了这些重复工作。

我们只需要写：

```python
from mcp.server import MCPServer

mcp = MCPServer("ai-service-learning-mcp")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b
```

SDK 会从函数上提取：

```text
函数名：add
参数名：a、b
参数类型：int、int
返回类型：int
docstring：Add two integers and return the result.
```

然后生成 MCP tool 描述。
Client 执行 `tools/list` 时能看到这个工具。
Client 执行 `tools/call` 时能调用这个函数。

这就是 SDK 的核心价值：

```text
你写 Python 函数，SDK 把它翻译成 MCP 能力。
```

### 5. MCPServer 对象是什么

本节代码里有一行：

```python
mcp = MCPServer("ai-service-learning-mcp")
```

可以把 `mcp` 理解成：

```text
当前这个 MCP Server 应用对象。
```

它负责保存：

```text
server 名字。
注册过的 tools。
注册过的 resources。
注册过的 prompts。
运行 transport 的能力。
处理 MCP Client 请求的逻辑。
```

你可以类比 FastAPI：

```python
app = FastAPI()
```

FastAPI 中我们写：

```python
@app.get("/health")
def health():
    ...
```

MCP SDK 中我们写：

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    ...
```

类比关系：

| FastAPI | MCP SDK |
| --- | --- |
| `app = FastAPI()` | `mcp = MCPServer(...)` |
| `@app.get("/health")` | `@mcp.tool()` |
| HTTP path | tool/resource/prompt |
| HTTP response | MCP result |

这个类比有助于入门，但不能完全等同。
FastAPI 是 Web API 框架，MCP SDK 是 MCP 协议框架。

### 6. 装饰器为什么能注册 tool

你已经学过 Python 函数。
这里补一个关键基础：装饰器。

装饰器写法：

```python
@mcp.tool()
def echo(message: str) -> str:
    return message
```

等价于一种“函数注册”过程。
可以粗略理解成：

```text
先定义 echo 函数。
再把 echo 函数交给 mcp.tool() 注册。
以后 MCP Client 调用 echo tool 时，SDK 会执行这个 Python 函数。
```

所以 `@mcp.tool()` 的作用不是让函数马上执行。
它的作用是：

```text
把这个函数登记到 MCP Server 的 tool registry 里。
```

这和 FastAPI 的 `@app.get(...)` 很像：

```text
@app.get("/health") 不是马上执行 health。
它是把 health 注册成 GET /health 的处理函数。
```

### 7. 类型提示为什么重要

本节代码：

```python
def add(a: int, b: int) -> int:
    return a + b
```

这里的 `a: int`、`b: int`、`-> int` 不只是给人看的。
MCP SDK 会使用这些信息生成 tool 的 schema。

Client 看到的工具大致会包含：

```json
{
  "name": "add",
  "description": "Add two integers and return the result.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "a": {
        "type": "integer"
      },
      "b": {
        "type": "integer"
      }
    },
    "required": ["a", "b"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "result": {
        "type": "integer"
      }
    },
    "required": ["result"]
  }
}
```

这说明：

```text
类型提示会影响 MCP Client 如何理解工具参数和返回值。
```

以后写真实业务工具时，类型提示不能随便写。
比如订单查询工具应该写清楚：

```python
def query_order(order_id: str, user_id: str, tenant_id: str) -> OrderToolResult:
    ...
```

而不是：

```python
def query_order(data):
    ...
```

后者对人和模型都不清晰，也不利于自动生成 schema。

### 8. docstring 为什么重要

本节代码：

```python
def echo(message: str) -> str:
    """Return the same message back to the caller."""
    return message
```

三引号里的内容叫 docstring。

对普通 Python 来说，它是函数说明。
对 MCP tool 来说，它还会成为工具描述的一部分。

这很重要，因为 AI Host 或开发者可能通过 `tools/list` 看到：

```text
echo: Return the same message back to the caller.
```

工具描述写得好，调用方才知道什么时候该用它。

差的描述：

```text
Do thing.
Tool.
Run.
```

好的描述：

```text
Return the same message back to the caller.
Add two integers and return the result.
Query a single order visible to the current user.
Create a customer support ticket after explicit user confirmation.
```

真实项目里，工具描述还要写清边界：

```text
这个工具是读操作还是写操作。
需要哪些权限。
是否会访问业务系统。
是否需要用户确认。
失败时可能返回什么错误。
```

本节先用简短 docstring，后面做真实业务工具时会继续加强。

### 9. Resource URI 是什么

本节有一个 resource：

```python
@mcp.resource("learning://hello/{name}")
def hello_resource(name: str) -> str:
    ...
```

这里的：

```text
learning://hello/{name}
```

是 Resource URI template。

可以理解为：

```text
这个 Server 暴露了一个可读取资源，URI 形状是 learning://hello/某个名字。
```

当 Client 读取：

```text
learning://hello/panpan
```

SDK 会把 `panpan` 提取成参数：

```python
name = "panpan"
```

然后执行：

```python
hello_resource("panpan")
```

Resource 和 Tool 的区别仍然要记住：

```text
Tool 是做动作。
Resource 是读资料。
```

本节的 `hello_resource` 只是教学例子。
后面项目里的 Resource 会更像：

```text
project-doc://java-ai-api-contract
learning-note://stage8-10-python-minimal-mcp-server
business-policy://refund-return-policy
```

### 10. stdio transport 下为什么不能随便 print

本节 server 可以通过：

```python
if __name__ == "__main__":
    mcp.run()
```

直接作为 MCP server 运行。

`mcp.run()` 默认使用 stdio transport。
stdio 的意思是：

```text
Client 通过标准输入 stdin 给 Server 发消息。
Server 通过标准输出 stdout 给 Client 回消息。
```

这里要记一个非常重要的工程规则：

```text
stdio transport 下，stdout 应该只输出合法 MCP 协议消息。
```

如果你在 server 里随便写：

```python
print("server started")
```

这行文字会跑到 stdout。
Client 可能会把它当成协议消息解析，然后报错。

所以：

```text
调试日志不要随便 print 到 stdout。
需要日志时应该走 stderr 或正式 logging 配置。
```

这就是为什么本节代码没有在 `minimal_server.py` 里加 `print`。

### 11. 为什么测试可以不用真实启动进程

本节测试用了：

```python
from mcp import Client
from app.mcp_servers.minimal_server import mcp

async with Client(mcp) as client:
    result = await client.call_tool("add", {"a": 7, "b": 5})
```

这叫 in-memory client。

意思是：

```text
Client 直接连接内存里的 MCPServer 对象。
```

优点：

```text
不用启动外部进程。
不用走网络端口。
不用依赖 Node 的 MCP Inspector。
不用依赖真实大模型。
测试速度快。
适合验证 server 注册和返回结构。
```

这不等于真实 transport 测试。
但对本节最小 server 来说已经足够。

后面学 MCP Client 调试时，再看：

```text
uv run mcp dev app/mcp_servers/minimal_server.py
uv run mcp run app/mcp_servers/minimal_server.py
```

## 本节主题系统讲解

### 1. 本节新增了哪些东西

本节在 `projects/ai-service` 中新增：

```text
app/mcp_servers/__init__.py
app/mcp_servers/minimal_server.py
tests/test_minimal_mcp_server.py
```

并修改：

```text
pyproject.toml
uv.lock
```

新增依赖：

```toml
"mcp[cli]>=2.0.0"
```

为什么加 `mcp[cli]`，而不是只加 `mcp`？

```text
mcp 是 Python SDK 主包。
mcp[cli] 额外安装命令行开发工具。
后面可以用 uv run mcp dev ... 打开 MCP Inspector 调试 server。
```

本节测试只需要 SDK 本身。
但为了后面第 11 节继续学习 Client 调试，把 CLI 一起装好更顺。

### 2. MCP server 文件放在哪里

本节放在：

```text
projects/ai-service/app/mcp_servers/minimal_server.py
```

为什么不是放到 `app/routers`？

```text
routers 是 FastAPI HTTP 路由。
mcp_servers 是 MCP Server 模块。
```

这两个概念要分开：

```text
HTTP API 对外通过 FastAPI router 暴露。
MCP 能力通过 MCPServer 暴露。
```

如果把 MCP Server 放进 `routers`，学习上容易误解：

```text
误以为 MCP tool 是一个普通 HTTP endpoint。
```

所以本节新建 `app/mcp_servers`，先把边界立清楚。

### 3. `mcp = MCPServer(...)`

代码：

```python
from mcp.server import MCPServer


mcp = MCPServer("ai-service-learning-mcp")
```

逐行解释：

```text
from mcp.server import MCPServer
```

表示从 MCP SDK 里导入 server 类。

```text
mcp = MCPServer("ai-service-learning-mcp")
```

表示创建一个 MCP Server 实例。
名字是：

```text
ai-service-learning-mcp
```

这个名字的作用：

```text
让 Client 或调试工具知道自己连接的是哪个 MCP Server。
在测试输出和调试信息中更容易定位。
```

真实项目里命名要稳定。
比如：

```text
ai-service-mcp
customer-support-mcp
order-tools-mcp
```

不要叫：

```text
test
demo
server1
```

因为名字会影响排查和协作理解。

### 4. `echo` tool

代码：

```python
@mcp.tool()
def echo(message: str) -> str:
    """Return the same message back to the caller."""
    return message
```

它暴露了一个 tool：

```text
name: echo
参数：message
参数类型：string
返回：string
```

它做的事很简单：

```text
传入什么 message，就返回什么 message。
```

为什么保留这个工具？

因为 echo 是最适合做连通性验证的工具。

它能回答：

```text
Client 是否能调用到 Server。
参数是否能传进去。
返回值是否能传回来。
编码是否正常。
```

它不涉及业务逻辑，所以排错时很干净。

### 5. `add` tool

代码：

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b
```

它暴露了一个 tool：

```text
name: add
参数：a、b
参数类型：integer、integer
返回：integer
```

为什么除了 echo 又加 add？

因为 `add` 可以让我们看到：

```text
多个参数如何传递。
类型提示如何进入 schema。
返回值如何变成 structured_content。
```

测试里调用：

```python
result = await client.call_tool("add", {"a": 7, "b": 5})
```

返回的关键结构是：

```python
result.structured_content == {"result": 12}
```

这里要理解：

```text
Python 函数返回 12。
SDK 把它包装成 MCP tool result。
结构化结果里用 result 字段承载返回值。
```

所以以后真实 tool 返回 Pydantic 模型或 dict 时，也会进入结构化返回。
这对 Agent 使用工具结果很重要。

### 6. `hello_resource`

代码：

```python
@mcp.resource("learning://hello/{name}")
def hello_resource(name: str) -> str:
    """Return a greeting resource for a learner."""
    return f"Hello, {name}. This resource comes from ai-service minimal MCP server."
```

它暴露了一个 resource：

```text
URI template: learning://hello/{name}
参数：name
返回：一段 text/plain 文本
```

测试里读取：

```python
result = await client.read_resource("learning://hello/panpan")
```

返回内容：

```text
Hello, panpan. This resource comes from ai-service minimal MCP server.
```

为什么本节也加 resource？

因为第 8 节刚学过 Resources。
现在用一段最小代码把概念落地：

```text
@mcp.resource(...) 可以把一个 URI 映射到 Python 函数。
Client read_resource 时，SDK 会根据 URI 找到对应函数并返回内容。
```

但要注意：

```text
这个 resource 是教学用，不是业务知识库。
后面才会把项目文档、API 契约、业务规则暴露成真实 MCP Resource。
```

### 7. `if __name__ == "__main__": mcp.run()`

代码：

```python
if __name__ == "__main__":
    mcp.run()
```

这段是 Python 常见入口写法。

含义：

```text
当这个文件被直接运行时，启动 MCP Server。
当这个文件被测试或其他模块 import 时，不自动启动 Server。
```

为什么需要这个判断？

测试时我们会：

```python
from app.mcp_servers.minimal_server import mcp
```

这时只希望拿到 `mcp` 对象。
不希望 import 的瞬间就启动一个阻塞的 server。

直接运行时：

```powershell
uv run python app\mcp_servers\minimal_server.py
```

会进入：

```python
mcp.run()
```

默认使用 stdio transport。

注意：

```text
直接运行后它可能看起来没有输出，这是正常的。
因为它在等待 MCP Client 通过 stdin/stdout 和它通信。
普通人不是通过肉眼看输出使用 stdio MCP Server。
```

后面用 MCP Inspector 或 MCP Client 调试时会更直观。

### 8. 测试文件验证了什么

测试文件：

```text
projects/ai-service/tests/test_minimal_mcp_server.py
```

核心验证三件事：

```text
Client 能 list_tools。
Client 能 call_tool。
Client 能 read_resource。
```

第一条测试：

```python
tools = await client.list_tools()
tool_names = {tool.name for tool in tools.tools}

assert "echo" in tool_names
assert "add" in tool_names
```

学习重点：

```text
@mcp.tool() 注册成功后，Client 通过 list_tools 能发现工具。
```

第二条测试：

```python
result = await client.call_tool("add", {"a": 7, "b": 5})

assert result.is_error is False
assert result.structured_content == {"result": 12}
```

学习重点：

```text
Client 通过 tool name 和参数调用 Python 函数。
函数返回值被 SDK 包装成 MCP tool result。
structured_content 是模型/Host 更容易消费的结构化结果。
```

第三条测试：

```python
result = await client.read_resource("learning://hello/panpan")

assert result.contents[0].text == (
    "Hello, panpan. This resource comes from ai-service minimal MCP server."
)
```

学习重点：

```text
Client 可以根据 resource URI 读取 Server 暴露的资源内容。
```

测试不用真实大模型。
因为本节验证的是 MCP Server 协议能力，不是模型推理能力。

### 9. 为什么这里用了 `asyncio.run`

MCP Client 调用是异步的：

```python
await client.list_tools()
await client.call_tool(...)
await client.read_resource(...)
```

而 pytest 默认测试函数是同步函数。
所以测试里写：

```python
def test_minimal_mcp_server_can_call_add_tool() -> None:
    async def run() -> None:
        ...

    asyncio.run(run())
```

含义：

```text
外层仍然是普通 pytest 测试。
内层用 asyncio.run 执行异步 MCP Client 调用。
```

这样做的优点：

```text
不额外引入 pytest-asyncio。
测试结构简单。
能清楚看到 MCP Client 是异步调用。
```

后面如果异步测试越来越多，可以再统一引入异步测试插件或项目约定。

## 代码变化讲解

### 1. `pyproject.toml`

新增依赖：

```toml
"mcp[cli]>=2.0.0"
```

学习意义：

```text
项目现在具备编写和调试 MCP Server 的 Python SDK 能力。
```

`uv add "mcp[cli]"` 做了两件事：

```text
更新 pyproject.toml。
更新 uv.lock。
```

`pyproject.toml` 是人读的项目依赖声明。
`uv.lock` 是锁定后的精确依赖版本。

### 2. `app/mcp_servers/__init__.py`

内容：

```python
"""MCP server examples used by the learning project."""
```

作用：

```text
把 mcp_servers 目录作为 Python package。
为后续多个 MCP Server 模块预留清晰位置。
```

### 3. `app/mcp_servers/minimal_server.py`

这个文件是本节核心。

它不是 FastAPI router。
它是 MCP Server 模块。

完整结构：

```text
导入 MCPServer
创建 mcp 对象
注册 echo tool
注册 add tool
注册 hello resource
直接运行时启动 server
```

这就是最小但完整的 MCP Server 骨架。

### 4. `tests/test_minimal_mcp_server.py`

这个测试不测业务。
它只测协议能力是否暴露成功。

验证目标：

```text
list_tools 能发现工具。
call_tool 能得到结构化结果。
read_resource 能读取文本资源。
```

这类测试以后会扩展成：

```text
query_order tool 能正确调用 Java adapter。
create_ticket tool 能要求确认和幂等键。
错误时能返回安全错误。
敏感字段不会暴露给模型。
```

## 手动运行和验证

本节已经新增了单独手动验证说明：

```text
notes/stage8-10-python-minimal-mcp-server-manual-tasks.md
```

最小验证命令：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests\test_minimal_mcp_server.py
```

可选 MCP Inspector：

```powershell
uv run mcp dev app\mcp_servers\minimal_server.py
```

注意：

```text
MCP Inspector 通常需要本机有 Node/npm/npx。
如果 npx 不可用，先不用纠结，本节以 pytest 通过为准。
```

## 常见误区

### 误区 1：MCP Server 就是 FastAPI Server

不准确。

FastAPI 暴露 HTTP API。
MCP Server 暴露 MCP 能力。

后面即使 MCP Server 通过 HTTP transport 运行，也仍然是在 HTTP 上承载 MCP 协议，不等于普通 REST API。

### 误区 2：`@mcp.tool()` 会马上执行函数

不对。

它是注册函数。
只有 Client 调用 `tools/call` 时，函数才会执行。

### 误区 3：函数名随便取也行

不建议。

函数名通常会成为 tool name。
tool name 是 Client 调用时的重要标识。

真实项目中应使用稳定、清晰、可理解的名字：

```text
query_order
create_ticket
get_refund_policy
```

### 误区 4：docstring 不重要

不对。

docstring 会影响工具描述。
工具描述会影响 Host、开发者甚至模型是否能正确理解工具用途。

### 误区 5：MCP tool 可以随便暴露内部函数

不可以。

真实 MCP tool 是对 AI Host 暴露的能力边界。
暴露前要考虑：

```text
权限。
参数校验。
敏感字段。
幂等。
审计。
错误兜底。
是否需要用户确认。
```

### 误区 6：stdio server 可以随便 print 调试

不可以。

stdio transport 下，stdout 是协议通道。
随便 print 可能破坏协议消息。
调试信息应该走 stderr 或 logging。

## 项目映射

本节最小 server 和未来真实项目的关系：

| 本节教学例子 | 未来项目真实形态 |
| --- | --- |
| `echo` | 健康检查或连通性调试 tool |
| `add` | 参数 schema 和 structured result 的学习样例 |
| `learning://hello/{name}` | 项目文档、业务规则、学习笔记 Resource |
| `Client(mcp)` 测试 | MCP Server 的单元测试和契约测试基础 |
| `mcp.run()` | 通过 stdio 或 HTTP transport 启动 MCP Server |

后面第 15 节会把已有链路接进来：

```text
MCP tool: query_order
-> Python adapter
-> Java business service
-> 字段白名单映射
-> Pydantic 校验
-> MCP structured_content
```

那时你会看到：

```text
MCP 不是取代已有系统，而是把已有系统能力按统一协议暴露给 AI Host。
```

## 本节练习

### 练习 1：用一句话解释 MCP Server 是什么

参考答案：

```text
MCP Server 是按 MCP 协议向 MCP Client 暴露 tools、resources、prompts 等能力的服务端，它让 AI Host 能用统一方式发现和调用外部能力。
```

### 练习 2：为什么本节没有把 MCP Server 放到 `app/routers`？

参考答案：

```text
因为 `app/routers` 是 FastAPI HTTP 路由目录，而 MCP Server 不是普通 HTTP endpoint。本节新建 `app/mcp_servers` 是为了明确区分 HTTP API 和 MCP 协议能力。
```

### 练习 3：`@mcp.tool()` 的作用是什么？

参考答案：

```text
它把一个普通 Python 函数注册成 MCP tool。注册后 Client 可以通过 tools/list 发现它，通过 tools/call 调用它。装饰器本身不会马上执行函数。
```

### 练习 4：为什么函数参数要写类型提示？

参考答案：

```text
类型提示会帮助 MCP SDK 推导工具的输入 schema 和输出 schema，让 Client、Host 和模型更清楚工具需要什么参数、会返回什么结构。
```

### 练习 5：为什么 stdio transport 下不能随便 `print`？

参考答案：

```text
因为 stdio transport 用 stdout 传输 MCP 协议消息。随便 print 会把普通文本写进 stdout，Client 可能把它当作协议消息解析，从而导致通信错误。
```

### 练习 6：本节 `add` tool 返回 `12`，为什么测试断言的是 `{"result": 12}`？

参考答案：

```text
Python 函数本身返回整数 12，MCP SDK 会把返回值包装成 tool result。对于这种简单返回值，SDK 在 structured_content 中使用 result 字段承载结构化结果，所以断言是 {"result": 12}。
```

### 练习 7：Resource URI `learning://hello/panpan` 是怎么和 Python 参数对应上的？

参考答案：

```text
Server 注册的是 URI template：learning://hello/{name}。Client 读取 learning://hello/panpan 时，SDK 会把 panpan 匹配成 name 参数，再调用 hello_resource(name="panpan")。
```

## 自测题

### 自测 1：MCP Server 是否等于大模型？

参考答案：

```text
不等于。MCP Server 是暴露工具、资源和 prompt 的协议服务端；大模型是生成内容的模型。MCP Server 可以被 AI Host 调用，但它本身不是模型。
```

### 自测 2：MCP Server 是否必须用 HTTP 运行？

参考答案：

```text
不必须。MCP 支持不同 transport，本节默认使用 stdio。后面也可以学习 Streamable HTTP 等方式。
```

### 自测 3：`mcp = MCPServer("ai-service-learning-mcp")` 里的字符串有什么意义？

参考答案：

```text
它是 server name，用来标识当前 MCP Server。Client 或调试工具可以通过这个名字知道连接的是哪个 server，排查问题时也更清楚。
```

### 自测 4：`echo` 和 `add` 为什么是 Tool，而不是 Resource？

参考答案：

```text
它们需要被调用并执行函数逻辑，属于动作能力，所以是 Tool。Resource 更适合表示可读取资料，比如文档、配置、规则、学习笔记。
```

### 自测 5：`hello_resource` 为什么是 Resource？

参考答案：

```text
它通过 URI 读取一段文本内容，没有执行业务写操作，也不是让模型调用一个动作，所以更适合作为 Resource。
```

### 自测 6：测试为什么使用 `Client(mcp)`，而不是启动一个进程？

参考答案：

```text
因为本节只验证 server 的 tool/resource 注册和返回结构，in-memory Client 更简单、稳定、快速，不需要进程、端口、Node、Docker 或真实模型。
```

### 自测 7：真实订单查询什么时候做成 MCP Tool？

参考答案：

```text
后面第 15 节会做。本节先掌握最小 MCP Server 骨架，第 12 到第 14 节还要先补参数校验、错误处理和安全边界，再接入真实业务工具更稳。
```

### 自测 8：以后把 `create_ticket` 做成 MCP Tool 时，最重要的安全点是什么？

参考答案：

```text
它是写操作，不能让模型直接执行。需要用户确认、幂等键、真实用户身份、租户边界、权限校验、错误兜底和审计日志。
```

## 本节总结

本节真正要记住的是：

```text
MCP Server 是暴露 MCP 能力的服务端。
Python SDK 用 MCPServer 对象管理 server。
@mcp.tool() 把 Python 函数注册成 MCP Tool。
@mcp.resource(...) 把 URI 映射到可读取资源。
类型提示和 docstring 会影响工具 schema 和描述。
stdio transport 下 stdout 是协议通道，不能随便 print。
in-memory Client 可以快速测试最小 server。
```

放到项目里：

```text
本节完成了 ai-service 中第一个最小 MCP Server。
它还不是业务 MCP Server，但已经具备被 MCP Client 发现、调用工具、读取资源的最小闭环。
后面会在这个基础上逐步加入参数校验、错误处理、安全边界，再封装真实 Java business service 能力。
```

下一节学习：

```text
阶段 8 第 11 节：MCP Client 调试
```
