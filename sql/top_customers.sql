-- Top Customers
-- Purpose: identify highest-value customers by revenue and order count.
-- Suggested indexes: customers(customer_id, customer_unique_id), orders(customer_id), order_items(order_id)

WITH customer_revenue AS (
    SELECT
        c.customer_unique_id,
        c.customer_id,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.price + oi.freight_value) AS revenue,
        MIN(o.order_purchase_timestamp) AS first_order_date,
        MAX(o.order_purchase_timestamp) AS last_order_date
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status IN ('delivered', 'shipped', 'invoiced', 'processing', 'approved')
    GROUP BY c.customer_unique_id, c.customer_id
)
SELECT
    customer_unique_id,
    total_orders,
    revenue,
    ROUND(revenue / NULLIF(total_orders, 0), 2) AS revenue_per_order,
    first_order_date,
    last_order_date
FROM customer_revenue
ORDER BY revenue DESC, total_orders DESC
LIMIT 100;
