package com.panpan.aibusinessservice.domain.model;

public enum PaymentStatus {
    UNPAID("unpaid"),
    PAID("paid"),
    REFUNDED("refunded");

    private final String code;

    PaymentStatus(String code) {
        this.code = code;
    }

    public String code() {
        return code;
    }
}
