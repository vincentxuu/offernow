#!/usr/bin/env python3
"""
抓取 MOPS 完整 31 欄位的薪資揭露資料，合併到 companies_with_salary.json。

包含：核心薪資、性別薪資、同業比較、薪資統計旗標、公司自述。

用法：
    python3 scripts/fetch-mops-full.py
"""

import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from html.parser import HTMLParser

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"
MOPS_FULL_FILE = DATA_DIR / "mops_full.json"

HEADERS = {"User-Agent": "OfferNow/1.0 (data aggregation)"}


def safe_int(val: str) -> int | None:
    val = val.replace(",", "").strip()
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def safe_float(val: str) -> float | None:
    val = val.replace(",", "").replace("%", "").strip()
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def is_applicable(val: str) -> bool:
    return val.strip() not in ("不適用", "-", "", "N/A")


class MOPSTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_td = False
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []
        self.current_data = ""

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.in_td = True
            self.current_data = ""
        elif tag == "br" and self.in_td:
            self.current_data += " "

    def handle_endtag(self, tag):
        if tag == "td":
            self.in_td = False
            self.current_row.append(self.current_data.strip().replace("\xa0", "").replace(",", ""))
        elif tag == "tr":
            if self.current_row and len(self.current_row) >= 5:
                self.rows.append(self.current_row)
            self.current_row = []

    def handle_data(self, data):
        if self.in_td:
            self.current_data += data


def fetch_mops_full(market: str = "sii", year: int = 114) -> list[dict]:
    market_label = "listed" if market == "sii" else "otc"
    print(f"Fetching MOPS full ({market_label}, year {year})...")

    data = urlencode({
        "encodeURIComponent": 1,
        "step": 1,
        "firstin": 1,
        "TYPEK": market,
        "RYEAR": year,
        "code": "",
    }).encode()

    req = Request(
        "https://mopsov.twse.com.tw/mops/web/ajax_t100sb15",
        data=data,
        headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
    )

    with urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    parser = MOPSTableParser()
    parser.feed(html)

    results = []
    for row in parser.rows:
        stock_id = row[1] if len(row) > 1 else ""
        if not stock_id or not re.match(r"^\d{4,6}$", stock_id):
            continue
        if len(row) < 26:
            continue

        entry = {
            "stock_id": stock_id,
            "company_name": row[2],
            "industry": row[0],
            "market": market_label,
            "year": year,

            # Core salary (9 fields)
            "salary_total_k": safe_int(row[3]),
            "employee_count": safe_int(row[4]),
            "salary_mean_k": safe_int(row[5]),
            "salary_mean_prev_k": safe_int(row[6]),
            "salary_mean_change_pct": safe_float(row[7]),
            "salary_median_k": safe_int(row[8]),
            "salary_median_prev_k": safe_int(row[9]),
            "salary_median_change_pct": safe_float(row[10]),
            "eps": safe_float(row[11]),

            # Gender salary (12 fields)
            "salary_male_mean_k": safe_int(row[12]) if is_applicable(row[12]) else None,
            "salary_male_mean_prev_k": safe_int(row[13]) if is_applicable(row[13]) else None,
            "salary_male_mean_change_pct": safe_float(row[14]) if is_applicable(row[14]) else None,
            "salary_female_mean_k": safe_int(row[15]) if is_applicable(row[15]) else None,
            "salary_female_mean_prev_k": safe_int(row[16]) if is_applicable(row[16]) else None,
            "salary_female_mean_change_pct": safe_float(row[17]) if is_applicable(row[17]) else None,
            "salary_male_median_k": safe_int(row[18]) if is_applicable(row[18]) else None,
            "salary_male_median_prev_k": safe_int(row[19]) if is_applicable(row[19]) else None,
            "salary_male_median_change_pct": safe_float(row[20]) if is_applicable(row[20]) else None,
            "salary_female_median_k": safe_int(row[21]) if is_applicable(row[21]) else None,
            "salary_female_median_prev_k": safe_int(row[22]) if is_applicable(row[22]) else None,
            "salary_female_median_change_pct": safe_float(row[23]) if is_applicable(row[23]) else None,

            # Industry comparison (2 fields)
            "industry_salary_avg_k": safe_int(row[24]),
            "industry_avg_eps": safe_float(row[25]),

            # Flags (3 fields)
            "flag_low_salary": row[26].strip() == "Y" if len(row) > 26 else False,
            "flag_eps_high_salary_low": row[27].strip() == "Y" if len(row) > 27 else False,
            "flag_eps_up_salary_down": row[28].strip() == "Y" if len(row) > 28 else False,

            # Company statements (2 fields)
            "salary_explanation": row[29].strip() if len(row) > 29 and row[29].strip() else None,
            "improvement_measures": row[30].strip() if len(row) > 30 and row[30].strip() else None,
        }
        results.append(entry)

    print(f"  → {len(results)} companies")
    return results


