import copy
import csv
import json
from importlib.util import find_spec
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_journal_metrics import COLUMNS, apply_projection
from validate_journal_metrics import audit, select_metric, validate_public_projection, validate_registry, validate_record

FIXTURE = json.loads((ROOT / "tests/fixtures/jcr-synthetic.json").read_text())


class JournalMetricsTests(unittest.TestCase):
    def setUp(self):
        self.registry = copy.deepcopy(FIXTURE["registry"])

    def rows(self, record):
        return [{
            "journal_id": "synthetic-journal", **{k: v for k, v in record.items() if k in COLUMNS},
            "category": c["name"], **{k: c[k] for k in
                ("rank", "total", "quartile", "s2_if_percent", "jif_percentile")}
        } for c in record["categories"]]

    def load_rows(self, rows, extension=".csv"):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ("synthetic" + extension)
            if extension == ".xlsx":
                from openpyxl import Workbook
                wb = Workbook()
                sheet = wb.active
                sheet.title = "JCR"
                sheet.append(COLUMNS)
                for row in rows:
                    sheet.append([row.get(col) for col in COLUMNS])
                wb.save(path)
                wb.close()
            else:
                with path.open("w", newline="") as file:
                    writer = csv.DictWriter(file, COLUMNS)
                    writer.writeheader()
                    writer.writerows(rows)
            apply_projection(self.registry, path)

    def test_csv_preserves_previous_year_and_revision(self):
        history, edition = FIXTURE["records"]
        self.load_rows(self.rows(edition) + self.rows(history))
        self.load_rows(self.rows({**edition, "revision": 2, "jif": 9}))
        self.load_rows(self.rows(edition))
        self.assertEqual([m["jif"] for m in self.registry["journals"][0]["metrics"]], [7, 8, 9])
        with self.assertRaisesRegex(ValueError, "new revision"):
            self.load_rows(self.rows({**edition, "jif": 10}))

    @unittest.skipUnless(find_spec("openpyxl"), "XLSX import is optional")
    def test_xlsx_import(self):
        self.load_rows(self.rows(FIXTURE["records"][1]), ".xlsx")
        self.assertEqual(len(self.registry["journals"][0]["metrics"][0]["categories"]), 2)

    def test_rejects_bad_values_and_unapproved_rows(self):
        edition = FIXTURE["records"][1]
        for key, value in (("release_year", 2030), ("public_authorized", False),
                           ("verification_status", "unverified"), ("ranking", "classic"),
                           ("category_completeness", "partial"), ("jif", float("nan"))):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_record({**edition, key: value})
        for key, value in (("rank", 0), ("quartile", "Q5"), ("jif_percentile", 101),
                           ("s2_if_percent", -1), ("rank_percent", 99)):
            bad = copy.deepcopy(edition)
            bad["categories"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_record(bad)
        rows = self.rows(edition)
        rows[0]["public_authorized"] = False
        with self.assertRaisesRegex(ValueError, "approval"):
            self.load_rows(rows)
        self.assertFalse(self.registry["journals"][0]["metrics"])

    def test_optional_rank_and_percentile_inputs(self):
        rows = self.rows(FIXTURE["records"][1])
        for row in rows:
            row.update(rank="", total="", jif_percentile="")
        self.load_rows(rows)
        record, category = select_metric(self.registry["journals"][0], self.registry["public_edition"])
        self.assertEqual(category["s2_if_percent"], 5)
        self.assertIsNone(category["rank_percent"])
        self.assertIsNone(category["jif_percentile"])

    def test_browser_and_python_selectors_agree(self):
        history, current = FIXTURE["records"]
        corrected = {**current, "revision": 2, "revision_date": "2026-11-05", "last_verified": "2026-11-06"}
        tied = copy.deepcopy(corrected)
        tied["categories"][1].update(name="ALPHA synthetic", s2_if_percent=5.0)
        missing = copy.deepcopy(current)
        missing["categories"][0].update(rank=None, total=None, jif_percentile=None, rank_percent=None)
        cases = [
            ([history, current, corrected], {}),
            ([history, current], {"mode": "historical", "year": 2024}),
            ([history, current], {"mode": "publication", "publicationYear": 2024}),
            ([history, current, corrected], {"mode": "asOf", "asOf": "2026-07-01"}),
            ([history, current, corrected], {"mode": "asOf", "asOf": "2026-11-06"}),
            ([history], {}),
            ([{**current, "verification_status": "unverified"}], {}),
            ([{**current, "public_authorized": False}], {}),
            ([{**current, "category_completeness": "partial", "category_count": 3}], {}),
            ([tied], {}),
            ([missing], {}),
        ]
        expected = []
        edition = self.registry["public_edition"]
        for records, options in cases:
            metric = select_metric({"metrics": records}, edition, **{
                {"publicationYear": "publication_year", "asOf": "as_of"}.get(k, k): v
                for k, v in options.items()
            })
            expected.append(None if metric is None else [metric[0]["data_year"], metric[0]["revision"], metric[1]["name"]])
        code = """
require('./assets/js/journal-metrics.js');
const {edition, cases} = JSON.parse(require('fs').readFileSync(0,'utf8'));
const result = cases.map(([metrics, options]) => {
  const value = globalThis.CMLabJournalMetrics.select({metrics}, edition, options);
  return value ? [value.record.data_year, value.record.revision, value.category.name] : null;
});
console.log(JSON.stringify(result));
"""
        actual = subprocess.run(["node", "-e", code], cwd=ROOT,
                                input=json.dumps({"edition": edition, "cases": cases}),
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(actual.stdout), expected)

    def test_rejects_duplicate_category_and_ambiguous_alias(self):
        edition = FIXTURE["records"][1]
        with self.assertRaisesRegex(ValueError, "duplicate category"):
            validate_record({**edition, "categories": [edition["categories"][0]] * 2})
        other = copy.deepcopy(self.registry["journals"][0])
        other.update(journal_id="synthetic-other", official_name="Synthetic Other", issn=None)
        self.registry["journals"].append(other)
        with self.assertRaisesRegex(ValueError, "ambiguous journal name"):
            validate_registry(self.registry)


class ProductionIntegrityTests(unittest.TestCase):
    def test_current_catalog_reconciles(self):
        registry = json.loads((ROOT / "data/journals.json").read_text())
        papers = json.loads((ROOT / "data/publications.json").read_text())
        validate_public_projection(registry)
        counts, issues, missing = audit(registry, papers)
        self.assertEqual(issues, [])
        self.assertEqual(sum(counts.values()), sum(p["type"] == "Journal" for p in papers))
        self.assertTrue(set(missing) <= set(counts))

    def test_rejects_duplicate_papers_and_synthetic_projections(self):
        registry = copy.deepcopy(FIXTURE["registry"])
        papers = copy.deepcopy(FIXTURE["publications"])
        with self.assertRaisesRegex(ValueError, "duplicate paper ID"):
            audit(registry, [*papers, papers[0]])
        with self.assertRaisesRegex(ValueError, "placeholder provenance"):
            validate_public_projection(registry)
        with self.assertRaises(ValueError):
            validate_public_projection(FIXTURE)

    def test_production_cli_accepts_populated_expanded_temporary_catalog(self):
        # Only a transient test projection with a structurally public-form URL.
        # The checked-in fixture, real registry and deployment copy stay independent.
        registry = copy.deepcopy(FIXTURE["registry"])
        papers = copy.deepcopy(FIXTURE["publications"])
        journal = registry["journals"][0]
        journal["bibliography"]["source_url"] = "https://review-fixture.cmlab-korea.github.io/"
        history, current = copy.deepcopy(FIXTURE["records"])
        for record in (history, current):
            record["source_url"] = "https://review-fixture.cmlab-korea.github.io/"
        added = {**current, "data_year": 2026, "release_year": 2027, "release_date": "2027-06-20",
                 "last_verified": "2027-06-21"}
        journal["metrics"] = [history, current, added]
        other = copy.deepcopy(journal)
        other.update(journal_id="synthetic-new", official_name="Synthetic New Journal", aliases=["New"],
                     issn=None, metrics=[added])
        registry["journals"].append(other)
        registry["public_edition"] = {"data_year": 2026, "release_year": 2027}
        papers.append({**papers[0], "id": 5, "title": "New Synthetic Paper", "catalog_number": "J3",
                       "venue": "Synthetic New Journal", "venue_short": "New'26"})
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target / "journals.json").write_text(json.dumps(registry))
            (target / "publications.json").write_text(json.dumps(papers))
            run = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/validate_journal_metrics.py"),
                                  "--registry", str(target / "journals.json"), "--publications",
                                  str(target / "publications.json")], text=True, capture_output=True, check=True)
            self.assertIn("Missing or incomplete common-edition metrics: none", run.stdout)
            self.assertIn('"synthetic-new": 1', run.stdout)
            node = subprocess.run(["node", str(ROOT / "tests/journal-production.test.cjs"), str(target)],
                                  text=True, capture_output=True, check=True)
            self.assertIn("current public catalog and registry reconcile", node.stdout)


if __name__ == "__main__":
    unittest.main()
