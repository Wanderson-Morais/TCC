// ─── Sidebar toggle (mobile) ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && e.target !== toggle) {
        sidebar.classList.remove('open');
      }
    });
  }

  // Auto-dismiss alerts
  document.querySelectorAll('.alert[data-autohide]').forEach(el => {
    setTimeout(() => el.style.opacity = '0', 3500);
    setTimeout(() => el.remove(), 4000);
  });

  initRelatorios();
  initTerminar();
});

// ─── Relatórios ───────────────────────────────────────────────────────────────
function initRelatorios() {
  // Guia "Como usar": some depois do "Entendi" e não volta mais neste navegador
  document.querySelectorAll('[data-fechar-guia]').forEach(btn => {
    const guia = btn.closest('.guia');
    const chave = `emotea-guia-${guia.id}`;
    try {
      if (localStorage.getItem(chave)) guia.hidden = true;
    } catch (e) { /* armazenamento indisponível: o guia só continua visível */ }
    btn.addEventListener('click', () => {
      guia.hidden = true;
      try { localStorage.setItem(chave, '1'); } catch (e) { /* idem */ }
    });
  });

  // Abas: trocam sem recarregar; o ?aba= vai junto ao trocar o período
  const abas = document.querySelector('[data-abas]');
  if (abas) {
    const links = abas.querySelectorAll('[data-aba]');
    links.forEach(link => {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        links.forEach(l => {
          const ativa = l === this;
          l.classList.toggle('on', ativa);
          l.setAttribute('aria-selected', ativa ? 'true' : 'false');
          document.getElementById(l.getAttribute('aria-controls')).hidden = !ativa;
        });
        history.replaceState(null, '', this.href);
        document.querySelectorAll('[data-aba-link]').forEach(a => {
          const url = new URL(a.href);
          url.searchParams.set('aba', this.dataset.aba);
          a.href = url;
        });
      });
    });
  }
}

// ─── Efeito sonoro de acerto ──────────────────────────────────────────────────
// Sintetizado com Web Audio (sem arquivo de áudio). Volume baixo e notas suaves,
// pensando na sensibilidade sensorial das crianças.
let audioCtx = null;

// O navegador só libera o áudio após um gesto do usuário; a resposta chega
// depois do fetch, então o contexto é criado/retomado já no toque.
function liberarAudio() {
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!Ctx) return;
  if (!audioCtx) audioCtx = new Ctx();
  if (audioCtx.state === 'suspended') audioCtx.resume();
}
document.addEventListener('pointerdown', liberarAudio, { capture: true });
document.addEventListener('keydown', liberarAudio, { capture: true });

function tocarNota(freq, inicio, duracao) {
  const osc = audioCtx.createOscillator();
  const ganho = audioCtx.createGain();
  osc.type = 'sine';
  osc.frequency.value = freq;
  ganho.gain.setValueAtTime(0, inicio);
  ganho.gain.linearRampToValueAtTime(0.18, inicio + 0.02);
  ganho.gain.exponentialRampToValueAtTime(0.001, inicio + duracao);
  osc.connect(ganho).connect(audioCtx.destination);
  osc.start(inicio);
  osc.stop(inicio + duracao);
}

// completo=false: "plim" curto de acerto; completo=true: melodia de conclusão
function tocarSomAcerto(completo) {
  if (!audioCtx) return;
  const t = audioCtx.currentTime;
  const notas = completo
    ? [523.25, 659.25, 783.99, 1046.5]  // Dó, Mi, Sol, Dó
    : [659.25, 987.77];                 // Mi, Si
  notas.forEach((freq, i) => tocarNota(freq, t + i * 0.11, completo ? 0.45 : 0.3));
}

