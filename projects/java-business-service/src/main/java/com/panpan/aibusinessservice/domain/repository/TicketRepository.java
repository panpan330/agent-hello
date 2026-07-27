package com.panpan.aibusinessservice.domain.repository;

import com.panpan.aibusinessservice.domain.model.Ticket;
import com.panpan.aibusinessservice.interfaces.dto.ticket.CreateTicketCommand;

public interface TicketRepository {
    Ticket createIdempotently(
            CreateTicketCommand command,
            String requesterUserId,
            String tenantId,
            String idempotencyKey
    );
}
