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
