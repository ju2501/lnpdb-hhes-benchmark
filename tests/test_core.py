import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from lnpdb_hhes.benchmark import metrics
from lnpdb_hhes.candidates import find_candidates, pair_direction_score, evaluate_curated
from lnpdb_hhes.data import DataError, Snapshot, assemble, fetch_snapshot, load_snapshot, verify_bytes
from lnpdb_hhes.lab import FIELDS, assess_file, assess_rows, write_template


def synthetic_snapshot():
    records = pd.DataFrame({
        "row_id": ["test:00000", "test:00001", "test:00002"],
        "LNP_ID": ["synthetic_1", "synthetic_2", "synthetic_3"],
        "Experiment_ID": ["synthetic_study"]*3, "IL_name": ["synthetic"]*3,
        "IL_SMILES": ["CC"]*3, "cargo": ["mRNA"]*3,
        "observed": [1., 3., 2.], "predicted": [1., 2., 3.]})
    features = pd.DataFrame({"IL_molratio": [22.,22.,22.], "HL_molratio": [20.,30.,40.],
                             "CHL_molratio": [56.5,46.5,36.5], "PEG_molratio": [1.5]*3,
                             "Dose_ug_nucleicacid": [2.]*3, "Cargo_mRNA": [1]*3,
                             "Cargo_pDNA": [0]*3, "Cargo_siRNA": [0]*3,
                             "Model_type_HeLa": [1]*3})
    return Snapshot(records, features)


class IntegrityTests(unittest.TestCase):
    def test_checksum_rejects_corruption(self):
        b=b"source\n"
        spec={"sha256":hashlib.sha256(b).hexdigest(),
              "git_blob_sha":hashlib.sha1(b"blob 7\0"+b).hexdigest()}
        verify_bytes("example.csv", b, spec)
        with self.assertRaises(DataError):
            verify_bytes("example.csv", b+b"x", spec)

    def test_fetch_checks_download_and_cache(self):
        b=b"x,y\n1,2\n"
        spec={"files":{"example.csv":{"url":"https://example.invalid/data.csv",
              "sha256":hashlib.sha256(b).hexdigest(),
              "git_blob_sha":hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()}}}
        with tempfile.TemporaryDirectory() as d, patch("lnpdb_hhes.data.manifest",return_value=spec):
            with patch("lnpdb_hhes.data.urlopen",return_value=io.BytesIO(b)):
                self.assertEqual(fetch_snapshot(d)[0]["status"],"downloaded_and_verified")
            with patch("lnpdb_hhes.data.urlopen") as network:
                self.assertEqual(fetch_snapshot(d)[0]["status"],"verified_cache")
                network.assert_not_called()
            (Path(d)/"example.csv").write_bytes(b"corrupt")
            with self.assertRaises(DataError): fetch_snapshot(d)
            self.assertEqual((Path(d)/"example.csv").read_bytes(),b"corrupt")

    def inputs(self):
        s=synthetic_snapshot()
        y=pd.DataFrame({"IL_SMILES":["C","CC","CCC"],"Experiment_value":[1.,2.,3.]})
        m=s.records[["LNP_ID","Experiment_ID","IL_name"]].copy()
        m["IL_SMILES"]=y.IL_SMILES
        m["Experiment_value"]=y.Experiment_value
        return y,y.copy(),m,s.features.copy()

    def test_alignment_accepts_matching_records(self):
        self.assertEqual(len(assemble(*self.inputs()).records),3)

    def test_alignment_rejects_shuffled_predictions(self):
        y,p,m,x=self.inputs()
        p=p.iloc[::-1].reset_index(drop=True)
        with self.assertRaises(DataError): assemble(y,p,m,x)

    def test_alignment_rejects_changed_metadata_labels(self):
        y,p,m,x=self.inputs();m.loc[0,"Experiment_value"]=999.
        with self.assertRaises(DataError): assemble(y,p,m,x)

    def test_alignment_rejects_duplicate_ids(self):
        y,p,m,x=self.inputs();m.loc[1,"LNP_ID"]=m.loc[0,"LNP_ID"]
        with self.assertRaises(DataError): assemble(y,p,m,x)

    def test_cargo_encoding_rejects_multiple_cargos(self):
        y,p,m,x=self.inputs();x.loc[0,"Cargo_pDNA"]=1
        with self.assertRaises(DataError): assemble(y,p,m,x)

    def test_nonfinite_predictions_rejected(self):
        y,p,m,x=self.inputs();p.loc[0,"Experiment_value"]=np.inf
        with self.assertRaises(DataError): assemble(y,p,m,x)


class EvaluationTests(unittest.TestCase):
    def test_rank_and_rmse(self):
        result=metrics([1,2,3],[3,2,1])
        self.assertAlmostEqual(result["spearman"],-1)
        self.assertAlmostEqual(result["rmse"],np.sqrt(8/3))

    def test_two_points_do_not_produce_correlation_claim(self):
        self.assertIsNone(metrics([1,2],[2,1])["spearman"])

    def test_constant_vectors_return_missing_correlation(self):
        self.assertIsNone(metrics([1,1,1],[1,2,3])["pearson"])

    def test_pair_ties_are_explicit(self):
        result=pair_direction_score([1,1,3],[1,2,2])
        self.assertEqual(result["n_observed_ties"],1)
        self.assertEqual(result["n_informative_pairs"],2)
        self.assertEqual(result["n_predicted_ties"],1)
        self.assertEqual(result["direction_score"],0.75)

    def test_all_observed_ties_have_no_score(self):
        self.assertIsNone(pair_direction_score([1,1],[1,2])["direction_score"])

    def test_negative_tolerance_rejected(self):
        with self.assertRaises(DataError): pair_direction_score([1,2],[1,2],-1)


