# 阶段 10 第 2 节：Tracing 是什么

## 本节定位

这一节学习 AI 应用生产化里的核心能力：Tracing，中文通常叫链路追踪、请求链路追踪或分布式追踪。

这节不写业务代码，也不急着接 OpenTelemetry、Jaeger、Grafana Tempo 这类工具。我们先把概念学明白：为什么一次 AI 请求必须能被追踪，追踪到底追什么，它和日志、指标、评估有什么区别。

如果这一节没学扎实，后面学 trace_id、span、event、metric、LLM 调用日志安全、token 成本、耗时拆解、多模型 fallback、RAG 评测、线上告警时，就会变成“知道名词，但是不知道为什么要这么设计”。

## 本节学习目标

学完本节，你要能说明：

1. Tracing 是什么。
2. 为什么传统后端能靠日志排查的问题，在 AI 应用里经常不够用。
3. 一次 AI 请求从入口到最终回答，可能经过哪些链路。
4. Tracing 和日志、指标、评估分别解决什么问题。
5. 为什么 AI 应用不仅要追踪“接口有没有报错”，还要追踪“模型、RAG、工具、成本、耗时、安全边界”。
6. 当前项目后续为什么要给 FastAPI、LLM、RAG、Tool、Java 服务、MySQL、Redis、SSE 都建立可追踪链路。

## 本节新增和修改

本节是纯知识学习节：

| 类型 | 内容 |
|---|---|
| 新增笔记 | `notes/stage10-02-what-is-tracing.md` |
| 修改进度 | 更新 `docs/learning-progress.md` |
| 新增代码 | 无 |
| 手动测试文档 | 无，纯知识节不需要 |

## 一句话先讲透

Tracing 就是给一次请求建立一份“完整行程单”：请求从哪里进来，经过了哪些服务和步骤，每一步花了多久，是否失败，为什么失败，调用了哪个模型、检索了哪些知识、执行了什么工具，最后如何生成回答。

## 基础知识铺垫

### 1. 先从一个真实排查问题说起

假设用户问 AI 客服：

> 我的订单 A1001 物流为什么还没更新？

后端返回很慢，最后还回答错了。

如果你只看接口状态，可能只看到：

```text
POST /chat 200 OK
耗时：12.8s
```

这说明接口没有 HTTP 500，但它没有告诉你真正的问题在哪里。

可能的原因有很多：

| 可能原因 | 说明 |
|---|---|
| 模型慢 | LLM API 响应耗时太长 |
| 检索慢 | 向量库搜索或 rerank 耗时太长 |
| 检索错 | RAG 找到的知识和订单问题无关 |
| 工具没调 | 模型本该调用 `query_order`，但直接回答了 |
| 工具参数错 | 模型提取订单号失败，把 `A1001` 提成了 `1001` |
| Java 服务慢 | Python 调 Java 订单服务耗时高 |
| 权限拒绝 | 用户无权查看该订单 |
| Redis / MySQL 慢 | Java 后端查询缓存或数据库慢 |
| prompt 被攻击 | 用户诱导模型绕过权限或泄露内部信息 |
| fallback 触发 | 主模型失败，切到了备用模型 |
| token 过多 | 上下文太长，成本高且响应慢 |
| 最终总结错 | 工具结果正确，但模型最后总结时说错了 |

这些问题单靠一行接口日志很难判断。

Tracing 的价值，就是把这次请求拆成一段一段可观察的链路，让你知道问题到底发生在哪一段。

### 2. 什么是 Trace

Trace 可以理解为一次完整请求的全链路记录。

在传统后端里，一次请求可能是：

```text
浏览器
-> Spring Boot Controller
-> Service
-> Mapper
-> MySQL
-> 返回结果
```

在 AI 应用里，一次请求可能是：

```text
用户问题
-> FastAPI /chat
-> 参数校验
-> prompt 构造
-> LLM 第一次调用
-> 判断是否需要工具
-> 调用 Java 业务服务
-> Java 查 Redis / MySQL
-> 工具结果返回 Python
-> LLM 第二次调用
-> 最终回答
-> SSE 流式输出
```

这整条链路，就可以称为一个 trace。

trace 的重点不是“某一行日志”，而是“这次请求完整经过了什么”。

### 3. 什么是 Tracing

Tracing 是收集、串联、查询、分析 trace 的能力。

你可以把它理解成一套机制：

