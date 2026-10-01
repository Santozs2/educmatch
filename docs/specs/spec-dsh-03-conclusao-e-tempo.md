---
title: "Spec DSH-03 — início do quiz, taxa de conclusão e tempo típico"
aliases: ["DSH-03", "Conclusão e tempo do quiz", "InicioDeQuiz"]
tags: [tcc, spec, painel, quiz, migracao, privacidade, lgpd]
status: proposto
projeto: TCC
branch: feature/quiz-conclusao-e-tempo
criado: 2026-10-01
---

> [!info] Plano: [[plano-dashboard-git-flow|🖥️ Dashboard novo e Git Flow]] · Anterior: [[spec-dsh-02-cursos-links-interesse|02 — Cursos, Links e Interesse]]

# ⏱️ DSH-03: início do quiz, taxa de conclusão e tempo típico

**Branch:** `feature/quiz-conclusao-e-tempo`, saindo da `develop` **com a DSH-02 já mesclada**
**Risco:** médio. **Uma migração** (um campo novo e uma tabela nova) e uma mudança no fluxo do quiz do aluno.
**Testes ao final:** 114 (103 + 11 novos)

> [!abstract] O que esta branch faz
> O design pede dois KPIs na tela Quiz que **o banco não consegue responder hoje**: "% concluídos" e "tempo médio". A `Tentativa_de_resposta` só nasce no fim do quiz, com `criado_em`. Não há registro de quem começou e desistiu, nem de quando começou.
> 1. Model novo `InicioDeQuiz`: uma linha por quiz começado, **sem dizer de quem**.
> 2. Campo novo `Tentativa_de_resposta.iniciado_em`.
> 3. O quiz grava os dois; o painel mostra **% concluídos**, **tempo típico** e **questões ativas**.

---

## 1️⃣ Onde o quiz "começa"

A tela de introdução (`quiz.html`) envia um **GET** com `respondido_por` e `etapa=1`. É esse o início. Mas o mesmo GET com `etapa=1` também acontece quando:

- o aluno **recarrega** a página;
- o aluno pula a questão 1 e o `pagina_quiz` o manda de volta com `?etapa=1`.

Por isso o início é marcado na **sessão** (`quiz_iniciado_em`) e só é contado se a marca ainda não existir. A marca sai em três lugares: quando o quiz termina, quando ele recomeça (`respondido_por` sem `etapa`) e quando o aluno entra por um link novo.

| Situação | Conta início? |
|---|---|
| Abre a 1ª questão pela primeira vez | ✅ |
| Recarrega, ou volta para a questão 1 | ❌ (a marca já existe) |
| Termina e começa outro quiz | ✅ (a marca saiu no fim) |
| Abre e fecha a aba sem terminar | ✅, e é justamente o abandono que a taxa mede |
| `POST` direto, sem passar pela introdução (os testes antigos fazem isso) | ❌, e a tentativa fica com `iniciado_em` vazio |

## 2️⃣ `quiz/models.py`

Em `Tentativa_de_resposta`, logo depois de `respondido_por`:

```python
    # DSH-03: quando a 1ª questão foi aberta. Vazio em tentativas antigas e nas
    # que chegaram sem passar pela tela de início (POST direto).
    iniciado_em = models.DateTimeField(null=True, blank=True)
```

E um model novo, antes de `class Resposta`:

```python
class InicioDeQuiz(models.Model):
    """Um quiz começado. Serve só para a taxa de conclusão do painel.

    De propósito, não guarda usuário, nome nem sessão: é uma contagem, e o
    painel nunca precisa saber quem começou.
    """
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    questionario_link = models.ForeignKey(
        QuestionarioLink, on_delete=models.SET_NULL, null=True, blank=True, related_name="inicios"
    )

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Início em {self.criado_em:%d/%m/%Y %H:%M}"
```

> [!danger] Por que o `InicioDeQuiz` não tem `user`, `respondido_por` nem sessão
> Ele existe para **uma** conta: começados ÷ concluídos. Guardar quem começou criaria uma lista de "pessoas que desistiram do quiz", que ninguém pediu e que a LGPD trataria como dado pessoal sem finalidade. O teste `test_inicio_nao_guarda_quem_comecou` trava os campos: se alguém acrescentar um, o teste quebra e obriga a discussão.

### A migração

```bash
cd backend
python manage.py makemigrations quiz -n inicio_de_quiz_e_iniciado_em
```

A saída tem de ser exatamente:

```
Migrations for 'quiz':
  quiz\migrations\0005_inicio_de_quiz_e_iniciado_em.py
    + Add field iniciado_em to tentativa_de_resposta
    + Create model InicioDeQuiz
```

