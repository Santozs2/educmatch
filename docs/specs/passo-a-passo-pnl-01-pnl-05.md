---
title: "Passo a passo — PNL-01 a PNL-05 (painel administrativo agregado)"
aliases: ["Passo a passo PNL", "Construir o painel", "Dashboard do admin", "Fase 3 do plano v0.2", "Painel de métricas do TCC"]
tags: [tcc, painel, metricas, privacidade, django, execucao, passo-a-passo, agregacao]
status: proposto
projeto: TCC
criado: 2026-09-17
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel e refino]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-v02|🗺️ Plano v0.2]] · Vem depois de: [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 REC-01 a REC-06]] · Front: [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Templates]]

# 📊 Passo a passo — PNL-01 a PNL-05

> [!abstract] O que esta nota é
> O **como** da Fase 3: o app `painel/`, as consultas de agregação, a regra de privacidade e a tela. Um PR só.
> O painel responde perguntas sobre **o catálogo e a demanda** — nunca sobre pessoas. Essa frase não é abertura bonita: é o requisito que decide o desenho de cada consulta desta nota.

> [!warning] Nada disto foi executado
> Escrito contra a [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|spec do painel]], que já define métricas, consultas e estrutura de arquivos. O que esta nota acrescenta é a ordem de execução, o código completo, as armadilhas de agregação e os testes. **Confirme os nomes de campo reais** — `related_name` e nomes de coluna vêm das notas, não do repositório.

> [!danger] Esta fase exige a Fase 2 mesclada. Não é preferência, é pré-requisito
> Cada métrica do painel depende de uma correção da REC:
> | Métrica | Depende de |
> |---|---|
> | Conversão por período | `REC-01` — `criado_em` deixou de ser `auto_now` |
> | Demanda por área | `REC-03` — `explicacao` virou `JSONField` |
> | Top cursos em 1º lugar | `REC-02` — curso inativo saiu do cálculo |
> | Distribuição de confiança | `REC-04` — a confiança passou a discriminar |
> | Aderência à recomendação | `REC-06` — `rank_snapshot` e `era_principal` existem |
>
> Construir antes é construir cinco números errados e refazer os cinco.

---

## 🚦 Antes de abrir o editor

```bash
git checkout main && git pull
git checkout -b feat/dash-painel
```

Confirme que a Fase 2 está dentro:

```bash
./.venv/Scripts/python.exe manage.py shell -c "from accounts.models import Interesse; print([f.name for f in Interesse._meta.fields])"
```

Tem de aparecer `afinidade_snapshot`, `rank_snapshot`, `era_principal` e `atualizado_em`. Se não aparecer, a Fase 2 não foi mesclada — pare aqui.

---

## 1️⃣ A regra de privacidade, antes da primeira consulta

Definir isto agora evita refazer depois, e rende seção própria na monografia. São cinco regras, e cada uma vira código nesta nota.

| Regra | Onde ela aparece no código |
|---|---|
| **Nenhuma consulta toca `user` nem `respondido_por`** | `metricas.py` — nenhuma função recebe usuário |
| **Sem *drill-down***: nenhum número é clicável | `dashboard.html` — zero `<a>` em número |
| **k-anonimato, k = 5**: célula com menos de 5 respondentes exibe `—` | `privacidade.py` |
| **Contagem por tentativa, não por usuário** | `distinct=True` sobre `tentativa_id` |
| **Período mínimo**: menos de 5 tentativas no período → só o total | `privacidade.py` |

> [!danger] Por que k-anonimato num TCC de escola, e não "só entre a gente"
> *"1 pessoa deu match com Fundição Artística nesta semana"*, combinado com qualquer contexto externo — quem faltou, quem comentou, quem é o único aluno do turno da noite — **identifica alguém**. Agregação com célula de tamanho 1 não é anonimização; é um dado pessoal com uma camada de tinta.
> O `respondido_por` é pior ainda: é texto livre digitado pelo aluno. Tratar como dado pessoal e manter **fora do painel por completo** é mais simples do que decidir caso a caso — e é defensável na banca em uma frase.

> [!important] O admin que precisa ver um caso individual usa o `/admin`
> Não é limitação, é desenho. O Django admin já registra quem é *staff* e já tem histórico de acesso. Duplicar essa capacidade no painel seria construir um segundo caminho para o dado individual, com metade dos controles.

---

## 2️⃣ PNL-01 — o app e os índices

```bash
./.venv/Scripts/python.exe manage.py startapp painel
```

Apague `painel/models.py`, `painel/tests.py` e `painel/views.py` gerados em branco — a estrutura desta fase é outra:

