package com.panpan.aibusinessservice.interfaces.dto.order;

import com.panpan.aibusinessservice.domain.model.Order;

public record OrderToolView(
        String orderId,
        String orderStatus,
        String paymentStatus,
        String logisticsMessage,
        String latestEvent,
        boolean canCreateTicket,
        String userVisibleSummary
) {
    public static OrderToolView from(Order order) {
        return new OrderToolView(
                order.orderId(),
                order.orderStatus().code(),
                order.paymentStatus().code(),
                order.logisticsMessage(),
                order.latestEvent(),
                order.canCreateTicket(),
                buildSummary(order)
        );
    }

    private static String buildSummary(Order order) {
        return order.logisticsMessage();
    }
}
