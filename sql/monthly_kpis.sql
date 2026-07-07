-- Monthly KPIs
-- Purpose: executive monthly dashboard metrics.
-- Suggested indexes: orders(order_purchase_timestamp, order_status), order_items(order_id), order_reviews(order_id)

WITH order_metrics AS (
    SELECT
        o.order_id,
        DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month,
        o.order_purchase_timestamp,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        SUM(oi.price + oi.freight_value) AS order_revenue,
        AVG(orv.review_score) AS average_review_score,
        CASE
            WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1
            ELSE 0
        END AS late_delivery_flag
    FROM orders o
    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id
    LEFT JOIN order_reviews orv
        ON o.order_id = orv.order_id
    WHERE o.order_status IN ('delivered', 'shipped', 'invoiced', 'processing', 'approved')
    GROUP BY o.order_id, DATE_TRUNC('month', o.order_purchase_timestamp), o.order_purchase_timestamp, o.order_delivered_customer_date, o.order_estimated_delivery_date
)
SELECT
    order_month,
    COUNT(*) AS orders,
    SUM(order_revenue) AS revenue,
    AVG(order_revenue) AS average_order_value,
    AVG(average_review_score) AS average_review_score,
    AVG(late_delivery_flag::numeric) AS late_delivery_rate
FROM order_metrics
GROUP BY order_month
ORDER BY order_month;
