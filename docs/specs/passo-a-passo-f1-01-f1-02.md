---
title: "Passo a passo — F1-01 e F1-02 (limite configurável e campos da camada de IA)"
aliases: ["Passo a passo F1", "Como fazer F1-01 e F1-02", "Migration da camada de IA"]
tags: [tcc, engine, django, migration, execucao, passo-a-passo]
status: em-andamento
projeto: TCC
criado: 2026-08-24
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-motor-e-ia-frentes-1-2|🧭 Spec das Frentes 1 e 2]] · Motor: [[engine-matching-cosseno 🟢|🧮 Engine]] · Modelagem: [[Projetos/EducMatch(Secretária)/modelagem-dados-quiz|🗃️ Modelagem]] · Testes: [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes]]

# 🔧 Passo a passo — F1-01 e F1-02

> [!abstract] O que esta nota é
> O **como** das duas primeiras tarefas da [[Projetos/EducMatch(Secretária)/spec-motor-e-ia-frentes-1-2|spec]], para executar com o editor aberto. Arquivo por arquivo, com o código no lugar certo e os comandos que provam que funcionou.
> Escrito contra o repositório no commit `a628753`. Se você já mexeu no `models.py`, confira os números de linha antes de colar.

> [!warning] Nada disto foi executado
> O código abaixo foi escrito contra a leitura do repositório, não rodado. **Os três comandos da seção de verificação são o que prova que deu certo** — não pule nenhum.

---

## 🚦 Antes de abrir o editor

```bash
git checkout -b feat/motor
```

E avise o grupo: **`Recommendation.rank` vira `rank_engine`**. Isso quebra `serializers.py`, `web_views.py` e `admin.py` — território da F4. Um PR só, sem fatiar.

Backup do banco — ele está no `.gitignore`, então não volta pelo git:

```bash
cp db.sqlite3 db.sqlite3.bak
```

---

## 1️⃣ F1-01 — tirar o `5` de dentro do código

### `config/settings.py` — no fim do arquivo

```python
# Quantos cursos a engine entrega. A camada de IA recebe exatamente esta lista
# (decisao do grupo: top-5 -> 1 principal + 4 alternativas).
RECOMMENDATION_LIMIT = 5
```

### `quiz/engine.py`

No topo, junto dos outros imports:

```python
from django.conf import settings
```

E a assinatura de `recommend` (linha 68):

```python
@transaction.atomic
def recommend(attempt, limit=None):
    if limit is None:
        limit = settings.RECOMMENDATION_LIMIT
    answers = attempt.answers.select_related("choice").prefetch_related(
```

> [!success] Não precisa mexer nas views
> `views.py` e `web_views.py` já chamam `recommend(attempt)` sem argumento, então passam a obedecer o settings sozinhas. Se você editar as views aqui, está aumentando o diff sem necessidade.

---

## 2️⃣ F1-02 — os campos da camada de IA

### `quiz/models.py` — `QuizAttempt`

Depois de `respondent_name`, antes do `class Meta`:

```python
    # Confianca do ranking: calculada pela engine, nao tem nada a ver com a IA.
    confidence_gap = models.FloatField(
        null=True, blank=True, help_text="Diferenca de score entre o 1o e o 2o colocado."
    )
    confidence_band = models.CharField(
        max_length=20, blank=True, help_text="alta | media | baixa (calibra o tom do texto)"
    )
    tie_set = models.JSONField(
        default=list, blank=True, help_text="course_id dos candidatos dentro de epsilon do topo."
    )

    # Metadados da chamada a LLM: sao da tentativa, nao de cada curso.
    llm_model = models.CharField(max_length=60, blank=True)
    prompt_version = models.CharField(max_length=20, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    tokens_in = models.PositiveIntegerField(null=True, blank=True)
    tokens_out = models.PositiveIntegerField(null=True, blank=True)
    used_fallback = models.BooleanField(default=False)
    diverged = models.BooleanField(default=False)
    cache_hit = models.BooleanField(default=False)
```

> [!note] `confidence_gap`, `confidence_band` e `tie_set` entram agora e ficam vazios
> Quem preenche é a F1-04 (conjunto de empate e banda). Entram aqui só para não fazer duas migrations no mesmo modelo com dois dias de diferença — e agora F1-04 vem **antes** de F1-03, porque o contrato C1 carrega esses campos.

### `quiz/models.py` — `Recommendation`

Troque o miolo da classe (linhas 77 a 83):

