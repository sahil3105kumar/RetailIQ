-- Monthly revenue trend
SELECT
    strftime('%Y-%m', order_purchase_timestamp) AS order_month,
    SUM(order_value) AS monthly_revenue,
    COUNT(DISTINCT order_id) AS total_orders
FROM orders_curated
GROUP BY 1
ORDER BY 1;

-- Top states by total payment value
SELECT
    customer_state,
    SUM(total_payment) AS total_payment_value,
    COUNT(DISTINCT order_id) AS orders_count
FROM orders_curated
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10;
