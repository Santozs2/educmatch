---
title: "Apresentação técnica do EducMatch — roteiro"
aliases: ["Roteiro da apresentação", "Apresentação do TCC", "Índice da apresentação"]
tags: [tcc, apresentacao, roteiro, educmatch]
status: pronto
projeto: TCC
atualizado: 2026-10-08
---

> [!info] Apresentação: **🎤 Roteiro** · [[engine|🧮 Engine]] · [[backend|⚙️ Backend]] · [[frontend|🎨 Front]] · [[ia|🤖 Camada de IA]] · [[demo-e-perguntas|🎬 Demo e banca]]

# 🎤 Apresentação técnica do EducMatch

> [!abstract] O que esta pasta é
> O roteiro da apresentação: **o que mostrar, em que ordem e o que responder**. Cada parte tem a sua nota, e esta é o índice e a espinha dorsal.
> **A engine é a estrela.** Ela tem nota própria, com conta à mão e métricas medidas, e o roteiro reserva a ela o maior bloco de tempo.

| Nota | Para quê | Quem deve dominar |
|---|---|---|
| [[engine\|🧮 Engine]] | Cosseno, funções, conta à mão, régua de empate e **métricas de 5.000 perfis** | **Todo o grupo** |
| [[backend\|⚙️ Backend]] | Models, views, painel (métricas e privacidade), avaliação, deploy e 150 testes | Quem fez o backend |
| [[frontend\|🎨 Front]] | Templates, o truque do `:target`, painel, scripts, CSS por tokens e acessibilidade | Quem fez o front |
| [[ia\|🤖 Camada de IA]] | Como a LLM entra **sem tirar o lugar da engine**, as travas e o status | Quem está fazendo a LLM |
| [[demo-e-perguntas\|🎬 Demo e banca]] | Roteiro da demo, perguntas prováveis, pendências e checklist da véspera | **Todo o grupo** |

---

## 🎯 1. A mensagem central (decore esta frase)

> [!quote]
> O EducMatch transforma as respostas de um quiz num **vetor de perfil**, compara esse vetor com o **vetor de cada curso** usando **similaridade de cosseno** e devolve os 5 cursos mais parecidos, **explicando o porquê** de cada um e **avisando quando há empate**. A coordenação acompanha a demanda num **painel que fala de cursos, nunca de pessoas**, e a avaliação de fim de curso é **anônima por desenho**.

Tudo o que for mostrado precisa voltar para essa frase. Se a banca lembrar de uma coisa só, que seja **o cosseno com explicação**.

---

## 🔢 2. O projeto em números (um slide)

| | | | |
|:-:|:-:|:-:|:-:|
| **12** áreas | **20** cursos | **10** questões × 4 alternativas | **153** pesos (73 de curso + 80 de alternativa) |
| **6** apps Django | **150** testes automatizados | **0** rotas de API pública | **1** deploy (Azure App Service) |
| **≈ 0,9 ms** por ranking | **12** consultas por recomendação, sempre | **34%** dos perfis com empate no topo | **20/20** cursos aparecem no top 5 |

