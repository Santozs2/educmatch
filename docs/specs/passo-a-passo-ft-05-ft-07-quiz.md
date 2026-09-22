---
title: "Passo a passo — FT-05 a FT-07 (boas-vindas, perguntas e \"Analisando\") · Pessoa A"
aliases: ["Passo a passo FT quiz", "Front do quiz", "PR-F2", "Wizard em CSS"]
tags: [tcc, front, css, javascript, django, templates, acessibilidade, execucao, passo-a-passo]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-templates|🎨 Spec do front]] · Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-templates|🗂️ Plano]] · Base: [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-01-fundacao|🧱 Fundação (D)]] · Mockups: `Downloads/altaFidelidade/Alta fidelidade 01` a `08`

# ❓ Passo a passo — o quiz (pessoa A)

> [!abstract] O que esta nota é
> O **como** das telas 01 a 08 do protótipo: boas-vindas, as seis perguntas (uma por vez) e a tela "Analisando seu perfil". Um PR só, o **PR-F2**, em três arquivos: `quiz.html`, `quiz.css` e `quiz.js`.

> [!success] O que já foi verificado (2026-09-22)
> Aplicado numa cópia da `main` junto com as outras notas: a tela 01 e as perguntas batem com os mockups 01 a 07 em 1440 px e 390 px; o quiz vai do "Começar" até o resultado; **com teclas de verdade**, a seta troca a opção sem avançar, o Enter avança e o foco vai para o enunciado, e o clique avança sozinho.

> [!important] A ideia central: o quiz funciona **sem JavaScript**
> Cada pergunta é um `<fieldset id="questao-N">`. Os links "Próxima" e "Voltar" só trocam o `#` da URL, e o CSS mostra **só** a pergunta cujo `id` é o `#` atual (a pseudo-classe `:target`). Todas as perguntas estão dentro do **mesmo** `<form>`: as escondidas continuam sendo enviadas.
> O `quiz.js` não controla nada disso. Ele só acrescenta conforto. Se o JS falhar na apresentação, o quiz continua respondível.

## 🧭 O mapa

| Tarefa | Tela | O que entrega |
|---|---|---|
| **FT-05** | 01 · boas-vindas | cartão com título, chips, nome opcional, "Começar" |
| **FT-06** | 02–07 · perguntas | barra de progresso, "Voltar", "Pergunta N de 6", opções numeradas, rodapé fixo com "Próxima" |
| **FT-07** | 08 · "Analisando" | `quiz.js`: avança ao clicar, Enter avança, foco na pergunta nova, tela de espera no envio |

> [!warning] O que o `quiz.js` antigo fazia (e por que sai inteiro)
> Ele ligava e desligava as classes `quiz--wizard` e `esta-ativo`, mas **nenhum CSS usava essas classes**: quem mostrava a pergunta era o `:target`. Por isso o avanço automático e a barra de progresso nunca funcionaram. O arquivo novo trabalha **com** o `:target`: para avançar, ele troca o `#` da URL, igual ao link faria.

---

## 🚦 Antes de abrir o editor

```bash
git switch main && git pull          # já com o PR-F1 da pessoa D
git switch -c front/quiz
```

Sem o PR-F1, as classes `.botao`, `.cartao`, `.chip`, `.campo`, `.barra` e `.voltar` não existem. Se ele ainda não entrou, comece pela estrutura HTML e faça `git merge origin/main` quando ele entrar.

---

## 1️⃣ FT-05 e FT-06 — `backend/templates/quiz/quiz.html` (substitua)

