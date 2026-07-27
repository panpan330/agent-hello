package com.panpan.aibusinessservice.infrastructure.persistence;

import com.panpan.aibusinessservice.domain.model.Order;
import com.panpan.aibusinessservice.domain.model.OrderStatus;
import com.panpan.aibusinessservice.domain.model.PaymentStatus;
import com.panpan.aibusinessservice.domain.repository.OrderRepository;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class InMemoryOrderRepository implements OrderRepository {
    private final Map<String, Order> orders = Map.of(
            "A1001", new Order(
                    "A1001",
                    "U1001",
                    "default",
                    OrderStatus.SHIPPED,
                    PaymentStatus.PAID,
                    "订单已发货，预计 2 天内送达。",
                    "包裹已离开发货仓。",
                    true
            ),
            "A1002", new Order(
                    "A1002",
                    "U1001",
                    "default",
                    OrderStatus.WAITING_SHIPMENT,
                    PaymentStatus.PAID,
                    "商家已接单，等待仓库发货。",
                    "仓库正在准备出库。",
                    true
            ),
            "A2001", new Order(
                    "A2001",
                    "U2001",
                    "default",
                    OrderStatus.DELIVERED,
                    PaymentStatus.PAID,
                    "订单已签收。",
                    "用户已确认收货。",
                    false
            )
    );

    @Override
    public Optional<Order> findByOrderId(String orderId) {
        return Optional.ofNullable(orders.get(orderId));
    }
}