> [!note] De onde vêm os números
> Contagens dos seeds e da suíte em 2026-10-08. As métricas de desempenho e de empate vêm de 5.000 perfis simulados com as funções da própria engine (ver [[engine#📊 6. Métricas da engine (5.000 perfis simulados)|🧮 Engine, §6]]).

---

## ⏱️ 3. Estrutura sugerida (≈ 20 min + perguntas)

| # | Bloco | Tempo | Quem mostra | Conteúdo |
|:-:|---|:-:|---|---|
| 1 | Problema e solução | 2 min | | A escola tem muitos cursos técnicos e o aluno não sabe qual combina com ele. O EducMatch recomenda pelo perfil |
| 2 | Arquitetura | 1 min | | Django com renderização no servidor, 6 apps, MySQL, Azure. Diagrama da §4 |
| 3 | **Demo ao vivo** | 5 min | | Link → quiz → resultado → salvar → login → painel. Ver [[demo-e-perguntas\|🎬 Demo]] |
| 4 | ⭐ **Engine** | **5 min** | | Vetores, **conta à mão**, caso real, régua de empate e **métricas**. Ver [[engine\|🧮 Engine]] |
| 5 | Backend | 2 min | | Models (com o snapshot), controle de acesso, painel e avaliação anônima |
| 6 | Front | 2 min | | `:target` no quiz, melhoria progressiva, tokens e acessibilidade |
| 7 | Camada de IA | 1 min | | "A engine decide, a LLM entrega": travas e status. Ver [[ia\|🤖 IA]] |
| 8 | Qualidade e limites | 2 min | | 150 testes, CI, `transaction.atomic`, e os limites ditos com honestidade |

> [!tip] Preencham a coluna "Quem mostra"
> Cada pessoa apresenta a parte que **escreveu**, porque é dela que vão vir as perguntas mais difíceis. Mas **todos** precisam saber explicar a engine.

---

## 🏗️ 4. Arquitetura em um slide

```
Navegador (HTML + CSS + JS sem build)
        │  GET/POST (formulários, sessão, CSRF)
        ▼
Django 5.2  (gunicorn + WhiteNoise no Azure App Service)
   ├─ core/       settings (tudo do .env), rotas raiz, dados da escola
   ├─ quiz/       Questao, Alternativa, Peso_alternativa, Tentativa, Resposta,
   │              Recomendacao, QuestionarioLink, InicioDeQuiz
   │              + engine.py ★ (cosseno)   + llm/ (camada de IA, em construção)
   ├─ catalogo/   Area, Curso, Peso_curso
   ├─ accounts/   User (login por e-mail), Interesse (snapshot), signal de adoção
   ├─ painel/     metricas.py + metricas_avaliacao.py + privacidade.py
   └─ avaliacao/  Pergunta, LinkDeAvaliacao, RespostaDeAvaliacao (anônima)
        │
        ▼
MySQL (fuso America/Sao_Paulo)  ·  cache no banco (DatabaseCache)
```

Quatro escolhas para defender logo no slide:

1. **Renderização no servidor, sem SPA.** O projeto começou com React e migrou para templates: um deploy só, nenhuma API para proteger e o quiz funcionando **mesmo sem JavaScript**.
2. **A engine é feita de funções puras** (`quiz/engine.py`): recebem vetores e devolvem números, sem banco. Dá para testar sozinha e simular milhares de perfis.
3. **O painel fala de cursos, nunca de pessoas.** Nenhuma métrica lê nome nem e-mail, e o k-anonimato está pronto como chave (hoje desligado por decisão do grupo, ver [[backend|⚙️ Backend]]).
4. **A IA é incremento, não dependência.** A engine grava antes; desligue a LLM e o sistema continua recomendando.

---

## 🔀 5. Fluxo do usuário (amarra a demo com o código)

```
Coordenação gera link ─► /questionario/<uuid>/   acessar_questionario: token na sessão
                                │
Aluno responde o quiz ─► /   pagina_quiz (POST)
                                │  Tentativa + Respostas + engine.recomendar()  [transaction.atomic]
                                ▼
                         /resultado/<id>/   anel, "Por que este curso?", aviso de empate
                                │
                         salvar curso ─► login ─► signal adota a tentativa anônima
                                ▼
                         /lista_interesse/   e   /painel/ (Início, Quiz, Cursos, Links, Interesse)
                                │
Fim do curso ──────────► /avaliacao/<uuid>/   anônima ─► /painel/avaliacoes/ (NPS, CSV)
```

---

## 🚫 6. O que NÃO fazer na apresentação

> [!danger] Erros que custam pontos
> - **Ler código linha por linha.** Mostre o trecho, explique a decisão e siga.
> - **Dizer "a IA recomenda".** Quem recomenda é a **engine** (cosseno, determinística). A IA, quando estiver ligada, **explica** e só desempata onde há empate.
> - **Dizer que o painel suprime números pequenos.** Hoje `K_MINIMO = 0`: o mecanismo existe e é testado, mas está desligado por decisão do grupo.
> - **Fazer a demo com o banco vazio.** Rode os seeds e tenha várias tentativas com perfis diferentes.
> - **Abrir os arquivos legados** (`quiz/views.py`, `templates/quiz/dashboard.html`, `templates/quiz/curso_detalhe.html`) sem a resposta pronta (ver [[demo-e-perguntas|🎬 Demo e banca]]).
> - **Mostrar uma etapa da IA que ainda não está mesclada.** Na banca, só o que está na `main`.
