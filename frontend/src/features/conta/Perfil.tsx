import { useMinhasTentativas, useInteresses } from '../../lib/queries'
import { useSessao } from '../../lib/sessao'
import { CascaConta } from './CascaConta'

export function Perfil() {
  const { usuario } = useSessao()
  const tentativas = useMinhasTentativas()
  const interesses = useInteresses()
  const nome = usuario?.nome || usuario?.email || ''

  const numero = (valor: number | undefined) => (valor === undefined ? '—' : String(valor))

  return (
    <CascaConta titulo="Meu perfil" subtitulo="Os dados da sua conta.">
      <div className="max-w-[620px] rounded-2xl border border-line-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="mb-7 flex items-center gap-4">
          <div className="grid h-16 w-16 place-items-center rounded-full bg-ink-900 text-xl font-bold text-white" aria-hidden>
            {nome.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="font-bold text-ink-900">{usuario?.nome || 'Sem nome cadastrado'}</p>
            <p className="text-sm text-ink-500">{usuario?.email}</p>
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-4">
          <div className="rounded-xl border border-line-200 bg-ink-50 p-4">
            <dt className="text-sm text-ink-500">Testes feitos</dt>
            <dd className="text-3xl font-bold text-ink-900">{numero(tentativas.data?.length)}</dd>
          </div>
          <div className="rounded-xl border border-line-200 bg-ink-50 p-4">
            <dt className="text-sm text-ink-500">Cursos na lista</dt>
            <dd className="text-3xl font-bold text-ink-900">{numero(interesses.data?.length)}</dd>
          </div>
        </dl>
      </div>
    </CascaConta>
  )
}