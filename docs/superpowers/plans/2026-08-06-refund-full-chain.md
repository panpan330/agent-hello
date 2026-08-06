# 退款全链路闭环 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现真实退款业务全链路：Java 退款接口与审计 → Agent 退款工具（MCP + 确认）→ 新意图 refund_request → 前端双入口 → 测试与真实联调验收。

**Architecture:** 三层扩展——Java 后端（orders 表 +4 列、内部退款接口含幂等与归属校验、公开退款接口供前端）、Python Agent 层（refund_order 工具解禁 + MCP handler + 新意图 refund_request 接入单 Agent 与多 Agent supervisor）、前端（订单页退款按钮 + AI 对话退款确认弹窗）。确认机制复用现有 Redis 确认存储（create_ticket 同机制），幂等复用 Idempotency-Key。

**Tech Stack:** Java 17 + Spring Boot 3（MyBatis）+ MySQL；Python 3.12 + FastAPI + LangGraph + MCP SDK；Vue 3 + Element Plus；pytest；maven。

## Global Constraints

- 自动测试不调用真实模型、不命中真实 Embedding/Rerank API、不写入真实业务数据、不依赖真实 Redis、不连接真实 Collector/LangSmith。
- 现有测试套件必须保持绿色：Python `uv run pytest -q` = 1417 passed；Java `mvn test -q` = 49 passed；前端 `npm run build` 通过。
- 不新增第三方依赖（Java/Python/前端均不引入新库）。
- 退款规则：仅 `order_status == unshipped` 且 `payment_status != refunded` 可退；全额退款（refund_amount = amount）。
- 必须用户确认：复用 `create_tool_confirmation_store` 的 `require_confirmed`；MCP 路径 confirmation_id 即幂等键。
- 保留 `refund_order` 的 `access_level=SENSITIVE` 与 `requires_confirmation=True`。
- 意图边界：退款诉求 → `refund_request`；取消订单仍归 `unsupported`（本次不做取消）。
- 迁移 SQL 需对已有库手动执行（本机 MySQL 127.0.0.1:3306）；schema.sql 同步更新供新建库。
- 本地 git commit；不推送 GitHub。
- 部署形态：MCP 模式（AGENT_MCP_TOOLS_ENABLED=true）+ 多 Agent 模式（AGENT_MULTI_AGENT_ENABLED=true）为当前 .env 形态，两者都要兼容。

---

### Task 1: Java 表结构扩展与 Order entity/DTO 更新

**Files:**
- Modify: `projects/java-business-service/src/main/resources/schema.sql:34-48`（orders 表）
- Modify: `projects/java-business-service/src/main/resources/data.sql:162-241`（订单种子补金额）
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/entity/Order.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/dto/OrderToolView.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/dto/OrderListItemView.java`
- Create: `projects/java-business-service/docs/refund-migration.sql`（迁移 SQL）
- Test: `projects/java-business-service/src/test/java/com/panpan/aibusinessservice/controller/InternalOrderControllerTest.java`

**Interfaces:**
- Consumes: 现有 `Order` entity（字段 orderStatus/paymentStatus/logisticsMessage/latestEvent/canCreateTicket，方法 visibleTo(userId, tenantId)）
- Produces: `Order` 新增字段 `amount/refundAmount/refundedAt/refundReason` + getter/setter；`OrderToolView` 新增字段 `refundAmount/refundedAt/refundReason`（Task 2/3 使用）；`OrderListItemView` 新增 `refundAmount/refundedAt`（Task 3 使用）

- [ ] **Step 1: 更新 schema.sql orders 表**

在 `schema.sql` 的 orders 表（34-48 行）追加 4 列：
```sql
  amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  refund_amount DECIMAL(10,2) NULL,
  refunded_at DATETIME(6) NULL,
  refund_reason VARCHAR(255) NULL,
