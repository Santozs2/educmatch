---
title: "Spec — front em HTML, CSS e JS (templates do Django) a partir do protótipo de alta fidelidade"
aliases: ["Spec do front", "Front em templates", "Spec do front HTML CSS JS", "Front EducMatch v2"]
tags: [tcc, spec, front, django, templates, css, javascript, acessibilidade, planejamento]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Plano: [[Projetos/EducMatch(Secretária)/plano-execucao-front-templates|🗂️ Plano de execução do front]] · Passo a passo: [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-01-fundacao|🧱 FT-01 a FT-04 e FT-15/16]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-05-ft-07-quiz|❓ FT-05 a FT-07]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-08-ft-10-resultado-curso|🎯 FT-08 a FT-10]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-11-ft-14-conta-painel|👤 FT-11 a FT-14]] · Substitui: [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front React]]

# 🎨 Spec — front em HTML, CSS e JS

> [!abstract] O que este documento é
> A especificação do front do EducMatch **depois do abandono do React** (2026-09-22): as mesmas telas do protótipo de alta fidelidade, agora como **templates do Django + CSS puro + JavaScript sem framework**.
> Escrita contra a `main` em `ac471c0` (depois do PR #7), a partir de três fontes: o **guia de estilo** (`Desktop/guia-de-estilo-educmatch.pdf`), as **12 telas de alta fidelidade** (`Downloads/altaFidelidade/`) e os tokens do protótipo React (`frontend/src/index.css`, no histórico do Git).
> Aqui ficam as decisões, o mapa de telas e o sistema visual. O "como", arquivo por arquivo, está nos quatro passo a passo.

> [!success] O que já foi verificado (2026-09-22)
> Todo o código dos passo a passo foi aplicado numa **cópia** da `main`, com banco MySQL próprio e o catálogo semeado (`12 20 73`):
> - `manage.py check` e `makemigrations --check` limpos;
> - **64 testes, 63 verdes**. O vermelho é o do fuso, que fica verde com as tabelas de fuso carregadas (README);
> - as telas foram abertas no navegador e comparadas com os mockups 01, 02, 08, 09, 10, 11 e 12, em **1440 px** e em **390 px** (celular), sem rolagem lateral em nenhuma;
> - letra grande e alto contraste ligam, desligam e ficam guardados no navegador; o fluxo "salvar curso sem estar logado → entrar → salvar agora" funciona.
>
> **Não** verificado: leitor de tela de verdade (NVDA) e o quiz com o JavaScript desligado no navegador. Os dois estão no roteiro da FT-16.

---

## 1️⃣ Decisões

| Decisão | Escolha | Por quê |
|---|---|---|
| Renderização | **Templates do Django**, sem SPA e sem API | Um processo, um endereço (`localhost:8000`), sem CORS nem CSRF entre origens. E todo o grupo consegue mexer no front |
| CSS | **CSS puro, sem framework e sem build** | Tailwind exigiria Node e um passo de build; o projeto não tem nenhum dos dois. As variáveis CSS fazem o papel do `@theme` do protótipo |
| Cores e fonte | As do **guia de estilo**, completadas pelos tons do protótipo | O guia define 5 cores e a Space Grotesk; o protótipo acrescenta os tons de apoio (cinzas, vermelho-claro dos chips). O CSS atual usava `#e33b32` e DM Sans, que não estão no guia |
| JavaScript | **Aprimoramento progressivo** | O quiz funciona inteiro sem JS; o JS só acrescenta conforto (avanço automático, tela "Analisando", foco). Se o JS falhar na apresentação, nada quebra |
| Uma pergunta por vez | **`:target` do CSS** (âncora `#questao-N`) | Já era assim, e é o que funciona sem JS. O `quiz.js` antigo trocava classes que **nenhum CSS usava**: o avanço automático e a barra nunca funcionaram |
| Arquivos de CSS | **Um por tela** + três comuns | Com um `style.css` só, quatro pessoas editando o mesmo arquivo dá conflito toda hora. Cada tela carrega o seu pelo `{% block estilos %}` |
| Ícones | **Font Awesome 6** (já carregado) | Tem os ícones do guia (casa, voltar, estrela, baixar, recarregar, sair, pessoa) no estilo "negrito" (`fa-solid`) |
| Componentes | **Classes CSS + `{% include %}` de template** | É o equivalente de "componente" sem React: `componentes/_anel.html`, `_barra.html`, `_campo.html`… |

---

## 2️⃣ Mapa: tela → rota → template → dono

| # | Tela (alta fidelidade) | Rota | Template | CSS | Dono |
|---|---|---|---|---|---|
| 01 | Boas-vindas | `/` | `templates/quiz/quiz.html` | `quiz.css` | **A** |
| 02–07 | Perguntas 1 a 6 | `/?etapa=1#questao-N` | `templates/quiz/quiz.html` | `quiz.css` | **A** |
| 08 | Analisando seu perfil | `/` (sobreposição, só com JS) | `templates/quiz/quiz.html` | `quiz.css` | **A** |
| 09 | Resultado | `/resultado/<id>/` | `templates/quiz/resultado.html` | `resultado.css` | **B** |
| 10 | Detalhe do curso | `/cursos/<id>/?tentativa=<id>` | `catalogo/templates/catalogo/curso_detalhe.html` | `curso.css` | **B** |
| 11 | Entrar | `/entrar/` | `accounts/templates/accounts/entrar.html` | `conta.css` | **C** |
| — | Criar conta | `/cadastro_usuario/` | `accounts/templates/accounts/criar_conta.html` | `conta.css` | **C** |
| 12 | Minha lista de interesse | `/lista_interesse/` | `accounts/templates/accounts/lista.html` | `conta.css` | **C** |
| — | Meus testes | `/meus-testes/` | `accounts/templates/accounts/tentativas.html` | `conta.css` | **C** |
| — | Meu perfil | `/meu-perfil/` | `templates/quiz/aluno_perfil.html` | `conta.css` | **C** |
| — | Link encerrado | `/questionario/<token>/` | `templates/quiz/link_invalido.html` | — | **C** |
| — | Painel da coordenação | `/painel/` | `painel/templates/painel/dashboard.html` | `painel.css` | **C** |
| — | Topo, rodapé, componentes | todas | `templates/base.html`, `templates/componentes/` | `tokens.css`, `base.css`, `componentes.css` | **D** |

As telas sem número não têm mockup: seguem os mesmos componentes das telas 11 e 12.

---

## 3️⃣ O sistema visual

### As cores

| Token | Valor | De onde | Uso |
|---|---|---|---|
| `--marca` | `#d9251c` | guia | botões, barra de progresso, destaques |
| `--marca-hover` | `#d84942` | guia | hover dos botões (texto `--gelo`) |
| `--tinta` | `#2d2d2d` | guia | texto principal |
| `--gelo` | `#ede8e4` | guia | texto no hover, fundo do número da opção |
| `--branco` | `#fffefe` | guia | texto sobre o vermelho e o preto |
| `--preto` | `#09090b` | protótipo | topo e faixas escuras |
| `--titulo` | `#6b1210` | protótipo | H1 em vermelho profundo ("Descubra o curso certo…") |
| `--marca-claro` · `--marca-clarinho` | `#fdecea` · `#fef5f4` | protótipo | chip de área · caixas de destaque |
| `--texto-2` · `--texto-3` | `#52525b` · `#71717a` | protótipo | texto secundário · legendas |
| `--linha` · `--fundo` · `--superficie` | `#e4e4e7` · `#f9fafb` · `#ffffff` | protótipo | bordas · fundo da página · cartões |

> [!important] Regra: **nenhum hexadecimal fora do `tokens.css`**
> Toda cor nova vira token com nome. É o que permite o modo alto contraste (que só redefine os tokens) e o que impede o projeto de ter 14 vermelhos diferentes daqui a um mês. O `grep` da FT-16 confere.

### A tipografia

Space Grotesk (400, 500, 600 e 700) em tudo, corpo de **17 px** (20 px com "letra grande"). `H1` e `H2` fluidos com `clamp()`, para diminuírem sozinhos no celular.

### Os componentes

| Classe | O que é | Onde aparece |
|---|---|---|
| `.botao` · `--contorno` · `--texto` · `--bloco` | Botão vermelho do guia · contorno · só texto · largura toda | todas |
| `.voltar` | Link "‹ Voltar" | perguntas, detalhe, entrar, listas |
| `.chip` · `--escuro` · `--area` · `--marca` | Pílula | boas-vindas, resultado, detalhe, lista |
| `.cartao` · `--centro` · `--estreito` | Cartão branco com sombra | boas-vindas, entrar, criar conta |
| `.campo` (+ `componentes/_campo.html`) | Label + input + ajuda + erro | entrar, criar conta, boas-vindas |
| `.barra` (+ `componentes/_barra.html`) | Barra de porcentagem | perguntas, "por que este curso" |
| `.anel` (+ `componentes/_anel.html`) | Anel de afinidade em SVG | resultado |
| `.aviso` · `.vazio` · `.mensagem` | Aviso na página · estado vazio · `messages` do Django | várias |
| `.visualmente-oculto` | Some da tela, fica para o leitor de tela | várias |

---

## 4️⃣ Divergências: protótipo × o que o sistema tem

> [!warning] V1 — "E-mail ou CPF" no login (tela 11)
> O sistema entra por **e-mail** (`USERNAME_FIELD = "email"`) e não guarda CPF. O rótulo fica **"E-mail"**. Aceitar CPF seria um campo novo, com validação e LGPD, fora do escopo.

> [!warning] V2 — "O que você vai aprender" (tela 10)
> O `Curso` não tem esse campo, e os quatro itens do mockup são genéricos, iguais para todo curso. A seção **fica de fora** até o catálogo (frente F3) ter o conteúdo. Mostrar texto igual em todo curso seria informação inventada.

> [!warning] V3 — Contato da secretaria (tela 10)
> O mockup traz um endereço e um telefone de exemplo. O cartão lê de `settings.ESCOLA`, que vem do `.env` (`ESCOLA_NOME`, `ESCOLA_ENDERECO`, `ESCOLA_TELEFONE`). **Sem os valores no `.env`, o cartão mostra só o nome da escola**: nada de "Rua da Escola Técnica, 1000".

> [!note] V4 — "Salvar resultado em PDF" (tela 09)
> É o **imprimir** do navegador (`window.print()`), que oferece "Salvar como PDF". O `resultado.css` tem um `@media print` que tira o topo e os botões da folha. Sem JS, o botão fica escondido e o `Ctrl+P` faz o mesmo.

> [!note] V5 — "Manifestar interesse" (telas 09 e 10)
> No protótipo o botão fica no detalhe do curso, não no resultado. Ficou assim: o resultado leva ao detalhe ("Ver detalhes do curso"), e o detalhe salva na lista. O fluxo de "interesse pendente" (salvar sem estar logado → entrar → "Salvar agora") continua igual.

> [!note] V6 — "Analisando seu perfil" (tela 08)
> No React era um `setTimeout` de 2 segundos, **falso**. Aqui a tela aparece no envio do formulário e some quando o servidor responde. Não há espera artificial: se o cálculo leva 200 ms, a tela aparece por 200 ms.

---

## 5️⃣ Estrutura dos arquivos

```
backend/
├─ templates/
│  ├─ base.html                  D · topo, mensagens, rodapé, blocos
│  ├─ componentes/               D · _anel, _barra, _topo_voltar
│  │                             B · _secretaria      C · _campo
│  └─ quiz/                      A · quiz.html   B · resultado.html   C · aluno_perfil.html, link_invalido.html
├─ catalogo/templates/catalogo/  B · curso_detalhe.html
├─ accounts/templates/accounts/  C · entrar, criar_conta, lista, tentativas
├─ painel/templates/painel/      C · dashboard.html (ajustes)
└─ static/
   ├─ css/  tokens.css  base.css  componentes.css   D
   │        quiz.css                                 A
   │        resultado.css  curso.css                 B
   │        conta.css  painel.css                    C
   └─ js/   acessibilidade.js                        D
            quiz.js                                  A
```

Cada template de tela carrega o próprio CSS:

```django
{% block estilos %}<link rel="stylesheet" href="{% static 'css/quiz.css' %}">{% endblock %}
```

---

## 6️⃣ Acessibilidade — o que não pode se perder

- **Funciona sem JavaScript.** O quiz é um formulário; cada pergunta é um `#questao-N`; o CSS mostra a da vez. Ver a FT-06.
- **Teclado:** foco sempre visível (`:focus-visible` com contorno vermelho de 3 px), alvos de pelo menos **48 px**, Enter avança no quiz.
- **Leitor de tela:** cada pergunta é `<fieldset>` + `<legend>`; o foco vai para a pergunta nova; o anel tem `aria-label="87% de afinidade"`; a linha inteira de "Também combinam" é clicável, mas **só o nome do curso é link** (ele lê uma vez, não cinco).
- **Letra grande e alto contraste**, pelos dois botões do topo (telas 01 e 09), guardados no navegador.
- **Menos movimento:** com `prefers-reduced-motion`, nenhuma animação.
- **Celular:** nenhuma tela rola para o lado em 390 px. Tabela larga do painel rola **dentro** do cartão.

---

## 7️⃣ Fora de escopo

- CPF no login (V1) e "o que você vai aprender" (V2).
- Modo escuro automático: o alto contraste cobre a necessidade de acessibilidade; tema escuro é outro trabalho.
- Gráficos com biblioteca (Chart.js): o painel usa barras em CSS puro, que funcionam offline e sem JS.
- Testes de navegador automatizados (Playwright): o `test_paginas.py` da FT-04 abre toda página pelo test client do Django, que pega erro de template; clique e visual ficam no roteiro manual.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/plano-execucao-front-templates|🗂️ Plano de execução do front]]
- [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Front em templates (a versão de agosto)]]
- [[Projetos/EducMatch(Secretária)/spec-front-react-vite|⚛️ Spec do front React]] — abandonada, mantida como histórico
