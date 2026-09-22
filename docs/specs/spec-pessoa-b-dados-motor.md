---
title: "Spec — Pessoa B · Dados e motor (PR-2 C4 e JSON · PR-3 motor e índices)"
aliases: ["Spec pessoa B", "Spec dados e motor", "PR-2 dados", "PR-3 motor", "Passo a passo de dados e motor"]
tags: [tcc, backend, django, migration, motor, recomendacao, spec, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Mapa: [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] · Origem: [[Projetos/EducMatch(Secretária)/passo-a-passo-bk-01-bk-08|🔧 BK-04 e BK-05]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 REC]] · Contrato: [[contratos-c1-a-c6 🟢|📜 C4]] · Colegas: [[Projetos/EducMatch(Secretária)/spec-pessoa-a-infra|🧱 A]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-c-painel|📊 C]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-d-telas|🎨 D]]

# 🧮 Spec — Pessoa B · Dados e motor

> [!abstract] O que esta nota é
> O **como** da frente de dados e motor, arquivo por arquivo. Missão em uma frase: fazer o banco **guardar os dados do jeito que o contrato C4 manda** (explicação em JSON e a "foto" do ranking quando o aluno salva um curso) e corrigir as bordas do motor, **sem tocar no cálculo do cosseno**, que está certo.
> Escrita contra o commit `a04c8e9`. Ignore tudo da spec BK que fala de API, serializer ou `/api/v1/`: a API REST foi removida.

> [!success] O que já foi verificado (2026-09-22)
> Todo o código desta nota foi aplicado numa **cópia** do repositório, no **MySQL 8 local**, num banco separado:
> - a migração do JSON converteu uma linha no formato antigo (`str(dict)`, com `None` e `True`) e uma linha vazia, e depois **voltou** (`migrate quiz 0001`) e **foi de novo** sem erro. Isso a BK não tinha conseguido verificar no MySQL;
> - o `makemigrations` perguntou do rename e gerou `RenameField` (não drop + add);
> - `makemigrations --check` limpo no fim;
> - o motor foi de **120 para 12 consultas** por quiz respondido (20 cursos, 6 respostas);
> - os testes novos desta nota passam, e o de curso desativado **fica vermelho** quando o filtro é desfeito.

## 🧭 O mapa

| Tarefa | O que faz | Arquivo | Migração? | PR |
|---|---|---|---|---|
| **B-1** | apagar `Login` e `Cadastro` (senha em texto puro) | `accounts/models.py` | ✅ | PR-2 |
| **B-2** | `explicacao` vira `JSONField` | `quiz/models.py` + `web_views.py` | ✅ à mão | PR-2 |
| **B-3** | o C4 completo em `Interesse` | `accounts/models.py` | ✅ | PR-2 |
| **B-4** | um lugar só grava interesse | `accounts/servicos.py` + `views.py` | ❌ | PR-2 |
| **B-5** | admin de usuário e interesse | `accounts/admin.py` | ❌ | PR-2 |
| **B-6** | curso desativado fora do motor | `quiz/engine.py` | ❌ | PR-3 |
| **B-7** | de 120 para 12 consultas | `quiz/engine.py` | ❌ | PR-3 |
| **B-8** | confiança medida antes do corte | `quiz/engine.py` | ❌ | PR-3 |
| **B-9** | índices do painel | `quiz/models.py` | ✅ | PR-3 |

> [!important] Você é a única pessoa do grupo que cria migração
> Se duas pessoas gerarem `0003_...` no mesmo app ao mesmo tempo, o `migrate` de todo mundo quebra. Toda mudança em `models.py` passa por você.

> [!warning] Três funções que moram em arquivos da pessoa D
> O PR-2 muda `_salvar_interesse_pendente` e `salvar_interesse` (em `accounts/views.py`) e `areas_da_recomendacao` (em `quiz/web_views.py`). Avise a D **no primeiro dia**: ela não mexe nessas três até o PR-2 entrar. Mudanças em funções diferentes do mesmo arquivo o Git junta sozinho.

---

## 🚦 Antes de abrir o editor

