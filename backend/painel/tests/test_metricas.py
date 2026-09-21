from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from painel import metricas


class MetricasTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        silencio = StringIO()
        for comando in ("seed_areas", "seed_cursos", "seed_questoes"):
            call_command(comando, stdout=silencio)

    def test_conversao_nao_infla_com_dois_joins(self):
        """O bug do produto cartesiano: dois Count sobre duas relacoes.

        Um curso com 3 recomendacoes e 2 interesses tem que devolver 3 e 2 --
        nao 6 e 6.
        """
        curso = self.criar_curso_com(recomendacoes=3, interesses=2)

        linha = next(
            l for l in metricas.conversao_por_curso(None) if l["id"] == curso.id
        )

        self.assertEqual(linha["recomendado"], 3)
        self.assertEqual(linha["interessados"], 2)

    def test_demanda_por_area_le_o_jsonfield(self):
        """Depende da REC-03: com TextField isto nao era possivel."""
        self.criar_tentativa_com_explicacao({"eletrica": 0.6, "ti": 0.2})

        demanda = metricas.demanda_por_area(None)

        self.assertTrue(any(d["total"] >= 1 for d in demanda))

    def test_curso_inativo_nao_entra_na_conversao(self):
        """Depende da REC-02."""
        inativo = self.criar_curso(is_active=False)
        ids = [linha["id"] for linha in metricas.conversao_por_curso(None)]
        self.assertNotIn(inativo.id, ids)

    def test_cobertura_acusa_area_sem_questao(self):
        """A metrica que justifica o trabalho da F3."""
        sem_questao = [a for a in metricas.cobertura_de_areas() if a["alternativas"] == 0]
        self.assertTrue(sem_questao, "nenhuma area sem questao: confira o related_name")