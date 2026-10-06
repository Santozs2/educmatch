from django.urls import reverse

from accounts.models import Interesse
from catalogo.models import Curso
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class TodaPaginaAbreTest(BaseEducMatch):
    """Smoke test das telas: toda página abre (200) e usa o CSS novo.

    Pega erro de template que nenhum outro teste pega, como um include que se
    chama a si mesmo ou uma variável com nome errado.
    """

    def abrir(self, url):
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200, url)
        self.assertContains(resposta, "css/tokens.css", msg_prefix=url)
        return resposta

    def test_paginas_publicas(self):
        self.responder_tudo()
        tentativa = Tentativa_de_resposta.objects.latest("id")
        curso = Curso.objects.filter(is_active=True).first()

        for url in (
            reverse("quiz-inicio"),
            reverse("quiz-resultado", args=[tentativa.pk]),
            reverse("curso-detalhe", args=[curso.pk]),
            reverse("entrar"),
            reverse("cadastro_usuario"),
        ):
            with self.subTest(url=url):
                self.abrir(url)

    def test_paginas_da_conta(self):
        self.client.force_login(self.criar_usuario())
        self.responder_tudo()

        for url in (
            reverse("lista_interesse"),
            reverse("minhas-tentativas"),
            reverse("aluno-perfil"),
        ):
            with self.subTest(url=url):
                self.abrir(url)

    def test_perfil_carrega_lista_de_interesse(self):
        usuario = self.criar_usuario()
        self.client.force_login(usuario)
        curso = Curso.objects.filter(is_active=True).first()
        Interesse.objects.create(usuario=usuario, curso=curso)

        resposta = self.client.get(reverse("aluno-perfil"))

        self.assertIn("interesses", resposta.context)
        self.assertEqual(len(resposta.context["interesses"]), 1)
        self.assertContains(resposta, curso.nome_curso)

    def test_painel_para_staff(self):
        self.client.force_login(self.criar_usuario("coord@exemplo.com", is_staff=True))
        self.abrir(reverse("painel-dashboard"))

    def test_nenhuma_pagina_usa_o_css_antigo(self):
        self.responder_tudo()
        for url in (reverse("quiz-inicio"), reverse("entrar")):
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), "css/style.css")