```bash
cd educmatch
git switch main && git pull
git switch -c feat/dados-c4
cd backend
source .venv/Scripts/activate
python manage.py migrate
python manage.py test 2>&1 | tail -5          # a sua linha de base
python manage.py shell -c "from catalogo.models import Area, Curso, Peso_curso; print(Area.objects.count(), Curso.objects.count(), Peso_curso.objects.count())"
```

O último tem de imprimir `12 20 73`. Se não imprimir: `python manage.py seed_areas && python manage.py seed_cursos && python manage.py seed_questoes`.

Faça backup do banco antes das migrações (não versione o arquivo):

```bash
mysqldump -u root -p educmatch > backup-antes-pr2.sql
```

---

## 1️⃣ B-1 — apagar `Login` e `Cadastro`

### `accounts/models.py`

Apague as duas classes inteiras, de `class Login(models.Model):` até o `__str__` de `Cadastro`. Nada no projeto as usa: nem views, nem admin, nem templates.

```bash
python manage.py makemigrations accounts -n remove_login_cadastro
```

A saída tem de ser só isto:

```
accounts\migrations\0003_remove_login_cadastro.py
    - Delete model Cadastro
    - Delete model Login
```

---

## 2️⃣ B-2 — `explicacao` vira `JSONField`

### Por que

A engine grava um dicionário, mas o campo é `TextField`, então o Django guarda `str(dict)`: `"{'top_areas': [...]}"`, com aspas simples, `None` e `True`. Isso não é JSON. Não dá para consultar, e o painel precisa ler a área de cada 1º lugar.

### `quiz/models.py` — na classe `Recomendacao`

```python
    explicacao = models.JSONField(default=dict, blank=True)
```

E, de passagem, os dois `__str__` que quebram o `/admin`:

```python
# Recomendacao.__str__: o campo é nome_curso, não nome
return f"Recomendação do curso {self.curso.nome_curso} para a tentativa {self.tentativa.id} - Score: {self.score}, Rank: {self.rank}"

# Tentativa_de_resposta.__str__: o username herdado é sempre vazio; o login é pelo e-mail
nome_usuario = self.user.email if self.user else "anônimo"
```

### A migração — escrita à mão

```bash
python manage.py makemigrations quiz --empty -n explicacao_jsonfield
```

Substitua o conteúdo de `quiz/migrations/0002_explicacao_jsonfield.py`:

```python
import ast
import json

from django.db import migrations, models


def texto_para_json(apps, schema_editor):
    """O TextField guardava str(dict): aspas simples, None, True.
    Isso não é JSON, e o MySQL recusa o ALTER para coluna JSON se uma
    linha só tiver valor inválido. Então converte ANTES de alterar."""
    Recomendacao = apps.get_model("quiz", "Recomendacao")
    for rec in Recomendacao.objects.all().only("id", "explicacao"):
        bruto = rec.explicacao
        if not bruto:
            valor = {}
        else:
            try:
                valor = ast.literal_eval(bruto)
            except (ValueError, SyntaxError):
                try:
                    valor = json.loads(bruto)
                except ValueError:
                    valor = {}
        rec.explicacao = json.dumps(valor, ensure_ascii=False)
        rec.save(update_fields=["explicacao"])


class Migration(migrations.Migration):
    dependencies = [("quiz", "0001_initial")]

    operations = [
        migrations.RunPython(texto_para_json, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="recomendacao",
            name="explicacao",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
```

> [!danger] A ordem das duas operações é o que faz a migração passar
> `AlterField` primeiro = `Invalid JSON text` no MySQL na primeira linha antiga. `RunPython` primeiro = cada linha vira JSON válido ainda dentro do `TextField`, e o `ALTER` só muda o tipo.

### `quiz/web_views.py` — o `ast` sai

Na função `areas_da_recomendacao`, troque o começo:

```python
# ANTES
    explicacao = recomendacao.explicacao
    if isinstance(explicacao, str):
        try:
            explicacao = ast.literal_eval(explicacao)
        except (ValueError, SyntaxError):
            return []
    if not isinstance(explicacao, dict):
```

```python
# DEPOIS
    explicacao = recomendacao.explicacao  # JSONField: já chega como dict
    if not isinstance(explicacao, dict):
```

