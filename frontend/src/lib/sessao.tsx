import { createContext, useContext, useState, type ReactNode } from 'react'

interface Sessao {
  logado: boolean
  admin: boolean
  interesses: number[]
  entrar: (comoAdmin?: boolean) => void
  sair: () => void
}

const Contexto = createContext<Sessao | null>(null)

export function SessaoProvider({ children }: { children: ReactNode }) {
  const [logado, setLogado] = useState(false)
  const [admin, setAdmin] = useState(false)
  const [interesses, setInteresses] = useState<number[]>([])

  const valor: Sessao = {
    logado,
    admin,
    interesses,
    entrar: (comoAdmin = false) => {
      setLogado(true)
      setAdmin(comoAdmin)
    },
    sair: () => {
      setLogado(false)
      setAdmin(false)
      setInteresses([])
    },
  }

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useSessao(): Sessao {
  const valor = useContext(Contexto)
  if (!valor) throw new Error('useSessao precisa estar dentro de <SessaoProvider>')
  return valor
}