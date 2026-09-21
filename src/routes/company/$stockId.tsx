import {
  Building,
  DollarSign,
  Flag,
  Scale,
  TrendingUp,
} from '@sketchyicons/react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { Badge } from '#/components/Badge'
import { BigMetric } from '#/components/BigMetric'
import { InfoRow } from '#/components/InfoRow'
import { Section } from '#/components/Section'
import {
  calculateAttractivenessScore,
  getCompanyByStockId,
} from '#/utils/companies.functions'
import type { AttractivenessScore } from '#/utils/types'

const GRADE_CONFIG: Record<
  string,
  { label: string; color: string; bg: string }
> = {
  A: {
    label: '優秀',
    color: 'text-[var(--green-positive)]',
    bg: 'bg-[var(--green-soft)]',
  },
  B: {
    label: '良好',
    color: 'text-[var(--accent)]',
    bg: 'bg-[var(--accent-soft)]',
  },
  C: {
    label: '普通',
    color: 'text-[var(--text-muted)]',
    bg: 'bg-[var(--bg-elevated)]',
  },
  D: {
    label: '偏低',
    color: 'text-[var(--red-negative)]',
    bg: 'bg-[var(--red-soft)]',
  },
  F: {
    label: '不佳',
    color: 'text-[var(--red-negative)]',
    bg: 'bg-[var(--red-soft)]',
  },
}

function ScoreBar({ score }: { score: number }) {
  const barColor =
    score >= 70
      ? 'var(--green-positive)'
      : score >= 45
        ? 'var(--accent)'
        : 'var(--red-negative)'
  return (
    <div className="h-2 w-full rounded-full bg-[var(--bg-elevated)]">
      <div
        className="h-2 rounded-full transition-all"
        style={{ width: `${score}%`, backgroundColor: barColor }}
      />
    </div>
  )
}

