# 阶段 6 第 18 节：模型输出失败处理

本节目标：让智能工单 Agent 在真实 LLM 节点输出失败时，不只是“报错结束”，而是能先识别失败类型，再决定是否降级到规则逻辑。

前面几节我们已经完成了这些基础：

```text
第 13 节：真实 LLM 意图识别节点
第 14 节：真实 LLM 工单字段提取节点
第 15 节：Pydantic 校验模型输出
第 16 节：fake LLM 和真实 LLM 双模式
第 17 节：prompt 版本管理
```

这些能力让 Agent 可以接真实模型，也能知道本次模型调用用了哪个 prompt 版本。

但是生产环境里还有一个很现实的问题：

```text
模型不是每一次都会返回我们想要的结构。
```

比如：

```text
空字符串
不是 JSON
JSON 是合法的，但字段不符合 schema
多返回了不允许的字段
字段类型不对
枚举值不在允许范围内
上游模型服务超时
模型 API key 没配
```

这些都不能简单地混成一句“模型失败了”。

因为不同失败，对应的处理策略不一样：

```text
空输出 / JSON 不合法 / schema 不通过
-> 可以考虑降级到规则逻辑，至少让用户流程继续走

超时 / 限流 / 服务商临时异常
-> 可以考虑 retry，也可以临时降级

API key 没配 / 权限不对 / 模型名不对
-> 不应该悄悄降级，否则开发者会误以为系统正常
```

本节要做的就是：

```text
把“模型输出失败”从模糊错误，变成可分类、可记录、可测试、可扩展的失败策略。
```

---

## 一、本节在主线里的位置

阶段 6 是生产化与评测阶段。

当前第 13-18 节的衔接关系可以这样理解：

```text
第 13 节
真实 LLM 可以做意图识别

第 14 节
真实 LLM 可以做字段提取

第 15 节
模型输出必须经过 Pydantic 校验

第 16 节
系统支持 rule_based / fake_llm / real_llm 三种模式

第 17 节
真实 LLM prompt 可以被命名、版本化、进入日志

第 18 节
模型输出失败后，系统能分类失败并按策略兜底
```

这节不是在教“怎么让模型永远不出错”。

模型永远会有不稳定性。

真正的工程能力是：

```text
模型出错时，系统知道自己该怎么失败。
```

这句话很重要。

业务系统不能假设 AI 永远正确。
AI 系统也不能假设业务系统永远等得起。
所以我们需要一个明确的失败处理层。

---

## 二、本节学习目标

学完本节，你要能解释清楚：

1. 什么是模型输出失败。
   答案：模型输出失败是指模型调用可能已经返回了内容，但内容不能被业务系统可靠使用，例如空输出、不是合法 JSON、字段不符合 schema、字段值越界等。

2. 模型输出失败和模型调用失败有什么区别。
   答案：模型输出失败更关注“返回内容不可用”；模型调用失败更关注“请求模型服务本身失败”，例如超时、限流、认证失败、网络异常。

3. 为什么不能把所有失败都写成一个 `except Exception`。
   答案：因为不同错误需要不同策略。可恢复错误可以降级或重试，配置错误应该暴露给开发者，未知错误应该保守抛出。混成一个异常会让日志、测试和后续排查都失去判断依据。

4. 为什么 Pydantic 校验不是失败处理的终点。
   答案：Pydantic 能告诉我们输出不合格，但它本身不决定“接下来怎么办”。失败处理层要根据校验错误决定是重试、降级、拒绝，还是继续抛错。

5. `invalid_json` 和 `schema_validation` 有什么区别。
   答案：`invalid_json` 表示内容连 JSON 都不是，解析阶段失败；`schema_validation` 表示内容是 JSON，但字段、类型、枚举、额外字段等不符合业务 schema。

6. 为什么 API key 未配置不应该自动降级。
   答案：因为这是配置错误，不是模型偶发输出错误。如果悄悄降级，会掩盖部署问题，让开发者以为真实模型已经接入成功。

7. 什么是规则兜底。
   答案：规则兜底是指当 LLM 输出不可用时，系统回退到确定性的本地规则逻辑，例如关键词分类、正则提取订单号、规则判断问题类型。

8. 为什么规则兜底不等于规则优先。
   答案：规则优先是默认就用规则；规则兜底是先尝试 LLM，失败后才临时使用规则。两者在系统行为和日志含义上不一样。

9. 为什么本节给兜底加了显式开关。
   答案：因为自动降级会改变真实 LLM 模式的行为。默认不改变原有行为，只有调用方明确开启 `enable_model_output_fallback=True`，才启用本节策略。

10. 本节新增测试主要保护什么。
    答案：保护失败分类是否正确、配置错误是否不会被隐藏、意图识别能否降级、字段提取能否降级并记录来源、真实 LLM 图是否能通过开关启用兜底。

---

## 三、本节暂时不学什么

本节只做模型输出失败处理的第一层。

暂时不展开：

- 不做自动 retry。
- 不做指数退避。
- 不做 circuit breaker。
- 不做 provider 级健康检查。
- 不做多模型 fallback。
- 不做模型 A 失败后切模型 B。
- 不做 prompt 自动修复。
- 不做让模型自我修正 JSON。
- 不做 LangChain structured output retry parser。
- 不做 LangSmith trace 可视化。
- 不做线上告警系统。

为什么先不做这些？

因为你现在需要先真正理解最基本的一层：

```text
失败是什么
失败怎么分类
哪些失败能兜底
哪些失败不能隐藏
兜底怎么进入现有 Agent 流程
怎么用测试证明这个策略没有乱来
```

这些没懂透，直接学 retry、熔断、多模型切换，会变成堆概念。

