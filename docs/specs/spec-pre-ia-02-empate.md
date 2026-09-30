---
title: "Spec pré-IA 02 — uma régua só para empate e o tie_set preenchido"
aliases: ["PRE-02", "Conjunto de empate", "tie_set"]
tags: [tcc, spec, engine, ia, confianca]
status: proposto
projeto: TCC
branch: feature/conjunto-de-empate
criado: 2026-09-30
---

> [!info] Plano: [[plano-pre-ia-git-flow|🚧 Pré-IA e Git Flow]] · Anterior: [[spec-pre-ia-01-rank-final|01 — rank final]] · Próxima: [[spec-pre-ia-03-config-llm|03 — config da LLM]] · Prompt: [[Projetos/EducMatch(Secretária)/prompt-padrao-recomendacao|📝 regra 2]]

# ⚖️ PRE-02: uma régua só para empate

**Branch:** `feature/conjunto-de-empate`, saindo da `develop` **com a 01 já mesclada**
**Risco:** baixo. Nenhuma migração (o campo `tie_set` já existe).
**Testes ao final:** 84 (78 + 6 novos)

> [!abstract] O problema
> Hoje existem **dois "0,05" que medem coisas diferentes**:
>
> | Onde | Mede | Fórmula |
> |---|---|---|
> | `confianca()` no `engine.py` | separação **relativa** | `(1º − 2º) / 1º` |
> | Regra 2 do prompt | diferença **absoluta** | `1º − 2º` |
>
> Com 1º = 0,50 e 2º = 0,47, a engine diz confiança **média** (0,03 / 0,50 = 0,06), mas o prompt diz que é **empate** (0,03 < 0,05). O aluno veria "confiança média" e a LLM teria licença para trocar o 1º lugar. Na banca, isso não se defende.
>
> Além disso, o campo `tie_set` existe desde a F1-02 e **nunca foi preenchido**.

---

## 🧭 A decisão: diferença absoluta, uma constante

> [!important] `EMPATE = 0.05`, absoluta, em três lugares
> 1. **Banda de confiança:** baixa se `1º − 2º < 0,05`, alta se `≥ 0,15`.
> 2. **`tie_set`:** os cursos a menos de 0,05 do 1º, com o 1º incluído.
> 3. **Regra 2 do prompt** (Passo 8): a LLM só pode pôr em 1º um curso do `tie_set`.
>
> Consequência que um teste garante: **confiança baixa ⇔ `tie_set` com mais de um curso**. O aviso na tela e o poder da LLM passam a dizer a mesma coisa.

> [!question] Por que absoluta e não relativa
> A afinidade é um cosseno de 0 a 1, e o prompt já recebe o `score` puro. A diferença absoluta é o número que a LLM **vê** e o que o grupo consegue explicar para a banca sem fórmula: "os dois cursos ficaram a menos de 5 pontos percentuais um do outro". Ela também já está gravada na tentativa, no campo `diferenca`.

> [!note] Tentativas antigas não são recalculadas
> Elas mantêm a `confidence_band` da régua relativa e `tie_set = []`. Isso não atrapalha, porque a LLM só vai rodar em tentativas novas. **Anote na monografia**: a distribuição de confiança do painel mistura as duas réguas para dados anteriores à tag `v0.4.0`.

---

## 1️⃣ `quiz/engine.py`: as constantes

Troque:

```python
BANDA_CONFIANCA_ALTA = 0.15
BANDA_CONFIANCA_MEDIA = 0.05
```

por:

```python
# Diferença ABSOLUTA de afinidade entre dois cursos. A mesma régua decide a
# banda de confiança, o tie_set e a regra 2 do prompt (quando a LLM pode
# trocar o 1º lugar): três lugares, um número só.
EMPATE = 0.05
BANDA_CONFIANCA_ALTA = 0.15
CASAS = 6  # arredonda antes de comparar: 0.80 - 0.75 dá 0.05000000000000004
```

