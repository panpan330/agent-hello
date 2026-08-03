# 阶段 10 第 12 节：成本控制

## 本节定位

这一节学习 AI 应用生产化里的成本治理能力：

```text
成本控制。
```

前面已经学了：

```text
Token 成本统计
多模型路由
模型 fallback
请求耗时拆解
```

这些能力都和成本有关。

这一节要解决的问题是：

```text
系统不能只知道花了多少钱，还要能在调用模型之前判断这次请求是否允许花这么多。
```

## 本节学习目标

- 理解成本统计和成本控制的区别。
- 理解 token 预算、金额预算、请求预算、用户预算、租户预算、功能预算。
- 理解为什么成本控制要尽量在模型调用前做。
- 理解高成本请求的来源。
- 理解输出上限、输入上限、总 token 上限、单次金额上限。
- 理解成本控制和模型路由、fallback、缓存、限流、降级的关系。
- 看懂本节新增的 `cost_control.py` 和 LLM service 接入方式。

## 本节新增和修改

- 新增 `app/core/cost_control.py`。
- 新增 `tests/test_cost_control.py`。
- 修改 `config.py`，增加 LLM 成本控制配置。
- 修改 `.env.example`，补充成本控制配置示例。
- 修改 `llm_service.py`，在模型调用前做成本控制预检。
- 修改配置、配置安全快照、LLM service 测试。

## 一句话先讲透

成本控制就是：

```text
模型调用前先估算这次请求大概会消耗多少 token 和多少钱；如果超过预算，就压缩输出上限、禁用 fallback，或者直接拒绝这次高成本请求。
```

## 基础知识铺垫

### 1. 为什么 AI 应用必须做成本控制

传统后端接口通常也有成本。

例如：

```text
数据库查询成本
Redis 成本
带宽成本
服务器 CPU 和内存成本
第三方短信成本
支付通道成本
```

但 AI 应用有一个很特殊的地方：

```text
每次模型调用都可能按 token 计费。
```

用户输入越长，成本可能越高。

模型输出越长，成本也可能越高。

RAG 拼进去的知识库上下文越多，成本也会变高。

Agent 多次调用模型，成本会继续放大。

Tool Calling、fallback、重试、评测、批处理都会增加模型调用次数。

所以 AI 应用不能只考虑：

```text
功能能不能跑通。
```

还要考虑：

```text
这个功能跑起来以后，成本是否可控。
```

### 2. 什么是成本统计

第 8 节学过 token 成本统计。

成本统计回答的是：

```text
这次调用实际用了多少 token？
大概花了多少钱？
```

例如模型返回：

```text
prompt_tokens = 1000
completion_tokens = 500
total_tokens = 1500
```

系统根据单价估算：

```text
输入成本
输出成本
总成本
```

这叫统计。

统计发生在：

```text
调用之后。
```

因为你只有拿到模型返回的 usage，才知道真实消耗。

### 3. 什么是成本控制

成本控制回答的是：

```text
这次请求是否允许这样调用模型？
如果太贵，系统应该怎么处理？
```

它通常发生在：

```text
调用之前。
```

因为如果等模型已经调用完再发现太贵：

```text
钱已经花出去了。
```

所以成本控制更像是：

```text
模型调用前的预算闸门。
```

它要尽量在请求真正打到模型之前判断：

```text
输入是否太长？
预留输出是否太多？
总 token 是否超预算？
单次预计金额是否超预算？
是否应该禁止 fallback？
是否应该直接拒绝？
```

### 4. 成本统计和成本控制的区别

这两个概念一定要分清。

```text
成本统计：事后记账。
成本控制：事前限制。
```

成本统计像：

```text
消费账单。
```

成本控制像：

```text
消费限额。
```

只做成本统计的问题是：

```text
你能知道钱花在哪里，但不能阻止钱继续被花掉。
```

只做成本控制但不做统计的问题是：

```text
你设置了限制，但不知道真实效果如何。
```

生产系统通常需要两者结合：

```text
调用前：预算预检。
调用后：真实 usage 统计。
```

### 5. 什么是 token 预算

token 预算可以理解为：

```text
一次请求最多允许消耗多少 token。
```

token 预算通常分成三类：

```text
输入 token 预算
输出 token 预算
总 token 预算
```

#### 输入 token 预算

输入 token 包括：

```text
system prompt
用户问题
历史消息
RAG 文档上下文
工具结果
结构化输出格式说明
安全规则
```

输入太长会导致：

```text
成本上升。
延迟上升。
超出模型上下文窗口。
模型注意力分散。
更容易遗漏关键信息。
```

