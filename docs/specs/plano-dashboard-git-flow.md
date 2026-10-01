---
title: "Dashboard novo — do alta fidelidade ao código (plano e Git Flow)"
aliases: ["Plano do dashboard", "Painel novo", "DSH"]
tags: [tcc, painel, dashboard, front, git, gitflow, plano, spec]
status: proposto
projeto: TCC
criado: 2026-10-01
---

> [!info] Design aprovado: `educmatch_dashboard_responsivo (2).html` (alta fidelidade, 15 telas) · Fase anterior: [[plano-pre-ia-git-flow|🚧 Pré-IA]]

# 🖥️ Dashboard novo: do alta fidelidade ao código

> [!abstract] O que esta nota é
> O alta fidelidade do painel foi aprovado em 2026-10-01. Ele tem **15 telas**, mas o banco só sustenta parte delas hoje. Esta nota divide o trabalho em **três fases**. As Fases **1** (três branches) e **2** (duas branches) já têm uma spec por branch; a Fase 3 está descrita para virar spec depois.
> Quem executa: **uma pessoa só**. A ordem é sequencial: cada branch sai da `develop` já com a anterior mesclada.

> [!success] O código das specs das Fases 1 e 2 já foi rodado
> As cinco branches foram aplicadas, em ordem, numa **cópia descartável** do backend (a partir da `main` em `7a0bd94`), testadas no MySQL e abertas no navegador com dados falsos, em 1440px e 375px:
> - a suíte fechou em **94 → 101 → 112 → 123 → 135** testes, todos verdes. Na `develop` real, com a PRE-03 mesclada (+2), os números são **96 → 103 → 114 → 125 → 137**;
> - `makemigrations --check` saiu limpo em cada etapa;
> - as migrações da DSH-03 e da FRM-01 foram rodadas **com dados**, na ida e na volta.
>
> Os números de teste de cada spec já contam a PRE-03.

---

## 🧭 Decisões de 2026-10-01

| Pergunta | Decisão |
|---|---|
| Implementar tudo de uma vez? | **Não. Três fases**, começando pelo que já tem dado no banco |
| Telas de tentativas mostram dado individual. E a privacidade? | **Anônimas**: o staff vê a tentativa (data, origem, resultado), mas **nunca** `respondido_por`, nome ou e-mail |
| % concluídos e tempo médio não existem no banco | **Criar o registro de início** (DSH-03), e não tirar os KPIs do design |
| Botões | **Nenhum botão fantasma**: todo botão do painel tem fundo sólido, com um teste que garante isso |
| O "formulário" aparece no fim do quiz? | **Não.** É uma **avaliação aplicada no fim do curso técnico** |
| Como o aluno responde a avaliação? | **Link por turma**, sem login |
| Anônima? | **Sempre**: nenhum model guarda usuário, nome, hora ou IP |
| Ligada a um curso? | **Sim**, a um curso do catálogo |
| Construtor de formulários? | **Não. Avaliação fixa**, com perguntas num seed (proposta a revisar pela coordenação) |

### 🔒 As duas regras que valem para toda tela do painel

1. **k-anonimato com K = 5.** Toda contagem menor que 5 vira "< 5" com cadeado, e toda **taxa** calculada sobre uma contagem escondida também some, porque taxa × total devolveria o número. Período com menos de 5 testes mostra só o total.
2. **Nenhum botão fantasma.** Variantes permitidas: `botao` (vermelho), `botao--secundario` (grafite), `botao--suave` (rosado), `botao--neutro` (gelo), `botao--perigo`. O `botao--contorno` e o `botao--texto` são do site do aluno.

---

## 🗺️ As três fases

