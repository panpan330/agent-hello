# 阶段 10 第 11 节：模型 fallback

## 本节定位

这一节学习 AI 应用生产化里的兜底能力：

```text
模型 fallback。
```

上一节学习的是多模型路由：

```text
调用模型之前，选择适合的模型。
```

这一节学习的是：

```text
模型已经选好了，但调用失败、超时、限流或服务异常时，系统如何兜底。
```

## 本节学习目标

- 理解什么是模型 fallback。
- 理解 fallback 和多模型路由、重试、降级的区别。
- 理解哪些错误适合 fallback，哪些错误不适合 fallback。
- 理解 fallback 对成本、延迟、日志、trace、用户体验的影响。
- 看懂本节新增的 `model_fallback.py` 和 `llm_service.py` 里的 fallback 链路。

## 本节新增和修改

- 新增 `app/core/model_fallback.py`。
- 新增 `tests/test_model_fallback.py`。
- 修改 `config.py`，增加 fallback 配置。
- 修改 `.env.example`，补充 fallback 配置示例。
- 修改 `llm_service.py`，普通聊天和流式创建阶段支持最小 fallback。
- 修改配置、配置安全快照和 LLM service 测试。

## 一句话先讲透

模型 fallback 就是：

```text
主模型调用失败后，后端判断这个错误是否值得兜底；如果值得，并且有不同的备用模型，就再调用一次备用模型，尽量把失败变成可用结果。
```

## 基础知识铺垫

### 1. 什么是 fallback

fallback 可以翻译成：

```text
兜底方案。
```

在软件系统里，它的意思是：

```text
主方案不可用时，系统切到备用方案，尽量不要让用户直接感受到彻底失败。
```

例子：

```text
主缓存 Redis 不可用 -> 暂时查数据库。
主支付通道失败 -> 切备用支付通道。
主短信服务失败 -> 切备用短信服务。
主模型超时 -> 切备用模型。
```

fallback 的核心不是“把错误藏起来”。

它的核心是：

```text
在明确边界内，提高系统可用性。
```

### 2. 什么是模型 fallback

模型 fallback 是 fallback 思想在 LLM 调用里的应用。

它处理的是：

```text
主模型调用不可用。
```

例如：

```text
主模型超时。
主模型被限流。
主模型服务返回 5xx。
主模型网络连接失败。
主模型返回空内容。
主模型返回格式异常。
```

这时系统可以尝试：

```text
调用备用模型。
```

例如：

```text
qwen-fast 失败 -> qwen-balanced
qwen-balanced 失败 -> qwen-backup
provider A 失败 -> provider B
```

本节先做最小版本：

```text
同一个 provider 下，主模型失败后切到配置的备用模型或备用档位。
```

暂时不做跨 provider。

### 3. fallback 不是重试

fallback 和重试很容易混。

重试是：

```text
同一个方案失败后，再试一次同一个方案。
```

例如：

```text
qwen-balanced 超时
-> 等 200ms
-> 再请求 qwen-balanced
```

fallback 是：

```text
主方案失败后，换一个备用方案。
```

例如：

```text
qwen-balanced 超时
-> 改请求 qwen-backup
```

它们解决的问题不完全一样。

重试适合：

```text
偶发网络抖动。
短暂连接失败。
瞬时 5xx。
```

fallback 适合：

```text
主模型持续不可用。
主模型被限流。
主模型当前不稳定。
主模型返回内容质量或格式异常。
```

后续第 14 节会专门学重试。

这一节先把 fallback 边界讲清楚。

### 4. fallback 不是路由

上一节学过多模型路由。

路由是：

```text
调用模型之前，选择哪个模型。
```

fallback 是：

```text
模型调用失败之后，决定是否换备用模型。
```

顺序是：

```text
用户请求
-> 模型路由
-> 调用主模型
-> 主模型失败
-> 判断是否 fallback
-> 调用备用模型
```

所以不要把它们写成一个混乱逻辑。

正确理解是：

```text
路由决定第一选择。
fallback 决定失败后的备用选择。
```

### 5. fallback 不是降级回答

降级回答是：

