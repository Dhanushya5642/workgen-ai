export default function ModuleCard({ title, description, icon, accent, onClick, theme }) {
  const dark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={onClick}
      className={`group relative overflow-hidden rounded-[28px] border p-6 text-left transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${
        dark ? 'border-white/10 bg-white/5' : 'border-[#D3CBB8] bg-[#FAF8F5]'
      }`}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${dark ? 'opacity-80' : 'opacity-20'} ${accent}`} />
      <div className="absolute inset-px rounded-[27px] bg-gradient-to-b from-white/10 to-transparent" />
      <div className="relative z-10">
        <div className={`mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border text-2xl shadow-lg ${
          dark ? 'border-white/15 bg-slate-950/40 text-white shadow-slate-950/20' : 'border-clay/20 bg-clay/10 text-clay shadow-clay/10'
        }`}>
          {icon}
        </div>
        <h3 className="text-xl font-semibold">{title}</h3>
        <p className={`mt-2 text-sm leading-6 ${dark ? 'text-slate-300' : 'text-stone-600'}`}>
          {description}
        </p>
        <div className={`mt-6 inline-flex items-center gap-2 text-sm font-medium ${
          dark ? 'text-cyan-300 group-hover:text-cyan-200' : 'text-clay group-hover:text-clay/85'
        }`}>
          Open module <span aria-hidden="true">→</span>
        </div>
      </div>
    </button>
  )
}