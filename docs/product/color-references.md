# OfferNow 配色參考

> 整理日期：2026-09-10

---

## A. 配色工具（自己調配色）

| 工具 | URL | 說明 | 適合 OfferNow 的原因 |
|------|-----|------|---------------------|
| **Realtime Colors** | realtimecolors.com | 即時預覽配色在真實 UI 上的效果 | 最實用 — 直接看配色套在頁面上的感覺 |
| **Coolors** | coolors.co | 按空白鍵隨機生成五色組合，可鎖定調整 | 快速探索大量配色方案 |
| **Happy Hues** | happyhues.co | 配色直接套在 UI demo 上展示 | 看配色在卡片、按鈕、背景的搭配效果 |
| **Huemint** | huemint.com | AI 生成配色，可指定品牌風格 | 給定一個主色，AI 推薦搭配 |
| **ColorHunt** | colorhunt.co | 社群投票的四色組合，可按風格篩選 | 搜 "professional" "dashboard" 找靈感 |
| **Learn UI Data Color Picker** | learnui.design/tools/data-color-picker.html | 專門給資料視覺化的配色工具 | 圖表、趨勢線的配色用這個 |
| **Adobe Color** | color.adobe.com | 色輪 + 對比度檢查 + WCAG 無障礙驗證 | 確保可及性 |

## B. shadcn/ui 主題工具（直接用在我們的技術棧）

| 工具 | URL | 說明 |
|------|-----|------|
| **shadcn/ui Create** | ui.shadcn.com/create | 官方工具，選色 + 字體 + 主題一站搞定 |
| **shadcn/ui Colors** | ui.shadcn.com/colors | 完整 Tailwind 色票（HEX/RGB/HSL/CSS variables） |
| **TweakCN** | tweakcn.com | 單色生成完整 shadcn 主題（light + dark），一鍵匯出 tailwind config |
| **shadesigner** | shadesigner.com | shadcn 調色盤設計器，介面漂亮 |
| **ShadCN Radix Colors** | ui.ewgenius.me/shadcn-radix-colors | 用 Radix Colors 生成 shadcn 主題 |
| **10000+ Themes** | ui.jln.dev | 一萬多個 shadcn 主題可預覽套用 |
| **UIColorful** | uicolorful.com | 從圖片或任意顏色生成 shadcn 主題 |

## C. 品牌配色參考（看別人怎麼選）

### 資料密集型 SaaS（最接近我們）

| 品牌 | 主色 | 風格 | 值得看的 |
|------|------|------|---------|
| **Mercury**（新創銀行） | 深藍 + 白 | 金融信任感，editorial typography | 金融數據卡片的配色克制 |
| **Stripe** | 靛紫 #635bff + 白 | 極簡，色彩只用在狀態 | 「色彩 = 狀態」原則 |
| **Linear** | 紫藍漸層 + 深色 | 開發者工具，一個強調色 | 深色模式的單色強調 |
| **Vercel** | 純黑白 + 綠/橙/紅 狀態色 | 幾乎無彩色，狀態色很純 | 用最少的色彩傳達最多資訊 |
| **PostHog** | 深藍 #1d4aff + 黃 | 分析工具，活潑但專業 | 資料儀表板 + 圖表的配色 |
| **Plausible** | 靛青 #4f46e5 + 淺灰 | 輕量分析，乾淨 | 極簡圖表配色 |

### 職缺平台

| 品牌 | 主色 | 風格 |
|------|------|------|
| **Job Frog** | 綠 #22c55e + 白 | 親切、台灣在地感 |
| **Jobuzzer** | 深灰 + 藍紫強調 | 全球科技感 |
| **RemoteOK** | 黃 + 黑 | 極簡、高對比 |
| **104** | 橙 #f97316 + 白 | 台灣主流、辨識度高 |
| **CakeResume** | 綠 + 白 | 科技新創清新感 |
| **Levels.fyi** | 藍 #3b82f6 + 白 | 數據導向、信任感 |

### 2026 SaaS 配色趨勢（from Tentackles）

| 配色名 | 適合 | 主色 | 感覺 |
|--------|------|------|------|
| **Oatmeal & Ink** | 研究平台、企業 SaaS | 米色 + 深墨 | 精緻信任感 |
| **Radioactive Earth** | 金融科技、AI 基建 | 深綠 + 螢光綠 | 永續 + 能量 |
| **Safety Orange** | 開發工具、資安 | 深色 + 橙 | 權威感 |
| **Digital Twilight** | AI 產品、agent 平台 | 暗紫漸層 | 流動精緻 |

## D. OfferNow 配色建議方向

基於產品定位（資料密集 + 台灣市場 + 信任感 + 上市櫃公司），有四個可能方向：

### 方向 1：專業穩重（Mercury / Stripe 路線）
```
主色：深藍 #1e3a5f
強調：金/琥珀 #c4a35a
背景：冷白 #f8f9fc
狀態：綠/橙/紅
```
→ 「這裡的數據可以信」

### 方向 2：科技活力（Levels.fyi / Linear 路線）
```
主色：靛藍 #4f46e5
強調：青綠 #06b6d4
背景：淺灰 #f9fafb
狀態：綠/橙/紅
```
→ 「這是給工程師用的工具」

### 方向 3：台灣在地（Job Frog / CakeResume 路線）
```
主色：翠綠 #059669
強調：橙 #f97316
背景：暖白 #fefce8
狀態：綠/橙/紅
```
→ 「找工作不用這麼累」

### 方向 4：極簡資訊（Finviz / Vercel 路線）
```
主色：石墨 #374151
強調：藍 #3b82f6
背景：純白 #ffffff
狀態：綠/橙/紅
```
→ 「不廢話，直接看數據」

---

## 建議流程

1. 先到 **Realtime Colors** (realtimecolors.com) 試四個方向的色值
2. 確定方向後用 **TweakCN** (tweakcn.com) 生成完整 shadcn 主題
3. 圖表配色用 **Learn UI Data Color Picker** 生成
4. 最終用 **Adobe Color** 檢查 WCAG 對比度
