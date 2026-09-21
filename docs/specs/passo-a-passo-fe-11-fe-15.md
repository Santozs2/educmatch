---
title: "Passo a passo — FE-11 a FE-15 (conta e lista de interesse na SPA)"
aliases: ["Passo a passo FE-11", "Fase 3 do front", "Login na SPA", "Interesse pendente React"]
tags: [tcc, front, react, autenticacao, sessao, csrf, execucao, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-21
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|🗂️ Plano]] · Vem depois de: [[Projetos/EducMatch(Secretária)/passo-a-passo-fe-06-fe-10|🎯 FE-06 a FE-10]] · Vem antes de: [[Projetos/EducMatch(Secretária)/passo-a-passo-fe-16-fe-21|🔗📊 FE-16 a FE-21]] · Regras: [[Projetos/EducMatch(Secretária)/spec-autenticacao-lista-interesse|🔐 Spec de autenticação]]

# 👤 Passo a passo — FE-11 a FE-15

> [!abstract] O que esta nota é
> O **como** da Fase 3: o `lib/sessao.tsx` falso vira a sessão do Django, o botão "Manifestar interesse" passa a gravar (com o desvio pelo login quando precisa), e as três telas de conta leem dado real.
> Ao fim, a métrica de conversão do painel (recomendado → interessado) tem de onde vir.

> [!success] Compila — mas não foi clicado
> Em 2026-09-21, o código desta nota (junto com o das Fases 2 e 5) passou em `tsc --noEmit` e `vite build`, e a API que ele consome passou nos testes de contrato da [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|BK]]. **Nenhum clique** foi feito: a seção 7 é o que prova que funciona.

## 🧭 Estado das decisões

| | Decisão | Estado |
|---|---|---|
| **D3** | Cards "aulas concluídas / horas estudadas / sequência" do perfil | ✅ **saem**; entram "testes feitos" e "cursos na lista", contados das APIs. É a opção que o plano dava como alternativa, e a única em que nenhum número é inventado |
| **D-editar** | "Salvar alterações" no perfil | ✅ **sai** nesta fase: o contrato v1 não tem `PATCH /auth/eu/`. Nome e e-mail ficam só leitura. Se entrar, é BK nova, não gambiarra no front |
| **D-pendente** | Onde guardar o interesse pendente | ✅ **`sessionStorage`**, não memória como dizia a spec §3: em memória ele morre no F5 da tela de login, e quem cria conta no meio do caminho às vezes recarrega |

> [!important] Pré-requisitos
> Fases 0, 1 e 2 fechadas. O `CSRF_TRUSTED_ORIGINS` da BK-08 **tem** que estar no ar: é nesta fase que o primeiro POST de usuário logado acontece, e sem ele todo POST autenticado volta 403 `Origin checking failed`.

---

## 1️⃣ FE-11 — a sessão real

### `lib/tipos.ts` — acrescente e ajuste

```ts
export interface Interesse {
  id: number
  curso: Curso
  status: 'interessado' | 'contatado' | 'descartado'
  criado_em: string
  rank_snapshot: number | null
  era_principal: boolean
}

export interface TentativaResumo {
  tentativa_id: number
  criado_em: string
  respondido_por: string
  confidence_band: 'alta' | 'media' | 'baixa'
  principal: Recomendacao | null
}

export interface DadosCadastro {
  nome: string
  email: string
  senha: string
}
```

### `lib/api.ts` — acrescente no fim

```ts
/** Erros de validação do DRF — {"email": ["Já existe…"]} → {email: "Já existe…"}.
 *  Vazio quando o erro não é 400 de campo. */
export function errosDeCampo(erro: unknown): Record<string, string> {
  if (!(erro instanceof ErroApi) || erro.status !== 400) return {}
  if (!erro.corpo || typeof erro.corpo !== 'object') return {}
  const saida: Record<string, string> = {}
  for (const [campo, valor] of Object.entries(erro.corpo as Record<string, unknown>)) {
    if (campo === 'detail') continue
    saida[campo] = Array.isArray(valor) ? String(valor[0]) : String(valor)
  }
  return saida
}
```

E, em `mensagemDeErro`, uma linha antes do `if (status === 401)`:

