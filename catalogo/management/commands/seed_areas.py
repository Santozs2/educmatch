from django.core.management.base import BaseCommand
from catalogo.models import Area

AREAS = [
    ("eletrica", "Elétrica", "Instalações elétricas, comandos e NR-10."),
    ("costura", "Costura", "Modelagem, corte e costura industrial."),
    ("ia", "Inteligência Artificial", "Machine learning, dados e automação inteligente."),
    ("ti", "Tecnologia da Informação", "Programação, redes e suporte técnico."),
    ("mecanica-automotiva", "Mecânica Automotiva", "Motores, injeção eletrônica e freios."),
    ("mecanica", "Mecânica", "Usinagem, metrologia e manutenção mecânica."),
    ("eletromecanica", "Eletromecânica", "Integração de sistemas elétricos e mecânicos."),
    ("metalurgia", "Metalurgia", "Tratamento de metais, soldagem e fundição."),
    ("rh", "Recursos Humanos", "Gestão de pessoas, recrutamento e desenvolvimento organizacional."),
    ("financas", "Finanças", "Contabilidade, análise financeira e planejamento estratégico."),
]


class Command(BaseCommand):
    help = "Cria ou atualiza as areas de perfil usadas pela engine de matching."

    def handle(self, *args, **options):
        for slug, nome, descricao in AREAS:
            area, created = Area.objects.update_or_create(
                slug=slug,
                defaults={"nome": nome, "descricao": descricao},
            )
            acao = "criada" if created else "atualizada"
            self.stdout.write(self.style.SUCCESS(f"Area {acao}: {area.nome}"))