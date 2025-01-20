def contar_ofertas_positivas(ofertas):
    """Conta quantos agentes têm uma oferta positiva para cada bem."""
    # Inicializa uma lista para contar ofertas positivas
    contador_ofertas = [0] * len(ofertas[0])  # Cria uma lista de zeros com o tamanho da primeira lista

    # Itera por cada agente nas ofertas
    for oferta in ofertas:
        for i, quantidade in enumerate(oferta):
            if quantidade > 0:
                contador_ofertas[i] += 1  # Incrementa o contador para o índice correspondente

    return contador_ofertas

# Exemplo de uso
ofertas = [
    [1, 0, 0, 0, 4, 1],
    [0, 0, 2, 3, 4, 0],
    [0, 0, 0, 1, 0, 0],
    [3, 0, 1, 1, 1, 1]
]

resultado = contar_ofertas_positivas(ofertas)
print(resultado)  # Saída: [2, 0, 2, 3, 3, 2]
