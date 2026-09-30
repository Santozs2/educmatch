from django.test import SimpleTestCase

from catalogo.models import Curso
from quiz.engine import confianca, recomendar
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class MotorTest(BaseEducMatch):
    def responder(self):
        self.responder_tudo()
        return Tentativa_de_resposta.objects.latest("id")

    def test_curso_desativado_nao_e_recomendado(self):
        """REC-02: o filtro está no motor, não na tela."""
        primeiro = self.responder().recomendacoes.get(rank=1).curso
        Curso.objects.filter(pk=primeiro.pk).update(is_active=False)

        tentativa = self.responder()

        cursos = set(tentativa.recomendacoes.values_list("curso_id", flat=True))
        self.assertNotIn(primeiro.pk, cursos)
        self.assertEqual(len(cursos), 5)

    def test_numero_de_consultas_nao_cresce_com_o_catalogo(self):
        """REC-05: eram 120 consultas por quiz; com prefetch, 12."""
        tentativa = self.responder()
        with self.assertNumQueries(12):
            recomendar(tentativa)


class ConfiancaTest(SimpleTestCase):
    """REC-04 com rankings montados à mão: (curso, afinidade, explicacao)."""

    def ranking(self, *afinidades):
        return [(None, valor, {}) for valor in afinidades]

    def test_primeiro_muito_a_frente_e_alta(self):
        self.assertEqual(confianca(self.ranking(0.9, 0.5, 0.4)), "alta")

    def test_quase_empate_e_baixa(self):
        self.assertEqual(confianca(self.ranking(0.80, 0.79, 0.5)), "baixa")

    def test_quiz_em_branco_e_baixa(self):
        self.assertEqual(confianca(self.ranking(0.0, 0.0)), "baixa")