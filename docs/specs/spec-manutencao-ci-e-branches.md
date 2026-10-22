---
title: "Spec · Manutenção: Actions no Node 24, limpeza das branches e o fluxo do Git"
aliases: ["Manutenção do CI", "Node 24 nas Actions", "Limpeza de branches", "Fluxo do Git"]
tags: [tcc, spec, ci, github, git, manutencao]
status: proposto
projeto: TCC
branch: chore/actions-node24
criado: 2026-10-22
---

> [!info] Antes: [[spec-u3-cold-start|⚡ U3, cold start]] (mexe no mesmo `deploy.yml`, então aplique este depois) · Relacionados: [[spec-deploy-github-actions|🚀 Deploy automático]]

# 🧹 Manutenção: Actions, branches e fluxo

**Branch:** `chore/actions-node24`, saindo da `develop` **depois do U3**
**Risco:** baixo. Nada muda no sistema, só no CI e na organização do repositório.

> [!abstract] Três tarefas pequenas, independentes
> 1. **Atualizar as actions** que ainda rodam no Node 20 (os avisos amarelos em todo workflow).
> 2. **Apagar as branches velhas** do GitHub, guardando antes o que não foi mesclado.
> 3. **Decidir o fluxo do Git.** Cinco PRs seguidos foram para a `main`, e a `develop` precisou ser sincronizada à mão toda vez.

---

## 1️⃣ Actions no Node 24

### O aviso
Todo workflow mostra: *"Node.js 20 is deprecated… actions/checkout@v4, actions/setup-python@v5, azure/login@v2"*. Hoje é só um aviso. Quando o GitHub desligar o Node 20, esses passos **param de rodar**, e o deploy junto.

### As versões (conferidas em 22/10/2026 no `action.yml` de cada uma)

| Action | Hoje | Runtime | Nova | Runtime | O que muda para nós |
|---|---|:-:|---|:-:|---|
| `actions/checkout` | `v4` | node20 | **`v7`** | node24 | Nada. As mudanças são de `pull_request_target`, que não usamos |
| `actions/setup-python` | `v5` | node20 | **`v7`** | node24 | Nada. O input removido (`pip-install`) nunca foi usado |
| `azure/login` | `v2` | node20 | **`v3`** | node24 | Nada. A única mudança é o Node 24 |
| `azure/webapps-deploy` | `v3` | node24 | (fica) | node24 | Já está certo |

### As trocas

**`.github/workflows/test.yml`:**

```yaml
      - uses: actions/checkout@v7          # era v4
        with:
          ref: ${{ inputs.ref }}

      - uses: actions/setup-python@v7      # era v5
```

**`.github/workflows/deploy.yml`, no job `deploy`:**

```yaml
      - uses: actions/checkout@v7          # era v4
      ...
      - uses: azure/login@v3               # era v2
```

O `actions/setup-python@v7` do `deploy.yml` já entra pelo U3.

> [!warning] Só dá para validar rodando
> A versão de uma action não se testa localmente. O PR roda o `test.yml`, que confere o `checkout` e o `setup-python`. O `azure/login@v3` **só roda no deploy**, depois do merge na `main`. Se ele falhar, a produção não muda, porque o login vem antes do backup e da publicação. Para voltar atrás, basta reverter a linha para `@v2`.

### Pronto quando
- [ ] O PR roda os testes sem o aviso de Node 20
- [ ] O próximo deploy na `main` fica verde, sem o aviso

---

## 2️⃣ Branches velhas no GitHub

Conferido em 22/10:

| Branch | Situação | O que fazer |
|---|---|---|
| `deploy/azure` | Já mesclada na `main` | Apagar |
| `feature/llm-experimento` | Já mesclada | Apagar |
| `fix/sqlite-sob-carga` | Já mesclada (U1) | Apagar |
| `fix/deploy-github-actions` | Já mesclada (U2) | Apagar |
| `fix/producao-sqlite-e-deploy` | **Não mesclada**: tem o U4 (testes sem rede) e a spec dele | **Guardar numa tag** e depois apagar |

