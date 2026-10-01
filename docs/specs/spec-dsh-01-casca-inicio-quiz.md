---
title: "Spec DSH-01 — casca do painel, tela Início e tela Quiz"
aliases: ["DSH-01", "Casca do painel", "Painel novo: Início e Quiz"]
tags: [tcc, spec, painel, dashboard, front, privacidade]
status: proposto
projeto: TCC
branch: feature/painel-casca-inicio-quiz
criado: 2026-10-01
---

> [!info] Plano: [[plano-dashboard-git-flow|🖥️ Dashboard novo e Git Flow]] · Próxima: [[spec-dsh-02-cursos-links-interesse|02 — Cursos, Links e Interesse]] · Design: `educmatch_dashboard_responsivo (2).html`

# 🖥️ DSH-01: casca do painel, Início e Quiz

**Branch:** `feature/painel-casca-inicio-quiz`, saindo da `develop` **com a PRE-03 já mesclada**
**Risco:** baixo. Nenhuma migração. Muda só o painel (`/painel/`), que só o staff vê.
**Testes ao final:** 96 (86 + 10 novos)

> [!abstract] O que esta branch faz
> 1. Troca o painel de página única (431 linhas, quase tudo em `style=""`) pela **casca do design aprovado**: menu lateral preto, barra do topo com período e acessibilidade, e barra inferior no celular.
> 2. Divide o conteúdo em duas telas: **Início** (`/painel/`) e **Quiz** (`/painel/quiz/`).
> 3. Cria as variantes de botão **sólidas** e um teste que **reprova** qualquer botão fantasma nos templates do painel.
> 4. Acrescenta três métricas que a Início pede: conversão geral, testes por dia e atividade recente. As três passam pela supressão k = 5.

---

## 1️⃣ Para onde vai cada número do painel atual

Nada some. Cada bloco do `dashboard.html` antigo ganha um lugar no design:

| Painel atual | Vai para | Observação |
|---|---|---|
| Testes, Pelo link, Cursos ativos | **Início**, KPIs | + KPI novo "Conversão" |
| Links (gerar, fechar, copiar) | **Início**, card "Link ativo" + botão "Gerar link" no menu | A tela de links completa chega na DSH-02 |
| Área que mais pesou (1º) | **Início**, gráfico de rosca | Chart.js, o mesmo CDN de antes |
| Top 3 manifestações, Top 1º, Top 5 | **Quiz**, três rankings | |
| Confiança | **Quiz**, lista com rótulo "Alta / Média / Baixa" | Antes saía "media", sem acento |
| Aderência | **Quiz**, % que salvou o 1º colocado | Agora com supressão (ver 7️⃣) |
| Conversão por curso | **Quiz**, tabela | Sem a coluna "recomendado", como antes |
| Cursos nunca recomendados, Cobertura | **Quiz** | |

> [!important] Três diferenças em relação ao design
> | Design | Aqui | Por quê |
> |---|---|---|
> | Período 7 / 30 / 90 dias | **Diário / Mensal / Anual / Mês**, os `PERIODOS` que já existem | Os testes `FiltroDePeriodoTest` travam esses quatro. Mudar a régua é outra discussão |
> | KPIs com "↑ 12% no período" | **Sem variação** | Exige calcular o período anterior em toda métrica. Fica para depois, se a banca pedir |
> | Card "Formulários recentes" e KPI de respostas de formulário | **Fora** | Formulários são a Fase 2. Não se desenha card de dado que não existe |

## 2️⃣ `templates/base.html`: um gancho no `<body>`

O `.conteudo` do `base.css` tem `max-width: 1120px`. O painel precisa da tela inteira, então o `<body>` ganha um bloco de classe:

```html
<body class="{% block classe_body %}{% endblock %}">
```

As outras páginas não definem o bloco: o atributo sai vazio e nada muda para elas.

## 3️⃣ `static/css/componentes.css`: botões sólidos

Acrescente no fim do arquivo:

