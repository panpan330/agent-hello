# Java + Python + AI 学习项目

这是一个 Java + Python 的 AI 客服工单系统学习项目，核心是企业知识库 RAG + LangGraph 智能工单 Agent。

当前项目定位是 AI 应用工程学习项目和作品原型，不是完整生产上线系统。它重点展示如何把传统后端工程能力迁移到 AI 应用里：用 Python FastAPI 承载 AI 服务，用 Java mock service 保留早期学习链路，并在阶段 7 新增真实 Spring Boot + MyBatis + MySQL/Redis 业务服务底座；用 RAG 处理企业知识库问答，用 Tool Calling 和 LangGraph 组织订单查询、用户确认和工单创建流程，再用评测、可观测性、稳定性策略、Docker Compose 和 CI 做工程保障。

## 当前状态

| 项目维度 | 当前状态 |
| --- | --- |
| 学习主线 | Java 后端 + Python AI 服务 + LLM API + RAG + Tool Calling + LangGraph + 工程化 |
| 已完成阶段 | Python 基础、FastAPI、LLM API、Tool Calling、RAG、LangGraph Agent、生产化与评测、真实 Java 后端接入 AI Agent、MCP 与 AI 工具生态基础 |
| 当前阶段 | 阶段 8：MCP 与 AI 工具生态基础已完成，准备进入下一阶段 |
| 当前定位 | AI 应用工程学习项目 / 作品原型 |
| 不是 | 完整生产上线系统 |
| 当前主线 | 在真实 Java 业务服务底座上继续补 Agent、RAG、MCP、评测和生产化能力 |

## 核心能力

- 企业知识库问答：文档加载、chunk 切分、embedding、向量检索、引用来源、无上下文拒答。
- 向量数据库实践：Qdrant 主线、Milvus 对比、metadata filter、索引和选型。
- 工具调用：订单查询、工单创建、工具参数校验、工具结果校验、权限边界。
- 智能工单 Agent：意图识别、RAG 回答、订单查询、字段提取、缺字段追问、用户确认、创建工单。
- Human-in-the-loop：写操作必须经过用户确认，不让模型直接修改业务系统。
- Agent 状态：checkpoint、thread_id、会话生命周期、过期和清理。
- 自动化评测：Agent eval dataset、意图/字段/路由/RAG 组合评测、报告、坏例分析、回归评测。
- 生产化设计：Pydantic 输出校验、prompt 版本管理、模型输出失败处理、日志、trace、metrics。
- 稳定性保护：timeout、retry、rate limit、circuit breaker、degradation。
- MCP 工具生态：Python MCP Server/Client、Tools、Resources、参数校验、错误处理、安全边界、契约测试、配置和可观测性。
- 本地编排和回归：Docker Compose、health/readiness、GitHub Actions CI、统一回归脚本。

## 技术栈地图

| 层次 | 技术 | 作用 |
| --- | --- | --- |
| 业务后端层 | Java mock service、Java business service | mock 服务保留历史学习链路；阶段 7 已新增真实 Spring Boot 业务服务，订单查询、创建工单、MyBatis、MySQL、Redis、internal API、trace_id 和契约测试已落地 |
| AI 服务层 | Python、FastAPI、Pydantic | 提供 AI HTTP API、请求/响应模型、结构化校验 |
| 模型调用层 | OpenAI-compatible SDK、prompt、structured output | 调用大模型、组织 messages、约束模型输出 |
| 知识库层 | RAG、embedding、Qdrant、Milvus | 把企业文档变成可检索知识，并支持引用回答 |
| Agent 编排层 | LangGraph、Tool Calling、Human-in-the-loop | 编排多步骤客服工单流程和安全工具调用 |
| 评测层 | pytest、eval suite、bad case、regression | 验证代码边界和 AI 效果表现 |
| 工程保障层 | logging、trace/span/log/metrics、timeout/retry/限流/熔断/降级 | 让系统可排查、可兜底、可持续迭代 |
| 本地与 CI 层 | Docker Compose、health/readiness、GitHub Actions | 支持本地多服务编排和自动回归 |

## 项目结构

```text
docs/                         学习路线、进度、上下文和项目规划
notes/                        每节学习笔记、练习答案、阶段复盘
projects/python-basics/       Python 基础练习项目
projects/ai-service/          Python FastAPI AI 服务，包含 LLM、RAG、Tool Calling、LangGraph Agent
projects/java-mock-service/   模拟 Java 业务后端，提供订单和工单相关接口
projects/java-business-service/  阶段 7 新增真实 Spring Boot 业务服务，已接入 MyBatis、MySQL、Redis、internal API、trace_id 和契约测试
compose.yml                   本地多服务编排入口
compose.env.example           Compose 环境变量示例
scripts/run_regression.py     本地和 CI 复用的统一回归脚本
```

## 快速阅读入口

| 想了解 | 入口 |
| --- | --- |
| 当前学习进度 | [docs/learning-progress.md](docs/learning-progress.md) |
| 总体学习路线 | [docs/ai-application-learning-roadmap.md](docs/ai-application-learning-roadmap.md) |
| 项目长期上下文 | [docs/learning-context.md](docs/learning-context.md) |
| 项目架构图和流程图 | [docs/project-diagrams.md](docs/project-diagrams.md) |
| 本地运行和演示脚本 | [docs/local-run-and-demo.md](docs/local-run-and-demo.md) |
| 简历描述和面试材料 | [docs/interview-and-resume.md](docs/interview-and-resume.md) |
| Java-AI API 契约草案 | [docs/java-ai-api-contract.md](docs/java-ai-api-contract.md) |
| Java business 数据库设计草案 | [docs/java-business-database-design.md](docs/java-business-database-design.md) |
| Python AI 服务代码 | [projects/ai-service](projects/ai-service) |
| Java mock 业务服务代码 | [projects/java-mock-service](projects/java-mock-service) |
| Java business 真实业务服务 | [projects/java-business-service](projects/java-business-service) |
| 阶段 7 第 1 节 | [notes/stage7-01-ai-agent-java-boundary-design.md](notes/stage7-01-ai-agent-java-boundary-design.md) |
| 阶段 7 第 2 节 | [notes/stage7-02-tool-calling-java-api-contract.md](notes/stage7-02-tool-calling-java-api-contract.md) |
| 阶段 7 第 3 节 | [notes/stage7-03-spring-boot-service-skeleton-domain-model.md](notes/stage7-03-spring-boot-service-skeleton-domain-model.md) |
| 阶段 7 第 4 节 | [notes/stage7-04-mysql-business-data-model.md](notes/stage7-04-mysql-business-data-model.md) |
| 阶段 7 第 5 节 | [notes/stage7-05-spring-boot-mysql-order-query.md](notes/stage7-05-spring-boot-mysql-order-query.md) |
| 阶段 7 第 6 节 | [notes/stage7-06-mysql-ticket-write-transaction.md](notes/stage7-06-mysql-ticket-write-transaction.md) |
| 阶段 7 第 7 节 | [notes/stage7-07-redis-idempotency-cache-rate-limit.md](notes/stage7-07-redis-idempotency-cache-rate-limit.md) |
| 阶段 7 第 7.5 节 | [notes/stage7-075-java-service-traditional-mybatis-refactor.md](notes/stage7-075-java-service-traditional-mybatis-refactor.md) |
| 阶段 7 第 7.5 节手动验证 | [notes/stage7-075-java-service-traditional-mybatis-refactor-manual-tasks.md](notes/stage7-075-java-service-traditional-mybatis-refactor-manual-tasks.md) |
| 阶段 7 第 8 节 | [notes/stage7-08-internal-auth-user-identity.md](notes/stage7-08-internal-auth-user-identity.md) |
| 阶段 7 第 8 节手动验证 | [notes/stage7-08-internal-auth-user-identity-manual-tasks.md](notes/stage7-08-internal-auth-user-identity-manual-tasks.md) |
| 阶段 7 第 9 节 | [notes/stage7-09-java-error-code-to-ai-user-answer.md](notes/stage7-09-java-error-code-to-ai-user-answer.md) |
| 阶段 7 第 9 节手动验证 | [notes/stage7-09-java-error-code-to-ai-user-answer-manual-tasks.md](notes/stage7-09-java-error-code-to-ai-user-answer-manual-tasks.md) |
| 阶段 7 第 10 节 | [notes/stage7-10-trace-id-python-java-chain.md](notes/stage7-10-trace-id-python-java-chain.md) |
| 阶段 7 第 10 节手动验证 | [notes/stage7-10-trace-id-python-java-chain-manual-tasks.md](notes/stage7-10-trace-id-python-java-chain-manual-tasks.md) |
| 阶段 7 第 11 节 | [notes/stage7-11-contract-and-integration-tests.md](notes/stage7-11-contract-and-integration-tests.md) |
| 阶段 7 第 11 节手动验证 | [notes/stage7-11-contract-and-integration-tests-manual-tasks.md](notes/stage7-11-contract-and-integration-tests-manual-tasks.md) |
| 阶段 7 第 12 节 | [notes/stage7-12-project-summary.md](notes/stage7-12-project-summary.md) |
| 阶段 8 学习计划 | [notes/stage8-00-mcp-learning-plan.md](notes/stage8-00-mcp-learning-plan.md) |
| 阶段 8 第 1 节 | [notes/stage8-01-what-is-mcp.md](notes/stage8-01-what-is-mcp.md) |
| 阶段 8 第 2 节 | [notes/stage8-02-mcp-vs-tool-calling.md](notes/stage8-02-mcp-vs-tool-calling.md) |
| 阶段 8 第 3 节 | [notes/stage8-03-mcp-architecture.md](notes/stage8-03-mcp-architecture.md) |
| 阶段 8 第 4 节 | [notes/stage8-04-mcp-communication-basics.md](notes/stage8-04-mcp-communication-basics.md) |
| 阶段 8 第 5 节 | [notes/stage8-05-mcp-lifecycle.md](notes/stage8-05-mcp-lifecycle.md) |
| 阶段 8 第 6 节 | [notes/stage8-06-mcp-transport.md](notes/stage8-06-mcp-transport.md) |
| 阶段 8 第 7 节 | [notes/stage8-07-mcp-tools-basics.md](notes/stage8-07-mcp-tools-basics.md) |
| 阶段 8 第 8 节 | [notes/stage8-08-mcp-resources-basics.md](notes/stage8-08-mcp-resources-basics.md) |
| 阶段 8 第 9 节 | [notes/stage8-09-mcp-prompts-basics.md](notes/stage8-09-mcp-prompts-basics.md) |
| 阶段 8 第 10 节 | [notes/stage8-10-python-minimal-mcp-server.md](notes/stage8-10-python-minimal-mcp-server.md) |
| 阶段 8 第 10 节手动验证 | [notes/stage8-10-python-minimal-mcp-server-manual-tasks.md](notes/stage8-10-python-minimal-mcp-server-manual-tasks.md) |
| 阶段 8 第 11 节 | [notes/stage8-11-mcp-client-debugging.md](notes/stage8-11-mcp-client-debugging.md) |
| 阶段 8 第 11 节手动验证 | [notes/stage8-11-mcp-client-debugging-manual-tasks.md](notes/stage8-11-mcp-client-debugging-manual-tasks.md) |
| 阶段 8 第 12 节 | [notes/stage8-12-mcp-tool-parameter-validation.md](notes/stage8-12-mcp-tool-parameter-validation.md) |
| 阶段 8 第 13 节 | [notes/stage8-13-mcp-error-handling.md](notes/stage8-13-mcp-error-handling.md) |
| 阶段 8 第 14 节 | [notes/stage8-14-mcp-security-boundary.md](notes/stage8-14-mcp-security-boundary.md) |
| 阶段 8 第 15 节 | [notes/stage8-15-mcp-query-order-tool.md](notes/stage8-15-mcp-query-order-tool.md) |
| 阶段 8 第 16 节 | [notes/stage8-16-mcp-create-ticket-tool.md](notes/stage8-16-mcp-create-ticket-tool.md) |
| 阶段 8 第 17 节 | [notes/stage8-17-mcp-project-resources.md](notes/stage8-17-mcp-project-resources.md) |
| 阶段 8 第 18 节 | [notes/stage8-18-mcp-and-existing-agent-relationship.md](notes/stage8-18-mcp-and-existing-agent-relationship.md) |
| 阶段 8 第 19 节 | [notes/stage8-19-mcp-testing-and-contract-tests.md](notes/stage8-19-mcp-testing-and-contract-tests.md) |
| 阶段 8 第 20 节 | [notes/stage8-20-mcp-initial-project-summary.md](notes/stage8-20-mcp-initial-project-summary.md) |
| 阶段 8 第 21 节 | [notes/stage8-21-mcp-server-engineering-structure.md](notes/stage8-21-mcp-server-engineering-structure.md) |
| 阶段 8 第 22 节 | [notes/stage8-22-mcp-config-and-env.md](notes/stage8-22-mcp-config-and-env.md) |
| 阶段 8 第 23 节 | [notes/stage8-23-mcp-observability.md](notes/stage8-23-mcp-observability.md) |
| 阶段 8 第 24 节 | [notes/stage8-24-mcp-summary-and-interview-expression.md](notes/stage8-24-mcp-summary-and-interview-expression.md) |
| M6 项目定位说明 | [notes/m6-01-project-positioning-and-portfolio-goals.md](notes/m6-01-project-positioning-and-portfolio-goals.md) |
| 阶段 6 生产化复盘 | [notes/stage6-36-project-summary-interview-expression.md](notes/stage6-36-project-summary-interview-expression.md) |

