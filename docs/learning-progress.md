# Java + Python + AI 学习进度

## 当前状态

```text
路线已确定：Java 后端 + Python AI 服务 + LangChain/LangGraph + RAG/Agent 工程化
当前阶段：阶段 9 RAG 进阶与检索质量优化第 15 节已完成；下一节学习 Bad Case 分析：怎么定位 RAG 答错的原因。
主要仓库：D:\wendang\java+python+ai
执行路线：docs/ai-application-learning-roadmap.md
当前工作约定：docs/current-stage-working-agreement.md
```

## 阶段进度

| 阶段 | 时间 | 主题 | 状态 | 产出 |
| --- | --- | --- | --- | --- |
| M0 | 第 0 周 | 环境与仓库 | 进行中 | README、上下文、路线图、进度表 |
| M1 | 第 1-2 周 | Python AI 服务基础 | 已完成 | `projects/ai-service`、聊天接口、流式输出、结构化输出 |
| M2 | 第 3-4 周 | LangChain + Java 工具调用 | 已完成 | 客服助手 v1、Java mock 业务服务 |
| M3 | 第 5-7 周 | 企业知识库 RAG | 已完成 | 文档入库、检索问答、引用来源、权限过滤、Milvus 对比、初版评测 |
| M4 | 第 8-9 周 | LangGraph 智能工单 | 已完成 | 26 节主线，完成可控、可测试、可恢复的工单 Agent v1 |
| M5 | 第 10-11 周 | 生产化与评测 | 已完成 | 36 节主线，补 Agent 评测、真实模型节点、持久化状态、追踪监控、稳定性保护和部署编排 |
| M6 | 第 12 周 | 作品整理 | 已完成 | 快速版 5 节：项目定位、README、架构图/流程图、运行说明/演示脚本、简历/面试问答 |
| M7 | 第 13 周起 | 真实 Java 后端接入 AI Agent | 已完成 | 阶段 7 共 12 节，完成真实 Spring Boot + MyBatis + MySQL/Redis 业务服务底座，并补齐 AI Agent 调用传统 Java 后端时的边界、契约、幂等、权限、错误码、trace_id 和契约测试 |
| M8 | 第 14 周 | MCP 与 AI 工具生态基础 | 已完成 | 阶段 8 共 24 节已完成：MCP 概念、架构、通信、生命周期、transport、tools、resources、prompts、Python MCP Server、Client 调试、参数校验、错误处理、安全、接入 Java business service、测试、工程结构、配置、可观测性和面试表达 |
| M9 | 第 15 周起 | RAG 进阶与检索质量优化 | 进行中 | 第 1-15 节已完成：RAG 进阶总览、基础 RAG 短板、RAG 问题分层排查、Query Rewrite、Multi Query、查询意图识别、Hybrid Search 进阶、检索分数语义、Rerank 进阶、真实 Rerank 模型 adapter、HttpReranker、RerankExecutionResult、fallback、MockTransport 测试、rerank_score 分数解释、引用来源校验、blocking/warning finding、轻量支撑度评分、Context Compression、keep/compress/drop、压缩报告、Metadata Filter、RagAccessScope、多租户/权限组/业务域过滤、payload/scalar filter、RAG Prompt Injection 防护、risk level、blocked reason codes、RAG 评测集设计、expected behavior、answer points、expected evidence、access context、refusal reason codes、dataset coverage report、检索指标、Hit@K、Hit Rate@K、Recall@K、Precision@K、MRR@K、metric breakdown、回答质量评测、answer point coverage、citation pass rate、refusal pass rate、forbidden source 检查和质量 bad case 输出；后续继续 bad case、调优、可观测性和生产化 |

## M6 快速版学习清单

M6 的定位是快速作品化，不把当前项目包装成完整生产系统，也不在这一阶段继续大规模新增业务功能。

目标：

```text
把已经完成的 AI 客服工单系统学习项目，整理成别人能看懂、自己能演示、面试能讲清楚、简历能准确表达的作品项目。
```

固定为 5 节：

| 节 | 主题 | 状态 | 目标 |
| --- | --- | --- | --- |
| 1 | 项目定位和作品化目标 | 已完成 | `notes/m6-01-project-positioning-and-portfolio-goals.md`、项目定位、作品化边界、README 基础文案、面试回答口径、M6 产出目标 |
| 2 | 整理 GitHub 首页 README | 已完成 | `notes/m6-02-github-homepage-readme.md`、README 首页作品化、项目定位、核心能力、技术栈地图、快速阅读入口、当前边界 |
| 3 | 架构图和核心流程图 | 已完成 | `notes/m6-03-architecture-and-core-flow-diagrams.md`、`docs/project-diagrams.md`、整体架构图、RAG 问答流程图、智能工单 Agent 流程图、工具调用安全流程图 |
| 4 | 本地运行说明和演示脚本 | 已完成 | `notes/m6-04-local-run-and-demo-script.md`、`docs/local-run-and-demo.md`、Windows 本地最小运行、真实模型可选演示、Qdrant/Milvus 可选演示、统一回归、常见问题 |
| 5 | 简历描述、面试讲稿、常见追问 | 已完成 | `notes/m6-05-resume-interview-qa.md`、`docs/interview-and-resume.md`、简历 bullet、1/3/5 分钟讲稿、常见面试追问、项目不足和后续路线 |

M6 完成后，优先进入：

```text
阶段 7：真实 Java Spring Boot + MySQL/Redis 业务服务
```

## 阶段 7 学习清单

阶段 7 的定位：

```text
不重复传统 Spring Boot 基础。
重点学习如何把传统 Java 后端设计成 AI Agent 可以安全、稳定、可追踪调用的真实业务系统。
```

| 节 | 主题 | 状态 | 目标 |
| --- | --- | --- | --- |
| 1 | AI Agent 调用传统 Java 后端时的边界设计 | 已完成 | `notes/stage7-01-ai-agent-java-boundary-design.md`、模型意图和后端执行边界、读写工具分级、DTO/Entity 边界、错误码、幂等、权限、trace_id、阶段 7 改造方向 |
| 2 | 面向 Tool Calling 的 Java API 契约设计 | 已完成 | `notes/stage7-02-tool-calling-java-api-contract.md`、`docs/java-ai-api-contract.md`、订单查询和工单创建接口契约、统一响应、请求 DTO、响应 DTO、错误码、Header、字段白名单、契约测试清单 |
| 3 | 真实 Spring Boot 服务骨架和领域模型 | 已完成 | `notes/stage7-03-spring-boot-service-skeleton-domain-model.md`、`projects/java-business-service`、Spring Boot 骨架、internal API、统一响应、错误码、Header 校验、订单/工单领域模型、内存 Repository、幂等雏形、MockMvc 契约测试 |
| 4 | MySQL 业务数据模型 | 已完成 | `notes/stage7-04-mysql-business-data-model.md`、`docs/java-business-database-design.md`、用户表、订单表、工单表、工单事件表、索引、唯一约束、幂等字段、AI 写操作审计字段 |
| 5 | 查询订单读工具真实化 | 已完成 | `notes/stage7-05-spring-boot-mysql-order-query.md`、Spring Boot DataSource、JDBC、JdbcTemplate、HikariCP、orders 表初始化、JdbcOrderRepository、H2 测试配置、Windows MySQL smoke |
| 6 | 创建工单写工具真实化 | 已完成 | `notes/stage7-06-mysql-ticket-write-transaction.md`、tickets 表、ticket_events 表、`@Transactional`、MySQL 唯一索引幂等兜底、request_fingerprint、DuplicateKeyException 处理、真实 MySQL smoke |
| 7 | Redis 幂等、缓存和限流 | 已完成 | `notes/stage7-07-redis-idempotency-cache-rate-limit.md`、Spring Data Redis、订单 read-through cache、工单幂等缓存、Redis fixed window 限流、Redis 失败降级、真实 Redis/MySQL smoke |
| 7.5 | Java 服务结构传统化重构 + MyBatis | 已完成 | `notes/stage7-075-java-service-traditional-mybatis-refactor.md`、`notes/stage7-075-java-service-traditional-mybatis-refactor-manual-tasks.md`；Java business service 已对齐到 `controller/service/service.impl/mapper/entity/dto/config/exception/common` 风格，并用 MyBatis Mapper + XML 替换 JdbcTemplate，同时保留 DTO 白名单、权限、幂等、trace_id、错误码和 internal token 边界 |
| 8 | AI 场景下的内部鉴权和用户身份传递 | 已完成 | `notes/stage7-08-internal-auth-user-identity.md`、`notes/stage7-08-internal-auth-user-identity-manual-tasks.md`；Python 调 Java 时的服务身份、真实用户身份、租户边界、internal token、allowed caller、header 格式校验、权限兜底 |
| 9 | Java 错误码到 AI 用户回答 | 已完成 | `notes/stage7-09-java-error-code-to-ai-user-answer.md`、`notes/stage7-09-java-error-code-to-ai-user-answer-manual-tasks.md`；Python `java_error_mapping.py` 集中处理 Java 错误码，区分用户可见业务错误和内部隐藏错误，避免模型自由解释 Java 内部细节 |
| 10 | trace_id 串联 Python + Java | 已完成 | `notes/stage7-10-trace-id-python-java-chain.md`、`notes/stage7-10-trace-id-python-java-chain-manual-tasks.md`；Python ContextVar + 日志 trace_id、Java TraceFilter + MDC + 响应头、Python client upstream_trace_id 日志，完成最小跨服务排查链路 |
| 11 | 契约测试和集成测试 | 已完成 | `notes/stage7-11-contract-and-integration-tests.md`、`notes/stage7-11-contract-and-integration-tests-manual-tasks.md`；共享契约 JSON、Java provider 契约测试、Python consumer 契约模型和测试已经落地，自动化测试不真实调用大模型 |
| 12 | 阶段 7 项目整理 | 已完成 | `notes/stage7-12-project-summary.md`；阶段 7 能力地图、当前项目边界、mock 链路与真实 Java business 链路关系、后续学习方向已整理，并同步更新 README、架构图、运行说明、面试材料和契约文档 |

## 阶段 8 学习清单

阶段 8 的定位：

```text
MCP 与 AI 工具生态基础。
重点学习如何用 MCP 把外部工具、资源、prompt 和 AI 应用按统一协议连接起来。
```

阶段 8 计划记录：

```text
notes/stage8-00-mcp-learning-plan.md
```

固定为 24 节：

