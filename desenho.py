import cv2

CONEXOES = [
    (0,1), (1,2), (2,3), (3,4),
    (0,5), (5,6), (6,7), (7,8),
    (5,9), (9,10), (10,11), (11,12),
    (9,13), (13,14), (14,15), (15,16),
    (13,17), (17,18), (18,19), (19,20),
    (0,17)
]

def desenhar_maos(frame, resultado):
    altura, largura, _ = frame.shape

    for i, mao in enumerate(resultado.hand_landmarks):

        lado = resultado.handedness[i][0].category_name

        if lado == "Right":
            cor = (255, 0, 0)  # Azul
        else:
            cor = (0, 0, 255)  # Vermelho

        pontos = []

        for ponto in mao:
            x = int(ponto.x * largura)
            y = int(ponto.y * altura)
            pontos.append((x, y))

        # Desenhar linhas
        for inicio, fim in CONEXOES:
            cv2.line(frame, pontos[inicio], pontos[fim], cor, 2)

        # Desenhar pontos brancos pequenos
        for x, y in pontos:
            cv2.circle(frame, (x, y), 3, (255, 255, 255), -1)

    return frame