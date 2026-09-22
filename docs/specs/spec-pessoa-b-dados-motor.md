---
title: "Spec — Pessoa B · Dados e motor (migrações, C4 e correções da recomendação)"
aliases: ["Spec pessoa B", "Spec dados e motor", "PR-2 dados", "PR-3 motor"]
tags: [tcc, backend, django, migration, motor, recomendacao, spec]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Visão geral: [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] · Código de referência: [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|🔧 BK-01 a BK-08]] §3, §4 e §7 · [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 REC]] §2, §4 e §5 · Contrato: [[contratos-c1-a-c6 🟢|📜 C4]] · Colegas: [[Projetos/EducMatch(Secretária)/spec-pessoa-a-infra|🧱 A]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-c-painel|📊 C]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-d-telas|🎨 D]]

# 🧮 Spec — Pessoa B · Dados e motor

> [!abstract] Sua missão em uma frase
> Fazer o banco **guardar os dados do jeito que o contrato C4 manda** (explicação como JSON e a "foto" do ranking no momento em que o aluno salva um curso) e corrigir as bordas do motor de recomendação, **sem mexer no cálculo do cosseno**, que está certo.

| PR | Branch | Quando | Libera |
|---|---|---|---|
| **PR-2** | `feat/dados-c4` | Rodadas 1 e 2 | As métricas de demanda e aderência do painel (**pessoa C**) |
| **PR-3** | `fix/motor-recomendacao` | Rodadas 3 e 4, numa branch **nova**, criada do `main` depois que o PR-2 entrar | — |

> [!important] Você é a única pessoa do grupo que cria migração
> Se duas pessoas gerarem `0003_...` no mesmo app ao mesmo tempo, o Django não sabe qual vem primeiro e o `migrate` de todo mundo quebra. Por isso **toda** mudança em `models.py` passa por você. Se alguém precisar de um campo ou índice novo, a pessoa pede para você.

---

## 1️⃣ Por que isso importa

- **`Login` e `Cadastro` guardam senha em texto puro.** Não são usados, mas estão no banco. Na banca, "tabela com senha em texto puro" derruba nota.
- **`Recomendacao.explicacao` é texto com um dicionário Python dentro** (`"{'top_areas': [...]}"`). Não dá para consultar, e o painel precisa saber a área de cada recomendação.
- **O `Interesse` não guarda a "foto" do momento**: em que posição o curso estava quando o aluno salvou, com que afinidade, e se era o 1º lugar. O contrato C4 exige isso, e tem um teste no repositório (`quiz/tests/test_contratos.py`) esperando esses campos.
- **`Interesse.criado_em` é `auto_now`**: a data muda **toda vez** que o registro é salvo. O painel conta "interesses criados no período" e hoje conta "interesses tocados no período".
- **O motor recomenda curso desativado.** O admin desativa um curso e ele continua aparecendo.
- **O motor faz dezenas de consultas ao banco** para cada quiz respondido.

---

## 2️⃣ O que é seu (e o que não é)

| ✅ Você pode mexer | ❌ Não mexa |
|---|---|
| **Toda migração** (`*/migrations/`) | `core/settings.py` → **A** |
| `accounts/models.py`, `quiz/models.py`, `catalogo/models.py` | `painel/` inteiro, inclusive `painel/metricas.py` → **C** |
| `accounts/admin.py`, `quiz/admin.py` | Templates, CSS e JS → **D** |
| `accounts/servicos.py` (novo) | **O cálculo do cosseno** (`afinidade`, `dot`, `norm`) |
| `quiz/engine.py` | |
| **Só duas funções** de `accounts/views.py` (`_salvar_interesse_pendente` e `salvar_interesse`) e **só uma** de `quiz/web_views.py` (`areas_da_recomendacao`) | O resto desses dois arquivos é da **D** |

> [!warning] Os dois arquivos que você divide com a pessoa D
> `accounts/views.py` e `quiz/web_views.py` são da D, mas o PR-2 precisa mudar três funções dentro deles. Avise a D **no primeiro dia**: "vou mexer em `_salvar_interesse_pendente`, `salvar_interesse` e `areas_da_recomendacao`; não mexa nessas três até o PR-2 entrar". Mudanças em funções diferentes do mesmo arquivo o Git junta sozinho.

---

## 3️⃣ Antes de começar

