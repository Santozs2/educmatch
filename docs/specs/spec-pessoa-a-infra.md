---
title: "Spec — Pessoa A · Infra (settings, fuso do MySQL e CI)"
aliases: ["Spec pessoa A", "Spec infra", "PR-1 infra", "PR-6 CI"]
tags: [tcc, backend, django, infra, mysql, ci, spec]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Visão geral: [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] · Código de referência: [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|🔧 BK-01 a BK-08]] §7 · [[Projetos/EducMatch(Secretária)/passo-a-passo-inf-01-inf-05|🧱 INF-04]] · Colegas: [[Projetos/EducMatch(Secretária)/spec-pessoa-b-dados-motor|🧮 B]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-c-painel|📊 C]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-d-telas|🎨 D]]

# 🧱 Spec — Pessoa A · Infra

> [!abstract] Sua missão em uma frase
> Deixar o projeto **rodando igual na máquina dos quatro**, com as configurações vindas de variável de ambiente e o MySQL sabendo o fuso de São Paulo, e no fim ligar uma **CI** que roda os testes em todo PR.

> [!note] O front é de templates do Django
> O React foi abandonado em 2026-09-22 e a API REST foi removida. O front é HTML, CSS e JS puro servido pelo próprio Django: um processo só, um endereço só (`localhost:8000`). Por isso esta spec **não** tem mais `CSRF_TRUSTED_ORIGINS`, `FRONTEND_URL` nem job de `pnpm` na CI.

| PR | Branch | Quando | Tamanho |
|---|---|---|---|
| **PR-1** | `infra/settings-env` | Rodada 1. É o primeiro PR de código a mesclar, logo depois do PR-0 da pessoa D | Pequeno: 1 dia |
| **PR-6** | `test/ci` | Rodadas 3 e 4. É o último a mesclar | Médio |

Na rodada 2 você revisa PRs e testa as telas dos outros no navegador.

---

## 1️⃣ Por que isso importa

- **Hoje metade da suíte de testes falha por um motivo só.** `ALLOWED_HOSTS = []` faz toda página responder **400** nos testes. Medido em 2026-09-22: 28 testes, **7 falhas e 15 erros**. Quase todos somem com o seu PR, e isso destrava os testes dos outros três.
- **A `SECRET_KEY` e a senha do banco estão escritas no código** (`backend/core/settings.py`). Qualquer um que veja o repositório vê as duas. Na banca, isso é falha de segurança básica.
- **Cada pessoa tem um usuário de MySQL diferente.** Hoje quem usa `tecmysql` precisa editar o `settings.py` e toma cuidado para não commitar. Com variável de ambiente, cada um configura a própria máquina e o arquivo versionado não muda.
- **O MySQL vem com as tabelas de fuso vazias.** O projeto usa `TIME_ZONE = "America/Sao_Paulo"`, e aí todo filtro por data (`__date`, `TruncDate`, `__month`) **volta vazio, sem erro nenhum**. O painel da pessoa C filtra por período: sem isso, os gráficos dela saem vazios.
- **A suíte de testes já se perdeu uma vez** porque nada rodava os testes sozinho. A CI é a correção estrutural disso.

---

## 2️⃣ O que é seu (e o que não é)

| ✅ Você pode mexer | ❌ Não mexa |
|---|---|
| `backend/core/settings.py` | `models.py` e migrações → **B** |
| `backend/.env.example` (novo) | `painel/` → **C** |
| `backend/core/tests.py` (novo) | `templates/`, `static/`, `web_views.py`, `accounts/views.py` → **D** |
| `.github/workflows/` (novo) | |
| `README.md`, seção "Como rodar" | |

---

## 3️⃣ Antes de começar

```bash
cd educmatch
git switch main
git pull                   # já com o PR-0 da pessoa D (React e API REST removidos)
git switch -c infra/settings-env
cd backend
source .venv/Scripts/activate
python -c "import django, rest_framework; print(django.__version__, rest_framework.__version__)"
python manage.py test 2>&1 | tail -5     # a linha de base: anote e mande no grupo
```

A primeira linha tem de imprimir `5.2.17 3.18.1`. Se não imprimir: `pip install -r requirements.txt`.

