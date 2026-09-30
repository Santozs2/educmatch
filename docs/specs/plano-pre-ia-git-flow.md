---
title: "Pré-IA — o que muda no código antes da LLM (plano e Git Flow)"
aliases: ["Plano pré-IA", "Pré-requisitos da camada de IA", "Git Flow pré-IA"]
tags: [tcc, ia, llm, git, gitflow, plano, spec]
status: proposto
projeto: TCC
criado: 2026-09-30
---

> [!info] Plano da IA: [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Camada de IA]] · Decisão: [[decisao-camada-ia 🟢|🤖 Decisão]] · Prompt: [[Projetos/EducMatch(Secretária)/prompt-padrao-recomendacao|📝 Prompt padrão]]

# 🚧 Pré-IA: o que muda no código antes da LLM

> [!abstract] O que esta nota é
> A revisão de 2026-09-30, feita contra a `main` em `22567a6`, concluiu que o sistema **está pronto para começar o Passo 7** (a parte offline), mas **não para ligar o Gemini**. Esta nota divide o que falta em **quatro branches**, uma spec para cada, e diz a ordem em que entram pelo Git Flow.
> Quem executa: **uma pessoa só**. Por isso a ordem é sequencial: cada branch sai da `develop` já com a anterior mesclada.

> [!success] O código das specs já foi rodado
> Cada mudança foi aplicada numa **cópia descartável** do backend e testada no MySQL antes de virar spec:
> - a suíte fechou em **86 testes, 85 verdes**; o único vermelho é o do fuso, que é da máquina local e passa na CI;
> - `makemigrations --check` saiu limpo;
> - a migração da branch 01 foi rodada **com dados já existentes**, na ida e na volta.
>
> Os números de teste de cada spec são os que você deve ver.

---

## 🗺️ As quatro branches

| # | Branch | Spec | O que resolve | Testes ao final |
|---|---|---|---|---|
| 00 | `feature/limpeza-pre-ia` | [[spec-pre-ia-00-limpeza]] | Nome `recomedacao`, `banda()` documentada (fica), arquivos vazios, CI olhando a `develop` | 74 (73 ✅ + fuso) |
| 01 | `feature/rank-engine-final` | [[spec-pre-ia-01-rank-final]] | `rank` → `rank_engine` + `rank_final`, metadados `llm_*`, "principal" = o que o aluno viu | 78 |
| 02 | `feature/conjunto-de-empate` | [[spec-pre-ia-02-empate]] | Uma régua só para empate, `tie_set` preenchido, aviso de confiança com o texto certo | 84 |
| 03 | `feature/config-llm` | [[spec-pre-ia-03-config-llm]] | Variáveis `LLM_*`, cache no banco, CI com a LLM desligada | 86 |

> [!important] Por que nesta ordem
> - **00 primeiro:** ela renomeia `recomedacao` → `recomendar`, e esse nome aparece no `engine.py` e no `web_views.py`, que a 01 e a 02 também editam. Renomear primeiro evita conflito nas duas seguintes.
> - **01 antes da 02:** os testes da 02 usam `rank_engine`, que só passa a existir na 01.
> - **03 por último:** ela não depende das outras, então pode ir em qualquer lugar da fila. Fica no fim para não atrasar a migração, que é a parte com risco.

### 🛟 O motor nunca sai do ar

> [!important] Regra da fase, decidida em 2026-09-30
> **A engine continua funcionando inteira e sozinha.** A IA é uma camada **em cima** dela e nunca **no lugar** dela. Se a IA der qualquer erro, o aluno recebe o resultado da engine, sem erro 500 e sem tela em branco. Nenhuma branch desta fase remove código do motor: `banda()`, os cortes, `confianca()` e `explicacao()` ficam.

Como cada branch sustenta essa regra:

| Garantia | Onde | Como |
|---|---|---|
| A engine grava **antes** da IA | já existe (`recomendar()` dentro do `atomic`) | O ranking está no banco antes de qualquer chamada de rede |
| Sem IA, a ordem entregue **é** a da engine | 01 | `rank_final = rank_engine` no `bulk_create`, com teste |
| A ordem da engine **nunca se perde** | 01 | `rank_engine` é coluna própria: a IA só escreve em `rank_final` |
| A IA só troca o 1º lugar em empate real | 02 | `tie_set` calculado pela engine, e não pela LLM |
| **Desligar a IA** é uma linha | 03 | `LLM_ENABLED=0` (e é o padrão) |
| Falha da IA → volta para a engine | Passo 9 | Timeout, JSON inválido ou sem crédito: `used_fallback=True` e `rank_final` continua igual ao `rank_engine` |

> [!tip] O teste que o Passo 9 tem de trazer
> Um provider que **lança exceção** e um que devolve **lixo** precisam terminar em: tela com status 200, os 5 cursos na ordem da engine e `used_fallback=True`. Enquanto esse teste não existir, a IA não entra na `main`.

### O que fica de fora de propósito

Estes itens foram apontados na revisão, mas **pertencem aos Passos 7 a 9**, e não a esta fase:

