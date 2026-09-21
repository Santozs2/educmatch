---
title: "Passo a passo — FE-22 a FE-24 (acessibilidade, deploy e corte dos templates)"
aliases: ["Passo a passo FE-22", "Fase 6 do front", "Deploy da SPA", "Aposentar templates Django"]
tags: [tcc, front, acessibilidade, deploy, whitenoise, django, execucao, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-21
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|🗂️ Plano]] · Vem depois de: [[Projetos/EducMatch(Secretária)/passo-a-passo-fe-16-fe-21|🔗📊 FE-16 a FE-21]] · Front antigo: [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Templates Django]]

# ✨ Passo a passo — FE-22 a FE-24

> [!abstract] O que esta nota é
> O **como** da Fase 6, a última: passar o pente de acessibilidade que a troca de stack costuma perder (FE-22), servir SPA e API no mesmo domínio (FE-23) e só então apagar os templates (FE-24).
> Três PRs, **nesta ordem**. A FE-24 é o último PR do projeto — antes dela, os templates são o plano B da banca.

> [!warning] Verificado só em parte
> O `Modal`, o `Layout`, o `useTitulo` e o foco/atalhos do `Wizard` (FE-22) e o `lazy` do `/painel` (FE-23) passaram em `tsc` + `vite build` em 2026-09-21. O lado Django da FE-23 (WhiteNoise, catch-all) e toda a FE-24 **não** foram executados. Cada seção termina na sua verificação.

---

## 1️⃣ FE-22 — acessibilidade

> [!abstract] DoD do plano: "quiz inteiro respondível só com teclado"
> O que isso exige na prática, e o que a leitura do código encontrou faltando:

| # | Onde | Problema | Seção |
|---|---|---|---|
| A1 | `Wizard` | Depois do auto-avanço, o botão focado **some** do DOM e o foco cai no `<body>`: quem usa teclado precisa de 10 Tabs para voltar às alternativas | 1.1 |
| A2 | `Modal` | Tab sai do modal para a página de trás; ao fechar, o foco não volta ao botão que abriu | 1.2 |
| A3 | `Header` | O menu "Minha conta" não fecha no `Esc` nem no clique fora | 1.3 |
| A4 | Troca de rota | SPA não anuncia a página nova; o `<title>` é o mesmo em todas | 1.4 |
| A5 | Texto `text-ink-400` (`#A1A1AA`) em fundo branco | Contraste **2,6 : 1** — reprova no WCAG AA (mínimo 4,5 : 1) | 1.5 |
| A6 | Alvos de 44 px | Itens do menu, "Voltar" da `CascaConta`, "Ver detalhes" da lista, seletor de período do painel | 1.5 |
| A7 | `animate-in`, `zoom-in-95`… | Classes sem plugin: nunca animaram (E6 da revisão da FE-01) | 1.6 |

### 1.1 — `Wizard`: o foco acompanha a pergunta

```tsx
import { useEffect, useRef, useState } from 'react'
// ...
  const titulo = useRef<HTMLHeadingElement>(null)
  const primeiraRenderizacao = useRef(true)

  // Junto dos outros hooks, ANTES dos returns antecipados:
  useEffect(() => {
    if (primeiraRenderizacao.current) {
      primeiraRenderizacao.current = false
      return // não rouba o foco ao abrir a página
    }
    titulo.current?.focus()
  }, [rascunho.passo])
```

E o `<h2>` da pergunta:

```tsx
        <h2 ref={titulo} tabIndex={-1} className="text-2xl font-bold text-ink-900 mb-8 leading-tight outline-none">
```

E um anúncio para leitor de tela, logo depois do contador "Pergunta X de Y":

```tsx
          <span className="sr-only" aria-live="polite">Pergunta {passo + 1} de {total}</span>
```

Por fim, atalho de teclado pelos números que as alternativas já mostram:

```tsx
  useEffect(() => {
    const aoTeclar = (evento: KeyboardEvent) => {
      if (evento.target instanceof HTMLInputElement || evento.altKey || evento.ctrlKey || evento.metaKey) return
      const alternativa = questaoAtual.current?.alternativas[Number(evento.key) - 1]
      if (alternativa) escolherAtual.current?.(alternativa.id)
    }
    document.addEventListener('keydown', aoTeclar)
    return () => document.removeEventListener('keydown', aoTeclar)
  }, [])
```

com dois refs atualizados a cada render, logo antes do `return (` do JSX:

```tsx
  questaoAtual.current = questao
  escolherAtual.current = escolher
```

