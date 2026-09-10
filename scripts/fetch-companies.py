#!/usr/bin/env python3
"""
抓取台灣全部上市櫃公司基本資料 + MOPS 薪資揭露，存成 JSON。

資料來源（全部免費、不需驗證）：
- TWSE OpenAPI: 上市公司基本資料
- TPEx OpenAPI: 上櫃公司基本資料
- MOPS: 非主管全時員工薪資資訊（POST HTML parse）

用法：
    uv run scripts/fetch-companies.py
    # 或
    python3 scripts/fetch-companies.py
"""

import json
import ssl
import time
import re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from html.parser import HTMLParser

OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {"User-Agent": "OfferNow/1.0 (data aggregation)"}

# TPEx 的 SSL 憑證缺 Subject Key Identifier，需要放寬驗證
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def fetch_json(url: str) -> list | dict:
    req = Request(url, headers=HEADERS)
    ctx = _ssl_ctx if "tpex.org.tw" in url else None
    with urlopen(req, timeout=30, context=ctx) as resp:
        return json.loads(resp.read())


def fetch_twse_companies() -> list[dict]:
    """上市公司基本資料 (TWSE OpenAPI)"""
    print("Fetching TWSE listed companies...")
    raw = fetch_json("https://openapi.twse.com.tw/v1/opendata/t187ap03_L")
    companies = []
    for r in raw:
        companies.append({
            "stock_id": r.get("公司代號", "").strip(),
            "name": r.get("公司名稱", "").strip(),
            "short_name": r.get("公司簡稱", "").strip(),
            "industry": r.get("產業別", "").strip(),
            "market": "listed",
            "chairman": r.get("董事長", "").strip(),
            "gm": r.get("總經理", "").strip(),
            "address": r.get("住址", "").strip(),
            "phone": r.get("電話", "").strip(),
            "established": r.get("成立日期", "").strip(),
            "listed_date": r.get("上市日期", "").strip(),
            "capital": r.get("實收資本額", "").strip(),
            "tax_id": r.get("營利事業統一編號", "").strip(),
        })
    print(f"  → {len(companies)} listed companies")
    return companies


def fetch_tpex_companies() -> list[dict]:
    """上櫃公司基本資料 (TPEx OpenAPI)"""
    print("Fetching TPEx OTC companies...")
    raw = fetch_json("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O")
    companies = []
    for r in raw:
        companies.append({
            "stock_id": r.get("SecuritiesCompanyCode", "").strip(),
            "name": r.get("CompanyName", "").strip(),
            "short_name": r.get("CompanyAbbreviation", r.get("公司簡稱", "")).strip() if r.get("CompanyAbbreviation") or r.get("公司簡稱") else "",
            "industry": r.get("IndustryCategory", r.get("產業類別", "")).strip() if r.get("IndustryCategory") or r.get("產業類別") else "",
            "market": "otc",
            "chairman": r.get("Chairman", r.get("董事長", "")).strip() if r.get("Chairman") or r.get("董事長") else "",
            "gm": r.get("GeneralManager", r.get("總經理", "")).strip() if r.get("GeneralManager") or r.get("總經理") else "",
            "address": r.get("Address", r.get("住址", "")).strip() if r.get("Address") or r.get("住址") else "",
            "phone": r.get("Telephone", r.get("電話", "")).strip() if r.get("Telephone") or r.get("電話") else "",
            "established": r.get("DateOfIncorporation", r.get("成立日期", "")).strip() if r.get("DateOfIncorporation") or r.get("成立日期") else "",
            "listed_date": r.get("DateOfListing", r.get("上櫃日期", "")).strip() if r.get("DateOfListing") or r.get("上櫃日期") else "",
            "capital": r.get("PaidInCapital", r.get("實收資本額", "")).strip() if r.get("PaidInCapital") or r.get("實收資本額") else "",
            "tax_id": r.get("UnifiedBusinessNo", r.get("營利事業統一編號", "")).strip() if r.get("UnifiedBusinessNo") or r.get("營利事業統一編號") else "",
        })
    print(f"  → {len(companies)} OTC companies")
    return companies


class MOPSTableParser(HTMLParser):
    """Parse MOPS salary disclosure HTML table."""

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


