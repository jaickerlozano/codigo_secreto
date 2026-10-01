# Backend — Código Secreto

API REST con Django y Django REST Framework para el eCommerce.

## Supported local profile

The supported backend toolchain is Python 3.12.x plus Pipenv on either native
Windows or WSL/Linux. `Pipfile.lock` is the authoritative installation input;
`requirements.txt` is its pinned default-and-development compatibility export.
Use a separate external Pipenv environment on each platform. Never reuse,
activate, modify, or delete the tracked legacy `backend/env/` directory.

### Install dependencies

PowerShell, from `backend/` (a bare `pipenv` command is not required):

```powershell
$env:PIPENV_DONT_LOAD_ENV = "1"
$env:PIPENV_VENV_IN_PROJECT = "0"
$env:PIPENV_IGNORE_VIRTUALENVS = "1"
py -3.12 -m pipenv sync --dev
py -3.12 -m pipenv --venv
```

WSL/Linux Bash, from `backend/`:

```bash
export PIPENV_DONT_LOAD_ENV=1
export PIPENV_VENV_IN_PROJECT=0
export PIPENV_IGNORE_VIRTUALENVS=1
python3.12 -m pipenv sync --dev
python3.12 -m pipenv --venv
```

The reported environment path must be outside the repository. Dependency
updates must start in `Pipfile`, regenerate `Pipfile.lock` with Python 3.12, and
refresh `requirements.txt` from that lock so all three declarations agree.

### Run without dotenv loading

The explicit `core.settings_local` profile refuses to start unless both dotenv
guards are present. It reads only `POSTGRES_DB`, `POSTGRES_USER`, and
`POSTGRES_PASSWORD` from the ignored `docker/postgres.env`; it never reads
`backend/.env`, accepts a database hostname from that file, or constructs a
remote database target. The resulting PostgreSQL connection is fixed to
`127.0.0.1:5432` and is transaction-read-only by default.

PowerShell:

```powershell
$env:DJANGO_SETTINGS_MODULE = "core.settings_local"
$env:DJANGO_READ_DOTENV = "0"
$env:PIPENV_DONT_LOAD_ENV = "1"
$env:PIPENV_VENV_IN_PROJECT = "0"
$env:PIPENV_IGNORE_VIRTUALENVS = "1"
py -3.12 -m pipenv run python manage.py check
py -3.12 -m pipenv run python manage.py runserver
```

WSL/Linux Bash:

```bash
export DJANGO_SETTINGS_MODULE=core.settings_local
export DJANGO_READ_DOTENV=0
export PIPENV_DONT_LOAD_ENV=1
export PIPENV_VENV_IN_PROJECT=0
export PIPENV_IGNORE_VIRTUALENVS=1
python3.12 -m pipenv run python manage.py check
python3.12 -m pipenv run python manage.py runserver
```

The server is available at `http://localhost:8000`. The local profile forces the
mock payment provider, blank Cloudinary credentials, offline media storage, and
email capture through the loopback Mailpit service. Its SMTP target is fixed to
`127.0.0.1:1025`, with TLS and credentials disabled; inherited SMTP variables
cannot redirect local mail to an external server. Existing remote image
references remain unresolved locally.

### Development containers

The root `compose.yaml` provides PostgreSQL 16 on loopback and persists its
catalog in the existing `postgres_data` named volume. It also provides Mailpit
without a Docker volume: SMTP capture is loopback-bound on `127.0.0.1:1025`, and
the browser inbox is loopback-bound at `http://127.0.0.1:8025`. Captured messages
are disposable and never leave Mailpit.

Provision the ignored `docker/postgres.env` from its tracked example without
copying its values into `backend/.env`, then start the two local services from
the repository root:

```bash
docker compose up -d --wait postgres mailpit
```

Normal local startup does not run migrations or seed/reset commands. Do not set
`LOCAL_ALLOW_WRITES`; that opt-in is reserved for an explicitly authorized
catalog-changing workflow. Focused settings tests use an isolated in-memory
SQLite database and Django's in-memory email backend by setting
`LOCAL_TEST_DATABASE=1`, so they neither connect to Mailpit nor connect to or
write the Docker catalog.

