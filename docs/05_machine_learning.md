# 05 Machine Learning

Owner: Karan.

## Committed task: hotspot classification

Predict whether an LSOA is a crime hotspot (high crime) from deprivation and area features.

Why this one is the headline:
- Clear, honest metrics: accuracy, precision, recall, F1, and a confusion matrix. Easy to explain on a slide.
- Maps cleanly onto the dashboard: colour each area by predicted hotspot.
- Presentable by a non-specialist: high crime versus not, and how well the model tells them apart.

Definition of a hotspot: label the top quartile of LSOAs by crime rate (or crime count if no population data) as hotspots, the rest as not. Record the exact threshold here once chosen, because it changes the class balance.

Features to start with:
- IMD overall score and decile.
- IMD sub-domains if used (income, employment, education, health), since they may matter differently.
- Population and population density where available.
- Optionally region, to test whether deprivation still predicts once broad geography is accounted for.

Model: start with logistic regression as a readable baseline, then a random forest for a likely accuracy gain. Report both so the comparison is visible.

Evaluation note: hotspots are the minority class if we use the top quartile, so accuracy alone is misleading. Lead with precision, recall, and F1 on the hotspot class, and show the confusion matrix.

## Alternative 1: crime rate prediction (regression)

Predict the crime count or rate per LSOA from the same features. Metrics: MAE, RMSE, R2. This keeps more information than a binary label, but a continuous number is harder to present cleanly and easier to over-read. Good as a secondary result or an extension.

## Alternative 2: area clustering (unsupervised)

Cluster LSOAs by their crime and deprivation profile with k-means, then describe the clusters (for example high-deprivation high-crime, low-deprivation low-crime, and the off-diagonal cases that break the pattern). Strong for the map and for exploration, weaker as a headline because there is no accuracy number and the evaluation is qualitative.

## Recommendation

Commit to hotspot classification as the graded result. Run the regression as a short secondary to add depth. Use clustering only if there is time, as a descriptive map layer. Log the final decision and the reasoning here once made.

## To record here as work happens

- Features engineered and why.
- Train/test split approach (a simple random split is fine, note it).
- Models tried, chosen model, and why.
- Metrics with the numbers, not just their names.
- What the result actually means for the research question.
- Problems hit and fixes.
