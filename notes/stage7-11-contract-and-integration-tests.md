# 阶段 7 第 11 节：契约测试和集成测试

## 本节定位

前面几节我们已经把真实 Java business service 的关键边界做出来了：

```text
第 7.5 节：Java 服务结构传统化重构 + MyBatis
第 8 节：AI 场景下的内部鉴权和用户身份传递
第 9 节：Java 错误码到 AI 用户回答
第 10 节：trace_id 串联 Python + Java
```

现在的问题是：

```text
这些边界以后怎么不被改坏？
```

真实项目里，Python 和 Java 一旦开始互相调用，就会出现一种很常见的问题：

```text
Java 改了字段名，Python 没发现。
Java 改了错误码，Python 映射层没更新。
Java 改了 HTTP 状态码，Python 重试/降级逻辑变错。
Java 忘了返回 X-Trace-Id，Python 日志串不起来。
Java 新增 required header，Python 没带。
Python 改了请求 body，Java validation 开始失败。
```

这类问题不一定是某个函数内部 bug。

它们本质上是：

```text
接口契约被破坏。
```

所以本节要学：

```text
如何用契约测试和集成测试，保护 Python AI 服务与 Java 业务服务之间的边界。
```

## 本节学习目标

学完本节，你应该能讲清楚：

```text
1. 单元测试、契约测试、集成测试分别是什么。
2. 为什么 Python + Java 项目必须有契约测试。
3. 契约测试应该锁住哪些东西。
4. 为什么不能只靠真实集成测试。
5. 为什么自动化测试里不能真实调用大模型。
6. provider 契约测试和 consumer 契约测试分别验证什么。
7. 共享契约用例文件有什么价值。
8. 手动真实联调清单和自动化测试的边界在哪里。
```

本节代码目标：

```text
新增共享契约用例文件：
contracts/java-business-service/internal-api-contract-cases.json

新增 Python consumer 契约模型：
projects/ai-service/app/services/java_business_contract.py

新增 Python consumer 契约测试：
projects/ai-service/tests/test_java_business_contract.py

新增 Java provider 契约测试：
projects/java-business-service/src/test/java/com/panpan/aibusinessservice/InternalApiContractTest.java
```

本节不做：

```text
完整 Pact 合约测试平台
CI 矩阵流水线
真实 Java 服务进程自动拉起
真实 MySQL 集成环境自动编排
真实 LLM 调用
大规模端到端测试平台
```

这些以后可以继续补。本节先建立最小但清晰的测试分层。

## 基础知识铺垫

### 1. 什么是单元测试

单元测试关注的是：

```text
一个很小的代码单元是否按预期工作。
```

比如 Python 里：

```text
build_java_error_app_exception()
```

它接收一个模拟的 Java 响应，然后返回一个 `AppException`。

我们可以测试：

```text
ORDER_NOT_FOUND -> ORDER_NOT_FOUND
INTERNAL_AUTH_FAILED -> TOOL_UPSTREAM_ERROR
IDEMPOTENCY_KEY_REQUIRED -> TICKET_UPSTREAM_REJECTED
```

这里不需要真的启动 Java。

因为我们测的是：

```text
Python 的错误映射函数
```

不是：

```text
Java 服务是否真的返回这些错误
```

Java 里也一样。

比如：

```text
TicketServiceImpl 处理幂等键冲突
InternalRequestResolver 校验 header
RedisToolRateLimiter 限流
```

这些都可以用单元测试或较轻的 Spring 测试验证。

单元测试的优点：

```text
快
稳定
定位明确
不依赖外部服务
```

缺点：

```text
它不能证明两个服务真的对得上。
```

### 2. 什么是集成测试

集成测试关注的是：

```text
多个组件放在一起是否能协作。
```

比如：

```text
Python service -> Java service -> MySQL
```

或者：

```text
Spring MVC Controller -> Service -> MyBatis -> H2/MySQL
```

集成测试能发现单元测试发现不了的问题：

```text
路径写错
header 没带
JSON 字段名不一致
数据库 SQL 不兼容
Spring validation 行为和预期不同
HTTP 状态码不对
```

