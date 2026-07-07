"""KPI engine for RetailIQ business analytics.

The KPI engine consumes the feature-engineered RetailIQ tables and produces
business-friendly pandas DataFrames for reporting, dashboarding, and analysis.
Each KPI is implemented as a dedicated method so the results can be reused
independently or assembled into a single report bundle.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .feature_engineering import FeatureBundle, FeatureEngineeringError
from .utils import setup_logging


class KPIEngineError(RuntimeError):
    """Raised when KPI calculation cannot be completed."""


@dataclass(slots=True)
class KPIReport:
    """Container for KPI outputs returned by the engine."""

    total_revenue: pd.DataFrame
    total_orders: pd.DataFrame
    average_order_value: pd.DataFrame
    profit_margin: pd.DataFrame
    top_categories: pd.DataFrame
    top_sellers: pd.DataFrame
    monthly_growth: pd.DataFrame
    repeat_customers: pd.DataFrame
    customer_retention: pd.DataFrame
    revenue_by_state: pd.DataFrame
    revenue_by_category: pd.DataFrame


@dataclass(slots=True)
class RetailIQKPIEngine:
    """Compute business KPIs from feature-engineered RetailIQ tables."""

    project_root: Path
    log_file: Path | None = None
    logger: logging.Logger = field(init=False)

    def __post_init__(self) -> None:
        """Initialize structured logging for KPI calculations."""

        if self.log_file is None:
            self.log_file = self.project_root / "reports" / "kpi.log"
        self.logger = setup_logging(self.log_file)

    def build_kpi_report(self, features: FeatureBundle) -> KPIReport:
        """Build the full KPI report bundle as pandas DataFrames."""

        self._validate_bundle(features)

        total_revenue = self.total_revenue(features)
        total_orders = self.total_orders(features)
        average_order_value = self.average_order_value(features)
        profit_margin = self.profit_margin(features)
        top_categories = self.top_categories(features)
        top_sellers = self.top_sellers(features)
        monthly_growth = self.monthly_growth(features)
        repeat_customers = self.repeat_customers(features)
        customer_retention = self.customer_retention(features)
        revenue_by_state = self.revenue_by_state(features)
        revenue_by_category = self.revenue_by_category(features)

        return KPIReport(
            total_revenue=total_revenue,
            total_orders=total_orders,
            average_order_value=average_order_value,
            profit_margin=profit_margin,
            top_categories=top_categories,
            top_sellers=top_sellers,
            monthly_growth=monthly_growth,
            repeat_customers=repeat_customers,
            customer_retention=customer_retention,
            revenue_by_state=revenue_by_state,
            revenue_by_category=revenue_by_category,
        )

    def total_revenue(self, features: FeatureBundle) -> pd.DataFrame:
        """Return total revenue as a one-row DataFrame."""

        revenue = float(features.fact_orders["order_value"].fillna(0).sum())
        return pd.DataFrame(
            [{"metric": "total_revenue", "value": revenue, "currency": "BRL"}]
        )

    def total_orders(self, features: FeatureBundle) -> pd.DataFrame:
        """Return total orders as a one-row DataFrame."""

        orders = int(features.fact_orders["order_id"].nunique())
        delivered_orders = int(
            features.fact_orders["order_id"].where(features.fact_orders["order_status"].eq("delivered")).nunique()
        )
        return pd.DataFrame(
            [
                {
                    "metric": "total_orders",
                    "value": orders,
                    "delivered_orders": delivered_orders,
                }
            ]
        )

    def average_order_value(self, features: FeatureBundle) -> pd.DataFrame:
        """Return average order value as a one-row DataFrame."""

        order_values = features.fact_orders[["order_id", "order_value"]].drop_duplicates(subset=["order_id"])
        aov = float(order_values["order_value"].fillna(0).mean()) if not order_values.empty else 0.0
        median_aov = float(order_values["order_value"].fillna(0).median()) if not order_values.empty else 0.0
        return pd.DataFrame(
            [
                {
                    "metric": "average_order_value",
                    "value": aov,
                    "median_order_value": median_aov,
                }
            ]
        )

    def profit_margin(self, features: FeatureBundle) -> pd.DataFrame:
        """Return profit margin metrics when a cost column is available.

        The Olist public dataset does not contain a native cost column, so this
        method returns a structured placeholder when profit cannot be computed.
        If a compatible cost field exists in the feature tables, the margin is
        calculated from item-level revenue and cost.
        """

        order_items = features.fact_order_items.copy()
        cost_column = self._detect_cost_column(order_items.columns)
        if cost_column is None:
            return pd.DataFrame(
                [
                    {
                        "metric": "profit_margin",
                        "value": np.nan,
                        "gross_profit": np.nan,
                        "note": "No cost column available in source data",
                    }
                ]
            )

        revenue = order_items["revenue"].fillna(0)
        cost = order_items[cost_column].fillna(0)
        gross_profit = revenue - cost
        margin = gross_profit.sum() / revenue.sum() if revenue.sum() else np.nan
        return pd.DataFrame(
            [
                {
                    "metric": "profit_margin",
                    "value": float(margin) if pd.notna(margin) else np.nan,
                    "gross_profit": float(gross_profit.sum()),
                    "revenue": float(revenue.sum()),
                }
            ]
        )

    def top_categories(self, features: FeatureBundle, top_n: int = 10) -> pd.DataFrame:
        """Return the top product categories by revenue."""

        df = features.fact_order_items.copy()
        category_column = self._category_name_column(df.columns)
        if category_column is None:
            raise KPIEngineError("No category column found in fact_order_items.")

        if "revenue" not in df.columns:
            raise KPIEngineError("fact_order_items must contain a revenue column.")

        summary = (
            df.groupby(category_column, as_index=False)
            .agg(
                revenue=("revenue", "sum"),
                orders=("order_id", "nunique"),
                units_sold=("order_item_id", "count"),
            )
            .sort_values(["revenue", "units_sold"], ascending=[False, False])
            .head(top_n)
            .reset_index(drop=True)
        )
        summary = summary.rename(columns={category_column: "category"})
        summary.insert(0, "rank", np.arange(1, len(summary) + 1))
        return summary

    def top_sellers(self, features: FeatureBundle, top_n: int = 10) -> pd.DataFrame:
        """Return the top sellers by revenue."""

        df = features.fact_order_items.copy()
        required_columns = {"seller_id", "revenue", "order_id"}
        self._require_columns(df.columns, required_columns, "fact_order_items")

        summary = (
            df.groupby("seller_id", as_index=False)
            .agg(
                revenue=("revenue", "sum"),
                orders=("order_id", "nunique"),
                units_sold=("order_item_id", "count"),
            )
            .sort_values(["revenue", "orders"], ascending=[False, False])
            .head(top_n)
            .reset_index(drop=True)
        )
        summary.insert(0, "rank", np.arange(1, len(summary) + 1))
        return summary

    def monthly_growth(self, features: FeatureBundle) -> pd.DataFrame:
        """Return month-over-month revenue growth."""

        monthly = features.monthly_revenue.copy()
        self._require_columns(monthly.columns, {"order_month", "monthly_revenue"}, "monthly_revenue")

        monthly = monthly.sort_values("order_month").reset_index(drop=True)
        monthly["monthly_revenue"] = pd.to_numeric(monthly["monthly_revenue"], errors="coerce").fillna(0)
        monthly["previous_month_revenue"] = monthly["monthly_revenue"].shift(1)
        monthly["growth_amount"] = monthly["monthly_revenue"] - monthly["previous_month_revenue"]
        monthly["growth_rate"] = monthly["growth_amount"] / monthly["previous_month_revenue"].replace({0: np.nan})
        return monthly

    def repeat_customers(self, features: FeatureBundle) -> pd.DataFrame:
        """Return repeat customer counts and share."""

        customers = features.dim_customers.copy()
        self._require_columns(customers.columns, {"customer_id", "total_orders", "repeat_customer"}, "dim_customers")

        repeat_count = int(customers["repeat_customer"].fillna(False).sum())
        total_customers = int(customers["customer_id"].nunique())
        repeat_share = repeat_count / total_customers if total_customers else np.nan
        return pd.DataFrame(
            [
                {
                    "metric": "repeat_customers",
                    "repeat_customers": repeat_count,
                    "total_customers": total_customers,
                    "repeat_customer_share": repeat_share,
                }
            ]
        )

    def customer_retention(self, features: FeatureBundle, retention_window_days: int = 90) -> pd.DataFrame:
        """Return a simple retention table by first order month.

        Retention is approximated as the share of customers who place another
        order within the specified number of days after their first purchase.
        """

        customers = features.dim_customers.copy()
        orders = features.fact_orders.copy()
        self._require_columns(customers.columns, {"customer_id", "first_order_date"}, "dim_customers")
        self._require_columns(orders.columns, {"customer_id", "order_purchase_timestamp"}, "fact_orders")

        first_orders = customers[["customer_id", "first_order_date"]].dropna().drop_duplicates(subset=["customer_id"]).copy()
        first_orders["cohort_month"] = pd.to_datetime(first_orders["first_order_date"]).dt.to_period("M").astype("string")

        order_history = orders[["customer_id", "order_purchase_timestamp"]].copy()
        order_history["order_purchase_timestamp"] = pd.to_datetime(order_history["order_purchase_timestamp"], errors="coerce")
        order_history = order_history.dropna(subset=["customer_id", "order_purchase_timestamp"])

        cohort_orders = first_orders.merge(order_history, on="customer_id", how="left")
        cohort_orders["days_from_first_order"] = (
            cohort_orders["order_purchase_timestamp"] - pd.to_datetime(cohort_orders["first_order_date"])
        ).dt.days
        cohort_orders["retained"] = cohort_orders["days_from_first_order"].between(1, retention_window_days, inclusive="both")

        retained_customers = (
            cohort_orders.groupby(["cohort_month", "customer_id"], as_index=False)
            .agg(retained=("retained", "max"))
        )

        retention = (
            retained_customers.groupby("cohort_month", as_index=False)
            .agg(
                customers_in_cohort=("customer_id", "nunique"),
                retained_customers=("retained", "sum"),
            )
            .sort_values("cohort_month")
            .reset_index(drop=True)
        )
        retention["retention_rate"] = retention["retained_customers"] / retention["customers_in_cohort"].replace({0: np.nan})
        retention["retention_window_days"] = retention_window_days
        return retention

    def revenue_by_state(self, features: FeatureBundle) -> pd.DataFrame:
        """Return revenue by customer state."""

        customers = features.dim_customers.copy()
        orders = features.fact_orders.copy()
        self._require_columns(customers.columns, {"customer_id", "customer_state"}, "dim_customers")
        self._require_columns(orders.columns, {"customer_id", "order_value"}, "fact_orders")

        df = orders.merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left")
        summary = (
            df.groupby("customer_state", as_index=False)
            .agg(
                revenue=("order_value", "sum"),
                orders=("order_id", "nunique"),
                average_order_value=("order_value", "mean"),
            )
            .sort_values("revenue", ascending=False)
            .reset_index(drop=True)
        )
        return summary

    def revenue_by_category(self, features: FeatureBundle) -> pd.DataFrame:
        """Return revenue by product category."""

        df = features.fact_order_items.copy()
        category_column = self._category_name_column(df.columns)
        if category_column is None:
            raise KPIEngineError("No category column found in fact_order_items.")
        self._require_columns(df.columns, {"revenue", "order_id"}, "fact_order_items")

        summary = (
            df.groupby(category_column, as_index=False)
            .agg(
                revenue=("revenue", "sum"),
                orders=("order_id", "nunique"),
                units_sold=("order_item_id", "count"),
            )
            .sort_values("revenue", ascending=False)
            .reset_index(drop=True)
        )
        return summary.rename(columns={category_column: "category"})

    def _validate_bundle(self, features: FeatureBundle) -> None:
        """Validate the feature bundle before KPI calculation."""

        if not isinstance(features, FeatureBundle):
            raise FeatureEngineeringError("KPI engine expects a FeatureBundle from the feature engineering layer.")

    def _detect_cost_column(self, columns: Iterable[str]) -> str | None:
        """Return the first compatible cost column if present."""

        cost_candidates = ("unit_cost", "product_cost", "estimated_cost", "cost_price")
        return next((column for column in cost_candidates if column in columns), None)

    def _category_name_column(self, columns: Iterable[str]) -> str | None:
        """Return the first usable category column name."""

        category_candidates = (
            "product_category_name_english",
            "product_category_name",
            "category_english",
            "category",
        )
        return next((column for column in category_candidates if column in columns), None)

    def _require_columns(self, columns: Iterable[str], required: set[str], table_name: str) -> None:
        """Raise a helpful error when a table is missing required columns."""

        missing = sorted(required.difference(columns))
        if missing:
            raise KPIEngineError(f"Missing required columns in {table_name}: {', '.join(missing)}")
