import { createServerFn } from '@tanstack/react-start'
import type { Job } from './types'

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

export const getJobRedirectUrl = createServerFn()
  .validator((data: string) => data)
  .handler(async ({ data: jobId }): Promise<string | null> => {
    return getJobRedirectUrlById(jobId)
  })

export async function getJobRedirectUrlById(
  jobId: string,
): Promise<string | null> {
  const db = await getD1()
  if (!db) return null
  try {
    const id = parseInt(jobId, 10)
    if (Number.isNaN(id)) return null
    await db
      .prepare('UPDATE jobs SET click_count = click_count + 1 WHERE id = ?')
      .bind(id)
      .all()
    const { results } = await db
      .prepare('SELECT job_url FROM jobs WHERE id = ?')
      .bind(id)
      .all<{ job_url: string }>()
    return results[0]?.job_url ?? null
  } catch {
    return null
  }
}

export type JobFilters = {
  source?: string
  search?: string
  cities?: string[]
  districts?: string[]
  jobType?: string
  industry?: string
  market?: string
  salaryMin?: number
  dateRange?: string
  expanding?: boolean
  offset?: number
  limit?: number
}

export type JobsPage = {
  jobs: Job[]
  total: number
  offset: number
  hasMore: boolean
}

export type FilterCounts = {
  sources: { name: string; count: number }[]
  total: number
}

const CITY_ALIASES: Record<string, string[]> = {
  台北: ['台北', 'Taipei', 'TPE'],
  新北: ['新北', 'New Taipei', 'TPQ', '三重', '板橋', '中和', '永和', '土城', '汐止', '林口', '淡水', '蘆洲', '樹林'],
  新竹: ['新竹', 'Hsinchu', 'Zhubei', '竹北', '竹東'],
  桃園: ['桃園', 'Taoyuan', '中壢', '龜山', '楊梅'],
  苗栗: ['苗栗', 'Miaoli', '竹南', '頭份'],
  台中: ['台中', 'Taichung'],
  台南: ['台南', 'Tainan', '善化', '新營'],
  高雄: ['高雄', 'Kaohsiung', '楠梓', '前鎮'],
}

function buildWhere(filters: JobFilters): { where: string; params: unknown[] } {
  const conditions: string[] = []
  const params: unknown[] = []

  if (filters.source && filters.source !== '全部') {
    conditions.push('j.source = ?')
    params.push(filters.source)
  }

  if (filters.search) {
    const q = `%${filters.search}%`
    conditions.push('(j.title LIKE ? OR j.company_name LIKE ? OR j.location LIKE ?)')
    params.push(q, q, q)
  }

  const locationGroups = [filters.cities, filters.districts]
  for (const values of locationGroups) {
    if (!values || values.length === 0) continue
    const aliases = values.flatMap((v) => CITY_ALIASES[v] || [v])
    const likeClauses = aliases.map(() => 'j.location LIKE ?')
    conditions.push(`(${likeClauses.join(' OR ')})`)
    for (const a of aliases) params.push(`%${a}%`)
  }

  if (filters.jobType === '全球遠端') {
    conditions.push("j.job_type = 'global_remote'")
  } else if (filters.jobType === '遠端/混合') {
    conditions.push("(j.job_type IN ('remote', 'global_remote') OR j.location LIKE '%remote%' OR j.location LIKE '%遠端%')")
  }

  if (filters.industry && filters.industry !== '全部') {
    conditions.push('j.stock_id IN (SELECT stock_id FROM company_profiles WHERE industry LIKE ?)')
    params.push(`%${filters.industry.replace('業', '')}%`)
  }

  if (filters.market && filters.market !== '全部') {
    conditions.push('j.stock_id IN (SELECT stock_id FROM company_profiles WHERE market = ?)')
    params.push(filters.market)
  }

  if (filters.salaryMin && filters.salaryMin > 0) {
    conditions.push('j.salary_min >= ?')
    params.push(filters.salaryMin)
  }

  if (filters.dateRange && filters.dateRange !== '全部') {
    const daysMap: Record<string, number> = { '3天': 3, '7天': 7, '14天': 14, '30天': 30 }
    const days = daysMap[filters.dateRange]
    if (days) {
      conditions.push("j.date_posted >= date('now', ?)")
      params.push(`-${days} days`)
    }
  }

  if (filters.expanding) {
    conditions.push("j.stock_id IN (SELECT stock_id FROM company_profiles WHERE job_count_trend = 'expanding')")
  }

  const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : ''
  return { where, params }
}

export const getFilterCounts = createServerFn().handler(
  async (): Promise<FilterCounts> => {
    const db = await getD1()
    if (!db) return { sources: [], total: 0 }
    try {
      const { results } = await db
        .prepare('SELECT source as name, COUNT(*) as count FROM jobs GROUP BY source ORDER BY count DESC')
        .all<{ name: string; count: number }>()
      const total = results.reduce((s, r) => s + r.count, 0)
      return { sources: results, total }
    } catch {
      return { sources: [], total: 0 }
    }
  },
)

export const getJobsPage = createServerFn()
  .validator((data: JobFilters) => data)
  .handler(async ({ data: filters }): Promise<JobsPage> => {
    const db = await getD1()
    if (!db) return { jobs: [], total: 0, offset: 0, hasMore: false }

    const limit = Math.min(filters.limit ?? 50, 100)
    const offset = filters.offset ?? 0
    const { where, params } = buildWhere(filters)

    try {
      const countRow = await db
        .prepare(`SELECT COUNT(*) as cnt FROM jobs j ${where}`)
        .bind(...params)
        .first<{ cnt: number }>()
      const total = countRow?.cnt ?? 0

      const { results } = await db
        .prepare(
          `SELECT j.id, j.stock_id, j.company_name, j.title, j.location, j.date_posted, j.job_url, j.source, j.salary_min, j.salary_max, j.job_type, j.click_count
           FROM (
             SELECT *, ROW_NUMBER() OVER (PARTITION BY source ORDER BY date_posted DESC, id DESC) as rn
             FROM jobs j ${where}
           ) j
           ORDER BY rn, date_posted DESC, source
           LIMIT ? OFFSET ?`,
        )
        .bind(...params, limit, offset)
        .all<Job>()

      return { jobs: results, total, offset, hasMore: offset + results.length < total }
    } catch {
      return { jobs: [], total: 0, offset: 0, hasMore: false }
    }
  })
