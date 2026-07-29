# 阶段 8 第 11 节手动验证：MCP Client 调试

## 验证目标

确认 MCP Client 能连接第 10 节的最小 MCP Server，并完成：

```text
list_tools
call_tool add
call_tool echo
read_resource learning://hello/panpan
```

本节不需要打开：

```text
VMware
Docker
Qdrant
Milvus
MySQL
Redis
Java business service
真实大模型
```

## 1. 进入 ai-service

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

## 2. 运行 MCP Client 调试脚本

```powershell
uv run python scripts\mcp_client_smoke.py
```

预期看到 JSON，包含：

```text
server
tools
tool_calls
resource_reads
```

重点检查：

```text
tools 里有 add 和 echo。
tool_calls.add.structured_content.result 是 12。
tool_calls.echo.structured_content.result 是 hello mcp。
resource_reads 里有 learning://hello/panpan。
```

## 3. 运行聚焦测试

```powershell
uv run pytest tests\test_mcp_client_smoke.py tests\test_minimal_mcp_server.py
```

预期：

```text
4 passed
```

## 4. 如果看到中文乱码

优先怀疑 PowerShell 输出编码问题。

可以临时执行：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

本节脚本已经使用：

```python
json.dumps(..., ensure_ascii=False, indent=2)
```

正常情况下不会把中文强制转成 `\uXXXX`。
