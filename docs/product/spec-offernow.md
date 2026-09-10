# OfferNow — 看得到公司全貌的職缺平台

> 產出日期：2026-09-10
> 方法：agent-ux-design 五步驟

---

## 1. 使用者意圖

**核心意圖（分層）**：

| 層級 | 意圖 | 一句話 |
|------|------|--------|
| **MVP** | 公司透視 | 「看懂一家公司值不值得去，不只看 JD 的話術」 |
| **第二波** | 時效 + 覆蓋 + 匹配 | 「不漏掉任何值得投的機會，比別人早知道，而且跟我匹配」 |
| **第三波** | 效率 | 「用最少的時間完成從發現到投遞的整個流程」 |

**目標用戶**：台灣求職者，特別是想進上市櫃或外商的中高階人才。

**產品定位**：三層覆蓋

| 層級 | 公司範圍 | 獨家資料 |
|------|---------|---------|
| **核心** | 台灣上市櫃（~2,000 家） | 薪資中位數 × 營收 × EPS × 市值 × 擴編信號 |
| **覆蓋** | 全台灣企業 | 跨平台聚合職缺 + AI 摘要 |
| **外商** | 在台外商（~100 家） | ATS 直爬 + 中文語意搜尋 |

---

## 2. 現況苦工

### 重複勞動
1. **一家一家翻**：104 搜一次、LinkedIn 搜一次、公司官網搜一次，同一個人重複 3 遍
2. **同職缺重複出現**：同一個缺在 104 + LinkedIn + 官網各出現一次，要自己判斷
3. **每家公司查薪資**：去 MOPS 查中位數、去比薪水看評價、去年報看 EPS

### 選擇焦慮
4. **2,000 家不知從哪開始**：「半導體好還是金融好？」「這家值不值得投？」
5. **職缺太多看不完**：台積電 7,000+ 缺、鴻海 11,000+ 缺，哪些跟我有關？

### 空白恐懼
6. **履歷客製化**：每投一家都該針對 JD 調整，但不知道改哪裡
7. **Cover Letter**：從零開始寫，不知道這家公司在意什麼

### 領域門檻
8. **看不懂財報跟招募的關聯**：「營收成長 20% 跟招什麼人有什麼關係？」
9. **外商英文 JD**：讀完還是不確定自己符不符合
10. **不知道市場行情**：「這個 offer 的薪資算好嗎？跟同業比呢？」

---

## 3. Agent 介入設計

### 設計原則

> 所有 agent 都是**隱形的** — 使用者看到的是「公司卡片自動有薪資」「職缺自動有 AI 摘要」，而不是「跟 AI 聊天問薪資」。

### MVP — 公司透視（護城河）

#### 3.1 跨平台合併搜尋（苦工 #1, #2）

**模式 C — 流程中自動**

UI 流程：
1. 使用者輸入關鍵字 + 選地點/產業
2. 按「搜尋」→ 搜尋本地已爬取的資料（秒出，非即時打外部 API）
3. 結果自動去重，每個職缺標記「出現在 104 + LinkedIn」
4. 使用者可展開看各來源原始連結

後端包裝：
- **預先爬取模式**（非即時搜尋）：Cron Triggers 定時爬 104 + LinkedIn → 存 D1 + 同步 Typesense
- 使用者搜的是本地資料，體驗秒出（參考 Job Frog / Jobuzzer 做法，非 Jobbo 的即時模式）
- 去重策略（三層）：
  1. **精確匹配**：同公司統編 + 同職缺標題 → 合併
  2. **公司模糊匹配**：LinkedIn 無統編 → 用公司名稱模糊匹配（Levenshtein + 別名表）建立 company mapping
  3. **職缺語意比對**：同公司、不同標題（中文 vs 英文）→ LLM 判斷是否為同一職缺（批次預處理）
- 合併後保留所有來源連結

控制邊界：
- 使用者可選擇只看特定平台
- 去重結果可展開驗證
- 去重有誤時可回報（「這不是同一個職缺」）

#### 3.2 公司全貌卡片（苦工 #3, #8, #10）

**模式 C — 流程中自動**

UI 流程：
1. 搜尋結果按公司分組（參考 Job Frog）
2. 每家公司卡片自動帶入：