e declarados com os outros hooks:

```tsx
  const questaoAtual = useRef<Questao>(undefined)
  const escolherAtual = useRef<(id: number) => void>(undefined)
```

> [!note] Por que refs, e não `[questao, escolher]` nas dependências
> `escolher` é recriada a cada render. Nas dependências, o `addEventListener` seria desfeito e refeito a cada clique — funciona, mas gira o listener sem motivo. O ref deixa o efeito montar uma vez só e sempre ler a pergunta atual.

> [!important] Por que o foco no `<h2>`, e não na primeira alternativa
> Focar a alternativa faz o leitor de tela ler "1, Consertar coisas…, botão" — sem a pergunta. Focando o título, ele lê a pergunta, e o próximo Tab já cai na primeira alternativa. `tabIndex={-1}` deixa o `<h2>` focável por código sem entrar na ordem do Tab.

### 1.2 — `components/Modal.tsx`: foco preso e devolvido

Substitua o arquivo:

```tsx
import { useEffect, useId, useRef, type ReactNode } from 'react'

interface Props {
  titulo: string
  icone?: ReactNode
  onFechar: () => void
  children: ReactNode
  acoes?: ReactNode
}

const FOCAVEIS = 'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])'

export function Modal({ titulo, icone, onFechar, children, acoes }: Props) {
  const caixa = useRef<HTMLDivElement>(null)
  const idTitulo = useId()
  const fechar = useRef(onFechar)

  useEffect(() => {
    fechar.current = onFechar
  })

  useEffect(() => {
    const anterior = document.activeElement as HTMLElement | null
    const focaveis = () => Array.from(caixa.current?.querySelectorAll<HTMLElement>(FOCAVEIS) ?? [])
    focaveis()[0]?.focus()
    document.body.style.overflow = 'hidden'

    const aoTeclar = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') fechar.current()
      if (evento.key !== 'Tab') return
      const lista = focaveis()
      if (lista.length === 0) return
      const primeiro = lista[0]
      const ultimo = lista[lista.length - 1]
      if (evento.shiftKey && document.activeElement === primeiro) {
        evento.preventDefault()
        ultimo.focus()
      } else if (!evento.shiftKey && document.activeElement === ultimo) {
        evento.preventDefault()
        primeiro.focus()
      }
    }

    document.addEventListener('keydown', aoTeclar)
    return () => {
      document.removeEventListener('keydown', aoTeclar)
      document.body.style.overflow = ''
      anterior?.focus() // devolve o foco para quem abriu
    }
  }, [])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={() => fechar.current()}>
      <div
        ref={caixa}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        onClick={(evento) => evento.stopPropagation()}
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 sm:p-8 animate-in zoom-in-95 duration-200"
      >
        <div className="flex items-center gap-3 mb-4">
          {icone && <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center shrink-0">{icone}</div>}
          <h2 id={idTitulo} className="text-xl font-bold text-ink-900">{titulo}</h2>
        </div>
        {children}
        {acoes && <div className="flex flex-col sm:flex-row gap-3 mt-8">{acoes}</div>}
      </div>
    </div>
  )
}
```

> [!warning] O `[onFechar]` da versão da FE-04 tinha um efeito colateral escondido
> Com `onFechar` nas dependências, qualquer re-render do pai com uma arrow nova (`onFechar={() => setX(false)}`) desmontava e remontava o efeito. Com o foco preso, isso **puxaria o foco de volta para o primeiro botão** no meio da digitação. O `fechar` em ref é o que permite `[]`.

### 1.3 — `Header`: o menu fecha como menu

Dentro do `Header`, junto dos hooks:

```tsx
import { useEffect, useRef, useState } from 'react'
// ...
  const menu = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menuAberto) return
    const fora = (evento: MouseEvent) => {
      if (!menu.current?.contains(evento.target as Node)) setMenuAberto(false)
    }
    const tecla = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') setMenuAberto(false)
    }
    document.addEventListener('mousedown', fora)
    document.addEventListener('keydown', tecla)
    return () => {
      document.removeEventListener('mousedown', fora)
      document.removeEventListener('keydown', tecla)
    }
  }, [menuAberto])
```

E `ref={menu}` no `<div className="relative">` que envolve o botão e o menu. Troque `py-3` por `min-h-[48px]` nos cinco `menuitem`.

### 1.4 — `Layout`: título, pular para o conteúdo e foco na troca de rota

