"""
RemoteOK 全球遠端職缺爬蟲
========================
- 使用 RemoteOK 公開 JSON API
- 遵守合理請求頻率
- 僅爬取公開可見資料
- 用途：個人求職分析

API Endpoint:
  https://remoteok.com/api
"""

import json
import re
import time
from datetime import datetime
from html import unescape
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent / "data"
ARCHIVE_DIR = DATA_DIR / "archive"

AI_TITLE_KEYWORDS = [
    "ai ", " ai", "artificial intelligence", "machine learning", "deep learning",
    "nlp", "llm", "data scientist", "data science", "ml engineer",
    "ai engineer", "generative ai", "genai", "gpt", "prompt engineer",
    "computer vision", "neural network", "mlops", "ml ops", "ai agent",
]

AI_TAG_KEYWORDS = [
    "machine learning", "deep learning", "nlp", "llm",
    "data science", "computer vision", "tensorflow", "pytorch",
    "langchain", "rag", "mlops",
]

ENGINEERING_TITLE_KEYWORDS = [
    "software engineer", "backend engineer", "backend developer",
    "frontend engineer", "frontend developer",
    "full stack", "fullstack", "sre", "devops",
    "platform engineer", "cloud engineer", "site reliability",
    "product manager", "product owner", "technical program manager",
    "engineering manager", "tech lead", "staff engineer",
    "senior engineer", "principal engineer",
]


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_relevant(job: dict) -> bool:
    title = job.get("position", "").lower()
    tags = " ".join(job.get("tags", [])).lower()

    if any(kw in title for kw in AI_TITLE_KEYWORDS):
        return True

    if any(kw in tags for kw in AI_TAG_KEYWORDS):
        return True

    if any(kw in title for kw in ENGINEERING_TITLE_KEYWORDS):
        return True

    return False


def parse_salary(val) -> int | None:
    if not val:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def fetch_remoteok() -> list[dict]:
    print("📡 Fetching RemoteOK API...")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "OfferNow/1.0 (Job Aggregator; Personal Use)",
        "Accept": "application/json",
    })

    try:
        resp = session.get("https://remoteok.com/api", timeout=30)
        resp.raise_for_status()
        raw = resp.json()
    except requests.RequestException as e:
        print(f"❌ 請求失敗: {e}")
        return []
    except json.JSONDecodeError:
        print("❌ 回傳非 JSON 格式")
        return []

    if raw and isinstance(raw[0], dict) and "legal" in raw[0]:
        raw = raw[1:]

    print(f"   取得 {len(raw)} 筆原始資料")

    jobs = []
    for item in raw:
        if not item.get("position"):
            continue

        if not is_relevant(item):
            continue

        epoch = item.get("epoch")
        date_posted = ""
        if epoch:
            try:
                date_posted = datetime.fromtimestamp(int(epoch)).strftime("%Y-%m-%d")
            except (ValueError, TypeError, OSError):
                date_posted = item.get("date", "")

        description = strip_html(item.get("description", ""))
        if len(description) > 500:
            description = description[:500] + "..."

        job_id = str(item.get("id", ""))
        slug = item.get("slug", "")
        job_url = f"https://remoteok.com/remote-jobs/{slug}" if slug else ""

        jobs.append({
            "job_id": f"remoteok_{job_id}",
            "title": item.get("position", ""),
            "company_name": item.get("company", ""),
            "location": item.get("location", "Worldwide"),
            "date_posted": date_posted,
            "job_url": job_url,
            "source": "remoteok",
            "description": description,
            "salary_min": parse_salary(item.get("salary_min")),
            "salary_max": parse_salary(item.get("salary_max")),
            "job_type": "global_remote",
            "tags": item.get("tags", []),
        })

    print(f"✅ 過濾後 {len(jobs)} 筆相關職缺")
    return jobs


def save(jobs: list[dict]) -> None:
    if not jobs:
        print("⚠️  沒有資料")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    out = DATA_DIR / "remoteok_jobs.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 已儲存至 {out}（共 {len(jobs)} 筆）")

    archive = ARCHIVE_DIR / f"remoteok_jobs_{ts}.json"
    with open(archive, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 已備份至 {archive}")


if __name__ == "__main__":
    print("=" * 60)
    print("RemoteOK: 全球遠端 AI / Engineering 職缺")
    print("=" * 60)

    jobs = fetch_remoteok()

    for i, job in enumerate(jobs[:10], 1):
        print(f"\n[{i}] {job['title']}")
        print(f"    公司: {job['company_name']}")
        print(f"    地點: {job['location']}")
        sal = ""
        if job["salary_min"] or job["salary_max"]:
            sal = f"    薪資: ${job['salary_min'] or '?'} - ${job['salary_max'] or '?'}"
        if sal:
            print(sal)

    save(jobs)
    print("\nDone!")
