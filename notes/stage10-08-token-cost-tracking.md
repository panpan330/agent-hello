# 阶段 10 第 8 节：Token 成本统计

## 本节定位

这一节学习 AI 应用生产化里的成本基础。

前面你已经学了：

```text
Tracing
日志安全
配置与密钥管理
```

现在继续补一个真实 AI 项目必须掌握的问题：

```text
一次模型调用到底用了多少 token，大概花了多少钱，系统应该怎么记录。
```

## 本节学习目标

- 理解 token、prompt tokens、completion tokens、total tokens。
- 理解为什么 AI 成本不是简单按“请求次数”算。
- 理解按百万 token 单价估算成本的公式。
- 理解成本统计和日志、metric、trace 的关系。
- 理解 RAG、Agent、Tool Calling 为什么容易让成本上升。
- 看懂本节新增的 token usage 归一化、成本估算和安全日志字段。

## 本节新增和修改

- 扩展 `app/core/token_usage.py`。
- 扩展 `Settings` 的 LLM 单价配置。
- 修改 LLM 成功日志，补充安全成本元信息。
- 更新 `.env.example` 的可选价格配置说明。
- 补充 token 成本相关测试。
- 更新学习进度。

## 一句话先讲透

Token 成本统计就是：

```text
先拿到模型返回的输入 token 和输出 token，再用对应模型的输入/输出单价估算本次调用成本，最后按模型、接口、功能和时间维度记录下来。
```

## 基础知识铺垫

### 1. 什么是 token

token 可以先粗略理解成：

```text
模型处理文本时使用的最小计量单位。
```

它不是严格等于：

```text
一个汉字
一个英文单词
一个字符
一行文本
```

模型不会像人一样直接按“字数”理解文本。

它会先把文本切成一段段 token，然后模型处理的是 token 序列。

例如英文中：

```text
hello
```

可能是一个 token。

但：

```text
unbelievable
```

可能被拆成多个 token。

中文里一个汉字常常会接近一个 token，但也不是绝对规则。

所以初学时先记住：

```text
token 是模型视角里的文本长度单位，不等于人眼看到的字数。
```

### 2. 为什么 AI 应用按 token 计费

传统后端项目常见成本是：

```text
服务器 CPU
内存
数据库
带宽
缓存
磁盘
```

一次普通 HTTP 请求可能不直接产生第三方调用费用。

但 AI 应用不一样。

很多模型平台按照：

```text
输入 token 数
输出 token 数
模型类型
```

计费。

也就是说：

```text
用户发的问题越长，可能越贵。
你塞给模型的上下文越长，可能越贵。
模型回答越长，可能越贵。
模型越高级，单价可能越高。
工具链调用模型次数越多，总成本越高。
```

所以 AI 应用的成本不是简单看：

```text
今天有多少个请求。
```

而要看：

```text
今天消耗了多少输入 token。
今天消耗了多少输出 token。
这些 token 分别调用了哪些模型。
这些模型单价是多少。
哪些接口或功能消耗最多。
哪些用户或租户消耗最多。
```

### 3. 什么是 prompt tokens

`prompt tokens` 通常表示：

```text
发送给模型的输入 token 数。
```

它不只是用户输入。

一次真实模型调用的输入可能包括：

```text
system prompt
developer prompt
用户当前问题
历史对话
RAG 检索到的文档片段
工具定义 tools
结构化输出 schema
已执行工具的结果
安全约束
格式要求
```

所以用户只问了一句：

```text
我的订单什么时候到？
```

最终送进模型的 prompt 可能很长。

因为系统可能会拼进去：

```text
你是客服助手
不能泄露内部信息
回答必须中文
订单状态字段解释
RAG 检索结果
工具调用规则
用户身份上下文
```

这就是为什么 AI 项目成本容易被低估。

你看到的是用户一句话，模型看到的是一大包上下文。

### 4. 什么是 completion tokens

`completion tokens` 通常表示：

```text
模型生成的输出 token 数。
```

也就是模型回答、结构化结果、工具调用参数等输出内容消耗的 token。

例如模型输出：

```text
您的订单 A1001 当前正在运输中，预计明天送达。
```

这些文本会产生 completion tokens。

如果模型输出很长，completion tokens 就会增加。

所以：

```text
回答越长，输出成本越高。
```