// ─── Activity execution ───────────────────────────────────────────────────────
function initExecution(criancaPk, atividadePk, sessaoId, csrfToken) {
  const startTime = Date.now();
  let answered = false;

  const buttons = document.querySelectorAll('.exec-grade .exec-img-btn');
  const grade = document.getElementById('exec-grade');
  const instrucao = document.getElementById('exec-instrucao');

  buttons.forEach(btn => {
    btn.addEventListener('click', function () {
      if (answered) return;
      answered = true;

      const tempo = ((Date.now() - startTime) / 1000).toFixed(2);
      this.classList.add('selected');

      fetch(`/desempenho/crianca/${criancaPk}/atividade/${atividadePk}/resposta/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          imagem_id: this.dataset.imagemId,
          tempo_resposta: tempo,
          sessao_id: sessaoId || null,
        }),
      })
        .then(r => {
          if (!r.ok) throw new Error('Falha ao registrar');
          return r.json();
        })
        .then(data => {
          this.classList.remove('selected');
          if (data.correto) {
            this.classList.add('correct');
            tocarSomAcerto(true);
          } else {
            this.classList.add('wrong');
            // Mostra qual era o rosto certo
            buttons.forEach(b => {
              if (b.dataset.emocao === data.emocao_correta) b.classList.add('correct');
            });
          }
          buttons.forEach(b => { b.disabled = true; });
          grade.classList.add('respondido');
          if (instrucao) instrucao.hidden = true;
          const retorno = document.getElementById(data.correto ? 'retorno-acerto' : 'retorno-erro');
          retorno.hidden = false;
          const seguir = retorno.querySelector('.btn');
          if (seguir) seguir.focus();
        })
        .catch(() => {
          // Deixa a criança tentar de novo se a resposta não foi salva
          answered = false;
          this.classList.remove('selected');
          if (instrucao) instrucao.textContent = 'Não foi possível registrar a resposta. Toque de novo.';
        });
    });
  });
}

// Fim de uma atividade de várias etapas: mostra "Muito bem!" com o botão de seguir
function mostrarConcluido(dica, erro) {
  if (dica) dica.hidden = true;
  const retorno = document.getElementById('retorno-acerto');
  if (!retorno) return;
  if (erro) {
    retorno.classList.replace('acerto', 'erro');
    document.getElementById('retorno-emoji').textContent = '😊';
    document.getElementById('retorno-titulo').textContent = erro.titulo;
    document.getElementById('retorno-mensagem').textContent = erro.mensagem;
  }
  retorno.hidden = false;
  const seguir = retorno.querySelector('.btn');
  if (seguir) seguir.focus();
}

// Última atividade da sessão: "Terminar" mostra a tela de parabéns
function initTerminar() {
  document.querySelectorAll('[data-terminar]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('exec-atividade').hidden = true;
      document.getElementById('exec-fim').hidden = false;
    });
  });
}

// ─── Cartões Correspondentes ──────────────────────────────────────────────────
function initCartoes(criancaPk, atividadePk, sessaoId, csrfToken) {
  const palavras = document.querySelectorAll('.cartao-palavra');
  const imagens = document.querySelectorAll('.cartao-imagem');
  const dica = document.getElementById('cartoes-dica');
  const barra = document.getElementById('cartoes-progresso');
  const contador = document.getElementById('cartoes-contador');

  const total = palavras.length;
  let respondidos = 0;  // pares feitos, certos ou errados
  let acertos = 0;
  let selecionada = null;
  let startTime = null;
  let aguardando = false;

  function setDica(texto) {
    if (dica) dica.textContent = texto;
  }

  palavras.forEach(btn => {
    btn.addEventListener('click', function () {
      if (aguardando || this.disabled) return;
      palavras.forEach(p => p.classList.remove('selected'));
      this.classList.add('selected');
      selecionada = this;
      startTime = Date.now();
      setDica(`Agora encontre o rosto: ${this.textContent.trim()}`);
    });
  });

  imagens.forEach(btn => {
    btn.addEventListener('click', function () {
      if (aguardando || this.disabled) return;
      if (!selecionada) {
        setDica('Primeiro escolha um cartão com o nome de uma emoção.');
        return;
      }
      aguardando = true;
      const palavra = selecionada;
      const tempo = ((Date.now() - startTime) / 1000).toFixed(2);

      fetch(`/desempenho/crianca/${criancaPk}/cartoes/${atividadePk}/resposta/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          cartao_id: palavra.dataset.cartaoId,
          imagem_id: this.dataset.cartaoId,
          tempo_resposta: tempo,
          sessao_id: sessaoId || null,
        }),
      })
        .then(r => {
          if (!r.ok) throw new Error('Falha ao registrar');
          return r.json();
        })
        .then(data => {
          palavra.classList.remove('selected');
          palavra.disabled = true;
          selecionada = null;
          respondidos += 1;
          // O rosto certo da palavra é o cartão com o mesmo id
          const certo = [...imagens].find(i => i.dataset.cartaoId === palavra.dataset.cartaoId);
          if (certo) {
            certo.classList.add('correct');
            certo.disabled = true;
          }

          if (data.correto) {
            acertos += 1;
            palavra.classList.add('matched');
            tocarSomAcerto(respondidos === total && acertos === total);
            setDica('Isso mesmo! Escolha outro cartão.');
          } else {
            // Erro fica marcado: a palavra não pode ser tentada de novo
            palavra.classList.add('errado');
            this.classList.add('wrong');
            setTimeout(() => this.classList.remove('wrong'), 1200);
            setDica('Esse não era o rosto. O certo está com borda verde ✔. Escolha outro cartão.');
          }

          if (barra) barra.style.width = `${(respondidos / total) * 100}%`;
          if (contador) contador.textContent = respondidos;
          if (respondidos === total) {
            mostrarConcluido(dica, acertos < total && {
              titulo: 'Fim da atividade!',
              mensagem: `Você acertou ${acertos} de ${total} pares.`,
            });
          }
        })
        .catch(() => {
          setDica('Não foi possível registrar a resposta. Tente novamente.');
        })
        .finally(() => { aguardando = false; });
    });
  });
}

