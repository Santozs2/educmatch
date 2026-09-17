from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalogo.models import Area, Curso, Peso_curso

# Pesos de 0 a 5. Área ausente = peso 0 (não precisa listar).
CURSOS = [
    {
        "nome": "Eletricista Instalador",
        "descricao": "Instalações elétricas prediais, leitura de projetos e NR-10.",
        "duracao": 160,
        "area_principal": "eletrica",
        "peso": {"eletrica": 5, "eletromecanica": 3, "mecanica": 1},
    },
    {
        "nome": "Comandos Elétricos e CLP",
        "descricao": "Acionamento de motores, painéis de comando e lógica ladder.",
        "duracao": 120,
        "area_principal": "eletrica",
        "peso": {"eletrica": 5, "eletromecanica": 4, "ti": 1, "mecanica": 1},
    },
    {
        "nome": "Costura Industrial",
        "descricao": "Operação de máquinas industriais e produção em série de vestuário.",
        "duracao": 200,
        "area_principal": "costura",
        "peso": {"costura": 5, "mecanica": 1},
    },
    {
        "nome": "Modelagem e Corte de Vestuário",
        "descricao": "Interpretação de moldes, escalonamento e encaixe de tecido.",
        "duracao": 160,
        "area_principal": "costura",
        "peso": {"costura": 5, "ti": 1},
    },
    {
        "nome": "Python para Análise de Dados",
        "descricao": "Tratamento de dados, visualização e automação de relatórios.",
        "duracao": 80,
        "area_principal": "ti",
        "peso": {"ti": 5, "ia": 4},
    },
    {
        "nome": "Fundamentos de Inteligência Artificial",
        "descricao": "Aprendizado de máquina, modelos preditivos e ética em IA.",
        "duracao": 100,
        "area_principal": "ia",
        "peso": {"ia": 5, "ti": 4},
    },
    {
        "nome": "Redes e Infraestrutura de TI",
        "descricao": "Cabeamento estruturado, switches, roteadores e suporte técnico.",
        "duracao": 160,
        "area_principal": "ti",
        "peso": {"ti": 5, "eletrica": 2, "eletromecanica": 1},
    },
    {
        "nome": "Mecânica de Motores a Combustão",
        "descricao": "Desmontagem, diagnóstico e retífica de motores ciclo Otto e Diesel.",
        "duracao": 200,
        "area_principal": "mecanica-automotiva",
        "peso": {"mecanica-automotiva": 5, "mecanica": 3, "eletromecanica": 1},
    },
    {
        "nome": "Injeção Eletrônica Automotiva",
        "descricao": "Sensores, atuadores e diagnóstico com scanner automotivo.",
        "duracao": 120,
        "area_principal": "mecanica-automotiva",
        "peso": {"mecanica-automotiva": 5,"eletrica": 3,"mecanica": 2,"eletromecanica": 2,"ti": 1,},
    },
    {
        "nome": "Usinagem CNC",
        "descricao": "Programação de tornos e centros de usinagem, metrologia dimensional.",
        "duracao": 220,
        "area_principal": "mecanica",
        "peso": {"mecanica": 5,"ti": 2,"eletromecanica": 2,"eletrica": 1,"mecanica-automotiva": 1,},
    },
    {
        "nome": "Manutenção Eletromecânica Industrial",
        "descricao": "Manutenção preventiva e corretiva de máquinas e sistemas industriais.",
        "duracao": 240,
        "area_principal": "eletromecanica",
        "peso": {"eletromecanica": 5,"eletrica": 4,"mecanica": 4,"ti": 1,"mecanica-automotiva": 1,},
    },
    {
        "nome": "Automação Industrial",
        "descricao": "Integração de CLP, IHM, sensores e redes industriais.",
        "duracao": 180,
        "area_principal": "eletromecanica",
        "peso": {"eletromecanica": 5,"eletrica": 4,"ti": 3,"ia": 2,"mecanica": 2,"mecanica-automotiva": 1,},
    },#kauã começou aq
    {
        "nome": "Analista de Recursos Humanos",
        "descricao": "Gestão de pessoas, recrutamento, seleção e desenvolvimento organizacional.",
        "duracao": 120,
        "area_principal": "rh",
        "peso": {"rh": 5,"marketing": 2,"ti": 1}
    },
    {
        "nome": "Assistente Financeiro",
        "descricao": "Controle de contas a pagar e receber, fluxo de caixa e conciliação bancária.",
        "duracao": 160,
        "area_principal": "financas",
        "peso": {"financas": 5,"rh": 2,"marketing": 1}
    },
    {
        "nome": "Auxiliar de Operação de Processos Metalúrgicos",
        "descricao": "Apoio na operação de fornos, laminação e tratamento térmico de metais.",
        "duracao": 160,
        "area_principal": "metalurgia",
        "peso": {"metalurgia": 5,"mecanica": 3,"eletromecanica": 2,"eletrica": 1}
    },
    {
        "nome": "Caldeireiro Montador",
        "descricao": "Montagem e manutenção de caldeiras, vasos de pressão e tubulações industriais.",
        "duracao": 160,
        "area_principal": "metalurgia",
        "peso": {"metalurgia": 5,"mecanica": 4,"eletromecanica": 3,"eletrica": 2}
    },
    {
        "nome": "Fundição Artística por Cera Perdida",
        "descricao": "Técnicas de fundição artística utilizando o processo de cera perdida.",
        "duracao": 32,
        "area_principal": "metalurgia",
        "peso": {"metalurgia": 5,"design": 4,"mecanica": 2,"eletromecanica": 1}
    },
    {
        "nome":"Inspeção de Qualidade em Soldagem",
        "descricao":"Técnicas de inspeção visual, ensaios não destrutivos e normas de soldagem.",
        "duracao": 48,
        "area_principal": "metalurgia",
        "peso": {"metalurgia": 5,"mecanica": 3,"eletromecanica": 2,"eletrica": 1}
    },
    {
        "nome":"Operação e Programação de Robô de Soldagem MAG",
        "descricao":"Programação e operação de robôs de soldagem MAG, incluindo segurança e manutenção.",
        "duracao": 72,
        "area_principal": "metalurgia",
        "peso": {"metalurgia": 5,"mecanica": 4,"eletromecanica": 3,"eletrica": 2,"ti": 1}
    },
    {
        "nome":"Especialização Profissional de Inspetor de Líquido Penetrante N1/N2",
        "descricao":"Formação avançada para inspetores de líquidos penetrantes, incluindo normas e técnicas de ensaio.",
        "duracao": 60,
        "area_principal": "metalurgia",
        "peso": {"metalurgia": 5,"mecanica": 3,"eletromecanica": 2,"eletrica": 1}
    }
]


