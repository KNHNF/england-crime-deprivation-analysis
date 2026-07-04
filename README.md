# Crime and Deprivation in England, at national scale

UWE Bristol, Big Data module, 25% group video assessment.

## What this is

A distributed Big Data pipeline that tests whether area deprivation is associated with crime across England, and whether deprivation features can predict crime levels at small-area (LSOA) level.

This is a fresh national-scale rebuild. An earlier prototype (repo `bigdata-crime-deprivation`) used pre-aggregated crime tables of about 25,000 rows and was marked down for not being genuinely big data. That prototype is kept for reference and is not reused here. This version processes the full street-level police.uk archive (multiple years, 19M+ individual crime records) with Apache Spark, stores processed output in MongoDB, trains a machine learning model, and presents results in a Streamlit dashboard.

## Why the scale matters

The full street-level archive is the point, not an optional extra. It is what justifies Spark over pandas, and it is the direct answer to the feedback on the prototype. Each crime record carries an LSOA code, so it joins straight to the Index of Multiple Deprivation at LSOA level. No manual police-force-to-district lookup is needed this time.

## Pipeline

```
Raw police.uk street CSVs
   -> Apache Spark (clean, join with IMD, aggregate to LSOA)
   -> feature engineering
   -> MongoDB (processed area records)
   -> machine learning (hotspot classification, plus alternatives)
   -> Streamlit dashboard
   -> evaluation
```

## How to read this repo

Start with `PROJECT_PLAN.md` for the plan, roles, and timeline. Then read `docs/` in order. Each `docs/` file covers one component in one to two pages: what it does, why that approach, problems hit, and outcome. You can present your section from the docs without reading the code.

```
docs/
  01_project_overview.md   research question and the whole pipeline in one page
  02_datasets.md           the two datasets, the join key, how to download
  03_spark_pipeline.md     what Spark does and why Spark
  04_mongodb.md            document schema, indexes, queries
  05_machine_learning.md   the ML task, model, metrics, and the two alternatives
  06_dashboard.md          the Streamlit app
  07_results.md            findings, each with an explanation
  08_limitations.md        what the data and method cannot tell us
  09_presentation_notes.md video plan, section split, talking points
```

## Repository layout

```
.
├── README.md
├── PROJECT_PLAN.md
├── requirements.txt
├── docs/                 one short file per component (read these)
├── src/                  pipeline code (see src/README.md)
├── data/                 raw and processed data, gitignored, download manually
└── figures/             charts and screenshots for the slides, gitignored
```

## Quickstart

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Download the datasets into `data/` as described in `docs/02_datasets.md` (the `data/` folder is gitignored, so nothing large is committed). Then follow `docs/03_spark_pipeline.md` to run the pipeline.

## Working rule for the whole team

Within about ten minutes of finishing any milestone, the person who did it updates the matching `docs/` file with four things: what was built, why that approach, problems hit, and the outcome. By video time the content already exists and nobody has to reverse-engineer code the night before.
