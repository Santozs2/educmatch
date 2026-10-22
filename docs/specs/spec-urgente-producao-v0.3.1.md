---
title: "Spec urgente · Produção — SQLite sob carga, deploy automático e cold start (v0.3.1)"
aliases: ["Spec urgente produção", "v0.3.1", "Hotfix de produção", "Deploy pelo GitHub Actions", "SQLite locked"]
tags: [tcc, spec, producao, azure, deploy, sqlite, ci]
status: proposto
projeto: TCC
branch: fix/deploy-github-actions
criado: 2026-10-16
---

> [!info] Contexto: [[../apresentacao/ia|🤖 Camada de IA]] · [[../apresentacao/backend|⚙️ Backend, §6 deploy]] · Antes: release `v0.3` (PR #53) · Depois: EDU-203 (ligar a LLM no Azure)

# 🚨 Spec urgente: produção (v0.3.1)

> [!info] Atualização de 22/10/2026
> - **U1** entrou na `develop` e na `main` (`c530f76`, PR #55), sozinho.
> - **U2**: o código está na branch `fix/deploy-github-actions`. Faltam os passos do Azure e do GitHub e o primeiro deploy.
> - **U4** (testes sem rede) ficou **fora**, por decisão do grupo. O PR #54 deve ser fechado sem merge.
> - **U3** continua para depois da v0.3.1.

> [!abstract] O que esta spec resolve
> Ao preparar o EDU-203 (ligar a LLM no Azure), a conferência do App Service achou **três problemas**. Dois deles **bloqueiam** a ida da v0.3 para a produção:
>
> | # | Achado | Prioridade | Bloqueia a v0.3 no ar? |
> |:-:|---|:-:|:-:|
> | **U1** | SQLite perde gravações com várias pessoas ao mesmo tempo | **P0** | ✅ sim |
> | **U2** | O deploy pelo GitHub não funciona, e a produção está parada no código de 06/10 | **P0** | ✅ sim |
> | **U3** | O primeiro acesso depois de o site "dormir" leva cerca de 53 s | P1 | ❌ não, mas afeta a banca |
>
> **Ordem:** U1 e U2 numa branch só, depois release `v0.3.1`. O U2 faz o primeiro deploy automático já com o U1 dentro. O U3 vem em seguida.

> [!success] Conferido em 16/10/2026
> Tudo nesta spec foi **medido**: a configuração do App Service foi lida pelo `az` (sem alterar nada), os arquivos servidos em produção foram comparados com os commits, e o teste de carga rodou com o código da `main`.

---

## 🔍 0. O estado da produção hoje

| Item | Valor | Fonte |
|---|---|---|
| App Service | `educmatch-7249` · grupo `rg-educmatch` · Linux · Python 3.12 | `az webapp config show` |
| Plano | **F1 (Free)**: 60 min de CPU por dia, **sem Always On** | `az appservice plan list` |
| Banco | **SQLite** em `/home/data/educmatch.sqlite3` (disco de rede do App Service) | App Settings `DB_ENGINE` e `DB_NAME` |
| Origem do deploy | `ExternalGit`, `isManualIntegration: true`, branch `main` | `az webapp deployment source show` |
| Autenticação básica do SCM | **desligada** | `basicPublishingCredentialsPolicies/scm` |
| Último deploy | **06/10, às 19:32** | `az webapp log deployment list` |
| **Código no ar** | **`06baffc`** (PR #39): os 7 CSS/JS servidos têm o mesmo hash desse commit e diferem da `main` em `base.css` e `quiz.js` | Hash do `ManifestStaticFilesStorage` × `md5` dos arquivos no Git |
| LLM | `LLM_ENABLED=0`, `LLM_PROVIDER=fake` | App Settings |
| Página inicial, a frio | **HTTP 200 em 53,3 s** | `curl` |

> [!important] Consequência
> **Nada da camada de IA (PRs #40 a #53) está no ar.** E, como não há migração nova entre `06baffc` e a `main`, o próximo deploy **não mexe na estrutura do banco**: o risco do deploy em si é baixo.

---

## U1 · SQLite perde gravações sob carga (P0)

### O problema
A v0.3 colocou o gunicorn com **2 workers × 8 threads** (EDU-202): até 16 alunos sendo atendidos ao mesmo tempo. Com SQLite na configuração padrão, gravações simultâneas falham com `database is locked`.

Por que falham, e não só esperam: o Django abre as transações do SQLite em modo **`DEFERRED`**. Duas threads começam lendo e, quando as duas tentam gravar, o SQLite devolve `SQLITE_BUSY` **na hora**, sem respeitar o `timeout`, porque esperar travaria as duas.

### A evidência
O teste de carga simulou **30 alunos terminando o quiz juntos**, com o código da `main` (v0.3), **sem WAL**:

| SQLite | Cenário | Erros `locked` | Entregas da IA **perdidas** |
|---|---|:-:|:-:|
| Padrão (hoje) | Gemini ok | 60 nos dois cenários | **12 / 30** |
| Padrão (hoje) | Gemini fora, com pausa | | **18 / 30** |
| **`timeout=20` + `IMMEDIATE`** | Gemini ok | **0** | **0 / 30** |
| **`timeout=20` + `IMMEDIATE`** | Gemini fora, com pausa | **0** | **0 / 30** |

Em todos os casos o aluno recebeu **HTTP 302**, sem tela de erro. É justamente o perigo: depois do EDU-202, o erro da gravação virou uma **perda silenciosa**. O texto da IA não aparece e as métricas do experimento ficam erradas, sem nenhum aviso.

> [!warning] Por que não usar o WAL
> O WAL resolveria ainda melhor, mas usa memória compartilhada entre processos, e isso **não funciona em disco de rede**. O `/home` do App Service é um compartilhamento de rede (Azure Storage). Fica fora.

### A correção
`backend/core/settings.py`:

```python
# Com o gunicorn em threads (startup.sh), várias gravações chegam ao mesmo tempo.
# IMMEDIATE: a transação já pede a trava de escrita ao começar, e quem chega
# depois ESPERA a vez (até `timeout` segundos) em vez de falhar com "database is
# locked". Sem WAL: o /home do App Service é disco de rede.
SQLITE_OPTIONS = {"timeout": 20, "transaction_mode": "IMMEDIATE"}

if DB_ENGINE == "sqlite":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "OPTIONS": SQLITE_OPTIONS,
    }
```

`transaction_mode` existe desde o Django 5.1, e o projeto usa o 5.2.

**Teste** (`backend/core/tests.py`). A CI roda em MySQL, então o teste confere a **configuração**, e não o comportamento:

```python
class OpcoesDoSQLite(SimpleTestCase):
    """U1: com threads, o SQLite espera a vez em vez de perder a gravação."""

    def test_transacao_imediata_com_espera(self):
        self.assertEqual(settings.SQLITE_OPTIONS["transaction_mode"], "IMMEDIATE")
        self.assertGreaterEqual(settings.SQLITE_OPTIONS["timeout"], 10)
```

**Evidência de comportamento (manual, anexar ao PR):** rodar o teste de carga com `DB_ENGINE=sqlite` e confirmar **0 erros `locked` e 0 entregas perdidas**. O roteiro foi usado no EDU-202, mas ficou fora do repositório. Nesta spec ele passa a ser versionado em `backend/scripts/carga_turma.py`, para qualquer pessoa do grupo conseguir repetir a medição.

### Riscos que continuam
- **SQLite em disco de rede** continua sendo uma escolha frágil para produção. Com uma turma (cerca de 30 pessoas) é aceitável. A solução definitiva é o **Azure Database for MySQL** (o *Azure for Students* costuma incluir 12 meses do B1ms). Isso fica fora desta spec.
- As gravações ficam **em fila**: com 16 threads gravando, a última espera as outras. Cada gravação leva milissegundos, e o teste mostrou a mesma latência de antes (pior caso de 4,3 s contra 4,2 s).

### DoD do U1
- [x] `SQLITE_OPTIONS` no `settings.py`, usado quando `DB_ENGINE=sqlite`
- [x] Teste `OpcoesDoSQLite` passando na CI (`backend/core/tests.py`)
- [ ] Print do teste de carga no PR: 0 erros `locked` e 0 entregas perdidas

---

## U2 · Deploy automático pelo GitHub (P0)

### O problema
O App Service está como **External Git manual**:
1. **Não há aviso de push.** O Azure só puxa o código quando alguém clica em **Sync**.
2. **O repositório é privado.** O External Git tenta baixar o código sem credencial, e o `github.com/Santozs2/educmatch` responde 404 para quem não está logado.

Resultado: a equipe passou a subir **zip pelo CLI**. Isso é manual, depende de uma máquina específica, e foi assim que a produção ficou parada no `06baffc` sem ninguém perceber.

### A solução: GitHub Actions com identidade gerenciada (OIDC)

> [!info] Detalhada em [[spec-deploy-github-actions|🚀 Spec do deploy automático]]
> Aquela spec tem o código validado, a verificação de versão no ar, o backup automático e o rollback. Os trechos abaixo são o resumo original; em caso de diferença, vale a spec do deploy.

```
merge na main ──► testes (MySQL) ──✅──► deploy no App Service ──► smoke test (HTTP 200)
                                  └──❌──► não publica nada
```

**Por que OIDC, e não publish profile:**

| | Publish profile | **OIDC + identidade gerenciada** |
|---|---|---|
| Senha guardada no GitHub | Sim (XML com usuário e senha) | **Não**: o GitHub ganha um token de minutos a cada execução |
| Autenticação básica do SCM | Precisa religar (hoje está **desligada**) | Continua desligada |
| Quem pode publicar | Quem tiver o XML | **Só** os workflows deste repositório rodando na `main` |
| Permissão | O site inteiro | `Website Contributor` **só neste App Service** |

### Passo a passo no Azure (CLI, feito pelo dono da conta)
Pré-requisito: papel **Owner** na assinatura (já conferido).

```bash
export MSYS_NO_PATHCONV=1      # Git Bash no Windows: não converter /subscriptions/...
APP=educmatch-7249; RG=rg-educmatch; ID=id-educmatch-deploy
```

1. Desligar o External Git, que não funciona:
   ```bash
   az webapp deployment source delete -n $APP -g $RG
   ```
2. Criar a identidade:
   ```bash
   az identity create -n $ID -g $RG
   ```
3. Confiar **só** na `main` deste repositório:
   ```bash
   az identity federated-credential create --name github-main --identity-name $ID -g $RG \
     --issuer https://token.actions.githubusercontent.com \
     --subject repo:Santozs2/educmatch:ref:refs/heads/main \
     --audiences api://AzureADTokenExchange
   ```
4. Permissão de deploy **só neste App Service**:
   ```bash
   az role assignment create --role "Website Contributor" \
     --assignee-object-id "$(az identity show -n $ID -g $RG --query principalId -o tsv)" \
     --assignee-principal-type ServicePrincipal \
     --scope "$(az webapp show -n $APP -g $RG --query id -o tsv)"
   ```

### Passo a passo no GitHub
São três **variáveis** (não segredos: são identificadores, não senhas):

```bash
gh variable set AZURE_CLIENT_ID --body "$(az identity show -n $ID -g $RG --query clientId -o tsv)"
gh variable set AZURE_TENANT_ID --body "$(az account show --query tenantId -o tsv)"
gh variable set AZURE_SUBSCRIPTION_ID --body "$(az account show --query id -o tsv)"
```

> [!note] Por que não usar um *environment* do GitHub
> Environments com regras de proteção, em repositório **privado**, exigem GitHub Pro. Por isso a credencial confia na **branch `main`** (`ref:refs/heads/main`), e não num environment. Quando o grupo ativar o Pro (EDU-206), dá para migrar para `environment:producao` com aprovação manual.

### Os workflows

**`.github/workflows/test.yml`** ganha `workflow_call` e deixa de rodar sozinho no push da `main`, para os testes não rodarem duas vezes:

```yaml
on:
  pull_request:
  push:
    branches: [develop]
  workflow_call:
```

**`.github/workflows/deploy.yml`** (novo):

```yaml
name: deploy

on:
  push:
    branches: [main]
  workflow_dispatch:        # botão "Run workflow", para republicar a main

concurrency:
  group: deploy-producao
  cancel-in-progress: false # nunca interromper um deploy no meio

permissions:
  id-token: write           # OIDC
  contents: read

jobs:
  testes:
    uses: ./.github/workflows/test.yml

  deploy:
    needs: testes
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Pacote sem docs nem arquivos de desenvolvimento
        run: git archive --format=zip -o pacote.zip HEAD -- backend requirements.txt

      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

      - uses: azure/webapps-deploy@v3
        with:
          app-name: educmatch-7249
          package: pacote.zip   # o Oryx instala o requirements.txt no servidor (SCM_DO_BUILD_DURING_DEPLOYMENT=true)

      - name: Smoke test (o F1 pode levar ~1 min para acordar)
        run: |
          for tentativa in 1 2 3 4 5; do
            codigo=$(curl -s -o /dev/null -w "%{http_code}" -m 120 https://educmatch-7249.azurewebsites.net/)
            echo "tentativa $tentativa: HTTP $codigo"
            [ "$codigo" = "200" ] && exit 0
            sleep 20
          done
          exit 1
```

> [!warning] Conferir no primeiro deploy
> - O pacote reproduz o zip que hoje sobe pelo CLI: `backend/` + o `requirements.txt` da raiz, que aponta para `backend/requirements.txt`, como pede o Oryx. Se o zip manual levava algo a mais, incluir aqui.
> - **Faça backup do banco antes do primeiro deploy automático**, mesmo sem migração nova. É uma cópia do `/home/data/educmatch.sqlite3` pelo Kudu (`https://educmatch-7249.scm.azurewebsites.net` → *Debug console*), baixada para fora do Azure.

### O fluxo depois do U2
**Publicar = mesclar a release na `main`.** O zip pelo CLI deixa de existir. Para republicar sem mudança de código (por exemplo, depois de trocar uma App Setting), use o *Run workflow* em **Actions → deploy**.

### DoD do U2
- [ ] Os passos do Azure executados e o External Git desligado
- [ ] As 3 variáveis no GitHub
- [ ] O `test.yml` com `workflow_call` e o `deploy.yml` mesclados via PR
- [ ] Release `v0.3.1` mesclada na `main` → o workflow `deploy` verde
- [ ] **Produção servindo o código da `main`:** o hash do `quiz.js` servido igual ao `md5` do `backend/static/js/quiz.js` da `main` (hoje é `c656d6d66caa`, de 06/10)
- [ ] Backup do SQLite guardado antes do primeiro deploy

---

## U3 · Cold start de 53 s (P1)

### O problema
No F1 não existe *Always On*: o site "dorme" depois de uns 20 min sem acesso. Ao acordar, o `startup.sh` roda **toda vez**: `migrate`, `createcachetable`, **4 seeds** e `collectstatic`, e só então sobe o gunicorn. A primeira página levou **53,3 s**. Numa banca, isso é a tela branca na hora da demonstração.

### O que fazer
1. **Medir antes de mexer.** Colocar `date` entre os comandos do `startup.sh` e ler o *log stream* de um boot a frio. Sem a medição, não dá para saber se o tempo vai nos seeds ou no próprio boot do F1.
2. **Tirar do boot o que não precisa estar lá:**
   - **`collectstatic`** passa para o build. A App Setting `DISABLE_COLLECTSTATIC=true` desliga o do Oryx, e o `startup.sh` roda de novo a cada boot. Basta um dos dois, e o lugar certo é o build.
   - **Seeds** rodam só quando o catálogo está vazio, ou por uma flag `RODAR_SEEDS=1` nas App Settings, ligada no deploy. Eles são idempotentes, mas leem e regravam o catálogo inteiro a cada boot.
3. **No dia da banca:**
   - **Aquecer o site** 5 minutos antes de apresentar: abrir a página e responder o quiz uma vez. Isso também aquece o cache da IA.
   - **Opcional:** subir para o **B1** só na semana da banca, para ter Always On. O custo sai do crédito do *Azure for Students*. Voltar para o F1 depois.

### DoD do U3
- [ ] Boot a frio medido, com os tempos por etapa anotados aqui
- [ ] `collectstatic` e seeds fora do caminho de todo boot
- [ ] Boot a frio **abaixo de 20 s**, ou justificativa registrada se o F1 não permitir

---

## 🗓️ Ordem de execução

| # | O quê | Branch / onde | Quem |
|:-:|---|---|---|
| 1 | Backup do `educmatch.sqlite3` | Kudu | Dono da conta Azure |
| 2 | U1 (settings + teste) ✅ e U2 (workflows) | U1 já na `develop`; U2 em `fix/deploy-github-actions` → `develop` | Dev + revisão de outra pessoa (Infra) |
| 3 | Passos do Azure e variáveis do GitHub (U2) | `az` / `gh` | Dono da conta Azure |
| 4 | Release `v0.3.1` | `release/v0.3.1` → `main` → tag → back-merge | Dev |
| 5 | Conferir o deploy (DoD do U2) | Actions + `curl` | Dev |
| 6 | U3 | `fix/cold-start` → `develop` | Dev |
| 7 | **EDU-203**: ligar a LLM nas App Settings e aquecer o cache | Portal / `az` | Dono da conta Azure |

> [!tip] Por que `v0.3.1`, e não `v0.4`
> Pelo SemVer, o último número é para **correção**. A v0.3.1 não traz funcionalidade nova para o aluno: corrige o banco e o caminho até a produção.
