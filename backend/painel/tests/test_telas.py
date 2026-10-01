from datetime import timedelta
from pathlib import Path

from django.urls import reverse
from django.utils import timezone

from accounts.models import Interesse
from painel import metricas
from painel.privacidade import K_MINIMO
from painel.tests.base import BasePainel
from quiz.models import QuestionarioLink, Tentativa_de_resposta


PASTA_DE_TEMPLATES = Path(__file__).resolve().parents[1] / "templates" / "painel"
BOTOES_FANTASMA = ("botao--contorno", "botao--texto", "botao--fantasma")


class CascaDoPainelTest(BasePainel):
    """Etapa 1: menu, período e a regra de nenhum botão fantasma."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.criar_staff())

    def test_menu_leva_o_periodo_escolhido(self):
        resposta = self.client.get(reverse("painel-dashboard"), {"periodo": "anual"})

        self.assertContains(resposta, 'href="/painel/quiz/?periodo=anual"')

    def test_periodo_invalido_cai_no_mensal(self):
        resposta = self.client.get(reverse("painel-quiz"), {"periodo": "semanal"})

        self.assertEqual(resposta.context["periodo"], "mensal")

    def test_menu_marca_a_tela_atual(self):
        resposta = self.client.get(reverse("painel-quiz"))

        self.assertContains(resposta, 'href="/painel/quiz/?periodo=mensal" aria-current="page"')

    def test_nenhum_template_do_painel_usa_botao_fantasma(self):
        for arquivo in PASTA_DE_TEMPLATES.glob("*.html"):
            texto = arquivo.read_text(encoding="utf-8")
            for classe in BOTOES_FANTASMA:
                with self.subTest(arquivo=arquivo.name, classe=classe):
                    self.assertNotIn(classe, texto)

    def test_tela_servida_tambem_nao_tem_botao_fantasma(self):
        self.criar_tentativas(quantidade=K_MINIMO)
        for tela in ("painel-dashboard", "painel-quiz", "painel-cursos", "painel-links", "painel-interesse"):
            corpo = self.client.get(reverse(tela)).content.decode()
            for classe in BOTOES_FANTASMA:
                with self.subTest(tela=tela, classe=classe):
                    self.assertNotIn(classe, corpo)


class MetricasDoInicioTest(BasePainel):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.criar_staff())

    def test_dia_com_poucos_testes_some_da_serie(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO + 2)
        ontem = timezone.now() - timedelta(days=1)
        Tentativa_de_resposta.objects.filter(pk__in=[t.pk for t in tentativas[:2]]).update(criado_em=ontem)

        serie = self.client.get(reverse("painel-dashboard")).context["serie"]

        self.assertEqual([linha["total"] for linha in serie], [None, K_MINIMO])

    def test_atividade_recente_tambem_e_suprimida(self):
        self.criar_tentativas(quantidade=K_MINIMO)

        atividade = self.client.get(reverse("painel-dashboard")).context["atividade"]

        testes_na_hora, _, cursos_salvos = atividade
        self.assertEqual(testes_na_hora["total"], K_MINIMO)
        self.assertIsNone(cursos_salvos["total"], "zero cursos salvos é menos que K")

    def test_conversao_geral_some_com_poucos_interesses(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(usuario=self.criar_usuario("um@exemplo.com"), curso=curso)

        self.assertIsNone(metricas.conversao_geral(None))

    def test_conversao_geral_e_salvos_sobre_recomendados(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        for i in range(K_MINIMO):
            Interesse.objects.create(usuario=self.criar_usuario(f"aluno{i}@exemplo.com"), curso=curso)

        recomendacoes = sum(t.recomendacoes.count() for t in tentativas)
        self.assertAlmostEqual(metricas.conversao_geral(None), K_MINIMO / recomendacoes * 100)

    def test_aderencia_some_com_poucos_primeiros(self):
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        Interesse.objects.create(
            usuario=self.criar_usuario("um@exemplo.com"), curso=curso, rank_snapshot=1, era_principal=True
        )

        aderencia = self.client.get(reverse("painel-quiz")).context["aderencia"]

        self.assertIsNone(aderencia["taxa"])

class TelasDeCadastroTest(BasePainel):
    """Etapa 2: Cursos e Áreas, Links de acesso e Lista de interesse."""

    TELAS = ("painel-cursos", "painel-links", "painel-interesse")

    def setUp(self):
        super().setUp()
        self.staff = self.criar_staff()

    def test_so_staff_entra(self):
        comum = self.criar_usuario("aluno@exemplo.com")
        for tela in self.TELAS:
            with self.subTest(tela=tela):
                self.client.logout()
                self.assertEqual(self.client.get(reverse(tela)).status_code, 302)
                self.client.force_login(comum)
                self.assertNotEqual(self.client.get(reverse(tela)).status_code, 200)
                self.client.force_login(self.staff)
                self.assertEqual(self.client.get(reverse(tela)).status_code, 200)

    def test_testes_por_link_sao_suprimidos(self):
        self.client.force_login(self.staff)
        link = QuestionarioLink.objects.create(criado_por=self.staff)
        tentativas = self.criar_tentativas(quantidade=2)
        Tentativa_de_resposta.objects.filter(pk__in=[t.pk for t in tentativas]).update(questionario_link=link)

        linhas = self.client.get(reverse("painel-links")).context["links"]

        self.assertTrue(linhas[0]["suprimido"])
        self.assertIsNone(linhas[0]["total"])

    def test_fechar_um_link_nao_fecha_os_outros(self):
        self.client.force_login(self.staff)
        primeiro, segundo = (QuestionarioLink.objects.create(criado_por=self.staff) for _ in range(2))

        resposta = self.client.post(
            reverse("painel-fechar-um-link", args=[primeiro.pk]), {"voltar": "painel-links"}
        )

        self.assertRedirects(resposta, reverse("painel-links"))
        primeiro.refresh_from_db()
        segundo.refresh_from_db()
        self.assertFalse(primeiro.ativo)
        self.assertTrue(segundo.ativo)

    def test_voltar_para_endereco_de_fora_cai_no_inicio(self):
        self.client.force_login(self.staff)

        resposta = self.client.post(reverse("painel-gerar-link"), {"voltar": "https://exemplo.com/"})

        self.assertRedirects(resposta, reverse("painel-dashboard"))

    def test_lista_de_interesse_nao_mostra_quem_salvou(self):
        self.client.force_login(self.staff)
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        emails = [f"pessoa{i}@exemplo.com" for i in range(K_MINIMO)]
        for email in emails:
            Interesse.objects.create(usuario=self.criar_usuario(email), curso=curso, era_principal=True)

        resposta = self.client.get(reverse("painel-interesse"))

        linha = next(l for l in resposta.context["por_curso"] if l["id"] == curso.id)
        self.assertEqual(linha["total"], K_MINIMO)
        self.assertEqual(linha["taxa_principal"], 100)
        for email in emails:
            self.assertNotContains(resposta, email)

    def test_taxa_de_1o_colocado_some_se_a_contagem_for_pequena(self):
        self.client.force_login(self.staff)
        tentativas = self.criar_tentativas(quantidade=K_MINIMO)
        curso = tentativas[0].recomendacoes.get(rank_final=1).curso
        for i in range(K_MINIMO):
            Interesse.objects.create(
                usuario=self.criar_usuario(f"pessoa{i}@exemplo.com"), curso=curso, era_principal=(i == 0)
            )

        linhas = self.client.get(reverse("painel-interesse")).context["por_curso"]

        linha = next(l for l in linhas if l["id"] == curso.id)
        self.assertTrue(linha["principal_suprimido"])
        self.assertIsNone(linha["taxa_principal"])

    def test_funil_segue_a_ordem_dos_status(self):
        self.client.force_login(self.staff)
        self.criar_tentativas(quantidade=K_MINIMO)

        funil = self.client.get(reverse("painel-interesse")).context["funil"]

        self.assertEqual([etapa["status"] for etapa in funil], [chave for chave, _ in Interesse.STATUS])