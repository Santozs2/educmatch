---
title: "Spec pré-IA 01 — rank_engine, rank_final e metadados da LLM"
aliases: ["PRE-01", "F1-02 no código atual", "Migração rank_final"]
tags: [tcc, spec, migration, django, ia, engine]
status: proposto
projeto: TCC
branch: feature/rank-engine-final
criado: 2026-09-30
---

> [!info] Plano: [[plano-pre-ia-git-flow|🚧 Pré-IA e Git Flow]] · Anterior: [[spec-pre-ia-00-limpeza|00 — limpeza]] · Próxima: [[spec-pre-ia-02-empate|02 — empate]] · Origem: [[passo-a-passo-f1-01-f1-02|F1-02]]

# 🔀 PRE-01: `rank_engine`, `rank_final` e metadados da LLM

**Branch:** `feature/rank-engine-final`, saindo da `develop` **com a 00 já mesclada**
**Risco:** médio. É a única branch com migração que **renomeia** coluna.
**Testes ao final:** 78 (74 + 4 novos)

> [!abstract] O que esta branch faz
> É a F1-02 do passo a passo antigo, reescrita para o código de hoje. Aquele texto foi escrito contra os nomes em inglês (`Recommendation`, `QuizAttempt`) e o SQLite, e **não se aplica mais**. O que muda:
> 1. `Recomendacao.rank` vira duas colunas: `rank_engine` (o que a engine calculou) e `rank_final` (o que o aluno viu).
> 2. `Tentativa_de_resposta` ganha os 8 campos de metadados da chamada à LLM.
> 3. Todo lugar que tratava `rank == 1` como "o principal" passa a usar `rank_final`.
> 4. O snapshot C4 passa a guardar também a posição da engine.

---

## 🧭 A decisão que esta branch registra

> [!important] "Principal" é o que o aluno **viu**
> Quando a LLM reordenar, o curso em destaque na tela é o `rank_final == 1`. Por isso:
> - `is_primary`, o snapshot C4 (`rank_snapshot`, `era_principal`) e o painel usam **`rank_final`**;
> - `rank_engine` continua gravado para o **Passo 11** comparar.
>
> Com a IA desligada, `rank_final == rank_engine` e nada muda para ninguém.

| Lugar | Hoje | Depois | Por quê |
|---|---|---|---|
| `Recomendacao.is_primary` | `rank == 1` | `rank_final == 1` | É o destaque da tela |
| Snapshot C4 `rank_snapshot` | `rec.rank` | `rec.rank_final` | O aluno salvou o que **viu** |
| Snapshot C4 `rank_engine_snapshot` | — | `rec.rank_engine` | **Novo.** Para medir engine × LLM |
| Painel "top 1º lugar" e "demanda por área" | `rank=1` | `rank_final=1` | O painel mostra o que foi entregue |

> [!tip] Por que `rank_engine_snapshot` agora
> Sem ele, o Passo 11 teria de reconstruir a posição da engine a partir da `Recomendacao`, e ela é apagada e regravada se a tentativa for recalculada. Com ele, a pergunta *"quando a LLM trocou o 1º lugar, o aluno salvou o curso que ela promoveu?"* sai de uma consulta só na tabela de interesse. É uma coluna a mais agora contra uma reconstrução frágil depois.

---

## 1️⃣ `quiz/models.py`

### `Tentativa_de_resposta`: logo depois de `tie_set`

```python
    tie_set = models.JSONField(default=list, blank=True)

    # Metadados da entrega pela LLM: são da chamada, não de cada curso.
    # llm_model vazio = a camada de IA não rodou nesta tentativa.
    llm_model = models.CharField(max_length=60, blank=True)
    prompt_version = models.CharField(max_length=20, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    tokens_in = models.PositiveIntegerField(null=True, blank=True)
    tokens_out = models.PositiveIntegerField(null=True, blank=True)
    used_fallback = models.BooleanField(default=False)
    diverged = models.BooleanField(default=False)
    cache_hit = models.BooleanField(default=False)
```

