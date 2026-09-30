# 07 Results

## Rule for this file

Every finding needs at least two sentences: what the pattern is, and why it happens. The marker rewards explanation, not description. A chart with no explanation scores poorly.

## Finding 1: deprivation and crime rate are strongly, monotonically linked

Chart: `figures/average_crime_rate_by_iod2025_decile.png` and `figures/crime_rate_vs_iod2025_score.png`.

Average crime rate falls in a clean, unbroken line from the most deprived decile to the least deprived, no bumps, no reversals:

| IMD decile (1 = most deprived) | Avg crimes per 1,000 residents |
|---|---|
| 1 | 540.3 |
| 2 | 431.2 |
| 3 | 389.4 |
| 4 | 330.6 |
| 5 | 275.5 |
| 6 | 233.6 |
| 7 | 215.3 |
| 8 | 191.0 |
| 9 | 156.4 |
| 10 | 112.9 |

The most deprived decile has a crime rate 4.8 times the least deprived decile. Why: deprivation domains that feed the overall IMD score (income, employment, education, housing) correlate with the conditions criminology links to crime opportunity and motive, lower guardianship (fewer people able to invest time/money in home and community security), higher unemployment and idle time, and concentrated poverty. This is association, not proof of causation, other unmeasured factors like population density and policing intensity move together with deprivation and are not separately controlled here (see `docs/08`). Worth noting: about 9.3% of the overall IMD score is itself built from a Crime domain (see the methodological note in `docs/08`), so a small part of this relationship is definitional rather than purely socioeconomic, still, a 4.8x gap is far larger than that 9.3% alone could produce.

## Finding 2: the extreme outliers are a footfall problem, not a deprivation problem

Chart: `figures/crime_rate_lsoa_map.png`, cross-checked against raw output.

The 8 LSOAs with the highest crime rates (up to 19,159 per 1,000 residents, against a national median of 204) are almost entirely central Westminster (4 separate LSOAs), Birmingham city centre, City of London, and one LSOA near Heathrow in Hillingdon. Their IMD deciles are mid-range (3-8), not uniformly deprived. Why: these are commercial, nightlife, and transport-hub areas with small resident populations but very high day and night footfall, shoppers, tourists, commuters, and travellers who are not counted in the "per resident" denominator but are still present and can be victims or offenders. This is a genuine limitation of a resident-population-normalised rate, not a data error, and it means the extreme tail of the crime-rate distribution should not be read as "most dangerous places to live," it largely reflects "busiest places," a distinct finding worth calling out explicitly since a naive read of the map would over-state danger in these specific areas.

## Finding 3: crime has a clear seasonal pattern, and a modest downward drift

Chart: `figures/monthly_crime_trend.png`.

Comparing the first 18 months of the archive to the last 18 months, national recorded crime is down about 4.6%. More striking than the overall drift is the seasonal shape: summer months (June, July, August) average 495,000-515,000 recorded crimes nationally, winter months (December, January, February) average 415,000-435,000, a 15-20% swing that repeats every year in the data. Why: this matches routine activity theory, one of the most consistent findings in criminology. Warmer months mean more people outdoors, more social and nightlife activity, more property left in accessible places (cars, gardens, bikes), and more opportunity for the offences that dominate the archive (violence and anti-social behaviour, both concentrated in social/outdoor settings). This is a genuinely explainable pattern, not noise, and it is worth showing precisely because it demonstrates the project extracting a "why," not just a "what."

## Finding 4: what actually gets recorded

Chart: `figures/national_crime_category_breakdown.png`.

Violence and sexual offences make up 34.4% of all recorded crime nationally, more than the next two categories combined (anti-social behaviour 15.9%, shoplifting 8.1%). This matters for interpreting Finding 1: the deprivation-crime link is not being driven by one narrow category, violence and anti-social behaviour, the two largest categories, are also the two most closely tied in criminology literature to the socioeconomic conditions IMD measures (income, employment, and to a lesser extent, education). A category-by-decile breakdown would sharpen this further, flagged as a "with more time" item in `docs/08`, not yet done.

## Finding 5: the hotspot model works, with an honest trade-off, not a clean win

Chart: `figures/logistic_regression_confusion_matrix.png`, `figures/random_forest_confusion_matrix.png`. Source: `figures/hotspot_model_metrics.json`, full detail in `docs/05_machine_learning.md`.

Both models clearly beat guessing, hotspots are 25% of LSOAs by construction (top quartile), so "always predict not-hotspot" would hit 75% accuracy with zero recall, both models beat that on the metric that matters, F1 on the hotspot class (logistic regression 0.670, random forest 0.575). Why report both rather than picking a winner: logistic regression catches 80% of true hotspots but with more false alarms (precision 0.578), random forest is more precise when it does call something a hotspot (0.700) but misses over half of the real ones (recall 0.487). Which model "wins" depends entirely on whether the intended use case cares more about not missing hotspots or not over-flagging safe areas, a real, defensible trade-off to present as-is rather than manufacturing a single "best" number.

## Finding 6: the model leans hardest on the overall score, income, and health

Chart: `figures/random_forest_feature_importance.png`. Source: `hotspot_model_metrics.json`, `feature_importance` key.

Ranked by importance: overall IMD score (0.151), income score (0.103), health score (0.090), employment score (0.086), living environment (0.083), housing (0.080), education (0.074), population (0.070), then the decile-transformed versions of each domain trail behind their raw score counterparts throughout. Why report this: income and employment leading makes sense and matches the IMD's own weighting logic, but health ranking above employment is a genuinely interesting result worth calling out on the slide rather than skipping past, it suggests area-level health deprivation carries real independent signal about crime hotspot status beyond what income and jobs alone capture, plausibly through the same underlying disadvantage (chronic illness, disability, reduced capacity to work) rather than health causing crime directly. Also worth noting: raw scores consistently beat their own decile versions as predictors, deciles throw away information by bucketing, and the model loses some signal doing that, this is a real methodological point, use the score fields, not deciles, when the goal is prediction rather than plain-language communication.

## Finding 7: Greater Manchester Police is not in this archive, and it matters

Chart: `figures/local_authority_ranking.png` (Greater Manchester deliberately excluded, see below).

Building a local-authority ranking table surfaced something bigger than a chart choice: all 10 Greater Manchester boroughs (Oldham, Bury, Tameside, Trafford, Salford, Rochdale, Bolton, Wigan, Manchester, Stockport) showed near-zero crime rates, 1.8 per 1,000 residents against a national average of 287. Checked directly: there is no Greater Manchester Police street-level file anywhere in the 36-month archive, not a filtering bug, the source data genuinely does not include this force. Why this matters for the presentation: without catching this, the honest-looking finding "safest places in England" would have been ten Greater Manchester boroughs, which is simply wrong and the kind of error a marker familiar with UK crime data could catch immediately. Full detail and the fix (exclude Greater Manchester from any ranking, caveat it on the map) in `docs/08_limitations.md`.

## Honest framing to keep

An association between deprivation and crime is not proof that deprivation causes crime. State findings as association and prediction, not cause. Carried into `docs/08`.