// ─── Organização de Emoções em Cenários ───────────────────────────────────────
function initCenarios(criancaPk, atividadePk, sessaoId, csrfToken) {
  const rotulos = document.querySelectorAll('.cenario-rotulo');
  const cenarios = document.querySelectorAll('.cenario-card');
  const dica = document.getElementById('cenarios-dica');

  // Uma cena por tela: cada cena conta como uma atividade da sessão,
  // com uma única tentativa (certa ou errada)
  let respondido = false;
  let selecionado = null;
  let aguardando = false;
  let startTime = Date.now();

  function setDica(texto) {
    if (dica) dica.textContent = texto;
  }

  function cenaResolvida() {
    return respondido;
  }

  function cenarioEm(x, y) {
    const el = document.elementFromPoint(x, y);
    const card = el && el.closest('.cenario-card');
    return card && !respondido ? card : null;
  }

  function limparOver() {
    cenarios.forEach(c => c.classList.remove('over'));
  }

  function responder(rotulo, card) {
    if (aguardando) return;
    aguardando = true;
    const tempo = ((Date.now() - startTime) / 1000).toFixed(2);

    fetch(`/desempenho/crianca/${criancaPk}/cenarios/${atividadePk}/resposta/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({
        cenario_id: card.dataset.cenarioId,
        emocao: rotulo.dataset.emocao,
        tempo_resposta: tempo,
        sessao_id: sessaoId || null,
      }),
    })
      .then(r => {
        if (!r.ok) throw new Error('Falha ao registrar');
        return r.json();
      })
      .then(data => {
        respondido = true;
        rotulos.forEach(r => {
          r.classList.remove('selected');
          r.disabled = true;
        });
        selecionado = null;
        card.querySelector('.cenario-alvo').textContent = rotulo.textContent.trim();
        if (data.correto) {
          card.classList.add('correct');
          rotulo.classList.add('certo');
          tocarSomAcerto(true);
          mostrarConcluido(dica);
        } else {
          // Erro fica marcado: a emoção escolhida em vermelho e a certa em verde
          card.classList.add('wrong');
          rotulo.classList.add('errado');
          const certa = [...rotulos].find(r => r.dataset.emocao === data.emocao_correta);
          if (certa) certa.classList.add('certo');
          mostrarConcluido(dica, {
            titulo: 'Quase lá!',
            mensagem: `A emoção certa era: ${certa ? certa.textContent.trim() : data.emocao_correta}.`,
          });
        }
      })
      .catch(() => {
        setDica('Não foi possível registrar a resposta. Tente novamente.');
      })
      .finally(() => { aguardando = false; });
  }

  rotulos.forEach(rotulo => {
    let origem = null;
    let arrastando = false;
    let ignorarClique = false;

    rotulo.addEventListener('pointerdown', function (e) {
      if (aguardando || cenaResolvida() || e.button > 0) return;
      origem = { x: e.clientX, y: e.clientY };
      arrastando = false;
      this.setPointerCapture(e.pointerId);
    });

    rotulo.addEventListener('pointermove', function (e) {
      if (!origem) return;
      const dx = e.clientX - origem.x;
      const dy = e.clientY - origem.y;
      if (!arrastando && Math.hypot(dx, dy) < 8) return;
      arrastando = true;
      this.classList.add('dragging');
      this.style.transform = `translate(${dx}px, ${dy}px)`;
      limparOver();
      const card = cenarioEm(e.clientX, e.clientY);
      if (card) card.classList.add('over');
    });

    function soltar(e, cancelado) {
      if (!origem) return;
      origem = null;
      rotulo.classList.remove('dragging');
      rotulo.style.transform = '';
      limparOver();
      if (!arrastando) return;
      arrastando = false;
      ignorarClique = true;
      setTimeout(() => { ignorarClique = false; }, 0);
      const card = cancelado ? null : cenarioEm(e.clientX, e.clientY);
      if (card) responder(rotulo, card);
    }
    rotulo.addEventListener('pointerup', e => soltar(e, false));
    rotulo.addEventListener('pointercancel', e => soltar(e, true));

    // Alternativa ao arrastar: tocar no rótulo e depois na cena (também via teclado)
    rotulo.addEventListener('click', function () {
      if (ignorarClique || aguardando || cenaResolvida()) return;
      const jaSelecionado = selecionado === this;
      rotulos.forEach(r => r.classList.remove('selected'));
      selecionado = jaSelecionado ? null : this;
      if (selecionado) {
        this.classList.add('selected');
        setDica(`Agora toque na cena se ela combina com: ${this.textContent.trim()}`);
      }
    });
  });

  cenarios.forEach(card => {
    function escolher() {
      if (respondido) return;
      if (!selecionado) {
        setDica('Arraste uma emoção até a cena, ou toque primeiro em uma emoção.');
        return;
      }
      responder(selecionado, card);
    }
    card.addEventListener('click', escolher);
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        escolher();
      }
    });
  });
}

// ─── Formulário de atividade de imagens ───────────────────────────────────────
function initFormAtividade(prefixo) {
  const form = document.getElementById('form-atividade');
  const lista = document.getElementById('imagens');
  const addBtn = document.getElementById('adicionar-imagem');
  const modelo = document.getElementById('modelo-imagem');
  const total = form.querySelector(`[name="${prefixo}-TOTAL_FORMS"]`);
  const max = parseInt(lista.dataset.max, 10);
  const titulo = document.getElementById('id_titulo');
  const pergunta = document.getElementById('id_pergunta');
  const radios = form.querySelectorAll('input[name="emocao_correta"]');

  const marcada = () => form.querySelector('input[name="emocao_correta"]:checked');
  const slotsVisiveis = () => [...lista.querySelectorAll('[data-slot]')].filter(s => !s.hidden);
  const temImagem = slot => !slot.querySelector('[data-previa]').hidden;

  // A pergunta acompanha a emoção enquanto a pessoa não escrever outra
  let sugerida = marcada() && pergunta.value === marcada().dataset.pergunta ? pergunta.value : null;
  radios.forEach(radio => {
    radio.addEventListener('change', () => {
      radios.forEach(r => r.closest('.emo-btn').classList.toggle('on', r.checked));
      if (!pergunta.value.trim() || pergunta.value === sugerida) pergunta.value = radio.dataset.pergunta;
      sugerida = radio.dataset.pergunta;
      atualizar();
    });
  });

  function prepararSlot(slot) {
    const arquivo = slot.querySelector('[data-arquivo]');
    arquivo.addEventListener('change', () => {
      const escolhido = arquivo.files[0];
      if (!escolhido) return;
      const previa = slot.querySelector('[data-previa]');
      previa.src = URL.createObjectURL(escolhido);
      previa.hidden = false;
      slot.querySelector('[data-vazio]').hidden = true;
      slot.querySelector('[data-trocar]').hidden = false;
      atualizar();
    });
    slot.querySelector('[data-emocao]').addEventListener('change', atualizar);
    slot.querySelector('[data-remover]').addEventListener('click', () => {
      slot.querySelector('input[name$="-DELETE"]').checked = true;
      slot.hidden = true;
      atualizar();
    });
    slot.querySelectorAll('[data-mover]').forEach(btn => {
      btn.addEventListener('click', () => {
        const visiveis = slotsVisiveis();
        const i = visiveis.indexOf(slot);
        const j = i + parseInt(btn.dataset.mover, 10);
        if (j < 0 || j >= visiveis.length) return;
        if (j > i) visiveis[j].after(slot); else visiveis[j].before(slot);
        atualizar();
      });
    });
  }

  lista.querySelectorAll('[data-slot]').forEach(prepararSlot);

  addBtn.addEventListener('click', () => {
    const n = parseInt(total.value, 10);
    addBtn.insertAdjacentHTML('beforebegin', modelo.innerHTML.replace(/__prefix__/g, n));
    total.value = n + 1;
    prepararSlot(addBtn.previousElementSibling);
    atualizar();
  });

  titulo.addEventListener('input', atualizar);
  pergunta.addEventListener('input', atualizar);

  function atualizar() {
    const certa = marcada() ? marcada().value : '';
    const visiveis = slotsVisiveis();
    const grade = document.getElementById('previa-grade');
    grade.replaceChildren();
    let completas = 0;
    let temCerta = false;

    visiveis.forEach((slot, i) => {
      slot.querySelector('[data-numero]').textContent = i + 1;
      slot.querySelector('[data-ordem]').value = i;
      slot.querySelector('[data-mover="-1"]').disabled = i === 0;
      slot.querySelector('[data-mover="1"]').disabled = i === visiveis.length - 1;

      const emocao = slot.querySelector('[data-emocao]').value;
      const completa = temImagem(slot) && emocao;
      const eCerta = Boolean(completa && emocao === certa);
      slot.classList.toggle('certa', eCerta);
      slot.querySelector('[data-selo]').hidden = !eCerta;
      if (completa) completas += 1;
      if (eCerta) temCerta = true;

      if (temImagem(slot)) {
        const cel = document.createElement('div');
        cel.className = eCerta ? 'previa-foto certa' : 'previa-foto';
        const img = document.createElement('img');
        img.src = slot.querySelector('[data-previa]').src;
        img.alt = '';
        cel.append(img);
        grade.append(cel);
      }
    });

    document.getElementById('previa-vazia').hidden = grade.children.length > 0;
    document.getElementById('previa-pergunta').textContent = pergunta.value.trim() || 'A pergunta aparece aqui.';
    addBtn.hidden = visiveis.length >= max;

    const itens = {
      titulo: titulo.value.trim() !== '',
      emocao: Boolean(certa),
      imagens: completas >= 2,
      certa: temCerta,
    };
    Object.entries(itens).forEach(([chave, ok]) => {
      document.querySelector(`#checklist [data-item="${chave}"]`).classList.toggle('feito', ok);
    });
    const pronto = Object.values(itens).every(Boolean);
    document.getElementById('salvar-atividade').disabled = !pronto;
    document.getElementById('salvar-dica').hidden = pronto;
  }

  atualizar();
}

