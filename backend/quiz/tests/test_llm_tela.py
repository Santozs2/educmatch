from django.test import override_settings

from quiz.models import Recomendacao, Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch

SELO = "Texto escrito com IA"


class TelaDeEntregaTest(BaseEducMatch):
    """Passo 10: a tela mostra o texto da LLM sem esconder a engine."""

    def resultado(self):
        resposta = self.responder_tudo()
        return Tentativa_de_resposta.objects.latest("id"), self.client.get(resposta.url)

    @override_settings(LLM_ENABLED=False)
    def test_sem_llm_a_tela_e_a_da_engine(self):
        tentativa, pagina = self.resultado()

        self.assertEqual(pagina.status_code, 200)
        self.assertContains(pagina, 'data-entrega="engine"')
        self.assertNotContains(pagina, SELO)
        self.assertContains(pagina, "Por que este curso?")
        self.assertEqual(len(pagina.context["outros"]) + 1, tentativa.recomendacoes.count())

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
    def test_com_llm_mostra_os_textos_e_o_selo(self):
        tentativa, pagina = self.resultado()

        self.assertContains(pagina, 'data-entrega="ia"')
        self.assertContains(pagina, SELO, count=1)
        for rec in tentativa.recomendacoes.all():
            with self.subTest(curso=rec.curso_id):
                self.assertContains(pagina, rec.llm_text)
        # A engine continua na tela: a banca quer ver o número por trás da frase.
        self.assertContains(pagina, "Por que este curso?")
        self.assertContains(pagina, "de afinidade")

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
    def test_destaque_e_o_principal_entregue_com_o_texto_dele(self):
        self.responder_tudo()
        tentativa = Tentativa_de_resposta.objects.latest("id")
        primeiro = tentativa.recomendacoes.get(rank_engine=1)
        segundo = tentativa.recomendacoes.get(rank_engine=2)
        primeiro.rank_final, segundo.rank_final = 2, 1
        segundo.llm_text = "Este é o texto do novo principal."
        Recomendacao.objects.bulk_update([primeiro, segundo], ["rank_final", "llm_text"])

        pagina = self.client.get(f"/resultado/{tentativa.pk}/")

        self.assertEqual(pagina.context["destaque"]["curso"], segundo.curso)
        self.assertEqual(pagina.context["destaque"]["texto"], "Este é o texto do novo principal.")

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="fake", LLM_PROMPT_VERSION="v1")
    def test_texto_da_llm_e_escapado(self):
        self.responder_tudo()
        tentativa = Tentativa_de_resposta.objects.latest("id")
        tentativa.recomendacoes.filter(rank_final=1).update(llm_text='<script>alert("x")</script>')

        pagina = self.client.get(f"/resultado/{tentativa.pk}/")

        self.assertNotContains(pagina, '<script>alert("x")</script>')
        self.assertContains(pagina, "&lt;script&gt;")

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="gemini", LLM_BASE_URL="", LLM_MODEL="")
    def test_no_fallback_a_tela_volta_a_ser_a_da_engine(self):
        # gemini sem modelo: o provedor nem monta, e a camada cai na engine.
        with self.assertLogs("quiz.delivery", "WARNING"):
            tentativa, pagina = self.resultado()

        self.assertTrue(tentativa.used_fallback)
        self.assertContains(pagina, 'data-entrega="engine"')
        self.assertNotContains(pagina, SELO)
