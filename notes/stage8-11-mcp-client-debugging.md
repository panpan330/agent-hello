# 阶段 8 第 11 节：MCP Client 调试

## 本节定位

上一节我们写了第一个最小 MCP Server：

```text
projects/ai-service/app/mcp_servers/minimal_server.py
```

它暴露了：

```text
echo tool
add tool
learning://hello/{name} resource
```

这一节学习 MCP Client 调试。

也就是站在调用方角度看：

```text
Client 怎样发现 Server 暴露了哪些 tools。
Client 怎样调用某个 tool。
Client 怎样读取某个 resource。
Client 怎样看返回值里哪些字段最重要。
```

一句话总结本节：

```text
MCP Client 调试不是为了写复杂业务，而是为了确认 Server 暴露的能力、schema、返回结构和错误标记是否符合预期。
```

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
MCP Client 是什么。
为什么一个 Host 里通常会有多个 Client。
MCP Client 和普通 HTTP client 有什么区别。
为什么调试 Client 时要先 list，再 call/read。
list_tools 返回的 tools 列表里应该重点看什么。
call_tool 返回的 content、structured_content、is_error 分别是什么意思。
read_resource 返回的 contents 应该怎么看。
为什么调试脚本要输出 JSON，而不是随便 print 几行文字。
in-memory Client 和 stdio/HTTP transport Client 的区别。
MCP Inspector 适合解决什么问题。
为什么自动化测试不真实调用大模型。
```

本节新增代码：

```text
projects/ai-service/app/mcp_clients/__init__.py
projects/ai-service/app/mcp_clients/minimal_client.py
projects/ai-service/scripts/mcp_client_smoke.py
projects/ai-service/tests/test_mcp_client_smoke.py
```

## 本节不做什么

省 token 模式下，本节只做 MCP Client 调试闭环，不提前扩展。

本节不做：

```text
不启动 VMware。
不启动 Docker。
不连接 Qdrant / Milvus。
不连接 MySQL / Redis。
不启动 Java business service。
不调用真实大模型。
不封装 query_order。
不做 MCP 参数校验体系。
不做 MCP 错误处理体系。
不提交 GitHub。
不做敏感信息扫描。
```

本节只做：

```text
用 MCP Client 连接上一节的最小 MCP Server。
列出 tools。
调用 add tool。
调用 echo tool。
读取 learning://hello/panpan resource。
把结果整理成 JSON-friendly 调试快照。
写测试固定这个调试快照。
```

## 官方资料依据

本节延续 MCP Python SDK v2 的用法。

| 资料 | 本节使用点 |
| --- | --- |
| [MCP Python SDK 官方仓库](https://github.com/modelcontextprotocol/python-sdk) | `Client(mcp)`、`list_tools()`、`call_tool()`、`read_resource()` |
| [MCP Python SDK 文档](https://py.sdk.modelcontextprotocol.io/) | in-memory Client 调试方式、CLI `mcp dev` / `mcp run` 的定位 |
| [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture) | Host、Client、Server 的职责关系 |
| [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | tools/list、tools/call、structuredContent、isError |
| [MCP Resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources) | resources/read、contents、text resource |

本项目当前本地 SDK 版本：

```text
MCP version 2.0.0
```

## 基础知识铺垫

### 1. MCP Client 是什么

MCP 架构里有三个重要角色：

```text
Host
Client
Server
```

简单说：

```text
Host 是 AI 应用本体。
Client 是 Host 里负责连接某个 MCP Server 的连接器。
Server 是暴露 tools/resources/prompts 的服务端。
```

如果用我们项目类比：

```text
ai-service 未来可以作为 Host 的一部分。
某个 MCP Client 负责连接订单工具 MCP Server。
另一个 MCP Client 负责连接文档资源 MCP Server。
MCP Server 负责暴露 query_order、create_ticket、project docs 等能力。
```

一个 Host 可以连接多个 Server。
所以通常是：

```text
一个 Host
多个 Client
多个 Server
```

示意：

```text
Host
  |
  |-- Client A -> Order MCP Server
  |-- Client B -> Docs MCP Server
  |-- Client C -> Git MCP Server
