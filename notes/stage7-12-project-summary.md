# 阶段 7 第 12 节：阶段 7 项目整理

## 本节定位

这一节是阶段 7 的收尾课。

阶段 7 的主题是：

```text
真实 Java Spring Boot + MySQL/Redis 业务服务如何接入 Python AI Agent
```

前面几节我们不是在重复传统 Spring Boot CRUD，而是在学习一个传统 Java 后端开发者进入 AI 应用工程后必须补齐的新边界：

```text
AI 不能直接操作业务系统。
模型只能提出意图。
真正的业务执行必须交给后端。
后端必须用接口契约、权限、幂等、错误码、trace_id 和测试体系兜住不确定性。
```

这一节要做的是把阶段 7 整体串起来，让你能回答下面几个问题：

```text
1. 阶段 7 到底学了什么？
2. 当前 Java 服务和早期 java-mock-service 有什么区别？
3. Python AI 服务调用 Java 业务服务时多了哪些工程边界？
4. 当前项目已经真实化到什么程度？
5. 哪些能力已经可以放进简历和面试表达？
6. 后续继续学习应该往哪里走？
```

## 本节学习目标

学完本节后，你应该能说清楚：

```text
阶段 7 的主线不是 Spring Boot 基础，而是 AI Agent 与真实 Java 后端的边界设计。
真实 Java 服务已经有 Spring Boot、MyBatis、MySQL、Redis、internal API、错误码、trace_id 和契约测试。
Python AI 服务不能相信模型输出，也不能直接相信 Java 响应，必须做参数校验、错误映射和响应契约校验。
Java 业务服务不能相信 Python 请求，更不能相信模型意图，必须做内部鉴权、用户身份传递、权限校验、事务、幂等和限流。
阶段 7 完成的是真实业务服务接入 AI Agent 的底座，不是完整生产系统。
```

## 本节不做什么

这一节不新增大块业务代码。

不做：

```text
不新增新的订单业务接口。
不新增新的工单业务流程。
不把 Python 运行时链路一次性切到 java-business-service。
不改 Java README。
不做敏感信息扫描。
不提交 GitHub。
不启动真实 MySQL/Redis。
```

原因很简单：

```text
阶段整理课的重点是收口和建立认知地图。
如果在收尾课里继续大改业务代码，很容易把阶段总结和新功能开发混在一起。
```

## 基础知识铺垫

### 1. 为什么阶段 7 不是普通 Java CRUD 阶段

你有传统 Java 后端基础，所以如果只是做：

```text
controller
service
mapper
entity
dto
MyBatis XML
MySQL 表
Redis 缓存
```

这些本身不是阶段 7 最难的地方。

阶段 7 真正新增的是：

```text
传统后端如何被 AI Agent 安全调用
```

以前普通系统里，调用方通常是：

```text
前端页面
移动端 App
另一个后端服务
定时任务
```

这些调用方虽然也可能传错参数，但它们的行为通常由开发者写死，变化相对可控。

AI Agent 场景里，调用前面多了一层模型：

```text
用户自然语言
-> 模型理解意图
-> 模型可能提出工具调用
-> Python AI 服务校验
-> Java 业务服务执行
```

模型有几个特点：

```text
它可能理解错用户意思。
它可能提取错参数。
它可能缺少必要字段。
它可能把不该调用的工具也当成可以调用。
它可能在错误发生后编造一个看似合理的解释。
```

所以阶段 7 的重点不是“会不会写 Spring Boot 接口”，而是：

```text
如何让传统 Java 接口变成 AI 可调用、可验证、可追踪、可兜底的业务工具接口。
```

### 2. AI Agent 接入 Java 后端后，系统边界发生了什么变化

传统后端接口常见边界是：

```text
前端传请求
后端校验参数
service 执行业务
mapper 访问数据库
返回结果
```

AI Agent 接入后，边界变成：

```text
用户表达真实需求
模型把自然语言变成结构化意图
Python AI 服务把意图变成工具调用请求
Java 服务把工具调用请求变成真实业务动作
数据库和 Redis 保存业务结果
Python 再把工具结果交给模型或模板生成用户回答
```

这条链路里每一层都有自己的职责。

不能混：

