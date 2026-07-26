# 阶段 6 第 26 节：LangSmith tracing 基础

本节目标：真正理解 LangSmith tracing 是什么、它和普通日志有什么区别、`trace / run / thread / tags / metadata` 分别解决什么问题，并为当前智能工单 Agent 设计一套最小但安全的 LangSmith tracing 上下文。

这一节先不真实上报 LangSmith。

原因很简单：

```text
先学会“应该记录什么、怎么组织、哪些不能记录”，再学习“怎么接 API key 上报”。
```

如果还没想清楚字段和隐私边界，就直接打开 tracing，很容易把用户原始问题、订单信息、工单描述、模型回答、检索片段全文都发到外部观测平台里。生产系统里这不是小问题。

---

## 一、本节在主线里的位置

阶段 6 到这里已经学完两大块：

```text
第 1-12 节：Agent 评测
第 13-21 节：真实模型节点、模型输出校验、工具链路生产化
第 22-25 节：checkpoint 持久化、存储选型、thread_id 生命周期、会话过期清理
```

第 26 节开始进入生产化可观测性这一组：

```text
第 26 节：LangSmith tracing 基础
第 27 节：OpenTelemetry 基础
第 28 节：trace / span / log / metrics 的关系
第 29 节：生产日志字段设计
```

这一组要解决的是：

```text
系统出问题时，怎么知道它在哪一步错了？
模型回答变差时，怎么知道是 prompt、模型、检索、工具还是业务规则的问题？
用户说“刚才那个工单怎么没创建成功”时，怎么找到对应执行链路？
上线以后，怎么按环境、版本、意图、错误码、延迟去筛选和分析？
```

第 25 节解决的是“状态怎么保留和清理”。

第 26 节解决的是“执行过程怎么被看见”。

---

## 二、官方资料确认

本节参考了 LangChain / LangSmith 官方文档：

- LangSmith Observability concepts: https://docs.langchain.com/langsmith/observability-concepts
- Add metadata and tags to traces: https://docs.langchain.com/langsmith/add-metadata-tags
- LangGraph LangSmith Observability: https://docs.langchain.com/oss/python/langgraph/observability
- Prevent logging of sensitive data in traces: https://docs.langchain.com/langsmith/mask-inputs-outputs

官方文档里和本节最相关的点：

```text
1. LangSmith 用 project 组织 traces。
2. 一个 trace 表示一次应用操作的完整执行过程。
3. 一个 trace 由多个 run 组成。
4. run 表示一次具体工作单元，例如 LLM 调用、检索、工具调用、解析步骤。
5. 多轮对话可以用 thread 关联多个 traces。
6. thread 可以通过 metadata 里的 session_id 或 thread_id 进行分组。
7. tags 是字符串标签，用来分类、过滤、分组。
8. metadata 是 key-value 字典，用来保存环境、用户、内部关联 ID 等上下文。
9. LangGraph 调用时可以在 config 里传 tags 和 metadata。
10. 真实开启 tracing 通常需要 LANGSMITH_TRACING=true 和 LANGSMITH_API_KEY。
11. 敏感数据可以通过隐藏 inputs / outputs、隐藏 metadata、匿名化等方式处理。
```

这说明我们本节做的不是凭空设计。

我们是在官方 tracing 模型上，把当前项目里的 `trace_id`、`thread_id`、Agent 状态字段、错误码、节点路径映射成 LangSmith 以后可以使用的观测上下文。

---

## 三、基础知识铺垫

### 1. 什么是可观测性

可观测性英文是 observability。

它不是“打印一些日志”这么简单。

可观测性要回答的是：

```text
系统运行时内部到底发生了什么？
我能不能从外部记录反推出内部状态？
当用户说有问题时，我能不能定位是哪一步、哪次调用、哪个节点、哪个上游服务造成的？
```

普通后端系统里，可观测性通常包含三类东西：

```text
logs：日志
metrics：指标
traces：链路追踪
```

简单理解：

```text
logs    = 一条条事件记录
metrics = 数字统计，比如请求数、错误率、平均耗时
traces  = 一次请求从开始到结束经过了哪些步骤
```

举一个普通 Web API 的例子。

用户调用：

```text
POST /tickets
```

系统内部可能做了：

```text
接收 HTTP 请求
校验请求体
查询用户
查询订单
创建工单
写数据库
返回响应
```

日志可以记录：

```text
ticket_create_started
ticket_create_finished
```

指标可以记录：

```text
请求耗时 120ms
成功率 99.5%
错误率 0.5%
```

trace 可以把这一整串步骤串起来：

```text
HTTP request trace
  - validate request
  - query user
  - query order
  - create ticket
  - write database
```

这就是 trace 的价值：它不是孤立事件，而是一条完整路径。

### 2. AI 应用为什么更需要 tracing

传统后端一般是确定性流程。

同样输入、同样数据库状态，大多数情况下结果比较稳定。

AI 应用不同。

AI 应用里经常会有这些不确定因素：

```text
模型可能输出不同内容
模型可能不按格式返回
RAG 检索结果可能不够相关
工具调用参数可能缺字段
上游模型可能超时
Java 业务接口可能失败
同一个问题可能走不同节点
一次对话可能跨多个请求继续
```

所以 AI 应用排查问题时，不能只看最终回答。

你需要知道：

