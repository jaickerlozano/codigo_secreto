# Backend — Código Secreto

API REST con Django y Django REST Framework para el eCommerce.

## Setup

```bash
cd backend
pipenv install
pipenv run python manage.py migrate
pipenv run python manage.py seed_products
pipenv run python manage.py runserver
```

El servidor queda disponible en `http://localhost:8000`.

## Base de datos

Por defecto el desarrollo local usa SQLite (`DATABASE_URL=sqlite:///db.sqlite3` en `.env`).
Para producción se recomienda PostgreSQL; solo hay que ajustar `DATABASE_URL`.

## Aplicaciones

Las apps viven en `apps/` y están aisladas por dominio:

- `authentication` — usuarios, JWT vía cookies HttpOnly.
- `products` — catálogo, categorías, proveedores.
- `carts` — carro de compras.
- `shipping` — regiones, comunas y opciones de envío.
- `orders` — pedidos y su ciclo de vida.
- `payments` — gateway de pagos simulado (`MockPaymentProvider`).

## Testing

```bash
pipenv run pytest
pipenv run pytest --cov --cov-report=term-missing
```

La configuración de cobertura está en `pyproject.toml`.

## Comandos de administración

### `seed_products`

Crea o actualiza el catálogo semilla de 44 productos.

```bash
pipenv run python manage.py seed_products
```

Para recrear desde cero:

```bash
pipenv run python manage.py seed_products --reset
```

## Schema de la API

Genera el schema OpenAPI en `schema.yaml`:

```bash
pipenv run python manage.py spectacular --file schema.yaml
```