```text
模型不能负责权限。
模型不能负责事务。
模型不能负责幂等。
模型不能负责数据库写入。
模型不能决定哪些字段可以暴露给自己。
```

也不能让 Java 后端把所有 AI 细节都接过去：

```text
Java 不负责 prompt。
Java 不负责多轮对话状态。
Java 不负责 RAG 检索上下文。
Java 不负责模型输出解析。
Java 不负责 Agent 图编排。
```

更合理的分工是：

| 层 | 负责什么 |
| --- | --- |
| 用户 | 提出自然语言需求 |
| 模型 | 理解意图、生成自然语言回答、提出可能的工具调用 |
| Python AI 服务 | 管理 prompt、RAG、Tool Calling、LangGraph、结构化校验、模型输出兜底 |
| Java 业务服务 | 负责真实业务规则、权限、事务、MySQL、Redis、审计、机器错误码 |
| 测试和契约 | 锁住跨服务边界，防止两边各改各的 |

### 3. 为什么 Java API 要专门面向 Tool Calling 设计

普通给前端用的接口，不一定适合直接给 AI 工具用。

比如前端订单详情接口可能返回：

```text
收货人姓名
手机号
详细地址
支付流水号
优惠券信息
内部备注
售后记录
页面展示字段
按钮状态
```

但 AI 查询订单时，可能只需要：

```text
订单号
订单状态
支付状态
物流摘要
最新事件
是否可以创建工单
用户可见摘要
```

如果把前端详情接口直接给模型，会有几个风险：

```text
模型看到过多敏感字段。
模型可能把内部字段说给用户。
接口变更会影响 AI 工具调用。
前端展示字段和 AI 工具字段混在一起。
AI 回答所需字段不稳定。
```

所以阶段 7 设计了 AI 工具专用 internal API：

```text
GET /internal/orders/{order_id}
POST /internal/tickets
```

它们不是普通开放接口，而是：

```text
只给内部 ai-service 调用。
必须带 internal token。
必须带真实用户身份。
必须带租户。
必须带 trace_id。
写操作必须带 Idempotency-Key。
只返回模型需要知道的白名单字段。
```

### 4. 为什么错误码比错误文案更重要

AI 应用里，错误不能只靠一句 message。

比如 Java 返回：

```json
{
  "success": false,
  "message": "当前用户无权查看或操作该订单。"
}
```

Python 能给用户展示这句话，但程序很难稳定判断：

```text
这是权限问题？
这是订单不存在？
这是系统异常？
这是内部鉴权失败？
这是幂等键问题？
```

所以 Java 必须返回机器可读错误码：

```json
{
  "success": false,
  "code": "ORDER_ACCESS_DENIED",
  "message": "当前用户无权查看或操作该订单。",
  "data": null,
  "trace_id": "trace-xxx"
}
```

Python AI 服务再把它映射成自己的 `AppException`：

```text
ORDER_ACCESS_DENIED
-> 可以安全告诉用户无权查看

INTERNAL_AUTH_FAILED
-> 不能告诉用户内部鉴权细节
-> 映射为 TOOL_UPSTREAM_ERROR

IDEMPOTENCY_KEY_REQUIRED
-> 用户不应该处理幂等键
-> 映射为 TICKET_UPSTREAM_REJECTED
```

这就是阶段 7 第 9 节的核心思想：

```text
Java code 是机器语义。
Java message 不等于最终用户话术。
Python AI 服务必须做安全映射。
模型不能自由解释 Java 内部错误。
```

### 5. 为什么 trace_id 在 AI 链路里更重要

普通后端系统排查问题时，通常看：

```text
请求日志
业务日志
数据库日志
异常堆栈
```

AI 系统多了几类问题：

```text
模型有没有理解错？
工具有没有被调用？
工具参数是什么？
Java 有没有收到请求？
Java 返回的错误码是什么？
模型最后有没有乱解释？
```

如果没有统一 trace_id，一次用户请求可能散落在：

```text
Python 入站请求日志
Python LLM 调用日志
Python 工具调用日志
Java Filter 日志
Java controller/service 日志
MySQL/Redis 操作
Python 最终回答日志
```

排查会非常困难。

所以阶段 7 第 10 节做了：

