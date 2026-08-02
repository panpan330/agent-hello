# 阶段 10 第 10 节：多模型路由基础

## 本节定位

这一节学习 AI 应用生产化里的一个重要能力：

```text
多模型路由。
```

前面第 8 节学了 token 成本，第 9 节学了请求耗时拆解。

这一节要解决的问题是：

```text
一次请求进来以后，系统到底应该用哪个模型来处理。
```

## 本节学习目标

- 理解什么是多模型路由。
- 理解为什么真实 AI 系统通常不会只用一个模型。
- 理解 fast / balanced / strong 三类模型分层。
- 理解路由和成本、耗时、fallback、评测、安全的关系。
- 看懂本节新增的 `model_routing.py`。

## 本节新增和修改

- 新增 `app/core/model_routing.py`。
- 新增 `tests/test_model_routing.py`。
- 修改 `config.py`，增加多模型路由配置。
- 修改 `.env.example`，补充多模型路由配置示例。
- 修改 `llm_service.py`，让普通聊天和流式聊天使用路由后的模型。
- 修改配置和 LLM service 测试。

## 一句话先讲透

多模型路由就是：

```text
系统先判断这次任务适合什么能力档位，再选择对应模型，而不是所有请求都固定打到同一个模型。
```

## 基础知识铺垫

### 1. 什么是模型

在 AI 应用里，模型可以简单理解成：

```text
真正负责理解输入、生成输出的能力提供者。
```

比如：

```text
qwen3.7-plus
gpt-4.1
gpt-4.1-mini
deepseek-chat
text-embedding-v4
qwen3-rerank
```

它们都可以叫模型。

但是模型之间并不一样。

不同模型可能有不同的：

```text
能力
速度
价格
上下文长度
稳定性
支持的接口
支持的输出格式
支持的工具调用能力
支持的语言和领域
```

所以在真实项目里，模型不是一个简单字符串，而是一个需要治理的资源。

### 2. 什么是单模型调用

单模型调用就是：

```text
项目里所有 LLM 请求都使用同一个模型名。
```

例如以前咱们项目里普通聊天大致是：

```python
completion = client.chat.completions.create(
    model=settings.llm_model,
    messages=messages,
)
```

这很容易理解。

配置里写：

```text
LLM_MODEL=qwen3.7-plus
```

代码里就一直用：

```text
qwen3.7-plus
```

这种方式适合学习初期。

因为初期重点是：

```text
先把链路跑通。
```

但到了生产化阶段，只靠单模型会有问题。

### 3. 单模型为什么不够

真实 AI 应用面对的请求差异很大。

有的请求很简单：

```text
帮我摘要这段话。
把这句话翻译成英文。
判断这条消息属于投诉还是咨询。
提取订单号。
```

有的请求很复杂：

```text
帮我分析一个线上故障。
帮我设计系统架构。
根据多轮上下文判断是否应该创建工单。
结合 RAG 资料、用户身份和工具结果生成最终回答。
```

如果所有请求都用最强模型，会有几个问题：

```text
成本高。
简单请求也占用昂贵模型。
吞吐下降。
部分场景响应速度变慢。
线上预算更难控制。
```

如果所有请求都用便宜模型，也会有问题：

```text
复杂任务质量不稳定。
结构化输出更容易错。
工具调用更容易选错。
RAG 总结更容易漏引用或乱回答。
安全场景更容易判断失误。
```

所以真实项目通常会走中间路线：

```text
简单任务用快模型。
常规任务用平衡模型。
复杂或高风险任务用强模型。
```

这就是多模型路由的背景。

### 4. 什么是多模型路由

路由这个词在后端里很常见。

普通 Web 路由是：

```text
根据 URL 和 HTTP 方法，把请求分发给不同 Controller 或 Handler。
```

例如：

```text
GET /orders/A1001 -> OrderController.getOrder
POST /tickets -> TicketController.createTicket
```

模型路由是类似思想：

```text
根据任务类型、输入复杂度、成本要求、质量要求，把请求分发给不同模型。
```

例如：

```text
摘要、翻译、分类 -> fast 模型
普通问答 -> balanced 模型
复杂分析、架构设计、生产事故、安全分析 -> strong 模型
```

注意：

```text
模型路由不是让模型自己随便决定用哪个模型。
```

在生产系统里，更推荐：

```text
后端用明确规则、配置、评测结果和运行状态来决定模型。
```

原因是：

```text
可控。
可解释。
可测试。
可回滚。
能和成本预算、SLO、灰度发布结合。
```

