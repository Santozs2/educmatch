from datetime import timedelta

from django.urls import reverse

from painel import metricas
from painel.privacidade import K_MINIMO
from painel.templatetags.painel_extras import duracao
from quiz.models import InicioDeQuiz, Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class InicioDoQuizTest(BaseEducMatch):
    """Etapa 3: o início do quiz é contado uma vez e vira iniciado_em na tentativa."""

    def comecar(self, nome="Visitante"):
        return self.client.get(reverse("quiz-inicio"), {"respondido_por": nome, "etapa": 1})

    def test_abrir_a_primeira_questao_conta_um_inicio(self):
        self.comecar()

        self.assertEqual(InicioDeQuiz.objects.count(), 1)

    def test_recarregar_nao_conta_de_novo(self):
        self.comecar()
        self.comecar()

        self.assertEqual(InicioDeQuiz.objects.count(), 1)

    def test_concluir_grava_o_inicio_na_tentativa_e_limpa_a_sessao(self):
        self.comecar()
        inicio = InicioDeQuiz.objects.get()

        self.responder_tudo()

        tentativa = Tentativa_de_resposta.objects.get()
        self.assertEqual(tentativa.iniciado_em, inicio.criado_em)
        self.assertNotIn("quiz_iniciado_em", self.client.session)

    def test_proximo_quiz_conta_outro_inicio(self):
        self.comecar()
        self.responder_tudo()
        self.comecar()

        self.assertEqual(InicioDeQuiz.objects.count(), 2)

    def test_post_direto_fica_sem_inicio(self):
        self.responder_tudo()

        self.assertIsNone(Tentativa_de_resposta.objects.get().iniciado_em)

    def test_inicio_nao_guarda_quem_comecou(self):
        campos = {campo.name for campo in InicioDeQuiz._meta.get_fields()}

        self.assertEqual(campos, {"id", "criado_em", "questionario_link"})


class MetricasDeConclusaoTest(BaseEducMatch):
    def concluir(self, quantidade, minutos=8):
        for _ in range(quantidade):
            tentativa = self.criar_tentativa()
            tentativa.iniciado_em = tentativa.criado_em - timedelta(minutes=minutos)
            tentativa.save(update_fields=["iniciado_em"])

    def test_taxa_de_conclusao(self):
        for _ in range(K_MINIMO * 2):
            InicioDeQuiz.objects.create()
        self.concluir(K_MINIMO)

        self.assertEqual(metricas.taxa_de_conclusao(None), 50.0)

    def test_taxa_some_com_poucos_inicios(self):
        InicioDeQuiz.objects.create()

        self.assertIsNone(metricas.taxa_de_conclusao(None))

    def test_tempo_tipico_e_a_mediana(self):
        self.concluir(K_MINIMO - 1, minutos=8)
        self.concluir(1, minutos=60 * 24)  # aba esquecida aberta por um dia

        self.assertEqual(metricas.tempo_tipico(None), timedelta(minutes=8))

    def test_tempo_some_com_poucas_tentativas(self):
        self.concluir(K_MINIMO - 1)

        self.assertIsNone(metricas.tempo_tipico(None))

    def test_formato_da_duracao(self):
        self.assertEqual(duracao(timedelta(minutes=8, seconds=42)), "08:42")
        self.assertEqual(duracao(timedelta(hours=1, minutes=5)), "1h05")