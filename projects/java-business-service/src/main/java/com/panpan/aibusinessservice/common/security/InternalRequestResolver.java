package com.panpan.aibusinessservice.common.security;

import com.panpan.aibusinessservice.common.error.BusinessErrorCode;
import com.panpan.aibusinessservice.common.error.BusinessException;
import com.panpan.aibusinessservice.common.trace.TraceHeaders;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.stereotype.Component;

@Component
public class InternalRequestResolver {
    private static final String EXPECTED_CALLER = "ai-service";

    private final InternalApiProperties properties;

    public InternalRequestResolver(InternalApiProperties properties) {
        this.properties = properties;
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

        return new InternalRequestContext(traceId, caller, userId, tenantId);
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