```ts
  if (status === 400 && corpo && typeof corpo === 'object') return 'Confira os campos destacados.'
```

> [!note] Por que dois formatos de erro
> O DRF devolve `{"detail": "..."}` para erro de regra (senha errada, sem permissão) e `{"campo": ["..."]}` para erro de validação (e-mail repetido, senha fraca). O `detail` já virava `mensagem`; o `errosDeCampo` pega o outro — e cada input mostra o seu.

### `lib/queries.ts` — novas chaves e hooks

```ts
import type { Curso, EnvioQuiz, Interesse, Questao, Tentativa, TentativaResumo } from './tipos'

export const chaves = {
  questoes: ['quiz', 'questoes'] as const,
  tentativa: (id: number) => ['quiz', 'tentativa', id] as const,
  curso: (id: number) => ['catalogo', 'curso', id] as const,
  eu: ['auth', 'eu'] as const,
  interesses: ['conta', 'interesses'] as const,
  tentativas: ['conta', 'tentativas'] as const,
}

// ... useQuestoes, useTentativa, useCurso, useEnviarQuiz como na Fase 2 ...

export function useInteresses(ativo = true) {
  return useQuery({
    queryKey: chaves.interesses,
    queryFn: () => api<Interesse[]>('/interesses/'),
    enabled: ativo,
  })
}

export function useCriarInteresse() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (corpo: { curso: number; tentativa: number | null }) =>
      api<Interesse>('/interesses/', { method: 'POST', body: JSON.stringify(corpo) }),
    onSuccess: () => cliente.invalidateQueries({ queryKey: chaves.interesses }),
  })
}

export function useRemoverInteresse() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api<void>(`/interesses/${id}/`, { method: 'DELETE' }),
    // Otimista: o item some na hora; se o DELETE falhar, volta.
    onMutate: async (id) => {
      await cliente.cancelQueries({ queryKey: chaves.interesses })
      const antes = cliente.getQueryData<Interesse[]>(chaves.interesses)
      cliente.setQueryData<Interesse[]>(chaves.interesses, (lista) => lista?.filter((item) => item.id !== id))
      return { antes }
    },
    onError: (_erro, _id, contexto) => cliente.setQueryData(chaves.interesses, contexto?.antes),
    onSettled: () => cliente.invalidateQueries({ queryKey: chaves.interesses }),
  })
}

export function useMinhasTentativas() {
  return useQuery({
    queryKey: chaves.tentativas,
    queryFn: () => api<TentativaResumo[]>('/tentativas/'),
  })
}
```

### `lib/sessao.tsx` — substitua o arquivo inteiro

```tsx
import { createContext, useContext, useEffect, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ErroApi, garantirCsrf } from './api'
import { chaves } from './queries'
import type { DadosCadastro, Usuario } from './tipos'

interface Sessao {
  carregando: boolean
  usuario: Usuario | null
  logado: boolean
  admin: boolean
  entrar: (email: string, senha: string) => Promise<Usuario>
  cadastrar: (dados: DadosCadastro) => Promise<Usuario>
  sair: () => Promise<void>
}

const Contexto = createContext<Sessao | null>(null)

async function buscarEu(): Promise<Usuario | null> {
  try {
    return await api<Usuario>('/auth/eu/')
  } catch (erro) {
    if (erro instanceof ErroApi && erro.status === 401) return null // deslogado não é erro
    throw erro
  }
}

export function SessaoProvider({ children }: { children: ReactNode }) {
  const cliente = useQueryClient()
  const eu = useQuery({ queryKey: chaves.eu, queryFn: buscarEu, staleTime: Infinity })

  useEffect(() => {
    garantirCsrf().catch(() => {}) // seta o cookie csrftoken; falhar aqui só adia o problema para o POST
  }, [])

  const aoEntrar = (usuario: Usuario) => {
    cliente.setQueryData(chaves.eu, usuario)
    // O claim do C6 pode ter acabado de adotar tentativas anônimas desta sessão.
    cliente.invalidateQueries({ queryKey: chaves.tentativas })
    cliente.invalidateQueries({ queryKey: chaves.interesses })
    return usuario
  }

  const valor: Sessao = {
    carregando: eu.isPending,
    usuario: eu.data ?? null,
    logado: Boolean(eu.data),
    admin: Boolean(eu.data?.is_superuser),
    entrar: (email, senha) =>
      api<Usuario>('/auth/entrar/', { method: 'POST', body: JSON.stringify({ email, senha }) }).then(aoEntrar),
    cadastrar: (dados) =>
      api<Usuario>('/auth/cadastro/', { method: 'POST', body: JSON.stringify(dados) }).then(aoEntrar),
    sair: async () => {
      await api<void>('/auth/sair/', { method: 'POST' })
      cliente.setQueryData(chaves.eu, null)
      // Computador de laboratório: nada da pessoa anterior fica no cache.
      cliente.removeQueries({ queryKey: chaves.interesses })
      cliente.removeQueries({ queryKey: chaves.tentativas })
      cliente.removeQueries({ queryKey: ['quiz', 'tentativa'] })
      try {
        sessionStorage.clear()
      } catch {
        /* sem storage, nada a limpar */
      }
    },
  }

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useSessao(): Sessao {
  const valor = useContext(Contexto)
  if (!valor) throw new Error('useSessao precisa estar dentro de <SessaoProvider>')
  return valor
}
```

