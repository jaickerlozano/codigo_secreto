import { http, HttpResponse } from 'msw'

import type { components } from '@/api/schema.d.ts'

type Cart = components['schemas']['Cart']
type AddToCart = components['schemas']['AddToCart']

const FREE_SHIPPING_THRESHOLD = 30000
const FLAT_SHIPPING_RATE = 3000

type MutableCart = {
  -readonly [K in keyof Cart]: K extends 'items'
    ? Array<{
        -readonly [IK in keyof Cart['items'][number]]: Cart['items'][number][IK]
      }>
    : Cart[K]
}

const testProduct: components['schemas']['Product'] = {
  id: 1,
  name: 'Vibrador de prueba',
  description: 'Descripción de prueba',
  current_stock: 10,
  minimum_stock: 1,
  price: 29990,
  stock: 10,
  image: '',
  images: [],
  sku: '101',
  icon: '✦',
  gradient: 'from-violet-950 via-purple-900 to-violet-800',
  experienceLevel: 'intermedio',
  features: [],
  badge: null,
  created_at: '2026-07-09T00:00:00Z',
  updated_at: '2026-07-09T00:00:00Z',
  category: '1',
  supplier: 1,
}

function calculateCartTotals(cart: MutableCart): void {
  const subtotal = cart.items.reduce((sum, item) => sum + item.subtotal, 0)
  const shippingCost =
    subtotal === 0 ? 0 : subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : FLAT_SHIPPING_RATE
  const total = subtotal + shippingCost
  const progress =
    FREE_SHIPPING_THRESHOLD > 0
      ? Math.min((subtotal / FREE_SHIPPING_THRESHOLD) * 100, 100)
      : 0

  cart.monto_total_final = subtotal
  cart.subtotal = subtotal
  cart.shipping_cost = shippingCost
  cart.total = total
  cart.free_shipping_progress = progress
  cart.free_shipping_threshold = FREE_SHIPPING_THRESHOLD
}

let serverCart: MutableCart = {
  id: 1,
  created_at: '2026-07-09T00:00:00Z',
  updated_at: '2026-07-09T00:00:00Z',
  items: [],
  monto_total_final: 0,
  subtotal: 0,
  shipping_cost: 0,
  total: 0,
  free_shipping_progress: 0,
  free_shipping_threshold: FREE_SHIPPING_THRESHOLD,
}

export function resetServerCart(): void {
  serverCart = {
    id: 1,
    created_at: '2026-07-09T00:00:00Z',
    updated_at: '2026-07-09T00:00:00Z',
    items: [],
    monto_total_final: 0,
    subtotal: 0,
    shipping_cost: 0,
    total: 0,
    free_shipping_progress: 0,
    free_shipping_threshold: FREE_SHIPPING_THRESHOLD,
  }
}

export const cartHandlers = [
  http.get('http://localhost:8000/api/cart/me/', () => HttpResponse.json(serverCart)),

  http.post('http://localhost:8000/api/cart/me/', async ({ request }) => {
    const body = (await request.json()) as AddToCart
    const index = serverCart.items.findIndex(
      (item) => item.product.id === body.product_id,
    )

    if (index >= 0) {
      const existing = serverCart.items[index]
      const newQuantity = (existing.quantity ?? 1) + body.quantity
      serverCart.items[index] = {
        ...existing,
        quantity: newQuantity,
        subtotal: testProduct.price * newQuantity,
      }
    } else {
      serverCart.items.push({
        cart: serverCart.id,
        product: testProduct,
        quantity: body.quantity,
        subtotal: testProduct.price * body.quantity,
      })
    }

    calculateCartTotals(serverCart)
    return HttpResponse.json(serverCart, { status: 201 })
  }),

  http.delete('http://localhost:8000/api/cart/me/', async ({ request }) => {
    const body = (await request.json()) as AddToCart
    const index = serverCart.items.findIndex(
      (item) => item.product.id === body.product_id,
    )

    if (index < 0) {
      return HttpResponse.json(
        {
          detail:
            'El producto seleccionado no se encuentra en tu carrito de compras.',
        },
        { status: 400 },
      )
    }

    const existing = serverCart.items[index]
    const currentQty = existing.quantity ?? 1
    if (currentQty <= body.quantity) {
      serverCart.items = serverCart.items.filter(
        (item) => item.product.id !== body.product_id,
      )
    } else {
      const newQuantity = currentQty - body.quantity
      serverCart.items[index] = {
        ...existing,
        quantity: newQuantity,
        subtotal: testProduct.price * newQuantity,
      }
    }

    calculateCartTotals(serverCart)
    return HttpResponse.json(serverCart)
  }),
]
