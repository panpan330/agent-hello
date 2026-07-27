package com.panpan.aibusinessservice.domain.model;

public enum OrderStatus {
    WAITING_SHIPMENT("waiting_shipment"),
    SHIPPED("shipped"),
    DELIVERED("delivered"),
    CANCELED("canceled");

    private final String code;

    OrderStatus(String code) {
        this.code = code;
    }

    public String code() {
        return code;
    }
}