```
（放在 `can_create_ticket` 之后、`created_at` 之前）

- [ ] **Step 2: 创建迁移 SQL 文件**

创建 `docs/refund-migration.sql`：
```sql
-- 已有库手动执行；新建库由 schema.sql 自动生效
ALTER TABLE orders ADD COLUMN amount DECIMAL(10,2) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN refund_amount DECIMAL(10,2) NULL;
ALTER TABLE orders ADD COLUMN refunded_at DATETIME(6) NULL;
ALTER TABLE orders ADD COLUMN refund_reason VARCHAR(255) NULL;
```

- [ ] **Step 3: 更新 data.sql 订单种子**

三条订单（A1001/A1002/A2001，162-241 行）的 INSERT 列追加 `amount`（值分别为 299.00 / 159.00 / 89.00，补在 can_create_ticket 之后）。确保 A1002 是 `waiting_shipment`（未发货，联调用）。

- [ ] **Step 4: 更新 Order entity**

`Order.java` 加 4 个字段（BigDecimal amount, BigDecimal refundAmount, LocalDateTime refundedAt, String refundReason）+ getter/setter。

- [ ] **Step 5: 更新 OrderToolView record**

加 3 个字段 `refundAmount, refundedAt, refundReason`（均 nullable），`from(Order)` 同步填充。

- [ ] **Step 6: 更新 OrderListItemView**

加 `refundAmount, refundedAt` 字段（前端展示用）。

- [ ] **Step 7: 跑 Java 编译与现有测试**

Run: `cd projects/java-business-service && mvn test -q`
Expected: BUILD SUCCESS，49 passed（编译通过即可，字段无逻辑变更）

- [ ] **Step 8: Commit**

```bash
git add projects/java-business-service/
git commit -m "feat: add order amount and refund columns to schema, entity and DTOs"
```

---

### Task 2: Java 内部退款接口（InternalOrderController + OrderService）

**Files:**
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/controller/InternalOrderController.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/service/OrderService.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/service/impl/OrderServiceImpl.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/exception/BusinessErrorCode.java`（如需要）
- Test: `projects/java-business-service/src/test/java/com/panpan/aibusinessservice/controller/InternalOrderControllerTest.java`

**Interfaces:**
- Consumes: Task 1 的 Order 新字段、OrderToolView；现有 `TicketIdempotencyCache`（get/put）、`InternalRequestContext`（userId()/tenantId()）、`OrderMapper`（selectByTenantIdAndOrderId/update）
- Produces: `OrderService.refundOrder(String orderId, String reason, InternalRequestContext context, String idempotencyKey) -> OrderToolView`；新内部接口 `POST /internal/orders/{orderId}/refund`（body `{"reason": "..."}`，头 Idempotency-Key 可选）。错误码：`ORDER_NOT_FOUND(404)`、`ORDER_ACCESS_DENIED(403)`、`ORDER_NOT_REFUNDABLE(409)`、`REFUND_ALREADY_EXISTS(409)`、`IDEMPOTENCY_KEY_CONFLICT(409)`（复用现有枚举命名风格）

- [ ] **Step 1: 写失败测试（InternalOrderControllerTest 追加）**

```java
@Test
void refundOrderReturnsToolFacingView() throws Exception {
    // 用 U1001 的 A1002（waiting_shipment）请求退款，200 且 paymentStatus=refunded、refundAmount 有值
}
@Test
void refundOrderDeniesShippedOrder() throws Exception {
    // A1001（shipped）退款 → 409 ORDER_NOT_REFUNDABLE
}
@Test
void refundOrderDeniesAlreadyRefunded() throws Exception {
    // 已退款订单再次退款 → 409 REFUND_ALREADY_EXISTS
}
@Test
void refundOrderIsIdempotentForSameKey() throws Exception {
    // 同 Idempotency-Key 重复请求返回首次结果
}
@Test
void refundOrderRejectsOtherUsersOrder() throws Exception {
    // U2001 的订单被 U1001 退 → 403 ORDER_ACCESS_DENIED
}
```
（先编译失败——refundOrder 接口与方法未定义）

- [ ] **Step 2: 跑测试确认失败**

Run: `cd projects/java-business-service && mvn test -q -Dtest=InternalOrderControllerTest`
Expected: 编译失败（refundOrder 未定义）

- [ ] **Step 3: OrderService 接口加 refundOrder**

```java
OrderToolView refundOrder(String orderId, String reason, InternalRequestContext context, String idempotencyKey);
```

- [ ] **Step 4: OrderServiceImpl 实现 refundOrder**

