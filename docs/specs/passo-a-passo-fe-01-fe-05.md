---
title: "Passo a passo — FE-01 a FE-05 (fundação do front React + Vite)"
aliases: ["Spec 1 do front", "Passo a passo FE", "Como começar o front", "Fundação React EducMatch"]
tags: [tcc, front, react, vite, typescript, execucao, passo-a-passo]
status: em-andamento
projeto: TCC
criado: 2026-09-19
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front React + Vite]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|🗂️ Plano de execução]] · Front antigo: [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Templates Django]] · Nota irmã: [[Projetos/EducMatch(Secretária)/passo-a-passo-aut-01-aut-03|🔑 Passo a passo AUT-01 a AUT-03]]

# ⚛️ Passo a passo — FE-01 a FE-05

> [!abstract] O que esta nota é
> O **como** da Fase 1 do [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|plano]], para executar com o editor aberto. Arquivo por arquivo, do `mkdir` até o commit.
> Ao fim desta nota existe um front React + Vite que **roda, navega por URL e faz build** — ainda com dado falso. A API entra na Fase 2; é de propósito.
> Escrito contra o export do Figma Make em `~/Downloads/Front End Development Task` e o repositório Django em `~/Documents/vscode/educmatch/EducMatch`, lidos em 2026-09-19.

> [!warning] Nada disto foi executado
> O código abaixo foi escrito contra a leitura dos dois projetos, não rodado. **A seção 6 é o que prova que deu certo** — não pule nenhum dos passos.

## 🧭 Estado das decisões

| | Decisão | Estado |
|---|---|---|
| **D-local** | Front em `educmatch/frontend/`, pasta irmã de `EducMatch/` | ✅ decidido |
| **D-config** | `vite.config.ts` e `index.html` novos; do export vêm só `App.tsx` e `index.css` | ✅ decidido |
| **D-auth** | Sessão Django + CSRF, não JWT | ✅ decidido — o cliente HTTP da seção 3 já nasce assim |
| **D2** | "Questionário por link": quiz normal **ou** app `pesquisa` próprio | ⚠️ **aberta** — nesta fase a rota aponta para a tela falsa; decidir antes da FE-16 |
| **D3** | Cards de "aulas concluídas / horas estudadas" no perfil | ⚠️ **aberta** — nesta fase vêm como estão; decidir na FE-14 |

## 🔎 Revisão de 2026-09-21 — spec × código × backend

> [!abstract] O que esta seção é
> Leitura cruzada desta nota com o `frontend/` commitado (`cc902fc`), com o Django em `EducMatch/` e com o [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|plano]]. Os erros **da nota** já foram corrigidos no texto abaixo (marcados com _revisado_); os desvios **do código** ficam listados aqui para fechar a Fase 1 antes da FE-06.

### ❌ O código ainda não cumpre a Fase 1

`pnpm typecheck` passa, mas por um motivo ruim: as telas são stubs. O que falta para a seção 6 fechar:

| # | Onde | Estado atual | O que a nota pede |
|---|---|---|---|
| R1 | `frontend/vite.config.ts` | Só `plugins` — **sem `proxy` e sem `alias`** | O bloco completo da FE-01. Sem o proxy nenhuma chamada da Fase 2 chega ao Django; sem o `alias`, um `import '@/...'` passa no `tsc` (o `tsconfig` tem `paths`) e **quebra só no navegador** |
| R2 | `features/**` | 12 das 13 telas são `<div>Nome</div>`; `Welcome` tem o `<main>` vazio | O JSX do protótipo recortado (seção 5) |
| R3 | `mock/dados.ts` | `AREAS = []`, `COURSES = []` | As constantes verbatim do `App.legacy.tsx` (linhas 66–212) |
| R4 | `App.legacy.tsx` | Ainda existe (81 KB) | Apagado no fim da FE-05 |
| R5 | `lib/formatter.ts` | Nome no singular | `lib/formatters.ts` — as Fases 2–5 importam por esse nome |
| R6 | `frontend/.gitignore` e `frontend/pnpm-lock.yaml` | **Apagados** no commit `bd4242b` | Recriar o `.gitignore` e rodar `pnpm install` para regerar o lock — sem lock, cada máquina resolve uma versão diferente |
| R7 | Raiz `educmatch/` | `package.json` vazio (`npm init`), `package-lock.json` e `pnpm-lock.yaml` sem dependências | Apagar os três. O único `package.json` do projeto é o de `frontend/` |

> [!tip] O `Header` do código tirou os botões "A+" e "contraste" — e está certo
> Eles vinham do protótipo sem `onClick`: `aria-label="Aumentar fonte"` num botão que não faz nada é pior que não ter botão, porque o leitor de tela anuncia uma função que não existe. Ficam fora até a FE-22 decidir se entram de verdade.

### ⚠️ Erros desta nota (corrigidos no texto)

| # | Problema | Correção |
|---|---|---|
| E1 | O `ToastProvider` não cancelava o `setTimeout` anterior: dois toasts em menos de 2 s e o **primeiro timer apagava o segundo** antes da hora | `useRef` guardando o timer e `clearTimeout` antes de agendar o próximo |
| E2 | `Usuario.username` em `tipos.ts`: o cadastro real (`CadastroForm`) grava `first_name`, e `User.username` é um campo herdado **sem `unique`** que ninguém preenche | `Usuario.nome` — o contrato da BK-07 expõe `first_name` como `nome` |
| E3 | `Tentativa` sem `respondido_por` nem `criado_em`: o título "Luis, esses são…" dependia do nome guardado no contexto, que **some no F5** em `/resultado/:id` | Os dois campos entram no payload (BK-02) e no tipo |
| E4 | A receita de corte mandava apagar só o `<Header/>`, mas `CourseDetailScreen`, `LoginScreen` e `InterestListScreen` têm um **`<header>` próprio inline** com "Voltar" — copiado verbatim, a tela fica com duas barras pretas | Regra nova na tabela: o `<header>` inline vira um botão "Voltar" dentro do `<main>`; o do quiz (barra de progresso) fica |
| E5 | "O corpo do `return (...)` vai verbatim" — o `return` de cada tela começa num `<div className="min-h-screen …">` que já existe no `Layout` | Leva-se só o `<main>` (e o que vier depois dele, como modais) |
| E6 | `animate-in`, `zoom-in-95`, `fade-in` são classes do plugin `tailwindcss-animate`, que **nem o export tinha** — nunca animaram, nem no protótipo | Registrado para a FE-22: `pnpm add -D tw-animate-css` + `@import 'tw-animate-css';`, ou apagar as classes |

