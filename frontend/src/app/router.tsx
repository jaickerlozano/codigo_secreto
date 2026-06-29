import { createBrowserRouter, Navigate, type RouteObject } from 'react-router'

import { LoginPage } from '@/features/auth'

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
        element: <LoginPage />,
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
