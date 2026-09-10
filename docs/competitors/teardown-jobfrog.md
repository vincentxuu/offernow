# Service Teardown: Job Frog (職缺青蛙)

> 拆解日期：2026-09-10
> 目標：job-frog.com
> 要回答的問題：搜尋怎麼實作？AI 摘要的觸發時機？資料管線架構？
> 對照目標：台灣百大上市櫃職缺聚合

---

## L1 — UI 層

### 首頁
- **搜尋框**：支援中英文關鍵字（「輸入職位、技能或描述」）
- **篩選器**：工作經驗、工作類型、地點、發布時間
- **導航**：本日新缺（需登入）、公司一覽、登入
- **Dark mode** 切換
- **更新通知 Dialog**：最近新增「我的追蹤」功能（追蹤公司+職缺類型組合，App 推播）
- **iOS App**：App Store 連結 (id6799597622)
- **意見箱**：Google Forms

### 搜尋結果頁
- **按公司分組**展示（NVIDIA 25 個職缺、ASML 36 個等）
- **AI 分類標籤列**：軟體工程 299、現場服務 56、品質與測試 40、硬體工程 34 等 12 類
- **管理層級篩選**：管理職 9、非管理職 480
- **職缺卡片**含 4 個 AI 生成欄位（繁中）：
  - 職責：一句話總結工作內容
  - 領域：技術領域分類
  - 技能：關鍵字清單
  - 亮點：賣點
- **操作按鈕**：收藏、分享、「我要申請」（導流到原始 ATS）

### 職缺詳情頁 (`/jobs/{id}`)
- **AI 職缺摘要**（職責/領域/技能/亮點）— 繁中
- **學歷要求**：從 JD 萃取（如 "Master"）
- **完整原文 JD**：保留英文原文
- **類似職缺推薦**：跨公司推薦（Microsoft、Google、Siemens 等）
- **申請導流**：`/go/{id}` → 跳轉到原始 ATS 申請頁

### 公司一覽頁 (`/companies`)
- **92 間公司，3000+ 個台灣職缺**
- **每家公司的 AI 生成介紹**：
  - 一句話標題（如「全球唯一 EUV 微影設備製造商」）
  - 詳細介紹段落（含台灣在地觀點）
  - 3 個核心業務標籤
  - 總部所在地
- **篩選**：IC 設計、半導體、軟體/雲端、生醫/醫療、金融/顧問、其他
- **排序**：A–Z、市值

`實測`

---

## L2 — 流程層

### 搜尋流程
1. 使用者輸入關鍵字 → URL 變成 `?searched=1&q=software&q=engineer`（空格分成多個 q 參數）
2. Next.js RSC 在伺服器端渲染結果 → 秒出（無 loading spinner）
3. 結果按公司分組，展示公司名 + 職缺數
4. 展開公司 → 觸發 `/api/search?companyExact=NVIDIA&page=1&pageSize=10&q=...` 載入職缺卡片
5. 點擊職缺 → `/jobs/{id}` 詳情頁（RSC 渲染）
6. 點「我要申請」→ `/go/{id}` 跳轉到原始 ATS

### AI 摘要時機
- **預先生成**（非即時）：搜尋結果秒出且包含摘要，沒有額外 LLM API 呼叫
- 推測爬蟲抓到新職缺時，批次跑 Claude API 生成摘要後存入 DB

`實測` + `推測`

---

## L3 — 網路層

### API 端點

| 端點 | 方法 | 用途 |
|------|------|------|
| `/?searched=1&q=...&_rsc=...` | GET | 初始搜尋（RSC 伺服器端渲染） |
| `/api/search?companyExact=X&page=1&pageSize=10&q=...` | GET | 展開公司載入職缺列表 |
| `/jobs/{id}?_rsc=...` | GET | 職缺詳情（RSC） |
| `/go/{id}` | GET | 跳轉到原始 ATS 申請頁（click tracking） |
| `/api/analytics/search` | POST | 搜尋分析 |
| `/api/analytics/events` | POST | 事件追蹤 |
| `/companies?_rsc=...` | GET | 公司列表（RSC） |

### 技術棧
- **框架**：Next.js 14+（React Server Components）
- **CDN/防護**：Cloudflare（`cdn-cgi/challenge-platform`）
- **分析**：Google Analytics 4 (G-7J1PF00QL6) + 自建分析
- **Logo**：嘗試從 `/logos/{company}.png` 載入（大量 404），fallback 到外部 favicon
- **渲染**：伺服器端為主，搜尋結果不走獨立 API，而是 RSC streaming

`實測`

---

## L4 — 資料結構

### 職缺 schema（從 UI 反推）

```
Job {
  id: number              // 16996
  title: string           // "System Software Engineer (RDSS Intern)"
  company: string         // "NVIDIA"
  location: string        // "台北"
  jobType: string         // "實習" | "正職" | "混合/遠端"
  experience: string      // "<1年" | "1-3年" | "不限"
  category: string        // "軟體工程"（AI 分類）
  managementLevel: string // "管理職" | "非管理職"
  publishDate: date       // 2026-08-30
  education: string       // "Master"
  
  // AI 生成（繁中）
  summary: {
    responsibilities: string  // 職責
    domain: string           // 領域
    skills: string           // 技能
    highlights: string       // 亮點
  }
  
  description: string     // 完整原文 JD（英文）
  applyUrl: string        // 原始 ATS 申請連結
}
```

