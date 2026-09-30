from accounts.servicos import registrar_interesse
from quiz.tests.base import BaseEducMatch


class RankFinalTest(BaseEducMatch):
    """PRE-01: a ordem da engine e a ordem entregue são colunas separadas."""

    def test_sem_llm_a_ordem_entregue_e_a_da_engine(self):
        tentativa = self.criar_tentativa()
        for rec in tentativa.recomendacoes.all():
            with self.subTest(curso=rec.curso_id):
                self.assertEqual(rec.rank_final, rec.rank_engine)

    def test_principal_e_o_primeiro_entregue(self):
        tentativa = self.criar_tentativa()
        principais = [rec for rec in tentativa.recomendacoes.all() if rec.is_primary]
        self.assertEqual(len(principais), 1)
        self.assertEqual(principais[0].rank_final, 1)

    def test_snapshot_segue_a_ordem_entregue_e_guarda_a_da_engine(self):
        """Simula a LLM trocando o 1º e o 2º lugar."""
        tentativa = self.criar_tentativa()
        primeiro = tentativa.recomendacoes.get(rank_engine=1)
        segundo = tentativa.recomendacoes.get(rank_engine=2)
        primeiro.rank_final, segundo.rank_final = 2, 1
        primeiro.save(update_fields=["rank_final"])
        segundo.save(update_fields=["rank_final"])

        interesse, _ = registrar_interesse(self.criar_usuario(), segundo.curso, tentativa)

        self.assertEqual(interesse.rank_snapshot, 1)
        self.assertEqual(interesse.rank_engine_snapshot, 2)
        self.assertTrue(interesse.era_principal)

    def test_resultado_mostra_a_ordem_entregue(self):
        self.responder_tudo()
        from quiz.models import Tentativa_de_resposta

        tentativa = Tentativa_de_resposta.objects.latest("id")
        primeiro = tentativa.recomendacoes.get(rank_engine=1)
        segundo = tentativa.recomendacoes.get(rank_engine=2)
        primeiro.rank_final, segundo.rank_final = 2, 1
        primeiro.save(update_fields=["rank_final"])
        segundo.save(update_fields=["rank_final"])

        resposta = self.client.get(f"/resultado/{tentativa.pk}/")

        self.assertEqual(resposta.context["destaque"]["curso"], segundo.curso)
