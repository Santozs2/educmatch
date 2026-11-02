from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalogo.models import Area
from quiz.models import Alternativa, Peso_alternativa, Questao

# Mudar o texto de uma alternativa apaga as respostas dela (CASCADE). Depois que
# houver respostas, troca de alternativa pede uma nova versão, nunca edição.
VERSAO_QUIZ = 2

# pesos de 0 a 5. Área ausente = peso 0.
QUESTOES = [
    {
        "texto": "Qual tipo de tarefa te dá mais satisfação?",
        "order": 1,
        "alternativa": [
            {"texto": "Ligar e programar sistemas elétricos e automáticos", "peso": {"automacao-energia": 5, "ti": 1}},
            {"texto": "Escrever programas e analisar dados no computador", "peso": {"ti": 5}},
            {"texto": "Consertar carros e motores", "peso": {"automotiva": 5, "fabricacao-mecanica": 1}},
            {"texto": "Organizar documentos e rotinas para o escritório funcionar", "peso": {"administracao-gestao": 5, "logistica-transporte": 1}},
        ],
    },
    {
        "texto": "Em qual ambiente você se imagina trabalhando?",
        "order": 2,
        "alternativa": [
            {"texto": "Oficina de veículos", "peso": {"automotiva": 4, "fabricacao-mecanica": 1}},
            {"texto": "Escritório, com computador", "peso": {"administracao-gestao": 3, "ti": 3}},
            {"texto": "Chão de fábrica, entre máquinas", "peso": {"fabricacao-mecanica": 4, "automacao-energia": 2, "metalurgia-soldagem": 1}},
            {"texto": "Casas, prédios e obras", "peso": {"construcao-mobiliario": 4, "refrigeracao-climatizacao": 2, "automacao-energia": 1}},
        ],
    },
    {
        "texto": "Você prefere trabalhar mais com o quê?",
        "order": 3,
        "alternativa": [
            {"texto": "Fios, painéis e sensores", "peso": {"automacao-energia": 5}},
            {"texto": "Chapas de aço e solda", "peso": {"metalurgia-soldagem": 5, "fabricacao-mecanica": 1}},
            {"texto": "Peças, tornos e medidas de precisão", "peso": {"fabricacao-mecanica": 5}},
            {"texto": "Dados, lógica e algoritmos", "peso": {"ti": 5}},
        ],
    },
    {
        "texto": "Diante de um equipamento quebrado, o que você faz primeiro?",
        "order": 4,
        "alternativa": [
            {"texto": "Testo a parte elétrica com um multímetro", "peso": {"automacao-energia": 4, "automotiva": 1}},
            {"texto": "Abro e inspeciono as peças mecânicas", "peso": {"fabricacao-mecanica": 4, "automotiva": 2}},
            {"texto": "Conecto um aparelho de diagnóstico", "peso": {"automotiva": 4, "automacao-energia": 1, "ti": 1}},
            {"texto": "Limpo, confiro filtros e meço a pressão", "peso": {"refrigeracao-climatizacao": 5}},
        ],
    },
    {
        "texto": "O que mais te atrai em uma profissão?",
        "order": 5,
        "alternativa": [
            {"texto": "Estar sempre aprendendo tecnologia nova", "peso": {"ti": 4, "automacao-energia": 2}},
            {"texto": "Ver pronto o produto que eu fiz", "peso": {"fabricacao-mecanica": 3, "metalurgia-soldagem": 3, "moda-joalheria": 2}},
            {"texto": "Deixar os ambientes mais confortáveis para as pessoas", "peso": {"refrigeracao-climatizacao": 4, "construcao-mobiliario": 2}},
            {"texto": "Fazer o material certo chegar na hora certa", "peso": {"logistica-transporte": 5, "administracao-gestao": 2}},
        ],
    },
    {
        "texto": "Com qual dessas ferramentas você se imagina trabalhando?",
        "order": 6,
        "alternativa": [
            {"texto": "Multímetro e alicate", "peso": {"automacao-energia": 5}},
            {"texto": "Máquina de solda", "peso": {"metalurgia-soldagem": 5}},
            {"texto": "Notebook e terminal de comando", "peso": {"ti": 5}},
            {"texto": "Rolo, pincel e espátula", "peso": {"construcao-mobiliario": 5}},
        ],
    },
    {
        "texto": "Num projeto em equipe, qual parte você pegaria?",
        "order": 7,
        "alternativa": [
            {"texto": "Organizar a equipe e os prazos", "peso": {"administracao-gestao": 5}},
            {"texto": "Controlar o estoque e os materiais", "peso": {"logistica-transporte": 5, "administracao-gestao": 1}},
            {"texto": "Desenhar a peça no computador", "peso": {"fabricacao-mecanica": 4, "ti": 2}},
            {"texto": "Construir o protótipo na oficina", "peso": {"fabricacao-mecanica": 3, "metalurgia-soldagem": 2, "automacao-energia": 1}},
        ],
    },
    {
        "texto": "Qual destes lugares você gostaria de conhecer por dentro?",
        "order": 8,
        "alternativa": [
            {"texto": "Um centro de distribuição de mercadorias", "peso": {"logistica-transporte": 5}},
            {"texto": "Um ateliê de joias", "peso": {"moda-joalheria": 5}},
            {"texto": "Uma sala de servidores e dados", "peso": {"ti": 4, "automacao-energia": 1}},
            {"texto": "Uma oficina de máquinas agrícolas e caminhões", "peso": {"automotiva": 5, "fabricacao-mecanica": 1}},
        ],
    },
    {
        "texto": "Qual resultado te deixaria mais orgulhoso(a)?",
        "order": 9,
        "alternativa": [
            {"texto": "Uma solda perfeita, aprovada na inspeção", "peso": {"metalurgia-soldagem": 5, "fabricacao-mecanica": 1}},
            {"texto": "Uma joia delicada feita por mim", "peso": {"moda-joalheria": 5}},
            {"texto": "Um prédio com pintura e acabamento impecáveis", "peso": {"construcao-mobiliario": 5}},
            {"texto": "Um ar-condicionado voltando a gelar", "peso": {"refrigeracao-climatizacao": 5}},
        ],
    },
    {
        "texto": "Com qual destes materiais você prefere lidar no dia a dia?",
        "order": 10,
        "alternativa": [
            {"texto": "Metais preciosos e peças pequenas", "peso": {"moda-joalheria": 5, "metalurgia-soldagem": 1}},
            {"texto": "Relatórios e planilhas", "peso": {"administracao-gestao": 4, "ti": 1}},
            {"texto": "Tintas, massas e texturas", "peso": {"construcao-mobiliario": 5}},
            {"texto": "Compressores, gás refrigerante e dutos", "peso": {"refrigeracao-climatizacao": 5}},
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
                versao=VERSAO_QUIZ,
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

        # Versões antigas saem do quiz, mas ficam no banco: são as respostas do histórico.
        Questao.objects.exclude(versao=VERSAO_QUIZ).update(is_active=False)

        self.stdout.write(self.style.SUCCESS(f"\nTotal: {len(QUESTOES)} perguntas no quiz."))
