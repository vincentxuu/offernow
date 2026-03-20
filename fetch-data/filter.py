"""
職缺過濾器
==========
讀取最新 104 / LinkedIn JSON，關鍵字初篩後用 claude -p 評分，
產生帶分數排名的 Markdown 報告。

執行：
    uv run filter.py
    uv run filter.py --max-llm 50
"""

import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# ── 關鍵字清單 ─────────────────────────────────────────────────

TITLE_KEYWORDS = [
    r"後端", r"backend", r"全端", r"full.?stack", r"fullstack",
    r"\bAI\b", r"\bML\b", r"\bLLM\b", r"資料工程", r"data engineer",
    r"machine learning", r"軟體工程師", r"software engineer",
]

TECH_KEYWORDS = [
    r"python", r"node\.?js", r"typescript", r"\b(go|golang)\b",
    r"rust", r"fastapi", r"django", r"nestjs", r"express",
    r"langchain", r"openai", r"pytorch", r"tensorflow",
    r"\bllm\b", r"\brag\b", r"embedding",
]

PREFERRED_TECH = [r"python", r"node\.?js", r"typescript", r"\b(go|golang)\b"]

AI_KEYWORDS = [r"\bai\b", r"\bllm\b", r"\brag\b", r"embedding", r"向量", r"生成式"]

EXCLUDE_KEYWORDS = [r"\bphp\b", r"\bc#"]


# ── 工具函數 ──────────────────────────────────────────────────

def clean_html(text: str) -> str:
    """去除 HTML 標籤，正規化空白。"""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def format_salary(job: dict) -> str:
    """格式化薪資顯示（104 專用）。"""
    low = job.get("salary_low", 0) or 0
    high = job.get("salary_high", 0) or 0
    if low and high:
        return f"{low:,}–{high:,}"
    salary = job.get("salary", "").strip()
    return salary if salary else "（無資料）"


def format_date(job: dict, source: str) -> str:
    """格式化發布日期。"""
    if source == "104":
        raw = job.get("appeared_date", "")
        if raw and len(raw) == 8:
            return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    else:
        raw = job.get("posted_date", "")
        if raw:
            return raw
    return "（未知）"


def fallback_score(pre_score: int) -> int:
    """將初篩分數對應到 1–10 的 fallback LLM 分數。"""
    if pre_score <= 0:
        return 4
    if pre_score == 1:
        return 5
    if pre_score == 2:
        return 6
    return 7  # >= 3


def _match_any(patterns: list, text: str) -> bool:
    """檢查 text 是否符合任一 pattern（不分大小寫）。"""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


# ── 第一層：關鍵字初篩 ─────────────────────────────────────────

def pre_filter_job(job: dict, source: str):
    """
    第一層初篩。
    回傳 (job, pre_score) 若通過，None 若排除。
    """
    job_name = job.get("job_name", "")

    # ── 排除判斷 ─────────────────────────────────────────────
    if source == "104":
        skills_list = [s.lower() for s in job.get("skills", [])]
        skills_text = " ".join(skills_list)
        has_exclude = _match_any(EXCLUDE_KEYWORDS, job_name) or \
                      _match_any(EXCLUDE_KEYWORDS, skills_text)
        has_preferred = any(
            re.search(p, s) for p in TECH_KEYWORDS for s in skills_list
        )
    else:  # linkedin
        desc_preview = job.get("description", "")[:500]
        has_exclude = _match_any(EXCLUDE_KEYWORDS, job_name)
        has_preferred = _match_any(TECH_KEYWORDS, desc_preview)

    if has_exclude and not has_preferred:
        return None  # 排除

    # ── 保留判斷 ─────────────────────────────────────────────
    title_match = _match_any(TITLE_KEYWORDS, job_name)

    if source == "104":
        skills_list = [s.lower() for s in job.get("skills", [])]
        tech_match = any(
            re.search(p, s) for p in TECH_KEYWORDS for s in skills_list
        )
    else:
        tech_match = _match_any(TECH_KEYWORDS, job.get("description", "")[:500])

    if not title_match and not tech_match:
        return None  # 不符合任何保留條件

    # ── 計算初篩分數 ──────────────────────────────────────────
    score = 0

    # AI/LLM/RAG 相關 +2
    ai_text = job_name + " " + job.get("description", "")[:200]
    if source == "104":
        ai_text += " " + " ".join(job.get("skills", []))
    if _match_any(AI_KEYWORDS, ai_text):
        score += 2

    # 偏好技術 +1
    if source == "104":
        pref_text = " ".join(job.get("skills", [])) + " " + job_name
    else:
        pref_text = job.get("description", "")[:200] + " " + job_name
    if _match_any(PREFERRED_TECH, pref_text):
        score += 1

    # 遠端 +1（104 only）
    if source == "104" and job.get("remote_work") == 1:
        score += 1

    # PHP / C# 但有偏好技術（未被排除）→ -1
    if has_exclude and has_preferred:
        score -= 1

    return (job, score)