| Fase | O que entra | Por que nesta ordem |
|---|---|---|
| **1. Painel com o que já existe** | Casca nova, Início, Quiz, Cursos e Áreas, Links, Lista de interesse, conclusão e tempo do quiz | Usa os dados que o banco já tem. Entrega o visual inteiro do design sem nenhuma funcionalidade nova para o aluno |
| **2. Avaliação de fim de curso** | App novo `avaliacao`: perguntas fixas, link por turma, página do aluno, resultados e CSV no painel | É funcionalidade nova, com models e fluxo do aluno. Precisa da casca da Fase 1 pronta |
| **3. Gestão do quiz** | Editor de questões e pesos, Tentativas anônimas, Detalhe da tentativa, Respostas unificadas | Mexe no que alimenta a engine (pesos). Fica por último para não competir com a camada de IA |

### Fase 1: as três branches

| # | Branch | Spec | O que resolve | Testes ao final |
|---|---|---|---|---|
| 01 | `feature/painel-casca-inicio-quiz` | [[spec-dsh-01-casca-inicio-quiz]] | Casca do design, botões sólidos, telas Início e Quiz, três métricas novas | 96 |
| 02 | `feature/painel-cursos-links-interesse` | [[spec-dsh-02-cursos-links-interesse]] | Telas Cursos e Áreas, Links (com QR e fechar um link) e Lista de interesse | 103 |
| 03 | `feature/quiz-conclusao-e-tempo` | [[spec-dsh-03-conclusao-e-tempo]] | `InicioDeQuiz`, `iniciado_em`, % concluídos e tempo típico | 114 |

> [!important] Por que nesta ordem
> - **01 primeiro:** cria a `base_painel.html`, o CSS e o JS que as outras duas usam.
> - **02 antes da 03:** a 02 não tem migração; a 03 tem. A parte com risco fica por último, sozinha num PR.
> - **03 antes do Passo 9 da IA:** a 03 edita o `pagina_quiz`, que o Passo 9 também vai editar (a chamada da LLM depois do `atomic`). Mesclar a 03 antes evita conflito no arquivo mais sensível do projeto.

### Fase 2: avaliação de fim de curso

| # | Branch | Spec | O que resolve | Testes ao final |
|---|---|---|---|---|
| FRM-01 | `feature/avaliacao-fim-de-curso` | [[spec-frm-01-avaliacao-fim-de-curso]] | App `avaliacao`: perguntas fixas, link por turma, página do aluno, resposta anônima | 125 |
| FRM-02 | `feature/painel-avaliacoes` | [[spec-frm-02-painel-avaliacoes]] | Painel: links das turmas com QR, resultados por curso e pergunta, CSV, KPI na Início | 137 |

> [!important] O que mudou em relação ao design
> O design tinha um **construtor** com 8 tipos de pergunta, status "pausado" e "vincular ao fim do quiz". Com as decisões acima, nada disso é necessário agora: a avaliação tem 4 tipos (nota 0–10, escala 1–5, escolha única, texto), as perguntas vêm de um seed, e "pausar" é fechar o link da turma. Se um dia a escola quiser outros formulários, o construtor entra como fase própria, em cima destes mesmos models.

### Fase 3: Gestão do quiz (spec a escrever)

| Tela | Observação |
|---|---|
| Questões e pesos | Hoje só pelo `/admin/`. Mudar peso muda a recomendação: precisa de aviso na tela e, idealmente, de versão do questionário |
| Tentativas | Lista anônima: data, origem, curso em 1º, banda de confiança, empate, IA/fallback. **Nunca** `respondido_por` |
| Detalhe da tentativa | Top 5 com `rank_engine` × `rank_final`, mostrando onde a IA reordenou. Depende do Passo 9 da IA |
| Respostas unificadas | Junta tentativas e avaliações. Depende da Fase 2 |

---

## 🐞 Achados da implementação de teste (fora do escopo, mas registrados)

| Achado | Onde | Sugestão |
|---|---|---|
| O filtro **"Mês" não tem fim**: `inicio_do_periodo("mes", "2026-03")` devolve só o começo, e `_no_periodo` filtra `criado_em >= início`. Escolher "março" mostra **tudo de março até hoje** | `painel/metricas.py` | Uma branch pequena `fix/painel-filtro-mes`, com `fim` em `_no_periodo` e um teste que cria uma tentativa em abril e confere que ela não entra em março |
| `.env.example` com um bloco `''' ... '''` (alteração local, ainda não commitada) | `backend/.env.example` | O leitor do `settings.py` ignora a linha porque ela não tem `=`, então não quebra. Mas `.env` não tem comentário de bloco: use `#` em cada linha |
| `_ranking.html` existia sem nenhum template usando | `painel/templates/painel/` | Resolvido na DSH-01, que passa a usá-lo |

