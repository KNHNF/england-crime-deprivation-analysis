# 04 MongoDB


## What it does

Stores the processed per-LSOA records that Spark produces. The dashboard and the ML step read from here.

## Why a document store fits

- The aggregated record for an LSOA has a variable set of crime-category counts. A document with a nested `crimes_by_category` field holds that naturally without a wide sparse table.
- The import is write-heavy and done in bulk from Spark output, which MongoDB handles well.
- The dashboard needs fast lookups by LSOA and fast aggregations by deprivation decile, both served by indexes.

## Proposed document schema

One document per LSOA:

```json
{
  "lsoa_code": "E01000001",
  "lsoa_name": "City of London 001A",
  "total_crimes": 128,
  "crimes_by_category": {
    "violence_and_sexual_offences": 40,
    "anti_social_behaviour": 33,
    "theft": 20
  },
  "imd_score": 12.4,
  "imd_decile": 8,
  "population": 1503,
  "crime_rate_per_1000": 85.2,
  "hotspot": false
}
```

Confirm the exact fields once the Spark output is final, then paste one real document here.

## Indexes

- `lsoa_code`: unique, the primary lookup for the dashboard.
- `imd_decile`: for the aggregations that compare crime across deprivation bands.
- `hotspot`: if the dashboard filters by predicted hotspot.

## To record here as work happens

- Final document schema with one real example document.
- Indexes created and why.
- Import method (bulk insert from the Spark Parquet output) and timing.
- Example queries with what they return: a find by LSOA, and an aggregate of average crime rate per IMD decile.
- Problems hit and fixes.