---

## 四、基础知识铺垫

### 1. “模型输出失败”到底是什么意思

模型输出失败不是一句泛泛的“模型没做好”。

在工程里，它通常表示：

```text
模型返回的内容无法被程序继续可靠使用。
```

注意这里有两个关键词：

```text
内容
可靠使用
```

如果模型返回：

```json
{"intent":"ticket_request","reason":"用户要创建工单"}
```

并且字段符合我们的 schema，那它可以被程序可靠使用。

如果模型返回：

```text
好的，我觉得用户想要创建工单。
```

人能看懂，但程序不能直接当作结构化结果用。

如果模型返回：

```json
{"intent":"create_ticket","reason":"用户要创建工单"}
```

它是合法 JSON，但 `intent` 不在我们允许的枚举值里。

如果模型返回：

```json
{
  "intent": "ticket_request",
  "reason": "用户要创建工单",
  "should_create_ticket": true
}
```

它看起来更“聪明”，但多了不允许的字段。
在我们的业务边界里，这也应该失败。

为什么？

因为我们已经规定：

```text
模型只负责分类或提取字段。
是否创建工单、是否进入确认节点，是后端流程控制的责任。
```

模型越界输出流程控制字段，就容易破坏后端安全边界。

所以模型输出失败不是小问题。
它直接关系到业务系统是否可信。

---

### 2. 模型输出失败和模型调用失败的区别

这两个概念很容易混。

可以这样区分：

```text
模型调用失败
-> 请求模型服务这个动作失败了

模型输出失败
-> 请求可能成功了，但返回内容不符合业务要求
```

例子：

```text
模型调用失败：
- API key 未配置
- 认证失败
- 权限不足
- 请求超时
- 服务商 500
- 网络连接失败
- rate limit

模型输出失败：
- 空字符串
- 非 JSON
- JSON 字段缺失
- JSON 多了字段
- 枚举值错误
- 字段类型错误
- 布尔值被写成字符串
- 订单号格式不合规
```

本节标题叫“模型输出失败处理”，但代码里也会识别一部分 provider 错误。

原因是：

当前真实 LLM 节点已经把底层 OpenAI SDK 异常统一映射成 `AppException`。
对 Agent 来说，它接收到的是一个项目内部错误对象。

所以本节的失败分类层会同时认识：

```text
输出类错误
临时 provider 类错误
配置类错误
未知错误
```

但学习重点仍然是输出类错误。

---

### 3. 为什么 JSON mode 不等于绝对可靠

当前项目真实 LLM 调用使用了：

```python
response_format={"type": "json_object"}
```

这通常叫 JSON mode。

它的作用是提高模型返回 JSON 的概率。

但你不能把它理解成：

```text
只要用了 JSON mode，就一定能拿到业务可用的 JSON。
```

原因有几个：

1. 不同 OpenAI-compatible provider 对 JSON mode 的支持程度可能不同。
2. 模型可能返回合法 JSON，但字段不符合你的业务 schema。
3. 模型可能返回空内容。
4. SDK 返回结构可能异常。
5. prompt 约束不够清楚时，模型可能给出不符合预期的字段。
6. 温度、上下文、模型版本变化，都可能影响输出稳定性。

所以真实工程里一般需要多层防线：

```text
prompt 约束
-> JSON mode 或 Structured Outputs
-> Pydantic 校验
-> 失败分类
-> retry / fallback / fail fast
-> 日志和 eval 回归
```

本节做的是第四层和第五层的一部分。

---

### 4. Pydantic 的角色是什么

Pydantic 的角色是：

```text
把“不可信输入”变成“可信对象”，或者明确拒绝。
```

在当前项目里，模型输出就是不可信输入。

哪怕模型是你自己调用的，也不能直接相信。

模型输出进入业务流程前，要先经过：

```python
LLMTicketIntentClassification.model_validate_json(raw_json)
LLMTicketFields.model_validate_json(raw_json)
```

如果失败，Pydantic 会抛出 `ValidationError`。

当前代码再把它转换成项目统一异常：

```python
AppException(
    code="TICKET_INTENT_LLM_VALIDATION_FAILED",
    message="模型意图识别结果校验失败，请稍后重试。",
    status_code=502,
    details=exc.errors(include_url=False),
)
```

这里的 `details` 很关键。

它里面会有 Pydantic 的结构化错误信息。

例如非 JSON 时，错误类型通常会包含：

```text
json_invalid
```

字段枚举不符合时，错误类型可能是：

```text
literal_error
```

多余字段时，错误类型可能是：

```text
extra_forbidden
```

这些细节让我们可以进一步区分：

```text
连 JSON 都不是
还是 JSON 合法但 schema 不通过
```

这就是本节 `invalid_json` 和 `schema_validation` 的来源。

---

### 5. 为什么不能直接 `except Exception: return rule_based()`

这看起来最省事。

但它有严重问题。

假设代码这样写：

```python
try:
    return llm_classifier.classify_intent(message)
except Exception:
    return rule_based_classifier.classify_intent(message)
```

问题是：

```text
API key 没配，也会被吞掉
模型名写错，也会被吞掉
代码 bug，也会被吞掉
依赖对象传错，也会被吞掉
真实模型从来没调用成功，也可能看起来“系统正常”
```

这会造成一个非常坏的工程后果：

```text
系统表面能跑，但真实模型能力根本没有生效。
```

所以兜底策略必须先分类。

正确的思路是：

```text
先识别失败类型
再决定能不能兜底
不能兜底的错误继续抛出
```

这就是本节新增 `classify_ticket_agent_model_output_failure()` 的原因。

---

### 6. 什么是 fail fast

