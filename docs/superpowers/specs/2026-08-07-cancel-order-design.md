# 订单取消全链路 — 设计规格

> 日期：2026-08-07
> 项目：AI 客服/工单系统（Java 18004 / Python AI 8000 / Vue 5173 / MCP 9100）
> 目标：实现订单取消业务全链路（Java 接口 → Agent 工具 → 新意图 cancel_request → 前端双入口 → 审计），作为"业务功能扩展"第二个里程碑（退款模式的 1:1 复用）。

## 1. 背景与目标

### 1.1 现状（explore 调查结论）
- 退款全链路已闭环（2026-08-06）：Java（InternalOrderController POST refund + OrderServiceImpl.refundOrder + order_events 审计 + 幂等）→ MCP（product_server `_product_refund_order` + tool_registry）→ 意图（refund_request + handle/execute 节点 + 确认中断 is_refund_execution）→ 前端（OrdersView 退款按钮 + AiChatView 确认弹窗）——**是订单取消的现成模板**
- Java 侧**无订单取消接口**：grep cancel 仅命中 `OrderStatus.java:7` 的 `CANCELED("canceled")` 枚举值（已预留）；无 controller/service/mapper/接口
- orders 表（schema.sql:34-52）：`order_status VARCHAR(32)` 自由文本 + `OrderStatus` 枚举（WAITING_SHIPMENT/SHIPPED/DELIVERED/CANCELED）——**取消状态枚举已预留**；无 canceled_at/cancel_reason 列
- 意图体系：`TicketIntent`（ticket_agent.py:61-69）7 值，**"取消订单"当前被 UNSUPPORTED_KEYWORDS 拦截**（ticket_agent.py:518）且提示词（:175）明确"要求直接取消订单→unsupported"
- 前端 OrdersView：操作列仅"申请退款"按钮（:102-115）；状态标签无 canceled

### 1.2 目标（用户确认的决策）
- **业务功能：订单取消全链路**（退款模板 1:1 复用）
- **业务规则**：仅未发货（order_status=waiting_shipment）且未取消（≠canceled）且未退款（payment_status≠refunded）可取消；取消后 order_status=canceled，记录 canceled_at/cancel_reason
- **必须用户确认**：复用 Redis 确认存储（与退款同机制）
- **双入口**：AI 对话（cancel_request 意图 → 确认弹窗）+ 订单页"取消订单"按钮
- **新意图 cancel_request**（仿 refund_request 全链路 7 处改动）

## 2. 架构与数据流

```
用户(前端)
  ├─ AI 对话：说"取消订单 A1002" → Agent 识别 cancel_request
  │     → 收集 order_id + reason（缺失则追问）
  │     → register_ticket_confirmation 登记确认凭证（Redis，tool_name=cancel_order）
  │     → 前端弹确认框 → 用户确认 → (经 MCP server)
  │     → cancel_order 工具（校验确认凭证）→ POST /internal/orders/{id}/cancel
  │     → Java 校验 → 更新订单 → order_events 记录 → 返回结果 → 前端展示
  │
  └─ 订单页：点"取消订单"（仅 waiting_shipment 且未取消/未退款可用）
        → 弹对话框输入原因 → 前端二次确认 → 直连 Java 公开接口
        → 刷新列表显示"已取消"
```

## 3. Java 后端变更

### 3.1 表结构（schema.sql）
orders 表追加 2 列（迁移 SQL 同步 docs/refund-migration.sql 或新 cancel-migration.sql——跟随退款先例）：
```sql
ALTER TABLE orders ADD COLUMN canceled_at DATETIME(6) NULL;
ALTER TABLE orders ADD COLUMN cancel_reason VARCHAR(255) NULL;
```
- 审计复用 `order_events` 表（event_type='cancel'，payload 存 reason）——退款已建，无需新表
- `OrderStatus.CANCELED` 枚举已存在，不改

### 3.2 内部接口 `POST /internal/orders/{orderId}/cancel`
- 请求体 `{"reason": "..."}`（必填非空）+ `Idempotency-Key` 头（可选）
- OrderService.cancelOrder(orderId, reason, context, idempotencyKey) 校验链（仿 refundOrder）：
  1. 正则校验 orderId → ORDER_ID_INVALID
  2. 幂等：同 key 返回首次结果（复用 TicketIdempotencyCache + order_events 落库幂等，指纹=sha256(orderId+reason+userId)）
  3. 查订单（selectByTenantIdAndOrderId）→ ORDER_NOT_FOUND
  4. 归属 visibleTo → ORDER_ACCESS_DENIED
  5. `order_status == waiting_shipment` 否则 → ORDER_NOT_CANCELABLE(409)
  6. `order_status != canceled` 且 `payment_status != refunded` 否则 → CANCEL_ALREADY_EXISTS(409)
  7. 更新：order_status=canceled、canceled_at=now、cancel_reason=reason、latest_event="订单已取消"（WHERE 加 `order_status != 'canceled'` 防并发，仿 updateRefundState 影响行数检查）
  8. 写 order_events（event_type='cancel'，payload={amount, reason}）+ 幂等 put + 刷新 Redis 缓存（复用退款缓存刷新模式）
