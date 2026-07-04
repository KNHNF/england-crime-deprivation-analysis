# src

Pipeline code lives here. Planned modules, built in this order:

- `ingest.py` or a Spark session helper: set up the SparkSession and read the raw police.uk CSV tree from `data/police/`.
- `spark_pipeline.py`: clean, join with IMD on LSOA, aggregate per LSOA, write Parquet to `data/processed/`. See `docs/03`.
- `load_mongo.py`: bulk import the processed Parquet into MongoDB, create indexes. See `docs/04`.
- `train_model.py`: feature engineering, hotspot classification, evaluation, save metrics and the confusion matrix to `figures/`. See `docs/05`.
- `dashboard/app.py`: the Streamlit app reading from MongoDB. See `docs/06`.

Keep each module runnable on its own so members can work in parallel. Configuration (MongoDB URI, data paths) goes in `.env`, loaded with python-dotenv, never hardcoded.
