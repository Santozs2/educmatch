---
title: "Spec CAL-01 — calibrar a régua de empate para o quiz de 10 perguntas"
aliases: ["CAL-01", "Calibrar EMPATE", "Régua de empate calibrada"]
tags: [tcc, spec, engine, ia, confianca, calibracao]
status: proposto
projeto: TCC
branch: feature/calibra-empate
criado: 2026-10-03
---

> [!info] Plano: [[plano-pre-ia-git-flow|🚧 Pré-IA e Git Flow]] · Origem da régua: [[spec-pre-ia-02-empate|02 — empate]] · Prompt: [[Projetos/EducMatch(Secretária)/prompt-padrao-recomendacao|📝 regra 2]] · Próximo: Passo 7 do [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 plano da IA]]

# 📏 CAL-01: calibrar a régua de empate

**Branch:** `feature/calibra-empate`, saindo da `develop` (v0.2, `7993b35`)
**Risco:** baixo. Nenhuma migração. Muda duas constantes, um teste velho e cria um comando.
**Testes ao final:** 149 (144 + 5 novos)

> [!success] O código desta spec já foi rodado
> Aplicado numa cópia da `develop` em 2026-10-03: **149 testes, 0 falhas** no MySQL, `makemigrations --check` limpo. As porcentagens das tabelas abaixo são a saída real do comando `medir_empate` criado aqui.

---

## 🧭 O problema

A PRE-02 escolheu `EMPATE = 0.05` e `BANDA_CONFIANCA_ALTA = 0.15` **antes** do quiz ter 10 perguntas e 24 cursos. Com o catálogo de hoje, as afinidades do 1º lugar ficam entre 0,56 e 0,92. Por isso as diferenças entre cursos são pequenas, e a régua de 0,05 ficou larga demais.

Medido em **3.000 perfis sorteados** (semente 1) e nas **21 tentativas reais** do banco local:

| Diferença 1º − 2º menor que | Perfis sorteados | Tentativas reais |
|---|---|---|
| 0,01 | 13% | 10% |
| 0,02 | 26% | 14% |
| 0,03 | 38% | 52% |
| **0,05 (régua atual)** | **58%** | **62%** |
| 0,08 | 81% | 86% |
| 0,10 | 91% | 90% |
| **0,15 (corte alto atual)** | **99%** | **100%** |

Com a régua de hoje:

| Efeito | Por que é um problema |
|---|---|
| A LLM pode trocar o 1º lugar em **~60%** dos casos | O grupo decidiu que ela só **desempata**. Com 60%, ela reordena quase sempre, e o Passo 11 mediria outra coisa |
| O aviso "quase na mesma medida" aparece para a **maioria** dos alunos | Um aviso que aparece sempre deixa de ser lido |
| Confiança "alta" em **1%** dos perfis | A banda vira, na prática, só "baixa" ou "média" |

## 🎯 A decisão

| Constante | Antes | Depois | Critério |
|---|---|---|---|
| `EMPATE` | 0,05 | **0,02** | ~p25 dos perfis sorteados: empate em **~1 a cada 4** |
| `BANDA_CONFIANCA_ALTA` | 0,15 | **0,08** | ~p80 dos perfis sorteados: alta em **~1 a cada 5** |

Distribuição resultante:

| | baixa (empate) | média | alta |
|---|---|---|---|
| Perfis sorteados | 26% | 55% | 19% |
| Tentativas reais | 14% | 71% | 14% |

> [!important] Por que perfis sorteados, e não só os reais
> As 21 tentativas reais são poucas e quase todas são testes do grupo. Os perfis sorteados mostram o comportamento do **catálogo**: o que a régua faz com qualquer combinação de respostas. Os reais servem de conferência, e os dois apontam na mesma direção.
> **Recalibre quando houver respostas de alunos de verdade.** É para isso que o comando `medir_empate` existe: a escolha fica reproduzível, e não um número tirado da cabeça.

> [!note] Para a monografia
> - A régua mudou duas vezes: relativa (v0.1, antes da PRE-02), absoluta 0,05 (PRE-02) e absoluta 0,02 (CAL-01). Tentativas antigas guardam a `confidence_band` e o `tie_set` da régua da época. **Não recalcule**: elas são o registro do que o aluno viu.
> - A tabela acima, gerada pelo comando, é a justificativa do valor. Cole a saída do `medir_empate` no capítulo de metodologia.

---