```text
用户原始输入是什么类型的问题？
意图识别结果是什么？
走了哪个 LangGraph 节点？
有没有检索知识库？
检索到了几条 citation？
有没有调用 query_order？
工具参数校验有没有失败？
有没有请求用户确认？
有没有执行写操作？
最终有没有 fallback？
耗时花在哪一步？
```

这些就是 tracing 要帮你看见的东西。

### 3. LangSmith 是什么

LangSmith 是 LangChain 生态里的 LLM 应用观测和评测平台。

它不是大模型。

它也不是向量数据库。

它主要帮助你做：

```text
记录 LLM 应用运行过程
查看一次 Agent 调用的完整链路
分析 prompt、模型调用、工具调用、检索结果
收集人工反馈
管理评测数据集
运行实验并比较效果
监控线上表现
```

放到我们的项目里：

```text
FastAPI 负责提供 HTTP 接口
LangGraph 负责组织智能工单 Agent 流程
Qdrant / Milvus 负责知识检索存储
Java mock service 负责模拟业务系统
LangSmith 负责看见 Agent 每次运行过程
```

所以 LangSmith 是“观测与评测层”。

### 4. trace 是什么

trace 可以理解成：

```text
一次完整任务的执行链路。
```

在我们当前项目里，一次用户请求可能是：

```text
用户问：我的订单 A1001 一直没发货，帮我创建工单
```

一次 trace 可以代表：

```text
这条消息进入智能工单 Agent 后，从开始到结束的完整处理过程。
```

它可能包含：

```text
normalize_user_input
classify_intent
decide_ticket_need
extract_ticket_fields
request_ticket_confirmation
```

如果后续用户确认，再继续执行：

```text
create_ticket
```

这可能是另一次 trace，但它们可以被同一个 `thread_id` 关联起来。

### 5. run 是什么

run 是 trace 里的一个工作单元。

你可以把 trace 和 run 的关系理解成：

```text
trace = 一整次请求的流水账
run   = 流水账里的一步
```

比如：

```text
trace: ticket_agent.invoke_thread
  run: normalize_user_input
  run: classify_intent
  run: LLM intent classification
  run: extract_ticket_fields
  run: LLM field extraction
  run: request_ticket_confirmation
```

LangSmith 里常见 run 类型包括：

```text
chain      复杂链路或 Agent / Graph
llm        一次模型调用
tool       一次工具调用
retriever  一次检索调用
parser     一次解析或格式转换
```

本节没有手动创建 run。

我们只是先准备好外层 trace 的上下文。

以后真实开启 LangSmith 后，LangChain / LangGraph 可以自动捕获很多内部 run。

### 6. thread 是什么

LangSmith 里的 thread 用来表示多轮对话。

官方文档说，多轮对话可以通过 metadata 里的特殊 key 来分组：

```text
session_id
thread_id
```

这和我们前面学的 LangGraph `thread_id` 很接近，但不要混淆。

在 LangGraph 里：

```text
thread_id 用来让 checkpointer 保存和恢复状态。
```

在 LangSmith 里：

```text
thread_id / session_id 用来把多次 trace 归到同一段对话下面，方便查看对话历史。
```

它们可以使用同一个值。

例如：

```text
LangGraph config.configurable.thread_id = ticket-thread-001
LangSmith metadata.thread_id            = ticket-thread-001
LangSmith metadata.session_id           = ticket-thread-001
```

这样做的好处是：

```text
checkpoint 恢复用的是同一个 ID
trace 分组看到的也是同一个 ID
日志里查到的也是同一个 ID
```

一个 ID 可以贯穿：

```text
HTTP 请求
日志
LangGraph checkpoint
LangSmith traces
人工排查
```

### 7. tags 是什么

tags 是标签。

它是字符串列表。

适合放：

```text
环境：env:local、env:test、env:production
服务：ai-service
组件：ticket-agent
框架：langgraph
操作：operation:invoke_thread
意图：intent:ticket_request
实验：experiment:v2-prompt
```

tags 的特点是：

```text
短
数量少
适合筛选
适合分组
不适合放复杂信息
不适合放用户原文
```

比如以后你在 LangSmith 里可以筛选：

```text
env:production
ticket-agent
intent:ticket_request
```

然后只看生产环境里智能工单 Agent 的工单请求。

### 8. metadata 是什么

metadata 是 key-value 字典。

适合放更具体的上下文字段：

```text
trace_id
thread_id
actor_id
operation
node_count
last_node
order_query_status
ticket_creation_status
agent_error_code
elapsed_ms
```

metadata 的特点是：

```text
比 tags 更结构化
可以按字段过滤
可以保存具体状态
但不能无脑塞大对象
也不能塞敏感内容
```

例如：

```json
{
  "component": "ticket_agent",
  "operation": "invoke_thread",
  "trace_id": "trace-001",
  "thread_id": "ticket-thread-001",
  "intent": "ticket_request",
  "node_count": 5,
  "last_node": "request_ticket_confirmation",
  "ticket_write_safety_status": "confirmation_required",
  "fallback_used": false
}
```

这类信息很适合进入 metadata。

它能帮你排查：

```text
这次请求走到了哪个节点？
是不是因为没确认而没有创建工单？
有没有 fallback？
有没有上游错误？
这次 trace 属于哪个 thread？
```

### 9. inputs / outputs 和 metadata 的区别

很多初学者会把所有东西都塞进 metadata。

这是错误习惯。

区别要分清楚：

```text
inputs   = 这个 run 的输入
outputs  = 这个 run 的输出
metadata = 用来解释和筛选这个 run 的上下文字段
tags     = 用来粗粒度分类的标签
```

