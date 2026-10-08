---
title: "Apresentação · Front (templates, scripts, CSS e acessibilidade)"
aliases: ["Front na apresentação", "O que apresentar do front"]
tags: [tcc, apresentacao, front, templates, css, acessibilidade]
status: pronto
projeto: TCC
atualizado: 2026-10-08
---

> [!info] Apresentação: [[README|🎤 Roteiro]] · [[engine|🧮 Engine]] · [[backend|⚙️ Backend]] · **🎨 Front** · [[ia|🤖 Camada de IA]] · [[demo-e-perguntas|🎬 Demo e banca]]

# 🎨 Front: o que apresentar

> [!abstract] O que esta nota é
> Não existe SPA nem build: nada de Node, nada de bundler. O front é **HTML renderizado pelo Django + CSS por tokens + 5 scripts pequenos**. Ordem sugerida: **templates → o truque do `quiz.html` → resultado → painel → scripts → CSS → acessibilidade**.

> [!quote] A frase que resume
> **Melhoria progressiva:** tudo funciona só com HTML e CSS. O JavaScript apenas deixa a experiência mais confortável. Se o JS falhar, o aluno ainda responde o quiz e vê o resultado, e a coordenação ainda navega pelo painel.

---

## 🗂️ 1. Estrutura dos templates

```
backend/templates/
├─ base.html                 esqueleto de todas as páginas do aluno (herança)
├─ componentes/              pedaços reutilizáveis ({% include %})
│  ├─ _anel.html             anel de afinidade (SVG)
│  ├─ _barra.html            barra de afinidade / progresso
│  ├─ _campo.html            campo de formulário com label, ajuda e erro
│  ├─ _secretaria.html       cartão de contato da escola
│  └─ _topo_voltar.html      topo simples com "Voltar"
└─ quiz/
   ├─ quiz.html              telas 01 a 08 (intro, 10 perguntas, "analisando")
   ├─ resultado.html         tela 09 (1º lugar em destaque + 4 alternativas)
   ├─ aluno_perfil.html      "Meu perfil"
   └─ link_invalido.html     link fechado ou inexistente

backend/<app>/templates/<app>/
├─ accounts/   entrar, criar_conta, lista, tentativas
├─ catalogo/   curso_detalhe (tela 10)
├─ avaliacao/  responder, obrigado, link_invalido
└─ painel/     base_painel + 7 telas + pedaços (_abas, _mais, _periodo, _celula, _ranking, _sem_massa)
```

### `base.html`

| O que tem | Por quê |
|---|---|
| Blocos `title`, `estilos`, `topo`, `mensagens`, `content`, `rodape`, `scripts` | **Herança:** cada tela carrega só o CSS dela no bloco `estilos` |
| Skip link "Pular para o conteúdo" + `<main id="conteudo">` | Teclado e leitor de tela pulam o menu |
| Menu do usuário com `<details>/<summary>` | **Abre e fecha sem JavaScript**. O link "Painel" só aparece para `user.is_staff` |
| Script **inline no `<head>`**, antes do CSS | Lê o `localStorage` e aplica `fonte-grande`/`alto-contraste` **antes da página pintar**: o tema não "pisca" |
| Dados da escola via **context processor** `core.contexto.escola` | `{{ escola.nome }}` em qualquer template, vindo do `.env` |

---

## ⭐ 2. `quiz.html`: o truque central

**Uma página, 10 perguntas, sem JavaScript.**

- Cada pergunta é um `<fieldset id="questao-N">`. "Próxima" e "Voltar" são **links** `href="#questao-N"`.
- O CSS usa **`:target`** (`quiz.css`): mostra só o fieldset cujo id está no `#` da URL. **Trocar de pergunta = trocar o `#`.**
- Enviou faltando resposta? A view guarda o que já foi respondido **na sessão** e redireciona para `#questao-<primeira em branco>`.
- Barra de progresso: `{% widthratio %}` no template, passada ao CSS por variáveis (`--valor`, `--de`, `--seguinte`) para animar de onde a pergunta anterior parou.
- Semântica: `<fieldset>` + `<legend>` + `<input type="radio">` dentro de `<label>`. O leitor de tela anuncia a pergunta e as opções.

> [!tip] Na demo, mostre a URL
> Responda duas perguntas e aponte para a barra de endereço: `#questao-2`, `#questao-3`… É a forma mais rápida de mostrar que **o quiz é navegação, não JavaScript**.

## 🏆 3. `resultado.html`: a engine na tela

| Bloco | De onde vem |
|---|---|
| Anel de afinidade do 1º lugar | `round(score × 100)`, a afinidade do [[engine|cosseno]] |
| "Por que este curso?" | `explicacao.top_areas`: as 3 áreas que mais pesaram, com percentual e barra |
| Aviso de empate | Aparece quando `confidence_band == "baixa"` |
| "Também combinam com você" | As outras 4, na ordem **`rank_final`** |
| Salvar curso / Ver detalhes | Lista de interesse e tela 10 (afinidade daquele aluno com o curso) |

---

## 📊 4. O painel da coordenação

| Peça | Arquivo | O que faz |
|---|---|---|
| Esqueleto | `painel/base_painel.html` | **Menu lateral** no computador; no celular, uma **barra de abas** embaixo (`_abas.html`) e a folha **"Mais"** (`_mais.html`) |
| Filtro de período | `_periodo.html` | Diário · Mensal · Anual · Mês escolhido. Os links do menu levam o filtro junto |
| Número ou "—" | `_celula.html` | Um lugar só decide como mostrar um número suprimido |
| 7 telas | `inicio`, `quiz`, `cursos`, `links`, `interesse`, `avaliacoes`, `avaliacoes_resultados` | Ver a tabela de telas em [[backend|⚙️ Backend]] |
| Atalho | botão **"Voltar ao teste"** | Abre o quiz pelo link ativo, para a coordenação testar como aluno |

