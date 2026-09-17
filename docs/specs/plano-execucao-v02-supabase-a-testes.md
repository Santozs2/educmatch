---
title: "Plano de execução v0.2 — Supabase, recomendação, painel e testes por contrato"
aliases: ["Plano v0.2", "Fases SB REC PNL TST", "Plano de execução do Supabase", "Ordem de serviço v0.2", "Migração para o Supabase"]
tags: [tcc, execucao, planejamento, git, supabase, painel, testes, contratos]
status: proposto
projeto: TCC
criado: 2026-09-17
---

> [!info] Auditoria: [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel e refino (REV-01…09)]] · Contratos: [[contratos-c1-a-c6 🟢|📜 C1 a C6]] · Git: [[git-ritual-de-entrega-do-tcc|🧾 Ritual de entrega]] · Equipe: [[Projetos/EducMatch(Secretária)/divisao-de-trabalho-tcc|👥 4 frentes]]

# 🗺️ Plano de execução v0.2 — quatro fases

> [!abstract] O que esta nota é
> O **o quê, em que ordem e por quem** das quatro entregas pedidas: migrar o banco para o **Supabase**, consertar os **erros da recomendação**, construir o **painel** e escrever os **testes pelos contratos**.
> O **como** — arquivo por arquivo, com o código no lugar certo — está em quatro notas separadas, uma por fase. Esta nota é o mapa; elas são o caminho.

> [!danger] Leia isto antes de qualquer comando
> Estas notas foram escritas contra as **notas de auditoria do vault**, não contra o repositório aberto. Cada caminho de arquivo e cada número de linha vem de [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|REV-01…09]] e de [[contratos-c1-a-c6 🟢|C1…C6]], registrados em 2026-09-11.
> **Nada disto foi executado.** Em cada fase existe uma seção de verificação: é ela que prova que deu certo, e nenhum comando dela é opcional.

## 1️⃣ A divergência que precisa ser resolvida no primeiro minuto

O vault descreve **dois** estados de repositório, e eles não são compatíveis:

| | Notas AUT / F1 / F2 (ago/2026) | Auditoria v0.1 (11/09/2026) |
|---|---|---|
| Pasta do projeto | `config/` | `core/` |
| Banco | SQLite | **MySQL 8.0.46** |
| Models | `Course`, `QuizAttempt`, `Recommendation` | `Curso`, `Tentativa_de_resposta`, `Recomendacao` |
| Suíte de testes | 12 testes verdes | **três `tests.py` vazios** |

Um comando resolve:

```bash
git log --oneline -5 && ls && ls quiz/ accounts/
```

> [!important] Este plano assume o estado **auditado** — `core/`, MySQL, models em português
> É a evidência mais recente, e é a única leitura em que "migrar para o Supabase" significa algo (do MySQL para o Postgres). Se o repositório estiver como as notas AUT descrevem, **as quatro fases continuam valendo na mesma ordem** — muda só o vocabulário, e a tradução completa já está tabelada em [[contratos-c1-a-c6 🟢|📜 C1 a C6, seção 9]].

> [!warning] A suíte de testes não foi "nunca escrita" — ela foi **perdida na tradução**
> [[Projetos/EducMatch(Secretária)/testes-e-validacao-tcc|✅ Testes e validação]] descreve 12 testes verdes em 17/08, com nomes em inglês. A auditoria de 11/09 encontra os três `tests.py` vazios, com o código todo em português. A reescrita para o português levou a suíte embora e ninguém percebeu, **porque não havia CI rodando `manage.py test` em cada PR**.
> Isso é um parágrafo da monografia, não uma fofoca: é a demonstração concreta de que *suíte de teste sem gatilho automático é documentação, não garantia*. A Fase 4 fecha essa porta.

---

## 2️⃣ Estado real, hoje

| Dimensão | Estado | Tratado em |
|---|---|---|
| Motor de matching (cosseno) | ✅ funcionando, ranking coerente | — |
| Catálogo | 20 cursos · 12 áreas · 73 pesos | — |
| Instrumento | 6 questões cobrindo **6 das 12 áreas** | fora de escopo (F3) |
| Banco | MySQL local, senha versionada | **Fase 1** |
| Segredos · `DEBUG` · `ALLOWED_HOSTS` | ❌ tudo em `core/settings.py` | **Fase 1** |
| Recomendação | ⚠️ 5 defeitos conhecidos | **Fase 2** |
| Painel administrativo | ❌ não existe | **Fase 3** |
| Camada REST | ❌ 3 endpoints em erro 500 | **Fase 4** |
| Testes automatizados | ❌ `tests.py` vazios, sem CI | **Fase 4** |
| Conformidade C1…C6 | ❌❌❌ 🟡🟡🟡 | **Fases 2 e 4** |

