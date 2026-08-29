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

## Notificaciones de cliente (`process_notifications`)

El comando `process_notifications` reintenta los correos transaccionales fallidos (pago y despacho):

```bash
pipenv run python manage.py process_notifications --batch-size 100
```

Ejecutarlo como mínimo cada 5 minutos. Ejemplo con cron:

```cron
*/5 * * * * cd /ruta/al/proyecto/backend && /usr/local/bin/pipenv run python manage.py process_notifications >> /var/log/codigo-secreto/notifications.log 2>&1
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
ExecStart=/usr/local/bin/pipenv run python manage.py process_notifications
```

### Variables de entorno SMTP (producción)

Con `DEBUG=False` el backend usa SMTP TLS; nunca cae a consola:

```bash
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=no-reply@example.com
EMAIL_HOST_PASSWORD=...
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL="Código Secreto <no-reply@example.com>"
```

En desarrollo con `DEBUG=True` y `EMAIL_HOST` vacío o ausente, los correos se imprimen en consola.

## Schema de la API

Genera el schema OpenAPI en `schema.yaml`:

```bash
pipenv run python manage.py spectacular --file schema.yaml
```
