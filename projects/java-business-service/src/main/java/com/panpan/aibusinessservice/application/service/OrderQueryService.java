package com.panpan.aibusinessservice.application.service;

import com.panpan.aibusinessservice.common.error.BusinessErrorCode;
import com.panpan.aibusinessservice.common.error.BusinessException;
import com.panpan.aibusinessservice.common.security.InternalRequestContext;
import com.panpan.aibusinessservice.domain.model.Order;
import com.panpan.aibusinessservice.domain.repository.OrderRepository;
import com.panpan.aibusinessservice.interfaces.dto.order.OrderToolView;
import java.util.regex.Pattern;
import org.springframework.stereotype.Service;

@Service
public class OrderQueryService {
    private static final Pattern ORDER_ID_PATTERN = Pattern.compile("^[A-Za-z0-9_-]{1,64}$");

    private final OrderRepository orderRepository;

    public OrderQueryService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public OrderToolView queryOrder(String orderId, InternalRequestContext context) {
        if (!ORDER_ID_PATTERN.matcher(orderId).matches()) {
            throw new BusinessException(BusinessErrorCode.ORDER_ID_INVALID);
        }

        Order order = orderRepository.findByTenantIdAndOrderId(context.tenantId(), orderId)
                .orElseThrow(() -> new BusinessException(BusinessErrorCode.ORDER_NOT_FOUND));

        if (!order.visibleTo(context.userId(), context.tenantId())) {
            throw new BusinessException(BusinessErrorCode.ORDER_ACCESS_DENIED);
        }

        return OrderToolView.from(order);
    }
}
