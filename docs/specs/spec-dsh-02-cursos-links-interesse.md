---
title: "Spec DSH-02 — telas Cursos e Áreas, Links de acesso e Lista de interesse"
aliases: ["DSH-02", "Cursos, Links e Interesse"]
tags: [tcc, spec, painel, dashboard, privacidade]
status: proposto
projeto: TCC
branch: feature/painel-cursos-links-interesse
criado: 2026-10-01
---

> [!info] Plano: [[plano-dashboard-git-flow|🖥️ Dashboard novo e Git Flow]] · Anterior: [[spec-dsh-01-casca-inicio-quiz|01 — casca, Início e Quiz]] · Próxima: [[spec-dsh-03-conclusao-e-tempo|03 — conclusão e tempo]]

# 📚 DSH-02: Cursos e Áreas, Links de acesso e Lista de interesse

**Branch:** `feature/painel-cursos-links-interesse`, saindo da `develop` **com a DSH-01 já mesclada**
**Risco:** baixo. Nenhuma migração. Uma rota de POST nova (fechar **um** link).
**Testes ao final:** 103 (96 + 7 novos)

> [!abstract] O que esta branch faz
> Três telas novas no menu, todas com dados que **já existem** no banco:
> 1. **Cursos e Áreas** (`/painel/cursos/`): o catálogo ativo, quantas vezes cada curso ficou em 1º e no Top 5, e atalho para editar no admin.
> 2. **Links de acesso** (`/painel/links/`): todos os links, com QR code, testes por link e botão para fechar **um** link (hoje só dá para fechar todos).
> 3. **Lista de interesse** (`/painel/interesse/`): o funil por status e uma tabela por curso, **sem nenhum nome ou e-mail**.

---

## 1️⃣ `painel/privacidade.py`: supressão de várias colunas

O `suprimir_pequenos` julga **um** campo e marca a linha inteira com `suprimido`. As tabelas desta branch têm duas ou três colunas contadas, e cada uma precisa da sua marca. Acrescente no fim do arquivo:

```python
def suprimir_campos(linhas, campos, k=K_MINIMO):
    """suprimir_pequenos para tabelas com mais de uma coluna contada.

    Cada campo é julgado sozinho e ganha a sua marca: "<campo>_suprimido".
    """
    resultado = []
    for linha in linhas:
        copia = dict(linha)
        for campo in campos:
            if copia.get(campo) is not None and copia[campo] < k:
                copia[campo] = SUPRIMIDO
                copia[f"{campo}_suprimido"] = True
        resultado.append(copia)
    return resultado
```

> [!note] Por que não mudar o `suprimir_pequenos`
> Os testes `SupressaoTest` e todas as telas da DSH-01 dependem do formato atual (`"suprimido": True`). Uma função nova não mexe em nada que já funciona.

## 2️⃣ `painel/metricas.py`: quatro consultas novas

Troque o import de `quiz.models`:

```python
from quiz.models import QuestionarioLink, Recomendacao, Tentativa_de_resposta
```

E acrescente no fim:

```python
def desempenho_por_curso(inicio):
    """Cada curso ativo com quantas vezes ficou em 1º e quantas entrou no Top 5."""
    periodo = _no_periodo(inicio, "recomendacoes__tentativa__criado_em")
    return list(
        Curso.objects
        .filter(is_active=True)
        .annotate(
            em_primeiro=Count("recomendacoes", filter=periodo & Q(recomendacoes__rank_final=1), distinct=True),
            no_top5=Count("recomendacoes", filter=periodo, distinct=True),
        )
        .values(
            "id", "nome_curso", "duracao", "inicio_dia", "fim_dia",
            "em_primeiro", "no_top5", area=F("area_principal__nome"),
        )
        .order_by("area", "nome_curso")
    )


def testes_por_link(limite=20):
    """Os links mais recentes, ativos ou fechados, com quantos testes cada um trouxe."""
    return list(
        QuestionarioLink.objects
        .annotate(total=Count("tentativas"))
        .values("id", "token", "criado_em", "ativo", "total")
        .order_by("-criado_em")[:limite]
    )


def funil_de_interesse(inicio):
    """Quantos cursos salvos estão em cada status, na ordem do funil."""
    contagem = dict(
        Interesse.objects
        .filter(_no_periodo(inicio))
        .values_list("status")
        .annotate(total=Count("id"))
    )
    return [
        {"status": chave, "rotulo": rotulo, "total": contagem.get(chave, 0)}
        for chave, rotulo in Interesse.STATUS
    ]


def interesse_por_curso(inicio):
    """Por curso: quantos salvaram, em que pé está o contato e quantos eram o 1º colocado."""
    periodo = _no_periodo(inicio, "interessados__criado_em")
    linhas = (
        Curso.objects
        .annotate(
            total=Count("interessados", filter=periodo & ~Q(interessados__status="removido")),
            contatados=Count("interessados", filter=periodo & Q(interessados__status="contatado")),
            principal=Count("interessados", filter=periodo & Q(interessados__era_principal=True) & ~Q(interessados__status="removido")),
        )
        .filter(total__gt=0)
        .values("id", "nome_curso", "total", "contatados", "principal", area=F("area_principal__nome"))
        .order_by("-total", "nome_curso")
    )
    return list(linhas)
```

> [!tip] `interesse_por_curso` não lê o usuário
> As contagens saem de `Count("interessados", filter=...)`, direto no curso. Nenhum `values()` desta função pede `usuario`, `email` ou `respondido_por`, e isso continua valendo a regra do topo do `metricas.py`: o painel fala de cursos, nunca de pessoas.

## 3️⃣ `painel/views.py`: substitua o arquivo inteiro

