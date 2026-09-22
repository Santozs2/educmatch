---
title: "Spec — Pessoa C · Painel (PR-4 painel com privacidade · PR-5 métricas do C4)"
aliases: ["Spec pessoa C", "Spec painel", "PR-4 painel", "PR-5 métricas", "Passo a passo do painel"]
tags: [tcc, painel, django, templates, metricas, privacidade, spec, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Mapa: [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] · Origem: [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 PNL-01 a PNL-05]] · [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel]] · Colegas: [[Projetos/EducMatch(Secretária)/spec-pessoa-a-infra|🧱 A]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-b-dados-motor|🧮 B]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-d-telas|🎨 D]]

# 📊 Spec — Pessoa C · Painel

> [!abstract] O que esta nota é
> O **como** da frente do painel, arquivo por arquivo. Missão em uma frase: entregar **um painel só**, em `/painel/`, que mostra à coordenação o que o catálogo e a demanda estão dizendo, **sem nunca deixar identificar uma pessoa**.
> Escrita contra o commit `a04c8e9`.

> [!success] O que já foi verificado (2026-09-22)
> Todo o código desta nota foi aplicado numa **cópia** do repositório, no MySQL local, junto com as specs A, B e D:
> - os **18 testes** do painel desta nota passam (6 de métrica, 12 de acesso e privacidade), inclusive os que renderizam o template com dado de verdade;
> - `/quiz/dashboard/` redireciona para `/painel/`;
> - a suíte inteira, com as quatro specs aplicadas, fecha em **59 testes, 58 verdes**. O único vermelho é o do fuso, que fica verde quando as tabelas de fuso são carregadas.

## 🧭 O mapa

| Tarefa | O que faz | Arquivo | PR |
|---|---|---|---|
| **C-1** | montar `/painel/` | `core/urls.py` | PR-4 |
| **C-2** | a base de testes que faltava | `painel/tests/base.py` | PR-4 |
| **C-3** | as métricas que não rodam | `painel/metricas.py` | PR-4 (4 funções) e PR-5 (3 funções) |
| **C-4** | privacidade completa + gerador de link | `painel/views.py` e `urls.py` | PR-4 |
| **C-5** | a tela | `painel/templates/painel/` e `static/css/painel.css` | PR-4 |
| **C-6** | aposentar o dashboard antigo | `quiz/web_urls.py`, `quiz/views.py` | PR-4 |
| **C-7** | os testes | `painel/tests/` | PR-4 e PR-5 |

## 1️⃣ O estado de hoje

Existem **dois dashboards**, e nenhum está certo:

| | `/quiz/dashboard/` (no ar) | App `painel/` (planejado) |
|---|---|---|
| Código | `dashboard_view` em `quiz/views.py` | `painel/metricas.py`, `privacidade.py`, `views.py` |
| Funciona? | Sim | **Não**: a URL não está montada e o template `painel/dashboard.html` não existe |
| Privacidade | **Nenhuma** | k-anonimato pronto em `privacidade.py` |
| Gera link de questionário | Sim | Não |

Os testes do painel também não rodam: chamam métodos que nunca foram escritos (`criar_curso_com`, `criar_tentativas`…). **O seu trabalho é juntar os dois**: o `painel/` vira o único painel, com a privacidade dele e o gerador de link do antigo.

## 2️⃣ As regras de privacidade

> [!important] A frase que decide cada tela
> O painel responde perguntas sobre **cursos e demanda**, nunca sobre **pessoas**. Se um número, somado a qualquer contexto de fora ("o único aluno do turno da noite"), identifica alguém, ele não aparece.

| Regra | Onde aparece no código |
|---|---|
| Nenhuma consulta usa `user` nem `respondido_por` | `metricas.py`: nenhuma função recebe usuário |
| Nenhum número é clicável | template: zero `<a>` em número |
| **k = 5**: célula com menos de 5 mostra `—` | `privacidade.suprimir_pequenos` (já existe) |
| Período com menos de 5 testes → só o total | `privacidade.periodo_tem_massa_suficiente` (já existe) |
| Linha suprimida perde a taxa também | `views.py` (C-4) |

> [!danger] A supressão é feita no servidor, nunca no template
> Se o número real chegar no contexto e o template só "não mostrar", ele está no HTML: basta um *ver código-fonte*.

---

## 🚦 Antes de abrir o editor

```bash
cd educmatch
git switch main && git pull
git switch -c feat/painel-template
cd backend
source .venv/Scripts/activate
python manage.py test painel 2>&1 | tail -5     # a sua linha de base
python manage.py createsuperuser                # se ainda não tiver
```

> [!warning] O CSS do painel fica num arquivo seu
> O `style.css` é da pessoa D. Peça a ela, **no primeiro dia**, o bloco no `<head>` do `base.html` e a troca do link do menu (está na spec dela, D-0):
> ```html
> {% block estilos %}{% endblock %}
> ...
> {% if user.is_staff %}<a href="{% url 'painel-dashboard' %}">Painel</a>{% endif %}
> ```

---

## 3️⃣ C-1 — `core/urls.py`

