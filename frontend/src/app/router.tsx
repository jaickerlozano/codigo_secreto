import { createBrowserRouter, Navigate, type RouteObject } from 'react-router'

import App from './App'

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: (
          <section className="rounded-xl border border-base-700 bg-base-800 p-8 text-center">
            <h1 className="mb-4 text-3xl font-bold text-neon-cyan-500">Código Secreto</h1>
            <p className="text-base-300">Bienvenido a la tienda.</p>
          </section>
        ),
      },
      {
        path: 'login',
        element: (
          <section className="mx-auto max-w-md rounded-xl border border-base-700 bg-base-800 p-8 text-center">
            <h1 className="mb-4 text-2xl font-bold text-neon-magenta-500">Iniciar sesión</h1>
            <p className="text-base-300">Formulario de login próximamente.</p>
          </section>
        ),
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]

export function createAppRouter() {
  return createBrowserRouter(routes)
}
