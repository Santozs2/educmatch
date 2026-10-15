---
title: "Spec IA · Passo 11 — experimento comparativo e métricas da IA no painel"
aliases: ["Passo 11", "Experimento da IA", "experimento_ia", "Taxa de divergência"]
tags: [tcc, ia, llm, spec, experimento, metricas, painel, monografia]
status: proposto
projeto: TCC
branch: feature/llm-experimento
criado: 2026-10-08
---

> [!info] Plano da IA: [[Projetos/EducMatch(Secretária)/camada-ia-plano-implementacao|🧩 Camada de IA]] · Anterior: [[spec-ia-passo-10-tela-de-entrega|🎨 Passo 10]] · Apresentação: [[ia|🤖 Camada de IA na banca]]

# 📊 Passo 11: experimento comparativo e métricas da IA no painel

**Branch:** `feature/llm-experimento`, saindo da `develop` **com o Passo 10 já mesclado**
**Risco:** baixo. Um comando novo e um bloco a mais na tela Quiz do painel. Nenhuma migração.
**Testes ao final:** a suíte do Passo 10 **+ 7** (na cópia: **203**)

> [!abstract] O que esta branch faz
> Transforma a camada de IA em **resultado medido**, não em "usamos IA":
> 1. **`python manage.py experimento_ia`:** roda N perfis pela engine **e** pela LLM e grava um **CSV**, uma linha por perfil, com uma coluna para a avaliação humana.
> 2. **Bloco "Camada de IA" no painel:** taxa de divergência, fallback, cache, latência, tokens e *qual curso o aluno salvou quando a IA trocou o 1º lugar*, com as tentativas reais.
>
> Os números do capítulo da monografia saem destes dois.

> [!success] O código desta spec já foi rodado
> Os **7 testes novos** passaram, e a suíte inteira fechou em **203 testes** (único erro: o do fuso, que depende do MySQL). O comando foi rodado na cópia com o provedor `fake` e gerou o CSV abaixo, sem deixar nenhuma tentativa no banco. `makemigrations --check`: **No changes detected**.

---

## 🎓 Entenda antes de começar

> [!question] A pergunta que a banca vai fazer
> *"Por que IA, se a engine já recomendava?"* Este passo existe para responder com números: **em quantos perfis a IA mudou o 1º lugar**, **se a mudança foi boa** (avaliação humana) e **quanto custou** (latência, tokens e fallback).

| Métrica | De onde vem | Pergunta que responde |
|---|---|---|
| **Taxa de divergência** | `diverged`, entre as entregas sem fallback | A IA mudou o 1º lugar em quantos %? |
| **Avaliação humana** | coluna `avaliacao_humana` do CSV | Quando mudou, melhorou, ficou indiferente ou piorou? |
| **Taxa de fallback** | `used_fallback` | Em quantos % a IA falhou e valeu a engine? |
| **Latência (mediana)** | `latency_ms`, **sem** os acertos de cache | Quanto o aluno espera a mais? |
| **Tokens** | `tokens_in`, `tokens_out` | Quanto custa cada chamada? |
| **Cache** | `cache_hit` | Quantas respostas saíram sem chamar a API? |
| **Seguiu a IA ou a engine** | `Interesse.rank_snapshot` × `rank_engine_snapshot` | Quando a IA trocou, o aluno salvou qual dos dois? |

> [!important] Divergência só pode acontecer no empate
> Pela regra 2, a LLM só troca o 1º lugar por um curso do `tie_set`. Em 5.000 perfis sorteados, **34%** têm empate no topo ([[engine|🧮 Engine, §6]]). Por isso o comando tem `--so-empates`: com a cota gratuita limitada, cada chamada vai para um perfil em que a IA **pode** discordar.

---

## 1️⃣ `backend/quiz/management/commands/experimento_ia.py` (arquivo novo)

