# 阶段 8 第 3 节：MCP 架构

## 本节定位

本节是阶段 8 第 3 节。

前两节我们已经解决了两个问题：

```text
第 1 节：MCP 是什么。
第 2 节：MCP 和 Tool Calling 有什么区别。
```

这一节开始进入 MCP 的核心架构。

本节要解决的是：

```text
MCP 这套协议到底由哪些角色组成？
Host、Client、Server 分别是什么？
为什么不是一个 AI 应用直接连一个工具，而是中间多了 Client？
为什么一个 Host 可以连接多个 Server？
Tools、Resources、Prompts 在架构里放在哪里？
MCP 架构和我们当前项目里的 ai-service、tool_registry、Java business service 怎么对应？
```

本节最重要的一句话：

```text
MCP 是 Host 创建并管理多个 Client，每个 Client 连接一个 Server，Server 对外暴露 Tools、Resources、Prompts 等能力。
```

如果你只把 MCP 理解成“一个远程工具调用协议”，就会学窄。

更准确的理解是：

```text
MCP 是一套让 AI 应用标准连接外部上下文和外部能力的 Host-Client-Server 架构。
```

## 本节学习目标

学完本节后，你应该能讲清楚：

```text
什么是 MCP Host。
什么是 MCP Client。
什么是 MCP Server。
为什么 Host 可以有多个 Client。
为什么每个 Client 通常只对应一个 Server。
为什么 Server 要保持职责边界清晰。
MCP 的 data layer 和 transport layer 大概分别负责什么。
Tools、Resources、Prompts 分别属于哪一侧提供的能力。
MCP 架构和 Tool Calling、LangGraph、RAG、Java business service 的关系。
当前项目以后怎么演进到 MCP 架构。
```

本节不是让你背概念，而是让你能看懂一张 MCP 架构图，并且能把它映射到真实项目。

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
概念讲解
架构拆解
项目映射
练习和自测
学习索引更新
```

## 官方资料依据

本节参考的官方资料：

| 资料 | 本节使用点 |
| --- | --- |
| [MCP Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture) | MCP 的 Host / Client / Server 参与者、一个 Host 连接多个 Server、data layer 和 transport layer |
| [MCP Specification: Architecture](https://modelcontextprotocol.io/specification/2025-11-25/architecture) | Host、Client、Server 的职责、1 个 Client 对应 1 个 Server、安全边界和组合原则 |
| [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25) | MCP 是连接 LLM 应用与外部数据源和工具的开放协议，协议使用 JSON-RPC，Server 提供 Resources、Prompts、Tools |
| [MCP Base Protocol Overview](https://modelcontextprotocol.io/specification/2025-11-25/basic) | MCP 基础协议、生命周期、能力协商、Server Features、Client Features 和通用工具能力 |

说明：

```text
本节只讲架构理解。
JSON-RPC 细节、生命周期细节、transport 细节会在后续第 4、5、6 节展开。
```

## 基础知识铺垫

### 1. 什么叫“架构”

学 MCP 架构前，先不要急着背 Host、Client、Server。

要先理解“架构”这个词。

在后端开发里，架构不是一个目录名，也不是画一张复杂图。

架构本质上回答几个问题：

```text
系统由哪些部分组成？
每个部分负责什么？
部分之间怎么通信？
谁拥有核心控制权？
谁负责安全边界？
谁可以独立替换或扩展？
```

比如传统 Spring Boot 三层架构：

```text
Controller
Service
Mapper
```

它不是为了好看，而是为了分清职责：

```text
Controller 负责 HTTP 请求入口。
Service 负责业务逻辑。
Mapper 负责数据库访问。
```

你看到这个结构，就知道：

```text
HTTP 参数不要直接在 Mapper 里处理。
SQL 不要写在 Controller 里。
业务事务不要散落在 Controller 和 Mapper 之间。
```

这就是架构的价值。

MCP 架构也是一样。

它要分清：

```text
AI 应用谁来代表？
连接谁来维护？
外部工具和资源谁来暴露？
安全和用户确认谁来管？
多外部系统怎么组合？
```

所以本节不是背名词，而是学会看职责边界。

### 2. 为什么 AI 应用需要特殊架构

传统 Web 后端通常是：

```text
前端
  |
  v
后端 API
  |
  v
数据库 / Redis / 第三方服务
```

AI 应用多了一个特殊参与者：

```text
大模型
```

大模型有几个特点：

```text
它能理解自然语言。
它能根据上下文选择工具。
它能生成参数。
它也可能误解、幻觉、越权、被 prompt injection 影响。
```

所以 AI 应用不能简单写成：

```text
模型直接调用数据库。
模型直接调用订单系统。
模型直接读取所有文件。
模型直接创建工单。
```

正确的结构应该是：

```text
模型只表达意图。
AI 应用负责控制边界。
外部系统通过受控接口暴露能力。
```

MCP 的 Host-Client-Server 架构，就是围绕这个问题来的。

### 3. 从“一个工具”到“工具生态”

如果只有一个工具，比如：

```text
query_order
```

你可以直接在 `ai-service` 里写一个函数，然后给模型一个 tools schema。

这时结构很简单：

```text
模型
  |
  v
