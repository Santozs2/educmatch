from django.urls import reverse

from avaliacao.models import LinkDeAvaliacao, RespostaDeAvaliacao
from avaliacao.tests.base import BaseAvaliacao
from catalogo.models import Curso
from painel import metricas_avaliacao
from painel.privacidade import K_MINIMO
from painel.tests.test_telas import BOTOES_FANTASMA


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

    def test_poucas_respostas_nao_mostram_perguntas(self):
        self.responder(self.criar_link(self.curso), K_MINIMO - 1)

        contexto = self.client.get(reverse("painel-avaliacoes-resultados")).context

        self.assertFalse(contexto["avaliacoes_com_massa"])
        self.assertNotIn("blocos", contexto)
        linha = next(l for l in contexto["resumo"] if l["curso_id"] == self.curso.id)
        self.assertIsNone(linha["nps"])
        self.assertIsNone(linha["media"])

    def test_resultados_com_massa(self):
        link = self.criar_link(self.curso)
        self.responder(link, K_MINIMO, nota=10, escala=4, texto="Mais prática")

        contexto = self.client.get(reverse("painel-avaliacoes-resultados"), {"curso": self.curso.id}).context

        blocos = {bloco["pergunta"].tipo: bloco for bloco in contexto["blocos"]}
        self.assertEqual(blocos["nps"]["nps"], 100)
        self.assertEqual(blocos["escala"]["media"], 4)
        self.assertEqual(blocos["texto"]["textos"], ["Mais prática"] * K_MINIMO)
        opcoes = {item["rotulo"]: item for item in blocos["escolha"]["distribuicao"]}
        self.assertEqual(opcoes["Sim"]["total"], K_MINIMO)
        self.assertTrue(opcoes["Não"]["suprimido"], "zero também é menos que K")

    def test_curso_pequeno_fica_fora_do_todos(self):
        """Sem isso, NPS geral - NPS do curso grande devolveria a opinião do curso pequeno."""
        outro = Curso.objects.filter(is_active=True).exclude(pk=self.curso.pk).first()
        self.responder(self.criar_link(self.curso), K_MINIMO, nota=10)
        self.responder(self.criar_link(outro), 2, nota=0)

        contexto = self.client.get(reverse("painel-avaliacoes-resultados")).context

        nps = next(bloco for bloco in contexto["blocos"] if bloco["pergunta"].tipo == "nps")
        self.assertEqual(nps["nps"], 100)
        self.assertEqual(contexto["fora_do_todos"], 1)

    def test_nps_conta_promotores_menos_detratores(self):
        self.assertEqual(metricas_avaliacao.nps([10, 9, 8, 6]), 25)
        self.assertIsNone(metricas_avaliacao.nps([]))

    def test_csv_sai_sem_turma_data_e_em_ordem(self):
        self.responder(self.criar_link(self.curso, turma="Turma Secreta"), K_MINIMO)

        resposta = self.client.get(reverse("painel-avaliacoes-csv"))

        corpo = resposta.content.decode("utf-8-sig")
        linhas = corpo.strip().splitlines()
        self.assertEqual(linhas[0], "curso;pergunta;resposta")
        self.assertEqual(len(linhas) - 1, K_MINIMO * 6, "6 itens por resposta (o texto ficou em branco)")
        self.assertNotIn("Turma Secreta", corpo)
        # Cada pergunta num bloco só: nada na ordem liga um item ao seu vizinho de resposta.
        perguntas = [linha.split(";")[1] for linha in linhas[1:]]
        blocos = [p for i, p in enumerate(perguntas) if i == 0 or p != perguntas[i - 1]]
        self.assertEqual(len(blocos), len(set(perguntas)))

    def test_csv_com_poucas_respostas_e_negado(self):
        self.responder(self.criar_link(self.curso), K_MINIMO - 1)

        resposta = self.client.get(reverse("painel-avaliacoes-csv"))

        self.assertRedirects(resposta, reverse("painel-avaliacoes-resultados"))

    def test_kpi_na_inicio(self):
        self.responder(self.criar_link(self.curso), 2)

        contexto = self.client.get(reverse("painel-dashboard")).context

        self.assertEqual(contexto["avaliacoes_no_periodo"], 2)
        self.assertEqual(RespostaDeAvaliacao.objects.count(), 2)

    def test_telas_novas_sem_botao_fantasma(self):
        self.responder(self.criar_link(self.curso), K_MINIMO)
        for tela in ("painel-avaliacoes", "painel-avaliacoes-resultados"):
            corpo = self.client.get(reverse(tela)).content.decode()
            for classe in BOTOES_FANTASMA:
                with self.subTest(tela=tela, classe=classe):
                    self.assertNotIn(classe, corpo)