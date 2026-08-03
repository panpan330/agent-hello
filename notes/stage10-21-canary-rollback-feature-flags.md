# 阶段 10 第 21 节：灰度发布、回滚与配置开关

## 本节定位

上一节我们学习了生产监控指标与告警。

监控和告警解决的是：

```text
上线后怎么发现系统正在变慢、变贵、失败变多或安全风险升高。
```

这一节继续学习发布控制：

```text
新模型、新 Prompt、新 RAG 参数、新路由策略、新安全规则，应该怎么小范围放量、观察、扩大或回滚。
```

真实 AI 应用里，很多改动不会让接口立刻报错，但会影响效果：

```text
新模型更贵。
新 Prompt 回答更啰嗦。
新 RAG 参数召回更多噪音。
新 rerank 策略让引用错文档。
新安全规则误伤正常用户。
新路由策略把简单任务发给昂贵模型。
```

所以 AI 应用更需要灰度和回滚。

本节不接真实发布平台，不启动 Docker，不真实调用模型。

## 本节学习目标

- 理解什么是灰度发布。
- 理解为什么 AI 应用更需要灰度。
- 理解模型、Prompt、RAG 参数、路由策略、安全策略如何灰度。
- 理解 feature flag、配置开关、kill switch。
- 理解 stable version 和 candidate version。
- 理解按用户/租户/百分比放量的基本思路。
- 理解 guardrail metric 和回滚决策。
- 看懂本项目新增的 rollout policy 和 rollback decision 模型。

## 本节新增和修改

- 新增 `projects/ai-service/app/core/release_control.py`
  - `FeatureFlagSpec`
  - `RolloutPolicy`
  - `RolloutAssignment`
  - `RollbackSignal`
  - `RollbackDecision`
  - 默认灰度策略。
  - 稳定百分比分桶。
  - 灰度版本分配。
  - 回滚决策。
- 新增 `projects/ai-service/tests/test_release_control.py`
  - 覆盖默认策略、状态和百分比校验、内部灰度、租户分层、稳定分桶、critical 回滚、warning 暂停。
- 更新学习进度。

## 一句话先讲透

灰度发布不是“直接把新版本上线”，而是让少量可控流量先使用 candidate，并用监控、评测和 guardrail 判断继续放量、暂停还是回滚。

## 基础知识铺垫

### 1. 什么是发布

发布就是把某个改动交给用户使用。

传统后端发布可能是：

```text
部署新 jar 包
部署新 Docker 镜像
上线新接口
切换数据库字段
```

AI 应用的发布不只有代码。

还包括：

```text
换模型
改 Prompt
改 RAG top_k
改 score_threshold
换 rerank 模型
改模型路由策略
改工具 schema
改安全规则
改成本控制阈值
```

这些都可能影响用户体验。

### 2. 什么是灰度发布

灰度发布就是：

```text
先让一小部分流量使用新版本，观察没有问题后再逐步扩大。
```

例如：

```text
0%：关闭
内部用户：只给团队自己试
5%：小流量用户试
25%：扩大流量
50%：半量
100%：全量
```

灰度的核心不是“慢慢上线”这么简单。

它的核心是：

```text
可控制范围
可观察效果
可快速停止
可回滚稳定版本
```

### 3. 为什么 AI 应用更需要灰度

传统后端很多问题能通过自动化测试发现。

例如：

```text
接口字段错了。
数据库插入失败。
权限校验没走。
```

AI 应用很多问题更隐蔽。

例如：

```text
回答风格变差。
引用来源不稳定。
模型更容易编造。
成本增加 30%。
安全规则误伤正常请求。
fallback 触发变多。
RAG no-context 变多。
```

这些问题可能不会让接口失败，但会影响质量和成本。

所以 AI 应用改动应该更谨慎。

### 4. 什么是 stable version

stable version 是当前稳定版本。

它可能是：