### ⚠️ Incoerências com o plano (corrigidas no [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|plano]])

- **FE-01** falava em `educmatch-front/`; a decisão D-local é `frontend/`. A §6 da spec também.
- **FE-02** tinha como DoD "DevTools do Query aparece em dev", mas nenhum passo instala `@tanstack/react-query-devtools`. Virou opcional.
- **FE-03** tinha como DoD "`/auth/csrf/` no boot seta o cookie" — impossível antes da BK-07, e esta nota diz, corretamente, que a chamada só entra na FE-11.
- **FE-04** pedia "`App.tsx` abaixo de 20 KB"; esta nota apaga o arquivo. Vale o mais forte: apagado.

> [!success] Por que a Fase 1 não depende da Fase 0
> A [[Projetos/EducMatch(Secretária)/spec-front-react-vite|spec]] põe o conserto da API antes de tudo, e continua valendo — mas **nada nesta nota chama a API**. A fundação roda com o dado falso do protótipo, então você pode montá-la em paralelo, enquanto os endpoints não existem. O primeiro `fetch` de verdade é a FE-07.

---

## 🚦 Antes de abrir o editor

```bash
node --version    # precisa ser ≥ 20
pnpm --version    # se faltar: npm install -g pnpm
```

> [!note] Por que `pnpm` e não `npm`
> O export do Figma Make já vem com `pnpm-lock.yaml`. Trocar de gerenciador no meio significa dois lockfiles e resolução diferente da que a ferramenta usou. Se preferir `npm`, troque em todos os comandos **e** apague o `pnpm-lock.yaml` — não deixe os dois.

> [!danger] Confira onde está o `.git` antes do primeiro commit
> Existem **dois**: `educmatch/.git` e `educmatch/EducMatch/.git`. O de fora é o que vai versionar `frontend/`.
> ```bash
> cd "$HOME/Documents/vscode/educmatch"
> git status --short | head
> ```
> Se `EducMatch/` aparecer como um único item (gitlink/submódulo), o commit desta fase **não inclui nada de dentro dele** — e nesta fase isso não é problema, porque só mexemos em `frontend/`. Só não se surpreenda depois, na Fase 0, quando as mudanças do Django não entrarem nesse commit.

> [!success] Resolvido em 2026-09-21 — agora é um repositório só
> O cenário acima de fato aconteceu: `EducMatch/` ficou registrado só como gitlink, e o backend nunca chegou ao GitHub. A pasta virou **`backend/`** dentro do repositório de fora, com o histórico do Django importado (merge `1c4a08f`). A estrutura atual é `backend/` + `frontend/` + `docs/`; onde esta nota diz `EducMatch/`, leia `backend/`.

Estrutura no fim desta nota:

```
educmatch/
├─ .git/
├─ EducMatch/          ← o Django, intocado nesta fase
└─ frontend/           ← tudo o que segue
```

---

## 1️⃣ FE-01 — a pasta e o esqueleto

### Os comandos

```bash
cd "$HOME/Documents/vscode/educmatch"
EXPORT="$HOME/Downloads/Front End Development Task"

mkdir -p frontend/src/{lib,components/ui,mock}
mkdir -p frontend/src/features/{quiz,conta,painel,pesquisa}

# o que aproveitamos do export — só três arquivos
cp "$EXPORT/src/App.tsx"        frontend/src/App.legacy.tsx
cp "$EXPORT/src/index.css"      frontend/src/index.css
cp "$EXPORT/src/vite-env.d.ts"  frontend/src/vite-env.d.ts
cp "$EXPORT/tsconfig.json"      frontend/tsconfig.json

cd frontend
```

> [!important] `App.tsx` entra como `App.legacy.tsx` de propósito
> Ele é a **jazida**, não o arquivo final: nas seções 4 e 5 as funções saem dele uma por uma. No fim da FE-05 ele é apagado. O sufixo `.legacy` existe para ninguém importar dele por engano no meio do caminho.

O que **não** vem do export, e por quê:

| Arquivo do export | Por que fica fora |
|---|---|
| `vite.config.ts` (11 KB) | 90% são plugins da plataforma Figma Make: dependem de `.figma/make/site.json`, da porta 8443 e de um overlay de erro próprio |
| `index.html` | Tem placeholders `<!-- figma:title -->` que a plataforma substituía no deploy; fora dela, o `<title>` fica literalmente vazio |
| `.figma/`, `AGENTS.md`, `CLAUDE.md`, `.mise.toml` | Instruções para a ferramenta que gerou o protótipo, não para o projeto |
| `pnpm-lock.yaml` | As dependências mudam nesta seção; o lock é gerado de novo pelo `pnpm install` |
| `src/imports/` | A imagem e o markdown colado não são importados por nenhuma linha do `App.tsx` — confira com `grep -n "imports/" src/App.legacy.tsx` antes de descartar |

### `frontend/package.json` — arquivo novo

```json
{
  "name": "educmatch-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.0.0",
    "lucide-react": "^1.34.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0",
    "recharts": "^3.10.1"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.0.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^6.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.7.0",
    "vite": "^8.0.5"
  }
}
```

