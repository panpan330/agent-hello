# 阶段 6 第 19 节：接入真实 `query_order` 到 LangGraph

本节目标：把智能工单 Agent 里的 `query_order` 占位节点，升级为真正会调用已有订单查询工具链路的 LangGraph 节点。

前面阶段已经学过：

```text
阶段 3：模型可以决定是否请求 query_order 工具
阶段 3：Python 可以通过 JavaOrderClient 调用 Java mock 订单服务
阶段 3：工具参数和工具返回结果都要经过 Pydantic 校验
阶段 5：LangGraph 可以把智能工单 Agent 拆成多个节点
阶段 6：真实 LLM 节点、prompt 版本、模型输出失败处理已经接入
```

但是在进入本节之前，`query_order` 在 LangGraph 智能工单 Agent 里仍然只是一个占位节点：

```text
用户问订单
-> Agent 识别为 order_query
-> 进入 query_order 节点
-> 返回“后续课程会接入 query_order 工具”
```

这显然还不是真正的业务链路。

本节完成后的链路变成：

```text
用户问订单
-> normalize_user_input
-> classify_intent
-> query_order_node
-> 提取订单号
-> QueryOrderArgs 校验
-> 执行 query_order 工具
-> JavaOrderClient 调用 Java mock 订单服务
-> 字段白名单映射
-> QueryOrderResult 校验
-> 写回 LangGraph state
-> 返回订单状态、支付状态、物流摘要和后续提示
```

这一步很重要，因为它代表智能工单 Agent 开始从“会走流程”进入“会连接业务系统”。

---

## 一、本节在主线里的位置

阶段 6 是生产化与评测阶段。

第 13-18 节主要在补真实模型节点和模型输出兜底：

```text
第 13 节：真实 LLM 意图识别节点
第 14 节：真实 LLM 字段提取节点
第 15 节：Pydantic 校验模型输出
第 16 节：fake LLM 和真实 LLM 双模式
第 17 节：prompt 版本管理
第 18 节：模型输出失败处理
```

这些内容解决的是：

```text
模型能不能可靠参与 Agent 流程？
模型输出坏了系统怎么办？
怎么在测试里不用真实模型也能保护工程边界？
```

第 19 节开始转向另一个生产化问题：

```text
Agent 识别出用户要查询订单之后，后端到底怎么安全地执行真实工具？
```

这里的“真实工具”不是说一定连接生产数据库。

在当前学习项目里，真实的意思是：

```text
不再返回写死占位文案
而是复用已有 query_order 工具函数
真的走 JavaOrderClient
真的请求 java-mock-service 的 GET /orders/{order_id}
真的经过字段白名单映射
真的经过 QueryOrderResult 校验
```

所以本节不是单纯“补一个函数调用”。

它是在练习真实 AI 工程里最常见的连接方式：

```text
LLM / Agent 负责判断要做什么
后端代码负责校验、执行、控制边界、记录结果
业务服务负责返回真实业务数据
```

---

## 二、本节学习目标

学完本节，你要能解释清楚：

1. `query_order` 工具和 `query_order_node` 节点有什么区别。

   答案：`query_order` 是一个可复用业务工具函数，输入 `QueryOrderArgs`，输出 `QueryOrderResult`；`query_order_node` 是 LangGraph 图里的节点，负责从 state 中取用户问题、提取订单号、调用工具、处理异常，并把结果写回 state。

2. 为什么 LangGraph 节点里不能直接相信用户原话。

   答案：用户原话是非结构化文本，可能没有订单号，也可能订单号格式不符合工具要求。节点必须先提取订单号，再用 `QueryOrderArgs` 做结构化校验。

3. 为什么工具参数和工具结果都要用 Pydantic。

   答案：参数校验保证传给业务工具的数据符合契约；结果校验保证业务服务返回的数据能被 Agent 安全使用。一个防止“请求坏”，一个防止“响应坏”。

4. 为什么本节要给 `query_order_node` 加 `order_query_executor` 注入。

   答案：真实运行时默认调用真实工具；测试时注入 fake executor，避免单元测试依赖 Java 服务、网络、Docker 和外部状态。

5. 为什么查询订单属于相对安全的只读工具，但仍然需要边界控制。

   答案：只读工具不会修改业务数据，风险低于创建工单、退款、改地址等写操作；但它仍然可能泄露数据、被越权调用、被错误参数打爆后端服务，所以仍然要参数校验、权限控制、错误处理和日志记录。

6. `AppException` 和未知异常在工具节点里为什么要区别处理。

   答案：`AppException` 是项目内已经结构化过的业务错误，可以把 `code` 和 `message` 写入 state；未知异常说明底层出现未预期问题，要统一收敛成安全兜底错误，不能把内部细节暴露给用户。

7. 为什么本节先由代码生成最终中文回答，而不是再交给模型润色。

   答案：本节重点是把真实工具执行链路接进 LangGraph，先保证业务数据可查、可校验、可测试。让模型基于工具结果做自然语言总结可以后续再加，否则本节会同时混入工具执行和模型总结两个变量。

8. 本节新增测试主要保护什么。

   答案：保护成功查询、缺少订单号、工具抛出业务异常、完整 LangGraph 路由能使用注入 executor 四个关键行为。