例如：

```text
用户原始问题：不应该塞进 metadata
模型完整回答：不应该塞进 metadata
检索片段全文：不应该塞进 metadata
订单查询完整结果：不应该塞进 metadata
```

这些内容即使未来要记录，也应该经过明确的输入输出脱敏策略，而不是混进 metadata。

本节代码选择了保守策略：

```text
metadata 只保存短字段、状态字段、计数字段、错误码、内部关联 ID。
```

### 10. LangSmith 和普通日志有什么区别

我们已经在阶段 5 第 24 节做过日志和 `trace_id`。

普通日志长这样：

```text
ticket_agent_started operation=invoke_thread thread_id=ticket-thread-001
ticket_agent_finished operation=invoke_thread elapsed_ms=25.32 intent=ticket_request
```

日志的优点：

```text
便宜
通用
容易接入
适合记录后端事件
适合被 ELK、Loki、CloudWatch 等日志系统采集
```

日志的缺点：

```text
需要自己搜索
上下级关系不明显
LLM 调用、prompt、工具调用、检索步骤不一定自动组织好
很难直接按 Agent 一次运行来查看
```

LangSmith tracing 的优点：

```text
以 trace 为中心看一次 Agent 运行
能看到 LLM / retriever / tool 等步骤
适合调试 prompt、模型输出、工具链路
可以和 eval、dataset、feedback 结合
可以按 tags 和 metadata 过滤
```

LangSmith tracing 的缺点：

```text
需要额外平台和 API key
可能产生成本或数据保留问题
必须认真处理隐私和敏感数据
不是所有后端系统都用它，不能替代通用日志
```

正确关系是：

```text
日志不是 LangSmith 的替代品。
LangSmith 也不是日志的替代品。

日志负责通用后端排查。
LangSmith 负责 LLM / Agent 执行链路排查。
```

### 11. tracing 和 eval 有什么区别

阶段 6 前半段学过 eval。

eval 解决的是：

```text
系统表现好不好？
改了 prompt 以后有没有退步？
意图识别准不准？
字段提取准不准？
RAG 回答有没有引用依据？
```

tracing 解决的是：

```text
这一次执行到底发生了什么？
哪一步耗时？
哪一步报错？
模型输入输出是什么？
工具有没有被调用？
路由为什么这么走？
```

关系是：

```text
eval 发现“结果不好”
tracing 帮你追“为什么不好”
```

例如：

```text
eval 报告说：ticket_request 召回率下降
tracing 里看：classify_intent 的模型输出经常给成 policy_question
再看 prompt：ticket_request 的定义不够清楚
再改 prompt
再跑 regression eval
```

这就是生产 AI 工程里的闭环。

### 12. dataset 和 experiment 是什么

LangSmith 还有两个很重要的概念：

```text
dataset
experiment
```

dataset 可以理解为：

```text
一组评测样本。
```

类似我们项目里的：

```text
data/agent_eval/agent_cases.json
```

experiment 可以理解为：

```text
拿某个版本的系统，在某个 dataset 上跑出来的一次实验结果。
```

例如：

```text
experiment: prompt_v1
experiment: prompt_v2
```

然后比较：

```text
哪个版本意图识别更准？
哪个版本字段提取错误更少？
哪个版本平均延迟更低？
哪个版本 fallback 更少？
```

本节不接 LangSmith dataset / experiment。

原因是我们本地已经有自己的 eval 脚本和报告，后面如果要接 LangSmith，可以把这些评测结果迁移或同步过去。

### 13. 隐私边界为什么非常重要

AI 应用 tracing 有一个特殊风险：

```text
它很容易记录大量文本。
```

这些文本可能包括：

```text
用户原始问题
手机号
地址
订单号
投诉内容
支付信息
客服内部规则
检索到的知识库全文
模型完整回答
系统 prompt
工具返回的业务数据
```

所以 LangSmith 这类平台虽然有隐藏 inputs / outputs、隐藏 metadata、匿名化等机制，但工程上最好的习惯是：

```text
从源头就不要把不该进 metadata 的东西放进去。
```

本节代码明确排除了这些字段：

```text
user_message
normalized_message
rag_query
rag_answer
rag_citations
rag_suggestions
final_answer
ticket_fields
ticket_creation_args
created_ticket
order_query_result
pending_ticket_confirmation
```

注意：这不等于未来永远不能记录输入输出。

未来如果要记录，需要满足：

```text
有明确业务目的
有脱敏策略
有环境开关
有保留周期
有访问权限
有合规确认
```

本节先坚持最小安全边界。

---

## 四、本节主题系统讲解

### 1. 当前项目已经有什么

当前项目已经有这些基础：

```text
app/core/trace.py
  generate_trace_id()
  get_or_create_trace_id()
  get_trace_id()
  build_trace_headers()

app/agents/ticket_agent.py
  build_ticket_agent_observation_metadata()
  log_ticket_agent_run_started()
  log_ticket_agent_run_finished()
  log_ticket_agent_run_failed()
  build_ticket_agent_thread_config()

app/agents/thread_lifecycle.py
  normalize_ticket_agent_thread_id()
  generate_ticket_agent_thread_id()
  create_ticket_agent_thread_binding()
  evaluate_ticket_agent_thread_resume()
```

这些已经能做到：

```text
日志里带 trace_id
LangGraph checkpoint 用 thread_id
thread_id 有基本安全校验
Agent 运行结束时能输出一些结构化日志字段
```

