# RESULT

Branch: `cloud/england-crime-deprivation-analysis-2026-11-02`. Nothing merged to main.

## What changed

- `src/spark_pipeline.py`: a missing police directory, or one with no `*-street.csv` files, now raises a `FileNotFoundError` that says what to do. Before, Spark raised `UNABLE_TO_INFER_SCHEMA` (observed).
- `src/train_model.py`:
  - Fewer than 8 rows with a crime rate now raises a clear `ValueError` instead of an obscure scikit-learn stratify error.
  - The imputer uses `keep_empty_features=True`. Without it, an all-empty feature column is silently dropped and the feature importances are misaligned with their names (the new test fails without this change, checked).
- `.env.example`: `MONGO_COLLECTION` was `lsoa_crime_deprivation`, but the code default and docs use `Crime_England_Deprivation`. Now consistent.
- `README.md`: the GM claim "near the same 200x gap" now matches `figures/gm_crime_rate_estimate.json` (212x nearest neighbours per docs/16, 275x forest, forest R2 0.23). Added an offline sample section and a Limits section.
- New: `tests/` (9 tests), `requirements-dev.txt` (adds pytest, needed to run the tests).

## What I read

README, `src/config.py`, `spark_session.py`, `spark_pipeline.py`, `train_model.py`, `.env.example`, `requirements.txt`, `.gitignore`, `src/README.md`, `data/README.md`, parts of `docs/07` and `docs/16`, and the metrics JSON files. I did not read `load_mongo.py` past its outline, nor `visualise*.py`, `estimate_gm_crime_rate.py`, `monthly_trend.py`, or the other docs in full.

## Tests (real output)

```
tests/test_pipeline_sample.py::test_pipeline_on_tiny_sample PASSED       [ 11%]
tests/test_pipeline_sample.py::test_missing_imd_column_gives_clear_error PASSED [ 22%]
tests/test_pipeline_sample.py::test_no_street_files_gives_clear_error PASSED [ 33%]
tests/test_pipeline_sample.py::test_missing_police_dir_gives_clear_error PASSED [ 44%]
tests/test_train_model.py::test_hotspot_is_top_quartile PASSED           [ 55%]
tests/test_train_model.py::test_null_rates_are_dropped PASSED            [ 66%]
tests/test_train_model.py::test_too_few_rows_gives_clear_error PASSED    [ 77%]
tests/test_train_model.py::test_missing_columns_gives_clear_error PASSED [ 88%]
tests/test_train_model.py::test_all_empty_feature_keeps_importances_aligned PASSED [100%]
======================== 9 passed, 1 warning in 32.58s =========================
```

Environment: Python 3.13, Java 21, PySpark 4.3.0, pandas 3.x, in a venv outside the repo. Not the pinned versions (see below). The tiny-sample test uses invented data and runs the real Spark pipeline end to end, offline.

## Could not check

- `pyspark==3.5.1` would not build on Python 3.13 here, so the pinned stack is untested. The project says Python 3.11 and Java 17.
- MongoDB loaders and `visualise_from_mongo.py` (no MongoDB).
- `visualise.py`, `estimate_gm_crime_rate.py`, `monthly_trend.py` (not run).
- The full-data run, so none of these are re-verified: 17,837,130 rows, 32,944 LSOAs, the 4.8x gap, the 540 to 113 decile table.

## Unverified claims

The README and docs numbers above come from the full local data, not from anything in the repo. What the repo does support: the decile table in docs/07 (540.3 to 112.9, ratio 4.79), the model metrics (0.804 / 0.820 accuracy, threshold 335.1, 32,870 rows) match `figures/hotspot_model_metrics.json`, and the GM figures match `figures/gm_crime_rate_estimate.json`. Not checked: the 17.8M row count, 1,563 file count, 74 unmatched and 0.22% figure (only in docs and README).

## Still missing for portfolio-ready

- A small committed sample dataset (or a script that generates one) so the full pipeline and the figures can be run by a reviewer.
- Tests for the Mongo loader, visualisation and GM estimate scripts, and CI running the tests.
- Decide whether to keep Streamlit in `requirements.txt` (dashboard descoped) and reconcile the pinned versions with a currently supported Python.
- Zero-crime LSOAs are missing from the output rather than zero; decide whether that biases the model, and say so in docs/08.
- Hotspot threshold uses `>=` the 75th percentile; README says "above 335". Minor wording.
- Model is trained and tested on random splits, with no spatial hold-out, so neighbouring LSOAs can leak across the split. Not tested or documented.

## Needs the laptop

Full-data run on the pinned versions, MongoDB steps, regenerating figures, confirming the row counts above.
