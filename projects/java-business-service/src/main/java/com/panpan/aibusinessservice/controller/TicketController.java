package com.panpan.aibusinessservice.controller;

import com.panpan.aibusinessservice.common.ApiResponse;
import com.panpan.aibusinessservice.common.trace.TraceFilter;
import com.panpan.aibusinessservice.dto.CurrentUserView;
import com.panpan.aibusinessservice.dto.TicketDetailView;
import com.panpan.aibusinessservice.dto.TicketListItemView;
import com.panpan.aibusinessservice.dto.UpdateTicketStatusRequest;
import com.panpan.aibusinessservice.service.AuthService;
import com.panpan.aibusinessservice.service.TicketQueryService;
import jakarta.validation.Valid;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
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

    @GetMapping("/{ticketId}")
    public ApiResponse<TicketDetailView> getTicket(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @PathVariable String ticketId,
            HttpServletRequest servletRequest
    ) {
        CurrentUserView currentUser = authService.currentUser(authorization);
        return ApiResponse.ok(
                ticketQueryService.getVisibleTicket(currentUser, ticketId),
                TraceFilter.currentTraceId(servletRequest)
        );
    }

    @PatchMapping("/{ticketId}/status")
    public ApiResponse<TicketDetailView> updateTicketStatus(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @PathVariable String ticketId,
            @Valid @RequestBody UpdateTicketStatusRequest request,
            HttpServletRequest servletRequest
    ) {
        CurrentUserView currentUser = authService.currentUser(authorization);
        String traceId = TraceFilter.currentTraceId(servletRequest);
        return ApiResponse.ok(
                ticketQueryService.updateTicketStatus(currentUser, ticketId, request, traceId),
                traceId
        );
    }
}
