# Front: o que apresentar

Não existe SPA nem build (sem Node, sem bundler). O front é **HTML renderizado pelo Django + CSS + 3 scripts pequenos**. A frase que resume:

> **Melhoria progressiva:** tudo funciona só com HTML e CSS. O JavaScript apenas deixa a experiência mais confortável. Se o JS falhar, o aluno ainda consegue responder o quiz e ver o resultado.

Ordem sugerida: **estrutura dos templates → quiz.html (o truque do `:target`) → scripts → componentes → CSS por tokens → acessibilidade**.

---

## 1. Estrutura dos templates (HTMLs)

```
backend/templates/
├─ base.html                 esqueleto de todas as páginas (herança)
├─ componentes/              pedaços reutilizáveis ({% include %})
│  ├─ _anel.html             anel de afinidade (SVG)
│  ├─ _barra.html            barra de afinidade / progresso
│  ├─ _campo.html            campo de formulário com label, ajuda e erro
│  ├─ _secretaria.html       cartão de contato da escola
│  └─ _topo_voltar.html      topo simples com "Voltar"
└─ quiz/
   ├─ quiz.html              telas 01 a 08 (intro, perguntas, "analisando")
   ├─ resultado.html         tela 09 (resultado)
   └─ link_invalido.html     link fechado ou inexistente

backend/<app>/templates/<app>/
├─ accounts/  entrar, criar_conta, lista, tentativas, perfil
├─ catalogo/  curso_detalhe (tela 10)
└─ painel/    dashboard, _celula (número ou "—"), _ranking
```

### `base.html`: o que mostrar

- **Herança de templates:** blocos `title`, `estilos`, `topo`, `content`, `rodape` e `scripts`. Cada tela carrega **só o CSS dela** no bloco `estilos` (`quiz.css`, `resultado.css`, `painel.css`...).
- **Skip link** "Pular para o conteúdo" e `<main id="conteudo">` (acessibilidade para teclado e leitor de tela).
- Menu do usuário com `<details>/<summary>`: **abre e fecha sem JavaScript**. O link "Painel" só aparece para `user.is_staff`.
- Mensagens do Django (`messages`) com `role="status"`.
- Script **inline no `<head>`**, antes do CSS, que lê o `localStorage` e aplica `fonte-grande` / `alto-contraste` **antes da página pintar**. Assim não há "piscada" de tema.
- Os scripts carregam com `defer` no final.
- Dados da escola vêm do **context processor** `core.contexto.escola` (`{{ escola.nome }}` em qualquer template).

---

## 2. `quiz.html`: o truque central do front ★

**Uma página, várias perguntas, sem JavaScript.**

- Cada pergunta é um `<fieldset id="questao-N">`. Os botões "Próxima" e "Voltar" são **links** `href="#questao-N"`.
- O CSS usa **`:target`** (`quiz.css`): mostra só o fieldset cujo id está no `#` da URL. Trocar de pergunta = trocar o `#`.
- Se o aluno enviar faltando resposta, a view guarda o que já foi respondido na sessão e redireciona para `#questao-<primeira em branco>`.
- A barra de progresso é calculada no template com `{% widthratio %}` e passada ao CSS por variáveis (`--valor`, `--de`, `--seguinte`) para animar de onde a pergunta anterior parou.
- Semântica: `<fieldset>` + `<legend>` + `<input type="radio">` dentro de `<label>`. O leitor de tela anuncia a pergunta e as opções corretamente.
- A tela "Analisando seu perfil" (tela 08) só aparece com JS (`hidden` por padrão).

---

## 3. Scripts (`backend/static/js/`)

Todos em **IIFE** `(function () { ... })()`: não poluem o escopo global. Todos saem cedo se o elemento não existe na página (`if (!form) return;`).

### `quiz.js`: conforto no quiz (≈ 110 linhas)

Cinco melhorias, todas sobre o HTML que já funciona:

1. **Avanço automático** ao marcar uma opção com mouse ou dedo, depois de uma pausa (`PAUSA_AO_MARCAR`) para o clique ser visto. Com **teclado** não avança sozinho: as setas trocam a opção a cada toque e o aluno seria jogado para a próxima pergunta antes de escolher (`pointerdown` × `keydown` decidem o modo).
2. **Enter avança** em vez de enviar o formulário pela metade. Se a pergunta está em branco, mostra o aviso (com animação de "tremer" reiniciada via `void aviso.offsetWidth`).
3. **Foco** vai para o `<legend>` da pergunta nova no `hashchange`: o leitor de tela anuncia a pergunta. Isso cobre também o voltar/avançar do navegador.
4. **No envio**, se faltar resposta, vai para a primeira em branco; senão mostra a tela "Analisando".
5. **Direção da animação:** grava `data-direcao="avancar|voltar"` no form **antes** do `#` mudar, para a pergunta entrar pelo lado certo.

