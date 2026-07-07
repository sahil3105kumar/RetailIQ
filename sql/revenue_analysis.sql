-- Revenue Analysis
-- Grain: order item, aggregated to order, month, category, and seller views.
-- Suggested indexes: orders(order_id, order_purchase_timestamp), order_items(order_id, product_id, seller_id), order_payments(order_id)

WITH order_item_revenue AS (
    SELECT
        oi.order_id,
        SUM(oi.price) AS item_revenue,
        SUM(oi.freight_value) AS freight_revenue,
        SUM(oi.price + oi.freight_value) AS gross_revenue,
        COUNT(*) AS items_in_order
    FROM order_items oi
    GROUP BY oi.order_id
),
order_payment_totals AS (
    SELECT
        op.order_id,
        SUM(op.payment_value) AS payment_revenue
    FROM order_payments op
    GROUP BY op.order_id
),
order_revenue AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.order_purchase_timestamp,
        COALESCE(oir.gross_revenue, 0) AS gross_revenue,
        COALESCE(opt.payment_revenue, 0) AS payment_revenue,
        COALESCE(oir.items_in_order, 0) AS items_in_order
    FROM orders o
    LEFT JOIN order_item_revenue oir
        ON o.order_id = oir.order_id
    LEFT JOIN order_payment_totals opt
        ON o.order_id = opt.order_id
    WHERE o.order_status IN ('delivered', 'shipped', 'invoiced', 'processing', 'approved')
)
SELECT
    DATE_TRUNC('month', order_purchase_timestamp) AS revenue_month,
    COUNT(DISTINCT order_id) AS orders,
    SUM(gross_revenue) AS gross_revenue,
    SUM(payment_revenue) AS payment_revenue,
    AVG(gross_revenue) AS average_order_value,
    SUM(items_in_order) AS items_sold
FROM order_revenue
GROUP BY 1
ORDER BY 1;