所以要有输入上限。

#### 输出 token 预算

输出 token 是模型生成的回答。

输出越长：

```text
成本越高。
耗时越长。
流式输出时间越久。
```

所以生产系统通常不会让模型无限输出。

需要设置：

```text
max_output_tokens
```

本节把它作为：

```text
请求预留输出预算。
```

#### 总 token 预算

总 token 大致是：

```text
输入 token + 预留输出 token
```

例如：

```text
输入估算 1200 token
预留输出 800 token
总预算 2000 token
```

总预算用于控制：

```text
一次请求整体最大消耗。
```

### 6. 什么是金额预算

金额预算就是：

```text
一次请求最多允许花多少钱。
```

模型计费通常和 token 有关。

但是不同模型价格不同。

同样 1000 token：

```text
fast 模型可能很便宜。
strong 模型可能更贵。
```

所以金额预算需要结合：

```text
模型单价。
输入 token 估算。
输出 token 预留。
```

本节新增的配置：

```text
LLM_MAX_ESTIMATED_COST_PER_REQUEST
```

就是单次请求预计金额上限。

注意：

```text
如果没有配置 token 单价，就无法做准确金额预算。
```

此时仍然可以做 token 数量预算。

### 7. 请求预算、用户预算、租户预算、功能预算

成本控制不是只有一种预算。

常见预算有：

```text
单次请求预算
用户预算
租户预算
功能预算
全局预算
```

#### 单次请求预算

限制：

```text
一个请求最多消耗多少。
```

本节实现的就是单次请求预算。

它最简单，也最适合先学。

#### 用户预算

限制：

```text
某个用户每天、每小时、每月最多消耗多少。
```

比如：

```text
普通用户每天最多 100 次 AI 问答。
高级用户每天最多 1000 次。
```

这需要用户身份、计数存储、时间窗口。

后面学习限流和 Redis 时会继续关联。

#### 租户预算

租户就是企业客户或组织。

租户预算限制：

```text
某个企业或团队整体最多消耗多少。
```

企业系统里非常常见。

因为 AI 成本通常由公司或租户承担。

#### 功能预算

不同功能成本不同。

例如：

```text
普通聊天
RAG 问答
Agent 工单创建
批量文档总结
自动化评测
```

它们可以有不同预算。

#### 全局预算

全局预算限制：

```text
整个系统在某段时间内最多花多少钱。
```

它适合防止：

```text
异常流量
脚本刷接口
错误循环调用模型
Agent 死循环
```

### 8. 高成本请求通常从哪里来

AI 应用的高成本请求通常来自这些地方：

```text
用户输入太长。
历史对话太长。
RAG 召回文档太多。
每个 chunk 太长。
工具结果太大。
Prompt 模板过重。
模型输出没有限制。
Agent 循环太多轮。
fallback 触发太频繁。
重试次数太多。
评测集批量跑太大。
强模型被滥用。
```

这说明成本控制不是一个孤立模块。

它会影响：

```text
Prompt 设计
RAG 检索
Agent Loop
模型路由
fallback
缓存
限流
评测
监控
```

### 9. 成本控制的常见处理方式

当系统发现请求可能太贵时，通常有几种处理方式。

#### 直接放行

如果在预算内：

```text
正常调用模型。
```

#### 压缩输出上限

如果输入不算太长，但总预算超了，可以减少输出预算。

例如：

```text
原来允许输出 1024 token
现在只允许输出 300 token
```

这叫：

```text
cap output
```

它的结果是：

```text
用户还能得到回答，但回答会更短。
```

#### 裁剪上下文

如果输入太长，可以减少输入。

例如：

```text
裁剪历史消息。
减少 RAG chunk 数。
压缩工具结果。
只保留最近对话。
只保留高分文档。
```

本节暂时不做真实上下文裁剪。

因为裁剪要结合 RAG、对话历史和工具结果分别设计。

本节先做预算判断。

#### 切低成本模型

如果任务可以接受低成本模型，可以通过路由切换。

例如：

```text
摘要任务走 fast。
复杂任务走 strong。
```

第 10 节已经做了多模型路由基础。

成本控制后续可以影响路由策略。

#### 禁用 fallback

fallback 可能让一次请求变成两次模型调用。

所以高成本请求不一定允许 fallback。

例如：

```text
一个请求本来就预留 7000 token。
主模型失败后再 fallback，成本可能翻倍。
```

本节新增：

```text
LLM_DISABLE_FALLBACK_ABOVE_TOTAL_TOKENS
```

