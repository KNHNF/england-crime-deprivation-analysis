from __future__ import annotations

import argparse
import csv
from pathlib import Path

from pymongo import ASCENDING, MongoClient

from config import load_settings, repo_path


def load_monthly_trend(csv_path: Path, mongo_uri: str, database: str, collection: str) -> int:
    client = MongoClient(mongo_uri)
    coll = client[database][collection]

    documents = []
    with open(csv_path, "r", encoding="utf-8") as handle:
        for month, crimes in csv.reader(handle):
            documents.append({"month": month, "crimes": int(crimes)})

    coll.delete_many({})  # small collection, full replace is simpler than upsert here
    coll.insert_many(documents)
    coll.create_index([("month", ASCENDING)], unique=True)
    client.close()
    return len(documents)


def parse_args() -> argparse.Namespace:
    settings = load_settings()
    parser = argparse.ArgumentParser(description="Load the monthly national crime trend CSV into MongoDB.")
    parser.add_argument("--csv-path", default="data/processed/monthly_crime_counts.csv")
    parser.add_argument("--mongo-uri", default=settings["mongo_uri"])
    parser.add_argument("--database", default=settings["mongo_db"])
    parser.add_argument("--collection", default="monthly_crime_trend")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = load_monthly_trend(
        repo_path(args.csv_path),
        args.mongo_uri,
        args.database,
        args.collection,
    )
    print(f"Loaded {count} monthly records into '{args.collection}'.")


if __name__ == "__main__":
    main()