- 返回 OrderToolView（含 canceled 字段）

### 3.3 公开接口 `POST /api/orders/{orderId}/cancel`（订单页用）
- Authorization 鉴权 → CurrentUserView → InternalRequestContext → orderService.cancelOrder（idempotencyKey=null）
- reason 长度校验 ≤200（仿 REFUND_REASON_TOO_LONG → CANCEL_REASON_TOO_LONG 422）
- 负向：无 token 401 / 缺 reason 422 / 越权 403

### 3.4 DTO 与错误码
- OrderToolView/OrderListItemView 加 `canceledAt`/`cancelReason`
- 错误码：ORDER_NOT_CANCELABLE(409)/CANCEL_ALREADY_EXISTS(409)/CANCEL_REASON_REQUIRED(422)/CANCEL_REASON_TOO_LONG(422)

## 4. Python Agent 侧变更

### 4.1 工具注册表（tool_registry.py）
```python
"cancel_order": ToolDefinition(
    name="cancel_order",
    description="取消订单操作，属于敏感业务动作，必须先让用户确认，且订单未发货才可取消。",
    access_level=ToolAccessLevel.SENSITIVE,
    requires_confirmation=True,
    enabled=True,
    argument_schema=get_cancel_order_args_json_schema(),
),
```
- `CANCEL_ORDER_TOOL_NAME = "cancel_order"` 常量；`get_cancel_order_args_json_schema()`（schemas/cancel.py：order_id 必填、reason 必填 1-200、requester_id 必填——与 refund 对齐避免 demo fallback）

### 4.2 MCP product_server（仿 `_product_refund_order`）
- `@server.tool()` 注册 `cancel_order` → `_product_cancel_order(order_id, reason, confirmation_id, user_confirmed=False, requester_id)`：
  1. user_confirmed=False → TOOL_CONFIRMATION_REQUIRED
  2. pydantic 校验 CancelOrderArgs
  3. `create_tool_confirmation_store().require_confirmed(confirmation_id, actor_id=requester_id)`
  4. `authorize_tool_call(CANCEL_ORDER_TOOL_NAME, user_confirmed=True)`
  5. `JavaOrderClient.cancel_order(order_id, reason, idempotency_key=confirmation_id)`
  6. 返回 `{ok, allowed, confirmation_checked, confirmation_id, error_code, message, cancel}`

### 4.3 JavaOrderClient.cancel_order（仿 refund_order）
- POST /internal/orders/{id}/cancel + Idempotency-Key + 错误映射（ORDER_NOT_CANCELABLE/CANCEL_ALREADY_EXISTS/CANCEL_REASON_REQUIRED/TOO_LONG → java_error_mapping.py）

### 4.4 新意图 cancel_request（ticket_agent.py，仿 refund_request 全链路）
1. `TicketIntent` Literal 加 `"cancel_request"`
2. 提示词：新增定义（"用户明确要求取消订单、退单、不要了"）；从 unsupported 描述移除"取消订单"（:175）
3. 路由表：`"cancel_request": "handle_cancel_request"`
4. `classify_ticket_intent` 关键词规则：加 CANCEL_KEYWORDS（"取消订单"/"退单"/"取消购物"），**优先级在 refund 之前**（"取消"语义先判 cancel，避免与退款混淆）；从 UNSUPPORTED_KEYWORDS 移除取消相关
5. 节点：`handle_cancel_request`（收集 order_id+reason → 确认中断）+ `execute_cancel_request`（确认后调 cancel_order）+ `cancel_request_active` 标志（仿 refund_request_active：拒绝/执行后清除防跨流误路由，仿 026a362 的修复）
6. 确认中断：worker 子图 `request_ticket_confirmation_interrupt_node` 写 `is_cancel_execution`（仿 is_refund_execution 26bf252 修复）
7. 结构化抽取意图（schemas/structured.py）：issue_type Literal 加 `'cancel'`（必须——否则 Agent 收集字段时无法生成 cancel 类型确认，前端 isCancelConfirmation 判别失效）

### 4.5 supervisor 路由
- `SupervisorRoute.CANCEL_REQUEST = "cancel_request"`；`TICKET_INTENT_TO_SUPERVISOR_ROUTE["cancel_request"]=CANCEL_REQUEST`；`SUPERVISOR_ROUTE_TABLE[CANCEL_REQUEST]="ticket_agent"`；intent→route 双映射（supervisor_graph.py）；ticket_worker 入口条件分流（仿 route_ticket_worker_entry 的 refund 分支加 cancel）