| Item | Onde entra |
|---|---|
| Chamar a LLM **depois** do `transaction.atomic()` do `pagina_quiz` | Passo 9 (é onde a chamada nasce) |
| Validador que **recusa** novo 1º lugar fora do `tie_set` (regra 2 no servidor) | Passo 8 (`DeliverySerializer`); a 02 só entrega o `tie_set` pronto |
| Validar pelo tamanho de `candidatos`, e não com um `5` fixo | Passo 8 |
| `respondido_por` **fora** do payload do prompt (LGPD) | Passo 7 (`build_payload`) |
| Endpoint C3 para o carregamento em duas etapas | F2-09 / Passo 10 |

---

## 🌿 O Git Flow deste trabalho

```
main ─────●──────────────────────────────────────────●── v0.4.0
           \                                        /
develop     ●──────●──────●──────●──────●──────●───●  (release/0.4.0-pre-ia)
             \    / \    / \    / \    /
feature/...   00      01      02      03
```

| Branch | Para quê | Sai de | Volta para |
|---|---|---|---|
| `main` | O que roda na defesa. Só recebe release | — | — |
| `develop` | Integração: onde as features se juntam | `main` | `main` (via release) |
| `feature/*` | Uma spec = uma branch = um PR | `develop` | `develop` |
| `release/0.4.0-pre-ia` | Congela a fase, conferência final | `develop` | `main` **e** `develop` |

> [!note] Não precisa instalar o `git-flow`
> Os comandos abaixo são `git` puro. Se você tiver a extensão `git flow`, o equivalente de cada bloco está no comentário.

### 1. Criar a `develop` (uma vez só)

```bash
git switch main
git pull
git switch -c develop            # git flow init -d
git push -u origin develop
```

No GitHub, em **Settings → Branches**, deixe a `develop` como *default branch*. Assim todo PR já abre com a base certa.

### 2. Registrar as specs na `develop`

As cinco notas desta fase entram antes do código, para que cada PR possa apontar para a sua spec:

```bash
git switch develop
git add docs/specs/plano-pre-ia-git-flow.md docs/specs/spec-pre-ia-*.md
git commit -m "docs(specs): plano e specs da fase pre-IA"
git push
```

### 3. O ciclo de cada feature (repetir para 00, 01, 02 e 03)

```bash
git switch develop
git pull                                    # traz a feature anterior já mesclada
git switch -c feature/limpeza-pre-ia        # git flow feature start limpeza-pre-ia
# ... seguir a spec ...
cd backend && python manage.py test && python manage.py makemigrations --check --dry-run && cd ..
git add -A
git commit -m "chore: ..."                  # a mensagem está no fim de cada spec
git push -u origin feature/limpeza-pre-ia
gh pr create --base develop --fill
```

Depois que a CI ficar verde, faça o merge do PR no GitHub e apague a branch. Só então comece a próxima feature, a partir de uma `develop` atualizada (`git pull`).

> [!warning] Um PR por spec, sem juntar duas
> Se a 01 e a 02 forem no mesmo PR e a migração der problema, não dá para reverter uma sem a outra. Separadas, cada uma é reversível sozinha.

### 4. A release

Com as quatro mescladas na `develop`:

```bash
git switch develop && git pull
git switch -c release/0.4.0-pre-ia          # git flow release start 0.4.0-pre-ia
cd backend && python manage.py test && cd ..
git push -u origin release/0.4.0-pre-ia
gh pr create --base main --title "release: 0.4.0 pre-IA" --fill
```

Depois do merge na `main`, marque a versão e devolva a release para a `develop`:

```bash
git switch main && git pull
git tag -a v0.4.0 -m "Base pronta para a camada de IA"
git push origin v0.4.0
git switch develop && git merge main && git push
git push origin --delete release/0.4.0-pre-ia
```

> [!tip] A tag é o "antes" do capítulo comparativo
> `v0.4.0` fica sendo o último commit com a engine pura. Se a banca pedir para ver o sistema sem IA, é `git checkout v0.4.0`, e não um "desliga aqui" improvisado.

### 5. Na sua máquina, depois da release

A branch 01 cria migrações e a 03 cria uma tabela de cache:

```bash
cd backend
python manage.py migrate
python manage.py createcachetable
```

---

## ✅ Definition of Done da fase

- [ ] `develop` criada e como *default branch*
- [ ] As quatro features mescladas na `develop`, **na ordem 00 → 01 → 02 → 03**
- [ ] CI verde em cada PR
- [ ] `python manage.py test` com **86 testes**; o do fuso só falha se a sua máquina não tiver as tabelas de fuso
- [ ] Os três testes `C1`, `C2` e `C3` **continuam em `skip`**: eles são dos Passos 7, 8 e F2-09, e não desta fase
- [ ] `release/0.4.0-pre-ia` mesclada na `main`, tag `v0.4.0` publicada
- [ ] `migrate` e `createcachetable` rodados no banco local

## ▶️ Depois desta fase

O **Passo 7** do [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 plano da IA]], em `feature/llm-fake-provider`, saindo da `develop`.
