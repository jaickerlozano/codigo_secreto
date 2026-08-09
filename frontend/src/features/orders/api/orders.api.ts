import { apiClient } from '@/lib/api-client'
import type { components, paths } from '@/api/schema.d.ts'

export type Order = components['schemas']['Order']
export type CreateOrderInput = NonNullable<paths['/api/orders/']['post']['requestBody']>['content']['application/json']

type AccessLocation = Pick<Location, 'hash' | 'pathname' | 'search'>
type HistoryWriter = Pick<History, 'replaceState'>

const ORDER_ACCESS_PATH = '/api/orders/by-order-number/{order_number}/access/'

export function readAccessFragment(hash: string): string | undefined {
  const fragment = hash.startsWith('#') ? hash.slice(1) : hash
  const token = new URLSearchParams(fragment).get('access')
  return token || undefined
}

function cleanAccessRoute(location: AccessLocation): string {
  const search = new URLSearchParams(location.search)
  search.delete('access')
  const query = search.toString()
  return `${location.pathname}${query ? `?${query}` : ''}`
}

export async function exchangeOrderAccess(
  orderNumber: string,
  capability: string
): Promise<void> {
  const { error } = await apiClient.POST(ORDER_ACCESS_PATH, {
    params: {
      header: { 'X-Order-Capability': capability },
      path: { order_number: orderNumber },
    },
  })

  if (error) {
    throw new Error(
      extractErrorMessage(error, 'No se pudo validar el enlace del pedido.')
    )
  }
}

export async function exchangeOrderAccessFromLocation(
  orderNumber: string,
  location: AccessLocation = globalThis.location,
  history: HistoryWriter = globalThis.history
): Promise<boolean> {
  const capability = readAccessFragment(location.hash)
  if (!capability) return false

  await exchangeOrderAccess(orderNumber, capability)
  history.replaceState(null, '', cleanAccessRoute(location))
  return true
}

export function extractErrorMessage(
  error: unknown,
  fallback = 'Ocurrió un error al crear el pedido. Inténtalo de nuevo.'
): string {
  if (typeof error === 'object' && error !== null) {
    if ('detail' in error && typeof error.detail === 'string') {
      return error.detail
    }
    if ('message' in error && typeof error.message === 'string') {
      return error.message
    }
    const messages = Object.values(error).flat()
    if (messages.length > 0 && typeof messages[0] === 'string') {
      return messages[0]
    }
  }
  return fallback
}

export async function createOrder(input: CreateOrderInput): Promise<Order> {
  const { data, error } = await apiClient.POST('/api/orders/', {
    body: input,
  })

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return data
}

export async function getOrderByNumber(orderNumber: string): Promise<Order> {
  const { data, error } = await apiClient.GET(
    '/api/orders/by-order-number/{order_number}/',
    {
      params: { path: { order_number: orderNumber } },
    }
  )

  if (error || !data) {
    throw new Error(extractErrorMessage(error) || 'Pedido no encontrado.')
  }

  return data
}