// ─── Formulário de atividade de cartões ───────────────────────────────────────
function initFormCartoes() {
  const titulo = document.getElementById('id_titulo');
  const escolhas = document.querySelectorAll('[data-escolher]');
  const parDe = valor => document.querySelector(`[data-par="${valor}"]`);
  const temFoto = par => !par.querySelector('[data-previa]').hidden;

  escolhas.forEach(caixa => {
    caixa.addEventListener('change', () => {
      const par = parDe(caixa.dataset.escolher);
      caixa.closest('.emo-btn').classList.toggle('on', caixa.checked);
      par.hidden = !caixa.checked;
      // Par desmarcado é removido ao salvar (ou ignorado, se ainda não existia)
      par.querySelector('[data-remover-campo]').checked = !caixa.checked;
      atualizar();
    });
  });

  document.querySelectorAll('[data-par]').forEach(par => {
    const arquivo = par.querySelector('[data-arquivo]');
    arquivo.addEventListener('change', () => {
      const escolhido = arquivo.files[0];
      if (!escolhido) return;
      const previa = par.querySelector('[data-previa]');
      previa.src = URL.createObjectURL(escolhido);
      previa.hidden = false;
      par.querySelector('[data-vazio]').hidden = true;
      par.querySelector('[data-trocar]').hidden = false;
      atualizar();
    });
    par.querySelector('[data-palavra]').addEventListener('input', atualizar);
    par.querySelector('[data-remover-par]').addEventListener('click', () => {
      const caixa = document.querySelector(`[data-escolher="${par.dataset.par}"]`);
      caixa.checked = false;
      caixa.dispatchEvent(new Event('change'));
    });
  });

  titulo.addEventListener('input', atualizar);

  function atualizar() {
    const escolhidos = [...document.querySelectorAll('[data-par]')].filter(p => !p.hidden);
    const palavras = document.getElementById('previa-palavras');
    const grade = document.getElementById('previa-grade');
    palavras.replaceChildren();
    grade.replaceChildren();

    escolhidos.forEach(par => {
      const foto = temFoto(par);
      const palavra = par.querySelector('[data-palavra]').value.trim();
      par.classList.toggle('pronto', foto && palavra !== '');
      par.querySelector('[data-pronto]').hidden = !(foto && palavra !== '');
      par.querySelector('[data-falta]').hidden = foto;

      const cartao = document.createElement('span');
      cartao.className = 'previa-palavra';
      cartao.textContent = palavra || '…';
      palavras.append(cartao);
      if (foto) {
        const cel = document.createElement('div');
        cel.className = 'previa-foto';
        const img = document.createElement('img');
        img.src = par.querySelector('[data-previa]').src;
        img.alt = '';
        cel.append(img);
        grade.append(cel);
      }
    });

    const qtd = escolhidos.length;
    document.getElementById('qtd-pares').textContent = qtd;
    document.getElementById('qtd-pares-txt').textContent = qtd === 1 ? 'par' : 'pares';
    document.getElementById('sem-pares').hidden = qtd > 0;
    document.getElementById('previa-vazia').hidden = qtd > 0;

    const itens = {
      titulo: titulo.value.trim() !== '',
      pares: qtd >= 2,
      fotos: qtd > 0 && escolhidos.every(temFoto),
      palavras: qtd > 0 && escolhidos.every(p => p.querySelector('[data-palavra]').value.trim() !== ''),
    };
    Object.entries(itens).forEach(([chave, ok]) => {
      document.querySelector(`#checklist [data-item="${chave}"]`).classList.toggle('feito', ok);
    });
    const pronto = Object.values(itens).every(Boolean);
    document.getElementById('salvar-atividade').disabled = !pronto;
    document.getElementById('salvar-dica').hidden = pronto;
  }

  atualizar();
}