---

## 三、本节暂时不学什么

本节只做“只读订单查询工具接入 LangGraph”。

暂时不展开：

- 不修改 `java-mock-service`。
- 不新增真实订单数据库。
- 不做用户权限校验。
- 不做写操作工具。
- 不做退款、改地址、取消订单。
- 不做多工具并行调用。
- 不做 LangChain/LangGraph 标准 ToolNode 封装。
- 不让模型决定工具参数。
- 不把工具结果再交给模型总结。
- 不做工具调用 retry。
- 不做工具节点熔断。
- 不做工具调用成本统计。
- 不把工具结果持久化到 checkpoint 外部数据库。

为什么先不做这些？

因为你现在需要先把最核心的一条链路学扎实：

```text
LangGraph 节点
-> 后端参数校验
-> 工具执行
-> 跨服务调用
-> 结果校验
-> state 写回
-> 安全回答
```

这条链路清楚了，以后再加权限、写操作确认、retry、持久化和观测性，才不是堆概念。

---

## 四、基础知识铺垫

### 1. 什么是 LangGraph 节点

LangGraph 里的节点可以先理解成：

```text
接收当前 state
执行一个明确步骤
返回要合并进 state 的更新字段
```

比如当前智能工单 Agent 里有这些节点：

```text
normalize_user_input
classify_intent
retrieve_policy
query_order
decide_ticket_need
extract_ticket_fields
ask_missing_fields
confirm_ticket
create_ticket
```

每个节点不是“什么都做一点”，而是负责流程中的一个明确环节。

`query_order` 节点负责的事情应该是：

```text
用户已经被识别为订单查询意图
现在从用户问题里找订单号
如果有订单号，就调用订单查询工具
如果没有订单号，就追问用户
如果查询失败，就返回安全错误信息
如果查询成功，就把订单数据放进 state
```

这就是节点的边界。

### 2. 什么是工具

在 AI 工程里，“工具”通常是模型或 Agent 可以触发的后端能力。

工具可以是：

```text
查订单
查库存
查用户会员等级
创建工单
发优惠券
取消订单
调用搜索引擎
检索知识库
```

但工具不是让模型直接操作数据库。

正确的工程边界一般是：

```text
模型提出意图或工具请求
后端校验工具名
后端校验参数
后端检查权限
后端执行工具
后端校验工具结果
后端决定怎么把结果交给用户或模型
```

所以工具调用不是“模型想干什么就干什么”。

工具调用真正安全的地方在后端。

### 3. `query_order` 工具和 `query_order_node` 节点的区别

这两个名字很像，但职责不同。

`query_order` 工具函数：

```text
位置：app/tools/fake_order_tool.py
输入：QueryOrderArgs
输出：QueryOrderResult
职责：调用订单服务，映射字段，校验结果
```

`query_order_node` LangGraph 节点：

```text
位置：app/agents/ticket_agent.py
输入：TicketAgentState
输出：TicketAgentState 的部分更新
职责：从 state 中提取订单号，调用 query_order，处理成功/失败，并写回 Agent state
```

可以用一句话记：

```text
工具关心“业务动作怎么执行”
节点关心“这个业务动作在 Agent 流程里怎么被使用”
```

这个区分非常重要。

如果把所有逻辑都写进节点，工具就不能在别的地方复用。

如果把所有流程逻辑都写进工具，工具就会依赖 LangGraph state，失去通用性。

### 4. 为什么查询订单是只读工具

查询订单通常是只读操作。

只读表示：

```text
不会改变订单状态
不会扣款
不会退款
不会创建工单
不会修改地址
不会发货
```

只读工具通常比写操作安全。

但“只读”不等于“无风险”。

查询订单仍然可能有这些风险：

```text
查了别人的订单
把敏感字段返回给模型
把内部字段暴露给用户
高频查询打爆业务服务
错误参数导致后端异常
日志里记录了不该记录的信息
```

所以只读工具也要做：

```text
参数校验
字段白名单
统一错误处理
日志记录
后续权限校验
测试保护
```

本节先做参数校验、字段白名单复用、错误处理和测试保护。

权限校验会放到后面专门讲。

### 5. 为什么要先提取订单号

用户的问题是自然语言：

```text
我的订单 A1001 到哪了？
帮我查一下 1001
订单是不是发货了
```

业务工具需要的是结构化参数：

```json
{"order_id": "A1001"}
```

中间必须有一步把自然语言变成结构化参数。

当前项目已经有 `_extract_order_id()`。

它的职责是从用户文本里识别订单号。

如果能识别，就继续调用工具。

如果不能识别，就不能强行查询。

正确行为是追问：

```text
请提供要查询的订单号（例如 A1001 或 1001），我拿到订单号后才能查询订单状态和物流信息。
```

这叫缺参数处理。

真实业务系统里，缺参数处理非常常见。

模型或用户没有提供足够信息时，系统应该追问，而不是胡猜。

### 6. 为什么要用 `QueryOrderArgs`

`QueryOrderArgs` 是工具参数模型。

它代表调用 `query_order` 工具所需的最小输入。

当前主要字段是：

```text
order_id
```