表示：

```text
如果预留总 token 超过这个阈值，就不允许 fallback。
```

#### 直接拒绝

如果请求太长或预计成本太高：

```text
直接拒绝。
```

这不是偷懒。

这是生产系统的必要边界。

否则一个异常请求就可能拖慢系统或造成不必要账单。

### 10. 成本控制为什么要尽量在模型调用前

模型调用前能做的是：

```text
估算。
```

模型调用后能做的是：

```text
统计。
```

虽然估算不一定精确，但它有价值。

因为它能在真正花钱前发现明显高风险请求。

例如：

```text
用户传了 5 万字。
RAG 拼了 30 个 chunk。
max_output_tokens 设置成 8000。
```

这种请求不用等模型返回。

调用前就应该被限制。

### 11. 估算为什么不等于真实账单

本节使用的是粗略 token 估算。

它不等于真实 tokenizer。

原因是：

```text
不同模型 tokenizer 不同。
中文、英文、符号切分方式不同。
SDK 计算方式可能不同。
服务端还可能加入额外格式开销。
```

所以本节的估算叫：

```text
preflight estimate
```

它用于：

```text
调用前控制风险。
```

真实账单仍然以模型返回的 usage 和供应商账单为准。

### 12. 成本控制和限流的区别

成本控制和限流也容易混。

限流回答的是：

```text
单位时间内允许多少请求。
```

成本控制回答的是：

```text
这次请求预计消耗是否超预算。
```

举例：

```text
每分钟 10 次请求，这是限流。
每次请求最多 8000 token，这是成本控制。
```

它们通常要一起用。

因为：

```text
少量高成本请求也可能很贵。
大量低成本请求也可能很贵。
```

### 13. 成本控制和缓存的关系

缓存可以降低成本。

例如：

```text
同一个问题重复问，直接返回缓存结果。
相同 RAG 查询复用检索结果。
相同 embedding 文本不重复向量化。
```

缓存适合解决：

```text
重复请求。
重复计算。
重复模型调用。
```

成本控制适合解决：

```text
单次请求过贵。
总预算不可控。
```

二者组合可以更有效。

### 14. 成本控制和产品策略

成本控制不是纯技术问题。

它和产品策略有关。

例如：

```text
免费用户最多使用 fast 模型。
付费用户允许更多 RAG 文档。
企业用户有租户预算。
管理员可以临时提高预算。
高价值业务流程允许 strong 模型。
```

所以真正生产系统里，成本控制会连接：

```text
用户等级
租户套餐
权限系统
账单系统
后台配置
运营策略
```

本节先做技术底座。

## 本节主题系统讲解

### 1. 本节在当前系统的位置

当前 LLM 调用链路已经有：

```text
模型路由
模型调用
fallback
token 成本统计
安全日志
```

本节新增一个步骤：

```text
模型调用前成本预检
```

完整链路变成：

```text
用户问题
-> route_llm_model
-> build_chat_messages
-> serialize_chat_messages
-> build_llm_cost_control_decision
-> 如果 block：不调用模型
-> 如果 cap_output：降低 max_tokens 后调用模型
-> 如果 allow：正常调用模型
-> 如果主模型失败：根据成本控制结果决定是否允许 fallback
-> 调用后继续统计真实 usage 和估算成本
```

### 2. 为什么成本控制放在 LLM service

本节把成本控制接在：

```text
app/services/llm_service.py
```

原因是这里最接近：

```text
真实模型调用。
```

它能同时看到：

```text
路由后的模型。
最终 messages。
max_output_tokens。
token pricing。
fallback 配置。
```

如果放得太早，比如 router 层：

```text
还不知道最终 prompt 长什么样。
```

如果放得太晚，比如模型调用后：

```text
钱已经花了。
```

所以放在 LLM service 调用前是合理的。

### 3. 本节新增的成本控制决策

核心对象是：

```text
LLMCostControlDecision
```

它包含：

```text
action
reason
estimated_input_tokens
requested_max_output_tokens
effective_max_output_tokens
reserved_total_tokens
fallback_allowed
estimated_cost
max_estimated_cost
```

这些字段分别回答：

```text
这次请求怎么处理？
为什么这样处理？
输入估算多少 token？
原本想给多少输出 token？
最终允许多少输出 token？
总共预留多少 token？
是否允许 fallback？
预计金额是多少？
金额预算是多少？
```

这比简单返回 true/false 更适合生产系统。

### 4. 当前支持的三种 action

本节有三种动作：

```text
allow
cap_output
block
```

#### allow

表示：

