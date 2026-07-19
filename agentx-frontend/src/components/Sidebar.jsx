const sidebarBase =
  'border-r backdrop-blur-xl transition-colors md:sticky md:top-0 md:h-screen md:w-80 md:min-w-80'

export default function Sidebar({ items, activePage, onChange, theme }) {
  const dark = theme === 'dark'

  return (
    <aside
      className={`${sidebarBase} ${
        dark ? 'border-white/10 bg-slate-950/70' : 'border-slate-200 bg-white/75'
      }`}
    >
      <div className="flex h-full flex-col px-4 py-5 md:px-5 md:py-8">
        <div className="mb-6 flex items-center gap-3 md:mb-10">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 via-sky-500 to-violet-500 text-xl font-bold text-white shadow-lg shadow-sky-500/20">
            AX
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-400">
              The ultimate AI assistant
            </p>
            <h1 className="text-2xl font-semibold">AgentX</h1>
          </div>
        </div>

        <div className="mb-3 text-xs font-semibold uppercase tracking-[0.26em] text-slate-400">
          Modules
        </div>

        <nav className="flex gap-2 overflow-x-auto pb-2 md:flex-1 md:flex-col md:overflow-visible">
          {items.map((item) => {
            const active = activePage === item.id

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onChange(item.id)}
                className={`group min-w-fit rounded-2xl border px-4 py-3 text-left transition-all md:min-w-0 ${
                  active
                    ? 'border-cyan-400/60 bg-gradient-to-r from-cyan-500/20 to-violet-500/20 shadow-lg shadow-cyan-500/10'
                    : dark
                      ? 'border-white/10 bg-white/5 hover:border-cyan-400/30 hover:bg-white/10'
                      : 'border-slate-200 bg-white/80 hover:border-cyan-300 hover:bg-cyan-50/70'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">{item.icon}</span>
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold md:text-[15px]">{item.label}</div>
                    <div className="truncate text-xs text-slate-400">{item.caption}</div>
                  </div>
                </div>
              </button>
            )
          })}
        </nav>

        <div
          className={`mt-6 rounded-3xl border p-4 ${
            dark ? 'border-white/10 bg-white/5' : 'border-slate-200 bg-white/90'
          }`}
        >
          {/* <p className="text-sm font-semibold">Introducing AgentX by</p> */}
  
          {/*<div className="mt-3 inline-flex rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
            Settings
          </div>
          */}
          
          {/* <p className="mt-1 text-sm text-slate-400">DHIVYA V</p> */}
      
        </div>
      </div>
    </aside>
  )
}