def pre_filter(jobs_104: list, jobs_linkedin: list) -> list:
    """
    對兩個來源執行初篩。
    回傳 [(job, source, pre_score), ...]，按 pre_score 降序。
    """
    results = []

    for job in jobs_104:
        r = pre_filter_job(job, "104")
        if r:
            results.append((r[0], "104", r[1]))

    for job in jobs_linkedin:
        r = pre_filter_job(job, "linkedin")
        if r:
            results.append((r[0], "linkedin", r[1]))

    results.sort(key=lambda x: x[2], reverse=True)
    return results


# ── CLI Provider 設定 ─────────────────────────────────────────

# 每個 provider 的 subprocess 指令樣板（{prompt} 會被替換）
CLI_PROVIDERS = {
    "claude": ["claude", "-p", "{prompt}"],
    "gemini": ["gemini", "-p", "{prompt}"],
    "codex":  ["codex", "exec", "{prompt}"],
}

DEFAULT_PROVIDER = "claude"


def call_llm_cli(prompt: str, provider: str, model: str | None = None) -> str:
    """
    呼叫指定 CLI provider，回傳 stdout 文字。
    失敗或找不到 CLI 時回傳空字串。
    """
    if provider not in CLI_PROVIDERS:
        raise ValueError(f"不支援的 provider: {provider}，可用：{list(CLI_PROVIDERS)}")

    cmd = [c.replace("{prompt}", prompt) for c in CLI_PROVIDERS[provider]]
    if model:
        # 在 prompt 參數前插入 --model <model>
        cmd = cmd[:-1] + ["--model", model, cmd[-1]]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )
        return result.stdout if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


# ── 第二層：LLM 批次評分 ─────────────────────────────────────

def parse_llm_response(output: str, fallback: int):
    """
    從單筆 claude -p 輸出中解析 score 和 reason（保留供測試用）。
    """
    json_match = re.search(
        r'\{[^{}]*"score"\s*:\s*(\d+)[^{}]*"reason"\s*:\s*"([^"]+)"[^{}]*\}',
        output
    )
    if json_match:
        return max(1, min(10, int(json_match.group(1)))), json_match.group(2)

    json_match2 = re.search(
        r'\{[^{}]*"reason"\s*:\s*"([^"]+)"[^{}]*"score"\s*:\s*(\d+)[^{}]*\}',
        output
    )
    if json_match2:
        return max(1, min(10, int(json_match2.group(2)))), json_match2.group(1)

    return fallback, "⚠️ 評分失敗，使用初篩分數"


def _build_job_block(idx: int, job: dict, source: str) -> str:
    """組合單筆職缺的 prompt 區塊。"""
    job_name = job.get("job_name", "")
    company = job.get("company", "")
    desc = clean_html(job.get("description", ""))[:300]
    skills_str = ", ".join(job.get("skills", [])) if source == "104" else "（無）"
    return (
        f"[{idx}] 職稱：{job_name}\n"
        f"    公司：{company}\n"
        f"    技術：{skills_str}\n"
        f"    描述：{desc}"
    )


def score_batch_with_llm(batch: list, fallbacks: list, provider: str = DEFAULT_PROVIDER, model: str | None = None) -> list:
    """
    一次呼叫 LLM CLI 評分多筆職缺。
    batch: [(job, source), ...]
    fallbacks: [int, ...]
    回傳 [(score, reason), ...]，長度與 batch 相同。
    """
    n = len(batch)
    blocks = "\n\n".join(
        _build_job_block(i + 1, job, source)
        for i, (job, source) in enumerate(batch)
    )

    prompt = f"""你是一個求職顧問，幫我評估以下 {n} 筆職缺是否適合我。

我的背景與偏好：
- 目標：後端/全端/AI 相關工程師職位
- 偏好技術：Python, Node.js, TypeScript, Go
- 不想做：PHP-only 或 C#-only 的工作
- 加分：有 AI/LLM/RAG 相關、遠端工作機會

{blocks}

請只回傳 JSON array，不要其他文字，順序對應 [1]~[{n}]：
[
  {{"id": 1, "score": <1-10整數>, "reason": "<一句話中文說明>"}},
  ...
  {{"id": {n}, "score": <1-10整數>, "reason": "<一句話中文說明>"}}
]"""

    output = call_llm_cli(prompt, provider, model=model)

    # 解析 JSON array
    parsed = {}
    if output:
        # 找整個 array
        arr_match = re.search(r'\[[\s\S]*\]', output)
        if arr_match:
            try:
                items = json.loads(arr_match.group())
                for item in items:
                    idx = int(item.get("id", 0))
                    score = max(1, min(10, int(item.get("score", fallbacks[idx - 1]))))
                    reason = item.get("reason", "⚠️ 評分失敗，使用初篩分數")
                    parsed[idx] = (score, reason)
            except (json.JSONDecodeError, ValueError):
                pass

    # 填補解析失敗的項目
    return [
        parsed.get(i + 1, (fallbacks[i], "⚠️ 評分失敗，使用初篩分數"))
        for i in range(n)
    ]


