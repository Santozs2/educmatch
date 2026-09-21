---
title: "Passo a passo — INF-01 a INF-05 (segredos fora do código, MySQL consolidado e seeds destravados)"
aliases: ["Passo a passo INF", "Fase 1 do plano v0.2", "Segredos no .env", "MySQL do TCC", "Tabelas de fuso do MySQL"]
tags: [tcc, infra, mysql, django, seguranca, execucao, passo-a-passo, seeds]
status: em-andamento
projeto: TCC
criado: 2026-09-17
---

> [!info] Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-v02|🗺️ Plano v0.2]] · Auditoria: [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 REV-06 a REV-08]] · Git: [[git-ritual-de-entrega-do-tcc|🧾 Ritual de entrega]] · Próxima fase: [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 REC-01 a REC-06]]

# 🧱 Passo a passo — INF-01 a INF-05

> [!abstract] O que esta nota é
> A Fase 1: tirar os segredos do código versionado, consolidar o MySQL como banco do projeto e destravar os seeds.
> **Esta nota é diferente das outras três.** As notas de REC, PNL e TST foram escritas contra as notas de auditoria e avisam que nada foi executado. Aqui, **INF-01, INF-02, INF-03 e INF-05 foram executados e verificados no repositório**, na branch `feat/infra-supabase` (commits `988e184`, `e1baa21`, `bc2cc3f`, `9ca574a`, `eead7f8`). Só a **INF-04** está aberta.

> [!important] O banco é MySQL. Uma tentativa de migrar para o Supabase foi revertida
> A evidência está na [[Projetos/EducMatch(Secretária)/plano-execucao-v02|seção 3 do plano]]: a rede onde o grupo trabalha bloqueia a saída na porta 5432 — medido contra um Postgres público sem relação com o Supabase, mesmo sintoma. Não reabrir sem ler aquela seção.
> O que ficou de bom: o banco agora é configurado por `DATABASE_URL`, então **trocar de banco é trocar o valor de uma variável de ambiente**. Esse ganho é independente de qual banco é.

## 🧭 Estado das tarefas

| Tarefa | O que faz | Estado |
|---|---|---|
| **INF-01** | segredos, `DEBUG` e `ALLOWED_HOSTS` para o `.env` (`REV-06`) | ✅ feito |
| **INF-02** | remover os models mortos com senha em texto puro (`REV-07`) | ✅ feito |
| **INF-03** | destravar o `seed_cursos` e completar o catálogo | ✅ feito |
| **INF-04** | carregar as tabelas de fuso do MySQL | 🟡 **aberto** |
| **INF-05** | `requirements.txt`, `.env.example` e README | ✅ feito |

---

## 1️⃣ INF-01 — segredos fora do código ✅

Este é o `REV-06`: senha do MySQL e `SECRET_KEY` em claro em `core/settings.py`, `DEBUG=True` fixo, `ALLOWED_HOSTS` vazio.

### As dependências

```bash
./.venv/Scripts/python.exe -m pip install python-dotenv dj-database-url mysqlclient
```

> [!tip] `mysqlclient` pode pendurar por dez minutos — force a *wheel*
> Sem restrição, o `pip` tenta compilar a partir do *sdist* e precisa de toolchain de C e dos headers do MySQL, que esta máquina não tem. Ele não falha: **fica parado, sem imprimir nada.**
> ```bash
> ./.venv/Scripts/python.exe -m pip install --only-binary :all: mysqlclient
> ```
> Assim ele baixa `mysqlclient-2.3.0-cp312-cp312-win_amd64.whl` (217 KB) e instala em segundos — ou falha na hora dizendo que não há *wheel*, o que também é informação.

### `core/settings.py` — o topo do arquivo

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

E no lugar do bloco `DATABASES`:

```python
DATABASES = {
    "default": dj_database_url.parse(
        os.environ["DATABASE_URL"],
        conn_max_age=0,
    )
}
```