```text
系统不再调用同等级能力，而是给用户一个能力较低但可接受的结果。
```

例如：

```text
模型不可用时，返回“当前智能回答暂时不可用，请稍后重试”。
RAG 检索失败时，只回答“没有查到相关知识库内容”。
工具调用失败时，引导用户转人工。
```

fallback 是：

```text
还在尝试另一个模型。
```

降级是：

```text
不再完整执行原能力，改走保守结果。
```

二者可以组合：

```text
主模型失败
-> fallback 模型失败
-> 降级回答
```

本节先做模型 fallback。

降级策略会在后面的成本控制、超时治理、SSE 和 Runbook 里继续出现。

### 6. 哪些错误适合 fallback

适合 fallback 的错误通常有一个共同点：

```text
换一个模型，有机会成功。
```

本节默认允许 fallback 的错误包括：

```text
LLM_TIMEOUT
LLM_RATE_LIMITED
LLM_PROVIDER_ERROR
LLM_CONNECTION_ERROR
LLM_PROVIDER_STATUS_ERROR
LLM_CALL_FAILED
LLM_EMPTY_RESPONSE
LLM_BAD_RESPONSE
```

逐个理解一下。

#### LLM_TIMEOUT

模型调用超时。

这可能是：

```text
模型太忙。
输入太长。
网络慢。
provider 响应慢。
```

换备用模型可能成功。

所以适合 fallback。

#### LLM_RATE_LIMITED

模型服务限流。

这说明：

```text
当前模型或当前账号请求太频繁。
```

如果备用模型使用不同限额，fallback 可能成功。

所以适合 fallback。

但要注意：

```text
如果备用模型和主模型共用同一个限额，fallback 可能仍然失败。
```

#### LLM_PROVIDER_ERROR

模型服务内部错误。

例如 provider 返回 500。

这通常是临时性问题。

换备用模型有机会成功。

#### LLM_CONNECTION_ERROR

无法连接模型服务。

可能是网络问题，也可能是服务地址不可达。

如果备用模型仍然走同一个 base_url，未必能解决。

但如果备用模型或备用 provider 走不同服务，fallback 就有价值。

本节当前还没有跨 provider，所以它只是保留可扩展边界。

#### LLM_PROVIDER_STATUS_ERROR

模型服务返回异常状态。

比如非预期 HTTP 状态码。

这类错误可能是模型侧临时异常，也可能是服务端返回了未覆盖的新错误。

可以尝试 fallback。

#### LLM_CALL_FAILED

未知模型调用失败。

这是兜底错误码。

它不够具体。

生产系统里应该尽量把错误分细。

但在学习项目里，可以先把它视为可 fallback。

#### LLM_EMPTY_RESPONSE

模型返回空内容。

这不是网络失败，而是结果不可用。

换一个模型可能得到正常回答。

所以适合 fallback。

#### LLM_BAD_RESPONSE

模型返回格式异常。

例如 SDK 返回结构不符合预期。

如果是某个模型或 provider 的返回不稳定，换备用模型可能有用。

所以适合 fallback。

### 7. 哪些错误不适合 fallback

不适合 fallback 的错误通常有一个共同点：

```text
换模型大概率解决不了，甚至会掩盖真实问题。
```

例如：

```text
LLM_API_KEY_MISSING
LLM_AUTHENTICATION_FAILED
LLM_PERMISSION_DENIED
LLM_RESOURCE_NOT_FOUND
LLM_BAD_REQUEST
```

#### LLM_API_KEY_MISSING

API key 没配置。

这是服务端配置问题。

换模型通常也没有用。

应该让 `/ready`、日志或部署检查告诉开发者：

```text
密钥没配。
```

#### LLM_AUTHENTICATION_FAILED

认证失败。

比如 API key 错了。

如果同一个 key 用于所有模型，fallback 没意义。

还可能造成更多失败请求。

#### LLM_PERMISSION_DENIED

没有模型权限。

如果主模型没有权限，备用模型是否有权限要看配置。

但默认不应该盲目 fallback。

否则容易掩盖权限配置问题。

