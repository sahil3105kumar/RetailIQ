"""Raw data loading and cleaning for the RetailIQ ETL pipeline.

This module implements a production-oriented preprocessing layer for the Olist
e-commerce dataset. It is designed to be reusable, configurable, and safe for
batch execution in local or scheduled environments.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .utils import (
    coerce_numeric_columns,
    ensure_directory,
    fill_categorical_missing,
    fill_numeric_missing,
    parse_datetime_columns,
    read_csv_file,
    safe_mode,
    setup_logging,
    standardize_column_names,
    write_csv_file,
)


class ETLConfigurationError(ValueError):
    """Raised when the ETL configuration is invalid."""


class DatasetLoadError(RuntimeError):
    """Raised when a dataset cannot be loaded from disk."""


class DatasetValidationError(RuntimeError):
    """Raised when a dataset is missing required structure or values."""


@dataclass(slots=True, frozen=True)
class SourceTableSpec:
    """Metadata describing one raw source file.

    Attributes:
        name: Logical dataset name used throughout the pipeline.
        filename: Raw CSV filename relative to the raw data directory.
        required_columns: Columns that must exist after normalization.
        dedupe_subset: Optional subset used for duplicate removal.
    """

    name: str
    filename: str
    required_columns: tuple[str, ...]
    dedupe_subset: tuple[str, ...] | None = None


@dataclass(slots=True)
class ETLConfig:
    """Configuration for the RetailIQ preprocessing workflow."""

    project_root: Path
    raw_dir: Path | None = None
    processed_dir: Path | None = None
    log_file: Path | None = None
    overwrite: bool = True
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        """Populate default paths and validate the configuration."""

        if self.raw_dir is None:
            self.raw_dir = self.project_root / "data" / "raw"
        if self.processed_dir is None:
            self.processed_dir = self.project_root / "data" / "processed"
        if self.log_file is None:
            self.log_file = self.project_root / "reports" / "etl.log"

        for path in (self.project_root, self.raw_dir, self.processed_dir, self.log_file.parent):
            if not isinstance(path, Path):
                raise ETLConfigurationError("All configured paths must be pathlib.Path instances.")


@dataclass(slots=True)
class RetailIQPreprocessor:
    """Load, validate, clean, and persist the Olist source tables."""

    config: ETLConfig
    logger: logging.Logger = field(init=False)

    def __post_init__(self) -> None:
        self.logger = setup_logging(self.config.log_file)

    @property
    def source_tables(self) -> tuple[SourceTableSpec, ...]:
        """Return the expected source files and schema hints."""

        return (
            SourceTableSpec("customers", "olist_customers_dataset.csv", ("customer_id",), ("customer_id",)),
            SourceTableSpec("geolocation", "olist_geolocation_dataset.csv", ("geolocation_zip_code_prefix",)),
            SourceTableSpec("order_items", "olist_order_items_dataset.csv", ("order_id", "order_item_id"), ("order_id", "order_item_id")),
            SourceTableSpec("order_payments", "olist_order_payments_dataset.csv", ("order_id", "payment_sequential"), ("order_id", "payment_sequential")),
            SourceTableSpec("order_reviews", "olist_order_reviews_dataset.csv", ("review_id", "order_id"), ("review_id",)),
            SourceTableSpec("orders", "olist_orders_dataset.csv", ("order_id", "customer_id"), ("order_id",)),
            SourceTableSpec("products", "olist_products_dataset.csv", ("product_id",), ("product_id",)),
            SourceTableSpec("sellers", "olist_sellers_dataset.csv", ("seller_id",), ("seller_id",)),
            SourceTableSpec("category_translation", "product_category_name_translation.csv", ("product_category_name",)),
        )

    def run(self) -> dict[str, pd.DataFrame]:
        """Execute the complete preprocessing workflow.

        Returns:
            A dictionary of cleaned pandas DataFrames keyed by logical table name.
        """

        raw_datasets = self.load_raw_datasets()
        cleaned_datasets = self.clean_all(raw_datasets)
        self.save_cleaned_datasets(cleaned_datasets)
        return cleaned_datasets

    def load_raw_datasets(self) -> dict[str, pd.DataFrame]:
        """Load all source tables from the configured raw data directory."""

        datasets: dict[str, pd.DataFrame] = {}
        load_failures: list[str] = []

        for spec in self.source_tables:
            try:
                datasets[spec.name] = self._load_single_table(spec)
            except (FileNotFoundError, pd.errors.ParserError, UnicodeDecodeError, OSError) as exc:
                load_failures.append(f"{spec.filename}: {exc}")
                self.logger.exception("Failed to load source table %s", spec.name)

        if load_failures:
            raise DatasetLoadError(
                "One or more source tables could not be loaded. "
                + " | ".join(load_failures)
            )

        return datasets

    def clean_all(self, datasets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        """Apply dataset-specific cleaning rules to every loaded table."""

        self._validate_expected_tables(datasets)

        return {
            "customers": self.clean_customers(datasets["customers"]),
            "geolocation": self.clean_geolocation(datasets["geolocation"]),
            "order_items": self.clean_order_items(datasets["order_items"]),
            "order_payments": self.clean_order_payments(datasets["order_payments"]),
            "order_reviews": self.clean_order_reviews(datasets["order_reviews"]),
            "orders": self.clean_orders(datasets["orders"]),
            "products": self.clean_products(datasets["products"]),
            "sellers": self.clean_sellers(datasets["sellers"]),
            "category_translation": self.clean_category_translation(datasets["category_translation"]),
        }

    def save_cleaned_datasets(self, datasets: dict[str, pd.DataFrame]) -> None:
        """Persist cleaned datasets to the processed data directory."""

        processed_dir = self._validated_processed_dir()
        ensure_directory(processed_dir)

        for table_name, dataframe in datasets.items():
            output_path = processed_dir / f"{table_name}_clean.csv"
            if output_path.exists() and not self.config.overwrite:
                self.logger.info("Skipping existing file: %s", output_path)
                continue
            try:
                write_csv_file(dataframe, output_path)
                self.logger.info("Saved %s to %s", table_name, output_path)
            except OSError as exc:
                self.logger.exception("Failed to persist cleaned dataset %s", table_name)
                raise DatasetLoadError(f"Failed to save cleaned dataset '{table_name}' to {output_path}: {exc}") from exc

    def clean_customers(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean customer master data."""

        df = dataframe.copy()
        df = self._standardize_columns(df)
        df = self._ensure_columns(df, ["customer_id"])
        df = self._drop_duplicates(df, subset=("customer_id",))
        df = fill_categorical_missing(df, ["customer_city", "customer_state"], default="Unknown")
        df = self._normalize_zip_prefix(df, "customer_zip_code_prefix")
        return df.reset_index(drop=True)

    def clean_geolocation(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean and aggregate noisy geolocation records."""

        df = dataframe.copy()
        df = self._standardize_columns(df)
        df = self._ensure_columns(df, ["geolocation_zip_code_prefix"])
        df = coerce_numeric_columns(df, ["geolocation_lat", "geolocation_lng"])
        df = fill_categorical_missing(df, ["geolocation_city", "geolocation_state"], default="Unknown")
        df = self._normalize_zip_prefix(df, "geolocation_zip_code_prefix")
        df = self._drop_duplicates(df)

        aggregated = (
            df.groupby("geolocation_zip_code_prefix", as_index=False)
            .agg(
                geolocation_lat=("geolocation_lat", "mean"),
                geolocation_lng=("geolocation_lng", "mean"),
                geolocation_city=("geolocation_city", lambda series: safe_mode(series, default="Unknown")),
                geolocation_state=("geolocation_state", lambda series: safe_mode(series, default="Unknown")),
            )
            .reset_index(drop=True)
        )
        return aggregated

    def clean_order_items(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean the order-item fact table."""

        df = dataframe.copy()
        df = self._standardize_columns(df)
        df = self._ensure_columns(df, ["order_id", "order_item_id", "product_id", "seller_id"])
        df = coerce_numeric_columns(df, ["order_item_id", "price", "freight_value"])
        df = parse_datetime_columns(df, ["shipping_limit_date"])
        df = fill_numeric_missing(df, ["order_item_id", "price", "freight_value"])
        df = df.dropna(subset=["order_id", "product_id", "seller_id"])
        df = self._drop_duplicates(df, subset=("order_id", "order_item_id"))
        df["order_item_id"] = df["order_item_id"].round().astype("int64")
        return df.reset_index(drop=True)

    def clean_order_payments(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean the order-payment fact table."""

        df = dataframe.copy()
        df = self._standardize_columns(df)
        df = self._ensure_columns(df, ["order_id", "payment_sequential"])
        df = coerce_numeric_columns(df, ["payment_sequential", "payment_installments", "payment_value"])
        df = fill_numeric_missing(df, ["payment_sequential", "payment_installments", "payment_value"])
        df = fill_categorical_missing(df, ["payment_type"], default="Unknown")
        df = df.dropna(subset=["order_id"])
        df = self._drop_duplicates(df, subset=("order_id", "payment_sequential"))
        df["payment_sequential"] = df["payment_sequential"].round().astype("int64")
        df["payment_installments"] = df["payment_installments"].round().astype("int64")
        return df.reset_index(drop=True)

    def clean_order_reviews(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean the review fact table."""

        df = dataframe.copy()
        df = self._standardize_columns(df)
        df = self._ensure_columns(df, ["review_id", "order_id"])
        df = coerce_numeric_columns(df, ["review_score"])
        df = parse_datetime_columns(df, ["review_creation_date", "review_answer_timestamp"])
        df = fill_numeric_missing(df, ["review_score"])
        df = fill_categorical_missing(df, ["review_comment_title", "review_comment_message"], default="")
        df = df.dropna(subset=["order_id"])
        df = self._drop_duplicates(df, subset=("review_id",))
        df["review_score"] = df["review_score"].round().astype("int64")
        return df.reset_index(drop=True)

    def clean_orders(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean the order header table."""

        df = dataframe.copy()
        df = self._standardize_columns(df)
        df = self._ensure_columns(df, ["order_id", "customer_id"])
        df = parse_datetime_columns(
            df,
            [
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
        )
        df = fill_categorical_missing(df, ["order_status"], default="unknown")
        df = df.dropna(subset=["order_id", "customer_id"])
        df = self._drop_duplicates(df, subset=("order_id",))
        return df.reset_index(drop=True)

    def clean_products(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean the product master table."""

        df = dataframe.copy()
        df = self._standardize_columns(df)
        df = df.rename(
            columns={
                "product_name_lenght": "product_name_length",
                "product_description_lenght": "product_description_length",
            }
        )
        df = self._ensure_columns(df, ["product_id"])

        numeric_columns = [
            "product_name_length",
            "product_description_length",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]
        df = coerce_numeric_columns(df, numeric_columns)
        df = fill_numeric_missing(df, numeric_columns)
        df = fill_categorical_missing(df, ["product_category_name"], default="unknown_category")
        df = self._drop_duplicates(df, subset=("product_id",))
        return df.reset_index(drop=True)

    def clean_sellers(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean seller master data."""

        df = dataframe.copy()
        df = self._standardize_columns(df)
        df = self._ensure_columns(df, ["seller_id"])
        df = fill_categorical_missing(df, ["seller_city", "seller_state"], default="Unknown")
        df = self._normalize_zip_prefix(df, "seller_zip_code_prefix")
        df = self._drop_duplicates(df, subset=("seller_id",))
        return df.reset_index(drop=True)

    def clean_category_translation(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Clean the category translation lookup table."""

        df = dataframe.copy()
        df = self._standardize_columns(df)
        df = self._ensure_columns(df, ["product_category_name"])
        df = fill_categorical_missing(df, ["product_category_name", "product_category_name_english"], default="Unknown")
        df = self._drop_duplicates(df, subset=("product_category_name",))
        return df.reset_index(drop=True)

    def _load_single_table(self, spec: SourceTableSpec) -> pd.DataFrame:
        """Load and normalize a single raw CSV source table."""

        raw_dir = self._validated_raw_dir()
        file_path = raw_dir / spec.filename
        if not file_path.exists():
            raise FileNotFoundError(f"Missing required raw file: {file_path}")

        try:
            dataframe = read_csv_file(file_path, encoding=self.config.encoding)
        except Exception as exc:  # pragma: no cover - defensive re-wrap for batch ETL
            raise DatasetLoadError(f"Failed to read {spec.filename}: {exc}") from exc

        dataframe.columns = standardize_column_names(dataframe.columns)
        self._ensure_columns(dataframe, list(spec.required_columns), table_name=spec.name)
        self.logger.info("Loaded %s from %s with %s rows and %s columns", spec.name, file_path, len(dataframe), len(dataframe.columns))
        return dataframe

    def _validate_expected_tables(self, datasets: dict[str, pd.DataFrame]) -> None:
        """Ensure every expected dataset is present before cleaning."""

        missing_tables = [spec.name for spec in self.source_tables if spec.name not in datasets]
        if missing_tables:
            raise DatasetValidationError(f"Missing expected tables: {', '.join(missing_tables)}")

    def _standardize_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Normalize all column names to snake_case."""

        df = dataframe.copy()
        df.columns = standardize_column_names(df.columns)
        return df

    def _ensure_columns(self, dataframe: pd.DataFrame, required_columns: Iterable[str], table_name: str | None = None) -> pd.DataFrame:
        """Raise a validation error when required columns are absent."""

        missing_columns = [column for column in required_columns if column not in dataframe.columns]
        if missing_columns:
            label = f" in table '{table_name}'" if table_name else ""
            raise DatasetValidationError(f"Missing required columns{label}: {', '.join(missing_columns)}")
        return dataframe

    def _drop_duplicates(self, dataframe: pd.DataFrame, subset: tuple[str, ...] | None = None) -> pd.DataFrame:
        """Remove duplicate records and preserve the first occurrence."""

        return dataframe.drop_duplicates(subset=list(subset) if subset else None, keep="first")

    def _normalize_zip_prefix(self, dataframe: pd.DataFrame, column_name: str) -> pd.DataFrame:
        """Normalize zip-code prefix columns to cleaned string values."""

        df = dataframe.copy()
        if column_name in df.columns:
            df[column_name] = (
                df[column_name]
                .astype("string")
                .str.replace(r"\.0$", "", regex=True)
                .fillna("00000")
            )
        return df

    def _validated_raw_dir(self) -> Path:
        """Return the configured raw directory or raise a configuration error."""

        raw_dir = self.config.raw_dir
        if raw_dir is None:
            raise ETLConfigurationError("raw_dir must be configured before running the pipeline.")
        return raw_dir

    def _validated_processed_dir(self) -> Path:
        """Return the configured processed directory or raise a configuration error."""

        processed_dir = self.config.processed_dir
        if processed_dir is None:
            raise ETLConfigurationError("processed_dir must be configured before running the pipeline.")
        return processed_dir
