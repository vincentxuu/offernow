import { createServerFn } from '@tanstack/react-start'
import type { Company } from './types'

// Server function to load company data
// Currently reads from JSON; swap to D1 query when bindings are ready
export const getCompanies = createServerFn().handler(async (): Promise<Company[]> => {
  const { default: data } = await import('../../scripts/data/companies_with_salary.json')
  return data as Company[]
})

export const getCompanyByStockId = createServerFn()
  .validator((stockId: string) => stockId)
  .handler(async ({ data: stockId }): Promise<Company | null> => {
    const { default: companies } = await import('../../scripts/data/companies_with_salary.json')
    const all = companies as Company[]
    return all.find((c) => c.stock_id === stockId) ?? null
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
