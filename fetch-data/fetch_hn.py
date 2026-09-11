"""
Hacker News "Who is Hiring?" 職缺爬蟲
=====================================
- 使用 HN Algolia API + Firebase API（公開 API）
- 抓取最新一期 "Ask HN: Who is hiring?" 的所有頂層留言
- 每則頂層留言 = 一則職缺
- 遵守合理請求頻率

API Endpoints:
  搜尋:   https://hn.algolia.com/api/v1/search_by_date
  留言:   https://hacker-news.firebaseio.com/v0/item/{id}.json
"""

import html
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent / "data"

REMOTE_KEYWORDS = [
    "remote", "onsite or remote", "remote ok", "fully remote",
    "remote-first", "work from anywhere", "wfh",
]

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "nlp", "generative ai", "gpt", "computer vision",
    "data scientist", "ml engineer", "ai engineer", "prompt engineer",
    "rag", "langchain", "openai", "diffusion", "transformer",
]


class HNScraper:
    """爬取 Hacker News Who is Hiring 職缺"""

    ALGOLIA_URL = "https://hn.algolia.com/api/v1/search_by_date"
    FIREBASE_URL = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"

    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self.session = requests.Session()

    def _wait(self):
        jitter = random.uniform(0.5, 1.5)
        time.sleep(self.delay * jitter)

    def find_latest_thread(self) -> dict | None:
        """找到最新一期 Who is Hiring 文章"""
        params = {
            "query": '"Ask HN: Who is hiring"',
            "tags": "ask_hn",
            "hitsPerPage": 5,
        }
        print("🔍 搜尋最新 Who is Hiring 文章...")
        try:
            resp = self.session.get(self.ALGOLIA_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"❌ 搜尋失敗: {e}")
            return None

        for hit in data.get("hits", []):
            title = hit.get("title", "")
            if re.match(r"Ask HN: Who is hiring\?", title, re.IGNORECASE):
                print(f"   找到: {title} (ID: {hit['objectID']}, 留言: {hit.get('num_comments', '?')})")
                return hit

        print("❌ 找不到 Who is Hiring 文章")
        return None

    def fetch_comment(self, item_id: int) -> dict | None:
        """從 Firebase API 取得單則留言"""
        url = self.FIREBASE_URL.format(item_id=item_id)
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            return None

    def _clean_html(self, text: str) -> str:
        """移除 HTML 標籤，保留純文字"""
        text = html.unescape(text)
        text = re.sub(r"<a[^>]*href=\"([^\"]+)\"[^>]*>[^<]*</a>", r"\1", text)
        text = re.sub(r"<br\s*/?>", "\n", text)
        text = re.sub(r"<p>", "\n", text)
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()

    def _parse_comment(self, comment: dict, story_date: str) -> dict | None:
        """解析一則 HN 留言為職缺"""
        text = comment.get("text", "")
        if not text or comment.get("deleted") or comment.get("dead"):
            return None

        clean = self._clean_html(text)
        lines = [l.strip() for l in clean.split("\n") if l.strip()]
        if len(lines) < 2:
            return None

        first_line = lines[0]

        # Parse pipe-separated header: Company | Role | Location | REMOTE | Full-time | URL
        parts = re.split(r"\s*\|\s*", first_line)
        company_name = parts[0].strip() if parts else ""

        SKIP_KEYWORDS = [
            "onsite", "remote", "hybrid", "office",
            "full-time", "part-time", "full time", "part time",
            "contract", "intern", "freelance",
            "http://", "https://", "www.",
        ]
        company_name = company_name.lstrip("*").strip()
        LOCATION_HINTS = [
            ",", "usa", "uk", "eu ", "germany", "france", "canada",
            "australia", "switzerland", "netherlands", "spain", "italy",
            "japan", "singapore", "india", "israel", "brazil",
            "new york", "san francisco", "london", "berlin", "tokyo",
            "nyc", "sf", "la", "seattle", "boston", "chicago",
            " ny", " ca", " tx", " wa",
        ]

        title = ""
        location = ""
        for part in parts[1:]:
            p = part.strip()
            p_lower = p.lower()
            if any(kw in p_lower for kw in SKIP_KEYWORDS):
                continue
            if not p or len(p) <= 1:
                continue
            is_location = any(hint in p_lower for hint in LOCATION_HINTS)
            if is_location and not location:
                location = p
            elif not title:
                title = p
            elif not location:
                location = p

        if not title:
            title = company_name

        # Detect remote
        text_lower = clean.lower()
        is_remote = any(kw in text_lower for kw in REMOTE_KEYWORDS)
        job_type = "global_remote" if is_remote else None

        # Parse salary
        salary_min, salary_max = self._parse_salary(clean)

        # Description: rest of text (truncated)
        description = "\n".join(lines[1:])
        if len(description) > 500:
            description = description[:497] + "..."

        comment_id = comment.get("id", "")
        posted_ts = comment.get("time", 0)
        date_posted = datetime.fromtimestamp(posted_ts).strftime("%Y-%m-%d") if posted_ts else story_date

        return {
            "job_id": str(comment_id),
            "title": title[:200],
            "company_name": company_name[:100],
            "location": location[:100],
            "date_posted": date_posted,
            "job_url": f"https://news.ycombinator.com/item?id={comment_id}",
            "source": "hackernews",
            "description": description,
            "job_type": job_type,
            "salary_min": salary_min,
            "salary_max": salary_max,
        }

    def _parse_salary(self, text: str) -> tuple[int | None, int | None]:
        """嘗試從文字中解析薪資範圍 (USD)"""
        # Match patterns like $150k-$200k, $150,000 - $200,000, 150k-200k
        patterns = [
            r"\$\s*(\d{2,3})[kK]\s*[-–—to]+\s*\$?\s*(\d{2,3})[kK]",
            r"\$\s*([\d,]+)\s*[-–—to]+\s*\$?\s*([\d,]+)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                lo, hi = m.group(1), m.group(2)
                lo = int(lo.replace(",", ""))
                hi = int(hi.replace(",", ""))
                if lo < 1000:
                    lo *= 1000
                if hi < 1000:
                    hi *= 1000
                if 30000 <= lo <= 1000000 and 30000 <= hi <= 1000000:
                    return lo, hi
        return None, None

    def scrape(self, max_comments: int | None = None) -> list[dict]:
        """抓取最新 Who is Hiring 的所有職缺"""
        thread = self.find_latest_thread()
        if not thread:
            return []

        story_id = int(thread["objectID"])
        story_date = thread.get("created_at", "")[:10]

        story = self.fetch_comment(story_id)
        if not story:
            print("❌ 無法取得文章內容")
            return []

        kid_ids = story.get("kids", [])
        if max_comments:
            kid_ids = kid_ids[:max_comments]

        print(f"\n📋 開始抓取 {len(kid_ids)} 則頂層留言...")
        jobs = []
        for i, kid_id in enumerate(kid_ids):
            comment = self.fetch_comment(kid_id)
            if not comment:
                continue

            job = self._parse_comment(comment, story_date)
            if job:
                jobs.append(job)

            if (i + 1) % 50 == 0:
                print(f"   進度: {i + 1}/{len(kid_ids)} ({len(jobs)} 筆職缺)")

            self._wait()

        print(f"\n✅ 共解析 {len(jobs)} 筆職缺")
        return jobs


def save_jobs(jobs: list[dict], name: str = "hn_jobs"):
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
    scraper = HNScraper(delay=0.5)

    print("=" * 60)
    print("Hacker News: Who is Hiring? 職缺爬蟲")
    print("=" * 60)

    jobs = scraper.scrape()

    # 顯示統計
    remote_count = sum(1 for j in jobs if j["job_type"] == "global_remote")
    with_salary = [j for j in jobs if j["salary_min"]]
    ai_jobs = [j for j in jobs if any(kw in (j["title"] + " " + j["description"]).lower() for kw in AI_KEYWORDS)]

    print(f"\n📊 統計:")
    print(f"   總職缺: {len(jobs)}")
    print(f"   遠端職缺: {remote_count}")
    print(f"   有薪資範圍: {len(with_salary)}")
    print(f"   AI 相關: {len(ai_jobs)}")

    if with_salary:
        avg_min = sum(j["salary_min"] for j in with_salary) / len(with_salary)
        avg_max = sum(j["salary_max"] for j in with_salary) / len(with_salary)
        print(f"   平均薪資: ${avg_min:,.0f} - ${avg_max:,.0f} USD")

    # 顯示前 5 筆
    for i, job in enumerate(jobs[:5], 1):
        print(f"\n[{i}] {job['title']}")
        print(f"    公司: {job['company_name']}")
        print(f"    地點: {job['location']}")
        sal = f"${job['salary_min']:,}-${job['salary_max']:,}" if job["salary_min"] else "未標示"
        print(f"    薪資: {sal}")

    save_jobs(jobs)