Duas entradas novas (`react-router-dom`, `@tanstack/react-query`) e uma que saiu (`oxfmt`, o formatador da plataforma).

> [!warning] `tsc --noEmit && vite build`, não `tsc -b`
> O `tsconfig.json` do export tem `noEmit: true` e não é `composite`. `tsc -b` recusa projeto não-composite com um erro que não explica nada. O `&&` é o que importa: se o TypeScript reclamar, o build **não** acontece — erro de tipo não vira deploy.

### `frontend/vite.config.ts` — arquivo novo

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // O front chama /api/... e o Vite repassa para o Django.
      // Efeito: o navegador vê MESMA ORIGEM — sem CORS, e o cookie
      // de sessão + o header de CSRF funcionam como em qualquer site.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

> [!important] O `proxy` entra agora, não quando a API ficar pronta
> É a linha que faz o ambiente de desenvolvimento se parecer com produção (onde front e API vão no mesmo domínio). Sem ele, o caminho "fácil" é liberar CORS geral e descobrir no deploy que o cookie de sessão nunca funcionou. Ver [[CORS|🌐 CORS]] e [[Vite|⚡ Vite]].

> [!note] `__dirname` num config ESM
> Funciona: o Vite compila o `vite.config.ts` antes de carregar e injeta o shim. O próprio config do Figma Make usava a mesma linha neste projeto.

### `frontend/index.html` — arquivo novo

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>QuizPessoal — orientação profissional SENAI</title>
    <meta name="description" content="Responda o teste de perfil e descubra quais cursos técnicos combinam com você." />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### `frontend/.gitignore` — arquivo novo

```gitignore
node_modules/
dist/
.vite/
*.tsbuildinfo
.env
.env.local
*.log
```

### Instalar e ver o protótipo de pé

```bash
pnpm install
pnpm dev
```

Abra `http://localhost:5173`. **Vai quebrar**, com erro de módulo não encontrado — o `main.tsx` do export importa `./App`, e o arquivo agora é `App.legacy.tsx`. É o esperado: a seção 2 reescreve o `main.tsx`. Se o erro for outro (Tailwind, plugin, porta), pare aqui e resolva antes de seguir.

---

## 2️⃣ FE-02 — os dois providers

### `frontend/src/lib/query.ts` — arquivo novo

```ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,          // 30s sem refetch — o catálogo não muda a cada clique
      retry: 1,                   // uma segunda tentativa; a terceira só irrita
      refetchOnWindowFocus: false, // trocar de aba não é motivo para recarregar
    },
  },
})
```

> [!note] Os padrões do TanStack Query são pensados para dashboard em tempo real
> `refetchOnWindowFocus` ligado e `staleTime: 0` fazem sentido num painel de cotações. Aqui, cada volta para a aba viraria uma rodada de requisições ao Django — e o resultado de um quiz não muda sozinho.

### `frontend/src/lib/sessao.tsx` — arquivo novo

```tsx
// ⚠️ TEMPORÁRIO — a FE-11 substitui o corpo deste arquivo por GET /api/v1/auth/eu/.
// Existe para as telas do protótipo continuarem funcionando sem backend,
// e para a navegação não voltar a ser prop drilling de seis callbacks.
import { createContext, useContext, useState, type ReactNode } from 'react'

interface Sessao {
  logado: boolean
  admin: boolean
  nome: string
  interesses: number[]
  entrar: (comoAdmin?: boolean) => void
  sair: () => void
  definirNome: (nome: string) => void
  alternarInteresse: (cursoId: number) => void
}

const Contexto = createContext<Sessao | null>(null)

export function SessaoProvider({ children }: { children: ReactNode }) {
  const [logado, setLogado] = useState(false)
  const [admin, setAdmin] = useState(false)
  const [nome, setNome] = useState('')
  const [interesses, setInteresses] = useState<number[]>([])

  const valor: Sessao = {
    logado,
    admin,
    nome,
    interesses,
    entrar: (comoAdmin = false) => {
      setLogado(true)
      setAdmin(comoAdmin)
    },
    sair: () => {
      setLogado(false)
      setAdmin(false)
      setInteresses([])
    },
    definirNome: setNome,
    alternarInteresse: (cursoId) =>
      setInteresses((atual) =>
        atual.includes(cursoId) ? atual.filter((id) => id !== cursoId) : [...atual, cursoId],
      ),
  }

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useSessao(): Sessao {
  const valor = useContext(Contexto)
  if (!valor) throw new Error('useSessao precisa estar dentro de <SessaoProvider>')
  return valor
}
```

> [!important] Este é o único estado global do projeto — e é global porque é de sessão
> Quem está logado e o que está na lista de interesse é lido por quase toda tela. Tudo o mais — passo do wizard, modal aberto, rascunho de formulário — fica no componente que usa. A regra: se só uma tela lê, não é global.

### `frontend/src/main.tsx` — substitua o arquivo

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'

import { router } from './routes'
import { queryClient } from './lib/query'
import { SessaoProvider } from './lib/sessao'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <SessaoProvider>
        <RouterProvider router={router} />
      </SessaoProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
```

> [!warning] Ordem dos providers não é estética
> `QueryClientProvider` por fora porque, na FE-11, o `SessaoProvider` vai buscar `/auth/eu/` com `useQuery` — e para isso precisa estar **dentro** dele. Inverter agora custa um bug confuso depois.

Ainda não roda: `./routes` não existe. Seção 5.

---

## 3️⃣ FE-03 — o cliente HTTP e os tipos

### `frontend/src/lib/api.ts` — arquivo novo

```ts
const BASE = '/api/v1'

export class ErroApi extends Error {
  constructor(
    public status: number,
    public corpo: unknown,
    mensagem: string,
  ) {
    super(mensagem)
    this.name = 'ErroApi'
  }
}

function lerCookie(nome: string): string {
  const achado = document.cookie.split('; ').find((linha) => linha.startsWith(`${nome}=`))
  return achado ? decodeURIComponent(achado.slice(nome.length + 1)) : ''
}

