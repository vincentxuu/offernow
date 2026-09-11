"""
OfferNow MCP Server
===================
讓 Claude 能直接查詢上市櫃公司資料、職缺、薪資排行與產業趨勢。

使用：
    uv run mcp_server.py

安裝：
    claude mcp add -s user offernow -- bash -c "cd /path/to/offernow/fetch-data && uv run mcp_server.py"
"""

import datetime
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("offernow")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
SCRIPTS_DATA_DIR = BASE_DIR.parent / "scripts" / "data"

_companies_cache: list[dict] | None = None
_jobs_cache: list[dict] | None = None


def _load_companies() -> list[dict]:
    global _companies_cache
    if _companies_cache is not None:
        return _companies_cache
    path = SCRIPTS_DATA_DIR / "companies_with_salary.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        _companies_cache = json.load(f)
    return _companies_cache


def _load_jobs() -> list[dict]:
    global _jobs_cache
    if _jobs_cache is not None:
        return _jobs_cache
    path = SCRIPTS_DATA_DIR / "jobs.json"
    if not path.exists():
        _jobs_cache = []
        return _jobs_cache
    with open(path, encoding="utf-8") as f:
        _jobs_cache = json.load(f)
    return _jobs_cache


def _compact_company(c: dict) -> dict:
    return {
        "stock_id": c.get("stock_id"),
        "name": c.get("name"),
        "short_name": c.get("short_name"),
        "industry": c.get("industry"),
        "market": c.get("market"),
        "salary_median_k": c.get("salary_median_k"),
        "salary_mean_k": c.get("salary_mean_k"),
        "employee_count": c.get("employee_count"),
        "market_cap": c.get("market_cap"),
        "revenue_yoy_pct": c.get("revenue_yoy_pct"),
        "job_count_104": c.get("job_count_104", 0),
        "job_count_linkedin": c.get("job_count_linkedin", 0),
    }


# ── Company Tools ────────────────────────────────────────────


@mcp.tool()
def search_companies(
    keyword: str = "",
    industry: str = "",
    market: str = "",
    min_salary_median_k: int = 0,
    min_market_cap: float = 0,
    has_jobs: bool = False,
    limit: int = 30,
    offset: int = 0,
) -> dict:
    """
    搜尋上市櫃公司。支援名稱/產業關鍵字、市場別、薪資與市值門檻篩選。

    Args:
        keyword:             公司名稱或簡稱關鍵字
        industry:            產業別關鍵字（如「半導體」「金融」「電腦」）
        market:              "listed"（上市）或 "otc"（上櫃），空字串不篩
        min_salary_median_k: 最低薪資中位數（千元），0 不篩
        min_market_cap:      最低市值（億元），0 不篩
        has_jobs:            只顯示有職缺的公司
        limit:               回傳筆數（預設 30）
        offset:              分頁起始位置
    """
    companies = _load_companies()
    results = []
    kw = keyword.lower()

    for c in companies:
        if kw:
            name = (c.get("name") or "").lower()
            short = (c.get("short_name") or "").lower()
            if kw not in name and kw not in short:
                continue
        if industry:
            ind = (c.get("industry") or "").lower()
            if industry.lower() not in ind:
                continue
        if market and c.get("market") != market:
            continue
        if min_salary_median_k and (c.get("salary_median_k") or 0) < min_salary_median_k:
            continue
        if min_market_cap and (c.get("market_cap") or 0) < min_market_cap:
            continue
        if has_jobs:
            total = (c.get("job_count_104") or 0) + (c.get("job_count_linkedin") or 0)
            if total == 0:
                continue
        results.append(c)

    total = len(results)
    page = results[offset : offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "count": len(page),
        "results": [_compact_company(c) for c in page],
    }


@mcp.tool()
def get_company(stock_id: str) -> dict:
    """
    取得單一公司的完整資料（基本資料、薪資、營收、職缺數）。

    Args:
        stock_id: 股票代號（如 "2330" 台積電、"2454" 聯發科）
    """
    companies = _load_companies()
    for c in companies:
        if c.get("stock_id") == stock_id:
            return c
    return {"error": f"找不到股票代號 {stock_id}"}