| 节 | 主题 | 状态 | 目标 |
| --- | --- | --- | --- |
| 1 | MCP 是什么 | 已完成 | `notes/stage8-01-what-is-mcp.md`；MCP 的定义、出现原因、Host/Client/Server、Tool/Resource/Prompt、与 HTTP API 和 Tool Calling 的区别、在当前项目中的位置 |
| 2 | MCP 和 Tool Calling 的区别 | 已完成 | `notes/stage8-02-mcp-vs-tool-calling.md`；Tool Calling 解决模型如何请求工具，MCP 解决 AI 应用如何标准连接工具、资源和 prompt，并说明 MCP 与 tool_registry、JavaOrderClient、LangGraph、RAG 的关系 |
| 3 | MCP 架构 | 已完成 | `notes/stage8-03-mcp-architecture.md`；MCP Host、Client、Server 的职责边界，一个 Host 管理多个 Client、一个 Client 连接一个 Server，Tools/Resources/Prompts 在架构中的位置，data layer 和 transport layer 的基础区别，以及 MCP 与 ai-service、LangGraph、Tool Calling、RAG、Java business service 的项目映射 |
| 4 | MCP 通信基础 | 已完成 | `notes/stage8-04-mcp-communication-basics.md`；JSON-RPC、JSON 和 JSON-RPC 的区别、request/response/notification、id/method/params/result/error、initialize 基础、tools/list、tools/call、list_changed notification、协议错误和工具执行错误、MCP 通信与 HTTP REST API 的区别 |
| 5 | MCP 生命周期 | 已完成 | `notes/stage8-05-mcp-lifecycle.md`；Initialization、Operation、Shutdown，initialize request/response、notifications/initialized、协议版本协商、能力协商、Operation 阶段约束、Shutdown 的 transport 关闭方式、请求超时、初始化失败处理，以及 ai-service 未来连接 MCP Server 的生命周期映射 |
| 6 | MCP Transport | 已完成 | `notes/stage8-06-mcp-transport.md`；data layer 和 transport layer 的区别、stdio 的 stdin/stdout/stderr 规则、为什么 stdout 只能输出合法 MCP 消息、Streamable HTTP 的 POST/GET/SSE、MCP endpoint、Origin 校验、localhost 绑定、MCP-Session-Id、MCP-Protocol-Version、本地/远程 MCP Server transport 选型 |
| 7 | MCP Tools 基础 | 已完成 | `notes/stage8-07-mcp-tools-basics.md`；MCP Tool 的定义、tools capability、tools/list、tools/call、Tool 的 name/title/description/inputSchema/outputSchema、content、structuredContent、isError、协议错误和工具执行错误、工具命名和描述设计、安全要求，以及 query_order/create_ticket 的 MCP Tool 设计映射 |
| 8 | MCP Resources 基础 | 已完成 | `notes/stage8-08-mcp-resources-basics.md`；MCP Resource 的定义、Resource 和 Tool/RAG 的区别、resources capability、resources/list、resources/read、uri/name/title/description/mimeType/size、text/blob、Resource Template、listChanged、subscribe/updated、常见 URI scheme、权限和 prompt injection 风险，以及 README、学习进度、Java-AI API 契约等项目文档的 Resource 映射 |
| 9 | MCP Prompts 基础 | 已完成 | `notes/stage8-09-mcp-prompts-basics.md`；MCP Prompt 的定义、Prompt 和 Tool/Resource/system prompt/user prompt 的关系、prompts capability、prompts/list、prompts/get、name/title/description/arguments、Prompt argument 和 Tool inputSchema 的区别、PromptMessage 的 role/content、text/image/audio/embedded resource、listChanged、Prompt 权限和 prompt injection 风险，以及 customer_reply、ticket_summary 等项目模板映射 |
| 10 | Python 最小 MCP Server | 已完成 | `notes/stage8-10-python-minimal-mcp-server.md`、`notes/stage8-10-python-minimal-mcp-server-manual-tasks.md`；新增 `app/mcp_servers/minimal_server.py`，使用 MCP Python SDK v2 创建 `MCPServer`，注册 `echo`/`add` tools 和 `learning://hello/{name}` resource，并用 in-memory `Client(mcp)` 测试 `list_tools`、`call_tool`、`read_resource` |
| 11 | MCP Client 调试 | 已完成 | `notes/stage8-11-mcp-client-debugging.md`、`notes/stage8-11-mcp-client-debugging-manual-tasks.md`；新增 `app/mcp_clients/minimal_client.py` 和 `scripts/mcp_client_smoke.py`，用 in-memory `Client(mcp)` 调试最小 MCP Server，输出 JSON-friendly 快照，覆盖 `list_tools`、`call_tool`、`read_resource` 和 `structured_content`/`content`/`is_error` 观察方法 |
| 12 | MCP 工具参数校验 | 已完成 | `notes/stage8-12-mcp-tool-parameter-validation.md`；新增 `app/mcp_servers/ticket_validation.py` 和 `validate_ticket_draft` tool，用 `Annotated + Field` 暴露 minLength/maxLength，用 `Literal` 暴露 enum，用 Pydantic 做 trim、`extra="forbid"`、`ValidationError` 简化和 `ok=false` 安全返回，并用测试覆盖 schema、合法参数、业务校验错误和非法枚举 schema 层拦截 |
| 13 | MCP 错误处理 | 已完成 | `notes/stage8-13-mcp-error-handling.md`；新增 `app/mcp_servers/tool_error_handling.py` 和 `simulate_tool_error_handling` tool，区分 `is_error=true` 与 `structured_content.ok=false`，模拟成功、业务不存在、权限不足、上游超时和未预期异常，使用安全 `ToolError` 包装系统错误，并用测试固定业务错误、系统错误和内部异常不泄露边界 |
| 14 | MCP 安全边界 | 已完成 | `notes/stage8-14-mcp-security-boundary.md`；新增 `app/mcp_servers/tool_security.py` 和 `inspect_tool_security_boundary` tool，演示工具最小暴露、读写分级、写操作确认、输出白名单、敏感字段过滤、prompt injection 风险识别、危险动作拒绝和安全决策结构化返回，并用测试固定敏感值不泄露、未确认写操作被拒绝、危险 SQL 能力不暴露 |
| 15 | 把订单查询封装成 MCP Tool | 已完成 | `notes/stage8-15-mcp-query-order-tool.md`；新增 `app/mcp_servers/order_tool.py` 和 MCP `query_order` tool，复用 `QueryOrderArgs`、`fake_order_tool.query_order()`、`JavaOrderClient` 与 `QueryOrderResult`，完成只读工具参数契约、业务错误 `ok=false`、系统错误安全 `ToolError`、订单输出白名单和 fake client MCP 调用测试 |
| 16 | 把创建工单封装成 MCP Tool | 已完成 | `notes/stage8-16-mcp-create-ticket-tool.md`；新增 `app/mcp_servers/ticket_tool.py` 和 MCP `create_ticket` tool，完成写操作确认边界、`confirmation_id` 格式校验、使用 `confirmation_id` 作为幂等键、复用 `CreateTicketArgs`/`JavaTicketClient` 风格 creator、业务错误 `ok=false`、系统错误安全 `ToolError`、创建结果输出白名单和 fake creator MCP 调用测试 |
| 17 | MCP Resource 接入项目文档 | 已完成 | `notes/stage8-17-mcp-project-resources.md`；新增 `app/mcp_servers/project_resources.py`，用白名单 URI 暴露 `README.md`、学习进度、Java-AI API 契约、阶段 8 计划和第 16 节 create_ticket 笔记为 `text/markdown` MCP Resources，补充 `resources/list`、`resources/read`、Resource Template 对比、路径逃逸防护和 fake/in-memory client 测试 |
| 18 | MCP 和现有 Agent 的关系 | 已完成 | `notes/stage8-18-mcp-and-existing-agent-relationship.md`；系统梳理 MCP 与 Tool Calling、LangGraph、RAG、Java business service、FastAPI ai-service 的分层关系，明确 MCP 是标准连接层而非替代 Agent/RAG/Java 后端，补充内部 Python tool 与 MCP tool 的取舍、当前项目推荐架构、MCP-backed Agent adapter 迁移路线、权限/trace_id/测试边界和面试表达 |
| 19 | MCP 测试和契约测试 | 已完成 | `notes/stage8-19-mcp-testing-and-contract-tests.md`、`tests/test_mcp_contracts.py`；系统学习 MCP 测试分层、fake client 与 in-memory MCP Client 区别、Tool/Resource 契约测试、业务错误和系统错误测试边界，新增工具名、input_schema、写操作未确认返回、Resource URI/mime_type/read 结果的公共契约测试 |
| 20 | 阶段 8 初版项目整理 | 已完成 | `notes/stage8-20-mcp-initial-project-summary.md`；按概念层、协议层、代码层、项目接入层、测试和工程保障层整理阶段 8 前 19 节成果，梳理 MCP Server/Client/Tools/Resources/契约测试文件地图、当前项目能力、边界、不足和第 21-24 节工程化必要性，并补充阶段性面试表达 |
| 21 | MCP Server 工程结构整理 | 已完成 | `notes/stage8-21-mcp-server-engineering-structure.md`、`server_factory.py`、`tool_registration.py`、`resource_registration.py`；把 `minimal_server.py` 从大装配文件整理为兼容入口，新增 MCP Server factory、Tool registration、Resource registration 分层，保留旧 `mcp` 导入路径，并用契约测试和 factory 测试确认工具/资源对外契约不变 |
| 22 | MCP 配置和环境变量 | 已完成 | `notes/stage8-22-mcp-config-and-env.md`；新增 `MCP_SERVER_NAME`、`MCP_ENABLE_LEARNING_RESOURCES`、`MCP_ENABLE_PROJECT_RESOURCES`、`MCP_PROJECT_RESOURCE_ROOT` 配置和 `.env.example` 示例，`server_factory` 读取 Settings 装配 MCPServer，Resource registration 支持按配置启用/禁用学习资源和项目文档资源，项目资源读取支持配置化 repo_root，并补默认配置、环境变量、env 文件、factory 配置和 Resource 契约测试 |
| 23 | MCP 可观测性 | 已完成 | `notes/stage8-23-mcp-observability.md`、`observability.py`、`tests/test_mcp_observability.py`；新增 MCP Tool/Resource 统一可观测性包装，记录 started/finished/failed、trace_id、tool_name/resource_uri、action_type、status、error_code/error_type、elapsed_ms，并用测试确认工具参数、用户正文、Resource 正文和内部敏感信息不进入 MCP 日志 |
| 24 | MCP 阶段总结和面试表达 | 已完成 | `notes/stage8-24-mcp-summary-and-interview-expression.md`；完整复盘阶段 8 六大模块，整理 MCP 和 Tool Calling、LangGraph、RAG、Java business service 的关系，梳理当前 MCP Server 的 Tools、Resources、测试、配置、可观测性、安全边界、项目不足、下一阶段方向和 30 秒/1 分钟/3 分钟面试表达 |

## 阶段 9 学习清单

阶段 9 的定位：

```text
RAG 进阶与检索质量优化。
重点把基础 RAG 从“能跑通”推进到“能调优、能评测、能解释、能用于真实项目”。
```

阶段 9 计划记录：

```text
notes/stage9-00-rag-advanced-learning-plan.md
```

固定为 24 节：

| 节 | 主题 | 状态 | 目标 |
| --- | --- | --- | --- |
| 1 | RAG 进阶总览：为什么基础 RAG 还不够 | 已完成 | `notes/stage9-01-rag-advanced-overview.md`；建立阶段 9 的完整学习地图，复盘基础 RAG 链路，系统讲解基础 RAG 的真实项目短板、RAG 答错的分层原因、召回/排序/生成/引用/安全/评测的关系，以及阶段 9 后续 24 节如何补齐质量闭环 |
| 2 | Query Rewrite：用户问题改写 | 已完成 | `notes/stage9-02-query-rewrite.md`、`projects/ai-service/app/rag/query_rewrite.py`、`projects/ai-service/tests/test_rag_query_rewrite.py`；系统学习 Query Rewrite 的定义、作用、边界、风险、和 Prompt 优化/意图识别/Multi Query 的区别，新增规则版 `RuleBasedQueryRewriter`、结构化 `QueryRewriteResult`、业务实体 warning、提示注入 warning 和可替换 `QueryRewriter` 协议 |
| 3 | Multi Query：一个问题生成多个检索问题 | 已完成 | `notes/stage9-03-multi-query.md`、`projects/ai-service/app/rag/multi_query.py`、`projects/ai-service/tests/test_rag_multi_query.py`；系统学习 Multi Query 的定义、价值、和 Query Rewrite/Hybrid Search/Rerank 的区别，新增规则版 `RuleBasedMultiQueryGenerator`、结构化 `MultiQueryExpansion`、`query_type`、`reason`、`max_queries` 限制、风险 query 不扩展策略和 debug 输出 |
| 4 | 查询意图识别：区分查政策、查订单、查流程、闲聊 | 已完成 | `notes/stage9-04-query-intent-classification.md`、`projects/ai-service/app/rag/query_intent.py`、`projects/ai-service/tests/test_rag_query_intent.py`；系统学习查询意图识别为什么要放在 Query Rewrite / Multi Query 前，新增规则版 `RuleBasedQueryIntentClassifier`，把用户问题路由到 `policy_lookup`、`order_lookup`、`ticket_creation`、`process_lookup`、`smalltalk`、`unsafe`、`unclear`，并输出 route、confidence、should_use_rag、should_rewrite_query、should_expand_multi_query、实体、warning 和原因 |
| 5 | Hybrid Search 进阶：关键词检索 + 向量检索融合 | 已完成 | `notes/stage9-05-hybrid-search-advanced.md`、`projects/ai-service/app/rag/hybrid.py`、`projects/ai-service/tests/test_rag_hybrid.py`；系统学习关键词检索和向量检索的互补关系、score 归一化、加权融合、chunk_id 去重、vector-only/keyword-only/both 来源分析、融合报告和 debug 输出，以及为什么 Hybrid Search 后通常还需要 rerank |
| 6 | 检索分数理解：score、distance、相似度到底怎么看 | 已完成 | `notes/stage9-06-retrieval-score-distance-similarity.md`、`projects/ai-service/app/rag/score_interpretation.py`、`projects/ai-service/tests/test_rag_score_interpretation.py`；系统学习 score、distance、similarity、Cosine、Dot/IP、L2/Euclid、Manhattan、Qdrant/Milvus 分数方向、`score_threshold` 的 `>=`/`<=` 比较差异、跨后端/跨模型不可直接比较，以及用 `RetrievalScoreMeaning` 把分数语义结构化 |
| 7 | Rerank 进阶：召回后为什么还要重排序 | 已完成 | `notes/stage9-07-rerank-advanced.md`、`projects/ai-service/app/rag/rerank.py`、`projects/ai-service/tests/test_rag_rerank.py`；系统学习召回和重排序的分工、rerank 能解决和不能解决的问题、retrieval_score 与 rerank_score 的区别、RerankReport、top_before/top_after、promoted/dropped、debug lines，以及 lower-is-better retrieval_score 的正确归一化 |
| 8 | 真实 Rerank 模型接入 | 已完成 | `notes/stage9-08-real-rerank-model-adapter.md`、`projects/ai-service/app/rag/rerank.py`、`projects/ai-service/tests/test_rag_rerank.py`、`projects/ai-service/app/core/config.py`；系统学习真实 rerank 模型、cross-encoder 思路、query + documents 输入、index + relevance_score 输出、HTTP adapter、provider 响应校验、MockTransport 自动化测试、真实模型失败 fallback、`RERANK_*` 配置和 `describe_rerank_score()` |
| 9 | 引用来源校验：回答必须能对应原文 | 已完成 | `notes/stage9-09-citation-source-verification.md`、`projects/ai-service/app/rag/citation_verification.py`、`projects/ai-service/tests/test_rag_citation_verification.py`；系统学习 grounded answer、source/chunk/citation/evidence 的区别、后端生成 citation 的优势、确定性引用结构校验、blocking/warning finding、轻量支撑度评分、no-context/answered 状态一致性，以及为什么引用校验是 RAG 生成后的工程防线而不是绝对事实判断 |
| 10 | Context Compression：上下文压缩 | 已完成 | `notes/stage9-10-context-compression.md`、`projects/ai-service/app/rag/context_compression.py`、`projects/ai-service/tests/test_rag_context_compression.py`；系统学习上下文窗口和上下文预算的区别、RAG 为什么不是检索越多越好、top_k/chunk_size/token budget 的关系、过滤/裁剪/压缩的区别、extractive/abstractive compression、规则版抽取式压缩、`ContextCompressionPolicy`、`ContextCompressionReport`、keep/compress/drop 动作、压缩 metadata 和 debug lines |
| 11 | Metadata Filter：用户、租户、权限、业务域过滤 | 已完成 | `notes/stage9-11-metadata-filter-access-scope.md`、`projects/ai-service/app/rag/filters.py`、`projects/ai-service/app/rag/retriever.py`、`projects/ai-service/tests/test_rag_filters.py`、`projects/ai-service/tests/test_rag_retriever.py`；系统学习 metadata filter、用户/租户/权限组/业务域/文档类型/source/status 的区别、为什么过滤应尽量发生在检索侧、payload filter/scalar filter、`RagAccessScope`、`match.value`/`match.any`、`must`/`must_not`、metadata 入库字段和 `MetadataFilterReport` |
| 12 | RAG Prompt Injection 防护 | 已完成 | `notes/stage9-12-rag-prompt-injection-defense.md`、`projects/ai-service/app/rag/security.py`、`projects/ai-service/tests/test_rag_security.py`；系统学习 RAG Prompt Injection 和普通 Prompt Injection 的区别、为什么知识库文档也是不可信输入、文档/metadata 攻击路径、blocking/warning 分级、工具滥用诱导、角色分隔符伪装、metadata prompt injection 扫描、`RagSecurityRiskLevel`、`blocked_reason_codes` 和分层防护边界 |
| 13 | RAG 评测集设计 | 已完成 | `notes/stage9-13-rag-evaluation-dataset-design.md`、`projects/ai-service/app/rag/evaluation.py`、`projects/ai-service/data/rag_eval/rag_cases.json`、`projects/ai-service/tests/test_rag_evaluation.py`；系统学习 RAG 评测集为什么要先于指标，新增 `RagEvalCase`、`RagEvalExpectation`、`RagEvalAccessContext` 和 dataset coverage report，把问题、期望行为、答案要点、期望证据、权限上下文、拒答原因、标签、优先级结构化 |
| 14 | 检索指标：命中率、召回率、Top-K 命中 | 已完成 | `notes/stage9-14-retrieval-metrics-hit-recall-topk.md`、`projects/ai-service/app/rag/evaluation.py`、`projects/ai-service/tests/test_rag_evaluation.py`；系统学习 Top-K、Hit@K、Hit Rate@K、Recall@K、Precision@K、MRR@K 的含义、公式、适用边界和常见误区，新增从 `RagEvalCase` 转换检索评测样本的函数，以及单条检索结果的 metric breakdown |
| 15 | 回答质量评测：正确性、引用一致性、拒答合理性 | 已完成 | `notes/stage9-15-answer-quality-evaluation.md`、`projects/ai-service/app/rag/evaluation.py`、`projects/ai-service/tests/test_rag_evaluation.py`；系统学习最终回答质量为什么要和检索质量分开评测，新增 `RagAnswerQualityResult`、`RagAnswerQualitySummary`、`evaluate_rag_answer_quality` 和 summary/bad case 输出，覆盖正确性、引用一致性、拒答合理性、禁用来源和结构化拒答原因 |
| 16 | Bad Case 分析：怎么定位 RAG 答错的原因 | 未开始 | 建立 RAG 问题排查路径，区分数据、检索、排序、生成和权限问题 |
| 17 | 参数调优：chunk_size、overlap、top_k、score_threshold | 未开始 | 学会用可观察结果调整 RAG 参数，而不是凭感觉乱调 |
| 18 | RAG 缓存、超时、降级和性能优化 | 未开始 | 学习真实服务里 RAG 的响应时间、成本和可用性保护 |
| 19 | RAG 可观测性：记录 query、召回、rerank、引用、耗时 | 未开始 | 给 RAG 链路补齐排查所需日志和指标 |
| 20 | RAG 数据更新：增量入库、删除、重新索引 | 未开始 | 理解知识库文档变化后，向量库和索引如何保持一致 |
| 21 | RAG 多知识库路由 | 未开始 | 学习用户问题应该查哪个知识库，而不是所有资料混在一起检索 |
| 22 | RAG 与 Agent 的组合边界 | 未开始 | 讲清楚 RAG 负责查资料，Agent 负责流程决策和工具编排 |
| 23 | RAG 生产化验收清单：质量、安全、性能、成本、可观测性 | 未开始 | 整理一个真实 RAG 功能上线前应该检查什么 |
| 24 | 阶段 9 总复盘和面试表达强化 | 未开始 | 把阶段 9 的能力整理成项目表达、面试回答和后续学习路线 |

