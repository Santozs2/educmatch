---
title: "Spec FRM-02 — avaliações no painel: links das turmas, resultados e CSV"
aliases: ["FRM-02", "Avaliações no painel", "Resultados das avaliações"]
tags: [tcc, spec, painel, avaliacao, privacidade]
status: proposto
projeto: TCC
branch: feature/painel-avaliacoes
criado: 2026-10-01
---

> [!info] Plano: [[plano-dashboard-git-flow|🖥️ Dashboard novo e Git Flow]] · Anterior: [[spec-frm-01-avaliacao-fim-de-curso|FRM-01 — avaliação de fim de curso]]

# 📊 FRM-02: avaliações no painel

**Branch:** `feature/painel-avaliacoes`, saindo da `develop` **com a FRM-01 já mesclada**
**Risco:** baixo. Nenhuma migração.
**Testes ao final:** 137 (125 + 12 novos)

> [!abstract] O que esta branch faz
> 1. Item **Avaliações** no menu, com a tela dos links por turma: escolher curso, dar nome à turma, gerar link (com QR) e fechar.
> 2. Tela **Resultados**: tabela por curso (respostas, NPS e média), um card por pergunta e filtro por curso.
> 3. **Exportar CSV**, desenhado para não deixar remontar a resposta de ninguém.
> 4. KPI **"Avaliações de curso"** na Início (o card que a DSH-01 deixou de fora).

---

## 1️⃣ Privacidade: três regras próprias desta tela

> [!important] A massa mínima é de **avaliações**, e não de testes
> As telas da Fase 1 usam "5 testes do quiz no período". Aqui isso não serve: um mês com 200 testes pode ter um curso com 3 avaliações, e a média de 3 pessoas sobre o instrutor delas não pode aparecer. A K = 5 é contada **por curso, em respostas de avaliação**.

> [!danger] O vazamento por diferença, achado ao testar esta spec
> A primeira versão mostrava, em "Todos os cursos", os gráficos com **todas** as respostas. No teste com dados falsos, Usinagem CNC tinha 12 respostas e Costura Industrial tinha 3:
> - a tabela mostrava o NPS de Usinagem: **50**;
> - o card de "Todos" mostrava o NPS geral: **40**.
>
> Com os dois números e as contagens, dá para calcular a opinião das 3 pessoas de Costura, mesmo com a linha de Costura escondida. A correção: **curso com menos de 5 avaliações não entra em nenhuma agregação de opinião** (cards, médias, NPS, CSV), nem no "Todos". A tela avisa quantos cursos ficaram de fora. O teste `test_curso_pequeno_fica_fora_do_todos` trava isso.
>
> As **contagens** seguem a regra do resto do painel (célula suprimida, total visível). Saber que "3 pessoas de Costura responderam" não expõe opinião de ninguém.

> [!note] O CSV não deixa juntar as respostas de uma pessoa
> Uma linha por item (`curso;pergunta;resposta`), **sem turma, sem data e sem id da resposta**, ordenada por pergunta e valor. As 7 respostas de um mesmo aluno ficam espalhadas por 7 blocos diferentes, e nada liga uma à outra. O teste `test_csv_sai_sem_turma_data_e_em_ordem` confere que cada pergunta forma um bloco só.

## 2️⃣ `painel/metricas_avaliacao.py` (novo)

