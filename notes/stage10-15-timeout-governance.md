# 阶段 10 第 15 节：超时治理

## 本节定位

这一节学习生产 AI 应用里的超时治理。

第 14 节我们学了重试：一次模型调用失败后，系统可以在有限规则下再试一次。

这一节要补上一个更重要的约束：就算错误可以重试，也不能无限等；就算 fallback 可以救场，也不能让用户一直卡住。

所以本节核心问题是：

```text
一次 AI 请求从开始到结束，最多允许占用多久？
在这个总时间里，重试和 fallback 还能不能继续执行？
```

本节不提前学习 SSE 生产化、中途断流处理、熔断器、复杂排队、异步任务、工作流调度。那些会放到后续小节。

## 本节学习目标

- 理解什么是超时，为什么生产系统必须显式设置超时。
- 区分连接超时、读取超时、单次请求超时、总超时、阶段超时。
- 理解为什么“单次 LLM 超时”和“一次用户请求总超时”不是一回事。
- 理解重试、fallback 和总超时预算之间的关系。
- 理解为什么超时治理不是简单把 timeout 调大。
- 学会给 LLM 调用链路加最小可用的总超时预算。
- 能解释本项目新增的 `LLM_TOTAL_TIMEOUT_SECONDS` 是解决什么问题的。

## 本节新增和修改

- 新增 `projects/ai-service/app/core/llm_timeout.py`：集中计算 LLM 总超时预算是否允许继续 retry 或 fallback。
- 修改 `projects/ai-service/app/core/config.py`：新增 `llm_total_timeout_seconds` 配置。
- 修改 `projects/ai-service/.env.example`：新增 `LLM_TOTAL_TIMEOUT_SECONDS` 示例。
- 修改 `projects/ai-service/app/core/config_safety.py`：安全配置快照里记录总超时配置，不记录任何密钥。
- 修改 `projects/ai-service/app/services/llm_service.py`：在 retry 前和 fallback 前加入总超时预算判断。
- 新增 `projects/ai-service/tests/test_llm_timeout.py`：测试超时预算规则。
- 修改配置和服务测试：覆盖配置读取、配置校验、预算不足时不继续重试/不继续 fallback。

## 一句话先讲透

超时治理不是“等多久算超时”这么简单，而是把一次 AI 请求拆成多个阶段，并给整条链路设置总时间预算；每次准备重试或切备用模型前，都要判断剩余时间是否足够再完成一次下游调用。

## 基础知识铺垫

### 1. 什么是超时

超时的英文是：

```text
Timeout
```

它的意思是：

```text
某个操作在规定时间内没有完成，系统主动停止等待，并把它当成失败处理。
```

比如：

```text
调用大模型接口，最多等 30 秒。
30 秒内返回了，继续处理。
30 秒还没有返回，就不要再等，抛出 LLM_TIMEOUT。
```

超时不是下游一定坏了。
超时只说明：

```text
在我能接受的时间范围内，它没有完成。
```

这句话很重要。

用户、接口、网关、后端服务都有自己的等待上限。
如果你的系统一直等下去，下游可能最后成功了，但用户早就断开了，请求线程也被占住了，系统整体吞吐会越来越差。

### 2. 为什么不能没有超时

没有超时的系统会出现几个问题。

第一，请求资源被长期占用。

一个 AI 请求卡住时，它可能占着：

```text
HTTP 连接
Python worker
线程或协程
数据库连接
下游连接池连接
日志 trace 上下文
用户前端等待状态
```

第二，故障会传播。

比如模型供应商响应很慢，如果 ai-service 一直等，前端也一直等，网关也一直等，调用链上的每一层都会被拖住。

第三，重试会放大等待时间。

假设：

```text
单次模型请求 timeout = 30 秒
最大重试 2 次
还有 fallback 1 次
```

如果不做总超时控制，最坏情况可能变成：

```text
主模型第 1 次等 30 秒
主模型第 2 次等 30 秒
主模型第 3 次等 30 秒
fallback 再等 30 秒
总共接近 120 秒
```

用户不可能愿意等这么久，网关也可能早就断开了。

所以生产系统不能只设置“单次超时”，还要设置“总超时预算”。

### 3. 常见的几种超时

#### 连接超时

