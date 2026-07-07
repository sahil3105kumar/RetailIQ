# RetailIQ Power BI Dashboard Specification

## Executive Goal
Design a leadership-grade dashboard for Flipkart-style executive review. The experience should answer, at a glance, whether the business is growing, where margin or service is under pressure, and what needs action this week.

## Design Principles
- Executive first: prioritize revenue, growth, margin, retention, and delivery reliability.
- Fast reading: the first screen should be interpretable in under 15 seconds.
- High signal, low noise: every visual must answer one business question.
- Consistent grain: avoid mixing order-level and item-level metrics in the same visual unless clearly labeled.
- Calm, premium styling: deep navy, slate, white, and restrained accents.

## Recommended Data Model
Use a star-like model built from the RetailIQ feature outputs.

### Fact Tables
- `fact_orders_features`
- `fact_order_items_features`
- `monthly_revenue`
- `customer_kpis`

### Dimensions
- `dim_customers_features`
- `dim_products_features`
- `dim_sellers_features`

### Key Relationships
- `fact_orders_features[customer_id]` -> `dim_customers_features[customer_id]`
- `fact_order_items_features[order_id]` -> `fact_orders_features[order_id]`
- `fact_order_items_features[product_id]` -> `dim_products_features[product_id]`
- `fact_order_items_features[seller_id]` -> `dim_sellers_features[seller_id]`
- `customer_kpis[customer_id]` -> `dim_customers_features[customer_id]`

## Page Structure
Create six pages:
1. Executive Summary
2. Customer Intelligence
3. Product Performance
4. Seller Performance
5. Operations & Delivery
6. Regional Performance

## Executive Summary Page
### Wireframe
- Top header with title, refresh date, and global slicers.
- KPI card row across the top.
- Large revenue and order trend visual in the center-left.
- Regional map or state bar chart in the center-right.
- Lower diagnostics row for top categories, top sellers, and late deliveries.

### KPI Cards
- Total Revenue
- Total Orders
- Average Order Value
- Profit Margin
- Repeat Customer Rate
- Late Delivery Rate
- Monthly Growth
- Revenue per Customer

### Visuals
- Line chart: revenue and orders by month
- Bar chart: top states by revenue
- Bar chart: top categories by revenue
- Bar chart: top sellers by revenue
- KPI strip or small multiples: growth, repeat customers, late deliveries

## Customer Intelligence Page
### Business Questions
- Are repeat customers contributing disproportionate revenue?
- Which cohorts retain well over time?
- What is revenue per customer and order frequency by segment?

### Visuals
- Cohort retention matrix
- Histogram: revenue per customer
- Bar chart: repeat vs one-time customer share
- Scatter plot: order frequency vs revenue per customer
- Table: top customers with conditional formatting

### Cards
- Repeat Customers
- Customer Retention
- Revenue per Customer
- Customer Lifetime Value Approx.

## Product Performance Page
### Business Questions
- Which categories drive revenue and order volume?
- Which products have concentration risk?
- Which categories have poor operational efficiency?

### Visuals
- Bar chart: top categories by revenue
- Bar chart: top categories by units sold
- Scatter plot: category revenue vs delivery delay
- Treemap: category mix
- Matrix: category, revenue, freight, units sold

### Cards
- Top Category Revenue
- Category Share of Revenue
- Product Units Sold

## Seller Performance Page
### Business Questions
- Which sellers are creating the most value?
- Which sellers are associated with delays or low review scores?
- Where is seller concentration risk highest?

### Visuals
- Ranked bar chart: top sellers by revenue
- Scatter plot: seller revenue vs late deliveries
- Table: seller scorecard with revenue, orders, delay rate, review score
- Map or state chart: seller geography

### Cards
- Top Seller Revenue
- Seller Late Delivery Rate
- Seller Order Count

## Operations & Delivery Page
### Business Questions
- Are we meeting promised delivery dates?
- Which months or states have higher service issues?
- What is the operational cost pressure from freight?

### Visuals
- Line chart: delivery time and estimated delivery time
- Bar chart: late delivery rate by state
- Heatmap: weekday vs month order density
- Waterfall: month-over-month growth contribution
- Table: delayed orders and exception list

### Cards
- Late Delivery Rate
- Average Delivery Time
- Approval Time
- Freight Share

## Regional Performance Page
### Business Questions
- Which states and cities matter most commercially?
- Where should sales and logistics investment be focused?

### Visuals
- Filled map or shape map: revenue by state
- Bar chart: orders by state
- Matrix: state, revenue, orders, AOV, delay rate
- Decomposition tree: revenue by state -> category -> seller

### Cards
- Top Revenue State
- Top Order State
- Highest Delay State

## Slicers
Use a compact slicer strip.
- Date range
- State
- City
- Category
- Seller
- Order status
- Payment type
- Customer segment
- Delivery status

## Filters
### Page-Level Filters
- Exclude cancelled orders from commercial KPIs by default.
- Use delivered and completed orders for leadership reporting.
- Allow an all-orders operational toggle on analysis pages.

### Visual-Level Filters
- Top 10 or Top 15 ranking limits for executive visuals.
- Hide low-volume categories and states where appropriate.

## Navigation
Use a left vertical navigation rail with these labels:
- Summary
- Customers
- Products
- Sellers
- Operations
- Geography

Recommended behavior:
- Active page highlight in emerald.
- Hover state in slate.
- Compact icon + label treatment.

## Color Palette
- Primary: deep navy `#0B1F3A`
- Secondary: slate `#5B6B7A`
- Background: soft white `#F7F9FC`
- Positive: emerald `#1F9D55`
- Warning: amber `#D97706`
- Risk: crimson `#C53030`
- Neutral gridlines: light gray `#D9E2EC`

## Typography
- Use a clean sans-serif such as Segoe UI or Aptos.
- Titles: bold, compact, high contrast.
- KPI numbers: large, consistent, no excessive decimals.

## Page Layout Rules
- Keep the first page above-the-fold.
- Use consistent card sizing across all pages.
- Prefer aligned columns and equal gutters.
- Avoid overloading any page with more than 6 to 8 visuals.

## Suggested Power BI Measures
Create these measures for the executive layer:
- Total Revenue
- Total Orders
- Average Order Value
- Profit Margin
- Late Delivery Rate
- Repeat Customer Rate
- Monthly Growth Rate
- Revenue per Customer
- Customer Retention Rate
- Top Category Revenue
- Top Seller Revenue

## Executive Narrative
The dashboard should tell a leadership story:
1. Are we growing?
2. Is growth healthy?
3. Where are we losing margin or service reliability?
4. What should leadership act on next?