> [!important] É aqui que a ordem dos providers da FE-02 se paga
> `SessaoProvider` usa `useQuery` — só funciona **dentro** do `QueryClientProvider`. O `main.tsx` da Fase 1 já nasceu assim.

> [!note] `sair` não faz `cliente.clear()`
> `clear()` apagaria também as perguntas e o catálogo, que não são da pessoa, e forçaria o `/auth/eu/` a rodar de novo. `removeQueries` por chave apaga só o que é pessoal.

> [!warning] `interesses`, `alternarInteresse` e `entrar(comoAdmin)` morreram
> Qualquer tela que ainda os importe quebra no `pnpm typecheck` — é o jeito de achar o que falta migrar. O botão de "login de admin" do protótipo some: admin é quem tem `is_superuser` no `/auth/eu/`, e acabou.

### `components/Header.tsx` — três ajustes

1. Pegue também `carregando` e `usuario` do `useSessao()`.
2. Enquanto `carregando`, **não** desenhe o botão "Entrar" (troque o `: (` do ternário por `: carregando ? null : (`) — senão ele pisca por 100 ms para quem está logado.
3. O "Sair" passa a esperar o servidor, e o avatar mostra a inicial real:

```tsx
<span className="grid h-7 w-7 place-items-center rounded-full bg-red-600 text-xs">
  {(usuario?.nome || usuario?.email || 'M').charAt(0).toUpperCase()}
</span>
```

```tsx
onClick={async () => {
  setMenuAberto(false)
  await sair()
  navegar('/')
}}
```

### `components/ExigeLogin.tsx` — arquivo novo

```tsx
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Carregando } from './Estado'
import { useSessao } from '../lib/sessao'

export function ExigeLogin({ children, admin = false }: { children: ReactNode; admin?: boolean }) {
  const { carregando, logado, admin: ehAdmin } = useSessao()
  const local = useLocation()

  if (carregando) return <Carregando /> // não decide nada antes de saber quem é
  if (!logado) {
    const volta = encodeURIComponent(local.pathname + local.search)
    return <Navigate to={`/entrar?next=${volta}`} replace />
  }
  if (admin && !ehAdmin) return <Navigate to="/" replace />
  return children
}
```

### `routes.tsx` — as rotas de conta ganham a guarda

```tsx
import { ExigeLogin } from './components/ExigeLogin'
// ...
      { path: '/meus-interesses', element: <ExigeLogin><ListaInteresse /></ExigeLogin> },
      { path: '/meu-perfil', element: <ExigeLogin><Perfil /></ExigeLogin> },
      { path: '/meus-testes', element: <ExigeLogin><Historico /></ExigeLogin> },
```

(O `admin` fica para a FE-18, no `/painel`.)

---

## 2️⃣ FE-12 — o interesse pendente

### `features/conta/interesse.ts` — arquivo novo