但是还缺 LangSmith 视角的组织方式：

```text
LangSmith project 叫什么？
一次 Agent 运行的 run_name 叫什么？
哪些 tags 用来过滤？
哪些 metadata 用来排查？
thread_id 怎么同时服务 checkpoint 和 trace 分组？
哪些字段不能进入 tracing metadata？
```

这就是本节新增模块要解决的问题。

### 2. 为什么不直接改 `ticket_agent.py`

可以直接在 `run_ticket_agent_in_thread()` 里塞 LangSmith 代码。

但现在不适合这么做。

原因有三个：

```text
1. 我们还没正式打开 LangSmith API key。
2. 这一节的学习重点是 tracing 字段设计，不是平台接入。
3. 直接改主流程，容易把教学代码和生产运行代码混在一起。
```

所以本节采取独立模块：

```text
app/agents/langsmith_tracing.py
```

它做三件事：

```text
1. 生成稳定 tags。
2. 从 Agent state 里提取安全 metadata。
3. 生成未来可传给 LangGraph config / LangSmith tracing_context 的上下文对象。
```

这样以后真正打开 LangSmith 时，不需要重新思考字段，只要把这个上下文接到真实调用处即可。

### 3. 当前项目和 LangSmith 概念的映射

| LangSmith 概念 | 当前项目里的对应物 | 本节怎么处理 |
| --- | --- | --- |
| project | `ai-service-ticket-agent` | 常量 `TICKET_AGENT_LANGSMITH_PROJECT_NAME` |
| trace | 一次 Agent 调用 | 用 `run_name`、`tags`、`metadata` 描述 |
| run | 节点、模型调用、工具调用等工作单元 | 本节先不手动创建 run |
| thread | 多轮会话 | metadata 里放 `thread_id` / `session_id` |
| tags | 分类标签 | `ai-service`、`ticket-agent`、`langgraph`、`env:*`、`operation:*`、`intent:*` |
| metadata | 筛选和排查字段 | trace_id、thread_id、状态、错误码、节点统计 |
| inputs | 用户输入 / 函数输入 | 本节不处理，避免误传敏感文本 |
| outputs | 模型回答 / 函数返回 | 本节不处理，避免误传敏感文本 |
| feedback | 人工或规则评分 | 后续可和 eval 结合 |
| dataset | 评测样本集 | 可对应 `agent_cases.json` |
| experiment | 一次评测实验 | 后续可对应不同 prompt / 模型版本 |

### 4. 本节设计的 tags

基础 tags：

```text
ai-service
ticket-agent
langgraph
```

环境 tag：

```text
env:local
env:test
env:production
```

操作 tag：

```text
operation:invoke
operation:invoke_safe
operation:invoke_thread
operation:resume_interrupt
```

意图 tag：

```text
intent:policy_question
intent:order_query
intent:ticket_request
intent:smalltalk
intent:unsupported
intent:unclear
```

为什么这些适合当 tag？

因为它们：

```text
短
稳定
有限枚举
适合筛选
不包含用户隐私
```

举例：

```text
我要看测试环境所有工单请求：
env:test + intent:ticket_request

我要看生产环境所有 resume_interrupt：
env:production + operation:resume_interrupt

我要看当前 Agent 所有 trace：
ticket-agent
```

### 5. 本节设计的 metadata

本节 metadata 分成几类。

第一类：身份和关联字段。

```text
component
operation
trace_id
thread_id
session_id
actor_id
```

这些字段回答：

```text
这是哪个组件？
这次执行是什么操作？
它对应哪条后端 trace？
它属于哪个对话 thread？
它属于哪个用户或内部 actor？
```

第二类：路径字段。

```text
node_count
last_node
```

这些字段回答：

```text
这次 Agent 走了几步？
最后停在哪个节点？
```

第三类：业务状态字段。

```text
intent
ticket_need_source
order_query_status
rag_answer_status
ticket_field_extraction_source
ticket_fields_complete
ticket_confirmation_required
ticket_confirmation_approved
ticket_write_safety_status
ticket_creation_status
```

这些字段回答：

```text
用户意图是什么？
RAG 有没有答上来？
订单查询成功了吗？
字段是否齐全？
是否需要确认？
写操作是否被安全策略阻断？
工单有没有创建成功？
```

第四类：错误字段。

```text
order_query_error_code
order_query_error_kind
order_query_error_action
ticket_creation_error_code
agent_error_code
agent_error_node
fallback_used
```

这些字段回答：

```text
失败类型是什么？
失败发生在哪个节点？
系统有没有进入 fallback？
后续应该让用户补信息、稍后重试，还是转人工？
```

第五类：计数字段。

```text
rag_citation_count
missing_ticket_fields_count
```

为什么用计数，而不是直接放原文？

因为：

```text
citation 全文可能很长，也可能包含内部知识库内容。
missing_ticket_fields 只需要知道缺几个字段，通常不用把完整对象放入 metadata。
```

第六类：性能字段。

```text
elapsed_ms
```

它回答：

```text
这次 Agent 调用用了多久？
```

以后如果接入更细粒度 run，还可以知道：

```text
模型调用耗时
RAG 检索耗时
Java API 耗时
工具校验耗时
```

### 6. 为什么 metadata 不放完整 state

当前 `TicketAgentState` 很大。

里面有：

```text
user_message
normalized_message
rag_citations
ticket_fields
order_query_result
created_ticket
final_answer
```

这些字段对调试有价值，但不适合直接进入 metadata。

