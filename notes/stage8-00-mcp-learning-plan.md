# 阶段 8 学习计划：MCP 与 AI 工具生态基础

## 阶段定位

阶段 8 的主题是：

```text
MCP 与 AI 工具生态基础
```

它接在阶段 7 后面。

阶段 7 已经解决：

```text
Python AI 服务如何安全调用真实 Java Spring Boot + MySQL/Redis 业务服务。
```

阶段 8 要继续解决：

```text
如何用 MCP 把外部工具、资源、业务服务和 AI 应用按统一协议连接起来。
```

可以先用一句话理解：

```text
Tool Calling 更像“模型调用应用里注册好的工具”。
MCP 更像“让 AI 应用用统一协议发现和调用外部工具、资源和 prompt”。
```

## 阶段目标

学完阶段 8 后，要能说清楚：

```text
MCP 是什么，解决什么问题。
MCP 和 Tool Calling、RAG、插件、普通 HTTP API 有什么区别。
MCP Host、Client、Server 分别是什么。
MCP Tool、Resource、Prompt 分别适合暴露什么能力。
如何用 Python 写一个最小 MCP Server。
如何把当前项目里的订单查询、创建工单、文档资源封装成 MCP 能力。
MCP 工具为什么仍然需要权限、幂等、trace_id、错误码和契约测试。
MCP 接入现有 LangGraph Agent 和 Java business service 时应该放在哪里。
```

## 默认环境

默认：

```text
Windows 本地学习。
不需要打开 VMware Ubuntu。
不需要 Qdrant / Milvus。
不需要真实大模型。
```

如果某一节需要：

```text
Java business service
MySQL
Redis
Docker
真实模型 API key
```

学习前再单独说明。

## 阶段 8 固定 24 节

| 节 | 主题 | 重点 |
| --- | --- | --- |
| 1 | MCP 是什么 | MCP 解决什么问题，为什么它不是普通 API，也不是简单 Tool Calling |
| 2 | MCP 和 Tool Calling 的区别 | Tool Calling、MCP、RAG、插件、API 的关系 |
| 3 | MCP 架构 | Host、Client、Server 分别是什么 |
| 4 | MCP 通信基础 | JSON-RPC、请求、响应、通知、能力协商 |
| 5 | MCP 生命周期 | initialization、operation、shutdown |
| 6 | MCP Transport | stdio、Streamable HTTP，先学本地 stdio |
| 7 | MCP Tools 基础 | 工具暴露、参数 schema、工具返回结果 |
| 8 | MCP Resources 基础 | 如何把文档、配置、schema、业务资料暴露成上下文 |
| 9 | MCP Prompts 基础 | 服务器提供可复用 prompt 模板 |
| 10 | Python 最小 MCP Server | 用 Python SDK 写第一个 MCP server |
| 11 | MCP Client 调试 | 如何列出工具、调用工具、看返回 |
| 12 | 工具参数校验 | Pydantic/schema、枚举、必填字段、错误提示 |
| 13 | MCP 错误处理 | 业务错误、系统错误、协议错误怎么分 |
| 14 | MCP 安全边界 | 权限、最小暴露、prompt injection、敏感字段过滤 |
| 15 | 把订单查询封装成 MCP Tool | MCP tool -> Python adapter -> Java business service |
| 16 | 把创建工单封装成 MCP Tool | 写操作确认、幂等键、用户身份传递 |
| 17 | MCP Resource 接入项目文档 | 暴露 API 契约、学习笔记、业务规则文档 |
| 18 | MCP 和现有 Agent 的关系 | MCP 在 LangGraph / Tool Calling / Java API 之间放在哪里 |
| 19 | MCP 测试和契约测试 | fake client、工具测试、错误映射测试 |
| 20 | 阶段 8 初版项目整理 | 总结 MCP 基础能力、项目边界、下一步工程化 |
| 21 | MCP Server 工程结构整理 | 避免只会写单文件 demo，学会项目化组织 |
| 22 | MCP 配置和环境变量 | 路径、token、Java 地址、权限开关配置化 |
| 23 | MCP 可观测性 | 日志、trace_id、工具调用耗时、错误码 |
| 24 | MCP 阶段总结和面试表达 | 把 MCP 和 Agent、RAG、Java 后端的关系讲清楚 |

## 阶段产出预期

阶段 8 结束时，项目应该至少有：

```text
MCP 学习笔记
一个最小 MCP Server
MCP tool 示例
MCP resource 示例
MCP prompt 示例
MCP 工具参数校验
MCP 错误处理
MCP 安全边界说明
MCP 与 Java business service 的接入设计
MCP 相关测试
阶段 8 总结和面试表达
```

代码放哪里先不死定。

第 1 节会根据当前项目结构决定：

```text
projects/ai-service/app/mcp/
```

或者：

```text
projects/mcp-service/
```

原则是：

```text
如果 MCP 只是 ai-service 的内部能力，放进 ai-service。
如果 MCP 要作为独立服务演示和运行，放成独立 mcp-service。
```

## 学习要求

阶段 8 继续沿用当前学习要求：

```text
基础知识铺垫要足。
本节主题系统讲解要足。
不能只写薄薄的 API 用法。
新增或修改的学习相关代码要讲清楚。
测试部分讲重要边界，不需要过度展开。
练习题和自测题答案放在对应题目下面。
如果使用省 token 模式，仍要保证主笔记质量，只减少不必要的重复和长验证输出。
```

## 阶段 8 和后续阶段的边界

阶段 8 先学 MCP。

不在这一阶段无限扩展：

```text
不深入 Kubernetes。
不做复杂 Multi-Agent 平台。
不做模型微调。
不做完整浏览器操作 Agent。
不做大规模企业 MCP 网关。
```

阶段 8 学完后，再考虑进入：

```text
LangGraph 深入
RAG 混合检索与 Rerank
Tracing 和自动化评估强化
多模型路由和成本控制
Human-in-the-loop 强化
```
