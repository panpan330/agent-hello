# 退款全链路闭环 — 设计规格

> 日期：2026-08-06
> 项目：AI 客服/工单系统（Java 18004 / Python AI 8000 / Vue 5173 / MCP 9100）
> 目标：实现真实退款业务全链路（Java 接口 → Agent 工具 → 前端入口 → 审计），作为"业务功能扩展"第一个里程碑。

## 1. 背景与目标

### 1.1 现状
- `app/tools/tool_registry.py` 中 `refund_order` 是**占位**：`enabled=False`、`access_level=SENSITIVE`、`requires_confirmation=True`、**无 argument_schema**，描述为"当前阶段不允许模型调用"。全库仅此一处。
- Java 侧**无退款接口**：`/internal/orders/{orderId}` 只有 GET 查询；`/api/orders` 只有列表。无退款 controller/service/mapper 逻辑。
- orders 表（schema.sql:34-48）无 `refund_amount` / `refunded_at` / `refund_reason` 字段；`payment_status` 枚举含 `refunded`（PaymentStatus.java:6）但无配套数据。
- 意图分类（ticket_agent.py:161-168 提示词）明确把"要求直接执行退款"归为 `unsupported`（安全边界）。
- 前端：OrdersView 只读列表（已支持 refunded 状态标签）；AiChatView 有通用工单确认弹窗机制。
- 反而已支持的：知识库 DOC_REFUND_POLICY、工单 category=refund、结构化抽取意图 `refund`（schemas/structured.py:7-12）、订单列表 refunded 标签。

### 1.2 目标（用户确认的决策）
- **退款全链路闭环**：Java 接口 + 表字段 + Agent 工具 + 前端入口 + 审计。
- **业务规则**：仅未发货（order_status=unshipped）且未退款（payment_status≠refunded）的订单可退；**全额退款**。
- **必须用户确认**：复用现有 Redis 确认存储（与 create_ticket 同机制）。
- **双入口**：AI 对话触发（Agent 识别 refund_request → 确认弹窗）+ 订单页"申请退款"按钮。
- **新增独立意图 `refund_request`**（用户采纳推荐）。

## 2. 架构与数据流

```
用户(前端)
  ├─ AI 对话：说"我要退款 A1001" → Agent 识别 refund_request
  │     → 收集 order_id + reason（缺失则追问）
  │     → register_ticket_confirmation 登记确认凭证（Redis）
  │     → 前端弹确认框 → 用户确认 → (经 MCP server)
  │     → refund_order 工具（校验确认凭证）→ POST /internal/orders/{id}/refund
  │     → Java 校验 → 更新订单 → ticket_events 记录 → 返回结果 → 前端展示
  │
  └─ 订单页：点"申请退款"（仅 unshipped 且未退款订单可用）
        → 弹对话框输入原因 → 前端二次确认 → 直连 Java 退款接口
        → 刷新列表显示"已退款 ¥xx（时间）"
```

## 3. Java 后端变更

### 3.1 表结构（schema.sql）
orders 表追加 3 列（ALTER TABLE，对已有库需手动执行迁移 SQL）：
```sql
ALTER TABLE orders ADD COLUMN amount DECIMAL(10,2) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN refund_amount DECIMAL(10,2) NULL;
ALTER TABLE orders ADD COLUMN refunded_at DATETIME(6) NULL;
ALTER TABLE orders ADD COLUMN refund_reason VARCHAR(255) NULL;
```
- `refund_amount` = 实付金额（全额退款）。为支持真实金额展示，**同时新增 `amount DECIMAL(10,2) NOT NULL DEFAULT 0` 列**（订单金额，data.sql 现有订单补金额值）；refund_amount 等于 amount。
- 不新建退款表；审计复用 `ticket_events` 表（event_type='refund'，payload 存金额/原因/操作者）。
- `payment_status` 枚举已含 `refunded`，不改。

### 3.2 新接口 `POST /internal/orders/{orderId}/refund`
- 请求体：`{ "reason": "string" }`（reason 必填，非空）
- 头：`Idempotency-Key`（可选，复用 TraceHeaders.IDEMPOTENCY_KEY，与 InternalTicketController 同模式）
- 归属校验：`user_id == context.userId()`（复用 InternalRequestContext/Resolver）
- 业务校验（OrderService.refundOrder）：
  1. 订单存在，否则 404（复用 queryOrder 的查询异常语义）
  2. 归属当前调用者，否则 403
  3. `order_status == unshipped`，否则 409（或业务错误码，如 `ORDER_NOT_REFUNDABLE`，返回原因）
  4. `payment_status != refunded`，否则幂等/重复退款处理
