"""
職缺技能分析器
==============
讀取 104 和 LinkedIn 爬蟲輸出的 JSON，
產生技能頻率排行與學習優先順序 Markdown 報告。
"""

from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import re
import subprocess

# 技能分類字典
# key: 分類名稱, value: (權重, {關鍵字: 顯示名稱})
SKILL_CATEGORIES: dict[str, tuple[float, dict[str, str]]] = {
    "程式語言": (1.2, {
        "python": "Python",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "typescript": "TypeScript",
        "javascript": "JavaScript",
        "go": "Go",
        "golang": "Go",
        "java": "Java",
        "php": "PHP",
        "rust": "Rust",
        "ruby": "Ruby",
        "c++": "C++",
        "c#": "C#",
        "kotlin": "Kotlin",
        "swift": "Swift",
        "scala": "Scala",
        "r language": "R",
    }),
    "後端框架": (1.1, {
        "express": "Express",
        "nestjs": "NestJS",
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "spring": "Spring",
        "laravel": "Laravel",
        "gin": "Gin",
        "asp.net": "ASP.NET",
        "rails": "Ruby on Rails",
        "fiber": "Fiber",
    }),
    "前端": (1.0, {
        "react": "React",
        "reactjs": "React",
        "vue": "Vue",
        "vuejs": "Vue",
        "next.js": "Next.js",
        "nextjs": "Next.js",
        "angular": "Angular",
        "angularjs": "Angular",
        "svelte": "Svelte",
        "html": "HTML",
        "css": "CSS",
        "sass": "Sass/SCSS",
        "scss": "Sass/SCSS",
        "jquery": "jQuery",
        "redux": "Redux",
        "webpack": "Webpack",
        "vite": "Vite",
        "tailwind": "Tailwind CSS",
    }),
    "資料庫": (1.0, {
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "elasticsearch": "Elasticsearch",
        "sqlite": "SQLite",
        "cassandra": "Cassandra",
        "ms sql": "SQL Server",
        "mssql": "SQL Server",
        "sql server": "SQL Server",
        "oracle": "Oracle DB",
        "dynamodb": "DynamoDB",
        "firebase": "Firebase",
        "supabase": "Supabase",
        "snowflake": "Snowflake",
        "bigquery": "BigQuery",
    }),
    "雲端/基礎設施": (1.3, {
        "aws": "AWS",
        "gcp": "GCP",
        "google cloud": "GCP",
        "azure": "Azure",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "ci/cd": "CI/CD",
        "linux": "Linux",
        "unix": "Unix",
        "terraform": "Terraform",
        "nginx": "Nginx",
        "jenkins": "Jenkins",
        "github actions": "GitHub Actions",
        "gitlab": "GitLab CI",
        "devops": "DevOps",
        "bash": "Bash/Shell",
        "shell": "Bash/Shell",
    }),
    "AI/ML": (1.5, {
        # 框架與工具
        "langchain": "LangChain",
        "langgraph": "LangGraph",
        "openai": "OpenAI",
        "chatgpt": "OpenAI",
        "gpt": "GPT",
        "gemini": "Gemini",
        "claude": "Claude",
        "llama": "LLaMA",
        "mistral": "Mistral",
        "ollama": "Ollama",
        "vllm": "vLLM",
        "huggingface": "HuggingFace",
        # 技術
        "llm": "LLM",
        "rag": "RAG",
        "embedding": "Embedding",
        "fine-tun": "Fine-tuning",
        "fine tuning": "Fine-tuning",
        "prompt engineer": "Prompt Engineering",
        "transformer": "Transformer",
        # ML 方向
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "nlp": "NLP",
        "natural language": "NLP",
        "computer vision": "Computer Vision",
        "opencv": "OpenCV",
        "stable diffusion": "Stable Diffusion",
        "generative ai": "Generative AI",
        "ai agent": "AI Agent",
        # MLOps / 平台
        "mlops": "MLOps",
        "mlflow": "MLflow",
        "vertex ai": "Vertex AI",
        "sagemaker": "SageMaker",
        "azure ml": "Azure ML",
        # 資料科學工具
        "pandas": "Pandas",
        "numpy": "NumPy",
        "scikit": "Scikit-learn",
        "xgboost": "XGBoost",
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow",
        "cuda": "CUDA",
        # 資料工程
        "spark": "Apache Spark",
        "airflow": "Airflow",
        "dbt": "dbt",
    }),
    "工具/方法": (1.0, {
        "git": "Git",
        "github": "GitHub",
        "graphql": "GraphQL",
        "grpc": "gRPC",
        "restful": "RESTful API",
        "rest api": "RESTful API",
        "websocket": "WebSocket",
        "agile": "Agile",
        "scrum": "Scrum",
        "microservices": "Microservices",
        "microservice": "Microservices",
        "message queue": "Message Queue",
        "kafka": "Kafka",
        "rabbitmq": "RabbitMQ",
        "jira": "JIRA",
        "swagger": "Swagger/OpenAPI",
        "openapi": "Swagger/OpenAPI",
        "jwt": "JWT",
        "oauth": "OAuth",
        "oop": "OOP",
        "tdd": "TDD",
        "solid": "SOLID",
        "etl": "ETL",
        "jest": "Jest",
        "pytest": "pytest",
        "ajax": "AJAX",
        "iot": "IoT",
        "pl/sql": "PL/SQL",
        "matlab": "MATLAB",
    }),
    "行動開發": (1.0, {
        "android": "Android",
        "ios": "iOS",
        "flutter": "Flutter",
        "react native": "React Native",
        "swift": "Swift",
        "kotlin": "Kotlin",
    }),
    "資料分析工具": (1.1, {
        "power bi": "Power BI",
        "tableau": "Tableau",
        "google analytics": "Google Analytics",
        "excel": "Excel",
        "looker": "Looker",
    }),
    "設計工具": (0.8, {
        "figma": "Figma",
        "photoshop": "Photoshop",
        "illustrator": "Illustrator",
        "after effects": "After Effects",
        "premiere": "Premiere",
        "sketch": "Sketch",
    }),
}