```bash
cd educmatch
git switch main
git pull
git switch -c feat/dados-c4
cd backend
source .venv/Scripts/activate
python manage.py migrate
python manage.py test 2>&1 | tail -5     # anote: é a sua linha de base
```

Confira o catálogo pelo **número**, não pela ausência de erro:

```bash
python manage.py shell -c "from catalogo.models import Area, Curso, Peso_curso; print(Area.objects.count(), Curso.objects.count(), Peso_curso.objects.count())"
```

Tem de dar `12 20 73`. Se não der: `python manage.py seed_areas && python manage.py seed_cursos && python manage.py seed_questoes`.

> [!tip] Faça um backup do banco antes das migrações
> ```bash
> mysqldump -u root -p educmatch > backup-antes-pr2.sql
> ```
> Não versione esse arquivo. Se uma migração der errado no meio, você volta com `mysql -u root -p educmatch < backup-antes-pr2.sql`.

---

## 4️⃣ PR-2 — passo a passo

> [!note] Nome das tarefas
> As specs antigas chamam isto de REC-01, REC-03 e REC-06; a spec BK chama de BK-04 e BK-05. **São a mesma coisa.** Siga a BK, que é mais nova e já foi testada numa cópia do projeto. Ignore tudo da BK que fala de API, serializer ou `/api/v1/`: a API REST foi removida.

### Passo 1 · apagar `Login` e `Cadastro`

- [ ] Em `accounts/models.py`, apague as classes `Login` e `Cadastro`
- [ ] Em `accounts/admin.py`, apague qualquer `admin.site.register` delas
- [ ] Gere a migração e confira que o arquivo só tem `DeleteModel`:
  ```bash
  python manage.py makemigrations accounts -n remove_login_cadastro
  ```

### Passo 2 · `explicacao` vira `JSONField` (BK-04)

Código completo em [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|BK]] §3.

- [ ] Em `quiz/models.py`, na `Recomendacao`: `explicacao = models.JSONField(default=dict, blank=True)`
- [ ] No `__str__` da `Recomendacao`, troque `self.curso.nome` por `self.curso.nome_curso` (o campo `nome` não existe; o admin quebra ao abrir)
- [ ] Crie a migração **vazia** e escreva ela à mão, colando o conteúdo da BK §3 (a função `repr_para_json` e as duas operações):
  ```bash
  python manage.py makemigrations quiz --empty -n explicacao_jsonfield
  ```
- [ ] Em `quiz/web_views.py`, na `areas_da_recomendacao`: troque o `ast.literal_eval` por `if not isinstance(explicacao, dict): return []` e apague o `import ast`

> [!danger] A ordem das duas operações é o que faz a migração funcionar
> Primeiro o `RunPython` (converte cada linha antiga em JSON válido, ainda como texto), **depois** o `AlterField` (muda o tipo da coluna). Na ordem inversa, o MySQL recusa na primeira linha antiga com `Invalid JSON text`.

### Passo 3 · o C4 completo em `Interesse` (BK-05)

Código completo em BK §4. O que muda na classe `Interesse`:

| Campo | Antes | Depois |
|---|---|---|
| FK para a tentativa | `envio_recurso` | **`tentativa_origem`** (o teste de contrato exige esse nome) |
| `rank_snapshot` | não existe | `PositiveSmallIntegerField(null=True, blank=True)` |
| `afinidade_snapshot` | não existe | `FloatField(null=True, blank=True)` |
| `era_principal` | não existe | `BooleanField(default=False)` |
| `criado_em` | `auto_now=True` | **`auto_now_add=True`** |

```bash
python manage.py makemigrations accounts -n interesse_c4
```

> [!warning] O `makemigrations` vai perguntar se `envio_recurso` foi renomeado para `tentativa_origem`
> Responda **`y`**. Se responder `n`, ele **apaga a coluna e cria outra**, e todo interesse que já existe perde a tentativa de origem. Depois de gerar, abra o arquivo e confira que aparece `RenameField`, e **não** `RemoveField` + `AddField`.

- [ ] Procure o nome antigo e troque: `grep -rn "envio_recurso" --include=*.py --include=*.html .`

### Passo 4 · um lugar só grava interesse (`accounts/servicos.py`, novo)