```python
import csv
import random
import time
from statistics import median

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from quiz.delivery import entregar
from quiz.engine import recomendar
from quiz.models import Questao, Resposta, Tentativa_de_resposta

COLUNAS = [
    "perfil", "areas_do_principal", "confianca", "tamanho_tie_set", "principal_engine", "principal_entregue",
    "diverged", "used_fallback", "cache_hit", "latency_ms", "tokens_in", "tokens_out",
    "texto_principal", "avaliacao_humana",
]


class Command(BaseCommand):
    help = (
        "Passo 11: roda N perfis sorteados pela engine e pela LLM do .env e grava um CSV, "
        "uma linha por perfil. Nada fica no banco: cada perfil roda numa transação desfeita."
    )

    def add_arguments(self, parser):
        parser.add_argument("--n", type=int, default=30, help="Quantos perfis (padrão 30).")
        parser.add_argument("--semente", type=int, default=1, help="Semente do sorteio (padrão 1).")
        parser.add_argument("--so-empates", action="store_true",
                            help="Só perfis com empate no topo, os únicos em que a LLM pode trocar o 1º.")
        parser.add_argument("--pausa", type=float, default=4.0,
                            help="Segundos entre chamadas, para não estourar o limite por minuto (padrão 4).")
        parser.add_argument("--saida", default="experimento_ia.csv", help="Arquivo CSV de saída.")

    def handle(self, *args, n, semente, so_empates, pausa, saida, **options):
        if not settings.LLM_ENABLED:
            raise CommandError("Ligue a LLM no .env (LLM_ENABLED=1) e configure o provedor antes.")
        sorteio = random.Random(semente)
        questoes = list(Questao.objects.filter(is_active=True).prefetch_related("alternativas"))
        linhas, tentativas_de_sorteio = [], 0

        while len(linhas) < n and tentativas_de_sorteio < n * 50:
            tentativas_de_sorteio += 1
            escolhas = [sorteio.choice(list(q.alternativas.all())) for q in questoes]
            linha = self._rodar(escolhas, so_empates)
            if linha is None:
                continue
            linhas.append(linha)
            self.stdout.write(f"{len(linhas)}/{n} {'troca' if linha['diverged'] else 'igual'}"
                              f"{' (fallback)' if linha['used_fallback'] else ''}")
            if pausa and len(linhas) < n and not linha["cache_hit"]:
                time.sleep(pausa)

        with open(saida, "w", newline="", encoding="utf-8-sig") as arquivo:  # -sig: o Excel lê os acentos
            escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, delimiter=";")
            escritor.writeheader()
            escritor.writerows(linhas)
        self._resumo(linhas, saida)

    def _rodar(self, escolhas, so_empates):
        """Um perfil inteiro dentro de uma transação que sempre é desfeita."""
        with transaction.atomic():
            tentativa = Tentativa_de_resposta.objects.create(respondido_por="")
            Resposta.objects.bulk_create(
                [Resposta(tentativa=tentativa, questao=a.questao, alternativa=a) for a in escolhas]
            )
            recomendar(tentativa)
            if so_empates and len(tentativa.tie_set) < 2:
                transaction.set_rollback(True)
                return None
            entregar(tentativa)
            tentativa.refresh_from_db()
            recs = list(tentativa.recomendacoes.select_related("curso"))
            engine = min(recs, key=lambda r: r.rank_engine)
            entregue = min(recs, key=lambda r: r.rank_final)
            linha = {
                "perfil": "-".join(str(a.pk) for a in escolhas),
                "areas_do_principal": ", ".join(a["area_name"] for a in engine.explicacao.get("top_areas", [])),
                "confianca": tentativa.confidence_band,
                "tamanho_tie_set": len(tentativa.tie_set),
                "principal_engine": engine.curso.nome_curso,
                "principal_entregue": entregue.curso.nome_curso,
                "diverged": tentativa.diverged,
                "used_fallback": tentativa.used_fallback,
                "cache_hit": tentativa.cache_hit,
                "latency_ms": tentativa.latency_ms,
                "tokens_in": tentativa.tokens_in,
                "tokens_out": tentativa.tokens_out,
                "texto_principal": entregue.llm_text,
                "avaliacao_humana": "",  # o grupo preenche: melhorou | indiferente | piorou
            }
            transaction.set_rollback(True)
        return linha

    def _resumo(self, linhas, saida):
        if not linhas:
            self.stdout.write(self.style.WARNING("Nenhum perfil rodou."))
            return
        total = len(linhas)
        entregues = [l for l in linhas if not l["used_fallback"]]
        latencias = [l["latency_ms"] for l in linhas if not l["cache_hit"] and l["latency_ms"] is not None]
        tokens = [l["tokens_out"] for l in linhas if l["tokens_out"] is not None]

        def pct(parte, todo):
            return f"{parte / todo:.0%}" if todo else "—"

        self.stdout.write(self.style.SUCCESS(f"\nCSV: {saida} ({total} perfis)"))
        self.stdout.write(f"Com empate no topo: {pct(sum(l['tamanho_tie_set'] > 1 for l in linhas), total)}")
        self.stdout.write(f"Divergência (trocou o 1º): {pct(sum(l['diverged'] for l in entregues), len(entregues))}")
        self.stdout.write(f"Fallback: {pct(total - len(entregues), total)}")
        self.stdout.write(f"Latência mediana: {median(latencias) if latencias else '—'} ms")
        self.stdout.write(f"Tokens de saída (média): {round(sum(tokens) / len(tokens)) if tokens else '—'}")
```