```ts
import { useLocation, useNavigate } from 'react-router-dom'
import { useToast } from '../../components/Toast'
import { useCriarInteresse } from '../../lib/queries'
import { useSessao } from '../../lib/sessao'

const CHAVE = 'educmatch.interessePendente'

interface Pendente {
  curso: number
  tentativa: number | null
}

function lerPendente(): Pendente | null {
  try {
    const bruto = sessionStorage.getItem(CHAVE)
    return bruto ? (JSON.parse(bruto) as Pendente) : null
  } catch {
    return null
  }
}

function guardarPendente(pendente: Pendente) {
  try {
    sessionStorage.setItem(CHAVE, JSON.stringify(pendente))
  } catch {
    /* sem storage: a pessoa entra e clica de novo */
  }
}

function limparPendente() {
  try {
    sessionStorage.removeItem(CHAVE)
  } catch {
    /* idem */
  }
}

/** Aceita só caminho interno: "/curso/4?tentativa=12" sim, "//site.com" e "https://…" não. */
export function destinoSeguro(next: string | null): string {
  return next && next.startsWith('/') && !next.startsWith('//') ? next : '/'
}

/** O clique em "Manifestar interesse": grava, ou desvia pelo login guardando a intenção. */
export function useManifestarInteresse() {
  const { logado } = useSessao()
  const navegar = useNavegarParaEntrar()
  const irPara = useNavigate()
  const criar = useCriarInteresse()
  const mostrarToast = useToast()

  const manifestar = (curso: number, tentativa: number | null) => {
    if (!logado) {
      guardarPendente({ curso, tentativa })
      navegar()
      return
    }
    criar.mutate(
      { curso, tentativa },
      {
        onSuccess: () => {
          mostrarToast('Curso adicionado à lista!')
          irPara('/meus-interesses')
        },
        onError: (erro) => mostrarToast(erro.message),
      },
    )
  }

  return { manifestar, salvando: criar.isPending }
}

function useNavegarParaEntrar() {
  const irPara = useNavigate()
  const local = useLocation()
  return () => irPara(`/entrar?next=${encodeURIComponent(local.pathname + local.search)}`)
}

/** Chamado depois de entrar ou cadastrar. Devolve true se havia pendente e ele foi salvo. */
export function useConcluirInteressePendente() {
  const criar = useCriarInteresse()
  const mostrarToast = useToast()

  return async (): Promise<boolean> => {
    const pendente = lerPendente()
    if (!pendente) return false
    limparPendente() // antes do POST: se falhar, não fica tentando para sempre
    try {
      await criar.mutateAsync(pendente)
      mostrarToast('Curso adicionado à lista!')
      return true
    } catch {
      mostrarToast('Não deu para salvar o interesse. Tente de novo pela página do curso.')
      return false
    }
  }
}
```

> [!important] Por que o POST depois do login pode ser repetido sem medo
> A BK-07 fez `POST /interesses/` idempotente (201 na primeira, 200 depois). Se a pessoa já tinha o curso na lista, o pendente só confirma — não aparece erro de "duplicado" para quem não fez nada de errado.

> [!danger] `destinoSeguro` não é enfeite
> Sem ele, `/entrar?next=https://site-falso.com/login` levaria a pessoa, logo depois de digitar a senha, para uma página que imita o login e diz "senha incorreta, tente de novo". É o *open redirect*, e o `next` é a porta clássica.

### `features/quiz/DetalheCurso.tsx` — o botão passa a gravar

```tsx
import { useManifestarInteresse } from '../conta/interesse'
import { useInteresses } from '../../lib/queries'
import { useSessao } from '../../lib/sessao'

// dentro do componente, junto dos outros hooks (antes de qualquer return):
  const { logado } = useSessao()
  const { manifestar, salvando } = useManifestarInteresse()
  const interesses = useInteresses(logado)
  const naLista = interesses.data?.some((item) => item.curso.id === cursoId) ?? false

// no lugar do ButtonPrimary provisório da Fase 2:
          <ButtonPrimary
            onClick={() => manifestar(dados.id, tentativaId)}
            disabled={salvando || naLista}
          >
            {naLista ? 'Este curso já está na sua lista' : 'Manifestar interesse neste curso'}
          </ButtonPrimary>
```

---

