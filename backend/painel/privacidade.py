K_MINIMO = 5
SUPRIMIDO = None


def suprimir_pequenos(linhas, campo="total", k=K_MINIMO):
    """Esconde o valor de toda célula com menos de k ocorrências.

    A linha continua na tabela e só o número some (vira SUPRIMIDO e ganha
    "suprimido": True). Esconder a linha inteira vazaria pela omissão: quem
    lê a tabela deduziria que o curso que faltou tem menos de k.
    Não altera a lista recebida: devolve cópias.
    """
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
