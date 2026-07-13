from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pymongo import MongoClient

from config import load_settings, repo_path


# Same charts as src/visualise.py, but sourced from live MongoDB aggregation
# queries instead of the local Parquet file. This is the version to reference
# on the "how we queried the data" slide, the queries below are the actual
# query examples, not illustrative pseudocode.


def save_decile_chart_from_mongo(coll, figures_dir: Path) -> Path:
    pipeline = [
        {"$match": {"imd_decile": {"$ne": None}, "crime_rate_per_1000": {"$ne": None}}},
        {"$group": {"_id": "$imd_decile", "avg_rate": {"$avg": "$crime_rate_per_1000"}}},
        {"$sort": {"_id": 1}},
    ]
    rows = list(coll.aggregate(pipeline))
    df = pd.DataFrame(rows).rename(columns={"_id": "imd_decile"})
    # 🔍 DEBUG — THIS MUST RUN BEFORE THE BARPLOT
    print("DEBUG DF COLUMNS:", df.columns)
    print(df.head())
   


    output = figures_dir / "average_crime_rate_by_iod2025_decile_mongo.png"
    plt.figure(figsize=(9, 5))
    sns.barplot(data=df, x="imd_decile", y="avg_rate", color="#4C78A8")
    plt.title("Average crime rate by IoD 2025 decile (from MongoDB aggregation)")
    plt.xlabel("IoD 2025 decile, 1 is most deprived")
    plt.ylabel("Average crimes per 1,000 residents")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def save_category_breakdown_from_mongo(coll, figures_dir: Path) -> Path:
    pipeline = [
        {"$project": {"categories": {"$objectToArray": "$crimes_by_category"}}},
        {"$unwind": "$categories"},
        {"$group": {"_id": "$categories.k", "total": {"$sum": "$categories.v"}}},
        {"$sort": {"total": -1}},
        {"$limit": 10},
    ]
    rows = list(coll.aggregate(pipeline))
    df = pd.DataFrame(rows).rename(columns={"_id": "category"}).sort_values("total")
    labels = [name.replace("_", " ").title() for name in df["category"]]

    output = figures_dir / "national_crime_category_breakdown_mongo.png"
    plt.figure(figsize=(9, 6))
    plt.barh(labels, df["total"], color="#4C78A8")
    plt.title("Top 10 crime categories (from MongoDB aggregation)")
    plt.xlabel("Total recorded crimes")
    for i, value in enumerate(df["total"]):
        plt.text(value, i, f" {value:,.0f}", va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def save_monthly_trend_from_mongo(trend_coll, figures_dir: Path) -> Path:
    rows = list(trend_coll.find({}, {"_id": 0}).sort("month", 1))
    df = pd.DataFrame(rows)
    df["month"] = pd.to_datetime(df["month"])

    output = figures_dir / "monthly_crime_trend_mongo.png"
    plt.figure(figsize=(11, 5.5))
    plt.plot(df["month"], df["crimes"], marker="o", color="#4C78A8", linewidth=2)
    plt.title("National recorded crime by month (from MongoDB), June 2023 to May 2026")
    plt.xlabel("Month")
    plt.ylabel("Recorded crimes (England, street-level)")
    plt.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def build_visuals_from_mongo(mongo_uri: str, database: str, collection: str, trend_collection: str, figures_dir: Path) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    client = MongoClient(mongo_uri)
    coll = client[database][collection]
    trend_coll = client[database][trend_collection]

    outputs = [
        save_decile_chart_from_mongo(coll, figures_dir),
        save_category_breakdown_from_mongo(coll, figures_dir),
    ]
    if trend_coll.estimated_document_count() > 0:
        outputs.append(save_monthly_trend_from_mongo(trend_coll, figures_dir))
    else:
        print(f"Skipped monthly trend chart: '{trend_collection}' is empty, run load_monthly_trend_mongo.py first.")

    client.close()
    return outputs


def parse_args() -> argparse.Namespace:
    settings = load_settings()
    parser = argparse.ArgumentParser(description="Rebuild presentation charts from live MongoDB queries.")
    parser.add_argument("--mongo-uri", default=settings["mongo_uri"])
    parser.add_argument("--database", default=settings["mongo_db"])
    parser.add_argument("--collection", default=settings["mongo_collection"])
    parser.add_argument("--trend-collection", default="monthly_crime_trend")
    parser.add_argument("--figures-dir", default=settings["figures_dir"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = build_visuals_from_mongo(
        args.mongo_uri,
        args.database,
        args.collection,
        args.trend_collection,
        repo_path(args.figures_dir),
    )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
