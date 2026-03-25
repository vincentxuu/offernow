"""
OfferNow MCP Server
===================
讓 Claude 能直接操作本地職缺資料（讀取 JSON、過濾、LLM 評分）。

使用：
    uv run mcp_server.py
"""

import datetime
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from fetch import Job104Scraper
from filter import (
    pre_filter,
    score_batch_with_llm,
    build_report,
    load_jobs,
    clean_html,
    DEFAULT_PROVIDER,
)
from cover_letter import generate_cover_letter, save_cover_letter

mcp = FastMCP("offernow")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"


# ── Tools ─────────────────────────────────────────────────────


@mcp.tool()
def list_local_data() -> dict:
    """
    列出本地已有的職缺資料檔案，包含筆數與最後更新時間。
    在做任何分析前先呼叫這個確認資料狀態。
    """
    result = {}

    for name in ["104_jobs_search.json", "linkedin_jobs.json"]:
        path = DATA_DIR / name
        if path.exists():
            with open(path, encoding="utf-8") as f:
                jobs = json.load(f)
            stat = path.stat()
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            result[name] = {"count": len(jobs), "updated": mtime}
        else:
            result[name] = {"count": 0, "updated": None}

    # 也列出 archive 最新檔
    archive = DATA_DIR / "archive"
    if archive.exists():
        for pattern in ["104_jobs_search_*.json", "linkedin_jobs_*.json"]:
            files = sorted(archive.glob(pattern))
            if files:
                latest = files[-1]
                result[f"archive/{latest.name}"] = {"path": str(latest)}

    return result


@mcp.tool()
def filter_and_score_jobs(
    max_llm: int = 20,
    batch_size: int = 8,
    model: str | None = None,
) -> str:
    """
    讀取本地 JSON → 關鍵字初篩 → LLM 批次評分 → 回傳 Markdown 報告。

    Args:
        max_llm:    最多評分幾筆（預設 20，避免太慢）
        batch_size: 每批評幾筆（預設 8）
        model:      指定模型（e.g. "claude-haiku-4-5-20251001"），None 用預設
    """
    import time

    jobs_104, jobs_linkedin = load_jobs(DATA_DIR)

    if not jobs_104 and not jobs_linkedin:
        return "❌ 找不到資料，請先執行 `uv run fetch.py` 爬取職缺"

    filtered = pre_filter(jobs_104, jobs_linkedin)

    passed_104 = sum(1 for _, src, _ in filtered if src == "104")
    passed_li = sum(1 for _, src, _ in filtered if src == "linkedin")

    if max_llm < len(filtered):
        to_score = filtered[:max_llm]
        unscored_raw = filtered[max_llm:]
    else:
        to_score = filtered
        unscored_raw = []

    start = time.time()
    scored = []

    for batch_start in range(0, len(to_score), batch_size):
        batch_items = to_score[batch_start:batch_start + batch_size]
        batch_jobs = [(job, source) for job, source, _ in batch_items]

        from filter import fallback_score
        fallbacks = [fallback_score(ps) for _, _, ps in batch_items]
        results = score_batch_with_llm(batch_jobs, fallbacks, provider=DEFAULT_PROVIDER, model=model)

        for (job, source, _), (score, reason) in zip(batch_items, results):
            scored.append((job, source, score, reason))

    elapsed = time.time() - start

    stats = {
        "104_total": len(jobs_104),
        "linkedin_total": len(jobs_linkedin),
        "104_passed": passed_104,
        "linkedin_passed": passed_li,
        "llm_count": len(scored),
        "elapsed": elapsed,
        "provider": DEFAULT_PROVIDER,
        "model_tag": f"/{model}" if model else "",
    }

    report = build_report(scored, [(j, s, ps) for j, s, ps in unscored_raw], stats)

    # 存檔
    from datetime import datetime
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    archive_dir = REPORTS_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    (archive_dir / f"filter_report_{ts}.md").write_text(report, encoding="utf-8")
    (REPORTS_DIR / "filter_report.md").write_text(report, encoding="utf-8")

    return report


@mcp.tool()
def get_job_detail(job_id: str) -> dict:
    """
    從 104 取得單筆職缺的完整詳細資訊（即時爬取）。

    Args:
        job_id: 職缺 ID，例如 "8d5g5g4"（從搜尋結果的 link 可取得）
    """
    scraper = Job104Scraper(delay=1.0)
    detail = scraper.get_detail(job_id)
    if not detail:
        return {"error": f"無法取得職缺 {job_id} 的詳細資訊"}
    return detail


