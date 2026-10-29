from django.urls import reverse

from avaliacao.models import ItemDeResposta, LinkDeAvaliacao, Pergunta, RespostaDeAvaliacao
from avaliacao.tests.base import BaseAvaliacao
from quiz.models import Tentativa_de_resposta


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
