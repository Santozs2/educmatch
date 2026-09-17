---
title: "Passo a passo — SB-01 a SB-06 (segredos fora do código e migração para o Supabase)"
aliases: ["Passo a passo SB", "Migrar para o Supabase", "Django no Supabase", "Fase 1 do plano v0.2", "MySQL para Postgres no TCC"]
tags: [tcc, infra, supabase, postgres, django, execucao, passo-a-passo, seguranca]
status: proposto
projeto: TCC
criado: 2026-09-17
---

> [!info] Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-v02-supabase-a-testes|🗺️ Plano v0.2]] · Auditoria: [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 REV-06 e REV-07]] · Git: [[git-ritual-de-entrega-do-tcc|🧾 Ritual de entrega]] · Próxima fase: [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 REC-01 a REC-06]]

# 🗄️ Passo a passo — SB-01 a SB-06

> [!abstract] O que esta nota é
> O **como** da Fase 1: tirar os segredos do código versionado e trocar o MySQL local por um Postgres gerenciado no Supabase. Arquivo por arquivo, com os comandos que provam que funcionou.
> São **dois PRs**, não um. O primeiro não troca de banco — e é justamente por isso que ele existe.

> [!warning] Nada disto foi executado
> Escrito contra as notas de auditoria do vault, não contra o repositório aberto. Os caminhos (`core/settings.py`, `accounts/models.py:34-47`) vêm de [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|REV-06 e REV-07]], registrados em 11/09/2026. **Confirme cada arquivo antes de colar.** A seção 8 é o que prova que deu certo — não pule nenhum comando dela.

## 🧭 Estado das decisões

| | Decisão | Estado |
|---|---|---|
| **D1** | Supabase entra só como **Postgres gerenciado** — sem Auth, sem Storage | ✅ **decidida no plano** — e a seção 2 explica o que quebraria |
| **D2** | Conexão pelo **Session Pooler**, porta 5432 | ✅ decidida — a seção 2 mostra as três opções e por que as outras duas falham aqui |
| **D3** | `manage.py test` roda em **Postgres local** | ✅ decidida — montada na SB-05 |
| **D4** | `USE_TZ = True` agora | ⚠️ **assumida** — custo e consequência na SB-04 |
| **D5** | Vocabulário fica em português, com glossário | ⚠️ assumida — a SB-06 é a única janela barata para os dois nomes errados |

> [!success] Por que dois PRs e não um
> **PR-1 (SB-01)** externaliza configuração e **não muda nada de funcional**: o `DATABASE_URL` continua apontando para o MySQL de cada um. É revisável em cinco minutos, não quebra ninguém que tenha criado o `.env`, e todo o grupo já se acostuma ao arquivo novo.
> **PR-2 (SB-02 a SB-06)** troca o valor dessa variável e leva os dados.
> O ganho é o *rollback*: depois do PR-1, voltar do Supabase para o MySQL é **editar uma linha do `.env`** — não é `git revert` com migração pendente no meio.

---

## 🚦 Antes de abrir o editor

```bash
git checkout main && git pull
git checkout -b feat/infra-supabase
```

Confirme o estado do repositório antes de qualquer coisa — o [[Projetos/EducMatch(Secretária)/plano-execucao-v02-supabase-a-testes|plano]] explica por que isto não é formalidade:

```bash
ls && ls quiz/ accounts/
./.venv/Scripts/python.exe -c "import django; print(django.get_version())"
./.venv/Scripts/python.exe manage.py showmigrations
```

> [!danger] Rode **sempre** pela `.venv`
> O Python global desta máquina está com Django 6.1.1, que exige MySQL 8.4+ enquanto o servidor local é 8.0.46. Fora da *venv*, qualquer comando falha com `NotSupportedError` **antes** de tocar no código — e você perde meia hora depurando o lugar errado. A `.venv` tem Django 4.2.30, e ele fica assim durante as quatro fases.

---

## 1️⃣ SB-01 — segredos fora do código · **PR-1**

Este é o `REV-06` da auditoria: senha do MySQL e `SECRET_KEY` em claro em `core/settings.py`, `DEBUG=True` fixo e `ALLOWED_HOSTS` vazio.

### As três dependências novas

```bash
./.venv/Scripts/python.exe -m pip install python-dotenv dj-database-url psycopg2-binary
```

| Pacote | Para quê |
|---|---|
| `python-dotenv` | ler o arquivo `.env` |
| `dj-database-url` | transformar uma URL de banco na configuração que o Django espera |
| `psycopg2-binary` | o *driver* do Postgres — instalado já agora, usado no PR-2 |

> [!note] `psycopg2-binary` e não `psycopg[binary]`
> O Django 4.2 aceita os dois, mas o `psycopg2-binary` tem *wheel* pronto para Windows e não pede compilador. O `psycopg` 3 é o caminho quando o projeto subir para o Django 5 — que **não** é agora.

