# 阶段 8 第 1 节：MCP 是什么

## 本节定位

本节是阶段 8 的第一节。

阶段 8 的主题是：

```text
MCP 与 AI 工具生态基础
```

这一节先不写代码。

原因是：

```text
MCP 不是一个普通 Python 库。
MCP 也不是一个新的 HTTP 接口写法。
MCP 是 AI 应用连接外部工具、数据源和上下文资源的一套协议思想。
```

如果一开始就写代码，很容易只记住：

```text
装一个包
写一个函数
跑一个 server
```

但不知道：

```text
为什么需要 MCP？
MCP 解决了什么问题？
MCP 和 Tool Calling 有什么不同？
Host / Client / Server 到底谁是谁？
Tool / Resource / Prompt 分别该放什么？
MCP 放在我们现有 Java + Python + AI 项目里的哪个位置？
```

所以本节目标是先把 MCP 的基本认知搭起来。

## 本节学习目标

学完本节后，你应该能用自己的话讲清楚：

```text
MCP 是什么。
MCP 为什么出现。
MCP 和普通 HTTP API 的区别。
MCP 和 Tool Calling 的关系。
MCP 里的 Host / Client / Server 是什么。
MCP 里的 Tool / Resource / Prompt 是什么。
MCP 为什么对 Agent 很重要。
MCP 在当前项目里可能怎么落地。
```

## 本节不做什么

本节不做：

```text
不安装 MCP SDK。
不写 MCP Server。
不调用 Java business service。
不启动 MySQL / Redis。
不打开 VMware Ubuntu。
不接真实大模型。
不做敏感扫描。
```

本节只做：

```text
概念学习
项目定位
笔记沉淀
手动复习清单
```

## 官方资料依据

本节参考 MCP 官方文档和官方规格说明：

