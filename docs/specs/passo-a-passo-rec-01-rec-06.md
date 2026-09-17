---
title: "Passo a passo — REC-01 a REC-06 (os erros da recomendação e os campos do C4)"
aliases: ["Passo a passo REC", "Erros da recomendação", "Consertar o motor", "Fase 2 do plano v0.2", "REV-01 a REV-04 na prática"]
tags: [tcc, motor, recomendacao, django, migration, execucao, passo-a-passo, contrato]
status: proposto
projeto: TCC
criado: 2026-09-17
---

> [!info] Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-v02-supabase-a-testes|🗺️ Plano v0.2]] · Achados: [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 REV-01 a REV-04 e REV-09]] · Contrato: [[contratos-c1-a-c6 🟢|📜 C4]] · Motor: [[engine-matching-cosseno 🟢|🧮 Engine de cosseno]] · Vem depois de: [[Projetos/EducMatch(Secretária)/passo-a-passo-sb-01-sb-06|🗄️ SB-01 a SB-06]]

# 🧮 Passo a passo — REC-01 a REC-06

> [!abstract] O que esta nota é
> O **como** da Fase 2: os cinco defeitos que a auditoria encontrou na recomendação, mais os três campos que o `C4` mandava gravar e que nunca chegaram ao banco. Um PR só, porque quatro deles mexem nos mesmos dois models.
> Nenhum toca no cálculo do cosseno. **O núcleo do trabalho está certo** — o que está errado é a borda: o que entra no cálculo, o que sai dele e o que é gravado depois.

> [!warning] Nada disto foi executado
> Escrito contra [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|REV-01 a REV-09]] e [[contratos-c1-a-c6 🟢|C4]], registrados em 11/09/2026 — não contra o repositório aberto. Os números de linha (`quiz/engine.py:100`, `accounts/models.py:63`, `accounts/views.py:112`) vêm de lá. **Abra cada arquivo e confirme a assinatura real antes de colar.** A seção 8 é o que prova que deu certo.

> [!danger] Esta fase depende da Fase 1 estar mesclada
> A REC-03 converte um `TextField` em `JSONField`. No Postgres isso é `jsonb` nativo; no MySQL é outro tipo, com outra migração. Fazer antes do Supabase é fazer duas vezes. E os testes desta fase precisam do Postgres local montado na SB-05.

## 🧭 O mapa da fase

| Tarefa | Achado | Arquivo | Migração? |
|---|---|---|---|
| **REC-01** | `REV-01` · `criado_em` é `auto_now` | `accounts/models.py` | ✅ |
| **REC-06** | `C4` · faltam os 3 campos de *snapshot* | `accounts/models.py` + `views.py` | ✅ (a mesma) |
| **REC-02** | `REV-02` · motor recomenda curso inativo | `quiz/engine.py` | ❌ |
| **REC-03** | `REV-03` · `explicacao` é *repr* de dicionário | `quiz/models.py` | ✅ (à mão) |
| **REC-04** | `REV-04` · confiança sobre o top-5 já cortado | `quiz/engine.py` | ❌ |
| **REC-05** | `REV-09` · N+1 no ranking (~27 consultas) | `quiz/engine.py` | ❌ |

> [!success] Por que os seis num PR só
> REC-01 e REC-06 abrem o mesmo model (`Interesse`) — duas migrações onde uma resolve. REC-02, 04 e 05 abrem o mesmo arquivo (`quiz/engine.py`), e a REC-05 reescreve justamente a função que a REC-02 filtra. Separar seria abrir o mesmo arquivo três vezes e resolver conflito consigo mesmo.
> A REC-03 é a única que poderia sair em PR próprio. Fica junto porque o painel da Fase 3 precisa dos seis, e porque um `migrate` só é mais fácil de explicar ao grupo do que três.

---

## 🚦 Antes de abrir o editor

```bash
git checkout main && git pull
git checkout -b fix/motor-recomendacao
```

Confirme que a Fase 1 está dentro e que você está em Postgres:

```bash
./.venv/Scripts/python.exe manage.py shell -c "from django.db import connection; print(connection.vendor)"
./.venv/Scripts/python.exe manage.py showmigrations accounts quiz
```

