"""
CakeResume (cake.me) 職缺爬蟲
==============================
- 使用 Playwright 繞過 Cloudflare challenge
- 遵守合理請求頻率
- 僅爬取公開可見資料
"""

import json
import time
import random
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

SEARCH_URLS = [
    "https://cake.me/jobs?q=AI&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=LLM&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=machine+learning&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=AI+PM&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=data+scientist&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=backend+engineer&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=fullstack&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=prompt+engineer&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=前端工程師&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=後端工程師&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=python&location_list%5B%5D=Taiwan",
    "https://cake.me/jobs?q=nodejs&location_list%5B%5D=Taiwan",
]


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 需要 playwright: pip install playwright && playwright install chromium")
        return

    print("=" * 60)
    print("CakeResume (cake.me): 搜尋科技/AI 職缺")
    print("=" * 60)

    all_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        for i, url in enumerate(SEARCH_URLS):
            q = url.split("q=")[1].split("&")[0].replace("+", " ")
            print(f"\n[{i+1}/{len(SEARCH_URLS)}] 🔍 搜尋: {q}")

            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(3)

                cf_challenge = page.query_selector("#challenge-running, #challenge-form")
                if cf_challenge:
                    print("  ⚠️  Cloudflare challenge，等待 10 秒...")
                    time.sleep(10)
                    page.reload(wait_until="networkidle", timeout=30000)
                    time.sleep(3)

                cards = page.query_selector_all('a[href*="/jobs/"]')
                if not cards:
                    cards = page.query_selector_all('[class*="JobSearchItem"], [class*="job-item"], [data-testid*="job"]')

                print(f"  找到 {len(cards)} 個職缺卡片")

                for card in cards:
                    try:
                        href = card.get_attribute("href") or ""
                        if not href or "/jobs/" not in href:
                            continue

                        text = card.inner_text()
                        lines = [l.strip() for l in text.split("\n") if l.strip()]

                        title = lines[0] if lines else ""
                        company = lines[1] if len(lines) > 1 else ""
                        location = ""
                        salary_text = ""

                        for line in lines:
                            if any(loc in line for loc in ["台北", "新北", "台中", "高雄", "新竹", "桃園", "台南", "Taiwan", "Remote"]):
                                location = line
                            if any(s in line for s in ["TWD", "NT$", "月薪", "年薪", "K", "萬"]):
                                salary_text = line

                        job_url = href if href.startswith("http") else f"https://cake.me{href}"

                        job_id_match = re.search(r"/jobs/([^/?]+)", href)
                        job_id = f"cake_{job_id_match.group(1)}" if job_id_match else f"cake_{hash(href)}"

                        all_jobs.append({
                            "job_id": job_id,
                            "title": title,
                            "company_name": company,
                            "location": location,
                            "date_posted": "",
                            "job_url": job_url,
                            "source": "cakeresume",
                            "description": " | ".join(lines[2:5]) if len(lines) > 2 else "",
                            "salary_text": salary_text,
                            "salary_min": None,
                            "salary_max": None,
                            "job_type": "",
                        })
                    except Exception:
                        continue

            except Exception as e:
                print(f"  ❌ 失敗: {e}")

            jitter = random.uniform(3.0, 6.0)
            time.sleep(jitter)

        browser.close()

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
    for path in [DATA_DIR / "cakeresume_jobs.json", archive_dir / f"cakeresume_jobs_{ts}.json"]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"💾 已儲存至 {DATA_DIR / 'cakeresume_jobs.json'}")
    print("Done!")


if __name__ == "__main__":
    main()
