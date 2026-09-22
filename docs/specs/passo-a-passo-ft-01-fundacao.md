---
title: "Passo a passo — FT-01 a FT-04, FT-15 e FT-16 (fundação do front e acabamento) · Pessoa D"
aliases: ["Passo a passo FT fundação", "Fundação do front", "PR-F1", "PR-F5", "Tokens e componentes"]
tags: [tcc, front, css, django, templates, acessibilidade, execucao, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-templates|🎨 Spec do front]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-templates|🗂️ Plano]] · Colegas: [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-05-ft-07-quiz|❓ A]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-08-ft-10-resultado-curso|🎯 B]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-11-ft-14-conta-painel|👤 C]]

# 🧱 Passo a passo — Fundação do front (pessoa D)

> [!abstract] O que esta nota é
> O **como** da base que as outras três pessoas usam: as cores do guia em variáveis, o esqueleto das páginas, os componentes e o teste que abre toda tela. E, no fim, a limpeza e a revisão final.
> Dois PRs: **PR-F1** (FT-01 a FT-04), que entra **no primeiro dia**, e **PR-F5** (FT-15 e FT-16), que fecha o trabalho.

> [!success] O que já foi verificado (2026-09-22)
> Todo o código desta nota foi aplicado numa cópia da `main` em `ac471c0`, junto com as notas de A, B e C: **64 testes, 63 verdes** (o vermelho é o do fuso). O topo, os botões de letra grande e contraste e o comportamento no celular (390 px) foram conferidos no navegador.

## 🧭 O mapa

| Tarefa | Arquivos | PR |
|---|---|---|
| **FT-01** tokens | `static/css/tokens.css` | PR-F1 |
| **FT-02** esqueleto | `static/css/base.css` · `templates/base.html` | PR-F1 |
| **FT-03** componentes | `static/css/componentes.css` · `static/js/acessibilidade.js` · `templates/componentes/_anel.html`, `_barra.html`, `_topo_voltar.html` | PR-F1 |
| **FT-04** rede de proteção | `quiz/tests/test_paginas.py` · remover `static/css/style.css` | PR-F1 |
| **FT-15** limpeza | remover `quiz/views.py`, `templates/quiz/dashboard.html`, `templates/quiz/curso_detalhe.html`, `accounts/templates/accounts/perfil.html` | PR-F5 |
| **FT-16** revisão final | roteiro manual | PR-F5 |

---

## 🚦 Antes de abrir o editor

```bash
git switch main && git pull
git tag antes-do-front-novo       # o plano B da banca: a última versão com o visual antigo
git push origin antes-do-front-novo
git switch -c front/fundacao
cd backend
python manage.py test 2>&1 | tail -3     # a linha de base
```

> [!important] Por que a tag
> O PR-F1 tira o `style.css`. Até os PRs de A, B e C entrarem, as telas ficam sem cor. Se alguém precisar mostrar o sistema nesse meio-tempo, `git switch --detach antes-do-front-novo` volta para a versão que funciona.

---

## 1️⃣ FT-01 — `backend/static/css/tokens.css` (arquivo novo)

As cinco cores do guia de estilo, os tons de apoio do protótipo, a fonte e as medidas. **É o único arquivo do projeto com hexadecimal.**

