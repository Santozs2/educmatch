---
title: "Spec · Deploy automático pelo GitHub Actions (U2)"
aliases: ["Deploy automático", "U2", "Deploy pelo GitHub", "deploy.yml", "Pipeline de deploy"]
tags: [tcc, spec, deploy, azure, ci, github-actions, oidc]
status: codigo-pronto
projeto: TCC
branch: fix/deploy-github-actions
criado: 2026-10-19
---

> [!info] Origem: [[spec-urgente-producao-v0.3.1|🚨 Spec urgente da produção, seção U2]] · Junto na mesma release: U1 (SQLite) · Depois: EDU-203 (ligar a LLM no Azure)

> [!success] Atualização de 22/10/2026: o código da §6 está pronto
> Na branch `fix/deploy-github-actions`, saindo da `develop` (que já tem o U1, `c530f76`). O U4 (testes sem rede) **ficou de fora** por decisão do grupo. **218 testes verdes**; os dois workflows foram validados como YAML; o `git archive --add-virtual-file` gera o pacote com o `backend/VERSAO`; e um `VERSAO` de teste aparece no `<meta>` da página.
> **Uma diferença da §6.2:** o job do `test.yml` ganhou `timeout-minutes: 15`, porque sem isso um teste travado prende o runner por até 6 horas.
> **Falta:** as §4 e §5 (Azure e GitHub, pelo dono da conta), o backup manual e o primeiro deploy (§8).

# 🚀 Spec: deploy automático pelo GitHub Actions

> [!abstract] Em uma frase
> **Publicar passa a ser mesclar na `main`.** O GitHub roda os testes, faz backup do banco, envia o código para o Azure e **confere que o commit certo está no ar**. Se qualquer etapa falhar, a produção não muda.

> [!success] O que já foi validado (19/10/2026, sem tocar no Azure)
> Numa cópia da branch `fix/producao-sqlite-e-deploy`:
> - **Os dois workflows** são YAML válido, com os gatilhos e a dependência `deploy → testes` certos.
> - **Os testes passaram: 221** (os 219 da branch + 2 novos). A única falha é a do fuso do MySQL, porque a validação rodou em SQLite.
> - **O pacote:** `git archive` com `--add-virtual-file` gera 216 arquivos (455 KB), com `startup.sh`, os dois `requirements.txt`, o `VERSAO` dentro e **nenhum `.env`**.
> - **A conferência de versão** rodou contra a página inicial real, servida localmente. Com o commit certo, passou (exit 0). Com um commit diferente (a situação de hoje, produção parada), falhou com `::error::` (exit 1).
> - **O backup:** o JSON do comando sai certo, e a retenção, simulada num `/home` falso, mantém exatamente os 5 mais recentes.
>
> O que **só dá para validar no primeiro deploy de verdade** está na §8.

---

## 🧭 1. Por que isto existe

| Hoje | Problema |
|---|---|
| App Service como **External Git manual** | O GitHub não avisa o Azure de nada, e o repositório **privado** responde 404 para o External Git. O "Sync" não funciona |
| Deploy por **zip pelo CLI** | Manual, depende da máquina de uma pessoa e não roda os testes antes |
| **Ninguém sabe o que está no ar** | A produção ficou parada no `06baffc` (06/10) durante 3 releases. Só descobrimos comparando o hash dos arquivos CSS e JS |

**O ponto 3 é o mais grave.** Esta spec não só automatiza o deploy: ela faz o site **dizer qual commit está rodando** e faz o pipeline **conferir isso** antes de dar verde.

---

## 🗺️ 2. O pipeline

```
merge na main ─┐
               ├─► testes (MySQL, o mesmo test.yml dos PRs)
Run workflow ──┘         │
 (rollback)              ├─❌─► para aqui: nada muda na produção
                         ▼
                  pacote.zip  (backend/ + requirements.txt + backend/VERSAO = commit)
                         ▼
                  login no Azure por OIDC  (sem senha guardada)
                         ▼
                  backup do SQLite em /home/data/backups  (ficam os 5 últimos)
                         │─❌─► para aqui: sem backup, não publica
                         ▼
                  webapps-deploy  (o Oryx instala o requirements.txt no servidor)
                         ▼
                  conferência: o <meta name="versao"> da página == o commit?
                         ├─✅─► verde
                         └─❌─► vermelho, com a versão que está no ar
```

---

## ⚖️ 3. As decisões

