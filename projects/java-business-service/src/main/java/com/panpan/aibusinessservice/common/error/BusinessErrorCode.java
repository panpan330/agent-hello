package com.panpan.aibusinessservice.common.error;

import org.springframework.http.HttpStatus;

public enum BusinessErrorCode {
    INTERNAL_AUTH_FAILED(HttpStatus.UNAUTHORIZED, "内部服务鉴权失败。"),
    ORDER_ID_INVALID(HttpStatus.UNPROCESSABLE_ENTITY, "订单号格式不正确。"),
    ORDER_NOT_FOUND(HttpStatus.NOT_FOUND, "订单不存在，请确认订单号是否正确。"),
    ORDER_ACCESS_DENIED(HttpStatus.FORBIDDEN, "当前用户无权查看或操作该订单。"),
    IDEMPOTENCY_KEY_REQUIRED(HttpStatus.BAD_REQUEST, "写操作缺少幂等键。"),
    IDEMPOTENCY_KEY_INVALID(HttpStatus.UNPROCESSABLE_ENTITY, "幂等键格式不正确。"),
    IDEMPOTENCY_KEY_CONFLICT(HttpStatus.CONFLICT, "同一个幂等键不能用于不同的请求参数。"),
    TICKET_REQUEST_INVALID(HttpStatus.UNPROCESSABLE_ENTITY, "工单请求参数不合法。"),
    TICKET_ALREADY_EXISTS(HttpStatus.CONFLICT, "已存在类似工单。"),
    ORDER_NOT_SUPPORT_TICKET(HttpStatus.CONFLICT, "当前订单不支持创建该类工单。");

    private final HttpStatus status;
    private final String defaultMessage;

    BusinessErrorCode(HttpStatus status, String defaultMessage) {
        this.status = status;
        this.defaultMessage = defaultMessage;
    }

    public HttpStatus status() {
        return status;
    }

    public String defaultMessage() {
        return defaultMessage;
    }
}