```
┌─────────────────────────────────────────────┐
│  [logo] 台積電 (2330)           ⭐ 追蹤     │
│  半導體業 · 新竹 · 上市                      │
│                                              │
│  💰 薪資中位數 355.2 萬（同業平均 258 萬）   │
│  📈 營收年增 +22%  ·  EPS 42.6              │
│  👥 正在徵 476 人（較上季 +18%）← 擴編信號  │
│                                              │
│  AI 洞察：營收創新高，正在擴招 AI/先進製程   │
│  團隊，薪資顯著高於同業。                    │
│                                              │
│  [查看 476 個職缺]                           │
└─────────────────────────────────────────────┘
```

3. 薪資數字來自 MOPS（標明年度）
4. 營收/EPS 來自 TWSE API
5. 「AI 洞察」= LLM 用財報+職缺數據生成一句話（預先生成，非即時）
6. 「較上季 +18%」= 定期快照比對

後端包裝：
- 大 prompt 模板：
  ```
  公司：{name}（{stock_id}）
  產業：{industry}
  薪資中位數：{median_salary}（同業：{industry_avg}）
  營收年增：{revenue_growth}
  EPS：{eps}
  近期職缺數變化：{job_count_trend}
  正在招募的職缺類型：{top_job_categories}

  用一句話（30 字內）總結這家公司對求職者的吸引力和風險。
  ```
- 由 Skill「company-insight」包裝
- 控制邊界：只用公開數據，不做主觀評價（「值得去」），只做客觀摘要（「營收創新高，正在擴招」）

#### 3.3 智慧公司推薦（苦工 #4）

**模式 A — AI 提案 → 用戶挑**

UI 流程：
1. 使用者填四個小格子：

```
┌─────────────────────────────────────────┐
│  🎯 幫我找適合的公司                     │
│                                          │
│  我的職能：[軟體工程 ▾]                  │
│  期望產業：[半導體 ☑] [金融 ☑] [軟體 ☐] │
│  最低年薪期望：[●────── 150 萬]          │
│  偏好規模：[⚡穩定] [📈成長] [🚀衝刺]   │
│                                          │
│  [為我推薦]                              │
└─────────────────────────────────────────┘
```

2. agent 依條件篩選 + 排序 → 顯示 TOP 10
3. 每家附「為什麼推薦」：
   - 「薪資中位數 355 萬 > 你的期望 150 萬」
   - 「營收年增 22%，正在擴招你的職能」
   - 「近 3 個月新增 120 個軟體工程職缺」
4. 使用者可調整任一條件重新排序

後端包裝：
- 篩選 = 結構化查詢（不需 LLM）：MOPS 薪資 > 期望值 + TWSE 產業匹配 + 職缺類別匹配
- 排序 = 加權分數：薪資距離 × 成長性 × 職缺匹配度
- 「為什麼推薦」= 模板填值（非 LLM）
- 控制邊界：推薦理由全部基於數據，不做主觀判斷

#### 3.4 行情比較（苦工 #10）

**模式 C — 流程中自動**

UI 流程：
1. 職缺詳情頁自動顯示：

```
💰 這家公司的薪資定位
├── 非主管中位數：355 萬（同業平均 258 萬，高出 37%）
├── 近一年變動：+8.2%
└── 切換比較：[全產業] [同業] [同職能]
```

2. 使用者可切換比較維度
3. 數據來自 MOPS，標明年度

### 第二波 — 時效 + 匹配

#### 3.5 AI 職缺評級（苦工 #5）

**模式 A — AI 提案 → 用戶挑**

- 上傳履歷一次 → AI 為每個搜尋結果打 S+~F 評級（參考 Jobuzzer）
- 使用者只看高分的，其他可隱藏
- 顯示評級理由：「技能匹配 85%，缺少 Kubernetes 經驗」

#### 3.6 外商 JD 中文摘要（苦工 #9）

**模式 B — 表單 → 一鍵產生**

- 英文 JD 自動翻譯 + 四欄摘要：職責/技能/亮點/門檻（參考 Job Frog）
- 預先生成存 DB，搜尋結果秒出

#### 3.7 新職缺即時通知（苦工 #5 延伸）

**模式 C — 流程中自動**

- 使用者設定追蹤條件（公司 + 職能 + 地點）
- 新職缺上線 → 即時推播（參考 Jobuzzer 的 Buzz）
- 免費延遲 12hr / 付費即時（參考 Jobuzzer 定價策略）

### 第三波 — 效率

#### 3.8 ATS 履歷分析（苦工 #6）

**模式 B — 表單 → 一鍵產生**

- 上傳履歷 + 選一個職缺 → ATS 通過率三維度分析（參考 Jobbo）
- 關鍵字匹配 60% + 量化成就 20% + 格式品質 20%
- AI 給出具體修改建議

