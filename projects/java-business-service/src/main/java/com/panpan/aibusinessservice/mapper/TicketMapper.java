package com.panpan.aibusinessservice.mapper;

import com.panpan.aibusinessservice.entity.Ticket;
import org.apache.ibatis.annotations.Param;

public interface TicketMapper {
    Ticket selectByTenantIdAndIdempotencyKey(
            @Param("tenantId") String tenantId,
            @Param("idempotencyKey") String idempotencyKey
    );

    Ticket selectByTenantIdAndTicketId(
            @Param("tenantId") String tenantId,
            @Param("ticketId") String ticketId
    );

    int insertTicket(Ticket ticket);

    int insertTicketEvent(
            @Param("tenantId") String tenantId,
            @Param("eventId") String eventId,
            @Param("ticketId") String ticketId,
            @Param("eventType") String eventType,
            @Param("eventPayload") String eventPayload,
            @Param("operatorType") String operatorType,
            @Param("operatorId") String operatorId,
            @Param("traceId") String traceId,
            @Param("createdAt") java.time.Instant createdAt
    );
}