```css
/* ---------- Botões sólidos (regra do painel: nenhum botão fantasma) ----------
   .botao é o principal (vermelho). As variantes abaixo trocam só o fundo:
   todas são preenchidas, sem borda aparente e com alvo de 48px. */

.botao--secundario {
  border-color: var(--preto-2);
  background: var(--preto-2);
  color: var(--branco);
}

.botao--secundario:hover {
  border-color: var(--preto);
  background: var(--preto);
  color: var(--branco);
  box-shadow: 0 6px 16px rgba(9, 9, 11, 0.2);
}

.botao--suave {
  border-color: var(--marca-claro);
  background: var(--marca-claro);
  color: var(--marca-escuro);
}

.botao--suave:hover {
  border-color: #f9d6d3;
  background: #f9d6d3;
  color: var(--marca-escuro);
  box-shadow: none;
}

.botao--neutro {
  border-color: var(--gelo);
  background: var(--gelo);
  color: var(--preto-2);
}

.botao--neutro:hover {
  border-color: #e4deda;
  background: #e4deda;
  color: var(--preto);
  box-shadow: none;
}

.botao--perigo {
  border-color: var(--erro);
  background: var(--erro);
  color: var(--branco);
}

.botao--perigo:hover {
  border-color: #b91c1c;
  background: #b91c1c;
  color: var(--branco);
  box-shadow: 0 6px 16px rgba(220, 38, 38, 0.22);
}

.botao--icone {
  width: var(--alvo);
  padding: 0;
}
```

> [!warning] Regra do painel: **nenhum botão fantasma**
> Fantasma é botão de fundo transparente ou branco só com borda. No painel, todo botão é uma destas variantes:
>
> | Classe | Fundo | Uso |
> |---|---|---|
> | `botao` | vermelho `--marca` | Ação principal da tela (Aplicar, Gerar link, Novo curso) |
> | `botao botao--secundario` | grafite `--preto-2` | Copiar, Cancelar, abrir menu |
> | `botao botao--suave` | rosado `--marca-claro` | Ações de linha de tabela, opções de menu |
> | `botao botao--neutro` | gelo `--gelo` | Botões de ícone da barra do topo |
> | `botao botao--perigo` | `--erro` | Fechar link |
>
> O `botao--contorno` e o `botao--texto` continuam existindo para o **site do aluno**, mas não podem aparecer em `painel/templates/`. O teste da seção 9️⃣ confere isso nos arquivos e no HTML servido.

## 4️⃣ `static/css/painel.css`: substitua o arquivo inteiro

