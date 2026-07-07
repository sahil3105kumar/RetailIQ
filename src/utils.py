"""Utility helpers for the RetailIQ analytics pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging for the RetailIQ project."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def ensure_directories(paths: Iterable[Path]) -> None:
    """Create directories when they do not already exist."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
