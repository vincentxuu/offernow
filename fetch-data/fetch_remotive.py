"""
Remotive 全球遠端職缺爬蟲
========================
- 使用 Remotive 公開 JSON API
- 遵守合理請求頻率
- 僅爬取公開可見資料

API Endpoint:
  https://remotive.com/api/remote-jobs
  https://remotive.com/api/remote-jobs?category=software-dev
"""

import json
import re
import time
from datetime import datetime
from html import unescape
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent / "data"
ARCHIVE_DIR = DATA_DIR / "archive"

CATEGORIES = [
    "software-dev",
    "data",
    "devops-sysadmin",
    "product",
    "design",
    "marketing",
    "customer-support",
    "sales",
    "finance-legal",
    "hr",
    "writing",
    "project-management",
    "all-others",
]

AI_KEYWORDS = [
    "ai ", " ai", "artificial intelligence", "machine learning", "deep learning",
    "nlp", "llm", "data scientist", "data science", "ml engineer",
    "ai engineer", "generative ai", "genai", "gpt", "prompt engineer",
    "computer vision", "neural network", "mlops", "ai agent",
]

ENGINEERING_KEYWORDS = [
    "software engineer", "backend engineer", "backend developer",
    "frontend engineer", "frontend developer",
    "full stack", "fullstack", "sre", "devops",
    "platform engineer", "cloud engineer", "site reliability",
    "product manager", "product owner", "technical program manager",
    "engineering manager", "tech lead", "staff engineer",
    "senior engineer", "principal engineer",
]


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_relevant(title: str, desc: str) -> bool:
    return bool(title.strip())


def fetch_remotive() -> list[dict]:
    print("📡 Fetching Remotive API...")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "OfferNow/1.0 (Job Aggregator; Personal Use)",
        "Accept": "application/json",
    })

    all_jobs_raw = []

    for cat in CATEGORIES:
        print(f"  📂 Category: {cat}")
        try:
            resp = session.get(
                f"https://remotive.com/api/remote-jobs?category={cat}",
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            cat_jobs = data.get("jobs", [])
            print(f"     {len(cat_jobs)} jobs")
            all_jobs_raw.extend(cat_jobs)
        except requests.RequestException as e:
            print(f"     ❌ Failed: {e}")
        except json.JSONDecodeError:
            print(f"     ❌ Non-JSON response")
        time.sleep(2)

    print(f"\n   Total raw: {len(all_jobs_raw)}")

    seen_ids = set()
    jobs = []
    for item in all_jobs_raw:
        job_id = item.get("id", "")
        if not job_id or job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        title = item.get("title", "")
        desc = strip_html(item.get("description", ""))

        if not is_relevant(title, desc):
            continue

        if len(desc) > 500:
            desc = desc[:500] + "..."

        salary_text = item.get("salary", "")
        salary_min = None
        salary_max = None
        if salary_text:
            nums = re.findall(r"[\d,]+", salary_text.replace(",", ""))
            if len(nums) >= 2:
                salary_min = int(nums[0])
                salary_max = int(nums[1])
            elif len(nums) == 1:
                salary_min = int(nums[0])

        pub_date = item.get("publication_date", "")
        date_posted = ""
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                date_posted = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                date_posted = pub_date[:10] if len(pub_date) >= 10 else ""

        jobs.append({
            "job_id": f"remotive_{job_id}",
            "title": title,
            "company_name": item.get("company_name", ""),
            "location": item.get("candidate_required_location", "Worldwide"),
            "date_posted": date_posted,
            "job_url": item.get("url", ""),
            "source": "remotive",
            "description": desc,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "job_type": "global_remote",
            "category": item.get("category", ""),
        })

    print(f"✅ Filtered: {len(jobs)} relevant jobs")
    return jobs


def save(jobs: list[dict]) -> None:
    if not jobs:
        print("⚠️  No data")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    out = DATA_DIR / "remotive_jobs.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to {out} ({len(jobs)} jobs)")

    archive = ARCHIVE_DIR / f"remotive_jobs_{ts}.json"
    with open(archive, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 Archived to {archive}")


if __name__ == "__main__":
    print("=" * 60)
    print("Remotive: Global Remote AI / Engineering Jobs")
    print("=" * 60)

    jobs = fetch_remotive()

    for i, job in enumerate(jobs[:10], 1):
        print(f"\n[{i}] {job['title']}")
        print(f"    Company: {job['company_name']}")
        print(f"    Location: {job['location']}")
        print(f"    Date: {job['date_posted']}")

    save(jobs)
    print("\nDone!")
