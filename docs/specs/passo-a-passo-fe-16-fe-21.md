---
title: "Passo a passo — FE-16 a FE-21 (questionário por link e painel administrativo)"
aliases: ["Passo a passo FE-16", "Fases 4 e 5 do front", "Painel na SPA", "Dashboard React", "Questionário por link React"]
tags: [tcc, front, react, painel, recharts, privacidade, execucao, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-21
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|🗂️ Plano]] · Painel: [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel]] · Vem depois de: [[Projetos/EducMatch(Secretária)/passo-a-passo-fe-11-fe-15|👤 FE-11 a FE-15]] · Vem antes de: [[Projetos/EducMatch(Secretária)/passo-a-passo-fe-22-fe-24|✨ FE-22 a FE-24]]

# 🔗📊 Passo a passo — FE-16 a FE-21

> [!abstract] O que esta nota é
> O **como** das Fases 4 e 5 do plano, juntas porque dividem o mesmo objeto (`QuestionarioLink`): o admin gera o link no painel (Fase 5), o estudante abre o link (Fase 4). São dois PRs, em qualquer ordem — o plano deixa isso explícito nos riscos.

> [!success] Compila — mas não foi clicado
> Em 2026-09-21, o código TypeScript das Fases 2–5 (esta nota e as duas anteriores) foi montado sobre o `frontend/` e passou em `tsc --noEmit` e `vite build`. **Nenhum clique** foi feito: as seções 3 e 7 são o que prova que funciona.

## 🧭 A decisão D2 — tomada aqui, com a saída registrada

