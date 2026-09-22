from painel import metricas
from painel.tests.base import BasePainel


class MetricasTest(BasePainel):
    def test_conversao_nao_infla_com_dois_joins(self):
        """O bug do produto cartesiano: dois Count sobre duas relações.

        Um curso com 3 recomendações e 2 interesses tem de devolver 3 e 2,
        não 6 e 6.
        """
        curso = self.criar_curso_com(recomendacoes=3, interesses=2)

        linha = next(l for l in metricas.conversao_por_curso(None) if l["id"] == curso.id)

        self.assertEqual(linha["recomendado"], 3)
        self.assertEqual(linha["interessados"], 2)
        self.assertAlmostEqual(linha["taxa"], 2 / 3 * 100)

    def test_demanda_por_area_le_a_area_dominante(self):
        """Lê top_areas[0]["area"], no formato que o motor grava de verdade. (PR-5)"""
        self.criar_tentativa_com_explicacao(
            {"top_areas": [{"area": "eletrica", "area_name": "Elétrica", "contribuicao": 3.0, "percentual": 75.0}]}
        )

        demanda = metricas.demanda_por_area(None)

        self.assertEqual(demanda[0]["area"], "eletrica")
        self.assertEqual(demanda[0]["total"], 1)

    def test_curso_inativo_nao_entra_na_conversao(self):
        inativo = self.criar_curso(is_active=False)
        ids = [linha["id"] for linha in metricas.conversao_por_curso(None)]
        self.assertNotIn(inativo.id, ids)

    def test_manifestacoes_contam_interesse_e_nao_recomendacao(self):
        curso = self.criar_curso_com(recomendacoes=4, interesses=1)

        top = metricas.top_cursos_com_manifestacoes(None)

        linha = next(l for l in top if l["curso_id"] == curso.id)
        self.assertEqual(linha["total"], 1)
        self.assertEqual(linha["nome"], curso.nome_curso)

    def test_distribuicao_de_confianca_roda(self):
        self.criar_tentativas(quantidade=2)
        bandas = {linha["confidence_band"] for linha in metricas.distribuicao_de_confianca(None)}
        self.assertTrue(bandas <= {"alta", "media", "baixa"})

    def test_cobertura_acusa_area_sem_questao(self):
        """A métrica que mostra o tamanho do buraco do instrumento."""
        sem_questao = [a for a in metricas.cobertura_de_areas() if a["alternativas"] == 0]
        self.assertTrue(sem_questao, "nenhuma área sem questão: confira o related_name")