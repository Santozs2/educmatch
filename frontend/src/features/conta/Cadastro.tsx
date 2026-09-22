import { useState, type ComponentProps, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'
import { ButtonPrimary } from '../../components/ui/Button'
import { errosDeCampo } from '../../lib/api'
import { useSessao } from '../../lib/sessao'
import { destinoSeguro, useConcluirInteressePendente } from './interesse'

const campo =
  'w-full border-2 border-line-200 rounded-[8px] p-3 min-h-[48px] text-[17px] focus:border-red-600 focus:ring-0 outline-none aria-[invalid=true]:border-red-600'

export function Cadastro() {
  const navegar = useNavigate()
  const [params] = useSearchParams()
  const { logado, cadastrar } = useSessao()
  const concluirPendente = useConcluirInteressePendente()

  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [erro, setErro] = useState('')
  const [campos, setCampos] = useState<Record<string, string>>({})
  const [enviando, setEnviando] = useState(false)

  const destino = destinoSeguro(params.get('next'))
  if (logado && !enviando) return <Navigate to={destino} replace />

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault()
    if (!email.trim() || !senha) return setErro('Preencha e-mail e senha para criar sua conta.')
    if (senha !== confirmacao) {
      setCampos({ confirmacao: 'As senhas não são iguais.' })
      return setErro('Confira os campos destacados.')
    }
    setEnviando(true)
    setErro('')
    setCampos({})
    try {
      await cadastrar({ nome: nome.trim(), email: email.trim(), senha })
      const salvouInteresse = await concluirPendente()
      navegar(salvouInteresse ? '/meus-interesses' : destino, { replace: true })
    } catch (falha) {
      setCampos(errosDeCampo(falha))
      setErro(falha instanceof Error ? falha.message : 'Não foi possível criar a conta.')
      setEnviando(false)
    }
  }

  const campoCom = (id: string, rotulo: string, props: ComponentProps<'input'>) => (
    <div className="mb-4">
      <label htmlFor={id} className="block font-semibold text-ink-900 mb-2">{rotulo}</label>
      <input id={id} {...props} aria-invalid={Boolean(campos[id])} aria-describedby={campos[id] ? `${id}-erro` : undefined} className={campo} />
      {campos[id] && <p id={`${id}-erro`} className="mt-1 text-sm text-red-700">{campos[id]}</p>}
    </div>
  )

  return (
    <main className="flex-1 max-w-[1440px] w-full mx-auto p-5 sm:p-8 flex flex-col items-center justify-center">
      <form onSubmit={enviar} noValidate className="max-w-[440px] w-full bg-white rounded-[12px] p-6 sm:p-10 shadow-[0_8px_24px_rgba(16,24,40,0.08)]">
        <h1 className="text-2xl font-bold text-red-900 mb-2">Crie sua conta</h1>
        <p className="text-ink-600 mb-6">Leva um minuto, e sua lista de interesse fica salva.</p>

        {erro && (
          <div role="alert" className="mb-5 flex items-start gap-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-900">
            <AlertCircle size={19} className="mt-0.5 shrink-0" />
            <span className="font-semibold">{erro}</span>
          </div>
        )}

        {campoCom('nome', 'Nome (opcional)', { type: 'text', autoComplete: 'given-name', value: nome, onChange: (e) => setNome(e.target.value) })}
        {campoCom('email', 'E-mail', { type: 'email', autoComplete: 'email', value: email, onChange: (e) => setEmail(e.target.value) })}
        {campoCom('senha', 'Senha', { type: 'password', autoComplete: 'new-password', value: senha, onChange: (e) => setSenha(e.target.value) })}
        {campoCom('confirmacao', 'Confirme a senha', { type: 'password', autoComplete: 'new-password', value: confirmacao, onChange: (e) => setConfirmacao(e.target.value) })}

        <div className="flex flex-col gap-3 mt-6">
          <ButtonPrimary type="submit" disabled={enviando}>{enviando ? 'Criando…' : 'Criar conta'}</ButtonPrimary>
          <Link to={`/entrar${params.get('next') ? `?next=${encodeURIComponent(params.get('next')!)}` : ''}`} className="font-bold rounded-xl min-h-[56px] px-8 flex items-center justify-center text-red-600 hover:bg-red-50">
            Já tenho conta
          </Link>
        </div>
      </form>
    </main>
  )
}