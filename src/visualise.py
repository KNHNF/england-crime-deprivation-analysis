from __future__ import annotations

import argparse
from pathlib import Path

import folium
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from folium.plugins import HeatMap

from config import load_settings, repo_path


def load_lsoa_table(parquet_dir: Path) -> pd.DataFrame:
    data = pd.read_parquet(parquet_dir)
    required = {
        "lsoa_code",
        "lsoa_name",
        "avg_longitude",
        "avg_latitude",
        "total_crimes",
        "crime_rate_per_1000",
        "imd_score",
        "imd_decile",
    }
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Processed data is missing columns: {missing}")
    return data


def clean_for_plots(data: pd.DataFrame) -> pd.DataFrame:
    plot_data = data.dropna(
        subset=["avg_longitude", "avg_latitude", "crime_rate_per_1000", "imd_score", "imd_decile"]
    ).copy()
    plot_data["crime_rate_per_1000"] = pd.to_numeric(plot_data["crime_rate_per_1000"], errors="coerce")
    plot_data["imd_score"] = pd.to_numeric(plot_data["imd_score"], errors="coerce")
    plot_data["imd_decile"] = pd.to_numeric(plot_data["imd_decile"], errors="coerce")
    return plot_data.dropna(subset=["crime_rate_per_1000", "imd_score", "imd_decile"])


def save_crime_rate_map(data: pd.DataFrame, figures_dir: Path) -> Path:
    output = figures_dir / "crime_rate_lsoa_map.png"
    plt.figure(figsize=(8, 10))
    scatter = plt.scatter(
        data["avg_longitude"],
        data["avg_latitude"],
        c=data["crime_rate_per_1000"],
        s=8,
        cmap="magma",
        alpha=0.65,
        linewidths=0,
    )
    plt.colorbar(scatter, label="Crimes per 1,000 residents")
    plt.title("Crime rate by LSOA, June 2023 to May 2026")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def save_deprivation_map(data: pd.DataFrame, figures_dir: Path) -> Path:
    output = figures_dir / "iod2025_deprivation_lsoa_map.png"
    plt.figure(figsize=(8, 10))
    scatter = plt.scatter(
        data["avg_longitude"],
        data["avg_latitude"],
        c=data["imd_decile"],
        s=8,
        cmap="viridis_r",
        alpha=0.65,
        linewidths=0,
    )
    plt.colorbar(scatter, label="IoD 2025 decile, 1 is most deprived")
    plt.title("IoD 2025 deprivation by LSOA")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def save_crime_deprivation_scatter(data: pd.DataFrame, figures_dir: Path) -> Path:
    output = figures_dir / "crime_rate_vs_iod2025_score.png"
    plt.figure(figsize=(9, 6))
    sns.regplot(
        data=data,
        x="imd_score",
        y="crime_rate_per_1000",
        scatter_kws={"alpha": 0.35, "s": 12},
        line_kws={"color": "black", "linewidth": 1.5},
    )
    plt.title("Crime rate and IoD 2025 deprivation score")
    plt.xlabel("IoD 2025 score")
    plt.ylabel("Crimes per 1,000 residents")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def save_decile_chart(data: pd.DataFrame, figures_dir: Path) -> Path:
    output = figures_dir / "average_crime_rate_by_iod2025_decile.png"
    deciles = (
        data.groupby("imd_decile", as_index=False)["crime_rate_per_1000"]
        .mean()
        .sort_values("imd_decile")
    )
    plt.figure(figsize=(9, 5))
    sns.barplot(data=deciles, x="imd_decile", y="crime_rate_per_1000", color="#4C78A8")
    plt.title("Average crime rate by IoD 2025 decile")
    plt.xlabel("IoD 2025 decile, 1 is most deprived")
    plt.ylabel("Average crimes per 1,000 residents")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def save_heatmap(data: pd.DataFrame, figures_dir: Path) -> Path:
    output = figures_dir / "crime_rate_heatmap.html"
    centre = [data["avg_latitude"].mean(), data["avg_longitude"].mean()]
    fmap = folium.Map(location=centre, zoom_start=6, tiles="CartoDB positron")
    heat_data = data[["avg_latitude", "avg_longitude", "crime_rate_per_1000"]].values.tolist()
    HeatMap(heat_data, radius=9, blur=12, min_opacity=0.25).add_to(fmap)
    fmap.save(output)
    return output


def save_deprivation_heatmap_interactive(data: pd.DataFrame, figures_dir: Path) -> Path:
    # Interactive twin of save_heatmap(), same zoomable street-level basemap,
    # coloured by deprivation instead of crime rate, plus a layer toggle so
    # both can be viewed in one file rather than two separate maps.
    output = figures_dir / "deprivation_heatmap.html"
    centre = [data["avg_latitude"].mean(), data["avg_longitude"].mean()]
    fmap = folium.Map(location=centre, zoom_start=6, tiles="CartoDB positron")

    crime_layer = folium.FeatureGroup(name="Crime rate (per 1,000 residents)", show=True)
    crime_data = data[["avg_latitude", "avg_longitude", "crime_rate_per_1000"]].values.tolist()
    HeatMap(crime_data, radius=9, blur=12, min_opacity=0.25).add_to(crime_layer)
    crime_layer.add_to(fmap)

    # IoD decile runs 1 (most deprived) to 10 (least deprived), invert so the
    # heatmap intensity reads the same way as the crime layer: hot = worse.
    deprivation_layer = folium.FeatureGroup(name="Deprivation (IoD 2025)", show=False)
    deprivation_weight = 11 - data["imd_decile"]
    deprivation_data = pd.DataFrame(
        {
            "lat": data["avg_latitude"],
            "lon": data["avg_longitude"],
            "weight": deprivation_weight,
        }
    ).values.tolist()
    HeatMap(deprivation_data, radius=9, blur=12, min_opacity=0.25).add_to(deprivation_layer)
    deprivation_layer.add_to(fmap)

    folium.LayerControl(collapsed=False).add_to(fmap)
    fmap.save(output)
    return output


