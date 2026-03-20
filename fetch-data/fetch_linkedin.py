"""
LinkedIn 職缺爬蟲
================
- 使用 LinkedIn 公開職缺頁面
- 遵守合理請求頻率
- 僅爬取公開可見資料
"""

import requests
import time
import json
import csv
import random
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup


class LinkedInScraper:
    """爬取 LinkedIn 公開職缺"""

    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

    # 時間過濾
    TIME_FILTER = {
        "24h": "r86400",
        "1week": "r604800",
        "1month": "r2592000",
    }

    def __init__(self, delay: float = 3.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        })

    def _wait(self):
        """隨機延遲"""
        jitter = random.uniform(0.5, 1.5)
        time.sleep(self.delay * jitter)

    def search(
        self,
        keywords: str,
        location: str = "Taiwan",
        time_filter: str | None = "1week",
        max_results: int | None = None,
        filter_name: list[str] | None = None,
        fetch_details: bool = True,
    ) -> list[dict]:
        """
        搜尋 LinkedIn 職缺

        Args:
            keywords:      搜尋關鍵字
            location:      地點
            time_filter:   時間過濾（24h / 1week / 1month / None）
            max_results:   最多抓幾筆（None = 全部）
            filter_name:   過濾職缺名稱
            fetch_details: 是否抓取詳細資訊（較慢）

        Returns:
            職缺列表
        """
        all_jobs = []
        start = 0
        page_size = 25

        while True:
            if max_results and len(all_jobs) >= max_results:
                break

            params = {
                "keywords": keywords,
                "location": location,
                "start": start,
            }

            # 時間過濾
            if time_filter and time_filter in self.TIME_FILTER:
                params["f_TPR"] = self.TIME_FILTER[time_filter]

            print(f"📡 LinkedIn 搜尋: start={start}")

            try:
                resp = self.session.get(self.BASE_URL, params=params, timeout=15)
                if resp.status_code == 429:
                    print("⚠️  被限流，等待 60 秒...")
                    time.sleep(60)
                    continue
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"❌ 請求失敗: {e}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            job_cards = soup.find_all("div", class_="base-search-card")

            if not job_cards:
                print("📭 已無更多結果")
                break

            print(f"   本頁 {len(job_cards)} 筆")

            for card in job_cards:
                job = self._parse_job_card(card)
                if job:
                    all_jobs.append(job)

            start += page_size
            self._wait()

        # 過濾
        if filter_name:
            filtered = []
            for job in all_jobs:
                job_title = job.get("job_name", "").lower()
                if any(kw.lower() in job_title for kw in filter_name):
                    filtered.append(job)
            all_jobs = filtered
            print(f"   過濾後剩 {len(all_jobs)} 筆")

        # 抓取詳情
        if fetch_details and all_jobs:
            print(f"\n📋 抓取 {len(all_jobs)} 筆職缺詳情...")
            for i, job in enumerate(all_jobs):
                detail = self._fetch_detail(job["job_id"])
                if detail:
                    job.update(detail)
                print(f"   進度: {i + 1}/{len(all_jobs)}")
                self._wait()

        print(f"\n✅ 共取得 {len(all_jobs)} 筆職缺")
        return all_jobs

    def _fetch_detail(self, job_id: str) -> dict | None:
        """抓取職缺詳情"""
        if not job_id:
            return None

        url = self.DETAIL_URL.format(job_id=job_id)
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"⚠️  詳情請求失敗: {job_id} status={resp.status_code}")
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # 職缺描述
            desc_elem = soup.find("div", class_="description__text")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # 工作條件
            criteria = soup.find_all("li", class_="description__job-criteria-item")
            seniority = ""
            employment_type = ""
            job_function = ""
            industries = ""

            for item in criteria:
                header = item.find("h3")
                value = item.find("span")
                if header and value:
                    h = header.get_text(strip=True).lower()
                    v = value.get_text(strip=True)
                    if "seniority" in h:
                        seniority = v
                    elif "employment" in h:
                        employment_type = v
                    elif "function" in h:
                        job_function = v
                    elif "industr" in h:
                        industries = v

            result = {
                "description": description[:500] + "..." if len(description) > 500 else description,
                "seniority": seniority,
                "employment_type": employment_type,
                "job_function": job_function,
                "industries": industries,
            }
            if not any(result.values()):
                print(f"⚠️  詳情解析為空（HTML 結構可能已變更）: {job_id}")
            return result
        except Exception as e:
            print(f"⚠️  詳情抓取失敗: {e}")
            return None

    def _parse_job_card(self, card) -> dict | None:
        """解析職缺卡片"""
        try:
            # 職缺名稱
            title_elem = card.find("h3", class_="base-search-card__title")
            job_name = title_elem.get_text(strip=True) if title_elem else ""

            # 公司名稱
            company_elem = card.find("h4", class_="base-search-card__subtitle")
            company = company_elem.get_text(strip=True) if company_elem else ""

            # 地點
            location_elem = card.find("span", class_="job-search-card__location")
            location = location_elem.get_text(strip=True) if location_elem else ""

            # 連結
            link_elem = card.find("a", class_="base-card__full-link")
            link = link_elem.get("href", "") if link_elem else ""

            # Job ID
            job_id = ""
            entity_urn = card.get("data-entity-urn", "")
            if entity_urn:
                match = re.search(r"jobPosting:(\d+)", entity_urn)
                if match:
                    job_id = match.group(1)

            # 發布時間
            time_elem = card.find("time", class_="job-search-card__listdate")
            posted_date = ""
            if time_elem:
                posted_date = time_elem.get("datetime", "") or time_elem.get_text(strip=True)

            return {
                "job_id": job_id,
                "job_name": job_name,
                "company": company,
                "location": location,
                "posted_date": posted_date,
                "link": link,
                "source": "LinkedIn",
            }
        except Exception as e:
            print(f"⚠️  解析失敗: {e}")
            return None

    def to_csv(self, jobs: list[dict], filename: str = "linkedin_jobs.csv"):
        """存為 CSV"""
        if not jobs:
            print("⚠️  沒有資料")
            return

        all_keys = list(dict.fromkeys(k for job in jobs for k in job.keys()))
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
            writer.writeheader()
            for job in jobs:
                writer.writerow({k: job.get(k, "") for k in all_keys})
        print(f"💾 已儲存至 {filename}（共 {len(jobs)} 筆）")

    def to_json(self, jobs: list[dict], filename: str = "linkedin_jobs.json"):
        """存為 JSON"""
        if not jobs:
            print("⚠️  沒有資料")
            return

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"💾 已儲存至 {filename}（共 {len(jobs)} 筆）")


