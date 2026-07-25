# 阶段 6 第 17 节：prompt 版本管理

本节目标：把智能工单 Agent 里的真实 LLM prompt 从“普通字符串”推进到“可命名、可版本化、可追踪、可测试”的工程资产。

前面几节我们已经完成：

```text
第 13 节：真实 LLM 意图识别节点
第 14 节：真实 LLM 工单字段提取节点
第 15 节：Pydantic 校验模型输出
第 16 节：fake LLM 和真实 LLM 双模式
```

现在真实模型已经可以接入，模型输出也有 Pydantic 校验，运行模式也能区分 `rule_based`、`fake_llm`、`real_llm`。

接下来就会遇到一个真实工程问题：

```text
prompt 改了以后，怎么知道当前用的是哪个版本？
```

如果不管理 prompt 版本，以后排查问题会很痛苦。

例如：

```text
昨天意图识别准确率 90%
今天意图识别准确率 78%

到底是：
1. 模型版本变了？
2. prompt 改了？
3. 测试集变了？
4. schema 变了？
5. 业务规则变了？
6. 用户输入分布变了？
```

如果日志、测试和 eval 报告里都没有 prompt version，就很难回答。

所以本节要补的是：

```text
让每次真实模型调用都能知道自己用了哪个 prompt。
```

---

## 一、本节在主线里的位置

阶段 6 的目标是把当前 RAG + 智能工单 Agent v1 推向真实工程系统。

当前阶段可以这样理解：

```text
第 1-11 节：先建立 eval 能力
第 12 节：理解 evaluator 类型
第 13-14 节：把真实 LLM 接入 Agent 节点
第 15 节：用 Pydantic 接住模型输出
第 16 节：区分规则、fake LLM、真实 LLM 三种模式
第 17 节：管理真实 LLM 节点使用的 prompt 版本
```

为什么第 17 节才讲 prompt 版本管理？

因为如果还没有真实 LLM 节点，prompt 版本管理没有落点。

如果还没有 Pydantic 输出校验，prompt 版本管理会和输出结构混在一起。

如果还没有 fake/real 双模式，prompt 版本管理会很容易误导自动测试去真实调模型。

所以顺序是合理的：

```text
先能接入真实模型
再能校验输出
再能控制运行模式
最后再让 prompt 可管理
```

---

## 二、本节学习目标

学完本节，你要能解释清楚：

1. prompt 为什么不是随便写在代码里的普通字符串。
2. 什么是 prompt 版本管理。
3. prompt name 和 prompt version 有什么区别。
4. prompt version 为什么要进日志。
5. prompt version 为什么要和 eval 结果关联。
6. prompt、model、schema、temperature 之间是什么关系。
7. 为什么只记录 prompt 内容不够，还要记录版本。
8. 为什么只记录版本也不够，未来还可能记录 hash。
9. 为什么日志里一般记录 prompt name/version，而不记录完整 prompt 内容。
10. 当前项目为什么先做简单 `v1`，不直接上复杂 prompt 平台。
11. `TicketAgentPromptSpec` 负责什么。
12. `TICKET_AGENT_PROMPTS` 这个注册表负责什么。
13. 为什么 message builder 要允许传入 `prompt_spec`。
14. 为什么 LLM classifier/extractor 要保存 `self.prompt_spec`。
15. 为什么工厂函数要透传 prompt spec。
16. 本节新增测试分别保护了哪些边界。

---

## 三、本节暂时不学什么

本节只做 prompt 版本管理的第一层工程基础。

暂时不展开：

- 不重写 prompt 内容。
- 不做 prompt v2。
- 不做 A/B 测试。
- 不做 prompt 自动优化。
- 不做 prompt 在线实验平台。
- 不接 LangSmith Prompt Hub。
- 不把 prompt 拆到数据库或远程配置中心。
- 不做 prompt 模板变量系统。
- 不做多语言 prompt 管理。
- 不做 prompt hash 强校验。
- 不把 prompt 版本写进真实 provider 的 `metadata` 参数。

为什么先不做这些？

因为你现在最需要先掌握基础：

```text
prompt 是什么
为什么要版本化
版本信息放在哪里
日志和测试怎么保护它
以后 eval 怎么用它
```

基础没懂，直接上平台，很容易变成“工具会用，但不知道为什么这么设计”。

---

## 四、基础知识铺垫

### 1. prompt 到底是什么

prompt 可以先理解为：

```text
你交给模型的任务说明、约束规则和上下文组织方式。
```

