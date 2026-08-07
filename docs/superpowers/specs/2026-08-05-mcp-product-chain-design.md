# MCP 接入产品主链路：设计文档

日期：2026-08-05
状态：已获用户逐节认可（方案 A）

## 1. 背景与目标

### 问题

当前 `projects/ai-service` 中 MCP 仅是学习型模块：

- `app/mcp_servers/minimal_server.py` 是 stdio 传输的学习型 server，含 `query_order` / `create_ticket` 等 7 个工具的**重复实现**（参数模型、错误响应、确认/幂等/授权逻辑与 `app/tools/` 主链路各写一套，双轨并存）。
- 产品主链路 `app/agents/ticket_agent.py` 的 `query_order_node` / `create_ticket_node` **硬编码直调** `JavaOrderClient` / `JavaTicketClient`，与 MCP 完全无关。
- 无 HTTP 传输层、无常驻部署、无产品级远程 client、无传输层测试。

### 目标

把 MCP 接入产品主链路，形成真实系统形态的调用链：

```text
Vue 前端 ──> Python AI 服务 (FastAPI :8000)
                │  LangGraph Agent (ticket_agent.py)
                │   ├─ query_order_node ──┐
                │   └─ create_ticket_node ─┤ 经 MCP Client 调用
                │                          ▼
                │         MCP Server 独立进程 (streamable HTTP)
                │                          │ 复用 app/tools/ 守卫
                │                          ▼
                │         Java internal API (:18004) → MySQL
```

### 已确认的关键决策

1. **部署形态**：独立进程 + MCP 2.0 streamable HTTP（`FastMCP.run(transport="streamable-http")`）。
2. **工具定位**：业务工具 MCP 化，Agent 全量走 MCP（`query_order` / `create_ticket`），不新增模拟外部系统。
3. **代码组织**：ai-service 内独立入口 + 复用现有守卫，消除双轨；学习型 `minimal_server.py` 保留。
4. **验收标准**：真实联调演示走通订单查询 + 工单创建两条路径；既有测试全绿。
5. **安全哲学**：MCP server 自行校验确认凭证（写操作后端自验证），确认存储从进程内存迁移到 Redis。

## 2. 架构与组件

| 组件 | 位置 | 职责 |
| --- | --- | --- |
| 产品级 MCP server（新，独立进程） | `app/mcp_servers/product_server.py` | FastMCP + streamable HTTP，暴露 `query_order`、`create_ticket` 业务工具；复用 `app/tools/` 的授权/确认/幂等守卫与 Java client |
| 产品级 MCP client（新） | `app/mcp_clients/product_client.py` | 封装 `streamablehttp_client`：连接管理、超时、重试、认证 header、工具结果 Pydantic 校验 |
| Agent 改造 | `app/agents/ticket_agent.py` | `query_order_node` / `create_ticket_node` 由直调 Java 改为经 MCP client 调用 |
| 配置 | `.env.example` / `app/core/config.py` | 新增 MCP server URL、内部 token、超时等 |
| 学习型 server | `app/mcp_servers/minimal_server.py` | 保留不动，继续供学习/调试 |

### 2.1 产品级 MCP server（`app/mcp_servers/product_server.py`）

- 形态：`FastMCP` + `run(transport="streamable-http", host="127.0.0.1", port=9100)`（`MCP_PRODUCT_BASE_URL=http://127.0.0.1:9100/mcp`），独立进程启动入口；与学习型 `minimal_server.py` 并存。
- 工具：仅注册 `query_order`、`create_ticket` 两个业务工具（白名单，不向模型暴露 `refund_order` 等禁用项）。
- 守卫复用：server 内部通过依赖注入复用 `app/tools/` 的 `authorize_tool_call`、`run_idempotent_tool`、`ToolConfirmationStore`（Redis 版）与 `JavaOrderClient` / `JavaTicketClient`。
- 认证：请求必须携带内部 Bearer token（`MCP_PRODUCT_AUTH_TOKEN`，环境变量管理，不进前端/不提交 Git）；模型与外部 client 无此 token 无法调用。
- 工具结果：返回 MCP-safe 结构（含 `ok`、业务字段、错误码），错误经 `ToolError` 包装成 MCP 协议错误。

### 2.2 产品级 MCP client（`app/mcp_clients/product_client.py`）

- 封装 `streamablehttp_client(url, headers=...)`：连接生命周期管理、超时、重试。
- 方法：`call_tool(name, args)` → 结果经 Pydantic 校验后再交给 Agent（不信任 MCP server 返回格式之外的字段）。
- 启动时缓存 `list_tools`，工具不可用时快速失败。
- 认证 header 从配置注入。

