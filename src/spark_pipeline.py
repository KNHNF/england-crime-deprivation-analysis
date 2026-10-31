from __future__ import annotations

import argparse
import json
from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from config import load_settings, repo_path
from spark_session import build_spark


IMD_COLUMNS = {
    "LSOA code (2021)": "lsoa_code",
    "LSOA name (2021)": "lsoa_name",
    "Local Authority District code (2024)": "lad_code",
    "Local Authority District name (2024)": "lad_name",
    "Index of Multiple Deprivation (IMD) Score": "imd_score",
    "Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)": "imd_rank",
    "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)": "imd_decile",
    "Income Score (rate)": "income_score",
    "Income Decile (where 1 is most deprived 10% of LSOAs)": "income_decile",
    "Employment Score (rate)": "employment_score",
    "Employment Decile (where 1 is most deprived 10% of LSOAs)": "employment_decile",
    "Education, Skills and Training Score": "education_score",
    "Education, Skills and Training Decile (where 1 is most deprived 10% of LSOAs)": "education_decile",
    "Health Deprivation and Disability Score": "health_score",
    "Health Deprivation and Disability Decile (where 1 is most deprived 10% of LSOAs)": "health_decile",
    "Crime Score": "iod_crime_score",
    "Crime Decile (where 1 is most deprived 10% of LSOAs)": "iod_crime_decile",
    "Barriers to Housing and Services Score": "housing_score",
    "Barriers to Housing and Services Decile (where 1 is most deprived 10% of LSOAs)": "housing_decile",
    "Living Environment Score": "living_environment_score",
    "Living Environment Decile (where 1 is most deprived 10% of LSOAs)": "living_environment_decile",
    "Total population: mid 2022": "population",
}


def read_police_data(spark, police_dir: Path) -> DataFrame:
    # police.uk exports two file types per force per month: *-street.csv (crime
    # incidents, has Crime type and location) and *-outcomes.csv (a separate,
    # incompatible schema tracking case outcomes only, no Crime type column).
    # Reading both together corrupts columns via positional CSV alignment, so
    # only street files are loaded here.
    if not police_dir.is_dir():
        raise FileNotFoundError(f"Police data directory not found: {police_dir}")
    if next(police_dir.rglob("*-street.csv"), None) is None:
        raise FileNotFoundError(
            f"No *-street.csv files found under {police_dir}. "
            "Download the police.uk archive with crime data included (see data/README.md)."
        )
    return (
        spark.read.option("header", True)
        .option("inferSchema", False)
        .option("recursiveFileLookup", True)
        .option("pathGlobFilter", "*-street.csv")
        .csv(str(police_dir))
    )


def clean_police_data(crimes: DataFrame) -> DataFrame:
    required = [
        "Month",
        "Crime type",
        "LSOA code",
        "Longitude",
        "Latitude",
        "Reported by",
        "Falls within",
        "Last outcome category",
    ]
    missing = [column for column in required if column not in crimes.columns]
    if missing:
        raise ValueError(f"Police CSVs are missing required columns: {missing}")

    return (
        crimes.select(
            F.to_date(F.concat(F.col("Month"), F.lit("-01"))).alias("month"),
            F.trim(F.col("Crime type")).alias("crime_type_raw"),
            F.trim(F.col("LSOA code")).alias("lsoa_code"),
            F.trim(F.col("LSOA name")).alias("police_lsoa_name"),
            F.col("Longitude").cast("double").alias("longitude"),
            F.col("Latitude").cast("double").alias("latitude"),
            F.trim(F.col("Reported by")).alias("reported_by"),
            F.trim(F.col("Falls within")).alias("falls_within"),
            F.trim(F.col("Last outcome category")).alias("last_outcome_category"),
        )
        .where(
            F.col("lsoa_code").isNotNull()
            & (F.col("lsoa_code") != "")
            # England-only scope: the IoD/IMD deprivation file covers English LSOAs
            # (E01...) only. Welsh forces (Dyfed-Powys, Gwent, North Wales, South
            # Wales) report against Welsh LSOAs (W01...), which cannot join to an
            # England-only deprivation index under any circumstance, that is a
            # coverage mismatch, not a data quality issue. Excluding non-English
            # LSOA codes here rather than letting them show up as false "unmatched"
            # rows downstream.
            & F.col("lsoa_code").startswith("E01")
        )
        .withColumn("crime_category", F.regexp_replace(F.lower(F.col("crime_type_raw")), r"[^a-z0-9]+", "_"))
        .withColumn("crime_category", F.regexp_replace(F.col("crime_category"), r"_$", ""))
        .withColumn(
            "outcome_category",
            F.when(
                F.col("last_outcome_category").isNull() | (F.col("last_outcome_category") == ""),
                F.lit("unknown"),
            ).otherwise(F.regexp_replace(F.lower(F.col("last_outcome_category")), r"[^a-z0-9]+", "_")),
        )
        .withColumn("outcome_category", F.regexp_replace(F.col("outcome_category"), r"_$", ""))
    )