复用 queryOrder 的查询/归属校验（:27-46），新增：
```java
public OrderToolView refundOrder(String orderId, String reason, InternalRequestContext context, String idempotencyKey) {
    // 1. 正则校验 orderId（复用 ORDER_ID_INVALID 逻辑）
    // 2. 幂等：idempotencyKey 非空时查 TicketIdempotencyCache（fingerprint=sha256(orderId+reason+context.userId())）
    //    命中且 fingerprint 一致 → 直接查库返回已退款订单（幂等返回）
    //    命中但 fingerprint 不一致 → 抛 IDEMPOTENCY_KEY_CONFLICT
    // 3. 查订单（selectByTenantIdAndOrderId），未命中抛 ORDER_NOT_FOUND
    // 4. visibleTo 校验，失败抛 ORDER_ACCESS_DENIED
    // 5. orderStatus 必须 unshipped，否则抛 ORDER_NOT_REFUNDABLE
    // 6. paymentStatus 不能是 refunded，否则抛 REFUND_ALREADY_EXISTS
    // 7. 更新订单：paymentStatus=refunded、refundAmount=amount、refundedAt=now、refundReason=reason、latestEvent="退款成功"
    //    （orderMapper 新增 update 或复用现有 update 方法；DuplicateKeyException 兜底重查）
    // 8. 写 ticket_events：event_type="refund"，payload={amount, reason}（复用 ticketMapper.insertTicketEvent，
    //    或新增 orderMapper.insertRefundEvent——跟随现有事件写入模式，见 TicketServiceImpl insertCreatedEvent）
    // 9. 幂等 put（rememberIdempotency）
    // 10. 返回 OrderToolView.from(order)
}
```

- [ ] **Step 5: InternalOrderController 加 POST 端点**

```java
@PostMapping("/{orderId}/refund")
public ApiResponse<OrderToolView> refundOrder(
        @PathVariable String orderId,
        @RequestBody Map<String, String> body,
        @RequestHeader(value = TraceHeaders.IDEMPOTENCY_KEY, required = false) String idempotencyKey,
        HttpServletRequest request
) {
    InternalRequestContext context = requestResolver.resolve(request);
    String reason = body.get("reason");
    if (reason == null || reason.isBlank()) {
        throw new BusinessException(BusinessErrorCode.REFUND_REASON_REQUIRED);
    }
    return ApiResponse.ok(orderService.refundOrder(orderId, reason, context, idempotencyKey), context.traceId());
}
```

- [ ] **Step 6: 跑测试确认通过**

Run: `cd projects/java-business-service && mvn test -q -Dtest=InternalOrderControllerTest`
Expected: PASS（5 个新测试 + 原有）

- [ ] **Step 7: 跑全量 Java 测试**

Run: `cd projects/java-business-service && mvn test -q`
Expected: BUILD SUCCESS

- [ ] **Step 8: Commit**

```bash
git add projects/java-business-service/
git commit -m "feat: add refund order internal endpoint with idempotency and audit"
```

---

### Task 3: Java 公开退款接口（供订单页）与列表字段

**Files:**
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/controller/OrderController.java`
- Modify: `projects/java-business-service/src/main/java/com/panpan/aibusinessservice/controller/InternalOrderController.java`（如复用）
- Test: `projects/java-business-service/src/test/java/com/panpan/aibusinessservice/controller/PublicOrderTicketControllerTest.java`

**Interfaces:**
- Consumes: Task 2 的 `OrderService.refundOrder`；`AuthService.currentUser(authorization)` → `CurrentUserView`
- Produces: 公开接口 `POST /api/orders/{orderId}/refund`（body `{"reason": "..."}`，Authorization 头鉴权）→ 复用 OrderService.refundOrder（userId/tenantId 从 CurrentUserView 构造 InternalRequestContext）

- [ ] **Step 1: 写失败测试**

```java
@Test
void customerCanRefundOwnUnshippedOrder() throws Exception {
    // POST /api/orders/A1002/refund 带 customer token + reason → 200
}
@Test
void customerCannotRefundShippedOrder() throws Exception {
    // POST /api/orders/A1001/refund → 409
}
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: OrderController 加 POST /{orderId}/refund**

