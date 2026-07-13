# src

Pipeline code. All modules below are built and runnable, listed in the order they run.

- `config.py`: shared path and MongoDB settings, loaded from `.env`.
- `spark_session.py`: SparkSession helper used by the pipeline and Mongo loaders.
- `spark_pipeline.py`: cleans the raw police.uk archive, joins with IoD 2025 on LSOA code, aggregates per LSOA, writes Parquet to `data/processed/lsoa_crime_deprivation`. Two real bugs were caught and fixed here (an outcomes-file schema mixup, and a Welsh-LSOA join failure), see `docs/03`.
- `load_mongo.py`: bulk imports the processed Parquet into MongoDB, creates indexes. See `docs/04`.
- `load_monthly_trend_mongo.py`: loads the 36 monthly national crime totals into a second MongoDB collection.
- `monthly_trend.py`: builds the monthly trend chart directly from the raw CSVs, independent of the Spark output, useful for a quick sanity check against the aggregated figures.
- `visualise.py`: creates the maps, heatmap, and crime-deprivation charts from the processed Parquet output. See `docs/07`.
- `visualise_from_mongo.py`: the same charts as `visualise.py`, sourced from live MongoDB aggregation queries instead of the local Parquet file. This is the version to reference when demonstrating that the charts come from the database, not just a local file.
- `train_model.py`: trains the hotspot classifiers (logistic regression, random forest), writes metrics JSON and confusion matrix images. See `docs/05`.

A Streamlit dashboard (`dashboard/app.py`) was planned but descoped on 11 July 2026, see `docs/06_dashboard.md`. It is not part of the current pipeline.

Each module runs on its own so members can work in parallel. Configuration (MongoDB URI, data paths) goes in `.env`, loaded with python-dotenv, never hardcoded.