但集成测试也有缺点：

```text
慢
环境依赖多
失败原因可能不清晰
维护成本高
```

所以集成测试不能无限堆。

它应该覆盖：

```text
关键链路
关键边界
高风险行为
```

而不是把所有小分支都用真实环境跑一遍。

### 3. 什么是契约测试

契约测试关注的是：

```text
服务之间约定好的接口规则有没有被破坏。
```

对我们这个项目来说，契约包括：

```text
路径
HTTP 方法
必填 header
请求 body 字段
HTTP 状态码
统一响应结构
data 字段
错误码
trace_id
Python 如何解释 Java 错误码
```

例如，订单查询成功契约是：

```text
GET /internal/orders/A1001
必带 X-Trace-Id / X-Caller / X-User-Id / X-Tenant-Id / X-Internal-Token
HTTP 200
success=true
code=OK
data.order_id 存在
data.order_status 存在
data.payment_status 存在
trace_id 和请求 trace_id 一致
```

如果 Java 某天把字段改成：

```text
data.orderNo
```

Python 仍然期待：

```text
data.order_id
```

那契约就破坏了。

契约测试的目标就是提前发现这种问题。

### 4. provider 和 consumer

在接口契约里，经常会有两个角色：

```text
provider：提供接口的一方
consumer：调用接口的一方
```

在本项目里：

```text
Java business service 是 provider。
Python AI service 是 consumer。
```

Java provider 要证明：

```text
我真的按照契约返回这些路径、状态码、字段、错误码、trace_id。
```

Python consumer 要证明：

```text
我能理解这份契约。
我知道哪些字段必须存在。
我知道 Java 错误码应该如何映射。
```

这两个方向缺一不可。

只测 Java 不够。

因为 Java 可能符合契约，但 Python 没按契约解析。

只测 Python 也不够。

因为 Python 可能能解析理想样例，但真实 Java 返回并不是那个样子。

### 5. 为什么不能只靠集成测试

你可能会问：

```text
既然最终要 Python 调 Java，那直接写真实集成测试不就行了吗？
```

真实集成测试有价值，但不能只靠它。

原因有四个。

第一，真实集成测试慢。

它可能需要：

```text
启动 Java 服务
启动 MySQL
初始化数据
配置 Redis
启动 Python 服务
发 HTTP 请求
清理数据
```

第二，真实集成测试容易受环境影响。

比如：

```text
MySQL 没启动
端口被占用
Redis 没开
本地密码不一样
服务还没启动完成
```

第三，失败定位不一定清晰。

一次集成测试失败，可能是：

```text
Python 请求错了
Java validation 变了
数据库数据没初始化
Redis 限流
网络连接失败
```

第四，真实集成测试不适合覆盖所有分支。

比如错误码映射有十几个分支，用真实服务构造每个错误很麻烦。

所以更好的分层是：

```text
单元测试：覆盖细分逻辑
契约测试：锁住跨服务接口规则
少量集成测试：验证真实链路能跑通
手动清单：验证本地真实环境和演示路径
```

### 6. 为什么自动化测试里不能真实调用大模型

AI 项目很容易犯一个错误：

```text
把真实大模型调用放进自动化测试。
```

这通常不是好做法。

原因是：

```text
大模型输出不稳定
调用有成本
调用可能超时
API key 有泄露风险
网络环境会影响结果
模型版本可能变化
测试失败不好定位
```

自动化测试应该尽量：

```text
稳定
可重复
低成本
不依赖外部账号
不依赖真实模型概率输出
```

所以我们在测试里通常用：

```text
fake LLM
mock transport
固定响应
依赖注入
Pydantic 校验
```

真实模型可以放在：

```text
手动 smoke
演示脚本
专门的评测任务
非默认 CI job
```

### 7. 契约测试应该锁住什么

对 Python 调 Java 来说，至少要锁住：

```text
HTTP method
path
required headers
request body
HTTP status
success/code/message/data/trace_id 响应包结构
data 必填字段
错误码
Python 错误映射结果
trace_id 响应头和响应体
```

