package com.panpan.aibusinessservice.mapper;

import com.panpan.aibusinessservice.entity.Order;
import java.util.List;
import org.apache.ibatis.annotations.Param;

public interface OrderMapper {
    Order selectByTenantIdAndOrderId(
            @Param("tenantId") String tenantId,
            @Param("orderId") String orderId
    );

    List<Order> selectByTenantIdAndUserId(
            @Param("tenantId") String tenantId,
            @Param("userId") String userId
    );

    List<Order> selectAllByTenantId(@Param("tenantId") String tenantId);
}
