import ModuleCard from '../components/ModuleCard'
import ResultCard from '../components/ResultCard'

export default function Dashboard({ items, onNavigate, theme }) {
  const featured = items.filter((item) => item.featured)
  const dark = theme === 'dark'

  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[1.35fr_0.85fr]">
        <div className={`rounded-[32px] border p-8 shadow-2xl backdrop-blur-xl transition ${
          dark ? 'border-cyan-400/15 bg-gradient-to-br from-cyan-500/15 via-slate-900/20 to-violet-500/15' : 'border-forest/20 bg-gradient-to-br from-forest/10 via-[#FAF8F5]/30 to-clay/10'
        }`}>
          <div className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] transition ${
            dark ? 'border-cyan-400/30 bg-cyan-400/10 text-cyan-300' : 'border-forest/30 bg-forest/10 text-forest'
          }`}>
            AgentX mission control
          </div>
          <h2 className="mt-5 max-w-3xl text-3xl font-semibold tracking-tight md:text-5xl">
            Balance worklife and mental health like a PRO
          </h2>
          <p className={`mt-4 max-w-2xl text-sm leading-7 md:text-base ${dark ? 'text-slate-300' : 'text-stone-700'}`}>
            A complete Power button for Email, Calender, Notion, Alarm, Research, Summary, Meeting Transcription, Journal, Cognitive Assistant and everything you want!! 
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => onNavigate('email')}
              className={`rounded-2xl px-5 py-3 text-sm font-semibold shadow-lg transition ${
                dark ? 'bg-cyan-400 text-slate-950 shadow-cyan-500/25 hover:bg-cyan-300' : 'bg-clay text-white shadow-clay/20 hover:bg-clay/90'
              }`}
            >
              Launch Email Intelligence
            </button>
            <button
              type="button"
              onClick={() => onNavigate('meeting')}
              className={`rounded-2xl border px-5 py-3 text-sm font-semibold transition ${
                dark ? 'border-white/15 bg-white/8 text-white hover:bg-white/12' : 'border-[#D3CBB8] bg-[#FAF8F5] text-[#2F2924] hover:bg-[#F3EFE4]'
              }`}
            >
              Open Meeting Intelligence
            </button>
          </div>
        </div>

        <ResultCard title="What's so special?" subtitle="You gonna regret if you don't have it" theme={theme}>
          <div className={`grid gap-3 text-sm ${theme === 'dark' ? 'text-slate-300' : 'text-stone-700'}`}>
            {[
              'Your virtual personal diary',
              'One dashboard for all AI workflows',
              'No more worry about to-do lists',
            
              'Cognitive AI notifications',
            ].map((point) => (
              <div
                key={point}
                className={`rounded-2xl border px-4 py-3 ${
                  theme === 'dark' ? 'border-white/10 bg-white/5' : 'border-[#D3CBB8] bg-[#FAF8F5] text-stone-700'
                }`}
              >
                {point}
              </div>
            ))}
          </div>
        </ResultCard>
      </section>

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {featured.map((item) => (
          <ModuleCard
            key={item.id}
            title={item.label}
            description={item.description}
            icon={item.icon}
            accent={item.accent}
            theme={theme}
            onClick={() => onNavigate(item.id)}
          />
        ))}
      </section>
    </div>
  )
}