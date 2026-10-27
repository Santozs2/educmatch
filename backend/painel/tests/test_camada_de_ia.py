from accounts.models import Interesse
from painel import metricas
from painel.tests.base import BasePainel


class CamadaDeIATest(BasePainel):
    """Passo 11: as métricas da LLM no painel, calculadas pelo servidor."""

    def tentativa(self, **metadados):
        tentativa = self.criar_tentativa()
        for campo, valor in metadados.items():
            setattr(tentativa, campo, valor)
        tentativa.save()
        return tentativa

    def cenario(self):
        trocou = self.tentativa(llm_model="m", diverged=True, latency_ms=1000, tokens_in=900, tokens_out=300)
        self.tentativa(llm_model="m", cache_hit=True, reordered_alternatives=True, latency_ms=5)
        self.tentativa(llm_model="m", used_fallback=True, latency_ms=8000)
        self.tentativa()  # LLM desligada: não conta
        return trocou

    def test_sem_chamadas_nao_ha_bloco(self):
        self.tentativa()
        self.assertIsNone(metricas.camada_de_ia(None))

    def test_taxas_e_mediana(self):
        self.cenario()

        ia = metricas.camada_de_ia(None)

        self.assertEqual(ia["chamadas"], 3)
        self.assertAlmostEqual(ia["fallback"], 100 / 3)
        self.assertEqual(ia["divergencia"], 50)  # 1 das 2 entregas
        self.assertEqual(ia["alternativas_reordenadas"], 50)
        self.assertEqual(ia["cache"], 50)
        self.assertEqual(ia["latencia_mediana"], 4500)  # 1000 e 8000: o cache fica de fora
        self.assertEqual((ia["tokens_entrada"], ia["tokens_saida"]), (900, 300))

    def test_qual_primeiro_o_aluno_salvou_quando_houve_troca(self):
        trocou = self.cenario()
        cursos = list(trocou.recomendacoes.order_by("rank_engine"))
        Interesse.objects.create(usuario=self.criar_usuario("a@exemplo.com"), curso=cursos[1].curso,
                                 tentativa_origem=trocou, rank_snapshot=1, rank_engine_snapshot=2)
        Interesse.objects.create(usuario=self.criar_usuario("b@exemplo.com"), curso=cursos[0].curso,
                                 tentativa_origem=trocou, rank_snapshot=2, rank_engine_snapshot=1)

        ia = metricas.camada_de_ia(None)

        self.assertEqual((ia["seguiu_ia"], ia["seguiu_engine"]), (1, 1))

    def test_tela_quiz_mostra_o_bloco_so_com_dados(self):
        self.client.force_login(self.criar_staff())
        self.tentativa()
        self.assertNotContains(self.client.get("/painel/quiz/?periodo=anual"), "Camada de IA")

        self.cenario()
        self.assertContains(self.client.get("/painel/quiz/?periodo=anual"), "Camada de IA")