> [!danger] `migrate` no Supabase só depois do merge
> Esta é a regra que entrou na SB-05 e esta fase é a primeira a ser afetada por ela. O banco de desenvolvimento agora é compartilhado: aplicar as migrações desta branch no Supabase antes do merge dá ao resto do grupo colunas que o código deles não conhece.
> Enquanto o PR estiver em revisão, **teste contra o Postgres local**:
> ```bash
> DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/educmatch_test \
> PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe manage.py test
> ```

---

## 1️⃣ REC-01 + REC-06 — o model `Interesse`

Duas coisas na mesma classe: a data que mente e os três campos que faltam.

### `accounts/models.py` — a classe `Interesse`

```python
class Interesse(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interesses"
    )
    curso = models.ForeignKey(
        "catalogo.Curso", on_delete=models.PROTECT, related_name="interessados"
    )
    tentativa_origem = models.ForeignKey(
        "quiz.Tentativa_de_resposta",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interesses",
    )

    # C4 — o retrato do momento em que a pessoa salvou.
    # Nulos nos registros criados antes desta migracao: a data de corte
    # esta declarada na monografia, e o painel conta so os nao-nulos.
    afinidade_snapshot = models.FloatField("afinidade no momento", null=True, blank=True)
    rank_snapshot = models.SmallIntegerField("posicao no momento", null=True, blank=True)
    era_principal = models.BooleanField("era o 1o colocado", null=True, blank=True)

    status = models.CharField(max_length=20, default="quero-fazer")
    nota = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)      # era auto_now
    atualizado_em = models.DateTimeField(auto_now=True)      # o campo que faltava

    class Meta:
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(fields=["usuario", "curso"], name="unico_interesse_por_curso")
        ]
```

> [!danger] `auto_now` × `auto_now_add` — a diferença de uma palavra e de toda a série temporal
> `auto_now=True` reescreve o valor **a cada `save()`**. `criado_em` era, na prática, um `atualizado_em` com o nome errado, e o `ordering = ["-criado_em"]` ordenava por "último toque", não por "criação".
> Consequência direta: **nenhuma métrica de conversão por período do painel era confiável** — `criado_em__gte=inicio` significava *"interesses tocados no período"*. É por isso que `REV-01` é listado como bloqueador do painel, e por isso que a Fase 2 vem antes da Fase 3.
> E é por isso que `atualizado_em` nasce junto: o comportamento antigo tinha utilidade (saber quando alguém mexeu no status), só estava no campo errado.

> [!warning] Os dados já gravados ficam imprecisos, e isso precisa estar escrito na monografia
> A migração não recupera a data de criação real de quem já existe — a informação foi sobrescrita. O que o `auto_now_add` garante é a partir de agora.
> Tratamento honesto: uma data de corte declarada no texto (*"a série temporal de interesses é válida a partir de <data do merge>"*) e o painel contando só o que está depois dela. Ver [[Conceitos/Metodologia Científica/met-validade-e-limitacoes|⚖️ Validade e limitações]].

> [!important] Os três nomes novos vão para o glossário **neste PR**
> `afinidade_snapshot` ↔ `score_snapshot`, `rank_snapshot` ↔ `rank_snapshot`, `era_principal` ↔ `was_primary`. É a regra que a **D5** do plano criou, e ela existe precisamente porque onze pares de nomes já nasceram sem registro — o achado central de [[contratos-c1-a-c6 🟢|📜 C1 a C6, seção 9]].
> Se o nome parecer óbvio demais para merecer uma linha na tabela, lembre que `envio_recurso` também pareceu.

```bash
./.venv/Scripts/python.exe manage.py makemigrations accounts -n c4_snapshot_e_criado_em
```

> [!note] Os três campos nascem `null=True` — de propósito
> Sem `null=True`, a migração pede um valor padrão para as linhas existentes, e qualquer valor que você inventar é **dado falso**: um `afinidade_snapshot = 0.0` num interesse antigo afirma que a pessoa salvou um curso com afinidade zero, o que não aconteceu. `NULL` significa *"não sabemos"*, que é a verdade.
> Lidar com `NULL` na consulta custa um `.exclude(rank_snapshot__isnull=True)`. Fabricar dado custa a validade do experimento.

### `accounts/views.py` — usar a variável que estava sendo descartada

Este é o trecho que a auditoria chamou de *"o achado mais eloquente"*: a consulta existia, o resultado era atribuído, e a variável era abandonada na linha seguinte (`accounts/views.py:112`).

