"""Shared helpers for the RetailIQ ETL pipeline.

The functions in this module keep filesystem, logging, and dataframe-level
utilities in one place so the preprocessing and feature engineering layers
stay focused on business logic.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable

import pandas as pd


LOGGER_NAME = "RetailIQ"


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not already exist."""

    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logging(log_file: Path | None = None, level: int = logging.INFO) -> logging.Logger:
    """Configure a reusable application logger."""

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file is not None:
        ensure_directory(log_file.parent)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def standardize_column_names(columns: Iterable[str]) -> list[str]:
    """Convert column names to lowercase snake_case."""

    cleaned_columns: list[str] = []
    for column in columns:
        standardized = column.strip().lower()
        standardized = re.sub(r"[^0-9a-zA-Z]+", "_", standardized)
        standardized = re.sub(r"_+", "_", standardized).strip("_")
        cleaned_columns.append(standardized)
    return cleaned_columns


def read_csv_file(path: Path, encoding: str = "utf-8") -> pd.DataFrame:
    """Read a CSV file with a consistent pandas configuration."""

    return pd.read_csv(path, encoding=encoding, low_memory=False)


def write_csv_file(df: pd.DataFrame, path: Path) -> None:
    """Persist a dataframe as a CSV file."""

    ensure_directory(path.parent)
    df.to_csv(path, index=False)


def safe_mode(series: pd.Series, default: str = "Unknown") -> str:
    """Return the most common non-null value from a series."""

    cleaned = series.dropna()
    if cleaned.empty:
        return default
    mode_values = cleaned.mode()
    if mode_values.empty:
        return default
    return str(mode_values.iloc[0])


def coerce_numeric_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Convert selected columns to numeric values where possible."""

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def parse_datetime_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Parse selected columns as datetimes."""

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def fill_numeric_missing(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Fill missing numeric values with the median of each column."""

    for column in columns:
        if column in df.columns:
            median_value = df[column].median()
            if pd.isna(median_value):
                median_value = 0
            df[column] = df[column].fillna(median_value)
    return df


def fill_categorical_missing(df: pd.DataFrame, columns: Iterable[str], default: str = "Unknown") -> pd.DataFrame:
    """Fill missing categorical values using a mode fallback."""

    for column in columns:
        if column in df.columns:
            fallback_value = safe_mode(df[column], default=default)
            df[column] = df[column].fillna(fallback_value).astype(str)
    return df