```python
from accounts.models import Interesse


def registrar_interesse(usuario, curso, tentativa=None):
    """Idempotente: devolve (interesse, criado). Se já existe, não mexe no snapshot."""
    rec = tentativa.recomendacoes.filter(curso=curso).first() if tentativa else None
    return Interesse.objects.get_or_create(
        usuario=usuario,
        curso=curso,
        defaults={
            "tentativa_origem": tentativa,
            "rank_snapshot": rec.rank if rec else None,
            "afinidade_snapshot": rec.score if rec else None,
            "era_principal": bool(rec and rec.rank == 1),
        },
    )
```

- [ ] Em `accounts/views.py`, troque os `Interesse.objects.get_or_create(...)` de `_salvar_interesse_pendente` e de `salvar_interesse` por chamadas a `registrar_interesse`. O trecho exato está na BK §4

### Passo 5 · admin

- [ ] No `InteresseAdmin`, mostre `tentativa_origem`, `rank_snapshot`, `afinidade_snapshot` e `era_principal`. Campo que o grupo não vê é campo que o grupo esquece que existe

## 5️⃣ PR-2 — pronto quando

```bash
python manage.py makemigrations --check --dry-run      # tem de dizer "No changes detected"
python manage.py migrate
python manage.py test quiz.tests.test_contratos -v 2   # os testes de C4 ficam verdes
python manage.py test 2>&1 | tail -5                   # nenhuma falha nova contra a linha de base
```

- [ ] A migração **volta**: `python manage.py migrate quiz 0001` e depois `python manage.py migrate quiz`, os dois sem erro
- [ ] `test_c4_interesse_tem_os_tres_campos_de_snapshot` e `test_c4_criado_em_nao_e_auto_now` verdes. Estavam vermelhos antes: são os seus "testes que falhariam antes"
- [ ] No navegador, logado: responder o quiz em `http://localhost:8000/`, salvar o 1º curso, abrir `/admin` → **Interesses** → os três campos de snapshot preenchidos e `era_principal` marcado
- [ ] A tela de resultado continua mostrando as áreas de cada curso (é o `areas_da_recomendacao` lendo o JSON novo)
- [ ] Contagem do catálogo continua `12 20 73`

### Como abrir o PR

```bash
git add -A
git status --short       # confira: nada de .env, backup .sql ou __pycache__
git commit -m "feat(dados): explicacao em JSON e C4 completo em Interesse"
git push -u origin feat/dados-c4
```

```markdown
## O que muda
- Remove Login e Cadastro (senha em texto puro)
- Recomendacao.explicacao: TextField -> JSONField, com migração que converte o formato antigo
- Interesse com o C4: tentativa_origem, rank/afinidade_snapshot, era_principal, criado_em auto_now_add
- accounts/servicos.py: registrar_interesse, um lugar só grava interesse

## Toca contrato de outra frente?
Sim: C4. O painel (pessoa C) passa a ler explicacao como JSON e os campos de snapshot.

## Como testar
1. git pull e python manage.py migrate
2. python manage.py test quiz.tests.test_contratos -v 2
3. Salvar um curso logado → /admin → Interesses → snapshot preenchido
```

> [!important] Depois do merge, avise o grupo com todas as letras
> "PR-2 entrou. **Todo mundo: `git pull` e `python manage.py migrate`**. Pessoa C, pode fazer demanda por área e aderência. Pessoa D, as três funções estão liberadas."

---

## 6️⃣ PR-3 — correções do motor e índices do painel

```bash
git switch main
git pull
git switch -c fix/motor-recomendacao
```

A função se chama `recomedacao`, com o erro de grafia. Não renomeie: outros arquivos importam esse nome.

### Passo 1 · meça antes de mudar

Esse número vai para a monografia:

```python
# python manage.py shell
from django.db import connection
from django.test.utils import CaptureQueriesContext
from quiz.engine import recomedacao
from quiz.models import Tentativa_de_resposta

t = Tentativa_de_resposta.objects.last()
with CaptureQueriesContext(connection) as ctx:
    recomedacao(t)
print(len(ctx))
```

- [ ] Anote o número ("antes")

### Passo 2 · REC-02 — curso desativado fora do cálculo

Hoje a função passa `Curso.objects.all()` para o ranking. Troque por `Curso.objects.filter(is_active=True)`.

> [!danger] O filtro tem de estar no motor, não na tela
> Se filtrar só na hora de mostrar, o curso desativado continua sendo calculado, gravado em `Recomendacao` e contado no painel. Ele só some da tela: o bug fica invisível, não resolvido.