Acrescente a linha do painel **antes** das rotas com prefixo vazio:

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("painel/", include("painel.urls")),
    path("", include("accounts.urls")),
    path("", include("quiz.web_urls")),
]
```

---

## 4️⃣ C-2 — `painel/tests/base.py` (arquivo novo)

Os testes do painel precisam de dados. Esta base cria esses dados **pelo caminho de verdade**: responde o quiz num navegador novo, como um aluno faria.

```python
from django.test import Client

from accounts.models import Interesse
from catalogo.models import Area, Curso
from quiz.models import Recomendacao, Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class BasePainel(BaseEducMatch):
    """Base dos testes do painel: catálogo real (seeds) e fábricas de dados."""

    def criar_staff(self, email="coord@exemplo.com"):
        return self.criar_usuario(email, is_staff=True)

    def responder_anonimo(self, nome="Visitante", coluna=0):
        """Responde o quiz num navegador novo: cada chamada é uma tentativa anônima."""
        from quiz.models import Questao

        navegador = Client(SERVER_NAME="localhost")
        dados = {"respondido_por": nome}
        for questao in Questao.objects.filter(is_active=True).order_by("id"):
            alternativas = list(questao.alternativas.order_by("id"))
            dados[f"questao_{questao.id}"] = alternativas[coluna % len(alternativas)].id
        navegador.post("/", dados)
        return Tentativa_de_resposta.objects.latest("id")

    def criar_tentativas(self, quantidade=None, nomes=None):
        nomes = nomes or [f"Visitante {i}" for i in range(quantidade)]
        return [self.responder_anonimo(nome, coluna=i) for i, nome in enumerate(nomes)]

    def criar_curso(self, **extra):
        dados = {
            "nome_curso": "Curso de teste",
            "descricao": "Criado pelo teste",
            "area_principal": Area.objects.first(),
            "duracao": 100,
        }
        dados.update(extra)
        return Curso.objects.create(**dados)

    def criar_curso_com(self, recomendacoes=0, interesses=0):
        """Um curso com N recomendações (em tentativas diferentes) e M interessados."""
        curso = self.criar_curso()
        for _ in range(recomendacoes):
            tentativa = Tentativa_de_resposta.objects.create()
            Recomendacao.objects.create(tentativa=tentativa, curso=curso, score=0.5, rank=2)
        for i in range(interesses):
            usuario = self.criar_usuario(f"interessado{i}@exemplo.com")
            Interesse.objects.create(usuario=usuario, curso=curso)
        return curso

    def criar_tentativa_com_explicacao(self, explicacao):
        tentativa = Tentativa_de_resposta.objects.create()
        Recomendacao.objects.create(
            tentativa=tentativa, curso=Curso.objects.first(), score=0.9, rank=1, explicacao=explicacao
        )
        return tentativa
```

---

## 5️⃣ C-3 — `painel/metricas.py`

### O que está quebrado hoje

| Função | Hoje | Conserto | PR |
|---|---|---|---|
| `conversao_por_curso` | `ValueError`: anota com o nome `interessados`, que já é um `related_name` | anotar como `n_interessados` e devolver a chave `interessados` | PR-4 |
| `top_cursos_com_manifestacoes` | cópia de `top_cursos_em_primeiro`: conta **recomendação** | contar `Interesse` | PR-4 |
| `distribuicao_de_confianca` | `confidence_level` (não existe) | `confidence_band` | PR-4 |
| todas com `values("curso__nome_curso")` | chave feia no template | `nome=F("curso__nome_curso")` | PR-4 |
| `cobertura_de_areas` | `Count("pesos_alternativa")` | `Count("pesos__alternativa")` | PR-4 |
| `demanda_por_area` | conta a **string** `"top_areas"` | lê `top_areas[0]["area"]` | **PR-5** (precisa do JSON da B) |
| `tentativas_via_link` | não existe | nova | **PR-5** |

### O arquivo inteiro, como fica no fim do PR-5

No PR-4, faça tudo menos `demanda_por_area` e `tentativas_via_link` (deixe as duas como estão hoje, ou comente a chamada na view).

```python
"""Agregações do painel. Funções puras: recebem datas, devolvem dados.

Nenhuma função daqui recebe request nem usuário, e nenhuma lê `user` ou
`respondido_por`. É isso que garante que o painel fala de cursos e demanda,
nunca de pessoas, e é o que deixa estes números testáveis sem navegador.
"""
from collections import Counter
from datetime import timedelta

from django.db.models import Count, F, Q
from django.utils import timezone

from accounts.models import Interesse
from catalogo.models import Area, Curso
from quiz.models import Recomendacao, Tentativa_de_resposta

PERIODOS = {"30": 30, "90": 90, "365": 365}


def inicio_do_periodo(dias):
    if dias is None:
        return None
    return timezone.now() - timedelta(days=dias)


def _no_periodo(inicio, prefixo="criado_em"):
    if inicio is None:
        return Q()
    return Q(**{f"{prefixo}__gte": inicio})


def total_de_tentativas(inicio):
    return Tentativa_de_resposta.objects.filter(_no_periodo(inicio)).count()


def tentativas_via_link(inicio):
    """Quantas tentativas do período vieram de um link de questionário."""
    return Tentativa_de_resposta.objects.filter(
        _no_periodo(inicio), questionario_link__isnull=False
    ).count()