- 幂等：复用 TicketIdempotencyCache 模式（Redis 缓存 key，重复 Idempotency-Key 返回首次结果；NoOp 实现用于测试）
- 成功后：`payment_status=refunded`、`refund_amount=<实付>`、`refunded_at=now`、`refund_reason=reason`、`latest_event=退款成功`；写 ticket_events（event_type='refund'）
- 返回 `OrderToolView`（扩展含退款字段）

> **实现偏离（2026-08-06 落地时）**：审计事件未复用 `ticket_events`，而是新建独立 `order_events` 表（tenant_id/order_id/event_type/payload 等）。原因：`ticket_events` 的 `ticket_id` NOT NULL 无法承载订单维度事件。迁移见 `projects/java-business-service/docs/refund-migration.sql`，审计写入/幂等判定均基于 `order_events`。

### 3.3 OrderService 接口扩展
```java
OrderToolView refundOrder(String orderId, String reason, InternalRequestContext context, String idempotencyKey);
```
- 实现放 OrderServiceImpl（现有 queryOrder 同文件或新增 RefundOrderService；跟随现有 impl 组织）
- 查询/归属校验复用 queryOrder 逻辑

### 3.4 OrderToolView 扩展
追加字段：`refundAmount`（BigDecimal|String|null）、`refundedAt`（String|null）、`refundReason`（String|null）。
`/api/orders` 列表（OrderListItemView）同步暴露 refundAmount/refundedAt（前端展示）。

## 4. Python Agent 侧变更

### 4.1 工具注册表解禁（app/tools/tool_registry.py）
```python
"refund_order": ToolDefinition(
    name="refund_order",
    description="发起退款操作，属于敏感业务动作，必须先让用户确认，且订单未发货才可退。",
    access_level=ToolAccessLevel.SENSITIVE,
    requires_confirmation=True,
    enabled=True,
    argument_schema=get_refund_order_args_json_schema(),
),
```
- 新增 `get_refund_order_args_json_schema()`（放 app/tools/ 或 schema 模块）：`order_id`（string, 必填）、`reason`（string, 必填）、`requester_id`（string, 可选）。

### 4.2 MCP product server 新增 refund handler（app/mcp_servers/product_server.py）
- `@server.tool()` 注册 `refund_order` → `_product_refund_order`（仿 `_product_create_ticket` 61-187 行模式）
- 签名：`refund_order(order_id, reason, confirmation_id, user_confirmed=False, requester_id=None)`
- 流程：
  1. `requester_id = requester_id or "demo_user_001"`（与 create_ticket 默认一致）
  2. `user_confirmed` 必须 True，否则返回需要确认的错误（如 `TOOL_CONFIRMATION_REQUIRED`）
  3. `store.require_confirmed(confirmation_id, actor_id=requester_id)` 校验确认凭证（Redis，跨进程共享）
  4. `authorize_tool_call(REFUND_ORDER_TOOL_NAME, user_confirmed=True)`（若工具鉴权入口如此）
  5. 调 Java：`JavaOrderClient.refund_order(orderId, reason, idempotency_key, context)` → `POST /internal/orders/{orderId}/refund`
  6. 返回成功（含退款金额/时间）或错误（映射 Java 业务错误码 → 用户可读文案，如"该订单未发货才能退款"）
- 透传 `X-User-Id`/`X-Tenant-Id`（与现有工具一致）

### 4.3 Java client 扩展（app/services/java_order_client.py 或 java_ticket_client.py）
- `JavaOrderClient` 新增 `refund_order(order_id, reason, *, idempotency_key=None, trace_context=None)`：
  - POST `/internal/orders/{order_id}/refund`，body `{"reason": reason}`，头 `Idempotency-Key` + `X-User-Id`/`X-Tenant-Id`
  - 幂等键生成：`refund:{order_id}:{user_id}:{uuid4 hex}`（调用方决定是否传）
- 错误映射：非 2xx 抛 `JavaClientError`（含 Java 错误码），由 MCP handler 转用户可读文案

### 4.4 新意图 `refund_request`（app/agents/ticket_agent.py）
- `TicketIntent` 枚举加 `refund_request`
- 提示词（161-168 行附近）：新增 `refund_request` 定义——"用户明确要求退款、退货退款、申请退款，且提供了订单号或退款对象"
- 与 `unsupported` 边界：**仅当用户要求执行退款/取消订单这类写操作时**→refund_request（取代原先归 unsupported）；仍保留"取消订单"为 unsupported（本次不做取消）
- 路由表（216-223 行附近）：`refund_request` → 新节点 `handle_refund_request`（或并入工单相关节点）
- 规则分类器 `classify_ticket_intent`（1386-1434 行）加 refund 关键词规则（"退款"/"退钱"/"申请退款"等）
- 若走多 Agent：supervisor 路由表（supervisor/supervisor_router.py:21-31）加 `refund_request` → REFUND_WORKER（或复用 TICKET_REQUEST 子图内的退款节点；**实现时按子图结构决定：若工单 worker 子图支持退款意图则映射到它，否则新增退款节点**）

