# 阶段 10 第 6 节：LLM 调用日志安全

## 本节定位

前面几节学习了 tracing：

```text
Tracing 是什么
trace_id / span / event / metric 的区别
Python AI 服务 tracing
Java 业务服务 tracing 对齐
```

这一节继续学习生产化里非常关键的一件事：

```text
LLM 调用日志安全
```

这节不是教你“多打日志”。

这节真正要学的是：

```text
调用大模型时，哪些信息必须记录，哪些信息绝对不能直接记录，以及怎么用代码把这件事固定下来。
```

## 本节学习目标

学完本节，你要能说清楚：

1. 为什么 LLM 调用日志比普通后端日志更危险。
2. 完整 prompt、messages、用户问题、模型回答、API Key 为什么不能直接入日志。
3. 哪些 LLM 元信息应该记录。
4. 成功、失败、超时、限流、认证失败、流式输出应该怎么记日志。
5. 白名单字段、黑名单字段、脱敏、摘要化分别是什么。
6. 本节新增的 `llm_logging_safety.py` 如何保护当前项目后续的 LLM 日志。

## 本节新增和修改

| 类型 | 内容 |
|---|---|
| 新增代码 | `projects/ai-service/app/core/llm_logging_safety.py` |
| 修改代码 | `projects/ai-service/app/services/llm_service.py` |
| 新增测试 | `projects/ai-service/tests/test_llm_logging_safety.py` |
| 新增笔记 | `notes/stage10-06-llm-call-log-safety.md` |
| 修改进度 | `docs/learning-progress.md` |
| 手动测试文档 | 无，本节不需要真实调用模型 |

## 一句话先讲透

LLM 调用日志应该记录“这次模型调用怎么运行”，不能记录“用户完整说了什么、系统完整提示词是什么、模型完整回答了什么、密钥是什么”。

## 基础知识铺垫

### 1. 为什么 LLM 日志是高风险区域

普通后端日志通常记录：

```text
接口路径
状态码
耗时
错误码
用户 ID
业务 ID
异常信息
```

这些已经需要谨慎。

但 LLM 应用更特殊。

因为一次模型调用里可能包含：

```text
system prompt
developer prompt
用户输入
历史对话
RAG 检索出来的文档片段
工具返回结果
内部策略
权限边界说明
模型最终回答
```

这些内容如果完整打进日志，风险非常高。

### 2. LLM 请求里到底有什么

以 OpenAI-compatible chat completions 为例，请求通常包含：

```text
model
messages
temperature
max_tokens
tools
tool_choice
stream
```

其中最危险的是：

```text
messages
```

因为 messages 可能包含：

| role | 可能包含什么 |
|---|---|
| system | 系统角色、内部规则、安全边界 |
| developer | 开发者约束、工具使用规则 |
| user | 用户原始问题、隐私、订单号、投诉内容 |
| assistant | 历史模型回答 |
| tool | 工具返回的业务结果 |

所以不能因为“排查方便”，就把完整 `messages` 打出来。

### 3. LLM 响应里有什么

模型响应可能包含：

```text
choices
message.content
tool_calls
usage
finish_reason
error
```

其中可以安全记录的通常是：

```text
usage.prompt_tokens
usage.completion_tokens
usage.total_tokens
finish_reason
错误码
耗时
```

不应该直接记录：

```text
完整 message.content
完整 tool_calls.arguments
完整错误原文中的密钥或请求体
完整 provider raw response
```

原因是：

```text
模型输出也可能包含用户隐私、业务信息、RAG 文档内容或被 prompt injection 诱导泄露的内容。
```

### 4. 日志的目的不是复制现场

很多初学者会把日志理解成：

```text
把当时所有信息都保存下来，出问题就能看。
```

这在 AI 应用里很危险。

生产日志的目标应该是：

```text
保存足够定位问题的线索，同时不保存不该保存的正文和秘密。
```

也就是：

```text
记录元信息，不记录完整敏感内容。
```

例如：

