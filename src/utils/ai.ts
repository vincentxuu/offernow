import OpenAI from 'openai'

// --- Provider Config ---

export type AIProvider = 'openrouter' | 'opencode'

interface ProviderConfig {
  baseURL: string
  envKey: string
  defaultModel: string
}

const PROVIDER_CONFIG: Record<AIProvider, ProviderConfig> = {
  openrouter: {
    baseURL: 'https://openrouter.ai/api/v1',
    envKey: 'OPENROUTER_API_KEY',
    defaultModel: 'google/gemini-2.5-flash',
  },
  opencode: {
    baseURL: 'https://opencode.ai/zen/v1',
    envKey: 'OPENCODE_API_KEY',
    defaultModel: 'deepseek-v4-flash',
  },
}

// --- Client Management ---

let _client: OpenAI | null = null
let _provider: AIProvider | null = null
let _model: string | null = null

export function getAIClient(): {
  client: OpenAI
  provider: AIProvider
  model: string
} {
  if (_client && _provider && _model)
    return { client: _client, provider: _provider, model: _model }

  // 環境變數覆蓋：AI_MODEL=xxx 可指定模型
  const envModel = process.env.AI_MODEL

  for (const [name, config] of Object.entries(PROVIDER_CONFIG) as [
    AIProvider,
    ProviderConfig,
  ][]) {
    const apiKey = process.env[config.envKey]
    if (apiKey) {
      _client = new OpenAI({ apiKey, baseURL: config.baseURL })
      _provider = name
      _model = envModel || config.defaultModel
      return { client: _client, provider: _provider, model: _model }
    }
  }

  throw new Error(
    'No AI provider configured. Set OPENROUTER_API_KEY or OPENCODE_API_KEY.',
  )
}

// --- Retry with Exponential Backoff ---

const RETRYABLE_STATUS = new Set([429, 500, 502, 503, 504])
const MAX_RETRIES = 2
const BASE_DELAY_MS = 2000

async function withRetry<T>(fn: () => Promise<T>, label: string): Promise<T> {
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      return await fn()
    } catch (error: unknown) {
      const status = (error as { status?: number })?.status
      const isRetryable = status ? RETRYABLE_STATUS.has(status) : false

      if (!isRetryable || attempt === MAX_RETRIES) {
        throw error
      }

      // Exponential backoff: 2s, 4s
      const delay = BASE_DELAY_MS * 2 ** attempt
      // 429 的 retry-after header
      const retryAfter = (
        error as { headers?: { get?: (k: string) => string | null } }
      )?.headers?.get?.('retry-after')
      const waitMs = retryAfter
        ? Math.min(parseInt(retryAfter, 10) * 1000, 30000)
        : delay

      console.warn(
        `[AI] ${label} attempt ${attempt + 1} failed (${status}), retrying in ${waitMs}ms...`,
      )
      await new Promise((r) => setTimeout(r, waitMs))
    }
  }
  throw new Error('unreachable')
}

// --- Output Parsing (統一不同模型的回傳格式) ---

function extractText(response: OpenAI.Chat.Completions.ChatCompletion): string {
  const content = response.choices?.[0]?.message?.content
  if (!content) return ''

  // 清理不同模型的格式差異
  let text = content.trim()

  // 有些模型會用引號包住
  if (
    (text.startsWith('"') && text.endsWith('"')) ||
    (text.startsWith('「') && text.endsWith('」'))
  ) {
    text = text.slice(1, -1).trim()
  }

  // 有些模型會加前綴如「答：」「回答：」
  text = text.replace(/^(答[：:]|回答[：:]|以下是|結果[：:])\s*/u, '')

  // 有些模型會加 markdown
  text = text.replace(/^\*\*(.+)\*\*$/, '$1')

  // 限制長度（30 字要求，但容許到 60 字）
  if (text.length > 60) {
    const cutoff = text.lastIndexOf('，', 60)
    text = cutoff > 20 ? text.slice(0, cutoff) : text.slice(0, 60)
  }

  return text
}

// --- Public API ---

export async function generateInsight(companyData: {
  name: string
  stock_id: string
  industry: string
  salary_median_k: number | null
  salary_median_change_pct: number | null
  eps: number | null
  employee_count: number | null
  job_count_104: number
}): Promise<string> {
  const { client, model } = getAIClient()

  const salaryWan = companyData.salary_median_k
    ? (companyData.salary_median_k / 10).toFixed(1)
    : '未揭露'
  const changePct =
    companyData.salary_median_change_pct !== null
      ? `${companyData.salary_median_change_pct > 0 ? '+' : ''}${companyData.salary_median_change_pct.toFixed(1)}%`
      : '未知'

  const prompt = `公司：${companyData.name}（${companyData.stock_id}）
產業：${companyData.industry}
非主管薪資中位數：${salaryWan} 萬（年變動 ${changePct}）
EPS：${companyData.eps ?? '未揭露'}
員工數：${companyData.employee_count?.toLocaleString() ?? '未揭露'}
104 職缺數：${companyData.job_count_104 || 0}

用一句話（30 字內繁體中文）總結這家公司對求職者的吸引力。只說客觀事實，不做主觀評價。不要用「值得」「推薦」等詞。直接輸出那句話，不要加引號或前綴。`

  const response = await withRetry(
    () =>
      client.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 100,
        temperature: 0.3,
      }),
    `insight:${companyData.stock_id}`,
  )

  return extractText(response)
}

export async function generateInsightsBatch(
  companies: Parameters<typeof generateInsight>[0][],
  options?: {
    batchSize?: number
    onProgress?: (done: number, total: number) => void
  },
): Promise<Map<string, string>> {
  const batchSize = options?.batchSize ?? 5
  const results = new Map<string, string>()

  for (let i = 0; i < companies.length; i += batchSize) {
    const batch = companies.slice(i, i + batchSize)
    const settled = await Promise.allSettled(
      batch.map((c) =>
        generateInsight(c).then((insight) => ({
          stock_id: c.stock_id,
          insight,
        })),
      ),
    )

    for (const result of settled) {
      if (result.status === 'fulfilled') {
        results.set(result.value.stock_id, result.value.insight)
      }
    }

    const done = Math.min(i + batchSize, companies.length)
    options?.onProgress?.(done, companies.length)

    // 批次間間隔，避免 rate limit
    if (i + batchSize < companies.length) {
      await new Promise((r) => setTimeout(r, 1500))
    }
  }

  return results
}