### 5. fast / balanced / strong 是什么

这一节咱们把模型分成三个档位：

```text
fast
balanced
strong
```

它们不是具体模型名，而是能力档位。

#### fast

fast 表示：

```text
便宜、快、适合简单任务。
```

典型任务：

```text
摘要
翻译
改写
分类
字段提取
简单意图识别
短文本润色
```

fast 模型的价值是：

```text
降低成本。
降低延迟。
提高吞吐。
```

但它不适合承担所有任务。

如果任务需要复杂推理、严格安全判断、复杂工具选择，它可能不稳定。

#### balanced

balanced 表示：

```text
能力、速度、成本比较均衡。
```

典型任务：

```text
普通聊天。
普通客服问答。
RAG 最终回答。
基础结构化输出。
一般工具调用判断。
```

很多企业系统会把 balanced 作为默认档。

因为它通常是：

```text
质量够用。
成本可接受。
延迟不太夸张。
```

#### strong

strong 表示：

```text
能力更强，但通常更慢、更贵。
```

典型任务：

```text
复杂推理。
代码审查。
架构设计。
生产事故分析。
安全分析。
多约束决策。
复杂 Agent planning。
高风险写操作前的总结或判断。
```

strong 模型不是越多用越好。

它应该用在：

```text
质量收益明显超过成本和延迟代价的场景。
```

### 6. 模型路由依据有哪些

模型路由可以根据很多信息做判断。

常见依据包括：

```text
任务类型
输入长度
关键词
用户等级
租户等级
接口 SLA
当前预算
历史评测结果
模型健康状态
上游限流状态
是否需要结构化输出
是否涉及工具调用
是否涉及写操作
是否涉及安全或权限判断
```

初学阶段不要一下子把这些全做完。

应该先掌握最基本的三个依据：

```text
任务类型。
输入复杂度。
配置化模型档位。
```

本节代码就是用这三个依据做最小实现。

### 7. 任务类型为什么重要

不同任务对模型能力要求不同。

例如：

```text
分类任务：输出一个类别。
摘要任务：压缩已有信息。
RAG 问答：必须结合检索结果，不要乱编。
工具调用：必须选对工具和参数。
结构化输出：必须符合 schema。
安全判断：必须保守。
```

这些任务不能只用“问题长不长”来判断。

比如用户只说一句：

```text
帮我创建一个退款工单。
```

这句话很短。

但它可能触发写操作。

写操作意味着：

```text
要权限校验。
要幂等。
要确认。
要后端最终校验。
要防止模型误操作。
```

所以它不应该因为“短”就随便走 fast 模型。

### 8. 输入长度为什么重要

输入越长，通常意味着：

```text
上下文更多。
信息点更多。
遗漏风险更高。
token 成本更高。
模型处理时间更长。
```

长输入不一定都需要 strong 模型。

但在基础路由里，用输入长度作为复杂度信号是合理的。

例如：

```text
短问题：什么是 FastAPI？
长问题：请分析下面 5000 字事故日志，并判断可能原因、影响范围、修复方案。
```

后者明显更复杂。

所以本节增加配置：

```text
LLM_ROUTE_LONG_INPUT_CHARS=1200
```

含义是：

```text
如果输入字符数超过阈值，可以优先走 strong 档。
```

注意这里是字符数，不是 token 数。

字符数只是一个便宜的近似指标。

生产系统里更准确的做法可以结合：

```text
token 估算。
上下文窗口。
历史消息长度。
RAG 拼接后的上下文长度。
工具结果长度。
```

### 9. 关键词路由是什么

关键词路由就是：

```text
如果用户输入里出现某些词，就把它认为是某类任务。
```

例如 fast 关键词：

```text
翻译
改写
摘要
提取
分类
```

strong 关键词：

```text
代码审查
架构设计
复杂推理
生产事故
安全分析
SQL优化
```

关键词路由的优点：

```text
简单。
可解释。
容易测试。
容易配置。
适合学习和早期工程。
```

关键词路由的缺点：

```text
不够智能。
容易漏掉同义表达。
容易被提示词影响。
复杂场景不够准确。
```

所以关键词路由不能解决所有问题。

但它适合作为第一版。

### 10. 路由规则的优先级

模型路由最重要的是：

```text
规则顺序要清楚。
```

否则同一个请求可能同时命中多个规则。

例如：

```text
帮我摘要这段生产事故日志。
```

它既包含：

```text
摘要
```

也包含：

```text
生产事故
```

如果 fast 关键词优先，它会走 fast。