```tsx
import { useEffect, useRef } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Header } from './Header'

export function Layout({ semNav = false }: { semNav?: boolean }) {
  const { pathname } = useLocation()
  const conteudo = useRef<HTMLDivElement>(null)
  const primeira = useRef(true)

  useEffect(() => {
    if (primeira.current) {
      primeira.current = false
      return
    }
    conteudo.current?.focus() // o leitor de tela começa a página nova do topo do conteúdo
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <div className="font-sans text-ink-900 selection:bg-red-100 selection:text-red-900 min-h-screen flex flex-col">
      <a href="#conteudo" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:font-bold focus:text-red-700">
        Pular para o conteúdo
      </a>
      <Header semNav={semNav} />
      <div id="conteudo" ref={conteudo} tabIndex={-1} className="flex-1 flex flex-col outline-none">
        <Outlet />
      </div>
    </div>
  )
}
```

### `lib/titulo.ts` — arquivo novo, e uma linha por tela

```ts
import { useEffect } from 'react'

export function useTitulo(titulo: string) {
  useEffect(() => {
    document.title = `${titulo} · QuizPessoal`
  }, [titulo])
}
```

| Tela | Chamada |
|---|---|
| `Welcome` | `useTitulo('Descubra seu curso')` |
| `Wizard` | `useTitulo(\`Pergunta ${passo + 1}\`)` — **antes** dos returns: use `rascunho.passo + 1` |
| `Resultado` | `useTitulo('Seu resultado')` |
| `DetalheCurso` | `useTitulo(curso.data?.nome_curso ?? 'Curso')` |
| `Entrar` / `Cadastro` | `useTitulo('Entrar')` / `useTitulo('Criar conta')` |
| Conta | `'Minha lista'`, `'Meu perfil'`, `'Meus testes'` |
| `Dashboard` | `useTitulo('Dashboard')` |
| `NaoEncontrado` | `useTitulo('Página não encontrada')` |

> [!note] Hooks antes de qualquer `return`
> `Wizard`, `Resultado` e `DetalheCurso` têm returns antecipados (carregando, erro). O `useTitulo` vai junto dos outros hooks no topo — senão o React acusa "Rendered fewer hooks than expected" na primeira troca de estado.

### 1.5 — contraste e alvos de toque

```bash
cd frontend
grep -rln "text-ink-400\|text-ink-300" src/    # troque por text-ink-500 quando for TEXTO
grep -rn "min-h-\[44px\]" src/                  # troque por min-h-[48px]
```

> [!important] `ink-400` ainda serve — para o que não é texto
> Ícone decorativo, borda, barra de gráfico: não há mínimo de 4,5 : 1 para elementos não textuais que não carregam informação sozinhos. A regra é: se alguém precisa **ler**, é `ink-500` (`#71717A`, 4,8 : 1) ou mais escuro.

> [!note] `--color-ink-300` e `--color-ink-400` são a mesma cor
> O `@theme` do export define os dois como `#A1A1AA`. Não é bug de tela, mas é um token mentiroso: quem escolher `ink-300` "para ficar mais claro" não vai ver diferença. Anote para a próxima revisão de tokens; não mexa no `@theme` nesta fase (decisão de design da spec §1).

### 1.6 — animação: instalar ou apagar

```bash
pnpm add -D tw-animate-css
```

