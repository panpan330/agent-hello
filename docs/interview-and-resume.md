# 简历描述和面试材料

本文档用于整理当前 AI 客服工单系统学习项目的简历描述、项目讲稿和常见面试追问。

当前项目定位：

```text
AI 应用工程学习项目 / 作品原型
不是完整生产上线系统
```

推荐项目名称：

```text
企业知识库 RAG + 智能工单 Agent 系统
```

## 1. 简历项目描述

### 1.1 简历标题

```text
企业知识库 RAG + 智能工单 Agent 系统
```

### 1.2 简短项目简介

```text
基于 Java + Python 构建的 AI 客服工单系统原型，使用 Python FastAPI 承载 AI 服务，结合 RAG、Tool Calling 和 LangGraph，实现企业知识库问答、订单查询、工单字段提取、用户确认和创建工单流程；并补充 Agent 评测、结构化输出校验、状态管理、可观测性、稳定性保护、Docker Compose 和 CI 回归等工程化能力。
```

### 1.3 简历 bullet 版本

可以按下面 5-7 条写：

```text
- 基于 FastAPI 构建 Python AI 服务，提供 LLM 调用、结构化输出、Tool Calling、RAG 问答和智能工单相关接口。
- 设计企业知识库 RAG 流程，完成文档加载、清洗、chunk 切分、metadata、embedding、Qdrant/Milvus 向量检索、引用来源和无上下文拒答。
- 使用 LangGraph 编排智能工单 Agent，覆盖意图识别、RAG 回答、订单查询、字段提取、缺字段追问、用户确认和创建工单流程。
- 通过 Java mock service 模拟订单查询和工单创建业务接口，AI 服务通过受控工具调用访问业务系统，避免模型直接操作业务数据。
- 使用 Pydantic 校验模型输出、工具参数和工具结果，写操作加入用户确认、权限判断和幂等键，强化 Tool Calling 安全边界。
- 设计 Agent eval 体系，覆盖意图识别、字段提取、路由决策、RAG + Agent 组合评测、坏例分析和回归评测。
- 补充日志、trace/span/log/metrics、token/成本/延迟指标、timeout/retry/限流/熔断/降级、Docker Compose、health/readiness 和 GitHub Actions CI。
```

### 1.4 更短版本

如果简历篇幅有限，可以写：

```text
- 基于 FastAPI + LangGraph 构建 AI 客服工单系统原型，结合 RAG、Tool Calling 和 Java mock service，实现知识库问答、订单查询、字段提取、用户确认和创建工单流程。
- 设计 Agent eval、Pydantic 输出校验、工具权限边界、checkpoint/thread_id、日志追踪、稳定性策略、Docker Compose 和 CI 回归，提升 AI 应用可验证性和工程化能力。
```

### 1.5 不建议写法

不要写：

```text
完整生产级 AI 客服系统
已企业上线
支持高并发生产客服业务
复杂 Multi-Agent 系统
```

更准确的表达：

```text
AI 应用工程学习项目
作品原型
可上线雏形设计
后续计划补真实 Spring Boot + MySQL/Redis、前端和部署
```

### 1.6 项目表达原则

讲这个项目时，建议遵守下面 5 条原则：

```text
1. 先讲业务问题，再讲技术方案。
2. 先讲主链路，再讲细节。
3. 技术名词必须能对应到项目里的真实模块。
4. 不夸大成完整生产系统。
5. 主动说明边界和后续真实化路线。
```

可以用这个对应关系检查自己的表达：

```text
简历一句话
-> 项目一个模块
-> 面试一段解释
-> 代码或文档一个证据
```

举例：

```text
写 RAG，就要能讲文档加载、chunk、metadata、embedding、检索、引用来源和拒答。
写 LangGraph，就要能讲 State、node、edge、checkpoint/thread_id 和用户确认。
写 Tool Calling 安全，就要能讲工具注册、参数校验、读写区分、权限、确认和幂等。
写 eval，就要能讲 dataset、evaluator、bad case 和 regression。
写生产化，就要能讲日志、trace、metrics、timeout、retry、限流、熔断、降级、health/readiness 和 CI。
```

## 2. 1 分钟项目讲稿

```text
这个项目是一个 Java + Python 的 AI 客服工单系统学习项目，核心是企业知识库 RAG + LangGraph 智能工单 Agent。

Python FastAPI 负责 AI 服务，Java mock service 模拟订单查询和工单创建等业务后端。用户可以问企业政策，系统通过 RAG 检索知识库并带出处回答；用户也可以查订单或创建工单，Agent 会识别意图、调用受控工具、提取字段、追问缺失信息，并在用户确认后创建工单。

项目里我重点补了 AI 工程化能力，包括 Pydantic 结构化校验、工具权限边界、用户确认、Agent eval、bad case、regression、checkpoint/thread_id、日志追踪、成本和延迟指标、timeout/retry/限流/熔断/降级、Docker Compose 和 CI。

它当前是学习项目和作品原型，不是完整生产系统。下一步会把 Java mock service 升级为真实 Spring Boot + MySQL/Redis 业务服务。
```

