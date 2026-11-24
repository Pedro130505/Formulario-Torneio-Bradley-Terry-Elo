/**
 * Mercado em Conexão - Controlador de Fluxo Integrado (Versão 3.0)
 * Gerencia Inscrição Oficial, Duelo de Brindes e Duelo de Palestras por Engenharia.
 */

// Estado Global da Aplicação
const Estado = {
  uid: '',
  iniciativa: 'Geral',
  nome: '',
  curso: '',
  etapaAtual: 1, // 1: Form, 2: Brindes, 3: Palestras, 4: Final
  parAtualBrinde: null,
  parAtualPalestra: null,
  bloqueado: false,
  votosBrindes: 0,
  votosPalestras: 0,
  metaRecomendada: 5,
  somAtivo: true
};

// ==========================================
// INICIALIZAÇÃO DE IDENTIFICADORES
// ==========================================
function inicializarSessao() {
  const urlParams = new URLSearchParams(window.location.search);
  
  // 1. Iniciativa ou Canal vindo da URL
  const iniUrl = urlParams.get('iniciativa') || urlParams.get('canal');
  if (iniUrl) {
    Estado.iniciativa = iniUrl.trim();
  } else {
    Estado.iniciativa = localStorage.getItem('mec_iniciativa') || 'Geral';
  }
  localStorage.setItem('mec_iniciativa', Estado.iniciativa);

  // 2. UID do Usuário
  let uidUrl = urlParams.get('uid');
  if (!uidUrl) {
    uidUrl = localStorage.getItem('mec_uid');
  }
  if (!uidUrl) {
    const sufixo = (window.crypto && crypto.randomUUID)
      ? crypto.randomUUID().split('-')[0]
      : Math.random().toString(36).substring(2, 10);
    uidUrl = 'u_' + sufixo;
  }
  Estado.uid = uidUrl;
  localStorage.setItem('mec_uid', uidUrl);

  // Atualiza campos ocultos do form
  const inputUid = document.getElementById('uid');
  if (inputUid) inputUid.value = Estado.uid;
  const inputIni = document.getElementById('iniciativa');
  if (inputIni) inputIni.value = Estado.iniciativa;

  // Atualiza a URL sem recarregar para garantir o link único
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('uid', Estado.uid);
    if (Estado.iniciativa && Estado.iniciativa !== 'Geral') {
      url.searchParams.set('iniciativa', Estado.iniciativa);
    }
    window.history.replaceState({}, '', url.toString());
  } catch (e) {}

  // 3. Pré-seleciona iniciativa se vier da URL
  if (Estado.iniciativa && Estado.iniciativa !== 'Geral') {
    const cardIni = document.getElementById('cardIniciativaOpcao');
    if (cardIni) {
      selecionarComoSoube(cardIni, 'Divulgação de alguma iniciativa');
      const selProj = document.getElementById('projeto_extensao');
      if (selProj) {
        const iniNorm = Estado.iniciativa.toLowerCase().replace(/[\s_\-]+/g, '');
        for (let opt of selProj.options) {
          const optNorm = opt.value.toLowerCase().replace(/[\s_\-]+/g, '');
          if (optNorm && (optNorm === iniNorm || optNorm.includes(iniNorm) || iniNorm.includes(optNorm))) {
            opt.selected = true;
            break;
          }
        }
      }
    }
  }

  // 4. Máscara de Telefone
  aplicarMascaraTelefone();

  // 5. Verifica se o usuário já preencheu o formulário anteriormente
  verificarCadastroExistente();
}

// Máscara dinâmica para Telefone (31) 99999-9999
function aplicarMascaraTelefone() {
  const telInput = document.getElementById('telefone');
  if (!telInput) return;

  telInput.addEventListener('input', function (e) {
    let x = e.target.value.replace(/\D/g, '').match(/(\d{0,2})(\d{0,5})(\d{0,4})/);
    if (!x[2]) {
      e.target.value = x[1] ? `(${x[1]}` : '';
    } else if (!x[3]) {
      e.target.value = `(${x[1]}) ${x[2]}`;
    } else {
      e.target.value = `(${x[1]}) ${x[2]}-${x[3]}`;
    }
  });
}

