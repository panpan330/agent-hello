# AI 应用工程学习路线图

版本：2026-07-31

适用目标：已有 Java 后端基础，转向 AI 应用开发 / 后端 AI 工程 / RAG 与 Agent 应用工程。

## 1. 路线定位

主线不是纯算法、模型训练或只做提示词，而是：

```text
Java 后端能力
  + Python AI 服务
  + LangChain / LangGraph
  + RAG / Tool Calling
  + 评测 / 追踪 / 安全 / 部署
  = 能落地的 AI 应用工程能力
```

学习后的目标不是“知道很多名词”，而是能独立做出两个可运行、可讲清楚、可继续迭代的项目：

1. 企业知识库 RAG 系统
2. 智能工单 Agent

第三个项目“业务数据助手”只作为加分项，等前两个项目稳定后再做。

## 2. 技术栈选择

### 主技术栈

| 层级 | 技术 | 用途 |
| --- | --- | --- |
| Java 业务层 | Spring Boot | 用户、权限、订单、退款、工单、业务 API |
| Python AI 层 | FastAPI | 对外提供 AI 服务接口 |
| 数据校验 | Pydantic | 请求、响应、结构化输出、tool 入参校验 |
| LLM 编排 | LangChain | 模型调用、prompt、tool calling、structured output、retriever |
| 流程编排 | LangGraph | 多步骤、有状态、可恢复、可人工确认的 Agent 流程 |
| 向量库 | Qdrant 主线 + Milvus 对比扩展 | Qdrant 上手快，适合作为 RAG 主线；Milvus 用于理解 schema/index 和大规模向量库选型 |
| 部署 | Docker Compose | 本地和演示环境一键启动 |
| 测试评估 | pytest + eval 脚本 | 单元测试、接口测试、RAG/Agent 效果评测 |

### 暂不作为主线

- Spring AI：当前目标环境不流行，先不作为主线。
- PyTorch / 模型训练 / 微调：以后要转算法或模型方向再补。
- Elasticsearch / pgvector / 更多向量库横向对比：先把 Qdrant 主线和 Milvus 对比学透，后续按项目需要再补。
- 全自动 Agent：先做可控流程，再逐步增加智能决策。
- Kubernetes：项目能 Docker Compose 跑通后再考虑。

## 3. 学习原则

1. **项目牵引，不刷 API**
   每个知识点都要落到接口、脚本、测试或项目功能里。

2. **从基础讲起，不跳知识**
   不默认已经懂某个概念。每个知识点都要先讲“是什么、为什么、解决什么问题”，再写最小例子，最后进入项目。

3. **理解优先，不只会用**
   目标不是复制命令，而是能向别人解释原理、用途、边界、常见错误和排查方式。

4. **资料辅助，建立体系**
   重要知识点要补充官方文档、课程或视频方向，避免只靠零散问答学习。

5. **练习必须有答案**
   每节笔记都要包含练习参考答案和自测参考答案，方便复盘和纠错。

6. **先可控，再智能**
   AI 只能调用明确授权的工具。创建工单、查询敏感数据等动作必须有权限校验和人工确认。

7. **日志和评测前置**
   从第一个 `/chat` 接口开始就记录模型、耗时、token、错误和 trace_id。

8. **Java 优势不能丢**
   Java 继续负责业务系统和稳定接口，Python 负责 AI 编排和模型生态。

9. **每周必须有可验收产出**
   没有通过验收标准，就不要急着进入下一阶段。

默认教学流程：

```text
概念解释 -> 为什么需要 -> 最小例子 -> 动手练习 -> 结果讲解 -> 常见问题 -> 自测问题 -> 笔记沉淀
```

## 4. 总体阶段

| 阶段 | 时间 | 主题 | 核心产出 |
| --- | --- | --- | --- |
| M0 | 第 0 周 | 环境与仓库 | 学习仓库、环境检查、模型 API、Docker |
| M1 | 第 1-2 周 | Python AI 服务基础 | FastAPI AI 服务、聊天接口、流式输出、结构化输出 |
| M2 | 第 3-4 周 | LangChain + Java 工具调用 | 客服助手 v1、Java mock 业务服务、tool 调用 |
| M3 | 第 5-7 周 | 企业知识库 RAG | 文档入库、检索问答、引用来源、权限过滤、初版评测 |
| M4 | 第 8-9 周 | LangGraph 智能工单 | 26 节主线，完成可控、可测试、可恢复的工单 Agent v1 |
| M5 | 第 10-11 周 | 生产化与评测 | 36 节主线，补 Agent 评测、真实模型节点、持久化状态、追踪监控、稳定性保护和部署编排 |
| M6 | 第 12 周 | 作品整理 | 快速版 5 节：项目定位、README、架构图/流程图、运行说明/演示脚本、简历/面试问答 |
| M7 | 第 13 周起 | 真实 Java 后端接入 AI Agent | 12 节主线，完成 Spring Boot + MyBatis + MySQL/Redis 业务服务底座，以及 AI 调用传统 Java 后端的边界、契约、权限、幂等、错误码、trace_id 和契约测试 |
| M8 | 第 14 周 | MCP 与 AI 工具生态基础 | 24 节主线，学习 MCP 概念、架构、通信、生命周期、transport、tools、resources、prompts、Python MCP Server、Client 调试、安全、测试、可观测性，以及如何接入 Java business service |
| M9 | 已完成 | RAG 进阶与检索质量优化 | 24 节主线，补 query rewrite、multi query、hybrid search、rerank、引用校验、权限过滤、RAG 评测、bad case 分析、参数调优、缓存降级、可观测性、数据更新、多知识库路由和面试表达 |
| M10 | 当前阶段 | AI 应用生产化与可运营能力 | 合并后 23 节主线，补 tracing、日志安全、配置与密钥、token 成本、耗时拆解、多模型路由、fallback、成本控制、限流、重试、超时、SSE 生产化、安全加固、自动化评估、监控告警、灰度回滚和 Runbook |

