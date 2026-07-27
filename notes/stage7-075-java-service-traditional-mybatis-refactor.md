# 阶段 7 第 7.5 节：Java 服务结构传统化重构 + MyBatis

## 本节定位

这一节是插在第 7 节和第 8 节之间的补课式重构。

前面我们为了更快讲清楚 AI Agent 调用 Java 后端的边界，先用了偏“分层架构/领域模型”的目录：

```text
application/service
domain/model
domain/repository
infrastructure/persistence
interfaces/internal
interfaces/dto
common/error
common/api
```

这种结构不是错的，但它和你以前熟悉的传统 Spring Boot 项目差别比较大。
你更熟悉的是：

```text
controller
service
service/impl
mapper
entity
dto
config
exception
common
```

所以这一节做两件事：

```text
第一，把 java-business-service 改成传统 Spring Boot 三层风格。
第二，把 JdbcTemplate 数据访问替换成 MyBatis Mapper + XML。
```

本节不是为了“重构而重构”。
真正目的有三个：

```text
让 Java 服务结构回到你熟悉的传统项目形态。
让后续学习 internal 鉴权、权限、错误码、trace、Python 对接时更容易定位代码。
让这个 Java 服务更像真实企业项目，而不是临时学习 Demo。
```

## 本节学习目标

学完本节，你应该能讲清楚：

```text
为什么 Spring Boot 项目经常分成 controller / service / mapper / entity / dto。
Controller、Service、Mapper、Entity、DTO 各自负责什么。
为什么不能把 SQL、业务判断、HTTP 参数解析都写在 Controller 里。
为什么 Service 是事务边界和业务规则边界。
为什么 Mapper 只负责数据库访问，不应该决定 AI 工具是否有权限。
为什么 Entity 和 DTO 要分开。
MyBatis 的 Mapper 接口和 XML 是怎么绑定的。
@Param 是干什么的。
resultMap 是干什么的。
为什么 MyBatis 项目常用 JavaBean 实体，而不是 record。
从 JdbcTemplate 切换到 MyBatis 后，业务能力为什么不应该改变。
AI Agent 调 Java 后端时，目录重构不能破坏哪些安全边界。
```

## 本节先不做什么

本节只做结构重构和 MyBatis 替换，不提前做这些内容：

```text
不改 Python AI 服务对接地址。
不修改 java-mock-service。
不新增真实用户登录系统。
不新增权限表。
不做新的业务接口。
不把 Redis 改成分布式锁。
不做 Docker Compose 编排。
不做生产部署。
```

原因很简单：

```text
这一节的核心是让 Java business service 的代码结构稳定下来。
结构稳定后，第 8 节再继续学 internal 鉴权和用户身份传递。
```

## 基础知识铺垫

### 1. 什么是传统 Spring Boot 三层结构

传统后端项目最常见的思路是：

```text
Controller 接 HTTP 请求
Service 处理业务规则
Mapper 访问数据库
```

你可以把一次请求想成这样：

```text
浏览器 / Python AI 服务 / 其他后端服务
        |
        v
Controller
        |
        v
Service
        |
        v
Mapper
        |
        v
MySQL
```

这个结构的核心不是“目录名字必须这样叫”，而是职责要清楚。

如果职责混在一起，会出现这些问题：

```text
Controller 里写 SQL：HTTP 层和数据库层绑死。
Mapper 里写权限判断：数据访问层知道太多业务含义。
Service 只转发不处理业务：业务规则散落到 Controller 或 Mapper。
DTO 直接当数据库实体用：对外 API 字段和内部表字段互相污染。
```

所以传统结构的价值是：

```text
请求入口清楚。
业务规则集中。
数据库访问集中。
对外数据和内部数据隔离。
后续维护时容易定位问题。
```

### 2. Controller 是什么

Controller 是 HTTP 入口。

它应该关心：

