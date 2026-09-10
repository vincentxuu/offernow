#!/usr/bin/env npx tsx
/**
 * 用 OpenRouter 或 OpenCode 為 TOP 100 公司生成 AI 洞察。
 *
 * 用法：
 *   OPENROUTER_API_KEY=sk-... npx tsx scripts/generate-insights.ts
 *   # 或
 *   OPENCODE_API_KEY=sk-... npx tsx scripts/generate-insights.ts
 */

import { readFileSync, writeFileSync } from 'fs'
import { join } from 'path'
import OpenAI from 'openai'

const DATA_DIR = join(import.meta.dirname, 'data')
const COMPANIES_FILE = join(DATA_DIR, 'companies_with_salary.json')
const INSIGHTS_FILE = join(DATA_DIR, 'insights.json')
const TOP_N = 100
const BATCH_SIZE = 5

type Company = {
  stock_id: string
  name: string
  short_name: string
  industry: string
  salary_median_k: number | null
  salary_median_change_pct: number | null
  eps: number | null
  employee_count: number | null
  job_count_104: number
  ai_insight?: string
}

// Resolve provider
const providers = [
  { name: 'openrouter', baseURL: 'https://openrouter.ai/api/v1', key: process.env.OPENROUTER_API_KEY, model: 'google/gemini-2.5-flash' },
  { name: 'opencode', baseURL: 'https://opencode.ai/zen/v1', key: process.env.OPENCODE_API_KEY, model: 'deepseek-v4-flash' },
]

const provider = providers.find(p => p.key)
if (!provider) {
  console.error('請設定 OPENROUTER_API_KEY 或 OPENCODE_API_KEY')
  process.exit(1)
}

console.log(`Using provider: ${provider.name} (${provider.model})`)

const client = new OpenAI({ apiKey: provider.key, baseURL: provider.baseURL })

async function generateInsight(c: Company): Promise<string> {
  const salaryWan = c.salary_median_k ? (c.salary_median_k / 10).toFixed(1) : '未揭露'
  const changePct = c.salary_median_change_pct !== null
    ? `${c.salary_median_change_pct > 0 ? '+' : ''}${c.salary_median_change_pct.toFixed(1)}%`
    : '未知'

  const response = await client.chat.completions.create({
    model: provider!.model,
    messages: [{
      role: 'user',
      content: `公司：${c.name}（${c.stock_id}）
產業：${c.industry}
非主管薪資中位數：${salaryWan} 萬（年變動 ${changePct}）
EPS：${c.eps ?? '未揭露'}
員工數：${c.employee_count?.toLocaleString() ?? '未揭露'}
104 職缺數：${c.job_count_104 || 0}

用一句話（30 字內繁體中文）總結這家公司對求職者的吸引力。只說客觀事實，不做主觀評價。不要用「值得」「推薦」等詞。直接輸出那句話，不要加引號或前綴。`,
    }],
    max_tokens: 100,
    temperature: 0.3,
  })

  return response.choices[0]?.message?.content?.trim() ?? ''
}

async function main() {
  console.log('='.repeat(60))
  console.log('OfferNow — Generating AI Insights')
  console.log('='.repeat(60))

  const companies: Company[] = JSON.parse(readFileSync(COMPANIES_FILE, 'utf-8'))

  // TOP N by salary median
  const top = companies
    .filter(c => c.salary_median_k !== null)
    .sort((a, b) => (b.salary_median_k ?? 0) - (a.salary_median_k ?? 0))
    .slice(0, TOP_N)

  console.log(`Generating insights for TOP ${top.length} companies...\n`)

  const insights: Record<string, string> = {}

  for (let i = 0; i < top.length; i += BATCH_SIZE) {
    const batch = top.slice(i, i + BATCH_SIZE)
    const results = await Promise.allSettled(batch.map(c => generateInsight(c)))

    for (let j = 0; j < batch.length; j++) {
      const result = results[j]
      const company = batch[j]
      if (result.status === 'fulfilled' && result.value) {
        insights[company.stock_id] = result.value
        console.log(`  ✓ ${company.short_name || company.name} (${company.stock_id}): ${result.value}`)
      } else {
        const reason = result.status === 'rejected' ? result.reason : 'empty'
        console.log(`  ✗ ${company.short_name || company.name} (${company.stock_id}): ${reason}`)
      }
    }

    if (i + BATCH_SIZE < top.length) {
      await new Promise(r => setTimeout(r, 1000))
    }
  }

  // Save insights backup
  writeFileSync(INSIGHTS_FILE, JSON.stringify(insights, null, 2), 'utf-8')
  console.log(`\nSaved ${Object.keys(insights).length} insights to ${INSIGHTS_FILE}`)

  // Merge into companies
  let updated = 0
  for (const company of companies) {
    if (insights[company.stock_id]) {
      company.ai_insight = insights[company.stock_id]
      updated++
    }
  }

  writeFileSync(COMPANIES_FILE, JSON.stringify(companies, null, 2), 'utf-8')
  console.log(`Updated ${updated} companies in ${COMPANIES_FILE}`)
  console.log('\nDone! Run `python3 scripts/db/seed.py && pnpm wrangler d1 execute offernow-db --local --file scripts/db/seed.sql` to update D1.')
}

main().catch(console.error)
