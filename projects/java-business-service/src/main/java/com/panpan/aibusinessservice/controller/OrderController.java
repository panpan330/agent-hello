package com.panpan.aibusinessservice.controller;

import com.panpan.aibusinessservice.common.ApiResponse;
import com.panpan.aibusinessservice.common.trace.TraceFilter;
import com.panpan.aibusinessservice.dto.CurrentUserView;
import com.panpan.aibusinessservice.dto.OrderListItemView;
import com.panpan.aibusinessservice.service.AuthService;
import com.panpan.aibusinessservice.service.OrderQueryService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/orders")
public class OrderController {
    private final AuthService authService;
    private final OrderQueryService orderQueryService;

    public OrderController(AuthService authService, OrderQueryService orderQueryService) {
        this.authService = authService;
        this.orderQueryService = orderQueryService;
    }

    @GetMapping
    public ApiResponse<List<OrderListItemView>> listOrders(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            HttpServletRequest servletRequest
    ) {
        CurrentUserView currentUser = authService.currentUser(authorization);
        return ApiResponse.ok(
                orderQueryService.listVisibleOrders(currentUser),
                TraceFilter.currentTraceId(servletRequest)
        );
    }
}