function mensagemDeErro(status: number, corpo: any): string {
  if (corpo?.detail) return corpo.detail
  if (status === 401) return 'Você precisa entrar para continuar.'
  if (status === 403) return 'Você não tem permissão para isso.'
  if (status === 404) return 'Não encontramos o que você procura.'
  if (status >= 500) return 'O servidor falhou. Tente de novo em instantes.'
  return 'Não foi possível concluir a ação.'
}

export async function api<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  const metodo = (init.method ?? 'GET').toUpperCase()
  const escreve = metodo !== 'GET' && metodo !== 'HEAD'

  const resposta = await fetch(`${BASE}${caminho}`, {
    ...init,
    method: metodo,
    credentials: 'include', // sem isto o cookie de sessão não viaja
    headers: {
      'Content-Type': 'application/json',
      ...(escreve ? { 'X-CSRFToken': lerCookie('csrftoken') } : {}),
      ...init.headers,
    },
  })

  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null)
    throw new ErroApi(resposta.status, corpo, mensagemDeErro(resposta.status, corpo))
  }
  if (resposta.status === 204) return null as T
  return resposta.json() as Promise<T>
}

// Chamada uma vez no boot, a partir da FE-11: faz o Django setar o cookie csrftoken.
export const garantirCsrf = () => api<void>('/auth/csrf/')
```

> [!important] Um lugar só decide o que é erro
> Toda tela que chamar `api()` recebe ou o dado, ou um `ErroApi` com mensagem em português pronta para exibir. Sem isso, cada tela inventa seu próprio `if (!res.ok)` — e três telas depois existem três textos diferentes para o mesmo 500.

> [!note] `garantirCsrf` vai dar 404 até a BK-07 existir
> Ela não é chamada nesta fase. Está aqui porque pertence a este arquivo, não porque já funcione.

### `frontend/src/lib/tipos.ts` — arquivo novo

Espelha o contrato da [[Projetos/EducMatch(Secretária)/spec-front-react-vite|spec §3]]. Os nomes seguem o servidor — `nome_curso`, `duracao` —, não o gosto do front.

```ts
export interface Alternativa {
  id: number
  texto: string
  order: number
}

export interface Questao {
  id: number
  texto: string
  order: number
  alternativas: Alternativa[]
}

export interface Area {
  slug: string
  nome: string
}

export interface Curso {
  id: number
  nome_curso: string
  descricao: string
  duracao: number // em horas
  area_principal: Area
}

export interface AreaExplicada {
  area: string
  area_name: string
  contribuicao: number
  percentual: number
}

export interface Recomendacao {
  rank: number
  score: number
  match: number // 0–100, já arredondado pelo servidor
  curso: Curso
  explicacao: { top_areas: AreaExplicada[] }
}

export interface Tentativa {
  tentativa_id: number
  respondido_por: string // revisado (E3): o nome volta do servidor, sobrevive ao F5
  criado_em: string
  confidence_band: 'alta' | 'media' | 'baixa'
  diferenca: number
  recomendacoes: Recomendacao[]
}

export interface Usuario {
  id: number
  email: string
  nome: string // revisado (E2): é o first_name; User.username não é usado
  is_superuser: boolean
}

export interface Interesse {
  id: number
  curso: Curso
  status: 'interessado' | 'contatado' | 'descartado'
  criado_em: string
}
```

> [!warning] O tipo documenta, não valida
> O TypeScript desaparece no build. Um JSON com campo faltando passa direto e estoura como `undefined` na tela. Quem garante a forma do dado é o **teste de contrato** do lado do Django (BK-01 a BK-07). Ver [[TypeScript|TypeScript]].

### `frontend/src/lib/formatters.ts` — arquivo novo

```ts
export const horas = (h: number) => `${h} ${h === 1 ? 'hora' : 'horas'}`

export const porcentagem = (score: number) => `${Math.round(score * 100)}%`

export const dataCurta = (iso: string) =>
  new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
```

> [!tip] Formatação é função, não campo
> O protótipo guardava `hours: '160 horas'` como string dentro do curso. O servidor manda `duracao: 160`. A string existe só na hora de desenhar — assim nada precisa ser reprocessado quando o texto mudar para "160h".

---

## 4️⃣ FE-04 — os compartilhados saem do `App.legacy.tsx`

Cinco arquivos. Nas quatro primeiras extrações, **as classes CSS vêm verbatim** do protótipo — o visual não muda nesta fase.

### `frontend/src/components/ui/Button.tsx` — arquivo novo

```tsx
import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode }

const base =
  'font-bold rounded-xl min-h-[56px] px-8 flex items-center justify-center transition-all duration-200 w-full'

export function ButtonPrimary({ children, className = '', type = 'button', ...resto }: Props) {
  return (
    <button
      type={type}
      className={`bg-red-600 hover:bg-red-700 active:bg-red-900 active:scale-[0.98] disabled:bg-ink-300 disabled:active:scale-100 disabled:opacity-70 text-white shadow-sm hover:shadow-md ${base} ${className}`}
      {...resto}
    >
      {children}
    </button>
  )
}

export function ButtonSecondary({ children, className = '', type = 'button', ...resto }: Props) {
  return (
    <button
      type={type}
      className={`bg-white border-2 border-red-600 text-red-600 hover:bg-red-50 active:bg-red-100 active:scale-[0.98] shadow-sm hover:shadow-md ${base} ${className}`}
      {...resto}
    >
      {children}
    </button>
  )
}