E apague o `import ast` do topo do arquivo.

---

## 3️⃣ B-3 — o C4 completo em `Interesse`

### `accounts/models.py` — só estas linhas da classe `Interesse`

```python
# ANTES
    envio_recurso = models.ForeignKey("quiz.Tentativa_de_resposta", null=True, blank=True, on_delete=models.SET_NULL, related_name="interesses")
    status = models.CharField(max_length=20, choices=STATUS, default="interessado")
    nota = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now=True)
```

```python
# DEPOIS
    tentativa_origem = models.ForeignKey(
        "quiz.Tentativa_de_resposta",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="interesses",
    )
    # C4: a "foto" do momento em que o aluno salvou o curso. A tentativa pode
    # ser refeita e a recomendação regravada; o snapshot não muda.
    rank_snapshot = models.PositiveSmallIntegerField("posição no momento", null=True, blank=True)
    afinidade_snapshot = models.FloatField("afinidade no momento", null=True, blank=True)
    era_principal = models.BooleanField("era o 1º colocado", default=False)
    status = models.CharField(max_length=20, choices=STATUS, default="interessado")
    nota = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)  # era auto_now: mudava a cada save
```

O `Meta` e o `__str__` ficam iguais.

```bash
python manage.py makemigrations accounts -n interesse_c4
```

O Django vai perguntar:

```
Was interesse.envio_recurso renamed to interesse.tentativa_origem (a ForeignKey)? [y/N]
```

> [!danger] Responda `y`
> Com `n`, ele **apaga a coluna e cria outra**, e todo interesse que já existe perde a tentativa de origem. Depois de gerar, abra `accounts/migrations/0004_interesse_c4.py`: a primeira operação tem de ser `RenameField`, e **não** `RemoveField` + `AddField`.

A saída esperada:

```
    ~ Rename field envio_recurso on interesse to tentativa_origem
    + Add field afinidade_snapshot to interesse
    + Add field era_principal to interesse
    + Add field rank_snapshot to interesse
    ~ Alter field criado_em on interesse
```

---

## 4️⃣ B-4 — um lugar só grava interesse

### `accounts/servicos.py` (arquivo novo)

```python
from accounts.models import Interesse


def registrar_interesse(usuario, curso, tentativa=None):
    """Um lugar só grava interesse, para o snapshot do C4 sair sempre igual.

    Idempotente: devolve (interesse, criado). Se o interesse já existe,
    não mexe no snapshot: ele é a foto do momento em que foi salvo.
    """
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

### `accounts/views.py` — as duas chamadas passam a usar o serviço

No topo, junto dos imports:

```python
from accounts.servicos import registrar_interesse
```

Em `_salvar_interesse_pendente`:

```python
# ANTES
    Interesse.objects.get_or_create(
        usuario=request.user,
        curso=curso,
        defaults={"envio_recurso": tentativa},
    )
```

```python
# DEPOIS
    registrar_interesse(request.user, curso, tentativa)
```

Em `salvar_interesse` (o `rec` calculado ali nunca era usado: era o snapshot pela metade):

```python
# ANTES
    tentativa = None
    if tentativa_id:
        tentativa = Tentativa_de_resposta.objects.filter(pk=tentativa_id).first()
        if tentativa:
            rec = tentativa.recomendacoes.filter(curso=curso).first()

    item, criado = Interesse.objects.get_or_create(
        usuario=request.user,
        curso=curso,
        defaults= {
            "envio_recurso": tentativa,
        },
    )
```

```python
# DEPOIS
    tentativa = None
    if tentativa_id:
        tentativa = Tentativa_de_resposta.objects.filter(pk=tentativa_id).first()

    item, criado = registrar_interesse(request.user, curso, tentativa)
