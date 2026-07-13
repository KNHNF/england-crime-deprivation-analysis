from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from config import load_settings, repo_path

# Force files whose LSOA codes are Welsh, not English, same exclusion the main
# Spark pipeline applies via the E01 filter in clean_police_data(). Kept as a
# name-based exclusion here (rather than reading and filtering every row) since
# this script only needs a row count per month, not per-row processing, and a
# full Spark read of the archive does not fit in constrained environments.
# This slightly undercounts England (a handful of genuinely English-LSOA rows
# inside Welsh force files are excluded too), a documented approximation, not
# an error, see docs/10_eda_and_build_log.md.
WELSH_FORCE_MARKERS = ("dyfed-powys", "gwent", "north-wales", "south-wales")


def count_monthly_crimes(police_dir: Path) -> pd.DataFrame:
    rows = []
    for month_dir in sorted(p for p in police_dir.iterdir() if p.is_dir()):
        total = 0
        for street_file in month_dir.glob("*-street.csv"):
            if any(marker in street_file.name for marker in WELSH_FORCE_MARKERS):
                continue
            with open(street_file, "r", encoding="utf-8", errors="replace") as handle:
                total += sum(1 for _ in handle) - 1  # minus header row
        rows.append({"month": month_dir.name, "crimes": total})
    return pd.DataFrame(rows)


def save_monthly_trend_chart(df: pd.DataFrame, figures_dir: Path) -> Path:
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"])
    output = figures_dir / "monthly_crime_trend.png"
    plt.figure(figsize=(11, 5.5))
    plt.plot(df["month"], df["crimes"], marker="o", color="#4C78A8", linewidth=2)
    plt.title("National recorded crime by month, England, June 2023 to May 2026")
    plt.xlabel("Month")
    plt.ylabel("Recorded crimes (England, street-level)")
    plt.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def parse_args() -> argparse.Namespace:
    settings = load_settings()
    parser = argparse.ArgumentParser(description="Build the national monthly crime trend chart and CSV.")
    parser.add_argument("--police-dir", default=settings["police_data_dir"])
    parser.add_argument("--figures-dir", default=settings["figures_dir"])
    parser.add_argument("--output-csv", default="data/processed/monthly_crime_counts.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = count_monthly_crimes(repo_path(args.police_dir))
    output_csv = repo_path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, header=False)
    chart_path = save_monthly_trend_chart(df, repo_path(args.figures_dir))
    print(f"Wrote {output_csv}")
    print(f"Wrote {chart_path}")


if __name__ == "__main__":
    main()