### Manual guest tracking-email check

Use this only with an explicitly authorized writable local catalog and the mock
payment provider; it does not require a real recipient or SMTP credential.

1. Start `postgres` and `mailpit`, then run the backend with the local profile
   and `LOCAL_ALLOW_WRITES=1`; run the frontend normally.
2. Complete the existing guest checkout with a synthetic address such as
   `guest@example.invalid`, then complete the existing mock payment approval.
3. Open `http://127.0.0.1:8025`, select the payment-confirmation message, and
   open its guest tracking link in a private browser window.
4. Confirm the order page loads, the URL capability fragment is removed after
   exchange, and no message was delivered to an external mailbox.

Do not use a real recipient, add provider credentials, or change checkout data
handling for this check. Mailpit captures the message regardless of its
recipient domain.

Production keeps using `core.settings`, its managed PostgreSQL `DATABASE_URL`,
SMTP, Cloudinary, and deployment-injected secrets. Never select
`core.settings_local` in production.

## Aplicaciones

Las apps viven en `apps/` y están aisladas por dominio:

- `authentication` — usuarios, JWT vía cookies HttpOnly.
- `products` — catálogo, categorías, proveedores.
- `carts` — carro de compras.
- `shipping` — regiones, comunas y opciones de envío.
- `orders` — pedidos y su ciclo de vida.
- `payments` — gateway de pagos simulado (`MockPaymentProvider`).

## Testing

With the local-profile guards above plus `LOCAL_TEST_DATABASE=1`, run tests
through Pipenv. For example, on PowerShell:

```powershell
$env:LOCAL_TEST_DATABASE = "1"
py -3.12 -m pipenv run python -m pytest core/tests/test_local_development.py core/tests/test_email_settings.py
```

On WSL/Linux, use `python3.12 -m pipenv run` with the same exported guards. La
configuración de cobertura está en `pyproject.toml`.

## Comandos de administración

### `seed_products`

Crea o actualiza el catálogo semilla de 44 productos.

This command changes the catalog and is not part of normal local-profile setup.
Run it only in an explicitly authorized writable workflow:

```bash
python manage.py seed_products
```

`seed_products --reset` is destructive and must not be used against the shared
Docker development catalog.

## Notificaciones de cliente (`process_notifications`)

El comando `process_notifications` reintenta los correos transaccionales fallidos (pago y despacho):

```bash
python manage.py process_notifications --batch-size 100
```

Ejecutarlo como mínimo cada 5 minutos. Ejemplo con cron:

```cron
*/5 * * * * cd /ruta/al/proyecto/backend && /path/to/venv/bin/python manage.py process_notifications >> /var/log/codigo-secreto/notifications.log 2>&1
```

O con systemd. Timer (`/etc/systemd/system/codigo-secreto-notifications.timer`):

```ini
[Unit]
Description=Reintentar notificaciones cada 5 minutos

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

Servicio (`/etc/systemd/system/codigo-secreto-notifications.service`):

```ini
[Unit]
Description=Procesar notificaciones de Código Secreto

[Service]
Type=oneshot
WorkingDirectory=/ruta/al/proyecto/backend
EnvironmentFile=/ruta/al/proyecto/backend/.env
ExecStart=/path/to/venv/bin/python manage.py process_notifications
```

### Variables de entorno SMTP (producción)

Production uses the Brevo SMTP contract documented in
[`docs/production-security.md`](../docs/production-security.md#brevo-transactional-email-contract).
Credentials remain deployment-injected; do not add them to repository files.
These variables apply to `core.settings`, not to `core.settings_local`, whose
only SMTP destination is the loopback Mailpit capture service.

## Schema de la API

Genera el schema OpenAPI en `schema.yaml`:

```bash
python manage.py spectacular --file schema.yaml
```
