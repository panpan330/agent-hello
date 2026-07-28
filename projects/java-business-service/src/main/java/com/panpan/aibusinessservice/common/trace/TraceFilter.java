package com.panpan.aibusinessservice.common.trace;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import java.util.regex.Pattern;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TraceFilter extends OncePerRequestFilter {
    private static final Pattern TRACE_ID_PATTERN = Pattern.compile("^[A-Za-z0-9._:-]{8,128}$");
    private static final String TRACE_ID_MDC_KEY = "trace_id";
    private static final String TRACE_ID_ATTRIBUTE = TraceFilter.class.getName() + ".TRACE_ID";

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        String traceId = resolveTraceId(request.getHeader(TraceHeaders.TRACE_ID));
        request.setAttribute(TRACE_ID_ATTRIBUTE, traceId);
        response.setHeader(TraceHeaders.TRACE_ID, traceId);
        MDC.put(TRACE_ID_MDC_KEY, traceId);
        try {
            filterChain.doFilter(request, response);
        } finally {
            MDC.remove(TRACE_ID_MDC_KEY);
        }
    }

    public static String currentTraceId(HttpServletRequest request) {
        Object traceId = request.getAttribute(TRACE_ID_ATTRIBUTE);
        if (traceId instanceof String value && !value.isBlank()) {
            return value;
        }
        String headerValue = request.getHeader(TraceHeaders.TRACE_ID);
        if (headerValue == null || headerValue.isBlank()) {
            return "-";
        }
        return headerValue.trim();
    }

    private String resolveTraceId(String incomingTraceId) {
        if (incomingTraceId != null) {
            String trimmedTraceId = incomingTraceId.trim();
            if (TRACE_ID_PATTERN.matcher(trimmedTraceId).matches()) {
                return trimmedTraceId;
            }
        }
        return UUID.randomUUID().toString().replace("-", "");
    }
}
