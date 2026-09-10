# LLM Schema-Based Career Page Extraction

> 日期：2026-09-10
> 狀態：規劃中

## 問題

台灣上市櫃公司的招募系統高度碎片化（自建為主），無法像外商用 ats-scrapers 的統一 adapter 爬取。傳統做法是為每家公司寫一個 CSS selector parser，但：

- 1,800+ 家公司，逐家寫不可行
- 網站改版就壞掉，維護成本高
- 每家結構都不一樣（Java/PHP/靜態頁面/SPA 都有）

## 方案

用 LLM 做通用的 career page parser — 不管 HTML 結構是什麼，LLM 都能理解語意並萃取結構化資料。

```
傳統：HTML → 寫死的 CSS selector → 資料（每家一個 parser）
LLM： HTML → LLM + schema prompt → 結構化 JSON（一套吃遍）
```

## 架構

```
                    ┌─────────────┐
Career Page URL ──→ │  Playwright  │──→ HTML
                    └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
              HTML ─│  LLM API    │──→ JSON
              +     │ (schema     │    [{ title, location,
              Schema│  prompt)    │     department, url }]
                    └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │  儲存 / 去重  │──→ D1 / jobs.json
                    └─────────────┘
```

### Step 1: 抓 HTML

用 Playwright 開招募頁面，等 JS 渲染完後取 HTML：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    page = p.chromium.launch().new_page()
    page.goto("https://yourcareers.mediatek.com/search")
    page.wait_for_load_state("networkidle")
    html = page.content()
```

有些頁面不需要 Playwright（純 server-render），可以用 requests 直接抓。

### Step 2: LLM 萃取

```python
prompt = f"""以下是一個公司招募頁面的 HTML。
請萃取所有職缺，回傳 JSON array。

每筆職缺包含：
- title: 職缺標題（string）
- location: 工作地點（string）
- department: 部門（string，如果有的話）
- url: 申請連結（完整 URL，string）
- job_type: 工作類型（全職/兼職/實習/約聘，string）

如果某個欄位找不到，設為 null。
只回傳 JSON array，不要其他文字。

HTML：
{html[:30000]}
"""

response = client.chat.completions.create(
    model="google/gemini-2.5-flash",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4096,
    temperature=0,
)
```

### Step 3: 去重 + 儲存

- 用 title + company + location 做去重（跟 104/LinkedIn 的職缺比對）
- 存入 `jobs.json` 和 D1

## 目標公司

### 第一批：有結構化 ATS 的（ats-scrapers 可處理）

| 公司 | ATS | 做法 | 預估職缺 |
|------|-----|------|---------|
| 台積電 | SuccessFactors | `ats-scrapers` adapter | 200+ |
| 在台外商（Google/NVIDIA/ASML 等） | Greenhouse/Lever/Workday | `ats-scrapers` adapter | 500+ |

### 第二批：自建系統的 TOP 20（LLM extraction）

| 公司 | 招募頁 | 預估職缺 |
|------|-------|---------|
| 聯發科 | yourcareers.mediatek.com | 476 |
| 鴻海 | recruit.foxconn.com | 1,386 |
| 國泰金 | recruit.cathayholdings.com | 數百 |
| 富邦金 | fubon.com/financialholdings/hr/ | 數十 |
| 中信金 | ctbcholding.com/Careers | 數十 |
| 台達電 | deltaww.com 子頁 | 990 |
| 華碩 | 104 + 官網 | 608 |
| 廣達 | hr.quantatw.com | 274 |
| 日月光 | ase.aseglobal.com/careers | 數十 |

### 第三批：ARES 資通 ATS 的（結構統一）

華碩、世界先進、欣興、寶成、建興、采鈺 — 這些用同一套 ARES ATS，寫一個 parser 就能覆蓋全部。

## 成本估算

| 項目 | 數量 | 單價 | 總計 |
|------|------|------|------|
| Playwright 抓 HTML | 100 頁 | 免費（本地跑） | $0 |
| LLM 萃取（Gemini Flash） | 100 頁 × ~5K tokens | $0.15/1M tokens | ~$0.08 |
| 每週更新 | 100 頁 | | ~$0.08/週 |

**月成本 < $1**，幾乎免費。

## LLM 選型

| 模型 | 優勢 | 成本 |
|------|------|------|
| **google/gemini-2.5-flash**（推薦） | 快、便宜、大 context（100 萬 tokens）、HTML 理解好 | $0.15/1M |
| deepseek-v4-flash | 便宜、中文好 | $0.14/1M |
| claude-sonnet-5 | 品質最好但貴 | $2/1M |

建議用 Gemini Flash — context window 夠大可以吃整頁 HTML，而且便宜到可以當免費用。

## 風險和應對

| 風險 | 嚴重度 | 應對 |
|------|--------|------|
| LLM 萃取不準確 | 中 | 抽樣人工驗證前 20 家，調整 prompt |
| 分頁處理 | 中 | 有些招募頁有分頁或 infinite scroll，需要 Playwright 滾動 |
| 反爬 | 低 | Career page 是公開頁面，少有反爬（跟 104 不同） |
| HTML 太大 | 低 | 先做 DOM 精簡（去掉 script/style/nav），只留 main content |
| 重複計算 | 低 | 同一職缺可能在官網 + 104 + LinkedIn 都出現，用 title+company 去重 |

## 跟現有管線的整合

```
現有管線：
├── TWSE/TPEx API → 公司基本資料
├── MOPS → 薪資
├── 104 Playwright → 職缺列表
├── JobSpy → LinkedIn/Indeed 職缺

新增：
├── ats-scrapers → 外商 ATS 職缺（Greenhouse/Lever/Workday/SuccessFactors）
├── LLM extraction → 台灣自建系統職缺（聯發科/鴻海/金控等）

全部匯入 → jobs.json → D1 → 前端
```

## 實作計畫

### Phase 1：驗證（1-2 天）

1. 台積電 — 用 ats-scrapers 的 SuccessFactors adapter 抓
2. 聯發科 — 用 Playwright + LLM extraction 抓
3. 比對結果品質，調整 prompt

### Phase 2：擴展 TOP 20（2-3 天）

1. 為 TOP 20 公司各跑一次 LLM extraction
2. 人工抽驗 5 家
3. 合併到 jobs.json + 部署

### Phase 3：自動化（之後）

1. Cloudflare Workers Cron Trigger 定期跑
2. 每週更新一次
3. 新增公司只需要加 URL，不需要寫 parser

## 相關文件

- `docs/data-sources/teardown-mops.md` — MOPS API 結構
- `docs/data-sources/data-pipeline-guide.md` — 資料管線操作指南
- `docs/data-sources/ats-platforms.md` — ATS 平台深度研究
- `docs/competitors/teardown-jobfrog.md` — Job Frog 的 ATS 爬蟲做法
- `docs/competitors/teardown-jobseek-oss.md` — JobSeek 的 Monitor/Scraper 架構
