import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from quiz.delivery import build_payload
from quiz.llm import LLMError, get_provider
from quiz.models import Tentativa_de_resposta
from quiz.prompt import montar_prompt
from quiz.serializers import validate_delivery


class Command(BaseCommand):
    help = (
        "Faz UMA chamada ao provedor do .env com a última tentativa do banco e mostra "
        "o resultado. Não grava nada e não usa o cache: serve para conferir a chave."
    )

    def handle(self, *args, **options):
        tentativa = (
            Tentativa_de_resposta.objects.filter(recomendacoes__isnull=False).order_by("-id").first()
        )
        if tentativa is None:
            raise CommandError("Responda o quiz uma vez antes: não há tentativa com recomendações.")
        if not settings.LLM_ENABLED:
            self.stdout.write(self.style.WARNING("LLM_ENABLED=0: o quiz não chama a LLM; este teste chama mesmo assim."))

        payload = build_payload(tentativa)
        self.stdout.write(f"Provedor: {settings.LLM_PROVIDER} | modelo: {settings.LLM_MODEL or '(vazio)'} | tentativa {tentativa.pk}")
        inicio = time.monotonic()
        try:
            resposta = get_provider().complete(montar_prompt(payload, settings.LLM_PROMPT_VERSION))
            latencia = round((time.monotonic() - inicio) * 1000)
            self.stdout.write(f"Respondeu em {latencia} ms | modelo {resposta.model} | tokens {resposta.tokens_in} → {resposta.tokens_out}")
            entrega = validate_delivery(resposta.text, payload)
        except LLMError as erro:
            raise CommandError(f"{type(erro).__name__}: {erro}") from None

        nomes = {c["course_id"]: c["nome"] for c in payload["candidatos"]}
        motor = [c["course_id"] for c in payload["candidatos"]]
        self.stdout.write(self.style.SUCCESS("Saída aprovada pela validação."))
        for posicao, curso_id in enumerate(entrega.ordem, start=1):
            marca = "" if motor[posicao - 1] == curso_id else f"  (engine: {motor.index(curso_id) + 1}º)"
            self.stdout.write(f"\n{posicao}. {nomes[curso_id]}{marca}\n   {entrega.textos[curso_id]}")