#### LLM_RESOURCE_NOT_FOUND

模型名或接口地址不存在。

这通常是配置写错。

应该修配置，而不是悄悄换模型。

#### LLM_BAD_REQUEST

请求参数错误。

例如参数格式不符合 provider 要求。

如果请求参数本身错了，换模型也可能继续错。

所以默认不 fallback。

### 8. fallback 为什么必须有限

fallback 不能无限做。

错误做法：

```text
主模型失败 -> 备用 A 失败 -> 备用 B 失败 -> 备用 C 失败 -> 一直试
```

这样会导致：

```text
延迟失控。
成本失控。
错误排查困难。
上游被打爆。
用户等更久但结果仍不一定好。
```

本节只做：

```text
最多一次 fallback。
```

这是学习阶段和生产早期最容易理解、最容易控制的方案。

以后如果要多级 fallback，也要配置清楚：

```text
最大 fallback 次数。
每一级模型。
每一级超时。
哪些错误进入下一层。
总请求预算。
总成本预算。
```

### 9. fallback 和用户体验

fallback 的目标是提高用户体验。

没有 fallback 时：

```text
主模型超时 -> 用户直接看到失败。
```

有 fallback 时：

```text
主模型超时 -> 备用模型成功 -> 用户得到回答。
```

但 fallback 也会带来副作用：

```text
用户等待时间可能变长。
回答风格可能变化。
备用模型质量可能低于主模型。
成本可能增加。
```

所以 fallback 不是越多越好。

它是一种权衡。

### 10. fallback 和成本

fallback 会增加成本。

因为一次用户请求可能变成：

```text
主模型调用一次
备用模型再调用一次
```

如果主模型失败发生在已经消耗 token 之后，成本可能已经产生。

然后备用模型又消耗一遍 token。

所以 fallback 要和第 8 节的 token 成本统计结合。

你要知道：

```text
fallback 发生了多少次。
fallback 成功率是多少。
fallback 多花了多少 token。
fallback 是否真的减少了用户失败。
```

否则 fallback 可能只是让账单变高。

### 11. fallback 和耗时

fallback 也会增加耗时。

没有 fallback：

```text
主模型 5 秒超时 -> 请求失败，用时 5 秒。
```

有 fallback：

```text
主模型 5 秒超时 -> 备用模型 2 秒成功 -> 请求成功，但总耗时约 7 秒。
```

用户得到了结果，但等得更久。

所以 fallback 要和第 9 节的请求耗时拆解结合。

日志和 trace 里应该能看出：

```text
primary model 耗时。
fallback model 耗时。
总请求耗时。
fallback 是否成功。
```

本节先记录 fallback started / succeeded / failed 日志。

后续更完整的 tracing 可以把它拆成 span。

### 12. fallback 和 trace/log/metric

fallback 必须可观测。

否则线上只会看到：

```text
请求成功了。
```

但不知道背后其实发生了：

```text
主模型失败。
备用模型成功。
```

生产系统里至少应该记录：

```text
primary_model
fallback_model
primary_error_code
fallback_success
fallback_elapsed_ms
route_tier
fallback_tier
```

同时不能记录：

```text
用户原始问题
完整 prompt
messages
模型完整回答
API key
Authorization
工具结果
RAG 文档正文
```

本节日志只记录安全元信息。

### 13. fallback 和流式输出

流式输出的 fallback 更复杂。

普通非流式调用是：

```text
模型完整返回后，服务端再把结果给用户。
```

所以如果主模型失败，服务端还没给用户任何内容。

这时 fallback 很自然。

流式输出是：

```text
模型边生成，服务端边把 token 发给用户。
```

如果已经输出了一半：

```text
主模型：你好，关于这个问题...
```

然后主模型断了。

这时再切备用模型，会有问题：

```text
备用模型不知道前面已经输出了什么。
用户可能看到两段风格不同、逻辑重复或互相矛盾的内容。
SSE 协议里也不好把已发出的内容收回。
```

所以本节只支持：

```text
流式创建阶段失败时 fallback。
```

也就是：

```text
还没开始给用户发送内容之前，可以换备用模型。
```