| 不安全记录 | 更安全记录 |
|---|---|
| 完整 prompt | prompt_template_version |
| 完整 user_message | message_length、message_hash |
| 完整 messages | message_count、history_size |
| 完整模型回答 | response_length、finish_reason |
| 完整 RAG 文档 | chunk_count、source_count、content_hash |
| 完整工具结果 | tool_name、result_status、error_code |
| API Key | 不记录 |

### 5. 什么是白名单字段

白名单字段是：

```text
明确允许记录的字段。
```

对 LLM 调用日志来说，常见白名单字段包括：

```text
trace_id
operation
outcome
provider
model
elapsed_ms
prompt_tokens
completion_tokens
total_tokens
error_code
status_code
retry_count
fallback_used
route
```

白名单思想是：

```text
不是“除了几个危险字段都能记”，而是“只有确认安全且有排查价值的字段才记”。
```

这对生产系统很重要。

### 6. 什么是黑名单字段

黑名单字段是：

```text
明确禁止记录的字段。
```

LLM 日志常见黑名单：

```text
api_key
openai_api_key
llm_api_key
authorization
cookie
secret
token
password
prompt
raw_prompt
system_prompt
developer_prompt
messages
history
input
user_message
query
raw_response
model_response
reply
final_answer
content
tool_result
document_content
chunk_content
retrieved_documents
```

黑名单不是万能的。

因为你不可能提前想到所有危险字段名。

所以更好的做法是：

```text
白名单为主，黑名单兜底。
```

本节代码就是这个思想：

```text
核心字段由 build_safe_llm_log_payload 统一生成。
extra_fields 只能放安全标量，敏感字段会被过滤，核心字段不能被覆盖。
```

### 7. 什么是脱敏

脱敏就是把敏感信息替换掉。

例如：

```text
手机号：13800000000 -> 138****0000
邮箱：user@example.com -> u***@example.com
API Key：sk-xxxx -> [REDACTED_SECRET]
```

脱敏适合在你确实需要保留部分内容时使用。

但要注意：

```text
能不记录原文，就优先不记录原文。
```

对 LLM prompt 来说，通常更推荐：

```text
不记录完整 prompt。
记录 prompt 版本、长度、hash、模板名。
```

### 8. 什么是摘要化

摘要化不是让模型总结日志。

这里的摘要化是指：

```text
把大而敏感的内容转成低风险元信息。
```

例如：

| 原始内容 | 摘要化记录 |
|---|---|
| 用户完整问题 | `message_length=36` |
| prompt | `prompt_template=customer_chat_v3` |
| RAG 文档正文 | `retrieved_chunk_count=5` |
| 工具结果 | `tool_result_status=success` |
| 模型回答 | `answer_length=180` |

摘要化的目标是：

```text
保留排查价值，降低泄露风险。
```

### 9. 成功日志应该记什么

一次 LLM 调用成功后，应该记录：

```text
event_name
trace_id
operation
outcome=success
provider
model
elapsed_ms
prompt_tokens
completion_tokens
total_tokens
```

可选记录：

```text
route
retry_count
fallback_used
stream=true/false
chunk_count
content_chunk_count
```

不记录：

```text
prompt
messages
user_message
完整 response
完整 answer
api_key
```

### 10. 失败日志应该记什么

失败日志应该记录：

```text
event_name
trace_id
operation
outcome=failure
provider
model
elapsed_ms
error_code
status_code
```

例如：

```text
LLM_TIMEOUT
LLM_RATE_LIMITED
LLM_AUTHENTICATION_FAILED
LLM_PROVIDER_ERROR
LLM_BAD_RESPONSE
LLM_EMPTY_RESPONSE
```

失败日志要特别注意：

```text
不要把 provider 原始异常完整 message 直接暴露给用户或大量写进业务日志。
```

因为上游异常里有时会包含请求信息、URL、headers 或 provider 返回的原始错误正文。

### 11. 流式日志有什么不同

流式输出不是一次性返回。

它可能经历：

```text
创建 stream 成功
收到多个 chunk
中途报错
客户端断开
最后收到 usage
```

所以流式日志可以记录：

