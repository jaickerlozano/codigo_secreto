# Código Secreto

Monorepo del eCommerce de bienestar íntimo para Chile. Incluye catálogo de productos, carro de compras, envíos, pagos simulados y seguimiento de pedidos.

## Estructura

```
/
├── backend/   Django + Django REST Framework + loopback PostgreSQL (local)
└── frontend/  React + TypeScript + Vite + Tailwind CSS
```

## Supported local toolchain

Use the same major-version contract on native Windows and WSL/Linux:

- Python 3.12.x with Pipenv (Windows: `backend/.venv`; WSL/Linux: separate external environment)
- Node.js 22.x LTS
- pnpm 10.x
- Docker Desktop 4.x with Docker Compose v2
- Git 2.40 or newer

Do not share virtual environments or `node_modules` between Windows and WSL.
The backend dependency source of truth is `backend/Pipfile.lock`; on Windows,
invoke Pipenv as `py -3.12 -m pipenv` rather than assuming it is on `PATH`.

## Inicio rápido

### Backend

On Windows Git Bash, install the locked dependencies and activate from `backend/`:

```bash
cd backend
export PIPENV_DONT_LOAD_ENV=1 DJANGO_READ_DOTENV=0
export PIPENV_VENV_IN_PROJECT=1 PIPENV_IGNORE_VIRTUALENVS=1
py -3.12 -m pipenv sync --dev
source .venv/Scripts/activate
python -c "import sys; print(sys.executable); print(sys.prefix)"
```

Both paths must point into `backend/.venv`. In PowerShell, set the same guards
with `$env:NAME = "value"`, then use `py -3.12 -m pipenv sync --dev` and
`.\.venv\Scripts\Activate.ps1` from `backend/`. Complete PowerShell commands
are in [the backend guide](backend/README.md#install-dependencies).

This is a Windows-only environment. Retain the existing external Windows
environment; no cleanup is required. WSL/Linux must use
`PIPENV_VENV_IN_PROJECT=0` with its own external environment, or a separate
checkout/environment; never activate or select the Windows `.venv`.

Activation selects Python; it does not select safe Django settings. Keep both
dotenv guards and explicitly set `DJANGO_SETTINGS_MODULE=core.settings_local`
before running Django, as shown in the backend guide. Do not use default
settings as an activation check.

Use the explicit read-only/offline local profile. It disables dotenv loading,
connects only to loopback PostgreSQL, and routes transactional email only to the
loopback Mailpit capture service; it does not run setup migrations or seed
commands. Mailpit accepts SMTP on `127.0.0.1:1025` and exposes its browser inbox
at `http://127.0.0.1:8025`. Startup and the manual guest tracking-email check are
documented in [the backend local-profile guide](backend/README.md#supported-local-profile).

El backend queda disponible en `http://localhost:8000`.

### Frontend

En PowerShell, CMD o WSL/Linux Bash:

```text
cd frontend
pnpm install
pnpm run dev
```

Si necesitás configuración local, copiá la plantilla ignorada con
`Copy-Item .env.example .env` en PowerShell o `cp .env.example .env` en
WSL/Linux Bash. Mantené configuraciones separadas entre Windows y WSL.

El frontend queda disponible en `http://localhost:5173`.

## Variables de entorno

The supported backend local profile does not read `backend/.env`. Docker keeps
its local PostgreSQL values in ignored `docker/postgres.env`; do not source,
print, or duplicate those values. Local Mailpit needs no credentials and has no
persistent volume. Production Brevo inputs remain deployment-injected under the
[documented environment contract](docs/production-security.md#brevo-transactional-email-contract).

### Frontend (`frontend/.env`)

Creá el archivo local copiando la plantilla como se indica arriba y editá la
copia para tu máquina. No compartas el archivo ni sus valores entre entornos.
Los comandos `test:local` y `build:local` omiten la carga de dotenv.

## Production security

Production environment formats, ownership, validation evidence, and release gates are documented in [Production security](docs/production-security.md). The runbook intentionally contains no secrets or assigned production API hostname.

## Regenerar tipos del API

Cuando cambien los serializers del backend:

```bash
cd frontend
pnpm run api:gen
```

Esto actualiza `src/api/schema.d.ts` a partir del schema OpenAPI del backend.
El script usa `VITE_API_URL` si está definida y, en caso contrario, apunta a
`http://localhost:8000` en PowerShell, CMD y Bash sin sintaxis específica del
shell.

## Testing

### Backend

Run focused tests through the platform-specific Python environment described in
the backend guide, with `DJANGO_SETTINGS_MODULE=core.settings_local`,
`DJANGO_READ_DOTENV=0`, `PIPENV_DONT_LOAD_ENV=1`, and
`LOCAL_TEST_DATABASE=1`. This keeps verification off the Docker catalog.

### Frontend

```text
cd frontend
pnpm run test:local
pnpm run build:local
pnpm run check:schema
pnpm oxlint src/
```

`test:local` y `build:local` establecen `LOCAL_NO_DOTENV=1` mediante Node. Para
validar producción, definí una URL HTTPS no secreta en `VITE_API_URL` y ejecutá
`pnpm run build`; el guard HTTPS de producción permanece activo. Los comandos
por shell y el drift check del backend están documentados en
[el contrato API](frontend/src/README.md#verificar-que-el-esquema-no-está-desactualizado-drift-check).