## 近期任务

- [ ] 确认 Python、Java、Docker 环境
- [x] 安装并配置 uv 到 D 盘
- [x] 确认 Python 3.12.3 可用
- [x] 确认 JDK 17 可用
- [x] 安装或配置 Docker（VMware Ubuntu）
- [x] 完成第 1 层：Python 项目环境和 uv 基础练习
- [x] 完成 Python 基础语法第 1 节：变量和基本类型
- [x] 完成 Python 基础语法第 2 节：字符串
- [x] 完成 Python 基础语法第 3 节：列表
- [x] 完成 Python 基础语法第 4 节：字典
- [x] 完成 Python 基础语法第 5 节：条件判断
- [x] 完成 Python 基础语法第 6 节：循环
- [x] 完成 Python 基础语法第 7 节：函数
- [x] 完成 Python 基础语法第 8 节：模块导入
- [x] 完成 Python 基础语法第 9 节：异常处理
- [x] 完成 Python 基础语法第 10 节：文件读写和 JSON
- [x] 完成 Python 基础语法第 11 节：类型提示
- [x] 完成 Python 基础语法第 12 节：类和对象
- [x] 完成 Python 基础语法第 13 节：元组和集合
- [x] 完成 Python 基础语法第 14 节：常用数据处理写法
- [x] 完成 Python 基础语法第 15 节：函数进阶
- [x] 完成 Python 基础语法第 16 节：标准库基础
- [x] 完成 Python 基础语法第 17 节：正则表达式 re
- [x] 完成 Python 基础语法第 18 节：pytest 测试基础
- [x] 完成 Python 基础语法第 19 节：调试和报错阅读
- [x] 完成 Python 基础语法第 20 节：HTTP/API 基础
- [x] 完成 Python 基础语法第 21 节：async/await 异步基础
- [x] 完成 Python 基础综合项目：Learning Task Assistant
- [x] 创建 `projects/ai-service`
- [x] 搭建 FastAPI 基础项目
- [x] 实现 `/health`
- [x] 实现模拟 `/chat` 接口
- [x] 实现 `/stream-chat`
- [x] 加入 `.env` 配置读取
- [x] 加入 trace_id 请求追踪
- [x] 加入统一异常处理
- [x] 加入 CORS 基础配置
- [x] 加入基础日志
- [x] 增加结构化输出练习接口
- [x] 完成阶段 1 第 1 节：Web 服务、HTTP 和 API 是什么
- [x] 完成阶段 1 第 2 节：FastAPI 是什么
- [x] 完成阶段 1 第 3 节：创建 `ai-service` 项目骨架
- [x] 完成阶段 1 第 4 节：FastAPI 最小服务 `/health`
- [x] 完成阶段 1 第 5 节：router 路由拆分
- [x] 完成阶段 1 第 6 节：POST、请求体和 JSON
- [x] 完成阶段 1 第 7 节：Pydantic 请求模型
- [x] 完成阶段 1 第 8 节：Pydantic 响应模型
- [x] 完成阶段 1 第 9 节：模拟 `/chat` 接口
- [x] 完成阶段 1 第 10 节：测试 FastAPI 接口
- [x] 完成阶段 1 第 11 节：`.env` 配置读取
- [x] 完成阶段 1 第 12 节：`logging` 日志
- [x] 完成阶段 1 第 13 节：`trace_id` 请求追踪
- [x] 完成阶段 1 第 14 节：统一异常处理
- [x] 完成阶段 1 第 15 节：CORS 基础
- [x] 完成阶段 1 第 16 节：阶段 1 项目整理
- [x] 完成阶段 2 第 1 节：什么是 LLM API
- [x] 完成阶段 2 第 2 节：API key 和 `.env` 安全配置
- [x] 完成阶段 2 第 3 节：token、上下文窗口、费用基础
- [x] 完成阶段 2 第 4 节：OpenAI-compatible SDK 基础调用方式
- [x] 完成阶段 2 第 5 节：messages 是什么：system / user / assistant
- [x] 完成阶段 2 第 6 节：prompt 基础：怎么写清楚任务
- [x] 完成阶段 2 第 7 节：第一次真实 `/chat` 调用
- [x] 完成阶段 2 第 8 节：多轮对话基础：历史消息怎么传
- [x] 完成阶段 2 第 9 节：timeout 超时
- [x] 完成阶段 2 第 10 节：retry 重试和 rate limit 限流基础
- [x] 完成阶段 2 第 11 节：模型调用错误处理
- [x] 完成阶段 2 第 12 节：模型调用日志：模型名、耗时、trace_id、token
- [x] 完成阶段 2 第 13 节：streaming 流式输出是什么
- [x] 完成阶段 2 第 14 节：FastAPI `StreamingResponse` 实现 `/stream-chat`
- [x] 完成阶段 2 第 15 节：结构化输出是什么
- [x] 完成阶段 2 第 16 节：Pydantic 约束结构化输出
- [x] 完成阶段 2 第 17 节：测试模型调用：mock/fake LLM client
- [x] 完成阶段 2 第 18 节：阶段 2 项目整理
- [x] 完成阶段 3 第 1 节：Tool Calling 是什么
- [x] 完成阶段 3 第 2 节：为什么 AI 不能直接操作业务系统
- [x] 完成阶段 3 第 3 节：工具参数和 JSON Schema
- [x] 完成阶段 3 第 4 节：结构化输出 vs Tool Calling
- [x] 完成阶段 3 第 5 节：用 fake tool 模拟查订单
- [x] 完成阶段 3 第 6 节：工具调用结果也要 Pydantic 校验
- [x] 完成阶段 3 第 7 节：工具调用错误处理：超时、404、500
- [x] 完成阶段 3 第 8 节：工具调用权限边界
- [x] 完成阶段 3 第 9 节：工具调用幂等性
- [x] 完成阶段 3 第 10 节：用 FastAPI 写一个最小 Java mock 业务服务
- [x] 完成阶段 3 第 11 节：Python AI 服务调用 Java mock API
- [x] 完成阶段 3 第 12 节：让模型决定是否调用工具
- [x] 完成阶段 3 第 13 节：工具调用结果再交给模型总结
- [x] 完成阶段 3 第 14 节：用户确认机制：敏感操作不能直接执行
- [x] 完成阶段 3 第 15 节：创建工单流程：提取字段、确认、调用 Java API
- [x] 完成阶段 3 第 16 节：工具调用日志和 trace_id 串联
- [x] 完成阶段 3 第 17 节：工具调用测试：fake Java API / fake tool
- [x] 完成阶段 3 第 18 节：LangChain 是什么，为什么现在才引入
- [x] 完成阶段 3 第 19 节：LangChain ChatModel 基础
- [x] 完成阶段 3 第 20 节：LangChain Tool 基础
- [x] 完成阶段 3 第 21 节：LangChain 结构化输出
- [x] 完成阶段 3 第 22 节：阶段 3 项目整理
- [x] 完成阶段 4 第 1 节：RAG 是什么，为什么大模型需要知识库
- [x] 完成阶段 4 第 2 节：RAG 完整流程
- [x] 完成阶段 4 第 3 节：文档、知识库、chunk、metadata 是什么
- [x] 完成阶段 4 第 4 节：embedding 是什么：文本怎么变成向量
- [x] 完成阶段 4 第 5 节：向量相似度：为什么能用向量找相似内容
- [x] 完成阶段 4 第 6 节：向量数据库是什么，为什么先选 Qdrant
- [x] 完成阶段 4 第 7 节：Qdrant 基础：collection、point、vector、payload
- [x] 完成阶段 4 第 8 节：本地启动 Qdrant 实机验证
- [x] 完成阶段 4 第 9 节：RAG 项目结构设计
- [x] 完成阶段 4 第 10 节：准备第一批 Markdown/txt 知识文档
- [x] 完成阶段 4 第 11 节：文档加载和文本清洗
- [x] 完成阶段 4 第 12 节：chunk 切分策略：大小、重叠、标题、段落
- [x] 完成阶段 4 第 13 节：生成 embedding 并写入 Qdrant
- [x] 完成阶段 4 第 14 节：metadata 设计：source、title、section、权限字段
- [x] 完成阶段 4 第 15 节：基础 top_k 检索
- [x] 完成阶段 4 第 16 节：payload filter：按文档类型、权限、来源过滤
- [x] 完成阶段 4 第 17 节：score_threshold：低相关内容不回答
- [x] 完成阶段 4 第 18 节：把检索结果交给模型回答
- [x] 完成阶段 4 第 19 节：引用来源：回答必须带出处
- [x] 完成阶段 4 第 20 节：无检索结果时怎么处理
- [x] 完成阶段 4 第 21 节：RAG 错误处理：embedding、向量库、模型调用异常
- [x] 完成阶段 4 第 22 节：RAG 测试：fake embedding、fake vector store
- [x] 完成阶段 4 第 23 节：文档更新、删除、重新入库
- [x] 完成阶段 4 第 24 节：embedding 模型选择、维度、成本和批量处理
- [x] 完成阶段 4 第 25 节：检索质量调优：chunk size、overlap、top_k、score_threshold
- [x] 完成阶段 4 第 26 节：混合检索：关键词检索 + 向量检索
- [x] 完成阶段 4 第 27 节：rerank 重排序是什么
- [x] 完成阶段 4 第 28 节：RAG 安全：文档权限、Prompt Injection、敏感信息
- [x] 完成阶段 4 第 29 节：RAG 性能：缓存、批处理、超时、降级
- [x] 完成阶段 4 第 30 节：阶段 4 主线项目验收和复盘
- [x] 完成阶段 4 第 31 节：Milvus 是什么，和 Qdrant 有什么区别
- [x] 完成阶段 4 第 32 节：本地 Docker 启动 Milvus Standalone
- [x] 完成阶段 4 第 33 节：Milvus 核心概念：collection、schema、field、entity、index
- [x] 完成阶段 4 第 34 节：用同一批文档写入 Milvus 并做向量检索
- [x] 完成阶段 4 第 35 节：Milvus metadata/scalar filter 和索引基础
- [x] 完成阶段 4 第 36 节：Qdrant vs Milvus：什么时候选谁
- [x] 完成阶段 4 第 37 节：RAG 检索评测基础
- [x] 完成阶段 4 第 38 节：给当前 RAG 项目做一个最小检索评测脚本
- [x] 完成阶段 4 第 39 节：企业知识库 RAG 最终收尾复盘
- [x] 完成阶段 5 第 1 节：LangGraph 是什么，为什么现在才学
- [x] 完成阶段 5 第 2 节：LangGraph 和 LangChain / 普通函数流程的区别
- [x] 完成阶段 5 第 3 节：Agent 流程和状态机基础
- [x] 完成阶段 5 第 4 节：State 是什么：Agent 为什么需要状态
- [x] 完成阶段 5 第 5 节：Reducer 是什么：状态字段怎么合并
- [x] 完成阶段 5 第 6 节：MessagesState：多轮对话消息怎么保存
- [x] 完成阶段 5 第 7 节：StateGraph 最小图
- [x] 完成阶段 5 第 8 节：node 节点是什么
- [x] 完成阶段 5 第 9 节：edge 边是什么
- [x] 完成阶段 5 第 10 节：conditional edge 条件分支
- [x] 完成阶段 5 第 11 节：START / END 和流程结束
- [x] 完成阶段 5 第 12 节：graph.invoke / graph.stream：普通执行和流式执行
- [x] 完成阶段 5 第 13 节：智能工单 Agent 总流程设计
- [x] 完成阶段 5 第 14 节：意图识别节点
- [x] 完成阶段 5 第 15 节：RAG 知识库回答节点
- [x] 完成阶段 5 第 16 节：判断是否需要创建工单
- [x] 完成阶段 5 第 17 节：工单字段提取节点
- [x] 完成阶段 5 第 18 节：缺失字段追问节点
- [x] 完成阶段 5 第 19 节：用户确认节点
- [x] 完成阶段 5 第 20 节：调用 Java mock 创建工单节点
- [x] 完成阶段 5 第 21 节：checkpoint 和 thread_id
- [x] 完成阶段 5 第 22 节：interrupt / human-in-the-loop
- [x] 完成阶段 5 第 23 节：节点错误处理、fallback 和流程兜底
- [x] 完成阶段 5 第 24 节：LangGraph 日志、trace_id 和可观测性
- [x] 完成阶段 5 第 25 节：LangGraph 测试：fake LLM / fake RAG / fake Java client
- [x] 完成阶段 5 第 26 节：阶段 5 项目整理和面试表达
- [x] 完成阶段 6 第 1 节：Agent 评测基础：为什么 AI 应用不能只靠感觉判断好坏
- [x] 完成阶段 6 第 2 节：什么是 eval：测试和评测的区别
- [x] 完成阶段 6 第 3 节：设计 Agent 测试集
- [x] 完成阶段 6 第 4 节：意图识别评测
- [x] 完成阶段 6 第 5 节：工单字段提取评测
- [x] 完成阶段 6 第 6 节：Agent 路由评测
- [x] 完成阶段 6 第 7 节：RAG + Agent 组合评测
- [x] 完成阶段 6 第 8 节：评测脚本设计
- [x] 完成阶段 6 第 9 节：评测报告
- [x] 完成阶段 6 第 10 节：坏例分析
- [x] 完成阶段 6 第 11 节：回归评测
- [x] 完成阶段 6 第 12 节：evaluator 类型
- [x] 完成阶段 6 第 13 节：真实 LLM 意图识别节点
- [x] 完成阶段 6 第 14 节：真实 LLM 字段提取节点
- [x] 完成阶段 6 第 15 节：Pydantic 校验模型输出
- [x] 完成阶段 6 第 16 节：fake LLM 和真实 LLM 双模式
- [x] 完成阶段 6 第 17 节：prompt 版本管理
- [x] 完成阶段 6 第 18 节：模型输出失败处理
- [x] 完成阶段 6 第 19 节：接入真实 `query_order` 到 LangGraph
- [x] 完成阶段 6 第 20 节：工具节点错误处理升级
- [x] 完成阶段 6 第 21 节：工具权限和写操作安全回归
- [x] 完成阶段 6 第 22 节：持久化 checkpoint 基础
- [x] 完成阶段 6 第 23 节：checkpoint 存储选型
- [x] 完成阶段 6 第 24 节：thread_id 生命周期
- [x] 完成阶段 6 第 25 节：会话过期与清理
- [x] 完成阶段 6 第 26 节：LangSmith tracing 基础
- [x] 完成阶段 6 第 27 节：OpenTelemetry 基础
- [x] 完成阶段 6 第 28 节：trace/span/log/metrics 的关系
- [x] 完成阶段 6 第 29 节：生产日志字段设计
- [x] 完成阶段 6 第 30 节：成本、token 和延迟指标
- [x] 完成阶段 6 第 31 节：timeout 超时策略
- [x] 完成阶段 6 第 32 节：retry 重试策略
- [x] 完成阶段 6 第 33 节：rate limit、circuit breaker 和降级
- [x] 完成阶段 6 第 34 节：Docker Compose 本地编排
- [x] 完成阶段 6 第 35 节：health check、readiness 和 CI 自动回归
- [x] 完成阶段 6 第 36 节：阶段 6 项目整理和面试表达
- [x] 写 FastAPI 项目结构学习笔记