```css
/* Tokens do EducMatch: guia de estilo (cores do SENAI, Space Grotesk)
   + os tons de apoio do protótipo de alta fidelidade.
   Toda cor e medida do projeto sai daqui. Nenhum outro arquivo tem hexadecimal. */

@import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap");

:root {
  /* Guia de estilo */
  --marca: #d9251c;          /* botões e destaques */
  --marca-hover: #d84942;    /* hover dos botões */
  --tinta: #2d2d2d;          /* texto principal */
  --gelo: #ede8e4;           /* texto sobre botão no hover, fundos quentes */
  --branco: #fffefe;

  /* Apoio (protótipo) */
  --preto: #09090b;          /* cabeçalho e faixas escuras */
  --preto-2: #2d2d31;        /* pílulas e hover sobre o preto */
  --titulo: #6b1210;         /* títulos H1 em vermelho profundo */
  --marca-escuro: #b01e16;
  --marca-claro: #fdecea;    /* chip de área */
  --marca-clarinho: #fef5f4; /* caixas de destaque suave */
  --texto-2: #52525b;        /* texto secundário */
  --texto-3: #71717a;        /* legendas */
  --linha: #e4e4e7;          /* bordas */
  --fundo: #f9fafb;          /* fundo da página */
  --superficie: #ffffff;     /* cartões */
  --sucesso: #16a34a;
  --alerta: #b45309;
  --erro: #dc2626;
  --foco: var(--marca);

  /* Nomes antigos, mantidos para o que ainda usa (painel.css): não use em código novo */
  --vermelho: var(--marca);
  --vermelho-escuro: var(--marca-escuro);
  --cinza: var(--texto-3);

  /* Tipografia */
  --fonte: "Space Grotesk", system-ui, sans-serif;
  --tamanho-base: 17px;
  --h1: clamp(1.75rem, 4vw, 2.4rem);
  --h2: clamp(1.25rem, 2.6vw, 1.55rem);
  --pequeno: 0.85rem;

  /* Forma */
  --raio: 12px;
  --raio-botao: 8px;
  --raio-pilula: 999px;
  --sombra: 0 1px 2px rgba(9, 9, 11, 0.06), 0 8px 24px rgba(9, 9, 11, 0.06);
  --alvo: 48px;              /* altura mínima de tudo que se clica */
  --largura: 600px;          /* coluna de leitura */
}

/* Botão "A" do cabeçalho: letra maior para quem precisa */
:root.fonte-grande {
  --tamanho-base: 20px;
}

/* Botão "contraste" do cabeçalho */
:root.alto-contraste {
  --marca: #b3160f;
  --marca-hover: #8f110b;
  --tinta: #000000;
  --titulo: #000000;
  --texto-2: #1f1f23;
  --texto-3: #2d2d2d;
  --linha: #2d2d2d;
  --fundo: #ffffff;
}
```

> [!note] Os "nomes antigos"
> `--vermelho`, `--vermelho-escuro` e `--cinza` existem só porque o `painel.css` ainda os usa. A pessoa C troca na FT-14; depois disso, as três linhas podem sair.

> [!tip] Letra grande e alto contraste sem uma linha de CSS nas telas
> As duas classes (`.fonte-grande` e `.alto-contraste`) só **redefinem tokens**. Como toda tela usa os tokens, o modo inteiro funciona de graça. É o motivo da regra "nenhum hexadecimal fora do `tokens.css`": uma cor escrita direto numa tela não muda no alto contraste.

---

## 2️⃣ FT-02 — o esqueleto

### `backend/static/css/base.css` (arquivo novo)

Reset, tipografia, topo, conteúdo, rodapé e o ajuste de celular do topo.

