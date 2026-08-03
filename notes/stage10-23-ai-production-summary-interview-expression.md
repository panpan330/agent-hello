# 阶段 10 第 23 节：阶段 10 总复盘和面试表达强化

## 本节定位

这一节是阶段 10 的最后一节。

阶段 10 的主题是 AI 应用生产化与可运营能力。前面很多节都在补一个核心问题：

```text
一个 AI 应用不只是能跑通，还要能上线、能观测、能控成本、能防风险、能评估质量、能灰度、能回滚、能处理故障。
```

本节不继续堆新功能，而是把阶段 10 学过的内容整理成你真正能讲清楚的知识体系。

学完本节后，你应该可以比较自然地回答：

- 你的 AI 项目有哪些生产化能力？
- 你怎么做 tracing？
- 你怎么保护 LLM 日志安全？
- 你怎么控制 token 成本？
- 你怎么处理限流、重试、超时和 fallback？
- 你怎么防 Prompt Injection？
- 你怎么评估模型和 RAG 的质量？
- 你怎么收集 bad case 并做回归？
- 你怎么做生产监控、告警、灰度、回滚、SLO 和 Runbook？
- 这个项目写在简历上到底应该怎么写？

## 本节学习目标

本节目标不是背诵阶段 10 的所有代码，而是建立表达能力。

你要能做到：

- 按“可观测性、稳定性、成本、安全、质量、发布运营”六层讲清楚阶段 10。
- 能把阶段 10 的每个技术点和真实线上问题对应起来。
- 能区分日志、trace、metric、alert、SLO、Runbook 的边界。
- 能解释为什么 AI 应用比传统后端多了 LLM、RAG、Tool、Prompt Injection、token 成本、评估困难这些生产风险。
- 能把项目能力写成简历 bullet。
- 能回答面试官对 AI 应用生产化的常见追问。
- 能明确阶段 10 之后还应该补哪些真实项目能力。

## 本节新增和修改

新增：

- `notes/stage10-23-ai-production-summary-interview-expression.md`

更新：

- `docs/learning-progress.md`

本节是纯知识整理，不新增代码，不新增测试，也不需要打开 VMware、Docker、MySQL、Redis、Qdrant 或 Milvus。

## 一句话先讲透

阶段 10 让这个项目从“能调用大模型的 AI 应用”升级成“具备真实上线意识的 AI 应用”：能追踪、能保护、能控成本、能限流、能降级、能评估、能告警、能灰度、能回滚、能按 Runbook 处理故障。

## 基础知识铺垫

### 1. 什么叫生产化能力

很多人做 AI 项目时，会停在这一步：

```text
前端输入问题
-> 后端调用大模型
-> 返回回答
```

这能证明你会调 API，但不代表这个系统可以真实上线。

真实上线后，系统会遇到很多问题：

- 用户输入很长，成本暴涨。
- 模型 provider 超时或失败。
- RAG 检索不到资料。
- RAG 找到了资料，但引用来源对不上。
- 工具调用失败，订单查不到或工单创建失败。
- 用户输入 prompt injection，试图绕过系统指令。
- 日志里不小心打印了用户隐私、API Key 或完整 prompt。
- 流式输出开始后中断，普通 JSON 错误已经无法返回。
- 新模型灰度后，少部分用户回答质量变差。
- 线上告警响了，但没有人知道先查什么。

生产化能力就是为这些问题提前做工程设计。

它不是一个单独功能，而是一组系统能力。

### 2. 生产化和业务功能的区别

业务功能解决的是：

```text
系统能做什么？
```

例如：

- 聊天。
- RAG 问答。
- 查订单。
- 创建工单。
- 工单确认。
- 多轮对话。

生产化能力解决的是：

```text
系统在真实环境里能不能稳定、安全、可控、可持续地做这些事？
```

例如：

- 出错能不能定位。
- 成本能不能控制。
- 流量高了能不能限流。
- 模型挂了能不能 fallback。
- 风险输入能不能拦截。
- 新版本能不能灰度。
- 坏 case 能不能进入回归。
- 故障能不能按 Runbook 恢复。

所以一个项目如果只有业务功能，会像 demo。

一个项目如果既有业务功能，又有生产化能力，才更像真实工程项目。

### 3. AI 应用为什么比传统后端更需要生产化

传统 Java 后端也需要日志、监控、限流、重试、超时、灰度、回滚。

但是 AI 应用多了几类特殊问题。

第一，模型输出不完全确定。

同一个问题，模型可能因为上下文、参数、版本变化而给出不同回答。

第二，外部模型 provider 是强依赖。

只要 provider 慢、限流、超时、鉴权失败，你的应用就会受影响。

第三，token 成本和输入输出长度强相关。

