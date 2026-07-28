import { useEffect, useMemo, useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import EmailIntelligence from './pages/EmailIntelligence'
import JournalAI from './pages/JournalAI'
import KnowledgeHub from './pages/KnowledgeHub'
import LiveTranscription from './pages/LiveTranscription'
import MeetingIntelligence from './pages/MeetingIntelligence'
import ResearchCopilot from './pages/ResearchCopilot'
import { API_BASE_URL } from './services/api'

const NAV_ITEMS = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    caption: 'Overview',
    icon: '◈',
    featured: false,
    description: 'Mission control for every AgentX workflow.',
    accent: 'from-slate-500/20 to-slate-900/10',
  },
  {
    id: 'email',
    label: 'Email Intelligence',
    caption: 'Core module',
    icon: '✉️',
    featured: true,
    description: 'Scan inboxes, classify intent, and push detected opportunities into action.',
    accent: 'from-cyan-500/30 via-sky-500/15 to-blue-500/10',
  },
  {
    id: 'meeting',
    label: 'Meeting Intelligence',
    caption: 'Transcript analysis',
    icon: '🧠',
    featured: true,
    description: 'Turn raw conversations into summaries, decisions, and next steps.',
    accent: 'from-violet-500/30 via-fuchsia-500/15 to-sky-500/10',
  },
  {
    id: 'research',
    label: 'Research Copilot',
    caption: 'LLM research packs',
    icon: '🔬',
    featured: true,
    description: 'Generate overviews, questions, outlines, and citations for any topic.',
    accent: 'from-emerald-500/30 via-cyan-500/15 to-teal-500/10',
  },
  {
    id: 'journal',
    label: 'Journal AI',
    caption: 'Emotion signals',
    icon: '📓',
    featured: true,
    description: 'Extract mood, stress, focus, and grounded coaching suggestions.',
    accent: 'from-amber-500/30 via-orange-500/15 to-rose-500/10',
  },
  {
    id: 'transcription',
    label: 'Live Transcription',
    caption: 'Whisper pipeline',
    icon: '🎙️',
    featured: true,
    description: 'Surface real-time speech-to-text output in a stage-friendly panel.',
    accent: 'from-indigo-500/30 via-sky-500/15 to-cyan-500/10',
  },
  {
    id: 'knowledge',
    label: 'Knowledge Hub',
    caption: 'Optional search layer',
    icon: '🗂️',
    featured: false,
    description: 'Explore saved insights across the AgentX knowledge graph.',
    accent: 'from-slate-500/25 via-sky-500/10 to-violet-500/10',
  },
]

const PAGE_COMPONENTS = {
  dashboard: Dashboard,
  email: EmailIntelligence,
  meeting: MeetingIntelligence,
  research: ResearchCopilot,
  journal: JournalAI,
  transcription: LiveTranscription,
  knowledge: KnowledgeHub,
}

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [theme, setTheme] = useState(() => localStorage.getItem('agentx-theme') || 'dark')

  useEffect(() => {
    localStorage.setItem('agentx-theme', theme)
  }, [theme])

  const activeItem = useMemo(
    () => NAV_ITEMS.find((item) => item.id === activePage) || NAV_ITEMS[0],
    [activePage],
  )

  const PageComponent = PAGE_COMPONENTS[activePage]
  const dark = theme === 'dark'

  return (
    <div
      className={`min-h-screen transition-colors ${
        dark ? 'bg-slate-950 text-slate-50' : 'light-theme bg-paper-grid text-[#23201C]'
      }`}
    >
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className={`absolute -left-16 top-10 h-64 w-64 rounded-full blur-3xl ${dark ? 'bg-cyan-500/12' : 'bg-clay/5'}`} />
        <div className={`absolute right-0 top-1/3 h-72 w-72 rounded-full blur-3xl ${dark ? 'bg-violet-500/12' : 'bg-forest/5'}`} />
        <div className={`absolute bottom-0 left-1/3 h-72 w-72 rounded-full blur-3xl ${dark ? 'bg-sky-500/10' : 'bg-clay/5'}`} />
      </div>

      <div className="relative flex min-h-screen flex-col md:flex-row">
        <Sidebar items={NAV_ITEMS} activePage={activePage} onChange={setActivePage} theme={theme} />

        <main className="flex-1 p-4 md:p-6 lg:p-8">
          <header className="mb-6 flex flex-col gap-4 lg:mb-8 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className={`text-sm font-semibold uppercase tracking-[0.28em] ${dark ? 'text-cyan-400' : 'text-forest'}`}>{activeItem.caption}</p>
              <h2 className="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">{activeItem.label}</h2>
              <p className={`mt-2 max-w-3xl text-sm leading-7 ${dark ? 'text-slate-300' : 'text-[#5F5852]'}`}>
                {activeItem.description}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div
                className={`rounded-2xl border px-4 py-3 text-sm shadow-lg backdrop-blur-xl ${
                  dark ? 'border-white/10 bg-white/5' : 'border-[#D3CBB8] bg-[#FAF8F5]/85'
                }`}
              >
                {/* <div className="text-slate-400">Backend API</div> */}
                {/*<div className="mt-1 font-medium">Team Bet@4ge</div>*/}
              </div>

              <button
                type="button"
                onClick={() => setTheme(dark ? 'light' : 'dark')}
                className={`rounded-2xl border px-4 py-3 text-sm font-medium shadow-lg backdrop-blur-xl transition ${
                  dark
                    ? 'border-white/10 bg-white/5 hover:bg-white/10'
                    : 'border-[#D3CBB8] bg-[#FAF8F5]/85 hover:bg-[#F3EFE4] text-slate-800'
                }`}
              >
                {dark ? '☀️ Light theme' : '🌙 Dark theme'}
              </button>
            </div>
          </header>

          <PageComponent items={NAV_ITEMS} onNavigate={setActivePage} theme={theme} />
        </main>
      </div>
    </div>
  )
}