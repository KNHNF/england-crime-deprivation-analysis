# 10 EDA and Build Log

Owner: Karan.

Real, dated build history. Earlier drafts of this file described the plan before anything ran, this version records what actually happened, in order, including the mistakes.

## What we checked first

The raw police.uk extract covers June 2023 to May 2026 across 1,563 street-level CSV files (paired with an equal number of separate outcomes-only files, see the bug below). Each street row has a month, crime type, LSOA code, approximate location, reporting force, owning force, and outcome category.

The IoD 2025 File 7 dataset gives LSOA-level deprivation scores, deciles, domain scores, local authority fields, and population denominators. Confirmed by web search that IoD 2025 (published 30 October 2025) is genuinely the current official edition of the English Indices of Deprivation, not a placeholder, so this is the right dataset to be using rather than the originally planned IMD 2019.

## Why the output is at LSOA level

The crime data is record-level, but the deprivation data is LSOA-level. Aggregating to one row per LSOA keeps the join valid and makes the output usable for MongoDB, maps, and machine learning.

## Environment issues hit, in order

1. **Java 25 incompatibility.** Spark/Hadoop failed with `UnsupportedOperationException: getSubject is not supported`. Fixed by installing Java 17.0.19 and making it the system default.
2. **Windows winutils.exe/hadoop.dll missing.** PySpark on Windows needs Hadoop's native Windows file-listing shim, without it Spark crashes with `UnsatisfiedLinkError` just listing the CSV directory, before any of our code even runs. Fixed by downloading Hadoop 3.3.6's `winutils.exe` and `hadoop.dll`, setting `HADOOP_HOME`, and copying `hadoop.dll` into `System32`. Neither of these is specific to this project, they hit any PySpark-on-Windows setup.

## Real pipeline bugs found and fixed