export function ButtonGhost({ children, className = '', type = 'button', ...resto }: Props) {
  return (
    <button
      type={type}
      className={`bg-transparent text-red-600 hover:bg-red-50 active:bg-red-100 active:scale-[0.98] ${base} ${className}`}
      {...resto}
    >
      {children}
    </button>
  )
}
```

> [!important] A única mudança real aqui é o fim do `: any`
> No protótipo as três assinaturas eram `({ children, onClick, className, disabled, type }: any)`. Com `ButtonHTMLAttributes`, `aria-label`, `form`, `autoFocus` e `onKeyDown` passam a funcionar sem tocar no componente — e `disabled` volta a ser checado pelo compilador.

### `frontend/src/components/Header.tsx` — arquivo novo

O cabeçalho do protótipo recebia **seis callbacks** (`onLoginClick`, `onViewInterests`, `onViewProfile`, `onViewTests`, `onViewDashboard`, `onLogout`) — e cada tela tinha que repassar todos. Com router e contexto, ele se resolve sozinho:

```tsx
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  BarChart3, ChevronDown, Contrast, History, List, LogOut, Settings, User, ZoomIn,
} from 'lucide-react'
import { useSessao } from '../lib/sessao'

export function Header({ semNav = false }: { semNav?: boolean }) {
  const [menuAberto, setMenuAberto] = useState(false)
  const navegar = useNavigate()
  const { logado, admin, sair } = useSessao()

  const ir = (rota: string) => {
    setMenuAberto(false)
    navegar(rota)
  }

  return (
    <header className="bg-ink-900 text-white p-4">
      <div className="max-w-[1440px] mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link to="/" className="font-bold text-xl hover:text-red-100 transition-colors">
            QuizPessoal
          </Link>
          <span className="bg-white/20 text-white text-xs px-2 py-1 rounded-full hidden sm:inline-block">
            Orientação profissional
          </span>
        </div>

        {!semNav && (
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="hidden sm:flex gap-2 mr-2 sm:mr-4 border-r border-ink-600 pr-2 sm:pr-4">
              <button className="flex items-center gap-1 text-sm font-semibold hover:text-red-100 p-2 min-h-[48px] min-w-[48px] justify-center" aria-label="Aumentar fonte">
                A <ZoomIn size={16} />
              </button>
              <button className="flex items-center gap-1 text-sm font-semibold hover:text-red-100 p-2 min-h-[48px] min-w-[48px] justify-center" aria-label="Alto contraste">
                <Contrast size={16} />
              </button>
            </div>

            {logado ? (
              <div className="relative">
                <button
                  onClick={() => setMenuAberto((aberto) => !aberto)}
                  aria-expanded={menuAberto}
                  aria-haspopup="menu"
                  className="flex items-center gap-2 rounded-lg border border-white/25 bg-white/10 px-3 py-2 text-sm font-bold text-white transition-colors hover:bg-white/20"
                >
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-red-600 text-xs">
                    {admin ? 'A' : 'M'}
                  </span>
                  <span className="hidden sm:inline">{admin ? 'Administração' : 'Minha conta'}</span>
                  <ChevronDown size={16} className={menuAberto ? 'rotate-180 transition-transform' : 'transition-transform'} />
                </button>

                {menuAberto && (
                  <div role="menu" className="absolute right-0 top-[calc(100%+10px)] z-40 w-60 overflow-hidden rounded-xl border border-line-200 bg-white py-2 text-ink-900 shadow-xl">
                    <button role="menuitem" onClick={() => ir('/meus-interesses')} className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-semibold hover:bg-red-50">
                      <List size={17} className="text-red-600" /> Minha lista
                    </button>
                    <button role="menuitem" onClick={() => ir('/meus-testes')} className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-semibold hover:bg-red-50">
                      <History size={17} className="text-red-600" /> Meus testes
                    </button>
                    <button role="menuitem" onClick={() => ir('/meu-perfil')} className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-semibold hover:bg-red-50">
                      <Settings size={17} className="text-red-600" /> Meu perfil
                    </button>
                    {admin && (
                      <button role="menuitem" onClick={() => ir('/painel')} className="flex w-full items-center gap-3 border-t border-line-200 px-4 py-3 text-left text-sm font-bold hover:bg-red-50">
                        <BarChart3 size={17} className="text-red-600" /> Dashboard
                      </button>
                    )}
                    <button
                      role="menuitem"
                      onClick={() => { setMenuAberto(false); sair(); navegar('/') }}
                      className="flex w-full items-center gap-3 border-t border-line-200 px-4 py-3 text-left text-sm font-semibold text-ink-600 hover:bg-red-50 hover:text-red-700"
                    >
                      <LogOut size={17} /> Sair
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => navegar('/entrar')}
                className="flex items-center gap-2 border-2 border-white/30 hover:bg-white/10 text-white px-4 py-2 rounded-lg font-bold transition-all duration-200 text-sm active:scale-95"
              >
                <User size={16} /> <span className="hidden sm:inline">Entrar</span>
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  )
}
```

> [!warning] O logo do protótipo dava `window.location.reload()`
> Clicar em "QuizPessoal" recarregava a página inteira — a única forma de "voltar ao início" quando a tela era `useState`. Agora é um `<Link to="/">`: navegação instantânea, sem perder o cache das queries, e abre em nova aba com ctrl+clique como qualquer link.

### `frontend/src/components/Layout.tsx` — arquivo novo

```tsx
import { Outlet } from 'react-router-dom'
import { Header } from './Header'

export function Layout({ semNav = false }: { semNav?: boolean }) {
  return (
    <div className="font-sans text-ink-900 selection:bg-red-100 selection:text-red-900 min-h-screen flex flex-col">
      <Header semNav={semNav} />
      <Outlet />
    </div>
  )
}
```

### `frontend/src/components/Modal.tsx` — arquivo novo

Generaliza o `ConfirmResetModal` do protótipo, mantendo as classes e acrescentando o que faltava: fechar no `Esc` e no clique fora.

```tsx
import { useEffect, type ReactNode } from 'react'

interface Props {
  titulo: string
  icone?: ReactNode
  onFechar: () => void
  children: ReactNode
  acoes?: ReactNode
}

export function Modal({ titulo, icone, onFechar, children, acoes }: Props) {
  useEffect(() => {
    const aoTeclar = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') onFechar()
    }
    document.addEventListener('keydown', aoTeclar)
    return () => document.removeEventListener('keydown', aoTeclar)
  }, [onFechar])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={onFechar}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        onClick={(evento) => evento.stopPropagation()}
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 sm:p-8 animate-in zoom-in-95 duration-200"
      >
        <div className="flex items-center gap-3 mb-4">
          {icone && (
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center shrink-0">
              {icone}
            </div>
          )}
          <h2 className="text-xl font-bold text-ink-900">{titulo}</h2>
        </div>
        {children}
        {acoes && <div className="flex flex-col sm:flex-row gap-3 mt-8">{acoes}</div>}
      </div>
    </div>
  )
}
```

> [!note] `stopPropagation` no conteúdo é o que faz o "clique fora" funcionar
> O `onClick` está no fundo escuro; sem parar a propagação no cartão branco, clicar em qualquer lugar do modal fecharia o modal.

### `frontend/src/components/Toast.tsx` — arquivo novo

No protótipo, o aviso "Curso adicionado à lista!" era um par `showSuccessToast` + `setTimeout` no `App`, passado como prop `showToast` até a `InterestListScreen`. Vira contexto:

```tsx
import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'
import { Check } from 'lucide-react'

const Contexto = createContext<(mensagem: string) => void>(() => {})

export function ToastProvider({ children }: { children: ReactNode }) {
  const [mensagem, setMensagem] = useState<string | null>(null)
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined)

  const mostrar = useCallback((texto: string) => {
    // revisado (E1): sem o clearTimeout, o timer do toast anterior
    // apagava este antes dos 2 s
    clearTimeout(timer.current)
    setMensagem(texto)
    timer.current = setTimeout(() => setMensagem(null), 2000)
  }, [])

  return (
    <Contexto.Provider value={mostrar}>
      {children}
      {mensagem && (
        <div
          role="status"
          aria-live="polite"
          className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-ink-900 text-white px-6 py-3 rounded-[8px] shadow-lg font-semibold flex items-center gap-2 animate-in fade-in slide-in-from-bottom-4 z-50"
        >
          <Check size={20} className="text-red-600" />
          {mensagem}
        </div>
      )}
    </Contexto.Provider>
  )
}

export const useToast = () => useContext(Contexto)
```

Registre-o no `main.tsx`, dentro do `SessaoProvider`:

```tsx
<SessaoProvider>
  <ToastProvider>
    <RouterProvider router={router} />
  </ToastProvider>
</SessaoProvider>
```

> [!tip] `role="status"` + `aria-live="polite"` não estavam no protótipo
> Sem eles, o leitor de tela não anuncia nada: para quem usa leitor, o clique em "tenho interesse" não teve resposta. Duas palavras resolvem.

---

## 5️⃣ FE-05 — as rotas e o corte do `App.legacy.tsx`

### `frontend/src/mock/dados.ts` — arquivo novo

Mova para cá, **sem editar**, as constantes do topo do `App.legacy.tsx` (linhas ~66 a ~212): `AREAS`, `COURSES`, `QUESTIONS`, `SURVEY_QUESTIONS`, `SEEDED_INTEREST_COUNTS`, `SEEDED_SURVEY_RESPONSES`, os tipos `SurveyResponse` e `TestRecord`, e a função `generateToken`. Exporte cada um.

```ts
// ⚠️ TEMPORÁRIO — dado falso do protótipo. A Fase 2 apaga este arquivo:
// QUESTIONS sai em FE-07, COURSES em FE-09/FE-10, SEEDED_* em FE-19.
export const AREAS = [ /* ... verbatim ... */ ]
export const COURSES = [ /* ... verbatim ... */ ]
// ...
```

> [!danger] `ADMIN_EMAIL` e `ADMIN_PASSWORD` não vão para cá
> O protótipo tinha `admin@senai.com` / `admin123` no código. **Apague as duas linhas agora**, não na FE-11. Credencial em arquivo versionado tem o péssimo hábito de sobreviver a refatoração — e essa some no `git log` de qualquer forma. Durante esta fase, o botão de login de admin chama `entrar(true)` do contexto, sem checar nada.

### A receita de corte — vale para as 13 telas

Cada `function XScreen({...})` do `App.legacy.tsx` vira um arquivo em `features/`. O **corpo do `return (...)` vai verbatim**; só a assinatura muda:

| No protótipo | No arquivo novo |
|---|---|
| Prop `onBack` | `const navegar = useNavigate()` → `navegar(-1)` |
| Prop `onViewCourse={(id) => ...}` | `navegar(\`/curso/${id}\`)` |
| Props `isLoggedIn`, `isAdmin` | `const { logado, admin } = useSessao()` |
| Props de menu (`onViewProfile`, `onLogout`, …) | **apagar** — quem resolve é o `Header` |
| `<Header ...6 props/>` | **apagar** — o `Layout` já renderiza |
| Prop `courseId` | `const { id } = useParams()` |
| Prop `showToast` | `const mostrarToast = useToast()` |
| `<div className="min-h-screen …">` que abre o `return` | **apagar** — o `Layout` já é o `min-h-screen flex-col`; leve só o `<main>` e o que vem depois (_revisado_, E5) |
| `<header>` inline com botão "Voltar" (`CourseDetailScreen`, `LoginScreen`, `InterestListScreen`, `AccountShell`) | vira `<button onClick={() => navegar(-1)}>` no topo do `<main>`, com as classes do botão original — senão a tela fica com duas barras (_revisado_, E4). O `<header>` do `QuizScreen` **fica**: é a barra de progresso, não navegação |

### O mapa completo

| Tela no `App.legacy.tsx` | Arquivo novo | Rota |
|---|---|---|
| `WelcomeScreen` | `features/quiz/Welcome.tsx` | `/` |
| `QuizScreen` | `features/quiz/Wizard.tsx` | `/quiz` |
| `CalculatingScreen` | `features/quiz/Calculando.tsx` | — (estado do `/quiz`) |
| `ConfirmResetModal` | `features/quiz/ModalRefazer.tsx` | — (usa `Modal`) |
| `ResultScreen` | `features/quiz/Resultado.tsx` | `/resultado/:id` |
| `CourseDetailScreen` | `features/quiz/DetalheCurso.tsx` | `/curso/:id` |
| `LoginScreen` | `features/conta/Entrar.tsx` | `/entrar` |
| `SignupModal` | `features/conta/Cadastro.tsx` | `/cadastro` |
| `InterestListScreen` | `features/conta/ListaInteresse.tsx` | `/meus-interesses` |
| `AccountShell` | `features/conta/CascaConta.tsx` | — (usado por duas telas) |
| `ProfileScreen` | `features/conta/Perfil.tsx` | `/meu-perfil` |
| `TestHistoryScreen` | `features/conta/Historico.tsx` | `/meus-testes` |
| `AdminDashboard` | `features/painel/Dashboard.tsx` | `/painel` |
| `SurveyLinkModal` | `features/painel/ModalLink.tsx` | — |
| `SurveyScreen` | `features/pesquisa/Questionario.tsx` | `/questionario/:token` |
| `SurveyCompleteScreen` | `features/pesquisa/Obrigado.tsx` | `/questionario/obrigado` |

### O exemplo completo — `features/quiz/Welcome.tsx`

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { ButtonPrimary, ButtonGhost } from '../../components/ui/Button'
import { useSessao } from '../../lib/sessao'

export function Welcome() {
  const navegar = useNavigate()
  const { logado, definirNome } = useSessao()
  const [nome, setNome] = useState('')

  const comecar = () => {
    definirNome(nome.trim())
    navegar('/quiz')
  }

  return (
    // ⬇️ daqui para baixo, o JSX do WelcomeScreen do protótipo, sem o <Header/>
    <main className="flex-1 max-w-[800px] w-full mx-auto p-5 sm:p-8 flex flex-col">
      {/* ... */}
    </main>
  )
}
```

> [!important] Não "melhore" o JSX no mesmo passo
> A tentação é ajustar espaçamento e texto durante a mudança. Não faça: se o visual mudar junto com a estrutura, qualquer regressão fica impossível de atribuir. Compare a tela lado a lado com `pnpm dev` do export antigo antes de seguir para a próxima.

### `frontend/src/routes.tsx` — arquivo novo

```tsx
import { createBrowserRouter } from 'react-router-dom'
import { Layout } from './components/Layout'

import { Welcome } from './features/quiz/Welcome'
import { Wizard } from './features/quiz/Wizard'
import { Resultado } from './features/quiz/Resultado'
import { DetalheCurso } from './features/quiz/DetalheCurso'
import { Entrar } from './features/conta/Entrar'
import { Cadastro } from './features/conta/Cadastro'
import { ListaInteresse } from './features/conta/ListaInteresse'
import { Perfil } from './features/conta/Perfil'
import { Historico } from './features/conta/Historico'
import { Dashboard } from './features/painel/Dashboard'
import { Questionario } from './features/pesquisa/Questionario'
import { Obrigado } from './features/pesquisa/Obrigado'
import { NaoEncontrado } from './components/NaoEncontrado'

export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <Welcome /> },
      { path: '/quiz', element: <Wizard /> },
      { path: '/resultado/:id', element: <Resultado /> },
      { path: '/curso/:id', element: <DetalheCurso /> },
      { path: '/entrar', element: <Entrar /> },
      { path: '/cadastro', element: <Cadastro /> },
      { path: '/meus-interesses', element: <ListaInteresse /> },
      { path: '/meu-perfil', element: <Perfil /> },
      { path: '/meus-testes', element: <Historico /> },
      { path: '/painel', element: <Dashboard /> },
      { path: '*', element: <NaoEncontrado /> },
    ],
  },
  {
    // Questionário por link: sem navegação de conta na barra —
    // quem chega por token não tem (nem precisa de) conta.
    element: <Layout semNav />,
    children: [
      { path: '/questionario/obrigado', element: <Obrigado /> },
      { path: '/questionario/:token', element: <Questionario /> },
    ],
  },
])
```

> [!note] `/questionario/obrigado` não conflita com `/questionario/:token`
> O React Router ordena por especificidade, não por posição: segmento literal vence segmento dinâmico. Listar primeiro é só clareza para quem lê.

### `frontend/src/components/NaoEncontrado.tsx` — arquivo novo

```tsx
import { Link } from 'react-router-dom'

