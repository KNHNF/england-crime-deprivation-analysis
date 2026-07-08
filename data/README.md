# data

This folder is gitignored except for this file. Nothing large is committed. Download the datasets here manually.

## Layout

```
data/
  police/          raw police.uk monthly CSVs (unzip the archive into here)
  imd2019.csv      English IMD 2019, File 7 (LSOA-level scores)
  lsoa_population.csv   optional, ONS mid-year LSOA population estimates
  processed/       Spark output (Parquet), generated, do not edit by hand
```

## Downloads

- police.uk + Include crime data + Include outcomes data (from june 2023 till; May 2026) archive: https://data.police.uk/data/ (select the full date range, download, unzip into `data/police/`).
- IMD 2025 File 7: https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025
- LSOA population (optional, only if reporting a per-1,000 rate): ONS mid-year population estimates at LSOA level.

Record the exact archive date range, row counts, and total size in `docs/02_datasets.md` once downloaded.
