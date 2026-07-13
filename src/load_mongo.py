from __future__ import annotations

import argparse
from typing import Any

from pymongo import ASCENDING, MongoClient, ReplaceOne

from config import load_settings, repo_path
from spark_session import build_spark
from datetime import date, datetime

def normalise_document(row: dict[str, Any]) -> dict[str, Any]:
    cleaned = {}
    for key, value in row.items():
        if value is None:
            continue
        if isinstance(value, (date, datetime)):
            cleaned[key] = value.isoformat()
        else:
            cleaned[key] = value
    return cleaned


def iter_documents(parquet_dir: str, batch_size: int = 1000):
    spark = build_spark("crime-deprivation-mongo-load")
    try:
        rows = spark.read.parquet(parquet_dir).toLocalIterator()
        batch = []
        for row in rows:
            batch.append(normalise_document(row.asDict(recursive=True)))
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
    finally:
        spark.stop()


def load_to_mongo(parquet_dir: str, mongo_uri: str, database: str, collection: str) -> int:
    client = MongoClient(mongo_uri)
    coll = client[database][collection]

    total = 0
    for batch in iter_documents(parquet_dir):
        operations = [
            ReplaceOne({"lsoa_code": doc["lsoa_code"]}, doc, upsert=True)
            for doc in batch
            if doc.get("lsoa_code")
        ]
        if operations:
            result = coll.bulk_write(operations, ordered=False)
            total += result.upserted_count + result.modified_count

    coll.create_index([("lsoa_code", ASCENDING)], unique=True)
    coll.create_index([("imd_decile", ASCENDING)])
    coll.create_index([("hotspot", ASCENDING)])
    coll.create_index([("crime_rate_per_1000", ASCENDING)])
    client.close()
    return total


def parse_args() -> argparse.Namespace:
    settings = load_settings()
    parser = argparse.ArgumentParser(description="Load Spark Parquet output into MongoDB.")
    parser.add_argument("--parquet-dir", default=settings["processed_dir"])
    parser.add_argument("--mongo-uri", default=settings["mongo_uri"])
    parser.add_argument("--database", default=settings["mongo_db"])
    parser.add_argument("--collection", default=settings["mongo_collection"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    changed = load_to_mongo(
        str(repo_path(args.parquet_dir)),
        args.mongo_uri,
        args.database,
        args.collection,
    )
    print(f"MongoDB load complete: {changed} documents inserted or updated.")


if __name__ == "__main__":
    main()
