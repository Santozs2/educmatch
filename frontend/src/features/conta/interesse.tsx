import { useLocation, useNavigate } from 'react-router-dom'
import { useToast } from '../../components/Toast'
import { useCriarInteresse } from '../../lib/queries'
import { useSessao } from '../../lib/sessao'

const CHAVE = 'educmatch.interessePendente'

interface Pendente {
  curso: number
  tentativa: number | null
}

function lerPendente(): Pendente | null {
  try {
    const bruto = sessionStorage.getItem(CHAVE)
    return bruto ? (JSON.parse(bruto) as Pendente) : null
  } catch {
    return null
  }
}

function guardarPendente(pendente: Pendente) {
  try {
    sessionStorage.setItem(CHAVE, JSON.stringify(pendente))
  } catch {
  }
}

function limparPendente() {
  try {
    sessionStorage.removeItem(CHAVE)
  } catch {
  }
}

export function destinoSeguro(next: string | null): string {
  return next && next.startsWith('/') && !next.startsWith('//') ? next : '/'
}
export function useManifestarInteresse() {
  const { logado } = useSessao()
  const navegar = useNavegarParaEntrar()
  const irPara = useNavigate()
  const criar = useCriarInteresse()
  const mostrarToast = useToast()

  const manifestar = (curso: number, tentativa: number | null) => {
    if (!logado) {
      guardarPendente({ curso, tentativa })
      navegar()
      return
    }
    criar.mutate(
      { curso, tentativa },
      {
        onSuccess: () => {
          mostrarToast('Curso adicionado à lista!')
          irPara('/meus-interesses')
        },
        onError: (erro) => mostrarToast(erro.message),
      },
    )
  }

  return { manifestar, salvando: criar.isPending }
}

function useNavegarParaEntrar() {
  const irPara = useNavigate()
  const local = useLocation()
  return () => irPara(`/entrar?next=${encodeURIComponent(local.pathname + local.search)}`)
}
export function useConcluirInteressePendente() {
  const criar = useCriarInteresse()
  const mostrarToast = useToast()

  return async (): Promise<boolean> => {
    const pendente = lerPendente()
    if (!pendente) return false
    limparPendente() 
    try {
      await criar.mutateAsync(pendente)
      mostrarToast('Curso adicionado à lista!')
      return true
    } catch {
      mostrarToast('Não deu para salvar o interesse. Tente de novo pela página do curso.')
      return false
    }
  }
}