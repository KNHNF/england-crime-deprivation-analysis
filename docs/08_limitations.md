# 08 Limitations


Naming limitations honestly gains marks. Pretending there are none loses them.

## Data limitations

- Recorded crime is not committed crime. Police.uk shows crimes that were reported and recorded. Under-reporting varies by crime type and by area, so differences partly reflect reporting behaviour, not just underlying crime.
- Location fuzzing. Police.uk snaps each crime to an approximate point for privacy, which introduces small geographic error at LSOA edges.
- Time gap. IMD is 2019, the crime archive is more recent. Deprivation may have shifted in some areas over that gap.
- LSOA boundary effects. A busy town centre LSOA with few residents can look extreme on a per-person rate. Note where this distorts the picture.

## Method limitations

- Correlation, not causation. A deprivation-crime association is not proof that deprivation causes crime. Other factors (density, opportunity, policing) are not fully controlled.
- Single-machine Spark. We run Spark on one machine, so we demonstrate the distributed model and the code scales, but not a real cluster. Say this plainly rather than implying a cluster.
- Any sampling or exclusion decisions (forces or months dropped) reduce coverage. List them here.

## What we would do with more time

- Add temporal analysis: how crime moved across the archive years, not just a snapshot.
- Bring in population density and land-use to separate density effects from deprivation.
- Test the model on a held-out region rather than a random split, to check it generalises geographically.
