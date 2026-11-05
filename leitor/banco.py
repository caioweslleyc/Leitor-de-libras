import sqlite3
import json
import math


def conectar():
    return sqlite3.connect("libras.db")


def criar_banco():
    conexao = conectar()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS sinais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            maos TEXT NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()


def preparar_maos(maos):
    resultado = []

    for mao in maos:
        pontos = mao["pontos"]

        pulso = pontos[0]

        escala = math.sqrt(
            (pontos[9]["x"] - pulso["x"]) ** 2 +
            (pontos[9]["y"] - pulso["y"]) ** 2 +
            (pontos[9]["z"] - pulso["z"]) ** 2
        )

        if escala == 0:
            return None

        pontos_normalizados = []

        for ponto in pontos:
            pontos_normalizados.append([
                (ponto["x"] - pulso["x"]) / escala,
                (ponto["y"] - pulso["y"]) / escala,
                (ponto["z"] - pulso["z"]) / escala
            ])

        resultado.append({
            "lado": mao["lado"],
            "pontos": pontos_normalizados
        })

    return sorted(resultado, key=lambda m: m["lado"])


def capturar_maos(resultado):
    maos = []

    for i, mao in enumerate(resultado.hand_landmarks):
        lado = resultado.handedness[i][0].category_name

        pontos = []

        for ponto in mao:
            pontos.append({
                "x": ponto.x,
                "y": ponto.y,
                "z": ponto.z
            })

        maos.append({
            "lado": lado,
            "pontos": pontos
        })

    return maos


def comparar_maos(maos1, maos2):
    if len(maos1) != len(maos2):
        return 999

    total = 0
    quantidade = 0

    maos1 = preparar_maos(maos1)
    maos2 = preparar_maos(maos2)

    if maos1 is None or maos2 is None:
        return 999

    for mao1, mao2 in zip(maos1, maos2):

        if mao1["lado"] != mao2["lado"]:
            return 999

        for p1, p2 in zip(mao1["pontos"], mao2["pontos"]):

            distancia = math.sqrt(
                (p1[0] - p2[0]) ** 2 +
                (p1[1] - p2[1]) ** 2 +
                (p1[2] - p2[2]) ** 2
            )

            total += distancia
            quantidade += 1

    if quantidade == 0:
        return 999

    return total / quantidade


def carregar_sinais():
    conexao = conectar()

    registros = conexao.execute(
        "SELECT nome, maos FROM sinais"
    ).fetchall()

    conexao.close()

    sinais = []

    for nome, dados in registros:
        sinais.append({
            "nome": nome,
            "maos": json.loads(dados)
        })

    return sinais


def salvar_sinal(nome, resultado):
    maos = capturar_maos(resultado)

    if not maos:
        print("Nenhuma mão detectada!")
        return False

    sinais = carregar_sinais()

    for sinal in sinais:
        distancia = comparar_maos(maos, sinal["maos"])

        if distancia < 0.12:
            print(
                f"Este gesto é muito parecido com "
                f"'{sinal['nome']}'. Não foi cadastrado."
            )
            return False

    conexao = conectar()

    conexao.execute(
        "INSERT INTO sinais (nome, categoria, maos) VALUES (?, ?, ?)",
        (nome, "gesto", json.dumps(maos))
    )

    conexao.commit()
    conexao.close()

    print(f"Gesto '{nome}' cadastrado com sucesso!")

    return True


def identificar_gesto(resultado, sinais):
    maos = capturar_maos(resultado)

    if not maos:
        return None

    melhor_nome = None
    menor_distancia = 999

    for sinal in sinais:
        distancia = comparar_maos(maos, sinal["maos"])

        if distancia < menor_distancia:
            menor_distancia = distancia
            melhor_nome = sinal["nome"]

    if menor_distancia < 0.18:
        return melhor_nome

    return None
