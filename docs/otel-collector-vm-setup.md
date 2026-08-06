# 在 VMware Ubuntu 上部署 OTLP Collector（手动配置指南）

> 用途：为本机 Windows 上的 Python AI 服务（`projects/ai-service`）提供 OpenTelemetry trace 接收端。
> 背景：Docker 跑在 VMware Ubuntu（`192.168.88.10`）里，本机无 Docker。以下步骤在 **VM 的 Ubuntu 终端**里执行。

## 0. 前置检查

```bash
# 确认 Docker 可用、Redis/Qdrant 容器已在跑（之前联调用的就是它们）
docker --version
docker ps
# 确认本机 Windows 能访问 VM 的 4317 端口（配置完容器后验证）
```

VM 的 IP 是 `192.168.88.10`（VMware NAT）。若网络变化，在 Ubuntu 里运行 `hostname -I` 更新。

## 1. 在 VM 上创建 Collector 配置目录与文件

```bash
mkdir -p ~/otel-collector
cd ~/otel-collector
```

用 `nano` 或 `vi` 创建两个文件：

**文件 1：`otel-collector-config.yml`**

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
exporters:
  debug:
    verbosity: detailed
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
```

**文件 2：`docker-compose.yml`**

```yaml
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: otel-collector
    restart: unless-stopped
    ports:
      - "4317:4317"   # OTLP/gRPC（Python 服务用这个）
      - "4318:4318"   # OTLP/HTTP（备用）
    volumes:
      - ./otel-collector-config.yml:/etc/otelcol-contrib/config.yaml
    command: ["--config=/etc/otelcol-contrib/config.yaml"]
```

## 2. 启动 Collector

```bash
cd ~/otel-collector
docker compose up -d
```

验证：

```bash
docker ps                     # 应看到 otel-collector 容器 Up
docker logs -f otel-collector # 观察 span 输出（收到 trace 会打印 detailed 日志）
```

## 3. 确认 VM 端口可被 Windows 访问

在本机 Windows PowerShell 验证：

```powershell
Test-NetConnection 192.168.88.10 -Port 4317
```

预期 `TcpTestSucceeded : True`。

## 4. 配置本机 Python 服务

编辑 `projects/ai-service/.env`：

```text
OTEL_EXPORTER_OTLP_ENDPOINT=http://192.168.88.10:4317
OTEL_SERVICE_NAME=ai-service
```

> 注意：**不是** `localhost:4317`（那是"本机跑 Collector"的写法）；现在 Collector 在 VM 上，用 VM 的 IP。

## 5. 启动服务并验证

```powershell
# 终端 1：Java（本机）
cd D:\wendang\java+python+ai\projects\java-business-service
mvn spring-boot:run

# 终端 2：Python AI 服务（本机）
cd D:\wendang\java+python+ai\projects\ai-service
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器打开 AI 客服页（或调用接口）发起一条对话（如"查订单 A1001 物流"），然后：

```bash
# 回到 VM 终端
docker logs -f otel-collector
```

**验证点**：Collector 日志中出现 span 树。span 树形状取决于 `.env` 的部署形态：

```text
MCP 模式（AGENT_MCP_TOOLS_ENABLED=true，当前 .env 形态，本进程内）：
http.request → agent.invoke → llm.call → tool.call
（Java 调用发生在独立 MCP server 进程内，其 java.call 不出现在本进程 span 树；
 若 MCP server 进程也接入 OTEL，会作为跨进程独立 span 存在）

非 MCP 模式（AGENT_MCP_TOOLS_ENABLED=false，工具直接调用 Java 内部 API）：
http.request → agent.invoke → llm.call → java.call
（无 tool.call）
```

每个 span 带 `x_trace_id` 属性（与 AI 服务日志中的 X-Trace-Id 一致）。

## 6. 常见问题