ai-service tool_registry
  |
  v
Java business service
```

但真实项目慢慢会变成：

```text
订单查询
创建工单
退款规则查询
物流接口查询
客户画像读取
知识库文档读取
数据库 schema 读取
GitHub issue 查询
客服回复 prompt 模板
工单总结 prompt 模板
```

这时你面对的已经不是“一个工具怎么调用”，而是：

```text
很多工具、很多资源、很多 prompt 怎么被 AI 应用标准连接。
```

MCP 要解决的就是这个级别的问题。

它不是只为了让模型多调一个函数。

它是为了让外部能力变成可发现、可连接、可组合的生态。

### 4. MCP 里为什么要分 Host、Client、Server

如果只看名字，你可能会觉得：

```text
Host 不就是客户端吗？
Client 不就是客户端吗？
为什么一个架构里同时有 Host 和 Client？
```

这是 MCP 最容易让初学者困惑的点。

你可以这样理解：

```text
Host 是整个 AI 应用。
Client 是 Host 里面负责连接某个 MCP Server 的连接组件。
Server 是外部能力提供方。
```

举一个更贴近后端的类比。

假设你有一个 Spring Boot 系统：

```text
order-admin-service
```

它里面可能有多个下游 client：

```text
UserClient
PaymentClient
LogisticsClient
TicketClient
```

这时：

```text
order-admin-service 是业务应用整体。
UserClient 只是它里面连接用户服务的 HTTP client。
PaymentClient 只是它里面连接支付服务的 HTTP client。
```

同理：

```text
MCP Host 是 AI 应用整体。
MCP Client 是 Host 里面连接某个 MCP Server 的组件。
```

所以 Host 和 Client 不是重复概念。

它们的层级不同。

### 5. 先记住这张最小架构图

```text
MCP Host
  |
  | 创建和管理
  v
MCP Client
  |
  | 通过 MCP 协议连接
  v
MCP Server
  |
  | 暴露
  v
Tools / Resources / Prompts
```

如果有多个 Server：

```text
MCP Host
  |
  |-- MCP Client A --> Order MCP Server
  |
  |-- MCP Client B --> Docs MCP Server
  |
  |-- MCP Client C --> GitHub MCP Server
```

重点：

```text
一个 Host 可以管理多个 Client。
一个 Client 通常维护一个 Server 连接。
一个 Server 负责一个边界清晰的外部能力集合。
```

## 本节主题系统讲解

### 1. MCP 总体架构

MCP 官方架构的核心是：

```text
Host
Client
Server
```

这三个词的中文理解可以先这样记：

| 角色 | 简单理解 | 关键职责 |
| --- | --- | --- |
| Host | AI 应用本体 | 管模型、管用户、管上下文、管多个 Client、管安全策略 |
| Client | Host 内部的连接器 | 连接一个 MCP Server，处理协议通信和能力协商 |
| Server | 外部能力服务 | 暴露 Tools、Resources、Prompts 等能力 |

一张更完整的图：

```text
用户
  |
  v
MCP Host / AI 应用
  - 管 UI 或 API
  - 管模型调用
  - 管用户授权
  - 管上下文整合
  - 管多个 MCP Client
  |
  |-- MCP Client 1 --> MCP Server 1: 订单能力
  |
  |-- MCP Client 2 --> MCP Server 2: 项目文档
  |
  |-- MCP Client 3 --> MCP Server 3: GitHub 能力
