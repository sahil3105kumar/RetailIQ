-- Top Products
-- Purpose: identify highest-performing products and categories.
-- Suggested indexes: order_items(product_id), products(product_id, product_category_name), category_translation(product_category_name)

WITH product_revenue AS (
    SELECT
        oi.product_id,
        COALESCE(ct.product_category_name_english, p.product_category_name) AS category_english,
        COUNT(DISTINCT oi.order_id) AS orders,
        COUNT(*) AS units_sold,
        SUM(oi.price) AS revenue,
        SUM(oi.freight_value) AS freight_revenue,
        AVG(oi.price) AS average_item_price
    FROM order_items oi
    JOIN products p
        ON oi.product_id = p.product_id
    LEFT JOIN product_category_name_translation ct
        ON p.product_category_name = ct.product_category_name
    GROUP BY oi.product_id, COALESCE(ct.product_category_name_english, p.product_category_name)
)
SELECT
    product_id,
    category_english,
    orders,
    units_sold,
    revenue,
    freight_revenue,
    average_item_price,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM product_revenue
ORDER BY revenue DESC, units_sold DESC
LIMIT 100;