| Decisão | Escolha | Por quê |
|---|---|---|
| Como entrar no Azure | **OIDC + identidade gerenciada** | Nenhuma senha no GitHub: cada execução ganha um token que vale minutos. A alternativa (*publish profile*) exigiria religar a autenticação básica do SCM, que hoje está **desligada** |
| Quem a identidade aceita | **Só a branch `main`** deste repositório (`repo:Santozs2/educmatch:ref:refs/heads/main`) | Um PR, uma branch de feature ou um fork **não conseguem** publicar |
| Permissão | `Website Contributor` **só no App Service** | Se a identidade vazar, o estrago fica restrito a este site |
| Testes antes do deploy | **O mesmo `test.yml`**, chamado como *workflow reutilizável* | Uma única definição dos testes. O deploy nunca roda uma versão diferente da que os PRs rodam |
| Como saber o que está no ar | **`<meta name="versao" content="<commit>">`** em toda página | O commit vai dentro do pacote (`backend/VERSAO`) e o `settings.py` lê esse arquivo. Fica visível no "exibir código-fonte" e é o que o pipeline confere |
| Backup | **No próprio Azure** (`/home/data/backups`), antes de cada deploy | O banco tem dados de alunos. **Não sai do Azure** (nada de artefato no GitHub), por causa da LGPD |
| Rollback | **Run workflow** com uma tag em `versao` | Volta para uma versão já testada em 1 clique, sem CLI |
| *Environment* do GitHub | **Não usar por enquanto** | Em repositório privado no plano gratuito, environments com regra de proteção exigem o GitHub Pro (EDU-206) |

---

## 🔐 4. Passos no Azure (uma vez, pelo dono da conta)

Pré-requisito: papel **Owner** na assinatura *Azure for Students* (conferido em 16/10).

```bash
export MSYS_NO_PATHCONV=1      # Git Bash no Windows: não converter /subscriptions/...
APP=educmatch-7249; RG=rg-educmatch; ID=id-educmatch-deploy
```

**1. Desligar o External Git**, que não funciona e confunde quem olha o portal:
```bash
az webapp deployment source delete -n $APP -g $RG
```

**2. Criar a identidade:**
```bash
az identity create -n $ID -g $RG
```

**3. Confiar só na `main` deste repositório:**
```bash
az identity federated-credential create --name github-main --identity-name $ID -g $RG \
  --issuer https://token.actions.githubusercontent.com \
  --subject repo:Santozs2/educmatch:ref:refs/heads/main \
  --audiences api://AzureADTokenExchange
```

**4. Dar permissão de deploy só neste App Service:**
```bash
az role assignment create --role "Website Contributor" \
  --assignee-object-id "$(az identity show -n $ID -g $RG --query principalId -o tsv)" \
  --assignee-principal-type ServicePrincipal \
  --scope "$(az webapp show -n $APP -g $RG --query id -o tsv)"
```

**Para conferir** (todos os comandos só leem):
```bash
az webapp deployment source show -n $APP -g $RG          # deve dar erro ou vir vazio
az identity federated-credential list --identity-name $ID -g $RG --query "[].subject" -o tsv
az role assignment list --assignee "$(az identity show -n $ID -g $RG --query principalId -o tsv)" --all --query "[].roleDefinitionName" -o tsv
```

---

## 🐙 5. Passos no GitHub (uma vez)

São três **variáveis**, e não segredos: são identificadores, sem valor para quem não tem acesso à identidade.

```bash
gh variable set AZURE_CLIENT_ID --body "$(az identity show -n $ID -g $RG --query clientId -o tsv)"
gh variable set AZURE_TENANT_ID --body "$(az account show --query tenantId -o tsv)"
gh variable set AZURE_SUBSCRIPTION_ID --body "$(az account show --query id -o tsv)"
```

---

## 🧩 6. O código

### 6.1 A versão no ar

**`backend/core/settings.py`**, no fim do arquivo:
```python
# O commit que está no ar. O deploy (deploy.yml) grava o arquivo VERSAO dentro
# do pacote; na máquina de quem desenvolve ele não existe e a versão é "dev".
_ARQUIVO_VERSAO = BASE_DIR / "VERSAO"
VERSAO = _ARQUIVO_VERSAO.read_text(encoding="utf-8").strip() if _ARQUIVO_VERSAO.exists() else "dev"
```

E no `TEMPLATES[0]["OPTIONS"]["context_processors"]`, logo depois de `'core.contexto.escola'`:
```python
                'core.contexto.versao',
```

**`backend/core/contexto.py`**:
```python
def versao(request):
    """O commit que está no ar, para o <meta name="versao"> do base.html."""
    return {"versao": settings.VERSAO}
```

**`backend/templates/base.html`**, no `<head>`, logo depois do `<meta charset>`:
```html
    <meta name="versao" content="{{ versao }}">
```

**`.gitignore`**:
```
backend/VERSAO
```