```css
/* src/index.css, logo depois de @import 'tailwindcss'; */
@import 'tw-animate-css';

@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

> [!tip] O `prefers-reduced-motion` vale mesmo sem o plugin
> O `animate-spin` do carregando, o `hover:-translate-y-0.5` das alternativas e a barra de progresso animam com Tailwind puro. Para quem tem sensibilidade a movimento (vestibular), o sistema operacional já diz "reduza" — basta ouvir.

### 1.7 — os botões "A+" e "contraste"

**Não voltam.** Zoom do navegador (Ctrl +) já aumenta a fonte, e todo o layout está em `rem`/Tailwind; alto contraste é do sistema operacional (`forced-colors`). Um botão próprio duplicaria as duas coisas pior. Se a banca perguntar: é decisão registrada, não esquecimento.

### ✅ Verificação da FE-22

| # | Ação | Esperado |
|---|---|---|
| 1 | Do `/`, **só teclado**: Tab até o nome, digitar, Enter | Abre o quiz |
| 2 | Tab até a 1ª alternativa, Enter | Marca, avança, o foco vai para a pergunta seguinte; Tab cai na 1ª alternativa |
| 3 | Pressionar `2` | Marca a 2ª alternativa e avança |
| 4 | Última pergunta → Tab até "Ver meu resultado" → Enter | Resultado (DoD da FE-22) |
| 5 | "Refazer o teste" → Tab várias vezes | O foco gira **dentro** do modal; Esc fecha e o foco volta ao botão "Refazer" |
| 6 | Primeiro Tab de qualquer página | "Pular para o conteúdo" aparece |
| 7 | DevTools → Lighthouse → Accessibility em `/`, `/quiz`, `/resultado/:id`, `/painel` | ≥ 95 em todas |
| 8 | Windows: Configurações → Acessibilidade → Efeitos visuais → Animação **desligada** | Nada gira nem desliza |

---

## 2️⃣ FE-23 — build e deploy no mesmo domínio

> [!abstract] A topologia
> O Django serve **tudo**: `/api/…` e `/admin/…` pelas views, os arquivos do `frontend/dist/` pelo WhiteNoise, e qualquer outra URL devolve o `index.html` da SPA. Um processo, um domínio, zero CORS — é o que a spec §6 prometeu e o que a BK-08 preparou.

> [!important] O conflito de rotas que o plano não previa
> Enquanto a FE-24 não roda, os templates **ainda** respondem em `/`, `/entrar/`, `/resultado/<pk>/`… — as mesmas URLs da SPA. Com o `APPEND_SLASH` do Django, `/entrar` (SPA) viraria redirect para `/entrar/` (template). Solução: nesta fase os templates mudam para **`/legado/`**. Continuam no ar como plano B, fora do caminho da SPA; a FE-24 só apaga a pasta.

### Backend — `requirements.txt` e `core/settings.py`

```text
whitenoise==6.9.0
```

```python
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # logo depois do Security
    # ... o resto igual
]

STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
# Os arquivos do build da SPA na raiz do site: /assets/index-3f9a1c2b.js etc.
WHITENOISE_ROOT = FRONTEND_DIST
# Nome com hash do Vite → cache de 1 ano; o index.html (sem hash) nunca fica velho.
WHITENOISE_IMMUTABLE_FILE_TEST = lambda caminho, url: "/assets/" in url

if not DEBUG:
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = FRONTEND_URL.startswith("https://")
```

> [!warning] Confira a versão do `whitenoise` antes de fixar
> `6.9.0` é a referência desta nota; rode `pip index versions whitenoise` e fixe a mais recente compatível com o Django 6.1. O `STORAGES` substituiu o antigo `STATICFILES_STORAGE` no Django 4.2 — não use o nome velho.

### Backend — `core/urls.py`

```python
from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path, re_path


def spa(request):
    indice = settings.FRONTEND_DIST / "index.html"
    if not indice.exists():
        raise Http404("Build da SPA ausente: rode `pnpm build` em frontend/.")
    resposta = FileResponse(indice.open("rb"), content_type="text/html; charset=utf-8")
    resposta["Cache-Control"] = "no-cache"  # sempre revalida: aponta para os assets novos
    return resposta


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.api_urls")),
    # Plano B até a FE-24 — fora do caminho da SPA
    path("legado/", include("accounts.urls")),
    path("legado/", include("quiz.web_urls")),
    # Tudo o mais é rota da SPA: /resultado/12, /painel, /questionario/<token>…
    re_path(r"^(?!api/|admin/|static/|legado/).*$", spa),
]
```

> [!danger] O catch-all tem que ser o **último** item
> O Django testa as rotas em ordem. Posto antes de `api/v1/`, o regex já exclui `api/` e funcionaria — mas qualquer app novo montado depois dele ficaria inalcançável sem aviso. Última linha, sempre.

> [!note] Os testes de template precisam do prefixo novo
> `quiz/tests/base.py::responder_tudo` posta em `"/"` fixo. Troque por `self.client.post(reverse("quiz-inicio"), dados)` — com `reverse`, o prefixo `/legado/` entra sozinho. Qualquer outro teste com URL literal de template, idem (`grep -rn 'post("/' */tests`).

### Frontend — o painel sai do pacote principal

O `vite.config.ts` fica como está: `base` padrão `/`, saída em `dist/`. O `proxy` só existe no `pnpm dev`; no build ele simplesmente não entra.

O que muda é o `routes.tsx`. Com tudo num arquivo só, o build dá **762 kB** de JS — e quase metade é o Recharts, que só o admin usa. Carregue o painel sob demanda:

```tsx
// routes.tsx — apague o `import { Dashboard } ...` do topo e troque a rota:
      {
        path: '/painel',
        lazy: async () => {
          const { Dashboard } = await import('./features/painel/Dashboard')
          return { element: <ExigeLogin admin><Dashboard /></ExigeLogin> }
        },
      },