```css
/* Base: reset, tipografia e o esqueleto da página (topo, conteúdo, rodapé). */

*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  font-size: var(--tamanho-base);
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: var(--fonte);
  line-height: 1.5;
  color: var(--tinta);
  background: var(--fundo);
  -webkit-font-smoothing: antialiased;
}

h1,
h2,
h3 {
  margin: 0 0 0.5em;
  line-height: 1.15;
  letter-spacing: -0.02em;
}

h1 {
  font-size: var(--h1);
  color: var(--titulo);
}

h2 {
  font-size: var(--h2);
}

h3 {
  font-size: 1.05rem;
}

p {
  margin: 0 0 1em;
}

a {
  color: inherit;
}

img,
svg {
  max-width: 100%;
}

button,
input,
select,
textarea {
  font: inherit;
  color: inherit;
}

/* Foco sempre visível para quem navega pelo teclado */
:focus-visible {
  outline: 3px solid var(--foco);
  outline-offset: 3px;
  border-radius: 4px;
}

/* ---------- Topo ---------- */

.topo {
  background: var(--preto);
  color: var(--branco);
}

.topo__inner {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 1120px;
  min-height: 64px;
  margin: 0 auto;
  padding: 8px 20px;
}

.marca {
  font-size: 1.15rem;
  font-weight: 700;
  text-decoration: none;
}

.topo__tagline {
  padding: 2px 10px;
  border-radius: var(--raio-pilula);
  background: var(--preto-2);
  font-size: 0.75rem;
}

.topo__nav {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.topo__icone {
  display: inline-grid;
  place-items: center;
  min-width: 40px;
  min-height: 40px;
  border: 0;
  border-radius: var(--raio-botao);
  background: transparent;
  color: var(--branco);
  cursor: pointer;
}

.topo__icone:hover,
.topo__icone[aria-pressed="true"] {
  background: var(--preto-2);
}

.usuario-menu {
  position: relative;
}

.usuario-menu summary {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 10px;
  border-radius: var(--raio-botao);
  cursor: pointer;
  list-style: none;
}

.usuario-menu summary::-webkit-details-marker {
  display: none;
}

.usuario-menu__dropdown {
  position: absolute;
  right: 0;
  z-index: 10;
  display: grid;
  min-width: 200px;
  margin-top: 6px;
  padding: 6px;
  border-radius: var(--raio);
  background: var(--superficie);
  color: var(--tinta);
  box-shadow: var(--sombra);
}

.usuario-menu__dropdown a,
.usuario-menu__dropdown button {
  display: block;
  width: 100%;
  min-height: 44px;
  padding: 10px 12px;
  border: 0;
  border-radius: var(--raio-botao);
  background: none;
  text-align: left;
  text-decoration: none;
  cursor: pointer;
}

.usuario-menu__dropdown a:hover,
.usuario-menu__dropdown button:hover {
  background: var(--fundo);
}

/* ---------- Conteúdo e rodapé ---------- */

.conteudo {
  flex: 1;
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: clamp(24px, 5vw, 56px) 20px;
}

.rodape {
  padding: 20px;
  color: var(--texto-3);
  font-size: var(--pequeno);
  text-align: center;
}

.rodape p {
  margin: 0;
}

/* Quem pediu menos movimento no sistema não vê animação */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}

/* ---------- Celular ---------- */

@media (max-width: 520px) {
  .topo__tagline {
    display: none;
  }

  .topo__inner {
    gap: 4px;
    padding: 8px 12px;
  }

  .topo__nav .botao {
    min-height: 40px;
    padding: 0 12px;
  }

  /* Fica só o ícone na tela; o "Olá, Nome" continua para o leitor de tela */
  .usuario-menu summary span {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
  }
}
```

> [!warning] No celular, o nome do usuário some da tela, mas **não** do leitor de tela
> O "Olá, Ana" é o único texto do botão do menu. Com `display: none`, o botão ficaria sem nome para quem usa leitor de tela. Por isso a regra de 520 px usa o mesmo truque da `.visualmente-oculto`.

### `backend/templates/base.html` (substitua)

