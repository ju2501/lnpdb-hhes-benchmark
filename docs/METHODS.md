# Methods and interpretation

## Data provenance

The four files under `data/LNPDB_for_LiON/single_split/` come from
`evancollins1/LNPDB` commit `fc7c38933b445eb54985014f2b8917606462eec1`:
`test.csv`, `test_results.csv`, `test_metadata.csv`, and `test_extra_x.csv`.
Their exact URLs, SHA-256 hashes, Git blob hashes, and feature order are in
`src/lnpdb_hhes/snapshot.json`. Source file bytes, including line endings, matter.

The supplied predictions are evaluated without executing a checkpoint.
`summary.json` records `model_executed=false` to make this distinction explicit.

## Alignment and units

Files must match the pinned hashes. The loader additionally checks row counts,
SMILES alignment, target agreement with metadata, unique LNP IDs, finite numeric
values, cargo one-hot encoding, and feature-column order. The features file has
no independent row identifier; its alignment is secured by using the exact
upstream bytes, not by reconstructing a join on nonunique SMILES.

The original source describes log transformation where appropriate followed by
standardization within publication and delivery context. Source
`Experiment_value` is used as provided. RMSE is in that standardized target
space. It cannot be compared directly with FACS-positive percentages or raw
luminescence. See the [source paper](https://doi.org/10.1038/s41467-026-68818-1).

## Public benchmark

Overall Pearson, Spearman, and RMSE are descriptive reproduction metrics. Counts
are reported by cargo; metrics are also computed per `Experiment_ID` and cargo.
An experiment ID can encompass multiple contexts. These first-pass study
metrics do not establish assay-matched comparisons.

Correlations are omitted for fewer than three observations or constant vectors.
The study figure shows only groups with at least five rows, while the CSV retains
all groups and explicit missing-correlation status. A display threshold of five
is not a statistical adequacy threshold.

The original split is described as amine-based. An `args.json` field with
`split_type=random` does not redefine the provenance of already supplied train,
validation, and test files. This release does not construct new splits.

## Candidate construction

Grouping uses `Experiment_ID`, `IL_SMILES`, and every supplied feature column
except the ratios allowed to change. The default allows changes to
`IL_molratio`, `HL_molratio`, `CHL_molratio`, and `PEG_molratio`.
The stricter mode allows only helper and cholesterol ratios to change.
Groups need at least two distinct composition vectors.

Matching is exact; no tolerance is introduced for floating-point ratio values.
Group IDs are deterministic hashes of the matching key and mode. Table row
order does not determine group identity. The snapshot commit remains part of
the analysis provenance; IDs are not universal experimental identifiers.

Candidate generation does not filter on observed outcomes or model agreement.
However, the dataset and question were chosen retrospectively. Missing assay,
time, preparation details, or batch information can invalidate a proposed
comparison even if the encoded features match.

## Curation and evaluation

Copy `curation_template.csv` to a separate file before editing it. Generated
templates may be regenerated, but the evaluator does not edit your curation file.
Use `decision=include` only after documenting a source, a shared readout method,
readout time in hours, and a comparability rationale. If a group contains a
mixture of methods or times, exclude it and design a finer grouping separately.
The tool cannot independently verify the curator's scientific judgment.

Curated evaluation currently accepts templates from the default `all` mode.
Repeated identical compositions within an included group are rejected: deciding
how to aggregate experimental repeats requires an explicit experimental design.

For every distinct pair in an included group:

1. If the absolute observed difference is at or below the observed tie tolerance,
   exclude that pair from directional scoring.
2. Otherwise, assign 1 for a correct predicted direction, 0 for an incorrect
   direction, and 0.5 for a predicted tie.
3. Average within a group, then average the available group scores equally.

Tolerances default to 0 in source standardized units. Choose justified tolerances
before examining performance, and report them. Counts of ties and informative
pairs are retained. If every observed pair is tied, the score is missing.
Spearman is also reported for groups with at least three nonconstant values.

Pairs share observations and groups can share lipids or an experiment. No
binomial significance tests or naive pair-level confidence intervals are
provided. These scores are descriptive, not evidence of independent biological
replication. A group with two formulations cannot support a useful correlation
claim on its own.

## Limits of extension to HHES

Metadata assessment never declares a new sample prediction-ready. It does not
validate molecular structure, derive an unknown PEG identity, calibrate a model
to FACS, or replace a missing model category. In particular, do not map Jurkat to
HEK293T or silently encode an unsupported cell as all zeroes.

The model's molar-ratio inputs use percentage-scale values. Four components in
the local lab template must sum to 100 within 0.01 percentage points. Dose basis
and IL-to-nucleic-acid mass-ratio definitions remain explicit source-review
requirements. FACS events, wells, and independent manufacturing batches are
different units of replication.

Future nearest-neighbor error analysis must search only the training pool for
the model being evaluated. A test point or its held-out study must not enter its
own reference pool. New features, fine-tuning, or changes selected using current
test results require a separate evaluation set for subsequent improvement claims.