### `core/settings.py` — o topo do arquivo

Substitua o começo do arquivo por este bloco. Mantenha tudo o que vem depois de `INSTALLED_APPS` como está.

```python
from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

# Sem valor padrao de proposito: se faltar, o erro aparece aqui e agora,
# e nao em producao com uma chave previsivel.
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
```

E, no lugar do bloco `DATABASES` inteiro:

```python
DATABASES = {
    "default": dj_database_url.parse(
        os.environ["DATABASE_URL"],
        conn_max_age=0,
    )
}
```

> [!danger] `os.environ["..."]` com colchete, não `.get()`
> `os.environ.get("DJANGO_SECRET_KEY", "django-insecure-...")` parece mais gentil e é a armadilha: o projeto sobe com a chave de exemplo, ninguém percebe, e a chave de exemplo vira a chave de verdade. Com colchete, quem esquecer o `.env` recebe `KeyError: 'DJANGO_SECRET_KEY'` no primeiro comando — dois segundos para diagnosticar.
> É a mesma lógica de `Choice.objects.get()` em vez de `filter().first()` já registrada em [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]]: **prefira a função que falha alto à que escolhe em silêncio.**

> [!warning] `DEBUG` lido como texto, comparado com `"true"`
> `bool(os.environ.get("DJANGO_DEBUG"))` é `True` para a string `"false"` — toda string não vazia é verdadeira em Python. É um dos erros mais comuns de configuração por ambiente, e o sintoma é o pior possível: **produção rodando com `DEBUG=True`**, exibindo *traceback* com trechos de código e valores de variáveis para qualquer visitante.

> [!warning] `ALLOWED_HOSTS` vazio derruba a aplicação no minuto em que `DEBUG` virar `False`
> Com `DEBUG=True` o Django aceita `localhost` sozinho, então o defeito fica invisível. No `.env` de desenvolvimento, `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` resolve. Para os testes, some `testserver` — ou passe `Client(SERVER_NAME="localhost")`, como [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições]] já registrou para o `DisallowedHost: 'testserver'`.

### `core/settings.py` — mais duas linhas, no bloco de internacionalização

```python
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
```

> [!important] `USE_TZ = True` é decisão de banco, e o momento é este (D4)
> Com `USE_TZ = True`, o Django grava `timestamptz` no Postgres e trata toda data em UTC internamente. Ligar isso **depois** de haver dado real faz o Postgres reinterpretar as datas já gravadas como se fossem UTC — e toda a série temporal anda três horas.
> Agora o custo é zero, porque: (a) o banco vai ser recriado nesta fase; (b) a auditoria já declarou o histórico impreciso no `REV-01` (`Interesse.criado_em` é `auto_now`); (c) o painel da Fase 3 filtra tudo por período e precisa de uma base temporal confiável.
> Pagar uma vez, aqui. Pagar duas vezes, depois.

### `.env` — arquivo novo, **nunca versionado**

```bash
DJANGO_SECRET_KEY=cole-aqui-a-chave-gerada-abaixo
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# PR-1: continua o MySQL local de sempre
DATABASE_URL=mysql://root:SENHA_LOCAL@127.0.0.1:3306/educmatch
```

Gerando uma chave nova:

```bash
./.venv/Scripts/python.exe -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

> [!danger] Gere uma chave **nova**. Não reaproveite a que está no `settings.py`
> A que está lá hoje está no histórico do Git para sempre. Mesmo apagando o arquivo, `git show <commit>:core/settings.py` ainda a devolve. **Considere-a queimada** — e o mesmo vale para a senha do MySQL: troque-a no servidor local, não só no arquivo. É o que `REV-06` quer dizer com *"o histórico não se limpa sozinho"*.

### `.env.example` — este sim, versionado

```bash
DJANGO_SECRET_KEY=
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# Desenvolvimento e demonstracao: Supabase (Session Pooler, porta 5432)
# Copie a URL exata do painel do Supabase e troque [SUA-SENHA]
DATABASE_URL=

# Teste: Postgres local. Nunca aponte para o Supabase aqui (ver SB-05)
DATABASE_URL_TEST=postgresql://postgres:postgres@127.0.0.1:5432/educmatch_test
```

> [!tip] O `.env.example` é o contrato de ambiente do grupo
> É o único lugar onde está escrito **quais** variáveis existem. Quem clonar o repositório copia, preenche e roda. Toda variável nova entra aqui **no mesmo PR** que a introduziu — senão o próximo a clonar descobre a falta por `KeyError`.

### `.gitignore`

```gitignore
.env
.env.local
*.env
!.env.example

.venv/
__pycache__/
*.pyc

