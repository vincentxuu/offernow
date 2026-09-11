<div align="center">

# OfferNow

**Job aggregator for Taiwan's listed companies — connecting TWSE, MOPS, and 104 in one place.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-early_preview-orange.svg)

[Quick start](#quick-start) · [Features](#features-at-a-glance) · [Data pipeline](#data-pipeline) · [MCP Server](#mcp-server) · [Deploy](#deploy)

[English](README.md) · [繁體中文](README.zh-TW.md)

</div>

> [!IMPORTANT]
> OfferNow is an unofficial open-source personal project for educational and research purposes only. It is not authorized by 104 Job Bank or LinkedIn. Usage may violate their Terms of Service — assess legal and compliance risks on your own.

## Why?

Looking for jobs at Taiwan's listed companies means checking three separate places:

- **TWSE / TPEx** — company fundamentals, industry classification, market cap, revenue
- **MOPS (Market Observation Post System)** — non-supervisory full-time employee median salary (updated annually in June)
- **104 / LinkedIn / company career pages** — job postings

OfferNow connects these three layers of public data into one platform, so you can instantly see **how much a company pays, whether it's expanding, and how healthy its finances are**.

## Features at a glance

| Feature | Description |
| --- | --- |
| **1,984 company profiles** | 1,094 listed + 890 OTC, with industry, market cap, revenue, headcount |
| **Salary rankings** | MOPS non-supervisory median / mean salary, including gender breakdown (for companies with capital over NT$10B) |
| **Job aggregation** | 104 + LinkedIn + remote jobs, 3,370+ listings |
| **Company attractiveness score** | Five-dimension structured scoring (A–F): salary competitiveness, growth momentum, hiring trend, financial health, risk flags |
| **Industry trends** | Job count delta by industry, expanding / shrinking signals |
| **Salary × jobs cross-reference** | "Hiring only" filter, "Growing & hiring" badge |
| **Click tracking** | `/go/{id}` click count + 302 redirect, laying groundwork for future CPC monetization |
| **JSON-LD SEO** | `JobPosting` + `Organization` structured data for Google for Jobs |
| **MCP Server** | 6 tools for direct Claude Code integration |

## Architecture

```text
Data sources                Pipeline                     Frontend + Services
────────────               ─────────                    ───────────────────
TWSE OpenAPI ─┐
TPEx OpenAPI ─┤
MOPS salary  ─┼── Python crawlers ──→ JSON ──→ seed SQL ──→ Cloudflare D1
104 API      ─┤       │                                        │
LinkedIn     ─┘       │                                        ▼
                      │                                 TanStack Start (React)
                      ▼                                 Cloudflare Workers
               Snapshot + trend                         Tailwind CSS
               calculation                                    │
                                                              ▼
MCP Server ◄──── Claude Code                           offernow.workers.dev
(6 tools)         direct query
```

## Quick start

**Requirements:** Node.js 22+, pnpm, [uv](https://docs.astral.sh/uv/) (for Python crawlers)

```bash
git clone https://github.com/vincentxuu/offernow.git
cd offernow
pnpm install
pnpm dev
```

Dev server starts at `http://localhost:3000`.

### Data refresh (one command)

```bash
./scripts/refresh-data.sh              # Crawl → snapshot → UPSERT D1
./scripts/refresh-data.sh --skip-fetch  # Skip crawling, just update D1
./scripts/refresh-data.sh --local       # Apply to local D1 (development)
```

## Data pipeline

### Crawlers

| Script | Source | Description |
| --- | --- | --- |
| `fetch-data/fetch.py` | 104 Job Bank | Public JSON API, keyword search + region filter |
| `fetch-data/fetch_linkedin.py` | LinkedIn | HTML parsing of public job pages |
| `fetch-data/fetch_104_company_ids.py` | 104 company list | Build stock_id ↔ encodedCustNo mapping |
| `scripts/fetch-companies.py` | TWSE / TPEx | Company fundamentals + industry classification |
| `scripts/fetch-mops-full.py` | MOPS | Employee salary disclosure (31 fields) |

### Processing

| Script | Description |
| --- | --- |
| `scripts/db/seed-jobs.py` | Merge job JSONs → UPSERT SQL (preserves click_count) |
| `scripts/snapshot-job-counts.py` | Monthly snapshot + expanding/shrinking trend calculation |
| `scripts/generate-insights.ts` | LLM-generated company AI insights (requires API key) |

### Data linking chain

```
104 encodedCustNo → exchangeId (stock ID) → TWSE OpenAPI → MOPS salary
```

Stock ID is the key linking all data sources. Current 104 mapping coverage: 59% (1,177 / 1,985).

## MCP Server

Let Claude Code query OfferNow data directly — no browser needed.

| Tool | Description |
| --- | --- |
| `search_companies` | Search by name / industry / market, with salary and market cap thresholds |
| `get_company` | Full company profile by stock ID |
| `get_top_salaries` | Salary median ranking with industry filter |
| `get_industry_trends` | Industry-level aggregation: company count, job count, average salary |
| `search_jobs` | Search jobs by keyword / company / location |
| `list_local_data` | Data file status check |

**Install:**

```bash
claude mcp add -s user offernow -- bash -c "cd /path/to/offernow/fetch-data && uv run mcp_server.py"
```

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | TanStack Start (React) + TanStack Router + TanStack Query |
| Styling | Tailwind CSS v4 |
| Database | Cloudflare D1 (SQLite) |
| Hosting | Cloudflare Workers |
| Crawlers | Python + requests + BeautifulSoup |
| MCP | FastMCP (Python) |

## Deploy

```bash
pnpm run deploy    # build + wrangler deploy
```

Deploys to Cloudflare Workers. D1 database connects automatically via Worker binding.

### D1 schema initialization

```bash
wrangler d1 execute offernow-db --remote --file=scripts/db/schema.sql
wrangler d1 execute offernow-db --remote --file=scripts/db/seed.sql
wrangler d1 execute offernow-db --remote --file=scripts/db/seed-jobs.sql
```

## Data sources

| Source | Content | Update frequency |
| --- | --- | --- |
| [TWSE OpenAPI](https://openapi.twse.com.tw/) | Listed company fundamentals, stock prices, revenue | Real-time |
| [TPEx](https://www.tpex.org.tw/) | OTC company fundamentals, stock prices, revenue | Real-time |
| [MOPS](https://mopsov.twse.com.tw/) | Employee salary disclosure (median / mean / gender) | Annually in June |
| [104 Job Bank](https://www.104.com.tw/) | Job listings, company info, salary rankings | Real-time |
| [LinkedIn](https://www.linkedin.com/jobs/) | Job listings | Real-time |

## Contributing

Use [GitHub Issues](https://github.com/vincentxuu/offernow/issues) to report bugs or suggest features. Please open an issue for discussion before submitting a pull request.

## Disclaimer

- This tool is not authorized by 104 Job Bank or LinkedIn. Usage may violate their Terms of Service — assess legal and compliance risks on your own.
- All analysis results are for reference only. No guarantee is made regarding timeliness, completeness, or accuracy.
- Users agree to bear all consequences of using this tool. The author and contributors assume no liability for any losses or legal issues.

## License

MIT License