`fail fast` 可以翻译成“快速失败”。

意思是：

```text
当错误说明系统配置或代码本身有问题时，不要假装成功，要尽早暴露出来。
```

比如：

```text
LLM_API_KEY_MISSING
LLM_AUTHENTICATION_FAILED
LLM_PERMISSION_DENIED
LLM_RESOURCE_NOT_FOUND
LLM_BAD_REQUEST
```

这些错误通常不是用户换一种问法就能解决的。

它们更可能说明：

```text
.env 没配
API key 错了
模型权限没开
模型名写错
请求参数写错
```

所以本节给这些错误的策略是：

```text
action = "raise_error"
```

也就是继续暴露错误，而不是自动兜底。

这不是“不够健壮”。
这是为了让真实问题尽早被发现。

---

### 7. 什么是 graceful degradation

`graceful degradation` 可以翻译成“优雅降级”。

意思是：

```text
系统某个高级能力不可用时，退回到低级但稳定的能力，让整体服务尽量可用。
```

在当前项目里：

```text
高级能力：真实 LLM 意图识别 / 真实 LLM 字段提取
低级但稳定的能力：规则分类 / 规则字段提取
```

比如用户说：

```text
订单 A2001 商品破损，帮我投诉处理
```

真实 LLM 本来可以更灵活地理解它。

但如果模型返回了坏 JSON，我们也可以用规则逻辑提取：

```text
intent = ticket_request
issue_type = complaint
order_id = A2001
urgency = high
```

这就是规则兜底的价值。

但降级不是免费的。

规则通常不如模型灵活。
复杂表达、隐含语义、上下文综合判断，规则可能做不好。

所以降级必须进入日志，让后续可以观察：

```text
这次结果是 LLM 成功的，还是 LLM 失败后规则兜底的？
```

---

### 8. 为什么要记录 fallback source

如果字段提取结果最后进入 state：

```python
"ticket_field_extraction_source": "llm"
```

我们就会以为本次字段来自 LLM。

但如果真实情况是：

```text
LLM 失败
规则兜底成功
```

那最好不要仍然标记成 `llm`。

所以本节新增了一个来源：

```python
"llm_fallback_rule_based"
```

它表达的是：

```text
这次原计划走 LLM，但 LLM 输出失败，最终字段来自规则兜底。
```

这个字段以后可以用于：

```text
日志分析
eval 分组
线上监控
问题排查
统计 LLM 失败率
统计兜底覆盖率
判断是否需要优化 prompt
```

这就是为什么“来源标记”不是小细节。

---

### 9. 为什么兜底要有显式开关

本节没有把 `real_llm` 默认行为直接改成自动兜底。

而是给 `build_ticket_agent_graph_for_model_mode()` 加了参数：

```python
enable_model_output_fallback: bool = False
```

默认是 `False`。

只有明确传：

```python
enable_model_output_fallback=True
```

才启用本节新增策略。

原因是：

```text
兜底会改变系统真实行为。
```

如果默认开启，有些测试或调试场景会变得不清晰：

```text
我是在测真实 LLM 能力？
还是在测 LLM 失败后的规则兜底？
```

显式开关能让行为更透明。

这也是生产工程里的一个重要习惯：

```text
会改变系统行为的策略，尽量显式开启。
```

---

### 10. retry 和 fallback 的区别

这两个概念也容易混。

retry 是：

```text
同一个能力失败后，再试一次同一个能力。
```

比如：

```text
调用 LLM 超时
-> 等 500ms
-> 再调用一次 LLM
```

fallback 是：

```text
一个能力失败后，换另一个能力。
```

比如：

```text
LLM 输出坏 JSON
-> 不再继续用 LLM
-> 改用规则提取
```

当前本节做的是 fallback，不是 retry。

但是本节新增的失败对象里有：

```python
retryable: bool
```

这不是说现在已经自动 retry。

它只是先把“将来是否值得重试”的判断记录下来。

例如：

```text
invalid_json -> retryable=True
schema_validation -> retryable=False
provider_error -> retryable=True
configuration_error -> retryable=False
```

以后第 31、32、33 节学 timeout、retry、rate limit、circuit breaker 时，这个字段就可以继续扩展。

---

### 11. 为什么规则兜底要做成包装器

本节没有直接改 `LLMTicketIntentClassifier` 和 `LLMTicketFieldExtractor` 的内部逻辑。

而是新增：

```python
ModelOutputFallbackTicketIntentClassifier
ModelOutputFallbackTicketFieldExtractor
```

这是一个设计选择。

它的好处是：

```text
LLM 类只负责调用 LLM
Fallback 类只负责失败策略
规则类只负责规则逻辑
```

职责拆开后，每个类更容易解释：

```text
LLMTicketIntentClassifier
-> 怎么调用模型、怎么构建 messages、怎么解析输出

ModelOutputFallbackTicketIntentClassifier
-> LLM 失败后是否兜底

RuleBasedTicketIntentClassifier
-> 不调用模型，按本地规则分类
```

如果把全部逻辑塞进 LLM 类，它会很快变成：

```text
调用模型
解析输出
处理异常
判断错误类型
决定 fallback
记录 fallback 日志
调用规则
处理规则结果
```

这会让类职责变得混乱。

所以本节用包装器更清晰。

---

## 五、本节主题系统讲解

### 1. 当前项目在本节之前的失败链路

第 18 节之前，真实 LLM 意图识别的大致流程是：

```text
classify_intent_node
-> LLMTicketIntentClassifier.classify_intent()
-> OpenAI-compatible chat.completions.create()
-> extract_first_reply()
-> parse_ticket_intent_classification_json()
-> Pydantic 校验
-> 返回 intent / reason
```

