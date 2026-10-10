"""Automated tests for python/analysis.py.

Run from the repository root:

    python -m unittest discover -s tests -v

Expected values below are validation targets derived from the supplied data; the
tests compare them with values recomputed from the raw CSV files.
"""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "python"))

import analysis as a  # noqa: E402


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_deliveries, cls.routes = a.load_data()
        cls.facts = a.validate_raw_data(cls.raw_deliveries, cls.routes)
        cls.clean = a.clean_deliveries(cls.raw_deliveries)
        cls.merged = a.merge_routes(cls.clean, cls.routes)
        cls.df = a.calculate_metrics(cls.merged)
        cls.service = a.build_service_summary(cls.df)
        cls.hub = a.build_hub_summary(cls.df)
        cls.route = a.build_route_summary(cls.df)
        cls.monthly = a.build_monthly_summary(cls.df)

    # ---- raw / clean row counts, duplicates, joins ---------------------------
    def test_raw_row_counts(self):
        self.assertEqual(len(self.raw_deliveries), 13)
        self.assertEqual(len(self.routes), 4)

    def test_exactly_one_exact_duplicate(self):
        self.assertEqual(int(self.raw_deliveries.duplicated().sum()), 1)
        dup = self.raw_deliveries[self.raw_deliveries.duplicated(keep=False)]
        self.assertEqual(dup["record_id"].unique().tolist(), [12])

    def test_duplicate_removed(self):
        self.assertEqual(len(self.clean), 12)
        self.assertTrue(self.clean["record_id"].is_unique)
        self.assertEqual(sorted(self.clean["record_id"]), list(range(1, 13)))

    def test_no_unmatched_route_keys(self):
        self.assertTrue(set(self.clean["route_id"]).issubset(set(self.routes["route_id"])))
        self.assertTrue(self.df["service_type"].notna().all())
        self.assertEqual(len(self.df), 12)

    def test_column_types(self):
        self.assertTrue(pd.api.types.is_integer_dtype(self.raw_deliveries["record_id"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(self.raw_deliveries["promised_days"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(self.raw_deliveries["actual_days"]))

    def test_validation_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            a.validate_raw_data(self.raw_deliveries.drop_duplicates(), self.routes)  # 12 rows
        with self.assertRaises(ValueError):
            a.validate_raw_data(self.raw_deliveries.rename(columns={"hub": "Hub"}), self.routes)

    # ---- delay calculation ----------------------------------------------------
    def test_delay_non_negative_and_formula(self):
        self.assertTrue(self.df["delay_days"].ge(0).all())
        expected = (self.df["actual_days"] - self.df["promised_days"]).clip(lower=0)
        pd.testing.assert_series_equal(self.df["delay_days"], expected, check_names=False)

    def test_delay_examples_from_spec(self):
        by_id = self.df.set_index("record_id")["delay_days"]
        self.assertEqual(by_id[1], 0)   # promised 2, actual 2
        self.assertEqual(by_id[2], 1)   # promised 3, actual 4
        self.assertEqual(by_id[3], 3)   # promised 5, actual 8
        self.assertEqual(by_id[12], 9)  # promised 6, actual 15
        self.assertEqual(by_id[6], 0)   # on time

    def test_early_delivery_would_clip_to_zero(self):
        row = pd.DataFrame({"record_id": [99], "month": ["Jan"], "route_id": ["R1"], "route": ["x"],
                            "service_type": ["Express"], "hub": ["Delhi"],
                            "promised_days": [5], "actual_days": [3]})
        out = a.calculate_metrics(row)
        self.assertEqual(out["delay_days"].iloc[0], 0)
        self.assertFalse(out["is_delayed"].iloc[0])

    # ---- month order ----------------------------------------------------------
    def test_month_order(self):
        self.assertEqual(self.monthly["month"].tolist(), ["Jan", "Feb", "Mar"])
        self.assertEqual(list(self.df["month"].cat.categories), ["Jan", "Feb", "Mar"])

    # ---- summary totals -------------------------------------------------------
    def test_monthly_totals(self):
        got = dict(zip(self.monthly["month"], self.monthly["total_delay_days"]))
        self.assertEqual(got, {"Jan": 8, "Feb": 9, "Mar": 17})

    def test_service_totals_and_rates(self):
        s = self.service.set_index("service_type")
        self.assertEqual(s.loc["Standard", "total_delay_days"], 22)
        self.assertEqual(s.loc["Express", "total_delay_days"], 12)
        self.assertEqual(self.service.iloc[0]["service_type"], "Standard")
        self.assertAlmostEqual(s.loc["Standard", "delay_incidence_rate"], 83.33, places=2)
        self.assertAlmostEqual(s.loc["Express", "delay_incidence_rate"], 66.67, places=2)

    def test_hub_totals_and_order(self):
        h = self.hub.set_index("hub")["total_delay_days"].to_dict()
        self.assertEqual(h, {"Mumbai": 15, "Delhi": 14, "Chennai": 5})
        self.assertEqual(self.hub["hub"].tolist()[:2], ["Mumbai", "Delhi"])

    def test_route_results(self):
        top = self.route.iloc[0]
        self.assertEqual((top["route_id"], top["route"]), ("R4", "Rural Feeder"))
        self.assertEqual(top["total_delay_days"], 14)
        self.assertAlmostEqual(top["share_of_total_delay_pct"], 41.18, places=2)
        over = self.route[self.route["total_delay_days"] > 8]["route_id"].tolist()
        self.assertEqual(sorted(over), ["R1", "R4"])  # R3 = 8 is NOT > 8

    # ---- incidence ------------------------------------------------------------
    def test_overall_incidence_from_counts(self):
        m = a.overall_metrics(self.df)
        self.assertEqual(m["delayed_count"], 9)
        self.assertEqual(m["delivery_count"], 12)
        self.assertEqual(m["delay_incidence_rate"], 75.00)
        self.assertEqual(m["total_delay_days"], 34)

    def test_incidence_not_average_of_subgroup_rates(self):
        # Equal-sized groups here, so build an unbalanced case to prove counts are used.
        df = pd.DataFrame({
            "record_id": range(1, 6), "month": pd.Categorical(["Jan"] * 5, categories=a.MONTH_ORDER, ordered=True),
            "hub": ["A", "A", "A", "A", "B"], "is_delayed": [True, True, True, True, False],
            "delay_days": [1, 1, 1, 1, 0],
        })
        s = a._summarise(df, ["hub"])
        self.assertEqual(s.set_index("hub").loc["A", "delay_incidence_rate"], 100.0)
        overall = df["is_delayed"].sum() / len(df) * 100
        self.assertEqual(overall, 80.0)           # counts-based
        self.assertNotEqual(s["delay_incidence_rate"].mean(), overall)  # 50.0 would be wrong

    def test_totals_agree_across_summaries(self):
        total = self.df["delay_days"].sum()
        for s in (self.service, self.hub, self.route, self.monthly):
            self.assertEqual(s["total_delay_days"].sum(), total)
            self.assertEqual(s["delivery_count"].sum(), 12)
        a.reconcile_summaries(self.df, self.service, self.hub, self.route, self.monthly)

    # ---- outputs --------------------------------------------------------------
    def test_outputs_created_and_correct(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = a.export_outputs(self.df, self.service, self.hub, self.route, self.monthly, Path(tmp))
            for p in paths.values():
                self.assertTrue(p.exists() and p.stat().st_size > 0, p)
            clean = pd.read_csv(paths["clean_data"])
            self.assertEqual(len(clean), 12)
            self.assertIn("service_type", clean.columns)
            self.assertIn("delay_days", clean.columns)
            self.assertEqual(clean["delay_days"].sum(), 34)
            svc = pd.read_csv(paths["service"])
            self.assertEqual(svc["total_delay_days"].sum(), 34)
            self.assertEqual(paths["chart"].read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_raw_files_unchanged_after_run(self):
        before = {p: a.file_sha256(p) for p in (a.DELIVERIES_FILE, a.ROUTES_FILE)}
        with tempfile.TemporaryDirectory() as tmp:
            a.export_outputs(self.df, self.service, self.hub, self.route, self.monthly, Path(tmp))
        after = {p: a.file_sha256(p) for p in (a.DELIVERIES_FILE, a.ROUTES_FILE)}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
