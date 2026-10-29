from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

# O que o startup.sh rodava a cada boot, um processo por comando. Os seeds usam
# update_or_create: rodar de novo não duplica nada, só gasta tempo.
ETAPAS = (
    ("migrate", {"interactive": False}),
    ("createcachetable", {}),
    ("seed_areas", {}),
    ("seed_cursos", {}),
    ("seed_questoes", {}),
    ("seed_avaliacao", {}),
)


class Command(BaseCommand):
    help = (
        "Prepara o banco para a versão no ar (migrate, cache e seeds), num processo só. "
        "Se o banco já foi preparado para esta versão, não faz nada: é o caso de quase "
        "todo boot, quando o site só acordou depois de dormir."
    )

    def add_arguments(self, parser):
        parser.add_argument("--forcar", action="store_true", help="Prepara mesmo que a versão não tenha mudado.")

    def handle(self, *args, forcar, **options):
        marcador = Path(settings.MARCADOR_PREPARO)
        versao = settings.VERSAO
        # "dev" não identifica um commit: sem VERSAO (deploy manual ou máquina local), sempre prepara.
        if not forcar and versao != "dev" and marcador.exists() and marcador.read_text(encoding="utf-8").strip() == versao:
            self.stdout.write(f"Banco já preparado para {versao}: nada a fazer.")
            return

        for nome, opcoes in ETAPAS:
            self.stdout.write(f"-> {nome}")
            call_command(nome, stdout=self.stdout, **opcoes)

        # Só depois de tudo dar certo: se uma etapa falhar, o próximo boot tenta de novo.
        marcador.parent.mkdir(parents=True, exist_ok=True)
        marcador.write_text(versao, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Banco preparado para {versao}."))