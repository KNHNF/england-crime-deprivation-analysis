# 08 Limitations


Naming limitations honestly gains marks. Pretending there are none loses them.

## Data limitations

- Recorded crime is not committed crime. Police.uk shows crimes that were reported and recorded. Under-reporting varies by crime type and by area, so differences partly reflect reporting behaviour, not just underlying crime.
- Location fuzzing. Police.uk snaps each crime to an approximate point for privacy, which introduces small geographic error at LSOA edges.
- Time gap. The deprivation file in use is IoD 2025 (published 30 October 2025, superseding IMD 2019 as the official edition), which is a good match for the crime archive's June 2023 to May 2026 window, better than the original IMD 2019 plan. Confirmed via gov.uk that IoD2025 is genuinely the current edition, not a placeholder or mislabelled file. One thing to check: MHCLG issued a v2 correction in November 2025 to some IoD2025 files (an LSOA-to-LAD lookup error affecting one LSOA in West Northamptonshire), worth confirming the local copy is the corrected version, though the impact of a single mislabelled LSOA on a 32,944-row analysis is negligible either way.
- LSOA boundary effects. A busy town centre LSOA with few residents can look extreme on a per-person rate. Confirmed directly in this data: the 8 highest crime-rate LSOAs (up to 19,159 crimes per 1,000 residents, versus a median of 204) are almost all central Westminster, City of London, and Birmingham city-centre LSOAs, plus one likely Heathrow-adjacent LSOA in Hillingdon. These are commercial, nightlife, and transport-hub areas with very small resident populations but huge day/night footfall, so "crimes per resident" massively overstates the danger to anyone who actually lives there. Name this on the slide rather than letting the chart imply Westminster is uniquely crime-ridden per capita.
- England only. The deprivation file covers English LSOAs only. The crime archive also includes Welsh forces (Dyfed-Powys, Gwent, North Wales, South Wales), which report against Welsh LSOA codes that cannot join to an England-only deprivation index. These are excluded from the join, so this analysis is England-only, not England and Wales. Say this on the slide rather than letting a marker notice on their own.

## Data limitations (continued): Greater Manchester Police is absent from the archive

Discovered 2026-07-11 while building a local-authority ranking table. Checked all 36 monthly folders directly: there is no `*-manchester-street.csv` file for Greater Manchester Police in any month, June 2023 to May 2026. Confirmed via the processed output too: the 830 LSOAs across Greater Manchester's 10 boroughs (Oldham, Bury, Tameside, Trafford, Salford, Rochdale, Bolton, Wigan, Manchester, Stockport) show a combined 2,701 crimes over 3 years for roughly 2.8 million people, an average rate of 1.8 per 1,000 residents against a national average of 287 per 1,000, about 160 times lower than expected. This is a genuine gap in the source archive (Greater Manchester Police has a documented history of data-quality issues with its crime recording system affecting its police.uk submissions), not a pipeline bug, the same pattern the England/Wales LSOA-code issue followed: don't silently drop it, name it.

Practical implication: any ranking of "safest" or "lowest crime" local authorities is invalid unless Greater Manchester's boroughs are explicitly excluded first, otherwise all 10 of them wrongly appear at the very top of a "safest places" list. The crime-rate map and heatmap also show Greater Manchester as artificially cold, this needs a spoken caveat when either is shown, since the map itself doesn't visually distinguish "genuinely low crime" from "no data."

## Method limitations

- Correlation, not causation. A deprivation-crime association is not proof that deprivation causes crime. Other factors (density, opportunity, policing) are not fully controlled.
- Mild circularity in the overall IMD score as a predictor. The IMD/IoD overall score is a weighted composite of seven domains: Income and Employment at 22.5% each, Education and Health at 13.5% each, and Crime, Barriers to Housing, and Living Environment at 9.3% each (confirmed against the official IoD2019/IoD2025 technical report methodology). Crime is one of the seven inputs that builds the overall `imd_score` used as a model feature, so predicting our crime rate from the overall IMD score is not fully independent, about 9.3% of the predictor is itself built from a crime measure (for a different reference period than this project's archive). The standalone crime sub-domain (`iod_crime_score`/`iod_crime_decile`) is deliberately excluded from the model's feature list for this reason, but the overall score still carries a sliver of it. Worth a sentence on the slide, and a real fix with more time: re-derive a "crime-domain-excluded" composite from the six non-crime domains using the published weights, and compare model performance against that instead.
- Single-machine Spark. We run Spark on one machine, so we demonstrate the distributed model and the code scales, but not a real cluster. Say this plainly rather than implying a cluster.
- Any sampling or exclusion decisions (forces or months dropped) reduce coverage. List them here.

## What we would do with more time

- Add temporal analysis: how crime moved across the archive years, not just a snapshot.
- Bring in population density and land-use to separate density effects from deprivation.
- Test the model on a held-out region rather than a random split, to check it generalises geographically.
