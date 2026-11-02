from io import StringIO

from django.core.management import call_command

from quiz.management.commands.seed_questoes import QUESTOES, VERSAO_QUIZ
from quiz.models import Alternativa, Questao, Resposta, Tentativa_de_resposta
from quiz.tests.base import BaseEducMatch


class VersaoDoQuizTest(BaseEducMatch):
    def criar_versao_antiga(self):
        """Pergunta da versão 1 com o mesmo texto de uma atual e uma resposta de aluno."""
        questao = Questao.objects.create(texto=QUESTOES[0]["texto"], order=1, versao=1)
        alternativa = Alternativa.objects.create(questao=questao, texto="Montar e ligar coisas")
        tentativa = Tentativa_de_resposta.objects.create(respondido_por="Antigo")
        return Resposta.objects.create(tentativa=tentativa, questao=questao, alternativa=alternativa)

    def test_seed_novo_nao_apaga_resposta_antiga(self):
        resposta = self.criar_versao_antiga()

        call_command("seed_questoes", stdout=StringIO())

        self.assertTrue(Resposta.objects.filter(pk=resposta.pk).exists())

    def test_so_a_versao_atual_fica_ativa(self):
        resposta = self.criar_versao_antiga()

        call_command("seed_questoes", stdout=StringIO())

        resposta.questao.refresh_from_db()
        self.assertFalse(resposta.questao.is_active)
        ativas = Questao.objects.filter(is_active=True)
        self.assertEqual(ativas.count(), len(QUESTOES))
        self.assertFalse(ativas.exclude(versao=VERSAO_QUIZ).exists())

    def test_rodar_de_novo_nao_duplica(self):
        call_command("seed_questoes", stdout=StringIO())

        self.assertEqual(Questao.objects.filter(versao=VERSAO_QUIZ).count(), len(QUESTOES))