> [!success] A migração foi rodada com dados, na ida e na volta
> Num banco com 40 tentativas: `migrate quiz` → `migrate quiz 0004` → `migrate quiz`, sem erro. O campo é `null=True`, então as tentativas antigas ficam com `iniciado_em` vazio, sem precisar de *data migration*.

## 3️⃣ `quiz/web_views.py`

```diff
@@ -2,8 +2,9 @@ from django.db import transaction
 from django.http import Http404 
 from django.shortcuts import get_object_or_404, redirect, render
 from django.urls import reverse
+from django.utils.dateparse import parse_datetime
 from urllib.parse import urlencode
-from quiz.models import Questao, QuestionarioLink, Resposta, Tentativa_de_resposta
+from quiz.models import InicioDeQuiz, Questao, QuestionarioLink, Resposta, Tentativa_de_resposta
 from catalogo.models import Curso
 from accounts.models import Interesse
 from quiz.engine import recomendar
@@ -29,6 +30,21 @@ def areas_da_recomendacao(recomendacao):
         areas_norm.append(area_norm)
     return areas_norm
 
+def _registrar_inicio(request):
+    """Conta um início na primeira vez que este navegador abre a 1ª questão.
+
+    A marca na sessão impede contar de novo ao recarregar ou ao voltar para a
+    questão 1; ela só sai quando o quiz termina ou recomeça.
+    """
+    if request.session.get("quiz_iniciado_em"):
+        return
+    link = QuestionarioLink.objects.filter(
+        token=request.session.get("questionario_link_token"), ativo=True
+    ).first()
+    inicio = InicioDeQuiz.objects.create(questionario_link=link)
+    request.session["quiz_iniciado_em"] = inicio.criado_em.isoformat()
+
+
 def pagina_quiz(request):
     questoes = perguntas_ativas()
     
@@ -38,6 +54,9 @@ def pagina_quiz(request):
         if respondido_por and not etapa:
             request.session.pop("quiz_respostas", None)
             request.session.pop("quiz_respondido_por", None)
+            request.session.pop("quiz_iniciado_em", None)
+        if etapa == "1" or (respondido_por and not etapa):
+            _registrar_inicio(request)
 
         respostas_salvas = request.session.get("quiz_respostas", {})
         for questao in questoes:
@@ -90,6 +109,7 @@ def pagina_quiz(request):
             respondido_por=respondido_por,
             user=usuario,
             questionario_link=questionario_link,
+            iniciado_em=parse_datetime(request.session.get("quiz_iniciado_em") or ""),
         )
         Resposta.objects.bulk_create(
             [
@@ -102,6 +122,7 @@ def pagina_quiz(request):
     tentativas.append(tentativa.pk)
     request.session.pop("quiz_respostas", None)
     request.session.pop("quiz_respondido_por", None)
+    request.session.pop("quiz_iniciado_em", None)
     request.session.modified = True
     
     return redirect("quiz-resultado", pk=tentativa.pk)
@@ -115,6 +136,7 @@ def acessar_questionario(request, token):
     request.session["questionario_link_token"] = str(link.token)
     request.session.pop("quiz_respostas", None)
     request.session.pop("quiz_respondido_por", None)
+    request.session.pop("quiz_iniciado_em", None)
     return redirect("quiz-inicio")
 
 def resultado_pagina(request,pk):
```

> [!note] `parse_datetime("")` devolve `None`
> Por isso o `or ""` na criação da tentativa: sem início na sessão, o campo fica vazio sem precisar de `if`.

## 4️⃣ `painel/metricas.py`

Os imports do topo ficam assim:

```python
from collections import Counter
from datetime import datetime, timedelta
from statistics import median
```

```python
from quiz.models import InicioDeQuiz, Questao, QuestionarioLink, Recomendacao, Tentativa_de_resposta
```

E no fim do arquivo:

```python
def taxa_de_conclusao(inicio):
    """Dos quizzes começados no período, quantos % viraram tentativa.

    Só conta tentativas com iniciado_em: as antigas (antes da DSH-03) não têm
    início registrado e inflariam a taxa acima de 100%.
    """
    from painel.privacidade import K_MINIMO

    comecados = InicioDeQuiz.objects.filter(_no_periodo(inicio)).count()
    if comecados < K_MINIMO:
        return None
    concluidos = Tentativa_de_resposta.objects.filter(
        _no_periodo(inicio, "iniciado_em"), iniciado_em__isnull=False
    ).count()
    return min(concluidos / comecados * 100, 100.0)


def tempo_tipico(inicio):
    """Mediana do tempo entre abrir a 1ª questão e ver o resultado.

    Mediana, e não média: uma aba esquecida aberta por um dia puxaria a média
    para horas, mas não mexe na mediana.
    """
    from painel.privacidade import K_MINIMO

    pares = Tentativa_de_resposta.objects.filter(
        _no_periodo(inicio), iniciado_em__isnull=False
    ).values_list("iniciado_em", "criado_em")
    duracoes = [criado - iniciado for iniciado, criado in pares]
    if len(duracoes) < K_MINIMO:
        return None
    return median(duracoes)


def questoes_ativas():
    return Questao.objects.filter(is_active=True).count()
```