## 本地验证入口

当前统一回归入口：

```powershell
python scripts\run_regression.py
```

这会分别验证 `projects/java-mock-service` 和 `projects/ai-service`。完整本地运行说明和演示脚本会在 M6 第 4 节整理。

## 当前边界

当前项目不是完整生产系统，还没有完成：

- Python Agent 运行时主链路还没有完全从历史 `java-mock-service` 切到 `java-business-service`。
- 完整真实 Spring Boot 业务系统。当前 `projects/java-business-service` 已完成订单查询、创建工单、MyBatis、MySQL、Redis、internal API、trace_id 和契约测试底座，但还不是完整客服后台。
- 真实用户表和完整权限体系还未真实化。
- Redis 分布式锁或生产会话存储。
- 完整登录认证和权限系统。
- 前端客服工作台。
- 线上部署、Nginx、HTTPS、正式域名。
- 生产级监控告警、日志采集和压测。

M6 的目标是快速作品化，不夸大项目；M6 已完成。阶段 7 已完成真实 Java Spring Boot + MySQL/Redis 业务服务底座，后续可以在这个基础上继续补 Agent、RAG、MCP、评测和生产化能力。

## 学习主线

- Java 后端负责业务系统、权限、数据库、稳定 API 和工程化能力。
- Python + FastAPI 负责 AI 服务层。
- LangChain 负责 LLM 调用、RAG、工具调用和结构化输出。
- LangGraph 负责多步骤、可恢复、可审计的 Agent/Workflow 编排。
- 项目重点先收敛到企业知识库 RAG 和智能工单 Agent，再逐步真实化。

## 核心文档

- [学习上下文](docs/learning-context.md)
- [AI 应用工程学习路线图](docs/ai-application-learning-roadmap.md)
- [学习进度](docs/learning-progress.md)
- [学习资料清单](docs/learning-resources.md)
- [旧版长期进度文档](docs/ai-application-learning-progress.md)

## Python 基础学习笔记索引

| 顺序 | 主题 | 笔记路径 |
| --- | --- | --- |
| 0 | Python 项目环境和 uv | [notes/python-project-environment.md](notes/python-project-environment.md) |
| 1 | 变量和基本类型 | [notes/python-variables-and-types.md](notes/python-variables-and-types.md) |
| 2 | 字符串 | [notes/python-strings.md](notes/python-strings.md) |
| 3 | 列表 | [notes/python-lists.md](notes/python-lists.md) |
| 4 | 字典 | [notes/python-dicts.md](notes/python-dicts.md) |
| 5 | 条件判断 | [notes/python-conditions.md](notes/python-conditions.md) |
| 6 | 循环 | [notes/python-loops.md](notes/python-loops.md) |
| 7 | 函数 | [notes/python-functions.md](notes/python-functions.md) |
| 8 | 模块导入 | [notes/python-imports.md](notes/python-imports.md) |
| 9 | 异常处理 | [notes/python-exceptions.md](notes/python-exceptions.md) |
| 10 | 文件读写和 JSON | [notes/python-files-json.md](notes/python-files-json.md) |
| 11 | 类型提示 | [notes/python-type-hints.md](notes/python-type-hints.md) |
| 12 | 类和对象 | [notes/python-classes.md](notes/python-classes.md) |
| 13 | 元组和集合 | [notes/python-tuples-sets.md](notes/python-tuples-sets.md) |
| 14 | 常用数据处理写法 | [notes/python-data-processing.md](notes/python-data-processing.md) |
| 15 | 函数进阶 | [notes/python-function-advanced.md](notes/python-function-advanced.md) |
| 16 | 标准库基础 | [notes/python-standard-library.md](notes/python-standard-library.md) |
| 17 | 正则表达式 re | [notes/python-regex.md](notes/python-regex.md) |
| 18 | pytest 测试基础 | [notes/python-pytest.md](notes/python-pytest.md) |
| 19 | 调试和报错阅读 | [notes/python-debugging-traceback.md](notes/python-debugging-traceback.md) |
| 20 | HTTP/API 基础 | [notes/python-http-api.md](notes/python-http-api.md) |
| 21 | async/await 异步基础 | [notes/python-async-await.md](notes/python-async-await.md) |
| 22 | Python 基础综合项目 | [notes/python-mini-project.md](notes/python-mini-project.md) |

对应练习代码主要在 [projects/python-basics](projects/python-basics)。

