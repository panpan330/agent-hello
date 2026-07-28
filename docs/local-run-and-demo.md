# 本地运行说明和演示脚本

本文档用于说明当前 AI 客服工单系统学习项目如何在本地运行，以及如何按固定顺序演示。

当前项目定位：

```text
Java + Python 的 AI 客服工单系统学习项目
核心是企业知识库 RAG + LangGraph 智能工单 Agent
当前是 AI 应用工程学习项目和作品原型，不是完整生产上线系统
```

## 1. 演示路线选择

推荐按依赖程度分成三种演示。

| 演示路线 | 是否需要模型 API Key | 是否需要 VMware Ubuntu Docker | 适合场景 |
| --- | --- | --- | --- |
| 最小演示 | 不需要 | 不需要 | 快速证明两个服务能跑、Python 能调用 Java、回归能跑 |
| 真实 Java business 演示 | 不需要 | Redis 可选 | 演示阶段 7 的 Spring Boot + MyBatis + MySQL/Redis internal API |
| 真实模型演示 | 需要 | 不需要 | 演示 `/chat`、结构化输出、真实 LLM 相关能力 |
| 向量库演示 | 视脚本而定 | 需要 | 演示 Qdrant/Milvus 实机检索或入库 |

本阶段优先推荐：

```text
Windows 本地最小演示
```

它不需要打开虚拟机，也不需要真实模型 API Key。

阶段 7 完成后，项目多了一个真实 Java business 服务：

```text
projects/java-business-service
```

它和早期 `java-mock-service` 的关系是：

```text
java-mock-service：保留历史 Tool Calling / Agent 学习链路，启动轻、依赖少。
java-business-service：阶段 7 新增真实 Spring Boot + MyBatis + MySQL/Redis 业务服务，适合演示真实后端底座。
```

如果只是快速演示 Agent 主线，继续用 `java-mock-service` 即可。

如果要演示阶段 7 的真实 Java 后端能力，启动 `java-business-service`。

## 2. 前置条件

Windows 本地需要：

```text
Python 3.12
uv
PowerShell
```

已验证项目主目录：

```text
D:\wendang\java+python+ai
```

如果你只做最小演示，不需要：

```text
VMware Ubuntu
Docker
Qdrant
Milvus
真实模型 API Key
```

## 3. 配置 ai-service `.env`

进入 ai-service：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

如果还没有 `.env`，从示例复制：

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

注意：

```text
.env.example 可以提交 GitHub。
.env 是本机真实配置，不能提交 GitHub。
```

如果只是最小演示，可以不填模型 API Key。

如果要演示真实模型，再在 `.env` 中配置：

```text
LLM_BASE_URL
LLM_MODEL
LLM_API_KEY
```

## 4. Windows 本地启动两个服务

### 4.1 终端 1：启动 Java mock service

打开一个 PowerShell：

```powershell
cd D:\wendang\java+python+ai\projects\java-mock-service
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8001
```

启动成功后不要关闭这个终端。

Java mock service 地址：

```text
http://127.0.0.1:8001
```

### 4.2 终端 2：启动 ai-service

再打开一个 PowerShell：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动成功后不要关闭这个终端。

ai-service 地址：

```text
http://127.0.0.1:8000
```

## 5. 健康检查和就绪检查

再打开第三个 PowerShell，用来发请求。

### 5.1 检查 Java mock service

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
Invoke-RestMethod http://127.0.0.1:8001/ready
```

预期：

```text
service = java-mock-service
status = ok 或 ready
```

### 5.2 检查 ai-service

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/ready
```

预期：

```text
service = ai-service
status = ok 或 ready
```

如果当前是 `rule_based` 模式，`/ready` 不要求 LLM API Key。

如果设置了：

```text
TICKET_AGENT_MODEL_MODE=real_llm
```

但没有配置 API Key，`/ready` 返回 503 是预期行为。

## 6. 最小演示：不需要模型 API Key

### 6.1 直接查询 Java mock 订单

```powershell
Invoke-RestMethod http://127.0.0.1:8001/orders/A1001
```

`A1001` 是可用演示订单。

预期能看到：

```text
order_id = A1001
order_status = waiting_shipment
payment_status = paid
can_create_ticket = true
```

### 6.2 通过 ai-service 调用受控工具查询订单

```powershell
$body = @{
    order_id = "A1001"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/tools/query-order `
    -ContentType "application/json" `
    -Body $body
```

这一步证明：

```text
Python ai-service 没有直接编造订单信息。
它通过 query_order 工具调用 Java mock service。
工具参数和结果会经过后端校验。
```

### 6.3 查询不存在订单

```powershell
$body = @{
    order_id = "A9999"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/tools/query-order `
    -ContentType "application/json" `
    -Body $body
```

预期：

```text
返回订单不存在相关错误。
```

这一步证明：

```text
工具调用有错误处理，不是只处理成功路径。
```

## 7. 可选演示：真实 Java business service

这一节用于演示阶段 7 新增的真实 Java Spring Boot 业务服务。

默认不需要真实模型 API Key。

