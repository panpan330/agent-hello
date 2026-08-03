# 阶段 10 第 20 节：生产监控指标与告警基础

## 本节定位

这一节学习 AI 应用生产监控指标与告警基础。

前面我们已经学习过：

```text
trace_id
span
event
metric
LLM 日志安全
token 成本统计
请求耗时拆解
fallback
限流
重试
超时
SSE 生产化
Prompt Injection 防护
自动化评估
Bad Case 回归
```

这些能力分别解决了不同问题。

本节要解决的是：

```text
系统上线后，怎么知道它是否正在变慢、变贵、变不稳定、变不安全，什么时候需要通知人处理。
```

本节不安装 Prometheus、Grafana、ELK、OpenTelemetry Collector，也不接真实云监控。

本节先做最重要的基础：

```text
定义生产指标目录和最小告警规则。
```

## 本节学习目标

- 理解监控、日志、Tracing、Eval 的区别。
- 理解指标是什么。
- 理解 counter、gauge、histogram 的区别。
- 理解请求量、错误率、延迟、P95/P99。
- 理解 AI 应用除了 HTTP 指标，还要监控 LLM、RAG、Tool、Java、成本、安全和限流。
- 理解低基数标签和高基数标签。
- 理解什么是告警，什么是有效告警。
- 理解为什么不能为每个小波动都告警。
- 看懂本项目新增的生产监控指标目录和告警规则模型。

## 本节新增和修改

- 新增 `projects/ai-service/app/core/production_monitoring.py`
  - `ProductionMetricSpec`
  - `AlertRuleSpec`
  - `MonitoringCatalog`
  - 默认生产监控指标目录。
  - 默认告警规则。
  - 低基数标签校验。
  - 告警条件判断。
- 新增 `projects/ai-service/tests/test_production_monitoring.py`
  - 覆盖默认指标域、告警规则、低基数标签、防噪音告警、告警阈值判断。
- 更新学习进度。

## 一句话先讲透

生产监控不是把所有日志都变成告警，而是用少量稳定指标观察系统健康，并只在用户体验、成本、安全或核心能力真正有风险时通知人处理。

## 基础知识铺垫

### 1. 什么是监控

监控就是持续观察系统运行状态。

它关注的问题是：

```text
系统现在还好吗？
有没有变慢？
有没有变贵？
有没有失败变多？
有没有外部依赖异常？
有没有安全风险增加？
```

监控不是等用户投诉才知道问题。

好的监控应该让你在这些情况出现时及时发现：

```text
接口 5xx 升高
请求延迟变高
模型调用失败率升高
fallback 大量触发
RAG 无结果突然变多
token 成本快速上涨
限流拒绝大量出现
安全拦截突然升高
Java 业务服务调用变慢
```

### 2. 监控和日志的区别

日志记录的是一条条事件。

例如：

```text
trace_id=abc
route=/chat
model=qwen-plus
elapsed_ms=1200
status=success
```

日志适合排查：

```text
这一次请求发生了什么？
为什么这个用户失败了？
哪个错误码出现了？
```

监控指标是聚合数据。

例如：

```text
过去 15 分钟 /chat 请求量 3000
过去 15 分钟 5xx 比例 6%
过去 15 分钟 p95 延迟 5800ms
过去 1 小时 LLM 估算成本 12 美元
```

指标适合回答：

```text
整体趋势是否正常？
系统有没有普遍性问题？
是否需要告警？
```

一句话：

```text
日志看单次细节，监控看整体趋势。
```

### 3. 监控和 Tracing 的区别

Tracing 关注一次请求的链路。

例如：

```text
HTTP request
  -> request validation
  -> RAG retrieval
  -> rerank
  -> LLM call
  -> tool call
  -> Java client
```

它适合排查：

```text
这一次请求慢在哪里？
哪个 span 报错？
调用链在哪断了？
```

监控关注大量请求的聚合状态。

例如：

```text
过去 15 分钟 LLM p95 延迟是否升高？
过去 30 分钟 RAG no-context 是否突然增加？
过去 1 小时 fallback 次数是否异常？
```

一句话：

```text
Tracing 看一条链路，Monitoring 看整体健康。
```

### 4. 监控和 Eval 的区别

Eval 关注效果质量。

例如：

```text
固定评测集 pass_rate 是否下降？
RAG 引用是否正确？
Agent 路由是否走对？
安全样本是否拒绝？
```

监控关注线上运行状态。

例如：

```text
请求量、错误率、延迟、成本、失败率、限流、安全拦截。
```