用户输入越长、上下文越多、工具结果越多、fallback 越多，成本越高。

第四，RAG 质量不只看接口成功。

接口返回 200 不代表回答正确。还要看检索是否召回、引用是否可靠、上下文是否被污染。

第五，Tool Calling 有真实业务风险。

模型不能直接决定写数据库。模型只能提出意图，后端必须校验、鉴权、幂等、审计。

第六，Prompt Injection 会攻击系统边界。

用户可能输入“忽略之前规则”“泄露系统提示词”“绕过权限查别人订单”等内容。

这些都是 AI 应用相对传统 CRUD 后端新增的生产风险。

### 4. 为什么阶段 10 很适合写进简历

很多初级 AI 项目只写：

```text
使用 FastAPI 调用大模型，实现智能客服问答。
```

这句话太薄。

阶段 10 学完后，你可以写：

```text
围绕 AI 客服与智能工单系统补齐生产化能力，包括 trace_id 链路追踪、LLM 调用日志脱敏、token 成本估算、多模型路由、fallback、限流、重试、超时治理、Prompt Injection 防护、自动化评估、Bad Case 回归、生产监控指标、灰度回滚和 SLO/Runbook。
```

这会明显更像真实项目。

注意，简历不是把所有技术名堆上去，而是要表达你解决了什么工程问题。

好的表达是：

```text
为了解决线上 AI 应用不可观测、成本不可控、模型失败不可恢复、回答质量难评估的问题，我设计并实现了对应的生产化治理能力。
```

这比单纯写“会 LangChain、会 RAG、会 Tool Calling”更强。

### 5. 阶段 10 和前面阶段的关系

阶段 10 不是孤立的。

它建立在前面这些能力上：

- Python AI 服务基础。
- LLM API 调用。
- Structured Output。
- Tool Calling。
- RAG。
- LangGraph Agent。
- Java Spring Boot 真实业务服务。
- MySQL / Redis。
- MCP。
- RAG 进阶和检索质量优化。

阶段 10 做的是把这些能力放到“线上系统”语境里重新审视。

比如：

- LLM API 调用，在阶段 10 里变成日志安全、成本、超时、重试、fallback。
- RAG，在阶段 10 里变成质量评估、bad case、指标、告警、生产验收。
- Tool Calling，在阶段 10 里变成权限、幂等、字段白名单、Java 错误码映射、可观测性。
- LangGraph，在阶段 10 里变成 trace、状态持久化、异常兜底、人工确认和流程恢复。

这就是技术从“会用”走向“会工程化”的过程。

## 本节主题系统讲解

### 1. 阶段 10 的六层能力地图

阶段 10 可以整理成六层能力：

```text
第一层：可观测性
第二层：日志与安全
第三层：成本与性能治理
第四层：稳定性保护
第五层：安全边界与质量评估
第六层：发布运营与故障响应
```

这六层不是按代码目录划分，而是按真实线上问题划分。

### 2. 第一层：可观测性

对应课程：

- 第 2 节：Tracing 是什么。
- 第 3 节：trace_id / span / event / metric 的区别。
- 第 4 节：Python AI 服务 tracing。
- 第 5 节：Java 业务服务 tracing 对齐。

这一层解决的问题是：

```text
一次 AI 请求慢了、错了、回答质量差了，我能不能知道它到底卡在哪一步？
```

核心概念：

- `trace_id`：一次请求的全局追踪 ID。
- `span`：请求中的一个阶段，比如 LLM call、RAG retrieval、tool execution。
- `event`：阶段里的关键事件，比如 started、finished、failed。
- `metric`：聚合指标，比如失败率、延迟分布、成本。

你要能讲清楚：

```text
日志适合看单次发生了什么，trace 适合看一次请求经过了哪些阶段，metric 适合看整体趋势和告警。
```

当前项目里的价值：

- Python AI 服务能描述 chat、stream、RAG、tool、Java 调用的 tracing plan。
- Java business service 能接收并传递 trace_id。
- Python 和 Java 的日志可以靠同一个 trace_id 串起来。

面试表达：

```text
我在项目里没有只停留在普通日志，而是把 AI 请求拆成 HTTP、LLM、RAG、Tool、Java client 等 span，并通过 trace_id 串联 Python AI 服务和 Java 业务服务，方便排查一次请求到底慢在模型、检索、工具还是业务后端。
```

### 3. 第二层：日志与安全

对应课程：

- 第 6 节：LLM 调用日志安全。
- 第 7 节：配置与密钥管理。

这一层解决的问题是：

```text
系统出问题需要日志，但日志不能泄露用户隐私、prompt、模型原始回答、工具结果、API Key。
```

AI 应用的日志风险比普通后端更高。

原因是 LLM 请求里通常包含：

