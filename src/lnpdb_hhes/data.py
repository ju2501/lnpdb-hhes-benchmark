"""Fetch and verify the exact four public files used in this benchmark."""

from dataclasses import dataclass
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


class DataError(ValueError):
    """An input violates the reproducibility or data contract."""


def manifest():
    return json.loads(files("lnpdb_hhes").joinpath("snapshot.json").read_text())


def verify_bytes(name, content, specification):
    digest = hashlib.sha256(content).hexdigest()
    git_digest = hashlib.sha1(
        b"blob " + str(len(content)).encode() + b"\0" + content
    ).hexdigest()
    if digest != specification["sha256"] or git_digest != specification["git_blob_sha"]:
        raise DataError(f"Checksum mismatch for {name}; do not edit source CSVs. Use fetch --refresh.")


def fetch_snapshot(destination, refresh=False):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    spec = manifest()
    states = []
    for name, expected in spec["files"].items():
        path = destination / name
        if path.exists() and not refresh:
            verify_bytes(name, path.read_bytes(), expected)
            states.append({"file": name, "status": "verified_cache"})
            continue
        request = Request(expected["url"], headers={"User-Agent": "lnpdb-hhes-benchmark/0.1"})
        with urlopen(request, timeout=30) as response:
            content = response.read(10_000_001)
        if len(content) > 10_000_000:
            raise DataError(f"Unexpectedly large download: {name}")
        verify_bytes(name, content, expected)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination, delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(content)
            os.replace(temporary, path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        states.append({"file": name, "status": "downloaded_and_verified"})
    return states


@dataclass
class Snapshot:
    records: pd.DataFrame
    features: pd.DataFrame


def assemble(truth, predictions, metadata, features):
    """Validate alignment; exact feature alignment also relies on pinned file hashes."""
    if not (len(truth) == len(predictions) == len(metadata) == len(features)):
        raise DataError("Source files have different row counts.")
    for frame, label in [(truth, "truth"), (predictions, "predictions"), (metadata, "metadata")]:
        if not {"IL_SMILES", "Experiment_value"}.issubset(frame.columns):
            raise DataError(f"Missing target or SMILES columns in {label}.")
    if not {"LNP_ID", "Experiment_ID", "IL_name"}.issubset(metadata.columns):
        raise DataError("Missing metadata identifiers.")
    if not truth.IL_SMILES.equals(predictions.IL_SMILES) or not truth.IL_SMILES.equals(metadata.IL_SMILES):
        raise DataError("SMILES row alignment failed.")
    if not np.allclose(truth.Experiment_value, metadata.Experiment_value, rtol=1e-10, atol=1e-12):
        raise DataError("Metadata and truth targets differ.")
    if metadata[["LNP_ID", "Experiment_ID", "IL_SMILES"]].isna().any().any():
        raise DataError("Missing source identity.")
    if metadata.LNP_ID.duplicated().any():
        raise DataError("Duplicate LNP IDs in this pinned snapshot.")
    cargo_columns = ["Cargo_mRNA", "Cargo_pDNA", "Cargo_siRNA"]
    if not set(cargo_columns).issubset(features.columns):
        raise DataError("Missing cargo encoding.")
    cargo = features[cargo_columns]
    if not cargo.isin([0, 1]).all().all() or not cargo.sum(axis=1).eq(1).all():
        raise DataError("Cargo must be encoded as exactly one of mRNA, pDNA, siRNA.")
    for values in [truth.Experiment_value, predictions.Experiment_value, features]:
        if not np.isfinite(np.asarray(values, dtype=float)).all():
            raise DataError("Non-finite numeric values in the snapshot.")
    records = metadata[["LNP_ID", "Experiment_ID", "IL_name", "IL_SMILES"]].copy()
    records.insert(0, "row_id", [f"test:{i:05d}" for i in range(len(records))])
    records["cargo"] = cargo.idxmax(axis=1).str.removeprefix("Cargo_")
    records["observed"] = truth.Experiment_value.to_numpy()
    records["predicted"] = predictions.Experiment_value.to_numpy()
    return Snapshot(records.reset_index(drop=True), features.reset_index(drop=True))


def load_snapshot(directory):
    directory = Path(directory)
    spec = manifest()
    frames = {}
    for name, expected in spec["files"].items():
        path = directory / name
        if not path.is_file():
            raise DataError(f"Missing {path}. Run 'lnpdb-hhes fetch' first.")
        verify_bytes(name, path.read_bytes(), expected)
        frames[name] = pd.read_csv(path)
    if frames["test_extra_x.csv"].columns.tolist() != spec["feature_columns"]:
        raise DataError("Feature order does not match the pinned checkpoint schema.")
    snapshot = assemble(frames["test.csv"], frames["test_results.csv"],
                        frames["test_metadata.csv"], frames["test_extra_x.csv"])
    if len(snapshot.records) != spec["expected_rows"]:
        raise DataError("Unexpected snapshot row count.")
    return snapshot


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