```django
{% extends "base.html" %}
{% load static %}

{% block title %}Quiz de orientação{% endblock %}

{% block estilos %}<link rel="stylesheet" href="{% static 'css/quiz.css' %}">{% endblock %}

{% block content %}
{% if via_link %}
<p class="aviso quiz-aviso-link" role="note">Você está respondendo pelo link da escola.</p>
{% endif %}

{% if not quiz_iniciado %}
{# Tela 01 · Boas-vindas. GET: sem JS, o "Começar" já leva à pergunta 1. #}
<form class="cartao cartao--centro quiz-intro" method="get" action="{% url 'quiz-inicio' %}#questao-1">
    <h1>Descubra o curso certo para o seu perfil</h1>
    <p class="subtitulo">
        Responda a {{ questoes|length }} perguntas simples sobre o seu jeito de trabalhar
        e descubra as áreas que mais combinam com você.
    </p>

    <ul class="chips">
        <li class="chip chip--escuro">Leva 2 minutos</li>
        <li class="chip">Sem cadastro</li>
        <li class="chip">{{ questoes|length }} perguntas</li>
    </ul>

    <label class="campo">
        <span>Seu nome <span class="campo__opcional">(opcional)</span></span>
        <input type="text" name="respondido_por" maxlength="100"
               value="{{ respondido_por|default:'' }}" autocomplete="given-name">
    </label>
    <input type="hidden" name="etapa" value="1">

    <button class="botao botao--bloco" type="submit">Começar</button>
    <p class="nota">Nenhum dado seu é compartilhado.</p>
</form>
{% endif %}

{# Telas 02 a 07 · uma pergunta por vez. O CSS mostra só a pergunta do #questao-N da URL. #}
<form class="quiz-form" method="post" action="{% url 'quiz-inicio' %}" data-quiz novalidate>
    {% csrf_token %}
    <input type="hidden" name="respondido_por" value="{{ respondido_por|default:'' }}">

    {% for questao in questoes %}
    <fieldset class="quiz-passo" id="questao-{{ forloop.counter }}" data-passo>
        <div class="barra quiz-passo__progresso" aria-hidden="true">
            <span class="barra__valor" style="--valor: {% widthratio forloop.counter questoes|length 100 %}%"></span>
        </div>

        <div class="quiz-passo__topo">
            {% if forloop.first %}
            <a class="voltar" href="{% url 'quiz-inicio' %}">Voltar</a>
            {% else %}
            <a class="voltar" href="#questao-{{ forloop.counter0 }}">Voltar</a>
            {% endif %}
            <span class="quiz-passo__contador">Pergunta {{ forloop.counter }} de {{ questoes|length }}</span>
        </div>

        <div class="quiz-passo__corpo">
            <legend tabindex="-1">
                <span class="quiz-passo__numero">{{ forloop.counter }}.</span>
                {{ questao.texto }}
            </legend>

            <div class="opcoes">
                {% for alternativa in questao.alternativas.all %}
                <label class="opcao">
                    <input type="radio" name="questao_{{ questao.id }}" value="{{ alternativa.id }}"
                           {% if alternativa.id == questao.marcada_id %}checked{% endif %}>
                    <span class="opcao__numero" aria-hidden="true">{{ forloop.counter }}</span>
                    <span class="opcao__texto">{{ alternativa.texto }}</span>
                </label>
                {% endfor %}
            </div>

            <p class="quiz-passo__aviso" data-aviso hidden role="alert">Escolha uma opção para continuar.</p>
        </div>

        <div class="quiz-passo__rodape">
            {% if forloop.last %}
            <button class="botao botao--bloco" type="submit">Ver meus cursos</button>
            {% else %}
            <a class="botao botao--bloco" href="#questao-{{ forloop.counter|add:'1' }}" data-proxima>Próxima</a>
            {% endif %}
        </div>
    </fieldset>
    {% endfor %}
</form>

{# Tela 08 · só aparece com JS, enquanto o servidor calcula #}
<div class="analisando" data-analisando hidden>
    <div class="cartao analisando__cartao" role="status" aria-live="polite">
        <i class="fa-solid fa-rotate analisando__icone" aria-hidden="true"></i>
        <p class="analisando__titulo">Analisando seu perfil e cruzando com nossos cursos...</p>
        <p class="nota">Isso leva só um instante</p>
    </div>
</div>
{% endblock %}

{% block scripts %}<script src="{% static 'js/quiz.js' %}" defer></script>{% endblock %}
```

> [!danger] O `#questao-1` no `action` da boas-vindas é o que faz o "Começar" funcionar
> Num formulário GET, o navegador troca o `?...` da URL pelos campos, mas **mantém o `#`**. Sem o `#questao-1`, o "Começar" leva a `/?respondido_por=Ana&etapa=1`, nenhuma pergunta é o `:target`, e a tela fica vazia.