这也是为什么生产系统经常要配置：

```text
MAX_OUTPUT_TOKENS
```

它的作用不是“让模型更聪明”，而是：

```text
限制模型最多输出多少 token，避免一次回答无限变长。
```

### 5. 什么是 total tokens

`total tokens` 通常表示：

```text
prompt tokens + completion tokens
```

例如：

```text
prompt_tokens = 1000
completion_tokens = 500
total_tokens = 1500
```

这表示：

```text
输入消耗 1000 token。
输出消耗 500 token。
本次总消耗 1500 token。
```

不过成本估算不能只看 total tokens。

因为很多模型平台的输入和输出单价不一样。

常见情况是：

```text
输出 token 比输入 token 更贵。
```

所以如果只知道：

```text
total_tokens = 1500
```

但不知道输入多少、输出多少，就很难准确估算成本。

### 6. 为什么输入和输出要分开计费

从模型服务角度看：

```text
处理输入
生成输出
```

消耗的计算资源不完全一样。

输出阶段通常涉及逐 token 生成。

每生成一个 token，模型都要继续推理后续内容。

所以平台常常把价格拆成：

```text
input price
output price
```

也就是：

```text
每 100 万输入 token 多少钱。
每 100 万输出 token 多少钱。
```

本节代码使用的也是这个模型：

```text
input_cost_per_million_tokens
output_cost_per_million_tokens
```

### 7. 为什么常说“每百万 token 单价”

很多模型平台不写：

```text
每 1 token 多少钱。
```

而写：

```text
每 1,000,000 tokens 多少钱。
```

原因是单个 token 的价格太小。

例如：

```text
每百万输入 token 2 元
```

单个输入 token 的价格就是：

```text
2 / 1,000,000 = 0.000002 元
```

这个数太小，不方便阅读。

所以实际估算公式是：

```text
输入成本 = prompt_tokens * 输入每百万 token 单价 / 1,000,000
输出成本 = completion_tokens * 输出每百万 token 单价 / 1,000,000
总成本 = 输入成本 + 输出成本
```

本节测试里的例子：

```text
prompt_tokens = 1000
completion_tokens = 500
输入每百万 token 单价 = 2.0
输出每百万 token 单价 = 6.0
```

计算：

```text
输入成本 = 1000 * 2.0 / 1,000,000 = 0.002
输出成本 = 500 * 6.0 / 1,000,000 = 0.003
总成本 = 0.005
```

### 8. 为什么本节不写真实模型价格

真实模型价格会变化。

不同平台、不同模型、不同地域、不同计费套餐、不同时间都可能不同。

所以项目代码里不应该写死：

```text
qwen3.7-plus 永远是多少钱。
```

更合理的方式是：

```text
价格从配置读取。
```

本节新增配置：

```text
LLM_INPUT_COST_PER_MILLION_TOKENS
LLM_OUTPUT_COST_PER_MILLION_TOKENS
LLM_PRICING_CURRENCY
```

它们是可选的。

如果没配置价格，系统仍然可以记录 token，但成本状态是：

```text
missing_pricing
```

意思是：

```text
有 token，但没有配置单价，所以不能估算成本。
```

### 9. 为什么成本只能叫 estimate

本节代码里用的是：

```text
estimated_cost
```

不是：

```text
actual_bill
```

原因是：

```text
模型平台最终账单可能包含套餐、折扣、免费额度、阶梯价、缓存优惠、失败调用规则、税费、汇率等因素。
```

我们在业务系统里用 token 和配置单价计算出来的是：

```text
估算成本。
```

它足够用于：

```text
趋势观察
接口对比
用户用量分析
预算预警
成本优化
排查异常请求
```

但不应该直接当财务最终账单。

### 10. 什么是 usage

模型 API 返回里通常会有 usage 字段。

它可能长这样：

```json
{
  "prompt_tokens": 1000,
  "completion_tokens": 500,
  "total_tokens": 1500
}
```

也可能在某些 API 形态里叫：

```text
input_tokens
output_tokens
total_tokens
```

所以本节新增：

```python
normalize_token_usage()
```

它负责把不同形态的 usage 归一化为：

```text
TokenUsageSnapshot
```

统一之后，后续成本估算就不用关心：

```text
原始 usage 是 dict 还是对象。
字段叫 prompt_tokens 还是 input_tokens。
```

