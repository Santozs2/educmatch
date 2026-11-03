from importlib import import_module
from io import StringIO

from unittest.mock import patch

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse
from django.utils.html import escape

from accounts.models import Interesse
from accounts.servicos import registrar_interesse
from avaliacao.models import ItemDeResposta, LinkDeAvaliacao, Pergunta, RespostaDeAvaliacao
from avaliacao.tests.base import BaseAvaliacao
from catalogo.management.commands.seed_cursos import ler_cursos
from catalogo.models import Area, Curso
from catalogo.servicos import url_curso_senai
from quiz.engine import perfil_vetor
from quiz.models import Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class AvaliacoesNoDetalheDoCursoTest(BaseAvaliacao):
	def abrir_detalhe(self):
		self.responder_tudo()
		tentativa = Tentativa_de_resposta.objects.latest("id")
		curso = tentativa.recomendacoes.get(rank_final=1).curso
		resposta = self.client.get(
			reverse("curso-detalhe", args=[curso.pk]), {"tentativa": tentativa.pk}
		)
		return curso, resposta

	def adicionar_avaliacao(self, link, nota, recomendacao, comentario):
		resposta = RespostaDeAvaliacao.objects.create(link=link)
		itens = []
		for pergunta in Pergunta.objects.filter(ativa=True):
			if pergunta.tipo == "escala":
				itens.append(ItemDeResposta(resposta=resposta, pergunta=pergunta, numero=nota))
			elif pergunta.tipo == "nps":
				itens.append(ItemDeResposta(resposta=resposta, pergunta=pergunta, numero=recomendacao))
			elif pergunta.tipo == "escolha":
				itens.append(ItemDeResposta(resposta=resposta, pergunta=pergunta, texto="Sim"))
			elif pergunta.tipo == "texto" and comentario:
				itens.append(ItemDeResposta(resposta=resposta, pergunta=pergunta, texto=comentario))
		ItemDeResposta.objects.bulk_create(itens)

	def test_detalhe_mostra_zero_quando_nao_ha_avaliacoes(self):
		_, resposta = self.abrir_detalhe()

		self.assertEqual(resposta.context["media_avaliacoes"], 0)
		self.assertContains(resposta, "0 <small>/ 5</small>")

	def test_detalhe_mostra_somente_a_media_geral(self):
		curso, _ = self.abrir_detalhe()
		link = LinkDeAvaliacao.objects.create(curso=curso, turma="Turma não exibida")
		self.adicionar_avaliacao(link, nota=5, recomendacao=10, comentario="Mais aulas práticas")
		self.adicionar_avaliacao(link, nota=3, recomendacao=8, comentario="Mais equipamentos")

		_, resposta = self.abrir_detalhe()

		self.assertEqual(resposta.context["media_avaliacoes"], 4)
		self.assertContains(resposta, "4,0")
		self.assertNotContains(resposta, "Média de recomendação")
		self.assertNotContains(resposta, "Mais aulas práticas")
		self.assertNotContains(resposta, "Mais equipamentos")
		self.assertNotContains(resposta, "Turma não exibida")


class BotaoDeInscricaoTest(BaseEducMatch):
	def abrir_detalhe(self, salvo, nivel="livre"):
		usuario = self.criar_usuario()
		self.client.force_login(usuario)
		tentativa = self.criar_tentativa(dono=usuario)
		curso = tentativa.recomendacoes.get(rank_final=1).curso
		Curso.objects.filter(pk=curso.pk).update(nivel=nivel)
		curso.refresh_from_db()
		if salvo:
			registrar_interesse(usuario, curso, tentativa)
		resposta = self.client.get(
			reverse("curso-detalhe", args=[curso.pk]), {"tentativa": tentativa.pk}
		)
		return curso, resposta

	def test_curso_na_lista_tem_inscrever_se_junto_com_remover(self):
		curso, resposta = self.abrir_detalhe(salvo=True)

		self.assertContains(resposta, "Inscrever-se")
		self.assertContains(resposta, "Remover da minha lista")
		self.assertContains(resposta, f'href="{escape(url_curso_senai(curso))}"')
		self.assertContains(resposta, 'target="_blank" rel="noopener noreferrer"')

	def test_curso_fora_da_lista_nao_tem_inscrever_se(self):
		_, resposta = self.abrir_detalhe(salvo=False)

		self.assertNotContains(resposta, "Inscrever-se")
		self.assertContains(resposta, "Manifestar interesse neste curso")

	def test_manifestar_interesse_salva_sem_sair_da_pagina(self):
		"""interesse.js: o SENAI abre em outra aba e a página recarrega com "Inscrever-se"."""
		curso, resposta = self.abrir_detalhe(salvo=False)

		self.assertContains(resposta, f'data-interesse data-url-senai="{escape(url_curso_senai(curso))}"')
		self.assertContains(resposta, "js/interesse.js")

	def test_aprendiz_e_graduacao_nao_prometem_inscricao(self):
		for nivel in ("aprendiz", "graduacao"):
			with self.subTest(nivel=nivel):
				Interesse.objects.all().delete()
				get_user_model().objects.all().delete()
				_, resposta = self.abrir_detalhe(salvo=True, nivel=nivel)

				self.assertContains(resposta, "Ver no site do SENAI")
				self.assertNotContains(resposta, "Inscrever-se")


