-- Customer Analytics
-- Purpose: customer-level behavior, order frequency, and monetary contribution.
-- Suggested indexes: customers(customer_id, customer_unique_id), orders(customer_id, order_purchase_timestamp), order_items(order_id)

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        c.customer_id,
        o.order_id,
        o.order_purchase_timestamp,
        o.order_status,
        COALESCE(SUM(oi.price + oi.freight_value), 0) AS order_revenue
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status IN ('delivered', 'shipped', 'invoiced', 'processing', 'approved')
    GROUP BY c.customer_unique_id, c.customer_id, o.order_id, o.order_purchase_timestamp, o.order_status
),
customer_lifecycle AS (
    SELECT
        customer_unique_id,
        MIN(order_purchase_timestamp) AS first_order_date,
        MAX(order_purchase_timestamp) AS last_order_date,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(order_revenue) AS total_revenue,
        AVG(order_revenue) AS average_order_value
    FROM customer_orders
    GROUP BY customer_unique_id
)
SELECT
    customer_unique_id,
    first_order_date,
    last_order_date,
    total_orders,
    total_revenue,
    average_order_value,
    CASE WHEN total_orders > 1 THEN TRUE ELSE FALSE END AS repeat_customer,
    CASE
        WHEN total_orders > 1
            THEN EXTRACT(EPOCH FROM (last_order_date - first_order_date)) / 86400.0 / NULLIF(total_orders - 1, 0)
        ELSE NULL
    END AS order_frequency_days,
    CASE
        WHEN total_orders > 0
            THEN total_revenue / total_orders
        ELSE NULL
    END AS revenue_per_customer,
    CASE
        WHEN total_orders > 0
            THEN total_revenue * (1 + EXTRACT(EPOCH FROM (last_order_date - first_order_date)) / 86400.0 / 365.0)
        ELSE total_revenue
    END AS customer_lifetime_value_approx
FROM customer_lifecycle
ORDER BY total_revenue DESC;
