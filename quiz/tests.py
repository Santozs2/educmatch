from django.test import TestCase

from catalogo.models import Area, Curso, Peso_curso
from quiz.engine import explicacao, recomedacao
from quiz.models import Alternativa, Peso_alternativa, Questao, Resposta, Tentativa_de_resposta


class ResultadoDisplayTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nome="Design", slug="design", descricao="Artes digitais")
        self.area_2 = Area.objects.create(nome="Programação", slug="programacao", descricao="Tecnologia")

        self.curso = Curso.objects.create(
            nome_curso="Curso de Design",
            descricao="Curso de design digital",
            area_principal=self.area,
            duracao=80,
        )
        Peso_curso.objects.create(curso=self.curso, area=self.area, peso=5.0)

        self.questao = Questao.objects.create(texto="Qual estilo você prefere?")
        self.alternativa = Alternativa.objects.create(texto="Crio interfaces", questao=self.questao)
        Peso_alternativa.objects.create(alternativa=self.alternativa, area=self.area, peso=5.0)

        self.tentativa = Tentativa_de_resposta.objects.create(respondido_por="Ana")
        Resposta.objects.create(tentativa=self.tentativa, questao=self.questao, alternativa=self.alternativa)

    def test_recomendacao_define_confidence_level(self):
        recomedacao(self.tentativa)
        self.tentativa.refresh_from_db()

        self.assertIn(self.tentativa.confidence_band, ["alta", "media", "baixa"])
        self.assertNotEqual(self.tentativa.confidence_band, "")

    def test_explicacao_exibe_area_name(self):
        resultado = explicacao(
            {"design": 5.0, "programacao": 4.0},
            {"design": 5.0, "programacao": 4.0},
            {"design": "Design", "programacao": "Programação"},
        )

        self.assertIn("top_areas", resultado)
        self.assertIn("area_name", resultado["top_areas"][0])