db.sqlite3
dados-*.json
*.log
```

> [!danger] `dados-*.json` antes de a SB-04 precisar
> A saída de `manage.py dumpdata` carrega e-mail, nome e hash de senha de quem criou conta, além de `respondido_por` — texto livre digitado por aluno. Se o `.gitignore` não cobrir o padrão **antes** do dump existir, um `git add -A` distraído publica dado pessoal num repositório do GitHub.

---

## 2️⃣ SB-02 — o projeto no Supabase e a string de conexão

### Criando o projeto

1. `supabase.com` → **New project**
2. **Name:** `educmatch` · **Region:** `South America (São Paulo)` — latência importa para quem vai demonstrar ao vivo
3. **Database password:** gere e **guarde**. Ela não aparece de novo
4. Espere o provisionamento (~2 min)

> [!danger] Gere a senha **sem** caracteres especiais
> A senha entra numa URL. Um `@`, um `#`, uma `/` ou um `:` dentro dela quebra a leitura da URL, e o erro que aparece não fala de senha:
> ```
> could not translate host name "..." to address
> ```
> Se o painel gerar uma senha com símbolos, ou troque por uma longa de letras e números, ou codifique cada símbolo em percent-encoding (`@` → `%40`). A primeira opção economiza uma hora.

### As três formas de conectar — e por que só uma serve

No painel: **Connect** (ou *Project Settings → Database*). O Supabase oferece três strings, e a diferença entre elas é a causa mais comum de "no meu computador não conecta":

| Modo | Porta | O que acontece aqui |
|---|---|---|
| **Direct connection** (`db.<ref>.supabase.co`) | 5432 | resolve só por **IPv6**. Em rede doméstica ou de escola sem IPv6, o comando simplesmente **pendura** até dar *timeout* — sem mensagem útil |
| **Transaction pooler** | 6543 | não mantém estado de sessão; *prepared statements* e cursores do servidor não funcionam. O `migrate` e várias consultas do Django quebram de formas difíceis de ler |
| ✅ **Session pooler** (`...pooler.supabase.com`) | **5432** | IPv4, comporta-se como um Postgres de verdade. `migrate`, `dumpdata`, `loaddata` e o ORM funcionam sem adaptação |

**Use o Session Pooler.** É a D2 do plano.

```bash
# .env — PR-2. Copie a URL EXATA do painel e troque só a senha
DATABASE_URL=postgresql://postgres.abcdefghijklmnop:SUA_SENHA@aws-0-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require
```

> [!warning] Copie do painel, não monte à mão
> O usuário do pooler é `postgres.<ref-do-projeto>`, com ponto — não `postgres`. O host tem um prefixo (`aws-0`, `aws-1`…) que **varia por projeto** e não é adivinhável. Montar a URL de cabeça produz `FATAL: Tenant or user not found`, que parece problema de senha e não é.

> [!note] `conn_max_age=0` é de propósito
> Conexão persistente é uma otimização — e aqui ela custa mais do que rende. Quatro pessoas desenvolvendo, cada uma com um `runserver` e um `shell` aberto, contra o limite de clientes do *pooler* no plano gratuito, dá `remaining connection slots are reserved` numa terça-feira à tarde. `0` fecha a conexão ao fim de cada requisição. Revisitem só se a latência incomodar na demonstração.

> [!success] O que **não** entra no `.env`, nunca
> As chaves `anon` e `service_role` que o painel exibe com destaque. Elas existem para quem usa a API REST do Supabase direto do navegador — ver a **D1** do [[Projetos/EducMatch(Secretária)/plano-execucao-v02-supabase-a-testes|plano]]. Aqui o único cliente do banco é o Django, autenticado por senha. Se alguém já copiou essas chaves para algum arquivo, apague.

---

## 3️⃣ SB-03 — não migre lixo (`REV-07`)

Antes de levar dado nenhum, tire do esquema o que não deveria existir. **Este é o único momento barato**: o banco vai ser recriado, e as tabelas simplesmente não nascem do outro lado.

### `accounts/models.py` — apague as classes `Login` e `Cadastro`

São resquício de antes do `AbstractUser` (linhas 34-47 na auditoria). Nenhuma view usa. O problema é o que elas têm dentro:

```python
# APAGAR — as duas classes inteiras
class Login(models.Model):
    ...
    senha = models.CharField(max_length=128)   # senha em texto puro
```

Três razões, em ordem de gravidade:

1. **Campo de senha em texto puro no schema.** Se alguém algum dia escrever numa dessas tabelas, grava senha legível. É o tipo de achado que a banca pergunta.
2. **Aparecem no DER.** O [[der-escopo-banco 🟢|📐 escopo do DER]] é documento de entrega, e duas tabelas mortas nele são duas perguntas que ninguém quer responder na apresentação.
3. Levá-las para o Postgres é criar tabela nova, em 2026, para código que já morreu.

```bash
./.venv/Scripts/python.exe manage.py makemigrations accounts -n remove_models_mortos
```

