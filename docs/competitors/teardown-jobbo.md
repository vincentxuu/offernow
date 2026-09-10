# Service Teardown: Jobbo

> 拆解日期：2026-09-10
> 目標：jobbojobs.com
> 要回答的問題：跨平台聚合怎麼做？去重邏輯？Chrome Extension 架構？
> 對照目標：台灣百大上市櫃職缺聚合

---

## L1 — UI 層

### 首頁
- **標語**：「100+ 職缺一次到齊，剩下的只要滑一下。」
- **定位**：為台灣求職者打造的職缺整合神器
- **四大平台**：LinkedIn、104 人力銀行、CakeResume、1111 人力銀行
- **永久免費 + 不需信用卡 + 30 秒上手**

### 核心四步驟

**Step 1 — 一鍵整合**
- 設定目標職位 → 四大平台同步搜尋
- 自動去重 + 完整 JD 抓取
- 23 秒完成（vs 手動 1 小時）

**Step 2 — 滑卡決定（Tinder 模式）**
- 每張卡片一個職缺：公司 logo + 職稱 + 薪資 + 地點 + 技能標籤
- **ATS 通過率百分比**（如 88%、84%、81%）
- **AI 重點摘要**：3 個重點（如「打造 Agent 架構」「熟悉 RAG / 向量檢索」）
- 來源平台標記（LinkedIn / 104 / CakeResume）
- 向右投遞 / 向左略過 / 鍵盤支援

**Step 3 — ATS 履歷分析**
- ATS 通過率評分 = 三維度加權：
  - 關鍵字匹配（60% 權重）
  - 量化成就（20% 權重）
  - 格式品質（20% 權重）
- AI 優化建議（如「建議加入 RAG pipeline 等關鍵字」）

**Step 4 — 一鍵 Cover Letter**
- 結合履歷 + JD 自動生成
- 中英雙語
- 可編輯、可一鍵複製

### Demo 職缺卡片（首頁展示）

| 來源 | 公司 | 職位 | 薪資 | ATS 率 |
|------|------|------|------|--------|
| LinkedIn | Appier | AI Engineer | 90K-130K TWD/月 | 88% |
| 104 | Trend Micro | AI Solutions Architect | 130K-180K TWD/月 | 84% |
| CakeResume | Kdan Mobile | LLM Application Engineer | 80K-120K TWD/月 | 81% |
| LinkedIn | Jobbo | Senior PM — AI Tools | 110K-160K TWD/月 | 92% |

`實測`

---

## L3 — 網路層

### API
- `GET /api/auth/me` → 401（未登入）
- **分析**：Mixpanel（不是 GA4 或 PostHog）
- **前端**：靜態網站（非 Next.js RSC），登入走 `/login.html`
- **無搜尋 API 在首頁觸發**：搜尋/聚合功能需要登入後才能使用

### 技術觀察
- 前端是純靜態 HTML/CSS/JS（`.html` 副檔名）
- 無 Cloudflare 防護（跟 Job Frog / Jobuzzer 不同）
- 推測核心聚合邏輯在用戶端（Chrome Extension）或登入後的 SPA

`實測`

---

## L4 — 產品機制分析

### 跟 Job Frog / Jobuzzer 的根本差異

Jobbo 不是「平台先爬好職缺讓你搜」，而是「你登入後即時幫你搜四大平台、現場聚合」。

| 面向 | Job Frog / Jobuzzer | Jobbo |
|------|---------------------|-------|
| **爬取時機** | 平台預先爬 | 使用者觸發即時搜尋 |
| **職缺來源** | 公司官網 career page | 人力銀行（104/LinkedIn/CakeResume/1111） |
| **去重** | 平台端預處理 | 即時去重 |
| **資料儲存** | 平台 DB | 推測為用戶端或 session 級 |

### ATS 通過率的計算邏輯（從 UI 反推）

```
ATS_Score = 關鍵字匹配(60%) + 量化成就(20%) + 格式品質(20%)
```

