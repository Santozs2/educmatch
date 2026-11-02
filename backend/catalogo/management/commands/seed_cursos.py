import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalogo.models import Area, Curso, Peso_curso

ARQUIVO = Path(settings.BASE_DIR) / "catalogo" / "dados" / "cursos_senai_801.csv"
PESO_MAXIMO = 5


def ler_pesos(texto):
    """'ti=5|automotiva=2' vira {'ti': 5.0, 'automotiva': 2.0}. Área ausente = peso 0."""
    pesos = {}
    for parte in texto.split("|"):
        slug, _, valor = parte.partition("=")
        pesos[slug] = float(valor)
    return pesos


def ler_cursos(arquivo=None):
    with open(arquivo or ARQUIVO, newline="", encoding="utf-8") as origem:
        return list(csv.DictReader(origem, delimiter=";"))


class Command(BaseCommand):
    help = (
        "Cria os cursos do catálogo que ainda não existem, com seus pesos por área, a partir do CSV. "
        "Curso que já existe fica como está: o peso é da coordenação, que edita no painel."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--sobrescrever",
            action="store_true",
            help="Volta os cursos existentes aos valores do CSV, apagando o que foi editado no painel.",
        )

    @transaction.atomic
    def handle(self, *args, sobrescrever=False, **options):
        areas = {area.slug: area for area in Area.objects.all()}
        if not areas:
            raise CommandError(
                "Nenhuma área cadastrada. Rode antes: manage.py seed_areas"
            )

        linhas = ler_cursos()
        for data in linhas:
            pesos = self._pesos_validados(data, areas)
            codigo = data["codigo_senai"] or None
            # Sem código (curso sem link no SENAI), o nome é o que resta para achar o curso.
            chave = {"codigo_senai": codigo} if codigo else {"codigo_senai": None, "nome_curso": data["nome"]}
            valores = {
                "nome_curso": data["nome"],
                "descricao": data["descricao"],
                "area_principal": areas[data["area"]],
                "nivel": data["nivel"],
                "modalidade": data["modalidade"],
                "duracao": int(data["duracao"]),
                "unidade_carga": data["unidade_carga"],
                "url_senai": data["url"],
                "consultado_em": data["consultado_em"] or None,
                "is_active": data["ativo"] == "1",
            }
            # Este comando roda a cada deploy (preparar_producao): sem esta trava,
            # todo merge na main desfazia os pesos ajustados no painel.
            if sobrescrever:
                curso, created = Curso.objects.update_or_create(**chave, defaults=valores)
            else:
                curso, created = Curso.objects.get_or_create(**chave, defaults=valores)
                if not created:
                    self.stdout.write(f"Curso mantido: {curso.nome_curso}")
                    continue

            for slug, peso in pesos.items():
                Peso_curso.objects.update_or_create(
                    curso=curso,
                    area=areas[slug],
                    defaults={"peso": peso},
                )

            # tira pesos que sobraram de cadastros anteriores
            removidos, _ = curso.curso_peso.exclude(area__slug__in=pesos).delete()

            acao = "criado" if created else "atualizado"
            extra = f" (-{removidos} peso obsoleto)" if removidos else ""
            self.stdout.write(
                self.style.SUCCESS(
                    f"Curso {acao}: {curso.nome_curso} [{len(pesos)} pesos]{extra}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"\nTotal: {len(linhas)} cursos no catálogo.")
        )

    @staticmethod
    def _pesos_validados(data, areas):
        """Erro no CSV para o comando: melhor um deploy parado do que recomendação errada."""
        nome = data["nome"]
        try:
            pesos = ler_pesos(data["pesos"])
        except ValueError as erro:
            raise CommandError(f"Curso '{nome}' tem peso inválido: {data['pesos']}") from erro

        desconhecidas = (set(pesos) | {data["area"]}) - set(areas)
        if desconhecidas:
            raise CommandError(f"Curso '{nome}' usa áreas inexistentes: {sorted(desconhecidas)}")
        if not all(0 <= peso <= PESO_MAXIMO for peso in pesos.values()):
            raise CommandError(f"Curso '{nome}' tem peso fora de 0 a {PESO_MAXIMO}: {pesos}")

        principal = pesos.get(data["area"], 0)
        outros = [peso for slug, peso in pesos.items() if slug != data["area"]]
        if not principal or any(peso >= principal for peso in outros):
            raise CommandError(f"Curso '{nome}': a área principal precisa ter o maior peso: {pesos}")
        return pesos
