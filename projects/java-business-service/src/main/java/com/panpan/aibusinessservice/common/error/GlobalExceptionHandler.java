package com.panpan.aibusinessservice.common.error;

import com.panpan.aibusinessservice.common.api.ApiResponse;
import com.panpan.aibusinessservice.common.trace.TraceHeaders;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiResponse<Object>> handleBusinessException(
            BusinessException exception,
            HttpServletRequest request
    ) {
        BusinessErrorCode code = exception.errorCode();
        return ResponseEntity
                .status(code.status())
                .body(ApiResponse.error(code.name(), exception.getMessage(), traceId(request)));
    }

    @ExceptionHandler({MethodArgumentNotValidException.class, ConstraintViolationException.class})
    public ResponseEntity<ApiResponse<Object>> handleValidationException(HttpServletRequest request) {
        return ResponseEntity
                .status(HttpStatus.UNPROCESSABLE_ENTITY)
                .body(ApiResponse.error(
                        BusinessErrorCode.TICKET_REQUEST_INVALID.name(),
                        BusinessErrorCode.TICKET_REQUEST_INVALID.defaultMessage(),
                        traceId(request)
                ));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Object>> handleUnexpectedException(HttpServletRequest request) {
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.error("JAVA_SERVICE_ERROR", "Java 业务服务内部错误。", traceId(request)));
    }

    private String traceId(HttpServletRequest request) {
        String traceId = request.getHeader(TraceHeaders.TRACE_ID);
        if (traceId == null || traceId.isBlank()) {
            return "-";
        }
        return traceId.trim();
    }
}
