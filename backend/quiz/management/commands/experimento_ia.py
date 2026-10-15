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