```

你要特别注意：

```text
模型不等于 Host。
MCP Client 不等于用户使用的客户端界面。
MCP Server 不一定是远程 HTTP 服务，也可以是本地进程。
```

这些词和传统 Web 里的“客户端/服务端”有重合，但不是完全一样。

### 2. Host 是什么

MCP Host 是整个 AI 应用。

常见例子：

```text
Claude Desktop
Claude Code
VS Code 里的 AI Agent
ChatGPT 里支持连接工具的环境
公司内部客服 AI 助手
我们未来的 ai-service
```

Host 的核心职责不是“执行某个工具”，而是协调全局。

它要负责：

```text
管理用户输入。
管理模型调用。
管理系统 prompt 和上下文。
创建和管理多个 MCP Client。
决定连接哪些 MCP Server。
决定哪些 Server 的能力可以暴露给模型。
做用户授权和确认。
聚合多个 Server 返回的上下文。
控制安全策略。
处理最终回答。
```

也就是说，Host 是主控方。

如果把 AI 应用比成一个公司客服工作台：

```text
Host 是客服工作台本身。
Client 是工作台接入不同系统的连接模块。
Server 是订单系统、工单系统、文档系统等外部能力提供方。
```

Host 最重要的职责之一是：

```text
不要把所有上下文和所有权限都无脑交给模型或 Server。
```

比如用户问：

```text
帮我查 A1001 订单物流。
```

Host 要决定：

```text
这个用户是谁？
他属于哪个租户？
他能不能查 A1001？
是否允许模型看到订单的哪些字段？
是否需要调用订单 MCP Server？
工具结果回来后哪些字段可以给模型总结？
```

这些都不是 MCP Server 单独能决定的。

### 3. Client 是什么

MCP Client 是 Host 里面的连接组件。

它不是用户打开的那个“客户端软件”。

在 MCP 语境里，Client 更像：

```text
Host 内部负责连接某个 MCP Server 的协议适配器。
```

它负责：

```text
和一个 MCP Server 建立连接。
做初始化。
做能力协商。
发送 tools/list、tools/call 等请求。
接收 Server 返回的响应。
处理通知、订阅、进度等协议消息。
把 Server 的能力交给 Host 使用。
```

为什么要有 Client？

因为一个 Host 可能连接很多 Server。

如果没有 Client 这一层，Host 就要直接维护所有连接细节：

```text
订单 Server 怎么连？
文档 Server 怎么连？
GitHub Server 怎么连？
每个 Server 支持什么能力？
每个 Server 的通知怎么收？
每个 Server 的生命周期怎么管？
```

这会让 Host 非常混乱。

Client 的价值就是：

```text
每个 Client 专心维护一个 Server 连接。
Host 只需要管理多个 Client。
```

这和传统后端里每个下游服务一个 client 很像：

```text
OrderClient -> order-service
PaymentClient -> payment-service
LogisticsClient -> logistics-service
```

MCP 里是：

```text
OrderMcpClient -> OrderMcpServer
DocsMcpClient -> DocsMcpServer
GitHubMcpClient -> GitHubMcpServer
```

### 4. Server 是什么

MCP Server 是外部能力提供方。

它对 MCP Client 暴露能力。

常见能力包括：

```text
Tools
Resources
Prompts
```

Server 可以是本地进程，也可以是远程服务。

本地进程例子：

```text
本地文件系统 MCP Server
本地项目文档 MCP Server
本地 SQLite 查询 MCP Server
```

远程服务例子：

```text
公司订单 MCP Server
公司工单 MCP Server
GitHub MCP Server
Sentry MCP Server
知识库 MCP Server
```

Server 的重点是：

```text
职责要聚焦。
边界要清晰。
不要什么都塞进一个 Server。
```

比如不建议做成：

```text
company-all-in-one-mcp-server
```

里面同时放：

```text
订单
工单
退款
人事
财务
代码仓库
生产数据库
```

这会带来：

```text
权限难管。
故障影响面大。
工具命名混乱。
测试复杂。
审计困难。
```

更好的方式是按边界拆：

```text
order-mcp-server
ticket-mcp-server
docs-mcp-server
github-mcp-server
```

当然真实公司里怎么拆还要看团队、权限和部署方式。

但学习阶段你先记住：

```text
MCP Server 应该是专注、可组合、边界清晰的能力提供方。
```

### 5. 为什么一个 Host 可以连接多个 Server

AI 应用经常需要多个外部能力。

比如一个客服 Agent 可能要：

```text
查订单。
查物流。
查退款规则文档。
创建工单。
读取客服回复模板。
查询历史工单。
```

这些能力不一定属于同一个系统。

如果 MCP Host 只能连接一个 Server，那就会被迫把所有能力塞进一个 Server。

这不符合真实工程边界。

所以 MCP 架构允许：

```text
一个 Host 管理多个 Client。
每个 Client 连接一个 Server。
不同 Server 提供不同能力。
```

图示：

```text
客服 AI Host
  |
  |-- Order Client --> Order MCP Server
  |       - query_order
  |       - query_logistics
  |
  |-- Ticket Client --> Ticket MCP Server
  |       - create_ticket
  |       - query_ticket
  |
  |-- Docs Client --> Docs MCP Server
          - refund policy resource
          - return policy resource
          - customer reply prompt