如果模型输出坏了：

```text
parse_ticket_intent_classification_json()
-> raise AppException(...)
-> LLMTicketIntentClassifier 记录失败日志
-> 继续 raise
-> LangGraph 流程中断
```

字段提取也是类似：

```text
extract_ticket_fields_node
-> LLMTicketFieldExtractor.extract_fields()
-> OpenAI-compatible chat.completions.create()
-> extract_first_reply()
-> parse_ticket_field_extraction_json()
-> Pydantic 校验
-> 返回 ticket_fields
```

如果模型输出坏了：

```text
LLM 字段提取失败
-> AppException
-> 节点失败
-> 图失败
```

这条链路有优点：

```text
失败不会被误当成成功
Pydantic 会严格保护业务结构
日志里已经有 prompt_name 和 prompt_version
```

但缺点是：

```text
一些本可以用规则兜底的场景，也会直接中断。
```

本节就是补这个缺口。

---

### 2. 本节新增的失败对象

本节新增：

```python
@dataclass(frozen=True)
class TicketAgentModelOutputFailure:
    code: str
    kind: TicketAgentModelOutputFailureKind
    action: TicketAgentModelOutputFailureAction
    message: str
    retryable: bool
```

逐个解释：

```text
code
-> 项目内部错误码，例如 TICKET_INTENT_LLM_VALIDATION_FAILED

kind
-> 错误类型归类，例如 invalid_json、schema_validation

action
-> 当前应该怎么处理，例如 fallback_to_rule_based 或 raise_error

message
-> 安全错误消息

retryable
-> 将来是否适合进入 retry 策略
```

为什么不用一个普通 dict？

因为这个对象有固定结构。

固定结构适合用 dataclass 表达：

```text
字段清楚
类型清楚
测试好写
日志好记录
以后扩展也更明确
```

为什么 `frozen=True`？

因为失败分类结果应该是一个事实描述。

创建之后，不应该在各处被随手改。

这能减少调试时的混乱。

---

### 3. 本节新增的失败类型

本节定义了：

```python
TicketAgentModelOutputFailureKind = Literal[
    "empty_response",
    "invalid_json",
    "schema_validation",
    "provider_error",
    "configuration_error",
    "unknown_error",
]
```

这些不是随便起名。

它们分别对应不同处理策略。

#### empty_response

表示模型没有给出可用文本。

对应例子：

```text
模型返回空字符串
模型返回 None
Ticket intent parse 收到空字符串
Ticket field parse 收到空字符串
```

策略：

```text
可以 fallback_to_rule_based
retryable=True
```

因为空输出可能是临时异常，也可能是 provider 返回异常。

#### invalid_json

表示内容不是合法 JSON。

比如：

```text
{invalid-json
```

策略：

```text
可以 fallback_to_rule_based
retryable=True
```

因为它可能是模型偶发没有遵守格式。
未来也可以先 retry 一次。

#### schema_validation

表示 JSON 是 JSON，但不符合业务 schema。

比如：

```json
{"intent":"create_ticket","reason":"用户要创建工单"}
```

`create_ticket` 不是允许的 intent。

策略：

```text
可以 fallback_to_rule_based
retryable=False
```

为什么这里暂时是 `False`？

因为 schema 不通过经常说明 prompt 约束、schema 设计或模型理解有偏差。
简单重试不一定有价值。

当然以后如果做“带错误信息的自我修正 prompt”，它也可以变成可修复。

#### provider_error

表示模型服务临时异常。

比如：

```text
LLM_TIMEOUT
LLM_RATE_LIMITED
LLM_PROVIDER_ERROR
LLM_CONNECTION_ERROR
```

策略：

```text
可以 fallback_to_rule_based
retryable=True
```

这类错误未来会和 retry、rate limit、circuit breaker 放在一起讲。

#### configuration_error

表示配置或权限问题。

比如：

```text
LLM_API_KEY_MISSING
LLM_AUTHENTICATION_FAILED
LLM_PERMISSION_DENIED
LLM_RESOURCE_NOT_FOUND
LLM_BAD_REQUEST
```

策略：

```text
raise_error
retryable=False
```

这类错误不能隐藏。

#### unknown_error

表示不在已知范围内的错误。

策略：

```text
raise_error
retryable=False
```

未知错误保守处理。

原因是：

```text
不知道是什么错误时，不应该假装能恢复。
```

---

### 4. 本节新增的分类函数

核心函数是：

```python
def classify_ticket_agent_model_output_failure(
    exc: Exception,
) -> TicketAgentModelOutputFailure:
```

它做的事情可以画成：

```text
Exception
  |
  |-- 不是 AppException
  |      -> unknown_error / raise_error
  |
  |-- empty response code
  |      -> empty_response / fallback_to_rule_based
  |
  |-- validation failed code
  |      |-- details 里有 json_invalid
  |      |      -> invalid_json / fallback_to_rule_based
  |      |
  |      |-- 否则
  |             -> schema_validation / fallback_to_rule_based
  |
  |-- transient provider code
  |      -> provider_error / fallback_to_rule_based
  |
  |-- configuration code
  |      -> configuration_error / raise_error
  |
  |-- 其他 AppException
         -> unknown_error / raise_error
```

这里最重要的是：

```text
分类函数只负责判断，不直接执行 fallback。
```

为什么？

因为判断和执行是两件事。

判断层：

```text
这个错误是什么？
它应该 fallback 还是 raise？
它是否 retryable？
```

执行层：

```text
如果应该 fallback，调用哪个规则组件？
日志怎么记？
source 怎么标？
```

这就是职责分离。

---

### 5. 为什么要检查 Pydantic 的 `json_invalid`

