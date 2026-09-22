import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Carregando } from './Estado'
import { useSessao } from '../lib/sessao'

export function ExigeLogin({ children, admin = false }: { children: ReactNode; admin?: boolean }) {
  const { carregando, logado, admin: ehAdmin } = useSessao()
  const local = useLocation()

  if (carregando) return <Carregando /> 
  if (!logado) {
    const volta = encodeURIComponent(local.pathname + local.search)
    return <Navigate to={`/entrar?next=${volta}`} replace />
  }
  if (admin && !ehAdmin) return <Navigate to="/" replace />
  return children
}