```

要记住：

```text
Client 不是最终用户界面。
Client 是 Host 内部用来和某个 MCP Server 通信的协议对象。
```

### 2. MCP Client 和 HTTP client 的区别

你之前学过 `httpx`，也写过 Python 调 Java API。

HTTP client 的典型调用是：

```python
client.get("/internal/orders/A1001")
client.post("/internal/tickets", json=payload)
```

它关心：

```text
URL
HTTP method
headers
query params
request body
status code
response body
```

MCP Client 的典型调用是：

```python
await client.list_tools()
await client.call_tool("add", {"a": 7, "b": 5})
await client.read_resource("learning://hello/panpan")
```

它关心：

```text
MCP method
tool name
tool arguments
resource URI
content
structured_content
is_error
protocol lifecycle
```

对比：

| 维度 | HTTP client | MCP Client |
| --- | --- | --- |
| 调用目标 | HTTP API | MCP Server 能力 |
| 入口 | URL + method | tool/resource/prompt 方法 |
| 典型调用 | `GET /orders/A1001` | `call_tool("query_order", {...})` |
| 结果重点 | status code + JSON body | content + structured_content + is_error |
| 面向对象 | 普通服务调用 | AI Host 连接工具生态 |

一句话：

```text
HTTP client 调的是接口地址。
MCP Client 调的是 Server 暴露出来的能力。
```

### 3. 为什么调试顺序是先 list 再 call

真实调试时不要一上来就调用工具。
正确顺序是：

```text
先 list。
再看 schema。
再 call。
最后看返回结构。
```

原因很简单：

```text
如果 list_tools 都看不到工具，call_tool 一定不可靠。
如果 list_tools 里的参数 schema 不对，模型或 Host 传参就可能错。
如果 description 写得不清楚，模型可能误用工具。
如果 output_schema 不清楚，后续 Agent 节点就不好消费工具结果。
```

所以调试 Client 时第一步不是：

```text
工具能不能跑业务？
```

而是：

```text
工具有没有正确暴露？
工具名字是否稳定？
工具描述是否清楚？
工具输入输出 schema 是否符合预期？
```

这就是本节脚本先输出 `tools` 的原因。

### 4. list_tools 重点看什么

本节脚本输出里，每个 tool 有四个核心字段：

```text
name
description
input_schema
output_schema
```

#### name

`name` 是工具调用时的稳定标识。

例子：

```text
echo
add
```

后面真实项目里会有：

```text
query_order
create_ticket
```

命名要求：

```text
短。
稳定。
表达动作。
不要有歧义。
不要频繁改。
```

因为 Host 或模型可能会把这个名字用于工具选择。
如果名字变来变去，调用链和测试都会不稳定。

#### description

`description` 用来解释工具用途。

例子：

```text
Add two integers and return the result.
```

真实工具描述要更重视边界。
比如：

```text
Query one order visible to the current user. This is a read-only tool and does not modify order data.
```

为什么 description 重要？

```text
它帮助开发者理解工具。
它也可能帮助 Host 或模型判断什么时候该用这个工具。
```

#### input_schema

`input_schema` 描述工具需要什么参数。

本节 `add` 的输入 schema 大致是：

```json
{
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
}
```

这说明：

```text
add 需要 a 和 b。
a、b 都是 integer。
两个字段都必填。
```

真实项目中，input_schema 是工具安全的第一道边界。
但只靠 schema 不够，后面还要学 Pydantic 校验和业务校验。

#### output_schema

`output_schema` 描述工具结构化返回。

本节 `add` 返回：

```json
{
  "result": 12
}
```

所以 output_schema 里会看到：

```text
result: integer
```

真实工具里，输出结构应该尽量稳定。
比如订单查询结果应该固定字段：

```text
order_id
status
paid_at
shipped_at
delivery_status
safe_summary
```

不要每次返回不同结构。
否则 Agent 后续节点很难处理。

### 5. call_tool 返回值怎么看

本节脚本里调用：

```python
add_result = await client.call_tool("add", {"a": 7, "b": 5})
```

返回结果里重点看三个字段：

```text
is_error
structured_content
content
```

#### is_error

`is_error` 表示工具执行是否返回工具级错误。

本节成功调用时：

```json
"is_error": false
```

后面真实工具可能会出现：

```text
订单不存在。
用户无权查看。
Java 服务超时。
Java 服务返回契约不合法。
```

这些要区分：

```text
协议错误
工具执行错误
业务错误
系统错误
```

第 13 节会专门学错误处理。

#### structured_content

`structured_content` 是结构化结果。

本节 `add`：

```json
"structured_content": {
  "result": 12
}
```

本节 `echo`：

```json
"structured_content": {
  "result": "hello mcp"
}
```

对 Agent 来说，结构化结果非常重要。
因为后续流程不应该依赖自然语言猜含义。

例如真实订单工具不应该只返回：

```text
订单 A1001 已发货。
```

而应该返回结构化字段：

```json
{
  "order_id": "A1001",
  "status": "shipped",
  "delivery_status": "in_transit",
  "can_create_ticket": true
}
```

这样后续节点才能稳定判断。

#### content

`content` 是给人或模型看的内容块。

本节 `add` 的 `content` 里有：

```text
12
```

本节 `echo` 的 `content` 里有：

```text
hello mcp
```

可以这样理解：

```text
structured_content 更适合程序消费。
content 更适合文本展示或模型上下文。
```

真实项目里这两者可以同时存在。
但工程上通常更信任结构化结果。

### 6. read_resource 返回值怎么看

本节调用：

```python
resource_result = await client.read_resource("learning://hello/panpan")
```

返回里重点看：

```text
contents
```

本节脚本把它整理成：

```json
"resource_reads": {
  "learning://hello/panpan": [
    "Hello, panpan. This resource comes from ai-service minimal MCP server."
  ]
}
```

真实 Resource 可能是：

```text
Markdown 文档。
API 契约。
业务规则。
项目说明。
```

读取 Resource 时重点看：

```text
URI 是否正确。
内容是否符合预期。
mime type 是否合理。
是否暴露了不该暴露的信息。
内容是否可能包含 prompt injection。
```

后面第 17 节会把项目文档接成 MCP Resource。

### 7. 为什么脚本输出 JSON

本节手动脚本：

```text
projects/ai-service/scripts/mcp_client_smoke.py
```

运行后输出 JSON。

为什么不直接 print：

```text
工具调用成功。
add = 12。
hello = ...
```

因为 JSON 更适合工程调试：

```text
结构稳定。
字段清楚。
可以被复制到笔记里分析。
可以被日志系统收集。
可以被测试或脚本二次处理。
可以清楚区分 tools、tool_calls、resource_reads。
```

以后真实 MCP 调试输出也应该尽量结构化。
少用不稳定的自然语言打印。

### 8. in-memory Client 是什么

本节代码：

```python
async with Client(mcp) as client:
    ...
