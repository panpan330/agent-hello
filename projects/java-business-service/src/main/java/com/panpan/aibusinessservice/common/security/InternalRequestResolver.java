package com.panpan.aibusinessservice.common.security;

import com.panpan.aibusinessservice.exception.BusinessErrorCode;
import com.panpan.aibusinessservice.exception.BusinessException;
import com.panpan.aibusinessservice.common.rate.ToolRateLimiter;
import com.panpan.aibusinessservice.common.trace.TraceHeaders;
import com.panpan.aibusinessservice.config.InternalApiProperties;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.stereotype.Component;

@Component
public class InternalRequestResolver {
    private static final String EXPECTED_CALLER = "ai-service";

    private final InternalApiProperties properties;
    private final ToolRateLimiter toolRateLimiter;

    public InternalRequestResolver(InternalApiProperties properties, ToolRateLimiter toolRateLimiter) {
        this.properties = properties;
        this.toolRateLimiter = toolRateLimiter;
    }

    public InternalRequestContext resolve(HttpServletRequest request) {
        String traceId = requiredHeader(request, TraceHeaders.TRACE_ID);
        String caller = requiredHeader(request, TraceHeaders.CALLER);
        String userId = requiredHeader(request, TraceHeaders.USER_ID);
        String tenantId = optionalHeader(request, TraceHeaders.TENANT_ID, "default");
        String token = requiredHeader(request, TraceHeaders.INTERNAL_TOKEN);

        if (!EXPECTED_CALLER.equals(caller) || !properties.token().equals(token)) {
            throw new BusinessException(BusinessErrorCode.INTERNAL_AUTH_FAILED);
        }

        InternalRequestContext context = new InternalRequestContext(traceId, caller, userId, tenantId);
        toolRateLimiter.check(context, request.getMethod(), request.getRequestURI());
        return context;
    }

    private String requiredHeader(HttpServletRequest request, String name) {
        String value = request.getHeader(name);
        if (value == null || value.isBlank()) {
            throw new BusinessException(BusinessErrorCode.INTERNAL_AUTH_FAILED);
        }
        return value.trim();
    }

    private String optionalHeader(HttpServletRequest request, String name, String defaultValue) {
        String value = request.getHeader(name);
        if (value == null || value.isBlank()) {
            return defaultValue;
        }
        return value.trim();
    }
}