你可以把它理解成工具入口的门卫：

```text
不是任何字符串都能传给订单服务
必须先变成 QueryOrderArgs
通过校验后才能调用工具
```

这样做有几个好处：

```text
工具参数契约清晰
测试能直接构造参数
错误能提前暴露
以后加字段时位置明确
自动文档和 schema 更容易生成
```

### 7. 为什么要用 `QueryOrderResult`

`QueryOrderResult` 是工具返回模型。

它把订单查询结果约束成后端认可的结构。

比如返回里应该有：

```text
order_id
order_status
payment_status
logistics_message
latest_event
can_create_ticket
source
```

为什么结果也要校验？

因为业务服务返回的数据也不能被盲目信任。

即使 Java mock 服务是我们自己写的，也可能因为后续改动导致字段缺失、类型变错、枚举值变错。

如果不校验，错误可能会在更后面才爆出来：

```text
模型总结时出错
前端显示时出错
日志分析时出错
工单决策时出错
```

用 `QueryOrderResult` 可以让错误尽早发生在工具边界。

工程上常说：

```text
边界越早校验，错误越容易定位。
```

### 8. JavaOrderClient 在链路里的位置

当前项目里，Python AI 服务不直接读取 Java 的数据结构。

它通过 `JavaOrderClient` 调用 Java mock 服务。

链路是：

```text
Python Agent
-> query_order 工具
-> JavaOrderClient
-> HTTP GET /orders/{order_id}
-> java-mock-service
```

这模拟的是真实公司里常见架构：

```text
Python AI 服务不拥有核心业务数据
Java 后端服务拥有订单、工单、用户等业务数据
AI 服务通过稳定 API 调用 Java 服务
```

这样设计的好处是：

```text
业务边界清晰
Java 系统仍然掌握核心数据
AI 服务只是业务能力的调用方
以后替换 AI 层不会影响 Java 核心系统
Java 侧也可以继续做鉴权、审计、风控
```

### 9. 什么是字段白名单映射

Java 服务返回的原始订单数据，不应该原样交给 Agent。

正确方式是做白名单映射：

```text
只取允许进入 AI 服务的字段
丢弃不该暴露的字段
统一字段名
补充 source
再做 Pydantic 校验
```

当前已有函数：

```python
def map_java_order_to_query_order_payload(raw_order):
    return {
        "order_id": raw_order.get("order_id"),
        "order_status": raw_order.get("order_status"),
        "payment_status": raw_order.get("payment_status"),
        "logistics_message": raw_order.get("logistics_message"),
        "latest_event": raw_order.get("latest_event"),
        "can_create_ticket": raw_order.get("can_create_ticket"),
        "source": "java_mock_service",
    }
```

这段代码的关键不是写法复杂。

关键是思想：

```text
业务服务返回什么，不等于 AI 层可以使用什么。
AI 层可以使用什么，必须由后端白名单决定。
```

以后接真实订单系统时，这个思想会非常重要。

### 10. 为什么要把工具结果写入 state

LangGraph 的 state 是 Agent 流程的共享状态。

`query_order_node` 查询成功后写入：

```text
order_query_order_id
order_query_status
order_query_result
order_query_error_code
order_query_error_message
final_answer
node_history
```

写入 state 的好处是：

```text
后续节点可以继续使用订单结果
stream 输出可以看到节点更新
日志和评测可以检查节点行为
测试可以断言结果是否正确
checkpoint 后续可以保存这些状态
```

如果节点只是返回一句话，不写结构化状态，后续工程能力会很弱。

结构化 state 是 LangGraph 项目能走向生产化的关键。

### 11. 为什么要用 executor 注入

本节新增了：

```python
OrderQueryExecutor = Callable[[QueryOrderArgs], QueryOrderResult]
```

这表示：

```text
只要一个对象能接收 QueryOrderArgs，并返回 QueryOrderResult
它就可以被当成订单查询执行器
```

真实运行时：

```text
executor = execute_ticket_order_query
-> query_order
-> JavaOrderClient
-> Java mock service
```

测试时：

```text
executor = RecordingOrderQueryExecutor()
-> 不请求网络
-> 不依赖 Java 服务
-> 直接返回 fake QueryOrderResult
```

这就是依赖注入。

依赖注入的核心目的不是“显得高级”。

它解决的是：

```text
业务代码要能接真实依赖
测试代码要能替换真实依赖
替换依赖时不改节点核心逻辑
```

这也是 AI 工程里非常重要的基本功。

### 12. 为什么本节不真实调用模型

本节新增的是工具节点。

自动化测试仍然不应该真实调用大模型。

原因有四个：

```text
真实模型调用有费用
真实模型调用不稳定
真实模型调用受网络和 API key 影响
本节要验证的是工具节点工程边界，不是模型质量
```

所以测试里只 fake 掉订单查询 executor。

这样我们能明确知道：

```text
如果测试失败，是节点逻辑或 state 写入出了问题
不是模型、网络、Java 服务状态导致的偶发问题
```

### 13. 为什么本节失败时也要写结构化状态

缺少订单号时，节点返回：

```text
order_query_status = "missing_order_id"
order_query_error_code = "ORDER_ID_REQUIRED"
final_answer = "请提供要查询的订单号..."
```

