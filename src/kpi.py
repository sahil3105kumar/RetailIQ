"""Business KPI calculations for the RetailIQ project."""

from __future__ import annotations

from typing import Dict

import pandas as pd


def compute_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """Compute key ecommerce KPIs from curated order-level data."""
    if df.empty:
        return {
            "total_orders": 0.0,
            "gross_revenue": 0.0,
            "avg_order_value": 0.0,
            "payment_capture_rate": 0.0,
        }

    total_orders = float(df["order_id"].nunique()) if "order_id" in df.columns else float(len(df))

    gross_revenue = float(df.get("order_value", pd.Series(dtype=float)).sum())
    total_payment = float(df.get("total_payment", pd.Series(dtype=float)).sum())

    avg_order_value = gross_revenue / total_orders if total_orders else 0.0
    payment_capture_rate = (total_payment / gross_revenue) if gross_revenue else 0.0

    return {
        "total_orders": total_orders,
        "gross_revenue": round(gross_revenue, 2),
        "avg_order_value": round(avg_order_value, 2),
        "payment_capture_rate": round(payment_capture_rate, 4),
    }