---

## 3️⃣ As decisões que este plano toma

Cada uma é uma escolha com alternativa real. Se o grupo discordar de alguma, **discorda aqui, na reunião, não no meio da fase** — as notas de execução dependem delas.

| | Decisão | Alternativa recusada | Por quê |
|---|---|---|---|
| **D1** | Supabase entra **só como Postgres gerenciado** | usar Supabase Auth e Storage | ver o aviso abaixo |
| **D2** | Conexão pelo **Session Pooler**, porta 5432 | conexão direta · transaction pooler (6543) | ver a Fase 1, SB-02 |
| **D3** | `manage.py test` roda em **Postgres local**, nunca no Supabase | rodar no Supabase · continuar em SQLite | ver o aviso abaixo |
| **D4** | `USE_TZ = True` **agora**, dentro da migração | deixar para depois | o custo de reinterpretar datas se paga uma vez só, e a auditoria já declarou as datas históricas imprecisas (REV-01) |
| **D5** | Vocabulário fica em **português**, com glossário versionado | renomear tudo para o inglês dos contratos | renomear custa migração em 7 models e invalida as notas F1/F2/AUT; o glossário custa uma tabela e resolve o achado central da auditoria |

> [!danger] D1 — o Supabase **não** vai cuidar do login. Isto não é negociável sem refazer três contratos
> A tentação é usar o Supabase por inteiro, porque é o que todo tutorial mostra. Neste projeto isso **quebraria o trabalho**:
> - o usuário do Django é um `AbstractUser` no banco, e `Interesse.usuario`, `Tentativa_de_resposta.user` e `@login_required` são chaves estrangeiras e decoradores que dependem dele;
> - o **C4** (registro de interesse), o **C5** (rotas e autorização) e o **C6** (*claim* da tentativa anônima) são contratos escritos em cima de `django.contrib.auth`;
> - com Supabase Auth, a tabela de usuários vive no schema `auth`, fora do ORM — cada uma dessas FKs vira consulta manual e o `/admin` deixa de listar gente.
>
> **O que o Supabase entrega aqui:** um Postgres gerenciado, com backup, painel de SQL e uma URL que funciona da casa de qualquer um dos quatro. É exatamente o que falta. Nada além disso entra.
> Consequência prática: as chaves `anon` e `service_role` que o painel do Supabase exibe **nunca são usadas e nunca entram no repositório**. Se alguém já as copiou para algum arquivo, apague.

> [!danger] D3 — teste nunca roda contra o Supabase
> `manage.py test` **cria e apaga um banco** a cada execução. Contra um banco compartilhado por quatro pessoas isso significa: dois testes simultâneos colidem no mesmo nome, e um `migrate` de alguém derruba a suíte de outro no meio.
> Além disso, é justamente na diferença **MySQL → Postgres** que mora o risco desta migração (comparação sensível a maiúsculas, ordenação com acento). Testar em SQLite esconderia exatamente o que precisa ser visto.
> Então: **Postgres local para teste, Supabase para desenvolver e demonstrar.** Um `DATABASE_URL` diferente, nada mais. A Fase 1 monta as duas pontas.

---

## 4️⃣ As quatro fases, em ordem

```
Fase 1 · SB ──► Fase 2 · REC ──► Fase 3 · PNL
  infra           recomendação      painel
  │                    │               │
  └────────────────────┴───────────────┴──► Fase 4 · TST
                                             testes por contrato + CI
```

| # | Fase | Branch | Dono | Revisor | PRs |
|---|---|---|---|---|---|
| 1 | 🗄️ **SB** — Supabase e segredos | `feat/infra-supabase` | quem abre a conta | scrum master | **2** |
| 2 | 🧮 **REC** — erros da recomendação | `fix/motor-recomendacao` | F1 · motor | F2 | 1 |
| 3 | 📊 **PNL** — painel administrativo | `feat/dash-painel` | F4 · jornada | F3 | 1 |
| 4 | 🧪 **TST** — testes por contrato | `test/contratos` | F1 + F2 | as duas pontas | 1 |

As quatro notas de execução:

- [[Projetos/EducMatch(Secretária)/passo-a-passo-sb-01-sb-06|🗄️ SB-01 a SB-06]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 REC-01 a REC-06]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 PNL-01 a PNL-05]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|🧪 TST-01 a TST-05]]