### 11. 为什么要忽略非法 token 数

token 数应该是：

```text
非负整数。
```

下面这些都不应该接受：

```text
-1
true
"100"
None
NaN
```

为什么 `true` 也不能接受？

因为在 Python 里：

```python
isinstance(True, int)
```

结果是：

```text
True
```

这是 Python 的历史设计。

但 token 数不能是布尔值。

所以本节代码专门排除了 bool。

这也是很多生产代码容易忽略的细节。

### 12. 为什么 RAG 会让 token 成本上升

RAG 的流程通常是：

```text
用户问题
检索知识库
拿到多个文档片段
把文档片段塞进 prompt
让模型基于上下文回答
```

成本上升的点在于：

```text
文档片段会进入 prompt tokens。
```

例如用户只问：

```text
退款多久到账？
```

但系统可能检索出 5 个 chunk，每个 chunk 800 字。

这些 chunk 都进入模型上下文后，prompt tokens 会明显增加。

所以 RAG 不能只追求：

```text
top_k 越大越好。
上下文越多越好。
```

还要考虑：

```text
检索质量
上下文压缩
chunk 长度
score_threshold
rerank
引用来源
成本
```

### 13. 为什么 Agent 会让 token 成本上升

Agent 通常不是只调用一次模型。

它可能会：

```text
第一次调用模型判断意图。
第二次调用模型决定工具。
第三次调用模型总结工具结果。
第四次调用模型追问缺失字段。
第五次调用模型生成最终回答。
```

每次调用都有：

```text
prompt tokens
completion tokens
```

所以 Agent 成本不是：

```text
用户发起一次请求的成本。
```

而是：

```text
这次请求内部所有模型调用成本之和。
```

这也是为什么生产系统要记录：

```text
operation
llm_task
prompt_name
model
provider
```

否则你只知道总成本上升，却不知道是哪一步贵。

### 14. 为什么 Tool Calling 也会增加 token

Tool Calling 可能增加两类 token。

第一类：

```text
工具定义本身进入模型上下文。
```

例如你告诉模型：

```text
query_order 工具有哪些参数。
create_ticket 工具有哪些参数。
哪些字段必填。
什么情况下调用。
```

这些工具描述会占用 prompt tokens。

第二类：

```text
工具结果回传模型。
```

例如订单结果、工单结果、RAG 文档结果都可能作为 tool message 再给模型总结。

这些也会增加 prompt tokens。

所以工具链越复杂，成本越需要观察。

### 15. 为什么 structured output 也可能增加 token

结构化输出常常需要给模型 schema 或格式要求。

例如：

```text
你必须输出 JSON。
字段包括 intent、order_id、need_ticket、reason。
字段必须符合 enum。
```

这些说明会增加输入 token。

模型输出 JSON 也会增加输出 token。

结构化输出的价值是：

```text
结果更稳定，更容易被程序解析。
```

但它不是免费的。

生产系统需要知道：

```text
为了更稳定的结构化输出，多消耗了多少 token，是否值得。
```

### 16. 为什么要按维度统计成本

只记录一天总成本，不够用。

比如你只知道：

```text
今天花了 100 元。
```

这很难优化。

你还需要知道：

```text
哪个模型花得多。
哪个接口花得多。
哪个功能花得多。
哪个用户或租户花得多。
哪种错误导致重复调用。
哪个 prompt 版本变贵了。
哪段 RAG 上下文过长。
哪个 Agent 节点调用次数过多。
```

常见统计维度包括：

```text
provider
model
operation
route
llm_task
prompt_name
prompt_version
tenant_id
user_id
trace_id
日期小时
```

但注意：

```text
不同数据放在不同系统里。
```

不是所有维度都适合进 metric 标签。

### 17. 成本统计和日志的关系

日志适合记录：

```text
某一次调用发生了什么。
```

例如：

```text
模型名
operation
prompt_tokens
completion_tokens
total_tokens
cost_status
estimated_cost
currency
trace_id
elapsed_ms
```

日志的优点是：

```text
能排查单次请求。
能和 trace_id 对上。
能看到具体一次调用的成本估算。
```

日志的缺点是：

```text
不适合直接做高效聚合。
数据量大。
查询成本可能高。
```

所以日志不是成本统计的唯一地方。

### 18. 成本统计和 metric 的关系