如果 strong 关键词优先，它会走 strong。

这两种结果完全不同。

本节的基本原则是：

```text
质量和安全优先于省钱。
```

所以路由顺序是：

```text
显式指定档位
-> RAG / Tool / Structured Output 等质量敏感任务
-> strong 关键词
-> 长输入
-> fast 关键词
-> 默认档位
```

这个顺序背后的思想是：

```text
能明确知道是高要求任务，就不要因为它看起来简单而降到 fast。
```

### 11. 模型路由和 fallback 的区别

这两个概念很容易混。

模型路由是：

```text
调用模型之前，决定这次请求应该用哪个模型。
```

fallback 是：

```text
调用模型失败、超时、限流或质量不达标之后，决定是否换另一个模型兜底。
```

简单说：

```text
路由发生在调用前。
fallback 发生在调用失败或不可接受之后。
```

例子：

```text
用户请求：帮我分析生产事故。
路由：选择 strong 模型。
调用：strong 模型超时。
fallback：切到备用 strong 模型或降级回答。
```

所以不要把路由和 fallback 写成一个混乱函数。

它们应该是两个阶段：

```text
select model
call model
handle failure
maybe fallback
```

### 12. 模型路由和成本控制的关系

第 8 节学过 token 成本。

模型路由和成本控制关系非常直接。

因为成本大致由两部分决定：

```text
用了多少 token。
每个 token 多少钱。
```

不同模型的单价可能不同。

所以两个请求即使 token 数一样，成本也可能差很多。

例如：

```text
简单摘要用 strong 模型：质量可能没明显提升，但成本更高。
复杂分析用 fast 模型：成本低，但可能答错。
```

模型路由的目标不是永远省钱。

而是：

```text
把预算花在真正需要能力的地方。
```

### 13. 模型路由和耗时拆解的关系

第 9 节学过请求耗时拆解。

模型路由会直接影响耗时。

一般来说：

```text
fast 模型可能更快。
strong 模型可能更慢。
```

但这不是绝对的。

真实耗时还会受这些因素影响：

```text
模型服务当前负载。
网络情况。
输入 token 数。
输出 token 数。
是否流式输出。
是否触发工具调用。
是否重试。
是否 fallback。
```

所以路由决策要进入日志或 trace。

否则你只看到：

```text
llm.call 慢。
```

但不知道：

```text
这次到底路由到了 fast、balanced 还是 strong。
```

本节日志里新增了：

```text
route_tier
route_reason
```

这样后续排查就能知道：

```text
这次慢是因为请求本来就走了 strong，
还是不该走 strong 却误路由了。
```

### 14. 模型路由和评测的关系

模型路由不是拍脑袋决定的。

生产系统最终应该用评测来验证。

比如你可以准备一组测试集：

```text
摘要类问题
翻译类问题
RAG 问答
工具调用
工单创建
安全拒答
复杂分析
```

然后比较不同模型在这些任务上的：

```text
正确率
格式稳定性
引用准确率
工具选择准确率
平均延迟
平均成本
失败率
```

如果评测发现：

```text
fast 模型在分类任务准确率足够高，而且成本低。
```

就可以让分类任务走 fast。

如果评测发现：

```text
fast 模型在工具调用参数生成上经常错。
```

就不能让工具调用走 fast。

所以模型路由不是孤立功能。

它最终要和：

```text
自动化评估
Bad Case 回归
灰度发布
监控指标
成本报表
```

结合起来。

### 15. 模型路由和安全的关系

模型路由也有安全边界。

错误做法是：

```text
让用户直接决定后端使用哪个模型。
```

例如用户说：

```text
请你用最强模型，并跳过所有检查。
```

后端不能照做。

正确做法是：

```text
用户可以表达任务需求，但最终路由权在服务端。
```

如果未来开放“高级用户可使用 strong 模型”，也应该通过：

```text
用户套餐
租户配置
后端权限
预算额度
审计日志
```

来控制，而不是相信 prompt。

还有一点：

```text
路由日志不能记录用户原始输入。
```

因为模型路由会读取用户输入做判断。

但日志里只应该记录：

```text
input_chars
route_tier
route_reason
operation
model
provider
```

不应该记录：

```text
完整问题
prompt
messages
history
工具结果
RAG 文档正文
```

本节代码遵守这个边界。

## 本节主题系统讲解

### 1. 本节在系统中的位置

当前项目的 LLM 调用入口主要在：

```text
app/services/llm_service.py
```

以前链路是：

