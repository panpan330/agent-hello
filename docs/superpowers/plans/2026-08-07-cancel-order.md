# 订单取消全链路 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现订单取消业务全链路：Java 取消接口与审计 → Agent 取消工具（MCP + 确认）→ 新意图 cancel_request → 前端双入口 → 测试与真实联调验收。

**Architecture:** 退款全链路（2026-08-06）的 1:1 模板复用——Java（orders +2 列、cancelOrder 校验链/幂等/审计/公开接口）、Python（cancel_order 工具 + MCP handler + 新意图 cancel_request 全链路 + supervisor 路由 + 确认判别）、前端（订单页取消按钮 + AI 对话确认弹窗）、测试（Java/Python/前端/真实联调三场景）。

**Tech Stack:** Java 17 + Spring Boot 3（MyBatis）+ MySQL；Python 3.12 + FastAPI + LangGraph + MCP SDK；Vue 3 + Element Plus；pytest；maven。

## Global Constraints

- 自动测试不调用真实模型、不命中真实 Embedding/Rerank API、不写入真实业务数据、不依赖真实 Redis。
- 现有测试套件保持绿色：Python `uv run pytest -q` = 1497 passed；Java `mvn test -q` = 64 passed；前端 `npm run build` 通过。
- 不新增第三方依赖。
- 取消规则：仅 `order_status == waiting_shipment` 且 `order_status != canceled` 且 `payment_status != refunded` 可取消；取消后 order_status=canceled + canceled_at/cancel_reason + latest_event="订单已取消"。
- 必须用户确认：复用 `create_tool_confirmation_store` 的 `require_confirmed`；MCP 路径 confirmation_id 即幂等键。
- `cancel_order` 工具：SENSITIVE + requires_confirmation=True + enabled=True + schema（order_id/reason 必填、requester_id 必填——与 refund 对齐）。
- 意图边界：取消诉求 → `cancel_request`；"取消订单"从 UNSUPPORTED_KEYWORDS（ticket_agent.py:518）移除；cancel 关键词优先级高于 refund（"取消订单"不含退款语义）。
- issue_type 结构化抽取（schemas/structured.py）必须加 `'cancel'`。
- 确认判别：worker 中断 payload 写 `is_cancel_execution`（仿 is_refund_execution）；register_ticket_confirmation tool_name 三分支（cancel/refund/create_ticket）。
- 迁移 SQL：本机 MySQL 手动跑 ALTER（canceled_at/cancel_reason 2 列）；schema.sql 同步更新。
- 本地 git commit；不推送 GitHub。

---

### Task 1: Java 表结构 + 实体/DTO + 迁移 SQL

**Files:**
- Modify: `projects/java-business-service/src/main/resources/schema.sql:34-52`（orders 表）
- Modify: `projects/java-business-service/docs/refund-migration.sql`（或新建 cancel-migration.sql——跟随退款先例，追加 2 条 ALTER）
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/entity/Order.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/dto/OrderToolView.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/dto/OrderListItemView.java`
- Modify: `projects/java-business-service/src/main/resources/mapper/OrderMapper.xml`（OrderColumns/OrderResultMap 加列）
- Test: `projects/java-business-service/src/test/java/com/panpan/aibusinessservice/InternalOrderControllerTest.java`

**Interfaces:**
- Consumes: 现有 `Order` entity（含退款字段 refundedAt/refundReason）、`OrderToolView`/`OrderListItemView`（refund 字段）
- Produces: `Order` 新增 `canceledAt`/`cancelReason` + getter/setter；DTO 同步（Task 2/3 使用）

- [ ] **Step 1: schema.sql orders 表 +2 列**

在 `schema.sql` orders 表（refund 列 :45-47 后）追加：
```sql
  canceled_at DATETIME(6) NULL,
  cancel_reason VARCHAR(255) NULL,
