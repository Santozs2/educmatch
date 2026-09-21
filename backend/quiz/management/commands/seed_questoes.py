from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalogo.models import Area
from quiz.models import Alternativa, Peso_alternativa, Questao

# pesos de 0 a 5. Área ausente = peso 0.
QUESTOES = [
    {
        "texto": "Qual tipo de tarefa te dá mais satisfação?",
        "order": 1,
        "alternativa": [
            {
                "texto": "Montar e ligar coisas que funcionam na hora",
                "peso": {"eletrica": 4, "eletromecanica": 3},
            },
            {
                "texto": "Criar produtos com as próprias mãos",
                "peso": {"costura": 4, "mecanica": 3},
            },
            {
                "texto": "Resolver problemas no computador",
                "peso": {"ti": 4, "ia": 3},
            },
            {
                "texto": "Desmontar máquinas para entender como funcionam",
                "peso": {"mecanica": 4, "mecanica-automotiva": 4},
            },
        ],
    },
    {
        "texto": "Em qual ambiente você se imagina trabalhando?",
        "order": 2,
        "alternativa": [
            {
                "texto": "Oficina com bancada e ferramentas",
                "peso": {"mecanica": 3, "mecanica-automotiva": 3, "eletromecanica": 2},
            },
            {
                "texto": "Escritório ou home office, com computador",
                "peso": {"ti": 4, "ia": 4},
            },
            {
                "texto": "Chão de fábrica, indo até as máquinas",
                "peso": {"eletromecanica": 4, "eletrica": 3, "mecanica": 2},
            },
            {
                "texto": "Ateliê ou setor de produção de vestuário",
                "peso": {"costura": 5},
            },
        ],
    },
    {
        "texto": "Você prefere trabalhar mais com o quê?",
        "order": 3,
        "alternativa": [
            {
                "texto": "Eletricidade, circuitos e comandos",
                "peso": {"eletrica": 5, "eletromecanica": 3},
            },
            {
                "texto": "Tecidos, moldes e acabamento",
                "peso": {"costura": 5},
            },
            {
                "texto": "Dados, lógica e algoritmos",
                "peso": {"ia": 4, "ti": 4},
            },
            {
                "texto": "Motores, engrenagens e ferramentas",
                "peso": {"mecanica": 4, "mecanica-automotiva": 4},
            },
        ],
    },
    {
        "texto": "Diante de um equipamento quebrado, o que você faz primeiro?",
        "order": 4,
        "alternativa": [
            {
                "texto": "Testo a parte elétrica com um multímetro",
                "peso": {"eletrica": 4, "eletromecanica": 3},
            },
            {
                "texto": "Abro e inspeciono as peças mecânicas",
                "peso": {"mecanica": 4, "mecanica-automotiva": 3},
            },
            {
                "texto": "Procuro o manual ou o código de erro na internet",
                "peso": {"ti": 3, "ia": 2},
            },
            {
                "texto": "Conecto um aparelho de diagnóstico",
                "peso": {"mecanica-automotiva": 4, "eletromecanica": 2, "ti": 2},
            },
        ],
    },
    {
        "texto": "O que mais te atrai em uma profissão?",
        "order": 5,
        "alternativa": [
            {
                "texto": "Estar sempre aprendendo tecnologia nova",
                "peso": {"ia": 4, "ti": 4},
            },
            {
                "texto": "Ver pronto o produto que eu fiz",
                "peso": {"costura": 4, "mecanica": 3},
            },
            {
                "texto": "Manter a indústria funcionando sem parar",
                "peso": {"eletromecanica": 5, "eletrica": 3, "mecanica": 2},
            },
            {
                "texto": "Trabalhar com carros e veículos",
                "peso": {"mecanica-automotiva": 5},
            },
        ],
    },
    {
        "texto": "Com qual dessas ferramentas você se imagina trabalhando?",
        "order": 6,
        "alternativa": [
            {
                "texto": "Multímetro e alicate",
                "peso": {"eletrica": 5, "eletromecanica": 2},
            },
            {
                "texto": "Máquina de costura industrial",
                "peso": {"costura": 5},
            },
            {
                "texto": "Notebook e terminal de comando",
                "peso": {"ti": 5, "ia": 3},
            },
            {
                "texto": "Torno, fresa e paquímetro",
                "peso": {"mecanica": 5, "eletromecanica": 1},
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Cria ou atualiza as perguntas do quiz com suas alternativas e peso."

    @transaction.atomic
    def handle(self, *args, **options):
        areas = {area.slug: area for area in Area.objects.all()}
        if not areas:
            raise CommandError("Nenhuma área cadastrada. Rode antes: manage.py seed_areas")

        for q_data in QUESTOES:
            questao, created = Questao.objects.update_or_create(
                texto=q_data["texto"],
                defaults={"order": q_data["order"], "is_active": True},
            )

            textos_validos = []
            for order, c_data in enumerate(q_data["alternativa"], start=1):
                desconhecidas = set(c_data["peso"]) - set(areas)
                if desconhecidas:
                    raise CommandError(
                        f"Alternativa '{c_data['texto']}' usa áreas "
                        f"inexistentes: {sorted(desconhecidas)}"
                    )

                alternativa, _ = Alternativa.objects.update_or_create(
                    questao= questao,
                    texto=c_data["texto"],
                    defaults={"order": order},
                )
                textos_validos.append(c_data["texto"])

                for slug, peso in c_data["peso"].items():
                    Peso_alternativa.objects.update_or_create(
                        alternativa =alternativa,
                        area=areas[slug],
                        defaults={"peso": peso},
                    )
                alternativa.pesos.exclude(area__slug__in=c_data["peso"]).delete()
            # alternativas que sairam do arquivo somem do banco
            questao.alternativas.exclude(texto__in=textos_validos).delete()

            acao = "criada" if created else "atualizada"
            self.stdout.write(
                self.style.SUCCESS(
                    f"Pergunta {acao}: {questao.texto} "
                    f"[{len(q_data['alternativa'])} alternativas]"
                )
            )

        self.stdout.write(self.style.SUCCESS(f"\nTotal: {len(QUESTOES)} perguntas no quiz."))