```text
Python 读或生成 X-Trace-Id。
Python 调 Java 时继续传 X-Trace-Id。
Java Filter 把 trace_id 写入 MDC。
Java 响应头返回 X-Trace-Id。
Java 响应体返回 trace_id。
Python client 记录 upstream_trace_id。
```

这让你以后可以说：

```text
我不是只会调用模型。
我知道 AI 工程里一条请求要从用户、模型、工具、Java 服务、数据库一路追踪。
```

### 6. 为什么契约测试是跨服务开发的关键

Python 和 Java 是两个服务。

只测 Python 自己，不知道 Java 有没有改坏。

只测 Java 自己，不知道 Python 能不能解析。

只靠手动 curl，不稳定，也容易忘。

所以阶段 7 第 11 节新增了共享契约：

```text
contracts/java-business-service/internal-api-contract-cases.json
```

Java provider 测试读取它：

```text
证明 Java 服务按契约提供接口。
```

Python consumer 测试读取它：

```text
证明 Python AI 服务能理解并消费接口。
```

这就是契约测试的价值：

```text
把“我们约定好了”变成“自动化测试能验证”。
```

## 本节主题系统讲解

### 1. 阶段 7 的完整学习主线

阶段 7 可以拆成 4 条线。

第一条线：设计边界。

```text
第 1 节：AI Agent 调用传统 Java 后端时的边界设计
第 2 节：面向 Tool Calling 的 Java API 契约设计
```

这一部分解决：

```text
AI 能做什么？
Java 后端必须做什么？
什么字段能给模型？
接口怎么设计才适合工具调用？
错误码、header、幂等、trace_id 应该怎么约定？
```

第二条线：真实 Java 服务落地。

```text
第 3 节：Spring Boot 服务骨架和领域模型
第 4 节：MySQL 业务数据模型
第 5 节：订单查询读工具真实化
第 6 节：创建工单写工具真实化
第 7 节：Redis 幂等、缓存和限流
第 7.5 节：传统三层结构 + MyBatis 重构
```

这一部分解决：

```text
Java 服务从内存 mock 走向真实 Spring Boot。
订单和工单数据进入 MySQL。
读接口有缓存。
写接口有事务和幂等。
工具接口有限流。
项目结构对齐传统 controller/service/mapper/entity/dto/config/exception/common 风格。
```

第三条线：AI 场景的安全和可排查边界。

```text
第 8 节：内部鉴权和用户身份传递
第 9 节：Java 错误码到 AI 用户回答
第 10 节：trace_id 串联 Python + Java
```

这一部分解决：

```text
Python 调 Java 时怎么证明自己是内部服务？
真实用户身份怎么传递？
租户边界怎么传？
模型为什么不能伪造用户身份？
Java 错误码怎么安全映射给用户？
跨服务问题怎么按 trace_id 排查？
```

第四条线：测试和阶段收口。

```text
第 11 节：契约测试和集成测试
第 12 节：阶段 7 项目整理
```

这一部分解决：

```text
Python 和 Java 的接口约定怎么被自动化测试锁住？
哪些测试应该稳定运行？
哪些测试适合手动验证？
阶段 7 到底完成了什么？
后续学习如何接着走？
```

### 2. 当前 Java business service 的状态

当前真实 Java 服务位置：

```text
projects/java-business-service
```

它已经不是早期那个 Python 写的 `java-mock-service`。

当前 Java 服务已经具备：

```text
Spring Boot 应用骨架
传统包结构
MyBatis Mapper + XML
MySQL 业务表
H2 测试配置
Redis 缓存、幂等和限流
internal API
统一响应结构
业务错误码
内部调用鉴权
真实用户身份和租户 header
trace_id Filter + MDC
MockMvc 测试
provider 契约测试
```

当前主要包结构包括：

```text
application
common
config
controller
domain
dto
entity
exception
infrastructure
interfaces
mapper
service
```

其中你最熟悉的传统结构是：

| 包 | 作用 |
| --- | --- |
| `controller` | HTTP 接口入口 |
| `service` / `service.impl` | 业务编排和事务边界 |
| `mapper` | MyBatis Mapper |
| `entity` | 数据库实体 |
| `dto` | 请求和响应对象 |
| `config` | 配置类 |
| `exception` | 全局异常和业务异常 |
| `common` | 通用响应、错误码、安全、trace 等基础能力 |