如果每天只有 1-2 小时，可以把 M3 和 M5 各延长 1 周。不要为了赶进度牺牲项目质量。

## 5. M0：环境与仓库

目标：把后续学习的基础环境和目录定下来。

任务：

- 安装 Python 3.11/3.12。
- 安装 uv 或 poetry，二选一即可。
- 安装 JDK 17+。
- 安装 Docker / Docker Compose。
- 准备一个 OpenAI-compatible 模型 API。
- 选择向量库，初期建议 Qdrant。
- 明确仓库目录：

```text
docs/       路线、进度、架构、复盘
notes/      学习笔记、踩坑记录
projects/   项目代码
```

验收标准：

- 能运行 `python --version`。
- 能运行 `java -version`。
- 能运行 `docker version`。
- 仓库有清晰的 README、路线图和进度表。

## 6. M1：Python AI 服务基础

时间：第 1-2 周

目标：做出一个标准的 Python AI 服务，而不是零散脚本。

建议目录：

```text
projects/ai-service/
  app/
    main.py
    core/config.py
    core/logging.py
    api/routes/
    schemas/
    services/
    tests/
  .env.example
  pyproject.toml
  Dockerfile
  README.md
```

学习内容：

- Python 虚拟环境和依赖管理。
- FastAPI 路由、请求体、响应体、异常处理。
- Pydantic 模型校验。
- 环境变量管理。
- httpx 调外部接口。
- logging、trace_id、请求耗时。
- pytest 基础测试。
- Dockerfile 基础。

必须实现：

- `GET /health`
- `POST /chat`
- `GET /stream-chat` 或 `POST /stream-chat`
- `POST /extract/resume`
- `POST /classify/intent`

验收标准：

- 服务能启动。
- 密钥不写死，统一从 `.env` 读取。
- 普通聊天和流式聊天都能调用模型。
- 结构化输出能被 Pydantic 校验。
- 每次请求至少记录 trace_id、模型名、耗时、错误信息。
- 至少有 5 个 pytest 用例。

## 7. M2：LangChain + Java 工具调用

时间：第 3-4 周

目标：掌握 tool calling，并把 Java 后端能力接入 AI。

### Python AI 层

学习内容：

- ChatModel / messages。
- Prompt template。
- structured output。
- tools 定义和调用。
- Runnable / chain 基础。
- streaming。
- callbacks / tracing 基础。

必须实现的 mock tools：

```text
query_order(order_id)
query_refund(order_id)
query_logistics(order_id)
create_ticket(user_id, title, description, category)
```

### Java 业务层

建议目录：

```text
projects/business-service/
```

必须实现接口：

```text
GET /api/orders/{orderId}
GET /api/refunds/{orderId}
GET /api/logistics/{orderId}
GET /api/tickets/{ticketId}
POST /api/tickets
GET /api/users/{userId}/permissions
```

安全原则：

- AI 不直接查业务数据库。
- AI 不直接执行高风险动作。
- AI 只能通过白名单 tool 调 Java API。
- 创建工单、退款、审批等动作必须预留 confirmation。

验收标准：

- 用户自然语言提问后，AI 能判断是否调用工具。
- tool 入参有 Pydantic 校验。
- tool 结果能被模型整合为自然语言回答。
- 每次 tool 调用都有日志。
- Python tool 可以调用 Java API。
- Java API 有清晰错误码和日志。

## 8. M3：企业知识库 RAG

时间：第 5-7 周

目标：完成第一个主项目：企业知识库 RAG 系统。

### 第 5 周：文档入库

学习内容：

- RAG 基础流程：load -> split -> embed -> store -> retrieve -> generate。
- Markdown / txt / PDF / docx 解析。
- 文本清洗。
- chunk 切分策略。
- embedding 接入。
- Qdrant 写入、删除、重建索引。
- metadata 设计。

