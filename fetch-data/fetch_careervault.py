"""
CareerVault 職缺爬蟲
====================
- 使用 CareerVault sitemap 取得職缺 URL
- 從 URL slug 解析職缺資訊（標題、公司名）
- 篩選 AI/Engineering/Product/Data 相關職缺
"""

import json
import re
import time
import random
import requests
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

AI_KEYWORDS = [
    "ai-", "-ai-", "artificial-intelligence", "machine-learning", "deep-learning",
    "llm", "nlp", "data-scientist", "ml-engineer", "ai-engineer",
    "generative-ai", "prompt-engineer", "mlops", "computer-vision",
]

TECH_KEYWORDS = [
    "software-engineer", "backend", "frontend", "fullstack", "full-stack",
    "devops", "cloud-engineer", "platform-engineer", "sre",
    "python", "golang", "rust", "typescript", "react",
    "product-manager", "engineering-manager", "tech-lead",
    "data-engineer", "analytics-engineer",
]

ALL_KEYWORDS = AI_KEYWORDS + TECH_KEYWORDS

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/xml, text/xml",
}

SITEMAPS_TO_CHECK = list(range(255, 235, -1))


def fetch_sitemap_urls(session: requests.Session, sitemap_num: int) -> list[str]:
    url = f"https://careervault.io/sitemap-{sitemap_num}.xml"
    print(f"  📡 {url}")

    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"    ⚠️  status {resp.status_code}")
            return []
    except requests.RequestException as e:
        print(f"    ❌ {e}")
        return []

    locs = re.findall(r"<loc>([^<]+)</loc>", resp.text)
    job_urls = [u for u in locs if re.search(r"/remote/[^/]+/[^/]+/[^/]+", u)]
    return job_urls


def parse_job_from_url(url: str) -> dict | None:
    match = re.search(r"/remote/([^/]+)/([^/]+)/([^/?]+)", url)
    if not match:
        return None

    company_slug = match.group(1)
    category = match.group(2)
    job_slug = match.group(3)

    company_raw = re.sub(r"-\d+$", "", company_slug)
    company_name = company_raw.replace("-", " ").title()

    title = job_slug
    id_suffix = re.search(r"-(\d{5,})$", title)
    if id_suffix:
        title = title[: -len(id_suffix.group())]
    title = title.replace("-", " ").title()

    return {
        "job_id": f"cv_{job_slug}",
        "title": title,
        "company_name": company_name,
        "location": "Remote",
        "date_posted": "",
        "job_url": url,
        "source": "careervault",
        "description": category.replace("-", " "),
        "salary_min": None,
        "salary_max": None,
        "job_type": "global_remote",
    }


def main():
    print("=" * 60)
    print("CareerVault: Sitemap 爬取")
    print("=" * 60)

    session = requests.Session()
    all_urls = []

    for num in SITEMAPS_TO_CHECK:
        urls = fetch_sitemap_urls(session, num)
        print(f"    {len(urls)} 個職缺 URL")
        all_urls.extend(urls)
        time.sleep(random.uniform(1, 2))

    print(f"\n📊 共 {len(all_urls)} 個職缺 URL")

    filtered = all_urls

    print(f"   共 {len(filtered)} 個職缺 URL（不限職類）")

    jobs = []
    seen = set()
    for url in filtered:
        job = parse_job_from_url(url)
        if job and job["job_id"] not in seen:
            seen.add(job["job_id"])
            jobs.append(job)

    print(f"   去重後 {len(jobs)} 筆")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    archive_dir = DATA_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for path in [DATA_DIR / "careervault_jobs.json", archive_dir / f"careervault_jobs_{ts}.json"]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"💾 已儲存至 {DATA_DIR / 'careervault_jobs.json'}")
    print("Done!")


if __name__ == "__main__":
    main()