> [!note] 🎓 Por que uma transação desfeita para cada perfil
> O experimento cria tentativas para poder chamar a mesma `recomendar` e a mesma `entregar` do quiz de verdade, **sem atalho**. Mas essas tentativas **não podem** aparecer no painel como se fossem alunos. O `transaction.set_rollback(True)` desfaz tudo no fim de cada perfil: **a chamada à API acontece, o banco fica intacto**.
> Efeito colateral: o cache também é desfeito (ele mora no mesmo banco), então rodar o experimento de novo chama a API de novo. Para pré-aquecer o cache da banca, use o **quiz de verdade** com os perfis da demo.

> [!note] 🎓 `--pausa` e a cota gratuita
> O plano gratuito limita as chamadas **por minuto**. Com `--pausa 4`, são cerca de 15 por minuto. Se aparecer `HTTP 429` no log, aumente a pausa. Cada 429 vira um fallback no CSV, e isso sujaria a taxa de fallback do experimento.

> [!tip] 🎓 `utf-8-sig` e `;`
> O `-sig` grava a marca que faz o **Excel** reconhecer os acentos, e o `;` como separador evita conflito com a vírgula decimal do Excel em português.

## 2️⃣ `backend/painel/metricas.py`: as métricas da camada

No import do Django, acrescente o `Avg`:

```python
from django.db.models import Avg, Count, F, Q
```

E, no fim do arquivo:

```python
def camada_de_ia(inicio):
    """Passo 11: o que a LLM fez no período. Só conta tentativas em que ela foi chamada.

    Divergência e cache são sobre as entregas da LLM (sem fallback). A latência
    ignora o cache: servir do banco leva milissegundos e esconderia a da API.
    """
    chamadas = Tentativa_de_resposta.objects.filter(_no_periodo(inicio)).exclude(llm_model="")
    total = chamadas.count()
    if not total:
        return None
    entregues = chamadas.filter(used_fallback=False)
    n_entregues = entregues.count()
    latencias = list(
        chamadas.filter(cache_hit=False, latency_ms__isnull=False).values_list("latency_ms", flat=True)
    )
    tokens = chamadas.filter(tokens_out__isnull=False).aggregate(entrada=Avg("tokens_in"), saida=Avg("tokens_out"))
    # Quando a LLM trocou o 1º lugar, qual dos dois o aluno salvou?
    salvos = Interesse.objects.filter(
        _no_periodo(inicio), tentativa_origem__diverged=True
    ).exclude(status="removido")
    return {
        "chamadas": total,
        "fallback": (total - n_entregues) / total * 100,
        "divergencia": entregues.filter(diverged=True).count() / n_entregues * 100 if n_entregues else None,
        "cache": entregues.filter(cache_hit=True).count() / n_entregues * 100 if n_entregues else None,
        "latencia_mediana": median(latencias) if latencias else None,
        "tokens_entrada": tokens["entrada"],
        "tokens_saida": tokens["saida"],
        "seguiu_ia": salvos.filter(rank_snapshot=1).exclude(rank_engine_snapshot=1).count(),
        "seguiu_engine": salvos.filter(rank_engine_snapshot=1).exclude(rank_snapshot=1).count(),
    }
```

