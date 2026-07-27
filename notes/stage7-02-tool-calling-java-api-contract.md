# 阶段 7 第 2 节：面向 Tool Calling 的 Java API 契约设计

## 本节定位

上一节我们确定了阶段 7 的核心边界：

```text
模型提出意图，后端执行动作。
```

这句话还只是原则。

这一节要把原则落到接口契约上。

也就是回答这些问题：

```text
Python AI 服务到底怎样调用 Java 后端？
Java 后端到底返回什么给 Python？
哪些信息可以给模型总结？
哪些信息只能留在 Java 内部？
错误码怎么设计，Agent 才能稳定处理？
Header 里应该传哪些上下文？
读工具和写工具的契约有什么区别？
```

本节仍然不急着写 Spring Boot 代码。

原因是：

```text
先定契约，再写实现。
```

如果不先定契约，后面很容易写成普通 CRUD 接口：

```text
GET /orders/{id}
POST /tickets
```

这当然能跑。

但 AI Agent 接真实业务系统时，只能跑还不够。

还要做到：

```text
字段稳定
错误可分类
权限可兜底
写操作可幂等
日志可追踪
模型可安全总结
测试可验证契约没有变
```

这才是阶段 7 的重点。

---

## 一、本节学习目标

学完本节，你要能讲清楚：

1. 什么是 API 契约。
2. 为什么 API 契约不只是 URL。
3. 为什么 Tool Calling 场景下契约比普通后端接口更重要。
4. Python AI 服务、Java 后端、大模型、测试分别依赖契约的哪部分。
5. 订单查询接口为什么适合做读工具。
6. 创建工单接口为什么属于写工具。
7. `order_id` 什么时候放 path，什么时候放 body。
8. `Idempotency-Key` 为什么更适合放 Header。
9. `X-Trace-Id`、`X-Caller`、`X-User-Id`、`X-Tenant-Id` 分别解决什么问题。
10. HTTP 状态码和业务错误码应该怎么配合。
11. 为什么不要所有错误都返回 HTTP 200。
12. 统一响应结构应该包含哪些字段。
13. 订单查询响应应该返回哪些字段。
14. 创建工单响应应该返回哪些字段。
15. 哪些字段不能给模型。
16. Java Entity、Java DTO、Python Pydantic Model、Tool Schema 的区别。
17. 错误码如何影响 Agent 下一步行为。
18. 契约变更为什么要考虑兼容性。
19. 契约测试应该测什么。
20. 本项目阶段 7 后续实现应该按哪份契约走。

---

## 二、本节先不做什么

这一节暂时不做：

1. 不创建 Spring Boot 项目。
2. 不写 Java Controller。
3. 不写 MySQL 表。
4. 不接 Redis。
5. 不改 Python client。
6. 不启动服务。
7. 不打开 VMware。
8. 不跑真实模型。

本节的产出是：

```text
接口契约学习笔记
可复用的 Java-AI API 契约文档
README 和学习进度索引更新
```

后续阶段写代码时，要尽量按照本节契约实现。

---

## 三、基础知识铺垫

### 1. 什么是 API 契约

API 契约就是服务之间约定好的调用规则。

它不只是：

```text
一个 URL。
```

完整 API 契约至少包括：

```text
请求方法
URL 路径
Path 参数
Query 参数
请求 Header
请求 Body
响应 Header
响应 Body
HTTP 状态码
业务错误码
字段类型
字段含义
字段是否必填
枚举值
鉴权方式
幂等规则
超时和重试语义
版本兼容规则
```

例如：

```text
GET /internal/orders/{order_id}
```

这只是路径。

真正的契约还要说明：

```text
order_id 是否允许空？
order_id 支持哪些字符？
用户身份从哪里来？
订单不存在返回什么 HTTP 状态？
无权限返回什么错误码？
返回字段里有没有手机号？
返回的 order_status 枚举有哪些值？
trace_id 怎么传？
Python 是否可以重试？
```

这些都属于 API 契约。

### 2. 为什么 Tool Calling 场景下契约更重要

普通前端调用后端，接口字段变了，前端页面可能直接报错。

AI Agent 调后端，接口字段变了，有时不会马上崩。

但会更危险。

例如 Java 原来返回：

```json
{
  "order_id": "A1001",
  "order_status": "shipped",
  "logistics_message": "订单已发货，预计 2 天内送达。"
}
```

Python 把它交给模型总结。

如果 Java 改成：

```json
{
  "id": "A1001",
  "state": "S",
  "logistics": "sent"
}
```

Python 如果没有严格校验，可能仍然把 JSON 交给模型。

模型也许还能猜出一点意思。

但回答质量会变差：

```text
订单似乎已经 sent，可能已发送。
```

