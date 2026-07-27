package com.panpan.aibusinessservice.service.impl;

import com.panpan.aibusinessservice.common.cache.OrderCache;
import com.panpan.aibusinessservice.common.security.InternalRequestContext;
import com.panpan.aibusinessservice.dto.OrderToolView;
import com.panpan.aibusinessservice.entity.Order;
import com.panpan.aibusinessservice.exception.BusinessErrorCode;
import com.panpan.aibusinessservice.exception.BusinessException;
import com.panpan.aibusinessservice.mapper.OrderMapper;
import com.panpan.aibusinessservice.service.OrderService;
import java.util.Optional;
import java.util.regex.Pattern;
import org.springframework.stereotype.Service;

@Service
public class OrderServiceImpl implements OrderService {
    private static final Pattern ORDER_ID_PATTERN = Pattern.compile("^[A-Za-z0-9_-]{1,64}$");

    private final OrderMapper orderMapper;
    private final OrderCache orderCache;

    public OrderServiceImpl(OrderMapper orderMapper, OrderCache orderCache) {
        this.orderMapper = orderMapper;
        this.orderCache = orderCache;
    }

    @Override
    public OrderToolView queryOrder(String orderId, InternalRequestContext context) {
        if (!ORDER_ID_PATTERN.matcher(orderId).matches()) {
            throw new BusinessException(BusinessErrorCode.ORDER_ID_INVALID);
        }

        Order order = orderCache.get(context.tenantId(), orderId)
                .or(() -> Optional.ofNullable(orderMapper.selectByTenantIdAndOrderId(context.tenantId(), orderId))
                        .map(foundOrder -> {
                            orderCache.put(foundOrder);
                            return foundOrder;
                        }))
                .orElseThrow(() -> new BusinessException(BusinessErrorCode.ORDER_NOT_FOUND));

        if (!order.visibleTo(context.userId(), context.tenantId())) {
            throw new BusinessException(BusinessErrorCode.ORDER_ACCESS_DENIED);
        }

        return OrderToolView.from(order);
    }
}
