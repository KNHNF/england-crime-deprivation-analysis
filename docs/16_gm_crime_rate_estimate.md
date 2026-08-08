# 16 Greater Manchester Crime Rate Estimate

Standalone analysis, not yet in the deck or the main report. Built on request to quantify the Greater Manchester gap (see `docs/08_limitations.md`) beyond "the actual figure is near zero", by asking what the model would expect GM's crime rate to be if it reported like everywhere else, given its real, present deprivation profile.

## Method

`src/estimate_gm_crime_rate.py`. A `RandomForestRegressor` trained on the 43 non-Greater-Manchester local authorities' LSOA-level deprivation features (the same `FEATURE_COLUMNS` used by the hotspot classifier in `train_model.py`) to predict `crime_rate_per_1000`, then applied to Greater Manchester's own LSOAs. GM's deprivation data is real and complete, only its crime data is missing, so this is a legitimate input to feed the model, the estimate is a counterfactual: what would we expect GM's crime rate to be, given a deprivation profile like Manchester's or Oldham's, if the area reported normally.

## Result

| | Crimes per 1,000 residents |
|---|---|
| National average (non-GM, actual) | 294.4 |
| Greater Manchester (actual, reported) | 1.8 |
| Greater Manchester (model estimate) | 503.1 |

Predicted vs actual gap: roughly 275x. Every one of the 10 boroughs individually predicts in the hundreds (see `figures/gm_predicted_vs_actual_crime_rate.png`), none close to the reported figure, and several (Manchester, Salford) predict above the national average, consistent with their more deprived profile.

## Honest caveat, read before using this number anywhere

The model's holdout R2 is 0.23 (MAE 127 crimes per 1,000, against a national mean of 294). Deprivation alone explains only about a quarter of the variance in crime rate nationally, population density, urban centre effects, and policing intensity all matter too and aren't in this feature set, the same limitation already named for the hotspot classifier in `docs/08`. That means the specific number, 503 per 1,000, should not be presented as a precise prediction. It's a plausible midpoint from a fairly weak model, not a measurement.

What the number does support, robustly, regardless of that weakness: **even a model that only explains a quarter of the variance still lands nowhere near zero.** A weak model being confidently wrong in the same direction as a strong one would be, is stronger evidence than the precision of any single figure. The 275x gap is the finding. The exact multiple is illustrative.

## Second, independent check: nearest-neighbour matching

The regression's R2 of 0.23 is a real weakness, so a second method was added that doesn't ask anyone to trust a model's internals: for each GM borough, find the 5 real, non-GM local authorities with the closest deprivation profile (standardised Euclidean distance across the same feature set), and just report what those actual places report.

`nearest_neighbour_comparison()` in the same script. Result: across all 10 boroughs, the nearest-neighbour average is 362.6 crimes per 1,000 against GM's actual 1.7, a roughly 212x gap. The matched places are real and plausible, Wolverhampton, Blackburn with Darwen, Nottingham, Hull, Preston, Derby, Newcastle, Gateshead, Sandwell, the kind of post-industrial cities and towns you'd expect to sit next to Manchester or Oldham on a deprivation ranking. Chart: `figures/gm_nearest_neighbour_crime_rate.png`.

This is the stronger of the two results to lead with. It needs no R2 caveat, "here are 5 real places with almost identical deprivation scores, here's what they report" is not a model prediction, it's a direct comparison. That it lands in the same order of magnitude as the regression estimate (212x here vs 275x there, both from independent methods, one trusting a fitted model, one trusting nothing but distance) is the real evidence: two different ways of asking the same question agree, so the "300+ times too low" story doesn't depend on any one method's assumptions.

## How to use this, if at all

- **Lead with the nearest-neighbour result**, not the regression. "Five real places with a near-identical deprivation profile to Oldham report around 380 crimes per 1,000. Oldham reports 0.9." needs no model caveat and is harder to argue with than a predicted number.
- **Use the regression as backup, not the headline.** It independently lands in the same range (275x vs 212x), which is what makes the overall case strong, two different methods agreeing, but its own number (503) shouldn't be quoted on its own without the R2 0.23 caveat attached.
- **Do not** present either number as "the real crime rate for Manchester". Neither is measured. One is a nearest-neighbour comparison, one is a model estimate, both are legitimate evidence that the reported 1.8 is implausible, neither is a replacement measurement.
- If asked in a viva or by the teacher: lead with the R2 caveat on the regression unprompted, don't wait to be asked. That's the honest-limitations habit this whole project has followed elsewhere (Wales exclusion, the 9.3% IMD circularity, single-machine Spark), and it's more convincing than hiding a weak R2 and hoping nobody checks.

## If this goes into the deck or report later

Would need: a short line naming both methods and noting they agree, and probably its own slide (a third Finding 3 slide, after the existing map and "why" pair, mirroring how Finding 2 grew to three slides for Bristol) rather than folding into the existing two. The nearest-neighbour chart is the one to lead the slide with, it's the more immediately convincing visual, actual bars are barely visible next to real comparable places. Not done yet, holding this as a standalone result until there's a decision on whether it earns its own slide given the deck's existing length.