```java
@PostMapping("/{orderId}/refund")
public ApiResponse<OrderToolView> refundOrder(@PathVariable String orderId, @RequestBody Map<String, String> body,
        @RequestHeader("Authorization") String authorization) {
    CurrentUserView user = authService.currentUser(authorization);
    InternalRequestContext context = new InternalRequestContext("api", user.id(), user.id(), user.tenantId());
    String reason = body.get("reason");
    return ApiResponse.ok(orderService.refundOrder(orderId, reason, context, null), null);
}
```
（InternalRequestContext record 构造参数顺序：traceId, caller, userId, tenantId——按实际代码修正）

- [ ] **Step 4: 跑测试确认通过**

- [ ] **Step 5: 跑全量 Java 测试 + Commit**

```bash
cd projects/java-business-service && mvn test -q
git add projects/java-business-service/
git commit -m "feat: add public refund endpoint for order page"
```

---

### Task 4: Python JavaOrderClient 新增 refund_order

**Files:**
- Modify: `projects/ai-service/app/services/java_order_client.py`
- Test: `projects/ai-service/tests/test_java_order_client.py`

**Interfaces:**
- Consumes: 现有 `get_order` 模式（_build_headers :130-135、build_java_error_app_exception、_unwrap_java_api_response_data）
- Produces: `JavaOrderClient.refund_order(order_id: str, reason: str, *, idempotency_key: str | None = None, trace_context: dict | None = None) -> dict`（调用 `POST /internal/orders/{order_id}/refund`，body `{"reason": reason}`，头带 Idempotency-Key；非 2xx 抛 AppException（映射 Java 错误码））

- [ ] **Step 1: 写失败测试**

```python
def test_refund_order_sends_post_with_reason_and_idempotency_key(respx_mock):
    # mock POST /internal/orders/A1002/refund 返回 200 {"code":0,"data":{...}}
    # 断言请求方法 POST、body 含 reason、头含 Idempotency-Key
def test_refund_order_maps_business_error(respx_mock):
    # mock 409 返回 Java 错误码 ORDER_NOT_REFUNDABLE
    # 断言抛 AppException 且 code 含 ORDER_NOT_REFUNDABLE
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: 实现 refund_order**

仿 `get_order`（java_order_client.py:40-60）新增方法：
```python
def refund_order(self, order_id, reason, *, idempotency_key=None, trace_context=None):
    url = f"{self.base_url}/internal/orders/{quote(order_id)}/refund"
    headers = self._build_headers(trace_context, idempotency_key=idempotency_key)
    try:
        response = self._http_client.post(url, json={"reason": reason}, headers=headers, timeout=self._timeout_seconds)
    except TimeoutException: raise AppException(...TOOL_TIMEOUT...)
    except Exception: raise AppException(...TOOL_UPSTREAM_ERROR...)
    if response.status_code != 200:
        raise build_java_error_app_exception(response, operation="order_refund", ...)
    return _unwrap_java_api_response_data(response.json())
```

- [ ] **Step 4: 跑测试确认通过**

- [ ] **Step 5: 跑相关测试 + Commit**

```bash
cd projects/ai-service && uv run pytest tests/test_java_order_client.py -q
git add projects/ai-service/
git commit -m "feat: add refund_order to Java order client"
```

---

### Task 5: Python 工具注册表解禁 refund_order

**Files:**
- Modify: `projects/ai-service/app/tools/tool_registry.py:27-33`
- Create: `projects/ai-service/app/schemas/refund.py`（或复用 schemas/tool.py 模式）
- Test: `projects/ai-service/tests/test_tool_registry.py`

**Interfaces:**
- Consumes: `ToolDefinition`（schemas/tool.py:26-54）；`authorize_tool_call`（tool_registry.py:87-101）
- Produces: `refund_order` 工具 `enabled=True` + `argument_schema`；`get_refund_order_args_json_schema()`（order_id 必填、reason 必填、requester_id 可选）；`REFUND_ORDER_TOOL_NAME = "refund_order"` 常量（Task 6 使用）

- [ ] **Step 1: 写失败测试**

```python
def test_refund_order_tool_is_enabled_and_requires_confirmation():
    # refund_order: enabled=True, access_level=SENSITIVE, requires_confirmation=True, argument_schema 含 order_id/reason 必填
def test_refund_order_not_in_read_only_model_callable_tools():
    # list_model_callable_tool_definitions_only_exposes_safe_read_tools 不含 refund_order
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: 实现**

