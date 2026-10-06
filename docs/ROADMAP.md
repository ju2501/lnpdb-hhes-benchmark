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

## Thesis connection

A suitable undergraduate thesis can combine experimental HHES formulation
comparison, a reproducible public-model analysis, and a discussion of which
parts of the public evidence apply to the local experiment.

The local experimental section should retain batch-specific QC and consistent
FACS definitions. The computational section can report reproducibility,
coverage, and source-reviewed composition comparisons. Disagreement or limited
applicability is a valid finding when its basis is documented.

Two local formulations support an exploratory case comparison; they do not
validate an optimum or robust predictive accuracy. A future mRNA sample adds a
case, and multiple independent batches add replication. Neither alone creates a
large multi-formulation dataset or establishes transfer to pDNA.

## Optional later work

- Compare a simple baseline and LiON on the same target and split.
- Compare AGILE only after matching its checkpoint inputs and evaluation data.
- Introduce additional physical features only with compatible training data and
  an independent evaluation design.
- Treat Martini simulations as a separate mechanistic project, requiring HHES
  mapping/parameter validation; membrane behavior is not a direct FACS prediction.

No new deep-learning training or molecular-dynamics run is required to complete
the first public analysis release.