```

| | Antes | Depois |
|---|---|---|
| JS que todo visitante baixa | 762 kB (228 kB gzip) | 402 kB (123 kB gzip) |
| JS extra só ao abrir `/painel` | — | 360 kB (105 kB gzip) |

> [!note] Medido, não estimado
> Os números saíram de um `vite build` com o código das Fases 2–5 desta trilha (2026-09-21). O aviso "Some chunks are larger than 500 kB" some junto.

### Rodar como em produção, na sua máquina

```bash
cd "$HOME/Documents/vscode/educmatch/frontend" && pnpm build
cd ../backend
pip install -r requirements.txt
DJANGO_DEBUG=0 DJANGO_ALLOWED_HOSTS=localhost FRONTEND_URL=http://localhost:8000 python manage.py collectstatic --noinput
DJANGO_DEBUG=0 DJANGO_ALLOWED_HOSTS=localhost FRONTEND_URL=http://localhost:8000 python manage.py runserver --insecure 8000
```

> [!note] `runserver --insecure` só para esta verificação
> Com `DEBUG=0`, o `runserver` recusa servir estáticos sem `--insecure`. O WhiteNoise serve de qualquer jeito — a flag é para os estáticos do `/admin/`. Num servidor de verdade, `gunicorn core.wsgi` (Linux) ou `waitress-serve --port=8000 core.wsgi:application` (Windows) no lugar do `runserver`.

> [!important] `FRONTEND_URL` em produção é o próprio domínio
> Em dev ele aponta para o Vite (`:5173`); em produção, SPA e API são o mesmo endereço (`http://localhost:8000` aqui, `https://educmatch.exemplo.br` no servidor). É dele que saem o `CSRF_TRUSTED_ORIGINS` e a URL dos links de questionário.

### ✅ Verificação da FE-23 — tudo em `localhost:8000`, sem o Vite rodando

| # | Ação | Esperado |
|---|---|---|
| 1 | `/` | A SPA, não o template |
| 2 | Responder o quiz → **F5** em `/resultado/<id>` | Carrega (o clique 4 da FE-05, agora no servidor de verdade) |
| 3 | `/pagina-que-nao-existe` | 404 **da SPA**, com o cabeçalho |
| 4 | Entrar, manifestar interesse, sair | Tudo funciona — sem `CORS_ALLOWED_ORIGINS` em lugar nenhum (DoD da FE-23) |
| 5 | DevTools → Network → um `/assets/*.js` | `Cache-Control: max-age=315360000, public, immutable` |
| 6 | O `index.html` | `Cache-Control: no-cache` |
| 7 | `/legado/` | O quiz de template, ainda vivo |
| 8 | `/admin/` | Admin com CSS (estáticos do `collectstatic`) |

---

## 3️⃣ FE-24 — aposentar os templates

> [!danger] Só depois de FE-23 verificada **e** de uma demo completa na SPA
> Apagar é o único passo sem volta fácil desta nota inteira. Antes: uma passada completa do fluxo (quiz → resultado → interesse → lista → painel) em `localhost:8000`, sem abrir o `/legado/` nenhuma vez.

### O que sai

```bash
cd "$HOME/Documents/vscode/educmatch/backend"

# Templates e estáticos do front antigo
git rm -r templates/ static/ accounts/templates/

# Views e rotas de página
git rm quiz/web_urls.py quiz/web_views.py accounts/urls.py accounts/views.py accounts/forms.py

# Testes que existiam só para as páginas (cobertos pela API em test_api.py e test_api_conta.py)
git rm accounts/tests/test_c5_rotas.py accounts/tests/test_c6_claim.py accounts/tests/test_c4_interesse.py
```

### O que muda

**`quiz/views.py`** — apague `superuser_required`, `gerar_questionario_link`, `dashboard_view` e os imports que só eles usavam (`wraps`, `redirect_to_login`, `PermissionDenied`, `JsonResponse`, `redirect`, `render`, `reverse`, `settings`). Ficam só as views de API.

**`core/urls.py`** — as duas linhas `legado/` saem e o regex do catch-all perde o `|legado/`:

```python
    re_path(r"^(?!api/|admin/|static/).*$", spa),
```

**`core/settings.py`**:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],          # era [BASE_DIR / "templates"]; o admin usa APP_DIRS
        "APP_DIRS": True,
        # OPTIONS igual
    },
]

