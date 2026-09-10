#!/usr/bin/env python3
"""
抓取台灣上市櫃公司在 LinkedIn 的職缺數。

方式：GET LinkedIn public jobs search 頁面，從 <title> 解析職缺數
（如 "7,000+ TSMC jobs in Taiwan" → 7000）

只抓薪資 TOP 200 公司，每次間隔 3-5 秒避免 rate limit。

用法：
    python3 scripts/fetch-linkedin-jobs.py
"""

import json
import re
import time
import random
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import URLError, HTTPError

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# 公司名英文對照（LinkedIn 搜尋用英文名效果更好）
NAME_MAP = {
    "台積電": "TSMC",
    "鴻海": "Foxconn",
    "聯發科": "MediaTek",
    "台達電": "Delta Electronics",
    "華碩": "ASUS",
    "廣達": "Quanta Computer",
    "瑞昱": "Realtek",
    "聯詠": "Novatek",
    "日月光投控": "ASE Group",
    "中華電": "Chunghwa Telecom",
    "國泰金": "Cathay Financial",
    "富邦金": "Fubon Financial",
    "中信金": "CTBC Financial",
    "玉山金": "E.SUN Financial",
    "元大金": "Yuanta Financial",
    "台新金": "Taishin Financial",
    "兆豐金": "Mega Financial",
    "第一金": "First Financial",
    "華南金": "Hua Nan Financial",
    "開發金": "China Development Financial",
    "新光金": "Shin Kong Financial",
    "合庫金": "TCB Bank",
    "友達": "AUO",
    "群創": "Innolux",
    "緯創": "Wistron",
    "仁寶": "Compal",
    "和碩": "Pegatron",
    "英業達": "Inventec",
    "技嘉": "GIGABYTE",
    "微星": "MSI",
    "宏碁": "Acer",
    "大立光": "Largan Precision",
    "統一": "Uni-President",
    "台塑": "Formosa Plastics",
    "南亞": "Nan Ya Plastics",
    "台化": "Formosa Chemicals",
    "長榮": "Evergreen Marine",
    "陽明": "Yang Ming Marine",
    "萬海": "Wan Hai Lines",
    "台泥": "Taiwan Cement",
    "遠東新": "Far Eastern New Century",
    "中鋼": "China Steel",
    "正新": "Cheng Shin Rubber",
    "研華": "Advantech",
    "可成": "Catcher Technology",
    "智邦": "Accton Technology",
    "矽力-KY": "Silergy",
    "信驊": "Aspeed Technology",
    "祥碩": "ASMedia Technology",
    "力旺": "eMemory Technology",
    "世芯-KY": "Alchip Technologies",
    "創意": "GUC",
    "群聯": "Phison Electronics",
    "環球晶": "GlobalWafers",
    "穩懋": "WIN Semiconductors",
}


def fetch_linkedin_count(search_name: str) -> int | None:
    """Fetch job count from LinkedIn public search title."""
    url = f"https://www.linkedin.com/jobs/search/?keywords={quote(search_name)}&location=Taiwan"
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError, TimeoutError) as e:
        print(f"    Error: {e}")
        return None

    title_match = re.search(r"<title>(.*?)</title>", html)
    if not title_match:
        return None

    title = title_match.group(1)
    # Match patterns like "7,000+ TSMC jobs" or "25 TSMC jobs"
    num_match = re.search(r"([\d,]+)\+?\s+", title)
    if num_match:
        return int(num_match.group(1).replace(",", ""))
    return 0


def main():
    print("=" * 60)
    print("OfferNow — Fetching LinkedIn Job Counts")
    print("=" * 60)

    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    # Get top 200 by salary
    with_salary = [c for c in companies if c.get("salary_median_k") is not None]
    with_salary.sort(key=lambda x: x["salary_median_k"], reverse=True)
    top200 = with_salary[:200]

    print(f"Fetching LinkedIn counts for top {len(top200)} companies by salary...\n")

    results = {}
    for i, c in enumerate(top200):
        short = c.get("short_name") or c.get("name", "")
        stock_id = c["stock_id"]

        # Use English name if available
        search_name = NAME_MAP.get(short, short)

        print(f"  [{i+1}/{len(top200)}] {short} ({stock_id}) → search: {search_name}", end=" ", flush=True)

        count = fetch_linkedin_count(search_name)
        if count is not None:
            results[stock_id] = count
            print(f"→ {count} jobs")
        else:
            print("→ failed")

        # Rate limit: 3-5 sec random delay
        delay = 3 + random.random() * 2
        time.sleep(delay)

    print(f"\nFetched: {len(results)} companies")

    # Save LinkedIn results
    linkedin_file = DATA_DIR / "linkedin_jobs.json"
    with open(linkedin_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved to {linkedin_file}")

    # Merge into companies
    for c in companies:
        stock_id = c["stock_id"]
        if stock_id in results:
            c["job_count_linkedin"] = results[stock_id]
        else:
            c.setdefault("job_count_linkedin", 0)

    with_linkedin = [c for c in companies if c.get("job_count_linkedin", 0) > 0]
    total_linkedin = sum(c.get("job_count_linkedin", 0) for c in companies)
    print(f"Companies with LinkedIn jobs: {len(with_linkedin)}")
    print(f"Total LinkedIn job postings: {total_linkedin}")

    top10 = sorted(companies, key=lambda x: x.get("job_count_linkedin", 0), reverse=True)[:10]
    print("\n--- TOP 10 LinkedIn 職缺數 ---")
    for i, c in enumerate(top10, 1):
        print(f"  {i}. {c.get('short_name') or c.get('name')} ({c['stock_id']}) — {c.get('job_count_linkedin', 0)} 缺")

    with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)
    print(f"\nUpdated {COMPANIES_FILE}")
    print("Done!")


if __name__ == "__main__":
    main()
