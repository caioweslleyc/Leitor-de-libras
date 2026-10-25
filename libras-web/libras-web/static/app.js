// =====================================================================
// Leitor de Libras - código que roda no NAVEGADOR
//
// Fluxo:  câmera -> MediaPipe acha a mão -> 63 números -> servidor
//         (Flask) diz qual gesto é -> mostramos a palavra na tela.
// =====================================================================

// Importa a biblioteca do MediaPipe (detector de mãos), direto da internet.
import { HandLandmarker, FilesetResolver } from
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";

// Atalho para pegar elementos da página pelo id.
const $ = (id) => document.getElementById(id);

// ---------- Configurações ----------
const ARQUIVOS_WASM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";
const MODELO_MAOS = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";
const LIMIAR = 0.6;       // confiança mínima (60%) para aceitar uma resposta
const INTERVALO = 200;    // de quanto em quanto tempo (ms) perguntamos ao servidor
const SEGUNDOS_GRAVANDO = 5;

// ---------- Elementos da página ----------
const video = $("video");
const tela = $("tela");                 // canvas onde desenhamos os pontos
const ctx = tela.getContext("2d");

// ---------- Variáveis de estado (o que o programa "lembra") ----------
let detector = null;          // detector de mãos do MediaPipe
let cameraLigada = false;
let ultimoTempo = -1;         // evita processar o mesmo quadro duas vezes
let ultimosNumeros = null;    // os 63 números da mão no quadro atual (ou null)
let gravando = false;
let amostras = [];            // números coletados durante uma gravação
let contadorQuadros = 0;
let modeloPronto = false;     // o servidor já tem um modelo treinado?
let ocupado = false;          // já há uma pergunta em andamento ao servidor?
let recentes = [];            // últimas respostas (para não oscilar)
let ultimaPalavra = "";       // última palavra adicionada à frase
let semGesto = 0;             // quantas vezes seguidas não houve gesto
let frase = [];

