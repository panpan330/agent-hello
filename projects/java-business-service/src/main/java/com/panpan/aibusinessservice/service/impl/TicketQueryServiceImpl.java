package com.panpan.aibusinessservice.service.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.panpan.aibusinessservice.dto.CurrentUserView;
import com.panpan.aibusinessservice.dto.TicketDetailView;
import com.panpan.aibusinessservice.dto.TicketEventView;
import com.panpan.aibusinessservice.dto.TicketListItemView;
import com.panpan.aibusinessservice.dto.UpdateTicketStatusRequest;
import com.panpan.aibusinessservice.entity.Ticket;
import com.panpan.aibusinessservice.exception.BusinessErrorCode;
import com.panpan.aibusinessservice.exception.BusinessException;
import com.panpan.aibusinessservice.mapper.TicketMapper;
import com.panpan.aibusinessservice.service.TicketQueryService;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class TicketQueryServiceImpl implements TicketQueryService {
    private static final Set<String> STAFF_ROLES = Set.of("agent", "supervisor", "admin");
    private static final Map<String, Set<String>> ALLOWED_TRANSITIONS = Map.of(
            "created", Set.of("in_progress", "waiting_user", "resolved", "closed"),
            "in_progress", Set.of("waiting_user", "resolved", "closed"),
            "waiting_user", Set.of("in_progress", "resolved", "closed"),
            "resolved", Set.of("closed", "in_progress"),
            "closed", Set.of()
    );

    private final TicketMapper ticketMapper;
    private final ObjectMapper objectMapper;

    public TicketQueryServiceImpl(TicketMapper ticketMapper, ObjectMapper objectMapper) {
        this.ticketMapper = ticketMapper;
        this.objectMapper = objectMapper;
    }

    @Override
    public List<TicketListItemView> listVisibleTickets(CurrentUserView currentUser) {
        if (currentUser.roles().contains("customer")) {
            return ticketMapper.selectByTenantIdAndRequesterUserId(currentUser.tenantId(), currentUser.userId())
                    .stream()
                    .map(TicketListItemView::from)
                    .toList();
        }

        return ticketMapper.selectAllByTenantId(currentUser.tenantId())
                .stream()
                .map(TicketListItemView::from)
                .toList();
    }

    @Override
    public TicketDetailView getVisibleTicket(CurrentUserView currentUser, String ticketId) {
        Ticket ticket = requireVisibleTicket(currentUser, ticketId);
        return toDetail(ticket);
    }

    @Override
    @Transactional
    public TicketDetailView updateTicketStatus(
            CurrentUserView currentUser,
            String ticketId,
            UpdateTicketStatusRequest request,
            String traceId
    ) {
        requireStaff(currentUser);
        Ticket ticket = requireVisibleTicket(currentUser, ticketId);
        validateTransition(ticket.getTicketStatus(), request.targetStatus());

        Instant now = Instant.now();
        ticketMapper.updateTicketStatus(
                ticket.getTenantId(),
                ticket.getTicketId(),
                request.targetStatus(),
                now
        );
        ticket.setTicketStatus(request.targetStatus());
        ticket.setUpdatedAt(now);
        insertStatusChangedEvent(ticket, currentUser, request, traceId, now);
        return toDetail(ticket);
    }

    private Ticket requireVisibleTicket(CurrentUserView currentUser, String ticketId) {
        Ticket ticket = ticketMapper.selectByTenantIdAndTicketId(currentUser.tenantId(), ticketId);
        if (ticket == null) {
            throw new BusinessException(BusinessErrorCode.TICKET_NOT_FOUND);
        }
        if (currentUser.roles().contains("customer")
                && !ticket.getRequesterUserId().equals(currentUser.userId())) {
            throw new BusinessException(BusinessErrorCode.TICKET_ACCESS_DENIED);
        }
        return ticket;
    }

    private void requireStaff(CurrentUserView currentUser) {
        boolean staff = currentUser.roles().stream().anyMatch(STAFF_ROLES::contains);
        if (!staff) {
            throw new BusinessException(BusinessErrorCode.TICKET_ACCESS_DENIED);
        }
    }

    private void validateTransition(String currentStatus, String targetStatus) {
        Set<String> allowedTargets = ALLOWED_TRANSITIONS.getOrDefault(currentStatus, Set.of());
        if (!allowedTargets.contains(targetStatus)) {
            throw new BusinessException(BusinessErrorCode.TICKET_STATUS_TRANSITION_INVALID);
        }
    }

    private TicketDetailView toDetail(Ticket ticket) {
        List<TicketEventView> events = ticketMapper
                .selectEventsByTenantIdAndTicketId(ticket.getTenantId(), ticket.getTicketId())
                .stream()
                .map(TicketEventView::from)
                .toList();
        return TicketDetailView.from(ticket, events);
    }

    private void insertStatusChangedEvent(
            Ticket ticket,
            CurrentUserView currentUser,
            UpdateTicketStatusRequest request,
            String traceId,
            Instant createdAt
    ) {
        ticketMapper.insertTicketEvent(
                ticket.getTenantId(),
                "E-" + UUID.randomUUID(),
                ticket.getTicketId(),
                "status_changed",
                statusChangedPayload(request),
                "staff",
                currentUser.userId(),
                traceId,
                createdAt
        );
    }

    private String statusChangedPayload(UpdateTicketStatusRequest request) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("target_status", request.targetStatus());
        payload.put("note", request.note());
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize ticket status event payload", exception);
        }
    }
}
