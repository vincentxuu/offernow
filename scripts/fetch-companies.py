#!/usr/bin/env python3
"""
抓取台灣全部上市櫃公司基本資料 + MOPS 薪資揭露 + 月營收 + 市值，存成 JSON。

資料來源（全部免費、不需驗證）：
- TWSE OpenAPI: 上市公司基本資料 + 月營收 + 每日收盤
- TPEx OpenAPI: 上櫃公司基本資料 + 月營收 + 每日收盤
- MOPS: 非主管全時員工薪資資訊（POST HTML parse）

用法：
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

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def fetch_json(url: str) -> list | dict:
    req = Request(url, headers=HEADERS)
    ctx = _ssl_ctx if "tpex.org.tw" in url else None
    with urlopen(req, timeout=30, context=ctx) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# 1. Company basics
# ---------------------------------------------------------------------------

def fetch_twse_companies() -> list[dict]:
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
            "shares_outstanding": r.get("已發行普通股數或TDR原股發行股數", "").strip(),
        })
    print(f"  → {len(companies)} listed companies")
    return companies


def fetch_tpex_companies() -> list[dict]:
    print("Fetching TPEx OTC companies...")
    raw = fetch_json("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O")
    companies = []
    for r in raw:
        def get(keys):
            for k in keys:
                v = r.get(k)
                if v:
                    return v.strip() if isinstance(v, str) else v
            return ""
        companies.append({
            "stock_id": get(["SecuritiesCompanyCode", "公司代號"]),
            "name": get(["CompanyName", "公司名稱"]),
            "short_name": get(["CompanyAbbreviation", "公司簡稱"]),
            "industry": get(["IndustryCategory", "產業類別"]),
            "market": "otc",
            "chairman": get(["Chairman", "董事長"]),
            "gm": get(["GeneralManager", "總經理"]),
            "address": get(["Address", "住址"]),
            "phone": get(["Telephone", "電話"]),
            "established": get(["DateOfIncorporation", "成立日期"]),
            "listed_date": get(["DateOfListing", "上櫃日期"]),
            "capital": get(["PaidInCapital", "實收資本額"]),
            "tax_id": get(["UnifiedBusinessNo", "營利事業統一編號"]),
            "shares_outstanding": get(["IssuedShares", "已發行普通股數"]),
        })
    print(f"  → {len(companies)} OTC companies")
    return companies


# ---------------------------------------------------------------------------
# 2. Revenue (monthly)
# ---------------------------------------------------------------------------

def fetch_twse_revenue() -> dict[str, dict]:
    print("Fetching TWSE monthly revenue...")
    raw = fetch_json("https://openapi.twse.com.tw/v1/opendata/t187ap05_L")
    result = {}
    for r in raw:
        stock_id = r.get("公司代號", "").strip()
        if not stock_id:
            continue
        result[stock_id] = {
            "revenue_latest": safe_int(r.get("營業收入-當月營收", "")),
            "revenue_prev_month": safe_int(r.get("營業收入-上月營收", "")),
            "revenue_last_year": safe_int(r.get("營業收入-去年當月營收", "")),
            "revenue_yoy_pct": safe_float(r.get("營業收入-去年同月增減(%)", "")),
            "revenue_period": r.get("資料年月", "").strip(),
        }
    print(f"  → {len(result)} listed companies with revenue")
    return result


def fetch_tpex_revenue() -> dict[str, dict]:
    print("Fetching TPEx monthly revenue...")
    raw = fetch_json("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O")
    result = {}
    for r in raw:
        stock_id = r.get("公司代號", "").strip()
        if not stock_id:
            continue
        result[stock_id] = {
            "revenue_latest": safe_int(r.get("營業收入-當月營收", "")),
            "revenue_prev_month": safe_int(r.get("營業收入-上月營收", "")),
            "revenue_last_year": safe_int(r.get("營業收入-去年當月營收", "")),
            "revenue_yoy_pct": safe_float(r.get("營業收入-去年同月增減(%)", "")),
            "revenue_period": r.get("資料年月", "").strip(),
        }
    print(f"  → {len(result)} OTC companies with revenue")
    return result


# ---------------------------------------------------------------------------
# 3. Stock price → market cap
# ---------------------------------------------------------------------------

def fetch_twse_stock_prices() -> dict[str, float]:
    print("Fetching TWSE stock prices...")
    raw = fetch_json("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL")
    result = {}
    for r in raw:
        code = r.get("Code", "").strip()
        price = safe_float(r.get("ClosingPrice", ""))
        if code and price and price > 0:
            result[code] = price
    print(f"  → {len(result)} stock prices")
    return result


def fetch_tpex_stock_prices() -> dict[str, float]:
    print("Fetching TPEx stock prices...")
    raw = fetch_json("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes")
    result = {}
    for r in raw:
        code = r.get("SecuritiesCompanyCode", "").strip()
        price = safe_float(r.get("Close", ""))
        if code and price and price > 0:
            result[code] = price
    print(f"  → {len(result)} OTC stock prices")
    return result


# ---------------------------------------------------------------------------
# 4. MOPS salary (enhanced with industry avg)
# ---------------------------------------------------------------------------

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
    market_label = "listed" if market == "sii" else "otc"
    print(f"Fetching MOPS salary ({market_label}, year {year})...")

    data = urlencode({
        "encodeURIComponent": 1, "step": 1, "firstin": 1,
        "TYPEK": market, "RYEAR": year, "code": "",
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

        salaries.append({
            "stock_id": stock_id,
            "company_name": row[2] if len(row) > 2 else "",
            "industry": row[0] if len(row) > 0 else "",
            # Core salary fields
            "salary_total_k": safe_int(row[3]) if len(row) > 3 else None,
            "employee_count": safe_int(row[4]) if len(row) > 4 else None,
            "salary_mean_k": safe_int(row[5]) if len(row) > 5 else None,
            "salary_mean_prev_k": safe_int(row[6]) if len(row) > 6 else None,
            "salary_mean_change_pct": safe_float(row[7]) if len(row) > 7 else None,
            "salary_median_k": safe_int(row[8]) if len(row) > 8 else None,
            "salary_median_prev_k": safe_int(row[9]) if len(row) > 9 else None,
            "salary_median_change_pct": safe_float(row[10]) if len(row) > 10 else None,
            "eps": safe_float(row[11]) if len(row) > 11 else None,
            # Industry comparison (columns 24-25)
            "industry_salary_avg_k": safe_int(row[24]) if len(row) > 24 else None,
            "industry_avg_eps": safe_float(row[25]) if len(row) > 25 else None,
            "market": market_label,
            "year": year,
        })

    print(f"  → {len(salaries)} companies with salary data")
    return salaries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_int(val: str | None) -> int | None:
    if val is None:
        return None
    val = str(val).replace(",", "").strip()
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def safe_float(val: str | None) -> float | None:
    if val is None:
        return None
    val = str(val).replace(",", "").replace("%", "").strip()
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("OfferNow Data Pipeline — Full Company Data")
    print("=" * 60)

    # 1. Companies
    twse = fetch_twse_companies()
    time.sleep(2)
    tpex = fetch_tpex_companies()
    all_companies = twse + tpex
    print(f"\nTotal companies: {len(all_companies)}")

    companies_file = OUTPUT_DIR / "companies.json"
    with open(companies_file, "w", encoding="utf-8") as f:
        json.dump(all_companies, f, ensure_ascii=False, indent=2)

    # 2. Revenue
    time.sleep(2)
    rev_twse = fetch_twse_revenue()
    time.sleep(2)
    rev_tpex = fetch_tpex_revenue()
    all_revenue = {**rev_twse, **rev_tpex}
    print(f"\nTotal revenue records: {len(all_revenue)}")

    # 3. Stock prices
    time.sleep(2)
    prices_twse = fetch_twse_stock_prices()
    time.sleep(2)
    prices_tpex = fetch_tpex_stock_prices()
    all_prices = {**prices_twse, **prices_tpex}
    print(f"\nTotal stock prices: {len(all_prices)}")

    # 4. MOPS salary
    time.sleep(3)
    salary_listed = fetch_mops_salary("sii", 114)
    time.sleep(3)
    salary_otc = fetch_mops_salary("otc", 114)
    all_salaries = salary_listed + salary_otc
    print(f"\nTotal salary records: {len(all_salaries)}")

    salary_file = OUTPUT_DIR / "salaries.json"
    with open(salary_file, "w", encoding="utf-8") as f:
        json.dump(all_salaries, f, ensure_ascii=False, indent=2)

    # 5. Merge everything
    salary_map = {s["stock_id"]: s for s in all_salaries}

    # Build shares outstanding map from company data
    shares_map = {}
    for c in all_companies:
        shares = safe_int(c.get("shares_outstanding"))
        if shares and shares > 0:
            shares_map[c["stock_id"]] = shares

    merged = []
    for c in all_companies:
        s = salary_map.get(c["stock_id"], {})
        r = all_revenue.get(c["stock_id"], {})
        price = all_prices.get(c["stock_id"])
        shares = shares_map.get(c["stock_id"])

        industry = s.get("industry") or c.get("industry", "")

        # Market cap = price × shares / 1億
        market_cap = None
        if price and shares:
            market_cap = round(price * shares / 100_000_000, 1)

        # Salary vs industry
        salary_median_k = s.get("salary_median_k")
        industry_salary_avg_k = s.get("industry_salary_avg_k")
        salary_vs_industry_pct = None
        if salary_median_k and industry_salary_avg_k and industry_salary_avg_k > 0:
            salary_vs_industry_pct = round(
                (salary_median_k - industry_salary_avg_k) / industry_salary_avg_k * 100, 1
            )

        merged.append({
            **c,
            "industry": industry,
            # Salary
            "salary_median_k": salary_median_k,
            "salary_mean_k": s.get("salary_mean_k"),
            "salary_median_prev_k": s.get("salary_median_prev_k"),
            "salary_mean_prev_k": s.get("salary_mean_prev_k"),
            "salary_median_change_pct": s.get("salary_median_change_pct"),
            "salary_mean_change_pct": s.get("salary_mean_change_pct"),
            "employee_count": s.get("employee_count"),
            "eps": s.get("eps"),
            "salary_year": s.get("year"),
            "industry_salary_avg_k": industry_salary_avg_k,
            "salary_vs_industry_pct": salary_vs_industry_pct,
            # Revenue
            "revenue_latest": r.get("revenue_latest"),
            "revenue_yoy_pct": r.get("revenue_yoy_pct"),
            "revenue_period": r.get("revenue_period"),
            # Market cap
            "market_cap": market_cap,
        })

    matched_salary = sum(1 for m in merged if m["salary_median_k"] is not None)
    matched_revenue = sum(1 for m in merged if m["revenue_latest"] is not None)
    matched_mcap = sum(1 for m in merged if m["market_cap"] is not None)
    print(f"\nMerged: {len(merged)} companies")
    print(f"  with salary: {matched_salary}")
    print(f"  with revenue: {matched_revenue}")
    print(f"  with market cap: {matched_mcap}")

    merged_file = OUTPUT_DIR / "companies_with_salary.json"
    with open(merged_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Saved to {merged_file}")

    # Stats
    with_mcap = [m for m in merged if m["market_cap"] is not None]
    if with_mcap:
        top5_mcap = sorted(with_mcap, key=lambda x: x["market_cap"] or 0, reverse=True)[:5]
        print("\n--- TOP 5 市值 ---")
        for i, c in enumerate(top5_mcap, 1):
            print(f"  {i}. {c['short_name'] or c['name']} ({c['stock_id']}) — {c['market_cap']} 億")

    with_salary = [m for m in merged if m["salary_median_k"] is not None]
    if with_salary:
        top5 = sorted(with_salary, key=lambda x: x["salary_median_k"] or 0, reverse=True)[:5]
        print("\n--- TOP 5 薪資中位數 ---")
        for i, c in enumerate(top5, 1):
            vs = f" (vs 同業 {c.get('salary_vs_industry_pct', '?')}%)" if c.get("salary_vs_industry_pct") is not None else ""
            print(f"  {i}. {c['short_name'] or c['name']} ({c['stock_id']}) — {c['salary_median_k']} 仟元{vs}")

    with_rev = [m for m in merged if m["revenue_yoy_pct"] is not None]
    if with_rev:
        top5_rev = sorted(with_rev, key=lambda x: x["revenue_yoy_pct"] or 0, reverse=True)[:5]
        print("\n--- TOP 5 營收年增率 ---")
        for i, c in enumerate(top5_rev, 1):
            print(f"  {i}. {c['short_name'] or c['name']} ({c['stock_id']}) — {c['revenue_yoy_pct']:.1f}%")

    print("\nDone!")


if __name__ == "__main__":
    main()
