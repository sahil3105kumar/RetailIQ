from pathlib import Path

import pandas as pd

from src.feature_engineering import add_time_features
from src.kpi import compute_kpis
from src.preprocessing import load_raw_data, preprocess_orders


def test_preprocess_orders_builds_order_value() -> None:
    datasets = {
        "orders": pd.DataFrame(
            {
                "order_id": ["o1", "o2"],
                "order_purchase_timestamp": ["2018-01-01", "2018-01-02"],
                "order_status": ["delivered", "shipped"],
            }
        ),
        "order_items": pd.DataFrame(
            {
                "order_id": ["o1", "o1", "o2"],
                "order_item_id": [1, 2, 1],
                "price": [10.0, 15.0, 20.0],
                "freight_value": [1.0, 1.5, 2.0],
            }
        ),
        "payments": pd.DataFrame(
            {
                "order_id": ["o1", "o2"],
                "payment_value": [27.5, 22.0],
            }
        ),
    }

    curated = preprocess_orders(datasets)

    assert "order_value" in curated.columns
    assert curated.loc[curated["order_id"] == "o1", "order_value"].iloc[0] == 27.5


def test_feature_and_kpi_outputs() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["o1", "o2"],
            "order_purchase_timestamp": ["2018-01-01", "2018-01-02"],
            "order_value": [27.5, 22.0],
            "total_payment": [27.5, 22.0],
        }
    )

    featured = add_time_features(frame)
    kpis = compute_kpis(featured)

    assert "order_month" in featured.columns
    assert kpis["total_orders"] == 2.0
    assert kpis["gross_revenue"] == 49.5
    assert kpis["payment_capture_rate"] == 1.0


def test_load_raw_data_missing_files(tmp_path: Path) -> None:
    loaded = load_raw_data(tmp_path)
    assert loaded == {}
