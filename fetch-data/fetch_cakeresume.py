"""
CakeResume (cake.me) 職缺爬蟲
==============================
- 使用 Google 搜尋索引取得 CakeResume 個別職缺頁面
- Cloudflare 阻擋直接存取，改從搜尋引擎抓取已索引的職缺
- 僅爬取公開可見資料
"""

import json
import re
import time
import random
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

DATA_DIR = Path(__file__).parent / "data"

SEARCHES = [
    "AI engineer",
    "machine learning engineer",
    "LLM engineer",
    "data scientist",
    "AI product manager",
    "prompt engineer",
    "backend engineer",
    "fullstack engineer",
    "frontend engineer",
    "python engineer",
    "MLOps",
    "NLP engineer",
    "deep learning",
    "AI 工程師",
    "後端工程師",
    "全端工程師",
    "前端工程師",
    "產品經理",
]


def search_google(query: str, session: requests.Session) -> list[dict]:
    results = []

    for start in [0, 10, 20]:
        params = {
            "q": query,
            "start": start,
            "num": 10,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8",
        }

        try:
            resp = session.get(
                "https://www.google.com/search",
                params=params,
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 429:
                print("    ⚠️  Google 限流，等 30 秒...")
                time.sleep(30)
                continue
            if resp.status_code != 200:
                print(f"    ⚠️  Google status {resp.status_code}")
                break

            html = resp.text

            pattern = r'<a[^>]*href="(https://(?:www\.)?cake\.me/companies/[^/]+/jobs/[^"&]+)"[^>]*>'
            urls_found = re.findall(pattern, html)

            for raw_url in urls_found:
                url = unquote(raw_url).split("&")[0].split("?")[0]
                if "/jobs/" not in url:
                    continue
                results.append(url)

        except Exception as e:
            print(f"    ❌ Google 搜尋失敗: {e}")
            break

        time.sleep(random.uniform(3, 6))

    return results


def parse_job_from_url(url: str) -> dict | None:
    match = re.search(r"/companies/([^/]+)/jobs/([^/?]+)", url)
    if not match:
        return None

    company_slug = match.group(1)
    job_slug = match.group(2)

    company_name = company_slug.replace("-", " ").replace("_", " ")

    title_parts = job_slug.replace("-", " ").split()
    title = " ".join(title_parts)

    hex_suffix = re.search(r"[a-f0-9]{6,}$", job_slug)
    if hex_suffix:
        title = title[: -len(hex_suffix.group())].strip()

    title = re.sub(r"\s+", " ", title).strip()

    if len(title) < 3:
        title = job_slug.replace("-", " ")

    return {
        "job_id": f"cake_{job_slug}",
        "title": title,
        "company_name": company_name,
        "location": "Taiwan",
        "date_posted": "",
        "job_url": url,
        "source": "cakeresume",
        "description": "",
        "salary_min": None,
        "salary_max": None,
        "job_type": "",
    }


def main():
    print("=" * 60)
    print("CakeResume (cake.me): Google 索引搜尋")
    print("=" * 60)

    session = requests.Session()
    all_urls = set()

    for kw in SEARCHES:
        query = f'site:cake.me/companies inurl:jobs "{kw}" Taiwan'
        print(f"\n🔍 搜尋: {kw}")
        urls = search_google(query, session)
        new_urls = set(urls) - all_urls
        all_urls.update(urls)
        print(f"    找到 {len(urls)} 個 URL，{len(new_urls)} 個新的")

        time.sleep(random.uniform(5, 10))

    print(f"\n📊 共收集 {len(all_urls)} 個不重複的職缺 URL")

    jobs = []
    for url in all_urls:
        job = parse_job_from_url(url)
        if job:
            jobs.append(job)

    seen_ids = set()
    unique = []
    for j in jobs:
        if j["job_id"] not in seen_ids:
            seen_ids.add(j["job_id"])
            unique.append(j)

    print(f"   解析出 {len(unique)} 筆職缺")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    archive_dir = DATA_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for path in [DATA_DIR / "cakeresume_jobs.json", archive_dir / f"cakeresume_jobs_{ts}.json"]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"💾 已儲存至 {DATA_DIR / 'cakeresume_jobs.json'}")
    print("Done!")


if __name__ == "__main__":
    main()
