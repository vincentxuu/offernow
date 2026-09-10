# OfferNow UI 參考資料

> 整理日期：2026-09-10
> 目的：為 OfferNow 各核心頁面找到值得參考的 UI 設計

---

## 🏆 最高參考價值

### 1. Cavuno TanStack Start Job Board Template
- **URL**: https://github.com/wollemiahq/cavuno-tanstack-start-shadcn-job-board-template
- **為什麼重要**：**跟我們技術棧完全一致**（TanStack Start + Cloudflare Workers + shadcn/ui + Tailwind CSS）的完整 job board template。有公司頁、薪資頁、職缺搜尋、master/detail、SEO 路由全部做好。
- **值得看的**：
  - `/companies/:slug/salaries` 薪資頁面結構
  - `/jobs` 搜尋 + master/detail 佈局
  - `/salaries` hub（按 title / skill / location 切）
  - 處理 messy data 的策略（長標題 clamp、缺薪資時 omit、技能 tag cap at 3+N）
  - programmatic SEO 路由設計
- **參考部分**：整體架構、路由設計、元件結構

### 2. Levels.fyi
- **URL**: https://levels.fyi
- **值得看的**：
  - 公司頁面：薪資拆分（base / stock / bonus）+ 表格 + 百分位數視覺化
  - 薪資比較：公司 vs 公司的並排比較 UI
  - 表格設計：可排序、可匯出、欄位可切換
- **參考部分**：薪資資料的呈現方式、百分位數圖表、公司比較 UI

### 3. Glassdoor 公司頁面
- **URL**: https://glassdoor.com/Reviews/index.htm
- **值得看的**：
  - 公司總覽卡片：評分 + 員工數 + 辦公室數 + 職缺數 + review 數 + 薪資數
  - 「Jobs / Reviews / Salaries」tab 切換
  - 公司比較功能
- **參考部分**：公司全貌卡片的資訊密度平衡

---

## 🎯 公司卡片 + 公司頁面

### 4. Wellfound (AngelList)
- **URL**: https://wellfound.com/candidates/overview
- **值得看的**：
  - 公司卡片：logo + 名稱 + 一句話介紹 + 公司規模 + 薪資範圍 + 股權
  - 一鍵申請（profile = application）
  - 薪資和股權直接顯示在職缺列表上
- **參考部分**：薪資透明的卡片設計、公司規模標籤

### 5. JobSeek CompanyCard 元件（開源）
- **URL**: https://github.com/colophon-group/jobseek/blob/main/apps/web/src/components/search/company-card.tsx
- **值得看的**：
  - 按公司分組的搜尋結果（跟我們的需求一致）
  - 公司卡片展開 → 內嵌職缺列表（可滾動、infinite scroll）
  - React.memo + shallow equality 優化（大量卡片效能）
- **參考部分**：按公司分組的具體 React 實作

### 6. Crunchbase
- **URL**: https://crunchbase.com
- **值得看的**：
  - 公司頁面：財務數據（融資 / 營收 / 員工數）+ 時間軸
  - 公司比較表
  - 篩選器設計（產業 / 規模 / 地點 / 融資階段）
- **參考部分**：財務數據的卡片呈現（跟我們的 TWSE 營收 / EPS 類似）

---

## 🔍 搜尋 + 篩選 + 職缺列表

### 7. RemoteOK
- **URL**: https://remoteok.com
- **值得看的**：
  - 極簡單列表設計（一行一個職缺，展開看詳情）
  - 薪資 + 福利直接顯示在列表行上
  - 標籤系統（AI / Async / Distributed / Executive 等）
  - 黑暗模式切換
  - Solo operator 做到 $110K/月的 UI — 證明極簡也能成功
- **參考部分**：極簡列表的資訊密度、標籤篩選

### 8. AngelList Careers 頁面
- **URL**: https://angellist.com/careers
- **值得看的**：
  - 每個職缺卡片 = 一行：職稱 + 一句話描述 + 地點
  - 按部門分組（Funds / Nova / AngelList）
  - 極度精簡但資訊充足
- **參考部分**：按部門/公司分組的極簡列表

---

## 📊 資料儀表板 + 排行榜

### 9. Stock Screener UI（Dribbble）
- **URL**: https://dribbble.com/search/stock-screener
- **值得看的**：
  - 股票篩選器的 UI 跟我們的「公司篩選」非常相似（市值 / 產業 / 營收成長）
  - 資料表格 + 篩選器 + 排序的組合
  - 數字的顏色編碼（綠漲紅跌）
- **參考部分**：財務數據篩選器的 UI 模式