## 1️⃣ `quiz/engine.py`: as duas constantes

Troque:

```python
# trocar o 1º lugar): três lugares, um número só.
EMPATE = 0.05
BANDA_CONFIANCA_ALTA = 0.15
CASAS = 6  # arredonda antes de comparar: 0.80 - 0.75 dá 0.05000000000000004
```

por:

```python
# trocar o 1º lugar): três lugares, um número só.
# Calibrados com `manage.py medir_empate` (quiz de 10 perguntas, 24 cursos):
# empate em ~1/4 dos perfis e confiança alta em ~1/5. Ver spec-calibra-empate.
EMPATE = 0.02
BANDA_CONFIANCA_ALTA = 0.08
CASAS = 6  # arredonda antes de comparar: 0.80 - 0.78 dá 0.020000000000000018
```

Nada mais no motor muda: `confianca()`, `conjunto_de_empate()` e `diferenca_do_topo()` já leem as constantes.

---

## 2️⃣ Comando novo: `quiz/management/commands/medir_empate.py`

Gera a tabela da seção acima. Lê o catálogo, **não grava nada** no banco.

```python
import random

from django.core.management.base import BaseCommand

from catalogo.models import Area, Curso
from quiz import engine
from quiz.models import Questao, Tentativa_de_resposta

LIMIARES = (0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.15)


def diferencas_simuladas(n, semente):
    """Diferença entre o 1º e o 2º para n perfis com respostas sorteadas."""
    sorteio = random.Random(semente)
    questoes = list(Questao.objects.filter(is_active=True).prefetch_related("alternativas__pesos__area"))
    cursos = list(Curso.objects.filter(is_active=True).prefetch_related("curso_peso__area"))
    nomes = dict(Area.objects.values_list("slug", "nome"))
    diferencas = []
    for _ in range(n):
        alternativas = [sorteio.choice(list(q.alternativas.all())) for q in questoes]
        ranking = engine.rank_cursos(engine.perfil_vetor(alternativas), cursos, nomes)
        if len(ranking) > 1:
            diferencas.append(engine.diferenca_do_topo(ranking, ranking[1][1]))
    return diferencas


def diferencas_reais():
    return [
        round(valor, engine.CASAS)
        for valor in Tentativa_de_resposta.objects.exclude(diferenca__isnull=True).values_list("diferenca", flat=True)
    ]


def fracao_abaixo(diferencas, limiar):
    return sum(d < limiar for d in diferencas) / len(diferencas) if diferencas else None


def porcento(valor):
    return "—" if valor is None else f"{valor:.0%}"


class Command(BaseCommand):
    help = (
        "Mede como se distribui a diferença entre o 1º e o 2º curso, em perfis "
        "sorteados e nas tentativas reais. Serve para calibrar EMPATE e "
        "BANDA_CONFIANCA_ALTA no quiz/engine.py."
    )

    def add_arguments(self, parser):
        parser.add_argument("--n", type=int, default=3000, help="Perfis sorteados (padrão 3000).")
        parser.add_argument("--semente", type=int, default=1, help="Semente do sorteio (padrão 1).")

    def handle(self, *args, n, semente, **options):
        simuladas = diferencas_simuladas(n, semente)
        reais = diferencas_reais()

        self.stdout.write(f"Perfis sorteados: {len(simuladas)} | tentativas reais: {len(reais)}\n")
        self.stdout.write("diferença <  | sorteados | reais")
        for limiar in LIMIARES:
            self.stdout.write(
                f"{limiar:<11} | {porcento(fracao_abaixo(simuladas, limiar)):>9} "
                f"| {porcento(fracao_abaixo(reais, limiar)):>5}"
            )

        self.stdout.write(
            f"\nRégua atual: EMPATE = {engine.EMPATE} | BANDA_CONFIANCA_ALTA = {engine.BANDA_CONFIANCA_ALTA}"
        )
        for nome, difs in (("sorteados", simuladas), ("reais", reais)):
            if not difs:
                continue
            baixa = fracao_abaixo(difs, engine.EMPATE)
            alta = 1 - fracao_abaixo(difs, engine.BANDA_CONFIANCA_ALTA)
            self.stdout.write(
                f"  {nome}: baixa (empate) {porcento(baixa)} | media {porcento(1 - baixa - alta)} | alta {porcento(alta)}"
            )
```