在聊天模型里，prompt 通常不是一个单独字符串，而是一组 messages：

```text
system message
user message
assistant message
tool message
```

当前项目里，真实 LLM 节点主要使用两类 prompt：

```text
意图识别 prompt
-> 告诉模型把用户消息分类成固定 intent

字段提取 prompt
-> 告诉模型从 Agent state 和用户消息中提取工单字段
```

prompt 的作用不是“让模型随便回答得好一点”。

它在工程里承担的是任务合同：

```text
你应该做什么
你不应该做什么
你必须输出什么结构
你可以选择哪些枚举值
你遇到不确定时应该怎么处理
```

所以 prompt 一旦进入业务系统，就不再只是自然语言。

它是业务逻辑的一部分。

### 2. prompt 为什么不是普通字符串

普通字符串改了，一般影响很小。

比如日志提示语：

```python
"ticket created"
```

改成：

```python
"ticket has been created"
```

多数情况下只是显示文字变化。

但 prompt 改了，可能影响模型行为。

例如把这句：

```text
ticket_request 表示用户明确要投诉、要求人工处理、创建工单或处理具体售后问题。
```

改成：

```text
ticket_request 表示所有售后相关问题。
```

后果可能是：

```text
原本应该走 policy_question 的退款规则咨询
被模型改判成 ticket_request
然后进入工单流程
```

这不是文案变化。

这是业务路径变化。

所以 prompt 更接近：

```text
代码逻辑
配置规则
模型任务合同
评测对象
```

而不是普通说明文字。

### 3. prompt 版本管理是什么

prompt 版本管理就是：

```text
给每一份 prompt 一个稳定身份，并在调用、日志、测试、评测里记录这个身份。
```

最基础的版本信息包括：

```text
prompt name
prompt version
prompt content
prompt purpose/description
```

当前项目新增的结构就是：

```python
TicketAgentPromptSpec(
    name="ticket_intent_classification",
    version="ticket_intent_classification:v1",
    system_prompt=...,
    description=...,
)
```

你可以把它理解成 prompt 的身份证。

### 4. prompt name 和 prompt version 的区别

这两个概念要分清。

`prompt name` 表示这个 prompt 是干什么的。

例如：

```text
ticket_intent_classification
ticket_field_extraction
```

`prompt version` 表示这个 prompt 当前是哪一版。

例如：

```text
ticket_intent_classification:v1
ticket_field_extraction:v1
```

区别是：

```text
name 是任务身份。
version 是任务说明的具体版本。
```

以后如果意图识别 prompt 改了：

```text
ticket_intent_classification:v1
-> ticket_intent_classification:v2
```

name 不变，因为它还是意图识别 prompt。

version 变化，因为任务说明内容变了。

### 5. prompt version 和 Git commit 的区别

你可能会问：

```text
代码不是已经有 Git commit 了吗？为什么还要 prompt version？
```

Git commit 能回答：

```text
这次代码整体是什么状态。
```

prompt version 能回答：

```text
这次模型调用具体用了哪个 prompt。
```

两者不是替代关系。

真实排查时，经常需要同时看：

```text
commit_sha
prompt_version
model
schema_version
eval_dataset_version
```

例如同一个 commit 里可能有两个 prompt：

```text
ticket_intent_classification:v1
ticket_field_extraction:v1
```

后面只改字段提取 prompt：

```text
ticket_intent_classification:v1
ticket_field_extraction:v2
```

这时只看 commit 不够直观。

prompt version 能更直接地定位模型行为变化。

### 6. prompt 和 model 的关系

模型输出不是只由 prompt 决定。

一般由这些因素共同决定：

```text
user input
system prompt
developer prompt
history messages
retrieved context
tool results
model name
model provider
temperature
max_output_tokens
response_format
schema
provider compatibility
```

所以评估一次 LLM 节点时，至少要能知道：

```text
用了哪个 model
用了哪个 prompt version
用了哪个 schema
```

本项目现在已经在日志里记录：

```text
provider
model
prompt_name
prompt_version
token usage
elapsed_ms
```

这就是一个可观测基础。

### 7. prompt 和 schema 的关系

当前真实 LLM 节点不是让模型自由回答。

它要求模型返回 JSON。

并且 JSON 要被 Pydantic 校验。

所以 prompt 和 schema 是配套关系。

例如 prompt 里说：

```text
intent 只能是 policy_question、order_query、ticket_request、smalltalk、unsupported、unclear。
```

