import { createServerFn } from '@tanstack/react-start'
import type { Company } from './types'

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

export const getCompanies = createServerFn().handler(async (): Promise<Company[]> => {
  const db = await getD1()
  if (db) {
    try {
      const { results } = await db.prepare(
        'SELECT * FROM company_profiles ORDER BY salary_median_k DESC NULLS LAST'
      ).all<Company>()
      return results
    } catch {
      // D1 table may not exist; fall through
    }
  }
  // Dev mode fallback: no JSON import, D1 handles production
  return []
})

export const getCompanyByStockId = createServerFn()
  .validator((stockId: string) => stockId)
  .handler(async ({ data: stockId }): Promise<Company | null> => {
    const db = await getD1()
    if (db) {
      try {
        return db.prepare(
          'SELECT * FROM company_profiles WHERE stock_id = ?'
        ).bind(stockId).first<Company>()
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

export const getIndustryTrends = createServerFn().handler(async (): Promise<IndustryTrend[]> => {
  const db = await getD1()
  if (db) {
    try {
      const { results } = await db.prepare(
        `SELECT industry,
                SUM(job_count_total) AS total_jobs,
                SUM(job_count_total) - SUM(job_count_prev_month) AS delta,
                COUNT(*) AS company_count
         FROM company_profiles
         WHERE industry IS NOT NULL
         GROUP BY industry
         ORDER BY delta DESC`
      ).all<IndustryTrend>()
      return results
    } catch {
      // Fall through
    }
  }
  return []
})

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
