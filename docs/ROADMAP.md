# Scope and next milestones

## Implemented in v0.1

Pinned public data retrieval, descriptive prediction audit, same-IL candidate
matching, a manual curation gate, descriptive curated evaluation, local lab
metadata checks, English documentation, and reproducible public figures.

The committed candidate set has not been scientifically curated. No curated
performance score is reported as a real research result. Synthetic fixtures are
used only to test evaluator behavior.

## Next: source-reviewed formulation benchmark

- Verify the candidate groups against `JW_2024` study records and assay context.
- Record inclusion/exclusion decisions and source locations before evaluating
  selected groups. Retain excluded and unresolved groups.
- Add compatible public comparisons from other studies, without pooling
  incompatible labels or presenting repeated rows as independent experiments.
- Preserve a separate evaluation set if model changes are selected using these
  results.

## Next: LiON execution and application domain

- Reproduce predictions by executing the exact checkpoint in an isolated
  Chemprop 1.7.0 environment, separately from this modern analysis environment.
- Build a tested input adapter for its exact feature order and preprocessing.
- Verify HHES and PEG chemical identity before custom inference.
- Evaluate structural/contextual distance using checkpoint-specific training
  reference pools. Do not report an uncalibrated similarity score as probability.
- Add pre-existing whole-study-held-out results and compare compatible targets.

## Experimental case-study integration

- Link permitted experimental records to explicit chemical, batch, assay, and
  readout metadata; retain original QC and measurement scales.
- Define which public comparisons match the intended experimental question and
  record mismatches in cargo, model system, timing, or formulation context.
- Verify the input adapter and checkpoint execution before adding custom HHES
  predictions. Metadata completeness alone is not scientific validation.
- Evaluate held-out formulations and report independent manufacturing batches
  separately from technical measurements. Limited formulation coverage supports
  exploratory case comparisons, not an optimum or a cross-cargo accuracy claim.

## Optional later work

- Compare a simple baseline and LiON on the same target and split.
- Compare AGILE only after matching its checkpoint inputs and evaluation data.
- Introduce additional physical features only with compatible training data and
  an independent evaluation design.
- Treat Martini simulations as a separate mechanistic project, requiring HHES
  mapping/parameter validation; membrane behavior is not a direct FACS prediction.

No new deep-learning training or molecular-dynamics run is required to complete
the first public analysis release.