> [!warning] Confira o arquivo gerado antes de seguir
> Tem de conter **só** `DeleteModel` para `Login` e `Cadastro`. Se aparecer `AlterField` ou `RemoveField` de outro model, algo mais mudou em `accounts/models.py` desde a última migração — pare, entenda o que é, e não empacote junto. Migração com duas intenções dentro é migração que ninguém consegue reverter.

> [!note] Não mexa em `Interesse` agora
> O `REV-01` (`criado_em` com `auto_now`) e os três campos de *snapshot* do `C4` são da **Fase 2**, num único bloco de migração no mesmo model. Adiantar meio campo aqui é criar duas migrações onde uma resolve. Ver [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 REC-01 a REC-06]].

---

## 4️⃣ SB-04 — levar o esquema e os dados

### Primeiro, a pergunta que decide o caminho

**O que existe hoje no MySQL que os `seed_*` não sabem recriar?**

| Dado | Recriável por seed? |
|---|---|
| Áreas, cursos, pesos, questões, alternativas | ✅ `seed_areas`, `seed_cursos`, `seed_questoes` |
| Usuários e superusuário | ❌ mas `createsuperuser` resolve em 20 s |
| Tentativas, respostas, recomendações | ❌ — e são dado de desenvolvimento |
| Interesses | ❌ — e são dado de desenvolvimento |

```bash
./.venv/Scripts/python.exe manage.py shell -c "from quiz.models import Tentativa_de_resposta as T; print(T.objects.count())"
```

> [!important] Se o número for pequeno, **comece limpo**. É o caminho recomendado
> Tentativa de teste não é dado de pesquisa: não houve consentimento, não houve instrumento estável, e o `REV-01` já diz que as datas estão erradas. Levar essas linhas para o banco definitivo é carregar ruído que depois vai ter de ser filtrado na análise — e alguém vai esquecer de filtrar.
> Faça o dump de qualquer forma (é grátis) e guarde-o **fora da pasta do projeto**, como rede de segurança. Não o use.

### Caminho A — começar limpo (recomendado)

```bash
# 1. rede de segurança, guardada FORA do repositorio
./.venv/Scripts/python.exe manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.permission -e admin.logentry -e sessions \
  --indent 2 -o ../backup-mysql-2026-09-17.json

# 2. troque DATABASE_URL no .env para a URL do Supabase

# 3. o esquema inteiro nasce no Postgres
./.venv/Scripts/python.exe manage.py migrate

# 4. os dados de catalogo, na ordem de sempre
./.venv/Scripts/python.exe manage.py seed_areas
./.venv/Scripts/python.exe manage.py seed_cursos
./.venv/Scripts/python.exe manage.py seed_questoes
./.venv/Scripts/python.exe manage.py createsuperuser
```

> [!tip] `-o arquivo.json`, nunca `> arquivo.json`
> O `-o` faz o Django escrever o arquivo em UTF-8 por conta própria. O `>` do shell passa pelo console do Windows e quebra em `UnicodeEncodeError` no primeiro nome de curso com acento — o mesmo `cp1252` já registrado em [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições, Ambiente]].

> [!warning] Os nomes dos comandos de seed podem ser outros
> A auditoria cita `seed_areas.py` e `seed_cursos.py`; as notas antigas citam `seed_questions`. Confirme antes:
> ```bash
> ./.venv/Scripts/python.exe manage.py help | grep -i seed
> ```

### Caminho B — levar os dados

Só se o grupo decidir que as tentativas importam. Depois do `migrate` no Postgres:

```bash
./.venv/Scripts/python.exe manage.py loaddata ../backup-mysql-2026-09-17.json
```

> [!danger] As quatro exclusões do `dumpdata` não são opcionais
> `-e contenttypes -e auth.permission -e admin.logentry -e sessions`. Sem elas o `loaddata` estoura com:
> ```
> IntegrityError: duplicate key value violates unique constraint
> "django_content_type_app_label_model_76bd3d3b_uniq"
> ```
> Porque o `migrate` **já criou** os `ContentType` e as `Permission` do lado novo, e o dump tenta criá-los de novo com outros ids. O `--natural-foreign` existe para que as chaves estrangeiras que apontam para `ContentType` sejam gravadas por nome de app e model, e não pelo id — que é diferente nos dois bancos.

> [!note] Sequências do Postgres
> O `loaddata` reajusta as sequências dos models que ele carregou, então você não precisa fazer nada. **Mas** se em algum momento alguém inserir linhas com id explícito por fora dele (SQL na mão no painel do Supabase, `pgloader`), a sequência fica atrás dos dados e o próximo `INSERT` do Django dá `duplicate key value violates unique constraint "..._pkey"`. O conserto:
> ```bash
> ./.venv/Scripts/python.exe manage.py sqlsequencereset quiz catalogo accounts
> ```
> Ele **imprime** o SQL; rode o resultado no painel do Supabase.

