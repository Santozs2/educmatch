from datetime import timedelta
from pathlib import Path

from django.urls import reverse
from django.utils import timezone

from accounts.models import Interesse
from painel import metricas
from painel.privacidade import K_MINIMO
from painel.tests.base import BasePainel
from quiz.models import Tentativa_de_resposta

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
        for tela in ("painel-dashboard", "painel-quiz"):
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