```
painel/
├── __init__.py
├── apps.py
├── metricas.py           # agregações puras, sem HTTP — testáveis
├── privacidade.py        # aplica k-anonimato ao resultado
├── urls.py
├── views.py              # @staff_member_required, nada de lógica
├── templates/painel/
│   └── dashboard.html
└── tests/
    ├── __init__.py
    ├── test_metricas.py
    └── test_privacidade.py
```

> [!important] `metricas.py` não importa `request`, e isso é o ponto inteiro da estrutura
> Toda função de `metricas.py` recebe datas e devolve dados. Nenhuma sabe que existe HTTP, sessão ou usuário logado. Consequência: os números são **testáveis sem cliente de teste** — e é isso que permite a suíte da PNL-05 existir.
> É a mesma decisão do motor, que separou funções puras do ORM e por isso pôde ser testado sem abrir banco ([[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]]). Um parágrafo pronto para a monografia: *a mesma disciplina arquitetural se pagou duas vezes, em duas camadas diferentes.*

### `core/settings.py`

```python
INSTALLED_APPS = [
    ...
    "quiz",
    "catalogo",
    "accounts",
    "painel",
]
```

### `core/urls.py`

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("painel/", include("painel.urls")),
    path("api/quiz/", include("quiz.urls")),
    path("", include("accounts.urls")),
    path("", include("quiz.web_urls")),
]
```

> [!note] `painel/` antes de quem registra a raiz
> Não há conflito real — os prefixos são diferentes. Manter quem tem prefixo antes de quem registra `""` é a ordem que não dá surpresa quando alguém acrescentar rota nova, e é a mesma convenção já adotada na [[Projetos/EducMatch(Secretária)/passo-a-passo-aut-01-aut-03|AUT-02]].

### Os dois índices — sem eles o painel fica lento e ninguém sabe por quê

```python
# quiz/models.py
class Tentativa_de_resposta(models.Model):
    ...
    class Meta:
        indexes = [models.Index(fields=["criado_em"], name="idx_tentativa_criado_em")]


class Recomendacao(models.Model):
    ...
    class Meta:
        indexes = [models.Index(fields=["rank", "curso"], name="idx_rec_rank_curso")]
```

```bash
./.venv/Scripts/python.exe manage.py makemigrations quiz -n indices_do_painel
```

> [!warning] Todo filtro do painel passa por esses dois índices
> Sem eles, o `JOIN` de `Recomendacao` para `Tentativa_de_resposta` vira varredura completa assim que a tabela crescer — e ela vai crescer no dia em que a turma responder o quiz, que é exatamente o dia em que alguém vai querer abrir o painel na frente de outra pessoa.
> Dois índices custam uma migração e alguns kilobytes. É a otimização com melhor relação custo-benefício do projeto inteiro.

> [!tip] Isto também é medível, como o N+1 da REC-05
> `manage.py shell` com `connection.queries` e um `EXPLAIN` antes e depois dá o segundo parágrafo de otimização medida da monografia. No MySQL, `EXPLAIN ANALYZE <consulta>` roda no `manage.py dbshell` ou no Workbench, e mostra se o índice foi usado (`index lookup`) ou se virou varredura (`table scan`).

---

## 3️⃣ PNL-02 — `metricas.py`

### `painel/metricas.py`

```python
"""Agregacoes do painel. Nenhuma funcao aqui conhece request, sessao ou usuario.

Regra do modulo: nenhuma consulta toca `user` nem `respondido_por`.
Quem precisar de caso individual usa o /admin.
"""

from collections import Counter
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from accounts.models import Interesse
from catalogo.models import Area, Curso
from quiz.models import Peso_alternativa, Recomendacao, Tentativa_de_resposta

PERIODOS = {"30": 30, "90": 90, "365": 365}


def inicio_do_periodo(dias):
    """None significa 'desde o comeco'."""
    if dias is None:
        return None
    return timezone.now() - timedelta(days=dias)


def _no_periodo(inicio, prefixo="criado_em"):
    """Monta o filtro temporal, ou um filtro vazio quando o periodo e 'tudo'."""
    if inicio is None:
        return Q()
    return Q(**{f"{prefixo}__gte": inicio})


def total_de_tentativas(inicio):
    return Tentativa_de_resposta.objects.filter(_no_periodo(inicio)).count()


def top_cursos_em_primeiro(inicio, limite=10):
    """Qual curso o instrumento mais indica como 1a opcao."""
    return list(
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", "curso__nome_curso")
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "curso__nome_curso")[:limite]
    )


def top_cursos_no_top5(inicio, limite=10):
    """Quais aparecem no resultado, mesmo sem vencer."""
    return list(
        Recomendacao.objects
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values("curso_id", "curso__nome_curso")
        .annotate(total=Count("tentativa_id", distinct=True))
        .order_by("-total", "curso__nome_curso")[:limite]
    )