| 现象 | 处理 |
| --- | --- |
| `docker compose up -d` 拉镜像失败 | 检查 VM 网络/Docker 镜像源；可先 `docker pull otel/opentelemetry-collector-contrib` 单独拉 |
| Windows 连不上 4317 | 确认 VM 防火墙放行 4317；`sudo ufw allow 4317/tcp`（若用 ufw） |
| Collector 日志无 span | 确认 `.env` 的 endpoint 是 `192.168.88.10:4317` 且服务已重启；Python 服务日志若有 `otel_setup_failed` 说明 exporter 初始化失败 |
| 只想快速看 span | 也可用本机 Python 跑临时脚本注入内存 exporter（不依赖 Collector），见项目内实现说明 |

## 7. 关闭 Collector（可选）

```bash
cd ~/otel-collector
docker compose down
```

> 本文件与项目根 `docker-compose.otel.yml`、`otel-collector-config.yml` 内容一致，供 VM 上手动创建用；将来若 VM 上配置了共享目录或 SSH，可直接复制这两个文件过去。

---

## 附录 A：傻瓜操作版（推荐给不熟悉 Linux 的你）

> 以下内容**不用看懂**，照做即可。所有操作都在 **VM 的 Ubuntu 终端**里完成。

### A1. 打开 VM 终端

打开 VMware 里的 Ubuntu 虚拟机 → 打开终端（Terminal）。若 Ubuntu 是图形界面，按 `Ctrl+Alt+T` 打开终端。

### A2. 复制下面这一整段，粘贴进终端，回车

```bash
# ===== 一键部署 OTLP Collector（复制从这一行到最后一行）=====
mkdir -p ~/otel-collector && cd ~/otel-collector && \
cat > otel-collector-config.yml << 'CONFIG_EOF'
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
exporters:
  debug:
    verbosity: detailed
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
CONFIG_EOF
cat > docker-compose.yml << 'COMPOSE_EOF'
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: otel-collector
    restart: unless-stopped
    ports:
      - "4317:4317"
      - "4318:4318"
    volumes:
      - ./otel-collector-config.yml:/etc/otelcol-contrib/config.yaml
    command: ["--config=/etc/otelcol-contrib/config.yaml"]
COMPOSE_EOF
docker compose up -d
```

粘贴后按回车，会看到类似输出（拉取镜像 + 启动容器）：

```text
[+] Running 2/2
 ✔ Network otel-collector_default  Created
 ✔ Container otel-collector       Started
```

### A3. 确认容器在跑

复制下面这一段，粘贴，回车：

```bash
docker ps --filter name=otel-collector
```

看到类似：

```text
CONTAINER ID   IMAGE                                        ...   STATUS
xxxxxxxxxxxx   otel/opentelemetry-collector-contrib:latest  ...   Up 2 seconds
```

就是成功了。`STATUS` 是 `Up ...`（不是 `Exited`）即可。

### A4. 回到 Windows 验证端口通不通

Windows 打开 PowerShell，粘贴：

```powershell
Test-NetConnection 192.168.88.10 -Port 4317
```

看到 `TcpTestSucceeded : True` 就说明通了，可以继续联调。

> **这一步通过后，其余按正文第 4-5 节进行**（.env 已配好、Python 服务启动后，回到 VM 终端跑 `docker logs -f otel-collector` 看 span）。

### A5. 如果 A2 出错怎么办

| 现象 | 做法 |
| --- | --- |
| 提示 `docker: command not found` | Docker 没装或不在 PATH，先确认 VM 里 Docker 能用（`docker --version`） |
| 提示 `docker compose` 不认识 | 有些旧版 Docker 用 `docker-compose`（带横杠），把 A2 最后一行换成 `docker-compose up -d` |
| 拉镜像很慢/超时 | 重跑一次 A2 的最后一行 `docker compose up -d`，或先 `docker pull otel/opentelemetry-collector-contrib` 单独拉 |
| 其他看不懂的报错 | 把报错截图/复制给我，我来帮你看 |
