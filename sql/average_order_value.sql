-- Average Order Value
-- Purpose: order-level revenue efficiency.
-- Suggested indexes: orders(order_id, order_purchase_timestamp), order_items(order_id)

WITH order_totals AS (
    SELECT
        o.order_id,
        DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month,
        SUM(oi.price + oi.freight_value) AS order_value
    FROM orders o
    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status IN ('delivered', 'shipped', 'invoiced', 'processing', 'approved')
    GROUP BY o.order_id, DATE_TRUNC('month', o.order_purchase_timestamp)
)
SELECT
    order_month,
    COUNT(*) AS orders,
    SUM(order_value) AS revenue,
    AVG(order_value) AS average_order_value
FROM order_totals
GROUP BY order_month
ORDER BY order_month;
