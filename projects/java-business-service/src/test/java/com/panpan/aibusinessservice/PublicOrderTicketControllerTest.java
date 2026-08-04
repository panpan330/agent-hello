package com.panpan.aibusinessservice;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.panpan.aibusinessservice.common.trace.TraceHeaders;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest
@AutoConfigureMockMvc
class PublicOrderTicketControllerTest {
    private static final String TRACE_ID = "trace-stage11-list-test";

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void customerListsOnlyOwnOrders() throws Exception {
        String token = loginAndExtractToken("customer");

        MvcResult result = mockMvc.perform(
                        get("/api/orders")
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                                .header("Authorization", "Bearer " + token)
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.length()").value(2))
                .andReturn();

        JsonNode data = objectMapper.readTree(result.getResponse().getContentAsString()).path("data");
        for (JsonNode order : data) {
            assertThat(order.path("owner_user_id").asText()).isEqualTo("U1001");
        }
    }

    @Test
    void agentListsTenantOrders() throws Exception {
        String token = loginAndExtractToken("agent");

        mockMvc.perform(
                        get("/api/orders")
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                                .header("Authorization", "Bearer " + token)
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.length()").value(3));
    }

    @Test
    void customerListsOnlyOwnTickets() throws Exception {
        String token = loginAndExtractToken("customer");

        MvcResult result = mockMvc.perform(
                        get("/api/tickets")
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                                .header("Authorization", "Bearer " + token)
                )
                .andExpect(status().isOk())
                .andReturn();

        JsonNode data = objectMapper.readTree(result.getResponse().getContentAsString()).path("data");
        assertThat(data).isNotEmpty();
        for (JsonNode ticket : data) {
            assertThat(ticket.path("requester_user_id").asText()).isEqualTo("U1001");
        }
    }

    @Test
    void publicListsRejectMissingAuthorization() throws Exception {
        mockMvc.perform(
                        get("/api/orders")
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                )
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("AUTH_REQUIRED"));
    }

    @Test
    void agentGetsTicketDetailWithEvents() throws Exception {
        String ticketId = "T-STAGE11-DETAIL";
        seedTicket(ticketId, "U1001", "created");
        seedEvent(ticketId, "E-STAGE11-DETAIL", "created", """
                {"title":"seeded ticket"}
                """);
        String token = loginAndExtractToken("agent");

        mockMvc.perform(
                        get("/api/tickets/{ticketId}", ticketId)
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                                .header("Authorization", "Bearer " + token)
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.ticket_id").value(ticketId))
                .andExpect(jsonPath("$.data.events[0].event_type").value("created"));
    }

    @Test
    void agentUpdatesTicketStatusAndWritesEvent() throws Exception {
        String ticketId = "T-STAGE11-STATUS";
        seedTicket(ticketId, "U1001", "created");
        String token = loginAndExtractToken("agent");

        mockMvc.perform(
                        patch("/api/tickets/{ticketId}/status", ticketId)
                                .header(TraceHeaders.TRACE_ID, "trace-stage11-ticket-status")
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {
                                          "target_status": "in_progress",
                                          "note": "manual follow up"
                                        }
                                        """)
                )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.ticket_id").value(ticketId))
                .andExpect(jsonPath("$.data.ticket_status").value("in_progress"));

        String status = jdbcTemplate.queryForObject(
                "SELECT ticket_status FROM tickets WHERE tenant_id = ? AND ticket_id = ?",
                String.class,
                "default",
                ticketId
        );
        Integer eventCount = jdbcTemplate.queryForObject(
                """
                        SELECT COUNT(*)
                        FROM ticket_events
                        WHERE tenant_id = ?
                          AND ticket_id = ?
                          AND event_type = 'status_changed'
                        """,
                Integer.class,
                "default",
                ticketId
        );

        assertThat(status).isEqualTo("in_progress");
        assertThat(eventCount).isEqualTo(1);
    }

    @Test
    void customerCannotUpdateTicketStatus() throws Exception {
        String ticketId = "T-STAGE11-CUSTOMER-DENIED";
        seedTicket(ticketId, "U1001", "created");
        String token = loginAndExtractToken("customer");

        mockMvc.perform(
                        patch("/api/tickets/{ticketId}/status", ticketId)
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                                .header("Authorization", "Bearer " + token)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {
                                          "target_status": "in_progress"
                                        }
                                        """)
                )
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value("TICKET_ACCESS_DENIED"));
    }

    private String loginAndExtractToken(String username) throws Exception {
        MvcResult result = mockMvc.perform(
                        post("/api/auth/login")
                                .header(TraceHeaders.TRACE_ID, TRACE_ID)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("""
                                        {
                                          "username": "%s",
                                          "password": "123456"
                                        }
                                        """.formatted(username))
                )
                .andExpect(status().isOk())
                .andReturn();

        JsonNode body = objectMapper.readTree(result.getResponse().getContentAsString());
        return body.path("data").path("token").asText();
    }

    private void seedTicket(String ticketId, String requesterUserId, String ticketStatus) {
        jdbcTemplate.update(
                "DELETE FROM ticket_events WHERE tenant_id = ? AND ticket_id = ?",
                "default",
                ticketId
        );
        jdbcTemplate.update(
                "DELETE FROM tickets WHERE tenant_id = ? AND ticket_id = ?",
                "default",
                ticketId
        );
        jdbcTemplate.update(
                """
                        INSERT INTO tickets (
                          tenant_id,
                          ticket_id,
                          requester_user_id,
                          related_order_id,
                          title,
                          description,
                          category,
                          priority,
                          ticket_status,
                          source,
                          confirmation_id,
                          idempotency_key,
                          request_fingerprint,
                          created_trace_id,
                          created_at,
                          updated_at
                        ) VALUES (
                          'default',
                          ?,
                          ?,
                          'A1001',
                          'Stage 11 ticket',
                          'Stage 11 ticket workbench test case.',
                          'logistics',
                          'normal',
                          ?,
                          'manual',
                          ?,
                          ?,
                          ?,
                          'trace-stage11-seed',
                          CURRENT_TIMESTAMP(6),
                          CURRENT_TIMESTAMP(6)
                        )
                        """,
                ticketId,
                requesterUserId,
                ticketStatus,
                "confirmation-" + ticketId,
                "idempotency-" + ticketId,
                "fingerprint-" + ticketId
        );
    }

    private void seedEvent(String ticketId, String eventId, String eventType, String payload) {
        jdbcTemplate.update(
                """
                        INSERT INTO ticket_events (
                          tenant_id,
                          event_id,
                          ticket_id,
                          event_type,
                          event_payload,
                          operator_type,
                          operator_id,
                          trace_id,
                          created_at
                        ) VALUES (
                          'default',
                          ?,
                          ?,
                          ?,
                          ?,
                          'system',
                          'test',
                          'trace-stage11-seed',
                          CURRENT_TIMESTAMP(6)
                        )
                        """,
                eventId,
                ticketId,
                eventType,
                payload
        );
    }
}
