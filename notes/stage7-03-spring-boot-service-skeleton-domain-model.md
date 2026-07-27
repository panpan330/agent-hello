# 阶段 7 第 3 节：真实 Spring Boot 服务骨架和领域模型

## 本节定位

前两节完成了阶段 7 的设计前提：

```text
第 1 节：AI Agent 调用传统 Java 后端时，边界到底怎么设计
第 2 节：面向 Tool Calling 的 Java API 契约设计
```

现在开始进入代码。

但这一节仍然不是重新学习 Spring Boot 入门。

你已经有传统 Java 后端经验，所以本节重点不是：

```text
@RestController 是什么
@Service 是什么
Maven 是什么
Spring Boot 怎么启动
```

本节重点是：

```text
如何把真实 Java 后端项目结构设计成能承接 AI Agent 工具调用契约的业务服务。
```

也就是说，今天不只是“创建一个 Spring Boot 项目”。

今天要完成的是：

```text
把 java-mock-service 的学习定位，推进到 java-business-service 的真实业务服务骨架。
```

当前项目原来是：

```text
projects/java-mock-service
```

它是 FastAPI 写的 mock 服务，用来模拟 Java 后端。

本节新增：

```text
projects/java-business-service
```

它是 Spring Boot 服务骨架，后续会逐步接入：

```text
MySQL
Redis
真实权限
事务
Python AI 服务对接
Docker Compose
```

---

## 一、本节学习目标

学完本节，你要能讲清楚：

1. 为什么要新增 `java-business-service`，而不是直接改 `java-mock-service`。
2. 为什么真实 Java 服务不应该负责 prompt、模型调用和 LangGraph。
3. Spring Boot 服务在 AI Agent 项目里的职责是什么。
4. 为什么本节先建骨架，不急着接 MySQL/Redis。
5. 为什么包结构要区分 `interfaces`、`application`、`domain`、`infrastructure`、`common`。
6. Internal Controller 和普通用户 Controller 有什么区别。
7. `ApiResponse<T>` 为什么属于通用契约层。
8. `BusinessErrorCode` 为什么要集中管理。
9. `InternalRequestResolver` 解决什么问题。
10. `Order`、`Ticket` 为什么是领域模型，不是数据库 Entity。
11. `OrderToolView`、`TicketToolView` 为什么是 Tool-facing DTO。
12. 为什么现在先用 `InMemoryOrderRepository` 和 `InMemoryTicketRepository`。
13. `OrderRepository`、`TicketRepository` 接口为什么放在 domain 层。
14. 创建工单为什么在 Java 侧仍然要检查幂等键和订单权限。
15. 本节测试覆盖了哪些关键边界。
16. 为什么测试里不调用真实大模型。
17. Maven 首次拉依赖慢和测试失败怎么区分。
18. IDEA 输出中文乱码时应该如何判断。
19. 本节代码和第 2 节契约怎么对应。
20. 下一节为什么要进入 MySQL 业务数据模型。

---

## 二、本节先不做什么

这一节暂时不做：

1. 不连接 MySQL。
2. 不连接 Redis。
3. 不改 Python AI 服务的 Java client。
4. 不替换 `java-mock-service`。
5. 不修改 Docker Compose。
6. 不做完整认证授权。
7. 不做数据库事务。
8. 不做 Swagger/OpenAPI。
9. 不启动 VMware。
10. 不调用真实大模型。

原因是：

```text
本节目标是立起真实 Java 服务骨架和领域边界。
```

如果这一步还没稳定，就急着接 MySQL/Redis，会把问题混在一起：

```text
到底是项目结构问题？
到底是接口契约问题？
到底是数据库问题？
到底是 Redis 问题？
到底是测试问题？
```

所以本节先做一个能编译、能测试、接口方向正确的 Spring Boot 骨架。

---

## 三、基础知识铺垫

### 1. mock 服务和真实业务服务的区别

`java-mock-service` 的价值是：

```text
让 Python AI 服务先能通过 HTTP 调用一个业务后端。
```

它帮助我们先学会：

```text
工具调用
Java client
订单查询
工单创建
幂等雏形
trace_id 透传
工具结果校验
```

但它仍然是 mock。

mock 的典型特点：