export function NaoEncontrado() {
  return (
    <main className="flex-1 max-w-[800px] w-full mx-auto p-5 sm:p-8 flex flex-col items-center justify-center text-center">
      <h1 className="text-3xl font-bold text-red-900 mb-3">Página não encontrada</h1>
      <p className="text-ink-600 text-[17px] mb-8">
        O endereço que você abriu não existe ou saiu do ar.
      </p>
      <Link to="/" className="font-bold text-red-600 hover:text-red-700 underline min-h-[48px] flex items-center">
        Voltar para o início
      </Link>
    </main>
  )
}
```

### Apagar a jazida

```bash
rm src/App.legacy.tsx
pnpm typecheck
```

> [!important] `pnpm typecheck` depois do `rm` é o teste de que o corte terminou
> Se algo ainda importava do `App.legacy.tsx`, o TypeScript acusa agora — não no navegador, três telas depois.

---

## 6️⃣ Verificação — é aqui que você descobre se deu certo

```bash
pnpm typecheck    # 0 erros
pnpm dev          # sobe em http://localhost:5173
```

Os nove cliques, na ordem:

| # | Ação | Esperado |
|---|---|---|
| 1 | Abrir `/` | Tela de boas-vindas, visual idêntico ao do export |
| 2 | Digitar o nome e começar | URL muda para `/quiz` |
| 3 | **F5** em `/quiz` | A página carrega no quiz, não no início |
| 4 | Abrir `/resultado/1` direto na barra de endereço | Carrega o resultado (dado falso), sem tela branca |
| 5 | Voltar do navegador | Volta uma tela, não sai do app |
| 6 | Clicar em "QuizPessoal" no topo | Vai para `/` sem recarregar (a aba não pisca) |
| 7 | Entrar (fake) → abrir o menu "Minha conta" | Os quatro itens navegam; o menu fecha ao escolher |
| 8 | Abrir `/pagina-que-nao-existe` | Tela de 404, com o cabeçalho no lugar |
| 9 | `Esc` com um modal aberto | O modal fecha |

Depois, o build:

```bash
pnpm build      # tsc --noEmit && vite build → dist/
pnpm preview    # serve o dist/ — confira os cliques 1, 4 e 8 de novo
```

> [!important] O clique 4 é o que os testes nunca pegam
> `/resultado/1` aberto direto é o caso que quebra em toda SPA montada às pressas: em dev o Vite devolve o `index.html` para qualquer rota, mas um servidor estático mal configurado devolve 404. Se o `pnpm preview` falhar nesse clique, o problema é de servidor, não de código — e é a FE-23 que resolve (fallback para `index.html`).

> [!warning] O que **não** deve funcionar ainda
> Nenhuma chamada de API. Se o DevTools mostrar requisição para `/api/...`, alguma tela foi ligada ao backend antes da hora — desfaça. O dado falso é o contrato desta fase.

---

## 7️⃣ O commit

Sem branch e sem PR: um commit só, na raiz `educmatch/`, com tudo o que esta nota criou.

```bash
cd "$HOME/Documents/vscode/educmatch"
git add frontend
git status --short          # confira: nada de node_modules/ nem dist/
```

> [!danger] Se `node_modules/` aparecer no `git status`
> O `.gitignore` de `frontend/` não foi criado ou está no lugar errado. **Não commite** — são milhares de arquivos e o repositório não volta ao normal com um `git rm` simples. Crie o arquivo, rode `git reset`, e refaça o `git add`.

```bash
git commit -m "$(cat <<'EOF'
feat(frontend): fundação React + Vite do EducMatch (FE-01 a FE-05)

