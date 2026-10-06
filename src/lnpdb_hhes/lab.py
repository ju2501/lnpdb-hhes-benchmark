"""Metadata checks for future lab cases; this is not a prediction adapter."""

import csv
import math
from pathlib import Path
from .data import DataError, manifest, write_json

FIELDS = ["sample_id", "batch_id", "cargo", "reporter", "il_name", "il_smiles", "structure_source",
          "il_mol_pct", "helper_lipid", "helper_mol_pct", "cholesterol_lipid", "cholesterol_mol_pct",
          "peg_lipid", "peg_mol_pct", "peg_identity_source", "il_to_nucleicacid_massratio",
          "dose_ug_nucleicacid", "dose_basis", "model_type", "model_target", "route",
          "mixing_method", "aqueous_buffer", "dialysis_buffer", "experiment_batching",
          "readout_method", "readout_time_h", "independent_batch_count", "notes"]
CATEGORY_PREFIX = {"cargo": "Cargo_", "reporter": "Cargo_type_", "helper_lipid": "HL_name_",
                   "cholesterol_lipid": "CHL_name_", "peg_lipid": "PEG_name_", "model_type": "Model_type_",
                   "model_target": "Model_target_", "route": "Route_of_administration_",
                   "mixing_method": "Mixing_method_", "aqueous_buffer": "Aqueous_buffer_",
                   "dialysis_buffer": "Dialysis_buffer_", "experiment_batching": "Experiment_batching_"}


def write_template(path):
    path = Path(path)
    if path.exists():
        raise DataError(f"Refusing to overwrite {path}.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(FIELDS)
    return {"template": str(path), "rows": 0}


def assess_rows(rows):
    columns = set(manifest()["feature_columns"])
    seen = set()
    results = []
    for i,row in enumerate(rows, start=2):
        errors = []
        for field in FIELDS:
            if field not in {"notes", "independent_batch_count"} and not str(row.get(field, "")).strip():
                errors.append(f"missing:{field}")
        sample = str(row.get("sample_id", "")).strip()
        if sample in seen:
            errors.append("duplicate:sample_id")
        seen.add(sample)
        for field,prefix in CATEGORY_PREFIX.items():
            value = str(row.get(field, "")).strip()
            if value and prefix + value not in columns:
                errors.append(f"unsupported:{field}={value}")
        ratios = []
        numeric = ["il_mol_pct", "helper_mol_pct", "cholesterol_mol_pct", "peg_mol_pct",
                   "dose_ug_nucleicacid", "il_to_nucleicacid_massratio", "readout_time_h"]
        for field in numeric:
            try:
                value = float(row.get(field, ""))
                if not math.isfinite(value):
                    raise ValueError
                if field.endswith("mol_pct"):
                    if not 0 <= value <= 100:
                        raise ValueError
                    ratios.append(value)
                elif value <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                errors.append(f"invalid_numeric:{field}")
        if len(ratios) == 4 and abs(sum(ratios)-100) > 0.01:
            errors.append("molar_percent_sum_must_be_100")
        count = str(row.get("independent_batch_count", "")).strip()
        if count and (not count.isdigit() or int(count) < 1):
            errors.append("independent_batch_count_must_be_a_positive_integer_or_blank")
        results.append({"csv_line": i, "sample_id": sample, "errors": errors,
                        "status": "needs_metadata_correction" if errors else "requires_scientific_review",
                        "prediction_ready": False,
                        "review_required": ["chemical_identity_and_SMILES", "dose_basis",
                                            "assay_and_time_comparability", "training_domain_coverage"]})
    return results


def assess_file(path, out):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise DataError("Missing or duplicate input column names.")
        rows = list(reader)
    if not rows:
        raise DataError("The template has no sample rows yet.")
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise DataError("A sample row has a different number of fields from the CSV header.")
    result = {"schema": "LNPDB_single_split_92_features", "rows": assess_rows(rows),
              "note": "Metadata checks only. No SMILES validation, efficacy inference, or FACS calibration performed."}
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, result)
    return result