- **關鍵字匹配**：比對 JD 關鍵字 vs 履歷關鍵字
- **量化成就**：有沒有數字化的成果描述
- **格式品質**：段落結構、項目符號使用
- 結果是百分比（如 88%），比 Jobuzzer 的 S+~F 更精確

`推測` — 基於首頁 demo UI

---

## L5 — 邊界層

### 已觀察到的限制
- **所有核心功能需登入**：首頁只有 demo，搜尋/滑卡/分析/Cover Letter 都在登入後
- **無公開 API**：首頁只打了 `/api/auth/me`
- **Chrome Extension 可能是核心**：跨平台抓取可能透過 Extension 在用戶端執行（繞過 CORS 和反爬）

### 未測試
- 登入後的搜尋流程和 API
- Chrome Extension 架構
- 付費方案（首頁只提到「永久免費」但有「隨時可升級」）
- 去重的精確度

---

## L6 — 對照分析（vs 台灣百大上市櫃職缺聚合）

### 可借鏡

| Jobbo 做法 | 對我們的價值 | 難度 |
|-----------|-------------|------|
| **Tinder 式滑卡 UX** | ⭐⭐⭐ 可考慮做進 App 版 | 中 |
| **ATS 通過率三維度評分** | ⭐⭐⭐⭐ 比 Jobuzzer 的 S+~F 更精確，可作為付費功能 | 中 |
| **四平台即時去重** | ⭐⭐⭐ 去重邏輯是核心，我們也需要跨來源去重 | 高 |
| **AI 重點摘要（3 點）** | ⭐⭐⭐ 比 Job Frog 的四欄更簡潔 | 低 |
| **一鍵 Cover Letter** | ⭐⭐ 附加價值，非核心差異化 | 中 |
| **Mixpanel 分析** | ⭐⭐ 產品分析工具選型參考 | 低 |

### 我們超越的空間

| 缺口 | 我們的優勢 |
|------|-----------|
| 只整合人力銀行（被動刊登的職缺） | 我們也爬公司官網（主動覆蓋） |
| 不以公司為軸心 | 我們以上市櫃公司為核心 |
| 無薪資/財務資料 | TWSE API + MOPS |
| 無歷史趨勢 | 定期快照 |
| 用戶端即時搜尋（慢、不穩定） | 伺服器端預爬（快、穩定） |

### 三家競品 UX 比較

| UX 模式 | 代表 | 適合場景 |
|---------|------|---------|
| **按公司分組** | Job Frog | 「我想看 NVIDIA 有什麼缺」— 公司導向 |
| **搜尋結果列表** | Jobuzzer / 104 | 「我想找 AI Engineer」— 職位導向 |
| **滑卡決定** | Jobbo | 「幫我快速篩一批」— 效率導向 |

我們的 UX 建議：**主打公司導向**（上市櫃為軸心，跟 Job Frog 一樣按公司分組），但加上搜尋列表和滑卡作為輔助模式。

---

## 已完成項目

| 層 | 項目 | 方法 |
|---|------|------|
| L1 | 首頁完整 UI 結構 | Playwright snapshot |
| L1 | 四步驟產品流程 | Playwright snapshot |
| L1 | Demo 職缺卡片結構 | Playwright snapshot |
| L3 | API + 技術棧辨識 | Network requests |
| L4 | 產品機制分析（即時聚合 vs 預爬） | UI 分析 |
| L5 | 登入限制 | 觀察 |
| L6 | 對照分析 + 三家 UX 比較 | 分析 |

## 待深入項目

| 項目 | 需要條件 | 說明 |
|------|---------|------|
| 登入後搜尋流程 | 建立帳號 | 看即時聚合的 API 和去重機制 |
| Chrome Extension 架構 | 安裝 Extension | 確認爬取是 Extension 端還是伺服器端 |
| 付費方案 | 登入 | 確認升級內容 |

## 沒拿到的

- 搜尋/聚合的實際 API（需登入）
- 去重的具體演算法
- Chrome Extension 的技術架構
- 付費方案定價和功能

## 殘留清單

無

---

## 原始擷取路徑

- `.playwright-mcp/jobbo-home-snapshot.md`
- `.playwright-mcp/jobbo-home-network.md`