def load_jobs(data_dir: Path) -> tuple[list[dict], list[dict]]:
    """
    載入最新的 104 和 LinkedIn JSON 檔案。
    先從 data/archive/ 找時間戳版本，fallback 到 data/ 固定檔名。
    """
    archive_dir = data_dir / "archive"

    def latest(pattern: str) -> list[dict]:
        files = sorted(archive_dir.glob(pattern)) if archive_dir.exists() else []
        if not files:
            return []
        path = files[-1]  # 字母排序最後 = 時間最新
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


def extract_skills(jobs: list[dict], source: str) -> Counter:
    """
    從職缺列表中萃取技能出現次數。
    每個職缺對同一技能只計一次。
    """
    counter: Counter = Counter()

    for job in jobs:
        texts: list[str] = []

        if source == "104":
            texts.extend(job.get("skills", []))
            texts.append(job.get("description", ""))
            texts.append(job.get("job_name", ""))
        else:  # linkedin
            texts.append(job.get("description", ""))
            texts.append(job.get("job_name", ""))
            texts.append(job.get("job_function", ""))

        combined = " ".join(str(t) for t in texts).lower()

        matched: set[str] = set()
        for _category, (_weight, keywords) in SKILL_CATEGORIES.items():
            for keyword, display_name in keywords.items():
                pattern = r'(?<![a-z])' + re.escape(keyword) + r'(?![a-z])'
                if re.search(pattern, combined) and display_name not in matched:
                    matched.add(display_name)
                    counter[display_name] += 1

    return counter


def analyze(jobs_104: list[dict], jobs_linkedin: list[dict]) -> dict:
    """
    合併兩個來源的技能計數，計算優先分數。
    """
    total = len(jobs_104) + len(jobs_linkedin)

    freq: Counter = Counter()
    freq.update(extract_skills(jobs_104, "104"))
    freq.update(extract_skills(jobs_linkedin, "linkedin"))

    # 建立 display_name -> 分類權重的查詢表
    weight_map: dict[str, float] = {}
    category_map: dict[str, str] = {}
    for category, (weight, keywords) in SKILL_CATEGORIES.items():
        for _kw, display_name in keywords.items():
            weight_map[display_name] = weight
            category_map[display_name] = category

    priority: dict[str, float] = {}
    for skill, count in freq.items():
        pct = count / total * 100 if total > 0 else 0
        priority[skill] = round(pct * weight_map.get(skill, 1.0), 2)

    categorized: dict[str, list[tuple[str, int]]] = {c: [] for c in SKILL_CATEGORIES}
    for skill, count in freq.items():
        cat = category_map.get(skill, "工具/方法")
        categorized[cat].append((skill, count))

    for cat in categorized:
        categorized[cat].sort(key=lambda x: x[1], reverse=True)

    return {
        "total": total,
        "sources": {"104": len(jobs_104), "linkedin": len(jobs_linkedin)},
        "freq": freq,
        "priority": priority,
        "categorized": categorized,
        "category_map": category_map,
    }


