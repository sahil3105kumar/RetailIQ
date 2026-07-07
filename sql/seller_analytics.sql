-- Seller Analytics
-- Purpose: fulfillment and sales performance by seller.
-- Suggested indexes: order_items(seller_id, order_id), sellers(seller_id, seller_state), orders(order_id, order_status)

WITH seller_order_items AS (
    SELECT
        oi.seller_id,
        oi.order_id,
        COUNT(*) AS items_sold,
        SUM(oi.price) AS seller_revenue,
        SUM(oi.freight_value) AS seller_freight
    FROM order_items oi
    GROUP BY oi.seller_id, oi.order_id
),
seller_orders AS (
    SELECT
        s.seller_id,
        s.seller_city,
        s.seller_state,
        COUNT(DISTINCT soi.order_id) AS total_orders,
        SUM(soi.items_sold) AS total_items_sold,
        SUM(soi.seller_revenue) AS gross_revenue,
        SUM(soi.seller_freight) AS freight_revenue,
        AVG(soi.seller_revenue) AS avg_order_revenue
    FROM sellers s
    LEFT JOIN seller_order_items soi
        ON s.seller_id = soi.seller_id
    GROUP BY s.seller_id, s.seller_city, s.seller_state
)
SELECT
    seller_id,
    seller_city,
    seller_state,
    total_orders,
    total_items_sold,
    gross_revenue,
    freight_revenue,
    avg_order_revenue,
    RANK() OVER (ORDER BY gross_revenue DESC) AS revenue_rank
FROM seller_orders
ORDER BY gross_revenue DESC, total_items_sold DESC;