def top_cursos_com_manifestacoes(inicio, limite=3):
    """Cursos que mais foram salvos na lista de interesse (C4)."""
    return list(
        Interesse.objects
        .filter(_no_periodo(inicio))
        .values("curso_id", nome=F("curso__nome_curso"))
        .annotate(total=Count("id"))
        .order_by("-total", "nome")[:limite]
    )


def top_cursos_em_primeiro(inicio, limite=10):
    return list(
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", nome=F("curso__nome_curso"))
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "nome")[:limite]
    )


def top_cursos_no_top5(inicio, limite=10):
    return list(
        Recomendacao.objects
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", nome=F("curso__nome_curso"))
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "nome")[:limite]
    )


def conversao_por_curso(inicio):
    linhas = (
        Curso.objects
        .filter(is_active=True)
        .annotate(
            recomendado=Count(
                "recomendacoes",
                filter=_no_periodo(inicio, "recomendacoes__tentativa__criado_em"),
                distinct=True,
            ),
            # "interessados" já é o related_name de Interesse.curso: anotar com
            # esse nome dá ValueError. O nome curto volta no dicionário abaixo.
            n_interessados=Count(
                "interessados",
                filter=_no_periodo(inicio, "interessados__criado_em"),
                distinct=True,
            ),
        )
        .values("id", "nome_curso", "recomendado", "n_interessados")
        .order_by("-n_interessados", "nome_curso")
    )

    resultado = []
    for linha in linhas:
        linha["interessados"] = linha.pop("n_interessados")
        recomendado = linha["recomendado"]
        linha["taxa"] = (linha["interessados"] / recomendado * 100) if recomendado else None
        resultado.append(linha)
    return resultado


def aderencia_a_recomendacao(inicio):
    """Quando o aluno salva um curso, em que posição do ranking ele estava?"""
    base = (
        Interesse.objects
        .filter(_no_periodo(inicio))
        .exclude(rank_snapshot__isnull=True)
    )
    return {
        "com_snapshot": base.count(),
        "por_posicao": list(
            base.values("rank_snapshot")
            .annotate(total=Count("id"))
            .order_by("rank_snapshot")
        ),
        "era_principal": base.filter(era_principal=True).count(),
    }


def demanda_por_area(inicio, limite=12):
    """A área que mais pesou em cada 1º lugar do período."""
    explicacoes = (
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values_list("explicacao", flat=True)
    )

    contagem = Counter()
    for explicacao in explicacoes:
        areas = (explicacao or {}).get("top_areas") or []
        if areas and isinstance(areas[0], dict) and areas[0].get("area"):
            contagem[areas[0]["area"]] += 1

    nomes = dict(Area.objects.values_list("slug", "nome"))
    return [
        {"area": slug, "nome": nomes.get(slug, slug), "total": total}
        for slug, total in contagem.most_common(limite)
    ]


def cursos_nunca_recomendados():
    return list(
        Curso.objects
        .filter(is_active=True, recomendacoes__isnull=True)
        .values("id", "nome_curso")
        .order_by("nome_curso")
    )


def distribuicao_de_confianca(inicio):
    return list(
        Tentativa_de_resposta.objects
        .filter(_no_periodo(inicio))
        .values("confidence_band")
        .annotate(total=Count("id"))
        .order_by("confidence_band")
    )


def cursos_ativos():
    return Curso.objects.filter(is_active=True).count()


def cobertura_de_areas():
    """Quantas alternativas do quiz pesam em cada área. Zero = área que o quiz não mede."""
    return list(
        Area.objects
        .annotate(alternativas=Count("pesos__alternativa", distinct=True))
        .values("slug", "nome", "alternativas")
        .order_by("alternativas", "nome")
    )
```

> [!note] `aderencia_a_recomendacao` já estava certa
> Ela lê `rank_snapshot` e `era_principal`, campos que só existem depois do PR-2 da pessoa B. Antes disso ela dá erro, então a view só pode chamá-la no PR-5.

---

## 6️⃣ C-4 — `painel/views.py` e `painel/urls.py`

### `painel/views.py` — substitua

```python
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from painel import metricas, privacidade
from quiz.models import QuestionarioLink


def _links_ativos(request):
    return [
        {
            "url": request.build_absolute_uri(
                reverse("questionario-link", kwargs={"token": link.token})
            ),
            "criado_em": link.criado_em,
        }
        for link in QuestionarioLink.objects.filter(ativo=True)[:5]
    ]