```django
{% load static %}<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Descubra seu curso ideal{% endblock %} · EducMatch</title>
    <script>
        // Aplica fonte grande e contraste ANTES de pintar a tela, para não piscar.
        try {
            if (localStorage.getItem("fonte-grande") === "1") document.documentElement.classList.add("fonte-grande");
            if (localStorage.getItem("alto-contraste") === "1") document.documentElement.classList.add("alto-contraste");
        } catch (e) {}
    </script>
    <link rel="stylesheet" href="{% static 'css/tokens.css' %}">
    <link rel="stylesheet" href="{% static 'css/base.css' %}">
    <link rel="stylesheet" href="{% static 'css/componentes.css' %}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
    {% block estilos %}{% endblock %}
</head>
<body>
    {% block topo %}
    <header class="topo">
        <div class="topo__inner">
            <a class="marca" href="{% url 'quiz-inicio' %}">QuizPessoal</a>
            <span class="topo__tagline">Orientação profissional</span>

            <nav class="topo__nav" aria-label="Navegação principal">
                <button class="topo__icone" type="button" data-alternar="fonte-grande"
                        aria-pressed="false" title="Aumentar a letra">
                    <span aria-hidden="true">A<i class="fa-solid fa-magnifying-glass-plus"></i></span>
                    <span class="visualmente-oculto">Aumentar a letra</span>
                </button>
                <button class="topo__icone" type="button" data-alternar="alto-contraste"
                        aria-pressed="false" title="Alto contraste">
                    <i class="fa-solid fa-circle-half-stroke" aria-hidden="true"></i>
                    <span class="visualmente-oculto">Alto contraste</span>
                </button>

                {% if user.is_authenticated %}
                <details class="usuario-menu">
                    <summary>
                        <i class="fa-solid fa-user" aria-hidden="true"></i>
                        <span>Olá, {{ user.first_name|default:user.email }}</span>
                    </summary>
                    <div class="usuario-menu__dropdown">
                        <a href="{% url 'lista_interesse' %}">Minha lista</a>
                        <a href="{% url 'minhas-tentativas' %}">Meus testes</a>
                        <a href="{% url 'aluno-perfil' %}">Meu perfil</a>
                        {% if user.is_staff %}<a href="{% url 'painel-dashboard' %}">Painel</a>{% endif %}
                        <form method="post" action="{% url 'logout' %}">
                            {% csrf_token %}
                            <button type="submit">Sair</button>
                        </form>
                    </div>
                </details>
                {% else %}
                <a class="botao botao--contorno" href="{% url 'entrar' %}">Entrar</a>
                {% endif %}
            </nav>
        </div>
    </header>
    {% endblock %}

    <main class="conteudo" id="conteudo">
        {% if messages %}
        <ul class="mensagens" role="status">
            {% for mensagem in messages %}
            <li class="mensagem mensagem--{{ mensagem.tags }}">{{ mensagem }}</li>
            {% endfor %}
        </ul>
        {% endif %}

        {% block content %}{% endblock %}
    </main>

    {% block rodape %}
    <footer class="rodape">
        <p>Recomendações calculadas por similaridade de perfil · SENAI</p>
    </footer>
    {% endblock %}

    <script src="{% static 'js/acessibilidade.js' %}" defer></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

| Bloco | Para quê | Quem usa |
|---|---|---|
| `{% block estilos %}` | o CSS da tela | todas as telas |
| `{% block topo %}` | trocar o topo inteiro | detalhe do curso, entrar, criar conta (topo só com "Voltar") |
| `{% block rodape %}` | trocar ou tirar o rodapé | — |
| `{% block scripts %}` | o JS da tela | quiz, resultado, painel |

> [!note] O `<script>` pequeno dentro do `<head>`
> Ele aplica letra grande e contraste **antes** de a página aparecer. Sem ele, quem ligou o alto contraste veria a página normal por um instante e depois ela mudaria (o "piscar").

---

## 3️⃣ FT-03 — os componentes

### `backend/static/css/componentes.css` (arquivo novo)

```css
/* Componentes reaproveitados por todas as telas.
   Regra: tela nova usa estas classes antes de inventar outra. */

/* ---------- Botões ---------- */