# ── 資料載入 ──────────────────────────────────────────────────

def load_jobs(data_dir: Path):
    """載入最新的 104 和 LinkedIn JSON。先從 archive/ 找時間戳版本，fallback 到固定檔名。"""
    archive_dir = data_dir / "archive"

    def latest(pattern: str) -> list:
        files = sorted(archive_dir.glob(pattern)) if archive_dir.exists() else []
        if not files:
            return []
        path = files[-1]
        print(f"📂 載入: {path.name}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    jobs_104 = latest("104_jobs_search_*.json")
    jobs_linkedin = latest("linkedin_jobs_*.json")

    if not jobs_104 and (data_dir / "104_jobs_search.json").exists():
        with open(data_dir / "104_jobs_search.json", encoding="utf-8") as f:
            jobs_104 = json.load(f)
        print("📂 載入: 104_jobs_search.json")

    if not jobs_linkedin and (data_dir / "linkedin_jobs.json").exists():
        with open(data_dir / "linkedin_jobs.json", encoding="utf-8") as f:
            jobs_linkedin = json.load(f)
        print("📂 載入: linkedin_jobs.json")

    if not jobs_104 and not jobs_linkedin:
        print("⚠️  找不到資料，請先執行爬蟲")

    return jobs_104, jobs_linkedin


# ── 報告產生 ──────────────────────────────────────────────────

def _format_job_entry(job: dict, source: str, score: int, reason: str) -> str:
    """格式化單筆職缺的 Markdown 區塊。"""
    job_name = job.get("job_name", "（無職稱）")
    company = job.get("company", "（無公司名）")
    link = job.get("link", "")

    if source == "104":
        salary = format_salary(job)
        location = job.get("area", "")
        mrt = job.get("mrt", "")
        if mrt:
            location = f"{location}（{mrt}）"
    else:
        salary = "（無資料）"
        location = job.get("location", "")

    date = format_date(job, source)

    lines = [
        f"### {score}/10 — {job_name} @ {company}",
        f"**來源：** {source} | **發布：** {date}",
        f"**理由：** {reason}",
        f"**薪資：** {salary}",
        f"**地點：** {location}",
        f"**連結：** {link}",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def build_report(
    scored: list,
    unscored: list,
    stats: dict,
) -> str:
    """
    組合完整 Markdown 報告。

    scored: [(job, source, score, reason), ...]
    unscored: [(job, source, pre_score), ...]
    stats: {"104_total", "linkedin_total", "104_passed", "linkedin_passed", "llm_count", "elapsed"}
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []

    lines += [
        f"# 職缺過濾報告 {now}",
        "",
        "## 統計摘要",
        "",
        f"- 104 原始：{stats['104_total']} 筆 → 初篩通過：{stats['104_passed']} 筆",
        f"- LinkedIn 原始：{stats['linkedin_total']} 筆 → 初篩通過：{stats['linkedin_passed']} 筆",
        f"- LLM 評分完成：{stats['llm_count']} 筆（{stats['provider']}{stats['model_tag']}，耗時 {stats['elapsed']:.0f}s）",
        f"- 未 LLM 評分（初篩保留）：{len(unscored)} 筆",
        "",
    ]

    top = [(j, s, sc, r) for j, s, sc, r in scored if sc >= 7]
    mid = [(j, s, sc, r) for j, s, sc, r in scored if 4 <= sc <= 6]
    low = [(j, s, sc, r) for j, s, sc, r in scored if sc <= 3]

    lines += [f"## 推薦職缺（評分 7+）　共 {len(top)} 筆", ""]
    if top:
        for job, source, score, reason in sorted(top, key=lambda x: x[2], reverse=True):
            lines.append(_format_job_entry(job, source, score, reason))
    else:
        lines += ["（無）", ""]

    lines += [f"## 還行的職缺（評分 4–6）　共 {len(mid)} 筆", ""]
    if mid:
        for job, source, score, reason in sorted(mid, key=lambda x: x[2], reverse=True):
            lines.append(_format_job_entry(job, source, score, reason))
    else:
        lines += ["（無）", ""]

    lines += [f"## 略過（評分 1–3）　共 {len(low)} 筆", ""]
    for job, source, score, reason in sorted(low, key=lambda x: x[2], reverse=True):
        job_name = job.get("job_name", "")
        company = job.get("company", "")
        lines.append(f"- {score}/10 — {job_name} @ {company} — {reason}")
    lines.append("")

    if unscored:
        lines += [f"## 未 LLM 評分（初篩通過，超出 --max-llm 上限）　共 {len(unscored)} 筆", ""]
        for job, source, pre_score in unscored:
            job_name = job.get("job_name", "")
            company = job.get("company", "")
            link = job.get("link", "")
            lines.append(f"- 初篩分數 {pre_score} — {job_name} @ {company} — {link}")
        lines.append("")

    return "\n".join(lines)


# ── 主程式 ────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="職缺過濾器")
    parser.add_argument("--max-llm", type=int, default=None,
                        help="最多對幾筆職缺做 LLM 評分（預設：全部）")
    parser.add_argument("--batch-size", type=int, default=8,
                        help="每次批次評分的職缺數（預設：8）")
    parser.add_argument("--provider", choices=list(CLI_PROVIDERS), default=DEFAULT_PROVIDER,
                        help=f"LLM CLI provider（預設：{DEFAULT_PROVIDER}）")
    parser.add_argument("--model", default=None,
                        help="指定模型（預設：各 provider 自身預設，e.g. claude-opus-4-6, gemini-2.5-pro, gpt-4o-mini）")
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    reports_dir = base_dir / "reports"
    reports_archive_dir = reports_dir / "archive"
    reports_dir.mkdir(parents=True, exist_ok=True)
    reports_archive_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("職缺過濾器")
    print("=" * 50)

    jobs_104, jobs_linkedin = load_jobs(data_dir)

    if not jobs_104 and not jobs_linkedin:
        print("❌ 找不到任何職缺資料，請先執行爬蟲")
        sys.exit(1)

    print(f"\n🔍 初篩中（104: {len(jobs_104)} 筆, LinkedIn: {len(jobs_linkedin)} 筆）...")
    filtered = pre_filter(jobs_104, jobs_linkedin)

    passed_104 = sum(1 for _, src, _ in filtered if src == "104")
    passed_li = sum(1 for _, src, _ in filtered if src == "linkedin")
    print(f"   初篩通過：{len(filtered)} 筆（104: {passed_104}, LinkedIn: {passed_li}）")

    if args.max_llm is not None and args.max_llm < len(filtered):
        to_score = filtered[:args.max_llm]
        unscored_raw = filtered[args.max_llm:]
    else:
        to_score = filtered
        unscored_raw = []

    unscored = [(j, s, ps) for j, s, ps in unscored_raw]

    batch_size = args.batch_size
    total = len(to_score)
    print(f"\n🤖 LLM 批次評分中（{total} 筆，每批 {batch_size} 筆）...")
    start = time.time()
    scored = []

    for batch_start in range(0, total, batch_size):
        batch_items = to_score[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        end_idx = min(batch_start + batch_size, total)
        print(f"  [批次 {batch_num}/{total_batches}] 評分 {batch_start + 1}–{end_idx} 筆...")

        batch_jobs = [(job, source) for job, source, _ in batch_items]
        fallbacks = [fallback_score(ps) for _, _, ps in batch_items]
        results = score_batch_with_llm(batch_jobs, fallbacks, provider=args.provider, model=args.model)

        for (job, source, _), (score, reason) in zip(batch_items, results):
            scored.append((job, source, score, reason))

        print(f"  ✓ 完成 {end_idx}/{total} 筆")

    elapsed = time.time() - start

    stats = {
        "104_total": len(jobs_104),
        "linkedin_total": len(jobs_linkedin),
        "104_passed": passed_104,
        "linkedin_passed": passed_li,
        "llm_count": len(scored),
        "elapsed": elapsed,
        "provider": args.provider,
        "model_tag": f"/{args.model}" if args.model else "",
    }

    report = build_report(scored, unscored, stats)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = reports_archive_dir / f"filter_report_{ts}.md"
    archive_path.write_text(report, encoding="utf-8")
    (reports_dir / "filter_report.md").write_text(report, encoding="utf-8")

    top_count = sum(1 for _, _, sc, _ in scored if sc >= 7)
    print(f"\n✅ 報告已儲存：{archive_path}")
    print(f"   推薦職缺（7+分）：{top_count} 筆")


if __name__ == "__main__":
    main()