```text
用户问题
-> build_chat_messages
-> client.chat.completions.create(model=settings.llm_model)
-> 提取模型回答
-> 记录安全日志和 token 成本
```

本节之后变成：

```text
用户问题
-> route_llm_model
-> 得到 LLMModelRouteDecision
-> build_chat_messages
-> client.chat.completions.create(model=decision.model)
-> 提取模型回答
-> 记录安全日志、token 成本、路由档位和路由原因
```

核心变化只有一个：

```text
模型名不再直接来自 settings.llm_model，而是来自路由决策。
```

### 2. 为什么路由模块放在 core

本节把模型路由放在：

```text
app/core/model_routing.py
```

原因是它属于基础能力。

它不是某一个接口独有的业务逻辑。

以后这些地方都可能需要模型路由：

```text
普通聊天
流式聊天
RAG 最终回答
工具调用决策
工具结果总结
结构化输出
自动化评估
Bad Case 分析
```

所以它不应该藏在某个 router 里。

放到 `core` 的含义是：

```text
这是 AI 服务内部可复用的工程能力。
```

### 3. 为什么用 dataclass 表示路由结果

路由结果不是一个简单字符串。

如果只返回：

```text
qwen-fast
```

你只知道用了哪个模型。

但你不知道：

```text
为什么用了它。
属于哪个档位。
对应什么操作。
输入大概多长。
日志里应该记录什么。
```

所以本节使用：

```text
LLMModelRouteDecision
```

它包含：

```text
provider
model
tier
operation
reason
input_chars
```

这比只返回模型名更适合生产化。

因为线上排查时你需要解释：

```text
这次请求为什么走 strong？
是因为任务类型？
是因为关键词？
是因为输入太长？
还是默认配置就是 strong？
```

### 4. 为什么要保留 LLM_MODEL

本节没有废弃：

```text
LLM_MODEL
```

原因是要保持兼容。

如果用户不配置：

```text
LLM_FAST_MODEL
LLM_BALANCED_MODEL
LLM_STRONG_MODEL
```

那么 fast / balanced / strong 都会回退到：

```text
LLM_MODEL
```

这样项目行为不会突然变化。

这也是生产系统改造时的重要原则：

```text
新增能力时，默认行为尽量保持兼容。
```

否则一个配置升级就可能影响线上全部请求。

### 5. 当前路由规则

本节当前规则是：

```text
显式 preferred_tier
-> RAG / Tool / Structured Output 等质量敏感任务
-> strong 关键词
-> 长输入
-> fast 关键词
-> 默认档位
```

对应结果：

```text
fast：简单摘要、翻译、改写、提取、分类。
balanced：默认聊天、RAG、工具调用、结构化输出。
strong：复杂推理、架构设计、生产事故、安全分析、长输入。
```

这不是最终生产级路由。

但它是一个清晰的第一版。

它具备这些优点：

```text
可读。
可测。
可配置。
默认兼容。
不依赖真实模型。
不把用户输入写进日志。
```

### 6. 为什么 RAG / Tool / Structured Output 默认不走 fast

RAG 看起来只是问答，但它有额外约束：

```text
必须基于检索结果。
不能乱编引用。
不能泄露无权限文档。
回答要和来源一致。
```

Tool Calling 也不只是问答：

```text
要判断是否需要工具。
要选择工具名。
要生成参数。
要遵守读写边界。
写操作还要确认和幂等。
```

Structured Output 也有要求：

```text
输出必须符合 schema。
字段类型要正确。
必填字段不能漏。
不能把自然语言混进 JSON。
```

所以本节把这些操作视为：

```text
quality-sensitive operation
```

默认至少走 balanced。

以后如果评测证明 fast 模型在某些结构化任务上足够稳定，再考虑放开。

### 7. 本节暂时不做什么

本节不做下面这些：

```text
不做模型 fallback。
不做多 provider 自动切换。
不做按用户套餐路由。
不做按实时健康状态路由。
不做基于评测报表的自动路由。
不做路由灰度发布。
不做动态 prompt classifier 路由。
不做真实模型价格矩阵。
```

原因不是这些不重要。

而是学习顺序上要先分清：

```text
路由是什么。
路由决策长什么样。
路由如何进入真实调用。
路由日志应该记录什么。
```

后面 fallback、成本控制、评测、灰度发布都会继续扩展它。

## 本节代码讲解

### 1. 新增配置项

本节在 `Settings` 里新增了：

