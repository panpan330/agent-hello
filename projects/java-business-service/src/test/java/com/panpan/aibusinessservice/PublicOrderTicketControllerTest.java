package com.panpan.aibusinessservice;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
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
}