> [!note] Como separar "IA desligada" de "IA falhou"
> `used_fallback=False` aparece nos dois casos. A diferença está em `llm_model`: vazio quer dizer que a IA nem rodou, preenchido com `used_fallback=True` quer dizer que ela falhou. A taxa de fallback do Passo 11 conta **só** as tentativas com `llm_model` preenchido.

### `Recomendacao`: troque `rank`, o `Meta` e o `is_primary`

Substitua desde `rank = models.IntegerField(default=0)` até o fim do `is_primary`:

```python
    rank_engine = models.PositiveSmallIntegerField(
        default=0, help_text="Ordem determinística calculada pela engine."
    )
    rank_final = models.PositiveSmallIntegerField(
        default=0, help_text="Ordem entregue ao aluno (a LLM pode reordenar)."
    )
    explicacao = models.JSONField(default=dict, blank=True)
    llm_text = models.TextField(blank=True)

    class Meta:
        unique_together = ('tentativa', 'curso')
        # A tela mostra a ordem que o aluno viu, não a que a engine calculou.
        ordering = ["rank_final"]
        indexes = [models.Index(fields=["rank_final", "curso"], name="idx_rec_rank_final_curso")]

    @property
    def is_primary(self):
        return self.rank_final == 1
```

E no `__str__`, troque `Rank: {self.rank}` por `Rank: {self.rank_final}`.

> [!note] `is_primary` continua `@property`, e não um campo
> O plano da IA previa um `BooleanField`. Como propriedade, ele **não tem como discordar** do `rank_final`. Com um campo, bastaria um `save` esquecido para existirem dois principais na mesma tentativa.

---

## 2️⃣ `quiz/migrations/0004_rank_engine_rank_final_e_metadados_llm.py`: escrita à mão

> [!warning] Não use `makemigrations` para o app `quiz`
> Ele não sabe que `rank` virou `rank_engine`: gera um *remove* e um *add*, e **perde a ordem de todas as recomendações já gravadas**. Crie o arquivo à mão, com o conteúdo abaixo.

```python
from django.db import migrations, models


def copia_rank_engine_para_rank_final(apps, schema_editor):
    # Antes da LLM, a ordem entregue ERA a da engine.
    Recomendacao = apps.get_model("quiz", "Recomendacao")
    Recomendacao.objects.update(rank_final=models.F("rank_engine"))


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0003_recomendacao_idx_rec_rank_curso_and_more"),
    ]

    operations = [
        # O índice antigo aponta para "rank": sai antes do rename.
        migrations.RemoveIndex(model_name="recomendacao", name="idx_rec_rank_curso"),
        migrations.RenameField(model_name="recomendacao", old_name="rank", new_name="rank_engine"),
        migrations.AlterField(
            model_name="recomendacao",
            name="rank_engine",
            field=models.PositiveSmallIntegerField(
                default=0, help_text="Ordem determinística calculada pela engine."
            ),
        ),
        migrations.AddField(
            model_name="recomendacao",
            name="rank_final",
            field=models.PositiveSmallIntegerField(
                default=0, help_text="Ordem entregue ao aluno (a LLM pode reordenar)."
            ),
        ),
        migrations.RunPython(copia_rank_engine_para_rank_final, migrations.RunPython.noop),
        migrations.AddField(
            model_name="recomendacao",
            name="llm_text",
            field=models.TextField(blank=True),
        ),
        migrations.AlterModelOptions(
            name="recomendacao",
            options={"ordering": ["rank_final"]},
        ),
        migrations.AddIndex(
            model_name="recomendacao",
            index=models.Index(fields=["rank_final", "curso"], name="idx_rec_rank_final_curso"),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="llm_model",
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="prompt_version",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="latency_ms",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="tokens_in",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="tokens_out",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="used_fallback",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="diverged",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="tentativa_de_resposta",
            name="cache_hit",
            field=models.BooleanField(default=False),
        ),
    ]
```