Pydantic 里也用 `Literal` 约束了这些值。

这就是两层边界：

```text
prompt
-> 先告诉模型应该怎么输出

Pydantic schema
-> 后端再检查模型是否真的按要求输出
```

如果未来 prompt v2 改了输出规则，但 Pydantic schema 没改，就可能产生冲突。

例如 prompt v2 告诉模型可以输出：

```text
after_sale
```

但 Pydantic 仍然只允许：

```text
refund
logistics
complaint
policy_gap
unknown
```

结果就是模型输出会被后端拒绝。

所以 prompt 版本管理不能只盯着 prompt。

它还要和 schema 变更一起考虑。

### 8. prompt 和 eval 的关系

prompt 改了以后，最重要的问题不是：

```text
我感觉新 prompt 写得更清楚。
```

而是：

```text
固定评测集上，新 prompt 的结果有没有变好？
有没有把旧能力改坏？
有没有产生新的坏例？
```

这就是为什么阶段 6 前面先做 eval。

如果没有 eval，prompt 修改很容易靠感觉判断。

例如你改了一句 prompt，然后手动试了 3 个例子都不错。

但固定评测集里可能有 30 个例子，其中 5 个旧能力退化。

所以成熟一点的流程应该是：

```text
改 prompt
-> 更新 prompt version
-> 跑目标 eval
-> 生成报告
-> 看 pass rate 和 bad cases
-> 决定是否保留这个 prompt 版本
```

本节先做到第一步：

```text
让 prompt 有版本，且调用日志能记录版本。
```

后面才更适合做 prompt 对比 eval。

### 9. 为什么日志里记录 prompt version

日志是排查线上问题的入口。

假设用户反馈：

```text
我只是问退款规则，系统却让我创建工单。
```

你需要查这次调用：

```text
trace_id 是什么？
intent 是什么？
用了哪个 model？
用了哪个 prompt version？
模型耗时多少？
token 用量多少？
有没有触发 Pydantic 校验失败？
```

如果日志里没有 prompt version，你只能猜：

```text
是不是最近 prompt 改过？
是不是它用了旧版本？
是不是不同机器版本不一致？
```

记录 prompt version 后，问题会清楚很多：

```text
trace_id=...
model=qwen-test
prompt_name=ticket_intent_classification
prompt_version=ticket_intent_classification:v1
intent=ticket_request
```

这就能把一次模型行为和具体 prompt 版本关联起来。

### 10. 为什么日志里不直接记录完整 prompt

完整 prompt 有时很长。

直接写进日志会带来问题：

- 日志体积变大。
- 日志成本上升。
- 排查时噪音变多。
- 如果 prompt 里未来包含动态上下文，可能泄露敏感信息。
- 日志系统不适合保存大段提示词内容。

所以更常见的做法是：

```text
日志记录 prompt_name 和 prompt_version。
完整 prompt 内容保存在代码仓库、配置仓库或 prompt 管理平台。
```

这样排查时可以通过版本回到源码里看内容。

### 11. version 和 hash 的区别

本节先做版本号：

```text
ticket_intent_classification:v1
```

未来还可能做 hash：

```text
sha256(prompt_content)
```

它们解决的问题不同。

版本号适合人读：

```text
v1
v2
v3
```

hash 适合机器校验：

```text
这段 prompt 内容是否被偷偷改过？
同一个 version 对应的内容是否一致？
```

当前学习阶段先做版本号。

因为你现在要先建立：

```text
prompt 是可命名、可版本化的工程资产
```

hash 属于更严格的生产治理，可以后面再补。

### 12. 为什么不直接上 prompt 管理平台

真实公司里可能会有：

- LangSmith Prompt Hub。
- 内部 prompt 管理平台。
- 配置中心。
- 实验平台。
- A/B 测试系统。

但现在不应该一开始就依赖这些平台。

原因是：

```text
你还在学习基础工程思想。
```

如果不理解 name、version、log、eval 的关系，直接上平台也只是会点按钮。

本节用本地代码实现最小版本管理，是为了让你先看清底层逻辑：

```text
prompt spec
-> prompt registry
-> message builder
-> LLM component
-> logs
-> tests
```

以后换成平台，本质也是这些概念。

---

## 五、本节主题系统讲解

### 1. 本节之前项目的状态

第 16 节后，项目已经有两个真实 LLM 节点：

```text
LLMTicketIntentClassifier
LLMTicketFieldExtractor
```