原因：

```text
1. 可能包含用户隐私。
2. 可能包含订单或工单业务数据。
3. 可能包含知识库片段全文。
4. 体积可能很大。
5. metadata 是用来筛选和定位，不是用来保存完整业务上下文。
```

所以本节采用策略：

```text
保存状态摘要，不保存原始文本和完整对象。
```

例如：

```text
保存 rag_citation_count = 2
不保存 rag_citations = [{"content": "..."}]

保存 missing_ticket_fields_count = 1
不保存 ticket_fields = {"description": "..."}

保存 order_query_status = succeeded
不保存 order_query_result = {"receiver_phone": "..."}
```

这就是生产系统里很重要的观念：

```text
观测数据也需要数据建模。
```

### 7. 为什么 `thread_id` 要复用生命周期校验

第 24 节已经做过：

```python
normalize_ticket_agent_thread_id(thread_id)
```

它会拒绝：

```text
空字符串
太长的字符串
带路径穿越风险的字符串
包含不安全字符的字符串
```

第 26 节没有重新写一套校验。

而是复用：

```python
normalize_ticket_agent_thread_id()
```

这是很重要的工程习惯：

```text
同一个业务概念，应该尽量复用同一套校验规则。
```

否则容易出现：

```text
checkpoint 认为 thread_id 不合法
LangSmith metadata 却记录了这个 thread_id
日志里又记录了另一个格式
```

最终排查时会非常混乱。

### 8. 为什么同时放 `thread_id` 和 `session_id`

LangSmith 官方文档提到，多轮对话可以通过 metadata 里的：

```text
session_id
thread_id
```

来关联。

本节代码在有 `thread_id` 时同时放：

```text
metadata["thread_id"] = normalized_thread_id
metadata["session_id"] = normalized_thread_id
```

这样做的目的：

```text
兼容 LangSmith 对 conversation thread 的分组习惯。
也让读代码的人一眼知道：这个 thread_id 同时也是这段会话的 session_id。
```

如果以后团队明确只用其中一个字段，也可以收敛成一个。

现在学习阶段保留两个字段更直观。

### 9. 本节没有做什么

本节刻意不做这些：

```text
不配置 LANGSMITH_API_KEY
不设置 LANGSMITH_TRACING=true
不真实发送 trace 到 LangSmith
不接 LangSmith dashboard
不做 dataset / experiment 同步
不做 OpenTelemetry
不做 tracing 采样率
不做生产隐私脱敏中间件
```

不是这些不重要。

而是学习顺序应该是：

```text
先理解概念
再设计字段
再写本地纯函数测试
再真实接入平台
再考虑生产采样、脱敏、保留周期、权限和成本
```

---

## 五、本节新增代码

本节新增：

```text
projects/ai-service/app/agents/langsmith_tracing.py
projects/ai-service/tests/test_ticket_agent_langsmith_tracing.py
```

### 1. `TicketAgentLangSmithTraceContext`

这个类表示一次 Agent 调用准备好的 LangSmith tracing 上下文。

它包含：

```python
project_name: str
run_name: str
tags: list[str]
metadata: dict[str, LangSmithMetadataValue]
thread_id: str | None
```

可以理解成：

```text
还没真正上报之前，先把“这次运行该怎么被 LangSmith 看见”整理成一个对象。
```

为什么不用普通 dict 到处传？

因为普通 dict 容易变成：

```text
这个地方叫 project
那个地方叫 project_name
这个地方 tags 是 tuple
那个地方 tags 是 list
有的地方忘了 metadata
有的地方忘了 run_name
```

用 dataclass 可以让结构更清晰。

### 2. `to_langgraph_config()`

这个方法返回未来可以传给 LangGraph `graph.invoke(..., config=...)` 的结构。

形状大概是：

```python
{
    "run_name": "ticket_agent.invoke_thread",
    "tags": ["ai-service", "ticket-agent", "langgraph", "env:test"],
    "metadata": {
        "trace_id": "trace-001",
        "thread_id": "ticket-thread-001",
        "session_id": "ticket-thread-001",
    },
    "configurable": {
        "thread_id": "ticket-thread-001",
    },
}
```

这里要看清楚：

```text
configurable.thread_id 是给 LangGraph checkpoint 用的。
metadata.thread_id / metadata.session_id 是给 LangSmith trace 分组和筛选用的。
```

它们值相同，但作用不同。

### 3. `to_tracing_context_kwargs()`

这个方法返回未来可以传给 LangSmith `tracing_context()` 的参数：

```python
{
    "project_name": "ai-service-ticket-agent",
    "enabled": True,
    "tags": [...],
    "metadata": {...},
}
```

未来真实接入时，形状大概是：

```python
import langsmith as ls

context = build_ticket_agent_langsmith_trace_context(
    state,
    operation="invoke_thread",
    thread_id="ticket-thread-001",
    environment="local",
)

with ls.tracing_context(**context.to_tracing_context_kwargs()):
    result = graph.invoke(
        build_ticket_agent_input(user_message),
        config=context.to_langgraph_config(),
    )
```

本节没有执行这段。

它只是告诉你以后接入时，这套上下文该怎么用。

### 4. `normalize_langsmith_tag()`

这个函数负责把标签清洗成稳定形式。

例如：

```text
"  Local Dev  "              -> "local-dev"
"operation:Invoke Thread"    -> "operation:invoke-thread"
None                         -> 忽略
空字符串                      -> 忽略
```