连接超时关注的是：

```text
能不能在规定时间内建立连接。
```

比如客户端想连模型服务，但网络不通、DNS 慢、服务端端口不可达，就会卡在连接阶段。

连接超时通常应该比较短。

#### 读取超时

读取超时关注的是：

```text
连接已经建立，但服务端迟迟不返回数据。
```

大模型调用最常见的是读取超时。

请求已经发出去了，服务端可能正在推理，但超过你能接受的时间，还没返回内容。

#### 单次请求超时

单次请求超时是一次下游调用自己的 timeout。

本项目已有：

```text
REQUEST_TIMEOUT_SECONDS=30
```

它控制的是 OpenAI-compatible SDK 一次请求最多等多久。

它解决的问题是：

```text
单次模型调用不能一直挂住。
```

#### 总超时

总超时是整条业务链路的最大等待时间。

本节新增：

```text
LLM_TOTAL_TIMEOUT_SECONDS=45
```

它解决的问题是：

```text
一次 LLM 操作，包括重试和 fallback 在内，不能超过整体可接受时间。
```

单次超时和总超时不是重复配置。
它们管的是不同层次。

### 4. 为什么不能简单把 timeout 调大

很多初学者遇到超时，第一反应是：

```text
那我把 30 秒改成 120 秒不就好了？
```

这在生产系统里通常不是好办法。

因为 timeout 变大之后：

```text
用户等待更久
接口资源占用更久
故障恢复更慢
网关更容易先断开
排查问题更困难
系统吞吐下降
失败反馈变慢
```

超时的目的不是让系统“尽量等到成功”。

超时的真正目的有两个：

```text
保护用户体验
保护系统资源
```

所以生产系统通常会做平衡：

```text
单次请求给合理时间
整体请求给总预算
预算不足时不再继续重试或 fallback
快速失败，并返回清晰错误
```

### 5. 超时和重试的关系

重试能提高成功率，但也会消耗时间。

假设：

```text
总预算：45 秒
单次请求超时：30 秒
第一次请求已经用了 30 秒
下一次重试还要最多再等 30 秒
```

这时就不应该再重试。

因为剩余时间只有：

```text
45 - 30 = 15 秒
```

而下一次重试最多可能需要：

```text
重试等待间隔 + 单次请求超时
0.2 + 30 = 30.2 秒
```

预算不够。

所以本节的判断逻辑是：

```text
剩余时间 >= 下一次调用可能需要的时间，才允许继续。
```

这个逻辑看起来保守，但生产系统里保守是有价值的。

### 6. 超时和 fallback 的关系

fallback 也不是免费的。

fallback 意味着：

```text
主模型失败后，再调用备用模型。
```

如果主模型已经耗掉了大量时间，再调用备用模型可能会让用户等太久。

比如：

```text
总预算 45 秒
主模型已经耗时 44 秒
备用模型单次 timeout 30 秒
```

这时 fallback 理论上可能成功，但不应该再执行。

因为它最多还会让用户多等 30 秒。

正确做法是：

```text
记录主模型失败
记录 fallback 被总超时预算拦截
返回明确的 LLM_TOTAL_TIMEOUT_EXCEEDED
```

### 7. 阶段超时

真实 AI 应用通常不是只有 LLM。

一次智能客服请求可能包含：

```text
接收用户请求
权限校验
RAG 检索
rerank
调用 LLM
tool calling
调用 Java 服务
模型总结
返回前端
```

每个阶段都可以有自己的超时。

例如：

```text
RAG 检索最多 2 秒
rerank 最多 3 秒
Java 订单查询最多 2 秒
LLM 单次调用最多 30 秒
整体 AI 请求最多 45 秒
```

阶段超时关注局部，整体超时关注端到端。

本节先只做 LLM 操作级总超时，后续再继续扩展到 SSE、Agent、RAG 和工具调用。

## 本节主题系统讲解

### 1. 本项目原来的问题

第 14 节之后，项目已经有了应用层重试：

```text
模型调用失败
-> 判断错误是否可重试
-> 判断重试次数是否用完
-> 等待一小段时间
-> 再次调用同一个模型
```

项目也已经有 fallback：

```text
主模型失败
-> 判断是否允许 fallback
-> 切备用模型
-> 再调用一次
```

