export type Company = {
  stock_id: string
  name: string
  short_name: string
  industry: string
  market: string
  chairman: string
  gm: string
  address: string
  phone: string
  established: string
  listed_date: string
  capital: string
  tax_id: string
  salary_median_k: number | null
  salary_mean_k: number | null
  salary_median_change_pct: number | null
  employee_count: number | null
  eps: number | null
  salary_year: number | null
  job_count_104: number | null
  encoded_cust_no_104: string | null
  job_count_linkedin: number | null
  ai_insight: string | null
  revenue_yoy_pct: number | null
  market_cap: number | null
  salary_vs_industry_pct: number | null
  industry_salary_avg_k: number | null
  salary_male_median_k: number | null
  salary_female_median_k: number | null
  flag_low_salary: number | null
  flag_eps_high_salary_low: number | null
  flag_eps_up_salary_down: number | null
}

export type Job = {
  stock_id: string
  company_name: string
  title: string
  location: string
  date_posted: string
  job_url: string
  source: string
  description: string
  salary_min: number | null
  salary_max: number | null
  job_type: string
}