```text
这个接口的 URL 是什么。
这个接口是 GET 还是 POST。
请求参数从哪里来。
请求体用哪个 DTO 接收。
响应状态码是什么。
调用哪个 Service。
```

它不应该关心：

```text
SQL 怎么写。
Redis key 怎么拼。
工单幂等细节怎么判断。
订单是否允许创建工单的完整业务规则。
事务什么时候提交。
```

本项目里：

```text
InternalOrderController
InternalTicketController
```

它们是给 Python AI 服务调用的 internal API，不是给普通前端用户直接调用的公开 API。
所以 Controller 除了路由转发，还要先通过 `InternalRequestResolver` 解析内部调用身份。

### 3. Service 是什么

Service 是业务规则中心。

它应该回答的问题是：

```text
这个订单 ID 合法吗？
这个用户能不能看这个订单？
这个订单是否允许创建工单？
这个幂等键有没有冲突？
创建工单时要写几张表？
事务应该覆盖哪些写操作？
Redis 只是加速还是业务兜底？
```

本节重构后：

```text
OrderService
OrderServiceImpl

TicketService
TicketServiceImpl
```

Service 接口表达“这个业务能力能做什么”。
ServiceImpl 表达“这个业务能力具体怎么做”。

为什么要有接口？

在真实项目中，接口有几个价值：

```text
Controller 只依赖业务能力，不依赖具体实现类。
后续可以替换实现，例如 mock 实现、远程实现、灰度实现。
测试时更容易替换依赖。
团队协作时接口就是业务边界。
```

小项目也可以不写接口，但你更熟悉传统企业项目，所以本节保留接口 + impl。

### 4. Mapper 是什么

Mapper 是 MyBatis 的数据访问层。

它负责把 Java 方法映射成 SQL。

例如：

```java
Order selectByTenantIdAndOrderId(String tenantId, String orderId);
```

背后对应一段 SQL：

```sql
SELECT ...
FROM orders
WHERE tenant_id = ?
  AND order_id = ?
```

Mapper 应该保持简单：

```text
接收查询参数。
执行 SQL。
返回 Entity。
```

Mapper 不应该决定：

```text
用户有没有权限。
模型能不能调用这个工具。
工单冲突应该怎么响应给 AI。
某个错误码应该返回 400 还是 409。
```

这些属于 Service 和异常处理层。

### 5. Entity 是什么

Entity 是和数据库表结构接近的 Java 对象。

例如 `orders` 表有：

```text
order_id
user_id
tenant_id
order_status
payment_status
logistics_message
latest_event
can_create_ticket
```

对应到 Java：

```text
Order.orderId
Order.ownerUserId
Order.tenantId
Order.orderStatus
Order.paymentStatus
Order.logisticsMessage
Order.latestEvent
Order.canCreateTicket
```

MyBatis 习惯使用 JavaBean：

```text
private 字段
无参构造
getter
setter
```

原因是 MyBatis 读取数据库后，需要创建对象并给属性赋值。
JavaBean 结构对 MyBatis 最友好，也最接近传统企业项目。

### 6. DTO 是什么

DTO 是接口数据模型，不是数据库表模型。

本项目有两类 DTO：

```text
CreateTicketCommand：接收创建工单请求。
OrderToolView / TicketToolView：返回给 AI 工具调用方看的白名单结果。
```

为什么不能直接把 Entity 返回给 AI？

因为 Entity 经常包含内部字段，例如：

```text
tenantId
ownerUserId
idempotencyKey
requestFingerprint
createdTraceId
内部状态字段
```

这些字段不一定应该暴露给模型。

AI Agent 场景下 DTO 更重要，因为模型看到什么字段，会直接影响它如何回答用户。
所以我们必须坚持：

```text
Entity 是内部数据。
DTO 是对外契约。
返回给模型的数据必须白名单化。
```

### 7. MyBatis 和 JdbcTemplate 的区别

JdbcTemplate 是 Spring JDBC 的工具类。