工具失败时，节点返回：

```text
order_query_status = "failed"
order_query_error_code = 具体错误码
agent_error_node = "query_order"
fallback_used = True
```

这样做的好处是：

```text
用户能得到安全回答
测试能断言失败类型
日志能定位失败节点
后续评测能统计 query_order 的失败原因
前端或调用方能区分缺参数和工具失败
```

这比只返回一句“系统繁忙”更工程化。

### 14. 为什么要记录 node_history

`node_history` 是我们在阶段 5 就开始维护的节点路径。

它可以告诉我们：

```text
这次请求经过了哪些节点
有没有走错路
是否误进了工单创建流程
最后停在哪个节点
```

订单查询成功时，完整路径应类似：

```text
normalize_user_input
classify_intent
query_order
```

这对 Agent 很重要。

因为 Agent 不是普通单函数。

它的正确性不仅是“最后有没有回答”，还包括：

```text
中间有没有走对路径
有没有跳过必要节点
有没有误触发危险操作
```

---

## 五、本节主题系统讲解

### 1. 本节最终链路

本节接通后的完整执行链路是：

```text
用户输入：
我的订单 A1001 到哪了？

1. normalize_user_input
   清理用户输入，写入 normalized_message

2. classify_intent
   判断意图是 order_query

3. conditional edge
   根据 intent 路由到 query_order

4. query_order_node
   从 normalized_message 里提取 A1001

5. QueryOrderArgs(order_id="A1001")
   校验工具参数

6. order_query_executor(arguments)
   默认执行 execute_ticket_order_query

7. execute_ticket_order_query
   调用 app.tools.fake_order_tool.query_order

8. query_order 工具
   创建 JavaOrderClient，调用 get_order("A1001")

9. Java mock service
   处理 GET /orders/A1001，返回订单数据

10. map_java_order_to_query_order_payload
    只保留允许进入 AI 服务的字段

11. QueryOrderResult.model_validate
    校验工具结果

12. query_order_node
    把结果写回 state，生成最终回答
```

你可以把它记成三层：

```text
Agent 流程层：LangGraph state 和节点路由
工具适配层：query_order 参数、执行、结果校验
业务服务层：Java mock service 提供订单数据
```

这三层不要混在一起。

### 2. 为什么从 `normalized_message` 提取订单号

节点里使用：

```python
normalized_message = state.get("normalized_message") or state.get("user_message", "")
order_id = _extract_order_id(normalized_message)
```

这段逻辑的含义是：

```text
优先使用前面 normalize_user_input 节点处理后的文本
如果没有 normalized_message，就退回 user_message
最后保证至少是空字符串
```

为什么不直接用 `user_message`？

因为 LangGraph 流程里，每个节点最好消费前一个节点已经整理过的 state。

这让流程更稳定：

```text
输入清理放在 normalize 节点
意图识别放在 classify 节点
订单查询放在 query_order 节点
```

节点之间通过 state 传递结果，而不是每个节点都重复做全部事情。

### 3. 缺订单号时为什么不调用工具

如果 `_extract_order_id()` 返回 `None`，节点直接返回缺参数状态。

这体现一个重要原则：

```text
参数不完整时，不要调用后端业务服务。
```

原因是：

```text
后端服务需要明确参数
缺参数调用只会制造无意义错误
错误日志会变脏
用户也得不到真正有用的回答
```

正确做法是追问用户。

这也是 Agent 多轮对话能力的基础：

```text
信息不足
-> 追问
-> 用户补充
-> 再继续执行
```

### 4. 参数校验失败时如何处理

提取到订单号后，节点构造：

```python
arguments = QueryOrderArgs(order_id=order_id)
```

这一步可能抛出 `ValidationError`。

如果参数校验失败，节点返回：

```text
order_query_status = "failed"
order_query_error_code = "TOOL_ARGUMENTS_VALIDATION_FAILED"
agent_error_node = "query_order"
fallback_used = True
```

这说明：

```text
订单号看起来存在
但不符合工具参数模型要求
所以不能继续调用工具
```

真实系统里，参数校验失败通常属于客户端输入问题或上游提取问题。

它应该被明确记录，方便以后优化提取逻辑或提示用户。

### 5. 成功查询后 state 里有什么

成功时，节点返回：

```python
return {
    "order_query_order_id": result.order_id,
    "order_query_status": "succeeded",
    "order_query_result": result.model_dump(mode="json"),
    "order_query_error_code": None,
    "order_query_error_message": None,
    "final_answer": build_order_query_success_answer(result),
    "node_history": ["query_order"],
}
```

这里每个字段都有意义：

```text
order_query_order_id
本次实际查询的订单号，后续节点或日志可以直接使用。

order_query_status
本次订单查询状态。成功是 succeeded，缺订单号是 missing_order_id，失败是 failed。

order_query_result
结构化订单结果，后续可以用于模型总结、前端展示、评测断言。

order_query_error_code
成功时为空，失败时写错误码。

order_query_error_message
成功时为空，失败时写安全错误消息。

final_answer
当前返回给用户的中文回答。

node_history
记录 query_order 节点已经执行。
```