class BotaoDeInscricaoNoResultadoTest(BaseEducMatch):
	def abrir_resultado(self, salvo, nivel="livre"):
		usuario = self.criar_usuario()
		self.client.force_login(usuario)
		tentativa = self.criar_tentativa(dono=usuario)
		curso = tentativa.recomendacoes.get(rank_final=1).curso
		Curso.objects.filter(pk=curso.pk).update(nivel=nivel)
		curso.refresh_from_db()
		if salvo:
			registrar_interesse(usuario, curso, tentativa)
		return curso, self.client.get(reverse("quiz-resultado", args=[tentativa.pk]))

	def test_manifestar_interesse_no_resultado_salva_sem_sair_da_pagina(self):
		curso, resposta = self.abrir_resultado(salvo=False)

		self.assertContains(resposta, f'data-interesse data-url-senai="{escape(url_curso_senai(curso))}"')

	def test_sem_login_o_form_segue_para_a_tela_de_entrar(self):
		tentativa = self.criar_tentativa()
		sessao = self.client.session
		sessao["minhas_tentativas"] = [tentativa.pk]
		sessao.save()

		resposta = self.client.get(reverse("quiz-resultado", args=[tentativa.pk]))

		self.assertContains(resposta, "Manifestar interesse")
		self.assertNotContains(resposta, "data-interesse")

	def test_curso_na_lista_troca_remover_por_inscrever_se(self):
		curso, resposta = self.abrir_resultado(salvo=True)

		self.assertContains(resposta, "Inscrever-se")
		self.assertContains(resposta, f'href="{escape(url_curso_senai(curso))}"')
		self.assertNotContains(resposta, "Remover da minha lista")
		self.assertNotContains(resposta, "Manifestar interesse")

	def test_curso_fora_da_lista_continua_com_manifestar_interesse(self):
		_, resposta = self.abrir_resultado(salvo=False)

		self.assertContains(resposta, "Manifestar interesse")
		self.assertNotContains(resposta, "Inscrever-se")

	def test_aprendiz_nao_promete_inscricao(self):
		_, resposta = self.abrir_resultado(salvo=True, nivel="aprendiz")

		self.assertContains(resposta, "Ver no site do SENAI")
		self.assertNotContains(resposta, "Inscrever-se")


class PesoDaAreaNoCursoTest(BaseEducMatch):
	"""O peso de cada área em um curso é da coordenação: vale no ranking e sobrevive ao deploy."""

	def rodar_seed(self, **opcoes):
		call_command("seed_cursos", stdout=StringIO(), **opcoes)

	def setUp(self):
		super().setUp()
		self.curso = Curso.objects.get(nome_curso="Eletricista Instalador Predial")
		self.area = Area.objects.get(slug="metalurgia-soldagem")
		self.pesos_do_seed = dict(self.curso.curso_peso.values_list("area__slug", "peso"))

	def test_peso_editado_muda_o_ranking(self):
		tentativa = self.criar_tentativa()
		fora_do_top = Curso.objects.filter(is_active=True).exclude(
			pk__in=tentativa.recomendacoes.values("curso")
		).first()
		self.assertIsNotNone(fora_do_top)
		perfil = perfil_vetor(
			[r.alternativa for r in tentativa.respostas.select_related("alternativa").prefetch_related("alternativa__pesos__area")]
		)
		fora_do_top.curso_peso.all().delete()
		for slug, valor in perfil.items():
			fora_do_top.curso_peso.create(area=Area.objects.get(slug=slug), peso=valor)

		primeiro = self.criar_tentativa().recomendacoes.get(rank_final=1)

		self.assertEqual(primeiro.curso, fora_do_top)

	def test_deploy_nao_desfaz_o_peso_editado(self):
		self.curso.curso_peso.all().delete()
		self.curso.curso_peso.create(area=self.area, peso=4)

		self.rodar_seed()

		self.assertEqual(
			dict(self.curso.curso_peso.values_list("area__slug", "peso")), {"metalurgia-soldagem": 4}
		)

	def test_deploy_nao_reativa_curso_desativado(self):
		Curso.objects.filter(pk=self.curso.pk).update(is_active=False, descricao="Editada")

		self.rodar_seed()

		self.curso.refresh_from_db()
		self.assertFalse(self.curso.is_active)
		self.assertEqual(self.curso.descricao, "Editada")

	def test_seed_cria_curso_que_falta_com_os_pesos(self):
		self.curso.delete()

		self.rodar_seed()

		recriado = Curso.objects.get(nome_curso="Eletricista Instalador Predial")
		self.assertEqual(
			dict(recriado.curso_peso.values_list("area__slug", "peso")), self.pesos_do_seed
		)

	def test_sobrescrever_volta_aos_valores_do_seed(self):
		self.curso.curso_peso.all().delete()
		self.curso.curso_peso.create(area=self.area, peso=4)

		self.rodar_seed(sobrescrever=True)

		self.assertEqual(
			dict(self.curso.curso_peso.values_list("area__slug", "peso")), self.pesos_do_seed
		)


