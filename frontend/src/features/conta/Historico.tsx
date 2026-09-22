import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, History } from 'lucide-react'
import { Carregando, EstadoErro } from '../../components/Estado'
import { ButtonPrimary } from '../../components/ui/Button'
import { dataCurta } from '../../lib/formatters'
import { useMinhasTentativas } from '../../lib/queries'
import { CascaConta } from './CascaConta'

export function Historico() {
  const navegar = useNavigate()
  const tentativas = useMinhasTentativas()

  const conteudo = () => {
    if (tentativas.isPending) return <Carregando />
    if (tentativas.isError) return <EstadoErro titulo="Não deu para abrir o histórico" mensagem={tentativas.error.message} onTentar={() => tentativas.refetch()} />
    if (tentativas.data.length === 0) {
      return (
        <div className="max-w-[600px] rounded-2xl border border-line-200 bg-white p-10 text-center shadow-sm">
          <History className="mx-auto mb-4 text-red-600" size={36} />
          <h2 className="text-xl font-bold text-ink-900">Ainda não há testes por aqui</h2>
          <p className="mt-2 text-ink-600">Quando você concluir o quiz, o resultado aparece neste espaço.</p>
          <ButtonPrimary onClick={() => navegar('/')} className="mx-auto mt-6 sm:w-auto">Fazer meu primeiro teste</ButtonPrimary>
        </div>
      )
    }
    return (
      <ul className="flex max-w-[720px] flex-col gap-4">
        {tentativas.data.map((t) => (
          <li key={t.tentativa_id}>
            <Link
              to={`/resultado/${t.tentativa_id}`}
              className="flex items-center gap-4 rounded-2xl border border-line-200 bg-white p-5 shadow-sm hover:border-red-300"
            >
              <div className="flex-1">
                <p className="text-xs font-bold uppercase tracking-[.16em] text-ink-500">{dataCurta(t.criado_em)}</p>
                <p className="mt-1 text-lg font-bold text-ink-900">{t.principal?.curso.nome_curso ?? 'Sem recomendação'}</p>
              </div>
              {t.principal && (
                <span className="text-2xl font-bold text-ink-900 tabular-nums">{t.principal.match}%</span>
              )}
              <ArrowRight className="text-red-600" aria-hidden />
            </Link>
          </li>
        ))}
      </ul>
    )
  }

  return (
    <CascaConta titulo="Meus testes" subtitulo="Cada teste que você fez, do mais recente ao mais antigo.">
      {conteudo()}
    </CascaConta>
  )
}