Padrões para citar: **delegação de eventos** (um listener no form, não um por botão), `closest()`, `dataset`, `setTimeout`/`clearTimeout` para não agendar dois avanços.

### `movimento.js`: números que contam

- Qualquer elemento com `data-contar` (ex.: `87%`) conta de 0 até o valor com `requestAnimationFrame` e *easing* `1 − (1 − t)⁴`.
- Lê a duração do **token CSS** `--dur-preencher`, então número, anel e barra andam no mesmo ritmo.
- Respeita **`prefers-reduced-motion`**: com "reduzir movimento" ligado, sai sem animar. Sem JS, o número já está no HTML.

### `acessibilidade.js`: fonte grande e alto contraste

- Botões com `data-alternar="fonte-grande"` ou `data-alternar="alto-contraste"` ligam uma classe no `<html>`.
- Atualiza `aria-pressed` (o leitor de tela sabe se está ligado) e salva no `localStorage` dentro de `try/catch` (navegação privada não quebra a página).
- ⚠️ **Hoje nenhum template tem um botão `data-alternar`.** O script e os tokens existem, mas o usuário não tem como ligar. Ou adicione os dois botões no topo do `base.html` antes da apresentação, ou apresente como "infraestrutura pronta" e não prometa na demo.

### Script do painel (inline em `painel/dashboard.html`)

- Gráficos com **Chart.js** (CDN) alimentados pelo contexto do Django, modais de confirmação para gerar e fechar link e botão "Copiar" com `navigator.clipboard`.
- Veja o aviso sobre os estilos inline deste arquivo em [demo-e-perguntas.md](demo-e-perguntas.md#antes-de-apresentar-corrigir-ou-ter-resposta).

---

## 4. Componentes

| Componente | Como funciona | Destaque |
| --- | --- | --- |
| `_anel.html` | SVG com 2 círculos; o CSS desenha o arco a partir de `--valor` | `role="img"` + `aria-label="87% de afinidade"`; o número visual fica `aria-hidden` para não ser lido duas vezes |
| `_barra.html` | `<span>` com `width` guiada por `--valor`; parâmetro `escura` | Reusada no resultado, no detalhe do curso e no progresso do quiz |
| `_campo.html` | label + input + ajuda + erros | Erro com `role="alert"`; marca "(opcional)" sozinho a partir do form do Django |
| `_secretaria.html` | Contato da escola vindo do `settings.ESCOLA` | Telefone vira link `tel:` já limpo com o filtro `cut` |

Uso: `{% include "componentes/_anel.html" with valor=destaque.match %}`. **Um componente = um lugar para corrigir.**

---

## 5. CSS por tokens (`backend/static/css/`)

| Arquivo | Conteúdo |
| --- | --- |
| `tokens.css` | Variáveis: cores, fontes, espaçamentos, raios, sombras e **tempos/curvas de movimento**. Também redefine tokens em `:root.fonte-grande` e `:root.alto-contraste`. |
| `base.css` | Reset, tipografia, layout, topo/rodapé, **keyframes num só lugar**, View Transitions, `prefers-reduced-motion` |
| `componentes.css` | Botões, cartões, chips, campos, anel, barra |
| `quiz.css`, `resultado.css`, `curso.css`, `conta.css`, `painel.css` | Um por tela, carregado só onde é usado |

Pontos para citar:

- **Nomenclatura BEM** em português: `.quiz-passo__topo`, `.botao--bloco`, `.destaque__info`.
- **Tokens:** para trocar a cor da marca, altera-se **uma** variável. O alto contraste e a fonte grande são só **outros valores dos mesmos tokens**.
- **Animações só com CSS:** o anel e as barras enchem por `transition`/`@keyframes` a partir de `--valor`. Entradas escalonadas com `.entrada` + `--i`.
- **View Transitions API** (`@view-transition`): troca de página suave, com o topo parado (`view-transition-name: topo`). Navegador sem suporte apenas troca a página normalmente.
- **`prefers-reduced-motion: reduce`** desliga tudo isso.

---

## 6. Acessibilidade (resumo para um slide)

- HTML semântico: `fieldset/legend`, `label`, `nav` com `aria-label`, `main`, `header`, `footer`.
- Navegação completa por teclado (Enter no quiz, foco gerenciado, skip link).
- ARIA só onde falta semântica: `aria-current` no período do painel, `aria-pressed`, `role="alert"`, `role="status"`, `aria-live="polite"`.
- Fonte grande e alto contraste persistentes (tokens + script prontos; falta o botão na tela, ver acima), e respeito a "reduzir movimento".
- Ícones do Font Awesome sempre com `aria-hidden="true"`.

> Na demo, **mostre o quiz sendo respondido só com o teclado** (Tab, setas, Enter). Leva 20 segundos e marca pontos. Se os botões de acessibilidade forem adicionados, ligue também o alto contraste.
