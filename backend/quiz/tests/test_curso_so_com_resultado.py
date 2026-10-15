from django.urls import reverse

from accounts.models import Interesse
from catalogo.models import Curso
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class CursoSoComResultadoTest(BaseEducMatch):
    """O detalhe do curso só abre a partir de um resultado que a pessoa pode ver."""

    def responder(self):
        self.responder_tudo()
        return Tentativa_de_resposta.objects.latest("id")

    def detalhe(self, curso_id, tentativa=None):
        url = reverse("curso-detalhe", args=[curso_id])
        return self.client.get(url if tentativa is None else f"{url}?tentativa={tentativa}")

    def test_sem_resultado_volta_para_o_inicio_do_quiz(self):
        tentativa = self.responder()
        curso_id = tentativa.recomendacoes.get(rank_final=1).curso_id

        for tentativa_na_url in (None, "", "abc", "999999"):
            with self.subTest(tentativa=tentativa_na_url):
                resposta = self.detalhe(curso_id, tentativa_na_url)
                self.assertRedirects(resposta, reverse("quiz-inicio"), fetch_redirect_response=False)

    def test_curso_fora_do_resultado_volta_para_o_resultado(self):
        tentativa = self.responder()
        no_resultado = set(tentativa.recomendacoes.values_list("curso_id", flat=True))
        fora = Curso.objects.filter(is_active=True).exclude(pk__in=no_resultado).first()

        resposta = self.detalhe(fora.pk, tentativa.pk)

        self.assertRedirects(resposta, reverse("quiz-resultado", args=[tentativa.pk]), fetch_redirect_response=False)

    def test_com_resultado_abre_com_a_afinidade_e_o_voltar(self):
        tentativa = self.responder()
        rec = tentativa.recomendacoes.get(rank_final=2)

        resposta = self.detalhe(rec.curso_id, tentativa.pk)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["afinidade"], round(rec.score * 100))
        self.assertContains(resposta, "Voltar para o meu resultado")


class ListaLevaAoResultadoTest(BaseEducMatch):
    """Minha lista e Meu perfil abrem o curso com o resultado de onde ele foi salvo."""

    def setUp(self):
        super().setUp()
        self.usuario = self.criar_usuario()
        self.client.force_login(self.usuario)
        self.responder_tudo()
        self.tentativa = Tentativa_de_resposta.objects.latest("id")
        self.rec = self.tentativa.recomendacoes.get(rank_final=1)

    def test_link_leva_o_resultado_de_origem(self):
        self.client.post(reverse("interesse-salvar"), {"curso_id": self.rec.curso_id, "tentativa_id": self.tentativa.pk})
        esperado = reverse("curso-detalhe", args=[self.rec.curso_id]) + f"?tentativa={self.tentativa.pk}"

        for tela in ("lista_interesse", "aluno-perfil"):
            with self.subTest(tela=tela):
                self.assertContains(self.client.get(reverse(tela)), esperado)

    def test_interesse_sem_origem_aparece_sem_link(self):
        Interesse.objects.create(usuario=self.usuario, curso=self.rec.curso)

        resposta = self.client.get(reverse("lista_interesse"))

        self.assertContains(resposta, self.rec.curso.nome_curso)
        self.assertNotContains(resposta, reverse("curso-detalhe", args=[self.rec.curso_id]))

    def test_remover_sem_resultado_volta_para_a_lista(self):
        Interesse.objects.create(usuario=self.usuario, curso=self.rec.curso)

        resposta = self.client.post(reverse("interesse-remover"), {"curso_id": self.rec.curso_id})

        self.assertRedirects(resposta, reverse("lista_interesse"), fetch_redirect_response=False)
