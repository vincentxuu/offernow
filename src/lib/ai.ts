import OpenAI from 'openai'

export type AIProvider = 'openrouter' | 'opencode'

const PROVIDER_CONFIG: Record<AIProvider, { baseURL: string; envKey: string; defaultModel: string }> = {
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

let _client: OpenAI | null = null
let _provider: AIProvider | null = null

function getClient(): { client: OpenAI; provider: AIProvider } {
  if (_client && _provider) return { client: _client, provider: _provider }

  for (const [name, config] of Object.entries(PROVIDER_CONFIG) as [AIProvider, typeof PROVIDER_CONFIG[AIProvider]][]) {
    const apiKey = process.env[config.envKey]
    if (apiKey) {
      _client = new OpenAI({ apiKey, baseURL: config.baseURL })
      _provider = name
      return { client: _client, provider: _provider }
    }
  }

  throw new Error('No AI provider configured. Set OPENROUTER_API_KEY or OPENCODE_API_KEY.')
}

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
  const { client, provider } = getClient()
  const config = PROVIDER_CONFIG[provider]

  const salaryWan = companyData.salary_median_k ? (companyData.salary_median_k / 10).toFixed(1) : '未揭露'
  const changePct = companyData.salary_median_change_pct !== null ? `${companyData.salary_median_change_pct > 0 ? '+' : ''}${companyData.salary_median_change_pct.toFixed(1)}%` : '未知'

  const prompt = `公司：${companyData.name}（${companyData.stock_id}）
產業：${companyData.industry}
非主管薪資中位數：${salaryWan} 萬（年變動 ${changePct}）
EPS：${companyData.eps ?? '未揭露'}
員工數：${companyData.employee_count?.toLocaleString() ?? '未揭露'}
104 職缺數：${companyData.job_count_104 || 0}

用一句話（30 字內繁體中文）總結這家公司對求職者的吸引力。只說客觀事實，不做主觀評價。不要用「值得」「推薦」等詞。`

  const response = await client.chat.completions.create({
    model: config.defaultModel,
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 100,
    temperature: 0.3,
  })

  return response.choices[0]?.message?.content?.trim() ?? ''
}

export async function generateInsightsBatch(companies: Parameters<typeof generateInsight>[0][], batchSize = 5): Promise<Map<string, string>> {
  const results = new Map<string, string>()

  for (let i = 0; i < companies.length; i += batchSize) {
    const batch = companies.slice(i, i + batchSize)
    const promises = batch.map(async (c) => {
      try {
        const insight = await generateInsight(c)
        results.set(c.stock_id, insight)
      } catch (e) {
        console.error(`Failed for ${c.stock_id} ${c.name}:`, e)
      }
    })
    await Promise.all(promises)

    if (i + batchSize < companies.length) {
      await new Promise((r) => setTimeout(r, 1000))
    }

    console.log(`  Progress: ${Math.min(i + batchSize, companies.length)}/${companies.length}`)
  }

  return results
}
