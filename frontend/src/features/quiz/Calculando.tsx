import { RefreshCw } from 'lucide-react'

export function Calculando() {
  return (
    <main className="flex-1 bg-bg-50 flex flex-col items-center justify-center p-5" aria-busy="true">
      <div className="bg-white p-10 rounded-2xl shadow-sm border border-line-200 flex flex-col items-center">
        <RefreshCw size={48} className="text-red-600 animate-spin mb-8" aria-hidden />
        <h2 className="text-2xl font-bold text-ink-900 text-center max-w-[320px] animate-pulse" role="status">
          Analisando seu perfil e cruzando com nossos cursos...
        </h2>
        <p className="text-ink-600 mt-4 text-sm font-medium">Isso leva só um instante</p>
      </div>
    </main>
  )
}