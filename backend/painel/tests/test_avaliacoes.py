from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from avaliacao.models import LinkDeAvaliacao, RespostaDeAvaliacao
from avaliacao.tests.base import BaseAvaliacao
from catalogo.models import Curso
from painel import metricas_avaliacao
from painel.tests.test_telas import BOTOES_FANTASMA

# Uma quantidade qualquer de testes ou respostas. O painel mostra tudo (K_MINIMO = 0),
# então nenhum teste daqui depende da regra antiga dos 5.
ALGUNS = 5


class AvaliacoesNoPainelTest(BaseAvaliacao):
    """Etapa 5: links por turma, resultados agregados e CSV, sempre com k = 5."""

    def setUp(self):
        super().setUp()
        self.staff = self.criar_usuario("coord@exemplo.com", is_staff=True)
        self.client.force_login(self.staff)
        self.curso = Curso.objects.filter(is_active=True).first()

    def responder(self, link, quantidade, **valores):
        """Cada resposta num navegador novo: a trava de sessão não deixa repetir no mesmo."""
        for _ in range(quantidade):
            self.client.logout()
            self.enviar(link, self.respostas_validas(**valores))
        self.client.force_login(self.staff)

    def test_so_staff_entra(self):
        comum = self.criar_usuario("aluno@exemplo.com")
        for tela in ("painel-avaliacoes", "painel-avaliacoes-resultados", "painel-avaliacoes-csv"):
            with self.subTest(tela=tela):
                self.client.force_login(comum)
                self.assertNotEqual(self.client.get(reverse(tela)).status_code, 200)

    def test_gerar_link_para_turma(self):
        resposta = self.client.post(
            reverse("painel-avaliacoes-gerar"), {"curso": self.curso.id, "turma": "2026/1 · Noite"}
        )

        self.assertRedirects(resposta, reverse("painel-avaliacoes"))
        link = LinkDeAvaliacao.objects.get()
        self.assertEqual((link.curso, link.turma, link.criado_por), (self.curso, "2026/1 · Noite", self.staff))

    def test_curso_inativo_nao_ganha_link(self):
        inativo = Curso.objects.create(
            nome_curso="Antigo", descricao="-", area_principal=self.curso.area_principal, duracao=10, is_active=False
        )

        self.client.post(reverse("painel-avaliacoes-gerar"), {"curso": inativo.id, "turma": "X"})

        self.assertFalse(LinkDeAvaliacao.objects.exists())

    def test_fechar_link_de_avaliacao(self):
        link = self.criar_link(self.curso)

        self.client.post(reverse("painel-avaliacoes-fechar", args=[link.pk]))

        link.refresh_from_db()
        self.assertFalse(link.ativo)

    def test_poucas_respostas_ja_mostram_tudo(self):
        self.responder(self.criar_link(self.curso), 2, nota=10)

        contexto = self.client.get(reverse("painel-avaliacoes-resultados")).context

        self.assertTrue(contexto["avaliacoes_com_massa"])
        self.assertIn("blocos", contexto)
        linha = next(l for l in contexto["resumo"] if l["curso_id"] == self.curso.id)
        self.assertEqual((linha["total"], linha["nps"]), (2, 100))

    def test_resultados_ignoram_filtro_de_periodo(self):
        link = self.criar_link(self.curso)
        self.responder(link, 2, nota=10)
        RespostaDeAvaliacao.objects.filter(link=link).update(
            respondido_em=timezone.localdate() - timedelta(days=40)
        )

        resposta = self.client.get(reverse("painel-avaliacoes-resultados"), {"periodo": "diario"})

        linha = next(linha for linha in resposta.context["resumo"] if linha["curso_id"] == self.curso.id)
        self.assertEqual(linha["total"], 2)
        self.assertContains(resposta, "Histórico completo")
        self.assertNotContains(resposta, "Aplicar")

    def test_lista_de_avaliacoes_nao_exibe_filtro_de_periodo(self):
        resposta = self.client.get(reverse("painel-avaliacoes"), {"periodo": "anual"})

        self.assertContains(resposta, "Histórico completo")
        self.assertNotContains(resposta, "Aplicar")

    def test_resultados_e_links_das_turmas_tem_navegacao_de_ida_e_volta(self):
        links = self.client.get(reverse("painel-avaliacoes"))
        resultados = self.client.get(reverse("painel-avaliacoes-resultados"))

        self.assertContains(links, f'href="{reverse("painel-avaliacoes-resultados")}?')
        self.assertContains(resultados, f'href="{reverse("painel-avaliacoes")}"')

    def test_resultados_por_pergunta(self):
        link = self.criar_link(self.curso)
        self.responder(link, ALGUNS, nota=10, escala=4, texto="Mais prática")

        contexto = self.client.get(reverse("painel-avaliacoes-resultados"), {"curso": self.curso.id}).context

        blocos = {bloco["pergunta"].tipo: bloco for bloco in contexto["blocos"]}
        self.assertEqual(blocos["nps"]["nps"], 100)
        self.assertEqual(blocos["escala"]["media"], 4)
        self.assertEqual(blocos["texto"]["textos"], ["Mais prática"] * ALGUNS)
        opcoes = {item["rotulo"]: item for item in blocos["escolha"]["distribuicao"]}
        self.assertEqual(opcoes["Sim"]["total"], ALGUNS)
        self.assertEqual(opcoes["Não"]["total"], 0, "o zero aparece como zero, sem cadeado")

    def test_todos_os_cursos_entram_no_todos(self):
        outro = Curso.objects.filter(is_active=True).exclude(pk=self.curso.pk).first()
        self.responder(self.criar_link(self.curso), ALGUNS, nota=10)
        self.responder(self.criar_link(outro), 2, nota=0)

        contexto = self.client.get(reverse("painel-avaliacoes-resultados")).context

        nps = next(bloco for bloco in contexto["blocos"] if bloco["pergunta"].tipo == "nps")
        self.assertEqual(nps["nps"], 43, "5 promotores e 2 detratores em 7: (5 - 2) / 7 = 43")
        self.assertEqual(contexto["fora_do_todos"], 0)

    def test_nps_conta_promotores_menos_detratores(self):
        self.assertEqual(metricas_avaliacao.nps([10, 9, 8, 6]), 25)
        self.assertIsNone(metricas_avaliacao.nps([]))

    def test_csv_sai_sem_turma_data_e_em_ordem(self):
        self.responder(self.criar_link(self.curso, turma="Turma Secreta"), ALGUNS)

        resposta = self.client.get(reverse("painel-avaliacoes-csv"))

        corpo = resposta.content.decode("utf-8-sig")
        linhas = corpo.strip().splitlines()
        self.assertEqual(linhas[0], "curso;pergunta;resposta")
        self.assertEqual(len(linhas) - 1, ALGUNS * 6, "6 itens por resposta (o texto ficou em branco)")
        self.assertNotIn("Turma Secreta", corpo)
        # Cada pergunta num bloco só: nada na ordem liga um item ao seu vizinho de resposta.
        perguntas = [linha.split(";")[1] for linha in linhas[1:]]
        blocos = [p for i, p in enumerate(perguntas) if i == 0 or p != perguntas[i - 1]]
        self.assertEqual(len(blocos), len(set(perguntas)))

    def test_csv_sem_nenhuma_resposta_volta_com_aviso(self):
        resposta = self.client.get(reverse("painel-avaliacoes-csv"))

        self.assertRedirects(resposta, reverse("painel-avaliacoes-resultados"))

    def test_kpi_na_inicio(self):
        self.responder(self.criar_link(self.curso), 2)

        contexto = self.client.get(reverse("painel-dashboard")).context

        self.assertEqual(contexto["avaliacoes_no_periodo"], 2)
        self.assertEqual(RespostaDeAvaliacao.objects.count(), 2)

    def test_telas_novas_sem_botao_fantasma(self):
        self.responder(self.criar_link(self.curso), ALGUNS)
        for tela in ("painel-avaliacoes", "painel-avaliacoes-resultados"):
            corpo = self.client.get(reverse(tela)).content.decode()
            for classe in BOTOES_FANTASMA:
                with self.subTest(tela=tela, classe=classe):
                    self.assertNotIn(classe, corpo)