```python
# ANTES — rec e calculado e jogado fora
if tentativa:
    rec = tentativa.recomendacoes.filter(curso=curso).first()

item, criado = Interesse.objects.get_or_create(
    usuario=request.user, curso=curso,
    defaults={"tentativa_origem": tentativa},
)
```

```python
# DEPOIS — rec vira as tres colunas que o C4 pedia
rec = (
    tentativa.recomendacoes.filter(curso=curso).first()
    if tentativa
    else None
)

item, criado = Interesse.objects.get_or_create(
    usuario=request.user,
    curso=curso,
    defaults={
        "tentativa_origem": tentativa,
        "afinidade_snapshot": rec.afinidade if rec else None,
        "rank_snapshot": rec.rank if rec else None,
        "era_principal": (rec.rank == 1) if rec else None,
    },
)
```

> [!important] São seis linhas, e é o que transforma o experimento da F2
> Sem `era_principal`, o TCC compara engine × LLM **por avaliação do próprio grupo**. Com ele, compara **por comportamento de usuário real**: quando a LLM promoveu outro curso ao topo, a taxa de salvamento subiu ou caiu?
> É a métrica de resultado do Passo 11, e ela não existe retroativamente — só a partir do dia em que estas seis linhas estiverem na `main`. Quanto mais tarde entrarem, menos dado o experimento tem. Esse é o argumento para a Fase 2 não esperar.

> [!warning] `defaults` só vale na criação — e o botão é um alternador
> `get_or_create` ignora `defaults` quando a linha já existe. Se a pessoa salvou o curso antes desta mudança, os três campos dela continuam `NULL` para sempre, mesmo que ela abra a página de novo.
> Isso está **correto** e é intencional: o *snapshot* é o retrato do momento da decisão, e esse momento passou. Preencher agora com a recomendação atual seria inventar história. O painel conta só os não-nulos; a monografia declara a data de corte.

> [!tip] Confira se a remoção do interesse apaga a linha ou muda o status
> Se `remover_interesse` faz `delete()`, um mesmo curso salvo → removido → salvo de novo gera um `Interesse` novo, com *snapshot* novo — e a análise vê duas decisões, que é o que de fato houve. Se faz `status = "removido"`, o *snapshot* antigo permanece e descreve a primeira decisão. Os dois comportamentos são defensáveis; o que não é defensável é ninguém saber qual está no código. Registre no PR qual é.

---

## 2️⃣ REC-02 — o motor recomenda curso desativado

`quiz/engine.py:100` passa `Curso.objects.all()` para a função de ranking. O campo `is_active` existe, está exposto no `/admin`, e a expectativa de quem desativa um curso é óbvia.

```python
# ANTES
cursos = Curso.objects.all()
```

```python
# DEPOIS
cursos = Curso.objects.filter(is_active=True)
```

> [!warning] Uma linha, três consequências
> 1. Curso desativado sai das recomendações — o que o admin já achava que acontecia.
> 2. Curso desativado sai da **contagem de matches do painel**, que é por que `REV-02` é listado como bloqueador da Fase 3.
> 3. O ranking de quem responder depois muda. Se algum curso está desativado hoje, **os rankings antes e depois deste PR não são comparáveis** — e isso importa para a calibração de pesos. Confira quantos são antes de mesclar:
> ```bash
> ./.venv/Scripts/python.exe manage.py shell -c "from catalogo.models import Curso; print(Curso.objects.filter(is_active=False).count())"
> ```
> Se der zero, nada muda hoje e a linha é prevenção. Se der mais que zero, diga o número no PR.

> [!danger] O `filter` tem de estar na **origem**, não na exibição
> A tentação é filtrar na view, ao montar a tela. Aí o curso inativo continua entrando no cálculo, continua sendo gravado em `Recomendacao` e continua contando no painel — só não aparece para o usuário. O defeito viraria invisível em vez de resolvido, e é o pior resultado possível: um bug que passou a mentir melhor.

---

## 3️⃣ REC-03 — `explicacao` deixa de ser texto e passa a ser JSON

Hoje o dicionário de `top_areas` vai para um `TextField` via `str()`, e `quiz/web_views.py:16` reconstrói com `ast.literal_eval` dentro de um `try/except` que devolve lista vazia **em silêncio** quando falha.

### Por que isto bloqueia o painel

A métrica de "demanda por área" precisa ler as áreas de dentro do banco. Com texto, não dá: `'{"eletrica": 0.42}'` é uma string — não se filtra, não se agrega, não se soma. E o `except` silencioso significa que uma explicação corrompida virou "sem explicação" sem nunca aparecer em log nenhum.