class CatalogoDoSenaiTest(BaseEducMatch):
	"""O CSV é o catálogo real: o que está nele precisa estar certo antes do deploy."""

	def test_csv_tem_os_cursos_das_planilhas(self):
		linhas = ler_cursos()
		ativos = [linha for linha in linhas if linha["ativo"] == "1"]

		self.assertEqual(len(linhas), 50)
		self.assertEqual(len(ativos), 47)
		codigos = [linha["codigo_senai"] for linha in linhas if linha["codigo_senai"]]
		self.assertEqual(len(codigos), 49)
		self.assertEqual(len(codigos), len(set(codigos)))

	def test_texto_provisorio_da_planilha_nao_entra(self):
		for linha in ler_cursos():
			with self.subTest(curso=linha["nome"]):
				self.assertNotIn("não publicado", linha["descricao"])
				self.assertNotIn("não exibido", linha["descricao"])
				self.assertNotIn("não confirmada", linha["descricao"])
				self.assertEqual(bool(linha["descricao"]), linha["ativo"] == "1")

	def test_seed_cria_o_catalogo_ativo(self):
		self.assertEqual(Curso.objects.filter(is_active=True).count(), 47)
		self.assertEqual(Curso.objects.count(), 50)
		self.assertEqual(Curso.objects.filter(nome_curso="Assistente Administrativo").count(), 2)

	def test_area_principal_tem_o_maior_peso_em_todo_curso(self):
		for curso in Curso.objects.prefetch_related("curso_peso__area"):
			with self.subTest(curso=curso.nome_curso):
				pesos = {peso.area_id: peso.peso for peso in curso.curso_peso.all()}
				maior = pesos.pop(curso.area_principal_id)
				self.assertTrue(all(peso < maior for peso in pesos.values()))

	def test_rodar_o_seed_de_novo_nao_duplica(self):
		call_command("seed_cursos", stdout=StringIO())

		self.assertEqual(Curso.objects.count(), 50)

	def test_sobrescrever_nao_reativa_curso_sem_descricao(self):
		call_command("seed_cursos", sobrescrever=True, stdout=StringIO())

		self.assertFalse(Curso.objects.get(nome_curso="Assistente Técnico de Vendas").is_active)
		self.assertEqual(Curso.objects.count(), 50)

	def test_curso_sem_codigo_e_achado_pelo_nome(self):
		call_command("seed_cursos", stdout=StringIO())

		self.assertEqual(
			Curso.objects.filter(nome_curso="Deep Learning e Inteligência Artificial Generativa Aplicada").count(), 1
		)

	def test_csv_com_problema_para_o_seed(self):
		base = {
			"codigo_senai": "1", "nome": "Teste", "descricao": "D", "area": "ti", "nivel": "livre",
			"modalidade": "Presencial", "duracao": "10", "unidade_carga": "horas", "url": "",
			"consultado_em": "", "ativo": "1",
		}
		for pesos in ("ti=2|automotiva=5", "ti=5|automotiva=5", "automotiva=5", "ti=6", "ti=abc", "ti=5|nao-existe=1"):
			with self.subTest(pesos=pesos), patch(
				"catalogo.management.commands.seed_cursos.ler_cursos", return_value=[{**base, "pesos": pesos}]
			):
				with self.assertRaises(CommandError):
					call_command("seed_cursos", stdout=StringIO())

	def test_toda_area_ativa_tem_curso_e_alternativa(self):
		for area in Area.objects.filter(is_active=True):
			with self.subTest(area=area.slug):
				self.assertTrue(area.cursos.filter(is_active=True).exists())
				self.assertTrue(area.pesos.filter(alternativa__questao__is_active=True).exists())