推荐 metadata：

```text
doc_id
chunk_id
content
source
page
title
department
user_group
created_at
```

验收标准：

- 可以上传或导入一个文档。
- 文档能切分成 chunks。
- 每个 chunk 有 metadata。
- 能按 doc_id 删除和重建索引。

### 第 6 周：查询链路

必须实现：

- 用户提问向量化。
- top_k 检索。
- score_threshold。
- context 拼接。
- 基于 context 回答。
- citations 引用来源。
- 无资料时拒答。
- 检索日志。

验收标准：

- 回答必须带引用。
- 引用能定位到文档和 chunk。
- 没有检索结果时不能胡编。
- 至少准备 20 个测试问题。

### 第 7 周：RAG 进阶

必须补充：

- 权限过滤：department / user_group / user_id。
- 问题改写。
- 混合检索初版：向量检索 + 关键词检索。
- rerank 初版。
- 上下文压缩。
- 命中率统计：hit / miss / low_score。

验收标准：

- 不同用户能看到不同文档范围。
- 同一个问题能看到召回和 rerank 的差异。
- 能输出检索到的 chunks。
- 有初版 RAG eval 报告。

## 9. M4：LangGraph 智能工单 Agent

时间：第 8-9 周

目标：完成第二个主项目：智能工单 Agent。

阶段 5 固定为 26 节主线。第 1-12 节先打 LangGraph 基础，第 13-22 节接入智能工单业务，第 23-26 节补错误处理、日志、测试和项目整理。不要为了赶进度压缩成 16 或 22 节；Agent 评测、LangSmith tracing、Docker Compose、前端工作台等更生产化内容放到后续阶段。

细化学习清单：

| 节 | 主题 | 目标 |
| --- | --- | --- |
| 1 | LangGraph 是什么，为什么现在才学 | 理解 LangGraph 解决多步骤、有状态、可恢复 Agent 流程 |
| 2 | LangGraph 和 LangChain / 普通函数流程的区别 | 区分组件封装、普通编排和图式状态机 |
| 3 | Agent 流程和状态机基础 | 理解 Agent 为什么可以被看成状态流转 |
| 4 | State 是什么：Agent 为什么需要状态 | 设计保存用户输入、中间结果、分支决策的 state |
| 5 | Reducer 是什么：状态字段怎么合并 | 理解状态更新、列表追加、消息合并等规则 |
| 6 | MessagesState：多轮对话消息怎么保存 | 理解多轮消息状态和普通业务 state 的区别 |
| 7 | StateGraph 最小图 | 创建最小可运行 graph |
| 8 | node 节点是什么 | 把流程步骤拆成单一职责节点 |
| 9 | edge 边是什么 | 理解节点之间的固定流转 |
| 10 | conditional edge 条件分支 | 根据 state 决定下一步 |
| 11 | START / END 和流程结束 | 理解图入口、出口和何时结束 |
| 12 | graph.invoke / graph.stream：普通执行和流式执行 | 理解一次性执行和流式观察中间状态 |
| 13 | 智能工单 Agent 总流程设计 | 画出完整业务流程和节点分工 |
| 14 | 意图识别节点 | 判断用户是问知识、查订单还是需要创建工单 |
| 15 | RAG 知识库回答节点 | 接入阶段 4 的知识库回答能力 |
| 16 | 判断是否需要创建工单 | 根据 RAG/意图/用户诉求决定是否进入工单流程 |
| 17 | 工单字段提取节点 | 从用户描述中提取 title、category、description 等字段 |
| 18 | 缺失字段追问节点 | 用户信息不完整时继续追问 |
| 19 | 用户确认节点 | 创建工单前必须确认敏感动作 |
| 20 | 调用 Java mock 创建工单节点 | 接回阶段 3 的 Java mock API |
| 21 | checkpoint 和 thread_id：中断、恢复、继续对话 | 保存流程状态并支持同一任务继续 |
| 22 | interrupt / human-in-the-loop | 学会在图执行中等待人工输入 |
| 23 | 节点错误处理、fallback 和流程兜底 | 处理模型失败、RAG 无资料、Java API 失败 |
| 24 | LangGraph 日志、trace_id 和可观测性 | 串联图节点日志和已有 trace_id |
| 25 | LangGraph 测试：fake LLM / fake RAG / fake Java client | 不依赖真实外部服务测试流程分支 |
| 26 | 阶段 5 项目整理和面试表达 | 复盘架构、验收清单和讲解版本 |

流程：

```text
用户描述问题
  -> 问题分类
  -> 检索知识库
  -> 判断能否直接解决
  -> 不能解决则提取工单字段
  -> 让用户确认
  -> 调用 Java API 创建工单
  -> 返回工单号
```

工单字段：

```text
title
description
category
priority
user_id
related_order_id
evidence
```

验收标准：

