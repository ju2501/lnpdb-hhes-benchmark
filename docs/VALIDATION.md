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

- The analysis used a verified local copy of the public files. First-download
  behavior was tested with mocked HTTP responses; a live download through the
  CLI was not verified because this execution environment restricts that host.
- Installation and tests used Python 3.12. Python 3.10 and 3.12 are configured
  in GitHub Actions, but remote CI has not run before the initial upload.
- A wheel was built, but a fresh dependency download and installation on the
  user's physical Pixel Chromebook have not been performed.
- No LiON checkpoint was executed. These are evaluations of supplied public
  predictions, not independently generated model outputs.
- No original-study curation has been completed for the 69 candidates. No
  curated biological performance score is claimed.
- No HHES experimental records or efficacy predictions are included.