```text
数据写死在内存里
没有真实数据库
没有真实权限
没有真实事务
不承载长期业务事实
适合快速学习和测试链路
```

真实业务服务的特点：

```text
有清楚的业务领域模型
有稳定接口契约
有真实数据持久化
有权限校验
有事务
有幂等
有错误码
有审计和日志
能被其他服务长期依赖
```

所以阶段 7 的目标不是把 mock 服务删掉。

而是新增一个更真实的 Java 服务：

```text
java-business-service
```

这样学习边界更清楚：

```text
java-mock-service
-> 历史学习阶段的过渡服务

java-business-service
-> 阶段 7 开始真实化的业务服务
```

### 2. 为什么不直接改 `java-mock-service`

直接把 `java-mock-service` 改成 Spring Boot 也可以。

但学习项目里不推荐。

原因有三点。

第一，保留历史学习脉络。

`java-mock-service` 记录了前面阶段：

```text
为什么先用 mock 跑通 AI 工具调用
```

如果直接覆盖掉，后面很难看出项目是怎么一步步演进的。

第二，降低改造风险。

Python AI 服务当前已经能调用 mock 服务。

如果直接替换，可能影响已有回归。

新增服务可以让我们先独立验证 Spring Boot 骨架。

第三，更符合工程迁移思路。

真实项目里经常是：

```text
先保留旧接口
再创建新服务或新版本
验证通过后再切流
```

所以本节采用：

```text
新增 java-business-service，不删除 java-mock-service。
```

### 3. Java 业务服务不负责 AI 逻辑

这是阶段 7 必须守住的边界。

Java 业务服务不负责：

```text
prompt
大模型调用
LangGraph 节点编排
RAG 检索
模型输出解析
模型总结
Agent eval
```

这些属于 Python AI 服务。

Java 业务服务负责：

```text
订单事实
用户身份
权限校验
工单创建
业务规则
幂等
事务
持久化
错误码
内部接口契约
```

如果把 AI 逻辑写进 Java 后端，会出现职责混乱：

```text
Java 后端既判断业务，又判断模型意图。
Python Agent 既编排工具，又被 Java 的 AI 逻辑影响。
后续测试和排查会变复杂。
```

更清楚的分工是：

```text
Python 负责 AI。
Java 负责业务。
```

### 4. 为什么要先建骨架

骨架不是空架子。

一个好骨架会提前决定：

```text
代码放哪里
职责怎么拆
以后数据库怎么接
以后 Redis 怎么接
Controller 能不能保持薄
领域逻辑会不会散落
DTO 会不会污染领域模型
异常和错误码会不会统一
测试能不能围绕契约写
```

如果骨架随便搭，后面会变成：

```text
Controller 里写一堆业务逻辑。
DTO 直接当 Entity 用。
错误码散落在各个方法里。
内存数据换 MySQL 时到处改。
Python client 依赖不稳定字段。
```

所以本节先把骨架立好。

### 5. 本节采用的分层方式

本节新服务采用这些主要包：

```text
common
interfaces
application
domain
infrastructure
```

这不是为了显得复杂。

每层有明确职责。

`common`：

```text
通用能力。
例如统一响应、错误码、异常处理、trace header、内部鉴权上下文。
```

`interfaces`：

```text
对外接口层。
这里主要是 internal Controller 和 HTTP DTO。
```

`application`：

```text
应用服务层。
负责编排一个用例，例如查询订单、创建工单。
```

`domain`：

```text
领域层。
放 Order、Ticket 这些业务概念，以及 Repository 接口。
```

`infrastructure`：

```text
基础设施层。
现在是内存 Repository，后续会换成 MySQL、Redis。
```

### 6. 为什么 Repository 接口放 domain 层

这点非常重要。

我们本节定义：

```text
domain/repository/OrderRepository.java
domain/repository/TicketRepository.java
```

接口在 domain 层。

实现放到 infrastructure：

```text
infrastructure/persistence/InMemoryOrderRepository.java
infrastructure/persistence/InMemoryTicketRepository.java
```

这样做的好处是：

```text
业务层依赖抽象，不依赖具体存储。
```

今天存储是内存。

下一节或后续可以换成：

```text
MySQL Repository
MyBatis Mapper
JPA Repository
Redis 幂等 Repository
```