O prefixo `test/` é uma extensão consciente da [[git-convencao-de-branches|convenção de branches]], que hoje prevê só `feat/` e `fix/`. Combinem na reunião; o resto do padrão (minúsculas, kebab-case, sem acento) continua igual.

### Por que a recomendação vem **antes** do painel

O painel mede exatamente o que a Fase 2 conserta. Se as fases trocarem de lugar:

- a métrica de conversão filtra por `Interesse.criado_em`, que hoje é `auto_now` e significa *"interesses tocados no período"* (REV-01);
- a demanda por área lê `Recomendacao.explicacao`, que hoje é *repr* de dicionário Python dentro de um `TextField` (REV-03) — não dá para consultar;
- cursos desativados entram na contagem de matches (REV-02);
- a distribuição de confiança é calculada sobre o top-5 já cortado, então é quase sempre alta (REV-04).

Construir o painel antes seria construir quatro gráficos que mentem — e depois refazê-los. Esta é a mesma ordem que a [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|spec do painel]] já havia definido (`REV-01 → REV-04`, depois `PNL`).

### Por que o Supabase vem **antes** de tudo

Três motivos, e o terceiro é o que decide:

1. A Fase 2 tem uma migração que converte `TextField` em `JSONField`. No Postgres isso é `jsonb` nativo; fazer no MySQL e migrar depois é pagar a conversão duas vezes.
2. `REV-06` (segredos fora do código) é **pré-requisito** de qualquer jeito: não existe forma de pôr a senha do Supabase em `core/settings.py` versionado.
3. **É a única fase que muda o ambiente de todo mundo.** Como a AUT-01 fez com o `AUTH_USER_MODEL`, existe uma janela em que isso é barato — enquanto o banco só tem dado de teste. Essa janela fecha no dia em que a F3 cadastrar o catálogo real ou a turma responder o quiz de verdade.

### Por que os testes vêm **por último** — e por que isso não é negligência

A ordem ideal de livro é teste primeiro. Aqui ela não se aplica: as Fases 2 e 3 **mudam o comportamento** que um teste escrito hoje congelaria, e o teste teria de ser reescrito junto. Então:

- **cada fase entrega os seus próprios testes no seu próprio PR** — é o que a seção "testes deste bloco" de cada nota faz, no mesmo formato da [[Projetos/EducMatch(Secretária)/passo-a-passo-aut-01-aut-03|AUT-01/03]];
- a **Fase 4** é outra coisa: é a suíte de **conformidade de contrato**, que responde *"o C4 foi cumprido?"* com um comando em vez de com uma leitura de código. É ela que produz a tabela que o artigo precisa.

> [!important] Regra que vale das quatro fases
> Nenhum PR entra na `main` sem, no mínimo, **um teste novo que falharia antes da mudança**. Um só, se for esse o tamanho da mudança. É a única regra deste plano que não tem exceção — e é ela que impede a suíte de se perder de novo.

---

## 5️⃣ Onde cada achado da auditoria foi parar

Nenhum dos nove `REV` ficou órfão, e nenhum código novo foi inventado para concorrer com a numeração existente.

| Achado | O que é | Fase · tarefa |
|---|---|---|
| REV-06 | segredos versionados, `DEBUG=True`, `ALLOWED_HOSTS` vazio | SB-01 |
| REV-07 | models mortos `Login`/`Cadastro` com senha em texto puro | SB-03 |
| `requeriments.txt` | nome grafado errado, blocos repetidos | SB-05 |
| REV-01 | `Interesse.criado_em` é `auto_now` | REC-01 |
| REV-02 | motor recomenda curso inativo | REC-02 |
| REV-03 | `explicacao` gravada como *repr* de dicionário | REC-03 |
| REV-04 | confiança calculada sobre o top-5 já cortado | REC-04 |
| REV-09 | N+1 no cálculo do ranking (~27 consultas) | REC-05 |
| **C4** | faltam `afinidade_snapshot`, `rank_snapshot`, `era_principal` | REC-06 |
| PNL | o painel agregado, com k-anonimato | PNL-01…05 |
| REV-05 | três endpoints REST em erro 500 | TST-02 (é o **C3**) |
| REV-08 | views duplicadas, rota quebrada, `signals` nunca conectado | TST-03 (**C5**) e TST-04 (**C6**) |
| Cobertura do instrumento | 6 áreas sem nenhuma questão | ❌ **fora de escopo** — é da F3 |

> [!note] Os três parciais da auditoria viram verdes nesta trilha
> `C4` na REC-06, `C5` na TST-03, `C6` na TST-04. `C1`, `C2` e `C3` continuam pendentes por projeto, não por falha: pertencem aos Passos 7 a 11 da [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|camada de IA]], que retomam depois desta trilha.

