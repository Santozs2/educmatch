from types import SimpleNamespace

from django.test import SimpleTestCase

from quiz.engine import confianca, conjunto_de_empate
from quiz.tests.base import BaseEducMatch


class ConjuntoDeEmpateTest(SimpleTestCase):
    """PRE-02: rankings montados à mão, (curso, afinidade, explicacao)."""

    def ranking(self, *afinidades):
        return [(SimpleNamespace(pk=i), valor, {}) for i, valor in enumerate(afinidades, start=1)]

    def test_primeiro_isolado_nao_tem_empate(self):
        self.assertEqual(conjunto_de_empate(self.ranking(0.9, 0.7, 0.6)), [1])

    def test_quem_esta_a_menos_de_005_entra(self):
        self.assertEqual(conjunto_de_empate(self.ranking(0.90, 0.88, 0.86, 0.70)), [1, 2, 3])

    def test_exatamente_005_nao_e_empate(self):
        """0.80 - 0.75 dá 0.05000000000000004 sem o arredondamento."""
        self.assertEqual(conjunto_de_empate(self.ranking(0.80, 0.75)), [1])

    def test_ranking_vazio(self):
        self.assertEqual(conjunto_de_empate([]), [])

    def test_banda_baixa_se_e_somente_se_ha_empate_no_topo(self):
        """A mesma régua: confiança baixa <=> a LLM pode trocar o 1º."""
        for afinidades in [(0.9, 0.5), (0.80, 0.79), (0.80, 0.75), (0.8, 0.7, 0.6), (0.61, 0.6)]:
            ranking = self.ranking(*afinidades)
            with self.subTest(afinidades=afinidades):
                self.assertEqual(confianca(ranking) == "baixa", len(conjunto_de_empate(ranking)) > 1)


class TieSetGravadoTest(BaseEducMatch):
    def test_engine_grava_o_tie_set_com_o_primeiro(self):
        tentativa = self.criar_tentativa()
        tentativa.refresh_from_db()
        primeiro = tentativa.recomendacoes.get(rank_engine=1)

        self.assertEqual(tentativa.tie_set[0], primeiro.curso_id)
        ids_entregues = set(tentativa.recomendacoes.values_list("curso_id", flat=True))
        self.assertTrue(set(tentativa.tie_set) <= ids_entregues)