```text
当前稳定模型
当前稳定 Prompt
当前稳定 RAG 参数
当前稳定安全规则
当前稳定路由策略
```

它的作用是：

```text
灰度失败时可以回去。
```

如果没有 stable version，回滚就没有目标。

### 5. 什么是 candidate version

candidate version 是候选新版本。

它可能是：

```text
新模型
新 Prompt
新 RAG 参数
新路由策略
新安全策略
```

candidate 不是直接全量上线。

它要先经过：

```text
内部验证
自动化评估
小流量灰度
监控观察
逐步扩大
```

### 6. 什么是 feature flag

feature flag 也叫功能开关。

它是一个配置项，用来控制某个能力是否启用。

例如：

```text
llm_model_canary_enabled=false
rag_parameter_canary_enabled=false
safety_policy_canary_enabled=false
```

好处是：

```text
不需要重新部署代码，也能打开或关闭某个能力。
```

### 7. 什么是 kill switch

kill switch 是紧急关闭开关。

如果灰度出现严重问题，可以立刻关闭。

例如：

```text
新模型失败率过高 -> 关闭模型灰度
新 RAG 参数引用错误 -> 关闭 RAG 参数灰度
新安全规则误伤用户 -> 关闭安全策略灰度
```

kill switch 的目标是：

```text
快速止损。
```

### 8. 什么是 guardrail metric

guardrail metric 是灰度期间必须盯住的保护指标。

例如模型灰度要看：

```text
llm.failures
http.server.duration
llm.estimated_cost
```

RAG 参数灰度要看：

```text
rag.retrieval.empty_results
rag.citation.failures
http.server.duration
```

安全规则灰度要看：

```text
safety.blocks
http.server.requests
```

guardrail 的意思是：

```text
如果这些指标越过危险阈值，就不能继续放量。
```

### 9. 什么是回滚

回滚就是把 candidate 停掉，恢复 stable。

回滚不丢人。

回滚是生产系统的正常能力。

真正危险的是：

```text
明知道新版本有问题，却没有办法快速恢复。
```

AI 应用中可以回滚：

```text
模型版本
Prompt 版本
RAG 参数
rerank 策略
路由策略
安全规则
成本阈值
```

## 本节主题系统讲解

### 1. 本项目已有的可灰度对象

当前项目已经有很多可以被灰度控制的能力。

模型：

```text
llm_model
llm_fast_model
llm_balanced_model
llm_strong_model
llm_default_route_tier
```

fallback：

```text
llm_enable_fallback
llm_fallback_model
llm_fallback_tier
```

成本控制：

```text
llm_enable_cost_control
llm_max_input_tokens_per_request
llm_max_total_tokens_per_request
llm_max_estimated_cost_per_request
```

限流：

```text
rate_limit_enabled
rate_limit_ai_requests_per_window
rate_limit_tool_requests_per_window
```

RAG：

```text
qdrant_collection_name
milvus_collection_name
embedding_model
rerank_model
```

安全：

```text
Prompt Injection 规则
敏感输出脱敏规则
工具白名单
写操作确认
```

这些都不应该随便全量改。

### 2. 本节默认灰度策略

本节新增：

```text
build_default_rollout_policies()
```

默认定义 3 类灰度：

```text
llm-balanced-model-canary
rag-parameter-canary
safety-policy-canary
```

它们分别代表：

```text
模型灰度
RAG 参数灰度
安全策略灰度
```

每个策略都有：

```text
stable_version
candidate_version
rollout_percentage
feature_flags
guardrail_metric_names
rollback_hint
```

### 3. 为什么先从 internal 开始

默认模型灰度是：

```text
status=internal
rollout_percentage=0
enabled_tenant_tiers=["internal"]
```

这表示：

```text
先给内部测试用户使用，不给普通用户。
```

原因是：

```text
内部用户能接受不稳定。
内部用户能反馈问题。
内部阶段能发现明显错误。
```