它通常这样写：

```java
jdbcTemplate.query(sql, rowMapper, args);
```

优点是直接、简单。
缺点是当 SQL 和字段映射变多时，代码会变得分散。

MyBatis 的思路是：

```text
Java Mapper 接口定义方法。
XML Mapper 写 SQL。
resultMap 定义数据库列和 Java 属性的映射关系。
```

它更适合你熟悉的传统后端项目，尤其是：

```text
SQL 需要手写和调优。
表字段比较多。
查询条件会逐步复杂。
团队习惯把 SQL 放到 mapper XML。
后续要和已有企业项目风格保持一致。
```

本项目目前 SQL 不复杂，但提前切到 MyBatis 有学习价值：

```text
以后你看真实 Java 项目时，更容易把 AI Agent 调用链路接到传统 mapper/service/controller 结构里。
```

### 8. Mapper 接口和 XML 怎么对应

MyBatis 通过 namespace 和方法名绑定。

接口：

```java
package com.panpan.aibusinessservice.mapper;

public interface OrderMapper {
    Order selectByTenantIdAndOrderId(String tenantId, String orderId);
}
```

XML：

```xml
<mapper namespace="com.panpan.aibusinessservice.mapper.OrderMapper">
    <select id="selectByTenantIdAndOrderId" resultMap="OrderResultMap">
        ...
    </select>
</mapper>
```

对应规则：

```text
namespace 对应 Mapper 接口全限定名。
select / insert / update / delete 的 id 对应接口方法名。
SQL 参数来自接口方法参数。
查询结果通过 resultMap 映射成 Entity。
```

### 9. @Param 是什么

当 Mapper 方法有多个参数时，需要告诉 MyBatis 每个参数在 SQL 里叫什么。

例如：

```java
Order selectByTenantIdAndOrderId(
        @Param("tenantId") String tenantId,
        @Param("orderId") String orderId
);
```

XML 中就可以写：

```xml
WHERE tenant_id = #{tenantId}
  AND order_id = #{orderId}
```

没有 `@Param` 时，多参数场景容易出现参数名绑定不清晰的问题。
所以传统项目里，Mapper 多参数方法通常都显式写 `@Param`。

### 10. resultMap 是什么

数据库列名和 Java 属性名不一定完全一样。

例如：

```text
数据库列：user_id
Java 属性：ownerUserId
```

这时需要 `resultMap` 明确写：

```xml
<result column="user_id" property="ownerUserId"/>
```

`resultMap` 的价值是：

```text
字段映射清楚。
SQL 查询结果和 Java Entity 的关系清楚。
后续字段增加时容易维护。
```

## 本节主题系统讲解

### 1. 重构前的问题

重构前代码已经能工作，但学习上有两个问题。

第一个问题是结构和你的经验不一致：

```text
interfaces/internal 更像分层架构里的接口适配层。
application/service 更像应用服务层。
domain/repository 更像领域仓储接口。
infrastructure/persistence 更像基础设施层。
```

这些概念对 DDD 或整洁架构有意义，但你当前目标是：

```text
把传统 Java 后端能力迁移到 AI Agent 可调用的真实业务服务中。
```

所以先对齐传统结构更合适。

第二个问题是数据访问层还是 JdbcTemplate：

```text
JdbcOrderRepository
JdbcTicketRepository
OrderRowMapper
TicketRowMapper
```

这些代码不是不能用，但你不习惯。
如果后续继续学权限、错误码、trace、Python 对接，还一直带着旧结构，会增加理解成本。

### 2. 重构后的目录

本节重构后的核心目录是：

```text
projects/java-business-service/src/main/java/com/panpan/aibusinessservice/
├── controller/
├── service/
│   └── impl/
├── mapper/
├── entity/
├── dto/
├── config/
├── exception/
└── common/
    ├── cache/
    ├── rate/
    ├── redis/
    ├── security/
    └── trace/
```

各目录职责：