```

- [ ] **Step 2: 迁移 SQL 追加 2 条 ALTER**

`docs/refund-migration.sql` 末尾追加（或新建 cancel-migration.sql）：
```sql
ALTER TABLE orders ADD COLUMN canceled_at DATETIME(6) NULL;
ALTER TABLE orders ADD COLUMN cancel_reason VARCHAR(255) NULL;
```

- [ ] **Step 3: Order entity 加 2 字段**

`Order.java` 加 `LocalDateTime canceledAt`、`String cancelReason` + getter/setter（仿 refundedAt/refundReason）。

- [ ] **Step 4: OrderToolView/OrderListItemView 加字段**

两 DTO 加 `canceledAt`/`cancelReason`（nullable）+ `from()` 同步填充（refund 字段后）。

- [ ] **Step 5: OrderMapper.xml 加列**

`OrderColumns`（:23-38）与 `OrderResultMap`（:6-21）在 refund 列后加 `canceled_at, cancel_reason` 与对应 `<result>`。

- [ ] **Step 6: 跑 Java 编译与现有测试**

Run: `cd projects/java-business-service && mvn test -q`
Expected: BUILD SUCCESS，64 passed（编译通过即可）

- [ ] **Step 7: Commit**

```bash
git add projects/java-business-service/
git commit -m "feat: add order cancel columns to schema, entity and DTOs"
```

---

### Task 2: Java 内部取消接口（InternalOrderController + OrderService）

**Files:**
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/controller/InternalOrderController.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/service/OrderService.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/service/impl/OrderServiceImpl.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/exception/BusinessErrorCode.java`
- Modify: `projects/java-business-service/src/main/resources/mapper/OrderMapper.xml`（updateCancelState）
- Test: `projects/java-business-service/src/test/java/com/panpan/aibusinessservice/InternalOrderControllerTest.java`

**Interfaces:**
- Consumes: Task 1 的 Order 新字段；现有 `refundOrder`/`applyRefund` 模板（impl:70-227）；幂等三件套（normalizeIdempotencyKey :130-135/fingerprint :240-253/findRefundedOrderByIdempotency :137-169）
- Produces: `OrderService.cancelOrder(String orderId, String reason, InternalRequestContext context, String idempotencyKey) -> OrderToolView`；`POST /internal/orders/{orderId}/cancel`；错误码 `ORDER_NOT_CANCELABLE(409)`/`CANCEL_ALREADY_EXISTS(409)`/`CANCEL_REASON_REQUIRED(422)`/`CANCEL_REASON_TOO_LONG(422)`；`orderMapper.updateCancelState`（WHERE `order_status != 'canceled'` + 影响行数）

- [ ] **Step 1: 写失败测试（InternalOrderControllerTest 追加，仿退款测试 :142-309）**