| 能力 | 解释 |
|---|---|
| 生成链路标识 | 给一次请求分配唯一身份，例如 trace_id |
| 传递上下文 | Python 调 Java 时，把 trace_id 继续传下去 |
| 拆分阶段 | 把一次请求拆成 LLM、RAG、Tool、DB 等阶段 |
| 记录关键属性 | 记录模型名、工具名、状态、耗时、错误码等 |
| 关联日志 | 让每条日志都能回到同一次请求 |
| 分析问题 | 查询某次请求为什么慢、为什么错、为什么贵 |

所以 Tracing 不是一个单独的函数，也不是一条日志，而是一种“把复杂请求看清楚”的系统能力。

### 4. 为什么 AI 应用比传统后端更需要 Tracing

传统后端的业务逻辑通常更确定：

```text
请求参数
-> 业务判断
-> 数据库查询
-> 返回固定格式结果
```

同样的输入，在数据不变的情况下，结果通常比较稳定。

AI 应用多了很多不确定性：

| 不确定来源 | 说明 |
|---|---|
| 模型输出不稳定 | 同一个问题，模型可能给出不同表达甚至不同判断 |
| 外部 API 依赖 | 模型服务可能超时、限流、波动 |
| prompt 影响结果 | prompt 一点变化可能导致输出质量变化 |
| RAG 检索质量不稳定 | 召回的文档不同，最终回答会变 |
| 工具调用由模型决定 | 模型可能该调用工具却没调用，也可能调用错工具 |
| token 成本不可忽略 | 输入越长、输出越长，成本越高 |
| 安全风险更复杂 | Prompt Injection 可能让模型越权、泄露信息 |

这些不确定性都不是单纯看 HTTP 200 / 500 能解决的。

Tracing 能把这些不确定步骤变成可观察对象。

### 5. 日志能做什么，不能做什么

日志是最常见的排查工具，例如：

```text
INFO received chat request trace_id=abc123
INFO call llm model=qwen3.7-plus trace_id=abc123
ERROR java service timeout trace_id=abc123
```

日志很重要，但单靠日志有几个问题：

| 问题 | 说明 |
|---|---|
| 日志是散的 | 多个服务、多个文件、多个线程里到处都是 |
| 难看层级 | 很难一眼看到谁调用谁 |
| 难看耗时比例 | 不容易看出 12 秒里 LLM 用了 10 秒还是 DB 用了 10 秒 |
| 难还原完整链路 | 需要人工按 trace_id 拼接很多日志 |
| AI 细节容易混乱 | LLM、RAG、Tool、rerank、fallback 混在日志里不好分析 |

Tracing 不是替代日志，而是把日志组织起来。

一个简单理解：

| 工具 | 更像什么 |
|---|---|
| 日志 logs | 每个地方写的“现场记录” |
| 链路 tracing | 一次请求的“完整行程单” |
| 指标 metrics | 很多请求汇总后的“统计报表” |
| 评估 eval | 回答质量的“考试和评分” |

### 6. Tracing 和 Metrics 的区别

Metrics 是指标，通常看的是聚合数据，例如：

```text
/chat 平均耗时 3.2s
P95 耗时 8.5s
LLM 调用成功率 99.2%
今日 token 成本 28 元
RAG 命中率 76%
```

Metrics 适合回答：

| 问题 | 示例 |
|---|---|
| 系统整体快不快 | P95 延迟是多少 |
| 系统稳定不稳定 | 错误率是多少 |
| 成本有没有失控 | 每天 token 消耗多少 |
| 服务是否需要告警 | 5 分钟内错误率是否超过阈值 |

Tracing 适合回答：

| 问题 | 示例 |
|---|---|
| 某一次请求为什么慢 | 是 LLM 慢、RAG 慢还是 Java 慢 |
| 某一次回答为什么错 | 检索错了、工具错了还是总结错了 |
| 某一次为什么没调工具 | 模型判断、tool_choice、prompt 或校验逻辑的问题 |
| 某一次 fallback 是否发生 | 主模型失败后有没有切备用模型 |

一句话区分：

```text
Metrics 看整体趋势，Tracing 看单次链路。
```

两者必须配合。

线上告警通常先由 metrics 发现“整体异常”，再用 tracing 下钻到“具体哪次请求、哪一步异常”。

### 7. Tracing 和 Evaluation 的区别

Evaluation 是评估，主要关注回答质量。

例如：