应用服务层不应该关心底层到底是 Map 还是 MySQL。

这就是为什么先抽 Repository 接口。

### 7. DTO 和领域模型为什么分开

本节有两类对象：

领域模型：

```text
Order
Ticket
OrderStatus
PaymentStatus
TicketCategory
TicketPriority
TicketStatus
```

接口 DTO：

```text
OrderToolView
CreateTicketCommand
TicketToolView
ApiResponse
```

领域模型表达业务事实。

例如：

```text
Order 属于哪个用户
Order 属于哪个租户
Order 当前状态是什么
Order 是否允许创建工单
```

接口 DTO 表达给调用方看的契约。

例如：

```text
AI 服务查询订单后能看到哪些字段
创建工单接口允许传哪些字段
工单创建成功后返回哪些字段
```

不要混在一起。

否则会出现：

```text
数据库或领域内部字段不小心暴露给 AI 服务。
接口为了兼容 Python 影响领域对象设计。
未来接 MySQL 时 Entity 改动影响 Python client。
```

### 8. Internal Controller 和普通 Controller 的区别

本节新增的是：

```text
InternalOrderController
InternalTicketController
```

路径是：

```text
/internal/orders/{orderId}
/internal/tickets
```

它们不是给普通用户直接访问。

它们是给：

```text
Python AI 服务
```

调用的。

所以 internal Controller 要关注：

```text
X-Trace-Id
X-Caller
X-User-Id
X-Tenant-Id
X-Internal-Token
Idempotency-Key
```

普通用户 Controller 关注的是：

```text
登录态
页面表单
用户前端交互
普通 API 权限
```

阶段 7 先做 internal Controller，因为当前项目主线是：

```text
Python AI 服务调用 Java 业务服务。
```

### 9. 为什么要统一 `ApiResponse<T>`

本节新增：

```text
ApiResponse<T>
```

结构是：

```text
success
code
message
data
trace_id
```

它对 AI 项目很重要。

Python AI 服务可以稳定判断：

```text
success=true
-> 校验 data。

success=false
-> 根据 code 决定追问、拒绝、重试、降级或转人工。

trace_id
-> 串联 Python 和 Java 日志。
```

这比直接返回一个业务对象更适合 Agent。

### 10. 为什么错误码集中管理

本节新增：

```text
BusinessErrorCode
BusinessException
GlobalExceptionHandler
```

错误码集中管理有三个好处。

第一，Python AI 服务能稳定映射。

例如：

```text
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
IDEMPOTENCY_KEY_CONFLICT
```

这些错误码后续会影响 Agent 行为。

第二，避免错误码散落。

如果每个 Controller 自己写字符串，后面很容易出现：

```text
ORDER_NOT_FOUND
ORDER_NOT_EXIST
ORDER_MISSING
```

这会让 Python 侧难以处理。

第三，方便做契约测试。

测试可以明确断言：

```text
无权限订单返回 ORDER_ACCESS_DENIED。
缺少幂等键返回 IDEMPOTENCY_KEY_REQUIRED。
```

### 11. 为什么内部鉴权现在只是占位

本节新增：

```text
InternalRequestResolver
InternalApiProperties
InternalRequestContext
```

现在内部鉴权很简单：

```text
X-Caller 必须是 ai-service。
X-Internal-Token 必须等于配置里的 token。
```

这还不是完整生产鉴权。

但它的意义是：

```text
先把鉴权位置留出来。
```

后续可以升级为：

```text
服务间签名
JWT
mTLS
网关鉴权
更完整的用户身份透传
```

学习阶段不需要一步到位，但结构要先有。

### 12. 为什么现在先用内存 Repository

本节仍然用内存数据：

```text
InMemoryOrderRepository
InMemoryTicketRepository
```

这不是退回 mock。

因为和原来的 mock 服务不同，本节已经建立了：

```text
Spring Boot 项目
internal API
领域模型
Repository 抽象
统一响应
错误码
内部 Header 校验
幂等雏形
契约测试
```

内存 Repository 只是暂时代替 MySQL/Redis。

下一步替换存储时，目标是：

```text
尽量不改 Controller。
尽量少改 Application Service。
主要替换 Infrastructure 实现。
```

这才是分层的价值。

### 13. 为什么测试不调用真实模型

