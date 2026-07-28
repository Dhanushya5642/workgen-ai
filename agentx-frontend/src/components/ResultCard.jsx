export default function ResultCard({ title, subtitle, theme, children, actions }) {
  const dark = theme === 'dark'

  return (
    <section
      className={`rounded-[28px] border p-5 shadow-xl backdrop-blur-xl md:p-6 ${
        dark ? 'border-white/10 bg-white/5' : 'border-[#D3CBB8] bg-[#FAF8F5]'
      }`}
    >
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h3 className="text-lg font-semibold">{title}</h3>
          {subtitle ? <p className={`mt-1 text-sm ${dark ? 'text-slate-400' : 'text-stone-500'}`}>{subtitle}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </div>
      {children}
    </section>
  )
}