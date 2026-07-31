# 阶段 9 第 22 节：RAG 与 Agent 的组合边界

## 本节定位

本节学习 RAG 与 Agent 的组合边界。

它接在第 21 节多知识库路由后面：上一节解决“RAG 应该查哪个知识库”，本节解决“什么时候用 RAG，什么时候用 Agent，什么时候用 Tool，谁负责流程，谁负责资料，谁负责真实业务操作”。

## 本节学习目标

学完本节，你要能说清楚：

- RAG、Agent、Tool 分别负责什么。
- 为什么不能把 RAG 当 Agent。
- 为什么不能让 Agent 直接替代 RAG。
- 订单查询、政策问答、工单创建、用户确认分别归谁。
- RAG 结果如何作为 Agent 的上下文。
- 写操作为什么必须经过确认。
- 常见错误架构有哪些。

## 本节新增和修改

新增：

```text
projects/ai-service/app/rag/agent_boundary.py
projects/ai-service/tests/test_rag_agent_boundary.py
notes/stage9-22-rag-agent-boundary.md
```

修改：

```text
projects/ai-service/app/rag/README.md
docs/learning-progress.md
```

## 一句话先讲透

RAG 与 Agent 的边界是：

```text
RAG 负责查资料并给出有依据的知识回答；Agent 负责多步骤流程决策和状态推进；Tool 负责真实业务系统读写；写操作必须由 Agent 编排并经过用户确认。
```

## 基础知识铺垫

### 1. 什么是 RAG

RAG 是 Retrieval-Augmented Generation。

它的核心是：

```text
先检索资料，再让模型基于资料回答。
```

RAG 擅长解决：

```text
政策解释。
FAQ 问答。
流程说明。
知识库资料查询。
引用来源展示。
基于文档的回答。
```

例如：

```text
质量问题退货运费谁承担？
账号安全验证有哪些规则？
售后换货流程怎么走？
```

这些问题的共同点是：

```text
答案主要来自知识库资料。
不需要读取实时订单状态。
不需要修改业务系统。
不需要多轮执行流程。
```

### 2. 什么是 Agent

Agent 不是“更聪明的 RAG”。

Agent 的核心是：

```text
围绕目标进行流程决策、状态推进、工具编排和多步骤处理。
```

Agent 擅长解决：

```text
多步骤任务。
需要补字段的问题。
需要用户确认的问题。
需要调用多个工具的问题。
需要根据中间结果决定下一步的问题。
需要状态保存和恢复的问题。
```

例如：

```text
帮我创建一个售后工单。
查询订单后判断能不能建工单。
缺少订单号时追问用户。
用户确认后再执行写入。
工具失败后决定重试、降级或人工处理。
```

这些问题不是单次检索能完成的。

### 3. 什么是 Tool

Tool 是后端暴露给 AI 系统的能力。

它通常对应真实业务系统能力：

```text
query_order：查询订单。
create_ticket：创建工单。
refund_order：发起退款。
```

Tool 的特点是：

```text
参数必须校验。
权限必须检查。
读写风险不同。
写操作必须确认。
敏感操作可能禁止模型调用。
执行结果来自后端，不应该由模型编造。
```

在本项目里：

```text
query_order 是 read tool。
create_ticket 是 write tool，需要确认。
refund_order 是 sensitive tool，当前阶段禁用。
```

### 4. RAG、Agent、Tool 的一句话区别

可以这样记：

```text
RAG：查资料。
Agent：管流程。
Tool：办业务。
```

更具体一点：

```text
RAG 查“知识库里怎么说”。
Agent 决定“下一步该做什么”。
Tool 执行“业务系统真实操作”。
```

三者不是互相替代，而是组合关系。

### 5. 为什么不能把 RAG 当 Agent

RAG 只解决知识增强回答。

它不擅长：

```text
保存流程状态。
追问缺失字段。
等待用户确认。
调用写工具。
根据工具结果分支。
处理长任务。
失败重试和恢复。
```

如果把 RAG 当 Agent，就会出现：

```text
用户说“帮我建工单”，系统只查到工单流程文档，然后给用户解释流程，但没有真正建工单。
用户说“订单 A1001 到哪了”，系统从知识库里找物流规则，却没有查实时订单。
用户缺少订单号，系统不追问，只根据 FAQ 回答。
```