| 资料 | 用途 |
| --- | --- |
| [MCP Introduction](https://modelcontextprotocol.io/docs/getting-started/intro) | MCP 是什么、解决什么问题 |
| [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture) | Host / Client / Server 和整体架构 |
| [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25) | 协议定位、JSON-RPC、参与者 |
| [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | Tool 的定位、调用和安全提示 |
| [MCP Resources](https://modelcontextprotocol.io/specification/2025-06-18/server/resources) | Resource 的定位 |
| [MCP Prompts](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts) | Prompt 的定位 |
| [MCP Lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) | 初始化、运行、关闭 |

注意：

```text
MCP 规格仍在快速演进。
本节先学稳定核心概念，不在第一节深入版本差异和草案变化。
后续学到通信、生命周期、Transport 时，再专门处理版本和协议细节。
```

## 基础知识铺垫

### 1. 先回忆：普通 AI 应用怎么连接外部系统

我们前面已经做过很多类似能力。

比如用户问：

```text
我的 A1001 订单现在怎么样？
```

AI 不能自己编订单状态。

于是我们做了：

```text
用户问题
-> Agent 判断需要查订单
-> Python AI 服务调用 query_order 工具
-> Python client 调 Java 业务服务
-> Java 查 MySQL / Redis
-> 返回订单摘要
-> AI 再组织中文回答
```

这条链路本质是：

```text
AI 应用需要连接外部业务系统。
```

在我们当前项目里，这个外部业务系统是：

```text
Java business service
```

在真实公司里，外部系统可能更多：

```text
订单系统
退款系统
物流系统
CRM
工单系统
知识库
文件系统
数据库
GitHub
飞书 / Slack
Notion
Google Drive
内部报表平台
```

如果每个 AI 应用都自己写一套连接方式，就会很混乱。

### 2. 没有 MCP 时，集成会有什么问题

假设公司里有 3 个 AI 应用：

```text
客服 Agent
运营数据助手
研发代码助手
```

又有 5 个外部系统：

```text
订单系统
工单系统
知识库
数据库
GitHub
```

如果没有统一协议，可能会变成：

```text
客服 Agent 自己写订单 API adapter。
运营助手自己写订单 API adapter。
代码助手自己写 GitHub adapter。
客服 Agent 自己写知识库 adapter。
运营助手又写一套数据库 adapter。
```

问题会越来越多：

```text
每个 AI 应用都重复接一遍外部系统。
同一个工具在不同应用里参数名字不一致。
工具描述、参数 schema、错误处理散落各处。
权限规则难统一。
工具列表不能被 AI 应用标准发现。
资源和 prompt 没有统一暴露方式。
```

这就是 MCP 要解决的大背景：

```text
AI 应用越来越多，外部系统越来越多，需要一个标准连接方式。
```

### 3. MCP 最基础的一句话定义

MCP 全称是：

```text
Model Context Protocol
```

可以翻译成：

```text
模型上下文协议
```

更容易理解的说法是：

```text
MCP 是一套让 AI 应用连接外部工具、数据源和上下文资源的开放协议。
```

这句话有几个关键词：

| 关键词 | 含义 |
| --- | --- |
| AI 应用 | 例如 ChatGPT、Claude Desktop、Claude Code、IDE Agent、我们自己的 ai-service |
| 外部工具 | 查订单、查数据库、调 API、搜索、计算、创建工单 |
| 数据源 | 文件、数据库、文档、业务资料、schema |
| 上下文资源 | 能提供给模型理解任务的信息 |
| 开放协议 | 不是某一个应用私有接口，而是一套可被多个客户端和服务端实现的约定 |

所以 MCP 不是：

```text
一个模型
一个 Agent 框架
一个数据库
一个向量库
一个 prompt 写法
一个普通 REST API
```

MCP 更像：

```text
AI 应用和外部系统之间的标准连接层。
```

### 4. 为什么官方常把 MCP 类比成 USB-C

官方文档里会用 USB-C 类比 MCP。

这个类比的意思不是说 MCP 真的像硬件接口，而是说：

```text
USB-C 让不同设备用统一接口连接。
MCP 让不同 AI 应用和外部系统用统一协议连接。
```

没有 USB-C 时，你可能需要：

```text
这个设备一根线
那个设备一根线
这个接口一个转接头
那个接口一个转接头
```

没有 MCP 时，AI 应用集成也可能变成：

```text
这个 AI 应用一套工具接入方式
那个 AI 应用一套插件方式
这个服务一套自定义 API adapter
那个服务一套特殊 JSON schema
```

MCP 的目标是降低这种重复集成成本。

但要注意：

```text
USB-C 只是帮助理解“标准连接”的类比。
真正开发时，还是要理解 MCP 的 Host / Client / Server / Tool / Resource / Prompt / Transport。
```

### 5. 先别把 MCP 想成“让模型直接访问系统”

这是初学 MCP 最容易犯的错误。

错误理解：

```text
MCP 就是让大模型直接调用数据库、直接访问文件、直接创建工单。
```

正确理解：

```text
MCP 是让 AI 应用通过标准协议连接外部能力。
真正的权限控制、用户确认、参数校验、审计和执行边界仍然要由应用和服务端负责。
```

模型不是直接拿到系统控制权。

更合理的链路是：

```text
用户
-> AI 应用 Host
-> MCP Client
-> MCP Server
-> 受控工具 / 资源 / prompt
-> 外部系统
```

这和阶段 7 的思想一致：

```text
AI 提出意图。
后端执行动作。
权限、幂等、trace_id、错误码、契约测试不能丢。
```

## 本节主题系统讲解

### 1. MCP 要解决的核心问题

MCP 的核心问题可以总结成一句话：

```text
让 AI 应用用统一方式发现、获取和调用外部上下文能力。
```

这里的“上下文能力”包括三类：

```text
Tools
Resources
Prompts
```

分别对应：

```text
能执行动作的工具
能提供上下文的数据
能复用的提示模板
```

比如在我们项目里：

| MCP 能力 | 当前项目可能对应什么 |
| --- | --- |
| Tool | 查询订单、创建工单、查询退款进度 |
| Resource | Java-AI API 契约文档、数据库 schema、学习笔记、业务规则文档 |
| Prompt | 工单分析模板、客服回复模板、RAG 回答模板 |

MCP 不是只解决“调用函数”。

它还解决：

```text
AI 应用怎么知道有哪些工具。
AI 应用怎么知道工具参数 schema。
AI 应用怎么读取外部上下文资源。
AI 应用怎么获取服务器提供的 prompt 模板。
AI 应用怎么和不同 MCP Server 建立连接。
AI 应用怎么根据能力协商判断服务器支持什么。
```

### 2. MCP 和普通 HTTP API 的区别

普通 HTTP API 是服务对外提供的接口。

比如阶段 7 的 Java 接口：

```text
GET /internal/orders/{order_id}
POST /internal/tickets
```

它们解决：

```text
具体业务服务如何被调用。
```

MCP 解决的是更上一层的问题：

```text
AI 应用如何标准发现和使用外部系统能力。
```

对比：

| 对比项 | 普通 HTTP API | MCP |
| --- | --- | --- |
| 核心目标 | 给调用方提供业务接口 | 给 AI 应用提供统一上下文和工具接入协议 |
| 调用前是否标准发现能力 | 通常没有，靠文档或代码写死 | 有标准的能力和列表机制 |
| 工具参数 schema | 通常散落在接口文档 / OpenAPI / DTO | Tool 自带输入 schema |
| 资源暴露 | 通常自己设计接口 | Resource 是协议级概念 |
| Prompt 暴露 | 通常没有标准 | Prompt 是协议级概念 |
| 面向对象 | 通用服务调用方 | AI Host / Client / Server |
| 是否替代业务 API | 不替代 | 不替代，通常会包装或连接已有 API |

所以：

```text
MCP 不是用来消灭 HTTP API。
MCP 可以把 HTTP API 包装成 AI 能标准发现和调用的工具。
```

在我们项目里，未来可能是：

```text
MCP Tool: query_order
-> Python MCP Server
-> JavaOrderClient
-> Java business service 的 GET /internal/orders/{order_id}
```

也就是说：

```text
Java API 仍然存在。
MCP Server 是 AI 接入层。
```

### 3. MCP 和 Tool Calling 的关系

Tool Calling 我们已经学过。

Tool Calling 的重点是：

```text
模型根据工具定义，决定是否请求调用某个工具。
```

典型链路：

```text
应用把 tools schema 发给模型
模型输出 tool_call
应用校验 tool_call
应用执行工具
应用把工具结果再交给模型
```

MCP 的重点不是“某个模型 API 怎么输出 tool_call”。

MCP 的重点是：

```text
AI 应用怎么从 MCP Server 发现工具、资源和 prompt。
```

可以这样理解：

```text
Tool Calling 是模型交互层能力。
MCP 是工具和上下文接入层协议。
```

二者可以配合：

```text
MCP Server 暴露工具。
MCP Client 列出工具。
AI Host 把这些工具转换成模型可用的 tool schema。
模型选择调用某个工具。
Host / Client 通过 MCP 调用 Server 上的工具。
工具结果返回给模型生成回答。
```

所以不要把它们对立起来。

更准确的关系是：

```text
MCP 可以成为 Tool Calling 背后的工具来源。
```

### 4. MCP 的三个参与者：Host / Client / Server

MCP 采用 client-server 架构。

但它的术语和普通前后端有一点不同。

#### Host 是什么

Host 是用户正在使用的 AI 应用。

比如：

```text
Claude Desktop
Claude Code
ChatGPT
某个 IDE Agent
公司内部 AI 助手
我们未来的 ai-service 或 Agent 平台
```

Host 负责：

```text
和用户交互。
管理一个或多个 MCP Client。
决定如何把 MCP Server 暴露的能力交给模型或界面。
处理用户确认、安全提示、上下文组装。
```

简单说：

```text
Host 是 AI 应用本体。
```

#### Client 是什么

Client 是 Host 里负责连接某个 MCP Server 的连接器。

一个 Host 可以连接多个 Server。

通常是：

```text
一个 MCP Server 对应一个 MCP Client。
```

比如：

```text
Host: 一个 AI 助手
Client A -> 文件系统 MCP Server
Client B -> GitHub MCP Server
Client C -> 公司订单 MCP Server
Client D -> 公司知识库 MCP Server
```

Client 负责：

```text
建立连接。
初始化和能力协商。
发送 tools/list、tools/call、resources/read 等协议请求。
接收 Server 响应。
把结果交回 Host。
```

简单说：

```text
Client 是 Host 和某个 MCP Server 之间的协议连接。
```

#### Server 是什么

Server 是真正暴露能力的一方。

它可以暴露：

```text
Tools
Resources
Prompts
```

比如：

```text
文件系统 MCP Server 暴露文件读写能力。
GitHub MCP Server 暴露 issue / PR / repo 能力。
数据库 MCP Server 暴露查询能力。
订单 MCP Server 暴露 query_order 工具。
项目文档 MCP Server 暴露学习笔记和 API 契约资源。
```

Server 负责：

```text
声明自己支持哪些能力。
提供工具列表。
执行工具调用。
提供资源列表和资源内容。
提供 prompt 模板。
做自己的权限、参数校验、错误处理和审计。
```

简单说：

```text
Server 是外部能力的标准化出口。
```

### 5. 一张最小 MCP 架构图

```text
用户
  |
  v
MCP Host：AI 应用
  |
  | 创建并管理
  v
MCP Client：连接某个 Server 的连接器
  |
  | MCP 协议
  v
MCP Server：暴露 Tools / Resources / Prompts
  |
  | 内部调用
  v
外部系统：文件、数据库、Java 业务服务、知识库、第三方 API
```

放到我们项目里，未来可能是：

```text
用户
  |
  v
Python AI Agent / ai-service
  |
  v
MCP Client
  |
  v
项目 MCP Server
  |
  +-> Tool: query_order -> Java business service
  +-> Tool: create_ticket -> Java business service
  +-> Resource: java-ai-api-contract.md
  +-> Resource: stage7 notes
  +-> Prompt: customer_ticket_summary_prompt
```

### 6. MCP Tool 是什么

Tool 是 MCP Server 暴露给 AI 应用的可执行能力。

官方语义里，Tool 用于让模型和外部系统交互，例如：

```text
查询数据库
调用 API
执行计算
创建工单
搜索文档
```

Tool 一般包含：

```text
工具名
工具描述
输入参数 schema
返回结果
错误信息
```

在我们项目里，典型 MCP Tool 可能是：

```text
query_order(order_id)
create_ticket(title, description, category, priority, related_order_id)
```

但是注意：

```text
Tool 能被模型请求调用，不代表模型应该无条件执行成功。
```

尤其是写操作：

```text
创建工单
取消订单
退款
修改地址
发送消息
```

必须继续保留：

```text
用户确认
权限判断
幂等键
trace_id
错误码
审计日志
```

这和阶段 7 完全一致。

### 7. MCP Resource 是什么

Resource 是 MCP Server 暴露给 Client 的上下文数据。

它更像：

```text
可被 AI 应用读取的资料、文件、schema、文档、业务上下文。
```

Resource 通常有 URI。

比如：

```text
file:///docs/java-ai-api-contract.md
project://notes/stage7-12-project-summary
dbschema://ai_business/orders
policy://refund-return-policy
```

在我们项目里，Resource 可以是：

```text
Java-AI API 契约文档
Java business 数据库设计文档
阶段 7 学习总结
RAG 业务知识库文档
工单字段说明
错误码表
```

Resource 和 Tool 的区别：

```text
Tool 偏动作。
Resource 偏上下文。
```

举例：

```text
读取“订单接口契约文档”是 Resource。
调用“查询订单接口”是 Tool。
```

### 8. MCP Prompt 是什么

Prompt 是 MCP Server 暴露的可复用提示模板。

它不是用户随便发的一句话，而是：

```text
服务器提供给 AI 应用的结构化 prompt 模板。
```

比如：

```text
客服工单总结模板
RAG 回答模板
代码 review 模板
数据库查询分析模板
订单异常分析模板
```

在我们项目里，未来可能有：

```text
customer_service_answer_prompt
ticket_creation_confirmation_prompt
order_problem_analysis_prompt
rag_citation_answer_prompt
```

Prompt 和 Resource 的区别：

```text
Resource 提供事实资料。
Prompt 提供任务指令模板。
```

Prompt 和 Tool 的区别：

```text
Prompt 指导模型怎么做。
Tool 让系统执行某个动作。
```

### 9. MCP 的通信基础：先知道 JSON-RPC

本节不展开协议细节，但先知道一件事：

```text
MCP 的底层消息使用 JSON-RPC 2.0。
```

这意味着 MCP 不是随便约定一堆 HTTP path。

它更像：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

或者：

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

你现在只要理解：

```text
MCP 是协议。
协议里有标准消息。
后续第 4 节会专门学通信基础。
```

### 10. MCP 生命周期先了解三个阶段

官方稳定规格中，MCP 连接生命周期通常包括：

```text
Initialization
Operation
Shutdown
```

意思是：

| 阶段 | 做什么 |
| --- | --- |
| Initialization | Client 和 Server 建立协议版本、能力协商、实现信息 |
| Operation | 正常列工具、调工具、读资源、取 prompt |
| Shutdown | 连接关闭 |

这一节不用记协议字段。

先知道：

```text
MCP Client 不是随便上来就调用工具。
它需要先知道 Server 支持什么能力。
```

这就是“能力协商”的意义。

### 11. MCP 为什么对 Agent 很重要

Agent 的能力来自三部分：

```text
模型推理能力
外部工具能力
上下文获取能力
```

模型本身不知道你公司的实时订单状态。

模型本身也不会自动知道：

```text
这个系统有哪些工具
工具怎么调用
参数是什么
哪些资源可以读
有哪些 prompt 模板可用
```

MCP 对 Agent 的价值是：

```text
让 Agent 能以标准方式连接外部能力。
```

它让工具生态更容易组合：

```text
今天接文件系统 Server。
明天接 GitHub Server。
后天接公司订单 Server。
再接公司知识库 Server。
```

如果每个 Server 都遵守 MCP，Host 就能用一套通用方式管理这些能力。

### 12. MCP 在当前项目里可能放在哪里

当前项目已经有：

```text
Python ai-service
Java mock service
Java business service
RAG
LangGraph Agent
Tool Calling
契约测试
```

阶段 8 后续有两个可能设计。

#### 方案 A：MCP 能力放进 ai-service

目录可能是：

```text
projects/ai-service/app/mcp/
```

适合：

```text
MCP 只是当前 Python AI 服务的内部能力。
我们想让 ai-service 自己提供 MCP Server 或 MCP adapter。
不想新增独立进程。
```

优点：

```text
复用现有 Python 配置、日志、错误映射、Java client。
学习成本低。
代码集中。
```

缺点：

```text
MCP Server 和 ai-service 生命周期耦合。
以后如果要独立部署，可能要拆。
```

#### 方案 B：单独建 mcp-service

目录可能是：

```text
projects/mcp-service/
```

适合：

```text
MCP Server 要作为独立服务演示。
未来多个 AI Host 都可能连接它。
希望 MCP 能力和 ai-service 解耦。
```

优点：

```text
边界清晰。
更像真实 MCP Server。
以后可以独立部署。
```

缺点：

```text
多一个项目和配置。
需要处理更多运行、测试、依赖管理。
```

本阶段暂不立即决定。

第 10 节开始写最小 MCP Server 前，再根据实际学习目标定。

### 13. 本项目里 MCP 和 Java business service 的关系

一定要分清三层：

```text
MCP Tool
Python adapter / client
Java business API
```

未来可能是：

```text
MCP Tool: query_order
  -> Python MCP Server 函数
  -> JavaOrderClient
  -> GET /internal/orders/{order_id}
  -> Java business service
  -> MySQL / Redis
```

这说明：

```text
MCP Tool 不是直接查 MySQL。
MCP Tool 也不应该绕过 Java 权限和业务规则。
```

阶段 7 做的东西仍然有用：

```text
internal token
X-User-Id
X-Tenant-Id
X-Trace-Id
Idempotency-Key
错误码映射
契约测试
```

MCP 只是把这些能力包装成 AI 生态更标准的接口。

不是让模型绕过这些边界。

### 14. 初学 MCP 的 5 个误区

#### 误区 1：MCP 等于 Tool Calling

不对。

```text
Tool Calling 是模型交互能力。
MCP 是上下文和工具接入协议。
```

二者能配合，但不是一回事。

#### 误区 2：MCP 等于普通 HTTP API

不对。

```text
HTTP API 是业务服务接口。
MCP 是 AI 应用连接外部能力的协议。
```

MCP 可以包装 HTTP API，但不等于 HTTP API。

#### 误区 3：MCP 让模型直接操作系统

不对。

```text
模型可以请求工具。
Host / Client / Server 负责受控执行。
敏感操作仍然需要权限、确认、幂等和审计。
```

#### 误区 4：MCP 只适合工具

不对。

MCP 还包括：

```text
Resources
Prompts
```

只学 Tool 会把 MCP 学窄。

#### 误区 5：学 MCP 就不用学后端工程

不对。

MCP 只是接入协议。

真正落地仍然需要：

```text
后端业务规则
数据库
权限
日志
测试
稳定性
部署
```

阶段 7 的后端基础仍然是 MCP 工具安全落地的前提。

## 和我们现有知识的关系

### 和 RAG 的关系

RAG 解决：

```text
从知识库检索上下文，再让模型基于上下文回答。
```

MCP Resource 可以提供：

```text
文档
schema
业务规则
API 契约
```

所以 MCP 可以成为 RAG 或 Agent 获取上下文的一种来源。

但：

```text
MCP 不等于 RAG。
RAG 是检索增强生成流程。
MCP 是连接外部上下文和工具的协议。
```

### 和 LangGraph 的关系

LangGraph 解决：

```text
Agent 多步骤流程编排。
```

MCP 解决：

```text
Agent 使用外部能力的标准接入。
```

未来可能是：

```text
LangGraph 某个 node 需要查订单。
这个 node 不直接写死 HTTP 调用。
它通过 MCP Client 调用 query_order tool。
```

所以：

```text
LangGraph 管流程。
MCP 管外部能力接入。
```

### 和 Java business service 的关系

Java business service 解决：

```text
真实业务规则、权限、事务、MySQL、Redis、错误码。
```

MCP 解决：

```text
把这些业务能力标准化暴露给 AI 应用。
```

所以：

```text
Java business service 是业务后端。
MCP Server 是 AI 接入层。
```

## 本节结论

你现在可以先用下面这段话记住 MCP：

```text
MCP 是 AI 应用连接外部系统的开放协议。
它让 AI Host 通过 Client 连接 MCP Server，从 Server 发现和使用 Tools、Resources、Prompts。
Tool 用来执行动作，Resource 用来提供上下文，Prompt 用来提供可复用提示模板。
MCP 不替代 Tool Calling、不替代 HTTP API、不替代 Java 后端。
它更像 AI 工具生态的标准接入层。
```

放到我们的项目里：

```text
阶段 7 已经有真实 Java business service。
阶段 8 学 MCP，是为了以后把订单查询、创建工单、项目文档、业务规则等能力按标准协议暴露给 AI 应用。
```

## 本节练习

### 练习 1：用一句话解释 MCP

参考答案：

```text
MCP 是一套开放协议，用来让 AI 应用以标准方式连接外部工具、数据源、资源和 prompt。
```

### 练习 2：MCP 和普通 HTTP API 有什么区别？

参考答案：

```text
普通 HTTP API 是具体业务服务的接口，调用方通常靠文档或代码知道怎么调。
MCP 是 AI 应用连接外部能力的协议，它包含能力发现、工具 schema、资源、prompt、协议消息和 client-server 连接模型。
MCP 可以包装 HTTP API，但不等于 HTTP API。
```

### 练习 3：MCP 和 Tool Calling 有什么关系？

参考答案：

```text
Tool Calling 是模型请求调用工具的能力。
MCP 是 AI 应用发现和连接外部工具、资源、prompt 的协议。
MCP Server 暴露的 tools 可以被 Host 转成模型可用的 Tool Calling 工具定义。
```

### 练习 4：Host / Client / Server 分别是什么？

参考答案：

```text
Host 是用户使用的 AI 应用，比如 ChatGPT、Claude Desktop、IDE Agent 或我们未来的 ai-service。
Client 是 Host 内部连接某个 MCP Server 的连接器。
Server 是暴露 Tools、Resources、Prompts 的外部能力提供方。
```

### 练习 5：Tool / Resource / Prompt 分别适合放什么？

参考答案：

```text
Tool 适合放可执行动作，比如查询订单、创建工单、调用 API。
Resource 适合放上下文资料，比如文档、数据库 schema、API 契约、业务规则。
Prompt 适合放可复用提示模板，比如客服回复模板、工单总结模板、RAG 回答模板。
```

## 自测题

### 自测 1：MCP 会不会替代 Java business service？

参考答案：

```text
不会。
Java business service 负责真实业务规则、权限、事务、MySQL、Redis 和错误码。
MCP 只是把这些能力按 AI 应用更容易接入的方式标准化暴露出来。
```

### 自测 2：为什么 MCP 工具仍然需要权限和用户确认？

参考答案：

```text
因为 MCP 只是协议，不会自动保证业务安全。
模型可能误判用户意图，写操作可能改变真实业务状态。
所以创建工单、退款、修改地址等操作仍然需要权限、用户确认、幂等键、trace_id 和审计日志。
```

### 自测 3：在当前项目中，`query_order` 如果做成 MCP Tool，内部链路应该怎么走？

参考答案：

```text
MCP Client 调用 query_order tool。
MCP Server 接收工具调用并校验参数。
MCP Server 内部调用 Python 的 JavaOrderClient。
JavaOrderClient 调 Java business service 的 /internal/orders/{order_id}。
Java business service 做鉴权、权限、缓存、数据库查询和统一响应。
MCP Server 把安全结果返回给 Client。
```

### 自测 4：Resource 和 Tool 最关键的区别是什么？

参考答案：

```text
Tool 偏动作，会执行外部操作。
Resource 偏上下文，用来读取资料、文档、schema、业务信息。
读取 API 契约文档是 Resource，调用订单查询接口是 Tool。
```

### 自测 5：为什么本节不急着写 MCP Server？

参考答案：

```text
因为 MCP 首先是一套连接 AI 应用和外部能力的协议思想。
如果没有先理解 Host、Client、Server、Tool、Resource、Prompt，直接写代码容易只会跑 demo，不知道它解决什么问题，也不知道怎么放进当前项目。
```

## 本节总结

本节是 MCP 的概念地基。

最重要的 5 句话：

```text
MCP 是 AI 应用连接外部系统的开放协议。
MCP 的参与者是 Host、Client、Server。
MCP Server 可以暴露 Tools、Resources、Prompts。
MCP 不替代 Tool Calling、HTTP API、RAG、LangGraph 或 Java 后端。
MCP 在我们项目里的价值，是把 Java business service、项目文档和业务 prompt 变成 AI 应用可以标准连接的能力。
```

下一节学习：

```text
阶段 8 第 2 节：MCP 和 Tool Calling 的区别
```