## 3. 3 分钟项目讲稿

```text
这个项目面向客服场景，目标是让 AI 既能基于企业知识库回答政策问题，也能在用户需要人工处理时收集信息并创建工单。

整体架构分成 Python AI 服务和 Java mock 业务服务。Python 侧用 FastAPI 提供接口，用 RAG 做知识库问答，用 LangGraph 编排智能工单 Agent；Java mock service 模拟订单查询和工单创建接口。向量库部分学习了 Qdrant 和 Milvus，分别用于理解轻量向量库和更复杂向量数据库的设计差异。

RAG 部分的流程是：先把 Markdown/txt 文档加载、清洗、切成 chunk，设计 metadata，生成 embedding 后写入向量库；用户提问时先检索相关 chunk，再把上下文交给模型回答，并要求带引用来源。如果没有可靠上下文，就拒答或转人工，避免模型编造。

Agent 部分用 LangGraph 组织流程。用户输入后先做意图识别，根据意图走知识库回答、订单查询、创建工单或安全兜底。创建工单时不会直接写业务系统，而是先提取字段、判断缺失字段、请求用户确认，确认后才通过受控工具调用 Java 服务创建工单。

工程化方面，我补了 Agent eval 和 regression，覆盖意图识别、字段提取、路由决策、RAG 组合评测和坏例分析；也补了 Pydantic 输出校验、工具权限和写操作安全、checkpoint/thread_id、日志追踪、成本和延迟指标、timeout/retry/限流/熔断/降级、Docker Compose、health/readiness 和 GitHub Actions CI。

当前项目不是完整生产上线系统，还缺真实 Spring Boot 业务服务、真实数据库、认证授权、前端工作台、部署和生产监控。下一阶段我会优先补真实 Java Spring Boot + MySQL/Redis，把 mock 业务服务升级得更接近真实后端。
```

## 4. 5 分钟项目讲稿

```text
这个项目是一个 Java + Python 的 AI 客服工单系统学习项目，定位是 AI 应用工程作品原型。它不是单纯聊天 Demo，而是围绕客服业务，把 RAG、Tool Calling、LangGraph Agent 和后端工程化能力组合起来。

业务上模拟三个典型场景：第一，用户问企业政策，比如退款、物流、账户安全规则，系统需要基于知识库回答；第二，用户问订单状态，AI 不能自己编，需要通过工具调用后端订单服务；第三，用户需要投诉或人工处理，系统要收集信息并创建工单，但写操作必须经过用户确认。

架构上分成 Python AI 服务和 Java mock 业务服务。Python FastAPI 提供 HTTP 接口，内部包含 LLM 服务、RAG 模块、Tool Calling、LangGraph Agent、评测和工程保障。Java mock service 模拟业务后端，提供订单查询和工单创建接口。Qdrant 和 Milvus 用于学习向量数据库，Docker Compose 用于本地多服务编排，GitHub Actions 用于自动回归。

RAG 部分我从基础链路开始做：文档加载、清洗、chunk 切分、metadata、embedding、写入向量库、top_k 检索、payload filter、score_threshold、引用来源、无上下文拒答、混合检索、rerank、安全和性能。后面还补了 RAG 检索评测，避免只靠主观感觉判断检索效果。

Agent 部分用 LangGraph 实现状态机式流程。流程包括意图识别、RAG 回答、订单查询、工单字段提取、缺字段追问、用户确认和创建工单。LangGraph 的价值是把多步骤、有状态、有分支、有人工确认的流程拆成节点和边，便于测试、恢复和排查。

Tool Calling 安全是项目重点。模型或规则可以提出工具意图，但执行权在后端。后端会检查工具名是否注册、参数是否符合 schema、工具是读操作还是写操作、写操作是否有用户确认、是否需要幂等键，最后还要校验工具返回结果。这样避免模型直接操作业务系统。

评测方面，我设计了 Agent eval dataset 和多类 evaluator，包括意图识别评测、字段提取评测、路由评测、RAG + Agent 组合评测、eval report、bad case analysis 和 regression。确定性边界用 pytest，AI 效果用 eval，这样代码修改或 prompt 修改后可以看有没有退化。

生产化方面，项目补了 Pydantic 模型输出校验、prompt 版本管理、模型输出失败分类、checkpoint/thread_id、会话生命周期、LangSmith 和 OpenTelemetry 基础、trace/span/log/metrics、生产日志字段、token/成本/延迟指标、timeout、retry、rate limit、circuit breaker、degradation、health/readiness 和 CI。

当前边界也很明确：它还不是完整生产系统，Java 服务还是 mock，没有真实数据库、认证授权、前端、线上部署和生产监控。M6 之后我会进入真实化阶段，优先把 Java mock service 升级为真实 Spring Boot + MySQL/Redis 业务服务，再继续补前端和部署。
```

