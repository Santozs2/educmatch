from django.core.management.base import BaseCommand
from django.db import transaction

from avaliacao.models import Pergunta

# A avaliação de fim de curso. É uma PROPOSTA: a coordenação revisa o texto aqui
# (ou no admin) antes da primeira turma. Rodar de novo atualiza pela "ordem".
PERGUNTAS = [
    {
        "ordem": 1,
        "tipo": "nps",
        "texto": "De 0 a 10, quanto você recomendaria este curso a um amigo?",
    },
    {
        "ordem": 2,
        "tipo": "escala",
        "texto": "O curso atendeu às suas expectativas?",
    },
    {
        "ordem": 3,
        "tipo": "escala",
        "texto": "Como você avalia os instrutores?",
    },
    {
        "ordem": 4,
        "tipo": "escala",
        "texto": "Como você avalia a estrutura (laboratórios, equipamentos e materiais)?",
    },
    {
        "ordem": 5,
        "tipo": "escala",
        "texto": "O que você aprendeu vai ajudar no seu próximo passo profissional?",
    },
    {
        # A pergunta que liga a avaliação ao TCC: a recomendação do quiz acertou?
        "ordem": 6,
        "tipo": "escolha",
        "texto": "O curso combinou com o que o quiz do EducMatch tinha mostrado para você?",
        "opcoes": ["Sim", "Em parte", "Não", "Não fiz o quiz"],
    },
    {
        "ordem": 7,
        "tipo": "texto",
        "texto": "O que poderia melhorar no curso?",
        "obrigatoria": False,
    },
]


class Command(BaseCommand):
    help = "Cria ou atualiza as perguntas da avaliação de fim de curso."

    @transaction.atomic
    def handle(self, *args, **options):
        for dados in PERGUNTAS:
            padrao = {"opcoes": [], "obrigatoria": True, "ativa": True, **dados}
            ordem = padrao.pop("ordem")
            Pergunta.objects.update_or_create(ordem=ordem, defaults=padrao)
        self.stdout.write(self.style.SUCCESS(f"{len(PERGUNTAS)} perguntas da avaliação"))