这就是职责错位。

### 6. 为什么不能让 Agent 直接替代 RAG

Agent 可以调用工具和模型，但它不应该凭空回答知识库问题。

如果不用 RAG，Agent 可能：

```text
根据模型记忆回答过期政策。
编造不存在的规则。
不给引用来源。
无法判断资料是否足够。
很难做检索指标和引用校验。
```

所以对于政策、FAQ、SOP 这类知识问题，Agent 如果参与，也应该把 RAG 当成资料来源。

正确方式是：

```text
Agent 决定需要查资料。
调用 RAG 检索相关知识。
把 RAG 结果作为上下文。
再决定下一步流程。
```

而不是让 Agent 直接自由回答。

### 7. RAG 适合的问题

适合 RAG 的问题通常是：

```text
规则是什么？
政策怎么说？
流程有哪些步骤？
FAQ 是否覆盖这个问题？
某类场景怎么处理？
```

例如：

```text
质量问题退货运费谁承担？
超过七天还能无理由退货吗？
账号安全验证有哪些方式？
售后换货流程怎么走？
```

这些问题需要：

```text
查知识库。
给出处。
拒绝资料不足的问题。
```

### 8. Agent 适合的问题

适合 Agent 的问题通常是：

```text
帮我完成一个任务。
根据当前信息决定下一步。
缺信息时追问。
需要用户确认。
需要读写工具组合。
需要状态持久化。
```

例如：

```text
帮我创建一个售后工单。
先查订单，再判断能不能建工单。
这个问题知识库没有，你帮我转人工处理。
用户确认后创建工单。
```

这些问题需要流程，不只是知识回答。

### 9. Tool 适合的问题

Tool 适合真实业务数据或真实业务动作。

例如：

```text
订单 A1001 到哪里了？
给订单 A1001 创建工单。
查询用户账户状态。
提交退款申请。
```

Tool 分读写：

```text
读工具：查询，不改变业务数据。
写工具：创建、修改、提交，会改变业务数据。
敏感工具：退款、取消订单、权限变更，风险更高。
```

读工具也要校验参数。

写工具必须确认。

敏感工具可能直接禁止模型调用。

### 10. 用户确认为什么重要

用户确认是写操作的安全边界。

如果没有确认，模型可能：

```text
误解用户意思。
提取错字段。
用错订单号。
创建重复工单。
执行用户并不想要的操作。
```

所以写操作应该是：

```text
Agent 收集字段。
Agent 生成待确认内容。
用户明确确认。
后端再次校验。
Tool 执行写入。
返回结果。
```

RAG 不应该直接执行写操作。

模型也不应该绕过后端确认。

### 11. RAG 结果如何作为 Agent 上下文

RAG 可以作为 Agent 的一个信息来源。

例如：

```text
用户：我的退款问题知识库没有写清楚，帮我建工单。
Agent：先调用 RAG 查退款政策。
RAG：返回 no_context 或资料不足。
Agent：判断这是 policy_gap。
Agent：提取工单字段。
Agent：请求用户确认。
Agent：确认后调用 create_ticket。
```

这里 RAG 没有变成 Agent。

它只是给 Agent 提供上下文：

```text
知识库是否覆盖。
找到哪些资料。
引用是否有效。
是否 no_context。
```

### 12. RAG 与 Tool Calling 的关系

Tool Calling 是模型请求后端工具的一种机制。

RAG 本身也可以被设计成一种工具：

```text
search_knowledge_base(query)
```

但工程边界仍然要清楚：

```text
RAG 工具返回资料或知识回答。
业务工具返回真实业务数据或执行业务动作。
Agent 决定什么时候调用哪个工具。
```

不要因为它们都叫 tool，就混淆风险等级。

查知识库和创建工单不是同一类风险。

### 13. RAG 与 LangGraph 的关系

LangGraph 是一种 Agent 编排方式。

它可以把流程拆成节点：

```text
classify_intent。
retrieve_policy。
query_order。
decide_ticket_need。
extract_fields。
request_confirmation。
create_ticket。
finish。
```

其中 `retrieve_policy` 可以调用 RAG。

但 LangGraph 不是 RAG。

它是流程图。