本节是 Java 业务服务测试。

它不应该调用真实大模型。

原因是：

```text
Java 服务不负责模型。
真实模型有成本。
真实模型输出不稳定。
Java 契约测试应该是确定性的。
```

本节测试的是：

```text
Spring Boot 服务是否能启动
internal API 是否返回统一响应
Header 鉴权是否生效
订单权限是否校验
创建工单是否需要幂等键
同一幂等键同一参数是否返回同一结果
同一幂等键不同参数是否冲突
```

这就是本节最该测的内容。

### 14. Maven 首次运行慢怎么判断

你在 IDEA 或命令行第一次跑：

```powershell
mvn test
```

可能会看到大量：

```text
Downloading from ...
Downloaded from ...
```

这表示 Maven 在拉依赖。

首次运行慢是正常的。

真正要看最后：

```text
BUILD SUCCESS
```

或者：

```text
BUILD FAILURE
```

如果是 `BUILD FAILURE`，再看失败原因。

本节第一次失败不是代码编译失败，而是测试里用正则提取 JSON 字段不可靠。

我们改成了：

```text
ObjectMapper.readTree(firstBody).path("data").path("ticket_id").asText()
```

这就是更稳的测试写法。

### 15. IDEA 里中文乱码怎么判断

你发来的 IDEA 输出里有中文乱码。

这类情况要先判断：

```text
是业务内容真的乱码？
还是控制台显示编码乱码？
```

本次属于后者。

因为测试失败的核心是：

```text
expected 值不等于 actual 值
```

不是中文字段真的错。

而且响应 body 里业务字段是正常 JSON。

所以不用大范围改编码，也不用重写中文文档。

这和你之前提醒的一样：

```text
看到中文显示异常，先怀疑 PowerShell/IDEA 控制台编码显示问题，不要误判成文件乱码。
```

---

## 四、本节主题系统讲解

### 1. 本节新增的项目

本节新增：

```text
projects/java-business-service
```

这个项目是阶段 7 的真实 Java 服务入口。

它和旧服务的关系：

```text
projects/java-mock-service
-> 历史 mock 服务，继续保留。

projects/java-business-service
-> 新的 Spring Boot 业务服务，后续逐步真实化。
```

### 2. 新服务当前目录结构

当前核心结构：

```text
projects/java-business-service/
  pom.xml
  README.md
  src/main/resources/application.yml
  src/main/java/com/panpan/aibusinessservice/
    AiBusinessServiceApplication.java
    common/
      api/
      error/
      security/
      trace/
    interfaces/
      internal/
      dto/
    application/
      service/
    domain/
      model/
      repository/
    infrastructure/
      persistence/
  src/test/java/com/panpan/aibusinessservice/
```

这套结构不是唯一正确答案。

但它适合本项目。

因为阶段 7 的重点是：

```text
让 Java 服务承接 AI 工具契约。
```

所以我们明确区分：

```text
接口契约
应用用例
领域模型
存储实现
通用边界
```

### 3. `pom.xml` 做了什么

本节新增 Maven 项目：

```text
groupId: com.panpan
artifactId: java-business-service
Java: 17
Spring Boot: 3.3.5
```

当前依赖只有：

```text
spring-boot-starter-web
spring-boot-starter-validation
spring-boot-starter-test
```

为什么现在依赖这么少？

因为本节不接数据库、不接 Redis。

现在只需要：

```text
Web API
参数校验
测试
```

后续接 MySQL/Redis 时再加：

```text
MyBatis / MyBatis-Plus / JPA
MySQL Driver
Spring Data Redis
```

这符合渐进式学习。

### 4. `application.yml` 做了什么

当前配置：

```yaml
server:
  port: 8002

spring:
  application:
    name: java-business-service
  jackson:
    property-naming-strategy: SNAKE_CASE

app:
  internal:
    token: ${JAVA_BUSINESS_INTERNAL_TOKEN:local-dev-internal-token}
```

重点有三个。

第一，端口用 `8002`。

因为：

```text
ai-service 常用 8000
java-mock-service 常用 8001
java-business-service 使用 8002
```

第二，Jackson 使用 `SNAKE_CASE`。

这样 Java record 字段：

```text
orderId
ticketId
traceId
```

返回 JSON 时会变成：