@staff_member_required
def dashboard(request):
    escolhido = request.GET.get("periodo", "90")
    dias = metricas.PERIODOS.get(escolhido)  # "tudo" ou chave inválida -> None -> sem filtro
    inicio = metricas.inicio_do_periodo(dias)

    total = metricas.total_de_tentativas(inicio)
    tem_massa = privacidade.periodo_tem_massa_suficiente(total)

    contexto = {
        "periodo": escolhido,
        "periodos": metricas.PERIODOS,
        "total_de_tentativas": total,
        "tem_massa": tem_massa,
        "k_minimo": privacidade.K_MINIMO,
        "links": _links_ativos(request),
    }
    if not tem_massa:
        # Período pequeno: nenhum número além do total sai do servidor.
        return render(request, "painel/dashboard.html", contexto)

    sup = privacidade.suprimir_pequenos

    conversao = sup(metricas.conversao_por_curso(inicio), campo="interessados")
    for linha in conversao:
        if linha.get("suprimido"):
            # taxa x recomendado / 100 devolveria o número que acabou de ser escondido
            linha["taxa"] = None

    aderencia = metricas.aderencia_a_recomendacao(inicio)
    aderencia["por_posicao"] = sup(aderencia["por_posicao"])

    contexto.update({
        "cursos_ativos": metricas.cursos_ativos(),
        "via_link": metricas.tentativas_via_link(inicio),
        "top_primeiro": sup(metricas.top_cursos_em_primeiro(inicio)),
        "top_manifestacoes": sup(metricas.top_cursos_com_manifestacoes(inicio)),
        "top_cinco": sup(metricas.top_cursos_no_top5(inicio)),
        "conversao": conversao,
        "aderencia": aderencia,
        "demanda_por_area": sup(metricas.demanda_por_area(inicio)),
        "confianca": sup(metricas.distribuicao_de_confianca(inicio)),
        "orfaos": metricas.cursos_nunca_recomendados(),
        "cobertura": metricas.cobertura_de_areas(),
    })
    return render(request, "painel/dashboard.html", contexto)


@require_POST
@staff_member_required
def gerar_link(request):
    QuestionarioLink.objects.create(criado_por=request.user)
    return redirect("painel-dashboard")
```

> [!important] No PR-4, sem os dados da B
> Se o PR-2 ainda não entrou, tire do `contexto.update` as três chaves que dependem dele (`aderencia`, `via_link`, `demanda_por_area`) e as duas linhas do `aderencia` logo acima. O template já trata chave ausente. Elas voltam no PR-5.

> [!danger] Três vazamentos que esta view fecha
> 1. **A taxa da conversão.** Com `interessados` suprimido mas a `taxa` na linha, `taxa × recomendado ÷ 100` devolve o número escondido.
> 2. **A confiança.** "1 teste de confiança baixa" num período de 6 é um número individual.
> 3. **A aderência por posição.** Mesma coisa: contagem pequena por posição.

### `painel/urls.py` — substitua

```python
from django.urls import path

from painel.views import dashboard, gerar_link

urlpatterns = [
    path("", dashboard, name="painel-dashboard"),
    path("gerar-link/", gerar_link, name="painel-gerar-link"),
]
```

> [!note] Staff, não superusuário
> O dashboard antigo exigia **superusuário**; o `painel/` usa `@staff_member_required`, igual ao `/admin`. Para liberar alguém da coordenação: `/admin` → **Usuários** → marcar "Membro da equipe". Quem não é staff cai na tela de login **do `/admin`**, não na `/entrar/`: é o esperado, avise quem for testar.

---

## 7️⃣ C-5 — a tela

### `painel/templates/painel/_celula.html` (arquivo novo)

Uma célula que sabe se mostrar suprimida. Um lugar só decide como o `—` aparece.

```html
{% if suprimido %}<abbr title="menos de {{ k_minimo }} respondentes">—</abbr>{% else %}{{ valor }}{% endif %}
```

### `painel/templates/painel/_ranking.html` (arquivo novo)

As três tabelas de "top cursos" são iguais. Um partial só:

```html
<article class="painel__cartao">
    <h2>{{ titulo }}</h2>
    <table>
        <caption class="visualmente-oculto">{{ titulo }}</caption>
        <thead><tr><th scope="col">Curso</th><th scope="col">{{ coluna }}</th></tr></thead>
        <tbody>
            {% for linha in linhas %}
            <tr>
                <td>
                    {{ linha.nome }}
                    {% if not linha.suprimido %}
                    <span class="painel__barra" style="--largura: {% widthratio linha.total total_de_tentativas 100 %}%" aria-hidden="true"></span>
                    {% endif %}
                </td>
                <td>{% include "painel/_celula.html" with valor=linha.total suprimido=linha.suprimido %}</td>
            </tr>
            {% empty %}
            <tr><td colspan="2">Nenhum dado no período.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</article>
