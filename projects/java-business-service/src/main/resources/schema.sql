CREATE TABLE IF NOT EXISTS orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id VARCHAR(64) NOT NULL,
  order_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  order_status VARCHAR(32) NOT NULL,
  payment_status VARCHAR(32) NOT NULL,
  logistics_message VARCHAR(255) NOT NULL,
  latest_event VARCHAR(255) NOT NULL,
  can_create_ticket TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  UNIQUE KEY uk_orders_tenant_order (tenant_id, order_id),
  KEY idx_orders_tenant_user_order (tenant_id, user_id, order_id)
);

CREATE TABLE IF NOT EXISTS tickets (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id VARCHAR(64) NOT NULL,
  ticket_id VARCHAR(64) NOT NULL,
  requester_user_id VARCHAR(64) NOT NULL,
  related_order_id VARCHAR(64) NULL,
  title VARCHAR(200) NOT NULL,
  description VARCHAR(1000) NOT NULL,
  category VARCHAR(32) NOT NULL,
  priority VARCHAR(32) NOT NULL,
  ticket_status VARCHAR(32) NOT NULL,
  source VARCHAR(32) NOT NULL,
  confirmation_id VARCHAR(64) NOT NULL,
  idempotency_key VARCHAR(128) NOT NULL,
  request_fingerprint VARCHAR(64) NOT NULL,
  created_trace_id VARCHAR(128) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  UNIQUE KEY uk_tickets_tenant_ticket (tenant_id, ticket_id),
  UNIQUE KEY uk_tickets_tenant_idempotency (tenant_id, idempotency_key),
  KEY idx_tickets_tenant_requester_created (tenant_id, requester_user_id, created_at),
  KEY idx_tickets_tenant_order_category (tenant_id, related_order_id, category)
);

CREATE TABLE IF NOT EXISTS ticket_events (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id VARCHAR(64) NOT NULL,
  event_id VARCHAR(64) NOT NULL,
  ticket_id VARCHAR(64) NOT NULL,
  event_type VARCHAR(64) NOT NULL,
  event_payload JSON NOT NULL,
  operator_type VARCHAR(32) NOT NULL,
  operator_id VARCHAR(64) NOT NULL,
  trace_id VARCHAR(128) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  UNIQUE KEY uk_ticket_events_tenant_event (tenant_id, event_id),
  KEY idx_ticket_events_tenant_ticket_created (tenant_id, ticket_id, created_at)
);