```text
controller：HTTP 接口入口。
service：业务能力接口。
service.impl：业务能力实现。
mapper：MyBatis 数据访问接口。
entity：数据库实体。
dto：请求和响应 DTO。
config：Spring Boot 配置属性和框架配置。
exception：业务异常、错误码、全局异常处理。
common：通用响应、内部安全上下文、trace、Redis 工具、缓存和限流。
```

这和你熟悉的传统项目结构基本一致。

### 3. 订单查询链路

现在订单查询链路是：

```text
GET /internal/orders/{orderId}
-> InternalOrderController
-> InternalRequestResolver
-> OrderService
-> OrderServiceImpl
-> OrderCache
-> RedisOrderCache 或 NoOpOrderCache
-> OrderMapper
-> OrderMapper.xml
-> MySQL orders
-> OrderToolView
-> ApiResponse
```

这里有几个重点。

第一，Controller 不直接查数据库。

第二，权限判断仍然在 Service：

```text
order.visibleTo(context.userId(), context.tenantId())
```

第三，Redis 仍然只是加速：

```text
缓存命中：拿缓存里的订单。
缓存未命中：查 MyBatis Mapper，再写回缓存。
```

第四，返回给 AI 的仍然是 `OrderToolView`，不是 `Order`。

这说明结构变化没有破坏 AI 工具调用的字段白名单边界。

### 4. 创建工单链路

现在创建工单链路是：

```text
POST /internal/tickets
-> InternalTicketController
-> InternalRequestResolver
-> TicketService
-> TicketServiceImpl
-> 校验 Idempotency-Key
-> 校验关联订单
-> Redis 幂等缓存尝试命中
-> TicketMapper 查询或写入 tickets
-> TicketMapper 写入 ticket_events
-> Redis 幂等缓存写入
-> TicketToolView
-> ApiResponse
```

这条链路里最重要的是：

```text
Redis 可以加速幂等判断。
MySQL 唯一索引仍然是最终兜底。
@Transactional 仍然包住工单和事件写入。
DTO 白名单仍然控制返回给 AI 的字段。
```

所以本节虽然改了目录和持久层实现，但没有改变第 6、7 节建立的业务安全原则。

### 5. 为什么删除旧 Repository

旧结构里有：

```text
OrderRepository
TicketRepository
JdbcOrderRepository
JdbcTicketRepository
InMemoryOrderRepository
InMemoryTicketRepository
```

本节切到 MyBatis 后，继续保留这些文件会造成两个问题：

```text
学习上会混乱：到底现在是 Repository 还是 Mapper？
Spring 扫描上可能混乱：旧实现和新实现可能同时成为 Bean。
```

所以本节删除旧 Repository/JDBC 路径，只保留：

```text
OrderMapper
TicketMapper
```

这让项目结构更像真实传统 Spring Boot + MyBatis 项目。

### 6. 为什么 app.persistence 配置也删除

第 5、6 节为了支持内存实现和 MySQL 实现切换，曾经保留：

```yaml
app:
  persistence:
    orders: mysql
    tickets: mysql
```

本节之后，Java 服务已经明确使用 MyBatis + 数据库。
测试环境也通过 H2 来模拟数据库，而不是用内存 Repository。

所以继续保留 `app.persistence` 会让人误以为还能切换旧实现。
删除它可以让配置更诚实：

```text
当前服务的数据访问层就是 MyBatis。
```

### 7. MyBatis 配置做了什么

本节新增：

```java
@MapperScan("com.panpan.aibusinessservice.mapper")
```

作用是告诉 Spring：

```text
扫描 mapper 包。
把 Mapper 接口交给 MyBatis 创建代理对象。
Service 注入 Mapper 时，Spring 能找到对应 Bean。
```

同时在 `application.yml` 配置：

```yaml
mybatis:
  mapper-locations: classpath:mapper/*.xml
  configuration:
    map-underscore-to-camel-case: true
```