```css
/* Painel da coordenação. Usa os tokens do tokens.css; os botões vêm do componentes.css.
   Regra da tela: nenhum botão fantasma. Todo botão tem fundo sólido. */

.pagina-painel .conteudo {
  max-width: none;
  padding: 0;
}

.painel-app {
  --menu: 248px;
  --barra: 72px;
  display: flex;
  min-height: 100vh;
}

/* ---------- Menu lateral ---------- */

.painel-menu {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 40;
  width: var(--menu);
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 18px 12px;
  overflow-y: auto;
  background: var(--preto);
  color: var(--branco);
}

.painel-menu__marca {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  font-size: 1.15rem;
  font-weight: 700;
  text-decoration: none;
}

.painel-menu__selo {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: var(--marca);
}

.painel-menu__nav {
  display: grid;
  gap: 6px;
}

.painel-menu__item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: var(--alvo);
  padding: 0 14px;
  border-radius: 9px;
  background: #17171a;
  color: #d4d4d8;
  font-weight: 600;
  text-decoration: none;
  transition: background var(--dur-rapida) var(--ease-padrao);
}

.painel-menu__item:hover {
  background: #242428;
  color: var(--branco);
}

.painel-menu__item[aria-current="page"] {
  background: var(--marca);
  color: var(--branco);
}

.painel-menu__item i {
  width: 20px;
  text-align: center;
}

.painel-menu__chamada {
  margin-top: auto;
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid #29292d;
  border-radius: var(--raio);
  background: #17171a;
  font-size: 0.85rem;
}

/* ---------- Barra do topo ---------- */

.painel-principal {
  flex: 1;
  min-width: 0;
  margin-left: var(--menu);
}

.painel-barra {
  position: sticky;
  top: 0;
  z-index: 25;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: var(--barra);
  padding: 12px 28px;
  border-bottom: 1px solid var(--linha);
  background: rgba(249, 250, 251, 0.96);
  backdrop-filter: blur(10px);
}

.painel-barra__menu {
  display: none;
}

.painel-periodo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.painel-campo {
  min-height: var(--alvo);
  padding: 0 12px;
  border: 0;
  border-radius: var(--raio-botao);
  background: var(--gelo);
  color: var(--tinta);
  font: inherit;
  font-weight: 600;
}

.painel-acessibilidade {
  position: relative;
  margin-left: auto;
}

.painel-acessibilidade summary {
  list-style: none;
}

.painel-acessibilidade summary::-webkit-details-marker {
  display: none;
}

.painel-acessibilidade__menu {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  z-index: 30;
  display: grid;
  gap: 6px;
  min-width: 210px;
  padding: 8px;
  border: 1px solid var(--linha);
  border-radius: var(--raio);
  background: var(--superficie);
  box-shadow: var(--sombra);
}

.painel-acessibilidade__menu [aria-pressed="true"] {
  border-color: var(--marca);
  background: var(--marca);
  color: var(--branco);
}

.painel-perfil {
  display: flex;
  align-items: center;
  gap: 10px;
}

.painel-perfil__avatar {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--marca-claro);
  color: var(--marca-escuro);
  font-weight: 700;
}

.painel-perfil__texto {
  display: grid;
  line-height: 1.2;
  font-size: 0.85rem;
}

.painel-perfil__texto small {
  color: var(--texto-3);
}

/* ---------- Conteúdo ---------- */

.painel-conteudo {
  max-width: 1600px;
  margin: 0 auto;
  padding: 26px 28px 48px;
}

.painel-cabecalho {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 3px solid var(--marca);
}

.painel-cabecalho h1 {
  margin: 0;
  font-size: var(--h2);
}

.painel-cabecalho p {
  margin: 4px 0 0;
  color: var(--texto-2);
}

.painel-cabecalho__acoes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.painel-kpis,
.painel-grade {
  display: grid;
  gap: 16px;
  margin-bottom: 16px;
}

.painel-kpis {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.painel-grade--2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.painel-grade--3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.painel-grade--2-1 {
  grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
}

.painel-card {
  min-width: 0;
  padding: 18px;
  border: 1px solid var(--linha);
  border-radius: 14px;
  background: var(--superficie);
  box-shadow: var(--sombra);
}

.painel-card--destaque {
  border-left: 4px solid var(--marca);
}

.painel-kpi h2,
.painel-card__titulo {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  font-size: 0.8rem;
  letter-spacing: 0.075em;
  text-transform: uppercase;
  color: var(--marca-escuro);
}

.painel-kpi h2 {
  min-height: 24px;
}

.painel-kpi__valor {
  margin: 0;
  font-size: 1.9rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.03em;
}

.painel-ajuda {
  position: relative;
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--gelo);
  color: var(--texto-2);
  font-size: 0.75rem;
  letter-spacing: 0;
  text-transform: none;
  cursor: help;
}

.painel-ajuda:hover::after,
.painel-ajuda:focus::after {
  content: attr(data-dica);
  position: absolute;
  bottom: 30px;
  left: 50%;
  z-index: 20;
  width: 240px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--preto);
  color: var(--branco);
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.35;
  transform: translateX(-50%);
}

.painel-grafico {
  position: relative;
  height: 260px;
}

.painel-grafico--rosca {
  height: 200px;
}

.painel-legenda,
.painel-lista,
.painel-barras,
.painel-ranking,
.painel-atividade {
  display: grid;
  gap: 10px;
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
  font-size: 0.85rem;
}

.painel-legenda li,
.painel-lista li,
.painel-barras li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--linha);
}

.painel-ranking li {
  display: grid;
  grid-template-columns: 32px 1fr auto;
  align-items: center;
  gap: 8px;
}

.painel-ranking__pos {
  color: var(--marca);
  font-weight: 700;
}

.painel-ranking__nome {
  font-weight: 600;
}

.painel-atividade li {
  display: flex;
  align-items: center;
  gap: 10px;
}

.painel-atividade__icone {
  display: grid;
  flex: none;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--marca-claro);
  color: var(--marca);
}

.painel-progresso {
  height: 10px;
  overflow: hidden;
  border-radius: var(--raio-pilula);
  background: #f0eeee;
}

.painel-progresso i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--marca);
}

.painel-selo {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: var(--raio-pilula);
  font-size: 0.75rem;
  font-weight: 700;
}

.painel-selo--sucesso { background: #eaf7ee; color: #15803d; }
.painel-selo--alerta { background: #fff5df; color: #92400e; }
.painel-selo--perigo { background: #feecec; color: #b91c1c; }
.painel-selo--neutro { background: #f1f1f3; color: var(--texto-2); }

.painel-alerta {
  color: var(--erro);
}

.painel-suprimido {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--marca-escuro);
  font-weight: 700;
  white-space: nowrap;
}

.painel-aviso {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px 14px;
  border: 1px solid #f6cbc7;
  border-radius: 10px;
  background: var(--marca-clarinho);
  color: var(--marca-escuro);
}

.painel-aviso p {
  margin: 0;
}

.painel-vazio {
  margin: 6px 0;
  color: var(--texto-3);
}

.painel-link {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.painel-link__url {
  flex: 1;
  min-width: 0;
  min-height: var(--alvo);
  padding: 0 10px;
  border: 1px solid var(--linha);
  border-radius: var(--raio-botao);
  background: var(--fundo);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.8rem;
}

/* Tabelas */

.painel-tabela {
  overflow-x: auto;
}

.painel-tabela table {
  width: 100%;
  min-width: 640px;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.painel-tabela th {
  padding: 10px 12px;
  background: #fafafa;
  color: var(--texto-3);
  font-size: 0.75rem;
  letter-spacing: 0.07em;
  text-align: left;
  text-transform: uppercase;
}

.painel-tabela td {
  padding: 10px 12px;
  border-top: 1px solid var(--linha);
}

.painel-tabela td.numero,
.painel-tabela th.numero {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* Modal de confirmação */

.painel-modal {
  width: min(480px, calc(100% - 32px));
  padding: 22px;
  border: 0;
  border-radius: 16px;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.22);
}

.painel-modal::backdrop {
  background: rgba(9, 9, 11, 0.52);
}

.painel-modal h2 {
  margin: 0 0 8px;
  color: var(--titulo);
}

.painel-modal__acoes {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 18px;
}

.painel-inferior,
.painel-fundo {
  display: none;
}

/* ---------- Alto contraste ---------- */

:root.alto-contraste .painel-card {
  border-color: var(--linha);
  box-shadow: none;
}

/* ---------- Tablet ---------- */

@media (max-width: 1100px) {
  .painel-grade--2-1,
  .painel-grade--3 {
    grid-template-columns: 1fr;
  }
}

/* ---------- Celular ---------- */

@media (max-width: 760px) {
  .painel-app {
    --menu: 0px;
  }

  .painel-menu {
    width: min(300px, 86vw);
    transform: translateX(-100%);
    transition: transform var(--dur-media) var(--ease-saida);
  }

  .painel-menu.aberto {
    transform: none;
    box-shadow: 20px 0 60px rgba(0, 0, 0, 0.25);
  }

  .painel-fundo:not([hidden]) {
    position: fixed;
    inset: 0;
    z-index: 35;
    display: block;
    background: rgba(9, 9, 11, 0.48);
  }

  .painel-barra {
    padding: 10px 14px;
  }

  .painel-barra__menu {
    display: inline-flex;
  }

  .painel-perfil {
    display: none;
  }

  .painel-conteudo {
    padding: 18px 14px 96px;
  }

  .painel-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .painel-grade--2 {
    grid-template-columns: 1fr;
  }

  .painel-inferior {
    position: fixed;
    inset: auto 0 0 0;
    z-index: 30;
    display: flex;
    justify-content: space-around;
    gap: 6px;
    padding: 6px;
    background: var(--preto);
  }

  .painel-inferior a,
  .painel-inferior button {
    display: flex;
    flex: 1;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    min-height: 56px;
    border: 0;
    border-radius: 8px;
    background: #17171a;
    color: #d4d4d8;
    font: inherit;
    font-size: 0.75rem;
    text-decoration: none;
  }

  .painel-inferior [aria-current="page"] {
    background: var(--marca);
    color: var(--branco);
  }
}
```

