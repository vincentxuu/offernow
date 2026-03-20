# fetch-data/test_filter.py
"""
filter.py 的單元測試。
只測純函數（不測 subprocess / IO）。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── clean_html ──────────────────────────────────────────────
def test_clean_html_strips_tags():
    from filter import clean_html
    assert clean_html("<p>Hello <b>World</b></p>") == "Hello World"

def test_clean_html_strips_nbsp():
    from filter import clean_html
    assert "  " not in clean_html("A&nbsp;B")

def test_clean_html_passthrough():
    from filter import clean_html
    assert clean_html("plain text") == "plain text"


# ── format_salary ────────────────────────────────────────────
def test_format_salary_range():
    from filter import format_salary
    job = {"salary": "面議", "salary_low": 60000, "salary_high": 90000}
    assert format_salary(job) == "60,000–90,000"

def test_format_salary_string_fallback():
    from filter import format_salary
    job = {"salary": "面議", "salary_low": 0, "salary_high": 0}
    assert format_salary(job) == "面議"

def test_format_salary_empty():
    from filter import format_salary
    job = {"salary": "", "salary_low": 0, "salary_high": 0}
    assert format_salary(job) == "（無資料）"


# ── format_date ──────────────────────────────────────────────
def test_format_date_104():
    from filter import format_date
    job = {"appeared_date": "20260316"}
    assert format_date(job, "104") == "2026-03-16"

def test_format_date_linkedin():
    from filter import format_date
    job = {"posted_date": "2026-03-10"}
    assert format_date(job, "linkedin") == "2026-03-10"

def test_format_date_missing():
    from filter import format_date
    assert format_date({}, "104") == "（未知）"


# ── fallback_score ───────────────────────────────────────────
def test_fallback_score_negative():
    from filter import fallback_score
    assert fallback_score(-1) == 4
    assert fallback_score(0) == 4

def test_fallback_score_mapping():
    from filter import fallback_score
    assert fallback_score(1) == 5
    assert fallback_score(2) == 6
    assert fallback_score(3) == 7
    assert fallback_score(10) == 7


# ── pre_filter: 排除邏輯 ──────────────────────────────────────
def test_prefilter_excludes_php_only_104():
    from filter import pre_filter_job
    job = {
        "job_name": "PHP 工程師",
        "skills": ["PHP"],
        "description": "開發 PHP 系統",
        "remote_work": 0,
    }
    result = pre_filter_job(job, "104")
    assert result is None  # 排除

def test_prefilter_excludes_csharp_only_104():
    from filter import pre_filter_job
    job = {
        "job_name": "C# 工程師",
        "skills": ["C#", ".NET"],
        "description": "開發 .NET 系統",
        "remote_work": 0,
    }
    result = pre_filter_job(job, "104")
    assert result is None

def test_prefilter_keeps_php_with_python_104():
    from filter import pre_filter_job
    job = {
        "job_name": "後端工程師",
        "skills": ["PHP", "Python"],
        "description": "需要 Python 和 PHP",
        "remote_work": 0,
    }
    result = pre_filter_job(job, "104")
    assert result is not None
    score = result[1]
    assert score <= 0  # PHP 扣分

def test_prefilter_keeps_backend_title_104():
    from filter import pre_filter_job
    job = {
        "job_name": "後端工程師",
        "skills": ["Node.js"],
        "description": "開發 API",
        "remote_work": 0,
    }
    result = pre_filter_job(job, "104")
    assert result is not None

def test_prefilter_ai_bonus_104():
    from filter import pre_filter_job
    job = {
        "job_name": "後端工程師",
        "skills": ["Python", "LLM"],
        "description": "RAG 系統開發",
        "remote_work": 1,
    }
    result = pre_filter_job(job, "104")
    assert result is not None
    score = result[1]
    assert score >= 4  # AI +2, Python +1, remote +1 = 4

def test_prefilter_excludes_php_only_linkedin():
    from filter import pre_filter_job
    job = {
        "job_name": "PHP Developer",
        "description": "Build PHP applications using Laravel framework",
        "location": "Taipei",
        "posted_date": "2026-03-10",
    }
    result = pre_filter_job(job, "linkedin")
    assert result is None

def test_prefilter_keeps_backend_linkedin():
    from filter import pre_filter_job
    job = {
        "job_name": "Backend Engineer",
        "description": "Python FastAPI microservices development",
        "location": "Taipei",
        "posted_date": "2026-03-10",
    }
    result = pre_filter_job(job, "linkedin")
    assert result is not None


# ── parse_llm_response ───────────────────────────────────────
def test_parse_llm_response_valid_json():
    from filter import parse_llm_response
    output = '{"score": 8, "reason": "Python 後端，有 LLM 整合"}'
    score, reason = parse_llm_response(output, fallback=5)
    assert score == 8
    assert "Python" in reason

def test_parse_llm_response_with_extra_text():
    from filter import parse_llm_response
    output = 'Here is my evaluation:\n{"score": 7, "reason": "不錯的機會"}\nDone.'
    score, reason = parse_llm_response(output, fallback=5)
    assert score == 7

def test_parse_llm_response_invalid_fallback():
    from filter import parse_llm_response
    score, reason = parse_llm_response("cannot parse this", fallback=5)
    assert score == 5
    assert "失敗" in reason
