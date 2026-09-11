"""
104 人力銀行 — 上市櫃公司 encodedCustNo 映射
=============================================
爬取 104 公司列表 API 全部 72 頁（zone=16 上市櫃），
用公司名稱模糊比對 companies_with_salary.json，
補齊 encoded_cust_no_104 欄位。

用法：
    uv run --with requests fetch-data/fetch_104_company_ids.py
"""

import json
import re
import time
import random
from pathlib import Path

import requests

COMPANY_LIST_URL = "https://www.104.com.tw/company/ajax/list"
DATA_DIR = Path(__file__).parent.parent / "scripts" / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"

HEADERS = {
    "User-Agent": "OfferNow/1.0 (Company ID Mapping)",
    "Referer": "https://www.104.com.tw/company/search/",
    "Accept": "application/json, text/plain, */*",
}

STRIP_SUFFIXES = re.compile(
    r"(控股)?(股份有限公司|有限公司|股份公司)$"
)

STRIP_PARENS = re.compile(r"[（(][^)）]*[)）]")


def clean_name(name: str) -> str:
    name = name.strip()
    name = STRIP_PARENS.sub("", name).strip()
    name = STRIP_SUFFIXES.sub("", name).strip()
    name = name.replace("臺", "台")
    return name


def name_variants(name: str) -> list[str]:
    """Generate multiple matching keys from a single company name."""
    variants = set()
    raw = name.strip()
    variants.add(raw)
    variants.add(clean_name(raw))

    # Handle underscore-separated names like "聯電_聯華電子股份有限公司"
    # Also handle full-width underscore ＿
    normalized = raw.replace("＿", "_")
    if "_" in normalized:
        for part in normalized.split("_"):
            part = part.strip()
            if part:
                variants.add(part)
                variants.add(clean_name(part))

    # Handle parenthetical like "鈺德科技股份有限公司(錸德集團)"
    without_parens = STRIP_PARENS.sub("", raw).strip()
    if without_parens != raw:
        variants.add(without_parens)
        variants.add(clean_name(without_parens))

    # Also strip trailing 集團/企業/實業 (not in STRIP_SUFFIXES since they're valid short names)
    for v in list(variants):
        for suffix in ("集團", "企業", "實業"):
            if v.endswith(suffix) and len(v) > len(suffix):
                variants.add(v[: -len(suffix)].strip())

    # Strip offshore-registration prefixes
    for prefix in ("英屬開曼群島商", "英屬維京群島商", "新加坡商", "日商", "美商",
                    "香港商", "韓商", "荷蘭商", "瑞士商", "德商", "法商"):
        for v in list(variants):
            if v.startswith(prefix):
                stripped = v[len(prefix):]
                if stripped:
                    variants.add(stripped)
                    variants.add(clean_name(stripped))

    # Strip "台灣分公司" suffix
    for v in list(variants):
        for tail in ("台灣分公司", "臺灣分公司", "台灣辦事處"):
            if v.endswith(tail):
                variants.add(v[: -len(tail)].strip())

    variants.discard("")
    return list(variants)


def fetch_all_104_companies() -> list[dict]:
    """Fetch all pages of the 104 listed-company API."""
    session = requests.Session()
    session.headers.update(HEADERS)

    all_companies = []
    page = 1
    last_page = None

    while True:
        params = {
            "zone": 16,
            "pageSize": 20,
            "page": page,
        }

        print(f"  page {page}" + (f"/{last_page}" if last_page else ""), end=" … ")

        try:
            resp = session.get(COMPANY_LIST_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"FAIL: {e}")
            break

        items = data.get("data", [])
        pagination = data.get("metadata", {}).get("pagination", {})
        last_page = pagination.get("lastPage", page)

        print(f"{len(items)} companies")
        all_companies.extend(items)

        if page >= last_page:
            break

        page += 1
        time.sleep(0.5 + random.uniform(0, 0.5))

    return all_companies


def build_104_lookup(companies_104: list[dict]) -> dict:
    """Build name → {encodedCustNo, jobCount} lookup with multiple key variants."""
    lookup = {}
    for item in companies_104:
        name = item.get("name", "")
        info = {
            "encoded_cust_no": item.get("encodedCustNo", ""),
            "job_count": item.get("jobCount", 0),
        }
        for variant in name_variants(name):
            if variant not in lookup:
                lookup[variant] = info
    return lookup


def main():
    print("=" * 60)
    print("OfferNow — 104 Company ID Mapping (All Pages)")
    print("=" * 60)

    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    before = sum(1 for c in companies if c.get("encoded_cust_no_104"))
    print(f"\nBefore: {before}/{len(companies)} mapped ({before*100//len(companies)}%)")

    print("\nFetching 104 company list (zone=16, all pages)…")
    companies_104 = fetch_all_104_companies()
    print(f"Fetched {len(companies_104)} companies from 104")

    lookup = build_104_lookup(companies_104)
    new_matches = 0

    for company in companies:
        if company.get("encoded_cust_no_104"):
            continue

        full_name = company.get("name", "")
        short = company.get("short_name", "")

        info = None
        for variant in name_variants(full_name):
            info = lookup.get(variant)
            if info:
                break
        if not info and short:
            for variant in name_variants(short):
                info = lookup.get(variant)
                if info:
                    break

        if info:
            company["encoded_cust_no_104"] = info["encoded_cust_no"]
            if info["job_count"]:
                company["job_count_104"] = info["job_count"]
            new_matches += 1

    after = sum(1 for c in companies if c.get("encoded_cust_no_104"))
    print(f"\nNew matches: {new_matches}")
    print(f"After: {after}/{len(companies)} mapped ({after*100//len(companies)}%)")

    with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)
    print(f"Saved to {COMPANIES_FILE}")

    unmatched_104 = []
    mapped_ids = {c.get("encoded_cust_no_104") for c in companies if c.get("encoded_cust_no_104")}
    for item in companies_104:
        if item.get("encodedCustNo") not in mapped_ids:
            unmatched_104.append(item.get("name", ""))
    if unmatched_104:
        print(f"\n104 companies not matched to any stock_id: {len(unmatched_104)}")
        for name in unmatched_104[:10]:
            print(f"  - {name}")
        if len(unmatched_104) > 10:
            print(f"  … and {len(unmatched_104) - 10} more")


if __name__ == "__main__":
    main()
