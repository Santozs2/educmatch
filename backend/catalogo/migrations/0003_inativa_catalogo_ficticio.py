from django.db import migrations

# Fica escrito aqui de propósito: o seed não lista mais estes cursos e áreas.
CURSOS_FICTICIOS = [
    "Eletricista Instalador",
    "Comandos Elétricos e CLP",
    "Costura Industrial",
    "Modelagem e Corte de Vestuário",
    "Python para Análise de Dados",
    "Fundamentos de Inteligência Artificial",
    "Redes e Infraestrutura de TI",
    "Mecânica de Motores a Combustão",
    "Injeção Eletrônica Automotiva",
    "Usinagem CNC",
    "Manutenção Eletromecânica Industrial",
    "Automação Industrial",
    "Analista de Recursos Humanos",
    "Assistente Financeiro",
    "Auxiliar de Operação de Processos Metalúrgicos",
    "Caldeireiro Montador",
    "Fundição Artística por Cera Perdida",
    "Inspeção de Qualidade em Soldagem",
    "Operação e Programação de Robô de Soldagem MAG",
    "Especialização Profissional de Inspetor de Líquido Penetrante N1/N2",
]
AREAS_ANTIGAS = [
    "costura", "eletrica", "eletromecanica", "financas", "ia", "marketing",
    "mecanica", "mecanica-automotiva", "metalurgia", "rh", "design",
]


def _marcar(apps, ativo):
    apps.get_model("catalogo", "Curso").objects.filter(nome_curso__in=CURSOS_FICTICIOS).update(is_active=ativo)
    apps.get_model("catalogo", "Area").objects.filter(slug__in=AREAS_ANTIGAS).update(is_active=ativo)


def inativar(apps, schema_editor):
    _marcar(apps, False)


def reativar(apps, schema_editor):
    _marcar(apps, True)


class Migration(migrations.Migration):
    """Só inativa: apagar levaria junto recomendações e respostas (CASCADE)."""

    dependencies = [
        ("catalogo", "0002_campos_do_catalogo_senai"),
    ]

    operations = [
        migrations.RunPython(inativar, reativar),
    ]
