from django.core.management.base import BaseCommand
from catalogo.models import Area

# As áreas tecnológicas do SENAI. As antigas ficam inativas (migração 0003 do catálogo).
AREAS = [
    ("automacao-energia", "Mecatrônica, Sistemas de Automação, Energia e Eletrônica", "Instalações elétricas, comandos, automação e eletrônica."),
    ("ti", "Tecnologia da Informação e Informática", "Programação, dados e inteligência artificial."),
    ("automotiva", "Automotiva", "Manutenção e diagnóstico de veículos e motores."),
    ("fabricacao-mecanica", "Fabricação Mecânica e Manutenção Industrial", "Usinagem, desenho de peças e manutenção mecânica."),
    ("metalurgia-soldagem", "Metalurgia e Soldagem", "Soldagem e serralheria."),
    ("administracao-gestao", "Administração e Gestão", "Rotinas administrativas e apoio às operações da empresa."),
    ("refrigeracao-climatizacao", "Refrigeração e Climatização", "Manutenção e limpeza de condicionadores de ar."),
    ("logistica-transporte", "Logística e Transporte", "Recebimento, armazenagem e movimentação de materiais."),
    ("construcao-mobiliario", "Construção Civil e Design de Mobiliário", "Pintura e acabamento de edificações."),
    ("moda-joalheria", "Design de Moda, Têxtil, Vestuário, Calçados e Joalheria", "Confecção de joias e artefatos de metal."),
]


class Command(BaseCommand):
    help = "Cria ou atualiza as areas de perfil usadas pela engine de matching."

    def handle(self, *args, **options):
        for slug, nome, descricao in AREAS:
            area, created = Area.objects.update_or_create(
                slug=slug,
                defaults={"nome": nome, "descricao": descricao, "is_active": True},
            )
            acao = "criada" if created else "atualizada"
            self.stdout.write(self.style.SUCCESS(f"Area {acao}: {area.nome}"))
