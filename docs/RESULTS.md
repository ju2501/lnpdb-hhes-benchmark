# Interpreting the public results

This guide interprets the committed outputs in `reports/`. A default local run
writes the corresponding outputs under `outputs/`, as described in
[USAGE.md](USAGE.md). All results below concern the four pinned files from
[`evancollins1/LNPDB`, commit `fc7c389`](https://github.com/evancollins1/LNPDB/tree/fc7c38933b445eb54985014f2b8917606462eec1/data/LNPDB_for_LiON/single_split),
not the full database or new experimental samples.

## What the workflow establishes

The current workflow verifies public input files, evaluates the predictions
already supplied with them, and identifies candidates for formulation-level
comparison. Source review and curated comparative evaluation follow that audit.
Executing LiON for new samples is a separate, unimplemented extension.

`model_executed=false` in the benchmark summary is expected. Successful tests or
CI establish that these computations run as specified; they do not validate
efficacy prediction for HHES or another new experimental setting.

## 1. Overall agreement

Source: [benchmark summary](../reports/public_snapshot/summary.json).

| Quantity | Value | Interpretation |
|---|---:|---|
| Test rows | 2,164 | Supplied observations, not independent biological replicates |
| Pearson correlation | 0.481876 | Positive linear association between observed and predicted targets |
| Spearman correlation | 0.444236 | Positive association between their rankings |
| RMSE | 0.911933 | Error magnitude in the source's standardized target units |

Neither correlation is a percentage accuracy or a predicted transfection rate.
RMSE is not a percentage-point error in FACS. These pooled statistics combine
multiple studies and contexts; they cannot identify how much of the association
comes from within-context formulation effects. Baseline comparisons and a
relevant independent evaluation are needed before claiming predictive utility
for a new use case. Target normalization and split provenance are described in
[METHODS.md](METHODS.md).

## 2. Cargo coverage and performance

Source: [cargo metrics](../reports/public_snapshot/cargo_metrics.csv).

| Cargo | Rows | Experiment IDs | Pearson | Spearman | RMSE |
|---|---:|---:|---:|---:|---:|
| mRNA | 1,659 | 26 | 0.4659 | 0.4378 | 0.9418 |
| pDNA | 16 | 1 | 0.1527 | 0.0426 | 0.7441 |
| siRNA | 489 | 4 | 0.5629 | 0.4818 | 0.8082 |

The pDNA subset consists entirely of `LL_2012`. Its observed rank association is
near zero, so this subset provides little support for using the predictions to
rank its pDNA formulations. With only 16 rows from one experiment ID, this is
not a general estimate of pDNA performance and says nothing directly about HHES.

A smaller pDNA RMSE than mRNA RMSE does not establish better pDNA prediction:
target distributions, experimental contexts, and coverage differ. Similarly,
cargo-level differences are confounded with studies, lipids, and assays; they
do not isolate a causal effect of cargo or demonstrate transfer across cargos.

## 3. Why inspect study-level results?

Source: [study metrics](../reports/public_snapshot/study_metrics.csv).

Performance varies by experiment ID. For example, `JW_2024` has 285 mRNA rows and
Spearman correlation 0.5582. `ZL_2022` has Spearman correlation 0.8514 but RMSE
2.2786 across 16 rows: agreement in ranking can coexist with substantial errors
in target magnitude. Neither example is a newly study-held-out validation.

Do not select only favorable studies. Report sample sizes and read the entire
table. Correlations are omitted for fewer than three rows or constant vectors;
the plot displays groups with at least five rows. These thresholds prevent some
misleading displays but do not establish adequate sample size.

## 4. What do 69 candidate groups mean?

Source: [candidate summary](../reports/candidates/summary.json).

Exact feature matching identifies **69 groups, 213 rows, and 15 ionizable-lipid
SMILES**, all from the `JW_2024` mRNA experiment. Within each group the ionizable
lipid and recorded context are fixed, while at least two component-ratio vectors
differ. Multiple groups can share one lipid, and all share one experiment ID.

These are comparison candidates, not 69 independent experiments or 69 successful
model predictions. Unencoded assay, timing, or preparation differences may still
invalidate a comparison. The candidate count alone has no performance meaning.
The full `JW_2024` correlation also does not measure performance within these
same-lipid groups.

No curated direction score has been reported for the real candidate set. Review
source evidence first, then run `evaluate-curated`. For its direction score,
1 means every informative pair was ordered correctly, 0 means every such pair
was reversed, and predicted ties receive half credit. A score of 0.5 can arise
from constant predictions and is not evidence of useful discrimination. See
[METHODS.md](METHODS.md) for exclusions, tolerances, and averaging.

## 5. What does the stricter zero mean?

Source: [helper/cholesterol summary](../reports/helper_cholesterol/summary.json).

Holding both IL and PEG molar percentages fixed, while allowing only helper and
cholesterol percentages to vary, finds **zero groups** in this pinned test subset.
There is therefore no comparison set satisfying that exact rule here.

This does not show that changing helper/cholesterol ratios has no effect, that
the model failed such a comparison, or that no suitable data exist elsewhere in
LNPDB. Extending to other splits or studies requires separate coverage and
comparability checks.

## 6. Connection to an experimental case study

The present results establish a reproducible public benchmark and expose gaps
in the evidence available for a new case. A useful next step is to curate the
candidate comparisons and document how their cargo, chemical structures,
experimental system, and readout differ from the intended case study.

Keep experimental QC and expression measurements on their original scales.
Link them to computational findings through explicit comparability criteria,
not a conversion from standardized predictions to FACS percentages. Custom
inference requires verified chemical identities, compatible model inputs, and
checkpoint execution. Held-out cases and independent experimental batches are
needed for stronger claims of predictive performance.

The supported conclusion at this stage is reproducible evaluation with limited
evidence for cross-cargo application. HHES efficacy, optimal formulation, durable
expression, and genomic integration have not been established by these outputs.
