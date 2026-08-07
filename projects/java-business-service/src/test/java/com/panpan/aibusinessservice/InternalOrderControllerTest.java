package com.panpan.aibusinessservice;

import static com.panpan.aibusinessservice.InternalApiTestSupport.TRACE_ID;
import static com.panpan.aibusinessservice.InternalApiTestSupport.withInternalHeaders;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.closeTo;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.panpan.aibusinessservice.common.trace.TraceHeaders;
import com.panpan.aibusinessservice.mapper.OrderMapper;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDateTime;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class InternalOrderControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private OrderMapper orderMapper;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void queryOrderReturnsToolFacingView() throws Exception {
        mockMvc.perform(withInternalHeaders(get("/internal/orders/A1001")))
                .andExpect(status().isOk())
                .andExpect(header().string(TraceHeaders.TRACE_ID, TRACE_ID))
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("OK"))
                .andExpect(jsonPath("$.data.order_id").value("A1001"))
                .andExpect(jsonPath("$.data.order_status").value("shipped"))
                .andExpect(jsonPath("$.data.can_create_ticket").value(true))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));
    }

    @Test
    void queryOrderDeniesOtherUsersOrder() throws Exception {
        mockMvc.perform(withInternalHeaders(get("/internal/orders/A2001")))
                .andExpect(status().isForbidden())
                .andExpect(header().string(TraceHeaders.TRACE_ID, TRACE_ID))
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("ORDER_ACCESS_DENIED"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));
    }

    @Test
    void queryOrderRejectsMissingInternalToken() throws Exception {
        mockMvc.perform(
                        get("/internal/orders/A1001")
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                                .header(TraceHeaders.CALLER, "ai-service")
                                .header(TraceHeaders.USER_ID, "U1001")
                                .header(TraceHeaders.TENANT_ID, "default")
                )
                .andExpect(status().isUnauthorized())
                .andExpect(header().string(TraceHeaders.TRACE_ID, TRACE_ID))
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("INTERNAL_AUTH_FAILED"));
    }

    @Test
    void queryOrderRejectsMissingTraceIdButReturnsGeneratedTraceHeader() throws Exception {
        MvcResult result = mockMvc.perform(
                        get("/internal/orders/A1001")
                                .header(TraceHeaders.CALLER, "ai-service")
                                .header(TraceHeaders.USER_ID, "U1001")
                                .header(TraceHeaders.TENANT_ID, "default")
                                .header(TraceHeaders.INTERNAL_TOKEN, InternalApiTestSupport.INTERNAL_TOKEN)
                )
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("INTERNAL_AUTH_FAILED"))
                .andReturn();

        assertThat(result.getResponse().getHeader(TraceHeaders.TRACE_ID))
                .matches("[0-9a-f]{32}");
    }

    @Test
    void queryOrderRejectsMissingTenantId() throws Exception {
        mockMvc.perform(
                        get("/internal/orders/A1001")
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                                .header(TraceHeaders.CALLER, "ai-service")
                                .header(TraceHeaders.USER_ID, "U1001")
                                .header(TraceHeaders.INTERNAL_TOKEN, InternalApiTestSupport.INTERNAL_TOKEN)
                )
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("INTERNAL_AUTH_FAILED"));
    }

    @Test
    void queryOrderRejectsUnexpectedCaller() throws Exception {
        mockMvc.perform(
                        get("/internal/orders/A1001")
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                                .header(TraceHeaders.CALLER, "unknown-service")
                                .header(TraceHeaders.USER_ID, "U1001")
                                .header(TraceHeaders.TENANT_ID, "default")
                                .header(TraceHeaders.INTERNAL_TOKEN, InternalApiTestSupport.INTERNAL_TOKEN)
                )
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("INTERNAL_AUTH_FAILED"));
    }

    @Test
    void queryOrderRejectsUnsafeUserId() throws Exception {
        mockMvc.perform(
                        get("/internal/orders/A1001")
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                                .header(TraceHeaders.CALLER, "ai-service")
                                .header(TraceHeaders.USER_ID, "U1001/../admin")
                                .header(TraceHeaders.TENANT_ID, "default")
                                .header(TraceHeaders.INTERNAL_TOKEN, InternalApiTestSupport.INTERNAL_TOKEN)
                )
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("INTERNAL_AUTH_FAILED"));
    }

    @Test
    void refundOrderReturnsToolFacingView() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/refund"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "refund-stage7-view-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"七天无理由退货\"}")
                )
                .andExpect(status().isOk())
                .andExpect(header().string(TraceHeaders.TRACE_ID, TRACE_ID))
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("OK"))
                .andExpect(jsonPath("$.data.order_id").value("A1002"))
                .andExpect(jsonPath("$.data.order_status").value("waiting_shipment"))
                .andExpect(jsonPath("$.data.payment_status").value("refunded"))
                .andExpect(jsonPath("$.data.refund_amount").value(closeTo(159.00, 0.001)))
                .andExpect(jsonPath("$.data.refund_reason").value("七天无理由退货"))
                .andExpect(jsonPath("$.data.latest_event").value("退款成功"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));
    }

    @Test
    void refundOrderDeniesShippedOrder() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1001/refund"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "refund-stage7-shipped-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"想退款\"}")
                )
                .andExpect(status().isConflict())
                .andExpect(header().string(TraceHeaders.TRACE_ID, TRACE_ID))
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("ORDER_NOT_REFUNDABLE"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));
    }

    @Test
    void refundOrderDeniesAlreadyRefunded() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/refund"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "refund-stage7-already-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"首次退款\"}")
                )
                .andExpect(status().isOk());

        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/refund"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "refund-stage7-already-002")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"重复退款\"}")
                )
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("REFUND_ALREADY_EXISTS"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));

        // 重复退款不产生第二条 refund 审计事件
        Integer refundEventCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM order_events WHERE tenant_id = ? AND order_id = ? AND event_type = ?",
                Integer.class,
                "default",
                "A1002",
                "refund"
        );
        assertThat(refundEventCount).isEqualTo(1);
    }

    @Test
    void refundOrderIsIdempotentForSameKey() throws Exception {
        String idempotencyKey = "refund-stage7-idem-001";

        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/refund"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, idempotencyKey)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"不想要了\"}")
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.payment_status").value("refunded"))
                .andExpect(jsonPath("$.data.refund_amount").value(closeTo(159.00, 0.001)));

        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/refund"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, idempotencyKey)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"不想要了\"}")
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.order_id").value("A1002"))
                .andExpect(jsonPath("$.data.payment_status").value("refunded"))
                .andExpect(jsonPath("$.data.refund_amount").value(closeTo(159.00, 0.001)));
    }

    @Test
    void refundOrderRejectsOtherUsersOrder() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A2001/refund"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "refund-stage7-other-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"跨用户退款\"}")
                )
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("ORDER_ACCESS_DENIED"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));
    }

    @Test
    void refundOrderRejectsNullBody() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/refund"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "refund-stage7-nullbody-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("null")
                )
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("REFUND_REASON_REQUIRED"));
    }

    @Test
    void refundOrderRequiresReasonInBody() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/refund"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "refund-stage7-noreason-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{}")
                )
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("REFUND_REASON_REQUIRED"));
    }

    @Test
    void refundOrderRejectsReasonTooLong() throws Exception {
        // reason 超过 200 字必须在 service 层拦截，否则落到 refund_reason
        // VARCHAR(255) 时 DataTruncation 返回 500。
        String tooLongReason = "A".repeat(201);
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/refund"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "refund-stage7-reason-long-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"" + tooLongReason + "\"}")
                )
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("REFUND_REASON_TOO_LONG"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));
    }

    @Test
    void updateRefundStateSkipsAlreadyRefundedRow() {
        LocalDateTime refundedAt = LocalDateTime.now();
        Instant updatedAt = Instant.now();
        BigDecimal amount = new BigDecimal("159.00");

        int first = orderMapper.updateRefundState(
                "default", "A1002", "refunded", amount, refundedAt, "首次", "退款成功", updatedAt
        );
        assertThat(first).isEqualTo(1);

        // WHERE payment_status != 'refunded' 已挡住重复更新（模拟并发下另一请求已退款）
        int second = orderMapper.updateRefundState(
                "default", "A1002", "refunded", amount, refundedAt, "重复", "退款成功", updatedAt
        );
        assertThat(second).isEqualTo(0);
    }

    @Test
    void cancelOrderReturnsToolFacingView() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/cancel"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "cancel-stage2-view-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"不想要了\"}")
                )
                .andExpect(status().isOk())
                .andExpect(header().string(TraceHeaders.TRACE_ID, TRACE_ID))
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("OK"))
                .andExpect(jsonPath("$.data.order_id").value("A1002"))
                .andExpect(jsonPath("$.data.order_status").value("canceled"))
                .andExpect(jsonPath("$.data.cancel_reason").value("不想要了"))
                .andExpect(jsonPath("$.data.canceled_at").isNotEmpty())
                .andExpect(jsonPath("$.data.latest_event").value("订单已取消"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));
    }

    @Test
    void cancelOrderDeniesShippedOrder() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1001/cancel"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "cancel-stage2-shipped-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"想取消\"}")
                )
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("ORDER_NOT_CANCELABLE"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));
    }

    @Test
    void cancelOrderDeniesAlreadyCanceled() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/cancel"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "cancel-stage2-already-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"首次取消\"}")
                )
                .andExpect(status().isOk());

        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/cancel"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "cancel-stage2-already-002")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"重复取消\"}")
                )
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("CANCEL_ALREADY_EXISTS"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));

        // 重复取消不产生第二条 cancel 审计事件
        Integer cancelEventCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM order_events WHERE tenant_id = ? AND order_id = ? AND event_type = ?",
                Integer.class,
                "default",
                "A1002",
                "cancel"
        );
        assertThat(cancelEventCount).isEqualTo(1);
    }

    @Test
    void cancelOrderIsIdempotentForSameKey() throws Exception {
        String idempotencyKey = "cancel-stage2-idem-001";

        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/cancel"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, idempotencyKey)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"不想要了\"}")
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.order_status").value("canceled"))
                .andExpect(jsonPath("$.data.cancel_reason").value("不想要了"));

        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/cancel"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, idempotencyKey)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"不想要了\"}")
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.order_id").value("A1002"))
                .andExpect(jsonPath("$.data.order_status").value("canceled"))
                .andExpect(jsonPath("$.data.cancel_reason").value("不想要了"));
    }

    @Test
    void cancelOrderRejectsOtherUsersOrder() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A2001/cancel"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "cancel-stage2-other-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"跨用户取消\"}")
                )
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("ORDER_ACCESS_DENIED"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));
    }

    @Test
    void cancelOrderRejectsNullBody() throws Exception {
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/cancel"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "cancel-stage2-nullbody-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("null")
                )
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("CANCEL_REASON_REQUIRED"));
    }

    @Test
    void cancelOrderRejectsReasonTooLong() throws Exception {
        // reason 超过 200 字必须在 service 层拦截，否则落到 cancel_reason
        // VARCHAR(255) 时 DataTruncation 返回 500。
        String tooLongReason = "A".repeat(201);
        mockMvc.perform(
                        withInternalHeaders(post("/internal/orders/A1002/cancel"))
                                .header(TraceHeaders.IDEMPOTENCY_KEY, "cancel-stage2-reason-long-001")
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"reason\": \"" + tooLongReason + "\"}")
                )
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("CANCEL_REASON_TOO_LONG"))
                .andExpect(jsonPath("$.trace_id").value(TRACE_ID));
    }

    @Test
    void updateCancelStateSkipsAlreadyCanceledRow() {
        LocalDateTime canceledAt = LocalDateTime.now();
        Instant updatedAt = Instant.now();

        int first = orderMapper.updateCancelState(
                "default", "A1002", "canceled", canceledAt, "首次", "订单已取消", updatedAt
        );
        assertThat(first).isEqualTo(1);

        // WHERE order_status != 'canceled' 已挡住重复更新（模拟并发下另一请求已取消）
        int second = orderMapper.updateCancelState(
                "default", "A1002", "canceled", canceledAt, "重复", "订单已取消", updatedAt
        );
        assertThat(second).isEqualTo(0);
    }
}
