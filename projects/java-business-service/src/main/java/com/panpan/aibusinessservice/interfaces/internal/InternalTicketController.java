package com.panpan.aibusinessservice.interfaces.internal;

import com.panpan.aibusinessservice.application.service.TicketApplicationService;
import com.panpan.aibusinessservice.common.api.ApiResponse;
import com.panpan.aibusinessservice.common.security.InternalRequestContext;
import com.panpan.aibusinessservice.common.security.InternalRequestResolver;
import com.panpan.aibusinessservice.common.trace.TraceHeaders;
import com.panpan.aibusinessservice.interfaces.dto.ticket.CreateTicketCommand;
import com.panpan.aibusinessservice.interfaces.dto.ticket.TicketToolView;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/tickets")
public class InternalTicketController {
    private final InternalRequestResolver requestResolver;
    private final TicketApplicationService ticketApplicationService;

    public InternalTicketController(
            InternalRequestResolver requestResolver,
            TicketApplicationService ticketApplicationService
    ) {
        this.requestResolver = requestResolver;
        this.ticketApplicationService = ticketApplicationService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ApiResponse<TicketToolView> createTicket(
            @Valid @RequestBody CreateTicketCommand command,
            @RequestHeader(value = TraceHeaders.IDEMPOTENCY_KEY, required = false) String idempotencyKey,
            HttpServletRequest request
    ) {
        InternalRequestContext context = requestResolver.resolve(request);
        TicketToolView ticket = ticketApplicationService.createTicket(command, context, idempotencyKey);
        return ApiResponse.ok(ticket, context.traceId());
    }
}
