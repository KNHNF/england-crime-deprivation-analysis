# 03 Spark Pipeline

Owner: Karan.

## What it does

Reads the raw monthly street CSVs at national scale, cleans them, joins with IMD on LSOA code, aggregates crime per LSOA, and writes processed output for MongoDB and the ML step.

## Stages

1. Read: load the whole `data/police/**/*.csv` tree into one Spark DataFrame. Let Spark read the directory rather than looping in Python, so the read is parallel.
2. Clean: drop or flag rows with a blank LSOA code, standardise the crime category column, cast types, handle schema drift where column names or sets differ between months.
3. Join: join the crime DataFrame to the IMD DataFrame on LSOA code (left join from crime to IMD so unmatched crimes are visible rather than silently dropped).
4. Aggregate: group by LSOA to get total crimes, crimes per category, outcomes per category, average coordinates for map placement, force lists, and attach the IMD score and decile for that LSOA. Divide by LSOA population for a rate.
5. Write: save the aggregated per-LSOA table as Parquet in `data/processed/lsoa_crime_deprivation`, then load it into MongoDB via `src/load_mongo.py`.

## Current implementation

Code now exists in `src/spark_pipeline.py`.

Run:

```bash
python src/spark_pipeline.py
```

The job reads `POLICE_DATA_DIR` recursively, reads the IoD 2025 File 7 CSV, joins on `lsoa_code`, and writes one record per LSOA. The output fields are designed to match the MongoDB document in `docs/04`: `lsoa_code`, names, local authority fields, `total_crimes`, nested `crimes_by_category`, nested `outcomes_by_category`, average longitude and latitude, force lists, IoD domain features, `population`, `crime_rate_per_1000`, and a placeholder `hotspot` field for the ML step.

Local validation so far:

- Python syntax checks pass.
- CLI help works for `src/spark_pipeline.py`.
- Java 25 issue resolved: Java 17.0.19 is now the system default.
- 2026-07-10: two real bugs found and fixed while validating on a small real sample (2 forces, one month). Full detail in the repo's local `GOTCHAS.md`.
  1. `read_police_data()` was reading `*-outcomes.csv` files alongside `*-street.csv` files. These are two different police.uk file types with incompatible schemas, mixing them corrupted columns and crashed the pivot. Fixed with a `pathGlobFilter` on `*-street.csv` only.
  2. After fix 1, 86% of output rows still failed to join against the IMD table. Not a bug: the IoD 2025 file only covers English LSOAs, and the archive includes four Welsh forces (Dyfed-Powys, Gwent, North Wales, South Wales) that report Welsh LSOA codes, which cannot match an England-only table. Added a filter to scope crime data to English LSOAs (`E01...`) before aggregation. Confirmed 0 unmatched rows on the same sample after the fix.
  3. `visualise.py` and `train_model.py` both run cleanly end to end against the fixed pipeline's output on the same small sample. Numbers from that run are not usable (54 LSOA rows, one month, two forces), this only confirms the code path works.
- 2026-07-10 (later): full national run completed successfully on Karan's own machine after fixing a separate Windows-only issue (missing winutils.exe/hadoop.dll, PySpark on Windows needs Hadoop's native file-listing shim or it crashes with `UnsatisfiedLinkError` even just listing the CSV directory). Real output:

```json
{
  "raw_crime_rows": 17837130,
  "clean_crime_rows": 16249125,
  "output_lsoa_rows": 32944,
  "unmatched_lsoa_rows": 74,
  "first_month": "2023-06-01",
  "last_month": "2026-05-01"
}
```

  17.8M raw crime records read, 16.2M after cleaning and the England-only filter, aggregated to 32,944 LSOA rows (essentially all English LSOAs), only 74 unmatched against IMD (0.22%, down from 86% before the two bug fixes on the earlier small-sample test). `total_crimes` and `crime_rate_per_1000` are 3-year cumulative figures (June 2023 to May 2026), not monthly, worth stating plainly on the slide so it is not misread as a monthly rate. Distribution: mean 493 crimes per LSOA over the 3 years, mean crime rate 287 per 1,000 residents, median 204 per 1,000, max 19,159 per 1,000 (a clear extreme outlier LSOA worth checking by name before presenting).

## Why Spark and not pandas

State this clearly for the video, ideally with a real timing:

- The raw archive is 19M+ rows across many files. Loaded naively into pandas it is slow and can exhaust memory on a normal laptop.
- Spark reads the files in parallel, applies the cleaning and join across partitions, and only the small aggregated result (about 32k LSOA rows) is collected at the end.
- The heavy work (19M rows) stays distributed. The output (32k rows) is small. That contrast is the argument for Spark.

## To record here as work happens

- What was built: the stages above, key transformations, and the actual column schema.
- Why Spark over pandas for this step, with a real timing if possible (full-archive read and aggregate time).
- Problems hit and fixes: schema drift between months, null or blank LSOA codes, skewed partitions, memory settings.
- Outcome: output row count, runtime, output format and location.