Cria educmatch/frontend/, o front que vai substituir os templates Django.
Nesta fase a estrutura está completa e ainda não há chamada de API: as telas
rodam com o dado falso do protótipo, de propósito.

O que entra:
- Projeto Vite + React 19 + TS + Tailwind 4, config escrita do zero
  (o vite.config.ts do export era 90% plugin da plataforma Figma Make)
- Proxy /api -> localhost:8000 em dev: o navegador vê mesma origem, o que
  permite autenticar por sessão + CSRF em vez de JWT
- React Router com 12 rotas reais: navegação por URL, F5 e botão Voltar
  funcionando, /resultado/:id compartilhável
- TanStack Query configurado (staleTime 30s, sem refetch ao focar a aba)
- lib/api.ts: fetch com credentials + X-CSRFToken e mensagem de erro em
  um lugar só; lib/tipos.ts espelhando o contrato da API v1
- Compartilhados extraídos do App.tsx de 81 KB: Button (sem `any`), Header
  (seis callbacks viraram useNavigate + contexto), Layout, Modal (agora
  fecha no Esc e no clique fora), Toast (com aria-live)
- 13 telas do protótipo divididas por fluxo em src/features/
- Tela de 404, que o protótipo não tinha

O que sai:
- Credenciais de admin que estavam no código (admin@senai.com / admin123)
- vite.config.ts, index.html e metadados da plataforma Figma Make