### 2.3 Agent 改造（`app/agents/ticket_agent.py`）

- `query_order_node`：`authorize_tool_call` 校验 → 经 MCP client 调 `query_order` → 结果 Pydantic 校验 → 回答。
- `create_ticket_node`：工单字段校验 → 用户确认（Redis 确认凭证）→ 经 MCP client 调 `create_ticket`（带幂等键）→ Java 创建。
- 图结构、意图识别、回答节点保持不变，只换工具执行通道；依赖经 lambda 注入（现有模式），便于测试替换。

### 2.4 数据流（写操作确认路径）

```text
用户确认工单 → 前端 POST /tickets/confirmations/{id}/execute
  → AI 服务登记确认凭证到 Redis（ToolConfirmationStore Redis 版）
  → create_ticket_node 读确认凭证，经 MCP client 调 create_ticket
  → MCP server 校验确认凭证 + 幂等键 → Java internal API → MySQL
```

### 2.5 错误处理与降级

- MCP server 不可达：MCP client 重试（可配置次数）→ 超时 → Agent 返回"系统繁忙，请稍后再试"（不编造成功）。
- MCP 工具错误：沿用现有 `ToolError` → 转用户可读回答。
- 配置缺失（无 token/URL）：Agent 快速失败并记录明确日志，不静默降级。

## 3. 测试与验证策略

### 3.1 新增自动化测试（`projects/ai-service/tests/`）

| 测试文件 | 覆盖内容 | 是否需要真实依赖 |
| --- | --- | --- |
| `test_mcp_product_server.py` | 产品级 server 注册的工具白名单（只有 query_order/create_ticket）、认证（无 token/错 token 拒绝）、工具调用走守卫与 Java client（mock） | 否 |
| `test_mcp_product_client.py` | client 连接管理、超时/重试、`call_tool` 结果 Pydantic 校验、`list_tools` 缓存、错误包装 | 否（mock streamable HTTP） |
| `test_agent_via_mcp.py` | Agent 在 `rule_based` / `fake_llm` 模式下，工具节点经 MCP client 调用的回归（mock MCP server 或内存 client） | 否 |
| `test_tool_confirmation_redis.py` | 确认存储 Redis 版：登记/校验/过期/幂等 | 否（可用 fakeredis 或 mock） |

沿用现有测试约定：自动测试不调用真实模型、真实 Embedding/Rerank API、不写真实业务数据。既有 1288 个测试必须保持全绿。

### 3.2 真实联调验收

启动依赖后按交接文档第 6 节顺序启动，走通两条路径：

1. **订单查询路径**：AI 对话"查一下我的订单物流" → Agent 识别 `order_query` → 经 MCP server 调 Java 订单接口 → 前端流式展示回答。
2. **工单创建路径**：AI 对话"我要申请退款工单" → Agent 提取字段 → 前端确认 → 确认凭证写 Redis → MCP server 校验后调 Java 创建工单 → 工单列表可见。

验证点：AI 服务日志中能看到 MCP client → MCP server → Java 的完整 trace 链；MCP server 拒绝无 token 请求。

### 3.3 质量回归

- Python：`uv run pytest -q` 全绿。
- Java：`mvn test -q` 全绿（预期无 Java 改动，验证边界未破坏）。
- 前端：`npm run build` 通过（预期无前端改动；若有则必须跑）。

### 3.4 文档

- 更新交接文档第 17 节：MCP 状态从"未接入产品主流程"改为"已接入"，补充 MCP server 启动方式与调用链。
- 更新 `.env.example` 新增 MCP 配置项说明。

## 4. 配置项（新增，`.env.example` / `app/core/config.py`）

```text
MCP_PRODUCT_BASE_URL=            # 产品级 MCP server 地址，如 http://127.0.0.1:9100/mcp
MCP_PRODUCT_AUTH_TOKEN=          # 内部 Bearer token，Git 忽略
MCP_PRODUCT_TIMEOUT=             # 单次调用超时
MCP_PRODUCT_RETRY_COUNT=         # 重试次数
```

## 5. 不在本次范围

- 不新增模拟外部系统工具（如外部物流/CRM）。
- 不改造 Java 服务、不改前端页面。
- 不接 LangSmith/OTEL 真实平台、不接 CI/CD 部署（另行规划）。
- `app/tools/` 中 `refund_order` 保持禁用。