### As quatro diferenças de comportamento que o MySQL escondia

Esta é a parte que nenhum tutorial de "Django + Supabase" menciona, e é onde o bug vai aparecer — dias depois, parecendo bug de outra coisa.

> [!danger] 1. Comparação de texto passa a ser **sensível a maiúsculas**
> A *collation* padrão do MySQL (`utf8mb4_0900_ai_ci`) ignora caixa e acento. O Postgres não ignora nada.
> ```python
> Area.objects.get(slug="Eletrica")   # MySQL: achava.  Postgres: DoesNotExist
> ```
> Todo `get()` e `filter()` por igualdade exata que hoje funciona "por sorte" passa a falhar. **Onde procurar:** os `seed_*`, que resolvem área por `slug`, e qualquer `filter(nome=...)`.
> Onde a intenção era mesmo ignorar caixa, o conserto é explicitar: `filter(slug__iexact=...)`. Não é gambiarra — é escrever o que se queria dizer.

> [!danger] 2. `unique` passa a permitir o que antes recusava
> No MySQL, um `unique` sobre `slug` recusava `eletrica` se já existisse `Eletrica`. No Postgres, as duas coexistem — e o catálogo ganha duas áreas "iguais" que o motor trata como distintas, dividindo o peso do perfil entre elas.
> **Sintoma:** ranking que muda sem ninguém ter mexido no motor. Depois do `migrate`, confira:
> ```bash
> ./.venv/Scripts/python.exe manage.py shell -c "from catalogo.models import Area; s=[a.slug for a in Area.objects.all()]; print(len(s), len({x.lower() for x in s}))"
> ```
> Os dois números têm de ser iguais. `12 11` significa duas áreas colidindo por caixa.

> [!warning] 3. Ordenação com acento muda
> `ORDER BY nome` ordena diferente nos dois bancos quando há acento — "Elétrica" e "Eletrônica" podem trocar de lugar. Isso importa aqui por um motivo específico: o **desempate do ranking é por nome**, e é isso que o teste `test_resultado_e_reprodutivel` de [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]] protege.
> A saída não é lutar contra a *collation*: é o desempate depender de algo estável. Um `order_by("-afinidade", "curso_id")` é reprodutível em qualquer banco. Fica registrado aqui e resolvido na **Fase 4**, que é quem reescreve esse teste.

> [!warning] 4. `SELECT DISTINCT` + `ORDER BY` em campo de fora agora é erro
> ```
> ProgrammingError: SELECT DISTINCT, ORDER BY expressions must appear in select list
> ```
> O MySQL aceitava; o Postgres exige. Aparece em `.distinct()` combinado com `order_by()` sobre campo de tabela relacionada. Guarde esta mensagem: a **Fase 3** vive de agregação, e é lá que ela tem mais chance de aparecer.

---

## 5️⃣ SB-05 — Postgres local para teste, e a higiene do repositório

### Um Postgres local, em um comando

Com Docker:

```bash
docker run -d --name pg-educmatch \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=educmatch_test \
  -p 5432:5432 postgres:15
```

Sem Docker: instale o **PostgreSQL 15** pelo instalador oficial, aceite a porta 5432 e crie o banco `educmatch_test` pelo pgAdmin.

Rodando a suíte contra ele:

```bash
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/educmatch_test \
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe manage.py test
```

> [!important] Por que não rodar o teste no Supabase, mesmo que "funcione" (D3)
> `manage.py test` **cria e apaga um banco** a cada execução. Contra um servidor compartilhado por quatro pessoas: dois testes ao mesmo tempo disputam o mesmo nome de banco, e um `migrate` de alguém derruba a suíte de outro no meio. Fora que cada execução consome do limite de conexões do plano gratuito.
> E por que não deixar o teste em SQLite, que é mais simples? Porque as quatro diferenças da SB-04 são exatamente o que precisa ser visto. Um teste em SQLite passaria feliz com o `get(slug="Eletrica")` que só quebra no Postgres.

> [!tip] Guarde o comando num arquivo, não na memória
> Duas linhas em `README.md`, ou um `testar.sh` de três linhas na raiz. Ninguém digita aquela linha inteira de cabeça toda vez, e o que não se digita não se roda.

### `requirements.txt`

O arquivo hoje se chama `requeriments.txt` e tem dois blocos repetidos.

```bash
git mv requeriments.txt requirements.txt
./.venv/Scripts/python.exe -m pip freeze > requirements.txt
```

> [!warning] `git mv`, não renomear no explorador
> Renomeando pelo Windows, o Git vê **um arquivo apagado e um criado** — e todo mundo que estiver com o arquivo antigo aberto numa branch ganha um conflito bobo. Com `git mv` ele registra a renomeação.