`schemas/refund.py`：
```python
from pydantic import BaseModel, Field

class RefundOrderArgs(BaseModel):
    order_id: str = Field(..., description="要退款的订单号")
    reason: str = Field(..., min_length=1, max_length=200, description="退款原因")
    requester_id: str | None = Field(None, description="发起退款的操作者用户 ID")

def get_refund_order_args_json_schema() -> dict:
    return RefundOrderArgs.model_json_schema()
```
`tool_registry.py` 更新 refund_order 定义（enabled=True + argument_schema=get_refund_order_args_json_schema()，description 改为"发起退款操作，属于敏感业务动作，必须先让用户确认，且订单未发货才可退。"）。在模块顶部定义 `REFUND_ORDER_TOOL_NAME = "refund_order"`（仿 CREATE_TICKET_TOOL_NAME）。

- [ ] **Step 4: 跑测试确认通过**

- [ ] **Step 5: Commit**

```bash
cd projects/ai-service && uv run pytest tests/test_tool_registry.py -q
git add projects/ai-service/
git commit -m "feat: enable refund_order tool with argument schema"
```

---

### Task 6: Python MCP product server 新增 refund handler

**Files:**
- Modify: `projects/ai-service/app/mcp_servers/product_server.py`
- Modify: `projects/ai-service/app/mcp_servers/order_tool.py`（或新增 refund handler 复用点）
- Test: `projects/ai-service/tests/test_mcp_product_server.py`

**Interfaces:**
- Consumes: Task 4 `JavaOrderClient.refund_order`；Task 5 `REFUND_ORDER_TOOL_NAME`/`get_refund_order_args_json_schema`；`create_tool_confirmation_store().require_confirmed`；`authorize_tool_call`；`run_idempotent_tool`（product_server.py 现有）
- Produces: `@server.tool()` 注册 `refund_order` → `_product_refund_order(order_id, reason, confirmation_id, user_confirmed=False, requester_id=None)`；返回结构与 `_product_create_ticket` 一致（ok/allowed/confirmation_checked/error_code/message/refund）

- [ ] **Step 1: 写失败测试（test_mcp_product_server.py 追加）**

```python
def test_product_refund_order_requires_user_confirmation():
    # user_confirmed=False → ok=False, error_code=TOOL_CONFIRMATION_REQUIRED
def test_product_refund_order_validates_confirmation_id_format():
    # 非法 confirmation_id → 参数校验失败
def test_product_refund_order_sets_business_context_before_java_call():
    # 确认凭证通过后 → 断言 JavaOrderClient.set_business_context 被调用（仿现有 create_ticket 测试）
def test_product_refund_order_confirmation_unavailable_mapped_to_ok_false():
    # require_confirmed 抛错 → ok=False + 错误码
def test_product_refund_order_success_returns_refund():
    # 确认通过 + Java 返回 200 → ok=True, refund 含退款信息
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: 实现 _product_refund_order**

仿 `_product_create_ticket`（product_server.py:61-187）：
```python
def _product_refund_order(order_id, reason, confirmation_id, user_confirmed=False, requester_id=None):
    # 1. user_confirmed=False → 返回 ok=False, error_code=TOOL_CONFIRMATION_REQUIRED
    # 2. requester_id = requester_id or "demo_user_001"
    # 3. pydantic 校验 RefundOrderArgs
    # 4. create_tool_confirmation_store().require_confirmed(confirmation_id, actor_id=requester_id)（AppException → ok=False）
    # 5. authorize_tool_call(REFUND_ORDER_TOOL_NAME, user_confirmed=True)
    # 6. JavaOrderClient.from_settings + set_business_context(user_id, tenant_id)
    # 7. run_idempotent_tool(REFUND_ORDER_TOOL_NAME, arguments, confirmation_id,
    #        lambda: java_order_client.refund_order(order_id, reason, idempotency_key=confirmation_id))
    # 8. 返回 {ok:True, allowed:True, confirmation_checked:True, confirmation_id, error_code:None, message:"退款成功", refund: result}
