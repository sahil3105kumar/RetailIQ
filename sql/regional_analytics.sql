-- Regional Analytics
-- Purpose: geographic performance by customer region.
-- Suggested indexes: customers(customer_state, customer_city), orders(customer_id, order_purchase_timestamp), order_items(order_id)

WITH customer_order_revenue AS (
    SELECT
        c.customer_state,
        c.customer_city,
        o.order_id,
        o.order_purchase_timestamp,
        SUM(oi.price + oi.freight_value) AS order_revenue
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status IN ('delivered', 'shipped', 'invoiced', 'processing', 'approved')
    GROUP BY c.customer_state, c.customer_city, o.order_id, o.order_purchase_timestamp
)
SELECT
    customer_state,
    customer_city,
    COUNT(DISTINCT order_id) AS orders,
    SUM(order_revenue) AS revenue,
    AVG(order_revenue) AS average_order_value,
    COUNT(DISTINCT DATE_TRUNC('month', order_purchase_timestamp)) AS active_months
FROM customer_order_revenue
GROUP BY customer_state, customer_city
ORDER BY revenue DESC, orders DESC;