> [!danger] O defeito que estava no primeiro commit desta fase, e que vale como lição
> O commit `988e184` trazia isto:
> ```python
> SECRET_KEY = os.environ['django-insecure-*z=y+!0ola&w4mrc!3xrfzm_0j*d!qc4+%!z-^2hew^u6iuk_6']
> ```
> Não é a chave sendo lida — é o **valor antigo usado como nome da variável de ambiente**. O projeto nunca subiria, e o erro (`KeyError` com a chave inteira dentro) parece um problema de `.env`.
> É o tipo de troca que acontece ao substituir um literal por uma leitura de ambiente com pressa. O `test_secret_key_vem_do_ambiente` da seção 6 existe por causa dele.

> [!danger] `os.environ["..."]` com colchete, não `.get()` com padrão
> `os.environ.get("DJANGO_SECRET_KEY", "django-insecure-...")` parece mais gentil e é a armadilha: o projeto sobe com a chave de exemplo, ninguém percebe, e ela vira a chave de verdade. Com colchete, quem esquecer o `.env` recebe `KeyError` no primeiro comando.
> É a mesma lógica do `.get()` em vez de `filter().first()` já registrada em [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]]: **prefira a função que falha alto à que escolhe em silêncio.**

> [!warning] `DEBUG` lido como texto, comparado com `"true"`
> `bool(os.environ.get("DJANGO_DEBUG"))` é `True` para a string `"false"` — toda string não vazia é verdadeira em Python. O sintoma é o pior possível: **produção rodando com `DEBUG=True`**, exibindo *traceback* com trechos de código para qualquer visitante.

### O `.env` e o `.env.example`

```bash
DJANGO_SECRET_KEY=<gere uma nova>
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver
DATABASE_URL=mysql://tecmysql:sua-senha@localhost:3306/educmatch
```

```bash
./.venv/Scripts/python.exe -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

> [!danger] Gere uma chave **nova**, e considere a antiga queimada
> A `SECRET_KEY` e a senha do MySQL que estavam no `settings.py` estão no histórico do Git desde o primeiro commit. `git show <commit>:core/settings.py` ainda as devolve. Tirar do arquivo **não** tira do histórico: as duas precisam ser **trocadas no servidor**, não só movidas. É o Risco 1 do [[Projetos/EducMatch(Secretária)/plano-execucao-v02|plano]].

> [!warning] Senha com `@ # / :` quebra a URL
> A senha entra numa `DATABASE_URL`. Um `@` no meio dela e a leitura da URL parte no lugar errado — e o erro fala de **host**, não de senha (`could not translate host name`). Ou use senha sem símbolos, ou *percent-encode* (`@` → `%40`).

O `.env.example` é o **contrato de ambiente**: versionado, sem valores, e toda variável nova entra nele no mesmo PR que a introduziu.

> [!note] Variável que nenhum código lê não entra no `.env.example`
> A primeira versão tinha um `DATABASE_URL_TEST` que **nada lia** — o `settings.py` só conhece `DATABASE_URL`. Foi removido. Variável de exemplo que não existe no código engana mais do que ajuda, e é a mesma família do `MAILERS` do `REV-08`.

---

## 2️⃣ INF-02 — não carregue lixo para frente ✅

`REV-07`: as classes `Login` e `Cadastro` em `accounts/models.py` eram resquício de antes do `AbstractUser`. Nenhuma view usava. O problema era o que tinham dentro:

```python
class Login(models.Model):
    nome = models.CharField(max_length=100)
    senha = models.CharField(max_length=100)   # senha em texto puro
```

Três razões para remover, em ordem de gravidade: campo de senha legível no esquema; as duas tabelas aparecem no [[der-escopo-banco 🟢|📐 DER]], que é documento de entrega; e são tabelas mantidas para código que já morreu.

```bash
grep -rn "\bLogin\b\|\bCadastro\b" --include="*.py" . | grep -v migrations
./.venv/Scripts/python.exe manage.py makemigrations accounts -n remove_models_mortos
```

> [!warning] Confira o arquivo gerado antes de aplicar
> Tem de conter **só** `DeleteModel` para `Cadastro` e `Login`. Confirmado com `sqlmigrate`:
> ```sql
> DROP TABLE "accounts_cadastro";
> DROP TABLE "accounts_login";
> ```
> Se aparecer `AlterField` ou `RemoveField` de outro campo, algo mais mudou no `models.py` desde a última migração — pare. Migração com duas intenções dentro é migração que ninguém consegue reverter.

