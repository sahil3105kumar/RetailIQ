# RetailIQ

RetailIQ is a production-oriented business intelligence project that simulates the analytical workflow of an e-commerce business analyst at a large marketplace such as Flipkart or Amazon. The project uses the Brazilian E-Commerce Public Dataset by Olist and turns raw transactional data into reusable analytics assets, KPI layers, SQL reporting, and executive-ready dashboard specifications.

## What This Project Contains

- Python ETL pipeline for cleaning and feature engineering
- SQL analytics query pack for business reporting
- KPI engine that returns pandas DataFrames
- Exploratory data analysis notebook
- Power BI dashboard blueprint for executive leadership
- Executive insights memo for senior management

## Quick Start

1. Place the raw Olist CSV files in [data/raw](data/raw).
2. Install dependencies from [requirements.txt](requirements.txt).
3. Run the pipeline with `python main.py --project-root /home/sahil/RetailIQ --overwrite`.
4. Review the cleaned outputs in [data/processed](data/processed).
5. Open the EDA notebook in [notebooks/retailiq_eda.ipynb](notebooks/retailiq_eda.ipynb).

## Documentation

- [Architecture Diagram](docs/architecture_diagram.md)
- [Data Flow Diagram](docs/data_flow_diagram.md)
- [Project Workflow](docs/project_workflow.md)
- [Folder Documentation](docs/folder_documentation.md)
- [Deployment Guide](docs/deployment_guide.md)
- [Business Case](docs/business_case.md)
- [Resume Bullet Points](docs/resume_bullets.md)
- [Interview Questions and Answers](docs/interview_questions_answers.md)

## Core Deliverables

- [src/preprocessing.py](src/preprocessing.py): raw data loading, cleaning, validation, and persistence
- [src/feature_engineering.py](src/feature_engineering.py): feature marts and business metrics
- [src/kpi.py](src/kpi.py): KPI engine returning pandas DataFrames
- [sql](sql): reusable business analytics query pack
- [dashboard](dashboard): Power BI blueprint and executive dashboard specification

## Business Outcome

RetailIQ is designed to answer the questions leadership actually asks:

- Is revenue growing, and is the growth healthy?
- Which categories, sellers, and regions are driving value?
- Where are fulfillment and retention leaks eroding performance?
- What should management act on next week?

## Folder Overview

- [data](data): raw and processed datasets
- [notebooks](notebooks): EDA and analysis notebooks
- [sql](sql): analytics-ready SQL queries
- [src](src): Python ETL, feature engineering, KPI engine, and utilities
- [dashboard](dashboard): Power BI implementation blueprint
- [reports](reports): executive summaries and management memos
- [images](images): project visuals and exports

## Notes

The project is built to resemble a real analytics team deliverable: modular, reproducible, and suitable for portfolio presentation, leadership reviews, and interview discussion.