.botao {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: var(--alvo);
  padding: 0 24px;
  border: 2px solid var(--marca);
  border-radius: var(--raio-botao);
  background: var(--marca);
  color: var(--branco);
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.botao:hover {
  border-color: var(--marca-hover);
  background: var(--marca-hover);
  color: var(--gelo);
}

.botao--bloco {
  width: 100%;
}

/* Contorno: ação secundária ("Refazer o teste") */
.botao--contorno {
  background: transparent;
  color: var(--marca);
}

.botao--contorno:hover {
  background: var(--marca-clarinho);
  color: var(--marca-escuro);
}

/* Texto: ação terciária ("Salvar resultado em PDF", "Remover") */
.botao--texto {
  border-color: transparent;
  background: transparent;
  color: var(--marca);
  padding: 0 12px;
}

.botao--texto:hover {
  border-color: transparent;
  background: var(--marca-clarinho);
  color: var(--marca-escuro);
}

/* ---------- Voltar ---------- */

.voltar {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 40px;
  color: var(--marca);
  font-weight: 700;
  text-decoration: none;
}

.voltar::before {
  content: "‹";
  font-size: 1.4em;
  line-height: 1;
}

.topo .voltar {
  color: var(--branco);
}

/* ---------- Chips ---------- */

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 1em;
  padding: 0;
  list-style: none;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border: 1px solid var(--linha);
  border-radius: var(--raio-pilula);
  background: var(--superficie);
  font-size: var(--pequeno);
  font-weight: 600;
}

.chip--escuro {
  border-color: var(--preto);
  background: var(--preto);
  color: var(--branco);
}

.chip--area {
  border-color: var(--marca-claro);
  background: var(--marca-claro);
  color: var(--titulo);
}

.chip--marca {
  border-color: var(--marca);
  background: var(--marca);
  color: var(--branco);
}

/* ---------- Cartões ---------- */

.cartao {
  padding: clamp(20px, 4vw, 40px);
  border: 1px solid var(--linha);
  border-radius: var(--raio);
  background: var(--superficie);
  box-shadow: var(--sombra);
}

/* Cartão central das telas curtas (boas-vindas, entrar, criar conta) */
.cartao--centro {
  width: 100%;
  max-width: var(--largura);
  margin: 0 auto;
}

.cartao--estreito {
  max-width: 420px;
}

.subtitulo {
  color: var(--texto-2);
}

.nota {
  color: var(--texto-3);
  font-size: var(--pequeno);
  text-align: center;
}

/* ---------- Campos de formulário ---------- */

.campo {
  display: grid;
  gap: 6px;
  margin-bottom: 18px;
  font-weight: 600;
}

.campo__opcional {
  color: var(--texto-3);
  font-weight: 400;
}

.campo input {
  width: 100%;
  min-height: var(--alvo);
  padding: 0 14px;
  border: 1.5px solid var(--linha);
  border-radius: var(--raio-botao);
  background: var(--superficie);
  font-weight: 400;
}

.campo input:focus-visible {
  border-color: var(--marca);
}

.campo__ajuda {
  margin: 0;
  color: var(--texto-3);
  font-size: var(--pequeno);
  font-weight: 400;
}

.campo__erro {
  margin: 0;
  color: var(--erro);
  font-size: var(--pequeno);
  font-weight: 600;
}

.campo--com-erro input {
  border-color: var(--erro);
}

/* ---------- Barra de porcentagem ---------- */

.barra {
  height: 6px;
  border-radius: var(--raio-pilula);
  background: var(--marca-claro);
  overflow: hidden;
}

.barra__valor {
  display: block;
  width: var(--valor, 0%);
  height: 100%;
  border-radius: inherit;
  background: var(--marca);
}

.barra--escura .barra__valor {
  background: var(--preto);
}

/* ---------- Anel de afinidade ---------- */

.anel {
  --tamanho: 120px;
  position: relative;
  display: grid;
  place-items: center;
  width: var(--tamanho);
  height: var(--tamanho);
}

.anel svg {
  position: absolute;
  inset: 0;
  transform: rotate(-90deg);
}

.anel__fundo {
  fill: none;
  stroke: var(--marca-claro);
  stroke-width: 8;
}

.anel__valor {
  fill: none;
  stroke: var(--marca);
  stroke-width: 8;
  stroke-linecap: round;
  /* circunferência de r=52: 2 x pi x 52 = 326.7 */
  stroke-dasharray: 326.7;
  stroke-dashoffset: calc(326.7 - 326.7 * var(--valor) / 100);
}