| 评估项 | 关注点 |
|---|---|
| 是否回答正确 | 有没有根据订单真实状态回答 |
| 是否引用知识库 | 是否基于 RAG 内容回答 |
| 是否遵守权限 | 是否泄露别人的订单信息 |
| 是否拒绝危险请求 | 是否抵御 Prompt Injection |
| 表达是否清楚 | 用户能不能看懂 |

Tracing 不直接等于质量评估。

但是 tracing 可以给评估提供证据。

比如一次回答被评为 bad case，tracing 能继续告诉你：

| Bad Case 现象 | Tracing 可能定位到 |
|---|---|
| 回答编造了物流状态 | 工具没有调用，模型直接猜了 |
| 回答用了错误知识 | RAG 召回了无关 chunk |
| 回答泄露敏感信息 | 权限校验 span 失败但后续仍继续生成 |
| 回答慢 | rerank 或 LLM second call 耗时异常 |

所以 eval 负责判断“答得好不好”，tracing 负责还原“为什么会这样”。

### 8. 一次 AI 请求的典型链路

以后我们项目里的一次完整 AI 客服请求，大致可能是这样：

```text
用户请求
-> FastAPI 接收请求
-> 生成 / 接收 trace_id
-> 校验参数和用户身份上下文
-> 查询会话历史
-> 判断是否需要 RAG
-> 生成 embedding
-> 搜索向量数据库
-> rerank 候选知识
-> 构造 prompt
-> 调用 LLM
-> 模型决定是否调用 tool
-> 后端校验 tool name / arguments
-> 调用 Java 业务服务
-> Java 查询 Redis / MySQL
-> Java 返回结构化结果
-> Python 校验工具结果
-> 把 tool result 回传模型
-> 模型生成最终回答
-> 输出给用户
```

这条链路里，每一步都可能出问题。

如果没有 tracing，排查时只能问：

```text
是不是模型的问题？
是不是 RAG 的问题？
是不是 Java 的问题？
是不是网络的问题？
是不是我代码的问题？
```

这些问题都太粗。

有了 tracing，就能问得更具体：

```text
这次请求的 query_order 工具有没有被模型请求？
模型请求工具时参数是什么？
后端有没有拦截非法工具名？
Java 服务返回的业务错误码是什么？
RAG 搜到了哪些 chunk？
rerank 后 top1 分数是多少？
第一次 LLM 调用耗时多少？
第二次 LLM 调用耗时多少？
总 token 消耗多少？
最终回答有没有基于工具结果？
```

这就是生产化排查能力的差别。

### 9. Tracing 的核心思想：上下文传递

Tracing 能串起来，靠的是上下文传递。

最常见的上下文就是 trace_id。

例如：

```text
FastAPI 收到请求，生成 trace_id = t-001
Python 调用 LLM 时带上 t-001
Python 调用 Java 时通过请求头传 t-001
Java 写日志时也带上 t-001
Java 查询数据库失败时也记录 t-001
Python 最终返回时也带上 t-001
```

这样一来，即使请求跨越多个服务，你也能通过同一个 trace_id 把它们找回来。

当前项目之前已经学过 trace_id 请求追踪。

但要注意：

```text
有 trace_id，只是 tracing 的第一步。
```

真正的 tracing 还要知道：

| 还需要什么 | 为什么 |
|---|---|
| 每个阶段是什么 | 知道请求经过了哪些步骤 |
| 每个阶段耗时多少 | 找慢点 |
| 每个阶段是否成功 | 找失败点 |
| 每个阶段关键属性 | 找模型、工具、知识库、错误码等上下文 |
| 父子关系 | 知道哪个步骤调用了哪个子步骤 |

这些内容后面会通过 span、event、metric 等概念逐步展开。

### 10. 为什么要有“阶段拆分”

如果只记录：

```text
/chat total_duration_ms=12000
```

你只知道总耗时 12 秒。

但生产排查真正想知道的是：

| 阶段 | 耗时 |
|---|---|
| request validation | 5ms |
| load conversation | 30ms |
| embedding | 300ms |
| vector search | 80ms |
| rerank | 900ms |
| first llm call | 4500ms |
| tool execution | 200ms |
| second llm call | 6000ms |
| response serialization | 10ms |

这时你会发现，主要耗时不在 Java 服务，也不在向量库，而是在两次 LLM 调用。

这就是阶段拆分的价值。

没有拆分，就只能猜。