// ==========================================
// CONTROLE DE ETAPAS E NAVEGAÇÃO
// ==========================================
function setEtapa(numero) {
  Estado.etapaAtual = numero;

  // Atualiza Stepper visual
  for (let i = 1; i <= 4; i++) {
    const el = document.getElementById(`stepIndicator${i}`);
    if (el) {
      el.classList.remove('active', 'completed');
      if (i < numero) el.classList.add('completed');
      else if (i === numero) el.classList.add('active');
    }
  }

  // Esconde todas as seções
  document.getElementById('etapaFormulario').style.display = 'none';
  document.getElementById('etapaBrindes').style.display = 'none';
  document.getElementById('etapaPalestras').style.display = 'none';
  document.getElementById('etapaFinal').style.display = 'none';

  // Exibe a seção ativa e inicializa dados
  if (numero === 1) {
    document.getElementById('etapaFormulario').style.display = 'block';
  } else if (numero === 2) {
    document.getElementById('etapaBrindes').style.display = 'block';
    carregarProximoDueloBrinde();
  } else if (numero === 3) {
    document.getElementById('etapaPalestras').style.display = 'block';
    const badgeCurso = document.getElementById('cursoAlunoBadge');
    if (badgeCurso) badgeCurso.textContent = Estado.curso || 'Engenharia';
    carregarProximoDueloPalestra();
  } else if (numero === 4) {
    document.getElementById('etapaFinal').style.display = 'block';
    document.getElementById('finalResumoCurso').textContent = Estado.curso || 'Geral';
    document.getElementById('finalResumoIniciativa').textContent = Estado.iniciativa || 'Geral';
    document.getElementById('finalResumoVotos').textContent = Estado.votosBrindes + Estado.votosPalestras;
    const txtNome = document.getElementById('textoFinalNome');
    if (txtNome && Estado.nome) {
      txtNome.innerHTML = `Obrigado, <strong>${escaparHtml(Estado.nome)}</strong>! Sua inscrição e seus votos foram registrados com sucesso no sistema oficial da <strong>Mercado em Conexão</strong>.`;
    }
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==========================================
// ETAPA 1: CONTROLES E VALIDAÇÃO DA PESQUISA
// ==========================================

function selecionarComoSoube(cardEl, valor) {
  const stack = cardEl.parentElement;
  if (stack) {
    stack.querySelectorAll('.radio-card-option').forEach(el => el.classList.remove('selected'));
  }
  cardEl.classList.add('selected');
  const radio = cardEl.querySelector('input[type="radio"]');
  if (radio) radio.checked = true;

  const boxProj = document.getElementById('boxProjetoExtensao');
  if (boxProj) {
    if (valor === 'Divulgação de alguma iniciativa') {
      boxProj.style.display = 'block';
    } else {
      boxProj.style.display = 'none';
      const selProj = document.getElementById('projeto_extensao');
      if (selProj && !Estado.iniciativaAuto) selProj.value = '';
    }
  }

  const err = document.getElementById('comoSoubeError');
  if (err) err.style.display = 'none';
}

function selecionarRadioSimples(cardEl, groupName, valor) {
  const parent = cardEl.parentElement;
  if (parent) {
    parent.querySelectorAll('.radio-pill').forEach(el => el.classList.remove('selected'));
  }
  cardEl.classList.add('selected');
  const radio = cardEl.querySelector('input[type="radio"]');
  if (radio) radio.checked = true;

  if (groupName === 'periodo_palestras') {
    const err = document.getElementById('periodoError');
    if (err) err.style.display = 'none';
  } else if (groupName === 'horario_feira') {
    const err = document.getElementById('horarioError');
    if (err) err.style.display = 'none';
  }
}

function aoAlternarTemaCheckbox(cardEl) {
  const chk = cardEl.querySelector('input[type="checkbox"]');
  const selecionados = document.querySelectorAll('input[name="temas_painel"]:checked');

  // Limite máximo de 3 opções de temas
  if (chk && chk.checked && selecionados.length > 3) {
    chk.checked = false;
    cardEl.classList.remove('selected');
    mostrarToast('Você pode selecionar no máximo 3 temas de palestras.', '⚠️');
    return;
  }

  if (chk && chk.checked) {
    cardEl.classList.add('selected');
  } else {
    cardEl.classList.remove('selected');
  }

  const total = document.querySelectorAll('input[name="temas_painel"]:checked').length;
  const counter = document.getElementById('counterTemas');
  if (counter) {
    counter.textContent = `${total} / 3 selecionadas`;
    if (total === 3) {
      counter.className = 'badge badge-accent';
    } else {
      counter.className = 'badge badge-primary';
    }
  }

  const err = document.getElementById('temasError');
  if (err) err.style.display = 'none';
}

function aoAlternarTemaOutro(cardEl) {
  aoAlternarTemaCheckbox(cardEl);
  const chk = cardEl.querySelector('input[type="checkbox"]');
  const boxOutro = document.getElementById('boxTemaOutroInput');
  if (boxOutro) {
    if (chk && chk.checked) {
      boxOutro.style.display = 'block';
      const inputOutro = document.getElementById('tema_outro');
      if (inputOutro) inputOutro.focus();
    } else {
      boxOutro.style.display = 'none';
    }
  }
}

function atualizarCursoSelecionado() {
  const sel = document.getElementById('curso');
  if (sel) {
    Estado.curso = sel.value;
  }
}

async function enviarInscricao(e) {
  e.preventDefault();

  const nomeInput = document.getElementById('nome');
  const emailInput = document.getElementById('email');
  const telInput = document.getElementById('telefone');
  const cursoInput = document.getElementById('curso');

  const radioComoSoube = document.querySelector('input[name="como_soube_opcao"]:checked');
  const selProjetoExtensao = document.getElementById('projeto_extensao');
  const empresasInput = document.getElementById('empresas_desejadas');

  const chkTemas = Array.from(document.querySelectorAll('input[name="temas_painel"]:checked')).map(c => c.value);
  const temaOutroInput = document.getElementById('tema_outro');

  const radioPeriodo = document.querySelector('input[name="periodo_palestras"]:checked');
  const radioHorario = document.querySelector('input[name="horario_feira"]:checked');

  let valido = true;

  // 1. Validação de dados pessoais
  [nomeInput, emailInput, telInput, cursoInput, empresasInput].forEach(inp => {
    if (!inp || !inp.value.trim()) {
      if (inp) inp.classList.add('is-invalid');
      valido = false;
    } else {
      if (inp) inp.classList.remove('is-invalid');
    }
  });

  // E-mail válido
  if (emailInput && (!emailInput.value.includes('@') || !emailInput.value.includes('.'))) {
    emailInput.classList.add('is-invalid');
    valido = false;
  }

  // Telefone com DDD
  if (telInput && telInput.value.replace(/\D/g, '').length < 10) {
    telInput.classList.add('is-invalid');
    valido = false;
  }

  // 2. Validação de como ficou sabendo
  const errComoSoube = document.getElementById('comoSoubeError');
  if (!radioComoSoube) {
    if (errComoSoube) errComoSoube.style.display = 'block';
    valido = false;
  } else {
    if (errComoSoube) errComoSoube.style.display = 'none';

    // Se selecionou iniciativa, deve escolher o projeto de extensão
    if (radioComoSoube.value === 'Divulgação de alguma iniciativa') {
      const errProj = document.getElementById('projetoExtensaoError');
      if (!selProjetoExtensao || !selProjetoExtensao.value.trim()) {
        if (errProj) errProj.style.display = 'block';
        valido = false;
      } else {
        if (errProj) errProj.style.display = 'none';
      }
    }
  }

  // 3. Validação de temas (1 a 3 temas selecionados)
  const errTemas = document.getElementById('temasError');
  if (chkTemas.length === 0 || chkTemas.length > 3) {
    if (errTemas) errTemas.style.display = 'block';
    valido = false;
  } else {
    if (errTemas) errTemas.style.display = 'none';
  }

  // 4. Validação de períodos
  const errPeriodo = document.getElementById('periodoError');
  if (!radioPeriodo) {
    if (errPeriodo) errPeriodo.style.display = 'block';
    valido = false;
  } else {
    if (errPeriodo) errPeriodo.style.display = 'none';
  }

  // 5. Validação de horário da feira
  const errHorario = document.getElementById('horarioError');
  if (!radioHorario) {
    if (errHorario) errHorario.style.display = 'block';
    valido = false;
  } else {
    if (errHorario) errHorario.style.display = 'none';
  }

  if (!valido) {
    mostrarToast('Por favor, preencha os campos obrigatórios destacados.', '⚠️');
    return;
  }

  const btnSalvar = document.getElementById('btnSalvarInscricao');
  if (btnSalvar) {
    btnSalvar.disabled = true;
    btnSalvar.innerHTML = '<span>Salvando respostas...</span>';
  }

  const payload = {
    uid: Estado.uid,
    iniciativa: (radioComoSoube && radioComoSoube.value === 'Divulgação de alguma iniciativa' && selProjetoExtensao && selProjetoExtensao.value)
      ? selProjetoExtensao.value
      : (Estado.iniciativa || 'Geral'),
    nome: nomeInput.value.trim(),
    email: emailInput.value.trim(),
    telefone: telInput.value.trim(),
    universidade: 'UFMG - Universidade Federal de Minas Gerais',
    curso: cursoInput.value,
    como_soube_opcao: radioComoSoube ? radioComoSoube.value : '',
    projeto_extensao: (selProjetoExtensao && selProjetoExtensao.value) ? selProjetoExtensao.value : '',
    empresas_desejadas: empresasInput.value.trim(),
    temas_painel: chkTemas,
    tema_outro: (temaOutroInput && chkTemas.includes('Outro')) ? temaOutroInput.value.trim() : '',
    periodo_palestras: radioPeriodo ? radioPeriodo.value : '',
    horario_feira: radioHorario ? radioHorario.value : ''
  };

  try {
    const res = await fetch('/api/inscricao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok && data.status === 'ok') {
      Estado.nome = payload.nome;
      Estado.curso = payload.curso;
      Estado.iniciativa = payload.iniciativa;
      localStorage.setItem('mec_nome', Estado.nome);
      localStorage.setItem('mec_curso', Estado.curso);
      localStorage.setItem('mec_iniciativa', Estado.iniciativa);
      mostrarToast('Respostas registradas! Vamos para os brindes.', '🎉');

      // Avança para o Duelo de Brindes (Etapa 2)
      setEtapa(2);
    } else {
      mostrarToast(data.detail || 'Erro ao validar respostas.', '❌');
    }
  } catch (err) {
    console.error('Erro na requisição de inscrição:', err);
    mostrarToast('Erro ao conectar ao servidor. Tente novamente.', '❌');
  } finally {
    if (btnSalvar) {
      btnSalvar.disabled = false;
      btnSalvar.innerHTML = '<span>Enviar Respostas e Votar nos Brindes</span><span>✨</span>';
    }
  }
}

async function verificarCadastroExistente() {
  if (!Estado.uid) return;
  try {
    const res = await fetch(`/api/inscricao/${encodeURIComponent(Estado.uid)}`);
    const data = await res.json();
    if (data.status === 'ok' && data.encontrado && data.inscrito) {
      Estado.nome = data.inscrito.nome;
      Estado.curso = data.inscrito.curso;
      Estado.iniciativa = data.inscrito.iniciativa;
      localStorage.setItem('mec_nome', Estado.nome);
      localStorage.setItem('mec_curso', Estado.curso);
      // Já está cadastrado, direciona diretamente para os duelos de brindes
      setEtapa(2);
    }
  } catch (e) {
    // Continua na etapa 1 se falhar
  }
}

// ==========================================
// ETAPA 2: DUELO DE BRINDES
// "Tirar ID, descrição, Competitivo(b) e inserir espaço para imagens"
// ==========================================
async function carregarProximoDueloBrinde() {
  Estado.bloqueado = false;
  const container = document.getElementById('dueloBrindesContainer');
  if (container) container.style.opacity = '0.6';

  try {
    const url = `/api/proximo-par?uid=${encodeURIComponent(Estado.uid)}&canal=${encodeURIComponent(Estado.iniciativa)}&categoria=brinde`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.status === 'ok') {
      Estado.parAtualBrinde = data;
      renderizarCardsDuelo(data.itemA, data.itemB, 'dueloBrindesContainer', 'brinde');
    } else if (data.status === 'concluido') {
      mostrarAvisoConclusaoCategoria('dueloBrindesContainer', data.mensagem || 'Você já avaliou todos os pares disponíveis de brindes!');
      ativarBotaoAvancarPalestras();
    }
  } catch (err) {
    console.error('Erro ao buscar próximo duelo de brindes:', err);
  } finally {
    if (container) container.style.opacity = '1';
  }
}

// Renderiza Cards 100% Limpos: Apenas Foto + Nome + Botão
function renderizarCardsDuelo(itemA, itemB, containerId, categoria) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const btnTexto = categoria === 'brinde' ? 'Escolher este brinde ✨' : 'Escolher este tema ✨';
  const imgFallback = categoria === 'brinde'
    ? 'https://images.unsplash.com/photo-1513151233558-d860c5398176?w=800&auto=format&fit=crop&q=80'
    : 'https://images.unsplash.com/photo-1475721027785-f74eccf877e2?w=800&auto=format&fit=crop&q=80';

  container.innerHTML = `
    <!-- Card Esquerda (Opção A) -->
    <div class="duel-card" id="card-${itemA.id}" onclick="votarDuelo('${itemA.id}', '${categoria}')">
      <div class="card-kbd-badge">[1] ou [←]</div>
      <div class="card-photo-wrapper">
        <img src="${escaparHtml(itemA.imagem_url)}" alt="${escaparHtml(itemA.nome)}" class="card-photo" loading="lazy" onerror="this.onerror=null; this.src='${imgFallback}'">
      </div>
      <div class="card-content">
        <h3 class="card-title">${escaparHtml(itemA.nome)}</h3>
        <div class="card-action-btn">
          <span>${btnTexto}</span>
        </div>
      </div>
    </div>

    <!-- Indicador VS Central -->
    <div class="vs-badge">VS</div>

    <!-- Card Direita (Opção B) -->
    <div class="duel-card" id="card-${itemB.id}" onclick="votarDuelo('${itemB.id}', '${categoria}')">
      <div class="card-kbd-badge">[2] ou [→]</div>
      <div class="card-photo-wrapper">
        <img src="${escaparHtml(itemB.imagem_url)}" alt="${escaparHtml(itemB.nome)}" class="card-photo" loading="lazy" onerror="this.onerror=null; this.src='${imgFallback}'">
      </div>
      <div class="card-content">
        <h3 class="card-title">${escaparHtml(itemB.nome)}</h3>
        <div class="card-action-btn">
          <span>${btnTexto}</span>
        </div>
      </div>
    </div>
  `;
}

