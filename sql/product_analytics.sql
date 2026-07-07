-- Product Analytics
-- Focus: category performance, product contribution, and item economics.
-- Suggested indexes: order_items(product_id, order_id), products(product_id, product_category_name), category_translation(product_category_name)

WITH item_level AS (
    SELECT
        oi.product_id,
        p.product_category_name,
        COALESCE(ct.product_category_name_english, p.product_category_name) AS category_english,
        oi.order_id,
        oi.price,
        oi.freight_value,
        oi.price + oi.freight_value AS gross_item_value
    FROM order_items oi
    JOIN products p
        ON oi.product_id = p.product_id
    LEFT JOIN product_category_name_translation ct
        ON p.product_category_name = ct.product_category_name
),
product_summary AS (
    SELECT
        product_id,
        category_english,
        COUNT(DISTINCT order_id) AS orders,
        COUNT(*) AS units_sold,
        SUM(price) AS product_revenue,
        SUM(freight_value) AS product_freight,
        AVG(price) AS average_item_price
    FROM item_level
    GROUP BY product_id, category_english
)
SELECT
    category_english,
    COUNT(DISTINCT product_id) AS distinct_products,
    SUM(orders) AS orders,
    SUM(units_sold) AS units_sold,
    SUM(product_revenue) AS product_revenue,
    SUM(product_freight) AS freight_revenue,
    AVG(average_item_price) AS average_item_price
FROM product_summary
GROUP BY category_english
ORDER BY product_revenue DESC, units_sold DESC;