## 5️⃣ Templates

### Apague

- `painel/templates/painel/dashboard.html`: o conteúdo foi para `inicio.html` e `quiz.html`.

### `painel/templates/painel/base_painel.html` (novo)

A casca de todas as telas do painel. As telas preenchem `titulo_pagina`, `subtitulo`, `acoes`, `painel` e, se precisarem de biblioteca, `scripts_painel`.

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

> [!note] Por que o menu leva `?{{ periodo_qs }}`
> Sem isso, quem escolhe "Anual" na Início e clica em "Quiz" volta para "Mensal" sem perceber. O `periodo_qs` sai pronto da view (`urlencode`), então nada do `GET` vai para o HTML sem passar pela validação do período.

### `painel/templates/painel/inicio.html` (novo)

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

### `painel/templates/painel/quiz.html` (novo)

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

### Parciais

`painel/templates/painel/_ranking.html` já existia, mas **nenhum template o usava**. Ele é reaproveitado com o visual novo:

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

`painel/templates/painel/_celula.html`: a célula suprimida passa de "—" para cadeado com "< 5", como no design:

```html
{% if suprimido %}<span class="painel-suprimido" title="menos de {{ k_minimo }} ocorrências: escondido para proteger quem respondeu"><i class="fa-solid fa-lock" aria-hidden="true"></i> &lt; {{ k_minimo }}</span>{% else %}{{ valor }}{% endif %}
```

