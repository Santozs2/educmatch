---
title: "Plano de execução v0.2 — infraestrutura, recomendação, painel e testes por contrato"
aliases: ["Plano v0.2", "Fases INF REC PNL TST", "Ordem de serviço v0.2", "Plano de execução do TCC"]
tags: [tcc, execucao, planejamento, git, mysql, painel, testes, contratos]
status: em-andamento
projeto: TCC
criado: 2026-09-17
---

> [!info] Auditoria: [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel e refino (REV-01…09)]] · Contratos: [[contratos-c1-a-c6 🟢|📜 C1 a C6]] · Git: [[git-ritual-de-entrega-do-tcc|🧾 Ritual de entrega]] · Equipe: [[Projetos/EducMatch(Secretária)/divisao-de-trabalho-tcc|👥 4 frentes]]

# 🗺️ Plano de execução v0.2 — quatro fases

> [!abstract] O que esta nota é
> O **o quê, em que ordem e por quem** das quatro entregas: consolidar a **infraestrutura** (segredos e banco), consertar os **erros da recomendação**, construir o **painel** e escrever os **testes pelos contratos**.
> O **como** — arquivo por arquivo, com o código no lugar certo — está em quatro notas separadas, uma por fase. Esta nota é o mapa; elas são o caminho.

> [!important] Revisado em 2026-09-17 — o banco continua MySQL
> A primeira versão deste plano tinha a migração para o **Postgres no Supabase** como Fase 1. **A decisão foi revertida no mesmo dia**, depois de a tentativa falhar por um motivo que não estava no radar de ninguém. A seção 3 registra a evidência, porque decisão revertida sem registro volta a ser proposta em duas semanas.
> O que sobrou dessa tentativa **e vale para sempre**: os segredos saíram do código versionado, e o banco passou a ser configurado por `DATABASE_URL`. Isso é independente de qual banco é, e é o ativo real do PR-1.

---

## 1️⃣ Estado real, hoje — verificado no repositório

| Dimensão | Estado | Tratado em |
|---|---|---|
| Motor de matching (cosseno) | ✅ funcionando | — |
| Banco | ✅ **MySQL 8.0.36**, `educmatch`, `utf8mb4` | — |
| Catálogo | ✅ **12 áreas · 20 cursos · 73 pesos** | INF-03 (destravado) |
| Instrumento | 6 questões cobrindo **6 das 12 áreas** | fora de escopo (F3) |
| Segredos / `DEBUG` / `ALLOWED_HOSTS` | ✅ no `.env`, fora do código | INF-01 ✔ |
| Models mortos com senha em texto puro | ✅ removidos (`accounts/0003`) | INF-02 ✔ |
| Tabelas de fuso do MySQL | ❌ **vazias** — `CONVERT_TZ` devolve `NULL` | INF-04 |
| Recomendação | ⚠️ 5 defeitos conhecidos | **Fase 2** |
| Painel administrativo | ❌ não existe | **Fase 3** |
| Camada REST | ❌ 3 endpoints em erro 500 | **Fase 4** |
| Testes automatizados | ⚠️ 9 em `core/`, os outros `tests.py` vazios | **Fase 4** |
| Conformidade C1…C6 | ❌❌❌ 🟡🟡🟡 | **Fases 2 e 4** |

> [!success] O catálogo estava incompleto, e ninguém sabia
> Até 17/09 este banco tinha **7 áreas e 12 cursos**, não os 12 e 20 que a auditoria relata. A causa eram **dois bugs empilhados** nos seeds, um escondendo o outro:
> 1. `seed_areas` não tinha `marketing` nem `design`, que o `seed_cursos` referencia;
> 2. `seed_cursos.py:166` montava a mensagem de erro com `data['nome_curso']`, onde a chave é `nome` — então o `CommandError` legível virava `KeyError`, o `@transaction.atomic` revertia **os 20 cursos**, e o banco ficava com o catálogo antigo sem dizer por quê.
>
> Corrigidos os dois, `seed_cursos` fecha em 20 cursos e 73 pesos. **A lição é a verificação:** "não deu erro" não era sinal de nada — o sinal é a **contagem**. Por isso a seção 8 exige conferir número, não ausência de traceback. Registrado em [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições]].

---

## 2️⃣ A divergência de vocabulário que continua valendo

