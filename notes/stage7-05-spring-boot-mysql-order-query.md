# 阶段 7 第 5 节：Spring Boot 接入 MySQL，订单查询读工具真实化第一步

## 本节定位

上一节我们只做了数据库设计。

上一节的重点是回答：

```text
Java 业务服务将来应该有哪些表？
订单表应该有哪些字段？
为什么要 tenant_id？
为什么订单属于 user_id？
为什么唯一索引不能只看 order_id？
MySQL 和 Redis 该怎么分工？
```

这一节开始真正接 MySQL。

但这一节仍然只做一件事：

```text
让 Java 业务服务的订单查询接口从真实 MySQL 读取 orders 表。
```

也就是说，原来：

```text
GET /internal/orders/{order_id}
-> Controller
-> OrderQueryService
-> InMemoryOrderRepository
-> Map 里的假数据
```

现在变成：

```text
GET /internal/orders/{order_id}
-> Controller
-> OrderQueryService
-> JdbcOrderRepository
-> JdbcTemplate
-> MySQL orders 表
```

这是阶段 7 从“服务骨架”走向“真实 Java 业务服务”的第一步。

---

## 一、本节学习目标

学完本节，你应该能解释清楚：

```text
Spring Boot 为什么能连接 MySQL。
MySQL Driver 是什么。
JDBC 是什么。
DataSource 是什么。
HikariCP 连接池是什么。
JdbcTemplate 帮我们省掉了哪些重复代码。
Repository 接口为什么能让内存实现换成 MySQL 实现。
RowMapper 为什么负责把 ResultSet 转成领域对象。
schema.sql 和 data.sql 是什么。
为什么本地真实运行用 MySQL，自动化测试却用 H2。
为什么测试环境 application.yml 会覆盖主配置。
为什么不能把 MySQL 密码直接提交到 Git。
为什么 Controller 不应该因为换数据库而大改。
```

本节完成后，Java 服务会具备一个真实能力：

```text
订单查询读工具已经可以从 MySQL 读取业务数据。
```

但是要注意：

```text
本节还没有把创建工单写入 MySQL。
本节还没有接 Redis。
本节还没有让 Python AI 服务切换到这个 Java business service。
本节还没有做完整用户表和工单事件表落地。
```

这些会放到后面的课程里。

---

## 二、本节先不做什么

为了让学习边界清楚，本节不提前做这些：

```text
不接 MyBatis。
不写复杂多表查询。
不做完整 users 表落地。
不做 tickets 表落地。
不做 ticket_events 表落地。
不做 Redis 缓存。
不做分布式事务。
不做 Docker MySQL。
不改 Python AI 服务调用链路。
```

为什么不先上 MyBatis？

因为这一节的重点是让你看懂 Spring Boot 连接数据库的基本机制。

`JdbcTemplate` 比 MyBatis 更直接：

```text
SQL 写在哪里，你看得见。
参数怎么传，你看得见。
查询结果怎么转成 Java 对象，你看得见。
Repository 如何替换实现，你看得见。
```

等你理解这个过程后，再学 MyBatis 时，你会知道 MyBatis 帮你封装的是哪一层。

---

## 三、基础知识铺垫

### 1. MySQL 在 Java 服务里扮演什么角色

MySQL 是长期业务事实存储。

所谓长期业务事实，就是系统不能随便丢的业务数据：

```text
订单属于谁。
订单现在是什么状态。
订单是否已支付。
物流当前是什么情况。
这个订单能不能创建工单。
工单是谁创建的。
工单有没有经过用户确认。
```

在 AI Agent 项目里，MySQL 不是直接给模型用的。

正确链路是：

```text
模型提出工具调用意图
-> Python AI 服务校验工具名和参数
-> Python 调 Java internal API
-> Java 校验身份、租户、权限和业务规则
-> Java 读写 MySQL
-> Java 返回字段白名单 DTO
-> Python 再交给模型组织回答
```

这意味着：

```text
模型不直接连接 MySQL。
模型不写 SQL。
模型不拿数据库密码。
模型不看 Entity 全字段。
```

Java 服务是模型和数据库之间的业务边界。

---

### 2. JDBC 是什么

JDBC 全称是 Java Database Connectivity。

你可以先把它理解成：

```text
Java 官方定义的一套访问数据库的标准接口。
```

Java 程序不应该直接依赖某一个数据库厂商的私有调用方式。

所以 Java 定义了一组统一接口，例如：