### 4.6 console 确认判别
- `_snapshot_confirmation_is_cancel_execution`（仿 is_refund_execution，从 snapshot.interrupts 读 is_cancel_execution）
- `register_ticket_confirmation` 按 is_cancel_execution 分流 tool_name=cancel_order（仿 Task 7/10 的 is_refund_execution 修复）
- `_record_exchange` 文案分流（确认取消/取消取消/修改取消信息并重新确认——仿退款文案对齐）

## 5. 前端变更（customer-service-console）

### 5.1 订单页入口（OrdersView.vue）
- 操作列加"取消订单"按钮：`order_status === 'waiting_shipment' && payment_status !== 'refunded' && order_status !== 'canceled'`
- 点击 → ElMessageBox.prompt（必填 + maxlength 100）→ 确认调 `cancelOrder` → ElMessage + 刷新
- 状态标签加 `canceled: '已取消'`；已取消显示 `已取消（canceled_at）` + cancel_reason
- businessApi.ts 加 `cancelOrder(orderId, reason)`（POST /api/orders/{id}/cancel）+ OrderListItem 类型加 canceled_at/cancel_reason

### 5.2 AI 对话确认弹窗（AiChatView.vue）
- `isCancelConfirmation()`：首选 `is_cancel_execution === true`，undefined 时 fallback `ticket_fields.issue_type === 'cancel'`（仿 isRefundConfirmation 的 flag 优先 + undefined fallback 修复 4f956ae）
- cancel 场景：标题"确认取消订单"、展示 order_id + 取消原因、按钮"确认取消/取消/修改信息"
- 气泡文案按场景区分（确认取消/取消取消/修改取消信息并重新确认，与后端 _record_exchange 对齐）
- ticket_fields 的 issue_type 支持 'cancel'（编辑表单下拉加 cancel 选项）

### 5.3 状态联动
- 取消后 latest_event="订单已取消"、can_create_ticket 保持原值（与退款一致）

## 6. 测试与验收

### 6.1 Java 测试（mvn test，基线 64 passed）
- cancelOrder 单测：未发货可取消 / 已发货拒绝（ORDER_NOT_CANCELABLE）/ 已取消拒绝（CANCEL_ALREADY_EXISTS）/ 已退款拒绝 / 订单不存在 / 归属不符 / 幂等 / reason 超长（CANCEL_REASON_TOO_LONG）
- 公开接口负向：无 token 401 / 缺 reason 422 / 越权 403
- order_events cancel 事件写入 + 并发（WHERE 条件 + 影响行数）

### 6.2 Python 测试（uv run pytest，基线 1497 passed）
- tool_registry：cancel_order enabled/SENSITIVE/确认/schema
- MCP handler：确认凭证（无凭证/actor 不符/通过）、Java 调用参数与幂等键、错误码映射
- 意图分类：cancel_request 识别（"取消订单 A1002"→cancel_request；"取消政策是什么"→policy_question；"退款"仍 refund_request 不混淆）
- Agent 流程：cancel_request 路径（收集→确认→执行）、跨流误路由防护（cancel_request_active 清除）
- supervisor：CANCEL_REQUEST 路由 + 子图映射
- console：is_cancel_execution 判别 + 文案分流

### 6.3 前端
- OrdersView 取消按钮 + canceled 展示 + AiChatView cancel 弹窗
- npm run build 通过

### 6.4 真实联调验收（启动 Java/MCP/Python/Vue）
- 场景 A（AI 对话）："取消订单 A1002" → cancel_request → 收集原因 → 确认弹窗 → 确认 → Java 取消成功 → 前端"已取消"
- 场景 B（订单页）：未发货订单点"取消订单"→ 输入原因 → 确认 → 成功，列表显示已取消
- 场景 C（边界）：已发货取消 → 409 ORDER_NOT_CANCELABLE；重复取消 → 409 CANCEL_ALREADY_EXISTS；退款后取消 → 拒绝
- 落库：order_status=canceled、canceled_at/cancel_reason 有值、order_events 有 cancel 事件

## 7. 范围外（YAGNI）
- 取消+自动退款联动（用户未选，排除）
- 任意状态可取消（用户决策排除）
- 物流详情 / 优惠券（其他候选方向，后续再做）

## 8. 风险与开放点
- **cancel_request 与 refund_request 关键词歧义**：实现时规则分类器里 cancel 优先于 refund（"取消订单"不含退款语义；若用户说"取消订单并退款"需澄清或选 cancel——设计约定 cancel 优先，报告说明）
- **issue_type 结构化抽取**：schemas/structured.py 的 issue_type Literal 必须加 'cancel'（规格 4.4 第 7 点已明确）
- **迁移 SQL**：本机 MySQL 需手动跑 ALTER（canceled_at/cancel_reason 2 列）；schema.sql 同步更新
- **AI 对话确认弹窗判别**：is_cancel_execution 标志需 worker 中断 payload 写入（仿 is_refund_execution 的跨进程链路）