def conversao_por_curso(inicio):
    """De quem viu o curso recomendado, quantos salvaram na lista.

    Os dois Count usam distinct=True por necessidade, nao por estilo -- ver
    o aviso da nota. Sem isso os dois JOIN se multiplicam e os numeros incham.
    """
    linhas = (
        Curso.objects
        .filter(is_active=True)
        .annotate(
            recomendado=Count(
                "recomendacoes",
                filter=_no_periodo(inicio, "recomendacoes__tentativa__criado_em"),
                distinct=True,
            ),
            interessados=Count(
                "interessados",
                filter=_no_periodo(inicio, "interessados__criado_em"),
                distinct=True,
            ),
        )
        .values("id", "nome_curso", "recomendado", "interessados")
        .order_by("-interessados", "nome_curso")
    )

    resultado = []
    for linha in linhas:
        recomendado = linha["recomendado"]
        linha["taxa"] = (linha["interessados"] / recomendado * 100) if recomendado else None
        resultado.append(linha)
    return resultado


def aderencia_a_recomendacao(inicio):
    """Quando salvou, salvou o 1o colocado ou desceu no ranking? (C4)"""
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
    """Para onde o perfil da turma aponta. Le o JSONField da REC-03."""
    explicacoes = (
        Recomendacao.objects
        .filter(rank=1)
        .filter(_no_periodo(inicio, "tentativa__criado_em"))
        .values_list("explicacao", flat=True)
    )

    contagem = Counter()
    for explicacao in explicacoes:
        if isinstance(explicacao, dict):
            contagem.update(explicacao.keys())

    nomes = dict(Area.objects.values_list("slug", "nome"))
    return [
        {"area": nomes.get(slug, slug), "total": total}
        for slug, total in contagem.most_common(limite)
    ]


def cursos_nunca_recomendados():
    """Lacuna de catalogo ou de questao. Sem recorte de periodo, de proposito."""
    return list(
        Curso.objects
        .filter(is_active=True, recomendacoes__isnull=True)
        .values("id", "nome_curso")
        .order_by("nome_curso")
    )


def distribuicao_de_confianca(inicio):
    """O teste esta separando bem? Depende da REC-04."""
    return list(
        Tentativa_de_resposta.objects
        .filter(_no_periodo(inicio))
        .values("confidence_level")
        .annotate(total=Count("id"))
        .order_by("confidence_level")
    )


def cobertura_de_areas():
    """Que area nenhuma questao alcanca. Nao e bug, e limitacao de conteudo."""
    return list(
        Area.objects
        .annotate(alternativas=Count("pesos_alternativa", distinct=True))
        .values("slug", "nome", "alternativas")
        .order_by("alternativas", "nome")
    )