function ScoreCard({ score }: { score: AttractivenessScore }) {
  const config = GRADE_CONFIG[score.grade] ?? GRADE_CONFIG.C
  return (
    <Section title="公司吸引力評分">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:gap-6">
        <div
          className={`flex flex-shrink-0 flex-col items-center justify-center rounded-xl ${config.bg} px-5 py-4`}
        >
          <div
            className={`font-display text-4xl font-extrabold ${config.color}`}
          >
            {score.grade}
          </div>
          <div className={`text-xs font-semibold ${config.color}`}>
            {config.label}
          </div>
          <div className="mt-1 text-[10px] text-[var(--text-muted)]">
            {score.overall}/100
          </div>
        </div>
        <div className="flex-1 space-y-3">
          {score.dimensions.map((d) => (
            <div key={d.name}>
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs font-semibold text-[var(--text-heading)]">
                  {(() => {
                    const icons: Record<string, React.FC<{ size?: number }>> = {
                      DollarSign,
                      TrendingUp,
                      Building,
                      Scale,
                      Flag,
                    }
                    const Icon = icons[d.icon]
                    return Icon ? <Icon size={14} /> : null
                  })()} {d.name}
                </span>
                <span className="text-xs text-[var(--text-muted)]">
                  {d.score}
                </span>
              </div>
              <ScoreBar score={d.score} />
              <div className="mt-0.5 text-[10px] text-[var(--text-muted)]">
                {d.detail}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  )
}

export const Route = createFileRoute('/company/$stockId')({
  loader: ({ params }) => getCompanyByStockId({ data: params.stockId }),
  component: CompanyDetailPage,
  head: ({ loaderData }) => {
    const c = loaderData
    if (!c) return { meta: [{ title: '找不到公司 | OfferNow' }] }
    const salaryStr = c.salary_median_k
      ? `薪資中位數 ${(c.salary_median_k / 10).toFixed(1)} 萬`
      : ''
    return {
      meta: [
        {
          title: `${c.short_name || c.name}（${c.stock_id}）${salaryStr ? ` · ${salaryStr}` : ''} | OfferNow`,
        },
        {
          name: 'description',
          content: `${c.name}（${c.stock_id}）的薪資、EPS、員工數等公司全貌資訊。${salaryStr}。`,
        },
      ],
    }
  },
})

function formatMarketCap(cap: number | null): string {
  if (!cap) return '—'
  if (cap >= 10000) return `${(cap / 10000).toFixed(1)} 兆`
  if (cap >= 1000)
    return `${cap.toLocaleString(undefined, { maximumFractionDigits: 0 })} 億`
  return `${cap.toFixed(0)} 億`
}

function formatRevenueYoY(pct: number | null): string {
  if (pct === null || pct === undefined) return '—'
  if (pct > 999) return '>999%'
  if (pct < -999) return '<-999%'
  return `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%`
}

function buildOrganizationJsonLd(
  c: NonNullable<ReturnType<typeof Route.useLoaderData>>,
) {
  const jsonLd: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: c.name,
    ...(c.address && {
      address: { '@type': 'PostalAddress', streetAddress: c.address },
    }),
    ...(c.phone && { telephone: c.phone }),
    ...(c.tax_id && { taxID: c.tax_id }),
    ...(c.employee_count && {
      numberOfEmployees: {
        '@type': 'QuantitativeValue',
        value: c.employee_count,
      },
    }),
    ...(c.industry && { industry: c.industry }),
  }
  return jsonLd
}

function CompanyDetailPage() {
  const company = Route.useLoaderData()

  if (!company) {
    return (
      <main className="page-wrap px-4 py-16 text-center">
        <h1 className="mb-4 font-display text-2xl font-bold text-[var(--text-heading)]">
          找不到公司
        </h1>
        <p className="mb-6 text-[var(--text-muted)]">
          沒有找到此股票代號的公司資料。
        </p>
        <Link to="/" className="text-sm font-semibold text-[var(--accent)]">
          ← 返回公司列表
        </Link>
      </main>
    )
  }

  const c = company
  const marketLabel = c.market === 'listed' ? '上市' : '上櫃'
  const salaryMedianWan = c.salary_median_k
    ? (c.salary_median_k / 10).toFixed(1)
    : null
  const salaryMeanWan = c.salary_mean_k
    ? (c.salary_mean_k / 10).toFixed(1)
    : null
  const initial = (c.short_name || c.name).charAt(0)

  const capitalFormatted = c.capital
    ? `${(Number(c.capital) / 100000000).toFixed(0)} 億`
    : '—'

  const formatDate = (d: string) => {
    if (!d || d.length < 8) return d || '—'
    return `${d.slice(0, 4)}/${d.slice(4, 6)}/${d.slice(6, 8)}`
  }

  const vsIndustry = c.salary_vs_industry_pct
  const industryAvgWan = c.industry_salary_avg_k
    ? (c.industry_salary_avg_k / 10).toFixed(1)
    : null

  const organizationJsonLd = buildOrganizationJsonLd(c)

  return (
    <main className="page-wrap px-4 pb-12 pt-6">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationJsonLd) }}
      />
      <div className="mb-6 flex items-center gap-4">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm font-medium text-[var(--text-body)] no-underline hover:text-[var(--accent)]"
        >
          ← 返回公司列表
        </Link>
        <Link
          to="/salary"
          className="inline-flex items-center gap-1 text-sm font-medium text-[var(--text-body)] no-underline hover:text-[var(--accent)]"
        >
          薪資排行 →
        </Link>
      </div>

      {/* Company Header */}
      <div className="mb-8 flex items-start gap-4">
        <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-xl bg-[var(--bg-elevated)] font-display text-2xl font-bold text-[var(--text-heading)]">
          {initial}
        </div>
        <div>
          <h1 className="font-display text-2xl font-extrabold text-[var(--text-heading)] sm:text-3xl">
            {c.short_name || c.name}
          </h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">{c.name}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className="rounded-full bg-[var(--accent-soft)] px-2.5 py-0.5 text-xs font-semibold text-[var(--text-heading)]">
              {c.stock_id}
            </span>
            <span className="rounded-full border border-[var(--border)] px-2.5 py-0.5 text-xs text-[var(--text-muted)]">
              {c.industry || '未分類'}
            </span>
            <span className="rounded-full border border-[var(--border)] px-2.5 py-0.5 text-xs text-[var(--text-muted)]">
              {marketLabel}
            </span>
            {c.market_cap && (
              <span className="rounded-full border border-[var(--border)] px-2.5 py-0.5 text-xs text-[var(--text-muted)]">
                市值 {formatMarketCap(c.market_cap)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Attractiveness Score */}
      <div className="mb-6">
        <ScoreCard score={calculateAttractivenessScore(c)} />
      </div>

      {/* Growth + Hiring Signal */}
      {(c.job_count_104 ?? 0) > 0 &&
        c.revenue_yoy_pct !== null &&
        c.revenue_yoy_pct !== undefined &&
        c.revenue_yoy_pct > 0 && (
          <div className="mb-6 flex items-center gap-2 rounded-xl bg-[var(--green-soft)] px-5 py-3">
            <span className="text-sm font-semibold text-[var(--green-positive)]">
              營收成長 +
              {c.revenue_yoy_pct > 999 ? '>999' : c.revenue_yoy_pct.toFixed(1)}%
              且正在招募 {c.job_count_104!.toLocaleString()} 個職缺
            </span>
          </div>
        )}

      {/* Hiring Trend */}
      {c.job_count_trend && c.job_count_trend !== 'stable' && (
        <div
          className={`mb-6 flex items-center gap-2 rounded-xl px-5 py-3 ${
            c.job_count_trend === 'expanding'
              ? 'bg-[var(--green-soft)]'
              : 'bg-[var(--red-soft)]'
          }`}
        >
          <span
            className={`text-sm font-semibold ${
              c.job_count_trend === 'expanding'
                ? 'text-[var(--green-positive)]'
                : 'text-[var(--red-negative)]'
            }`}
          >
            {c.job_count_trend === 'expanding' ? '擴編中' : '縮編中'}
            {c.job_count_prev_month != null && (c.job_count_total ?? 0) > 0 && (
              <span className="ml-2 font-normal">
                上月 {c.job_count_prev_month.toLocaleString()} 缺 → 本月{' '}
                {(c.job_count_total ?? 0).toLocaleString()} 缺
              </span>
            )}
          </span>
        </div>
      )}

      {/* Salary Flags */}
      {(c.flag_low_salary === 1 ||
        c.flag_eps_high_salary_low === 1 ||
        c.flag_eps_up_salary_down === 1) && (
        <div className="mb-6 flex flex-wrap gap-2">
          {c.flag_low_salary === 1 && (
            <span className="rounded-lg bg-[var(--red-soft)] px-3 py-1.5 text-xs font-medium text-[var(--red-negative)]">
              ⚠ 非主管平均薪資未達 50 萬
            </span>
          )}
          {c.flag_eps_high_salary_low === 1 && (
            <span className="rounded-lg bg-[var(--red-soft)] px-3 py-1.5 text-xs font-medium text-[var(--red-negative)]">
              ⚠ EPS 優於同業但薪資低於同業
            </span>
          )}
          {c.flag_eps_up_salary_down === 1 && (
            <span className="rounded-lg bg-[var(--red-soft)] px-3 py-1.5 text-xs font-medium text-[var(--red-negative)]">
              ⚠ EPS 成長但薪資減少
            </span>
          )}
        </div>
      )}

      {/* AI Insight */}
      {c.ai_insight && (
        <div className="mb-6 rounded-xl bg-[var(--accent-soft)] px-5 py-4">
          <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-[var(--accent)]">
            AI 洞察
          </div>
          <div className="text-sm text-[var(--text-heading)]">
            {c.ai_insight}
          </div>
        </div>
      )}

      {/* 104 Link */}
      {c.job_count_104 != null && c.job_count_104 > 0 && (
        <div className="mb-6">
          <a
            href={
              c.encoded_cust_no_104
                ? `https://www.104.com.tw/company/${c.encoded_cust_no_104}`
                : `https://www.104.com.tw/company/search?keyword=${encodeURIComponent(c.short_name || c.name)}`
            }
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-[#1a2e1a] no-underline transition hover:bg-[var(--accent-hover)]"
          >
            在 104 上查看 {c.job_count_104.toLocaleString()} 個職缺 →
          </a>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Salary + Financial Section */}
        <div className="lg:col-span-2 space-y-6">
          <Section title="薪資資訊">
            <div className="grid gap-4 sm:grid-cols-2">
              <BigMetric
                label="非主管薪資中位數"
                value={salaryMedianWan ? `${salaryMedianWan} 萬` : '未揭露'}
                badge={
                  c.salary_median_change_pct !== null ? (
                    <Badge value={c.salary_median_change_pct} suffix="%" />
                  ) : undefined
                }
                note={c.salary_year ? `${c.salary_year} 年度` : undefined}
              />
              <BigMetric
                label="非主管薪資平均數"
                value={salaryMeanWan ? `${salaryMeanWan} 萬` : '未揭露'}
              />
              {vsIndustry !== null && vsIndustry !== undefined && (
                <BigMetric
                  label="同業薪資比較"
                  value={`${vsIndustry > 0 ? '+' : ''}${vsIndustry.toFixed(1)}%`}
                  note={
                    industryAvgWan ? `同業平均 ${industryAvgWan} 萬` : undefined
                  }
                  badge={<Badge value={vsIndustry} suffix="" />}
                />
              )}
              <BigMetric
                label="EPS"
                value={c.eps !== null ? `${c.eps} 元/股` : '未揭露'}
              />
              <BigMetric
                label="員工人數"
                value={
                  c.employee_count
                    ? `${c.employee_count.toLocaleString()} 人`
                    : '未揭露'
                }
              />
              {c.job_count_104 != null && c.job_count_104 > 0 && (
                <BigMetric
                  label="104 職缺數"
                  value={`${c.job_count_104.toLocaleString()} 個`}
                />
              )}
            </div>
          </Section>

          {/* Gender Salary */}
          {(c.salary_male_median_k || c.salary_female_median_k) && (
            <Section title="性別薪資（資本額 100 億以上）">
              <div className="grid gap-4 sm:grid-cols-2">
                <BigMetric
                  label="男性薪資中位數"
                  value={
                    c.salary_male_median_k
                      ? `${(c.salary_male_median_k / 10).toFixed(1)} 萬`
                      : '未揭露'
                  }
                />
                <BigMetric
                  label="女性薪資中位數"
                  value={
                    c.salary_female_median_k
                      ? `${(c.salary_female_median_k / 10).toFixed(1)} 萬`
                      : '未揭露'
                  }
                />
              </div>
              {c.salary_male_median_k && c.salary_female_median_k && (
                <p className="mt-3 text-xs text-[var(--text-muted)]">
                  性別薪資差異：
                  {(
                    ((c.salary_male_median_k - c.salary_female_median_k) /
                      c.salary_male_median_k) *
                    100
                  ).toFixed(1)}
                  % （男性
                  {c.salary_male_median_k > c.salary_female_median_k
                    ? '較高'
                    : '較低'}
                  ）
                </p>
              )}
            </Section>
          )}

          {/* Revenue & Market Cap */}
          {(c.revenue_yoy_pct !== null || c.market_cap) && (
            <Section title="財務概況">
              <div className="grid gap-4 sm:grid-cols-2">
                {c.revenue_yoy_pct !== null &&
                  c.revenue_yoy_pct !== undefined && (
                    <BigMetric
                      label="營收年增率"
                      value={formatRevenueYoY(c.revenue_yoy_pct)}
                      badge={
                        <Badge
                          value={
                            c.revenue_yoy_pct > 999
                              ? 999
                              : c.revenue_yoy_pct < -999
                                ? -999
                                : c.revenue_yoy_pct
                          }
                          suffix=""
                        />
                      }
                    />
                  )}
                {c.market_cap && (
                  <BigMetric
                    label="市值"
                    value={formatMarketCap(c.market_cap)}
                  />
                )}
              </div>
            </Section>
          )}
        </div>

        {/* Company Info */}
        <div>
          <Section title="公司資訊">
            <div className="space-y-3">
              <InfoRow label="資本額" value={capitalFormatted} />
              <InfoRow label="董事長" value={c.chairman || '—'} />
              <InfoRow label="總經理" value={c.gm || '—'} />
              <InfoRow label="成立日期" value={formatDate(c.established)} />
              <InfoRow
                label={c.market === 'listed' ? '上市日期' : '上櫃日期'}
                value={formatDate(c.listed_date)}
              />
              <InfoRow label="地址" value={c.address || '—'} />
              {c.phone && <InfoRow label="電話" value={c.phone} />}
              {c.tax_id && <InfoRow label="統一編號" value={c.tax_id} />}
            </div>
          </Section>
        </div>
      </div>
    </main>
  )
}
