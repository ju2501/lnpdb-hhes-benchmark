"""Find formulation-comparison candidates; matching does not establish comparability."""

import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd

from .benchmark import metrics
from .data import DataError, manifest, write_json

RATIOS = ["IL_molratio", "HL_molratio", "CHL_molratio", "PEG_molratio"]
GROUP_COLUMNS = ["group_id", "Experiment_ID", "cargo", "IL_name", "IL_SMILES", "n_rows", "n_formulations"]
REVIEW_COLUMNS = ["decision", "evidence_source", "readout_method", "readout_time_h", "comparability_note"]


def find_candidates(snapshot, vary="all"):
    if vary not in {"all", "helper-cholesterol"}:
        raise DataError("Unsupported variation mode.")
    varying = RATIOS if vary == "all" else ["HL_molratio", "CHL_molratio"]
    context = [c for c in snapshot.features.columns if c not in varying]
    keys = ["Experiment_ID", "IL_SMILES"] + context
    table = pd.concat([snapshot.records, snapshot.features], axis=1)
    descriptions, members = [], []
    for key, group in table.groupby(keys, sort=True, dropna=False):
        n_formulations = len(group[RATIOS].drop_duplicates())
        if n_formulations < 2:
            continue
        key_values = [v.item() if isinstance(v, np.generic) else v for v in key]
        encoded = json.dumps({"mode": vary, "keys": keys, "values": key_values}, separators=(",", ":"), allow_nan=False)
        group_id = hashlib.sha256(encoded.encode()).hexdigest()[:16]
        first = group.iloc[0]
        descriptions.append({"group_id": group_id, "Experiment_ID": first.Experiment_ID,
                             "cargo": first.cargo, "IL_name": first.IL_name, "IL_SMILES": first.IL_SMILES,
                             "n_rows": len(group), "n_formulations": n_formulations})
        group = group.copy()
        group.insert(0, "group_id", group_id)
        members.append(group)
    groups = pd.DataFrame(descriptions, columns=GROUP_COLUMNS).sort_values(["Experiment_ID", "group_id"])
    if groups.group_id.duplicated().any():
        raise DataError("Candidate group ID collision.")
    rows = pd.concat(members, ignore_index=True) if members else pd.DataFrame(columns=["group_id"] + table.columns.tolist())
    rows = rows.sort_values(["group_id", "row_id"])
    return groups.reset_index(drop=True), rows.reset_index(drop=True)


def run_candidates(snapshot, out, vary="all"):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    groups, rows = find_candidates(snapshot, vary)
    groups.to_csv(out / "candidate_groups.csv", index=False)
    rows.to_csv(out / "candidate_rows.csv", index=False)
    review = groups.copy()
    for c in REVIEW_COLUMNS:
        review[c] = "unreviewed" if c == "decision" else ""
    # Regenerate the template; manual reviews belong in a separate copied file.
    review.to_csv(out / "curation_template.csv", index=False)
    summary = {"source_commit": manifest()["commit"], "vary": vary,
               "n_candidate_groups": len(groups), "n_candidate_rows": len(rows),
               "n_unique_il_smiles": int(rows.IL_SMILES.nunique()),
               "groups_by_experiment": {str(k): int(v) for k,v in groups.Experiment_ID.value_counts().items()},
               "review_status": "unreviewed_candidates",
               "matching": "Exact values in supplied feature columns; assay and time must be reviewed separately.",
               "scope": "This pinned test subset only. Groups are not independent experiments."}
    write_json(out / "summary.json", summary)
    return summary