```

> [!danger] Os dois `Count` da `conversao_por_curso` e o bug que incha todos os números
> `annotate()` com **duas** contagens sobre **duas** relações diferentes faz o SQL juntar as duas tabelas na mesma consulta. O banco produz o produto cartesiano: um curso com 8 recomendações e 3 interesses gera 24 linhas, e sem `distinct=True` a contagem devolve `recomendado=24` e `interessados=24`.
> O sintoma é traiçoeiro: os números **parecem plausíveis** — só estão grandes. Ninguém desconfia de um painel que mostra 24 em vez de 8.
> `distinct=True` resolve para `Count`. **Não resolve para `Sum` e `Avg`** — lá o produto cartesiano soma valores repetidos e `distinct` não tem como saber o que deduplicar. Se em algum momento o painel precisar de uma média sobre duas relações, faça **duas consultas separadas** e junte em Python. É o erro de agregação número um do Django, e agora está escrito.

> [!warning] `Count("tentativa_id", distinct=True)` e não `Count("id")`
> A regra de privacidade diz *"contagem por tentativa, não por usuário"*. `Count("id")` conta **linhas de `Recomendacao`** — e se um dia o recálculo gravar duas recomendações do mesmo curso na mesma tentativa, o número infla sem aviso. Contar tentativas distintas é o que a métrica afirma medir.

> [!danger] A mina desta fase: filtro por data devolvendo **vazio, sem erro**
> Se a `INF-04` não foi feita, as tabelas de fuso do MySQL estão vazias. Com `USE_TZ = True` e `TIME_ZONE = "America/Sao_Paulo"`, o Django traduz fuso **dentro do SQL** com `CONVERT_TZ()` — que nesse estado devolve `NULL`. Resultado: `__date`, `__year`, `__month`, `__hour`, `TruncDate` e `TruncMonth` passam a **devolver vazio**, sem exceção nenhuma.
> Confira antes de desconfiar do seu código:
> ```sql
> SELECT CONVERT_TZ(NOW(), 'UTC', 'America/Sao_Paulo');   -- NULL = tabelas vazias
> ```
> **O que salva as funções acima é que elas usam `criado_em__gte=<datetime>`**, comparação direta que não passa por `CONVERT_TZ`. É por isso que o painel funciona mesmo com as tabelas vazias — e é exatamente o que torna a mina perigosa: metade das consultas funciona. No dia em que alguém acrescentar um gráfico "tentativas por dia" com `TruncDate`, ele nasce vazio e parece bug de template.
> Ver [[Projetos/EducMatch(Secretária)/passo-a-passo-inf-01-inf-05|🧱 INF-04]], e o teste `test_mysql_conhece_o_fuso_de_sao_paulo`, que já está no repositório guardando isso.

> [!warning] `ONLY_FULL_GROUP_BY` — o modo padrão do MySQL 8 que recusa agregação frouxa
> ```
> OperationalError: (1055, "Expression #N of SELECT list is not in GROUP BY clause...")
> ```
> Aparece quando um `.values().annotate()` seleciona coluna que não está no agrupamento. As funções acima não caem nisso porque cada `.values()` lista explicitamente o que agrupa — **manter essa disciplina é o que evita a mensagem**. A tentação, ao ver esse erro, é desligar o `ONLY_FULL_GROUP_BY` no MySQL; não faça: ele está ligado porque agregação ambígua devolve um valor **arbitrário** entre os do grupo, e num painel isso é número errado com cara de certo.

> [!note] `demanda_por_area` agrega em Python, e isto é escolha consciente
> O MySQL 8 sabe percorrer chaves de JSON com `JSON_TABLE`, mas isso exigiria `RawSQL` e amarraria o painel ao banco — e o MySQL não indexa chave de JSON sem coluna gerada. Com algumas centenas de tentativas, trazer os dicionários e usar `Counter` é instantâneo e legível por qualquer um do grupo.
> A hora de trocar é quando a consulta passar de um segundo — e aí a otimização será medida, o que é melhor do que otimizar por antecipação. Se alguém perguntar na banca, esta é a resposta.

> [!warning] `cobertura_de_areas` precisa do `related_name` real
> O `pesos_alternativa` acima é um chute a partir de `Peso_alternativa`. Confirme:
> ```bash
> ./.venv/Scripts/python.exe manage.py shell -c "from catalogo.models import Area; print([r.get_accessor_name() for r in Area._meta.related_objects])"
> ```
> Esta métrica é a que justifica o trabalho da F3: ela mostra, com número, que **6 das 12 áreas não têm nenhuma questão** — e portanto que 8 cursos não conseguem ser 1º colocados a partir de nenhum perfil típico.

---

## 4️⃣ PNL-03 — `privacidade.py`

### `painel/privacidade.py`

```python
"""k-anonimato aplicado depois da agregacao, num lugar so.

Regra: celula com menos de K_MINIMO respondentes nao e exibida.
"""

K_MINIMO = 5
SUPRIMIDO = None


def suprimir_pequenos(linhas, campo="total", k=K_MINIMO):
    """Zera o valor das celulas pequenas em vez de esconder a linha.

    Esconder a linha inteira vazaria informacao por omissao: quem sabe que o
    catalogo tem 20 cursos e ve 17 na tabela descobriu que os outros 3 tem
    entre 1 e 4 respondentes.
    """
    resultado = []
    for linha in linhas:
        copia = dict(linha)
        if copia.get(campo) is not None and copia[campo] < k:
            copia[campo] = SUPRIMIDO
            copia["suprimido"] = True
        resultado.append(copia)
    return resultado


def periodo_tem_massa_suficiente(total_de_tentativas, k=K_MINIMO):
    """Menos de k tentativas no periodo: exibe so o total, suprime o resto."""
    return total_de_tentativas >= k
```

> [!important] Suprimir o **valor**, não a linha — e isto é o detalhe que separa k-anonimato de teatro
> Se a tabela mostra 17 cursos e o grupo sabe que o catálogo tem 20, quem lê descobriu que os três ausentes têm entre 1 e 4 respondentes. A informação vazou **pela omissão**.
> Mantendo as 20 linhas e trocando os valores pequenos por `—`, o leitor sabe que existe um valor e não sabe qual. É a diferença entre um controle que funciona e um que parece funcionar.

> [!warning] A supressão é do lado do servidor, não do template
> Se o valor real chegar no contexto e o template decidir não mostrar, ele está no HTML — ou no `view-source`, ou numa resposta de API futura. Suprimir em `privacidade.py`, **antes** de montar o contexto, é o que garante que o número pequeno não sai do processo.

> [!note] `K_MINIMO = 5` é escolha, e escolha citável
> Cinco é o valor convencional para micro-dados educacionais e é o que a [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|spec]] fixou. O que importa para a monografia é que o número está **numa constante com nome**, num módulo cujo nome diz o que ele faz — então a decisão é rastreável no `git log` e citável no texto. Ver [[Conceitos/Metodologia Científica/met-validade-e-limitacoes|⚖️ Validade e limitações]].

---

## 5️⃣ PNL-04 — a view e a tela

### `painel/views.py`

```python
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from painel import metricas, privacidade