- 每个节点职责单一。
- 状态里能看到中间结果。
- 条件分支可测试。
- 同一个 thread_id 能继续对话。
- 字段提取使用 structured output。
- 创建工单前必须 human confirmation。
- 创建成功后能查 Java 后端工单记录。

## 10. M5：生产化与评测

时间：第 10-11 周

目标：把项目从 demo 提升到可上线雏形。

阶段 6 固定为 36 节主线。目标不是继续堆 Agent 功能，而是把已经能运行的 RAG + 智能工单 Agent 往真实工程系统推进：能评测、能接真实模型、能追踪、能保存状态、能处理上游失败、能控制成本和延迟、能用 Docker Compose 编排本地多服务。不要把这一阶段压缩成只学 eval、Docker 或 tracing；这三者都只是生产化的一部分。

细化学习清单：

| 节 | 主题 | 目标 |
| --- | --- | --- |
| 1 | Agent 评测基础：为什么 AI 应用不能只靠感觉判断好坏 | 理解 AI 输出不稳定，必须用固定样本和指标判断质量 |
| 2 | 什么是 eval：测试和评测的区别 | 区分功能正确性测试、效果评测、回归评测和线上监控 |
| 3 | 设计 Agent 测试集 | 设计 query、expected intent、expected route、expected tool、expected fields |
| 4 | 意图识别评测 | 衡量 `policy_question`、`order_query`、`ticket_request` 等分类是否正确 |
| 5 | 工单字段提取评测 | 衡量 `order_id`、`issue_type`、`urgency`、`need_human_review` 等字段正确率 |
| 6 | Agent 路由评测 | 判断 RAG、工单、订单查询、闲聊、不支持、追问分支是否走对 |
| 7 | RAG + Agent 组合评测 | 评估检索结果、RAG 回答和 Agent 决策如何共同影响最终行为 |
| 8 | 评测脚本设计 | 用 JSON 样本和 Python 脚本写可重复运行的本地评测 |
| 9 | 评测报告 | 输出 pass/fail、命中率、字段正确率、坏例列表和改进建议 |
| 10 | 坏例分析 | 分析 bad case 是数据问题、prompt 问题、模型问题还是流程问题 |
| 11 | 回归评测 | 改 prompt、改节点、改工具后防止旧能力退化 |
| 12 | evaluator 类型 | 理解规则 evaluator、代码 evaluator、人类评审、LLM-as-judge 和 pairwise 对比 |
| 13 | 真实 LLM 意图识别节点 | 把规则版分类逐步升级为模型版分类 |
| 14 | 真实 LLM 字段提取节点 | 用模型提取工单字段，并保持结构化输出 |
| 15 | Pydantic 校验模型输出 | 模型结果不能直接信，必须做 schema 校验和错误兜底 |
| 16 | fake LLM 和真实 LLM 双模式 | 测试用 fake，手动验收和 smoke test 用真实模型 |
| 17 | prompt 版本管理 | 记录 prompt 版本、变更原因、评测结果和回滚方式 |
| 18 | 模型输出失败处理 | 处理空输出、非 JSON、字段缺失、拒答、超时和安全拒绝 |
| 19 | 接入真实 `query_order` 到 LangGraph | 把阶段 3 的订单查询工具链路接入 `query_order` 节点 |
| 20 | 工具节点错误处理升级 | 处理 Java 服务超时、404、500、字段异常和上游不可用 |
| 21 | 工具权限和写操作安全回归 | 复查工具白名单、风险等级、用户确认、幂等和敏感操作边界 |
| 22 | 持久化 checkpoint 基础 | 理解为什么 `MemorySaver` 不适合生产，并打通文件型 checkpoint 快照基础 |
| 23 | checkpoint 存储选型 | 对比内存、文件、SQLite、Postgres、Redis 的适用场景，并确定当前项目推荐路径 |
| 24 | `thread_id` 生命周期 | 设计 thread 创建、归属绑定、恢复、完成、关闭和过期判断策略 |
| 25 | 会话过期与清理 | 防止长期堆积 checkpoint，设计 retention、过期确认、归档和热 checkpoint 清理策略 |
| 26 | LangSmith tracing 基础 | 理解 trace、run、metadata、dataset、experiment 在 Agent 里的作用 |
| 27 | OpenTelemetry 基础 | 理解 trace、span、logs、metrics 和 vendor-neutral observability |
| 28 | trace/span/log/metrics 的关系 | 区分一次请求链路、单个操作、日志事件和聚合指标 |
| 29 | 生产日志字段设计 | 设计 trace_id、thread_id、node、route、error_code、latency、status 等字段 |
| 30 | 成本、token 和延迟指标 | 观察模型成本、token 用量、RAG/工具耗时和端到端延迟 |
| 31 | timeout 超时策略 | 给模型、RAG、向量库、Java 服务和整体 Agent 设置合理超时 |
| 32 | retry 重试策略 | 判断哪些错误可以重试，哪些错误不能重试，避免重复写操作 |
| 33 | rate limit、circuit breaker 和降级 | 学习限流、熔断、持续失败保护和降级回答 |
| 34 | Docker Compose 本地编排 | 编排 Python AI 服务、Java mock、Qdrant/Milvus 等多服务 |
| 35 | health check、readiness 和 CI 自动回归 | 让服务启动可检查，测试和评测可自动运行 |
| 36 | 阶段 6 项目整理和面试表达 | 复盘生产化与评测能力，整理项目讲解版本 |

