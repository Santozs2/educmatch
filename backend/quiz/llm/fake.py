import json
import re

from quiz.llm.base import LLMResponse, LLMUnavailable

# Acha os ids em qualquer prompt: no JSON.
COURSE_ID = re.compile(r'"course_id"\s*:\s*(\d+)')


class FakeProvider:
    """Provedor de teste: nada de rede, e sempre a mesma resposta para o mesmo prompt.

    Entrega os cursos na ordem em que vieram, no formato de saída do contrato.
    """

    name = "fake"

    def complete(self, prompt: str) -> LLMResponse:
        ids = list(dict.fromkeys(int(i) for i in COURSE_ID.findall(prompt)))
        if not ids:
            raise LLMUnavailable("o prompt não tem nenhum course_id")

        principal, *alternativas = ids
        saida = {
            "principal": {"course_id": principal, "texto": f"Texto de teste do curso {principal}."},
            "alternativas": [
                {"course_id": i, "texto": f"Texto de teste do curso {i}."} for i in alternativas
            ],
        }
        return LLMResponse(text=json.dumps(saida, ensure_ascii=False), model="fake")