import type { components } from '@/api/schema.d.ts'
import type { CartItem } from '../types'
import { mapApiProduct } from '@/features/catalog/lib/mappers'

export function mapApiCartItem(
  apiItem: components['schemas']['CartItem'],
): CartItem {
  return {
    product: mapApiProduct(apiItem.product),
    quantity: apiItem.quantity ?? 1,
    subtotal: apiItem.subtotal,
  }
}
