# 03 Spark Pipeline

Owner: Karan.

## What it does

Reads the raw monthly street CSVs at national scale, cleans them, joins with IMD on LSOA code, aggregates crime per LSOA, and writes processed output for MongoDB and the ML step.

## Stages

1. Read: load the whole `data/police/**/*.csv` tree into one Spark DataFrame. Let Spark read the directory rather than looping in Python, so the read is parallel.
2. Clean: drop or flag rows with a blank LSOA code, standardise the crime category column, cast types, handle schema drift where column names or sets differ between months.
3. Join: join the crime DataFrame to the IMD DataFrame on LSOA code (left join from crime to IMD so unmatched crimes are visible rather than silently dropped).
4. Aggregate: group by LSOA to get total crimes, crimes per category, and attach the IMD score and decile for that LSOA. Optionally divide by LSOA population for a rate.
5. Write: save the aggregated per-LSOA table (Parquet on disk, then into MongoDB via `docs/04`).

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
