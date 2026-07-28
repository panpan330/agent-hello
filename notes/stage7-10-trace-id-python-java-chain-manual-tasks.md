# 阶段 7 第 10 节手动验证清单

本节是省 token 模式。自动化测试我已经跑了关键部分；你手动只需要确认 trace_id 在 Python 和 Java 两边能对上。

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

如果你想真实启动 Java 服务：

```text
需要 Windows MySQL。
Redis 可以关掉。
```

## 2. 推荐先跑 Python trace 测试

进入：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

运行：

```powershell
uv run pytest tests/test_trace.py tests/test_java_order_client.py tests/test_java_ticket_client.py
```

期望：

```text
26 passed
```

## 3. 推荐再跑 Java trace 相关测试

进入：

```powershell
cd D:\wendang\java+python+ai\projects\java-business-service
```

运行：

```powershell
mvn -q "-Dtest=InternalOrderControllerTest,InternalTicketControllerTest" test
```

期望：

```text
BUILD SUCCESS
```

如果控制台没直接显示 `BUILD SUCCESS`，但命令正常回到提示符且没有 failure/error，也算通过。

## 4. 可选：真实启动 Java 服务验证响应头

如果你想手动 curl，先设置环境变量：

```powershell
cd D:\wendang\java+python+ai\projects\java-business-service
$env:JAVA_BUSINESS_DB_PASSWORD = "root"
$env:JAVA_BUSINESS_REDIS_ENABLED = "false"
$env:JAVA_BUSINESS_INTERNAL_TOKEN = "local-dev-internal-token"
$env:JAVA_BUSINESS_INTERNAL_ALLOWED_CALLER = "ai-service"
mvn spring-boot:run
```

另开一个 PowerShell 窗口请求订单查询：

```powershell
curl.exe -i -X GET "http://127.0.0.1:8002/internal/orders/A1001" `
  -H "X-Trace-Id: manual-stage7-10-order-ok" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

你重点看两个位置。

响应头：

```text
X-Trace-Id: manual-stage7-10-order-ok
```

响应体：

```json
"trace_id":"manual-stage7-10-order-ok"
```

## 5. 可选：验证失败时也有 trace_id

故意查无权限订单：

```powershell
curl.exe -i -X GET "http://127.0.0.1:8002/internal/orders/A2001" `
  -H "X-Trace-Id: manual-stage7-10-denied" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

期望：

```text
HTTP 403
响应头 X-Trace-Id: manual-stage7-10-denied
响应体 code: ORDER_ACCESS_DENIED
响应体 trace_id: manual-stage7-10-denied
```

## 6. 可选：验证缺少 trace_id 时 Java 仍给排查编号

故意不传 `X-Trace-Id`：

```powershell
curl.exe -i -X GET "http://127.0.0.1:8002/internal/orders/A1001" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

期望：

```text
HTTP 401
code: INTERNAL_AUTH_FAILED
响应头里仍然有 X-Trace-Id
```

这里要理解：

```text
Java 生成 trace_id 是为了排查。
它不代表允许缺少 X-Trace-Id 的 internal 调用通过。
```

## 7. 你需要贴给我的结果

如果你只跑自动化测试，贴最后结果即可：

```text
26 passed
Java 测试通过
```

如果你跑真实 curl，贴这三项即可：

```text
成功查询的响应头 X-Trace-Id
成功查询的响应体 trace_id
失败查询的 code 和 trace_id
```

不用贴完整大段日志。