```text
chunk_count
content_chunk_count
elapsed_ms
prompt_tokens
completion_tokens
total_tokens
error_code
```

不应该记录：

```text
每个 chunk 的完整 content
完整流式响应对象
```

当前 `LLMChatService` 已经记录：

```text
chunks
content_chunks
tokens
elapsed_ms
```

本节把这些字段放进安全 payload 规则里。

### 12. LLM 日志和 tracing 的关系

第 4 节学过：

```text
llm.call
llm.stream
llm.final_answer
```

这些是 span。

本节的 LLM 日志是这些 span 上的安全信息。

可以理解为：

```text
span 告诉你这段模型调用在哪里、花了多久、是否失败。
日志告诉你这段模型调用的安全元信息和错误码。
metric 后续会告诉你很多模型调用汇总后的耗时、错误率、token 和成本。
```

三者不是替代关系。

它们配合使用。

### 13. LLM 日志和成本统计的关系

后面第 8 节会学 Token 成本统计。

成本统计依赖这些字段：

```text
model
provider
prompt_tokens
completion_tokens
total_tokens
```

这些字段是安全的。

它们不泄露用户原文，但能计算成本。

例如：

```text
qwen3.7-plus
prompt_tokens=1200
completion_tokens=200
```

就可以估算：

```text
这次模型调用大概花了多少钱。
```

### 14. LLM 日志和 Prompt Injection 的关系

Prompt Injection 可能诱导模型输出内部信息。

如果你把完整模型回答写进日志，就可能把被诱导泄露的内容长期保存下来。

所以日志安全是 Prompt Injection 防护的一部分。

正确做法是：

```text
安全检测结果可以记录。
完整危险内容不要直接记录。
```

例如：

```text
prompt_injection_detected=true
security_policy=blocked
reason_code=RAG_DOC_INJECTION
```

而不是记录完整恶意输入。

## 本节主题系统讲解

### 1. 当前项目已有的好习惯

`LLMChatService` 之前已经没有直接记录：

```text
user_message
messages
prompt
api_key
模型完整回答
```

它主要记录：

```text
provider
model
elapsed_ms
prompt_tokens
completion_tokens
total_tokens
error_code
status_code
chunks
content_chunks
```

这是正确方向。

但生产项目不能只靠“开发者记得别乱打日志”。

更稳妥的做法是：

```text
把安全规则写成可复用 helper，并用测试固定。
```

这就是本节新增代码的原因。

### 2. 本节新增的安全层

新增文件：

```text
projects/ai-service/app/core/llm_logging_safety.py
```

它提供两个核心能力：

```text
build_safe_llm_log_payload
find_forbidden_llm_log_fields
```

第一个用于生成安全 payload。

第二个用于检查一组字段里是否包含 LLM 日志禁用字段。

这两个能力服务于后续：

```text
普通聊天
流式聊天
Tool Calling 模型决策
工具结果总结
结构化输出
RAG 最终回答
多模型 fallback
自动化评估日志
```

### 3. 安全 payload 的核心字段

本节安全 payload 固定生成：

```text
app.trace_id
llm.operation
llm.outcome
llm.provider
llm.model
llm.elapsed_ms
llm.prompt_tokens
llm.completion_tokens
llm.total_tokens
llm.error_code
http.status_code
```

这些字段都是元信息。

它们能回答：

| 字段 | 回答的问题 |
|---|---|
| `app.trace_id` | 这次调用属于哪条链路 |
| `llm.operation` | 这次模型调用用于什么场景 |
| `llm.outcome` | 成功还是失败 |
| `llm.provider` | 用哪个供应商 |
| `llm.model` | 用哪个模型 |
| `llm.elapsed_ms` | 调用耗时 |
| `llm.prompt_tokens` | 输入 token |
| `llm.completion_tokens` | 输出 token |
| `llm.total_tokens` | 总 token |
| `llm.error_code` | 失败原因 |
| `http.status_code` | 对用户或上层返回的状态 |

### 4. `operation` 为什么重要

同样是 LLM 调用，场景可能不同：

```text
chat
stream_chat
tool_decision
tool_summary
structured_output
rag_final_answer
```

