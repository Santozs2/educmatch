---
title: "Passo a passo — FE-06 a FE-10 (fluxo público na SPA)"
aliases: ["Passo a passo FE-06", "Fase 2 do front", "Quiz na SPA", "Fluxo público React"]
tags: [tcc, front, react, tanstack-query, execucao, passo-a-passo, quiz]
status: proposto
projeto: TCC
criado: 2026-09-21
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|🗂️ Plano]] · Vem depois de: [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|🔧 BK-01 a BK-08]] · Vem antes de: [[Projetos/EducMatch(Secretária)/passo-a-passo-fe-11-fe-15|👤 FE-11 a FE-15]]

# 🎯 Passo a passo — FE-06 a FE-10

> [!abstract] O que esta nota é
> O **como** da Fase 2: as quatro telas do fluxo público deixam o dado falso e passam a falar com `/api/v1/`. Ao fim, o TCC roda ponta a ponta na SPA — **quiz → engine → ranking explicado** —, que é o marco para mostrar à banca.
> Escrito contra o `frontend/` em `cc902fc` e o contrato da [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|Fase 0]].

> [!success] Compila — mas não foi clicado
> Em 2026-09-21, o código desta nota (junto com o das Fases 3 e 5) passou em `tsc --noEmit` e `vite build`. **Nenhum clique** foi feito: a seção 7 é o que prova que funciona.

## 🚦 Pré-requisitos — sem eles, pare