如果流式输出中途失败，本节不做 fallback。

后面学习 SSE 生产化和流式错误处理时再专门讲。

## 本节主题系统讲解

### 1. 本节接在多模型路由之后

上一节新增了：

```text
route_llm_model
LLMModelRouteDecision
```

调用链变成：

```text
用户问题
-> route_llm_model
-> decision.model
-> 调用模型
```

本节在这个基础上增加：

```text
主模型失败
-> build_llm_fallback_decision
-> 判断是否 fallback
-> 调用 fallback_route.model
```

所以 fallback 不是替代路由。

它是路由之后的失败处理。

### 2. 本节新增的配置

本节新增：

```text
LLM_ENABLE_FALLBACK=true
LLM_FALLBACK_MODEL=""
LLM_FALLBACK_TIER="balanced"
LLM_FALLBACK_ERROR_CODES="LLM_TIMEOUT,..."
```

它们分别表示：

```text
是否启用 fallback。
显式备用模型名。
没有显式备用模型时，用哪个档位作为备用。
哪些错误码允许 fallback。
```

如果 `LLM_FALLBACK_MODEL` 为空：

```text
系统会用 LLM_FALLBACK_TIER 对应的模型。
```

如果对应模型和主模型一样：

```text
不会 fallback。
```

这能避免：

```text
同一个模型失败后，又用同一个模型再调用一次。
```

那种行为更像 retry，不是 fallback。

### 3. 本节的 fallback 决策对象

核心对象是：

```text
LLMFallbackDecision
```

它包含：

```text
should_attempt
reason
primary_error_code
primary_model
fallback_route
```

含义是：

```text
should_attempt：是否真的要 fallback。
reason：为什么 fallback 或为什么不 fallback。
primary_error_code：主模型失败原因。
primary_model：主模型名。
fallback_route：备用模型路由结果。
```

它不是简单返回 `True/False`。

因为线上排查时你需要知道：

```text
为什么没有 fallback？
是关闭了？
错误不允许？
还是备用模型和主模型一样？
```

### 4. 本节的 fallback 原因

当前原因有四种：

```text
retryable_error
disabled
non_retryable_error
same_model
```

#### retryable_error

表示：

```text
错误码允许 fallback，并且备用模型和主模型不同。
```

这时会真正尝试备用模型。

#### disabled

表示：

```text
配置关闭了 fallback。
```

这时主模型失败就直接失败。

#### non_retryable_error

表示：

```text
错误码不在允许 fallback 的列表里。
```

例如认证失败、权限失败、参数错误。

#### same_model

表示：

```text
备用模型和主模型是同一个模型。
```

这种情况下不 fallback。

因为换模型没有发生。

### 5. 普通聊天 fallback 链路

普通聊天现在的流程是：

```text
生成主路由 route_decision
-> 构造 messages
-> 调用主模型
-> 主模型成功：记录成功日志并返回
-> 主模型失败：映射 AppException
-> 构造 fallback_decision
-> 记录主模型失败日志
-> 如果不能 fallback：抛出主错误
-> 如果能 fallback：调用备用模型
-> 备用模型成功：记录成功和 fallback_succeeded，返回备用结果
-> 备用模型失败：记录 fallback_failed，抛出备用错误
```

这里有一个重要点：

```text
主模型失败会被记录。
```

即使备用模型成功，日志里也能看到主模型曾经失败过。

否则线上成功率看起来很好，但背后的模型不稳定会被掩盖。

### 6. 流式聊天 fallback 链路

流式聊天现在只在：

```text
stream create 阶段失败
```

时 fallback。

也就是：

```text
还没开始迭代 chunk。
还没开始向用户输出内容。
```

流程是：

```text
创建主模型 stream
-> 创建失败：判断是否 fallback
-> 创建备用模型 stream
-> 备用 stream 创建成功：返回备用 stream iterator
```

如果已经进入：

```text
for chunk in stream
```

之后才失败，本节不 fallback。

原因是：

```text
部分内容可能已经发给用户，不能安全切另一个模型继续写。
```

### 7. 本节暂时不做什么

本节不做：

