---
title: "Guia · Deploy automático com GitHub Actions (e como levar para qualquer projeto)"
aliases: ["Deploy automático", "CI/CD", "GitHub Actions + Azure", "OIDC"]
tags: [guia, deploy, ci-cd, github-actions, azure, oidc]
status: pronto
criado: 2026-10-22
---

> [!info] No EducMatch: [[../specs/spec-deploy-github-actions|🚀 Spec do deploy]] · `.github/workflows/deploy.yml` · `.github/workflows/test.yml`

# 🚀 Deploy automático: como funciona e como levar para qualquer projeto

> [!abstract] O que este guia é
> A explicação do deploy automático do EducMatch, em duas partes:
> 1. **Como ele funciona aqui**, peça por peça.
> 2. **Uma receita para qualquer projeto**, com os passos genéricos, o modelo de workflow e os erros que nós já cometemos, para você não repetir.

---

## 🎓 1. Os conceitos (em 2 minutos)

| Termo | O que é, em português |
|---|---|
| **Deploy** | Colocar uma versão do código no ar, no servidor que as pessoas acessam |
| **CI** (integração contínua) | Rodar os testes **automaticamente** a cada mudança |
| **CD** (entrega contínua) | Publicar **automaticamente** quando os testes passam |
| **GitHub Actions** | O "robô" do GitHub que executa as tarefas descritas em arquivos `.yml` dentro de `.github/workflows/` |
| **Workflow** | Um desses arquivos: *quando* rodar (gatilho) e *o que* fazer (jobs e passos) |
| **OIDC** | O jeito de o GitHub **provar quem é** para a nuvem **sem senha guardada**: a cada execução ele ganha um token que vale alguns minutos |
| **Identidade gerenciada** | Uma "conta de robô" na nuvem. O GitHub entra no Azure como ela |

### Os dois jeitos de fazer deploy

```
PULL  (o servidor busca o código)          PUSH  (o GitHub entrega o código)
┌────────┐   "tem novidade?"   ┌──────┐     ┌──────┐   testes ✓ → pacote   ┌────────┐
│ Azure  │ ──────────────────► │GitHub│     │GitHub│ ─────────────────────► │ Azure  │
└────────┘   (precisa de acesso)└──────┘     └──────┘   (login sem senha)    └────────┘
```

O EducMatch começou no **pull** (o "External Git" do Azure). Com o repositório privado, o Azure não tinha acesso, o *sync* falhava em silêncio, e a produção ficou **três releases parada** sem ninguém perceber. O **push** resolve isso: quem tem o código (o GitHub) é quem entrega, e só depois de os testes passarem.

---

## 🧩 2. Como funciona no EducMatch

```
merge na main ──► GitHub Actions: deploy.yml
                    │
                    ├─ job "testes"  ── o MESMO test.yml dos PRs (MySQL, 218+ testes)
                    │     └─ falhou? para aqui. A produção não muda
                    │
                    └─ job "deploy"
                          1. pacote.zip  = backend/ + requirements.txt + backend/VERSAO (o commit)
                          2. login no Azure por OIDC (sem senha)
                          3. backup do SQLite no próprio Azure (guarda os 5 últimos)
                          4. publica o pacote no App Service
                          5. abre o site e confere: <meta name="versao"> == commit?
                                ├─ sim → ✅ verde
                                └─ não → ❌ vermelho, mostrando a versão que está no ar
```

### As peças, e por que cada uma existe

| Peça | Onde | Por que existe |
|---|---|---|
| **Testes antes de publicar** | `deploy.yml` chama o `test.yml` (*workflow reutilizável*) | Uma única definição de testes. O deploy nunca publica algo que os PRs não testariam |
| **O commit dentro do pacote** | `backend/VERSAO`, gravado pelo `git archive --add-virtual-file` | Para o sistema **saber** qual versão é |
| **`<meta name="versao">` em toda página** | `settings.VERSAO` → `contexto.py` → `base.html` | Para **qualquer pessoa** ver a versão no ar (em "Exibir código-fonte") e para o pipeline conferir |
| **Login por OIDC** | `azure/login` + a identidade `id-educmatch-deploy` | Nenhuma senha no GitHub. A identidade **só** aceita execuções da branch `main` deste repositório |
| **Permissão mínima** | `Website Contributor` **só no App Service** | Se algo vazar, o estrago fica restrito a este site |
| **Backup antes de publicar** | Passo com `curl` no Kudu (`/api/command`) | O banco tem dados de alunos. Se o backup falhar, o pipeline **para antes** de publicar |
| **Conferência no fim** | `curl` no site, até 10 tentativas | "Publicou" não é o mesmo que "está no ar". O verde só sai quando o site **responde com o commit certo** |
| **Rollback** | Actions → deploy → **Run workflow**, com uma tag em "versao" | Volta para uma versão testada em 1 clique |
| **Fila** | `concurrency: deploy-producao` | Dois merges seguidos não publicam ao mesmo tempo |

