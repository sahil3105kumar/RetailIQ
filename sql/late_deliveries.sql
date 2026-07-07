-- Late Deliveries
-- Purpose: quantify SLA misses and delivery lag by month and geography.
-- Suggested indexes: orders(order_status, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date)

WITH delivery_metrics AS (
    SELECT
        o.order_id,
        o.order_purchase_timestamp,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        c.customer_state,
        c.customer_city,
        CASE
            WHEN o.order_delivered_customer_date IS NOT NULL
             AND o.order_estimated_delivery_date IS NOT NULL
             AND o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1
            ELSE 0
        END AS late_delivery_flag,
        EXTRACT(DAY FROM (o.order_delivered_customer_date - o.order_purchase_timestamp)) AS delivery_time_days,
        EXTRACT(DAY FROM (o.order_delivered_customer_date - o.order_estimated_delivery_date)) AS delivery_delay_days
    FROM orders o
    JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status IN ('delivered', 'shipped', 'invoiced', 'processing', 'approved')
)
SELECT
    DATE_TRUNC('month', order_purchase_timestamp) AS order_month,
    customer_state,
    customer_city,
    COUNT(*) AS orders,
    SUM(late_delivery_flag) AS late_deliveries,
    AVG(delivery_time_days) AS average_delivery_time_days,
    AVG(delivery_delay_days) AS average_delay_days,
    AVG(late_delivery_flag::numeric) AS late_delivery_rate
FROM delivery_metrics
GROUP BY 1, 2, 3
ORDER BY order_month, late_delivery_rate DESC;