```

Confira que o nome antigo sumiu:

```bash
grep -rn "envio_recurso" --include=*.py --include=*.html . | grep -v migrations
```

---

## 5️⃣ B-5 — `accounts/admin.py`

Hoje o arquivo está vazio: **nem o usuário nem o interesse aparecem no `/admin`**. Substitua:

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import Interesse, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # O login é pelo e-mail: o username herdado fica vazio e sai das telas.
    ordering = ["email"]
    list_display = ["email", "first_name", "is_staff", "is_superuser", "date_joined"]
    search_fields = ["email", "first_name"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Dados pessoais", {"fields": ["first_name", "last_name"]}),
        ("Permissões", {"fields": ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
        ("Datas", {"fields": ["last_login", "date_joined"]}),
    ]
    add_fieldsets = [
        (None, {"classes": ["wide"], "fields": ["email", "first_name", "password1", "password2"]}),
    ]


@admin.register(Interesse)
class InteresseAdmin(admin.ModelAdmin):
    list_display = ["usuario", "curso", "status", "rank_snapshot", "era_principal", "criado_em"]
    list_filter = ["status", "era_principal"]
    search_fields = ["usuario__email", "curso__nome_curso"]
    # O snapshot é a foto do momento: ninguém edita pelo admin.
    readonly_fields = ["tentativa_origem", "rank_snapshot", "afinidade_snapshot", "era_principal", "criado_em"]
```

> [!note] Por que o admin do usuário importa para o painel
> A pessoa C precisa marcar a coordenação como **staff** para ela ver o painel. Sem o `UserAdmin`, isso só dá pelo `shell`.

---

## 6️⃣ Os testes do PR-2

### `accounts/tests/test_c4_interesse.py` (hoje o arquivo existe, mas está vazio)

```python
from django.urls import reverse

from accounts.models import Interesse
from accounts.servicos import registrar_interesse
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class C4SnapshotTest(BaseEducMatch):
    """C4: ao salvar um curso, o Interesse guarda a foto do ranking."""

    def setUp(self):
        super().setUp()
        self.usuario = self.criar_usuario()
        self.client.force_login(self.usuario)
        self.responder_tudo()
        self.tentativa = Tentativa_de_resposta.objects.latest("id")

    def salvar(self, rec):
        return self.client.post(
            reverse("interesse-salvar"),
            {"curso_id": rec.curso_id, "tentativa_id": self.tentativa.pk},
        )

    def test_salvar_o_primeiro_lugar_grava_o_snapshot(self):
        primeiro = self.tentativa.recomendacoes.get(rank=1)

        self.salvar(primeiro)

        item = Interesse.objects.get(usuario=self.usuario, curso=primeiro.curso)
        self.assertEqual(item.tentativa_origem, self.tentativa)
        self.assertEqual(item.rank_snapshot, 1)
        self.assertAlmostEqual(item.afinidade_snapshot, primeiro.score)
        self.assertTrue(item.era_principal)

    def test_salvar_o_terceiro_lugar_nao_e_principal(self):
        terceiro = self.tentativa.recomendacoes.get(rank=3)

        self.salvar(terceiro)

        item = Interesse.objects.get(usuario=self.usuario, curso=terceiro.curso)
        self.assertEqual(item.rank_snapshot, 3)
        self.assertFalse(item.era_principal)

    def test_registrar_de_novo_nao_reescreve_a_foto(self):
        """Idempotente: a segunda chamada devolve o mesmo interesse, intacto."""
        primeiro = self.tentativa.recomendacoes.get(rank=1)
        item, criado = registrar_interesse(self.usuario, primeiro.curso, self.tentativa)

        de_novo, criado_de_novo = registrar_interesse(self.usuario, primeiro.curso, None)

        self.assertTrue(criado)
        self.assertFalse(criado_de_novo)
        self.assertEqual(de_novo.pk, item.pk)
        self.assertEqual(de_novo.rank_snapshot, 1)

    def test_criado_em_nao_muda_quando_o_interesse_e_salvo_de_novo(self):
        """REV-01: com auto_now, a data mudava a cada save."""
        primeiro = self.tentativa.recomendacoes.get(rank=1)
        item, _ = registrar_interesse(self.usuario, primeiro.curso, self.tentativa)
        antes = item.criado_em

        item.status = "contatado"
        item.save()
        item.refresh_from_db()

        self.assertEqual(item.criado_em, antes)
```