### `quiz/models.py`

```python
class Recomendacao(models.Model):
    ...
    explicacao = models.JSONField("areas que pesaram", default=dict, blank=True)
```

### A migração — esta você **escreve**, não gera

```bash
./.venv/Scripts/python.exe manage.py makemigrations quiz --empty -n explicacao_para_jsonb
```

E preenche o arquivo criado:

```python
import ast

from django.db import migrations, models


def texto_para_json(apps, schema_editor):
    """Converte o repr de dicionario Python gravado como texto em JSON de verdade."""
    Recomendacao = apps.get_model("quiz", "Recomendacao")
    convertidas = falhas = 0

    for rec in Recomendacao.objects.exclude(explicacao="").iterator():
        try:
            valor = ast.literal_eval(rec.explicacao)
        except (ValueError, SyntaxError):
            falhas += 1
            continue
        if not isinstance(valor, dict):
            falhas += 1
            continue
        Recomendacao.objects.filter(pk=rec.pk).update(explicacao_json=valor)
        convertidas += 1

    # A contagem e impressa de proposito: perda silenciosa foi o defeito original.
    print(f"\n  explicacao: {convertidas} convertidas, {falhas} ilegiveis (ficaram vazias)")


def json_para_texto(apps, schema_editor):
    Recomendacao = apps.get_model("quiz", "Recomendacao")
    for rec in Recomendacao.objects.exclude(explicacao_json=None).iterator():
        Recomendacao.objects.filter(pk=rec.pk).update(explicacao=str(rec.explicacao_json))


class Migration(migrations.Migration):
    dependencies = [("quiz", "0002_camada_ia")]   # confira o nome real da ultima

    operations = [
        migrations.AddField(
            model_name="recomendacao",
            name="explicacao_json",
            field=models.JSONField(null=True, blank=True),
        ),
        migrations.RunPython(texto_para_json, json_para_texto),
        migrations.RemoveField(model_name="recomendacao", name="explicacao"),
        migrations.RenameField(
            model_name="recomendacao",
            old_name="explicacao_json",
            new_name="explicacao",
        ),
        migrations.AlterField(
            model_name="recomendacao",
            name="explicacao",
            field=models.JSONField("areas que pesaram", default=dict, blank=True),
        ),
    ]
```

> [!danger] **Nunca** deixe o Django gerar um `AlterField` direto de `TextField` para `JSONField` aqui
> Ele produz, no Postgres, algo equivalente a `ALTER COLUMN explicacao TYPE jsonb USING explicacao::jsonb` — e isso **falha na primeira linha**, porque o conteúdo gravado é *repr* de Python, com aspas simples, e aspas simples não são JSON válido:
> ```
> DataError: invalid input syntax for type json
> DETAIL: Token "'" is invalid.
> ```
> Se a tabela estiver vazia, o `AlterField` passa — e você descobre o problema meses depois, na máquina de quem tinha dados. O caminho de cinco operações acima é mais longo porque é o que funciona nos dois casos.

> [!important] `apps.get_model()`, nunca `from quiz.models import Recomendacao`
> Dentro de migração, o model precisa vir do **estado histórico** daquela migração, não do arquivo atual. Importando direto, a migração roda contra a versão de hoje do model — e quebra no dia em que alguém rodar as migrações do zero numa máquina nova, com uma mensagem que não aponta para aqui. É o mesmo tipo de armadilha do `use_in_migrations = True` registrada na [[Projetos/EducMatch(Secretária)/passo-a-passo-aut-01-aut-03|AUT-01]].

> [!note] O `print` da contagem não é *debug* esquecido
> O defeito original era **perda silenciosa** de dado. Uma migração que converte e não diz quantas linhas não conseguiu converter repete o mesmo pecado num nível mais alto. O número aparece no terminal de quem roda o `migrate` e entra no recado ao grupo.

### `quiz/web_views.py` — apagar o `try/except`

```python
# ANTES (linha 16)
try:
    areas = ast.literal_eval(rec.explicacao)
except Exception:
    areas = []
```

```python
# DEPOIS
areas = rec.explicacao or {}
```

E remova o `import ast` do topo, que deixa de ser usado.