#### 3.9 一鍵 Cover Letter（苦工 #7）

**模式 B — 表單 → 一鍵產生**

- 履歷 + JD + 公司資料 → 一鍵產生中英 Cover Letter（參考 Jobbo）
- 可編輯、可再生成

---

## 4. 可控性檢查

- [x] 每個 agent 動作前後都有使用者可介入點
- [x] 結果落在使用者預期內（搜什麼出什麼、數據是公開事實）
- [x] 可「重生 / 微調單格 / 退回上一步」（調條件重搜、切換比較維度）
- [x] 不是右邊一個 chat 視窗，是融進流程（薪資在卡片上、摘要在職缺裡）
- [x] 推薦理由透明（為什麼推這家、為什麼評 S+）
- [x] AI 生成內容標明「AI 摘要」，可切換看原始數據
- [x] 「AI 洞察」只做客觀摘要，不做主觀判斷（「營收創新高」✓、「值得去」✗）

### 成就感設計

| 使用者感受 | 怎麼做到 |
|-----------|---------|
| 「我比別人懂這家公司」 | 公司透視卡：薪資+財報+擴編信號，別的平台看不到 |
| 「我找到了別人沒看到的機會」 | 跨來源聚合去重 + 新職缺即時通知 |
| 「我的決定是有依據的」 | 每個推薦都有數據佐證，不是 AI 說了算 |
| 「投遞前我已經準備好了」 | ATS 分析 + 客製 Cover Letter |

---

## 5. 資料來源與串接

### 資料管線

```
第一層（核心 ~70%）：
  104 API → /company/ajax/list?zone=16（1,280 家上市櫃）
           → /jobs/search/api/jobs?zone=16（職缺搜尋）
           → /company/ajax/salary/top100（薪資 + exchangeId）

第二層（補齊，覆蓋率更高）：
  LinkedIn → job-source-mcp / JobSpy（Guest API）
           → 需建立 companyId ↔ 股票代號 mapping

第三層（官網差異）：
  ats-scrapers → SuccessFactors（台積電）/ Workday / Greenhouse / Lever
  逐家自建 → 鴻海 isite-web / 聯發科 / 金控自建

公開資料層：
  TWSE OpenAPI → 公司基本資料 + 營收 + 股價（JSON，免費）
  TPEx OpenAPI → 上櫃公司同上（英文欄位，需 mapping）
  MOPS → POST /mops/web/ajax_t100sb15（薪資 31 欄，HTML parse）

串接 key：股票代號
  TWSE 公司代號 = 104 exchangeId = MOPS 公司代號（已驗證）
```

### 開源工具

| 工具 | 用途 |
|------|------|
| `ats-scrapers`（PyPI） | ATS 爬蟲，50+ adapter 含 SuccessFactors |
| `job-source-mcp` | 104/CakeResume/Yourator/LinkedIn 爬蟲 |
| `JobSpy`（4.3K⭐） | LinkedIn/Indeed/Glassdoor 一行爬 |
| `TWSEMCPServer` | TWSE/TPEx 143 個 API tools |
| `JobSeek` 架構 | Monitor/Scraper 分離 + Typesense + Redis |

---

## 6. MVP 範圍（分階段）

### Day 1 — 公司全貌（靜態資料，不需爬蟲）

| 功能 | 說明 | 資料來源 |
|------|------|---------|
| 公司列表頁 | 1,984 家上市櫃公司，按產業/市值篩選 | TWSE + TPEx API |
| 公司全貌卡片 | 薪資中位數 + 營收 + EPS + 員工數 | MOPS + TWSE |
| 搜尋 | 公司名/產業/地點全文搜尋 | Typesense |
| 行情比較 | 同業薪資比較、排行榜 | MOPS |

> 這階段不需要爬蟲，只需要打公開 API + parse MOPS HTML，一兩天就能上線。
> 使用者價值：「台灣第一個把所有上市櫃公司的薪資和財報整理在一起的地方」。

### Day 2 — 加上職缺（104 爬蟲）

| 功能 | 說明 | 資料來源 |
|------|------|---------|
| 104 職缺聚合 | zone=16 上市櫃職缺，按公司分組 | 104 API（Cron 定時爬） |
| 職缺數趨勢 | 每家公司的職缺數變化（擴編/縮編信號） | 定期快照比對 |
| 公司卡片升級 | 卡片加上「正在徵 N 人」 | 104 jobCount |

### Day 3 — 跨來源 + AI

