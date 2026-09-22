---
title: "Plano de execução — front em HTML, CSS e JS (FT-01 a FT-16)"
aliases: ["Plano do front", "Backlog do front", "Fases FT", "Execução do front em templates"]
tags: [tcc, plano, front, django, templates, css, javascript, backlog, planejamento]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Spec: [[Projetos/EducMatch(Secretária)/spec-front-templates|🎨 Spec do front]] · Passo a passo: [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-01-fundacao|🧱 D]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-05-ft-07-quiz|❓ A]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-08-ft-10-resultado-curso|🎯 B]] · [[Projetos/EducMatch(Secretária)/passo-a-passo-ft-11-ft-14-conta-painel|👤 C]] · Substitui: [[Projetos/EducMatch(Secretária)/plano-execucao-front-react|🗂️ Plano do front React]]

# 🗂️ Plano de execução — front em HTML, CSS e JS

> [!abstract] O que esta nota é
> O **o quê, quem e em que ordem** das 16 tarefas do front. O "por quê" está na [[Projetos/EducMatch(Secretária)/spec-front-templates|spec]]; o "como", com o código, nos quatro passo a passo (um por pessoa).

## 📊 Visão geral

| Pessoa | Frente | Tarefas | PR | Branch |
|---|---|---|---|---|
| **D** | 🧱 Fundação e acabamento | FT-01 a FT-04 · FT-15 e FT-16 | PR-F1 · PR-F5 | `front/fundacao` · `front/acabamento` |
| **A** | ❓ Quiz | FT-05 a FT-07 | PR-F2 | `front/quiz` |
| **B** | 🎯 Resultado e curso | FT-08 a FT-10 | PR-F3 | `front/resultado-curso` |
| **C** | 👤 Conta e painel | FT-11 a FT-14 | PR-F4 | `front/conta-painel` |

## 📋 As tarefas

| ID | Tarefa | Dono | Pronto quando |
|---|---|---|---|
| **FT-01** | Tokens do guia (`tokens.css`) | D | Nenhum hexadecimal fora do `tokens.css` |
| **FT-02** | `base.css` e `base.html`: topo, mensagens, rodapé, blocos `estilos`/`topo`/`scripts` | D | Toda página tem o topo preto com "QuizPessoal" |
| **FT-03** | `componentes.css` + `_anel`, `_barra`, `_topo_voltar` + letra grande e contraste | D | Os dois botões do topo ligam e ficam guardados |
| **FT-04** | `test_paginas.py` e remoção do `style.css` | D | Toda página abre no teste e nenhuma carrega o `style.css` |
| **FT-05** | Boas-vindas (tela 01) | A | Igual ao mockup 01; "Começar" leva à pergunta 1 sem JS |
| **FT-06** | Perguntas (telas 02–07) com `:target` | A | Uma pergunta por vez, barra, "Voltar", rodapé fixo; funciona sem JS |
| **FT-07** | `quiz.js`: avanço automático, Enter, foco, "Analisando" (tela 08) | A | Marcou → avança; enviar → tela "Analisando" |
| **FT-08** | Resultado (tela 09): destaque, anel, "por que", lista, PDF | B | Igual ao mockup 09, sem rolagem lateral no celular |
| **FT-09** | Detalhe do curso (tela 10) com afinidade e `quiz/permissoes.py` | B | Mostra "Sua afinidade" só para quem fez o teste |
| **FT-10** | Cartão da secretaria (`ESCOLA` no settings) | B | Sem `.env`, mostra só o nome da escola |
| **FT-11** | Entrar (tela 11) e criar conta com `_campo.html` | C | Igual ao mockup 11; erro de senha aparece no campo |
| **FT-12** | Minha lista (tela 12), meus testes e perfil | C | Igual ao mockup 12; estados vazios com ação |
| **FT-13** | Link de questionário encerrado | C | Token inválido mostra página própria, com 404 |
| **FT-14** | Painel nos tokens novos | C | Nenhum hexadecimal no `painel.css`; tabela larga rola dentro do cartão |
| **FT-15** | Limpeza: arquivos que ninguém usa | D | `quiz/views.py`, `quiz/dashboard.html`, `quiz/curso_detalhe.html` e `accounts/perfil.html` fora |
| **FT-16** | Revisão final: celular, teclado, sem JS, contraste | D | O roteiro da §3 do passo a passo D, todo marcado |