## 3️⃣ FE-11 — as telas `Entrar` e `Cadastro`

### `features/conta/Entrar.tsx` — substitua

O JSX do `LoginScreen` (linhas 901–989 do legado), sem o `<header>` inline e sem o `SignupModal`:

```tsx
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
```

> [!note] `<label htmlFor>` e `autoComplete` não existiam no protótipo
> Sem `htmlFor`, clicar em "E-mail" não focava o campo e o leitor de tela lia "caixa de texto" sem nome. Sem `autoComplete`, o gerenciador de senhas do navegador não oferece preencher — e a banca vai testar com senha salva.

> [!note] O `if (logado && !enviando)` evita uma corrida
> Assim que `entrar()` resolve, `logado` vira `true` e o componente re-renderiza **antes** do `navegar()` decidir entre a lista e o `next`. Sem o `!enviando`, o `<Navigate>` ganharia e o interesse pendente iria para o destino errado.

### `features/conta/Cadastro.tsx` — substitua

A antiga `SignupModal` vira página (a rota `/cadastro` já existia no `routes.tsx`):

```tsx
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
```

> [!tip] A validação de senha é do servidor
> O cliente só confere se as duas senhas batem (o servidor não recebe a confirmação). Tamanho mínimo, senha comum, senha parecida com o e-mail — os `AUTH_PASSWORD_VALIDATORS` do Django decidem e voltam em `campos.senha`, em português. Duplicar a regra em TypeScript é garantir que um dia as duas discordem.

---

## 4️⃣ FE-13 a FE-15 — as telas de conta

### `features/conta/CascaConta.tsx` — arquivo novo

O `AccountShell` do protótipo (linhas 1081–1095), sem o `<Header hideNav />`:

```tsx
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'

export function CascaConta({ titulo, subtitulo, children }: { titulo: string; subtitulo: string; children: ReactNode }) {
  const navegar = useNavigate()
  return (
    <main className="flex-1 bg-bg-50 w-full">
      <div className="max-w-[900px] mx-auto px-5 py-8 sm:px-8 sm:py-12">
        <button onClick={() => navegar(-1)} className="mb-8 flex min-h-[44px] items-center gap-1 rounded-lg px-2 font-semibold text-red-700 hover:bg-red-50">
          <ChevronLeft size={20} /> Voltar
        </button>
        <div className="mb-8 border-l-4 border-red-600 pl-5">
          <h1 className="text-3xl font-bold text-ink-900">{titulo}</h1>
          <p className="mt-1 text-ink-600">{subtitulo}</p>
        </div>
        {children}
      </div>
    </main>
  )
}
```

### `features/conta/ListaInteresse.tsx` — substitua (FE-13)

