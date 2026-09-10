#!/usr/bin/env python3
"""
用 rapidfuzz 過濾 jobs.json 中的雜訊 — 去掉搜尋結果中公司不匹配的職缺。

用法：
    python3 scripts/filter-jobs.py
"""

import json
from pathlib import Path
from rapidfuzz import fuzz

DATA_DIR = Path(__file__).parent / "data"
JOBS_FILE = DATA_DIR / "jobs.json"

# Company name variants for matching
NAME_VARIANTS: dict[str, list[str]] = {
    "信驊": ["Aspeed", "Aspeed Technology", "信驊", "信驊科技"],
    "聯發科": ["MediaTek", "聯發科", "聯發科技"],
    "祥碩": ["ASMedia", "祥碩", "祥碩科技"],
    "瑞昱": ["Realtek", "瑞昱", "瑞昱半導體"],
    "台積電": ["TSMC", "Taiwan Semiconductor", "台積電", "台灣積體電路"],
    "新潤": ["新潤", "Shin Ruenn"],
    "原相": ["PixArt", "原相", "原相科技"],
    "達發": ["達發", "Airoha", "達發科技"],
    "力旺": ["eMemory", "力旺", "力旺電子"],
    "鴻勁": ["鴻勁", "鴻勁精密"],
    "聯詠": ["Novatek", "聯詠", "聯詠科技"],
    "鈊象": ["鈊象", "IGS", "鈊象電子"],
    "台達電": ["Delta", "Delta Electronics", "台達電", "台達電子"],
    "華碩": ["ASUS", "華碩", "華碩電腦"],
    "鴻海": ["Foxconn", "Hon Hai", "鴻海", "鴻海精密"],
    "廣達": ["Quanta", "Quanta Computer", "廣達", "廣達電腦"],
    "群聯": ["Phison", "群聯", "群聯電子"],
    "智邦": ["Accton", "Accton Technology", "智邦", "智邦科技"],
    "緯穎": ["Wiwynn", "緯穎", "緯穎科技"],
    "緯創": ["Wistron", "緯創", "緯創資通"],
    "仁寶": ["Compal", "Compal Electronics", "仁寶", "仁寶電腦"],
    "英業達": ["Inventec", "英業達"],
}


def is_company_match(company_listed: str, company_name: str, company_search: str) -> bool:
    if not company_listed:
        return True  # no info to filter on

    cl = company_listed.lower().strip()

    # Direct variants check
    variants = NAME_VARIANTS.get(company_name, [company_name, company_search])
    for v in variants:
        vl = v.lower()
        if vl in cl or cl in vl:
            return True

    # Also check company_search directly
    sl = company_search.lower()
    if sl in cl or cl in sl:
        return True

    # Fuzzy match
    best = max(
        fuzz.token_sort_ratio(cl, v.lower())
        for v in [company_name, company_search] + variants
    )
    return best >= 55


def main():
    print("=" * 60)
    print("OfferNow — Filtering Job Noise with RapidFuzz")
    print("=" * 60)

    with open(JOBS_FILE, encoding="utf-8") as f:
        jobs = json.load(f)

    before = len(jobs)
    filtered = []
    removed = []

    for job in jobs:
        company_listed = job.get("company_listed", "")
        company_name = job.get("company_name", "")
        company_search = job.get("company_search", "")

        if is_company_match(company_listed, company_name, company_search):
            filtered.append(job)
        else:
            removed.append(job)

    after = len(filtered)
    print(f"Before: {before} jobs")
    print(f"After:  {after} jobs")
    print(f"Removed: {before - after} jobs ({(before-after)/before*100:.1f}%)")

    if removed:
        print(f"\nRemoved examples:")
        for r in removed[:10]:
            print(f"  Searched '{r.get('company_search','')}' → got '{r.get('company_listed','')}': {r.get('title','')}")

    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    print(f"\nSaved filtered jobs to {JOBS_FILE}")

    # Save removed for review
    removed_file = DATA_DIR / "jobs_removed.json"
    with open(removed_file, "w", encoding="utf-8") as f:
        json.dump(removed, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(removed)} removed jobs to {removed_file}")

    print("\nDone!")


if __name__ == "__main__":
    main()
