---
title: "Correções da revisão — branches de A, B e C (2026-09-22)"
aliases: ["Correções da revisão", "O que falta para mesclar", "Revisão das branches A B C"]
tags: [tcc, revisao, git, merge, correcoes, spec]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Mapa: [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] · Specs: [[Projetos/EducMatch(Secretária)/spec-pessoa-a-infra|🧱 A]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-b-dados-motor|🧮 B]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-c-painel|📊 C]]

# 🔎 Correções da revisão — A, B e C

> [!important] Rodada 2 (2026-09-22, contra a `main` em `56a49b2`): **o código das três está certo**
> Mesclando as três branches na ordem **A → B → C** numa cópia da `main`, a suíte fecha em **59 testes, 58 verdes**. O único vermelho é o do fuso, que é esperado na máquina local e passa na CI (o workflow carrega as tabelas).
> O que ainda impede o merge **não é o código**. São três coisas de Git e uma de segredo:
>
> | Pessoa | Falta |
> |---|---|
> | **A** | ❌ nada mudou desde a rodada 1: a senha `devmysql` e o usuário `tecmysql` continuam como padrão no `settings.py` (A-2) e o README (A-3) |
> | **B** | ✅ `.sql`, `import ast` e `*.sql` no `.gitignore` feitos, e o PR-3 adiantado e certo. ❌ **não fez o `git merge origin/main`** (passo comum): os conflitos continuam. ❌ **mexeu no `ALLOWED_HOSTS` do `settings.py`**, que é da A |
> | **C** | ✅ `_celula.html` e a rota `cursos/` feitos. ❌ **não fez o `git merge origin/main`**. ❌ **mexeu no `ALLOWED_HOSTS` do `settings.py`**, que é da A. ⏳ continua dependendo do merge da B |
>
> **B e C: desfaçam a mudança no `settings.py`.** Ela conflita com o PR da A, que já resolve o `ALLOWED_HOSTS` do jeito certo (por variável de ambiente). Para os testes rodarem na sua máquina antes do PR da A entrar, deixe a mudança **sem commit**. Para tirar do commit:
> ```bash
> git switch <sua-branch>
> git fetch origin
> git merge origin/main                         # o passo comum, que faltou
> git checkout --theirs backend/catalogo/ docs/specs/   # só os que estiverem em conflito
> git checkout origin/main -- backend/core/settings.py  # desfaz o ALLOWED_HOSTS
> git add -A && git commit --no-edit
> git push
> ```
> Depois, confira: `git diff origin/main -- backend/core/settings.py` tem de sair **vazio**.

