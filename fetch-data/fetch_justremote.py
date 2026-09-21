"""
JustRemote 全球遠端職缺爬蟲
===========================
- JustRemote 是 React SPA，無公開 API 或 RSS
- 使用 Google 搜尋索引取得職缺 URL，再解析標題/公司
- 僅爬取公開可見資料
"""

import json
import re
import time
import random
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent / "data"
ARCHIVE_DIR = DATA_DIR / "archive"

SEARCHES = [
    "AI engineer",
    "machine learning",
    "data scientist",
    "software engineer",
    "backend developer",
    "frontend developer",
    "fullstack developer",
    "product manager",
    "devops engineer",
    "cloud engineer",
    "LLM",
    "prompt engineer",
    "MLOps",
    "platform engineer",
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
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            resp = session.get(
                "https://www.google.com/search",
                params=params,
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 429:
                print("    ⚠️  Google rate limited, waiting 30s...")
                time.sleep(30)
                continue
            if resp.status_code != 200:
                print(f"    ⚠️  Google status {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "justremote.co/remote-" not in href:
                    continue

                url_match = re.search(r"(https://justremote\.co/remote-[^\s&\"']+)", href)
                if not url_match:
                    continue

                url = url_match.group(1).split("&")[0].split("?")[0]

                title_text = a_tag.get_text(strip=True)

                results.append({
                    "url": url,
                    "title_text": title_text,
                })

        except Exception as e:
            print(f"    ❌ Google search failed: {e}")
            break

        time.sleep(random.uniform(3, 6))

    return results


def parse_job_from_result(result: dict) -> dict | None:
    url = result["url"]
    title_text = result["title_text"]

    if "/remote-jobs" == url.rstrip("/").split("justremote.co")[-1]:
        return None

    slug = url.split("/")[-1]
    if not slug or slug in ("remote-jobs", "remote-developer-jobs", "remote-design-jobs",
                            "remote-marketing-jobs", "remote-customer-service-jobs",
                            "remote-sales-jobs", "remote-writing-jobs"):
        return None

    parts = slug.rsplit("-", 1)
    if len(parts) == 2 and len(parts[1]) > 20:
        slug_clean = parts[0]
    else:
        slug_clean = slug

    title = ""
    company = ""

    if " - " in title_text and "JustRemote" not in title_text.split(" - ")[-1]:
        segments = title_text.split(" - ")
        if len(segments) >= 2:
            title = segments[0].strip()
            company = segments[1].strip().replace(" | JustRemote", "").strip()
    elif " at " in title_text:
        idx = title_text.index(" at ")
        title = title_text[:idx].strip()
        company = title_text[idx+4:].replace(" | JustRemote", "").strip()
    elif "|" in title_text:
        parts = title_text.split("|")
        title = parts[0].strip()
        if len(parts) > 1:
            company = parts[1].strip()

    if not title:
        title = slug_clean.replace("-", " ").title()
    if not company:
        company = ""

    title = title.replace(" | JustRemote", "").replace("JustRemote", "").strip()
    company = company.replace("JustRemote", "").strip()

    if not title or len(title) < 3:
        return None

    return {
        "job_id": f"justremote_{slug}",
        "title": title,
        "company_name": company,
        "location": "Remote",
        "date_posted": "",
        "job_url": url,
        "source": "justremote",
        "description": "",
        "salary_min": None,
        "salary_max": None,
        "job_type": "global_remote",
    }


def main():
    print("=" * 60)
    print("JustRemote: Google Index Search")
    print("=" * 60)

    session = requests.Session()
    all_results = []
    seen_urls = set()

    for kw in SEARCHES:
        query = f'site:justremote.co/remote- "{kw}" -inurl:remote-jobs$'
        print(f"\n🔍 Search: {kw}")
        results = search_google(query, session)
        new_results = [r for r in results if r["url"] not in seen_urls]
        for r in new_results:
            seen_urls.add(r["url"])
        all_results.extend(new_results)
        print(f"    Found {len(results)} URLs, {len(new_results)} new")

        time.sleep(random.uniform(5, 10))

    print(f"\n📊 Total unique URLs: {len(all_results)}")

    jobs = []
    seen_ids = set()
    for result in all_results:
        job = parse_job_from_result(result)
        if job and job["job_id"] not in seen_ids:
            seen_ids.add(job["job_id"])
            jobs.append(job)

    print(f"   Parsed {len(jobs)} jobs")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for path in [DATA_DIR / "justremote_jobs.json", ARCHIVE_DIR / f"justremote_jobs_{ts}.json"]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"💾 Saved to {DATA_DIR / 'justremote_jobs.json'} ({len(jobs)} jobs)")
    print("Done!")


if __name__ == "__main__":
    main()
