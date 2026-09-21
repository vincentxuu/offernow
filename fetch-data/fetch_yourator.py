"""
Yourator 職缺爬蟲
=================
- 使用 Yourator 公開 JSON API
- 遵守合理請求頻率（每次請求間隔 2 秒）
- 僅爬取公開可見資料
"""

import json
import time
import random
import requests
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

SEARCHES = [
    "AI",
    "LLM",
    "machine learning",
    "deep learning",
    "NLP",
    "data scientist",
    "prompt engineer",
    "AI PM",
    "AI 產品經理",
    "MLOps",
    "backend engineer",
    "fullstack engineer",
    "nodejs",
    "python engineer",
    "前端工程師",
    "後端工程師",
    "全端工程師",
]


class YouratorScraper:
    BASE_URL = "https://www.yourator.co/api/v4/jobs"
    SEARCH_URL = "https://www.yourator.co/api/v3/search"

    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "OfferNow/1.0 (Job Aggregator)",
            "Referer": "https://www.yourator.co/jobs",
            "Accept": "application/json",
        })

    def _wait(self):
        jitter = random.uniform(0.5, 1.5)
        time.sleep(self.delay * jitter)

    def search(self, keyword: str, max_pages: int = 5) -> list[dict]:
        all_jobs = []
        page = 1

        while page <= max_pages:
            print(f"  📡 page {page}: term={keyword}")
            try:
                resp = self.session.get(
                    self.BASE_URL,
                    params={"term[]": keyword, "page": page},
                    timeout=15,
                )
                if resp.status_code == 429:
                    print("  ⚠️  被限流，等待 60 秒...")
                    time.sleep(60)
                    continue
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                print(f"  ❌ 請求失敗: {e}")
                break
            except json.JSONDecodeError:
                print("  ❌ 回傳非 JSON")
                break

            payload = data.get("payload", {})
            jobs = payload.get("jobs", [])
            if not jobs:
                break

            print(f"     本頁 {len(jobs)} 筆")

            for j in jobs:
                company = j.get("company", {})
                salary_text = j.get("salary", "")
                salary_min, salary_max = self._parse_salary(salary_text)

                all_jobs.append({
                    "job_id": f"yourator_{j.get('id', '')}",
                    "title": j.get("name", ""),
                    "company_name": company.get("brand", ""),
                    "location": j.get("location", ""),
                    "date_posted": "",
                    "job_url": f"https://www.yourator.co{j.get('path', '')}",
                    "source": "yourator",
                    "description": ", ".join(j.get("tags", [])),
                    "salary_text": salary_text,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "job_type": "",
                    "third_party_url": j.get("thirdPartyUrl", ""),
                })

            if not payload.get("hasMore", False):
                break

            page += 1
            self._wait()

        return all_jobs

    def _parse_salary(self, text: str) -> tuple:
        if not text:
            return None, None
        import re
        nums = re.findall(r"[\d,]+", text.replace(",", ""))
        if len(nums) >= 2:
            lo, hi = int(nums[0]), int(nums[1])
            if "年薪" in text:
                return lo // 12, hi // 12
            return lo, hi
        if len(nums) == 1:
            val = int(nums[0])
            if "年薪" in text:
                return val // 12, None
            return val, None
        return None, None


def main():
    scraper = YouratorScraper(delay=2.0)

    print("=" * 60)
    print("Yourator: 搜尋科技/AI 相關職缺")
    print("=" * 60)

    all_jobs = []
    for kw in SEARCHES:
        print(f"\n🔍 搜尋: {kw}")
        jobs = scraper.search(kw, max_pages=5)
        all_jobs.extend(jobs)

    seen = set()
    unique = []
    for job in all_jobs:
        if job["job_id"] not in seen:
            seen.add(job["job_id"])
            unique.append(job)

    print(f"\n📊 合併後共 {len(unique)} 筆（去重複，原始 {len(all_jobs)} 筆）")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    archive_dir = DATA_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for path in [DATA_DIR / "yourator_jobs.json", archive_dir / f"yourator_jobs_{ts}.json"]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"💾 已儲存至 {DATA_DIR / 'yourator_jobs.json'}")
    print("Done!")


if __name__ == "__main__":
    main()