必须补充：

- 请求日志。
- 模型调用日志。
- tool 调用日志。
- token 成本统计。
- 超时控制。
- 失败重试。
- 限流。
- 缓存。
- 错误码规范。
- Docker Compose。
- 健康检查。

建议记录 `ai_trace`：

```text
trace_id
user_id
question
route
retrieved_chunks
tool_calls
final_answer
latency_ms
token_usage
cost
error
created_at
```

评测集：

```text
知识库问答 30 条
工单场景 20 条
订单/退款查询 20 条
异常输入 10 条
越权问题 10 条
```

评测维度：

- 检索是否命中。
- 答案是否基于引用。
- 是否胡编。
- tool 是否调用正确。
- 字段提取是否正确。
- 是否越权。
- 响应耗时。

验收标准：

- 有 `eval.py` 或等价评测脚本。
- 能一键输出 pass/fail 报告。
- 能定位失败样例。
- 每次改 prompt、chunk、rerank 策略后能对比效果。
- 服务能 `docker compose up` 一键启动。

## 11. M6：作品整理和面试准备

时间：第 12 周

目标：把项目整理成能展示、能讲清楚、能写进简历的作品。

当前执行策略：

```text
M6 使用快速版，共 5 节。
这一阶段只做作品化、总结、展示和表达，不把当前项目强行扩展成完整生产系统。
M6 完成后，进入真实 Java 后端接入 AI Agent 主线。
```

快速版目录：

| 节 | 主题 | 目标 |
| --- | --- | --- |
| 1 | 项目定位和作品化目标 | 讲清楚这个项目是什么、为什么不是完整生产系统但仍然可以作为 AI 工程作品 |
| 2 | 整理 GitHub 首页 README | 整理项目介绍、技术栈、目录结构、学习阶段、核心能力和运行入口 |
| 3 | 架构图和核心流程图 | 整理整体架构、RAG 流程、Agent 工单流程、工具调用安全流程 |
| 4 | 本地运行说明和演示脚本 | 写清楚如何启动服务、如何演示知识库问答、查订单、创建工单、评测和 CI |
| 5 | 简历描述、面试讲稿、常见追问 | 准备 1/3/5 分钟讲法、简历 bullet、常见面试问答、项目不足和后续路线 |

每个主项目必须整理：

- README。
- 架构图。
- 启动方式。
- 接口文档。
- 核心流程截图。
- 测试问题样例。
- 技术难点说明。
- 可优化点。
- 失败案例和改进记录。

面试必须能讲清楚：

- RAG 为什么会答错？
- chunk 大小怎么选？
- 向量检索和关键词检索区别？
- rerank 解决什么问题？
- 为什么 AI 不能直接操作数据库？
- tool calling 怎么保证安全？
- LangGraph 解决了什么问题？
- human-in-the-loop 为什么必要？
- 如何评测一个知识库问答系统？
- 如何定位一次 AI 回答失败？

简历表达草稿：

```text
基于 FastAPI + LangChain + LangGraph 构建企业知识库问答与智能工单 Agent，
实现文档解析、chunk 切分、embedding、向量检索、权限过滤、RAG 引用回答、
LangGraph 多节点流程编排、人工确认、Java 业务工具调用、流式响应、
调用链日志、token 成本统计、评测脚本和 Docker Compose 部署。
```

## 12. M7：真实 Java 后端接入 AI Agent

M7 已完成。

阶段定位：

```text
不重复传统 Spring Boot 基础。
重点学习传统 Java 后端被 AI Agent 调用时新增的工程边界。
```

固定完成 12 节：

| 节 | 主题 | 状态 |
| --- | --- | --- |
| 1 | AI Agent 调用传统 Java 后端时的边界设计 | 已完成 |
| 2 | 面向 Tool Calling 的 Java API 契约设计 | 已完成 |
| 3 | 真实 Spring Boot 服务骨架和领域模型 | 已完成 |
| 4 | MySQL 业务数据模型 | 已完成 |
| 5 | 查询订单读工具真实化 | 已完成 |
| 6 | 创建工单写工具真实化 | 已完成 |
| 7 | Redis 幂等、缓存和限流 | 已完成 |
| 7.5 | Java 服务结构传统化重构 + MyBatis | 已完成 |
| 8 | AI 场景下的内部鉴权和用户身份传递 | 已完成 |
| 9 | Java 错误码到 AI 用户回答 | 已完成 |
| 10 | trace_id 串联 Python + Java | 已完成 |
| 11 | 契约测试和集成测试 | 已完成 |
| 12 | 阶段 7 项目整理 | 已完成 |