LOGIN_URL = "/entrar"  # rota da SPA; LOGIN_REDIRECT_URL e LOGOUT_REDIRECT_URL saem
# STATICFILES_DIRS sai: a pasta static/ não existe mais
```

**`quiz/tests/base.py`** — `responder_tudo` passa a responder pela API:

```python
    def responder_tudo(self, nome="Visitante", coluna=0):
        return self.api().post("/api/v1/quiz/tentativas/", self.payload_valido(coluna, nome), format="json")
```

(Qualquer teste que use `responder_tudo` com `self.client` e espere redirect precisa ser reescrito para o 201 da API — `grep -rn responder_tudo */tests`.)

**`accounts/signals.py`** — **fica**. O claim do C6 é do `login()`, e a API chama `login()`.

**`accounts/servicos.py`** — fica. `_salvar_interesse_pendente` morre junto com `accounts/views.py`: na SPA, o pendente mora no cliente (FE-12).

> [!note] Links antigos de questionário continuam funcionando
> O template atendia `/questionario/<uuid>/` (com barra); a SPA atende `/questionario/:token`. O React Router casa a rota com ou sem a barra final, e o catch-all do Django entrega o `index.html` para as duas. Link enviado por WhatsApp antes do corte ainda abre.

### No vault

- [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Front em templates Django]]: no frontmatter, `status: historico`; logo abaixo do título, o callout:
  > `> [!warning] Histórico — substituído pela SPA React em <data do merge>. Ver [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ spec do front]].`
- [[Projetos/EducMatch(Secretária)/api-quiz-drf|🔌 API REST do quiz]]: o mesmo tratamento (o vocabulário em inglês já tinha virado histórico na spec §2, B15).
- `bash System/scripts/vault.sh idx` para regenerar o índice.

### Na monografia

A spec §7 pede que a perda do *progressive enhancement* vire parágrafo, não omissão. Sugestão de conteúdo (reescreva na voz do texto): nos templates, o quiz funcionava com JavaScript desligado porque cada resposta era um POST de formulário; na SPA, sem JavaScript não há tela. A troca foi aceita porque (1) o público-alvo usa navegadores modernos em laboratório e celular, (2) a URL por resultado — o ganho do PRG — foi preservada, e (3) a acessibilidade por teclado e leitor de tela foi verificada explicitamente (FE-22).

### ✅ Verificação da FE-24

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test                                      # DoD da FE-24: verde
grep -rn "web_views\|web_urls\|render(" --include=*.py . | grep -v .venv   # vazio (exceto o admin)
```

E a mesma tabela da FE-23 — menos o passo 7, que agora tem que dar o 404 da SPA.

---

## 4️⃣ Os commits

Três PRs, em ordem:

```bash
# tudo a partir da raiz do monorepo
cd "$HOME/Documents/vscode/educmatch"

# PR 1 — frontend/
git switch -c fase-6a-acessibilidade
git add frontend && git commit -m "feat(frontend): passada de acessibilidade (FE-22)"

# PR 2 — backend/ (settings, urls, requirements) e frontend/ (lazy do /painel)
git switch main && git pull && git switch -c fase-6b-deploy-mesmo-dominio
git add backend frontend && git commit -m "feat(deploy): SPA e API no mesmo domínio via WhiteNoise (FE-23)"

# PR 3 — backend/
git switch main && git pull && git switch -c fase-6c-aposenta-templates
git add backend && git commit -m "refactor!: remove os templates Django, substituídos pela SPA (FE-24)"
```

> [!tip] O `!` no último commit é Conventional Commits para "quebra compatibilidade"
> Quem tinha `/entrar/` nos favoritos cai no 404 da SPA (a rota nova é `/entrar`, sem barra). É pequeno, mas é quebra — o `!` deixa isso registrado no histórico.

---

## ▶️ Próxima ação

Nenhuma nesta trilha: a FE-24 fecha o [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|plano]]. O que sobra é o que a spec §8 deixou fora de escopo de propósito — testes E2E (Playwright), e a camada de IA, cujo contrato de payload a SPA já respeita.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front]] — §6 (topologia) e §7 (o que não pode se perder)
- [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Templates Django]] — o que esta fase aposenta
- [[Projetos/EducMatch(Secretária)/defesa-monografia-tcc|🎤 Defesa]] — onde o parágrafo do *progressive enhancement* vai ser perguntado
- **Conceitos:** [[arq-spa|🖥️ SPA]] · [[CORS|🌐 CORS]] · [[Vite|⚡ Vite]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]]