RAG 是其中一个节点或工具。

### 14. 为什么要把边界结构化

只靠口头约定很容易乱。

例如：

```text
这个问题到底归 RAG 还是 Agent？
订单查询要不要走 RAG？
创建工单能不能直接 tool calling？
写工具是不是要确认？
安全问题是不是先拦截？
```

本节新增的 `RagAgentBoundaryDecision` 就是把这些判断结构化。

它记录：

```text
primary_owner。
should_use_rag。
should_use_agent。
should_call_tool。
should_require_confirmation。
selected_tool_name。
selected_knowledge_base_ids。
actions。
warnings。
reasons。
```

这样系统和人都能看懂边界。

### 15. 什么是 Workflow

Workflow 是工作流。

它表示一个任务要经过多个步骤，每一步可能依赖前一步结果。

例如创建工单不是一个动作，而是一条流程：

```text
识别用户意图。
判断是不是工单请求。
提取订单号、问题类型、描述、优先级。
检查字段是否缺失。
缺字段就追问。
字段完整后生成确认内容。
用户确认。
后端校验工具权限。
调用 create_ticket。
记录结果。
失败时决定重试、降级或人工处理。
```

这条流程就是 workflow。

RAG 不负责 workflow。

RAG 可以在 workflow 中提供资料，但不会替你管理这些步骤。

### 16. 什么是 Orchestration

Orchestration 是编排。

在 AI 应用里，它表示：

```text
谁先执行？
谁后执行？
什么时候查 RAG？
什么时候调用工具？
什么时候追问用户？
什么时候结束？
什么时候进入人工处理？
```

Agent 的核心价值之一就是编排。

比如：

```text
先查订单。
如果订单存在，再判断能不能建工单。
如果用户没有确认，先暂停。
如果用户确认，再调用写工具。
如果工具失败，返回可解释错误。
```

这不是 RAG 能做的事情。

RAG 的输出可以参与编排判断，但 RAG 本身不是编排器。

### 17. 读操作、写操作、敏感操作的风险差异

AI 系统调用工具时，必须区分风险等级。

读操作：

```text
查询订单。
查询物流。
查询工单状态。
```

特点是：

```text
不改变业务数据。
主要风险是越权读取、参数错误、泄露信息。
```

写操作：

```text
创建工单。
修改用户信息。
提交售后申请。
```

特点是：

```text
会改变业务数据。
需要用户确认。
需要幂等。
需要审计。
```

敏感操作：

```text
退款。
取消订单。
封禁账号。
修改权限。
```

特点是：

```text
业务风险高。
通常需要更严格权限。
当前学习项目里默认不允许模型直接调用。
```

所以边界不能只问：

```text
模型想不想调用工具？
```

而要问：

```text
这个工具是什么风险等级？
参数是否完整？
用户是否确认？
后端是否授权？
是否允许当前阶段执行？
```

### 18. “能回答”和“能执行”不是一回事

这是 RAG 和 Agent 边界里非常重要的一点。

RAG 可以回答：

```text
创建工单需要哪些信息？
售后流程怎么走？
退款规则是什么？
```

但这不代表 RAG 可以执行：

```text
帮用户创建工单。
提交退款。
修改订单状态。
```

同样，Agent 可以执行流程，但也不代表它可以不查资料就回答政策。

真实项目里必须区分：

```text
回答规则。
执行操作。
推进流程。
读取实时数据。
写入业务系统。
```

这几个动作的责任主体不同。

### 19. RAG 输出和 Agent 输出的区别

RAG 输出通常是：

```text
answer。
citations。
no_context_reason。
retrieved_chunks。
answer_status。
```

它强调：

```text
资料依据。
引用来源。
是否有上下文。
回答是否 grounded。
```

Agent 输出通常是：

```text
route。
state。
missing_fields。
confirmation_required。
tool_result。
next_action。
final_answer。
```

它强调：

```text
流程状态。
下一步动作。
工具执行结果。
用户确认。
任务是否完成。
```

如果你把这两类输出混在一起，代码会变得很乱。

比如让 RAG 输出 `next_action=create_ticket`，就是把知识回答模块变成流程控制模块。

比如让 Agent 输出没有引用的政策答案，就是绕过了 RAG 的 grounded 边界。

