"""Exercise the refresh import with crawler-shaped data and real SQLite UPSERTs."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest


SEED_SCRIPT = Path(__file__).resolve().parents[1] / "db" / "seed-jobs.py"


class SeedJobsIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.legacy = root / "scripts-data"
        self.fresh = root / "fetch-data"
        self.legacy.mkdir()
        self.fresh.mkdir()
        spec = importlib.util.spec_from_file_location("seed_jobs_under_test", SEED_SCRIPT)
        self.seed = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.seed)
        self.seed.DATA_DIR = self.legacy
        self.seed.FETCH_DATA_DIR = self.fresh
        self.seed.OUTPUT_FILE = root / "seed.sql"
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)

    def write(self, directory, filename, rows):
        (directory / filename).write_text(json.dumps(rows), encoding="utf-8")

    def import_jobs(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.seed.main()
        self.db.executescript(self.seed.OUTPUT_FILE.read_text(encoding="utf-8"))

    def row(self, url):
        return self.db.execute("SELECT * FROM jobs WHERE job_url = ?", (url,)).fetchone()

    def test_fresh_sources_override_legacy_and_preserve_clicks_on_repeat(self):
        url = "https://www.104.com.tw/job/abc"
        self.write(self.legacy, "jobs.json", [{
            "title": "Old title", "company_name": "Example", "job_url": url,
            "location": "Old location", "source": "104", "salary_min": 100,
        }])
        self.import_jobs()
        self.db.execute("UPDATE jobs SET click_count = 17 WHERE job_url = ?", (url,))
        self.db.commit()
        fresh = {
            "job_name": "Engineer", "company": "Example", "link": url + "?jobsource=refresh",
            "area": "台北市", "appeared_date": "20261009", "salary_low": 60000,
            "salary_high": 90000, "description": "Updated engineering role",
        }
        self.write(self.fresh, "104_jobs_search.json", [fresh])
        self.write(self.fresh, "linkedin_jobs.json", [{
            "job_name": "Data Engineer", "company": "Linked Example",
            "link": "https://www.linkedin.com/jobs/view/123?trackingId=abc",
            "location": "Taiwan", "posted_date": "2026-10-08",
        }])
        self.import_jobs()
        row = self.row(url)
        self.assertEqual((row["title"], row["location"], row["date_posted"]),
                         ("Engineer", "台北市", "2026-10-09"))
        self.assertEqual((row["salary_min"], row["salary_max"], row["click_count"]),
                         (60000, 90000, 17))
        linked = self.row("https://www.linkedin.com/jobs/view/123")
        self.assertIsNotNone(linked)
        self.assertEqual((linked["source"], linked["location"], linked["date_posted"]),
                         ("linkedin", "Taiwan", "2026-10-08"))
        fresh["salary_low"] = 70000
        self.write(self.fresh, "104_jobs_search.json", [fresh])
        self.import_jobs()
        self.assertEqual(self.row(url)["salary_min"], 70000)
        self.assertEqual(self.row(url)["click_count"], 17)
        self.assertEqual(self.db.execute("SELECT count(*) FROM jobs").fetchone()[0], 2)

    def test_distinct_urls_with_same_title_and_company_are_preserved(self):
        self.write(self.fresh, "104_jobs_search.json", [
            {"job_name": "Engineer", "company": "Example", "link": link}
            for link in ["https://www.104.com.tw/job/one", "https://www.104.com.tw/job/two"]
        ])
        self.import_jobs()
        self.assertEqual(self.db.execute("SELECT count(*) FROM jobs").fetchone()[0], 2)

    def test_existing_tracking_url_keeps_clicks_when_fresh_tracking_changes(self):
        stored_url = "https://www.104.com.tw/job/abc?jobsource=old"
        self.write(self.legacy, "jobs.json", [{
            "title": "Engineer", "company_name": "Example", "job_url": stored_url,
            "source": "104",
        }])
        self.import_jobs()
        self.db.execute("UPDATE jobs SET click_count = 23")
        self.db.commit()
        self.write(self.fresh, "104_jobs_search.json", [{
            "job_name": "Updated Engineer", "company": "Example",
            "link": "https://www.104.com.tw/job/abc?jobsource=new",
        }])
        self.import_jobs()
        row = self.row(stored_url)
        self.assertIsNotNone(row)
        self.assertEqual((row["title"], row["click_count"]), ("Updated Engineer", 23))
        self.assertEqual(self.db.execute("SELECT count(*) FROM jobs").fetchone()[0], 1)

    def test_missing_fresh_files_keep_legacy_import_and_other_url_queries(self):
        urls = ["https://example.com/jobs?job=1", "https://example.com/jobs?job=2"]
        self.write(self.legacy, "jobs.json", [
            {"title": "Engineer", "company_name": "Example", "job_url": url, "source": "other"}
            for url in urls
        ])
        self.import_jobs()
        for url in urls:
            self.assertIsNotNone(self.row(url))
        self.assertEqual(self.db.execute("SELECT count(*) FROM jobs").fetchone()[0], 2)

    def test_required_fresh_sources_fail_without_overwriting_output(self):
        sentinel = "existing SQL must survive validation failure"
        valid = [{"job_name": "Engineer", "company": "Example",
                  "link": "https://www.104.com.tw/job/one"}]
        for failure in ("missing", "stale", "empty", "invalid_json", "invalid_shape"):
            with self.subTest(failure=failure):
                self.write(self.fresh, "104_jobs_search.json", valid)
                self.write(self.fresh, "linkedin_jobs.json", valid)
                path = self.fresh / "104_jobs_search.json"
                required_after = time.time() - 5
                if failure == "missing":
                    path.unlink()
                elif failure == "stale":
                    os.utime(path, (required_after - 10, required_after - 10))
                elif failure == "empty":
                    self.write(self.fresh, path.name, [])
                elif failure == "invalid_json":
                    path.write_text("{invalid", encoding="utf-8")
                elif failure == "invalid_shape":
                    self.write(self.fresh, path.name, {"jobs": valid})
                self.seed.OUTPUT_FILE.write_text(sentinel, encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(ValueError):
                        self.seed.main(require_fetched_after=required_after)
                self.assertEqual(self.seed.OUTPUT_FILE.read_text(encoding="utf-8"), sentinel)


if __name__ == "__main__":
    unittest.main()
