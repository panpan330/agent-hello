-- 已有库手动执行；新建库由 schema.sql 自动生效
ALTER TABLE orders ADD COLUMN amount DECIMAL(10,2) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN refund_amount DECIMAL(10,2) NULL;
ALTER TABLE orders ADD COLUMN refunded_at DATETIME(6) NULL;
ALTER TABLE orders ADD COLUMN refund_reason VARCHAR(255) NULL;