注意：`order_query_result` 使用了：

```python
result.model_dump(mode="json")
```

意思是把 Pydantic 模型转成普通 JSON 友好的 dict。

LangGraph state 里最好保存普通数据结构。

### 6. 为什么要把枚举状态翻译成中文

Java 或工具返回的状态可能是：

```text
waiting_shipment
paid
```

用户更容易理解：

```text
待发货
已支付
```

所以本节新增：

```python
ORDER_STATUS_LABELS = {
    "waiting_shipment": "待发货",
    "shipped": "已发货",
    "delivered": "已签收",
    "canceled": "已取消",
}
```

和：

```python
PAYMENT_STATUS_LABELS = {
    "unpaid": "未支付",
    "paid": "已支付",
    "refunded": "已退款",
}
```

这不是为了让代码复杂。

这是为了区分：

```text
系统内部稳定字段值
用户可读的展示文案
```

内部字段值适合机器处理。

展示文案适合用户阅读。

这两层在真实项目里通常要分开。

### 7. 为什么工具异常分成两类

节点里对异常分成：

```python
except AppException as exc:
    ...
except Exception as exc:
    ...
```

`AppException` 表示项目已经知道怎么表达这个错误。

例如：

```text
ORDER_NOT_FOUND
TOOL_RESULT_VALIDATION_FAILED
JAVA_ORDER_SERVICE_TIMEOUT
```

这类错误可以把 `code` 和 `message` 写回 state。

未知 `Exception` 表示没有被项目显式识别的错误。

这类错误不能直接暴露内部细节。

所以统一收敛成：

```text
TOOL_CALL_FAILED
订单查询工具调用失败，请稍后重试或联系人工客服。
```

这叫错误边界收敛。

它的价值是：

```text
对用户安全
对日志可查
对测试可控
对后续升级友好
```

### 8. 为什么 `build_ticket_agent_graph` 也要接收 executor

只改 `query_order_node` 还不够。

因为多数时候我们不会手动调用节点，而是调用完整图：

```python
graph = build_ticket_agent_graph()
result = graph.invoke(...)
```

如果图构造函数不支持传入 `order_query_executor`，测试完整图时就会走默认真实工具。

这会带来问题：

```text
单元测试可能依赖 Java 服务是否启动
网络抖动会导致测试失败
本节测试范围变得不清晰
```

所以本节把 executor 从图构造函数透传到节点：

```text
build_ticket_agent_graph(order_query_executor=...)
-> lambda state: query_order_node(state, order_query_executor=...)
```

这是一种很常见的测试友好设计。

### 9. 为什么还要更新 stream 测试

LangGraph 有普通执行和流式执行：

```text
graph.invoke()
graph.stream()
```

普通执行只看最终 state。

流式执行可以看到每个节点的更新。

本节把 `query_order` 从占位返回变成真实结构化返回，所以原来的 stream 测试不能再断言占位文案。

现在应该断言：

```text
query_order 更新里有 order_query_order_id
query_order_status 是 succeeded
order_query_result 里有 order_id 和 source
final_answer 包含查询到订单
node_history 是 ["query_order"]
```

这说明流式输出里也能看到真实订单查询节点的结构化结果。

### 10. 本节链路和阶段 3 工具调用的关系

阶段 3 第 13 节学过：

```text
模型请求 query_order
后端执行工具
把工具结果再交给模型总结
```

本节不完全重复那条链路。

本节是在 LangGraph 智能工单 Agent 里接入工具执行。

区别可以这样看：

```text
阶段 3：
重点是 Tool Calling 机制
模型提出工具请求，后端执行，再由模型总结

阶段 6 第 19 节：
重点是 LangGraph 节点生产化
Agent 路由到 query_order 节点，节点执行真实工具，把结构化结果写入 state
```

以后可以把两者合起来：

```text
LangGraph query_order 节点
-> 执行真实工具
-> 把工具结果交给模型总结
-> 写入最终回答
```

但本节先不加模型总结，是为了把工具执行边界先学透。

---

## 六、本节代码改动讲解

### 1. 新增订单查询执行器类型

本节新增：

```python
OrderQueryExecutor = Callable[[QueryOrderArgs], QueryOrderResult]
```

这行代码定义的是一个“函数形状”。

它表示：

```text
接收 QueryOrderArgs
返回 QueryOrderResult
```

任何符合这个形状的函数或对象，都可以作为订单查询执行器。

真实执行器：

```python
def execute_ticket_order_query(arguments: QueryOrderArgs) -> QueryOrderResult:
    return run_query_order_tool(arguments)
```

测试执行器：

```python
class RecordingOrderQueryExecutor:
    def __call__(self, arguments: QueryOrderArgs) -> QueryOrderResult:
        self.calls.append(arguments)
        return make_query_order_result(arguments.order_id)
```

这说明 Python 里不一定非要写接口类。

只要对象能像函数一样被调用，并符合输入输出契约，就可以注入使用。

### 2. 扩展 `TicketAgentState`

本节给 state 增加了订单查询相关字段：

```python
order_query_order_id: str | None
order_query_status: TicketOrderQueryStatus
order_query_result: dict[str, Any]
order_query_error_code: str | None
order_query_error_message: str | None
```

