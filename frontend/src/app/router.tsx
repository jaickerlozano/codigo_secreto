import { createBrowserRouter, type RouteObject } from 'react-router'

import { LoginPage } from '@/features/auth'
import { CategoryPage, HomePage, ProductDetailPage } from '@/features/catalog'
import { CheckoutPage } from '@/features/checkout'
import { ConfirmationPage, OrderTrackingPage } from '@/features/orders'
import { NotFoundPage } from '@/pages/NotFoundPage'

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
        path: 'order/:orderId',
        element: <OrderTrackingPage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]

export function createAppRouter() {
  return createBrowserRouter(routes)
}