O vault descreve dois estados de repositório. O real é o **auditado**: pasta `core/`, models em português (`Curso`, `Tentativa_de_resposta`, `Recomendacao`, `Interesse`), função `recomedacao()` com erro de grafia, campo `envio_recurso` que não é tradução de `source_attempt`.

As notas AUT/F1/F2 descrevem `config/`, SQLite e models em inglês — um estado que não existe mais. A tradução completa dos onze pares está em [[contratos-c1-a-c6 🟢|📜 C1 a C6, seção 9]], e as duas specs antigas já levaram banner de aviso no topo.

---

## 3️⃣ Registro da decisão revertida — Supabase

> [!danger] Tentado e revertido em 2026-09-17. Não reabrir sem ler isto
> A proposta era migrar do MySQL para um Postgres gerenciado no Supabase, para os quatro compartilharem um banco só. O projeto foi criado (`EducMatch`, `sa-east-1`, Postgres 17.6, `ACTIVE_HEALTHY`) e **nunca recebeu uma conexão do Django**. O que foi medido:
>
> | Verificação | Resultado |
> |---|---|
> | Projeto no Supabase | ✅ ativo, API REST respondendo `401` |
> | Banco por HTTPS (conector) | ✅ alcançável, `select version()` funciona |
> | Porta **5432** (session pooler) | ❌ **bloqueada na rede** — TCP "abre" em 12 s e o handshake TLS é dropado |
> | Controle: Postgres público sem relação com o Supabase, 5432 | ❌ **mesmo sintoma** |
> | Porta **6543** (transaction pooler) | ✅ TCP + TLS 1.3 completos em ~135 ms, consistentemente |
> | Autenticação na 6543 | ❌ o pooler fecha antes de olhar credencial — **erro idêntico com senha propositalmente errada**, logo não é senha |
> | `db.<ref>.supabase.co` | ❌ não resolve (IPv4 é add-on pago) |
> | Gerar o DDL do Postgres sem conexão | ❌ `sqlmigrate` exige conexão viva |
>
> **Conclusão:** a rede onde o grupo desenvolve **e vai apresentar** não permite tráfego Postgres de saída de forma confiável. A 5432 é bloqueada por filtro de terceiro que ninguém do grupo controla; a 6543 chega ao *pooler* mas não roteia o *tenant*. HTTPS funciona normalmente.
>
> **Se alguém quiser reabrir:** a única configuração que resolveria de raiz é hospedar a **aplicação Django na nuvem também**, para que o tráfego Postgres seja nuvem-a-nuvem e da escola só se precise de HTTPS. Isso é um deploy, com custo e escopo próprios — e viraria a demonstração da defesa numa URL em vez de um notebook, o que é um ganho separado. **Não é pré-requisito de nenhuma das quatro fases.**

> [!success] O que a tentativa deixou de bom, e fica
> - `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` e o banco vindos do `.env` (`REV-06` fechado) — o ganho é independente de qual banco é
> - `dj_database_url` lendo `DATABASE_URL`: trocar de banco virou trocar **o valor de uma variável**, não editar `settings.py`
> - `.env.example` como contrato de ambiente versionado
> - os models mortos `Login` e `Cadastro` fora do esquema (`REV-07`)
> - `requirements.txt` com o nome certo, sem os três blocos repetidos
> - **os dois bugs de seed**, que só apareceram porque alguém finalmente rodou os seeds do zero

---

## 4️⃣ As decisões que este plano toma

| | Decisão | Alternativa recusada | Por quê |
|---|---|---|---|
| **D1** | Banco é **MySQL 8 local**, um por pessoa | Postgres gerenciado na nuvem | ver a seção 3 |
| **D2** | Configuração do banco por **`DATABASE_URL`** no `.env` | voltar o bloco `DATABASES` para o `settings.py` | trocar de banco é trocar uma variável; e é o que fecha o `REV-06` |
| **D3** | `manage.py test` roda no **MySQL local**, com banco `test_educmatch` | banco de teste compartilhado · SQLite | já funciona: `tecmysql` tem `CREATE`, e a suíte criou e destruiu o banco de teste sem ajuste |
| **D4** | `USE_TZ = True` + `TIME_ZONE = America/Sao_Paulo` | `TIME_ZONE = UTC` para fugir do `CONVERT_TZ` | o painel filtra e agrupa por período; datas em UTC na tela são erro de leitura esperando acontecer. O custo é carregar as tabelas de fuso uma vez (INF-04) |
| **D5** | Vocabulário fica em **português**, com glossário versionado | renomear tudo para o inglês dos contratos | renomear custa migração em 7 models e invalida as notas F1/F2/AUT; o glossário custa uma tabela e resolve o achado central da auditoria |