> [!note] `pip freeze` resolve os blocos repetidos de brinde
> Ele lista o que está **instalado na `.venv`**, uma linha por pacote, com versão fixada. Confira a saída: se aparecer algo que não tem nada a ver com o projeto, sua `.venv` tem lixo, e vale recriá-la a partir do arquivo novo.

### `README.md` — o parágrafo que economiza duas horas por pessoa

````markdown
## Rodando o projeto

1. `python -m venv .venv`
2. `./.venv/Scripts/python.exe -m pip install -r requirements.txt`
3. `cp .env.example .env` e preencha — a senha do banco vem por canal privado
4. `./.venv/Scripts/python.exe manage.py migrate`
5. `./.venv/Scripts/python.exe manage.py runserver`

O banco de desenvolvimento é **compartilhado** (Supabase). Você não precisa
instalar Postgres para rodar o site — só para rodar os testes:

```bash
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/educmatch_test \
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe manage.py test
```
````

> [!danger] "O banco de desenvolvimento é compartilhado" tem uma consequência que precisa estar escrita
> Não é mais o banco de cada um. Quem rodar `migrate` numa branch com migração nova **aplica no banco de todos**, e quem estiver na `main` passa a ver colunas que o código dele não conhece. Isso não dá erro imediato — dá erro estranho, depois.
> Regra do grupo, a partir desta fase: **`migrate` no Supabase só depois do merge na `main`.** Enquanto a migração está em revisão, quem a escreveu testa contra o Postgres local. É a mesma disciplina de "nunca dê push na `main`", aplicada ao banco.

---

## 6️⃣ SB-06 — a única janela barata para os dois nomes errados

**Opcional, e só com ratificação do grupo.** Pule esta seção inteira se não houver acordo — nada mais nesta nota depende dela.

A auditoria encontrou dois nomes que não são escolha de idioma, são erro:

| Onde | Hoje | Deveria | Custo |
|---|---|---|---|
| `quiz/engine.py` | `recomedacao()` | `recomendar()` | só `grep` — nenhuma migração |
| `accounts/models.py` | `envio_recurso` | `tentativa_origem` | uma `RenameField` |

```bash
grep -rn "recomedacao" --include="*.py" --include="*.html" .
grep -rn "envio_recurso" --include="*.py" --include="*.html" .
```

```bash
./.venv/Scripts/python.exe manage.py makemigrations accounts -n renomeia_tentativa_origem
```

> [!important] Por que aqui e não depois
> `envio_recurso` "não é tradução de `source_attempt`" — é o exemplo que [[contratos-c1-a-c6 🟢|📜 C1 a C6, seção 9]] usa para o achado central: **a verificabilidade de um contrato depende de ele compartilhar identificadores com o código que ele governa.** Enquanto o campo se chama `envio_recurso`, ninguém procurando por `source_attempt` o encontra, e a conferência do C4 exige ler o código inteiro traduzindo de cabeça.
> E é agora porque a Fase 2 vai abrir esse mesmo model para acrescentar três campos: uma passada de migração, não duas.

> [!danger] Isto toca contrato de outra frente — marque **sim** no PR
> `recomedacao()` é chamado pelas views e pelos templates de mais de uma frente. Renomear sem avisar quebra o trabalho de outra pessoa numa branch aberta. Duas aprovações, e um recado no grupo **antes** do merge.

### A entrega que fecha a D5: o glossário

Crie `docs/glossario.md` (ou a seção correspondente no README) com a tabela de [[contratos-c1-a-c6 🟢|📜 C1 a C6, seção 9]] — `Course`↔`Curso`, `QuizAttempt`↔`Tentativa_de_resposta`, e as outras nove.

> [!success] A tabela custa dez minutos e resolve o achado mais importante da auditoria
> Não é documentação decorativa. É o que torna possível responder *"o C4 foi cumprido?"* com um `grep` em vez de com uma leitura. E, a partir de agora, a regra do plano: **nome novo de campo, método ou rota entra no glossário no mesmo PR que o criou.** Foi a ausência dessa regra que produziu onze pares de nomes não registrados.

---

## 7️⃣ Os testes deste bloco

Uma fase de infraestrutura parece não ter o que testar. Tem — e são os três testes mais baratos da trilha inteira.

### `core/tests.py` — arquivo novo