`painel/templates/painel/_sem_massa.html` (novo):

```html
<div class="painel-aviso" role="status">
    <i class="fa-solid fa-lock" aria-hidden="true"></i>
    <p><strong>Privacidade:</strong> menos de {{ k_minimo }} testes neste período, então só o total aparece. Escolha um período maior.</p>
</div>
```

## 6️⃣ JavaScript

### `static/js/painel.js` (novo)

Tudo o que o painel faz no navegador. **Sem JS, o painel continua funcionando**: os forms enviam direto (sem o modal) e o campo de mês fica sempre visível.

```js
/* Painel: menu no celular, confirmação antes de POST, copiar link e campo de mês.
   Sem JS o painel continua funcionando: os forms enviam direto e o mês fica visível. */
(function () {
    const menu = document.getElementById("painel-menu");
    const fundo = document.querySelector("[data-fechar-menu]");
    const abridores = document.querySelectorAll("[data-abrir-menu]");

    function alternarMenu(abrir) {
        menu.classList.toggle("aberto", abrir);
        fundo.hidden = !abrir;
        abridores.forEach(function (botao) {
            botao.setAttribute("aria-expanded", String(abrir));
        });
    }

    abridores.forEach(function (botao) {
        botao.addEventListener("click", function () {
            alternarMenu(!menu.classList.contains("aberto"));
        });
    });
    fundo.addEventListener("click", function () {
        alternarMenu(false);
    });
    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") alternarMenu(false);
    });

    // O campo de mês só aparece quando o período escolhido é "Mês".
    const periodo = document.getElementById("periodo");
    const mes = document.getElementById("mes");
    function mostrarMes() {
        mes.hidden = periodo.value !== "mes";
    }
    periodo.addEventListener("change", mostrarMes);
    mostrarMes();

    // Todo form com data-confirmar passa por um <dialog> antes de enviar.
    const modal = document.getElementById("painel-confirmar");
    const ok = modal.querySelector("[data-confirmar-ok]");
    let pendente = null;

    document.querySelectorAll("form[data-confirmar]").forEach(function (form) {
        form.addEventListener("submit", function (evento) {
            if (form.dataset.confirmado === "1") return;
            evento.preventDefault();
            pendente = form;
            modal.querySelector("[data-mensagem]").textContent = form.dataset.confirmar;
            ok.className = "perigo" in form.dataset ? "botao botao--perigo" : "botao";
            modal.showModal();
        });
    });

    ok.addEventListener("click", function () {
        modal.close();
        if (pendente) {
            pendente.dataset.confirmado = "1";
            pendente.requestSubmit();
        }
    });
    modal.querySelector("[data-cancelar]").addEventListener("click", function () {
        pendente = null;
        modal.close();
    });

    document.querySelectorAll("[data-copiar]").forEach(function (botao) {
        botao.addEventListener("click", function () {
            const campo = botao.parentElement.querySelector("input");
            navigator.clipboard.writeText(campo.value).then(function () {
                const original = botao.innerHTML;
                botao.textContent = "Copiado!";
                setTimeout(function () {
                    botao.innerHTML = original;
                }, 1600);
            });
        });
    });
})();
```

