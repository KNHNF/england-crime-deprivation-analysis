# 04 MongoDB

Status as of 2026-07-11: real run complete against Atlas, 32,944 documents loaded into the `Crime_England_Deprivation` collection (renamed from the originally planned `lsoa_crime_deprivation`, set via `MONGO_COLLECTION` in `.env`), plus a `monthly_crime_trend` collection with 36 documents. One real bug caught and fixed during the run: `first_month`/`last_month` are Python `date` objects in the Parquet output, and PyMongo cannot encode those directly, `normalise_document()` now converts them to ISO date strings before insert. Real document still to be pasted below, replacing the placeholder schema.

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
  "avg_longitude": -0.092,
  "avg_latitude": 51.514,
  "reported_by_forces": ["City of London Police"],
  "crimes_by_category": {
    "violence_and_sexual_offences": 40,
    "anti_social_behaviour": 33,
    "theft": 20
  },
  "outcomes_by_category": {
    "investigation_complete_no_suspect_identified": 50,
    "unable_to_prosecute_suspect": 10,
    "unknown": 8
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
- `crime_rate_per_1000`: for sorted hotspot and comparison queries.

## Current implementation

Code now exists in `src/load_mongo.py`.

Run after the Spark Parquet output exists:

```bash
python src/load_mongo.py
```

The loader reads `data/processed/lsoa_crime_deprivation`, upserts by `lsoa_code`, and creates the indexes listed above. It uses `ReplaceOne` bulk operations so the import can be rerun after the Spark output changes.

Example dashboard queries to test after import:

```python
collection.find_one({"lsoa_code": "E01000001"})
```

```python
collection.aggregate([
    {"$group": {"_id": "$imd_decile", "avg_rate": {"$avg": "$crime_rate_per_1000"}}},
    {"$sort": {"_id": 1}},
])
```

## To record here as work happens

- Final document schema with one real example document.
- Indexes created and why.
- Import method (bulk insert from the Spark Parquet output) and timing.
- Example queries with what they return: a find by LSOA, and an aggregate of average crime rate per IMD decile.
- Problems hit and fixes.