```java
@Test void cancelOrderReturnsToolFacingView() // A1002（waiting_shipment）→ 200 且 orderStatus=canceled、canceledAt 有值
@Test void cancelOrderDeniesShippedOrder() // A1001（shipped）→ 409 ORDER_NOT_CANCELABLE
@Test void cancelOrderDeniesAlreadyCanceled() // 已取消再取消 → 409 CANCEL_ALREADY_EXISTS
@Test void cancelOrderIsIdempotentForSameKey() // 同 key 重复返回首次结果
@Test void cancelOrderRejectsOtherUsersOrder() // U2001 订单被 U1001 取消 → 403
@Test void cancelOrderRejectsNullBody() // body null → 422 CANCEL_REASON_REQUIRED
@Test void cancelOrderRejectsReasonTooLong() // reason >200 → 422 CANCEL_REASON_TOO_LONG
@Test void updateCancelStateSkipsAlreadyCanceledRow() // WHERE 条件保护，首刷 1 行、已取消后 0 行
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: BusinessErrorCode 加 4 个错误码**

仿 refund（:17-20）：ORDER_NOT_CANCELABLE(CONFLICT)/CANCEL_ALREADY_EXISTS(CONFLICT)/CANCEL_REASON_REQUIRED(422)/CANCEL_REASON_TOO_LONG(422)。

- [ ] **Step 4: OrderService 接口加 cancelOrder + impl 实现**

仿 refundOrder（impl:70-112）：
```java
public OrderToolView cancelOrder(String orderId, String reason, InternalRequestContext context, String idempotencyKey) {
    // 1. 正则校验 orderId（ORDER_ID_PATTERN）
    // 2. reason 超长校验（CANCEL_REASON_MAX_LENGTH = 200 → CANCEL_REASON_TOO_LONG）
    // 3. 幂等三件套：normalizeIdempotencyKey → fingerprint → findCanceledOrderByIdempotency（仿 findRefundedOrderByIdempotency :137-169，缓存/事件表双查）
    // 4. loadOrder（cache→DB）→ checkAccess
    // 5. orderStatus == WAITING_SHIPMENT 否则 ORDER_NOT_CANCELABLE
    // 6. orderStatus != CANCELED 且 paymentStatus != REFUNDED 否则 CANCEL_ALREADY_EXISTS
    // 7. applyCancel：置 orderStatus=CANCELED、canceledAt=now、cancelReason=reason、latestEvent="订单已取消"
    //    → updateCancelState（WHERE order_status != 'canceled'，影响行数 0 → CANCEL_ALREADY_EXISTS）
    //    → orderCache.put 刷新 → insertOrderEvent(event_type="cancel", payload={amount, reason})
    //    → 幂等 put
    // 8. DuplicateKeyException 并发兜底（仿 refund :105-111）
}
```

- [ ] **Step 5: InternalOrderController 加 POST /{orderId}/cancel**

仿 refundOrder（:44-63）：`@RequestBody(required=false) Map<String,String> body` + Idempotency-Key 头 + reason 校验（null/blank → CANCEL_REASON_REQUIRED）。

- [ ] **Step 6: OrderMapper.xml 加 updateCancelState**

仿 updateRefundState（:65-76），WHERE 加 `AND order_status != 'canceled'`，返回 int 影响行数。

- [ ] **Step 7: 跑测试确认通过 + 全量 mvn test**

Run: `cd projects/java-business-service && mvn test -q`
Expected: 8 新测试 + 原有全过

- [ ] **Step 8: Commit**

```bash
git add projects/java-business-service/
git commit -m "feat: add cancel order internal endpoint with idempotency and audit"
```

---

### Task 3: Java 公开取消接口（订单页用）

**Files:**
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/controller/OrderController.java`
- Test: `projects/java-business-service/src/test/java/com/panpan/aibusinessservice/PublicOrderTicketControllerTest.java`

**Interfaces:**
- Consumes: Task 2 的 `OrderService.cancelOrder`
- Produces: `POST /api/orders/{orderId}/cancel`（Authorization 鉴权，idempotencyKey=null）

- [ ] **Step 1: 写失败测试（PublicOrderTicketControllerTest 追加，仿退款 :514-594）**

