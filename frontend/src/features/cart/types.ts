import type { Product } from '@/features/catalog/types'

export type CartMode = 'guest' | 'authenticated'

export interface CartItem {
  product: Product
  quantity: number
  subtotal?: number
}
