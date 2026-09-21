import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { Check } from 'lucide-react'

const Contexto = createContext<(mensagem: string) => void>(() => {})

export function ToastProvider({ children }: { children: ReactNode }) {
  const [mensagem, setMensagem] = useState<string | null>(null)

  const mostrar = useCallback((texto: string) => {
    setMensagem(texto)
    setTimeout(() => setMensagem(null), 2000)
  }, [])

  return (
    <Contexto.Provider value={mostrar}>
      {children}
      {mensagem && (
        <div
          role="status"
          aria-live="polite"
          className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-ink-900 text-white px-6 py-3 rounded-[8px] shadow-lg font-semibold flex items-center gap-2 animate-in fade-in slide-in-from-bottom-4 z-50"
        >
          <Check size={20} className="text-red-600" />
          {mensagem}
        </div>
      )}
    </Contexto.Provider>
  )
}

export const useToast = () => useContext(Contexto)