```java
@Test void customerCanCancelOwnUnshippedOrder() // A1002 → 200 且 orderStatus=canceled
@Test void customerCannotCancelShippedOrder() // A1001 → 409
@Test void customerCannotCancelWithoutToken() // 无 token → 401
@Test void customerCannotCancelWithoutReason() // 缺 reason → 422
@Test void customerCannotCancelOthersOrder() // U2001 的 A2001 → 403
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: OrderController 加 POST /{orderId}/cancel**

仿 refundOrder（:50-76）：`authService.currentUser(authorization)` → InternalRequestContext → `orderService.cancelOrder(orderId, reason, context, null)`。

- [ ] **Step 4: 跑测试确认通过 + 全量 mvn test + Commit**

```bash
cd projects/java-business-service && mvn test -q
git add projects/java-business-service/
git commit -m "feat: add public cancel endpoint for order page"
```

---

### Task 4: Python JavaOrderClient.cancel_order + schemas/cancel.py

**Files:**
- Modify: `projects/ai-service/app/services/java_order_client.py`
- Create: `projects/ai-service/app/schemas/cancel.py`
- Modify: `projects/ai-service/app/services/java_error_mapping.py`（错误码映射）
- Test: `projects/ai-service/tests/test_java_order_client.py`

**Interfaces:**
- Consumes: `refund_order` 模式（java_order_client.py:131-247）；`RefundOrderArgs` 模式（schemas/refund.py）
- Produces: `JavaOrderClient.cancel_order(order_id: str, reason: str, *, idempotency_key=None, trace_context=None) -> dict`（POST /internal/orders/{id}/cancel）；`CancelOrderArgs`（schemas/cancel.py：order_id/reason(1-200)/requester_id(1-64) 必填，extra=forbid）；`get_cancel_order_args_json_schema()`；错误码映射 ORDER_NOT_CANCELABLE/CANCEL_ALREADY_EXISTS/CANCEL_REASON_REQUIRED/TOO_LONG

- [ ] **Step 1: 写失败测试（test_java_order_client.py 追加，仿 refund :323/:360）**

```python
def test_cancel_order_sends_post_with_reason_and_idempotency_key():
    # mock POST /internal/orders/A1002/cancel → 断言方法/body/头
def test_cancel_order_maps_business_error():
    # mock 409 ORDER_NOT_CANCELABLE → AppException code 含 ORDER_NOT_CANCELABLE
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: 实现 schemas/cancel.py**

仿 schemas/refund.py：`CancelOrderArgs`（order_id 必填、reason 必填 1-200、requester_id 必填 1-64，extra=forbid）+ `get_cancel_order_args_json_schema()`。

- [ ] **Step 4: 实现 JavaOrderClient.cancel_order + 错误映射**

仿 refund_order（:131-247）：path `/internal/orders/{order_id}/cancel`，body `{"reason": reason}`，Idempotency-Key 头；`java_error_mapping.py` 加 ORDER_NOT_CANCELABLE(409)/CANCEL_ALREADY_EXISTS(409)/CANCEL_REASON_REQUIRED(422)/CANCEL_REASON_TOO_LONG(422)。

- [ ] **Step 5: 跑测试确认通过 + 相关套件 + Commit**

```bash
cd projects/ai-service && uv run pytest tests/test_java_order_client.py -q
git add projects/ai-service/
git commit -m "feat: add cancel_order to Java order client and cancel schema"
```

---

### Task 5: Python 工具注册表 + MCP handler

**Files:**
- Modify: `projects/ai-service/app/tools/tool_registry.py`
- Modify: `projects/ai-service/app/mcp_servers/product_server.py`
- Test: `projects/ai-service/tests/test_tool_registry.py` + `tests/test_mcp_product_server.py`

**Interfaces:**
- Consumes: Task 4 的 `CancelOrderArgs`/`get_cancel_order_args_json_schema`、`JavaOrderClient.cancel_order`；`REFUND_ORDER_TOOL_NAME` 常量模式（tool_registry.py:11）
- Produces: `CANCEL_ORDER_TOOL_NAME = "cancel_order"`；tool_registry 加 cancel_order（SENSITIVE + 确认 + schema）；MCP `_product_cancel_order` + `@server.tool()` 注册（confirmation_id pattern、requester_id 必填）

- [ ] **Step 1: 写失败测试（test_tool_registry.py + test_mcp_product_server.py 追加，仿 refund）**