- 用户原始输入。
- 多轮历史。
- 系统提示词。
- RAG 上下文。
- 工具调用参数。
- 工具返回结果。
- 模型完整输出。

这些内容如果直接进日志，就可能泄露隐私和内部策略。

阶段 10 的核心原则是：

```text
日志记录元信息，不记录敏感正文。
```

可以记录：

- provider。
- model。
- operation。
- outcome。
- elapsed_ms。
- token usage。
- error_code。
- trace_id。

不应该记录：

- API Key。
- Authorization。
- 完整 prompt。
- 用户原文。
- 系统提示词。
- RAG 原文 chunk。
- 完整工具结果。
- 隐私字段。

面试表达：

```text
我把 LLM 调用日志分成安全元信息和敏感正文两类，只记录 provider、model、operation、耗时、token、错误码和 trace_id，不把 prompt、用户输入、系统提示词、工具结果和 API Key 写入日志。
```

### 4. 第三层：成本与性能治理

对应课程：

- 第 8 节：Token 成本统计。
- 第 9 节：请求耗时拆解。
- 第 10 节：多模型路由基础。
- 第 12 节：成本控制。

这一层解决的问题是：

```text
AI 请求为什么贵、为什么慢、什么请求应该用什么模型，系统能不能提前控制成本？
```

AI 应用的成本通常来自：

- 输入 token。
- 输出 token。
- 多轮历史。
- RAG 上下文。
- rerank。
- tool result 再总结。
- retry。
- fallback。
- 使用更强更贵的模型。

阶段 10 里建立了几个意识：

- token usage 要归一化。
- 模型价格要可配置。
- 单次请求要能预估成本。
- 不同任务可以走 fast、balanced、strong 模型。
- 高成本请求要限制输出长度。
- 超预算时可以阻断或降级。

性能上也不能只看总耗时。

要拆成：

```text
HTTP 入口耗时
LLM 调用耗时
RAG 检索耗时
rerank 耗时
tool validation 耗时
tool execution 耗时
Java client 耗时
序列化和输出耗时
```

面试表达：

```text
我在项目里把 AI 请求成本和耗时拆开治理：通过 token usage 归一化和模型价格配置估算成本，通过 fast/balanced/strong 分层做多模型路由，并在请求执行前做预算预检，避免长上下文、fallback 和重试导致成本不可控。
```

### 5. 第四层：稳定性保护

对应课程：

- 第 11 节：模型 fallback。
- 第 13 节：限流。
- 第 14 节：重试。
- 第 15 节：超时治理。
- 第 16 节：SSE 流式输出生产化与中断处理。

这一层解决的问题是：

```text
模型失败、上游慢、流量高、流式中断时，系统如何保护自己和用户体验？
```

关键边界：

#### fallback

fallback 是主模型失败后切换备用路径。

它不是重试。

它解决的是：

```text
主路径不可用时，有没有备用路径继续给用户一个可接受结果。
```

#### retry

retry 是同一路径临时失败后再试一次。

它适合：

- 网络抖动。
- 临时超时。
- 429 之后按 Retry-After 等待。
- 5xx 临时错误。

不适合：

- 参数错误。
- 鉴权错误。
- 权限错误。
- 写操作没有幂等保护。

#### timeout

timeout 是防止请求无限等待。

AI 请求尤其需要总超时预算。

不能每一步都单独给很长时间，否则：

```text
LLM retry + fallback + RAG + tool + Java
```

叠加后用户可能等很久。

#### rate limiting

限流是保护系统、成本和依赖。

它和权限不同：

- 权限决定能不能访问。
- 限流决定访问频率是否过高。

#### SSE

SSE 流式输出开始后，HTTP 状态码已经发出，不能再像普通接口一样返回标准 JSON 错误。

所以流式接口要通过事件表达：

- start。
- message。
- heartbeat。
- error。
- done。

面试表达：

```text
我把 AI 服务的稳定性保护拆成 fallback、retry、timeout、rate limit 和 SSE 中断处理。retry 只处理临时错误，fallback 处理主模型不可用，timeout 控制总耗时预算，rate limit 防止成本和依赖被打爆，SSE 则通过事件流表达开始、心跳、错误和完成。
```

### 6. 第五层：安全边界与质量评估

对应课程：

- 第 17 节：Prompt Injection、权限控制与隐私保护。
- 第 18 节：自动化评估平台基础与评测集版本管理。
- 第 19 节：Bad Case 收集、分析与回归测试。

这一层解决两个问题：

```text
第一，AI 不能越权、泄露、被提示词攻击。
第二，AI 质量不能只靠人工感觉，要能评估和回归。
```

安全边界：

- 用户输入不能改变系统规则。
- 外部文档不能指挥模型泄露系统提示词。
- 模型不能绕过后端权限。
- 工具调用必须由后端校验参数、权限、幂等和字段白名单。
- 日志和输出都要做隐私保护。

