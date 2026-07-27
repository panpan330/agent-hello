package com.panpan.aibusinessservice.domain.model;

import java.time.Instant;

public record Ticket(
        String ticketId,
        String requesterUserId,
        String tenantId,
        TicketStatus ticketStatus,
        String title,
        String description,
        TicketCategory category,
        TicketPriority priority,
        String relatedOrderId,
        String confirmationId,
        Instant createdAt
) {
}
