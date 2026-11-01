
import cv2
import time

from detector import DetectorMaos
from desenho import desenhar_maos
from banco import (
    criar_banco,
    salvar_sinal,
    carregar_sinais,
    identificar_gesto
)

NOME_JANELA = "Leitor de Libras"

camera = None
detector = None

criar_banco()

# Carregar os gestos cadastrados
sinais = carregar_sinais()

try:
    detector = DetectorMaos()

    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    cv2.namedWindow(NOME_JANELA, cv2.WINDOW_NORMAL)

    inicio = time.monotonic()
    ultimo_timestamp = -1

    while True:
        sucesso, frame = camera.read()

        if not sucesso:
            print("Erro ao acessar a câmera!")
            break

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        timestamp = int((time.monotonic() - inicio) * 1000)
        timestamp = max(timestamp, ultimo_timestamp + 1)
        ultimo_timestamp = timestamp

        resultado = detector.detectar(rgb, timestamp)

        frame = desenhar_maos(frame, resultado)

        # Reconhecer o gesto atual
        gesto = identificar_gesto(resultado, sinais)

        # Mostrar somente quando reconhecer
        if gesto is not None:
            cv2.putText(
                frame,
                gesto,
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 255, 0),
                3
            )

        cv2.imshow(NOME_JANELA, frame)

        tecla = cv2.waitKey(1) & 0xFF

        # Cadastrar gesto
        if tecla == ord("s"):
            nome = input("Digite o nome do gesto: ").strip()

            if nome:
                if salvar_sinal(nome, resultado):
                    sinais = carregar_sinais()

        elif tecla == ord("q"):
            break

finally:
    if camera is not None:
        camera.release()

    if detector is not None:
        detector.fechar()

    cv2.destroyAllWindows()
