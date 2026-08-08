from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import load_settings, repo_path
from train_model import FEATURE_COLUMNS

NEIGHBOUR_K = 5

# Same set used in visualise.py's Manchester-gap chart and docs/08's writeup.
GM_BOROUGHS = {
    "Oldham", "Bury", "Tameside", "Trafford", "Salford",
    "Rochdale", "Bolton", "Wigan", "Manchester", "Stockport",
}


def load_data(parquet_dir: Path) -> pd.DataFrame:
    data = pd.read_parquet(parquet_dir)
    required = set(FEATURE_COLUMNS + ["lad_name", "population", "crime_rate_per_1000"])
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Processed data is missing columns: {missing}")
    data = data.dropna(subset=["crime_rate_per_1000", "lad_name"]).copy()
    for col in FEATURE_COLUMNS:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    return data


def train_regressor(train_x: pd.DataFrame, train_y: pd.Series) -> Pipeline:
    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=300,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(train_x, train_y)
    return model


def save_borough_chart(borough_summary: pd.DataFrame, figures_dir: Path) -> Path:
    output = figures_dir / "gm_predicted_vs_actual_crime_rate.png"
    ordered = borough_summary.sort_values("predicted_crime_rate_per_1000")

    fig, ax = plt.subplots(figsize=(9, 6))
    y_pos = range(len(ordered))
    ax.barh(
        [p - 0.2 for p in y_pos],
        ordered["actual_crime_rate_per_1000"],
        height=0.4,
        color="#B5451B",
        label="Actual (reported)",
    )
    ax.barh(
        [p + 0.2 for p in y_pos],
        ordered["predicted_crime_rate_per_1000"],
        height=0.4,
        color="#4C78A8",
        label="Predicted (model estimate)",
    )
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(ordered.index)
    ax.set_xlabel("Crimes per 1,000 residents")
    ax.set_title(
        "Greater Manchester: reported vs model-estimated crime rate\n"
        "Estimate trained on the other 43 local authorities' deprivation features"
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)
    return output


def aggregate_to_local_authority(data: pd.DataFrame) -> pd.DataFrame:
    # Population-weighted mean for deprivation features (an LSOA of 500 people
    # shouldn't count the same as one of 5,000), population itself summed,
    # crime rate population-weighted too so it matches how the rest of the
    # deck reports local-authority figures (visualise.py's save_lad_ranking).
    def weighted(group: pd.DataFrame, col: str) -> float:
        weights = group["population"].fillna(0)
        if weights.sum() == 0:
            return float(group[col].mean())
        return float((group[col] * weights).sum() / weights.sum())

    rows = []
    for name, group in data.groupby("lad_name"):
        row = {"lad_name": name, "population": float(group["population"].sum())}
        for col in FEATURE_COLUMNS:
            if col == "population":
                continue
            row[col] = weighted(group, col)
        row["crime_rate_per_1000"] = weighted(group, "crime_rate_per_1000")
        row["n_lsoas"] = len(group)
        rows.append(row)
    return pd.DataFrame(rows).set_index("lad_name")


def nearest_neighbour_comparison(lad_data: pd.DataFrame, k: int = NEIGHBOUR_K) -> dict[str, object]:
    # Deliberately not the random forest: this is meant as a second,
    # independent check that doesn't ask anyone to trust a model's internals.
    # "Here are k real places with a similar deprivation profile, here's what
    # they actually report" is easier to defend in a viva than an R2 figure.
    non_gm = lad_data[~lad_data.index.isin(GM_BOROUGHS)]
    gm = lad_data[lad_data.index.isin(GM_BOROUGHS)]

    scaler = StandardScaler()
    non_gm_scaled = scaler.fit_transform(non_gm[FEATURE_COLUMNS])
    gm_scaled = scaler.transform(gm[FEATURE_COLUMNS])

    finder = NearestNeighbors(n_neighbors=k).fit(non_gm_scaled)
    distances, indices = finder.kneighbors(gm_scaled)

    borough_results = []
    for row_i, borough in enumerate(gm.index):
        neighbour_names = non_gm.index[indices[row_i]].tolist()
        neighbour_rates = non_gm.iloc[indices[row_i]]["crime_rate_per_1000"].tolist()
        borough_results.append(
            {
                "lad_name": borough,
                "actual_crime_rate_per_1000": float(gm.loc[borough, "crime_rate_per_1000"]),
                "imd_score": float(gm.loc[borough, "imd_score"]),
                "neighbours": [
                    {
                        "lad_name": n_name,
                        "distance": float(dist),
                        "imd_score": float(non_gm.loc[n_name, "imd_score"]),
                        "actual_crime_rate_per_1000": float(rate),
                    }
                    for n_name, dist, rate in zip(
                        neighbour_names, distances[row_i].tolist(), neighbour_rates
                    )
                ],
                "neighbour_mean_crime_rate_per_1000": float(np.mean(neighbour_rates)),
            }
        )
    return {"k": k, "boroughs": borough_results}