> [!important] D2: o link abre **o quiz normal** (opção a)
> A [[Projetos/EducMatch(Secretária)/spec-front-react-vite#5️⃣ Divergências protótipo × backend|spec §5]] deixou a escolha aberta e apontou a (a) como a que "custa zero e não some com nada do TCC". Esta nota segue a (a) porque:
> - o backend **já é** (a): `QuestionarioLink` guarda um token, `acessar_questionario` redireciona para o quiz, `Tentativa_de_resposta.questionario_link` já existe, e a BK-02 já aceita o token no POST;
> - a (b) é um app novo (`Pesquisa`, `PerguntaPesquisa`, `RespostaPesquisa`), três endpoints e uma segunda agregação k-anônima — escopo de uma fase inteira, sem ganho para a pergunta de pesquisa do TCC (a recomendação);
> - o painel **ganha** um número real com a (a): quantas tentativas vieram por link (`via_link`, BK-06).
>
> **O que morre com a (a):** `SurveyScreen`, `SurveyCompleteScreen`, `SURVEY_QUESTIONS`, `SEEDED_SURVEY_RESPONSES`, o bloco "Resultados da pesquisa" e o gráfico de pizza "Sinais mais frequentes" do dashboard.
> **Se o grupo escolher (b)**, esta nota vale inteira para a Fase 5 e a FE-16/17 precisam de uma spec própria antes de começar — não improvise o modelo no meio do PR.

---

# 🔗 Fase 4 — questionário por link

## 1️⃣ FE-16 — `/questionario/:token`

### `lib/queries.ts` — acrescente

```ts
export function useValidarLink(token: string | undefined) {
  return useQuery({
    queryKey: ['questionario', token],
    queryFn: () => api<{ ativo: true }>(`/questionario/${token}/`),
    enabled: Boolean(token),
    retry: false,
    staleTime: Infinity,
  })
}
```

### `features/pesquisa/Questionario.tsx` — substitua

A tela do protótipo (a pesquisa de 4 perguntas) **não** é recortada: com a D2 (a), esta rota só valida o token e entrega a pessoa ao fluxo normal.

```tsx
import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Carregando, EstadoErro } from '../../components/Estado'
import { useValidarLink } from '../../lib/queries'
import { iniciarRascunho } from '../quiz/rascunho'

export function Questionario() {
  const { token } = useParams()
  const navegar = useNavigate()
  const link = useValidarLink(token)

  useEffect(() => {
    if (link.isSuccess && token) {
      iniciarRascunho('', token) // o Welcome preserva o token; o Wizard o envia no POST
      navegar('/', { replace: true }) // o Voltar do navegador não volta para o link
    }
  }, [link.isSuccess, token, navegar])

  if (link.isError) {
    return (
      <EstadoErro
        titulo="Este link não está mais ativo"
        mensagem="Peça um link novo para a secretaria da escola — ou faça o teste por conta própria pela página inicial."
      />
    )
  }
  return <Carregando texto="Abrindo o questionário…" />
}
```

> [!note] UUID malformado também dá "link inativo"
> `/api/v1/questionario/abc/` não casa com `<uuid:token>` e o Django devolve o 404 **HTML** dele. O `api.ts` tenta `resposta.json()`, falha em silêncio (`.catch(() => null)`) e lança `ErroApi(404)` do mesmo jeito. Um caminho de erro só, para token inexistente, encerrado ou mal digitado — é o DoD da FE-16.

### `routes.tsx` — o grupo `semNav` encolhe

```tsx
  {
    element: <Layout semNav />,
    children: [{ path: '/questionario/:token', element: <Questionario /> }],
  },
```

`/questionario/obrigado` sai (ver FE-17). Apague `features/pesquisa/Obrigado.tsx`.

---

## 2️⃣ FE-17 — o vínculo e a conclusão

O vínculo **já funciona** desde a Fase 2: o `Wizard` manda `questionario_link: rascunho.link`, e a BK-02 grava a FK. O que falta é a pessoa saber que respondeu pelo link da escola.

### `features/quiz/Welcome.tsx` — um aviso quando há token

Logo abaixo do `<h1>`:

```tsx
import { lerRascunho } from './rascunho'
// ...
  const viaLink = Boolean(lerRascunho().link)
// ...
        {viaLink && (
          <p className="mb-6 rounded-lg border border-red-100 bg-red-50 p-3 text-sm font-semibold text-red-900">
            Você está respondendo pelo link enviado pela sua escola.
          </p>
        )}
```

### `features/quiz/Wizard.tsx` — o `navegar` do `onSuccess` leva a marca

```tsx
          navegar(`/resultado/${tentativa.tentativa_id}`, {
            replace: true,
            state: { viaLink: Boolean(rascunho.link) },
          })
```

### `features/quiz/Resultado.tsx` — o "obrigado" vira faixa, não tela

```tsx
import { useLocation } from 'react-router-dom'
// junto dos hooks:
  const viaLink = Boolean((useLocation().state as { viaLink?: boolean } | null)?.viaLink)
// logo depois do <h1>:
      {viaLink && (
        <p role="status" className="mb-6 rounded-lg border border-line-200 bg-white p-4 font-semibold text-ink-900">
          Obrigado por responder! Sua escola recebe só os números agregados — nunca as suas respostas individuais.
        </p>
      )}
```

> [!note] Por que a conclusão não é mais uma tela separada
> O `SurveyCompleteScreen` existia porque a pesquisa do protótipo **não tinha resultado** para mostrar. Com a D2 (a), quem responde pelo link recebe o mesmo ranking que qualquer um — mandar para um "obrigado" vazio seria esconder dele o valor do teste. A faixa usa `state` do router (e não a URL) de propósito: ela some no F5, e o resultado compartilhado não carrega o aviso.

> [!important] A frase da faixa tem que ser verdade
> O painel mostra só agregados com supressão k ≥ 5 (FE-21); o admin do Django, porém, **vê** cada tentativa. A frase fala do que a escola recebe no painel. Se a banca perguntar do `/admin/`, a resposta é: acesso restrito a superusuário, e é por isso que o painel existe.

### Admin — a associação visível (DoD da FE-17)

Em `quiz/admin.py`, o `QuizTentativaAdmin` **já existe** — só ganha a coluna e o filtro (não crie um segundo `@admin.register`: dá `AlreadyRegistered` na subida):

```python
@admin.register(Tentativa_de_resposta)
class QuizTentativaAdmin(admin.ModelAdmin):
    list_display = ['id', 'respondido_por', 'user', 'criado_em', 'confidence_band', 'questionario_link']
    list_filter = ['confidence_band', ('questionario_link', admin.EmptyFieldListFilter)]
    readonly_fields = ['criado_em']
    # ... o resto da classe como está
```

### `mock/dados.ts`

Apague `SURVEY_QUESTIONS`, `SEEDED_SURVEY_RESPONSES` e o tipo `SurveyResponse`.

## 3️⃣ Verificação da Fase 4

| # | Ação | Esperado |
|---|---|---|
| 1 | Como admin, gerar um link (Fase 5) ou no shell: `QuestionarioLink.objects.create()` | Um token UUID |
| 2 | Abrir `localhost:5173/questionario/<token>` numa janela anônima | Cai no `/` com a faixa "respondendo pelo link da sua escola" |
| 3 | Responder tudo | Resultado com a faixa de obrigado |
| 4 | F5 no resultado | A faixa some; o resultado fica |
| 5 | `/admin/quiz/tentativa_de_resposta/` | A tentativa com a coluna `questionario_link` preenchida (DoD da FE-17) |
| 6 | Desativar o link no admin e reabrir a URL | "Este link não está mais ativo" (DoD da FE-16) |
| 7 | `/questionario/abc` | A mesma tela, sem erro no console além do 404 da rede |

---

# 📊 Fase 5 — painel administrativo

## 4️⃣ Os tipos e os hooks

### `lib/tipos.ts` — acrescente

O espelho do que a `Metricas` da BK-06 devolve. `total: number | null` porque **suprimido é `null`**, e o tipo obriga cada tela a tratar isso.

```ts
export type Periodo = 30 | 90 | 365

interface Suprimivel {
  suprimido?: true
}

export interface LinhaCurso extends Suprimivel {
  curso_id: number
  nome: string
  total: number | null
}

export interface LinhaConversao extends Suprimivel {
  id: number
  nome_curso: string
  recomendado: number
  interessados: number | null
  taxa: number | null
}

export interface LinhaArea extends Suprimivel {
  area: string
  nome: string
  total: number | null
}

export interface LinhaConfianca extends Suprimivel {
  confidence_band: 'alta' | 'media' | 'baixa'
  total: number | null
}

interface MetricasBase {
  periodo: Periodo
  total_de_tentativas: number
  k_minimo: number
}

export interface MetricasSemMassa extends MetricasBase {
  tem_massa: false
}

export interface MetricasCompletas extends MetricasBase {
  tem_massa: true
  cursos_ativos: number
  via_link: number
  top_primeiro: LinhaCurso[]
  top_manifestacoes: LinhaCurso[]
  top_cinco: LinhaCurso[]
  conversao: LinhaConversao[]
  aderencia: {
    com_snapshot: number
    era_principal: number
    por_posicao: ({ rank_snapshot: number; total: number | null } & Suprimivel)[]
  }
  demanda_por_area: LinhaArea[]
  confianca: LinhaConfianca[]
  orfaos: { id: number; nome_curso: string }[]
  cobertura: { slug: string; nome: string; alternativas: number }[]
}

export type Metricas = MetricasSemMassa | MetricasCompletas

export interface LinkQuestionario {
  token: string
  url: string
  criado_em: string
}
```

> [!tip] `tem_massa` é discriminante de união
> Depois de `if (!dados.tem_massa) return <Aviso/>`, o TypeScript sabe que `dados.top_primeiro` existe. Sem a união, cada gráfico precisaria de um `?.` — e um `?.` esquecido vira tela branca exatamente no período com pouco dado, que é o da demo.

### `lib/queries.ts` — acrescente

```ts
import { keepPreviousData } from '@tanstack/react-query'
import type { LinkQuestionario, Metricas, Periodo } from './tipos'

export function useMetricas(periodo: Periodo) {
  return useQuery({
    queryKey: ['painel', 'metricas', periodo],
    queryFn: () => api<Metricas>(`/painel/metricas/?periodo=${periodo}`),
    placeholderData: keepPreviousData, // trocar de período não apaga a tela enquanto carrega
  })
}

export function useLinks() {
  return useQuery({ queryKey: ['painel', 'links'], queryFn: () => api<LinkQuestionario[]>('/painel/links/') })
}

export function useGerarLink() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: () => api<LinkQuestionario>('/painel/links/', { method: 'POST' }),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['painel', 'links'] }),
  })
}
```

---

## 5️⃣ FE-18 — a guarda do `/painel`

### `routes.tsx`

```tsx
      { path: '/painel', element: <ExigeLogin admin><Dashboard /></ExigeLogin> },
```

A `ExigeLogin` da FE-11 já tem o modo `admin`: enquanto o `/auth/eu/` não volta, desenha `<Carregando/>`; volta usuário comum, `<Navigate to="/" replace>`. O layout do painel **nunca** chega a montar para quem não é admin — é o DoD ("sem layout piscar").

> [!important] A guarda do front é conforto, não segurança
> Quem garante é o `EhSuperusuario` da BK-06: um `curl` com cookie de usuário comum recebe 403 do servidor, com ou sem SPA. A guarda só evita mostrar uma tela que ia falhar.

---

## 6️⃣ FE-19 a FE-21 — o `Dashboard`

### `features/painel/numero.ts` — arquivo novo

```ts
/** A regra da FE-21 num lugar só: suprimido é "—", nunca 0. */
export const exibir = (valor: number | null | undefined) =>
  valor === null || valor === undefined ? '—' : valor.toLocaleString('pt-BR')

export const exibirTaxa = (taxa: number | null) => (taxa === null ? '—' : `${Math.round(taxa)}%`)
```

### `features/painel/graficos/GraficoBarras.tsx` — arquivo novo

```tsx
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

interface Linha {
  nome: string
  total: number | null
  suprimido?: true
}

export function GraficoBarras({ dados, kMinimo, destaque = 3 }: { dados: Linha[]; kMinimo: number; destaque?: number }) {
  // Barra de altura 0 lê como "zero". Suprimido não entra no gráfico: vai para a nota abaixo.
  const visiveis = dados.filter((linha): linha is Linha & { total: number } => linha.total !== null)
  const suprimidos = dados.filter((linha) => linha.total === null)

  if (dados.length === 0) {
    return <p className="py-10 text-center text-sm text-ink-500">Sem dados neste período.</p>
  }

  return (
    <div>
      {visiveis.length > 0 && (
        <div className="h-[240px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={visiveis} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: '#71717A' }} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="nome" width={160} tick={{ fontSize: 12, fill: '#52525B' }} tickLine={false} axisLine={false} />
              <Tooltip cursor={{ fill: '#FEF5F4' }} contentStyle={{ borderRadius: 10, border: '1px solid #E4E4E7' }} />
              <Bar dataKey="total" radius={[0, 5, 5, 0]}>
                {visiveis.map((_, indice) => (
                  <Cell key={indice} fill={indice < destaque ? '#D9251C' : '#A1A1AA'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      {suprimidos.length > 0 && (
        <p className="mt-3 text-xs text-ink-500">
          Com menos de {kMinimo} ocorrências (ocultos por privacidade): {suprimidos.map((linha) => linha.nome).join(', ')}.
        </p>
      )}
    </div>
  )
}
```

> [!danger] O gráfico é onde o "—, nunca 0" costuma quebrar
> Recharts desenha `null` como barra vazia — visualmente idêntica a zero. Um curso com 3 interessados suprimidos apareceria como "nenhum interessado", o que é pior que não mostrar: é **falso**. Por isso o filtro antes do gráfico e a nota "ocultos por privacidade" depois.

> [!note] Horizontal, não vertical como no protótipo
> O `BarChart` do protótipo era vertical e cortava os nomes com `.replace('Fundamentos de ', '')`. Nomes reais de curso têm 30–50 caracteres; no eixo Y de um gráfico deitado eles cabem inteiros. É a única mudança visual deliberada da fase.

### `features/painel/ModalLink.tsx` — arquivo novo

O `SurveyLinkModal` (linhas 1120–1206), sobre o `Modal` da FE-04 e com o link real:

```tsx
import { useState } from 'react'
import { CheckCircle, Copy, ExternalLink } from 'lucide-react'
import { Modal } from '../../components/Modal'
import type { LinkQuestionario } from '../../lib/tipos'

export function ModalLink({ link, onFechar }: { link: LinkQuestionario; onFechar: () => void }) {
  const [copiado, setCopiado] = useState(false)

  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(link.url)
      setCopiado(true)
      setTimeout(() => setCopiado(false), 2000)
    } catch {
      // clipboard exige HTTPS ou localhost; fora disso, o texto já está selecionável
    }
  }

  return (
    <Modal titulo="Link do questionário" onFechar={onFechar}>
      <p className="text-ink-600 text-sm mb-4">Compartilhe com os estudantes. Quem responde pelo link não precisa de conta.</p>
      <div className="bg-ink-50 border border-line-200 rounded-xl p-4 mb-4">
        <p className="text-sm font-mono text-ink-900 break-all leading-relaxed select-all">{link.url}</p>
      </div>
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={copiar}
          className={`flex items-center justify-center gap-2 font-bold rounded-xl min-h-[48px] px-6 flex-1 transition-all duration-200 border-2 ${
            copiado ? 'bg-green-50 border-green-500 text-green-700' : 'bg-white border-ink-900 text-ink-900 hover:bg-ink-50'
          }`}
        >
          {copiado ? <CheckCircle size={18} /> : <Copy size={18} />}
          {copiado ? 'Copiado!' : 'Copiar link'}
        </button>
        <a
          href={link.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl min-h-[48px] px-6 flex-1 transition-all duration-200"
        >
          <ExternalLink size={18} /> Abrir em nova aba
        </a>
      </div>
      <span className="sr-only" role="status">{copiado ? 'Link copiado' : ''}</span>
    </Modal>
  )
}
```

> [!note] O aviso "O link é anônimo" saiu
> Com a D2 (a), quem estiver logado ao abrir o link tem a tentativa vinculada à conta (é o mesmo `EnvioQuiz`). "Anônimo" seria falso; "não precisa de conta" é verdade.

### `features/painel/Dashboard.tsx` — substitua

```tsx
import { useState, type ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import { AlertCircle, BarChart3, ClipboardList, Link2, Users } from 'lucide-react'
import { Carregando, EstadoErro } from '../../components/Estado'
import { useGerarLink, useLinks, useMetricas } from '../../lib/queries'
import type { LinkQuestionario, MetricasCompletas, Periodo } from '../../lib/tipos'
import { GraficoBarras } from './graficos/GraficoBarras'
import { ModalLink } from './ModalLink'
import { exibir, exibirTaxa } from './numero'

const PERIODOS: Periodo[] = [30, 90, 365]

function lerPeriodo(valor: string | null): Periodo {
  const numero = Number(valor)
  return (PERIODOS as number[]).includes(numero) ? (numero as Periodo) : 90
}

export function Dashboard() {
  const [params, setParams] = useSearchParams()
  const periodo = lerPeriodo(params.get('periodo'))
  const metricas = useMetricas(periodo)
  const links = useLinks()
  const gerar = useGerarLink()
  const [modal, setModal] = useState<LinkQuestionario | null>(null)

  const trocarPeriodo = (novo: Periodo) => setParams({ periodo: String(novo) }, { replace: true })
  const gerarLink = () => gerar.mutate(undefined, { onSuccess: setModal })
  const linkAtivo = links.data?.[0]

  return (
    <main className="flex-1 bg-[#f5f5f5] w-full">
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-ink-900">Dashboard</h1>
            <p className="text-ink-500 text-sm mt-1">Visão agregada das recomendações e dos interesses</p>
          </div>
          <div className="flex gap-3">
            {linkAtivo && (
              <button onClick={() => setModal(linkAtivo)} className="flex items-center gap-2 bg-white border-2 border-ink-900 text-ink-900 hover:bg-ink-50 font-bold rounded-xl px-5 min-h-[48px] text-sm shadow-sm">
                <Link2 size={16} /> Ver link ativo
              </button>
            )}
            <button onClick={gerarLink} disabled={gerar.isPending} className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl px-5 min-h-[48px] text-sm shadow-sm active:scale-95">
              <ClipboardList size={16} /> {linkAtivo ? 'Novo link' : 'Gerar link do questionário'}
            </button>
          </div>
        </div>

        <div role="radiogroup" aria-label="Período" className="mb-8 inline-flex rounded-xl border border-line-200 bg-white p-1">
          {PERIODOS.map((opcao) => (
            <button
              key={opcao}
              role="radio"
              aria-checked={opcao === periodo}
              onClick={() => trocarPeriodo(opcao)}
              className={`min-h-[44px] rounded-lg px-4 text-sm font-bold ${opcao === periodo ? 'bg-ink-900 text-white' : 'text-ink-600 hover:bg-ink-50'}`}
            >
              {opcao === 365 ? '1 ano' : `${opcao} dias`}
            </button>
          ))}
        </div>

        {metricas.isPending ? (
          <Carregando texto="Calculando as métricas…" />
        ) : metricas.isError ? (
          <EstadoErro titulo="Não deu para carregar o painel" mensagem={metricas.error.message} onTentar={() => metricas.refetch()} />
        ) : !metricas.data.tem_massa ? (
          <div role="status" className="rounded-2xl border border-amber-200 bg-amber-50 p-6 flex items-start gap-3">
            <AlertCircle className="text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-ink-900">Ainda não há respostas suficientes neste período</p>
              <p className="text-sm text-ink-600 mt-1">
                {metricas.data.total_de_tentativas} tentativa(s). Os números aparecem a partir de {metricas.data.k_minimo} —
                abaixo disso, dava para identificar respostas individuais.
              </p>
            </div>
          </div>
        ) : (
          <div className={metricas.isPlaceholderData ? 'opacity-60 transition-opacity' : ''}>
            <Painel dados={metricas.data} />
          </div>
        )}

        {gerar.isError && <p role="alert" className="mt-4 text-sm font-semibold text-red-700">{gerar.error.message}</p>}
        <p className="text-center text-ink-400 text-xs mt-6">Nenhuma informação pessoal é exibida. Todos os dados são agregados.</p>
      </div>

      {modal && <ModalLink link={modal} onFechar={() => setModal(null)} />}
    </main>
  )
}

function Painel({ dados }: { dados: MetricasCompletas }) {
  const k = dados.k_minimo
  const cartoes = [
    { rotulo: 'Tentativas no período', valor: dados.total_de_tentativas, icone: BarChart3 },
    { rotulo: 'Pelo link da escola', valor: dados.via_link, icone: Link2 },
    { rotulo: 'Cursos ativos', valor: dados.cursos_ativos, icone: Users },
  ]
  const confianca = dados.confianca.map((linha) => ({
    nome: { alta: 'Alta', media: 'Média', baixa: 'Baixa' }[linha.confidence_band],
    total: linha.total,
    suprimido: linha.suprimido,
  }))

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {cartoes.map(({ rotulo, valor, icone: Icone }) => (
          <div key={rotulo} className="bg-white rounded-2xl border border-line-200 p-5 flex items-start gap-4 shadow-sm">
            <div className="w-11 h-11 rounded-xl bg-ink-900 flex items-center justify-center shrink-0">
              <Icone size={20} className="text-white" />
            </div>
            <div>
              <p className="text-ink-500 text-sm font-medium">{rotulo}</p>
              <p className="text-3xl font-bold text-ink-900 leading-none mt-1">{exibir(valor)}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-2 mb-8">
        <Secao titulo="Cursos mais recomendados em 1º lugar">
          <GraficoBarras dados={dados.top_primeiro} kMinimo={k} />
        </Secao>
        <Secao titulo="Cursos com mais manifestações de interesse">
          <GraficoBarras dados={dados.top_manifestacoes} kMinimo={k} />
        </Secao>
        <Secao titulo="Demanda por área (área dominante do 1º lugar)">
          <GraficoBarras dados={dados.demanda_por_area} kMinimo={k} />
        </Secao>
        <Secao titulo="Confiança da recomendação">
          <GraficoBarras dados={confianca} kMinimo={k} destaque={0} />
        </Secao>
      </div>

      <Secao titulo="Conversão: recomendado → interessado">
        {dados.conversao.length === 0 ? (
          <p className="py-6 text-center text-sm text-ink-500">Sem dados neste período.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line-200 bg-[#fafafa]">
                  <th scope="col" className="text-left px-4 py-3 text-xs font-bold text-ink-500 uppercase tracking-wider">Curso</th>
                  <th scope="col" className="text-right px-4 py-3 text-xs font-bold text-ink-500 uppercase tracking-wider">Recomendado</th>
                  <th scope="col" className="text-right px-4 py-3 text-xs font-bold text-ink-500 uppercase tracking-wider">Interessados</th>
                  <th scope="col" className="text-right px-4 py-3 text-xs font-bold text-ink-500 uppercase tracking-wider">Taxa</th>
                </tr>
              </thead>
              <tbody>
                {dados.conversao.map((linha) => (
                  <tr key={linha.id} className="border-b border-line-200 last:border-0">
                    <td className="px-4 py-3 font-semibold text-ink-900">{linha.nome_curso}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{exibir(linha.recomendado)}</td>
                    <td className="px-4 py-3 text-right tabular-nums" title={linha.suprimido ? `Menos de ${k}` : undefined}>{exibir(linha.interessados)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{exibirTaxa(linha.taxa)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Secao>

      <div className="grid gap-5 lg:grid-cols-2 mt-5">
        <Secao titulo="Cursos nunca recomendados">
          {dados.orfaos.length === 0 ? (
            <p className="text-sm text-ink-500">Todos os cursos ativos já apareceram em alguma recomendação.</p>
          ) : (
            <ul className="list-disc pl-5 text-sm text-ink-900 space-y-1">
              {dados.orfaos.map((curso) => <li key={curso.id}>{curso.nome_curso}</li>)}
            </ul>
          )}
        </Secao>
        <Secao titulo="Áreas sem nenhuma alternativa no quiz">
          {dados.cobertura.filter((a) => a.alternativas === 0).length === 0 ? (
            <p className="text-sm text-ink-500">Todas as áreas são alcançáveis pelas perguntas.</p>
          ) : (
            <ul className="list-disc pl-5 text-sm text-ink-900 space-y-1">
              {dados.cobertura.filter((a) => a.alternativas === 0).map((a) => <li key={a.slug}>{a.nome}</li>)}
            </ul>
          )}
        </Secao>
      </div>
    </>
  )
}

function Secao({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-line-200 bg-white p-5 shadow-sm sm:p-6">
      <h2 className="mb-4 font-bold text-ink-900">{titulo}</h2>
      {children}
    </section>
  )
}
```

> [!important] O que saiu do dashboard do protótipo, e por quê
> | Protótipo | Destino |
> |---|---|
> | "3 maiores / 3 menores" de `SEEDED_INTEREST_COUNTS` | `top_manifestacoes` real. Os "3 menores" viram a lista de **cursos nunca recomendados** — que responde a pergunta útil ("que curso a engine nunca sugere?") |
> | "Respostas da pesquisa", pizza "Sinais mais frequentes", "Insight 1–3" | Morrem com a D2 (a). No lugar: `via_link` e "Confiança da recomendação" |
> | `areaColors` com sete cores fixas por nome de área | Sai. Área nova no seed ficava cinza sem ninguém notar |
> | Nenhum seletor de período | 30 / 90 / 365, sincronizado com `?periodo=` (DoD da FE-19) |

### `mock/dados.ts` — o arquivo morre

`SEEDED_INTEREST_COUNTS` era o último export em uso. Apague o arquivo e a pasta `mock/`:

```bash
grep -rn "mock/" src/   # vazio
rm -r src/mock
```

---

## 7️⃣ Verificação da Fase 5

Para ter massa, gere tentativas antes (o seed não cria nenhuma). No shell do Django:

```bash
python manage.py shell -c "
from rest_framework.test import APIClient
from quiz.models import Questao
for coluna in range(12):
    c = APIClient(SERVER_NAME='localhost')
    respostas = []
    for q in Questao.objects.filter(is_active=True):
        alts = list(q.alternativas.order_by('id'))
        respostas.append({'questao': q.id, 'alternativa': alts[coluna % len(alts)].id})
    c.post('/api/v1/quiz/tentativas/', {'respondido_por': f'Teste {coluna}', 'respostas': respostas}, format='json')
"
```

| # | Ação | Esperado |
|---|---|---|
| 1 | Usuário comum abre `/painel` | Vai para `/` **sem** ver o layout do painel (DoD da FE-18) |
| 2 | Admin abre `/painel` com o banco zerado | Aviso amarelo "ainda não há respostas suficientes", **nenhum** número de curso (DoD da FE-21) |
| 3 | Rodar o script acima e recarregar | Cartões e gráficos; cursos com < 5 aparecem na nota "ocultos por privacidade", não como barra |
| 4 | Clicar em "30 dias" | A URL vira `?periodo=30`, a tela esmaece e atualiza sem sumir (DoD da FE-19) |
| 5 | F5 | Continua em 30 dias |
| 6 | Tabela de conversão | Interessados suprimidos e a **taxa** da mesma linha como "—" (a BK-06 zera a taxa) |
| 7 | Gerar link → Copiar → colar numa janela anônima | Fluxo da Fase 4 inteiro |
| 8 | DevTools → Network → resposta do `/painel/metricas/` | Nenhum `total` menor que 5 que não seja `null` |

> [!important] O passo 8 é o teste de privacidade que a banca pode pedir ao vivo
> A tela pode esconder um número que o JSON entrega — e qualquer pessoa abre o DevTools. A garantia está na resposta do servidor, não no React. Por isso a supressão mora em `painel/privacidade.py` e o front só respeita o `null`.

---

## 8️⃣ Os commits

Dois PRs, como manda o plano:

```bash
git switch -c fase-4-questionario-link
git add frontend && git commit -m "feat(frontend): questionário por link abre o quiz (FE-16, FE-17)

D2 decidida pela opção (a): o link valida o token e entra no fluxo normal;
a tentativa sai vinculada ao QuestionarioLink. Sai a pesquisa de demanda
do protótipo, que não tinha backend.

Spec: vault > EducMatch(Secretária) > passo-a-passo-fe-16-fe-21"
```

```bash
git switch main && git switch -c fase-5-painel
git add frontend && git commit -m "feat(frontend): painel administrativo com dado real (FE-18 a FE-21)

- /painel guardado por is_superuser, sem piscar o layout
- Métricas por período (30/90/365) sincronizadas com ?periodo=
- Gráficos em Recharts que não desenham suprimido como zero
- tem_massa=false mostra o aviso de k_minimo e nenhum número
- Gerar e copiar link do questionário
- Fim do mock/: nenhum dado falso restante no front

Spec: vault > EducMatch(Secretária) > passo-a-passo-fe-16-fe-21"
```

(O `Co-Authored-By` e o corpo longo ficam a critério — o padrão das outras fases vale aqui também.)

---

## ▶️ Próxima ação

[[Projetos/EducMatch(Secretária)/passo-a-passo-fe-22-fe-24|✨ FE-22 a FE-24 — acessibilidade, deploy e aposentadoria dos templates]].

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel]] — a origem de cada métrica e do k = 5
- `docs/specs/passo-a-passo-pnl-01-pnl-05.md` (no repositório, não no vault) — o painel em template que este substitui
- [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front]] — §5, D2
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]]
