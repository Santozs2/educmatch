---
title: "Spec do dashboard — Pessoa B · Telas"
aliases: ["Dashboard pessoa B", "Spec B dashboard", "Telas do painel"]
tags: [tcc, painel, dashboard, avaliacao, templates, html, acessibilidade, spec, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-10-01
---

> [!info] Mapa: [[guia-dashboard-live-share|🖥️ Guia do grupo]] · Colegas: [[spec-dashboard-pessoa-a-dados|🧮 A · Dados]] · [[spec-dashboard-pessoa-c-estilo-e-testes|🎨 C · Estilo e testes]]

# 🖼️ Pessoa B · Telas

> [!abstract] A sua missão
> Você decide **onde cada coisa aparece**. Escreve todos os templates: a casca do painel (menu, barra do topo, menu do celular), cada tela do painel e as telas do aluno na avaliação.
> Você é dona de todo arquivo `.html`. Você **usa** as variáveis que A manda (o contrato está no começo de cada etapa) e as **classes** que C estiliza (lista no [[guia-dashboard-live-share|guia]]).

> [!tip] Como ler esta spec
> Cada etapa tem: as variáveis que você vai receber, os templates na ordem em que convém escrever, um **🎓 Entenda** e um **✅ Pronta quando**. Você não precisa esperar A terminar para começar: escreva usando os nomes do contrato. A tela só vai **abrir** no navegador quando a view de A estiver pronta.

> [!warning] As duas regras que valem em todo template seu
> 1. **Nenhum botão fantasma.** Use só `botao`, `botao--secundario`, `botao--suave`, `botao--neutro` e `botao--perigo`. Nunca `botao--contorno` nem `botao--texto` no painel: um teste de C reprova.
> 2. **Nada de `style=""`**, a não ser a largura de barra (`style="width: …%"`), que é um dado. Estilo é com C, no CSS.

---

## 🧭 O mapa

| Etapa | Arquivos seus |
|---|---|
| **1** | `templates/base.html` (uma linha), `painel/templates/painel/base_painel.html`, `inicio.html`, `quiz.html`, `_ranking.html`, `_celula.html`, `_sem_massa.html`; apagar `dashboard.html` |
| **2** | `base_painel.html` (menu), `cursos.html`, `links.html`, `interesse.html` |
| **3** | `quiz.html` (4 KPIs) |
| **4** | `avaliacao/templates/avaliacao/`: `responder.html`, `obrigado.html`, `link_invalido.html` |
| **5** | `base.html` (mensagens), `base_painel.html`, `inicio.html`, `avaliacoes.html`, `avaliacoes_resultados.html` |

> [!note] Sobre os blocos `diff`
> Linha com `+` **entra**, com `-` **sai**, e as outras estão lá só para você achar o lugar. Não copie os sinais.

---

# Etapa 1 · Casca do painel, Início e Quiz

### O que você recebe de A

| Tela | Variáveis |
|---|---|
| Todas | `secao`, `periodo`, `periodo_label`, `periodo_qs`, `periodos`, `mes`, `total_de_tentativas`, `tem_massa`, `k_minimo` |
| Início | `links`, `cursos_ativos`; com massa: `via_link`, `conversao_geral`, `serie`, `demanda_por_area`, `atividade` |
| Quiz | com massa: `top_manifestacoes`, `top_primeiro`, `top_cinco`, `confianca` (cada linha com `rotulo` e `total`), `aderencia` (com `taxa`), `conversao`, `orfaos`, `cobertura` |

> [!tip] 🎓 Entenda: para onde vai cada número do painel antigo
> O `dashboard.html` antigo tinha 431 linhas, quase tudo com `style=""`. Nada some, só muda de lugar:
>
> | Painel antigo | Vai para |
> |---|---|
> | Testes, Pelo link, Cursos ativos, Links | **Início** |
> | Área que mais pesou | **Início**, gráfico de rosca |
> | Top 3, Top 1º, Top 5, Confiança, Aderência, Conversão, Nunca recomendados, Cobertura | **Quiz** |

## 1.1 `templates/base.html`: um gancho no `<body>`

O `.conteudo` do site tem largura máxima de 1120px. O painel precisa da tela inteira, então o `<body>` ganha um bloco de classe:

```html
<body class="{% block classe_body %}{% endblock %}">
```

As outras páginas não usam o bloco, então o atributo sai vazio e nada muda para elas.

## 1.2 `painel/templates/painel/base_painel.html` (novo)

A casca de **todas** as telas do painel. As telas só preenchem os blocos `titulo_pagina`, `subtitulo`, `acoes`, `painel` e, se precisarem de biblioteca, `scripts_painel`.

```html
{% extends "base.html" %}
{% load static %}
{% block title %}{% block titulo_painel %}Painel{% endblock %} · Painel{% endblock %}
{% block classe_body %}pagina-painel{% endblock %}
{% block estilos %}<link rel="stylesheet" href="{% static 'css/painel.css' %}">{% endblock %}
{% block topo %}{% endblock %}
{% block rodape %}{% endblock %}

{% block content %}
<div class="painel-app">
    <aside class="painel-menu" id="painel-menu" aria-label="Menu do painel">
        <a class="painel-menu__marca" href="{% url 'painel-dashboard' %}?{{ periodo_qs }}">
            <span class="painel-menu__selo" aria-hidden="true">E</span> EducMatch
        </a>
        <nav class="painel-menu__nav">
            <a class="painel-menu__item" href="{% url 'painel-dashboard' %}?{{ periodo_qs }}" {% if secao == "inicio" %}aria-current="page"{% endif %}>
                <i class="fa-solid fa-house" aria-hidden="true"></i> Início
            </a>
            <a class="painel-menu__item" href="{% url 'painel-quiz' %}?{{ periodo_qs }}" {% if secao == "quiz" %}aria-current="page"{% endif %}>
                <i class="fa-solid fa-circle-question" aria-hidden="true"></i> Quiz
            </a>
        </nav>
        <form class="painel-menu__chamada" method="post" action="{% url 'painel-gerar-link' %}" data-confirmar="Gerar um novo link de acesso ao quiz?">
            {% csrf_token %}
            <strong>Gere um link e compartilhe o quiz com a turma.</strong>
            <button type="submit" class="botao botao--bloco"><i class="fa-solid fa-link" aria-hidden="true"></i> Gerar link</button>
        </form>
    </aside>
    <div class="painel-fundo" data-fechar-menu hidden></div>

    <div class="painel-principal">
        <header class="painel-barra">
            <button type="button" class="botao botao--secundario botao--icone painel-barra__menu" data-abrir-menu aria-controls="painel-menu" aria-expanded="false" aria-label="Abrir menu">
                <i class="fa-solid fa-bars" aria-hidden="true"></i>
            </button>

            <form class="painel-periodo" method="get" aria-label="Período">
                <label class="visualmente-oculto" for="periodo">Período</label>
                <select id="periodo" name="periodo" class="painel-campo">
                    {% for chave, config in periodos.items %}
                    <option value="{{ chave }}" {% if periodo == chave %}selected{% endif %}>{{ config.label }}</option>
                    {% endfor %}
                </select>
                <label class="visualmente-oculto" for="mes">Mês</label>
                <input id="mes" type="month" name="mes" value="{{ mes }}" class="painel-campo painel-periodo__mes">
                <button type="submit" class="botao">Aplicar</button>
            </form>

            <details class="painel-acessibilidade">
                <summary class="botao botao--neutro botao--icone" aria-label="Acessibilidade">
                    <i class="fa-solid fa-universal-access" aria-hidden="true"></i>
                </summary>
                <div class="painel-acessibilidade__menu">
                    <button type="button" class="botao botao--suave botao--bloco" data-alternar="fonte-grande">Fonte grande</button>
                    <button type="button" class="botao botao--suave botao--bloco" data-alternar="alto-contraste">Alto contraste</button>
                </div>
            </details>

            <div class="painel-perfil">
                <span class="painel-perfil__avatar" aria-hidden="true">{{ user.first_name|default:user.email|first|upper }}</span>
                <span class="painel-perfil__texto"><b>{{ user.first_name|default:"Coordenação" }}</b><small>Staff</small></span>
            </div>
        </header>

        <div class="painel-conteudo">
            <header class="painel-cabecalho">
                <div>
                    <h1>{% block titulo_pagina %}Painel{% endblock %}</h1>
                    <p>{% block subtitulo %}{% endblock %} · Período: {{ periodo_label }}{% if periodo == "mes" and mes %} ({{ mes }}){% endif %}</p>
                </div>
                <div class="painel-cabecalho__acoes">{% block acoes %}{% endblock %}</div>
            </header>

            {% block painel %}{% endblock %}
        </div>
    </div>

    <nav class="painel-inferior" aria-label="Menu do painel (celular)">
        <a href="{% url 'painel-dashboard' %}?{{ periodo_qs }}" {% if secao == "inicio" %}aria-current="page"{% endif %}><i class="fa-solid fa-house" aria-hidden="true"></i>Início</a>
        <a href="{% url 'painel-quiz' %}?{{ periodo_qs }}" {% if secao == "quiz" %}aria-current="page"{% endif %}><i class="fa-solid fa-circle-question" aria-hidden="true"></i>Quiz</a>
        <button type="button" data-abrir-menu aria-controls="painel-menu" aria-expanded="false"><i class="fa-solid fa-ellipsis" aria-hidden="true"></i>Mais</button>
    </nav>
</div>

<dialog class="painel-modal" id="painel-confirmar" aria-labelledby="painel-confirmar-titulo">
    <h2 id="painel-confirmar-titulo">Confirmar</h2>
    <p data-mensagem></p>
    <div class="painel-modal__acoes">
        <button type="button" class="botao botao--secundario" data-cancelar>Cancelar</button>
        <button type="button" class="botao" data-confirmar-ok>Confirmar</button>
    </div>
</dialog>
{% endblock %}

{% block scripts %}
<script src="{% static 'js/painel.js' %}" defer></script>
{% block scripts_painel %}{% endblock %}
{% endblock %}
```

> [!tip] 🎓 Entenda: herança de template
> O `base_painel.html` **estende** o `base.html` do site e esvazia o topo e o rodapé do aluno (`{% block topo %}{% endblock %}`). As telas do painel, por sua vez, estendem o `base_painel.html`. São três andares: **site → painel → tela**. Cada andar só escreve o que muda.

> [!note] 🎓 Entenda: por que o menu leva `?{{ periodo_qs }}`
> Sem isso, quem escolhe "Anual" na Início e clica em "Quiz" volta para "Mensal" sem perceber.

> [!tip] 🎓 Entenda: acessibilidade de graça
> - `aria-current="page"` diz ao leitor de tela qual item do menu é a página atual (e C usa o mesmo atributo para pintar o item de vermelho).
> - Os botões **Fonte grande** e **Alto contraste** têm `data-alternar`. O `acessibilidade.js`, que já existe no projeto, liga, salva e marca esses botões sozinho.
> - O `<dialog id="painel-confirmar">` no fim é a janela de confirmação. C escreve o JS que a abre.

## 1.3 `painel/templates/painel/inicio.html` (novo)

```html
{% extends "painel/base_painel.html" %}
{% load static %}
{% block titulo_painel %}Início{% endblock %}
{% block titulo_pagina %}Olá, {{ user.first_name|default:"Coordenação" }}!{% endblock %}
{% block subtitulo %}Resumo do quiz{% endblock %}

{% block painel %}
<div class="painel-kpis">
    <article class="painel-card painel-kpi">
        <h2>Testes realizados</h2>
        <p class="painel-kpi__valor" data-contar>{{ total_de_tentativas }}</p>
    </article>
    <article class="painel-card painel-kpi">
        <h2>Testes pelo link</h2>
        <p class="painel-kpi__valor">{% if tem_massa %}{{ via_link }}{% else %}—{% endif %}</p>
    </article>
    <article class="painel-card painel-kpi">
        <h2>Cursos ativos</h2>
        <p class="painel-kpi__valor">{{ cursos_ativos }}</p>
    </article>
    <article class="painel-card painel-kpi">
        <h2>Conversão <span class="painel-ajuda" tabindex="0" data-dica="Cursos salvos na lista de interesse ÷ cursos recomendados no período.">?</span></h2>
        <p class="painel-kpi__valor">{% if conversao_geral is None %}—{% else %}{{ conversao_geral|floatformat:0 }}%{% endif %}</p>
    </article>
</div>

{% if not tem_massa %}
{% include "painel/_sem_massa.html" %}
{% else %}
<div class="painel-grade painel-grade--2-1">
    <article class="painel-card">
        <h2 class="painel-card__titulo">Testes ao longo do tempo</h2>
        <div class="painel-grafico"><canvas id="grafico-serie" role="img" aria-label="Gráfico de linha com os testes do período"></canvas></div>
        <p class="painel-vazio"><i class="fa-solid fa-lock" aria-hidden="true"></i> Dias com menos de {{ k_minimo }} testes ficam em branco na linha.</p>
    </article>
    <article class="painel-card">
        <h2 class="painel-card__titulo">Demanda por área</h2>
        <div class="painel-grafico painel-grafico--rosca"><canvas id="grafico-areas" role="img" aria-label="Gráfico de rosca com a área que mais pesou no 1º lugar"></canvas></div>
        <ul class="painel-legenda">
            {% for linha in demanda_por_area|slice:":5" %}
            <li><span>{{ linha.nome }}</span><b>{% include "painel/_celula.html" with valor=linha.total suprimido=linha.suprimido %}</b></li>
            {% empty %}<li>Nenhum dado.</li>{% endfor %}
        </ul>
    </article>
</div>
{{ serie|json_script:"dados-serie" }}
{{ demanda_por_area|json_script:"dados-areas" }}
{% endif %}

<div class="painel-grade painel-grade--2-1">
    <article class="painel-card painel-card--destaque">
        <h2 class="painel-card__titulo">Link ativo do quiz</h2>
        {% for link in links %}
        <div class="painel-link">
            <input class="painel-link__url" type="text" value="{{ link.url }}" readonly aria-label="Endereço do link">
            <button type="button" class="botao botao--secundario" data-copiar><i class="fa-solid fa-copy" aria-hidden="true"></i> Copiar</button>
        </div>
        {% empty %}
        <p class="painel-vazio">Nenhum link ativo. Use “Gerar link” no menu.</p>
        {% endfor %}
        {% if links %}
        <form method="post" action="{% url 'painel-fechar-link' %}" data-confirmar="Fechar todos os links ativos? Quem tiver o endereço não consegue mais entrar." data-perigo>
            {% csrf_token %}
            <button type="submit" class="botao botao--perigo"><i class="fa-solid fa-ban" aria-hidden="true"></i> Fechar links</button>
        </form>
        {% endif %}
    </article>

    {% if tem_massa %}
    <article class="painel-card">
        <h2 class="painel-card__titulo">Atividade recente</h2>
        <ul class="painel-atividade">
            {% for item in atividade %}
            <li>
                <span class="painel-atividade__icone"><i class="fa-solid {{ item.icone }}" aria-hidden="true"></i></span>
                <span><b>{% include "painel/_celula.html" with valor=item.total suprimido=item.suprimido %}</b> {{ item.rotulo }}</span>
            </li>
            {% endfor %}
        </ul>
    </article>
    {% endif %}
</div>
{% endblock %}

{% block scripts_painel %}
{% if tem_massa %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js" defer></script>
<script src="{% static 'js/painel-graficos.js' %}" defer></script>
{% endif %}
{% endblock %}
```

> [!tip] 🎓 Entenda: `json_script`
> `{{ serie|json_script:"dados-serie" }}` escreve os dados dentro de uma tag `<script type="application/json" id="dados-serie">`. O JS de C lê dali. É o jeito **seguro** de mandar dados do Python para o JavaScript: o Django escapa tudo, então um nome de curso com aspas não quebra a página.

## 1.4 `painel/templates/painel/quiz.html` (novo)

```html
{% extends "painel/base_painel.html" %}
{% block titulo_painel %}Quiz{% endblock %}
{% block titulo_pagina %}Quiz — Visão geral{% endblock %}
{% block subtitulo %}Desempenho da recomendação e cobertura da engine{% endblock %}

{% block painel %}
{% if not tem_massa %}
{% include "painel/_sem_massa.html" %}
{% else %}
<div class="painel-grade painel-grade--3">
    {% include "painel/_ranking.html" with titulo="Mais salvos na lista" linhas=top_manifestacoes %}
    {% include "painel/_ranking.html" with titulo="Mais vezes em 1º lugar" linhas=top_primeiro %}
    {% include "painel/_ranking.html" with titulo="Mais vezes no Top 5" linhas=top_cinco %}
</div>

<div class="painel-grade painel-grade--2">
    <article class="painel-card">
        <h2 class="painel-card__titulo">Distribuição de confiança</h2>
        <ul class="painel-barras">
            {% for linha in confianca %}
            <li>
                <span>{{ linha.rotulo }}</span>
                <b>{% include "painel/_celula.html" with valor=linha.total suprimido=linha.suprimido %}</b>
            </li>
            {% empty %}<li>Nenhum dado.</li>{% endfor %}
        </ul>
    </article>
    <article class="painel-card">
        <h2 class="painel-card__titulo">Aderência à recomendação <span class="painel-ajuda" tabindex="0" data-dica="Dos cursos salvos, quantos eram o 1º colocado do ranking no momento em que o aluno salvou.">?</span></h2>
        {% if aderencia.taxa is None %}
        <p class="painel-vazio">Menos de {{ k_minimo }} cursos salvos como 1º colocado no período.</p>
        {% else %}
        <p class="painel-kpi__valor">{{ aderencia.taxa|floatformat:0 }}%</p>
        <p class="painel-vazio">dos cursos salvos eram o 1º colocado</p>
        <div class="painel-progresso" aria-hidden="true"><i style="width: {{ aderencia.taxa|floatformat:0 }}%"></i></div>
        {% endif %}
    </article>
</div>

<article class="painel-card painel-grade">
    <h2 class="painel-card__titulo">Conversão por curso <span class="painel-ajuda" tabindex="0" data-dica="Quantas vezes o curso foi salvo na lista de interesse ÷ quantas vezes foi recomendado.">?</span></h2>
    <div class="painel-tabela">
        <table>
            <thead><tr><th scope="col">Curso</th><th scope="col" class="numero">Salvo</th><th scope="col" class="numero">Taxa</th></tr></thead>
            <tbody>
                {% for linha in conversao %}
                <tr>
                    <td>{{ linha.nome_curso }}</td>
                    <td class="numero">{% include "painel/_celula.html" with valor=linha.interessados suprimido=linha.suprimido %}</td>
                    <td class="numero">{% if linha.taxa is None %}—{% else %}{{ linha.taxa|floatformat:0 }}%{% endif %}</td>
                </tr>
                {% empty %}<tr><td colspan="3">Nenhum curso ativo.</td></tr>{% endfor %}
            </tbody>
        </table>
    </div>
</article>

<div class="painel-grade painel-grade--2">
    <article class="painel-card">
        <h2 class="painel-card__titulo">Cursos nunca recomendados</h2>
        <ul class="painel-lista">
            {% for curso in orfaos %}
            <li><span>{{ curso.nome_curso }}</span><span class="painel-selo painel-selo--perigo">Alerta</span></li>
            {% empty %}<li>Todos os cursos ativos já foram recomendados.</li>{% endfor %}
        </ul>
    </article>
    <article class="painel-card">
        <h2 class="painel-card__titulo">Cobertura de áreas <span class="painel-ajuda" tabindex="0" data-dica="Quantas alternativas do quiz dão peso a cada área. Zero = área que o quiz não mede.">?</span></h2>
        <ul class="painel-lista">
            {% for area in cobertura %}
            <li><span>{{ area.nome }}</span><b {% if not area.alternativas %}class="painel-alerta"{% endif %}>{{ area.alternativas }}</b></li>
            {% endfor %}
        </ul>
    </article>
</div>
{% endif %}
{% endblock %}
```

## 1.5 Os parciais

`_ranking.html` já existia, mas **nenhum template usava**. Ele volta com o visual novo:

```html
<article class="painel-card">
    <h2 class="painel-card__titulo">{{ titulo }}</h2>
    <ol class="painel-ranking">
        {% for linha in linhas %}
        <li>
            <span class="painel-ranking__pos">{{ forloop.counter|stringformat:"02d" }}</span>
            <span class="painel-ranking__nome">{{ linha.nome }}</span>
            <b>{% include "painel/_celula.html" with valor=linha.total suprimido=linha.suprimido %}</b>
        </li>
        {% empty %}
        <li class="painel-vazio">Nenhum dado no período.</li>
        {% endfor %}
    </ol>
</article>
```

`_celula.html`: o número escondido passa de "—" para **cadeado com "< 5"**:

```html
{% if suprimido %}<span class="painel-suprimido" title="menos de {{ k_minimo }} ocorrências: escondido para proteger quem respondeu"><i class="fa-solid fa-lock" aria-hidden="true"></i> &lt; {{ k_minimo }}</span>{% else %}{{ valor }}{% endif %}
```

`_sem_massa.html` (novo):

```html
<div class="painel-aviso" role="status">
    <i class="fa-solid fa-lock" aria-hidden="true"></i>
    <p><strong>Privacidade:</strong> menos de {{ k_minimo }} testes neste período, então só o total aparece. Escolha um período maior.</p>
</div>
```

> [!tip] 🎓 Entenda: parcial com `include ... with`
> `{% include "painel/_celula.html" with valor=linha.total suprimido=linha.suprimido %}` reaproveita o mesmo pedaço de HTML em todo lugar que mostra um número que pode estar escondido. Se um dia o cadeado mudar, muda em um arquivo só.

## 1.6 Apague `painel/templates/painel/dashboard.html`

O conteúdo dele foi para `inicio.html` e `quiz.html`.

### ✅ Pronta quando

- [ ] Nenhum `botao--contorno` ou `botao--texto` nos seus arquivos (`Ctrl+Shift+F` na pasta `painel/templates`)
- [ ] Quando A avisar "views prontas": `/painel/` e `/painel/quiz/` abrem sem erro

---

# Etapa 2 · Cursos e Áreas, Links e Lista de interesse

### O que você recebe de A

| Tela | Variáveis |
|---|---|
| Cursos e Áreas | `cursos` (cada um com `nome_curso`, `area`, `duracao`, `inicio_dia`, `fim_dia`, `em_primeiro`, `em_primeiro_suprimido`, `no_top5`, `no_top5_suprimido`, `id`), `demanda_por_area` |
| Links | `links` (cada um com `url`, `ativo`, `total`, `suprimido`, `criado_em`, `id`) |
| Lista de interesse | `funil` (cada etapa com `rotulo`, `total`, `suprimido`), `por_curso` (com `nome_curso`, `area`, `total`, `total_suprimido`, `contatados`, `contatados_suprimido`, `taxa_principal`) |

## 2.1 `base_painel.html`: três itens no menu e a ordem dos scripts

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

> [!warning] 🎓 Entenda: a ordem dos scripts importa
> A tela de Links carrega a biblioteca de QR code (`qrcode.min.js`), e o `painel.js` de C usa essa biblioteca. Os dois têm `defer`, e scripts com `defer` rodam **na ordem em que aparecem no HTML**. Por isso o bloco `scripts_painel` (bibliotecas da tela) passou para **antes** do `painel.js`. Com a ordem invertida, a página abre normal, sem erro nenhum, e só **não aparece QR**. Esse erro passa calado.

> [!note] O campo `voltar`
> O form de "Gerar link" do menu ganhou um `<input type="hidden" name="voltar">`. É ele que faz a ação voltar para a tela de Links quando é feita de lá. A explica na spec dela por que esse campo só aceita nomes de rota.

## 2.2 `painel/templates/painel/cursos.html` (novo)

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

> [!note] "Novo curso" e "Editar" levam para o admin
> O painel não ganha formulário de curso agora. O admin já cadastra e valida curso, área e pesos. O botão existe para o fluxo do design ficar completo.

## 2.3 `painel/templates/painel/links.html` (novo)

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

## 2.4 `painel/templates/painel/interesse.html` (novo)

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

> [!important] 🎓 Entenda: o que saiu do design nesta tela
> O design tinha uma coluna "Status" por curso e "Era o 1º colocado? Sim/Não". As duas não fazem sentido numa tabela **agregada**: um curso tem vários interessados, cada um num status. Ficaram o **funil** no topo e, por curso, o **%** que tinha o curso em 1º lugar.

### ✅ Pronta quando

- [ ] O menu tem 5 itens e marca a tela atual
- [ ] Com as views de A prontas, as três telas abrem sem erro

---

# Etapa 3 · % concluídos e tempo típico

### O que você recebe de A

`questoes_ativas` (sempre), `taxa_de_conclusao` e `tempo_tipico` (podem vir `None` ou nem existir) e o filtro `duracao`, carregado com `{% load painel_extras %}`.

## 3.1 `painel/templates/painel/quiz.html`

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

> [!note] 🎓 Entenda: variável que não existe vira `None`
> Sem massa, a view nem calcula a taxa e o tempo. Dentro de um `{% if %}`, uma variável que não existe vale `None`, então `{% if taxa_de_conclusao is None %}` mostra "—" nos dois casos (calculou e deu `None`, ou nem calculou). Os KPIs "Testes concluídos" e "Questões ativas" não dizem nada sobre pessoas, então aparecem sempre.

### ✅ Pronta quando

- [ ] A tela Quiz mostra 4 KPIs no topo, com "—" onde não há dado suficiente

---

# Etapa 4 · Avaliação de fim de curso (telas do aluno)

### O que você recebe de A

| Tela | Variáveis |
|---|---|
| Responder | `link` (com `link.curso.nome_curso` e `link.turma`) e `form`; `form.campos_por_pergunta` dá pares `(pergunta, campo)`, e `pergunta.tipo` é `nps`, `escala`, `escolha` ou `texto` |
| Obrigado | `link` (pode vir `None`) |

Essas telas são do **site do aluno**: estendem o `base.html` direto, e não o `base_painel.html`. Ficam em `avaliacao/templates/avaliacao/`.

## 4.1 `responder.html`

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Avaliação do curso{% endblock %}
{% block estilos %}<link rel="stylesheet" href="{% static 'css/avaliacao.css' %}">{% endblock %}

{% block content %}
<form class="cartao avaliacao entrada" method="post" novalidate>
    {% csrf_token %}
    <header class="avaliacao__topo">
        <p class="chip">Avaliação de fim de curso</p>
        <h1>{{ link.curso.nome_curso }}</h1>
        <p class="subtitulo">Turma {{ link.turma }} · leva uns 3 minutos.</p>
        <p class="aviso avaliacao__anonimo" role="note">
            <i class="fa-solid fa-lock" aria-hidden="true"></i>
            É anônimo: não pedimos nome nem e-mail, e a escola só vê os resultados somados da turma.
        </p>
    </header>

    {% if form.errors %}
    <p class="campo__erro avaliacao__resumo-erro" role="alert">Faltou responder algumas perguntas. Elas estão marcadas abaixo.</p>
    {% endif %}

    {% for pergunta, campo in form.campos_por_pergunta %}
    <fieldset class="avaliacao__pergunta{% if campo.errors %} avaliacao__pergunta--erro{% endif %}">
        <legend>
            {{ forloop.counter }}. {{ pergunta.texto }}
            {% if not pergunta.obrigatoria %}<span class="campo__opcional">(opcional)</span>{% endif %}
        </legend>

        {% if pergunta.tipo == "texto" %}
        <label class="visualmente-oculto" for="{{ campo.id_for_label }}">{{ pergunta.texto }}</label>
        {{ campo }}
        {% else %}
        <div class="avaliacao__opcoes avaliacao__opcoes--{{ pergunta.tipo }}">
            {% for opcao in campo %}
            <label class="avaliacao__opcao">{{ opcao.tag }}<span>{{ opcao.choice_label }}</span></label>
            {% endfor %}
        </div>
        {% if pergunta.tipo == "nps" %}
        <p class="avaliacao__legenda"><span>0 = nada provável</span><span>10 = com certeza</span></p>
        {% elif pergunta.tipo == "escala" %}
        <p class="avaliacao__legenda"><span>1 = muito ruim</span><span>5 = excelente</span></p>
        {% endif %}
        {% endif %}

        {% for erro in campo.errors %}<p class="campo__erro" role="alert">{{ erro }}</p>{% endfor %}
    </fieldset>
    {% endfor %}

    <button class="botao botao--bloco" type="submit">Enviar avaliação</button>
</form>
{% endblock %}
```

> [!tip] 🎓 Entenda: `fieldset` e `legend`
> Cada pergunta é um `<fieldset>` com a pergunta no `<legend>`. Assim o leitor de tela lê "De 0 a 10, quanto você recomendaria…, grupo, opção 9" e a pessoa cega sabe a que pergunta aquele 9 responde. Um `<div>` com um `<p>` em cima não dá essa informação.

> [!tip] 🎓 Entenda: `{% for opcao in campo %}`
> Num campo de rádio do Django, dá para percorrer as opções uma a uma: `opcao.tag` é o `<input type="radio">` e `opcao.choice_label` é o texto. É isso que deixa você montar os botões de 0 a 10 do jeito do design, em vez do HTML padrão do Django.

## 4.2 `obrigado.html`

```html
{% extends "base.html" %}

{% block title %}Avaliação enviada{% endblock %}

{% block content %}
<section class="cartao cartao--centro entrada">
    <h1>Obrigado pela avaliação!</h1>
    <p class="subtitulo">
        {% if link %}Suas respostas sobre {{ link.curso.nome_curso }} foram registradas.{% else %}Suas respostas foram registradas.{% endif %}
        Elas ajudam a escola a melhorar o curso para as próximas turmas.
    </p>
</section>
{% endblock %}
```

## 4.3 `link_invalido.html`

```html
{% extends "base.html" %}

{% block title %}Link encerrado{% endblock %}

{% block content %}
<section class="cartao cartao--centro entrada">
    <h1>Este link de avaliação não existe ou foi encerrado</h1>
    <p class="subtitulo">Confira o endereço com a coordenação do curso.</p>
</section>
{% endblock %}
```

### ✅ Pronta quando

- [ ] Com o app de A pronto e um link criado no admin, `/avaliacao/<token>/` mostra curso, turma, o aviso de anonimato e as 7 perguntas

---

# Etapa 5 · Avaliações no painel

### O que você recebe de A

| Tela | Variáveis |
|---|---|
| Início | + `avaliacoes_no_periodo` |
| Links das turmas | `links` (com `curso__nome_curso`, `turma`, `url`, `total`, `suprimido`, `ativo`, `id`) e `form` (com `form.curso` e `form.turma`) |
| Resultados | `curso` (ou `None`), `avaliacoes_com_massa`, `resumo` (cada curso com `nome`, `total`, `suprimido`, `nps`, `media`), `cursos_avaliados`; com massa: `blocos` (cada um com `pergunta`, `distribuicao` ou `textos`, `nps`, `media`) e `fora_do_todos` |

## 5.1 Mensagens dentro do painel

As ações desta etapa mostram mensagens ("Link criado para…"). O `base.html` as mostra acima do conteúdo, e no painel isso cai **atrás do menu fixo**. O `base.html` ganha um bloco em volta delas:

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

E o `base_painel.html` esvazia esse bloco, mostra as mensagens dentro da área de conteúdo e ganha o item **Avaliações** no menu:

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

## 5.2 `inicio.html`: o KPI de avaliações

Antes do KPI de Conversão:

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

## 5.3 `painel/templates/painel/avaliacoes.html` (novo)

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

## 5.4 `painel/templates/painel/avaliacoes_resultados.html` (novo)

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

> [!note] 🎓 Entenda: barras em CSS, sem biblioteca de gráfico
> Os cards por pergunta usam a mesma barra (`painel-progresso`) da tela Quiz. São até 11 barras por card e 7 cards, e uma biblioteca de gráfico para isso seria peso sem ganho. A largura de cada barra vem pronta da view **depois** da supressão: uma barra escondida tem largura zero e não entrega pelo tamanho o número que o cadeado esconde.

### ✅ Pronta quando

- [ ] O menu tem o item **Avaliações**, e as mensagens aparecem dentro da área de conteúdo, e não atrás do menu
- [ ] As duas telas novas abrem, com e sem avaliações
