# Interview Questions and Answers

## 1. Why did you choose a layered architecture for RetailIQ?
**Answer:** I separated preprocessing, feature engineering, KPI generation, SQL analytics, and dashboard design so each layer has one responsibility. That makes the project easier to test, reuse, and explain to stakeholders. It also mirrors how mature analytics teams structure production reporting.

## 2. How did you make the ETL pipeline reusable?
**Answer:** I used configurable paths, object-oriented classes, shared helper functions, and consistent output tables. The pipeline can run on fresh Olist data without code changes, and the outputs are written in a way that downstream notebook, SQL, and BI layers can reuse directly.

## 3. Why did you build a KPI engine instead of calculating metrics only in Power BI?
**Answer:** The KPI engine centralizes metric logic in Python so the same definitions can be reused across notebooks, SQL checks, and reporting. That reduces metric drift and makes the project more maintainable than calculating everything in one dashboard layer.

## 4. How did you handle profit margin if the Olist dataset does not contain cost data?
**Answer:** I did not invent cost values. The KPI layer is designed to compute profit margin only when a compatible cost column exists. If cost is unavailable, the output remains explicit and transparent rather than misleading.

## 5. What are the most important KPIs in this project?
**Answer:** Total Revenue, Total Orders, Average Order Value, Repeat Customer Rate, Customer Retention, Revenue by State, Revenue by Category, Monthly Growth, and Late Delivery Rate. These metrics give leadership a balanced view of growth, customer value, and operational health.

## 6. How did you avoid double counting in revenue calculations?
**Answer:** I aggregated order items to the order grain before rolling them up to customer, state, month, or category levels. That ensures one order contributes once to order-level KPIs and prevents inflated totals from item-level joins.

## 7. What business problem does the dashboard solve?
**Answer:** It gives senior leadership a fast operating view of growth quality. The dashboard highlights where revenue is coming from, where service performance is weak, and where action is needed on retention, freight, categories, sellers, and geography.

## 8. Why are CTEs useful in your SQL queries?
**Answer:** CTEs make the logic easier to read, help isolate order-level aggregation from final reporting, and reduce the risk of duplicated joins. They also make the queries easier to review and maintain in a business environment.

## 9. How does the project reflect real analytics-team work?
**Answer:** It includes the full workflow: raw ingestion, cleaning, feature engineering, KPI production, SQL reporting, EDA, dashboard planning, and executive communication. That is very close to how a real business intelligence team would package a retail analytics initiative.

## 10. What would you improve next?
**Answer:** I would add automated tests, scheduled orchestration, a documented semantic model for Power BI, and a small data quality framework. If additional cost data becomes available, I would also compute true gross margin rather than a placeholder or conditional margin layer.

## 11. How would you explain the business impact to senior management?
**Answer:** I would say the project shows where growth is strong, where customer loyalty can be improved, and where operational leakage is hurting margin. The goal is not just reporting performance, but identifying the levers that improve profitability and reliability.

## 12. What made the project portfolio-quality?
**Answer:** It is modular, reproducible, and business-focused. The deliverables include code, SQL, analysis, dashboard design, documentation, and executive insights, which demonstrates both technical execution and business thinking.