```text
order_id
ticket_id
trace_id
```

这和 Python/Pydantic/Tool Calling 里常用字段风格更一致。

第三，内部 token 支持环境变量覆盖。

本地默认：

```text
local-dev-internal-token
```

后续真实部署时不能用这个默认值。

### 5. `ApiResponse<T>` 对应第 2 节契约

第 2 节设计了统一响应：

```text
success
code
message
data
trace_id
```

本节用 Java record 实现：

```java
public record ApiResponse<T>(
        boolean success,
        String code,
        String message,
        T data,
        @JsonProperty("trace_id") String traceId
) {
}
```

这里要注意：

```text
ApiResponse<T> 是接口契约对象，不是领域对象。
```

它只负责统一 HTTP 返回格式。

### 6. `BusinessErrorCode` 对应 Agent 可理解错误

本节新增错误码：

```text
INTERNAL_AUTH_FAILED
ORDER_ID_INVALID
ORDER_NOT_FOUND
ORDER_ACCESS_DENIED
IDEMPOTENCY_KEY_REQUIRED
IDEMPOTENCY_KEY_INVALID
IDEMPOTENCY_KEY_CONFLICT
TICKET_REQUEST_INVALID
TICKET_ALREADY_EXISTS
ORDER_NOT_SUPPORT_TICKET
```

这些错误不是随便给人看的。

它们后续会给 Python AI 服务做映射。

例如：

```text
ORDER_NOT_FOUND
-> 让用户检查订单号。

ORDER_ACCESS_DENIED
-> 拒绝泄露订单信息。

IDEMPOTENCY_KEY_CONFLICT
-> 告诉系统不要让模型编造成功。
```

### 7. `InternalRequestResolver` 的作用

`InternalRequestResolver` 从请求 Header 里解析：

```text
X-Trace-Id
X-Caller
X-User-Id
X-Tenant-Id
X-Internal-Token
```

然后生成：

```text
InternalRequestContext
```

它的意义是：

```text
Controller 不直接散乱读取 Header。
内部调用边界集中在一个地方。
```

当前校验逻辑很简单：

```text
X-Caller 必须是 ai-service。
X-Internal-Token 必须匹配配置。
```

后续可以在这里升级鉴权。

### 8. `Order` 领域模型的关键点

`Order` 里有：

```text
orderId
ownerUserId
tenantId
orderStatus
paymentStatus
logisticsMessage
latestEvent
canCreateTicket
```

最关键的是：

```java
public boolean visibleTo(String userId, String tenantId) {
    return ownerUserId.equals(userId) && this.tenantId.equals(tenantId);
}
```

这表达了订单权限规则的雏形：

```text
只有订单所属用户，并且租户匹配，才能看到订单。
```

虽然现在规则很简单，但它说明一件事：

```text
权限判断不交给模型。
权限判断在 Java 业务服务里。
```

### 9. `OrderToolView` 是给 AI 工具看的订单摘要

`OrderToolView` 包含：

```text
orderId
orderStatus
paymentStatus
logisticsMessage
latestEvent
canCreateTicket
userVisibleSummary
```

它不是完整订单。

它是：

```text
订单查询工具返回给 Python AI 服务的白名单视图。
```

这个设计对应第 2 节：

```text
模型只看到完成回答所需的最小信息。
```

### 10. `CreateTicketCommand` 是写工具请求 DTO

`CreateTicketCommand` 包含：

```text
title
description
category
priority
relatedOrderId
source
confirmationId
```

它没有 `requesterId`。

原因是：

```text
requesterId 不应该由模型或 body 决定。
用户身份来自 X-User-Id。
```

这正是第 2 节讲的接口契约原则。

### 11. `TicketApplicationService` 做了什么

创建工单不是 Controller 直接调用 Repository。

而是经过：

```text
TicketApplicationService
```

它负责一个完整用例：

```text
校验幂等键
校验关联订单是否存在
校验订单是否属于当前用户
校验订单是否支持创建工单
调用 TicketRepository 创建工单
返回 TicketToolView
```

这就是 application 层的价值。

它不是普通工具类。

它表达一个业务用例。

### 12. `InMemoryTicketRepository` 的幂等逻辑

当前内存仓库里维护：

```text
idempotencyKey -> IdempotencyRecord
```

