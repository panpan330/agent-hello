package com.panpan.aibusinessservice.domain.repository;

import com.panpan.aibusinessservice.domain.model.Order;
import java.util.Optional;

public interface OrderRepository {
    Optional<Order> findByOrderId(String orderId);
}
