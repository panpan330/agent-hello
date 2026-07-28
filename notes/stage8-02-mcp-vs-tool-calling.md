# 阶段 8 第 2 节：MCP 和 Tool Calling 的区别

## 本节定位

本节是阶段 8 第 2 节。

第 1 节我们已经知道：

```text
MCP 是 AI 应用连接外部系统的开放协议。
MCP 里的核心参与者是 Host、Client、Server。
MCP Server 可以暴露 Tools、Resources、Prompts。
```

这一节专门解决一个很容易混淆的问题：

```text
MCP 和 Tool Calling 到底是不是一回事？
```

结论先放出来：

```text
不是一回事。
```

但它们关系很近。

最简短的区别是：

```text
Tool Calling 解决“模型如何请求调用工具”。
MCP 解决“AI 应用如何标准连接外部工具、资源和 prompt”。
```

如果只记这一句话，还不够。

因为真正开发时你还要知道：

```text
MCP Server 暴露的 tool 怎么变成模型能用的 tool？
我们已有的 tool_registry 和 MCP 是什么关系？
MCP 会不会替代 JavaOrderClient？
MCP 会不会替代 LangGraph？
什么时候只用 Tool Calling 就够？
什么时候值得引入 MCP？
```

本节就把这些讲清楚。

## 本节学习目标

学完本节后，你应该能说明：

```text
Tool Calling 的职责边界。
MCP 的职责边界。
MCP Tool 和模型 Tool Calling tool 的区别。
MCP Server 暴露的 Tool 如何被 Host 转成模型可调用工具。
MCP 和当前项目 tool_registry、JavaOrderClient、LangGraph Agent 的关系。
什么时候只用 Tool Calling 就够。
什么时候引入 MCP 更合适。
```

## 本节不做什么

本节是纯知识点章节。

不做：

```text
不写代码。
不启动服务。
不打开虚拟机。
不生成手动验证清单。
不跑业务测试。
不做敏感扫描。
```

本节只做：

```text
概念对比
项目映射
笔记沉淀
练习和自测
```

## 官方资料依据

本节参考：

