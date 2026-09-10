# Service Teardown: Jobuzzer

> 拆解日期：2026-09-10
> 目標：jobuzzer.com
> 要回答的問題：AI 履歷配對評分怎麼做？MCP 整合怎麼設計？商業模式細節？
> 對照目標：台灣百大上市櫃職缺聚合

---

## L1 — UI 層

### 首頁
- **標語**：「AI 幫你找，你只管投。」
- **規模數據**：599.9K+ 職缺、12K+ 追蹤公司、2.1K+ 用戶
- **三步驟核心價值**：
  1. **Buzz 即時通知**：職缺上線就推到信箱/瀏覽器
  2. **AI 評級（S+ ~ F）**：存一次履歷，AI 依經歷為每個職缺打分
  3. **履歷報告**：告訴你缺什麼，逐句建議怎麼改
- **即時職缺 Feed**：首頁展示最近擷取的職缺（12 分鐘前、16 分鐘前等）
- **追蹤公司 Logo 牆**：Google、Apple、Amazon、Meta、OpenAI、Anthropic 等
- **繁體中文完整翻譯**：含 FAQ、定價、所有 UI
- **iOS/Android**：未觀察到 App 連結

### 搜尋頁 (`/jobs`)
- **篩選器**：職位名稱/關鍵字、公司、工作模式、職缺類型、類別（70+ 類）、產業、級別（Entry~Executive）、地點、刊登時間、排序
- **AI Match 開關**：Toggle 按鈕，需登入上傳履歷
- **職缺卡片結構**：
  - 公司 logo + 名稱 + 職缺標題
  - 時間戳（如「2 小時前」）
  - 標籤：最新 / 混合 / 全職 / 總監 / 15+ 年 / 學士
  - AI 生成的繁中職缺摘要
  - 技能標籤（Field Service Engineering、Supply Chain Management 等）
  - 地點 + 薪資（有的話，如 $162,000–$200,000/yr）
  - 「客製化履歷」連結 → `/resume-report?jobId=...`
  - 申請 / 收藏按鈕
- **未登入限制**：可瀏覽所有職缺，但 AI Match 評級需登入 + 上傳履歷

`實測`

### 定價模式

| | 免費方案 | Buzz 方案 |
|---|---|---|
| **價格** | $0/月 | $5/月（年繳省 29%） |
| **通知** | 瀏覽器快訊，延遲 12 小時 | 每小時 Email + 瀏覽器快訊 |
| **AI 配對** | ❌ | ✅ S+~F 評級 |
| **AI 額度** | ❌ | 每月 150 點 |
| **履歷報告** | ❌ | ✅ |
| **履歷數** | 3 份 | 不限 |
| **篩選儲存** | 1 個 | 10 個 |
| **CSV 匯出** | ❌ | ✅ |
| **MCP API** | ✅（10 req/min） | ✅（100 req/min） |
| **試用** | — | 7 天免費 |

`實測`

---

## L2 — 流程層

### AI 評級流程（推測）
1. 使用者上傳履歷（文字貼上或 PDF）→ 存入帳號
2. 搜尋職缺時開啟 AI Match → 系統比對履歷與職缺要求
3. 為每個搜尋結果打 S+ ~ F 評級
4. 評級展示在職缺卡片上（如首頁 demo 的 S+）

### 履歷報告流程（推測）
1. 點擊「客製化履歷」→ `/resume-report?jobId=...&jobTitle=...`
2. 系統比對上傳的履歷與該職缺的 JD
3. 產出：硬技能覆蓋率（如 82%）、缺口（如 Kubernetes）、3 項建議修改（依影響力排序）
4. 消耗 AI 額度（150 點/月）

### 職缺同步流程
- FAQ 明確寫「直接從公司招聘頁面擷取，不從其他求職網站抓取」
- 「全天不間斷同步」— 推測為持續爬蟲 pipeline
- 「比主流求職網站更早」— 強調時效性差異

`推測` — 基於首頁 demo 和 FAQ

---

## L3 — 網路層

### API 架構

| 端點 | 用途 |
|------|------|
| `api.jobuzzer.com/api/auth/get-session` | 驗證 session |
| `api.jobuzzer.com/api/saved-filters` | 儲存的搜尋篩選（401 = 未登入） |
| `api.jobuzzer.com/api/stats/avatars` | 用戶頭像統計 |
| `mcp.jobuzzer.com/mcp` | MCP Server 端點 |

### 技術棧
- **框架**：Next.js（RSC，`_rsc` 參數）
- **CDN/防護**：Cloudflare
- **分析**：PostHog (us.i.posthog.com) + Google Analytics (G-J32LH912SS)
- **前後端分離**：`jobuzzer.com`（前端）+ `api.jobuzzer.com`（API）+ `mcp.jobuzzer.com`（MCP）
- **Auth**：Google OAuth

`實測`

---

## L4 — MCP API 設計（重點拆解）

Jobuzzer 提供完整的 MCP Server，這是競品中最獨特的功能。

### 11 個 MCP Tools

**解析工具（搜尋前置）：**
- `search_skills` — 把技能名稱解析成精確值
- `search_locations` — 把地點名稱解析成精確值
- `search_organizations` — 以名稱查詢公司 ID

**核心搜尋：**
- `search_jobs` — 篩選條件搜尋（工作模式/類型/職級/技能/地點/薪資），回傳分頁結果
- `get_job` — 取得單一職缺完整內容 + 直接投遞連結