有了拆分，优化方向会更清楚：

| 发现的问题 | 可能优化方向 |
|---|---|
| LLM 很慢 | 换模型、启用流式、限制输出长度、fallback |
| embedding 慢 | 缓存 query embedding、换 embedding 模型 |
| rerank 慢 | 减少候选数量、只对高价值问题 rerank |
| Java 慢 | 查数据库索引、Redis 缓存、连接池 |
| 工具失败多 | 检查参数校验、权限、幂等 |

### 11. Tracing 关注的不只是错误

很多初学者会觉得：

```text
没报错就不用追踪。
```

这是不对的。

AI 应用的很多线上问题并不是异常，而是“质量、成本、体验、安全”问题。

| 问题类型 | 例子 |
|---|---|
| 慢 | 接口 200，但是用户等了 15 秒 |
| 贵 | 接口 200，但是一次请求用了大量 token |
| 错 | 接口 200，但是回答不符合事实 |
| 编造 | 接口 200，但是模型没有依据工具结果 |
| 越权 | 接口 200，但是泄露了不该看的信息 |
| 不稳定 | 接口 200，但是同类问题有时好有时坏 |
| 体验差 | 接口 200，但是 SSE 卡住或中断后无提示 |

这些都需要 tracing 帮你看清楚过程。

### 12. AI Tracing 应该记录哪些信息

一个实用的 AI tracing，不是把所有内容都原样保存。

它应该记录对排查有用、又不造成隐私风险的信息。

常见可记录内容：

| 类别 | 示例 |
|---|---|
| 请求信息 | trace_id、user_id hash、tenant_id、接口名 |
| 模型信息 | model、provider、temperature、max_tokens |
| token 信息 | input_tokens、output_tokens、total_tokens、估算成本 |
| 耗时信息 | LLM 耗时、RAG 耗时、工具耗时、Java 耗时 |
| RAG 信息 | collection、top_k、召回数量、rerank 是否启用 |
| 工具信息 | tool_name、参数校验结果、执行状态、业务错误码 |
| 安全信息 | 是否触发 prompt injection 拦截、权限校验结果 |
| fallback 信息 | 是否发生 fallback、fallback 原因、备用模型 |
| 结果信息 | success、error_code、finish_reason |

需要谨慎记录或脱敏记录的内容：

| 内容 | 风险 |
|---|---|
| API Key | 绝对不能记录 |
| 完整用户隐私 | 可能泄露手机号、地址、订单信息 |
| 完整 prompt | 可能包含系统提示词、内部规则、用户隐私 |
| 完整 tool result | 可能包含业务敏感数据 |
| 认证 token | 绝对不能记录 |
| 内部密钥和连接串 | 绝对不能记录 |

生产化不是“记录越多越好”，而是“记录足够排查，同时控制隐私和安全风险”。

### 13. Tracing 的最小可用版本

对当前学习项目来说，最小可用 tracing 不需要一开始就接复杂平台。

可以先达到这些目标：

| 能力 | 最小要求 |
|---|---|
| 请求有唯一 trace_id | 每次请求都能查到同一条链路 |
| 跨服务传递 trace_id | Python 调 Java 时继续传递 |
| 关键阶段可区分 | LLM、RAG、Tool、Java 至少能分开 |
| 关键阶段有耗时 | 能知道慢在哪里 |
| 关键阶段有状态 | success / failed / fallback / denied |
| 关键错误有码 | 不只是一句“调用失败” |
| 敏感内容不落日志 | prompt、key、隐私数据要控制 |

这就是我们后面逐步实现的基础。

### 14. Tracing 在面试和项目表达里的价值

如果你只说：

> 我做了一个 AI 客服系统，可以调用大模型和 RAG。

这更像 demo。

如果你能说：

> 我给 AI 请求链路设计了 trace_id 贯穿 FastAPI、LLM、RAG、Tool Calling、Java 业务服务和数据库访问；能够拆分模型调用、向量检索、rerank、工具执行、业务权限校验、最终回答生成的耗时和状态，用于定位慢请求、错误回答、工具调用失败、fallback 和 token 成本异常。

这就更像真实工程项目。

Tracing 的价值不只是技术点本身，而是证明你知道 AI 应用上线后怎么排查问题、怎么控制风险、怎么持续运营。

## 本节主题系统讲解

### 1. 当前项目为什么要引入 Tracing

当前项目已经不是一个单接口 demo。

