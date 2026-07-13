from __future__ import annotations

from pyspark.sql import SparkSession


def build_spark(app_name: str = "crime-deprivation-pipeline") -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "200")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .getOrCreate()
    )
