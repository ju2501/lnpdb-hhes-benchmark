# Validation record

Validated on 2026-10-01 in a Linux execution environment with Python 3.12.14.
The numerical package versions are recorded in `requirements-tested.txt`:
NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0, and Matplotlib 3.10.8.

## Completed checks

| Check | Result |
|---|---|
| Editable package installation | Passed using existing runtime dependencies |
| Wheel build | Passed without downloading dependencies |
| Unit and public-snapshot tests | 30 passed, including 3 snapshot regression tests |
| Four source file hashes | SHA-256 and Git blob hashes match the immutable manifest |
| Overall metrics | 2,164 rows; Pearson 0.481875957902; RMSE 0.911933051764; Spearman 0.444235922218 |
| Cargo and study metrics | Written to `cargo_metrics.csv` and `study_metrics.csv` |
| Same-IL candidate analysis | 69 groups, 213 rows, 15 structures; all from `JW_2024` |
| Helper/cholesterol-only variation | 0 candidate groups in this test subset |
| Untouched curation template | Correctly rejected with exit code 2 |
| Empty local lab template | Correctly rejected with exit code 2 |
| Scientific figures | Both figure layouts visually inspected |
| Local documentation links | Resolved successfully |

The tests cover misaligned prediction rows, changed labels, duplicated IDs,
invalid cargo encoding, nonfinite values, damaged downloads and caches,
small-sample/constant correlations, tie handling, grouping by context, source
review requirements, malformed lab CSV rows, unsupported cell categories, and
composition units. Synthetic fixtures are explicitly labeled and are not lab
measurements.

## Reproduce the committed results

From the repository root, after installation:

```bash
lnpdb-hhes fetch
python -m unittest discover -s tests -v
lnpdb-hhes benchmark --out reports/public_snapshot
lnpdb-hhes candidates --out reports/candidates
lnpdb-hhes candidates --vary helper-cholesterol --out reports/helper_cholesterol
```

Snapshot tests skip when the four source CSVs have not been downloaded. Run
`fetch` first to execute the complete suite. Numeric values should reproduce
within floating-point precision; SVG formatting can differ across Matplotlib
versions.

## Verification limits

- The initial local analysis used verified cached files and mocked HTTP
  responses. Live CLI downloads were subsequently verified in GitHub Actions.
- Local installation and tests used Python 3.12. GitHub Actions additionally
  verified installation and the full test suite on Python 3.10 and 3.12.
- A wheel was built, but a fresh dependency download and installation on the
  user's physical Pixel Chromebook have not been performed.
- No LiON checkpoint was executed. These are evaluations of supplied public
  predictions, not independently generated model outputs.
- No original-study curation has been completed for the 69 candidates. No
  curated biological performance score is claimed.
- No HHES experimental records or efficacy predictions are included.

## GitHub Actions verification

On 2026-10-06, [workflow run 37422513951](https://github.com/ju2501/lnpdb-hhes-benchmark/actions/runs/37422513951)
passed on both Python 3.10 and Python 3.12 for
[commit 97721a7](https://github.com/ju2501/lnpdb-hhes-benchmark/commit/97721a779ff366c1a8932449ec75e0176273d6ce).
Both jobs successfully completed:

1. A fresh editable installation with dependencies.
2. Live download and hash verification of all four pinned source CSVs.
3. The 30-test suite, including the three public-snapshot regression checks.
4. Benchmark tables and figures via `lnpdb-hhes benchmark`.
5. Formulation candidate generation via `lnpdb-hhes candidates`.

The 39 uploaded file blobs were also compared with the prepared local files;
every Git blob hash matched before this documentation update.