比如订单查询成功必须锁：

```text
GET /internal/orders/A1001
HTTP 200
code=OK
data.order_id
data.order_status
data.payment_status
data.logistics_message
data.latest_event
data.can_create_ticket
data.user_visible_summary
trace_id
```

工单创建成功必须锁：

```text
POST /internal/tickets
Idempotency-Key 必填
HTTP 201
code=OK
data.ticket_id
data.ticket_status
data.title
data.category
data.priority
data.related_order_id
data.created_at
data.user_visible_summary
```

错误也要锁：

```text
ORDER_ACCESS_DENIED -> HTTP 403
IDEMPOTENCY_KEY_REQUIRED -> HTTP 400
INTERNAL_AUTH_FAILED -> HTTP 401
```

而 Python 侧还要锁：

```text
ORDER_ACCESS_DENIED -> Python AppException ORDER_ACCESS_DENIED
IDEMPOTENCY_KEY_REQUIRED -> Python AppException TICKET_UPSTREAM_REJECTED
```

### 8. 契约文件为什么有价值

本节新增：

```text
contracts/java-business-service/internal-api-contract-cases.json
```

它的价值不是“多一个 JSON 文件”。

它的价值是：

```text
把 Python 和 Java 都要遵守的接口规则放到一个共同位置。
```

这样：

```text
Java provider 测试读取它。
Python consumer 测试也读取它。
文档也可以引用它。
```

如果将来要加一个错误码：

```text
ORDER_NOT_SUPPORT_TICKET
```

就可以先改契约用例，再让 Python 和 Java 测试一起推动实现。

这就比“散落在各自测试里的魔法字符串”更好。

## 本节主题系统讲解

### 1. 本节发现的真实问题

这节梳理时，我们发现一个很真实的历史包袱：

```text
Python JavaOrderClient / JavaTicketClient 还保留了早期 java-mock-service 的风格。
真实 Java business service 已经使用 /internal/orders 和 /internal/tickets。
真实 Java business service 还有统一响应包 success/code/message/data/trace_id。
```

这就是为什么契约测试重要。

如果没有契约测试，我们可能会以为：

```text
Python 已经能调用 Java。
```

但实际上要问清楚：

```text
调用的是早期 mock service 契约？
还是真实 Java business service 契约？
```

本节没有暴力改掉所有旧 mock 链路。

原因是：

```text
旧 mock service 仍然是前面学习阶段的历史链路。
直接改动会牵动很多旧测试和 Agent 工具。
```

本节更稳的做法是：

```text
先建立真实 Java business service 的契约测试入口。
把真实契约固定下来。
后续要切换 Python 运行链路时，有明确契约可以对照。
```

这也是工程里的常见做法：

```text
先锁契约，再迁移调用方。
```

### 2. 新增共享契约文件

新增：

```text
contracts/java-business-service/internal-api-contract-cases.json
```

里面定义了四个核心用例：

```text
query_order_success
query_order_access_denied
create_ticket_success
create_ticket_missing_idempotency_key
```

它包含：

```text
公共 header
请求 method
请求 path
请求 body
幂等键
期望 HTTP status
期望 success
期望 code
期望 data 字段
Python 侧期望错误映射
```

这四个用例不是全部情况，但能覆盖最重要的契约边界：

```text
读成功
读权限失败
写成功
写契约失败
```

### 3. Java provider 契约测试

新增：

```text
projects/java-business-service/src/test/java/com/panpan/aibusinessservice/InternalApiContractTest.java
```

它读取共享契约文件，然后用 MockMvc 调真实 Spring MVC 链路。

例如订单成功：

```text
读取 query_order_success
-> GET /internal/orders/A1001
-> 带公共 header
-> 断言 HTTP 200
-> 断言 X-Trace-Id
-> 断言 success=true
-> 断言 code=OK
-> 断言 data.order_id 等字段存在
```

这证明：

```text
Java provider 当前实现符合共享契约。
```

它不是单纯测 Controller 某个函数。

它是在测：

