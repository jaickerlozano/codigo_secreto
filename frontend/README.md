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