### 20. RAG、Agent、Tool 的三种常见组合形态

第一种：纯 RAG。

```text
用户问政策
-> query intent 判断为 policy_lookup
-> 知识库路由
-> 检索资料
-> 生成有引用回答
```

适合：

```text
规则解释。
FAQ。
流程说明。
```

第二种：Agent 调 RAG。

```text
用户请求处理问题
-> Agent 判断需要知识背景
-> 调 RAG 查政策或 SOP
-> Agent 根据 RAG 结果决定是否追问、建工单或结束
```

适合：

```text
policy_gap。
复杂售后。
需要根据知识库判断下一步的任务。
```

第三种：Agent 调 Tool。

```text
用户要完成业务操作
-> Agent 收集字段
-> 用户确认
-> Tool 执行业务写入
-> Agent 汇总结果
```

适合：

```text
创建工单。
提交申请。
组合多个业务动作。
```

这三种形态可以组合，但边界不能混。

### 21. 边界判断为什么有助于面试表达

面试里如果你只说：

```text
我们用了 RAG 和 Agent。
```

这句话很泛。

更好的表达是：

```text
我们把知识问答、流程编排和业务工具执行拆开。
政策类问题由 RAG 负责，保证有检索依据和引用。
订单状态由只读工具查询，避免模型编造实时业务数据。
工单创建由 LangGraph Agent 编排，负责字段补全、用户确认、写工具调用和异常处理。
写操作必须经过用户确认，敏感工具即使模型请求也会被后端拒绝。
```

这样别人能听出来你不是只会“调 API”，而是真的理解工程边界。

## 本节主题系统讲解

### 1. 第 22 节在阶段 9 里的位置

阶段 9 前面主要补 RAG 自身能力：

```text
query rewrite。
multi query。
intent。
hybrid。
rerank。
citation。
compression。
filter。
security。
evaluation。
tuning。
performance。
observability。
data update。
knowledge routing。
```

现在要把 RAG 放回完整 AI 应用里。

完整客服 AI 不只有 RAG，还包括：

```text
Tool Calling。
Java business service。
Ticket Agent。
LangGraph。
用户确认。
错误处理。
权限控制。
```

所以本节的重点是组合边界。

### 2. 当前项目里的已有边界

项目里已经有几类能力：

```text
query_intent.py：判断用户问题大意图。
knowledge_routing.py：RAG 问题查哪个知识库。
tool_registry.py：定义 query_order、create_ticket、refund_order。
tool_decision_service.py：让模型决定是否请求 read tool。
ticket_agent.py：LangGraph 工单流程 Agent。
generator.py：RAG 资料回答。
```

本节新增 `agent_boundary.py`，它不替代这些模块。

它只是把它们之间的职责关系明确写出来。

### 3. 本节新增的核心判断

本节核心函数：

```text
build_rag_agent_boundary_decision()
```

它根据：

```text
query intent。
可选知识库路由结果。
可选 requested_tool_name。
Agent 是否需要 RAG 政策上下文。
```

输出边界决策。

### 4. policy/process 问题归 RAG

如果 intent 是：

```text
policy_lookup。
process_lookup。
```

边界判断是：

```text
primary_owner = rag
should_use_rag = true
should_use_agent = false
should_call_tool = false
actions = retrieve_knowledge
```

意思是：

```text
这是知识问题，先查资料，不要启动完整 Agent，也不要调用业务工具。
```

### 5. 订单查询归 read tool

如果 intent 是：

```text
order_lookup
```

并且用户提供了订单号：

```text
primary_owner = tool
selected_tool_name = query_order
selected_tool_access_level = read
actions = call_read_tool
```

原因是订单状态是实时业务数据。

它不应该从知识库里猜，也不应该由模型编造。

如果没有订单号：

```text
primary_owner = clarification
actions = ask_clarifying_question
```

因为工具参数不完整。

### 6. 工单创建归 Agent

如果 intent 是：

```text
ticket_creation
```

边界判断是：

```text
primary_owner = agent
should_use_agent = true
should_require_confirmation = true
actions = run_agent_workflow + request_user_confirmation
```

原因是创建工单需要：

```text
提取字段。
检查缺失。
可能追问。
确认写入。
调用 create_ticket。
处理错误。
保存状态。
```

