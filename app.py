"""
Servidor do Leitor de Libras (versão simples).

O que ele faz:
  1. Entrega a página (rota "/").
  2. Guarda no banco os exemplos de cada gesto (amostras).
  3. Treina o modelo de Machine Learning com esses exemplos.
  4. Recebe os números de uma mão e responde qual gesto é.
"""
import json
import sqlite3
from pathlib import Path

import joblib
from flask import Flask, jsonify, render_template, request
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# >>> Troque pelo link do repositório de vocês <<<
GITHUB_URL = "https://github.com/SEU-USUARIO/SEU-REPOSITORIO"

PASTA = Path(__file__).parent
BANCO = PASTA / "dados.db"          # arquivo do banco de dados (SQLite)
ARQUIVO_MODELO = PASTA / "modelo.joblib"  # modelo treinado salvo em disco
N_NUMEROS = 63                      # 21 pontos da mão x (x, y, z)

app = Flask(__name__)
modelo = None  # modelo carregado na memória (None = ainda não treinado)


# ---------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------
def conectar():
    return sqlite3.connect(BANCO)


def criar_tabela():
    with conectar() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS amostras (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   sinal TEXT NOT NULL,      -- nome do gesto, ex.: OLÁ
                   numeros TEXT NOT NULL     -- os 63 números, guardados como texto JSON
               )"""
        )


# ---------------------------------------------------------------
# Treino do modelo
# ---------------------------------------------------------------
def treinar():
    """Lê todas as amostras do banco, treina o modelo e salva em disco."""
    global modelo
    with conectar() as c:
        linhas = c.execute("SELECT sinal, numeros FROM amostras").fetchall()

    nomes = [l[0] for l in linhas]
    X = [json.loads(l[1]) for l in linhas]  # lista de listas de 63 números

    if len(set(nomes)) < 2:
        modelo = None
        ARQUIVO_MODELO.unlink(missing_ok=True)
        return {"pronto": False, "mensagem": "Cadastre pelo menos 2 gestos (inclua o NENHUM) para o sistema aprender."}

    # Teste rápido de qualidade: separa 20% das amostras só para testar.
    acuracia = None
    try:
        X_treino, X_teste, y_treino, y_teste = train_test_split(
            X, nomes, test_size=0.2, stratify=nomes, random_state=42
        )
        teste = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_treino, y_treino)
        acuracia = teste.score(X_teste, y_teste)
    except ValueError:
        pass  # poucas amostras para separar o teste

    # Modelo final: aprende com TODAS as amostras.
    modelo = RandomForestClassifier(n_estimators=100, random_state=42).fit(X, nomes)
    joblib.dump(modelo, ARQUIVO_MODELO)

    texto = f"Modelo atualizado com {len(set(nomes))} gestos."
    if acuracia is not None:
        texto += f" Acerto no teste: {acuracia * 100:.0f}%."
    return {"pronto": True, "mensagem": texto}


# ---------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------
@app.get("/")
def pagina():
    return render_template("index.html", github_url=GITHUB_URL)


@app.get("/api/gestos")
def listar_gestos():
    """Devolve cada gesto e quantas amostras ele tem."""
    with conectar() as c:
        linhas = c.execute("SELECT sinal, COUNT(*) FROM amostras GROUP BY sinal ORDER BY sinal").fetchall()
    return jsonify(gestos=[{"nome": n, "total": t} for n, t in linhas], modelo_pronto=modelo is not None)


@app.post("/api/gestos")
def adicionar_gesto():
    """Guarda as amostras de um gesto e treina o modelo de novo."""
    dados = request.get_json()
    nome = str(dados.get("sinal", "")).strip().upper()
    amostras = dados.get("amostras", [])

    if not nome or not amostras:
        return jsonify(erro="Informe o nome e grave as amostras."), 400
    if any(len(a) != N_NUMEROS for a in amostras):
        return jsonify(erro="Formato de amostra inválido."), 400

    with conectar() as c:
        c.executemany(
            "INSERT INTO amostras (sinal, numeros) VALUES (?, ?)",
            [(nome, json.dumps(a)) for a in amostras],
        )
    return jsonify(salvas=len(amostras), treino=treinar())


@app.delete("/api/gestos/<nome>")
def remover_gesto(nome):
    """Apaga todas as amostras de um gesto e treina o modelo de novo."""
    with conectar() as c:
        c.execute("DELETE FROM amostras WHERE sinal = ?", (nome.upper(),))
    return jsonify(treino=treinar())


@app.post("/api/prever")
def prever():
    """Recebe os 63 números de uma mão e devolve o gesto mais provável."""
    if modelo is None:
        return jsonify(erro="Modelo ainda não treinado."), 409
    numeros = request.get_json().get("numeros", [])
    if len(numeros) != N_NUMEROS:
        return jsonify(erro="Formato inválido."), 400

    probabilidades = modelo.predict_proba([numeros])[0]  # chance de cada gesto
    melhor = probabilidades.argmax()
    return jsonify(sinal=str(modelo.classes_[melhor]), confianca=float(probabilidades[melhor]))


criar_tabela()
if ARQUIVO_MODELO.exists():
    modelo = joblib.load(ARQUIVO_MODELO)

if __name__ == "__main__":
    app.run(debug=True)