> [!tip] O `grep` antes do `makemigrations` não é cerimônia
> Se algum `admin.py`, `forms.py` ou `views.py` ainda importasse essas classes, o `DeleteModel` passaria e o **import quebraria depois**, na máquina de outra pessoa. Aqui o `grep` voltou vazio, o que é o que autorizou a remoção.

---

## 3️⃣ INF-03 — os dois bugs que mantinham o catálogo pela metade ✅

Este não estava no plano. Apareceu ao rodar os seeds do zero, e é o achado mais instrutivo da fase.

### O sintoma

O banco tinha **7 áreas e 12 cursos**. A [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|auditoria de 11/09]] relata **12 áreas, 20 cursos e 73 pesos**. Ninguém tinha notado a diferença porque o `seed_cursos` "rodava".

### O que de fato acontecia

```
$ manage.py seed_cursos
  File ".../seed_cursos.py", line 166, in handle
    f"Curso '{data['nome_curso']}' usa áreas inexistentes: {sorted(desconhecidas)}"
              ~~~~^^^^^^^^^^^^^^
KeyError: 'nome_curso'
```

Dois defeitos, **um escondendo o outro**:

1. **`seed_areas` não tinha `marketing` nem `design`**, que o `seed_cursos` referencia nos pesos. A validação do `seed_cursos` detectava isso corretamente.
2. **A mensagem de erro estava errada.** A chave do dicionário é `nome`, não `nome_curso`. Então o `CommandError` legível — *"Curso X usa áreas inexistentes: ['design', 'marketing']"* — virava um `KeyError`, e o `@transaction.atomic` revertia **os 20 cursos**.

Resultado: banco com o catálogo antigo, e uma mensagem de erro que fala de uma chave de dicionário em vez do problema real.

### O conserto

```python
# catalogo/management/commands/seed_areas.py
    ("marketing", "Marketing", "Comunicação, mídias digitais e comportamento do consumidor."),
    ("design", "Design", "Design gráfico, projeto visual e experiência do usuário."),
```

```python
# catalogo/management/commands/seed_cursos.py:166
                # A chave do dicionario e `nome`. Escrito `nome_curso`, esta
                # linha trocava o CommandError legivel por um KeyError -- e o
                # @transaction.atomic revertia os 20 cursos sem dizer por que.
                raise CommandError(
                    f"Curso '{data['nome']}' usa áreas inexistentes: {sorted(desconhecidas)}"
                )
```

```bash
./.venv/Scripts/python.exe manage.py seed_areas    # 12 areas
./.venv/Scripts/python.exe manage.py seed_cursos   # Total: 20 cursos no catálogo.
./.venv/Scripts/python.exe manage.py seed_questoes # Total: 6 perguntas no quiz.
```

**12 áreas · 20 cursos · 73 pesos · 24 alternativas.** Os números da auditoria, pela primeira vez neste banco.

> [!danger] A lição, e ela vale para as três fases seguintes
> **Código dentro de uma mensagem de erro não é testado por ninguém.** A validação estava certa, o `raise` estava no lugar certo, e a linha que *explica* o problema é que quebrava — transformando um erro de dado num erro de programação e mandando quem depura para o lugar errado.
> É prima da lição do `validate` × `validar` já registrada em [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições, Passo 5]]: **o caminho de erro é código, e código não exercitado apodrece.**

> [!important] E a lição de verificação, que virou regra na definição de pronto
> Durante semanas, "o seed não deu erro" foi lido como "o seed funcionou". Com `@transaction.atomic`, uma falha no meio **reverte tudo e o comando termina** — e o banco fica num estado antigo perfeitamente coerente.
> **Sinal de sucesso é contagem, não ausência de traceback.** Por isso a [[Projetos/EducMatch(Secretária)/plano-execucao-v02|definição de pronto]] exige conferir `12 / 20 / 73`.

---

## 4️⃣ INF-04 — as tabelas de fuso do MySQL 🟡 **aberto**

O único item pendente da fase, e o único que bloqueia a Fase 3.

### O problema