```

这里 `mcp` 是上一节创建的 `MCPServer` 对象。

这表示：

```text
Client 直接连接内存里的 Server 对象。
```

它没有：

```text
启动外部进程。
打开 HTTP 端口。
通过 stdin/stdout 传输。
通过网络传输。
```

优点：

```text
快。
稳定。
适合单元测试。
不用额外工具。
不依赖 Node/npm/npx。
```

缺点：

```text
不能验证真实 transport。
不能发现 stdio stdout 污染问题。
不能验证 HTTP header/session 等 transport 细节。
```

所以本节用 in-memory Client 是合理的。
后面如果要验证真实运行方式，再用 MCP Inspector 或 transport 级测试。

### 9. MCP Inspector 是什么

MCP Inspector 可以理解成：

```text
一个用于开发和调试 MCP Server 的可视化工具。
```

通过命令：

```powershell
uv run mcp dev app\mcp_servers\minimal_server.py
```

可以打开调试界面，查看：

```text
Server 信息。
Tools 列表。
Tool schema。
Tool 调用结果。
Resources。
Prompts。
错误信息。
```

它适合：

```text
人工观察 MCP Server 暴露了什么。
手动尝试不同参数。
排查 schema 和描述是否清楚。
演示 MCP Server 能力。
```

但它不是自动化测试的替代品。

自动化测试仍然要保留：

```text
pytest
fake client
in-memory client
契约测试
```

### 10. 为什么本节不调用真实大模型

MCP Client 调试和 LLM 调用是两件事。

本节要验证的是：

```text
Client 是否能连接 Server。
Client 是否能发现工具。
Client 是否能调用工具。
Client 是否能读取资源。
返回结构是否稳定。
```

这些不需要大模型。

如果在本节加入真实 LLM，会引入很多额外变量：

```text
API Key。
网络。
模型延迟。
模型输出不稳定。
费用。
供应商兼容差异。
```

这会模糊本节重点。

所以本节坚持：

```text
调试 MCP Client，不调试 LLM。
```

## 本节主题系统讲解

### 1. 本节新增结构

新增模块：

```text
projects/ai-service/app/mcp_clients/
```

作用：

```text
存放 MCP Client 侧的调试和调用逻辑。
```

为什么不是只写一个脚本？

因为纯脚本有一个问题：

```text
脚本里面的核心逻辑不容易被测试复用。
```

所以本节拆成：

```text
app/mcp_clients/minimal_client.py：核心 Client 调试逻辑。
scripts/mcp_client_smoke.py：手动运行入口。
tests/test_mcp_client_smoke.py：自动化验证。
```

结构关系：

```text
tests/test_mcp_client_smoke.py
        |
        v
