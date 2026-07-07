# Folder Documentation

## Repository Structure

```text
RetailIQ/
├── data/
│   ├── raw/
│   └── processed/
├── dashboard/
├── docs/
├── images/
├── notebooks/
├── reports/
├── sql/
├── src/
├── main.py
├── README.md
└── requirements.txt
```

## Folder Purpose

### `data/raw`
Stores the original Olist CSV files before processing.

### `data/processed`
Stores cleaned tables, feature marts, and reusable analytical outputs.

### `src`
Contains Python modules for preprocessing, feature engineering, KPI generation, and shared utilities.

### `sql`
Contains business analytics SQL queries organized by use case.

### `notebooks`
Contains the exploratory data analysis notebook and any future analysis notebooks.

### `dashboard`
Contains the Power BI implementation blueprint, wireframes, and measure documentation.

### `reports`
Contains executive-facing summaries, such as business memos and insight packs.

### `images`
Reserved for exported visuals, diagram snapshots, and presentation assets.

### `docs`
Contains project documentation, architecture, workflow, and career-oriented materials.

## File Purpose

- `main.py`: command-line pipeline entrypoint
- `requirements.txt`: Python dependencies
- `README.md`: project overview and navigation
- `src/preprocessing.py`: raw data ingestion and cleaning
- `src/feature_engineering.py`: feature generation
- `src/kpi.py`: KPI engine
- `notebooks/retailiq_eda.ipynb`: exploratory data analysis
- `dashboard/*`: Power BI blueprint documentation
- `reports/*`: business-facing memos and summaries