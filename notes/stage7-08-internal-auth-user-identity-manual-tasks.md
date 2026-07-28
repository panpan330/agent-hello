# 阶段 7 第 8 节手动验证清单

这个文档用于“省 token 模式”。
我已经完成代码修改、主笔记和轻量测试。
下面是真实本地服务 smoke，你可以手动跑。

## 1. 本节需要打开哪些东西

本节不需要 VMware。

需要：

```text
Windows MySQL 已启动。
Java business service 能连接 ai_business 数据库。
```

如果 Redis 没开，先关闭 Redis：

```powershell
$env:JAVA_BUSINESS_REDIS_ENABLED = "false"
```

## 2. 启动 Java 服务

进入 Java 服务目录：

```powershell
cd D:\wendang\java+python+ai\projects\java-business-service
```

设置本机 MySQL 密码：

```powershell
$env:JAVA_BUSINESS_DB_PASSWORD = "你的 MySQL 密码"
$env:JAVA_BUSINESS_REDIS_ENABLED = "false"
```

启动：

```powershell
mvn spring-boot:run "-Dspring-boot.run.arguments=--server.port=18004"
```

健康检查：

```powershell
curl.exe http://127.0.0.1:18004/health
```

期望：

```json
{"service":"java-business-service","status":"ok"}
```

## 3. 正常订单查询

```powershell
curl.exe -X GET "http://127.0.0.1:18004/internal/orders/A1001" `
  -H "X-Trace-Id: manual-stage7-08-order-ok" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

期望：

```text
success 为 true。
data.order_id 为 A1001。
trace_id 为 manual-stage7-08-order-ok。
```

## 4. 缺少租户应该失败

```powershell
curl.exe -X GET "http://127.0.0.1:18004/internal/orders/A1001" `
  -H "X-Trace-Id: manual-stage7-08-missing-tenant" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Internal-Token: local-dev-internal-token"
```

期望：

```text
success 为 false。
code 为 INTERNAL_AUTH_FAILED。
```

## 5. 错误 caller 应该失败

```powershell
curl.exe -X GET "http://127.0.0.1:18004/internal/orders/A1001" `
  -H "X-Trace-Id: manual-stage7-08-wrong-caller" `
  -H "X-Caller: unknown-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

期望：

```text
success 为 false。
code 为 INTERNAL_AUTH_FAILED。
```

## 6. 不安全 user_id 应该失败

```powershell
curl.exe -X GET "http://127.0.0.1:18004/internal/orders/A1001" `
  -H "X-Trace-Id: manual-stage7-08-bad-user" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001/../admin" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

期望：

```text
success 为 false。
code 为 INTERNAL_AUTH_FAILED。
```

## 7. 用户无权访问订单应该是业务权限失败

```powershell
curl.exe -X GET "http://127.0.0.1:18004/internal/orders/A2001" `
  -H "X-Trace-Id: manual-stage7-08-access-denied" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

期望：

```text
success 为 false。
code 为 ORDER_ACCESS_DENIED。
```

这一条和前面几条的区别很重要：

```text
INTERNAL_AUTH_FAILED：调用身份或上下文不可信。
ORDER_ACCESS_DENIED：调用身份可信，但用户无权访问业务对象。
```

## 8. 创建工单仍然应该成功

PowerShell 里传 JSON 给 `curl.exe` 时，建议先写入临时文件：

```powershell
$ticketBodyPath = Join-Path $env:TEMP "stage7-08-create-ticket.json"
$ticketBody = '{"title":"order logistics slow","description":"A1001 logistics has not updated for a long time","category":"logistics","priority":"normal","related_order_id":"A1001","source":"ai_agent","confirmation_id":"9f4d0b2f5b0c4f2a9d6c8b1e0a3f7c11"}'
[System.IO.File]::WriteAllText($ticketBodyPath, $ticketBody, [System.Text.UTF8Encoding]::new($false))

curl.exe -X POST "http://127.0.0.1:18004/internal/tickets" `
  -H "Content-Type: application/json" `
  -H "X-Trace-Id: manual-stage7-08-ticket-ok" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token" `
  -H "Idempotency-Key: manual-stage7-08-ticket-001" `
  --data-binary "@$ticketBodyPath"
```

期望：

```text
success 为 true。
data.ticket_status 为 created。
```

## 9. 清理手动创建的工单

把返回里的 `ticket_id` 填进去：

```powershell
$env:MYSQL_PWD = "你的 MySQL 密码"
mysql -u root -h 127.0.0.1 -P 3306 ai_business -e "DELETE FROM ticket_events WHERE ticket_id = '你的工单ID'; DELETE FROM tickets WHERE ticket_id = '你的工单ID';"
```

## 10. 你需要贴给我的关键输出

如果需要我判断：

```text
正常订单查询返回体。
缺少租户返回体。
错误 caller 返回体。
不安全 user_id 返回体。
A2001 权限失败返回体。
创建工单返回体。
```

不用贴完整 Java 启动日志。
如果出现 `JAVA_SERVICE_ERROR`，只贴 Java 控制台最下面的 `Caused by:` 几段。