```text
Connection
PreparedStatement
ResultSet
DataSource
```

不同数据库厂商负责提供自己的 JDBC Driver。

比如：

```text
MySQL 提供 mysql-connector-j。
PostgreSQL 提供 PostgreSQL JDBC Driver。
Oracle 提供 Oracle JDBC Driver。
```

这样 Java 代码可以通过统一的 JDBC 接口访问不同数据库。

---

### 3. MySQL Driver 是什么

本节在 `pom.xml` 里新增了：

```xml
<dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
    <scope>runtime</scope>
</dependency>
```

它就是 MySQL 的 JDBC Driver。

作用是：

```text
把 Java 的 JDBC 调用转换成 MySQL 能理解的网络协议。
```

为什么 scope 是 `runtime`？

因为我们的业务代码里没有直接写：

```java
com.mysql.cj.jdbc.Driver
```

代码主要依赖的是 JDBC/Spring 抽象。

MySQL Driver 主要在运行时被 Spring Boot 加载，用来真正连接 MySQL。

---

### 4. DataSource 是什么

`DataSource` 可以理解成：

```text
数据库连接的来源。
```

Java 代码要查数据库，最终需要连接。

但是每次请求都临时创建一个数据库连接，再用完关闭，成本很高。

所以真实项目里通常不是直接创建连接，而是用连接池。

Spring Boot 里配置了：

```yaml
spring:
  datasource:
    url: ...
    username: ...
    password: ...
```

Spring Boot 就会根据这些配置创建一个 `DataSource`。

后面的 `JdbcTemplate` 会从 `DataSource` 里拿连接去执行 SQL。

---

### 5. HikariCP 是什么

你在测试和启动日志里会看到：

```text
HikariPool-1 - Starting...
HikariPool-1 - Start completed.
```

HikariCP 是 Spring Boot 默认使用的数据库连接池。

连接池解决的问题是：

```text
提前维护一批数据库连接。
请求来了从池里借一个连接。
SQL 执行完把连接还回池里。
不用每次请求都重新建立 TCP 连接和数据库会话。
```

连接池不是业务功能，但它是后端服务稳定性的基础。

如果没有连接池，高并发下数据库连接创建和销毁会非常浪费。

---

### 6. JdbcTemplate 是什么

如果你直接写 JDBC，代码通常会很繁琐：

```text
打开连接。
创建 PreparedStatement。
设置参数。
执行 SQL。
遍历 ResultSet。
把每一行转成 Java 对象。
处理异常。
关闭资源。
```

`JdbcTemplate` 是 Spring 提供的一个轻量工具。

它帮你处理大量重复代码：

```text
连接获取
PreparedStatement 创建
参数绑定
ResultSet 遍历
异常转换
资源释放
```

你主要关心两件事：

```text
SQL 怎么写。
一行查询结果怎么转成 Java 对象。
```

所以本节新增了：

```text
JdbcOrderRepository
OrderRowMapper
```

---

### 7. Repository 是什么

Repository 是领域层访问数据的抽象。

你可以先这样理解：

```text
Service 不应该关心数据到底来自内存、MySQL、Redis 还是远程接口。
Service 只关心：我能不能根据业务条件拿到一个 Order。
```

所以我们保留了接口：

```java
public interface OrderRepository {
    Optional<Order> findByTenantIdAndOrderId(String tenantId, String orderId);
}
```

它表达的是业务需要：

```text
按租户和订单号查订单。
```

而不是表达技术细节：

```text
用 Map 查。
用 SQL 查。
用 MyBatis 查。
用 JPA 查。
```

本节真正替换的是接口背后的实现。

---

### 8. RowMapper 是什么

数据库查询返回的是一行一行的数据。

JDBC 里叫 `ResultSet`。

但是业务代码不应该一直拿 `ResultSet` 到处传。

业务代码更应该拿到：

```text
Order
```

所以需要一个转换器：

```text
ResultSet 一行
-> Order 领域对象
```

Spring JDBC 里这个转换器叫 `RowMapper<T>`。

本节新增：

```text
OrderRowMapper
```

它负责：

```text
order_id -> Order.orderId
user_id -> Order.ownerUserId
tenant_id -> Order.tenantId
order_status -> OrderStatus
payment_status -> PaymentStatus
can_create_ticket -> boolean
```

这就是数据库行到领域对象的映射。

---

### 9. schema.sql 是什么

`schema.sql` 是建表脚本。

本节新增：

```text
src/main/resources/schema.sql
```

