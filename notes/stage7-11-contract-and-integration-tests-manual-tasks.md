# 阶段 7 第 11 节手动验证清单

本节自动化部分已经建立了共享契约测试入口。手动验证主要用于确认本地真实 Java 服务能按契约运行。

## 1. 是否需要打开虚拟机

默认不需要。

只跑自动化测试：

```text
不用 VMware Ubuntu
不用 Redis
不用 Qdrant
不用 Milvus
不用真实大模型
```

真实启动 Java 服务时：

```text
需要 Windows MySQL。
Redis 可以关掉。
```

## 2. 跑 Python consumer 契约测试

进入：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

运行：

```powershell
uv run pytest tests/test_java_business_contract.py
```

期望：

```text
6 passed
```

## 3. 跑 Java provider 契约测试

进入：

```powershell
cd D:\wendang\java+python+ai\projects\java-business-service
```

运行：

```powershell
mvn -q "-Dtest=InternalApiContractTest" test
```

期望：

```text
测试通过，没有 failures/errors
```

## 4. 可选：真实启动 Java 服务

如果你想做真实 curl 集成验证：

```powershell
cd D:\wendang\java+python+ai\projects\java-business-service
$env:JAVA_BUSINESS_DB_PASSWORD = "root"
$env:JAVA_BUSINESS_REDIS_ENABLED = "false"
$env:JAVA_BUSINESS_INTERNAL_TOKEN = "local-dev-internal-token"
$env:JAVA_BUSINESS_INTERNAL_ALLOWED_CALLER = "ai-service"
mvn spring-boot:run
```

确认健康检查：

```powershell
curl.exe http://127.0.0.1:8002/health
```

期望：

```json
{"service":"java-business-service","status":"ok"}
```

## 5. 可选：真实订单查询契约

```powershell
curl.exe -i -X GET "http://127.0.0.1:8002/internal/orders/A1001" `
  -H "X-Trace-Id: manual-stage7-11-order-ok" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

重点看：

```text
HTTP 200
响应头 X-Trace-Id: manual-stage7-11-order-ok
响应体 success: true
响应体 code: OK
响应体 data.order_id: A1001
响应体 trace_id: manual-stage7-11-order-ok
```

## 6. 可选：真实权限失败契约

```powershell
curl.exe -i -X GET "http://127.0.0.1:8002/internal/orders/A2001" `
  -H "X-Trace-Id: manual-stage7-11-order-denied" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

期望：

```text
HTTP 403
code: ORDER_ACCESS_DENIED
trace_id: manual-stage7-11-order-denied
```

## 7. 可选：真实创建工单契约

PowerShell 里推荐用临时 JSON 文件，避免 curl.exe 的 JSON 引号问题：

```powershell
$ticketBodyPath = Join-Path $env:TEMP "stage7-11-create-ticket.json"
$ticketBody = '{"title":"物流太慢","description":"用户反馈 A1001 订单物流长时间未更新，希望客服跟进。","category":"logistics","priority":"normal","related_order_id":"A1001","source":"ai_agent","confirmation_id":"9f4d0b2f5b0c4f2a9d6c8b1e0a3f7c11"}'
[System.IO.File]::WriteAllText($ticketBodyPath, $ticketBody, [System.Text.UTF8Encoding]::new($false))

curl.exe -i -X POST "http://127.0.0.1:8002/internal/tickets" `
  -H "Content-Type: application/json" `
  -H "X-Trace-Id: manual-stage7-11-ticket-ok" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token" `
  -H "Idempotency-Key: manual-stage7-11-ticket-001" `
  --data-binary "@$ticketBodyPath"
```

期望：

```text
HTTP 201
code: OK
data.ticket_id 存在
data.ticket_status: created
trace_id: manual-stage7-11-ticket-ok
```

## 8. 可选：真实缺少幂等键契约

```powershell
curl.exe -i -X POST "http://127.0.0.1:8002/internal/tickets" `
  -H "Content-Type: application/json" `
  -H "X-Trace-Id: manual-stage7-11-ticket-no-idem" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token" `
  --data-binary "@$ticketBodyPath"
```

期望：

```text
HTTP 400
code: IDEMPOTENCY_KEY_REQUIRED
trace_id: manual-stage7-11-ticket-no-idem
```

## 9. 你需要贴给我的结果

如果只跑自动化测试，贴：

```text
Python: 6 passed
Java: InternalApiContractTest 通过
```

如果跑真实 curl，贴这四个关键信息即可：

```text
订单查询成功：HTTP status + code + trace_id
订单权限失败：HTTP status + code + trace_id
创建工单成功：HTTP status + code + ticket_id + trace_id
缺少幂等键：HTTP status + code + trace_id
```

不用贴完整大段日志。
