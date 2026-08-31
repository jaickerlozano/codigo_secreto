# Código Secreto

Monorepo del eCommerce de bienestar íntimo para Chile. Incluye catálogo de productos, carro de compras, envíos, pagos simulados y seguimiento de pedidos.

## Estructura

```
/
├── backend/   Django + Django REST Framework + SQLite (dev)
└── frontend/  React + TypeScript + Vite + Tailwind CSS
```

## Requisitos

- Python 3.12 + Pipenv
- Node.js + pnpm

## Inicio rápido

### Backend

```bash
cd backend
pipenv install
pipenv run python manage.py migrate
pipenv run python manage.py seed_products
pipenv run python manage.py runserver
```

El backend queda disponible en `http://localhost:8000`.

### Frontend

```bash
cd frontend
pnpm install
pnpm run dev
```

El frontend queda disponible en `http://localhost:5173`.

## Variables de entorno

### Backend (`backend/.env`)

```env
DEBUG=True
SECRET_KEY="your-secret-key"
DATABASE_URL=sqlite:///db.sqlite3
```

### Frontend (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
VITE_SUPPORT_PHONE=56912345678
```

## Production security

Production environment formats, ownership, validation evidence, and release gates are documented in [Production security](docs/production-security.md). The runbook intentionally contains no secrets or assigned production API hostname.

## Regenerar tipos del API

Cuando cambien los serializers del backend:

```bash
cd frontend
pnpm run api:gen
```

Esto actualiza `src/api/schema.d.ts` a partir del schema OpenAPI del backend.

## Testing

### Backend

```bash
cd backend
pipenv run pytest --cov --cov-report=term-missing
```

### Frontend

```bash
cd frontend
pnpm run test
pnpm run build
pnpm oxlint src/
```
