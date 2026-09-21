import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, Check, ChevronLeft } from 'lucide-react'
import { ButtonPrimary } from '../../components/ui/Button'
import { Carregando, EstadoErro } from '../../components/Estado'
import { useEnviarQuiz, useQuestoes } from '../../lib/queries'
import { Calculando } from './Calculando'
import { lerRascunho, limparRascunho, salvarRascunho } from './rascunho'

const AUTO_AVANCO_MS = 320

export function Wizard() {
  const navegar = useNavigate()
  const questoes = useQuestoes()
  const enviar = useEnviarQuiz()
  const [rascunho, setRascunho] = useState(lerRascunho)
  const [semEscolha, setSemEscolha] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined)

  useEffect(() => salvarRascunho(rascunho), [rascunho])
  useEffect(() => () => clearTimeout(timer.current), [])

  if (questoes.isPending) return <Carregando texto="Carregando as perguntas…" />
  if (questoes.isError) {
    return <EstadoErro titulo="Não deu para carregar o quiz" mensagem={questoes.error.message} onTentar={() => questoes.refetch()} />
  }
  if (enviar.isPending) return <Calculando />

  const lista = questoes.data
  const total = lista.length
  const passo = Math.min(rascunho.passo, total - 1) 
  const questao = lista[passo]
  const marcada = rascunho.respostas[questao.id]
  const ultima = passo === total - 1

  const irPara = (novo: number) => {
    clearTimeout(timer.current)
    setSemEscolha(false)
    setRascunho((atual) => ({ ...atual, passo: novo }))
  }

  const escolher = (alternativaId: number) => {
    setSemEscolha(false)
    setRascunho((atual) => ({ ...atual, respostas: { ...atual.respostas, [questao.id]: alternativaId } }))
    clearTimeout(timer.current)
    if (!ultima) timer.current = setTimeout(() => irPara(passo + 1), AUTO_AVANCO_MS)
  }

  const concluir = () => {
    const pendente = lista.findIndex((q) => rascunho.respostas[q.id] === undefined)
    if (pendente !== -1) {
      irPara(pendente)
      setSemEscolha(true)
      return
    }
    enviar.mutate(
      {
        respondido_por: rascunho.nome,
        questionario_link: rascunho.link,
        respostas: lista.map((q) => ({ questao: q.id, alternativa: rascunho.respostas[q.id] })),
      },
      {
        onSuccess: (tentativa) => {
          limparRascunho()
          navegar(`/resultado/${tentativa.tentativa_id}`, { replace: true })
        },
      },
    )
  }

  const avancar = () => {
    if (marcada === undefined) return setSemEscolha(true)
    if (ultima) return concluir()
    irPara(passo + 1)
  }

  const voltar = () => (passo === 0 ? navegar('/') : irPara(passo - 1))

  return (
    <div className="flex-1 bg-white flex flex-col pb-24">
      <div className="bg-white border-b border-line-200">
        <div
          className="h-2 w-full bg-red-100"
          role="progressbar"
          aria-valuemin={1}
          aria-valuemax={total}
          aria-valuenow={passo + 1}
          aria-label="Progresso do quiz"
        >
          <div className="h-full bg-red-600 transition-all duration-300" style={{ width: `${((passo + 1) / total) * 100}%` }} />
        </div>
        <div className="max-w-[1440px] mx-auto p-4 flex items-center">
          <button onClick={voltar} className="flex items-center text-red-600 font-semibold min-h-[48px] px-2 hover:bg-red-50 rounded">
            <ChevronLeft size={20} className="mr-1" /> Voltar
          </button>
          <span className="mx-auto font-semibold text-ink-600 pr-[88px] sm:pr-0">
            Pergunta {passo + 1} de {total}
          </span>
        </div>
      </div>

      <main className="flex-1 max-w-[600px] w-full mx-auto p-5 sm:p-8 flex flex-col">
        {semEscolha && (
          <div role="alert" className="bg-red-50 border border-red-300 rounded-lg p-4 mb-6 flex items-start gap-3 text-ink-900">
            <AlertCircle className="text-red-600 mt-0.5 shrink-0" size={20} />
            <span className="font-semibold">Escolha uma opção para continuar.</span>
          </div>
        )}

        {enviar.error && (
          <div role="alert" className="bg-red-50 border border-red-300 rounded-lg p-4 mb-6 flex items-start gap-3 text-ink-900">
            <AlertCircle className="text-red-600 mt-0.5 shrink-0" size={20} />
            <span className="font-semibold">
              {enviar.error.message} Suas respostas estão guardadas — é só tentar de novo.
            </span>
          </div>
        )}

        <h2 className="text-2xl font-bold text-ink-900 mb-8 leading-tight">
          <span className="text-red-600 mr-2">{passo + 1}.</span>
          {questao.texto}
        </h2>

        <div className="flex flex-col gap-4">
          {questao.alternativas.map((alternativa, indice) => {
            const escolhida = marcada === alternativa.id
            return (
              <button
                key={alternativa.id}
                onClick={() => escolher(alternativa.id)}
                aria-pressed={escolhida}
                className={`flex items-center text-left p-5 rounded-xl min-h-[72px] border-2 transition-all duration-200 group ${
                  escolhida
                    ? 'border-red-600 bg-red-50 shadow-sm ring-1 ring-red-600'
                    : 'border-line-200 bg-white hover:border-red-300 hover:shadow-md hover:-translate-y-0.5'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mr-4 font-bold transition-colors ${
                  escolhida ? 'bg-red-600 text-white' : 'bg-line-200 text-ink-600 group-hover:bg-red-100 group-hover:text-red-900'
                }`}>
                  {indice + 1}
                </div>
                <span className={`flex-1 text-[17px] leading-snug ${escolhida ? 'font-bold text-red-900' : 'text-ink-900'}`}>
                  {alternativa.texto}
                </span>
                <div className="w-6 h-6 ml-2 flex items-center justify-center shrink-0">
                  {escolhida && <Check className="text-red-600" size={24} />}
                </div>
              </button>
            )
          })}
        </div>
      </main>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-line-200 shadow-[0_-4px_16px_rgba(0,0,0,0.05)]">
        <div className="max-w-[600px] mx-auto">
          <ButtonPrimary onClick={avancar}>{ultima ? 'Ver meu resultado' : 'Próxima'}</ButtonPrimary>
        </div>
      </div>
    </div>
  )
}