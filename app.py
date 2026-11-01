
import cv2
import time
import threading

from flask import Flask, render_template, Response, jsonify, request

from detector import DetectorMaos
from desenho import desenhar_maos
from banco import criar_banco, salvar_sinal, carregar_sinais, identificar_gesto

app = Flask(__name__)

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

if not camera.isOpened():
    raise RuntimeError("Não foi possível abrir a câmera.")

detector = DetectorMaos()
criar_banco()

sinais = carregar_sinais()

lock = threading.Lock()

frame_atual = None
resultado_atual = None
gesto_atual = None


def processar_camera():
    global frame_atual, resultado_atual, gesto_atual, sinais

    inicio = time.monotonic()
    ultimo_timestamp = -1

    while True:
        sucesso, frame = camera.read()

        if not sucesso:
            continue

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        timestamp = int((time.monotonic() - inicio) * 1000)
        timestamp = max(timestamp, ultimo_timestamp + 1)
        ultimo_timestamp = timestamp

        resultado = detector.detectar(rgb, timestamp)

        frame = desenhar_maos(frame, resultado)

        gesto = identificar_gesto(resultado, sinais)

        if gesto:
            cv2.putText(
                frame,
                gesto,
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 255, 0),
                3
            )

        sucesso, imagem = cv2.imencode(".jpg", frame)

        if sucesso:
            with lock:
                frame_atual = imagem.tobytes()
                resultado_atual = resultado
                gesto_atual = gesto


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/video")
def video():
    def gerar():
        while True:
            with lock:
                imagem = frame_atual

            if imagem is not None:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + imagem + b"\r\n"
                )

            time.sleep(0.03)

    return Response(
        gerar(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/estado")
def estado():
    with lock:
        return jsonify({"gesto": gesto_atual})


@app.route("/salvar", methods=["POST"])
def salvar():
    global sinais

    dados = request.get_json()
    nome = dados.get("nome", "").strip()

    if not nome:
        return jsonify({"mensagem": "Digite o nome do gesto."}), 400

    with lock:
        resultado = resultado_atual

        if resultado is None or not resultado.hand_landmarks:
            return jsonify({"mensagem": "Nenhuma mão detectada."}), 400

        sucesso = salvar_sinal(nome, resultado)

        if sucesso:
            sinais = carregar_sinais()

    if sucesso:
        return jsonify({"mensagem": "Gesto salvo com sucesso!"})

    return jsonify({
        "mensagem": "Gesto muito parecido com outro já cadastrado."
    }), 400


if __name__ == "__main__":
    threading.Thread(
        target=processar_camera,
        daemon=True
    ).start()

    try:
        app.run(host="127.0.0.1", port=5000, debug=False)
    finally:
        camera.release()
        detector.fechar()
