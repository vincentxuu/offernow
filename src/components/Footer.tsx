export default function Footer() {
  return (
    <footer className="mt-16 border-t border-[var(--border)] px-4 py-8">
      <div className="page-wrap text-center text-xs text-[var(--text-muted)]">
        <p className="m-0">
          OfferNow &middot; 資料來源：證交所 OpenAPI、公開資訊觀測站（MOPS）
        </p>
        <p className="m-0 mt-1">
          薪資為 114 年度非主管全時員工資料 &middot; 職缺資訊來自各公司公開頁面
        </p>
      </div>
    </footer>
  )
}