---

## 6️⃣ Git — o mínimo que todo mundo precisa saber

> [!important] Quem nunca abriu um PR começa por aqui
> [[git-ritual-de-entrega-do-tcc|🧾 Ritual de entrega — Git passo a passo]]. São oito comandos, na ordem, com o que significa cada um e as seis situações de pânico (conflito, commit na `main` por engano, `.env` commitado, duas migrações com o mesmo número). Leia **antes** de começar a sua fase, não quando der errado.

O fluxo é o [[git-fluxo-aplicado-tcc|GitHub Flow]] já decidido pelo grupo: só `main` e branches curtas. O resumo operacional:

```bash
git checkout main && git pull        # sempre, antes de tudo
git checkout -b feat/infra-supabase  # a branch da sua fase
# ... trabalha, commita em pedaços ...
git push -u origin feat/infra-supabase
# abre o PR no GitHub, pede revisão, mescla com "Squash and merge"
```

- **Commits** em [[git-commits-e-mensagens|Conventional Commits]], com o escopo da fase: `feat(infra)`, `fix(motor)`, `feat(painel)`, `test(contratos)`.
- **Merge é sempre *squash*.** Um PR = um commit na `main`. O `git log --oneline` é a linha do tempo que vai para a monografia; commit de merge no meio suja essa leitura.
- **Ninguém aprova o próprio PR.** 1 aprovação basta, **2 quando o PR toca contrato de outra frente** — e nas Fases 2 e 4 isso acontece.
- **SLA de 24h** para o primeiro retorno da revisão.

### O campo do template de PR que decide tudo

```markdown
## Toca contrato de outra frente? ( ) não ( ) sim → qual
```

| Fase | Toca contrato? | Quem mais aprova |
|---|---|---|
| 1 · SB | **sim** — muda o banco de todo mundo | as quatro frentes ficam sabendo (aviso no grupo), 1 aprovação |
| 2 · REC | **sim** — `C4` e o `confidence_level` que o Passo 11 vai usar | F2 obrigatoriamente |
| 3 · PNL | não — o painel só lê | F3 |
| 4 · TST | **sim** — `C3`, `C5` e `C6` | as duas pontas de cada contrato |

---

## 7️⃣ Coordenação — quem toca o quê

A regra que evita 90% dos conflitos: **duas fases nunca abrem o mesmo arquivo na mesma semana.**

| Fase | Arquivos que ela é dona | O que ela **não** abre |
|---|---|---|
| 1 · SB | `core/settings.py`, `.env*`, `.gitignore`, `requirements.txt`, `README.md` | qualquer `views.py`, qualquer template |
| 2 · REC | `quiz/engine.py`, `quiz/models.py`, `accounts/models.py`, `accounts/views.py`, migrações | `core/settings.py` (só constantes novas no fim) |
| 3 · PNL | `painel/` inteiro, uma linha em `core/urls.py`, uma em `INSTALLED_APPS` | `quiz/`, `accounts/` — o painel **só lê** |
| 4 · TST | `*/tests/`, `quiz/serializers.py`, `quiz/views.py`, `accounts/signals.py`, `accounts/apps.py`, `.github/workflows/` | `quiz/engine.py` — se um teste exigir mudança lá, é REC, e volta para a Fase 2 |

> [!danger] O único conflito que o Git não resolve sozinho: duas migrações com o mesmo número
> As Fases 2 e 3 criam migração. Se as duas branches nascerem da mesma `main` e cada uma gerar `quiz/migrations/0003_*`, o Git mescla os **dois arquivos** sem reclamar — e o `migrate` quebra depois, na máquina de outra pessoa, com `Conflicting migrations detected`.
> Prevenção, em ordem de preferência:
> 1. **Serialize.** A Fase 3 só abre a branch depois de a Fase 2 estar na `main`. É o que este plano recomenda.
> 2. Se precisarem correr em paralelo, quem mesclar **depois** roda `git pull` na `main`, recria a branch e regenera a migração — nunca edita o número à mão.
> 3. `manage.py makemigrations --merge` só existe para quando o item 2 não foi feito. É remendo, e aparece no histórico.

---

## 8️⃣ Definição de pronto — vale para as quatro fases

Um PR está pronto quando **todas** as linhas abaixo são verdade. Não é burocracia: cada linha corresponde a um bug que já aconteceu neste projeto e está registrado em [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições]].