```
工具注册处（@server.tool()）加 refund_order，schema 用 get_refund_order_args_json_schema()，confirmation_id 用与 create_ticket 相同的 `Field(pattern=r"^[a-f0-9]{16,32}$")`。

- [ ] **Step 4: 跑测试确认通过**

- [ ] **Step 5: 跑相关测试 + Commit**

```bash
cd projects/ai-service && uv run pytest tests/test_mcp_product_server.py -q
git add projects/ai-service/
git commit -m "feat: add refund_order tool to product MCP server"
```

---

### Task 7: Python 新意图 refund_request（单 Agent ticket_agent）

**Files:**
- Modify: `projects/ai-service/app/agents/ticket_agent.py`（TicketIntent :56-63、提示词 :157-169、路由表 :216-223、classify_ticket_intent :1386-1435）
- Test: `projects/ai-service/tests/test_ticket_agent_intent.py`

**Interfaces:**
- Consumes: `refund_order` 工具（经 MCP 或直接 Java）；现有确认机制（build_pending_ticket_confirmation / register_ticket_confirmation）
- Produces: `TicketIntent` 增加 `"refund_request"`；路由 `refund_request → handle_refund_request` 节点；`classify_ticket_intent` 识别退款关键词；退款确认交互（收集 order_id + reason → 确认弹窗 → 执行）

- [ ] **Step 1: 写失败测试**

```python
def test_classify_refund_request_intent():
    # "我要退 A1002 的款" → refund_request
    # "申请退款" → refund_request
def test_classify_refund_policy_question_still_policy():
    # "退款政策是什么" → policy_question（不误伤）
def test_classify_cancel_order_still_unsupported():
    # "取消订单" → unsupported（边界保留）
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: 实现意图扩展**

1. `TicketIntent` Literal 加 `"refund_request"`。
2. 提示词（:157-169）：新增 refund_request 定义——"refund_request 表示用户明确要求执行退款、退货退款、申请退款，并提供了订单号或退款对象。"；修改 :166 的 unsupported 描述——去掉"退款"（保留"取消订单"）。
3. 路由表（:216-223）：`"refund_request": "handle_refund_request"`。
4. `classify_ticket_intent`（:1386-1435）：在 ticket_request 之前加 refund 关键词分支（REFUND_KEYWORDS = ["退款", "退钱", "申请退款", "退货款"]，且含 order_id 模式或明确退款动词）。
5. 新增节点 `handle_refund_request`（仿 create_ticket 节点流程）：收集 order_id + reason（缺失追问）→ 构建退款确认（复用 build_pending_ticket_confirmation 机制，confirmation_id=sha256(fields)[:32]）→ interrupt 等待用户确认 → 确认后调 refund_order 工具 → 返回结果。
   - 若复用现有工单确认节点有难度，可先做"提示用户提供订单号与原因"的简化版，真实执行仍走 MCP 工具（确认由前端弹窗完成）。

- [ ] **Step 4: 跑测试确认通过**

- [ ] **Step 5: 跑相关测试 + Commit**

```bash
cd projects/ai-service && uv run pytest tests/test_ticket_agent_intent.py -q
git add projects/ai-service/
git commit -m "feat: add refund_request intent to ticket agent"
```

---

### Task 8: 多 Agent supervisor 支持 refund_request

**Files:**
- Modify: `projects/ai-service/app/agents/supervisor/supervisor_router.py`（SupervisorRoute :19-25、TICKET_INTENT_TO_SUPERVISOR_ROUTE :28-35）
- Modify: `projects/ai-service/app/agents/supervisor/supervisor_graph.py`（SUPERVISOR_ROUTE_TABLE :27-33、intent 映射 :86-90、:125-127）
- Test: `projects/ai-service/tests/test_supervisor_router.py`

**Interfaces:**
- Consumes: Task 7 的 `refund_request` 意图
- Produces: `SupervisorRoute.REFUND_REQUEST = "refund_request"`；`TICKET_INTENT_TO_SUPERVISOR_ROUTE["refund_request"] = SupervisorRoute.REFUND_REQUEST`；`SUPERVISOR_ROUTE_TABLE[SupervisorRoute.REFUND_REQUEST] = "ticket_agent"`（复用工单 worker，退款执行由 ticket_worker 的 handle_refund_request 完成——若 ticket_worker 无该节点则映射到 knowledge/直接答复兜底，实现时验证）