质量评估：

- 测试验证代码确定性行为。
- 评估验证 AI 输出质量。
- eval dataset 要有版本。
- eval run 要能记录 baseline 和 candidate。
- bad case 要能从失败中沉淀。
- 修复后要进入 regression case。

面试表达：

```text
我没有把模型当成可信执行者，而是把模型放在受控边界内。Prompt Injection、高风险输入、工具权限和敏感字段都由后端控制。同时我用评测集版本、baseline/candidate 对比、bad case 收集和 regression case，把 AI 输出质量纳入可持续评估。
```

### 7. 第六层：发布运营与故障响应

对应课程：

- 第 20 节：生产监控指标与告警基础。
- 第 21 节：灰度发布、回滚与配置开关。
- 第 22 节：SLO / SLA / Runbook。

这一层解决的问题是：

```text
上线后如何知道系统是否健康，新版本如何小流量验证，出问题如何止损和恢复？
```

生产监控：

- HTTP 指标。
- LLM 指标。
- RAG 指标。
- Tool 指标。
- Java client 指标。
- 成本指标。
- 安全指标。

告警：

- 要有阈值。
- 要有窗口。
- 要有持续时间。
- 要有严重级别。
- 要有 runbook hint。

灰度：

- stable version。
- candidate version。
- feature flag。
- kill switch。
- guardrail metric。
- tenant tier。
- rollout percentage。

SLO / Runbook：

- SLI 表示测什么。
- SLO 表示目标是多少。
- SLA 表示外部承诺。
- Error Budget 表示允许失败空间。
- Incident Severity 表示故障等级。
- Runbook 表示故障处理步骤。

面试表达：

```text
我把线上运营设计成闭环：监控指标发现趋势，告警触发处理，SLO 定义服务目标，错误预算约束发布风险，灰度发布控制候选版本影响面，异常时通过 kill switch 或 rollback 快速止损，并用 Runbook 固化排查、降级、回滚和升级步骤。
```

## 阶段 10 技术点总表

| 能力 | 学过的技术点 | 解决的问题 |
| --- | --- | --- |
| 可观测性 | trace_id、span、event、metric、Python/Java trace 对齐 | 请求慢了、错了能定位 |
| 日志安全 | LLM 日志脱敏、密钥配置、`.env.example`、安全元信息 | 避免日志泄露 prompt、隐私、API Key |
| 成本治理 | token usage、模型价格、成本估算、预算预检 | 防止 AI 调用成本失控 |
| 性能治理 | latency breakdown、多阶段耗时拆解 | 知道慢在 LLM、RAG、Tool 还是 Java |
| 模型治理 | 多模型路由、fast/balanced/strong、fallback | 不同任务用不同模型，主模型失败可兜底 |
| 流量保护 | rate limit、429、Retry-After | 防止用户、路由、AI 能力或工具被打爆 |
| 失败恢复 | retry、timeout、总超时预算、可重试错误分类 | 临时失败可恢复，永久失败不盲目重试 |
| 流式体验 | SSE start/message/heartbeat/error/done | 流式开始后也能表达错误和完成 |
| 安全边界 | Prompt Injection、权限控制、隐私脱敏 | 防止模型被恶意输入诱导越权 |
| 质量评估 | eval dataset、baseline、candidate、metric、report | AI 质量可比较、可回归 |
| 坏例闭环 | bad case、failure_layer、regression case | 失败样本能沉淀为长期测试资产 |
| 生产监控 | counter、gauge、histogram、低基数标签、alert rule | 线上趋势和异常可观测 |
| 发布控制 | canary、feature flag、kill switch、rollback | 新模型、新 prompt、新 RAG 参数小流量验证 |
| 故障响应 | SLI、SLO、SLA、error budget、incident severity、Runbook | 服务质量有目标，故障处理有流程 |

## 项目表达模板

### 30 秒版本

```text
我做的是一个 AI 客服与智能工单系统，核心链路包括 FastAPI AI 服务、真实 Java Spring Boot 业务服务、RAG 知识库、Tool Calling 和 LangGraph Agent。后续我重点补了生产化能力，包括 tracing、日志脱敏、token 成本控制、多模型路由、fallback、限流、重试、超时、Prompt Injection 防护、自动化评估、bad case 回归、监控告警、灰度回滚和 SLO/Runbook，让项目不只是能跑通，而是具备真实上线和运营意识。
```

### 1 分钟版本