app/mcp_clients/minimal_client.py
        |
        v
app/mcp_servers/minimal_server.py

scripts/mcp_client_smoke.py
        |
        v
app/mcp_clients/minimal_client.py
```

这就是工程上常见的拆法：

```text
核心逻辑放 app。
手动入口放 scripts。
测试验证 app 里的核心逻辑。
```

### 2. `minimal_client.py` 做了什么

核心函数：

```python
async def collect_minimal_mcp_debug_snapshot() -> dict[str, Any]:
    """Call the minimal MCP server and return a JSON-friendly debug snapshot."""
```

它的职责是：

```text
连接 minimal MCP Server。
列出工具。
调用 add。
调用 echo。
读取 learning://hello/panpan。
把结果整理成普通 dict。
```

为什么叫 debug snapshot？

因为它是一个调试快照：

```text
在某一刻，把 Server 暴露能力和调用结果采样出来。
```

这和日志里的“快照”思想类似：

```text
不要只打印一句成功。
要保留足够结构，让以后能分析哪里对、哪里不对。
```

### 3. 为什么返回 JSON-friendly dict

MCP SDK 返回的是对象。
比如：

```text
CallToolResult
ReadResourceResult
ListToolsResult
```

这些对象适合程序内部使用。
但手动调试时，我们更想看到稳定 JSON。

所以本节把 SDK 对象整理成：

```python
return {
    "server": "ai-service-learning-mcp",
    "tools": [...],
    "tool_calls": {...},
    "resource_reads": {...},
}
```

这种结构更适合：

```text
终端查看。
复制到笔记。
测试断言。
后续改成日志。
后续改成诊断接口。
```

### 4. `_extract_text_items`

代码：

```python
def _extract_text_items(items: list[Any]) -> list[str]:
    return [item.text for item in items if getattr(item, "text", None) is not None]
```

它的作用：

```text
从 MCP content items 里提取 text 内容。
```

为什么不直接写：

```python
[item.text for item in items]
```

因为 MCP content 未来不一定只有 text。
还可能有：

```text
image
audio
resource
```

本节只关心文本内容。
所以用 `getattr(item, "text", None)` 做轻量过滤。

这不是完整内容解析器。
它只是本节调试脚本的最小提取函数。

### 5. `async with Client(mcp) as client`

代码：

```python
async with Client(mcp) as client:
    ...
