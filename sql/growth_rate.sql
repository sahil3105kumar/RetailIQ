-- Growth Rate
-- Purpose: month-over-month revenue growth and order growth.
-- Suggested indexes: orders(order_purchase_timestamp, order_status), order_items(order_id)

WITH monthly_metrics AS (
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month,
        COUNT(DISTINCT o.order_id) AS orders,
        SUM(oi.price + oi.freight_value) AS revenue
    FROM orders o
    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status IN ('delivered', 'shipped', 'invoiced', 'processing', 'approved')
    GROUP BY DATE_TRUNC('month', o.order_purchase_timestamp)
),
monthly_growth AS (
    SELECT
        order_month,
        orders,
        revenue,
        LAG(orders) OVER (ORDER BY order_month) AS previous_orders,
        LAG(revenue) OVER (ORDER BY order_month) AS previous_revenue
    FROM monthly_metrics
)
SELECT
    order_month,
    orders,
    revenue,
    ROUND((orders - previous_orders) / NULLIF(previous_orders::numeric, 0), 4) AS orders_growth_rate,
    ROUND((revenue - previous_revenue) / NULLIF(previous_revenue::numeric, 0), 4) AS revenue_growth_rate
FROM monthly_growth
ORDER BY order_month;
