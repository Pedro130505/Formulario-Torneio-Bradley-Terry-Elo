/**
 * Lógica do Duelo / Torneio Bradley-Terry / Elo
 * Suporte a atalhos de teclado, áudio sintético Web Audio API e UI fluida.
 */

// Estado Global
let parAtual = null;
let bloqueado = false;
let votosNestaSessao = 0;
let somAtivado = true;

// Inicialização de UID e Canal
function obterOuCriarUid() {
  const STORAGE_KEY = 'torneio_auto_uid';
  const urlParams = new URLSearchParams(window.location.search);
  let uid = urlParams.get('uid');

  if (!uid) {
    uid = localStorage.getItem(STORAGE_KEY);
  }

  if (!uid) {
    const sufixo = (window.crypto && crypto.randomUUID)
      ? crypto.randomUUID().split('-')[0]
      : Math.random().toString(36).substring(2, 10);
    uid = 'u_' + sufixo;
  }

  localStorage.setItem(STORAGE_KEY, uid);

  // Mantém na URL visível
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('uid', uid);
    window.history.replaceState({}, '', url.toString());
  } catch (e) {}

  return uid;
}

function obterCanal() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('canal') || 'geral';
}

const UID = obterOuCriarUid();
const CANAL = obterCanal();

// Som sintético agradável via Web Audio API (Offline & Zero dependência externa)
function tocarSomVoto() {
  if (!somAtivado) return;
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.08); // A5

    gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.12);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + 0.12);
  } catch (e) {
    // Silencia se áudio for bloqueado pelo navegador
  }
}