> [!important] D1 tem uma consequência boa que a versão anterior deste plano não tinha
> Com banco local por pessoa, **não existe banco compartilhado para quebrar**. Cai a regra "`migrate` só depois do merge", cai o risco de alguém aplicar migração de uma branch no banco de todos, e cai o combinado de distribuir senha por canal privado.
> O ritual volta a ser o que o grupo já conhece: `git pull` → `migrate` → seeds se preciso. Para um grupo que está aprendendo Git, isso é uma superfície de erro a menos — e o catálogo inteiro nasce de comando, então recriar o banco custa quatro linhas.

> [!warning] E uma consequência ruim, que precisa estar dita
> Métrica agregada de vários respondentes exige juntar dados de máquinas diferentes. Enquanto o piloto não roda, é irrelevante — o painel da Fase 3 mede o banco de quem o abre. **Na hora do piloto com respondentes reais, o grupo precisa decidir em qual máquina ele roda**, e essa máquina passa a ser a fonte dos números da monografia. Decidir antes de coletar, não depois.

---

## 5️⃣ As quatro fases, em ordem

```
Fase 1 · INF ──► Fase 2 · REC ──► Fase 3 · PNL
  infra            recomendação      painel
  │                     │               │
  └─────────────────────┴───────────────┴──► Fase 4 · TST
                                              testes por contrato + CI
```

| # | Fase | Branch | Dono | Revisor | Estado |
|---|---|---|---|---|---|
| 1 | 🧱 **INF** — segredos, banco e seeds | `feat/infra-supabase` ⚠️ | quem cuida da infra | scrum master | 🟡 **quase pronta** — falta INF-04 |
| 2 | 🧮 **REC** — erros da recomendação | `fix/motor-recomendacao` | F1 · motor | F2 | ⬜ |
| 3 | 📊 **PNL** — painel administrativo | `feat/dash-painel` | F4 · jornada | F3 | ⬜ |
| 4 | 🧪 **TST** — testes por contrato | `test/contratos` | F1 + F2 | as duas pontas | ⬜ |

> [!warning] O nome da branch da Fase 1 ficou errado
> Ela se chama `feat/infra-supabase` e já está no `origin`, mas não migra nada para o Supabase — o conteúdo virou "segredos no `.env`, MySQL consolidado e seeds destravados". **Nenhum PR foi aberto ainda**, então renomear é barato:
> ```bash
> git branch -m feat/infra-supabase feat/infra-segredos
> git push -u origin feat/infra-segredos
> git push origin --delete feat/infra-supabase
> ```
> Se preferir não mexer, o PR pode simplesmente explicar o nome. O que não vale é abrir um PR chamado "supabase" que não tem Supabase dentro.

As quatro notas de execução:

- [[Projetos/EducMatch(Secretária)/passo-a-passo-inf-01-inf-05|🧱 INF-01 a INF-05]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 REC-01 a REC-06]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 PNL-01 a PNL-05]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|🧪 TST-01 a TST-05]]

### Por que a recomendação vem **antes** do painel

O painel mede exatamente o que a Fase 2 conserta:

- a conversão por período filtra por `Interesse.criado_em`, que hoje é `auto_now` e significa *"interesses tocados no período"* (`REV-01`);
- a demanda por área lê `Recomendacao.explicacao`, hoje *repr* de dicionário Python num `TextField` (`REV-03`) — não se consulta;
- cursos desativados entram na contagem de matches (`REV-02`);
- a distribuição de confiança é calculada sobre o top-5 já cortado, então é quase sempre alta (`REV-04`).

Construir o painel antes seria construir quatro gráficos que mentem. É a mesma ordem que a [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|spec do painel]] já definia.

### Por que os testes vêm **por último** — e por que não é negligência

As Fases 2 e 3 **mudam o comportamento** que um teste escrito hoje congelaria. Então:

- **cada fase entrega os seus próprios testes no seu próprio PR** — é o que a seção "testes deste bloco" de cada nota faz;
- a **Fase 4** é outra coisa: é a suíte de **conformidade de contrato**, que responde *"o C4 foi cumprido?"* com um comando em vez de com uma leitura de código.

> [!important] Regra que vale das quatro fases
> Nenhum PR entra na `main` sem **um teste novo que falharia antes da mudança**. Um só, se for esse o tamanho da mudança. É a única regra sem exceção — e é ela que impede a suíte de se perder de novo.

---

## 6️⃣ Onde cada achado da auditoria foi parar

| Achado | O que é | Fase · tarefa | Estado |
|---|---|---|---|
| REV-06 | segredos versionados, `DEBUG`, `ALLOWED_HOSTS` | INF-01 | ✅ |
| REV-07 | models mortos `Login`/`Cadastro` com senha em texto puro | INF-02 | ✅ |
| `requeriments.txt` | nome errado, blocos repetidos, `mysqlclient` de volta | INF-05 | ✅ |
| Seeds | `marketing`/`design` ausentes + `KeyError` mascarando o erro | INF-03 | ✅ |
| Fuso do MySQL | tabelas de fuso vazias, `CONVERT_TZ` → `NULL` | **INF-04** | 🟡 |
| REV-01 | `Interesse.criado_em` é `auto_now` | REC-01 | ⬜ |
| REV-02 | motor recomenda curso inativo | REC-02 | ⬜ |
| REV-03 | `explicacao` gravada como *repr* de dicionário | REC-03 | ⬜ |
| REV-04 | confiança sobre o top-5 já cortado | REC-04 | ⬜ |
| REV-09 | N+1 no cálculo do ranking | REC-05 | ⬜ |
| **C4** | faltam os três campos de *snapshot* | REC-06 | ⬜ |
| PNL | o painel agregado, com k-anonimato | PNL-01…05 | ⬜ |
| REV-05 | três endpoints REST em erro 500 | TST-02 | ⬜ |
| REV-08 | views duplicadas, rota quebrada, `signals` nunca conectado | TST-03 e TST-04 | ⬜ |
| Cobertura do instrumento | 6 áreas sem nenhuma questão | ❌ **fora de escopo** — é da F3 | — |

---

## 7️⃣ Git — o mínimo que todo mundo precisa saber

> [!important] Quem nunca abriu um PR começa por aqui
> [[git-ritual-de-entrega-do-tcc|🧾 Ritual de entrega — Git passo a passo]]. Oito comandos, na ordem, e as seis situações de pânico. Leia **antes** de começar a sua fase.

```bash
git checkout main && git pull
git checkout -b fix/motor-recomendacao
# ... trabalha, roda os testes ...
git push -u origin fix/motor-recomendacao
# abre o PR, pede revisão, mescla com "Squash and merge"
```

- **Commits** em [[git-commits-e-mensagens|Conventional Commits]], escopo da fase: `infra`, `motor`, `painel`, `contratos`.
- **Merge é sempre *squash*.** Um PR = um commit na `main`.
- **Ninguém aprova o próprio PR.** 1 aprovação basta, **2 quando toca contrato de outra frente** — nas Fases 2 e 4 acontece.
- **SLA de 24h** para o primeiro retorno.

| Fase | Toca contrato? | Quem mais aprova |
|---|---|---|
| 1 · INF | **sim** — todo mundo precisa criar o `.env` | 1 aprovação + aviso no grupo |
| 2 · REC | **sim** — `C4` e o `confidence_level` do Passo 11 | F2 obrigatoriamente |
| 3 · PNL | não — o painel só lê | F3 |
| 4 · TST | **sim** — `C3`, `C5` e `C6` | as duas pontas de cada contrato |

---

## 8️⃣ Definição de pronto — vale para as quatro fases

Cada linha corresponde a um defeito que já aconteceu neste projeto.

- [ ] `manage.py makemigrations --check --dry-run` diz **No changes detected**
- [ ] `PYTHONIOENCODING=utf-8 ... manage.py test` verde
- [ ] pelo menos um teste novo que **falharia antes** desta mudança
- [ ] os cliques manuais da seção de verificação da nota da fase, todos feitos
- [ ] `/admin` abre e lista Usuários, Cursos e Interesses
- [ ] **contagem conferida**, não ausência de erro — `12 / 20 / 73` no catálogo
- [ ] nenhum segredo novo no diff — `git diff main --stat` antes do push
- [ ] nome novo de campo, método ou rota **no glossário** (D5)

