package com.panpan.aibusinessservice.domain.model;

public record Order(
        String orderId,
        String ownerUserId,
        String tenantId,
        OrderStatus orderStatus,
        PaymentStatus paymentStatus,
        String logisticsMessage,
        String latestEvent,
        boolean canCreateTicket
) {
    public boolean visibleTo(String userId, String tenantId) {
        return ownerUserId.equals(userId) && this.tenantId.equals(tenantId);
    }
}