里面创建 `orders` 表。

Spring Boot 配置了：

```yaml
spring:
  sql:
    init:
      mode: always
```

启动时，Spring Boot 会尝试执行 `schema.sql`。

本节的 `schema.sql` 使用：

```sql
CREATE TABLE IF NOT EXISTS orders (...)
```

意思是：

```text
如果 orders 表不存在，就创建。
如果已经存在，就不重复创建。
```

这对学习阶段很方便。

真实生产项目后续更常用 Flyway 或 Liquibase 管理数据库迁移，本节先不展开。

---

### 10. data.sql 是什么

`data.sql` 是初始化数据脚本。

本节新增：

```text
src/main/resources/data.sql
```

它插入三条订单数据：

```text
A1001：属于 U1001，已发货，可以创建工单。
A1002：属于 U1001，等待发货，可以创建工单。
A2001：属于 U2001，已签收，不允许创建工单。
```

这些数据和之前内存 Repository 里的数据保持一致。

这样做的目的：

```text
接口行为不变。
数据来源从内存换成 MySQL。
测试仍然能验证原来的业务边界。
```

---

### 11. 为什么用环境变量保存密码

本节没有把你的 MySQL 密码直接写进 Git。

配置里写的是：

```yaml
password: ${JAVA_BUSINESS_DB_PASSWORD:}
```

意思是：

```text
优先读取 JAVA_BUSINESS_DB_PASSWORD 环境变量。
如果环境变量不存在，就用空字符串。
```

本地运行时你可以临时设置：

```powershell
$env:JAVA_BUSINESS_DB_PASSWORD = "你的 MySQL 密码"
```

为什么不直接提交密码？

因为真实项目里：

```text
数据库密码属于敏感信息。
Git 仓库会被别人看到。
CI 日志、PR、备份、镜像都可能扩散这个密码。
```

即使你现在是本地学习项目，也要养成这个习惯。

---

### 12. 为什么测试不用你的真实 MySQL

本节自动化测试使用 H2 内存数据库。

测试配置在：

```text
src/test/resources/application.yml
```

里面配置的是：

```yaml
spring:
  datasource:
    driver-class-name: org.h2.Driver
    url: jdbc:h2:mem:ai_business_test;MODE=MySQL;DATABASE_TO_UPPER=false;DB_CLOSE_DELAY=-1
```

原因：

```text
自动化测试不应该依赖你电脑上有没有 MySQL。
自动化测试不应该依赖你的 MySQL 密码。
自动化测试不应该污染真实数据库。
H2 内存库启动快，测试结束数据自动消失。
```

但是测试仍然走 `JdbcOrderRepository`。

也就是说：

```text
测试没有退回内存 Repository。
测试仍然验证 JDBC 查询链路。
只是底层数据库从 MySQL 换成了 H2。
```

---

### 13. 测试配置为什么会覆盖主配置

本节调试时遇到一个真实问题：

```text
src/test/resources/application.yml 覆盖了部分主配置。
```

一开始测试配置只写了 datasource。

结果丢了两个关键配置：

```text
spring.jackson.property-naming-strategy: SNAKE_CASE
app.internal.token: local-dev-internal-token
```

造成两个问题：

```text
confirmation_id 无法映射到 confirmationId，工单请求变成 422。
app.internal.token 为空，internal token 校验出现 NPE。
```

修复方式是：

```text
测试配置里补上测试必须依赖的配置。
```

这个问题很值得记住。

真实项目里，测试配置、dev 配置、prod 配置经常不完全一样。

你要知道：

```text
换环境不仅会换数据库，也可能换掉序列化、鉴权、日志、缓存等配置。
```

---

## 四、本节主题系统讲解

### 1. 本节架构变化

第 4 节之后，Java 服务有数据库设计，但没有真正读库。

第 5 节之后，订单查询链路变成：

```text
HTTP 请求
-> InternalOrderController
-> InternalRequestResolver
-> OrderQueryService
-> OrderRepository 接口
-> JdbcOrderRepository
-> JdbcTemplate
-> orders 表
-> OrderRowMapper
-> Order 领域对象
-> OrderToolView
-> ApiResponse
```

你可以注意：

```text
Controller 没有因为接 MySQL 而大改。
OrderQueryService 没有直接写 SQL。
SQL 被限制在 infrastructure/persistence 层。
返回给 AI 的仍然是 OrderToolView。
```

这说明我们的边界是对的。

---

### 2. 为什么 Controller 不应该知道 MySQL

