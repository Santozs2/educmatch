import json
import re

from quiz.llm.base import LLMResponse, LLMUnavailable

# Acha os ids em qualquer prompt: no JSON.
COURSE_ID = re.compile(r'"course_id"\s*:\s*(\d+)')
# Só o prompt do consultor do painel traz áreas com "slug".
SLUG = re.compile(r'"slug"\s*:\s*"([\w-]+)"')


class FakeProvider:
    """Provedor de teste: nada de rede, e sempre a mesma resposta para o mesmo prompt.

    Entrega os cursos na ordem em que vieram, no formato de saída do contrato.
    """

    name = "fake"

    def __init__(self, timeout=None):
        pass  # sem rede, nada a esperar

    def complete(self, prompt: str) -> LLMResponse:
        slugs = list(dict.fromkeys(SLUG.findall(prompt)))
        if slugs:
            return self._consultor(slugs)

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

    @staticmethod
    def _consultor(slugs):
        """A saída do consultor de cursos: as duas primeiras áreas do prompt."""
        saida = {
            "areas": [
                {"slug": slug, "justificativa": f"Justificativa de teste da área {slug}.", "peso": 5 - i}
                for i, slug in enumerate(slugs[:2])
            ],
            "nenhuma_area_adequada": False,
            "nova_area_sugerida": "",
            "nome_sugerido": "Nome de teste",
            "descricao_sugerida": "Descrição de teste.",
            "observacoes": "",
        }
        return LLMResponse(text=json.dumps(saida, ensure_ascii=False), model="fake")