> [!tip] Por que `<dialog>` e não um modal feito à mão
> O `<dialog>` com `showModal()` já prende o foco dentro dele, fecha com Esc e escurece o fundo com `::backdrop`. Um modal de `<div>` precisaria de tudo isso em JS e ainda assim seria pior para leitor de tela.

### `static/js/painel-graficos.js` (novo)

```js
/* Gráficos da tela Início. Os dados chegam por json_script, já suprimidos:
   um dia com menos de K testes vem como null e vira um buraco na linha. */
(function () {
    if (typeof Chart === "undefined") {
        console.warn("Chart.js não carregou; os números continuam nas legendas.");
        return;
    }

    const estilo = getComputedStyle(document.documentElement);
    const marca = estilo.getPropertyValue("--marca").trim();
    const fonte = estilo.getPropertyValue("--fonte").trim();
    const tons = [marca, "#8e2520", "#a8564f", "#bda09c", "#d7c8c4"];
    Chart.defaults.font.family = fonte;

    function dados(id) {
        const elemento = document.getElementById(id);
        return elemento ? JSON.parse(elemento.textContent) : [];
    }

    const serie = dados("dados-serie");
    new Chart(document.getElementById("grafico-serie"), {
        type: "line",
        data: {
            labels: serie.map(function (linha) { return linha.rotulo; }),
            datasets: [{
                label: "Testes",
                data: serie.map(function (linha) { return linha.total; }),
                borderColor: marca,
                backgroundColor: marca,
                tension: 0.3,
                spanGaps: false,
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
    });

    // Rosca: as 4 maiores áreas e o resto somado em "Outras".
    const areas = dados("dados-areas").filter(function (linha) { return linha.total !== null; });
    const principais = areas.slice(0, 4);
    const outras = areas.slice(4).reduce(function (soma, linha) { return soma + linha.total; }, 0);
    const rotulos = principais.map(function (linha) { return linha.nome; });
    const valores = principais.map(function (linha) { return linha.total; });
    if (outras) {
        rotulos.push("Outras");
        valores.push(outras);
    }
    new Chart(document.getElementById("grafico-areas"), {
        type: "doughnut",
        data: { labels: rotulos, datasets: [{ data: valores, backgroundColor: tons, borderWidth: 0 }] },
        options: { maintainAspectRatio: false, cutout: "62%", plugins: { legend: { display: false } } },
    });
})();
```

O botão de acessibilidade da barra **não precisa de JS novo**: os dois botões têm `data-alternar`, que o `acessibilidade.js` (já carregado pelo `base.html`) liga, salva no `localStorage` e marca com `aria-pressed`.

## 7️⃣ `painel/metricas.py`: três métricas novas

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

> [!danger] Cada uma tem uma armadilha de privacidade
> | Métrica | Armadilha | Como foi resolvida |
> |---|---|---|
> | `conversao_geral` | A taxa sobre um total conhecido devolve a contagem: 3 salvos ÷ 120 recomendações = 2,5% → 3 | Com menos de K salvos, a taxa é `None` |
> | `tentativas_por_dia` | Um dia com 1 teste diz "alguém respondeu na terça" | A view passa a série por `suprimir_pequenos`: o dia vira `null` e a linha fica com um buraco, explicado na legenda |
> | `atividade_recente` | O design tinha "Nova manifestação · Enfermagem · há 16 min", que aponta para uma pessoa | Só contagens de janela (1 h, 24 h), e também suprimidas |
>
> A **aderência** da tela Quiz caía no mesmo caso da conversão e é corrigida na view (seção 8️⃣).

## 8️⃣ `painel/views.py` e `painel/urls.py`

Substitua o `views.py` inteiro:

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

E o `urls.py`:

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

> [!note] O nome `painel-dashboard` continua
> A rota `/painel/` é a mesma e o nome também. O `base.html` (menu do usuário), o redirecionamento de `/quiz/dashboard/` e o `test_paginas.py` não mudam.

---

## 9️⃣ Testes

### `painel/tests/test_privacidade.py`

Os testes de privacidade abriam uma tela só. Agora os dados estão em duas, então a classe `PrivacidadeNaTelaTest` passa a abrir as duas. Substitua a classe inteira (do `class PrivacidadeNaTelaTest` até o fim do arquivo):

