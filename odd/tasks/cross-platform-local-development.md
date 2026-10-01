# Cross-platform local development

## Objective

Make the local development workflow reproducible on native Windows and WSL/Linux without exposing credentials, changing the existing Docker Desktop PostgreSQL catalog, or weakening production safeguards.

## Authorization and constraints

- User authorized planning and implementation for local Windows + WSL/Linux support.
- Preserve the healthy Docker service `codigo-secreto-development-postgres-1` and its named volume. Do not run `docker compose down -v`, seed/reset the catalog, migrate the catalog, or stop unrelated services.
- Never read, print, copy, or commit secret values from `backend/.env` or `docker/postgres.env`.
- Local settings must not connect to remote infrastructure, Cloudinary, SMTP, or production payment providers.
- The tracked Linux virtual environment under `backend/env/` is an unsafe cross-platform artifact. Its removal from Git and the working tree is destructive and requires an explicit confirmation immediately before that operation.
- Existing unrelated untracked task documents remain untouched.
- TDD: disabled; ordinary focused functional checks are required.
- RDD: on by harness default. Candidate review is assessed after a work-unit commit; no commit, push, PR, or merge is authorized by this plan.
- Delivery strategy: ask-on-risk. Estimated authored changes: 260–380 lines excluding the legacy virtualenv removal. Reforecast before a commit if scope materially grows.

## Baseline evidence

- Active branch: `feat/managed-postgresql-runtime`.
- Docker PostgreSQL 16.11 is healthy and loopback-bound at `127.0.0.1:5432`.
- `backend/.env` exists; `frontend/.env` and `docker/postgres.env` are ignored configuration files.
- `backend/env/` is tracked and contains a Linux `/usr/bin` virtualenv layout, unusable on native Windows.
- Backend dependency declarations conflict: Pipenv requires Django 6.0.6 but omits Cloudinary packages, while requirements pin Django 5.2.6 and settings unconditionally register Cloudinary.
- Portable setup is also blocked by POSIX shell expansion in `frontend`'s `api:gen` command and Unix-only runtime code in `backend/core/managed_postgresql_runtime/`.

## Tasks

- [x] **CPD-0 — Provision the supported Windows toolchain.** DONE 2026-09-29.
  - Evidence: Python Install Manager installed user-scoped Python 3.12.10; `py -3.12 -m pip install --user pipenv` installed Pipenv 2026.8.0; both version checks passed. Node 24.19.0, pnpm 12.6.0, Git 2.52.0, Docker Desktop, and Compose were already available.
  - Use `py -3.12 -m pipenv`, not a bare `pipenv` command: its user script directory is not on PATH. No repository, Docker, database, or secret configuration changed.

- [x] **CPD-1 — Reconcile the supported local configuration contract.** DONE 2026-09-29 WITH RECORDED SECURITY EXCEPTION.
  - Route: delegated worker; mapping and configuration span backend settings, environment examples, Docker credentials contract, and project documentation.
  - Implemented candidate changes: a guarded `settings_local` profile, offline local media storage, focused local-profile tests, and Windows/WSL documentation. Django 5.2.6 was selected from repository history; Pipfile, regenerated lock, and requirements now align and declare Cloudinary dependencies. Pipenv created an external user virtualenv, never using `backend/env/`.
  - **Safety decision accepted 2026-09-29:** the normal local profile categorically blocks SMTP egress. Existing SMTP-oriented tests now prove hostile standard and legacy SMTP configuration cannot override that safety contract.
  - Independent dynamic verification in the external Python 3.12 environment passed: focused local/email tests `18 passed` with `settings: core.settings_local (from env)` and `manage.py check` reported zero issues. This proves the pytest base-settings pin does not silently bypass the profile.
  - **Recorded process exception:** one implementation worker reported that a broad grep unintentionally accessed `backend/.env`; it says the file was neither modified, sourced, printed, nor reused. Later independent verification did not access secret files. User acknowledged the residual risk and authorized continuation on 2026-09-29.

- [x] **CPD-2 — Make backend runtime code portable.** DONE 2026-09-29.
  - Route: delegated worker; updated evidence storage and runner code with Windows DACL/reparse-point/write-through checks, Windows process-group/tree termination, and preserved POSIX UID/mode/session/signal behavior. Filesystems that cannot prove the Windows privacy guarantee fail closed.
  - Focused changed-file tests passed `45 passed`; Django system check passed. The complete managed-runtime test selection remains `94 passed, 3 failed`: `backend/core/tests/test_managed_postgresql_runtime_runner.py` still asserts POSIX-only `start_new_session` and `SIGKILL` behavior.
  - User authorized the one derived additional edit surface `backend/core/tests/test_managed_postgresql_runtime_runner.py` on 2026-09-29. No database, Docker, secret, migration, seed, or remote operation occurred. WSL execution remains pending; only Windows dynamic execution and POSIX branch tests have run.
  - Independent verification found and the worker corrected a medium Windows cleanup defect: graceful `taskkill /T` failure now escalates to `/F`, preserves timeout/cancellation semantics on success, and still propagates force-termination failure fail-closed. Targeted escalation tests `2 passed`; full managed-runtime selection `99 passed` with no skips; dynamic Django system check and static diff checks passed.
  - Non-blocking limits: Windows process cleanup is safely unit-tested with doubles, not a live child tree; real WSL execution remains a separate CPD-5 environment check. Low malformed-evidence and ACL-test-strengthening findings do not bypass current fail-closed behavior.