metric 适合记录：

```text
可聚合的数值。
```

例如：

```text
app.llm.client.requests
gen_ai.client.token.usage
app.llm.client.estimated_cost
```

metric 的优点是：

```text
适合做趋势图。
适合做告警。
适合按低基数维度聚合。
```

metric 的缺点是：

```text
不适合带用户原文、trace_id、完整 prompt、完整回答。
```

尤其是 metric 标签要控制基数。

比如：

```text
model=qwen3.7-plus
operation=chat
status=ok
```

这种标签基数低，适合 metric。

但：

```text
trace_id=每次请求都不同
user_message=每个用户问题都不同
```

这种标签基数高，不适合 metric。

### 19. 成本统计和 trace 的关系

trace 适合回答：

```text
一次请求内部每一步分别花了多久、用了多少 token、成本大概多少。
```

例如一次智能工单请求：

```text
http.request
  llm.intent_classification
  rag.search
  llm.tool_decision
  java.orders.get
  llm.final_answer
```

每个 LLM span 都可以带：

```text
prompt_tokens
completion_tokens
estimated_cost
model
```

这样你能看出：

```text
最贵的是意图识别，还是最终回答，还是工具总结。
```

但当前本节先不接真实 OpenTelemetry，只把数据结构和日志能力打好。

### 20. 为什么成本统计不能泄露敏感信息

成本统计需要记录 token 和金额。

但不需要记录：

```text
用户原文
完整 prompt
完整模型回答
API Key
Authorization
RAG 文档正文
工具结果全文
```

因为成本统计关注的是：

```text
用了多少。
哪里用了。
大概花了多少。
```

不是关注：

```text
用户具体说了什么。
模型完整答了什么。
密钥是什么。
```

这和第 6 节、第 7 节是一条线：

```text
生产化记录要保留排查价值，但不能泄露敏感内容。
```

### 21. 成本统计为什么要处理“缺失 usage”

不是所有模型响应都一定返回 usage。

可能出现：

```text
模型平台不返回。
SDK 版本差异。
流式响应没有开启 include_usage。
调用失败没有 usage。
中途断流没有最终 usage。
兼容 OpenAI 的平台字段不完全一致。
```

所以成本统计不能假设 usage 一定完整。

本节代码把状态分成：

```text
estimated
missing_pricing
incomplete_usage
```

含义：

```text
estimated：usage 和单价都足够，可以估算。
missing_pricing：有可能有 usage，但没配置价格。
incomplete_usage：配置了价格，但缺少输入或输出 token。
```

这样比直接报错更适合生产环境。

### 22. 为什么流式输出要特别处理 usage

非流式响应通常一次返回完整 completion。

usage 可能就在最终响应对象里。

流式响应不同。

它是一块一块返回：

```text
chunk 1
chunk 2
chunk 3
...
final chunk
```

usage 往往在最后一个 chunk 才出现。

所以当前项目在流式调用里设置：

```python
stream_options={"include_usage": True}
```

并在遍历 chunk 时：

```text
遇到 usage 就记录下来。
```

这就是为什么流式 token 统计要比普通调用麻烦一点。

### 23. 成本统计和限流的关系

后面会学限流。

限流不只是防止接口被打爆。

在 AI 应用里，限流还和成本有关。

例如：

```text
单用户每分钟最多请求 10 次。
单用户每天最多消耗 100 万 token。
单租户每天最多成本 100 元。
高成本模型每天只能调用固定次数。
```

如果没有 token 成本统计，就很难做：

```text
按 token 限流。
按成本限流。
按模型预算限流。
```

所以本节是后续成本控制和限流的基础。

### 24. 成本统计和缓存的关系

缓存可以降低成本。

比如：

```text
同一个常见问题，答案可以缓存。
同一个 query rewrite 结果可以缓存。
同一个 embedding 结果可以缓存。
相同 RAG 检索结果可以短期缓存。
```

如果没有成本统计，你很难判断：

```text
缓存到底省了多少钱。
哪个功能最值得加缓存。
缓存命中率提高后成本下降多少。
```

所以成本统计不是独立能力，它会指导后续优化。

### 25. 本节要形成的判断能力

以后看到一次 AI 调用，你要能问：

