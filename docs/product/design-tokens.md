# OfferNow Design Tokens

> 基於 Happy Hues Palette 5，已在 prototype 中驗證
> Prototype: https://claude.ai/code/artifact/82a9d922-68fe-4117-9392-7d8c3df0748d

## Color Tokens

### Light Mode

| Token | Hex | 用途 |
|-------|-----|------|
| `--bg` | `#f2f7f5` | 頁面背景 |
| `--bg-surface` | `#ffffff` | 卡片、表格背景 |
| `--bg-elevated` | `#e8f0ed` | 指標區塊、hover 狀態 |
| `--text-heading` | `#00473e` | 標題、重要文字 |
| `--text-body` | `#475d5b` | 內文 |
| `--text-muted` | `#7a928d` | 輔助文字、標籤 |
| `--accent` | `#faae2b` | CTA 按鈕、連結、重點 |
| `--accent-hover` | `#e89b1c` | CTA hover |
| `--accent-soft` | `rgba(250,174,43,0.12)` | AI 洞察背景、accent 淡色 |
| `--pink` | `#f582ae` | 裝飾、點綴 |
| `--pink-soft` | `rgba(245,130,174,0.12)` | 粉色淡底 |
| `--green-positive` | `#059669` | 正向指標（擴編、成長） |
| `--green-soft` | `rgba(5,150,105,0.1)` | 正向 badge 背景 |
| `--red-negative` | `#dc2626` | 負向指標（縮編、下降） |
| `--red-soft` | `rgba(220,38,38,0.1)` | 負向 badge 背景 |
| `--border` | `#d8e4e0` | 邊框、分隔線 |

### Dark Mode

| Token | Hex | 變化 |
|-------|-----|------|
| `--bg` | `#0d1f1b` | 深墨綠 |
| `--bg-surface` | `#142b26` | 稍亮墨綠 |
| `--bg-elevated` | `#1a3630` | 指標區塊 |
| `--text-heading` | `#e8f0ed` | 淺灰綠 |
| `--text-body` | `#9fb3af` | 中灰綠 |
| `--text-muted` | `#6b8580` | 暗灰綠 |
| `--accent` | `#faae2b` | 不變 |
| `--accent-hover` | `#ffc45c` | 稍亮 |
| `--green-positive` | `#34d399` | 亮綠 |
| `--red-negative` | `#f87171` | 亮紅 |
| `--border` | `#1f3d36` | 深邊框 |

## Typography

| 角色 | 字型 | 用途 |
|------|------|------|
| Display / Heading | Plus Jakarta Sans 700-800 | 標題、數字、品牌名 |
| Body | Inter 400-600 | 內文、標籤、按鈕 |

## Spacing & Layout

| Token | 值 | 用途 |
|-------|---|------|
| `--radius` | `12px` | 卡片、大元件 |
| `--radius-sm` | `8px` | 按鈕、badge、小元件 |
| `--shadow` | `0 1px 3px rgba(0,71,62,0.06)` | 卡片預設 |
| `--shadow-lg` | `0 4px 12px rgba(0,71,62,0.08)` | 卡片 hover |

## Brand

- **名稱**：OfferNow
- **品牌色**：深墨綠 `#00473e` + 橘黃 `#faae2b`
- **調性**：專業但不冷、有辨識度但不花俏、資料密集但不擁擠