async function votarDuelo(vencedorId, categoria) {
  if (Estado.bloqueado) return;
  Estado.bloqueado = true;

  tocarSomVoto();

  const parAtual = categoria === 'brinde' ? Estado.parAtualBrinde : Estado.parAtualPalestra;
  if (!parAtual) return;

  // Feedback visual instantâneo
  const cardSelecionado = document.getElementById(`card-${vencedorId}`);
  if (cardSelecionado) cardSelecionado.classList.add('selected');

  try {
    const payload = {
      uid: Estado.uid,
      canal: Estado.iniciativa,
      categoria: categoria,
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
      if (categoria === 'brinde') {
        Estado.votosBrindes++;
        atualizarProgressoBrindes();
        setTimeout(carregarProximoDueloBrinde, 220);
      } else {
        Estado.votosPalestras++;
        atualizarProgressoPalestras();
        setTimeout(carregarProximoDueloPalestra, 220);
      }
    }
  } catch (err) {
    console.error('Erro ao registrar voto:', err);
    Estado.bloqueado = false;
  }
}

function atualizarProgressoBrindes() {
  const contador = document.getElementById('votosBrindesContador');
  if (contador) contador.textContent = Estado.votosBrindes;

  const pct = Math.min(100, Math.round((Estado.votosBrindes / Estado.metaRecomendada) * 100));
  const fill = document.getElementById('brindesProgressoFill');
  if (fill) fill.style.width = `${pct}%`;

  // Quando atingir a meta recomendada de 5 duelos, exibe o botão para avançar para palestras
  if (Estado.votosBrindes >= Estado.metaRecomendada) {
    ativarBotaoAvancarPalestras();
  }
}

