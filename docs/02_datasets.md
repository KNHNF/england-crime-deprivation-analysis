# 02 Datasets


## Sources

1. police.uk street-level crime archive
   - URL: https://data.police.uk/data/
   - Download the full archive as monthly CSVs across multiple years. Each row is one recorded crime with a category, a month, an approximate location, and an LSOA code.
   - Scale: 19M+ rows across the archive. This is the dataset that justifies Spark.

2. English Index of Multiple Deprivation (IMD) 2019
   - URL: https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019
   - File 7 (the LSOA-level scores) is the one to use. IMD combines income, employment, education, health, crime, housing, and living environment into one score and rank per LSOA. Higher score means more deprived.
   - Scale: 32,844 LSOAs.

3. Optional but recommended: LSOA population estimates
   - ONS mid-year population estimates at LSOA level.
   - Needed only if we report a crime rate per 1,000 people rather than raw crime counts. Without it we can still classify hotspots on counts, but a rate is fairer across areas of different size. Decide this in `docs/05`.

## The join

Join key is the LSOA code. Street records carry it directly, IMD is published at LSOA level, so it is a direct join with no manual geography lookup. This removes the force-to-district mapping the prototype needed.

## Why these two

Crime volume at record level gives the scale that justifies Spark. IMD gives the socioeconomic angle that turns description into explanation. Both are open UK government data with no licensing issues, and both differ from the 75% paper dataset and the ML course dataset, which the module requires.

## To record here as work happens

- Exact archive date range downloaded, row counts per year, total size on disk.
- Missing value rates per column, and known quirks: blank LSOA codes, the deliberate location fuzzing police.uk applies, category changes between years.
- Any forces or months excluded and the reason.
- IMD version note: IMD is 2019, crime is more recent, so there is a time gap. Record it here and carry it into `docs/08`.
