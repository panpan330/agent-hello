package com.panpan.aibusinessservice.controller;

import com.panpan.aibusinessservice.service.OrderService;
import com.panpan.aibusinessservice.common.ApiResponse;
import com.panpan.aibusinessservice.common.security.InternalRequestContext;
import com.panpan.aibusinessservice.common.security.InternalRequestResolver;
import com.panpan.aibusinessservice.dto.OrderToolView;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/orders")
public class InternalOrderController {
    private final InternalRequestResolver requestResolver;
    private final OrderService orderService;

    public InternalOrderController(
            InternalRequestResolver requestResolver,
            OrderService orderService
    ) {
        this.requestResolver = requestResolver;
        this.orderService = orderService;
    }

    @GetMapping("/{orderId}")
    public ApiResponse<OrderToolView> getOrder(
            @PathVariable String orderId,
            HttpServletRequest request
    ) {
        InternalRequestContext context = requestResolver.resolve(request);
        return ApiResponse.ok(orderService.queryOrder(orderId, context), context.traceId());
    }
}