阶段 7 第 7.5 节专门做过传统结构重构，是为了让这个服务更贴近你以前的 Java 项目习惯。

### 3. 当前 Python AI service 的状态

Python AI 服务位置：

```text
projects/ai-service
```

阶段 7 主要新增或强化了这些 Java 相关能力：

```text
java_order_client.py
java_ticket_client.py
java_error_mapping.py
java_business_contract.py
```

它们的分工是：

| 文件 | 作用 |
| --- | --- |
| `java_order_client.py` | Python 调 Java 订单查询接口，并记录 upstream trace |
| `java_ticket_client.py` | Python 调 Java 创建工单接口，并处理幂等 header |
| `java_error_mapping.py` | 把 Java 错误码映射成 Python 安全 AppException |
| `java_business_contract.py` | 用 Pydantic 锁 Java 成功响应 envelope 和工具可见字段 |

要注意一个阶段 7 结束时的真实边界：

```text
Python 运行时主链路还保留了历史 java-mock-service 学习链路。
真实 Java business service 的契约和测试已经建立。
后续如果要把运行时链路彻底切换过去，应该以共享契约为准逐步迁移。
```

这不是失败，而是阶段化演进。

原因是：

```text
旧 java-mock-service 支撑了前面 Tool Calling、RAG、LangGraph、Agent eval 的大量学习和测试。
一次性切换会牵动很多历史测试和 Agent 节点。
更稳的方式是先建立真实 Java 服务，再建立契约，再逐步迁移运行链路。
```

### 4. 当前两个 Java 服务的关系

项目里现在有两个“Java 业务服务相关”的目录。

准确说：

```text
projects/java-mock-service
projects/java-business-service
```

它们的定位不同。

| 服务 | 定位 | 当前作用 |
| --- | --- | --- |
| `java-mock-service` | 早期学习用 mock 服务 | 支撑阶段 3 到阶段 6 的 Tool Calling 和 Agent 主线 |
| `java-business-service` | 阶段 7 新增真实 Java 业务服务 | 用 Spring Boot + MySQL/Redis/MyBatis 实现真实业务后端底座 |

不要混淆：

```text
java-mock-service 是学习早期的模拟业务服务。
java-business-service 是阶段 7 开始真实化的 Java 后端。
```

后续方向应该是：

```text
逐步让 Python AI 服务从 mock API 迁移到 java-business-service 的 internal API。
```

但这个迁移要谨慎，因为它会影响：

```text
工具调用接口
Agent 节点
错误处理
测试数据
评测样本
本地运行说明
CI 脚本
演示流程
```

### 5. 阶段 7 已经掌握的能力地图

阶段 7 学完后，你在“传统 Java 后端 + AI 应用工程”的交叉点上，已经覆盖了下面这些能力。

| 能力 | 当前掌握程度 |
| --- | --- |
| Java Spring Boot internal API | 已实践 |
| MyBatis + XML | 已实践 |
| MySQL 业务表设计 | 已实践 |
| Redis 缓存 | 已实践 |
| Redis 幂等缓存 | 已实践 |
| Redis 限流 | 已实践 |
| 事务和唯一约束兜底 | 已实践 |
| DTO 白名单 | 已实践 |
| Java 统一响应 | 已实践 |
| 机器错误码 | 已实践 |
| Python 错误映射 | 已实践 |
| internal token | 已实践 |
| caller 校验 | 已实践 |
| user_id / tenant_id 传递 | 已实践 |
| trace_id 跨服务传递 | 已实践 |
| Java MDC | 已实践 |
| Python upstream_trace_id 日志 | 已实践 |
| provider 契约测试 | 已实践 |
| consumer 契约测试 | 已实践 |
| 手动真实集成验证 | 已实践 |

这些能力比普通 CRUD 更贴近 AI 应用后端岗位需要。

因为真实工作里，企业不只是问你：

```text
你会不会调大模型？
```

更会问：

```text
模型要查订单，你怎么保证不越权？
模型要创建工单，你怎么保证不重复创建？
Java 返回内部错误，你怎么防止模型乱解释？
Python 和 Java 接口变更，你怎么发现？
用户投诉一单查错了，你怎么按 trace_id 排查？
```