如果同一个幂等键再次请求：

```text
参数相同 -> 返回同一张工单。
参数不同 -> 返回 IDEMPOTENCY_KEY_CONFLICT。
```

这模拟了真实 Redis/MySQL 幂等行为。

后续会改造成：

```text
Redis 保存幂等记录
MySQL 保存工单事实
数据库唯一约束兜底
```

### 13. Controller 为什么保持薄

`InternalOrderController` 做的事很少：

```text
解析 internal request context
调用 OrderQueryService
包装 ApiResponse
```

`InternalTicketController` 也是：

```text
解析 internal request context
读取 Idempotency-Key
调用 TicketApplicationService
包装 ApiResponse
```

Controller 不直接写：

```text
订单权限判断
工单业务规则
幂等逻辑
存储逻辑
```

这就是“薄 Controller”。

它让代码更容易测试和替换底层实现。

### 14. 本节测试覆盖了什么

本节新增测试：

```text
HealthControllerTest
InternalOrderControllerTest
InternalTicketControllerTest
```

覆盖：

```text
/health 返回 ok
订单查询成功返回统一响应
订单查询带 trace_id
无权订单返回 ORDER_ACCESS_DENIED
缺少内部 token 返回 INTERNAL_AUTH_FAILED
创建工单成功返回 TicketToolView
创建工单必须有 Idempotency-Key
同一幂等键同一参数返回同一 ticket_id
同一幂等键不同参数返回 IDEMPOTENCY_KEY_CONFLICT
```

这些测试和第 2 节契约直接对应。

### 15. 本节遇到的测试问题

第一次测试失败在：

```text
createTicketIsIdempotentForSameKeyAndSamePayload
```

原因是测试代码用正则从 JSON 字符串里提取：

```text
ticket_id
```

正则太贪婪，把后面一大段 JSON 也吞进了期望值。

错误写法的本质是：

```text
用字符串技巧解析结构化数据。
```

修复方式是：

```text
用 ObjectMapper 解析 JSON。
```

这也是一个工程习惯：

```text
有结构化格式时，优先用结构化解析，不要靠脆弱的字符串处理。
```

### 16. 本节最终验证结果

最终执行：

```powershell
cd D:\wendang\java+python+ai\projects\java-business-service
mvn test
```

结果：