```python
from urllib.parse import urlencode

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from painel import metricas, privacidade
from quiz.models import QuestionarioLink, Tentativa_de_resposta


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


def _contexto_base(request, secao):
    """O que toda tela do painel usa: período escolhido, massa mínima e menu."""
    escolhido = request.GET.get("periodo", "mensal")
    if escolhido not in metricas.PERIODOS:
        escolhido = "mensal"
    mes = request.GET.get("mes") or ""
    inicio = metricas.inicio_do_periodo(escolhido, mes=mes)
    total = metricas.total_de_tentativas(inicio)

    filtro = {"periodo": escolhido}
    if escolhido == "mes" and mes:
        filtro["mes"] = mes

    return inicio, {
        "secao": secao,
        "periodo": escolhido,
        "periodo_label": metricas.PERIODOS[escolhido]["label"],
        "mes": mes,
        "periodos": metricas.PERIODOS,
        # Os links do menu levam o período junto: trocar de tela não reseta o filtro.
        "periodo_qs": urlencode(filtro),
        "total_de_tentativas": total,
        "tem_massa": privacidade.periodo_tem_massa_suficiente(total),
        "k_minimo": privacidade.K_MINIMO,
    }


@staff_member_required
def dashboard(request):
    inicio, contexto = _contexto_base(request, "inicio")
    contexto["links"] = _links_ativos(request)
    contexto["cursos_ativos"] = metricas.cursos_ativos()
    if not contexto["tem_massa"]:
        # Período pequeno: nenhum número além do total sai do servidor.
        return render(request, "painel/inicio.html", contexto)

    sup = privacidade.suprimir_pequenos
    contexto.update({
        "via_link": metricas.tentativas_via_link(inicio),
        "conversao_geral": metricas.conversao_geral(inicio),
        "serie": sup(metricas.tentativas_por_dia(inicio)),
        "demanda_por_area": sup(metricas.demanda_por_area(inicio)),
        "atividade": sup(metricas.atividade_recente()),
    })
    return render(request, "painel/inicio.html", contexto)


@staff_member_required
def quiz_visao_geral(request):
    inicio, contexto = _contexto_base(request, "quiz")
    if not contexto["tem_massa"]:
        return render(request, "painel/quiz.html", contexto)

    sup = privacidade.suprimir_pequenos
    conversao = sup(metricas.conversao_por_curso(inicio), campo="interessados")
    for linha in conversao:
        if linha.get("suprimido"):
            # taxa x recomendado / 100 devolveria o número que acabou de ser escondido
            linha["taxa"] = None

    aderencia = metricas.aderencia_a_recomendacao(inicio)
    aderencia["por_posicao"] = sup(aderencia["por_posicao"])
    # Mesma regra da conversão: a taxa sobre um total conhecido devolveria o número pequeno.
    principal = aderencia["era_principal"]
    aderencia["taxa"] = (
        principal / aderencia["com_snapshot"] * 100 if principal >= privacidade.K_MINIMO else None
    )

    confianca = sup(metricas.distribuicao_de_confianca(inicio))
    nomes = dict(Tentativa_de_resposta.CONFIDENCE_CHOICE_NIVEIS)
    for linha in confianca:
        linha["rotulo"] = nomes.get(linha["confidence_band"], "Sem banda")

    contexto.update({
        "top_manifestacoes": sup(metricas.top_cursos_com_manifestacoes(inicio)),
        "top_primeiro": sup(metricas.top_cursos_em_primeiro(inicio, limite=5)),
        "top_cinco": sup(metricas.top_cursos_no_top5(inicio, limite=5)),
        "confianca": confianca,
        "aderencia": aderencia,
        "conversao": conversao,
        "orfaos": metricas.cursos_nunca_recomendados(),
        "cobertura": metricas.cobertura_de_areas(),
    })
    return render(request, "painel/quiz.html", contexto)


@staff_member_required
def cursos(request):
    inicio, contexto = _contexto_base(request, "cursos")
    linhas = metricas.desempenho_por_curso(inicio)
    if contexto["tem_massa"]:
        linhas = privacidade.suprimir_campos(linhas, ("em_primeiro", "no_top5"))
        contexto["demanda_por_area"] = privacidade.suprimir_pequenos(metricas.demanda_por_area(inicio))
    else:
        for linha in linhas:
            linha["em_primeiro"] = linha["no_top5"] = None
    contexto["cursos"] = linhas
    return render(request, "painel/cursos.html", contexto)


@staff_member_required
def links(request):
    _, contexto = _contexto_base(request, "links")
    linhas = privacidade.suprimir_pequenos(metricas.testes_por_link())
    for linha in linhas:
        linha["url"] = request.build_absolute_uri(
            reverse("questionario-link", kwargs={"token": linha["token"]})
        )
    contexto["links"] = linhas
    return render(request, "painel/links.html", contexto)


@staff_member_required
def interesse(request):
    inicio, contexto = _contexto_base(request, "interesse")
    if not contexto["tem_massa"]:
        return render(request, "painel/interesse.html", contexto)

    linhas = privacidade.suprimir_campos(
        metricas.interesse_por_curso(inicio), ("total", "contatados", "principal")
    )
    for linha in linhas:
        # O % sobre um total conhecido devolveria um número escondido: só sai se os dois saíram.
        pode = linha["total"] is not None and linha["principal"] is not None
        linha["taxa_principal"] = linha["principal"] / linha["total"] * 100 if pode else None

    contexto.update({
        "funil": privacidade.suprimir_pequenos(metricas.funil_de_interesse(inicio)),
        "por_curso": linhas,
    })
    return render(request, "painel/interesse.html", contexto)


# As ações de link voltam para a tela de onde vieram, mas só para uma destas.
VOLTAS_PERMITIDAS = {"painel-dashboard", "painel-links"}


def _voltar(request):
    destino = request.POST.get("voltar")
    return redirect(destino if destino in VOLTAS_PERMITIDAS else "painel-dashboard")


@require_POST
@staff_member_required
def fechar_um_link(request, pk):
    link = get_object_or_404(QuestionarioLink, pk=pk)
    link.ativo = False
    link.save()
    return _voltar(request)


@require_POST
@staff_member_required
def fechar_link(request):
    ativo = QuestionarioLink.objects.filter(ativo=True)
    for link in ativo:
        link.ativo = False
        link.save()
    return _voltar(request)


@require_POST
@staff_member_required
def gerar_link(request):
    QuestionarioLink.objects.create(criado_por=request.user)
    return _voltar(request)
```

