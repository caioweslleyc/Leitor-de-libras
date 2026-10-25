# Leitor de Libras (versão intermediária)

## Rodar
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

## Usar
1. **Abrir câmera**.
2. Em **Gestos**, grave pelo menos 2 gestos, incluindo **NENHUM** (mão relaxada).
3. O modelo é treinado automaticamente a cada gesto adicionado ou removido.
4. Faça o gesto: a resposta aparece abaixo da câmera.

## Arquivos
- `app.py` – servidor Flask, banco SQLite (`dados.db`) e modelo (`modelo.joblib`)
- `templates/index.html` – página
- `static/style.css` – visual
- `static/app.js` – câmera, MediaPipe, gravação e reconhecimento