但是缺少一个总控制：

```text
整条 LLM 操作最多能花多久？
```

如果没有这个控制，重试和 fallback 都各自看起来合理，但叠加起来就可能让一次请求变得过长。

这就是生产系统常见的问题：

```text
每个局部策略都是对的，组合起来却让整体体验变差。
```

### 2. 本节新增的总超时预算放在哪里

本节新增的判断器放在：

```text
app/core/llm_timeout.py
```

它属于 core 层，因为它不是具体的 OpenAI SDK 调用，也不是 FastAPI router。

它只回答一个问题：

```text
从当前已经消耗的时间看，是否还允许进入下一阶段？
```

它不负责：

```text
真正睡眠
真正调用模型
真正切换模型
真正返回 HTTP 响应
```

这些仍然由 `LLMChatService` 负责。

这样拆分的好处是：

```text
规则集中
容易测试
LLM service 只负责编排
后续 Agent、RAG、Tool 也可以借鉴同样模式
```

### 3. 本节总超时判断的核心公式

本节的判断公式是：

```text
remaining_seconds = total_timeout_seconds - elapsed_seconds
required_seconds = next_delay_seconds + request_timeout_seconds

如果 remaining_seconds >= required_seconds：
    允许继续
否则：
    阻止继续
```

其中：

```text
elapsed_seconds：从本次 LLM 操作开始到现在，已经用了多久
total_timeout_seconds：本次 LLM 操作总预算
request_timeout_seconds：下一次模型调用最多可能占用多久
next_delay_seconds：重试前需要等待的时间，fallback 没有等待就是 0
```

为什么 `required_seconds` 要加上 `request_timeout_seconds`？

因为下一次调用不是一定马上成功。
它最坏可能再次等到单次请求超时。

生产系统做预算时，不能只按最好情况设计，而要考虑合理的最坏情况。

### 4. 为什么使用可注入时间源

本节修改了 `LLMChatService` 的构造函数，允许传入 `time_func`。

真实运行时使用：

```text
perf_counter
```

测试时使用：

```text
FakeClock
```

这样做不是为了炫技。

原因是：超时逻辑如果依赖真实时间，测试会很慢、很不稳定。

比如你真的等 30 秒再测试预算不足，那每次测试都要浪费 30 秒。

使用 fake clock 可以让测试瞬间模拟：

```text
第一次调用已经耗时 30 秒
主模型已经耗时 44 秒
```

这就是生产代码可测试性的一种设计方式：

```text
把不可控的外部因素变成可注入依赖。
```

### 5. retry 前为什么检查预算

retry 的判断顺序是：

```text
先判断错误是否可重试
再判断重试次数是否允许
再判断总超时预算是否允许
最后才 sleep 并发起下一次调用
```

不能把预算判断放在 sleep 后面。

因为如果预算已经不够，还 sleep 一下，只会浪费剩余时间。

正确顺序是：

```text
决定要不要继续之前，先算预算。
```

### 6. fallback 前为什么检查预算

fallback 的判断顺序是：

```text
主模型失败
-> 判断错误是否允许 fallback
-> 判断成本控制是否允许 fallback
-> 判断总超时预算是否允许 fallback
-> 真正调用 fallback 模型
```

成本控制和超时控制是两个不同维度：

```text
成本控制：这次调用还值不值得花钱
超时控制：这次调用还来不来得及
```

一个控制钱，一个控制时间。

两者都应该满足，fallback 才能继续。

### 7. 为什么新增错误码 `LLM_TOTAL_TIMEOUT_EXCEEDED`

原来单次模型请求超时会映射为：

```text
LLM_TIMEOUT
```

本节新增的是：

```text
LLM_TOTAL_TIMEOUT_EXCEEDED
```

这两个错误码含义不同。

`LLM_TIMEOUT` 表示：

```text
某一次模型调用本身超时了。
```

`LLM_TOTAL_TIMEOUT_EXCEEDED` 表示：

```text
系统判断如果继续重试或 fallback，会超过整条 LLM 操作的总时间预算。
```

它不一定意味着当前这一次请求已经超过总预算。
它也可能表示：

```text
继续下一步的风险太大，所以提前停止。
```

这叫预算式保护。

## 本节代码讲解

