---
title: "Tarefas do grupo — quem faz o quê (4 frentes em paralelo)"
aliases: ["Checklist do grupo", "Checklist do backend", "Quem faz o quê", "Divisão em 4 frentes", "Rodadas do grupo"]
tags: [tcc, equipe, planejamento, checklist, django, templates]
status: proposto
projeto: TCC
criado: 2026-09-22
---

> [!info] Specs: [[Projetos/EducMatch(Secretária)/spec-pessoa-a-infra|🧱 A · Infra]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-b-dados-motor|🧮 B · Dados e motor]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-c-painel|📊 C · Painel]] · [[Projetos/EducMatch(Secretária)/spec-pessoa-d-telas|🎨 D · Telas do aluno]] · Equipe: [[Projetos/EducMatch(Secretária)/divisao-de-trabalho-tcc|👥 4 frentes]] · Contratos: [[contratos-c1-a-c6 🟢|📜 C1 a C6]]

# 👥 Tarefas do grupo — quem faz o quê

> [!abstract] O que esta nota é
> O mapa das quatro frentes: quem faz o quê, em que ordem, e as regras para ninguém atrapalhar ninguém. O passo a passo de cada pessoa está na spec dela (links acima).
> Estado conferido em 2026-09-22.

> [!important] Decisão de 2026-09-22: o front é HTML, CSS e JS puro
> O front React foi **abandonado** e a **API REST foi removida** (não tinha mais quem a usasse). As telas são os templates do Django. Consequência boa: **todo o grupo consegue mexer no front**, e o projeto roda num servidor só (`localhost:8000`).
> As specs `spec-front-react-vite`, `plano-execucao-front-react` e `passo-a-passo-fe-*` viram histórico. Da `passo-a-passo-bk-01-bk-08`, só vale o que não é API: BK-04, BK-05 e o settings da BK-08.

---

## As quatro frentes

| Pessoa | Frente | PRs | Em uma frase |
|---|---|---|---|
| **A** | 🧱 Infra | PR-1 · PR-6 | Settings por variável de ambiente, `ALLOWED_HOSTS`, fuso do MySQL e CI |
| **B** | 🧮 Dados e motor | PR-2 · PR-3 | Migrações, contrato C4 no `Interesse`, `explicacao` em JSON, correções do motor |
| **C** | 📊 Painel | PR-4 · PR-5 | Um painel só em `/painel/`, com k-anonimato e gerador de link |
| **D** | 🎨 Telas do aluno (quem cuida do front) | PR-0 · PR-7 · PR-8 | Quiz, resultado, detalhe do curso, perfil, acessibilidade |

---

## Regras de convivência

1. **Dono por arquivo.** Se o arquivo é de outra pessoa, peça no grupo antes de mexer.

   | Pessoa | É dona de |
   |---|---|
   | **A** | `core/settings.py`, `.env.example`, `core/tests.py`, `.github/`, a seção "Como rodar" do `README.md` |
   | **B** | **toda migração**, `*/models.py`, `*/admin.py`, `quiz/engine.py`, `accounts/servicos.py` |
   | **C** | `painel/` inteiro, `static/css/painel.css`, `templates/quiz/dashboard.html` e o dashboard em `quiz/views.py` |
   | **D** | `templates/`, `accounts/templates/`, `static/css/style.css`, `static/js/quiz.js`, `quiz/web_views.py`, `accounts/views.py`, `accounts/urls.py`, `catalogo/views.py` e `catalogo/urls.py` |

2. **Arquivos divididos, com combinado.** Mudança em funções diferentes do mesmo arquivo o Git junta sozinho; o problema é duas pessoas na **mesma** função.
   - **B** mexe em três funções da D (`areas_da_recomendacao`, `_salvar_interesse_pendente` e `salvar_interesse`). A D não toca nelas até o PR-2 entrar.
   - **C** pede à D um `{% block estilos %}` no `<head>` do `base.html` e o link "Dashboard" apontando para o painel. É a D quem faz, no primeiro dia.
   - **C** mexe nas duas linhas do dashboard em `quiz/web_urls.py`, e mais nada ali.