我们前面已经做过：

| 模块 | 已学习内容 |
|---|---|
| Python FastAPI | AI 服务入口、配置、日志、异常、SSE |
| LLM API | 模型调用、结构化输出、工具调用 |
| RAG | 文档切分、embedding、Qdrant、Milvus、rerank、检索评测 |
| Agent / Tool | 模型决定工具、后端校验工具、执行工具、再交给模型总结 |
| Java Spring Boot | 真实业务服务、MySQL、Redis、权限、幂等、限流、熔断、SSE 对接 |
| 安全 | Prompt Injection、权限边界、敏感信息控制 |
| 评估 | eval dataset、evaluator、bad case、回归测试 |

这些模块一旦连起来，问题就不再局限于一个函数。

例如：

```text
用户说回答错了
```

你要判断：

| 方向 | 要查什么 |
|---|---|
| 输入层 | 用户问题是否被正确接收 |
| RAG 层 | 是否检索到了正确知识 |
| 模型层 | 模型是否理解了问题 |
| 工具层 | 是否请求了正确工具 |
| Java 层 | 工具结果是否真实 |
| 权限层 | 用户是否有权访问 |
| 输出层 | 最终回答是否忠于证据 |

Tracing 就是把这些层串起来。

### 2. 在当前项目里，一条 trace 应该覆盖哪些节点

后续比较理想的一条 trace，可以覆盖：

```text
FastAPI request
-> auth / caller context
-> request validation
-> chat orchestration
-> prompt building
-> safety check
-> rag retrieval
-> embedding
-> vector search
-> rerank
-> llm call
-> tool decision
-> tool argument validation
-> java-business-service call
-> Java controller
-> Java service
-> Redis / MySQL
-> Java response
-> Python tool result validation
-> final llm call
-> final answer
-> SSE response
```

不是每一节都要一次性实现全部节点。

但你要先建立这个全局图，否则后续学习每个点时会碎。

### 3. Tracing 让问题从“猜测”变成“定位”

没有 tracing 时，排查问题像这样：

```text
回答慢，是不是模型慢？
回答错，是不是 RAG 错？
接口失败，是不是 Java 挂了？
成本高，是不是 prompt 太长？
```

有 tracing 后，排查问题可以变成：

```text
trace_id=t-20260801-001

总耗时：9800ms
RAG：320ms
rerank：700ms
LLM first call：4100ms
Tool query_order：180ms
LLM final call：4300ms
token：input 6200 / output 850
fallback：false
tool：query_order success
permission：passed
```

这时你就知道：

1. 慢主要在两次 LLM。
2. Java 工具不是瓶颈。
3. RAG 不是主要瓶颈。
4. 成本高可能和输入 token 太多有关。
5. 如果回答错，要重点看模型是否正确使用 tool result。

Tracing 的核心作用就是减少猜测。

### 4. Tracing 不是为了“看起来专业”

生产项目里引入 tracing 的目的不是堆技术名词。

它解决的是这些真实问题：

| 问题 | Tracing 的作用 |
|---|---|
| 用户投诉某次回答错 | 查这次请求的证据链 |
| 某天成本突然升高 | 找高 token 请求和对应链路 |
| P95 延迟升高 | 找慢在哪个阶段 |
| fallback 频繁触发 | 查主模型失败原因 |
| 工具调用失败 | 查模型请求、参数校验、后端执行 |
| RAG 质量下降 | 查召回内容和 rerank 结果 |
| 权限问题 | 查权限校验是否执行、结果是什么 |
| SSE 中断 | 查流式输出在哪一段中断 |

这也是为什么阶段 10 不再只学“功能怎么写”，而是学“功能上线后怎么活下去”。

### 5. Tracing 和 trace_id 的关系

你可以先这样理解：

```text
trace_id 是一次请求的身份证号。
Tracing 是围绕这个身份证号收集整条请求行程的系统能力。
```

只有 trace_id，你能把日志关联起来。

有 tracing，你还能看到：

| 内容 | 例子 |
|---|---|
| 阶段 | llm_call、rag_retrieval、tool_execution |
| 层级 | /chat 包含 LLM，LLM 后又包含 tool |
| 耗时 | 每个阶段多少 ms |
| 状态 | success、failed、timeout、denied |
| 属性 | model、tool_name、collection、error_code |

下一节会专门拆：

```text
trace_id / span / event / metric
```

