---
title: "Spec pré-IA 00 — limpeza antes de mexer no motor"
aliases: ["PRE-00", "Limpeza pré-IA"]
tags: [tcc, spec, limpeza, refactor, ci]
status: proposto
projeto: TCC
branch: feature/limpeza-pre-ia
criado: 2026-09-30
---

> [!info] Plano: [[plano-pre-ia-git-flow|🚧 Pré-IA e Git Flow]] · Próxima: [[spec-pre-ia-01-rank-final|01 — rank final]]

# 🧹 PRE-00: limpeza

**Branch:** `feature/limpeza-pre-ia`, saindo da `develop`
**Risco:** baixo. Nenhuma migração, nenhum comportamento muda.
**Testes ao final:** 74 (os mesmos de hoje)

> [!abstract] Por que esta vem primeiro
> A função que a view chama se chama `recomedacao`, com um "n" faltando. A 01 e a 02 editam o `engine.py` e o `web_views.py`. Renomear agora, sozinho, evita que o rename apareça misturado com a migração no diff das próximas branches. Isso também deixa o PR da 01 mais fácil de revisar.

---

## 1️⃣ `recomedacao` → `recomendar`

> [!question] Por que `recomendar` e não só corrigir para `recomendacao`
> `recomendacao` colide com o model `Recomendacao` e com o parâmetro de `areas_da_recomendacao(recomendacao)` no `web_views.py`. Um verbo diz o que a função **faz**: ela calcula e grava. E não se confunde com a linha do banco.

São 9 ocorrências em 5 arquivos:

| Arquivo | Linha | Troca |
|---|---|---|
| `quiz/engine.py` | 100 | `def recomedacao(` → `def recomendar(` |
| `quiz/web_views.py` | 9 | `from quiz.engine import recomedacao` → `recomendar` |
| `quiz/web_views.py` | 100 | `recomedacao(tentativa)` → `recomendar(tentativa)` |
| `quiz/web_views.py` | 129 e 138 | variável `recomedacoes` → `recomendacoes` |
| `quiz/tests/base.py` | 50 e 60 | import e chamada |
| `quiz/tests/test_motor.py` | 4 e 29 | import e chamada |
| `quiz/tests/test_resultado.py` | 4 e 29 | import e chamada |

Use o **Replace in Files** do VS Code (`Ctrl+Shift+H`) com *Match Case* ligado, restrito à pasta `backend/`:
1. `recomedacoes` → `recomendacoes` (**primeiro este**, senão o próximo o transforma em `recomendares`)
2. `recomedacao` → `recomendar`

Confira que não sobrou nada:

```bash
grep -rn "recomedac" backend --include=*.py --exclude-dir=.venv
```

Tem de sair vazio.

> [!warning] Não use `sed` no Windows para isso
> Os arquivos estão com quebra de linha CRLF, e o `sed` do Git Bash grava LF. O diff vira "arquivo inteiro mudou" e o revisor não consegue ver as 9 linhas. O VS Code preserva o CRLF.

---

## 2️⃣ `banda()` e os cortes **ficam**: só ganham uma docstring

> [!important] Decisão do grupo (2026-09-30): nada do motor sai
> `banda()`, `CORTE_MINIMO` e `CORTE_MAXIMO` **continuam no `engine.py`**. O motor tem de funcionar inteiro, sozinho, para o caso de a IA falhar. Hoje ninguém chama `banda()`, mas ela mede uma coisa que a `confianca()` não mede. Ela vai ser usada no fallback e no tom do prompt (v2).

As duas "bandas" medem coisas diferentes, e a docstring deixa isso explícito para ninguém confundir no Passo 8:

| Função | Mede | Pergunta que responde |
|---|---|---|
| `banda(afinidade)` | o **nível** da afinidade de um curso (cortes 0,5 e 0,8) | "Este curso combina muito ou pouco com o aluno?" |
| `confianca(ranking)` | a **separação** entre o 1º e o 2º | "O 1º lugar ganhou com folga ou empatou?" |

Troque só a função, deixando as constantes como estão:

```python
def banda(afinidade):
    """Nível da afinidade de UM curso: baixo (< 0,5), medio (< 0,8) ou alto.

    Não confundir com confianca(), que mede a separação entre o 1º e o 2º.
    Fica no motor para o fallback e para o tom do prompt: um 1º lugar com
    afinidade "baixo" não pode ser apresentado como "combina muito com você",
    venha o texto da LLM ou da engine.
    """
    if afinidade < CORTE_MINIMO:
        return "baixo"
    elif afinidade < CORTE_MAXIMO:
        return "medio"
    else:
        return "alto"
```

> [!tip] Onde ela entra depois
> - **Passo 7:** o `build_payload` envia `"banda": banda(score)` de cada candidato. A LLM recebe o nível pronto e não precisa interpretar o cosseno.
> - **Passo 10 / fallback:** quando a IA falhar, a tela da engine pode usar a mesma `banda()` para calibrar a frase do destaque.

---

## 3️⃣ Arquivos que não deviam estar no Git

```bash
git rm backend/out.txt
git rm backend/accounts/templates/accounts/perfil.html
git rm backend/quiz/tests/test_recomendacao.py
```

| Arquivo | Por quê |
|---|---|
| `out.txt` | Saída de um `manage.py test` com erro de sintaxe no comando. É lixo de depuração |
| `accounts/perfil.html` | 0 bytes e nenhuma view usa. O perfil real é `templates/quiz/aluno_perfil.html` |
| `quiz/tests/test_recomendacao.py` | 0 bytes. Os testes do motor estão em `test_motor.py` e `test_engine_puro.py` |

> [!caution] `_celula.html` e `_barra.html` **não** são vazios
> O `wc -l` mostra 0 linhas neles porque não têm quebra de linha no final, mas têm 111 e 207 bytes e são usados pelo painel e pelo resultado. **Não apague.**

---

## 4️⃣ CI rodando também na `develop`

Em `.github/workflows/test.yml`:

```yaml
on:
  pull_request:
  push:
    branches: [main, develop]
```

Sem isso, o merge de uma feature na `develop` não roda a CI, e só se descobre a quebra na release.

---

## ✅ Verificação

```bash
cd backend
grep -rn "recomedac" . --include=*.py --exclude-dir=.venv                        # vazio
grep -n "def banda\|CORTE_M" quiz/engine.py                                     # 5 linhas: banda() e os cortes continuam
python manage.py test                                                            # 74 testes
python manage.py makemigrations --check --dry-run                                # No changes detected
```

## 📦 Commit e PR

```bash
git add -A
git commit -m "chore: renomeia recomedacao para recomendar e limpa arquivos vazios

- engine: recomedacao -> recomendar; banda() documentada (fica para o fallback)
- remove out.txt, perfil.html e test_recomendacao.py (vazios)
- ci: roda tambem no push para develop"
git push -u origin feature/limpeza-pre-ia
gh pr create --base develop --fill
```

> [!success] Definition of Done
> Nenhuma ocorrência de `recomedac`, 74 testes com o mesmo resultado de antes, CI verde no PR.