```

含义：

```text
创建 MCP Client。
连接内存里的 mcp server。
进入可调用状态。
代码块结束后释放连接资源。
```

为什么用 `async with`？

因为 MCP Client 连接通常涉及生命周期管理。

类比你以前学过的文件操作：

```python
with open("file.txt") as f:
    ...
```

`with` 保证用完关闭文件。
`async with` 是异步版本，用来管理异步资源。

### 6. `await client.list_tools()`

代码：

```python
tools_response = await client.list_tools()
```

它对应 MCP 协议里的：

```text
tools/list
```

返回结果包含：

```text
tools
meta
next_cursor
```

本节重点取：

```python
tools_response.tools
```

然后整理每个 tool：

```python
{
    "name": tool.name,
    "description": tool.description,
    "input_schema": tool.input_schema,
    "output_schema": tool.output_schema,
}
```

这一步是在检查：

```text
Server 暴露的工具是否符合预期。
```

### 7. `await client.call_tool(...)`

代码：

```python
add_result = await client.call_tool("add", {"a": 7, "b": 5})
echo_result = await client.call_tool("echo", {"message": "hello mcp"})
```

它对应 MCP 协议里的：

```text
tools/call
```

第一参数是 tool name：

```text
add
echo
```

第二参数是 arguments：

```json
{"a": 7, "b": 5}
{"message": "hello mcp"}
```

调试时重点看：

```text
is_error 是否 false。
structured_content 是否符合预期。
text_content 是否能展示给人看。
```

本节输出：

```json
"add": {
  "is_error": false,
  "structured_content": {
    "result": 12
  },
  "text_content": [
    "12"
  ]
}
```

这里你要能说清楚：

```text
add 的 Python 返回值是整数 12。
SDK 包装后 structured_content 变成 {"result": 12}。
content 里还有文本形式 "12"。
```

### 8. `await client.read_resource(...)`

代码：

```python
resource_result = await client.read_resource("learning://hello/panpan")
```

它对应 MCP 协议里的：

```text
resources/read
```

调试时重点看：

```text
URI 是否匹配。
contents 是否有文本。
文本是否符合预期。
```

本节输出：

```json
"resource_reads": {
  "learning://hello/panpan": [
    "Hello, panpan. This resource comes from ai-service minimal MCP server."
  ]
}
```

这说明：

```text
Client 通过 URI 成功读取到了 Server 的 resource。
```

### 9. `mcp_client_smoke.py` 做了什么

脚本：

```text
projects/ai-service/scripts/mcp_client_smoke.py
```

核心：

```python
snapshot = asyncio.run(collect_minimal_mcp_debug_snapshot())
print(json.dumps(snapshot, ensure_ascii=False, indent=2))
```

含义：

```text
运行异步 client 调试函数。
把结果以 UTF-8 JSON 打印出来。
```

为什么 `ensure_ascii=False`？

因为后面项目里可能会输出中文。
如果设置成默认 True，中文会变成：

```text
\u4e2d\u6587
```

学习和调试时不方便看。

为什么加 `indent=2`？

为了让 JSON 更容易阅读。

### 10. 测试验证了什么

测试：

```text
projects/ai-service/tests/test_mcp_client_smoke.py
```

验证：

```text
tools 里包含 add 和 echo。
add 调用成功。
add structured_content 是 {"result": 12}。
echo structured_content 是 {"result": "hello mcp"}。
resource_reads 能读到 learning://hello/panpan。
```

测试不是为了证明加法正确。
测试重点是：

```text
Client 调试链路没有断。
返回结构没有变。
最小 server 的 tool/resource 能被 client 消费。
```

## 代码变化讲解

### 1. `app/mcp_clients/__init__.py`

内容：

```python
"""MCP client helpers used by the learning project."""
```

作用：

```text
把 mcp_clients 做成 Python package。
让后续 MCP Client 相关模块有固定目录。
```

这和第 10 节的 `app/mcp_servers` 对应：

```text
app/mcp_servers：Server 侧。
app/mcp_clients：Client 侧。
```

### 2. `app/mcp_clients/minimal_client.py`

这个文件是本节核心。

它封装：

```text
连接 minimal MCP Server。
列出 tools。
调用 tools。
读取 resource。
整理 JSON-friendly 调试快照。
```

这里没有业务逻辑。
这是有意为之。

因为本节学习目标是：

```text
看清 MCP Client 调试的基本形状。
```

### 3. `scripts/mcp_client_smoke.py`

这个文件是手动入口。

运行：

```powershell
uv run python scripts\mcp_client_smoke.py
```

能看到 JSON 输出。

这类 smoke 脚本的定位是：

```text
给学习者和开发者快速确认某条链路是否能跑通。
```

它不是正式服务入口。
它也不是完整测试替代品。

### 4. `tests/test_mcp_client_smoke.py`

这个文件是自动化保障。

它防止以后改 MCP Server 或 Client 时不小心破坏：

```text
tool name。
structured_content。
resource URI。
resource 内容。
```

这就是为什么要同时有脚本和测试：

```text
脚本方便人看。
测试方便机器长期守住边界。
```

## 手动验证

本节手动验证说明：

```text
notes/stage8-11-mcp-client-debugging-manual-tasks.md
```

最小命令：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts\mcp_client_smoke.py
```