> [!important] Duas decisões que mudam o número
> | Decisão | Alternativa | Por quê |
> |---|---|---|
> | **Mediana**, e o card diz "Tempo típico" | Média, como no design ("Tempo médio") | Um aluno que deixa a aba aberta de um dia para o outro soma 24 h. Numa turma de 30, isso puxa a média de 8 min para 56 min. A mediana nem se mexe. O teste `test_tempo_tipico_e_a_mediana` usa exatamente esse caso |
> | A taxa só conta tentativas **com** `iniciado_em` | Contar todas | As tentativas de antes desta branch não têm início registrado. Contá-las daria mais de 100% no primeiro mês |
>
> As duas métricas devolvem `None` com menos de K (5) amostras, como o resto do painel.

## 5️⃣ O filtro `duracao`

Crie `painel/templatetags/__init__.py` vazio e `painel/templatetags/painel_extras.py`:

```python
from django import template

register = template.Library()


@register.filter
def duracao(valor):
    """timedelta -> "08:42" (min:seg) ou "1h05" acima de uma hora."""
    segundos = int(valor.total_seconds())
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    if horas:
        return f"{horas}h{minutos:02d}"
    return f"{minutos:02d}:{segundos:02d}"
```

## 6️⃣ `painel/views.py` e `quiz.html`

```diff
@@ -71,6 +71,7 @@ def dashboard(request):
 @staff_member_required
 def quiz_visao_geral(request):
     inicio, contexto = _contexto_base(request, "quiz")
+    contexto["questoes_ativas"] = metricas.questoes_ativas()
     if not contexto["tem_massa"]:
         return render(request, "painel/quiz.html", contexto)
 
@@ -101,6 +102,8 @@ def quiz_visao_geral(request):
         "confianca": confianca,
         "aderencia": aderencia,
         "conversao": conversao,
+        "taxa_de_conclusao": metricas.taxa_de_conclusao(inicio),
+        "tempo_tipico": metricas.tempo_tipico(inicio),
         "orfaos": metricas.cursos_nunca_recomendados(),
         "cobertura": metricas.cobertura_de_areas(),
     })
```

No `painel/templates/painel/quiz.html`:

```diff
@@ -1,9 +1,29 @@
 {% extends "painel/base_painel.html" %}
+{% load painel_extras %}
 {% block titulo_painel %}Quiz{% endblock %}
 {% block titulo_pagina %}Quiz — Visão geral{% endblock %}
 {% block subtitulo %}Desempenho da recomendação e cobertura da engine{% endblock %}
 
 {% block painel %}
+<div class="painel-kpis">
+    <article class="painel-card painel-kpi">
+        <h2>Testes concluídos</h2>
+        <p class="painel-kpi__valor">{{ total_de_tentativas }}</p>
+    </article>
+    <article class="painel-card painel-kpi">
+        <h2>% concluídos <span class="painel-ajuda" tabindex="0" data-dica="Dos quizzes começados no período, quantos chegaram ao resultado. Testes antigos, sem início registrado, ficam de fora.">?</span></h2>
+        <p class="painel-kpi__valor">{% if taxa_de_conclusao is None %}—{% else %}{{ taxa_de_conclusao|floatformat:0 }}%{% endif %}</p>
+    </article>
+    <article class="painel-card painel-kpi">
+        <h2>Tempo típico <span class="painel-ajuda" tabindex="0" data-dica="Mediana do tempo entre abrir a 1ª questão e ver o resultado.">?</span></h2>
+        <p class="painel-kpi__valor">{% if tempo_tipico is None %}—{% else %}{{ tempo_tipico|duracao }}{% endif %}</p>
+    </article>
+    <article class="painel-card painel-kpi">
+        <h2>Questões ativas</h2>
+        <p class="painel-kpi__valor">{{ questoes_ativas }}</p>
+    </article>
+</div>
+
 {% if not tem_massa %}
 {% include "painel/_sem_massa.html" %}
 {% else %}
```

> [!note] Os KPIs aparecem mesmo sem massa
> "Testes concluídos" e "Questões ativas" não dizem nada sobre pessoas, então ficam visíveis sempre. "% concluídos" e "Tempo típico" só são calculados com massa; sem ela, o template recebe a variável ausente e mostra "—".

---

## 7️⃣ Testes: `quiz/tests/test_inicio.py` (novo)