def main():
    print("=" * 60)
    print("OfferNow — MOPS Full 31-Field Scraper")
    print("=" * 60)

    listed = fetch_mops_full("sii", 114)
    time.sleep(3)
    otc = fetch_mops_full("otc", 114)

    all_mops = listed + otc
    print(f"\nTotal MOPS records: {len(all_mops)}")

    # Save full MOPS data
    with open(MOPS_FULL_FILE, "w", encoding="utf-8") as f:
        json.dump(all_mops, f, ensure_ascii=False, indent=2)
    print(f"Saved to {MOPS_FULL_FILE}")

    # Stats
    with_gender = [m for m in all_mops if m.get("salary_male_median_k") is not None]
    with_flags = [m for m in all_mops if m.get("flag_low_salary") or m.get("flag_eps_high_salary_low") or m.get("flag_eps_up_salary_down")]
    with_explanation = [m for m in all_mops if m.get("salary_explanation")]
    print(f"  With gender salary: {len(with_gender)}")
    print(f"  With any flag: {len(with_flags)}")
    print(f"  With explanation: {len(with_explanation)}")

    # Merge into companies_with_salary.json
    if COMPANIES_FILE.exists():
        with open(COMPANIES_FILE, encoding="utf-8") as f:
            companies = json.load(f)

        mops_map = {m["stock_id"]: m for m in all_mops}
        updated = 0

        for company in companies:
            m = mops_map.get(company.get("stock_id", ""))
            if not m:
                continue

            # New fields from full MOPS
            company["salary_male_median_k"] = m.get("salary_male_median_k")
            company["salary_female_median_k"] = m.get("salary_female_median_k")
            company["salary_male_mean_k"] = m.get("salary_male_mean_k")
            company["salary_female_mean_k"] = m.get("salary_female_mean_k")
            company["industry_salary_avg_k"] = m.get("industry_salary_avg_k")
            company["industry_avg_eps"] = m.get("industry_avg_eps")
            company["flag_low_salary"] = m.get("flag_low_salary", False)
            company["flag_eps_high_salary_low"] = m.get("flag_eps_high_salary_low", False)
            company["flag_eps_up_salary_down"] = m.get("flag_eps_up_salary_down", False)
            company["salary_explanation"] = m.get("salary_explanation")
            company["improvement_measures"] = m.get("improvement_measures")
            updated += 1

        with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)
        print(f"\nMerged {updated} companies into {COMPANIES_FILE}")
    else:
        print(f"\n{COMPANIES_FILE} not found, skipping merge")

    # Show a sample with gender data
    if with_gender:
        sample = with_gender[0]
        print(f"\nSample with gender salary: {sample['company_name']} ({sample['stock_id']})")
        print(f"  Male median:   {sample['salary_male_median_k']}仟")
        print(f"  Female median: {sample['salary_female_median_k']}仟")
        print(f"  Male mean:     {sample['salary_male_mean_k']}仟")
        print(f"  Female mean:   {sample['salary_female_mean_k']}仟")

    print("\nDone!")


if __name__ == "__main__":
    main()