## 阶段 1 细化学习清单

学习状态和代码状态分开看。即使代码已经提前搭好，学习上也按下面顺序重新讲透。

| 节 | 主题 | 学习状态 | 对应产出 |
| --- | --- | --- | --- |
| 1 | Web 服务、HTTP 和 API 是什么 | 已完成 | `notes/fastapi-stage1-01-web-http-api.md` |
| 2 | FastAPI 是什么 | 已完成 | `notes/fastapi-stage1-02-what-is-fastapi.md` |
| 3 | 创建 `projects/ai-service` 项目骨架 | 已完成 | `notes/fastapi-stage1-03-ai-service-project-skeleton.md` |
| 4 | FastAPI 最小服务 `/health` | 已完成 | `notes/fastapi-stage1-04-health-endpoint.md` |
| 5 | router 路由拆分 | 已完成 | `notes/fastapi-stage1-05-router-splitting.md` |
| 6 | POST、请求体和 JSON | 已完成 | `notes/fastapi-stage1-06-post-body-json.md` |
| 7 | Pydantic 请求模型 | 已完成 | `notes/fastapi-stage1-07-pydantic-request-model.md`、`app/schemas/chat.py`、`tests/test_chat_schema.py` |
| 8 | Pydantic 响应模型 | 已完成 | `notes/fastapi-stage1-08-pydantic-response-model.md`、`app/schemas/chat.py`、`tests/test_chat_schema.py` |
| 9 | 模拟 `/chat` 接口 | 已完成 | `notes/fastapi-stage1-09-mock-chat-endpoint.md`、`app/routers/chat.py`、`tests/test_chat_api.py` |
| 10 | 测试 FastAPI 接口 | 已完成 | `notes/fastapi-stage1-10-testing-fastapi-apis.md`、`tests/conftest.py`、`tests/test_health.py`、`tests/test_chat_api.py` |
| 11 | `.env` 配置读取 | 已完成 | `notes/fastapi-stage1-11-env-config.md`、`.env.example`、`app/core/config.py`、`tests/test_config.py` |
| 12 | `logging` 日志 | 已完成 | `notes/fastapi-stage1-12-logging.md`、`app/core/logging.py`、`tests/test_logging.py` |
| 13 | `trace_id` 请求追踪 | 已完成 | `notes/fastapi-stage1-13-trace-id.md`、`app/core/trace.py`、`app/middleware/tracing.py`、`tests/test_trace.py` |
| 14 | 统一异常处理 | 已完成 | `notes/fastapi-stage1-14-exception-handling.md`、`app/core/exception_handlers.py`、`app/core/exceptions.py`、`app/schemas/error.py`、`tests/test_exception_handlers.py` |
| 15 | CORS 基础 | 已完成 | `notes/fastapi-stage1-15-cors.md`、`app/core/cors.py`、`tests/test_cors.py`、`.env.example` |
| 16 | 阶段 1 项目整理 | 已完成 | `notes/fastapi-stage1-16-project-summary.md`、`projects/ai-service/README.md`、测试检查 |

## 阶段 2 细化学习清单

阶段 2 目标：把当前 mock `/chat` 逐步变成真实大模型调用，并补齐 API key、安全、token、prompt、超时、重试、日志、流式输出、结构化输出和测试基础。

| 节 | 主题 | 学习状态 | 对应产出 |
| --- | --- | --- | --- |
| 1 | 什么是 LLM API | 已完成 | `notes/llm-api-stage2-01-what-is-llm-api.md` |
| 2 | API key 和 `.env` 安全配置 | 已完成 | `notes/llm-api-stage2-02-api-key-env-security.md`、`app/core/config.py`、`tests/test_config.py` |
| 3 | token、上下文窗口、费用基础 | 已完成 | `notes/llm-api-stage2-03-token-context-cost.md`、`app/core/token_usage.py`、`tests/test_token_usage.py`、`.env.example` |
| 4 | OpenAI-compatible SDK 基础调用方式 | 已完成 | `notes/llm-api-stage2-04-openai-compatible-sdk.md`、`app/services/llm_client.py`、`tests/test_llm_client.py`、`scripts/llm_compatible_smoke_test.py` |
| 5 | messages 是什么：system / user / assistant | 已完成 | `notes/llm-api-stage2-05-messages-roles.md`、`app/schemas/chat.py`、`app/services/message_builder.py`、`tests/test_message_builder.py` |
| 6 | prompt 基础：怎么写清楚任务 | 已完成 | `notes/llm-api-stage2-06-prompt-basics.md`、`app/services/prompt_builder.py`、`tests/test_prompt_builder.py` |
| 7 | 第一次真实 `/chat` 调用 | 已完成 | `notes/llm-api-stage2-07-real-chat-call.md`、`app/services/llm_service.py`、`app/routers/chat.py`、`tests/test_llm_service.py`、`tests/test_chat_api.py` |
| 8 | 多轮对话基础：历史消息怎么传 | 已完成 | `notes/llm-api-stage2-08-multi-turn-history.md`、`ChatRequest.history`、`LLMChatService.generate_reply(..., history=...)`、多轮对话测试 |
| 9 | 超时 timeout | 已完成 | `notes/llm-api-stage2-09-timeout.md`、`APITimeoutError` -> `LLM_TIMEOUT`、504 接口测试 |
| 10 | 重试 retry 和限流 rate limit 基础 | 已完成 | `notes/llm-api-stage2-10-retry-rate-limit.md`、`LLM_MAX_RETRIES`、`RateLimitError` -> `LLM_RATE_LIMITED` |
| 11 | 模型调用错误处理 | 已完成 | `notes/llm-api-stage2-11-model-error-handling.md`、`map_openai_error_to_app_exception`、常见 SDK 错误映射测试 |
| 12 | 模型调用日志：模型名、耗时、trace_id、token | 已完成 | `notes/llm-api-stage2-12-llm-call-logging.md`、`LLMTokenUsage`、`extract_token_usage`、成功/失败调用日志测试 |
| 13 | streaming 流式输出是什么 | 已完成 | `notes/llm-api-stage2-13-streaming-concept.md`、普通响应/流式响应、chunk、SSE、`StreamingResponse` 概念 |
| 14 | FastAPI `StreamingResponse` 实现 `/stream-chat` | 已完成 | `notes/llm-api-stage2-14-stream-chat-endpoint.md`、`/stream-chat`、SSE `message/done/error`、流式 service/router 测试 |
| 15 | 结构化输出是什么 | 已完成 | `notes/llm-api-stage2-15-structured-output-concept.md`、JSON Mode、Structured Outputs、JSON Schema、Pydantic 校验概念 |
| 16 | Pydantic 约束结构化输出 | 已完成 | `notes/llm-api-stage2-16-pydantic-structured-output.md`、`/extract-ticket`、`TicketExtraction`、JSON Mode、Pydantic 输出校验 |
| 17 | 测试模型调用：mock/fake LLM client | 已完成 | `notes/llm-api-stage2-17-testing-model-calls.md`、`tests/fakes.py`、`tests/test_fake_llm_client.py`、fake client 复用 |
| 18 | 阶段 2 项目整理 | 已完成 | `notes/llm-api-stage2-18-project-summary.md`、模型参数基础、OpenAI-compatible 差异、调用链路复盘、阶段验收 |

## 阶段 3 细化学习清单

阶段 3 目标：让 Python AI 服务具备工具调用能力，并逐步接入 Java 业务服务。先讲清楚 Tool Calling 的底层流程，再引入 LangChain 的封装。

| 节 | 主题 | 学习状态 | 对应产出 |
| --- | --- | --- | --- |
| 1 | Tool Calling 是什么 | 已完成 | `notes/tool-calling-stage3-01-what-is-tool-calling.md` |
| 2 | 为什么 AI 不能直接操作业务系统 | 已完成 | `notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md` |
| 3 | 工具参数和 JSON Schema | 已完成 | `notes/tool-calling-stage3-03-tool-parameters-json-schema.md` |
| 4 | 结构化输出 vs Tool Calling | 已完成 | `notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md` |
| 5 | 用 fake tool 模拟查订单 | 已完成 | `notes/tool-calling-stage3-05-fake-query-order-tool.md`、`app/tools/fake_order_tool.py`、`app/schemas/tool.py`、`app/routers/tools.py`、`tests/test_fake_order_tool.py`、`tests/test_tools_api.py`、`tests/test_tool_schema.py` |
| 6 | 工具调用结果也要 Pydantic 校验 | 已完成 | `notes/tool-calling-stage3-06-tool-result-pydantic-validation.md`、`validate_query_order_result()`、`QueryOrderResult.model_validate(...)`、`TOOL_RESULT_VALIDATION_FAILED` |
| 7 | 工具调用错误处理：超时、404、500 | 已完成 | `notes/tool-calling-stage3-07-tool-error-handling.md`、`FakeOrderServiceTimeoutError`、`FakeOrderServiceError`、`map_query_order_error()`、`TOOL_TIMEOUT`、`TOOL_UPSTREAM_ERROR`、`TOOL_CALL_FAILED` |
| 8 | 工具调用权限边界 | 已完成 | `notes/tool-calling-stage3-08-tool-permission-boundary.md`、`ToolDefinition`、`ToolAccessLevel`、`TOOL_REGISTRY`、`authorize_tool_call()`、`TOOL_NOT_ALLOWED`、`TOOL_CONFIRMATION_REQUIRED` |
| 9 | 工具调用幂等性 | 已完成 | `notes/tool-calling-stage3-09-tool-idempotency.md`、`Idempotency-Key`、`run_idempotent_tool()`、`build_arguments_fingerprint()`、`IDEMPOTENCY_KEY_CONFLICT`、`IDEMPOTENCY_KEY_INVALID` |
| 10 | 用 FastAPI 写一个最小 Java mock 业务服务 | 已完成 | `notes/tool-calling-stage3-10-java-mock-service.md`、`projects/java-mock-service`、`GET /health`、`GET /orders/{order_id}`、`ORDER_NOT_FOUND`、`ORDER_SERVICE_ERROR` |
| 11 | Python AI 服务调用 Java mock API | 已完成 | `notes/tool-calling-stage3-11-python-calls-java-mock-api.md`、`app/services/java_order_client.py`、`JAVA_MOCK_SERVICE_BASE_URL`、`JAVA_MOCK_SERVICE_TIMEOUT_SECONDS`、`httpx.MockTransport`、`map_java_order_to_query_order_payload()`、`source=java_mock_service` |
| 12 | 让模型决定是否调用工具 | 已完成 | `notes/tool-calling-stage3-12-model-decides-tool-call.md`、`app/services/tool_decision_service.py`、`app/schemas/tool_decision.py`、`POST /tool-decision`、`tools=...`、`tool_choice="auto"`、`tool_calls`、`QueryOrderArgs.model_validate(arguments)` |
| 13 | 工具调用结果再交给模型总结 | 已完成 | `notes/tool-calling-stage3-13-tool-result-model-summary.md`、`app/services/tool_calling_chat_service.py`、`POST /tool-chat`、assistant tool-call message、`tool_call_id`、tool message、第二轮模型总结、`TOOL_CALL_ID_MISSING` |
| 14 | 用户确认机制：敏感操作不能直接执行 | 已完成 | `notes/tool-calling-stage3-14-user-confirmation.md`、`ToolConfirmationService`、`ToolConfirmationStore`、`POST /tools/confirmations`、确认 ID、操作者/参数绑定、参数指纹、TTL 过期、确认幂等 |
| 15 | 创建工单流程：提取字段、确认、调用 Java API | 已完成 | `notes/tool-calling-stage3-15-ticket-creation-workflow.md`、`CreateTicketArgs`、`TicketWorkflowService`、`JavaTicketClient`、`POST /tickets/plans`、`POST /tickets/confirmations/{confirmation_id}/execute`、Java mock `POST /tickets`、确认计划消费、写操作幂等 |
| 16 | 工具调用日志和 trace_id 串联 | 已完成 | `notes/tool-calling-stage3-16-tool-logging-trace-id.md`、`build_trace_headers()`、出站 `X-Trace-Id`、`java_order_request_*`、`java_ticket_create_*`、`tool_execution_*`、`ticket_execution_*`、敏感字段不入日志 |
| 17 | 工具调用测试：fake Java API / fake tool | 已完成 | `notes/tool-calling-stage3-17-tool-testing-fakes.md`、`tests/tool_fakes.py`、`tests/test_tool_fakes.py`、`FakeOrderLookupClient`、`FakeTicketExtractor`、`FakeTicketCreator`、`httpx.MockTransport`、`dependency_overrides`、service/client/router 分层测试 |
| 18 | LangChain 是什么，为什么现在才引入 | 已完成 | `notes/tool-calling-stage3-18-what-is-langchain.md`、LangChain 定位、框架/库/抽象/编排、LangChain vs LangGraph vs LangSmith、SDK vs LangChain vs LangGraph、当前项目模块和 LangChain 概念映射 |
| 19 | LangChain ChatModel 基础 | 已完成 | `notes/tool-calling-stage3-19-langchain-chatmodel-basics.md`、`langchain-openai`、`ChatOpenAI`、`SystemMessage`、`HumanMessage`、`AIMessage`、`model.invoke()`、`LangChainChatModelService`、`POST /langchain-chat`、ChatModel 与 OpenAI-compatible SDK 对比 |
| 20 | LangChain Tool 基础 | 已完成 | `notes/tool-calling-stage3-20-langchain-tool-basics.md`、`app/tools/langchain_tools.py`、`StructuredTool.from_function()`、`QueryOrderArgs` 作为 `args_schema`、`GET /tools/langchain`、`POST /tools/langchain/query-order`、LangChain Tool 与项目 `ToolDefinition` 边界 |
| 21 | LangChain 结构化输出 | 已完成 | `notes/tool-calling-stage3-21-langchain-structured-output.md`、`app/services/langchain_structured_output_service.py`、`POST /langchain-extract-ticket`、`with_structured_output(TicketExtraction, method="json_mode")`、LangChain 结构化输出与原生 JSON Mode 对比 |
| 22 | 阶段 3 项目整理 | 已完成 | `notes/tool-calling-stage3-22-project-summary.md`、阶段 3 总图、接口地图、核心调用链路、Python AI 服务和 Java mock 服务分工、原生 SDK 与 LangChain 对比、阶段验收清单、阶段 4 RAG 衔接 |