阶段 7 就是在补这些问题。

### 6. 当前项目还没有完成的部分

阶段 7 完成后，项目比 M6 时真实了很多，但仍然不是完整生产系统。

还没有完全完成：

```text
Python Agent 运行时主链路完全切到 java-business-service。
真实用户表和登录认证。
完整 RBAC 或 ABAC 权限模型。
前端客服工作台。
生产部署、域名、HTTPS、Nginx。
集中日志采集和告警。
更完整的链路追踪平台。
压测和容量评估。
真实工单业务的复杂状态流转。
更多业务工具，比如退款、物流、售后、用户资料查询。
```

这里要形成一个成熟表达：

```text
阶段 7 完成的是真实 Java 业务服务接入 AI Agent 的核心底座。
它还不是完整生产客服系统。
但它已经覆盖了 AI 调用传统后端时最关键的安全、契约、幂等、错误和追踪边界。
```

### 7. 阶段 7 和你已有 Java 经验的关系

你有传统 Java 后端经验，这是优势。

阶段 7 不是让你重新学：

```text
Controller 怎么写
Service 怎么写
Mapper 怎么写
MyBatis XML 怎么写
application.yml 怎么配
```

阶段 7 是在你的原有能力上加一层：

```text
当调用方变成 AI Agent 时，传统后端要额外怎么设计。
```

可以这样理解：

```text
传统 Java 后端能力是地基。
AI Agent 调用边界是新加的门禁、审计、监控和契约层。
```

如果你未来面试 AI 应用后端岗位，传统 Java 经验会让你能负责：

```text
业务系统
权限
数据库
缓存
事务
稳定 API
```

阶段 7 补上的能力让你能进一步负责：

```text
AI 工具接口设计
模型输出安全兜底
跨服务错误映射
Human-in-the-loop 写操作保护
AI 调用链路 trace
契约测试和集成验证
```

这两部分合起来，才是更完整的 AI 应用后端能力。

### 8. 阶段 7 可以怎么对外表达

简历或面试可以这样讲：

```text
在原有 RAG 和 LangGraph 智能工单 Agent 基础上，我把早期 mock 业务接口逐步升级为真实 Spring Boot 业务服务。
Java 侧使用 MyBatis + MySQL 实现订单查询和工单创建，使用 Redis 支持订单缓存、工单幂等和工具限流。
为了让 AI Agent 安全调用业务系统，我设计了 internal API 契约、internal token、caller/user/tenant header、DTO 白名单、机器错误码、Python 错误映射、trace_id 跨服务追踪和共享契约测试。
这个阶段重点不是普通 CRUD，而是 AI 调用传统 Java 后端时的权限、幂等、契约、错误处理和可观测性边界。
```

如果面试官追问“为什么不让模型直接调用数据库”，可以回答：

```text
模型输出不稳定，不能承担权限、事务和幂等职责。
真实业务写操作必须由 Java 后端控制，模型最多提出工具意图。
Python AI 服务负责校验和编排，Java 服务负责真实业务规则、权限、事务、MySQL/Redis 和审计。
```

如果面试官追问“你怎么保证 Python 和 Java 接口不改坏”，可以回答：

```text
我用共享 JSON 契约文件描述关键接口场景。
Java provider 契约测试读取这份文件，验证状态码、错误码、响应字段和 trace_id。
Python consumer 契约测试也读取同一份文件，验证自己能解析成功响应，并能把 Java 错误码映射成安全 AppException。
这样两边不是各测各的，而是围绕同一份契约验证。
```

## 本节项目整理结果

### 1. 阶段 7 笔记入口

阶段 7 已形成下面这些笔记：

| 节 | 主题 |
| --- | --- |
| 1 | AI Agent 调用传统 Java 后端时的边界设计 |
| 2 | 面向 Tool Calling 的 Java API 契约设计 |
| 3 | 真实 Spring Boot 服务骨架和领域模型 |
| 4 | MySQL 业务数据模型 |
| 5 | 查询订单读工具真实化 |
| 6 | 创建工单写工具真实化 |
| 7 | Redis 幂等、缓存和限流 |
| 7.5 | Java 服务结构传统化重构 + MyBatis |
| 8 | AI 场景下的内部鉴权和用户身份传递 |
| 9 | Java 错误码到 AI 用户回答 |
| 10 | trace_id 串联 Python + Java |
| 11 | 契约测试和集成测试 |
| 12 | 阶段 7 项目整理 |

