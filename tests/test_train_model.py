"""Offline tests for the hotspot model code, using invented data."""
import numpy as np
import pandas as pd
import pytest

import train_model as tm


def fake_frame(n=80, seed=0, nan_column=None):
    rng = np.random.default_rng(seed)
    data = {c: rng.random(n) for c in tm.FEATURE_COLUMNS}
    data["lsoa_code"] = [f"E01{i:06d}" for i in range(n)]
    data["crime_rate_per_1000"] = data["imd_score"] * 100
    df = pd.DataFrame(data)
    if nan_column:
        df[nan_column] = np.nan
    return df


def test_hotspot_is_top_quartile():
    out, threshold = tm.add_hotspot_label(fake_frame())
    assert out["hotspot"].mean() == pytest.approx(0.25, abs=0.03)
    assert (out.loc[out["hotspot"], "crime_rate_per_1000"] >= threshold).all()


def test_null_rates_are_dropped():
    df = fake_frame()
    df.loc[:9, "crime_rate_per_1000"] = np.nan
    out, _ = tm.add_hotspot_label(df)
    assert len(out) == 70


def test_too_few_rows_gives_clear_error():
    with pytest.raises(ValueError, match="at least 8"):
        tm.add_hotspot_label(fake_frame(n=3))


def test_missing_columns_gives_clear_error(tmp_path):
    fake_frame().drop(columns=["population"]).to_parquet(tmp_path / "p.parquet")
    with pytest.raises(ValueError, match="population"):
        tm.load_training_data(tmp_path)


def test_all_empty_feature_keeps_importances_aligned(tmp_path):
    pytest.importorskip("pyarrow")
    fake_frame(nan_column="health_score").to_parquet(tmp_path / "p.parquet")
    res = tm.train_and_evaluate(tmp_path, tmp_path / "figs")
    assert set(res["feature_importance"]) == set(tm.FEATURE_COLUMNS)