**用戶操作：**
- `save_job` / `unsave_job` — 收藏管理
- `list_saved_jobs` — 列出收藏
- `mark_applied` — 記錄已投遞（不實際送出）
- `list_applications` — 列出投遞紀錄
- `update_application_status` — 更新進度（面試/作業/錄取/被拒/撤回）

### MCP 設計亮點
- **解析-搜尋分離**：先 resolve 技能/地點/公司名稱，再用精確值搜尋 — 避免模糊匹配錯誤
- **免費開放**：10 req/min（免費）/ 100 req/min（付費），不阻擋免費用戶
- **寫入權限分離**：save/mark_applied 需要寫入權限
- **支援多客戶端**：Claude、VS Code、Cursor、Codex 都有設定教學
- **提示詞產生器**：選好偏好後自動生成可貼上的 prompt

`實測`

---

## L5 — 邊界層

### 已觀察到的限制
- **AI Match 需登入 + 上傳履歷**：未登入只能瀏覽，不能評級
- **`saved-filters` API 回 401**：未登入時篩選儲存被阻擋
- **免費通知延遲 12 小時**：付費才有即時通知
- **AI 額度 150 點/月**：推測每份履歷報告消耗數點

### 未測試
- 登入後的 AI Match 實際評級體驗
- 履歷報告的完整內容和品質
- MCP Server 的實際呼叫 response schema
- 付費方案的 CSV 匯出格式

---

## L6 — 對照分析（vs 台灣百大上市櫃職缺聚合）

### 可直接借鏡

| Jobuzzer 做法 | 對我們的價值 | 難度 |
|--------------|-------------|------|
| AI S+~F 評級 | ✅ 用 MOPS 薪資 + JD 做配對，更有台灣特色 | 中 |
| 履歷報告（缺口+建議） | ✅ 差異化付費功能 | 中 |
| MCP Server 11 tools | ✅ 讓 AI 助手可以搜我們的職缺 | 中 |
| 解析-搜尋分離的 API 設計 | ✅ 好的 API 設計模式 | 低 |
| Freemium + $5/月 Buzz | ✅ 清晰的付費轉換點 | 低 |
| 12hr 延遲 vs 即時通知 | ✅ 時效性是付費轉換的利器 | 低 |
| 提示詞產生器 | ✅ 降低 MCP 使用門檻 | 低 |
| PostHog 分析 | ⚠️ 可考慮（比 GA4 更偏產品分析） | 低 |

### 我們可以超越的

| 缺口 | 我們的優勢 |
|------|-----------|
| 全球覆蓋但台灣稀疏 | 專注台灣 1,800+ 上市櫃 |
| 無公司財務/薪資資料 | TWSE API + MOPS 薪資中位數 |
| 純英文生態（翻譯而非原生） | 原生繁中，台灣 JD 本就是中文 |
| 無產業趨勢分析 | 可做「半導體業本週新增 X 缺」 |
| 無擴編/縮編信號 | 定期快照追蹤職缺數量變化 |
| AI 評級基於純文字比對 | 可加入產業薪資、公司規模等結構化資料 |

### Jobuzzer vs Job Frog 比較（給我們的啟示）

| 面向 | Job Frog | Jobuzzer |
|------|----------|---------|
| **定位** | 台灣外商科技 | 全球職缺 |
| **規模** | 92 家，3K 職缺 | 12K 家，600K 職缺 |
| **AI 角色** | 摘要+翻譯（預處理） | 評級+報告（互動式） |
| **商業模式** | 免費 side project | Freemium $5/月 |
| **MCP** | ❌ | ✅ 11 tools |
| **技術棧** | Next.js RSC | Next.js RSC + 獨立 API |
| **啟示** | 台灣本地化 + AI 摘要做得好 | 商業模式 + MCP 整合更成熟 |

---

## 已完成項目

| 層 | 項目 | 方法 |
|---|------|------|
| L1 | 首頁 UI 結構 + 規模數據 | Playwright snapshot |
| L1 | 搜尋頁篩選器 + 職缺卡片 | Playwright snapshot |
| L1 | 定價模式 | Playwright snapshot |
| L2 | AI 評級/履歷報告流程（推測） | UI + FAQ 分析 |
| L3 | API 端點 + 技術棧 | Network requests |
| L4 | MCP Server 完整 11 tools | MCP 文件頁 |
| L5 | 登入限制、API 401 | 觀察 |
| L6 | 對照分析 | — |

## 待深入項目

| 項目 | 需要條件 | 說明 |
|------|---------|------|
| AI Match 實際評級體驗 | 建立帳號 + 上傳履歷 | 看 S+~F 的實際分布 |
| 履歷報告完整內容 | 建立帳號 + Buzz 方案 | 看報告品質和 AI 額度消耗 |
| MCP Server response schema | 建立帳號 + MCP 呼叫 | 確認 search_jobs 回傳欄位 |
| 付費 CSV 匯出格式 | Buzz 方案 | 確認匯出的資料完整度 |

## 沒拿到的

- AI 評級的具體演算法和使用的 LLM 模型
- MCP API 的完整 response schema（需登入呼叫）
- 爬蟲覆蓋的 ATS 平台清單（12K 家公司用哪些系統）
- 履歷報告的 AI 額度消耗比例

## 殘留清單

無（未建立任何測試資料或登入 session）

---

## 原始擷取路徑

- `.playwright-mcp/jobuzzer-home-snapshot.md`
- `.playwright-mcp/jobuzzer-home-network.md`
- `.playwright-mcp/jobuzzer-search-snapshot.md`
- `.playwright-mcp/jobuzzer-search-network.md`
- `.playwright-mcp/jobuzzer-mcp-docs.md`