- [x] **CPD-3 — Make frontend tooling and documentation shell-neutral.** DONE 2026-09-30.
  - Route: delegated worker; expected edits span package scripts, Vite configuration, examples, and READMEs.
  - Replace POSIX-only package scripts and document PowerShell plus Bash/WSL commands that avoid ambient dotenv loading.
  - The first delegated writer stalled during file discovery and made no frontend changes. User authorized a newly scoped, narrow discovery pass on 2026-09-30; do not reuse the timed-out task.
  - Node wrappers now launch allowlisted package bins without shell interpolation; `LOCAL_NO_DOTENV=1` is set before local tests/builds; production and development modes remain distinct. Documentation covers PowerShell, CMD, and WSL/Bash paths.
  - Verification: `test:local` passed 289 tests; production build with a non-secret HTTPS fixture passed; local development-mode build passed; `check:schema` now passes after `src/api/schema.d.ts` was regenerated offline from versioned `backend/schema.yaml`.
  - User authorized and the parent deleted the nonfunctional untracked `frontend/pnpm-workspace.yaml` placeholder. Independent verification confirmed its absence, schema currency, and wrapper safety. No further package installation/download occurred after the initial failed attempt.

- [x] **CPD-4 — Retire the tracked Linux virtualenv safely.** DONE 2026-09-30.
  - User authorized removal; `backend/env/` is absent from the working tree and Git index. Root `.gitignore` blocks replacement paths.
  - Add durable ignore protection and document creation of a per-machine virtualenv/Pipenv environment.
  - Checks: verify no `backend/env/` paths remain tracked and a fresh environment can run the supported backend checks.

- [x] **CPD-5 — Verify the local workflow and record evidence.** DONE 2026-09-30 WITH WSL FRONTEND DEFERRED TO LINUX CI.
  - Route: delegated verification.
  - Validate Windows-native-compatible commands in the current environment and Bash/WSL-compatible commands without stopping or modifying the existing PostgreSQL catalog.
  - Record exact checks, outcomes, skipped external services, and any remaining platform limitations.
  - Native Windows evidence: Docker PostgreSQL healthy; Django check passes under in-memory local profile; frontend local tests 289 passed; production and local builds passed; schema and diff checks passed. Full backend suite had 3 timestamp-ordering failures but immediate isolated rerun passed all 3; candidate did not touch those files, so causality is unproven/non-candidate by current evidence.
  - User accepted Windows-native verification as the local development gate on 2026-09-30. Backend Windows suite passed 687 tests after deterministic tie-safe test assertions; frontend Windows checks passed. WSL backend suite also passed 687 tests, but WSL frontend execution is deferred: native WSL Node 24/pnpm was installed, yet host-cancelled full-suite attempts made it unsuitable as a local gate.
  - Linux compatibility moves to CI on an Ubuntu runner, which is more relevant to DigitalOcean than a WSL checkout under `/mnt/c`. `docker/postgres.env` remains absent; never create or inspect it. CPD-6 is authorized.

- [ ] **CPD-6 — Create reviewable work-unit commits.** AUTHORIZED AFTER CPD-5 PASSES.
  - Blocked pending explicit user authorization to commit.
  - Keep code, tests, and documentation together in conventional commits; assess each committed candidate before reporting it complete.

## Acceptance criteria

1. A developer can set up and run the backend/frontend on Windows PowerShell and WSL/Linux Bash from documented commands.
2. The local profile uses only the existing loopback Docker PostgreSQL configuration and does not modify its catalog during setup or verification.
3. No platform-specific virtualenv, credentials, or unsafe production integration configuration is tracked.
4. The backend no longer crashes merely because Windows lacks POSIX-only APIs.
5. Dependency, environment, and documentation instructions agree and the applicable checks have recorded outcomes.

## Next step

**CPD-7 — Restore local checkout CORS preflight.** DONE. Added the exact guest capability, idempotency, and retry headers to the backend allow-list; system and safe OPTIONS checks passed without wildcard CORS behavior. Evidence: `1df83a1` (`fix(cors): allow checkout request headers`).

**CPD-8 — Add safe transactional-email environments.** DONE. Mailpit is loopback-only with no credentials/volume; local Django targets it while tests retain in-memory mail. Documentation defines the secret-free Brevo production contract. Focused checks passed; manual Mailpit confirmation was observed. Evidence: `a9bad4b` (`feat(email): add local Mailpit capture`).

**CPD-9 — Notify customers on delivered status.** DONE. Added the idempotent `delivered` notification event, scheduled only after the legal `SHIPPED` → `DELIVERED` transition. Guest emails receive a signed tracking ticket; authenticated users receive no capability. Existing retries record failure without reversing delivery. Isolated focused test suite passed (67 passed, 1 PostgreSQL-only skipped); independent verification passed (44 passed). Evidence: `b8d0f27` (`feat(orders): notify customers when delivered`).

**CPD-10 — Clarify guest tracking status in Django Admin.** DONE. Replaced technical capability terminology in the order list with user-facing guest-tracking states: `Disponible`, `No aplica`, `Expirado`, and `Revocado`; security/action behavior remains unchanged. Focused parameterized admin test passed (4 cases), including revoked-before-expired precedence; independent verification passed. Evidence: `8f09df5` (`feat(admin): clarify guest tracking statuses`).