### 4. 百分比灰度怎么做

百分比灰度需要稳定分桶。

不能每次请求随机。

如果每次随机，用户这次命中新版本，下次又回旧版本，体验会混乱。

本节使用：

```text
stable_percentage_bucket()
```

它根据：

```text
policy.name + subject_id
```

算出 0 到 99 的稳定 bucket。

如果：

```text
bucket < rollout_percentage
```

就使用 candidate。

否则使用 stable。

### 5. 为什么要支持 tenant_tier

灰度不一定只按百分比。

还可以按租户层级：

```text
internal
beta
public
enterprise
```

例如：

```text
先给 internal
再给 beta
最后给 public
```

这样比直接随机给所有用户更可控。

### 6. 回滚决策怎么做

本节新增：

```text
build_rollback_decision()
```

它根据 guardrail signals 决定：

```text
continue
hold
rollback
```

含义：

```text
continue：继续灰度。
hold：暂停扩大，先观察或排查。
rollback：立即回滚到 stable。
```

当前最小规则：

```text
有 critical signal -> rollback
有 warning signal -> hold
没有 signal -> continue
```

### 7. 什么情况下应该回滚

典型回滚条件：

```text
核心接口 5xx 明显升高
P95/P99 延迟明显升高
LLM 失败率升高
fallback 异常增加
成本超过阈值
RAG citation failures 增加
RAG no-context 增加
安全误伤增加
P0 eval regression
用户投诉集中出现
```

AI 应用尤其要注意：

```text
质量退化不一定体现在 5xx。
```

所以要结合：

```text
监控指标
自动化评估
Bad Case
人工反馈
```

## 本节代码讲解

### 1. `FeatureFlagSpec`

它表示一个配置开关。

核心字段：

```text
name
enabled
description
owner
kill_switch
```

`kill_switch=True` 表示它可以作为紧急关闭开关。

### 2. `RolloutPolicy`

它表示一条灰度策略。

核心字段：

```text
name
target
status
stable_version
candidate_version
rollout_percentage
enabled_tenant_tiers
feature_flags
guardrail_metric_names
rollback_hint
```

它会校验：

```text
disabled 必须 0%
rolled_back 必须 0%
full 必须 100%
```

避免出现语义不一致的策略。

### 3. `assign_rollout_version()`

这个函数决定某个请求使用 stable 还是 candidate。

判断顺序：

```text
disabled / rolled_back -> stable
tenant_tier 不允许 -> stable
internal -> candidate
full -> candidate
canary -> 按稳定 bucket 判断
```

它返回：

```text
RolloutAssignment
```

里面有：

```text
selected_version
candidate_selected
reason
rollout_percentage
```

### 4. `stable_percentage_bucket()`

它用 SHA-256 算一个稳定 bucket。

同一个：

```text
policy.name + subject_id
```

每次结果一样。

这样用户不会在 stable 和 candidate 之间来回跳。

### 5. `RollbackSignal`

它表示一个回滚信号。

例如：

```text
metric_name=llm.failures
current_value=0.2
threshold=0.1
severity=critical
```

意思是：

```text
LLM 失败率超过阈值，属于严重问题。
```

### 6. `RollbackDecision`

它表示最终回滚决策。

核心字段：

```text
action
reason
policy_name
stable_version
candidate_version
blocking_signals
```

如果：

```text
action=rollback
```

就应该关闭 candidate，恢复 stable。

## 常见误区

### 误区 1：灰度就是随机给一部分用户

不完整。

灰度要稳定分桶、可观察、可停止、可回滚。

### 误区 2：AI 应用只要代码不报错就能全量

不对。

AI 应用可能功能不报错，但回答质量、引用、成本、安全都退化。

### 误区 3：配置开关越多越好

不对。

开关太多会让系统复杂。

开关应该服务明确风险，例如模型切换、RAG 参数、安全策略、成本控制。

### 误区 4：warning 也要立刻回滚