Eval 不一定实时。

它可能在：

```text
提交代码前
合并 PR 前
发布前
每天定时
```

监控通常是持续的。

它观察系统正在发生什么。

一句话：

```text
Eval 判断质量有没有退化，Monitoring 判断线上运行是否健康。
```

### 5. 什么是指标

指标是可以被持续采集和聚合的数字。

例如：

```text
请求数
失败数
延迟
token 数
成本
fallback 次数
限流拒绝次数
安全阻断次数
RAG 无结果次数
```

指标通常包含：

```text
name：指标名
type：指标类型
unit：单位
labels：标签
description：说明
```

例如：

```text
name=http.server.duration
type=histogram
unit=ms
labels=route, method, status_code_class
```

### 6. Counter、Gauge、Histogram

Counter 是只增不减的计数器。

适合：

```text
请求总数
失败总数
token 总数
fallback 总数
安全阻断总数
```

Gauge 是当前值。

适合：

```text
当前队列长度
当前连接数
当前缓存大小
当前熔断器状态
```

Histogram 是分布。

适合：

```text
请求耗时
LLM 调用耗时
RAG 检索耗时
Java 调用耗时
```

为什么延迟不用 counter？

因为你不只关心总耗时，还关心分布：

```text
大多数请求多快？
最慢的 5% 多慢？
最慢的 1% 多慢？
```

这就要用 histogram。

### 7. 什么是 P95 和 P99

P95 表示：

```text
95% 的请求都不超过这个耗时。
```

如果 `/chat` P95 是 5000ms，意思是：

```text
100 次请求里，大约 95 次在 5 秒内完成，最慢的 5 次可能更慢。
```

P99 表示：

```text
99% 的请求都不超过这个耗时。
```

P95/P99 比平均值更适合看用户体验。

因为平均值可能被掩盖。

例如：

```text
99 个请求 100ms
1 个请求 30s
平均值看起来可能还能接受
但那个 30s 用户体验非常差
```

### 8. 什么是低基数标签

标签用于把指标分组。

例如：

```text
route=/chat
method=POST
status_code_class=2xx
model=qwen-plus
operation=chat
```

低基数标签表示取值数量有限。

例如：

```text
route：接口数量有限
method：GET/POST/PUT/DELETE
status_code_class：2xx/4xx/5xx
model：模型数量有限
tool_name：工具数量有限
```

高基数标签表示取值数量可能非常多。

例如：

```text
trace_id
user_id
order_id
ticket_id
query
prompt
message
email
phone
```

高基数标签不能随便放进 metrics。

否则监控系统会产生海量时间序列，成本高、查询慢，还可能泄露隐私。

所以本节代码禁止这些标签进入指标目录。

### 9. 什么是告警

告警是系统发现风险后通知人处理。

例如：

```text
HTTP 5xx 比例超过 5%
LLM 失败率超过 10%
P95 延迟超过 5 秒
1 小时模型成本超过阈值
RAG no-context 突然升高
安全阻断突然升高
```

告警不是仪表盘。

仪表盘用于观察。

告警用于叫人处理。

如果一个告警经常响，但没人需要处理，它就是噪音。

### 10. 什么是有效告警

有效告警应该满足：

```text
有明确风险
有明确阈值
有持续时间
有严重级别
有排查方向
能减少用户影响、成本失控或安全风险
```

比如：

```text
过去 15 分钟 HTTP 5xx 超过 5%，持续 5 分钟。
```

这比下面这种更有效：

```text
某一次请求失败了，立刻告警。
```

单次失败通常应该进日志和 trace，不一定要告警。

## 本节主题系统讲解

### 1. AI 应用要监控哪些域

本节默认指标目录覆盖 8 个域：

```text
http
llm
rag
tool
java
resilience
cost
safety
```

http：

```text
请求量、错误率、延迟。
```

llm：

```text
模型调用次数、失败次数、模型维度、操作类型。
```

rag：

```text
检索耗时、无结果、引用失败。
```

tool：

```text
工具调用次数、工具失败次数。
```

java：

```text
Python 调 Java 业务服务的耗时和错误。
```

resilience：

```text
fallback、限流拒绝。
```

cost：

```text
token 使用量、估算成本。
```

safety：

```text
Prompt Injection、安全阻断、隐私保护阻断。
```

### 2. 为什么 AI 应用比传统后端多监控项

传统后端通常重点看：

```text
请求量
错误率
延迟
数据库
缓存
队列
CPU/内存
```

AI 应用还要看：