@staff_member_required
def dashboard(request):
    escolhido = request.GET.get("periodo", "90")
    dias = metricas.PERIODOS.get(escolhido)          # chave invalida -> None -> tudo
    inicio = metricas.inicio_do_periodo(dias)

    total = metricas.total_de_tentativas(inicio)
    tem_massa = privacidade.periodo_tem_massa_suficiente(total)

    contexto = {
        "periodo": escolhido,
        "periodos": metricas.PERIODOS,
        "total_de_tentativas": total,
        "tem_massa": tem_massa,
        "k_minimo": privacidade.K_MINIMO,
    }

    if tem_massa:
        contexto.update({
            "top_primeiro": privacidade.suprimir_pequenos(
                metricas.top_cursos_em_primeiro(inicio)
            ),
            "top_cinco": privacidade.suprimir_pequenos(
                metricas.top_cursos_no_top5(inicio)
            ),
            "conversao": privacidade.suprimir_pequenos(
                metricas.conversao_por_curso(inicio), campo="interessados"
            ),
            "aderencia": metricas.aderencia_a_recomendacao(inicio),
            "demanda_por_area": privacidade.suprimir_pequenos(
                metricas.demanda_por_area(inicio)
            ),
            "confianca": metricas.distribuicao_de_confianca(inicio),
            "orfaos": metricas.cursos_nunca_recomendados(),
            "cobertura": metricas.cobertura_de_areas(),
        })

    return render(request, "painel/dashboard.html", contexto)
```

### `painel/urls.py`

```python
from django.urls import path

from painel.views import dashboard

urlpatterns = [path("", dashboard, name="painel-dashboard")]
```

> [!warning] `@staff_member_required` não usa o seu `LOGIN_URL`
> Ele manda quem não é *staff* para a tela de login **do `/admin`**, não para `/entrar/`. Aqui isso é o comportamento correto — o painel é ferramenta de administração, e o `/admin` já é onde o *staff* entra. Mas é surpresa se você esperava a tela do projeto, e a pessoa que testar vai achar que errou a URL.
> A alternativa (`@login_required` + checagem de `is_staff` na view) usaria o `LOGIN_URL`, e custa a checagem escrita à mão em toda view nova — e uma checagem escrita à mão é uma checagem que alguém esquece.

> [!danger] Usuário logado comum tem de **não** ver o painel. E isso precisa ser um teste
> O `C5` já ensinou a disciplina: a regra de acesso é o que sobrevive quando os nomes derivam ([[contratos-c1-a-c6 🟢|📜 C5]]). Um `@staff_member_required` esquecido numa view nova do painel não quebra nada, não dá erro e não aparece em revisão — só expõe. O teste da PNL-05 percorre **todas** as rotas do app.

### `painel/templates/painel/dashboard.html`

```html
{% extends "base.html" %}

{% block title %}Painel{% endblock %}