本节新增了：

```python
def _has_pydantic_error_type(details: object, error_type: str) -> bool:
```

它的作用是从 `AppException.details` 里看有没有某种 Pydantic 错误类型。

当 `model_validate_json()` 遇到非法 JSON 时，Pydantic 会把错误放进结构化 details。

我们只关心：

```text
details 里有没有 type == "json_invalid"
```

如果有，就说明：

```text
模型输出不是合法 JSON
```

如果没有，但仍然是 validation failed，就更可能是：

```text
JSON 合法，但字段不符合 schema
```

这比只看错误码更细。

因为当前两个错误都可能使用：

```text
TICKET_INTENT_LLM_VALIDATION_FAILED
TICKET_FIELD_LLM_VALIDATION_FAILED
```

错误码告诉我们“校验失败”。
details 告诉我们“为什么校验失败”。

---

### 6. 意图识别的兜底包装器

本节新增：

```python
class ModelOutputFallbackTicketIntentClassifier:
```

它的结构是：

```text
primary
-> 默认是真实 LLM classifier

fallback
-> 默认是 RuleBasedTicketIntentClassifier
```

执行逻辑是：

```text
先调用 primary.classify_intent(message)

如果成功：
    直接返回 LLM 结果

如果失败：
    classify_ticket_agent_model_output_failure(exc)

    如果 action 是 fallback_to_rule_based：
        记录 fallback 日志
        调用规则分类器
        返回规则结果

    如果 action 是 raise_error：
        继续抛出原错误
```

它表达的是：

```text
真实 LLM 是主路径。
规则分类是 LLM 输出失败后的兜底路径。
```

它不是把规则和 LLM 混在一起。
而是清楚地规定了主备关系。

---

### 7. 字段提取的兜底包装器

本节新增：

```python
class ModelOutputFallbackTicketFieldExtractor:
```

它和意图识别包装器类似，但多一个问题：

```text
字段提取结果要写入 ticket_field_extraction_source。
```

如果 LLM 成功：

```text
ticket_field_extraction_source = "llm"
```

如果 LLM 失败后规则兜底：

```text
ticket_field_extraction_source = "llm_fallback_rule_based"
```

所以包装器维护了：

```python
self.last_extraction_source
```

当 primary 成功：

```python
self.last_extraction_source = self.primary.extraction_source
```

当 fallback 生效：

```python
self.last_extraction_source = "llm_fallback_rule_based"
```

然后 `extract_ticket_fields_node()` 不再直接读：

```python
extractor.extraction_source
```

而是通过：

```python
get_ticket_field_extraction_source(extractor)
```

这样节点就能拿到动态来源。

这点很关键。

因为字段来源不是固定类属性能完全表达的：

```text
同一个 wrapper
这次可能 LLM 成功
下次可能规则兜底
```

所以需要一个运行时 source。

---

### 8. 为什么 `TicketFieldExtractionSource` 要新增一个值

原来只有：

```python
TicketFieldExtractionSource = Literal["rule_based", "fake_llm", "llm"]
```

本节新增：

```python
"llm_fallback_rule_based"
```

四个值的含义现在是：

```text
rule_based
-> 本来就使用规则字段提取

fake_llm
-> 测试用 fake LLM，模拟 JSON/Pydantic 边界

llm
-> 真实 LLM 成功提取

llm_fallback_rule_based
-> 原计划真实 LLM，失败后回退到规则提取
```

这比只写 `rule_based` 更准确。

如果写成 `rule_based`，会丢失一个事实：

```text
它不是普通规则模式，而是 LLM 失败后的降级结果。
```

对生产排查来说，这个区别很重要。

---

### 9. 本节的工厂开关

本节修改了：

```python
create_ticket_agent_model_dependencies(...)
build_ticket_agent_graph_for_model_mode(...)
```

新增参数：

```python
enable_model_output_fallback: bool = False
```

当：

```python
selected_mode == "real_llm"
```

并且：

```python
enable_model_output_fallback=True
```

才会包装真实 LLM 组件：

```python
intent_classifier = ModelOutputFallbackTicketIntentClassifier(intent_classifier)
field_extractor = ModelOutputFallbackTicketFieldExtractor(field_extractor)
```

这说明：

```text
fake_llm 模式不需要这个兜底
rule_based 模式本来就是规则
real_llm 模式才需要 LLM 输出失败策略
```

默认不开启，是为了保持原有行为。

---

### 10. 本节日志记录了什么

本节新增的 fallback 日志大致长这样：

```text
ticket_agent_model_output_fallback
component=intent_classifier
code=TICKET_INTENT_LLM_EMPTY_RESPONSE
kind=empty_response
action=fallback_to_rule_based
retryable=True
```

字段解释：

```text
component
-> 是意图识别失败，还是字段提取失败

code
-> 项目内部错误码

kind
-> 失败归类

action
-> 本次采取的处理动作

retryable
-> 未来是否适合进入 retry 策略
```

这里没有记录用户原文、API key、完整 prompt。

原因是：

```text
日志要能排查问题，但不能随便泄露敏感信息。
```

第 17 节我们已经把 prompt name/version 进入 LLM 调用日志。

第 18 节把 fallback 事件本身记录下来。

以后如果组合起来看，就可以回答：

```text
哪个 prompt version 下，模型输出失败更多？
失败更多的是 intent 还是 fields？
主要是 invalid_json 还是 schema_validation？
fallback 后业务还能不能继续走？
```

这就是生产化的思路。

---

### 11. 本节执行链路总览

开启 fallback 后，意图识别链路变成：