---

## 🛠️ 3. Receita para qualquer projeto

Os passos são sempre os mesmos. Muda só **onde** o projeto roda (a nuvem) e **como** ele é empacotado (a linguagem).

### Passo 0: os pré-requisitos

- [ ] O projeto tem **testes** que rodam com um comando (`python manage.py test`, `npm test`, `pytest`…)
- [ ] O projeto **lê a configuração de variáveis de ambiente** (banco, chaves, `DEBUG`), e não de arquivos dentro do código
- [ ] Já existe um servidor na nuvem (o App Service, no caso do Azure), criado uma vez pelo portal ou pelo CLI
- [ ] Você tem papel de **Owner** (ou *User Access Administrator*) na assinatura, para criar a identidade e dar permissão

### Passo 1: o workflow de testes, reutilizável

`.github/workflows/test.yml`:

```yaml
name: testes

on:
  pull_request:
  workflow_call:              # permite o deploy chamar este mesmo arquivo
    inputs:
      ref:
        type: string
        default: ""

jobs:
  testes:
    runs-on: ubuntu-latest
    timeout-minutes: 15       # sem isto, um teste travado prende o runner por até 6 h
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ inputs.ref }}
      - uses: actions/setup-python@v7          # ou setup-node, setup-java...
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt   # instalar dependências
      - run: python -m pytest                  # o comando de testes do seu projeto
```

> [!tip] Banco de dados nos testes
> Se os testes precisam de MySQL ou Postgres, use `services:` no job, como faz o `test.yml` do EducMatch. O GitHub sobe o banco num contêiner só para a execução.

### Passo 2: a identidade na nuvem (Azure, uma vez)

```bash
export MSYS_NO_PATHCONV=1                  # só no Git Bash do Windows
APP=nome-do-app-service; RG=nome-do-grupo; ID=id-deploy-$APP
REPO=usuario/repositorio

# 1. a "conta de robô"
az identity create -n $ID -g $RG

# 2. ela confia SÓ na main deste repositório (veja o aviso abaixo sobre o formato)
az identity federated-credential create --name github-main --identity-name $ID -g $RG \
  --issuer https://token.actions.githubusercontent.com \
  --subject "repo:$REPO:ref:refs/heads/main" \
  --audiences api://AzureADTokenExchange

# 3. permissão de publicar SÓ neste site
az role assignment create --role "Website Contributor" \
  --assignee-object-id "$(az identity show -n $ID -g $RG --query principalId -o tsv)" \
  --assignee-principal-type ServicePrincipal \
  --scope "$(az webapp show -n $APP -g $RG --query id -o tsv)"

# 4. os 3 valores para o GitHub
az identity show -n $ID -g $RG --query clientId -o tsv      # AZURE_CLIENT_ID
az account show --query tenantId -o tsv                      # AZURE_TENANT_ID
az account show --query id -o tsv                            # AZURE_SUBSCRIPTION_ID
```

> [!danger] O erro que nós cometemos: o formato do *subject*
> Em 2026, o GitHub passou a mandar o *subject* com os **IDs numéricos** da conta e do repositório:
> `repo:Santozs2@203097652/educmatch@1380343423:ref:refs/heads/main`
> Se a credencial for criada no formato antigo (`repo:Santozs2/educmatch:...`), o login falha com **`AADSTS700213: No matching federated identity record found for presented assertion subject '...'`**.
> **A solução mais simples:** rode o deploy uma vez, copie o *subject* **exato** da mensagem de erro e crie uma credencial com ele. Pode existir mais de uma credencial na mesma identidade.

