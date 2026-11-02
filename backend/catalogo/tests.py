from io import StringIO

from django.core.management import call_command
from django.urls import reverse
from django.utils.html import escape

from accounts.servicos import registrar_interesse
from avaliacao.models import ItemDeResposta, LinkDeAvaliacao, Pergunta, RespostaDeAvaliacao
from avaliacao.tests.base import BaseAvaliacao
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
	def abrir_detalhe(self, salvo):
		usuario = self.criar_usuario()
		self.client.force_login(usuario)
		tentativa = self.criar_tentativa(dono=usuario)
		curso = tentativa.recomendacoes.get(rank_final=1).curso
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


class BotaoDeInscricaoNoResultadoTest(BaseEducMatch):
	def abrir_resultado(self, salvo):
		usuario = self.criar_usuario()
		self.client.force_login(usuario)
		tentativa = self.criar_tentativa(dono=usuario)
		curso = tentativa.recomendacoes.get(rank_final=1).curso
		if salvo:
			registrar_interesse(usuario, curso, tentativa)
		return curso, self.client.get(reverse("quiz-resultado", args=[tentativa.pk]))

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


class PesoDaAreaNoCursoTest(BaseEducMatch):
	"""O peso de cada área em um curso é da coordenação: vale no ranking e sobrevive ao deploy."""

	def rodar_seed(self, **opcoes):
		call_command("seed_cursos", stdout=StringIO(), **opcoes)

	def setUp(self):
		super().setUp()
		self.curso = Curso.objects.get(nome_curso="Eletricista Instalador")
		self.area = Area.objects.get(slug="metalurgia")
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
			dict(self.curso.curso_peso.values_list("area__slug", "peso")), {"metalurgia": 4}
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

		recriado = Curso.objects.get(nome_curso="Eletricista Instalador")
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
