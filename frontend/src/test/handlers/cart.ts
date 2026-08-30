import { http, HttpResponse } from 'msw'

import type { components } from '@/api/schema.d.ts'

type Cart = components['schemas']['Cart']
type AddToCart = components['schemas']['AddToCart']

const FREE_SHIPPING_THRESHOLD = 30000

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
  image_original: '',
  images: [],
  sku: '101',
  icon: '✦',
  gradient: 'from-violet-950 via-purple-900 to-violet-800',
  experience_level: 3,
  features: [],
  badge: null,
  created_at: '2026-07-09T00:00:00Z',
  updated_at: '2026-07-09T00:00:00Z',
  category: 1,
  supplier: 1,
}

function applyServerCartContract(cart: MutableCart): void {
  Object.assign(
    cart,
    cart.items.length === 0
      ? {
          monto_total_final: 0,
          subtotal: 0,
          shipping_cost: 0,
          total: 0,
          free_shipping_progress: 0,
          free_shipping_threshold: FREE_SHIPPING_THRESHOLD,
        }
      : {
          monto_total_final: 29990,
          subtotal: 29990,
          shipping_cost: 0,
          total: 29990,
          free_shipping_progress: 99.97,
          free_shipping_threshold: FREE_SHIPPING_THRESHOLD,
        },
  )
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
  free_shipping_threshold: 30000,
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
  http.get('http://localhost:8000/api/cart/me/', () =>
    HttpResponse.json(serverCart)
  ),

  http.post('http://localhost:8000/api/cart/me/', async ({ request }) => {
    const body = (await request.json()) as AddToCart
    const index = serverCart.items.findIndex(
      (item) => item.product.id === body.product_id
    )

    if (index >= 0) {
      const existing = serverCart.items[index]
      const newQuantity = (existing.quantity ?? 1) + body.quantity
      serverCart.items[index] = {
        ...existing,
        quantity: newQuantity,
        subtotal: 29990,
      }
    } else {
      serverCart.items.push({
        cart: serverCart.id,
        product: testProduct,
        quantity: body.quantity,
        subtotal: 29990,
      })
    }

    applyServerCartContract(serverCart)
    return HttpResponse.json(serverCart, { status: 201 })
  }),

  http.delete('http://localhost:8000/api/cart/me/', ({ request }) => {
    const url = new URL(request.url)
    const productId = Number(url.searchParams.get('product_id'))
    const quantity = Number(url.searchParams.get('quantity'))
    const index = serverCart.items.findIndex(
      (item) => item.product.id === productId
    )

    if (index < 0) {
      return HttpResponse.json(
        {
          detail:
            'El producto seleccionado no se encuentra en tu carrito de compras.',
        },
        { status: 400 }
      )
    }

    const existing = serverCart.items[index]
    const currentQty = existing.quantity ?? 1
    if (currentQty <= quantity) {
      serverCart.items = serverCart.items.filter(
        (item) => item.product.id !== productId
      )
    } else {
      const newQuantity = currentQty - quantity
      serverCart.items[index] = {
        ...existing,
        quantity: newQuantity,
        subtotal: 29990,
      }
    }

    applyServerCartContract(serverCart)
    return HttpResponse.json(serverCart)
  }),
]
