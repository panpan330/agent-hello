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
| 真实模型演示 | 需要 | 不需要 | 演示 `/chat`、结构化输出、真实 LLM 相关能力 |
| 向量库演示 | 视脚本而定 | 需要 | 演示 Qdrant/Milvus 实机检索或入库 |

本阶段优先推荐：

```text
Windows 本地最小演示
```

它不需要打开虚拟机，也不需要真实模型 API Key。

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

## 7. 可选演示：真实模型接口

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

## 8. 可选演示：Qdrant / Milvus

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

## 9. 统一回归

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

## 10. Agent eval 演示

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

## 11. PowerShell 调接口建议

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

## 12. 常见问题

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

## 13. 推荐演示话术

可以按这个顺序讲：

```text
第一步，我先介绍项目定位：这是一个 Java + Python 的 AI 客服工单系统学习项目，核心是 RAG + LangGraph Agent。

第二步，我打开 README 和 project-diagrams，说明整体架构：Python ai-service 负责 AI 能力，Java mock service 模拟业务后端，RAG 连接向量库，Agent 编排工具调用和工单流程。

第三步，我启动两个本地服务，先验证 /health 和 /ready，说明服务进程和就绪状态。

第四步，我直接调用 Java mock service 查询订单，证明业务服务可用。

第五步，我通过 ai-service 的 /tools/query-order 查询同一订单，证明 Python AI 服务通过受控工具调用 Java 服务，而不是自己编造业务数据。

第六步，我运行统一回归脚本，说明项目有自动化验证。

如果配置了模型 API Key，再演示 /chat、结构化工单提取和用户确认后的创建工单。

如果打开了虚拟机，再演示 Qdrant 或 Milvus。
```

## 14. 关闭服务

在启动服务的两个 PowerShell 终端中按：

```text
Ctrl + C
```

即可停止服务。
