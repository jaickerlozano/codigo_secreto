import { createBrowserRouter, Navigate, type RouteObject } from 'react-router'

import { LoginPage } from '@/features/auth'
import { HomePage } from '@/features/catalog'
import { CheckoutPage } from '@/features/checkout'

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
        path: 'checkout',
        element: <CheckoutPage />,
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