它们的风险和排查方式不同。

例如：

| operation | 重点 |
|---|---|
| `chat` | 普通回答是否成功、耗时和 token |
| `stream_chat` | 流式 chunk、首 token、流中断 |
| `tool_decision` | 模型是否请求工具 |
| `tool_summary` | 工具结果总结是否成功 |
| `structured_output` | 结构化抽取是否符合 schema |
| `rag_final_answer` | 是否基于检索上下文回答 |

所以日志里要有 `llm.operation`。

### 5. `outcome` 为什么重要

`outcome` 表示：

```text
success
failure
```

它的价值是后续统计：

```text
成功率
失败率
不同模型失败率
不同 operation 失败率
```

例如你可以判断：

```text
普通 chat 很稳定，但 tool_summary 经常失败。
```

这说明问题不是模型整体不可用，而是工具结果总结环节可能有 prompt 或上下文问题。

### 6. 为什么 extra_fields 不能随便进日志

生产代码里经常会出现：

```python
logger.info("xxx", extra={...})
```

如果 extra 里随便塞字典，很容易把敏感内容带进去。

本节的 `extra_fields` 规则是：

```text
只接受安全标量。
敏感字段直接过滤。
核心字段不能覆盖。
复杂对象不记录。
空字符串不记录。
```

安全标量包括：

```text
str
int
float
bool
```

不记录：

```text
dict
list
object
空字符串
NaN
无穷大
负 token
```

这是为了避免：

```text
完整 messages、完整 response、完整 tool_result 伪装成 extra 进入日志。
```

### 7. 当前 `LLMChatService` 的变化

本节修改：

```text
projects/ai-service/app/services/llm_service.py
```

原本 `_log_success`、`_log_failure`、`_log_stream_success`、`_log_stream_failure` 直接拼接字段。

现在它们先调用：

```text
build_safe_llm_log_payload(...)
```

再从安全 payload 里取字段输出。

好处是：

```text
当前日志格式基本保持不变。
安全规则集中到一个 helper。
后续新增 LLM 日志时可以复用同一套白名单。
```

### 8. 成功调用日志链路

普通成功调用：

```text
用户请求 /chat
LLMChatService.generate_reply
模型返回 completion
extract_token_usage
build_safe_llm_log_payload
logger.info llm_chat_succeeded
```

日志里有：

```text
provider
model
elapsed_ms
prompt_tokens
completion_tokens
total_tokens
trace_id
```

没有：

```text
用户原文
prompt
messages
模型完整回答
API key
```

### 9. 失败调用日志链路

失败调用：

```text
模型超时 / 限流 / 认证失败 / provider 异常
map_openai_error_to_app_exception
build_safe_llm_log_payload
logger.warning llm_chat_failed
```

日志里有：

```text
code
provider
model
status_code
elapsed_ms
trace_id
```

没有：

```text
provider 原始请求体
Authorization
API Key
完整 prompt
完整错误 response
```

### 10. 流式调用日志链路

流式成功：

```text
stream_reply
模型返回 stream
迭代 chunks
统计 chunk_count 和 content_chunk_count
提取 usage
build_safe_llm_log_payload
logger.info llm_stream_chat_succeeded
```

流式失败：

```text
stream 创建失败
或 stream 迭代中途失败
map_openai_error_to_app_exception
build_safe_llm_log_payload
logger.warning llm_stream_chat_failed
```

记录：

```text
chunks
content_chunks
tokens
elapsed_ms
error_code
```

不记录：

```text
每个 chunk 的 content
完整流式响应对象
```

### 11. 和第 4 节 tracing plan 的关系

第 4 节我们设计了：

```text
llm.call
llm.stream
llm.final_answer
```

本节进一步回答：

```text
这些 LLM span 上应该挂哪些安全日志字段。
```

例如：

```text
span: llm.call
log: llm_chat_succeeded
fields: provider, model, elapsed_ms, tokens
```

这就是生产化链路的一部分。

### 12. 本节没有做什么

本节没有做：