```text
Tests run: 8, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

说明：

```text
Spring Boot 服务能启动测试上下文。
internal API 契约雏形可用。
基础权限、幂等和错误码行为通过测试。
```

---

## 五、本节新增代码讲解

### 1. 新增 `projects/java-business-service`

这是阶段 7 的真实 Java 后端项目。

它和 `java-mock-service` 并存。

学习意义：

```text
保留历史 mock 链路，同时开始真实业务服务建设。
```

### 2. `pom.xml`

本节只引入 Web、Validation、Test。

学习意义：

```text
只为当前目标引依赖。
不提前把 MySQL、Redis、MyBatis 都加进来。
```

这样你能清楚看到每节引入了什么、为什么引入。

### 3. `ApiResponse<T>`

它是 Java 对第 2 节统一响应契约的实现。

学习意义：

```text
让 Python AI 服务能稳定解析成功、失败、错误码、trace_id 和业务数据。
```

### 4. `BusinessErrorCode`

它把业务错误码集中起来。

学习意义：

```text
错误码是 Java 和 Python Agent 之间的机器信号，不能散乱命名。
```

### 5. `InternalRequestResolver`

它集中解析 internal Header。

学习意义：

```text
内部调用边界要集中管理，不要散落在每个 Controller。
```

### 6. `Order` 和 `Ticket`

它们是领域模型。

学习意义：

```text
领域模型表达业务事实，不等于 HTTP DTO，也不等于数据库 Entity。
```

### 7. `OrderToolView` 和 `TicketToolView`

它们是工具视图。

学习意义：

```text
AI 服务看到的是白名单业务摘要，不是完整内部对象。
```

### 8. `InMemoryOrderRepository` 和 `InMemoryTicketRepository`

它们是临时基础设施实现。

学习意义：

```text
先让接口和领域边界跑通，后续再把 infrastructure 替换成 MySQL/Redis。
```

### 9. `OrderQueryService`

它承接查询订单用例。

学习意义：

```text
订单权限由 Java 服务判断，不由模型判断。
```

### 10. `TicketApplicationService`

它承接创建工单用例。

学习意义：

```text
写操作必须在 Java 侧继续校验幂等、权限和业务规则。
```

### 11. `InternalOrderController` 和 `InternalTicketController`

它们是 Python AI 服务调用的 internal API。

学习意义：

```text
AI 工具接口和普通用户接口要分清楚。
```

### 12. 测试类

测试类验证了契约边界。

学习意义：

```text
阶段 7 的测试重点不是大模型，而是 Java 服务契约是否稳定。
```

---

## 六、常见误区

### 误区 1：新增 Spring Boot 项目就是阶段 7 的重点

不是。

Spring Boot 项目只是载体。

阶段 7 的重点是：

```text
Java 后端如何安全承接 AI Agent 工具调用。
```

### 误区 2：Controller 能跑就行

不够。

如果 Controller 里写满业务逻辑，后续接 MySQL/Redis、权限、事务会很乱。

### 误区 3：内存 Repository 就等于 mock，没有意义

不对。

当前内存 Repository 是 infrastructure 的临时实现。

它存在的意义是：

```text
先让分层和契约稳定。
```

后续可以替换为 MySQL/Redis。

### 误区 4：DTO 和领域模型可以混用

不推荐。

Tool-facing DTO 是给 Python AI 服务看的。

领域模型是 Java 内部业务事实。

数据库 Entity 是持久化结构。

三者职责不同。

### 误区 5：内部服务 token 简单就没意义

现在确实简单。

但它让代码里已经有：

```text
内部鉴权位置
配置入口
失败错误码
测试覆盖
```

后续升级会更自然。

### 误区 6：看到中文乱码就马上改文件编码

不应该。

本节 IDEA 输出里的中文乱码主要是控制台显示问题。

排查时先看：

```text
测试真正断言失败点是什么。
JSON 原始字段是否正确。
文件内容是否真的损坏。
```

不要因为控制台显示异常就大范围改文件。

### 误区 7：测试失败就说明业务代码一定错

不一定。

本节第一次失败就是测试提取 JSON 的方式错。

测试代码也是代码，也可能有 bug。

---

## 七、本节练习

### 练习 1：为什么本节新增 `java-business-service`，而不是直接覆盖 `java-mock-service`？

参考答案：

```text
因为 java-mock-service 记录了前面阶段用 mock 跑通 AI 工具链路的学习过程，直接覆盖会丢失演进脉络。新增 java-business-service 可以保留旧 mock 服务，同时独立建设真实 Spring Boot 业务服务，降低对现有 Python AI 服务回归的影响。
```

### 练习 2：为什么 Java 业务服务不负责 prompt 和 LangGraph？

参考答案：

```text
因为 prompt、模型调用、RAG、LangGraph 编排属于 Python AI 服务职责；Java 业务服务负责业务事实、权限、事务、幂等、持久化和稳定接口契约。混在一起会导致职责不清，测试和排查困难。
```

### 练习 3：`interfaces`、`application`、`domain`、`infrastructure` 分别负责什么？

参考答案：

```text
interfaces 负责 HTTP Controller 和 DTO；application 负责编排查询订单、创建工单等用例；domain 负责 Order、Ticket 等领域模型和 Repository 抽象；infrastructure 负责具体存储实现，现在是内存实现，后续会替换为 MySQL/Redis。
```

### 练习 4：为什么 `OrderToolView` 不直接返回完整 `Order`？

参考答案：

```text
因为 Order 是 Java 内部领域模型，可能包含 AI 服务不需要或不应该看到的信息。OrderToolView 是给 Python AI 服务的白名单视图，只包含订单回答所需字段，符合最小暴露原则。
```

### 练习 5：为什么 `CreateTicketCommand` 不建议包含 `requesterId`？

参考答案：

```text
因为 requesterId 表示真实用户身份，应该来自 X-User-Id 这类认证上下文，而不是由模型或请求 body 决定。这样可以避免模型编造身份、用户冒用身份或 Prompt Injection 影响用户身份。
```

### 练习 6：为什么创建工单在 Java 侧还要检查幂等键？

参考答案：

```text
因为 Python AI 服务可能重试，用户可能重复确认，模型也可能重复触发工具。Java 是最终写操作边界，必须用幂等键防止重复创建工单。同一幂等键同一参数返回同一结果，同一幂等键不同参数返回冲突。
```

### 练习 7：本节测试为什么不调用真实大模型？

参考答案：

```text
因为本节测试的是 Java 业务服务契约、权限、幂等和错误码，都是确定性后端行为。真实大模型不属于 Java 服务职责，并且有成本、网络和不稳定输出问题，不适合进入本节自动化测试。
```

### 练习 8：测试中为什么要用 `ObjectMapper` 解析 JSON，而不是正则？

参考答案：

```text
因为 JSON 是结构化数据，应该用结构化解析工具读取字段。正则容易因为贪婪匹配、字段顺序、转义字符或中文显示问题导致错误。ObjectMapper 能准确读取 data.ticket_id。
```

---

## 八、自测问题

### 自测 1：本节完成后，项目里 Java 服务发生了什么变化？

答案：

```text
项目新增了真实 Spring Boot 服务骨架 projects/java-business-service。它还没有接 MySQL/Redis，但已经有 internal API、统一响应、错误码、内部 Header 校验、领域模型、Repository 抽象、内存实现、订单查询和创建工单接口，以及基础契约测试。
```

### 自测 2：一句话说明 `java-business-service` 的定位。

答案：

```text
java-business-service 是 AI Agent 可以安全、稳定、可追踪调用的真实 Java 业务服务骨架，后续会逐步接入 MySQL、Redis、权限、事务和 Python AI 服务。
```

### 自测 3：为什么说本节不是普通 Spring Boot 入门？

答案：

```text
因为本节重点不是学习 @RestController、@Service 或 Maven 基础，而是围绕 AI Agent 调用 Java 后端的契约，设计 internal API、领域模型、DTO、错误码、幂等和 trace_id 边界。
```

### 自测 4：为什么 Repository 接口在 domain 层，实现放 infrastructure 层？

答案：

```text
因为业务层应该依赖存储抽象，而不是依赖具体实现。现在实现是内存 Map，后续可以替换成 MySQL/Redis，而应用服务和领域层尽量不被底层存储变化影响。
```

### 自测 5：`InternalRequestResolver` 的核心作用是什么？

答案：

```text
它集中解析和校验 internal API Header，包括 trace_id、caller、user_id、tenant_id 和 internal token，并生成 InternalRequestContext，避免每个 Controller 散乱处理内部调用边界。
```

### 自测 6：本节 `mvn test` 最终结果是什么？

答案：

```text
最终 mvn test 通过，Tests run: 8, Failures: 0, Errors: 0, Skipped: 0，BUILD SUCCESS。
```

### 自测 7：下一节应该学什么？

答案：

```text
下一节应该学习 MySQL 业务数据模型，把当前内存 Order/Ticket 数据推进到真实数据库表设计，包括用户表、订单表、工单表、工单事件表、索引和约束。
```

---

## 九、本节总结

这一节完成了阶段 7 的第一次真实代码推进。

新增：

```text
projects/java-business-service
```

这个服务当前已经具备：

```text
Spring Boot 3.3.5
JDK 17
Maven 项目结构
统一 ApiResponse
BusinessErrorCode
GlobalExceptionHandler
InternalRequestResolver
Order / Ticket 领域模型
OrderToolView / TicketToolView
CreateTicketCommand
InMemoryOrderRepository
InMemoryTicketRepository
InternalOrderController
InternalTicketController
HealthController
基础 MockMvc 测试
```

本节最重要的学习点不是“Spring Boot 怎么写接口”。

而是：

```text
真实 Java 业务服务要从一开始就围绕 AI 工具契约、权限边界、字段白名单、幂等和 trace_id 来设计。
```

当前还没有 MySQL/Redis。

这是刻意的。

因为我们先让：

```text
接口契约
项目分层
领域模型
错误码
internal header
测试边界
```

稳定下来。

下一节进入：

```text
阶段 7 第 4 节：MySQL 业务数据模型
```

下一节会把当前内存数据进一步真实化：

```text
用户表
订单表
工单表
工单事件表
索引
唯一约束
字段类型
订单和工单之间的关系
幂等键后续如何配合 MySQL/Redis
```