```

这样做的好处：

```text
能力可以按业务域拆分。
权限可以按 Server 控制。
某个 Server 出问题不会影响所有能力。
团队可以独立维护自己的 Server。
Host 可以按用户场景选择启用哪些 Server。
```

这就是 MCP 的可组合性。

### 6. 为什么一个 Client 通常只连接一个 Server

官方架构里，一个 Host 会为每个 Server 创建一个 Client。

也就是说：

```text
Client 和 Server 通常是一对一关系。
```

这不是多余设计。

它有几个好处。

#### 好处 1：连接状态清楚

每个 Client 只维护一个 Server 的连接状态。

```text
初始化是否完成？
Server 支持哪些能力？
Server 是否还在线？
Server 有没有发通知？
```

这些状态不会和其他 Server 混在一起。

#### 好处 2：能力协商清楚

不同 Server 支持的能力不同。

比如：

```text
Order Server 支持 tools。
Docs Server 支持 resources。
Prompt Server 支持 prompts。
```

每个 Client 只记住自己对应 Server 的能力。

#### 好处 3：安全边界清楚

如果一个 Server 只应该看到订单相关信息，那它不应该顺便看到文档 Server、GitHub Server 的上下文。

Client 和 Server 一对一，有利于隔离：

```text
连接隔离
能力隔离
上下文隔离
权限隔离
错误隔离
```

#### 好处 4：故障处理清楚

如果 Docs Server 掉线，不应该影响 Order Server。

Host 可以知道：

```text
哪个 Client 失败。
哪个 Server 不可用。
哪些能力暂时不能暴露给模型。
```

所以一对一关系不是形式主义，而是为了让边界可控。

### 7. Tools、Resources、Prompts 在架构里属于谁

在 MCP 中，Tools、Resources、Prompts 通常是 Server 暴露给 Client 的能力。

```text
MCP Server
  |
  |-- Tools
  |-- Resources
  |-- Prompts
```

三者区别：

| 类型 | 作用 | 例子 |
| --- | --- | --- |
| Tools | 可执行动作，通常会调用外部系统或计算 | `query_order`、`create_ticket`、`search_logs` |
| Resources | 可读取上下文数据 | API 契约、数据库 schema、业务规则文档、项目文件 |
| Prompts | 可复用提示词模板或工作流模板 | 客服回答模板、工单总结模板、代码审查模板 |

放到我们项目里：

```text
query_order 更像 Tool。
create_ticket 更像 Tool。
docs/java-ai-api-contract.md 更像 Resource。
notes/stage8-xx.md 更像 Resource。
客服回答格式要求更像 Prompt。
工单总结模板更像 Prompt。
```

这里要避免一个误区：

```text
不是所有外部能力都应该做成 Tool。
```

如果只是读资料，通常更像 Resource。

如果是让模型或 Agent 执行业务动作，才更像 Tool。

如果是给用户或模型复用的一套提示词结构，更像 Prompt。

### 8. Data layer 和 Transport layer

MCP 官方架构里还会讲两层：

```text
Data layer
Transport layer
```

这两个词不用背得很复杂。

先这样理解：

```text
Data layer 负责“消息长什么样、表达什么含义”。
Transport layer 负责“消息通过什么通道传过去”。
```

#### Data layer

Data layer 包括：

```text
JSON-RPC 消息格式
请求和响应
通知
生命周期
能力协商
tools/list
tools/call
resources/read
prompts/get
错误信息
进度信息
```

比如：

```text
Client 要列出工具。
Client 要调用工具。
Server 返回工具结果。
Server 通知工具列表变了。
```

这些都是 data layer 关注的。

它关心“说什么”。

#### Transport layer

Transport layer 包括：

```text
stdio
Streamable HTTP
连接建立
消息传输
消息 framing
HTTP 场景下的授权
```

它关心“怎么传”。

类比一下：

```text
Data layer 像快递包裹里的内容和单据格式。
Transport layer 像快递走陆运、空运还是同城配送。
```

同一套 data layer 消息，可以跑在不同 transport 上。

后续我们会单独学：

```text
第 4 节：MCP 通信基础，重点讲 JSON-RPC。
第 5 节：MCP 生命周期。
第 6 节：MCP Transport。
```

本节先建立架构地图。

### 9. 能力协商在架构里的位置

MCP Client 连接 MCP Server 后，不是直接乱调。

它们需要知道彼此支持什么能力。

这叫能力协商。

你可以理解成：

```text
Client：我支持哪些客户端能力。
Server：我支持哪些服务端能力。
双方初始化时交换这些信息。
后面只能按已经声明的能力来使用。
```

比如某个 Server 可能支持：

```text
tools
resources
```

但不支持：

```text
prompts
```

那 Host 就不应该指望从它那里获取 prompt 模板。

能力协商的价值：

```text
让 Host 知道这个 Server 能提供什么。
让 Client 不要调用 Server 不支持的功能。
让 Server 和 Client 可以逐步扩展。
让协议具备兼容性。
```

放到项目里，未来可能是：

```text
Order MCP Server 声明支持 tools。
Docs MCP Server 声明支持 resources。
Prompt MCP Server 声明支持 prompts。
```

Host 启动时就能形成一张能力表：

| Server | Tools | Resources | Prompts |
| --- | --- | --- | --- |
| Order MCP Server | 是 | 否 | 否 |
| Docs MCP Server | 否 | 是 | 否 |
| Customer Prompt MCP Server | 否 | 否 | 是 |

这张表会影响 Host 后续如何给模型组织工具和上下文。

### 10. Host 为什么是安全边界核心

MCP Server 可以提供很强的能力。

比如：

```text
读取文件。
查询数据库。
调用订单接口。
创建工单。
访问 GitHub。
```

这些能力如果不控制，风险很高。

所以 Host 必须承担安全边界职责。

Host 需要决定：

```text
哪些 Server 可以连接。
哪些 Tools 可以暴露给模型。
哪些 Resources 可以读。
哪些 Prompts 可以用。
用户是否授权。
写操作是否需要确认。
工具结果是否需要脱敏。
Server 是否只能获得必要上下文。
```

一个非常重要的原则：

```text
MCP Server 不应该默认看到完整对话。
```

Server 只应该拿到执行当前任务所需的最小信息。

比如订单查询 Server 只需要：

```text
order_id
user_id
tenant_id
trace_id
必要的调用来源信息
```

不需要看到：

```text
用户整段聊天历史
其他 Server 的工具结果
系统 prompt 全文
内部权限策略细节
其他订单信息
```

这和我们之前学习的安全边界是一致的：

```text
模型不能直接操作业务系统。
工具调用必须校验。
写操作必须确认。
敏感字段不能随便交给模型。
```

MCP 只是多了一层标准协议，不代表安全问题自动消失。

### 11. 本地 Server 和远程 Server

MCP Server 可以本地运行，也可以远程运行。

本地 Server：

```text
运行在用户机器上。
常见 transport 是 stdio。
适合文件系统、项目代码、个人本地工具。
```

远程 Server：

```text
运行在远程平台或公司服务器上。
常见 transport 是 Streamable HTTP。
适合公司业务系统、云服务、团队共享能力。
```

举例：

```text
本地项目文档 MCP Server：读取 D:/wendang/java+python+ai/docs 下的资料。
远程订单 MCP Server：连接公司订单业务系统。
远程 GitHub MCP Server：访问仓库、issue、PR。
```

选择本地还是远程，要看：

```text
数据在哪里。
权限怎么管。
是否需要多人共享。
是否需要稳定部署。
是否需要访问本机文件。
```

对我们当前学习路线来说，后续更适合先从本地 Python MCP Server 学起。

原因：

```text
部署简单。
容易调试。
不需要先处理复杂认证。
能快速理解协议结构。
```

等概念扎实后，再考虑远程 HTTP 方式。

### 12. MCP 架构和 Tool Calling 的关系

第 2 节已经讲过区别。

这里从架构角度再放一次：

```text
模型
  |
  | Tool Calling
  v
