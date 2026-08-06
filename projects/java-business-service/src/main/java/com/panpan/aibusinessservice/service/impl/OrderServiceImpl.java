package com.panpan.aibusinessservice.service.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.panpan.aibusinessservice.common.cache.OrderCache;
import com.panpan.aibusinessservice.common.cache.TicketIdempotencyCache;
import com.panpan.aibusinessservice.common.cache.TicketIdempotencyCacheEntry;
import com.panpan.aibusinessservice.common.security.InternalRequestContext;
import com.panpan.aibusinessservice.dto.OrderToolView;
import com.panpan.aibusinessservice.entity.Order;
import com.panpan.aibusinessservice.entity.OrderEvent;
import com.panpan.aibusinessservice.entity.OrderStatus;
import com.panpan.aibusinessservice.entity.PaymentStatus;
import com.panpan.aibusinessservice.exception.BusinessErrorCode;
import com.panpan.aibusinessservice.exception.BusinessException;
import com.panpan.aibusinessservice.mapper.OrderMapper;
import com.panpan.aibusinessservice.service.OrderService;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.regex.Pattern;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderServiceImpl implements OrderService {
    private static final Pattern ORDER_ID_PATTERN = Pattern.compile("^[A-Za-z0-9_-]{1,64}$");

    private final OrderMapper orderMapper;
    private final OrderCache orderCache;
    private final TicketIdempotencyCache ticketIdempotencyCache;
    private final ObjectMapper objectMapper;

    public OrderServiceImpl(
            OrderMapper orderMapper,
            OrderCache orderCache,
            TicketIdempotencyCache ticketIdempotencyCache,
            ObjectMapper objectMapper
    ) {
        this.orderMapper = orderMapper;
        this.orderCache = orderCache;
        this.ticketIdempotencyCache = ticketIdempotencyCache;
        this.objectMapper = objectMapper;
    }

    @Override
    public OrderToolView queryOrder(String orderId, InternalRequestContext context) {
        if (!ORDER_ID_PATTERN.matcher(orderId).matches()) {
            throw new BusinessException(BusinessErrorCode.ORDER_ID_INVALID);
        }

        Order order = loadOrder(context, orderId);
        checkAccess(order, context);

        return OrderToolView.from(order);
    }

    @Override
    @Transactional
    public OrderToolView refundOrder(
            String orderId,
            String reason,
            InternalRequestContext context,
            String idempotencyKey
    ) {
        if (!ORDER_ID_PATTERN.matcher(orderId).matches()) {
            throw new BusinessException(BusinessErrorCode.ORDER_ID_INVALID);
        }

        String normalizedKey = normalizeIdempotencyKey(idempotencyKey);
        String fingerprint = fingerprint(orderId, reason, context.userId());

        Optional<Order> idempotent = findRefundedOrderByIdempotency(context, normalizedKey, fingerprint);
        if (idempotent.isPresent()) {
            return OrderToolView.from(idempotent.get());
        }

        Order order = loadOrder(context, orderId);
        checkAccess(order, context);

        if (!OrderStatus.WAITING_SHIPMENT.code().equals(order.getOrderStatus())) {
            throw new BusinessException(BusinessErrorCode.ORDER_NOT_REFUNDABLE);
        }
        if (PaymentStatus.REFUNDED.code().equals(order.getPaymentStatus())) {
            throw new BusinessException(BusinessErrorCode.REFUND_ALREADY_EXISTS);
        }

        try {
            applyRefund(context, order, reason, normalizedKey, fingerprint);
            return OrderToolView.from(order);
        } catch (DuplicateKeyException exception) {
            Optional<Order> concurrent = findRefundedOrderByIdempotency(context, normalizedKey, fingerprint);
            if (concurrent.isPresent()) {
                return OrderToolView.from(concurrent.get());
            }
            throw exception;
        }
    }

    private Order loadOrder(InternalRequestContext context, String orderId) {
        return orderCache.get(context.tenantId(), orderId)
                .or(() -> Optional.ofNullable(orderMapper.selectByTenantIdAndOrderId(context.tenantId(), orderId))
                        .map(foundOrder -> {
                            orderCache.put(foundOrder);
                            return foundOrder;
                        }))
                .orElseThrow(() -> new BusinessException(BusinessErrorCode.ORDER_NOT_FOUND));
    }

    private void checkAccess(Order order, InternalRequestContext context) {
        if (!order.visibleTo(context.userId(), context.tenantId())) {
            throw new BusinessException(BusinessErrorCode.ORDER_ACCESS_DENIED);
        }
    }

    private String normalizeIdempotencyKey(String idempotencyKey) {
        if (idempotencyKey == null || idempotencyKey.isBlank()) {
            return null;
        }
        return idempotencyKey.trim();
    }

    private Optional<Order> findRefundedOrderByIdempotency(
            InternalRequestContext context,
            String idempotencyKey,
            String fingerprint
    ) {
        if (idempotencyKey == null) {
            return Optional.empty();
        }

        Optional<TicketIdempotencyCacheEntry> cached = ticketIdempotencyCache.get(context.tenantId(), idempotencyKey);
        if (cached.isPresent()) {
            TicketIdempotencyCacheEntry entry = cached.get();
            if (!entry.requestFingerprint().equals(fingerprint)) {
                if (orderMapper.selectEventByTenantIdAndIdempotencyKey(context.tenantId(), idempotencyKey) != null) {
                    throw new BusinessException(BusinessErrorCode.IDEMPOTENCY_KEY_CONFLICT);
                }
                return Optional.empty();
            }
            return Optional.ofNullable(loadOrder(context, entry.ticketId()));
        }

        Optional<OrderEvent> event = Optional.ofNullable(
                orderMapper.selectEventByTenantIdAndIdempotencyKey(context.tenantId(), idempotencyKey)
        );
        if (event.isEmpty()) {
            return Optional.empty();
        }
        OrderEvent record = event.get();
        if (!record.getRequestFingerprint().equals(fingerprint)) {
            throw new BusinessException(BusinessErrorCode.IDEMPOTENCY_KEY_CONFLICT);
        }
        return Optional.ofNullable(loadOrder(context, record.getOrderId()));
    }

    private void applyRefund(
            InternalRequestContext context,
            Order order,
            String reason,
            String idempotencyKey,
            String fingerprint
    ) {
        Instant updatedAt = Instant.now();
        LocalDateTime refundedAt = LocalDateTime.now();

        order.setPaymentStatus(PaymentStatus.REFUNDED.code());
        order.setRefundAmount(order.getAmount());
        order.setRefundedAt(refundedAt);
        order.setRefundReason(reason);
        order.setLatestEvent("退款成功");
        order.setUpdatedAt(updatedAt);

        int updated = orderMapper.updateRefundState(
                order.getTenantId(),
                order.getOrderId(),
                order.getPaymentStatus(),
                order.getRefundAmount(),
                order.getRefundedAt(),
                order.getRefundReason(),
                order.getLatestEvent(),
                updatedAt
        );
        if (updated == 0) {
            // 并发下另一请求已退款该订单（payment_status 已为 refunded）
            throw new BusinessException(BusinessErrorCode.REFUND_ALREADY_EXISTS);
        }

        // 刷新订单缓存，避免 queryOrder/幂等返回读到退款前的 stale 快照
        orderCache.put(order);

        orderMapper.insertOrderEvent(
                order.getTenantId(),
                "E-" + UUID.randomUUID(),
                order.getOrderId(),
                "refund",
                refundEventPayload(order),
                context.caller(),
                context.userId(),
                context.traceId(),
                idempotencyKey,
                fingerprint,
                updatedAt
        );

        if (idempotencyKey != null) {
            ticketIdempotencyCache.put(
                    order.getTenantId(),
                    idempotencyKey,
                    new TicketIdempotencyCacheEntry(fingerprint, order.getOrderId())
            );
        }
    }

    private String refundEventPayload(Order order) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("amount", order.getRefundAmount());
        payload.put("reason", order.getRefundReason());
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize refund event payload", exception);
        }
    }

    private String fingerprint(String orderId, String reason, String userId) {
        String source = orderId + "\n" + (reason == null ? "" : reason) + "\n" + userId;
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(source.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder(hash.length * 2);
            for (byte item : hash) {
                hex.append(String.format("%02x", item));
            }
            return hex.toString();
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is not available", exception);
        }
    }
}
