# 多 Agent 协作升级：设计文档

日期：2026-08-05
状态：已获用户逐节认可（方案 A+C）

## 1. 背景与目标

### 问题

当前 `projects/ai-service` 的客服 Agent 是**单个** LangGraph 工单 Agent（`app/agents/ticket_agent.py`，3022 行单文件，12 个节点、4 组条件路由），承担意图分类、RAG 知识库问答、订单查询、工单创建全流程。交接文档第 9 节明确列出"多 Agent 协作：当前是单个 LangGraph 工单 Agent，不是 Multi-Agent 系统"为未实现项。

### 目标

把客服 Agent 升级为**监督-工作（supervisor-worker）多 Agent 系统**：

```text
                ┌─────────────────────────────────────────┐
                │  顶层监督 Agent (Supervisor StateGraph)  │
                │  normalize_user_input                    │
                │  supervisor_route (LLM/rule 可切换)      │
                └───────┬────────┬────────┬───────────────┘
                        │        │        │
          ┌─────────────┘        │        └─────────────┐
          ▼                      ▼                      ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ 知识库问答子 Agent│   │ 订单查询子 Agent  │   │ 工单创建子 Agent  │
│ (knowledge_graph)│   │ (order_graph)    │   │ (ticket_graph)   │
│  RAG 检索/引用    │   │ 订单查询/物流     │   │ 字段提取/确认/创建 │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

### 已确认的关键决策

1. **架构形态**：监督-工作 Agent（supervisor-worker），LangGraph 嵌套子图（方案 A）。
2. **监督决策**：监督 Agent 引入 LLM 路由（`supervisor_router` LLM 模式），rule 模式保留为默认/回退（方案 C 落地）。
3. **子 Agent 划分**：3 个工作 Agent——知识库问答（RAG）、订单查询、工单创建。
4. **灰度策略**：双模式共存——保留现有单 Agent 图，新增多 Agent 监督图，配置开关切换。
5. **验收标准**：真实联调演示走通三条路径（知识库问答、订单查询、工单创建）；既有测试全绿。

## 2. 架构与组件

### 2.1 文件组织

| 新文件 | 内容 | 来源（现有代码） |
| --- | --- | --- |
| `app/agents/supervisor/supervisor_graph.py` | 顶层监督图：normalize + supervisor_route + 3 个子图节点 + 直接回答节点 | 现有 `build_ticket_agent_graph` 的框架部分（`ticket_agent.py:2420-2494`） |
| `app/agents/supervisor/supervisor_router.py` | LLM/rule 双模式路由决策 | `route_by_intent`（`ticket_agent.py:1430`）+ `LLMTicketIntentClassifier`（`ticket_agent.py:798`） |
| `app/agents/workers/knowledge_agent.py` | 知识库问答子图：retrieve_policy → decide_ticket_need | `retrieve_policy_node`（`ticket_agent.py:2012`）、`decide_ticket_need_node`（`ticket_agent.py:1469`）、`PolicyRagService` |
| `app/agents/workers/order_agent.py` | 订单查询子图：query_order | `query_order_node`（`ticket_agent.py:2035`）、`OrderQueryExecutor` |
| `app/agents/workers/ticket_worker.py` | 工单创建子图：字段提取→追问→确认→创建 | `extract_ticket_fields_node`（`ticket_agent.py:2131`）、`ask_missing_ticket_fields_node`（`ticket_agent.py:2159`）、`request_ticket_confirmation_node`（`ticket_agent.py:2171`）、`create_ticket_node`（`ticket_agent.py:2258`）、`TicketCreator` |
| `app/agents/ticket_agent.py` | **保留不动**（单 Agent 模式继续可用） | — |

### 2.2 双模式切换

`console_agent_service._build_graph` 按配置选择构建多 Agent 监督图或现有单 Agent 图：

```python
if settings.agent_multi_agent_enabled:
    graph = build_supervisor_graph(...)   # 多 Agent 监督图
else:
    graph = build_ticket_agent_graph_for_model_mode(...)  # 现有单 Agent 图
```

**与 MCP 链路的关系（正交、可叠加）**：多 Agent 模式下的订单查询子图与工单创建子图**继续复用上一轮已完成的 MCP executor/creator**（`McpTicketCreator` / `create_mcp_order_query_executor`，受 `AGENT_MCP_TOOLS_ENABLED` 独立控制）。即 `AGENT_MULTI_AGENT_ENABLED` 决定 Agent 组织形态，`AGENT_MCP_TOOLS_ENABLED` 决定工具执行通道，两者互不冲突：多 Agent + MCP、多 Agent + 直连 Java、单 Agent + MCP、单 Agent + 直连均可用。子图构建时复用 `console_agent_service._build_graph` 现有的工具注入逻辑（MCP/直连分叉），仅替换图框架。

## 3. 状态模型与数据流

### 3.1 状态拆分

现有 `TicketAgentState`（约 50 字段，`ticket_agent.py:375-427`）拆分为**顶层监督 state + 子图私有 state**：

```text
SupervisorState（顶层，监督图共享）:
  user_message / normalized_message / agent_trace_id / intent / intent_reason
  final_answer / node_history / agent_error_*

KnowledgeWorkerState（知识库问答子图）:
  rag_query / rag_answer_status / rag_citations / rag_no_context_reason
  rag_suggestions /（输出）final_answer

OrderWorkerState（订单查询子图）:
  order_query_order_id / order_query_status / order_query_result
  order_query_error_* /（输出）final_answer

TicketWorkerState（工单创建子图）:
  ticket_fields / missing_fields / ticket_confirmation_approved
  pending_ticket_confirmation / ticket_creation_* / created_ticket /（输出）final_answer
