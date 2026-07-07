"""Exploratory analysis helpers for RetailIQ."""

from __future__ import annotations

from typing import Dict

import pandas as pd


def basic_eda_summary(df: pd.DataFrame) -> Dict[str, object]:
    """Return a compact EDA summary for quick business diagnostics."""
    if df.empty:
        return {
            "row_count": 0,
            "column_count": 0,
            "date_range": None,
            "status_distribution": {},
        }

    min_date = None
    max_date = None
    if "order_purchase_timestamp" in df.columns:
        timestamps = pd.to_datetime(df["order_purchase_timestamp"], errors="coerce")
        min_date = timestamps.min()
        max_date = timestamps.max()

    status_distribution: Dict[str, int] = {}
    if "order_status" in df.columns:
        status_distribution = (
            df["order_status"].value_counts(dropna=False).to_dict()  # type: ignore[assignment]
        )

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "date_range": (str(min_date), str(max_date)) if min_date is not None else None,
        "status_distribution": status_distribution,
    }