def fetch_mops_salary(market: str = "sii", year: int = 114) -> list[dict]:
    """
    MOPS 非主管全時員工薪資資訊。
    market: sii (上市) / otc (上櫃)
    year: 民國年 (114 = 2025)
    """
    market_label = "listed" if market == "sii" else "otc"
    print(f"Fetching MOPS salary ({market_label}, year {year})...")

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

    ctx = _ssl_ctx if "twse.com.tw" in "mopsov.twse.com.tw" else None
    with urlopen(req, timeout=60, context=ctx) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    parser = MOPSTableParser()
    parser.feed(html)

    salaries = []
    for row in parser.rows:
        stock_id = row[1] if len(row) > 1 else ""
        if not stock_id or not re.match(r"^\d{4,6}$", stock_id):
            continue

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

        salaries.append({
            "stock_id": stock_id,
            "company_name": row[2] if len(row) > 2 else "",
            "industry": row[0] if len(row) > 0 else "",
            "salary_total_k": safe_int(row[3]) if len(row) > 3 else None,
            "employee_count": safe_int(row[4]) if len(row) > 4 else None,
            "salary_mean_k": safe_int(row[5]) if len(row) > 5 else None,
            "salary_mean_prev_k": safe_int(row[6]) if len(row) > 6 else None,
            "salary_mean_change_pct": safe_float(row[7]) if len(row) > 7 else None,
            "salary_median_k": safe_int(row[8]) if len(row) > 8 else None,
            "salary_median_prev_k": safe_int(row[9]) if len(row) > 9 else None,
            "salary_median_change_pct": safe_float(row[10]) if len(row) > 10 else None,
            "eps": safe_float(row[11]) if len(row) > 11 else None,
            "market": market_label,
            "year": year,
        })

    print(f"  → {len(salaries)} companies with salary data")
    return salaries


def main():
    print("=" * 60)
    print("OfferNow Data Pipeline — Fetching Company Data")
    print("=" * 60)

    # 1. TWSE + TPEx companies
    twse = fetch_twse_companies()
    time.sleep(2)
    tpex = fetch_tpex_companies()

    all_companies = twse + tpex
    print(f"\nTotal companies: {len(all_companies)}")

    # Save companies
    companies_file = OUTPUT_DIR / "companies.json"
    with open(companies_file, "w", encoding="utf-8") as f:
        json.dump(all_companies, f, ensure_ascii=False, indent=2)
    print(f"Saved to {companies_file}")

    # 2. MOPS salary
    time.sleep(3)
    salary_listed = fetch_mops_salary("sii", 114)
    time.sleep(3)
    salary_otc = fetch_mops_salary("otc", 114)

    all_salaries = salary_listed + salary_otc
    print(f"\nTotal salary records: {len(all_salaries)}")

    salary_file = OUTPUT_DIR / "salaries.json"
    with open(salary_file, "w", encoding="utf-8") as f:
        json.dump(all_salaries, f, ensure_ascii=False, indent=2)
    print(f"Saved to {salary_file}")

    # 3. Merge: company + salary
    salary_map = {s["stock_id"]: s for s in all_salaries}

    merged = []
    for c in all_companies:
        s = salary_map.get(c["stock_id"], {})
        industry = s.get("industry") or c.get("industry", "")
        merged.append({
            **c,
            "industry": industry,
            "salary_median_k": s.get("salary_median_k"),
            "salary_mean_k": s.get("salary_mean_k"),
            "salary_median_change_pct": s.get("salary_median_change_pct"),
            "employee_count": s.get("employee_count"),
            "eps": s.get("eps"),
            "salary_year": s.get("year"),
        })

    matched = sum(1 for m in merged if m["salary_median_k"] is not None)
    print(f"\nMerged: {len(merged)} companies, {matched} with salary data")

    merged_file = OUTPUT_DIR / "companies_with_salary.json"
    with open(merged_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Saved to {merged_file}")

    # Quick stats
    with_salary = [m for m in merged if m["salary_median_k"] is not None]
    if with_salary:
        top5 = sorted(with_salary, key=lambda x: x["salary_median_k"] or 0, reverse=True)[:5]
        print("\n--- TOP 5 薪資中位數 ---")
        for i, c in enumerate(top5, 1):
            print(f"  {i}. {c['short_name'] or c['name']} ({c['stock_id']}) — {c['salary_median_k']} 仟元 ({c['market']})")

    print("\nDone!")


if __name__ == "__main__":
    main()