> [!note] A barra de progresso é calculada no servidor
> Cada pergunta tem a **própria** barra, com a largura já certa: `{% widthratio forloop.counter questoes|length 100 %}` dá 17%, 33%, 50%… Não precisa de JS para a barra andar.

> [!note] Por que o rádio não é `display: none`
> Com `display: none`, o rádio sai do teclado e do leitor de tela. O CSS o deixa transparente (`opacity: 0`) e a `<label>` inteira vira a área de clique: o cartão todo é clicável, e o Tab continua passando pelas opções.

---

## 2️⃣ FT-05 e FT-06 — `backend/static/css/quiz.css` (arquivo novo)

```css
/* Quiz: boas-vindas (tela 01), perguntas (02 a 07) e "Analisando" (08).
   Uma pergunta por vez SEM JavaScript: só a pergunta do #questao-N da URL aparece. */

.quiz-aviso-link {
  max-width: var(--largura);
  margin: 0 auto 20px;
}

/* ---------- Tela 01 · boas-vindas ---------- */

.quiz-intro {
  margin-top: clamp(0px, 6vh, 64px);
}

.quiz-intro .chips {
  margin: 24px 0 28px;
}

/* ---------- Telas 02 a 07 · perguntas ---------- */

.quiz-passo {
  display: none;
  margin: 0;
  padding: 0;
  border: 0;
  min-width: 0;
}

.quiz-passo:target {
  display: block;
}

/* Rede de segurança: quiz já começado mas URL sem #questao-N -> mostra a primeira */
body:not(:has(.quiz-intro)) .quiz-form:not(:has(.quiz-passo:target)) .quiz-passo:first-of-type {
  display: block;
}

/* Durante as perguntas, a página fica só com o quiz (como no protótipo) */
body:has(.quiz-passo:target) .topo,
body:has(.quiz-passo:target) .rodape,
body:has(.quiz-passo:target) .quiz-intro {
  display: none;
}

body:has(.quiz-passo:target) .conteudo {
  max-width: none;
  padding: 0;
}

.quiz-passo__progresso {
  height: 8px;
  border-radius: 0;
}

.quiz-passo__topo {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  min-height: 72px;
  padding: 0 clamp(16px, 6vw, 88px);
  border-bottom: 1px solid var(--linha);
  background: var(--superficie);
}

.quiz-passo__contador {
  color: var(--texto-2);
  font-weight: 600;
}

.quiz-passo__corpo {
  max-width: var(--largura);
  margin: 0 auto;
  padding: 40px 20px 140px; /* espaço para o rodapé fixo */
}

.quiz-passo legend {
  margin-bottom: 28px;
  padding: 0;
  font-size: var(--h2);
  font-weight: 700;
  line-height: 1.25;
}

.quiz-passo legend:focus {
  outline: none;
}

.quiz-passo__numero {
  color: var(--marca);
}

/* ---------- Opções ---------- */

.opcoes {
  display: grid;
  gap: 16px;
}

.opcao {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 74px;
  padding: 14px 20px;
  border: 2px solid var(--linha);
  border-radius: var(--raio);
  background: var(--superficie);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.opcao:hover {
  border-color: var(--marca-hover);
}

/* O rádio some da tela, mas continua no teclado e no leitor de tela */
.opcao input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.opcao__numero {
  display: grid;
  flex: none;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--gelo);
  color: var(--texto-2);
  font-weight: 700;
}

.opcao:has(input:checked) {
  border-color: var(--marca);
  background: var(--marca-clarinho);
}

.opcao:has(input:checked) .opcao__numero {
  background: var(--marca);
  color: var(--branco);
}

.opcao:has(input:focus-visible) {
  outline: 3px solid var(--foco);
  outline-offset: 3px;
}

.quiz-passo__aviso {
  margin-top: 16px;
  color: var(--erro);
  font-weight: 600;
}

/* ---------- Rodapé fixo com "Próxima" ---------- */

.quiz-passo__rodape {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  padding: 16px 20px;
  border-top: 1px solid var(--linha);
  background: var(--superficie);
}

.quiz-passo__rodape .botao {
  display: flex;
  max-width: var(--largura);
  margin: 0 auto;
}

/* Sem resposta marcada, "Próxima" fica apagado e não responde ao clique */
.quiz-passo:not(:has(input:checked)) [data-proxima] {
  opacity: 0.45;
  pointer-events: none;
}

/* ---------- Tela 08 · Analisando ---------- */

.analisando {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: grid;
  place-items: center;
  padding: 20px;
  background: var(--fundo);
}

.analisando[hidden] {
  display: none;
}

.analisando__cartao {
  max-width: 400px;
  text-align: center;
}

.analisando__icone {
  color: var(--marca);
  font-size: 2.4rem;
  animation: girar 1.2s linear infinite;
}

.analisando__titulo {
  margin: 20px 0 8px;
  color: var(--texto-3);
  font-size: 1.3rem;
  font-weight: 700;
}

@keyframes girar {
  to {
    transform: rotate(360deg);
  }
}
```