**Teste** (`backend/core/tests.py`; precisa de `from django.urls import reverse`):
```python
class VersaoNoAr(TestCase):
    """U2: a página diz qual commit está no ar. O deploy confere isso no fim."""

    @override_settings(VERSAO="abc1234")
    def test_pagina_inicial_mostra_o_commit(self):
        resposta = self.client.get(reverse("quiz-inicio"), HTTP_HOST="localhost")
        self.assertContains(resposta, '<meta name="versao" content="abc1234">', html=False)

    def test_sem_arquivo_de_versao_e_dev(self):
        self.assertEqual(settings.VERSAO, "dev")
```

### 6.2 `.github/workflows/test.yml`: vira reutilizável

Duas mudanças: ele passa a poder ser **chamado pelo deploy** e deixa de rodar sozinho no push da `main`, porque lá quem chama os testes é o deploy. Sem isso, os testes rodariam duas vezes.

```yaml
on:
  pull_request:
  push:
    branches: [develop]   # na main quem roda os testes é o deploy.yml, antes de publicar
  workflow_call:
    inputs:
      ref:
        description: "Commit, branch ou tag a testar (vazio = o do evento)"
        type: string
        default: ""
```

E no checkout, para o rollback testar a versão que vai publicar:
```yaml
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.ref }}
```

Nos PRs e no push da `develop`, o `inputs.ref` vem vazio e o checkout continua igual a hoje.

### 6.3 `.github/workflows/deploy.yml` (novo)

```yaml
name: deploy

# Publica no Azure App Service a cada merge na main, só se os testes passarem.
# Rollback: Actions -> deploy -> Run workflow, com uma tag em "versao" (ex.: v0.3.1).

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      versao:
        description: "Tag ou commit a publicar (vazio = a main de agora)"
        type: string
        default: ""

concurrency:
  group: deploy-producao
  cancel-in-progress: false   # nunca interromper um deploy no meio

permissions:
  id-token: write   # login no Azure por OIDC, sem senha guardada
  contents: read

env:
  APP: educmatch-7249
  SITE: https://educmatch-7249.azurewebsites.net

jobs:
  testes:
    uses: ./.github/workflows/test.yml
    with:
      ref: ${{ inputs.versao }}

  deploy:
    needs: testes
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.versao }}

      - name: Pacote com o commit dentro (backend/VERSAO)
        run: |
          COMMIT=$(git rev-parse --short HEAD)
          echo "COMMIT=$COMMIT" >> "$GITHUB_ENV"
          git archive --format=zip -o pacote.zip \
            --add-virtual-file=backend/VERSAO:$COMMIT \
            HEAD -- backend requirements.txt
          unzip -l pacote.zip | tail -1

      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

      - name: Backup do banco antes de publicar (fica no próprio Azure)
        run: |
          token=$(az account get-access-token --query accessToken -o tsv)
          comando="mkdir -p data/backups \
            && cp data/educmatch.sqlite3 data/backups/educmatch-$(date -u +%Y%m%d-%H%M)-${COMMIT}.sqlite3 \
            && ls -1t data/backups/*.sqlite3 | tail -n +6 | xargs -r rm -f \
            && ls -1t data/backups"
          resposta=$(curl -sS -f -X POST "https://${APP}.scm.azurewebsites.net/api/command" \
            -H "Authorization: Bearer ${token}" -H "Content-Type: application/json" \
            -d "$(jq -n --arg c "$comando" '{command: ("bash -c \"" + $c + "\""), dir: "/home"}')")
          echo "$resposta" | jq -r '.Output, .Error'
          [ "$(echo "$resposta" | jq -r '.ExitCode')" = "0" ]

      - uses: azure/webapps-deploy@v3
        with:
          app-name: ${{ env.APP }}
          package: pacote.zip   # o Oryx instala o requirements.txt no servidor (SCM_DO_BUILD_DURING_DEPLOYMENT=true)

      - name: Conferir que o commit certo está no ar
        run: |
          for tentativa in $(seq 1 10); do
            versao=$(curl -s -m 120 "${SITE}/" | grep -o 'name="versao" content="[^"]*"' | cut -d'"' -f4)
            echo "tentativa ${tentativa}: no ar=${versao:-?} esperado=${COMMIT}"
            [ "$versao" = "$COMMIT" ] && exit 0
            sleep 30
          done
          echo "::error::A produção não está servindo ${COMMIT}"
          exit 1
```

> [!note] Por que a conferência espera até ~25 minutos
> Depois do deploy, o App Service reinicia e o `startup.sh` roda migrate, os seeds e o collectstatic. No F1, isso levou **53 s** numa medição a frio. São 10 tentativas, cada uma com até 120 s de `curl` mais 30 s de espera, o que cobre um build lento do Oryx sem deixar o job pendurado para sempre (`timeout-minutes: 30`).

