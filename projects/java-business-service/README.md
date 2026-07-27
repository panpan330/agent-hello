# Java Business Service

这个项目是阶段 7 新增的真实 Java Spring Boot 业务服务骨架。

它的定位不是 AI 服务，也不是模型服务，而是：

```text
AI Agent 可以安全、稳定、可追踪调用的 Java 业务系统。
```

当前第 3 节只完成最小骨架：

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
```

后续阶段会继续接入：

```text
MySQL
Redis
真实权限
事务
Python AI 服务适配
Docker Compose
```

## 运行

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

## 当前 internal 接口

```text
GET /internal/orders/{order_id}
POST /internal/tickets
```

这两个接口按 [../../docs/java-ai-api-contract.md](../../docs/java-ai-api-contract.md) 的方向设计。
