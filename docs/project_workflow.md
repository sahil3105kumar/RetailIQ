# Project Workflow

## End-to-End Workflow

1. Obtain the Olist dataset files.
2. Place the raw files in `data/raw`.
3. Run the preprocessing pipeline from `main.py`.
4. Validate the cleaned outputs in `data/processed`.
5. Generate feature marts with the feature engineering layer.
6. Compute KPI DataFrames through the KPI engine.
7. Run the SQL query pack for repeatable reporting.
8. Explore the notebook for patterns, outliers, and business context.
9. Use the Power BI blueprint to build the executive dashboard.
10. Publish the executive memo and presentation-ready insights.

## Operating Cadence

- Daily or on-refresh: data loading and cleaning
- Weekly: KPI review and exception management
- Monthly: trend analysis, category review, seller scorecard review
- Quarterly: strategic business review and dashboard refinement

## Quality Controls

- Validate required source files before execution
- Check for missing values and abnormal categories
- Confirm row counts after each transformation stage
- Keep business metrics consistent across Python, SQL, and Power BI

## Delivery Rhythm

This project mirrors how a real analytics team operates: raw ingestion, transformation, QA, metric production, analysis, and leadership reporting.