---

## 🔁 As rodadas

A FT-01 a FT-04 são **pequenas e vêm prontas** no passo a passo. Por isso a pessoa D mescla o PR-F1 **no primeiro dia**, e as outras três já trabalham em cima dele.

| Rodada | D | A | B | C |
|---|---|---|---|---|
| **1** | **PR-F1** (FT-01 a FT-04), mesclado no mesmo dia | Estrutura HTML da FT-05 e FT-06 | Estrutura HTML da FT-08 | Estrutura HTML da FT-11 |
| **2** | Revisa os PRs que abrirem | Atualiza com a `main` · CSS da FT-05/06 · FT-07 | Atualiza com a `main` · CSS da FT-08 · FT-09 e FT-10 | Atualiza com a `main` · FT-12 a FT-14 |
| **3** | **PR-F5** (FT-15 e FT-16) | Revisa o PR-F5 | Revisa o PR-F2 | Revisa o PR-F3 |

**Ordem de merge:** PR-F1 → (PR-F2, PR-F3 e PR-F4 em qualquer ordem) → PR-F5.

> [!warning] Entre o PR-F1 e os outros, as telas ficam sem estilo
> O PR-F1 tira o `style.css` antigo. Até o PR de cada tela entrar, aquela tela fica com o visual cru (funciona, mas sem cor). Por isso os PRs F2, F3 e F4 entram **na mesma rodada**, e ninguém apresenta nada da `main` nesse meio-tempo. O plano B da banca é a última tag antes do PR-F1.

## 🧩 Dono por arquivo

| Pessoa | Arquivos |
|---|---|
| **D** | `static/css/tokens.css`, `base.css`, `componentes.css` · `static/js/acessibilidade.js` · `templates/base.html` · `templates/componentes/_anel.html`, `_barra.html`, `_topo_voltar.html` · `quiz/tests/test_paginas.py` |
| **A** | `templates/quiz/quiz.html` · `static/css/quiz.css` · `static/js/quiz.js` |
| **B** | `templates/quiz/resultado.html` · `catalogo/templates/catalogo/curso_detalhe.html` · `catalogo/views.py` · `quiz/permissoes.py` · `core/contexto.py` · `templates/componentes/_secretaria.html` · `static/css/resultado.css`, `curso.css` · o `ESCOLA` e o context processor no `settings.py` · `quiz/tests/test_telas.py` |
| **C** | `accounts/templates/accounts/*` · `templates/quiz/aluno_perfil.html`, `link_invalido.html` · `templates/componentes/_campo.html` · `static/css/conta.css`, `painel.css` · `painel/templates/painel/dashboard.html` |

> [!important] Precisa de um componente novo?
> Primeiro veja se as classes do `componentes.css` resolvem. Se não resolverem, **peça à D**: componente criado dentro do CSS de uma tela vira cópia na tela seguinte.

## ✅ Definição de pronto (vale para os cinco PRs)

- [ ] `python manage.py test` sem falha nova (a do fuso só some com as tabelas carregadas)
- [ ] A tela aberta em **1440 px** e em **390 px**, comparada com o mockup, sem rolagem lateral
- [ ] Navegada **só com o teclado**: dá para chegar em tudo e sempre se vê o foco
- [ ] `grep -rn "#[0-9a-fA-F]\{3,6\}" backend/static/css --include=*.css | grep -v tokens.css` não encontra nada
- [ ] Nenhum texto sem acento que deveria ter ("voce", "opcao", "proxima")
- [ ] Print da tela no PR, ao lado do mockup

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/spec-front-templates|🎨 Spec do front]]
- [[Projetos/EducMatch(Secretária)/tarefas-backend-por-pessoa|👥 Tarefas por pessoa]] — as regras de convivência (Live Share, dono por arquivo) valem aqui também