Controller 的职责是处理 HTTP。

它应该关心：

```text
URL 是什么。
PathVariable 是什么。
Header 怎么取。
请求怎么交给 Service。
响应怎么包成 ApiResponse。
```

它不应该关心：

```text
订单存在 MySQL 还是内存。
SQL 怎么写。
字段怎么映射。
连接池怎么拿连接。
```

所以本节没有大改 `InternalOrderController`。

这是一个重要信号：

```text
如果换数据库导致 Controller 大量变化，通常说明分层边界不干净。
```

---

### 3. 为什么 Service 仍然保留权限判断

`OrderQueryService` 里仍然保留：

```text
订单号格式校验。
订单不存在处理。
用户是否有权查看订单。
DTO 白名单转换。
```

即使数据来自 MySQL，这些业务规则也不能消失。

本节的查询方式是：

```text
按 tenant_id + order_id 查订单。
再判断 ownerUserId 是否等于当前 userId。
```

为什么不是只按 order_id 查？

因为多租户系统里，不同租户可能有相同订单号。

为什么不是直接按 tenant_id + user_id + order_id 查？

因为当前接口测试希望区分：

```text
订单不存在 -> ORDER_NOT_FOUND
订单存在但不属于你 -> ORDER_ACCESS_DENIED
```

所以本节选择：

```text
先限制租户，再判断用户归属。
```

这样既保留租户边界，也保留“无权访问”的业务错误码。

---

### 4. 为什么 Repository 方法要改名

之前接口是：

```java
Optional<Order> findByOrderId(String orderId);
```

本节改成：

```java
Optional<Order> findByTenantIdAndOrderId(String tenantId, String orderId);
```

这个改动很重要。

它不是为了代码好看，而是为了让数据访问层从接口上表达真实业务边界：

```text
订单查询不是全局按订单号查。
订单查询必须带租户。
```

如果接口还是 `findByOrderId`，后续很容易有人写出危险代码：

```sql
SELECT * FROM orders WHERE order_id = ?
```

这在多租户系统里是不安全的。

所以接口名字本身也是一种约束。

---

### 5. JdbcOrderRepository 做了什么

新增文件：

```text
src/main/java/.../infrastructure/persistence/JdbcOrderRepository.java
```

它的职责是：

```text
实现 OrderRepository。
使用 JdbcTemplate 查询 orders 表。
把 SQL 参数绑定到 PreparedStatement。
把查询结果交给 OrderRowMapper。
返回 Optional<Order>。
```

核心 SQL：

```sql
SELECT
  order_id,
  user_id,
  tenant_id,
  order_status,
  payment_status,
  logistics_message,
  latest_event,
  can_create_ticket
FROM orders
WHERE tenant_id = ? AND order_id = ?
```

这里的 `?` 是占位符。

它不是字符串拼接。

正确写法是：

```text
SQL 里写 ?
参数单独传给 JdbcTemplate
```

这样可以避免 SQL 注入。

---

### 6. OrderRowMapper 做了什么

新增文件：

```text
src/main/java/.../infrastructure/persistence/OrderRowMapper.java
```

它把数据库行转换成领域对象：

```text
ResultSet
-> Order
```

字段映射关系：

| 数据库字段 | Java 领域字段 |
| --- | --- |
| `order_id` | `orderId` |
| `user_id` | `ownerUserId` |
| `tenant_id` | `tenantId` |
| `order_status` | `OrderStatus` |
| `payment_status` | `PaymentStatus` |
| `logistics_message` | `logisticsMessage` |
| `latest_event` | `latestEvent` |
| `can_create_ticket` | `canCreateTicket` |

注意：

```text
数据库里的 order_status 是字符串。
Java 领域模型里是 OrderStatus 枚举。
```

所以本节给枚举补了：

```text
OrderStatus.fromCode
PaymentStatus.fromCode
```

这样数据库里的 `shipped` 可以转成 Java 里的 `OrderStatus.SHIPPED`。

---

### 7. 为什么保留 InMemoryOrderRepository

本节没有删除内存实现。

而是加了条件：

```java
@ConditionalOnProperty(name = "app.persistence.orders", havingValue = "memory")
```

意思是：

```text
只有配置 app.persistence.orders=memory 时，才启用内存订单 Repository。
```

同时 `JdbcOrderRepository` 是：

```java
@ConditionalOnProperty(name = "app.persistence.orders", havingValue = "mysql", matchIfMissing = true)
```

意思是：

