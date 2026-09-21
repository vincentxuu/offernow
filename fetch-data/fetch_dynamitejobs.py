"""
Dynamite Jobs 職缺爬蟲
======================
- 爬取 dynamitejobs.com 各類別頁面的遠端職缺
- 遵守合理請求頻率
- 僅爬取公開可見資料
"""

import json
import re
import time
import random
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent / "data"

CATEGORIES = [
    "remote-development-jobs",
    "remote-data-analyst-jobs",
    "remote-product-jobs",
    "remote-design-jobs",
    "remote-marketing-jobs",
    "remote-management-operations-jobs",
    "remote-technical-support-jobs",
    "remote-sales-jobs",
    "remote-writing-jobs",
    "remote-customer-service-jobs",
    "remote-finance-jobs",
    "remote-hr-jobs",
    "remote-education-jobs",
    "remote-legal-jobs",
    "remote-accounting-jobs",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_category(session: requests.Session, category: str) -> list[dict]:
    url = f"https://dynamitejobs.com/category/{category}"
    print(f"  📡 {url}")

    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"    ⚠️  status {resp.status_code}")
            return []
    except requests.RequestException as e:
        print(f"    ❌ {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        match = re.match(r"/company/([^/]+)/remote-job/([^/]+)", href)
        if not match:
            continue

        company_slug = match.group(1)
        job_slug = match.group(2)

        parent = link
        for _ in range(5):
            if parent.parent:
                parent = parent.parent
            else:
                break

        text = parent.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        title = lines[0] if lines else job_slug.replace("-", " ").title()
        company_name = company_slug.replace("-", " ").title()

        for line in lines:
            low = line.lower()
            if company_slug.replace("-", " ") in low or company_slug.replace("-", "") in low.replace(" ", ""):
                company_name = line
                break

        job_url = f"https://dynamitejobs.com{href}"
        job_id = f"dynamite_{job_slug}"

        jobs.append({
            "job_id": job_id,
            "title": title,
            "company_name": company_name,
            "location": "Remote",
            "date_posted": "",
            "job_url": job_url,
            "source": "dynamitejobs",
            "description": category.replace("remote-", "").replace("-jobs", "").replace("-", " "),
            "salary_min": None,
            "salary_max": None,
            "job_type": "global_remote",
        })

    return jobs


def main():
    print("=" * 60)
    print("Dynamite Jobs: 遠端職缺爬取")
    print("=" * 60)

    session = requests.Session()
    all_jobs = []

    for cat in CATEGORIES:
        print(f"\n🔍 類別: {cat}")
        jobs = scrape_category(session, cat)
        print(f"    找到 {len(jobs)} 筆")
        all_jobs.extend(jobs)
        time.sleep(random.uniform(2, 4))

    seen = set()
    unique = []
    for j in all_jobs:
        if j["job_id"] not in seen:
            seen.add(j["job_id"])
            unique.append(j)

    print(f"\n📊 合併後共 {len(unique)} 筆（去重複，原始 {len(all_jobs)} 筆）")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    archive_dir = DATA_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for path in [DATA_DIR / "dynamitejobs_jobs.json", archive_dir / f"dynamitejobs_jobs_{ts}.json"]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"💾 已儲存至 {DATA_DIR / 'dynamitejobs_jobs.json'}")
    print("Done!")


if __name__ == "__main__":
    main()