class InativaCatalogoFicticioTest(BaseEducMatch):
	def migracao(self):
		return import_module("catalogo.migrations.0003_inativa_catalogo_ficticio")

	def test_inativa_sem_apagar_o_historico(self):
		area = Area.objects.create(nome="Costura", slug="costura", descricao="Antiga")
		ficticio = Curso.objects.create(
			nome_curso="Costura Industrial", descricao="Antiga", area_principal=area, duracao=200
		)
		tentativa = self.criar_tentativa()
		recomendacao = tentativa.recomendacoes.get(rank_final=1)
		recomendacao.curso = ficticio
		recomendacao.save()
		real = Curso.objects.filter(is_active=True).first()

		self.migracao().inativar(apps, None)

		ficticio.refresh_from_db()
		area.refresh_from_db()
		self.assertFalse(ficticio.is_active)
		self.assertFalse(area.is_active)
		self.assertTrue(tentativa.recomendacoes.filter(curso=ficticio).exists())
		real.refresh_from_db()
		self.assertTrue(real.is_active)

		self.migracao().reativar(apps, None)

		ficticio.refresh_from_db()
		self.assertTrue(ficticio.is_active)


class DetalheDoCursoRealTest(BaseEducMatch):
	def abrir(self, **campos):
		usuario = self.criar_usuario()
		self.client.force_login(usuario)
		tentativa = self.criar_tentativa(dono=usuario)
		curso = tentativa.recomendacoes.get(rank_final=1).curso
		Curso.objects.filter(pk=curso.pk).update(**campos)
		curso.refresh_from_db()
		return curso, self.client.get(reverse("curso-detalhe", args=[curso.pk]), {"tentativa": tentativa.pk})

	def test_mostra_nivel_modalidade_e_carga_na_unidade_certa(self):
		_, resposta = self.abrir(nivel="graduacao", modalidade="Presencial", duracao=2880, unidade_carga="horas_aula")

		self.assertContains(resposta, "Graduação")
		self.assertContains(resposta, "Presencial")
		self.assertContains(resposta, "2880 horas/aula")

	def test_mostra_de_onde_veio_a_informacao(self):
		_, resposta = self.abrir(consultado_em="2026-10-30")

		self.assertContains(resposta, "consultadas em 30/10/2026")

	def test_sem_data_de_consulta_nao_mostra_a_linha(self):
		_, resposta = self.abrir(consultado_em=None)

		self.assertNotContains(resposta, "consultadas em")

	def test_link_e_a_pagina_do_curso_e_sem_link_e_a_busca(self):
		curso = Curso(nome_curso="X", url_senai="https://www.sp.senai.br/curso/x/1")
		self.assertEqual(url_curso_senai(curso), "https://www.sp.senai.br/curso/x/1")

		curso.url_senai = ""
		self.assertIn("pesquisa=X", url_curso_senai(curso))


class CursoInativoNoHistoricoTest(BaseEducMatch):
	"""O detalhe de curso inativo é 404: quem veio antes da troca não pode cair nele."""

	def setUp(self):
		super().setUp()
		self.usuario = self.criar_usuario()
		self.client.force_login(self.usuario)
		self.tentativa = self.criar_tentativa(dono=self.usuario)
		self.recomendacoes = list(self.tentativa.recomendacoes.select_related("curso"))
		for recomendacao in self.recomendacoes:
			registrar_interesse(self.usuario, recomendacao.curso, self.tentativa)
		Curso.objects.filter(pk__in=[r.curso_id for r in self.recomendacoes]).update(is_active=False)

	def assert_sem_link(self, resposta):
		for recomendacao in self.recomendacoes:
			self.assertNotContains(resposta, reverse("curso-detalhe", args=[recomendacao.curso_id]) + "?")
		self.assertContains(resposta, "Curso não oferecido atualmente")

	def test_resultado_antigo_abre_sem_link_e_sem_inscricao(self):
		resposta = self.client.get(reverse("quiz-resultado", args=[self.tentativa.pk]))

		self.assertEqual(resposta.status_code, 200)
		self.assert_sem_link(resposta)
		self.assertNotContains(resposta, "Inscrever-se")
		self.assertNotContains(resposta, "Manifestar interesse")

	def test_lista_de_interesse_sem_link(self):
		self.assert_sem_link(self.client.get(reverse("lista_interesse")))

	def test_nao_salva_interesse_em_curso_inativo(self):
		resposta = self.client.post(reverse("interesse-salvar"), {"curso_id": self.recomendacoes[0].curso_id})

		self.assertEqual(resposta.status_code, 404)