```python
from datetime import timedelta

from django.urls import reverse

from painel import metricas
from painel.privacidade import K_MINIMO
from painel.templatetags.painel_extras import duracao
from quiz.models import InicioDeQuiz, Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class InicioDoQuizTest(BaseEducMatch):
    """DSH-03: o início do quiz é contado uma vez e vira iniciado_em na tentativa."""

    def comecar(self, nome="Visitante"):
        return self.client.get(reverse("quiz-inicio"), {"respondido_por": nome, "etapa": 1})

    def test_abrir_a_primeira_questao_conta_um_inicio(self):
        self.comecar()

        self.assertEqual(InicioDeQuiz.objects.count(), 1)

    def test_recarregar_nao_conta_de_novo(self):
        self.comecar()
        self.comecar()

        self.assertEqual(InicioDeQuiz.objects.count(), 1)

    def test_concluir_grava_o_inicio_na_tentativa_e_limpa_a_sessao(self):
        self.comecar()
        inicio = InicioDeQuiz.objects.get()

        self.responder_tudo()

        tentativa = Tentativa_de_resposta.objects.get()
        self.assertEqual(tentativa.iniciado_em, inicio.criado_em)
        self.assertNotIn("quiz_iniciado_em", self.client.session)

    def test_proximo_quiz_conta_outro_inicio(self):
        self.comecar()
        self.responder_tudo()
        self.comecar()

        self.assertEqual(InicioDeQuiz.objects.count(), 2)

    def test_post_direto_fica_sem_inicio(self):
        self.responder_tudo()

        self.assertIsNone(Tentativa_de_resposta.objects.get().iniciado_em)

    def test_inicio_nao_guarda_quem_comecou(self):
        campos = {campo.name for campo in InicioDeQuiz._meta.get_fields()}

        self.assertEqual(campos, {"id", "criado_em", "questionario_link"})


class MetricasDeConclusaoTest(BaseEducMatch):
    def concluir(self, quantidade, minutos=8):
        for _ in range(quantidade):
            tentativa = self.criar_tentativa()
            tentativa.iniciado_em = tentativa.criado_em - timedelta(minutes=minutos)
            tentativa.save(update_fields=["iniciado_em"])

    def test_taxa_de_conclusao(self):
        for _ in range(K_MINIMO * 2):
            InicioDeQuiz.objects.create()
        self.concluir(K_MINIMO)

        self.assertEqual(metricas.taxa_de_conclusao(None), 50.0)

    def test_taxa_some_com_poucos_inicios(self):
        InicioDeQuiz.objects.create()

        self.assertIsNone(metricas.taxa_de_conclusao(None))

    def test_tempo_tipico_e_a_mediana(self):
        self.concluir(K_MINIMO - 1, minutos=8)
        self.concluir(1, minutos=60 * 24)  # aba esquecida aberta por um dia

        self.assertEqual(metricas.tempo_tipico(None), timedelta(minutes=8))

    def test_tempo_some_com_poucas_tentativas(self):
        self.concluir(K_MINIMO - 1)

        self.assertIsNone(metricas.tempo_tipico(None))

    def test_formato_da_duracao(self):
        self.assertEqual(duracao(timedelta(minutes=8, seconds=42)), "08:42")
        self.assertEqual(duracao(timedelta(hours=1, minutes=5)), "1h05")
```

---

## ✅ Verificação

```bash
cd backend
python manage.py makemigrations --check --dry-run   # No changes detected (depois de criar a 0005)
python manage.py migrate
python manage.py test                                # 114 testes
python manage.py runserver
```

- [ ] Responda o quiz uma vez pela tela de introdução. No `shell`: `InicioDeQuiz.objects.count()` é 1 e a última tentativa tem `iniciado_em` preenchido
- [ ] Recarregue a 1ª questão antes de terminar: continua 1 início
- [ ] Em `/painel/quiz/`, com 5 ou mais testes novos: "% concluídos" e "Tempo típico" aparecem; com menos, "—"

## 📦 Commit e PR

```bash
git add -A
git commit -m "feat(quiz): registra o inicio do quiz para conclusao e tempo

- InicioDeQuiz sem dado pessoal: so data e link de origem
- Tentativa_de_resposta.iniciado_em, preenchido a partir da sessao
- painel: % concluidos, tempo tipico (mediana) e questoes ativas
- migracao 0005 testada com dados, na ida e na volta"
git push -u origin feature/quiz-conclusao-e-tempo
gh pr create --base develop --fill
```

> [!success] Definition of Done
> 114 testes, CI verde, migração aplicada no banco local e o checklist acima conferido. Com esta branch mesclada, a `develop` está pronta para a release `0.5.0-painel` (ver [[plano-dashboard-git-flow|🖥️ plano]]).