```

> [!tip] Barra em CSS puro, sem biblioteca de gráfico
> `{% widthratio a b 100 %}` calcula a porcentagem no template, e o CSS desenha uma barra com essa largura. Sem Chart.js, sem CDN, sem JavaScript: funciona na rede da escola e com JS desligado. A barra é `aria-hidden` porque o número ao lado já diz tudo.

### `painel/templates/painel/dashboard.html` (arquivo novo)

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Painel da coordenação{% endblock %}

{% block estilos %}<link rel="stylesheet" href="{% static 'css/painel.css' %}">{% endblock %}

{% block content %}
<section class="painel">
    <header class="painel__topo">
        <div>
            <p>Painel da coordenação</p>
            <h1>O que o catálogo e a demanda estão dizendo</h1>
        </div>
        <nav class="painel__periodos" aria-label="Período">
            {% for chave, dias in periodos.items %}
            <a href="?periodo={{ chave }}" {% if periodo == chave %}aria-current="page"{% endif %}>{{ dias }} dias</a>
            {% endfor %}
            <a href="?periodo=tudo" {% if periodo == "tudo" %}aria-current="page"{% endif %}>Tudo</a>
        </nav>
    </header>

    <div class="painel__numeros">
        <article class="painel__numero">
            <h2>Testes respondidos</h2>
            <p>{{ total_de_tentativas }}</p>
        </article>
        {% if tem_massa %}
        <article class="painel__numero">
            <h2>Pelo link da escola</h2>
            <p>{{ via_link }}</p>
        </article>
        <article class="painel__numero">
            <h2>Cursos ativos</h2>
            <p>{{ cursos_ativos }}</p>
        </article>
        {% endif %}
    </div>

    {% if not tem_massa %}
    <p class="painel__aviso" role="status">
        Menos de {{ k_minimo }} testes neste período. Para proteger quem respondeu,
        só o total aparece. Escolha um período maior.
    </p>
    {% else %}

    <div class="painel__grade">
        {% include "painel/_ranking.html" with titulo="Cursos em 1º lugar" linhas=top_primeiro coluna="Testes" %}
        {% include "painel/_ranking.html" with titulo="Cursos que aparecem no top 5" linhas=top_cinco coluna="Testes" %}
        {% include "painel/_ranking.html" with titulo="Cursos mais salvos na lista" linhas=top_manifestacoes coluna="Alunos" %}

        <article class="painel__cartao">
            <h2>Área que mais pesou no 1º lugar</h2>
            <table>
                <caption class="visualmente-oculto">Demanda por área</caption>
                <thead><tr><th scope="col">Área</th><th scope="col">Testes</th></tr></thead>
                <tbody>
                    {% for linha in demanda_por_area %}
                    <tr>
                        <td>{{ linha.nome }}</td>
                        <td>{% include "painel/_celula.html" with valor=linha.total suprimido=linha.suprimido %}</td>
                    </tr>
                    {% empty %}
                    <tr><td colspan="2">Nenhum dado no período.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </article>

        <article class="painel__cartao">
            <h2>Confiança do resultado</h2>
            <table>
                <caption class="visualmente-oculto">Distribuição da confiança</caption>
                <thead><tr><th scope="col">Confiança</th><th scope="col">Testes</th></tr></thead>
                <tbody>
                    {% for linha in confianca %}
                    <tr>
                        <td>{{ linha.confidence_band|default:"sem cálculo"|capfirst }}</td>
                        <td>{% include "painel/_celula.html" with valor=linha.total suprimido=linha.suprimido %}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </article>

        <article class="painel__cartao">
            <h2>Quem salva, salva o 1º lugar?</h2>
            {% if aderencia.com_snapshot %}
            <p class="painel__destaque">{% widthratio aderencia.era_principal aderencia.com_snapshot 100 %}%</p>
            <p>dos cursos salvos eram o 1º lugar do aluno.</p>
            {% else %}
            <p>Ninguém salvou curso no período.</p>
            {% endif %}
        </article>
    </div>

    <article class="painel__cartao painel__cartao--largo">
        <h2>Conversão: recomendado → salvo</h2>
        <table>
            <caption class="visualmente-oculto">Conversão por curso</caption>
            <thead>
                <tr><th scope="col">Curso</th><th scope="col">Recomendado</th><th scope="col">Salvo</th><th scope="col">Taxa</th></tr>
            </thead>
            <tbody>
                {% for linha in conversao %}
                <tr>
                    <td>{{ linha.nome_curso }}</td>
                    <td>{{ linha.recomendado }}</td>
                    <td>{% include "painel/_celula.html" with valor=linha.interessados suprimido=linha.suprimido %}</td>
                    <td>{% if linha.taxa is None %}{% include "painel/_celula.html" with suprimido=True %}{% else %}{{ linha.taxa|floatformat:0 }}%{% endif %}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </article>

    <div class="painel__grade">
        <article class="painel__cartao">
            <h2>Cursos nunca recomendados</h2>
            <ul>
                {% for curso in orfaos %}<li>{{ curso.nome_curso }}</li>{% empty %}<li>Todos os cursos já apareceram.</li>{% endfor %}
            </ul>
        </article>

        <article class="painel__cartao">
            <h2>Áreas que o quiz mede</h2>
            <table>
                <caption class="visualmente-oculto">Cobertura das áreas pelo quiz</caption>
                <thead><tr><th scope="col">Área</th><th scope="col">Alternativas</th></tr></thead>
                <tbody>
                    {% for area in cobertura %}
                    <tr {% if not area.alternativas %}class="painel__alerta"{% endif %}>
                        <td>{{ area.nome }}</td>
                        <td>{{ area.alternativas }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </article>
    </div>
    {% endif %}

    <article class="painel__cartao painel__cartao--largo">
        <h2>Links de questionário</h2>
        <form method="post" action="{% url 'painel-gerar-link' %}">
            {% csrf_token %}
            <button class="botao" type="submit">Gerar novo link</button>
        </form>
        <ul class="painel__links">
            {% for link in links %}
            <li>
                <input type="text" value="{{ link.url }}" readonly aria-label="Link criado em {{ link.criado_em|date:'d/m/Y H:i' }}">
                <button type="button" class="botao botao--ghost" data-copiar>Copiar</button>
            </li>
            {% empty %}
            <li>Nenhum link ativo.</li>
            {% endfor %}
        </ul>
    </article>

    <p class="painel__rodape">
        Nenhum nome, e-mail ou resposta individual aparece aqui. Números abaixo de
        {{ k_minimo }} aparecem como <abbr title="menos de {{ k_minimo }} respondentes">—</abbr>.
        Para um caso individual, use o <a href="{% url 'admin:index' %}">/admin</a>.
    </p>
</section>
{% endblock %}

{% block scripts %}
<script>
    // Copiar o link: melhora opcional. Sem JS, o campo continua selecionável.
    document.querySelectorAll("[data-copiar]").forEach(function (botao) {
        botao.addEventListener("click", function () {
            var campo = botao.previousElementSibling;
            navigator.clipboard.writeText(campo.value).then(function () {
                botao.textContent = "Copiado";
            });
        });
    });
</script>
{% endblock %}
```