为什么 tag 要清洗？

因为 tag 是用来筛选的。

如果不清洗，可能出现：

```text
env:Local
Env:local
env:local
env: local
```

这些在人的眼里意思差不多，但在系统里就是不同标签。

稳定标签能减少后续筛选混乱。

### 5. `build_langsmith_trace_tags()`

这个函数按固定规则生成 tags：

```python
build_langsmith_trace_tags(
    environment="test",
    operation="invoke_thread",
    intent="ticket_request",
    extra_tags=["regression"],
)
```

会得到：

```python
[
    "ai-service",
    "ticket-agent",
    "langgraph",
    "env:test",
    "operation:invoke_thread",
    "intent:ticket_request",
    "regression",
]
```

它还会去重。

例如额外传入：

```python
extra_tags=["ticket-agent"]
```

不会生成重复的 `ticket-agent`。

### 6. `build_ticket_agent_langsmith_metadata()`

这是本节最核心的函数。

它从 Agent state 里提取安全字段。

输入：

```python
state = {
    "agent_trace_id": "trace-001",
    "intent": "ticket_request",
    "ticket_write_safety_status": "confirmation_required",
    "node_history": ["normalize_user_input", "extract_ticket_fields"],
}
```

调用：

```python
metadata = build_ticket_agent_langsmith_metadata(
    state,
    operation="invoke_thread",
    thread_id="ticket-thread-001",
    actor_id="demo_user_001",
    elapsed_ms=12.3456,
)
```

结果会包含：

```python
{
    "component": "ticket_agent",
    "operation": "invoke_thread",
    "trace_id": "trace-001",
    "thread_id": "ticket-thread-001",
    "session_id": "ticket-thread-001",
    "actor_id": "demo_user_001",
    "intent": "ticket_request",
    "node_count": 2,
    "last_node": "extract_ticket_fields",
    "ticket_write_safety_status": "confirmation_required",
    "elapsed_ms": 12.35,
}
```

重点不是代码多复杂。

重点是字段选择：

```text
只保留方便定位问题的短字段。
不保留原始用户文本、完整工单字段、订单查询完整结果和模型完整回答。
```

### 7. `extra_metadata` 为什么不能覆盖核心字段

本节支持额外 metadata：

```python
extra_metadata={"experiment_name": "baseline"}
```

但它不能覆盖这些核心字段：

```text
component
operation
trace_id
thread_id
session_id
actor_id
```

原因：

```text
这些字段是排查链路的核心标识。
如果调用方随便覆盖，trace 就不可信。
```

例如调用方传：

```python
extra_metadata={"trace_id": "wrong"}
```

代码会忽略它，保留真实 `trace_id`。

这就是“保护核心观测字段”。

### 8. 为什么复杂对象会被忽略

本节 metadata 只接受：

```text
str
int
float
bool
```

复杂对象会被忽略：

```python
{"raw_payload": {"too": "large"}}
```

不会进入 metadata。

原因：

```text
metadata 不是业务数据仓库。
复杂对象更容易携带隐私，也更难过滤和查询。
```

如果未来真的需要保存复杂对象，应该单独设计：

```text
脱敏规则
字段白名单
存储位置
访问权限
保留周期
```

不要直接丢给 metadata。

### 9. 文本为什么限制长度

本节把 metadata 文本限制在：

```text
200 字符
```

原因：

```text
metadata 应该短而稳定。
长文本会增加体积，也会让筛选字段失去意义。
```

如果真的需要看长文本，应该放到受控的 inputs / outputs 记录里，并配合脱敏和隐藏策略。

---

## 六、本节测试讲解

本节测试文件：

```text
projects/ai-service/tests/test_ticket_agent_langsmith_tracing.py
```

测试重点不是“为了覆盖率而覆盖率”。

测试的核心目的是验证四条规则。

### 1. tags 要稳定

测试确认：

```text
空白会去掉
大小写会统一
空标签会忽略
重复标签会去掉
```

这保证以后在 LangSmith 里筛选不会乱。

### 2. metadata 要可观测

测试确认 metadata 会包含：

```text
trace_id
thread_id
session_id
actor_id
intent
node_count
last_node
elapsed_ms
```

这些字段能帮助你定位一次 Agent 执行。

### 3. 敏感 payload 要排除

测试确认这些字段不会进入 metadata：

```text
user_message
normalized_message
final_answer
ticket_fields
created_ticket
order_query_result
pending_ticket_confirmation
```

这是本节最重要的安全测试。

### 4. thread_id 要复用校验

测试确认非法 `thread_id` 会被拒绝。

例如：

```text
../bad-thread
```

不会进入 LangSmith metadata，也不会进入 LangGraph config。

---

## 七、以后真实接入 LangSmith 时怎么做

以后如果要真实接入 LangSmith，通常需要：

```text
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=你的 LangSmith API key
LANGSMITH_PROJECT=ai-service-ticket-agent
```

但注意：

```text
API key 不应该写进代码。
API key 不应该提交到 GitHub。
API key 应该放本机 .env 或部署平台的 secret 配置里。
```

以后真实接入时，调用形态可能会接近：

```python
context = build_ticket_agent_langsmith_trace_context(
    state,
    operation="invoke_thread",
    thread_id=thread_id,
    actor_id=actor_id,
    environment=settings.app_env,
)

with ls.tracing_context(**context.to_tracing_context_kwargs()):
    result = graph.invoke(
        initial_state,
        config=context.to_langgraph_config(),
    )
```