Temporário, com prazo de validade anotado no próprio arquivo:
- src/mock/dados.ts (morre na Fase 2)
- src/lib/sessao.tsx com sessão falsa (a FE-11 troca por GET /auth/eu/)

Django intocado. Spec: vault > EducMatch(Secretária) > spec-front-react-vite
EOF
)"
```

> [!note] Por que o corpo do commit é longo
> É o único registro que sobra dentro do repositório — a spec está no vault, que não acompanha o `git log`. Quem abrir esse commit em dezembro precisa entender por que existe um `mock/` e por que o front não chama API nenhuma.

---

## ▶️ Próxima ação

Primeiro, fechar R1–R7 da [[#🔎 Revisão de 2026-09-21 — spec × código × backend|revisão]]. Depois, **Fase 0 — [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|🔧 BK-01 a BK-08]]**, e não a FE-06. A partir daqui o front precisa de `/api/v1/` respondendo, e três dos endpoints atuais quebram em runtime (`KeyError`, `AttributeError`, rota sem `<pk>`). Codificar a FE-07 contra eles é escrever cliente para um contrato que não existe.

Se quiser continuar no front enquanto isso, o único trabalho que não depende da API é o clique 9 da verificação virar regra geral: passada de acessibilidade por teclado nas 13 telas (parte da FE-22).

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front React + Vite]] — o que e o porquê destas tarefas
- [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|🗂️ Plano de execução do front]] — onde esta nota se encaixa nas 7 fases
- [[Projetos/EducMatch(Secretária)/passo-a-passo-aut-01-aut-03|🔑 Passo a passo AUT-01 a AUT-03]] — a nota irmã, mesmo formato
- [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Front em templates Django]] — o que está sendo substituído
- **Conceitos:** [[arq-spa|🖥️ SPA]] · [[CORS|🌐 CORS]] · [[cs-csrf|🚨 CSRF]] · [[React|React]] · [[Vite|⚡ Vite]] · [[TypeScript|TypeScript]] · [[Tailwind CSS|🎨 Tailwind CSS]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]] · [[Projetos|🚀 Projetos]]