```text
这是第几次模型调用？
调用的是哪个模型？
输入 token 多少？
输出 token 多少？
单价从哪里来？
成本是估算还是最终账单？
usage 是否完整？
成本记录有没有泄露 prompt 或 key？
这个成本应该进日志、metric，还是 trace？
这个成本能不能按功能、接口、模型聚合？
```

这才是真正理解 token 成本统计。

## 本节主题系统讲解

### 1. 当前项目原来有什么

项目里原来已经有：

```text
app/core/token_usage.py
```

原来的职责比较小：

```text
粗略估算一段文本大概会占多少 token。
构建 TokenBudget。
```

这适合在调用模型前做：

```text
输入长度预估。
最大输出预留。
```

但它还不够完成生产化成本统计。

因为成本统计需要：

```text
真实 usage 归一化。
输入/输出 token 分开。
配置模型单价。
估算输入成本和输出成本。
输出安全日志字段。
```

所以本节是在原有 `token_usage.py` 上扩展，而不是另起一个完全无关的工具。

### 2. 本节新增后的分层

现在可以这样理解：

```text
调用前：
  estimate_text_tokens_roughly()
  build_token_budget()

调用后：
  normalize_token_usage()
  estimate_token_cost()
  build_token_cost_record()
```

调用前解决：

```text
我大概会用多少上下文窗口。
我最多允许模型输出多少。
```

调用后解决：

```text
模型实际报告用了多少 token。
按照配置单价大概花了多少钱。
日志里应该记录哪些安全字段。
```

这两个方向都属于 token 管理，但阶段不同。

### 3. `TokenUsageSnapshot` 的系统位置

`TokenUsageSnapshot` 是归一化后的 usage。

它有：

```text
prompt_tokens
completion_tokens
total_tokens
```

它不关心：

```text
原始响应来自哪个 SDK。
原始 usage 是 dict 还是对象。
字段名是 prompt_tokens 还是 input_tokens。
```

统一后，后面的成本估算、日志、metric、trace 都可以基于它做。

这是一种很常见的后端设计思路：

```text
外部输入可能有多种形态。
先归一化成内部稳定结构。
内部逻辑只依赖稳定结构。
```

### 4. `TokenPricing` 的系统位置

`TokenPricing` 表示单价配置。

它包含：

```text
input_cost_per_million_tokens
output_cost_per_million_tokens
currency
```

为什么价格不直接写在代码里？

因为：

```text
模型价格会变。
不同模型价格不同。
不同平台价格不同。
不同环境可能使用不同价格。
```

所以本节把价格放到 `Settings`：

```text
LLM_INPUT_COST_PER_MILLION_TOKENS
LLM_OUTPUT_COST_PER_MILLION_TOKENS
LLM_PRICING_CURRENCY
```

真实项目里，多模型路由后还会更复杂：

```text
每个模型有自己的价格。
```

本节先做最小但完整的一层：

```text
当前 LLM 配置对应一组输入/输出单价。
```

### 5. `TokenCostEstimate` 的系统位置

`TokenCostEstimate` 不只保存金额。

它还保存：

```text
status
```

为什么？

因为生产环境里不能假设每次都能估算成功。

可能有：

```text
没有配置价格。
usage 缺少 prompt_tokens。
usage 缺少 completion_tokens。
流式响应中断。
供应商字段不兼容。
```

所以状态很重要。

否则你看到：

```text
estimated_cost=None
```

会不知道是：

```text
没配置价格？
没有 usage？
代码 bug？
```

有了 status，就能区分。

### 6. `TokenCostRecord` 的系统位置

`TokenCostRecord` 把三类信息放在一起：

```text
provider / model / operation
usage
cost
```

也就是说它能表达：

```text
哪个模型的哪类调用，用了多少 token，大概花了多少钱。
```

例如：

```text
provider = test-provider
model = qwen-test
operation = chat
prompt_tokens = 1000
completion_tokens = 500
estimated_total_cost = 0.005
```

这正是生产排查需要的最小成本记录。

### 7. 为什么本节先不做数据库持久化

成本统计最终可以进数据库。

但本节没有做。

原因是：

```text
当前阶段先建立成本数据的正确形状。
```

如果一开始就做数据库表，很容易把注意力放到：

```text
建表
DAO
接口
分页
查询
```

反而忽略核心问题：