## 5. 常见面试追问与答案

### 5.1 你这个项目到底是什么？

答：

```text
这是一个 Java + Python 的 AI 客服工单系统学习项目，核心是企业知识库 RAG + LangGraph 智能工单 Agent。它模拟客服场景，支持知识库问答、订单查询和用户确认后的工单创建，同时补了评测、工具安全、状态管理和生产化设计。
```

### 5.2 它是完整生产系统吗？

答：

```text
不是完整生产系统。它当前是 AI 应用工程学习项目和作品原型。它已经完成 RAG、Tool Calling、LangGraph Agent、评测和生产化设计，但还缺真实 Spring Boot 业务服务、真实数据库、认证授权、前端、部署和生产监控。
```

### 5.3 为什么用 RAG？

答：

```text
客服场景里很多回答依赖企业内部政策，模型本身不知道这些私有、可变的业务知识。RAG 可以先从知识库检索相关文档 chunk，再把检索结果交给模型回答，并带引用来源。这样比直接让模型回答更可控，也能在没有可靠上下文时拒答。
```

### 5.4 RAG 为什么会答错？

答：

```text
RAG 可能在检索阶段或生成阶段出错。检索阶段可能 chunk 切分不好、embedding 不合适、top_k/threshold 不合理、metadata filter 过严或过松；生成阶段可能模型没有严格依据上下文，或者引用来源处理不清楚。所以项目里补了 score_threshold、引用来源、无上下文拒答、混合检索、rerank 和检索评测。
```

### 5.5 Qdrant 和 Milvus 怎么选？

答：

```text
Qdrant 更轻量，本地启动和学习成本低，适合中小规模 RAG 和快速迭代。Milvus 更偏大规模向量检索和复杂索引场景，组件更多，运维复杂度也更高。当前项目先用 Qdrant 跑通主线，再补 Milvus 对比，目的是理解不同向量数据库的选型边界。
```

### 5.6 为什么用 LangGraph？

答：

```text
因为当前工单流程不是单轮问答，而是多步骤、有状态、有分支、有用户确认的业务流程。LangGraph 可以把流程拆成节点和边，用 State 保存中间状态，用 checkpoint/thread_id 支持恢复。当前项目用它组织意图识别、RAG 回答、订单查询、字段提取、用户确认和创建工单。
```

### 5.7 LangGraph 和普通函数有什么区别？

答：

```text
普通函数也能写简单流程，但节点多、分支多、状态多、需要中断恢复时会越来越难维护。LangGraph 更适合把 Agent 流程建模成图，节点负责单步逻辑，边负责跳转，State 保存流程状态，checkpoint 支持恢复。
```

### 5.8 AI 为什么不能直接操作数据库？

答：

```text
模型输出不稳定，可能理解错、编造参数或越权操作。真实业务系统的读写必须由后端控制。AI 可以提出意图，但后端要做工具注册、参数校验、权限判断、用户确认、幂等控制和结果校验。尤其是创建工单这种写操作，必须用户确认后才能执行。
```

### 5.9 Tool Calling 怎么保证安全？

答：

```text
当前项目把工具执行权放在后端。模型或规则提出工具意图后，后端先校验工具名是否注册，再用 Pydantic/JSON Schema 校验参数，判断工具是否需要确认。只读工具可以在授权后执行；写操作必须用户确认并带幂等键。工具返回结果也要做字段白名单映射和 Pydantic 校验。
```

### 5.10 怎么评测 Agent？

答：

```text
我把 Agent 评测拆成多层，而不是只看最终回答。意图识别评测判断用户问题应该走哪个业务分支；字段提取评测判断工单字段是否提取正确；路由评测判断 LangGraph 节点路径是否符合预期；RAG + Agent 组合评测判断知识库回答、引用来源、无上下文拒答和工单决策。失败样本会进入 bad case analysis，关键样本进入 regression。
```

### 5.11 测试和 eval 有什么区别？

答：