需要：

```text
JDK 17
Maven
Windows MySQL
```

Redis 是可选的：

```text
如果 VMware Ubuntu 里的 Redis 开着，可以演示 Redis 缓存、幂等和限流。
如果 Redis 没开，可以临时设置 JAVA_BUSINESS_REDIS_ENABLED=false，先演示 MySQL + internal API 主线。
```

启动服务：

```powershell
cd D:\wendang\java+python+ai\projects\java-business-service
$env:JAVA_BUSINESS_DB_PASSWORD = "root"
$env:JAVA_BUSINESS_REDIS_ENABLED = "false"
$env:JAVA_BUSINESS_INTERNAL_TOKEN = "local-dev-internal-token"
$env:JAVA_BUSINESS_INTERNAL_ALLOWED_CALLER = "ai-service"
mvn spring-boot:run
```

默认端口来自 `application.yml`：

```text
http://127.0.0.1:8002
```

如果你在 IDEA 或环境变量里改过端口，以实际启动日志为准。

健康检查：

```powershell
curl.exe http://127.0.0.1:8002/health
```

查询订单：

```powershell
curl.exe -i -X GET "http://127.0.0.1:8002/internal/orders/A1001" `
  -H "X-Trace-Id: demo-stage7-order" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token"
```

创建工单时，PowerShell 推荐先写临时 JSON 文件，避免 `curl.exe` 引号解析问题：

```powershell
$ticketBodyPath = Join-Path $env:TEMP "stage7-demo-create-ticket.json"
$ticketBody = '{"title":"物流太慢","description":"用户反馈 A1001 订单物流长时间未更新，希望客服跟进。","category":"logistics","priority":"normal","related_order_id":"A1001","source":"ai_agent","confirmation_id":"9f4d0b2f5b0c4f2a9d6c8b1e0a3f7c11"}'
[System.IO.File]::WriteAllText($ticketBodyPath, $ticketBody, [System.Text.UTF8Encoding]::new($false))

curl.exe -i -X POST "http://127.0.0.1:8002/internal/tickets" `
  -H "Content-Type: application/json" `
  -H "X-Trace-Id: demo-stage7-ticket" `
  -H "X-Caller: ai-service" `
  -H "X-User-Id: U1001" `
  -H "X-Tenant-Id: default" `
  -H "X-Internal-Token: local-dev-internal-token" `
  -H "Idempotency-Key: demo-stage7-ticket-001" `
  --data-binary "@$ticketBodyPath"