```python
# test_tool_registry.py
def test_cancel_order_tool_is_enabled_and_requires_confirmation():
    # enabled=True, SENSITIVE, requires_confirmation=True, schema 含 order_id/reason/requester_id
# test_mcp_product_server.py
def test_product_cancel_order_requires_user_confirmation()  # user_confirmed=False → TOOL_CONFIRMATION_REQUIRED
def test_product_cancel_order_validates_confirmation_id_format()  # 非法 confirmation_id → 参数校验失败
def test_product_cancel_order_sets_business_context_before_java_call()  # set_business_context 被调用
def test_product_cancel_order_confirmation_unavailable_mapped_to_ok_false()
def test_product_cancel_order_success_returns_cancel()
def test_product_cancel_order_rejects_missing_requester_id()  # 空 → INVALID_TOOL_ARGUMENTS
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: tool_registry 加 cancel_order**

仿 refund_order（:31-38）：`CANCEL_ORDER_TOOL_NAME` 常量 + ToolDefinition（SENSITIVE/确认/enabled/schema=get_cancel_order_args_json_schema()）。

- [ ] **Step 4: product_server 加 _product_cancel_order + 注册**

仿 `_product_refund_order`（:211-332）+ refund_order 注册（:393-417）：user_confirmed 校验 → pydantic → require_confirmed(actor_id=requester_id) → authorize_tool_call(CANCEL_ORDER_TOOL_NAME, user_confirmed=True) → set_business_context → run_idempotent_tool(confirmation_id 幂等键) → JavaOrderClient.cancel_order → 返回 `{ok, allowed, confirmation_checked, confirmation_id, error_code, message, cancel}`。

- [ ] **Step 5: 跑测试确认通过 + 相关套件 + Commit**

```bash
cd projects/ai-service && uv run pytest tests/test_tool_registry.py tests/test_mcp_product_server.py -q
git add projects/ai-service/
git commit -m "feat: add cancel_order tool to registry and product MCP server"
```

---

### Task 6: Python 新意图 cancel_request（单 Agent ticket_agent）

**Files:**
- Modify: `projects/ai-service/app/agents/ticket_agent.py`
- Modify: `projects/ai-service/app/schemas/structured.py`（TicketIntent 加 CANCEL）
- Modify: `projects/ai-service/app/agents/mcp_tool_adapters.py`（register_ticket_confirmation 三分支）
- Test: `projects/ai-service/tests/test_ticket_agent_intent.py`

**Interfaces:**
- Consumes: `refund_request` 全链路模板（ticket_agent.py:2583-2780）；Task 5 的 cancel_order 工具
- Produces: `TicketIntent` 加 `"cancel_request"`；`issue_type` Literal 加 `'cancel'`；CANCEL_KEYWORDS/CANCEL_ACTION_PHRASES/CANCEL_WITH_ORDER_PATTERN；`handle_cancel_request_node`/`execute_cancel_request_node`/`cancel_request_active` 标志；`is_cancel_execution` 写入中断 payload；register_ticket_confirmation tool_name 三分支

- [ ] **Step 1: 写失败测试（test_ticket_agent_intent.py 追加，仿 refund :241-275/:1427-1600）**

```python
def test_classify_cancel_request_intent():
    # "取消订单 A1002" → cancel_request
    # "退单" → cancel_request
def test_classify_cancel_policy_question_still_policy():
    # "取消政策是什么" → policy_question（不误伤）
def test_classify_refund_still_refund():
    # "我要退 A1002 的款" → refund_request（cancel 优先不混淆）
# 注意：改写现有 test_classify_cancel_order_still_unsupported（:278-280）——"取消订单"现在应 → cancel_request
def test_execute_cancel_request_node_blocks_without_user_confirmation()
def test_interrupting_graph_resumes_approved_cancel_to_execute_cancel_order()
def test_interrupting_graph_clears_cancel_flag_after_rejection_before_ticket_creation()  # 跨流防误路由
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: 意图扩展（仿 refund）**

