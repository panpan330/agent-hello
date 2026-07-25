# 学习资料清单

维护原则：

- 官方文档优先，用来确认概念、API 和最佳实践。
- GitHub 学习笔记和教程作为辅助，用来补中文解释和练习。
- 视频只作为理解辅助，不用视频替代动手编码。
- 每个资料都要服务当前学习阶段，不为了收藏资料而收藏。
- 学完一个资料，要沉淀到 `notes/`，并用代码验证。

## 1. Python 基础

### 主资料

- [Python 官方教程](https://docs.python.org/3/tutorial/index.html)
  - 用途：确认 Python 语法和语言特性。
  - 使用方式：遇到变量、列表、字典、函数、异常、模块等概念时查官方解释。

- [Datawhale：聪明办法学 Python 第二版](https://github.com/datawhalechina/learn-python-the-smart-way-v2)
  - 用途：中文系统入门资料，偏计算机科学和 AI 学习方向。
  - 使用方式：作为 Python 基础阶段的主要中文参考。

### 辅助资料

- [jackfrued/Python-100-Days](https://github.com/jackfrued/python-100-days)
  - 用途：中文内容完整，覆盖 Python 基础、Web、数据、项目实践。
  - 使用方式：不按 100 天完整照学，只按当前知识点查对应章节。

- [shibing624/python-tutorial](https://github.com/shibing624/python-tutorial)
  - 用途：偏实用教程，包含 Python 基础、高级特性、Web、爬虫等。
  - 使用方式：作为补充例子和复习材料。

### 视频辅助

- [小甲鱼：零基础入门学习 Python](https://www.bilibili.com/video/BV1xs411Q799/)
  - 用途：适合零基础听概念。
  - 使用方式：只看当前知识点对应视频，不刷全集。

## 2. Python 项目环境与 uv

### 主资料

- [uv 官方文档](https://docs.astral.sh/uv/)
  - 用途：确认 uv 的项目管理、依赖管理、虚拟环境、lock 文件用法。

- [uv 项目指南](https://docs.astral.sh/uv/guides/projects/)
  - 用途：学习 `uv init`、`uv add`、`uv run`、`uv sync`。

### 已完成练习

- `projects/python-basics`
- `notes/python-project-environment.md`

## 3. HTTP / JSON / requests

### 主资料

- [MDN：HTTP messages](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Messages)
  - 用途：理解 HTTP 请求和响应的基本结构。

- [MDN：HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods)
  - 用途：理解 GET、POST、PUT、PATCH、DELETE 等方法的语义。

- [MDN：POST request method](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/POST)
  - 用途：理解 POST 用于向服务端发送数据，以及请求体类型由 `Content-Type` 指明。

- [MDN：Content-Type header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Type)
  - 用途：理解 `Content-Type: application/json` 表示请求体或响应体的媒体类型。

- [MDN：HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)
  - 用途：理解 200、404、422、500 等状态码。

- [Requests 官方 Quickstart](https://requests.readthedocs.io/en/latest/user/quickstart/)
  - 用途：学习 GET、POST、headers、JSON、timeout 等基础用法。

- [Requests 中文快速上手](https://docs.python-requests.org/projects/cn/zh-cn/latest/user/quickstart.html)
  - 用途：中文辅助理解。

### HTTPX 跨服务调用

- [HTTPX Quickstart](https://www.python-httpx.org/quickstart/)
  - 用途：学习 `httpx.Client`、GET 请求、读取 JSON 响应和基础请求写法。
- [HTTPX Timeouts](https://www.python-httpx.org/advanced/timeouts/)
  - 用途：理解跨服务 HTTP 调用为什么必须配置 timeout，以及 timeout 不是可选细节。
- [HTTPX Exceptions](https://www.python-httpx.org/exceptions/)
  - 用途：理解 `TimeoutException`、`RequestError` 等异常层级，方便把底层错误映射成项目统一错误码。
- [HTTPX Transports and MockTransport](https://www.python-httpx.org/advanced/transports/)
  - 用途：学习测试时如何模拟 HTTP 响应，避免单元测试依赖真实外部服务。

### 辅助练习

- [4GeeksAcademy: Python API Requests Tutorial and Exercises](https://github.com/4GeeksAcademy/python-http-requests-api-tutorial-exercises)
  - 用途：练习 HTTP 请求和 API 调用。

## 4. FastAPI

### 主资料

- [FastAPI 官方 Tutorial](https://fastapi.tiangolo.com/tutorial/)
  - 用途：学习路由、请求参数、响应模型、依赖注入、自动文档。

- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
  - 用途：学习 FastAPI 如何读取 JSON 请求体，并在下一节配合 Pydantic 校验数据。

- [FastAPI Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
  - 用途：学习 `response_model`、响应文档、响应校验、输出过滤和响应模型边界。

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
  - 用途：学习 `TestClient`，用 pytest 测试 GET、POST、JSON body 和响应状态码。

- [FastAPI TestClient Reference](https://fastapi.tiangolo.com/reference/testclient/)
  - 用途：查 `TestClient` 的请求方法和行为。

- [FastAPI Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)
  - 用途：学习 FastAPI 项目中如何集中读取环境变量和 `.env` 配置。

- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
  - 用途：学习如何在请求进入路由前、响应返回客户端前统一处理逻辑，例如 trace_id 和请求耗时。

- [FastAPI Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
  - 用途：学习 `HTTPException`、自定义异常处理器、覆盖默认校验错误响应。

- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
  - 用途：学习 `CORSMiddleware`、`allow_origins`、`allow_methods`、`allow_headers` 等基础配置。

- [FastAPI HTTPException Reference](https://fastapi.tiangolo.com/reference/exceptions/)
  - 用途：理解 `HTTPException` 的定位，它适合表达客户端请求相关错误，不适合直接暴露服务端内部错误。

- [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
  - 用途：理解 `FastAPI()`、path operation、装饰器、`/docs` 和 OpenAPI。

- [FastAPI Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
  - 用途：学习 `APIRouter`、多文件路由拆分、`include_router`、`prefix` 和 `tags`。

- [FastAPI APIRouter Reference](https://fastapi.tiangolo.com/reference/apirouter/)
  - 用途：查 `APIRouter`、`prefix`、`tags`、`dependencies` 等参数含义。

- [FastAPI Run a Server Manually](https://fastapi.tiangolo.com/deployment/manually/)
  - 用途：理解 FastAPI、ASGI、Uvicorn 和 `main:app` 的关系。

- [FastAPI GitHub 仓库](https://github.com/fastapi/fastapi)
  - 用途：确认框架定位和官方示例。

### 中文辅助

- [FastAPI-Learning-Example](https://github.com/oinsd/FastAPI-Learning-Example)
  - 用途：中文视频配套示例。

- [fastapi-best-practices-zh-cn](https://github.com/hellowac/fastapi-best-practices-zh-cn)
  - 用途：进阶阶段看项目结构、异步、最佳实践。
  - 注意：不要一开始就看，等基础接口会写后再看。

## 5. Pydantic

### 主资料

- [Pydantic 官方 Get Started](https://pydantic.dev/docs/validation/latest/get-started/)
  - 用途：理解数据校验的作用。

- [Pydantic Models 文档](https://pydantic.dev/docs/validation/latest/concepts/models/)
  - 用途：学习 `BaseModel`、字段类型、嵌套模型、校验错误。

- [Pydantic Fields 文档](https://pydantic.dev/docs/validation/latest/concepts/fields/)
  - 用途：学习 `Field()`、默认值、字段约束和字段说明。

- [Pydantic Error Handling 文档](https://pydantic.dev/docs/validation/latest/errors/errors/)
  - 用途：学习 `ValidationError` 和结构化错误信息。

### 配置相关资料

- [Pydantic Settings Management](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/)
  - 用途：学习 `BaseSettings`、`SettingsConfigDict`、环境变量和 `.env` 文件读取。

- [python-dotenv PyPI](https://pypi.org/project/python-dotenv/)
  - 用途：了解 `.env` 文件读取能力来自哪里，知道它通常作为配置读取的底层依赖。

## 6. pytest

### 主资料

- [pytest fixtures reference](https://docs.pytest.org/en/stable/reference/fixtures.html)
  - 用途：理解 `conftest.py`、fixture 共享和测试复用。

- [pytest about fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
  - 用途：从概念上理解 fixture 是测试上下文和准备数据。

## 7. logging 日志

### 主资料

- [Python 官方文档：logging](https://docs.python.org/3/library/logging.html)
  - 用途：理解 `getLogger()`、logger、handler、formatter、日志层级和日志传播。

- [Python 官方文档：Logging HOWTO](https://docs.python.org/3/howto/logging.html)
  - 用途：入门理解日志是什么、什么时候用 `print`、什么时候用 `logging`、各日志级别的含义。

- [Uvicorn Settings - Logging](https://uvicorn.dev/settings/)
  - 用途：理解 Uvicorn 的 `--log-level` 和 `--log-config`。

- [Uvicorn Logging](https://uvicorn.dev/concepts/logging/)
  - 用途：理解 Uvicorn 如何使用 Python logging，以及后续如何自定义更完整的日志配置。

## 8. trace_id 请求追踪

### 主资料

- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
  - 用途：理解 middleware 如何在请求前后执行，适合做 trace_id、耗时统计和通用请求日志。

- [Python 官方文档：contextvars](https://docs.python.org/3/library/contextvars.html)
  - 用途：理解 `ContextVar`，用于保存当前请求自己的 trace_id，避免并发请求串号。

- [Python 官方文档：Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
  - 用途：理解如何给日志补充上下文信息，例如 trace_id。

- [Python 官方文档：uuid](https://docs.python.org/3/library/uuid.html)
  - 用途：理解 `uuid4()` 如何生成随机唯一编号。

## 9. 统一异常处理

### 主资料

- [FastAPI Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
  - 用途：理解 FastAPI 如何处理 `HTTPException`、自定义异常和 `RequestValidationError`。

- [FastAPI HTTPException Reference](https://fastapi.tiangolo.com/reference/exceptions/)
  - 用途：确认 `HTTPException` 的参数和适用场景。

- [Starlette Exceptions](https://starlette.dev/exceptions/)
  - 用途：理解 FastAPI 底层 Starlette 的异常处理机制，以及为什么要处理 Starlette 的 HTTPException。

- [Python 官方文档：Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html)
  - 用途：复习 Python 异常基础，理解异常是运行时错误以及如何处理。

## 10. CORS 基础

### 主资料

- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
  - 用途：理解 FastAPI 中如何使用 `CORSMiddleware` 允许指定前端来源访问后端接口。

- [MDN：Cross-Origin Resource Sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)
  - 用途：理解 CORS 的浏览器机制、请求头、响应头和预检请求。

- [MDN：Same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy)
  - 用途：理解什么是同源，为什么协议、域名、端口任一不同都算不同源。

## 11. LangChain

### 主资料

- [LangChain 官方 Overview](https://docs.langchain.com/oss/python/langchain/overview)
  - 用途：理解 LangChain 在模型、prompt、tool、agent harness 中的位置。

- [LangChain Models](https://docs.langchain.com/oss/python/langchain/models)
  - 用途：理解 ChatModel 的 `invoke()`、`stream()`、`batch()` 等基础调用方式。

- [LangChain Messages](https://docs.langchain.com/oss/python/langchain/messages)
  - 用途：理解 `SystemMessage`、`HumanMessage`、`AIMessage` 和 `ToolMessage` 的角色。

- [LangChain ChatOpenAI integration](https://docs.langchain.com/oss/python/integrations/chat/openai)
  - 用途：理解 `langchain-openai`、`ChatOpenAI`、`base_url`、`api_key` 和 OpenAI-compatible 调用边界。

- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
  - 用途：理解 agent loop、model、tools、system prompt、structured output 和 harness 的关系。

- [LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)
  - 用途：理解 LangChain 如何把 Python callable 包装成模型可请求的工具。

- [LangChain Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
  - 用途：理解 LangChain 结构化输出的 provider strategy、tool strategy、Pydantic schema 和错误处理。

- [LangChain Python Reference](https://reference.langchain.com/python/langchain)
  - 用途：查 API 细节。

## 12. LangGraph

### 主资料

- [LangGraph 官方 Overview](https://docs.langchain.com/oss/python/langgraph/overview)
  - 用途：理解有状态、长流程、可恢复 agent 编排。

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
  - 用途：做第一个最小图流程。

- [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
  - 用途：理解固定工作流和动态 Agent 的区别。

- [LangGraph Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)
  - 用途：理解如何把客服 Agent 拆成离散节点、设计 State，并区分 LLM step、data step、action step 和 user input step。

- [LangGraph Fault tolerance](https://docs.langchain.com/oss/python/langgraph/fault-tolerance)
  - 用途：理解 LangGraph 中临时错误、LLM 可恢复错误、用户可修复错误、恢复分支、未知错误、retry 和 error handler 的边界。

- [LangGraph LangSmith Observability](https://docs.langchain.com/oss/python/langgraph/observability)
  - 用途：理解 LangGraph/LangSmith 里的 trace、run、metadata、tracing 开关和敏感信息脱敏思路，作为第 24 节本地 logging 的生产化参考。

- [LangGraph Streaming](https://docs.langchain.com/oss/python/langgraph/streaming)
  - 用途：理解 `updates`、`values`、`messages`、`checkpoints`、`tasks`、`debug` 等 stream mode，以及 stream 与日志、trace 的区别。

- [LangGraph Test](https://docs.langchain.com/oss/python/langgraph/test)
  - 用途：理解如何用 pytest 测试 LangGraph，包括节点级测试、编译图测试、checkpoint、`update_state(..., as_node=...)`、`interrupt_after` 和局部执行。

- [LangSmith Observability concepts](https://docs.langchain.com/langsmith/observability-concepts)
  - 用途：理解 LangSmith 里 trace/run 的概念，为后续把本地日志升级成可视化 tracing 做准备。

- [LangChain Academy: Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)
  - 用途：系统课程辅助理解。

### 阶段 5 使用方式

阶段 5：LangGraph 智能工单 Agent。当前先按 26 节主线推进，资料使用顺序如下：

1. 第 1-3 节优先看 LangGraph Overview，理解 LangGraph 为什么用于有状态 Agent 流程。
2. 第 4-12 节配合 LangGraph Quickstart，重点理解 State、Reducer、MessagesState、StateGraph、node、edge、conditional edge、START/END、invoke 和 stream。
3. 第 13-22 节结合 LangGraph Workflows and agents，把智能工单流程拆成意图识别、RAG 回答、工单字段提取、用户确认、Java API 调用、checkpoint、interrupt 和 human-in-the-loop。
4. 第 23-26 节回到项目代码，重点做错误处理、trace_id、fake 测试、阶段复盘和面试表达。

### 本仓库阶段 5 笔记

- [阶段 5 第 1 节：LangGraph 是什么，为什么现在才学](../notes/langgraph-stage5-01-what-is-langgraph.md)
  - 用途：理解 LangGraph 的定位、为什么在 Tool Calling 和 RAG 之后学习、它和 LangChain / 普通函数流程的边界，以及阶段 5 智能工单 Agent 的整体学习路线。

- [阶段 5 第 2 节：LangGraph 和 LangChain / 普通函数流程的区别](../notes/langgraph-stage5-02-langgraph-vs-langchain-function-flow.md)
  - 用途：建立普通函数 / service、LangChain、LangGraph 的三层分工，理解 workflow 与 agent 的区别，并明确后续智能工单 Agent 为什么要用 LangGraph 编排但不能把所有业务逻辑都塞进图里。

- [阶段 5 第 3 节：Agent 流程和状态机基础](../notes/langgraph-stage5-03-agent-flow-state-machine-basics.md)
  - 用途：理解 Agent 为什么是多步骤、有状态、会在状态之间转移的业务流程，掌握状态、事件、转移、动作、守卫条件、副作用、HTTP 无状态与 Agent 有状态等基础，为后续 StateGraph 代码做准备。

- [阶段 5 第 4 节：State 是什么：Agent 为什么需要状态](../notes/langgraph-stage5-04-state-agent-needs-state.md)
  - 用途：理解 LangGraph State 是所有节点共享的结构化流程快照，区分 State 与局部变量、请求体、响应体、messages、缓存和日志，并掌握智能工单 Agent 的初版 State 字段设计原则。

- [阶段 5 第 5 节：Reducer 是什么：状态字段怎么合并](../notes/langgraph-stage5-05-reducer-state-merge.md)
  - 用途：理解 State 字段的新旧值如何合并，掌握默认覆盖、自定义 reducer、`Annotated`、`operator.add`、messages 追加、ticket_fields 字典合并和并行节点更新冲突等基础。

- [阶段 5 第 6 节：MessagesState：多轮对话消息怎么保存](../notes/langgraph-stage5-06-messages-state.md)
  - 用途：理解 messages 是模型多轮上下文，掌握 `SystemMessage`、`HumanMessage`、`AIMessage`、`ToolMessage`、`add_messages`、`MessagesState`，以及 messages 与结构化业务 State 的分工。

- [阶段 5 第 7 节：StateGraph 最小图](../notes/langgraph-stage5-07-stategraph-minimal-graph.md)
  - 用途：第一次真正运行 LangGraph，理解 `StateGraph`、State schema、node、edge、`START`、`END`、`compile()`、`invoke()` 和节点返回局部 State 更新的完整最小链路。

- [阶段 5 第 8 节：node 节点是什么](../notes/langgraph-stage5-08-what-is-node.md)
  - 用途：理解 node 是图里的单一职责处理步骤，掌握 node 的输入 State、局部 State 更新、命名、粒度、测试方式，以及调用 service、模型、外部 API 和处理副作用时的边界。

- [阶段 5 第 9 节：edge 边是什么](../notes/langgraph-stage5-09-what-is-edge.md)
  - 用途：理解 edge 是节点之间的连接关系，掌握固定 edge、`add_edge()`、`START` 入口、`END` 出口、edge 和 node 的区别，以及固定边和条件边的边界。

- [阶段 5 第 10 节：conditional edge 条件分支](../notes/langgraph-stage5-10-conditional-edge.md)
  - 用途：理解 conditional edge 如何根据 State 动态选择下一步节点，掌握 routing function、path map、`add_conditional_edges()`、普通 edge 与条件 edge 的区别，以及智能工单 Agent 中意图分流、字段完整性分流、工具结果分流的基础。

- [阶段 5 第 11 节：START / END 和流程结束](../notes/langgraph-stage5-11-start-end-flow-finish.md)
  - 用途：理解 `START` 是虚拟入口、`END` 是虚拟终点，掌握入口边、结束边、条件分支直接进入 `END`、本轮流程结束和业务成功的区别，以及智能工单 Agent 中何时继续、何时结束。

- [阶段 5 第 12 节：graph.invoke / graph.stream：普通执行和流式执行](../notes/langgraph-stage5-12-invoke-stream.md)
  - 用途：理解 `invoke` 一次性返回最终 State，`stream` 逐步观察执行过程，掌握 `stream_mode="updates"`、`stream_mode="values"`、`version="v2"`、节点增量更新和完整 State 快照的区别。

- [阶段 5 第 13 节：智能工单 Agent 总流程设计](../notes/langgraph-stage5-13-ticket-agent-overall-design.md)
  - 用途：把前 12 节 LangGraph 基础接入智能工单 Agent v1，明确业务边界、主流程、State 字段、节点拆分、普通边和条件边设计、RAG/订单查询/工单创建路线、用户确认机制和后续实现顺序。

- [阶段 5 第 14 节：意图识别节点](../notes/langgraph-stage5-14-intent-classification-node.md)
  - 用途：实现智能工单 Agent 的第一层业务分流，理解意图识别、规则分类器、固定 intent 集合、`classify_intent_node`、`route_by_intent`、六类业务路线和占位节点测试。

- [阶段 5 第 15 节：RAG 知识库回答节点](../notes/langgraph-stage5-15-rag-policy-node.md)
  - 用途：把 `policy_question` 路线从占位节点升级成 RAG 知识库回答节点，理解 `PolicyRagService`、fake RAG service、`RagAnswer`、引用来源、无资料兜底和 RAG 结果写入 Agent State。

- [阶段 5 第 16 节：判断是否需要创建工单](../notes/langgraph-stage5-16-decide-ticket-need.md)
  - 用途：理解智能客服 Agent 为什么不能所有问题都创建工单，也不能所有问题都只回答，掌握 `decide_ticket_need` 判断节点、`needs_ticket`、`ticket_need_reason`、`ticket_need_source`、条件边和工单流程入口分支。

- [阶段 5 第 17 节：工单字段提取节点](../notes/langgraph-stage5-17-ticket-field-extraction-node.md)
  - 用途：理解工单字段、字段抽取、字段缺失和结构化 State，掌握 `TicketFields`、`extract_ticket_fields`、`find_missing_ticket_fields`、`ticket_fields`、`missing_ticket_fields` 和 `ticket_fields_complete`。

- [阶段 5 第 18 节：缺失字段追问节点](../notes/langgraph-stage5-18-missing-field-follow-up-node.md)
  - 用途：理解字段缺失时为什么要追问、字段完整时为什么不追问，掌握 `route_by_ticket_fields_complete`、`build_missing_ticket_fields_question`、`ask_missing_ticket_fields_node` 和追问 State 字段设计。

- [阶段 5 第 19 节：用户确认节点](../notes/langgraph-stage5-19-ticket-confirmation-node.md)
  - 用途：理解字段完整不等于用户授权，掌握用户确认节点、待确认工单、确认 ID、`pending_ticket_confirmation`、确认话术、字段完整进入确认和字段缺失仍追问的业务边界。

- [阶段 5 第 20 节：调用 Java mock 创建工单节点](../notes/langgraph-stage5-20-java-mock-create-ticket-node.md)
  - 用途：理解创建工单这种写操作为什么必须在用户确认之后执行，掌握 `TicketFields` 到 `CreateTicketArgs` 的契约映射、幂等键、`TicketCreator` 依赖注入、`create_ticket_node`、确认后条件边和 fake client 测试。

- [阶段 5 第 21 节：checkpoint 和 thread_id：中断、恢复、继续对话](../notes/langgraph-stage5-21-checkpoint-thread-id.md)
  - 用途：理解多轮 Agent 为什么需要保存 State，掌握 checkpoint、thread_id、`MemorySaver`、`graph.get_state`、`graph.update_state`、`as_node`、`graph.invoke(None)` 和待确认工单的手动恢复执行。

- [阶段 5 第 22 节：interrupt / human-in-the-loop](../notes/langgraph-stage5-22-interrupt-human-in-the-loop.md)
  - 用途：理解 LangGraph 如何在节点内部正式暂停并等待人类输入，掌握 `interrupt()`、`Command(resume=...)`、`__interrupt__`、结构化 interrupt payload、resume 后节点重跑、副作用边界和工单确认恢复执行。

- [阶段 5 第 23 节：节点错误处理、fallback 和流程兜底](../notes/langgraph-stage5-23-node-error-fallback.md)
  - 用途：理解 Agent 节点错误分类、业务失败和程序异常区别、fallback State、创建工单失败兜底、图级安全执行入口、interrupt 恢复失败兜底，以及失败路径测试。

- [阶段 5 第 24 节：LangGraph 日志、trace_id 和可观测性](../notes/langgraph-stage5-24-observability-trace-logging.md)
  - 用途：理解 Agent 可观测性基础，掌握 logging、trace_id、thread_id、node_history 的分工，Agent 运行日志、创建工单节点日志、日志安全边界和 `caplog` 日志测试。

- [阶段 5 第 25 节：LangGraph 测试：fake LLM / fake RAG / fake Java client](../notes/langgraph-stage5-25-agent-testing-fakes.md)
  - 用途：理解复杂 Agent 测试分层，掌握 fake LLM / fake RAG / fake Java client、依赖注入、节点级测试、整图路径测试、checkpoint 局部执行、interrupt/fallback/logging 测试和测试替身设计。

- [阶段 5 第 26 节：阶段 5 项目整理和面试表达](../notes/langgraph-stage5-26-project-summary-interview.md)
  - 用途：复盘阶段 5 的 LangGraph 智能工单 Agent v1，梳理完整架构、主链路、节点职责、State 字段、测试体系、验收清单、面试表达、当前限制和下一阶段生产化方向。

## 13. 阶段 6：生产化与评测资料

阶段 6 固定为 36 节，目标是把 RAG + 智能工单 Agent v1 往真实工程系统推进。资料使用顺序先以本仓库笔记为主，再结合官方文档理解 eval、tracing、OpenTelemetry 和 Docker Compose。

### 主资料

- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation)
  - 用途：理解 dataset、evaluator、experiment、offline evaluation、online evaluation，以及如何用固定样本评测 AI 应用质量。

- [LangSmith Evaluation Concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
  - 用途：理解为什么 LLM 输出不稳定，为什么需要把“好”拆成可衡量的标准。

- [LangSmith Evaluation Types](https://docs.langchain.com/langsmith/evaluation-types)
  - 用途：理解 LLM-as-judge、code evaluator、summary evaluator、pairwise evaluator 等评测器类型，后续判断什么指标适合自动化，什么指标适合人工复核。

- [LangSmith How to evaluate agents](https://docs.langchain.com/langsmith/evaluate-llm-application)
  - 用途：理解 Agent 评测如何围绕 dataset、target function、evaluator 和 experiment 组织，而不是只靠临时试问。

- [LangSmith Manage Datasets](https://docs.langchain.com/langsmith/manage-datasets)
  - 用途：理解评测数据集如何版本化、筛选、拆分和导出，为后续回归评测做准备。

- [LangSmith Example data format](https://docs.langchain.com/langsmith/example-data-format)
  - 用途：理解评测样本里的 inputs、outputs/reference outputs 和 metadata 字段，对照本地 agent_cases.json 的 inputs/expected/metadata 结构。

- [OpenAI Evals Guide](https://platform.openai.com/docs/guides/evals)
  - 用途：作为 eval 概念和评测流程的补充资料，帮助理解模型应用上线前为什么需要固定样本、指标和报告。

- [LangGraph Persistence / Memory](https://docs.langchain.com/oss/python/langgraph/persistence)
  - 用途：理解 checkpoint、thread、持久化状态和多轮 Agent 恢复能力。

- [LangGraph LangSmith Observability](https://docs.langchain.com/oss/python/langgraph/observability)
  - 用途：理解 LangGraph 流程如何接入 LangSmith tracing，观察节点执行、metadata 和错误。

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
  - 用途：理解 vendor-neutral observability，掌握 traces、metrics、logs 的基础定位。

- [OpenTelemetry Traces](https://opentelemetry.io/docs/concepts/signals/traces/)
  - 用途：理解 trace、span、tracer、exporter，以及一次请求链路如何被拆成多个操作。

- [Docker Compose](https://docs.docker.com/compose/)
  - 用途：理解如何用一个 YAML 文件定义并运行多容器应用，后续编排 Python AI 服务、Java mock、Qdrant/Milvus。

### 本仓库阶段 6 笔记

- [阶段 6 第 1 节：Agent 评测基础：为什么 AI 应用不能只靠感觉判断好坏](../notes/stage6-01-agent-evaluation-basics.md)
  - 用途：建立 Agent 评测的第一层基础概念，理解评测集、expected output、pass/fail、bad case、回归评测、offline evaluation、online evaluation、evaluator，以及为什么当前智能工单 Agent 要先从结构化行为评测开始。

- [阶段 6 第 2 节：什么是 eval：测试和评测的区别](../notes/stage6-02-test-vs-eval.md)
  - 用途：区分传统 test 和 AI eval，理解 pytest 负责确定性代码契约，eval 负责 AI 行为质量；掌握 evaluator、metric、bad case、pytest 跑 eval、CI 分层和当前智能工单 Agent 的质量保障边界。

- [阶段 6 第 3 节：设计 Agent 测试集](../notes/stage6-03-agent-eval-dataset-design.md)
  - 用途：学习如何把智能工单 Agent 的评测目标落成第一版固定样本集，理解 inputs、expected、metadata、task_type、business_domain、case_type、priority、p0/p1、golden case、bad case 候选，以及本地 agent_cases.json 如何服务后续评测脚本。

- [阶段 6 第 4 节：意图识别评测](../notes/stage6-04-agent-intent-evaluation.md)
  - 用途：学习如何用固定 Agent 测试集评测意图分类，理解 expected intent、actual intent、intent_route、classifier、evaluator、pass/fail、accuracy、p0_accuracy、bad case，以及如何用脚本和 pytest 固定第一版意图识别回归保护。

- [阶段 6 第 5 节：工单字段提取评测](../notes/stage6-05-agent-ticket-field-evaluation.md)
  - 用途：学习如何用固定 Agent 测试集评测工单字段提取，理解 expected fields、actual fields、missing_ticket_fields、confirmation_required、ticket_need_source、case_pass_rate、field_accuracy、字段级 bad case，以及 eval 如何反向推动字段规则修正。

- [阶段 6 第 6 节：Agent 路由评测](../notes/stage6-06-agent-route-evaluation.md)
  - 用途：学习如何用固定 Agent 测试集评测节点路径，理解 node_history、expected node path、actual node path、path exact match、required nodes、forbidden nodes、terminal node、route_pass_rate、exact_match_rate，以及为什么 intent 对了仍然可能路由错误。

- [阶段 6 第 7 节：RAG + Agent 组合评测](../notes/stage6-07-rag-agent-combination-evaluation.md)
  - 用途：学习如何把 RAG 结构信号和 Agent 后续业务决策放在一起评测，理解 rag_answer_status、answered、no_context、citations、expected_sources、actual_sources、source_recall、must_cite、ticket_decision_passed_count、policy_gap，以及为什么 RAG 有答案时不创建工单、RAG 无上下文时进入 policy_gap 工单。

- [阶段 6 第 8 节：评测脚本设计](../notes/stage6-08-agent-eval-script-design.md)
  - 用途：学习如何把分散的 Agent evaluator 组织成统一命令行入口，理解评测脚本、CLI、argparse、argv、exit code、stdout、eval suite、registry、脚本入口要薄、核心编排逻辑要可测试，以及 `scripts/agent_eval.py` 如何默认运行完整 Agent eval suite 并支持 `--suite`、`--list-suites`、`--cases-path`。

- [阶段 6 第 9 节：评测报告](../notes/stage6-09-agent-eval-report.md)
  - 用途：学习如何把一次 Agent eval suite 运行结果保存成 Markdown 报告，理解评测报告、终端输出、Markdown 报告、JSON 报告、Overall、Suite Summary、Summary、Bad Cases、PASS/FAIL、报告路径、UTF-8 写入、CI artifact，并掌握 `scripts/agent_eval.py --report-path` 和 `data/agent_eval/reports/agent_eval_report.md` 的使用。

- [阶段 6 第 10 节：坏例分析](../notes/stage6-10-bad-case-analysis.md)
  - 用途：学习如何从 bad cases 进入根因分析，理解 bad case 和 bug 的区别、expected issue、dataset issue、first divergence、RAG retrieval/citation issue、Agent routing issue、ticket field extraction issue、recommended action、regression action，以及如何用 `scripts/agent_eval.py --bad-case-analysis-path` 生成真实坏例分析报告，并阅读 synthetic 坏例分析样例。

- [阶段 6 第 11 节：回归评测](../notes/stage6-11-regression-evaluation.md)
  - 用途：学习如何防止旧能力退化，理解 regression、regression evaluation、回归样本、P0 回归集、full suite regression、targeted regression、case_filter、selected_cases、空筛选保护，以及如何用 `scripts/agent_eval.py --regression --priority p0` 跑当前 10 条 P0 回归样本并生成回归评测报告。

- [阶段 6 第 12 节：evaluator 类型](../notes/stage6-12-evaluator-types.md)
  - 用途：系统理解 evaluator 类型，区分规则/代码 evaluator、人工 evaluator、LLM-as-judge、pairwise evaluator、composite evaluator、summary evaluator、reference-based、reference-free、deterministic、non-deterministic，并把这些类型映射到当前项目的 intent、field、route、RAG + Agent、eval_suite、eval_report、bad_case_analysis。

- [阶段 6 第 13 节：真实 LLM 意图识别节点](../notes/stage6-13-real-llm-intent-node.md)
  - 用途：学习如何把 `classify_intent` 从固定规则分类升级为支持真实 LLM 分类器注入，理解 JSON mode、Pydantic 输出校验、模型输出边界、`TicketIntentClassifier` Protocol、fake/real 双模式、默认规则图和真实 LLM smoke 脚本的工程边界。

- [阶段 6 第 14 节：真实 LLM 字段提取节点](../notes/stage6-14-real-llm-field-extraction-node.md)
  - 用途：学习如何把 `extract_ticket_fields` 从固定规则提取升级为支持真实 LLM 字段提取器注入，理解字段提取和意图识别的区别、工单字段 schema、JSON mode + Pydantic 二次校验、模型输出信任边界、缺字段判断仍由代码控制、fake/real 双模式和真实 LLM 字段提取 smoke 脚本。

- [阶段 6 第 15 节：Pydantic 校验模型输出](../notes/stage6-15-pydantic-validate-model-output.md)
  - 用途：学习为什么模型输出属于不可信输入，区分 JSON 解析和业务校验，理解 `ConfigDict(extra="forbid")`、`Field(pattern=...)`、`StrictBool`、`field_validator(mode="before")`、多余字段拒绝、订单号格式校验、空值归一化、统一异常转换，以及如何用 fake 测试主动覆盖模型乱输出。

- [阶段 6 第 16 节：fake LLM 和真实 LLM 双模式](../notes/stage6-16-fake-real-llm-modes.md)
  - 用途：学习为什么生产化 AI 项目要区分 `rule_based`、`fake_llm` 和 `real_llm`，理解 fake/mock/stub、运行模式配置、依赖注入、工厂函数、默认防误调用、真实模型 API key 检查、自动测试不真实调用模型，以及 fake LLM 只验证工程边界不代表真实模型效果。

- [阶段 6 第 17 节：prompt 版本管理](../notes/stage6-17-prompt-version-management.md)
  - 用途：学习为什么 prompt 是会影响模型行为和业务路径的工程资产，理解 prompt name/version、PromptSpec、prompt registry、prompt 与 model/schema/eval/log 的关系，以及如何让真实 LLM 调用日志记录 `prompt_name` 和 `prompt_version`，为后续 prompt v2/v3 对比评测打基础。

- [阶段 6 第 18 节：模型输出失败处理](../notes/stage6-18-model-output-failure-handling.md)
  - 用途：学习真实 LLM 输出失败时如何区分空输出、非法 JSON、schema 校验失败、provider 临时异常和配置错误，理解为什么不是所有错误都能兜底，以及如何用规则逻辑、fallback 日志、source 标记和测试保护 Agent 的生产化边界。

- [阶段 6 第 19 节：接入真实 `query_order` 到 LangGraph](../notes/stage6-19-query-order-langgraph.md)
  - 用途：学习如何把 LangGraph 智能工单 Agent 的 `query_order` 占位节点升级为真实只读工具节点，理解节点和工具的区别、订单号提取、`QueryOrderArgs` 参数校验、`QueryOrderResult` 结果校验、JavaOrderClient 跨服务调用、字段白名单映射、结构化 state 写回、executor 注入测试和工具异常兜底。

- [阶段 6 第 20 节：工具节点错误处理升级](../notes/stage6-20-tool-node-error-handling.md)
  - 用途：学习真实工具接入 LangGraph 后如何处理失败，理解 `code`、`kind`、`action`、`retryable` 的区别，掌握订单不存在、工具超时、上游服务不可用、工具结果校验失败和未知异常的分类策略，以及为什么工具错误要写成可测试、可统计、可观测的结构化 state。

- [阶段 6 第 21 节：工具权限和写操作安全回归](../notes/stage6-21-tool-permission-write-safety-regression.md)
  - 用途：学习只读工具和写操作工具的安全差异，理解为什么用户确认不等于后端授权、为什么写操作必须经过工具注册表、为什么 `create_ticket` 要带 `idempotency_key`，以及如何用 `ticket_write_safety_status` 和回归测试证明未确认、缺字段、授权失败时不会误调用写操作。

### 阶段 6 使用方式

1. 第 1-12 节先看 LangSmith Evaluation 相关资料，建立 Agent 评测、测试集、evaluator 和回归评测概念。
2. 第 13-18 节回到模型调用和结构化输出，重点看真实 LLM 节点、Pydantic 校验、fake/real 双模式、prompt 版本管理和模型输出失败处理。
3. 第 19-25 节先把真实工具链路生产化，再结合 LangGraph persistence，把工具错误处理、权限边界、checkpoint 持久化、thread 生命周期和会话清理补齐。
4. 第 26-30 节看 LangSmith Observability 和 OpenTelemetry，理解 trace、span、logs、metrics、成本和延迟指标。
5. 第 31-35 节补 timeout、retry、rate limit、circuit breaker、Docker Compose、health check 和 CI 自动回归。
6. 第 36 节做阶段 6 项目整理和面试表达。

## 14. RAG / 向量库

### 主资料

- [LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)
  - 用途：理解 RAG 的检索、文档索引、retriever 和把检索结果交给模型回答的整体方向。

- [OpenAI Embeddings Guide](https://developers.openai.com/api/docs/guides/embeddings)
  - 用途：理解 embedding 是什么，文本为什么可以变成向量，以及 embedding 在搜索、聚类、推荐和 RAG 里的作用。

- [Alibaba Cloud Model Studio Embedding](https://www.alibabacloud.com/help/en/model-studio/embedding)
  - 用途：理解阿里云 Model Studio embedding 模型、batch size、文本限制和 embedding 模型选择基础。

- [Alibaba Cloud Model Studio Text Embedding Synchronous API](https://www.alibabacloud.com/help/en/model-studio/text-embedding-synchronous-api)
  - 用途：理解 `text-embedding-v4` 等模型的输出维度、同步调用参数和 batch 限制。

- [Qdrant 官方文档](https://qdrant.tech/documentation/)
  - 用途：理解向量库、collection、point、filter、search。

- [Qdrant Local Quickstart](https://qdrant.tech/documentation/quickstart/)
  - 用途：后续本地跑 Qdrant 时使用。

- [Qdrant Collections](https://qdrant.tech/documentation/manage-data/collections/)
  - 用途：理解同一个 collection 里的向量必须维度一致，并根据 embedding 模型选择合适的 vector size 和 distance。

- [Qdrant Points](https://qdrant.tech/documentation/manage-data/points/)
  - 用途：理解 Qdrant 的 point 是 vector + payload 的记录，是后续文档 chunk 入库的基础。

- [Qdrant Delete Points API](https://api.qdrant.tech/api-reference/points/delete-points)
  - 用途：理解如何按 point id 或 payload filter 删除 Qdrant points，是文档删除、文档更新和重新入库的基础。

- [Qdrant Filtering](https://qdrant.tech/documentation/search/filtering/)
  - 用途：理解 payload filter，做文档类型、来源、权限过滤时会用到。

- [Qdrant Query Points API](https://api.qdrant.tech/api-reference/search/query-points)
  - 用途：理解 Qdrant 查询向量时如何同时传入 `query`、`limit`、`filter`、`score_threshold`、`with_payload` 和 `with_vector`。

- [Qdrant Search Points API](https://api.qdrant.tech/api-reference/search/points)
  - 用途：辅助理解 `score_threshold` 的官方含义：定义最低分数门槛，低相关结果不会返回；具体高于还是低于阈值取决于距离函数。

- [Milvus 官方文档](https://milvus.io/docs)
  - 用途：阶段 4 后半段理解 Milvus 的向量数据库定位、安装、collection、index 和搜索能力。

- [Milvus Docker Compose 安装](https://milvus.io/docs/install_standalone-docker-compose.md)
  - 用途：后续本地启动 Milvus Standalone 时使用。

- [Milvus Basic Vector Search](https://milvus.io/docs/single-vector-search.md)
  - 用途：理解 Milvus 基础 ANN 向量搜索流程。

- [Milvus Create Collection](https://milvus.io/docs/create-collection.md)
  - 用途：理解 Milvus collection 创建时为什么需要 schema、vector field、index params 和 metric type。

- [PyMilvus create_collection API](https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Collections/create_collection.md)
  - 用途：确认 Python 代码里 `MilvusClient.create_collection(...)` 的参数含义，尤其是 custom schema 和 index params。

- [PyMilvus upsert API](https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Vector/upsert.md)
  - 用途：理解把 chunk entity 写入或更新到 Milvus collection 时，`data` 必须匹配 schema。

- [PyMilvus search API](https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Vector/search.md)
  - 用途：理解 PyMilvus 向量检索的 `data`、`anns_field`、`filter`、`limit`、`output_fields` 和 `search_params`。

- [Milvus Scalar Index](https://milvus.io/docs/scalar_index.md)
  - 用途：理解 scalar index 如何加速 metadata filter，以及 Milvus 如何把过滤条件用于缩小向量检索候选范围。

- [Milvus Boolean Expression Rules](https://milvus.io/docs/boolean.md)
  - 用途：理解 Milvus filter 表达式里的 `and`、`or`、`not`、比较运算、`in` 和 `like` 等基础语法。

- [Milvus Inverted Index](https://milvus.io/docs/inverted.md)
  - 用途：理解 `INVERTED` 索引为什么适合分类字段、权限字段、文档类型和来源字段的 exact/in 查询。

- [Milvus STL_SORT Index](https://milvus.io/docs/stl-sort.md)
  - 用途：理解范围查询和有序字段为什么可能使用排序类 scalar index，和本节默认 `INVERTED` 的边界做对比。

- [PyMilvus create_index API](https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Management/create_index.md)
  - 用途：确认 Python 代码里如何给已有 collection 创建 scalar index，以及 `sync=True` 的等待语义。

- [PyMilvus list_indexes API](https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Management/list_indexes.md)
  - 用途：理解为什么要先列出现有索引，再只补建缺失索引，避免重复创建。

- [PyMilvus describe_index API](https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Management/describe_index.md)
  - 用途：后续排查索引字段、索引类型和索引参数时使用。

- [Milvus Index Explained](https://milvus.io/docs/index-explained.md)
  - 用途：理解向量索引的作用、成本和召回率取舍。

- [LangChain Milvus integration](https://docs.langchain.com/oss/python/integrations/vectorstores/milvus)
  - 用途：理解 LangChain 如何接入 Milvus vector store。

### 辅助理解

- [RAGFlow GitHub](https://github.com/infiniflow/ragflow)
  - 用途：观察成熟 RAG 系统的功能边界。
  - 注意：不作为初学主线，先自己实现基础 RAG。

- [RAGFlow 文档](https://ragflow.io/docs/)
  - 用途：参考 RAG 产品化能力，如数据集、解析、引用、问答流程。

## 15. LLM API 基础调用

### 主资料

- [OpenAI Developer quickstart](https://platform.openai.com/docs/quickstart)
  - 用途：理解 OpenAI API 的基本入口、API key、SDK 安装和第一次 API 调用。

- [OpenAI API Reference：Authentication](https://developers.openai.com/api/reference/overview#authentication)
  - 用途：确认 API key 是敏感凭证，应该在服务端通过环境变量或密钥管理服务读取，不要暴露在客户端代码里。

- [OpenAI Python API library](https://developers.openai.com/api/reference/python)
  - 用途：确认 Python SDK 如何读取 `OPENAI_API_KEY`，以及为什么推荐用 `.env` 避免把 key 存进源码。

- [OpenAI SDKs and CLI](https://developers.openai.com/api/docs/libraries)
  - 用途：理解 OpenAI SDK 的安装、环境变量读取和基础使用方式。

- [OpenAI Production best practices](https://platform.openai.com/docs/guides/production-best-practices)
  - 用途：理解生产环境中 API key 不应写进代码或公开仓库，应该通过环境变量或 secret management service 提供给应用。

- [OpenAI Key concepts：Tokens](https://developers.openai.com/api/docs/concepts#tokens)
  - 用途：理解 token 是模型处理文本的基本片段，以及 token、上下文长度和 tokenizer 工具的关系。

- [OpenAI Pricing](https://developers.openai.com/api/docs/pricing)
  - 用途：确认不同模型的 input、cached input、output token 当前价格。价格会变化，需要使用时再查。

- [OpenAI Reasoning models](https://developers.openai.com/api/docs/guides/reasoning)
  - 用途：理解 reasoning tokens、上下文空间、`max_output_tokens` 和成本控制之间的关系。

- [OpenAI Text generation](https://platform.openai.com/docs/guides/text)
  - 用途：理解如何用大语言模型根据 prompt 生成文本，以及为什么阶段 2 优先使用 Responses API。

- [OpenAI Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
  - 用途：理解不同消息角色的优先级、developer/user/assistant 的职责，以及为什么 prompt 要在代码里可版本化和可测试。

- [OpenAI Migrate to the Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
  - 用途：理解 Chat Completions 的 `messages` 和 Responses API 的 typed Items 之间的关系，以及多轮对话状态管理方式。

- [OpenAI Models](https://platform.openai.com/docs/models)
  - 用途：了解模型会随时间更新，模型选择要以官方文档为准，不死记某个固定名字。

- [OpenAI Responses API Reference](https://platform.openai.com/docs/api-reference/responses/create)
  - 用途：后续实现真实模型调用时查请求参数、响应结构和流式事件。

- [OpenAI Streaming API responses](https://developers.openai.com/api/docs/guides/streaming-responses)
  - 用途：理解 Chat Completions 和 Completions 通过 `stream=True` 返回流式数据，以及为什么要逐块读取响应。

- [OpenAI Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
  - 用途：理解 Structured Outputs、JSON Schema、JSON Mode 的区别，以及为什么 schema adherence 比只返回 JSON 更稳定。

- [OpenAI API Reference：Chat Completions](https://developers.openai.com/api/reference/resources/chat)
  - 用途：确认 Chat Completions 风格接口的 `model`、`messages` 和响应结构。

- [OpenAI API Reference：Chat Completions create](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create/)
  - 用途：确认 `client.chat.completions.create(...)` 的返回结构，以及 `usage` 里的 token 用量信息。

- [OpenAI Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)
  - 用途：理解多轮对话中如何管理上下文状态，以及为什么要主动保存或传递对话状态。

- [OpenAI Python API library：Timeouts](https://developers.openai.com/api/reference/python#timeouts)
  - 用途：确认 OpenAI Python SDK 的 `timeout` 配置方式、默认超时和 `APITimeoutError`。

- [OpenAI Error codes](https://developers.openai.com/api/docs/guides/error-codes)
  - 用途：理解 OpenAI Python SDK 常见异常类型，例如 `APITimeoutError`、`APIConnectionError`、`RateLimitError`。

- [OpenAI Rate limits guide](https://platform.openai.com/docs/guides/rate-limits)
  - 用途：理解模型服务的请求频率、token 用量、限流和 429 错误。

- [FastAPI：StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/)
  - 用途：理解 FastAPI 如何通过生成器或迭代器逐块返回响应内容。

- [FastAPI：Stream Data](https://fastapi.tiangolo.com/advanced/stream-data/)
  - 用途：理解 FastAPI 在流式返回时会原样发送每个 chunk，不会自动转换为 JSON。

- [MDN：Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
  - 用途：理解 SSE 事件流格式、`text/event-stream` 和浏览器如何接收服务端持续推送。

- [MDN：EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
  - 用途：理解浏览器 `EventSource` 如何打开 SSE 连接并接收服务端事件。

- [MDN：429 Too Many Requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429)
  - 用途：理解 HTTP 429 的通用语义。

- [Python logging 官方文档](https://docs.python.org/3/library/logging.html)
  - 用途：理解 logger、日志级别、`exc_info` 和日志格式化。

- [Python time.perf_counter 官方文档](https://docs.python.org/3/library/time.html#time.perf_counter)
  - 用途：理解为什么统计调用耗时要用适合测量时间间隔的计时器。

- [阿里云百炼：OpenAI Chat接口兼容](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)
  - 用途：学习如何用 OpenAI SDK 调用千问兼容接口，重点理解 API Key、BASE_URL 和模型名称三项配置。

- [阿里云百炼：流式输出](https://help.aliyun.com/zh/model-studio/stream)
  - 用途：理解百炼模型流式输出、`stream=True`、`stream_options={"include_usage": true}` 和流式计费说明。

- [阿里云百炼：结构化输出](https://help.aliyun.com/zh/model-studio/qwen-structured-output)
  - 用途：理解千问 OpenAI 兼容接口的 JSON Mode、`response_format={"type": "json_object"}` 和提示词 JSON 关键词要求。

- [阿里云百炼：文本生成模型API参考](https://help.aliyun.com/zh/model-studio/qwen-api-reference/)
  - 用途：理解百炼提供的 OpenAI 兼容 Chat Completions、OpenAI 兼容 Responses、Anthropic 兼容 Messages 和 DashScope 原生接口之间的区别。

- [Pydantic：JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)
  - 用途：理解 Pydantic 如何从 `BaseModel` 生成 JSON Schema，以及为什么下一节可以用 Pydantic 约束模型输出。

- [JSON Schema：Creating your first schema](https://json-schema.org/learn/getting-started-step-by-step)
  - 用途：理解 JSON Schema 如何描述对象、字段、类型、必填项和枚举值。

## 16. Tool Calling / 工具调用

### 主资料

- [OpenAI Function Calling Guide](https://developers.openai.com/api/docs/guides/function-calling)
  - 用途：理解模型如何根据工具定义返回工具调用，以及工具调用为什么需要开发者在后端执行。

- [OpenAI Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
  - 用途：和 Function Calling 对比，理解什么时候只是约束模型输出格式，什么时候需要连接工具、函数或外部数据。

- [OpenAI Tools Guide](https://platform.openai.com/docs/guides/tools)
  - 用途：理解 OpenAI API 中 tools 的整体定位，后续区分函数工具、内置工具和 agent 工作流。

- [OpenAI Responses API Reference](https://platform.openai.com/docs/api-reference/responses/create)
  - 用途：后续实现真实工具调用时查 `tools`、工具调用输出和响应结构。

- [OpenAI Safety Best Practices](https://developers.openai.com/api/docs/guides/safety-best-practices)
  - 用途：理解上线 AI 应用时为什么需要对抗测试、人类审核和安全边界。

- [OpenAI API Key Safety](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)
  - 用途：复习 API key 为什么不能放到客户端、仓库或模型上下文里。

- [RFC 9110：HTTP Semantics，Idempotent Methods](https://datatracker.ietf.org/doc/html/rfc9110#section-9.2.2)
  - 用途：理解“同一个请求执行一次和多次，服务端预期效果相同”这个幂等性基础定义。

- [Stripe：Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
  - 用途：学习真实 API 如何用 idempotency key 防止连接错误和重试导致重复创建或重复更新。

- [阿里云百炼：Function Calling](https://help.aliyun.com/zh/model-studio/qwen-function-calling)
  - 用途：理解千问兼容模型里的工具调用流程、工具定义和多轮调用方式。

- [阿里云百炼：结构化输出](https://help.aliyun.com/zh/model-studio/qwen-structured-output)
  - 用途：理解千问兼容模型里的 JSON 输出能力，并和 Function Calling 的外部工具调用能力区分开。

- [JSON Schema：Creating your first schema](https://json-schema.org/learn/getting-started-step-by-step)
  - 用途：理解工具参数为什么要用 schema 描述，以及 `type`、`properties`、`required` 的含义。

- [JSON Schema：Object](https://json-schema.org/understanding-json-schema/reference/object)
  - 用途：理解 `properties`、`required` 和 `additionalProperties` 如何约束对象字段。

- [JSON Schema：Enumerated values](https://json-schema.org/understanding-json-schema/reference/enum)
  - 用途：理解 `enum` 如何限制字段只能取固定值。

- [Pydantic：JSON Schema](https://pydantic.dev/docs/validation/latest/concepts/json_schema/)
  - 用途：理解 Pydantic 如何从 `BaseModel` 生成 JSON Schema，后续用于工具参数说明。

- [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
  - 用途：理解 LLM 应用里的 Prompt Injection、Insecure Output Handling、Excessive Agency 等风险分类。

- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
  - 用途：理解用户输入、外部文档或网页内容如何诱导模型偏离原始规则。

- [OWASP LLM Top 10 2025 Risks and Mitigations](https://genai.owasp.org/llm-top-10/)
  - 用途：理解生成式 AI 应用的 2025 风险框架，后续设计工具权限和人工确认时参考。

### 本仓库笔记

- [阶段 3 第 1 节：Tool Calling 是什么](../notes/tool-calling-stage3-01-what-is-tool-calling.md)
  - 用途：用智能工单 Agent 场景理解 Tool Calling 的边界、流程、安全要求和 Java 集成关系。

- [阶段 3 第 2 节：为什么 AI 不能直接操作业务系统](../notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md)
  - 用途：理解模型输出为什么是“不可信输入”，以及权限、确认、幂等、审计为什么必须由后端控制。

- [阶段 3 第 3 节：工具参数和 JSON Schema](../notes/tool-calling-stage3-03-tool-parameters-json-schema.md)
  - 用途：理解工具参数 schema 的基本写法，以及 `type`、`properties`、`required`、`enum`、`additionalProperties` 的含义。

- [阶段 3 第 4 节：结构化输出 vs Tool Calling](../notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md)
  - 用途：区分“按固定格式返回数据”和“请求调用外部工具”，理解二者在智能工单 Agent 中如何组合使用。

- [阶段 3 第 5 节：用 fake tool 模拟查订单](../notes/tool-calling-stage3-05-fake-query-order-tool.md)
  - 用途：用本地 Python 函数模拟未来 Java 订单服务，理解工具输入、工具输出、fake 数据和统一错误响应。

- [阶段 3 第 6 节：工具调用结果也要 Pydantic 校验](../notes/tool-calling-stage3-06-tool-result-pydantic-validation.md)
  - 用途：理解工具返回结果、Java API 响应和第三方接口返回都属于外部输入，进入业务逻辑前也要校验成 Pydantic 对象。

- [阶段 3 第 7 节：工具调用错误处理：超时、404、500](../notes/tool-calling-stage3-07-tool-error-handling.md)
  - 用途：理解工具调用失败时如何把底层 timeout、404、上游 500 转换成统一、安全、可测试的 API 错误。

- [阶段 3 第 8 节：工具调用权限边界](../notes/tool-calling-stage3-08-tool-permission-boundary.md)
  - 用途：理解模型只能请求工具，后端必须通过工具注册表、启用状态、用户确认和风险等级决定是否执行。

- [阶段 3 第 9 节：工具调用幂等性](../notes/tool-calling-stage3-09-tool-idempotency.md)
  - 用途：理解 `Idempotency-Key`、参数指纹、重复请求复用结果和同 key 不同参数冲突。

- [阶段 3 第 10 节：用 FastAPI 写一个最小 Java mock 业务服务](../notes/tool-calling-stage3-10-java-mock-service.md)
  - 用途：理解 mock service、业务服务边界、`/orders/{order_id}` 路径参数、统一错误响应和跨服务调用准备。

- [阶段 3 第 11 节：Python AI 服务调用 Java mock API](../notes/tool-calling-stage3-11-python-calls-java-mock-api.md)
  - 用途：理解跨服务 HTTP 调用、`JavaOrderClient`、`base_url`、timeout、上游错误映射、DTO 字段映射、Pydantic 二次校验和 `httpx.MockTransport` 测试。
- [阶段 3 第 12 节：让模型决定是否调用工具](../notes/tool-calling-stage3-12-model-decides-tool-call.md)
  - 用途：理解 `tools`、`tool_choice="auto"`、`tool_calls`、模型工具选择、后端工具白名单、工具参数 JSON 解析和 Pydantic 二次校验。

- [阶段 3 第 13 节：工具调用结果再交给模型总结](../notes/tool-calling-stage3-13-tool-result-model-summary.md)
  - 用途：理解 assistant tool-call message、`tool_call_id`、tool message、工具结果 JSON 序列化、第二轮模型总结，以及为什么工具执行失败时不能让模型假装成功。

- [阶段 3 第 14 节：用户确认机制：敏感操作不能直接执行](../notes/tool-calling-stage3-14-user-confirmation.md)
  - 用途：理解 human-in-the-loop、确认计划、操作者和参数绑定、参数指纹、确认过期、确认幂等，以及为什么确认不等于执行。

- [阶段 3 第 15 节：创建工单流程：提取字段、确认、调用 Java API](../notes/tool-calling-stage3-15-ticket-creation-workflow.md)
  - 用途：理解自然语言如何变成后端业务命令、确认计划如何被消费、Python AI 服务如何调用 Java 业务服务、写操作为什么要幂等，以及跨服务返回值为什么仍要 Pydantic 校验。

- [阶段 3 第 16 节：工具调用日志和 trace_id 串联](../notes/tool-calling-stage3-16-tool-logging-trace-id.md)
  - 用途：理解工具调用链路为什么必须可排查、`trace_id` 如何关联入口日志和跨服务调用、出站 `X-Trace-Id` 如何传递、工具执行日志应该记录什么以及哪些敏感内容不能进日志。

- [阶段 3 第 17 节：工具调用测试：fake Java API / fake tool](../notes/tool-calling-stage3-17-tool-testing-fakes.md)
  - 用途：理解 fake、mock、stub、dependency override、`httpx.MockTransport` 的区别，掌握模型 fake、工具 fake、HTTP client 测试和 FastAPI router 测试的分层方式。

- [阶段 3 第 18 节：LangChain 是什么，为什么现在才引入](../notes/tool-calling-stage3-18-what-is-langchain.md)
  - 用途：理解 LangChain 的框架定位、它封装了什么、不负责什么，以及它和当前项目手写工具调用链路、LangGraph、LangSmith 的关系。

- [阶段 3 第 19 节：LangChain ChatModel 基础](../notes/tool-calling-stage3-19-langchain-chatmodel-basics.md)
  - 用途：理解 ChatModel、`ChatOpenAI`、`SystemMessage`、`HumanMessage`、`AIMessage`、`invoke()`，以及 `/chat` 原生 SDK 调用和 `/langchain-chat` LangChain 调用的区别。

- [阶段 3 第 20 节：LangChain Tool 基础](../notes/tool-calling-stage3-20-langchain-tool-basics.md)
  - 用途：理解 LangChain Tool、`StructuredTool`、`args_schema`、工具名和描述，以及 LangChain Tool 与项目 `ToolDefinition`、权限边界和 Pydantic 校验的关系。

- [阶段 3 第 21 节：LangChain 结构化输出](../notes/tool-calling-stage3-21-langchain-structured-output.md)
  - 用途：理解 `with_structured_output()`、Pydantic schema、`json_mode`/`json_schema` 的取舍，以及 LangChain 结构化输出和原生 JSON Mode + Pydantic 的区别。

- [阶段 3 第 22 节：阶段 3 项目整理](../notes/tool-calling-stage3-22-project-summary.md)
  - 用途：复盘 Tool Calling、Java mock API、用户确认、trace_id、分层测试和 LangChain 封装，建立阶段 3 的完整项目地图，并衔接下一阶段 RAG。

- [阶段 4 第 1 节：RAG 是什么，为什么大模型需要知识库](../notes/rag-stage4-01-what-is-rag.md)
  - 用途：理解 RAG 的核心价值、普通聊天/prompt/微调/Tool Calling/RAG 的区别，以及阶段 4 的完整学习地图。

- [阶段 4 第 2 节：RAG 完整流程](../notes/rag-stage4-02-rag-pipeline.md)
  - 用途：理解文档入库流水线和用户问答流水线，明确 load、clean、split、embed、store、retrieve、generate、cite sources 每一步的职责。

- [阶段 4 第 3 节：文档、知识库、chunk、metadata 是什么](../notes/rag-stage4-03-documents-chunks-metadata.md)
  - 用途：理解 RAG 的基本数据单位，区分 document、knowledge base、chunk、content、metadata、embedding、vector 和 vector store。

- [阶段 4 第 4 节：embedding 是什么：文本怎么变成向量](../notes/rag-stage4-04-what-is-embedding.md)
  - 用途：理解 embedding、chunk embedding、query embedding、向量维度、关键词匹配和语义检索的区别，以及 embedding 在 RAG 里的边界。

- [阶段 4 第 5 节：向量相似度：为什么能用向量找相似内容](../notes/rag-stage4-05-vector-similarity.md)
  - 用途：理解 similarity、distance、cosine similarity、dot product、top_k、score_threshold，以及为什么相似度高不等于答案正确。

- [阶段 4 第 6 节：向量数据库是什么，为什么先选 Qdrant](../notes/rag-stage4-06-vector-database-qdrant.md)
  - 用途：理解向量数据库的职责边界，Qdrant 的 collection/point/vector/payload/search/filter 基础，以及为什么先用 Qdrant 后对比 Milvus。

- [阶段 4 第 7 节：Qdrant 基础：collection、point、vector、payload](../notes/rag-stage4-07-qdrant-core-concepts.md)
  - 用途：理解 Qdrant 的 collection、point、id、vector、payload 数据模型，掌握 chunk 到 point、metadata 到 payload、embedding 到 vector 的映射关系。

- [阶段 4 第 8 节：本地启动 Qdrant](../notes/rag-stage4-08-start-qdrant-locally.md)
  - 用途：理解 Qdrant 作为独立服务的启动方式，掌握 Docker 镜像、容器、端口映射、数据持久化，以及 Windows 主项目访问 VMware Ubuntu Qdrant 的链路。

- [阶段 4 第 9 节：RAG 项目结构设计](../notes/rag-stage4-09-rag-project-structure.md)
  - 用途：理解 RAG 入库流程和问答流程的模块拆分，掌握 `app/rag`、`app/services`、`app/routers`、`app/schemas` 的职责边界，以及 `RagDocument`、`RagChunk` 内部数据模型的作用。

- [阶段 4 第 10 节：准备第一批 Markdown/txt 知识文档](../notes/rag-stage4-10-first-knowledge-documents.md)
  - 用途：理解 RAG 为什么需要先准备可控知识文档，掌握 Markdown/txt 入门材料的组织方式、metadata 线索设计，以及 `data/knowledge_base` 示例知识库的后续用途。

- [阶段 4 第 11 节：文档加载和文本清洗](../notes/rag-stage4-11-document-loading-cleaning.md)
  - 用途：理解 loader 在 RAG 入库流程中的职责，掌握 Markdown/txt 文件读取、UTF-8 编码、基础文本清洗、标题提取、metadata 提取，以及为什么 loader 输出 `RagDocument`。

- [阶段 4 第 12 节：chunk 切分策略：大小、重叠、标题、段落](../notes/rag-stage4-12-chunk-splitting.md)
  - 用途：理解 chunk 在 RAG 检索中的作用，掌握 chunk_size、chunk_overlap、标题上下文、段落优先切分、稳定 chunk_id，以及 `RagDocument -> list[RagChunk]` 的实现边界。

- [阶段 4 第 13 节：生成 embedding 并写入 Qdrant](../notes/rag-stage4-13-embedding-qdrant-ingestion.md)
  - 用途：理解 chunk 如何变成向量并写入向量数据库，掌握 EmbeddedChunk、Qdrant point、vector、payload、collection 校验、upsert 和入库流程。

- [阶段 4 第 14 节：metadata 设计：source、title、section、权限字段](../notes/rag-stage4-14-metadata-design.md)
  - 用途：理解 metadata 在 RAG 中如何支撑引用来源、权限过滤、文档类型过滤、调试和重建入库，掌握必备字段、字段语义、payload 白名单和校验边界。

- [阶段 4 第 15 节：基础 top_k 检索](../notes/rag-stage4-15-basic-top-k-retrieval.md)
  - 用途：理解 retrieval、query embedding、top_k、score 和 Qdrant Query API，掌握从向量库取回最相似 chunk 的最小链路。

- [阶段 4 第 16 节：payload filter：按文档类型、权限、来源过滤](../notes/rag-stage4-16-payload-filter.md)
  - 用途：理解 payload filter、`must` 条件、`match.value` 精确匹配、filter 和 top_k 的关系，以及 metadata 如何支撑权限和业务范围过滤。

- [阶段 4 第 17 节：score_threshold：低相关内容不回答](../notes/rag-stage4-17-score-threshold.md)
  - 用途：理解 `top_k` 不等于结果一定可用，掌握 `score_threshold` 如何拦截低相关 chunk，以及阈值为什么必须结合真实 embedding、距离函数和业务数据调优。

- [阶段 4 第 18 节：把检索结果交给模型回答](../notes/rag-stage4-18-retrieved-context-to-model-answer.md)
  - 用途：理解 RAG 的 generate 阶段，掌握如何把 `RetrievedChunk` 整理成模型上下文、构造 messages、约束模型只能根据资料回答，以及无检索资料时为什么不能硬答。

- [阶段 4 第 19 节：引用来源：回答必须带出处](../notes/rag-stage4-19-citations.md)
  - 用途：理解 citation 在企业 RAG 中的可信追溯作用，掌握 `answer` 和 `citations` 的结构化拆分、后端根据 retrieved chunks 生成来源列表，以及 chunk 级出处和逐句引用校验的边界。

- [阶段 4 第 20 节：无检索结果时怎么处理](../notes/rag-stage4-20-no-context-handling.md)
  - 用途：理解无检索结果是 RAG 的业务状态而不是系统异常，掌握 `no_context` 结构化返回、无资料不调用模型、不伪造 citations、用户建议和后续知识库运营之间的关系。

- [阶段 4 第 21 节：RAG 错误处理：embedding、向量库、模型调用异常](../notes/rag-stage4-21-error-handling.md)
  - 用途：理解 RAG 链路中 embedding、向量库和模型调用异常的分类，掌握 `no_context` 与系统错误的区别，以及 RAG 层如何把底层异常映射成稳定安全的应用错误码。

- [阶段 4 第 22 节：RAG 测试：fake embedding、fake vector store](../notes/rag-stage4-22-rag-testing-fakes.md)
  - 用途：理解 RAG 自动化测试为什么要隔离真实 embedding、向量库和模型，掌握 fake/stub/mock/spy 的基础区别，以及如何用 fake embedding、fake vector store 测试检索、入库、无资料和错误映射边界。

- [阶段 4 第 23 节：文档更新、删除、重新入库](../notes/rag-stage4-23-document-update-delete-reingest.md)
  - 用途：理解 RAG 知识库为什么不能只新增入库，掌握按 `source` 删除旧 chunks、重新入库前清理旧 points、`upsert` 的作用和局限，以及 fake vector store 如何测试删除和刷新编排。

- [阶段 4 第 24 节：embedding 模型选择、维度、成本和批量处理](../notes/rag-stage4-24-embedding-model-dimension-cost-batch.md)
  - 用途：理解真实 embedding 模型和聊天模型的区别、维度和 Qdrant collection 的关系、模型选择标准、batch size、成本估算，以及如何用 OpenAI-compatible embedding adapter 接入真实模型。

- [阶段 4 第 25 节：检索质量调优：chunk size、overlap、top_k、score_threshold](../notes/rag-stage4-25-retrieval-quality-tuning.md)
  - 用途：理解 chunk 切分参数和检索参数如何影响召回质量，掌握 `chunk_size`、`chunk_overlap`、`top_k`、`score_threshold` 的边界和调优观察方法。

- [阶段 4 第 26 节：混合检索：关键词检索 + 向量检索](../notes/rag-stage4-26-hybrid-search.md)
  - 用途：理解为什么企业 RAG 不能只依赖向量检索，掌握关键词召回、向量召回、候选去重、分数归一化、加权融合和 metadata filter 在混合检索里的作用。

- [阶段 4 第 27 节：rerank 重排序是什么](../notes/rag-stage4-27-rerank.md)
  - 用途：理解 rerank 在召回之后、生成之前的位置，掌握 recall/precision、规则 reranker、cross-encoder reranker、LLM reranker、原始排名、重排排名和分数拆解。

- [阶段 4 第 28 节：RAG 安全：文档权限、Prompt Injection、敏感信息](../notes/rag-stage4-28-rag-security.md)
  - 用途：理解 RAG 安全为什么要在资料进入模型前处理，掌握权限复查、Prompt Injection 风险、敏感信息识别、脱敏 evidence、safe chunks 和安全报告。

- [阶段 4 第 29 节：RAG 性能：缓存、批处理、超时、降级](../notes/rag-stage4-29-rag-performance.md)
  - 用途：理解 RAG 工程性能不是单纯追求快，掌握检索缓存 key、TTL 缓存、embedding 批处理、near_timeout、timeout 和降级决策。

- [阶段 4 第 30 节：阶段 4 主线项目验收和复盘](../notes/rag-stage4-30-project-summary.md)
  - 用途：把第 1-29 节 RAG 主线串成完整项目地图，复盘入库流水线、问答流水线、模块职责、学习版/生产级差距、验收清单和面试口述版。

- [阶段 4 第 31 节：Milvus 是什么，和 Qdrant 有什么区别](../notes/rag-stage4-31-milvus-vs-qdrant.md)
  - 用途：理解 Milvus 和 Qdrant 都在 RAG 中承担 vector store 角色，掌握 Qdrant `collection/point/vector/payload` 与 Milvus `collection/schema/field/entity` 的概念映射，并建立向量数据库选型基础。

- [阶段 4 第 32 节：本地 Docker 启动 Milvus Standalone](../notes/rag-stage4-32-start-milvus-standalone-locally.md)
  - 用途：理解 Docker Compose、Milvus Standalone、etcd、MinIO、`19530/9091` 端口、数据目录和启动/停止/删除数据的区别；记录 VMware Ubuntu Docker 实机启动、权限问题排查和 Windows WebUI 访问验证。

- [阶段 4 第 33 节：Milvus 核心概念：collection、schema、field、entity、index](../notes/rag-stage4-33-milvus-core-concepts.md)
  - 用途：理解 Milvus collection/schema/field/entity/index 的数据模型，掌握 primary key、vector field、scalar field 和 RAG chunk schema 设计，为后续写入 Milvus 做准备。

- [阶段 4 第 34 节：用同一批文档写入 Milvus 并做向量检索](../notes/rag-stage4-34-milvus-ingestion-search.md)
  - 用途：理解同一套 RAG chunk 如何映射成 Milvus entity，掌握 PyMilvus schema/index/upsert/flush/search 的最小完整链路，并和 Qdrant 入库检索流程做对照。

- [阶段 4 第 35 节：Milvus metadata/scalar filter 和索引基础](../notes/rag-stage4-35-milvus-metadata-scalar-filter-index.md)
  - 用途：理解 metadata filter、scalar field、scalar index 的关系，掌握 Milvus boolean expression、`INVERTED` scalar index、已有 collection 补索引、filter 不应后置到 Python 的原因，以及 VMware Milvus 上的 filter/index smoke 验证。

- [阶段 4 第 36 节：Qdrant vs Milvus：什么时候选谁](../notes/rag-stage4-36-qdrant-vs-milvus-selection.md)
  - 用途：把 Qdrant 和 Milvus 放到同一个选型框架里比较，理解 point/payload 与 entity/schema 的数据模型差异，掌握部署、filter/index、规模、团队运维能力、成本和项目阶段如何影响向量数据库选择。

- [阶段 4 第 37 节：RAG 检索评测基础](../notes/rag-stage4-37-rag-retrieval-evaluation-basics.md)
  - 用途：理解为什么 RAG 不能只靠感觉判断效果，掌握评测集、query、expected source/section/chunk、Hit Rate@K、Recall@K、Precision@K、MRR 和 bad case 分析，为下一节实现最小检索评测脚本做准备。

- [阶段 4 第 38 节：给当前 RAG 项目做一个最小检索评测脚本](../notes/rag-stage4-38-rag-retrieval-evaluation-script.md)
  - 用途：把检索评测基础落到当前项目，掌握固定评测样本、match_level、no-result case、Hit Rate@K、Recall@K、Precision@K、MRR 和 bad case 报告如何写成可重复运行的本地脚本。

- [阶段 4 第 39 节：企业知识库 RAG 最终收尾复盘](../notes/rag-stage4-39-final-review.md)
  - 用途：把阶段 4 的 RAG 概念、入库链路、问答链路、Qdrant/Milvus 选型、检索质量、安全、性能、评测和生产级差距串成完整知识体系，并衔接阶段 5 LangGraph。

- [Stanford IR Book: Evaluation in information retrieval](https://nlp.stanford.edu/IR-book/pdf/08eval.pdf)
  - 用途：理解信息检索评测里的 precision、recall、ranked retrieval、Precision@K、MAP、NDCG 和用户效用等基础思想。

- [Stanford CS276 Evaluation handout](https://web.stanford.edu/class/cs276/handouts/EvaluationNew-handout-1-per.pdf)
  - 用途：辅助理解 Precision@K、MRR、MAP、NDCG 等 rank-based measures 的直观含义。

- [LangSmith: Evaluate a RAG application](https://docs.langchain.com/langsmith/evaluate-rag-tutorial)
  - 用途：理解 RAG 评测通常要创建测试数据集、运行应用、再用不同 evaluator 衡量回答相关性、正确性、groundedness 和 retrieval quality。

- [Ragas Metrics](https://docs.ragas.io/en/v0.1.21/concepts/metrics/)
  - 用途：理解 RAG pipeline 可以按组件拆开评测，包括 faithfulness、answer relevancy、context recall、context precision 等。

- [Ragas Context Precision](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/)
  - 用途：理解 context precision 如何衡量 retriever 是否把相关 chunks 排在更靠前的位置。

- [Ragas Context Recall](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/context_recall/)
  - 用途：理解 context recall 如何衡量相关资料或信息是否被成功找回。

## 阶段 4 推荐资料组合

阶段 4：企业知识库 RAG 基础 + 向量数据库入门。当前优先看：

1. 本仓库 `notes/rag-stage4-01-what-is-rag.md`
2. 本仓库 `notes/rag-stage4-02-rag-pipeline.md`
3. 本仓库 `notes/rag-stage4-03-documents-chunks-metadata.md`
4. 本仓库 `notes/rag-stage4-04-what-is-embedding.md`
5. 本仓库 `notes/rag-stage4-05-vector-similarity.md`
6. 本仓库 `notes/rag-stage4-06-vector-database-qdrant.md`
7. 本仓库 `notes/rag-stage4-07-qdrant-core-concepts.md`
8. 本仓库 `notes/rag-stage4-08-start-qdrant-locally.md`
9. 本仓库 `notes/rag-stage4-09-rag-project-structure.md`
10. 本仓库 `notes/rag-stage4-10-first-knowledge-documents.md`
11. 本仓库 `notes/rag-stage4-11-document-loading-cleaning.md`
12. 本仓库 `notes/rag-stage4-12-chunk-splitting.md`
13. 本仓库 `notes/rag-stage4-13-embedding-qdrant-ingestion.md`
14. 本仓库 `notes/rag-stage4-14-metadata-design.md`
15. 本仓库 `notes/rag-stage4-15-basic-top-k-retrieval.md`
16. 本仓库 `notes/rag-stage4-16-payload-filter.md`
17. 本仓库 `notes/rag-stage4-17-score-threshold.md`
18. 本仓库 `notes/rag-stage4-18-retrieved-context-to-model-answer.md`
19. 本仓库 `notes/rag-stage4-19-citations.md`
20. 本仓库 `notes/rag-stage4-20-no-context-handling.md`
21. 本仓库 `notes/rag-stage4-21-error-handling.md`
22. 本仓库 `notes/rag-stage4-22-rag-testing-fakes.md`
23. 本仓库 `notes/rag-stage4-23-document-update-delete-reingest.md`
24. 本仓库 `notes/rag-stage4-24-embedding-model-dimension-cost-batch.md`
25. 本仓库 `notes/rag-stage4-25-retrieval-quality-tuning.md`
26. 本仓库 `notes/rag-stage4-26-hybrid-search.md`
27. 本仓库 `notes/rag-stage4-27-rerank.md`
28. 本仓库 `notes/rag-stage4-28-rag-security.md`
29. 本仓库 `notes/rag-stage4-29-rag-performance.md`
30. 本仓库 `notes/rag-stage4-30-project-summary.md`
31. 本仓库 `notes/rag-stage4-31-milvus-vs-qdrant.md`
32. 本仓库 `notes/rag-stage4-32-start-milvus-standalone-locally.md`
33. 本仓库 `notes/rag-stage4-33-milvus-core-concepts.md`
34. 本仓库 `notes/rag-stage4-34-milvus-ingestion-search.md`
35. 本仓库 `notes/rag-stage4-35-milvus-metadata-scalar-filter-index.md`
36. 本仓库 `notes/rag-stage4-36-qdrant-vs-milvus-selection.md`
37. 本仓库 `notes/rag-stage4-37-rag-retrieval-evaluation-basics.md`
38. 本仓库 `notes/rag-stage4-38-rag-retrieval-evaluation-script.md`
39. 本仓库 `notes/rag-stage4-39-final-review.md`
40. Stanford IR Book Evaluation，理解 precision、recall、ranked retrieval 和检索评测基本思想
41. Stanford CS276 Evaluation handout，复习 Precision@K、MRR、MAP、NDCG 等排序评测指标
42. LangSmith RAG Evaluation，理解 RAG 评测数据集、evaluator 和 retrieval/generation 分层评测
43. Ragas Metrics / Context Precision / Context Recall，理解 RAG 组件级评测指标
44. LangChain Retrieval，理解 RAG 的整体流程
45. OpenAI Embeddings Guide，理解文本如何变成向量
46. Alibaba Cloud Model Studio Embedding，理解阿里云 embedding 模型和 batch 限制
47. Alibaba Cloud Text Embedding Synchronous API，理解 `text-embedding-v4` 维度参数
48. Qdrant 官方文档，理解 collection、point、vector、payload、search
49. Qdrant Local Quickstart，按官方方式用 Docker 启动 Qdrant
50. Qdrant Collections，理解同一 collection 内向量维度必须一致
51. Qdrant Points，理解 chunk 入库时为什么要同时保存 vector 和 payload
52. Qdrant Delete Points API，理解文档删除、重新入库和旧 chunk 清理
53. Qdrant Filtering，理解权限过滤和 metadata 过滤
54. Qdrant Query Points API，理解查询请求体里的 filter、score_threshold 如何和 query/top_k 一起工作
55. Qdrant Search Points API，辅助理解 score_threshold 与距离函数的关系
56. Qdrant Installation / API & SDKs / Web UI，理解本节 Qdrant 部署、接口和调试路径
57. Milvus 官方文档，后半段用于向量数据库对比
58. Milvus Docker Compose 安装，按官方方式在本地 Docker 启动 Milvus Standalone
59. Milvus Collection Explained，理解 collection、field、entity 和 load/release
60. Milvus Schema Explained，理解 vector field、scalar field、metadata filtering 和字段类型
61. Milvus Primary Field & AutoID，理解 primary key 的唯一定位作用
62. Milvus Insert Entities，理解 entity 必须满足 schema 才能写入
63. Milvus Index Explained，后半段理解索引和召回率取舍
64. Milvus Basic Vector Search，后半段理解 ANN 搜索
65. Milvus Scalar Index / Boolean Expression / Inverted Index，理解本节 metadata filter 和 scalar index 的官方语义
66. Milvus Deployment Options / Main Components，理解 Milvus Lite、Standalone、Distributed 的适用规模和组件化部署能力
67. PyMilvus create_collection / upsert / search / create_index / list_indexes API，理解本节代码直接调用的 Python SDK 参数
68. RAGFlow GitHub / 文档，只做产品化功能观察，不作为初学实现主线

## 阶段 3 复盘资料组合

阶段 3：LangChain + Java 工具调用基础。复盘时优先看：

1. 本仓库 `notes/tool-calling-stage3-01-what-is-tool-calling.md`
2. 本仓库 `notes/tool-calling-stage3-02-why-ai-cannot-operate-business-system-directly.md`
3. 本仓库 `notes/tool-calling-stage3-03-tool-parameters-json-schema.md`
4. 本仓库 `notes/tool-calling-stage3-04-structured-output-vs-tool-calling.md`
5. 本仓库 `notes/tool-calling-stage3-05-fake-query-order-tool.md`
6. 本仓库 `notes/tool-calling-stage3-06-tool-result-pydantic-validation.md`
7. 本仓库 `notes/tool-calling-stage3-07-tool-error-handling.md`
8. 本仓库 `notes/tool-calling-stage3-08-tool-permission-boundary.md`
9. 本仓库 `notes/tool-calling-stage3-09-tool-idempotency.md`
10. 本仓库 `notes/tool-calling-stage3-10-java-mock-service.md`
11. 本仓库 `notes/tool-calling-stage3-11-python-calls-java-mock-api.md`
12. 本仓库 `notes/tool-calling-stage3-12-model-decides-tool-call.md`
13. 本仓库 `notes/tool-calling-stage3-13-tool-result-model-summary.md`
14. 本仓库 `notes/tool-calling-stage3-14-user-confirmation.md`
15. 本仓库 `notes/tool-calling-stage3-15-ticket-creation-workflow.md`
16. 本仓库 `notes/tool-calling-stage3-16-tool-logging-trace-id.md`
17. 本仓库 `notes/tool-calling-stage3-17-tool-testing-fakes.md`
18. 本仓库 `notes/tool-calling-stage3-18-what-is-langchain.md`
19. 本仓库 `notes/tool-calling-stage3-19-langchain-chatmodel-basics.md`
20. 本仓库 `notes/tool-calling-stage3-20-langchain-tool-basics.md`
21. 本仓库 `notes/tool-calling-stage3-21-langchain-structured-output.md`
22. 本仓库 `notes/tool-calling-stage3-22-project-summary.md`
23. LangChain overview，理解 LangChain 的整体定位
24. LangChain Models，理解 ChatModel 的 `invoke()`、`stream()` 和 `batch()`
25. LangChain Messages，理解 `SystemMessage`、`HumanMessage`、`AIMessage`
26. LangChain ChatOpenAI integration，理解 `langchain-openai` 和 OpenAI-compatible `base_url`
27. LangChain Tools，理解工具定义、参数 schema 和模型工具调用
28. LangChain Structured output，理解 provider strategy、tool strategy 和 Pydantic schema
29. LangChain Agents，理解 model + tools + harness 的 agent loop
30. LangGraph overview，理解 LangGraph 与 LangChain 的分工
31. LangGraph Workflows and agents，理解 workflow 与 agent 的区别
32. HTTPX Quickstart，理解 Python HTTP 客户端的 GET、JSON 和响应读取
33. HTTPX Timeouts，理解跨服务调用为什么必须配置 timeout
34. HTTPX Exceptions，理解 timeout、连接失败等异常层级
35. HTTPX Transports and MockTransport，理解如何在测试里模拟 HTTP 响应
36. OpenAI Function Calling Guide，理解工具定义、工具调用和后端执行的边界
37. RFC 9110 Idempotent Methods，理解幂等性的基础定义
38. Stripe Idempotent requests，理解 idempotency key 的真实 API 实践
39. FastAPI Path Parameters，理解 `/orders/{order_id}` 这类路径参数
40. FastAPI Bigger Applications，理解 `APIRouter` 和多文件项目结构
41. FastAPI Handling Errors，理解接口错误应该统一抛出和统一响应
42. FastAPI Testing，理解如何用 `TestClient` 测试 API
43. OpenAI Structured model outputs，理解结构化输出和 Tool Calling 的边界
44. OpenAI Tools Guide，理解 tools 在模型调用里的定位
45. OpenAI Safety Best Practices，理解对抗测试和人类审核
46. OWASP Top 10 for LLM Applications，理解 Prompt Injection、Insecure Output Handling、Excessive Agency
47. OWASP LLM06:2025 Excessive Agency，理解过多工具、过大权限和过高自主性带来的风险
48. OWASP LLM01:2025 Prompt Injection，理解为什么不能只靠 prompt 做安全控制
49. OpenAI Responses API Reference，后续查真实工具调用参数和响应结构
50. 阿里云百炼：Function Calling，理解千问兼容模型里的工具调用流程
51. 阿里云百炼：结构化输出，理解千问兼容模型里的 JSON 输出能力
52. JSON Schema Creating your first schema，理解工具参数 schema 的基础
53. JSON Schema Object，理解 `properties`、`required`、`additionalProperties`
54. JSON Schema Enumerated values，理解 `enum`
55. Pydantic JSON Schema，理解 `BaseModel.model_json_schema()`
56. Pydantic Models，理解 `model_validate` 和 `ValidationError`
57. Pydantic Configuration，理解 `ConfigDict(extra="forbid")`
58. MDN HTTP response status codes，理解 404、502、504 的语义
59. 本仓库 `notes/llm-api-stage2-15-structured-output-concept.md`，复习结构化输出
60. 本仓库 `notes/llm-api-stage2-16-pydantic-structured-output.md`，复习 Pydantic 校验
61. 本仓库 `notes/fastapi-stage1-13-trace-id.md`，复习请求追踪
62. 本仓库 `notes/fastapi-stage1-14-exception-handling.md`，复习统一异常处理

阶段 2：LLM API 基础调用已完成。复盘时可看：

1. 本仓库 `notes/llm-api-stage2-01-what-is-llm-api.md`
2. 本仓库 `notes/llm-api-stage2-02-api-key-env-security.md`
3. 本仓库 `notes/llm-api-stage2-03-token-context-cost.md`
4. 本仓库 `notes/llm-api-stage2-04-openai-compatible-sdk.md`
5. 本仓库 `notes/llm-api-stage2-05-messages-roles.md`
6. 本仓库 `notes/llm-api-stage2-06-prompt-basics.md`
7. 本仓库 `notes/llm-api-stage2-07-real-chat-call.md`
8. 本仓库 `notes/llm-api-stage2-08-multi-turn-history.md`
9. 本仓库 `notes/llm-api-stage2-09-timeout.md`
10. 本仓库 `notes/llm-api-stage2-10-retry-rate-limit.md`
11. 本仓库 `notes/llm-api-stage2-11-model-error-handling.md`
12. 本仓库 `notes/llm-api-stage2-12-llm-call-logging.md`
13. 本仓库 `notes/llm-api-stage2-13-streaming-concept.md`
14. 本仓库 `notes/llm-api-stage2-14-stream-chat-endpoint.md`
15. 本仓库 `notes/llm-api-stage2-15-structured-output-concept.md`
16. 本仓库 `notes/llm-api-stage2-16-pydantic-structured-output.md`
17. 本仓库 `notes/llm-api-stage2-17-testing-model-calls.md`
18. 本仓库 `notes/llm-api-stage2-18-project-summary.md`
19. OpenAI Developer quickstart，理解 API key、SDK 和第一次 API 调用
20. OpenAI API Reference：Authentication，理解 API key 认证和密钥安全
21. OpenAI Python API library，理解 Python SDK、`.env`、timeouts、retries、错误层级和 `APIStatusError`
22. OpenAI SDKs and CLI，理解 SDK 安装和基础使用
23. OpenAI API Reference：Chat Completions，确认 `model`、`messages` 和 `choices[0].message.content`
24. OpenAI API Reference：Chat Completions create，确认 `usage.prompt_tokens`、`usage.completion_tokens`、`usage.total_tokens`、`temperature`、`top_p`、`max_completion_tokens` 和 `response_format`
25. OpenAI Streaming API responses，理解 `stream=True` 和逐块读取响应
26. OpenAI Structured model outputs，理解 Structured Outputs、JSON Mode 和 JSON Schema
27. OpenAI Conversation state，理解多轮对话状态管理
28. OpenAI Error codes，理解 SDK 错误类型和错误处理
29. OpenAI Rate limits guide，理解请求频率、token 限额和 429
30. FastAPI StreamingResponse，理解服务端如何逐块返回数据
31. FastAPI Stream Data，理解 FastAPI 不会自动把 chunk 转换成 JSON
32. FastAPI Testing Dependencies with Overrides，理解测试时替换外部依赖
33. pytest monkeypatch，理解临时替换对象、环境变量和路径
34. Python unittest.mock，理解 mock、patch 和调用断言
35. MDN Using server-sent events，理解 SSE 和 `text/event-stream`
36. MDN EventSource，理解浏览器 SSE 接收方式
37. Python logging 官方文档，理解日志级别、日志格式和 `exc_info`
38. Python time.perf_counter 官方文档，理解模型调用耗时统计
39. MDN 429 Too Many Requests，理解 HTTP 429 通用语义
40. 阿里云百炼：OpenAI Chat接口兼容，理解千问兼容接口的 `api_key`、`base_url`、`model`、`messages` 和 `usage`
41. 阿里云百炼：流式输出，理解 `stream=True`、`stream_options={"include_usage": true}` 和流式计费
42. 阿里云百炼：结构化输出，理解 JSON Mode 和 `response_format={"type": "json_object"}`
43. 阿里云百炼：文本生成模型API参考，理解兼容 Chat Completions、Responses、Anthropic Messages 和 DashScope 的区别
44. Pydantic JSON Schema，理解 `BaseModel.model_json_schema()`
45. Pydantic JSON，理解 `BaseModel.model_validate_json()`
46. JSON Schema Creating your first schema，理解对象、字段、类型和必填项
47. OpenAI Production best practices，理解生产环境 key 安全和 token 成本估算
48. OpenAI Key concepts：Tokens，理解 token 和上下文窗口
49. OpenAI Pricing，确认当前模型价格
50. OpenAI Reasoning models，理解 reasoning tokens 和 `max_output_tokens`
51. OpenAI Text generation，理解大模型文本生成和 Responses API
52. OpenAI Prompt engineering，理解消息角色、prompt 版本化和测试
53. OpenAI Migrate to the Responses API，理解 `messages` 和 typed Items 的映射
54. OpenAI Models，理解模型选择要看当前官方文档
55. OpenAI Responses API Reference，后续写真实调用时查参数和响应
56. 本仓库 `notes/fastapi-stage1-16-project-summary.md`，复习当前 FastAPI 服务基础
57. 本仓库 `notes/fastapi-stage1-11-env-config.md`，复习 `.env` 配置读取
58. 本仓库 `notes/fastapi-stage1-12-logging.md`，复习日志
59. 本仓库 `notes/fastapi-stage1-13-trace-id.md`，复习请求追踪
60. 本仓库 `notes/fastapi-stage1-14-exception-handling.md`，复习统一异常处理

阶段 1：FastAPI 服务基础已完成。复盘时可看：

1. 本仓库 `notes/fastapi-stage1-01-web-http-api.md`
2. 本仓库 `notes/fastapi-stage1-02-what-is-fastapi.md`
3. 本仓库 `notes/fastapi-stage1-03-ai-service-project-skeleton.md`
4. 本仓库 `notes/fastapi-stage1-04-health-endpoint.md`
5. 本仓库 `notes/fastapi-stage1-05-router-splitting.md`
6. 本仓库 `notes/fastapi-stage1-06-post-body-json.md`
7. 本仓库 `notes/fastapi-stage1-07-pydantic-request-model.md`
8. 本仓库 `notes/fastapi-stage1-08-pydantic-response-model.md`
9. 本仓库 `notes/fastapi-stage1-09-mock-chat-endpoint.md`
10. 本仓库 `notes/fastapi-stage1-10-testing-fastapi-apis.md`
11. 本仓库 `notes/fastapi-stage1-11-env-config.md`
12. 本仓库 `notes/fastapi-stage1-12-logging.md`
13. 本仓库 `notes/fastapi-stage1-13-trace-id.md`
14. 本仓库 `notes/fastapi-stage1-14-exception-handling.md`
15. 本仓库 `notes/fastapi-stage1-15-cors.md`
16. 本仓库 `notes/fastapi-stage1-16-project-summary.md`
17. 本仓库 `notes/fastapi-stage1-project-structure.md`
18. MDN HTTP messages，理解请求和响应
19. MDN HTTP request methods，理解 GET、POST 等方法
20. MDN POST request method，理解 POST 和请求体
21. MDN Content-Type header，理解 `application/json`
22. MDN HTTP response status codes，理解状态码
23. MDN Same-origin policy，理解同源策略和 origin
24. MDN CORS，理解跨源资源共享和预检请求
25. FastAPI First Steps，理解 `FastAPI()`、path operation 和自动文档
26. FastAPI Bigger Applications，理解 router 路由拆分
27. FastAPI Request Body，理解请求体和 Pydantic 的关系
28. FastAPI Response Model，理解响应模型和 `response_model`
29. FastAPI Testing，理解 `TestClient` 如何测试接口
30. FastAPI Settings and Environment Variables，理解环境变量和配置读取
31. FastAPI Middleware，理解请求前后统一处理逻辑
32. FastAPI Handling Errors，理解异常处理器和 `RequestValidationError`
33. FastAPI CORS Middleware，理解 `CORSMiddleware`
34. FastAPI HTTPException Reference，理解 `HTTPException`
35. Starlette Exceptions，理解 FastAPI 底层异常处理机制
36. Python Logging HOWTO，理解日志级别和 `getLogger(__name__)`
37. Python logging 文档，理解 logger、handler、formatter、LogRecord
38. Python contextvars，理解当前请求上下文
39. Python uuid，理解 `uuid4()` 生成唯一编号
40. Python Errors and Exceptions，复习 Python 异常基础
41. Uvicorn Settings - Logging，理解 `--log-level`
42. pytest fixtures reference，理解 `conftest.py` 和 fixture
43. Pydantic Models，理解 `BaseModel`
44. Pydantic Fields，理解 `Field()` 和字段约束
45. Pydantic Settings Management，理解 `BaseSettings` 和 `.env`
46. python-dotenv PyPI，理解 `.env` 文件读取依赖
47. FastAPI 官方 Tutorial，只看当前需要的路由、请求、响应、自动文档
48. uv 官方项目指南，重点复习 `uv sync`、`uv add`、`uv run`
49. HTTP/API 基础笔记 `notes/python-http-api.md`

暂时不要深入：

- FastAPI 复杂最佳实践
- LangChain
- LangGraph
- RAGFlow
- Qdrant

这些后面到对应阶段再看。阶段 1 复盘重点是：能写、能启动、能测试一个基础 API 服务，并能解释项目里每个基础模块的作用。
