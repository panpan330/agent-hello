package com.panpan.aibusinessservice.infrastructure.persistence;

import com.panpan.aibusinessservice.common.error.BusinessErrorCode;
import com.panpan.aibusinessservice.common.error.BusinessException;
import com.panpan.aibusinessservice.domain.model.Ticket;
import com.panpan.aibusinessservice.domain.model.TicketStatus;
import com.panpan.aibusinessservice.domain.repository.TicketRepository;
import com.panpan.aibusinessservice.interfaces.dto.ticket.CreateTicketCommand;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.stereotype.Repository;

@Repository
public class InMemoryTicketRepository implements TicketRepository {
    private final AtomicInteger sequence = new AtomicInteger(1001);
    private final Map<String, IdempotencyRecord> idempotencyRecords = new ConcurrentHashMap<>();

    @Override
    public Ticket createIdempotently(
            CreateTicketCommand command,
            String requesterUserId,
            String tenantId,
            String idempotencyKey
    ) {
        String fingerprint = fingerprint(command, requesterUserId, tenantId);
        IdempotencyRecord existingRecord = idempotencyRecords.get(idempotencyKey);
        if (existingRecord != null) {
            if (!existingRecord.fingerprint().equals(fingerprint)) {
                throw new BusinessException(BusinessErrorCode.IDEMPOTENCY_KEY_CONFLICT);
            }
            return existingRecord.ticket();
        }

        Ticket ticket = new Ticket(
                "T" + sequence.getAndIncrement(),
                requesterUserId,
                tenantId,
                TicketStatus.CREATED,
                command.title(),
                command.description(),
                command.category(),
                command.priority(),
                command.relatedOrderId(),
                command.confirmationId(),
                Instant.now()
        );
        idempotencyRecords.put(idempotencyKey, new IdempotencyRecord(fingerprint, ticket));
        return ticket;
    }

    private String fingerprint(CreateTicketCommand command, String requesterUserId, String tenantId) {
        return String.valueOf(Objects.hash(
                requesterUserId,
                tenantId,
                command.title(),
                command.description(),
                command.category(),
                command.priority(),
                command.relatedOrderId(),
                command.source(),
                command.confirmationId()
        ));
    }

    private record IdempotencyRecord(String fingerprint, Ticket ticket) {
    }
}