这些字段让订单查询不再只是 `final_answer` 的一部分，而是变成可观察、可测试、可复用的结构化状态。

如果以后要做这些事，就能直接用它们：

```text
前端展示订单卡片
后续节点根据订单状态决定是否创建工单
评测脚本统计订单查询成功率
日志追踪订单查询失败原因
checkpoint 保存订单查询状态
```

### 3. 新增订单状态展示映射

本节新增订单状态和支付状态的中文映射。

核心作用是：

```text
内部状态值保持稳定
用户回答使用中文展示
```

如果不做映射，用户会看到：

```text
waiting_shipment
paid
```

这对普通用户不友好。

但如果内部直接存中文，也会影响程序判断。

所以更好的做法是：

```text
内部 state 保存结构化字段值
最终回答时再做用户可读展示
```

### 4. 新增缺订单号状态构造函数

```python
def build_order_query_missing_order_id_state() -> TicketAgentState:
    return {
        "order_query_order_id": None,
        "order_query_status": "missing_order_id",
        "order_query_error_code": "ORDER_ID_REQUIRED",
        "order_query_error_message": TICKET_ORDER_QUERY_MISSING_ORDER_ID_MESSAGE,
        "final_answer": TICKET_ORDER_QUERY_MISSING_ORDER_ID_MESSAGE,
        "node_history": ["query_order"],
    }
```

这段代码学习重点是：

```text
缺参数也是一种明确状态
不是异常崩溃
不是随便返回一句文案
```

用户没给订单号时，系统还没有真正失败。

它只是需要更多信息。

所以状态叫：

```text
missing_order_id
```

这比直接写 `failed` 更准确。

### 5. 新增工具失败状态构造函数

```python
def build_order_query_failure_state(...):
    update = build_ticket_agent_fallback_state(
        node_name="query_order",
        code=code,
        message=message,
    )
    update.update(...)
    return update
```

这里复用了已有的 `build_ticket_agent_fallback_state`。

这样订单查询失败时，也能和其他节点失败保持一致：

```text
agent_error_code
agent_error_message
agent_error_node
fallback_used
final_answer
```

这就是项目内错误状态的一致性。

一致性越好，后续日志、评测、排查越容易。

### 6. 新增成功回答构造函数

```python
def build_order_query_success_answer(result: QueryOrderResult) -> str:
    ...
```

它负责把结构化订单结果转成用户可读回答。

这里有一个重要设计点：

```text
工具结果仍然是结构化数据
用户看到的是展示层文案
```

不要把展示文案当成后续业务判断依据。

后续节点如果要判断订单状态，应该读：

```python
state["order_query_result"]["order_status"]
```

而不是从 `final_answer` 里解析“待发货”。

### 7. 替换 `query_order_node` 占位逻辑

本节最核心的代码是 `query_order_node`。

它现在完整做了：

```text
读取输入
提取订单号
缺参数返回追问
构造 QueryOrderArgs
参数校验失败返回结构化失败
选择真实或注入 executor
记录开始日志
执行工具
处理 AppException
处理未知 Exception
记录成功日志
写入成功 state
```

这就是一个生产化工具节点的最小形态。

它不是最复杂的版本，但边界已经清楚：

```text
输入边界：state -> order_id -> QueryOrderArgs
执行边界：executor(arguments)
错误边界：AppException / unknown exception
输出边界：QueryOrderResult -> state
```

### 8. 图构造函数透传 executor

本节更新：

```python
build_ticket_agent_graph(order_query_executor=...)
build_ticket_agent_graph_for_model_mode(order_query_executor=...)
build_checkpointed_ticket_agent_graph(order_query_executor=...)
build_interrupting_ticket_agent_graph(order_query_executor=...)
```

为什么这些都要改？

因为当前项目有多种构造图的入口：

```text
普通图
按模型模式构造的图
带 checkpoint 的图
带 interrupt 的图
```

如果只改普通图，其他入口仍然不能注入订单查询 fake。

这会造成测试和真实运行行为不一致。

生产化工程里，依赖透传要保持完整。

---

## 七、本节测试讲解

测试不是本节笔记重点，但几个关键测试要看懂。

### 1. 成功查询测试

测试目标：

```text
query_order_node 能从文本里提取 A1001
能调用注入的 executor
能把 QueryOrderResult 写回 state
能生成包含订单号和状态的回答
能记录成功日志
```

这保护的是主成功链路。

### 2. 缺少订单号测试

测试目标：

```text
用户说“我的订单到哪了？”
系统不能调用 executor
必须返回 missing_order_id
必须提示用户提供订单号
```

这保护的是缺参数边界。

### 3. 工具业务异常测试

测试目标：

```text
executor 抛 AppException
节点写入 failed
保留错误码 ORDER_NOT_FOUND
agent_error_node 是 query_order
fallback_used 为 True
final_answer 使用安全业务错误消息
```

这保护的是已知工具错误边界。

### 4. 完整图注入 executor 测试

测试目标：

```text
build_ticket_agent_graph(order_query_executor=executor)
完整 invoke 后能走到 query_order 节点
node_history 是 normalize_user_input -> classify_intent -> query_order
```