它们分别使用两个 system prompt：

```text
TICKET_INTENT_CLASSIFICATION_SYSTEM_PROMPT
TICKET_FIELD_EXTRACTION_SYSTEM_PROMPT
```

问题是：

```text
这两个 prompt 只是字符串。
```

字符串本身没有：

- 名称。
- 版本。
- 用途说明。
- 注册入口。
- 日志字段。
- 测试保护。

所以如果未来改了 prompt 内容，很难从日志和 eval 里看出影响。

### 2. 本节之后项目的状态

本节给 prompt 增加了一层结构：

```text
TicketAgentPromptSpec
```

并创建两个 prompt spec：

```text
TICKET_INTENT_CLASSIFICATION_PROMPT
TICKET_FIELD_EXTRACTION_PROMPT
```

现在可以这样理解：

```text
system prompt 字符串
-> 被包装成 PromptSpec
-> 注册到 TICKET_AGENT_PROMPTS
-> message builder 从 PromptSpec 取 system_prompt
-> LLM classifier/extractor 持有 PromptSpec
-> 成功/失败日志记录 prompt_name 和 prompt_version
-> 测试保证版本信息没有丢
```

这条链路很重要。

如果只定义版本号，但调用和日志不用它，那只是表面版本管理。

本节做的是让版本进入真实调用链路。

### 3. 当前 prompt registry

当前注册表是：

```python
TICKET_AGENT_PROMPTS = {
    "ticket_intent_classification": TICKET_INTENT_CLASSIFICATION_PROMPT,
    "ticket_field_extraction": TICKET_FIELD_EXTRACTION_PROMPT,
}
```

它的作用是：

```text
集中保存当前项目里已经明确管理的 Agent prompt。
```

以后如果你想看当前项目有哪些 prompt，不需要全文搜索 `_SYSTEM_PROMPT`。

可以先看：

```text
TICKET_AGENT_PROMPTS
```

这就是注册表的意义。

### 4. 当前版本命名

本节使用：

```text
ticket_intent_classification:v1
ticket_field_extraction:v1
```

为什么不只写 `v1`？

因为日志里单独看到 `v1` 不够清楚。

例如：

```text
prompt_version=v1
```

你还要配合 `prompt_name` 才知道是哪一个 prompt。

写成：

```text
prompt_version=ticket_intent_classification:v1
```

可读性更强。

当然，日志里同时也记录了 `prompt_name`，所以这不是唯一可行方案。

当前这样设计是为了学习阶段更直观。

### 5. message builder 为什么支持 prompt_spec 参数

现在函数变成：

```python
build_ticket_intent_classification_messages(
    user_message,
    prompt_spec=TICKET_INTENT_CLASSIFICATION_PROMPT,
)
```

默认用 v1。

但测试或未来代码可以传入 v2：

```python
custom_prompt = TicketAgentPromptSpec(
    name="ticket_intent_classification",
    version="ticket_intent_classification:v2",
    system_prompt="...",
    description="...",
)
```

这样 message builder 不再硬绑某个全局字符串。

它变成：

```text
给我一个 prompt spec，我就用它构建 messages。
```

这就是面向扩展的设计。

### 6. LLM component 为什么保存 self.prompt_spec

`LLMTicketIntentClassifier` 现在会保存：

```python
self.prompt_spec = prompt_spec
```

原因是一次 LLM 调用需要在多个地方使用 prompt 信息：

```text
构造 messages
写成功日志
写失败日志
测试验证当前版本
```

如果只在 message builder 里用 prompt spec，日志里就拿不到版本。

如果只在日志里写版本，message builder 可能仍然用了旧 prompt。

所以把 prompt spec 放在 LLM component 里更清楚：

```text
这个 LLM component 使用哪一版 prompt，是它自身配置的一部分。
```

### 7. 工厂函数为什么要透传 prompt_spec

本节也让：

```text
create_llm_ticket_intent_classifier()
create_llm_ticket_field_extractor()
create_ticket_agent_model_dependencies()
build_ticket_agent_graph_for_model_mode()
```

都能透传 prompt spec。

这样以后如果要构建一个 v2 graph，可以这样做：

```python
graph = build_ticket_agent_graph_for_model_mode(
    mode="real_llm",
    intent_prompt_spec=intent_prompt_v2,
    field_prompt_spec=field_prompt_v1,
)
```

这个能力现在不一定马上使用，但它让后续 prompt 对比变得自然。