- [ ] **Step 1: 写失败测试**

```python
def test_supervisor_routes_refund_request():
    # RuleSupervisorRouter.route("我要退 A1002 的款") → REFUND_REQUEST
def test_refund_request_maps_to_ticket_worker():
    # SUPERVISOR_ROUTE_TABLE[REFUND_REQUEST] == "ticket_agent"
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: 实现**

`supervisor_router.py`：SupervisorRoute 枚举加 `REFUND_REQUEST = "refund_request"`；`TICKET_INTENT_TO_SUPERVISOR_ROUTE` 加 `"refund_request": SupervisorRoute.REFUND_REQUEST`。
`supervisor_graph.py`：`SUPERVISOR_ROUTE_TABLE` 加 `SupervisorRoute.REFUND_REQUEST: "ticket_agent"`；intent→route 映射（:86-90 与 :125-127）加 `"refund_request"`。
**验证 ticket_worker 是否处理 refund_request**：若 `ticket_worker.py` 的 extract_ticket_fields 需区分退款，在实现时给 `build_ticket_worker_graph` 传入的 intent 检查加 refund_request 分支（复用 create_ticket 流程但执行 refund_order）。

- [ ] **Step 4: 跑测试确认通过**

- [ ] **Step 5: 跑相关测试 + Commit**

```bash
cd projects/ai-service && uv run pytest tests/test_supervisor_router.py -q
git add projects/ai-service/
git commit -m "feat: route refund_request intent in supervisor graph"
```

---

### Task 9: 前端订单页退款按钮与展示

**Files:**
- Modify: `projects/customer-service-console/src/views/OrdersView.vue`
- Modify: `projects/customer-service-console/src/services/businessApi.ts`
- Test: 前端构建 `npm run build`

**Interfaces:**
- Consumes: Task 3 公开接口 `POST /api/orders/{orderId}/refund`；OrderListItemView 新字段 refundAmount/refundedAt
- Produces: OrdersView 行内"申请退款"按钮（仅 unshipped 且未退款可用）+ 退款原因对话框 + 已退款展示（金额/时间）

- [ ] **Step 1: businessApi.ts 加退款方法**

```ts
export function refundOrder(orderId: string, reason: string) {
  return javaApi.post(`/api/orders/${orderId}/refund`, { reason });
}
```

- [ ] **Step 2: OrdersView.vue 加退款按钮与对话框**

- 表格加"操作"列：`order_status === 'unshipped' && payment_status !== 'refunded'` 时显示"申请退款"按钮
- 点击 → `ElMessageBox.prompt`（或 el-dialog）输入退款原因 → 确认调 `refundOrder`
- 支付状态列已有 refunded 标签；追加显示 `已退款 ¥{refundAmount}（{refundedAt}）`
- 成功后刷新列表 + ElMessage.success

- [ ] **Step 3: 前端构建验证**

Run: `cd projects/customer-service-console && npm run build`
Expected: 构建成功

- [ ] **Step 4: Commit**

```bash
git add projects/customer-service-console/
git commit -m "feat: add refund button and status display to orders page"
```

---

### Task 10: 前端 AI 对话退款确认弹窗

**Files:**
- Modify: `projects/customer-service-console/src/views/AiChatView.vue`
- Test: 前端构建

**Interfaces:**
- Consumes: Task 7/8 的 refund_request 确认交互（复用现有确认弹窗数据流 decideConfirmation）
- Produces: 确认弹窗支持退款场景（类型标识 refund、字段 order_id + reason），确认/纠错后走现有 decideConsoleAgentTicketConfirmation

- [ ] **Step 1: 确认弹窗通用化**

现有模板（:360-429）按 `pendingConfirmation` 展示 issue_type/order_id/urgency/description。加退款分支：
- `pendingConfirmation.type === 'refund'`（或确认信息含 refund 标识）时显示"确认退款"文案 + 订单号 + 退款原因
- 按钮文案：退款 → "确认退款" / "取消" / "修改信息"

- [ ] **Step 2: 前端构建验证**

- [ ] **Step 3: Commit**

```bash
git add projects/customer-service-console/
git commit -m "feat: support refund confirmation dialog in AI chat"
```

---

### Task 11: 全量回归与真实联调验收

**Files:**
- Modify: `docs/project-handoff-for-vibe-coding.md`（第 9/18 节更新退款能力状态）
- 无代码变更（验收）

**Interfaces:**
- Consumes: 全部 Task 1-10 的交付

- [ ] **Step 1: Python 全量回归**

Run: `cd projects/ai-service && uv run pytest -q`
Expected: ≥1417 passed（新增退款测试全过）

- [ ] **Step 2: Java 全量回归**

Run: `cd projects/java-business-service && mvn test -q`
Expected: BUILD SUCCESS

- [ ] **Step 3: 前端构建**

Run: `cd projects/customer-service-console && npm run build`
Expected: 构建成功

- [ ] **Step 4: 真实联调验收（三场景）**

启动顺序：MySQL(本机) → Redis(本机或 VM) → Qdrant → Java(18004) → MCP(9100) → Python(8000) → Vue(5173)。
- **场景 A（AI 对话）**：登录 customer/123456 → 对话"我要退 A1002 的款，因为不想要了" → 识别 refund_request → 收集信息 → 确认弹窗 → 确认 → Java 退款成功 → 前端显示"已退款 ¥159.00"
- **场景 B（订单页）**：订单页 A1002（unshipped）行点"申请退款" → 输入原因 → 确认 → 成功，列表显示已退款金额/时间
- **场景 C（边界）**：A1001（shipped）申请退款 → 拒绝并返回"未发货才能退款"；再次退款（幂等）→ 幂等返回首次结果
- 验证落库：MySQL 查 orders A1002 → payment_status=refunded、refund_amount=159.00、refunded_at 有值、refund_reason 有值；ticket_events 有 refund 事件

- [ ] **Step 5: 更新交接文档**

- 第 9 节"已实现但未接入产品主流程"表格中删除/更新退款相关行（refund_order 从占位变为已接入）
- 第 18 节"已完成里程碑"加一行"退款全链路闭环"
- 新增排障行（如有）：退款失败常见原因（未发货校验/确认凭证过期）

- [ ] **Step 6: 最终全分支审查 + Commit**

```bash
git add docs/project-handoff-for-vibe-coding.md
git commit -m "docs: update handoff with refund full-chain milestone"
```

---

## Self-Review 记录

**1. Spec 覆盖：**
- 3.1 表结构（amount/refund_amount/refunded_at/refund_reason）→ Task 1 ✅
- 3.2 内部退款接口（校验/幂等/事件）→ Task 2 ✅
- 3.4 / 5.3 公开接口与列表字段 → Task 3 ✅
- 4.3 Java client → Task 4 ✅
- 4.1 工具解禁 + schema → Task 5 ✅
- 4.2 MCP handler → Task 6 ✅
- 4.4 新意图 refund_request → Task 7 ✅
- 4.4 supervisor 映射 → Task 8 ✅
- 5.2 订单页按钮 + 展示 → Task 9 ✅
- 5.1 AI 对话确认弹窗 → Task 10 ✅
- 6 测试与验收 + 迁移 → Task 11（含迁移 SQL 在 Task 1）✅

**2. 占位符扫描：** 无 TBD/TODO；Task 7/8 中有"若……验证"的开放性表述，但均给了明确决策路径（复用现有机制 + 实现时验证），不阻塞实现。

**3. 类型一致性：**
- `refund_order` 工具名、`REFUND_ORDER_TOOL_NAME` 常量、MCP 注册名一致 ✅
- `OrderService.refundOrder(orderId, reason, context, idempotencyKey)` 签名在 Task 2/3 一致 ✅
- `JavaOrderClient.refund_order(order_id, reason, idempotency_key=...)` 在 Task 4/6 一致 ✅
- 意图 `refund_request` 在 Task 7/8 一致 ✅
- 数据库列名 amount/refund_amount/refunded_at/refund_reason 在 Task 1/2/9 一致 ✅

**开放点（实现时需按实际代码修正）：**
- InternalRequestContext 构造参数顺序（traceId, caller, userId, tenantId）——Task 3 已注明按实际修正
- ticket_worker 是否已有 handle_refund_request 或需在 Task 8 加分支——Task 8 注明验证路径
- OrderMapper 更新方法名（update 现有 or 新增）——Task 2 注明跟随现有模式
