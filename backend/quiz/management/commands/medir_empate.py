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