> [!note] Por que o `—` é um `<abbr>`
> Um leitor de tela lê "—" como "travessão", o que não diz nada. Com o `title`, ele lê "menos de 5 respondentes". Quem enxerga vê a explicação ao passar o mouse.

### `static/css/painel.css` (arquivo novo)

```css
/* Painel da coordenação. Usa as variáveis do :root do style.css. */

.painel {
  display: grid;
  gap: 1.5rem;
}

.painel__topo {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1rem;
  border-bottom: 3px solid var(--vermelho);
  padding-bottom: 1rem;
}

.painel__periodos {
  display: flex;
  gap: 0.5rem;
}

.painel__periodos a {
  padding: 0.5rem 0.9rem;
  border: 1px solid var(--linha);
  border-radius: 999px;
  text-decoration: none;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
}

.painel__periodos a[aria-current="page"] {
  background: var(--preto);
  color: var(--branco);
  border-color: var(--preto);
}

.painel__numeros,
.painel__grade {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.painel__numero,
.painel__cartao {
  background: var(--branco);
  border: 1px solid var(--linha);
  border-radius: 12px;
  padding: 1.2rem;
}

.painel__numero h2,
.painel__cartao h2 {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--vermelho-escuro);
  margin-bottom: 0.6rem;
}

.painel__numero p,
.painel__destaque {
  font-size: 2.2rem;
  font-weight: 700;
  margin: 0;
}

.painel__cartao--largo {
  grid-column: 1 / -1;
}

.painel table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.painel th {
  text-align: left;
  border-bottom: 2px solid var(--preto);
  padding: 0.4rem;
}

.painel td {
  border-bottom: 1px solid var(--linha);
  padding: 0.4rem;
}

.painel td:last-child,
.painel th:last-child {
  text-align: right;
}

/* Barra proporcional ao total de testes do período */
.painel__barra {
  display: block;
  height: 6px;
  margin-top: 0.3rem;
  width: var(--largura);
  background: var(--vermelho);
  border-radius: 3px;
}

.painel abbr {
  text-decoration: none;
  cursor: help;
  color: var(--cinza);
}

.painel__aviso {
  background: #fff8e1;
  border-left: 4px solid #b26a00;
  padding: 1rem;
  border-radius: 8px;
}

.painel__alerta td {
  color: var(--vermelho-escuro);
  font-weight: 700;
}

.painel__links {
  list-style: none;
  padding: 0;
  display: grid;
  gap: 0.5rem;
}

.painel__links li {
  display: flex;
  gap: 0.5rem;
}

.painel__links input {
  flex: 1;
  min-height: 44px;
  padding: 0 0.6rem;
  border: 1px solid var(--linha);
  border-radius: 8px;
}

.painel__rodape {
  font-size: 0.85rem;
  color: var(--cinza);
}

/* Escondido na tela, lido pelo leitor de tela */
.visualmente-oculto {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
```

---

## 8️⃣ C-6 — aposentar o dashboard antigo

### `quiz/web_urls.py` — substitua

```python
from django.urls import path
from django.views.generic import RedirectView

from quiz.web_views import acessar_questionario, pagina_quiz, resultado_pagina

urlpatterns = [
    path('', pagina_quiz, name='quiz-inicio'),
    path('questionario/<uuid:token>/', acessar_questionario, name='questionario-link'),
    path('resultado/<int:pk>/', resultado_pagina, name='quiz-resultado'),
    # O dashboard antigo virou o painel: o endereço velho só redireciona
    path('quiz/dashboard/', RedirectView.as_view(pattern_name='painel-dashboard', permanent=True), name='dashboard'),
]
```

### Apagar o que sobrou do dashboard antigo

```bash
git rm quiz/views.py templates/quiz/dashboard.html
grep -rn "quiz.views\|quiz/dashboard.html\|gerar-questionario-link" --include=*.py --include=*.html .
```

O `grep` tem de voltar vazio. `quiz/views.py` só tinha o dashboard e o gerador de link: os dois agora estão no `painel/`.

### `quiz/tests/test_rotas_web.py` — o teste do dashboard muda

```python
    def test_dashboard_antigo_redireciona_para_o_painel(self):
        resposta = self.client.get("/quiz/dashboard/")
        self.assertEqual(resposta.status_code, 301)
        self.assertEqual(resposta["Location"], "/painel/")
```