> [!note] Se o projeto também desativar o deploy antigo
> Se o App Service estiver ligado a um "External Git" ou a outro *deployment source*, desligue com `az webapp deployment source delete -n $APP -g $RG`. Dois caminhos de deploy confundem quem olha o portal.

### Passo 3: as variáveis no GitHub (uma vez)

Repositório → **Settings → Secrets and variables → Actions → aba _Variables_** → *New repository variable*:

| Name | Valor |
|---|---|
| `AZURE_CLIENT_ID` | O do passo 2.4 |
| `AZURE_TENANT_ID` | O do passo 2.4 |
| `AZURE_SUBSCRIPTION_ID` | O do passo 2.4 |

> [!warning] Variables, não Secrets
> Com OIDC, esses valores **não são senhas**: sozinhos, não dão acesso a nada. O workflow lê `vars.AZURE_CLIENT_ID`. Se forem criadas na aba *Secrets*, ou dentro de um *Environment*, chegam **vazias**, e o login falha com *"Not all values are present. Ensure 'client-id' and 'tenant-id' are supplied"*. Foi o nosso primeiro erro.

### Passo 4: o workflow de deploy

`.github/workflows/deploy.yml`, o modelo mínimo (sem o backup e sem a versão no ar, que estão no passo 5):

```yaml
name: deploy

on:
  push:
    branches: [main]
  workflow_dispatch:            # botão "Run workflow", usado também para rollback
    inputs:
      versao:
        type: string
        default: ""

concurrency:
  group: deploy-producao
  cancel-in-progress: false     # nunca interromper um deploy no meio

permissions:
  id-token: write               # obrigatório para o OIDC
  contents: read

jobs:
  testes:
    uses: ./.github/workflows/test.yml
    with:
      ref: ${{ inputs.versao }}

  deploy:
    needs: testes               # só publica se os testes passarem
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ inputs.versao }}

      - name: Pacote
        run: git archive --format=zip -o pacote.zip HEAD

      - uses: azure/login@v3
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

      - uses: azure/webapps-deploy@v3
        with:
          app-name: nome-do-app-service
          package: pacote.zip
```

> [!note] O `git archive` empacota só o que está **commitado**
> Arquivos ignorados pelo Git (a `.venv`, o `.env`, o `node_modules`) ficam de fora sozinhos. Para incluir algo gerado no build, como os estáticos do Django ou o `dist/` do front, acrescente ao zip **depois**: `zip -qr pacote.zip pasta/gerada`.

### Passo 5: os extras que valem a pena (os que salvaram o EducMatch)

**5.1 A versão no ar.** Grave o commit dentro do pacote e mostre-o no site:

```yaml
      - name: Pacote com o commit dentro
        run: |
          COMMIT=$(git rev-parse --short HEAD)
          echo "COMMIT=$COMMIT" >> "$GITHUB_ENV"
          git archive --format=zip -o pacote.zip --add-virtual-file=VERSAO:$COMMIT HEAD
```

O sistema lê o arquivo `VERSAO` (ou `"dev"`, se ele não existir) e coloca `<meta name="versao" content="...">` no HTML. Qualquer linguagem faz isso em 3 linhas.

**5.2 A conferência no fim.** Só fica verde quando o site responde com o commit certo:

```yaml
      - name: Conferir que o commit certo está no ar
        run: |
          for i in $(seq 1 10); do
            v=$(curl -s -m 120 https://SEU-SITE/ | grep -o 'name="versao" content="[^"]*"' | cut -d'"' -f4)
            echo "tentativa $i: no ar=${v:-?} esperado=$COMMIT"
            [ "$v" = "$COMMIT" ] && exit 0
            sleep 30
          done
          exit 1
```

**5.3 Backup antes de publicar,** se o banco mora no próprio servidor (como o SQLite). Veja o passo "Backup do banco" no `deploy.yml` do EducMatch. Com um banco gerenciado (Azure Database, RDS, Cloud SQL), use o backup automático do próprio serviço.

**5.4 Trabalho pesado no build, e não no boot.** Tudo o que **não muda entre um boot e outro** (compilar o CSS e o JS, o `collectstatic`, o `npm run build`) deve rodar no GitHub, e não no `startup` do servidor. No EducMatch, o `collectstatic` no boot custava 11 s cada vez que o site acordava (ver [[../specs/spec-u3-cold-start|⚡ U3]]).

