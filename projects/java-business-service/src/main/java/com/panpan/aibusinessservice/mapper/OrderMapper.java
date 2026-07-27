package com.panpan.aibusinessservice.mapper;

import com.panpan.aibusinessservice.entity.Order;
import org.apache.ibatis.annotations.Param;

public interface OrderMapper {
    Order selectByTenantIdAndOrderId(
            @Param("tenantId") String tenantId,
            @Param("orderId") String orderId
    );
}
