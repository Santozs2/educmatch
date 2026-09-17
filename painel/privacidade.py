
K_MINIMO = 5
SUPRIMIDO = None


def suprimir_pequenos(linhas, campo="total", k=K_MINIMO):

    resultado = []
    for linha in linhas:
        copia = dict(linha)
        if copia.get(campo) is not None and copia[campo] < k:
            copia[campo] = SUPRIMIDO
            copia["suprimido"] = True
        resultado.append(copia)
    return resultado


def periodo_tem_massa_suficiente(total_de_tentativas, k=K_MINIMO):
    return total_de_tentativas >= k