```python
"""Agregações da avaliação de fim de curso. Mesma regra do metricas.py:
funções puras, sem request, e nenhuma volta uma resposta inteira de alguém.
"""
from collections import Counter

from django.db.models import Count, Q
from django.utils import timezone

from avaliacao.models import ItemDeResposta, LinkDeAvaliacao, Pergunta, RespostaDeAvaliacao


def _desde(inicio, prefixo="respondido_em"):
    # A resposta guarda só o dia: compara com o dia do início do período.
    if inicio is None:
        return Q()
    return Q(**{f"{prefixo}__gte": timezone.localdate(inicio)})


def respostas(inicio, cursos=None):
    """As respostas do período; `cursos` (lista de ids) restringe, None não restringe."""
    filtro = _desde(inicio)
    if cursos is not None:
        filtro &= Q(link__curso_id__in=cursos)
    return RespostaDeAvaliacao.objects.filter(filtro)


def cursos_com_massa(inicio, k):
    """Ids dos cursos com k respostas ou mais no período.

    Só eles entram nas agregações de opinião. Se um curso com 3 respostas
    entrasse no "Todos os cursos", a diferença entre o NPS geral e o NPS dos
    outros cursos (que a tabela mostra) devolveria a opinião daquelas 3 pessoas.
    """
    return list(
        RespostaDeAvaliacao.objects.filter(_desde(inicio))
        .values("link__curso_id")
        .annotate(total=Count("id"))
        .filter(total__gte=k)
        .values_list("link__curso_id", flat=True)
    )


def links(limite=30):
    return list(
        LinkDeAvaliacao.objects
        .annotate(total=Count("respostas"))
        .values("id", "token", "turma", "criado_em", "ativo", "total", "curso__nome_curso")
        .order_by("-criado_em")[:limite]
    )


def nps(notas):
    """% de promotores (9 e 10) menos % de detratores (0 a 6). Vai de -100 a 100."""
    if not notas:
        return None
    promotores = sum(1 for nota in notas if nota >= 9)
    detratores = sum(1 for nota in notas if nota <= 6)
    return round((promotores - detratores) / len(notas) * 100)


def resumo_por_curso(inicio):
    """Por curso avaliado: quantas respostas, NPS e média das escalas."""
    linhas = (
        RespostaDeAvaliacao.objects
        .filter(_desde(inicio))
        .values("link__curso_id", "link__curso__nome_curso")
        .annotate(total=Count("id"))
        .order_by("link__curso__nome_curso")
    )
    itens = ItemDeResposta.objects.filter(_desde(inicio, "resposta__respondido_em"))
    notas, escalas = {}, {}
    for curso_id, tipo, numero in itens.values_list("resposta__link__curso_id", "pergunta__tipo", "numero"):
        if tipo == "nps":
            notas.setdefault(curso_id, []).append(numero)
        elif tipo == "escala":
            escalas.setdefault(curso_id, []).append(numero)

    resultado = []
    for linha in linhas:
        curso_id = linha["link__curso_id"]
        valores = escalas.get(curso_id, [])
        resultado.append({
            "curso_id": curso_id,
            "nome": linha["link__curso__nome_curso"],
            "total": linha["total"],
            "nps": nps(notas.get(curso_id, [])),
            "media": sum(valores) / len(valores) if valores else None,
        })
    return resultado


def por_pergunta(inicio, cursos):
    """Para cada pergunta ativa, o resumo que cabe ao tipo dela, só dos `cursos` dados."""
    filtro = _desde(inicio, "resposta__respondido_em") & Q(resposta__link__curso_id__in=cursos)

    resultado = []
    for pergunta in Pergunta.objects.filter(ativa=True):
        itens = ItemDeResposta.objects.filter(filtro, pergunta=pergunta)
        bloco = {"pergunta": pergunta, "total": itens.count()}

        if pergunta.tipo in ("nps", "escala"):
            numeros = list(itens.values_list("numero", flat=True))
            contagem = Counter(numeros)
            faixa = range(11) if pergunta.tipo == "nps" else range(1, 6)
            bloco["distribuicao"] = [{"rotulo": n, "total": contagem.get(n, 0)} for n in faixa]
            bloco["nps"] = nps(numeros) if pergunta.tipo == "nps" else None
            bloco["media"] = sum(numeros) / len(numeros) if numeros else None
        elif pergunta.tipo == "escolha":
            contagem = Counter(itens.values_list("texto", flat=True))
            bloco["distribuicao"] = [{"rotulo": opcao, "total": contagem.get(opcao, 0)} for opcao in pergunta.opcoes]
        else:
            # Ordem alfabética: na ordem de chegada, o 1º texto seria o de quem respondeu primeiro.
            bloco["textos"] = sorted(t for t in itens.values_list("texto", flat=True) if t)
        resultado.append(bloco)
    return resultado


def linhas_do_csv(inicio, cursos):
    """Uma linha por item (curso, pergunta, resposta), ordenadas por pergunta e valor.

    Sem turma, sem data e sem id da resposta: as linhas de uma mesma pessoa não
    podem ser juntadas de volta numa resposta completa.
    """
    filtro = _desde(inicio, "resposta__respondido_em") & Q(resposta__link__curso_id__in=cursos)
    linhas = sorted(
        ItemDeResposta.objects.filter(filtro)
        .values_list("resposta__link__curso__nome_curso", "pergunta__ordem", "numero", "texto", "pergunta__texto"),
        key=lambda linha: (linha[0], linha[1], linha[2] if linha[2] is not None else -1, linha[3]),
    )
    return [
        (curso, pergunta, str(numero) if numero is not None else texto)
        for curso, _, numero, texto, pergunta in linhas
    ]
```

> [!tip] Comentários em ordem alfabética
> Na ordem de chegada, o primeiro comentário seria o de quem respondeu primeiro, e numa turma todo mundo sabe quem saiu da aula antes. A ordem alfabética não diz nada.

## 3️⃣ `painel/forms.py` (novo)

```python
from django import forms

from avaliacao.models import LinkDeAvaliacao
from catalogo.models import Curso


class NovoLinkDeAvaliacao(forms.ModelForm):
    class Meta:
        model = LinkDeAvaliacao
        fields = ["curso", "turma"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curso"].queryset = Curso.objects.filter(is_active=True).order_by("nome_curso")
        self.fields["curso"].empty_label = "Escolha o curso"
        self.fields["turma"].widget.attrs["placeholder"] = "Ex.: 2026/1 · Noite"
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "painel-campo"
```