> [!tip] Três seletores fazem o trabalho do JavaScript
> - `.quiz-passo:target` mostra a pergunta da vez;
> - `body:has(.quiz-passo:target) .topo` esconde o topo durante as perguntas (as telas 02 a 07 não têm topo);
> - `.quiz-passo:not(:has(input:checked)) [data-proxima]` apaga o "Próxima" até a pessoa responder.
>
> O `:has()` funciona em todos os navegadores atuais (Chrome, Edge, Firefox, Safari).

> [!note] A "rede de segurança"
> Se a URL chegar com o quiz já começado mas **sem** `#` (por exemplo, a pessoa apagou o `#` e deu Enter), a primeira pergunta aparece em vez de uma tela vazia.

---

## 3️⃣ FT-07 — `backend/static/js/quiz.js` (substitua)

```javascript
// Melhorias do quiz com JavaScript. SEM JS o quiz funciona igual: cada pergunta é
// um #questao-N, os links "Próxima"/"Voltar" trocam o # da URL e o CSS (:target)
// mostra só a pergunta da vez. Este arquivo só acrescenta conforto:
//   1. marcou a resposta com o mouse ou o dedo -> avança sozinho;
//   2. Enter avança em vez de enviar o formulário pela metade;
//   3. o foco vai para a pergunta nova (leitor de tela anuncia);
//   4. no envio, mostra a tela "Analisando seu perfil".
(function () {
    const form = document.querySelector("[data-quiz]");
    if (!form) return;

    const passos = Array.from(form.querySelectorAll("[data-passo]"));
    const analisando = document.querySelector("[data-analisando]");

    function passoAtual() {
        return passos.find((passo) => "#" + passo.id === location.hash);
    }

    function irPara(indice) {
        if (indice >= 0 && indice < passos.length) location.hash = passos[indice].id;
    }

    function respondido(passo) {
        return Boolean(passo.querySelector("input[type=radio]:checked"));
    }

    function avisar(passo) {
        const aviso = passo.querySelector("[data-aviso]");
        if (aviso) aviso.hidden = false;
    }

    // No teclado, as setas trocam a opção marcada e disparam "change" a cada toque.
    // Avançar sozinho aí jogaria a pessoa para a próxima pergunta antes de escolher:
    // no teclado, quem avança é o Enter.
    let pelaTeclado = false;
    form.addEventListener("pointerdown", () => { pelaTeclado = false; });
    form.addEventListener("keydown", () => { pelaTeclado = true; });

    // 1. Marcou a resposta com o mouse/dedo: segue sozinho, com uma pausa para o clique ser visto.
    form.addEventListener("change", (evento) => {
        if (evento.target.type !== "radio") return;
        const passo = evento.target.closest("[data-passo]");
        const aviso = passo.querySelector("[data-aviso]");
        if (aviso) aviso.hidden = true;
        const indice = passos.indexOf(passo);
        if (!pelaTeclado && indice < passos.length - 1) setTimeout(() => irPara(indice + 1), 320);
    });

    // 2. Enter avança em vez de enviar o formulário pela metade.
    form.addEventListener("keydown", (evento) => {
        if (evento.key !== "Enter") return;
        const passo = passoAtual();
        if (!passo) return;
        const indice = passos.indexOf(passo);
        if (indice === passos.length - 1) return; // na última, Enter envia mesmo
        evento.preventDefault();
        if (respondido(passo)) irPara(indice + 1);
        else avisar(passo);
    });

    // 3. Pergunta nova na tela: o foco vai para o enunciado.
    window.addEventListener("hashchange", () => {
        const passo = passoAtual();
        if (passo) passo.querySelector("legend").focus({ preventScroll: true });
        window.scrollTo(0, 0);
    });

    // 4. Enviou: a tela "Analisando" cobre tudo enquanto o servidor calcula.
    //    Se faltar resposta, volta para a primeira pergunta em branco.
    form.addEventListener("submit", (evento) => {
        const vazio = passos.find((passo) => !respondido(passo));
        if (vazio) {
            evento.preventDefault();
            location.hash = vazio.id;
            avisar(vazio);
            return;
        }
        if (analisando) analisando.hidden = false;
    });
})();
```