```text
token 怎么来。
成本怎么算。
哪些状态不能估。
哪些字段能进日志。
哪些字段不能泄露。
```

后续如果要做完整项目，可以再把 `TokenCostRecord` 持久化。

### 8. 为什么本节先接 LLM 成功日志

本节改了普通 LLM 成功日志和流式成功日志。

成功日志新增：

```text
cost_status
estimated_cost
currency
```

这样每次模型调用成功后，日志里能看到：

```text
用了多少 token。
成本有没有估算成功。
估算总成本是多少。
币种是什么。
```

失败日志没有强行估算成本。

原因是：

```text
失败时通常没有完整 usage。
不同平台失败调用是否计费也不一致。
```

所以本节先做：

```text
成功调用的成本元信息记录。
```

这比较稳。

### 9. 为什么日志只记录 estimated_total_cost

本节日志里主要展示：

```text
estimated_cost
```

也就是总估算成本。

同时 `TokenCostRecord.to_log_fields()` 里也准备了：

```text
estimated_input_cost
estimated_output_cost
cost_currency
cost_status
```

这些字段会进入安全 payload。

但日志消息展示保持简洁。

原因是：

```text
日志消息太长会影响阅读。
详细字段后续可以进入结构化日志或 metric。
```

### 10. 为什么成本日志不能带用户维度

按用户统计成本很重要。

但不是所有地方都适合直接写 user_id。

尤其是 metric 标签里，用户 ID 是高基数字段。

如果把 user_id 作为 metric 标签，可能导致：

```text
标签数量爆炸。
存储压力变大。
查询变慢。
监控系统成本上升。
```

所以要区分：

```text
日志/审计表可以记录经过权限控制的用户维度。
metric 应该优先使用低基数维度。
trace 可以通过 trace_id 关联单次请求。
```

本节先不做用户维度，只把模型调用级成本打好。

### 11. 本节和已有 `app/agents/llm_metrics.py` 的关系

项目里已有：

```text
app/agents/llm_metrics.py
```

它更偏向：

```text
Agent 场景里的 metrics 设计。
```

里面包含：

```text
metric spec
metric measurement
token usage metric
estimated cost metric
高基数字段过滤
```

本节新增的 `app/core/token_usage.py` 更基础：

```text
普通 LLM 服务也能使用的 token 和成本工具。
```

可以这样分工：

```text
core/token_usage.py：通用 token usage 和成本估算。
agents/llm_metrics.py：Agent 维度的 metric 设计和指标输出形状。
```

未来如果继续重构，可以让 metrics 模块复用 core 的成本估算。

本节暂时不做大重构，避免影响面太大。

### 12. 本节和配置管理的关系

第 7 节讲了配置与密钥管理。

本节马上用上：

```text
LLM_INPUT_COST_PER_MILLION_TOKENS
LLM_OUTPUT_COST_PER_MILLION_TOKENS
LLM_PRICING_CURRENCY
```

这三个值是配置，不是密钥。

但也没有必要在日志里频繁打印单价。

日志需要的是：

```text
本次调用估算成本。
```

单价配置本身可以通过安全配置快照知道：

```text
pricing_configured = true / false
currency = USD
```

不需要每次暴露完整单价。

### 13. 本节和日志安全的关系

第 6 节讲了 LLM 日志安全。

本节沿用它：

```python
build_safe_llm_log_payload(...)
```

成本字段不是直接拼接任意对象。

而是先进入安全 payload。

这样可以继续保证：

```text
prompt 不进日志。
messages 不进日志。
用户输入不进日志。
API Key 不进日志。
完整回答不进日志。
```

成本统计只记录：

```text
token 数
成本状态
估算金额
币种
```

这些属于安全元信息。

### 14. 本节和下一节的关系

下一节是：

```text
请求耗时拆解
```

它会关注：

```text
一次请求里每个阶段耗时多少。
```

本节关注：

```text
一次请求里模型调用消耗多少 token 和成本。
```

两者结合后，就能回答：

```text
这个请求慢在哪里？
这个请求贵在哪里？
有没有又慢又贵的环节？
```

这是真实 AI 应用优化时很关键的两个维度。

## 本节代码讲解

### 1. `TokenUsageSnapshot`

新增结构：

```python
@dataclass(frozen=True)
class TokenUsageSnapshot:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
```

它表示一次模型调用的 token 用量快照。