这不是 RAG 的职责。

### 7. RAG 作为 Agent 上下文

有些 Agent 流程需要查知识库。

例如：

```text
创建 policy_gap 工单前，先确认知识库是否确实没有覆盖。
```

这时边界是：

```text
primary_owner = agent
should_use_rag = true
should_use_agent = true
actions = use_rag_as_agent_context + run_agent_workflow + request_user_confirmation
```

注意：

```text
RAG 是上下文来源。
Agent 仍然是流程 owner。
```

### 8. 写工具必须确认

如果 requested_tool 是：

```text
create_ticket
```

它是 write tool。

边界判断是：

```text
primary_owner = agent
should_require_confirmation = true
actions = run_agent_workflow + request_user_confirmation
```

也就是说模型不能直接执行写操作。

需要 Agent 编排和用户确认。

### 9. 禁用敏感工具要拒绝

如果 requested_tool 是：

```text
refund_order
```

它在当前阶段 disabled。

边界判断是：

```text
primary_owner = safety
actions = reject_tool_execution
```

这体现了后端拥有最终执行权。

模型请求了也不能执行。

### 10. unsafe 问题先拦截

如果 intent 是：

```text
unsafe
```

边界判断是：

```text
primary_owner = safety
actions = block_for_safety
```

不应该：

```text
查 RAG。
调用 Agent。
调用 Tool。
```

安全边界要在前面。

### 11. smalltalk 直接回答

如果用户只是：

```text
你好，你是谁？
```

边界判断是：

```text
primary_owner = direct_answer
actions = answer_directly
```

不需要 RAG、Agent、Tool。

这也是成本控制的一部分。

### 12. 典型链路一：纯 RAG 问答

纯 RAG 问答链路是：

```text
用户问题
-> query intent = policy_lookup/process_lookup
-> knowledge routing 选择知识库
-> metadata filter 限制权限和业务域
-> retrieval / rerank / compression
-> generation
-> citation verification
-> 返回有引用的回答
```

在这条链路里：

```text
RAG 是 primary owner。
Agent 不需要启动。
Tool 不需要调用。
用户确认不需要出现。
```

适合例子：

```text
质量问题退货运费谁承担？
账号安全验证规则是什么？
售后换货流程怎么走？
```

如果这类问题都启动 Agent，会让系统变复杂，成本增加，排查路径变长。

### 13. 典型链路二：工具读数据

工具读数据链路是：

```text
用户问题
-> query intent = order_lookup
-> 检查是否有订单号
-> 后端校验 query_order 参数
-> 调 Java business service
-> 返回订单状态
-> 模型或后端总结成用户可读回答
```

在这条链路里：

```text
Tool 是 primary owner。
RAG 不应该参与回答具体订单状态。
Agent 通常不需要启动。
```

适合例子：

```text
订单 A1001 到哪里了？
这个订单发货了吗？
物流有没有更新？
```

原因是：

```text
订单状态不是知识库知识，而是实时业务数据。
```

### 14. 典型链路三：Agent 编排写流程

Agent 编排写流程是：

```text
用户请求创建工单
-> Agent 识别意图
-> 提取字段
-> 需要时查询订单或 RAG 政策
-> 缺字段则追问
-> 字段完整后生成确认内容
-> 用户确认
-> 后端授权 create_ticket
-> 调 Java business service 写入
-> 返回工单结果
```

在这条链路里：

```text
Agent 是 primary owner。
RAG 可以提供上下文。
Tool 负责真实写入。
用户确认是必须边界。
```

适合例子：

```text
帮我创建一个售后工单。
这个退款规则没有覆盖，帮我转人工。
订单物流很久没更新，帮我提交问题。
```

这条链路比纯 RAG 更复杂，所以不能滥用。

### 15. 边界错位怎么排查

当 AI 应用答错或行为不符合预期时，可以先问：

```text
这是不是知识问题？
这是不是实时业务数据问题？
这是不是写操作？
这是不是需要多步骤流程？
这是不是缺少用户确认？
这是不是安全问题？
```

对应排查：

```text
知识问题答错：先看 RAG 检索、引用、知识库路由。
订单状态答错：先看 query_order 工具和 Java business service。
工单创建异常：先看 Agent 状态、字段提取、确认、create_ticket。
越权或敏感问题：先看 safety、tool registry、permission。
用户表达不清：先看 clarification。
```

