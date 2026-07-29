# Contrato API — Regeneración

## Prerrequisitos

- Backend Django ejecutándose en `http://localhost:8000`

## Regenerar el esquema

```bash
pnpm api:gen
```

Esto ejecuta `openapi-typescript` contra `GET /api/schema/` del backend y
sobrescribe `src/api/schema.d.ts`.

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