| 功能 | 說明 | 資料來源 |
|------|------|---------|
| LinkedIn 職缺聚合 | 補齊 104 沒有的 | job-source-mcp / JobSpy |
| 跨來源去重 | 104 + LinkedIn 同職缺合併 | 三層去重策略 |
| AI 公司洞察 | 一句話總結（預先生成） | Claude API |
| 外商 JD 摘要 | 英文 JD 四欄繁中摘要 | Claude API |

### Day 4 — 智慧功能

| 功能 | 說明 |
|------|------|
| 智慧公司推薦 | 填條件 → TOP 10 |
| 外商公司覆蓋 | ats-scrapers 爬 Greenhouse/Lever/Workday |

### 後續波次

| 功能 | 原因排到後面 |
|------|------------|
| AI 職缺評級 S+~F | 需要使用者上傳履歷，增加 onboarding 摩擦 |
| 新職缺即時通知 | 需要推播基建 |
| ATS 履歷分析 | 付費功能 |
| 一鍵 Cover Letter | 付費功能 |
| MCP Server | Jobuzzer 驗證可行，但非核心 |

---

## 7. 商業模式

### 免費/付費切割原則

> 護城河功能（公司全貌）的**基本版免費**吸引流量，**深度版付費**轉換營收。
> 免費要讓人覺得「好用」，付費要讓人覺得「更深入」。

| | 免費 | Pro（建議 $5-8/月） |
|---|---|---|
| 公司列表 + 搜尋 | ✅ 全部 | ✅ |
| 公司卡片 — 基本 | ✅ 薪資中位數 + 職缺數 | ✅ |
| 公司卡片 — 深度 | ❌ | ✅ 性別薪資、同業比較、EPS、擴編趨勢圖 |
| AI 公司洞察 | ✅ 一句話 | ✅ 詳細分析 |
| 跨平台搜尋 + 去重 | ✅ | ✅ |
| 公司推薦 TOP 10 | ✅ 每日 3 次 | ✅ 無限 |
| 薪資排行榜 | ✅ TOP 20 | ✅ 完整排行 + 篩選 |
| AI 職缺評級 | ❌ | ✅ |
| 即時通知 | 延遲 12hr | 即時 |
| ATS 履歷分析 | ❌ | ✅ 每月 30 次 |
| Cover Letter | ❌ | ✅ 每月 30 次 |
| CSV 匯出 | ❌ | ✅ |
| MCP API | 10 req/min | 100 req/min |

---

## 8. 技術棧

```
前端：TanStack Start（React + Vinxi/Nitro，原生 Cloudflare Workers 支援）
      TanStack Query（多資料源 cache/refetch）
      TanStack Table（職缺列表、薪資排行、公司比較表）
      TanStack Router（type-safe routing）
搜尋：Typesense Cloud（全文搜尋 + facet 篩選 + 中文分詞）
資料庫：Cloudflare D1（SQLite-based，邊緣部署）
快取/KV：Cloudflare KV（session、去重暫存、搜尋快取）
物件儲存：Cloudflare R2（JD 原文、履歷、公司 logo 快取）
爬蟲排程：Cloudflare Workers + Cron Triggers
AI：Claude API（摘要 + 洞察 + 評級）
部署：Cloudflare Pages（前端）+ Cloudflare Workers（API + 爬蟲）
分析：PostHog（參考 Jobuzzer）
```

### 8.1 Typesense 部署方案

Typesense 是架構裡唯一不在 Cloudflare 的服務。

| 方案 | 優劣 | 月費 |
|------|------|------|
| **Typesense Cloud**（推薦） | 官方 SaaS，零維運，API 直接用 | ~$30/月起 |
| 自建 VPS（Fly.io） | 一個 Docker container | ~$5-15/月 |
| 用 D1 FTS5 替代 | 全在 Cloudflare，但中文分詞需自己處理 | $0 |

建議 MVP 用 **Typesense Cloud**，省維運。Cloudflare Workers 打 Typesense API 跟打任何外部 API 一樣，無特殊限制。

### 8.2 D1 效能策略 — 預計算 denormalized 表

公司全貌卡片需要 JOIN 多張表（公司 + 薪資 + 職缺計數 + 營收）。D1 是 SQLite，大量 JOIN 可能慢。

**策略**：用 Cron Trigger 定期預計算一張 `company_profiles` denormalized 表。