```text
这个项目是一个 AI 客服与智能工单系统。用户可以进行政策问答、订单查询和工单创建。Python AI 服务负责 LLM、RAG、Tool Calling 和 Agent 编排，Java Spring Boot 服务负责真实业务数据和工单写入，底层接入 MySQL、Redis 和向量数据库。

我后面重点做了 AI 应用生产化能力。比如用 trace_id 串联 Python 和 Java 链路，把一次请求拆成 HTTP、LLM、RAG、Tool、Java client 等阶段；LLM 日志只记录 provider、model、耗时、token 和错误码，不记录 prompt、用户原文和密钥；通过 token 成本估算、多模型路由、fallback、限流、重试和超时治理控制稳定性和成本；通过 Prompt Injection 防护、权限校验、字段白名单保护安全边界；再用评测集版本、bad case 和 regression case 做质量闭环。最后还整理了生产监控指标、灰度发布、回滚、SLO 和 Runbook。
```

### 3 分钟版本

```text
这个项目一开始不是只做一个简单聊天接口，而是按真实 AI 应用拆成几层。

第一层是 Python AI 服务，负责普通聊天、流式聊天、RAG 问答、Tool Calling 和 LangGraph Agent 编排。第二层是真实 Java Spring Boot 业务服务，使用传统 controller、service、mapper、entity、dto 结构，接 MySQL 和 Redis，提供订单查询、工单创建、权限校验、幂等和错误码。第三层是知识库和向量检索，包括文档切分、embedding、Qdrant、Milvus 对比、混合检索、rerank、引用校验、metadata filter 和 RAG 评估。

在生产化阶段，我重点补了六类能力。第一是可观测性，用 trace_id、span、event、metric 区分单次链路、阶段片段、关键事件和聚合指标，并对齐 Python 和 Java 日志。第二是日志与密钥安全，LLM 调用只记录安全元信息，不记录 prompt、用户输入、系统提示词、工具结果和 API Key。第三是成本和性能治理，包括 token usage 归一化、模型价格、请求成本估算、耗时拆解、多模型路由和预算预检。第四是稳定性保护，包括 fallback、限流、重试、总超时预算和 SSE 流式中断处理。第五是安全和质量，包括 Prompt Injection 防护、权限边界、隐私脱敏、自动化评估、评测集版本、bad case 分析和回归测试。第六是线上运营，包括生产监控指标、告警规则、灰度发布、feature flag、kill switch、rollback、SLO、错误预算和 Runbook。

所以这个项目的重点不是只会调用大模型，而是把 LLM、RAG、Tool Calling 和传统 Java 后端结合起来，并补上真实上线时需要考虑的稳定性、安全性、成本、质量评估和运营能力。
```

## 简历素材

### 项目名称

```text
AI 客服与智能工单系统
```

### 项目简介

```text
基于 FastAPI、Java Spring Boot、LangGraph、RAG、Tool Calling、MySQL、Redis 和向量数据库构建 AI 客服与智能工单系统，支持知识库问答、订单查询、工单创建、多轮确认和真实业务服务调用，并补齐 tracing、成本控制、限流重试、Prompt Injection 防护、自动化评估、灰度回滚和 SLO/Runbook 等生产化能力。
```

### 简历 bullet 版本 1：偏完整

```text
- 设计并实现 AI 客服与智能工单系统，使用 FastAPI 承载 LLM/RAG/Agent 编排，Java Spring Boot + MyBatis + MySQL/Redis 承载订单和工单业务能力，通过 Tool Calling 打通 AI 服务与真实业务后端。
- 构建企业知识库 RAG 链路，覆盖文档切分、embedding、向量检索、metadata filter、hybrid search、rerank、context compression、引用校验和 RAG 质量评估，提升知识问答的可追溯性和可靠性。
- 为 AI 服务补齐生产化治理能力，包括 trace_id 链路追踪、LLM 日志脱敏、token 成本估算、多模型路由、fallback、限流、重试、超时治理和 SSE 流式中断处理。
- 建立 AI 安全与质量闭环，覆盖 Prompt Injection 防护、权限控制、敏感信息脱敏、自动化评估集版本管理、bad case 收集分析和 regression case 回归验证。
- 设计生产运营能力，包括监控指标、告警规则、灰度发布、feature flag、kill switch、rollback、SLO、错误预算和 Runbook，提升系统上线后的可观测性、稳定性和可恢复性。
```

### 简历 bullet 版本 2：更简洁

```text
- 基于 FastAPI + Spring Boot 构建 AI 客服与智能工单系统，集成 LLM API、RAG、Tool Calling、LangGraph Agent、MySQL、Redis 和向量数据库，实现知识问答、订单查询和工单创建。
- 设计 AI 应用生产化能力，覆盖 tracing、日志脱敏、token 成本控制、多模型路由、fallback、限流、重试、超时、SSE 流式输出和灰度回滚。
- 建立安全和质量闭环，支持 Prompt Injection 防护、权限边界、字段白名单、自动化评估、bad case 分析、回归测试、监控告警、SLO 和 Runbook。
```

