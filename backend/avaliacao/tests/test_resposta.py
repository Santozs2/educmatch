from io import StringIO

from django.core.management import call_command
from django.db import models
from django.urls import reverse

from avaliacao.models import ItemDeResposta, Pergunta, RespostaDeAvaliacao
from avaliacao.tests.base import BaseAvaliacao


class RespostaDoAlunoTest(BaseAvaliacao):
    """Etapa 4: o aluno responde pelo link da turma, sem conta e sem se identificar."""

    def test_seed_cria_sete_perguntas_e_pode_rodar_de_novo(self):
        call_command("seed_avaliacao", stdout=StringIO())

        self.assertEqual(Pergunta.objects.count(), 7)

    def test_pagina_mostra_curso_e_turma(self):
        link = self.criar_link()

        resposta = self.client.get(reverse("avaliacao-responder", args=[link.token]))

        self.assertContains(resposta, link.curso.nome_curso)
        self.assertContains(resposta, "2026/1 · Noite")

    def test_resposta_completa_e_gravada(self):
        link = self.criar_link()

        resposta = self.enviar(link, self.respostas_validas(texto="Mais aulas práticas"))

        self.assertRedirects(resposta, reverse("avaliacao-obrigado", args=[link.token]))
        gravada = RespostaDeAvaliacao.objects.get()
        self.assertEqual(gravada.link, link)
        self.assertEqual(gravada.itens.count(), 7)
        self.assertEqual(gravada.itens.get(pergunta__tipo="nps").numero, 9)
        self.assertEqual(gravada.itens.get(pergunta__tipo="texto").texto, "Mais aulas práticas")

    def test_opcional_em_branco_nao_vira_item(self):
        link = self.criar_link()

        self.enviar(link, self.respostas_validas(texto=""))

        self.assertEqual(ItemDeResposta.objects.count(), 6)

    def test_falta_obrigatoria_nao_grava(self):
        link = self.criar_link()
        dados = self.respostas_validas()
        dados.pop(f"pergunta_{Pergunta.objects.get(ordem=1).id}")

        resposta = self.enviar(link, dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Faltou responder")
        self.assertFalse(RespostaDeAvaliacao.objects.exists())

    def test_nota_fora_da_escala_e_recusada(self):
        link = self.criar_link()

        self.enviar(link, self.respostas_validas(nota=11))

        self.assertFalse(RespostaDeAvaliacao.objects.exists())

    def test_link_fechado_da_404(self):
        link = self.criar_link(ativo=False)

        resposta = self.client.get(reverse("avaliacao-responder", args=[link.token]))

        self.assertEqual(resposta.status_code, 404)

    def test_mesmo_navegador_nao_envia_duas_vezes(self):
        link = self.criar_link()
        self.enviar(link, self.respostas_validas())

        resposta = self.enviar(link, self.respostas_validas())

        self.assertRedirects(resposta, reverse("avaliacao-obrigado", args=[link.token]))
        self.assertEqual(RespostaDeAvaliacao.objects.count(), 1)

    def test_pergunta_inativa_some_do_formulario(self):
        link = self.criar_link()
        Pergunta.objects.filter(ordem=5).update(ativa=False)

        resposta = self.client.get(reverse("avaliacao-responder", args=[link.token]))

        self.assertNotContains(resposta, Pergunta.objects.get(ordem=5).texto)


class AnonimatoTest(BaseAvaliacao):
    def test_resposta_nao_tem_onde_guardar_quem_respondeu(self):
        for model in (RespostaDeAvaliacao, ItemDeResposta):
            with self.subTest(model=model.__name__):
                ligados_a_usuario = [
                    campo.name for campo in model._meta.get_fields()
                    if campo.is_relation and campo.related_model and campo.related_model._meta.label == "accounts.User"
                ]
                self.assertEqual(ligados_a_usuario, [])

    def test_resposta_guarda_o_dia_e_nao_a_hora(self):
        campo = RespostaDeAvaliacao._meta.get_field("respondido_em")

        self.assertIs(type(campo), models.DateField)