O projeto roda com `USE_TZ = True` e `TIME_ZONE = "America/Sao_Paulo"` (**D4** do plano). Com fuso não-UTC, o Django traduz fuso **dentro do SQL**, chamando `CONVERT_TZ()`. Um MySQL recém-instalado vem com as tabelas de fuso **vazias**, e `CONVERT_TZ` então devolve `NULL`.

Medido neste banco:

```sql
SELECT CONVERT_TZ(NOW(), 'UTC', 'America/Sao_Paulo');   -- NULL
SELECT COUNT(*) FROM mysql.time_zone_name;              -- 0
```

> [!danger] Por que isto é uma mina embaixo do painel, e não um detalhe
> Com `CONVERT_TZ` devolvendo `NULL`, **todo** filtro e agrupamento que o Django traduz por ele passa a devolver vazio: `__date`, `__year`, `__month`, `__hour`, `TruncDate`, `TruncMonth`. **Sem erro nenhum.**
> O painel da Fase 3 filtra por período e agrupa por data. Um gráfico vazio por causa disso é exatamente o tipo de defeito que consome uma tarde e termina em "deve ser problema do Django".
> Nota: `criado_em__gte=<datetime>` **não** passa por `CONVERT_TZ` e funciona mesmo assim — o que é pior, porque metade das consultas funciona e a outra metade volta vazia.

### O conserto — uma vez, como root do MySQL

No Windows não existe o `mysql_tzinfo_to_sql`; usa-se o pacote pronto:

1. Baixe o pacote POSIX em `dev.mysql.com/downloads/timezones.html`
2. Importe:

```bash
mysql -u root -p mysql < timezone_posix.sql
```

3. Confirme:

```sql
SELECT CONVERT_TZ(NOW(), 'UTC', 'America/Sao_Paulo');   -- tem que devolver data
```

> [!note] A alternativa, e por que não é a recomendada
> Deixar `TIME_ZONE = "UTC"` faz o Django não chamar `CONVERT_TZ`, e o problema desaparece. O custo é que toda data exibida fica três horas adiantada — e "18:40" na tela quando eram 15:40 é erro de leitura esperando acontecer, inclusive na defesa. A **D4** escolheu pagar o carregamento das tabelas uma vez.

### O guarda

Já está no repositório, vermelho, esperando:

```python
def test_mysql_conhece_o_fuso_de_sao_paulo(self):
    with connection.cursor() as cursor:
        cursor.execute("select CONVERT_TZ(NOW(), 'UTC', %s)", [settings.TIME_ZONE])
        convertido = cursor.fetchone()[0]

    self.assertIsNotNone(convertido, "as tabelas de fuso do MySQL estao vazias")
```

> [!important] Um teste vermelho de propósito é melhor do que uma nota
> Enquanto as tabelas não forem carregadas, `manage.py test core` fecha em **8 verdes e 1 vermelho**, com a instrução no texto da falha. Quem clonar o projeto descobre no primeiro `test`, não no dia em que um gráfico voltar vazio.

---

## 5️⃣ INF-05 — dependências, contrato de ambiente e README ✅

```bash
git mv requeriments.txt requirements.txt
./.venv/Scripts/python.exe -m pip freeze > requirements.txt
```

O arquivo tinha **três blocos repetidos** e declarava `Django==5.2.17` enquanto a `.venv` tem **4.2.30**. Depois do `freeze`:

```
asgiref==3.12.1
dj-database-url==3.1.2
Django==4.2.30
djangorestframework==3.18.0
mysqlclient==2.3.0
python-dotenv==1.2.3
sqlparse==0.6.0
tzdata==2026.3
```

> [!warning] `git mv`, não renomear pelo explorador
> Renomeando pelo Windows, o Git vê **um arquivo apagado e um criado**, e quem estiver com o arquivo antigo aberto numa branch ganha um conflito bobo. Com `git mv` ele registra a renomeação.

> [!note] `psycopg2-binary` saiu junto
> Entrou na tentativa do Supabase e não tem função com MySQL. Dependência sem uso é dependência que alguém vai tentar explicar na banca.

O `.gitignore` foi desduplicado e cobre `dados-*.json` e `backup-*.json`.