1. `TicketIntent` Literal 加 `"cancel_request"`
2. 提示词（:165-178）：新增 cancel_request 定义；unsupported 描述（:175）移除"要求直接取消订单"
3. 路由表（:226-251）：`"cancel_request": "handle_cancel_request"` + confirmation routes `execute_cancel_request` + fixed edges
4. `classify_ticket_intent`（:1485-1543）：UNSUPPORTED_KEYWORDS（:517-531）移除"取消订单"；新增 CANCEL_KEYWORDS（"取消订单"/"退单"/"取消购物"）/CANCEL_ACTION_PHRASES/CANCEL_WITH_ORDER_PATTERN/CANCEL_QUERY_WORDS；`_is_cancel_request` 判定**优先级在 refund 之前**（:1455-1482 之前）
5. `schemas/structured.py` TicketIntent 加 `CANCEL = "cancel"`
6. 节点：`handle_cancel_request_node`（收集 order_id+reason → 置 cancel_request_active=True → 确认中断）+ `execute_cancel_request_node`（确认后调 cancel_order → 成功清标志）+ `build_cancel_ticket_fields`（issue_type:"cancel"）+ `find_missing_cancel_fields` + `has_active_cancel_collection` + `route_by_cancel_fields` + `build_cancel_failure_state`
7. 中断 payload：`build_ticket_confirmation_interrupt_payload`（:1797-1808）写 `is_cancel_execution = state.get("cancel_request_active") is True`
8. `request_ticket_confirmation_interrupt_node`（:2355-2439）：拒绝后清 cancel_request_active（仿 refund :2431-2435）
9. `mcp_tool_adapters.register_ticket_confirmation`（:258）tool_name 三分支：`CANCEL_ORDER_TOOL_NAME if is_cancel_execution else (REFUND_ORDER_TOOL_NAME if is_refund_execution else CREATE_TICKET_TOOL_NAME)`

- [ ] **Step 4: 跑测试确认通过 + 相关套件**

- [ ] **Step 5: 全量 pytest + Commit**

Run: `cd projects/ai-service && uv run pytest -q`
```bash
git add projects/ai-service/
git commit -m "feat: add cancel_request intent to ticket agent"
```

---

### Task 7: supervisor 路由 + console 确认判别 + worker 入口分流

**Files:**
- Modify: `projects/ai-service/app/agents/supervisor/supervisor_router.py`
- Modify: `projects/ai-service/app/agents/supervisor/supervisor_graph.py`
- Modify: `projects/ai-service/app/agents/workers/ticket_worker.py`（入口分流 + 清残留标志）
- Modify: `projects/ai-service/app/services/console_agent_service.py`（is_cancel_execution 判别 + 文案分流）
- Test: `projects/ai-service/tests/test_supervisor_router.py` + `tests/test_supervisor_graph.py` + `tests/test_console_agent_api.py`

**Interfaces:**
- Consumes: Task 6 的 cancel_request 意图与节点
- Produces: `SupervisorRoute.CANCEL_REQUEST`；全链映射；worker 入口条件分流；console `_snapshot_confirmation_is_cancel_execution` + `_record_exchange` 文案（确认取消/取消取消/修改取消信息并重新确认）

- [ ] **Step 1: 写失败测试（仿 refund 路由测试）**