if __name__ == "__main__":
    scraper = LinkedInScraper(delay=3.0)

    print("=" * 60)
    print("LinkedIn: Node.js 後端/全端 + AI 相關職缺（Taiwan）")
    print("=" * 60)

    # 多關鍵字搜尋
    all_jobs = []
    keywords_list = [
        # Node.js 後端/全端
        "backend engineer",
        "backend developer",
        "fullstack engineer",
        "fullstack developer",
        "nodejs",
        "node.js developer",
        # AI 相關
        "AI engineer",
        "machine learning engineer",
        "LLM engineer",
        "generative AI",
        "AI agent",
        "prompt engineer",
    ]

    for kw in keywords_list:
        print(f"\n🔍 搜尋關鍵字: {kw}")
        jobs = scraper.search(
            keywords=kw,
            location="Taiwan",
            time_filter="1month",
            max_results=None,
            filter_name=None,  # 先不過濾，收集全部
            fetch_details=True,
        )
        all_jobs.extend(jobs)

    # 去重複（用 job_id）
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        if job["job_id"] not in seen:
            seen.add(job["job_id"])
            unique_jobs.append(job)

    print(f"\n📊 合併後共 {len(unique_jobs)} 筆（去重複）")
    jobs = unique_jobs

    # 顯示前 10 筆
    for i, job in enumerate(jobs[:10], 1):
        print(f"\n[{i}] {job['job_name']}")
        print(f"    公司: {job['company']}")
        print(f"    地點: {job['location']}")
        print(f"    發布: {job['posted_date']}")
        print(f"    連結: {job['link']}")

    # 輸出
    if jobs:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_dir = Path(__file__).parent / "data"
        archive_dir = data_dir / "archive"
        data_dir.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)
        scraper.to_csv(jobs, str(archive_dir / f"linkedin_jobs_{ts}.csv"))
        scraper.to_json(jobs, str(archive_dir / f"linkedin_jobs_{ts}.json"))
        scraper.to_csv(jobs, str(data_dir / "linkedin_jobs.csv"))
        scraper.to_json(jobs, str(data_dir / "linkedin_jobs.json"))
