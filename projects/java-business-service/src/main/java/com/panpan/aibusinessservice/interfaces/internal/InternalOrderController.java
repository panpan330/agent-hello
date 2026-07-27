package com.panpan.aibusinessservice.interfaces.internal;

import com.panpan.aibusinessservice.application.service.OrderQueryService;
import com.panpan.aibusinessservice.common.api.ApiResponse;
import com.panpan.aibusinessservice.common.security.InternalRequestContext;
import com.panpan.aibusinessservice.common.security.InternalRequestResolver;
import com.panpan.aibusinessservice.interfaces.dto.order.OrderToolView;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/orders")
public class InternalOrderController {
    private final InternalRequestResolver requestResolver;
    private final OrderQueryService orderQueryService;

    public InternalOrderController(
            InternalRequestResolver requestResolver,
            OrderQueryService orderQueryService
    ) {
        this.requestResolver = requestResolver;
        this.orderQueryService = orderQueryService;
    }

    @GetMapping("/{orderId}")
    public ApiResponse<OrderToolView> getOrder(
            @PathVariable String orderId,
            HttpServletRequest request
    ) {
        InternalRequestContext context = requestResolver.resolve(request);
        return ApiResponse.ok(orderQueryService.queryOrder(orderId, context), context.traceId());
    }
}
