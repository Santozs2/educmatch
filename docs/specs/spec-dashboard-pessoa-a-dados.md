---
title: "Spec do dashboard — Pessoa A · Dados e regras"
aliases: ["Dashboard pessoa A", "Spec A dashboard", "Dados e regras do painel"]
tags: [tcc, painel, dashboard, avaliacao, django, privacidade, spec, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-10-01
---

> [!info] Mapa: [[guia-dashboard-live-share|🖥️ Guia do grupo]] · Colegas: [[spec-dashboard-pessoa-b-telas|🖼️ B · Telas]] · [[spec-dashboard-pessoa-c-estilo-e-testes|🎨 C · Estilo e testes]]

# 🧮 Pessoa A · Dados e regras

> [!abstract] A sua missão
> Você decide **o que cada tela recebe**. Escreve as consultas ao banco, as views e as rotas, e é a guardiã da regra mais importante do painel: **nenhum número pode apontar uma pessoa**.
> Você é dona de todo arquivo `.py` que **não** é teste. B depende dos nomes das suas variáveis e C depende das suas funções; por isso, no começo de cada etapa há uma tabela **"o que você entrega"**, que é o seu pedaço do contrato.

> [!tip] Como ler esta spec
> Cada etapa tem: o que você entrega (o contrato), os arquivos na ordem em que convém escrever, um **🎓 Entenda** explicando o porquê, e um **✅ Pronta quando** para você saber que acabou. Ao terminar, avise no chat da sessão: **"A: views da etapa N prontas"**. É o sinal para C rodar os testes.

---

## 🧭 O mapa

| Etapa | Arquivos seus |
|---|---|
| **1** | `painel/metricas.py`, `painel/views.py`, `painel/urls.py` |
| **2** | `painel/privacidade.py`, `painel/metricas.py`, `painel/views.py`, `painel/urls.py` |
| **3** | `quiz/models.py` + migração, `quiz/web_views.py`, `painel/metricas.py`, `painel/views.py`, `painel/templatetags/` |
| **4** | App novo `avaliacao/` (models, migração, seed, form, views, rotas, admin), `core/settings.py`, `core/urls.py` |
| **5** | `painel/metricas_avaliacao.py`, `painel/forms.py`, `painel/views.py`, `painel/urls.py` |

> [!note] Sobre os blocos `diff`
> Quando um arquivo muda só um pouco, a spec mostra a mudança como **diff**: linha começando com `+` **entra**, com `-` **sai**, e as outras (sem sinal) estão lá só para você achar o lugar. Os `@@ ... @@` dizem mais ou menos em que linha fica. Não copie os sinais `+` e `-`.

---

# Etapa 1 · Casca do painel, Início e Quiz

### O que você entrega

| Tela | Rota | Variáveis que a tela recebe (além das comuns do guia) |
|---|---|---|
| Início | `painel-dashboard` | `links`, `cursos_ativos`; e, **só se `tem_massa`**: `via_link`, `conversao_geral`, `serie`, `demanda_por_area`, `atividade` |
| Quiz | `painel-quiz` | **só se `tem_massa`**: `top_manifestacoes`, `top_primeiro`, `top_cinco`, `confianca`, `aderencia`, `conversao`, `orfaos`, `cobertura` |

Toda lista que passa pela supressão tem, em cada linha, `total` (ou `None`) e `suprimido: True` quando foi escondida.

## 1.1 `painel/metricas.py`: três métricas novas

No topo, junto dos imports do Django:

```python
from django.db.models.functions import TruncDate, TruncMonth
```

E no fim do arquivo:

```python
def conversao_geral(inicio):
    """Cursos salvos ÷ cursos recomendados no período, somando todos os cursos.

    Com menos de K interesses, a taxa vira None: taxa x recomendações / 100
    devolveria a contagem pequena que a supressão esconde.
    """
    from painel.privacidade import K_MINIMO

    linhas = conversao_por_curso(inicio)
    recomendado = sum(linha["recomendado"] for linha in linhas)
    interessados = sum(linha["interessados"] for linha in linhas)
    if not recomendado or interessados < K_MINIMO:
        return None
    return interessados / recomendado * 100


def tentativas_por_dia(inicio):
    """Testes por dia (até 62 dias) ou por mês (períodos maiores), em ordem."""
    agora = timezone.now()
    por_mes = inicio is None or (agora - inicio).days > 62
    truncar = TruncMonth("criado_em") if por_mes else TruncDate("criado_em")
    formato = "%m/%Y" if por_mes else "%d/%m"

    linhas = (
        Tentativa_de_resposta.objects
        .filter(_no_periodo(inicio))
        .annotate(dia=truncar)
        .values("dia")
        .annotate(total=Count("id"))
        .order_by("dia")
    )
    return [{"rotulo": linha["dia"].strftime(formato), "total": linha["total"]} for linha in linhas]


def atividade_recente():
    """Contagens das últimas horas. Nunca uma linha por pessoa nem horário exato."""
    agora = timezone.now()
    return [
        {
            "icone": "fa-circle-check",
            "rotulo": "testes concluídos na última hora",
            "total": Tentativa_de_resposta.objects.filter(criado_em__gte=agora - timedelta(hours=1)).count(),
        },
        {
            "icone": "fa-clipboard-list",
            "rotulo": "testes concluídos nas últimas 24 horas",
            "total": Tentativa_de_resposta.objects.filter(criado_em__gte=agora - timedelta(days=1)).count(),
        },
        {
            "icone": "fa-heart",
            "rotulo": "cursos salvos nas últimas 24 horas",
            "total": Interesse.objects.filter(criado_em__gte=agora - timedelta(days=1)).exclude(status="removido").count(),
        },
    ]
```

> [!danger] 🎓 Entenda: cada métrica tem uma armadilha de privacidade
> | Métrica | Armadilha | Como foi resolvida |
> |---|---|---|
> | `conversao_geral` | Uma **taxa** sobre um total conhecido devolve a contagem: 3 salvos ÷ 120 recomendações = 2,5% → dá para voltar ao 3 | Com menos de 5 salvos, a taxa vira `None` |
> | `tentativas_por_dia` | Um dia com 1 teste diz "alguém respondeu na terça" | A view passa a série pela supressão: o dia vira `None` e a linha do gráfico fica com um buraco |
> | `atividade_recente` | O design tinha "Nova manifestação · Enfermagem · há 16 min", que aponta para uma pessoa | Só contagens de janela (última hora, últimas 24 h), e também suprimidas |

## 1.2 `painel/views.py`: substitua o arquivo inteiro

```python
from urllib.parse import urlencode

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
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


@require_POST
@staff_member_required
def fechar_link(request):
    ativo = QuestionarioLink.objects.filter(ativo=True)
    for link in ativo:
        link.ativo = False
        link.save()
    return redirect("painel-dashboard")


@require_POST
@staff_member_required
def gerar_link(request):
    QuestionarioLink.objects.create(criado_por=request.user)
    return redirect("painel-dashboard")
```

> [!tip] 🎓 Entenda: o `_contexto_base`
> Toda tela do painel precisa das mesmas coisas: o período escolhido, se há massa mínima e qual item do menu marcar. Em vez de repetir isso em cada view, a função devolve um dicionário pronto, e cada view só acrescenta o que é dela com `contexto.update(...)`.
>
> Repare em duas proteções:
> - **Período inválido** (`?periodo=qualquercoisa`) volta para `"mensal"`. Nunca confie no que vem da URL.
> - O `periodo_qs` sai pronto do `urlencode`. É ele que faz o filtro **não se perder** quando a coordenação troca de tela pelo menu.

> [!important] 🎓 Entenda: a aderência também esconde a taxa
> Na view do Quiz, a aderência (quantos salvaram o 1º colocado) só vira porcentagem se o número de "era o 1º" for 5 ou mais. É a mesma armadilha da conversão: uma taxa sobre um total conhecido devolve o número pequeno.

## 1.3 `painel/urls.py`: substitua o arquivo inteiro

```python
from django.urls import path
from painel.views import dashboard, fechar_link, gerar_link, quiz_visao_geral

urlpatterns = [
    path("", dashboard, name="painel-dashboard"),
    path("quiz/", quiz_visao_geral, name="painel-quiz"),
    path("gerar-link/", gerar_link, name="painel-gerar-link"),
    path("fechar-link/", fechar_link, name="painel-fechar-link"),
]
```

O nome `painel-dashboard` continua o mesmo de antes. Assim o menu do usuário no `base.html` e o redirecionamento de `/quiz/dashboard/` continuam funcionando sem ninguém mexer neles.

### ✅ Pronta quando

- [ ] `python manage.py check` responde `System check identified no issues`
- [ ] Você avisou no chat: **"A: views da etapa 1 prontas"**

---

# Etapa 2 · Cursos e Áreas, Links e Lista de interesse

### O que você entrega

| Tela | Rota | Variáveis |
|---|---|---|
| Cursos e Áreas | `painel-cursos` | `cursos` (cada linha com `em_primeiro`, `no_top5` e os `_suprimido` de cada um), `demanda_por_area` (só se `tem_massa`) |
| Links | `painel-links` | `links` (cada linha com `url`, `ativo`, `total`, `suprimido`, `criado_em`, `id`) |
| Lista de interesse | `painel-interesse` | só se `tem_massa`: `funil`, `por_curso` (com `total_suprimido`, `contatados_suprimido` e `taxa_principal`) |
| (ação) | `painel-fechar-um-link` | POST que fecha **um** link e volta para onde o campo `voltar` mandar |

## 2.1 `painel/privacidade.py`: supressão de várias colunas

A função `suprimir_pequenos` olha **um** campo e marca a linha inteira. As tabelas desta etapa têm duas ou três colunas contadas, e cada uma precisa da sua marca. Acrescente no fim:

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

> [!note] 🎓 Entenda: por que uma função nova, e não mudar a antiga
> Tudo o que a etapa 1 fez depende do formato da antiga (`"suprimido": True`). Uma função nova não mexe em nada que já funciona. Regra boa para a vida: **ampliar é mais seguro do que alterar**.

## 2.2 `painel/metricas.py`: quatro consultas novas

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

> [!tip] 🎓 Entenda: contar sem olhar quem
> `interesse_por_curso` conta os interessados direto no curso, com `Count("interessados", filter=...)`. Nenhum `values()` pede `usuario` ou `email`. Assim a regra do topo do arquivo continua valendo: estas funções falam de cursos, nunca de pessoas.

## 2.3 `painel/views.py`: substitua o arquivo inteiro

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

> [!danger] 🎓 Entenda: o `voltar` é uma lista fechada, e não um endereço
> Gerar e fechar link agora podem voltar para a Início **ou** para a tela de Links. O jeito ingênuo seria `redirect(request.POST["voltar"])`, e isso abre um *open redirect*: qualquer página poderia mandar um POST com `voltar=https://site-falso` e o painel levaria a coordenação para lá. Aqui o `voltar` só aceita **nomes de rota** da lista `VOLTAS_PERMITIDAS`; qualquer outra coisa cai na Início.

## 2.4 `painel/urls.py`: substitua o arquivo inteiro

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

### ✅ Pronta quando

- [ ] `python manage.py check` sem problemas
- [ ] Você avisou: **"A: views da etapa 2 prontas"**

---

# Etapa 3 · % concluídos e tempo típico do quiz

### O que você entrega

| Onde | O que |
|---|---|
| Tela Quiz | `questoes_ativas` (sempre); `taxa_de_conclusao` e `tempo_tipico` (só se `tem_massa`; podem vir `None`) |
| Filtro de template | `duracao`, em `painel/templatetags/painel_extras.py`: transforma um `timedelta` em `"08:42"` |
| Banco | Model `InicioDeQuiz` e campo `Tentativa_de_resposta.iniciado_em` |

> [!abstract] 🎓 Entenda: por que o banco precisa de algo novo
> O design pede "% concluídos" e "tempo médio". Hoje a tentativa só nasce **no fim** do quiz, com `criado_em`. Não existe registro de quem **começou e desistiu**, nem de **quando** começou. Esta etapa cria os dois.

## 3.1 Onde o quiz "começa"

A tela de introdução (`quiz.html`) envia um GET com `respondido_por` e `etapa=1`. Esse é o início. Mas o mesmo GET também acontece quando o aluno **recarrega** a página ou **volta** para a questão 1. Por isso o início é marcado na **sessão** e só conta se a marca ainda não existe:

| Situação | Conta início? |
|---|---|
| Abre a 1ª questão pela primeira vez | ✅ |
| Recarrega, ou volta para a questão 1 | ❌ (a marca já existe) |
| Termina e começa outro quiz | ✅ (a marca saiu no fim) |
| Abre e fecha a aba sem terminar | ✅, e é justamente o abandono que a taxa mede |
| Envia direto, sem passar pela introdução | ❌, e a tentativa fica com `iniciado_em` vazio |

## 3.2 `quiz/models.py`

Em `Tentativa_de_resposta`, logo depois de `respondido_por`:

```python
    # Etapa 3: quando a 1ª questão foi aberta. Vazio em tentativas antigas e nas
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

> [!danger] 🎓 Entenda: por que o `InicioDeQuiz` não guarda quem começou
> Ele existe para **uma** conta: começados ÷ concluídos. Guardar quem começou criaria uma lista de "pessoas que desistiram do quiz", que ninguém pediu e que a LGPD trataria como dado pessoal sem finalidade. O teste de C `test_inicio_nao_guarda_quem_comecou` trava os campos.

### A migração (só você, no terminal de quem hospeda)

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

Depois, `python manage.py migrate`. O campo novo aceita vazio (`null=True`), então as tentativas antigas ficam com `iniciado_em` vazio e não é preciso preencher nada à mão.

## 3.3 `quiz/web_views.py`

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

> [!note] 🎓 Entenda: `parse_datetime("")` devolve `None`
> Por isso o `or ""` na criação da tentativa: sem início na sessão, o campo fica vazio, sem precisar de `if`.

## 3.4 `painel/metricas.py`

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

    Só conta tentativas com iniciado_em: as antigas (antes da Etapa 3) não têm
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

> [!important] 🎓 Entenda: mediana, e não média
> Um aluno que deixa a aba aberta de um dia para o outro soma 24 horas. Numa turma de 30 com 8 minutos cada, isso puxa a **média** de 8 para **56 minutos**. A **mediana** (o valor do meio da fila) nem se mexe. Por isso o card se chama **"Tempo típico"**.
>
> E a taxa só conta tentativas **com** `iniciado_em`: as antigas não têm início registrado e dariam mais de 100% no primeiro mês.

## 3.5 `painel/views.py`

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

## 3.6 O filtro `duracao`

Crie a pasta `painel/templatetags/` com um `__init__.py` vazio e o arquivo `painel_extras.py`:

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

> [!tip] 🎓 Entenda: filtro de template
> No template, `{{ tempo_tipico|duracao }}` chama esta função com o valor da esquerda. A pasta precisa se chamar exatamente `templatetags` e ter o `__init__.py`, senão o Django não acha. B vai carregar com `{% load painel_extras %}`.

### ✅ Pronta quando

- [ ] `python manage.py makemigrations --check --dry-run` responde `No changes detected`
- [ ] `python manage.py migrate` rodou na máquina de quem hospeda
- [ ] Você avisou: **"A: etapa 3 pronta, migração aplicada"**

---

# Etapa 4 · Avaliação de fim de curso (a página do aluno)

### O que você entrega

| Onde | O que |
|---|---|
| Rotas | `avaliacao-responder` e `avaliacao-obrigado`, em `/avaliacao/<token>/` |
| Tela de responder | `link` (com `link.curso` e `link.turma`) e `form`, que tem `form.campos_por_pergunta` → pares `(pergunta, campo)` |
| Tela de obrigado | `link` (pode vir `None`) |
| Admin | Perguntas e Links de avaliação |
| Comando | `python manage.py seed_avaliacao` (7 perguntas) |

> [!abstract] 🎓 Entenda: o que foi decidido
> Não aparece no fim do quiz: é aplicada **no fim do curso técnico**. O aluno chega por um **link da turma**, sem login. É **sempre anônima**, ligada a **um curso** do catálogo, e **fixa** (sem construtor de perguntas).

## 4.1 Criar e registrar o app

```bash
cd backend
python manage.py startapp avaliacao
```

Apague o `avaliacao/tests.py` que o comando cria: C vai pôr os testes numa pasta. Depois registre o app e a rota:

```diff
@@ -48,6 +48,7 @@ INSTALLED_APPS = [
     'catalogo',
     'accounts',
     'painel',
+    'avaliacao',
 ]
 
 AUTH_USER_MODEL = 'accounts.User'
```

```diff
@@ -7,4 +7,5 @@ urlpatterns = [
     path("", include("accounts.urls")),
     path("", include("quiz.web_urls")),
     path("cursos/", include("catalogo.urls")),
+    path("avaliacao/", include("avaliacao.urls")),
 ]
\ No newline at end of file
```

## 4.2 `avaliacao/models.py`

```python
"""Avaliação de fim de curso: perguntas fixas, um link por turma, respostas anônimas.

Nenhum model deste app guarda usuário, nome, e-mail, IP ou horário. A resposta
sabe só o link (e por ele o curso e a turma) e o DIA em que chegou. É isso que
permite dizer à turma "é anônimo" sem precisar de promessa: não há onde guardar.
"""
import uuid

from django.conf import settings
from django.db import models


class Pergunta(models.Model):
    TIPOS = [
        ("nps", "Nota de 0 a 10"),
        ("escala", "Escala de 1 a 5"),
        ("escolha", "Escolha única"),
        ("texto", "Texto livre"),
    ]

    texto = models.CharField(max_length=200)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    # Só para "escolha": a lista de opções, na ordem em que aparecem.
    opcoes = models.JSONField(default=list, blank=True)
    obrigatoria = models.BooleanField(default=True)
    ordem = models.PositiveSmallIntegerField(unique=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["ordem"]

    def __str__(self):
        return f"{self.ordem}. {self.texto}"


class LinkDeAvaliacao(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    curso = models.ForeignKey("catalogo.Curso", on_delete=models.PROTECT, related_name="links_de_avaliacao")
    turma = models.CharField(max_length=60, help_text='Como a escola chama a turma. Ex.: "2026/1 · Noite"')
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "link de avaliação"
        verbose_name_plural = "links de avaliação"

    def __str__(self):
        return f"{self.curso} · {self.turma}"


class RespostaDeAvaliacao(models.Model):
    link = models.ForeignKey(LinkDeAvaliacao, on_delete=models.PROTECT, related_name="respostas")
    # Data e não data e hora: "respondeu às 10h14" junto com a turma aponta para uma pessoa.
    respondido_em = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "resposta de avaliação"
        verbose_name_plural = "respostas de avaliação"


class ItemDeResposta(models.Model):
    resposta = models.ForeignKey(RespostaDeAvaliacao, on_delete=models.CASCADE, related_name="itens")
    pergunta = models.ForeignKey(Pergunta, on_delete=models.PROTECT, related_name="itens")
    numero = models.PositiveSmallIntegerField(null=True, blank=True)  # nps e escala
    texto = models.TextField(blank=True)  # escolha e texto

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["resposta", "pergunta"], name="uma_resposta_por_pergunta"),
        ]
```

> [!danger] 🎓 Entenda: anônimo **por construção**
> | Escolha | Por quê |
> |---|---|
> | A resposta **não tem** campo de usuário, nem quando o aluno está logado | Se o campo existisse, alguém um dia o preencheria "só para conferir". Sem o campo, não há como |
> | `respondido_em` guarda o **dia**, e não a hora | Numa turma de 20, "respondeu às 10h14" aponta para uma pessoa. O dia não aponta |
> | Nada de IP nem de sessão | Os dois identificam o aparelho |
> | `PROTECT` em `link` e `pergunta` | Apagar um link ou uma pergunta não pode apagar respostas em silêncio. Para tirar uma pergunta, desmarque `ativa` |

### A migração

```bash
python manage.py makemigrations avaliacao
```

A saída tem de ser:

```
Migrations for 'avaliacao':
  avaliacao\migrations\0001_initial.py
    + Create model Pergunta
    + Create model LinkDeAvaliacao
    + Create model RespostaDeAvaliacao
    + Create model ItemDeResposta
```

E depois `python manage.py migrate`.

## 4.3 As perguntas: `avaliacao/management/commands/seed_avaliacao.py`

Crie também os `__init__.py` vazios em `avaliacao/management/` e em `avaliacao/management/commands/`.

```python
from django.core.management.base import BaseCommand
from django.db import transaction

from avaliacao.models import Pergunta

# A avaliação de fim de curso. É uma PROPOSTA: a coordenação revisa o texto aqui
# (ou no admin) antes da primeira turma. Rodar de novo atualiza pela "ordem".
PERGUNTAS = [
    {
        "ordem": 1,
        "tipo": "nps",
        "texto": "De 0 a 10, quanto você recomendaria este curso a um amigo?",
    },
    {
        "ordem": 2,
        "tipo": "escala",
        "texto": "O curso atendeu às suas expectativas?",
    },
    {
        "ordem": 3,
        "tipo": "escala",
        "texto": "Como você avalia os instrutores?",
    },
    {
        "ordem": 4,
        "tipo": "escala",
        "texto": "Como você avalia a estrutura (laboratórios, equipamentos e materiais)?",
    },
    {
        "ordem": 5,
        "tipo": "escala",
        "texto": "O que você aprendeu vai ajudar no seu próximo passo profissional?",
    },
    {
        # A pergunta que liga a avaliação ao TCC: a recomendação do quiz acertou?
        "ordem": 6,
        "tipo": "escolha",
        "texto": "O curso combinou com o que o quiz do EducMatch tinha mostrado para você?",
        "opcoes": ["Sim", "Em parte", "Não", "Não fiz o quiz"],
    },
    {
        "ordem": 7,
        "tipo": "texto",
        "texto": "O que poderia melhorar no curso?",
        "obrigatoria": False,
    },
]


class Command(BaseCommand):
    help = "Cria ou atualiza as perguntas da avaliação de fim de curso."

    @transaction.atomic
    def handle(self, *args, **options):
        for dados in PERGUNTAS:
            padrao = {"opcoes": [], "obrigatoria": True, "ativa": True, **dados}
            ordem = padrao.pop("ordem")
            Pergunta.objects.update_or_create(ordem=ordem, defaults=padrao)
        self.stdout.write(self.style.SUCCESS(f"{len(PERGUNTAS)} perguntas da avaliação"))
```

> [!warning] As perguntas são uma **proposta**
> Elas foram escritas para esta spec, e não vieram da coordenação. Antes da primeira turma real, a coordenação revisa o texto **aqui** (e vocês rodam o comando de novo) ou direto no admin.
> A **pergunta 6** ("o curso combinou com o que o quiz mostrou?") é a ponte com o TCC: é a primeira medida, vinda do próprio aluno, de se a recomendação acertou.

Rode: `python manage.py seed_avaliacao` → `7 perguntas da avaliação`.

## 4.4 `avaliacao/forms.py` (novo)

```python
from django import forms


def _campo(pergunta):
    """Um campo do Django para cada tipo de pergunta."""
    comum = {"label": pergunta.texto, "required": pergunta.obrigatoria}
    if pergunta.tipo == "nps":
        return forms.TypedChoiceField(
            choices=[(n, n) for n in range(11)], coerce=int, widget=forms.RadioSelect, **comum
        )
    if pergunta.tipo == "escala":
        return forms.TypedChoiceField(
            choices=[(n, n) for n in range(1, 6)], coerce=int, widget=forms.RadioSelect, **comum
        )
    if pergunta.tipo == "escolha":
        return forms.ChoiceField(
            choices=[(opcao, opcao) for opcao in pergunta.opcoes], widget=forms.RadioSelect, **comum
        )
    return forms.CharField(max_length=1000, widget=forms.Textarea(attrs={"rows": 4}), **comum)


class FormularioDeAvaliacao(forms.Form):
    """Montado na hora a partir das perguntas ativas: trocar o seed troca o formulário."""

    def __init__(self, perguntas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.perguntas = list(perguntas)
        for pergunta in self.perguntas:
            self.fields[f"pergunta_{pergunta.id}"] = _campo(pergunta)

    def campos_por_pergunta(self):
        """(pergunta, campo do form) na ordem, para o template saber o tipo de cada um."""
        return [(pergunta, self[f"pergunta_{pergunta.id}"]) for pergunta in self.perguntas]
```

> [!tip] 🎓 Entenda: formulário montado na hora
> Em vez de escrever um campo para cada pergunta, o form lê as perguntas **ativas do banco** e cria os campos sozinho. É por isso que trocar uma pergunta no seed ou no admin não exige mudar nenhuma linha de código.

## 4.5 `avaliacao/views.py` e `avaliacao/urls.py`

```python
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import FormularioDeAvaliacao
from .models import ItemDeResposta, LinkDeAvaliacao, Pergunta, RespostaDeAvaliacao

# Os links que este navegador já respondeu. É uma trava leve: impede o envio
# repetido sem querer (duplo clique, voltar e reenviar), mas não é um controle
# forte. Um controle forte exigiria saber quem respondeu, e aí não seria anônimo.
CHAVE_SESSAO = "avaliacoes_respondidas"


def _link_ativo(token):
    return LinkDeAvaliacao.objects.select_related("curso").filter(token=token, ativo=True).first()


def responder(request, token):
    link = _link_ativo(token)
    if link is None:
        return render(request, "avaliacao/link_invalido.html", status=404)
    if link.pk in request.session.get(CHAVE_SESSAO, []):
        return redirect("avaliacao-obrigado", token=token)

    perguntas = Pergunta.objects.filter(ativa=True)
    form = FormularioDeAvaliacao(perguntas, request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            resposta = RespostaDeAvaliacao.objects.create(link=link)
            itens = []
            for pergunta in form.perguntas:
                valor = form.cleaned_data.get(f"pergunta_{pergunta.id}")
                if valor in (None, ""):
                    continue  # pergunta opcional deixada em branco
                if pergunta.tipo in ("nps", "escala"):
                    itens.append(ItemDeResposta(resposta=resposta, pergunta=pergunta, numero=valor))
                else:
                    itens.append(ItemDeResposta(resposta=resposta, pergunta=pergunta, texto=valor.strip()))
            ItemDeResposta.objects.bulk_create(itens)

        respondidas = request.session.get(CHAVE_SESSAO, [])
        request.session[CHAVE_SESSAO] = respondidas + [link.pk]
        return redirect("avaliacao-obrigado", token=token)

    return render(request, "avaliacao/responder.html", {"link": link, "form": form})


def obrigado(request, token):
    link = LinkDeAvaliacao.objects.select_related("curso").filter(token=token).first()
    return render(request, "avaliacao/obrigado.html", {"link": link})
```

> [!note] 🎓 Entenda: a trava de "já respondeu" é leve de propósito
> Ela usa a sessão do navegador: segura o duplo clique e o "voltar e reenviar", mas outro navegador consegue responder de novo. Uma trava forte exigiria saber **quem** respondeu, e aí não seria anônimo. Para uma avaliação de turma, esse é o equilíbrio certo, e vale saber explicar isso na banca.

```python
from django.urls import path

from . import views

urlpatterns = [
    path("<uuid:token>/", views.responder, name="avaliacao-responder"),
    path("<uuid:token>/obrigado/", views.obrigado, name="avaliacao-obrigado"),
]
```

## 4.6 `avaliacao/admin.py`

```python
from django.contrib import admin

from .models import LinkDeAvaliacao, Pergunta


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ["ordem", "texto", "tipo", "obrigatoria", "ativa"]
    list_display_links = ["texto"]
    list_filter = ["tipo", "ativa"]


@admin.register(LinkDeAvaliacao)
class LinkDeAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ["curso", "turma", "criado_em", "ativo"]
    list_filter = ["ativo", "curso"]
    readonly_fields = ["token", "criado_em", "criado_por"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)

# As respostas não entram no admin de propósito: o lugar delas é o painel,
# agregado e com supressão. Uma lista resposta a resposta no admin desfaria isso.
```

### ✅ Pronta quando

- [ ] `makemigrations --check --dry-run` sem mudanças, `migrate` e `seed_avaliacao` rodados
- [ ] No admin dá para criar um **Link de avaliação**
- [ ] Você avisou: **"A: etapa 4 pronta, app avaliacao no ar"**

---

# Etapa 5 · Avaliações no painel

### O que você entrega

| Tela | Rota | Variáveis |
|---|---|---|
| Início | `painel-dashboard` | + `avaliacoes_no_periodo` (sempre) |
| Links das turmas | `painel-avaliacoes` | `links` (com `curso__nome_curso`, `turma`, `url`, `total`, `suprimido`, `ativo`, `id`), `form` (com `form.curso` e `form.turma`) |
| Resultados | `painel-avaliacoes-resultados` | `curso` (ou `None`), `avaliacoes_com_massa`, `resumo`, `cursos_avaliados`; e, com massa: `blocos`, `fora_do_todos` |
| CSV | `painel-avaliacoes-csv` | (download) |
| Ações | `painel-avaliacoes-gerar`, `painel-avaliacoes-fechar` | POST, com mensagem de sucesso ou erro |

## 5.1 As três regras de privacidade desta tela

> [!important] 🎓 Entenda: a massa mínima é de **avaliações**, e não de testes
> Um mês com 200 testes do quiz pode ter um curso com 3 avaliações, e a média de 3 pessoas sobre o instrutor delas não pode aparecer. Aqui a regra do 5 é contada **por curso, em respostas de avaliação**.

> [!danger] 🎓 Entenda: o vazamento por diferença
> Uma primeira versão mostrava, em "Todos os cursos", os gráficos com **todas** as respostas. No teste, Usinagem CNC tinha 12 respostas e Costura Industrial tinha 3:
> - a tabela mostrava o NPS de Usinagem: **50**;
> - o card de "Todos" mostrava o NPS geral: **40**.
>
> Com esses dois números, dá para **calcular** a opinião das 3 pessoas de Costura, mesmo com a linha de Costura escondida. A correção está em `cursos_com_massa`: **curso com menos de 5 avaliações não entra em nenhuma média, NPS, gráfico ou CSV**, nem no "Todos". As **contagens** seguem a regra do resto do painel.

> [!note] 🎓 Entenda: o CSV não deixa juntar as respostas de uma pessoa
> Uma linha por item (`curso;pergunta;resposta`), **sem turma, sem data e sem número da resposta**, em ordem de pergunta e de valor. As 7 respostas de um aluno ficam espalhadas por 7 blocos diferentes, e nada liga uma à outra.

## 5.2 `painel/metricas_avaliacao.py` (novo)

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

> [!tip] 🎓 Entenda: comentários em ordem alfabética
> Na ordem de chegada, o primeiro comentário seria o de quem respondeu primeiro, e numa turma todo mundo sabe quem saiu da aula antes. A ordem alfabética não diz nada.

## 5.3 `painel/forms.py` (novo)

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

## 5.4 `painel/views.py`

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
+# ---------- Avaliação de fim de curso (Etapa 5) ----------
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

> [!note] 🎓 Entenda: o `"﻿"` no CSV
> É um caractere invisível no começo do arquivo (o *BOM*). Sem ele, o Excel abre o CSV achando que não é UTF-8, e "Avaliação" vira "AvaliaÃ§Ã£o".

## 5.5 `painel/urls.py`

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

### ✅ Pronta quando

- [ ] `python manage.py check` sem problemas
- [ ] Você avisou: **"A: views da etapa 5 prontas"**