```text
模型调用失败
模型 fallback
token 成本
上下文长度
RAG 检索无结果
RAG 引用失败
工具调用失败
安全阻断
模型输出质量退化
```

因为 AI 应用有更多外部依赖和不确定性。

模型不一定稳定。

RAG 不一定召回正确资料。

Tool Calling 不一定请求正确工具。

成本可能因为 prompt 变长或 retry/fallback 激增而失控。

### 3. 本节默认指标目录

本节新增：

```text
build_default_monitoring_catalog()
```

它定义了 15 个默认指标：

```text
http.server.requests
http.server.duration
llm.calls
llm.failures
llm.fallbacks
llm.tokens
llm.estimated_cost
rag.retrieval.duration
rag.retrieval.empty_results
rag.citation.failures
tool.calls
tool.failures
java.client.duration
rate_limit.rejections
safety.blocks
```

这些不是完整监控平台。

它们是当前项目的最小生产监控地图。

### 4. 本节默认告警规则

本节定义了 6 条默认告警：

```text
High HTTP 5xx rate
High p95 request latency
High LLM failure rate
Cost burn rate high
RAG no-context spike
Safety block spike
```

这些告警分别对应：

```text
服务整体不可用风险
用户体验变差
模型依赖异常
成本失控
知识库/RAG 链路异常
安全风险或规则误伤
```

这比“所有错误都告警”更合理。

### 5. 为什么告警要有 window 和 for_duration

window 表示观察窗口。

例如：

```text
过去 15 分钟
过去 30 分钟
过去 1 小时
```

for_duration 表示持续多久才触发。

例如：

```text
持续 5 分钟
持续 10 分钟
```

为什么需要持续时间？

因为系统可能有瞬时抖动。

如果某一秒失败率高，但下一秒恢复，不一定需要叫人。

告警要避免噪音。

### 6. 为什么有 runbook_hint

告警响了以后，值班的人要知道怎么查。

所以告警规则里要有：

```text
runbook_hint
```

例如 LLM 失败率高时，提示检查：

```text
provider 状态
API key
timeout
rate limit
fallback
```

这能减少“告警响了但不知道干什么”的问题。

### 7. 本节和前面阶段的关系

和 Tracing 的关系：

```text
监控发现整体异常，Tracing 用来追具体请求。
```

和日志安全的关系：

```text
指标标签不能放敏感文本和高基数字段，日志也不能记录敏感正文。
```

和 token 成本的关系：

```text
token_usage 负责估算成本，monitoring 负责把成本变成可观察指标和告警。
```

和 fallback、限流、超时的关系：

```text
这些是稳定性保护动作；监控要观察它们是否频繁触发。
```

和 Eval/Bad Case 的关系：

```text
Eval/Bad Case 发现质量退化，Monitoring 发现线上运行风险。
```

## 本节代码讲解

### 1. `ProductionMetricSpec`

这个模型定义一个生产指标。

核心字段：

```text
name
metric_type
domain
unit
description
labels
```

它会校验：

```text
指标名必须是小写点分格式。
labels 不能包含高基数字段。
labels 必须在低基数白名单中。
```

这样可以防止把 `user_id`、`trace_id`、`query` 这类字段放进指标标签。

### 2. `AlertRuleSpec`

这个模型定义一条告警规则。

核心字段：

```text
name
metric_name
severity
comparator
threshold
window
for_duration
description
runbook_hint
```

它表达的是：

```text
在某个时间窗口里，某个指标满足某个阈值条件，就触发某个级别的告警。
```

### 3. `MonitoringCatalog`

这个模型把指标和告警放在一起。

它会校验：

```text
指标名不能重复。
告警名不能重复。
告警引用的 metric_name 必须存在。
```

这样避免出现：

```text
告警规则写了，但指标不存在。
```

### 4. `build_default_monitoring_catalog()`

这个函数返回当前项目推荐的最小生产监控目录。

它不采集真实数据。

它只是定义：

```text
将来应该采集哪些指标。
哪些指标应该进入告警。
```

这一步很重要。

因为如果没有指标设计，后续接 Prometheus 或云监控时很容易乱加指标。

### 5. `evaluate_alert_rule()`

这个函数做简单阈值判断。

例如：

```text
current_value=5000
comparator=>=
threshold=5000
```

结果是触发。

真实监控平台会自己计算窗口、聚合、持续时间。

本项目当前先把告警规则结构和阈值判断讲清楚。

## 常见误区

### 误区 1：日志多就等于监控好

不对。

日志多不代表有指标、有趋势、有告警。