```tsx
import { useNavigate } from 'react-router-dom'
import { ArrowRight, BookOpen, List, Trash2 } from 'lucide-react'
import { Carregando, EstadoErro } from '../../components/Estado'
import { useToast } from '../../components/Toast'
import { horas } from '../../lib/formatters'
import { useInteresses, useRemoverInteresse } from '../../lib/queries'
import { CascaConta } from './CascaConta'

export function ListaInteresse() {
  const navegar = useNavigate()
  const lista = useInteresses()
  const remover = useRemoverInteresse()
  const mostrarToast = useToast()

  const conteudo = () => {
    if (lista.isPending) return <Carregando />
    if (lista.isError) return <EstadoErro titulo="Não deu para abrir sua lista" mensagem={lista.error.message} onTentar={() => lista.refetch()} />
    if (lista.data.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-full bg-ink-100 flex items-center justify-center mb-4">
            <List size={28} className="text-ink-400" />
          </div>
          <p className="text-ink-600 font-semibold text-lg mb-1">Sua lista está vazia</p>
          <p className="text-ink-400 text-sm">Explore os cursos e manifeste interesse para adicioná-los aqui.</p>
        </div>
      )
    }
    return (
      <ul className="flex flex-col gap-4">
        {lista.data.map(({ id, curso }) => (
          <li key={id} className="bg-white rounded-[12px] border border-line-200 p-4 sm:p-5 flex flex-col gap-4 hover:border-red-200 hover:shadow-md transition-all duration-200">
            <div className="flex flex-col sm:flex-row sm:items-start gap-4">
              <div className="flex-1 min-w-0">
                <h2 className="font-bold text-ink-900 text-lg leading-tight">{curso.nome_curso}</h2>
                <p className="text-ink-600 text-sm mt-1 line-clamp-2">{curso.descricao}</p>
                <div className="flex flex-wrap gap-2 mt-3">
                  <span className="bg-red-100 text-red-900 px-2 py-1 rounded text-xs font-bold uppercase tracking-wide">{curso.area_principal.nome}</span>
                  <span className="bg-white border border-line-200 text-ink-600 px-2 py-1 rounded text-xs font-bold uppercase tracking-wide flex items-center gap-1">
                    <BookOpen size={11} /> {horas(curso.duracao)}
                  </span>
                </div>
              </div>
              <button
                onClick={() => remover.mutate(id, { onSuccess: () => mostrarToast('Curso removido da lista') })}
                className="min-w-[48px] min-h-[48px] flex items-center justify-center text-ink-300 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors active:scale-95 self-start shrink-0"
                aria-label={`Remover ${curso.nome_curso} da lista`}
              >
                <Trash2 size={20} />
              </button>
            </div>
            <div className="border-t border-line-200 pt-3">
              <button onClick={() => navegar(`/curso/${curso.id}`)} className="flex items-center gap-2 text-red-600 font-semibold text-sm hover:text-red-800 hover:underline transition-colors min-h-[44px]">
                <ArrowRight size={16} /> Ver detalhes do curso
              </button>
            </div>
          </li>
        ))}
      </ul>
    )
  }

  return (
    <CascaConta titulo="Minha lista de interesse" subtitulo="Os cursos que você quer conhecer melhor.">
      {remover.isError && <p role="alert" className="mb-4 text-sm font-semibold text-red-700">{remover.error.message} O item voltou para a lista.</p>}
      {conteudo()}
    </CascaConta>
  )
}
```

> [!note] `aria-label` com o nome do curso
> O protótipo tinha cinco botões idênticos "Remover curso". Para quem navega por leitor de tela, a lista de botões lia "Remover curso, Remover curso, Remover curso…" sem dizer qual.

### `features/conta/Perfil.tsx` — substitua (FE-14, decisão D3)

```tsx
import { useMinhasTentativas, useInteresses } from '../../lib/queries'
import { useSessao } from '../../lib/sessao'
import { CascaConta } from './CascaConta'

export function Perfil() {
  const { usuario } = useSessao() // a guarda ExigeLogin garante que não é null
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
```

> [!important] "—" enquanto carrega, nunca `0`
> Zero é um dado ("você não fez nenhum teste"). Mostrar 0 antes da resposta chegar é mentir por 200 ms — e é o mesmo princípio que a FE-21 aplica no painel.

### `features/conta/Historico.tsx` — substitua (FE-15)

O protótipo mostrava só o último teste, com "Perfil técnico explorador" e "Fundamentos de IA · 96%" escritos à mão. Agora é a lista inteira:

```tsx
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
```

> [!note] O item inteiro é `<Link>`, não `<button onClick={navegar}>`
> Link de verdade abre em nova aba com Ctrl+clique e aparece como link para o leitor de tela. É o ganho de ter URL por resultado — não desperdice escondendo-a num `onClick`.

### `mock/dados.ts` — o que morre aqui

Nada novo: a Fase 3 não usava mock. Confira que `grep -rn "sessao\b.*interesses\|alternarInteresse\|definirNome" src/` volta vazio.

---

## 5️⃣ O admin hardcoded — conferência final

```bash
grep -rn "admin123\|admin@senai" frontend/src/   # tem que voltar vazio
```

A FE-05 já mandava apagar; se ainda existir no `App.legacy.tsx`, o arquivo não foi removido (R4 da revisão). **Não** crie um superusuário com essa senha "para a demo" — crie com `python manage.py createsuperuser` e uma senha que não esteja no git.

---

## 6️⃣ Mudanças no `routes.tsx` e no `main.tsx`

Só a guarda da seção 1. O `main.tsx` não muda: o `SessaoProvider` novo tem a mesma assinatura do falso.

---