## 阶段 1：Python AI 服务学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | Web 服务、HTTP 和 API 是什么 | [notes/fastapi-stage1-01-web-http-api.md](notes/fastapi-stage1-01-web-http-api.md) | [projects/ai-service](projects/ai-service) |
| 2 | FastAPI 是什么 | [notes/fastapi-stage1-02-what-is-fastapi.md](notes/fastapi-stage1-02-what-is-fastapi.md) | [projects/ai-service](projects/ai-service) |
| 3 | 创建 `ai-service` 项目骨架 | [notes/fastapi-stage1-03-ai-service-project-skeleton.md](notes/fastapi-stage1-03-ai-service-project-skeleton.md) | [projects/ai-service](projects/ai-service) |
| 4 | FastAPI 最小服务 `/health` | [notes/fastapi-stage1-04-health-endpoint.md](notes/fastapi-stage1-04-health-endpoint.md) | [projects/ai-service](projects/ai-service) |
| 5 | router 路由拆分 | [notes/fastapi-stage1-05-router-splitting.md](notes/fastapi-stage1-05-router-splitting.md) | [projects/ai-service](projects/ai-service) |
| 6 | POST、请求体和 JSON | [notes/fastapi-stage1-06-post-body-json.md](notes/fastapi-stage1-06-post-body-json.md) | [projects/ai-service](projects/ai-service) |
| 7 | Pydantic 请求模型 | [notes/fastapi-stage1-07-pydantic-request-model.md](notes/fastapi-stage1-07-pydantic-request-model.md) | [projects/ai-service](projects/ai-service) |
| 8 | Pydantic 响应模型 | [notes/fastapi-stage1-08-pydantic-response-model.md](notes/fastapi-stage1-08-pydantic-response-model.md) | [projects/ai-service](projects/ai-service) |
| 9 | 模拟 `/chat` 接口 | [notes/fastapi-stage1-09-mock-chat-endpoint.md](notes/fastapi-stage1-09-mock-chat-endpoint.md) | [projects/ai-service](projects/ai-service) |
| 10 | 测试 FastAPI 接口 | [notes/fastapi-stage1-10-testing-fastapi-apis.md](notes/fastapi-stage1-10-testing-fastapi-apis.md) | [projects/ai-service](projects/ai-service) |
| 11 | `.env` 配置读取 | [notes/fastapi-stage1-11-env-config.md](notes/fastapi-stage1-11-env-config.md) | [projects/ai-service](projects/ai-service) |
| 12 | `logging` 日志 | [notes/fastapi-stage1-12-logging.md](notes/fastapi-stage1-12-logging.md) | [projects/ai-service](projects/ai-service) |
| 13 | `trace_id` 请求追踪 | [notes/fastapi-stage1-13-trace-id.md](notes/fastapi-stage1-13-trace-id.md) | [projects/ai-service](projects/ai-service) |
| 14 | 统一异常处理 | [notes/fastapi-stage1-14-exception-handling.md](notes/fastapi-stage1-14-exception-handling.md) | [projects/ai-service](projects/ai-service) |
| 15 | CORS 基础 | [notes/fastapi-stage1-15-cors.md](notes/fastapi-stage1-15-cors.md) | [projects/ai-service](projects/ai-service) |
| 16 | 阶段 1 项目整理 | [notes/fastapi-stage1-16-project-summary.md](notes/fastapi-stage1-16-project-summary.md) | [projects/ai-service](projects/ai-service) |

## 阶段 2：LLM API 基础调用学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | 什么是 LLM API | [notes/llm-api-stage2-01-what-is-llm-api.md](notes/llm-api-stage2-01-what-is-llm-api.md) | [projects/ai-service](projects/ai-service) |
| 2 | API key 和 `.env` 安全配置 | [notes/llm-api-stage2-02-api-key-env-security.md](notes/llm-api-stage2-02-api-key-env-security.md) | [projects/ai-service](projects/ai-service) |
| 3 | token、上下文窗口、费用基础 | [notes/llm-api-stage2-03-token-context-cost.md](notes/llm-api-stage2-03-token-context-cost.md) | [projects/ai-service](projects/ai-service) |
| 4 | OpenAI-compatible SDK 基础调用方式 | [notes/llm-api-stage2-04-openai-compatible-sdk.md](notes/llm-api-stage2-04-openai-compatible-sdk.md) | [projects/ai-service](projects/ai-service) |
| 5 | messages 是什么：system / user / assistant | [notes/llm-api-stage2-05-messages-roles.md](notes/llm-api-stage2-05-messages-roles.md) | [projects/ai-service](projects/ai-service) |
| 6 | prompt 基础：怎么写清楚任务 | [notes/llm-api-stage2-06-prompt-basics.md](notes/llm-api-stage2-06-prompt-basics.md) | [projects/ai-service](projects/ai-service) |
| 7 | 第一次真实 `/chat` 调用 | [notes/llm-api-stage2-07-real-chat-call.md](notes/llm-api-stage2-07-real-chat-call.md) | [projects/ai-service](projects/ai-service) |
| 8 | 多轮对话基础：历史消息怎么传 | [notes/llm-api-stage2-08-multi-turn-history.md](notes/llm-api-stage2-08-multi-turn-history.md) | [projects/ai-service](projects/ai-service) |
| 9 | timeout 超时 | [notes/llm-api-stage2-09-timeout.md](notes/llm-api-stage2-09-timeout.md) | [projects/ai-service](projects/ai-service) |
| 10 | retry 重试和 rate limit 限流基础 | [notes/llm-api-stage2-10-retry-rate-limit.md](notes/llm-api-stage2-10-retry-rate-limit.md) | [projects/ai-service](projects/ai-service) |
| 11 | 模型调用错误处理 | [notes/llm-api-stage2-11-model-error-handling.md](notes/llm-api-stage2-11-model-error-handling.md) | [projects/ai-service](projects/ai-service) |
| 12 | 模型调用日志：模型名、耗时、trace_id、token | [notes/llm-api-stage2-12-llm-call-logging.md](notes/llm-api-stage2-12-llm-call-logging.md) | [projects/ai-service](projects/ai-service) |
| 13 | streaming 流式输出是什么 | [notes/llm-api-stage2-13-streaming-concept.md](notes/llm-api-stage2-13-streaming-concept.md) | [projects/ai-service](projects/ai-service) |
| 14 | FastAPI `StreamingResponse` 实现 `/stream-chat` | [notes/llm-api-stage2-14-stream-chat-endpoint.md](notes/llm-api-stage2-14-stream-chat-endpoint.md) | [projects/ai-service](projects/ai-service) |
| 15 | 结构化输出是什么 | [notes/llm-api-stage2-15-structured-output-concept.md](notes/llm-api-stage2-15-structured-output-concept.md) | [projects/ai-service](projects/ai-service) |
| 16 | Pydantic 约束结构化输出 | [notes/llm-api-stage2-16-pydantic-structured-output.md](notes/llm-api-stage2-16-pydantic-structured-output.md) | [projects/ai-service](projects/ai-service) |
| 17 | 测试模型调用：mock/fake LLM client | [notes/llm-api-stage2-17-testing-model-calls.md](notes/llm-api-stage2-17-testing-model-calls.md) | [projects/ai-service](projects/ai-service) |
| 18 | 阶段 2 项目整理 | [notes/llm-api-stage2-18-project-summary.md](notes/llm-api-stage2-18-project-summary.md) | [projects/ai-service](projects/ai-service) |