> [!important] Antes de apagar: fechar o PR #54 e guardar o U4
> O U4 foi adiado, e não descartado. Uma tag guarda os 3 commits para sempre, e a branch pode ir embora:
> ```bash
> git fetch origin
> git tag -a arquivo/u4-testes-sem-rede origin/fix/producao-sqlite-e-deploy -m "U4 adiado: testes sem rede (core/test_runner.py) e a spec"
> git push origin arquivo/u4-testes-sem-rede
> ```
> Para retomar um dia: `git switch -c feat/testes-sem-rede arquivo/u4-testes-sem-rede`.

**Apagar no GitHub** (depois do PR #54 fechado e da tag criada):

```bash
git push origin --delete deploy/azure feature/llm-experimento fix/sqlite-sob-carga fix/deploy-github-actions fix/producao-sqlite-e-deploy
```

**Limpar as cópias locais** de cada pessoa. O `-d` só apaga branches já mescladas, então é seguro:

```bash
git fetch --prune origin
git branch --merged origin/main | grep -vE "^\*|main|develop" | xargs -r git branch -d
```

### Pronto quando
- [ ] O PR #54 está fechado e a tag `arquivo/u4-testes-sem-rede` existe
- [ ] Em **Code → Branches**, só aparecem a `main`, a `develop` e as branches de trabalho abertas

---

## 3️⃣ O fluxo do Git: decisão do grupo

### O que aconteceu
Os PRs #40, #42, #43, #44, #45, #46, #47 e #57 foram abertos com base **`main`**, porque é a branch padrão do repositório. Depois de cada um, a `develop` ficou para trás e precisou ser sincronizada à mão. Por duas vezes, ela também foi **apagada** pelo "Delete branch" no merge.

**Desde o U2, cada merge na `main` vai para a produção**, depois dos testes. Por isso esta decisão importa mais agora.

### As duas opções

| | **A. `feature → main`** (GitHub Flow) | **B. `feature → develop → main`** (Git Flow) |
|---|---|---|
| Como funciona | Cada PR vai para a `main`, e o merge **publica** | Os PRs vão para a `develop`; de tempos em tempos, uma release `develop` → `main` publica |
| Combina com o que o grupo faz hoje | ✅ É o que já acontece na prática | ❌ Exige mudar o hábito |
| Risco na produção | Cada PR publica sozinho, e os testes e a revisão são a única barreira | Menor: dá para juntar e conferir várias mudanças antes de publicar |
| Trabalho de manutenção | Nenhum | Lembrar da base `develop` em todo PR |

**O que configurar em cada uma:**

| Configuração | A | B |
|---|---|---|
| Settings → General → **Default branch** | `main` (já está) | **`develop`** |
| `test.yml`, `push: branches` | Tirar a `develop` (os PRs já testam) | Fica como está |
| Branch `develop` | Apagar | Fica, protegida pelo ruleset |
| Ruleset | Só na `main` | `main` e `develop` (já está) |
| Settings → General → "Automatically delete head branches" | Pode ligar (apaga só as features) | **Deixar desligado** |

> [!tip] Recomendação: **A**, até a banca
> É o que o grupo já faz, e nada precisa ser lembrado. O deploy automático tem o que importa contra erro: os testes antes de publicar, o backup do banco e a conferência da versão no ar. O rollback é 1 clique (Run workflow com a tag anterior). Com 4 pessoas e poucas semanas até a banca, uma regra a menos para esquecer vale mais que uma etapa de *staging*.
>
> A **B** faz mais sentido se o projeto continuar depois do TCC, com mais gente e releases planejadas.

### Pronto quando
- [ ] A decisão registrada aqui, com a data
- [ ] As configurações da opção escolhida aplicadas
- [ ] O `README.md` (seção "Contribuindo") descrevendo o fluxo escolhido

---

## 📦 Commit e PR (só a parte 1 é código)

```bash
git switch develop && git pull
git switch -c chore/actions-node24
# ... troca as 4 linhas ...
git add .github/workflows/test.yml .github/workflows/deploy.yml
git commit -m "ci: actions no Node 24 (checkout v7, setup-python v7, azure/login v3)"
git push -u origin chore/actions-node24
```

As partes 2 e 3 não geram commit: são configurações e comandos no GitHub.