这不是稳定系统。

所以 Tool Calling 场景下契约更重要。

因为契约同时影响：

```text
Python client 是否能解析
Pydantic 是否能校验
Agent 是否能决定下一步
模型是否能正确总结
eval 是否能稳定判断结果
日志是否能定位问题
```

### 3. API 契约的参与方

在本项目里，接口契约不是 Java 自己看的。

至少有 6 个参与方。

第一，Java 后端。

Java 后端要按照契约实现：

```text
路径
参数
Header
响应结构
错误码
权限
幂等
```

第二，Python AI 服务。

Python client 要按照契约调用：

```text
传正确 Header
传正确 Body
解析统一响应
映射错误码
做 Pydantic 校验
```

第三，工具注册表。

Tool schema 要和契约对齐。

例如模型看到的 `query_order` 参数是：

```json
{
  "order_id": "A1001"
}
```

那 Java 订单查询接口也要能接收这个业务含义。

第四，大模型。

模型不直接看全部 Java 响应，但会看到 Python 白名单过滤后的工具结果。

所以契约会影响模型总结。

第五，测试。

契约测试要验证：

```text
Java 响应是否符合 Python 预期
Python client 是否能识别错误
错误码变更是否导致 Agent 行为变化
```

第六，未来的你。

当项目变复杂后，契约文档会帮助你判断：

```text
这个字段能不能改？
这个错误码能不能删？
这个接口能不能给模型看？
这个操作能不能重试？
```

### 4. Tool Schema 和 Java API 契约不是一回事

Tool Schema 是给模型看的工具参数说明。

例如：

```json
{
  "name": "query_order",
  "parameters": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string"
      }
    },
    "required": ["order_id"]
  }
}
```

它告诉模型：

```text
如果你要查订单，只能提供 order_id。
```

Java API 契约是 Python 调 Java 的接口说明。

例如：

```text
GET /internal/orders/{order_id}
Header: X-Trace-Id, X-Caller, X-User-Id, X-Tenant-Id, X-Internal-Token
Response: ApiResponse<OrderToolView>
```

它告诉 Python 和 Java：

```text
后端如何真正执行订单查询。
```

两者应该对齐，但不是同一个东西。

关系是：

```text
Tool Schema
-> 限制模型能提出什么参数

Java API Contract
-> 限制 Python 和 Java 之间如何安全执行动作
```

### 5. URL、Body、Header 分别放什么

这是接口契约里很常见的问题。

URL 适合放资源定位信息。

例如：

```text
GET /internal/orders/A1001
```

这里 `A1001` 是要查询的订单资源。

Body 适合放复杂业务数据。

例如创建工单：

```json
{
  "title": "物流太慢",
  "description": "用户反馈 A1001 订单物流停滞。",
  "category": "logistics",
  "priority": "normal",
  "related_order_id": "A1001"
}
```

Header 适合放调用上下文和控制信息。

例如：

```text
X-Trace-Id
X-Caller
X-User-Id
X-Tenant-Id
X-Internal-Token
Idempotency-Key
```

这些不是业务表单字段。

它们描述的是：

```text
谁在调用
代表哪个用户
属于哪个租户
如何追踪
如何鉴权
如何防重复
```

### 6. `order_id` 放 path 还是 body

查询单个订单时，`order_id` 适合放 path：

```text
GET /internal/orders/{order_id}
```

因为这是典型资源查询。

它表达：

```text
查询某一个订单资源。
```

如果是复杂搜索，则适合用 query 或 body。

例如：

```text
GET /internal/orders?status=shipped&from=2026-07-01
```

或者：

```text
POST /internal/orders/search
```

本项目当前只需要按订单号查订单。

所以契约使用：

```text
GET /internal/orders/{order_id}
```

### 7. `Idempotency-Key` 为什么放 Header

创建工单需要幂等键。

可以放 body：

```json
{
  "idempotency_key": "ticket-create-xxx",
  "title": "物流太慢"
}
```

也可以放 Header：

```text
Idempotency-Key: ticket-create-xxx
```

更推荐放 Header。

原因是：

```text
幂等键不是业务数据本身。
幂等键是请求控制信息。
同一份业务参数可以由不同请求控制信息包裹。
很多 API 约定都把幂等键作为 Header。
```

Java 后端处理时可以理解为：

```text
Body 告诉我要创建什么工单。
Idempotency-Key 告诉我这次创建请求如何防重复。
```

### 8. HTTP 状态码和业务错误码怎么配合

不要只用 HTTP 状态码。

因为：

```text
404 只能说明没找到，但不知道是订单不存在、接口不存在、还是路由错误。
403 只能说明禁止访问，但不知道是订单权限、租户权限、还是内部服务权限。
500 只能说明服务错误，但不知道是数据库、Redis、下游超时、还是未知异常。
```