```python
import os

from django.conf import settings
from django.db import connection
from django.test import SimpleTestCase


class ConfiguracaoTest(SimpleTestCase):
    def test_nenhum_segredo_esta_no_codigo(self):
        """SECRET_KEY tem que vir do ambiente, nao de um literal no settings."""
        self.assertEqual(settings.SECRET_KEY, os.environ["DJANGO_SECRET_KEY"])
        self.assertNotIn("django-insecure", settings.SECRET_KEY)

    def test_debug_vem_de_variavel_de_ambiente_como_texto(self):
        """A armadilha do bool('false'): toda string nao vazia e verdadeira."""
        for valor, esperado in (("true", True), ("false", False), ("", False)):
            with self.subTest(valor=valor):
                lido = valor.lower() == "true"
                self.assertIs(lido, esperado)

    def test_allowed_hosts_nao_esta_vazio(self):
        """ALLOWED_HOSTS vazio derruba a aplicacao no minuto em que DEBUG virar False."""
        self.assertTrue(settings.ALLOWED_HOSTS)

    def test_banco_e_postgres_e_o_fuso_esta_ligado(self):
        """Depois do PR-2, nenhum ambiente do projeto roda em outro banco."""
        self.assertEqual(connection.vendor, "postgresql")
        self.assertTrue(settings.USE_TZ)
```

> [!important] `test_nenhum_segredo_esta_no_codigo` é o guardião do `REV-06`
> Ele parece bobo hoje — obviamente a chave vem do ambiente, você acabou de escrever isso. O valor aparece em novembro, quando alguém estiver com pressa, o `.env` não carregar na máquina dele, e a "solução" de dez segundos for pôr a chave de volta no `settings.py` "só para hoje". O teste vermelho é a única coisa no repositório que diz não.

> [!note] `test_banco_e_postgres_e_o_fuso_esta_ligado` só entra no PR-2
> No PR-1 o banco ainda é MySQL e ele falharia, corretamente. Escreva-o no PR-2, junto com a troca do `DATABASE_URL`. É o teste que impede alguém voltar para SQLite "para o teste rodar mais rápido" e, com isso, deixar de ver as quatro diferenças da SB-04.

---

## 8️⃣ Verificação — é aqui que você descobre se deu certo

### Depois do PR-1 (ainda no MySQL)

```bash
./.venv/Scripts/python.exe manage.py check
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe manage.py test core
./.venv/Scripts/python.exe manage.py runserver 8010
```

E o teste que importa mais do que os três automatizados:

```bash
mv .env .env.guardado && ./.venv/Scripts/python.exe manage.py check ; mv .env.guardado .env
```

Tem de dar `KeyError: 'DJANGO_SECRET_KEY'`. Se subir normalmente, sobrou um valor padrão em algum lugar do `settings.py`.

### Depois do PR-2 (no Supabase)

```bash
./.venv/Scripts/python.exe manage.py migrate --plan          # vazio: nada pendente
./.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
./.venv/Scripts/python.exe manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('select version()'); print(c.fetchone())"
```

```bash
./.venv/Scripts/python.exe manage.py shell -c "from catalogo.models import Area, Curso; from quiz.models import Questao; print(Area.objects.count(), Curso.objects.count(), Questao.objects.count())"
```

Tem de imprimir `12 20 6`. Qualquer número menor significa seed que falhou no meio — e o `@transaction.atomic` reverteu tudo em silêncio, como já aconteceu com `marketing` e `design` ([[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Descoberta do seed]]).

E os sete cliques que nenhum teste automatizado faz por você:

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | Abrir `/` | Home carrega, quiz começa |
| 2 | Responder o quiz inteiro | Cai em `/resultado/<pk>/` com 5 cursos e explicação |
| 3 | Conferir os nomes com acento no resultado | "Elétrica", não "Elétrica" quebrado nem `???` |
| 4 | `/admin/` → **Usuários** | A lista abre e ordena |
| 5 | `/admin/` → **Cursos** | Os 20 aparecem, com os pesos no rodapé |
| 6 | `/admin/` → procurar **Login** e **Cadastro** | ❌ **não existem mais** (SB-03) |
| 7 | Painel do Supabase → **Table Editor** | As tabelas `quiz_*`, `catalogo_*`, `accounts_*` estão lá, com linhas |

> [!important] O clique 3 é o que os testes nunca pegam
> Encoding quebra na **borda** — no driver, no console, no template — não na lógica. A suíte inteira pode estar verde com "Mecânica" virando `MecÃ¢nica` na tela. E é a tela que a banca vai ver projetada na parede.

> [!warning] O clique 6 existe porque `DeleteModel` é a migração mais fácil de esquecer de aplicar
> Se as tabelas ainda aparecem no `/admin`, ou o `admin.py` ainda registra as classes apagadas (e aí o import quebraria), ou o `migrate` não rodou com a migração da SB-03 dentro. Confira com `manage.py showmigrations accounts`.

---

## 9️⃣ Commit, push, PR e o recado para o grupo

### PR-1

```bash
git add -A
git commit -m "feat(infra): carrega segredos do .env e aceita DATABASE_URL"
git push -u origin feat/infra-supabase
```

Abra o PR pelo link que o terminal imprime. No template:

```markdown
## O que muda
SECRET_KEY, DEBUG, ALLOWED_HOSTS e a URL do banco passam a vir do .env.
O banco continua o mesmo MySQL local. Fecha o REV-06.

## Por quê
A senha do banco e a SECRET_KEY estavam versionadas. E sem DATABASE_URL
em variavel de ambiente nao ha como apontar para o Supabase no PR-2.

## Como testar
cp .env.example .env  → preencher → manage.py check → manage.py test core
Renomear o .env e rodar manage.py check: tem que dar KeyError.

## Toca contrato de outra frente? (x) sim → todas: todo mundo precisa criar o .env
```

Recado pronto para colar no grupo, **antes do merge**:

> Subi a branch `feat/infra-supabase` (PR-1). Ela tira a senha do banco e a `SECRET_KEY` do `core/settings.py` e passa a ler de um arquivo `.env`.
>
> **Quando você atualizar, o projeto não sobe até você criar o `.env`:**
>
> ```
> cp .env.example .env
> ```
>
> Depois abra o `.env` e preencha três coisas: `DJANGO_SECRET_KEY` (gere com o comando que está no README), `DATABASE_URL` com a senha do **seu** MySQL local, e deixe o resto como está. São dois minutos, uma vez só.
>
> Se aparecer `KeyError: 'DJANGO_SECRET_KEY'`, é isso — faltou o `.env`. Ele **não** vem no repositório de propósito.
>
> ⚠️ O `.env` nunca entra em commit. Se aparecer em `git status`, me chame antes de commitar.

### PR-2

```bash
git checkout main && git pull
git branch -D feat/infra-supabase
git checkout -b feat/infra-supabase
# ... SB-02 a SB-06 ...
git add -A
git commit -m "feat(infra): migra o banco para o Postgres no Supabase"
git push -u origin feat/infra-supabase
```

Recado do PR-2, **antes do merge** — e este exige resposta de cada um:

> PR-2 da `feat/infra-supabase`: o banco do projeto agora é um **Postgres no Supabase**, compartilhado pelos quatro. Não vai mais existir "o meu banco".
>
> **O que você precisa fazer quando eu mesclar:**
>
> ```
> git checkout main && git pull
> ./.venv/Scripts/python.exe -m pip install -r requirements.txt
> ```
>
> Depois troque a linha `DATABASE_URL` do seu `.env` pela que eu te mandei **no privado** (não vou mandar aqui).
>
> **Não precisa rodar `migrate`.** O banco já está migrado e populado: 12 áreas, 20 cursos, 6 questões. Rodar `migrate` sem necessidade não quebra nada, mas a regra nova é importante:
>
> 🔴 **`migrate` no Supabase só depois do merge na `main`.** Se você está numa branch com migração nova, teste contra um Postgres local (comando no README). Se rodar no Supabase, você aplica a mudança no banco de todos, e quem está na `main` passa a ver colunas que o código dele não conhece.
>
> Seu MySQL local pode ser desligado. **Não apague ainda** — espere uma semana, até todos confirmarem que está tudo funcionando.
>
> ⚠️ **F3:** a partir de agora, curso cadastrado no `/admin` fica no banco de todos e sobrevive a `git pull`. Isso é bom — mas os 18 cursos reais continuam devendo entrar por `seed_cursos`, não pelo painel, porque o seed é o que o teste e a monografia citam como fonte.

> [!danger] O recado do PR-2 é o único momento em que a senha circula
> Individual, por canal privado, **uma pessoa por vez**. Nunca no mesmo lugar onde está o link do projeto — quem tiver os dois tem o banco. Ver o Risco 2 do [[Projetos/EducMatch(Secretária)/plano-execucao-v02-supabase-a-testes|plano]].

---

## ▶️ Próxima ação

**Fase 2 — REC-01 a REC-06, num PR único.** São cinco defeitos de recomendação e os três campos de *snapshot* do `C4`, todos com migração no mesmo par de models. Fazer numa passada evita três migrações mexendo nas mesmas tabelas — e o painel da Fase 3 depende dos seis.

Ver [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 Passo a passo REC-01 a REC-06]].

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/plano-execucao-v02-supabase-a-testes|🗺️ Plano v0.2]] — as decisões D1 a D5 que esta nota executa
- [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 Fase 2 — erros da recomendação]] — o bloco seguinte
- [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel e refino]] — origem do `REV-06` e do `REV-07`
- [[contratos-c1-a-c6 🟢|📜 Os contratos C1 a C6]] — a tabela de tradução da SB-06
- [[git-ritual-de-entrega-do-tcc|🧾 Ritual de entrega]] — o que fazer se o `.env` for commitado (pânico 3)
- [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições]] — o `cp1252` e o `DisallowedHost`
- [[der-escopo-banco 🟢|📐 Escopo do DER]] — atualizar depois da SB-03
- **Conceitos:** [[Banco de Dados|Banco de Dados]] · [[Migrations|Migrations]] · [[ORM|ORM]] · [[Git|Git]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]] · [[Projetos|🚀 Projetos]]
