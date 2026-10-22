"""Teste de carga: uma turma inteira enviando o quiz ao mesmo tempo.

Mede o que os testes automáticos não conseguem: várias threads gravando no
SQLite juntas, como no gunicorn com threads (startup.sh). Usa o settings.py
como está, num banco SQLite temporário, e um dublê no lugar da LLM: não gasta
cota nem precisa de internet.

Uso, de dentro de backend/:
    python scripts/carga_turma.py
    python scripts/carga_turma.py --alunos 30 --lugares 16

Sai com código 1 se algum aluno não recebeu o resultado (HTTP diferente de
302) ou se a entrega de alguma tentativa não foi gravada.
"""
import argparse
import os
import random
import sys
import tempfile
import threading
import time
from pathlib import Path
from statistics import median
from unittest import mock

BACKEND = Path(__file__).resolve().parent.parent
BANCO = Path(tempfile.gettempdir()) / "educmatch_carga.sqlite3"

# Antes do django.setup(): o .env só preenche o que não estiver definido aqui.
os.environ.update(
    DJANGO_SETTINGS_MODULE="core.settings",
    DB_ENGINE="sqlite",
    DB_NAME=str(BANCO),
    LLM_ENABLED="1",
    LLM_PROVIDER="fake",
)
sys.path.insert(0, str(BACKEND))

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.db import connections  # noqa: E402
from django.test import Client  # noqa: E402

from quiz.llm import FakeProvider, LLMTimeout  # noqa: E402
from quiz.models import Questao, Tentativa_de_resposta  # noqa: E402


class Duble:
    """A LLM de mentira: demora `atraso` segundos e responde, ou cai."""

    name = "duble"

    def __init__(self, atraso, cai):
        self.atraso, self.cai = atraso, cai

    def complete(self, prompt):
        time.sleep(self.atraso)
        if self.cai:
            raise LLMTimeout(f"sem resposta em {self.atraso}s")
        return FakeProvider().complete(prompt)


def cenario(nome, alunos, lugares, atraso, cai, questoes):
    """Todos os alunos enviam juntos; `lugares` imita as threads do gunicorn."""
    cache.clear()
    fila = threading.Semaphore(lugares)
    sorteio = random.Random(42)
    perfis = [
        {f"questao_{q}": str(sorteio.choice(alternativas)) for q, alternativas in questoes}
        for _ in range(alunos)
    ]
    antes = Tentativa_de_resposta.objects.count()
    esperas, status = [], []

    def aluno(i):
        inicio = time.monotonic()
        with fila:
            resposta = Client(HTTP_HOST="localhost", raise_request_exception=False).post(
                "/", {"respondido_por": f"Aluno {i}", **perfis[i]}
            )
        status.append(resposta.status_code)
        esperas.append(time.monotonic() - inicio)
        connections.close_all()

    with mock.patch("quiz.delivery.get_provider", return_value=Duble(atraso, cai)):
        threads = [threading.Thread(target=aluno, args=(i,)) for i in range(alunos)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    novas = Tentativa_de_resposta.objects.order_by("id")[antes:]
    sem_gravar = sum(not t.llm_model for t in novas)
    sem_resultado = alunos - status.count(302)
    print(
        f"{nome:<32} | mediana {median(esperas):4.1f}s | pior {max(esperas):4.1f}s | "
        f"resultado {status.count(302)}/{alunos} | entrega não gravada: {sem_gravar}"
    )
    return sem_resultado + sem_gravar


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--alunos", type=int, default=30)
    parser.add_argument("--lugares", type=int, default=16, help="workers x threads (padrão 2x8)")
    args = parser.parse_args()

    BANCO.unlink(missing_ok=True)
    for comando in ["migrate", "createcachetable", "seed_areas", "seed_cursos", "seed_questoes"]:
        call_command(comando, verbosity=0)
    questoes = [
        (q.id, [a.id for a in q.alternativas.all()]) for q in Questao.objects.filter(is_active=True)
    ]

    print(f"SQLite {settings.DATABASES['default'].get('OPTIONS')}")
    print(f"{args.alunos} alunos, {args.lugares} atendidos ao mesmo tempo\n")
    problemas = cenario("LLM respondendo (1,7 s)", args.alunos, args.lugares, 1.7, False, questoes)
    problemas += cenario("LLM fora do ar (timeout 8 s)", args.alunos, args.lugares, 8, True, questoes)

    connections.close_all()  # no Windows, arquivo aberto não pode ser apagado
    BANCO.unlink(missing_ok=True)
    print("\nOK: nenhum resultado nem entrega perdidos." if not problemas else f"\nFALHOU: {problemas} problema(s).")
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
