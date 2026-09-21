"""
全球 AI 職缺爬蟲（via JobSpy）
==============================
- 使用 JobSpy 同時搜 LinkedIn, Indeed, Glassdoor, Google Jobs
- 專注 AI/ML/LLM 相關全球遠端職缺
- 遵守合理請求頻率
"""

import json
import time
from datetime import datetime
from pathlib import Path

from jobspy import scrape_jobs

DATA_DIR = Path(__file__).parent / "data"

SEARCHES = [
    {"term": "AI engineer remote", "location": ""},
    {"term": "machine learning engineer remote", "location": ""},
    {"term": "LLM engineer remote", "location": ""},
    {"term": "AI product manager", "location": ""},
    {"term": "generative AI", "location": ""},
    {"term": "prompt engineer remote", "location": ""},
    {"term": "MLOps engineer remote", "location": ""},
    {"term": "data scientist AI remote", "location": ""},
    {"term": "AI engineer", "location": "Taiwan"},
    {"term": "machine learning", "location": "Taiwan"},
    {"term": "AI product manager", "location": "Taiwan"},
]

SITES = ["linkedin", "indeed", "glassdoor", "google"]


def main():
    print("=" * 60)
    print("OfferNow — Global AI Jobs via JobSpy")
    print(f"Sites: {', '.join(SITES)}")
    print("=" * 60)

    all_jobs = []

    for i, search in enumerate(SEARCHES):
        term = search["term"]
        location = search["location"] or "Worldwide"
        print(f"\n[{i+1}/{len(SEARCHES)}] '{term}' @ {location}")

        try:
            kwargs = {
                "site_name": SITES,
                "search_term": term,
                "results_wanted": 25,
                "hours_old": 720,
                "linkedin_fetch_description": True,
            }
            if search["location"]:
                kwargs["location"] = search["location"]
                kwargs["country_indeed"] = search["location"]

            results = scrape_jobs(**kwargs)

            for _, row in results.iterrows():
                job = {
                    "title": str(row.get("title", "")),
                    "company_name": str(row.get("company", "")),
                    "location": str(row.get("location", "")),
                    "date_posted": str(row.get("date_posted", "")),
                    "job_url": str(row.get("job_url", "")),
                    "source": str(row.get("site", "")),
                    "description": str(row.get("description", ""))[:500],
                    "salary_min": row.get("min_amount") if row.get("min_amount") else None,
                    "salary_max": row.get("max_amount") if row.get("max_amount") else None,
                    "job_type": "global_remote" if not search["location"] else "",
                }
                all_jobs.append(job)

            print(f"  → {len(results)} jobs found")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        time.sleep(5)

    seen = set()
    unique = []
    for job in all_jobs:
        key = (job["title"], job["company_name"], job["job_url"])
        if key not in seen:
            seen.add(key)
            unique.append(job)

    print(f"\n{'=' * 60}")
    print(f"Total: {len(all_jobs)} → {len(unique)} unique")

    by_source = {}
    for j in unique:
        by_source.setdefault(j["source"], []).append(j)
    for src, jobs in sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {src}: {len(jobs)}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    archive_dir = DATA_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for path in [DATA_DIR / "global_ai_jobs.json", archive_dir / f"global_ai_jobs_{ts}.json"]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved {len(unique)} jobs to {DATA_DIR / 'global_ai_jobs.json'}")
    print("Done!")


if __name__ == "__main__":
    main()
