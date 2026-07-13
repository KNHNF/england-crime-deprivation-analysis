# data

This folder is gitignored except for this file. Nothing large is committed. Download the datasets here manually.

## Layout

```
data/
  Crime Data LSOA (june 2023 - may 2026)/  extracted police.uk monthly CSVs
  File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv
  processed/       Spark output (Parquet), generated, do not edit by hand
```

## Downloads

- police.uk archive: https://data.police.uk/data/ (select the full date range, include crime data and outcomes data, download, unzip; current local extract covers June 2023 to May 2026).
- IoD 2025 File 7: https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025 (LSOA-level scores, ranks, deciles, and population denominators).

Record the exact archive date range, row counts, and total size in `docs/02_datasets.md` once downloaded.