- [ ] `manage.py makemigrations --check --dry-run` diz que **não há mudanças pendentes**
- [ ] `PYTHONIOENCODING=utf-8 ... manage.py test` verde, **contra Postgres local**
- [ ] pelo menos um teste novo que **falharia antes** desta mudança
- [ ] os cliques manuais da seção de verificação da nota da fase, todos feitos
- [ ] `/admin` abre e lista Usuários, Cursos e Interesses (nenhum teste pega `FieldError` de admin)
- [ ] nenhum segredo novo no diff — `git diff main --stat` conferido antes do push
- [ ] nome novo de campo, método ou rota **acrescentado ao glossário** (D5)
- [ ] recado no grupo, **antes** do merge, se a fase exigir alguém apagar ou recriar banco

---

## 9️⃣ O que fica fora de escopo, de propósito

Dizer isto agora evita a conversa "achei que estava incluído" na semana da entrega.

- **Deploy da aplicação.** O Supabase hospeda o *banco*. O Django continua rodando em `runserver` na máquina de quem apresenta. Publicar o site é outra decisão, com outro custo.
- **Atualizar o Django.** Fica em 4.2.30 durante as quatro fases. Atualizar framework junto com banco é a receita para não saber qual dos dois quebrou.
- **Supabase Auth, Storage, Realtime, Edge Functions.** Ver D1.
- **RLS (*Row Level Security*).** O painel do Supabase vai exibir aviso de "RLS desativado" nas tabelas criadas pelo Django. É **esperado** e não é vulnerabilidade aqui: o único cliente do banco é o Django, autenticado por senha, e nenhuma chave `anon` foi publicada. RLS é a proteção de quem deixa o front falar direto com o banco — não é o caso. **Não habilite "para tirar o aviso"**: é configuração sem ganho aqui e com risco de efeito que ninguém do grupo vai saber depurar.
- **As 6 áreas sem questão.** É conteúdo, é da F3, e o painel vai justamente medir o tamanho do problema.
- **Passos 7 a 11 da camada de IA.** Retomam depois, com `C1`/`C2`/`C3`. A Fase 4 deixa o terreno preparado.

---

## 🔟 Os dois riscos de calendário

> [!warning] Risco 1 — o Supabase **pausa** projeto do plano gratuito
> Projeto gratuito sem atividade por alguns dias é pausado, e voltar exige alguém logar no painel e mandar restaurar. No dia da banca, com a sala esperando, isso é o tipo de falha que não se explica.
> Mitigação, as três juntas: (a) alguém abre o painel e roda o site **uma vez por semana**; (b) na véspera da defesa, `dumpdata` do banco inteiro guardado **fora do repositório**; (c) um `DATABASE_URL` alternativo apontando para o Postgres local, testado antes, que entra em vigor trocando uma linha do `.env`.

> [!warning] Risco 2 — a senha do banco fica com quem?
> A senha do Postgres do Supabase dá poder de apagar o banco inteiro. Ela **não entra no repositório**, nem no grupo do WhatsApp junto com o link — quem vaza os dois juntos entregou o banco.
> Combinem: **uma pessoa é dona da rotação da senha**, a distribuição é individual e por canal privado, e a senha antiga do MySQL (que está no histórico do Git para sempre) é considerada queimada e trocada também no servidor local.

---

## ▶️ Próxima ação

**Fase 1, PR-1: `REV-06` — só os segredos, sem trocar de banco.** Externalizar `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` e a URL do banco para o `.env`, com o `DATABASE_URL` ainda apontando para o MySQL local.

É o PR de menor risco da trilha inteira e o que mais desbloqueia: depois dele, mudar de banco é **trocar o valor de uma variável de ambiente** — e o *rollback* da migração para o Supabase passa a ser uma linha do `.env`, não um `git revert`.

Ver [[Projetos/EducMatch(Secretária)/passo-a-passo-sb-01-sb-06|🗄️ Passo a passo SB-01 a SB-06]].

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/passo-a-passo-sb-01-sb-06|🗄️ Fase 1 — Supabase e segredos]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 Fase 2 — erros da recomendação]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 Fase 3 — painel administrativo]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|🧪 Fase 4 — testes por contrato]]
- [[git-ritual-de-entrega-do-tcc|🧾 Ritual de entrega — Git passo a passo]] · [[git-fluxo-aplicado-tcc|🎓 Fluxo de Git do TCC]]
- [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel e refino]] — origem dos `REV`
- [[contratos-c1-a-c6 🟢|📜 Os contratos C1 a C6]] — origem dos `C`
- [[Projetos/EducMatch(Secretária)/passo-a-passo-aut-01-aut-03|🔑 AUT-01 a AUT-03]] — a nota que serviu de forma para estas quatro
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]] · [[Projetos|🚀 Projetos]]