```text
classify_intent_node
-> ModelOutputFallbackTicketIntentClassifier
   -> LLMTicketIntentClassifier
      -> 调模型
      -> 解析
      -> Pydantic 校验
   -> 如果成功：返回 LLM intent
   -> 如果失败：
      -> classify_ticket_agent_model_output_failure
      -> fallback_to_rule_based ?
      -> RuleBasedTicketIntentClassifier
      -> 返回规则 intent
```

字段提取链路变成：

```text
extract_ticket_fields_node
-> ModelOutputFallbackTicketFieldExtractor
   -> LLMTicketFieldExtractor
      -> 调模型
      -> 解析
      -> Pydantic 校验
   -> 如果成功：
      -> last_extraction_source = "llm"
      -> 返回 LLM fields
   -> 如果失败：
      -> classify_ticket_agent_model_output_failure
      -> fallback_to_rule_based ?
      -> last_extraction_source = "llm_fallback_rule_based"
      -> RuleBasedTicketFieldExtractor
      -> 返回规则 fields
-> get_ticket_field_extraction_source()
-> 写入 ticket_field_extraction_source
```

这条链路你要能从入口讲到出口。

这比背代码更重要。

---

## 六、本节代码讲解

### 1. 新增失败类型 Literal

本节新增：

```python
TicketAgentModelOutputFailureKind = Literal[
    "empty_response",
    "invalid_json",
    "schema_validation",
    "provider_error",
    "configuration_error",
    "unknown_error",
]
```

这段代码值得理解的是：

```text
我们不是用任意字符串表达失败类型。
而是把允许的失败类型限制在固定集合里。
```

这样做的好处：

```text
减少拼写错误
让 IDE 更容易提示
让测试更明确
让后续统计字段更稳定
```

如果日志里一会儿写 `invalid_json`，一会儿写 `bad_json`，一会儿写 `json_error`，后面统计会很痛苦。

固定枚举值就是为了避免这种混乱。

---

### 2. 新增 `TicketAgentModelOutputFailure`

核心结构：

```python
@dataclass(frozen=True)
class TicketAgentModelOutputFailure:
    code: str
    kind: TicketAgentModelOutputFailureKind
    action: TicketAgentModelOutputFailureAction
    message: str
    retryable: bool
```

这不是业务返回给用户的对象。

它是内部策略对象。

你可以把它理解成：

```text
对一次模型失败做出的诊断报告。
```

诊断报告至少要回答：

```text
错误码是什么？
归类是什么？
现在怎么处理？
是否值得重试？
```

---

### 3. 新增错误码分组常量

本节把错误码分成了几组：

```python
TICKET_AGENT_MODEL_EMPTY_RESPONSE_CODES
TICKET_AGENT_MODEL_SCHEMA_VALIDATION_FAILED_CODES
TICKET_AGENT_MODEL_TRANSIENT_PROVIDER_ERROR_CODES
TICKET_AGENT_MODEL_CONFIGURATION_ERROR_CODES
```

这样做比在函数里写一长串 `if code in {...}` 更清楚。

尤其是以后你要调整策略时，可以直接看：

```text
哪些错误算空输出
哪些错误算 schema 校验失败
哪些错误算 provider 临时异常
哪些错误算配置异常
```

这就是“策略显式化”。

---

### 4. 新增分类函数

核心函数：

```python
classify_ticket_agent_model_output_failure(exc)
```

学习它时不要一行行死背。

你应该抓住它的判断顺序：

```text
先排除非 AppException
再判断空输出
再判断 schema 校验失败
再判断 provider 临时错误
再判断配置错误
最后 unknown
```

为什么先排除非 `AppException`？

因为当前项目已经有统一异常边界。
如果传进来的是普通 `RuntimeError`，说明它不一定是业务可理解的模型错误。

对未知错误保守处理：

```text
raise_error
```

这可以防止代码 bug 被兜底吞掉。

---

### 5. 新增意图识别 fallback wrapper

代码结构：

```python
class ModelOutputFallbackTicketIntentClassifier:
    def __init__(self, primary, *, fallback=None):
        self.primary = primary
        self.fallback = fallback or RuleBasedTicketIntentClassifier()
```

这里的 `primary` 表示主路径。

通常是：

```python
LLMTicketIntentClassifier(...)
```

`fallback` 表示备用路径。

默认是：

```python
RuleBasedTicketIntentClassifier()
```

关键逻辑：

```python
try:
    return self.primary.classify_intent(message)
except Exception as exc:
    failure = classify_ticket_agent_model_output_failure(exc)
    if failure.action != "fallback_to_rule_based":
        raise

    log_ticket_agent_model_output_fallback(...)
    return self.fallback.classify_intent(message)
```

这段代码最重要的是：

```text
不是所有 Exception 都 fallback。
```

它只在分类结果允许时 fallback。

---

### 6. 新增字段提取 fallback wrapper

字段提取 wrapper 多了 source 管理。

核心逻辑：

```python
try:
    fields = self.primary.extract_fields(state)
    self.last_extraction_source = self.primary.extraction_source
    return fields
except Exception as exc:
    failure = classify_ticket_agent_model_output_failure(exc)
    if failure.action != "fallback_to_rule_based":
        raise

    self.last_extraction_source = "llm_fallback_rule_based"
    return self.fallback.extract_fields(state)
```

这段代码说明：

```text
结果字段从哪里来，不只取决于类是谁，还取决于本次运行发生了什么。
```

同一个 wrapper：

```text
本次 LLM 成功 -> source 是 llm
下次 LLM 失败 -> source 是 llm_fallback_rule_based
```

这就是为什么需要 `last_extraction_source`。

---

### 7. `extract_ticket_fields_node()` 的小改动

原来：

```python
extraction_source = extractor.extraction_source
```