```text
测试更适合验证确定性代码边界，比如参数校验、异常处理、权限判断、接口状态码。eval 更适合验证 AI 效果，比如意图识别是否正确、字段是否抽取对、路由是否合理、回答是否引用正确来源。当前项目两者都做，pytest 保证代码边界，eval 保证 AI 表现。
```

### 5.12 为什么测试不用真实模型？

答：

```text
真实模型有成本、网络、API Key 和输出不稳定问题，不适合作为所有自动化测试的基础依赖。当前项目用 rule_based 和 fake_llm 做稳定测试，用 real_llm 做受控 smoke 或人工验证。这样 CI 稳定，真实模型能力也能单独验证。
```

### 5.13 Pydantic 在项目里解决什么问题？

答：

```text
Pydantic 是模型输出和业务系统之间的结构化边界。模型返回 JSON 不代表一定可靠，可能多字段、少字段、类型错、枚举值错。Pydantic 用来校验请求、响应、模型结构化输出、工具参数和工具结果，防止不合法数据进入业务流程。
```

### 5.14 如果 Java 服务超时怎么办？

答：

```text
工具调用会捕获并分类错误，比如超时、404、5xx 和结果校验失败。超时和 5xx 属于可重试或可降级场景，404 订单不存在通常不可重试。阶段 6 还补了 timeout、retry、rate limit、circuit breaker 和 degradation 策略，避免上游异常拖垮整个系统。
```

### 5.15 你怎么排查一次 AI 回答失败？

答：

```text
先用 trace_id 定位这次请求，再看它经过哪些节点和 span，比如意图识别、RAG 检索、工具调用、字段提取、创建工单。单个节点问题看结构化日志里的 event_name、error_code、node、fallback_used 等字段；整体趋势问题看 metrics，比如延迟、错误率、token 和成本。
```

### 5.16 当前项目最大的不足是什么？

答：

```text
最大不足是业务后端还不够真实。Java 服务现在还是 mock，没有真实 Spring Boot 项目结构、数据库表、事务、认证授权和复杂业务规则。另外还没有前端工作台、线上部署和生产监控。下一阶段我会优先补真实 Java Spring Boot + MySQL/Redis。
```

### 5.17 后续怎么真实化？

答：

```text
第一步把 Java mock service 升级成真实 Spring Boot + MySQL/Redis 业务服务，补订单表、工单表、用户表、认证授权、事务和接口鉴权。第二步做前端客服工作台。第三步做 Dockerfile、部署、Nginx、HTTPS、日志采集和监控告警。第四步继续补真实 embedding、多模型路由、MCP 和更大规模评测。
```

### 5.18 面试追问准备清单

复习常见追问时，不要只背答案，要先看它背后的考点。

```text
RAG 类问题
-> 考是否理解私有知识、检索召回、chunk、embedding、引用、拒答和评测。

LangGraph 类问题
-> 考是否理解多步骤流程、状态管理、分支跳转、中断恢复和用户确认。

Tool Calling 类问题
-> 考是否理解模型不可靠、后端执行权、参数校验、读写隔离、权限、确认和幂等。

eval 类问题
-> 考是否理解 AI 效果不能只靠手工试，应该有数据集、评测器、坏例和回归。

生产化类问题
-> 考是否理解真实系统还需要数据库、事务、认证、部署、监控、稳定性和成本控制。

项目不足类问题
-> 考是否诚实，是否知道当前做到哪里，是否有清楚的后续路线。
```

如果遇到不会的问题，可以按这个结构答：

```text
先承认边界。
再说当前项目做到哪一步。
再说自己对这个问题的理解。
最后说后续会怎么验证和补齐。
```

## 6. 项目不足和后续路线

当前不足：

```text
Java 服务仍是 mock。
没有真实 MySQL/PostgreSQL。
没有 Redis。
没有完整认证授权。
没有前端客服工作台。
没有真实线上部署。
没有生产监控告警。
eval dataset 规模还小。
真实 embedding 和多模型路由还没系统补。
MCP、Multi-Agent、Kubernetes 等高级方向还没学。
```

后续路线：

```text
阶段 7：真实 Java Spring Boot + MySQL/Redis 业务服务
阶段 8：前端客服工作台
阶段 9：部署上线和运维
阶段 10：AI 能力深化，补真实 embedding、MCP、多模型路由、大规模评测
```

## 7. 面试前快速复习顺序

建议按这个顺序复习：

```text
1. README 第一屏
2. docs/project-diagrams.md
3. docs/local-run-and-demo.md
4. docs/interview-and-resume.md
5. notes/stage6-36-project-summary-interview-expression.md
```

如果时间只有 20 分钟：

```text
看 1 分钟讲稿
看整体架构图
看 Tool Calling 安全问答
看项目不足和后续路线
```
