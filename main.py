"""Command-line entrypoint for the RetailIQ ETL pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.feature_engineering import RetailIQFeatureEngineer
from src.preprocessing import ETLConfig, RetailIQPreprocessor


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Run the RetailIQ ETL pipeline.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Root directory of the RetailIQ project.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing processed files.",
    )
    return parser.parse_args()


def main() -> int:
    """Execute the preprocessing and feature engineering workflow."""

    args = parse_args()
    config = ETLConfig(project_root=args.project_root, overwrite=args.overwrite)

    preprocessor = RetailIQPreprocessor(config=config)
    cleaned_datasets = preprocessor.run()

    feature_engineer = RetailIQFeatureEngineer(
        project_root=config.project_root,
        processed_dir=config.processed_dir, #type: ignore
        log_file=config.log_file,
        overwrite=config.overwrite,
    )
    feature_bundle = feature_engineer.build_feature_bundle(cleaned_datasets)
    feature_engineer.save_feature_bundle(feature_bundle)

    preprocessor.logger.info("RetailIQ ETL pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
