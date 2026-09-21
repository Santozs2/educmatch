import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ChevronLeft, MapPin, Phone } from 'lucide-react'
import { ButtonPrimary } from '../../components/ui/Button'
import { Carregando, EstadoErro } from '../../components/Estado'
import { ErroApi } from '../../lib/api'
import { CONTATO_SECRETARIA } from '../../lib/config'
import { horas } from '../../lib/formatters'
import { idDaUrl, useCurso, useTentativa } from '../../lib/queries'

export function DetalheCurso() {
  const navegar = useNavigate()
  const cursoId = idDaUrl(useParams().id)
  const tentativaId = idDaUrl(useSearchParams()[0].get('tentativa'))

  const tentativa = useTentativa(tentativaId)
  const rec = tentativa.data?.recomendacoes.find((r) => r.curso.id === cursoId)
  const curso = useCurso(cursoId, rec?.curso)

  if (cursoId === null || (curso.error instanceof ErroApi && curso.error.status === 404)) {
    return <EstadoErro titulo="Curso não encontrado" mensagem="Este curso não existe ou não está mais disponível." />
  }
  if (curso.isPending) return <Carregando />
  if (curso.isError) return <EstadoErro titulo="Não deu para abrir o curso" mensagem={curso.error.message} onTentar={() => curso.refetch()} />

  const dados = curso.data
  const temContato = CONTATO_SECRETARIA.endereco || CONTATO_SECRETARIA.telefone

  return (
    <main className="flex-1 max-w-[800px] w-full mx-auto p-5 sm:p-8 flex flex-col">
      <button onClick={() => navegar(-1)} className="mb-4 self-start flex items-center font-semibold min-h-[48px] px-2 hover:bg-red-50 rounded text-red-700">
        <ChevronLeft size={20} className="mr-1" /> Voltar
      </button>

      <div className="bg-white rounded-[12px] border border-line-200 overflow-hidden mb-8 shadow-sm">
        <div className="p-6 sm:p-8 border-b border-line-200 bg-ink-900 text-white">
          <div className="flex flex-wrap gap-2 mb-4">
            <span className="bg-red-700 text-red-100 px-3 py-1 rounded-full text-sm font-semibold">{dados.area_principal.nome}</span>
            <span className="bg-white/10 text-white border border-white/20 px-3 py-1 rounded-full text-sm font-semibold">{horas(dados.duracao)}</span>
          </div>
          <h1 className="text-3xl font-bold mb-4">{dados.nome_curso}</h1>
          <p className="text-red-100 text-[17px] leading-relaxed max-w-[600px]">{dados.descricao}</p>
        </div>

        <div className="p-6 sm:p-8">
          {rec && (
            <div className="bg-red-50 rounded-lg p-5 border border-red-100 flex items-center justify-between mb-8">
              <div>
                <h2 className="font-bold text-red-900 mb-1">Sua afinidade</h2>
                <p className="text-red-700 text-sm">Baseado nas suas respostas · {rec.rank}º lugar</p>
              </div>
              <div className="text-3xl font-bold text-red-700">{rec.match}%</div>
            </div>
          )}
          <ButtonPrimary onClick={() => navegar('/entrar')}>Manifestar interesse neste curso</ButtonPrimary>
        </div>
      </div>

      {temContato && (
        <div className="bg-white rounded-[12px] border border-line-200 p-6 sm:p-8 mb-12 shadow-sm">
          <h2 className="text-xl font-bold text-ink-900 mb-4">Falar com a secretaria da escola</h2>
          <div className="flex flex-col sm:flex-row gap-6">
            {CONTATO_SECRETARIA.endereco && (
              <div className="flex items-start gap-3 flex-1">
                <MapPin className="text-red-600 shrink-0 mt-1" aria-hidden />
                <div>
                  <h3 className="font-bold text-ink-900">Endereço</h3>
                  <p className="text-ink-600 text-sm mt-1 whitespace-pre-line">{CONTATO_SECRETARIA.endereco}</p>
                </div>
              </div>
            )}
            {CONTATO_SECRETARIA.telefone && (
              <div className="flex items-start gap-3 flex-1">
                <Phone className="text-red-600 shrink-0 mt-1" aria-hidden />
                <div>
                  <h3 className="font-bold text-ink-900">Telefone / WhatsApp</h3>
                  <p className="text-ink-600 text-sm mt-1">{CONTATO_SECRETARIA.telefone}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  )
}