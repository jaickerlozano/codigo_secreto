import { Link, Outlet } from 'react-router'

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-base-900 text-base-100">
      <header className="border-b border-base-700 bg-base-800/50 px-6 py-4 backdrop-blur">
        <nav className="mx-auto flex max-w-6xl items-center justify-between">
          <Link to="/" className="text-xl font-bold text-neon-cyan-500">
            Código Secreto
          </Link>
          <Link
            to="/login"
            className="rounded-md border border-neon-cyan-500 px-4 py-2 text-sm font-medium text-neon-cyan-500 transition hover:bg-neon-cyan-500/10"
          >
            Iniciar sesión
          </Link>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}
