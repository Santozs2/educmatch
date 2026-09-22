import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'

export function CascaConta({ titulo, subtitulo, children }: { titulo: string; subtitulo: string; children: ReactNode }) {
  const navegar = useNavigate()
  return (
    <main className="flex-1 bg-bg-50 w-full">
      <div className="max-w-[900px] mx-auto px-5 py-8 sm:px-8 sm:py-12">
        <button onClick={() => navegar(-1)} className="mb-8 flex min-h-[44px] items-center gap-1 rounded-lg px-2 font-semibold text-red-700 hover:bg-red-50">
          <ChevronLeft size={20} /> Voltar
        </button>
        <div className="mb-8 border-l-4 border-red-600 pl-5">
          <h1 className="text-3xl font-bold text-ink-900">{titulo}</h1>
          <p className="mt-1 text-ink-600">{subtitulo}</p>
        </div>
        {children}
      </div>
    </main>
  )
}