class CandidateTests(unittest.TestCase):
    def test_composition_changes_are_grouped(self):
        groups,rows=find_candidates(synthetic_snapshot())
        self.assertEqual(len(groups),1)
        self.assertEqual(groups.n_formulations.iloc[0],3)
        self.assertEqual(len(rows),3)

    def test_context_changes_split_groups(self):
        s=synthetic_snapshot();s.features.loc[2,"Dose_ug_nucleicacid"]=4
        groups,rows=find_candidates(s)
        self.assertEqual(len(groups),1)
        self.assertEqual(len(rows),2)

    def test_strict_matching_holds_il_and_peg_fixed(self):
        s=synthetic_snapshot();s.features.loc[2,"IL_molratio"]=25
        groups,rows=find_candidates(s,"helper-cholesterol")
        self.assertEqual(len(rows),2)

    def test_single_composition_is_not_a_candidate(self):
        s=synthetic_snapshot()
        s.features["HL_molratio"]=30;s.features["CHL_molratio"]=46.5
        self.assertTrue(find_candidates(s)[0].empty)

    def test_group_id_independent_of_row_order(self):
        s=synthetic_snapshot();first=find_candidates(s)[0].group_id.tolist()
        reversed_snapshot=Snapshot(s.records.iloc[::-1].reset_index(drop=True),s.features.iloc[::-1].reset_index(drop=True))
        self.assertEqual(first,find_candidates(reversed_snapshot)[0].group_id.tolist())

    def test_curated_evaluation_requires_evidence(self):
        s=synthetic_snapshot();groups,_=find_candidates(s)
        review=groups.assign(decision="include",evidence_source="",readout_method="fluorescence",
                             readout_time_h="24",comparability_note="synthetic unit test")
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"review.csv";review.to_csv(p,index=False)
            with self.assertRaises(DataError): evaluate_curated(s,p,Path(d)/"out")
            review["evidence_source"]="synthetic_fixture"
            review.to_csv(p,index=False)
            result=evaluate_curated(s,p,Path(d)/"out")
            self.assertAlmostEqual(result["macro_direction_score"],2/3)
            self.assertEqual(result["n_unique_il_smiles"],1)

    def test_unreviewed_groups_cannot_be_evaluated(self):
        s=synthetic_snapshot();groups,_=find_candidates(s)
        review=groups.assign(decision="unreviewed",evidence_source="",readout_method="",readout_time_h="",comparability_note="")
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"review.csv";review.to_csv(p,index=False)
            with self.assertRaises(DataError): evaluate_curated(s,p,Path(d)/"out")


class LabTests(unittest.TestCase):
    def valid_metadata(self):
        row={field:"synthetic_fixture" for field in FIELDS}
        row.update(cargo="mRNA",reporter="GFP",helper_lipid="DOPE",cholesterol_lipid="Cholesterol",
                   peg_lipid="DMG-PEG2000",model_type="HEK293T",model_target="in_vitro",route="in_vitro",
                   mixing_method="microfluidics",aqueous_buffer="acetate",dialysis_buffer="PBS",
                   experiment_batching="individual",il_mol_pct="22",helper_mol_pct="30",
                   cholesterol_mol_pct="46.5",peg_mol_pct="1.5",dose_ug_nucleicacid="2",
                   il_to_nucleicacid_massratio="12",readout_time_h="72",independent_batch_count="")
        return row

    def test_complete_metadata_is_never_prediction_ready(self):
        result=assess_rows([self.valid_metadata()])[0]
        self.assertEqual(result["errors"],[])
        self.assertFalse(result["prediction_ready"])

    def test_jurkat_is_not_silently_replaced(self):
        row=self.valid_metadata();row["model_type"]="Jurkat"
        self.assertIn("unsupported:model_type=Jurkat",assess_rows([row])[0]["errors"])

    def test_fractions_are_not_accepted_as_percent(self):
        row=self.valid_metadata()
        for k in ["il_mol_pct","helper_mol_pct","cholesterol_mol_pct","peg_mol_pct"]:
            row[k]=str(float(row[k])/100)
        self.assertIn("molar_percent_sum_must_be_100",assess_rows([row])[0]["errors"])

    def test_duplicate_sample_ids_are_reported(self):
        row=self.valid_metadata()
        self.assertIn("duplicate:sample_id",assess_rows([row,row])[1]["errors"])

    def test_template_does_not_overwrite_lab_data(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"template.csv";write_template(p)
            with self.assertRaises(DataError): write_template(p)

    def test_malformed_csv_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"metadata.csv"
            p.write_text("sample_id,batch_id\nsample_without_batch\n", encoding="utf-8")
            with self.assertRaisesRegex(DataError, "number of fields"):
                assess_file(p, Path(d)/"review.json")


if __name__ == "__main__":
    unittest.main()
