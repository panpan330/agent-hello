# 可观测性真实接入：设计文档

日期：2026-08-06
状态：已获用户逐节认可（方案 A）

## 1. 背景与目标

### 问题

当前 `projects/ai-service` 的可观测性是**"纸上设计"**：

- `app/agents/langsmith_tracing.py`（341 行）与 `app/agents/otel_tracing.py`（487 行）是纯函数工具模块——**零 import langsmith/opentelemetry**，只产出"plan/signal"数据类，从不真实上报。
- 生产链路只有自定义 `X-Trace-Id` 字符串（`app/core/trace.py`）+ 结构化日志（`app/core/logging.py`），**无运行时 span 概念**。
- `langsmith_tracing.py` 的 `to_langgraph_config()` 产物从未被 graph invoke 消费；`app/main.py` 无任何 tracing 初始化。
- 依赖缺失：`langsmith`/`opentelemetry-sdk`/`opentelemetry-exporter-otlp` 均未声明（仅 api 层传递依赖）。
- 学习笔记（`notes/stage6-26/27`）明确说"这一节先不真实上报……后续事项"——意图清晰，从未实施。

### 目标

把可观测性从"学习型适配"升级为**真实接入**：

```text
Vue 前端 ──> Python AI 服务 (FastAPI :8000)
                │  app/core/telemetry.py（新，统一初始化）
                │    ├─ TracerProvider + OTLP exporter → 本机 Docker Collector :4317
                │    └─ LangSmith 条件配置（有 key 才启用）
                │
                ├─ HTTP 层：trace middleware（现有）升级为 OTEL span
                │    └─ span: "http.request"
                ├─ Agent 层：console_agent_service graph invoke 包 span
                │    └─ span: "agent.invoke" + graph config 传 to_langgraph_config()
                ├─ LLM 层：LLM 调用包 span
                │    └─ span: "llm.call"
                └─ 工具层：MCP/Java 调用包 span
                     └─ span: "tool.call" / "java.call"
```

### 已确认的关键决策

1. **目标平台**：OpenTelemetry 真实接入（本机 Docker OTLP Collector :4317）+ LangSmith 条件启用。
2. **LangSmith 处理**：无 API key，条件启用——`LANGSMITH_API_KEY` 空则跳过初始化；`to_langgraph_config()` 接入 graph config，有 key 即生效。
3. **OTEL 导出**：本机 Docker 跑 OTLP Collector（localhost:4317），Python 服务经 OTLP/gRPC 导出。
4. **改造范围**：Python 服务全链路 trace；Java/前端本次不动，X-Trace-Id 契约保持。
5. **验收标准**：真实 trace 验证——Collector 中看到完整 span 树（HTTP → Agent → LLM → 工具）；既有测试全绿。

## 2. 架构与组件

### 2.1 文件组织

| 文件 | 类型 | 职责 |
| --- | --- | --- |
| `app/core/telemetry.py` | 新建 | 统一初始化：`setup_telemetry(settings)`（TracerProvider + OTLP exporter + LangSmith 条件配置）；`get_tracer()` 返回项目 tracer；`shutdown_telemetry()` flush |
| `app/agents/tracing_spans.py` | 新建 | 把现有 `otel_tracing.py` 的 span plan 翻译成真实 span：`start_agent_span` / `start_llm_span` / `start_tool_span` / `start_java_span` 辅助函数 |
| `app/core/trace.py` | 修改 | 保留 X-Trace-Id 生成；新增 `trace_id ↔ span_context` 关联（span attribute `trace_id` 与现有日志字段一致） |
| `app/main.py` | 修改 | `create_app` 接入 `setup_telemetry`；`app_lifespan` 的 shutdown 调 `shutdown_telemetry` |
| `app/middleware/tracing.py` | 修改 | HTTP 请求开 `http.request` span（method/path/status/duration） |
| `app/services/console_agent_service.py` | 修改 | graph invoke 包 `agent.invoke` span；config 传 `to_langgraph_config()` |
| `app/agents/ticket_agent.py` | 修改 | LLM 分类/字段提取/回答调用点包 `llm.call` span（经辅助函数，不改核心逻辑） |
| `app/mcp_clients/product_client.py` | 修改 | `call_tool` 包 `tool.call` span |
| `app/services/java_order_client.py` / `java_ticket_client.py` | 修改 | Java 调用包 `java.call` span |
| `app/core/config.py` | 修改 | 新增 OTEL/LangSmith 配置字段 |
| `compose.yml` 或 `docker-compose.otel.yml` | 修改/新建 | 本机 OTLP Collector 服务定义 |

### 2.2 关键设计决策

1. **现有 `otel_tracing.py` 的 span plan 保留**（供学习/测试），新增 `tracing_spans.py` 作为真实 span 适配层——两套并存，plan 不删除。
2. **telemetry 初始化失败不阻断服务**：Collector 不可达时 exporter 静默降级（OTEL 默认异步批量、失败重试有限次后丢弃），日志记录 `telemetry_export_failed`，服务照常运行。
3. **LangSmith 条件启用**：启用条件 = `LANGSMITH_TRACING=true` **且** `LANGSMITH_API_KEY` 非空，两者同时满足才初始化 LangSmith；任一不满足则跳过（不设环境变量、不传 tracing 参数）。`LANGSMITH_TRACING` 是总开关（默认 false），`LANGSMITH_API_KEY` 是凭据——缺 key 时即使开关为 true 也跳过并记一条 `langsmith_skipped_no_api_key` 日志。

## 3. Span 覆盖范围与数据流

### 3.1 Span 清单