如果要进一步保护隐私，还要考虑：

```text
LANGSMITH_HIDE_INPUTS=true
LANGSMITH_HIDE_OUTPUTS=true
LANGSMITH_HIDE_METADATA=true 或自定义 hide_metadata
Client(anonymizer=...)
按环境决定是否开启 tracing
按用户、租户、请求类型决定是否采样
```

本节先不做这些，是因为它们属于后续生产接入策略。

---

## 八、容易混淆的点

### 1. `trace_id` 和 LangSmith trace ID 是不是一个东西

不完全是。

当前项目里的 `trace_id` 是我们自己的请求关联 ID。

LangSmith 也会有自己的 trace / run 标识。

本节把项目 `trace_id` 放进 metadata：

```text
metadata["trace_id"] = 当前项目 trace_id
```

这样做的价值是：

```text
你可以用同一个 trace_id 在后端日志和 LangSmith 之间互相跳转排查。
```

### 2. `thread_id` 是不是等于一次请求

不是。

`thread_id` 表示一段对话或一个可恢复流程。

一次请求可能是一个 trace。

多次请求可以属于同一个 thread。

例如：

```text
第 1 次请求：用户要求创建工单，系统请求确认
第 2 次请求：用户点击确认，系统继续创建工单
```

这两次请求可以是两个 trace，但共享同一个 `thread_id`。

### 3. tags 和 metadata 到底怎么选

简单判断：

```text
想按它快速筛选大类 -> tag
想按 key-value 查具体状态 -> metadata
可能很长或敏感 -> 都不要直接放
```

例如：

```text
env:test                         -> tag
intent:ticket_request            -> tag
ticket_creation_status=blocked   -> metadata
user_message=我的手机号是...       -> 不直接放
```

### 4. LangSmith 能不能替代测试

不能。

LangSmith 能帮你看见执行过程。

测试能帮你自动判断代码是否符合预期。

eval 能帮你判断 AI 输出质量是否达标。

三者关系：

```text
测试：代码是否正确
eval：AI 行为是否达标
tracing：一次运行发生了什么
```

### 5. 为什么这节只做“元数据准备”

因为生产 tracing 最怕两件事：

```text
记录太少：出问题查不到原因
记录太多：泄漏数据、成本上升、页面混乱
```

所以正确学习顺序不是先开平台，而是先回答：

```text
哪些字段真的有用？
哪些字段有风险？
字段名称怎么稳定？
如何和现有 trace_id / thread_id 对齐？
```

本节就是先把这一步学扎实。

---

## 九、本节练习

### 练习 1：解释 trace 和 run 的区别

问题：用自己的话解释 LangSmith 里的 trace 和 run 有什么区别。

参考答案：

```text
trace 是一次完整操作的执行链路，比如一次智能工单 Agent 调用。
run 是 trace 里面的一个具体步骤，比如一次 LLM 调用、一次 RAG 检索、一次工具调用或一个节点执行。
trace 是整体，run 是步骤。
```

### 练习 2：判断字段应该放在哪里

问题：下面字段分别应该放 tags、metadata，还是不应该直接放？

```text
env:production
intent:ticket_request
trace_id
thread_id
user_message
final_answer
ticket_creation_status
order_query_result
elapsed_ms
```

参考答案：

```text
env:production -> tags
intent:ticket_request -> tags
trace_id -> metadata
thread_id -> metadata
user_message -> 不应该直接放
final_answer -> 不应该直接放
ticket_creation_status -> metadata
order_query_result -> 不应该直接放
elapsed_ms -> metadata
```

解释：

```text
tags 适合短标签和分类。
metadata 适合结构化状态字段。
用户原文、模型完整回答、订单查询完整结果可能包含敏感信息，不应该无脑进入 tracing metadata。
```

### 练习 3：为什么 `thread_id` 要同时出现在 LangGraph 和 LangSmith 里

问题：`configurable.thread_id` 和 `metadata.thread_id` 的作用分别是什么？

参考答案：

```text
configurable.thread_id 是给 LangGraph checkpoint 用的，它决定状态保存和恢复属于哪个线程。
metadata.thread_id 是给 LangSmith 观测用的，它让多次 trace 能按同一个会话分组，也方便过滤查询。
两者可以使用同一个值，但作用不同。
```

### 练习 4：为什么不把完整 `TicketAgentState` 放进 metadata

问题：完整 state 对调试很有帮助，为什么本节不直接把它放进 metadata？

参考答案：

```text
因为完整 state 里可能包含用户原始输入、订单信息、工单描述、检索片段全文、模型回答等敏感或大体积内容。
metadata 应该服务于筛选和定位，不应该变成业务数据仓库。
更安全的做法是只放短字段、状态字段、错误码、计数字段和内部关联 ID。
```

### 练习 5：读代码判断结果

问题：下面代码会生成哪些关键 metadata？

```python
state = {
    "agent_trace_id": "trace-001",
    "intent": "order_query",
    "order_query_status": "failed",
    "order_query_error_code": "ORDER_QUERY_TIMEOUT",
    "fallback_used": True,
    "node_history": ["normalize_user_input", "classify_intent", "query_order"],
}

metadata = build_ticket_agent_langsmith_metadata(
    state,
    operation="invoke_thread",
    thread_id="ticket-thread-001",
    actor_id="demo_user_001",
    elapsed_ms=305.129,
)
```

参考答案：

