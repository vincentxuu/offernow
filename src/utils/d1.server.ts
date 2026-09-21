// Server-only：直接存取 Cloudflare D1，不可被 client bundle 引用
export type D1Database = {
  prepare: (sql: string) => {
    bind: (...values: unknown[]) => {
      all: <T>() => Promise<{ results: T[] }>
      first: <T>() => Promise<T | null>
    }
    all: <T>() => Promise<{ results: T[] }>
    first: <T>() => Promise<T | null>
  }
}

export async function getD1(): Promise<D1Database | null> {
  try {
    const mod: Record<string, unknown> = await import('cloudflare:workers')
    const env = mod.env as Record<string, unknown> | undefined
    if (env?.DB) return env.DB as D1Database
  } catch {
    // Not in Cloudflare Workers environment
  }
  return null
}

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
