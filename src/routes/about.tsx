import { createFileRoute, Link } from '@tanstack/react-router'

export const Route = createFileRoute('/about')({
  component: About,
})

function About() {
  return (
    <main className="page-wrap px-4 pb-12 pt-8">
      <section className="mb-10">
        <h1 className="mb-3 font-display text-3xl font-extrabold tracking-tight text-[var(--text-heading)] sm:text-4xl">
          關於 OfferNow
        </h1>
        <p className="max-w-2xl text-base leading-relaxed text-[var(--text-body)]">
          OfferNow 是一個以台灣上市櫃公司為軸心的職缺聚合平台。我們把三個原本分散在不同政府網站的公開資料串在一起，讓你在同一個頁面就能看到一家公司的薪資水準、財務體質和招募動態。
        </p>
      </section>

      <section className="mb-10">
        <h2 className="mb-4 font-display text-xl font-bold text-[var(--text-heading)]">
          解決什麼問題？
        </h2>
        <p className="mb-4 max-w-2xl text-sm leading-relaxed text-[var(--text-body)]">
          想了解一家上市櫃公司值不值得去，你得自己拼湊資訊：
        </p>
        <div className="grid gap-4 sm:grid-cols-3">
          <InfoCard
            emoji="🏢"
            title="公司基本面"
            desc="去證交所 OpenAPI 查產業、資本額、營收"
            source="TWSE / TPEx"
          />
          <InfoCard
            emoji="💰"
            title="薪資真相"
            desc="去公開資訊觀測站翻非主管薪資中位數"
            source="MOPS 員工薪資揭露"
          />
          <InfoCard
            emoji="📋"
            title="職缺動態"
            desc="再去 104、LinkedIn 一家一家搜招募中的職位"
            source="104 / LinkedIn"
          />
        </div>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[var(--text-body)]">
          OfferNow 自動把這些資料交叉比對，讓「薪資中位數 × EPS × 市值 × 現正招募」一眼看完。
        </p>
      </section>

      <section className="mb-10">
        <h2 className="mb-4 font-display text-xl font-bold text-[var(--text-heading)]">
          核心功能
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <FeatureCard
            title="1,984 家上市櫃公司"
            desc="涵蓋上市（TWSE）與上櫃（TPEx）全部公司，依產業分類瀏覽。"
          />
          <FeatureCard
            title="薪資排行"
            desc="非主管全時員工薪資中位數與平均數，含年增率、同業比較、性別薪資差距。"
          />
          <FeatureCard
            title="市值與財務"
            desc="即時市值計算（收盤價 × 發行股數）、每月營收、EPS，掌握公司財務體質。"
          />
          <FeatureCard
            title="職缺聚合"
            desc="從 104 人力銀行與 LinkedIn 聚合職缺，看哪些公司正在擴編、招什麼人。"
          />
        </div>
      </section>

      <section className="mb-10">
        <h2 className="mb-4 font-display text-xl font-bold text-[var(--text-heading)]">
          資料來源
        </h2>
        <div className="overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] shadow-[var(--shadow)]">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="border-b border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  資料
                </th>
                <th className="border-b border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  來源
                </th>
                <th className="border-b border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  更新頻率
                </th>
              </tr>
            </thead>
            <tbody>
              <DataRow data="公司基本資料、產業分類" source="TWSE OpenAPI / TPEx" freq="即時" />
              <DataRow data="每月營業收入" source="TWSE / TPEx 月營收" freq="每月" />
              <DataRow data="股價與市值" source="TWSE / TPEx 收盤價" freq="每日" />
              <DataRow data="非主管薪資中位數 / 平均數" source="MOPS 公開資訊觀測站" freq="每年（6 月底）" />
              <DataRow data="性別薪資差距" source="MOPS（資本額 100 億以上）" freq="每年" />
              <DataRow data="職缺" source="104 人力銀行 / LinkedIn" freq="定期爬取" />
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-[var(--text-muted)]">
          所有資料均來自公開管道。薪資資料為 114 年度（2025）揭露值。
        </p>
      </section>

      <section className="mb-10 rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-6 shadow-[var(--shadow)]">
        <h2 className="mb-3 font-display text-lg font-bold text-[var(--text-heading)]">
          免責聲明
        </h2>
        <ul className="list-inside list-disc space-y-2 text-sm leading-relaxed text-[var(--text-body)]">
          <li>本站為非官方的個人學習專案，僅供教育研究與個人使用，非商業用途。</li>
          <li>未獲 104 人力銀行、LinkedIn 或任何政府機關官方授權。</li>
          <li>所有分析結果僅供參考，不保證資料的即時性、完整性或準確性。</li>
          <li>使用者同意自行承擔使用本站的一切後果，作者不對任何損失或法律問題負責。</li>
        </ul>
      </section>

      <div className="text-center">
        <Link
          to="/"
          className="inline-block rounded-xl border border-[var(--accent)] bg-[var(--accent-soft)] px-6 py-2.5 text-sm font-semibold text-[var(--text-heading)] no-underline transition hover:bg-[var(--accent)] hover:text-[#00473e]"
        >
          開始探索公司
        </Link>
      </div>
    </main>
  )
}

function InfoCard({ emoji, title, desc, source }: { emoji: string; title: string; desc: string; source: string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-5 shadow-[var(--shadow)]">
      <div className="mb-2 text-2xl">{emoji}</div>
      <h3 className="mb-1 text-sm font-bold text-[var(--text-heading)]">{title}</h3>
      <p className="mb-2 text-xs leading-relaxed text-[var(--text-body)]">{desc}</p>
      <span className="text-[10px] font-medium text-[var(--text-muted)]">{source}</span>
    </div>
  )
}

function FeatureCard({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-5 shadow-[var(--shadow)]">
      <h3 className="mb-1 text-sm font-bold text-[var(--text-heading)]">{title}</h3>
      <p className="text-xs leading-relaxed text-[var(--text-body)]">{desc}</p>
    </div>
  )
}

function DataRow({ data, source, freq }: { data: string; source: string; freq: string }) {
  return (
    <tr className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-elevated)]">
      <td className="px-4 py-3 text-[var(--text-heading)]">{data}</td>
      <td className="px-4 py-3 text-[var(--text-body)]">{source}</td>
      <td className="px-4 py-3 text-[var(--text-muted)]">{freq}</td>
    </tr>
  )
}
