import type { QueryClient } from '@tanstack/react-query'

import { addToCart } from '../api/cart.api'
import type { CartItem } from '../types'
import { useCartStore } from '../store/cartStore'

const STORAGE_KEY = 'cs-cart'

export async function mergeOnLogin(
  guestItems: CartItem[],
  queryClient: QueryClient,
): Promise<void> {
  if (guestItems.length === 0) {
    finalizeLogin(queryClient)
    return
  }

  await Promise.all(
    guestItems.map((item) =>
      addToCart({
        product_id: item.product.id,
        quantity: item.quantity,
      }),
    ),
  )

  finalizeLogin(queryClient)
}

function finalizeLogin(queryClient: QueryClient): void {
  useCartStore.getState().setMode('authenticated')
  useCartStore.getState().clearCart()
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
  void queryClient.invalidateQueries({ queryKey: ['cart'] })
}