```text
Java 对外 internal API 形状没有变。
```

### 4. Python consumer 契约测试

新增：

```text
projects/ai-service/tests/test_java_business_contract.py
```

它也读取同一个共享契约文件。

Python 侧主要验证：

```text
Python 知道有哪些核心契约案例。
Python 的 Pydantic 模型能接受 Java 成功响应包。
Python 的错误映射能符合共享契约。
Python 会拒绝缺少关键 data 字段的 Java 成功响应。
```

这证明：

```text
Python consumer 能理解这份真实 Java business contract。
```

### 5. Python 契约模型

新增：

```text
projects/ai-service/app/services/java_business_contract.py
```

里面有：

```text
JavaApiEnvelope
JavaOrderToolView
JavaTicketToolView
validate_java_success_envelope()
```

`JavaApiEnvelope` 锁住统一响应包：

```text
success
code
message
data
trace_id
```

`JavaOrderToolView` 锁住订单工具视图：

```text
order_id
order_status
payment_status
logistics_message
latest_event
can_create_ticket
user_visible_summary
```

`JavaTicketToolView` 锁住工单工具视图：

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

`validate_java_success_envelope()` 做三件事：

```text
1. 校验 Java 是否返回统一响应包。
2. 校验 success=true 且 code=OK。
3. 校验 data 是否符合对应工具视图模型。
```

如果不符合，抛出：

```text
JAVA_CONTRACT_VALIDATION_FAILED
```

这就是 consumer 侧的契约防线。

### 6. 为什么不直接把旧 Python client 全部改掉

这节没有直接大范围改：

```text
JavaOrderClient
JavaTicketClient
fake_order_tool
ticket workflow
大量旧测试
```

原因是：

```text
这会把“契约测试”这节变成“大规模迁移调用链路”。
```

学习上会变散。

工程上也更容易引入额外风险。

更好的顺序是：

```text
第 11 节：先把真实 Java 契约固定下来。
第 12 节：阶段整理时说明当前 mock 链路和真实 Java 契约的边界。
后续新阶段：再正式把 Python 运行链路从 mock service 切到 java-business-service。
```

这不是逃避问题。

这是工程迁移时常用的风险控制：

```text
先建立保护网，再改运行链路。
```

### 7. 手动集成测试放在哪里

本节新增手动清单：

```text
notes/stage7-11-contract-and-integration-tests-manual-tasks.md
```

里面放真实联调步骤：

```text
启动 Java service
Windows MySQL 准备
Redis 关闭
curl 订单查询
curl 工单创建
检查 X-Trace-Id
检查 code/status/data 字段
```

为什么不全部自动化？

因为你当前本地环境涉及：

```text
Windows MySQL 密码
端口
服务启动状态
历史数据
PowerShell curl 转义
```

这些更适合先做手动 smoke。

等后面要做 CI 或 Docker Compose 一键启动时，再把它自动化。

## 本节代码讲解

### 1. 共享契约文件

文件：

```text
contracts/java-business-service/internal-api-contract-cases.json
```

它不是业务代码，但它是非常重要的工程资产。

里面的 `common_headers`：

```json
{
  "X-Trace-Id": "trace-contract-stage7-11",
  "X-Caller": "ai-service",
  "X-User-Id": "U1001",
  "X-Tenant-Id": "default",
  "X-Internal-Token": "local-dev-internal-token"
}
```

这明确了真实 Java internal API 的最小必备 header。

里面的 `cases` 列表表示核心契约用例。

比如：

```text
query_order_success
```

锁住：

```text
GET /internal/orders/A1001
HTTP 200
success=true
code=OK
data 必须有订单工具字段
```

再比如：

```text
create_ticket_missing_idempotency_key
```

锁住：

```text
POST /internal/tickets
缺少 Idempotency-Key
HTTP 400
code=IDEMPOTENCY_KEY_REQUIRED
Python 映射成 TICKET_UPSTREAM_REJECTED
```

### 2. `JavaApiEnvelope`

Python 新增：

```python
class JavaApiEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    code: str
    message: str
    data: dict[str, Any] | None
    trace_id: str
```

