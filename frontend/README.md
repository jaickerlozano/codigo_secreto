# Código Secreto — Frontend

Cliente React + TypeScript + Vite para el eCommerce de bienestar íntimo.

## Flujo de desarrollo

Instalá las dependencias con `pnpm install`. Si necesitás configuración local,
copiá la plantilla ignorada sin compartirla entre Windows y WSL:

```powershell
# PowerShell
Copy-Item .env.example .env
```

```bash
# WSL/Linux Bash
cp .env.example .env
```

Después podés usar los mismos scripts en PowerShell, CMD o Bash:

```text
pnpm run dev
pnpm run test:local
pnpm run build:local
pnpm run lint
pnpm run format
pnpm run api:gen
```

`test:local` y `build:local` ejecutan Vite con `LOCAL_NO_DOTENV=1`. El build
local usa modo `development`, por lo que prueba la configuración local sin
relajar el guard de producción. `api:gen` toma `VITE_API_URL` del proceso y usa
`http://localhost:8000` cuando no está definida; el wrapper no depende de la
sintaxis de expansión de variables del shell.

El build de producción sigue exigiendo una URL HTTPS. Usá una variable del
proceso, no un archivo local:

```powershell
# PowerShell
$env:VITE_API_URL = "https://api.example.test"
pnpm run build
```

```cmd
:: CMD
set "VITE_API_URL=https://api.example.test"
pnpm run build
```

```bash
# WSL/Linux Bash
VITE_API_URL=https://api.example.test pnpm run build
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