## 阶段 4 细化学习清单

阶段 4 目标：完成企业知识库 RAG 基础，理解文档如何变成可检索知识，先用 Qdrant 跑通主线，再补 RAG 工程优化、Milvus 对比和检索评测。当前阶段 4 已完成，后续进入阶段 5 LangGraph 智能工单 Agent。

| 节 | 主题 | 学习状态 | 对应产出 |
| --- | --- | --- | --- |
| 1 | RAG 是什么，为什么大模型需要知识库 | 已完成 | `notes/rag-stage4-01-what-is-rag.md`、RAG 概念、普通聊天/prompt/微调/Tool Calling/RAG 对比、阶段 4 学习地图 |
| 2 | RAG 完整流程：load -> split -> embed -> store -> retrieve -> generate | 已完成 | `notes/rag-stage4-02-rag-pipeline.md`、文档入库流水线、用户问答流水线、每一步输入输出、失败后果、后续代码落点 |
| 3 | 文档、知识库、chunk、metadata 是什么 | 已完成 | `notes/rag-stage4-03-documents-chunks-metadata.md`、document/knowledge base/chunk/metadata 概念、vector/content/metadata 职责、metadata 字段设计、chunk_id 设计 |
| 4 | embedding 是什么：文本怎么变成向量 | 已完成 | `notes/rag-stage4-04-what-is-embedding.md`、embedding 概念、关键词匹配 vs 语义检索、chunk embedding、query embedding、embedding 维度、embedding 局限 |
| 5 | 向量相似度：为什么能用向量找相似内容 | 已完成 | `notes/rag-stage4-05-vector-similarity.md`、similarity/distance、cosine similarity、dot product、top_k、score_threshold、相似度边界 |
| 6 | 向量数据库是什么，为什么先选 Qdrant | 已完成 | `notes/rag-stage4-06-vector-database-qdrant.md`、向量数据库定位、collection/point/vector/payload/search/filter 基础、Qdrant 优先原因、Qdrant 与 Milvus 学习顺序 |
| 7 | Qdrant 基础：collection、point、vector、payload | 已完成 | `notes/rag-stage4-07-qdrant-core-concepts.md`、collection/point/id/vector/payload、chunk 到 point 映射、payload 字段设计、score 查询语义 |
| 8 | 本地启动 Qdrant | 已完成 | `notes/rag-stage4-08-start-qdrant-locally.md`、VMware Ubuntu Docker、Qdrant 1.18.2、端口映射、数据持久化、Windows 访问 `http://192.168.88.10:6333` 已验证 |
| 9 | RAG 项目结构设计 | 已完成 | `notes/rag-stage4-09-rag-project-structure.md`、`projects/ai-service/app/rag`、`RagDocument`、`RagChunk`、RAG 模块边界、入库流程和问答流程拆分 |
| 10 | 准备第一批 Markdown/txt 知识文档 | 已完成 | `notes/rag-stage4-10-first-knowledge-documents.md`、`projects/ai-service/data/knowledge_base`、订单发货/退款退货/物流查询/账号安全示例文档、metadata 线索、示例文档存在性测试 |
| 11 | 文档加载和文本清洗 | 已完成 | `notes/rag-stage4-11-document-loading-cleaning.md`、`projects/ai-service/app/rag/loaders.py`、Markdown/txt 加载、UTF-8 读取、基础文本清洗、title/metadata 提取、目录批量加载、loader 测试 |
| 12 | chunk 切分策略：大小、重叠、标题、段落 | 已完成 | `notes/rag-stage4-12-chunk-splitting.md`、`projects/ai-service/app/rag/splitters.py`、段落优先切分、标题感知、chunk_size、chunk_overlap、稳定 chunk_id、section metadata、splitter 测试 |
| 13 | 生成 embedding 并写入 Qdrant | 已完成 | `notes/rag-stage4-13-embedding-qdrant-ingestion.md`、`app/rag/embeddings.py`、`app/rag/vector_store.py`、`app/rag/ingestion.py`、`scripts/rag_ingest_smoke.py` |
| 14 | metadata 设计：source、title、section、权限字段 | 已完成 | `notes/rag-stage4-14-metadata-design.md`、`app/rag/metadata.py`、metadata 标准化、必备字段校验、Qdrant payload 白名单、权限字段边界、metadata 测试 |
| 15 | 基础 top_k 检索 | 已完成 | `notes/rag-stage4-15-basic-top-k-retrieval.md`、`app/rag/retriever.py`、`QdrantVectorStore.query_similar()`、`scripts/rag_retrieve_smoke.py`、query embedding、top_k、score、检索结果解析、retriever 测试 |
| 16 | payload filter：按文档类型、权限、来源过滤 | 已完成 | `notes/rag-stage4-16-payload-filter.md`、`app/rag/filters.py`、`QdrantVectorStore.query_similar(payload_filter=...)`、`retrieve_top_k()` 过滤参数、`permission_group/business_domain/doc_type/source`、payload filter 测试 |
| 17 | score_threshold：低相关内容不回答 | 已完成 | `notes/rag-stage4-17-score-threshold.md`、`retrieve_top_k(score_threshold=...)`、`QdrantVectorStore.query_similar(score_threshold=...)`、Qdrant Query API `score_threshold` 请求体、低相关结果过滤测试 |
| 18 | 把检索结果交给模型回答 | 已完成 | `notes/rag-stage4-18-retrieved-context-to-model-answer.md`、`app/rag/generator.py`、`RagAnswerService`、`build_rag_messages()`、检索资料上下文构造、无资料不调用模型、fake LLM 测试 |
| 19 | 引用来源：回答必须带出处 | 已完成 | `notes/rag-stage4-19-citations.md`、`RagCitation`、`RagAnswer`、`build_rag_citation()`、`build_rag_citations()`、后端根据 retrieved chunks 生成结构化 citations、空结果不伪造出处、fake LLM 测试 |
| 20 | 无检索结果时怎么处理 | 已完成 | `notes/rag-stage4-20-no-context-handling.md`、`RagAnswerStatus`、`RagNoContextReason`、`build_no_context_rag_answer()`、`build_grounded_rag_answer()`、结构化 `no_context` 状态、无资料 suggestions、无资料不调用模型 |
| 21 | RAG 错误处理：embedding、向量库、模型调用异常 | 已完成 | `notes/rag-stage4-21-error-handling.md`、`app/rag/errors.py`、`RAG_EMBEDDING_FAILED`、`RAG_EMBEDDING_BAD_RESPONSE`、`RAG_VECTOR_STORE_FAILED`、`RAG_VECTOR_STORE_CONFIG_ERROR`、retriever/ingestion 错误映射测试 |
| 22 | RAG 测试：fake embedding、fake vector store | 已完成 | `notes/rag-stage4-22-rag-testing-fakes.md`、`tests/rag_fakes.py`、`FakeEmbeddingModel`、`FakeVectorStoreReader`、`FakeVectorStoreWriter`、`make_retrieved_chunk()`、RAG 测试分层、fake 工具测试 |
| 23 | 文档更新、删除、重新入库 | 已完成 | `notes/rag-stage4-23-document-update-delete-reingest.md`、`QdrantVectorStore.delete_points_by_filter()`、`VectorStoreUpdater`、`delete_document_from_vector_store()`、`refresh_directory_in_vector_store()`、按 `source` 删除旧 chunks、重新入库前清理旧 points、fake 删除测试 |
| 24 | embedding 模型选择、维度、成本和批量处理 | 已完成 | `notes/rag-stage4-24-embedding-model-dimension-cost-batch.md`、`OpenAICompatibleEmbeddingModel`、独立 embedding 配置、`EMBEDDING_MODEL`、`EMBEDDING_DIMENSION`、`EMBEDDING_BATCH_SIZE`、`split_texts_into_batches()`、`estimate_dense_vector_storage_bytes()`、真实 embedding 适配器测试 |
| 25 | 检索质量调优：chunk size、overlap、top_k、score_threshold | 已完成 | `notes/rag-stage4-25-retrieval-quality-tuning.md`、`app/rag/tuning.py`、`ChunkTuningCase`、`ChunkTuningReport`、`RetrievalTuningCase`、`RetrievalTuningReport`、`rag_chunk_tuning_preview.py`、chunk 分布观察、top_k/score_threshold 调优报告 |
| 26 | 混合检索：关键词检索 + 向量检索 | 已完成 | `notes/rag-stage4-26-hybrid-search.md`、`app/rag/hybrid.py`、`SimpleKeywordRetriever`、`KeywordSearchResult`、`HybridSearchResult`、`HybridSearchWeights`、`extract_keyword_terms()`、`fuse_hybrid_results()`、`hybrid_retrieve()`、`rag_keyword_search_preview.py`、关键词召回、向量召回、去重、分数归一化和加权融合 |
| 27 | rerank 重排序是什么 | 已完成 | `notes/rag-stage4-27-rerank.md`、`app/rag/rerank.py`、`RerankCandidate`、`RerankedChunk`、`RerankScoreBreakdown`、`RuleBasedReranker`、`rerank_candidates()`、`reranked_chunks_to_retrieved_chunks()`、`rag_rerank_preview.py`、召回后重排序、原始排名/重排排名、分数拆解、规则 reranker |
| 28 | RAG 安全：文档权限、Prompt Injection、敏感信息 | 已完成 | `notes/rag-stage4-28-rag-security.md`、`app/rag/security.py`、`RagSecurityPolicy`、`RagSecurityFinding`、`RagSecurityReport`、`inspect_retrieved_chunks()`、`inspect_chunk_security()`、`rag_security_preview.py`、权限复查、Prompt Injection 检测、敏感信息识别、safe chunks 过滤和 findings 报告 |
| 29 | RAG 性能：缓存、批处理、超时、降级 | 已完成 | `notes/rag-stage4-29-rag-performance.md`、`app/rag/performance.py`、`RagCacheKey`、`InMemoryTtlCache`、`RagBatchPlan`、`RagOperationTiming`、`RagDegradationDecision`、`build_retrieval_cache_key()`、`build_batch_plan()`、`assess_operation_timing()`、`choose_degradation_decision()`、`rag_performance_preview.py`、缓存 key、TTL、batch、near_timeout、降级决策 |
| 30 | 阶段 4 主线项目验收和复盘 | 已完成 | `notes/rag-stage4-30-project-summary.md`、阶段 4 RAG 主线地图、入库流水线、问答流水线、模块职责、学习版/生产级差距、验收清单、面试口述版、Milvus 衔接 |
| 31 | Milvus 是什么，和 Qdrant 有什么区别 | 已完成 | `notes/rag-stage4-31-milvus-vs-qdrant.md`、Milvus/Qdrant 概念对比、collection/point/entity/schema/field/payload/scalar field 映射、向量库选型问题、误区、面试表达 |
| 32 | 本地 Docker 启动 Milvus Standalone | 已完成 | `notes/rag-stage4-32-start-milvus-standalone-locally.md`、Docker Compose 基础、Milvus Standalone/etcd/MinIO 职责、端口 `19530/9091`、启动/停止/删除数据区别、`volumes/milvus` 权限问题排查、VMware Ubuntu Docker 实机验证、Windows 访问 WebUI 已验证 |
| 33 | Milvus 核心概念：collection、schema、field、entity、index | 已完成 | `notes/rag-stage4-33-milvus-core-concepts.md`、collection/schema/field/entity/index 概念、primary key/vector field/scalar field、RAG chunk 到 Milvus schema 映射、Qdrant/Milvus 概念对照、练习和自测 |
| 34 | 用同一批文档写入 Milvus 并做向量检索 | 已完成 | `notes/rag-stage4-34-milvus-ingestion-search.md`、`app/rag/milvus_store.py`、`scripts/rag_milvus_smoke.py`、Milvus schema/index 创建、entity upsert、flush-on-wait、filter expression、PyMilvus search、VMware Milvus 实机 smoke |
| 35 | Milvus metadata/scalar filter 和索引基础 | 已完成 | `notes/rag-stage4-35-milvus-metadata-scalar-filter-index.md`、`MilvusVectorStore.ensure_scalar_indexes()`、`INVERTED` scalar index、`match.any`、`range`、`should`、`must_not`、`scripts/rag_milvus_filter_smoke.py`、VMware Milvus 实机 filter/index smoke |
| 36 | Qdrant vs Milvus：什么时候选谁 | 已完成 | `notes/rag-stage4-36-qdrant-vs-milvus-selection.md`、Qdrant/Milvus 数据模型对照、部署复杂度、filter/index、规模、运维、成本、团队能力和项目阶段选型框架 |
| 37 | RAG 检索评测基础 | 已完成 | `notes/rag-stage4-37-rag-retrieval-evaluation-basics.md`、评测集、query/expected source/section/chunk、Hit Rate@K、Recall@K、Precision@K、MRR、bad case 分析、当前项目最小评测集设计 |
| 38 | 给当前 RAG 项目做一个最小检索评测脚本 | 已完成 | `notes/rag-stage4-38-rag-retrieval-evaluation-script.md`、`app/rag/evaluation.py`、`data/rag_eval/retrieval_cases.json`、`scripts/rag_retrieval_eval.py`、固定评测样本、match_level、Hit Rate@K、Recall@K、Precision@K、MRR、no-result case、bad case 报告 |
| 39 | 企业知识库 RAG 最终收尾复盘 | 已完成 | `notes/rag-stage4-39-final-review.md`、阶段 4 总学习地图、入库链路、问答链路、模块职责、Qdrant/Milvus 选型、检索质量、安全、性能、评测、生产级差距、阶段 5 LangGraph 衔接 |

