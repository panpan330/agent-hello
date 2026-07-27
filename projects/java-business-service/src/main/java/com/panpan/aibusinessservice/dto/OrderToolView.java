package com.panpan.aibusinessservice.dto;

import com.panpan.aibusinessservice.entity.Order;

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
                order.getOrderId(),
                order.getOrderStatus(),
                order.getPaymentStatus(),
                order.getLogisticsMessage(),
                order.getLatestEvent(),
                order.isCanCreateTicket(),
                buildSummary(order)
        );
    }

    private static String buildSummary(Order order) {
        return order.getLogisticsMessage();
    }
}