作用是：

```text
告诉 MyBatis 去 resources/mapper 下找 XML。
开启下划线到驼峰的基础映射习惯。
```

即使已经写了 `resultMap`，这个配置也符合传统项目习惯。

### 8. 本节对 AI Agent 边界的影响

这节重构没有让模型拥有更多权限。

模型仍然不能：

```text
直接连 MySQL。
直接写 Redis。
绕过 Java Service 创建工单。
绕过 Idempotency-Key。
绕过 internal token。
绕过用户身份和租户边界。
看到 Entity 的全部内部字段。
```

模型能做的仍然是：

```text
通过 Python AI 服务发起工具调用。
Python 根据工具契约调用 Java internal API。
Java 后端校验 header、用户、租户、幂等、权限和业务规则。
Java 返回白名单 DTO。
模型基于白名单 DTO 给用户总结。
```

这就是传统后端接入 AI Agent 时最重要的思想：

```text
AI 可以提出意图。
后端必须负责执行边界。
```

## 本节代码改动讲解

### 1. Controller 层

本节把 Controller 移到：

```text
controller/HealthController.java
controller/InternalOrderController.java
controller/InternalTicketController.java
```

Controller 的核心变化是依赖传统 Service：

```text
InternalOrderController -> OrderService
InternalTicketController -> TicketService
```

这比旧的 `OrderQueryService`、`TicketApplicationService` 更贴近传统项目命名。

你看 Controller 时只需要记住：

```text
Controller 负责 HTTP。
真正业务交给 Service。
```

### 2. Service 层

新增：

```text
service/OrderService.java
service/TicketService.java
service/impl/OrderServiceImpl.java
service/impl/TicketServiceImpl.java
```

`OrderServiceImpl` 负责：

```text
校验订单 ID。
读取 Redis 缓存。
缓存未命中时通过 OrderMapper 查数据库。
校验用户和租户是否能访问订单。
转成 OrderToolView。
```

`TicketServiceImpl` 负责：

```text
校验 Idempotency-Key。
校验关联订单是否存在、是否属于当前用户、是否允许创建工单。
计算 requestFingerprint。
先看 Redis 幂等缓存。
再看 MySQL 幂等记录。
新建工单。
写入 ticket_events。
处理 DuplicateKeyException。
写回 Redis 幂等缓存。
转成 TicketToolView。
```

这些内容都属于业务规则，所以放在 ServiceImpl 合理。

### 3. Mapper 层

新增：

```text
mapper/OrderMapper.java
mapper/TicketMapper.java
resources/mapper/OrderMapper.xml
resources/mapper/TicketMapper.xml
```

`OrderMapper` 只查订单。
`TicketMapper` 负责工单查询、工单写入、工单事件写入。

这里要注意：

```text
Mapper 不是 Service。
Mapper 不处理业务判断。
Mapper 只表达数据库访问动作。
```

### 4. Entity 层

新增：

```text
entity/Order.java
entity/Ticket.java
entity/OrderStatus.java
entity/PaymentStatus.java
entity/TicketCategory.java
entity/TicketPriority.java
entity/TicketStatus.java
```

`Order` 和 `Ticket` 改成 JavaBean，是为了更自然地配合 MyBatis。

枚举仍然保留，是因为请求 DTO 里需要稳定枚举约束：

```text
category 只能是 logistics / refund / quality / account / other。
priority 只能是 low / normal / high / urgent。
```

这属于接口输入边界，不能因为换持久层就放松。

### 5. DTO 层

新增：

```text
dto/CreateTicketCommand.java
dto/OrderToolView.java
dto/TicketToolView.java
```

DTO 仍然负责 AI 工具契约。

`OrderToolView` 不暴露：

```text
ownerUserId
tenantId
```

`TicketToolView` 不暴露：

```text
idempotencyKey
requestFingerprint
createdTraceId
description 全量内部字段
```