Ele substitui o `test_dashboard_continua_na_mesma_url`.

---

## 9️⃣ C-7 — os testes

### `painel/tests/test_privacidade.py` — substitua

```python
from django.test import SimpleTestCase
from django.urls import reverse

from accounts.models import Interesse
from painel.privacidade import K_MINIMO, suprimir_pequenos
from painel.tests.base import BasePainel
from quiz.models import QuestionarioLink


class SupressaoTest(SimpleTestCase):
    def test_celula_pequena_e_suprimida_mas_a_linha_fica(self):
        linhas = [{"nome": "A", "total": 9}, {"nome": "B", "total": 2}]

        saida = suprimir_pequenos(linhas)

        self.assertEqual(len(saida), 2, "esconder a linha vazaria pela omissão")
        self.assertEqual(saida[0]["total"], 9)
        self.assertIsNone(saida[1]["total"])
        self.assertTrue(saida[1]["suprimido"])

    def test_a_funcao_nao_altera_a_entrada(self):
        linhas = [{"nome": "B", "total": 2}]
        suprimir_pequenos(linhas)
        self.assertEqual(linhas[0]["total"], 2)


class AcessoAoPainelTest(BasePainel):
    def setUp(self):
        super().setUp()
        self.comum = self.criar_usuario("aluno@exemplo.com")
        self.staff = self.criar_staff()

    def test_anonimo_nao_entra(self):
        resposta = self.client.get(reverse("painel-dashboard"))
        self.assertEqual(resposta.status_code, 302)

    def test_usuario_comum_nao_entra(self):
        self.client.force_login(self.comum)
        resposta = self.client.get(reverse("painel-dashboard"))
        self.assertNotEqual(resposta.status_code, 200)

    def test_staff_entra(self):
        self.client.force_login(self.staff)
        resposta = self.client.get(reverse("painel-dashboard"))
        self.assertEqual(resposta.status_code, 200)

    def test_usuario_comum_nao_gera_link(self):
        self.client.force_login(self.comum)
        self.client.post(reverse("painel-gerar-link"))
        self.assertFalse(QuestionarioLink.objects.exists())

    def test_staff_gera_link_e_ele_aparece_no_painel(self):
        self.client.force_login(self.staff)

        resposta = self.client.post(reverse("painel-gerar-link"), follow=True)

        link = QuestionarioLink.objects.get()
        self.assertContains(resposta, str(link.token))

    def test_gerar_link_por_get_nao_faz_nada(self):
        self.client.force_login(self.staff)
        resposta = self.client.get(reverse("painel-gerar-link"))
        self.assertEqual(resposta.status_code, 405)
        self.assertFalse(QuestionarioLink.objects.exists())


class PrivacidadeNaTelaTest(BasePainel):
    def setUp(self):
        super().setUp()
        self.staff = self.criar_staff()

    def abrir_painel(self):
        self.client.force_login(self.staff)
        return self.client.get(reverse("painel-dashboard"))

    def test_sem_massa_so_o_total_sai_do_servidor(self):
        self.criar_tentativas(quantidade=K_MINIMO - 1)

        contexto = self.abrir_painel().context

        self.assertFalse(contexto["tem_massa"])
        self.assertEqual(contexto["total_de_tentativas"], K_MINIMO - 1)
        for chave in ("conversao", "top_primeiro", "confianca", "demanda_por_area"):
            self.assertNotIn(chave, contexto)

    def test_conversao_suprimida_nao_vaza_pela_taxa(self):
        """taxa x recomendado / 100 reconstruiria o número escondido."""
        tentativas = self.criar_tentativas(quantidade=K_MINIMO + 1)
        curso = tentativas[0].recomendacoes.get(rank=1).curso
        Interesse.objects.create(usuario=self.criar_usuario("um@exemplo.com"), curso=curso)

        conversao = self.abrir_painel().context["conversao"]

        linha = next(l for l in conversao if l["id"] == curso.id)
        self.assertTrue(linha["suprimido"])
        self.assertIsNone(linha["interessados"])
        self.assertIsNone(linha["taxa"])

    def test_confianca_tambem_e_suprimida(self):
        self.criar_tentativas(quantidade=K_MINIMO + 1)

        confianca = self.abrir_painel().context["confianca"]

        for linha in confianca:
            if linha["total"] is not None:
                self.assertGreaterEqual(linha["total"], K_MINIMO)

    def test_nenhum_nome_de_respondente_aparece_na_pagina(self):
        """A regra de privacidade, verificada no HTML servido."""
        nomes = ["Ana Zoraide", "Bento Kling", "Cleo Vasquez", "Dora Pimm", "Eli Nunes", "Fabi Ros"]
        self.criar_tentativas(nomes=nomes)

        corpo = self.abrir_painel().content.decode()

        for nome in nomes:
            self.assertNotIn(nome, corpo)
```

> [!important] O `test_nenhum_nome...` usa **6** nomes de propósito
> Com 3 (como estava), o período fica sem massa e o painel mostra só o total: o teste passaria sem nunca renderizar uma tabela. Com 6, o painel mostra tudo, e o teste prova que nenhum nome vaza **mesmo com todas as tabelas na tela**.