## 4️⃣ `painel/views.py` e `painel/urls.py`

```diff
@@ -1,11 +1,17 @@
+import csv
 from urllib.parse import urlencode
 
+from django.contrib import messages
 from django.contrib.admin.views.decorators import staff_member_required
+from django.http import HttpResponse
 from django.shortcuts import get_object_or_404, redirect, render
 from django.urls import reverse
 from django.views.decorators.http import require_POST
 
-from painel import metricas, privacidade
+from avaliacao.models import LinkDeAvaliacao
+from catalogo.models import Curso
+from painel import metricas, metricas_avaliacao, privacidade
+from painel.forms import NovoLinkDeAvaliacao
 from quiz.models import QuestionarioLink, Tentativa_de_resposta
 
 
@@ -53,6 +59,7 @@ def dashboard(request):
     inicio, contexto = _contexto_base(request, "inicio")
     contexto["links"] = _links_ativos(request)
     contexto["cursos_ativos"] = metricas.cursos_ativos()
+    contexto["avaliacoes_no_periodo"] = metricas_avaliacao.respostas(inicio).count()
     if not contexto["tem_massa"]:
         # Período pequeno: nenhum número além do total sai do servidor.
         return render(request, "painel/inicio.html", contexto)
@@ -190,3 +197,99 @@ def fechar_link(request):
 def gerar_link(request):
     QuestionarioLink.objects.create(criado_por=request.user)
     return _voltar(request)
+
+
+# ---------- Avaliação de fim de curso (FRM-02) ----------
+# A massa mínima aqui é de RESPOSTAS DE AVALIAÇÃO, e não de testes do quiz:
+# um curso com 3 avaliações não pode mostrar média, mesmo num mês de 200 testes.
+
+
+@staff_member_required
+def avaliacoes(request):
+    _, contexto = _contexto_base(request, "avaliacoes")
+    linhas = privacidade.suprimir_pequenos(metricas_avaliacao.links())
+    for linha in linhas:
+        linha["url"] = request.build_absolute_uri(
+            reverse("avaliacao-responder", kwargs={"token": linha["token"]})
+        )
+    contexto.update({"links": linhas, "form": NovoLinkDeAvaliacao()})
+    return render(request, "painel/avaliacoes.html", contexto)
+
+
+@require_POST
+@staff_member_required
+def gerar_link_avaliacao(request):
+    form = NovoLinkDeAvaliacao(request.POST)
+    if form.is_valid():
+        link = form.save(commit=False)
+        link.criado_por = request.user
+        link.save()
+        messages.success(request, f"Link criado para {link.curso.nome_curso} · {link.turma}.")
+    else:
+        messages.error(request, "Escolha um curso ativo e dê um nome à turma.")
+    return redirect("painel-avaliacoes")
+
+
+@require_POST
+@staff_member_required
+def fechar_link_avaliacao(request, pk):
+    link = get_object_or_404(LinkDeAvaliacao, pk=pk)
+    link.ativo = False
+    link.save(update_fields=["ativo"])
+    return redirect("painel-avaliacoes")
+
+
+def _cursos_do_filtro(request, inicio):
+    """(curso escolhido ou None, ids que podem entrar nas agregações de opinião)."""
+    com_massa = metricas_avaliacao.cursos_com_massa(inicio, privacidade.K_MINIMO)
+    curso_id = request.GET.get("curso")
+    curso = Curso.objects.filter(pk=curso_id).first() if curso_id and curso_id.isdigit() else None
+    if curso is None:
+        return None, com_massa
+    return curso, [curso.id] if curso.id in com_massa else []
+
+
+@staff_member_required
+def avaliacoes_resultados(request):
+    inicio, contexto = _contexto_base(request, "avaliacoes")
+    curso, cursos = _cursos_do_filtro(request, inicio)
+
+    resumo = metricas_avaliacao.resumo_por_curso(inicio)
+    for linha in resumo:
+        if linha["total"] < privacidade.K_MINIMO:
+            linha.update(total=None, suprimido=True, nps=None, media=None)
+
+    contexto.update({
+        "curso": curso,
+        "avaliacoes_com_massa": bool(cursos),
+        "resumo": resumo,
+        "cursos_avaliados": Curso.objects.filter(links_de_avaliacao__isnull=False).distinct().order_by("nome_curso"),
+    })
+    if cursos:
+        blocos = metricas_avaliacao.por_pergunta(inicio, cursos)
+        for bloco in blocos:
+            if "distribuicao" in bloco:
+                bloco["distribuicao"] = privacidade.suprimir_pequenos(bloco["distribuicao"])
+                maior = max((d["total"] or 0 for d in bloco["distribuicao"]), default=0)
+                for item in bloco["distribuicao"]:
+                    item["largura"] = round((item["total"] or 0) / maior * 100) if maior else 0
+        contexto["blocos"] = blocos
+        contexto["fora_do_todos"] = len(resumo) - len(cursos) if curso is None else 0
+    return render(request, "painel/avaliacoes_resultados.html", contexto)
+
+
+@staff_member_required
+def avaliacoes_csv(request):
+    inicio, _ = _contexto_base(request, "avaliacoes")
+    _, cursos = _cursos_do_filtro(request, inicio)
+    if not cursos:
+        messages.error(request, f"O CSV só sai para cursos com {privacidade.K_MINIMO} avaliações ou mais.")
+        return redirect("painel-avaliacoes-resultados")
+
+    resposta = HttpResponse(content_type="text/csv; charset=utf-8")
+    resposta["Content-Disposition"] = 'attachment; filename="avaliacoes.csv"'
+    resposta.write("\ufeff")  # BOM: o Excel abre os acentos certos
+    escritor = csv.writer(resposta, delimiter=";")
+    escritor.writerow(["curso", "pergunta", "resposta"])
+    escritor.writerows(metricas_avaliacao.linhas_do_csv(inicio, cursos))
+    return resposta
```