> [!tip] Por que a semente
> Com `--semente` fixa, o sorteio é sempre o mesmo: quem rodar o comando na banca vê **exatamente** a tabela da monografia. Trocar a semente mostra que o resultado não depende de um sorteio de sorte.

---

## 3️⃣ `quiz/tests/test_empate.py`: substitua o arquivo inteiro

Os casos antigos usavam 0,05 como fronteira. Os novos testam **as duas fronteiras calibradas**, com um caso de cada lado:

```python
from types import SimpleNamespace

from django.test import SimpleTestCase

from quiz.engine import confianca, conjunto_de_empate
from quiz.tests.base import BaseEducMatch


def montar(*afinidades):
    """Ranking montado à mão: (curso, afinidade, explicacao)."""
    return [(SimpleNamespace(pk=i), valor, {}) for i, valor in enumerate(afinidades, start=1)]


class ConjuntoDeEmpateTest(SimpleTestCase):
    """PRE-02 com a régua calibrada (CAL-01): EMPATE = 0.02."""

    def test_primeiro_isolado_nao_tem_empate(self):
        self.assertEqual(conjunto_de_empate(montar(0.9, 0.7, 0.6)), [1])

    def test_quem_esta_a_menos_de_002_entra(self):
        self.assertEqual(conjunto_de_empate(montar(0.90, 0.89, 0.885, 0.70)), [1, 2, 3])

    def test_exatamente_002_nao_e_empate(self):
        """0.80 - 0.78 dá 0.020000000000000018 sem o arredondamento."""
        self.assertEqual(conjunto_de_empate(montar(0.80, 0.78)), [1])

    def test_diferenca_de_003_deixou_de_ser_empate(self):
        """Com a régua antiga (0.05) isto era empate; com a calibrada, não."""
        self.assertEqual(conjunto_de_empate(montar(0.80, 0.77)), [1])

    def test_ranking_vazio(self):
        self.assertEqual(conjunto_de_empate([]), [])

    def test_banda_baixa_se_e_somente_se_ha_empate_no_topo(self):
        """A mesma régua: confiança baixa <=> a LLM pode trocar o 1º."""
        for afinidades in [(0.9, 0.5), (0.80, 0.79), (0.80, 0.78), (0.80, 0.77), (0.8, 0.7, 0.6), (0.61, 0.6)]:
            ranking = montar(*afinidades)
            with self.subTest(afinidades=afinidades):
                self.assertEqual(confianca(ranking) == "baixa", len(conjunto_de_empate(ranking)) > 1)


class ConfiancaCalibradaTest(SimpleTestCase):
    """CAL-01: os dois cortes da banda, um caso em cada lado de cada corte."""

    def test_cortes(self):
        casos = [
            ((0.80, 0.79), "baixa"),   # 0.01
            ((0.80, 0.78), "media"),   # 0.02: exatamente o EMPATE
            ((0.80, 0.73), "media"),   # 0.07
            ((0.80, 0.72), "alta"),    # 0.08: exatamente o corte alto
        ]
        for afinidades, esperado in casos:
            with self.subTest(afinidades=afinidades):
                self.assertEqual(confianca(montar(*afinidades)), esperado)


class TieSetGravadoTest(BaseEducMatch):
    def test_engine_grava_o_tie_set_com_o_primeiro(self):
        tentativa = self.criar_tentativa()
        tentativa.refresh_from_db()
        primeiro = tentativa.recomendacoes.get(rank_engine=1)

        self.assertEqual(tentativa.tie_set[0], primeiro.curso_id)
        ids_entregues = set(tentativa.recomendacoes.values_list("curso_id", flat=True))
        self.assertTrue(set(tentativa.tie_set) <= ids_entregues)
```

> [!note] `test_motor.py` não muda
> Os casos de `ConfiancaTest` continuam certos com a régua nova: `(0.9, 0.5, 0.4)` → alta, `(0.80, 0.79, 0.5)` → baixa, `(0.0, 0.0)` → baixa.

## 4️⃣ Teste novo: `quiz/tests/test_medir_empate.py`