### `painel/tests/test_metricas.py` — substitua

```python
from painel import metricas
from painel.tests.base import BasePainel


class MetricasTest(BasePainel):
    def test_conversao_nao_infla_com_dois_joins(self):
        """O bug do produto cartesiano: dois Count sobre duas relações.

        Um curso com 3 recomendações e 2 interesses tem de devolver 3 e 2,
        não 6 e 6.
        """
        curso = self.criar_curso_com(recomendacoes=3, interesses=2)

        linha = next(l for l in metricas.conversao_por_curso(None) if l["id"] == curso.id)

        self.assertEqual(linha["recomendado"], 3)
        self.assertEqual(linha["interessados"], 2)
        self.assertAlmostEqual(linha["taxa"], 2 / 3 * 100)

    def test_demanda_por_area_le_a_area_dominante(self):
        """Lê top_areas[0]["area"], no formato que o motor grava de verdade. (PR-5)"""
        self.criar_tentativa_com_explicacao(
            {"top_areas": [{"area": "eletrica", "area_name": "Elétrica", "contribuicao": 3.0, "percentual": 75.0}]}
        )

        demanda = metricas.demanda_por_area(None)

        self.assertEqual(demanda[0]["area"], "eletrica")
        self.assertEqual(demanda[0]["total"], 1)

    def test_curso_inativo_nao_entra_na_conversao(self):
        inativo = self.criar_curso(is_active=False)
        ids = [linha["id"] for linha in metricas.conversao_por_curso(None)]
        self.assertNotIn(inativo.id, ids)

    def test_manifestacoes_contam_interesse_e_nao_recomendacao(self):
        curso = self.criar_curso_com(recomendacoes=4, interesses=1)

        top = metricas.top_cursos_com_manifestacoes(None)

        linha = next(l for l in top if l["curso_id"] == curso.id)
        self.assertEqual(linha["total"], 1)
        self.assertEqual(linha["nome"], curso.nome_curso)

    def test_distribuicao_de_confianca_roda(self):
        self.criar_tentativas(quantidade=2)
        bandas = {linha["confidence_band"] for linha in metricas.distribuicao_de_confianca(None)}
        self.assertTrue(bandas <= {"alta", "media", "baixa"})

    def test_cobertura_acusa_area_sem_questao(self):
        """A métrica que mostra o tamanho do buraco do instrumento."""
        sem_questao = [a for a in metricas.cobertura_de_areas() if a["alternativas"] == 0]
        self.assertTrue(sem_questao, "nenhuma área sem questão: confira o related_name")
```

> [!warning] O teste de demanda antigo passava pelo motivo errado
> Ele montava `{"eletrica": 0.6, "ti": 0.2}`, um formato que o motor **nunca** gravou, e a função antiga contava as chaves do dicionário. O teste novo usa o formato real (`top_areas`). No PR-4, deixe esse teste para o PR-5.

---

## 🔟 Verificação

```bash
python manage.py test painel quiz.tests.test_rotas_web -v 2
python manage.py test 2>&1 | tail -5                # nenhuma falha nova
```

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | Anônimo em `/painel/` | Vai para o login do `/admin` |
| 2 | Aluno logado em `/painel/` | **Não** vê o painel |
| 3 | Staff, com menos de 5 testes no período | Só o total e o aviso |
| 4 | Responder o quiz 6 vezes numa janela anônima e abrir o painel | Tabelas com números, e toda célula abaixo de 5 como `—` |
| 5 | Linha de conversão com `—` | A taxa também é `—` |
| 6 | *Ver código-fonte* e `Ctrl+F` pelo nome digitado no quiz | Não aparece |
| 7 | "Gerar novo link" → abrir o link numa janela anônima | Cai no quiz com a faixa "link da escola" (depois da D) |
| 8 | `/quiz/dashboard/` | Redireciona para `/painel/` |

---

## 1️⃣1️⃣ Commits e PRs

**PR-4** (`feat/painel-template`):

```bash
git add -A && git status --short
git commit -m "feat(painel): painel unico em /painel/ com k-anonimato e gerador de link"
git push -u origin feat/painel-template
```

```markdown
## O que muda
- /painel/ no ar: um painel só, com k-anonimato (k = 5)
- Supressão também na taxa de conversão, na confiança e na aderência por posição
- Gerador de link de questionário dentro do painel
- /quiz/dashboard/ redireciona para /painel/; o dashboard antigo foi removido
- painel/tests/base.py: as fábricas de dados que os testes chamavam e não existiam

## Toca contrato de outra frente?
Não: o painel só lê.
```

**PR-5** (`feat/painel-metricas`, depois do PR-2 da B mesclado): `demanda_por_area`, `tentativas_via_link`, as três chaves de volta na view e o teste de demanda. Commit: `feat(painel): demanda por area, aderencia e respostas pelo link`.

---

## ▶️ Próxima ação

Pedir à pessoa D o `{% block estilos %}` no `base.html`, criar a branch `feat/painel-template` e fazer a §3.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]]
- [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel]] — de onde vêm as regras de privacidade
- [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 PNL-01 a PNL-05]] — o plano original
