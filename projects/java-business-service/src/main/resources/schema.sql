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
