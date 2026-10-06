"""Descriptive evaluation of existing public predictions, not retraining."""

from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .data import manifest, write_json


def metrics(observed, predicted):
    observed, predicted = np.asarray(observed, float), np.asarray(predicted, float)
    if len(observed) != len(predicted) or not len(observed):
        raise ValueError("Metrics require equally sized nonempty arrays.")
    if not (np.isfinite(observed).all() and np.isfinite(predicted).all()):
        raise ValueError("Metrics require finite values.")
    result = {"n_rows": int(len(observed)), "rmse": float(np.sqrt(np.mean((observed-predicted)**2))),
              "pearson": None, "spearman": None, "correlation_status": "available"}
    if len(observed) < 3:
        result["correlation_status"] = "fewer_than_three_rows"
    elif np.ptp(observed) == 0 or np.ptp(predicted) == 0:
        result["correlation_status"] = "constant_vector"
    else:
        result["pearson"] = float(np.corrcoef(observed, predicted)[0, 1])
        result["spearman"] = float(spearmanr(observed, predicted).statistic)
    return result


def benchmark_tables(snapshot):
    data = snapshot.records
    counts = data.groupby("cargo").agg(n_rows=("row_id", "size"),
                                       n_experiment_ids=("Experiment_ID", "nunique")).reset_index()
    study = pd.DataFrame([
        {"Experiment_ID": experiment, "cargo": cargo, **metrics(g.observed, g.predicted)}
        for (experiment, cargo), g in data.groupby(["Experiment_ID", "cargo"], sort=True)
    ])
    return counts, study


def run_benchmark(snapshot, out, figures=True):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    counts, study = benchmark_tables(snapshot)
    cargo_metrics = pd.DataFrame([
        {"cargo": cargo, "n_experiment_ids": int(group.Experiment_ID.nunique()),
         **metrics(group.observed, group.predicted)}
        for cargo, group in snapshot.records.groupby("cargo", sort=True)
    ])
    summary = {"source_commit": manifest()["commit"],
               "evaluation": "published_single_split_predictions",
               "model_executed": False,
               "overall": metrics(snapshot.records.observed, snapshot.records.predicted),
               "scope": "Retrospective test-subset analysis; not whole-database coverage or new external validation."}
    counts.to_csv(out / "cargo_counts.csv", index=False)
    cargo_metrics.to_csv(out / "cargo_metrics.csv", index=False)
    study.to_csv(out / "study_metrics.csv", index=False)
    write_json(out / "summary.json", summary)
    if figures:
        plot_benchmark(counts, study, out)
    lines = ["# Public LiON prediction audit", "", f"Source commit: `{manifest()['commit']}`.", "",
             "This run evaluates supplied predictions. It does not execute or train LiON.", "",
             "| Cargo | Test rows | Experiment IDs |", "|---|---:|---:|"]
    lines += [f"| {r.cargo} | {r.n_rows} | {r.n_experiment_ids} |" for r in counts.itertuples()]
    lines += ["", "## Overall descriptive metrics", "", json_block(summary["overall"]), "",
              "Cargo-level metrics are in `cargo_metrics.csv`; study-level metrics are in `study_metrics.csv`.",
              "Report row counts and study counts with correlations. Cargo-level pooled metrics retain study confounding.",
              "Overall metrics pool heterogeneous normalized targets and do not establish performance for a new cargo or assay.",
              "The original split is described as amine-based. Study subsets here are not newly held-out studies.",
              "No confidence intervals or claims of biological replication are inferred from row counts.", ""]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def json_block(value):
    import json
    return "```json\n" + json.dumps(value, indent=2, allow_nan=False) + "\n```"


def plot_benchmark(counts, study, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    palette = {"mRNA": "#236779", "pDNA": "#ba6428", "siRNA": "#6c698a"}
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.hashsalt": "lnpdb-hhes-v0.1", "axes.spines.top": False,
                         "axes.spines.right": False}):
        c = counts.set_index("cargo").loc[["mRNA", "siRNA", "pDNA"]]
        fig, ax = plt.subplots(figsize=(8.5, 3.4), layout="constrained")
        ax.barh(c.index, c.n_rows, color=[palette[v] for v in c.index])
        for i, row in enumerate(c.itertuples()):
            study_label = "study" if row.n_experiment_ids == 1 else "studies"
            ax.text(row.n_rows + 24, i, f"{row.n_rows:,} rows / {row.n_experiment_ids} {study_label}", va="center", fontsize=10)
        ax.set_xlim(0, c.n_rows.max() * 1.43)
        ax.invert_yaxis()
        ax.set_xlabel("Rows in the published test split")
        ax.set_title("Cargo coverage in the evaluated subset", loc="left", weight="bold", pad=16)
        ax.spines[["left", "bottom"]].set_visible(False)
        fig.savefig(out / "cargo_coverage.svg", metadata={"Date": None})
        plt.close(fig)
        s = study[study.spearman.notna() & study.n_rows.ge(5)].sort_values("spearman")
        fig, ax = plt.subplots(figsize=(8.5, max(5, len(s)*0.29+1.5)), layout="constrained")
        labels = [f"{r.Experiment_ID}  (n={r.n_rows})" for r in s.itertuples()]
        ax.barh(labels, s.spearman, color=[palette[v] for v in s.cargo], height=0.7)
        ax.axvline(0, color="#6b7280", linewidth=0.8)
        ax.set_xlim(-1, 1)
        ax.set_xlabel("Spearman correlation (studies with at least 5 test rows)")
        ax.set_title("Published predictions, evaluated by study", loc="left", weight="bold", pad=16)
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(color=v, label=k) for k,v in palette.items()], loc="lower right", frameon=False)
        fig.savefig(out / "study_performance.svg", metadata={"Date": None})
        plt.close(fig)