> [!tip] Primeiro PR em par, pelo Live Share
> Se for o seu primeiro PR, faça esta seção e a §6 numa sessão de Live Share com a pessoa D. **Você é o anfitrião**, porque a branch é sua. A regra do grupo é: código só se escreve na própria branch; no Live Share, quem hospeda é sempre o dono da branch.

---

## 4️⃣ PR-1 — passo a passo

### Passo 1 · `core/settings.py` lendo do ambiente

Troque as linhas de `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` e o bloco `DATABASES` inteiro por:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-inseguro-troque-em-producao")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

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

- [ ] Apague o bloco `MAILERS` e coloque no lugar: `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"`
- [ ] Deixe **um só** `STATIC_URL = "static/"` (hoje ele aparece duas vezes) e `STATICFILES_DIRS = [BASE_DIR / "static"]`
- [ ] **Não** apague `TIME_ZONE`, `USE_TZ`, `LOGIN_URL` nem `QUIZ_RECOMENDACAO_LIMIT`

> [!note] Por que os testes voltam a funcionar
> O executor de testes do Django acrescenta `testserver` ao `ALLOWED_HOSTS` sozinho, e a base de testes usa `localhost`. Com a lista vazia, nem `localhost` passava. Com o default `localhost,127.0.0.1`, passa.

> [!note] Por que não usar `python-dotenv`
> Com `os.environ.get` e um default de desenvolvimento, o projeto roda **sem arquivo nenhum**. É uma dependência a menos para a banca instalar. Quem quiser usar o `.env` exporta no shell: `set -a; source .env; set +a`.

### Passo 2 · `backend/.env.example` (arquivo novo)

```bash
DJANGO_SECRET_KEY=troque-por-uma-chave-longa
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=educmatch
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
```

- [ ] Confira que `.env` está no `backend/.gitignore`. O `.env.example` **vai** para o Git; o `.env` **nunca**.

### Passo 3 · tabelas de fuso do MySQL (INF-04)

Isto é feito **no MySQL**, não no código. No Windows não existe o `mysql_tzinfo_to_sql`, então:

1. Baixe o pacote **POSIX** em `https://dev.mysql.com/downloads/timezones.html`
2. Descompacte e importe:
   ```bash
   mysql -u root -p mysql < timezone_posix.sql
   ```
3. Confirme no MySQL:
   ```sql
   SELECT CONVERT_TZ(NOW(), 'UTC', 'America/Sao_Paulo');   -- tem de devolver uma data, não NULL
   ```

### Passo 4 · o teste que avisa quem clonar (`backend/core/tests.py`, novo)

```python
from django.conf import settings
from django.db import connection
from django.test import TestCase


class FusoDoMySQL(TestCase):
    def test_mysql_conhece_o_fuso_de_sao_paulo(self):
        with connection.cursor() as cursor:
            cursor.execute("select CONVERT_TZ(NOW(), 'UTC', %s)", [settings.TIME_ZONE])
            convertido = cursor.fetchone()[0]

        self.assertIsNotNone(
            convertido,
            "as tabelas de fuso do MySQL estao vazias: veja o README, secao 'Tabelas de fuso'",
        )
```

Rode **antes** do passo 3 e ele fica vermelho; depois, verde. É o seu "teste que falharia antes".

### Passo 5 · README, seção "Como rodar"

- [ ] Como criar o `.env` a partir do `.env.example` e exportar no shell
- [ ] A seção **"Tabelas de fuso"**, com os comandos do passo 3. **Cada pessoa** precisa rodar isso uma vez no próprio MySQL
- [ ] Um só servidor: `python manage.py runserver` e abrir `http://localhost:8000`

### Passo 6 · avisar o grupo

- [ ] A **`SECRET_KEY` antiga e a senha antiga do MySQL estão no histórico do Git**. Tirar do arquivo não apaga do histórico. Cada um troca a senha do próprio MySQL, e ninguém reaproveita aquela chave.
- [ ] Quem tinha mudado o `USER` do banco direto no `settings.py` (por exemplo, `tecmysql`) desfaz essa mudança e passa a usar `DB_USER` no `.env`.

---

## 5️⃣ PR-1 — pronto quando