// ─── Formulário de atividade de cenários ──────────────────────────────────────
function initFormCenarios(prefixo) {
  const form = document.getElementById('form-cenarios');
  const lista = document.getElementById('cenas');
  const addBtn = document.getElementById('adicionar-cena');
  const modelo = document.getElementById('modelo-cena');
  const total = form.querySelector(`[name="${prefixo}-TOTAL_FORMS"]`);
  const max = parseInt(lista.dataset.max, 10);
  const titulo = document.getElementById('id_titulo');
  let verIdx = 0;  // cena mostrada na prévia

  const cenasVisiveis = () => [...lista.querySelectorAll('[data-cena]')].filter(c => !c.hidden);
  const temFoto = cena => !cena.querySelector('[data-previa]').hidden;
  const emocaoDe = cena => cena.querySelector('[data-emocao-cena]:checked');
  const descricaoDe = cena => cena.querySelector('[data-descricao]').value.trim();

  function prepararCena(cena) {
    const arquivo = cena.querySelector('[data-arquivo]');
    arquivo.addEventListener('change', () => {
      const escolhido = arquivo.files[0];
      if (!escolhido) return;
      const previa = cena.querySelector('[data-previa]');
      previa.src = URL.createObjectURL(escolhido);
      previa.hidden = false;
      cena.querySelector('[data-vazio]').hidden = true;
      cena.querySelector('[data-trocar]').hidden = false;
      verCena(cena);
    });
    cena.querySelector('[data-descricao]').addEventListener('input', () => verCena(cena));
    cena.querySelectorAll('[data-emocao-cena]').forEach(radio => {
      radio.addEventListener('change', () => {
        cena.querySelectorAll('[data-emocao-cena]').forEach(r => r.closest('.chip').classList.toggle('on', r.checked));
        verCena(cena);
      });
    });
    cena.querySelector('[data-ver]').addEventListener('click', () => verCena(cena));
    cena.querySelector('[data-remover]').addEventListener('click', () => {
      cena.querySelector('input[name$="-DELETE"]').checked = true;
      cena.hidden = true;
      verIdx = 0;
      atualizar();
    });
    cena.querySelectorAll('[data-mover]').forEach(btn => {
      btn.addEventListener('click', () => {
        const visiveis = cenasVisiveis();
        const i = visiveis.indexOf(cena);
        const j = i + parseInt(btn.dataset.mover, 10);
        if (j < 0 || j >= visiveis.length) return;
        if (j > i) visiveis[j].after(cena); else visiveis[j].before(cena);
        verCena(cena);
      });
    });
  }

  function verCena(cena) {
    verIdx = Math.max(cenasVisiveis().indexOf(cena), 0);
    atualizar();
  }

  lista.querySelectorAll('[data-cena]').forEach(prepararCena);

  addBtn.addEventListener('click', () => {
    const n = parseInt(total.value, 10);
    addBtn.insertAdjacentHTML('beforebegin', modelo.innerHTML.replace(/__prefix__/g, n));
    total.value = n + 1;
    const nova = addBtn.previousElementSibling;
    prepararCena(nova);
    verCena(nova);
  });

  document.getElementById('previa-anterior').addEventListener('click', () => { verIdx -= 1; atualizar(); });
  document.getElementById('previa-proxima').addEventListener('click', () => { verIdx += 1; atualizar(); });
  titulo.addEventListener('input', atualizar);

  function atualizar() {
    const visiveis = cenasVisiveis();
    const usadas = new Map();  // valor → nome, na ordem dos botões
    let prontas = 0;

    visiveis.forEach((cena, i) => {
      cena.querySelector('[data-numero]').textContent = i + 1;
      cena.querySelector('[data-ordem]').value = i;
      cena.querySelector('[data-mover="-1"]').disabled = i === 0;
      cena.querySelector('[data-mover="1"]').disabled = i === visiveis.length - 1;

      const emocao = emocaoDe(cena);
      if (emocao) usadas.set(emocao.value, emocao.dataset.nome);
      const faltas = [];
      if (!temFoto(cena)) faltas.push('foto');
      if (!descricaoDe(cena)) faltas.push('descrição');
      if (!emocao) faltas.push('emoção');
      const pronta = faltas.length === 0;
      if (pronta) prontas += 1;
      cena.classList.toggle('pronta', pronta);
      cena.querySelector('[data-pronta]').hidden = !pronta;
      const falta = cena.querySelector('[data-falta]');
      falta.hidden = pronta;
      falta.textContent = `Falta: ${faltas.join(', ')}`;
    });

    // Prévia da cena escolhida
    verIdx = Math.min(Math.max(verIdx, 0), Math.max(visiveis.length - 1, 0));
    const atual = visiveis[verIdx];
    const foto = document.getElementById('previa-foto');
    const comFoto = Boolean(atual && temFoto(atual));
    foto.hidden = !comFoto;
    if (comFoto) foto.src = atual.querySelector('[data-previa]').src;
    document.getElementById('previa-sem-foto').hidden = comFoto;
    document.getElementById('previa-desc').textContent =
      (atual && descricaoDe(atual)) || 'A descrição da cena aparece aqui.';
    document.getElementById('previa-contador').textContent =
      visiveis.length ? `Cena ${verIdx + 1} de ${visiveis.length}` : 'Nenhuma cena ainda';
    document.getElementById('previa-anterior').disabled = verIdx <= 0;
    document.getElementById('previa-proxima').disabled = verIdx >= visiveis.length - 1;

    const rotulos = document.getElementById('previa-rotulos');
    rotulos.replaceChildren();
    const ordem = [...visiveis[0]?.querySelectorAll('[data-emocao-cena]') || []].map(r => r.value);
    [...usadas.keys()].sort((a, b) => ordem.indexOf(a) - ordem.indexOf(b)).forEach(valor => {
      const rotulo = document.createElement('span');
      rotulo.className = 'previa-palavra previa-rotulo';
      rotulo.textContent = usadas.get(valor);
      rotulos.append(rotulo);
    });

    addBtn.hidden = visiveis.length >= max;

    const itens = {
      titulo: titulo.value.trim() !== '',
      prontas: prontas >= 2,
      emocoes: usadas.size >= 2,
      completas: visiveis.length > 0 && prontas === visiveis.length,
    };
    Object.entries(itens).forEach(([chave, ok]) => {
      document.querySelector(`#checklist [data-item="${chave}"]`).classList.toggle('feito', ok);
    });
    const pronto = Object.values(itens).every(Boolean);
    document.getElementById('salvar-atividade').disabled = !pronto;
    document.getElementById('salvar-dica').hidden = pronto;
  }

  atualizar();
}