```python
    score = models.FloatField()
    rank_engine = models.PositiveSmallIntegerField(
        help_text="Ordem deterministica calculada pela engine."
    )
    rank_final = models.PositiveSmallIntegerField(
        help_text="Ordem efetivamente entregue ao usuario (a LLM pode reordenar)."
    )
    explanation = models.JSONField(default=dict, blank=True)
    llm_text = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ("attempt", "course")
        # Ordena pelo que foi entregue, nao pelo que a engine calculou: se a LLM
        # reordenar, a tela tem que mostrar a ordem que a pessoa viu.
        ordering = ["rank_final"]
```

### `quiz/migrations/0002_camada_ia.py` — escrita à mão

> [!warning] Não use `makemigrations` para esta
> Ele pergunta de forma interativa se `rank` virou `rank_engine`, e não sabe copiar o valor antigo para o `rank_final`. Crie o arquivo na mão.

```python
from django.db import migrations, models


def preenche_rank_final(apps, schema_editor):
    Recommendation = apps.get_model("quiz", "Recommendation")
    # order_by() limpo: o ordering historico ainda aponta para o campo antigo.
    for rec in Recommendation.objects.order_by().iterator():
        Recommendation.objects.filter(pk=rec.pk).update(
            rank_final=rec.rank_engine,
            is_primary=rec.rank_engine == 1,
        )


class Migration(migrations.Migration):

    dependencies = [("quiz", "0001_initial")]

    operations = [
        # Solta o ordering antes do rename, senao o state fica apontando para
        # um campo que nao existe mais.
        migrations.AlterModelOptions(name="recommendation", options={}),
        migrations.RenameField("recommendation", "rank", "rank_engine"),
        migrations.AlterField(
            model_name="recommendation",
            name="rank_engine",
            field=models.PositiveSmallIntegerField(
                help_text="Ordem deterministica calculada pela engine."
            ),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="rank_final",
            field=models.PositiveSmallIntegerField(
                null=True,
                help_text="Ordem efetivamente entregue ao usuario (a LLM pode reordenar).",
            ),
        ),
        migrations.AddField(
            model_name="recommendation",
            name="llm_text",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="recommendation",
            name="is_primary",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="confidence_gap",
            field=models.FloatField(
                blank=True,
                null=True,
                help_text="Diferenca de score entre o 1o e o 2o colocado.",
            ),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="confidence_band",
            field=models.CharField(
                blank=True,
                default="",
                max_length=20,
                help_text="alta | media | baixa (calibra o tom do texto)",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="tie_set",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="course_id dos candidatos dentro de epsilon do topo.",
            ),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="llm_model",
            field=models.CharField(blank=True, default="", max_length=60),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="prompt_version",
            field=models.CharField(blank=True, default="", max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="latency_ms",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="tokens_in",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="tokens_out",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="used_fallback",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="diverged",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="cache_hit",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(preenche_rank_final, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="recommendation",
            name="rank_final",
            field=models.PositiveSmallIntegerField(
                help_text="Ordem efetivamente entregue ao usuario (a LLM pode reordenar)."
            ),
        ),
        migrations.AlterModelOptions(
            name="recommendation", options={"ordering": ["rank_final"]}
        ),
    ]
```

> [!tip] O que `preserve_default=False` faz
> O `default=""` existe só para preencher as linhas que já estão no banco. Sem isso, o default entraria no modelo para sempre e o `models.py` deixaria de bater com a migration. Nos `CharField`/`TextField` ele é obrigatório; nos `BooleanField(default=False)` não, porque ali o default é de verdade.

### `quiz/engine.py` — gravar os três campos

No `bulk_create` (linhas 76 a 86), troque o `rank=posicao`:

```python
            Recommendation(
                attempt=attempt,
                course=course,
                score=round(score, 4),
                rank_engine=posicao,
                rank_final=posicao,
                is_primary=posicao == 1,
                explanation=explicacao,
            )
```

> [!success] É isso que mantém o sistema funcionando sem a camada de IA
> Com a IA desligada, `rank_final == rank_engine` e o 1º colocado já nasce como principal. A tela de entrega (Passo 10) funciona antes de existir uma linha de LLM.

### `quiz/serializers.py`

Acrescente o campo declarado, junto dos outros da classe:

```python
    course_id = serializers.IntegerField(source="course.id", read_only=True)
```

E troque a lista de `fields` (linha 24):

```python
        fields = [
            "course_id",
            "rank_engine",
            "rank_final",
            "is_primary",
            "score",
            "explanation",
            "llm_text",
            "course_name",
            "course_description",
            "duration_hours",
            "main_area",
        ]
```