## 阶段 5 细化学习清单

阶段 5 目标：完成智能工单 Agent v1。这个阶段不是只学 LangGraph API，而是把 FastAPI AI 服务、LLM API、Tool Calling、Java mock 业务服务、用户确认机制和 RAG 知识库组织成一个可控、可测试、可恢复的 Agent 流程。阶段 5 主线固定为 26 节，后续不要压缩成 16 或 22 节；Agent 评测、LangSmith tracing、Docker Compose、前端工作台等更生产化内容放到阶段 6。

| 节 | 主题 | 学习状态 | 对应产出 |
| --- | --- | --- | --- |
| 1 | LangGraph 是什么，为什么现在才学 | 已完成 | `notes/langgraph-stage5-01-what-is-langgraph.md`、LangGraph 定位、为什么现在才学、LangGraph/LangChain/普通函数流程边界、Agent/state/node/edge/conditional edge/checkpoint/thread_id/interrupt/human-in-the-loop 基础认知、阶段 5 路线 |
| 2 | LangGraph 和 LangChain / 普通函数流程的区别 | 已完成 | `notes/langgraph-stage5-02-langgraph-vs-langchain-function-flow.md`、普通函数 / service、LangChain、LangGraph 三层分工、workflow 与 agent 区别、智能工单 Agent 架构边界 |
| 3 | Agent 流程和状态机基础 | 已完成 | `notes/langgraph-stage5-03-agent-flow-state-machine-basics.md`、流程、状态、状态机、事件、转移、动作、守卫条件、副作用、HTTP 无状态与 Agent 有状态、智能工单 Agent 初版状态机 |
| 4 | State 是什么：Agent 为什么需要状态 | 已完成 | `notes/langgraph-stage5-04-state-agent-needs-state.md`、State 定义、State 与变量/messages/请求体/响应体区别、State schema、TypedDict/Pydantic/dataclass 选择、智能工单 Agent 初版 State 设计 |
| 5 | Reducer 是什么：状态字段怎么合并 | 已完成 | `notes/langgraph-stage5-05-reducer-state-merge.md`、默认覆盖、自定义 reducer、left/right、Annotated、operator.add、messages 追加、ticket_fields 字典合并、并行更新冲突 |
| 6 | MessagesState：多轮对话消息怎么保存 | 已完成 | `notes/langgraph-stage5-06-messages-state.md`、messages、SystemMessage/HumanMessage/AIMessage/ToolMessage、user_message 与 messages 区别、add_messages、MessagesState、消息历史与结构化 State 分工 |
| 7 | StateGraph 最小图 | 已完成 | `notes/langgraph-stage5-07-stategraph-minimal-graph.md`、`app/agents/minimal_graph.py`、`scripts/langgraph_minimal_graph_smoke.py`、`tests/test_langgraph_minimal_graph.py`、langgraph 依赖、START/END、add_node、add_edge、compile、invoke |
| 8 | node 节点是什么 | 已完成 | `notes/langgraph-stage5-08-what-is-node.md`、`classify_message_node`、node 单一职责、局部 State 更新、node 命名、node 粒度、node 测试、副作用和幂等性 |
| 9 | edge 边是什么 | 已完成 | `notes/langgraph-stage5-09-what-is-edge.md`、`MINIMAL_GRAPH_EDGES`、固定 edge、START/END 入口出口、add_edge、edge 和 node 区别、固定边适用场景 |
| 10 | conditional edge 条件分支 | 已完成 | `notes/langgraph-stage5-10-conditional-edge.md`、`MessageRoute`、`MINIMAL_GRAPH_CONDITIONAL_ROUTES`、`route_by_message_status`、`add_conditional_edges`、path map、ready/blank 分支、条件边测试 |
| 11 | START / END 和流程结束 | 已完成 | `notes/langgraph-stage5-11-start-end-flow-finish.md`、`MessageStatus`、`stop -> END`、`START` 虚拟入口、`END` 虚拟终点、入口边、结束边、条件分支直接终止、`/stop` 路线测试 |
| 12 | graph.invoke / graph.stream：普通执行和流式执行 | 已完成 | `notes/langgraph-stage5-12-invoke-stream.md`、`build_minimal_graph_input`、`run_minimal_graph`、`stream_minimal_graph_updates`、`stream_minimal_graph_values`、`stream_mode="updates"`、`stream_mode="values"`、`version="v2"`、invoke 与 stream 对比 |
| 13 | 智能工单 Agent 总流程设计 | 已完成 | `notes/langgraph-stage5-13-ticket-agent-overall-design.md`、智能工单 Agent v1 业务边界、主路线、State 设计、节点设计、edge/conditional edge 设计、确认机制、RAG/订单/工单路线、后续 14-22 节实现顺序 |
| 14 | 意图识别节点 | 已完成 | `notes/langgraph-stage5-14-intent-classification-node.md`、`app/agents/ticket_agent.py`、`TicketIntent`、`TicketAgentState`、`classify_ticket_intent`、`classify_intent_node`、`route_by_intent`、`TICKET_AGENT_INTENT_ROUTES`、六类 intent、占位业务路线、stream 路由测试 |
| 15 | RAG 知识库回答节点 | 已完成 | `notes/langgraph-stage5-15-rag-policy-node.md`、`app/agents/ticket_agent.py`、`PolicyRagService`、`FakePolicyRagService`、`retrieve_policy_node`、`rag_query`、`rag_answer_status`、`rag_citations`、`rag_no_context_reason`、`rag_suggestions`、有资料回答、无资料兜底、完整图和 stream 测试 |
| 16 | 判断是否需要创建工单 | 已完成 | `notes/langgraph-stage5-16-decide-ticket-need.md`、`TicketNeedRoute`、`TicketNeedSource`、`TicketNeedDecision`、`decide_ticket_need`、`decide_ticket_need_node`、`route_by_ticket_need`、`needs_ticket`、`ticket_need_reason`、`ticket_need_source`、RAG answered 不建工单、RAG no_context 进入工单流程、明确投诉进入工单流程 |
| 17 | 工单字段提取节点 | 已完成 | `notes/langgraph-stage5-17-ticket-field-extraction-node.md`、`TicketFields`、`TicketIssueType`、`TicketUrgencyLevel`、`extract_ticket_fields`、`find_missing_ticket_fields`、`extract_ticket_fields_node`、`ticket_fields`、`missing_ticket_fields`、`ticket_fields_complete`、规则抽取订单号/问题类型/诉求/紧急程度、policy_gap、字段完整和缺失测试 |
| 18 | 缺失字段追问节点 | 已完成 | `notes/langgraph-stage5-18-missing-field-follow-up-node.md`、`TicketFieldCompletionRoute`、`TICKET_AGENT_FIELD_COMPLETION_ROUTES`、`route_by_ticket_fields_complete`、`build_missing_ticket_fields_question`、`ask_missing_ticket_fields_node`、`missing_ticket_field_question`、`missing_ticket_field_question_fields`、字段缺失进入追问、字段完整不追问、stream 追问节点测试 |
| 19 | 用户确认节点 | 已完成 | `notes/langgraph-stage5-19-ticket-confirmation-node.md`、`TicketConfirmationStatus`、`PendingTicketConfirmation`、`ticket_confirmation_required`、`ticket_confirmation_message`、`pending_ticket_confirmation`、`build_ticket_confirmation_id`、`build_ticket_confirmation_message`、`build_pending_ticket_confirmation`、`request_ticket_confirmation_node`、字段完整进入确认、字段缺失仍追问、待确认工单和 stream 确认节点测试 |
| 20 | 调用 Java mock 创建工单节点 | 已完成 | `notes/langgraph-stage5-20-java-mock-create-ticket-node.md`、`TicketCreator`、`TicketConfirmationRoute`、`TICKET_AGENT_CONFIRMATION_ROUTES`、`route_by_ticket_confirmation`、`build_create_ticket_args_from_fields`、`create_ticket_node`、`ticket_confirmation_approved`、`ticket_creation_status`、`created_ticket`、确认后条件边、fake ticket creator 图测试、`policy_gap` 工单类别契约 |
| 21 | checkpoint 和 thread_id：中断、恢复、继续对话 | 已完成 | `notes/langgraph-stage5-21-checkpoint-thread-id.md`、`MemorySaver`、`build_checkpointed_ticket_agent_graph`、`build_ticket_agent_thread_config`、`run_ticket_agent_in_thread`、`get_ticket_agent_thread_state`、`approve_ticket_confirmation_and_resume`、`graph.get_state`、`graph.update_state`、`as_node="request_ticket_confirmation"`、`graph.invoke(None)`、thread 状态保存、恢复和隔离测试 |
| 22 | interrupt / human-in-the-loop | 已完成 | `notes/langgraph-stage5-22-interrupt-human-in-the-loop.md`、`Command`、`interrupt`、`request_ticket_confirmation_interrupt_node`、`build_interrupting_ticket_agent_graph`、`build_ticket_confirmation_interrupt_payload`、`get_ticket_confirmation_interrupt_payload`、`resume_ticket_confirmation_interrupt`、`TICKET_CONFIRMATION_INTERRUPT_KIND`、`TICKET_CONFIRMATION_REJECTED_MESSAGE`、`__interrupt__`、`Command(resume=...)`、approved/rejected 恢复测试 |
| 23 | 节点错误处理、fallback 和流程兜底 | 已完成 | `notes/langgraph-stage5-23-node-error-fallback.md`、`agent_error_code`、`agent_error_message`、`agent_error_node`、`fallback_used`、`build_ticket_agent_fallback_state`、`build_ticket_creation_failure_state`、`run_ticket_agent_safely`、`resume_ticket_confirmation_interrupt_safely`、创建工单 AppException/未知异常兜底、图级安全执行和 interrupt 恢复失败测试 |
| 24 | LangGraph 日志、trace_id 和可观测性 | 已完成 | `notes/langgraph-stage5-24-observability-trace-logging.md`、`agent_trace_id`、`build_ticket_agent_observation_metadata`、`log_ticket_agent_run_started`、`log_ticket_agent_run_finished`、`log_ticket_agent_run_failed`、`run_ticket_agent`/`run_ticket_agent_safely`/`run_ticket_agent_in_thread`/`resume_ticket_confirmation_interrupt` 运行日志、创建工单节点 started/finished/failed 日志、trace_id 与日志安全测试 |
| 25 | LangGraph 测试：fake LLM / fake RAG / fake Java client | 已完成 | `notes/langgraph-stage5-25-agent-testing-fakes.md`、`build_ticket_agent_graph(policy_rag_service=...)`、`FakePolicyRagService`、`FakeNoContextPolicyRagService`、compiled graph `graph.nodes[...]` 节点级测试、fake RAG 整图路径测试、checkpoint `update_state(..., as_node=...)` 局部执行测试、fake Java client 调用记录和异常模拟测试 |
| 26 | 阶段 5 项目整理和面试表达 | 已完成 | `notes/langgraph-stage5-26-project-summary-interview.md`、阶段 5 三段式复盘、智能工单 Agent v1 总架构、完整执行链路、节点职责表、State 字段分组、测试体系、项目验收清单、面试 30 秒/1 分钟/3 分钟表达、当前 v1 限制和下一阶段生产化方向 |

## 阶段 6 细化学习清单

阶段 6 目标：把已经能运行的 RAG + 智能工单 Agent 往真实工程系统推进。这一阶段固定为 36 节，不只是学 eval、Docker 或 tracing，而是系统补齐 Agent 评测、真实模型节点、工具链路生产化、持久化 checkpoint、可观测性、稳定性保护、部署编排和阶段复盘。