### Passo 6: o primeiro deploy

1. **Faça um backup manual** do banco de produção. É a rede de proteção se algo der errado na primeira vez.
2. Mescle na `main` → **Actions → deploy**.
3. Se falhar, olhe o **passo vermelho** e consulte a tabela da §4.
4. Confirme com os próprios olhos: site → **Exibir código-fonte** → `<meta name="versao">`.

---

## 🧯 4. Quando dá vermelho: os erros que já vimos

| Onde parou | Mensagem | Causa | Solução |
|---|---|---|---|
| `azure/login` | *Not all values are present. Ensure 'client-id' and 'tenant-id' are supplied* | Variáveis ausentes, criadas como **Secrets** ou num **Environment** | Criar na aba **Variables** do repositório |
| `azure/login` | **`AADSTS700213`** *No matching federated identity record found for presented assertion subject '…'* | O *subject* da credencial não é o que o GitHub manda | Criar uma credencial com o *subject* **exato** da mensagem |
| `azure/login` | *AADSTS70021* *No matching federated identity record found* | `--issuer` ou `--audiences` da credencial errados | Conferir `https://token.actions.githubusercontent.com` e `api://AzureADTokenExchange`, e recriar a credencial |
| Backup / Kudu | HTTP 401 ou 403 | A identidade sem permissão no App Service | Conferir o `Website Contributor` no escopo do site |
| `webapps-deploy` | Erro de build do Oryx | Dependência que não instala no servidor | Ver o log do build no portal (Deployment Center) |
| Conferência | `no ar=<versão antiga>` | O site ainda reiniciando, ou o build falhou em silêncio | Esperar e rodar de novo; ver o *log stream* do App Service |
| Aviso amarelo | *Node.js 20 is deprecated* | Actions numa versão antiga | Subir para a major mais nova (`checkout@v7`, `azure/login@v3`…) |

> [!tip] Como ver o erro completo
> Actions → o workflow → a execução → o **job** vermelho → o **passo** com ❌. As linhas em vermelho no fim do passo dizem o motivo. A seção *Annotations*, na página da execução, resume os erros de todos os jobs.

---

## ☁️ 5. E em outras nuvens?

A ideia é a mesma: **identidade federada (OIDC) + permissão mínima + uma action de deploy**. Mudam os nomes:

| | Azure | AWS | Google Cloud |
|---|---|---|---|
| "Conta de robô" | Identidade gerenciada | **IAM Role** | **Service Account** |
| Confiar no GitHub | Credencial federada (*subject*) | **OIDC provider** `token.actions.githubusercontent.com` + condição no `sub` da *trust policy* | **Workload Identity Federation** (pool + provider) |
| Action de login | `azure/login` | `aws-actions/configure-aws-credentials` (com `role-to-assume`) | `google-github-actions/auth` |
| Deploy típico | `azure/webapps-deploy` | `aws deploy`, `aws s3 sync`, App Runner, Elastic Beanstalk | `gcloud run deploy`, App Engine |

> [!note] Hospedagens "fáceis" (Vercel, Render, Railway, Fly.io)
> Muitas fazem o deploy sozinhas quando você conecta o repositório (o modelo **pull**, mas com acesso autorizado pelo GitHub). É mais simples, porém você perde o controle de "**só publicar se os testes passarem**". A boa prática é ligar a opção que espera as *checks* do GitHub ficarem verdes antes de publicar, quando a plataforma tiver.

---

## ✅ 6. Checklist para levar para outro projeto

- [ ] Testes rodam com um comando, e o `test.yml` roda em todo PR
- [ ] A configuração vem de variáveis de ambiente (nada de senha no código)
- [ ] Identidade na nuvem + credencial federada (com o *subject* **exato**) + permissão **só no recurso**
- [ ] As 3 variáveis no GitHub, na aba **Variables**
- [ ] `deploy.yml` com `needs: testes`, `permissions: id-token: write` e `concurrency`
- [ ] O commit dentro do pacote e visível no site
- [ ] A conferência da versão no fim do deploy
- [ ] Backup antes de publicar (se o banco mora no servidor)
- [ ] Trabalho pesado no build, e não no boot
- [ ] Um backup manual antes do **primeiro** deploy
- [ ] O rollback testado ao menos uma vez (Run workflow com uma tag anterior)