function ativarBotaoAvancarPalestras() {
  const btn = document.getElementById('btnAvancarPalestras');
  if (btn) {
    btn.style.display = 'inline-flex';
    btn.classList.add('animate-pulse');
  }
}

function avancarParaPalestras() {
  setEtapa(3);
}

// ==========================================
// ETAPA 3: DUELO DE TEMAS DE PALESTRAS
// Filtradas de acordo com o Curso/Engenharia
// ==========================================
async function carregarProximoDueloPalestra() {
  Estado.bloqueado = false;
  const container = document.getElementById('dueloPalestrasContainer');
  if (container) container.style.opacity = '0.6';

  try {
    const cursoParam = encodeURIComponent(Estado.curso || 'todos');
    const url = `/api/proximo-par?uid=${encodeURIComponent(Estado.uid)}&canal=${encodeURIComponent(Estado.iniciativa)}&categoria=palestra&curso=${cursoParam}`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.status === 'ok') {
      Estado.parAtualPalestra = data;
      renderizarCardsDuelo(data.itemA, data.itemB, 'dueloPalestrasContainer', 'palestra');
    } else if (data.status === 'concluido') {
      mostrarAvisoConclusaoCategoria('dueloPalestrasContainer', data.mensagem || 'Você já avaliou todos os pares de temas para seu curso!');
      ativarBotaoConcluirParticipacao();
    }
  } catch (err) {
    console.error('Erro ao carregar próximo duelo de palestras:', err);
  } finally {
    if (container) container.style.opacity = '1';
  }
}

