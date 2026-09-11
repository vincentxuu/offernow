export function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-5 shadow-[var(--shadow)]">
      <h2 className="mb-4 font-display text-lg font-bold text-[var(--text-heading)]">
        {title}
      </h2>
      {children}
    </section>
  )
}