```python
class PrivacidadeNaTelaTest(BasePainel):
    TELAS = ("painel-dashboard", "painel-quiz")

    def setUp(self):
        super().setUp()
        self.staff = self.criar_staff()

    def abrir_painel(self, tela="painel-dashboard"):
        self.client.force_login(self.staff)
        return self.client.get(reverse(tela))

    def test_sem_massa_so_o_total_sai_do_servidor(self):
        self.criar_tentativas(quantidade=K_MINIMO - 1)

        for tela in self.TELAS:
            with self.subTest(tela=tela):
                contexto = self.abrir_painel(tela).context
                self.assertFalse(contexto["tem_massa"])
                self.assertEqual(contexto["total_de_tentativas"], K_MINIMO - 1)
                for chave in ("conversao", "top_primeiro", "confianca", "demanda_por_area", "serie", "atividade"):
                    self.assertNotIn(chave, contexto)

    def test_conversao_suprimida_nao_vaza_pela_taxa(self):
        """taxa x recomendado / 100 reconstruiria o número escondido."""
        tentativas = self.criar_tentativas(quantidade=K_MINIMO + 1)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(usuario=self.criar_usuario("um@exemplo.com"), curso=curso)

        conversao = self.abrir_painel("painel-quiz").context["conversao"]

        linha = next(l for l in conversao if l["id"] == curso.id)
        self.assertTrue(linha["suprimido"])
        self.assertIsNone(linha["interessados"])
        self.assertIsNone(linha["taxa"])

    def test_confianca_tambem_e_suprimida(self):
        self.criar_tentativas(quantidade=K_MINIMO + 1)

        confianca = self.abrir_painel("painel-quiz").context["confianca"]

        for linha in confianca:
            if linha["total"] is not None:
                self.assertGreaterEqual(linha["total"], K_MINIMO)

    def test_nenhum_nome_de_respondente_aparece_na_pagina(self):
        """A regra de privacidade, verificada no HTML servido."""
        nomes = ["Ana Zoraide", "Bento Kling", "Cleo Vasquez", "Dora Pimm", "Eli Nunes", "Fabi Ros"]
        self.criar_tentativas(nomes=nomes)

        for tela in self.TELAS:
            corpo = self.abrir_painel(tela).content.decode()
            for nome in nomes:
                with self.subTest(tela=tela, nome=nome):
                    self.assertNotIn(nome, corpo)
```

> [!important] Nenhum teste de privacidade foi enfraquecido
> Os quatro testes continuam, com as mesmas asserções. A diferença é que `test_sem_massa_so_o_total_sai_do_servidor` e `test_nenhum_nome_de_respondente_aparece_na_pagina` agora rodam **nas duas telas**, e o primeiro também confere `serie` e `atividade`.

### `painel/tests/test_telas.py` (novo)