| Span 名 | 位置 | 主要属性 | 说明 |
| --- | --- | --- | --- |
| `http.request` | `app/middleware/tracing.py` | method、path、status_code、trace_id、duration_ms | 每个 HTTP 请求一个根 span |
| `agent.invoke` | `console_agent_service.py`（reply/stream_reply） | intent、thread_id、conversation_id、node_count | Agent 图执行整体 |
| `agent.node` | 关键节点入口（可选，先做主要节点） | node_name | 图内节点级 span |
| `llm.call` | LLM 分类/字段提取/回答调用点 | model、provider、prompt_tokens、completion_tokens、total_tokens、prompt_name | 模型调用，token 统计复用现有 `extract_token_usage` |
| `tool.call` | `product_client.py` `call_tool` | tool_name、status、error_code、duration_ms | 工具执行（经 MCP 链路） |
| `java.call` | `java_order_client`/`java_ticket_client` | path、status_code、upstream_trace_id、duration_ms | Java 内部 API 调用 |

**span 层级**：`http.request`（根）→ `agent.invoke` → `llm.call` / `tool.call` / `java.call` / `agent.node`

### 3.2 Trace 关联策略

- **现有 X-Trace-Id 保留**（前端→Java 契约不变，Java 侧不本次改造）。
- **OTEL span 通过 `trace_id` attribute 关联到现有日志字段**：每个 span 记录 `trace_id`（现有 `core.trace` 的 hex 值），日志与 span 可互相检索。
- **W3C traceparent 不引入**（Java/前端未改造，本次保持 X-Trace-Id 语义；span 内部用 OTEL 自身 trace_id）。

### 3.3 数据流示例（一次"查订单"请求）

```text
HTTP 请求 → middleware 生成 X-Trace-Id → 开 http.request span
  → console_agent_service.reply → 开 agent.invoke span
      → 监督路由（LLM 或 rule）→ 开 llm.call span（如 LLM 路由）→ 关
      → order_agent 子图 → query_order_node → 开 tool.call span
          → ProductMcpClient.call_tool → 开 java.call span → Java 响应
      → 关 agent.invoke span
→ 关 http.request span → exporter 批量上报 Collector
```

### 3.4 错误处理与降级

- **Collector 不可达**：OTEL exporter 默认异步批量、失败重试有限次后静默丢弃，服务不中断；日志记录 `telemetry_export_failed`。
- **LangSmith 未配置**：跳过初始化，不设环境变量，graph config 不传 tracing 参数（`to_langgraph_config()` 返回空 dict 时跳过）。
- **span 辅助函数失败**：用 `try/finally` 保证 span 一定结束，辅助函数自身异常不影响业务逻辑。

## 4. 测试与验证策略

### 4.1 新增自动化测试（`projects/ai-service/tests/`）

| 测试文件 | 覆盖内容 | 是否需要真实依赖 |
| --- | --- | --- |
| `test_telemetry.py` | `setup_telemetry` 初始化（TracerProvider/exporter 创建）、LangSmith 条件启用（有 key/无 key 分支）、Collector 不可达降级（exporter 不抛异常）、shutdown flush | 否（mock exporter / 注入） |
| `test_tracing_spans.py` | `start_agent_span`/`start_llm_span`/`start_tool_span`：span 名/属性/层级、异常时 span 仍结束（try/finally）、trace_id attribute 与现有日志一致 | 否（内存 span exporter） |
| `test_telemetry_integration.py` | middleware → agent.invoke → tool.call 的 span 父子链（用内存 exporter 断言 span 树结构） | 否（内存 exporter） |

沿用现有约定：自动测试不调用真实模型、不连接真实 Collector/LangSmith（用内存 exporter 或 mock）。**既有 1395 测试必须保持全绿**。

### 4.2 真实 trace 验证

1. **启动本机 OTLP Collector**（Docker，暴露 :4317）。
2. 启动 Python 服务（`.env` 设 `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`）。
3. 发起一条真实 Agent 对话（如"查订单 A1001 物流"）。
4. **验证点**：
   - Collector 导出数据中能看到完整 span 树：`http.request` → `agent.invoke` → `tool.call` → `java.call`。
   - 每个 span 带 `trace_id` attribute，与 AI 服务日志中的 X-Trace-Id 一致（可交叉检索）。
   - LangSmith 条件启用验证：未配 key 时服务正常启动无报错、无上报；配 key 后（如有）LangGraph 上报 Agent 执行 trace。

### 4.3 质量回归

- Python：`uv run pytest -q` 全绿（既有 1395 + 新增）。
- Java：`mvn test -q` 全绿（预期无 Java 改动）。
- 前端：`npm run build` 通过（预期无前端改动）。

### 4.4 文档（简短）

- 更新交接文档第 9 节"LangSmith / OpenTelemetry"行：从"有学习型适配和本地 trace 设计；未接入真实 LangSmith 或 OTEL Collector"改为"已接入真实 OTEL（本机 Collector :4317），LangSmith 条件启用"。
- 更新第 17 节表格 + `.env.example` 新增配置项说明 + 启动步骤（Collector 先行）。

## 5. 配置项（新增，`.env.example` / `app/core/config.py`）

```text
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317   # 本机 Collector
OTEL_SERVICE_NAME=ai-service                          # 服务名（trace 中标识）
LANGSMITH_TRACING=false                               # LangSmith 条件启用开关
LANGSMITH_API_KEY=                                    # 空则不启用
```

## 6. 不在本次范围

- 不改造 Java 服务 / 前端（X-Trace-Id 契约保持，不引入 W3C traceparent）。
- 不本地部署 LangSmith（企业级许可 + K8s，不现实）；不引入 Langfuse。
- 不接 CI/CD、不接生产监控告警（另行规划）。
- 现有 `langsmith_tracing.py` / `otel_tracing.py` 的 plan 数据类保留不动（供学习/测试）。