```text
多级 fallback。
跨 provider fallback。
按实时健康状态 fallback。
按用户套餐 fallback。
fallback 后自动降级回答。
fallback 成本报表。
fallback span 树。
流式中途失败后的模型切换。
```

这些都重要。

但学习顺序上先掌握：

```text
哪些错误能 fallback。
fallback 决策怎么表达。
怎么接入一次真实 LLM 调用。
怎么保证日志安全。
怎么用测试锁住行为。
```

## 本节代码讲解

### 1. `model_fallback.py`

本节新增：

```text
app/core/model_fallback.py
```

它负责：

```text
判断某次模型失败后是否应该 fallback。
```

它不负责：

```text
真实调用模型。
构造 prompt。
处理 HTTP。
记录完整日志。
```

这让它保持简单、可测试。

### 2. `build_llm_fallback_decision`

核心函数：

```python
build_llm_fallback_decision(
    settings,
    primary_route=route_decision,
    error_code=app_exception.code,
)
```

它做三层判断：

```text
1. fallback 是否启用。
2. 错误码是否允许 fallback。
3. 备用模型是否和主模型不同。
```

只有三层都通过：

```text
should_attempt=True
```

### 3. `build_fallback_route_decision`

备用模型也用：

```text
LLMModelRouteDecision
```

这样好处是：

```text
主模型和备用模型在日志、成本、调用链上结构一致。
```

备用 route 的模型名来自：

```text
settings.resolved_llm_fallback_model
```

也就是：

```text
优先 LLM_FALLBACK_MODEL。
如果没有，就用 LLM_FALLBACK_TIER 对应的模型。
```

### 4. `llm_service.py` 普通聊天变化

普通聊天里新增了失败后的分支：

```text
主模型调用失败
-> 转成 AppException
-> build_llm_fallback_decision
-> 不能 fallback 就抛出
-> 能 fallback 就调用 fallback_route.model
```

关键点：

```text
fallback 不重新构造 prompt。
fallback 使用同一份 serialized_messages。
```

因为用户请求没变。

变化的只是：

```text
使用哪个模型执行这次请求。
```

### 5. `llm_service.py` 流式变化

流式聊天只在：

```text
_create_stream_completion
```

失败时 fallback。

如果 stream 创建成功，后续 chunk 迭代里的失败仍然走原来的失败处理。

这是为了避免：

```text
用户已经看到部分内容后，又切模型造成混乱。
```

### 6. 测试覆盖

本节新增和修改测试，覆盖：

```text
可 fallback 错误会调用备用模型。
认证失败不会 fallback。
备用模型和主模型相同不会 fallback。
显式 fallback model 优先。
流式创建阶段失败可以 fallback。
fallback 日志不记录用户原文。
配置默认值和环境变量读取正常。
```

这些测试的意义是：

```text
以后你改 fallback 配置或 LLM 调用链路时，不会不小心把兜底边界改坏。
```

## 常见误区

### 误区 1：所有错误都应该 fallback

不是。

认证失败、权限失败、参数错误、模型名不存在这些问题，fallback 往往解决不了。

盲目 fallback 会掩盖配置问题。

### 误区 2：fallback 越多越稳定

不是。

fallback 次数越多，成本和延迟越难控。

生产系统必须限制 fallback 次数。

本节只做一次。

### 误区 3：fallback 成功就不用记录主模型失败

不是。

如果主模型失败但备用模型成功，用户看到的是成功。

但系统运营者必须知道：

```text
主模型其实不稳定。
```

所以主模型失败日志仍然要保留。

### 误区 4：流式中途失败也直接换模型继续

这通常不安全。

因为用户已经看到部分内容。

换模型继续可能导致：

```text
重复。
前后矛盾。
风格不一致。
协议状态混乱。
```

本节只处理流式创建阶段失败。

### 误区 5：fallback 不影响成本

会影响。

主模型失败也可能已经消耗 token。

备用模型再调用一次，会增加成本。

### 误区 6：fallback 可以代替监控

不能。

fallback 只是减少用户失败。

但如果 fallback 频率变高，说明主模型或上游服务有问题。

