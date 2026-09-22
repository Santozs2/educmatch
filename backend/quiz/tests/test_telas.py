import uuid

from django.urls import reverse

from catalogo.models import Curso
from quiz.models import QuestionarioLink, Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class TelasDoAlunoTest(BaseEducMatch):
    def responder(self, **kwargs):
        self.responder_tudo(**kwargs)
        return Tentativa_de_resposta.objects.latest("id")

    def test_aviso_de_baixa_confianca_aparece(self):
        """O template testava `confidence_level`, que não existe: o aviso nunca aparecia."""
        tentativa = self.responder()
        Tentativa_de_resposta.objects.filter(pk=tentativa.pk).update(confidence_band="baixa")

        resposta = self.client.get(reverse("quiz-resultado", args=[tentativa.pk]))

        self.assertContains(resposta, "afinidade com os cursos disponiveis ficou baixa")

    def test_resultado_leva_ao_detalhe_do_curso(self):
        tentativa = self.responder()
        primeiro = tentativa.recomendacoes.get(rank=1).curso

        resposta = self.client.get(reverse("quiz-resultado", args=[tentativa.pk]))

        destino = reverse("curso-detalhe", args=[primeiro.pk]) + f"?tentativa={tentativa.pk}"
        self.assertContains(resposta, destino)

    def test_detalhe_do_curso_mostra_o_curso_e_volta_ao_resultado(self):
        curso = Curso.objects.first()

        resposta = self.client.get(reverse("curso-detalhe", args=[curso.pk]) + "?tentativa=7")

        self.assertContains(resposta, curso.nome_curso)
        self.assertContains(resposta, reverse("quiz-resultado", args=[7]))

    def test_curso_desativado_nao_tem_pagina(self):
        curso = Curso.objects.first()
        Curso.objects.filter(pk=curso.pk).update(is_active=False)

        resposta = self.client.get(reverse("curso-detalhe", args=[curso.pk]))

        self.assertEqual(resposta.status_code, 404)

    def test_perfil_so_mostra_numeros_que_o_sistema_mede(self):
        usuario = self.criar_usuario()
        self.client.force_login(usuario)
        self.responder()

        resposta = self.client.get(reverse("aluno-perfil"))

        self.assertNotIn("estatisticas", resposta.context)
        self.assertEqual(resposta.context["total_de_testes"], 1)
        self.assertEqual(resposta.context["total_na_lista"], 0)

    def test_link_de_questionario_inexistente_tem_pagina_propria(self):
        resposta = self.client.get(reverse("questionario-link", args=[uuid.uuid4()]))

        self.assertEqual(resposta.status_code, 404)
        self.assertContains(resposta, "não existe ou foi encerrado", status_code=404)

    def test_quem_entra_pelo_link_ve_o_aviso(self):
        link = QuestionarioLink.objects.create()

        self.client.get(reverse("questionario-link", args=[link.token]))
        resposta = self.client.get(reverse("quiz-inicio"))

        self.assertContains(resposta, "link da escola")