```diff
@@ -10,4 +10,9 @@ urlpatterns = [
     path("gerar-link/", views.gerar_link, name="painel-gerar-link"),
     path("fechar-link/", views.fechar_link, name="painel-fechar-link"),
     path("links/<int:pk>/fechar/", views.fechar_um_link, name="painel-fechar-um-link"),
+    path("avaliacoes/", views.avaliacoes, name="painel-avaliacoes"),
+    path("avaliacoes/gerar/", views.gerar_link_avaliacao, name="painel-avaliacoes-gerar"),
+    path("avaliacoes/<int:pk>/fechar/", views.fechar_link_avaliacao, name="painel-avaliacoes-fechar"),
+    path("avaliacoes/resultados/", views.avaliacoes_resultados, name="painel-avaliacoes-resultados"),
+    path("avaliacoes/resultados.csv", views.avaliacoes_csv, name="painel-avaliacoes-csv"),
 ]
```

## 5️⃣ Mensagens dentro do painel

As views usam `messages` ("Link criado para…"). O `base.html` as mostra acima do conteúdo, o que no painel cai atrás do menu fixo. O `base.html` ganha um bloco em volta delas:

```diff
@@ -52,6 +52,7 @@
     {% endblock %}
 
     <main class="conteudo" id="conteudo">
+        {% block mensagens %}
         {% if messages %}
         <ul class="mensagens" role="status">
             {% for mensagem in messages %}
@@ -59,6 +60,7 @@
             {% endfor %}
         </ul>
         {% endif %}
+        {% endblock %}
 
         {% block content %}{% endblock %}
     </main>
```

E o `base_painel.html` esvazia esse bloco, mostra as mensagens dentro da área de conteúdo e ganha o item do menu:

```diff
@@ -5,6 +5,7 @@
 {% block estilos %}<link rel="stylesheet" href="{% static 'css/painel.css' %}">{% endblock %}
 {% block topo %}{% endblock %}
 {% block rodape %}{% endblock %}
+{% block mensagens %}{% endblock %}
 
 {% block content %}
 <div class="painel-app">
@@ -19,6 +20,9 @@
             <a class="painel-menu__item" href="{% url 'painel-quiz' %}?{{ periodo_qs }}" {% if secao == "quiz" %}aria-current="page"{% endif %}>
                 <i class="fa-solid fa-circle-question" aria-hidden="true"></i> Quiz
             </a>
+            <a class="painel-menu__item" href="{% url 'painel-avaliacoes' %}?{{ periodo_qs }}" {% if secao == "avaliacoes" %}aria-current="page"{% endif %}>
+                <i class="fa-solid fa-clipboard-check" aria-hidden="true"></i> Avaliações
+            </a>
             <a class="painel-menu__item" href="{% url 'painel-cursos' %}?{{ periodo_qs }}" {% if secao == "cursos" %}aria-current="page"{% endif %}>
                 <i class="fa-solid fa-graduation-cap" aria-hidden="true"></i> Cursos e Áreas
             </a>
@@ -81,6 +85,14 @@
                 <div class="painel-cabecalho__acoes">{% block acoes %}{% endblock %}</div>
             </header>
 
+            {% if messages %}
+            <ul class="mensagens" role="status">
+                {% for mensagem in messages %}
+                <li class="mensagem mensagem--{{ mensagem.tags }}">{{ mensagem }}</li>
+                {% endfor %}
+            </ul>
+            {% endif %}
+
             {% block painel %}{% endblock %}
         </div>
     </div>
```

O KPI na `inicio.html`, antes do de Conversão:

```diff
@@ -18,6 +18,10 @@
         <h2>Cursos ativos</h2>
         <p class="painel-kpi__valor">{{ cursos_ativos }}</p>
     </article>
+    <article class="painel-card painel-kpi">
+        <h2>Avaliações de curso</h2>
+        <p class="painel-kpi__valor">{{ avaliacoes_no_periodo }}</p>
+    </article>
     <article class="painel-card painel-kpi">
         <h2>Conversão <span class="painel-ajuda" tabindex="0" data-dica="Cursos salvos na lista de interesse ÷ cursos recomendados no período.">?</span></h2>
         <p class="painel-kpi__valor">{% if conversao_geral is None %}—{% else %}{{ conversao_geral|floatformat:0 }}%{% endif %}</p>
```

## 6️⃣ Templates novos

### `painel/templates/painel/avaliacoes.html`

```html
{% extends "painel/base_painel.html" %}
{% block titulo_painel %}Avaliações{% endblock %}
{% block titulo_pagina %}Avaliações de fim de curso{% endblock %}
{% block subtitulo %}Um link por turma, respostas anônimas{% endblock %}
{% block acoes %}
<a class="botao botao--secundario" href="{% url 'painel-avaliacoes-resultados' %}?{{ periodo_qs }}"><i class="fa-solid fa-chart-column" aria-hidden="true"></i> Ver resultados</a>
{% endblock %}

{% block painel %}
<article class="painel-card painel-card--destaque painel-grade">
    <h2 class="painel-card__titulo">Novo link para uma turma</h2>
    <form class="painel-form-linha" method="post" action="{% url 'painel-avaliacoes-gerar' %}" data-confirmar="Criar um link de avaliação para esta turma?">
        {% csrf_token %}
        <label class="visualmente-oculto" for="{{ form.curso.id_for_label }}">Curso</label>
        {{ form.curso }}
        <label class="visualmente-oculto" for="{{ form.turma.id_for_label }}">Turma</label>
        {{ form.turma }}
        <button type="submit" class="botao"><i class="fa-solid fa-plus" aria-hidden="true"></i> Gerar link</button>
    </form>
</article>

<article class="painel-card">
    <div class="painel-tabela">
        <table>
            <thead>
                <tr>
                    <th scope="col">QR code</th>
                    <th scope="col">Curso e turma</th>
                    <th scope="col">Endereço</th>
                    <th scope="col" class="numero">Respostas</th>
                    <th scope="col">Status</th>
                    <th scope="col"><span class="visualmente-oculto">Ações</span></th>
                </tr>
            </thead>
            <tbody>
                {% for link in links %}
                <tr>
                    <td>{% if link.ativo %}<div class="painel-qr" data-qr="{{ link.url }}" role="img" aria-label="QR code do link"></div>{% else %}—{% endif %}</td>
                    <td><b>{{ link.curso__nome_curso }}</b><br><span class="painel-vazio">{{ link.turma }}</span></td>
                    <td>
                        <div class="painel-link">
                            <input class="painel-link__url" type="text" value="{{ link.url }}" readonly aria-label="Endereço do link">
                            {% if link.ativo %}<button type="button" class="botao botao--secundario" data-copiar><i class="fa-solid fa-copy" aria-hidden="true"></i> Copiar</button>{% endif %}
                        </div>
                    </td>
                    <td class="numero">{% include "painel/_celula.html" with valor=link.total suprimido=link.suprimido %}</td>
                    <td>{% if link.ativo %}<span class="painel-selo painel-selo--sucesso">Ativo</span>{% else %}<span class="painel-selo painel-selo--neutro">Fechado</span>{% endif %}</td>
                    <td>
                        {% if link.ativo %}
                        <form method="post" action="{% url 'painel-avaliacoes-fechar' link.id %}" data-confirmar="Fechar este link? A turma não consegue mais responder." data-perigo>
                            {% csrf_token %}
                            <button type="submit" class="botao botao--perigo"><i class="fa-solid fa-ban" aria-hidden="true"></i> Fechar</button>
                        </form>
                        {% endif %}
                    </td>
                </tr>
                {% empty %}
                <tr><td colspan="6">Nenhum link ainda. Crie o primeiro acima quando uma turma estiver terminando o curso.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</article>
{% endblock %}

{% block scripts_painel %}
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js" defer></script>
{% endblock %}
```

### `painel/templates/painel/avaliacoes_resultados.html`