### 简历 bullet 版本 3：适合后端转 AI 应用开发

```text
- 在传统 Java 后端能力基础上，构建 Python AI 服务与 Java 业务服务协作的智能客服系统，将 LLM、RAG、Tool Calling、Agent 编排与 MySQL/Redis 业务数据打通。
- 重点解决 AI 应用工程化问题，包括模型调用失败、token 成本不可控、RAG 质量波动、工具调用越权、日志泄露、流式中断和线上故障恢复等风险。
- 补齐生产级治理链路，包含 trace_id 跨服务追踪、评测集和 bad case 回归、监控告警、灰度发布、回滚开关、SLO 和 Runbook。
```

## 面试常见问题

### 问题 1：你这个项目和普通 ChatGPT 套壳有什么区别？

参考回答：

```text
普通套壳主要是把用户输入转发给模型，然后展示回答。我的项目重点是把 AI 能力接入真实业务系统。它包含 RAG 知识库、Tool Calling、LangGraph Agent、Java Spring Boot 业务服务、MySQL/Redis 数据、订单查询和工单创建。模型不能直接操作业务数据，只能提出工具调用意图，后端负责参数校验、权限、幂等、字段白名单和错误码映射。另外我还补了 tracing、成本控制、限流、重试、超时、Prompt Injection 防护、评估、bad case 回归、灰度回滚和 SLO/Runbook 等生产化能力。
```

### 问题 2：你怎么定位一次 AI 请求为什么慢？

参考回答：

```text
我不会只看总耗时，而是通过 trace_id 和 span 把一次请求拆开。比如 HTTP 入口、LLM 调用、RAG 检索、rerank、tool validation、tool execution、Java client、SSE 输出都可以作为独立阶段。这样当 p95 延迟升高时，可以看慢在模型、向量检索、工具调用还是 Java 业务服务。同时 metric 用来看整体趋势，日志用来看具体错误，trace 用来看单次链路。
```

### 问题 3：LLM 调用日志怎么保证安全？

参考回答：

```text
LLM 调用日志我只记录安全元信息，比如 provider、model、operation、outcome、elapsed_ms、token usage、error_code 和 trace_id。不记录完整 prompt、用户原始输入、系统提示词、RAG 原文、工具结果、API Key 和 Authorization。这样既能排查模型失败、耗时和成本，又避免日志系统变成敏感信息泄露点。
```

### 问题 4：fallback、retry、timeout 有什么区别？

参考回答：

```text
retry 是同一路径遇到临时失败后再试一次，适合网络抖动、临时 5xx、可重试超时或 429。fallback 是主路径不可用时切换备用路径，比如主模型失败后切备用模型。timeout 是控制每次调用和整条链路的最长等待时间，防止 LLM、RAG、工具和 Java 调用叠加后用户一直等待。它们要配合使用，但不能混成一件事。
```

### 问题 5：你怎么控制 AI 应用成本？

参考回答：

```text
我从 token 和模型两个角度控制成本。首先归一化 prompt tokens、completion tokens 和 total tokens，并根据模型价格估算单次请求成本。其次按任务复杂度做 fast、balanced、strong 多模型路由。再次在请求前做预算预检，对高成本请求限制 max output tokens、禁用不必要 fallback 或阻断超预算请求。另外也会通过日志和 metric 观察高成本来源，比如长上下文、多轮历史、RAG 文档过多、重试和 fallback。
```

### 问题 6：你怎么防 Prompt Injection？

参考回答：

```text
我把用户输入、RAG 文档和工具结果都当作不可信外部输入，不允许它们改变系统规则或越过权限边界。对于高置信 prompt injection，会在后端入口做阻断或安全响应。工具调用也不是模型说了算，后端会做工具名校验、参数校验、权限校验、字段白名单、写操作确认和幂等控制。模型不能直接访问数据库，也不能绕过 Java 后端权限。
```

### 问题 7：你怎么评估 AI 回答质量？

参考回答：

```text
我区分测试和评估。测试主要验证代码确定性逻辑，比如参数校验、错误映射、权限边界。评估用于判断 AI 输出质量，比如回答是否命中预期、RAG 引用是否正确、是否遵守安全规则。我会维护 eval dataset 版本，记录 baseline 和 candidate 的 eval run，并把失败样本沉淀成 bad case。修复后再把 bad case 转成 regression case，防止同类问题再次出现。
```

### 问题 8：灰度发布在 AI 应用里怎么用？

参考回答：