> [!important] 🎓 "Seguiu a IA ou a engine" usa o snapshot que já existia
> Desde a PRE-01, o `Interesse` guarda **duas** posições do curso no momento em que o aluno salvou: `rank_snapshot` (a que ele **viu**) e `rank_engine_snapshot` (a que a engine **calculou**). Quando a IA trocou o 1º:
> - salvou o curso com `rank_snapshot = 1` e `rank_engine_snapshot ≠ 1` → **seguiu a IA**;
> - salvou o curso com `rank_engine_snapshot = 1` e `rank_snapshot ≠ 1` → **ficou com a engine**.
>
> É a única métrica que vem do **comportamento do aluno**, e não da opinião do grupo.

> [!note] 🎓 Como a função continua "pura"
> Ela segue a regra do `metricas.py`: recebe uma data, devolve números e **não lê pessoa nenhuma**. Só conta tentativas e interesses.

## 3️⃣ `backend/painel/views.py`: a tela Quiz recebe o bloco

No `quiz_visao_geral`, dentro do `contexto.update({...})`, depois de `"cobertura"`:

```python
        "camada_de_ia": metricas.camada_de_ia(inicio),
```

## 4️⃣ `backend/painel/templates/painel/quiz.html`

Logo **antes** do `<article>` da "Conversão por curso":

```html
{% if camada_de_ia %}
<article class="painel-card painel-grade" id="camada-de-ia">
    <h2 class="painel-card__titulo">Camada de IA <span class="painel-ajuda" tabindex="0" data-dica="Só as tentativas em que a LLM foi chamada. Divergência: a LLM trocou o 1º lugar da engine, o que ela só pode fazer dentro de um empate.">?</span></h2>
    <ul class="painel-lista">
        <li><span>Chamadas à LLM</span><b>{{ camada_de_ia.chamadas }}</b></li>
        <li><span>Trocou o 1º lugar (divergência)</span><b>{% if camada_de_ia.divergencia is None %}—{% else %}{{ camada_de_ia.divergencia|floatformat:0 }}%{% endif %}</b></li>
        <li><span>Caiu na engine (fallback)</span><b {% if camada_de_ia.fallback > 20 %}class="painel-alerta"{% endif %}>{{ camada_de_ia.fallback|floatformat:0 }}%</b></li>
        <li><span>Servido do cache</span><b>{% if camada_de_ia.cache is None %}—{% else %}{{ camada_de_ia.cache|floatformat:0 }}%{% endif %}</b></li>
        <li><span>Tempo de resposta (mediana)</span><b>{% if camada_de_ia.latencia_mediana is None %}—{% else %}{{ camada_de_ia.latencia_mediana|floatformat:0 }} ms{% endif %}</b></li>
        <li><span>Tokens por chamada (entrada → saída)</span><b>{% if camada_de_ia.tokens_saida is None %}—{% else %}{{ camada_de_ia.tokens_entrada|floatformat:0 }} → {{ camada_de_ia.tokens_saida|floatformat:0 }}{% endif %}</b></li>
        <li><span>Quando trocou, o aluno salvou o da IA / o da engine</span><b>{{ camada_de_ia.seguiu_ia }} / {{ camada_de_ia.seguiu_engine }}</b></li>
    </ul>
</article>
{% endif %}
```

> [!tip] 🎓 Só classes que o painel já tem
> `painel-card`, `painel-lista`, `painel-ajuda` e `painel-alerta` já existem no `painel.css`: o bloco nasce com a cara do resto do painel, sem CSS novo. O fallback acima de 20% fica destacado em `painel-alerta`, porque é sinal de chave errada, cota estourada ou modelo lento demais.

---

## 5️⃣ Testes

### `backend/painel/tests/test_camada_de_ia.py` (arquivo novo)

