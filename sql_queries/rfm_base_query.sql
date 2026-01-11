
-- RFM Base Query: Gets customer purchase history
SELECT 
    c.customer_id,
    c.customer_state,
    COUNT(DISTINCT o.order_id) as frequency,
    MAX(DATE(o.order_purchase_timestamp)) as last_purchase_date,
    SUM(op.payment_value) as monetary_value,
    AVG(op.payment_value) as avg_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_payments op ON o.order_id = op.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_id, c.customer_state
ORDER BY monetary_value DESC
LIMIT 10;
