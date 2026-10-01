from django import template

register = template.Library()


@register.filter
def duracao(valor):
    """timedelta -> "08:42" (min:seg) ou "1h05" acima de uma hora."""
    segundos = int(valor.total_seconds())
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    if horas:
        return f"{horas}h{minutos:02d}"
    return f"{minutos:02d}:{segundos:02d}"