```text
默认使用 mysql 实现。
如果显式配置 memory，才切回内存实现。
```

这个设计有两个好处：

```text
主线开始走真实 MySQL。
需要临时演示或排查时，还可以切回内存实现。
```

---

### 8. 为什么自动初始化只落地 orders 表

上一节设计了四张表：

```text
users
orders
tickets
ticket_events
```

但本节 `schema.sql` 只创建了 `orders` 表。

这是刻意控制节奏。

因为本节只真实化订单查询读工具。

如果同时落地四张表，会把学习重点冲散：

```text
你既要学 DataSource。
又要学 JdbcTemplate。
又要学订单查询。
又要学工单事务。
又要学事件表。
又要学幂等写入。
```

这样不利于真正理解。

所以本节先把读链路打通。

下一节再做写链路：

```text
创建工单 -> tickets 表 -> ticket_events 表 -> 事务
```

---

### 9. 为什么真实 MySQL 和测试 H2 都能走同一套代码

本节测试用 H2，但代码用的还是：

```text
JdbcOrderRepository
JdbcTemplate
schema.sql
data.sql
```

原因是 JDBC 抽象隐藏了底层数据库差异。

只要 SQL 语法兼容，代码可以连接：

```text
MySQL
H2
PostgreSQL
```

当然，真实项目里不同数据库的 SQL 方言会有差异。

本节为了减少差异，使用了比较简单的建表和插入语句。

---

### 10. 本节真实 MySQL smoke 验证了什么

本节已经在 Windows MySQL 上验证过：

```text
MySQL 8.0.41 可用。
MySQL 服务 MySQL80 正在运行。
ai_business 数据库已创建。
Java 服务能通过 HikariCP 连接 MySQL。
GET /internal/orders/A1001 能返回订单数据。
```

启动日志里能看到：

```text
HikariPool-1 - Added connection com.mysql.cj.jdbc.ConnectionImpl
Tomcat started on port 18002
```

这说明运行时连接的是 MySQL，不是 H2。

接口返回里 PowerShell 显示过中文乱码。

后续用 Python 检查 Unicode 码点，确认实际响应内容是正确中文。

所以本节再次验证了一个经验：

```text
看到中文乱码时，先怀疑 PowerShell 输出编码或显示层，不要立刻大规模改源码或数据库。
```

---

## 五、本节代码变更讲解

### 1. `pom.xml`

新增：

```text
spring-boot-starter-jdbc
mysql-connector-j
h2
```

它们分别负责：

| 依赖 | 作用 |
| --- | --- |
| `spring-boot-starter-jdbc` | 提供 DataSource、JdbcTemplate、事务基础能力 |
| `mysql-connector-j` | MySQL JDBC Driver，运行时连接 MySQL |
| `h2` | 测试环境内存数据库 |

这一节不是单纯加依赖。

你要知道每个依赖进入项目后的职责：

```text
starter-jdbc 让 Spring Boot 能自动创建 JdbcTemplate。
mysql-connector-j 让 DataSource 能连 MySQL。
h2 让测试能在没有真实 MySQL 的情况下跑数据库链路。
```

---

### 2. `application.yml`

新增主配置：

```yaml
spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: ${JAVA_BUSINESS_DB_URL:jdbc:mysql://127.0.0.1:3306/ai_business?...}
    username: ${JAVA_BUSINESS_DB_USERNAME:root}
    password: ${JAVA_BUSINESS_DB_PASSWORD:}
  sql:
    init:
      mode: always
      encoding: UTF-8

app:
  persistence:
    orders: ${JAVA_BUSINESS_ORDER_PERSISTENCE:mysql}
```

这段配置表达三件事：

```text
默认连接 Windows 本机 MySQL 的 ai_business 数据库。
密码从环境变量读取。
订单 Repository 默认使用 mysql 实现。
```

你本地启动前需要设置：

```powershell
$env:JAVA_BUSINESS_DB_PASSWORD = "你的 MySQL 密码"
```

---

### 3. `OrderRepository`

从：

```java
Optional<Order> findByOrderId(String orderId);
```

改成：

```java
Optional<Order> findByTenantIdAndOrderId(String tenantId, String orderId);
```

这体现阶段 7 的核心要求：

```text
AI Agent 调业务系统时，不能绕过租户边界。
```

---

### 4. `OrderQueryService`

现在调用：

```text
orderRepository.findByTenantIdAndOrderId(context.tenantId(), orderId)
```

Service 仍然负责：

