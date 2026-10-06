# Usage and output files

Install with Python 3.10 or newer using the [README quick start](../README.md#quick-start).
The commands below run from the repository root with the virtual environment
activated. `python -m lnpdb_hhes` is equivalent to `lnpdb-hhes`.

## Run the public analysis

```bash
lnpdb-hhes fetch
lnpdb-hhes benchmark
lnpdb-hhes candidates
lnpdb-hhes candidates --vary helper-cholesterol --out outputs/helper_cholesterol
```

`fetch` downloads approximately 1.2 MB into `data/raw/single_split/` and checks
the pinned hashes. Subsequent analysis can run offline. Both `data/raw/` and
`outputs/` are ignored by Git. Committed reference outputs are in `reports/`;
your default command outputs are in `outputs/`.

| Command | Default output | Purpose |
|---|---|---|
| `benchmark` | `outputs/benchmark/summary.json` | Overall metrics and source commit; `model_executed=false` |
| `benchmark` | `outputs/benchmark/cargo_counts.csv` | Row and experiment-ID counts by cargo |
| `benchmark` | `outputs/benchmark/cargo_metrics.csv` | Pooled metrics within each cargo |
| `benchmark` | `outputs/benchmark/study_metrics.csv` | Metrics by experiment ID and cargo |
| `benchmark` | `outputs/benchmark/*.svg` | Cargo coverage and study-level correlation figures |
| `candidates` | `outputs/candidates/candidate_groups.csv` | One row per proposed comparison group |
| `candidates` | `outputs/candidates/candidate_rows.csv` | Source rows, features, observations, and predictions for those groups |
| `candidates` | `outputs/candidates/curation_template.csv` | Review decisions and supporting evidence to complete |
| `candidates` | `outputs/candidates/summary.json` | Candidate counts and matching scope |

The stricter command above writes the same candidate file types to
`outputs/helper_cholesterol/`. An empty candidate table is a valid result.
Read [RESULTS.md](RESULTS.md) for interpretation of the committed snapshot.

Use `--data-dir PATH` to select a different location for the same pinned files,
`--out PATH` to choose an output directory, and `benchmark --no-figures` to skip
plots. These options do not change the dataset or accept arbitrary model inputs.
For a damaged cache, use `lnpdb-hhes fetch --refresh`.

## Review and evaluate formulation comparisons

```bash
cp outputs/candidates/curation_template.csv outputs/curation.csv
# Edit the copy after reviewing the original study records.
lnpdb-hhes evaluate-curated --curation outputs/curation.csv
```

Set `decision=include` only after recording `evidence_source`, `readout_method`,
`readout_time_h`, and `comparability_note`. Retain excluded and unresolved groups
in the review file. Generated templates can be overwritten by another candidate
run, so keep manual decisions in the separate copy.

An untouched template is deliberately rejected. Evaluation accepts candidate IDs
from the default `all` mode, and rejects included groups with repeated identical
compositions. See [METHODS.md](METHODS.md) for matching and aggregation rules.

Successful evaluation writes `group_metrics.csv`, `included_curation.csv`, and
`summary.json` to `outputs/evaluate-curated/`. The summary records the curation
file's hash and the tie tolerances. `--observed-tie-tolerance` and
`--predicted-tie-tolerance` default to zero in source target units; choose any
alternative before inspecting comparative performance.

## Check experimental metadata

```bash
lnpdb-hhes lab-template
# Complete data/private/formulations.csv using experimental records.
lnpdb-hhes assess-lab --input data/private/formulations.csv
```

The blank template contains no experimental examples and cannot be assessed until
sample rows are added. Field definitions are in [LAB_DATA.md](LAB_DATA.md).
Assessment writes `outputs/lab/metadata_review.json`, including missing fields,
unsupported categories, and composition checks. Exit code 2 indicates input
errors. Even complete metadata remains `prediction_ready=false`; this command
does not run a model or establish scientific applicability.

Keep raw measurements and local experimental records in `data/private/` or
another untracked location. The template command refuses to overwrite an
existing file.

## Troubleshooting

| Symptom | Action |
|---|---|
| `lnpdb-hhes: command not found` | Activate the virtual environment; try `python -m lnpdb_hhes --help`. |
| `externally-managed-environment` | Install packages inside the virtual environment. |
| Missing snapshot CSV | Run `lnpdb-hhes fetch`. |
| Checksum mismatch | Preserve manual edits elsewhere, then use `fetch --refresh`. |
| Network error on first download | Check access to `raw.githubusercontent.com`; a verified cache works offline. |
| No explicitly included groups | Complete source review in a copy of the curation template. |
| Unsupported model category | Preserve the actual experimental identity; consult the pinned schema. |

The complete test command and the recorded CI environment are in
[VALIDATION.md](VALIDATION.md).
