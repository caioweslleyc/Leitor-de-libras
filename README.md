# 🤟 Leitor de Libras

**Sistema experimental de reconhecimento de gestos estáticos de Libras utilizando Python, OpenCV e MediaPipe.**

## 📌 Sobre o projeto

O Leitor de Libras é um projeto de estudo que utiliza visão computacional para detectar as mãos por meio de uma webcam e reconhecer gestos estáticos previamente cadastrados.

A aplicação possui uma interface web desenvolvida com Flask, permitindo acompanhar a câmera e visualizar o resultado do reconhecimento pelo navegador.

## 🎯 Funcionalidades

- Detecção de até duas mãos.
- Identificação de 21 pontos de referência em cada mão.
- Desenho dos pontos e conexões das mãos.
- Cadastro de gestos com nomes personalizados.
- Armazenamento dos gestos em SQLite.
- Comparação de novos gestos com os cadastrados.
- Exibição do gesto reconhecido na interface web.

## 🛠️ Tecnologias

| Tecnologia | Utilização |
|---|---|
| Python | Linguagem principal |
| OpenCV | Captura e processamento de imagens |
| MediaPipe | Detecção das mãos |
| Flask | Aplicação web |
| SQLite | Banco de dados |
| HTML, CSS e JavaScript | Interface web |

## 📁 Estrutura do projeto

```text
Leitor-de-libras/
│
├── leitor_libras/
│   ├── __init__.py
│   ├── detector.py
│   ├── desenho.py
│   └── banco.py
│
├── modelos/
│   └── hand_landmarker.task
│
├── templates/
│   └── index.html
│
├── web.py
├── README.md
├── requirements.txt
└── .gitignore
```

## ⚙️ Como instalar

### 1. Clone o repositório

```bash
git clone URL_DO_REPOSITORIO
```

### 2. Entre na pasta

```bash
cd Leitor-de-libras
```

### 3. Instale as dependências

```bash
python -m pip install -r requirements.txt
```

### 4. Execute o projeto

```bash
python web.py
```

### 5. Abra no navegador

Acesse:

```text
http://127.0.0.1:5000
```

É necessário ter uma webcam disponível e o arquivo `hand_landmarker.task` dentro da pasta `modelos`.

## 🧠 Como funciona

1. A webcam captura imagens em tempo real.
2. O MediaPipe detecta as mãos.
3. O sistema identifica os pontos de referência.
4. O OpenCV desenha os pontos e as conexões.
5. Os dados são comparados com os gestos cadastrados.
6. Quando há correspondência, o nome do gesto é exibido na página.

## 🚧 Limitações e melhorias futuras

O projeto está direcionado ao reconhecimento de gestos estáticos. O método de comparação atual é experimental e pode confundir gestos semelhantes ou apresentar resultados diferentes conforme a posição e a orientação das mãos.

Melhorias planejadas:

- Aprimorar a precisão do reconhecimento.
- Melhorar a diferenciação entre gestos semelhantes.
- Aumentar o conjunto de gestos cadastrados.
- Melhorar a interface web.
- Estudar futuramente o reconhecimento de sinais dinâmicos.

## 📍 Status

**Em desenvolvimento.**

Projeto de estudo sobre Python, visão computacional e reconhecimento experimental de gestos de Libras.