## 7️⃣ Verificação

```bash
pnpm typecheck && pnpm build
```

Em `http://localhost:5173`, com um usuário criado pelo `createsuperuser` e outro comum:

| # | Ação | Esperado |
|---|---|---|
| 1 | F5 em `/` deslogado | Header mostra "Entrar"; aba Network: `GET /auth/eu/` → **401** e `GET /auth/csrf/` → 204 com `Set-Cookie: csrftoken` |
| 2 | Responder o quiz deslogado → detalhe do curso → "Manifestar interesse" | Vai para `/entrar?next=/curso/4%3Ftentativa%3D12` |
| 3 | Senha errada | Caixa vermelha "E-mail ou senha incorretos.", campo de senha com borda vermelha, **nenhum `alert()`** |
| 4 | Senha certa | Vai direto para `/meus-interesses`, com o curso lá e o toast "Curso adicionado à lista!" (DoD da FE-12) |
| 5 | Menu → Meus testes | O teste do passo 2 aparece — o claim do C6 funcionou pela SPA |
| 6 | Clicar nele | Abre o resultado certo (DoD da FE-15) |
| 7 | Na lista, remover o curso | Some na hora, toast "Curso removido da lista", sem reload (DoD da FE-13) |
| 8 | Parar o Django e remover outro | O item some e **volta**, com a mensagem de erro |
| 9 | Meu perfil | Nome, e-mail, "Testes feitos: 1", "Cursos na lista: n" — nenhum card de aulas/horas (DoD da FE-14) |
| 10 | Sair → Voltar do navegador até `/meus-testes` | Redireciona para `/entrar?next=/meus-testes`; a lista **não** aparece nem por um instante |
| 11 | Cadastro com senha `123` | Erro no campo senha, em português, vindo do Django |
| 12 | `/entrar?next=//google.com` → entrar | Vai para `/`, não para o Google |

> [!important] O passo 1 é o que prova que o CSRF está de pé
> Sem o `csrftoken` no cookie, o passo 3 falharia com 403 **só para quem já estivesse logado** — e o primeiro sintoma seria "o sair não funciona". Confira o `Set-Cookie` antes de seguir.

---

## 8️⃣ O commit

```bash
cd "$HOME/Documents/vscode/educmatch"
git switch -c fase-3-conta-interesse
git add frontend
git commit -m "$(cat <<'EOF'
feat(frontend): conta e lista de interesse (FE-11 a FE-15)

A sessão falsa do protótipo vira a sessão do Django (cookie + CSRF), e o
interesse passa a ser gravado com snapshot da recomendação.

- lib/sessao.tsx lê GET /auth/eu/ (401 = deslogado, não erro); entrar,
  cadastrar e sair pela API; sair limpa só o cache pessoal
- ExigeLogin nas rotas de conta, sem piscar a tela antes de saber quem é
- Interesse pendente em sessionStorage: clicar deslogado, entrar ou criar
  conta, e o curso já está na lista — sem passo extra
- next= aceita só caminho interno (sem open redirect)
- Erros do DRF por campo (errosDeCampo) nas telas de entrar e cadastro
- Lista com remoção otimista e rollback se o DELETE falhar
- Perfil sem números inventados (D3): testes feitos e cursos na lista
- Histórico com todas as tentativas, cada uma linkando o resultado
- Fim do admin hardcoded e do login "como admin"

Spec: vault > EducMatch(Secretária) > passo-a-passo-fe-11-fe-15
EOF
)"
```

---

## ▶️ Próxima ação

[[Projetos/EducMatch(Secretária)/passo-a-passo-fe-16-fe-21|🔗📊 FE-16 a FE-21 — questionário por link e painel]]. As duas fases são independentes: dá para fazer o painel antes, se a decisão D2 ainda não estiver fechada com o grupo.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-autenticacao-lista-interesse|🔐 Spec de autenticação e lista]] — D4 ("a intenção sobrevive ao login") e o C4
- [[Projetos/EducMatch(Secretária)/contratos-c1-a-c6|📜 C1–C6]] — o C6 que o passo 5 da verificação prova
- **Conceitos:** [[cs-csrf|🚨 CSRF]] · [[React|React]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]]
