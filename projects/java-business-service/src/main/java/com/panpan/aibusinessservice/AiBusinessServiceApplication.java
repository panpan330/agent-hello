package com.panpan.aibusinessservice;

import com.panpan.aibusinessservice.common.security.InternalApiProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(InternalApiProperties.class)
public class AiBusinessServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(AiBusinessServiceApplication.class, args);
    }
}
