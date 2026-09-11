import { createServerFn } from '@tanstack/react-start'
import type { AttractivenessScore, Company } from './types'

function clamp(v: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, v))
}

function lerp(
  value: number,
  inLow: number,
  inHigh: number,
  outLow: number,
  outHigh: number,
): number {
  if (inHigh === inLow) return (outLow + outHigh) / 2
  return outLow + ((value - inLow) / (inHigh - inLow)) * (outHigh - outLow)
}

export function calculateAttractivenessScore(c: Company): AttractivenessScore {
  // 1. Salary Competitiveness (30%)
  let salaryScore = 50
  if (
    c.salary_vs_industry_pct !== null &&
    c.salary_vs_industry_pct !== undefined
  ) {
    salaryScore = clamp(lerp(c.salary_vs_industry_pct, -50, 50, 0, 100))
  } else if (c.salary_median_k) {
    salaryScore = clamp(lerp(c.salary_median_k, 500, 2000, 20, 80))
  }
  const salaryDetail =
    c.salary_vs_industry_pct !== null && c.salary_vs_industry_pct !== undefined
      ? `同業${c.salary_vs_industry_pct > 0 ? '+' : ''}${c.salary_vs_industry_pct.toFixed(0)}%`
      : c.salary_median_k
        ? `中位數 ${(c.salary_median_k / 10).toFixed(0)} 萬`
        : '未揭露'

  // 2. Growth Momentum (20%)
  let growthScore = 50
  const revScore =
    c.revenue_yoy_pct !== null && c.revenue_yoy_pct !== undefined
      ? clamp(lerp(c.revenue_yoy_pct, -30, 30, 0, 100))
      : 50
  const salGrowthScore =
    c.salary_median_change_pct !== null &&
    c.salary_median_change_pct !== undefined
      ? clamp(lerp(c.salary_median_change_pct, -10, 20, 0, 100))
      : 50
  growthScore = revScore * 0.7 + salGrowthScore * 0.3
  const growthParts: string[] = []
  if (c.revenue_yoy_pct !== null && c.revenue_yoy_pct !== undefined)
    growthParts.push(
      `營收${c.revenue_yoy_pct > 0 ? '+' : ''}${c.revenue_yoy_pct.toFixed(1)}%`,
    )
  if (
    c.salary_median_change_pct !== null &&
    c.salary_median_change_pct !== undefined
  )
    growthParts.push(
      `薪資${c.salary_median_change_pct > 0 ? '+' : ''}${c.salary_median_change_pct.toFixed(1)}%`,
    )
  const growthDetail =
    growthParts.length > 0 ? growthParts.join('、') : '資料不足'

  // 3. Hiring Trend (20%)
  let hiringScore = 40
  const totalJobs = c.job_count_total ?? 0
  if (c.job_count_trend === 'expanding') {
    hiringScore = totalJobs >= 50 ? 95 : totalJobs >= 10 ? 85 : 80
  } else if (c.job_count_trend === 'shrinking') {
    hiringScore = totalJobs >= 10 ? 30 : 15
  } else if (totalJobs > 0) {
    hiringScore = totalJobs >= 50 ? 60 : totalJobs >= 10 ? 50 : 40
  } else {
    hiringScore = 20
  }
  const hiringDetail =
    totalJobs > 0
      ? `${totalJobs} 個職缺${c.job_count_trend === 'expanding' ? '（擴編中）' : c.job_count_trend === 'shrinking' ? '（縮編中）' : ''}`
      : '目前無職缺'

  // 4. Financial Health (20%)
  let financeScore = 50
  if (c.eps !== null && c.eps !== undefined) {
    financeScore =
      c.eps > 0
        ? clamp(lerp(c.eps, 0, 15, 40, 90))
        : clamp(lerp(c.eps, -5, 0, 10, 40))
  }
  if (c.market_cap && c.market_cap > 1000)
    financeScore = Math.min(100, financeScore + 10)
  const financeDetail =
    c.eps !== null
      ? `EPS ${c.eps} 元` +
        (c.market_cap
          ? `、市值 ${c.market_cap >= 10000 ? `${(c.market_cap / 10000).toFixed(1)} 兆` : `${c.market_cap.toFixed(0)} 億`}`
          : '')
      : '未揭露'

  // 5. Risk Flags (10%, deduction)
  const flagCount =
    (c.flag_low_salary === 1 ? 1 : 0) +
    (c.flag_eps_high_salary_low === 1 ? 1 : 0) +
    (c.flag_eps_up_salary_down === 1 ? 1 : 0)
  const riskScore = clamp(100 - flagCount * 33)
  const riskLabels: string[] = []
  if (c.flag_low_salary === 1) riskLabels.push('低薪')
  if (c.flag_eps_high_salary_low === 1) riskLabels.push('EPS高薪低')
  if (c.flag_eps_up_salary_down === 1) riskLabels.push('EPS漲薪減')
  const riskDetail =
    riskLabels.length > 0 ? riskLabels.join('、') : '無風險旗標'

  const overall = Math.round(
    salaryScore * 0.3 +
      growthScore * 0.2 +
      hiringScore * 0.2 +
      financeScore * 0.2 +
      riskScore * 0.1,
  )

  let grade: AttractivenessScore['grade'] = 'C'
  if (overall >= 80) grade = 'A'
  else if (overall >= 65) grade = 'B'
  else if (overall >= 50) grade = 'C'
  else if (overall >= 35) grade = 'D'
  else grade = 'F'

  return {
    overall,
    grade,
    dimensions: [
      {
        name: '薪資競爭力',
        icon: '💰',
        score: Math.round(salaryScore),
        detail: salaryDetail,
      },
      {
        name: '成長動能',
        icon: '📈',
        score: Math.round(growthScore),
        detail: growthDetail,
      },
      {
        name: '擴編趨勢',
        icon: '🏢',
        score: Math.round(hiringScore),
        detail: hiringDetail,
      },
      {
        name: '財務健康',
        icon: '⚖️',
        score: Math.round(financeScore),
        detail: financeDetail,
      },
      {
        name: '風險旗標',
        icon: '🚩',
        score: Math.round(riskScore),
        detail: riskDetail,
      },
    ],
  }
}