```text
真实调用模型
真实计算费用
接入日志平台
接入 Prometheus
接入 OpenTelemetry exporter
记录 prompt hash
记录 prompt template version
```

这些会在后续继续补。

当前最重要的是：

```text
先建立 LLM 日志安全边界。
```

## 本节代码讲解

### 1. `build_safe_llm_log_payload`

这是本节核心函数。

它负责生成安全日志 payload。

你可以把它理解成：

```text
LLM 日志字段的统一安检入口。
```

它接收：

```text
operation
outcome
provider
model
elapsed_ms
tokens
error_code
status_code
trace_id
extra_fields
```

它输出：

```text
dict[str, str | int | float | bool]
```

也就是结构化、安全的日志字段。

### 2. `LLM_LOG_SENSITIVE_KEYS`

这是敏感字段黑名单。

里面包含：

```text
api_key
authorization
prompt
messages
history
user_message
raw_response
final_answer
tool_result
document_content
```

这些字段一旦出现在 `extra_fields` 里，会被过滤。

### 3. `LLM_LOG_PROTECTED_KEYS`

这是受保护字段集合。

例如：

```text
llm.model
llm.provider
app.trace_id
llm.outcome
```

为什么要保护？

因为调用方不能通过 `extra_fields` 覆盖核心字段。

否则可能出现：

```text
真实 model 是 qwen3.7-plus，
extra_fields 里传入 llm.model=cheap-model，
日志被污染。
```

生产日志必须可信。

### 4. `find_forbidden_llm_log_fields`

这个函数用于检查一组字段里有没有敏感字段。

例如：

```python
find_forbidden_llm_log_fields({
    "Prompt": "...",
    "messages": [],
    "api_key": "..."
})
```

会返回：

```text
api_key
messages
prompt
```

后续如果要做更严格的日志审计，可以复用它。

### 5. `LLMChatService` 的接入方式

本节没有改变业务行为。

模型仍然按原来的方式调用。

改变的是日志生成前多了一层：

```text
安全 payload 生成
```

这属于工程质量改进。

它不会让模型回答更聪明，但会让系统上线后更安全、更可维护。

### 6. 本节测试重点

新增测试：

```text
projects/ai-service/tests/test_llm_logging_safety.py
```

覆盖：

| 测试点 | 目的 |
|---|---|
| 成功 payload | 确认 provider、model、tokens、elapsed_ms 被保留 |
| 失败 payload | 确认 error_code、status_code 被保留 |
| 敏感字段过滤 | 确认 prompt、messages、API key、Authorization、final_answer 不入日志 |
| 保护字段不可覆盖 | 确认 extra_fields 不能改写 model、provider、trace_id |
| 非法值过滤 | 确认复杂对象、空字符串、负 token 不入日志 |
| 禁用字段检测 | 确认可识别 prompt、messages、api_key |
| trace_id 复用 | 确认自动读取当前请求 trace_id |

相邻测试：

```text
tests/test_llm_service.py
```

确认原有 LLM 调用、流式输出、错误映射和日志行为没有被破坏。

## 常见误区

### 误区 1：排查模型问题必须记录完整 prompt

不对。

完整 prompt 风险太高。

优先记录：

```text
prompt_template_version
message_length
history_size
token 数
trace_id
错误码
```

### 误区 2：模型回答是系统生成的，所以可以随便记录

不对。

模型回答可能包含用户隐私、业务数据、RAG 文档内容，甚至被注入攻击诱导泄露内部信息。

### 误区 3：API Key 不会出现在日志里

不能这样假设。

异常对象、请求对象、headers、debug 输出都可能间接带出密钥。

所以日志 helper 要明确过滤 API key、Authorization、token。

### 误区 4：黑名单足够安全

不够。

黑名单很容易漏字段。

生产项目更推荐：

```text
白名单生成核心字段，黑名单过滤额外字段。
```

### 误区 5：流式日志可以记录每个 chunk 内容

不建议。

chunk 内容拼起来就是完整模型回答。

应该记录 chunk 数量、content chunk 数量、耗时和 token。