@mcp.tool()
def search_local_jobs(
    keyword: str,
    source: str = "all",
    limit: int = 50,
    offset: int = 0,
    include_description: bool = False,
) -> dict:
    """
    在本地 JSON 資料中搜尋職缺（不發網路請求）。
    預設不回傳 description 欄位以避免超出 token 上限；需要詳細內容請用 get_job_detail。

    Args:
        keyword:             搜尋關鍵字（職缺名稱、技能或描述）
        source:              "104"、"linkedin" 或 "all"
        limit:               回傳筆數上限（預設 50，0 = 不限）
        offset:              分頁起始位置（預設 0）
        include_description: 是否包含 description 欄位（預設 False）
    """
    EXCLUDE_FIELDS = {"description"}

    jobs_104, jobs_linkedin = load_jobs(DATA_DIR)

    matched = []
    kw = keyword.lower()

    if source in ("104", "all"):
        for job in jobs_104:
            name = job.get("job_name", "").lower()
            skills = " ".join(job.get("skills", [])).lower()
            desc = job.get("description", "").lower()
            if kw in name or kw in skills or kw in desc:
                matched.append({**job, "_source": "104"})

    if source in ("linkedin", "all"):
        for job in jobs_linkedin:
            name = job.get("job_name", "").lower()
            desc = job.get("description", "").lower()
            if kw in name or kw in desc:
                matched.append({**job, "_source": "linkedin"})

    total = len(matched)
    page = matched[offset: offset + limit] if limit > 0 else matched[offset:]

    if not include_description:
        page = [{k: v for k, v in job.items() if k not in EXCLUDE_FIELDS} for job in page]

    by_source: dict[str, int] = {}
    for job in matched:
        s = job.get("_source", "unknown")
        by_source[s] = by_source.get(s, 0) + 1

    return {
        "total": total,
        "by_source": by_source,
        "offset": offset,
        "limit": limit,
        "count": len(page),
        "results": page,
    }


@mcp.tool()
def generate_cover_letter_for_job(
    job_id: str | None = None,
    keyword: str | None = None,
    pick: int = 1,
    job_name: str | None = None,
    company: str | None = None,
    description: str | None = None,
    language: str | None = None,
    paragraphs: int | None = None,
    model: str | None = None,
    fetch_detail: bool = False,
) -> str:
    """
    針對指定職缺產生客製化的求職信（Cover Letter）。

    三種指定職缺的方式（擇一）：
    1. job_id:   104 職缺 ID，從本地資料或即時 API 取得
    2. keyword:  搜尋關鍵字，搭配 pick 選第 N 筆
    3. job_name + company + description: 手動提供職缺資訊

    Args:
        job_id:       104 職缺 ID（例如 "8d5g5g4"）
        keyword:      搜尋關鍵字
        pick:         搭配 keyword，選第幾筆（預設 1）
        job_name:     職缺名稱（手動輸入）
        company:      公司名稱（手動輸入）
        description:  職缺描述（手動輸入）
        language:     輸出語言 "zh-TW" 或 "en"（預設讀 profile.toml）
        paragraphs:   段落數（預設讀 profile.toml）
        model:        指定 LLM 模型
        fetch_detail: 是否從 104 即時取得完整描述
    """
    job = None

    if job_name and company:
        job = {
            "job_name": job_name,
            "company": company,
            "description": description or "",
        }

    elif job_id:
        # 從本地找
        jobs_104, _ = load_jobs(DATA_DIR)
        for j in jobs_104:
            if j.get("job_id") == job_id or j.get("link", "").endswith(job_id):
                job = {**j, "_source": "104"}
                break

        if not job:
            # 即時取得
            scraper = Job104Scraper(delay=1.0)
            detail = scraper.get_detail(job_id)
            if detail:
                job = {
                    "job_name": detail.get("header", {}).get("jobName", ""),
                    "company": detail.get("header", {}).get("custName", ""),
                    "description": detail.get("condition", {}).get("other", ""),
                    "_source": "104",
                }

    elif keyword:
        jobs_104, jobs_linkedin = load_jobs(DATA_DIR)
        matched = []
        kw = keyword.lower()
        for j in jobs_104:
            text = (j.get("job_name", "") + " " + j.get("company", "")).lower()
            if kw in text:
                matched.append({**j, "_source": "104"})
        for j in jobs_linkedin:
            text = (j.get("job_name", "") + " " + j.get("company", "")).lower()
            if kw in text:
                matched.append({**j, "_source": "linkedin"})

        if not matched:
            return f"❌ 找不到包含「{keyword}」的職缺"
        if pick > len(matched):
            return f"❌ 只有 {len(matched)} 筆結果，無法選第 {pick} 筆"
        job = matched[pick - 1]

    if not job:
        return "❌ 請指定職缺（job_id / keyword / job_name+company）"

    # 取得完整描述
    if fetch_detail and job.get("_source") == "104":
        jid = job.get("job_id", "")
        if not jid:
            link = job.get("link", "")
            jid = link.rstrip("/").split("/")[-1] if link else ""
        if jid:
            detail = Job104Scraper(delay=1.0).get_detail(jid)
            if detail:
                full_desc = detail.get("condition", {}).get("other", "")
                if full_desc:
                    job["description"] = full_desc

    result = generate_cover_letter(
        job,
        provider=DEFAULT_PROVIDER,
        model=model,
        language=language,
        paragraphs=paragraphs,
    )

    # 存檔
    if not result.startswith("❌"):
        path = save_cover_letter(result, job)
        result += f"\n\n---\n💾 已儲存: {path}"

    return result


if __name__ == "__main__":
    mcp.run()