```

这条真实 Java 演示证明：

```text
AI 工具接口不是直接查数据库。
Python 调 Java 时必须带 internal token、caller、真实 user_id、tenant_id、trace_id。
写接口必须带 Idempotency-Key。
Java 侧负责权限、事务、MySQL、Redis 相关边界和机器错误码。
```

## 8. 可选演示：真实模型接口

这些接口需要配置真实模型 API Key。

如果没有配置，跳过本节。

### 7.1 普通聊天

```powershell
$body = @{
    message = "用一句话介绍这个项目"
    history = @()
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/chat `
    -ContentType "application/json" `
    -Body $body
```

如果没有配置 API Key，返回 `LLM_API_KEY_MISSING` 是预期行为。

### 7.2 结构化工单提取

```powershell
$body = @{
    message = "订单 A1001 已付款一周还没发货，我要投诉。"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/extract-ticket `
    -ContentType "application/json" `
    -Body $body
```

这一步证明：

```text
模型输出会被抽取成结构化字段，并经过 Pydantic 校验。
```

### 7.3 创建工单确认链路

先生成工单计划：

```powershell
$planBody = @{
    actor_id = "demo_user_001"
    message = "订单 A1001 已付款一周仍未发货，请帮我处理。"
} | ConvertTo-Json

$plan = Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/tickets/plans `
    -ContentType "application/json" `
    -Body $planBody

$confirmationId = $plan.confirmation.confirmation_id
$confirmationId
```

确认工具调用：

```powershell
$confirmBody = @{
    actor_id = "demo_user_001"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/tools/confirmations/$confirmationId/confirm" `
    -ContentType "application/json" `
    -Body $confirmBody
```

执行已确认工单：

```powershell
$executeBody = @{
    actor_id = "demo_user_001"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/tickets/confirmations/$confirmationId/execute" `
    -ContentType "application/json" `
    -Body $executeBody
```

这一步证明：

```text
创建工单是写操作。
写操作不是模型直接执行。
它必须先生成确认单，再由用户确认，最后后端才调用 Java mock service。
```

## 9. 可选演示：Qdrant / Milvus

只有演示向量库实机能力时才需要打开 VMware Ubuntu。

### 8.1 Qdrant

在 VMware Ubuntu 中：

```bash
docker ps --filter name=qdrant
curl http://localhost:6333
hostname -I
```

在 Windows PowerShell 中，把 IP 换成你的虚拟机 IP，例如：

```powershell
Invoke-RestMethod http://192.168.88.10:6333/collections
```

### 8.2 Milvus

在 VMware Ubuntu 中：

```bash
cd ~/milvus-standalone
docker compose up -d
docker compose ps
hostname -I
```

在 Windows PowerShell 中验证端口：

```powershell
Test-NetConnection 192.168.88.10 -Port 19530
```

Milvus Web UI：

```text
http://192.168.88.10:9091
```

注意：

```text
如果只做 Windows 本地最小演示，不需要打开 VMware Ubuntu。
```

## 10. 统一回归

在仓库根目录运行：

```powershell
cd D:\wendang\java+python+ai
python scripts\run_regression.py
```

它会分别验证：

```text
projects/java-mock-service
projects/ai-service
```

验证内容包括：

```text
uv sync --frozen
compileall
pytest
```

这一步证明：

```text
项目不是只能手工演示，还有自动化回归入口。
```

## 11. Agent eval 演示

进入 ai-service：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

查看可用评测套件：

```powershell
uv run python scripts\agent_eval.py --list-suites
```

运行回归评测：

```powershell
uv run python scripts\agent_eval.py --regression
```

生成报告：

```powershell
uv run python scripts\agent_eval.py `
    --regression `
    --report-path data\agent_eval\reports\agent_regression_report.md `
    --bad-case-analysis-path data\agent_eval\reports\agent_regression_bad_case_analysis.md
```

这一步证明：

```text
AI Agent 能力不是只靠感觉判断，而是有固定评测集和回归评测。
```

## 12. PowerShell 调接口建议

在 PowerShell 中优先使用：

```powershell
Invoke-RestMethod
```

不要直接依赖：

```powershell
curl
```

原因：

```text
PowerShell 里的 curl 可能是 Invoke-WebRequest 的别名。
JSON 引号和中文输出容易出问题。
```

如果确实要用真正的 curl，写：

```powershell
curl.exe
```

## 13. 常见问题

### 12.1 端口被占用

查看端口：

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :8001
```

处理方式：

```text
关闭占用端口的旧服务，或换端口启动。
```

### 12.2 `LLM_API_KEY_MISSING`

说明：

```text
当前接口需要真实模型 API Key，但 .env 没配置。
```

处理方式：

```text
最小演示可以跳过真实模型接口。
如果要演示真实模型，在 projects/ai-service/.env 中配置 LLM_API_KEY。
```

### 12.3 ai-service 工具查询失败

先确认 Java mock service 是否启动：

```powershell
Invoke-RestMethod http://127.0.0.1:8001/ready
```

再确认 ai-service `.env` 中：

```text
JAVA_MOCK_SERVICE_BASE_URL="http://127.0.0.1:8001"
```

### 12.4 Qdrant / Milvus 连接失败

先确认是否需要演示向量库。

如果需要，打开 VMware Ubuntu，然后检查：

```bash
docker ps
hostname -I
```

Windows 访问时要使用虚拟机 IP，例如：

```text
192.168.88.10
```

### 12.5 PowerShell 中文看起来像乱码

如果只是 PowerShell 输出中文异常，先怀疑：

```text
PowerShell 输出编码或字体显示问题。
```

不要立刻大范围修改项目文件。

可以优先用浏览器、日志文件或 UTF-8 编辑器查看。

### 12.6 `ModuleNotFoundError: No module named 'app'`

通常是运行目录不对，或直接执行脚本时没有把项目根目录加入 Python import path。

推荐：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
uv run python scripts\agent_eval.py --list-suites
```

如果某个旧脚本仍然报这个错，可以临时设置：

```powershell
$env:PYTHONPATH = (Get-Location).Path
uv run python scripts\脚本名.py
```

## 14. 推荐演示话术

可以按这个顺序讲：

```text
第一步，我先介绍项目定位：这是一个 Java + Python 的 AI 客服工单系统学习项目，核心是 RAG + LangGraph Agent。

第二步，我打开 README 和 project-diagrams，说明整体架构：Python ai-service 负责 AI 能力，Java mock service 保留历史学习链路，Java business service 是阶段 7 新增的真实 Spring Boot + MySQL/Redis 业务服务底座，RAG 连接向量库，Agent 编排工具调用和工单流程。

第三步，我启动两个本地服务，先验证 /health 和 /ready，说明服务进程和就绪状态。

第四步，最小演示时我直接调用 Java mock service 查询订单，证明受控工具链路可用。

第五步，我通过 ai-service 的 /tools/query-order 查询同一订单，证明 Python AI 服务通过受控工具调用 Java 服务，而不是自己编造业务数据。

第六步，我运行统一回归脚本，说明项目有自动化验证。

如果配置了模型 API Key，再演示 /chat、结构化工单提取和用户确认后的创建工单。

如果要演示阶段 7，再启动 java-business-service，演示 /internal/orders 和 /internal/tickets，说明 internal token、user_id、tenant_id、trace_id、幂等键和契约测试。

如果打开了虚拟机，再演示 Qdrant 或 Milvus。
```

## 15. 关闭服务

在启动服务的两个 PowerShell 终端中按：

```text
Ctrl + C
```

即可停止服务。