```python
from io import StringIO

from django.core.management import call_command

from quiz.management.commands.medir_empate import fracao_abaixo
from quiz.tests.base import BaseEducMatch


class MedirEmpateTest(BaseEducMatch):
    """CAL-01: o comando que sustenta a escolha do EMPATE roda e é reprodutível."""

    def medir(self, **opcoes):
        saida = StringIO()
        call_command("medir_empate", stdout=saida, **opcoes)
        return saida.getvalue()

    def test_mostra_a_tabela_e_a_regua_atual(self):
        saida = self.medir(n=50)

        self.assertIn("Perfis sorteados: 50", saida)
        self.assertIn("Régua atual: EMPATE = 0.02", saida)
        self.assertIn("sorteados: baixa (empate)", saida)

    def test_mesma_semente_mesmo_resultado(self):
        self.assertEqual(self.medir(n=50, semente=7), self.medir(n=50, semente=7))

    def test_fracao_abaixo(self):
        self.assertEqual(fracao_abaixo([0.01, 0.03, 0.05, 0.07], 0.04), 0.5)
        self.assertIsNone(fracao_abaixo([], 0.04))
```

---

## 5️⃣ Um teste do painel que estava errado desde o #34

> [!bug] `test_confianca_tambem_e_suprimida` passava por coincidência
> Em `painel/tests/test_privacidade.py` (linha 135), ele confere que toda faixa de confiança tem total **≥ 5 ou escondido**. Mas o #34 desligou o esconder (`K_MINIMO = 0`), e o próprio comentário do arquivo diz que *nenhum teste daqui depende da regra antiga dos 5*. Ele passava só porque, com a régua 0,05, as 6 tentativas do teste caíam todas na mesma faixa. Com a régua calibrada elas se dividem (3 + 3) e o teste quebra.
>
> Conserto: testar o que o #34 promete, que é **nenhuma faixa escondida e nada perdido na soma**. O teste novo passa com a régua antiga **e** com a nova, ou seja, não depende da calibração.

Troque o método inteiro:

```python
    def test_confianca_tambem_e_suprimida(self):
        self.criar_tentativas(quantidade=ALGUNS + 1)

        confianca = self.abrir_painel("painel-quiz").context["confianca"]

        for linha in confianca:
            if linha["total"] is not None:
                self.assertGreaterEqual(linha["total"], ALGUNS)
```

por:

```python
    def test_confianca_mostra_toda_faixa_sem_esconder(self):
        """K_MINIMO = 0: faixa pequena aparece com o número, e nada se perde na soma."""
        tentativas = self.criar_tentativas(quantidade=ALGUNS + 1)

        confianca = self.abrir_painel("painel-quiz").context["confianca"]

        self.assertTrue(all(linha["total"] is not None for linha in confianca))
        self.assertEqual(sum(linha["total"] for linha in confianca), len(tentativas))
```

---

## 6️⃣ Fora do código: o prompt no vault

Na nota [[Projetos/EducMatch(Secretária)/prompt-padrao-recomendacao|📝 Prompt padrão]], a regra 2 ainda fala em diferença **menor que 0,05** e não cita o `tie_set`. Atualize para:

> Só coloque em 1º lugar um curso cujo `course_id` esteja em `tie_set`. Se `tie_set` tiver um único id, o 1º lugar não muda.

Sem número no prompt: quem decide o empate é a engine, que manda o `tie_set` pronto. Se a régua for recalibrada de novo, **o prompt não muda** e a `prompt_version` não precisa subir.

---

## ✅ Verificação

```bash
cd backend
python manage.py test                               # 149 testes, OK
python manage.py makemigrations --check --dry-run   # No changes detected
python manage.py medir_empate                       # "Régua atual: EMPATE = 0.02 | BANDA_CONFIANCA_ALTA = 0.08"
grep -n "EMPATE = 0.05\|ALTA = 0.15" quiz/engine.py # vazio
```

A saída do `medir_empate` no seu banco deve bater com as tabelas desta spec (sorteados 26% / 55% / 19%), desde que o catálogo e as perguntas sejam os mesmos.

## 📦 Commit e PR

```bash
git switch develop && git pull
git switch -c feature/calibra-empate
# ... seguir a spec ...
git add -A
git commit -m "feat(motor): calibra a regua de empate para o quiz de 10 perguntas

- EMPATE 0.05 -> 0.02 e BANDA_CONFIANCA_ALTA 0.15 -> 0.08
- comando medir_empate gera a tabela que justifica os valores
- test_empate cobre as duas fronteiras calibradas
- painel: teste de confianca passa a provar o K_MINIMO = 0 do #34"
git push -u origin feature/calibra-empate
gh pr create --base develop --fill
```

> [!success] Definition of Done
> 149 testes, `medir_empate` mostrando a régua 0,02 / 0,08, prompt do vault sem número na regra 2, e a saída do comando guardada para o capítulo de metodologia.
