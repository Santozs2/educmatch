---
title: "Spec — Pessoa A · Infra (PR-1 settings e fuso · PR-6 CI)"
aliases: ["Spec pessoa A", "Spec infra", "PR-1 infra", "PR-6 CI", "Passo a passo da infra"]
tags: [tcc, backend, django, infra, mysql, ci, spec, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Mapa: [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] · Origem: [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|🔧 BK-08]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-inf-01-inf-05|🧱 INF-04]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|🧪 TST-05]] · Colegas: [[Projetos/EducMatch(Secretária)/spec-pessoa-b-dados-motor|🧮 B]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-c-painel|📊 C]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-d-telas|🎨 D]]

# 🧱 Spec — Pessoa A · Infra

> [!abstract] O que esta nota é
> O **como** da frente de infra, arquivo por arquivo, com o código no lugar certo. Missão em uma frase: fazer o projeto **rodar igual na máquina dos quatro**, com a configuração vinda de variável de ambiente e o MySQL sabendo o fuso de São Paulo, e no fim ligar uma **CI** que roda os testes em todo PR.
> Escrita contra o commit `a04c8e9` (branch `chore/remove-react-e-api`), depois da remoção do React e da API REST.

> [!success] O que já foi verificado (2026-09-22)
> O código do PR-1 foi aplicado numa **cópia** do repositório, no MySQL local:
> - `manage.py check` sem erros, com banco configurado só por variável de ambiente;
> - os 3 testes de página que davam **400** passaram a responder certo só com a troca do `ALLOWED_HOSTS`;
> - o teste de fuso novo fica **vermelho** com as tabelas vazias, como deve.
>
> **Não** verificado: o teste de fuso ficando verde, porque carregar as tabelas muda o MySQL da máquina, e isso cada pessoa faz na sua. E a CI (PR-6), que só roda no GitHub.

## 🧭 O mapa

| Tarefa | O que faz | Arquivo | PR |
|---|---|---|---|
| **A-1** | segredos e banco vindos do ambiente | `core/settings.py` | PR-1 |
| **A-2** | `ALLOWED_HOSTS` com default | `core/settings.py` | PR-1 |
| **A-3** | contrato de ambiente versionado | `.env.example` | PR-1 |
| **A-4** | tabelas de fuso + o teste que avisa | MySQL · `core/tests.py` | PR-1 |
| **A-5** | README "Como rodar" | `README.md` | PR-1 |
| **A-6** | CI e proteção da `main` | `.github/workflows/test.yml` | PR-6 |

> [!note] Por que esta spec não tem `CSRF_TRUSTED_ORIGINS` nem job de `pnpm`
> O front React foi abandonado em 2026-09-22. O front é template do Django, servido pelo mesmo processo, no mesmo endereço (`localhost:8000`). Sem segunda origem não existe problema de CSRF entre origens, e sem `package.json` não existe `pnpm`.

---

## 🚦 Antes de abrir o editor

```bash
cd educmatch
git switch main
git pull                       # já com o PR-0 da pessoa D
git switch -c infra/settings-env
cd backend
source .venv/Scripts/activate
python -c "import django, rest_framework; print(django.__version__, rest_framework.__version__)"
```

Tem de imprimir `5.2.17 3.18.1`. Se não imprimir: `pip install -r requirements.txt`.

Anote a linha de base e mande no grupo. É a referência dos quatro:

```bash
python manage.py test 2>&1 | tail -5
```

> [!important] A linha de base de 2026-09-22
> **28 testes: 7 falhas, 15 erros, 3 pulados.** Quase todos os erros das páginas vêm de uma linha só (`ALLOWED_HOSTS = []`), que é a A-2. O seu PR é o que mais derruba esse número.

> [!tip] Primeiro PR em par, pelo Live Share
> Faça este PR numa sessão de Live Share com a pessoa D. **Você é o anfitrião**, porque a branch é sua. Regra do grupo: código só se escreve na própria branch; no Live Share, quem hospeda é sempre o dono da branch.

---

## 1️⃣ A-1 e A-2 — `core/settings.py`

### O estado de hoje