这保护的是：

```text
不是单个节点能跑就够了
完整 LangGraph 路由也必须能接入真实工具节点
```

### 5. 为什么不在测试里启动 Java 服务

本节的自动测试没有启动 Java mock service。

原因是：

```text
单元测试要验证节点逻辑
不是验证 Docker、网络、Java 服务状态
```

以后可以加 smoke test 手动验证真实服务链路。

但 pytest 自动回归默认应该稳定、快速、可重复。

---

## 八、完整链路复盘

本节完成后，订单查询这条路径可以这样讲：

```text
当用户问“我的订单 A1001 到哪了？”时，
LangGraph 先把用户输入归一化，
再识别意图为 order_query，
然后路由到 query_order_node。

query_order_node 不直接相信原文，
而是从 normalized_message 提取订单号，
并用 QueryOrderArgs 做参数校验。

校验通过后，节点调用订单查询 executor。
默认 executor 会复用已有 query_order 工具。
query_order 工具通过 JavaOrderClient 请求 Java mock 订单服务，
拿到原始订单数据后做字段白名单映射，
再用 QueryOrderResult 校验结果。

校验成功后，节点把订单结果写入 LangGraph state，
同时生成用户可读的中文回答。
如果缺少订单号、业务工具报错或出现未知异常，
节点会返回结构化失败状态，而不是让流程直接崩溃。
```

这段话如果你能顺畅讲出来，说明本节主线已经理解。

---

## 九、常见误区

### 误区 1：以为 LangGraph 节点就是工具

不对。

节点是流程步骤，工具是业务能力。

节点可以调用工具，但节点本身不等于工具。

### 误区 2：以为只读工具就不用安全控制

不对。

只读工具不会改数据，但可能泄露数据、越权查询、暴露内部字段或造成服务压力。

### 误区 3：以为测试必须连真实 Java 服务才算真实

不对。

自动化测试优先验证代码契约。

真实跨服务链路可以用 smoke test 或集成测试单独覆盖。

### 误区 4：把 `final_answer` 当成业务数据

不对。

`final_answer` 是展示文案。

后续程序判断应该读结构化 state，例如 `order_query_result`。

### 误区 5：工具失败时只返回一句话就行

不够。

用户需要一句安全话，但系统也需要结构化错误码、失败节点和 fallback 标记。

否则后续无法测试、评测、统计和排查。

---

## 十、本节练习

### 练习 1：解释 `query_order` 和 `query_order_node` 的区别

题目：用自己的话解释为什么项目里既有 `query_order` 工具函数，又有 `query_order_node`。

参考答案：

`query_order` 是业务工具，负责真正查询订单、调用 Java 服务、做字段映射和结果校验。`query_order_node` 是 LangGraph 流程节点，负责从 Agent state 里取用户输入、提取订单号、调用工具、处理异常，并把结果写回 state。前者偏业务能力，后者偏流程编排。

### 练习 2：画出本节订单查询链路

题目：从“我的订单 A1001 到哪了？”开始，写出它经过的主要步骤。

参考答案：

```text
用户输入
-> normalize_user_input
-> classify_intent 得到 order_query
-> 条件边路由到 query_order
-> query_order_node 提取 A1001
-> QueryOrderArgs 校验
-> order_query_executor 执行
-> query_order 工具
-> JavaOrderClient.get_order("A1001")
-> Java mock service 返回订单
-> 字段白名单映射
-> QueryOrderResult 校验
-> 写回 order_query_result
-> 生成 final_answer
```

### 练习 3：说明为什么要注入 executor

题目：为什么不在测试里直接调用真实 `query_order`？

参考答案：

因为单元测试要稳定、快速、可重复。真实 `query_order` 会依赖 Java 服务、网络、配置和外部状态，容易让测试变慢或偶发失败。注入 fake executor 可以只测试 LangGraph 节点逻辑，同时保留真实运行时默认执行真实工具的能力。

### 练习 4：缺少订单号时应该怎么处理

题目：用户只说“我的订单到哪了？”时，节点为什么不应该调用工具？

参考答案：

因为工具需要明确订单号。缺少订单号时调用工具没有意义，还会制造无效错误和脏日志。正确做法是返回 `missing_order_id` 状态，并提示用户提供订单号。

### 练习 5：解释字段白名单映射的作用

题目：为什么 Java 服务返回的订单数据不应该原样交给 Agent？

参考答案：

因为原始业务数据可能包含 AI 层不该使用或不该暴露的字段。白名单映射只保留允许进入 AI 服务的字段，并统一字段结构，再用 Pydantic 校验。这样可以减少敏感信息泄露和字段漂移风险。

### 练习 6：解释 `AppException` 和未知异常的不同处理

题目：为什么节点要分别捕获 `AppException` 和普通 `Exception`？

参考答案：

`AppException` 是项目内已知错误，包含明确 `code`、`message` 和 `status_code`，可以安全写入 state。普通 `Exception` 是未知错误，可能包含内部细节，不能直接暴露给用户，所以要统一转换成安全的 `TOOL_CALL_FAILED` 兜底。

### 练习 7：说明 `order_query_result` 和 `final_answer` 的区别

