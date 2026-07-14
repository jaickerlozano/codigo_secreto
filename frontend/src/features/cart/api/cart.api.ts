import { apiClient } from '@/lib/api-client'
import type { components } from '@/api/schema.d.ts'

export type Cart = components['schemas']['Cart']
export type AddToCartInput = components['schemas']['AddToCart']

function extractErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null) {
    if ('detail' in error && typeof error.detail === 'string') {
      return error.detail
    }
    if ('message' in error && typeof error.message === 'string') {
      return error.message
    }
  }
  return 'Ocurrió un error con el carrito. Inténtalo de nuevo.'
}

export async function getCart(): Promise<Cart> {
  const { data, error } = await apiClient.GET('/api/cart/me/')

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return data
}

export async function addToCart(input: AddToCartInput): Promise<Cart> {
  const { data, error } = await apiClient.POST('/api/cart/me/', {
    body: input,
  })

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return data
}

export async function removeFromCart(input: AddToCartInput): Promise<Cart> {
  // drf-spectacular no genera requestBody para DELETE, pero la vista lo requiere.
  const { data, error } = (await apiClient.DELETE('/api/cart/me/', {
    body: input,
  } as never)) as { data: Cart | undefined; error: unknown }

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return data
}

export interface UpdateCartItemInput {
  productId: number
  quantity: number
  currentQuantity: number
}

export async function updateCartItem({
  productId,
  quantity,
  currentQuantity,
}: UpdateCartItemInput): Promise<Cart> {
  const delta = quantity - currentQuantity

  if (delta > 0) {
    return addToCart({ product_id: productId, quantity: delta })
  }

  if (delta < 0) {
    return removeFromCart({ product_id: productId, quantity: -delta })
  }

  return getCart()
}
