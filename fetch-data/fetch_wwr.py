"""
We Work Remotely 全球遠端職缺爬蟲
=================================
- 使用 WWR 公開 RSS feeds
- 遵守合理請求頻率（每次請求間隔 2 秒）
- 僅爬取公開可見資料
- 用途：個人求職分析

RSS Feeds:
  https://weworkremotely.com/categories/remote-programming-jobs.rss
  https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss
  https://weworkremotely.com/categories/remote-product-jobs.rss
  https://weworkremotely.com/categories/remote-data-jobs.rss
"""

import hashlib
import json
import re
import time
import random
from datetime import datetime
from html import unescape
from pathlib import Path

import feedparser

DATA_DIR = Path(__file__).parent / "data"
ARCHIVE_DIR = DATA_DIR / "archive"

FEEDS = [
    ("Programming", "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
    ("DevOps", "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"),
    ("Product", "https://weworkremotely.com/categories/remote-product-jobs.rss"),
    ("Data", "https://weworkremotely.com/categories/remote-data-jobs.rss"),
    ("Design", "https://weworkremotely.com/categories/remote-design-jobs.rss"),
    ("Marketing", "https://weworkremotely.com/categories/remote-marketing-jobs.rss"),
    ("Sales", "https://weworkremotely.com/categories/remote-sales-jobs.rss"),
    ("Customer Support", "https://weworkremotely.com/categories/remote-customer-support-jobs.rss"),
    ("Finance", "https://weworkremotely.com/categories/remote-finance-jobs.rss"),
    ("HR", "https://weworkremotely.com/categories/remote-human-resources-jobs.rss"),
    ("Writing", "https://weworkremotely.com/categories/remote-copywriting-jobs.rss"),
    ("Management", "https://weworkremotely.com/categories/remote-management-executive-jobs.rss"),
    ("All Others", "https://weworkremotely.com/categories/remote-all-other-jobs.rss"),
]


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def make_job_id(url: str) -> str:
    return "wwr_" + hashlib.md5(url.encode()).hexdigest()[:12]


def parse_entry(entry: dict, category: str) -> dict | None:
    title = entry.get("title", "").strip()
    if not title:
        return None

    parts = title.split(":", 1) if ":" in title else ("", title)
    company_name = parts[0].strip() if len(parts) == 2 else ""
    job_title = parts[1].strip() if len(parts) == 2 else title

    link = entry.get("link", "")

    published = entry.get("published_parsed")
    date_posted = ""
    if published:
        try:
            date_posted = datetime(*published[:6]).strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            pass

    description = ""
    if entry.get("summary"):
        description = strip_html(entry["summary"])
        if len(description) > 500:
            description = description[:500] + "..."

    return {
        "job_id": make_job_id(link),
        "title": job_title,
        "company_name": company_name,
        "location": "Worldwide",
        "date_posted": date_posted,
        "job_url": link,
        "source": "wwr",
        "description": description,
        "salary_min": None,
        "salary_max": None,
        "job_type": "global_remote",
        "category": category,
    }


def fetch_wwr() -> list[dict]:
    all_jobs = []
    seen_urls = set()

    for category, feed_url in FEEDS:
        print(f"📡 Fetching WWR: {category}...")

        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"❌ RSS 解析失敗 ({category}): {e}")
            continue

        if feed.bozo and not feed.entries:
            print(f"⚠️  Feed 異常 ({category}): {feed.bozo_exception}")
            continue

        count = 0
        for entry in feed.entries:
            job = parse_entry(entry, category)
            if not job:
                continue
            if job["job_url"] in seen_urls:
                continue
            seen_urls.add(job["job_url"])
            all_jobs.append(job)
            count += 1

        print(f"   {count} 筆職缺")

        jitter = random.uniform(1.5, 3.0)
        time.sleep(jitter)

    print(f"\n✅ 共取得 {len(all_jobs)} 筆 WWR 職缺")
    return all_jobs


def save(jobs: list[dict]) -> None:
    if not jobs:
        print("⚠️  沒有資料")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    out = DATA_DIR / "wwr_jobs.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 已儲存至 {out}（共 {len(jobs)} 筆）")

    archive = ARCHIVE_DIR / f"wwr_jobs_{ts}.json"
    with open(archive, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 已備份至 {archive}")


if __name__ == "__main__":
    print("=" * 60)
    print("We Work Remotely: 全球遠端職缺")
    print("=" * 60)

    jobs = fetch_wwr()

    for i, job in enumerate(jobs[:10], 1):
        print(f"\n[{i}] {job['title']}")
        print(f"    公司: {job['company_name']}")
        print(f"    分類: {job['category']}")
        print(f"    日期: {job['date_posted']}")

    save(jobs)
    print("\nDone!")