### 4.5 确认交互复用
- Agent 收集 order_id + reason → `register_ticket_confirmation`（console_agent_service.py 现有机制）登记确认凭证
- 前端确认弹窗通用化：AiChatView 现有工单确认弹窗扩展支持退款类型（显示订单摘要 + 退款原因）
- 确认后 resume → 退款执行（若走 console agent 的确认-执行链，仿工单创建）

### 4.6 结构化抽取意图（schemas/structured.py）
- 已有 `refund`，复用；无需改。

## 5. 前端变更（customer-service-console）

### 5.1 AI 对话入口（AiChatView.vue）
- 确认弹窗支持退款场景：类型标识（ticket/refund）、字段（订单号、退款原因）、确认/纠错按钮
- 退款结果消息：成功（退款金额/时间）、失败（原因文案）差异化展示

### 5.2 订单页入口（OrdersView.vue）
- 列表行"申请退款"按钮：仅 `order_status=unshipped && payment_status≠refunded` 时可用（否则禁用/隐藏）
- 点击 → 弹对话框（输入退款原因）→ 前端二次确认 → **直连 Java 退款接口**（`POST /api/...`——若公开接口存在；否则复用内部接口需经网关——**设计约定：新增公开端点 `POST /api/orders/{orderId}/refund`（带用户 token 鉴权）供订单页使用**，InternalOrderController 与公开 controller 分离，实现时确认现有 /api/orders 鉴权模式）
- 成功后刷新列表，显示"已退款 ¥xx（时间）"

### 5.3 状态展示
- 订单列表/详情：refunded 显示"已退款"附金额/时间（OrderListItemView 新字段）

## 6. 测试与验收

### 6.1 Java 测试（mvn test，基线 49）
- OrderService.refundOrder 单测：成功 / 未发货校验 / 已退款重复拒绝 / 订单不存在 / 归属不符 / 幂等重复返回首次结果
- 退款事件写入验证（ticket_events）
- 新公开退款接口鉴权测试（若新增）

### 6.2 Python 测试（uv run pytest，基线 1417）
- tool_registry：refund_order enabled=True、schema 完整、SENSITIVE + requires_confirmation
- MCP handler：无确认凭证拒绝 / actor 不符拒绝 / 凭证通过执行 / Java 调用参数与 Idempotency-Key / 错误码映射
- 意图分类：refund_request 识别（"我要退款"→refund_request；"退款政策是什么"→policy_question；"取消订单"→unsupported）
- Agent 流程（fake Java client）：refund_request 路径收集→确认→执行；失败回退文案
- 前端 `npm run build` 通过

### 6.3 真实联调验收（模拟数据 + 真实服务）
启动顺序：MySQL/Redis/Qdrant → Java(18004) → MCP(9100) → Python(8000) → Vue(5173)。
- 场景 A（AI 对话）："我要退 A1001 的款" → refund_request → 收集原因 → 确认弹窗 → 确认 → Java 退款成功 → 前端"已退款"
- 场景 B（订单页）：未发货订单点"申请退款" → 输入原因 → 确认 → 成功，列表显示已退款金额/时间
- 场景 C（边界）：已发货订单申请退款 → 拒绝返回原因；重复退款（同 idempotency_key）→ 幂等返回
- 验证落库：payment_status=refunded、refund_amount/refunded_at/refund_reason 有值、ticket_events 有 refund 事件

### 6.4 迁移与数据
- 文档注明已有库执行 ALTER 迁移 SQL；schema.sql 同步更新（新建库自动生效）
- data.sql 可选补一条未发货演示订单（便于联调）

## 7. 范围外（YAGNI）
- 取消订单（cancel_order）——本次不做，unsupported 保留该场景
- 部分退款 / 任意状态退款——按用户决策排除
- LangSmith 真实上报、生产化部署——其他候选方向，不在本规格

## 8. 风险与开放点
- **公开退款接口鉴权**：/api/orders 现有鉴权模式需确认（token → user），退款接口仿之
- **多 Agent 子图映射**：refund_request 在 supervisor 下映射到哪个 worker——实现时按子图结构决定
- **迁移 SQL 对已有库手动执行**：本机 MySQL（127.0.0.1:3306，Java 服务连接）需手动跑 ALTER；schema.sql 同步更新供新建库用
- **amount 列回填**：data.sql 现有订单需补金额值（否则显示 ¥0）