### 8. 当前日志字段

意图识别成功日志会包含：

```text
ticket_intent_llm_classification_succeeded
provider=...
model=...
prompt_name=ticket_intent_classification
prompt_version=ticket_intent_classification:v1
elapsed_ms=...
intent=...
prompt_tokens=...
completion_tokens=...
total_tokens=...
```

字段提取成功日志会包含：

```text
ticket_field_llm_extraction_succeeded
provider=...
model=...
prompt_name=ticket_field_extraction
prompt_version=ticket_field_extraction:v1
elapsed_ms=...
issue_type=...
has_order_id=...
urgency=...
need_human_review=...
prompt_tokens=...
completion_tokens=...
total_tokens=...
```

失败日志也会记录 prompt name/version。

这点重要。

因为有时问题不是成功调用后效果差，而是模型输出校验失败。

失败时同样要知道：

```text
是哪一个 prompt version 更容易导致失败。
```

### 9. prompt 版本进入 eval 的方式

本节还没有修改 eval 报告。

但现在已经具备基础。

后面可以把 prompt version 继续传进 eval result：

```text
case_id
expected_intent
actual_intent
passed
model
prompt_version
reason
```

这样可以比较：

```text
ticket_intent_classification:v1
vs
ticket_intent_classification:v2
```

如果 v2 提升了普通样本，但破坏了 P0 样本，就不能贸然上线。

这就是 prompt 版本管理和 eval 的衔接。

---

## 六、本节代码讲解

本节主要修改：

```text
projects/ai-service/app/agents/ticket_agent.py
projects/ai-service/tests/test_ticket_agent_prompt_versions.py
projects/ai-service/tests/test_ticket_agent_llm_intent.py
projects/ai-service/tests/test_ticket_agent_llm_fields.py
```

### 1. TicketAgentPromptName

新增：

```python
TicketAgentPromptName = Literal[
    "ticket_intent_classification",
    "ticket_field_extraction",
]
```

这表示当前 Agent prompt 名称只能是这两个。

为什么不用普通 `str`？

因为 prompt name 是项目内部的固定标识。

写成 `Literal` 可以减少拼错。

例如：

```text
ticket_intent_classify
ticket_fields_extraction
```

这些都不是当前合法名称。

### 2. TicketAgentPromptSpec

新增：

```python
@dataclass(frozen=True)
class TicketAgentPromptSpec:
    name: TicketAgentPromptName
    version: str
    system_prompt: str
    description: str
```

字段含义：

```text
name
-> prompt 负责的任务名称

version
-> 当前 prompt 的具体版本

system_prompt
-> 真实发给模型的 system message 内容

description
-> 给开发者看的用途说明
```

为什么用 `dataclass(frozen=True)`？

因为 prompt spec 应该像配置对象一样稳定。

`frozen=True` 表示创建后不应该随便改字段。

这能减少这种错误：

```python
prompt_spec.version = "v2"
```

如果要改版本，应该创建新的 prompt spec，而不是运行时偷偷改旧对象。

### 3. TICKET_INTENT_CLASSIFICATION_PROMPT

新增：

```python
TICKET_INTENT_CLASSIFICATION_PROMPT = TicketAgentPromptSpec(
    name="ticket_intent_classification",
    version="ticket_intent_classification:v1",
    system_prompt=TICKET_INTENT_CLASSIFICATION_SYSTEM_PROMPT,
    description="Classify a customer message into one allowed ticket agent intent.",
)
```

它把旧的 system prompt 字符串包装成一个有身份的对象。

注意：

```text
system_prompt 内容没有改。
```

本节不是调 prompt 效果，而是管理 prompt 身份。

### 4. TICKET_FIELD_EXTRACTION_PROMPT

新增：

```python
TICKET_FIELD_EXTRACTION_PROMPT = TicketAgentPromptSpec(
    name="ticket_field_extraction",
    version="ticket_field_extraction:v1",
    system_prompt=TICKET_FIELD_EXTRACTION_SYSTEM_PROMPT,
    description="Extract validated customer service ticket fields from agent state.",
)
```

它负责字段提取节点的 prompt 身份。

### 5. TICKET_AGENT_PROMPTS

新增：

```python
TICKET_AGENT_PROMPTS = {
    TICKET_INTENT_CLASSIFICATION_PROMPT.name: TICKET_INTENT_CLASSIFICATION_PROMPT,
    TICKET_FIELD_EXTRACTION_PROMPT.name: TICKET_FIELD_EXTRACTION_PROMPT,
}
```

