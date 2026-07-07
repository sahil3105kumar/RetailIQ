"""Data ingestion and preprocessing routines for RetailIQ."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import pandas as pd

LOGGER = logging.getLogger(__name__)

RAW_FILE_MAP: Dict[str, str] = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "customers": "olist_customers_dataset.csv",
}


def load_raw_data(raw_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load available Olist CSV files from the raw data directory."""
    datasets: Dict[str, pd.DataFrame] = {}

    for name, filename in RAW_FILE_MAP.items():
        file_path = raw_dir / filename
        if not file_path.exists():
            LOGGER.warning("Missing input file: %s", file_path)
            continue
        datasets[name] = pd.read_csv(file_path)
        LOGGER.info("Loaded %s rows from %s", len(datasets[name]), filename)

    return datasets


def preprocess_orders(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Clean and join core transactional datasets for analysis."""
    required = ["orders", "order_items", "payments"]
    missing = [name for name in required if name not in datasets]
    if missing:
        LOGGER.warning("Cannot preprocess due to missing datasets: %s", missing)
        return pd.DataFrame()

    orders = datasets["orders"].copy()
    order_items = datasets["order_items"].copy()
    payments = datasets["payments"].copy()

    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )

    item_totals = (
        order_items.groupby("order_id", as_index=False)
        .agg(
            total_price=("price", "sum"),
            total_freight=("freight_value", "sum"),
            unique_items=("order_item_id", "count"),
        )
        .fillna(0)
    )

    payment_totals = (
        payments.groupby("order_id", as_index=False)
        .agg(total_payment=("payment_value", "sum"))
        .fillna(0)
    )

    curated = (
        orders.merge(item_totals, on="order_id", how="left")
        .merge(payment_totals, on="order_id", how="left")
        .fillna({"total_price": 0.0, "total_freight": 0.0, "unique_items": 0, "total_payment": 0.0})
    )

    curated["order_value"] = curated[["total_price", "total_freight"]].sum(axis=1)
    curated["unique_items"] = curated["unique_items"].astype(int)

    return curated


def save_processed_data(df: pd.DataFrame, output_path: Path) -> None:
    """Persist processed dataframe to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    LOGGER.info("Saved processed data to %s", output_path)
