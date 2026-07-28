# 阶段 7 第 7.5 节手动验证清单

这个文档用于“省 token 模式”。
我已经完成代码重构、主笔记和轻量编译检查。
下面这些偏长、偏环境相关的验证，你可以手动执行，之后把关键输出贴给我。

## 1. IDEA 里刷新项目

在 IntelliJ IDEA 中打开：

```text
D:\wendang\java+python+ai\projects\java-business-service
```

操作：

```text
打开右侧 Maven 面板。
点击 Reload All Maven Projects。
确认 pom.xml 里的 mybatis-spring-boot-starter 能正常下载。
确认 src/main/resources/mapper 下能看到 OrderMapper.xml 和 TicketMapper.xml。
```

如果 IDEA 提示 Mapper XML 未识别，先不用急。
只要 Maven 编译和测试通过，说明项目本身没问题。

## 2. 编译检查

在 PowerShell 进入 Java 服务目录：

```powershell
cd D:\wendang\java+python+ai\projects\java-business-service
```

执行：

```powershell
mvn -DskipTests compile
mvn -DskipTests test-compile
```

期望结果：

```text
BUILD SUCCESS
```

如果出现 `非法字符: '\ufeff'`，说明某个 Java 文件有 UTF-8 BOM。
这不是普通中文显示乱码，而是真实编译错误。

## 3. 自动化测试

执行：

```powershell
mvn test
```

期望结果：

```text
BUILD SUCCESS
```

说明：

```text
测试环境使用 H2 内存数据库。
测试环境默认 app.redis.enabled=false。
所以这一步不需要打开 VMware Ubuntu，也不需要真实 Redis。
```

## 4. 本地 MySQL 真实运行

确认 Windows MySQL 已启动，并且 root 密码按你的本机环境设置。

创建数据库：

```powershell
$env:MYSQL_PWD = "你的 MySQL 密码"
mysql -u root -h 127.0.0.1 -P 3306 -e "CREATE DATABASE IF NOT EXISTS ai_business DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
```

设置 Java 服务读取 MySQL：

```powershell
$env:JAVA_BUSINESS_DB_PASSWORD = "你的 MySQL 密码"
$env:JAVA_BUSINESS_REDIS_ENABLED = "false"
```

启动服务：

```powershell
mvn spring-boot:run "-Dspring-boot.run.arguments=--server.port=18004"
```

另开一个 PowerShell 测试健康检查：

```powershell
curl.exe http://127.0.0.1:18004/health
```

期望看到：

```json
{"status":"ok","service":"java-business-service"}
```

## 5. 订单查询 smoke

执行：

```powershell
curl.exe -X GET "http://127.0.0.1:18004/internal/orders/A1001" `
  -H "X-Trace-Id: manual-stage7-075-order" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

期望：

```text
success 为 true。
data.order_id 为 A1001。
trace_id 为 manual-stage7-075-order。
```

这一步验证：

```text
Controller -> Service -> MyBatis Mapper -> MySQL -> DTO
```

## 6. 创建工单 smoke

Windows PowerShell 直接把一大段 JSON 字符串传给 `curl.exe` 时，容易丢失 JSON 里的双引号。
所以这里先把请求体写入临时 JSON 文件，再让 `curl.exe` 从文件读取。

执行：

```powershell
$ticketBodyPath = Join-Path $env:TEMP "stage7-075-create-ticket.json"
$ticketBody = '{"title":"order logistics slow","description":"A1001 logistics has not updated for a long time","category":"logistics","priority":"normal","related_order_id":"A1001","source":"ai_agent","confirmation_id":"9f4d0b2f5b0c4f2a9d6c8b1e0a3f7c11"}'
[System.IO.File]::WriteAllText($ticketBodyPath, $ticketBody, [System.Text.UTF8Encoding]::new($false))

curl.exe -X POST "http://127.0.0.1:18004/internal/tickets" `
  -H "Content-Type: application/json" `
  -H "X-Trace-Id: manual-stage7-075-ticket" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token" `
  -H "Idempotency-Key: manual-stage7-075-ticket-001" `
  --data-binary "@$ticketBodyPath"
```

期望：

```text
HTTP 201。
success 为 true。
data.ticket_id 存在。
data.ticket_status 为 created。
```

把返回里的 `ticket_id` 记下来，后面清理数据会用到。

## 7. 幂等验证

用完全相同的命令再请求一次。

期望：

```text
仍然 HTTP 201。
返回同一个 ticket_id。
```

这一步验证：

```text
MyBatis 写入链路没有破坏第 6 节的幂等设计。
```

## 8. 可选 Redis 验证

只有当 VMware Ubuntu 虚拟机已打开，且 Redis 容器已启动时再做。

Windows 连通性检查：

```powershell
Test-NetConnection 192.168.88.10 -Port 6379
```

设置 Redis：

```powershell
$env:JAVA_BUSINESS_REDIS_ENABLED = "true"
$env:JAVA_BUSINESS_REDIS_HOST = "192.168.88.10"
$env:JAVA_BUSINESS_REDIS_PORT = "6379"
```

重新启动 Java 服务，再执行订单查询和创建工单 smoke。

这一步验证：

```text
MyBatis 重构后，Redis 缓存、幂等缓存、限流仍然能工作。
```

## 9. 清理手动 smoke 数据

如果创建了手动工单，可以在 MySQL 中清理。

把下面的 `你的工单ID` 替换成刚才返回的 `ticket_id`：

```powershell
$env:MYSQL_PWD = "你的 MySQL 密码"
mysql -u root -h 127.0.0.1 -P 3306 ai_business -e "DELETE FROM ticket_events WHERE ticket_id = '你的工单ID'; DELETE FROM tickets WHERE ticket_id = '你的工单ID';"
```

如果你只做学习验证，不清理也可以。
因为 `idempotency_key` 不同，后续测试不会直接受影响。

## 10. 你需要贴给我的关键输出

如果你要我帮你判断是否通过，贴这些就够：

```text
mvn test 最后 20 行。
订单查询 curl 返回体。
创建工单 curl 返回体。
第二次幂等请求返回体。
如果 Redis 开启，再贴 Test-NetConnection 结果和一次订单查询返回体。
```

不要贴超长 Maven 下载日志。
如果 Maven 失败，只贴第一个 `[ERROR]` 附近的 30 行。