def build_report(result: dict, insights: str = "") -> str:
    """組合 Markdown 報告字串"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = result["total"]
    freq: Counter = result["freq"]
    priority: dict = result["priority"]
    categorized: dict = result["categorized"]
    category_map: dict = result["category_map"]
    sources = result["sources"]

    top3 = [skill for skill, _ in freq.most_common(3)]

    lines: list[str] = []

    lines += [
        "# 職缺技能分析報告",
        "",
        f"**產生時間：** {now}  ",
        f"**分析職缺數：** {total} 筆",
        "",
    ]

    if insights:
        lines += ["", insights, "", "---", ""]

    lines += [
        "## 摘要",
        "",
        f"- **104 人力銀行：** {sources['104']} 筆",
        f"- **LinkedIn：** {sources['linkedin']} 筆",
        f"- **最高頻技能 Top 3：** {', '.join(top3)}",
        "",
    ]

    lines += [
        "## 技能頻率排行 Top 30",
        "",
        "| 排名 | 技能 | 分類 | 出現次數 | 佔比 |",
        "|------|------|------|----------|------|",
    ]
    for rank, (skill, count) in enumerate(freq.most_common(30), 1):
        pct = count / total * 100 if total > 0 else 0
        cat = category_map.get(skill, "-")
        lines.append(f"| {rank} | {skill} | {cat} | {count} | {pct:.1f}% |")
    lines.append("")

    lines += ["## 技能分類", ""]
    for category, items in categorized.items():
        if not items:
            continue
        lines.append(f"### {category}")
        lines.append("")
        lines.append("| 技能 | 出現次數 | 佔比 |")
        lines.append("|------|----------|------|")
        for skill, count in items:
            pct = count / total * 100 if total > 0 else 0
            lines.append(f"| {skill} | {count} | {pct:.1f}% |")
        lines.append("")

    top10 = sorted(priority.items(), key=lambda x: x[1], reverse=True)[:10]

    REASONS = {
        "AI/ML": "AI 需求快速成長，加權 1.5x",
        "雲端/基礎設施": "幾乎所有職缺都要求，加權 1.3x",
        "程式語言": "核心技能，高頻必備，加權 1.2x",
        "後端框架": "與語言搭配，職缺需求明確",
        "資料庫": "後端標配，出現頻率高",
        "前端": "全端職缺需求",
        "工具/方法": "工程實踐通用技能",
    }

    lines += [
        "## 建議學習優先順序 Top 10",
        "",
        "| 優先級 | 技能 | 分類 | 優先分數 | 建議理由 |",
        "|--------|------|------|----------|---------|",
    ]
    for rank, (skill, score) in enumerate(top10, 1):
        cat = category_map.get(skill, "-")
        reason = REASONS.get(cat, "高頻需求")
        lines.append(f"| {rank} | {skill} | {cat} | {score:.1f} | {reason} |")

    lines.append("")
    return "\n".join(lines)


CLI_PROVIDERS = {
    "claude": ["claude", "-p", "{prompt}"],
    "gemini": ["gemini", "-p", "{prompt}"],
    "codex":  ["codex", "exec", "{prompt}"],
}
DEFAULT_PROVIDER = "claude"


def call_llm_cli(prompt: str, provider: str, model: str | None = None) -> str:
    cmd = [c.replace("{prompt}", prompt) for c in CLI_PROVIDERS[provider]]
    if model:
        cmd = cmd[:-1] + ["--model", model, cmd[-1]]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.stdout if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def generate_insights(result: dict, provider: str, model: str | None = None) -> str:
    """
    把量化分析結果餵給 LLM，產生敘述性洞察與學習建議。
    """
    freq = result["freq"]
    priority = result["priority"]
    categorized = result["categorized"]
    category_map = result["category_map"]
    total = result["total"]
    sources = result["sources"]

    top20 = "\n".join(
        f"  {i+1}. {skill}（{count} 次, {count/total*100:.1f}%）— 分類：{category_map.get(skill, '-')}"
        for i, (skill, count) in enumerate(freq.most_common(20))
    )
    top10_priority = "\n".join(
        f"  {i+1}. {skill}（優先分數 {score:.1f}）"
        for i, (skill, score) in enumerate(
            sorted(priority.items(), key=lambda x: x[1], reverse=True)[:10]
        )
    )

    ai_skills = "\n".join(
        f"  - {skill}（{count} 次）"
        for skill, count in categorized.get("AI/ML", [])[:10]
    )

    prompt = f"""你是一位資深職涯顧問，專精台灣科技業後端/AI工程師職缺市場。