```html
{% extends "painel/base_painel.html" %}
{% block titulo_painel %}Resultados das avaliações{% endblock %}
{% block titulo_pagina %}Resultados das avaliações{% endblock %}
{% block subtitulo %}{% if curso %}{{ curso.nome_curso }}{% else %}Todos os cursos{% endif %}{% endblock %}
{% block acoes %}
<a class="botao botao--secundario" href="{% url 'painel-avaliacoes' %}?{{ periodo_qs }}"><i class="fa-solid fa-link" aria-hidden="true"></i> Links das turmas</a>
{% if avaliacoes_com_massa %}
<a class="botao" href="{% url 'painel-avaliacoes-csv' %}?{{ periodo_qs }}{% if curso %}&amp;curso={{ curso.id }}{% endif %}"><i class="fa-solid fa-file-csv" aria-hidden="true"></i> Exportar CSV</a>
{% endif %}
{% endblock %}

{% block painel %}
<form class="painel-form-linha painel-grade" method="get">
    <input type="hidden" name="periodo" value="{{ periodo }}">
    {% if mes %}<input type="hidden" name="mes" value="{{ mes }}">{% endif %}
    <label class="visualmente-oculto" for="curso">Curso</label>
    <select id="curso" name="curso" class="painel-campo">
        <option value="">Todos os cursos</option>
        {% for opcao in cursos_avaliados %}
        <option value="{{ opcao.id }}" {% if curso and curso.id == opcao.id %}selected{% endif %}>{{ opcao.nome_curso }}</option>
        {% endfor %}
    </select>
    <button type="submit" class="botao">Filtrar</button>
</form>

<article class="painel-card painel-grade">
    <h2 class="painel-card__titulo">Por curso <span class="painel-ajuda" tabindex="0" data-dica="NPS: % de notas 9 e 10 menos % de notas 0 a 6. Vai de -100 a 100. Média: das perguntas de 1 a 5.">?</span></h2>
    <div class="painel-tabela">
        <table>
            <thead><tr><th scope="col">Curso</th><th scope="col" class="numero">Respostas</th><th scope="col" class="numero">NPS</th><th scope="col" class="numero">Média (1 a 5)</th></tr></thead>
            <tbody>
                {% for linha in resumo %}
                <tr>
                    <td>{{ linha.nome }}</td>
                    <td class="numero">{% include "painel/_celula.html" with valor=linha.total suprimido=linha.suprimido %}</td>
                    <td class="numero">{% if linha.nps is None %}—{% else %}{{ linha.nps }}{% endif %}</td>
                    <td class="numero">{% if linha.media is None %}—{% else %}{{ linha.media|floatformat:1 }}{% endif %}</td>
                </tr>
                {% empty %}<tr><td colspan="4">Nenhuma avaliação no período.</td></tr>{% endfor %}
            </tbody>
        </table>
    </div>
</article>

{% if not avaliacoes_com_massa %}
<div class="painel-aviso" role="status">
    <i class="fa-solid fa-lock" aria-hidden="true"></i>
    <p><strong>Privacidade:</strong> as respostas por pergunta só aparecem para cursos com {{ k_minimo }} avaliações ou mais no período.</p>
</div>
{% else %}
{% if fora_do_todos %}
<p class="painel-vazio"><i class="fa-solid fa-lock" aria-hidden="true"></i> {{ fora_do_todos }} curso(s) com menos de {{ k_minimo }} avaliações ficaram fora dos gráficos abaixo.</p>
{% endif %}
<div class="painel-grade painel-grade--2">
    {% for bloco in blocos %}
    <article class="painel-card">
        <h2 class="painel-card__titulo">{{ bloco.pergunta.ordem }}. {{ bloco.pergunta.texto }}</h2>
        {% if bloco.pergunta.tipo == "nps" %}
        <p class="painel-kpi__valor">NPS {% if bloco.nps is None %}—{% else %}{{ bloco.nps }}{% endif %}</p>
        {% elif bloco.pergunta.tipo == "escala" %}
        <p class="painel-kpi__valor">{% if bloco.media is None %}—{% else %}{{ bloco.media|floatformat:1 }}{% endif %} <small class="painel-vazio">de 5</small></p>
        {% endif %}

        {% if bloco.distribuicao %}
        <ul class="painel-distribuicao">
            {% for item in bloco.distribuicao %}
            <li>
                <span>{{ item.rotulo }}</span>
                <div class="painel-progresso" aria-hidden="true"><i style="width: {{ item.largura }}%"></i></div>
                <b>{% include "painel/_celula.html" with valor=item.total suprimido=item.suprimido %}</b>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p class="painel-vazio">{{ bloco.textos|length }} comentário(s), em ordem alfabética, sem data nem turma.</p>
        <ul class="painel-comentarios">
            {% for texto in bloco.textos %}<li>{{ texto }}</li>{% empty %}<li class="painel-vazio">Nenhum comentário.</li>{% endfor %}
        </ul>
        {% endif %}
    </article>
    {% endfor %}
</div>
{% endif %}
{% endblock %}
```

> [!note] Barras em CSS, sem Chart.js
> Os cards por pergunta usam a mesma `painel-progresso` da tela Quiz. São até 11 barras por card e 7 cards, e Chart.js para isso seria peso sem ganho. A largura de cada barra é calculada **depois** da supressão: uma barra escondida tem largura zero e não entrega pelo tamanho o número que o cadeado esconde.

