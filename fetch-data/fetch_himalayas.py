"""
Himalayas 全球遠端職缺爬蟲
==========================
- 使用 Himalayas 公開 JSON API
- 遵守合理請求頻率（每次請求間隔 2 秒）
- 僅爬取公開可見資料

API Endpoint:
  https://himalayas.app/jobs/api?limit=50&offset=N
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

MAX_JOBS = 2000
PAGE_SIZE = 50
MAX_PAGES = 200


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_relevant(job: dict) -> bool:
    return bool(job.get("title"))


def parse_salary(val) -> int | None:
    if not val:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def fetch_himalayas() -> list[dict]:
    print("📡 Fetching Himalayas API...")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "OfferNow/1.0 (Job Aggregator; Personal Use)",
        "Accept": "application/json",
    })

    all_jobs = []
    offset = 0

    pages = 0
    while len(all_jobs) < MAX_JOBS and pages < MAX_PAGES:
        url = f"https://himalayas.app/jobs/api?limit={PAGE_SIZE}&offset={offset}"
        print(f"  📡 offset={offset}, collected={len(all_jobs)}")

        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"  ❌ 請求失敗: {e}")
            break
        except json.JSONDecodeError:
            print("  ❌ 回傳非 JSON")
            break

        jobs = data.get("jobs", [])
        if not jobs:
            print("  📭 已無更多結果")
            break

        total = data.get("totalCount", "?")
        print(f"     本頁 {len(jobs)} 筆 (total: {total})")

        for item in jobs:
            if not is_relevant(item):
                continue

            desc = strip_html(item.get("description", "") or item.get("excerpt", ""))
            if len(desc) > 200:
                desc = desc[:200]

            pub_date_raw = item.get("pubDate", "")
            pub_date = ""
            if isinstance(pub_date_raw, (int, float)):
                try:
                    pub_date = datetime.fromtimestamp(pub_date_raw / 1000 if pub_date_raw > 1e12 else pub_date_raw).strftime("%Y-%m-%d")
                except (ValueError, TypeError, OSError):
                    pass
            elif isinstance(pub_date_raw, str) and pub_date_raw:
                pub_date = pub_date_raw[:10] if "T" in pub_date_raw else pub_date_raw

            guid = item.get("guid", "")
            slug = guid.split("/")[-1] if guid else item.get("title", "").lower().replace(" ", "-")
            company_slug = item.get("companySlug", "")
            job_url = f"https://himalayas.app/companies/{company_slug}/jobs/{slug}" if company_slug else guid

            locations = item.get("locationRestrictions", [])
            location = ", ".join(locations) if locations else "Worldwide"

            all_jobs.append({
                "job_id": f"himalayas_{slug}",
                "title": item.get("title", ""),
                "company_name": item.get("companyName", ""),
                "location": location,
                "date_posted": pub_date,
                "job_url": job_url,
                "source": "himalayas",
                "description": desc,
                "salary_min": parse_salary(item.get("minSalary")),
                "salary_max": parse_salary(item.get("maxSalary")),
                "job_type": "global_remote",
            })

        offset += PAGE_SIZE
        pages += 1
        time.sleep(2)

    print(f"\n✅ 過濾後 {len(all_jobs)} 筆相關職缺")
    return all_jobs


def save(jobs: list[dict]) -> None:
    if not jobs:
        print("⚠️  沒有資料")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    out = DATA_DIR / "himalayas_jobs.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 已儲存至 {out}（共 {len(jobs)} 筆）")

    archive = ARCHIVE_DIR / f"himalayas_jobs_{ts}.json"
    with open(archive, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 已備份至 {archive}")


if __name__ == "__main__":
    print("=" * 60)
    print("Himalayas: 全球遠端 AI / Engineering 職缺")
    print("=" * 60)

    jobs = fetch_himalayas()

    for i, job in enumerate(jobs[:10], 1):
        print(f"\n[{i}] {job['title']}")
        print(f"    公司: {job['company_name']}")
        print(f"    地點: {job['location']}")
        print(f"    日期: {job['date_posted']}")
        if job["salary_min"] or job["salary_max"]:
            print(f"    薪資: ${job['salary_min'] or '?'} - ${job['salary_max'] or '?'}")

    save(jobs)
    print("\nDone!")