> [!danger] O `voltar` é uma lista fechada, e não uma URL
> Gerar e fechar link agora podem voltar para a Início **ou** para a tela de Links. O jeito ingênuo seria `redirect(request.POST["voltar"])`, e isso é um *open redirect*: qualquer página poderia mandar um POST com `voltar=https://site-falso` e o painel levaria o coordenador para lá. Aqui o `voltar` só aceita **nomes de rota** de `VOLTAS_PERMITIDAS`; qualquer outra coisa cai na Início. O teste `test_voltar_para_endereco_de_fora_cai_no_inicio` trava isso.

## 4️⃣ `painel/urls.py`: substitua o arquivo inteiro

```python
from django.urls import path
from painel import views

urlpatterns = [
    path("", views.dashboard, name="painel-dashboard"),
    path("quiz/", views.quiz_visao_geral, name="painel-quiz"),
    path("cursos/", views.cursos, name="painel-cursos"),
    path("links/", views.links, name="painel-links"),
    path("interesse/", views.interesse, name="painel-interesse"),
    path("gerar-link/", views.gerar_link, name="painel-gerar-link"),
    path("fechar-link/", views.fechar_link, name="painel-fechar-link"),
    path("links/<int:pk>/fechar/", views.fechar_um_link, name="painel-fechar-um-link"),
]
```

## 5️⃣ Templates

### `painel/templates/painel/base_painel.html`: três itens no menu

Depois do item "Quiz", e com um campo `voltar` no form de "Gerar link" do menu:

```diff
@@ -19,9 +19,19 @@
             <a class="painel-menu__item" href="{% url 'painel-quiz' %}?{{ periodo_qs }}" {% if secao == "quiz" %}aria-current="page"{% endif %}>
                 <i class="fa-solid fa-circle-question" aria-hidden="true"></i> Quiz
             </a>
+            <a class="painel-menu__item" href="{% url 'painel-cursos' %}?{{ periodo_qs }}" {% if secao == "cursos" %}aria-current="page"{% endif %}>
+                <i class="fa-solid fa-graduation-cap" aria-hidden="true"></i> Cursos e Áreas
+            </a>
+            <a class="painel-menu__item" href="{% url 'painel-links' %}?{{ periodo_qs }}" {% if secao == "links" %}aria-current="page"{% endif %}>
+                <i class="fa-solid fa-link" aria-hidden="true"></i> Links de acesso
+            </a>
+            <a class="painel-menu__item" href="{% url 'painel-interesse' %}?{{ periodo_qs }}" {% if secao == "interesse" %}aria-current="page"{% endif %}>
+                <i class="fa-solid fa-heart" aria-hidden="true"></i> Lista de interesse
+            </a>
         </nav>
         <form class="painel-menu__chamada" method="post" action="{% url 'painel-gerar-link' %}" data-confirmar="Gerar um novo link de acesso ao quiz?">
             {% csrf_token %}
+            <input type="hidden" name="voltar" value="{% if secao == 'links' %}painel-links{% else %}painel-dashboard{% endif %}">
             <strong>Gere um link e compartilhe o quiz com a turma.</strong>
             <button type="submit" class="botao botao--bloco"><i class="fa-solid fa-link" aria-hidden="true"></i> Gerar link</button>
         </form>
@@ -93,6 +103,7 @@
 {% endblock %}
 
 {% block scripts %}
-<script src="{% static 'js/painel.js' %}" defer></script>
+{# Bibliotecas da tela primeiro: com defer, a ordem do documento é a de execução. #}
 {% block scripts_painel %}{% endblock %}
+<script src="{% static 'js/painel.js' %}" defer></script>
 {% endblock %}
```

> [!note] O menu inferior do celular não muda
> Ele continua com Início, Quiz e **Mais**. O "Mais" abre o menu lateral inteiro, onde estão os itens novos.

### `painel/templates/painel/cursos.html` (novo)