> [!tip] `import` sobrando é rastro de intenção esquecida
> [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições, Passo 5]] já registrou isso com o `transaction` importado e não usado. Ao terminar cada tarefa desta fase, releia os imports do arquivo que você tocou.

> [!warning] O template também muda: dicionário não se percorre igual a lista
> Se `resultado.html` fazia `{% for area in rec.explicacao %}` sobre uma lista, com dicionário isso passa a iterar as **chaves**. Para nome e peso juntos:
> ```html
> {% for nome, peso in rec.explicacao.items %}
> ```
> É uma mudança de duas palavras que os testes de backend não pegam. Está no clique 4 da seção 8.

---

## 4️⃣ REC-04 — a confiança que nunca avisa nada

`confianca()` tira a média das afinidades **depois** do `[:limit]`. É a média dos cinco melhores, que é quase sempre alta — então o aviso de baixa confiança no `resultado.html` praticamente nunca dispara.

### `quiz/engine.py`

```python
BANDA_CONFIANCA_ALTA = 0.15
BANDA_CONFIANCA_MEDIA = 0.05


def confianca(ranking_completo):
    """Quanto o 1o lugar se separou do 2o, no ranking INTEIRO.

    Recebe o ranking completo, antes de qualquer corte. Quem chamar
    com a lista ja cortada mede a coisa errada -- era o REV-04.
    """
    if len(ranking_completo) < 2:
        return "indefinida"

    primeiro = ranking_completo[0].afinidade
    segundo = ranking_completo[1].afinidade

    if primeiro <= 0:
        return "baixa"          # quiz em branco: nada separou nada

    separacao = (primeiro - segundo) / primeiro

    if separacao >= BANDA_CONFIANCA_ALTA:
        return "alta"
    if separacao >= BANDA_CONFIANCA_MEDIA:
        return "media"
    return "baixa"
```

E no chamador, a ordem que importa:

```python
ranking = rank_cursos(perfil, cursos)          # completo
nivel = confianca(ranking)                     # mede antes do corte
top = ranking[:limit]                          # so agora corta
```

> [!important] Separação **relativa**, não diferença absoluta
> `primeiro - segundo` pareceria mais simples, e quebraria a propriedade que este projeto defende. O teste `test_escala_nao_muda_o_score` de [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]] dobra todos os pesos do perfil e exige o mesmo resultado — é **a decisão de usar cosseno**, transformada em asserção.
> Com diferença absoluta, dobrar os pesos dobraria o *gap* e um perfil "médio" viraria "alto" sem nada ter mudado. Dividir por `primeiro` devolve a invariância de escala. **A correção da confiança tinha de respeitar a decisão do motor, não apenas trocar de fórmula.**

> [!danger] Confirme a assinatura real antes de colar
> A [[Projetos/EducMatch(Secretária)/passo-a-passo-f1-04-f1-03|F1-04]] introduziu `conjunto_empate` e uma "banda" — este código pode ter de se compor com o que já existe, em vez de substituí-lo. Se houver conflito de conceito (duas noções de confiança no mesmo arquivo), **pare e resolva no PR, com a F2 na conversa**: `confidence_level` é o campo pelo qual o Passo 11 vai segmentar o experimento comparativo, e duas definições concorrentes invalidam a segmentação.

> [!warning] As duas bandas são um chute — e precisam ser calibradas com dado
> `0.15` e `0.05` são um ponto de partida razoável, não um resultado. Depois de o painel da Fase 3 mostrar a distribuição real, os números mudam. Deixe-os como **constantes no topo do módulo**, com esse nome, para que a calibração seja editar duas linhas — e para que o valor usado na coleta esteja rastreável no `git log` quando a monografia precisar citá-lo.

---

## 5️⃣ REC-05 — as 27 idas ao banco

Cada curso dispara uma consulta para os pesos e cada alternativa uma para os dela: ~27 consultas por submissão com 20 cursos e 6 respostas.

### `quiz/engine.py`

```python
cursos = (
    Curso.objects
    .filter(is_active=True)                      # a REC-02, junto
    .prefetch_related("curso_peso__area")
)

respostas = (
    tentativa.respostas
    .select_related("alternativa")
    .prefetch_related("alternativa__pesos__area")
)
```