```python
from datetime import timedelta
from pathlib import Path

from django.urls import reverse
from django.utils import timezone

from accounts.models import Interesse
from painel import metricas
from painel.privacidade import K_MINIMO
from painel.tests.base import BasePainel
from quiz.models import Tentativa_de_resposta

PASTA_DE_TEMPLATES = Path(__file__).resolve().parents[1] / "templates" / "painel"
BOTOES_FANTASMA = ("botao--contorno", "botao--texto", "botao--fantasma")


class CascaDoPainelTest(BasePainel):
    """DSH-01: menu, período e a regra de nenhum botão fantasma."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.criar_staff())

    def test_menu_leva_o_periodo_escolhido(self):
        resposta = self.client.get(reverse("painel-dashboard"), {"periodo": "anual"})

        self.assertContains(resposta, 'href="/painel/quiz/?periodo=anual"')

    def test_periodo_invalido_cai_no_mensal(self):
        resposta = self.client.get(reverse("painel-quiz"), {"periodo": "semanal"})

        self.assertEqual(resposta.context["periodo"], "mensal")

    def test_menu_marca_a_tela_atual(self):
        resposta = self.client.get(reverse("painel-quiz"))

        self.assertContains(resposta, 'href="/painel/quiz/?periodo=mensal" aria-current="page"')

    def test_nenhum_template_do_painel_usa_botao_fantasma(self):
        for arquivo in PASTA_DE_TEMPLATES.glob("*.html"):
            texto = arquivo.read_text(encoding="utf-8")
            for classe in BOTOES_FANTASMA:
                with self.subTest(arquivo=arquivo.name, classe=classe):
                    self.assertNotIn(classe, texto)

    def test_tela_servida_tambem_nao_tem_botao_fantasma(self):
        self.criar_tentativas(quantidade=K_MINIMO)
        for tela in ("painel-dashboard", "painel-quiz"):
            corpo = self.client.get(reverse(tela)).content.decode()
            for classe in BOTOES_FANTASMA:
                with self.subTest(tela=tela, classe=classe):
                    self.assertNotIn(classe, corpo)


class MetricasDoInicioTest(BasePainel):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.criar_staff())

    def test_dia_com_poucos_testes_some_da_serie(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO + 2)
        ontem = timezone.now() - timedelta(days=1)
        Tentativa_de_resposta.objects.filter(pk__in=[t.pk for t in tentativas[:2]]).update(criado_em=ontem)

        serie = self.client.get(reverse("painel-dashboard")).context["serie"]

        self.assertEqual([linha["total"] for linha in serie], [None, K_MINIMO])

    def test_atividade_recente_tambem_e_suprimida(self):
        self.criar_tentativas(quantidade=K_MINIMO)

        atividade = self.client.get(reverse("painel-dashboard")).context["atividade"]

        testes_na_hora, _, cursos_salvos = atividade
        self.assertEqual(testes_na_hora["total"], K_MINIMO)
        self.assertIsNone(cursos_salvos["total"], "zero cursos salvos é menos que K")

    def test_conversao_geral_some_com_poucos_interesses(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(usuario=self.criar_usuario("um@exemplo.com"), curso=curso)

        self.assertIsNone(metricas.conversao_geral(None))

    def test_conversao_geral_e_salvos_sobre_recomendados(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        for i in range(K_MINIMO):
            Interesse.objects.create(usuario=self.criar_usuario(f"aluno{i}@exemplo.com"), curso=curso)

        recomendacoes = sum(t.recomendacoes.count() for t in tentativas)
        self.assertAlmostEqual(metricas.conversao_geral(None), K_MINIMO / recomendacoes * 100)

    def test_aderencia_some_com_poucos_primeiros(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(
            usuario=self.criar_usuario("um@exemplo.com"), curso=curso, rank_snapshot=1, era_principal=True
        )

        aderencia = self.client.get(reverse("painel-quiz")).context["aderencia"]

        self.assertIsNone(aderencia["taxa"])
```

---

## ✅ Verificação

```bash
cd backend
python manage.py test                                # 96 testes
python manage.py makemigrations --check --dry-run   # No changes detected
python manage.py runserver
```

Com um usuário staff, confira à mão:

- [ ] `/painel/` mostra o menu preto, os 4 KPIs, a linha, a rosca, o link ativo e a atividade recente
- [ ] Trocar o período para "Anual" e clicar em "Quiz" no menu mantém "Anual"
- [ ] "Gerar link" e "Fechar links" abrem o modal; "Cancelar" não envia nada; "Fechar links" tem o botão vermelho de perigo
- [ ] Botão de acessibilidade: "Fonte grande" e "Alto contraste" funcionam e continuam ligados depois de recarregar
- [ ] Na largura de celular (DevTools, 375px): barra inferior, KPIs em 2×2, e "Mais" abre o menu por cima
- [ ] Com menos de 5 testes no período, só o total aparece e o aviso de privacidade fica no lugar dos gráficos

## 📦 Commit e PR

```bash
git add -A
git commit -m "feat(painel): casca nova com telas Inicio e Quiz

- base_painel com menu lateral, barra do topo e menu inferior no celular
- botoes solidos (secundario, suave, neutro, perigo) e teste contra botao fantasma
- Inicio: conversao geral, testes por dia e atividade recente, todos suprimidos
- Quiz: rankings, confianca, aderencia suprimida, conversao, orfaos e cobertura
- remove dashboard.html (431 linhas de estilo inline)"
git push -u origin feature/painel-casca-inicio-quiz
gh pr create --base develop --fill
```

> [!success] Definition of Done
> 96 testes, CI verde, nenhum `style=""` nos templates novos além da largura da barra de aderência, e o checklist acima conferido no navegador. Para a banca, o teste `test_nenhum_template_do_painel_usa_botao_fantasma` é a prova de que a regra do design vale no código.