不一定。

warning 通常先 hold，暂停扩大并观察。

critical 才应该快速回滚。

### 误区 5：回滚就是失败

不对。

能快速回滚说明系统具备生产控制能力。

不能回滚才危险。

## 当前项目边界

本节已经具备：

```text
Feature flag 模型
Kill switch 标识
Rollout policy
Stable / candidate version
按 tenant_tier 控制
按百分比稳定分桶
Guardrail metric
Rollback signal
Rollback decision
关键测试
```

尚未深入：

```text
真实配置中心
数据库保存灰度策略
后台页面管理开关
真实流量分配
CI/CD 发布平台
自动执行回滚
灰度指标实时看板
```

这些适合完整项目部署阶段继续做。

## 练习题

### 练习 1：下面哪些 AI 改动适合灰度？

题目：

```text
A. 替换主模型
B. 修改 RAG top_k
C. 修改 Prompt
D. 调整安全拦截规则
E. 修复 README 错别字
```

参考答案：

```text
A、B、C、D 适合灰度。

它们都可能影响质量、成本或安全。

E 通常不需要灰度。
```

### 练习 2：为什么百分比灰度要稳定分桶？

参考答案：

```text
因为同一个用户应该稳定命中同一个版本。
如果每次请求随机，用户体验会在 stable 和 candidate 之间来回切换，问题也更难排查。
```

### 练习 3：模型灰度期间应该看哪些 guardrail？

参考答案：

```text
至少看 LLM 失败率、HTTP 延迟、fallback 次数、token 和成本、P0 eval regression、用户反馈。
```

### 练习 4：什么情况下应该回滚安全策略灰度？

参考答案：

```text
如果 safety.blocks 异常升高并且确认误伤正常用户，或者安全样本评测失败，或者用户核心路径被安全规则阻断，就应该回滚到稳定安全策略。
```

## 自测问题

### 自测 1：stable version 和 candidate version 的区别是什么？

参考答案：

```text
stable version 是当前稳定版本，用于正常流量和回滚目标。
candidate version 是候选新版本，只应该通过内部、灰度或配置开关逐步放量。
```

### 自测 2：feature flag 和 kill switch 的关系是什么？

参考答案：

```text
feature flag 是功能开关。
kill switch 是用于紧急关闭风险能力的特殊开关。
```

### 自测 3：为什么 AI 应用灰度要结合 Eval 和 Monitoring？

参考答案：

```text
Monitoring 能发现线上运行风险，例如错误率、延迟、成本、安全阻断。
Eval 能发现质量退化，例如路由、引用、字段提取、安全样本失败。
AI 应用很多问题不会表现为 5xx，所以两者都需要。
```

### 自测 4：hold 和 rollback 有什么区别？

参考答案：

```text
hold 是暂停扩大灰度，继续观察或排查。
rollback 是停止 candidate，恢复 stable。
warning 通常先 hold，critical 通常 rollback。
```

### 自测 5：为什么回滚能力很重要？

参考答案：

```text
因为新模型、新 Prompt、新 RAG 参数和新安全规则都可能上线后才暴露问题。
有回滚能力才能快速止损，减少用户影响、成本损失和安全风险。
```

## 本节手动验证命令

本节不需要打开 VMware Ubuntu。

本节不需要真实调用大模型。

按当前约定，测试由你手动执行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests/test_release_control.py -q
```

## 本节小结

本节把发布控制从“改了就上线”推进到“可灰度、可观察、可暂停、可回滚”。

你现在应该能讲清：

```text
什么是灰度发布。
为什么 AI 应用更需要灰度。
feature flag 和 kill switch 的作用。
stable/candidate 的区别。
为什么百分比灰度要稳定分桶。
guardrail metric 如何辅助回滚决策。
什么情况下 continue、hold、rollback。
```

下一节进入：

```text
阶段 10 第 22 节：SLO / SLA / Runbook
```