```python
from accounts.models import Interesse
from painel import metricas
from painel.tests.base import BasePainel


class CamadaDeIATest(BasePainel):
    """Passo 11: as métricas da LLM no painel, calculadas pelo servidor."""

    def tentativa(self, **metadados):
        tentativa = self.criar_tentativa()
        for campo, valor in metadados.items():
            setattr(tentativa, campo, valor)
        tentativa.save()
        return tentativa

    def cenario(self):
        trocou = self.tentativa(llm_model="m", diverged=True, latency_ms=1000, tokens_in=900, tokens_out=300)
        self.tentativa(llm_model="m", cache_hit=True, latency_ms=5)
        self.tentativa(llm_model="m", used_fallback=True, latency_ms=8000)
        self.tentativa()  # LLM desligada: não conta
        return trocou

    def test_sem_chamadas_nao_ha_bloco(self):
        self.tentativa()
        self.assertIsNone(metricas.camada_de_ia(None))

    def test_taxas_e_mediana(self):
        self.cenario()

        ia = metricas.camada_de_ia(None)

        self.assertEqual(ia["chamadas"], 3)
        self.assertAlmostEqual(ia["fallback"], 100 / 3)
        self.assertEqual(ia["divergencia"], 50)  # 1 das 2 entregas
        self.assertEqual(ia["cache"], 50)
        self.assertEqual(ia["latencia_mediana"], 4500)  # 1000 e 8000: o cache fica de fora
        self.assertEqual((ia["tokens_entrada"], ia["tokens_saida"]), (900, 300))

    def test_qual_primeiro_o_aluno_salvou_quando_houve_troca(self):
        trocou = self.cenario()
        cursos = list(trocou.recomendacoes.order_by("rank_engine"))
        Interesse.objects.create(usuario=self.criar_usuario("a@exemplo.com"), curso=cursos[1].curso,
                                 tentativa_origem=trocou, rank_snapshot=1, rank_engine_snapshot=2)
        Interesse.objects.create(usuario=self.criar_usuario("b@exemplo.com"), curso=cursos[0].curso,
                                 tentativa_origem=trocou, rank_snapshot=2, rank_engine_snapshot=1)

        ia = metricas.camada_de_ia(None)

        self.assertEqual((ia["seguiu_ia"], ia["seguiu_engine"]), (1, 1))

    def test_tela_quiz_mostra_o_bloco_so_com_dados(self):
        self.client.force_login(self.criar_staff())
        self.tentativa()
        self.assertNotContains(self.client.get("/painel/quiz/?periodo=anual"), "Camada de IA")

        self.cenario()
        self.assertContains(self.client.get("/painel/quiz/?periodo=anual"), "Camada de IA")
```

### `backend/quiz/tests/test_experimento_ia.py` (arquivo novo)

```python
import csv
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from quiz.management.commands.experimento_ia import COLUNAS
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
class ExperimentoIATest(BaseEducMatch):
    """Passo 11: o experimento grava o CSV e não deixa nada no banco."""

    def rodar(self, **opcoes):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "experimento.csv"
            call_command("experimento_ia", pausa=0, saida=str(saida), stdout=StringIO(), **opcoes)
            with open(saida, encoding="utf-8-sig") as arquivo:
                return list(csv.DictReader(arquivo, delimiter=";"))

    def test_uma_linha_por_perfil_e_banco_intacto(self):
        linhas = self.rodar(n=3)

        self.assertEqual(len(linhas), 3)
        self.assertEqual(list(linhas[0]), COLUNAS)
        self.assertTrue(all(linha["texto_principal"] for linha in linhas))
        self.assertEqual(Tentativa_de_resposta.objects.count(), 0)

    def test_so_empates(self):
        linhas = self.rodar(n=2, so_empates=True)

        self.assertEqual(len(linhas), 2)
        self.assertTrue(all(int(linha["tamanho_tie_set"]) > 1 for linha in linhas))

    @override_settings(LLM_ENABLED=False)
    def test_recusa_com_a_llm_desligada(self):
        with self.assertRaises(CommandError):
            self.rodar(n=1)
```

---

## 🧪 6️⃣ Rodando o experimento de verdade

Com o Passo 9 configurado (`LLM_ENABLED=1` e a chave no `.env`):

```bash
cd backend
python manage.py experimento_ia --n 30 --so-empates --saida experimento_ia_v1.csv
```

Saída real na cópia, com o provedor `fake` (que nunca diverge, de propósito):

