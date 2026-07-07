# RetailIQ Power BI Measures

Use these measure definitions as the basis for the executive dashboard.

## Core Commercial Measures
- Total Revenue = SUM('fact_orders_features'[order_value])
- Total Orders = DISTINCTCOUNT('fact_orders_features'[order_id])
- Average Order Value = DIVIDE([Total Revenue], [Total Orders])
- Revenue per Customer = DIVIDE([Total Revenue], DISTINCTCOUNT('fact_orders_features'[customer_id]))
- Repeat Customer Rate = DIVIDE(CALCULATE(DISTINCTCOUNT('dim_customers_features'[customer_id]), 'dim_customers_features'[total_orders] > 1), DISTINCTCOUNT('dim_customers_features'[customer_id]))

## Operations Measures
- Late Delivery Rate = DIVIDE(CALCULATE(COUNTROWS('fact_orders_features'), 'fact_orders_features'[late_deliveries] = TRUE()), [Total Orders])
- Average Delivery Time = AVERAGE('fact_orders_features'[delivery_time_days])
- Approval Time = AVERAGE('fact_orders_features'[approval_time_hours])
- Freight Share = DIVIDE(SUM('fact_order_items_features'[freight_value]), SUM('fact_order_items_features'[item_total_value]))

## Growth Measures
- Monthly Growth Rate = DIVIDE([Current Month Revenue] - [Previous Month Revenue], [Previous Month Revenue])
- Current Month Revenue = CALCULATE([Total Revenue], DATESMTD('fact_orders_features'[order_purchase_timestamp]))
- Previous Month Revenue = CALCULATE([Total Revenue], DATEADD('fact_orders_features'[order_purchase_timestamp], -1, MONTH))

## Customer Measures
- Customer Lifetime Value Approx = AVERAGE('dim_customers_features'[customer_lifetime_value])
- Customer Retention Rate = DIVIDE(COUNTROWS(FILTER('dim_customers_features', 'dim_customers_features'[repeat_customer] = TRUE())), DISTINCTCOUNT('dim_customers_features'[customer_id]))

## Ranking Measures
- Top Category Revenue = CALCULATE(MAX('dim_products_features'[product_revenue]))
- Top Seller Revenue = CALCULATE(MAX('dim_sellers_features'[seller_revenue]))