> [!warning] O arredondamento não é enfeite
> Em ponto flutuante, `0.80 - 0.75` é `0.05000000000000004`. Sem o `round`, uma diferença de exatamente 0,05 cai de um lado ou do outro dependendo dos números. Um dos testes abaixo trava exatamente esse caso.

## 2️⃣ `quiz/engine.py`: `confianca()` reescrita e `conjunto_de_empate()` nova

Substitua a função `confianca` inteira por estas três:

```python
def diferenca_do_topo(ranking, score):
    return round(ranking[0][1] - score, CASAS)


def confianca(ranking):
    """Quanto o 1º lugar se separou do 2º, no ranking INTEIRO (antes do corte)."""
    if not ranking or ranking[0][1] <= 0:
        return "baixa"

    segundo = ranking[1][1] if len(ranking) > 1 else 0.0
    diferenca = diferenca_do_topo(ranking, segundo)
    if diferenca >= BANDA_CONFIANCA_ALTA:
        return "alta"
    if diferenca >= EMPATE:
        return "media"
    return "baixa"


def conjunto_de_empate(ranking):
    """Ids dos cursos a menos de EMPATE do 1º lugar, o 1º incluído.

    É a lista de quem a LLM pode colocar em 1º (regra 2). Um item só = sem
    empate: a LLM não pode trocar o principal.
    """
    if not ranking:
        return []
    return [curso.pk for curso, score, _ in ranking if diferenca_do_topo(ranking, score) < EMPATE]
```

## 3️⃣ `quiz/engine.py`: gravar o `tie_set` em `recomendar()`

Troque:

```python
    tentativa.diferenca = primeiro - segundo
    tentativa.confidence_band = confianca(ranking)     # REC-04: mede antes do corte
    tentativa.save(update_fields=["confidence_band", "diferenca"])

    ranking = ranking[:limit]
```

por:

```python
    tentativa.diferenca = primeiro - segundo
    tentativa.confidence_band = confianca(ranking)     # REC-04: mede antes do corte
    ranking = ranking[:limit]
    tentativa.tie_set = conjunto_de_empate(ranking)    # só quem a LLM vai receber
    tentativa.save(update_fields=["confidence_band", "diferenca", "tie_set"])
```

> [!note] A confiança é medida **antes** do corte e o `tie_set` **depois**
> A confiança descreve o ranking inteiro (REC-04, não muda). O `tie_set` descreve o que a LLM pode fazer, e ela só recebe o top-5. Como o ranking está ordenado, os dois só divergiriam se mais de 5 cursos empatassem com o 1º. Nesse caso, a LLM só pode escolher entre os 5 que recebeu, e é isso que queremos.

> [!success] Nenhuma consulta a mais
> O `tie_set` entra no mesmo `save` que já existia. O teste REC-05 (`assertNumQueries(12)`) continua passando sem mudar o número.

---

## 4️⃣ O aviso da tela estava dizendo outra coisa

`templates/quiz/resultado.html`, linha 21. Hoje, para banda "baixa":

> Sua afinidade com os cursos disponíveis ficou baixa.

Mas a banda **nunca mediu afinidade**, e sim a **separação** entre o 1º e o 2º. Um aluno com 0,95 e 0,94 recebe "afinidade baixa", o que é o contrário da verdade. Troque o parágrafo por:

```html
    <p class="aviso" role="note">
        Mais de um curso combinou com você quase na mesma medida. Vale ler os
        primeiros com calma ou conversar com a secretaria antes de decidir.
    </p>
```

E em `quiz/tests/test_telas.py`, no `test_aviso_de_baixa_confianca_aparece`:

```python
        self.assertContains(resposta, "quase na mesma medida")
```

---

## 5️⃣ Testes novos: `quiz/tests/test_empate.py`