```python
SECRET_KEY = 'django-insecure-*z=y+!0ola&w4mrc!3xrfzm_0j*d!qc4+%!z-^2hew^u6iuk_6'
DEBUG = True
ALLOWED_HOSTS = []
...
DATABASES = {
    'default': {
        ...
        'USER': 'tecmysql',        # usuário de UMA máquina, commitado no a04c8e9
        'PASSWORD': 'devmysql',
        ...
```

Três problemas numa tela: a chave e a senha estão no Git; o usuário do banco é o de uma pessoa só (quem usa `root` tem de editar o arquivo e tomar cuidado para não commitar); e `ALLOWED_HOSTS` vazio faz toda página responder **400** nos testes.

### O topo do arquivo — substitua até o `ALLOWED_HOSTS` inclusive

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Tudo que muda de uma máquina para outra vem de variável de ambiente.
# Os defaults servem para desenvolvimento; veja backend/.env.example.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-inseguro-troque-em-producao")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]
```

### O bloco `DATABASES` — substitua inteiro

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "educmatch"),
        "USER": os.environ.get("DB_USER", "root"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "3306"),
    }
}
```

### O fim do arquivo — substitua do primeiro `STATIC_URL` até o fim

```python
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
QUIZ_RECOMENDACAO_LIMIT = 5
```

Isso tira o `STATIC_URL` duplicado e o bloco `MAILERS`, que o Django nunca leu (o nome certo da configuração é `EMAIL_BACKEND`).

> [!warning] Não apague `TIME_ZONE`, `USE_TZ`, `LOGIN_URL` nem `QUIZ_RECOMENDACAO_LIMIT`
> O painel depende do fuso, as páginas protegidas dependem do `LOGIN_URL`, e o motor lê o limite.

> [!note] Por que os testes param de dar 400
> O executor de testes do Django acrescenta `testserver` ao `ALLOWED_HOSTS` sozinho, e a base de testes (`quiz/tests/base.py`) usa `localhost`. Com a lista vazia, nem `localhost` passava. Com o default `localhost,127.0.0.1`, passa.

> [!note] Por que não usar `python-dotenv`
> Com `os.environ.get` e um default de desenvolvimento, o projeto roda **sem arquivo nenhum**. É uma dependência a menos para a banca instalar.

---

## 2️⃣ A-3 — `backend/.env.example` (arquivo novo)

```bash
# Copie para .env e ajuste para a sua máquina. O .env NUNCA vai para o Git.
# Para carregar no Git Bash:  set -a; source .env; set +a
DJANGO_SECRET_KEY=troque-por-uma-chave-longa
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=educmatch
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
```

O `.env` já está no `.gitignore` da raiz. Confira antes do commit: `git check-ignore backend/.env` tem de imprimir o caminho.

Cada pessoa cria o seu:

```bash
cp .env.example .env          # e edita DB_USER e DB_PASSWORD
set -a; source .env; set +a   # no terminal onde vai rodar o runserver e os testes
```

---

## 3️⃣ A-4 — as tabelas de fuso do MySQL

### O problema

O projeto usa `USE_TZ = True` com `TIME_ZONE = "America/Sao_Paulo"`. Com fuso diferente de UTC, o Django converte o fuso **dentro do SQL** com `CONVERT_TZ()`. Um MySQL recém-instalado vem com as tabelas de fuso **vazias**, e aí `CONVERT_TZ` devolve `NULL`:

```sql
SELECT CONVERT_TZ(NOW(), 'UTC', 'America/Sao_Paulo');   -- NULL
SELECT COUNT(*) FROM mysql.time_zone_name;              -- 0
```

> [!danger] Por que isso é uma mina embaixo do painel
> Com `CONVERT_TZ` devolvendo `NULL`, **todo** filtro e agrupamento que passa por ele volta vazio: `__date`, `__month`, `TruncDate`, `TruncMonth`. **Sem erro nenhum.** O painel da pessoa C filtra por período. Um gráfico vazio por causa disso consome uma tarde e termina em "deve ser problema do Django".

### O conserto — uma vez por máquina, como root do MySQL

No Windows não existe o `mysql_tzinfo_to_sql`. Usa-se o pacote pronto:

1. Baixe o pacote **POSIX** em `https://dev.mysql.com/downloads/timezones.html`
2. Descompacte e importe:
   ```bash
   mysql -u root -p mysql < timezone_posix.sql
   ```