### 1. `LLM_TOTAL_TIMEOUT_SECONDS`

配置文件新增：

```python
llm_total_timeout_seconds: float = Field(default=45.0, gt=0)
```

含义：

```text
一次 LLM 操作的总时间预算，默认 45 秒。
```

为什么默认是 45 秒？

因为当前单次模型请求默认 30 秒。
总预算 45 秒意味着：

```text
允许一次正常模型调用有足够时间
允许快速失败后做一次短路径恢复
不允许多个 30 秒调用叠加成 90 秒或 120 秒
```

这不是生产绝对标准，只是当前学习项目的保守默认值。

### 2. `LLMTimeoutBudgetDecision`

这个对象表达一次预算判断结果。

核心字段：

```text
allowed：是否允许继续
reason：允许或拒绝的原因
phase：当前判断的是 retry 还是 fallback
elapsed_seconds：已经耗时
remaining_seconds：剩余预算
required_seconds：下一步预计至少要预留的预算
next_delay_seconds：重试前等待时间
```

这里不用普通 `dict`，而是用 dataclass，是为了让结果结构清晰、字段固定、测试更容易。

### 3. `build_llm_timeout_budget_decision`

这个函数是本节规则核心。

它不关心模型名、不关心 prompt、不关心用户问题。

它只关心：

```text
总预算
已经消耗多久
下一步最多可能再消耗多久
```

这样能避免日志或测试里混入用户输入、API key 等敏感信息。

### 4. `LLMChatService` 的 `time_func`

服务构造函数新增 `time_func`。

真实业务不需要传，默认使用高精度计时：

```python
self._time_func = time_func or perf_counter
```

测试可以传 fake clock。

这让测试可以模拟耗时，而不用真的等待。

### 5. retry 接入点

retry 决策通过后，真正 sleep 之前，新增预算判断：

```text
错误可重试
-> 次数没超
-> 总预算允许
-> sleep
-> 再调模型
```

如果预算不足，抛出：

```text
LLM_TOTAL_TIMEOUT_EXCEEDED
```

这样避免“明知道来不及还继续重试”。

### 6. fallback 接入点

fallback 决策通过后，真正调用备用模型之前，新增预算判断：

```text
错误允许 fallback
-> 成本允许 fallback
-> 总预算允许 fallback
-> 调备用模型
```

如果预算不足，不会调用备用模型。

测试里会验证：

```text
completions.calls 只有主模型一次
```

这能证明 fallback 被预算拦截了。

## 常见误区

### 误区 1：把单次 timeout 当成总 timeout

错误理解：

```text
REQUEST_TIMEOUT_SECONDS=30，所以用户最多等 30 秒。
```

实际不一定。

如果还有重试和 fallback，总等待可能超过 30 秒。

所以需要总预算：

```text
LLM_TOTAL_TIMEOUT_SECONDS
```

### 误区 2：超时了就一定重试

超时通常是可重试错误，但不代表一定要重试。

还要看：

```text
重试次数
剩余时间
成本预算
是否幂等
是否会造成下游压力
```

### 误区 3：fallback 一定比失败好

fallback 能提升可用性，但它也会增加时间、成本和复杂度。

如果用户已经等了很久，再 fallback 可能不是体验优化，而是体验变差。

### 误区 4：timeout 越大越稳定

timeout 变大只会让系统更愿意等待。
它不等于更稳定。

真正的稳定来自：

```text
合理超时
有限重试
fallback
限流
降级
可观测性
明确错误码
```

### 误区 5：测试超时逻辑一定要真的等待

不应该真的等 30 秒、45 秒去测试超时预算。

更好的做法是注入 fake clock。

这也是本节引入 `time_func` 的原因。

## 本节关键测试说明

本节测试只覆盖关键边界，不真实调用模型。

### 1. 预算规则测试

`tests/test_llm_timeout.py` 验证：

```text
剩余时间够时允许 retry
剩余时间不够时阻止 retry
剩余时间不够时阻止 fallback
日志字段不包含 prompt 和 secret
```

### 2. 服务层测试

`tests/test_llm_service.py` 验证：

```text
预算不足时不会继续重试
预算不足时不会调用 fallback 模型
日志不会泄露用户原始问题
```