它的作用是：

```text
锁住 Java 统一响应包。
```

`extra="forbid"` 表示：

```text
Java 如果多返回了 Python 没约定的顶层字段，Python 会认为契约不匹配。
```

这在工具接口里很重要。

因为给模型或 Agent 的字段越多，越可能泄露不该看的信息。

### 3. `JavaOrderToolView`

Python 新增：

```python
class JavaOrderToolView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    order_status: str
    payment_status: str
    logistics_message: str
    latest_event: str
    can_create_ticket: bool
    user_visible_summary: str
```

它对应 Java 的：

```text
OrderToolView
```

这层模型不是 Entity。

它是：

```text
工具视图
```

也就是 Python AI 服务真正需要看到的最小字段。

### 4. `JavaTicketToolView`

Python 新增：

```python
class JavaTicketToolView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticket_id: str = Field(pattern=r"^T-[0-9a-fA-F-]{36}$")
    ticket_status: str
    title: str
    category: str
    priority: str
    related_order_id: str | None
    created_at: datetime
    user_visible_summary: str
```

注意这里的 `ticket_id` 规则：

```text
T-UUID
```

这是现在 Java business service 的真实生成方式。

这也暴露出一个学习重点：

```text
早期 mock service 的 ticket_id 可能是 T1001。
真实 Java business service 的 ticket_id 是 T-UUID。
```

如果 Python 还按旧规则 `T\d{4}` 校验，未来接真实 Java 时一定会失败。

这就是契约测试的价值。

### 5. `validate_java_success_envelope()`

核心逻辑：

```python
envelope = JavaApiEnvelope.model_validate(payload)
if envelope.success is not True or envelope.code != "OK":
    raise ValueError(...)
if envelope.data is None:
    raise ValueError(...)
return data_model.model_validate(envelope.data)
```

它负责把 Java 成功响应分成两层校验：

```text
先校验统一 envelope
再校验 data 业务视图
```

这样错误定位更清楚：

```text
是统一响应包不对？
还是 data 字段不对？
```

### 6. `InternalApiContractTest`

Java 新增：

```text
InternalApiContractTest
```

它从共享 JSON 读取用例：

```java
objectMapper.readTree(CONTRACT_PATH.toFile())
```

然后通过 MockMvc 请求真实 Controller：

```java
mockMvc.perform(withContractHeaders(get(item.path("path").asText())))
```

这样它不是写死一堆散落常量，而是对照共享契约。

如果契约变了，Java 测试会立刻反映。

### 7. Python `test_java_business_contract.py`

Python 测试覆盖：

```text
共享契约核心 case 存在
订单成功 envelope 能被 Python 接受
工单成功 envelope 能被 Python 接受
Java 错误码映射符合共享契约
缺少 data 字段会被 Python 拒绝
```

这说明 Python 不是被动等真实联调才发现问题。

它自己也有 consumer 防线。

## 常见误区

### 误区 1：有单元测试就不需要契约测试

不对。

单元测试可以证明：

```text
某个函数本身没问题。
```

但不能证明：

```text
Python 和 Java 对同一份 HTTP 契约理解一致。
```

### 误区 2：有集成测试就不需要契约测试

也不对。

集成测试能证明真实链路能跑，但它慢、重、环境依赖多。

契约测试更轻，能更快发现接口形状变化。

### 误区 3：契约测试就是测返回 200

不是。

契约测试要测：

```text
路径
方法
header
状态码
响应包结构
data 字段
错误码
trace_id
错误映射
```

只测 200 太浅。

### 误区 4：测试越真实越好

不一定。

测试要分层。

有些逻辑用 mock 更好：

```text
错误码映射
Pydantic 字段校验
LLM 输出解析
```

有些逻辑才适合真实集成：

```text
Python 真能连 Java
Java 真能连 MySQL
trace_id 真实跨服务传递
```

### 误区 5：大模型也应该进入集成测试

默认不应该。

真实模型调用适合：

```text
手动验证
离线评测
专门的模型评测任务
```