Host
  |
  | MCP Client
  v
MCP Server
  |
  v
外部系统
```

Tool Calling 发生在：

```text
模型 <-> Host
```

MCP 发生在：

```text
Host / MCP Client <-> MCP Server
```

所以一次完整调用可能是：

```text
1. Host 连接 Order MCP Server。
2. Client 获取 tools/list。
3. Host 把 MCP Tool 转成模型 tools schema。
4. 用户问订单问题。
5. 模型通过 Tool Calling 返回 query_order 调用意图。
6. Host 校验工具名、参数、权限。
7. Host 通过 MCP Client 调用 Order MCP Server。
8. Server 执行 query_order。
9. Host 把结果交回模型。
10. 模型生成中文回答。
```

这里最容易犯错的理解是：

```text
模型直接调用 MCP Server。
```

更准确的理解是：

```text
模型向 Host 表达工具调用意图。
Host 决定是否通过 MCP Client 调用 MCP Server。
```

Host 仍然是主控。

### 13. MCP 架构和 LangGraph 的关系

LangGraph 负责流程编排。

比如：

```text
识别意图
查知识库
查订单
缺字段追问
用户确认
创建工单
最终回答
```

MCP 负责外部能力接入。

比如：

```text
连接订单 MCP Server。
连接文档 MCP Server。
连接工单 MCP Server。
```

未来可以这样组合：

```text
LangGraph workflow
  |
  |-- rag_node
  |     -> 读取向量库或 MCP Resource
  |
  |-- query_order_node
  |     -> 通过 MCP Client 调 Order MCP Server 的 query_order
  |
  |-- create_ticket_node
        -> 通过 MCP Client 调 Ticket MCP Server 的 create_ticket
```

所以：

```text
LangGraph 管流程。
MCP 管连接。
Tool Calling 管模型选择工具。
Java business service 管真实业务。
```

这四个不要混。

### 14. MCP 架构和 RAG 的关系

RAG 负责：

```text
文档切分。
embedding。
向量检索。
召回上下文。
让模型基于上下文回答。
```

MCP Resource 负责：

```text
把外部资源标准暴露给 Host。
```

它们可以组合：

```text
Docs MCP Server 暴露项目文档 Resource
  |
  v
