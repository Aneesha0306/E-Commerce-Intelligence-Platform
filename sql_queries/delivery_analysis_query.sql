
-- Delivery Analysis: Calculates delivery times
SELECT 
    c.customer_state,
    AVG(JULIANDAY(o.order_delivered_customer_date) - 
        JULIANDAY(o.order_purchase_timestamp)) as avg_delivery_days,
    COUNT(*) as order_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_purchase_timestamp IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delivery_days DESC;