.anel__numero {
  font-size: 1.9rem;
  font-weight: 700;
}

/* ---------- Mensagens (Django messages) ---------- */

.mensagens {
  display: grid;
  gap: 8px;
  max-width: var(--largura);
  margin: 0 auto 24px;
  padding: 0;
  list-style: none;
}

.mensagem {
  padding: 12px 16px;
  border-left: 4px solid var(--tinta);
  border-radius: var(--raio-botao);
  background: var(--superficie);
  box-shadow: var(--sombra);
}

.mensagem--success {
  border-color: var(--sucesso);
}

.mensagem--warning {
  border-color: var(--alerta);
}

.mensagem--error {
  border-color: var(--erro);
}

/* ---------- Avisos dentro da página ---------- */

.aviso {
  padding: 12px 16px;
  border-left: 4px solid var(--marca);
  border-radius: var(--raio-botao);
  background: var(--marca-clarinho);
}

/* ---------- Estado vazio ---------- */

.vazio {
  padding: 32px;
  border: 1.5px dashed var(--linha);
  border-radius: var(--raio);
  text-align: center;
  color: var(--texto-2);
}

/* ---------- Utilidades ---------- */

/* Escondido na tela, lido pelo leitor de tela */
.visualmente-oculto {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.pilha {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
}
```

### `backend/static/js/acessibilidade.js` (arquivo novo)

```javascript
// Botões de acessibilidade do cabeçalho: letra maior e alto contraste.
// Cada botão liga/desliga uma classe no <html> e lembra a escolha no navegador.
// O <head> do base.html aplica a escolha antes de pintar a tela.
(function () {
    const raiz = document.documentElement;

    document.querySelectorAll("[data-alternar]").forEach(function (botao) {
        const classe = botao.dataset.alternar;
        botao.setAttribute("aria-pressed", String(raiz.classList.contains(classe)));

        botao.addEventListener("click", function () {
            const ligado = raiz.classList.toggle(classe);
            botao.setAttribute("aria-pressed", String(ligado));
            try {
                localStorage.setItem(classe, ligado ? "1" : "0");
            } catch (e) {
                // Navegador sem localStorage (aba anônima restrita): vale só nesta página.
            }
        });
    });
})();
```

### `backend/templates/componentes/_anel.html` (arquivo novo)

```django
{# Anel de afinidade. Uso: {% include "componentes/_anel.html" with valor=96 %} #}
<div class="anel" style="--valor: {{ valor }}" role="img" aria-label="{{ valor }}% de afinidade">
    <svg viewBox="0 0 120 120" aria-hidden="true">
        <circle class="anel__fundo" cx="60" cy="60" r="52"></circle>
        <circle class="anel__valor" cx="60" cy="60" r="52"></circle>
    </svg>
    <span class="anel__numero" aria-hidden="true">{{ valor }}%</span>
</div>
```

> [!note] Como o anel é desenhado
> Um círculo SVG de raio 52 tem 326,7 de circunferência. O `stroke-dasharray` faz o traço ter esse tamanho, e o `stroke-dashoffset` esconde a parte que falta para 100%. O valor chega pela variável `--valor`, e o CSS faz a conta. O `role="img"` com `aria-label` faz o leitor de tela dizer "87% de afinidade", em vez de ler o SVG.

### `backend/templates/componentes/_barra.html` (arquivo novo)

```django
{# Barra de porcentagem. Uso: {% include "componentes/_barra.html" with valor=48 %} (escura=True para a preta) #}
<div class="barra{% if escura %} barra--escura{% endif %}" aria-hidden="true">
    <span class="barra__valor" style="--valor: {{ valor|stringformat:'s' }}%"></span>
</div>
```

> [!danger] O `stringformat:'s'` não é enfeite
> Com `LANGUAGE_CODE = "pt-br"`, o Django escreve `59.3` como **`59,3`**. No CSS, `--valor: 59,3%` é inválido, e a barra some sem erro nenhum. O `stringformat:'s'` escreve o número com ponto.

### `backend/templates/componentes/_topo_voltar.html` (arquivo novo)

```django
{# Topo só com "Voltar" (telas 10 e 11). Uso: {% include "componentes/_topo_voltar.html" with destino=url texto="Voltar" %} #}
<header class="topo">
    <div class="topo__inner">
        <a class="voltar" href="{{ destino }}">{{ texto|default:"Voltar" }}</a>
    </div>
</header>
```

> [!danger] Comentário de template é de **uma linha só**
> `{# ... #}` só funciona numa linha. Se o comentário continuar na linha de baixo, o Django **executa** o que estiver dentro dele. Na verificação, um exemplo de `{% include %}` escrito num comentário de duas linhas fez o template incluir a si mesmo até dar `RecursionError`. Comentário de várias linhas é `{% comment %} ... {% endcomment %}`.

---

## 4️⃣ FT-04 — a rede de proteção

### `backend/quiz/tests/test_paginas.py` (arquivo novo)

```python
from django.urls import reverse

from catalogo.models import Curso
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class TodaPaginaAbreTest(BaseEducMatch):
    """Smoke test das telas: toda página abre (200) e usa o CSS novo.

    Pega erro de template que nenhum outro teste pega, como um include que se
    chama a si mesmo ou uma variável com nome errado.
    """

    def abrir(self, url):
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200, url)
        self.assertContains(resposta, "css/tokens.css", msg_prefix=url)
        return resposta

    def test_paginas_publicas(self):
        self.responder_tudo()
        tentativa = Tentativa_de_resposta.objects.latest("id")
        curso = Curso.objects.filter(is_active=True).first()

        for url in (
            reverse("quiz-inicio"),
            reverse("quiz-resultado", args=[tentativa.pk]),
            reverse("curso-detalhe", args=[curso.pk]),
            reverse("entrar"),
            reverse("cadastro_usuario"),
        ):
            with self.subTest(url=url):
                self.abrir(url)

    def test_paginas_da_conta(self):
        self.client.force_login(self.criar_usuario())
        self.responder_tudo()

        for url in (
            reverse("lista_interesse"),
            reverse("minhas-tentativas"),
            reverse("aluno-perfil"),
        ):
            with self.subTest(url=url):
                self.abrir(url)

    def test_painel_para_staff(self):
        self.client.force_login(self.criar_usuario("coord@exemplo.com", is_staff=True))
        self.abrir(reverse("painel-dashboard"))

    def test_nenhuma_pagina_usa_o_css_antigo(self):
        self.responder_tudo()
        for url in (reverse("quiz-inicio"), reverse("entrar")):
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), "css/style.css")
```

> [!important] Por que este teste existe
> Nenhum outro teste abria a tela de login. Foi assim que o `RecursionError` do comentário passou por uma suíte "verde". Este teste abre **toda** página, logado e deslogado, e é o que pega erro de template antes da banca.

### Remover o CSS antigo

```bash
git rm backend/static/css/style.css
```

O `base.html` novo já não carrega o `style.css`. O `test_nenhuma_pagina_usa_o_css_antigo` garante que ninguém o traz de volta.

## ✅ PR-F1 — pronto quando

```bash
python manage.py check
python manage.py test quiz.tests.test_paginas -v 2
python manage.py test 2>&1 | tail -3
grep -rn "#[0-9a-fA-F]\{3,6\}" static/css --include=*.css | grep -v tokens.css     # só o painel.css, até a FT-14
```

- [ ] Toda página tem o topo preto com "QuizPessoal" e a pílula "Orientação profissional"
- [ ] O botão "A" aumenta a letra, o de meio círculo liga o alto contraste; F5 e os dois continuam ligados
- [ ] Em 390 px, o topo cabe sem rolagem lateral

```bash
git add -A
git commit -m "feat(front): tokens do guia, base e componentes (FT-01 a FT-04)"
git push -u origin front/fundacao
```

> [!important] Mescle **no mesmo dia** e avise
> "PR-F1 entrou: `git pull` e `git merge origin/main` na sua branch de front. As classes do `componentes.css` estão prontas."

---

## 5️⃣ FT-15 — limpeza (PR-F5)

```bash
git switch main && git pull
git switch -c front/acabamento
```

Quatro arquivos que ninguém usa e que confundem quem chega:

| Arquivo | Por que sair |
|---|---|
| `backend/quiz/views.py` | Só tinha o `dashboard_view` antigo. Nenhuma rota o importa: `/quiz/dashboard/` redireciona para `/painel/` |
| `backend/templates/quiz/dashboard.html` | O template daquele dashboard |
| `backend/templates/quiz/curso_detalhe.html` | A versão antiga; a de verdade é `catalogo/templates/catalogo/curso_detalhe.html` |
| `backend/accounts/templates/accounts/perfil.html` | Vazio. O perfil usa `templates/quiz/aluno_perfil.html` |

```bash
grep -rn "quiz.views\|dashboard_view\|quiz/dashboard.html\|quiz/curso_detalhe.html\|accounts/perfil.html" --include=*.py --include=*.html backend
```

O `grep` tem de voltar vazio antes do `git rm`:

```bash
git rm backend/quiz/views.py backend/templates/quiz/dashboard.html backend/templates/quiz/curso_detalhe.html backend/accounts/templates/accounts/perfil.html
```

---

## 6️⃣ FT-16 — revisão final

Com os PRs F2, F3 e F4 mesclados. Anote cada item no PR-F5.

### Visual (1440 px e 390 px)

| # | Tela | Compare com |
|---|---|---|
| 1 | `/` | mockup 01 |
| 2 | Perguntas 1 e 6 | mockups 02 e 07 |
| 3 | Clicar em "Ver meus cursos" | mockup 08 (aparece por um instante) |
| 4 | `/resultado/<id>/` | mockup 09 |
| 5 | Detalhe do curso | mockup 10 |
| 6 | `/entrar/` | mockup 11 |
| 7 | `/lista_interesse/` | mockup 12 |

No DevTools, em 390 px, rode em cada tela:

```js
document.documentElement.scrollWidth > document.documentElement.clientWidth   // tem de dar false
```

### Teclado

- [ ] Da tela 01 até o resultado, **sem o mouse**: Tab, setas (troca a opção), Enter (avança)
- [ ] O foco aparece em **todo** link e botão, inclusive no "Voltar" e nas opções
- [ ] No resultado, Tab passa **uma vez** por curso da lista (o link do nome), e não por pedaços da linha

### Sem JavaScript

DevTools → ⚙️ → *Debugger* → **Disable JavaScript**:

- [ ] Boas-vindas → Começar → as 6 perguntas pelo "Próxima" → "Ver meus cursos" → resultado
- [ ] O "Salvar resultado em PDF" some (e o `Ctrl+P` imprime a página limpa)

### Contraste e letra grande

- [ ] Com os dois ligados, toda tela continua legível e nada se sobrepõe

### Cores

```bash
grep -rn "#[0-9a-fA-F]\{3,6\}" backend/static/css --include=*.css | grep -v tokens.css
```

Tem de voltar **vazio**. Se o `painel.css` aparecer, a FT-14 não terminou.

Commit: `chore(front): limpeza e revisao final (FT-15 e FT-16)`.

## ▶️ Próxima ação

Criar a tag `antes-do-front-novo`, a branch `front/fundacao` e fazer a §1.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-front-templates|🎨 Spec do front]] — a tabela de tokens e componentes
- [[Projetos/EducMatch(Secretária)/plano-execucao-front-templates|🗂️ Plano]] — rodadas e dono por arquivo