预期能看到 JSON，里面包括：

```text
server
tools
tool_calls
resource_reads
```

聚焦测试：

```powershell
uv run pytest tests\test_mcp_client_smoke.py tests\test_minimal_mcp_server.py
```

预期：

```text
4 passed
```

## 常见误区

### 误区 1：Client 调试就是看工具能不能运行

不够。

Client 调试至少要看：

```text
工具是否能被发现。
工具 schema 是否正确。
工具描述是否清楚。
工具调用是否成功。
工具返回结构是否稳定。
资源是否能被读取。
错误标记是否正确。
```

### 误区 2：有 content 就不用 structured_content

不对。

`content` 更适合展示给人或模型看。
`structured_content` 更适合程序消费。

Agent 工程里要尽量依赖结构化结果。

### 误区 3：in-memory Client 通过了，就代表真实部署一定没问题

不对。

in-memory Client 能验证 server 能力注册和结果结构。
但不能验证：

```text
stdio transport。
HTTP transport。
进程启动。
stdout 污染。
网络。
session。
header。
权限。
```

后面需要分层补验证。

### 误区 4：MCP Inspector 可以替代测试

不可以。

Inspector 适合人工调试和观察。
pytest 适合自动回归。

真实项目两个都需要：

```text
Inspector 帮人理解和排查。
测试帮系统长期守住边界。
```

### 误区 5：调试脚本随便输出就行

不建议。

调试输出最好结构化。
因为以后要比较、复制、分析、记录时，JSON 比散乱文本更可靠。

## 项目映射

本节现在调的是：

```text
minimal MCP Server
```

后面真实项目会变成：

```text
MCP Client
-> list_tools
-> 看到 query_order/create_ticket
-> call_tool query_order
-> Python adapter 调 Java business service
-> 返回结构化订单结果
```

今天的 `add` 和 `echo` 很简单，但它们对应的调试方法以后不变：

```text
先 list。
看 schema。
call tool。
看 is_error。
看 structured_content。
看 content。
写测试固定结果。
```

这套方法以后可以用于任何 MCP Server。

## 本节练习

### 练习 1：MCP Client 是什么？

参考答案：

```text
MCP Client 是 Host 内部负责连接某个 MCP Server 的协议对象。它可以向 Server 发起 list_tools、call_tool、read_resource、get_prompt 等请求。
```

### 练习 2：为什么调试时要先 `list_tools`？

参考答案：

```text
因为 list_tools 可以确认工具是否正确暴露，并检查 name、description、input_schema、output_schema。如果工具发现阶段就不正确，后面的 call_tool 就没有可靠基础。
```

