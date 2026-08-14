import { createBrowserRouter, type RouteObject } from 'react-router'

import { LoginPage } from '@/features/auth'
import { RegisterPage } from '@/features/auth/pages/RegisterPage'
import { CategoryPage, HomePage, ProductDetailPage } from '@/features/catalog'
import { CheckoutPage, PendingPaymentPage } from '@/features/checkout'
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
        path: 'register',
        element: <RegisterPage />,
      },
      {
        path: 'checkout',
        element: <CheckoutPage />,
      },
      {
        path: 'checkout/payment/:orderNumber',
        element: <PendingPaymentPage />,
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
        path: 'confirmation/:orderNumber',
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