```html
{% extends "painel/base_painel.html" %}
{% block titulo_painel %}Cursos e Áreas{% endblock %}
{% block titulo_pagina %}Cursos e Áreas{% endblock %}
{% block subtitulo %}Catálogo ativo e como cada curso aparece no ranking{% endblock %}
{% block acoes %}
<a class="botao" href="{% url 'admin:catalogo_curso_add' %}"><i class="fa-solid fa-plus" aria-hidden="true"></i> Novo curso</a>
{% endblock %}

{% block painel %}
{% if not tem_massa %}{% include "painel/_sem_massa.html" %}{% endif %}
<div class="painel-grade painel-grade--2-1">
    <article class="painel-card">
        <h2 class="painel-card__titulo">Cursos ativos ({{ cursos|length }})</h2>
        <div class="painel-tabela">
            <table>
                <thead>
                    <tr>
                        <th scope="col">Curso</th>
                        <th scope="col">Área</th>
                        <th scope="col" class="numero">Duração</th>
                        <th scope="col">Turma</th>
                        <th scope="col" class="numero">Em 1º</th>
                        <th scope="col" class="numero">No Top 5</th>
                        <th scope="col"><span class="visualmente-oculto">Ações</span></th>
                    </tr>
                </thead>
                <tbody>
                    {% for curso in cursos %}
                    <tr>
                        <td>{{ curso.nome_curso }}</td>
                        <td>{{ curso.area }}</td>
                        <td class="numero">{{ curso.duracao }}h</td>
                        <td>{% if curso.inicio_dia %}{{ curso.inicio_dia|date:"d/m" }}–{{ curso.fim_dia|date:"d/m"|default:"?" }}{% else %}—{% endif %}</td>
                        <td class="numero">{% if tem_massa %}{% include "painel/_celula.html" with valor=curso.em_primeiro suprimido=curso.em_primeiro_suprimido %}{% else %}—{% endif %}</td>
                        <td class="numero">{% if tem_massa %}{% include "painel/_celula.html" with valor=curso.no_top5 suprimido=curso.no_top5_suprimido %}{% else %}—{% endif %}</td>
                        <td><a class="botao botao--suave botao--icone" href="{% url 'admin:catalogo_curso_change' curso.id %}" aria-label="Editar {{ curso.nome_curso }}"><i class="fa-solid fa-pen" aria-hidden="true"></i></a></td>
                    </tr>
                    {% empty %}<tr><td colspan="7">Nenhum curso ativo.</td></tr>{% endfor %}
                </tbody>
            </table>
        </div>
    </article>

    <article class="painel-card">
        <h2 class="painel-card__titulo">Áreas mais fortes no 1º lugar</h2>
        {% if tem_massa %}
        <ul class="painel-lista">
            {% for linha in demanda_por_area %}
            <li><span>{{ linha.nome }}</span><b>{% include "painel/_celula.html" with valor=linha.total suprimido=linha.suprimido %}</b></li>
            {% empty %}<li>Nenhum dado no período.</li>{% endfor %}
        </ul>
        {% else %}
        <p class="painel-vazio">Aparece quando o período tiver {{ k_minimo }} testes ou mais.</p>
        {% endif %}
    </article>
</div>
{% endblock %}
```

> [!important] "Novo curso" e "Editar" levam para o admin
> O painel **não** ganha formulário de curso nesta fase. O admin já cadastra e valida curso, área e pesos; duplicar isso no painel seria código novo para manter, sem ganho para a banca. O botão existe para o fluxo do design ficar completo.

### `painel/templates/painel/links.html` (novo)