也不要所有错误都返回 HTTP 200。

因为：

```text
HTTP 状态码是基础协议语义。
网关、日志、监控、重试策略都会依赖它。
所有错误都 200，会让系统误以为调用成功。
```

推荐做法：

```text
HTTP 状态码表达大类。
业务错误码表达具体原因。
```

例如：

```text
404 + ORDER_NOT_FOUND
403 + ORDER_ACCESS_DENIED
422 + ORDER_ID_INVALID
409 + TICKET_IDEMPOTENCY_CONFLICT
504 + JAVA_SERVICE_TIMEOUT
502 + JAVA_SERVICE_UNAVAILABLE
```

这样 Python AI 服务可以同时利用：

```text
HTTP status
business code
message
trace_id
```

### 9. 统一响应结构的价值

统一响应结构不是为了格式好看。

它是为了让调用方稳定处理结果。

本项目建议真实 Java 服务返回：

```json
{
  "success": true,
  "code": "OK",
  "message": "OK",
  "data": {},
  "trace_id": "trace-id"
}
```

失败时：

```json
{
  "success": false,
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在，请确认订单号是否正确。",
  "data": null,
  "trace_id": "trace-id"
}
```

这样 Python 可以稳定判断：

```text
success 为 true -> 读取 data 并做 Pydantic 校验。
success 为 false -> 读取 code 并映射成 Agent 行为。
trace_id -> 写日志和排查问题。
```

### 10. 错误码会影响 Agent 行为

错误码不是给人看的装饰。

它会影响 Agent 下一步。

例如订单查询失败：

```text
ORDER_NOT_FOUND
```

Agent 应该告诉用户：

```text
没有查到这个订单，请确认订单号。
```

如果是：

```text
ORDER_ACCESS_DENIED
```

Agent 应该告诉用户：

```text
当前身份无权查看该订单。
```

如果是：

```text
JAVA_SERVICE_TIMEOUT
```

Agent 可以：

```text
提示稍后再试
触发重试策略
转人工
```

如果是：

```text
MISSING_REQUIRED_FIELD
```

Agent 可以继续追问用户缺失字段。

所以错误码本质上是：

```text
Java 后端告诉 AI 服务下一步应该怎么处理的机器信号。
```

### 11. DTO、Entity、Pydantic Model、Tool Schema 的区别

这几个概念容易混。

Java Entity：

```text
面向数据库表。
关注持久化字段。
不应该直接暴露给 AI。
```

Java Request/Response DTO：

```text
面向 HTTP API 契约。
关注调用方能传什么、能看到什么。
```

Python Pydantic Model：

```text
面向 Python AI 服务内部校验。
保证 Java 返回结果符合 Python 预期。
```

Tool Schema：

```text
面向模型。
告诉模型允许提出哪些工具参数。
```

它们之间的关系是：

```text
数据库 Entity
-> Java DTO
-> Python Pydantic Model
-> 白名单工具结果
-> 模型总结
```

越往后，字段应该越少、越安全、越面向用户可见信息。

### 12. 字段白名单和最小暴露

字段白名单是指：

```text
明确允许哪些字段流向 Python AI 服务和模型。
```

不是黑名单。

黑名单是：

```text
这些字段不能给模型。
```

白名单是：

```text
只有这些字段能给模型。
```

AI 场景推荐白名单。

因为未来数据库字段会增加。

如果只靠黑名单，新增字段可能不小心暴露给模型。

例如订单 Entity 新增：

```text
risk_score
internal_cost
fraud_flag
customer_phone
```

如果没有白名单，可能被返回到 AI 服务。

所以更稳的做法是：

```text
Java Response DTO 先收敛字段。
Python 再做一次 Pydantic 校验和白名单映射。
模型只看到最终工具结果。
```

### 13. Header 契约是 AI 后端的重要部分

传统接口设计时，有时只关注 body。

但 AI Agent 调后端时，Header 很关键。

建议至少设计这些：

```text
X-Trace-Id
X-Caller
X-User-Id
X-Tenant-Id
X-Internal-Token
Idempotency-Key
```

其中：

```text
X-Trace-Id
-> 串联 Python + Java 日志。

X-Caller
-> 标识调用方是 ai-service。

X-User-Id
-> 表示当前用户身份。

X-Tenant-Id
-> 表示租户或业务域。

X-Internal-Token
-> 内部服务鉴权。

Idempotency-Key
-> 写操作防重复。
```

不是每个接口都需要 `Idempotency-Key`。

读接口一般不需要。

写接口必须考虑。

### 14. 契约变更要兼容

接口契约一旦被 Python AI 服务依赖，就不能随便改。