这是当前项目的本地 prompt registry。

它的价值是：

```text
集中管理当前 Agent 已知 prompt。
```

### 6. get_ticket_agent_prompt_spec

新增：

```python
def get_ticket_agent_prompt_spec(prompt_name):
    return TICKET_AGENT_PROMPTS[prompt_name]
```

它现在很简单。

但它让外部代码不用直接访问 dict。

以后如果要加默认值、错误处理、版本选择、远程加载，都可以从这里扩展。

### 7. message builder 接收 prompt_spec

意图识别消息构造函数现在支持：

```python
def build_ticket_intent_classification_messages(
    user_message: str,
    *,
    prompt_spec: TicketAgentPromptSpec = TICKET_INTENT_CLASSIFICATION_PROMPT,
)
```

字段提取消息构造函数也支持：

```python
def build_ticket_field_extraction_messages(
    state: TicketAgentState,
    *,
    prompt_spec: TicketAgentPromptSpec = TICKET_FIELD_EXTRACTION_PROMPT,
)
```

调用处使用：

```python
"content": prompt_spec.system_prompt
```

这表示：

```text
消息内容从 prompt spec 来。
```

以后替换 prompt 版本时，不需要改 message builder 内部逻辑。

### 8. LLM 类保存 prompt_spec

意图识别分类器：

```python
class LLMTicketIntentClassifier:
    def __init__(..., prompt_spec=TICKET_INTENT_CLASSIFICATION_PROMPT):
        self.prompt_spec = prompt_spec
```

字段提取器：

```python
class LLMTicketFieldExtractor:
    def __init__(..., prompt_spec=TICKET_FIELD_EXTRACTION_PROMPT):
        self.prompt_spec = prompt_spec
```

这代表：

```text
每个 LLM 组件都明确知道自己正在使用哪一版 prompt。
```

### 9. 日志记录 prompt name/version

成功日志加了：

```text
prompt_name=%s prompt_version=%s
```

失败日志也加了：

```text
prompt_name=%s prompt_version=%s
```

这能帮助后续排查：

```text
同一个模型，不同 prompt version 的成功率、失败率、延迟和 token 用量。
```

### 10. 工厂函数透传 prompt_spec

工厂函数现在支持：

```python
create_llm_ticket_intent_classifier(..., prompt_spec=...)
create_llm_ticket_field_extractor(..., prompt_spec=...)
create_ticket_agent_model_dependencies(..., intent_prompt_spec=..., field_prompt_spec=...)
build_ticket_agent_graph_for_model_mode(..., intent_prompt_spec=..., field_prompt_spec=...)
```

这让后续 prompt v2 测试有落点。

如果未来想做对比，可以构建两个 graph：

```text
graph_v1 -> intent prompt v1
graph_v2 -> intent prompt v2
```

再用同一批 eval case 比较结果。

---

## 七、本节测试重点

### 1. prompt 注册表测试

新增测试确认：

```text
ticket_intent_classification
ticket_field_extraction
```

都注册到了：

```text
TICKET_AGENT_PROMPTS
```

这保证 prompt 不是散落对象。

### 2. v1 版本稳定性测试

测试确认：

```text
TICKET_INTENT_CLASSIFICATION_PROMPT.version == "ticket_intent_classification:v1"
TICKET_FIELD_EXTRACTION_PROMPT.version == "ticket_field_extraction:v1"
```

这不是为了死记字符串。

而是为了防止有人无意中改了版本号。

prompt 版本变化应该是有意识的动作。

### 3. message builder 可替换 prompt_spec 测试

测试构造一个自定义 prompt：

```python
TicketAgentPromptSpec(
    name="ticket_intent_classification",
    version="ticket_intent_classification:v2",
    system_prompt="custom intent system prompt",
    description="test prompt override",
)
```

再断言 system message 使用的是自定义内容。

这证明：

```text
message builder 没有硬绑全局 v1 字符串。
```

### 4. 工厂函数透传测试

测试给真实 LLM 依赖工厂传入两个自定义 prompt spec。

然后断言：

```python
dependencies["intent_classifier"].prompt_spec is intent_prompt_spec
dependencies["field_extractor"].prompt_spec is field_prompt_spec
```

这证明：

```text
prompt spec 能从工厂入口传到具体 LLM 组件。
```

### 5. 日志字段测试

已有真实 LLM fake client 测试里，新增断言：

