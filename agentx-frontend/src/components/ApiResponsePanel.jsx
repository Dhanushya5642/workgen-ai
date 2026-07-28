export default function ApiResponsePanel({ title = 'Backend Response', data, theme }) {
  const empty = data == null
  const cardClass = theme === 'dark' ? 'border-white/10 bg-slate-950/70 text-slate-200' : 'border-[#D3CBB8] bg-[#FAF8F5] text-stone-800'

  return (
    <section className={`rounded-[28px] border p-5 shadow-xl backdrop-blur-xl md:p-6 ${cardClass}`}>
      <h3 className="text-lg font-semibold">{title}</h3>
      <pre className="mt-4 overflow-x-auto whitespace-pre-wrap break-words text-sm leading-7">
        {empty ? 'No backend response yet.' : JSON.stringify(data, null, 2)}
      </pre>
    </section>
  )
}