from urllib.parse import urlencode

from django.conf import settings
from django.utils.text import slugify


def url_curso_senai(curso):
    """A busca do curso no site do SENAI, na cidade da escola: é lá que o aluno se inscreve."""
    endereco = settings.ESCOLA.get("endereco", "")
    partes_endereco = [parte.strip() for parte in endereco.split(",") if parte.strip()]
    cidade = partes_endereco[-2] if len(partes_endereco) >= 2 else ""
    if cidade:
        cidade = cidade.rsplit(" - ", 1)[0].strip()

    parametros = []
    if cidade:
        parametros.append(("cidadeint", slugify(cidade)))
    parametros.extend((("pesquisa", curso.nome_curso), ("pag", 1)))
    return f"https://www.sp.senai.br/cursos/0/0?{urlencode(parametros)}"