| | Checagem | Como ver |
|---|---|---|
| ✅ | Fase 1 fechada, **incluindo R1–R7** da [[Projetos/EducMatch(Secretária)/passo-a-passo-fe-01-fe-05#🔎 Revisão de 2026-09-21 — spec × código × backend|revisão]] — principalmente o `proxy` do `vite.config.ts` | `grep -n proxy frontend/vite.config.ts` |
| ✅ | Fase 0 mesclada: `/api/v1/` respondendo | `curl -s localhost:8000/api/v1/quiz/questoes/ \| head -c 200` |
| ✅ | Banco semeado | `python manage.py seed_areas && python manage.py seed_cursos && python manage.py seed_questoes` |
| ✅ | Os dois servidores de pé | `python manage.py runserver` (8000) e `pnpm dev` (5173) |

> [!important] Sempre pelo `localhost:5173`
> Abrir `localhost:8000` mostra os templates; abrir `127.0.0.1:5173` cria **outro** cookie de sessão (host diferente) e o resultado some. Todo teste desta nota é em `http://localhost:5173`.

---

## 1️⃣ A camada de dados — `lib/`

### `lib/tipos.ts` — acrescente

```ts
export interface RespostaEnviada {
  questao: number
  alternativa: number
}

export interface EnvioQuiz {
  respondido_por: string
  questionario_link: string | null
  respostas: RespostaEnviada[]
}
```

(`Tentativa` e `Usuario` já estão na forma revisada — `respondido_por`, `criado_em`, `nome`. Se o seu `tipos.ts` ainda tem `username`, a revisão E2/E3 da FE-03 não foi aplicada.)

### `lib/query.ts` — o `retry` passa a olhar o erro

```ts
import { QueryClient } from '@tanstack/react-query'
import { ErroApi } from './api'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // 4xx é resposta, não falha: repetir um 404 só atrasa a tela de "não encontrado".
      retry: (falhas, erro) => !(erro instanceof ErroApi && erro.status < 500) && falhas < 1,
    },
  },
})
```

> [!note] Por que isso não estava na FE-02
> Com `retry: 1` fixo, `/resultado/999` esperava a segunda tentativa (≈1 s de backoff) antes de mostrar o 404. Não dava para perceber antes de existir um 404 de verdade.

### `lib/queries.ts` — arquivo novo

O único lugar que conhece as URLs da API. Tela nenhuma chama `api()` direto.

```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api'
import type { Curso, EnvioQuiz, Questao, Tentativa } from './tipos'

export const chaves = {
  questoes: ['quiz', 'questoes'] as const,
  tentativa: (id: number) => ['quiz', 'tentativa', id] as const,
  curso: (id: number) => ['catalogo', 'curso', id] as const,
}

/** "12" → 12; "abc", "0", "-3", null → null. Toda rota com :id passa por aqui. */
export function idDaUrl(valor: string | null | undefined): number | null {
  const numero = Number(valor)
  return Number.isInteger(numero) && numero > 0 ? numero : null
}

export function useQuestoes() {
  return useQuery({
    queryKey: chaves.questoes,
    queryFn: () => api<Questao[]>('/quiz/questoes/'),
    staleTime: Infinity, // as perguntas não mudam durante uma visita
  })
}

export function useTentativa(id: number | null) {
  return useQuery({
    queryKey: chaves.tentativa(id ?? 0),
    queryFn: () => api<Tentativa>(`/quiz/tentativas/${id}/`),
    enabled: id !== null,
    staleTime: Infinity, // tentativa é imutável: voltar do detalhe nunca refaz a busca
  })
}

export function useCurso(id: number | null, inicial?: Curso) {
  return useQuery({
    queryKey: chaves.curso(id ?? 0),
    queryFn: () => api<Curso>(`/catalogo/cursos/${id}/`),
    enabled: id !== null,
    placeholderData: inicial, // o curso já veio dentro da recomendação: desenha na hora
  })
}

export function useEnviarQuiz() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (corpo: EnvioQuiz) =>
      api<Tentativa>('/quiz/tentativas/', { method: 'POST', body: JSON.stringify(corpo) }),
    onSuccess: (tentativa) => {
      // O 201 já é o payload do GET: /resultado/:id abre sem segunda requisição.
      cliente.setQueryData(chaves.tentativa(tentativa.tentativa_id), tentativa)
    },
  })
}
```

> [!important] `setQueryData` no `onSuccess` é o que torna o "calculando" honesto
> O `POST` devolve o mesmo JSON que o `GET /tentativas/<pk>/`. Guardando no cache com a chave do `GET`, a navegação para `/resultado/12` encontra o dado pronto: a tela de cálculo dura exatamente o tempo do servidor, nem um `setTimeout` a mais.

### `features/quiz/rascunho.ts` — arquivo novo

O quiz em andamento vive no `sessionStorage`, não no contexto:

```ts
const CHAVE = 'educmatch.quiz'

export interface Rascunho {
  nome: string
  passo: number
  respostas: Record<number, number> // questao.id → alternativa.id
  link: string | null // token do QuestionarioLink (FE-16)
}

const VAZIO: Rascunho = { nome: '', passo: 0, respostas: {}, link: null }

export function lerRascunho(): Rascunho {
  try {
    const bruto = sessionStorage.getItem(CHAVE)
    return bruto ? { ...VAZIO, ...JSON.parse(bruto) } : VAZIO
  } catch {
    return VAZIO // aba anônima com storage bloqueado, JSON corrompido: começa do zero
  }
}

export function salvarRascunho(rascunho: Rascunho) {
  try {
    sessionStorage.setItem(CHAVE, JSON.stringify(rascunho))
  } catch {
    /* sem storage o quiz funciona igual; só não sobrevive ao F5 */
  }
}

export function iniciarRascunho(nome: string, link: string | null) {
  salvarRascunho({ ...VAZIO, nome, link })
}

export function limparRascunho() {
  try {
    sessionStorage.removeItem(CHAVE)
  } catch {
    /* idem */
  }
}
```

> [!note] `sessionStorage`, não `localStorage`
> Fecha a aba, o rascunho morre — o mesmo tempo de vida da sessão dos templates (`quiz_respostas`). Com `localStorage`, quem usasse um computador do laboratório herdaria as respostas do aluno anterior.

### `lib/sessao.tsx` — `nome` e `definirNome` saem

O nome do respondente agora anda no rascunho e volta do servidor em `Tentativa.respondido_por`. Apague `nome`, `definirNome` e o `useState` correspondente. É o primeiro pedaço do contexto falso a morrer; o resto vai na FE-11.

---

## 2️⃣ Dois estados que toda tela vai usar

### `components/Estado.tsx` — arquivo novo

```tsx
import type { ReactNode } from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { ButtonPrimary } from './ui/Button'

export function Carregando({ texto = 'Carregando…' }: { texto?: string }) {
  return (
    <main className="flex-1 flex flex-col items-center justify-center p-8" aria-busy="true">
      <RefreshCw size={36} className="text-red-600 animate-spin mb-4" aria-hidden />
      <p className="text-ink-600 font-semibold">{texto}</p>
    </main>
  )
}

export function EstadoErro({
  titulo,
  mensagem,
  onTentar,
  children,
}: {
  titulo: string
  mensagem: string
  onTentar?: () => void
  children?: ReactNode
}) {
  return (
    <main className="flex-1 max-w-[600px] w-full mx-auto p-5 sm:p-8 flex flex-col items-center justify-center text-center">
      <div role="alert" className="flex flex-col items-center">
        <AlertCircle size={40} className="text-red-600 mb-4" aria-hidden />
        <h1 className="text-2xl font-bold text-ink-900 mb-2">{titulo}</h1>
        <p className="text-ink-600 text-[17px] mb-8">{mensagem}</p>
      </div>
      {onTentar && <ButtonPrimary onClick={onTentar} className="sm:w-auto">Tentar de novo</ButtonPrimary>}
      {children}
    </main>
  )
}
```

> [!tip] O `mensagem` vem pronto do `ErroApi`
> `erro.message` já é o texto em português que a FE-03 decidiu num lugar só. Nenhuma tela escreve "O servidor falhou" de novo.

---

## 3️⃣ FE-06 — `Welcome` real

### `features/quiz/Welcome.tsx` — substitua

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ButtonPrimary } from '../../components/ui/Button'
import { useQuestoes } from '../../lib/queries'
import { iniciarRascunho, lerRascunho } from './rascunho'

export function Welcome() {
  const navegar = useNavigate()
  const [nome, setNome] = useState('')
  const { data: questoes } = useQuestoes() // também aquece o cache do /quiz
  const total = questoes?.length

  const comecar = () => {
    // Preserva o token se a pessoa chegou por /questionario/:token (FE-16)
    iniciarRascunho(nome.trim(), lerRascunho().link)
    navegar('/quiz')
  }

  return (
    <main className="flex-1 max-w-[1440px] w-full mx-auto p-5 sm:p-8 md:p-12 flex flex-col items-center justify-center">
      <div className="max-w-[600px] w-full bg-white rounded-[12px] p-6 sm:p-10 shadow-[0_8px_24px_rgba(16,24,40,0.08)]">
        <h1 className="text-3xl sm:text-4xl font-bold text-red-900 mb-4 leading-tight">
          Descubra o curso certo para o seu perfil
        </h1>
        <p className="text-ink-600 text-[17px] mb-8">
          Responda a {total ?? 'algumas'} perguntas simples sobre o seu jeito de trabalhar e descubra as áreas que mais combinam com você.
        </p>

        <div className="flex flex-wrap gap-3 mb-8">
          <span className="bg-ink-900 text-white px-4 py-1.5 rounded-full text-sm font-semibold flex items-center gap-1 shadow-sm">
            Leva 2 minutos
          </span>
          <span className="bg-white border border-line-200 text-ink-900 px-4 py-1.5 rounded-full text-sm font-semibold flex items-center gap-1 shadow-sm">
            Sem cadastro
          </span>
          {total !== undefined && (
            <span className="bg-white border border-line-200 text-ink-900 px-4 py-1.5 rounded-full text-sm font-semibold flex items-center gap-1 shadow-sm">
              {total} perguntas
            </span>
          )}
        </div>

        <form onSubmit={(evento) => { evento.preventDefault(); comecar() }}>
          <div className="mb-8">
            <label htmlFor="nome" className="block font-semibold text-ink-900 mb-2">Seu nome (opcional)</label>
            <input
              id="nome"
              type="text"
              autoComplete="given-name"
              maxLength={100}
              value={nome}
              onChange={(evento) => setNome(evento.target.value)}
              className="w-full border-2 border-line-200 rounded-[8px] p-3 min-h-[48px] text-[17px] text-ink-900 focus:border-red-600 focus:ring-0 outline-none"
            />
          </div>
          <ButtonPrimary type="submit">Começar</ButtonPrimary>
        </form>

        <p className="text-center text-ink-600 text-sm mt-4">Nenhum dado seu é compartilhado.</p>
      </div>
    </main>
  )
}
```

> [!note] "6 perguntas" deixou de ser texto fixo
> O protótipo escrevia "6" em dois lugares. O número agora é `questoes.length` — desativar uma questão no admin não deixa a tela mentindo. Enquanto carrega, o chip simplesmente não aparece.

> [!note] `<form onSubmit>` no lugar de `onClick`
> Enter no campo de nome passa a começar o quiz, e o `maxLength={100}` casa com o `max_length=100` do `EnvioSerializer` — sem ele, um nome de 101 caracteres viraria 400 só no fim do quiz.

**DoD da FE-06** ("sem login, o header mostra Entrar") já vale com a sessão falsa, que nasce deslogada. A troca por `/auth/eu/` é da FE-11.

---

## 4️⃣ FE-07 e FE-08 — o `Wizard` e a submissão

### `features/quiz/Calculando.tsx` — arquivo novo

O JSX do `CalculatingScreen` (linhas 522–534 do legado), com `<main>` no lugar do `<div min-h-screen>`:

```tsx
import { RefreshCw } from 'lucide-react'

export function Calculando() {
  return (
    <main className="flex-1 bg-bg-50 flex flex-col items-center justify-center p-5" aria-busy="true">
      <div className="bg-white p-10 rounded-2xl shadow-sm border border-line-200 flex flex-col items-center">
        <RefreshCw size={48} className="text-red-600 animate-spin mb-8" aria-hidden />
        <h2 className="text-2xl font-bold text-ink-900 text-center max-w-[320px] animate-pulse" role="status">
          Analisando seu perfil e cruzando com nossos cursos...
        </h2>
        <p className="text-ink-600 mt-4 text-sm font-medium">Isso leva só um instante</p>
      </div>
    </main>
  )
}
```

### `features/quiz/Wizard.tsx` — substitua

```tsx
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
  const passo = Math.min(rascunho.passo, total - 1) // rascunho antigo com mais passos que o quiz atual
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
          // replace: o Voltar do navegador no resultado não reabre o quiz respondido
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
```

> [!important] O índice virou `id` — e é isso que conserta o F5
> O protótipo guardava `answers[questionIndex] = optionIndex`: posição na lista. Se o admin reordenar ou desativar uma questão entre o F5 e o envio, a posição 2 passa a ser outra pergunta e a resposta vai para a questão errada **sem erro nenhum**. Guardando `questao.id → alternativa.id`, o pior caso é o servidor devolver 400 ("faltam respostas") — e o `concluir()` leva a pessoa direto para a que falta.

> [!note] Onde o protótipo e o plano divergem: auto-avanço
> O `QuizScreen` do protótipo exigia clicar em "Próxima"; os templates (`static/js/quiz.js`) avançavam sozinhos. O plano ficou com o auto-avanço de 320 ms — tempo de ver o check antes de trocar. O botão "Próxima" continua: é o caminho de quem voltou para revisar e não quer mudar a resposta.

> [!warning] A barra de progresso não é mais `<header>`
> Ela está abaixo do `Header` do `Layout`; dois `<header>` na página confundem leitor de tela ("banner" duas vezes). Virou `<div>` com `role="progressbar"` — que o protótipo não tinha.

> [!note] Sem tempo mínimo na tela de cálculo
> O protótipo segurava 2 s com `setTimeout`. Com a engine local, o POST volta em ~100 ms e a tela "pisca". É a verdade: o plano pediu `isPending`, não teatro. Se a banca estranhar, um `Math.max` de 600 ms no `onSuccess` resolve — mas decida conscientemente, não por imitação.

---

## 5️⃣ FE-09 — `Resultado` com dado real

### `features/quiz/ModalRefazer.tsx` — arquivo novo

```tsx
import { RefreshCw } from 'lucide-react'
import { Modal } from '../../components/Modal'
import { ButtonPrimary, ButtonSecondary } from '../../components/ui/Button'

export function ModalRefazer({ onConfirmar, onCancelar }: { onConfirmar: () => void; onCancelar: () => void }) {
  return (
    <Modal
      titulo="Refazer o teste?"
      icone={<RefreshCw className="text-red-600" size={22} />}
      onFechar={onCancelar}
      acoes={
        <>
          <ButtonPrimary onClick={onConfirmar}>Sim, refazer o teste</ButtonPrimary>
          <ButtonSecondary onClick={onCancelar}>Cancelar</ButtonSecondary>
        </>
      }
    >
      <p className="text-ink-600 text-[17px] mb-2">
        Um novo teste gera um <strong className="text-ink-900">novo resultado</strong> — este continua salvo no endereço atual.
      </p>
      <p className="text-ink-600 text-sm">Sua lista de interesse é mantida.</p>
    </Modal>
  )
}
```

> [!note] O texto do modal mudou — porque o comportamento mudou
> O protótipo dizia "suas respostas atuais serão apagadas". Com `/resultado/:id` persistido no banco, isso passou a ser falso: a tentativa antiga continua lá e abre pelo histórico. Microcopy que mente sobre o sistema é bug, não estilo.

### `features/quiz/Resultado.tsx` — substitua

```tsx
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
const CIRCUNFERENCIA = 2 * Math.PI * RAIO // 364.4 — o valor fixo do protótipo

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

  // Sem desestruturar antes dos ifs: é o `consulta.isPending`/`isError` que faz o
  // TypeScript saber que `data` existe daqui para baixo.
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
```

> [!important] Todo número da tela veio do servidor
> | Protótipo | Agora |
> |---|---|
> | `COURSES[0]` fixo | `recomendacoes[0]` (rank 1) |
> | `96%` e `strokeDashoffset="14.5"` fixos | `match` e o offset calculado dele |
> | `bestMatch.areas` — percentuais inventados no curso | `explicacao.top_areas[].percentual`, saída da engine |
> | `90 - idx * 5` nos cards menores | `rec.match` |
> | `idx + 2` como posição | `rec.rank` |
> | "Salvar resultado em PDF" sem `onClick` | `window.print()` — o navegador já oferece "Salvar como PDF", e o botão diz isso |

> [!note] O `percentual` não é "quanto você tem da área"
> É a fatia daquela área **na afinidade com este curso** (`contribuicao / total`, em `engine.explicacao`). Por isso as barras somam ~100% entre si. Se a banca perguntar, a frase certa é "o quanto cada área pesou nesta combinação".

---

## 6️⃣ FE-10 — `DetalheCurso`

### `lib/config.ts` — arquivo novo

```ts
// Dados da unidade. Vazio = o bloco "Falar com a secretaria" não aparece.
// TODO(TCC): preencher com o endereço e telefone reais da escola parceira.
export const CONTATO_SECRETARIA = {
  endereco: '',
  telefone: '',
}
```

### `features/quiz/DetalheCurso.tsx` — substitua

```tsx
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

  const tentativa = useTentativa(tentativaId) // do cache: nenhuma requisição se veio do resultado
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

          {/* FE-12 liga este botão ao POST /interesses/ com o fluxo do interesse pendente */}
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
```

> [!danger] Três conteúdos inventados saem desta tela
> 1. A frase "O profissional formado poderá atuar em indústrias, oficinas e concessionárias." — o protótipo a **colava no fim de toda descrição**, inclusive de Costura e IA.
> 2. A lista "O que você vai aprender" — quatro itens genéricos, iguais para todos os cursos. O `Curso` não tem esse campo; se a banca quiser, é campo novo no model, não texto fixo no React.
> 3. `85%` de afinidade fixo e o endereço "Rua da Escola Técnica, 1000" / "(11) 99999-0000". A afinidade agora só aparece quando a pessoa **chegou do resultado** (`?tentativa=`); o contato só aparece quando alguém preencher `config.ts`.

> [!note] `?tentativa=12` na URL, e não `state` do router
> `navigate(url, { state })` some quando a pessoa cola o link em outra aba. A query string sobrevive a F5, a link copiado e ao botão Voltar — e o dado vem do cache do `useTentativa`, sem requisição nova.

### `mock/dados.ts` — o que morre aqui

`QUESTIONS` e `COURSES` não têm mais nenhum import. Apague os dois (confira com `grep -rn "mock/dados" src/`). Ficam `SURVEY_QUESTIONS` e `SEEDED_*`, que morrem nas Fases 4 e 5.

---

## 7️⃣ Verificação

```bash
pnpm typecheck   # 0 erros
pnpm build       # e o build passa
```

Com os dois servidores de pé, sempre em `http://localhost:5173`:

| # | Ação | Esperado |
|---|---|---|
| 1 | Abrir `/` | O chip mostra o número real de perguntas do banco |
| 2 | Nome "Ana" → Começar → responder 3 perguntas | Cada clique avança sozinho depois de ~⅓ s |
| 3 | **F5** na pergunta 4 | Volta na pergunta 4, com as 3 anteriores marcadas ao clicar Voltar |
| 4 | Parar o Django (`Ctrl+C`) e clicar "Ver meu resultado" na última | Aviso de erro **dentro do quiz**, respostas intactas. Subir o Django e clicar de novo → resultado |
| 5 | DevTools → Network no clique final | **Um** POST `/api/v1/quiz/tentativas/` e **nenhum** GET de tentativa depois (veio do `setQueryData`) |
| 6 | No resultado | "Ana, esses são…", anel com o `match` real, barras de `top_areas`, cards com rank 2–5 |
| 7 | Refazer respondendo **sempre a última alternativa** | Outro curso em 1º lugar (DoD da FE-09) |
| 8 | Voltar do navegador no resultado | Vai para `/`, não para o quiz respondido |
| 9 | Ver detalhes → Voltar | O resultado reaparece **sem** requisição nova na aba Network (DoD da FE-10) |
| 10 | Colar a URL do resultado numa **janela anônima** | "Resultado não encontrado" em < 1 s (não espera retry) |
| 11 | `/curso/abc` e `/resultado/0` | Telas de "não encontrado", sem requisição |

> [!important] O passo 10 é a regra C6 funcionando, não um bug
> A janela anônima é outro navegador para o Django: a tentativa anônima só abre para a sessão que a criou. Quando a pessoa entrar na conta (Fase 3), o *claim* adota a tentativa e ela passa a abrir em qualquer lugar onde ela esteja logada.

---

## 8️⃣ O commit

No repositório **de fora** (`educmatch/`), em branch — é o PR que vira a demo da banca:

```bash
cd "$HOME/Documents/vscode/educmatch"
git switch -c fase-2-fluxo-publico
git add frontend
git status --short
git commit -m "$(cat <<'EOF'
feat(frontend): fluxo público contra a API v1 (FE-06 a FE-10)

Quiz, resultado e detalhe do curso deixam o dado falso do protótipo e
passam a consumir /api/v1/. O TCC roda ponta a ponta na SPA.

- lib/queries.ts: único lugar que conhece as URLs; setQueryData no POST
  faz /resultado/:id abrir sem segunda requisição
- Wizard por questao.id -> alternativa.id em sessionStorage: F5 no meio
  do quiz não perde nada, e reordenar questões não troca respostas
- Tela de cálculo ligada ao isPending do POST (sem setTimeout de 2 s)
- Erro de rede no envio mostra aviso no próprio quiz, com as respostas
  guardadas
- Resultado lê rank, match e explicacao.top_areas reais; sai COURSES[0]
- Detalhe do curso por GET /catalogo/cursos/:id/, afinidade só quando se
  chega do resultado (?tentativa=)
- Removidos conteúdos inventados: afinidade 85%, lista de aprendizado
  genérica, endereço e telefone de exemplo
- retry não repete 4xx

Spec: vault > EducMatch(Secretária) > passo-a-passo-fe-06-fe-10
EOF
)"
```

---

## ▶️ Próxima ação

[[Projetos/EducMatch(Secretária)/passo-a-passo-fe-11-fe-15|👤 FE-11 a FE-15 — conta e interesse]]: a sessão falsa morre e o botão "Manifestar interesse" passa a gravar de verdade.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front]] — §4 (mapa tela → endpoint) e §5 (D1, o resultado falso)
- [[Projetos/EducMatch(Secretária)/engine-matching-cosseno|🧮 Engine de cosseno]] — de onde saem `match` e `top_areas`
- [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Templates Django]] — o `quiz.js` de onde vem o auto-avanço
- **Conceitos:** [[arq-spa|🖥️ SPA]] · [[React|React]] · [[TypeScript|TypeScript]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]]