| 节 | 主题 | 学习状态 | 对应产出 |
| --- | --- | --- | --- |
| 1 | Agent 评测基础：为什么 AI 应用不能只靠感觉判断好坏 | 已完成 | `notes/stage6-01-agent-evaluation-basics.md`、评测集、expected output、pass/fail、bad case、回归评测、offline evaluation、online evaluation、evaluator、Agent 结构化评测对象 |
| 2 | 什么是 eval：测试和评测的区别 | 已完成 | `notes/stage6-02-test-vs-eval.md`、test/eval 边界、Arrange/Act/Assert/Cleanup、确定性测试、AI 效果评测、evaluator、metric、bad case、pytest 跑 eval、CI 分层 |
| 3 | 设计 Agent 测试集 | 已完成 | `notes/stage6-03-agent-eval-dataset-design.md`、`projects/ai-service/data/agent_eval/agent_cases.json`、`projects/ai-service/data/agent_eval/README.md`、inputs/expected/metadata、task_type、business_domain、case_type、priority、p0/p1、golden case、bad case 候选、12 条第一版 Agent eval cases |
| 4 | 意图识别评测 | 已完成 | `notes/stage6-04-agent-intent-evaluation.md`、`app/agents/intent_evaluation.py`、`scripts/agent_intent_eval.py`、`tests/test_agent_intent_evaluation.py`、expected intent、actual intent、intent_route、classifier、evaluator、pass/fail、accuracy、p0_accuracy、bad case、12 条样本全部通过 |
| 5 | 工单字段提取评测 | 已完成 | `notes/stage6-05-agent-ticket-field-evaluation.md`、`app/agents/field_evaluation.py`、`scripts/agent_ticket_field_eval.py`、`tests/test_agent_field_evaluation.py`、expected fields、actual fields、missing_ticket_fields、confirmation_required、ticket_need_source、case_pass_rate、field_accuracy、bad case、4 条工单样本和 16 个字段全部通过 |
| 6 | Agent 路由评测 | 已完成 | `notes/stage6-06-agent-route-evaluation.md`、`app/agents/route_evaluation.py`、`scripts/agent_route_eval.py`、`tests/test_agent_route_evaluation.py`、node_history、expected node path、actual node path、path exact match、required nodes、forbidden nodes、terminal node、route_pass_rate、exact_match_rate、12 条样本全部通过 |
| 7 | RAG + Agent 组合评测 | 已完成 | `notes/stage6-07-rag-agent-combination-evaluation.md`、`app/agents/rag_agent_evaluation.py`、`scripts/agent_rag_eval.py`、`tests/test_agent_rag_evaluation.py`、rag_answer_status、answered、no_context、citations、expected_sources、actual_sources、source_recall、must_cite、ticket_decision_passed_count、policy_gap、3 条 RAG 样本全部通过 |
| 8 | 评测脚本设计 | 已完成 | `notes/stage6-08-agent-eval-script-design.md`、`app/agents/eval_suite.py`、`scripts/agent_eval.py`、`tests/test_agent_eval_suite.py`、AgentEvalSuite、AgentEvalRunReport、suite registry、`--suite`、`--list-suites`、`--cases-path`、统一 Agent eval suite、Overall、exit code、8 条新测试通过 |
| 9 | 评测报告 | 已完成 | `notes/stage6-09-agent-eval-report.md`、`app/agents/eval_report.py`、`scripts/agent_eval.py --report-path`、`tests/test_agent_eval_report.py`、`data/agent_eval/reports/agent_eval_report.md`、Markdown report、Overall、Suite Summary、Summary、Bad Cases、PASS/FAIL、UTF-8 写入、3 条新增报告测试通过 |
| 10 | 坏例分析 | 已完成 | `notes/stage6-10-bad-case-analysis.md`、`app/agents/bad_case_analysis.py`、`scripts/agent_eval.py --bad-case-analysis-path`、`tests/test_bad_case_analysis.py`、`data/agent_eval/reports/agent_bad_case_analysis.md`、`data/agent_eval/reports/bad_case_analysis_sample.md`、BadCaseAnalysisItem、BadCaseAnalysisReport、bad case vs bug、expected issue、dataset issue、first divergence、root cause category、recommended action、regression action、5 条新增坏例分析测试通过 |
| 11 | 回归评测 | 已完成 | `notes/stage6-11-regression-evaluation.md`、`agent_cases.json` 中 10 条 P0 样本增加 `regression`/`p0_regression` 标签、`AgentEvalCaseFilter`、`filter_agent_eval_cases`、`describe_agent_eval_case_filter`、`scripts/agent_eval.py --regression --tag --priority`、`case_filter`、`selected_cases`、`data/agent_eval/reports/agent_regression_report.md`、`data/agent_eval/reports/agent_regression_bad_case_analysis.md`、P0 regression selected_cases=10、5 条新增回归筛选测试通过 |
| 12 | evaluator 类型 | 已完成 | `notes/stage6-12-evaluator-types.md`、evaluator、eval dataset、eval runner、eval report、bad case analysis、rule/code evaluator、human evaluator、LLM-as-judge、pairwise evaluator、composite evaluator、summary evaluator、reference-based、reference-free、deterministic、non-deterministic、当前项目 evaluator 类型映射、为什么当前阶段优先代码/规则 evaluator、后续真实模型评测选择原则 |
| 13 | 真实 LLM 意图识别节点 | 已完成 | `notes/stage6-13-real-llm-intent-node.md`、`LLMTicketIntentClassification`、`TicketIntentClassifier`、`LLMTicketIntentClassifier`、`build_ticket_intent_classification_messages()`、`parse_ticket_intent_classification_json()`、`create_llm_ticket_intent_classifier()`、`classify_intent_node(..., classifier=...)`、`build_ticket_agent_graph(intent_classifier=...)`、JSON mode、Pydantic 输出校验、fake/real 注入、`tests/test_ticket_agent_llm_intent.py`、`scripts/ticket_agent_llm_intent_smoke.py` |
| 14 | 真实 LLM 字段提取节点 | 已完成 | `notes/stage6-14-real-llm-field-extraction-node.md`、`LLMTicketFields`、`TicketFieldExtractor`、`LLMTicketFieldExtractor`、`TICKET_FIELD_EXTRACTION_SYSTEM_PROMPT`、`build_ticket_field_extraction_messages()`、`parse_ticket_field_extraction_json()`、`create_llm_ticket_field_extractor()`、`extract_ticket_fields_node(..., extractor=...)`、`build_ticket_agent_graph(field_extractor=...)`、JSON mode + Pydantic 二次校验、fake/real 注入、`tests/test_ticket_agent_llm_fields.py`、`scripts/ticket_agent_llm_field_smoke.py` |
| 15 | Pydantic 校验模型输出 | 已完成 | `notes/stage6-15-pydantic-validate-model-output.md`、`ConfigDict(extra="forbid")`、`StrictBool`、`Field(pattern=...)`、`field_validator(mode="before")`、意图识别输出拒绝多余字段、字段提取输出拒绝 `should_create_ticket`、订单号格式校验、订单号空值归一化、空 reason/description 校验、`tests/test_ticket_agent_llm_output_validation.py` |
| 16 | fake LLM 和真实 LLM 双模式 | 已完成 | `notes/stage6-16-fake-real-llm-modes.md`、`TICKET_AGENT_MODEL_MODE`、`TicketAgentModelMode`、`FakeLLMTicketIntentClassifier`、`FakeLLMTicketFieldExtractor`、`create_ticket_agent_model_dependencies()`、`build_ticket_agent_graph_for_model_mode()`、默认 `rule_based` 防误调用、`fake_llm` 走 JSON/Pydantic 边界、`real_llm` API key 检查、`tests/test_ticket_agent_llm_modes.py` |
| 17 | prompt 版本管理 | 已完成 | `notes/stage6-17-prompt-version-management.md`、`TicketAgentPromptSpec`、`TicketAgentPromptName`、`TICKET_INTENT_CLASSIFICATION_PROMPT`、`TICKET_FIELD_EXTRACTION_PROMPT`、`TICKET_AGENT_PROMPTS`、`get_ticket_agent_prompt_spec()`、message builder 支持 `prompt_spec`、LLM 成功/失败日志记录 `prompt_name` 和 `prompt_version`、模式工厂透传 prompt spec、`tests/test_ticket_agent_prompt_versions.py` |
| 18 | 模型输出失败处理 | 已完成 | `notes/stage6-18-model-output-failure-handling.md`、`TicketAgentModelOutputFailure`、`TicketAgentModelOutputFailureKind`、`TicketAgentModelOutputFailureAction`、`classify_ticket_agent_model_output_failure()`、`ModelOutputFallbackTicketIntentClassifier`、`ModelOutputFallbackTicketFieldExtractor`、`llm_fallback_rule_based` 字段来源、`enable_model_output_fallback` 显式开关、fallback 日志、配置错误不隐藏、`tests/test_ticket_agent_model_output_failure.py` |
| 19 | 接入真实 `query_order` 到 LangGraph | 已完成 | `notes/stage6-19-query-order-langgraph.md`、`OrderQueryExecutor`、`execute_ticket_order_query()`、`query_order_node(..., order_query_executor=...)`、`QueryOrderArgs` 参数校验、`QueryOrderResult` 结果写回、缺订单号追问、工具异常结构化兜底、`build_ticket_agent_graph(order_query_executor=...)` 依赖注入、`tests/test_ticket_agent_query_order_node.py`、`tests/test_ticket_agent_intent.py` |
| 20 | 工具节点错误处理升级 | 已完成 | `notes/stage6-20-tool-node-error-handling.md`、`TicketOrderQueryFailure`、`TicketOrderQueryFailureKind`、`TicketOrderQueryFailureAction`、`classify_ticket_order_query_failure()`、`order_query_error_kind`、`order_query_error_action`、`order_query_retryable`、`order_query_error_status_code`、缺订单号追问状态、订单不存在不可重试、超时/上游错误可重试、工具结果校验失败安全文案、未知异常安全兜底、`tests/test_ticket_agent_query_order_node.py` |
| 21 | 工具权限和写操作安全回归 | 已完成 | `notes/stage6-21-tool-permission-write-safety-regression.md`、`CREATE_TICKET_TOOL_NAME`、`TicketWriteSafetyStatus`、`build_ticket_write_safety_state()`、`authorize_tool_call("create_ticket", user_confirmed=True)`、`ticket_tool_name`、`ticket_tool_access_level`、`ticket_tool_requires_confirmation`、`ticket_write_safety_status`、`ticket_creation_idempotency_key`、未确认阻断、缺确认字段阻断、授权失败不调用 creator、确认后带幂等键创建、写操作安全回归测试 |
| 22 | 持久化 checkpoint 基础 | 已完成 | `notes/stage6-22-persistent-checkpoint-basics.md`、`app/agents/checkpoint_store.py`、`TicketAgentCheckpointSnapshot`、`FileTicketAgentCheckpointStore`、`normalize_checkpoint_thread_id()`、`build_checkpoint_snapshot_filename()`、UTF-8 JSON 快照、schema_version、saved_at、metadata、thread_id 文件名安全、文件内容 thread_id 校验、`build_ticket_agent_checkpoint_snapshot()`、`save_ticket_agent_checkpoint_snapshot()`、7 条 checkpoint store 测试 |
| 23 | checkpoint 存储选型 | 已完成 | `notes/stage6-23-checkpoint-storage-selection.md`、checkpointer vs store、MemorySaver/InMemorySaver、文件 JSON 快照、SQLite、Postgres、Redis、持久性、事务、并发、多实例、TTL、审计、运维成本、当前环境扩展包检查、当前项目推荐路径：学习用 MemorySaver + 文件快照，本地练习用 SQLite，生产主 checkpoint 优先 Postgres，Redis 做短期状态和 TTL 辅助 |
| 24 | `thread_id` 生命周期 | 已完成 | `notes/stage6-24-thread-id-lifecycle.md`、`app/agents/thread_lifecycle.py`、`TicketAgentThreadBinding`、`TicketAgentThreadResumeDecision`、`generate_ticket_agent_thread_id()`、`normalize_ticket_agent_thread_id()`、`create_ticket_agent_thread_binding()`、`mark_ticket_agent_thread_waiting_confirmation()`、`complete_ticket_agent_thread()`、`close_ticket_agent_thread()`、`is_ticket_agent_thread_expired()`、`evaluate_ticket_agent_thread_resume()`、active/waiting_confirmation/completed/closed/expired 生命周期、actor 绑定校验、确认 TTL、恢复决策、11 条生命周期测试 |
| 25 | 会话过期与清理 | 已完成 | `notes/stage6-25-session-expiration-cleanup.md`、`app/agents/thread_cleanup.py`、`TicketAgentThreadCleanupPolicy`、`TicketAgentThreadCleanupDecision`、`TicketAgentThreadCleanupPlan`、`evaluate_ticket_agent_thread_cleanup()`、`build_ticket_agent_thread_cleanup_plan()`、keep/expire/archive、checkpoint `delete_after_archive`、retention、grace period、归档前置、清理计划统计、7 条清理策略测试 |
| 26 | LangSmith tracing 基础 | 已完成 | `notes/stage6-26-langsmith-tracing-basics.md`、`app/agents/langsmith_tracing.py`、`TicketAgentLangSmithTraceContext`、`build_langsmith_trace_tags()`、`build_ticket_agent_langsmith_metadata()`、`build_ticket_agent_langsmith_trace_context()`、LangSmith project / trace / run / thread / tags / metadata 基础、LangGraph `config` 与 LangSmith `tracing_context` 的未来接入形状、trace_id / thread_id / session_id 对齐、安全 metadata 白名单、敏感 payload 排除、tags 归一化、8 条 tracing 上下文测试 |
| 27 | OpenTelemetry 基础 | 已完成 | `notes/stage6-27-opentelemetry-basics.md`、`app/agents/otel_tracing.py`、`OtelTraceParent`、`OtelTraceContext`、`TicketAgentOtelSpanPlan`、`normalize_otel_trace_id()`、`normalize_otel_span_id()`、`parse_traceparent()`、`build_traceparent()`、`build_otel_trace_context()`、`build_ticket_agent_otel_resource_attributes()`、`build_ticket_agent_otel_span_attributes()`、OpenTelemetry trace/span/context propagation/resource/semantic conventions 基础、W3C `traceparent`、`trace_id`/`span_id` 非零十六进制规则、`X-Trace-Id` 与 `traceparent` 区分、Agent span attributes 安全白名单、13 条 OTel 上下文测试 |
| 28 | trace/span/log/metrics 的关系 | 已完成 | `notes/stage6-28-trace-span-log-metrics-relationship.md`、`app/agents/observability_signals.py`、`TicketAgentSignalCorrelation`、`TicketAgentTraceSignal`、`TicketAgentSpanSignal`、`TicketAgentLogSignal`、`TicketAgentMetricSignal`、`TicketAgentObservabilitySignals`、`build_ticket_agent_observability_signals()`、`build_ticket_agent_investigation_steps()`、trace/span/log/metrics 四类观测信号关系、log 与 trace/span correlation、metrics cardinality、高基数字段不进 metrics、单用户失败/延迟升高/错误率升高/Agent 决策调试的排查顺序、7 条观测信号测试 |
| 29 | 生产日志字段设计 | 已完成 | `notes/stage6-29-production-log-field-design.md`、`app/agents/production_logging.py`、`TicketAgentLogFieldSpec`、`TicketAgentProductionLogRecord`、`build_ticket_agent_log_field_specs()`、`validate_ticket_agent_event_name()`、`normalize_ticket_agent_log_severity()`、`find_forbidden_ticket_agent_log_fields()`、`build_ticket_agent_production_log_record()`、top-level/resource/attributes/forbidden 字段分层、event_name 稳定命名、severity_text/severity_number、trace_id/span_id/thread_id/app_trace_id/actor_id 区分、error_code/error_node/fallback_used、敏感 payload 不进生产日志、9 条生产日志字段测试 |
| 30 | 成本、token 和延迟指标 | 已完成 | `notes/stage6-30-cost-token-latency-metrics.md`、`app/agents/llm_metrics.py`、`LLMMetricSpec`、`LLMMetricMeasurement`、`LLMTokenUsageSnapshot`、`LLMTokenPricing`、`LLMEstimatedCost`、`build_llm_metric_specs()`、`normalize_llm_token_usage()`、`estimate_llm_call_cost()`、`build_llm_metric_attributes()`、`build_llm_call_metrics()`、prompt_tokens/completion_tokens/total_tokens、成本估算公式、`gen_ai.client.operation.duration`、`gen_ai.client.token.usage`、counter vs histogram、metrics cardinality、低基数 attributes、高基数和敏感字段过滤、12 条 LLM 指标测试 |
| 31 | timeout 超时策略 | 已完成 | `notes/stage6-31-timeout-strategy.md`、`app/agents/timeout_strategy.py`、`TimeoutBudget`、`TicketAgentTimeoutPolicy`、`TimeoutFailure`、`build_timeout_budget()`、`build_ticket_agent_timeout_policies()`、`classify_timeout_phase()`、`build_timeout_failure()`、`is_timeout_retry_allowed()`、`sanitize_timeout_metric_attributes()`、connect/read/write/pool/total/operation timeout、LLM/embedding/Java/RAG timeout 策略、读写操作 timeout 差异、写操作幂等 retry 边界、timeout error_code 映射、fallback/retry 边界、13 条 timeout 策略测试 |
| 32 | retry 重试策略 | 已完成 | `notes/stage6-32-retry-strategy.md`、`app/agents/retry_strategy.py`、`RetryBackoff`、`TicketAgentRetryPolicy`、`RetryDecision`、`build_default_retry_backoff()`、`build_ticket_agent_retry_policies()`、`classify_http_status_for_retry()`、`classify_error_code_for_retry()`、`classify_exception_for_retry()`、`classify_retry_failure()`、`decide_retry()`、`sanitize_retry_metric_attributes()`、attempt vs retry、max_retries vs max_attempts、retryable failure category、408/409/429/5xx retry 边界、400/401/403/404/422 非 retry 边界、exponential backoff、jitter、Retry-After、LLM 成本敏感、SDK 双重 retry 风险、Java 读写工具 retry 差异、写操作幂等键、retry decision 日志和指标字段、16 条 retry 策略测试 |
| 33 | rate limit、circuit breaker 和降级 | 已完成 | `notes/stage6-33-rate-limit-circuit-breaker-degradation.md`、`app/agents/resilience_strategy.py`、`RateLimitPolicy`、`RateLimitUsage`、`RateLimitDecision`、`CircuitBreakerPolicy`、`CircuitBreakerSnapshot`、`CircuitBreakerDecision`、`CircuitBreakerResult`、`DegradationPlan`、`TicketAgentResiliencePolicy`、`DependencyProtectionDecision`、`build_ticket_agent_resilience_policies()`、`decide_rate_limit()`、`decide_circuit_breaker()`、`record_circuit_breaker_result()`、`build_degradation_plan()`、`evaluate_dependency_protection()`、`sanitize_resilience_metric_attributes()`、rate limit/throttling、near limit、429、circuit breaker closed/open/half-open、fail fast、half-open probe、failure threshold、degradation/fallback/cache 区分、LLM/Embedding/Java/Qdrant/Milvus 保护策略、写操作 require_manual_review、向量库 cache/no-context 降级、retry storm、低基数指标字段、22 条 resilience 策略测试 |
| 34 | Docker Compose 本地编排 | 已完成 | `notes/stage6-34-docker-compose-local-orchestration.md`、`compose.yml`、`compose.env.example`、Docker vs Docker Compose、image/container、services、ports、environment、env_file、Compose 根目录 `.env` vs service `env_file`、bind mount vs named volume、networks、服务名 DNS、depends_on、healthcheck、profiles、默认启动 `ai-service`/`java-mock-service`、可选 `qdrant` profile、可选 `milvus` profile、Qdrant/Milvus 端口冲突提醒、Windows `.venv` 与 Linux 容器隔离、`UV_PROJECT_ENVIRONMENT`、Windows + VMware Ubuntu Docker 路径关系、真实密钥不进 compose、无法在当前 Windows 环境实机运行 Docker 的说明 |
| 35 | health check、readiness 和 CI 自动回归 | 已完成 | `notes/stage6-35-health-readiness-ci-regression.md`、`app/schemas/health.py`、`app/routers/health.py`、`HealthResponse`、`ReadinessCheck`、`ReadinessResponse`、`/health`、`/ready`、liveness/readiness/startup probe 区分、`ai-service` real_llm 缺 API Key 时 `/ready` 返回 503、`java-mock-service` 内存订单/工单 store readiness、Compose healthcheck 改为 `/ready`、`scripts/run_regression.py`、`uv sync --frozen`、`compileall`、`pytest`、`.github/workflows/ci.yml`、GitHub Actions push/PR/workflow_dispatch、`astral-sh/setup-uv`、本地和 CI 复用同一回归入口、Java mock 13 条测试、AI service 880 条测试、CI 不真实调用模型、真实密钥不进 CI |
| 36 | 阶段 6 项目整理和面试表达 | 已完成 | `notes/stage6-36-project-summary-interview-expression.md`、阶段 6 主线复盘、demo/可上线雏形/生产级系统区别、Agent eval、真实模型节点、Pydantic 输出边界、工具调用安全、checkpoint/thread_id、LangSmith/OpenTelemetry、trace/span/log/metrics、生产日志、成本/token/延迟、timeout/retry/rate limit/circuit breaker/degradation、Docker Compose、health/readiness、CI 自动回归、项目 1/3/5 分钟讲法、面试问答、简历表达、当前项目边界、M6 作品整理方向 |