```text
请求在预算内，可以正常调用模型。
```

#### cap_output

表示：

```text
输入可以接受，但总 token 超预算，所以降低输出上限。
```

例如：

```text
requested_max_output_tokens = 1024
effective_max_output_tokens = 300
```

这时仍然调用模型，但传给模型的 `max_tokens` 会更小。

#### block

表示：

```text
请求超出预算，不能调用模型。
```

当前项目会抛出：

```text
LLM_COST_BUDGET_EXCEEDED
```

状态码是：

```text
429
```

这表示请求被预算/额度限制拒绝。

### 5. 当前支持的 reason

本节有这些原因：

```text
disabled
within_budget
input_tokens_exceeded
total_tokens_exceeded
estimated_cost_exceeded
```

它们用于解释：

```text
为什么放行？
为什么压缩输出？
为什么阻断？
```

线上排查不能只看：

```text
block
```

还要知道：

```text
是输入太长？
是总 token 超了？
还是预计金额超了？
```

### 6. 为什么高成本请求会禁用 fallback

fallback 会把一次请求变成：

```text
主模型调用 + 备用模型调用
```

如果请求本来就很大，再 fallback 一次，成本和耗时会更高。

所以本节引入：

```text
fallback_allowed
```

当：

```text
reserved_total_tokens > LLM_DISABLE_FALLBACK_ABOVE_TOTAL_TOKENS
```

时，主模型失败后不会 fallback。

这不是放弃稳定性。

这是明确告诉系统：

```text
这类高成本请求不允许再追加一次备用模型成本。
```

### 7. 本节暂时不做什么

本节不做：

```text
用户级预算。
租户级预算。
Redis 计数。
数据库账单记录。
RAG 上下文裁剪。
多轮历史智能裁剪。
按套餐模型路由。
成本报表页面。
全局预算熔断。
```

这些以后都可以扩展。

本节先做最小但关键的一步：

```text
单次请求级成本控制。
```

## 本节代码讲解

### 1. 新增配置

本节新增：

```text
LLM_ENABLE_COST_CONTROL
LLM_MAX_INPUT_TOKENS_PER_REQUEST
LLM_MAX_TOTAL_TOKENS_PER_REQUEST
LLM_MIN_OUTPUT_TOKENS
LLM_MAX_ESTIMATED_COST_PER_REQUEST
LLM_DISABLE_FALLBACK_ABOVE_TOTAL_TOKENS
```

含义分别是：

```text
是否启用成本控制。
单次请求最大输入 token。
单次请求最大总 token。
压缩输出时最低保留多少输出 token。
单次请求最大预计金额。
超过多少总 token 后禁用 fallback。
```

### 2. `cost_control.py`

新增模块：

```text
app/core/cost_control.py
```

它只负责：

```text
根据 messages、max_output_tokens、pricing、settings 生成成本控制决策。
```

它不负责：

```text
真实调用模型。
真实扣费。
存储账单。
裁剪上下文。
修改用户套餐。
```

这样边界清楚。

### 3. `build_llm_cost_control_decision`

核心函数：

```python
build_llm_cost_control_decision(
    settings,
    serialized_messages=serialized_messages,
    requested_max_output_tokens=settings.max_output_tokens,
    pricing=self._build_token_pricing(),
)
```

它做的判断顺序是：

```text
1. 成本控制是否关闭。
2. 输入 token 是否超过输入预算。
3. 输入 + 输出预留是否超过总 token 预算。
4. 如果能压缩输出，就 cap_output。
5. 如果压缩后输出太少，就 block。
6. 如果配置了金额预算，就判断预计金额是否超限。
7. 判断是否允许 fallback。
```

### 4. LLM service 接入

普通聊天和流式聊天都会先执行：

```text
cost_decision = self._build_cost_control_decision(serialized_messages)
```

然后记录：

```text
llm_cost_control_decision
```

如果：

```text
cost_decision.should_block
```

就直接抛出：

```text
LLM_COST_BUDGET_EXCEEDED
```

不会调用模型。

如果不阻断，就把：

```text
cost_decision.effective_max_output_tokens
```

传给模型调用：

```text
max_tokens=...
```

### 5. 成本控制和 fallback 的接入

主模型失败后，原本会构造：

```text
fallback_decision
```

本节又加了一层：

```text
_apply_cost_control_to_fallback
```

如果成本控制判断：

```text
fallback_allowed=False
```

就把 fallback reason 改成：

```text
cost_control
```

这样日志里能看出来：

```text
不是错误不能 fallback，而是成本预算不允许 fallback。
```