题目：为什么成功查询后既要保存 `order_query_result`，又要生成 `final_answer`？

参考答案：

`order_query_result` 是结构化业务数据，适合后续节点、测试、评测和前端展示使用。`final_answer` 是给用户看的自然语言回答，适合阅读，但不适合作为程序判断依据。两者分别服务机器和用户。

---

## 十一、自测题

### 自测 1：本节的“真实 query_order”真实在哪里？

答案：真实在于 LangGraph 节点不再返回占位文案，而是复用已有 `query_order` 工具，默认通过 `JavaOrderClient` 调用 Java mock 服务，并经过字段白名单映射和 `QueryOrderResult` 校验。

### 自测 2：`OrderQueryExecutor = Callable[[QueryOrderArgs], QueryOrderResult]` 表达了什么？

答案：它表达订单查询执行器的输入输出契约：接收 `QueryOrderArgs`，返回 `QueryOrderResult`。符合这个形状的函数或可调用对象都可以注入到节点里。

### 自测 3：为什么 `query_order_node` 返回的是部分 state？

答案：LangGraph 节点通常返回要合并进全局 state 的更新字段，而不是重新构造完整 state。这样每个节点只负责自己产生的字段。

### 自测 4：缺少订单号时，`order_query_status` 为什么不是 `failed`？

答案：缺少订单号更准确地说是“参数不足，需要用户补充”，不是工具执行失败。用 `missing_order_id` 可以让调用方区分追问场景和真正失败场景。

### 自测 5：为什么 `result.model_dump(mode="json")` 比直接把 Pydantic 对象塞进 state 更合适？

答案：`model_dump(mode="json")` 会把 Pydantic 模型转成 JSON 友好的普通 dict，更适合 state 序列化、stream 输出、测试断言和后续 checkpoint。

### 自测 6：为什么本节没有让模型总结工具结果？

答案：因为本节重点是工具链路接入 LangGraph。先把参数、执行、结果、错误和 state 边界做稳定，再引入模型总结，学习负担和系统变量都会更清楚。

### 自测 7：如果 Java 服务返回多余字段，当前 AI 服务会怎么处理？

答案：`map_java_order_to_query_order_payload` 只取白名单字段，多余字段不会进入 `QueryOrderResult`。这可以避免原始业务字段直接暴露给 AI 层。

### 自测 8：如果 Java 服务返回的订单状态不符合 `QueryOrderResult` 的枚举要求，会怎样？

答案：工具结果校验会失败，并被映射成项目内错误，例如 `TOOL_RESULT_VALIDATION_FAILED`，节点捕获后写入失败 state。

### 自测 9：为什么完整图测试比单节点测试多一层价值？

答案：单节点测试只能证明 `query_order_node` 自己能工作；完整图测试还能证明意图识别后的条件边会正确路由到 `query_order`，并且图构造函数能正确注入 executor。

### 自测 10：本节完成后，下一节适合学什么？

答案：下一节适合学“工具节点错误处理升级”。因为本节已经能执行真实订单查询工具，下一步就应该系统化处理工具超时、404、502、参数错误、结果校验失败、未知异常和日志/评测字段。

---

## 十二、面试表达

如果面试官问：你们的 Agent 是怎么接业务系统的？

可以这样回答：

```text
我们没有让大模型直接操作业务系统，而是把业务能力封装成后端工具。
以订单查询为例，LangGraph 先通过意图识别把用户问题路由到 query_order 节点。
节点从用户文本里提取订单号，用 Pydantic 的 QueryOrderArgs 校验参数，
再调用订单查询 executor。默认 executor 会复用 query_order 工具，
由 JavaOrderClient 调用 Java 订单服务。

Java 服务返回原始订单数据后，AI 服务不会原样使用，
而是先做字段白名单映射，再用 QueryOrderResult 校验。
成功后，节点把结构化订单结果写入 LangGraph state，
同时生成用户可读回答。

为了测试稳定，我们给 query_order_node 和图构造函数都支持 executor 注入，
单元测试里用 fake executor，不依赖真实 Java 服务。
工具异常也会被结构化写入 state，保留错误码、失败节点和 fallback 标记。
```

这段表达体现了几个能力：

```text
Agent 编排能力
跨服务调用能力
Pydantic 边界校验能力
安全边界意识
测试可替换依赖能力
生产化错误处理意识
```

---

## 十三、本节小结

本节完成了一件关键事情：

```text
把 LangGraph 智能工单 Agent 的 query_order 节点，从占位回答升级为真实订单查询工具节点。
```

现在订单查询路径已经具备：

```text
订单号提取
参数模型校验
真实工具执行
Java mock 服务调用
字段白名单映射
结果模型校验
成功 state 写回
缺参数追问
工具异常兜底
executor 注入测试
完整图路由测试
```

你要重点掌握的不是某一行代码。

本节最重要的是这条工程原则：

```text
Agent 可以决定流程方向，但真实业务执行必须由后端代码控制边界。
```

下一节进入：

```text
阶段 6 第 20 节：工具节点错误处理升级
```

我们会在本节真实工具接入的基础上，把工具节点的失败类型、错误状态、日志字段和回归测试继续做扎实。
