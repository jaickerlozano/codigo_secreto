# Windows Project-Local Virtualenv

## Goal
Create a recognizable Windows-only Pipenv environment at `backend/.venv/` so the user can activate it from Git Bash with `source .venv/Scripts/activate`.

## Problem and accepted decision
The external environment is valid practice, but its generated path is inconvenient for this user's Windows Git Bash workflow. Keep Pipenv and `Pipfile.lock` authoritative; the change is environment location, not dependency/runtime/security behavior.

## Scope and constraints
- Create `backend/.venv/` with Python 3.12 and locked default/development dependencies using Pipenv.
- Windows operator commands select `PIPENV_VENV_IN_PROJECT=1`; preserve all dotenv guards and `core.settings_local` behavior.
- Update root/backend README instructions to explain local Windows activation and separate WSL environments.
- `.venv` is already ignored by Git; never stage installed packages/interpreter binaries.
- Preserve the previous external environment under `%USERPROFILE%\.virtualenvs\<previous-project-environment>` until separately confirmed, path-specific cleanup. Do not delete other environments or the entire `.virtualenvs` directory.
- No .env/docker secret reads, live database/network service tests, migrations, seeds, Docker lifecycle, shell/profile/alias writes or system configuration changes. Commit/push requires user authorization, now granted for documentation only.
- Installation may contact locked dependency package sources only. Do not upgrade the lockfile.
- Do not change WSL's environment or share the Windows environment with WSL.

## Execution and checks
- Delegated writer/setup: new environment and two README changes require coordinated work.
- Strict TDD disabled, source existing session/ODD mode; ordinary verification required.
- Setup from backend with `PIPENV_DONT_LOAD_ENV=1 DJANGO_READ_DOTENV=0 PIPENV_VENV_IN_PROJECT=1 PIPENV_IGNORE_VIRTUALENVS=1`: `py -3.12 -m pipenv sync --dev`.
- Verify `py -3.12 -m pipenv --venv` and interpreter `sys.prefix/sys.executable` point into backend/.venv.
- Verify interpreter/dependency integrity with `py -3.12 -m pipenv run python -m pip check`.
- Under `DJANGO_SETTINGS_MODULE=core.settings_local LOCAL_TEST_DATABASE=1` plus the setup guards: `py -3.12 -m pipenv run python manage.py check`; `py -3.12 -m pipenv run python -m pytest core/tests/test_local_development.py core/tests/test_email_settings.py`.
- Verify `git check-ignore backend/.venv/Scripts/python.exe` and no Pipfile.lock/source/unrelated artifacts changed.
- Forecast approximately 30-100 authored changed lines (environment files excluded); delivery strategy ask-on-risk.

## Tasks
- [x] WV-1: Create Windows local Pipenv environment and update operator documentation.
- [x] WV-2: Validate interpreter, locked dependencies, activation, isolated checks and ignored Git state.
- [ ] WV-3: External-environment cleanup only after explicit path-specific authorization.
- [x] WV-4: Documentation commit/push authorized and published separately on `chore/windows-project-virtualenv`.

## Recovery
Retain the external environment while local creation/validation is incomplete. If setup fails, record the exact failure and preserve both existing source and environments. Do not bypass Windows path restrictions via global system changes. Never invoke `pipenv --rm` with the new local environment selected when intending to remove the external old one.

## Progress and evidence
WV-1 and WV-2 complete locally:
- Windows-only backend/.venv created with Python 3.12.10 using unchanged Pipfile/Pipfile.lock; frontend lock also unchanged.
- Writer: pip check clean, Django check clean, 20 isolated local/email tests passed, successful disposable Git Bash activation, ignored environment, no new unrelated changes.
- Independent verifier: confirmed local prefix/interpreter, pip check, 20 passing tests, disposable activation, Git ignore and unchanged pre/post status.
- Parent spot check: Pipenv reports backend/.venv. Documentation corrected to remove obsolete tracked-env wording and avoid a personal absolute path in the public README.
- Native ASSESS unavailable due to untracked declarations; its required independent verification was completed. No native approved receipt claimed.
- PowerShell activation and WSL execution documented but not exercised.

## Next step
Use `source .venv/Scripts/activate` from backend. Windows Pipenv commands require PIPENV_VENV_IN_PROJECT=1; runtime dotenv guards/local Django settings still apply. Documentation commit `dd7c34d` pushed to `origin/chore/windows-project-virtualenv`, independently based on verified default `main`, per user-selected `stacked-to-main` delivery. Fresh independent verification: pip check and Django check clean, 20 isolated tests passed, committed scope/whitespace/ignore checks passed. No PR/merge performed. WV-3 remains pending: external environment retained; no environment binaries uploaded, deletion or alias/profile edits performed.