> [!note] Estes testes precisam do PR-1
> O `responder_tudo` faz um POST na página do quiz, que só responde certo depois que o `ALLOWED_HOSTS` da pessoa A entrou. Se o PR-1 ainda não entrou, faça `git pull --rebase origin main` depois que ele entrar.

---

## 7️⃣ Verificação do PR-2

```bash
python manage.py makemigrations --check --dry-run      # "No changes detected"
python manage.py migrate
python manage.py migrate quiz 0001                     # a migração do JSON volta...
python manage.py migrate                               # ...e vai de novo
python manage.py test accounts.tests.test_c4_interesse quiz.tests.test_contratos -v 2
python manage.py test 2>&1 | tail -5                   # nenhuma falha nova
```

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | `test_c4_interesse_tem_os_tres_campos_de_snapshot` e `test_c4_criado_em_nao_e_auto_now` | Verdes. **Eram vermelhos antes**: são os seus "testes que falhariam antes" |
| 2 | Logado, responder o quiz e salvar o 1º curso | `/admin` → **Interesses**: posição 1, afinidade preenchida, "era o 1º colocado" marcado |
| 3 | Abrir um resultado **antigo** (de antes da migração) | As áreas de "Por que este curso" continuam aparecendo |
| 4 | `/admin` → **Usuários** | A lista abre, com e-mail e nome |
| 5 | Catálogo | Continua `12 20 73` |

### Commit e PR

```bash
git add -A
git status --short       # nada de .env, backup .sql ou __pycache__
git commit -m "feat(dados): explicacao em JSON e C4 completo em Interesse"
git push -u origin feat/dados-c4
```

```markdown
## O que muda
- Remove Login e Cadastro (senha em texto puro)
- Recomendacao.explicacao: TextField -> JSONField, com migração que converte o formato antigo
- Interesse com o C4: tentativa_origem, rank/afinidade_snapshot, era_principal, criado_em auto_now_add
- accounts/servicos.py: registrar_interesse, um lugar só grava interesse
- Admin de Usuário e de Interesse (o arquivo estava vazio)

## Toca contrato de outra frente?
Sim: C4. O painel (pessoa C) passa a ler explicacao como JSON e os campos de snapshot.

## Como testar
1. git pull e python manage.py migrate
2. python manage.py test accounts.tests.test_c4_interesse quiz.tests.test_contratos -v 2
3. Salvar um curso logado → /admin → Interesses → snapshot preenchido
```

> [!important] Depois do merge, avise o grupo com todas as letras
> "PR-2 entrou. **Todo mundo: `git pull` e `python manage.py migrate`**. Pessoa C, pode fazer o PR-5. Pessoa D, as três funções estão liberadas."

---

## 8️⃣ PR-3 — o motor

```bash
git switch main && git pull
git switch -c fix/motor-recomendacao
```

A função se chama `recomedacao`, com o erro de grafia. Não renomeie: outros arquivos importam esse nome.

### Meça antes de mudar

Salve como `medir.py` na pasta **acima** do repositório, a que contém a pasta `educmatch`. Assim o Git nunca vê o arquivo:

```
pasta-de-cima/        ← medir.py fica aqui
└── educmatch/        ← o repositório (tem o .git)
    └── backend/      ← daqui você roda o comando
```

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext
from quiz.engine import recomedacao
from quiz.models import Questao, Resposta, Tentativa_de_resposta

t = Tentativa_de_resposta.objects.create(respondido_por="medicao")
for q in Questao.objects.filter(is_active=True):
    Resposta.objects.create(tentativa=t, questao=q, alternativa=q.alternativas.first())
with CaptureQueriesContext(connection) as ctx:
    recomedacao(t)
print("CONSULTAS:", len(ctx))
t.delete()
```

```bash
python manage.py shell -c "exec(open('../../medir.py', encoding='utf-8').read())"
```

> [!warning] `../../`, e não `../`
> De dentro de `backend/`, `../` é a raiz do repositório: um `medir.py` salvo ali aparece no `git status` e acaba entrando num commit.

Medido em 2026-09-22: **`CONSULTAS: 120`**. É o número "antes" da monografia.

### `quiz/engine.py` — as constantes, no topo (B-8)

```python
TOP3 = 3
CORTE_MINIMO = 0.5
CORTE_MAXIMO = 0.8