---

## ⏪ 7. Rollback

**Quando:** o deploy ficou verde, mas algo quebrou no uso real.

1. GitHub → **Actions** → **deploy** → **Run workflow** (deixe a branch `main` selecionada).
2. Em **versao**, coloque a **tag anterior**, por exemplo `v0.3.1`.
3. O pipeline testa essa versão, faz backup e publica. A conferência só fica verde quando ela estiver no ar.

> [!warning] Rollback do código não desfaz o banco
> Se a versão nova tiver aplicado uma **migração**, voltar o código não volta a estrutura do banco. Nesse caso, restaure também o backup mais recente de antes do deploy, que fica em `/home/data/backups/` (Kudu → *Debug console*), com o site parado. A v0.3.1 **não tem migração nova**.

> [!tip] O plano B continua existindo
> Se o próprio pipeline estiver quebrado (o Azure mudou alguma coisa, ou a identidade foi apagada), o deploy por **zip pelo CLI** continua funcionando como antes. Ele só deixa de ser o caminho normal.

---

## 🧪 8. O que só se valida no primeiro deploy

Não dá para testar sem mexer na produção. Fica como checklist da primeira execução:

| Item | Risco | Se falhar |
|---|---|---|
| **Kudu `/api/command` aceitar o token do Azure AD** (a autenticação básica está desligada) | Médio | O pipeline **para antes de publicar**, então a produção não muda. Alternativa: fazer o backup com `az webapp ssh`/Kudu pelo portal e comentar o passo até investigar |
| **`Website Contributor` bastar para o Kudu e o deploy** | Baixo | Mesmo efeito: para no backup ou no deploy |
| **`cp` do SQLite com o site no ar** | Baixo: o deploy dura minutos e quase ninguém grava nesse intervalo | Um backup inconsistente. Para não depender disso, faça um backup manual antes da primeira execução |
| **O Oryx montar o pacote** como montava o zip do CLI | Baixo: o pacote tem os mesmos arquivos | A conferência fica vermelha e mostra a versão antiga no ar |
| **Tempo do build no F1** (60 min de CPU por dia) | Baixo | O pacote é pequeno; o `pip install` é o maior gasto |

**Recomendação:** antes de mesclar a release, **faça um backup manual** do `/home/data/educmatch.sqlite3` pelo Kudu (portal → App Service → *Advanced Tools* → *Go* → *Debug console* → `data/`), baixado para fora do Azure. É a rede de proteção, caso o primeiro backup automático não funcione.

---

## ✅ 9. Critérios de aceite (DoD)

**Código (PR para a `develop`):**
- [ ] `VERSAO` no `settings.py`, `versao` no `contexto.py` e o `<meta>` no `base.html`
- [ ] `backend/VERSAO` no `.gitignore`
- [ ] Testes `VersaoNoAr` passando
- [ ] `test.yml` com `workflow_call` e sem a `main` no `push`
- [ ] `deploy.yml` criado
- [ ] **O PR roda os testes normalmente** (o `pull_request` do `test.yml` continua funcionando)

**Infra (dono da conta, antes da release):**
- [ ] Os passos da §4 executados e conferidos
- [ ] As 3 variáveis da §5 no GitHub
- [ ] Backup manual do SQLite baixado

**Primeiro deploy (release `v0.3.1` → `main`):**
- [ ] O workflow **deploy** verde, com os 3 jobs (testes, deploy e conferência)
- [ ] O log da conferência mostra `no ar=<commit da v0.3.1>`
- [ ] O backup aparece no log (`ls -1t data/backups`)
- [ ] Abrindo o site e usando "exibir código-fonte", o `<meta name="versao">` tem o commit da `main`
- [ ] **O EDU-203 está liberado:** com a v0.3.1 no ar, dá para ligar a LLM nas App Settings

---

## 🗓️ 10. Ordem

| # | Passo | Quem |
|:-:|---|---|
| 1 | Código da §6 na branch `fix/deploy-github-actions` → PR para a `develop` ✅ código pronto | Dev + revisão de Infra |
| 2 | Passos da §4 e §5 | Dono da conta Azure |
| 3 | Backup manual do SQLite | Dono da conta Azure |
| 4 | Release `v0.3.1` → `main` (o merge dispara o primeiro deploy) | Dev |
| 5 | Checklist da §8 e DoD do primeiro deploy | Dev |
| 6 | Tag `v0.3.1`, back-merge `main` → `develop` | Dev |