def save_neighbour_chart(neighbour_results: dict[str, object], figures_dir: Path) -> Path:
    output = figures_dir / "gm_nearest_neighbour_crime_rate.png"
    boroughs = neighbour_results["boroughs"]
    df = pd.DataFrame(boroughs).set_index("lad_name")
    df = df.sort_values("neighbour_mean_crime_rate_per_1000")

    fig, ax = plt.subplots(figsize=(9, 6))
    y_pos = range(len(df))
    ax.barh(
        [p - 0.2 for p in y_pos],
        df["actual_crime_rate_per_1000"],
        height=0.4,
        color="#B5451B",
        label="GM actual (reported)",
    )
    ax.barh(
        [p + 0.2 for p in y_pos],
        df["neighbour_mean_crime_rate_per_1000"],
        height=0.4,
        color="#788C5D",
        label=f"Nearest {neighbour_results['k']} real areas, similar deprivation (actual)",
    )
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(df.index)
    ax.set_xlabel("Crimes per 1,000 residents")
    ax.set_title(
        "Greater Manchester vs its nearest real-world matches\n"
        "Matched on deprivation profile alone, no model, just similar real places"
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)
    return output


def estimate(parquet_dir: Path, figures_dir: Path) -> dict[str, object]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    data = load_data(parquet_dir)

    non_gm = data[~data["lad_name"].isin(GM_BOROUGHS)]
    gm = data[data["lad_name"].isin(GM_BOROUGHS)]

    x = non_gm[FEATURE_COLUMNS]
    y = non_gm["crime_rate_per_1000"]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42)

    model = train_regressor(x_train, y_train)
    test_pred = model.predict(x_test)
    holdout_r2 = float(r2_score(y_test, test_pred))
    holdout_mae = float(mean_absolute_error(y_test, test_pred))

    gm_pred_lsoa = model.predict(gm[FEATURE_COLUMNS])
    gm = gm.assign(predicted_crime_rate_per_1000=gm_pred_lsoa)

    def weighted_mean(group: pd.DataFrame, col: str) -> float:
        weights = group["population"].fillna(0)
        if weights.sum() == 0:
            return float(group[col].mean())
        return float((group[col] * weights).sum() / weights.sum())

    borough_rows = []
    for name, group in gm.groupby("lad_name"):
        borough_rows.append(
            {
                "lad_name": name,
                "population": float(group["population"].sum()),
                "actual_crime_rate_per_1000": weighted_mean(group, "crime_rate_per_1000"),
                "predicted_crime_rate_per_1000": weighted_mean(group, "predicted_crime_rate_per_1000"),
            }
        )
    borough_summary = pd.DataFrame(borough_rows).set_index("lad_name")
    borough_summary["gap_multiple"] = (
        borough_summary["predicted_crime_rate_per_1000"] / borough_summary["actual_crime_rate_per_1000"]
    )

    national_actual_mean = float(non_gm["crime_rate_per_1000"].mean())
    gm_actual_mean = weighted_mean(gm, "crime_rate_per_1000")
    gm_predicted_mean = weighted_mean(gm, "predicted_crime_rate_per_1000")

    chart_path = save_borough_chart(borough_summary, figures_dir)

    lad_data = aggregate_to_local_authority(data)
    neighbour_results = nearest_neighbour_comparison(lad_data)
    neighbour_chart_path = save_neighbour_chart(neighbour_results, figures_dir)

    results = {
        "method": (
            "RandomForestRegressor trained on the 43 non-Greater-Manchester local "
            "authorities' LSOA-level deprivation features (same feature set as the "
            "hotspot classifier) to predict crime_rate_per_1000, then applied to "
            "Greater Manchester's own real, present deprivation data."
        ),
        "holdout_r2": holdout_r2,
        "holdout_mae_crimes_per_1000": holdout_mae,
        "rows_trained_on": int(len(non_gm)),
        "gm_lsoa_rows": int(len(gm)),
        "national_actual_mean_crime_rate_per_1000": national_actual_mean,
        "gm_actual_mean_crime_rate_per_1000": gm_actual_mean,
        "gm_predicted_mean_crime_rate_per_1000": gm_predicted_mean,
        "gm_predicted_vs_actual_multiple": gm_predicted_mean / gm_actual_mean if gm_actual_mean else None,
        "borough_summary": borough_summary.reset_index().to_dict(orient="records"),
        "chart": str(chart_path),
        "nearest_neighbour_comparison": neighbour_results,
        "nearest_neighbour_chart": str(neighbour_chart_path),
    }

    metrics_path = figures_dir / "gm_crime_rate_estimate.json"
    metrics_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def parse_args() -> argparse.Namespace:
    settings = load_settings()
    parser = argparse.ArgumentParser(
        description="Estimate what Greater Manchester's crime rate would likely be, "
        "based on a model trained on every other local authority's deprivation-to-crime "
        "relationship, applied to GM's own real deprivation data."
    )
    parser.add_argument("--parquet-dir", default=settings["processed_dir"])
    parser.add_argument("--figures-dir", default=settings["figures_dir"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = estimate(repo_path(args.parquet_dir), repo_path(args.figures_dir))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