# Quanto o 1º lugar precisa se separar do 2º (em proporção do 1º) para a
# confiança ser alta ou média. Valores de partida: calibrar com o painel.
BANDA_CONFIANCA_ALTA = 0.15
BANDA_CONFIANCA_MEDIA = 0.05
```

### `quiz/engine.py` — a função `confianca`

```python
def confianca(ranking):
    """Quanto o 1º lugar se separou do 2º, no ranking INTEIRO (antes do corte)."""
    if not ranking:
        return "baixa"

    primeiro = ranking[0][1]
    segundo = ranking[1][1] if len(ranking) > 1 else 0.0

    if primeiro <= 0:
        return "baixa"

    separacao = (primeiro - segundo) / primeiro
    if separacao >= BANDA_CONFIANCA_ALTA:
        return "alta"
    if separacao >= BANDA_CONFIANCA_MEDIA:
        return "media"
    return "baixa"
```

### `quiz/engine.py` — o miolo de `recomedacao` (B-6, B-7 e B-8)

```python
# ANTES
    alternativas = [resposta.alternativa for resposta in tentativa.respostas.select_related("alternativa")]
    perfil = perfil_vetor(alternativas)
    nome_areas = dict(Area.objects.values_list("slug", "nome"))
    ranking = rank_cursos(perfil, Curso.objects.all(), nome_areas)[:limit]

    primeiro = ranking[0][1] if ranking else 0.0
    segundo = ranking[1][1] if len(ranking) > 1 else 0.0

    tentativa.diferenca = primeiro - segundo
    tentativa.confidence_band = confianca(ranking)
    tentativa.save(update_fields=["confidence_band", "diferenca"])
```

```python
# DEPOIS
    respostas = (
        tentativa.respostas
        .select_related("alternativa")                 # FK: um JOIN
        .prefetch_related("alternativa__pesos__area")  # para-muitos: uma consulta a mais
    )
    perfil = perfil_vetor([resposta.alternativa for resposta in respostas])
    nome_areas = dict(Area.objects.values_list("slug", "nome"))

    # REC-02: curso desativado não entra no cálculo (e nem no painel).
    cursos = Curso.objects.filter(is_active=True).prefetch_related("curso_peso__area")
    ranking = rank_cursos(perfil, cursos, nome_areas)   # completo

    primeiro = ranking[0][1] if ranking else 0.0
    segundo = ranking[1][1] if len(ranking) > 1 else 0.0

    tentativa.diferenca = primeiro - segundo
    tentativa.confidence_band = confianca(ranking)     # REC-04: mede antes do corte
    tentativa.save(update_fields=["confidence_band", "diferenca"])

    ranking = ranking[:limit]                           # só agora corta
```

O resto da função (`delete` e `bulk_create`) fica igual.

Rode `medir.py` de novo: **`CONSULTAS: 12`**.

> [!danger] O filtro de curso ativo tem de estar no motor, não na tela
> Se filtrar só na hora de mostrar, o curso desativado continua sendo calculado, gravado em `Recomendacao` e contado no painel. O bug fica invisível, não resolvido.

> [!warning] A spec REC descreve um código que não existe mais
> Ela diz que a confiança tira a **média** do top-5. No código real, `confianca()` já compara o 1º com o 2º, então cortar a lista não mudava o resultado. E o "aviso de baixa confiança que nunca aparece" tinha outra causa: o template testava `confidence_level` em vez de `confidence_band`. **Quem conserta isso é a pessoa D.** Aqui, a mudança é deixar a ordem certa garantida por código e as bandas em constantes com nome.
> **Não** crie o valor `"indefinida"` que a spec REC propõe: o template e o painel só conhecem `alta`, `media` e `baixa`.

### `quiz/models.py` — os índices do painel (B-9)

No `Meta` da `Tentativa_de_resposta`:

```python
    class Meta:
        ordering = ["-criado_em"]
        # O painel filtra toda métrica por período
        indexes = [models.Index(fields=["criado_em"], name="idx_tentativa_criado_em")]