## 7️⃣ `static/css/painel.css`

Antes do bloco `/* Modal de confirmação */`:

```css
/* Avaliações de fim de curso */

.painel-form-linha {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.painel-form-linha .painel-campo {
  flex: 1 1 220px;
}

.painel-distribuicao {
  display: grid;
  gap: 8px;
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
  font-size: 0.85rem;
}

.painel-distribuicao li {
  display: grid;
  grid-template-columns: minmax(48px, 120px) 1fr 56px;
  align-items: center;
  gap: 10px;
}

.painel-distribuicao b {
  text-align: right;
}

.painel-comentarios {
  display: grid;
  gap: 8px;
  max-height: 320px;
  margin: 8px 0 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
}

.painel-comentarios li {
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--fundo);
  font-size: 0.9rem;
}
```

---

## 8️⃣ Testes: `painel/tests/test_avaliacoes.py` (novo)

```python
from django.urls import reverse

from avaliacao.models import LinkDeAvaliacao, RespostaDeAvaliacao
from avaliacao.tests.base import BaseAvaliacao
from catalogo.models import Curso
from painel import metricas_avaliacao
from painel.privacidade import K_MINIMO
from painel.tests.test_telas import BOTOES_FANTASMA


class AvaliacoesNoPainelTest(BaseAvaliacao):
    """FRM-02: links por turma, resultados agregados e CSV, sempre com k = 5."""

    def setUp(self):
        super().setUp()
        self.staff = self.criar_usuario("coord@exemplo.com", is_staff=True)
        self.client.force_login(self.staff)
        self.curso = Curso.objects.filter(is_active=True).first()

    def responder(self, link, quantidade, **valores):
        """Cada resposta num navegador novo: a trava de sessão não deixa repetir no mesmo."""
        for _ in range(quantidade):
            self.client.logout()
            self.enviar(link, self.respostas_validas(**valores))
        self.client.force_login(self.staff)

    def test_so_staff_entra(self):
        comum = self.criar_usuario("aluno@exemplo.com")
        for tela in ("painel-avaliacoes", "painel-avaliacoes-resultados", "painel-avaliacoes-csv"):
            with self.subTest(tela=tela):
                self.client.force_login(comum)
                self.assertNotEqual(self.client.get(reverse(tela)).status_code, 200)

    def test_gerar_link_para_turma(self):
        resposta = self.client.post(
            reverse("painel-avaliacoes-gerar"), {"curso": self.curso.id, "turma": "2026/1 · Noite"}
        )

        self.assertRedirects(resposta, reverse("painel-avaliacoes"))
        link = LinkDeAvaliacao.objects.get()
        self.assertEqual((link.curso, link.turma, link.criado_por), (self.curso, "2026/1 · Noite", self.staff))

    def test_curso_inativo_nao_ganha_link(self):
        inativo = Curso.objects.create(
            nome_curso="Antigo", descricao="-", area_principal=self.curso.area_principal, duracao=10, is_active=False
        )

        self.client.post(reverse("painel-avaliacoes-gerar"), {"curso": inativo.id, "turma": "X"})

        self.assertFalse(LinkDeAvaliacao.objects.exists())

    def test_fechar_link_de_avaliacao(self):
        link = self.criar_link(self.curso)

        self.client.post(reverse("painel-avaliacoes-fechar", args=[link.pk]))

        link.refresh_from_db()
        self.assertFalse(link.ativo)

    def test_poucas_respostas_nao_mostram_perguntas(self):
        self.responder(self.criar_link(self.curso), K_MINIMO - 1)

        contexto = self.client.get(reverse("painel-avaliacoes-resultados")).context

        self.assertFalse(contexto["avaliacoes_com_massa"])
        self.assertNotIn("blocos", contexto)
        linha = next(l for l in contexto["resumo"] if l["curso_id"] == self.curso.id)
        self.assertIsNone(linha["nps"])
        self.assertIsNone(linha["media"])

    def test_resultados_com_massa(self):
        link = self.criar_link(self.curso)
        self.responder(link, K_MINIMO, nota=10, escala=4, texto="Mais prática")

        contexto = self.client.get(reverse("painel-avaliacoes-resultados"), {"curso": self.curso.id}).context

        blocos = {bloco["pergunta"].tipo: bloco for bloco in contexto["blocos"]}
        self.assertEqual(blocos["nps"]["nps"], 100)
        self.assertEqual(blocos["escala"]["media"], 4)
        self.assertEqual(blocos["texto"]["textos"], ["Mais prática"] * K_MINIMO)
        opcoes = {item["rotulo"]: item for item in blocos["escolha"]["distribuicao"]}
        self.assertEqual(opcoes["Sim"]["total"], K_MINIMO)
        self.assertTrue(opcoes["Não"]["suprimido"], "zero também é menos que K")

    def test_curso_pequeno_fica_fora_do_todos(self):
        """Sem isso, NPS geral - NPS do curso grande devolveria a opinião do curso pequeno."""
        outro = Curso.objects.filter(is_active=True).exclude(pk=self.curso.pk).first()
        self.responder(self.criar_link(self.curso), K_MINIMO, nota=10)
        self.responder(self.criar_link(outro), 2, nota=0)

        contexto = self.client.get(reverse("painel-avaliacoes-resultados")).context

        nps = next(bloco for bloco in contexto["blocos"] if bloco["pergunta"].tipo == "nps")
        self.assertEqual(nps["nps"], 100)
        self.assertEqual(contexto["fora_do_todos"], 1)

    def test_nps_conta_promotores_menos_detratores(self):
        self.assertEqual(metricas_avaliacao.nps([10, 9, 8, 6]), 25)
        self.assertIsNone(metricas_avaliacao.nps([]))

    def test_csv_sai_sem_turma_data_e_em_ordem(self):
        self.responder(self.criar_link(self.curso, turma="Turma Secreta"), K_MINIMO)

        resposta = self.client.get(reverse("painel-avaliacoes-csv"))

        corpo = resposta.content.decode("utf-8-sig")
        linhas = corpo.strip().splitlines()
        self.assertEqual(linhas[0], "curso;pergunta;resposta")
        self.assertEqual(len(linhas) - 1, K_MINIMO * 6, "6 itens por resposta (o texto ficou em branco)")
        self.assertNotIn("Turma Secreta", corpo)
        # Cada pergunta num bloco só: nada na ordem liga um item ao seu vizinho de resposta.
        perguntas = [linha.split(";")[1] for linha in linhas[1:]]
        blocos = [p for i, p in enumerate(perguntas) if i == 0 or p != perguntas[i - 1]]
        self.assertEqual(len(blocos), len(set(perguntas)))

    def test_csv_com_poucas_respostas_e_negado(self):
        self.responder(self.criar_link(self.curso), K_MINIMO - 1)

        resposta = self.client.get(reverse("painel-avaliacoes-csv"))

        self.assertRedirects(resposta, reverse("painel-avaliacoes-resultados"))

    def test_kpi_na_inicio(self):
        self.responder(self.criar_link(self.curso), 2)

        contexto = self.client.get(reverse("painel-dashboard")).context

        self.assertEqual(contexto["avaliacoes_no_periodo"], 2)
        self.assertEqual(RespostaDeAvaliacao.objects.count(), 2)

    def test_telas_novas_sem_botao_fantasma(self):
        self.responder(self.criar_link(self.curso), K_MINIMO)
        for tela in ("painel-avaliacoes", "painel-avaliacoes-resultados"):
            corpo = self.client.get(reverse(tela)).content.decode()
            for classe in BOTOES_FANTASMA:
                with self.subTest(tela=tela, classe=classe):
                    self.assertNotIn(classe, corpo)
```

