import { createBrowserRouter, Navigate, type RouteObject } from 'react-router'

import { LoginPage } from '@/features/auth'
import { CategoryPage, HomePage, ProductDetailPage } from '@/features/catalog'
import { CheckoutPage } from '@/features/checkout'
import { ConfirmationPage } from '@/features/orders'

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
        path: 'category/:categoryId',
        element: <CategoryPage />,
      },
      {
        path: 'product/:productId',
        element: <ProductDetailPage />,
      },
      {
        path: 'confirmation',
        element: <ConfirmationPage />,
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