不适合普通自动化测试。

## 本节练习

### 练习 1：区分三类测试

请说明单元测试、契约测试、集成测试分别关注什么。

参考答案：

```text
单元测试：关注一个函数、类或小模块内部逻辑是否正确。
契约测试：关注服务之间约定的接口规则是否被破坏。
集成测试：关注多个真实组件放在一起是否能协作运行。
```

### 练习 2：为什么 Python 和 Java 都要读同一份契约文件

参考答案：

```text
因为 Java 是 provider，要证明自己按契约提供接口；Python 是 consumer，要证明自己能理解和消费这份契约。
两边读同一份契约文件，可以减少魔法字符串散落，避免两边测试各测各的。
```

### 练习 3：哪些内容应该进入契约测试

下面哪些应该进入契约测试？

```text
HTTP path
HTTP method
必填 header
响应字段
错误码
用户头像 UI 是否好看
真实大模型回答是否优美
trace_id
```

参考答案：

```text
应该进入：
HTTP path
HTTP method
必填 header
响应字段
错误码
trace_id

不适合进入这类接口契约测试：
用户头像 UI 是否好看
真实大模型回答是否优美
```

### 练习 4：为什么真实 LLM 不放进默认自动化测试

参考答案：

```text
因为真实 LLM 输出不稳定、有成本、依赖网络和 API key、可能超时、模型版本可能变化。
默认自动化测试应该稳定、可重复、低成本。
真实 LLM 更适合手动 smoke、离线评测或单独的非默认评测任务。
```

### 练习 5：这节为什么没有直接把所有 Python client 切到真实 Java

参考答案：

```text
因为当前项目还保留了早期 java-mock-service 学习链路，直接切换会牵动大量旧测试和 Agent 代码。
本节重点是先建立真实 Java business service 的契约保护网。
更稳的迁移顺序是先锁契约，再逐步切运行链路。
```

## 自测题

### 自测 1：provider 契约测试验证什么？

参考答案：

```text
验证接口提供方是否真的按契约返回路径、状态码、响应结构、字段、错误码和 trace_id。
在本项目里，Java business service 是 provider。
```

### 自测 2：consumer 契约测试验证什么？

参考答案：

```text
验证接口调用方是否能理解契约，包括能解析成功响应、能识别关键字段、能正确映射错误码。
在本项目里，Python AI service 是 consumer。
```

### 自测 3：为什么契约测试不能只测成功？

参考答案：

```text
因为真实系统里很多跨服务问题发生在失败场景，比如权限不足、缺少幂等键、鉴权失败、字段校验失败。
如果只测成功，错误码、HTTP status 和安全提示映射很容易被改坏。
```

### 自测 4：`JAVA_CONTRACT_VALIDATION_FAILED` 表示什么？

参考答案：

```text
表示 Java 成功响应没有满足 Python AI 服务期待的契约。
例如缺少 data 字段、data 缺少 order_status、统一响应包结构不对等。
```

### 自测 5：手动集成验证和自动化契约测试是什么关系？

参考答案：

```text
自动化契约测试用于快速、稳定地锁住接口规则。
手动集成验证用于确认本地真实服务、MySQL、端口、环境变量和 curl 链路真的能跑通。
两者互补，不是谁替代谁。
```

## 本节总结

本节把 Python + Java 的测试边界从“各自测试”推进到“共享契约驱动”。

现在我们有了：

```text
共享契约用例文件
Java provider 契约测试
Python consumer 契约测试
手动真实集成验证清单
```

本节最重要的思想是：

```text
跨服务问题不是只靠单元测试能解决的。
真实集成测试也不能无限堆。
契约测试负责锁接口规则。
集成测试负责验证真实组件协作。
真实大模型不进入默认自动化测试。
```

下一节进入：

```text
阶段 7 第 12 节：阶段 7 项目整理
```

那一节会整理：

```text
阶段 7 到底完成了什么。
哪些是真实 Java business service 已落地。
哪些仍是历史 mock 链路。
后续如果要切真实 Python -> Java business service，应该怎么继续。
```