应该监控并告警。

## 本节练习

### 练习 1：解释 fallback 和路由的区别

请回答：

```text
模型 fallback 和多模型路由有什么区别？
```

参考答案：

```text
多模型路由发生在模型调用之前，决定第一次使用哪个模型。
模型 fallback 发生在主模型调用失败之后，判断是否切换到备用模型继续尝试。
```

### 练习 2：判断哪些错误适合 fallback

下面哪些错误更适合 fallback？

```text
1. LLM_TIMEOUT
2. LLM_AUTHENTICATION_FAILED
3. LLM_RATE_LIMITED
4. LLM_BAD_REQUEST
5. LLM_PROVIDER_ERROR
```

参考答案：

```text
更适合 fallback 的是 1、3、5。
2 是认证失败，通常是密钥问题；4 是请求参数错误，换模型通常也解决不了。
```

### 练习 3：为什么备用模型相同就不 fallback

请回答：

```text
为什么 fallback model 和 primary model 一样时，不应该 fallback？
```

参考答案：

```text
因为这并没有换备用方案，只是又调用同一个模型一次，更接近 retry。fallback 的含义是切换到不同备用方案，所以相同模型不应该算 fallback。
```

### 练习 4：为什么流式中途失败不直接 fallback

请回答：

```text
为什么模型已经流式输出了一部分内容后，不适合直接切备用模型继续输出？
```

参考答案：

```text
因为用户已经看到部分内容，备用模型不知道前面已经输出了什么，继续生成可能造成重复、矛盾、风格不一致或协议状态混乱。所以本节只在流式创建阶段失败时 fallback。
```

### 练习 5：解释 fallback 对成本和延迟的影响

请回答：

```text
fallback 为什么会增加成本和延迟？
```

参考答案：

```text
因为一次用户请求可能先调用主模型，主模型失败后又调用备用模型。主模型可能已经消耗时间和 token，备用模型也会再次消耗时间和 token，所以 fallback 会增加总耗时和总成本。
```

## 自测题

### 自测 1：fallback 的核心目的是什么

参考答案：

```text
核心目的是在主模型临时不可用或结果不可用时，通过备用模型提高系统可用性，尽量避免用户直接看到失败。
```

### 自测 2：为什么认证失败不适合默认 fallback

参考答案：

```text
认证失败通常是 API key 或权限配置问题。如果多个模型共用同一套认证配置，换模型也解决不了，反而会掩盖真实配置错误。
```

### 自测 3：本节为什么只做一次 fallback

参考答案：

```text
因为多次 fallback 会让延迟、成本和排查复杂度快速上升。学习阶段和生产早期应该先控制边界，最多一次 fallback 更容易理解、测试和运营。
```

### 自测 4：fallback 成功后为什么还要记录主模型失败

参考答案：

```text
因为用户虽然得到了结果，但系统需要知道主模型曾经失败。否则主模型不稳定会被备用模型掩盖，后续无法做监控、告警、成本分析和模型治理。
```

### 自测 5：fallback 决策里为什么要有 reason

参考答案：

```text
reason 可以解释为什么 fallback 或为什么不 fallback，例如 disabled、non_retryable_error、same_model、retryable_error。线上排查时不能只看 true/false。
```

### 自测 6：fallback 日志为什么不能记录 prompt

参考答案：

```text
prompt、messages、用户输入、工具结果和 RAG 文档正文都可能包含隐私或业务敏感信息。fallback 排查只需要模型名、错误码、是否 fallback、fallback 原因和耗时等安全元信息。
```

## 本节小结

这一节你要记住：

```text
fallback 是主模型失败后的有限兜底，不是无限重试，也不是掩盖所有错误。
```

当前项目已经具备：

```text
fallback 配置
-> fallback 决策
-> 普通聊天 fallback
-> 流式创建阶段 fallback
-> 安全日志
-> 自动化测试
```

下一节会学习：

```text
成本控制。
```

也就是在路由、fallback、token 成本统计之后，继续学习如何限制预算、减少不必要的高成本调用，并让 AI 应用在真实环境中可持续运行。