```text
prompt_name=...
prompt_version=...
```

这保证：

```text
真实模型调用成功时，日志不会漏掉 prompt version。
```

---

## 八、以后怎么新增 prompt v2

本节没有新增 v2。

但你现在应该知道未来怎么做。

假设要改意图识别 prompt。

合理流程是：

```text
1. 复制当前 v1 prompt 内容。
2. 新建 TICKET_INTENT_CLASSIFICATION_PROMPT_V2。
3. version 写成 ticket_intent_classification:v2。
4. 只改你明确想验证的 prompt 内容。
5. 用 build_ticket_agent_graph_for_model_mode 传入 v2。
6. 跑意图识别 eval。
7. 对比 v1/v2 pass rate 和 bad cases。
8. 如果 v2 明确更好，再把默认 prompt 切到 v2。
```

不要直接覆盖 v1。

因为直接覆盖会导致：

```text
旧版本不可复现。
坏例不知道是怎么来的。
eval 报告无法对比。
```

### 一个未来可能的 v2 形态

示意：

```python
TICKET_INTENT_CLASSIFICATION_PROMPT_V2 = TicketAgentPromptSpec(
    name="ticket_intent_classification",
    version="ticket_intent_classification:v2",
    system_prompt=(
        TICKET_INTENT_CLASSIFICATION_SYSTEM_PROMPT
        + "如果用户只是询问政策，不要过早判定为 ticket_request。"
    ),
    description="Reduce over-routing policy questions into ticket requests.",
)
```

这只是示意，不是本节要提交的代码。

真正做 v2 前，需要先看坏例。

prompt 变更应该被坏例驱动，而不是凭空润色。

---

## 九、常见误区

### 误区 1：prompt 版本管理就是写个 v1

不是。

只写 `v1` 没有意义。

版本必须进入：

```text
调用链路
日志
测试
eval
```

本节至少做到调用链路、日志和测试。

### 误区 2：prompt 改一点点不用升版本

不对。

只要 prompt 变更可能影响模型行为，就应该升版本。

哪怕只是换一种说法，也可能改变模型判断边界。

### 误区 3：prompt 越长越好

不一定。

prompt 太长会带来：

- token 成本增加。
- 模型注意力分散。
- 约束互相冲突。
- 后续维护困难。

好 prompt 应该清楚、稳定、可验证，而不是单纯长。

### 误区 4：prompt 版本可以代替 eval

不能。

prompt version 只能告诉你用了哪个版本。

eval 才能告诉你这个版本效果如何。

### 误区 5：有 Git 就不需要 prompt version

不对。

Git 是代码整体版本。

prompt version 是模型任务说明的业务版本。

两者应该配合使用。

---

## 十、本节练习

### 练习 1：解释 prompt version 的价值

题目：为什么真实 LLM 节点需要记录 prompt version？

参考答案：

因为模型行为会受 prompt 影响。记录 prompt version 后，日志和 eval 才能把一次模型输出和具体 prompt 版本关联起来。这样当效果变差、输出校验失败或成本变化时，可以判断是否和某次 prompt 修改有关。

### 练习 2：区分 prompt name 和 prompt version

题目：`ticket_intent_classification` 和 `ticket_intent_classification:v1` 分别表示什么？

参考答案：

`ticket_intent_classification` 是 prompt name，表示这个 prompt 的任务是意图识别。`ticket_intent_classification:v1` 是 prompt version，表示这个意图识别 prompt 当前使用第 1 版任务说明。

### 练习 3：为什么不直接在日志里写完整 prompt

题目：为什么日志里记录 `prompt_name` 和 `prompt_version`，而不是每次都记录完整 prompt 内容？

参考答案：

因为完整 prompt 可能很长，写入日志会增加体积和成本，也可能带来敏感信息风险。更合理的方式是日志记录 prompt name/version，完整内容保存在代码仓库或 prompt 管理系统里，通过版本回查。

### 练习 4：prompt 改动后应该怎么验证

题目：如果你把意图识别 prompt 从 v1 改成 v2，应该怎么判断 v2 是否更好？

参考答案：

应该用同一批固定 eval case 分别跑 v1 和 v2，对比 pass rate、P0 样本表现和 bad cases。不能只靠手动试几个例子或主观感觉判断。

### 练习 5：为什么要把 prompt_spec 传进 message builder

题目：为什么不继续让 message builder 固定使用全局 `TICKET_INTENT_CLASSIFICATION_SYSTEM_PROMPT`？