- [ ] Escreva no PR quantos cursos estão desativados hoje: `python manage.py shell -c "from catalogo.models import Curso; print(Curso.objects.filter(is_active=False).count())"`

### Passo 3 · REC-05 — acabar com as consultas repetidas

```python
cursos = Curso.objects.filter(is_active=True).prefetch_related("curso_peso__area")
alternativas = [
    resposta.alternativa
    for resposta in tentativa.respostas.select_related("alternativa").prefetch_related("alternativa__pesos__area")
]
```

- [ ] Rode a medição do passo 1 de novo e anote o número ("depois")

### Passo 4 · REC-04 — confiança calculada antes do corte

> [!warning] O código real é diferente do que a spec REC descreve
> A spec REC diz que a confiança tira a **média** do top-5. No código atual, `confianca()` já compara o 1º com o 2º lugar, então cortar a lista em 5 não muda o resultado. E o "aviso de baixa confiança que nunca aparece" tinha outra causa: o template testa `confidence_level` em vez de `confidence_band`. **Quem conserta isso é a pessoa D**, no template.
> O que fica com você:
> - chamar `confianca(ranking)` com o ranking **inteiro** e só **depois** cortar com `[:limit]`;
> - pôr os limites `0.15` e `0.05` em constantes no topo (`BANDA_CONFIANCA_ALTA` e `BANDA_CONFIANCA_MEDIA`), para a calibração futura ser editar duas linhas;
> - **não** criar o valor `"indefinida"` da spec REC: o template e o painel só conhecem `alta`, `media` e `baixa`.

```python
ranking = rank_cursos(perfil, cursos, nome_areas)   # completo
tentativa.confidence_band = confianca(ranking)      # mede antes do corte
ranking = ranking[:limit]                           # só agora corta
```

### Passo 5 · os índices do painel (PNL-01)

O painel da pessoa C filtra por data e por posição. Sem índice, vira varredura da tabela inteira no dia em que a turma responder o quiz. Em `quiz/models.py`, no `Meta` de cada model:

```python
# Tentativa_de_resposta
indexes = [models.Index(fields=["criado_em"], name="idx_tentativa_criado_em")]

# Recomendacao (junto do unique_together e do ordering que já existem)
indexes = [models.Index(fields=["rank", "curso"], name="idx_rec_rank_curso")]
```

```bash
python manage.py makemigrations quiz -n indices_do_painel
```

### Passo 6 · testes

Em `quiz/tests/test_recomendacao.py`, ou num arquivo novo `quiz/tests/test_motor.py`:

- [ ] **Curso desativado não aparece:** desativar um curso que apareceria no top-5, responder, e afirmar que ele não está em `tentativa.recomendacoes`
- [ ] **Número de consultas:** `with self.assertNumQueries(N): recomedacao(tentativa)`, com o N "depois" que você mediu
- [ ] **Confiança:** chamar `confianca()` com um ranking montado à mão (1º e 2º quase empatados → `"baixa"`; 1º muito à frente → `"alta"`)
- [ ] **O cosseno continua certo:** `quiz/tests/test_engine_puro.py` verde

## 7️⃣ PR-3 — pronto quando

- [ ] Os testes novos passam, e **o de curso desativado falha** se você desfizer o `filter(is_active=True)`
- [ ] No `/admin`, desativar um curso e responder o quiz de novo → o curso não aparece
- [ ] O PR diz os dois números: "de X para Y consultas por quiz respondido, com 20 cursos e 6 respostas"
- [ ] `makemigrations --check --dry-run` limpo depois da migração dos índices

Texto do PR no mesmo formato do PR-2, com "Toca contrato de outra frente? Sim: `confidence_band`, que a tela de resultado e o painel mostram".

---

## 8️⃣ Armadilhas

> [!danger] Não gere migração "para ver o que acontece"
> Cada `makemigrations` cria um arquivo. Se gerou uma errada, **apague o arquivo antes do commit** e gere de novo. Nunca faça commit de duas migrações que se desfazem.

> [!warning] Se o `migrate` reclamar de migração conflitante
> Alguém criou migração no mesmo app. Pela regra do grupo, isso não deveria acontecer: pare e fale no grupo antes de resolver.

> [!note] O que **não** é seu nesta fase
> - Calibrar os pesos do catálogo (só depois de o painel mostrar a distribuição real)
> - As 6 áreas sem nenhuma questão (é conteúdo, fica para depois)
> - Mexer no cálculo do cosseno
