import { createServerFn } from '@tanstack/react-start'
import type { Job } from './types'

type D1Database = {
  prepare: (sql: string) => {
    bind: (...values: unknown[]) => {
      all: <T>() => Promise<{ results: T[] }>
    }
    all: <T>() => Promise<{ results: T[] }>
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
  })

export const getJobs = createServerFn().handler(async (): Promise<Job[]> => {
  const db = await getD1()
  if (db) {
    try {
      const { results } = await db
        .prepare(
          'SELECT id, stock_id, company_name, title, location, date_posted, job_url, source, salary_min, salary_max, job_type, click_count FROM jobs ORDER BY date_posted DESC LIMIT 200',
        )
        .all<Job>()
      return results
    } catch {
      // D1 table may not exist; fall through
    }
  }
  // Dev mode fallback: no JSON import needed, D1 handles production
  return []
})