### 10. Figma Stock Market Dashboard UI Kit
- **URL**: https://www.figma.com/community/file/1359230717010633204
- **值得看的**：
  - 金融數據卡片設計（走勢圖 + 數字 + 變動百分比）
  - Dark mode 設計
  - Portfolio 概覽的佈局
- **參考部分**：數字 + 趨勢圖的卡片組合（可用於擴編信號視覺化）

### 11. Financial Dashboard Best Practices（Eleken）
- **URL**: https://www.eleken.co/blog-posts/financial-dashboard-examples
- **值得看的**：
  - 設計原則：summary before detail、encode state in form as well as number
  - 平衡 simplicity and depth
  - 設計 for decision-making（每個圖表回答一個具體問題）
- **參考部分**：資料密集型 UI 的設計原則

---

## 🧩 元件庫 + 模板

### 12. shadcn/ui Job Board 元件
- **Job Card**: https://21st.dev/@ruixen.ui/components/job-card — 公司 avatar + 薪資 + 地點 + 技能 tag
- **Job Listings Table**: https://www.shadcn.io/blocks/tables-job-listings — 表格式職缺列表 + badge + 薪資
- **Careers Block**: https://www.shadcnblocks.com/block/careers6 — stats header + job cards
- **Job Details**: https://www.shadcn-ui-blocks.com/blocks/marketing/careers/job-details — 雙欄職缺詳情
- **Open Positions**: https://www.shadcn.io/blocks/about-open-positions — 部門篩選 + 動畫列表
- **值得看的**：都是 shadcn/ui 元件，跟我們的技術棧直接相容

### 13. Talentry AI Job Search Dashboard（Figma）
- **URL**: https://creativemarket.com/wencory/291591616-AI-Powered-Job-Search-Dashboard-UI
- **值得看的**：
  - AI match score 在職缺卡片上的呈現
  - 側邊欄篩選器設計
  - CV rating 和 interview readiness 指標
- **參考部分**：AI 功能在 UI 上的融入方式

### 14. Jobnetic Figma Template
- **URL**: https://themes.aedevstudio.com/templates/themeforest/89934-jobnetic-job-board-career-portal-figma-template
- **值得看的**：93+ 頁面完整設計系統（求職者 + 企業 + 後台）
- **參考部分**：完整 job board 的頁面清單和流程

---

## 🏗️ 開源全端 Job Board（技術 + UI 雙參考）

### 15. Cavuno Template（TanStack Start + Cloudflare）
- 同 #1，技術棧完全匹配

### 16. Indeed Clone（Next.js + Convex + shadcn）
- **URL**: https://github.com/sonnysangha/Vibe-Code-the-Right-Way-Ep-1-Indeed-Clone-Multi-Tenant-Clerk-Convex-MCP
- **值得看的**：多租戶公司 workspace、applicant pipeline kanban、即時通知
- **參考部分**：企業端功能的 UI 設計

### 17. Opentunity（TanStack Start + AI）
- **URL**: https://github.com/jaimenguyen168/tanstack-opentunity
- **值得看的**：AI resume scanning → profile extraction → job matching 的 UI 流程
- **參考部分**：AI 功能在 TanStack Start 裡的實作

### 18. CepatHire（TanStack Router + Cloudflare Workers）
- **URL**: https://github.com/Wafiqsw/cepat-hire
- **值得看的**：自然語言搜尋 → AI auto-apply 的 UX、Cloudflare Workers 部署
- **參考部分**：AI 驅動的搜尋 UI

---

## 📋 OfferNow 各頁面的參考對照表

| OfferNow 頁面 | 主要參考 | 次要參考 |
|--------------|---------|---------|
| **公司全貌卡片** | Glassdoor 公司卡 + Crunchbase 財務 | Wellfound 薪資透明卡 |
| **搜尋結果（按公司分組）** | JobSeek CompanyCard + Job Frog | AngelList Careers |
| **薪資排行榜** | Levels.fyi 薪資表 | Stock Screener UI |
| **職缺列表** | Cavuno Template + shadcn Job Card | RemoteOK 極簡列表 |
| **篩選器** | Crunchbase + Stock Screener | Talentry 側邊欄 |
| **公司詳情頁** | Glassdoor（tab 切換）| Levels.fyi 公司頁 |
| **職缺詳情頁** | shadcn Job Details | Cavuno Template |
| **AI 洞察呈現** | Talentry AI match score | Jobuzzer S+~F 評級 |
| **擴編/薪資趨勢圖** | Figma Stock Dashboard | 金融儀表板 best practices |
| **整體技術實作** | **Cavuno Template**（第一優先） | Opentunity + CepatHire |
