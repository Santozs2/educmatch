import type { ReactNode } from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { ButtonPrimary } from './ui/Button'

export function Carregando({ texto = 'Carregando…' }: { texto?: string }) {
  return (
    <main className="flex-1 flex flex-col items-center justify-center p-8" aria-busy="true">
      <RefreshCw size={36} className="text-red-600 animate-spin mb-4" aria-hidden />
      <p className="text-ink-600 font-semibold">{texto}</p>
    </main>
  )
}

export function EstadoErro({
  titulo,
  mensagem,
  onTentar,
  children,
}: {
  titulo: string
  mensagem: string
  onTentar?: () => void
  children?: ReactNode
}) {
  return (
    <main className="flex-1 max-w-[600px] w-full mx-auto p-5 sm:p-8 flex flex-col items-center justify-center text-center">
      <div role="alert" className="flex flex-col items-center">
        <AlertCircle size={40} className="text-red-600 mb-4" aria-hidden />
        <h1 className="text-2xl font-bold text-ink-900 mb-2">{titulo}</h1>
        <p className="text-ink-600 text-[17px] mb-8">{mensagem}</p>
      </div>
      {onTentar && <ButtonPrimary onClick={onTentar} className="sm:w-auto">Tentar de novo</ButtonPrimary>}
      {children}
    </main>
  )
}