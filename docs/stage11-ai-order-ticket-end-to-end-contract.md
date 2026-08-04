# 阶段 11 第 10 节：AI 订单查询与创建工单端到端契约

本节目标是把 Python AI 服务和真实 Java business-service 接起来，让订单查询和创建工单不再走旧 mock 服务。

## 1. 真实链路

```text
前端 AI 页面
-> Python ai-service
-> Java business-service internal API
-> MySQL / Redis
-> Java ApiResponse
-> Python Pydantic 校验
-> 前端展示
```

## 2. Python 调 Java 的配置

`projects/ai-service/.env.example` 已新增：

```env
JAVA_BUSINESS_SERVICE_BASE_URL="http://127.0.0.1:18004"
JAVA_BUSINESS_SERVICE_TIMEOUT_SECONDS=5
JAVA_BUSINESS_INTERNAL_TOKEN="local-dev-internal-token"
JAVA_BUSINESS_INTERNAL_CALLER="ai-service"
JAVA_BUSINESS_DEFAULT_USER_ID="U1001"
JAVA_BUSINESS_DEFAULT_TENANT_ID="default"
```

本地 `.env` 使用同一组配置，真实密钥类内容仍不提交。

## 3. 订单查询契约

Python 客户端：

```text
app/services/java_order_client.py
```

Java 接口：

```text
GET /internal/orders/{order_id}
```

必要 header：

```text
X-Trace-Id
X-Caller
X-User-Id
X-Tenant-Id
X-Internal-Token
```

Python 会把 Java 返回的 `ApiResponse.data` 解包，再映射成 `QueryOrderResult`，并且只保留允许给模型看的字段。

## 4. 创建工单契约

Python 客户端：

```text
app/services/java_ticket_client.py
```

Java 接口：

```text
POST /internal/tickets
```

额外 header：

```text
Idempotency-Key
```

Python 发给 Java 的请求体只包含 Java 内部写操作需要的字段：

```json
{
  "title": "order logistics slow",
  "description": "A1001 logistics has not updated for a long time",
  "category": "logistics",
  "priority": "normal",
  "related_order_id": "A1001",
  "source": "ai_agent",
  "confirmation_id": "32位十六进制确认ID"
}
```

Python 不让模型直接执行写操作；创建工单仍然走“计划 -> 用户确认 -> 执行”的确认链路。

## 5. 本节验证结果

- Python 单测全量：`1256 passed`
- Java Maven 测试：`33 passed`
- 真实 Java `/health`：通过
- 真实 Java `GET /internal/orders/A1001`：通过
- 真实 Python `JavaOrderClient -> Java -> MySQL`：通过
- 真实 Python `JavaTicketClient -> Java -> MySQL`：通过，返回 `T-uuid` 工单号

## 6. 本地启动注意

Java business-service 默认端口已统一为：

```text
18004
```

Windows MySQL 本地默认配置：

```text
username=root
password=root
database=ai_business
```

如果以后机器环境变化，优先通过环境变量覆盖，不要把真实生产密码写进仓库。