参考答案：

固定全局字符串会让后续 prompt v2 难以接入和测试。message builder 接收 `prompt_spec` 后，可以默认使用 v1，也可以在测试或 eval 中显式传入 v2，从而支持版本对比。

### 练习 6：解释 frozen dataclass 的作用

题目：为什么 `TicketAgentPromptSpec` 使用 `@dataclass(frozen=True)`？

参考答案：

因为 prompt spec 应该像稳定配置一样使用。`frozen=True` 可以防止代码在运行中随意修改 name、version 或 system_prompt。如果要改 prompt，应该创建新的版本对象，而不是偷偷改旧对象。

---

## 十一、自测题

### 自测 1

题目：prompt version 能不能证明某个 prompt 效果更好？

答案：不能。prompt version 只能标识版本，效果好不好要靠 eval、bad case 分析和真实测试判断。

### 自测 2

题目：为什么 prompt 改动可能影响业务流程？

答案：因为当前 Agent 会根据模型输出决定后续路由或字段提取结果。prompt 改动可能让模型把同一句用户输入分类成不同 intent，或者提取出不同字段，从而影响业务流程。

### 自测 3

题目：当前项目的两个 prompt name 是什么？

答案：`ticket_intent_classification` 和 `ticket_field_extraction`。

### 自测 4

题目：当前意图识别 prompt 的版本是什么？

答案：`ticket_intent_classification:v1`。

### 自测 5

题目：当前字段提取 prompt 的版本是什么？

答案：`ticket_field_extraction:v1`。

### 自测 6

题目：如果日志里有 `prompt_version=ticket_field_extraction:v1`，它说明什么？

答案：说明这次字段提取模型调用使用的是字段提取 prompt 的 v1 版本。

### 自测 7

题目：为什么失败日志也要记录 prompt version？

答案：因为模型输出校验失败、API 错误或其他异常也可能和某个 prompt 版本有关。失败日志记录版本后，才能统计和排查哪个版本更容易出问题。

### 自测 8

题目：本节有没有修改 prompt 内容本身？

答案：没有。本节主要给现有 prompt 增加名称、版本、注册表、日志记录和测试保护，不调 prompt 效果。

---

## 十二、面试表达版

如果面试官问：

```text
你们项目里的 prompt 是怎么管理的？
```

可以这样回答：

```text
我们没有把真实 LLM prompt 当成普通字符串随意散落在代码里，而是给智能工单 Agent 的核心 prompt 建了 PromptSpec，里面包含 prompt name、version、system prompt 和 description。

当前有两个受管理的 prompt：ticket_intent_classification:v1 和 ticket_field_extraction:v1，分别用于意图识别和工单字段提取。

LLM classifier 和 field extractor 会持有自己的 prompt_spec，message builder 从 prompt_spec 读取 system prompt，成功和失败日志都会记录 prompt_name 和 prompt_version。这样后续排查某次模型调用或对比 eval 结果时，可以明确知道使用的是哪个 prompt 版本。

我们也让工厂函数和 graph 构建入口支持透传 prompt_spec，为后续 prompt v2/v3 的 A/B eval 和回归对比留了接口。
```

这个回答体现了：

- 知道 prompt 是工程资产。
- 知道 prompt version 要进入调用链路和日志。
- 知道 prompt 变更要和 eval 关联。
- 知道当前没有过度引入复杂平台。
- 知道为后续版本对比预留接口。

---

## 十三、本节小结

本节完成的是 prompt 版本管理的第一层能力：

```text
PromptSpec
-> Prompt registry
-> message builder 使用 prompt_spec
-> LLM component 持有 prompt_spec
-> 成功/失败日志记录 prompt_name 和 prompt_version
-> 测试保护默认 v1 和自定义 prompt 透传
```

你现在要记住：

```text
prompt 不是普通文案。
prompt 是会影响模型行为和业务路径的工程资产。
```

本节还没有做 prompt v2，也没有做 prompt 对比 eval。

这很正常。

合理顺序是：

```text
先让 prompt 可命名、可版本化、可追踪
再根据坏例设计 v2
再用 eval 比较 v1/v2
最后决定是否切换默认版本
```

下一节进入：

```text
阶段 6 第 18 节：模型输出失败处理
```

那一节会继续解决真实 LLM 接入后的生产问题：

```text
如果模型空输出、非 JSON、Pydantic 校验失败、字段缺失或 provider 异常，系统应该怎么处理？
```