危险变更包括：

```text
删除字段
修改字段名
修改字段类型
修改枚举值
修改错误码
把原本可空字段改成必填
改变 HTTP 状态码语义
改变幂等行为
```

相对安全的变更包括：

```text
新增可选字段
新增错误码但保持旧错误码兼容
新增响应 data 里的非必需字段
新增接口版本
```

如果必须破坏兼容，建议新开版本：

```text
/internal/v2/orders/{order_id}
```

或者保留旧字段一段时间。

### 15. 契约测试是什么

契约测试不是测业务算法多复杂。

它测的是：

```text
服务之间约定有没有被破坏。
```

例如：

```text
Java 查询订单成功时，必须返回 success=true、code=OK、data.order_id。
Java 查询订单不存在时，必须返回 404 + ORDER_NOT_FOUND。
Java 创建工单缺少 Idempotency-Key 时，必须返回 400/422 + IDEMPOTENCY_KEY_REQUIRED。
Python client 收到 ORDER_ACCESS_DENIED 时，必须映射成正确 AppException。
```

契约测试的价值是：

```text
Java 改接口时，能及时发现 Python AI 服务会不会被破坏。
```

---

## 四、本节主题系统讲解

### 1. 当前项目已有契约雏形

当前 `java-mock-service` 已经有两个核心接口：

```text
GET /orders/{order_id}
POST /tickets
```

当前 `ai-service` 已经有：

```text
JavaOrderClient
JavaTicketClient
QueryOrderArgs
QueryOrderResult
CreateTicketArgs
CreatedTicket
Tool Registry
Idempotency-Key
X-Trace-Id
```

这说明项目不是从零开始。

已经有了可运行的 mock 契约。

但当前契约还偏学习 Demo：

```text
接口路径没有 internal 前缀
成功响应直接返回业务对象
错误响应和成功响应结构不统一
Header 只有 trace_id 和幂等键雏形
用户身份和租户边界还不完整
内部鉴权还没系统设计
字段白名单还需要更明确
错误码分类还可以更贴近 Agent 行为
```

阶段 7 第 2 节就是把它升级成真实后端契约草案。

### 2. 推荐的阶段 7 契约文件

本节新增：

```text
docs/java-ai-api-contract.md
```

它不是代码。

它是后续实现 Spring Boot 服务时的接口合同。

后续写 Java 代码时，应该让：

```text
Controller
Request DTO
Response DTO
Exception Handler
Swagger/OpenAPI
Python client
契约测试
```

都尽量对齐这份文档。

### 3. 基础路径建议

当前 mock 路径是：

```text
GET /orders/{order_id}
POST /tickets
```

真实化后建议变成内部接口：

```text
GET /internal/orders/{order_id}
POST /internal/tickets
```

为什么加 `/internal`？

因为这些接口不是给普通浏览器用户直接调用的。

它们是：

```text
Python AI 服务调用 Java 业务服务的内部接口。
```

加 `/internal` 可以让边界更清楚：

```text
外部用户 -> Python AI 服务
Python AI 服务 -> Java internal API
Java internal API -> MySQL/Redis
```

### 4. 统一响应结构草案

建议统一响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "OK",
  "data": {},
  "trace_id": "trace-xxx"
}
```

字段说明：

```text
success
-> 是否业务成功。

code
-> 机器可读业务码。

message
-> 简短人类可读说明，供日志和必要时给模型参考。

data
-> 成功时的业务数据；失败时通常为 null。

trace_id
-> 本次请求追踪 ID。
```

注意：

```text
success=false 不应该配 HTTP 200。
```

例如订单不存在：

```text
HTTP 404
success=false
code=ORDER_NOT_FOUND
```

这样协议语义和业务语义都清楚。

### 5. Header 契约草案

阶段 7 建议先设计这些 Header：

| Header | 必填 | 用途 |
| --- | --- | --- |
| `X-Trace-Id` | 建议必填 | 串联 Python 和 Java 日志 |
| `X-Caller` | 必填 | 标识调用方，例如 `ai-service` |
| `X-User-Id` | 业务接口必填 | 当前真实用户 |
| `X-Tenant-Id` | 多租户场景必填 | 当前租户或业务域 |
| `X-Internal-Token` | 必填 | 内部服务鉴权 |
| `Idempotency-Key` | 写接口必填 | 防止重复写入 |

当前项目可以先用简化版本：

```text
X-Trace-Id
X-Caller
X-User-Id
X-Internal-Token
Idempotency-Key
```

`X-Tenant-Id` 可以先设计进契约，后续如果暂时没有多租户，也可以用默认值：

```text
default
```

### 6. 订单查询接口契约

推荐接口：

```text
GET /internal/orders/{order_id}
```

用途：

```text
给 Python AI 服务查询当前用户有权查看的订单摘要。
```

它是读工具。

请求 Header：

```text
X-Trace-Id: 4f7d...
X-Caller: ai-service
X-User-Id: U1001
X-Tenant-Id: default
X-Internal-Token: ***
```

Path 参数：

```text
order_id
```

约束：

```text
1 到 64 位
只允许字母、数字、下划线、短横线
```

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "OK",
  "data": {
    "order_id": "A1001",
    "order_status": "shipped",
    "payment_status": "paid",
    "logistics_message": "订单已发货，预计 2 天内送达。",
    "latest_event": "包裹已离开发货仓。",
    "can_create_ticket": true,
    "user_visible_summary": "订单已发货，正在运输中。"
  },
  "trace_id": "4f7d..."
}
```