```text
校验订单号格式。
处理订单不存在。
校验用户是否能看这个订单。
转换成 OrderToolView。
```

换数据库没有改变业务规则。

这就是分层的价值。

---

### 5. `TicketApplicationService`

创建工单时，如果带了关联订单：

```text
也要按 tenant_id + order_id 查订单。
```

因为工单写操作也不能跨租户校验订单。

虽然本节还没有把工单写入 MySQL，但它已经复用了真实订单查询边界。

---

### 6. `JdbcOrderRepository`

这是本节最核心的新类。

它属于：

```text
infrastructure/persistence
```

也就是基础设施层。

它知道：

```text
表名叫 orders。
字段叫 order_id、user_id、tenant_id。
SQL 怎么写。
JdbcTemplate 怎么查。
```

它不应该决定：

```text
用户有没有权限。
接口返回什么字段。
模型能不能看到某个字段。
```

这些仍然在 Service 和 DTO 层。

---

### 7. `OrderRowMapper`

它是数据库行到领域对象的转换器。

这个类虽然小，但很重要。

因为它把数据库表示和 Java 表示隔离开：

```text
数据库：order_status = 'shipped'
Java：OrderStatus.SHIPPED
```

以后如果数据库字段名变化，通常先改 Mapper，而不是让所有业务代码一起变化。

---

### 8. `schema.sql` 和 `data.sql`

这两个文件让本地启动和测试都能自动准备基础订单数据。

本节不是为了让它们替代正式迁移工具。

它们的学习价值是：

```text
让你看到数据库表如何真正和 Java 代码对应。
让你可以本地快速跑通真实 MySQL。
让测试环境有可控的初始数据。
```

---

### 9. `src/test/resources/application.yml`

测试配置补了：

```yaml
spring:
  jackson:
    property-naming-strategy: SNAKE_CASE
app:
  internal:
    token: local-dev-internal-token
```

这次调试告诉我们：

```text
测试配置不是只写 datasource 就完了。
只要测试依赖某个配置，就要在测试配置中保证它存在。
```

这也是实际工作中很常见的坑。

---

## 六、现在的 Java 服务结构

这一节之后，订单查询已经很接近传统 Spring Boot 分层：

```text
interfaces/internal/InternalOrderController
-> application/service/OrderQueryService
-> domain/repository/OrderRepository
-> infrastructure/persistence/JdbcOrderRepository
-> JdbcTemplate
-> MySQL orders
```

它和传统三层的对应关系大致是：

| 当前项目 | 传统说法 |
| --- | --- |
| `interfaces/internal` | Controller |
| `application/service` | Service |
| `domain/repository` | Repository 接口 |
| `infrastructure/persistence` | Mapper/DAO/Repository 实现 |
| `schema.sql` | 表结构 |
| `data.sql` | 初始化数据 |

如果后续换成 MyBatis，结构可能变成：

```text
Controller
-> Service
-> Repository
-> MyBatis Mapper
-> MySQL
```

但本节先用 JdbcTemplate 帮你看清楚底层逻辑。

---

## 七、本地运行方式

### 1. 确认 MySQL 可用

```powershell
mysql --version
```

本节已确认你的 Windows MySQL 是：

```text
MySQL 8.0.41
```

### 2. 创建数据库

```powershell
$env:MYSQL_PWD = "你的 MySQL 密码"
mysql -u root -h 127.0.0.1 -P 3306 -e "CREATE DATABASE IF NOT EXISTS ai_business DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
```

### 3. 设置 Java 服务数据库密码

```powershell
$env:JAVA_BUSINESS_DB_PASSWORD = "你的 MySQL 密码"
```

### 4. 启动 Java 服务

```powershell
cd D:\wendang\java+python+ai\projects\java-business-service
mvn spring-boot:run
```

默认端口：

```text
8002
```

### 5. 查询订单

```powershell
curl.exe "http://127.0.0.1:8002/internal/orders/A1001" ^
  -H "X-Trace-Id: trace-local-test" ^
  -H "X-Caller: ai-service" ^
  -H "X-User-Id: U1001" ^
  -H "X-Tenant-Id: default" ^
  -H "X-Internal-Token: local-dev-internal-token"
```

PowerShell 里如果多行命令不方便，也可以写成一行。

---

## 八、本节重要测试

本节最重要的测试不是“能不能启动”，而是这几类：