### 误区 6：失败日志应该把原始异常完整打出来

要谨慎。

可以记录安全错误码和必要堆栈，但不要把上游请求体、headers、密钥、prompt、messages 一起打出来。

### 误区 7：日志安全只是上线后的事

不对。

日志习惯要从开发阶段建立。

否则后面系统复杂后，很难再彻底清理所有不安全日志。

## 本节练习

### 练习 1：判断哪些字段可以记录

请判断下面字段哪些适合进入 LLM 调用日志：

```text
model
provider
elapsed_ms
prompt
messages
prompt_tokens
completion_tokens
api_key
error_code
final_answer
```

参考答案：

适合记录：

```text
model
provider
elapsed_ms
prompt_tokens
completion_tokens
error_code
```

不适合记录：

```text
prompt
messages
api_key
final_answer
```

原因：

前者是安全元信息，后者包含敏感内容、密钥或完整模型输出。

### 练习 2：为什么不能记录完整 messages

参考答案：

因为 `messages` 可能包含 system prompt、用户隐私、历史对话、RAG 文档、工具结果和内部规则。完整记录会带来隐私泄露、业务数据泄露和安全策略泄露风险。

### 练习 3：一次 LLM_TIMEOUT 应该记录哪些字段

参考答案：

应该记录：

```text
trace_id
operation
outcome=failure
provider
model
elapsed_ms
error_code=LLM_TIMEOUT
status_code=504
```

不应该记录：

```text
完整 prompt
完整 messages
API key
完整原始响应
```

### 练习 4：为什么 token 数可以记录

参考答案：

token 数是模型调用的元信息，不包含用户原文。它能帮助排查上下文过长、响应过长、成本升高等问题，也为后续成本统计提供基础。

### 练习 5：为什么 extra_fields 不能覆盖 `llm.model`

参考答案：

因为 `llm.model` 是核心事实字段，必须由调用方真实配置生成。如果 extra_fields 可以覆盖它，日志就可能被污染，导致排查和成本统计错误。

## 自测题

### 自测 1：LLM 调用日志最重要的安全原则是什么

参考答案：

记录安全元信息，不记录完整敏感内容。尤其不要记录完整 prompt、messages、用户输入、模型回答、API Key、Authorization 和完整工具结果。

### 自测 2：白名单字段和黑名单字段有什么区别

参考答案：

白名单字段是明确允许记录的字段，黑名单字段是明确禁止记录的字段。生产日志应以白名单为主，黑名单兜底。

### 自测 3：成功 LLM 调用最应该记录哪些元信息

参考答案：

`trace_id`、operation、outcome、provider、model、elapsed_ms、prompt_tokens、completion_tokens、total_tokens。

### 自测 4：失败 LLM 调用最应该记录哪些元信息

参考答案：

`trace_id`、operation、outcome=failure、provider、model、elapsed_ms、error_code、status_code。

### 自测 5：流式输出为什么记录 chunks 而不是 chunk 内容

参考答案：

chunk 内容属于模型输出正文，可能包含敏感信息；chunk 数量和 content chunk 数量是安全元信息，能用于排查流式过程和性能。

### 自测 6：本节新增 helper 对后续阶段有什么用

参考答案：

后续学习 token 成本、耗时拆解、多模型 fallback、RAG final answer、Tool summary、评估和监控时，都需要记录 LLM 调用元信息。这个 helper 能保证新增日志继续遵守同一套安全边界。

## 本节小结

本节你要记住：

```text
LLM 日志不是越详细越好。
能定位问题的安全元信息要记录。
完整 prompt、messages、用户输入、模型回答、工具结果和密钥不能直接记录。
```

当前项目本节新增了：

```text
llm_logging_safety.py
test_llm_logging_safety.py
```

并让：

```text
LLMChatService
```

的普通调用和流式调用日志先通过安全 payload 生成，再输出原有日志格式。

下一节是阶段 10 第 7 节：

```text
配置与密钥管理
```

它会继续学习 `.env`、`.env.example`、不同环境配置、API Key 管理、密钥不上 GitHub、配置分层和最小暴露。