> [!success] Testada com dados reais, nos dois sentidos
> Num banco temporário com 3 recomendações gravadas no esquema antigo, a ida deixou `(rank_engine, rank_final)` = `(1,1)`, `(2,2)`, `(3,3)`. O `migrate quiz 0003` (a volta) devolveu `rank` = 1, 2, 3. O `noop` na volta é seguro: quando se desfaz, `rank_final` é descartado e `rank_engine` volta a se chamar `rank`.

---

## 3️⃣ `quiz/engine.py`: o `bulk_create`

Em `recomendar()`, troque `rank=rank,` por:

```python
                rank_engine=rank,
                rank_final=rank,  # sem LLM, a ordem entregue é a da engine
```

## 4️⃣ `quiz/web_views.py`: `resultado_pagina`

```python
            "rank": rec.rank_final,
```

A chave do dicionário continua `"rank"`, então o template não muda. `destaque = itens[0]` já sai certo, porque o `ordering` agora é `rank_final`.

## 5️⃣ `quiz/admin.py`: `RecomendacaoInline`

```python
    readonly_fields = ['curso', 'score', 'rank_engine', 'rank_final', 'explicacao', 'llm_text']
```

## 6️⃣ `painel/metricas.py`

Nas duas ocorrências, em `top_cursos_em_primeiro` (linha 79) e `demanda_por_area` (linha 151):

```python
        .filter(rank_final=1)
```

---

## 7️⃣ O snapshot C4: `accounts/`

### `accounts/models.py`, no `Interesse`, logo depois de `rank_snapshot`

```python
    # A posição que a ENGINE tinha dado. Igual a rank_snapshot enquanto a LLM
    # não reordena; quando difere, é o dado do experimento engine x LLM.
    rank_engine_snapshot = models.PositiveSmallIntegerField("posição na engine", null=True, blank=True)
```

### `accounts/servicos.py`, os `defaults` de `registrar_interesse`

```python
        defaults={
            "tentativa_origem": tentativa,
            "rank_snapshot": rec.rank_final if rec else None,
            "rank_engine_snapshot": rec.rank_engine if rec else None,
            "afinidade_snapshot": rec.score if rec else None,
            "era_principal": bool(rec and rec.rank_final == 1),
        },
```

### `accounts/admin.py`, no `readonly_fields`

Acrescente `"rank_engine_snapshot"` logo depois de `"rank_snapshot"`. O snapshot é a foto do momento e ninguém edita pelo admin.

### Migração do `accounts`: esta pode ser gerada

```bash
python manage.py makemigrations accounts -n rank_engine_snapshot
```

Gera `accounts/migrations/0005_rank_engine_snapshot.py` com um `AddField` só. Aqui não há rename, então o `makemigrations` acerta.

> [!note] Interesses antigos ficam com `rank_engine_snapshot = NULL`
> Está certo assim: na época, ninguém mediu. O Passo 11 filtra `rank_engine_snapshot__isnull=False`.

---

## 8️⃣ Testes

### Os que já existem: troca mecânica

| Arquivo | Troca |
|---|---|
| `accounts/tests/test_c4_interesse.py` (6×) | `recomendacoes.get(rank=N)` → `recomendacoes.get(rank_final=N)` |
| `quiz/tests/test_motor.py` (1×) | idem |
| `quiz/tests/test_telas.py` (3×) | idem |
| `painel/tests/test_privacidade.py` (1×) | idem |
| `painel/tests/base.py` linha 46 | `rank=2` → `rank_engine=2, rank_final=2` |
| `painel/tests/base.py` linha 55 | `rank=1` → `rank_engine=1, rank_final=1` |

Use o *Replace in Files* com `recomendacoes.get(rank=` → `recomendacoes.get(rank_final=`. Depois confira:

```bash
grep -rn "rank=[0-9]\|\.rank\b" backend --include=*.py --exclude-dir=.venv --exclude-dir=migrations
```

Tem de sair vazio.

### Novo: `quiz/tests/test_rank_final.py`

