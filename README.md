# RetailIQ

RetailIQ is a portfolio-grade Business Intelligence project that simulates the work of a Business Analyst in an e-commerce company.

## Tech Stack

- Python
- SQL
- Pandas
- NumPy
- Power BI
- Jupyter Notebook
- Git

## Project Structure

```text
RetailIQ/
│
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── sql/
├── src/
│   ├── preprocessing.py
│   ├── feature_engineering.py
│   ├── analysis.py
│   ├── kpi.py
│   └── utils.py
├── dashboard/
├── reports/
├── images/
├── tests/
├── requirements.txt
├── README.md
└── main.py
```

## What the Pipeline Does

1. Loads raw Olist transaction tables from `data/raw`.
2. Cleans and joins order, item, and payment data.
3. Engineers time-based analytical features.
4. Saves curated data in `data/processed/orders_curated.csv`.
5. Computes business KPIs and logs compact EDA outputs.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Example SQL Business Questions

See `/sql/business_questions.sql` for monthly revenue and top-state payment analyses.

## Power BI

Use `data/processed/orders_curated.csv` as the dashboard data source and build visuals for revenue trends, order status mix, and payment insights.