function atualizarProgressoPalestras() {
  const contador = document.getElementById('votosPalestrasContador');
  if (contador) contador.textContent = Estado.votosPalestras;

  const pct = Math.min(100, Math.round((Estado.votosPalestras / Estado.metaRecomendada) * 100));
  const fill = document.getElementById('palestrasProgressoFill');
  if (fill) fill.style.width = `${pct}%`;

  if (Estado.votosPalestras >= Estado.metaRecomendada) {
    ativarBotaoConcluirParticipacao();
  }
}

function ativarBotaoConcluirParticipacao() {
  const btn = document.getElementById('btnConcluirParticipacao');
  if (btn) {
    btn.style.display = 'inline-flex';
  }
}

function finalizarTudo() {
  setEtapa(4);
}

function continuarVotando() {
  setEtapa(2);
}

function pularDuelo(categoria) {
  if (categoria === 'brinde') {
    carregarProximoDueloBrinde();
  } else {
    carregarProximoDueloPalestra();
  }
}

function mostrarAvisoConclusaoCategoria(containerId, mensagem) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = `
    <div style="grid-column: 1 / -1; text-align: center; padding: 40px 20px; background: #ffffff; border-radius: 16px; border: 1px solid var(--slate-200);">
      <div style="font-size: 2.2rem; margin-bottom: 12px;">🌟</div>
      <h3 style="color: var(--primary); font-size: 1.3rem; margin-bottom: 8px;">Excelente participação!</h3>
      <p style="color: var(--slate-600); max-width: 500px; margin: 0 auto 20px auto;">${escaparHtml(mensagem)}</p>
    </div>
  `;
}