### 2. 阶段 7 代码入口

核心入口：

```text
projects/java-business-service
projects/ai-service/app/services/java_order_client.py
projects/ai-service/app/services/java_ticket_client.py
projects/ai-service/app/services/java_error_mapping.py
projects/ai-service/app/services/java_business_contract.py
contracts/java-business-service/internal-api-contract-cases.json
```

Java 测试入口：

```text
projects/java-business-service/src/test/java/com/panpan/aibusinessservice/InternalOrderControllerTest.java
projects/java-business-service/src/test/java/com/panpan/aibusinessservice/InternalTicketControllerTest.java
projects/java-business-service/src/test/java/com/panpan/aibusinessservice/RedisToolRateLimiterTest.java
projects/java-business-service/src/test/java/com/panpan/aibusinessservice/InternalApiContractTest.java
```

Python 测试入口：

```text
projects/ai-service/tests/test_java_order_client.py
projects/ai-service/tests/test_java_ticket_client.py
projects/ai-service/tests/test_java_error_mapping.py
projects/ai-service/tests/test_java_business_contract.py
```

### 3. 阶段 7 当前验收标准

阶段 7 完成后，可以用下面标准判断是否达标：

```text
知道 AI Agent 和 Java 后端的职责边界。
知道为什么要设计 AI 工具专用 internal API。
知道为什么 Java Entity 不直接暴露给模型。
知道为什么写操作需要用户确认和幂等键。
知道 Redis 在订单缓存、幂等和限流里的作用。
知道 internal token、caller、user_id、tenant_id 分别解决什么问题。
知道 Java 错误码为什么不能直接等于用户话术。
知道 trace_id 如何串联 Python 和 Java。
知道契约测试为什么比只写单元测试更适合跨服务边界。
知道当前 mock 链路和真实 Java business 链路的关系。
```

### 4. 阶段 7 最重要的收获

阶段 7 最重要的收获可以压缩成一句话：

```text
AI Agent 不能替代后端边界，反而要求后端边界更清晰。
```

再展开一点：

```text
模型负责理解和生成。
Python 负责 AI 编排和校验。
Java 负责真实业务执行。
MySQL 负责持久化事实。
Redis 负责缓存、幂等和限流等短期状态。
契约测试负责锁住跨服务接口。
trace_id 负责让问题能被排查。
```

## 本节修改说明

本节主要是文档整理。

新增：

```text
notes/stage7-12-project-summary.md
```

更新：

```text
README.md
docs/learning-progress.md
docs/java-ai-api-contract.md
docs/project-diagrams.md
docs/local-run-and-demo.md
docs/interview-and-resume.md
```

没有修改：

```text
projects/java-business-service/README.md
```

没有新增核心业务代码。

## 本节练习

### 练习 1：阶段 7 的核心主题是什么？

参考答案：

```text
阶段 7 的核心主题不是普通 Spring Boot CRUD，而是真实 Java Spring Boot + MySQL/Redis 业务服务如何被 Python AI Agent 安全、稳定、可追踪地调用。
```

### 练习 2：为什么需要 AI 工具专用 internal API？

参考答案：

```text
因为普通前端接口可能返回过多字段，甚至包含手机号、地址、支付流水、内部备注等不应该给模型看的信息。
AI 工具专用 internal API 可以只暴露模型回答所需的最小字段，并强制要求 internal token、真实用户身份、租户、trace_id 和幂等键等边界。
```

### 练习 3：当前 `java-mock-service` 和 `java-business-service` 有什么区别？

参考答案：

```text
java-mock-service 是早期学习 Tool Calling 和 Agent 主线时使用的模拟业务服务。
java-business-service 是阶段 7 新增的真实 Java Spring Boot 业务服务，已经引入 MyBatis、MySQL、Redis、internal API、错误码、trace_id 和契约测试。
```

### 练习 4：为什么 Python 不能直接相信 Java 返回的成功响应？