```text
订单查询成功。
查询别人的订单返回 ORDER_ACCESS_DENIED。
缺少 internal token 返回 INTERNAL_AUTH_FAILED。
创建工单时关联订单仍然能走真实订单查询。
测试环境使用 H2，但仍然走 JdbcOrderRepository。
```

本节已运行：

```text
mvn test
```

结果：

```text
Tests run: 8, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

本节还做了真实 MySQL smoke：

```text
启动 Java 服务
连接 Windows MySQL
调用 GET /internal/orders/A1001
返回 success=true
```

---

## 九、常见误区

### 误区 1：接了 MySQL 就是完整真实项目

不是。

本节只真实化了订单查询读链路。

还没完成：

```text
工单写入 MySQL。
工单事件表。
Redis 幂等。
真实用户权限。
Python AI 服务切换调用 java-business-service。
```

---

### 误区 2：测试也应该连本机 MySQL

一般不建议。

自动化测试应该稳定、可重复、容易在 CI 跑。

所以本节使用 H2。

但测试仍然走 JDBC Repository，不是退回假实现。

---

### 误区 3：看到中文乱码就改数据库字符集

不要急。

本节 smoke 时，PowerShell 输出里出现过中文乱码。

但 Python 检查实际响应后确认 Unicode 内容正确。

所以正确排查顺序是：

```text
先确认实际字节和 Unicode 是否正确。
再判断是终端显示问题、HTTP 编码问题、数据库编码问题，还是源文件编码问题。
```

不要一看到乱码就大范围改源码和数据库。

---

### 误区 4：Repository 只是 Mapper 的别名

不完全是。

Mapper 通常更贴近 SQL 映射。

Repository 更贴近领域需要。

本节的 `OrderRepository` 表达：

```text
我要按租户和订单号拿订单。
```

`JdbcOrderRepository` 才表达：

```text
我用 SQL 从 orders 表拿订单。
```

后面如果换 MyBatis，可以在 infrastructure 层增加 MyBatis Mapper。

领域层接口不需要跟着 MyBatis 细节变化。

---

### 误区 5：测试配置只是主配置的补充

不一定。

本节一开始测试失败，就是因为测试配置覆盖后丢了主配置里的部分关键项。

你要养成习惯：

```text
新增测试 application.yml 后，检查测试所需的 jackson、鉴权、业务开关等配置是否还在。
```

---

## 十、本节练习

### 练习 1：解释 `spring.datasource.url` 的作用

参考答案：

```text
spring.datasource.url 告诉 Spring Boot 数据库在哪里、使用什么协议连接、连接哪个库，以及一些连接参数。
例如 jdbc:mysql://127.0.0.1:3306/ai_business 表示使用 MySQL JDBC 协议连接本机 3306 端口上的 ai_business 数据库。
```

### 练习 2：为什么 `JAVA_BUSINESS_DB_PASSWORD` 不应该写死在配置文件里？

参考答案：

```text
数据库密码属于敏感信息。如果直接写死并提交到 Git，别人可以通过仓库、历史提交、CI 日志或备份看到密码。
使用环境变量可以让代码和秘密分离，仓库保存配置模板，真实密码留在本机或部署环境中。
```

### 练习 3：`JdbcTemplate` 帮我们省掉了哪些重复代码？

参考答案：

```text
JdbcTemplate 帮我们处理连接获取、PreparedStatement 创建、参数绑定、SQL 执行、ResultSet 遍历、异常转换和资源释放。
业务代码主要负责写 SQL，并提供 RowMapper 把查询结果转成 Java 对象。
```

### 练习 4：为什么 `OrderRepository` 要改成按 `tenantId + orderId` 查询？

参考答案：

```text
因为订单查询必须带租户边界。只按 orderId 查询，在多租户系统里可能查到其他租户的数据。
把 tenantId 放进 Repository 方法签名，相当于从接口层面强制所有实现都考虑租户隔离。
```

### 练习 5：`OrderRowMapper` 的职责是什么？

参考答案：

```text
OrderRowMapper 负责把数据库 ResultSet 的一行记录转换成 Order 领域对象。
它处理字段名映射、字符串状态转枚举、TINYINT/boolean 转换等数据库表示到 Java 表示的转换工作。
```

### 练习 6：为什么测试环境用 H2，而不是直接用你的 Windows MySQL？

参考答案：

```text
测试应该稳定、可重复、容易在不同机器和 CI 环境执行。
如果测试依赖本机 MySQL、真实密码和真实数据，就容易因为环境不同失败，也可能污染本地数据。
H2 内存库启动快、隔离性好，适合自动化测试。
```

### 练习 7：为什么测试配置里要补 `spring.jackson.property-naming-strategy: SNAKE_CASE`？

参考答案：

```text
因为接口 JSON 使用 snake_case，例如 confirmation_id，而 Java record 字段是 confirmationId。
如果测试配置丢了 SNAKE_CASE，Jackson 就不能把 confirmation_id 正确映射到 confirmationId，Bean Validation 会认为字段为空，返回 422。
```

### 练习 8：为什么本节没有把 tickets 表也落地？

参考答案：

```text
本节目标是订单查询读工具真实化。只落地 orders 表可以集中学习 DataSource、JdbcTemplate、Repository 替换和读链路。
tickets 和 ticket_events 涉及写操作、事务、幂等和审计，应该放到下一节单独学习。
```

---

## 十一、自测问题

### 自测 1：本节之后订单查询链路是什么？

答案：

```text
InternalOrderController -> OrderQueryService -> OrderRepository -> JdbcOrderRepository -> JdbcTemplate -> MySQL orders 表 -> OrderRowMapper -> Order -> OrderToolView。
```

### 自测 2：本节新增的三个数据库相关依赖分别是什么？

答案：

```text
spring-boot-starter-jdbc、mysql-connector-j、h2。
starter-jdbc 提供 JDBC/Spring 数据访问能力，mysql-connector-j 是 MySQL Driver，h2 用于测试环境内存数据库。
```

### 自测 3：`schema.sql` 和 `data.sql` 分别负责什么？

答案：

```text
schema.sql 负责建表结构。
data.sql 负责初始化基础数据。
本节 schema.sql 创建 orders 表，data.sql 插入 A1001、A1002、A2001 三条订单数据。
```

### 自测 4：为什么 Controller 不需要因为接 MySQL 大改？

答案：

```text
因为 Controller 只负责 HTTP 层，不负责数据来源。
数据来源变化被 Repository 实现层吸收，Service 继续依赖 OrderRepository 接口，所以 Controller 的契约可以保持稳定。
```

### 自测 5：如果 MySQL 密码没有设置，启动可能会怎样？

答案：

```text
主配置里 password 默认是空字符串。如果你的 MySQL root 用户有密码但没有设置 JAVA_BUSINESS_DB_PASSWORD，服务连接数据库会失败。
本地运行前应设置 $env:JAVA_BUSINESS_DB_PASSWORD。
```

### 自测 6：为什么本节保留 `InMemoryOrderRepository`？

答案：

```text
保留它可以在需要时通过 app.persistence.orders=memory 切回内存实现。
但默认配置已经切到 mysql，实现主线真实化，同时保留本地排查或演示的灵活性。
```

### 自测 7：本节测试失败时，为什么要先给兜底异常加日志？

答案：

```text
因为统一异常处理会把真实异常包装成 JAVA_SERVICE_ERROR 返回给调用方。
这对外部用户是安全的，但开发排查时必须在服务日志里看到真实堆栈。
所以兜底异常应该记录 error 日志，验证异常也应该记录关键原因。
```

### 自测 8：下一节应该学什么？

答案：

```text
下一节应该学习创建工单写工具真实化：把 tickets 表和 ticket_events 表落地到 MySQL，并在 Java Service 中处理用户确认、业务校验、幂等、事务和事件记录。
```

---

## 十二、本节总结

本节完成了阶段 7 的一个关键转折：

```text
订单查询不再只依赖内存 Map。
Java business service 已经能连接 Windows MySQL。
orders 表已经可以通过 schema.sql/data.sql 初始化。
GET /internal/orders/{order_id} 已经从 MySQL 查询订单。
测试环境使用 H2 但仍然覆盖 JDBC 查询链路。
```

你现在应该真正理解：

```text
接 MySQL 不只是加一个依赖和 URL。
它涉及 Driver、DataSource、连接池、JdbcTemplate、Repository、RowMapper、SQL 初始化、测试环境配置和敏感信息管理。
```

本节之后，Java 服务结构已经更接近传统 Spring Boot：

```text
Controller
-> Service
-> Repository
-> JDBC/MySQL
```

下一节进入：

```text
阶段 7 第 6 节：创建工单写工具真实化
```

下一节会开始处理更复杂的写操作：

```text
创建 tickets 表
创建 ticket_events 表
用户确认
幂等键
事务
写入工单
写入事件
```

这会比本节更接近真实业务系统的核心写链路。