> [!danger] Dump de `dumpdata` não entra em commit
> Carrega e-mail, nome e hash de senha de quem criou conta, além do `respondido_por` — texto livre digitado por aluno. Guarde **fora da pasta do projeto**.

O README passou a ter: setup, o SQL de criação do banco em `utf8mb4`, o `GRANT` que o `manage.py test` exige, o procedimento das tabelas de fuso e o fluxo de Git.

> [!tip] O `GRANT` do banco de teste é o que ninguém lembra
> `manage.py test` cria e apaga um banco `test_educmatch`. Sem privilégio sobre ele, a suíte não roda:
> ```sql
> GRANT ALL PRIVILEGES ON `test\_educmatch`.* TO 'tecmysql'@'localhost';
> ```
> Neste banco o `tecmysql` já tinha o privilégio — a suíte criou e destruiu o banco de teste sem ajuste. Vale conferir na máquina de cada um.

---

## 6️⃣ Os testes desta fase

`core/tests.py`, **9 testes**. Uma fase de infraestrutura parece não ter o que testar; estes são os mais baratos da trilha.

| Classe | Teste | O que protege |
|---|---|---|
| `SegredosTest` | `test_secret_key_vem_do_ambiente` | o `REV-06` — a chave não volta para o código |
| | `test_secret_key_nao_e_a_chave_de_exemplo_do_django` | a chave queimada do histórico não reaparece |
| | `test_debug_lido_como_texto_e_nao_como_bool` | a armadilha do `bool("false")` |
| | `test_allowed_hosts_nao_esta_vazio` | o defeito invisível enquanto `DEBUG=True` |
| `LimpezaDoEsquemaTest` | `test_models_login_e_cadastro_nao_existem_mais` | o `REV-07` |
| `BancoTest` | `test_fuso_horario_esta_ligado` | a **D4** |
| | `test_banco_e_mysql` | ninguém troca de banco sem decisão |
| `CharsetTest` | `test_conexao_e_utf8mb4` | acento em nome de curso |
| | `test_mysql_conhece_o_fuso_de_sao_paulo` | a **INF-04** 🟡 |

> [!important] `test_secret_key_vem_do_ambiente` é o guardião do `REV-06`
> Parece bobo — obviamente a chave vem do ambiente. O valor aparece em novembro, quando alguém com pressa tiver o `.env` não carregando e a "solução" de dez segundos for pôr a chave de volta no `settings.py` "só para hoje". O teste vermelho é a única coisa no repositório que diz não.

> [!note] `CharsetTest` é `TestCase`, as outras são `SimpleTestCase` — de propósito
> `SimpleTestCase` **proíbe** consulta ao banco, e a proibição é a feature: ela impede que alguém torne um teste barato em caro sem perceber. Os dois testes que precisam consultar o MySQL ficam numa classe separada, que paga o custo de criar o banco de teste.
> É a mesma separação de [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]]: `MatematicaTest` sem banco, `RecomendacaoTest` com banco.

---

## 7️⃣ Verificação

```bash
./.venv/Scripts/python.exe manage.py check
./.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe manage.py test core
```

Resultado atual: `check` limpo, **No changes detected**, e **8 verdes + 1 vermelho** (a INF-04).

