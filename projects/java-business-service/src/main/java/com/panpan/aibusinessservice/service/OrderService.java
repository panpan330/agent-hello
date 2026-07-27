package com.panpan.aibusinessservice.service;

import com.panpan.aibusinessservice.common.security.InternalRequestContext;
import com.panpan.aibusinessservice.dto.OrderToolView;

public interface OrderService {
    OrderToolView queryOrder(String orderId, InternalRequestContext context);
}