以下是從 {total} 筆職缺（104: {sources['104']} 筆，LinkedIn: {sources['linkedin']} 筆）統計出的技能需求數據。

求職者背景：
- 目標職位：後端工程師、全端工程師、AI/ML 相關
- 偏好技術：Python, Node.js, TypeScript, Go
- 不想做：PHP-only 或 C#-only
- 加分項：AI/LLM/RAG 整合、遠端工作

技能出現頻率 Top 20：
{top20}

加權優先順序 Top 10：
{top10_priority}

AI/ML 技能細項：
{ai_skills}

請用繁體中文撰寫一份 **職涯洞察報告**，包含以下段落（用 Markdown 格式）：

## 市場觀察
2–3 段敘述：目前台灣後端/AI 市場的技能需求趨勢，哪些技術正在上升？

## 對你的意義
根據求職者偏好分析：哪些技能是強項、哪些是缺口、哪些值得投資？

## 行動建議
3–5 條具體可執行的學習或求職行動，要有優先順序和理由。

## 需要注意
1–2 條警示：哪些技能看起來很多但跟目標方向不符，不要浪費時間？"""

    output = call_llm_cli(prompt, provider, model)
    if not output.strip():
        return "_⚠️ LLM 洞察產生失敗，請確認 CLI 可用_\n"
    return output.strip()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="職缺技能分析器")
    parser.add_argument("--provider", choices=list(CLI_PROVIDERS), default=DEFAULT_PROVIDER,
                        help=f"LLM CLI provider（預設：{DEFAULT_PROVIDER}）")
    parser.add_argument("--model", default=None,
                        help="指定模型（預設：各 provider 自身預設）")
    parser.add_argument("--skip-llm", action="store_true",
                        help="跳過 LLM 洞察，只產生量化報告")
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    reports_dir = base_dir / "reports"
    reports_archive_dir = reports_dir / "archive"
    reports_dir.mkdir(parents=True, exist_ok=True)
    reports_archive_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("職缺技能分析器")
    print("=" * 50)

    jobs_104, jobs_linkedin = load_jobs(data_dir)

    if not jobs_104 and not jobs_linkedin:
        print("❌ 找不到任何職缺資料，請先執行爬蟲")
        return

    print(f"\n📊 共 {len(jobs_104) + len(jobs_linkedin)} 筆職缺，分析中...")
    result = analyze(jobs_104, jobs_linkedin)

    insights = ""
    if not args.skip_llm:
        print(f"\n🤖 產生 LLM 洞察（provider: {args.provider}{f'/{args.model}' if args.model else ''}）...")
        insights = generate_insights(result, args.provider, args.model)

    report = build_report(result, insights)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = reports_archive_dir / f"skills_report_{ts}.md"
    archive_path.write_text(report, encoding="utf-8")
    (reports_dir / "skills_report.md").write_text(report, encoding="utf-8")
    print(f"\n✅ 報告已儲存：{archive_path}")
    print(f"   分析技能數：{len(result['freq'])} 種")
    top3 = result["freq"].most_common(3)
    print(f"   Top 3：{', '.join(s for s, _ in top3)}")


if __name__ == "__main__":
    main()
