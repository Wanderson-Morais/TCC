# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

WAN (branded "EmoTEA" in templates) is a Django 5.2 web platform, built as a TCC (undergraduate thesis), that helps psychologists teach emotion recognition to children with autism (TEA). A child is shown facial-expression images and a question such as "Quem está feliz?"; the system records hit/miss and response time.

All domain code, identifiers, URLs, and UI text are in Brazilian Portuguese (`crianca`, `sessao`, `desempenho`, `psicologo`, `responsavel`). Keep new code and user-facing strings in Portuguese to match.

## Commands

```bash
..\venv\Scripts\activate              # Windows; the venv lives one level above the repo
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser      # the only way to get an administrator
python manage.py runserver            # http://127.0.0.1:8000

python manage.py makemigrations       # after any models.py change
python manage.py test                 # all apps
python manage.py test desempenho      # one app
python manage.py test desempenho.tests.ClassName.test_method   # one test
```

There is no linter, formatter, or build step configured. The only real tests are in `desempenho/tests.py` (card-matching activity); the other `tests.py` files are empty stubs.

`db.sqlite3` is gitignored, but `media/` (uploaded images) is committed.

## Architecture

Server-rendered Django with function-based views, plain HTML/CSS/vanilla JS (no JS framework, no DRF). Templates live in the project-level `templates/<app>/` directory, not inside each app; all pages extend `templates/base.html` except `desempenho/executar.html`, which is a standalone full-screen page.

### Apps and dependency order

`accounts` → `criancas`, `atividades` → `sessoes` → `desempenho`

- **accounts** — `CustomUser` (`AUTH_USER_MODEL`), login/registration, admin user management, and the role-based `dashboard` view (in `dashboard_views.py` / `dashboard_urls.py`, mounted at `/dashboard/`, separate from `accounts/urls.py`).
- **criancas** — `Crianca`, owned by one `psicologo` (FK) and linked to many `responsaveis` (M2M). Children never log in.
- **atividades** — `Atividade` (question + `emocao_correta`) with inline `ImagemEmocao` rows edited through `ImagemFormSet`. An image is correct when its `emocao` equals the activity's `emocao_correta` (`ImagemEmocao.correta` property) — correctness is derived, not stored.
- **atividades (cartões)** — a second activity type, "Cartões Correspondentes": `AtividadeCartoes` with `CartaoEmocao` rows (word + face image + emotion label). The child picks a word card, then the matching face; a pairing is correct when both cards share the same `emocao`, so the formset enforces one card per emotion. It has its own URLs (`/atividades/cartoes/...`, `/desempenho/crianca/<pk>/cartoes/<pk>/...`), its own result model `DesempenhoCartoes` (one row per pairing attempt), and `initCartoes()` in `main.js`. Report totals sum `Desempenho` and `DesempenhoCartoes`. In sessions it is linked through a plain M2M, `Sessao.atividades_cartoes`, and is not part of the "next activity" chain.
- **atividades (cenários)** — a third type, "Organização de Emoções em Cenários": `AtividadeCenario` with `CenarioEmocao` rows (scene image + description + `emocao_correta`). The child drags an emotion label onto each scene (`initCenarios()` in `main.js`, pointer events with a tap-label-then-tap-scene fallback); there is one label per distinct emotion and several scenes may share one. Same structure as the card type: `/atividades/cenarios/...`, `/desempenho/crianca/<pk>/cenarios/<pk>/...`, result model `DesempenhoCenario`, session link `Sessao.atividades_cenarios`. The two newer types share the access helpers `_get_atividade_or_404` and `_get_sessao` in `desempenho/views.py`.
- **sessoes** — `Sessao` groups activities and children through explicit through-models (`SessaoAtividade` carries `ordem`, `SessaoCrianca`). Because of the through-models, `SessaoForm` declares the M2M fields manually and writes them in its own `save()`.
- **desempenho** — `Desempenho`, one row per answer (child, activity, optional session, selected image, `correto`, `tempo_resposta`, `executado_por`). Also owns activity execution and reports.

URL names are global (no `app_name` namespaces): `reverse('detalhe_crianca')`, not `criancas:detalhe`.

### Roles and access control

`CustomUser.role` is one of `admin`, `psicologo`, `responsavel`; psychologists additionally need `aprovado=True`, which an admin sets from `/accounts/admin/usuarios/` (a custom screen, distinct from Django's `/admin/`). Psychologists register unapproved and are sent to `aguardando_aprovacao`; responsáveis are logged in immediately after registering.

Access is enforced in two layers, and new views need both:

1. **Decorators** in `accounts/decorators.py` — `role_required(*roles)` plus the shorthands `psicologo_required`, `responsavel_required`, `admin_required`, `adulto_required`. They redirect (with a flash message) rather than returning 403, let `is_superuser` through regardless of role, and bounce unapproved psychologists. Views stack them under `@login_required`.
2. **Queryset scoping inside each view** — the decorator only checks the role, not ownership. Psychologists see objects where `psicologo=request.user`; responsáveis reach data only through `user.criancas_responsavel` (sessions containing their children, and activities in those sessions). Follow the existing `get_object_or_404(Model, pk=pk, psicologo=user)` pattern and the helpers `_get_crianca_or_403` (desempenho) and `_get_crianca_editavel` (criancas).

A user created with `createsuperuser` keeps the default `role='responsavel'`; it works as admin only because code checks `is_superuser or role == 'admin'`. Keep that double check when branching on role.

### Activity execution flow

`desempenho.views.executar_atividade` renders the images; `initExecution()` in `static/js/main.js` times the answer client-side and POSTs JSON (`imagem_id`, `tempo_resposta`, `sessao_id`) to `registrar_resposta`, which decides correctness server-side, creates the `Desempenho` row, and returns `{correto, emocao_correta}` for the feedback overlay.

Session playback is stateless: the session is carried as a `?sessao=<pk>` query parameter, and the view computes the "next activity" URL from `SessaoAtividade.ordem`. Without that parameter an activity runs standalone and the result is saved with `sessao=None`.

### Settings

`core/settings.py` is a single development configuration (SQLite, `DEBUG=True`, hardcoded `SECRET_KEY`, `ALLOWED_HOSTS=['*']`); there is no environment-based config. Locale is `pt-br` / `America/Sao_Paulo`. Media files are served by Django via `static()` in `core/urls.py`.