> [!note] `select_related` e `prefetch_related` não são sinônimos
> `select_related` vale para `ForeignKey` e faz **um** `JOIN` — é o caso de `resposta → alternativa`.
> `prefetch_related` vale para relação para muitos e faz **uma segunda consulta** que o Django casa em memória — é o caso de `curso → pesos → área`.
> Trocar um pelo outro dá erro imediato e legível, então não é armadilha. A armadilha é não usar nenhum dos dois e nunca perceber, porque em desenvolvimento, com 20 cursos, ninguém sente.

> [!success] Esta é a única correção da fase que rende parágrafo **medido** na monografia
> As outras cinco são "estava errado, corrigimos". Esta tem número antes e depois:
> ```python
> from django.test.utils import CaptureQueriesContext
> from django.db import connection
>
> with CaptureQueriesContext(connection) as ctx:
>     recomendar(tentativa)
> print(len(ctx))
> ```
> Rode **antes** de aplicar o `prefetch`, anote o número, aplique e rode de novo. Otimização com medida é metodologia; otimização sem medida é opinião. Ver [[Projetos/EducMatch(Secretária)/artigo-secao-calculo-cosseno 🟢|✍️ Como o cálculo vira seção de artigo]] para o formato.

> [!warning] Meça no Postgres, não no MySQL antigo
> O número de consultas é o mesmo, mas o tempo total não: agora cada consulta atravessa a internet até o Supabase. É justamente por isso que N+1 deixou de ser detalhe — 27 idas ao banco na rede custam o que 27 idas ao `localhost` não custavam. Se quiser o número de impacto para o texto, meça o **tempo** também, com o `DATABASE_URL` do Supabase.

---

## 6️⃣ Os testes desta fase

Cinco testes, um por defeito. O `quiz/tests.py` está vazio hoje — a Fase 4 é que monta a suíte inteira; aqui entram só estes, porque a regra do plano é que **nenhum PR entra sem um teste que falharia antes**.

### `quiz/tests.py`

```python
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from catalogo.models import Curso
from quiz.engine import confianca


class ConfiancaTest(TestCase):
    """REV-04: a confianca mede a separacao do 1o para o 2o, no ranking completo."""

    class Falso:
        def __init__(self, afinidade):
            self.afinidade = afinidade

    def bandas(self, *valores):
        return confianca([self.Falso(v) for v in valores])

    def test_primeiro_muito_a_frente_da_alta(self):
        self.assertEqual(self.bandas(0.90, 0.40, 0.30), "alta")

    def test_empate_tecnico_da_baixa(self):
        self.assertEqual(self.bandas(0.80, 0.79, 0.70), "baixa")

    def test_quiz_em_branco_nao_estoura(self):
        self.assertEqual(self.bandas(0.0, 0.0, 0.0), "baixa")

    def test_escala_nao_muda_a_banda(self):
        """A mesma invariancia que justifica o cosseno: dobrar tudo nao muda nada."""
        self.assertEqual(self.bandas(0.90, 0.40), self.bandas(1.80, 0.80))


class RecomendacaoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        silencio = StringIO()
        for comando in ("seed_areas", "seed_cursos", "seed_questoes"):
            call_command(comando, stdout=silencio)

    def test_curso_inativo_fica_fora_do_ranking(self):
        """REV-02: desativar um curso no admin tem que tira-lo das recomendacoes."""
        fora = Curso.objects.filter(is_active=True).first()
        fora.is_active = False
        fora.save()

        tentativa = self.responder_tudo()

        self.assertFalse(
            tentativa.recomendacoes.filter(curso=fora).exists(),
            "curso desativado apareceu na recomendacao",
        )

    def test_explicacao_e_dicionario_consultavel(self):
        """REV-03: explicacao tem que voltar do banco como dict, nao como texto."""
        tentativa = self.responder_tudo()
        primeira = tentativa.recomendacoes.order_by("rank").first()

        self.assertIsInstance(primeira.explicacao, dict)
        self.assertTrue(primeira.explicacao, "explicacao veio vazia")

    def test_ranking_nao_faz_uma_consulta_por_curso(self):
        """REV-09: o numero de consultas nao cresce com o tamanho do catalogo."""
        with self.assertNumQueries(12):       # ajuste ao numero real medido
            self.responder_tudo()
```

E, em `accounts/tests.py`, o teste do `C4`:

```python
class SnapshotDoInteresseTest(TestCase):
    def test_salvar_interesse_grava_afinidade_rank_e_era_principal(self):
        """C4: os tres campos que o contrato pedia e que a v0.1 descartava."""
        # ... login, responder o quiz, salvar o 1o curso recomendado ...
        interesse = Interesse.objects.get(usuario=self.usuario, curso=curso_top1)

        self.assertIsNotNone(interesse.afinidade_snapshot)
        self.assertEqual(interesse.rank_snapshot, 1)
        self.assertTrue(interesse.era_principal)

    def test_criado_em_nao_muda_quando_o_status_muda(self):
        """REV-01: auto_now reescrevia a data a cada save()."""
        interesse = Interesse.objects.create(usuario=self.usuario, curso=self.curso)
        nascimento = interesse.criado_em

        interesse.status = "matriculado"
        interesse.save()
        interesse.refresh_from_db()

        self.assertEqual(interesse.criado_em, nascimento)
        self.assertGreater(interesse.atualizado_em, nascimento)
```

> [!important] `test_criado_em_nao_muda_quando_o_status_muda` é o guardião do `REV-01`
> É o teste mais importante dos sete, e o que menos parece. `auto_now` × `auto_now_add` é uma palavra de diferença, e o defeito é **invisível** — nada quebra, nada dá erro, a data simplesmente passa a significar outra coisa. Se alguém reverter isso por engano num merge, este teste é a única coisa no repositório que percebe.

> [!warning] `assertNumQueries(12)` — o número tem de ser o **seu**, medido
> Colar 12 sem medir transforma um teste de desempenho num teste de adivinhação, e ele vai falhar no primeiro `prefetch` legítimo que alguém acrescentar. Rode `CaptureQueriesContext` (seção 5) depois do conserto, leia o número, e escreva-o com um comentário dizendo em que commit foi medido.
> Quando esse teste falhar no futuro, a pergunta certa é *"o que passou a consultar mais?"* — e é exatamente para essa pergunta existir que ele vale a pena.

---

## 7️⃣ O que **não** entra nesta fase

- **A cobertura do instrumento.** Seis áreas sem nenhuma questão é conteúdo, é da F3, e o painel da Fase 3 vai medir o tamanho do buraco.
- **A camada REST em erro 500** (`REV-05`). É o `C3`, e é a Fase 4.
- **O *claim* da tentativa anônima** (`C6`). Fase 4.
- **Recalibrar os pesos do catálogo.** O `REV-02` muda o conjunto de cursos que entra no cálculo, então qualquer calibração feita agora é calibração sobre outra base. Depois do painel.
- **Mexer no cálculo do cosseno.** Ele está certo. É o ativo mais forte do trabalho e nenhuma das seis tarefas o toca.

---

## 8️⃣ Verificação

