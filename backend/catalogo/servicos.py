from urllib.parse import urlencode

from django.conf import settings
from django.utils.text import slugify


def url_curso_senai(curso):
    """A página do curso no site do SENAI. Sem link, a busca do curso na cidade da escola."""
    if curso.url_senai:
        return curso.url_senai

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
