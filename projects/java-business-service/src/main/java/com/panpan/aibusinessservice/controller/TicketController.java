package com.panpan.aibusinessservice.controller;

import com.panpan.aibusinessservice.common.ApiResponse;
import com.panpan.aibusinessservice.common.trace.TraceFilter;
import com.panpan.aibusinessservice.dto.CurrentUserView;
import com.panpan.aibusinessservice.dto.TicketListItemView;
import com.panpan.aibusinessservice.service.AuthService;
import com.panpan.aibusinessservice.service.TicketQueryService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/tickets")
public class TicketController {
    private final AuthService authService;
    private final TicketQueryService ticketQueryService;

    public TicketController(AuthService authService, TicketQueryService ticketQueryService) {
        this.authService = authService;
        this.ticketQueryService = ticketQueryService;
    }

    @GetMapping
    public ApiResponse<List<TicketListItemView>> listTickets(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            HttpServletRequest servletRequest
    ) {
        CurrentUserView currentUser = authService.currentUser(authorization);
        return ApiResponse.ok(
                ticketQueryService.listVisibleTickets(currentUser),
                TraceFilter.currentTraceId(servletRequest)
        );
    }
}
