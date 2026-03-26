"""
求職信產生器
============
根據職缺資訊與個人背景，用 LLM 產生客製化的 Cover Letter。

執行：
    uv run cover_letter.py --url https://www.104.com.tw/job/8d5g5g4
    uv run cover_letter.py --keyword "後端工程師" --pick 1
    uv run cover_letter.py --job-name "Backend Engineer" --company "Foo Inc" --description "..."
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from profile import load_profile, load_prompt_template, profile_to_prompt_vars, resume_to_prompt_section
from filter import call_llm_cli, clean_html, load_jobs, DEFAULT_PROVIDER, CLI_PROVIDERS

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

LANGUAGE_MAP = {
    "zh-TW": "繁體中文（台灣慣用語法）",
    "en": "English",
}


# ── URL 解析 ──────────────────────────────────────────────────

def parse_job_url(url: str) -> dict | None:
    """
    從 104 或 LinkedIn 職缺 URL 解析出來源與 ID。

    支援格式：
      https://www.104.com.tw/job/8d5g5g4
      https://www.104.com.tw/job/8d5g5g4?jobsource=...
      https://www.linkedin.com/jobs/view/1234567890
      https://www.linkedin.com/jobs/view/some-title-1234567890

    回傳 {"source": "104"|"linkedin", "job_id": "..."}，無法解析回傳 None。
    """
    # 104
    m = re.search(r'104\.com\.tw/job/([A-Za-z0-9]+)', url)
    if m:
        return {"source": "104", "job_id": m.group(1)}

    # LinkedIn
    m = re.search(r'linkedin\.com/jobs/view/(?:.*?[-/])?(\d+)', url)
    if m:
        return {"source": "linkedin", "job_id": m.group(1)}

    return None


def resolve_job_from_url(url: str) -> dict | None:
    """
    從 URL 解析職缺，先查本地資料，找不到就即時從 104 API 取得。
    LinkedIn 職缺因無公開 API，僅能從本地資料比對。
    """
    parsed = parse_job_url(url)
    if not parsed:
        return None

    source = parsed["source"]
    job_id = parsed["job_id"]

    # 先查本地
    jobs_104, jobs_linkedin = load_jobs(DATA_DIR)

    if source == "104":
        for job in jobs_104:
            if job.get("job_id") == job_id or job.get("link", "").endswith(job_id):
                return {**job, "_source": "104"}
        # 本地沒有，即時取得
        print(f"  本地找不到，從 104 即時取得 {job_id}...")
        detail = fetch_104_detail(job_id)
        if detail:
            return {
                "job_name": detail.get("header", {}).get("jobName", ""),
                "company": detail.get("header", {}).get("custName", ""),
                "description": detail.get("condition", {}).get("other", ""),
                "job_id": job_id,
                "_source": "104",
            }

    elif source == "linkedin":
        for job in jobs_linkedin:
            # LinkedIn job_id 可能在 link 欄位中
            link = job.get("link", "")
            if job_id in link:
                return {**job, "_source": "linkedin"}
        print(f"  LinkedIn 職缺 {job_id} 不在本地資料中（LinkedIn 無公開 API 可即時取得）")

    return None


# ── 職缺查找 ─────────────────────────────────────────────────

def find_job_by_id(job_id: str) -> dict | None:
    """從本地 JSON 找 104 職缺（by job_id）。"""
    jobs_104, _ = load_jobs(DATA_DIR)
    for job in jobs_104:
        if job.get("job_id") == job_id or job.get("link", "").endswith(job_id):
            return {**job, "_source": "104"}
    return None


def find_jobs_by_keyword(keyword: str) -> list[dict]:
    """從本地 JSON 搜尋包含關鍵字的職缺。"""
    jobs_104, jobs_linkedin = load_jobs(DATA_DIR)
    matched = []
    kw = keyword.lower()

    for job in jobs_104:
        text = (job.get("job_name", "") + " " + job.get("company", "")).lower()
        if kw in text:
            matched.append({**job, "_source": "104"})

    for job in jobs_linkedin:
        text = (job.get("job_name", "") + " " + job.get("company", "")).lower()
        if kw in text:
            matched.append({**job, "_source": "linkedin"})

    return matched


def fetch_104_detail(job_id: str) -> dict | None:
    """即時從 104 API 取得職缺完整描述。"""
    from fetch import Job104Scraper
    scraper = Job104Scraper(delay=1.0)
    return scraper.get_detail(job_id)


# ── Cover Letter 產生 ─────────────────────────────────────────

def build_cover_letter_prompt(
    job: dict,
    profile: dict,
    language: str = "zh-TW",
    paragraphs: int = 3,
) -> str:
    """組合 Cover Letter 的 LLM prompt。"""
    template = load_prompt_template("cover_letter")
    vars_ = profile_to_prompt_vars(profile)

    # 職缺資訊
    job_name = job.get("job_name", "")
    company = job.get("company", "")
    description = clean_html(job.get("description", ""))

    # 履歷資料
    resume_section = resume_to_prompt_section(profile)

    # cover_letter 設定
    cl_config = profile.get("cover_letter", {})
    experience = cl_config.get("experience", "").strip()

    # 組合 experience_section：優先用 [resume]，補充 [cover_letter].experience
    parts = []
    if resume_section:
        parts.append(resume_section)
    if experience:
        parts.append(f"額外補充：\n{experience}")
    experience_section = "\n\n".join(parts)

    lang_display = LANGUAGE_MAP.get(language, language)
    length = str(paragraphs)

    if template:
        return template.format(
            job_name=job_name,
            company=company,
            job_description=description,
            language=lang_display,
            length=length,
            experience_section=experience_section,
            **vars_,
        )

    # 內建 fallback prompt
    return f"""你是一位專業的求職顧問，擅長撰寫有說服力且客製化的求職信。

