# Java Business Service

这个项目是阶段 7 新增的真实 Java Spring Boot 业务服务骨架。

它的定位不是 AI 服务，也不是模型服务，而是：

```text
AI Agent 可以安全、稳定、可追踪调用的 Java 业务系统。
```

当前第 3 节完成最小骨架，第 4 节完成 MySQL 业务数据模型设计：

```text
Spring Boot 启动入口
internal API Controller
统一 ApiResponse
订单和工单领域模型
内存 Repository
内部调用 Header 校验
trace_id 透传
创建工单幂等雏形
基础契约测试
MySQL 表设计草案
订单查询 MySQL 读链路
```

后续阶段会继续接入：

```text
工单写入 MySQL
Redis
传统 Spring Boot 目录结构重构
MyBatis 数据访问层
真实权限
事务
Python AI 服务适配
Docker Compose
```

MySQL 设计文档：

```text
../../docs/java-business-database-design.md
```

当前 MySQL 落地状态：

```text
orders 表已通过 schema.sql / data.sql 初始化。
GET /internal/orders/{order_id} 已通过 JdbcOrderRepository 从 MySQL 读取。
POST /internal/tickets 当前仍是内存工单 Repository，后续阶段再持久化到 MySQL。
```

结构重构计划：

```text
阶段 7 第 7.5 节会在第 8 节前执行 Java 服务结构传统化重构。
目标结构会对齐 controller / service / service.impl / mapper / entity / dto / config / exception / common。
数据访问层会从 JdbcTemplate 切换到 MyBatis。
重构时必须保留 AI Agent 调用边界：DTO 白名单、权限、幂等、trace_id、错误码和 internal token。
```

## 运行

本地运行前先确认 Windows MySQL 已启动，并创建数据库：

```powershell
$env:MYSQL_PWD = "你的 MySQL 密码"
mysql -u root -h 127.0.0.1 -P 3306 -e "CREATE DATABASE IF NOT EXISTS ai_business DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
```

设置 Java 服务读取 MySQL 密码：

```powershell
$env:JAVA_BUSINESS_DB_PASSWORD = "你的 MySQL 密码"
```

```powershell
mvn spring-boot:run
```

默认端口：

```text
8002
```

健康检查：

```text
GET http://127.0.0.1:8002/health
GET http://127.0.0.1:8002/ready
```

## 测试

```powershell
mvn test
```

测试环境使用 H2 内存数据库，但仍然走 `JdbcOrderRepository` 和 `JdbcTemplate` 查询链路。

## 当前 internal 接口

```text
GET /internal/orders/{order_id}
POST /internal/tickets
```

这两个接口按 [../../docs/java-ai-api-contract.md](../../docs/java-ai-api-contract.md) 的方向设计。

后续 MySQL 表结构按 [../../docs/java-business-database-design.md](../../docs/java-business-database-design.md) 落地。