Host 读取资源
  |
  v
RAG 入库或临时检索
  |
  v
模型回答
```

也可以是：

```text
RAG Service 被包装成 MCP Tool
  |
  v
search_knowledge_base(query)
```

但要注意：

```text
MCP Resource 不等于 RAG。
RAG 也不一定必须通过 MCP。
```

MCP 是连接协议。

RAG 是知识检索方法。

### 15. MCP 架构和 Java business service 的关系

我们当前已经有真实 Java business service。

它负责：

```text
订单查询。
工单创建。
MyBatis。
MySQL。
Redis。
权限。
幂等。
错误码。
trace_id。
契约测试。
```

MCP Server 不应该替代 Java business service。

更合理的结构是：

```text
AI Host / ai-service
  |
  v
MCP Client
  |
  v
Order MCP Server
  |
  v
JavaOrderClient
  |
  v
Java business service
  |
  v
MySQL / Redis
```

也就是说：

```text
MCP Server 是 AI 接入层的标准外壳。
Java business service 是业务事实来源。
```

不要让 MCP Server 直接绕过 Java 服务去读写数据库。

否则会破坏：

```text
Java 侧权限。
事务。
幂等。
错误码。
审计。
trace_id。
业务封装。
```

这也是我们之前阶段 7 的价值：

```text
先把传统业务服务边界打牢，再让 AI 工具安全接入它。
```

### 16. 把当前项目映射成 MCP 架构

当前项目还没有真正实现 MCP Server。

但可以先做架构映射。

| 当前项目部分 | 在 MCP 架构里的可能角色 | 说明 |
| --- | --- | --- |
| `projects/ai-service` | Host | AI 应用主控，负责模型、Agent、RAG、权限和工具策略 |
| LangGraph workflow | Host 内部的流程编排 | 决定节点怎么流转，不是 MCP Server |
| `tool_registry.py` | Host 内部工具适配层，或未来 MCP Server 的工具来源 | 现在是本地工具注册表，未来可能被 MCP 包装 |
| `JavaOrderClient` | MCP Tool 下游业务 client | 负责调用 Java order API |
| `JavaTicketClient` | MCP Tool 下游业务 client | 负责调用 Java ticket API |
| `projects/java-business-service` | 外部业务服务 | 真实业务规则和数据来源 |
| `docs/java-ai-api-contract.md` | Resource 候选 | 可以通过 MCP Resource 暴露 |
| 学习笔记 `notes/` | Resource 候选 | 可以作为项目知识上下文暴露 |
| 客服回复模板 | Prompt 候选 | 可以通过 MCP Prompt 暴露 |

未来第一版 MCP 架构可能是：

```text
ai-service 作为 Host
  |
  |-- MCP Client --> business-tools-mcp-server
  |       |-- Tool: query_order
  |       |-- Tool: create_ticket
  |
  |-- MCP Client --> project-docs-mcp-server
          |-- Resource: java-ai-api-contract.md
          |-- Resource: learning-progress.md
          |-- Resource: stage notes
```

更成熟一点可以拆成：

```text
ai-service Host
  |
  |-- order-mcp-server
  |-- ticket-mcp-server
  |-- docs-mcp-server
  |-- prompt-template-mcp-server
