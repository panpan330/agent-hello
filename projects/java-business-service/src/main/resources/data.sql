INSERT INTO orders (
  tenant_id,
  order_id,
  user_id,
  order_status,
  payment_status,
  logistics_message,
  latest_event,
  can_create_ticket,
  created_at,
  updated_at
)
SELECT
  'default',
  'A1001',
  'U1001',
  'shipped',
  'paid',
  '订单已发货，预计 2 天内送达。',
  '包裹已离开发货仓。',
  1,
  CURRENT_TIMESTAMP(6),
  CURRENT_TIMESTAMP(6)
WHERE NOT EXISTS (
  SELECT 1 FROM orders WHERE tenant_id = 'default' AND order_id = 'A1001'
);

INSERT INTO orders (
  tenant_id,
  order_id,
  user_id,
  order_status,
  payment_status,
  logistics_message,
  latest_event,
  can_create_ticket,
  created_at,
  updated_at
)
SELECT
  'default',
  'A1002',
  'U1001',
  'waiting_shipment',
  'paid',
  '商家已接单，等待仓库发货。',
  '仓库正在准备出库。',
  1,
  CURRENT_TIMESTAMP(6),
  CURRENT_TIMESTAMP(6)
WHERE NOT EXISTS (
  SELECT 1 FROM orders WHERE tenant_id = 'default' AND order_id = 'A1002'
);

INSERT INTO orders (
  tenant_id,
  order_id,
  user_id,
  order_status,
  payment_status,
  logistics_message,
  latest_event,
  can_create_ticket,
  created_at,
  updated_at
)
SELECT
  'default',
  'A2001',
  'U2001',
  'delivered',
  'paid',
  '订单已签收。',
  '用户已确认收货。',
  0,
  CURRENT_TIMESTAMP(6),
  CURRENT_TIMESTAMP(6)
WHERE NOT EXISTS (
  SELECT 1 FROM orders WHERE tenant_id = 'default' AND order_id = 'A2001'
);