这比一上来怀疑“模型不行”更工程化。

### 16. 当前项目推荐的职责分配

当前项目里可以这样理解：

```text
RAG 模块：负责知识库检索、排序、引用、评测、安全、可观测性。
Tool Registry：负责声明哪些工具存在、启用状态、读写风险、是否确认。
Tool Decision Service：负责只读工具调用请求的模型决策和后端校验。
Ticket Agent：负责工单流程、字段提取、用户确认、写工具调用和状态推进。
Java business service：负责真实业务数据和业务写入。
```

这套分配的好处是：

```text
知识问题可评测。
业务数据不编造。
写操作有确认。
工具执行有后端授权。
Agent 状态可恢复。
RAG 和 Agent 的问题可以分开排查。
```

### 17. 本节暂时不做什么

本节不改真实 LangGraph。

原因：

```text
这节是边界学习，不是重构 Agent 流程。
```

本节不真实调用大模型。

原因：

```text
边界判断应该能通过规则和结构化测试稳定验证。
```

本节不新增真实业务接口。

原因：

```text
Tool 和 Java business service 已在前面阶段学过。
```

## 本节代码讲解

### 1. `RagAgentBoundaryDecision`

这个模型是本节核心。

它记录一次请求的职责边界：

```text
primary_owner。
should_use_rag。
should_use_agent。
should_call_tool。
should_require_confirmation。
selected_tool_name。
selected_tool_access_level。
selected_knowledge_base_ids。
actions。
warnings。
reasons。
```

它让边界判断变成可测试、可解释的结构。

### 2. `build_rag_agent_boundary_decision()`

这个函数是入口。

它支持三类输入：

```text
query。
classification。
route_decision。
requested_tool_name。
```

如果有 `requested_tool_name`，先判断工具边界。

如果没有，就根据 query intent 判断归属。

### 3. `primary_owner`

`primary_owner` 表示这次请求主要归谁负责。

可选值：

```text
rag。
agent。
tool。
direct_answer。
safety。
clarification。
```

这个字段很重要，因为它能避免“所有问题都丢给 Agent”或“所有问题都丢给 RAG”。

### 4. `actions`

`actions` 表示建议执行动作。

例如：

```text
retrieve_knowledge。
call_read_tool。
run_agent_workflow。
request_user_confirmation。
block_for_safety。
ask_clarifying_question。
```

它不是直接执行结果，而是结构化计划。

### 5. `warnings`

warnings 表示边界提醒。

例如：

```text
RAG_AGENT_BOUNDARY_RAG_ONLY。
RAG_AGENT_BOUNDARY_TOOL_READ_ONLY。
RAG_AGENT_BOUNDARY_WRITE_REQUIRES_CONFIRMATION。
RAG_AGENT_BOUNDARY_SAFETY_BLOCK。
```

这些 warning 后续可以进入可观测性或评测。

### 6. 本节测试重点

测试覆盖：

```text
政策问题归 RAG。
带订单号的订单查询归 read tool。
没订单号时先追问。
创建工单归 Agent 并需要确认。
Agent 可以使用 RAG 作为上下文。
create_ticket 写工具需要确认。
refund_order 禁用敏感工具被拒绝。
unsafe 问题先安全拦截。
smalltalk 直接回答。
```

## 常见误区

### 误区 1：Agent 比 RAG 高级，所以所有问题都交给 Agent

不对。

简单知识问答用 RAG 更清晰、更可控、更容易评测。

Agent 适合流程，不适合替代所有问答。

### 误区 2：RAG 能回答流程，所以也能执行流程

不对。

RAG 可以解释“流程怎么走”，但不会真的推进流程状态。

真正执行流程需要 Agent 和 Tool。

### 误区 3：订单查询可以从知识库里回答

不对。

订单状态是实时业务数据，应该调用 read tool 或业务服务。

知识库只能回答订单规则，不应该回答具体订单状态。

### 误区 4：模型说要调用写工具就可以执行

不对。

写操作必须由后端控制，并要求用户确认。

模型请求不等于后端授权。

