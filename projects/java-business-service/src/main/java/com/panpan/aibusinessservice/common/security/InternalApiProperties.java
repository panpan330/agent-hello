package com.panpan.aibusinessservice.common.security;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.internal")
public record InternalApiProperties(String token) {
}