type D1Database = {
  prepare: (sql: string) => {
    bind: (...values: unknown[]) => {
      all: <T>() => Promise<{ results: T[] }>
      first: <T>() => Promise<T | null>
    }
    all: <T>() => Promise<{ results: T[] }>
    first: <T>() => Promise<T | null>
  }
}

async function getD1(): Promise<D1Database | null> {
  try {
    const mod: Record<string, unknown> = await import('cloudflare:workers')
    const env = mod.env as Record<string, unknown> | undefined
    if (env?.DB) return env.DB as D1Database
  } catch {
    // Not in Cloudflare Workers environment
  }
  return null
}

export const getCompanies = createServerFn().handler(
  async (): Promise<Company[]> => {
    const db = await getD1()
    if (db) {
      try {
        const { results } = await db
          .prepare(
            'SELECT * FROM company_profiles ORDER BY salary_median_k DESC NULLS LAST',
          )
          .all<Company>()
        return results
      } catch {
        // D1 table may not exist; fall through
      }
    }
    // Dev mode fallback: no JSON import, D1 handles production
    return []
  },
)

export const getCompanyByStockId = createServerFn()
  .validator((stockId: string) => stockId)
  .handler(async ({ data: stockId }): Promise<Company | null> => {
    const db = await getD1()
    if (db) {
      try {
        return db
          .prepare('SELECT * FROM company_profiles WHERE stock_id = ?')
          .bind(stockId)
          .first<Company>()
      } catch {
        // Fall through
      }
    }
    return null
  })

export type IndustryTrend = {
  industry: string
  total_jobs: number
  delta: number
  company_count: number
}

export const getIndustryTrends = createServerFn().handler(
  async (): Promise<IndustryTrend[]> => {
    const db = await getD1()
    if (db) {
      try {
        const { results } = await db
          .prepare(
            `SELECT industry,
                SUM(job_count_total) AS total_jobs,
                SUM(job_count_total) - SUM(job_count_prev_month) AS delta,
                COUNT(*) AS company_count
         FROM company_profiles
         WHERE industry IS NOT NULL
         GROUP BY industry
         ORDER BY delta DESC`,
          )
          .all<IndustryTrend>()
        return results
      } catch {
        // Fall through
      }
    }
    return []
  },
)

export const INDUSTRIES = [
  '全部',
  '半導體業',
  '電子零組件業',
  '金融保險業',
  '光電業',
  '電腦及週邊設備業',
  '生技醫療業',
  '通信網路業',
  '資訊服務業',
  '電機機械',
  '建材營造',
  '鋼鐵工業',
] as const