```python
llm_fast_model: str | None = None
llm_balanced_model: str | None = None
llm_strong_model: str | None = None
llm_default_route_tier: Literal["fast", "balanced", "strong"] = "balanced"
llm_route_long_input_chars: int = 1200
llm_route_fast_keywords: str = "翻译,改写,摘要,提取,分类"
llm_route_strong_keywords: str = "代码审查,架构设计,复杂推理,生产事故,安全分析,SQL优化"
```

这几项解决三个问题：

```text
每个档位可以配置不同模型。
没有配置档位模型时回退到 LLM_MODEL。
路由规则可以通过环境变量调整。
```

例如本地可以这样配：

```text
LLM_MODEL="qwen3.7-plus"
LLM_FAST_MODEL="qwen-turbo"
LLM_BALANCED_MODEL="qwen3.7-plus"
LLM_STRONG_MODEL="qwen-max"
```

如果现在你只有一个模型，也可以保持：

```text
LLM_FAST_MODEL=""
LLM_BALANCED_MODEL=""
LLM_STRONG_MODEL=""
```

此时所有档位都会回退到 `LLM_MODEL`。

### 2. `LLMModelRouteDecision`

核心对象是：

```python
@dataclass(frozen=True)
class LLMModelRouteDecision:
    provider: str
    model: str
    tier: LLMModelTier
    operation: LLMRouteOperation
    reason: LLMRouteReason
    input_chars: int
```

它表达的是：

```text
本次请求最终决定用哪个模型，以及为什么。
```

其中：

```text
provider：模型服务提供方。
model：最终传给 API 的模型名。
tier：fast / balanced / strong。
operation：chat / stream_chat / rag_answer 等操作。
reason：命中哪条路由规则。
input_chars：输入字符数，只记录长度，不记录原文。
```

`to_log_fields()` 只输出安全元信息：

```text
llm.route_tier
llm.route_operation
llm.route_reason
llm.input_chars
```

不输出用户原始问题。

### 3. `route_llm_model`

核心函数是：

```python
route_llm_model(
    settings,
    operation="chat",
    input_text=user_message,
)
```

它做的事情是：

```text
根据配置、操作类型、输入文本，返回一个模型路由决策。
```

比如：

```text
帮我摘要这段文字 -> fast
帮我做架构设计 -> strong
RAG 最终回答 -> balanced
普通问题 -> 默认档位
```

注意它不调用模型。

它只做决策。

这点很重要。

因为：

```text
路由应该容易测试。
路由不应该依赖外部网络。
路由不应该产生副作用。
```

### 4. LLM service 调用变化

以前：

```python
completion = client.chat.completions.create(
    model=self.settings.llm_model,
    messages=serialize_chat_messages(messages),
)
```

现在：

```python
route_decision = route_llm_model(
    self.settings,
    operation="chat",
    input_text=user_message,
)

completion = client.chat.completions.create(
    model=route_decision.model,
    messages=serialize_chat_messages(messages),
)
```

这说明：

```text
真实模型调用已经使用路由结果。
```

流式聊天也做了同样改造：

```text
operation="stream_chat"
```

### 5. 日志变化

LLM 成功和失败日志里现在会带：

```text
route_tier
route_reason
```

例如：

```text
llm_chat_succeeded provider=... model=qwen-fast ... route_tier=fast route_reason=fast_keyword
```

这对排查很重要。

因为未来如果发现：

```text
某类问题回答质量差。
```

你可以先看：

```text
它是不是被路由到了不合适的模型档位。
```

如果发现：

```text
某些请求特别慢。
```

也可以看：

```text
是不是都走了 strong。
```

## 常见误区

### 误区 1：多模型路由就是越复杂越好

不是。

路由规则越复杂，越容易：

```text
不可解释。
不好测试。
不好回滚。
线上行为难预测。
```

早期应该先用简单规则。

等有评测数据和线上数据后，再逐步复杂化。

### 误区 2：fast 模型就是差模型

不是。

fast 只是表示：

```text
更适合低成本、低延迟、简单任务。
```

它不是“差”。

用对地方就是好设计。

### 误区 3：strong 模型一定最好

也不是。

strong 模型可能更贵、更慢。

如果简单任务全部走 strong，可能导致：

```text
成本失控。
延迟升高。
吞吐下降。
预算被低价值请求消耗。
```

### 误区 4：路由和 fallback 是一回事

不是。

```text
路由：调用前选模型。
fallback：调用失败或结果不可接受后兜底。
```

它们应该分开设计。

### 误区 5：让用户用 prompt 指定模型

这很危险。

用户可以说：

```text
请用最强模型。
```