// Toast Notificações
function mostrarToast(mensagem, icone = '✅') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>${icone}</span> <span>${escaparHtml(mensagem)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'all 0.3s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}

// Carregamento de Duelos
async function carregarProximoPar() {
  bloqueado = false;
  const statusEl = document.getElementById('statusTexto');
  if (statusEl) statusEl.textContent = 'Buscando próximo duelo equilibrado...';

  const container = document.getElementById('dueloContainer');
  if (container) {
    container.style.opacity = '0.6';
  }

  try {
    const res = await fetch(`/api/proximo-par?uid=${encodeURIComponent(UID)}&canal=${encodeURIComponent(CANAL)}`);
    const data = await res.json();

    if (data.status === 'ok') {
      parAtual = data;
      renderizarDuelo(data.itemA, data.itemB);

      const contadorEl = document.getElementById('contadorUsuario');
      if (contadorEl) {
        contadorEl.textContent = data.totalRespondidosUsuario;
      }

      if (statusEl) {
        statusEl.textContent = 'Escolha o seu preferido ou use os atalhos do teclado.';
      }
    } else {
      mostrarTelaFinal(data.mensagem || 'Não há duelos disponíveis no momento.');
    }
  } catch (err) {
    console.error('Erro ao buscar próximo duelo:', err);
    if (statusEl) statusEl.textContent = 'Erro ao conectar ao servidor. Tentando novamente...';
  } finally {
    if (container) {
      container.style.opacity = '1';
    }
  }
}

// Renderização dos Cards
function renderizarDuelo(itemA, itemB) {
  const container = document.getElementById('dueloContainer');
  if (!container) return;

  container.innerHTML = `
    ${gerarHtmlCard(itemA, 'itemA', '1', '←')}
    <div class="vs-badge">VS</div>
    ${gerarHtmlCard(itemB, 'itemB', '2', '→')}
  `;
}

function gerarHtmlCard(item, sideKey, keyNumber, keyArrow) {
  const imgUrl = item.imagem_url || 'https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=600&auto=format&fit=crop&q=80';
  return `
    <div class="duel-card" id="card-${item.id}" onclick="votar('${item.id}')">
      <div class="card-kbd" title="Atalho de teclado">[${keyNumber}] ou [${keyArrow}]</div>
      <div class="card-photo-wrapper">
        <img src="${escaparHtml(imgUrl)}" alt="${escaparHtml(item.nome)}" class="card-photo" loading="lazy" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=600&auto=format&fit=crop&q=80'">
      </div>
      <div>
        <h3 class="card-title">${escaparHtml(item.nome)}</h3>
        <p class="card-desc">${escaparHtml(item.descricao || '')}</p>
      </div>
      <div class="card-action-btn">
        <span>Escolher este brinde</span>
        <span>✨</span>
      </div>
    </div>
  `;
}

// Registro de Voto
async function votar(vencedorId) {
  if (bloqueado || !parAtual) return;
  bloqueado = true;

  tocarSomVoto();

  // Feedback visual instantâneo
  const cardSelecionado = document.getElementById(`card-${vencedorId}`);
  if (cardSelecionado) {
    cardSelecionado.classList.add('selected');
  }

  const statusEl = document.getElementById('statusTexto');
  if (statusEl) statusEl.textContent = 'Registrando escolha e recalculando Elo...';

  try {
    const payload = {
      uid: UID,
      canal: CANAL,
      item_a_id: parAtual.itemA.id,
      item_b_id: parAtual.itemB.id,
      vencedor_id: vencedorId
    };

    const res = await fetch('/api/voto', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok && data.status === 'ok') {
      votosNestaSessao++;
      const sessaoEl = document.getElementById('contadorSessao');
      if (sessaoEl) sessaoEl.textContent = votosNestaSessao;

      mostrarToast('Escolha registrada com sucesso!', '✨');
      
      // Transição suave para o próximo par
      setTimeout(() => {
        carregarProximoPar();
      }, 180);
    } else {
      bloqueado = false;
      mostrarToast(data.detail || 'Erro ao registrar voto.', '⚠️');
      if (cardSelecionado) cardSelecionado.classList.remove('selected');
    }
  } catch (err) {
    bloqueado = false;
    if (cardSelecionado) cardSelecionado.classList.remove('selected');
    console.error('Erro ao enviar voto:', err);
    mostrarToast('Falha na conexão ao salvar voto.', '❌');
  }
}

// Pular Duelo Atual
function pularDuelo() {
  if (bloqueado) return;
  mostrarToast('Duelo ignorado. Carregando outro...', '⏭️');
  carregarProximoPar();
}

// Concluir e Sair
function encerrarParticipacao() {
  mostrarTelaFinal(`Você respondeu ${votosNestaSessao} duelo(s) nesta sessão. Seus votos foram salvos com sucesso!`);
}

function mostrarTelaFinal(mensagem) {
  const areaJogo = document.getElementById('areaJogo');
  const areaFinal = document.getElementById('areaFinal');
  const textoFinal = document.getElementById('textoFinal');

  if (areaJogo) areaJogo.style.display = 'none';
  if (areaFinal) areaFinal.style.display = 'block';
  if (textoFinal) textoFinal.textContent = mensagem;
}

function reiniciarSessao() {
  const areaJogo = document.getElementById('areaJogo');
  const areaFinal = document.getElementById('areaFinal');

  if (areaFinal) areaFinal.style.display = 'none';
  if (areaJogo) areaJogo.style.display = 'block';
  carregarProximoPar();
}

// Controle de Som
function alternarSom() {
  somAtivado = !somAtivado;
  const btn = document.getElementById('btnSom');
  if (btn) {
    btn.innerHTML = somAtivado ? '🔊' : '🔇';
    btn.title = somAtivado ? 'Silenciar efeitos sonoros' : 'Ativar efeitos sonoros';
  }
}

// Escape de HTML para segurança
function escaparHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Atalhos de Teclado
document.addEventListener('keydown', function(e) {
  // Ignora se estiver digitando em inputs
  if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

  if (!parAtual || bloqueado) return;

  if (e.key === '1' || e.key === 'ArrowLeft') {
    e.preventDefault();
    votar(parAtual.itemA.id);
  } else if (e.key === '2' || e.key === 'ArrowRight') {
    e.preventDefault();
    votar(parAtual.itemB.id);
  } else if (e.key === ' ' || e.key === 's' || e.key === 'S') {
    e.preventDefault();
    pularDuelo();
  }
});

// Inicialização ao carregar página
document.addEventListener('DOMContentLoaded', () => {
  const uidLabel = document.getElementById('uidLabel');
  if (uidLabel) {
    uidLabel.textContent = `${UID} (${CANAL})`;
  }

  carregarProximoPar();
});