class Command(BaseCommand):
    help = "Cria ou atualiza os cursos do catálogo com seus pesos por área."

    @transaction.atomic
    def handle(self, *args, **options):
        areas = {area.slug: area for area in Area.objects.all()}
        if not areas:
            raise CommandError(
                "Nenhuma área cadastrada. Rode antes: manage.py seed_areas"
            )

        for data in CURSOS:
            usadas = set(data["peso"]) | {data["area_principal"]}
            desconhecidas = usadas - set(areas)
            if desconhecidas:
                raise CommandError(
                    f"Curso '{data['nome']}' usa áreas inexistentes: {sorted(desconhecidas)}"
                )

            curso, created = Curso.objects.update_or_create(
                nome_curso=data["nome"],
                defaults={
                    "descricao": data["descricao"],
                    "duracao": data["duracao"],
                    "area_principal": areas[data["area_principal"]],
                    "is_active": True,
                },
            )

            for slug, peso in data["peso"].items():
                Peso_curso.objects.update_or_create(
                    curso=curso,
                    area=areas[slug],
                    defaults={"peso": peso},
                )

            # tira pesos que sobraram de cadastros anteriores
            removidos, _ = curso.curso_peso.exclude(
                area__slug__in=data["peso"]
            ).delete()

            acao = "criado" if created else "atualizado"
            extra = f" (-{removidos} peso obsoleto)" if removidos else ""
            self.stdout.write(
                self.style.SUCCESS(
                    f"Curso {acao}: {curso.nome_curso} [{len(data['peso'])} pesos]{extra}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"\nTotal: {len(CURSOS)} cursos no catálogo.")
        )