> [!danger] A penúltima linha é a lição do dia 17/09
> O `seed_cursos` "não dava erro" porque o erro dele era um `KeyError` dentro da mensagem de erro, e o `@transaction.atomic` revertia tudo em silêncio. **Terminar sem traceback não é sinal de sucesso.** Sinal é número: 12 áreas, 20 cursos, 73 pesos.

---

## 9️⃣ O que fica fora de escopo, de propósito

- **Deploy da aplicação.** O Django roda em `runserver` na máquina de quem apresenta. Ver a seção 3: virou a alternativa de longo prazo para o problema de rede, mas não é pré-requisito de nada aqui.
- **Atualizar o Django.** Fica em 4.2.30 durante as quatro fases.
- **Trocar de banco.** Ver a seção 3. Reabrir só com a evidência de lá na mesa.
- **As 6 áreas sem questão.** É conteúdo, é da F3, e o painel vai medir o tamanho do buraco.
- **Passos 7 a 11 da camada de IA.** Retomam depois, com `C1`/`C2`/`C3`. A Fase 4 prepara o terreno.

---

## 🔟 Riscos

> [!warning] Risco 1 — a senha do MySQL e a `SECRET_KEY` originais estão no histórico do Git
> Estavam em claro em `core/settings.py` desde o primeiro commit. Tirá-las do arquivo **não** as tira do histórico: `git show <commit>:core/settings.py` ainda as devolve. As duas são **consideradas queimadas** e precisam ser trocadas no servidor, não só no arquivo. É a parte do `REV-06` que não se resolve com `.env`.

> [!warning] Risco 2 — banco local por pessoa e o piloto
> Enquanto é desenvolvimento, é vantagem (D1). No piloto com respondentes reais, os dados ficam na máquina em que o quiz foi respondido, e o painel só vê o banco local. **Decidir a máquina do piloto antes de coletar** — depois não há como juntar sem trabalho manual.

> [!warning] Risco 3 — a rede da escola
> Medido em 17/09: a porta 5432 é bloqueada na saída. Não afeta o MySQL local, mas afeta qualquer serviço externo que o projeto venha a usar por porta não-HTTP. Se um dia a camada de IA precisar de algo que não seja HTTPS, esse é o primeiro suspeito — e a medição está na seção 3.

---

## ▶️ Próxima ação

**INF-04 — carregar as tabelas de fuso do MySQL.** É o último item aberto da Fase 1, e é o único que bloqueia a Fase 3: com as tabelas vazias, `CONVERT_TZ` devolve `NULL` e todo filtro por `__date`, `__month` ou `TruncDate` passa a **devolver vazio sem erro**. O teste `test_mysql_conhece_o_fuso_de_sao_paulo` já está no repositório, vermelho, esperando.

Depois: Fase 2, `REC-01` a `REC-06`, num PR único.

Ver [[Projetos/EducMatch(Secretária)/passo-a-passo-inf-01-inf-05|🧱 Passo a passo INF-01 a INF-05]].

## 📎 Veja também

- [[Projetos/EducMatch(Secretária)/passo-a-passo-inf-01-inf-05|🧱 Fase 1 — infraestrutura]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-rec-01-rec-06|🧮 Fase 2 — erros da recomendação]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-pnl-01-pnl-05|📊 Fase 3 — painel administrativo]]
- [[Projetos/EducMatch(Secretária)/passo-a-passo-tst-01-tst-05|🧪 Fase 4 — testes por contrato]]
- [[git-ritual-de-entrega-do-tcc|🧾 Ritual de entrega]] · [[git-fluxo-aplicado-tcc|🎓 Fluxo de Git do TCC]]
- [[Projetos/EducMatch(Secretária)/spec-painel-admin-e-refino|📊 Spec do painel e refino]] — origem dos `REV`
- [[contratos-c1-a-c6 🟢|📜 Os contratos C1 a C6]] — origem dos `C`
- [[Projetos/EducMatch(Secretária)/bugs-e-licoes-tcc|🐛 Bugs e lições]] — os dois bugs de seed e o achado da rede
- [[Projetos/EducMatch(Secretária)/TCC|🎓 TCC]] · [[Projetos|🚀 Projetos]]
