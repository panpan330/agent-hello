package com.panpan.aibusinessservice.infrastructure.persistence;

import com.panpan.aibusinessservice.domain.model.Order;
import com.panpan.aibusinessservice.domain.repository.OrderRepository;
import java.util.Optional;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
@ConditionalOnProperty(name = "app.persistence.orders", havingValue = "mysql", matchIfMissing = true)
public class JdbcOrderRepository implements OrderRepository {
    private static final String FIND_BY_TENANT_AND_ORDER_SQL = """
            SELECT
              order_id,
              user_id,
              tenant_id,
              order_status,
              payment_status,
              logistics_message,
              latest_event,
              can_create_ticket
            FROM orders
            WHERE tenant_id = ? AND order_id = ?
            """;

    private final JdbcTemplate jdbcTemplate;
    private final OrderRowMapper orderRowMapper = new OrderRowMapper();

    public JdbcOrderRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public Optional<Order> findByTenantIdAndOrderId(String tenantId, String orderId) {
        return jdbcTemplate
                .query(FIND_BY_TENANT_AND_ORDER_SQL, orderRowMapper, tenantId, orderId)
                .stream()
                .findFirst();
    }
}
