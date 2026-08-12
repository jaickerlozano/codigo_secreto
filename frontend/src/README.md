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

```bash
pnpm check:schema
```

Compara la salida generada con `src/api/schema.d.ts` y sale con código 1 si el
tipo no está al día. En el backend, el check equivalente es:

```bash
cd ../backend && env/bin/python manage.py spectacular --validate --file /tmp/schema.yaml && diff -q /tmp/schema.yaml schema.yaml
```

## Validación

```bash
pnpm run build
pnpm run lint
```

Ambos deben salir con código 0.

## Reglas

- `src/api/schema.d.ts` es auto-generado. No editar a mano.
- Tras cualquier cambio en los serializers o endpoints del backend, regenerar
  el esquema y reparar los consumidores (mappers, tipos, hooks) antes de
  commitear.