Found while validating the pipeline logic against real data before committing to a full run (initial validation happened in a resource-constrained Cowork sandbox, which is why small samples were used first, full detail also in the repo's local `GOTCHAS.md`).

1. **Outcomes files contaminating the crime read.** police.uk ships two file types per force per month: `*-street.csv` (crime incidents, what this pipeline needs) and `*-outcomes.csv` (a separate file tracking case outcomes only, with a different, incompatible column layout, no `Crime type` column at all). The original read used `recursiveFileLookup` with no filename filter, pulling in both types. Spark applied the first file's header to every file positionally, so outcome files' trailing columns landed under the wrong names, corrupting `crime_type_raw` and crashing the category pivot with `AMBIGUOUS_REFERENCE`. Fixed with `.option("pathGlobFilter", "*-street.csv")`.
2. **86% of LSOA rows failing to join against IMD.** Looked like a join bug, was not one. The IoD 2025 file only covers English LSOAs (`E01...`). The archive includes four Welsh forces (Dyfed-Powys, Gwent, North Wales, South Wales) that report against Welsh LSOA codes (`W01...`), which can never match an England-only deprivation table. Fixed by scoping the crime data to English LSOAs before aggregation. This makes the analysis England-only, logged as a limitation in `docs/08`, not silently dropped.

## Full national run, real numbers

Completed successfully on 2026-07-10/11 after the environment fixes above:

```
raw_crime_rows:      17,837,130
clean_crime_rows:    16,249,125   (after cleaning and the England-only filter)
output_lsoa_rows:    32,944       (essentially all English LSOAs)
unmatched_lsoa_rows: 74           (0.22%, down from 86% before the two bug fixes)
date range:          2023-06-01 to 2026-05-01
```

`total_crimes` and `crime_rate_per_1000` in the output are 3-year cumulative figures across the whole archive, not monthly, say this plainly on the slide.

## EDA findings, with real numbers

- **Crime rate distribution:** mean 493 crimes per LSOA over 3 years (287 per 1,000 residents), median 204 per 1,000, but heavily right-skewed, max 19,159 per 1,000.
- **The outlier LSOAs explain themselves once you look at them.** The top 8 by crime rate are almost entirely central Westminster (four separate LSOAs), Birmingham city centre, City of London, an LSOA near Heathrow in Hillingdon, and one in Newham. These are commercial, nightlife, and transport-hub areas: very small resident populations, huge day and night footfall. "Crimes per resident" massively overstates personal risk there, since most of the people present (workers, shoppers, tourists, transiting passengers) are not counted in the denominator. This is the actual "why" behind the extreme tail of the distribution, not a data error, name it on the slide.
- **National crime category breakdown** (`figures/national_crime_category_breakdown.png`): violence and sexual offences dominate at 34.4% of all recorded crime, followed by anti-social behaviour at 15.9%, shoplifting 8.1%, criminal damage and arson 7.3%, other theft 7.1%, public order 6.9%, vehicle crime 5.7%. This is useful context before showing the deprivation link, since "crime" is not one uniform thing, and different categories likely relate to deprivation differently (worth a caveat if time allows, not yet broken down by decile).
- **Deprivation link:** see `figures/average_crime_rate_by_iod2025_decile.png` and `figures/crime_rate_vs_iod2025_score.png` for the main research-question evidence, real chart, not yet narrated in depth here, that belongs in `docs/07_results.md`.

## Modelling, real result

Hotspot defined as top quartile of LSOAs by `crime_rate_per_1000` (threshold 335.1 per 1,000). Both models trained on the real 32,870-row output (74 unmatched rows excluded, same as the join issue above):

| Model | Accuracy | Precision (hotspot) | Recall (hotspot) | F1 |
|---|---|---|---|---|
| Logistic regression | 0.804 | 0.578 | 0.798 | 0.670 |
| Random forest | 0.820 | 0.700 | 0.487 | 0.575 |

Real trade-off, not a clean win for either model: logistic regression catches more true hotspots but with more false alarms, random forest is more precise when it flags something but misses over half the real hotspots. Full detail and interpretation in `docs/05_machine_learning.md`.

## A methodological point worth being upfront about

The overall IMD score used as a model feature is a weighted composite of seven domains (Income and Employment 22.5% each, Education and Health 13.5% each, Crime, Barriers to Housing, and Living Environment 9.3% each, confirmed against the official IoD technical report methodology). Crime is one of those seven inputs, so using the overall `imd_score` to predict this project's crime rate is not fully independent, roughly 9.3% of the predictor is itself built from a crime measure (albeit for a different reference period). The standalone crime sub-domain fields are deliberately excluded from the model's feature list for this reason, but the overall composite still carries a sliver of it. Full detail in `docs/08_limitations.md`.

## What this shows in the presentation

The project shows the full workflow: raw national CSV archive (17.8M rows), Spark processing, MongoDB storage, visual EDA with genuine explanations (not just description), and a machine learning task linked to the research question, with honest trade-offs rather than a cherry-picked best result.

The honest point to keep making: an association between deprivation and crime is not proof that deprivation causes crime.

## Second EDA pass, 2026-07-11: feature importance, local authority ranking, and a serious data gap caught

- **Feature importance** (`figures/random_forest_feature_importance.png`): overall IMD score leads (0.151), then income (0.103), then health (0.090), ahead of employment (0.086). Health outranking employment is a genuinely interesting result, not just expected confirmation. Raw domain scores consistently beat their decile-transformed versions, deciles throw away predictive information.
- **Interactive deprivation map** added (`figures/deprivation_heatmap.html`), same zoomable street-level basemap as the crime heatmap, with a layer toggle so both live in one file.
- **Local authority ranking** (`figures/local_authority_ranking.png`) surfaced a real problem before it became an embarrassing one: all 10 Greater Manchester boroughs showed near-zero crime rates. Checked directly, there is no Greater Manchester Police file in any of the 36 monthly folders, the force is simply absent from this archive, not a pipeline bug. Without catching this, the "safest places in England" finding would have been ten Greater Manchester boroughs, which is wrong and exactly the kind of gap someone familiar with UK police data could catch immediately. Fixed by excluding Greater Manchester from the ranking and documenting it prominently in `docs/08_limitations.md`, this needs a spoken caveat whenever the crime rate map is shown too, since the map itself can't visually distinguish "genuinely low crime" from "no data reported."
- Population: already used, but only as a single mid-2022 snapshot (from the IMD file), not a multi-year time series. A true year-by-year population history would need separate ONS mid-year estimates downloaded per year, flagged as a possible future addition, not done, likely not worth the effort for a 12-13 minute video.
