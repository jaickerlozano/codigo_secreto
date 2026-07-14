import { useQuery } from '@tanstack/react-query'

import { getCart } from '../api/cart.api'
import type { Cart } from '../api/cart.api'

export function useCartItems(options: { enabled?: boolean } = {}) {
  return useQuery<Cart, Error>({
    queryKey: ['cart'],
    queryFn: getCart,
    enabled: options.enabled,
    retry: 1,
    staleTime: 1000 * 60 * 2,
    refetchOnWindowFocus: false,
  })
}