日志用于排查，监控用于发现整体风险。

### 误区 2：每个错误都应该告警

不对。

单次错误通常进入日志和 trace。

告警应该关注持续性、聚合性、影响用户或成本安全的问题。

### 误区 3：平均延迟就够了

不够。

平均值可能掩盖慢请求。

生产系统更关注 p95、p99。

### 误区 4：metrics label 越详细越好

不对。

高基数标签会造成监控系统压力，也可能泄露隐私。

`user_id`、`trace_id`、`order_id`、`query` 不应该作为 metrics label。

### 误区 5：成本只要月底看账单就行

不对。

AI 应用成本可能因为流量、prompt、retry、fallback、长上下文突然升高。

应该有 token 和估算成本指标，必要时有成本告警。

## 当前项目边界

本节已经具备：

```text
生产指标目录
指标类型
指标域
指标低基数标签校验
默认告警规则
告警严重级别
告警窗口
runbook_hint
告警条件判断
关键测试
```

尚未深入：

```text
Prometheus 实际采集
Grafana 看板
OpenTelemetry Collector
云监控平台
真实告警通知
短信/邮件/飞书/Slack
SLO burn rate 告警
多维度成本仪表盘
```

这些适合后续完整项目部署时再做。

## 练习题

### 练习 1：下面哪些字段适合作为 metrics label？

题目：

```text
A. route
B. method
C. user_id
D. trace_id
E. model
F. query
```

参考答案：

```text
A、B、E 适合。

route、method、model 都是低基数字段。

C、D、F 不适合。
user_id、trace_id、query 是高基数或敏感字段，不应该作为 metrics label。
```

### 练习 2：为什么延迟指标适合 histogram？

参考答案：

```text
因为延迟不是只看总数，而是要看分布。
Histogram 可以支持 p50、p95、p99 等分位数，帮助判断大多数用户和慢请求用户的体验。
```

### 练习 3：LLM 失败率升高时应该查什么？

参考答案：

```text
先查 provider 状态、API Key、网络、超时、限流、错误码分布、retry 是否过多、fallback 是否触发、是否近期改过模型路由或配置。
```

### 练习 4：为什么安全阻断升高不一定是坏事？

参考答案：

```text
安全阻断升高可能表示攻击流量增加，也可能表示安全规则误伤正常请求。
所以要看 safety_reason 分布和脱敏后的样本元信息，不能只凭数量判断。
```

## 自测问题

### 自测 1：日志、Tracing、Monitoring、Eval 分别解决什么问题？

参考答案：

```text
日志记录单次事件细节。
Tracing 串联一次请求的完整链路。
Monitoring 聚合观察线上运行健康。
Eval 判断 AI 效果质量有没有退化。
```

### 自测 2：什么是有效告警？

参考答案：

```text
有效告警应该有明确风险、明确阈值、观察窗口、持续时间、严重级别和排查方向，并且响了以后确实需要人处理。
```

### 自测 3：为什么不能把 `trace_id` 放进 metrics label？

参考答案：

```text
因为 trace_id 每次请求都不同，是高基数字段。
放进 metrics label 会产生海量时间序列，增加监控成本和查询压力。
trace_id 应该用于日志和 tracing，不用于指标标签。
```

### 自测 4：AI 应用为什么要监控 token 和成本？

参考答案：

```text
因为 AI 成本会受到输入长度、输出长度、模型价格、retry、fallback、流量和 RAG 上下文长度影响，可能快速增长。
监控 token 和成本可以提前发现成本失控。
```

### 自测 5：RAG no-context 升高可能说明什么？

参考答案：

```text
可能说明向量库异常、知识库数据缺失、metadata filter 过严、score_threshold 太高、query rewrite 变差、入库失败或用户问题超出知识库覆盖范围。
```

## 本节手动验证命令

本节不需要打开 VMware Ubuntu。

本节不需要真实调用大模型。

按当前约定，测试由你手动执行：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run pytest tests/test_production_monitoring.py -q
```

## 本节小结

本节把生产监控从“知道要看日志”推进到“知道应该设计哪些指标和告警”。

你现在应该能讲清：

```text
监控和日志、Tracing、Eval 的区别。
Counter、Gauge、Histogram 的区别。
P95/P99 为什么重要。
为什么指标标签要低基数。
AI 应用比传统后端多监控哪些内容。
什么是有效告警。
为什么告警要有窗口、持续时间和 runbook_hint。
```

下一节进入：

```text
阶段 10 第 21 节：灰度发布、回滚与配置开关
```
