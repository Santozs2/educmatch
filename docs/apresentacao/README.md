# Apresentação técnica do EducMatch

Roteiro para a apresentação técnica. Esta pasta junta **o que mostrar**, **em que ordem** e **o que responder**. O detalhe de cada parte fica nos arquivos ao lado:

| Arquivo | Para quê |
| --- | --- |
| [backend.md](backend.md) | Models, engine de recomendação, views, painel com privacidade, contas e testes |
| [frontend.md](frontend.md) | Templates (HTMLs), componentes, scripts JS, CSS por tokens e acessibilidade |
| [demo-e-perguntas.md](demo-e-perguntas.md) | Roteiro da demonstração ao vivo, perguntas prováveis da banca e checklist da véspera |

---

## A mensagem central (decore esta frase)

> O EducMatch transforma as respostas de um quiz num **vetor de perfil**, compara esse vetor com o **vetor de cada curso** usando **similaridade de cosseno** e devolve os cursos mais parecidos, **explicando o porquê** de cada um. A coordenação acompanha a demanda num painel que **nunca mostra dados individuais** (k-anonimato, k = 5).

Tudo o que for mostrado precisa voltar para essa frase. Se a banca lembrar de uma coisa só, que seja o **cosseno com explicação** e a **privacidade no painel**.

---

## Estrutura sugerida (≈ 20 min + perguntas)

| # | Bloco | Tempo | Quem mostra | Conteúdo |
| --- | --- | --- | --- | --- |
| 1 | Problema e solução | 2 min | — | A escola tem muitos cursos técnicos e o aluno não sabe qual combina com ele. O EducMatch recomenda com base no perfil. |
| 2 | Arquitetura | 2 min | — | Django monolítico com renderização no servidor, 4 apps, MySQL. Diagrama abaixo. |
| 3 | **Demo ao vivo** | 5 min | — | Link → quiz → resultado → salvar interesse → login → painel. Ver [demo-e-perguntas.md](demo-e-perguntas.md). |
| 4 | Backend | 5 min | — | Models (DER), **engine**, views principais, privacidade do painel. |
| 5 | Front | 4 min | — | Templates, componentes, `quiz.js` (melhoria progressiva), tokens de CSS e acessibilidade. |
| 6 | Qualidade | 1 min | — | 64 testes automatizados, `transaction.atomic`, consultas otimizadas. |
| 7 | Limitações e próximos passos | 1 min | — | Seja honesto: a banca respeita quem conhece os limites do próprio sistema. |

> Preencha a coluna "Quem mostra" com o grupo. Cada pessoa deve apresentar a parte que **escreveu**, porque é dela que vão vir as perguntas mais difíceis.

---

## Arquitetura em um slide

```
Navegador (HTML + CSS + JS sem build)
        │  GET/POST (formulários, sessão, CSRF)
        ▼
Django 5.2  ── core/ (settings, rotas raiz, context processor da escola)
   ├─ quiz/       Questao, Alternativa, Peso_alternativa, Tentativa, Resposta,
   │              Recomendacao, QuestionarioLink  +  engine.py (cosseno)
   ├─ catalogo/   Area, Curso, Peso_curso  +  detalhe do curso
   ├─ accounts/   User (login por e-mail), Interesse (lista), signal de "adoção"
   └─ painel/     metricas.py (consultas agregadas) + privacidade.py (k = 5)
        │
        ▼
MySQL (fuso America/Sao_Paulo)
```

Três escolhas para defender logo no slide:

1. **Renderização no servidor, sem SPA.** O projeto começou com React e migrou para templates Django: um deploy só, sem API para proteger e com o quiz funcionando **mesmo sem JavaScript**.
2. **O "motor" é uma função pura** (`quiz/engine.py`): recebe vetores e devolve números, sem depender de banco. Por isso dá para testar isoladamente (`test_engine_puro.py`).
3. **A privacidade é aplicada no servidor.** O número suprimido nunca chega ao HTML.

---

## Fluxo do usuário (use para amarrar a demo com o código)

```
Coordenação gera link ──► /questionario/<uuid>/  (acessar_questionario grava o token na sessão)
                                  │
Aluno responde o quiz ──► / (pagina_quiz, POST)
                                  │  cria Tentativa + Respostas + chama engine.recomedacao()
                                  ▼
                          /resultado/<id>/ (resultado_pagina)  ── anel, barras, "por que este curso?"
                                  │
                          salvar interesse ──► pede login ──► signal adota a tentativa anônima
                                  ▼
                          /lista_interesse/  e  /painel/ (métricas agregadas, k = 5)
```

---

## O que NÃO fazer amanhã

- Ler código linha por linha. Mostre **o trecho**, explique **a decisão** e siga em frente.
- Abrir arquivos legados (`quiz/views.py`, `templates/quiz/dashboard.html`) sem ter a explicação pronta (ver perguntas).
- Fazer a demo com o banco vazio. Rode os seeds **e** tenha pelo menos 5 tentativas para o painel mostrar os números.
- Dizer "a IA recomenda". O motor é **matemático e determinístico** (cosseno). Se falarem em IA, apresente como proposta futura.