它还有：

```python
has_split_usage
computed_total_tokens
total_matches_split
```

这些属性用于判断：

```text
有没有输入/输出拆分。
根据输入/输出算出来的总数是多少。
模型返回的 total_tokens 是否等于输入+输出。
```

### 2. `normalize_token_usage`

这个函数接收：

```text
dict
对象
TokenUsageSnapshot
None
```

然后统一返回：

```text
TokenUsageSnapshot
```

它支持：

```text
prompt_tokens / completion_tokens
input_tokens / output_tokens
```

这样做是为了兼容不同模型 API 返回形状。

### 3. `TokenPricing`

代码结构：

```python
@dataclass(frozen=True)
class TokenPricing:
    input_cost_per_million_tokens: float
    output_cost_per_million_tokens: float
    currency: str = "USD"
```

它表示：

```text
输入每百万 token 单价
输出每百万 token 单价
币种
```

`__post_init__` 做校验：

```text
价格必须是数字。
价格必须有限。
价格不能为负。
currency 不能为空。
```

### 4. `estimate_token_cost`

核心公式：

```python
input_cost = prompt_tokens * input_price / 1_000_000
output_cost = completion_tokens * output_price / 1_000_000
total_cost = input_cost + output_cost
```

如果缺少价格：

```text
status = missing_pricing
```

如果缺少输入/输出拆分：

```text
status = incomplete_usage
```

如果可以估算：

```text
status = estimated
```

### 5. `TokenCostRecord`

这个结构把调用维度、usage 和成本放到一起：

```python
provider
model
operation
usage
cost
```

它的 `to_log_fields()` 返回安全日志字段：

```text
llm.cost_status
llm.cost_currency
llm.estimated_input_cost
llm.estimated_output_cost
llm.estimated_total_cost
```

它不会返回：

```text
prompt
messages
user_message
API Key
raw response
```

### 6. `Settings` 新增配置

本节给 `Settings` 新增：

```python
llm_input_cost_per_million_tokens
llm_output_cost_per_million_tokens
llm_pricing_currency
```

并增加：

```python
has_llm_token_pricing
resolved_llm_pricing_currency
```

这样业务代码可以判断：

```text
是否已经配置了完整价格。
```

如果只配置输入价格，不配置输出价格，也不能估算完整成本。

所以 `has_llm_token_pricing` 要求：

```text
输入价格和输出价格都存在。
```

### 7. LLM 成功日志改动

普通聊天成功日志现在会带：

```text
cost_status
estimated_cost
currency
```

流式聊天成功日志也会带这些字段。

如果没有配置价格，日志里会出现：

```text
cost_status=missing_pricing
estimated_cost=None
currency=None
```

这说明：

```text
模型调用成功，token 可能有记录，但当前没法估算成本。
```

如果配置了价格并且 usage 完整：

```text
cost_status=estimated
estimated_cost=0.005
currency=USD
```

### 8. 为什么测试不真实调用模型

本节测试使用 fake completion。

原因是：

```text
成本统计逻辑只依赖 usage 字段，不需要真实模型。
```

自动化测试不应该为了验证公式去花真实 token。

测试只需要构造：

```text
prompt_tokens = 1000
completion_tokens = 500
```

就能验证：

```text
成本公式是否正确。
日志是否安全。
缺价格是否能识别。
非法 token 是否被忽略。
```

## 常见误区

### 误区 1：把 token 当成字数

token 不是字数。

字数只能粗略估算。

真实计费要以模型返回的 usage 为准。

### 误区 2：只看 total tokens

只看 total tokens 不够。

因为输入和输出单价可能不同。

成本估算最好需要：

```text
prompt_tokens
completion_tokens
```

### 误区 3：把估算成本当成最终账单

业务系统里算出来的是 estimated cost。

最终账单可能受套餐、折扣、免费额度、缓存策略、失败计费规则影响。

### 误区 4：RAG top_k 越大越好

top_k 越大，塞给模型的上下文可能越多。

上下文越多，prompt tokens 越多，成本越高。

RAG 要平衡：

```text
召回率
准确率
上下文长度
成本
延迟
```

### 误区 5：Agent 一次用户请求只算一次模型成本

Agent 内部可能多次调用模型。

所以要统计所有 LLM 节点成本之和。

### 误区 6：成本指标里可以随便放 user_id