```python
def test_supervisor_routes_cancel_request():  # "取消订单 A1002" → CANCEL_REQUEST
def test_cancel_request_maps_to_ticket_worker():  # SUPERVISOR_ROUTE_TABLE[CANCEL_REQUEST] == "ticket_agent"
def test_console_api_cancel_confirmation_transcript():  # decide 后 transcript 文案含"确认取消订单"
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: supervisor_router.py**

`SupervisorRoute` 加 `CANCEL_REQUEST = "cancel_request"`；`TICKET_INTENT_TO_SUPERVISOR_ROUTE["cancel_request"] = CANCEL_REQUEST`。

- [ ] **Step 4: supervisor_graph.py**

`SUPERVISOR_ROUTE_TABLE[CANCEL_REQUEST] = "ticket_agent"`；intent→route 双映射（:109-117/:149-160）加 cancel_request；active-cancel-collection 守卫（仿 refund :73-83）。

- [ ] **Step 5: ticket_worker.py 入口分流**

`route_ticket_worker_entry`（:38-56）加 cancel 分支（intent==cancel_request 或 has_active_cancel_collection → handle_cancel_request）；`_extract_ticket_fields_reset_refund_flag` 扩展为同时清 cancel_request_active（或新增同名 cancel 函数——跟随最小侵入）。

- [ ] **Step 6: console_agent_service.py**

`_snapshot_confirmation_is_cancel_execution`（仿 is_refund_execution :907-922，从 interrupt payload 读 is_cancel_execution）；`_pending_confirmation_from_state`（:924-948）透出；`register_ticket_confirmation` 传 is_cancel_execution；`_record_exchange`（:570-579）文案三分支（确认取消/取消取消/确认退款/取消退款/确认创建工单/取消创建工单）。

- [ ] **Step 7: 跑测试确认通过 + 相关套件 + 全量 pytest + Commit**

```bash
cd projects/ai-service && uv run pytest tests/test_supervisor_router.py tests/test_supervisor_graph.py tests/test_console_agent_api.py -q
uv run pytest -q
git add projects/ai-service/
git commit -m "feat: route cancel_request in supervisor and console confirmation"
```

---

### Task 8: 前端订单页取消按钮 + AI 对话确认弹窗

**Files:**
- Modify: `projects/customer-service-console/src/views/OrdersView.vue`
- Modify: `projects/customer-service-console/src/services/businessApi.ts`
- Modify: `projects/customer-service-console/src/views/AiChatView.vue`
- Test: 前端 `npm run build`

**Interfaces:**
- Consumes: Task 3 公开接口 `POST /api/orders/{orderId}/cancel`；Task 7 的 is_cancel_execution（确认弹窗判别）
- Produces: OrdersView 取消按钮 + canceled 展示；businessApi.cancelOrder；AiChatView isCancelConfirmation（flag 优先 + undefined fallback）

- [ ] **Step 1: businessApi.ts 加 cancelOrder + 类型**

仿 refundOrder（:127-129）：`cancelOrder(orderId, reason)` POST /api/orders/{id}/cancel；`OrderListItem`/`OrderToolView` 加 canceled_at/cancel_reason。

- [ ] **Step 2: OrdersView.vue 取消按钮与展示**

- 操作列加"取消订单"按钮：`row.order_status === 'waiting_shipment' && row.payment_status !== 'refunded' && row.order_status !== 'canceled'`（仿退款按钮 :102-115）
- 点击 → ElMessageBox.prompt（必填 + maxlength 100）→ `cancelOrder` → ElMessage + 刷新
- 状态标签加 `canceled: '已取消'`；已取消显示 `已取消（canceled_at）` + cancel_reason

- [ ] **Step 3: AiChatView.vue 确认弹窗 cancel 场景**

仿 `isRefundConfirmation`（:347-357）：`isCancelConfirmation()`（flag 优先 `is_cancel_execution === true`，undefined fallback `issue_type === 'cancel'`）；弹窗模板（:376-461）加 cancel 分支（标题"确认取消订单"、展示 order_id + 取消原因、按钮"确认取消/取消/修改信息"）；气泡文案三态（cancel/refund/ticket）对齐后端 _record_exchange。

- [ ] **Step 4: 前端构建验证**

Run: `cd projects/customer-service-console && npm run build`
Expected: 构建成功

- [ ] **Step 5: Commit**

```bash
git add projects/customer-service-console/
git commit -m "feat: add cancel order button and AI confirmation dialog"
```

---

### Task 9: 全量回归与真实联调验收

**Files:**
- Modify: `docs/project-handoff-for-vibe-coding.md`（第 17/18 节更新）
- 无代码变更（验收）

**Interfaces:**
- Consumes: 全部 Task 1-8 交付

- [ ] **Step 1: Python 全量回归**

Run: `cd projects/ai-service && uv run pytest -q`
Expected: ≥1497 passed

- [ ] **Step 2: Java 全量回归**

Run: `cd projects/java-business-service && mvn test -q`
Expected: BUILD SUCCESS

- [ ] **Step 3: 前端构建**

Run: `cd projects/customer-service-console && npm run build`
Expected: 构建成功

- [ ] **Step 4: 真实联调验收（三场景）**

启动：MySQL(本机) → Redis/Qdrant(VM) → Java(18004) → MCP(9100) → Python(8000) → Vue(5173)。先执行迁移 SQL（本机 MySQL 跑 ALTER canceled_at/cancel_reason + 验证 A1002 未发货可取消）。
- **场景 A（AI 对话）**："取消订单 A1002，因为不想要了" → cancel_request → 收集 → 确认弹窗（is_cancel_execution）→ 确认 → Java 取消成功 → 前端"已取消"
- **场景 B（订单页）**：未发货订单点"取消订单"→ 输入原因 → 确认 → 成功，列表显示已取消
- **场景 C（边界）**：已发货取消 → 409 ORDER_NOT_CANCELABLE；重复取消 → 409 CANCEL_ALREADY_EXISTS；退款后取消 → 拒绝
- 落库验证：order_status=canceled、canceled_at/cancel_reason 有值、order_events 有 cancel 事件

- [ ] **Step 5: 更新交接文档**

- 第 17 节加"订单取消全链路"行
- 第 18 节"已完成里程碑"加"订单取消全链路"
- 候选方向表更新（业务功能扩展标记含订单取消）

- [ ] **Step 6: 最终全分支审查 + Commit**

```bash
git add docs/project-handoff-for-vibe-coding.md
git commit -m "docs: update handoff with cancel order milestone"
```

---

## Self-Review 记录

**1. Spec 覆盖：**
- 3.1 表结构（canceled_at/cancel_reason + 迁移）→ Task 1 ✅
- 3.2 内部取消接口（校验链/幂等/审计/并发）→ Task 2 ✅
- 3.3 公开接口（订单页）→ Task 3 ✅
- 4.3 JavaOrderClient + 4.1 schema → Task 4 ✅
- 4.1/4.2 工具注册表 + MCP handler → Task 5 ✅
- 4.4 新意图 cancel_request（7 处）→ Task 6 ✅
- 4.5/4.6 supervisor + console 判别 → Task 7 ✅
- 5.1/5.2 前端双入口 → Task 8 ✅
- 6 测试与验收 → Task 9 ✅

**2. 占位符扫描：** 无 TBD/TODO；Task 6/7 的节点与判别均给了精确仿照位置（ticket_agent.py:2583-2780/:2355-2439、console_agent_service.py:907-922/:570-579），不阻塞。

**3. 类型一致性：**
- `cancel_order` 工具名、`CANCEL_ORDER_TOOL_NAME`、MCP 注册名一致 ✅
- `OrderService.cancelOrder(orderId, reason, context, idempotencyKey)` 在 Task 2/3 一致 ✅
- `JavaOrderClient.cancel_order(order_id, reason, idempotency_key=...)` 在 Task 4/5 一致 ✅
- `cancel_request` 意图在 Task 6/7/8 一致 ✅
- 数据库列 canceled_at/cancel_reason 在 Task 1/2/9 一致 ✅
- `is_cancel_execution` 在 Task 6（写入）/7（判别）/8（前端）一致 ✅

**开放点（实现时按实际代码修正）：**
- issue_type 结构化抽取：schemas/structured.py TicketIntent 加 CANCEL——规格 4.4 第 7 点已明确必须
- worker `_extract_ticket_fields_reset_refund_flag` 扩展为同时清 cancel（跟随最小侵入）
- console 文案三分支的精确措辞（与前端对齐）
- 迁移 SQL 位置（追加 refund-migration.sql 或新建 cancel-migration.sql）