这里返回的是订单摘要，不是完整订单 Entity。

### 7. 订单查询不应该返回哪些字段

订单查询工具不应该返回：

```text
用户手机号完整值
收货人完整姓名
完整收货地址
支付流水号
内部成本
供应商信息
内部风控字段
内部客服备注
数据库自增主键
租户内部配置
```

原因是：

```text
这些字段不是回答用户“订单到哪里了”所必需的。
这些字段给模型会增加泄露风险。
```

如果后续确实需要部分敏感信息，也应该：

```text
脱敏
按权限返回
明确白名单
避免传给模型
```

### 8. 订单查询错误码

建议错误码：

| HTTP | code | 含义 | Agent 行为 |
| --- | --- | --- | --- |
| 422 | `ORDER_ID_INVALID` | 订单号格式不合法 | 让用户重新提供订单号 |
| 401 | `INTERNAL_AUTH_FAILED` | Python 调 Java 内部鉴权失败 | 不暴露细节，记录告警 |
| 403 | `ORDER_ACCESS_DENIED` | 当前用户无权查看订单 | 告知无权查看 |
| 404 | `ORDER_NOT_FOUND` | 订单不存在 | 让用户确认订单号 |
| 504 | `JAVA_SERVICE_TIMEOUT` | Java 服务或数据库超时 | 提示稍后重试或转人工 |
| 503 | `JAVA_SERVICE_UNAVAILABLE` | 服务不可用 | 触发降级或转人工 |

这些错误码不是随便命名。

它们要服务 Agent 行为。

例如：

```text
ORDER_NOT_FOUND
-> 用户可能输错订单号。

ORDER_ACCESS_DENIED
-> 用户不是订单所有者。

JAVA_SERVICE_TIMEOUT
-> 不是用户的问题，是服务临时失败。
```

### 9. 创建工单接口契约

推荐接口：

```text
POST /internal/tickets
```

用途：

```text
在用户确认后，由 Python AI 服务请求 Java 后端创建客服工单。
```

它是写工具。

请求 Header：

```text
X-Trace-Id: 4f7d...
X-Caller: ai-service
X-User-Id: U1001
X-Tenant-Id: default
X-Internal-Token: ***
Idempotency-Key: ticket-create-4f7d-A1001
```

请求 Body：

```json
{
  "title": "物流太慢",
  "description": "用户反馈 A1001 订单物流长时间未更新，希望客服跟进。",
  "category": "logistics",
  "priority": "normal",
  "related_order_id": "A1001",
  "source": "ai_agent",
  "confirmation_id": "9f4d0b2f5b0c4f2a9d6c8b1e0a3f7c11"
}
```

这里有几个细节。

`requester_id` 不建议从 body 传。

更推荐从：

```text
X-User-Id
```

得到。

原因是：

```text
用户身份属于认证上下文，不应该由模型或请求 body 随便填写。
```

`confirmation_id` 可以放 body。

它表示：

```text
Python AI 服务侧确实完成过用户确认流程。
```

但 Java 后端不能只凭它无条件创建。

Java 仍然要校验：

```text
用户身份
订单归属
工单类型
幂等键
业务规则
```

### 10. 创建工单成功响应

