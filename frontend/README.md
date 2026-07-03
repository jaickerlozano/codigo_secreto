# Código Secreto — Frontend

Cliente React + TypeScript + Vite para el eCommerce de bienestar íntimo.

## Flujo de desarrollo

```bash
# Instalar dependencias
pnpm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env según tu entorno local

# Servidor de desarrollo
pnpm run dev

# Ejecutar tests
pnpm run test

# Build de producción
pnpm run build

# Lint
pnpm run lint

# Formatear código
pnpm run format

# Generar tipos desde el esquema OpenAPI del backend
pnpm run api:gen
```

## Páginas y rutas

La aplicación usa React Router v7 con `createBrowserRouter`. Las rutas principales son:

| Ruta | Página | Descripción |
|------|--------|-------------|
| `/` | `HomePage` | Catálogo destacado, hero y beneficios |
| `/category/:categoryId` | `CategoryPage` | Listado filtrado por categoría |
| `/product/:productId` | `ProductDetailPage` | Detalle de producto |
| `/checkout` | `CheckoutPage` | Checkout en 5 pasos |
| `/confirmation` | `ConfirmationPage` | Confirmación de pedido |
| `/order/:orderId` | `OrderTrackingPage` | Seguimiento de pedido |
| `/login` | `LoginPage` | Inicio de sesión |
| `*` | `NotFoundPage` | Página 404 on-brand |

## Sistema de diseño

El frontend usa una paleta de neón sobre fondo oscuro, inspirada en la identidad de Código Secreto.

### Paleta

| Token | Valor | Uso |
|-------|-------|-----|
| `neon-magenta` | `#ff2bd6` | Color primario, CTAs, acentos |
| `neon-cyan` | `#00f0ff` | Links secundarios, badges "nuevo" |
| `neon-violet` | `#a855f7` | Gradientes, acentos |
| `neon-lime` | `#a3e635` | Éxito, envío gratis, confirmaciones |

### Tokens CSS

```css
:root {
  --gradient-brand: linear-gradient(135deg, #ff2bd6, #a855f7);
  --shadow-glow-brand: 0 0 24px rgba(255, 43, 214, 0.4);
  --circuit-overlay: url("data:image/svg+xml,...");
}
```

La hoja `src/styles/animations.css` centraliza los keyframes (`fadeIn`, `slideUp`, `pulse`, `glow`, etc.) y respeta `prefers-reduced-motion`.

## Capturas de pantalla

> _Pendiente: agregar screenshots de Home, Category, Product Detail, Checkout y Confirmation._

## Accesibilidad

- Se respetan las preferencias de `prefers-reduced-motion`.
- Todos los modales/drawers implementan trampa de foco.
- Skip link para saltar al contenido principal (`#main-content`).
- Iconos decorativos ocultos para lectores de pantalla (`aria-hidden`).

## Convención de commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/) en español:

- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `docs:` documentación
- `style:` cambios de formato/estilo sin afectar lógica
- `refactor:` refactorización de código
- `test:` tests
- `chore:` tareas de mantenimiento/configuración

Ejemplo: `feat: agregar formulario de login`
