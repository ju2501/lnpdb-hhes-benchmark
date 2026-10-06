"""Integration checks against public source files; run `fetch` first to enable."""
from pathlib import Path
import unittest
from lnpdb_hhes.data import load_snapshot
from lnpdb_hhes.benchmark import metrics, benchmark_tables
from lnpdb_hhes.candidates import find_candidates

DATA = Path(__file__).resolve().parents[1] / "data/raw/single_split"


@unittest.skipUnless((DATA/"test.csv").is_file(), "Download the pinned public snapshot to enable integration checks.")
class PublishedSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.snapshot=load_snapshot(DATA)

    def test_published_prediction_metrics(self):
        d=self.snapshot.records;result=metrics(d.observed,d.predicted)
        self.assertEqual(result["n_rows"],2164)
        self.assertAlmostEqual(result["pearson"],0.4818759579,places=8)
        self.assertAlmostEqual(result["rmse"],0.9119330517639239,places=10)

    def test_cargo_coverage_is_subset_specific(self):
        counts,_=benchmark_tables(self.snapshot)
        self.assertEqual(counts.set_index("cargo").n_rows.to_dict(),{"mRNA":1659,"pDNA":16,"siRNA":489})
        d=self.snapshot.records.query("cargo == 'pDNA'")
        self.assertEqual(d.Experiment_ID.unique().tolist(),["LL_2012"])
        self.assertAlmostEqual(metrics(d.observed,d.predicted)["spearman"],0.0426,places=4)

    def test_formulation_candidate_counts(self):
        groups,rows=find_candidates(self.snapshot)
        self.assertEqual((len(groups),len(rows),rows.IL_SMILES.nunique()),(69,213,15))
        self.assertEqual(groups.Experiment_ID.unique().tolist(),["JW_2024"])
        self.assertTrue(find_candidates(self.snapshot,"helper-cholesterol")[0].empty)


if __name__ == "__main__": unittest.main()
