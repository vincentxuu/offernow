-- OfferNow D1 Schema
-- Denormalized company_profiles table for fast reads

DROP TABLE IF EXISTS company_profiles;

CREATE TABLE company_profiles (
  stock_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  short_name TEXT,
  industry TEXT,
  market TEXT NOT NULL,  -- 'listed' or 'otc'

  -- Company basics (TWSE/TPEx)
  chairman TEXT,
  gm TEXT,
  address TEXT,
  phone TEXT,
  established TEXT,
  listed_date TEXT,
  capital TEXT,
  tax_id TEXT,
  shares_outstanding TEXT,

  -- Salary (MOPS, annual update)
  salary_median_k INTEGER,
  salary_mean_k INTEGER,
  salary_median_prev_k INTEGER,
  salary_mean_prev_k INTEGER,
  salary_median_change_pct REAL,
  salary_mean_change_pct REAL,
  employee_count INTEGER,
  eps REAL,
  salary_year INTEGER,

  -- Gender salary (MOPS, 資本額100億以上)
  salary_male_median_k INTEGER,
  salary_female_median_k INTEGER,
  salary_male_mean_k INTEGER,
  salary_female_mean_k INTEGER,

  -- Industry comparison (MOPS)
  industry_salary_avg_k INTEGER,
  industry_avg_eps REAL,
  salary_vs_industry_pct REAL,

  -- Salary flags (MOPS)
  flag_low_salary INTEGER DEFAULT 0,
  flag_eps_high_salary_low INTEGER DEFAULT 0,
  flag_eps_up_salary_down INTEGER DEFAULT 0,

  -- Company statements (MOPS)
  salary_explanation TEXT,
  improvement_measures TEXT,

  -- Revenue (TWSE/TPEx, monthly update)
  revenue_latest INTEGER,
  revenue_yoy_pct REAL,
  revenue_period TEXT,

  -- Market cap (calculated: price × shares)
  market_cap REAL,

  -- Job counts (updated by crawlers)
  job_count_104 INTEGER DEFAULT 0,
  job_count_linkedin INTEGER DEFAULT 0,
  job_count_total INTEGER DEFAULT 0,
  job_count_prev_month INTEGER DEFAULT 0,
  job_count_trend TEXT DEFAULT 'stable',  -- 'expanding' / 'stable' / 'shrinking'

  -- AI insight (pre-generated)
  ai_insight TEXT,
  ai_insight_updated_at TEXT,

  -- External IDs for cross-linking
  encoded_cust_no_104 TEXT,
  linkedin_company_id TEXT,

  updated_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for common queries
CREATE INDEX idx_industry ON company_profiles(industry);
CREATE INDEX idx_market ON company_profiles(market);
CREATE INDEX idx_salary_median ON company_profiles(salary_median_k DESC);
CREATE INDEX idx_job_count ON company_profiles(job_count_total DESC);
CREATE INDEX idx_employee_count ON company_profiles(employee_count DESC);
CREATE INDEX idx_market_cap ON company_profiles(market_cap DESC);
CREATE INDEX idx_revenue_yoy ON company_profiles(revenue_yoy_pct DESC);

-- Jobs table (runtime query, not bundled)
DROP TABLE IF EXISTS jobs;

CREATE TABLE jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_id TEXT,
  company_name TEXT NOT NULL,
  title TEXT NOT NULL,
  location TEXT,
  date_posted TEXT,
  job_url TEXT,
  source TEXT,
  description TEXT,
  salary_min INTEGER,
  salary_max INTEGER,
  job_type TEXT DEFAULT ''
);

CREATE INDEX idx_jobs_stock_id ON jobs(stock_id);
CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_jobs_job_type ON jobs(job_type);