阶段产出：

```text
projects/java-business-service
docs/java-ai-api-contract.md
docs/java-business-database-design.md
contracts/java-business-service/internal-api-contract-cases.json
notes/stage7-12-project-summary.md
```

阶段 7 完成后，项目已经具备真实 Java 业务服务底座，但仍不是完整生产系统。

仍需后续补：

```text
Python Agent 主链路完全迁移到 java-business-service。
真实用户表和完整认证授权。
前端客服工作台。
部署、监控、告警和压测。
更多 AI 应用工程进阶技术。
```

## 13. M8：MCP 与 AI 工具生态基础

M8 已完成。下一阶段进入 M9。

阶段定位：

```text
MCP 与 AI 工具生态基础。
在已经学过 Tool Calling、LangGraph Agent、RAG 和真实 Java business service 的基础上，学习如何用 MCP 把外部工具、资源、prompt 和 AI 应用按统一协议连接起来。
```

固定为 24 节：

| 节 | 主题 | 目标 |
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

阶段计划笔记：

```text
notes/stage8-00-mcp-learning-plan.md
```

默认环境：

```text
Windows 本地。
默认不需要打开 VMware Ubuntu。
默认不需要 Qdrant / Milvus。
默认不需要真实大模型。
```

## 14. M9：RAG 进阶与检索质量优化

阶段定位：

```text
RAG 进阶与检索质量优化。
在已经完成基础 RAG、Qdrant、Milvus、LangGraph、真实 Java 后端和 MCP 的基础上，把 RAG 从“能跑通”推进到“能调优、能评测、能解释、能用于真实项目”。
```

固定为 24 节：

| 节 | 主题 | 目标 |
| --- | --- | --- |
| 1 | RAG 进阶总览：为什么基础 RAG 还不够 | 建立阶段 9 的完整学习地图，理解基础 RAG 在真实项目中的典型短板 |
| 2 | Query Rewrite：用户问题改写 | 学会把口语化、含糊、不完整的问题改写成更适合检索的问题 |
| 3 | Multi Query：一个问题生成多个检索问题 | 理解为什么一个用户问题可能需要多种检索角度，提高召回覆盖面 |
| 4 | 查询意图识别：区分查政策、查订单、查流程、闲聊 | 学会在 RAG 前判断问题类型，避免所有问题都盲目查知识库 |
| 5 | Hybrid Search 进阶：关键词检索 + 向量检索融合 | 学习关键词检索和向量检索的互补关系，以及初步融合策略 |
| 6 | 检索分数理解：score、distance、相似度到底怎么看 | 理解不同检索系统分数方向、含义和不可直接横向比较的问题 |
| 7 | Rerank 进阶：召回后为什么还要重排序 | 理解粗召回和精排序的分工，知道 rerank 解决什么质量问题 |
| 8 | 真实 Rerank 模型接入 | 学会接入真实 rerank 模型，并保留 fake rerank 方便测试 |
| 9 | 引用来源校验：回答必须能对应原文 | 学会检查答案是否真的来自召回文档，减少编造和错引 |
| 10 | Context Compression：上下文压缩 | 理解为什么不能把所有 chunk 都塞给模型，学习压缩上下文的方法 |
| 11 | Metadata Filter：用户、租户、权限、业务域过滤 | 把检索范围限定在用户有权访问的文档和业务域内 |
| 12 | RAG Prompt Injection 防护 | 学习文档内容中恶意提示的风险，以及模型侧和系统侧防护边界 |
| 13 | RAG 评测集设计 | 学会设计问题、期望答案、期望来源、权限场景和拒答场景 |
| 14 | 检索指标：命中率、召回率、Top-K 命中 | 用指标判断检索是否把正确资料找出来，而不是只看最终回答 |
| 15 | 回答质量评测：正确性、引用一致性、拒答合理性 | 评估最终回答是否正确、是否引用一致、是否该拒答时拒答 |
| 16 | Bad Case 分析：怎么定位 RAG 答错的原因 | 建立 RAG 问题排查路径，区分数据、检索、排序、生成和权限问题 |
| 17 | 参数调优：chunk_size、overlap、top_k、score_threshold | 学会用可观察结果调整 RAG 参数，而不是凭感觉乱调 |
| 18 | RAG 缓存、超时、降级和性能优化 | 学习真实服务里 RAG 的响应时间、成本和可用性保护 |
| 19 | RAG 可观测性：记录 query、召回、rerank、引用、耗时 | 给 RAG 链路补齐排查所需日志和指标 |
| 20 | RAG 数据更新：增量入库、删除、重新索引 | 理解知识库文档变化后，向量库和索引如何保持一致 |
| 21 | RAG 多知识库路由 | 学习用户问题应该查哪个知识库，而不是所有资料混在一起检索 |
| 22 | RAG 与 Agent 的组合边界 | 讲清楚 RAG 负责查资料，Agent 负责流程决策和工具编排 |
| 23 | RAG 生产化验收清单：质量、安全、性能、成本、可观测性 | 整理一个真实 RAG 功能上线前应该检查什么 |
| 24 | 阶段 9 总复盘和面试表达强化 | 把阶段 9 的能力整理成项目表达、面试回答和后续学习路线 |