A contagem do catálogo — e isto é verificação, não conferência visual:

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe manage.py shell -c "from catalogo.models import Area, Curso, Peso_curso; from quiz.models import Questao, Alternativa; print(Area.objects.count(), Curso.objects.count(), Peso_curso.objects.count(), Questao.objects.count(), Alternativa.objects.count())"
```

Tem de imprimir `12 20 73 6 24`.

E o teste que nenhum comando faz por você:

```bash
mv .env .env.guardado && ./.venv/Scripts/python.exe manage.py check ; mv .env.guardado .env
```

Tem de dar `KeyError: 'DJANGO_SECRET_KEY'`. Se subir normalmente, sobrou um valor padrão em algum lugar do `settings.py`.

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | `runserver` e responder o quiz inteiro | 5 cursos com explicação |
| 2 | Conferir os nomes com acento no resultado | "Elétrica", não `Elétrica` quebrado nem `???` |
| 3 | `/admin` → **Cursos** | os 20 aparecem, com os pesos no rodapé |
| 4 | `/admin` → procurar **Login** e **Cadastro** | ❌ não existem mais |
| 5 | `/admin` → **Áreas** | as 12, incluindo Marketing e Design |

> [!important] O clique 2 é o que os testes nunca pegam
> Encoding quebra na **borda** — no driver, no console, no template — não na lógica. A suíte inteira pode estar verde com "Mecânica" virando `MecÃ¢nica` na tela. E é a tela que a banca vê projetada na parede.

---

## 8️⃣ Commit, PR e o recado para o grupo

Os commits desta fase, na branch `feat/infra-supabase`:

```
988e184  feat(infra): carrega segredos do .env e aceita DATABASE_URL
e1baa21  feat(infra): conclui a Fase 1 sem o passo da conexao real do Supabase
bc2cc3f  docs(infra): .env.example vira contrato de ambiente documentado
9ca574a  docs(infra): enxuga o .env.example para a lista de variaveis
eead7f8  fix(catalogo): destrava o seed_cursos e completa o catalogo em 12/20/73
```

> [!warning] O nome da branch ficou errado
> `feat/infra-supabase` já está no `origin` e **não migra nada para o Supabase**. Nenhum PR foi aberto ainda, então renomear é barato:
> ```bash
> git branch -m feat/infra-supabase feat/infra-segredos
> git push -u origin feat/infra-segredos
> git push origin --delete feat/infra-supabase
> ```

Recado para o grupo, **antes do merge**:

> Subi a branch da infraestrutura. Ela tira a senha do banco e a `SECRET_KEY` do `core/settings.py` e passa a ler de um arquivo `.env`.
>
> **Quando você atualizar, o projeto não sobe até você criar o `.env`:**
>
> ```
> git checkout main && git pull
> ./.venv/Scripts/python.exe -m pip install -r requirements.txt
> cp .env.example .env
> ```
>
> Abra o `.env` e preencha duas coisas: `DJANGO_SECRET_KEY` (o comando está dentro do arquivo) e `DATABASE_URL` com a senha do **seu** MySQL local — o formato é `mysql://usuario:senha@localhost:3306/educmatch`.
>
> Se aparecer `KeyError: 'DJANGO_SECRET_KEY'`, é isso: faltou o `.env`. Ele não vem no repositório de propósito.
>
> O `requirements.txt` mudou de nome (estava `requeriments`), então rode o `pip install` de novo.
>
> 📌 **Rode os seeds de novo, todos:** o `seed_cursos` estava quebrado e o catálogo de vocês provavelmente está com **12 cursos em vez de 20**. Depois de rodar, tem que imprimir `Total: 20 cursos no catálogo`. Se imprimir menos, me chame.
>
> ⚠️ Um teste fica **vermelho** de propósito (`test_mysql_conhece_o_fuso_de_sao_paulo`) até carregarmos as tabelas de fuso do MySQL. Está explicado no README; é uma tarefa de root, uma vez só.

---

## ▶️ Próxima ação

**INF-04**, que é o que falta aqui, e depois a **Fase 2 — REC-01 a REC-06** num PR único: cinco defeitos de recomendação e os três campos de *snapshot* do `C4`, todos com migração no mesmo par de models.

Ver [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 Passo a passo REC-01 a REC-06]].

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/plano-execucao-v02|🗺️ Plano v0.2]] — as decisões D1 a D5 e o registro da tentativa do Supabase
- [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 Fase 2 — erros da recomendação]]
- [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel e refino]] — origem do `REV-06`, `REV-07` e `REV-08`
- [[Projetos/EducMatch(Secretária)/catalogo-areas-e-cursos|📚 Catálogo]] — o que os seeds constroem
- [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições]] — os dois bugs de seed entraram lá
- [[git-ritual-de-entrega-do-tcc|🧾 Ritual de entrega]] — o que fazer se o `.env` for commitado (pânico 3)
- [[der-escopo-banco 🟢|📐 Escopo do DER]] — atualizar depois da INF-02
- **Conceitos:** [[Banco de Dados|Banco de Dados]] · [[Migrations|Migrations]] · [[ORM|ORM]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]] · [[Projetos|🚀 Projetos]]
