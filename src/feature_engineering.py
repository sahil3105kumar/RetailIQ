"""Feature engineering for analytics-ready RetailIQ datasets.

This module converts cleaned Olist tables into reusable business feature tables.
The implementation is modular so the same logic can support notebooks, SQL
exports, or BI downstream layers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .utils import ensure_directory, safe_mode, setup_logging, write_csv_file


class FeatureEngineeringError(RuntimeError):
    """Raised when feature engineering cannot complete successfully."""


@dataclass(slots=True, frozen=True)
class FeaturePaths:
    """Input and output paths for feature generation."""

    project_root: Path
    processed_dir: Path
    output_dir: Path | None = None

    def resolved_output_dir(self) -> Path:
        """Return the directory where feature tables should be written."""

        return self.output_dir or self.processed_dir


@dataclass(slots=True)
class FeatureBundle:
    """Container for reusable feature-engineered tables."""

    fact_orders: pd.DataFrame
    fact_order_items: pd.DataFrame
    dim_customers: pd.DataFrame
    dim_products: pd.DataFrame
    dim_sellers: pd.DataFrame
    monthly_revenue: pd.DataFrame
    customer_kpis: pd.DataFrame


@dataclass(slots=True)
class RetailIQFeatureEngineer:
    """Build business features from cleaned RetailIQ source tables."""

    project_root: Path
    processed_dir: Path
    output_dir: Path | None = None
    log_file: Path | None = None
    overwrite: bool = True
    logger: logging.Logger = field(init=False)

    def __post_init__(self) -> None:
        """Initialize logging and validate the configured paths."""

        if self.log_file is None:
            self.log_file = self.project_root / "reports" / "etl.log"
        self.logger = setup_logging(self.log_file)

    def build_feature_bundle(self, cleaned: dict[str, pd.DataFrame]) -> FeatureBundle:
        """Create all feature marts from cleaned source tables."""

        self._validate_input_tables(cleaned)

        orders = cleaned["orders"].copy()
        order_items = cleaned["order_items"].copy()
        customers = cleaned["customers"].copy()
        products = cleaned["products"].copy()
        sellers = cleaned["sellers"].copy()
        payments = cleaned["order_payments"].copy()
        reviews = cleaned["order_reviews"].copy()
        category_translation = cleaned["category_translation"].copy()

        fact_orders = self.build_order_features(orders, order_items, payments, reviews, customers)
        fact_order_items = self.build_order_item_features(order_items, orders, products, sellers, category_translation)
        dim_customers = self.build_customer_features(customers, orders, order_items, payments)
        dim_products = self.build_product_features(products, order_items, category_translation)
        dim_sellers = self.build_seller_features(sellers, order_items)
        monthly_revenue = self.build_monthly_revenue(fact_orders)

        customer_kpis = dim_customers[
            [
                "customer_id",
                "customer_unique_id",
                "total_orders",
                "repeat_customer",
                "revenue_per_customer",
                "order_frequency_days",
                "customer_lifetime_value",
                "clv_approx",
            ]
        ].copy()

        return FeatureBundle(
            fact_orders=fact_orders,
            fact_order_items=fact_order_items,
            dim_customers=dim_customers,
            dim_products=dim_products,
            dim_sellers=dim_sellers,
            monthly_revenue=monthly_revenue,
            customer_kpis=customer_kpis,
        )

    def build_order_features(
        self,
        orders: pd.DataFrame,
        order_items: pd.DataFrame,
        payments: pd.DataFrame,
        reviews: pd.DataFrame,
        customers: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build order-level business metrics."""

        df = self._copy_with_datetime_columns(
            orders,
            [
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
        )

        df = df.merge(self._aggregate_order_items(order_items), on="order_id", how="left")
        df = df.merge(self._aggregate_payments(payments), on="order_id", how="left")
        df = df.merge(self._aggregate_reviews(reviews), on="order_id", how="left")
        df = df.merge(self._build_customer_order_context(orders, order_items, customers), on="order_id", how="left")

        df["order_value"] = df["gross_item_value"].fillna(0) + df["gross_freight_value"].fillna(0)
        df["average_order_value"] = np.where(df["total_orders_by_customer"].gt(0), df["customer_revenue"] / df["total_orders_by_customer"], df["order_value"])
        df["delivery_time_days"] = self._days_between(df, "order_purchase_timestamp", "order_delivered_customer_date")
        df["approval_time_hours"] = self._hours_between(df, "order_purchase_timestamp", "order_approved_at")
        df["delivery_delay_days"] = self._days_between(df, "order_estimated_delivery_date", "order_delivered_customer_date")
        df["late_deliveries"] = df["delivery_delay_days"].gt(0).where(df["delivery_delay_days"].notna(), pd.NA)

        df["order_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype("string")
        df["month"] = df["order_purchase_timestamp"].dt.month
        df["quarter"] = df["order_purchase_timestamp"].dt.quarter
        df["year"] = df["order_purchase_timestamp"].dt.year
        df["weekday"] = df["order_purchase_timestamp"].dt.day_name()
        df["is_weekend_order"] = df["order_purchase_timestamp"].dt.dayofweek.isin([5, 6])

        monthly_revenue_map = df.groupby("order_month")["order_value"].sum()
        df["monthly_revenue"] = df["order_month"].map(monthly_revenue_map)

        return df.reset_index(drop=True)

    def build_order_item_features(
        self,
        order_items: pd.DataFrame,
        orders: pd.DataFrame,
        products: pd.DataFrame,
        sellers: pd.DataFrame,
        category_translation: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build item-level features for product and seller analysis."""

        df = self._copy_with_datetime_columns(order_items, ["shipping_limit_date"])
        df["item_total_value"] = df["price"].fillna(0) + df["freight_value"].fillna(0)
        df["freight_share"] = np.where(df["item_total_value"].ne(0), df["freight_value"] / df["item_total_value"], np.nan)
        df["high_freight_flag"] = df["freight_value"].gt(df["price"])

        product_features = self._build_product_features(products, category_translation)
        seller_features = self._build_seller_features(sellers, order_items)

        df = df.merge(orders[["order_id", "customer_id", "order_purchase_timestamp", "order_status"]], on="order_id", how="left")
        df = df.merge(product_features, on="product_id", how="left")
        df = df.merge(seller_features, on="seller_id", how="left")

        df["revenue"] = df["item_total_value"]
        df["weekend_order"] = df["order_purchase_timestamp"].dt.dayofweek.isin([5, 6])
        df["profit_margin"] = self._compute_profit_margin(df)
        return df.reset_index(drop=True)

    def build_customer_features(
        self,
        customers: pd.DataFrame,
        orders: pd.DataFrame,
        order_items: pd.DataFrame,
        payments: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build customer-level KPIs and lifecycle features."""

        df = customers.copy()
        customer_revenue = self._build_customer_revenue(orders, order_items, payments)
        customer_timing = self._build_customer_timing(orders)

        df = df.merge(customer_timing, on="customer_id", how="left")
        df = df.merge(customer_revenue, on="customer_id", how="left")

        df["total_orders"] = df["total_orders"].fillna(0).astype("int64")
        df["repeat_customer"] = df["total_orders"].gt(1)
        df["revenue_per_customer"] = np.where(df["total_orders"].gt(0), df["customer_revenue"] / df["total_orders"], 0)
        df["order_frequency_days"] = np.where(df["total_orders"].gt(1), df["customer_span_days"] / (df["total_orders"] - 1), np.nan)
        df["clv_approx"] = df["customer_revenue"].fillna(0)
        df["customer_lifetime_value"] = df["clv_approx"]
        return df.reset_index(drop=True)

    def build_product_features(
        self,
        products: pd.DataFrame,
        order_items: pd.DataFrame,
        category_translation: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build product-level features for category and fulfillment analysis."""

        df = self._build_product_features(products, category_translation)
        item_metrics = order_items.groupby("product_id", as_index=False).agg(
            product_units_sold=("order_id", "count"),
            product_revenue=("price", "sum"),
            product_freight=("freight_value", "sum"),
        )
        df = df.merge(item_metrics, on="product_id", how="left")
        return df.reset_index(drop=True)

    def build_seller_features(self, sellers: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
        """Build seller-level features for fulfillment analysis."""

        df = self._build_seller_features(sellers, order_items)
        seller_metrics = order_items.groupby("seller_id", as_index=False).agg(
            seller_revenue=("price", "sum"),
            seller_freight=("freight_value", "sum"),
            seller_items=("order_id", "count"),
            seller_unique_orders=("order_id", "nunique"),
        )
        df = df.merge(seller_metrics, on="seller_id", how="left")
        return df.reset_index(drop=True)

    def build_monthly_revenue(self, order_features: pd.DataFrame) -> pd.DataFrame:
        """Aggregate monthly revenue and average order value."""

        if "order_purchase_timestamp" not in order_features.columns:
            raise FeatureEngineeringError("order_purchase_timestamp is required to build monthly revenue.")

        monthly = (
            order_features.groupby(order_features["order_purchase_timestamp"].dt.to_period("M"), as_index=False)
            .agg(
                monthly_revenue=("order_value", "sum"),
                orders_in_month=("order_id", "nunique"),
                average_order_value=("order_value", "mean"),
            )
            .rename(columns={"order_purchase_timestamp": "order_month"})
            .sort_values("order_month")
            .reset_index(drop=True)
        )
        monthly["order_month"] = monthly["order_month"].astype("string")
        return monthly

    def save_feature_bundle(self, bundle: FeatureBundle) -> None:
        """Persist feature outputs to the configured output directory."""

        output_dir = self._validated_output_dir()
        ensure_directory(output_dir)

        outputs = {
            "fact_orders_features": bundle.fact_orders,
            "fact_order_items_features": bundle.fact_order_items,
            "dim_customers_features": bundle.dim_customers,
            "dim_products_features": bundle.dim_products,
            "dim_sellers_features": bundle.dim_sellers,
            "monthly_revenue": bundle.monthly_revenue,
            "customer_kpis": bundle.customer_kpis,
        }

        for name, dataframe in outputs.items():
            output_path = output_dir / f"{name}.csv"
            if output_path.exists() and not self.overwrite:
                self.logger.info("Skipped existing file: %s", output_path)
                continue
            write_csv_file(dataframe, output_path)
            self.logger.info("Saved feature table %s to %s", name, output_path)

    def _aggregate_order_items(self, order_items: pd.DataFrame) -> pd.DataFrame:
        """Aggregate order items to the order grain."""

        return (
            order_items.groupby("order_id", as_index=False)
            .agg(
                total_items=("order_item_id", "count"),
                unique_products=("product_id", "nunique"),
                unique_sellers=("seller_id", "nunique"),
                gross_item_value=("price", "sum"),
                gross_freight_value=("freight_value", "sum"),
                average_item_price=("price", "mean"),
            )
            .reset_index(drop=True)
        )

    def _aggregate_payments(self, payments: pd.DataFrame) -> pd.DataFrame:
        """Aggregate payment data to the order grain."""

        return (
            payments.groupby("order_id", as_index=False)
            .agg(
                total_payment_value=("payment_value", "sum"),
                total_installments=("payment_installments", "sum"),
                payment_method_count=("payment_type", "nunique"),
                dominant_payment_type=("payment_type", lambda series: safe_mode(series, default="Unknown")),
            )
            .reset_index(drop=True)
        )

    def _aggregate_reviews(self, reviews: pd.DataFrame) -> pd.DataFrame:
        """Aggregate review data to the order grain."""

        return (
            reviews.groupby("order_id", as_index=False)
            .agg(
                average_review_score=("review_score", "mean"),
                review_count=("review_id", "count"),
                review_answer_timestamp=("review_answer_timestamp", "max"),
            )
            .reset_index(drop=True)
        )

    def _build_customer_order_context(self, orders: pd.DataFrame, order_items: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
        """Build customer-linked order context for order-level features."""

        customer_revenue = self._build_customer_revenue(orders, order_items, pd.DataFrame(columns=["order_id", "payment_value"]))
        customer_timing = self._build_customer_timing(orders)

        customer_context = customer_timing.merge(customer_revenue, on="customer_id", how="left")
        customer_context["average_order_value_customer"] = np.where(
            customer_context["total_orders"].gt(0),
            customer_context["customer_revenue"] / customer_context["total_orders"],
            np.nan,
        )

        return orders[["order_id", "customer_id"]].merge(customer_context, on="customer_id", how="left")

    def _build_customer_revenue(self, orders: pd.DataFrame, order_items: pd.DataFrame, payments: pd.DataFrame) -> pd.DataFrame:
        """Estimate revenue generated by each customer."""

        order_revenue = orders[["order_id", "customer_id"]].merge(
            order_items.groupby("order_id", as_index=False).agg(order_value=("price", "sum")),
            on="order_id",
            how="left",
        )
        order_revenue = order_revenue.drop_duplicates(subset=["order_id"])
        item_revenue = order_revenue.groupby("customer_id", as_index=False).agg(
            customer_revenue=("order_value", "sum"),
            total_orders=("order_id", "nunique"),
        )

        if not payments.empty and {"order_id", "payment_value"}.issubset(payments.columns):
            payment_revenue = (
                orders[["order_id", "customer_id"]]
                .merge(payments.groupby("order_id", as_index=False).agg(payment_value=("payment_value", "sum")), on="order_id", how="left")
                .drop_duplicates(subset=["order_id"])
                .groupby("customer_id", as_index=False)
                .agg(payment_revenue=("payment_value", "sum"))
            )
            item_revenue = item_revenue.merge(payment_revenue, on="customer_id", how="left")
            item_revenue["customer_revenue"] = item_revenue["customer_revenue"].fillna(item_revenue["payment_revenue"])

        return item_revenue[["customer_id", "customer_revenue", "total_orders"]]

    def _build_customer_timing(self, orders: pd.DataFrame) -> pd.DataFrame:
        """Build first and last purchase timing per customer."""

        grouped = (
            self._copy_with_datetime_columns(orders, ["order_purchase_timestamp"])
            .sort_values("order_purchase_timestamp")
            .groupby("customer_id", as_index=False)
            .agg(
                first_order_date=("order_purchase_timestamp", "min"),
                last_order_date=("order_purchase_timestamp", "max"),
                total_orders=("order_id", "nunique"),
            )
        )
        grouped["customer_span_days"] = (grouped["last_order_date"] - grouped["first_order_date"]).dt.days
        return grouped

    def _build_product_features(self, products: pd.DataFrame, category_translation: pd.DataFrame) -> pd.DataFrame:
        """Build product master features and category translation."""

        df = self._copy_with_text_columns(products)
        df = self._rename_product_columns(df)
        df = self._coerce_numeric_columns(
            df,
            [
                "product_name_length",
                "product_description_length",
                "product_photos_qty",
                "product_weight_g",
                "product_length_cm",
                "product_height_cm",
                "product_width_cm",
            ],
        )

        df["product_volume_cm3"] = df.get("product_length_cm", 0) * df.get("product_height_cm", 0) * df.get("product_width_cm", 0)
        df["product_density_g_per_cm3"] = np.where(df["product_volume_cm3"].ne(0), df["product_weight_g"] / df["product_volume_cm3"], np.nan)
        df["is_lightweight"] = df["product_weight_g"].le(1000)

        translation = self._copy_with_text_columns(category_translation)
        df = df.merge(translation, on="product_category_name", how="left")
        return df

    def _build_seller_features(self, sellers: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
        """Build seller dimension features and fulfillment metrics."""

        df = self._copy_with_text_columns(sellers)
        seller_summary = order_items.groupby("seller_id", as_index=False).agg(
            seller_items=("order_id", "count"),
            seller_unique_orders=("order_id", "nunique"),
            seller_revenue=("price", "sum"),
            seller_freight=("freight_value", "sum"),
        )
        df = df.merge(seller_summary, on="seller_id", how="left")
        return df

    def _compute_profit_margin(self, dataframe: pd.DataFrame) -> pd.Series:
        """Compute profit margin when a cost column is available."""

        cost_columns = ["unit_cost", "product_cost", "estimated_cost", "cost_price"]
        cost_column = next((column for column in cost_columns if column in dataframe.columns), None)
        if cost_column is None:
            return pd.Series(np.nan, index=dataframe.index, dtype="float64")

        revenue = dataframe["price"].fillna(0)
        cost = dataframe[cost_column].fillna(0)
        return np.where(revenue.ne(0), (revenue - cost) / revenue, np.nan)

    def _days_between(self, dataframe: pd.DataFrame, start_column: str, end_column: str) -> pd.Series:
        """Return elapsed days between two datetime columns."""

        if start_column not in dataframe.columns or end_column not in dataframe.columns:
            return pd.Series(np.nan, index=dataframe.index, dtype="float64")
        return (dataframe[end_column] - dataframe[start_column]).dt.total_seconds().div(86400)

    def _hours_between(self, dataframe: pd.DataFrame, start_column: str, end_column: str) -> pd.Series:
        """Return elapsed hours between two datetime columns."""

        if start_column not in dataframe.columns or end_column not in dataframe.columns:
            return pd.Series(np.nan, index=dataframe.index, dtype="float64")
        return (dataframe[end_column] - dataframe[start_column]).dt.total_seconds().div(3600)

    def _copy_with_datetime_columns(self, dataframe: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        """Return a copy with selected columns parsed as datetimes."""

        df = dataframe.copy()
        for column in columns:
            if column in df.columns:
                df[column] = pd.to_datetime(df[column], errors="coerce")
        return df

    def _copy_with_text_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with normalized text column names."""

        df = dataframe.copy()
        df.columns = [column.strip().lower() for column in df.columns]
        return df

    def _rename_product_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Standardize product column names from the raw Olist schema."""

        return dataframe.rename(
            columns={
                "product_name_lenght": "product_name_length",
                "product_description_lenght": "product_description_length",
            }
        )

    def _coerce_numeric_columns(self, dataframe: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        """Coerce selected columns to numeric values when possible."""

        df = dataframe.copy()
        for column in columns:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")
        return df

    def _validate_input_tables(self, cleaned: dict[str, pd.DataFrame]) -> None:
        """Ensure the cleaned data dictionary includes every required table."""

        required = {
            "orders",
            "order_items",
            "customers",
            "products",
            "sellers",
            "order_payments",
            "order_reviews",
            "category_translation",
        }
        missing = sorted(required.difference(cleaned))
        if missing:
            raise FeatureEngineeringError(f"Missing required cleaned tables: {', '.join(missing)}")

    def _validated_output_dir(self) -> Path:
        """Resolve the directory used to persist engineered features."""

        return self.output_dir or self.processed_dir