def save_heatmap_static(data: pd.DataFrame, figures_dir: Path) -> Path:
    # Static PNG version of the England crime heatmap for the slide deck.
    # The interactive folium HTML above is not embeddable in pptx, and this
    # avoids depending on an internet basemap tile fetch: the LSOA point
    # cloud itself already traces England's outline at this density.
    output = figures_dir / "crime_rate_heatmap_static.png"
    plt.figure(figsize=(8, 10))
    plt.hexbin(
        data["avg_longitude"],
        data["avg_latitude"],
        C=data["crime_rate_per_1000"],
        reduce_C_function=lambda vals: sum(vals) / len(vals),
        gridsize=120,
        cmap="inferno",
        mincnt=1,
    )
    plt.colorbar(label="Crimes per 1,000 residents (3-year total)")
    plt.title("England crime rate heatmap, June 2023 to May 2026")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.gca().set_facecolor("black")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def save_lad_ranking(parquet_dir: Path, figures_dir: Path) -> Path:
    # Greater Manchester's 10 boroughs are excluded here: Greater Manchester
    # Police has no data in this archive at all (confirmed by checking every
    # monthly folder directly), so their crime rate reads as near-zero and
    # would wrongly dominate the "lowest crime" side of this ranking. See
    # docs/08_limitations.md for the full explanation.
    GM_BOROUGHS = {
        "Oldham", "Bury", "Tameside", "Trafford", "Salford",
        "Rochdale", "Bolton", "Wigan", "Manchester", "Stockport",
    }
    data = pd.read_parquet(
        parquet_dir, columns=["lad_name", "total_crimes", "population"]
    ).dropna(subset=["lad_name"])
    data = data[~data["lad_name"].isin(GM_BOROUGHS)]

    lad = data.groupby("lad_name").agg(
        total_crimes=("total_crimes", "sum"),
        population=("population", "sum"),
        n_lsoas=("lad_name", "count"),
    )
    lad = lad[lad["n_lsoas"] >= 10]  # drop partial/tiny LADs for a fair comparison
    lad["crime_rate_per_1000"] = lad["total_crimes"] / lad["population"] * 1000

    top10 = lad.nlargest(10, "crime_rate_per_1000")
    bottom10 = lad.nsmallest(10, "crime_rate_per_1000")

    output = figures_dir / "local_authority_ranking.png"
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))

    axes[0].barh(top10.index[::-1], top10["crime_rate_per_1000"][::-1], color="#B5451B")
    axes[0].set_title("Highest crime rate local authorities")
    axes[0].set_xlabel("Crimes per 1,000 residents (3-year total)")

    axes[1].barh(bottom10.index[::-1], bottom10["crime_rate_per_1000"][::-1], color="#4C78A8")
    axes[1].set_title("Lowest crime rate local authorities")
    axes[1].set_xlabel("Crimes per 1,000 residents (3-year total)")

    fig.suptitle("Local authorities by crime rate (Greater Manchester excluded, no data, see limitations)")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def save_crime_category_breakdown(parquet_dir: Path, figures_dir: Path) -> Path:
    # National crime category breakdown, summed across all LSOAs. crimes_by_category
    # is stored as a Spark map, which pandas/pyarrow reads back as a list of
    # (key, value) tuples per row, not a dict, hence the manual tally below.
    import pandas as pd
    from collections import Counter

    raw = pd.read_parquet(parquet_dir, columns=["crimes_by_category"])
    totals: Counter = Counter()
    for row in raw["crimes_by_category"]:
        if row is None:
            continue
        for key, value in row:
            totals[key] += value

    output = figures_dir / "national_crime_category_breakdown.png"
    top = pd.Series(dict(totals.most_common(10))).sort_values(ascending=True)
    labels = [name.replace("_", " ").title() for name in top.index]

    plt.figure(figsize=(9, 6))
    plt.barh(labels, top.values, color="#4C78A8")
    plt.title("Top 10 crime categories, England, June 2023 to May 2026")
    plt.xlabel("Total recorded crimes")
    for i, value in enumerate(top.values):
        plt.text(value, i, f" {value:,.0f}", va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def build_visuals(parquet_dir: Path, figures_dir: Path) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    data = clean_for_plots(load_lsoa_table(parquet_dir))
    outputs = [
        save_crime_rate_map(data, figures_dir),
        save_deprivation_map(data, figures_dir),
        save_crime_deprivation_scatter(data, figures_dir),
        save_decile_chart(data, figures_dir),
        save_heatmap(data, figures_dir),
        save_heatmap_static(data, figures_dir),
        save_deprivation_heatmap_interactive(data, figures_dir),
        save_crime_category_breakdown(parquet_dir, figures_dir),
        save_lad_ranking(parquet_dir, figures_dir),
    ]
    return outputs


def parse_args() -> argparse.Namespace:
    settings = load_settings()
    parser = argparse.ArgumentParser(description="Create presentation figures from processed LSOA output.")
    parser.add_argument("--parquet-dir", default=settings["processed_dir"])
    parser.add_argument("--figures-dir", default=settings["figures_dir"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = build_visuals(repo_path(args.parquet_dir), repo_path(args.figures_dir))
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