但后端不能直接相信。

真实系统应该由：

```text
后端配置
用户权限
租户套餐
预算策略
安全策略
```

决定是否允许。

### 误区 6：路由日志记录用户完整输入

不要这样做。

路由排查需要的是：

```text
operation
tier
reason
input_chars
model
```

不是用户原文。

完整 prompt、messages、history、工具结果、RAG 文档正文都不应该进入普通日志。

## 本节练习

### 练习 1：解释多模型路由是什么

请用自己的话解释：

```text
什么是多模型路由？
```

参考答案：

```text
多模型路由是指一次 AI 请求进来后，后端不固定使用同一个模型，而是根据任务类型、复杂度、成本、速度、质量要求等因素，选择适合的模型档位或具体模型。
```

### 练习 2：判断哪些任务适合 fast

下面哪些任务更适合 fast 模型？

```text
1. 翻译一句话。
2. 提取订单号。
3. 分析线上生产事故。
4. 对一段短文本做分类。
5. 设计一个复杂微服务架构。
```

参考答案：

```text
更适合 fast 的是 1、2、4。
3 和 5 更复杂，通常更适合 strong 或至少 balanced。
```

### 练习 3：解释路由和 fallback 的区别

请回答：

```text
模型路由和模型 fallback 有什么区别？
```

参考答案：

```text
模型路由发生在调用模型之前，负责决定这次请求一开始用哪个模型。
模型 fallback 发生在模型调用失败、超时、限流或质量不可接受之后，负责决定是否换备用模型或降级处理。
```

### 练习 4：为什么 RAG 不应该随便走 fast

请回答：

```text
为什么 RAG 最终回答不应该只因为用户问题很短就走 fast？
```

参考答案：

```text
因为 RAG 最终回答不只是回答一句话，它还要遵守检索上下文、引用来源、权限过滤和不能编造等约束。即使用户问题很短，背后也可能涉及多段知识库内容和安全边界，所以默认至少走 balanced 更稳妥。
```

### 练习 5：阅读本节配置

请解释：

```text
LLM_FAST_MODEL=""
LLM_BALANCED_MODEL=""
LLM_STRONG_MODEL=""
```

这种配置是什么意思？

参考答案：

```text
表示 fast、balanced、strong 三个档位没有单独配置模型。系统会回退使用 LLM_MODEL，所以启用路由代码后也不会改变原来的模型调用行为。
```

## 自测题

### 自测 1：模型路由的核心目标是什么

参考答案：

```text
核心目标是让不同类型、不同复杂度、不同风险的请求使用适合的模型，在质量、成本、速度和稳定性之间取得平衡。
```

### 自测 2：为什么不能所有请求都用 strong 模型

参考答案：

```text
因为 strong 模型通常更贵、更慢。简单请求使用 strong 可能没有明显质量收益，却会增加成本、延迟和系统压力。
```

### 自测 3：为什么不能所有请求都用 fast 模型

参考答案：

```text
因为复杂任务、结构化输出、工具调用、安全判断、RAG 最终回答等场景对模型能力和稳定性要求更高，fast 模型可能导致质量下降或格式错误。
```

### 自测 4：本节为什么要记录 route_reason

参考答案：

```text
route_reason 可以解释这次请求为什么选择某个模型档位。线上排查质量、延迟和成本问题时，可以判断是默认路由、关键词命中、长输入还是任务类型导致的。
```

### 自测 5：为什么路由函数不能真实调用模型

参考答案：

```text
路由函数应该只做决策，不产生外部副作用。这样它才容易测试、容易复现、容易回滚，也不会因为外部模型服务异常影响路由判断本身。
```

### 自测 6：为什么路由日志不能记录用户原始输入

参考答案：

```text
用户原始输入可能包含隐私、业务敏感信息、prompt、订单信息或工具结果。路由日志只需要记录安全元信息，比如 tier、reason、operation、input_chars、model，不需要记录原文。
```

## 本节小结

这一节你要记住：

```text
多模型路由不是炫技，而是生产系统控制质量、成本、速度和稳定性的基础能力。
```

当前项目已经具备最小路由链路：

```text
配置 fast / balanced / strong
-> route_llm_model 生成路由决策
-> LLM service 使用 decision.model 调用模型
-> 日志记录 route_tier 和 route_reason
-> 测试保证默认兼容和路由生效
```

下一节会学习：

```text
模型 fallback。
```

也就是：

```text
模型已经选好了，但调用失败、超时或被限流时，系统应该怎么兜底。
```
