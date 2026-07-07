-- Customer Retention
-- Purpose: cohort retention by first purchase month.
-- Suggested indexes: orders(customer_id, order_purchase_timestamp), customers(customer_id)

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month,
        DATE_TRUNC('month', MIN(o.order_purchase_timestamp) OVER (PARTITION BY c.customer_unique_id)) AS cohort_month
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    WHERE o.order_status IN ('delivered', 'shipped', 'invoiced', 'processing', 'approved')
),
cohort_activity AS (
    SELECT DISTINCT
        customer_unique_id,
        cohort_month,
        order_month,
        (EXTRACT(YEAR FROM order_month) - EXTRACT(YEAR FROM cohort_month)) * 12
        + (EXTRACT(MONTH FROM order_month) - EXTRACT(MONTH FROM cohort_month)) AS month_number
    FROM customer_orders
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_unique_id) AS cohort_size
    FROM cohort_activity
    WHERE month_number = 0
    GROUP BY cohort_month
),
retention AS (
    SELECT
        ca.cohort_month,
        ca.month_number,
        COUNT(DISTINCT ca.customer_unique_id) AS active_customers
    FROM cohort_activity ca
    GROUP BY ca.cohort_month, ca.month_number
)
SELECT
    r.cohort_month,
    r.month_number,
    r.active_customers,
    cs.cohort_size,
    ROUND(r.active_customers::numeric / NULLIF(cs.cohort_size, 0), 4) AS retention_rate
FROM retention r
JOIN cohort_sizes cs
    ON r.cohort_month = cs.cohort_month
ORDER BY r.cohort_month, r.month_number;