| 资料 | 用途 |
| --- | --- |
| [MCP Introduction](https://modelcontextprotocol.io/docs/getting-started/intro) | MCP 是连接 AI 应用与外部系统的开放标准 |
| [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture) | MCP Host / Client / Server 与 Tools / Resources / Prompts |
| [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25) | MCP 使用 JSON-RPC，定义 Host、Client、Server 和能力 |
| [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | MCP Server 暴露可由语言模型调用的工具 |
| [OpenAI Function Calling](https://developers.openai.com/api/docs/guides/function-calling) | Function calling / tool calling 让模型连接应用提供的数据和动作 |
| [OpenAI Tools](https://developers.openai.com/api/docs/guides/tools) | OpenAI 工具入口，包括 function calling 和远程 MCP servers |

说明：

```text
不同模型平台对 tool calling 的接口名字和返回格式可能不同。
本节讲通用职责边界，不绑定某一个平台的具体参数名。
```

## 基础知识铺垫

### 1. 为什么 MCP 和 Tool Calling 容易混淆

MCP 和 Tool Calling 容易混淆，不是因为它们真的一样，而是因为它们经常出现在同一条链路里。

比如一次“查订单”的 AI 调用里，你可能同时看到：

```text
模型 tools 参数
模型返回 tool_call
工具名 query_order
工具参数 order_id
MCP Server 暴露 tools/list
MCP Client 调 tools/call
```

这些词里反复出现 tool，就很容易让人误以为：

```text
只要叫 tool，就是同一个东西。
```

但真正要分清的是：

```text
Tool Calling 里的 tool，是给模型看的工具描述。
MCP 里的 Tool，是 MCP Server 对外暴露的能力。
```

再说得更直白一点：

```text
Tool Calling 关心“模型想不想用工具”。
MCP 关心“工具从哪里来、怎么被标准发现、怎么被标准调用”。
```

它们像是一条链路里的两个环节。

```text
MCP Server 提供工具能力。
Host 把这些工具能力整理成模型能理解的 tools。
模型通过 Tool Calling 选择其中一个工具。
Host 再回到 MCP Server 执行这个工具。
```

所以二者不是替代关系，更像上下游关系：

```text
MCP 可以给 Tool Calling 提供工具来源。
Tool Calling 可以让模型使用 MCP 暴露的工具。
```

你学习时可以先抓住三个关键词：

| 关键词 | 对应问题 | 更接近哪一边 |
| --- | --- | --- |
| 选择 | 模型要不要调用某个工具 | Tool Calling |
| 发现 | Host 怎么知道有哪些外部工具 | MCP |
| 执行 | Host 怎么调用外部 Server 上的工具 | MCP + 应用后端 |

这三个词很重要。

如果问题是：

```text
模型为什么选择 query_order 而不是 create_ticket？
```

这主要是 Tool Calling 的问题。

如果问题是：

```text
query_order 这个工具从哪里发现、由哪个 Server 提供、怎么标准调用？
```

这主要是 MCP 的问题。

### 2. 先回忆我们已经做过的 Tool Calling

阶段 3、阶段 5、阶段 6 都围绕 Tool Calling 做过很多内容。

比如订单查询：

```text
用户：帮我查一下 A1001 订单物流
模型或规则判断：需要 query_order
后端校验工具名和参数
后端调用 Java mock 或 Java business service
工具结果返回
模型根据工具结果生成中文回答
```

这条链路里最关键的点是：

```text
模型不直接查数据库。
模型只提出工具调用请求。
真正执行工具的是应用后端。
```

这就是 Tool Calling 的基础思想。

你可以把它理解为：

```text
给模型一份工具菜单。
模型根据用户问题选择要不要点某个工具。
应用后端决定能不能执行、怎么执行、结果怎么返回。
```

### 3. Tool Calling 具体解决什么问题

大模型本身只有训练时学到的知识和当前上下文。

它不知道：

```text
用户 A1001 订单现在到哪了。
数据库里有没有这个工单。
退款接口今天是否返回成功。
公司内部 API 契约是什么。
```

Tool Calling 让模型可以“请求”应用提供的外部能力。

典型工具包括：

```text
查订单
查物流
创建工单
查询知识库
计算价格
调用内部 API
查数据库
发邮件
```

但要注意：

```text
Tool Calling 不是模型执行代码。
Tool Calling 是模型输出结构化工具调用意图。
应用层执行真正的函数、API、数据库查询或业务动作。
```

这个边界非常重要。

错误理解：

```text
模型会调用我的 Python 函数。
```

更准确的理解：

```text
模型输出“我想调用某个函数，参数是什么”。
你的应用收到这个请求后，自己决定是否执行。
```

### 4. Tool Calling 里的“工具定义”通常长什么样

不同平台格式不同，但核心信息类似：

```text
工具名
工具描述
参数 JSON schema
参数必填项
参数类型
```

例如概念上可以是：

```json
{
  "name": "query_order",
  "description": "查询当前用户有权查看的订单摘要",
  "parameters": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "订单号"
      }
    },
    "required": ["order_id"]
  }
}
```

模型看到这个工具定义后，可能输出：

```json
{
  "tool_name": "query_order",
  "arguments": {
    "order_id": "A1001"
  }
}
```

应用收到后继续做：

```text
工具名是否注册？
参数是否合法？
当前用户是否有权限？
是否需要确认？
是否需要幂等键？
执行失败怎么处理？
结果是否符合 schema？
```

这些我们之前都学过。

### 5. MCP 又是从哪里来的

Tool Calling 可以让模型请求工具。

但它没有完全解决：

```text
工具从哪里来？
不同 AI 应用如何发现工具？
不同工具服务如何统一暴露能力？
资源和 prompt 怎么暴露？
一个 Host 连接多个外部系统时怎么管理？
工具服务如何被不同客户端复用？
```

比如你有：

```text
ChatGPT
Claude Desktop
IDE Agent
公司内部客服 Agent
公司运营数据助手
```

又有：

```text
GitHub 工具
文件系统工具
数据库工具
订单系统工具
知识库资源
工单 prompt 模板
```

如果每个 AI 应用都自己写自己的工具接入方式，就会重复。

MCP 想解决的是：

```text
用统一协议把 AI 应用和外部能力连接起来。
```

所以 MCP 的视角比单次模型 tool call 更大。

### 6. MCP 里的 Tool 和 Tool Calling 里的 Tool 名字一样，但层级不同

这是最容易混的地方。

两边都叫 Tool。

但它们不是完全同一层东西。

| 名称 | 所在层级 | 含义 |
| --- | --- | --- |
| Tool Calling 里的 tool | 模型交互层 | 传给模型看的工具定义，模型可能输出 tool call |
| MCP Tool | 协议接入层 | MCP Server 暴露给 MCP Client 的可执行能力 |

可以这样理解：

```text
MCP Tool 是外部工具能力的来源。
Tool Calling tool 是模型上下文里的工具描述。
```

它们之间可能需要转换。

例如：

```text
MCP Server 暴露 query_order tool
-> MCP Client tools/list 拿到 tool 信息
-> Host 把它转换成模型 API 可接受的 tools schema
-> 模型输出 tool_call
-> Host 通过 MCP Client 调用 MCP Server 的 query_order
```

所以：

```text
MCP Tool 可以成为 Tool Calling tool 的上游来源。
```

## 本节主题系统讲解

### 1. 一句话区别

先用一句话区分：

```text
Tool Calling 是模型如何选择和请求工具。
MCP 是 AI 应用如何发现和连接工具、资源、prompt。
```

再用项目语言说：

```text
Tool Calling 发生在模型和应用之间。
MCP 发生在应用和外部能力服务之间。
```

更具体：

```text
Tool Calling 关心：模型要不要调用 query_order，参数是什么。
MCP 关心：query_order 这个工具从哪个 Server 来，怎么发现，怎么调用，Server 还暴露哪些资源和 prompt。
```

### 2. 位置不同：一个靠近模型，一个靠近工具生态

Tool Calling 更靠近模型。

它的问题是：

```text
怎么把工具告诉模型？
模型怎么选择工具？
模型怎么输出工具参数？
工具结果怎么交回模型？
```

MCP 更靠近工具生态。

它的问题是：

```text
外部能力怎么标准暴露？
AI 应用怎么连接多个外部 Server？
如何列出 tools/resources/prompts？
如何调用 Server 上的工具？
如何读取 Server 上的资源？
```

一张图：

```text
用户
  |
  v
模型
  |
  | Tool Calling：模型请求调用工具
  v
AI Host / 应用后端
  |
  | MCP：应用连接外部工具服务
  v
MCP Client
  |
  v
MCP Server
  |
  v
外部系统 / 业务服务 / 文件 / 数据库
```

所以：

```text
Tool Calling 是模型能力使用方式。
MCP 是工具能力供应方式。
```

### 3. 三层模型：模型交互层 / AI 应用层 / 外部能力层

要真正理解 MCP 和 Tool Calling，最好不要只看一个词，而是把一次 AI 应用调用拆成三层。

```text
第一层：模型交互层
第二层：AI 应用层
第三层：外部能力层
```

#### 第一层：模型交互层

这一层主要处理：

```text
messages
system prompt
tools schema
tool_choice
模型输出 tool_call
模型读取 tool result 后生成最终回答
```

这一层最核心的问题是：

```text
模型应该怎么理解用户问题？
模型是否需要工具？
模型应该选择哪个工具？
模型应该生成什么参数？
工具结果回来后，模型应该怎么组织答案？
```

这就是 Tool Calling 最主要的位置。

你可以把它理解成：

```text
Tool Calling 是模型交互层的能力。
```

#### 第二层：AI 应用层

这一层是我们自己写的后端应用。

比如当前项目里的：

```text
ai-service
LangGraph workflow
tool_registry
JavaOrderClient
JavaTicketClient
RAG service
权限判断
trace_id
错误处理
日志
```

这一层最核心的问题是：

```text
模型说要调用工具，我信不信？
工具名是否合法？
参数是否合法？
用户有没有权限？
写操作是否需要确认？
要调哪个下游服务？
下游失败怎么兜底？
结果怎么过滤后再交给模型？
```

这层是安全边界和业务编排的核心。

非常重要的一点是：

```text
无论有没有 MCP，AI 应用层都不能消失。
```

因为模型不能直接替你承担：

```text
权限控制
幂等控制
错误映射
租户隔离
审计日志
业务契约校验
```

#### 第三层：外部能力层

这一层是 AI 应用要连接的真实能力来源。

可能包括：

```text
Java business service
MySQL
Redis
Qdrant / Milvus
文件系统
GitHub
内部知识库
公司订单系统
公司工单系统
```

MCP 主要站在 AI 应用层和外部能力层之间。

它关心：

```text
外部能力怎么暴露给 AI Host？
Host 怎么发现这些能力？
Host 怎么调用这些能力？
工具、资源、prompt 怎么用统一协议描述？
```

所以三层关系可以这样画：

```text
用户
  |
  v
模型交互层
  - messages
  - tools schema
  - tool_call
  - final answer
  重点：Tool Calling
  |
  v
AI 应用层
  - Host
  - Agent workflow
  - tool policy
  - permission
  - trace_id
  - error mapping
  重点：业务编排和安全边界
  |
  v
外部能力层
  - Java service
  - databases
  - documents
  - external tools
  重点：真实业务和数据来源
```

MCP 加进来后，大致变成：

```text
AI 应用层
  |
  v
MCP Client
  |
  v
MCP Server
  |
  v
外部能力层
```

你要记住：

```text
Tool Calling 不负责定义整个外部工具生态。
MCP 不负责替模型思考该选哪个工具。
AI 应用层负责把二者接起来，并且守住业务边界。
```

### 4. 7 个维度对比表

| 维度 | Tool Calling | MCP |
| --- | --- | --- |
| 解决的问题 | 模型如何请求使用工具 | AI 应用如何标准连接外部工具、资源、prompt |
| 主要发生位置 | 模型 API / 模型交互层 | Host / Client / Server 协议层 |
| 直接交互对象 | 应用和模型 | MCP Client 和 MCP Server |
| 工具来源 | 通常由应用手写或组装后传给模型 | 由 MCP Server 暴露，Host 可发现 |
| 典型动作 | 提供 tools schema、接收 tool_call、回传 tool result | tools/list、tools/call、resources/read、prompts/get |
| 是否包含 Resources/Prompts | 通常不包含，主要围绕工具调用 | 包含 Tools、Resources、Prompts 等能力 |
| 在项目里的角色 | 让模型选择 query_order / create_ticket | 让 query_order / create_ticket / 文档 / prompt 可以被标准接入 |

这个表要重点看“解决的问题”和“发生位置”。

只要这两个维度想清楚，后面就不容易乱。

```text
Tool Calling 是模型怎么用工具。
MCP 是工具怎么接入 AI 应用。
```

### 5. 解决范围不同

Tool Calling 主要覆盖：

```text
工具描述
工具选择
参数生成
工具调用请求
工具结果回传模型
```

MCP 覆盖：

```text
Host / Client / Server 架构
协议消息
能力协商
工具发现
工具调用
资源读取
prompt 获取
Transport
部分安全和授权框架
调试工具和 SDK 生态
```

所以 MCP 范围更大。

但范围大不代表一定替代 Tool Calling。

更准确是：

```text
MCP 可以给 Tool Calling 提供工具来源。
Tool Calling 可以让模型使用 MCP 暴露出来的工具。
```

### 6. 交互对象不同

Tool Calling 里，核心交互对象是：

```text
应用 <-> 模型
```

应用把工具定义传给模型，模型返回工具调用请求。

MCP 里，核心交互对象是：

```text
MCP Client <-> MCP Server
```

Client 通过协议向 Server 发：

```text
tools/list
tools/call
resources/list
resources/read
prompts/list
prompts/get
```

这说明：

```text
Tool Calling 是模型 API 层的事情。
MCP 是 client-server 协议层的事情。
```

### 7. 数据流对比

#### 只有 Tool Calling 的数据流

```text
用户问题
-> 应用构造 messages + tools
-> 模型选择工具并输出 tool_call
-> 应用执行本地函数或调用 HTTP API
-> 应用把工具结果交回模型
-> 模型生成最终回答
```

这里工具通常由应用自己维护。

比如我们当前项目：

```text
app/tools/tool_registry.py
app/services/java_order_client.py
app/services/java_ticket_client.py
```

#### 加入 MCP 后的数据流

```text
用户问题
-> Host 连接 MCP Server
-> MCP Client 获取 tools/list
-> Host 把 MCP tools 转成模型可用 tools
-> 模型选择工具并输出 tool_call
-> Host 通过 MCP Client 调 MCP Server tools/call
-> MCP Server 执行内部 adapter 或调用外部 API
-> 结果返回 Host
-> Host 把结果交回模型
-> 模型生成最终回答
```

这里工具由 MCP Server 暴露。

Host 不一定要自己写死每个工具。

### 8. 用我们项目的 `query_order` 对比

#### 当前 Tool Calling 方式

现在项目里的思路大致是：

```text
模型或规则判断需要 query_order
-> Python tool_registry 找到 query_order
-> Python 校验参数
-> Python JavaOrderClient 调 Java mock 或 Java business service
-> 返回工具结果
-> Agent 生成回答
```

它的特点：

```text
工具注册在 ai-service 代码里。
工具调用逻辑也在 ai-service 里。
只服务当前这个 AI 应用。
```

#### 未来 MCP 方式

未来可能变成：

```text
订单 MCP Server 暴露 query_order tool
-> Host 的 MCP Client 通过 tools/list 发现 query_order
-> Host 把 query_order 转成模型工具定义
-> 模型请求调用 query_order
-> Host 通过 MCP Client 发 tools/call
-> MCP Server 内部调用 JavaOrderClient
-> JavaOrderClient 调 Java business service
-> 返回结果
```

它的特点：

```text
query_order 不只属于某个 Agent。
任何支持 MCP 的 Host 都可以连接这个 Server 并发现它。
工具能力更标准，更容易复用。
```

### 9. MCP 会不会替代我们的 tool_registry

短期不会直接替代。

原因：

```text
tool_registry 是我们当前 ai-service 内部的工具注册和权限边界。
MCP 是外部能力接入协议。
```

未来可能有几种关系。

#### 关系 A：tool_registry 继续存在，MCP 暂不接入

适合：

```text
项目只有一个 AI 应用。
工具数量少。
工具都在 ai-service 内部。
不需要给外部 AI Host 复用。
```

#### 关系 B：MCP Server 包装现有 tool_registry

适合：

```text
我们希望把现有工具以 MCP 形式暴露出去。
```

可能结构：

```text
MCP Server tools/list
-> 从 tool_registry 读取工具定义

MCP Server tools/call
-> 调用 tool_registry 的执行逻辑
```

这种方式可以复用已有校验、权限和工具结果校验。

#### 关系 C：MCP 成为工具来源，tool_registry 做本地缓存/适配

适合：

```text
ai-service 作为 Host，连接多个外部 MCP Server。
```

可能结构：

```text
MCP Client 发现外部 tools
-> 转成 ai-service 内部工具描述
-> 给 LangGraph Agent 或模型使用
```

这种情况下，tool_registry 可能从“手写工具注册表”变成“统一工具适配层”。

### 10. MCP 会不会替代 JavaOrderClient

不会。

`JavaOrderClient` 的职责是：

```text
按 Java business API 契约发 HTTP 请求
带上 X-Trace-Id / X-User-Id / X-Tenant-Id / internal token
处理超时和错误
记录 upstream_trace_id
把 Java 响应映射成 Python 安全异常或工具结果
```

MCP 的职责是：

```text
把 query_order 这种能力标准暴露给 AI Host。
```

所以未来更可能是：

```text
MCP Tool: query_order
  -> 调用 JavaOrderClient
  -> JavaOrderClient 调 Java business service
```

也就是说：

```text
MCP Server 是上层入口。
JavaOrderClient 是下游业务 API client。
```

MCP 不应该绕过它。

否则阶段 7 做的：

```text
错误映射
契约校验
trace_id
header 传递
超时处理
日志
```

都会被破坏。

### 11. MCP 会不会替代 LangGraph

不会。

LangGraph 解决的是：

```text
流程编排。
```

例如：

```text
意图识别
RAG 回答
订单查询
字段提取
缺字段追问
用户确认
创建工单
最终回答
```

MCP 解决的是：

```text
外部能力接入。
```

未来它们可以配合：

```text
LangGraph 的 query_order_node
-> 通过 MCP Client 调 query_order tool
```

所以：

```text
LangGraph 管流程。
MCP 管外部工具/资源/prompt 的标准连接。
```

### 12. MCP 和 RAG 的关系也不同

RAG 解决：

```text
检索相关知识，再让模型基于知识回答。
```

MCP Resource 可以提供：

```text
文档
文件
数据库 schema
API 契约
业务规则
```

但 Resource 本身不等于 RAG。

如果你只是通过 MCP 读取一个文档：

```text
resources/read -> java-ai-api-contract.md
```

这只是读取资源。

如果你要基于很多文档做：

```text
chunk
embedding
向量检索
top_k
rerank
引用来源
无上下文拒答
```

这才是 RAG。

所以：

```text
MCP Resource 可以成为 RAG 的资料来源。
MCP 不等于 RAG。
```

### 13. 三种落地模式

这一节最容易学薄的地方，就是只说“它们不同”，但没有说“项目里怎么用”。

放到真实项目里，通常有三种落地模式。

#### 模式 A：只用 Tool Calling，不引入 MCP

结构是：

```text
模型
  |
  | tool_call
  v
ai-service
  |
  v
本地 tool_registry / Java client / RAG service
```

特点：

```text
工具定义写在 ai-service 里。
工具执行逻辑也由 ai-service 控制。
所有权限、确认、错误映射都在 ai-service 内部处理。
不需要 MCP Server。
```

优点：

```text
结构简单。
学习成本低。
调试路径短。
适合单个项目早期验证。
```

缺点：

```text
工具不容易被其他 AI Host 复用。
工具发现不够标准。
如果工具越来越多，ai-service 会越来越重。
不同 AI 应用可能重复写相似工具接入代码。
```

我们前面阶段大部分就是这个模式。

它不是落后，也不是错误。

它适合：

```text
先把 Agent 主链路学会。
先把权限、确认、Java 服务接入、RAG 学扎实。
暂时不急着做工具生态标准化。
```

#### 模式 B：把现有工具包装成 MCP Server

结构是：

```text
模型
  |
  | tool_call
  v
Host / ai-service
  |
  | MCP Client
  v
订单 MCP Server
  |
  v
JavaOrderClient / JavaTicketClient
  |
  v
Java business service
```

特点：

```text
query_order / create_ticket 不再只是 ai-service 内部工具。
它们被包装成 MCP Tools。
Host 通过 MCP Client 发现和调用它们。
MCP Server 内部仍然复用原来的业务 client 和安全校验。
```

优点：

```text
工具能力可以更标准地暴露。
未来其他 Host 也能复用这些工具。
工具接入层和 Agent 编排层更容易分开。
```

缺点：

```text
多了一层 MCP Server。
要处理连接、协议、错误、测试和部署。
早期项目会变复杂。
```

这个模式很适合我们后续学习。

因为我们已经有：

```text
query_order
create_ticket
JavaOrderClient
JavaTicketClient
Java business service
权限和错误边界
```

这些都是可以被 MCP Server 包装的现成能力。

#### 模式 C：ai-service 作为 Host，连接多个外部 MCP Server

结构是：

```text
模型
  |
  v
ai-service / Host
  |
  | MCP Client 1
  v
订单 MCP Server

ai-service / Host
  |
  | MCP Client 2
  v
文档 MCP Server

ai-service / Host
  |
  | MCP Client 3
  v
GitHub / 文件 / 数据库 MCP Server
```

特点：

```text
ai-service 不一定自己实现所有工具。
它可以连接多个外部 MCP Server。
启动时发现每个 Server 暴露了哪些 Tools / Resources / Prompts。
再把可用能力整理给模型和 Agent workflow 使用。
```

优点：

```text
扩展性强。
外部能力可以独立演进。
适合企业内部多个系统接入 AI。
也适合 IDE Agent、客服 Agent、运营 Agent 共用工具生态。
```

缺点：

```text
权限边界更复杂。
工具命名冲突要处理。
不同 Server 的错误要统一。
观测、审计、配置管理要求更高。
```

这个模式更接近成熟 AI 工具生态。

但对学习顺序来说，不能一开始就上来做这个。

更合理的顺序是：

```text
先理解 Tool Calling
再理解 MCP 架构
再写一个最小 MCP Server
再把 query_order 包成 MCP Tool
最后再考虑多个 MCP Server 的组合
```

### 14. 什么时候只用 Tool Calling 就够

如果满足这些条件，只用 Tool Calling 通常够：

```text
只有一个 AI 应用。
工具数量少。
工具都在应用内部。
不需要给多个 Host 复用。
不需要暴露 Resource / Prompt。
工具列表变化不频繁。
部署和权限边界比较简单。
```

比如当前项目早期阶段：

```text
只有 ai-service 一个 Host。
query_order / create_ticket 工具数量少。
工具直接调用 Java mock service。
主要目标是学习 Tool Calling 和 Agent 流程。
```

这时候直接写：

```text
tool_registry
Pydantic 参数模型
Java client
测试
```

完全合理。

过早引入 MCP 反而会增加复杂度。

### 15. 什么时候值得引入 MCP

如果出现下面情况，就值得考虑 MCP：

```text
多个 AI 应用都想复用同一批工具。
公司有多个外部系统要接入 AI。
工具、资源、prompt 希望按统一协议暴露。
希望第三方或其他团队能连接你的工具服务。
希望工具能力独立部署和演进。
希望 Host 能动态发现 Server 提供的能力。
```

举例：

```text
客服 Agent 要查订单。
运营助手也要查订单。
管理后台 AI 助手也要查订单。
IDE Agent 要读取项目 API 契约。
内部 Chat 助手要读取业务规则。
```

如果每个应用都自己写一遍：

```text
JavaOrderClient
工具 schema
权限说明
错误映射
文档读取
```

就会重复。

这时可以做：

```text
公司业务 MCP Server
```

统一暴露：

```text
Tools: query_order, create_ticket
Resources: API 契约、数据库 schema、业务规则文档
Prompts: 工单总结模板、客服回答模板
```

### 16. 决策清单：什么时候不需要 MCP，什么时候需要 MCP

以后你判断技术方案时，可以直接按下面这组问题问。

#### 先问：这个项目是不是还在单应用阶段？

如果答案是：

```text
只有一个 ai-service。
只有当前这个 Agent 会用这些工具。
工具数量还不多。
```

那通常先不用 MCP。

原因是：

```text
MCP 的价值是标准连接和复用。
如果暂时没有复用需求，过早引入会增加协议层、调试层和部署层复杂度。
```

#### 再问：工具是不是只服务当前 Agent 流程？

如果工具只服务一个固定流程，比如：

```text
用户查订单
缺字段追问
确认后创建工单
```

并且这些工具不会给其他 Host 使用，那么：

```text
Tool Calling + 本地 tool_registry 足够。
```

#### 再问：工具是否要被多个 AI 产品复用？

如果出现：

```text
客服 Agent 要用。
运营 Agent 要用。
IDE Agent 要用。
内部 Chat 助手也要用。
```

这时就要认真考虑 MCP。

因为 MCP 可以把能力做成：

```text
可发现
可调用
可复用
可独立部署
```

#### 再问：除了工具，是否还要暴露资源和 prompt？

如果你只需要：

```text
query_order
create_ticket
```

Tool Calling 可能已经够。

但如果还希望暴露：

```text
API 契约文档
数据库 schema
业务规则文件
客服回复模板
工单总结模板
```

那 MCP 的价值会明显变大。

因为 MCP 不只管 Tool，还管：

```text
Resources
Prompts
```

#### 最后问：团队是否需要工具生态标准化？

如果团队里每个人都在不同项目里重复写：

```text
订单工具接入
工单工具接入
知识库读取
文档读取
prompt 模板管理
```

就说明这个能力已经不是某个单点功能，而是一个生态问题。

这时 MCP 更适合。

#### 一句话决策

```text
单项目、少工具、自己用：先用 Tool Calling。
多项目、多工具、多 Host 复用：考虑 MCP。
工具之外还要标准暴露文档和 prompt：更应该考虑 MCP。
```

### 17. 两者结合的完整链路

未来一个完整链路可能是：

```text
1. Host 启动。
2. Host 为订单 MCP Server 创建 MCP Client。
3. Client 初始化连接并做能力协商。
4. Client 请求 tools/list。
5. Server 返回 query_order、create_ticket 等 MCP tools。
6. Host 把这些 MCP tools 转成模型 API 可接受的 Tool Calling schema。
7. 用户问：A1001 订单到哪了？
8. 模型输出 tool_call: query_order({order_id: "A1001"}).
9. Host 校验用户上下文和工具调用策略。
10. Host 通过 MCP Client 调 tools/call。
11. MCP Server 执行 query_order。
12. query_order 内部调用 JavaOrderClient。
13. JavaOrderClient 调 Java business service。
14. Java 返回统一响应。
15. MCP Server 返回工具结果。
16. Host 把工具结果交回模型。
17. 模型生成最终中文回答。
```

这条链路里：

```text
第 6-8 步是 Tool Calling 重点。
第 2-5、10-15 步是 MCP 重点。
第 12-14 步是阶段 7 Java 业务服务接入重点。
第 16-17 步是模型总结重点。
```

### 18. 和我们项目模块的对应关系

| 当前模块 | 当前职责 | 引入 MCP 后可能的位置 |
| --- | --- | --- |
| `tool_registry.py` | 注册工具、权限和参数规则 | 可能被 MCP Server 包装，或作为 Host 的工具适配层 |
| `java_order_client.py` | 调 Java 订单接口 | 仍然作为 MCP Tool 下游 client |
| `java_ticket_client.py` | 调 Java 工单接口 | 仍然作为 MCP Tool 下游 client |
| `java_error_mapping.py` | Java 错误码安全映射 | MCP Tool 仍应复用 |
| `java_business_contract.py` | Java 响应契约校验 | MCP Tool 仍应复用 |
| LangGraph Agent | 多步骤流程编排 | 可通过 MCP Client 使用外部工具 |
| RAG 模块 | 文档检索和回答 | 可读取 MCP Resource 作为上下文来源之一 |
| Java business service | 真实业务执行 | 不被 MCP 替代，仍是业务事实来源 |

### 19. 关键判断：MCP 是“工具供应链”，Tool Calling 是“模型使用工具”

为了避免混淆，可以用一个比喻。

Tool Calling 像：

```text
服务员根据顾客需求选择菜单上的菜。
```

MCP 像：

```text
餐厅用标准方式接入不同厨房、食材仓库、菜单模板。
```

模型像服务员。

Tool Calling 是服务员点菜的机制。

MCP 是后厨能力标准化接入的机制。

这个比喻不需要记太久，但可以帮助你区分：

```text
一个管“模型怎么选择工具”。
一个管“工具和资源怎么标准接入 AI 应用”。
```

### 20. 面试表达：怎么把这件事讲得专业

如果别人问：

```text
MCP 和 Tool Calling 有什么区别？
```

不要只回答：

```text
一个是协议，一个是工具调用。
```

这个回答太短，别人听不出你真的理解。

更好的回答可以分三层。

#### 第一层：先给结论

```text
MCP 和 Tool Calling 不是同一层东西。
Tool Calling 主要解决模型如何选择并请求调用工具。
MCP 主要解决 AI 应用如何用统一协议连接外部工具、资源和 prompt。
```

#### 第二层：说明它们怎么配合

```text
在实际链路里，Host 可以先通过 MCP Client 从 MCP Server 发现工具，
再把这些 MCP Tools 转成模型 API 可以理解的 tools schema。
模型通过 Tool Calling 选择某个工具后，
Host 再通过 MCP Client 调用 MCP Server 的 tools/call。
```

这句话能体现你知道：

```text
MCP Tool 不是直接等于模型 tool_call。
中间有 Host 适配和安全控制。
```

#### 第三层：结合项目边界

可以接着说：

```text
在我们的项目里，query_order 和 create_ticket 现在是 ai-service 内部工具。
未来可以把它们包装成 MCP Tools。
但 MCP Server 内部仍然应该复用 JavaOrderClient / JavaTicketClient，
不能绕过 Java business service 的权限、错误码、trace_id、幂等和契约校验。
LangGraph 仍然负责 Agent 流程编排，MCP 只负责外部能力标准接入。
```

这个表达就比“一个是协议，一个是函数调用”强很多。

它说明你理解了：

```text
模型层
应用层
协议层
业务服务层
安全边界
项目演进方式
```

如果要再压缩成一句高级但不空的话，可以说：

```text
Tool Calling 让模型能表达“我要用哪个工具和什么参数”，MCP 让应用能用标准协议发现和调用外部工具、资源与 prompt；在工程上通常由 Host 把 MCP 暴露的能力适配成模型 tools，再把模型的 tool_call 转回 MCP tools/call 执行。
```

## 常见误区

### 误区 1：有了 MCP 就不需要 Tool Calling

不对。

MCP Server 暴露工具后，模型仍然需要某种方式选择工具。

如果 Host 使用模型 API 的 tool calling，那么 Host 需要把 MCP tool 转成模型可用的工具 schema。

### 误区 2：有了 Tool Calling 就不需要 MCP

也不一定。

如果只是一个应用、几个工具，确实可以不用 MCP。

但如果要让多个 AI 应用复用外部工具、资源和 prompt，MCP 就有价值。

### 误区 3：MCP Tool 就是 Java API

不对。

Java API 是业务接口。

MCP Tool 是 AI 接入层暴露的工具能力。

MCP Tool 可以调用 Java API，但不等于 Java API。

### 误区 4：MCP 可以绕过权限

不对。

MCP 不会自动解决所有业务安全问题。

写操作仍然需要：

```text
用户确认
权限校验
幂等键
trace_id
审计
错误映射
```

### 误区 5：MCP 只用来暴露工具

不对。

MCP 还有：

```text
Resources
Prompts
```

如果只把 MCP 当作远程函数调用，就学窄了。

## 本节结论

你可以这样记：

```text
Tool Calling 是模型请求工具的机制。
MCP 是 AI 应用连接外部工具、资源和 prompt 的协议。
MCP Tool 可以被 Host 转换成模型 Tool Calling 的工具定义。
模型通过 Tool Calling 选择工具，Host 再通过 MCP Client 调用 MCP Server。
```

放到我们项目里：

```text
当前 tool_registry 是内部工具注册表。
未来 MCP Server 可以包装 query_order / create_ticket。
MCP Tool 内部仍然应该调用 JavaOrderClient / JavaTicketClient。
Java business service 仍然负责真实业务规则、权限、MySQL、Redis 和错误码。
LangGraph 仍然负责流程编排。
```

## 本节练习

### 练习 1：用一句话区分 MCP 和 Tool Calling

参考答案：

```text
Tool Calling 解决模型如何请求调用工具，MCP 解决 AI 应用如何标准连接外部工具、资源和 prompt。
```

### 练习 2：MCP Tool 和模型 tools schema 是不是同一个东西？

参考答案：

```text
不是完全同一个层级。
MCP Tool 是 MCP Server 暴露的工具能力。
模型 tools schema 是 Host 传给模型看的工具定义。
Host 可以把 MCP Tool 转换成模型 tools schema。
```

### 练习 3：为什么 MCP 不应该绕过 JavaOrderClient？

参考答案：

```text
因为 JavaOrderClient 已经负责 Java business API 的 header、trace_id、错误映射、超时处理和响应契约。
MCP Tool 如果绕过它直接调数据库或裸调 Java API，会破坏阶段 7 建好的安全和契约边界。
```

### 练习 4：什么时候只用 Tool Calling 就够？

参考答案：

```text
当只有一个 AI 应用、工具数量少、工具都在应用内部、不需要跨 Host 复用、不需要暴露 Resources 和 Prompts 时，只用 Tool Calling 通常足够。
```

### 练习 5：什么时候适合引入 MCP？

参考答案：

```text
当多个 AI 应用需要复用同一批工具、资源和 prompt，或者希望外部能力独立部署、标准发现、标准调用时，适合引入 MCP。
```

### 练习 6：把下面动作分到 Tool Calling 或 MCP

动作：

```text
1. 模型决定调用 query_order。
2. Host 从某个 Server 获取 tools/list。
3. 模型生成 order_id 参数。
4. MCP Client 向 MCP Server 发送 tools/call。
5. Host 把工具执行结果交回模型总结。
```

参考答案：

```text
1 属于 Tool Calling。
2 属于 MCP。
3 属于 Tool Calling。
4 属于 MCP。
5 更靠近 Tool Calling 的工具结果回传环节，但实际由 Host 应用层负责执行。
```

### 练习 7：为什么单项目早期不一定要上 MCP？

参考答案：

```text
因为如果只有一个 AI 应用、工具数量少、工具都由当前 ai-service 自己维护，那么本地 tool_registry + Tool Calling 就能解决问题。
MCP 的主要价值是标准连接、发现和复用。
如果暂时没有复用和工具生态需求，过早上 MCP 会增加协议、测试、部署和调试复杂度。
```

### 练习 8：如果公司有客服 Agent、运营 Agent、内部 Chat 助手都要查订单，为什么 MCP 更合适？

参考答案：

```text
因为这些不同 Host 都需要复用同一个订单查询能力。
如果每个 Host 都自己写订单工具接入，会产生重复代码和重复维护。
把订单查询包装成 MCP Tool 后，多个 Host 可以通过统一协议发现和调用它，订单权限、错误映射、trace_id 和下游 Java 服务调用也更容易集中维护。
```

## 自测题

### 自测 1：MCP 会不会替代 LangGraph？

参考答案：

```text
不会。
LangGraph 负责多步骤 Agent 流程编排。
MCP 负责外部工具、资源和 prompt 的标准接入。
未来 LangGraph 节点可以通过 MCP Client 调用外部工具。
```

### 自测 2：MCP 会不会替代 Java business service？

参考答案：

```text
不会。
Java business service 负责真实业务规则、权限、事务、MySQL、Redis 和错误码。
MCP Server 只是把这些能力包装成 AI 应用可标准连接的工具或资源。
```

### 自测 3：模型选择工具这一步属于 MCP 还是 Tool Calling？

参考答案：

```text
更属于 Tool Calling。
MCP 负责让 Host 从 Server 发现和调用工具。
模型根据工具 schema 选择工具，是 Tool Calling 的核心职责。
```

### 自测 4：读取 API 契约文档更像 MCP Tool 还是 Resource？

参考答案：

```text
更像 Resource。
读取文档是获取上下文，不是执行业务动作。
如果调用订单查询接口，那才更像 Tool。
```

### 自测 5：当前项目未来最自然的 MCP 改造点是什么？

参考答案：

```text
最自然的是把 query_order 和 create_ticket 暴露成 MCP Tools，把 Java-AI API 契约、数据库设计、业务规则文档暴露成 MCP Resources，再把客服回复和工单总结模板暴露成 MCP Prompts。
```

### 自测 6：如果模型返回了 tool_call，是否说明 MCP Server 已经被调用了？

参考答案：

```text
不一定。
模型返回 tool_call 只说明模型表达了“想调用某个工具”的意图。
Host 收到后还要做工具名校验、参数校验、权限判断、确认判断等应用层处理。
如果这个工具来自 MCP，Host 之后才会通过 MCP Client 调用 MCP Server 的 tools/call。
```

### 自测 7：为什么说 MCP Tool 可以是 Tool Calling tool 的上游来源？

参考答案：

```text
因为 Host 可以先通过 MCP Client 从 MCP Server 获取工具列表和参数 schema，
再把这些 MCP Tool 信息转换成模型 API 可以接收的 tools schema。
模型看到的是转换后的工具定义，并通过 Tool Calling 选择工具。
所以 MCP Tool 可以作为模型工具定义的来源，但它们不是同一层对象。
```

## 本节总结

本节最重要的是分清层级：

```text
Tool Calling：模型如何请求使用工具。
MCP：AI 应用如何标准连接工具、资源和 prompt。
LangGraph：Agent 如何编排流程。
Java business service：真实业务如何执行。
```

你以后可以这样对外讲：

```text
我不会把 MCP 简单理解成 Tool Calling。
Tool Calling 是模型和应用之间的工具选择机制。
MCP 是 AI 应用和外部能力之间的标准连接协议。
在项目里，MCP 可以把订单查询、创建工单、API 契约文档和 prompt 模板暴露给 AI Host；但真实业务执行仍然要走 Java business service 的权限、幂等、错误码和 trace_id 边界。
```

下一节学习：

```text
阶段 8 第 3 节：MCP 架构
```
