import { Link } from '@tanstack/react-router'
import ThemeToggle from './ThemeToggle'

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg)]/90 px-4 backdrop-blur-lg">
      <nav className="page-wrap flex items-center gap-x-6 py-3">
        <Link
          to="/"
          className="flex items-center gap-1 font-display text-lg font-extrabold tracking-tight no-underline"
        >
          <span className="text-[var(--text-heading)]">Offer</span>
          <span className="text-[var(--accent)]">Now</span>
        </Link>

        <div className="hidden items-center gap-5 text-sm font-medium sm:flex">
          <Link
            to="/"
            className="text-[var(--text-muted)] transition no-underline hover:text-[var(--text-heading)] [&.active]:text-[var(--text-heading)]"
            activeOptions={{ exact: true }}
          >
            探索公司
          </Link>
          <Link
            to="/salary"
            className="text-[var(--text-muted)] transition no-underline hover:text-[var(--text-heading)] [&.active]:text-[var(--text-heading)]"
          >
            薪資排行
          </Link>
          <Link
            to="/jobs"
            className="text-[var(--text-muted)] transition no-underline hover:text-[var(--text-heading)] [&.active]:text-[var(--text-heading)]"
          >
            職缺搜尋
          </Link>
        </div>

        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </nav>
    </header>
  )
}
