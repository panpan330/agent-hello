package com.panpan.aibusinessservice.mapper;

import com.panpan.aibusinessservice.entity.Ticket;
import com.panpan.aibusinessservice.entity.TicketEvent;
import java.time.Instant;
import java.util.List;
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

    List<Ticket> selectByTenantIdAndRequesterUserId(
            @Param("tenantId") String tenantId,
            @Param("requesterUserId") String requesterUserId
    );

    List<Ticket> selectAllByTenantId(@Param("tenantId") String tenantId);

    int insertTicket(Ticket ticket);

    List<TicketEvent> selectEventsByTenantIdAndTicketId(
            @Param("tenantId") String tenantId,
            @Param("ticketId") String ticketId
    );

    int updateTicketStatus(
            @Param("tenantId") String tenantId,
            @Param("ticketId") String ticketId,
            @Param("ticketStatus") String ticketStatus,
            @Param("updatedAt") Instant updatedAt
    );

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