```
1/5 igual
2/5 igual
...
CSV: experimento.csv (5 perfis)
Com empate no topo: 100%
Divergência (trocou o 1º): 0%
Fallback: 0%
Latência mediana: 16 ms
Tokens de saída (média): —
```

E as primeiras linhas do CSV:

```
perfil;areas_do_principal;confianca;tamanho_tie_set;principal_engine;principal_entregue;diverged;used_fallback;cache_hit;latency_ms;tokens_in;tokens_out;texto_principal;avaliacao_humana
1-5-9-13-20-22-28-29-34-40;Elétrica, Eletromecânica, Mecânica;baixa;3;Eletricista Instalador;Eletricista Instalador;False;False;False;16;;;Texto de teste do curso 1.;
```

### O protocolo para a monografia

1. **Rode duas vezes:** `--so-empates` (30 perfis) e **sem** a opção (30 perfis). A primeira mostra o que a IA faz quando **pode** discordar; a segunda, o comportamento no caso geral.
2. **Avaliação humana:** abra o CSV no Excel e, **só nas linhas com `diverged = True`**, cada integrante preenche sozinho `melhorou`, `indiferente` ou `piorou`, comparando `principal_engine` com `principal_entregue` e lendo `texto_principal`. Depois o grupo junta as notas e anota as discordâncias.
3. **Leia também os textos das linhas sem troca.** A regra 4 do prompt proíbe falar de salário e emprego, e a validação não lê o texto. Qualquer texto que fure as regras é um achado, e vira motivo para uma `entrega_v2.md`.
4. **Guarde o CSV** com o nome da versão do prompt (`experimento_ia_v1.csv`). Ele entra como anexo.

> [!example] A tabela do capítulo
> | Métrica | Só empates (n=30) | Geral (n=30) |
> |---|:-:|:-:|
> | Divergência | ?% | ?% |
> | Melhorou / indiferente / piorou | ? / ? / ? | ? / ? / ? |
> | Fallback | ?% | ?% |
> | Latência mediana | ? ms | ? ms |
> | Tokens (entrada → saída) | ? → ? | ? → ? |
>
> No caso geral, a divergência **não pode** passar da taxa de empate (cerca de 34%): é a regra 2 funcionando. Se passar, há bug.

---

## ✅ Verificação

```bash
cd backend
python manage.py test painel.tests.test_camada_de_ia quiz.tests.test_experimento_ia   # 7 testes, OK
python manage.py test                                                                # 203 na cópia
python manage.py experimento_ia --n 3 --pausa 0 --saida teste.csv                    # com LLM_ENABLED=1
```

No painel (`/painel/quiz/`), depois de alguns quizzes com a LLM ligada, o bloco **"Camada de IA"** aparece com os números. Sem nenhuma chamada no período, ele **não aparece**.

## 📦 Commit e PR

```bash
git switch develop && git pull
git switch -c feature/llm-experimento
# ... aplica a spec ...
git add backend/quiz/management/commands/experimento_ia.py backend/quiz/tests/test_experimento_ia.py backend/painel
git commit -m "feat(ia): experimento comparativo e metricas da IA no painel (Passo 11)

- experimento_ia: N perfis pela engine e pela LLM, CSV com coluna de avaliacao humana
- cada perfil roda numa transacao desfeita: nada fica no banco
- painel/quiz: bloco Camada de IA com divergencia, fallback, cache, latencia e tokens"
git push -u origin feature/llm-experimento
```

> [!warning] O CSV não vai para o Git do código
> `experimento_ia_*.csv` é material da monografia. Guarde-o na pasta do TCC, ou acrescente `*.csv` ao `.gitignore` do `backend/`. Ele não tem dado pessoal, mas não é código.

> [!success] Definition of Done (o do plano)
> - [ ] 7 testes novos verdes
> - [ ] CSV gerado com a LLM real, nas duas rodadas (só empates e geral)
> - [ ] Avaliação humana preenchida nas linhas com divergência
> - [ ] Tabela de métricas fechada e o capítulo escrito
> - [ ] [[ia|🤖 A nota de apresentação da IA]] atualizada com os números reais
