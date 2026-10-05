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
});

// ─── Activity execution ───────────────────────────────────────────────────────
function initExecution(criancaPk, atividadePk, sessaoId, csrfToken) {
  let startTime = Date.now();
  let answered = false;

  const buttons = document.querySelectorAll('.exec-img-btn');
  const overlay = document.getElementById('feedback-overlay');
  const feedbackBox = document.getElementById('feedback-box');
  const nextBtn = document.getElementById('next-btn');

  buttons.forEach(btn => {
    btn.addEventListener('click', function () {
      if (answered) return;
      answered = true;

      const imagemId = this.dataset.imagemId;
      const tempo = ((Date.now() - startTime) / 1000).toFixed(2);

      // Visual selection
      this.classList.add('selected');

      // POST to server
      fetch(`/desempenho/crianca/${criancaPk}/atividade/${atividadePk}/resposta/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          imagem_id: imagemId,
          tempo_resposta: tempo,
          sessao_id: sessaoId || null,
        }),
      })
        .then(r => r.json())
        .then(data => {
          if (data.correto) {
            this.classList.add('correct');
            showFeedback(true);
          } else {
            this.classList.add('wrong');
            // Highlight correct answer
            buttons.forEach(b => {
              if (b.dataset.emocao === data.emocao_correta) b.classList.add('correct');
            });
            showFeedback(false);
          }
          if (nextBtn) nextBtn.style.display = 'inline-flex';
        })
        .catch(() => {
          if (nextBtn) nextBtn.style.display = 'inline-flex';
        });
    });
  });

  function showFeedback(correto) {
    if (!overlay || !feedbackBox) return;
    feedbackBox.innerHTML = correto
      ? '<span class="feedback-emoji">🎉</span>Muito bem! Você acertou!'
      : '<span class="feedback-emoji">😊</span>Quase lá! Vamos tentar de novo?';
    overlay.classList.add('show');
    setTimeout(() => overlay.classList.remove('show'), 2000);
  }
}

// ─── Cartões Correspondentes ──────────────────────────────────────────────────
function initCartoes(criancaPk, atividadePk, sessaoId, csrfToken) {
  const palavras = document.querySelectorAll('.cartao-palavra');
  const imagens = document.querySelectorAll('.cartao-imagem');
  const dica = document.getElementById('cartoes-dica');
  const barra = document.getElementById('cartoes-progresso');
  const nextBtn = document.getElementById('next-btn');
  const overlay = document.getElementById('feedback-overlay');
  const feedbackBox = document.getElementById('feedback-box');

  const total = palavras.length;
  let pareados = 0;
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
          if (data.correto) {
            palavra.classList.remove('selected');
            palavra.classList.add('matched');
            palavra.disabled = true;
            this.classList.add('correct');
            this.disabled = true;
            selecionada = null;
            pareados += 1;
            if (barra) barra.style.width = `${(pareados / total) * 100}%`;
            if (pareados === total) {
              setDica('Você encontrou todos os pares!');
              mostrarFeedback('🎉', 'Muito bem! Você encontrou todos os pares!');
              if (nextBtn) nextBtn.style.display = 'inline-flex';
            } else {
              setDica('Isso mesmo! Escolha outro cartão.');
            }
          } else {
            this.classList.add('wrong');
            setTimeout(() => this.classList.remove('wrong'), 600);
            startTime = Date.now();
            setDica('Quase lá! Tente outro rosto.');
          }
        })
        .catch(() => {
          setDica('Não foi possível registrar a resposta. Tente novamente.');
        })
        .finally(() => { aguardando = false; });
    });
  });

  function mostrarFeedback(emoji, texto) {
    if (!overlay || !feedbackBox) return;
    feedbackBox.innerHTML = `<span class="feedback-emoji">${emoji}</span>${texto}`;
    overlay.classList.add('show');
    setTimeout(() => overlay.classList.remove('show'), 2000);
  }
}

// ─── Organização de Emoções em Cenários ───────────────────────────────────────
function initCenarios(criancaPk, atividadePk, sessaoId, csrfToken) {
  const rotulos = document.querySelectorAll('.cenario-rotulo');
  const cenarios = document.querySelectorAll('.cenario-card');
  const dica = document.getElementById('cenarios-dica');
  const barra = document.getElementById('cenarios-progresso');
  const indice = document.getElementById('cenarios-indice');
  const proximaBtn = document.getElementById('proxima-cena');
  const nextBtn = document.getElementById('next-btn');
  const overlay = document.getElementById('feedback-overlay');
  const feedbackBox = document.getElementById('feedback-box');

  const total = cenarios.length;
  let resolvidos = 0;
  let atual = 0;  // uma cena por vez
  let selecionado = null;
  let aguardando = false;
  let startTime = Date.now();

  function setDica(texto) {
    if (dica) dica.textContent = texto;
  }

  function cenaResolvida() {
    return cenarios[atual].classList.contains('correct');
  }

  if (proximaBtn) {
    proximaBtn.addEventListener('click', function () {
      cenarios[atual].hidden = true;
      atual += 1;
      cenarios[atual].hidden = false;
      if (indice) indice.textContent = atual + 1;
      this.style.display = 'none';
      startTime = Date.now();
      setDica('Arraste a emoção até a cena.');
    });
  }

  function cenarioEm(x, y) {
    const el = document.elementFromPoint(x, y);
    const card = el && el.closest('.cenario-card');
    return card && !card.classList.contains('correct') ? card : null;
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
        rotulos.forEach(r => r.classList.remove('selected'));
        selecionado = null;
        startTime = Date.now();
        if (data.correto) {
          card.classList.add('correct');
          card.querySelector('.cenario-alvo').textContent = rotulo.textContent.trim();
          resolvidos += 1;
          if (barra) barra.style.width = `${(resolvidos / total) * 100}%`;
          if (resolvidos === total) {
            setDica('Você organizou todas as emoções!');
            mostrarFeedback('🎉', 'Muito bem! Você organizou todas as emoções!');
            if (nextBtn) nextBtn.style.display = 'inline-flex';
          } else {
            setDica('Isso mesmo! Vamos para a próxima cena.');
            if (proximaBtn) {
              proximaBtn.style.display = 'inline-flex';
              proximaBtn.focus();
            }
          }
        } else {
          card.classList.add('wrong');
          setTimeout(() => card.classList.remove('wrong'), 600);
          setDica('Quase lá! Observe a cena e tente outra emoção.');
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
      if (card.classList.contains('correct')) return;
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

  function mostrarFeedback(emoji, texto) {
    if (!overlay || !feedbackBox) return;
    feedbackBox.innerHTML = `<span class="feedback-emoji">${emoji}</span>${texto}`;
    overlay.classList.add('show');
    setTimeout(() => overlay.classList.remove('show'), 2000);
  }
}
