import { createBrowserRouter, Navigate, type RouteObject } from 'react-router'

import { LoginPage } from '@/features/auth'
import { HomePage } from '@/features/catalog'

import App from './App'

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: <HomePage />,
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