def read_imd(spark, imd_file: Path) -> DataFrame:
    imd = spark.read.option("header", True).option("inferSchema", True).csv(str(imd_file))

    selected = []
    for raw_name, clean_name in IMD_COLUMNS.items():
        if raw_name not in imd.columns:
            raise ValueError(f"IoD CSV is missing required column: {raw_name}")
        selected.append(F.col(raw_name).alias(clean_name))

    return imd.select(*selected)


def aggregate_lsoa(crimes: DataFrame, imd: DataFrame) -> DataFrame:
    category_counts = (
        crimes.groupBy("lsoa_code")
        .pivot("crime_category")
        .count()
        .na.fill(0)
    )
    category_columns = [column for column in category_counts.columns if column != "lsoa_code"]

    outcome_counts = (
        crimes.groupBy("lsoa_code")
        .pivot("outcome_category")
        .count()
        .na.fill(0)
    )
    outcome_columns = [column for column in outcome_counts.columns if column != "lsoa_code"]

    totals = crimes.groupBy("lsoa_code").agg(
        F.count("*").alias("total_crimes"),
        F.min("month").alias("first_month"),
        F.max("month").alias("last_month"),
        F.avg("longitude").alias("avg_longitude"),
        F.avg("latitude").alias("avg_latitude"),
        F.count("longitude").alias("crimes_with_coordinates"),
        F.collect_set("reported_by").alias("reported_by_forces"),
        F.collect_set("falls_within").alias("falls_within_forces"),
    )

    category_struct = F.create_map(
        *[
            item
            for category in sorted(category_columns)
            for item in (F.lit(category), F.col(category).cast("long"))
        ]
    )
    outcome_struct = F.create_map(
        *[
            item
            for outcome in sorted(outcome_columns)
            for item in (F.lit(outcome), F.col(outcome).cast("long"))
        ]
    )

    result = (
        totals.join(category_counts, "lsoa_code", "left")
        .join(outcome_counts, "lsoa_code", "left")
        .join(imd, "lsoa_code", "left")
        .withColumn(
            "crime_rate_per_1000",
            F.when(F.col("population") > 0, F.col("total_crimes") / F.col("population") * 1000),
        )
        .withColumn("crimes_by_category", category_struct)
        .withColumn("outcomes_by_category", outcome_struct)
        .withColumn("hotspot", F.lit(None).cast("boolean"))
    )

    return result.select(
        "lsoa_code",
        "lsoa_name",
        "lad_code",
        "lad_name",
        "total_crimes",
        "crimes_by_category",
        "outcomes_by_category",
        "first_month",
        "last_month",
        "avg_longitude",
        "avg_latitude",
        "crimes_with_coordinates",
        "reported_by_forces",
        "falls_within_forces",
        "imd_score",
        "imd_rank",
        "imd_decile",
        "income_score",
        "income_decile",
        "employment_score",
        "employment_decile",
        "education_score",
        "education_decile",
        "health_score",
        "health_decile",
        "iod_crime_score",
        "iod_crime_decile",
        "housing_score",
        "housing_decile",
        "living_environment_score",
        "living_environment_decile",
        "population",
        "crime_rate_per_1000",
        "hotspot",
    )


def write_summary(output_dir: Path, stats: dict[str, int | str | None]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "_run_summary.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")


def run_pipeline(police_dir: Path, imd_file: Path, output_dir: Path) -> dict[str, int | str | None]:
    spark = build_spark()
    try:
        crimes_raw = read_police_data(spark, police_dir)
        crimes = clean_police_data(crimes_raw).cache()
        imd = read_imd(spark, imd_file)
        lsoa_output = aggregate_lsoa(crimes, imd).cache()

        lsoa_output.write.mode("overwrite").parquet(str(output_dir))

        stats = {
            "raw_crime_rows": crimes_raw.count(),
            "clean_crime_rows": crimes.count(),
            "output_lsoa_rows": lsoa_output.count(),
            "unmatched_lsoa_rows": lsoa_output.where(F.col("imd_score").isNull()).count(),
            "first_month": crimes.agg(F.min("month")).first()[0].isoformat(),
            "last_month": crimes.agg(F.max("month")).first()[0].isoformat(),
            "output_dir": str(output_dir),
        }
        write_summary(output_dir, stats)
        return stats
    finally:
        spark.stop()


def parse_args() -> argparse.Namespace:
    settings = load_settings()
    parser = argparse.ArgumentParser(description="Build LSOA-level crime and deprivation dataset.")
    parser.add_argument("--police-dir", default=settings["police_data_dir"])
    parser.add_argument("--imd-file", default=settings["imd_file"])
    parser.add_argument("--output-dir", default=settings["processed_dir"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = run_pipeline(
        repo_path(args.police_dir),
        repo_path(args.imd_file),
        repo_path(args.output_dir),
    )
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