// ---------- Utilidades ----------
const esperar = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Conversa com o servidor Flask e devolve a resposta em objeto.
async function enviar(url, metodo = "GET", corpo) {
  const resposta = await fetch(url, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  return resposta.json();
}

// =====================================================================
// 1) CÂMERA E DETECÇÃO DA MÃO
// =====================================================================
async function carregarDetector() {
  $("status").textContent = "Carregando detector de mãos…";
  const arquivos = await FilesetResolver.forVisionTasks(ARQUIVOS_WASM);
  detector = await HandLandmarker.createFromOptions(arquivos, {
    baseOptions: { modelAssetPath: MODELO_MAOS },
    runningMode: "VIDEO",
    numHands: 1,                       // uma mão só: deixa tudo mais simples e estável
  });
}

async function ligarCamera() {
  $("btnCamera").disabled = true;
  try {
    if (!detector) await carregarDetector();
    // Pede permissão e abre a webcam.
    const fluxo = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
    video.srcObject = fluxo;
    await video.play();
    tela.width = video.videoWidth;     // canvas do mesmo tamanho do vídeo
    tela.height = video.videoHeight;

    cameraLigada = true;
    $("placeholder").hidden = true;
    $("btnCamera").textContent = "Desligar câmera";
    $("btnGravar").disabled = false;
    $("btnGravarNenhum").disabled = false;
    $("status").textContent = "Câmera ligada";
    requestAnimationFrame(repetir);    // começa o laço de detecção
  } catch (erro) {
    $("status").textContent = "Não foi possível abrir a câmera: " + erro.message;
  }
  $("btnCamera").disabled = false;
}

function desligarCamera() {
  cameraLigada = false;
  video.srcObject.getTracks().forEach((t) => t.stop());
  video.srcObject = null;
  ctx.clearRect(0, 0, tela.width, tela.height);
  ultimosNumeros = null;
  $("placeholder").hidden = false;
  $("btnCamera").textContent = "Abrir câmera";
  $("btnGravar").disabled = true;
  $("btnGravarNenhum").disabled = true;
  $("status").textContent = "Câmera desligada";
  atualizarSeloMao(false);
  mostrarResposta(null);
}

$("btnCamera").onclick = () => (cameraLigada ? desligarCamera() : ligarCamera());

// Roda uma vez por quadro de vídeo, enquanto a câmera estiver ligada.
function repetir() {
  if (!cameraLigada) return;

  if (video.currentTime !== ultimoTempo) {          // só se for um quadro novo
    ultimoTempo = video.currentTime;
    const resultado = detector.detectForVideo(video, performance.now());
    const mao = resultado.landmarks[0];             // os 21 pontos (ou undefined)

    desenharMao(mao);
    ultimosNumeros = mao ? calcularNumeros(mao) : null;
    atualizarSeloMao(!!mao);

    // Durante a gravação, guarda 1 a cada 3 quadros (quadros vizinhos são quase iguais).
    if (gravando && ultimosNumeros) {
      contadorQuadros++;
      if (contadorQuadros % 3 === 0) amostras.push(ultimosNumeros);
    }
  }
  requestAnimationFrame(repetir);                   // pede o próximo quadro
}

function atualizarSeloMao(detectada) {
  $("maoStatus").textContent = detectada ? "Mão: detectada" : "Mão: não detectada";
  $("maoStatus").classList.toggle("ativo", detectada);
}

// Desenha os 21 pontos e as linhas da mão sobre o vídeo.
function desenharMao(mao) {
  ctx.clearRect(0, 0, tela.width, tela.height);
  if (!mao) return;
  const L = tela.width, A = tela.height;

  ctx.strokeStyle = "#0969da";
  ctx.lineWidth = 3;
  for (const ligacao of HandLandmarker.HAND_CONNECTIONS) {
    ctx.beginPath();
    ctx.moveTo(mao[ligacao.start].x * L, mao[ligacao.start].y * A);
    ctx.lineTo(mao[ligacao.end].x * L, mao[ligacao.end].y * A);
    ctx.stroke();
  }
  for (const ponto of mao) {
    ctx.beginPath();
    ctx.arc(ponto.x * L, ponto.y * A, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.stroke();
  }
}

// Transforma os 21 pontos em 63 números que NÃO dependem de onde a mão está
// na tela nem do tamanho dela:
//   1) subtrai a posição do punho (ponto 0)  -> posição some
//   2) divide pelo tamanho da mão            -> tamanho some
function calcularNumeros(mao) {
  const punho = mao[0];
  let tamanho = 0;
  for (const p of mao) tamanho = Math.max(tamanho, Math.hypot(p.x - punho.x, p.y - punho.y));
  if (tamanho === 0) tamanho = 1;

  const numeros = [];
  for (const p of mao) {
    numeros.push((p.x - punho.x) / tamanho, (p.y - punho.y) / tamanho, (p.z - punho.z) / tamanho);
  }
  return numeros;   // 21 pontos x 3 = 63 números
}

// =====================================================================
// 2) GRAVAR, ADICIONAR E REMOVER GESTOS
// =====================================================================
async function gravar(nome) {
  nome = nome.trim().toUpperCase();
  if (!cameraLigada) { $("msgGestos").textContent = "Abra a câmera primeiro."; return; }
  if (!nome) { $("msgGestos").textContent = "Digite o nome do gesto."; return; }

  $("btnGravar").disabled = $("btnGravarNenhum").disabled = true;

  for (let s = 3; s > 0; s--) {                    // contagem regressiva
    $("msgGestos").textContent = `Prepare o gesto "${nome}"… ${s}`;
    await esperar(1000);
  }

  amostras = []; contadorQuadros = 0; gravando = true;
  for (let s = SEGUNDOS_GRAVANDO; s > 0; s--) {
    $("msgGestos").textContent = `Gravando… ${s}s (${amostras.length} amostras). Mova a mão devagar.`;
    await esperar(1000);
  }
  gravando = false;

  if (amostras.length < 15) {
    $("msgGestos").textContent = "Poucas amostras: mantenha a mão visível na câmera e tente de novo.";
  } else {
    const r = await enviar("/api/gestos", "POST", { sinal: nome, amostras });
    $("msgGestos").textContent = r.erro || `${r.salvas} amostras salvas. ${r.treino.mensagem}`;
    $("nomeGesto").value = "";
    await carregarGestos();
  }
  $("btnGravar").disabled = $("btnGravarNenhum").disabled = !cameraLigada;
}

$("btnGravar").onclick = () => gravar($("nomeGesto").value);
$("btnGravarNenhum").onclick = () => gravar("NENHUM");

async function removerGesto(nome) {
  if (!confirm(`Remover o gesto ${nome}?`)) return;
  const r = await enviar("/api/gestos/" + encodeURIComponent(nome), "DELETE");
  $("msgGestos").textContent = `"${nome}" removido. ${r.treino.mensagem}`;
  await carregarGestos();
}

// Busca no servidor a lista de gestos e desenha na página.
async function carregarGestos() {
  const dados = await enviar("/api/gestos");
  modeloPronto = dados.modelo_pronto;

  const lista = $("listaGestos");
  lista.innerHTML = "";
  if (dados.gestos.length === 0) {
    lista.innerHTML = '<li class="apagado">Nenhum gesto cadastrado ainda.</li>';
  }
  for (const g of dados.gestos) {
    const item = document.createElement("li");
    const texto = document.createElement("span");
    texto.textContent = `${g.nome} (${g.total} amostras)`;
    const botao = document.createElement("button");
    botao.textContent = "Remover";
    botao.onclick = () => removerGesto(g.nome);
    item.append(texto, botao);
    lista.appendChild(item);
  }
}

// =====================================================================
// 3) RECONHECER E MOSTRAR A RESPOSTA
// =====================================================================
async function reconhecer() {
  // Só pergunta ao servidor se há câmera, mão visível e modelo treinado.
  if (!cameraLigada || !modeloPronto || ocupado) return;
  if (!ultimosNumeros) { registrarSemGesto(); return; }

  ocupado = true;
  const r = await enviar("/api/prever", "POST", { numeros: ultimosNumeros });
  ocupado = false;
  if (r.erro) return;

  // Guarda as últimas 4 respostas; só aceita quando 3 delas concordam.
  recentes.push(r.confianca >= LIMIAR ? r.sinal : "?");
  if (recentes.length > 4) recentes.shift();
  const atual = recentes[recentes.length - 1];
  const votos = recentes.filter((x) => x === atual).length;

  if (atual !== "?" && atual !== "NENHUM" && votos >= 3) {
    mostrarResposta(atual, r.confianca);
    semGesto = 0;
    if (atual !== ultimaPalavra) {          // novo gesto -> entra na frase
      ultimaPalavra = atual;
      frase.push(atual);
      mostrarFrase();
    }
  } else {
    registrarSemGesto();
  }
}
setInterval(reconhecer, INTERVALO);          // repete a cada 200 ms

function registrarSemGesto() {
  mostrarResposta(null);
  semGesto++;
  if (semGesto >= 3) ultimaPalavra = "";     // mão saiu: o mesmo gesto pode entrar de novo
}

function mostrarResposta(palavra, confianca) {
  $("palavra").textContent = palavra || (modeloPronto ? "Aguardando gesto" : "Cadastre gestos para começar");
  $("palavra").classList.toggle("vazio", !palavra);
  $("confianca").textContent = palavra ? `confiança ${Math.round(confianca * 100)}%` : "";
}

function mostrarFrase() {
  $("frase").textContent = frase.join(" ");
}
$("btnLimpar").onclick = () => { frase = []; ultimaPalavra = ""; mostrarFrase(); };
$("btnFalar").onclick = () => {
  const fala = new SpeechSynthesisUtterance(frase.join(" ").toLowerCase());
  fala.lang = "pt-BR";
  speechSynthesis.speak(fala);
};

// =====================================================================
// 4) EXTRA: o quadro 2 aparece suavemente quando a pessoa rola a página
// =====================================================================
new IntersectionObserver((entradas) => {
  entradas.forEach((e) => e.isIntersecting && $("app").classList.add("in"));
}, { threshold: 0.12 }).observe($("app"));

// Ao abrir a página:
carregarGestos().then(() => mostrarResposta(null));