---

## 🌿 O Git Flow desta fase

Mesmo fluxo da [[plano-pre-ia-git-flow|🚧 Pré-IA]]: `develop` já existe e é a *default branch*.

```
develop ──●──────●──────●──────●───●  (release/0.5.0-painel)
           \    / \    / \    /
            DSH-01  DSH-02  DSH-03
```

### 0. Pré-requisito

A **PRE-03** (`feature/config-llm`) mesclada na `develop`. As specs contam os testes a partir dos 86 dela.

### 1. Registrar as specs na `develop`

```bash
git switch develop && git pull
git add docs/specs/plano-dashboard-git-flow.md docs/specs/spec-dsh-*.md docs/specs/spec-frm-*.md
git commit -m "docs(specs): plano e specs das fases 1 e 2 do dashboard"
git push
```

### 2. O ciclo de cada feature (DSH-01, 02, 03, depois FRM-01, 02)

```bash
git switch develop
git pull
git switch -c feature/painel-casca-inicio-quiz
# ... seguir a spec ...
cd backend && python manage.py test && python manage.py makemigrations --check --dry-run && cd ..
git add -A
git commit -m "..."                         # a mensagem está no fim de cada spec
git push -u origin feature/painel-casca-inicio-quiz
gh pr create --base develop --fill
```

CI verde → merge no GitHub → apague a branch → só então a próxima.

### 3. As releases

Uma por fase. A da Fase 1, depois da DSH-03:

```bash
git switch develop && git pull
git switch -c release/0.5.0-painel
cd backend && python manage.py test && cd ..
git push -u origin release/0.5.0-painel
gh pr create --base main --title "release: 0.5.0 painel novo" --fill
```

Depois do merge na `main`:

```bash
git switch main && git pull
git tag -a v0.5.0 -m "Painel novo: casca, Inicio, Quiz, Cursos, Links, Interesse, conclusao e tempo"
git push origin v0.5.0
git switch develop && git merge main && git push
git push origin --delete release/0.5.0-painel
```

A da Fase 2, depois da FRM-02, com os mesmos comandos trocando o nome para `release/0.6.0-avaliacoes` e a tag para `v0.6.0`.

### 4. Na sua máquina, depois de cada release

A DSH-03 cria a migração `quiz.0005`; a FRM-01 cria o app `avaliacao` e as perguntas:

```bash
cd backend
python manage.py migrate
python manage.py seed_avaliacao          # só depois da FRM-01
```

---

## ✅ Definition of Done

**Fase 1**

- [ ] PRE-03 mesclada antes de começar
- [ ] As três features DSH mescladas na `develop`, **na ordem 01 → 02 → 03**
- [ ] CI verde em cada PR
- [ ] `python manage.py test` com **114 testes**
- [ ] O checklist de navegador de cada spec conferido em 1440px e 375px
- [ ] `release/0.5.0-painel` mesclada na `main`, tag `v0.5.0` publicada
- [ ] `migrate` rodado no banco local

**Fase 2**

- [ ] FRM-01 e FRM-02 mescladas na `develop`, nessa ordem
- [ ] `python manage.py test` com **137 testes**
- [ ] Perguntas do `seed_avaliacao` revisadas pela coordenação antes da primeira turma real
- [ ] `release/0.6.0-avaliacoes` mesclada na `main`, tag `v0.6.0`

## ▶️ Depois destas fases

1. `fix/painel-filtro-mes` (achado acima), pequena e independente.
2. Fase 3: escrever as specs depois do Passo 9 da IA, porque o Detalhe da tentativa depende dele.
