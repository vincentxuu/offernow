"""
Arc.dev 遠端職缺爬蟲
====================
- 從 Arc.dev 公開頁面的 __NEXT_DATA__ 取得職缺 JSON
- 支援分類頁面（ai, machine-learning, python 等）
- 遵守合理請求頻率

資料來源:
  主頁:     https://arc.dev/remote-jobs
  分類頁:   https://arc.dev/remote-jobs/{category}
"""

import json
import random
import re
import time
from datetime import datetime
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent / "data"

CATEGORIES = [
    "ai",
    "machine-learning",
    "python",
    "data-science",
    "nodejs",
    "backend",
    "full-stack",
    "devops",
]


class ArcDevScraper:
    """爬取 Arc.dev 遠端職缺"""

    BASE_URL = "https://arc.dev/remote-jobs"

    def __init__(self, delay: float = 3.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def _wait(self):
        jitter = random.uniform(0.5, 1.5)
        time.sleep(self.delay * jitter)

    def _extract_next_data(self, html_text: str) -> dict | None:
        """從 HTML 中提取 __NEXT_DATA__ JSON"""
        match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            html_text,
            re.DOTALL,
        )
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

    def _parse_arc_job(self, job: dict) -> dict:
        """解析 arcJobs 格式的職缺"""
        posted_ts = job.get("postedAt", 0)
        date_posted = datetime.fromtimestamp(posted_ts).strftime("%Y-%m-%d") if posted_ts else ""

        categories = [c.get("name", "") for c in job.get("categories", [])]
        url_string = job.get("urlString", "")

        salary_min = job.get("minAnnualSalary")
        salary_max = job.get("maxAnnualSalary")

        countries = job.get("requiredCountries", [])
        location = ", ".join(countries) if countries else "Remote"

        return {
            "job_id": job.get("randomKey", ""),
            "title": job.get("title", ""),
            "company_name": "",
            "location": location,
            "date_posted": date_posted,
            "job_url": f"https://arc.dev/remote-jobs/{url_string}" if url_string else "",
            "source": "arcdev",
            "description": ", ".join(categories),
            "job_type": "global_remote",
            "salary_min": salary_min,
            "salary_max": salary_max,
        }

    def _parse_external_job(self, job: dict) -> dict:
        """解析 externalJobs 格式的職缺"""
        posted_ts = job.get("postedAt", 0)
        date_posted = datetime.fromtimestamp(posted_ts).strftime("%Y-%m-%d") if posted_ts else ""

        categories = [c.get("name", "") for c in job.get("categories", [])]
        url_string = job.get("urlString", "")

        company = job.get("company", {})
        company_name = company.get("name", "") if isinstance(company, dict) else ""

        countries = job.get("requiredCountries", [])
        location = ", ".join(countries) if countries else "Remote"

        return {
            "job_id": job.get("randomKey", ""),
            "title": job.get("title", ""),
            "company_name": company_name,
            "location": location,
            "date_posted": date_posted,
            "job_url": f"https://arc.dev/remote-jobs/{url_string}" if url_string else "",
            "source": "arcdev",
            "description": ", ".join(categories),
            "job_type": "global_remote",
            "salary_min": None,
            "salary_max": None,
        }

    def fetch_page(self, category: str | None = None) -> list[dict]:
        """抓取一個頁面的職缺"""
        url = f"{self.BASE_URL}/{category}" if category else self.BASE_URL
        label = category or "all"
        print(f"📡 Arc.dev: 抓取 {label}...")

        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"   ⚠️ HTTP {resp.status_code}")
                return []
        except requests.RequestException as e:
            print(f"   ❌ 請求失敗: {e}")
            return []

        data = self._extract_next_data(resp.text)
        if not data:
            print("   ❌ 無法解析 __NEXT_DATA__")
            return []

        props = data.get("props", {}).get("pageProps", {})
        arc_jobs = props.get("arcJobs", [])
        ext_jobs = props.get("externalJobs", [])

        jobs = []
        for j in arc_jobs:
            jobs.append(self._parse_arc_job(j))
        for j in ext_jobs:
            jobs.append(self._parse_external_job(j))

        print(f"   ✅ {len(arc_jobs)} arc + {len(ext_jobs)} external = {len(jobs)} 筆")
        return jobs

    def scrape(self, categories: list[str] | None = None) -> list[dict]:
        """抓取多個分類的職缺，去重複"""
        if categories is None:
            categories = CATEGORIES

        all_jobs = []

        # Always fetch main page first
        main_jobs = self.fetch_page(None)
        all_jobs.extend(main_jobs)
        self._wait()

        # Then fetch each category
        for cat in categories:
            jobs = self.fetch_page(cat)
            all_jobs.extend(jobs)
            self._wait()

        # Deduplicate by job_id
        seen = set()
        unique = []
        for j in all_jobs:
            if j["job_id"] and j["job_id"] not in seen:
                seen.add(j["job_id"])
                unique.append(j)

        print(f"\n📊 合併後共 {len(unique)} 筆（去重複，原始 {len(all_jobs)} 筆）")
        return unique


def save_jobs(jobs: list[dict], name: str = "arcdev_jobs"):
    """存檔（主檔 + 時間戳副本）"""
    if not jobs:
        print("⚠️  沒有資料可儲存")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    archive_dir = DATA_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    main_file = DATA_DIR / f"{name}.json"
    archive_file = archive_dir / f"{name}_{ts}.json"

    for path in [main_file, archive_file]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"💾 已儲存至 {main_file}（共 {len(jobs)} 筆）")
    print(f"💾 備份至 {archive_file}")


if __name__ == "__main__":
    scraper = ArcDevScraper(delay=3.0)

    print("=" * 60)
    print("Arc.dev: 遠端職缺爬蟲")
    print("=" * 60)

    jobs = scraper.scrape()

    # 顯示前 10 筆
    for i, job in enumerate(jobs[:10], 1):
        sal = ""
        if job["salary_min"] and job["salary_max"]:
            sal = f" | ${job['salary_min']:,}-${job['salary_max']:,}"
        elif job["salary_min"]:
            sal = f" | ${job['salary_min']:,}+"
        print(f"\n[{i}] {job['title']}")
        print(f"    公司: {job['company_name'] or '(Arc.dev)'}")
        print(f"    地點: {job['location']}{sal}")
        print(f"    技能: {job['description']}")

    save_jobs(jobs)