这就是字段白名单。

### 6. Config 和 Exception

新增：

```text
config/InternalApiProperties.java
config/RedisFeatureProperties.java
config/MyBatisConfig.java

exception/BusinessErrorCode.java
exception/BusinessException.java
exception/GlobalExceptionHandler.java
```

这样比旧的 `common/error`、`common/security/InternalApiProperties` 更接近传统项目。

异常层仍然负责：

```text
业务错误码。
HTTP 状态码。
统一错误响应。
trace_id 回传。
```

### 7. Common 层

`common` 里保留的是跨层通用能力：

```text
ApiResponse
cache
rate
redis
security
trace
```

这里不是所有东西都必须塞进一个 `common` 包。
本项目目前这样放，是为了让传统结构和已有代码之间保持平衡。

## 本节常见问题

### 1. 为什么不直接照搬你以前的包名 `com/example/orderservice`

因为当前项目名是：

```text
com.panpan.aibusinessservice
```

包名应该表达当前项目归属。
目录结构可以传统化，但包名前缀不用改成示例包。

### 2. 为什么 Mapper 不写注解 SQL，而写 XML

MyBatis 两种方式都支持：

```text
注解 SQL：适合很短的 SQL。
XML SQL：适合传统企业项目和复杂 SQL。
```

你以前更熟悉 Mapper XML，所以本节直接使用 XML。

### 3. 为什么不再保留内存 Repository

因为现在阶段 7 的方向已经是真实 Java Spring Boot + MySQL/Redis。
继续保留内存 Repository 会让学习重点变散。

测试依然不用真实 MySQL，而是使用 H2 内存数据库。
这和“内存 Repository”不是一回事：

```text
H2 是数据库测试替身。
内存 Repository 是另一套代码实现。
```

本节选择 H2，是为了测试仍然覆盖 MyBatis SQL 链路。

### 4. 为什么 Redis 缓存也要改代码

因为 `Order` 从 record 变成了 JavaBean。

旧写法：

```java
order.orderId()
```

新写法：

```java
order.getOrderId()
```

这是 Java 对象风格变化，不是业务变化。

### 5. 为什么编译时曾出现 `\ufeff` 非法字符

这是 UTF-8 BOM 问题。

前面批量移动和改包名时，PowerShell 写文件可能把 BOM 写到了 Java 文件开头。
`javac` 会把这个字符当成非法字符。

处理方式是：

```text
用 UTF-8 without BOM 重新保存 Java 文件。
```

注意这和你之前提醒的中文显示乱码不是一回事。
如果只是 PowerShell 显示中文乱码，不能乱改文件。
这次是编译器明确报了非法字符，所以是真实文件编码问题。

## 本节练习

### 练习 1：按职责分类

把下面内容放入正确层：

```text
接收 POST /internal/tickets
校验 Idempotency-Key
INSERT INTO tickets
返回 ticket_id / ticket_status
读取 app.redis.enabled
把业务异常转成 JSON 响应
```

参考答案：

```text
接收 POST /internal/tickets：controller
校验 Idempotency-Key：service.impl
INSERT INTO tickets：mapper + mapper XML
返回 ticket_id / ticket_status：dto
读取 app.redis.enabled：config
把业务异常转成 JSON 响应：exception
```

### 练习 2：解释 Entity 和 DTO

问题：

```text
为什么不能直接把 Ticket Entity 返回给 AI 模型？
```

参考答案：

```text
因为 Ticket Entity 是内部数据对象，包含 idempotencyKey、requestFingerprint、createdTraceId、tenantId 等内部字段。
这些字段不一定应该暴露给模型。
AI 工具响应必须是白名单 DTO，只暴露模型回答用户需要的字段。
```

### 练习 3：解释 Mapper 和 Service

问题：

```text
为什么用户是否能查看订单的判断不能放在 OrderMapper.xml 里？
```

参考答案：