```text
AI 应用里灰度发布不仅用于普通代码，也适用于新模型、新 prompt、新 RAG 参数、新路由策略和新安全策略。我会保留 stable version 和 candidate version，通过 feature flag、tenant tier 和 rollout percentage 控制候选版本流量，并用 guardrail metrics 观察失败率、延迟、成本、RAG 质量和安全拦截。如果候选版本指标异常，可以通过 kill switch 或 rollback 让流量回到稳定版本。
```

### 问题 9：SLO 和告警有什么区别？

参考回答：

```text
告警是某个指标在某个窗口内超过阈值，用来提醒团队处理异常。SLO 是服务等级目标，用来定义服务在一段时间内应该达到什么质量水平。比如告警可以是 15 分钟内 LLM 失败率超过 10%，SLO 可以是 30 天内 LLM 成功率不低于 98%。告警偏实时处理，SLO 偏长期质量目标和错误预算管理。
```

### 问题 10：Runbook 的价值是什么？

参考回答：

```text
Runbook 是故障处理手册。它把告警触发后该看什么、怎么判断影响面、怎么降级、什么时候回滚、什么时候升级、怎么确认恢复提前写清楚。故障时人很容易紧张，如果没有 Runbook，处理会依赖临场经验。AI 应用尤其需要 Runbook，因为故障来源可能是 LLM、RAG、Tool、Java 服务、成本、安全策略或流式输出。
```

## 当前项目能力边界

阶段 10 学完后，项目已经具备较强的工程化学习价值。

已经具备：

- Python AI 服务。
- Java Spring Boot 真实业务服务。
- MySQL / Redis 业务依赖。
- RAG 和向量数据库链路。
- Tool Calling 和 Agent 编排。
- MCP 基础能力。
- 生产化治理模型和部分落地代码。
- 自动化测试和评估基础。
- 项目表达、架构图、运行说明和学习笔记。

但还没有完全等同于企业正式生产系统。

还需要继续补：

- 更完整的前端管理台。
- 用户登录和权限体系。
- 更完整的数据库表和业务流程。
- 真实部署环境。
- CI/CD。
- 真实监控平台接入。
- 更完整的线上告警通知。
- 更完整的产品功能。
- 更接近企业项目的部署文档和演示脚本。

所以合理表达是：

```text
这是一个具备真实工程架构和生产化意识的 AI 应用项目，已经可以作为简历项目继续打磨，但后续还可以进一步作品化、前端化、部署化和产品化。
```

## 后续学习路线建议

阶段 10 完成后，下一步不建议继续零散学很多概念。

更合理的路线是进入“完整项目真实化”。

建议后续按这个方向推进：

```text
阶段 11：完整智能工单系统项目化
```

可以包括：

- 统一项目需求和产品范围。
- 设计前端页面。
- 完善用户、订单、工单、知识库、AI 会话等业务模块。
- 完善 Java 后端接口。
- 完善 Python AI 服务接口。
- 打通前端、Java、Python、MySQL、Redis、向量数据库。
- 接入真实 LLM、真实 embedding、真实 rerank。
- 整理部署方案。
- 整理演示脚本。
- 整理简历和面试材料。

阶段 10 已经补了很多生产化知识。下一阶段如果继续学习，重点应该从“单点技术”转向“把系统做成完整作品”。

## 常见误区

### 误区 1：觉得会调模型 API 就等于会 AI 应用开发

调 API 只是入口。

真实 AI 应用还要考虑 RAG、Tool、Agent、权限、成本、稳定性、评估、监控和故障处理。

### 误区 2：简历里只堆技术名

比如写：

```text
使用 FastAPI、LangChain、RAG、Redis、MySQL。
```

这不够。

更好的写法是把技术和问题绑定：

```text
通过 RAG 引用校验和 bad case 回归降低无依据回答风险，通过 token 成本估算和多模型路由控制大模型调用成本。
```

### 误区 3：把生产化理解成部署到服务器

部署只是生产化的一部分。

生产化还包括：

- 可观测。
- 可恢复。
- 可控成本。
- 可评估。
- 可灰度。
- 可回滚。
- 有安全边界。
- 有故障处理流程。

### 误区 4：觉得 AI 输出质量靠人工看几次就行

人工体验很重要，但不够稳定。

真正的项目要有 eval dataset、baseline、candidate、bad case、regression case。

### 误区 5：觉得模型越强越好

模型越强通常越贵、越慢。

真实系统要根据任务复杂度做模型路由，而不是所有请求都用最贵模型。

### 误区 6：忽略“模型不能直接做业务决策”

模型可以理解意图、生成结构化参数、请求工具。

但是鉴权、幂等、字段白名单、写操作确认、审计和最终业务执行必须由后端控制。

## 本节练习

### 练习 1：用六层能力复述阶段 10

请你用自己的话说出阶段 10 的六层能力。

参考答案：

```text
阶段 10 可以分成可观测性、日志与安全、成本与性能治理、稳定性保护、安全边界与质量评估、发布运营与故障响应六层。
```

