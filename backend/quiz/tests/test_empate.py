from types import SimpleNamespace

from django.test import SimpleTestCase

from quiz.engine import confianca, conjunto_de_empate
from quiz.tests.base import BaseEducMatch


def montar(*afinidades):
    """Ranking montado à mão: (curso, afinidade, explicacao)."""
    return [(SimpleNamespace(pk=i), valor, {}) for i, valor in enumerate(afinidades, start=1)]


class ConjuntoDeEmpateTest(SimpleTestCase):
    """PRE-02 com a régua calibrada (CAL-01): EMPATE = 0.02."""

    def test_primeiro_isolado_nao_tem_empate(self):
        self.assertEqual(conjunto_de_empate(montar(0.9, 0.7, 0.6)), [1])

    def test_quem_esta_a_menos_de_002_entra(self):
        self.assertEqual(conjunto_de_empate(montar(0.90, 0.89, 0.885, 0.70)), [1, 2, 3])

    def test_exatamente_002_nao_e_empate(self):
        """0.80 - 0.78 dá 0.020000000000000018 sem o arredondamento."""
        self.assertEqual(conjunto_de_empate(montar(0.80, 0.78)), [1])

    def test_diferenca_de_003_deixou_de_ser_empate(self):
        """Com a régua antiga (0.05) isto era empate; com a calibrada, não."""
        self.assertEqual(conjunto_de_empate(montar(0.80, 0.77)), [1])

    def test_ranking_vazio(self):
        self.assertEqual(conjunto_de_empate([]), [])

    def test_banda_baixa_se_e_somente_se_ha_empate_no_topo(self):
        """A mesma régua: confiança baixa <=> a LLM pode trocar o 1º."""
        for afinidades in [(0.9, 0.5), (0.80, 0.79), (0.80, 0.78), (0.80, 0.77), (0.8, 0.7, 0.6), (0.61, 0.6)]:
            ranking = montar(*afinidades)
            with self.subTest(afinidades=afinidades):
                self.assertEqual(confianca(ranking) == "baixa", len(conjunto_de_empate(ranking)) > 1)


class ConfiancaCalibradaTest(SimpleTestCase):
    """CAL-01: os dois cortes da banda, um caso em cada lado de cada corte."""

    def test_cortes(self):
        casos = [
            ((0.80, 0.79), "baixa"),   # 0.01
            ((0.80, 0.78), "media"),   # 0.02: exatamente o EMPATE
            ((0.80, 0.73), "media"),   # 0.07
            ((0.80, 0.72), "alta"),    # 0.08: exatamente o corte alto
        ]
        for afinidades, esperado in casos:
            with self.subTest(afinidades=afinidades):
                self.assertEqual(confianca(montar(*afinidades)), esperado)


class TieSetGravadoTest(BaseEducMatch):
    def test_engine_grava_o_tie_set_com_o_primeiro(self):
        tentativa = self.criar_tentativa()
        tentativa.refresh_from_db()
        primeiro = tentativa.recomendacoes.get(rank_engine=1)

        self.assertEqual(tentativa.tie_set[0], primeiro.curso_id)
        ids_entregues = set(tentativa.recomendacoes.values_list("curso_id", flat=True))
        self.assertTrue(set(tentativa.tie_set) <= ids_entregues)