```sql
-- 預計算表：每日由 Cron Worker 重建
CREATE TABLE company_profiles (
  stock_id TEXT PRIMARY KEY,        -- 股票代號 (2330)
  name TEXT,                         -- 公司名稱
  short_name TEXT,                   -- 簡稱
  industry TEXT,                     -- 產業分類
  market TEXT,                       -- sii(上市) / otc(上櫃)
  
  -- MOPS 薪資（年度更新）
  salary_median INTEGER,             -- 非主管薪資中位數（仟元）
  salary_mean INTEGER,               -- 非主管薪資平均數
  salary_median_prev INTEGER,        -- 前一年中位數
  salary_change_pct REAL,            -- 變動%
  industry_salary_avg INTEGER,       -- 同業平均
  employee_count INTEGER,            -- 員工人數
  eps REAL,                          -- EPS
  
  -- TWSE 營收（月度更新）
  revenue_latest INTEGER,            -- 最新月營收
  revenue_yoy_pct REAL,              -- 營收年增%
  market_cap INTEGER,                -- 市值（收盤價×股數）
  
  -- 104 職缺（每日更新）
  job_count_104 INTEGER,             -- 104 上的職缺數
  job_count_linkedin INTEGER,        -- LinkedIn 職缺數
  job_count_total INTEGER,           -- 合計（去重後）
  job_count_prev_month INTEGER,      -- 上月職缺數（擴編信號）
  job_count_trend TEXT,              -- 'expanding' / 'stable' / 'shrinking'
  top_job_categories TEXT,           -- JSON array of top 5 職缺類別
  
  -- AI 洞察（預先生成）
  ai_insight TEXT,                   -- 一句話洞察
  ai_insight_updated_at TEXT,        -- 洞察更新時間
  
  -- 串接 ID
  encoded_cust_no_104 TEXT,          -- 104 公司 ID
  linkedin_company_id TEXT,          -- LinkedIn company ID
  
  updated_at TEXT
);
```

這樣前端查公司列表只需 `SELECT * FROM company_profiles WHERE ...`，一張表搞定，不需 JOIN。

### 8.3 外商覆蓋邊界定義

「在台外商」的範圍：

| 條件 | 怎麼判斷 | 來源 |
|------|---------|------|
| **有台灣職缺** | 職缺地點包含台灣縣市 | 104/LinkedIn/官網爬蟲 |
| 不要求有台灣法人實體 | — | — |
| 不要求在台灣上市 | — | 上市櫃公司走核心層，外商走擴展層 |

**初始名單建立方式**：
1. 從 Job Frog 的 92 家開始（已整理好）
2. 104 搜尋 `zone=4,5`（外商篩選），取得更多
3. ats-scrapers 爬 Greenhouse/Lever API 時，篩選 location 含 Taiwan 的公司
4. 逐步擴充，不做人工策展（跟 Job Frog 的差異：我們用自動化擴展）

**外商公司在系統裡的標記**：
- 沒有股票代號 → 不串 TWSE/MOPS（沒有薪資中位數、營收等）
- 用 `company_type: 'foreign'` 區分
- 公司卡片顯示的資料不同（無薪資中位數，改顯示 Glassdoor/比薪水的 UGC 薪資，或標「未揭露」）

---

## 9. 競品差異化總結

| 面向 | 104 | Job Frog | Jobuzzer | Jobbo | **OfferNow** |
|------|-----|----------|---------|-------|-------------|
| 公司範圍 | 付費企業 | 92 外商 | 12K 全球 | 跨平台 | **2,000 上市櫃 + 全台 + 外商** |
| 薪資資料 | 有（分開頁面） | 無 | 無 | 無 | **✅ 卡片內建，串財報** |
| 財報交叉 | 無 | 無 | 無 | 無 | **✅ 營收×EPS×擴編信號** |
| 跨來源去重 | N/A | N/A | N/A | 有 | **✅** |
| AI 摘要 | 無 | ✅ 四欄 | ✅ 翻譯 | ✅ 三點 | **✅ + 公司洞察** |
| AI 評級 | 無 | 無 | ✅ S+~F | ✅ ATS% | **第二波** |
| MCP | 無 | 無 | ✅ | 無 | **第二波** |

---

## 附件

| 目錄 | 內容 |
|------|------|
| `docs/competitors/` | 競品地圖 + 5 個 teardown（Job Frog / Jobuzzer / Jobbo / LinkedIn / JobSeek OSS） |
| `docs/data-sources/` | 3 個資料來源 teardown（104 API / MOPS / TWSE API）+ ATS 深度研究 |
| `docs/product/` | 本文（產品規格） |
| `docs/tech/` | 待填：DB schema、API 設計、爬蟲架構 |
| `.research/` | 原始研究檔案（備份） |
