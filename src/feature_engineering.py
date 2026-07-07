"""Feature engineering utilities for RetailIQ datasets."""

from __future__ import annotations

import pandas as pd


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add date-based analytical features to processed order data."""
    if df.empty:
        return df.copy()

    result = df.copy()
    result["order_purchase_timestamp"] = pd.to_datetime(
        result["order_purchase_timestamp"], errors="coerce"
    )
    result["order_year"] = result["order_purchase_timestamp"].dt.year
    result["order_month"] = result["order_purchase_timestamp"].dt.to_period("M").astype(str)
    result["order_weekday"] = result["order_purchase_timestamp"].dt.day_name()
    return result