阶段计划笔记：

```text
notes/stage9-00-rag-advanced-learning-plan.md
```

默认环境：

```text
多数小节 Windows 本地即可。
涉及 Qdrant、Milvus、真实向量库数据更新时，需要打开 VMware Ubuntu。
涉及真实 Query Rewrite、Multi Query、Rerank 或 LLM-as-judge 时，才需要真实模型 API。
自动化测试默认不真实调用大模型。
```

## 15. M10：AI 应用生产化与可运营能力

阶段定位：

```text
AI 应用生产化与可运营能力。在已经完成 RAG、Agent、MCP、真实 Java 后端和 RAG 进阶的基础上，补齐真实 AI 应用上线后必须面对的稳定性、可观测性、安全性、成本控制、评估回归、灰度发布和故障处理能力。
```

阶段计划笔记：

```text
notes/stage10-00-ai-production-operability-learning-plan.md
```

阶段 10 原计划为 28 节。
第 1-15 节完成后，后半段合并为 8 节，总节数调整为 23 节。
合并原则：只合并强相关主题，不删知识点，不降低笔记质量。

| 节 | 主题 | 目标 |
| --- | --- | --- |
| 1 | AI 应用生产化总览 | 建立阶段 10 的完整地图 |
| 2 | Tracing 是什么 | 理解 AI 应用为什么必须能追踪完整链路 |
| 3 | trace_id / span / event / metric 的区别 | 区分链路标识、阶段片段、关键事件和聚合指标 |
| 4 | Python AI 服务 tracing | 梳理 ai-service 内部的追踪方式 |
| 5 | Java 业务服务 tracing 对齐 | 串联 Python 到 Java 的跨服务排查链路 |
| 6 | LLM 调用日志安全 | 安全记录模型调用，不泄露密钥、隐私和敏感上下文 |
| 7 | 配置与密钥管理 | 管理 `.env`、API Key、环境配置和密钥边界 |
| 8 | Token 成本统计 | 统计 prompt、completion、总 token 和成本 |
| 9 | 请求耗时拆解 | 拆解检索、rerank、LLM、Tool、Java 后端等耗时 |
| 10 | 多模型路由基础 | 按任务、成本、速度和稳定性选择模型 |
| 11 | 模型 fallback | 主模型失败时切备用模型 |
| 12 | 成本控制 | 设计预算、限额、降级和低成本模型策略 |
| 13 | 限流 | 设计用户级、接口级、模型级、工具级限流 |
| 14 | 重试 | 区分可重试错误、不可重试错误和幂等边界 |
| 15 | 超时治理 | 设计请求总超时和各阶段超时 |
| 16 | SSE 流式输出生产化与中断处理 | 覆盖原 16、17：SSE 事件格式、心跳、首 token 延迟、资源释放、中途错误、用户取消、断连处理和部分输出边界 |
| 17 | Prompt Injection、权限控制与隐私保护 | 覆盖原 18、19、20：系统提示防护、工具调用防注入、外部输入隔离、多轮上下文风险、用户/租户/角色/工具权限、敏感信息保护、日志脱敏和安全回答边界 |
| 18 | 自动化评估平台基础与评测集版本管理 | 覆盖原 21、22：eval 脚本、评测任务、评测数据、评测结果、报告沉淀、评测集版本、基线和回归对比 |
| 19 | Bad Case 收集、分析与回归测试 | 覆盖原 23：线上问题沉淀、失败分类、复现方式、修复验证和防止旧问题回归 |
| 20 | 生产监控指标与告警基础 | 覆盖原 24、25：请求量、错误率、延迟、token、成本、模型失败、fallback、限流、RAG/LLM/tool 指标，以及有效告警规则 |
| 21 | 灰度发布、回滚与配置开关 | 覆盖原 26：模型、Prompt、RAG 参数、路由策略和安全策略的灰度发布、配置开关、失败回滚 |
| 22 | SLO / SLA / Runbook | 覆盖原 27：服务目标、对外承诺、故障分级、排查步骤、恢复动作和复盘记录 |
| 23 | 阶段 10 总复盘和面试表达强化 | 覆盖原 28：生产化能力地图、项目表达、面试问答、简历素材和后续路线 |

默认环境：

```text
多数小节 Windows 本地即可。
只有涉及真实 Java 服务、Redis/MySQL、真实模型 API、SSE 手动体验或外部服务验证时，才需要额外启动服务。
开始每节前，如果需要 VMware Ubuntu、Docker、Redis、MySQL、Java 服务或真实模型 API，必须先明确提醒。
```

