import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'
import { ButtonPrimary } from '../../components/ui/Button'
import { errosDeCampo } from '../../lib/api'
import { useSessao } from '../../lib/sessao'
import { destinoSeguro, useConcluirInteressePendente } from './interesse'

const campo =
  'w-full border-2 border-line-200 rounded-[8px] p-3 min-h-[48px] text-[17px] focus:border-red-600 focus:ring-0 outline-none aria-[invalid=true]:border-red-600'

export function Entrar() {
  const navegar = useNavigate()
  const [params] = useSearchParams()
  const { logado, entrar } = useSessao()
  const concluirPendente = useConcluirInteressePendente()

  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [campos, setCampos] = useState<Record<string, string>>({})
  const [enviando, setEnviando] = useState(false)

  const next = params.get('next')
  const destino = destinoSeguro(next)

  if (logado && !enviando) return <Navigate to={destino} replace />

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault()
    if (!email.trim() || !senha) {
      setErro('Preencha e-mail e senha para continuar.')
      return
    }
    setEnviando(true)
    setErro('')
    setCampos({})
    try {
      await entrar(email.trim(), senha)
      const salvouInteresse = await concluirPendente()
      navegar(salvouInteresse ? '/meus-interesses' : destino, { replace: true })
    } catch (falha) {
      setCampos(errosDeCampo(falha))
      setErro(falha instanceof Error ? falha.message : 'Não foi possível entrar.')
      setEnviando(false)
    }
  }

  return (
    <main className="flex-1 max-w-[1440px] w-full mx-auto p-5 sm:p-8 flex flex-col items-center justify-center">
      <form onSubmit={enviar} noValidate className="max-w-[400px] w-full bg-white rounded-[12px] p-6 sm:p-10 shadow-[0_8px_24px_rgba(16,24,40,0.08)]">
        <h1 className="text-2xl font-bold text-red-900 mb-2">Entre na sua conta</h1>
        <p className="text-ink-600 mb-6">Para salvar seu interesse, precisamos saber quem é você.</p>

        {erro && (
          <div role="alert" className="mb-5 flex items-start gap-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-900">
            <AlertCircle size={19} className="mt-0.5 shrink-0" />
            <span className="font-semibold">{erro}</span>
          </div>
        )}

        <div className="mb-4">
          <label htmlFor="email" className="block font-semibold text-ink-900 mb-2">E-mail</label>
          <input
            id="email" type="email" autoComplete="email" value={email}
            onChange={(e) => setEmail(e.target.value)}
            aria-invalid={Boolean(campos.email)}
            aria-describedby={campos.email ? 'email-erro' : undefined}
            className={campo}
          />
          {campos.email && <p id="email-erro" className="mt-1 text-sm text-red-700">{campos.email}</p>}
        </div>

        <div className="mb-8">
          <label htmlFor="senha" className="block font-semibold text-ink-900 mb-2">Senha</label>
          <input
            id="senha" type="password" autoComplete="current-password" value={senha}
            onChange={(e) => setSenha(e.target.value)}
            aria-invalid={Boolean(campos.senha || erro)}
            className={campo}
          />
        </div>

        <div className="flex flex-col gap-3">
          <ButtonPrimary type="submit" disabled={enviando}>{enviando ? 'Entrando…' : 'Entrar'}</ButtonPrimary>
          <Link
            to={next ? `/cadastro?next=${encodeURIComponent(next)}` : '/cadastro'}
            className="font-bold rounded-xl min-h-[56px] px-8 flex items-center justify-center text-red-600 hover:bg-red-50"
          >
            Cadastrar-se
          </Link>
        </div>
      </form>
    </main>
  )
}