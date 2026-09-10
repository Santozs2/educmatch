from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Popula o banco com areas, cursos e perguntas (roda os tres seeds)."

    def handle(self, *args, **options):
        for comando in ("seed_areas", "seed_courses", "seed_questions"):
            self.stdout.write(self.style.WARNING(f"-> {comando}"))
            call_command(comando)
        self.stdout.write(self.style.SUCCESS("Banco populado."))
