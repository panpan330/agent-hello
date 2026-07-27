package com.panpan.aibusinessservice.interfaces.dto.ticket;

import com.panpan.aibusinessservice.domain.model.Ticket;
import java.time.Instant;

public record TicketToolView(
        String ticketId,
        String ticketStatus,
        String title,
        String category,
        String priority,
        String relatedOrderId,
        Instant createdAt,
        String userVisibleSummary
) {
    public static TicketToolView from(Ticket ticket) {
        return new TicketToolView(
                ticket.ticketId(),
                ticket.ticketStatus().code(),
                ticket.title(),
                ticket.category().code(),
                ticket.priority().code(),
                ticket.relatedOrderId(),
                ticket.createdAt(),
                "工单已创建，客服会继续跟进。"
        );
    }
}