> [!warning] Isto é mudança de contrato da API
> O campo `rank` some da resposta de `/api/quiz/submit/` e de `/api/quiz/attempts/<pk>/`. O `course_id` entra porque a F2 e a F4 vão precisar dele (contratos C1 e C3 da [[Projetos/EducMatch(Secretária)/spec-motor-e-ia-frentes-1-2|spec]]). Anuncie junto com a renomeação — é o mesmo aviso, não dois.

### `quiz/web_views.py` — linha 67

```python
            "rank": rec.rank_final,
```

> [!note] A chave do dicionário continua `rank`
> Por isso **`templates/quiz/result.html` não muda**. Menos churn no arquivo da F4, e o template continua funcionando exatamente igual.

### `quiz/admin.py` — linha 42

```python
    readonly_fields = ['course', 'score', 'rank_engine', 'rank_final', 'is_primary', 'explanation', 'llm_text']
```

### `quiz/management/commands/test_engine.py` — linha 40

```python
                    self.stdout.write(f"  {rec.rank_final}. {rec.course.name} "
```

---

## 3️⃣ Os dois testes novos

Em `quiz/tests.py`, no import do topo:

```python
from django.test import SimpleTestCase, TestCase, override_settings
```

E dentro de `RecomendacaoTest`:

```python
    @override_settings(RECOMMENDATION_LIMIT=3)
    def test_limite_vem_do_settings(self):
        """O 5 nao pode estar escrito na engine: top-5 ou top-3 e decisao de grupo."""
        attempt = QuizAttempt.objects.create(respondent_name="teste")
        choice = Choice.objects.get(text__icontains="Eletricidade")
        Answer.objects.create(attempt=attempt, question=choice.question, choice=choice)
        self.assertEqual(len(recommend(attempt)), 3)

    def test_rank_final_nasce_igual_ao_rank_engine(self):
        """Sem camada de IA, a ordem entregue e a ordem calculada."""
        attempt = QuizAttempt.objects.create(respondent_name="teste")
        choice = Choice.objects.get(text__icontains="Tecidos")
        Answer.objects.create(attempt=attempt, question=choice.question, choice=choice)
        recomendacoes = recommend(attempt)
        self.assertTrue(all(r.rank_final == r.rank_engine for r in recomendacoes))
        self.assertEqual(
            [r.is_primary for r in recomendacoes], [True, False, False, False, False]
        )
```

---

## 4️⃣ Verificação — é aqui que você descobre se deu certo

```bash
./.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

Tem que dizer que **não há mudanças pendentes**. Se ele quiser criar uma `0003`, o `models.py` e a migration escrita à mão discordam em algum campo — leia o que ele quer criar, é exatamente o campo divergente.

```bash
./.venv/Scripts/python.exe manage.py migrate
```

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe manage.py test
```

**14 testes verdes** — os 12 de antes mais os 2 novos.

> [!important] O teste que os automatizados não pegam
> Abrir uma tentativa **antiga**, de antes da migration, no site:
> ```bash
> ./.venv/Scripts/python.exe manage.py runserver
> ```
> Vá em `/resultado/<pk>/` de alguma tentativa que já existia. Se o `RunPython` funcionou, ela aparece na ordem certa. Se aparecer bagunçada, o `rank_final` ficou nulo naquelas linhas — e nenhum teste automatizado ia te contar isso, porque eles criam o banco do zero.

---

## 5️⃣ Commit

```bash
git add -A && git commit -m "feat(motor): limite configuravel e campos da camada de IA no modelo"
```

Se preferir dois commits, corte entre o F1-01 (settings + engine) e o F1-02 (models + migration + consumidores). Mas a migration e os arquivos que consomem `rank` **têm que ficar no mesmo commit** — senão o repositório fica quebrado no meio do histórico, e quem der `checkout` naquele ponto não consegue rodar nada.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-motor-e-ia-frentes-1-2|🧭 Spec das Frentes 1 e 2]] — o que vem depois destas duas tarefas
- [[engine-matching-cosseno 🟢|🧮 Engine de matching]] · [[Projetos/EducMatch(Secretária)/modelagem-dados-quiz|🗃️ Modelagem de dados]] · [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]]
- [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Plano da camada de IA]] · [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições]]
- **Conceitos:** [[Migrations|Migrations]] · [[tst-testes-django|Testes em Django]] · [[ORM|ORM]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]] · [[Projetos|🚀 Projetos]]