## 16. M11：完整智能工单系统项目化

阶段定位：

```text
完整智能工单系统项目化。把已经学过的前端、Java Spring Boot、Python FastAPI、MySQL、Redis、Qdrant、真实 LLM/embedding/rerank、RAG、Tool Calling、Agent 和生产化能力整合成完整、真实、可运行、可演示、可写简历的 AI 应用项目。
```

阶段 11 的核心变化：

```text
前面阶段以学习技术点为主。
阶段 11 以完整项目交付为主。
```

阶段 11 的主文档：

```text
docs/stage11-product-scope-and-realization-standards.md
docs/stage11-technical-plan-and-task-breakdown.md
```

阶段 11 的默认标准：

- 核心链路尽量使用真实组件，不继续停留在 mock 演示。
- 需要真实外部资源时，开始对应小节前先明确告诉用户准备什么。
- 阶段文档以产品文档、接口文档、数据库文档、运行文档、演示脚本为主。
- 遇到新知识仍然从基础讲清楚，但不再每节都写成大篇课程笔记。

阶段 11 初步拆分为 16 节：

| 节 | 主题 | 目标 |
| --- | --- | --- |
| 1 | 项目产品范围与真实化标准 | 固定项目边界、真实化标准和验收标准 |
| 2 | 阶段 11 技术方案与任务拆分 | 明确前端、Java、Python、数据库、向量库和部署实施顺序 |
| 3 | 前端技术选型与项目骨架 | 使用 Vue3 + TypeScript + Vite + Element Plus 创建真实前端项目 |
| 4 | 登录与用户角色最小闭环 | 打通用户身份、角色和基础权限 |
| 5 | Java 业务数据模型补全 | 完善用户、订单、工单、知识库等核心业务表 |
| 6 | 前端订单与工单基础页面 | 做出订单和工单可操作页面 |
| 7 | Python AI 对话接口真实化整理 | 对齐前端调用的 AI API |
| 8 | 知识库管理与真实入库 | 支持真实 embedding 和 Qdrant 入库 |
| 9 | 真实 LLM + embedding + rerank 链路验收 | 验证真实模型链路可用 |
| 10 | AI 查询订单和创建工单端到端联调 | 前端到 AI 到 Java 到数据库完整跑通 |
| 11 | 客服工单工作台 | 支持客服处理、状态流转和事件记录 |
| 12 | AI 评估与 bad case 页面 | 把评估和坏例能力产品化展示 |
| 13 | 生产化配置和运行说明 | 整理完整本地启动和环境变量 |
| 14 | Docker Compose 本地部署 | 尽量一键启动核心服务 |
| 15 | 演示脚本和简历材料 | 完成作品化表达 |
| 16 | 阶段 11 总验收和补洞 | 检查完整项目达标情况 |

默认环境：

```text
第 1 节不需要外部服务。
涉及前端时需要 Node.js。
涉及 Java 业务联调时需要 MySQL/Redis。
涉及 RAG 时需要 Qdrant。
涉及真实 AI 能力时需要 LLM、embedding、rerank API Key。
如果某节需要 VMware Ubuntu、Docker、数据库或真实模型 API，开始前必须明确提醒。
```

## 17. 每周执行节奏

建议每周固定节奏：

```text
周一：明确本周验收标准，拆任务
周二到周四：编码实现核心功能
周五：补测试、日志、异常处理
周六：整理 README、笔记、截图
周日：复盘，更新 learning-progress.md
```

每天 2 小时版本：

```text
20 分钟：看文档或复习概念
70 分钟：写代码
20 分钟：测试和调试
10 分钟：更新笔记
```

## 18. 不要提前分散精力

前 8 周不要重点投入：

- 大模型微调。
- PyTorch 深度学习。
- 多模型横向测评。
- 复杂前端 UI。
- Kubernetes。
- 多 Agent 花活。
- 自研向量数据库。

这些东西不是没用，而是当前阶段投入产出比不高。先把 RAG 和工单 Agent 做成可运行项目。

## 19. 通关标准

达到下面 6 条，才算具备 AI 应用工程实战基础：

```text
1. 能独立做一个知识库 RAG 系统。
2. 能解释 chunk、embedding、rerank、引用来源。
3. 能用 LangGraph 做多步骤业务流程。
4. 能让 AI 安全调用 Java 后端接口。
5. 能做日志、评测、权限、成本统计。
6. 能把项目 Docker 化并写清楚部署文档。
```

## 20. 下一步

立即开始 M0/M1：

1. 检查 Python、Java、Docker 环境。
2. 创建 `projects/ai-service`。
3. 搭建 FastAPI 基础项目。
4. 实现 `/health`、`/chat`、`/stream-chat`。
5. 从第一天开始记录日志、trace_id 和学习笔记。