这些测试防止未来改代码时把总超时预算绕过去。

## 手动测试命令

本节按省 token 模式，我没有自动跑测试。你可以在 Windows PowerShell 里运行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests/test_llm_timeout.py tests/test_llm_service.py -q
uv run pytest tests/test_config.py tests/test_config_safety.py -q
```

如果你想跑全量测试：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest -q
```

## 本节练习

### 练习 1：判断是否应该 retry

题目：

```text
总预算 45 秒，单次请求 timeout 30 秒。
主模型第一次调用已经耗时 30 秒。
下一次 retry 前要等待 0.2 秒。
此时应该 retry 吗？为什么？
```

参考答案：

不应该 retry。

因为剩余预算是：

```text
45 - 30 = 15 秒
```

下一次 retry 需要预留：

```text
0.2 + 30 = 30.2 秒
```

15 秒小于 30.2 秒，所以预算不够。

### 练习 2：判断是否应该 fallback

题目：

```text
总预算 45 秒，单次请求 timeout 30 秒。
主模型已经耗时 44 秒后失败。
备用模型可能还要最多等 30 秒。
此时应该 fallback 吗？为什么？
```

参考答案：

不应该 fallback。

因为剩余预算只有：

```text
45 - 44 = 1 秒
```

而 fallback 模型最多可能需要 30 秒。

继续 fallback 会让一次请求大概率超过整体可接受时间。

### 练习 3：解释两个配置的区别

题目：

```text
REQUEST_TIMEOUT_SECONDS 和 LLM_TOTAL_TIMEOUT_SECONDS 有什么区别？
```

参考答案：

`REQUEST_TIMEOUT_SECONDS` 是单次模型请求的超时。

`LLM_TOTAL_TIMEOUT_SECONDS` 是一次 LLM 操作的总时间预算，包含主模型调用、retry 等待、retry 调用，以及 fallback 判断和调用。

一个管单次调用，一个管整条 LLM 操作。

### 练习 4：为什么测试使用 fake clock

题目：

```text
为什么本节测试不真的 sleep 30 秒，而是注入 fake clock？
```

参考答案：

因为真实等待会让测试变慢、不稳定，也会浪费开发时间。

fake clock 可以瞬间模拟“已经耗时 30 秒”或“已经耗时 44 秒”，让超时预算逻辑可测试、可重复、速度快。

## 自测问题

### 自测 1：超时治理解决的核心问题是什么？

参考答案：

超时治理解决的是“系统最多愿意等待多久，以及在剩余时间不足时是否应该停止继续 retry 或 fallback”的问题。它保护用户体验和服务资源。

### 自测 2：为什么总预算不足时不应该继续 retry？

参考答案：

因为下一次 retry 可能再次等到单次请求超时。如果剩余预算不足以覆盖等待间隔和下一次请求，就会让整条请求拖得过久。

### 自测 3：`LLM_TIMEOUT` 和 `LLM_TOTAL_TIMEOUT_EXCEEDED` 有什么区别？

参考答案：

`LLM_TIMEOUT` 表示某一次模型调用超时。

`LLM_TOTAL_TIMEOUT_EXCEEDED` 表示系统判断继续下一步会超过总超时预算，因此提前停止。

### 自测 4：为什么 timeout 不是越大越好？

参考答案：

timeout 越大，系统等待越久，资源占用越久，失败反馈越慢。生产系统要在成功率、用户体验和资源保护之间平衡。

### 自测 5：fallback 前应该检查哪些条件？

参考答案：

至少要检查：

```text
错误是否允许 fallback
备用模型是否和主模型不同
成本预算是否允许
总超时预算是否允许
```

都满足后才应该调用备用模型。

## 本节小结

本节把 LLM 链路从“单次请求有 timeout”升级为“整条 LLM 操作有总时间预算”。

现在项目里的调用边界更清晰：

```text
REQUEST_TIMEOUT_SECONDS 管单次模型调用
LLM_MAX_RETRIES 管最多额外重试几次
LLM_TOTAL_TIMEOUT_SECONDS 管整条 LLM 操作最多能花多久
LLM fallback 只有在错误、成本、时间都允许时才执行
```

这就是生产化能力里的一个重要思想：

```text
局部策略要服从整体预算。
```