这节先把 tracing 的整体价值和使用场景学透。

### 6. 当前项目的 Tracing 边界

当前项目后续做 tracing 时，要遵守几个边界：

| 边界 | 说明 |
|---|---|
| 先追关键链路 | 不一开始追所有函数 |
| 先做可解释 | 让学习者看懂链路意义 |
| 先控敏感信息 | 不把 prompt、key、隐私全量写出 |
| 先统一语义 | Python 和 Java 对 trace_id、error_code、耗时字段理解一致 |
| 先服务业务排查 | 不为了工具而工具 |

好的 tracing 不是追踪越细越好。

太粗，排查不了问题。

太细，数据量大、成本高、噪声多、还可能泄露隐私。

当前阶段先追这些主线就够：

```text
入口请求
模型调用
RAG 检索
rerank
工具决策
工具执行
Java 业务调用
数据库/缓存访问结果摘要
最终回答生成
SSE 输出状态
```

### 7. Tracing 对后续课程的影响

后面很多节都会依赖这节：

| 后续章节 | 和 Tracing 的关系 |
|---|---|
| trace_id / span / event / metric | 把 tracing 的组成部分拆清楚 |
| Python AI 服务 tracing | 在 FastAPI 和 AI 链路里落地 |
| Java 业务服务 tracing 对齐 | 让 Java 服务接住并传递链路上下文 |
| LLM 调用日志安全 | 决定模型调用里哪些能记录、哪些不能 |
| Token 成本统计 | 把成本挂到 trace 上 |
| 请求耗时拆解 | 用 span 定位慢点 |
| 多模型路由 / fallback | 追踪路由选择和切换原因 |
| SSE 生产化 | 追踪流式输出是否正常 |
| Prompt Injection 防护 | 记录安全拦截结果 |
| 自动化评估 / Bad Case | 把质量问题和链路证据关联 |
| 监控和告警 | 从 trace 汇总出指标，再下钻排查 |

所以 Tracing 是阶段 10 的地基之一。

## 本节代码讲解

本节没有新增业务代码。

原因是：Tracing 不是先从装工具开始学，而是先从“为什么要追踪、追踪什么、追踪到什么程度”开始学。

如果一上来直接写装饰器、middleware、OpenTelemetry exporter，很容易变成：

```text
代码能跑，但是不知道这些字段为什么存在。
```

本节真正要掌握的是设计判断：

| 问题 | 你应该能回答 |
|---|---|
| 为什么要 tracing | 因为 AI 链路多、不确定、难排查 |
| tracing 看什么 | 看单次请求经过的阶段、耗时、状态、关键属性 |
| tracing 不该做什么 | 不该无脑记录隐私、密钥、完整 prompt |
| tracing 和日志区别 | 日志是现场记录，tracing 是链路行程单 |
| tracing 和 metrics 区别 | tracing 看单次，metrics 看整体 |
| tracing 和 eval 区别 | eval 判断质量，tracing 解释过程 |

## 常见误区

### 误区 1：Tracing 就是日志

不对。

日志是分散记录，tracing 是结构化链路。

日志可以属于 tracing 的证据之一，但 tracing 更强调一次请求的完整路径、阶段层级、耗时和状态。

### 误区 2：有 trace_id 就等于有 Tracing

不对。

trace_id 只是把同一次请求标出来。

如果没有阶段拆分、耗时、状态、关键属性，仍然很难判断问题在哪里。

### 误区 3：只要 HTTP 200，链路就是成功的

不对。

AI 应用可能 HTTP 200，但是回答错、成本高、越权、编造、没调用工具、检索错知识。

生产化不能只看接口状态码。

### 误区 4：记录越多越好

不对。

记录太少排查不了，记录太多会带来成本、噪声和安全风险。

AI 应用尤其不能随便记录完整 prompt、完整用户隐私、完整工具结果和密钥。

### 误区 5：Tracing 只是运维的事

不对。

开发者写接口、设计工具调用、设计 RAG、设计 fallback 时，就要考虑后续怎么追踪。

如果代码里没有传递 trace_id，没有清晰错误码，没有阶段边界，后面运维平台也很难补救。

### 误区 6：AI 应用只需要追踪模型调用

不对。

模型只是链路的一部分。

RAG、rerank、工具执行、Java 业务服务、权限校验、Redis、MySQL、SSE 输出都可能影响最终结果。

### 误区 7：Tracing 只用于定位慢请求

