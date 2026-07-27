# Java + Python + AI 学习进度

## 当前状态

```text
路线已确定：Java 后端 + Python AI 服务 + LangChain/LangGraph + RAG/Agent 工程化
当前阶段：M6 作品整理和面试准备快速版已完成，第 5 节 简历描述、面试讲稿、常见追问 已完成。下一步进入阶段 7：真实 Java Spring Boot + MySQL/Redis 业务服务。
主要仓库：D:\wendang\java+python+ai
执行路线：docs/ai-application-learning-roadmap.md
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

- [ ] Spring Boot 业务服务
- [ ] 用户权限接口
- [ ] 订单查询接口
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
- [ ] 限流
- [x] 重试
- [ ] 缓存
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
