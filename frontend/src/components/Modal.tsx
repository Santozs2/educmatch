import { useEffect, type ReactNode } from 'react'

interface Props {
  titulo: string
  icone?: ReactNode
  onFechar: () => void
  children: ReactNode
  acoes?: ReactNode
}

export function Modal({ titulo, icone, onFechar, children, acoes }: Props) {
  useEffect(() => {
    const aoTeclar = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') onFechar()
    }
    document.addEventListener('keydown', aoTeclar)
    return () => document.removeEventListener('keydown', aoTeclar)
  }, [onFechar])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={onFechar}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        onClick={(evento) => evento.stopPropagation()}
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 sm:p-8 animate-in zoom-in-95 duration-200"
      >
        <div className="flex items-center gap-3 mb-4">
          {icone && (
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center shrink-0">
              {icone}
            </div>
          )}
          <h2 className="text-xl font-bold text-ink-900">{titulo}</h2>
        </div>
        {children}
        {acoes && <div className="flex flex-col sm:flex-row gap-3 mt-8">{acoes}</div>}
      </div>
    </div>
  )
}