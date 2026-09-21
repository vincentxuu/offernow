"""
Working Nomads 遠端職缺爬蟲
============================
- 使用 Working Nomads 公開 JSON API
- 單次呼叫取得全部職缺
- 僅爬取公開可見資料

API Endpoint:
  https://www.workingnomads.com/api/exposed_jobs/
"""

import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent / "data"
ARCHIVE_DIR = DATA_DIR / "archive"


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_workingnomads() -> list[dict]:
    print("📡 Fetching Working Nomads API...")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "OfferNow/1.0 (Job Aggregator; Personal Use)",
        "Accept": "application/json",
    })

    try:
        resp = session.get("https://www.workingnomads.com/api/exposed_jobs/", timeout=30)
        resp.raise_for_status()
        raw = resp.json()
    except requests.RequestException as e:
        print(f"❌ 請求失敗: {e}")
        return []
    except json.JSONDecodeError:
        print("❌ 回傳非 JSON 格式")
        return []

    if not isinstance(raw, list):
        print(f"❌ 預期 list，收到 {type(raw).__name__}")
        return []

    print(f"   取得 {len(raw)} 筆職缺")

    jobs = []
    for item in raw:
        title = item.get("title", "")
        if not title:
            continue

        desc = strip_html(item.get("description", ""))
        if len(desc) > 200:
            desc = desc[:200]

        pub_date = item.get("pub_date", "")
        if pub_date and "T" in pub_date:
            pub_date = pub_date[:10]

        url = item.get("url", "")
        job_id = url.split("/")[-2] if url else str(hash(title))

        jobs.append({
            "job_id": f"workingnomads_{job_id}",
            "title": title,
            "company_name": item.get("company_name", ""),
            "location": item.get("location", "Worldwide"),
            "date_posted": pub_date,
            "job_url": url,
            "source": "workingnomads",
            "description": desc,
            "salary_min": None,
            "salary_max": None,
            "job_type": "global_remote",
            "category": item.get("category_name", ""),
            "tags": item.get("tags", ""),
        })

    print(f"✅ {len(jobs)} 筆職缺")
    return jobs


def save(jobs: list[dict]) -> None:
    if not jobs:
        print("⚠️  沒有資料")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    out = DATA_DIR / "workingnomads_jobs.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 已儲存至 {out}（共 {len(jobs)} 筆）")

    archive = ARCHIVE_DIR / f"workingnomads_jobs_{ts}.json"
    with open(archive, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 已備份至 {archive}")


if __name__ == "__main__":
    print("=" * 60)
    print("Working Nomads: 數位遊牧遠端職缺")
    print("=" * 60)

    jobs = fetch_workingnomads()

    for i, job in enumerate(jobs[:10], 1):
        print(f"\n[{i}] {job['title']}")
        print(f"    公司: {job['company_name']}")
        print(f"    地點: {job['location']}")
        print(f"    類別: {job.get('category', '')}")

    save(jobs)
    print("\nDone!")