```html
{% extends "painel/base_painel.html" %}
{% block titulo_painel %}Links de acesso{% endblock %}
{% block titulo_pagina %}Links de acesso{% endblock %}
{% block subtitulo %}Endereços para a turma responder o quiz{% endblock %}
{% block acoes %}
<form method="post" action="{% url 'painel-gerar-link' %}" data-confirmar="Gerar um novo link de acesso ao quiz?">
    {% csrf_token %}
    <input type="hidden" name="voltar" value="painel-links">
    <button type="submit" class="botao"><i class="fa-solid fa-plus" aria-hidden="true"></i> Gerar link</button>
</form>
{% endblock %}

{% block painel %}
<article class="painel-card">
    <div class="painel-tabela">
        <table>
            <thead>
                <tr>
                    <th scope="col">QR code</th>
                    <th scope="col">Endereço</th>
                    <th scope="col">Criado em</th>
                    <th scope="col" class="numero">Testes</th>
                    <th scope="col">Status</th>
                    <th scope="col"><span class="visualmente-oculto">Ações</span></th>
                </tr>
            </thead>
            <tbody>
                {% for link in links %}
                <tr>
                    <td>{% if link.ativo %}<div class="painel-qr" data-qr="{{ link.url }}" role="img" aria-label="QR code do link"></div>{% else %}—{% endif %}</td>
                    <td>
                        <div class="painel-link">
                            <input class="painel-link__url" type="text" value="{{ link.url }}" readonly aria-label="Endereço do link">
                            {% if link.ativo %}<button type="button" class="botao botao--secundario" data-copiar><i class="fa-solid fa-copy" aria-hidden="true"></i> Copiar</button>{% endif %}
                        </div>
                    </td>
                    <td>{{ link.criado_em|date:"d/m/Y H:i" }}</td>
                    <td class="numero">{% include "painel/_celula.html" with valor=link.total suprimido=link.suprimido %}</td>
                    <td>{% if link.ativo %}<span class="painel-selo painel-selo--sucesso">Ativo</span>{% else %}<span class="painel-selo painel-selo--neutro">Fechado</span>{% endif %}</td>
                    <td>
                        {% if link.ativo %}
                        <form method="post" action="{% url 'painel-fechar-um-link' link.id %}" data-confirmar="Fechar este link? Quem tiver o endereço não consegue mais entrar." data-perigo>
                            {% csrf_token %}
                            <input type="hidden" name="voltar" value="painel-links">
                            <button type="submit" class="botao botao--perigo"><i class="fa-solid fa-ban" aria-hidden="true"></i> Fechar</button>
                        </form>
                        {% endif %}
                    </td>
                </tr>
                {% empty %}<tr><td colspan="6">Nenhum link gerado ainda.</td></tr>{% endfor %}
            </tbody>
        </table>
    </div>
</article>
{% endblock %}

{% block scripts_painel %}
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js" defer></script>
{% endblock %}
```

### `painel/templates/painel/interesse.html` (novo)

```html
{% extends "painel/base_painel.html" %}
{% block titulo_painel %}Lista de interesse{% endblock %}
{% block titulo_pagina %}Lista de interesse{% endblock %}
{% block subtitulo %}Cursos salvos pelos alunos, sem dados pessoais{% endblock %}

{% block painel %}
{% if not tem_massa %}
{% include "painel/_sem_massa.html" %}
{% else %}
<ol class="painel-funil">
    {% for etapa in funil %}
    <li class="painel-card">
        <span>{{ etapa.rotulo }}</span>
        <b>{% include "painel/_celula.html" with valor=etapa.total suprimido=etapa.suprimido %}</b>
    </li>
    {% endfor %}
</ol>

<article class="painel-card">
    <h2 class="painel-card__titulo">Por curso</h2>
    <div class="painel-tabela">
        <table>
            <thead>
                <tr>
                    <th scope="col">Curso</th>
                    <th scope="col">Área</th>
                    <th scope="col" class="numero">Salvaram</th>
                    <th scope="col" class="numero">Contatados</th>
                    <th scope="col" class="numero">Era o 1º colocado <span class="painel-ajuda" tabindex="0" data-dica="Dos que salvaram o curso, quantos o tinham em 1º lugar no resultado.">?</span></th>
                </tr>
            </thead>
            <tbody>
                {% for linha in por_curso %}
                <tr>
                    <td>{{ linha.nome_curso }}</td>
                    <td>{{ linha.area }}</td>
                    <td class="numero">{% include "painel/_celula.html" with valor=linha.total suprimido=linha.total_suprimido %}</td>
                    <td class="numero">{% include "painel/_celula.html" with valor=linha.contatados suprimido=linha.contatados_suprimido %}</td>
                    <td class="numero">{% if linha.taxa_principal is None %}—{% else %}{{ linha.taxa_principal|floatformat:0 }}%{% endif %}</td>
                </tr>
                {% empty %}<tr><td colspan="5">Nenhum curso salvo no período.</td></tr>{% endfor %}
            </tbody>
        </table>
    </div>
</article>
{% endif %}
{% endblock %}
```

