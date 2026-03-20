# Offernow

## fetch-data

職缺爬蟲工具，支援 104 人力銀行與 LinkedIn。

### 環境需求

- [uv](https://docs.astral.sh/uv/) — Python 套件與執行環境管理工具

### 安裝 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

### Pipeline 概覽

```
fetch.py          fetch_linkedin.py
    │                     │
    ▼                     ▼
104_jobs_search.json   linkedin_jobs.json
         │                 │
         └────────┬────────┘
                  │
        ┌─────────┴──────────┬──────────────────┐
        ▼                    ▼                  ▼
    filter.py           analyze.py         mcp_server.py
        │                    │              (Claude 直接呼叫)
        ▼                    ▼
reports/filter_report.md   reports/skills_report.md
```

| 階段 | 腳本 | 說明 |
|------|------|------|
| 爬蟲 | `fetch.py` | 呼叫 104 前端公開 JSON API |
| 爬蟲 | `fetch_linkedin.py` | HTML 解析 LinkedIn 公開職缺 |
| 過濾評分 | `filter.py` | 關鍵字初篩 → LLM 批次評分，輸出排名報告 |
| 技能分析 | `analyze.py` | 統計技能頻率並加權，輸出學習優先順序報告 |
| MCP Server | `mcp_server.py` | 讓 Claude Code 直接呼叫本地職缺資料 |

### 使用方式

有兩種方式操作職缺資料：

#### 方式一：MCP Server（推薦）

讓 Claude Code 直接呼叫，不需要記指令：

```bash
# 1. 先爬職缺（一次性，之後可定期跑）
uv run fetch-data/fetch.py
uv run fetch-data/fetch_linkedin.py

# 2. 在 Claude Code 對話中直接說：
# 「幫我看一下現在有哪些職缺資料」
# 「幫我過濾並評分最新職缺」
# 「找 AI 相關的職缺」
```

**安裝 MCP Server：**

```bash
claude mcp add -s user offernow -- bash -c "uv run mcp_server.py"
```

然後編輯 `~/.claude.json`，把指令改成帶路徑的版本：

```json
{
  "mcpServers": {
    "offernow": {
      "command": "bash",
      "args": ["-c", "cd /path/to/offernow/fetch-data && uv run mcp_server.py"]
    }
  }
}
```

#### 方式二：手動執行 Pipeline

```bash
./fetch-data/run.sh
```

選項：

```bash
MAX_LLM=100 ./fetch-data/run.sh          # LLM 評分上限（預設 50）
SKIP_FETCH=1 ./fetch-data/run.sh         # 跳過爬蟲，直接過濾+分析
```

執行完成後，報告輸出至：
- `fetch-data/reports/filter_report.md` — 職缺評分排名
- `fetch-data/reports/skills_report.md` — 技能頻率分析

---

### fetch.py — 104 人力銀行爬蟲

爬取 104 前端公開 JSON API，支援關鍵字搜尋、地區過濾、薪資統計，輸出 CSV / JSON。

**依賴：** `requests`

**執行：**

```bash
uv run --with requests fetch-data/fetch.py
```

**輸出檔案：**

- `104_jobs_search.csv`
- `104_jobs_search.json`

---

### fetch_linkedin.py — LinkedIn 爬蟲

爬取 LinkedIn 公開職缺頁面，支援多關鍵字搜尋、時間過濾、去重複，輸出 CSV / JSON。

**依賴：** `requests`, `beautifulsoup4`

**執行：**

```bash
uv run --with requests --with beautifulsoup4 fetch-data/fetch_linkedin.py
```

**輸出檔案：**

- `linkedin_jobs.csv`
- `linkedin_jobs.json`

---

### filter.py — 職缺過濾與評分

讀取最新 104 / LinkedIn JSON，兩層處理：關鍵字初篩 → LLM 批次評分，產生帶分數排名的 Markdown 報告。

**依賴：** 純 stdlib + 任一 LLM CLI（`claude` / `gemini` / `codex`）

**執行：**

```bash
uv run filter.py                          # 全部職缺，使用 claude（預設）
uv run filter.py --max-llm 50             # 只評分初篩前 50 名
uv run filter.py --provider gemini        # 使用 Gemini CLI
uv run filter.py --provider codex         # 使用 Codex CLI
uv run filter.py --model claude-haiku-4-5-20251001  # 指定模型
uv run filter.py --batch-size 5           # 每批 5 筆（預設 8）
```

**支援的 LLM CLI：**

| Provider | 安裝 | 指令 | 推薦模型 |
|----------|------|------|---------|
| `claude`（預設）| [Claude Code](https://claude.ai/download) | `claude -p` | `claude-haiku-4-5-20251001` |
| `gemini` | `npm i -g @google/gemini-cli` | `gemini -p` | `gemini-2.0-flash` |
| `codex`  | `npm i -g @openai/codex` | `codex exec` | `gpt-4o-mini` |

**輸出檔案：**

- `reports/filter_report.md`（最新，固定路徑）
- `reports/archive/filter_report_YYYYMMDD_HHMMSS.md`（歷史存檔）

---

### analyze.py — 職缺技能分析

讀取最新 104 / LinkedIn JSON，統計技能出現頻率並依分類加權，並透過 LLM 產生敘述性職涯洞察報告。

**依賴：** 純 stdlib + 任一 LLM CLI（`claude` / `gemini` / `codex`）

**執行：**

```bash
uv run analyze.py                         # 含 LLM 洞察，使用 claude（預設）
uv run analyze.py --model claude-haiku-4-5-20251001
uv run analyze.py --provider gemini
uv run analyze.py --skip-llm              # 只輸出量化數據，不呼叫 LLM
```

**輸出檔案：**

- `reports/skills_report.md`（最新）
- `reports/archive/skills_report_YYYYMMDD_HHMMSS.md`（歷史存檔）

---

### 微調偏好與 Prompt

不需要修改 `.py` 原始碼，只需編輯以下兩個設定：

**`fetch-data/profile.toml`** — 求職偏好與篩選條件

```toml
[user]
preferred_tech = ["Python", "Node.js", "TypeScript", "Go"]
exclude_tech   = ["PHP", "C#"]
bonus_factors  = ["AI", "LLM", "RAG", "遠端"]

[filter]
extra_title_keywords   = []   # 補充職稱關鍵字
extra_exclude_keywords = []   # 補充排除條件
```

**`fetch-data/prompts/`** — LLM prompt 模板

| 檔案 | 用途 |
|------|------|
| `filter_batch.txt` | 職缺評分 prompt |
| `analyze_insights.txt` | 職涯洞察 prompt |

---

### 一次安裝依賴（建立本地環境）

若需要在 `fetch-data/` 目錄下建立可重複使用的虛擬環境：

```bash
cd fetch-data
uv init --no-workspace
uv add requests beautifulsoup4
uv run fetch.py
uv run fetch_linkedin.py
```

---

## 免責聲明

本工具為非官方的個人學習專案，僅供教育研究與個人使用，非商業用途。

- 本工具未獲 104 人力銀行或 LinkedIn 官方授權，使用可能違反各平台服務條款（Terms of Service），請自行評估法律與合規風險。
- 所有分析結果僅供參考，不保證資料的即時性、完整性或準確性。
- 使用者同意自行承擔使用本工具的一切後果，作者及貢獻者不對任何損失或法律問題負責。