> [!abstract] O que esta nota é
> O resultado da revisão de código das três branches abertas, feita em 2026-09-22 contra a `main` em `c50960f` (depois do PR #4, que consertou a página do curso). Cada branch foi **mesclada numa cópia** da `main` e testada no MySQL. Nenhuma está pronta para entrar ainda, mas todas estão perto: **o código principal de cada uma está certo**, e o que falta é pequeno e está listado abaixo, com os comandos.

## 🧭 Resumo

| Pessoa | Branch | Veredito | O que falta |
|---|---|---|---|
| **A** | `test/ci` | 🟡 perto | conflito no `catalogo`, **senha de volta no código**, README |
| **B** | `feat/dados-c4` | 🟡 perto | conflito no `catalogo` e nas specs, o `.sql` de backup, um `import` sobrando |
| **C** | `feat/painel_template` | 🟠 falta mais | conflito no `catalogo`, **apaga a rota `cursos/`**, falta o `_celula.html`, precisa do PR da B antes |

**Ordem de merge:** A → B → C. A C depende dos campos novos da B, e todos os testes de página dependem do `ALLOWED_HOSTS` da A.

---

## ⚙️ O primeiro passo é igual para os três: trazer a `main` nova

A `main` mudou desde que as branches foram criadas (o PR #4 corrigiu o `catalogo/views.py`). **As três branches têm uma versão antiga ou quebrada desse arquivo**, e por isso dão conflito. Resolva sempre ficando com a versão da `main`:

```bash
git switch <sua-branch>
git pull                          # traz o que já está no GitHub da sua branch
git fetch origin
git merge origin/main             # vai parar em conflito: é esperado
```

Nos arquivos em conflito que estão listados na sua seção, fique com a versão da `main`:

```bash
git checkout --theirs backend/catalogo/views.py      # e os outros da sua lista
git add backend/catalogo/views.py
git commit --no-edit
```

> [!note] Por que `--theirs`
> Durante um `git merge origin/main`, "ours" é a sua branch e "theirs" é a `main`. A `main` tem a versão certa do `catalogo`: `from catalogo.models import Curso` e `is_active=True`.

Confira que o conserto veio:

```bash
grep -n "import Curso\|is_activ" backend/catalogo/views.py
```

Tem de aparecer `from catalogo.models import Curso` e `is_active=True`. Se aparecer `accounts.models` ou `is_activate`, o conflito foi resolvido para o lado errado.

---

## 🧱 Pessoa A — `test/ci`

**O que está certo:** o settings lendo do ambiente, o leitor de `.env` escrito à mão (boa solução, sem dependência nova), o `ALLOWED_HOSTS` com default, o teste de fuso e o workflow da CI, igual ao da spec.

### A-1 · conflito

Na hora do `git merge origin/main`: `backend/catalogo/views.py` → `git checkout --theirs`.

### A-2 · 🔴 a senha voltou para o código

Hoje, em `backend/core/settings.py`:

```python
"USER": os.environ.get("DB_USER", "tecmysql"),
"PASSWORD": os.environ.get("DB_PASSWORD", "devmysql"),
```

A senha `devmysql` é a que já vazou no histórico do Git. Com ela como **valor padrão**, ela continua no código, e o objetivo do PR (tirar segredo do código) não é cumprido. Troque por:

```python
"USER": os.environ.get("DB_USER", "root"),
"PASSWORD": os.environ.get("DB_PASSWORD", ""),
```

E no `backend/.env.example`, que vai para o Git, **sem senha**:

```bash
DB_USER=root
DB_PASSWORD=
```

Quem usa `tecmysql` coloca isso no **próprio** `backend/.env`, que não vai para o Git:

```bash
DB_USER=tecmysql
DB_PASSWORD=devmysql
```

Confira que o `.env` está ignorado: `git check-ignore backend/.env` tem de imprimir o caminho.

### A-3 · README

Falta a seção "Como rodar" com o `.env` e as tabelas de fuso (spec A, §4). Sem ela, a próxima pessoa que clonar não sabe que precisa do `.env`.

### A-4 · sobre a CI

O workflow está certo, mas **vai ficar vermelho em todo PR** até os PRs da B e da C entrarem e o PR-3 da B consertar o `test_engine_puro`. Isso é esperado: **não** ligue ainda a opção "Require status checks to pass" na proteção da `main`.

### Pronto quando

- [ ] `grep -n "devmysql\|tecmysql" backend/core/settings.py backend/.env.example` não encontra nada
- [ ] Com o seu `backend/.env` criado, `python manage.py check` passa
- [ ] `python manage.py test quiz.tests.test_rotas_web` → 3 verdes (antes do seu PR davam 400)
- [ ] O PR na aba **Actions** do GitHub roda o workflow (vermelho é esperado, pelo A-4)

---

## 🧮 Pessoa B — `feat/dados-c4`

**O que está certo:** o model `Interesse` com o C4, a migração do JSON (igual à da spec, verificada no MySQL), a migração única que remove `Login`/`Cadastro` e aplica o C4 (juntar as duas numa só está certo), o `servicos.py`, as views usando o serviço e o admin. Os 4 testes do C4 passam.

### B-1 · conflitos

O seu segundo commit copiou arquivos da `main` antiga. Na hora do `git merge origin/main`, fique com a `main` em todos:

```bash
git checkout --theirs backend/catalogo/views.py backend/catalogo/urls.py docs/specs/spec-pessoa-a-infra.md docs/specs/spec-pessoa-b-dados-motor.md
git add backend/catalogo docs/specs
git commit --no-edit
```

### B-2 · o backup do banco foi para o Git

```bash
git rm backend/backup-antes-pr2.sql
```

Está vazio, mas a spec pede para **nunca** versionar backup: um backup de verdade teria os dados de todos os alunos. Para não acontecer de novo, acrescente no `.gitignore` da raiz:

```
*.sql
```

### B-3 · o `import ast` que sobrou

A primeira linha de `backend/quiz/web_views.py` ainda é `import ast`, e ninguém mais usa: o JSON já chega como dicionário. Apague a linha.

### Pronto quando

- [ ] `grep -n "import Curso" backend/catalogo/views.py` mostra `catalogo.models`
- [ ] `git ls-files backend/*.sql` não mostra nada
- [ ] `python manage.py makemigrations --check --dry-run` → `No changes detected`
- [ ] `python manage.py test accounts.tests.test_c4_interesse quiz.tests.test_contratos` → verdes (depois do PR da A, por causa do `ALLOWED_HOSTS`)
- [ ] Depois do merge: **avisar o grupo** para rodar `python manage.py migrate`

---

## 📊 Pessoa C — `feat/painel_template`

**O que está certo:** a view com a privacidade completa (taxa, confiança e aderência suprimidas), as métricas consertadas, o gerador de link, o redirecionamento do dashboard antigo, a base de testes e o CSS.

### C-1 · conflito

Na hora do `git merge origin/main`: `backend/catalogo/views.py` → `git checkout --theirs`.

### C-2 · 🔴 a branch apaga a rota `cursos/`

A sua branch saiu de uma `main` em que o `core/urls.py` ainda não tinha a rota do curso, e o seu commit a removeu. Sem ela, **a tela de resultado quebra** (`NoReverseMatch: 'curso-detalhe'`), porque os nomes dos cursos viraram links para o detalhe. Depois do merge, confira que o `core/urls.py` tem **as duas** linhas:

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("painel/", include("painel.urls")),
    path("", include("accounts.urls")),
    path("", include("quiz.web_urls")),
    path("cursos/", include("catalogo.urls")),
]
```

> [!warning] O Git não vai avisar
> A remoção da linha não dá conflito: o merge simplesmente aceita a remoção. Tem de conferir à mão.

### C-3 · 🔴 falta o `_celula.html`

O `dashboard.html` inclui `painel/_celula.html` em três lugares, mas o arquivo não foi para o commit. Sem ele, o painel dá **erro 500** sempre que o período tem 5 testes ou mais. Crie `backend/painel/templates/painel/_celula.html`, com uma linha:

```html
{% if suprimido %}<abbr title="menos de {{ k_minimo }} respondentes">—</abbr>{% else %}{{ valor }}{% endif %}
```

```bash
git add backend/painel/templates/painel/_celula.html
```

### C-4 · espere o PR da B

A sua view chama `aderencia_a_recomendacao` (lê `rank_snapshot`) e `demanda_por_area` (lê o JSON). Antes do PR da B entrar, isso dá `FieldError` e `'str' object has no attribute 'get'`. **Mescle depois da B.** Quando o PR dela entrar:

```bash
git fetch origin && git merge origin/main
python manage.py migrate
```

### Pronto quando

- [ ] `grep -n "cursos/\|painel/" backend/core/urls.py` mostra as duas rotas
- [ ] `ls backend/painel/templates/painel/` mostra `_celula.html`, `_ranking.html` e `dashboard.html`
- [ ] `python manage.py test painel quiz.tests.test_telas` → tudo verde (depois de A e B)
- [ ] No navegador, como staff: responder o quiz 6 vezes numa janela anônima e abrir `/painel/` → tabelas com `—` nos números pequenos, sem erro

---

## 📬 Depois de corrigir

Cada um abre o PR da sua branch para a `main` e pede revisão. A revisão usa esta nota como lista de conferência.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] — a ordem das rodadas
- [[Projetos/EducMatch(Secretária)/spec-pessoa-a-infra|🧱 Spec A]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-b-dados-motor|🧮 Spec B]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-c-painel|📊 Spec C]]
