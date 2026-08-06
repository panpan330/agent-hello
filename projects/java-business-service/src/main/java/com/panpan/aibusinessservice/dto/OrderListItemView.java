package com.panpan.aibusinessservice.dto;

import com.panpan.aibusinessservice.entity.Order;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDateTime;

public record OrderListItemView(
        String orderId,
        String ownerUserId,
        String orderStatus,
        String paymentStatus,
        String logisticsMessage,
        String latestEvent,
        boolean canCreateTicket,
        BigDecimal refundAmount,
        LocalDateTime refundedAt,
        Instant updatedAt
) {
    public static OrderListItemView from(Order order) {
        return new OrderListItemView(
                order.getOrderId(),
                order.getOwnerUserId(),
                order.getOrderStatus(),
                order.getPaymentStatus(),
                order.getLogisticsMessage(),
                order.getLatestEvent(),
                order.isCanCreateTicket(),
                order.getRefundAmount(),
                order.getRefundedAt(),
                order.getUpdatedAt()
        );
    }
}
