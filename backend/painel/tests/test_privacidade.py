from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse

from accounts.models import Interesse
from painel import metricas
from painel.privacidade import suprimir_pequenos
from painel.tests.base import BasePainel
from quiz.models import QuestionarioLink

# Uma quantidade qualquer de testes ou respostas. O painel mostra tudo (K_MINIMO = 0),
# então nenhum teste daqui depende da regra antiga dos 5.
ALGUNS = 5


class SupressaoTest(SimpleTestCase):
    def test_celula_pequena_e_suprimida_mas_a_linha_fica(self):
        """A função continua pronta para religar o k-anonimato (K_MINIMO = 5)."""
        linhas = [{"nome": "A", "total": 9}, {"nome": "B", "total": 2}]

        saida = suprimir_pequenos(linhas, k=5)

        self.assertEqual(len(saida), 2, "esconder a linha vazaria pela omissão")
        self.assertEqual(saida[0]["total"], 9)
        self.assertIsNone(saida[1]["total"])
        self.assertTrue(saida[1]["suprimido"])

    def test_com_k_zero_nada_e_escondido(self):
        linhas = [{"nome": "A", "total": 0}, {"nome": "B", "total": 2}]

        self.assertEqual(suprimir_pequenos(linhas), linhas)

    def test_a_funcao_nao_altera_a_entrada(self):
        linhas = [{"nome": "B", "total": 2}]
        suprimir_pequenos(linhas)
        self.assertEqual(linhas[0]["total"], 2)


class FiltroDePeriodoTest(SimpleTestCase):
    def test_periodos_suportam_diario_mensal_anual_e_mes(self):
        self.assertIn("diario", metricas.PERIODOS)
        self.assertIn("mensal", metricas.PERIODOS)
        self.assertIn("anual", metricas.PERIODOS)
        self.assertIn("mes", metricas.PERIODOS)
        self.assertEqual(metricas.PERIODOS["diario"]["dias"], 1)
        self.assertEqual(metricas.PERIODOS["mensal"]["dias"], 30)
        self.assertEqual(metricas.PERIODOS["anual"]["dias"], 365)

    def test_inicio_do_periodo_para_mes_escolhido(self):
        inicio = metricas.inicio_do_periodo("mes", mes="2024-03")
        self.assertEqual(inicio.strftime("%Y-%m"), "2024-03")


class ConfiguracaoDeHostsTest(SimpleTestCase):
    def test_hosts_padrao_permitidos_para_link_gerado(self):
        self.assertIn("localhost", settings.ALLOWED_HOSTS)
        self.assertIn("127.0.0.1", settings.ALLOWED_HOSTS)
        self.assertIn("testserver", settings.ALLOWED_HOSTS)


class AcessoAoPainelTest(BasePainel):
    def setUp(self):
        super().setUp()
        self.comum = self.criar_usuario("aluno@exemplo.com")
        self.staff = self.criar_staff()

    def test_anonimo_nao_entra(self):
        resposta = self.client.get(reverse("painel-dashboard"))
        self.assertEqual(resposta.status_code, 302)

    def test_usuario_comum_nao_entra(self):
        self.client.force_login(self.comum)
        resposta = self.client.get(reverse("painel-dashboard"))
        self.assertNotEqual(resposta.status_code, 200)

    def test_staff_entra(self):
        self.client.force_login(self.staff)
        resposta = self.client.get(reverse("painel-dashboard"))
        self.assertEqual(resposta.status_code, 200)

    def test_usuario_comum_nao_gera_link(self):
        self.client.force_login(self.comum)
        self.client.post(reverse("painel-gerar-link"))
        self.assertFalse(QuestionarioLink.objects.exists())

    def test_staff_gera_link_e_ele_aparece_no_painel(self):
        self.client.force_login(self.staff)

        resposta = self.client.post(reverse("painel-gerar-link"), follow=True)

        link = QuestionarioLink.objects.get()
        self.assertContains(resposta, str(link.token))

    def test_gerar_link_por_get_nao_faz_nada(self):
        self.client.force_login(self.staff)
        resposta = self.client.get(reverse("painel-gerar-link"))
        self.assertEqual(resposta.status_code, 405)
        self.assertFalse(QuestionarioLink.objects.exists())


class PrivacidadeNaTelaTest(BasePainel):
    TELAS = ("painel-dashboard", "painel-quiz")

    def setUp(self):
        super().setUp()
        self.staff = self.criar_staff()

    def abrir_painel(self, tela="painel-dashboard"):
        self.client.force_login(self.staff)
        return self.client.get(reverse(tela))

    def test_periodo_pequeno_mostra_tudo(self):
        self.criar_tentativas(quantidade=2)

        for tela in self.TELAS:
            with self.subTest(tela=tela):
                contexto = self.abrir_painel(tela).context
                self.assertTrue(contexto["tem_massa"])
                self.assertEqual(contexto["total_de_tentativas"], 2)
        self.assertIn("serie", self.abrir_painel("painel-dashboard").context)
        self.assertIn("confianca", self.abrir_painel("painel-quiz").context)

    def test_conversao_com_um_interesse_aparece(self):
        tentativas = self.criar_tentativas(quantidade=ALGUNS + 1)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(usuario=self.criar_usuario("um@exemplo.com"), curso=curso)

        conversao = self.abrir_painel("painel-quiz").context["conversao"]

        linha = next(l for l in conversao if l["id"] == curso.id)
        self.assertNotIn("suprimido", linha)
        self.assertEqual(linha["interessados"], 1)
        self.assertIsNotNone(linha["taxa"])

    def test_confianca_tambem_e_suprimida(self):
        self.criar_tentativas(quantidade=ALGUNS + 1)

        confianca = self.abrir_painel("painel-quiz").context["confianca"]

        for linha in confianca:
            if linha["total"] is not None:
                self.assertGreaterEqual(linha["total"], ALGUNS)

    def test_nenhum_nome_de_respondente_aparece_na_pagina(self):
        """A regra de privacidade, verificada no HTML servido."""
        nomes = ["Ana Zoraide", "Bento Kling", "Cleo Vasquez", "Dora Pimm", "Eli Nunes", "Fabi Ros"]
        self.criar_tentativas(nomes=nomes)

        for tela in self.TELAS:
            corpo = self.abrir_painel(tela).content.decode()
            for nome in nomes:
                with self.subTest(tela=tela, nome=nome):
                    self.assertNotIn(nome, corpo)