"""Runs the Spark pipeline on a tiny synthetic sample, fully offline.

The data below is invented for testing. It is not police.uk or IoD data.
"""
import csv
import json

import pandas as pd
import pytest

pytest.importorskip("pyspark")

import spark_pipeline  # noqa: E402

STREET_HEADER = [
    "Crime ID", "Month", "Reported by", "Falls within", "Longitude", "Latitude",
    "Location", "LSOA code", "LSOA name", "Crime type", "Last outcome category", "Context",
]


def street_row(month, lsoa, crime, outcome="", lon="-1.0", lat="51.0"):
    return ["", month, "Test Police", "Test Police", lon, lat, "On or near", lsoa, "x", crime, outcome, ""]


def write_police(police_dir):
    sub = police_dir / "2024-01"
    sub.mkdir(parents=True)
    rows = [
        street_row("2024-01", "E01000001", "Burglary", "Under investigation"),
        street_row("2024-01", "E01000001", "Burglary"),
        street_row("2024-02", "E01000001", "Violence and sexual offences"),
        street_row("2024-01", "E01000002", "Burglary"),
        street_row("2024-01", "E01000009", "Burglary"),  # not in IoD file
        street_row("2024-01", "W01000001", "Burglary"),  # Welsh, must be dropped
        street_row("2024-01", "", "Burglary"),  # no LSOA, must be dropped
    ]
    with open(sub / "2024-01-test-street.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(STREET_HEADER)
        w.writerows(rows)
    # Outcomes files have a different schema and must be ignored.
    with open(sub / "2024-01-test-outcomes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Crime ID", "Month", "Reported by", "Falls within", "Longitude", "Latitude",
                    "Location", "LSOA code", "LSOA name", "Outcome type"])
        w.writerow(["", "2024-01", "T", "T", "0", "0", "x", "E01000001", "x", "Something"])


def write_imd(path, extra_missing_column=None):
    cols = list(spark_pipeline.IMD_COLUMNS)
    if extra_missing_column:
        cols.remove(extra_missing_column)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for code, pop in (("E01000001", 1000), ("E01000002", 500), ("E01000003", 800)):
            row = []
            for c in cols:
                name = spark_pipeline.IMD_COLUMNS[c]
                if name == "lsoa_code":
                    row.append(code)
                elif name in ("lsoa_name", "lad_name"):
                    row.append("n")
                elif name == "lad_code":
                    row.append("E0900001")
                elif name == "population":
                    row.append(pop)
                else:
                    row.append(3)
            w.writerow(row)


def test_pipeline_on_tiny_sample(tmp_path):
    police, imd, out = tmp_path / "police", tmp_path / "imd.csv", tmp_path / "out"
    write_police(police)
    write_imd(imd)

    stats = spark_pipeline.run_pipeline(police, imd, out)

    assert stats["raw_crime_rows"] == 7  # outcomes file excluded
    assert stats["clean_crime_rows"] == 5  # Welsh and blank LSOA rows dropped
    assert stats["output_lsoa_rows"] == 3
    assert stats["unmatched_lsoa_rows"] == 1
    assert stats["first_month"] == "2024-01-01"
    assert stats["last_month"] == "2024-02-01"

    df = pd.read_parquet(out).set_index("lsoa_code")
    assert df.loc["E01000001", "total_crimes"] == 3
    assert df.loc["E01000001", "crime_rate_per_1000"] == pytest.approx(3.0)
    assert df.loc["E01000002", "crime_rate_per_1000"] == pytest.approx(2.0)
    assert pd.isna(df.loc["E01000009", "crime_rate_per_1000"])
    assert dict(df.loc["E01000001", "crimes_by_category"])["burglary"] == 2
    # LSOAs with no crimes at all are absent, not zero rows (documented limit).
    assert "E01000003" not in df.index
    assert json.loads((out / "_run_summary.json").read_text())["output_lsoa_rows"] == 3


def test_missing_imd_column_gives_clear_error(tmp_path):
    imd = tmp_path / "imd.csv"
    write_imd(imd, extra_missing_column="Total population: mid 2022")
    from spark_session import build_spark

    spark = build_spark("test")
    try:
        with pytest.raises(ValueError, match="Total population"):
            spark_pipeline.read_imd(spark, imd)
    finally:
        spark.stop()


def test_no_street_files_gives_clear_error(tmp_path):
    police = tmp_path / "empty"
    police.mkdir()
    imd = tmp_path / "imd.csv"
    write_imd(imd)
    with pytest.raises(FileNotFoundError, match="street.csv"):
        spark_pipeline.run_pipeline(police, imd, tmp_path / "out")


def test_missing_police_dir_gives_clear_error(tmp_path):
    imd = tmp_path / "imd.csv"
    write_imd(imd)
    with pytest.raises(FileNotFoundError, match="not found"):
        spark_pipeline.run_pipeline(tmp_path / "nope", imd, tmp_path / "out")