## 阶段 3：LangChain + Java 工具调用学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | Tool Calling 是什么 | [notes/tool-calling-stage3-01-what-is-tool-calling.md](notes/tool-calling-stage3-01-what-is-tool-calling.md) | [projects/ai-service](projects/ai-service) |
| 2 | 为什么 AI 不能直接操作业务系统 | [notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md](notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md) | [projects/ai-service](projects/ai-service) |
| 3 | 工具参数和 JSON Schema | [notes/tool-calling-stage3-03-tool-parameters-json-schema.md](notes/tool-calling-stage3-03-tool-parameters-json-schema.md) | [projects/ai-service](projects/ai-service) |
| 4 | 结构化输出 vs Tool Calling | [notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md](notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md) | [projects/ai-service](projects/ai-service) |
| 5 | 用 fake tool 模拟查订单 | [notes/tool-calling-stage3-05-fake-query-order-tool.md](notes/tool-calling-stage3-05-fake-query-order-tool.md) | [projects/ai-service](projects/ai-service) |
| 6 | 工具调用结果也要 Pydantic 校验 | [notes/tool-calling-stage3-06-tool-result-pydantic-validation.md](notes/tool-calling-stage3-06-tool-result-pydantic-validation.md) | [projects/ai-service](projects/ai-service) |
| 7 | 工具调用错误处理：超时、404、500 | [notes/tool-calling-stage3-07-tool-error-handling.md](notes/tool-calling-stage3-07-tool-error-handling.md) | [projects/ai-service](projects/ai-service) |
| 8 | 工具调用权限边界 | [notes/tool-calling-stage3-08-tool-permission-boundary.md](notes/tool-calling-stage3-08-tool-permission-boundary.md) | [projects/ai-service](projects/ai-service) |
| 9 | 工具调用幂等性 | [notes/tool-calling-stage3-09-tool-idempotency.md](notes/tool-calling-stage3-09-tool-idempotency.md) | [projects/ai-service](projects/ai-service) |
| 10 | 用 FastAPI 写一个最小 Java mock 业务服务 | [notes/tool-calling-stage3-10-java-mock-service.md](notes/tool-calling-stage3-10-java-mock-service.md) | [projects/java-mock-service](projects/java-mock-service) |
| 11 | Python AI 服务调用 Java mock API | [notes/tool-calling-stage3-11-python-calls-java-mock-api.md](notes/tool-calling-stage3-11-python-calls-java-mock-api.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |
| 12 | 让模型决定是否调用工具 | [notes/tool-calling-stage3-12-model-decides-tool-call.md](notes/tool-calling-stage3-12-model-decides-tool-call.md) | [projects/ai-service](projects/ai-service) |
| 13 | 工具调用结果再交给模型总结 | [notes/tool-calling-stage3-13-tool-result-model-summary.md](notes/tool-calling-stage3-13-tool-result-model-summary.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |
| 14 | 用户确认机制：敏感操作不能直接执行 | [notes/tool-calling-stage3-14-user-confirmation.md](notes/tool-calling-stage3-14-user-confirmation.md) | [projects/ai-service](projects/ai-service) |
| 15 | 创建工单流程：提取字段、确认、调用 Java API | [notes/tool-calling-stage3-15-ticket-creation-workflow.md](notes/tool-calling-stage3-15-ticket-creation-workflow.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |
| 16 | 工具调用日志和 trace_id 串联 | [notes/tool-calling-stage3-16-tool-logging-trace-id.md](notes/tool-calling-stage3-16-tool-logging-trace-id.md) | [projects/ai-service](projects/ai-service) |
| 17 | 工具调用测试：fake Java API / fake tool | [notes/tool-calling-stage3-17-tool-testing-fakes.md](notes/tool-calling-stage3-17-tool-testing-fakes.md) | [projects/ai-service](projects/ai-service) |
| 18 | LangChain 是什么，为什么现在才引入 | [notes/tool-calling-stage3-18-what-is-langchain.md](notes/tool-calling-stage3-18-what-is-langchain.md) | [projects/ai-service](projects/ai-service) |
| 19 | LangChain ChatModel 基础 | [notes/tool-calling-stage3-19-langchain-chatmodel-basics.md](notes/tool-calling-stage3-19-langchain-chatmodel-basics.md) | [projects/ai-service](projects/ai-service) |
| 20 | LangChain Tool 基础 | [notes/tool-calling-stage3-20-langchain-tool-basics.md](notes/tool-calling-stage3-20-langchain-tool-basics.md) | [projects/ai-service](projects/ai-service) |
| 21 | LangChain 结构化输出 | [notes/tool-calling-stage3-21-langchain-structured-output.md](notes/tool-calling-stage3-21-langchain-structured-output.md) | [projects/ai-service](projects/ai-service) |
| 22 | 阶段 3 项目整理 | [notes/tool-calling-stage3-22-project-summary.md](notes/tool-calling-stage3-22-project-summary.md) | [projects/ai-service](projects/ai-service)、[projects/java-mock-service](projects/java-mock-service) |

## 阶段 4：企业知识库 RAG 学习笔记索引

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | RAG 是什么，为什么大模型需要知识库 | [notes/rag-stage4-01-what-is-rag.md](notes/rag-stage4-01-what-is-rag.md) | 待新增 |
| 2 | RAG 完整流程：load -> split -> embed -> store -> retrieve -> generate | [notes/rag-stage4-02-rag-pipeline.md](notes/rag-stage4-02-rag-pipeline.md) | 待新增 |
| 3 | 文档、知识库、chunk、metadata 是什么 | [notes/rag-stage4-03-documents-chunks-metadata.md](notes/rag-stage4-03-documents-chunks-metadata.md) | 待新增 |
| 4 | embedding 是什么：文本怎么变成向量 | [notes/rag-stage4-04-what-is-embedding.md](notes/rag-stage4-04-what-is-embedding.md) | 待新增 |
| 5 | 向量相似度：为什么能用向量找相似内容 | [notes/rag-stage4-05-vector-similarity.md](notes/rag-stage4-05-vector-similarity.md) | 待新增 |
| 6 | 向量数据库是什么，为什么先选 Qdrant | [notes/rag-stage4-06-vector-database-qdrant.md](notes/rag-stage4-06-vector-database-qdrant.md) | 待新增 |
| 7 | Qdrant 基础：collection、point、vector、payload | [notes/rag-stage4-07-qdrant-core-concepts.md](notes/rag-stage4-07-qdrant-core-concepts.md) | 待新增 |
| 8 | 本地启动 Qdrant | [notes/rag-stage4-08-start-qdrant-locally.md](notes/rag-stage4-08-start-qdrant-locally.md) | VMware Ubuntu Docker 已验证 |
| 9 | RAG 项目结构设计 | [notes/rag-stage4-09-rag-project-structure.md](notes/rag-stage4-09-rag-project-structure.md) | [projects/ai-service/app/rag](projects/ai-service/app/rag) |
| 10 | 准备第一批 Markdown/txt 知识文档 | [notes/rag-stage4-10-first-knowledge-documents.md](notes/rag-stage4-10-first-knowledge-documents.md) | [projects/ai-service/data/knowledge_base](projects/ai-service/data/knowledge_base) |
| 11 | 文档加载和文本清洗 | [notes/rag-stage4-11-document-loading-cleaning.md](notes/rag-stage4-11-document-loading-cleaning.md) | [projects/ai-service/app/rag/loaders.py](projects/ai-service/app/rag/loaders.py) |
| 12 | chunk 切分策略：大小、重叠、标题、段落 | [notes/rag-stage4-12-chunk-splitting.md](notes/rag-stage4-12-chunk-splitting.md) | [projects/ai-service/app/rag/splitters.py](projects/ai-service/app/rag/splitters.py) |
| 13 | 生成 embedding 并写入 Qdrant | [notes/rag-stage4-13-embedding-qdrant-ingestion.md](notes/rag-stage4-13-embedding-qdrant-ingestion.md) | [projects/ai-service/app/rag/embeddings.py](projects/ai-service/app/rag/embeddings.py)、[projects/ai-service/app/rag/vector_store.py](projects/ai-service/app/rag/vector_store.py)、[projects/ai-service/app/rag/ingestion.py](projects/ai-service/app/rag/ingestion.py) |
| 14 | metadata 设计：source、title、section、权限字段 | [notes/rag-stage4-14-metadata-design.md](notes/rag-stage4-14-metadata-design.md) | [projects/ai-service/app/rag/metadata.py](projects/ai-service/app/rag/metadata.py) |
| 15 | 基础 top_k 检索 | [notes/rag-stage4-15-basic-top-k-retrieval.md](notes/rag-stage4-15-basic-top-k-retrieval.md) | [projects/ai-service/app/rag/retriever.py](projects/ai-service/app/rag/retriever.py) |
| 16 | payload filter：按文档类型、权限、来源过滤 | [notes/rag-stage4-16-payload-filter.md](notes/rag-stage4-16-payload-filter.md) | [projects/ai-service/app/rag/filters.py](projects/ai-service/app/rag/filters.py) |
| 17 | score_threshold：低相关内容不回答 | [notes/rag-stage4-17-score-threshold.md](notes/rag-stage4-17-score-threshold.md) | [projects/ai-service/app/rag/retriever.py](projects/ai-service/app/rag/retriever.py)、[projects/ai-service/app/rag/vector_store.py](projects/ai-service/app/rag/vector_store.py) |
| 18 | 把检索结果交给模型回答 | [notes/rag-stage4-18-retrieved-context-to-model-answer.md](notes/rag-stage4-18-retrieved-context-to-model-answer.md) | [projects/ai-service/app/rag/generator.py](projects/ai-service/app/rag/generator.py) |
| 19 | 引用来源：回答必须带出处 | [notes/rag-stage4-19-citations.md](notes/rag-stage4-19-citations.md) | [projects/ai-service/app/rag/generator.py](projects/ai-service/app/rag/generator.py) |
| 20 | 无检索结果时怎么处理 | [notes/rag-stage4-20-no-context-handling.md](notes/rag-stage4-20-no-context-handling.md) | [projects/ai-service/app/rag/generator.py](projects/ai-service/app/rag/generator.py) |
| 21 | RAG 错误处理：embedding、向量库、模型调用异常 | [notes/rag-stage4-21-error-handling.md](notes/rag-stage4-21-error-handling.md) | [projects/ai-service/app/rag/errors.py](projects/ai-service/app/rag/errors.py)、[projects/ai-service/app/rag/retriever.py](projects/ai-service/app/rag/retriever.py)、[projects/ai-service/app/rag/ingestion.py](projects/ai-service/app/rag/ingestion.py) |
| 22 | RAG 测试：fake embedding、fake vector store | [notes/rag-stage4-22-rag-testing-fakes.md](notes/rag-stage4-22-rag-testing-fakes.md) | [projects/ai-service/tests/rag_fakes.py](projects/ai-service/tests/rag_fakes.py) |
| 23 | 文档更新、删除、重新入库 | [notes/rag-stage4-23-document-update-delete-reingest.md](notes/rag-stage4-23-document-update-delete-reingest.md) | [projects/ai-service/app/rag/ingestion.py](projects/ai-service/app/rag/ingestion.py)、[projects/ai-service/app/rag/vector_store.py](projects/ai-service/app/rag/vector_store.py) |
| 24 | embedding 模型选择、维度、成本和批量处理 | [notes/rag-stage4-24-embedding-model-dimension-cost-batch.md](notes/rag-stage4-24-embedding-model-dimension-cost-batch.md) | [projects/ai-service/app/rag/embeddings.py](projects/ai-service/app/rag/embeddings.py)、[projects/ai-service/app/core/config.py](projects/ai-service/app/core/config.py) |
| 25 | 检索质量调优：chunk size、overlap、top_k、score_threshold | [notes/rag-stage4-25-retrieval-quality-tuning.md](notes/rag-stage4-25-retrieval-quality-tuning.md) | [projects/ai-service/app/rag/tuning.py](projects/ai-service/app/rag/tuning.py)、[projects/ai-service/scripts/rag_chunk_tuning_preview.py](projects/ai-service/scripts/rag_chunk_tuning_preview.py) |
| 26 | 混合检索：关键词检索 + 向量检索 | [notes/rag-stage4-26-hybrid-search.md](notes/rag-stage4-26-hybrid-search.md) | [projects/ai-service/app/rag/hybrid.py](projects/ai-service/app/rag/hybrid.py)、[projects/ai-service/scripts/rag_keyword_search_preview.py](projects/ai-service/scripts/rag_keyword_search_preview.py) |
| 27 | rerank 重排序是什么 | [notes/rag-stage4-27-rerank.md](notes/rag-stage4-27-rerank.md) | [projects/ai-service/app/rag/rerank.py](projects/ai-service/app/rag/rerank.py)、[projects/ai-service/scripts/rag_rerank_preview.py](projects/ai-service/scripts/rag_rerank_preview.py) |
| 28 | RAG 安全：文档权限、Prompt Injection、敏感信息 | [notes/rag-stage4-28-rag-security.md](notes/rag-stage4-28-rag-security.md) | [projects/ai-service/app/rag/security.py](projects/ai-service/app/rag/security.py)、[projects/ai-service/scripts/rag_security_preview.py](projects/ai-service/scripts/rag_security_preview.py) |
| 29 | RAG 性能：缓存、批处理、超时、降级 | [notes/rag-stage4-29-rag-performance.md](notes/rag-stage4-29-rag-performance.md) | [projects/ai-service/app/rag/performance.py](projects/ai-service/app/rag/performance.py)、[projects/ai-service/scripts/rag_performance_preview.py](projects/ai-service/scripts/rag_performance_preview.py) |
| 30 | 阶段 4 主线项目验收和复盘 | [notes/rag-stage4-30-project-summary.md](notes/rag-stage4-30-project-summary.md) | [projects/ai-service/app/rag](projects/ai-service/app/rag)、[projects/ai-service/tests](projects/ai-service/tests) |
| 31 | Milvus 是什么，和 Qdrant 有什么区别 | [notes/rag-stage4-31-milvus-vs-qdrant.md](notes/rag-stage4-31-milvus-vs-qdrant.md) | 概念对比，无代码改动 |
| 32 | 本地 Docker 启动 Milvus Standalone | [notes/rag-stage4-32-start-milvus-standalone-locally.md](notes/rag-stage4-32-start-milvus-standalone-locally.md) | VMware Ubuntu Docker 已验证 |
| 33 | Milvus 核心概念：collection、schema、field、entity、index | [notes/rag-stage4-33-milvus-core-concepts.md](notes/rag-stage4-33-milvus-core-concepts.md) | 概念讲解，无代码改动 |
| 34 | 用同一批文档写入 Milvus 并做向量检索 | [notes/rag-stage4-34-milvus-ingestion-search.md](notes/rag-stage4-34-milvus-ingestion-search.md) | [projects/ai-service/app/rag/milvus_store.py](projects/ai-service/app/rag/milvus_store.py)、[projects/ai-service/scripts/rag_milvus_smoke.py](projects/ai-service/scripts/rag_milvus_smoke.py) |
| 35 | Milvus metadata/scalar filter 和索引基础 | [notes/rag-stage4-35-milvus-metadata-scalar-filter-index.md](notes/rag-stage4-35-milvus-metadata-scalar-filter-index.md) | [projects/ai-service/app/rag/milvus_store.py](projects/ai-service/app/rag/milvus_store.py)、[projects/ai-service/scripts/rag_milvus_filter_smoke.py](projects/ai-service/scripts/rag_milvus_filter_smoke.py) |
| 36 | Qdrant vs Milvus：什么时候选谁 | [notes/rag-stage4-36-qdrant-vs-milvus-selection.md](notes/rag-stage4-36-qdrant-vs-milvus-selection.md) | 选型讲解，无代码改动 |
| 37 | RAG 检索评测基础 | [notes/rag-stage4-37-rag-retrieval-evaluation-basics.md](notes/rag-stage4-37-rag-retrieval-evaluation-basics.md) | 概念讲解，无代码改动 |
| 38 | 给当前 RAG 项目做一个最小检索评测脚本 | [notes/rag-stage4-38-rag-retrieval-evaluation-script.md](notes/rag-stage4-38-rag-retrieval-evaluation-script.md) | [projects/ai-service/app/rag/evaluation.py](projects/ai-service/app/rag/evaluation.py)、[projects/ai-service/data/rag_eval/retrieval_cases.json](projects/ai-service/data/rag_eval/retrieval_cases.json)、[projects/ai-service/scripts/rag_retrieval_eval.py](projects/ai-service/scripts/rag_retrieval_eval.py) |
| 39 | 企业知识库 RAG 最终收尾复盘 | [notes/rag-stage4-39-final-review.md](notes/rag-stage4-39-final-review.md) | 阶段 4 总复盘，无代码改动 |

## 阶段 5：LangGraph 智能工单 Agent 学习规划

阶段 5 已确定按 26 节推进，目标是做出智能工单 Agent v1。第 1-12 节先学 LangGraph 基础和图执行方式，第 13-22 节接入智能工单业务流程，第 23-26 节补错误处理、日志、测试和项目整理。

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | LangGraph 是什么，为什么现在才学 | [notes/langgraph-stage5-01-what-is-langgraph.md](notes/langgraph-stage5-01-what-is-langgraph.md) | 概念讲解，无代码改动 |
| 2 | LangGraph 和 LangChain / 普通函数流程的区别 | [notes/langgraph-stage5-02-langgraph-vs-langchain-function-flow.md](notes/langgraph-stage5-02-langgraph-vs-langchain-function-flow.md) | 概念讲解，无代码改动 |
| 3 | Agent 流程和状态机基础 | [notes/langgraph-stage5-03-agent-flow-state-machine-basics.md](notes/langgraph-stage5-03-agent-flow-state-machine-basics.md) | 概念讲解，无代码改动 |
| 4 | State 是什么：Agent 为什么需要状态 | [notes/langgraph-stage5-04-state-agent-needs-state.md](notes/langgraph-stage5-04-state-agent-needs-state.md) | 概念讲解，无代码改动 |
| 5 | Reducer 是什么：状态字段怎么合并 | [notes/langgraph-stage5-05-reducer-state-merge.md](notes/langgraph-stage5-05-reducer-state-merge.md) | 概念讲解，无代码改动 |
| 6 | MessagesState：多轮对话消息怎么保存 | [notes/langgraph-stage5-06-messages-state.md](notes/langgraph-stage5-06-messages-state.md) | 概念讲解，无代码改动 |
| 7 | StateGraph 最小图 | [notes/langgraph-stage5-07-stategraph-minimal-graph.md](notes/langgraph-stage5-07-stategraph-minimal-graph.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/scripts/langgraph_minimal_graph_smoke.py](projects/ai-service/scripts/langgraph_minimal_graph_smoke.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 8 | node 节点是什么 | [notes/langgraph-stage5-08-what-is-node.md](notes/langgraph-stage5-08-what-is-node.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 9 | edge 边是什么 | [notes/langgraph-stage5-09-what-is-edge.md](notes/langgraph-stage5-09-what-is-edge.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 10 | conditional edge 条件分支 | [notes/langgraph-stage5-10-conditional-edge.md](notes/langgraph-stage5-10-conditional-edge.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 11 | START / END 和流程结束 | [notes/langgraph-stage5-11-start-end-flow-finish.md](notes/langgraph-stage5-11-start-end-flow-finish.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 12 | graph.invoke / graph.stream：普通执行和流式执行 | [notes/langgraph-stage5-12-invoke-stream.md](notes/langgraph-stage5-12-invoke-stream.md) | [projects/ai-service/app/agents/minimal_graph.py](projects/ai-service/app/agents/minimal_graph.py)、[projects/ai-service/scripts/langgraph_minimal_graph_smoke.py](projects/ai-service/scripts/langgraph_minimal_graph_smoke.py)、[projects/ai-service/tests/test_langgraph_minimal_graph.py](projects/ai-service/tests/test_langgraph_minimal_graph.py) |
| 13 | 智能工单 Agent 总流程设计 | [notes/langgraph-stage5-13-ticket-agent-overall-design.md](notes/langgraph-stage5-13-ticket-agent-overall-design.md) | 设计笔记，无代码改动 |
| 14 | 意图识别节点 | [notes/langgraph-stage5-14-intent-classification-node.md](notes/langgraph-stage5-14-intent-classification-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 15 | RAG 知识库回答节点 | [notes/langgraph-stage5-15-rag-policy-node.md](notes/langgraph-stage5-15-rag-policy-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 16 | 判断是否需要创建工单 | [notes/langgraph-stage5-16-decide-ticket-need.md](notes/langgraph-stage5-16-decide-ticket-need.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 17 | 工单字段提取节点 | [notes/langgraph-stage5-17-ticket-field-extraction-node.md](notes/langgraph-stage5-17-ticket-field-extraction-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 18 | 缺失字段追问节点 | [notes/langgraph-stage5-18-missing-field-follow-up-node.md](notes/langgraph-stage5-18-missing-field-follow-up-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 19 | 用户确认节点 | [notes/langgraph-stage5-19-ticket-confirmation-node.md](notes/langgraph-stage5-19-ticket-confirmation-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 20 | 调用 Java mock 创建工单节点 | [notes/langgraph-stage5-20-java-mock-create-ticket-node.md](notes/langgraph-stage5-20-java-mock-create-ticket-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/app/schemas/ticket.py](projects/ai-service/app/schemas/ticket.py)、[projects/java-mock-service/app/schemas/ticket.py](projects/java-mock-service/app/schemas/ticket.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py)、[projects/java-mock-service/tests/test_tickets_api.py](projects/java-mock-service/tests/test_tickets_api.py) |
| 21 | checkpoint 和 thread_id：中断、恢复、继续对话 | [notes/langgraph-stage5-21-checkpoint-thread-id.md](notes/langgraph-stage5-21-checkpoint-thread-id.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 22 | interrupt / human-in-the-loop | [notes/langgraph-stage5-22-interrupt-human-in-the-loop.md](notes/langgraph-stage5-22-interrupt-human-in-the-loop.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 23 | 节点错误处理、fallback 和流程兜底 | [notes/langgraph-stage5-23-node-error-fallback.md](notes/langgraph-stage5-23-node-error-fallback.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 24 | LangGraph 日志、trace_id 和可观测性 | [notes/langgraph-stage5-24-observability-trace-logging.md](notes/langgraph-stage5-24-observability-trace-logging.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 25 | LangGraph 测试：fake LLM / fake RAG / fake Java client | [notes/langgraph-stage5-25-agent-testing-fakes.md](notes/langgraph-stage5-25-agent-testing-fakes.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/tool_fakes.py](projects/ai-service/tests/tool_fakes.py)、[projects/ai-service/tests/test_tool_fakes.py](projects/ai-service/tests/test_tool_fakes.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 26 | 阶段 5 项目整理和面试表达 | [notes/langgraph-stage5-26-project-summary-interview.md](notes/langgraph-stage5-26-project-summary-interview.md) | 阶段 5 总复盘，梳理 [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py)、[projects/ai-service/tests/tool_fakes.py](projects/ai-service/tests/tool_fakes.py) |

## 阶段 6：生产化与评测学习规划

阶段 6 固定为 36 节，目标是把已经能运行的 RAG + 智能工单 Agent v1 往真实工程系统推进。这个阶段会补 Agent 评测、真实模型节点、工具链路生产化、持久化 checkpoint、可观测性、稳定性保护、部署编排和阶段复盘。

| 顺序 | 主题 | 笔记路径 | 代码路径 |
| --- | --- | --- | --- |
| 1 | Agent 评测基础：为什么 AI 应用不能只靠感觉判断好坏 | [notes/stage6-01-agent-evaluation-basics.md](notes/stage6-01-agent-evaluation-basics.md) | 概念讲解，无代码改动 |
| 2 | 什么是 eval：测试和评测的区别 | [notes/stage6-02-test-vs-eval.md](notes/stage6-02-test-vs-eval.md) | 概念讲解，无代码改动 |
| 3 | 设计 Agent 测试集 | [notes/stage6-03-agent-eval-dataset-design.md](notes/stage6-03-agent-eval-dataset-design.md) | [projects/ai-service/data/agent_eval/agent_cases.json](projects/ai-service/data/agent_eval/agent_cases.json)、[projects/ai-service/data/agent_eval/README.md](projects/ai-service/data/agent_eval/README.md) |
| 4 | 意图识别评测 | [notes/stage6-04-agent-intent-evaluation.md](notes/stage6-04-agent-intent-evaluation.md) | [projects/ai-service/app/agents/intent_evaluation.py](projects/ai-service/app/agents/intent_evaluation.py)、[projects/ai-service/scripts/agent_intent_eval.py](projects/ai-service/scripts/agent_intent_eval.py)、[projects/ai-service/tests/test_agent_intent_evaluation.py](projects/ai-service/tests/test_agent_intent_evaluation.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py) |
| 5 | 工单字段提取评测 | [notes/stage6-05-agent-ticket-field-evaluation.md](notes/stage6-05-agent-ticket-field-evaluation.md) | [projects/ai-service/app/agents/field_evaluation.py](projects/ai-service/app/agents/field_evaluation.py)、[projects/ai-service/scripts/agent_ticket_field_eval.py](projects/ai-service/scripts/agent_ticket_field_eval.py)、[projects/ai-service/tests/test_agent_field_evaluation.py](projects/ai-service/tests/test_agent_field_evaluation.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py) |
| 6 | Agent 路由评测 | [notes/stage6-06-agent-route-evaluation.md](notes/stage6-06-agent-route-evaluation.md) | [projects/ai-service/app/agents/route_evaluation.py](projects/ai-service/app/agents/route_evaluation.py)、[projects/ai-service/scripts/agent_route_eval.py](projects/ai-service/scripts/agent_route_eval.py)、[projects/ai-service/tests/test_agent_route_evaluation.py](projects/ai-service/tests/test_agent_route_evaluation.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py) |
| 7 | RAG + Agent 组合评测 | [notes/stage6-07-rag-agent-combination-evaluation.md](notes/stage6-07-rag-agent-combination-evaluation.md) | [projects/ai-service/app/agents/rag_agent_evaluation.py](projects/ai-service/app/agents/rag_agent_evaluation.py)、[projects/ai-service/scripts/agent_rag_eval.py](projects/ai-service/scripts/agent_rag_eval.py)、[projects/ai-service/tests/test_agent_rag_evaluation.py](projects/ai-service/tests/test_agent_rag_evaluation.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py) |
| 8 | 评测脚本设计 | [notes/stage6-08-agent-eval-script-design.md](notes/stage6-08-agent-eval-script-design.md) | [projects/ai-service/app/agents/eval_suite.py](projects/ai-service/app/agents/eval_suite.py)、[projects/ai-service/scripts/agent_eval.py](projects/ai-service/scripts/agent_eval.py)、[projects/ai-service/tests/test_agent_eval_suite.py](projects/ai-service/tests/test_agent_eval_suite.py) |
| 9 | 评测报告 | [notes/stage6-09-agent-eval-report.md](notes/stage6-09-agent-eval-report.md) | [projects/ai-service/app/agents/eval_report.py](projects/ai-service/app/agents/eval_report.py)、[projects/ai-service/scripts/agent_eval.py](projects/ai-service/scripts/agent_eval.py)、[projects/ai-service/tests/test_agent_eval_report.py](projects/ai-service/tests/test_agent_eval_report.py)、[projects/ai-service/data/agent_eval/reports/agent_eval_report.md](projects/ai-service/data/agent_eval/reports/agent_eval_report.md) |
| 10 | 坏例分析 | [notes/stage6-10-bad-case-analysis.md](notes/stage6-10-bad-case-analysis.md) | [projects/ai-service/app/agents/bad_case_analysis.py](projects/ai-service/app/agents/bad_case_analysis.py)、[projects/ai-service/scripts/agent_eval.py](projects/ai-service/scripts/agent_eval.py)、[projects/ai-service/tests/test_bad_case_analysis.py](projects/ai-service/tests/test_bad_case_analysis.py)、[projects/ai-service/data/agent_eval/reports/agent_bad_case_analysis.md](projects/ai-service/data/agent_eval/reports/agent_bad_case_analysis.md)、[projects/ai-service/data/agent_eval/reports/bad_case_analysis_sample.md](projects/ai-service/data/agent_eval/reports/bad_case_analysis_sample.md) |
| 11 | 回归评测 | [notes/stage6-11-regression-evaluation.md](notes/stage6-11-regression-evaluation.md) | [projects/ai-service/app/agents/eval_suite.py](projects/ai-service/app/agents/eval_suite.py)、[projects/ai-service/scripts/agent_eval.py](projects/ai-service/scripts/agent_eval.py)、[projects/ai-service/tests/test_agent_eval_suite.py](projects/ai-service/tests/test_agent_eval_suite.py)、[projects/ai-service/data/agent_eval/agent_cases.json](projects/ai-service/data/agent_eval/agent_cases.json)、[projects/ai-service/data/agent_eval/reports/agent_regression_report.md](projects/ai-service/data/agent_eval/reports/agent_regression_report.md)、[projects/ai-service/data/agent_eval/reports/agent_regression_bad_case_analysis.md](projects/ai-service/data/agent_eval/reports/agent_regression_bad_case_analysis.md) |
| 12 | evaluator 类型 | [notes/stage6-12-evaluator-types.md](notes/stage6-12-evaluator-types.md) | 概念讲解，对照 [projects/ai-service/app/agents/intent_evaluation.py](projects/ai-service/app/agents/intent_evaluation.py)、[projects/ai-service/app/agents/field_evaluation.py](projects/ai-service/app/agents/field_evaluation.py)、[projects/ai-service/app/agents/route_evaluation.py](projects/ai-service/app/agents/route_evaluation.py)、[projects/ai-service/app/agents/rag_agent_evaluation.py](projects/ai-service/app/agents/rag_agent_evaluation.py)、[projects/ai-service/app/agents/eval_suite.py](projects/ai-service/app/agents/eval_suite.py)、[projects/ai-service/app/agents/eval_report.py](projects/ai-service/app/agents/eval_report.py)、[projects/ai-service/app/agents/bad_case_analysis.py](projects/ai-service/app/agents/bad_case_analysis.py) |
| 13 | 真实 LLM 意图识别节点 | [notes/stage6-13-real-llm-intent-node.md](notes/stage6-13-real-llm-intent-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_llm_intent.py](projects/ai-service/tests/test_ticket_agent_llm_intent.py)、[projects/ai-service/scripts/ticket_agent_llm_intent_smoke.py](projects/ai-service/scripts/ticket_agent_llm_intent_smoke.py) |
| 14 | 真实 LLM 字段提取节点 | [notes/stage6-14-real-llm-field-extraction-node.md](notes/stage6-14-real-llm-field-extraction-node.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_llm_fields.py](projects/ai-service/tests/test_ticket_agent_llm_fields.py)、[projects/ai-service/scripts/ticket_agent_llm_field_smoke.py](projects/ai-service/scripts/ticket_agent_llm_field_smoke.py) |
| 15 | Pydantic 校验模型输出 | [notes/stage6-15-pydantic-validate-model-output.md](notes/stage6-15-pydantic-validate-model-output.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_llm_output_validation.py](projects/ai-service/tests/test_ticket_agent_llm_output_validation.py) |
| 16 | fake LLM 和真实 LLM 双模式 | [notes/stage6-16-fake-real-llm-modes.md](notes/stage6-16-fake-real-llm-modes.md) | [projects/ai-service/app/core/config.py](projects/ai-service/app/core/config.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/.env.example](projects/ai-service/.env.example)、[projects/ai-service/tests/test_config.py](projects/ai-service/tests/test_config.py)、[projects/ai-service/tests/test_ticket_agent_llm_modes.py](projects/ai-service/tests/test_ticket_agent_llm_modes.py) |
| 17 | prompt 版本管理 | [notes/stage6-17-prompt-version-management.md](notes/stage6-17-prompt-version-management.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_prompt_versions.py](projects/ai-service/tests/test_ticket_agent_prompt_versions.py)、[projects/ai-service/tests/test_ticket_agent_llm_intent.py](projects/ai-service/tests/test_ticket_agent_llm_intent.py)、[projects/ai-service/tests/test_ticket_agent_llm_fields.py](projects/ai-service/tests/test_ticket_agent_llm_fields.py) |
| 18 | 模型输出失败处理 | [notes/stage6-18-model-output-failure-handling.md](notes/stage6-18-model-output-failure-handling.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_model_output_failure.py](projects/ai-service/tests/test_ticket_agent_model_output_failure.py)、[projects/ai-service/tests/test_ticket_agent_llm_output_validation.py](projects/ai-service/tests/test_ticket_agent_llm_output_validation.py) |
| 19 | 接入真实 `query_order` 到 LangGraph | [notes/stage6-19-query-order-langgraph.md](notes/stage6-19-query-order-langgraph.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/app/tools/fake_order_tool.py](projects/ai-service/app/tools/fake_order_tool.py)、[projects/ai-service/tests/test_ticket_agent_query_order_node.py](projects/ai-service/tests/test_ticket_agent_query_order_node.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py) |
| 20 | 工具节点错误处理升级 | [notes/stage6-20-tool-node-error-handling.md](notes/stage6-20-tool-node-error-handling.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_query_order_node.py](projects/ai-service/tests/test_ticket_agent_query_order_node.py) |
| 21 | 工具权限和写操作安全回归 | [notes/stage6-21-tool-permission-write-safety-regression.md](notes/stage6-21-tool-permission-write-safety-regression.md) | [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/app/tools/tool_registry.py](projects/ai-service/app/tools/tool_registry.py)、[projects/ai-service/tests/test_ticket_agent_intent.py](projects/ai-service/tests/test_ticket_agent_intent.py)、[projects/ai-service/tests/test_tool_registry.py](projects/ai-service/tests/test_tool_registry.py) |
| 22 | 持久化 checkpoint 基础 | [notes/stage6-22-persistent-checkpoint-basics.md](notes/stage6-22-persistent-checkpoint-basics.md) | [projects/ai-service/app/agents/checkpoint_store.py](projects/ai-service/app/agents/checkpoint_store.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_checkpoint_store.py](projects/ai-service/tests/test_ticket_agent_checkpoint_store.py) |
| 23 | checkpoint 存储选型 | [notes/stage6-23-checkpoint-storage-selection.md](notes/stage6-23-checkpoint-storage-selection.md) | 概念讲解，对照 [projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/app/agents/checkpoint_store.py](projects/ai-service/app/agents/checkpoint_store.py) |
| 24 | `thread_id` 生命周期 | [notes/stage6-24-thread-id-lifecycle.md](notes/stage6-24-thread-id-lifecycle.md) | [projects/ai-service/app/agents/thread_lifecycle.py](projects/ai-service/app/agents/thread_lifecycle.py)、[projects/ai-service/app/agents/ticket_agent.py](projects/ai-service/app/agents/ticket_agent.py)、[projects/ai-service/tests/test_ticket_agent_thread_lifecycle.py](projects/ai-service/tests/test_ticket_agent_thread_lifecycle.py) |
| 25 | 会话过期与清理 | [notes/stage6-25-session-expiration-cleanup.md](notes/stage6-25-session-expiration-cleanup.md) | [projects/ai-service/app/agents/thread_cleanup.py](projects/ai-service/app/agents/thread_cleanup.py)、[projects/ai-service/app/agents/thread_lifecycle.py](projects/ai-service/app/agents/thread_lifecycle.py)、[projects/ai-service/tests/test_ticket_agent_thread_cleanup.py](projects/ai-service/tests/test_ticket_agent_thread_cleanup.py) |
| 26 | LangSmith tracing 基础 | [notes/stage6-26-langsmith-tracing-basics.md](notes/stage6-26-langsmith-tracing-basics.md) | [projects/ai-service/app/agents/langsmith_tracing.py](projects/ai-service/app/agents/langsmith_tracing.py)、[projects/ai-service/tests/test_ticket_agent_langsmith_tracing.py](projects/ai-service/tests/test_ticket_agent_langsmith_tracing.py) |
| 27 | OpenTelemetry 基础 | [notes/stage6-27-opentelemetry-basics.md](notes/stage6-27-opentelemetry-basics.md) | [projects/ai-service/app/agents/otel_tracing.py](projects/ai-service/app/agents/otel_tracing.py)、[projects/ai-service/tests/test_ticket_agent_otel_tracing.py](projects/ai-service/tests/test_ticket_agent_otel_tracing.py) |
| 28 | trace/span/log/metrics 的关系 | [notes/stage6-28-trace-span-log-metrics-relationship.md](notes/stage6-28-trace-span-log-metrics-relationship.md) | [projects/ai-service/app/agents/observability_signals.py](projects/ai-service/app/agents/observability_signals.py)、[projects/ai-service/tests/test_ticket_agent_observability_signals.py](projects/ai-service/tests/test_ticket_agent_observability_signals.py) |
| 29 | 生产日志字段设计 | [notes/stage6-29-production-log-field-design.md](notes/stage6-29-production-log-field-design.md) | [projects/ai-service/app/agents/production_logging.py](projects/ai-service/app/agents/production_logging.py)、[projects/ai-service/tests/test_ticket_agent_production_logging.py](projects/ai-service/tests/test_ticket_agent_production_logging.py) |
| 30 | 成本、token 和延迟指标 | [notes/stage6-30-cost-token-latency-metrics.md](notes/stage6-30-cost-token-latency-metrics.md) | [projects/ai-service/app/agents/llm_metrics.py](projects/ai-service/app/agents/llm_metrics.py)、[projects/ai-service/tests/test_ticket_agent_llm_metrics.py](projects/ai-service/tests/test_ticket_agent_llm_metrics.py) |
| 31 | timeout 超时策略 | [notes/stage6-31-timeout-strategy.md](notes/stage6-31-timeout-strategy.md) | [projects/ai-service/app/agents/timeout_strategy.py](projects/ai-service/app/agents/timeout_strategy.py)、[projects/ai-service/tests/test_ticket_agent_timeout_strategy.py](projects/ai-service/tests/test_ticket_agent_timeout_strategy.py) |
| 32 | retry 重试策略 | [notes/stage6-32-retry-strategy.md](notes/stage6-32-retry-strategy.md) | [projects/ai-service/app/agents/retry_strategy.py](projects/ai-service/app/agents/retry_strategy.py)、[projects/ai-service/tests/test_ticket_agent_retry_strategy.py](projects/ai-service/tests/test_ticket_agent_retry_strategy.py) |
| 33 | rate limit、circuit breaker 和降级 | [notes/stage6-33-rate-limit-circuit-breaker-degradation.md](notes/stage6-33-rate-limit-circuit-breaker-degradation.md) | [projects/ai-service/app/agents/resilience_strategy.py](projects/ai-service/app/agents/resilience_strategy.py)、[projects/ai-service/tests/test_ticket_agent_resilience_strategy.py](projects/ai-service/tests/test_ticket_agent_resilience_strategy.py) |
| 34 | Docker Compose 本地编排 | [notes/stage6-34-docker-compose-local-orchestration.md](notes/stage6-34-docker-compose-local-orchestration.md) | [compose.yml](compose.yml)、[compose.env.example](compose.env.example) |
| 35 | health check、readiness 和 CI 自动回归 | [notes/stage6-35-health-readiness-ci-regression.md](notes/stage6-35-health-readiness-ci-regression.md) | [projects/ai-service/app/routers/health.py](projects/ai-service/app/routers/health.py)、[projects/java-mock-service/app/routers/health.py](projects/java-mock-service/app/routers/health.py)、[scripts/run_regression.py](scripts/run_regression.py)、[.github/workflows/ci.yml](.github/workflows/ci.yml) |
| 36 | 阶段 6 项目整理和面试表达 | [notes/stage6-36-project-summary-interview-expression.md](notes/stage6-36-project-summary-interview-expression.md) | 阶段 6 主线复盘、生产化能力地图、项目 1/3/5 分钟讲法、面试问答、简历表达、当前项目边界和下一阶段方向 |

## M6：作品整理和面试准备快速版

M6 固定为 5 节，目标是把当前 AI 客服工单系统学习项目快速整理成能展示、能讲清楚、能写进简历的作品项目。M6 不把项目强行包装成完整生产系统，完成后进入真实 Java Spring Boot + MySQL/Redis 业务服务学习。

| 顺序 | 主题 | 笔记路径 | 产出 |
| --- | --- | --- | --- |
| 1 | 项目定位和作品化目标 | [notes/m6-01-project-positioning-and-portfolio-goals.md](notes/m6-01-project-positioning-and-portfolio-goals.md) | 项目定位、作品化边界、README 基础文案、面试回答口径、M6 产出目标 |
| 2 | 整理 GitHub 首页 README | [notes/m6-02-github-homepage-readme.md](notes/m6-02-github-homepage-readme.md) | README 首页作品化、项目定位、核心能力、技术栈地图、快速阅读入口、当前边界 |
| 3 | 架构图和核心流程图 | [notes/m6-03-architecture-and-core-flow-diagrams.md](notes/m6-03-architecture-and-core-flow-diagrams.md) | [docs/project-diagrams.md](docs/project-diagrams.md)、整体架构图、RAG 问答流程图、智能工单 Agent 流程图、工具调用安全流程图 |
| 4 | 本地运行说明和演示脚本 | [notes/m6-04-local-run-and-demo-script.md](notes/m6-04-local-run-and-demo-script.md) | [docs/local-run-and-demo.md](docs/local-run-and-demo.md)、Windows 本地最小运行、真实模型可选演示、Qdrant/Milvus 可选演示、统一回归、常见问题 |
| 5 | 简历描述、面试讲稿、常见追问 | [notes/m6-05-resume-interview-qa.md](notes/m6-05-resume-interview-qa.md) | [docs/interview-and-resume.md](docs/interview-and-resume.md)、简历 bullet、1/3/5 分钟讲稿、常见面试追问、项目不足和后续路线 |

## 阶段 7：真实 Java Spring Boot + MySQL/Redis 业务服务

阶段 7 不重复学习传统 Spring Boot 基础。由于已有 Java 后端经验，这一阶段重点学习传统 Java 后端和 AI Agent 接触时新增的工程问题：边界设计、工具接口契约、读写安全、幂等、权限、错误码、trace_id、契约测试，以及 Python AI 服务如何对接真实 Java 业务系统。

| 顺序 | 主题 | 笔记路径 | 产出 |
| --- | --- | --- | --- |
| 1 | AI Agent 调用传统 Java 后端时的边界设计 | [notes/stage7-01-ai-agent-java-boundary-design.md](notes/stage7-01-ai-agent-java-boundary-design.md) | 模型意图和后端执行边界、读写工具分级、DTO/Entity 边界、错误码、幂等、权限、trace_id、阶段 7 改造方向 |
| 2 | 面向 Tool Calling 的 Java API 契约设计 | [notes/stage7-02-tool-calling-java-api-contract.md](notes/stage7-02-tool-calling-java-api-contract.md) | [docs/java-ai-api-contract.md](docs/java-ai-api-contract.md)、订单查询和工单创建接口契约、统一响应、请求 DTO、响应 DTO、错误码、Header、字段白名单、契约测试清单 |
| 3 | 真实 Spring Boot 服务骨架和领域模型 | [notes/stage7-03-spring-boot-service-skeleton-domain-model.md](notes/stage7-03-spring-boot-service-skeleton-domain-model.md) | [projects/java-business-service](projects/java-business-service)、Spring Boot 骨架、internal API、统一响应、错误码、Header 校验、订单/工单领域模型、内存 Repository、幂等雏形、MockMvc 契约测试 |
| 4 | MySQL 业务数据模型 | 已完成 | [notes/stage7-04-mysql-business-data-model.md](notes/stage7-04-mysql-business-data-model.md)、[docs/java-business-database-design.md](docs/java-business-database-design.md)、用户表、订单表、工单表、工单事件表、索引、唯一约束、幂等字段、AI 写操作审计字段 |
| 5 | 查询订单读工具真实化 | 已完成 | [notes/stage7-05-spring-boot-mysql-order-query.md](notes/stage7-05-spring-boot-mysql-order-query.md)、Spring Boot DataSource、JDBC、JdbcTemplate、HikariCP、orders 表初始化、JdbcOrderRepository、H2 测试配置、Windows MySQL smoke |
| 6 | 创建工单写工具真实化 | 已完成 | [notes/stage7-06-mysql-ticket-write-transaction.md](notes/stage7-06-mysql-ticket-write-transaction.md)、tickets 表、ticket_events 表、`@Transactional`、MySQL 唯一索引幂等兜底、request_fingerprint、DuplicateKeyException 处理、真实 MySQL smoke |
| 7 | Redis 幂等、缓存和限流 | 已完成 | `notes/stage7-07-redis-idempotency-cache-rate-limit.md`、Spring Data Redis、订单 read-through cache、工单幂等缓存、Redis fixed window 限流、Redis 失败降级、真实 Redis/MySQL smoke |
| 7.5 | Java 服务结构传统化重构 + MyBatis | 已完成 | [notes/stage7-075-java-service-traditional-mybatis-refactor.md](notes/stage7-075-java-service-traditional-mybatis-refactor.md)；Java business service 已对齐到 `controller/service/service.impl/mapper/entity/dto/config/exception/common` 风格，并用 MyBatis Mapper + XML 替换 JdbcTemplate；保留 DTO 白名单、权限、幂等、trace_id、错误码和 internal token 边界 |
| 8 | AI 场景下的内部鉴权和用户身份传递 | 已完成 | `notes/stage7-08-internal-auth-user-identity.md`、`notes/stage7-08-internal-auth-user-identity-manual-tasks.md`；internal allowed caller 配置化、`X-Tenant-Id` 必传、trace/caller/user/tenant 基础格式校验、模型不能伪造用户身份、Java 业务权限兜底测试 |
| 9 | Java 错误码到 AI 用户回答 | 已完成 | `notes/stage7-09-java-error-code-to-ai-user-answer.md`、`notes/stage7-09-java-error-code-to-ai-user-answer-manual-tasks.md`；新增 Python `java_error_mapping.py`，把 Java 机器错误码映射为安全 `AppException` 和用户可理解提示，隐藏 internal auth、服务异常、契约错误等内部细节 |
| 10 | trace_id 串联 Python + Java | 已完成 | `notes/stage7-10-trace-id-python-java-chain.md`、`notes/stage7-10-trace-id-python-java-chain-manual-tasks.md`；Java 新增 `TraceFilter`，响应头统一返回 `X-Trace-Id`，MDC 写入 `trace_id`，Python Java client 日志记录 `upstream_trace_id` |
| 11 | 契约测试和集成测试 | 已完成 | `notes/stage7-11-contract-and-integration-tests.md`、`notes/stage7-11-contract-and-integration-tests-manual-tasks.md`；新增共享契约文件 `contracts/java-business-service/internal-api-contract-cases.json`、Java provider 契约测试、Python consumer 契约模型和测试，明确区分历史 mock 链路与真实 Java business contract |
| 12 | 阶段 7 项目整理 | 已完成 | `notes/stage7-12-project-summary.md`；完成阶段 7 能力地图、当前项目边界、mock 链路与真实 Java business 链路关系、后续学习方向整理，并更新 README、进度、契约、架构图、运行说明和面试材料 |

## 当前目标

12 周内完成两个能展示的项目：

1. 企业知识库 RAG 系统
2. 智能工单 Agent

第三个项目“业务数据助手”作为加分项，等前两个主项目稳定后再做。

每次继续学习时，优先更新 `docs/learning-progress.md`，再把代码、笔记和复盘分别放入对应目录。