成功响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "OK",
  "data": {
    "ticket_id": "T1001",
    "ticket_status": "created",
    "title": "物流太慢",
    "category": "logistics",
    "priority": "normal",
    "related_order_id": "A1001",
    "created_at": "2026-07-27T10:30:00Z",
    "user_visible_summary": "工单已创建，客服会继续跟进物流问题。"
  },
  "trace_id": "4f7d..."
}
```

注意：

```text
返回给 AI 的 data 仍然是用户可见摘要。
```

不应该返回：

```text
数据库内部主键
处理人内部排班
风控标记
内部 SLA 规则细节
内部备注
```

### 11. 创建工单错误码

建议错误码：

| HTTP | code | 含义 | Agent 行为 |
| --- | --- | --- | --- |
| 400 | `IDEMPOTENCY_KEY_REQUIRED` | 写操作缺少幂等键 | 阻断执行，记录后端错误 |
| 409 | `IDEMPOTENCY_KEY_CONFLICT` | 同一幂等键对应不同参数 | 阻断执行，提示系统异常 |
| 422 | `TICKET_REQUEST_INVALID` | 工单参数不合法 | 让用户补充或修正 |
| 403 | `ORDER_ACCESS_DENIED` | 无权基于该订单创建工单 | 告知无权操作 |
| 404 | `ORDER_NOT_FOUND` | 关联订单不存在 | 让用户确认订单号 |
| 409 | `TICKET_ALREADY_EXISTS` | 已存在类似工单 | 告知已有工单，不重复创建 |
| 409 | `ORDER_NOT_SUPPORT_TICKET` | 当前订单不支持创建该类工单 | 解释业务限制 |
| 504 | `JAVA_SERVICE_TIMEOUT` | 创建工单超时 | 如果有幂等键，可查询或重试 |
| 503 | `JAVA_SERVICE_UNAVAILABLE` | 服务不可用 | 提示稍后再试或转人工 |

写操作错误码要特别注意：

```text
超时不等于一定失败。
```

例如：

```text
Python 调 Java 创建工单超时。
```

可能发生了两种情况：

```text
Java 没创建成功。
Java 已经创建成功，但响应丢了。
```

所以写操作必须有幂等键。

后续可以通过同一个幂等键查询或重试，避免重复创建。

### 12. `confirmation_id` 和 `Idempotency-Key` 不是一回事

这两个字段容易混。

`confirmation_id` 解决：

```text
用户是否确认过这个 AI 计划。
```

`Idempotency-Key` 解决：

```text
同一个写请求重复提交时，业务结果不要重复创建。
```

它们不是同一个问题。

一个用户确认可能对应一次写请求。

但网络失败时，同一个写请求可能重试多次。

所以写操作里可以同时存在：

```text
confirmation_id
Idempotency-Key
```

### 13. 用户身份从 Header 来，不从模型来

当前学习项目里有些字段还会直接传 `requester_id`。

这是学习阶段可以接受的简化。

真实化后更推荐：

```text
用户身份来自认证上下文。
```

在 Python 调 Java 时，可以先用 Header 表达：

```text
X-User-Id: U1001
```

Java 后端根据它判断：

```text
用户是否存在
用户是否属于当前租户
用户是否有权查看订单
用户是否有权创建工单
```

不要让模型生成：

```json
{
  "requester_id": "admin"
}
```

然后 Java 就相信。

模型不能决定用户身份。

### 14. Python 要做两次白名单

Java 已经返回 DTO。

Python 仍然要做白名单。

第一层：

```text
Pydantic 校验 Java response data。
```

第二层：

```text
把校验后的 data 映射成模型可见 tool result。
```

比如 Java 返回：

```json
{
  "order_id": "A1001",
  "order_status": "shipped",
  "payment_status": "paid",
  "logistics_message": "订单已发货，预计 2 天内送达。",
  "latest_event": "包裹已离开发货仓。",
  "can_create_ticket": true,
  "user_visible_summary": "订单已发货，正在运输中。"
}
```

模型可能只需要：

```json
{
  "order_id": "A1001",
  "order_status": "shipped",
  "logistics_message": "订单已发货，预计 2 天内送达。",
  "can_create_ticket": true
}
```

这就是最小暴露。

### 15. Java 错误到 AI 回答的映射

Java 不应该直接生成最终 AI 回答。

Java 返回：

```text
ORDER_NOT_FOUND
```

Python AI 服务决定：

```text
这个错误是否交给模型总结。
是否直接用模板回答。
是否触发追问。
是否转人工。
```

建议策略：

```text
参数类错误
-> 让用户补充或修正。

权限类错误
-> 简洁告知无权，不暴露内部权限细节。

业务类错误
-> 按业务原因解释。