> [!important] O que saiu do design nesta tela
> O design tinha uma coluna "Status" por curso e "Era o 1º colocado? Sim/Não". As duas não fazem sentido numa tabela **agregada** (um curso tem vários interessados, com status diferentes). Ficaram: o funil por status no topo e, por curso, o **%** que tinha o curso em 1º lugar, suprimido como a conversão.

## 6️⃣ CSS e JS

### `static/css/painel.css`

Antes do bloco `/* Modal de confirmação */`:

```css
/* Funil da lista de interesse e QR dos links */

.painel-funil {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 0 0 16px;
  padding: 0;
  list-style: none;
}

.painel-funil li {
  display: grid;
  gap: 4px;
  border-left: 4px solid var(--marca);
  background: var(--marca-clarinho);
  text-align: center;
}

.painel-funil b {
  color: var(--titulo);
  font-size: 1.5rem;
}

.painel-qr {
  width: 88px;
  height: 88px;
  padding: 4px;
  border: 1px solid var(--linha);
  border-radius: 8px;
  background: var(--branco);
}

.painel-qr img,
.painel-qr canvas {
  width: 100% !important;
  height: 100% !important;
}
```

E dentro do `@media (max-width: 760px)`, depois de `.painel-grade--2`:

```css
  .painel-funil {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
```

### `static/js/painel.js`

Antes do bloco `data-copiar`, o desenho do QR:

```js
    // QR dos links: o qrcode.min.js só é carregado na tela de links, antes deste arquivo.
    if (window.QRCode) {
        document.querySelectorAll("[data-qr]").forEach(function (caixa) {
            new QRCode(caixa, { text: caixa.dataset.qr, width: 160, height: 160 });
        });
    }
```

### `base_painel.html`: a ordem dos scripts

Já está no diff da seção 5️⃣, mas merece a explicação. O `qrcode.min.js` precisa rodar **antes** do `painel.js`. Os dois usam `defer`, que executa na ordem do documento, então o bloco da tela vem primeiro:

```html
{% block scripts %}
{# Bibliotecas da tela primeiro: com defer, a ordem do documento é a de execução. #}
{% block scripts_painel %}{% endblock %}
<script src="{% static 'js/painel.js' %}" defer></script>
{% endblock %}
```

> [!warning] Esse erro passa calado
> Com a ordem invertida, a página abre normalmente, sem erro no console, e só **não aparece QR nenhum**. Foi o que aconteceu quando esta spec foi testada pela primeira vez.

---

## 7️⃣ Testes

### `painel/tests/test_telas.py`

No topo, o import de `quiz.models` passa a trazer o link:

```python
from quiz.models import QuestionarioLink, Tentativa_de_resposta
```

No `test_tela_servida_tambem_nao_tem_botao_fantasma`, as telas novas entram na volta:

```python
        for tela in ("painel-dashboard", "painel-quiz", "painel-cursos", "painel-links", "painel-interesse"):
```

E uma classe nova no fim do arquivo:

```python
class TelasDeCadastroTest(BasePainel):
    """DSH-02: Cursos e Áreas, Links de acesso e Lista de interesse."""

    TELAS = ("painel-cursos", "painel-links", "painel-interesse")

    def setUp(self):
        super().setUp()
        self.staff = self.criar_staff()

    def test_so_staff_entra(self):
        comum = self.criar_usuario("aluno@exemplo.com")
        for tela in self.TELAS:
            with self.subTest(tela=tela):
                self.client.logout()
                self.assertEqual(self.client.get(reverse(tela)).status_code, 302)
                self.client.force_login(comum)
                self.assertNotEqual(self.client.get(reverse(tela)).status_code, 200)
                self.client.force_login(self.staff)
                self.assertEqual(self.client.get(reverse(tela)).status_code, 200)

    def test_testes_por_link_sao_suprimidos(self):
        self.client.force_login(self.staff)
        link = QuestionarioLink.objects.create(criado_por=self.staff)
        tentativas = self.criar_tentativas(quantidade=2)
        Tentativa_de_resposta.objects.filter(pk__in=[t.pk for t in tentativas]).update(questionario_link=link)

        linhas = self.client.get(reverse("painel-links")).context["links"]

        self.assertTrue(linhas[0]["suprimido"])
        self.assertIsNone(linhas[0]["total"])

    def test_fechar_um_link_nao_fecha_os_outros(self):
        self.client.force_login(self.staff)
        primeiro, segundo = (QuestionarioLink.objects.create(criado_por=self.staff) for _ in range(2))

        resposta = self.client.post(
            reverse("painel-fechar-um-link", args=[primeiro.pk]), {"voltar": "painel-links"}
        )

        self.assertRedirects(resposta, reverse("painel-links"))
        primeiro.refresh_from_db()
        segundo.refresh_from_db()
        self.assertFalse(primeiro.ativo)
        self.assertTrue(segundo.ativo)

    def test_voltar_para_endereco_de_fora_cai_no_inicio(self):
        self.client.force_login(self.staff)

        resposta = self.client.post(reverse("painel-gerar-link"), {"voltar": "https://exemplo.com/"})

        self.assertRedirects(resposta, reverse("painel-dashboard"))

    def test_lista_de_interesse_nao_mostra_quem_salvou(self):
        self.client.force_login(self.staff)
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        emails = [f"pessoa{i}@exemplo.com" for i in range(K_MINIMO)]
        for email in emails:
            Interesse.objects.create(usuario=self.criar_usuario(email), curso=curso, era_principal=True)

        resposta = self.client.get(reverse("painel-interesse"))

        linha = next(l for l in resposta.context["por_curso"] if l["id"] == curso.id)
        self.assertEqual(linha["total"], K_MINIMO)
        self.assertEqual(linha["taxa_principal"], 100)
        for email in emails:
            self.assertNotContains(resposta, email)

    def test_taxa_de_1o_colocado_some_se_a_contagem_for_pequena(self):
        self.client.force_login(self.staff)
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        for i in range(K_MINIMO):
            Interesse.objects.create(
                usuario=self.criar_usuario(f"pessoa{i}@exemplo.com"), curso=curso, era_principal=(i == 0)
            )

        linhas = self.client.get(reverse("painel-interesse")).context["por_curso"]

        linha = next(l for l in linhas if l["id"] == curso.id)
        self.assertTrue(linha["principal_suprimido"])
        self.assertIsNone(linha["taxa_principal"])

    def test_funil_segue_a_ordem_dos_status(self):
        self.client.force_login(self.staff)
        self.criar_tentativas(quantidade=K_MINIMO)

        funil = self.client.get(reverse("painel-interesse")).context["funil"]

        self.assertEqual([etapa["status"] for etapa in funil], [chave for chave, _ in Interesse.STATUS])
```

---

## ✅ Verificação

```bash
cd backend
python manage.py test                                # 103 testes
python manage.py makemigrations --check --dry-run   # No changes detected
python manage.py runserver
```

- [ ] O menu tem 5 itens e marca a tela atual
- [ ] **Links**: um link ativo mostra o QR; "Gerar link" no topo da tela volta para a própria tela de links; "Fechar" fecha só aquele link e pede confirmação em vermelho
- [ ] **Cursos**: os 20 cursos ativos, "Em 1º" e "No Top 5" com cadeado onde a contagem é menor que 5; "Novo curso" e o lápis abrem o admin
- [ ] **Lista de interesse**: o funil na ordem Interessado → Contatado → Descartado → Removido; nenhum e-mail na página (Ctrl+F `@`)

## 📦 Commit e PR

```bash
git add -A
git commit -m "feat(painel): telas de cursos, links e lista de interesse

- cursos: catalogo ativo com vezes em 1o e no top 5, atalhos para o admin
- links: todos os links com QR, testes por link e fechar um link so
- interesse: funil por status e tabela por curso sem dados pessoais
- privacidade.suprimir_campos para tabelas com mais de uma contagem
- voltar das acoes de link restrito a rotas conhecidas"
git push -u origin feature/painel-cursos-links-interesse
gh pr create --base develop --fill
```

> [!success] Definition of Done
> 103 testes, CI verde, o checklist acima conferido e nenhum dado pessoal nas três telas novas.