```

No `Meta` da `Recomendacao`:

```python
    class Meta:
        unique_together = ('tentativa', 'curso')
        ordering = ["rank"]
        # "Top cursos em 1º lugar" filtra por rank e agrupa por curso
        indexes = [models.Index(fields=["rank", "curso"], name="idx_rec_rank_curso")]
```

```bash
python manage.py makemigrations quiz -n indices_do_painel
```

### `quiz/tests/test_engine_puro.py` — o import quebrado

Hoje o arquivo inteiro dá `ImportError`, porque importa `cosseno`, e na engine a função se chama `afinidade`. Troque a linha do import:

```python
# O cosseno se chama `afinidade` na engine; o teste mantém o nome da matemática.
from quiz.engine import afinidade as cosseno
```

Isso devolve à suíte o `test_escala_nao_muda_o_score`, o teste que protege a **decisão** de usar cosseno.

### `quiz/tests/test_motor.py` (arquivo novo)

```python
from django.test import SimpleTestCase

from catalogo.models import Curso
from quiz.engine import confianca, recomedacao
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class MotorTest(BaseEducMatch):
    def responder(self):
        self.responder_tudo()
        return Tentativa_de_resposta.objects.latest("id")

    def test_curso_desativado_nao_e_recomendado(self):
        """REC-02: o filtro está no motor, não na tela."""
        primeiro = self.responder().recomendacoes.get(rank=1).curso
        Curso.objects.filter(pk=primeiro.pk).update(is_active=False)

        tentativa = self.responder()

        cursos = set(tentativa.recomendacoes.values_list("curso_id", flat=True))
        self.assertNotIn(primeiro.pk, cursos)
        self.assertEqual(len(cursos), 5)

    def test_numero_de_consultas_nao_cresce_com_o_catalogo(self):
        """REC-05: eram 120 consultas por quiz; com prefetch, 12."""
        tentativa = self.responder()
        with self.assertNumQueries(12):
            recomedacao(tentativa)


class ConfiancaTest(SimpleTestCase):
    """REC-04 com rankings montados à mão: (curso, afinidade, explicacao)."""

    def ranking(self, *afinidades):
        return [(None, valor, {}) for valor in afinidades]

    def test_primeiro_muito_a_frente_e_alta(self):
        self.assertEqual(confianca(self.ranking(0.9, 0.5, 0.4)), "alta")

    def test_quase_empate_e_baixa(self):
        self.assertEqual(confianca(self.ranking(0.80, 0.79, 0.5)), "baixa")

    def test_quiz_em_branco_e_baixa(self):
        self.assertEqual(confianca(self.ranking(0.0, 0.0)), "baixa")
```

---

## 9️⃣ Verificação do PR-3

```bash
python manage.py makemigrations --check --dry-run
python manage.py test quiz -v 2
```

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | `quiz.tests.test_motor` e `test_engine_puro` | Verdes |
| 2 | **Desfaça** o `filter(is_active=True)` e rode `test_motor` | `test_curso_desativado_nao_e_recomendado` fica **vermelho**. Refaça |
| 3 | `/admin` → desativar um curso → responder o quiz | O curso não aparece mais no resultado |
| 4 | `medir.py` | 120 antes, 12 depois. Os dois números vão no texto do PR |

> [!success] O parágrafo medido da monografia
> *"De 120 para 12 consultas ao banco por quiz respondido, com 20 cursos e 6 respostas, medido com `CaptureQueriesContext` e travado por `assertNumQueries`."* É uma afirmação verificável; "ficou mais rápido" não é.

Commit: `fix(motor): curso inativo fora do calculo, prefetch e confianca antes do corte`. No PR: "Toca contrato de outra frente? Sim: `confidence_band`, que a tela de resultado e o painel mostram".

---

## ▶️ Próxima ação

Criar a branch `feat/dados-c4`, avisar a pessoa D sobre as três funções, e fazer a §1.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]]
- [[engine-matching-cosseno 🟢|🧮 Engine de cosseno]] — o que **não** muda
- [[contratos-c1-a-c6 🟢|📜 C4]] — os três campos de snapshot
