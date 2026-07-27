package com.panpan.aibusinessservice.entity;

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

    public static TicketStatus fromCode(String code) {
        for (TicketStatus status : values()) {
            if (status.code.equals(code)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown ticket status: " + code);
    }
}