### 公司 schema（從 UI 反推）

```
Company {
  slug: string            // "nvidia"
  name: string            // "NVIDIA"
  logo: image
  headquarters: string    // "美國加州聖塔克拉拉"
  sector: string          // "半導體"
  
  // AI 生成（繁中）
  tagline: string         // "全球 AI 運算晶片的絕對王者"
  description: string     // 詳細介紹（含台灣在地觀點）
  tags: string[]          // ["GPU 設計", "AI 加速器", "資料中心"]
  
  jobCount: number        // 25
}
```

`推測` — 基於 UI 反推，未確認實際 DB schema

---

## L5 — 邊界層

### 已觀察到的限制
- **「本日新缺」需登入**：未登入只能看搜尋和公司列表，無法看每日更新
- **Cloudflare 保護**：有 challenge platform，但未觸發（正常瀏覽無阻）
- **Logo 大量 404**：`/logos/` 路徑下公司 logo 大量缺失，似乎在遷移載入方式
- **搜尋結果上限**：顯示 "400+ 筆"（不精確數字），推測有分頁但未顯示總數

### 未測試
- 登入後的功能（追蹤、收藏列表、通知設定）
- iOS App 的推播機制
- 搜尋的 rate limiting

---

## L6 — 對照分析（vs 台灣百大上市櫃職缺聚合）

### 可直接借鏡

| Job Frog 做法 | 對我們的價值 | 難度 |
|--------------|-------------|------|
| AI 四欄摘要（職責/領域/技能/亮點） | ✅ 直接套用，改用中英雙語 | 低 |
| 預先生成摘要存 DB，搜尋秒出 | ✅ 批次 LLM 處理 > 即時 | 低 |
| 按公司分組展示 | ✅ 核心 UX，上市櫃公司為軸心 | 低 |
| 公司介紹頁含台灣在地觀點 | ✅ 用 TWSE 資料 + LLM 生成 | 中 |
| 產業分類篩選 | ✅ 用 TWSE 產業分類 | 低 |
| `/go/{id}` 導流追蹤 | ✅ 點擊追蹤是商業模式基礎 | 低 |
| RSC 伺服器端渲染 | ✅ SEO + 效能 | 中 |

### 我們可以超越的

| 缺口 | 我們的優勢 |
|------|-----------|
| 只有 92 家外商 | 我們覆蓋 1,800+ 家上市櫃 |
| 無薪資資料 | MOPS 員工薪資中位數是獨家資料 |
| 無財務資料 | TWSE API 提供營收、市值、產業分類 |
| 無歷史趨勢 | 定期快照可追蹤擴編/縮編信號 |
| 無多來源交叉比對 | 官網 + 104 + LinkedIn 去重 |
| 只做科技/金融/生醫 | 全產業覆蓋 |
| 無中文原生 JD 處理 | 台灣上市櫃多數 JD 就是中文 |

---

## 已完成項目

| 層 | 項目 | 方法 |
|---|------|------|
| L1 | 首頁 UI 結構 | Playwright snapshot |
| L1 | 搜尋結果 UI | Playwright snapshot |
| L1 | 職缺詳情 UI | Playwright snapshot |
| L1 | 公司一覽 UI | Playwright snapshot |
| L2 | 搜尋流程（輸入→結果→詳情→申請） | 逐步操作 |
| L3 | API 端點時序 | Network requests 記錄 |
| L3 | 技術棧辨識 | Network + DOM 分析 |
| L4 | 職缺/公司 schema 反推 | UI 結構分析 |
| L5 | 登入限制、Cloudflare 保護 | 觀察 |
| L6 | 對照分析 | — |

## 待深入項目

| 項目 | 需要條件 | 說明 |
|------|---------|------|
| 登入後功能 | 建立帳號 | 追蹤、收藏、通知設定 |
| ATS 爬蟲覆蓋率 | — | 確認 92 家各用哪個 ATS |
| 搜尋 API response body | 登入 or API 攔截 | 確認 schema 完整欄位 |
| iOS App 推播 | 下載 App | 通知頻率與觸發條件 |

## 沒拿到的

- 搜尋 API 的完整 response schema（RSC payload 混在 HTML 裡，難以獨立擷取）
- LLM 摘要的具體 prompt 和使用的模型版本
- 爬蟲排程頻率（推測每日，但無確認）
- 資料庫架構（只能從 UI 反推）

## 殘留清單

無（未建立任何測試資料或登入 session）

---

## 原始擷取路徑

- `.playwright-mcp/jobfrog-home-snapshot.md`
- `.playwright-mcp/jobfrog-home-network.md`
- `.playwright-mcp/jobfrog-search-result-snapshot.md`
- `.playwright-mcp/jobfrog-search-network.md`
- `.playwright-mcp/jobfrog-nvidia-expanded.md`
- `.playwright-mcp/jobfrog-job-detail-snapshot.md`
- `.playwright-mcp/jobfrog-job-detail-network.md`
- `.playwright-mcp/jobfrog-companies-snapshot.md`