系统类错误
-> 提示稍后再试，记录日志，必要时转人工。
```

### 16. 契约如何影响 eval

Agent eval 不是只评模型回答。

契约稳定后，可以评：

```text
订单不存在时，Agent 是否让用户检查订单号。
无权限时，Agent 是否拒绝泄露信息。
工单重复时，Agent 是否告诉用户已有工单。
创建工单超时时，Agent 是否没有编造成功。
```

如果 Java 错误码不稳定，eval 就很难写。

所以契约是 eval 的基础。

### 17. 本节不直接改业务代码的原因

本节只新增文档，不改业务代码。

原因是：

```text
当前 mock 服务已经能跑。
我们先确定真实化目标契约。
后续再按契约创建或改造 Spring Boot 服务。
```

这样学习顺序更清楚：

```text
先知道为什么这么设计。
再知道接口应该长什么样。
最后再写代码实现。
```

---

## 五、本项目契约草案速记

### 1. 订单查询

```text
GET /internal/orders/{order_id}
```

类型：

```text
读工具
```

必备 Header：

```text
X-Trace-Id
X-Caller
X-User-Id
X-Tenant-Id
X-Internal-Token
```

成功 data：

```text
order_id
order_status
payment_status
logistics_message
latest_event
can_create_ticket
user_visible_summary
```

关键错误：

```text
ORDER_ID_INVALID
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
JAVA_SERVICE_TIMEOUT
JAVA_SERVICE_UNAVAILABLE
```

### 2. 创建工单

```text
POST /internal/tickets
```

类型：

```text
写工具
```

必备 Header：

```text
X-Trace-Id
X-Caller
X-User-Id
X-Tenant-Id
X-Internal-Token
Idempotency-Key
```

请求 body：

```text
title
description
category
priority
related_order_id
source
confirmation_id
```

成功 data：

```text
ticket_id
ticket_status
title
category
priority
related_order_id
created_at
user_visible_summary
```

关键错误：

```text
IDEMPOTENCY_KEY_REQUIRED
IDEMPOTENCY_KEY_CONFLICT
TICKET_REQUEST_INVALID
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
TICKET_ALREADY_EXISTS
ORDER_NOT_SUPPORT_TICKET
JAVA_SERVICE_TIMEOUT
JAVA_SERVICE_UNAVAILABLE
```

### 3. 统一响应

```json
{
  "success": true,
  "code": "OK",
  "message": "OK",
  "data": {},
  "trace_id": "trace-id"
}
```

失败：

```json
{
  "success": false,
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在，请确认订单号是否正确。",
  "data": null,
  "trace_id": "trace-id"
}
```

---

## 六、常见误区

### 误区 1：API 契约就是接口路径

不对。

接口路径只是契约的一小部分。

完整契约还包括：

```text
字段、类型、Header、错误码、状态码、鉴权、幂等、兼容规则。
```

### 误区 2：模型能理解错误消息，所以错误码不重要

不对。

模型可以理解自然语言，但 Agent 需要机器可读信号。

错误码决定：

```text
追问
拒绝
重试
降级
转人工
```

### 误区 3：所有错误都返回 200 更方便

不推荐。

所有错误都 200 会破坏 HTTP 语义。

监控、网关、日志、重试策略都难以判断真实状态。

### 误区 4：Java 返回 Entity 更省事

短期省事，长期危险。

Entity 可能包含敏感字段和内部字段。

AI 服务应该依赖稳定 DTO，不应该依赖数据库结构。

### 误区 5：Python 已经校验了，Java 不用再校验

不对。

Python 校验是第一层。

Java 是最终业务边界。

权限、业务规则、事务和幂等必须由 Java 兜底。

### 误区 6：用户确认和幂等是一回事

不对。

用户确认解决用户是否同意。

幂等解决重复提交是否重复写入。

### 误区 7：字段越多，模型越聪明

不对。

字段越多，泄露风险越高，噪声越多。

模型应该只看到完成回答所需的最小信息。

---

## 七、本节练习

### 练习 1：API 契约至少包含哪些内容？

参考答案：

```text
API 契约至少包含请求方法、URL、Path/Query 参数、Header、请求 Body、响应 Body、HTTP 状态码、业务错误码、字段类型、字段含义、鉴权、幂等、超时重试语义和兼容规则。
```

### 练习 2：为什么 Tool Calling 场景下契约更重要？

参考答案：

```text
因为 Java 接口返回会影响 Python client 解析、Pydantic 校验、Agent 下一步决策、模型总结、eval 判断和日志排查。字段或错误码不稳定时，系统可能不立刻崩溃，但 AI 行为会变得不可控。
```

### 练习 3：为什么订单查询接口使用 `GET /internal/orders/{order_id}`？

参考答案：

```text
因为查询单个订单是典型资源读取，order_id 用来定位订单资源，适合放在 path 中。加 internal 表示这是 Python AI 服务调用 Java 后端的内部接口，不是普通用户直接访问的公开接口。
```

### 练习 4：为什么创建工单必须有 `Idempotency-Key`？

参考答案：

```text
创建工单是写操作，可能因为网络超时、用户重复确认、模型重复调用或服务重试导致重复提交。Idempotency-Key 用来保证同一个创建请求重复执行时不会创建多个工单。
```

### 练习 5：`confirmation_id` 和 `Idempotency-Key` 有什么区别？

参考答案：

```text
confirmation_id 表示用户在 Python AI 服务侧确认过某个工具计划；Idempotency-Key 表示同一个写请求重复提交时要返回同一业务结果，防止重复写入。前者解决用户是否同意，后者解决重复提交。
```

### 练习 6：为什么用户身份更适合从 Header 来，而不是从模型生成的 body 来？

参考答案：

```text
用户身份属于认证上下文，必须来自可信认证链路，不能由模型或用户自然语言决定。如果让模型在 body 里填写 requester_id，可能导致越权、冒用身份或被 Prompt Injection 诱导。
```

### 练习 7：为什么不要把 Java Entity 直接返回给 Python AI 服务？

参考答案：

```text
Entity 面向数据库，可能包含内部字段、敏感字段和不稳定字段。AI 服务需要的是稳定、最小、面向工具调用的 DTO。直接返回 Entity 会让 AI 服务依赖数据库结构，并增加敏感信息泄露风险。
```

### 练习 8：`ORDER_NOT_FOUND` 和 `ORDER_ACCESS_DENIED` 为什么不能混成一个错误？

参考答案：

```text
因为它们对应不同的 Agent 行为。ORDER_NOT_FOUND 说明订单不存在或订单号错误，可以让用户检查订单号；ORDER_ACCESS_DENIED 说明用户无权查看，应该拒绝泄露信息。混在一起会让 AI 服务无法稳定决策。
```

---

## 八、自测问题

### 自测 1：本节最重要的学习目标是什么？

答案：

```text
把上一节的 AI Agent 和 Java 后端边界，落实成订单查询和创建工单两个真实接口的契约，包括路径、Header、Body、响应结构、错误码、字段白名单、幂等和鉴权。
```

### 自测 2：统一响应结构建议包含哪些字段？

答案：

```text
建议包含 success、code、message、data、trace_id。success 表示业务是否成功，code 是机器可读业务码，message 是简短说明，data 是业务数据，trace_id 用于链路排查。
```

### 自测 3：订单查询成功响应中，哪些字段适合返回给 AI 服务？

答案：

```text
适合返回 order_id、order_status、payment_status、logistics_message、latest_event、can_create_ticket、user_visible_summary。这些字段足够支撑模型回答订单状态，又不会暴露过多内部数据。
```

### 自测 4：创建工单请求 body 为什么不建议传 requester_id？

答案：

```text
因为 requester_id 表示用户身份，应该来自认证上下文或 X-User-Id 这类可信 Header，不应该由模型生成或由请求 body 随便传入。
```

### 自测 5：HTTP 状态码和业务错误码怎么分工？

答案：

```text
HTTP 状态码表达协议层大类，例如 404、403、422、503；业务错误码表达具体业务原因，例如 ORDER_NOT_FOUND、ORDER_ACCESS_DENIED、ORDER_ID_INVALID、JAVA_SERVICE_UNAVAILABLE。
```

### 自测 6：字段白名单为什么比黑名单更适合 AI 场景？

答案：

```text
因为未来 Entity 或 DTO 可能新增字段，如果只靠黑名单，新增敏感字段可能被意外暴露。白名单只允许明确需要的字段流向 AI 服务和模型，更符合最小暴露原则。
```

### 自测 7：下一节应该学什么？

答案：

```text
下一节应该学习真实 Spring Boot 服务骨架和领域模型，把本节接口契约落到 Java 项目结构、包结构、Controller、DTO、Service 和领域对象上。
```

---

## 九、本节总结

这一节把阶段 7 的边界思想落到了 API 契约上。

你要记住：

```text
Tool Calling 的 Java API 契约不是普通 CRUD 接口说明。
```

它必须同时服务：

```text
Java 后端实现
Python client 调用
Pydantic 结构校验
Agent 下一步决策
模型安全总结
eval 稳定评测
日志追踪和问题排查
```

本项目后续真实化时，两个核心接口先按这个方向设计：

```text
GET /internal/orders/{order_id}
POST /internal/tickets
```

最关键的契约元素是：

```text
统一响应结构
机器可读错误码
稳定 DTO
Header 上下文
字段白名单
写操作幂等
内部鉴权
trace_id
```

后续写 Spring Boot 时，不是先随手写接口，而是照着这份契约实现。

下一节进入：

```text
阶段 7 第 3 节：真实 Spring Boot 服务骨架和领域模型
```

下一节会开始进入代码层面，但仍然不会把重点放在 Spring Boot 入门，而是关注：

```text
如何让 Java 项目结构承接 AI 工具契约
如何设计 internal Controller
如何拆 Request DTO / Response DTO / Domain Model / Entity
如何为 MySQL 和 Redis 的后续接入留好位置
```
