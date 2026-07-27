package com.panpan.aibusinessservice.infrastructure.persistence;

import com.panpan.aibusinessservice.domain.model.Order;
import com.panpan.aibusinessservice.domain.model.OrderStatus;
import com.panpan.aibusinessservice.domain.model.PaymentStatus;
import java.sql.ResultSet;
import java.sql.SQLException;
import org.springframework.jdbc.core.RowMapper;

class OrderRowMapper implements RowMapper<Order> {
    @Override
    public Order mapRow(ResultSet rs, int rowNum) throws SQLException {
        return new Order(
                rs.getString("order_id"),
                rs.getString("user_id"),
                rs.getString("tenant_id"),
                OrderStatus.fromCode(rs.getString("order_status")),
                PaymentStatus.fromCode(rs.getString("payment_status")),
                rs.getString("logistics_message"),
                rs.getString("latest_event"),
                rs.getBoolean("can_create_ticket")
        );
    }
}