现在：

```python
extraction_source = get_ticket_field_extraction_source(extractor)
```

这个改动很小，但意义很明确：

```text
节点不再假设 source 一定是静态属性。
```

普通 extractor 仍然没问题：

```text
RuleBasedTicketFieldExtractor.extraction_source = "rule_based"
LLMTicketFieldExtractor.extraction_source = "llm"
FakeLLMTicketFieldExtractor.extraction_source = "fake_llm"
```

fallback wrapper 则可以提供：

```text
last_extraction_source
```

这是一种兼容式扩展。

---

### 8. 工厂函数里的显式接入点

本节不是要求你手动 new wrapper。

而是在图工厂里提供入口：

```python
build_ticket_agent_graph_for_model_mode(
    mode="real_llm",
    enable_model_output_fallback=True,
)
```

这样以后上层调用可以明确表达：

```text
我要真实 LLM 模式，并且开启模型输出失败兜底。
```

如果不开启：

```text
真实 LLM 输出失败仍然按原来的方式抛出。
```

这保留了调试、测试、评估时的清晰边界。

---

## 七、本节测试讲解

测试不需要背，但你要知道每类测试在保护什么。

### 1. 失败分类测试

测试：

```text
empty response -> empty_response / fallback_to_rule_based / retryable=True
invalid JSON -> invalid_json / fallback_to_rule_based / retryable=True
API key missing -> configuration_error / raise_error / retryable=False
```

它保护的是：

```text
分类函数不会把不同错误混在一起。
```

### 2. 意图识别兜底测试

测试构造一个会抛错的 primary classifier。

然后用：

```text
ModelOutputFallbackTicketIntentClassifier
```

验证当 LLM 空输出时，可以回退到规则分类。

它保护的是：

```text
LLM 输出失败时，用户的 ticket_request 流程还能继续识别。
```

### 3. 配置错误不隐藏测试

测试让 primary classifier 抛出：

```text
LLM_API_KEY_MISSING
```

期望 wrapper 继续抛出，而不是 fallback。

它保护的是：

```text
系统不会因为自动降级掩盖部署配置错误。
```

### 4. 字段提取兜底测试

测试让 LLM 字段提取抛出 schema validation 错误。

然后验证：

```text
字段由规则提取
source 标记为 llm_fallback_rule_based
```

它保护的是：

```text
fallback 不只返回结果，还能保留来源信息。
```

### 5. 真实 LLM 图开关测试

测试用 fake client 返回坏 JSON。

然后构建：

```python
build_ticket_agent_graph_for_model_mode(
    mode="real_llm",
    enable_model_output_fallback=True,
)
```

验证图仍然可以走完整：

```text
意图识别 LLM 失败 -> 规则兜底
字段提取 LLM 失败 -> 规则兜底
```

它保护的是：

```text
本节策略真的进入了 LangGraph，而不是只停留在孤立函数里。
```

---

## 八、本节容易踩的坑

### 坑 1：把 fallback 当成成功

fallback 不是普通成功。

它应该被记录。

否则你以后看到系统“能跑”，却不知道其实真实 LLM 经常失败。

### 坑 2：把配置错误也 fallback

这会掩盖部署问题。

尤其是：

```text
API key 未配置
模型名错误
权限不足
```

这些必须尽早暴露。

### 坑 3：以为 JSON mode 能替代 Pydantic

JSON mode 只能提高 JSON 输出概率。

业务字段是否合法，仍然要靠 Pydantic 和后端规则校验。

### 坑 4：只看错误 message，不看 code

message 是给人看的。

code 才适合程序判断。

本节分类函数主要看 `AppException.code`，这是正确方向。

### 坑 5：把 retry 和 fallback 混成一件事

retry 是重试同一个能力。

fallback 是换一个能力。

本节只做 fallback。

### 坑 6：忽略 source

字段提取结果如果来自兜底规则，就应该和真实 LLM 成功区分开。

否则 eval 和日志分析都会失真。

---

## 九、本节完成后的项目能力

现在项目多了一层生产化能力：

```text
真实 LLM 节点
-> prompt version 可追踪
-> Pydantic 输出校验
-> 失败分类
-> 部分失败规则兜底
-> 配置错误保守暴露
-> fallback 日志
-> fallback source 标记
-> 测试保护
```

这比“能调模型”更接近真实工程。

因为真实工程关注的不只是：

```text
正常时怎么跑
```

还关注：

```text
异常时怎么退
退的时候怎么记录
什么不能退
怎么证明策略可靠
```

---

## 十、本节练习

### 练习 1：判断失败类型

下面这些错误分别应该归到哪一类？

1. 模型返回空字符串。
2. 模型返回 `{intent: ticket_request}`，不是合法 JSON。
3. 模型返回 `{"intent":"create_ticket","reason":"..."}`，但 `create_ticket` 不在允许枚举里。
4. `.env` 没有配置 LLM API key。
5. 模型服务返回 429。

参考答案：

1. `empty_response`，可以 fallback，未来也可能 retry。
2. `invalid_json`，可以 fallback，未来也可能 retry。
3. `schema_validation`，可以 fallback，但当前不标记为 retryable。
4. `configuration_error`，应该 `raise_error`，不能悄悄 fallback。
5. `provider_error`，可以 fallback，未来也适合纳入 retry/rate limit 策略。

### 练习 2：解释为什么配置错误不能兜底

问题：如果 `LLM_API_KEY_MISSING` 也自动 fallback 到规则逻辑，会有什么风险？

参考答案：

这样会掩盖真实模型没有接入成功的问题。系统表面上能跑，但其实一直在用规则逻辑，开发者可能误以为真实 LLM 正常工作。生产环境里，这会让部署问题、权限问题和配置问题长期隐藏，后续评测和日志分析也会失真。