@mcp.tool()
def get_top_salaries(
    limit: int = 20,
    market: str = "",
    industry: str = "",
) -> dict:
    """
    薪資中位數排行榜，可依市場別或產業篩選。

    Args:
        limit:    回傳筆數（預設 20）
        market:   "listed" 或 "otc"，空字串不篩
        industry: 產業別關鍵字
    """
    companies = _load_companies()
    filtered = []

    for c in companies:
        if not c.get("salary_median_k"):
            continue
        if market and c.get("market") != market:
            continue
        if industry and industry.lower() not in (c.get("industry") or "").lower():
            continue
        filtered.append(c)

    filtered.sort(key=lambda c: c.get("salary_median_k", 0), reverse=True)
    top = filtered[:limit]

    return {
        "total": len(filtered),
        "limit": limit,
        "results": [
            {
                "rank": i + 1,
                "stock_id": c.get("stock_id"),
                "name": c.get("short_name") or c.get("name"),
                "industry": c.get("industry"),
                "market": c.get("market"),
                "salary_median_k": c.get("salary_median_k"),
                "salary_mean_k": c.get("salary_mean_k"),
                "salary_median_change_pct": c.get("salary_median_change_pct"),
                "employee_count": c.get("employee_count"),
                "eps": c.get("eps"),
            }
            for i, c in enumerate(top)
        ],
    }


@mcp.tool()
def get_industry_trends(limit: int = 20) -> dict:
    """
    產業別職缺趨勢：每個產業的公司數、總職缺數，依職缺數降序排列。

    Args:
        limit: 回傳產業數（預設 20）
    """
    companies = _load_companies()
    industries: dict[str, dict] = {}

    for c in companies:
        ind = c.get("industry")
        if not ind:
            continue
        if ind not in industries:
            industries[ind] = {
                "industry": ind,
                "company_count": 0,
                "total_jobs": 0,
                "total_employees": 0,
                "avg_salary_median_k": 0,
                "_salary_sum": 0,
                "_salary_count": 0,
            }
        entry = industries[ind]
        entry["company_count"] += 1
        entry["total_jobs"] += (c.get("job_count_104") or 0) + (c.get("job_count_linkedin") or 0)
        entry["total_employees"] += c.get("employee_count") or 0
        if c.get("salary_median_k"):
            entry["_salary_sum"] += c["salary_median_k"]
            entry["_salary_count"] += 1

    results = []
    for entry in industries.values():
        if entry["_salary_count"] > 0:
            entry["avg_salary_median_k"] = round(entry["_salary_sum"] / entry["_salary_count"])
        del entry["_salary_sum"]
        del entry["_salary_count"]
        results.append(entry)

    results.sort(key=lambda x: x["total_jobs"], reverse=True)
    return {
        "total_industries": len(results),
        "limit": limit,
        "results": results[:limit],
    }


# ── Job Tools ────────────────────────────────────────────────


@mcp.tool()
def search_jobs(
    keyword: str = "",
    stock_id: str = "",
    company: str = "",
    location: str = "",
    source: str = "",
    limit: int = 30,
    offset: int = 0,
) -> dict:
    """
    搜尋職缺，支援關鍵字、公司代號、公司名、地點、來源篩選。
    不含 description 以節省 token；需詳情請用 get_job_detail。

    Args:
        keyword:  職缺名稱關鍵字
        stock_id: 股票代號（如 "2330"）
        company:  公司名稱關鍵字
        location: 地點關鍵字（如「新竹」「台北」）
        source:   "104" 或 "linkedin"，空字串不篩
        limit:    回傳筆數（預設 30）
        offset:   分頁起始位置
    """
    jobs = _load_jobs()
    results = []

    for job in jobs:
        if keyword:
            title = (job.get("title") or "").lower()
            if keyword.lower() not in title:
                continue
        if stock_id and job.get("stock_id") != stock_id:
            continue
        if company:
            cname = (job.get("company_name") or "").lower()
            if company.lower() not in cname:
                continue
        if location:
            loc = (job.get("location") or "").lower()
            if location.lower() not in loc:
                continue
        if source and job.get("source") != source:
            continue
        results.append(job)

    total = len(results)
    page = results[offset : offset + limit]

    compact_page = [
        {k: v for k, v in job.items() if k != "description"}
        for job in page
    ]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "count": len(compact_page),
        "results": compact_page,
    }


@mcp.tool()
def list_local_data() -> dict:
    """
    列出本地已有的資料檔案，包含筆數與最後更新時間。
    在做任何分析前先呼叫這個確認資料狀態。
    """
    result = {}

    companies = _load_companies()
    result["companies"] = {"count": len(companies)}

    jobs = _load_jobs()
    result["jobs"] = {"count": len(jobs)}

    for name in ["104_jobs_search.json", "linkedin_jobs.json"]:
        path = DATA_DIR / name
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            stat = path.stat()
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            result[name] = {"count": len(data), "updated": mtime}
        else:
            result[name] = {"count": 0, "updated": None}

    return result


if __name__ == "__main__":
    mcp.run()
