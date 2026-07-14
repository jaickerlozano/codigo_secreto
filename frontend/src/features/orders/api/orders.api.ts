import { apiClient } from '@/lib/api-client'
import type { components } from '@/api/schema.d.ts'

export type Order = components['schemas']['Order']

/**
 * Guest order item type.
 * The generated schema has guest_items as 'unknown', so we define the expected shape.
 */
export type GuestOrderItem = {
  product_id: number
  quantity: number
}

/**
 * CreateOrderInput extends the generated Order schema.
 * We use Pick<> to select only the fields needed for order creation.
 * guest_items is overridden with a specific type because the schema has it as 'unknown'.
 */
export type CreateOrderInput = Omit<
  Pick<
    Order,
    | 'phone'
    | 'shipping_address'
    | 'apartment_office'
    | 'payment_method'
    | 'comuna'
    | 'comuna_name'
    | 'region_name'
    | 'guest_email'
    | 'guest_name'
  >,
  'guest_items'
> & {
  guest_items?: GuestOrderItem[]
}

export function extractErrorMessage(error: unknown): string {
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
  return 'Ocurrió un error al crear el pedido. Inténtalo de nuevo.'
}

export async function createOrder(input: CreateOrderInput): Promise<Order> {
  const { data, error } = await apiClient.POST('/api/orders/', {
    body: input as Order,
  })

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return data
}

export async function getOrder(orderNumber: string): Promise<Order> {
  // The spec and the UI identify orders by the public order_number, but the
  // generated OpenAPI path still declares the parameter as {id}. The backend
  // endpoint is expected to resolve the public order_number.
  const { data, error } = await apiClient.GET('/api/orders/{id}/', {
    params: { path: { id: orderNumber as unknown as number } },
  })

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return data
}