### 练习 3：解释 source 的意义

问题：为什么字段提取要区分 `llm` 和 `llm_fallback_rule_based`？

参考答案：

因为两者代表不同事实。`llm` 表示真实 LLM 成功产出字段；`llm_fallback_rule_based` 表示本来要用 LLM，但 LLM 输出失败，最后使用规则提取。这个区别可以帮助后续统计 LLM 失败率、分析 fallback 效果、定位 prompt 问题，并防止误以为所有字段都是 LLM 提取的。

### 练习 4：画出兜底链路

问题：开启 `enable_model_output_fallback=True` 后，字段提取节点在 LLM 返回坏 JSON 时会怎么走？

参考答案：

```text
extract_ticket_fields_node
-> ModelOutputFallbackTicketFieldExtractor.extract_fields()
-> LLMTicketFieldExtractor.extract_fields()
-> parse_ticket_field_extraction_json()
-> Pydantic 发现 invalid_json
-> 抛出 AppException
-> fallback wrapper 分类失败
-> action=fallback_to_rule_based
-> 记录 fallback 日志
-> RuleBasedTicketFieldExtractor.extract_fields()
-> last_extraction_source="llm_fallback_rule_based"
-> extract_ticket_fields_node 写入 ticket_field_extraction_source
```

### 练习 5：思考 retry 与 fallback

问题：如果模型返回 invalid JSON，你觉得应该先 retry 还是直接 fallback？

参考答案：

这取决于业务场景。当前项目先直接 fallback，因为本节重点是建立清晰的失败分类和规则兜底入口，避免引入 retry 复杂度。未来如果发现 invalid JSON 是偶发问题，可以先 retry 一次，再 fallback；但 retry 要配合超时、次数限制、日志和成本控制，不能无限重试。

---

## 十一、自测题

### 自测 1：什么是模型输出失败？

参考答案：

模型输出失败是指模型返回的内容不能被业务系统可靠使用，例如空输出、不是合法 JSON、字段缺失、多余字段、字段类型错误、枚举值不合法等。

### 自测 2：为什么 Pydantic 校验失败后还要再做失败分类？

参考答案：

Pydantic 只负责指出输出不符合模型约束，但它不负责决定系统下一步动作。失败分类层要根据错误码和 details 判断是 invalid JSON、schema 不通过、配置错误还是其他错误，再决定 fallback、raise 或未来 retry。

### 自测 3：本节为什么新增 `TicketAgentModelOutputFailure`？

参考答案：

因为我们需要把一次失败抽象成结构化诊断结果，包含错误码、失败类型、处理动作、消息和是否适合重试。这样策略更清楚，日志和测试也更稳定。

### 自测 4：为什么未知错误默认 `raise_error`？

参考答案：

未知错误可能是代码 bug、依赖注入错误或没有被分类的新异常。如果直接 fallback，会把真实问题吞掉。保守策略是继续抛出，让开发者尽早发现。

### 自测 5：`ModelOutputFallbackTicketIntentClassifier` 的 primary 和 fallback 分别是什么？

参考答案：

`primary` 是主路径，通常是真实 LLM 意图识别器；`fallback` 是备用路径，默认是规则意图识别器。它先调用 primary，只有当失败分类结果允许 fallback 时，才调用 fallback。

### 自测 6：为什么本节不默认开启 fallback？

参考答案：

因为 fallback 会改变真实 LLM 模式的行为。默认不开启可以保持原有行为清晰；只有显式设置 `enable_model_output_fallback=True`，才说明调用方希望在真实 LLM 失败时降级到规则逻辑。

### 自测 7：`retryable=True` 是否表示本节已经会自动重试？

参考答案：

不是。`retryable=True` 只是失败分类结果里的策略信息，表示未来可以考虑对这类错误做 retry。本节只实现 fallback，不实现自动 retry。

### 自测 8：如果模型返回合法 JSON，但多了 `should_create_ticket` 字段，为什么要失败？

参考答案：

因为当前后端规定模型只负责分类或字段提取，不负责流程控制。`should_create_ticket` 这类字段会越过后端流程边界，可能影响安全控制，所以 schema 使用 `extra="forbid"` 拒绝多余字段。

### 自测 9：本节新增测试中，为什么要用 fake client？

参考答案：

因为自动化测试不应该真实调用模型。fake client 可以稳定模拟坏 JSON、空输出和调用行为，让测试专注验证我们自己的失败分类、兜底策略和图接入逻辑。

### 自测 10：本节完成后，下一步为什么适合接真实 `query_order` 到 LangGraph？

参考答案：

因为真实 LLM 节点已经具备更完整的工程边界：prompt 可追踪、输出可校验、失败可分类、可规则兜底。接下来可以把真实工具链路放入 LangGraph，并继续学习工具节点错误处理和权限安全回归。

---

## 十二、本节小结

本节最核心的不是新增了多少代码，而是建立了一个工程判断：

```text
模型失败不能只靠感觉处理。
必须分类、必须记录、必须知道哪些能兜底、哪些不能兜底。
```

现在你应该能解释：

```text
模型输出失败是什么
为什么 JSON mode 不够
Pydantic 校验之后还要做失败分类
为什么配置错误不能隐藏
规则兜底和规则优先的区别
为什么 fallback 要显式开关
为什么字段来源要标记 llm_fallback_rule_based
```

下一节适合进入：

```text
阶段 6 第 19 节：接入真实 query_order 到 LangGraph
```

也就是把真实工具调用链路接进智能工单 Agent 的 LangGraph 流程里。