```bash
./.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

Tem de dizer que **não há mudanças pendentes**. Se ele quiser criar migração para `quiz` ou `accounts`, algum model mudou depois do `makemigrations` — ou a migração escrita à mão da REC-03 não terminou no mesmo estado que o `models.py`.

```bash
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/educmatch_test \
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe manage.py test
```

O teste que só a REC-03 exige — provar que a migração **volta**:

```bash
./.venv/Scripts/python.exe manage.py migrate quiz <numero-anterior>
./.venv/Scripts/python.exe manage.py migrate quiz
```

> [!important] Migração de dados sem reversão testada é migração que ninguém ousa aplicar
> A `json_para_texto` existe para isto. Se a ida funciona e a volta estoura, você descobre agora, no seu Postgres local, e não no Supabase compartilhado às onze da noite com o grupo esperando.

E os cinco cliques:

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | Responder o quiz inteiro | 5 cursos, com explicação legível |
| 2 | Responder marcando tudo na mesma coluna | Aviso de **baixa confiança** aparece — antes nunca aparecia |
| 3 | `/admin` → desativar um curso → responder de novo | O curso não aparece mais no resultado |
| 4 | Olhar a lista de áreas no resultado | Nome **e** peso de cada área, não só o nome (o `.items` do template) |
| 5 | Logado, salvar o 1º curso → `/admin` → **Interesses** | `afinidade snapshot`, `posicao no momento` e `era o 1o colocado` preenchidos |

> [!important] O clique 2 é o único jeito de saber que a REC-04 funcionou de verdade
> Um perfil "indeciso" — todas as respostas puxando para lados diferentes, ou todas iguais — é o caso que o aviso de baixa confiança existe para pegar, e o caso em que ele nunca disparava. Se depois da correção ele continuar sem aparecer, ou as bandas estão erradas para a distribuição real, ou o chamador continua passando a lista já cortada.

> [!warning] O clique 5 é o `C4` sendo conferido a olho
> Os testes provam que os campos são gravados; o `/admin` prova que estão **visíveis para quem vai usar o dado**. Se os três campos não aparecem na tela do `Interesse`, falta acrescentá-los ao `InteresseAdmin` — e um campo que o grupo não vê é um campo que o grupo esquece que existe.

---

## 9️⃣ Commit, push, PR e o recado

```bash
git add -A
git commit -m "fix(motor): ignora curso inativo, confianca sobre o ranking completo e explicacao em JSON"
git commit -m "feat(contas): grava afinidade, rank e era_principal no interesse (C4)"
git push -u origin fix/motor-recomendacao
```

> [!tip] Dois commits, um PR
> O merge é *squash*, então na `main` isso vira um commit só. Separar aqui serve à **revisão**: quem revisa consegue ler o diff do motor e o diff do contrato separadamente, em vez de encarar as duas coisas num bloco.

No template, o campo que não pode ficar em branco:

```markdown
## Toca contrato de outra frente? (x) sim → C4 (Interesse) e o confidence_level do Passo 11
```

> [!danger] Duas aprovações neste PR, e uma delas é a F2
> `confidence_level` é o campo pelo qual o experimento comparativo vai segmentar a amostra, e `era_principal` é a métrica de resultado dele. Mudar a definição dos dois sem a F2 na conversa é mudar o instrumento de medida do experimento de outra pessoa.

Recado para o grupo, **antes do merge**:

> Subi o PR da `fix/motor-recomendacao`. Ele conserta cinco defeitos da recomendação e acrescenta três campos no `Interesse`.
>
> **Quando eu mesclar, rode:**
>
> ```
> git checkout main && git pull
> ```
>
> Não precisa rodar `migrate` — eu aplico no Supabase depois do merge, uma vez, e aviso aqui quando terminar.
>
> **O que muda no que você vê:**
>
> - curso desativado no `/admin` **sai** das recomendações (antes ficava);
> - o aviso de "baixa confiança" no resultado **passa a aparecer** de verdade para quem responde indeciso — antes ele praticamente nunca disparava;
> - a explicação da recomendação agora é JSON no banco. Se você usa `rec.explicacao` em algum template, virou dicionário: `{% for nome, peso in rec.explicacao.items %}`.
>
> **Sobre os dados antigos:** a migração converte as explicações já gravadas e **imprime quantas não conseguiu converter**. Vou colar o número aqui quando rodar.
>
> ⚠️ **Para a F2 (camada de IA):** a definição de `confianca` mudou — agora é a separação relativa entre 1º e 2º, sobre o ranking completo. É o campo pelo qual o Passo 11 segmenta o experimento. Se isso conflita com o que você planejou, fale **antes** do merge.
>
> ⚠️ **Para todos:** `Interesse.criado_em` era `auto_now` e estava sendo reescrito a cada alteração. As datas dos interesses que já existem **estão erradas e não dá para recuperar**. A série temporal é válida a partir de hoje, e isso precisa aparecer nas limitações da monografia.

---

## ▶️ Próxima ação

**Fase 3 — o painel (PNL-01 a PNL-05).** Os seis bloqueadores saíram do caminho: `criado_em` é confiável, a explicação é consultável, curso inativo não conta, a confiança discrimina, e o `Interesse` tem *snapshot*. O painel agora pode ler.

Abra a branch da Fase 3 **só depois** de este PR estar na `main` — as duas fases criam migração, e é o único conflito que o Git não resolve sozinho.

Ver [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 Passo a passo PNL-01 a PNL-05]].

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/plano-execucao-v02-supabase-a-testes|🗺️ Plano v0.2]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-sb-01-sb-06|🗄️ Fase 1 — Supabase]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 Fase 3 — painel]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|🧪 Fase 4 — testes]]
- [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel e refino]] — origem dos `REV`
- [[contratos-c1-a-c6 🟢|📜 C1 a C6]] — o `C4` e a variável `rec` abandonada
- [[engine-matching-cosseno 🟢|🧮 Engine de matching]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-f1-04-f1-03|🎚️ F1-04 — conjunto de empate e banda]]
- [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições]] — acrescente os desta fase ao terminar
- **Conceitos:** [[Migrations|Migrations]] · [[Models|Models]] · [[ORM|ORM]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]] · [[Projetos|🚀 Projetos]]
