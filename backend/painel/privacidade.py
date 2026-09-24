
K_MINIMO = 5
SUPRIMIDO = None


def suprimir_pequenos(linhas, campo="total", k=K_MINIMO):
    """Mantém os valores pequenos visíveis no dashboard.

    A regra de privacidade continua protegendo o período mínimo, mas os
    valores individuais menores que 5 não são mais ocultados.
    """
    return [dict(linha) for linha in linhas]


def periodo_tem_massa_suficiente(total_de_tentativas, k=K_MINIMO):
    return total_de_tentativas >= k