> [!danger] No teclado, o quiz **não** avança sozinho, de propósito
> Num grupo de rádio, as setas **trocam a opção marcada** e disparam `change` a cada toque. Se o avanço automático valesse para o teclado, quem aperta ↓ para ouvir a próxima opção seria jogado para a pergunta seguinte antes de escolher. Por isso o `pelaTeclado`: com mouse ou dedo, avança sozinho; com teclado, quem avança é o Enter.

> [!note] Por que a tela "Analisando" não tem `setTimeout`
> No protótipo React, ela ficava 2 segundos na tela, **de mentira**. Aqui ela aparece no `submit` e some quando o servidor devolve o resultado. Se o cálculo leva 200 ms, ela aparece por 200 ms. Não há espera artificial.

---

## 4️⃣ Verificação

```bash
python manage.py test quiz.tests.test_paginas quiz.tests.test_rotas_web accounts.tests.test_c6_claim 2>&1 | tail -3
python manage.py test 2>&1 | tail -3
```

| # | O quê | Sinal de que passou |
|---|---|---|
| 1 | `/` em 1440 px e 390 px | Igual ao mockup 01; sem rolagem lateral |
| 2 | "Começar" | Pergunta 1, igual ao mockup 02: barra vermelha no topo, "‹ Voltar", "Pergunta 1 de 6" |
| 3 | "Próxima" sem responder | Apagado; não faz nada |
| 4 | Clicar numa opção | Borda vermelha, número em vermelho, e avança sozinho |
| 5 | Só teclado: Tab até as opções, ↓ e ↑ | Troca a opção **sem** avançar |
| 6 | Enter | Avança; o leitor de tela lê a pergunta nova |
| 7 | "Voltar" na pergunta 3 | Volta para a 2 com a resposta ainda marcada |
| 8 | Última pergunta → "Ver meus cursos" | Aparece a tela "Analisando…" e depois o resultado |
| 9 | **JS desligado** (DevTools → ⚙️ → *Disable JavaScript*) | Dá para responder as 6 pelo "Próxima" e ver o resultado |
| 10 | Entrar por um link de questionário (`/questionario/<token>/`) | A faixa "Você está respondendo pelo link da escola" |

## 5️⃣ Commit e PR

```bash
git add backend/templates/quiz/quiz.html backend/static/css/quiz.css backend/static/js/quiz.js
git commit -m "feat(front): quiz nas telas 01 a 08 do prototipo (FT-05 a FT-07)"
git push -u origin front/quiz
```

No PR: prints das telas 01, 02 e 08 ao lado dos mockups, e o resultado dos itens 5, 6 e 9 da tabela.

## ▶️ Próxima ação

Criar a branch `front/quiz` e começar pela estrutura do `quiz.html`.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-front-templates|🎨 Spec do front]] — V6 (a tela "Analisando")
- [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Front em templates (agosto)]] — de onde veio o `:target`
