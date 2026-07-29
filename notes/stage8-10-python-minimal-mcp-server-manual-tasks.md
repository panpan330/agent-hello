# 阶段 8 第 10 节手动验证：Python 最小 MCP Server

## 验证目标

确认本节新增的最小 MCP Server 可以被 MCP Client 发现、调用和读取。

本节不需要：

```text
VMware
Docker
Qdrant
Milvus
MySQL
Redis
Java business service
真实大模型 API Key
```

## 1. 进入 ai-service

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

## 2. 运行本节自动化验证

```powershell
uv run pytest tests\test_minimal_mcp_server.py
```

预期结果：

```text
3 passed
```

这说明：

```text
Client 能 list_tools。
Client 能 call_tool("add", ...)。
Client 能 read_resource("learning://hello/panpan")。
```

## 3. 可选：查看 MCP CLI

```powershell
uv run mcp --help
```

能看到 `dev`、`run`、`install` 等命令即可。

## 4. 可选：用 MCP Inspector 调试

```powershell
uv run mcp dev app\mcp_servers\minimal_server.py
```

注意：

```text
MCP Inspector 通常需要本机有 Node/npm/npx。
如果这里提示 npx 不存在或下载慢，本节不用卡住，pytest 通过即可。
```

## 5. 不建议直接用普通 curl 验证

本节 server 默认是 stdio MCP Server，不是普通 HTTP REST 服务。

所以不要这样验证：

```powershell
curl.exe http://127.0.0.1:xxxx/tools/list
```

原因：

```text
本节没有启动 HTTP transport。
MCP 的 tools/list 也不是普通 REST URL。
```
