# Contrato API — Regeneración

## Prerrequisitos

- Backend Django ejecutándose en `http://localhost:8000`

## Regenerar el esquema

```bash
pnpm api:gen
```

Esto ejecuta `openapi-typescript` contra `GET /api/schema/` del backend y
sobrescribe `src/api/schema.d.ts`.

Para regenerar de forma determinista desde el `backend/schema.yaml` versionado
(equivalente a lo que sirve `GET /api/schema/`):

```bash
pnpm exec openapi-typescript ../backend/schema.yaml -o src/api/schema.d.ts
```

## Verificar que el esquema no está desactualizado (drift check)

Este comando es portable entre PowerShell, CMD y WSL/Linux Bash:

```text
pnpm run check:schema
```

Compara la salida generada con `src/api/schema.d.ts` y sale con código 1 si el
tipo no está al día.

Para verificar también que el YAML versionado coincide con el schema generado
por Django, usá el entorno Python propio de cada plataforma y bloqueá la carga
de dotenv. En PowerShell:

```powershell
cd ../backend
$env:DJANGO_SETTINGS_MODULE = "core.settings_local"
$env:DJANGO_READ_DOTENV = "0"
$env:PIPENV_DONT_LOAD_ENV = "1"
$schema = Join-Path $env:TEMP "codigo-secreto-schema.yaml"
py -3.12 -m pipenv run python manage.py spectacular --validate --file $schema
git diff --no-index --exit-code -- schema.yaml $schema
```

En WSL/Linux Bash:

```bash
cd ../backend
schema="$(mktemp)"
DJANGO_SETTINGS_MODULE=core.settings_local DJANGO_READ_DOTENV=0 \
  PIPENV_DONT_LOAD_ENV=1 pipenv run python manage.py spectacular \
  --validate --file "$schema"
git diff --no-index --exit-code -- schema.yaml "$schema"
```

## Validación

Las pruebas y el build locales aíslan la configuración de dotenv:

```text
pnpm run test:local
pnpm run build:local
pnpm run lint
```

El build de producción conserva el guard HTTPS. Por ejemplo, en PowerShell:

```powershell
$env:VITE_API_URL = "https://api.example.test"
pnpm run build
```

Todos los comandos deben salir con código 0.

## Reglas

- `src/api/schema.d.ts` es auto-generado. No editar a mano.
- Tras cualquier cambio en los serializers o endpoints del backend, regenerar
  el esquema y reparar los consumidores (mappers, tipos, hooks) antes de
  commitear.