## 常见误区

### 误区 1：有成本统计就等于有成本控制

不是。

成本统计是事后知道花了多少。

成本控制是事前限制最多能花多少。

### 误区 2：估算不准就没意义

不是。

估算不等于账单，但能拦住明显过大的请求。

生产系统经常先用估算做前置保护。

### 误区 3：只限制输出就够了

不够。

输入太长同样会带来高成本。

RAG、历史消息、工具结果都可能让输入爆炸。

### 误区 4：fallback 总是提升体验

不一定。

fallback 会增加成本和耗时。

高成本请求可能需要禁用 fallback。

### 误区 5：成本控制只靠后端代码

不是。

真实项目还需要产品策略、租户预算、用户套餐、监控告警、账单报表一起配合。

### 误区 6：成本控制应该偷偷裁剪用户内容

不能随便偷偷裁剪。

如果裁剪影响回答质量，系统应该有明确策略。

比如：

```text
保留最近历史。
保留高分 RAG 文档。
告诉用户内容太长。
提供摘要后再问。
```

## 本节练习

### 练习 1：解释成本统计和成本控制的区别

参考答案：

```text
成本统计是模型调用后记录实际 token 和估算金额，属于事后记账。
成本控制是模型调用前估算本次请求是否超预算，属于事前限制。
```

### 练习 2：判断哪些因素会增加 AI 成本

下面哪些会增加成本？

```text
1. 用户输入很长。
2. RAG 拼接很多文档。
3. max_output_tokens 设置很大。
4. fallback 频繁发生。
5. 日志里多打印几行普通文本。
```

参考答案：

```text
1、2、3、4 都会增加模型调用成本。
5 通常增加的是日志存储成本，不是模型 token 成本。
```

### 练习 3：为什么高成本请求可能要禁用 fallback

参考答案：

```text
因为 fallback 会额外调用备用模型。高成本请求本身已经预留很多 token，如果主模型失败后再调用备用模型，成本和耗时可能进一步放大，所以可以通过预算策略禁止 fallback。
```

### 练习 4：什么时候应该 cap_output

参考答案：

```text
当输入还在允许范围内，但输入 token 加上原始输出预算超过总 token 上限，并且剩余输出预算仍然足够生成一个可用回答时，可以压缩输出上限，而不是直接拒绝请求。
```

### 练习 5：什么时候应该 block

参考答案：

```text
当输入本身已经超过输入预算，或者压缩输出后剩余输出预算太小，或者单次预计金额超过预算时，应该直接 block，避免调用模型产生不可控成本。
```

## 自测题

### 自测 1：为什么成本控制要尽量在模型调用前做

参考答案：

```text
因为模型调用后成本可能已经产生。调用前虽然只能估算，但可以提前拦截明显超预算的请求，避免不必要的模型费用。
```

### 自测 2：什么是 reserved_total_tokens

参考答案：

```text
reserved_total_tokens 是输入 token 估算值加上有效输出 token 上限，表示这次请求预留的最大 token 消耗规模。
```

### 自测 3：为什么 max_output_tokens 是成本控制的重要配置

参考答案：

```text
因为模型输出越长，completion tokens 越多，成本和耗时也越高。限制 max_output_tokens 可以控制单次请求的最大输出成本。
```

### 自测 4：为什么金额预算依赖 token pricing

参考答案：

```text
因为金额估算需要知道输入 token 和输出 token 的单价。如果没有配置模型单价，只能做 token 数量预算，不能做可靠的金额预算。
```

### 自测 5：成本控制和限流有什么区别

参考答案：

```text
限流控制单位时间请求数量，成本控制控制单次或累计请求的 token 和金额消耗。少量高成本请求也需要成本控制，大量低成本请求也需要限流。
```

### 自测 6：为什么成本控制日志不能记录用户原文

参考答案：

```text
成本控制只需要记录估算 token、action、reason、预算和是否允许 fallback，不需要记录用户输入、prompt、messages 或 RAG 文档正文，避免泄露隐私和业务敏感信息。
```

## 本节小结

这一节你要记住：

```text
成本控制不是账单统计，而是模型调用前的预算闸门。
```

当前项目已经具备：

```text
输入 token 预算
总 token 预算
输出上限压缩
单次预计金额预算
高成本请求禁用 fallback
超预算请求阻断
成本控制安全日志
自动化测试
```

下一节会学习：

```text
限流。
```

也就是继续从“单次请求成本控制”扩展到“单位时间内请求数量控制”，防止高频请求把 AI 服务和模型额度打满。