不对。

Tracing 也能帮助定位回答错误、工具调用失败、权限拒绝、fallback、成本异常、Prompt Injection 拦截和 bad case 原因。

## 本节练习

### 练习 1：用自己的话解释 Tracing

题目：不要背定义，用自己的话解释 Tracing 是什么。

参考答案：

Tracing 是把一次请求从入口到结束的完整过程记录下来。它不只记录有没有报错，还记录请求经过了哪些步骤，每一步用了多久，是否成功，关键参数是什么，方便以后排查慢、错、贵、安全风险等问题。

### 练习 2：区分日志和 Tracing

题目：为什么说日志不是 Tracing？

参考答案：

日志通常是一条条分散记录，告诉我们某个位置发生了什么。Tracing 是把同一次请求的多条记录串成完整链路，能看到阶段、层级、耗时、状态和关键属性。日志可以被 trace_id 关联起来，但只有日志不一定能形成清晰的链路。

### 练习 3：分析 AI 客服慢请求

题目：一次 `/chat` 请求耗时 15 秒，但 HTTP 返回 200。Tracing 应该帮助我们拆出哪些阶段？

参考答案：

至少应该拆出请求入口、会话读取、RAG 检索、embedding、向量搜索、rerank、LLM 调用、工具决策、工具执行、Java 服务调用、Redis/MySQL 访问、最终模型总结、SSE 输出等阶段。这样才能判断 15 秒主要花在模型、检索、工具、Java 后端还是输出过程。

### 练习 4：判断哪些信息不应该原样记录

题目：下面哪些信息不应该原样写入 trace 或日志：API Key、模型名、完整 prompt、tool_name、用户手机号、error_code、完整 tool result？

参考答案：

API Key 绝对不能记录；完整 prompt、用户手机号、完整 tool result 通常不能原样记录，必须脱敏、摘要化或只记录必要字段。模型名、tool_name、error_code 通常可以记录，因为它们对排查有价值，敏感风险较低。

### 练习 5：解释 Tracing 和 Evaluation 的关系

题目：如果一次回答被评测系统判定为 bad case，Tracing 能帮什么忙？

参考答案：

Evaluation 负责判断回答不好，Tracing 负责解释为什么不好。Tracing 可以帮助查看这次请求是否检索到了正确文档、是否调用了正确工具、工具参数是否正确、Java 服务返回了什么业务状态、模型是否基于工具结果总结、是否发生 fallback 或权限拒绝。

## 自测题

### 自测 1：Tracing 主要看单次请求还是整体趋势？

答案：主要看单次请求的完整链路。整体趋势通常由 metrics 观察。

### 自测 2：Metrics 和 Tracing 的一句话区别是什么？

答案：Metrics 看整体统计和趋势，Tracing 看某一次请求的详细过程。

### 自测 3：为什么 AI 应用 HTTP 200 也可能是失败体验？

答案：因为接口成功不代表回答正确。AI 应用可能出现回答编造、检索错误、工具没调用、权限越界、成本过高、响应过慢、SSE 中断等问题，这些都可能在 HTTP 200 下发生。

### 自测 4：trace_id 是不是 Tracing 的全部？

答案：不是。trace_id 只是链路标识。完整 tracing 还需要阶段拆分、耗时、状态、关键属性、错误码、父子关系和跨服务上下文传递。

### 自测 5：为什么不能把完整 prompt 都记录下来？

答案：完整 prompt 可能包含系统提示词、内部安全规则、用户隐私、业务敏感信息。生产环境记录完整 prompt 会带来泄密风险，所以通常要摘要化、脱敏或只记录必要元数据。

### 自测 6：当前项目里 Tracing 应该覆盖哪些核心链路？

答案：至少应覆盖 FastAPI 请求入口、LLM 调用、RAG 检索、embedding、向量数据库、rerank、工具决策、工具参数校验、Java 业务服务、Redis/MySQL 访问、最终回答生成和 SSE 输出状态。

## 本节小结

本节你要记住三句话：

1. Tracing 是一次请求的完整行程单。
2. AI 应用比传统后端更需要 Tracing，因为模型、RAG、工具、成本、安全和质量都存在不确定性。
3. Tracing 不是日志、不是指标、也不是评估，但它能把日志组织起来，帮助指标下钻，解释评估中的 bad case。

下一节学习：`阶段 10 第 3 节：trace_id / span / event / metric 的区别`。