```

子图通过**顶层 state 的子集字段**与监督图通信（LangGraph 子图嵌套的 state 传递机制）：监督图把 `normalized_message` 传入子图，子图把 `final_answer`/结果字段写回顶层。

### 3.2 数据流

**监督路由**：

```text
用户消息 → normalize_user_input → supervisor_route
  → [LLM 或 rule] 判定 intent:
      knowledge_question → knowledge 子图
      order_query       → order 子图
      ticket_request    → ticket 子图
      smalltalk         → build_direct_answer（监督图内节点）
      unsupported       → build_unsupported_answer
      unclear           → ask_clarifying_question
```

**跨 Agent 协作**（监督层处理）：

- 知识库子图返回 `rag_answer_status=no_context` → 监督层判定是否转工单（现有 `decide_ticket_need` 的 `rag_no_context` 逻辑上移到监督层）
- 工单子图 `request_ticket_confirmation` interrupt → 顶层 `graph.stream` 照常发出 `__interrupt__`（复用现有协议）

### 3.3 LLM 路由实现

`supervisor_router` 新增 `LLMSupervisorRouter`：复用 `LLMTicketIntentClassifier` 的调用封装（prompt → structured output → Pydantic 校验 → rule fallback），输出受限枚举：

```python
class SupervisorRoute(StrEnum):
    KNOWLEDGE_QUESTION = "knowledge_question"
    ORDER_QUERY = "order_query"
    TICKET_REQUEST = "ticket_request"
    SMALLTALK = "smalltalk"
    UNSUPPORTED = "unsupported"
    UNCLEAR = "unclear"
```

rule 模式复用现有 `route_by_intent` 关键词逻辑。双模式经 `SUPERVISOR_ROUTER_MODE` 配置切换（默认 rule，联调时切 LLM）。

### 3.4 协议不变

- interrupt 确认、`MemorySaver`/`RedisSaver` checkpoint、`graph.stream(stream_mode="updates")`、`graph.get_state` 全部复用现有机制
- `console_agent_service` 的 `reply`/`stream_reply`/`decide_ticket_confirmation` **零改动**（子图嵌套对上层透明）

## 4. 测试与验证策略

### 4.1 新增自动化测试（`projects/ai-service/tests/`）

| 测试文件 | 覆盖内容 | 是否需要真实依赖 |
| --- | --- | --- |
| `test_supervisor_router.py` | 监督路由：rule 模式各意图分类、LLM 模式（fake LLM）输出 → 路由枚举、LLM 失败 → rule fallback、未知输出 → unclear | 否（fake LLM） |
| `test_supervisor_graph.py` | 顶层监督图：各意图路由到正确子图、跨 Agent 协作（RAG no_context → 转工单）、interrupt 确认照常发出、子图结果回写顶层 state | 否（fake service） |
| `test_knowledge_agent.py` | 知识库子图：RAG 检索/引用/无上下文拒答/转工单决策 | 否（fake RAG） |
| `test_order_agent.py` | 订单子图：查询成功/失败/缺订单号 | 否（fake executor） |
| `test_ticket_worker_agent.py` | 工单子图：字段提取/缺字段追问/确认/创建（复用现有 fake creator） | 否 |
| `test_multi_agent_console.py` | console_agent_service 多 Agent 模式端到端（rule 模式）：对话 → 路由 → 子图 → 回答/确认 | 否（rule_based + fake） |

沿用现有约定：自动测试不调用真实模型、不写真实业务数据。**既有 1349 个测试必须保持全绿**（单 Agent 模式不动）。

### 4.2 真实联调验收

启动依赖后（MySQL/Redis/Qdrant/VM/模型 API），`AGENT_MULTI_AGENT_ENABLED=true` + `SUPERVISOR_ROUTER_MODE=llm`，走通三条路径：

1. **知识库问答路径**：AI 对话"退货政策是什么" → 监督 LLM 路由 → knowledge 子图 → RAG 引用回答
2. **订单查询路径**：AI 对话"查一下我的订单 A1001 物流" → 监督 LLM 路由 → order 子图 → MCP → Java 订单数据
3. **工单创建路径**：AI 对话"我要申请退款工单" → 监督 LLM 路由 → ticket 子图 → 字段提取 → 确认 → 创建

验证点：AI 服务日志能看到**监督 Agent 路由决策 + 子 Agent 执行**的协作链（`supervisor_routed intent=... worker=...` 日志）；前端对话流式展示不变。

### 4.3 质量回归

- Python：`uv run pytest -q` 全绿（既有 1349 + 新增）
- Java：`mvn test -q` 全绿（预期无 Java 改动）
- 前端：`npm run build` 通过（预期无前端改动）

### 4.4 文档（简短）

- 更新交接文档第 9 节"多 Agent 协作"行：从"当前是单个 LangGraph 工单 Agent"改为"已升级为监督-工作多 Agent（可配置开关）"
- 更新第 17 节表格 + `.env.example` 新增配置项说明

## 5. 配置项（新增，`.env.example` / `app/core/config.py`）

```text
AGENT_MULTI_AGENT_ENABLED=false    # 默认单 Agent，多 Agent 模式开关
SUPERVISOR_ROUTER_MODE=rule        # rule | llm，监督路由模式
```

## 6. 不在本次范围

- 不新增质检 Agent / 更多子 Agent（后续可扩展）
- 不改 Java 服务、不改前端页面
- 不引入新的第三方依赖
- `ticket_agent.py` 单 Agent 代码保留不动，仅作为可选项