// ==========================================
// SOM SINTÉTICO (WEB AUDIO API)
// ==========================================
function tocarSomVoto() {
  if (!Estado.somAtivo) return;
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
  } catch (e) {}
}

window.atualizarEstadoSom = function(habilitado) {
  Estado.somAtivo = habilitado;
};

// ==========================================
// ATALHOS DE TECLADO ([1], [2], [Espaço])
// ==========================================
document.addEventListener('keydown', function (e) {
  // Ignora atalhos se o foco estiver dentro de inputs de texto do formulário
  if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
    return;
  }

  if (Estado.etapaAtual === 2 && Estado.parAtualBrinde && !Estado.bloqueado) {
    if (e.key === '1' || e.key === 'ArrowLeft') {
      votarDuelo(Estado.parAtualBrinde.itemA.id, 'brinde');
    } else if (e.key === '2' || e.key === 'ArrowRight') {
      votarDuelo(Estado.parAtualBrinde.itemB.id, 'brinde');
    } else if (e.key === ' ' || e.key === 'Spacebar') {
      e.preventDefault();
      pularDuelo('brinde');
    }
  } else if (Estado.etapaAtual === 3 && Estado.parAtualPalestra && !Estado.bloqueado) {
    if (e.key === '1' || e.key === 'ArrowLeft') {
      votarDuelo(Estado.parAtualPalestra.itemA.id, 'palestra');
    } else if (e.key === '2' || e.key === 'ArrowRight') {
      votarDuelo(Estado.parAtualPalestra.itemB.id, 'palestra');
    } else if (e.key === ' ' || e.key === 'Spacebar') {
      e.preventDefault();
      pularDuelo('palestra');
    }
  }
});

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
  }, 2800);
}

function escaparHtml(texto) {
  if (!texto) return '';
  return String(texto)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Inicializa a aplicação ao carregar o DOM ou imediatamente se já carregado
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', inicializarSessao);
} else {
  inicializarSessao();
}
