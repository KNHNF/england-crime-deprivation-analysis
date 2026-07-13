from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import load_settings, repo_path


FEATURE_COLUMNS = [
    "imd_score",
    "imd_decile",
    "income_score",
    "income_decile",
    "employment_score",
    "employment_decile",
    "education_score",
    "education_decile",
    "health_score",
    "health_decile",
    "housing_score",
    "housing_decile",
    "living_environment_score",
    "living_environment_decile",
    "population",
]


def load_training_data(parquet_dir: Path) -> pd.DataFrame:
    data = pd.read_parquet(parquet_dir)
    required = set(FEATURE_COLUMNS + ["lsoa_code", "crime_rate_per_1000"])
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Processed data is missing columns: {missing}")
    return data


def add_hotspot_label(data: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    model_data = data.copy()
    model_data["crime_rate_per_1000"] = pd.to_numeric(model_data["crime_rate_per_1000"], errors="coerce")
    model_data = model_data.dropna(subset=["crime_rate_per_1000"])
    threshold = float(model_data["crime_rate_per_1000"].quantile(0.75))
    model_data["hotspot"] = model_data["crime_rate_per_1000"] >= threshold
    return model_data, threshold


def build_models() -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=250,
                        random_state=42,
                        class_weight="balanced",
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def evaluate_model(model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float | list[list[int]]]:
    predictions = model.predict(x_test)
    matrix = confusion_matrix(y_test, predictions, labels=[False, True])
    return {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision_hotspot": float(precision_score(y_test, predictions, zero_division=0)),
        "recall_hotspot": float(recall_score(y_test, predictions, zero_division=0)),
        "f1_hotspot": float(f1_score(y_test, predictions, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
    }


def save_feature_importance(model: Pipeline, feature_names: list[str], figures_dir: Path) -> Path:
    # Random forest only, logistic regression's coefficients aren't directly
    # comparable in scale without extra work, and the random forest is the
    # stronger non-linear model here anyway.
    importances = model.named_steps["model"].feature_importances_
    labels = [name.replace("_", " ").title() for name in feature_names]
    order = sorted(range(len(importances)), key=lambda i: importances[i])

    output = figures_dir / "random_forest_feature_importance.png"
    plt.figure(figsize=(9, 6))
    plt.barh([labels[i] for i in order], [importances[i] for i in order], color="#4C78A8")
    plt.title("Which features the hotspot model actually relies on")
    plt.xlabel("Relative importance (random forest, Gini-based)")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()
    return output


def save_confusion_matrix(matrix: list[list[int]], title: str, output_path: Path) -> None:
    plt.figure(figsize=(5, 4))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["not hotspot", "hotspot"],
        yticklabels=["not hotspot", "hotspot"],
    )
    plt.title(title)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def train_and_evaluate(parquet_dir: Path, figures_dir: Path) -> dict[str, object]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    data, threshold = add_hotspot_label(load_training_data(parquet_dir))
    x = data[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    y = data["hotspot"]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    results: dict[str, object] = {
        "hotspot_definition": "Top quartile of LSOAs by crimes per 1,000 residents",
        "hotspot_threshold_crimes_per_1000": threshold,
        "rows_used": int(len(data)),
        "features": FEATURE_COLUMNS,
        "models": {},
    }

    for name, model in build_models().items():
        model.fit(x_train, y_train)
        metrics = evaluate_model(model, x_test, y_test)
        results["models"][name] = metrics
        save_confusion_matrix(
            metrics["confusion_matrix"],
            name.replace("_", " ").title(),
            figures_dir / f"{name}_confusion_matrix.png",
        )
        if name == "random_forest":
            importance_path = save_feature_importance(model, FEATURE_COLUMNS, figures_dir)
            importances = model.named_steps["model"].feature_importances_
            results["feature_importance"] = {
                feature: float(score) for feature, score in sorted(
                    zip(FEATURE_COLUMNS, importances), key=lambda pair: pair[1], reverse=True
                )
            }
            print(f"Wrote {importance_path}")

    metrics_path = figures_dir / "hotspot_model_metrics.json"
    metrics_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def parse_args() -> argparse.Namespace:
    settings = load_settings()
    parser = argparse.ArgumentParser(description="Train hotspot classifiers from processed LSOA output.")
    parser.add_argument("--parquet-dir", default=settings["processed_dir"])
    parser.add_argument("--figures-dir", default=settings["figures_dir"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = train_and_evaluate(repo_path(args.parquet_dir), repo_path(args.figures_dir))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
