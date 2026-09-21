import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowRight, BookOpen, Check, Printer, RefreshCw } from 'lucide-react'
import { ButtonGhost, ButtonPrimary, ButtonSecondary } from '../../components/ui/Button'
import { Carregando, EstadoErro } from '../../components/Estado'
import { ErroApi } from '../../lib/api'
import { horas } from '../../lib/formatters'
import { idDaUrl, useTentativa } from '../../lib/queries'
import { ModalRefazer } from './ModalRefazer'
import { limparRascunho } from './rascunho'

const RAIO = 58
const CIRCUNFERENCIA = 2 * Math.PI * RAIO 

export function Resultado() {
  const navegar = useNavigate()
  const tentativaId = idDaUrl(useParams().id)
  const consulta = useTentativa(tentativaId)
  const [refazer, setRefazer] = useState(false)

  if (tentativaId === null || (consulta.error instanceof ErroApi && consulta.error.status === 404)) {
    return (
      <EstadoErro
        titulo="Resultado não encontrado"
        mensagem="Este resultado não existe ou foi feito em outro navegador. Entre na sua conta para ver o seu histórico."
      >
        <ButtonPrimary onClick={() => navegar('/')} className="sm:w-auto mt-3">Fazer o teste</ButtonPrimary>
      </EstadoErro>
    )
  }
  if (consulta.isPending) return <Carregando texto="Carregando seu resultado…" />
  if (consulta.isError) {
    return <EstadoErro titulo="Não deu para abrir o resultado" mensagem={consulta.error.message} onTentar={() => consulta.refetch()} />
  }

  const data = consulta.data
  const [destaque, ...outros] = data.recomendacoes
  if (!destaque) {
    return <EstadoErro titulo="Nenhum curso disponível" mensagem="Não há cursos ativos no catálogo neste momento." />
  }

  const verCurso = (cursoId: number) => navegar(`/curso/${cursoId}?tentativa=${data.tentativa_id}`)
  const nome = data.respondido_por

  return (
    <main className="flex-1 max-w-[800px] w-full mx-auto p-5 sm:p-8 flex flex-col">
      <h1 className="text-3xl font-bold text-red-900 mb-6 leading-tight">
        {nome ? `${nome}, esses` : 'Esses'} são os cursos que mais combinam com você
      </h1>

      {data.confidence_band === 'baixa' && (
        <p className="mb-6 rounded-lg border border-line-200 bg-ink-50 p-4 text-ink-600">
          Seu perfil ficou dividido: os primeiros cursos estão muito próximos entre si. Vale olhar os três com calma.
        </p>
      )}

      <div className="bg-white rounded-2xl border-2 border-ink-900 overflow-hidden mb-10 shadow-lg transition-all hover:shadow-xl">
        <div className="bg-ink-900 p-3 flex items-center justify-center border-b-2 border-ink-900">
          <span className="bg-white text-ink-900 font-bold px-4 py-1 rounded-full uppercase text-sm tracking-wide flex items-center gap-2">
            <Check size={16} className="text-red-600" /> Melhor combinação
          </span>
        </div>

        <div className="p-6 sm:p-8 flex flex-col sm:flex-row gap-8 items-center sm:items-start">
          <div className="flex flex-col items-center shrink-0">
            <div className="relative w-[140px] h-[140px] flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90 drop-shadow-sm" viewBox="0 0 140 140" aria-hidden>
                <circle cx="70" cy="70" r={RAIO} fill="transparent" stroke="var(--color-line-200)" strokeWidth="12" />
                <circle
                  cx="70" cy="70" r={RAIO} fill="transparent" stroke="var(--color-red-600)" strokeWidth="12"
                  strokeDasharray={CIRCUNFERENCIA}
                  strokeDashoffset={CIRCUNFERENCIA * (1 - destaque.match / 100)}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-white rounded-full m-[12px] shadow-[inset_0_2px_4px_rgba(0,0,0,0.06)]">
                <span className="text-4xl font-bold text-ink-900 leading-none tracking-tight">{destaque.match}%</span>
              </div>
            </div>
            <span className="text-ink-600 font-medium mt-4 text-center text-sm uppercase tracking-wider">De afinidade</span>
          </div>

          <div className="flex-1">
            <h2 className="text-2xl sm:text-3xl font-bold text-ink-900 mb-2">{destaque.curso.nome_curso}</h2>
            <p className="text-ink-600 text-[17px] mb-4">{destaque.curso.descricao}</p>

            <div className="flex flex-wrap gap-2 mb-6">
              <span className="bg-red-100 text-red-900 px-3 py-1 rounded-full text-sm font-semibold">
                {destaque.curso.area_principal.nome}
              </span>
              <span className="bg-white border border-line-200 text-ink-600 px-3 py-1 rounded-full text-sm font-semibold flex items-center gap-1">
                <BookOpen size={14} /> {horas(destaque.curso.duracao)}
              </span>
            </div>

            {destaque.explicacao.top_areas.length > 0 && (
              <div className="bg-white rounded-lg p-4 border border-line-200">
                <h3 className="font-bold text-ink-900 mb-3">Por que este curso?</h3>
                <div className="flex flex-col gap-3">
                  {destaque.explicacao.top_areas.map((area) => (
                    <div key={area.area}>
                      <div className="flex justify-between text-sm font-semibold mb-1">
                        <span className="text-ink-900">{area.area_name}</span>
                        <span className="text-red-700">{Math.round(area.percentual)}%</span>
                      </div>
                      <div className="h-2 w-full bg-red-100 rounded-full overflow-hidden">
                        <div className="h-full bg-red-600 rounded-full" style={{ width: `${area.percentual}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-6">
              <ButtonPrimary onClick={() => verCurso(destaque.curso.id)}>Ver detalhes do curso</ButtonPrimary>
            </div>
          </div>
        </div>
      </div>

      {outros.length > 0 && (
        <>
          <h2 className="text-xl font-bold text-ink-900 mb-4">Também combinam com você</h2>
          <div className="flex flex-col gap-4 mb-8">
            {outros.map((rec) => (
              <div key={rec.curso.id} className="bg-white rounded-[12px] border border-line-200 p-4 sm:p-5 flex flex-col sm:flex-row gap-4 sm:items-center hover:border-red-300 transition-colors">
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-8 h-8 rounded-full bg-red-100 text-red-900 font-bold flex items-center justify-center shrink-0">{rec.rank}</div>
                  <div>
                    <h3 className="font-bold text-ink-900 text-lg leading-tight">{rec.curso.nome_curso}</h3>
                    <p className="text-ink-600 text-sm line-clamp-1 mt-1">{rec.curso.descricao}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between sm:justify-end gap-6 border-t sm:border-t-0 pt-4 sm:pt-0 border-line-200 mt-2 sm:mt-0">
                  <span className="bg-red-100 text-red-900 px-2 py-1 rounded text-xs font-semibold">{rec.curso.area_principal.nome}</span>
                  <div className="flex flex-col items-end shrink-0 w-[80px]">
                    <span className="font-bold text-ink-900 tabular-nums">{rec.match}%</span>
                    <div className="h-1.5 w-full bg-line-200 rounded-full mt-1 overflow-hidden">
                      <div className="h-full bg-ink-900 rounded-full" style={{ width: `${rec.match}%` }} />
                    </div>
                  </div>
                  <button
                    onClick={() => verCurso(rec.curso.id)}
                    className="min-w-[48px] min-h-[48px] flex items-center justify-center text-red-600 hover:bg-red-50 rounded"
                    aria-label={`Ver o curso ${rec.curso.nome_curso}`}
                  >
                    <ArrowRight size={24} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="flex flex-col sm:flex-row gap-4 pb-12 print:hidden">
        <ButtonSecondary onClick={() => setRefazer(true)}>
          <RefreshCw size={18} className="mr-2" /> Refazer o teste
        </ButtonSecondary>
        <ButtonGhost onClick={() => window.print()}>
          <Printer size={20} className="mr-2" /> Imprimir ou salvar em PDF
        </ButtonGhost>
      </div>

      {refazer && (
        <ModalRefazer
          onConfirmar={() => { limparRascunho(); navegar('/') }}
          onCancelar={() => setRefazer(false)}
        />
      )}
    </main>
  )
}