不建议把 user_id 放进 metric 标签。

它是高基数字段，会让监控系统压力变大。

用户级成本可以进数据库、审计表或专门账单系统，但不要随便作为指标标签。

### 误区 7：没有 usage 就让业务失败

不一定。

如果模型回答成功但 usage 缺失，可以先让业务继续返回，同时记录：

```text
incomplete_usage
```

成本统计失败不应该轻易影响用户主流程。

## 本节练习

### 练习 1：计算单次模型调用成本

已知：

```text
prompt_tokens = 2000
completion_tokens = 1000
输入每百万 token 单价 = 3
输出每百万 token 单价 = 9
```

本次估算成本是多少？

参考答案：

```text
输入成本 = 2000 * 3 / 1,000,000 = 0.006
输出成本 = 1000 * 9 / 1,000,000 = 0.009
总成本 = 0.015
```

### 练习 2：为什么只知道 total_tokens=3000 还不够准确估算

参考答案：

```text
因为输入 token 和输出 token 的单价可能不同。
如果不知道 3000 里面多少是输入、多少是输出，就无法准确拆分输入成本和输出成本。
```

### 练习 3：RAG 为什么会增加 prompt tokens

参考答案：

```text
因为 RAG 会把检索到的文档片段作为上下文放进 prompt。
用户问题可能很短，但文档片段、引用、回答规则和安全约束会让输入变长。
```

### 练习 4：为什么成本统计日志不能记录完整 prompt

参考答案：

```text
成本统计只需要 token 数、模型、operation、成本状态和估算金额。
完整 prompt 可能包含用户隐私、RAG 文档正文、工具结果和系统策略，记录它会带来泄露风险。
```

### 练习 5：`missing_pricing` 和 `incomplete_usage` 有什么区别

参考答案：

```text
missing_pricing 表示没有配置单价，所以不能估算成本。
incomplete_usage 表示配置了单价，但 usage 缺少 prompt_tokens 或 completion_tokens，所以不能准确估算。
```

### 练习 6：为什么本节价格配置是可选的

参考答案：

```text
因为本地学习、自动化测试和 fake 模型模式不一定需要真实价格。
价格不配置时，系统仍能运行，只是成本状态会显示 missing_pricing。
```

## 自测题

### 自测 1：prompt tokens 包含哪些内容

参考答案：

```text
prompt tokens 不只是用户输入，还可能包含 system prompt、历史对话、RAG 文档片段、工具定义、结构化输出 schema、安全约束和格式要求。
```

### 自测 2：completion tokens 是什么

参考答案：

```text
completion tokens 是模型生成输出消耗的 token，包括自然语言回答、JSON 结构化结果或工具调用参数等输出内容。
```

### 自测 3：成本估算公式是什么

参考答案：

```text
输入成本 = prompt_tokens * 输入每百万 token 单价 / 1,000,000
输出成本 = completion_tokens * 输出每百万 token 单价 / 1,000,000
总成本 = 输入成本 + 输出成本
```

### 自测 4：为什么要按 model 统计成本

参考答案：

```text
因为不同模型单价、速度和效果不同。
按 model 统计后，才能知道哪个模型成本最高，哪些任务是否应该切换到更便宜的模型。
```

### 自测 5：为什么日志、metric、trace 都可能记录成本，但职责不同

参考答案：

```text
日志适合排查单次调用。
metric 适合聚合、趋势和告警。
trace 适合看一次请求内部每个阶段的 token 和成本分布。
```

### 自测 6：为什么 Agent 成本可能比普通 Chat 更高

参考答案：

```text
因为 Agent 一次用户请求内部可能多次调用模型，例如意图识别、工具决策、字段提取、工具结果总结和最终回答，每一步都会产生 token 和成本。
```

## 本节小结

这一节你要真正记住：

```text
AI 成本不是按请求次数简单计算，而是和 token、模型、输入输出长度、调用次数和单价有关。
```

当前项目现在具备了：

```text
调用前粗略 token 预算
调用后 usage 归一化
输入/输出 token 拆分
按百万 token 单价估算成本
缺价格和缺 usage 的状态表达
LLM 成功日志里的安全成本元信息
```

后续学习成本控制、限流、多模型路由、fallback、耗时拆解时，这些 token 和成本数据都会继续发挥作用。
