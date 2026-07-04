# 01 Project Overview

Owner: Karan. Everyone reads this one.

## Research question

Is area deprivation associated with crime across England, and can deprivation-related features predict crime levels at LSOA level?

LSOA means Lower Layer Super Output Area, the small-area unit used across UK statistics. England has 32,844 of them, each roughly 1,500 people. Working at LSOA level is what lets us line up crime and deprivation on the same geography.

## Why this project

The module requires a genuinely big dataset processed with Big Data tools. The full national street-level police.uk archive (multiple years, 19M+ individual crime records) justifies Spark. A smaller aggregated table does not, which is exactly what the prototype was marked down for. Deprivation adds the socioeconomic angle that turns a description of where crime happens into an attempt to explain it.

## Pipeline at a glance

```
Raw police.uk street CSVs
   -> Spark (clean, join with IMD on LSOA, aggregate crime per LSOA)
   -> feature engineering
   -> MongoDB (processed area records)
   -> machine learning (hotspot classification)
   -> Streamlit dashboard
   -> evaluation
```

## What changed from the prototype

The prototype used pre-aggregated crime counts by police force area (about 25,000 rows) and needed a manual force-to-district lookup to line up with deprivation. This version uses the raw street-level records, which already carry an LSOA code, so it joins directly to IMD at LSOA level. That is both genuinely big data and a cleaner, more defensible join.

## Status log

Update after each milestone with date, what was built, why that approach, problems hit, and outcome. Keep entries to one or two lines.

- 2026-07-04: repo structure and docs created. National-scale plan agreed. No pipeline code yet.