求職者背景：
{vars_.get('background', '')}

核心技術：{vars_.get('preferred_tech', '')}
目標職位：{vars_.get('target_roles', '')}

{experience_section}

請針對以下職缺撰寫一封求職信：

職缺名稱：{job_name}
公司名稱：{company}
職缺描述：
{description}

要求：
- 語言：{lang_display}
- 長度：{length} 段落
- 專業但有個人特色
- 不要編造不存在的經歷

請直接輸出求職信內容（Markdown 格式），不要加額外說明。"""


def generate_cover_letter(
    job: dict,
    provider: str = DEFAULT_PROVIDER,
    model: str | None = None,
    language: str | None = None,
    paragraphs: int | None = None,
) -> str:
    """
    產生 Cover Letter。

    Args:
        job:        職缺 dict（需包含 job_name, company, description）
        provider:   LLM provider
        model:      指定模型
        language:   輸出語言（覆寫 profile.toml 設定）
        paragraphs: 段落數（覆寫 profile.toml 設定）

    Returns:
        Cover Letter 文字（Markdown）
    """
    profile = load_profile()
    cl_config = profile.get("cover_letter", {})

    lang = language or cl_config.get("language", "zh-TW")
    paras = paragraphs or cl_config.get("paragraphs", 3)

    prompt = build_cover_letter_prompt(job, profile, language=lang, paragraphs=paras)
    output = call_llm_cli(prompt, provider, model=model)

    if not output.strip():
        return "❌ LLM 未回傳內容，請確認 CLI provider 是否可用"

    return output.strip()


def save_cover_letter(content: str, job: dict) -> Path:
    """存檔到 reports/cover_letters/。"""
    out_dir = REPORTS_DIR / "cover_letters"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    company = re.sub(r'[^\w\-]', '_', job.get("company", "unknown"))[:30]
    filename = f"cover_letter_{company}_{ts}.md"
    path = out_dir / filename

    # 加上元資料 header
    header = (
        f"<!-- job: {job.get('job_name', '')} -->\n"
        f"<!-- company: {job.get('company', '')} -->\n"
        f"<!-- generated: {datetime.now().isoformat()} -->\n\n"
    )
    path.write_text(header + content, encoding="utf-8")
    return path


# ── CLI ───────────────────────────────────────────────────────

def print_job_list(jobs: list[dict]):
    """列出搜尋結果供使用者選擇。"""
    for i, job in enumerate(jobs, 1):
        source = job.get("_source", "?")
        name = job.get("job_name", "（無職稱）")
        company = job.get("company", "（無公司名）")
        print(f"  [{i}] [{source}] {name} — {company}")


def main():
    parser = argparse.ArgumentParser(description="產生客製化求職信")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--url", help="104 或 LinkedIn 職缺 URL（最簡單的方式）")
    group.add_argument("--job-id", help="104 職缺 ID（直接指定）")
    group.add_argument("--keyword", help="搜尋關鍵字（從本地資料找職缺）")

    # 手動指定職缺資訊（不需本地資料）
    parser.add_argument("--job-name", help="職缺名稱（手動輸入）")
    parser.add_argument("--company", help="公司名稱（手動輸入）")
    parser.add_argument("--description", help="職缺描述（手動輸入）")

    parser.add_argument("--pick", type=int, default=0, help="搭配 --keyword，直接選第 N 筆")
    parser.add_argument("--language", choices=["zh-TW", "en"], help="輸出語言")
    parser.add_argument("--paragraphs", type=int, help="段落數")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, choices=list(CLI_PROVIDERS))
    parser.add_argument("--model", help="指定 LLM 模型")
    parser.add_argument("--fetch-detail", action="store_true", help="從 104 即時取得完整職缺描述")
    parser.add_argument("--no-save", action="store_true", help="不存檔，只輸出到 stdout")

    args = parser.parse_args()

    # ── 決定目標職缺 ──────────────────────────────────────────
    job = None

    if args.url:
        print(f"🔗 解析 URL: {args.url}")
        job = resolve_job_from_url(args.url)
        if not job:
            parsed = parse_job_url(args.url)
            if not parsed:
                print("❌ 無法解析此 URL，支援 104.com.tw 和 linkedin.com 職缺連結")
            else:
                print(f"❌ 無法取得職缺資訊（{parsed['source']} ID: {parsed['job_id']}）")
            sys.exit(1)

    elif args.job_name and args.company:
        # 手動輸入模式
        job = {
            "job_name": args.job_name,
            "company": args.company,
            "description": args.description or "",
        }

    elif args.job_id:
        print(f"🔍 搜尋職缺 ID: {args.job_id}")
        job = find_job_by_id(args.job_id)
        if not job:
            print("  本地找不到，嘗試從 104 即時取得...")
            detail = fetch_104_detail(args.job_id)
            if detail:
                job = {
                    "job_name": detail.get("header", {}).get("jobName", ""),
                    "company": detail.get("header", {}).get("custName", ""),
                    "description": detail.get("condition", {}).get("other", ""),
                    "_source": "104",
                }

    elif args.keyword:
        print(f"🔍 搜尋關鍵字: {args.keyword}")
        matched = find_jobs_by_keyword(args.keyword)
        if not matched:
            print("❌ 找不到符合的職缺")
            sys.exit(1)

        if args.pick > 0:
            if args.pick > len(matched):
                print(f"❌ 只有 {len(matched)} 筆結果，無法選第 {args.pick} 筆")
                sys.exit(1)
            job = matched[args.pick - 1]
        else:
            print(f"\n找到 {len(matched)} 筆：")
            print_job_list(matched[:20])
            try:
                choice = int(input("\n請輸入編號: "))
                job = matched[choice - 1]
            except (ValueError, IndexError):
                print("❌ 無效選擇")
                sys.exit(1)

    if not job:
        print("❌ 請指定職缺（--url / --keyword / --job-name + --company）")
        parser.print_help()
        sys.exit(1)

    # 若描述太短且是 104 職缺，嘗試取得完整描述
    desc = job.get("description", "")
    if args.fetch_detail and job.get("_source") == "104":
        job_id = job.get("job_id", "")
        if not job_id:
            link = job.get("link", "")
            job_id = link.rstrip("/").split("/")[-1] if link else ""
        if job_id:
            print("📋 取得完整職缺描述...")
            detail = fetch_104_detail(job_id)
            if detail:
                full_desc = detail.get("condition", {}).get("other", "")
                if full_desc:
                    job["description"] = full_desc

    # ── 產生 Cover Letter ─────────────────────────────────────
    print(f"\n✍️  為「{job.get('job_name', '')}」@「{job.get('company', '')}」產生求職信...\n")

    result = generate_cover_letter(
        job,
        provider=args.provider,
        model=args.model,
        language=args.language,
        paragraphs=args.paragraphs,
    )

    print(result)

    if not args.no_save and not result.startswith("❌"):
        path = save_cover_letter(result, job)
        print(f"\n💾 已儲存: {path}")


if __name__ == "__main__":
    main()
