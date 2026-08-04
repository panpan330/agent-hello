package com.panpan.aibusinessservice.dto;

import com.panpan.aibusinessservice.entity.Ticket;
import java.time.Instant;
import java.util.List;

public record TicketDetailView(
        String ticketId,
        String requesterUserId,
        String ticketStatus,
        String title,
        String description,
        String category,
        String priority,
        String relatedOrderId,
        String source,
        String createdTraceId,
        Instant createdAt,
        Instant updatedAt,
        List<TicketEventView> events
) {
    public static TicketDetailView from(Ticket ticket, List<TicketEventView> events) {
        return new TicketDetailView(
                ticket.getTicketId(),
                ticket.getRequesterUserId(),
                ticket.getTicketStatus(),
                ticket.getTitle(),
                ticket.getDescription(),
                ticket.getCategory(),
                ticket.getPriority(),
                ticket.getRelatedOrderId(),
                ticket.getSource(),
                ticket.getCreatedTraceId(),
                ticket.getCreatedAt(),
                ticket.getUpdatedAt(),
                events
        );
    }
}
