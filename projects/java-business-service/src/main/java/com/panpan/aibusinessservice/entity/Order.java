package com.panpan.aibusinessservice.entity;

public class Order {
    private String orderId;
    private String ownerUserId;
    private String tenantId;
    private String orderStatus;
    private String paymentStatus;
    private String logisticsMessage;
    private String latestEvent;
    private boolean canCreateTicket;

    public Order() {
    }

    public Order(
            String orderId,
            String ownerUserId,
            String tenantId,
            String orderStatus,
            String paymentStatus,
            String logisticsMessage,
            String latestEvent,
            boolean canCreateTicket
    ) {
        this.orderId = orderId;
        this.ownerUserId = ownerUserId;
        this.tenantId = tenantId;
        this.orderStatus = orderStatus;
        this.paymentStatus = paymentStatus;
        this.logisticsMessage = logisticsMessage;
        this.latestEvent = latestEvent;
        this.canCreateTicket = canCreateTicket;
    }

    public boolean visibleTo(String userId, String tenantId) {
        return ownerUserId.equals(userId) && this.tenantId.equals(tenantId);
    }

    public String getOrderId() {
        return orderId;
    }

    public void setOrderId(String orderId) {
        this.orderId = orderId;
    }

    public String getOwnerUserId() {
        return ownerUserId;
    }

    public void setOwnerUserId(String ownerUserId) {
        this.ownerUserId = ownerUserId;
    }

    public String getTenantId() {
        return tenantId;
    }

    public void setTenantId(String tenantId) {
        this.tenantId = tenantId;
    }

    public String getOrderStatus() {
        return orderStatus;
    }

    public void setOrderStatus(String orderStatus) {
        this.orderStatus = orderStatus;
    }

    public String getPaymentStatus() {
        return paymentStatus;
    }

    public void setPaymentStatus(String paymentStatus) {
        this.paymentStatus = paymentStatus;
    }

    public String getLogisticsMessage() {
        return logisticsMessage;
    }

    public void setLogisticsMessage(String logisticsMessage) {
        this.logisticsMessage = logisticsMessage;
    }

    public String getLatestEvent() {
        return latestEvent;
    }

    public void setLatestEvent(String latestEvent) {
        this.latestEvent = latestEvent;
    }

    public boolean isCanCreateTicket() {
        return canCreateTicket;
    }

    public void setCanCreateTicket(boolean canCreateTicket) {
        this.canCreateTicket = canCreateTicket;
    }
}
