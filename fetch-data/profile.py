"""
讀取 profile.toml 與 prompts/ 模板，供 filter.py 和 analyze.py 使用。
"""

import sys
import tomllib
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROFILE_PATH = BASE_DIR / "profile.toml"
PROMPTS_DIR = BASE_DIR / "prompts"


def load_profile() -> dict:
    """載入 profile.toml，若不存在則回傳空 dict（使用各腳本預設值）。"""
    if not PROFILE_PATH.exists():
        return {}
    with open(PROFILE_PATH, "rb") as f:
        return tomllib.load(f)


def load_prompt_template(name: str) -> str:
    """
    載入 prompts/{name}.txt 模板。
    name: 'filter_batch' 或 'analyze_insights'
    若不存在則回傳空字串（各腳本 fallback 到內建 prompt）。
    """
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def profile_to_prompt_vars(profile: dict) -> dict:
    """把 profile dict 轉成 prompt template 用的變數字典。"""
    user = profile.get("user", {})
    analyze = profile.get("analyze", {})
    return {
        "background":     user.get("background", "").strip(),
        "target_roles":   "、".join(user.get("target_roles", [])),
        "preferred_tech": "、".join(user.get("preferred_tech", [])),
        "exclude_tech":   "、".join(user.get("exclude_tech", [])),
        "bonus_factors":  "、".join(user.get("bonus_factors", [])),
        "salary_note":    user.get("salary_note", "無硬性限制"),
        "focus_note":     analyze.get("focus_note", ""),
    }


def resume_to_prompt_section(profile: dict) -> str:
    """
    把 [resume] 區塊組成可嵌入 prompt 的文字段落。
    只包含有填寫的欄位，空欄位自動跳過。
    """
    resume = profile.get("resume", {})
    if not resume:
        return ""

    sections = []

    name = resume.get("name", "").strip()
    headline = resume.get("headline", "").strip()
    if name or headline:
        line = ""
        if name:
            line += f"姓名：{name}"
        if headline:
            line += f"\n定位：{headline}" if name else f"定位：{headline}"
        sections.append(line)

    yoe = resume.get("years_of_experience", "").strip()
    if yoe:
        sections.append(f"年資：{yoe}")

    field_labels = [
        ("education", "學歷"),
        ("work_experience", "工作經歷"),
        ("projects", "專案經歷"),
        ("skills_detail", "技術能力"),
        ("certifications", "證照"),
        ("soft_skills", "個人特質"),
    ]

    for key, label in field_labels:
        val = resume.get(key, "").strip()
        if val:
            sections.append(f"{label}：\n{val}")

    if not sections:
        return ""

    return "求職者履歷：\n" + "\n\n".join(sections)


if __name__ == "__main__":
    # 快速驗證：python profile.py
    p = load_profile()
    if not p:
        print("⚠️  profile.toml 不存在")
        sys.exit(1)
    vars_ = profile_to_prompt_vars(p)
    print("✅ profile.toml 載入成功")
    for k, v in vars_.items():
        print(f"  {k}: {v[:60]}{'...' if len(v) > 60 else ''}")
