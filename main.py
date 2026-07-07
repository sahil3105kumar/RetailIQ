"""Entry point for the RetailIQ ETL and KPI workflow."""

from __future__ import annotations

import logging
from pathlib import Path

from src.analysis import basic_eda_summary
from src.feature_engineering import add_time_features
from src.kpi import compute_kpis
from src.preprocessing import load_raw_data, preprocess_orders, save_processed_data
from src.utils import ensure_directories, setup_logging

LOGGER = logging.getLogger(__name__)


def run_pipeline() -> None:
    """Execute data loading, preprocessing, feature engineering, and KPI output."""
    base_dir = Path(__file__).resolve().parent
    raw_dir = base_dir / "data" / "raw"
    processed_dir = base_dir / "data" / "processed"
    output_file = processed_dir / "orders_curated.csv"

    ensure_directories([raw_dir, processed_dir])
    datasets = load_raw_data(raw_dir)
    curated = preprocess_orders(datasets)

    if curated.empty:
        LOGGER.warning("No curated dataset produced. Ensure raw Olist CSV files are available.")
        return

    featured = add_time_features(curated)
    save_processed_data(featured, output_file)

    kpi_summary = compute_kpis(featured)
    eda_summary = basic_eda_summary(featured)

    LOGGER.info("KPI Summary: %s", kpi_summary)
    LOGGER.info("EDA Summary: %s", eda_summary)


if __name__ == "__main__":
    setup_logging()
    run_pipeline()