{% block conteudo %}
<section class="painel">
    <p class="olho">Visao agregada</p>
    <h1 class="titulo">Painel</h1>

    <nav class="painel__periodo">
        {% for chave, dias in periodos.items %}
            <a class="botao {% if periodo == chave %}botao--principal{% else %}botao--fantasma{% endif %}"
               href="?periodo={{ chave }}">{{ dias }} dias</a>
        {% endfor %}
        <a class="botao {% if periodo == 'tudo' %}botao--principal{% else %}botao--fantasma{% endif %}"
           href="?periodo=tudo">Tudo</a>
    </nav>

    <p class="painel__numerao">{{ total_de_tentativas }}</p>
    <p class="campo__dica">tentativas no periodo</p>

    {% if not tem_massa %}
        <p class="alerta" role="status">
            Menos de {{ k_minimo }} tentativas neste periodo. Para preservar o anonimato
            dos respondentes, so o total e exibido. Escolha um periodo maior.
        </p>
    {% else %}

    <h2 class="painel__secao">Cursos mais indicados em 1o lugar</h2>
    <table class="tabela">
        <thead><tr><th>Curso</th><th>Tentativas</th></tr></thead>
        <tbody>
        {% for linha in top_primeiro %}
            <tr>
                <td>{{ linha.curso__nome_curso }}</td>
                <td>
                    {% if linha.suprimido %}&mdash;{% else %}
                        <span class="barra" style="--n: {{ linha.total }}"></span>
                        {{ linha.total }}
                    {% endif %}
                </td>
            </tr>
        {% empty %}
            <tr><td colspan="2">Nenhuma tentativa no periodo.</td></tr>
        {% endfor %}
        </tbody>
    </table>

    <h2 class="painel__secao">Conversao: recomendado &rarr; salvo na lista</h2>
    <table class="tabela">
        <thead><tr><th>Curso</th><th>Recomendado</th><th>Salvaram</th><th>Taxa</th></tr></thead>
        <tbody>
        {% for linha in conversao %}
            <tr>
                <td>{{ linha.nome_curso }}</td>
                <td>{{ linha.recomendado }}</td>
                <td>{% if linha.suprimido %}&mdash;{% else %}{{ linha.interessados }}{% endif %}</td>
                <td>
                    {% if linha.suprimido or linha.taxa is None %}&mdash;
                    {% else %}{{ linha.taxa|floatformat:1 }}%{% endif %}
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>

    <h2 class="painel__secao">Cursos ativos que nunca foram recomendados</h2>
    {% if orfaos %}
        <ul class="lista">
        {% for curso in orfaos %}<li>{{ curso.nome_curso }}</li>{% endfor %}
        </ul>
        <p class="campo__dica">
            Curso que nunca aparece costuma indicar area sem questao no quiz,
            nao curso ruim. Ver a cobertura de areas abaixo.
        </p>
    {% else %}
        <p>Todos os cursos ativos ja apareceram em alguma recomendacao.</p>
    {% endif %}

    <h2 class="painel__secao">Cobertura de areas pelo quiz</h2>
    <table class="tabela">
        <thead><tr><th>Area</th><th>Alternativas que pontuam nela</th></tr></thead>
        <tbody>
        {% for area in cobertura %}
            <tr class="{% if not area.alternativas %}linha--alerta{% endif %}">
                <td>{{ area.nome }}</td>
                <td>{{ area.alternativas }}</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>

    <p class="campo__dica">
        Numeros agregados por tentativa, incluindo respostas anonimas. Celulas com
        menos de {{ k_minimo }} respondentes aparecem como &mdash;. Este painel nao
        exibe nome, e-mail nem resposta individual.
    </p>
    {% endif %}
</section>
{% endblock %}
```

### `static/css/style.css` — no fim do arquivo

```css
.painel__numerao {
    font-size: 3rem;
    font-weight: 700;
    line-height: 1;
    margin: 0;
}

.painel__secao {
    margin-top: 2.5rem;
    font-size: 1.125rem;
}