### 误区 5：RAG 作为 Agent 上下文时，流程 owner 就变成 RAG

不对。

RAG 只是提供资料。

Agent 仍然负责流程决策、确认和工具编排。

### 误区 6：安全问题可以先检索再判断

不建议。

明显 unsafe 的问题应该在进入 RAG、Agent、Tool 前拦截。

### 误区 7：Tool Calling 就等于 Agent

不对。

Tool Calling 只是模型请求调用工具的机制。

Agent 是更完整的流程编排能力，通常包含：

```text
状态。
节点。
分支。
追问。
确认。
失败处理。
持久化。
```

一次简单的 `query_order` 工具调用，不一定需要完整 Agent。

### 误区 8：检索到政策就可以直接执行工单

不对。

RAG 检索到政策，只说明系统找到相关资料。

创建工单还需要：

```text
字段完整。
用户确认。
后端授权。
幂等保护。
写入结果校验。
```

这些是 Agent 和 Tool 的职责。

### 误区 9：用户说“帮我处理”就一定要创建工单

不一定。

用户可能只是想问规则，也可能想查订单，也可能真的要人工处理。

Agent 需要根据意图、上下文和字段完整度判断，必要时追问。

### 误区 10：RAG no_context 就一定要马上建工单

不一定。

`no_context` 说明当前知识库没有足够资料回答。

下一步可能是：

```text
换个问法。
追问用户问题细节。
记录知识库缺口。
创建 policy_gap 工单。
转人工。
```

具体走哪一步应该由 Agent 或业务规则决定。

## 本节练习

### 练习 1：用户问“质量问题退货运费谁承担？”应该归谁？

答案：

归 RAG。因为这是政策知识问题，需要查退款退货政策知识库并基于资料回答，不需要调用订单工具，也不需要启动工单 Agent。

### 练习 2：用户问“订单 A1001 到哪里了？”应该归谁？

答案：

归 read tool。因为具体订单状态是实时业务数据，应调用 `query_order` 这类只读工具，不能从知识库里猜。

### 练习 3：用户说“帮我创建一个售后工单”应该归谁？

答案：

归 Agent。因为创建工单是多步骤写流程，需要提取字段、检查缺失、请求用户确认，再调用写工具。

### 练习 4：Agent 什么时候需要用 RAG？

答案：

当 Agent 流程需要知识库资料作为判断依据时。例如创建 policy_gap 工单前，需要先确认知识库是否没有相关政策；或者创建工单时需要引用当前政策作为背景。

### 练习 5：为什么禁用的敏感工具不能因为模型请求就执行？

答案：

因为后端拥有最终执行权。模型请求只是建议，不能绕过工具注册表、权限、enabled 状态和用户确认。敏感工具禁用时必须拒绝执行。

## 自测题

### 自测 1：RAG、Agent、Tool 各自一句话职责是什么？

答案：

RAG 负责查资料并基于资料回答。Agent 负责流程决策、状态推进和工具编排。Tool 负责真实业务系统的读写操作。

### 自测 2：为什么写工具必须用户确认？

答案：

因为写工具会改变业务数据。模型可能误解用户、提取错字段或用错订单号，所以必须先把待执行内容展示给用户确认，再由后端执行。

### 自测 3：RAG 与 Agent 组合时，谁是流程 owner？

答案：

如果是多步骤任务，Agent 是流程 owner。RAG 可以作为 Agent 的上下文来源，但不负责流程推进。

### 自测 4：订单查询为什么不是 RAG 任务？

答案：

因为订单查询需要实时业务数据，知识库只有规则和说明，不包含用户订单当前状态。具体订单状态应该通过 read tool 查询。

### 自测 5：安全拦截应该在 RAG/Agent/Tool 之前还是之后？

答案：

应该在之前。明显 unsafe 的问题不应该进入知识库检索、Agent 流程或工具执行。

## 本节小结

本节你学到的是：

```text
RAG 查资料。
Agent 管流程。
Tool 办业务。
读工具可以在参数校验后执行。
写工具必须用户确认。
敏感禁用工具必须拒绝。
RAG 可以作为 Agent 上下文，但不接管流程。
```

下一节学习 RAG 生产化验收清单，把阶段 9 的质量、安全、性能、成本、可观测性整理成上线前检查标准。
