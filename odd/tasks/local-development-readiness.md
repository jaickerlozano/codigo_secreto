# Local development readiness

## Objective and authorization

Make manual application startup reproducible on the user's computer with the existing PostgreSQL catalog, then run isolated functional checks. This is not production readiness or a new generic testing framework.

- Current authorization: one bounded local implementation and functional-check pass for LDR-1/2/3, including localhost backend:8000 and frontend:5173 startup, closed with work-unit commits on the feature branch (push/PR/merge remain user decisions).
- Read-only local inspection of `docker/postgres.env` and explicit loopback PostgreSQL is authorized. Never print credentials or put them in command arguments, documentation, or evidence.
- Never read/load `backend/.env`, inherit remote credentials, call Cloudinary, or write catalog/image data. Only the two authorized local application services may be started; do not stop unrelated processes.
- Implementation may use isolated package installation and disposable tests. No catalog seeding/reset, image-reference changes, upload/delete, migrations on the catalog, remote operations, merge, push, or PR is included.
- Future production intent is DigitalOcean backend and Vercel frontend with a custom domain. Current Vercel lacks that custom domain. Provisioning, domain selection and remote access remain excluded.

## Verified baseline

- Branch `feat/managed-postgresql-runtime`, HEAD `c9d1707`; local `main` is stale. Cached `origin/main` contains HEAD through PR130 and has the same tree. No fetch performed.
- Preserve nine dirty files: authentication test factories and factory tests; order notification-processing tests; product image-upload tests; `backend/conftest.py`, `core/settings.py`, `pytest.ini`, `requirements.txt`; `docs/production-security.md`. Baseline: 68 additions and 6 deletions. These are pre-existing changes, not accepted work or passing evidence.
- Preserve untracked `backend/.runtime-evidence/`; contents were not inspected. Add ignore protection before future staging, not deletion.
- Local connection configuration is available in `docker/postgres.env`. Explicit `127.0.0.1:5432` authentication succeeded; requested database/user matched server identity before catalog queries. Transaction was read-only and rolled back.
- PostgreSQL currently has 44 products, 43 nonempty primary references and zero gallery rows. All 43 references are relative; none supplies Cloudinary namespace provenance. No rows or assets changed.
- Installed backend environment: Python 3.12.13, Django 6.0.6, psycopg 3.3.5. Requirements instead pin Django 5.2.6 and psycopg 3.2.10. Pipfile pins Django 6.0.6 and lacks Cloudinary/storage declarations. Node 20.20.0 and pnpm 10.33.4 are available.
- Current settings require Cloudinary inputs and default to cloud-backed storage; local mock payment requires `DEBUG=True` and `PAYMENT_PROVIDER=mock`. Vite currently loads local dotenv files unless explicitly disabled.

## Route, modes and delivery

- Route: delegated implementation. Trigger evidence: coordinated settings/storage, frontend environment, dependency and functional-verification work requires analysis across multiple files. No UI redesign or API contract changes are planned.
- TDD: disabled; authoritative source supplied by parent is full Engram #144, `sdd/codigo_secreto/testing-capabilities`, dated 2026-09-11. Ordinary functional tests are still required; no invented RED/GREEN receipt.
- RDD: off, source `clone_local` (parent-resolved). Do not start review or change that switch.
- Default delivery: ask-on-risk. Advisory budget is 400 authored additions plus deletions, including tests and this document. No automatic commits and no artificial splits.
- Forecast: 340-395 authored changed lines total, including the existing 74 and this document. Assumes one small local settings module, bounded storage policy, focused tests and no lockfile regeneration. Stop and ask if a credible revised forecast exceeds 400; do not omit tests to fit.

## Tasks

- [x] **LDR-1 — Reproducible local configuration and dependency route.** DONE 2026-09-24. `core/settings_local.py` enforces both dotenv guards, refuses production, injects development-only secret/DEBUG/mock payments/console email, and blanks Cloudinary credentials; `core/local_configuration.py` parses only the three approved keys from `docker/postgres.env` without shell evaluation, pins loopback host/port, and sets `default_transaction_read_only=on`. Clean requirements-based venv verified at `/tmp/opencode/codigo-local-venv` (Django 5.2.6, psycopg 3.2.10); ambient `backend/env` untouched. Frontend: `LOCAL_NO_DOTENV=1` disables Vite envDir loading, `envPrefix` exposes `LOCAL_*` to tests only, dev server binds `localhost`. Evidence: 11 focused tests pass; `manage.py check` clean; full suite green (below).
- [x] **LDR-2 — Safe catalog/image presentation.** DONE 2026-09-24 with a documented limitation. `core/local_storage.py` renders delivery URLs only from an owner-supplied `LOCAL_CLOUDINARY_NAMESPACE` (validated charset, relative refs only, no SDK/network), and `open/save/delete/exists` always raise `PermissionError`. `apps/products/images.py` passes preserved delivery URLs through unchanged (no AI transformations). Without a namespace, `url()` returns `None` → API serves `image: null` and the frontend shows its existing placeholder; catalog and references are untouched. Remaining limitation: the public Cloudinary cloud name is not in committed source; provide it via `LOCAL_CLOUDINARY_NAMESPACE=<cloud-name>` (public identifier, not a secret) to render real images locally.
- [x] **LDR-3 — Verify existing changes and document manual startup.** DONE 2026-09-24 except deferred items below. The nine-file baseline was reviewed by diff (dotenv opt-out in `core/settings.py`, psycopg pin, marker text, factory/test adjustments, docs) and validated by the full green suite rather than silent adoption; `backend/.runtime-evidence/` is now git-ignored. Isolated functional checks and localhost smoke executed (evidence below). Deferred, not blocking local manual testing: `pg_only` tests (need separately authorized disposable PostgreSQL) and work-unit commits (need explicit user authorization).