---

## ✅ Verificação

```bash
cd backend
python manage.py test                                # 137 testes
python manage.py makemigrations --check --dry-run   # No changes detected
python manage.py runserver
```

- [ ] **Avaliações**: gerar um link (curso + turma) pede confirmação, mostra a mensagem de sucesso dentro do painel e o link aparece com QR
- [ ] Responda pelo link em **5 navegadores ou janelas anônimas** diferentes (a trava de sessão impede repetir no mesmo)
- [ ] **Resultados**: com 4 respostas, só a tabela por curso aparece, com cadeado; com 5, os cards por pergunta aparecem
- [ ] Um segundo curso com 1 ou 2 respostas: em "Todos", o aviso "1 curso(s) … ficaram fora" aparece e os números dos cards não mudam
- [ ] **Exportar CSV** abre no Excel com acentos certos, sem turma e sem data
- [ ] A Início mostra o KPI "Avaliações de curso"

## 📦 Commit e PR

```bash
git add -A
git commit -m "feat(painel): avaliacoes de fim de curso no painel

- links por turma com QR, gerar e fechar
- resultados por curso e por pergunta, NPS e media, com k=5 por curso
- curso com menos de 5 avaliacoes fica fora de toda agregacao de opiniao
- CSV por item, sem turma, data ou id: nao remonta a resposta de ninguem
- KPI de avaliacoes na Inicio e mensagens dentro do painel"
git push -u origin feature/painel-avaliacoes
gh pr create --base develop --fill
```

> [!success] Definition of Done
> 137 testes, CI verde e o checklist acima conferido. Com esta branch mesclada, a Fase 2 está completa e a `develop` está pronta para a release `0.6.0-avaliacoes` (ver [[plano-dashboard-git-flow|🖥️ plano]]).