```python
{
    "component": "ticket_agent",
    "operation": "invoke_thread",
    "trace_id": "trace-001",
    "thread_id": "ticket-thread-001",
    "session_id": "ticket-thread-001",
    "actor_id": "demo_user_001",
    "node_count": 3,
    "last_node": "query_order",
    "intent": "order_query",
    "order_query_status": "failed",
    "order_query_error_code": "ORDER_QUERY_TIMEOUT",
    "fallback_used": True,
    "rag_citation_count": 0,
    "missing_ticket_fields_count": 0,
    "elapsed_ms": 305.13,
}
```

可能还会有其他字段，取决于 state 里是否提供了对应状态字段。

### 练习 6：设计一个排查查询

问题：如果线上用户反馈“点击确认后工单没有创建”，你会优先用哪些 tags / metadata 去查？

参考答案：

```text
tags:
env:production
ticket-agent
operation:resume_interrupt

metadata:
thread_id
actor_id
ticket_confirmation_approved
ticket_write_safety_status
ticket_creation_status
ticket_creation_error_code
agent_error_code
agent_error_node
fallback_used
```

排查思路：

```text
先用 thread_id 找到同一段会话。
再看 resume_interrupt 对应 trace。
如果 ticket_confirmation_approved=false，说明确认没有成功进入流程。
如果 ticket_write_safety_status 不是 authorized，说明写操作被安全策略阻断。
如果 ticket_creation_status=failed，看 ticket_creation_error_code。
如果 fallback_used=true，看 agent_error_code 和 agent_error_node。
```

---

## 十、自测题

### 自测 1：LangSmith 是不是大模型？

答案：

```text
不是。LangSmith 是 LLM 应用的观测、调试、评测和监控平台。它可以记录和分析模型调用、工具调用、检索流程等，但它本身不是用来生成文本的大模型。
```

### 自测 2：metadata 里能不能放用户原始消息？

答案：

```text
不建议直接放。用户原始消息可能包含隐私或敏感业务信息。即使未来需要记录输入，也应该使用受控的 inputs / outputs 策略，并配合脱敏、隐藏、权限和保留周期。
```

### 自测 3：tags 适合放什么？

答案：

```text
tags 适合放短、稳定、低敏感、用于分类和过滤的字符串，例如 env:test、ticket-agent、langgraph、operation:invoke_thread、intent:ticket_request。
```

### 自测 4：metadata 适合放什么？

答案：

```text
metadata 适合放结构化上下文字段，例如 trace_id、thread_id、operation、node_count、last_node、order_query_status、ticket_creation_status、agent_error_code、elapsed_ms。
```

### 自测 5：为什么 `session_id` 和 `thread_id` 可以使用同一个值？

答案：

```text
因为当前项目里 LangGraph 的 thread_id 本来就表示一段可恢复会话。LangSmith 也可以用 session_id 或 thread_id 把多个 traces 关联成一段 conversation thread。使用同一个值可以让 checkpoint、日志和 tracing 更容易互相对应。
```

### 自测 6：LangSmith tracing 能不能替代日志？

答案：

```text
不能。日志适合通用后端排查和系统事件记录；LangSmith tracing 更适合 LLM / Agent 执行链路、prompt、模型、检索和工具调用排查。生产系统通常两者都需要。
```

### 自测 7：为什么本节不真实上报 LangSmith？

答案：

```text
因为本节的核心目标是先理解 tracing 概念和字段设计，并建立安全 metadata 白名单。真实上报需要 API key、环境变量、隐私策略和平台配置，应该在字段边界清楚之后再接。
```

### 自测 8：如果 `extra_metadata` 传入 `trace_id="wrong"`，为什么代码会忽略它？

答案：

```text
trace_id 是核心关联字段，不能被调用方随意覆盖。否则同一次运行在日志和 tracing 里可能对应不上，排查链路会失真。
```

---

## 十一、本节命令

在 `projects/ai-service` 目录运行：

```powershell
uv run pytest tests/test_ticket_agent_langsmith_tracing.py
```

本节当前测试结果：

```text
8 passed
```

后续还需要在提交前运行全量测试：

```powershell
uv run pytest
```

---

## 十二、本节小结

本节你需要真正掌握的不是某个 API 怎么写，而是这套思维：

```text
1. AI 应用需要 tracing，因为一次回答背后有模型、检索、工具、状态和业务规则。
2. trace 表示一次完整操作，run 表示其中一步。
3. thread 用来关联多轮对话或可恢复流程。
4. tags 用来做粗粒度筛选。
5. metadata 用来做结构化定位。
6. 日志、tracing、eval 是互补关系，不是互相替代。
7. tracing 字段必须有隐私边界，不能把完整 state 原样塞进去。
8. 当前项目应该让 trace_id、thread_id、LangGraph checkpoint 和 LangSmith metadata 对齐。
```

本节完成后，当前项目已经具备：

```text
本地 trace_id
结构化运行日志
thread_id 生命周期
checkpoint 清理策略
LangSmith tracing 上下文准备
安全 metadata 白名单
tags 规范化
LangGraph config / LangSmith tracing_context 的未来接入形状
```

下一节进入：

```text
阶段 6 第 27 节：OpenTelemetry 基础
```

下一节会开始补通用可观测性标准：

```text
为什么不是所有 tracing 都应该绑定某一个平台？
OpenTelemetry 的 trace / span / attribute 是什么？
它和 LangSmith 的 trace / run / metadata 有什么相似和不同？
为什么生产系统常常需要 vendor-neutral observability？
```