### 练习 3：`content` 和 `structured_content` 有什么区别？

参考答案：

```text
content 是内容块，更适合展示给人或模型看；structured_content 是结构化结果，更适合程序和 Agent 后续节点稳定消费。
```

### 练习 4：为什么本节脚本输出 JSON？

参考答案：

```text
JSON 结构稳定，字段清晰，便于阅读、复制、测试、日志记录和后续自动分析，比散乱 print 更适合工程调试。
```

### 练习 5：in-memory Client 的优点和限制是什么？

参考答案：

```text
优点是快、稳定、适合测试，不需要进程、端口、Node 或网络。限制是不能验证真实 stdio/HTTP transport、进程启动、stdout 污染、session/header 等部署细节。
```

### 练习 6：MCP Inspector 适合做什么？

参考答案：

```text
MCP Inspector 适合人工观察和调试 MCP Server，比如查看 tools、schema、resources、prompts，手动调用工具和排查返回。它不能替代自动化测试。
```

### 练习 7：为什么本节不调用真实大模型？

参考答案：

```text
因为本节验证的是 MCP Client 和 Server 的协议调用链，不是模型推理能力。真实大模型会引入 API Key、网络、费用和不稳定输出，反而干扰本节学习目标。
```

## 自测题

### 自测 1：一个 Host 是否只能有一个 MCP Client？

参考答案：

```text
不是。一个 Host 可以有多个 MCP Client，每个 Client 通常连接一个 MCP Server，用来接入不同工具、资源或 prompt 来源。
```

### 自测 2：`call_tool("add", {"a": 7, "b": 5})` 里的 `"add"` 是什么？

参考答案：

```text
它是 tool name，也就是 Server 通过 @mcp.tool() 暴露出来的工具标识。Client 通过这个名字选择要调用哪个工具。
```

### 自测 3：如果 `is_error` 是 true，说明什么？

参考答案：

```text
说明工具调用返回了工具级错误。它不一定是协议错误，可能是业务错误或系统错误。后面需要结合错误内容、错误码和错误处理策略判断。
```

### 自测 4：为什么真实订单工具应优先依赖结构化返回？

参考答案：

```text
因为结构化返回字段稳定，后续 Agent 节点可以准确读取 order_id、status、delivery_status 等字段。如果只依赖自然语言，程序很难稳定判断下一步。
```

### 自测 5：本节 `resource_reads` 验证了什么？

参考答案：

```text
验证 Client 能通过 resource URI 读取 Server 暴露的资源内容，也验证 URI template learning://hello/{name} 能正确匹配 panpan 参数。
```

### 自测 6：脚本和测试为什么都要有？

参考答案：

```text
脚本方便人手动运行和观察 JSON 输出；测试方便机器自动回归，防止以后修改代码时破坏 tool name、返回结构或 resource URI。
```

### 自测 7：第 11 节和第 10 节的区别是什么？

参考答案：

```text
第 10 节站在 Server 侧，学习如何暴露 tool/resource。第 11 节站在 Client 侧，学习如何发现、调用、读取和检查 Server 暴露的能力。
```

## 本节总结

本节真正要记住的是：

```text
MCP Client 是 Host 内部连接 MCP Server 的协议对象。
Client 调试要先 list，再 call/read。
list_tools 重点看 name、description、input_schema、output_schema。
call_tool 重点看 is_error、structured_content、content。
read_resource 重点看 URI 和 contents。
in-memory Client 适合单元测试和最小调试，但不能替代真实 transport 验证。
调试输出应该尽量结构化，方便人看，也方便测试和日志。
```

放到项目里：

```text
本节已经让 ai-service 具备了最小 MCP Client 调试能力。
现在我们不仅能写 MCP Server，还能站在 Client 角度检查它暴露了什么、调用后返回什么。
下一步就可以继续学习参数校验，让 MCP Tool 从“能调用”走向“能安全、稳定地调用”。
```

下一节学习：

```text
阶段 8 第 12 节：MCP 工具参数校验
```