3. Confira:
   ```sql
   SELECT CONVERT_TZ(NOW(), 'UTC', 'America/Sao_Paulo');   -- tem de devolver uma data
   ```

### O guarda — `backend/core/tests.py` (arquivo novo)

```python
from django.conf import settings
from django.db import connection
from django.test import TestCase


class FusoDoMySQL(TestCase):
    """Com TIME_ZONE fora de UTC, o Django converte fuso DENTRO do SQL
    (CONVERT_TZ). Sem as tabelas de fuso, a conversão devolve NULL e todo
    filtro por __date, __month ou TruncDate volta vazio, sem erro."""

    def test_mysql_conhece_o_fuso_de_sao_paulo(self):
        with connection.cursor() as cursor:
            cursor.execute("select CONVERT_TZ(NOW(), 'UTC', %s)", [settings.TIME_ZONE])
            convertido = cursor.fetchone()[0]

        self.assertIsNotNone(
            convertido,
            "as tabelas de fuso do MySQL estao vazias: veja o README, secao 'Tabelas de fuso'",
        )
```

Rode **antes** de carregar as tabelas: fica vermelho, com a instrução no texto da falha. Depois: verde. É o seu "teste que falharia antes".

> [!important] Um teste vermelho de propósito vale mais do que um aviso no grupo
> Quem clonar o projeto descobre no primeiro `manage.py test`, não no dia em que um gráfico do painel voltar vazio.

> [!warning] Não troque o `TIME_ZONE` para `"UTC"` para fugir disso
> Funciona, mas toda hora na tela fica três horas adiantada. Na defesa, "18:40" quando eram 15:40 é pergunta da banca na certa (decisão D4 do plano v0.2).

---

## 4️⃣ A-5 — `README.md`, seção "Como rodar"

Substitua a parte do backend por:

````markdown
## Como rodar

Um servidor só: o Django serve as páginas e o `/admin`.

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # ajuste DB_USER e DB_PASSWORD
set -a; source .env; set +a
python manage.py migrate
python manage.py seed_areas && python manage.py seed_cursos && python manage.py seed_questoes
python manage.py runserver           # http://localhost:8000
```

Confira o catálogo pelo número: `12` áreas, `20` cursos, `73` pesos.

### Tabelas de fuso (uma vez por máquina)

O MySQL vem sem as tabelas de fuso, e sem elas os filtros por data do painel voltam vazios.
Baixe o pacote POSIX em https://dev.mysql.com/downloads/timezones.html e rode:

```bash
mysql -u root -p mysql < timezone_posix.sql
```

O teste `python manage.py test core` diz se deu certo.
````

---

## 5️⃣ Verificação do PR-1

```bash
python manage.py check                         # sem erros
python manage.py test core                     # verde depois das tabelas de fuso
python manage.py test 2>&1 | tail -5           # compare com a linha de base
git diff main -- backend/core/settings.py      # nenhuma senha ou chave de verdade
```

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | `runserver` sem o `.env` carregado | Sobe (usa os defaults) e reclama de acesso ao banco só se o seu usuário não for `root` |
| 2 | `runserver` com o `.env` carregado | `/`, `/entrar/` e `/admin/` abrem |
| 3 | A suíte inteira | Os testes de página (`test_rotas_web`) passam; o total de falhas e erros **cai** |
| 4 | `git status` | O `.env` **não** aparece |

---

## 6️⃣ Commit, push e PR

```bash
git add backend/core/settings.py backend/core/tests.py backend/.env.example README.md
git status --short
git commit -m "feat(infra): settings por variavel de ambiente e fuso do MySQL"
git push -u origin infra/settings-env
```

```markdown
## O que muda
- SECRET_KEY, DEBUG, ALLOWED_HOSTS e banco vêm de variável de ambiente (.env.example)
- ALLOWED_HOSTS com default localhost: os testes de página param de dar 400
- Teste que falha se o MySQL não tiver as tabelas de fuso
- README: como rodar com .env e como carregar as tabelas de fuso

## Testes
Antes: 7 falhas e 15 erros. Depois: X falhas e Y erros. Nenhuma falha nova.