- [ ] `python manage.py check` sem erros
- [ ] `python manage.py runserver` sobe; `/`, `/entrar/` e `/admin/` abrem
- [ ] `python manage.py test core` verde (depois das tabelas de fuso)
- [ ] `python manage.py test`: **nenhuma falha nova**, e o total de falhas e erros **cai** em relação à linha de base. Escreva os dois números no PR
- [ ] `git diff main` sem nenhuma senha ou chave de verdade

### Como abrir o PR

```bash
git add backend/core/settings.py backend/core/tests.py backend/.env.example README.md
git status --short          # confira: nada de .env, nada de __pycache__
git commit -m "feat(infra): settings por variavel de ambiente e fuso do MySQL"
git push -u origin infra/settings-env
```

Texto do PR:

```markdown
## O que muda
- SECRET_KEY, DEBUG, ALLOWED_HOSTS e banco vêm de variável de ambiente (.env.example)
- ALLOWED_HOSTS com default localhost: os testes de página param de dar 400
- Teste que falha se o MySQL não tiver as tabelas de fuso

## Testes
Antes: X falhas e Y erros. Depois: X' falhas e Y' erros. Nenhuma falha nova.

## Como testar
1. Carregar as tabelas de fuso (README, seção "Tabelas de fuso")
2. python manage.py test

## Atenção, grupo
A SECRET_KEY e a senha antigas estão no histórico do Git: troquem a senha do MySQL de vocês.
```

Peça revisão para qualquer um dos outros três. Mesclar com **Squash and merge** e avisar no grupo: "PR-1 entrou: `git pull` e criem o `.env` de vocês".

---

## 6️⃣ Rodada 2 — revisar e testar no navegador

- [ ] Revisar os PRs que abrirem na rodada (prazo combinado: 24 h)
- [ ] Para cada PR de tela (C e D): trocar para a branch (`git switch <branch>`), subir o `runserver` e clicar em tudo que o PR diz que mudou. Anotar no PR o que der errado, com print

---

## 7️⃣ PR-6 — a CI (rodadas 3 e 4)

Referência: [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|🧪 TST-01 a TST-05]] §5 (TST-05). O que o workflow precisa ter:

- [ ] `.github/workflows/test.yml` disparando em `pull_request` e em `push` para `main`
- [ ] Um serviço **MySQL 8.0** no job, com usuário que tenha permissão de `CREATE` (o Django cria o banco `test_educmatch`)
- [ ] Um passo que **carrega as tabelas de fuso** no MySQL do job (sem isso, o seu teste do passo 4 fica vermelho na CI)
- [ ] As variáveis `DB_*` apontando para o serviço, e `DJANGO_SECRET_KEY` com qualquer valor
- [ ] `pip install -r backend/requirements.txt`, `python manage.py makemigrations --check --dry-run` e `python manage.py test`, dentro de `backend/`

**Só ligue a proteção da `main` quando a suíte estiver verde.** No GitHub, em *Settings → Branches → Add rule* para `main`:
- [ ] Require a pull request before merging
- [ ] Require approvals: **1**
- [ ] Require status checks to pass → marcar o job de testes
- [ ] Automatically delete head branches

### PR-6 — pronto quando

- [ ] A CI roda sozinha num PR e fica **verde**
- [ ] Você quebrou um teste de propósito numa branch de rascunho e a CI ficou **vermelha** (depois apague essa branch)
- [ ] Rodou o exercício "quebre de propósito" da TST §6 e guardou a saída de `python manage.py test -v 2`, que vai de anexo na monografia

---

## 8️⃣ Armadilhas

> [!danger] Rodar sem erro não é sinal de sucesso
> O `seed_cursos` já "não deu erro" enquanto apagava o catálogo em silêncio. Depois de qualquer mudança, confira o **número**: `12` áreas, `20` cursos e `73` pesos.
> ```bash
> python manage.py shell -c "from catalogo.models import Area, Curso, Peso_curso; print(Area.objects.count(), Curso.objects.count(), Peso_curso.objects.count())"
> ```

> [!warning] Não troque o `TIME_ZONE` para `"UTC"` para fugir das tabelas de fuso
> Funciona, mas toda hora na tela fica três horas adiantada. Na defesa, "18:40" quando eram 15:40 é pergunta da banca na certa. O grupo já decidiu isso (D4 do plano v0.2).