```

学习阶段不用一上来拆太细。

我们会先做简单版，保证你能看懂、能运行、能解释。

### 17. 架构设计中的三个边界

MCP 架构最值得学的是边界。

#### 边界 1：Host 和模型的边界

模型可以：

```text
理解用户问题。
选择工具。
生成参数。
总结工具结果。
```

模型不应该：

```text
直接决定越权调用。
直接看到所有敏感字段。
直接绕过确认做写操作。
直接访问数据库。
```

这些由 Host 控制。

#### 边界 2：Host 和 Server 的边界

Host 可以：

```text
连接 Server。
发现 Server 能力。
调用 Server 工具。
读取 Server 资源。
获取 Server prompt。
```

Server 不应该：

```text
默认拿到完整对话。
看到其他 Server 的上下文。
绕过 Host 做用户授权。
决定最终给用户怎么回答。
```

Server 专注提供能力。

Host 专注协调和安全。

#### 边界 3：MCP Server 和业务服务的边界

MCP Server 可以：

```text
把业务能力包装成 MCP Tool。
把业务文档包装成 Resource。
把业务 prompt 包装成 Prompt。
```

MCP Server 不应该：

```text
重写完整业务系统。
绕过已有 Java API。
绕过数据库事务和权限。
把内部错误原样暴露给模型。
```

业务事实仍然来自 Java business service。

### 18. 常见架构误区

#### 误区 1：Host 就是模型

不对。

模型只是 Host 使用的一个能力。

Host 还要管：

```text
用户输入
上下文
工具列表
MCP Client
权限
确认
最终响应
```

#### 误区 2：Client 是用户安装的客户端软件

不准确。

MCP Client 是 Host 里面连接 MCP Server 的组件。

用户看到的桌面软件或 Web 页面更接近 Host 的外壳。

#### 误区 3：Server 就是业务后端

不一定。

MCP Server 是 AI 接入层的能力提供方。

它可以调用业务后端，但不等于业务后端。

#### 误区 4：一个 Server 放所有工具最方便

短期看方便，长期会混乱。

问题包括：

```text
权限难拆。
测试难写。
故障影响面大。
工具命名冲突。
维护责任不清。
```

#### 误区 5：MCP 有协议，就自动安全

不对。

协议只提供连接方式。

安全仍然要靠：

```text
Host 策略。
用户授权。
工具白名单。
参数校验。
字段脱敏。
写操作确认。
下游业务权限。
审计日志。
```

### 19. 本节主题的项目级理解

如果把本节放回我们的长期学习项目，你应该这样理解：

```text
阶段 3 学的是模型怎么通过 Tool Calling 请求工具。
阶段 4 学的是知识怎么通过 RAG 进入模型上下文。
阶段 5 学的是 LangGraph 怎么编排多步骤 Agent。
阶段 7 学的是 Java business service 怎么成为安全可靠的真实业务后端。
阶段 8 学的是这些外部能力未来怎么用 MCP 标准化接入。
```

MCP 不是推翻前面的东西。

MCP 是把前面的能力接入方式标准化。

你可以把现在项目看成：

```text
已经有业务能力。
已经有 Agent 流程。
已经有 RAG。
已经有工具调用安全边界。
```

MCP 要做的是：

```text
把这些能力整理成 Host 可以标准发现和调用的 Tools、Resources、Prompts。
```

这就是阶段 8 的意义。

### 20. 面试表达：怎么讲 MCP 架构

如果别人问：

```text
MCP 的架构是什么？
```

不要只说：

```text
MCP 有 Host、Client、Server。
```

这句话太浅。

更好的回答：

```text
MCP 是一种 Host-Client-Server 架构。
Host 是 AI 应用本体，负责模型调用、用户授权、上下文管理和多个 Client 的管理。
Client 是 Host 内部的连接组件，通常一个 Client 对应一个 MCP Server，负责连接、初始化、能力协商和协议消息转发。
Server 是外部能力提供方，负责暴露 Tools、Resources、Prompts 等能力。
```

再补一句工程化理解：

```text
这种设计让 AI 应用可以连接多个职责清晰的外部能力服务，同时让每个 Server 只拿到必要上下文，安全边界由 Host 控制。
```

结合我们的项目可以说：

```text
在我们的项目里，ai-service 未来可以作为 Host，订单查询和创建工单可以封装成 MCP Tools，项目文档和 API 契约可以封装成 Resources，客服回复模板可以封装成 Prompts。MCP Server 内部仍然要调用 Java business service，不能绕过 Java 侧权限、幂等、错误码和 trace_id 边界。
```

这样讲，别人能听出来你不是只背了概念。

你能把 MCP 放到真实项目架构里。

## 本节结论

本节最重要的结论：

```text
MCP 的核心架构是 Host、Client、Server。
Host 是 AI 应用主控。
Client 是 Host 内部连接某个 Server 的组件。
Server 是外部能力提供方。
一个 Host 可以管理多个 Client。
一个 Client 通常连接一个 Server。
Server 通过 MCP 暴露 Tools、Resources、Prompts。
Host 负责模型、上下文、安全策略、用户确认和多 Server 能力整合。
```

放到项目里：

```text
ai-service 未来更像 Host。
MCP Client 是 ai-service 里连接外部 MCP Server 的组件。
MCP Server 可以包装 query_order、create_ticket、项目文档和 prompt 模板。
Java business service 仍然是真实业务系统，不被 MCP 替代。
LangGraph 仍然负责 Agent 流程编排。
Tool Calling 仍然负责模型选择工具。
```

## 本节练习

### 练习 1：用一句话说明 Host、Client、Server 的关系

参考答案：

```text
Host 是 AI 应用本体，它创建并管理多个 Client；每个 Client 负责连接一个 MCP Server；Server 负责暴露 Tools、Resources、Prompts 等外部能力。
```

### 练习 2：为什么 MCP 里 Host 和 Client 不是同一个概念？

参考答案：

```text
Host 是整个 AI 应用，负责模型调用、用户上下文、安全策略和多个 Server 能力整合。
Client 是 Host 内部的连接组件，只负责维护某一个 MCP Server 的连接、能力协商和协议通信。
它们层级不同，职责不同。
```

### 练习 3：为什么一个 Host 可以连接多个 Server？

参考答案：

```text
因为真实 AI 应用通常需要多个外部能力，例如订单、工单、文档、GitHub、知识库和 prompt 模板。
让一个 Host 通过多个 Client 连接多个 Server，可以让不同能力按业务边界拆分，方便权限控制、独立维护和组合使用。
```

### 练习 4：为什么每个 Client 通常只连接一个 Server？

参考答案：

```text
这样可以让连接状态、能力协商、安全边界和故障处理更清晰。
如果一个 Client 混连多个 Server，就会增加状态管理和权限隔离复杂度。
```

### 练习 5：把我们项目里的这些东西映射到 MCP 架构

题目：

```text
ai-service
Java business service
query_order
docs/java-ai-api-contract.md
客服回复模板
```

参考答案：

```text
ai-service 未来可以作为 MCP Host。
Java business service 是真实业务服务，不是 MCP Host。
query_order 可以封装成 MCP Tool。
docs/java-ai-api-contract.md 可以封装成 MCP Resource。
客服回复模板可以封装成 MCP Prompt。
```

### 练习 6：MCP Server 能不能直接替代 Java business service？

参考答案：

```text
不应该。
MCP Server 是 AI 接入层的标准能力外壳，可以调用 Java business service。
Java business service 负责真实业务规则、权限、事务、MySQL、Redis、幂等、错误码和 trace_id。
如果 MCP Server 绕过 Java business service，会破坏原来的业务边界。
```

### 练习 7：Data layer 和 Transport layer 有什么区别？

参考答案：

```text
Data layer 负责 MCP 消息表达什么含义，例如 JSON-RPC 请求、响应、通知、tools/list、tools/call、resources/read、生命周期和能力协商。
Transport layer 负责这些消息通过什么通道传输，例如 stdio 或 Streamable HTTP。
简单说，Data layer 管“说什么”，Transport layer 管“怎么传”。
```

## 自测题

### 自测 1：模型是不是 MCP Host？

参考答案：

```text
不是。
模型只是 Host 调用的能力之一。
Host 是完整 AI 应用，除了调用模型，还要管理用户上下文、MCP Client、安全策略、工具结果和最终响应。
```

### 自测 2：MCP Client 是不是用户打开的软件界面？

参考答案：

```text
不是。
MCP Client 是 Host 内部连接某个 MCP Server 的组件。
用户打开的软件界面更接近 Host 的外壳或入口。
```

### 自测 3：MCP Server 暴露的三类核心能力是什么？

参考答案：

```text
Tools、Resources、Prompts。
Tools 是可执行能力。
Resources 是可读取上下文数据。
Prompts 是可复用提示词或工作流模板。
```

### 自测 4：为什么说 Host 是安全边界核心？

参考答案：

```text
因为 Host 控制哪些 Server 可以连接、哪些工具暴露给模型、哪些资源可以读、写操作是否需要用户确认、工具结果是否脱敏，以及 Server 能拿到多少上下文。
MCP Server 不应该默认看到完整对话，也不应该绕过 Host 做授权决策。
```

### 自测 5：如果未来我们做一个 `business-tools-mcp-server`，里面放 `query_order` 和 `create_ticket`，它内部应该直接查 MySQL 吗？

参考答案：

```text
不应该。
它应该复用 JavaOrderClient / JavaTicketClient 去调用 Java business service。
MySQL、Redis、权限、事务、幂等和错误码仍然应该由 Java business service 管理。
```

### 自测 6：LangGraph 在 MCP 架构中是什么角色？

参考答案：

```text
LangGraph 不是 MCP 的 Host、Client 或 Server。
它更像 Host 内部的 Agent 流程编排层。
LangGraph 节点可以通过 MCP Client 调用 MCP Server 暴露的工具或读取资源。
```

### 自测 7：为什么 Server 职责要聚焦？

参考答案：

```text
职责聚焦可以让权限、测试、部署、故障隔离和维护责任更清晰。
如果一个 Server 放入订单、工单、财务、人事、代码仓库等所有能力，会导致权限混乱、影响面过大、工具命名冲突和审计困难。
```

## 本节总结

这一节你要真正记住的是：

```text
MCP 不是只有一个 Server，也不是模型直接调工具。
MCP 是 Host 管理多个 Client，每个 Client 连接一个 Server，Server 暴露 Tools、Resources、Prompts。
Host 是主控方，负责模型、上下文、用户授权、安全策略和多 Server 能力整合。
Server 是能力提供方，应该职责聚焦，不能默认看到完整对话，也不能绕过业务服务边界。
```

阶段 8 后续写代码时，我们会不断回到这张图：

```text
ai-service Host
  |
  |-- MCP Client --> business-tools-mcp-server
  |       |-- query_order
  |       |-- create_ticket
  |
  |-- MCP Client --> project-docs-mcp-server
          |-- docs
          |-- notes
          |-- API contract
```

下一节学习：

```text
阶段 8 第 4 节：MCP 通信基础
```