> [!note] 🎓 Os gráficos recebem os dados por `json_script`
> `{{ serie|json_script:"dados-serie" }}` escreve um `<script type="application/json">` seguro (sem risco de injeção) que o `painel-graficos.js` lê e entrega ao **Chart.js**. Se o Chart.js não carregar (sem internet na sala), o script avisa no console e **os números continuam nas legendas**.

---

## 🧠 5. Scripts (`backend/static/js/`)

Todos em **IIFE** `(function () { ... })()`, sem poluir o escopo global, e todos **saem cedo** se o elemento não existe na página (`if (!form) return;`).

| Script | Linhas | O que faz |
|---|:-:|---|
| `quiz.js` | ~110 | **Enter avança** (e não envia pela metade); aviso que "treme" se a pergunta está em branco; **foco no `<legend>`** a cada pergunta (o leitor de tela anuncia); direção da animação (`data-direcao`); no envio, volta para a 1ª em branco ou mostra a tela **"Analisando"** |
| `movimento.js` | ~30 | Números com `data-contar` contam de 0 até o valor (`requestAnimationFrame`, *easing* `1 − (1 − t)⁴`), no ritmo do token `--dur-preencher`. Respeita **`prefers-reduced-motion`** |
| `acessibilidade.js` | ~25 | Botões `data-alternar` ligam `fonte-grande`/`alto-contraste` no `<html>`, atualizam `aria-pressed` e salvam no `localStorage` (dentro de `try/catch`: navegação privada não quebra) |
| `painel.js` | ~110 | Folha "Mais" no celular, animação da troca de aba, **confirmação antes de cada POST** (gerar e fechar link), botão **Copiar** (`navigator.clipboard`) e campo de mês |
| `painel-graficos.js` | ~50 | Gráficos da tela Início com **Chart.js**, nas cores dos tokens (`--marca`) |

Padrões para citar: **delegação de eventos** (um listener no form, não um por botão), `closest()`, `dataset`, `hashchange`.

> [!warning] Dois detalhes do `quiz.js` para ter resposta pronta
> 1. **O avanço automático foi desligado:** marcar uma opção não troca mais de pergunta, e quem avança é o botão "Próxima" ou o Enter. As variáveis `PAUSA_AO_MARCAR` e `pelaTeclado` ficaram sem uso. É limpeza pendente, não bug.
> 2. **A tela "Analisando" segura o envio por 1,5 s de propósito** (`setTimeout`). A engine responde em milissegundos; a pausa é uma escolha de experiência, para o aluno perceber que houve análise. Se perguntarem, diga isso. Com a camada de IA, a espera passa a ser real.

---

## 🎛️ 6. CSS por tokens (`backend/static/css/`)

| Arquivo | Conteúdo |
|---|---|
| `tokens.css` | Variáveis: cores, fontes, espaços, raios, sombras, **tempos e curvas de movimento**. Redefine os tokens em `:root.fonte-grande` e `:root.alto-contraste` |
| `base.css` | Reset, tipografia, layout, topo/rodapé, keyframes num só lugar, View Transitions, `prefers-reduced-motion` |
| `componentes.css` | Botões, cartões, chips, campos, anel, barra |
| `quiz.css` · `resultado.css` · `curso.css` · `conta.css` · `avaliacao.css` | Uma folha por tela, carregada só onde é usada |
| `painel.css` · `painel-abas.css` | Painel e a navegação por abas do celular |

- **BEM em português:** `.quiz-passo__topo`, `.botao--bloco`, `.destaque__info`.
- **Tokens:** trocar a cor da marca = mudar **uma** variável. Alto contraste e fonte grande são **outros valores dos mesmos tokens**.
- **Animações só com CSS:** anel e barras enchem por `transition` a partir de `--valor`; as entradas são escalonadas com `.entrada` + `--i`.
- **View Transitions API:** troca de página suave com o topo parado. Navegador sem suporte apenas troca a página.

---

## ♿ 7. Acessibilidade (um slide)

- HTML semântico: `fieldset/legend`, `label`, `nav` com `aria-label`, `main`, `header`, `footer`.
- Teclado do começo ao fim: skip link, Enter no quiz, foco gerenciado a cada pergunta.
- ARIA só onde falta semântica: `aria-current` no menu e no período, `aria-pressed`, `aria-expanded` na folha "Mais", `role="alert"`, `role="status"`.
- **Fonte grande e alto contraste** com os botões no painel (menu lateral e folha "Mais"), persistentes no navegador.
- Respeito a "reduzir movimento" em CSS **e** em JS. Ícones sempre com `aria-hidden="true"`.

> [!warning] Os botões de acessibilidade estão só no **painel**
> Na área do aluno (quiz e resultado) o script e os tokens funcionam, mas **não há botão na tela**: quem já ligou no painel vê o tema aplicado, porque o `base.html` lê o `localStorage`. Ou acrescentem os dois botões no topo do `base.html`, ou mostrem o recurso **pelo painel** na demo.

> [!tip] 20 segundos que marcam pontos
> Responda duas perguntas **só com o teclado** (Tab, setas, Enter) e depois ligue o **alto contraste** no painel.
