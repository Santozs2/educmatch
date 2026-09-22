import { createContext, useContext, useEffect, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ErroApi, garantirCsrf } from './api'
import { chaves } from './queries'
import type { DadosCadastro, Usuario } from './tipos'

interface Sessao {
  carregando: boolean
  usuario: Usuario | null
  logado: boolean
  admin: boolean
  entrar: (email: string, senha: string) => Promise<Usuario>
  cadastrar: (dados: DadosCadastro) => Promise<Usuario>
  sair: () => Promise<void>
}

const Contexto = createContext<Sessao | null>(null)

async function buscarEu(): Promise<Usuario | null> {
  try {
    return await api<Usuario>('/auth/eu/')
  } catch (erro) {
    if (erro instanceof ErroApi && erro.status === 401) return null
    throw erro
  }
}

export function SessaoProvider({ children }: { children: ReactNode }) {
  const cliente = useQueryClient()
  const eu = useQuery({ queryKey: chaves.eu, queryFn: buscarEu, staleTime: Infinity })

  useEffect(() => {
    garantirCsrf().catch(() => {}) 
  }, [])

  const aoEntrar = (usuario: Usuario) => {
    cliente.setQueryData(chaves.eu, usuario)
    cliente.invalidateQueries({ queryKey: chaves.tentativas })
    cliente.invalidateQueries({ queryKey: chaves.interesses })
    return usuario
  }

  const valor: Sessao = {
    carregando: eu.isPending,
    usuario: eu.data ?? null,
    logado: Boolean(eu.data),
    admin: Boolean(eu.data?.is_superuser),
    entrar: (email, senha) =>
      api<Usuario>('/auth/entrar/', { method: 'POST', body: JSON.stringify({ email, senha }) }).then(aoEntrar),
    cadastrar: (dados) =>
      api<Usuario>('/auth/cadastro/', { method: 'POST', body: JSON.stringify(dados) }).then(aoEntrar),
    sair: async () => {
      await api<void>('/auth/sair/', { method: 'POST' })
      cliente.setQueryData(chaves.eu, null)
      cliente.removeQueries({ queryKey: chaves.interesses })
      cliente.removeQueries({ queryKey: chaves.tentativas })
      cliente.removeQueries({ queryKey: ['quiz', 'tentativa'] })
      try {
        sessionStorage.clear()
      } catch {
      }
    },
  }

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useSessao(): Sessao {
  const valor = useContext(Contexto)
  if (!valor) throw new Error('useSessao precisa estar dentro de <SessaoProvider>')
  return valor
}