```python
from accounts.servicos import registrar_interesse
from quiz.tests.base import BaseEducMatch


class RankFinalTest(BaseEducMatch):
    """PRE-01: a ordem da engine e a ordem entregue são colunas separadas."""

    def test_sem_llm_a_ordem_entregue_e_a_da_engine(self):
        tentativa = self.criar_tentativa()
        for rec in tentativa.recomendacoes.all():
            with self.subTest(curso=rec.curso_id):
                self.assertEqual(rec.rank_final, rec.rank_engine)

    def test_principal_e_o_primeiro_entregue(self):
        tentativa = self.criar_tentativa()
        principais = [rec for rec in tentativa.recomendacoes.all() if rec.is_primary]
        self.assertEqual(len(principais), 1)
        self.assertEqual(principais[0].rank_final, 1)

    def test_snapshot_segue_a_ordem_entregue_e_guarda_a_da_engine(self):
        """Simula a LLM trocando o 1º e o 2º lugar."""
        tentativa = self.criar_tentativa()
        primeiro = tentativa.recomendacoes.get(rank_engine=1)
        segundo = tentativa.recomendacoes.get(rank_engine=2)
        primeiro.rank_final, segundo.rank_final = 2, 1
        primeiro.save(update_fields=["rank_final"])
        segundo.save(update_fields=["rank_final"])

        interesse, _ = registrar_interesse(self.criar_usuario(), segundo.curso, tentativa)

        self.assertEqual(interesse.rank_snapshot, 1)
        self.assertEqual(interesse.rank_engine_snapshot, 2)
        self.assertTrue(interesse.era_principal)

    def test_resultado_mostra_a_ordem_entregue(self):
        self.responder_tudo()
        from quiz.models import Tentativa_de_resposta

        tentativa = Tentativa_de_resposta.objects.latest("id")
        primeiro = tentativa.recomendacoes.get(rank_engine=1)
        segundo = tentativa.recomendacoes.get(rank_engine=2)
        primeiro.rank_final, segundo.rank_final = 2, 1
        primeiro.save(update_fields=["rank_final"])
        segundo.save(update_fields=["rank_final"])

        resposta = self.client.get(f"/resultado/{tentativa.pk}/")

        self.assertEqual(resposta.context["destaque"]["curso"], segundo.curso)
```

> [!tip] Os dois últimos testes são o ensaio do Passo 9
> Eles fazem à mão exatamente o que a LLM vai fazer: trocar o `rank_final`. Se passam agora, a tela e o C4 já estão prontos para a reordenação antes de existir uma linha de Gemini.

---

## ✅ Verificação

```bash
cd backend
python manage.py makemigrations --check --dry-run    # No changes detected
python manage.py test                                # 78 testes
python manage.py migrate                             # no seu banco local
python manage.py showmigrations quiz accounts        # 0004 do quiz e 0005 do accounts com [X]
```

> [!caution] Faça backup do banco local antes do `migrate`
> O `.sql` está no `.gitignore`, então ele não volta pelo Git:
> ```bash
> mysqldump -u root -p educmatch > ../educmatch-antes-pre-01.sql
> ```
> Se o `mysqldump` não estiver no PATH (na revisão ele não estava), use o MySQL Workbench: **Server → Data Export**, schema `educmatch`, *Export to Self-Contained File*.

## 📦 Commit e PR

```bash
git add -A
git commit -m "feat(motor): separa rank_engine de rank_final e grava metadados da LLM

- Recomendacao.rank -> rank_engine + rank_final (migracao manual com copia)
- Tentativa ganha llm_model, prompt_version, latency_ms, tokens, used_fallback, diverged, cache_hit
- principal = rank_final == 1 (tela, C4 e painel)
- Interesse ganha rank_engine_snapshot para o experimento engine x LLM"
git push -u origin feature/rank-engine-final
gh pr create --base develop --fill
```

> [!success] Definition of Done
> 78 testes, `makemigrations --check` limpo, migração aplicada no banco local sem perder a ordem das recomendações antigas, e **nenhuma referência a `.rank` ou `rank=`** fora das migrações.