## Atenção, grupo
1. Criem o .env de vocês (cp .env.example .env) e carreguem as tabelas de fuso.
2. A SECRET_KEY e a senha antigas estão no histórico do Git: troquem a senha do MySQL.
```

Mesclar com **Squash and merge** e avisar no grupo.

---

## 7️⃣ Rodada 2 — revisar e testar no navegador

Enquanto B, C e D trabalham, você é quem mais testa:

- [ ] Revisar cada PR que abrir, em até 24 h
- [ ] Para cada PR de tela: `git switch <branch>`, `runserver`, clicar em tudo que o PR diz que mudou, e escrever no PR o que deu errado, com print

---

## 8️⃣ A-6 — a CI (PR-6)

```bash
git switch main && git pull
git switch -c test/ci
```

### `.github/workflows/test.yml` (arquivo novo, na **raiz** do repositório)

```
educmatch/                  ← raiz do repositório (onde está o .git)
├── .github/
│   └── workflows/
│       └── test.yml        ← aqui, e não dentro de backend/
├── backend/
└── docs/
```

```bash
mkdir -p .github/workflows      # rodando na raiz; o Explorador do Windows não gosta de pasta com ponto
```

> [!warning] O GitHub só lê workflows em `.github/workflows/` na raiz
> Em qualquer outro lugar o arquivo é ignorado, sem aviso. É por isso que o workflow abaixo tem `working-directory: backend`: o arquivo mora na raiz, e os comandos entram em `backend/`.

```yaml
name: testes

on:
  pull_request:
  push:
    branches: [main]

jobs:
  django:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: raiz
          MYSQL_DATABASE: educmatch
        ports: ["3306:3306"]
        options: >-
          --health-cmd="mysqladmin ping -praiz"
          --health-interval=5s --health-timeout=5s --health-retries=20

    env:
      DJANGO_SECRET_KEY: so-para-a-ci
      DB_NAME: educmatch
      DB_USER: root
      DB_PASSWORD: raiz
      DB_HOST: 127.0.0.1
      DB_PORT: "3306"

    defaults:
      run:
        working-directory: backend

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Dependências do sistema para o mysqlclient
        run: sudo apt-get update && sudo apt-get install -y pkg-config libmysqlclient-dev

      - name: Tabelas de fuso no MySQL do job
        run: mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -h 127.0.0.1 -uroot -praiz mysql

      - run: pip install -r requirements.txt

      - name: Nenhuma migração esquecida
        run: python manage.py makemigrations --check --dry-run

      - run: python manage.py test -v 2
```

> [!note] No Linux da CI o `mysql_tzinfo_to_sql` existe
> É a mesma coisa que o pacote POSIX faz no Windows, lida direto do `/usr/share/zoneinfo` do sistema.

### A proteção da `main`

**Só ligue quando a suíte estiver verde.** No GitHub, *Settings → Branches → Add rule* para `main`:

- [ ] Require a pull request before merging
- [ ] Require approvals: **1**
- [ ] Require status checks to pass → marcar `django`
- [ ] Automatically delete head branches

> [!important] A lição que a CI resolve
> A suíte de testes do projeto já se perdeu uma vez, e ninguém percebeu por três semanas, porque nada rodava os testes sozinho. **Suíte sem gatilho automático é documentação, não garantia.** É um parágrafo curto e forte para a monografia.

### Verificação do PR-6

| # | O quê | Sinal |
|---|---|---|
| 1 | Abrir o PR-6 | O check `testes / django` aparece e fica verde |
| 2 | Numa branch de rascunho, quebrar um teste de propósito | O check fica **vermelho** (depois apague a branch) |
| 3 | O exercício "quebre de propósito" da [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|TST]] §6 | Cada quebra acende o teste certo. Guarde a saída de `test -v 2`: é anexo da monografia |

---

## ▶️ Próxima ação

Criar a branch `infra/settings-env` e fazer a §1. Com o PR-1 mesclado, **avisar o grupo** para criar o `.env` e carregar as tabelas de fuso.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-inf-01-inf-05|🧱 INF-01 a INF-05]] — a origem da INF-04
- [[Projetos/EducMatch(Secretária)/plano-execucao-v02|🗺️ Plano v0.2]] — decisões D1 a D5 e a seção 3 (por que MySQL)