参考答案：

```text
因为跨服务接口可能被改坏，比如字段缺失、字段类型变化、统一响应结构变化。
Python AI 服务如果直接把不完整或不符合预期的数据交给模型，模型可能编造回答。
所以 Python 需要用 Pydantic 契约模型校验 Java 成功响应和工具可见字段。
```

### 练习 5：为什么契约测试比只写单元测试更适合 Python + Java 边界？

参考答案：

```text
单元测试主要验证某个服务内部逻辑。
Python + Java 的问题经常发生在接口边界，比如状态码、错误码、字段名、header、响应结构不一致。
契约测试可以让 provider 和 consumer 围绕同一份契约验证，减少两边各测各的风险。
```

## 自测题

### 自测 1：模型、Python AI 服务、Java 业务服务分别负责什么？

参考答案：

```text
模型负责理解用户意图、生成自然语言回答、提出可能的工具调用。
Python AI 服务负责 prompt、RAG、Tool Calling、LangGraph、模型输出和工具参数校验、错误映射。
Java 业务服务负责真实业务规则、权限、事务、MySQL、Redis、审计和机器错误码。
```

### 自测 2：为什么写操作必须有用户确认和幂等？

参考答案：

```text
因为创建工单这类写操作会改变业务系统状态。
模型可能理解错用户意图，网络或调用方也可能重复提交。
用户确认用于保证用户真的同意执行写操作，幂等键用于防止同一次确认重复创建多条工单。
```

### 自测 3：`X-User-Id` 和 `X-Internal-Token` 有什么区别？

参考答案：

```text
X-Internal-Token 证明调用方是被允许的内部服务，例如 ai-service。
X-User-Id 表示当前真实用户身份，用于业务权限判断。
前者解决服务身份，后者解决用户身份，不能互相替代。
```

### 自测 4：为什么 Java 错误码不能直接交给模型自由解释？

参考答案：

```text
因为有些 Java 错误码包含内部系统语义，例如内部鉴权失败、上游服务异常、幂等键缺失。
这些错误不应该暴露给用户，也不应该让模型自由发挥。
Python AI 服务需要先把 Java 错误码映射成安全的 AppException 和用户可理解提示。
```

### 自测 5：阶段 7 完成后，项目是否已经是完整生产系统？

参考答案：

```text
不是。
阶段 7 完成的是真实 Java 业务服务接入 AI Agent 的核心底座。
项目仍缺完整登录认证、真实用户权限体系、前端客服工作台、生产部署、集中监控告警、压测和更完整业务流程。
```

### 自测 6：如果后续要把 Python 运行时链路切到 `java-business-service`，应该先看什么？

参考答案：

```text
应该先看共享契约文件 contracts/java-business-service/internal-api-contract-cases.json 和 docs/java-ai-api-contract.md。
迁移时要保证 Python client、Agent 工具节点、错误映射、测试数据和评测样本都按真实 Java business contract 调整。
```

## 本节总结

阶段 7 到这里完成。

这一阶段你不是只学了一个 Spring Boot 服务，而是学了：

```text
传统 Java 后端如何变成 AI Agent 可以调用的真实业务系统。
```

这一阶段的核心能力是：

```text
边界设计
工具接口契约
真实 MySQL/Redis 业务服务
传统 MyBatis 项目结构
内部鉴权
用户身份和租户传递
错误码安全映射
trace_id 跨服务追踪
契约测试和集成测试
```

你现在应该形成一个很重要的判断：

```text
AI 应用不是把模型接到数据库上。
AI 应用是把模型放进一个有边界、有权限、有契约、有测试、有追踪的后端系统里。
```

下一阶段可以继续补新的 AI 应用工程技术，例如：

```text
LangGraph 更深入
MCP
Human-in-the-loop 强化
Agent 状态持久化强化
Tracing 和自动化评估强化
混合检索与 Rerank
多模型路由
成本控制
```

具体下一阶段学什么，可以根据你的目标选择：

```text
想强化 Agent 工程：优先 LangGraph 深入和 Human-in-the-loop。
想强化企业集成：优先 MCP。
想强化 RAG 效果：优先混合检索和 Rerank。
想强化生产能力：优先 tracing、自动化评估、成本控制。
```
