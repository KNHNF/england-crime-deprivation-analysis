# 02 Datasets


## Sources

1. police.uk street-level crime archive
   - URL: https://data.police.uk/data/
   - Download the full archive as monthly CSVs across multiple years. Each row is one recorded crime with a category, a month, an approximate location, and an LSOA code.
   - Scale: 19M+ rows across the archive. This is the dataset that justifies Spark.

2. English Indices of Deprivation 2025
   - Local file: `data/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv`.
   - File 7 is the LSOA-level scores file. It includes IoD scores, ranks, deciles, local authority fields, and mid-2022 population denominators.
   - Scale: about 33k LSOAs.

3. Population denominators
   - Already included in the IoD 2025 File 7 CSV as `Total population: mid 2022`.
   - The Spark output uses this to calculate `crime_rate_per_1000`.

## The join

Join key is the LSOA code. Street records carry it directly, IMD is published at LSOA level, so it is a direct join with no manual geography lookup. This removes the force-to-district mapping the prototype needed.

## Why these two

Crime volume at record level gives the scale that justifies Spark. IMD gives the socioeconomic angle that turns description into explanation. Both are open UK government data with no licensing issues, and both differ from the 75% paper dataset and the ML course dataset, which the module requires.

## To record here as work happens

- Exact archive date range downloaded, row counts per year, total size on disk.
- Missing value rates per column, and known quirks: blank LSOA codes, the deliberate location fuzzing police.uk applies, category changes between years.
- Any forces or months excluded and the reason.
- IoD version note: IoD 2025 is now used, so the deprivation snapshot is closer to the June 2023 to May 2026 crime window than the earlier 2019 plan.

## Current Local Files

- Police archive extracted folder: `data/Crime Data LSOA (june 2023 - may 2026)`.
- Street CSV count: 1,563 files.
- IoD file: `data/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv`.