```text
Mapper XML 负责数据库访问。
权限判断属于业务规则，应该放在 Service。
如果把权限规则散落到 SQL 里，后续规则变化会难维护，也不利于复用和测试。
```

### 练习 4：解释 MyBatis 绑定关系

问题：

```text
OrderMapper.java 的 selectByTenantIdAndOrderId 和 OrderMapper.xml 是怎么对应起来的？
```

参考答案：

```text
OrderMapper.xml 的 namespace 指向 com.panpan.aibusinessservice.mapper.OrderMapper。
XML 里的 select id 是 selectByTenantIdAndOrderId。
namespace + id 就对应到 Java Mapper 接口里的同名方法。
```

### 练习 5：解释本节没有改变的业务边界

问题：

```text
本节从 JdbcTemplate 切到 MyBatis 后，AI Agent 调用 Java 服务的安全边界哪些不能变？
```

参考答案：

```text
internal token 不能变。
trace_id 传递不能变。
用户身份和租户边界不能变。
订单权限校验不能变。
创建工单必须有 Idempotency-Key 不能变。
MySQL 唯一索引作为幂等兜底不能变。
返回给模型的 DTO 白名单不能变。
```

## 自测题

### 自测 1：Controller 可以直接调用 Mapper 吗？

参考答案：

```text
技术上可以，但不推荐。
Controller 直接调用 Mapper 会绕过 Service 业务层，导致权限、幂等、事务、错误码等规则容易分散。
传统项目里应该让 Controller 调 Service，Service 再调 Mapper。
```

### 自测 2：Service 接口一定必须有吗？

参考答案：

```text
不是绝对必须。
小项目可以 Controller 直接依赖 ServiceImpl。
但传统企业项目经常保留 Service 接口，用来表达业务能力边界、方便替换实现、方便测试和协作。
本项目为了贴近你的项目习惯，保留接口 + impl。
```

### 自测 3：MyBatis 的 `resultMap` 主要解决什么问题？

参考答案：

```text
解决数据库列和 Java 属性之间的映射问题。
例如数据库 user_id 可以映射到 Java 的 ownerUserId。
它让 SQL 查询结果如何变成 Entity 更清楚。
```

### 自测 4：为什么测试环境用 H2 仍然有价值？

参考答案：

```text
因为 H2 虽然不是 MySQL，但它仍然会跑数据库初始化、MyBatis Mapper、SQL 查询和写入链路。
它比纯 mock 更接近真实数据库访问。
同时它不依赖本机真实 MySQL，适合自动化测试。
```

### 自测 5：为什么这节不能顺手改 Python AI 服务？

参考答案：

```text
因为本节目标是稳定 Java 服务内部结构。
如果同时改 Python 对接，很难判断问题来自 Java 重构、MyBatis SQL、HTTP 契约还是 Python client。
先让 Java 服务结构稳定，下一步再学 Python 对接更清晰。
```

## 本节总结

这一节完成的是一次“结构对齐”：

```text
旧结构：interfaces/application/domain/infrastructure
新结构：controller/service/service.impl/mapper/entity/dto/config/exception/common
```

也完成了一次“持久层对齐”：

```text
旧方式：JdbcTemplate + RowMapper
新方式：MyBatis Mapper + XML + resultMap
```

更重要的是，AI Agent 调用 Java 后端的安全边界没有变：

```text
模型只提出意图。
Python 负责工具调用编排。
Java Service 负责业务执行和安全兜底。
MySQL 保存最终业务事实。
Redis 只做加速和保护。
DTO 白名单控制模型能看到什么。
```

下一节进入：

```text
阶段 7 第 8 节：AI 场景下的内部鉴权和用户身份传递
```

这一节会继续基于新的传统结构讲：

```text
Python AI 服务调用 Java internal API 时，header 应该怎么设计。
内部 token、caller、user_id、tenant_id 各自代表什么。
Java 后端为什么不能相信模型直接传来的权限结论。
```