```python
from types import SimpleNamespace

from django.test import SimpleTestCase

from quiz.engine import confianca, conjunto_de_empate
from quiz.tests.base import BaseEducMatch


class ConjuntoDeEmpateTest(SimpleTestCase):
    """PRE-02: rankings montados à mão, (curso, afinidade, explicacao)."""

    def ranking(self, *afinidades):
        return [(SimpleNamespace(pk=i), valor, {}) for i, valor in enumerate(afinidades, start=1)]

    def test_primeiro_isolado_nao_tem_empate(self):
        self.assertEqual(conjunto_de_empate(self.ranking(0.9, 0.7, 0.6)), [1])

    def test_quem_esta_a_menos_de_005_entra(self):
        self.assertEqual(conjunto_de_empate(self.ranking(0.90, 0.88, 0.86, 0.70)), [1, 2, 3])

    def test_exatamente_005_nao_e_empate(self):
        """0.80 - 0.75 dá 0.05000000000000004 sem o arredondamento."""
        self.assertEqual(conjunto_de_empate(self.ranking(0.80, 0.75)), [1])

    def test_ranking_vazio(self):
        self.assertEqual(conjunto_de_empate([]), [])

    def test_banda_baixa_se_e_somente_se_ha_empate_no_topo(self):
        """A mesma régua: confiança baixa <=> a LLM pode trocar o 1º."""
        for afinidades in [(0.9, 0.5), (0.80, 0.79), (0.80, 0.75), (0.8, 0.7, 0.6), (0.61, 0.6)]:
            ranking = self.ranking(*afinidades)
            with self.subTest(afinidades=afinidades):
                self.assertEqual(confianca(ranking) == "baixa", len(conjunto_de_empate(ranking)) > 1)


class TieSetGravadoTest(BaseEducMatch):
    def test_engine_grava_o_tie_set_com_o_primeiro(self):
        tentativa = self.criar_tentativa()
        tentativa.refresh_from_db()
        primeiro = tentativa.recomendacoes.get(rank_engine=1)

        self.assertEqual(tentativa.tie_set[0], primeiro.curso_id)
        ids_entregues = set(tentativa.recomendacoes.values_list("curso_id", flat=True))
        self.assertTrue(set(tentativa.tie_set) <= ids_entregues)
```

> [!note] Os três testes antigos de `ConfiancaTest` continuam valendo
> `(0.9, 0.5, 0.4)` → alta, `(0.80, 0.79, 0.5)` → baixa e `(0.0, 0.0)` → baixa dão o mesmo resultado nas duas réguas. Não precisa mexer em `test_motor.py`.

---

## 6️⃣ Fora do código: atualize o prompt no vault

Na nota [[Projetos/EducMatch(Secretária)/prompt-padrao-recomendacao|📝 Prompt padrão]], a regra 2 passa a citar o `tie_set` explicitamente. Assim o Passo 8 já nasce com a regra conferível pelo servidor:

> Só coloque em 1º lugar um curso cujo `course_id` esteja em `tie_set`. Se `tie_set` tiver um único id, o 1º lugar não muda.

E o `build_payload` do Passo 7 passa a enviar `"tie_set": [...]` junto com os `candidatos`.

---

## ✅ Verificação

```bash
cd backend
python manage.py test                                # 84 testes
python manage.py makemigrations --check --dry-run    # No changes detected
grep -n "BANDA_CONFIANCA_MEDIA\|separacao" quiz/engine.py   # vazio
```

## 📦 Commit e PR

```bash
git add -A
git commit -m "feat(motor): regua unica de empate e tie_set gravado

- confianca() passa a usar diferenca absoluta (EMPATE = 0.05)
- conjunto_de_empate() preenche Tentativa.tie_set com o top-5
- banda baixa <=> tie_set com mais de um curso (testado)
- aviso da tela descreve empate, nao afinidade baixa"
git push -u origin feature/conjunto-de-empate
gh pr create --base develop --fill
```

> [!success] Definition of Done
> 84 testes. Toda tentativa nova sai com `tie_set` não vazio e com o 1º colocado na primeira posição. O teste de equivalência (banda baixa ⇔ empate) está verde.