def pair_direction_score(observed, predicted, observed_tolerance=0.0, predicted_tolerance=0.0):
    if not np.isfinite([observed_tolerance, predicted_tolerance]).all() or min(observed_tolerance, predicted_tolerance) < 0:
        raise DataError("Tie tolerances must be finite and nonnegative.")
    if len(observed) != len(predicted) or len(observed) < 2:
        raise DataError("Pairwise evaluation requires at least two aligned observations.")
    if not np.isfinite(np.concatenate([observed, predicted])).all():
        raise DataError("Pairwise evaluation requires finite values.")
    wins = ties = informative = observed_ties = 0
    for i,j in itertools.combinations(range(len(observed)), 2):
        delta_y, delta_p = observed[i]-observed[j], predicted[i]-predicted[j]
        if abs(delta_y) <= observed_tolerance:
            observed_ties += 1
            continue
        informative += 1
        if abs(delta_p) <= predicted_tolerance:
            ties += 1
        elif np.sign(delta_y) == np.sign(delta_p):
            wins += 1
    return {"n_informative_pairs": informative, "n_observed_ties": observed_ties,
            "n_predicted_ties": ties,
            "direction_score": (wins+0.5*ties)/informative if informative else None}


def evaluate_curated(snapshot, curation, out, observed_tolerance=0.0, predicted_tolerance=0.0):
    groups, rows = find_candidates(snapshot, "all")
    review = pd.read_csv(curation, keep_default_na=False, dtype=str)
    required = {"group_id", *REVIEW_COLUMNS}
    if not required.issubset(review.columns):
        raise DataError(f"Curation is missing columns: {sorted(required-set(review.columns))}")
    if review.group_id.duplicated().any():
        raise DataError("Duplicate curation group IDs.")
    if not set(review.group_id).issubset(set(groups.group_id)):
        raise DataError("Unknown group IDs; use a curation template from this snapshot and mode='all'.")
    if not set(review.decision).issubset({"", "unreviewed", "include", "exclude"}):
        raise DataError("Curation decision must be include, exclude, or unreviewed.")
    accepted = review[review.decision.eq("include")]
    if accepted.empty:
        raise DataError("No explicitly included groups. Review source evidence before evaluating candidates.")
    results = []
    for row in accepted.itertuples():
        if any(not str(getattr(row, c)).strip() for c in REVIEW_COLUMNS if c != "decision"):
            raise DataError(f"Incomplete comparability evidence for group {row.group_id}.")
        try:
            time_h = float(row.readout_time_h)
        except ValueError as exc:
            raise DataError(f"Invalid readout_time_h for {row.group_id}.") from exc
        if not np.isfinite(time_h) or time_h <= 0:
            raise DataError(f"readout_time_h must be positive for {row.group_id}.")
        group = rows[rows.group_id.eq(row.group_id)]
        if group[RATIOS].duplicated().any():
            raise DataError(f"Repeated compositions in {row.group_id}: aggregation requires an explicit separate design.")
        observed, predicted = group.observed.to_numpy(), group.predicted.to_numpy()
        results.append({"group_id": row.group_id, "Experiment_ID": group.Experiment_ID.iloc[0],
                        "cargo": group.cargo.iloc[0], "IL_SMILES": group.IL_SMILES.iloc[0],
                        "n_rows": len(group), "spearman": metrics(observed, predicted)["spearman"],
                        **pair_direction_score(observed, predicted, observed_tolerance, predicted_tolerance)})
    result = pd.DataFrame(results)
    available = result.direction_score.dropna()
    summary = {"source_commit": manifest()["commit"], "n_reviewed_groups": len(result),
               "n_experiment_ids": int(result.Experiment_ID.nunique()),
               "n_unique_il_smiles": int(result.IL_SMILES.nunique()),
               "macro_direction_score": float(available.mean()) if len(available) else None,
               "observed_tie_tolerance": observed_tolerance,
               "predicted_tie_tolerance": predicted_tolerance,
               "curation_sha256": hashlib.sha256(Path(curation).read_bytes()).hexdigest(),
               "scope": "Retrospective curated evaluation; pairs and groups are not independent biological replicates."}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    result.to_csv(out / "group_metrics.csv", index=False)
    accepted.to_csv(out / "included_curation.csv", index=False)
    write_json(out / "summary.json", summary)
    return summary
