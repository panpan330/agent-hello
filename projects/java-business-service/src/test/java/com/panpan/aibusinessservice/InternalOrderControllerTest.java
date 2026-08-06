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
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class InternalOrderControllerTest {
    @Autowired
    private MockMvc mockMvc;

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
}
