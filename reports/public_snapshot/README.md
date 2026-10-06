# Public LiON prediction audit

Source commit: `fc7c38933b445eb54985014f2b8917606462eec1`.

This run evaluates supplied predictions. It does not execute or train LiON.

| Cargo | Test rows | Experiment IDs |
|---|---:|---:|
| mRNA | 1659 | 26 |
| pDNA | 16 | 1 |
| siRNA | 489 | 4 |

## Overall descriptive metrics

```json
{
  "n_rows": 2164,
  "rmse": 0.9119330517639239,
  "pearson": 0.48187595790197846,
  "spearman": 0.44423592221839653,
  "correlation_status": "available"
}
```

Cargo-level metrics are in `cargo_metrics.csv`; study-level metrics are in `study_metrics.csv`.
Report row counts and study counts with correlations. Cargo-level pooled metrics retain study confounding.
Overall metrics pool heterogeneous normalized targets and do not establish performance for a new cargo or assay.
The original split is described as amine-based. Study subsets here are not newly held-out studies.
No confidence intervals or claims of biological replication are inferred from row counts.