.painel__periodo {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.tabela {
    width: 100%;
    border-collapse: collapse;
}

.tabela th,
.tabela td {
    text-align: left;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

/* Barra proporcional em CSS puro: --n vem do template, sem biblioteca. */
.barra {
    display: inline-block;
    height: 0.5rem;
    width: calc(var(--n) * 0.5rem);
    max-width: 12rem;
    background: currentColor;
    opacity: 0.35;
    border-radius: 2px;
    margin-right: 0.5rem;
    vertical-align: middle;
}

.linha--alerta td {
    background: rgba(200, 120, 0, 0.08);
}
```

> [!success] Barra em CSS puro, sem biblioteca de gráfico
> A stack do projeto é *templates Django + CSS puro + JavaScript vanilla* ([[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]]). Acrescentar Chart.js por causa de quatro tabelas seria trocar uma decisão registrada por conveniência, e trazer uma dependência que precisa ser explicada na banca.
> `width: calc(var(--n) * 0.5rem)` com `max-width` entrega o essencial: comparação visual imediata. Se o painel algum dia pedir gráfico de verdade, isso é uma decisão nova, com justificativa nova.

> [!warning] `periodo=tudo` não está em `PERIODOS` — e é isso que faz funcionar
> `metricas.PERIODOS.get("tudo")` devolve `None`, `inicio_do_periodo(None)` devolve `None`, e `_no_periodo(None)` devolve um `Q()` vazio, que o Django ignora. Uma chave inválida qualquer (`?periodo=xyz`) cai no mesmo caminho e mostra tudo — sem erro 500, sem validação extra.
> Se preferir recusar valor inválido, é `if escolhido not in PERIODOS and escolhido != "tudo": raise Http404`. As duas são defensáveis; o que não é defensável é um `int(request.GET["periodo"])` cru, que dá 500 com `?periodo=abc` — e alguém **vai** digitar isso.

---

## 6️⃣ PNL-05 — os testes

Três grupos: os números, a privacidade e o acesso.

### `painel/tests/test_metricas.py`

```python
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from painel import metricas


class MetricasTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        silencio = StringIO()
        for comando in ("seed_areas", "seed_cursos", "seed_questoes"):
            call_command(comando, stdout=silencio)

    def test_conversao_nao_infla_com_dois_joins(self):
        """O bug do produto cartesiano: dois Count sobre duas relacoes.

        Um curso com 3 recomendacoes e 2 interesses tem que devolver 3 e 2 --
        nao 6 e 6.
        """
        curso = self.criar_curso_com(recomendacoes=3, interesses=2)

        linha = next(
            l for l in metricas.conversao_por_curso(None) if l["id"] == curso.id
        )

        self.assertEqual(linha["recomendado"], 3)
        self.assertEqual(linha["interessados"], 2)

    def test_demanda_por_area_le_o_jsonfield(self):
        """Depende da REC-03: com TextField isto nao era possivel."""
        self.criar_tentativa_com_explicacao({"eletrica": 0.6, "ti": 0.2})

        demanda = metricas.demanda_por_area(None)

        self.assertTrue(any(d["total"] >= 1 for d in demanda))

    def test_curso_inativo_nao_entra_na_conversao(self):
        """Depende da REC-02."""
        inativo = self.criar_curso(is_active=False)
        ids = [linha["id"] for linha in metricas.conversao_por_curso(None)]
        self.assertNotIn(inativo.id, ids)

    def test_cobertura_acusa_area_sem_questao(self):
        """A metrica que justifica o trabalho da F3."""
        sem_questao = [a for a in metricas.cobertura_de_areas() if a["alternativas"] == 0]
        self.assertTrue(sem_questao, "nenhuma area sem questao: confira o related_name")
```

### `painel/tests/test_privacidade.py`

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from painel.privacidade import K_MINIMO, suprimir_pequenos


class SupressaoTest(TestCase):
    def test_celula_pequena_e_suprimida_mas_a_linha_fica(self):
        linhas = [{"nome": "A", "total": 9}, {"nome": "B", "total": 2}]

        saida = suprimir_pequenos(linhas)

        self.assertEqual(len(saida), 2, "esconder a linha vazaria pela omissao")
        self.assertEqual(saida[0]["total"], 9)
        self.assertIsNone(saida[1]["total"])
        self.assertTrue(saida[1]["suprimido"])

    def test_a_funcao_nao_altera_a_entrada(self):
        linhas = [{"nome": "B", "total": 2}]
        suprimir_pequenos(linhas)
        self.assertEqual(linhas[0]["total"], 2)


class AcessoAoPainelTest(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.comum = Usuario.objects.create_user(email="aluno@exemplo.com", password="x-2026-y")
        self.staff = Usuario.objects.create_user(
            email="coord@exemplo.com", password="x-2026-y", is_staff=True
        )

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

    def test_nenhum_nome_de_respondente_aparece_na_pagina(self):
        """A regra de privacidade, verificada no HTML servido."""
        self.criar_tentativas(nomes=["Ana Zoraide", "Bento Kling", "Cleo Vasquez"])
        self.client.force_login(self.staff)

        corpo = self.client.get(reverse("painel-dashboard")).content.decode()

        for nome in ("Ana Zoraide", "Bento Kling", "Cleo Vasquez"):
            self.assertNotIn(nome, corpo)
```

> [!important] `test_nenhum_nome_de_respondente_aparece_na_pagina` é o teste mais valioso do painel
> Os outros verificam que os números estão certos. Este verifica a **promessa** — e é a única coisa no repositório que defende a regra de privacidade sozinha, contra a mudança futura de quem vai querer "só mostrar quem respondeu, para conferir".
> Ele é o análogo exato do `test_quiz_anonimo_continua_respondendo` da [[Projetos/EducMatch(Secretária)/passo-a-passo-aut-01-aut-03|AUT-01]]: parece bobo hoje, e existe para o dia em que alguém, com pressa e boa intenção, cruzar uma linha que ninguém está olhando.

> [!warning] `test_conversao_nao_infla_com_dois_joins` tem de falhar sem o `distinct=True`
> Antes de considerar a fase pronta, **apague os dois `distinct=True`** e rode só este teste. Se ele continuar verde, o cenário que você montou não tem recomendações e interesses suficientes para o produto cartesiano aparecer — e o teste não está medindo nada. Três recomendações e dois interesses no mesmo curso é o mínimo que revela.

---

## 7️⃣ Verificação

```bash
./.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe manage.py test painel
./.venv/Scripts/python.exe manage.py runserver 8010
```

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | `/painel/` deslogado | Manda para o login do `/admin`, **não** mostra número |
| 2 | `/painel/` logado como usuário comum | **Não** abre |
| 3 | `/painel/` logado como *staff* | Abre com o total e as quatro tabelas |
| 4 | Banco com menos de 5 tentativas | Só o total + o aviso de anonimato |
| 5 | Trocar o período (30 / 90 / 365 / Tudo) | Os números **mudam** — se não mudarem, o filtro não está chegando |
| 6 | `?periodo=abc` na URL | Abre normalmente (mostra tudo), não 500 |
| 7 | `/admin` → desativar um curso → recarregar o painel | O curso sai da conversão |
| 8 | Conferir "cursos nunca recomendados" | A lista bate com as áreas de cobertura zero |
| 9 | Ler a página inteira procurando nome de pessoa | Nenhum |

> [!important] O clique 5 é o que pega o erro mais comum desta fase
> Filtro temporal que não filtra é um bug silencioso: a tela abre, os números aparecem, e estão todos "desde sempre". Se `30 dias` e `Tudo` mostram o mesmo número num banco que tem tentativa antiga, o `inicio` não está chegando na consulta — provavelmente porque um `_no_periodo` ficou de fora de uma das funções.

> [!warning] O clique 4 exige um banco pequeno de propósito
> Com banco local por pessoa (**D1** do plano), é o cenário natural: quem ainda não respondeu o quiz muitas vezes tem menos de 5 tentativas e vê a supressão funcionando. Se o seu banco já passou disso, o jeito de reproduzir é o inverso — subir o `K_MINIMO` temporariamente num `shell` e conferir que a tela suprime. Não apague tentativas para testar.

---

## 8️⃣ Commit, push, PR e o recado

```bash
git add -A
git commit -m "feat(painel): dashboard agregado com k-anonimato e recorte por periodo"
git push -u origin feat/dash-painel
```

```markdown
## O que muda
App `painel/` novo, rota `/painel/` protegida por staff. Oito metricas agregadas
sobre catalogo e demanda, com k-anonimato (k=5) e recorte por periodo.
Mais dois indices (Tentativa.criado_em e Recomendacao.rank+curso).

## Por quê
Entrega a PNL da spec do painel. Responde "qual curso o instrumento mais indica",
"o curso indicado interessa de fato" e "que area nenhuma questao alcanca".

## Como testar
manage.py migrate
manage.py test painel
/painel/ deslogado -> vai pro login; como usuario comum -> nao abre; como staff -> abre

## Toca contrato de outra frente? ( ) sim (x) nao -- o painel so le
```

Recado para o grupo:

> Subi o PR da `feat/dash-painel`: tem painel em `/painel/`, e ele abre **só para quem é *staff***.
>
> ```
> git checkout main && git pull
> ```
>
> ```
> ./.venv/Scripts/python.exe manage.py migrate
> ```
>
> A migração é só de índice (deixa o painel rápido), sem mudança de campo. Cada um roda no próprio MySQL.
>
> **Para ver o painel, sua conta precisa ser *staff*.** Me chame que eu marco, ou marque você mesmo no `/admin` → Usuários → sua conta → ✅ *Membro da equipe*.
>
> **O que o painel mostra:** tentativas no período, cursos mais indicados, conversão recomendado → salvo, cursos que nunca foram recomendados e cobertura de áreas pelo quiz.
>
> **O que ele não mostra, de propósito:** nome, e-mail ou resposta de ninguém. Nenhum número é clicável até chegar numa pessoa, e célula com menos de 5 respondentes aparece como `—`. Isso é requisito, não falta de tempo — quem precisar de um caso individual usa o `/admin`.
>
> 📌 **F3, olha a última tabela:** ela mostra, com número, quantas áreas não têm **nenhuma** questão no quiz. Os cursos dessas áreas aparecem na lista de "nunca recomendados" — não porque sejam ruins, mas porque nenhum perfil consegue chegar neles. É a medida do tamanho do trabalho de questões novas.

---

## ▶️ Próxima ação

**Fase 4 — TST-01 a TST-05.** A suíte de conformidade de contrato: `C3` (os três endpoints em 500), `C5` (a matriz de rotas e autorização), `C6` (o *claim* que nunca foi implementado) e a CI que roda tudo isso a cada PR — o que faltava quando a suíte anterior se perdeu.

Ver [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|🧪 Passo a passo TST-01 a TST-05]].

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel e refino]] — o que e o porquê destas métricas
- [[Projetos/EducMatch(Secretária)/plano-execucao-v02|🗺️ Plano v0.2]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 Fase 2 — pré-requisito desta]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|🧪 Fase 4 — testes por contrato]]
- [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Front em templates Django]] — as classes de CSS reaproveitadas
- [[Projetos/EducMatch(Secretária)/catalogo-areas-e-cursos|📚 Catálogo]] — o que a cobertura de áreas mede
- [[contratos-c1-a-c6 🟢|📜 C4]] — a origem de `rank_snapshot` e `era_principal`
- **Conceitos:** [[ORM|ORM]] · [[Views|Views]] · [[Banco de Dados|Banco de Dados]]
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]] · [[Projetos|🚀 Projetos]]
