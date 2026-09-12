# England Crime and Deprivation Analysis

UWE Bristol, Big Data module, 25% group video assessment.
This repo is my own individual rebuild of the pipeline, built alongside the group's official 25% video assessment submission (UWE Bristol, Big Data module). Other group members were not involved in this repo's code.

GitHub: [KNHNF/england-crime-depriviation-analysis](https://github.com/KNHNF/england-crime-depriviation-analysis) (renamed from the working repo name `bigdata-crime-deprivation-spark`).

## What this is

A distributed Big Data pipeline that tests whether area deprivation is associated with crime across England, and whether deprivation features can predict crime levels at small-area (LSOA) level.

This is a national-scale rebuild of an earlier prototype (`bigdata-crime-deprivation`), which used pre-aggregated crime tables of about 25,000 rows and was marked down for not being genuinely big data. That prototype is kept for reference and is not reused here. This version processes the full street-level police.uk archive (June 2023 to May 2026, 17.8 million individual crime records) with Apache Spark, stores processed output in MongoDB, and trains a machine learning model to predict crime hotspots from deprivation features.

## Why the scale matters

The full street-level archive is the point, not an optional extra. It is what justifies Spark over pandas, and it is the direct answer to the feedback on the prototype. Each crime record carries an LSOA code, so it joins straight to the Index of Multiple Deprivation at LSOA level. No manual police-force-to-district lookup is needed this time.

## Pipeline

```
Raw police.uk street CSVs (17.8M rows, 1,563 files)
   -> Apache Spark (clean, join with IoD 2025, aggregate to LSOA)
   -> MongoDB (32,944 processed area records)
   -> machine learning (hotspot classification: logistic regression and random forest)
   -> presentation
```

A Streamlit dashboard was in the original plan but was descoped on 11 July 2026: the brief only requires showing how the data gets queried, which the MongoDB schema and query slide already covers, and a dashboard was real added scope this close to the deadline with no marks specifically tied to it. See `docs/06_dashboard.md` for the full reasoning, kept for reference in case there's time to revisit it.

## How to read this repo

Start with `docs/01_project_overview.md` for the research question and the whole pipeline in one page. Each `docs/` file after that covers one component: what it does, why that approach, problems hit, and outcome. You can present your section from the docs without reading the code.

```
docs/
  01_project_overview.md   research question and the whole pipeline in one page
  02_datasets.md           the two datasets, the join key, how to download
  03_spark_pipeline.md     what Spark does and why Spark, including real bugs hit and fixed
  04_mongodb.md            document schema, indexes, queries
  05_machine_learning.md   the ML task, model, metrics
  06_dashboard.md          why the dashboard was descoped
  07_results.md            findings, each with an explanation
  08_limitations.md        what the data and method cannot tell us
  09_presentation_notes.md video plan, section split, talking points
  10_eda_and_build_log.md  EDA plan, build decisions, and issues hit
```

## Repository layout

```
.
├── README.md
├── requirements.txt
├── docs/                 one short file per component (read these)
├── src/                  pipeline code (see src/README.md)
├── data/                 raw and processed data, gitignored, download manually
└── figures/              charts and screenshots for the slides, gitignored
```

## Quickstart

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

PySpark needs Java 11 or 17. Java 25 fails locally with `getSubject is not supported`, so set `JAVA_HOME` to a Java 17 install before running the full pipeline. On Windows you may also see a `winutils.exe` warning, that one is harmless, the Java version error is the one that blocks the run.

Copy `.env.example` to `.env` and fill in the MongoDB URI. The current local police.uk extract is `data/Crime Data LSOA (june 2023 - may 2026)`, and the IoD file is already named in `.env.example`.

Run the Spark pipeline:

```bash
python src/spark_pipeline.py
```

Create the presentation maps, charts, and model outputs:

```bash
python src/visualise.py
python src/train_model.py
```

Load the Spark Parquet output into MongoDB:

```bash
python src/load_mongo.py
python src/load_monthly_trend_mongo.py
```

The `data/` folder is gitignored, so nothing large is committed.

## Real numbers from the full run

17,837,130 raw crime rows read, 16,249,125 after cleaning and filtering to English LSOAs, aggregated to 32,944 LSOA rows (essentially all English LSOAs), 74 unmatched against the IoD table (0.22%). Figures are 3-year cumulative totals, June 2023 to May 2026, not monthly rates. Full detail and the two real bugs found along the way are in `docs/03_spark_pipeline.md`.

## Tools used

- Python 3.11: project scripts.
- Java 17: required for PySpark on this project.
- Apache Spark, through PySpark: reads and aggregates the national police.uk CSV archive.
- MongoDB Atlas: stores the processed LSOA documents (`Crime_England_Deprivation`, 32,944 documents) and monthly national totals (`monthly_crime_trend`, 36 documents).
- MongoDB Compass: checking imported documents and indexes, and screenshotting real query output for the slides.
- scikit-learn: hotspot classification (logistic regression and random forest).
- Matplotlib and Seaborn: charts for the slides.
- Microsoft Teams: recording the group video.

## Working rule for the whole team

Within about ten minutes of finishing any milestone, the person who did it updates the matching `docs/` file with four things: what was built, why that approach, problems hit, and the outcome. By video time the content already exists and nobody has to reverse-engineer code the night before.