展开表达：

```text
可观测性负责 trace、span、event、metric；日志与安全负责 LLM 日志脱敏和密钥管理；成本与性能治理负责 token 成本、耗时拆解和模型路由；稳定性保护负责 fallback、限流、重试、超时和 SSE；安全边界与质量评估负责 Prompt Injection、防越权、eval 和 bad case；发布运营与故障响应负责监控、告警、灰度、回滚、SLO 和 Runbook。
```

### 练习 2：回答“你怎么让 AI 项目更像真实项目”

参考答案：

```text
我没有只做模型调用，而是把 AI 应用接入真实 Java 业务服务和数据库，并补了生产化能力。比如通过 trace_id 追踪 Python 和 Java 链路，通过日志脱敏保护 prompt 和隐私，通过 token 成本估算和多模型路由控制成本，通过 fallback、限流、重试和超时提升稳定性，通过 Prompt Injection 防护和权限校验控制安全边界，通过评测集、bad case 和回归测试管理 AI 质量，再通过监控告警、灰度回滚、SLO 和 Runbook 支撑上线后的运营。
```

### 练习 3：把阶段 10 写成一句简历 bullet

参考答案：

```text
为 AI 客服与智能工单系统补齐生产化治理能力，覆盖 trace_id 链路追踪、LLM 日志脱敏、token 成本估算、多模型路由、fallback、限流、重试、超时治理、Prompt Injection 防护、自动化评估、bad case 回归、监控告警、灰度回滚、SLO 和 Runbook。
```

### 练习 4：解释为什么测试和评估不一样

参考答案：

```text
测试主要验证确定性代码逻辑，比如参数校验、权限判断、错误码映射、字段白名单。评估主要验证 AI 输出质量，比如回答是否符合预期、是否引用正确来源、是否遵守安全规则。测试偏工程正确性，评估偏模型效果和业务质量。
```

### 练习 5：解释为什么 AI 应用需要错误预算

参考答案：

```text
错误预算能把服务稳定性和迭代速度平衡起来。如果 SLO 允许少量失败，那么这部分允许失败空间就是错误预算。错误预算充足时可以继续灰度新模型、新 prompt 或新 RAG 参数；错误预算接近耗尽时应该暂停高风险发布，优先修复稳定性问题。
```

## 自测题

### 自测 1：阶段 10 最核心的变化是什么？

答案：

阶段 10 的核心变化是把项目从“功能能跑通”推进到“具备生产化和可运营意识”。也就是不仅能调用模型、检索知识、执行工具，还能追踪问题、控制成本、处理失败、防安全风险、评估质量、灰度发布和按 Runbook 处理故障。

### 自测 2：日志、trace、metric、alert、SLO、Runbook 分别解决什么？

答案：

日志解决单次事件细节，trace 解决一次请求的完整链路，metric 解决整体趋势统计，alert 解决异常提醒，SLO 解决服务质量目标，Runbook 解决故障发生后的标准处理步骤。

### 自测 3：为什么模型不能直接执行写操作？

答案：

因为模型输出不完全可靠，也不应该承担业务权限判断。写操作必须由后端做参数校验、权限校验、幂等控制、审计、字段白名单和确认机制。模型最多提出工具调用请求，不能直接改数据库。

### 自测 4：为什么 bad case 要转成 regression case？

答案：

bad case 是已经发生过的失败样本。如果只修一次，不进入回归测试，后续改 prompt、模型、RAG 参数或工具链时可能再次出现同类问题。转成 regression case 后，可以长期验证这个问题没有复发。

### 自测 5：阶段 10 完成后，下一步最适合做什么？

答案：

下一步最适合进入完整项目真实化，把已有 AI、RAG、Agent、Java 后端、数据库、缓存、向量库和生产化能力整合成更完整的项目，包括前端、真实部署、演示流程、业务功能补全和简历作品化。

## 阶段 10 总结

阶段 10 学完后，你掌握的不是某一个库的用法，而是一整套 AI 应用生产化思维。

可以总结为：

```text
功能层面：AI 服务能调用模型、检索知识、执行工具、编排 Agent。
业务层面：AI 服务能连接真实 Java 后端、MySQL、Redis 和业务接口。
工程层面：系统具备 tracing、日志安全、成本控制、限流、重试、超时、fallback、SSE 生产化。
安全层面：系统具备 Prompt Injection 防护、权限控制、隐私脱敏和工具边界。
质量层面：系统具备评测集、baseline/candidate、bad case 和 regression case。
运营层面：系统具备监控指标、告警、灰度、回滚、SLO、错误预算和 Runbook。
```

这套能力已经能支撑你去构建一个更完整、更真实、可以继续打磨成简历项目的 AI 应用。