## 当前 Sprint 验收标准

M0/M1 第一阶段完成时，必须满足：

- [x] 本地能运行 Python、Java、Docker。
- [x] 本地能运行 Python。
- [x] 本地能运行 Java。
- [x] 本地能运行 Docker（VMware Ubuntu）。
- [x] uv 安装在 D 盘，缓存、Python 管理目录和工具目录都指向 D 盘。
- [x] `projects/ai-service` 有清晰目录结构。
- [x] FastAPI 服务能启动。
- [x] `/health` 返回正常。
- [x] `/chat` 能完成一次普通模型调用。
- [x] `/stream-chat` 能流式返回。
- [x] 请求日志包含 trace_id、模型名、耗时、错误信息。
- [x] 密钥只从 `.env` 或环境变量读取，并提供 `.env.example`。
- [x] 至少有 5 个 pytest 用例。

## 项目目标

### 项目 1：企业知识库 RAG

必须能力：

- 文档上传
- 文档解析
- chunk 切分
- embedding
- 向量库入库
- top_k 检索
- score_threshold
- 引用来源
- 权限过滤
- 无资料拒答
- 评测集

### 项目 2：智能工单 Agent

必须能力：

- 用户问题分类
- 检索知识库
- 判断是否能直接回答
- 结构化提取工单字段
- 用户确认
- 调用 Java API 创建工单
- 支持继续对话
- 记录完整调用链

## 知识点清单

### Python AI 工程

- [ ] Python 虚拟环境
- [ ] 依赖管理
- [ ] FastAPI
- [ ] Pydantic
- [x] httpx
- [x] logging
- [x] pytest
- [ ] Dockerfile

### LLM API

- [x] OpenAI-compatible SDK 基础调用
- [x] system prompt / user prompt
- [x] streaming
- [x] structured output
- [x] tool calling
- [x] token 成本
- [x] 超时和重试
- [x] 模型错误兜底

### LangChain

- [x] ChatModel
- [ ] PromptTemplate
- [ ] Runnable
- [x] tools
- [x] structured output
- [ ] callbacks
- [ ] retriever

### RAG

- [x] RAG 基础概念
- [x] 文档解析
- [x] chunk 切分
- [x] embedding
- [x] vector store
- [x] metadata
- [x] similarity search
- [x] score_threshold
- [x] answer generation
- [x] hybrid search
- [x] rerank
- [x] citations
- [x] 权限过滤
- [x] 无资料拒答
- [x] fake embedding / fake vector store 测试
- [x] 文档删除 / 重新入库
- [x] 真实 embedding 适配器 / 批量 embedding 基础
- [x] 检索参数调优基础
- [x] RAG 安全基础 / 检索结果安全检查
- [x] RAG 性能基础 / 缓存、批处理、超时、降级
- [x] RAG 主线项目验收 / 阶段复盘
- [x] Milvus vs Qdrant 概念对比 / 向量数据库选型基础
- [x] Milvus Standalone 本地 Docker 启动实机验证
- [x] Milvus collection / schema / field / entity / index 核心概念
- [x] Milvus 文档入库 / entity upsert / 向量检索 smoke
- [x] Milvus metadata filter / scalar index / filter expression smoke
- [x] Qdrant vs Milvus 选型判断 / 项目阶段选择 / 面试表达
- [x] RAG 检索评测基础 / Hit Rate@K / Recall@K / Precision@K / MRR / bad case 分析
- [x] 检索评测脚本 / 固定样本 / no-result case / bad case 报告
- [x] 阶段 4 最终收尾复盘 / RAG 知识地图 / 阶段 5 衔接

### LangGraph

- [x] StateGraph
- [x] state schema
- [x] reducer
- [x] MessagesState
- [x] node
- [x] edge
- [x] conditional edge
- [x] START / END
- [x] graph.invoke / graph.stream
- [x] checkpoint
- [x] interrupt
- [x] human-in-the-loop
- [x] thread_id
- [x] 持久化 checkpoint 快照基础
- [x] thread_id 生命周期 / 归属绑定 / 恢复决策
- [x] 会话过期与清理计划 / retention / archive / delete_after_archive
- [x] OpenTelemetry traceparent / span attributes / resource attributes 基础
- [x] 智能工单 Agent 总流程
- [x] 意图识别节点
- [x] RAG 知识库回答节点
- [x] 判断是否需要创建工单
- [x] 工单字段提取节点
- [x] 缺失字段追问节点
- [x] 用户确认节点
- [x] Java mock 创建工单节点
- [x] 节点错误处理 / fallback
- [x] LangGraph 测试

### Java 集成

- [x] Spring Boot 业务服务
- [ ] 用户权限接口
- [x] 订单查询接口
- [ ] 退款查询接口
- [x] 工单创建接口
- [x] AI tools 调 Java API
- [x] 敏感操作确认

### 工程化

- [x] 请求日志
- [x] 模型调用日志
- [x] tool 调用日志
- [x] trace_id
- [ ] token 成本统计
- [x] 限流
- [x] 重试
- [x] 缓存
- [ ] Docker Compose
- [ ] eval.py

## 复盘记录

### 2026-07-04

- 从旧线程 `019f26a1-6a8b-7362-97c8-91060948d331` 整理学习上下文。
- 明确主线：不走 Spring AI 主线，优先 LangChain + LangGraph。
- 明确产出：企业知识库 RAG、智能工单 Agent。
- 当前项目目录作为后续学习主仓库。
- 完善学习路径：将 12 周计划拆成 M0-M6，收敛为两个主项目，并把日志、评测、安全前置。
- 安装 uv 0.11.26 到 `D:\tools\uv\bin`，并配置 `UV_CACHE_DIR`、`UV_PYTHON_INSTALL_DIR`、`UV_TOOL_DIR` 到 D 盘。
- 检查环境：Python 3.12.3 可用，JDK 17 可用，Docker 暂不可用。
- 创建 `projects/python-basics`，完成 uv 项目初始化、虚拟环境创建、`requests` 依赖安装和 HTTP 请求练习。
- 新增笔记 `notes/python-project-environment.md`。
- 明确后续教学主旨：所有知识从基础讲起，不默认已经会；目标是会用、理解原理、能解释给别人听，并通过代码和自测验证。
- 新增 `docs/learning-resources.md`，开始维护官方文档、GitHub 学习笔记、视频课程和阶段资料组合。
- 完成变量和基本类型练习，新增 `projects/python-basics/01_variables_types.py` 和 `notes/python-variables-and-types.md`。
- 明确笔记规则：以后每节练习和自测问题都要附参考答案；已补充到变量和基本类型笔记。
- 完成字符串练习，新增 `projects/python-basics/02_strings.py`、`projects/python-basics/02_practice_clean_question.py` 和 `notes/python-strings.md`。
- 完成列表练习，新增 `projects/python-basics/03_lists.py`、`projects/python-basics/03_practice_task_list.py` 和 `notes/python-lists.md`。
- 完成字典练习，新增 `projects/python-basics/04_dicts.py`、`projects/python-basics/04_practice_user_profile.py` 和 `notes/python-dicts.md`。
- 完成条件判断练习，新增 `projects/python-basics/05_conditions.py`、`projects/python-basics/05_practice_question_check.py` 和 `notes/python-conditions.md`。
- 完成循环练习，新增 `projects/python-basics/06_loops.py`、`projects/python-basics/06_practice_batch_tasks.py` 和 `notes/python-loops.md`。
- 完成函数练习，新增 `projects/python-basics/07_functions.py`、`projects/python-basics/07_practice_question_functions.py` 和 `notes/python-functions.md`。
- 完成模块导入练习，新增 `projects/python-basics/question_utils.py`、`projects/python-basics/08_imports.py`、`projects/python-basics/08_practice_import_question_utils.py` 和 `notes/python-imports.md`。
- 完成异常处理练习，新增 `projects/python-basics/09_exceptions.py`、`projects/python-basics/09_practice_safe_request.py` 和 `notes/python-exceptions.md`。
- 完成文件读写和 JSON 练习，新增 `projects/python-basics/10_files_json.py`、`projects/python-basics/10_practice_task_json.py`、示例 JSON 数据和 `notes/python-files-json.md`。
- 完成类型提示练习，新增 `projects/python-basics/11_type_hints.py`、`projects/python-basics/11_practice_typed_question.py` 和 `notes/python-type-hints.md`。
- 完成类和对象练习，新增 `projects/python-basics/12_classes.py`、`projects/python-basics/12_practice_learning_task.py` 和 `notes/python-classes.md`。
- 完成元组和集合练习，新增 `projects/python-basics/13_tuple_set.py`、`projects/python-basics/13_practice_tuple_set.py` 和 `notes/python-tuples-sets.md`。
- 完成常用数据处理写法练习，新增 `projects/python-basics/14_data_processing.py`、`projects/python-basics/14_practice_data_processing.py` 和 `notes/python-data-processing.md`。

### 2026-07-05

- 完成函数进阶练习，新增 `projects/python-basics/15_function_advanced.py`、`projects/python-basics/15_practice_function_advanced.py` 和 `notes/python-function-advanced.md`。
- 完成标准库基础练习，新增 `projects/python-basics/16_standard_library.py`、`projects/python-basics/16_practice_standard_library.py` 和 `notes/python-standard-library.md`。
- 完成正则表达式练习，新增 `projects/python-basics/17_regex.py`、`projects/python-basics/17_practice_regex.py` 和 `notes/python-regex.md`。
- 完成 pytest 测试基础练习，新增 `projects/python-basics/lesson18_pytest_basics.py`、`projects/python-basics/lesson18_practice_pytest.py`、测试文件和 `notes/python-pytest.md`。
- 完成调试和报错阅读练习，新增 `projects/python-basics/lesson19_debugging_traceback.py`、`projects/python-basics/lesson19_practice_debugging.py`、测试文件和 `notes/python-debugging-traceback.md`。
- 完成 HTTP/API 基础练习，新增 `projects/python-basics/lesson20_http_api.py`、`projects/python-basics/lesson20_practice_http_api.py`、测试文件和 `notes/python-http-api.md`。
- 完成 async/await 异步基础练习，新增 `projects/python-basics/lesson21_async_await.py`、`projects/python-basics/lesson21_practice_async_await.py`、测试文件和 `notes/python-async-await.md`。
- 完成 Python 基础综合项目 Learning Task Assistant，新增 `projects/python-basics/learning_task_assistant/`、`projects/python-basics/lesson22_mini_project_demo.py`、测试文件和 `notes/python-mini-project.md`。
- 开始阶段 1：FastAPI 服务基础，创建 `projects/ai-service`，完成 FastAPI 项目骨架、`/health` 接口、健康检查测试和 `notes/fastapi-stage1-project-structure.md`。
