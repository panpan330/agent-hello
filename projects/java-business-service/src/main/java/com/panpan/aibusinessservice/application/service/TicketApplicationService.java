package com.panpan.aibusinessservice.application.service;

import com.panpan.aibusinessservice.common.error.BusinessErrorCode;
import com.panpan.aibusinessservice.common.error.BusinessException;
import com.panpan.aibusinessservice.common.security.InternalRequestContext;
import com.panpan.aibusinessservice.domain.model.Order;
import com.panpan.aibusinessservice.domain.repository.OrderRepository;
import com.panpan.aibusinessservice.domain.repository.TicketRepository;
import com.panpan.aibusinessservice.interfaces.dto.ticket.CreateTicketCommand;
import com.panpan.aibusinessservice.interfaces.dto.ticket.TicketToolView;
import java.util.regex.Pattern;
import org.springframework.stereotype.Service;

@Service
public class TicketApplicationService {
    private static final Pattern IDEMPOTENCY_KEY_PATTERN = Pattern.compile("^[A-Za-z0-9._:-]{8,128}$");

    private final OrderRepository orderRepository;
    private final TicketRepository ticketRepository;

    public TicketApplicationService(
            OrderRepository orderRepository,
            TicketRepository ticketRepository
    ) {
        this.orderRepository = orderRepository;
        this.ticketRepository = ticketRepository;
    }

    public TicketToolView createTicket(
            CreateTicketCommand command,
            InternalRequestContext context,
            String idempotencyKey
    ) {
        String normalizedKey = validateIdempotencyKey(idempotencyKey);
        validateRelatedOrder(command, context);
        return TicketToolView.from(
                ticketRepository.createIdempotently(
                        command,
                        context.userId(),
                        context.tenantId(),
                        normalizedKey
                )
        );
    }

    private String validateIdempotencyKey(String idempotencyKey) {
        if (idempotencyKey == null || idempotencyKey.isBlank()) {
            throw new BusinessException(BusinessErrorCode.IDEMPOTENCY_KEY_REQUIRED);
        }
        String normalizedKey = idempotencyKey.trim();
        if (!IDEMPOTENCY_KEY_PATTERN.matcher(normalizedKey).matches()) {
            throw new BusinessException(BusinessErrorCode.IDEMPOTENCY_KEY_INVALID);
        }
        return normalizedKey;
    }

    private void validateRelatedOrder(CreateTicketCommand command, InternalRequestContext context) {
        if (command.relatedOrderId() == null || command.relatedOrderId().isBlank()) {
            return;
        }

        Order order = orderRepository.findByTenantIdAndOrderId(context.tenantId(), command.relatedOrderId())
                .orElseThrow(() -> new BusinessException(BusinessErrorCode.ORDER_NOT_FOUND));

        if (!order.visibleTo(context.userId(), context.tenantId())) {
            throw new BusinessException(BusinessErrorCode.ORDER_ACCESS_DENIED);
        }

        if (!order.canCreateTicket()) {
            throw new BusinessException(BusinessErrorCode.ORDER_NOT_SUPPORT_TICKET);
        }
    }
}
