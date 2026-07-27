package com.panpan.aibusinessservice.domain.model;

public enum TicketStatus {
    CREATED("created"),
    PROCESSING("processing"),
    CLOSED("closed");

    private final String code;

    TicketStatus(String code) {
        this.code = code;
    }

    public String code() {
        return code;
    }
}