## Executed verification evidence (2026-09-24)

Interpreter: `/tmp/opencode/codigo-local-venv/bin/python` (requirements.txt pins). Every backend command ran in a cleared environment with `PIPENV_DONT_LOAD_ENV=1 DJANGO_READ_DOTENV=0 DJANGO_SETTINGS_MODULE=core.settings_local`; test suites added `LOCAL_TEST_DATABASE=1` (in-memory SQLite, in-memory media, locmem email, network access denied by autouse conftest fixture). Frontend ran with cleared env and `LOCAL_NO_DOTENV=1`.

| Check | Command | Result |
|---|---|---|
| Focused local config/storage tests | `pytest core/tests/test_local_development.py` | 11 passed |
| Backend ordinary suite | `pytest -m 'not pg_only'` | 660 passed, 4 deselected, 3 pre-existing pagination warnings |
| Django discovery | `manage.py test --noinput` | ran; 0 unittest-style tests discovered (pytest is the authoritative runner; system checks clean) |
| Catalog profile checks | `manage.py check` / `migrate --check` / `makemigrations --check --dry-run` (PostgreSQL, read-only) | no issues / no pending migrations / no changes detected |
| Frontend unit/integration | `pnpm run test` | 289 passed (65 files) |
| Frontend lint | `pnpm run lint` | 0 errors, 8 pre-existing warnings |
| OpenAPI contract | `pnpm run check:schema` | no drift |
| Frontend build | `VITE_API_URL=https://api.example.test pnpm run build` | success after fixing a candidate-caused TS2591 (`node:process` import in `src/test/setup.ts` replaced with `import.meta.env` + `envPrefix`); pre-existing chunk-size warning only |
| Frontend format | `pnpm run format:check` | pre-existing repository-wide failure (190 files incl. untouched ones); prettier is not an enforced gate here — recorded, not normalized |
| Localhost smoke | backend `runserver localhost:8000`, frontend `vite --host localhost --port 5173 --strictPort` | both listeners on `127.0.0.1` only; `GET /api/` 200; `GET /api/products/` 200 with `count: 44` from PostgreSQL; frontend `/` 200; proxied `/api/products/` 200; no image URLs fetched; both processes stopped afterwards |

Manual startup contract (unchanged wrappers):

```bash
# backend/ — catalog browsing profile (PostgreSQL read-only)
env -i PATH=/usr/bin:/bin PIPENV_DONT_LOAD_ENV=1 DJANGO_READ_DOTENV=0 \
  DJANGO_SETTINGS_MODULE=core.settings_local \
  /tmp/opencode/codigo-local-venv/bin/python manage.py runserver localhost:8000 --noreload
# add LOCAL_CLOUDINARY_NAMESPACE=<public-cloud-name> to render real images
# frontend/
env -i PATH=/home/jaicker/.nvm/versions/node/v20.20.0/bin:/usr/bin:/bin HOME=/home/jaicker \
  LOCAL_NO_DOTENV=1 pnpm exec vite --host localhost --port 5173 --strictPort
```

## Acceptance, evidence and next step

- Acceptance MET for local manual testing: documented startup reaches the preserved 44-product catalog read-only, mock configuration is explicit, SMTP/storage mutation is disabled, credentials cannot be inherited, isolated checks have real outcomes, and the image limitation is honestly reported (placeholder until a public namespace is supplied).
- Rollback units: remove `backend/core/{settings_local,local_configuration,local_storage}.py`, `backend/core/tests/test_local_development.py`, the `images.py` preserve-delivery-url hunk, conftest offline fixture, `.gitignore` line, frontend `envDir`/`envPrefix`/`host`/setup.ts hunks, and `odd/` — each independently revertible; never revert the pre-existing baseline wholesale or alter catalog data.
- Authored line count: 95 (tracked diff) + 149 (new source/tests) = 244, plus 87 doc lines; under the 400 advisory budget.
- Pending evidence: `pg_only` suite on a separately authorized disposable PostgreSQL; manual checkout walkthrough by the user (catalog mode blocks real writes by design; checkout flows are covered by the disposable-SQLite test suite).
- Work-unit commits (branch `feat/managed-postgresql-runtime`, not pushed; push/PR/merge remain user decisions):
  - `03bdb3d` fix(runtime): harden managed PostgreSQL test support — the reviewed pre-existing baseline (10 files).
  - `c7bd612` feat(dev): add local-only development profile with read-only catalog (7 files).
  - `f88b14b` docs(odd): record local development readiness tasks and verification evidence.
  - `2f0f02b` feat(dev): add explicit LOCAL_ALLOW_WRITES opt-in for catalog writes — checkout testing needs writes; default stays read-only (12 focused tests, full suite 661 passed).
  - `a1eb6a3` docs(odd): record local image reconciliation outcome.
- Next step: user runs the manual browser smoke, simulates local mock purchases, and decides push/merge to main. Three products now use their verified Cloudinary image sets; the other 41 remain placeholders until real images are uploaded.