3. **Só a pessoa B cria migração.** Duas migrações no mesmo app ao mesmo tempo quebram o `migrate` de todo mundo.
4. **Antes de qualquer mudança, anote a linha de base:** `python manage.py test 2>&1 | tail -5`. Em 2026-09-22 ela era **28 testes, 7 falhas, 15 erros, 3 pulados**, a maioria por causa do `ALLOWED_HOSTS` vazio (resolvido no PR-1). No fim de cada PR: **nenhuma falha nova** e pelo menos **um teste novo que falharia antes**.
5. **Um PR por bloco**, branch criada do `main` atualizado, Conventional Commits e *squash merge*. Ninguém aprova o próprio PR. Revisão em até 24 h.
6. **Live Share:** código só se escreve na própria branch, na própria máquina. No Live Share, **quem hospeda é sempre o dono da branch**, e os outros entram para ajudar. O primeiro PR de cada pessoa é feito em par, com a pessoa D junto.

---

## Ninguém fica parado: as rodadas

Ordem de **merge** não é ordem de **trabalho**. Cada um cria a sua branch e começa no mesmo dia. Só existe **uma** dependência real: o PR-5 (métricas de demanda e aderência) usa os dados novos do PR-2.

| Rodada | A · Infra | B · Dados e motor | C · Painel | D · Telas |
|---|---|---|---|---|
| **0** | — | — | — | **PR-0**: fecha a remoção do React e da API |
| **1** | **PR-1** inteiro | **PR-2**: `Login`/`Cadastro` e `explicacao` em JSON | **PR-4**: URL, métricas que não rodam, privacidade | Cria o `{% block estilos %}` · **PR-7**: aviso de confiança e detalhe do curso |
| **2** | Revisa e testa os PRs dos outros no navegador | **PR-2**: C4 no `Interesse` e `servicos.py` | **PR-4**: template, gerador de link, aposenta o dashboard antigo | **PR-7**: perfil, histórico e lista |
| **3** | Começa o **PR-6** (CI) | Mescla o PR-2, **avisa o grupo** · começa o **PR-3** | **PR-5**: demanda por área e aderência | **PR-8**: acessibilidade e link de questionário |
| **4** | Liga a CI e a proteção da `main` | Fecha o **PR-3** (motor e índices) | Revisa o PR-8 (acessibilidade das telas) | **PR-8**: testes de rota C5 e C6 |

**Ordem de merge:** PR-0 → PR-1 → PR-2, PR-4 e PR-7 (em qualquer ordem) → PR-5 → PR-3 → PR-8 → PR-6.

Quem terminar antes da vez de mesclar **atualiza a branch** (`git pull --rebase origin main`) e espera, sem começar outra coisa na mesma branch.

> [!tip] Uma rodada não é um dia fixo
> A rodada acaba quando os PRs dela estão prontos para revisão. Marquem um check-in rápido no grupo no fim de cada uma: quem terminou antes puxa o próximo item, e a pessoa B não esquece de avisar quando o PR-2 entrar.

### Esperando? Tem trabalho útil

- **Escrever o teste antes do código.** Rode, veja ficar vermelho e só então implemente. Cumpre a regra do "teste que falharia antes" sem esforço extra.
- **Revisar o PR de outra pessoa.** Revisão parada trava o grupo mais do que código atrasado.
- **Testar a branch de um colega no navegador:** `git switch <branch>`, `runserver`, clicar em tudo que o PR diz que mudou.
- **Carregar as tabelas de fuso** no próprio MySQL (INF-04). Cada um faz isso uma vez.

---

## Decisões que continuam abertas

- **Em qual máquina roda o piloto** com respondentes reais. O banco é local, por pessoa: os dados do piloto ficam na máquina onde o quiz foi respondido, e é dela que saem os números da monografia. Decidir **antes** de coletar (risco 2 do plano v0.2).
- **Tirar o DRF de vez.** A API foi removida, mas o pacote continua instalado para o contrato C3 da camada de IA. Se a camada de IA não precisar de endpoint, sai do `requirements.txt` e do `INSTALLED_APPS`.

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/divisao-de-trabalho-tcc|👥 Divisão de trabalho]] · [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]]
- [[Projetos/EducMatch(Secretária)/front-templates-django|🎨 Front em templates do Django]]
- [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel e refino]] — a origem das regras de privacidade
