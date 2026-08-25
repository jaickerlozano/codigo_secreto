import { useQuery } from '@tanstack/react-query'

import { getCart } from '../api/cart.api'
import type { Cart } from '../api/cart.api'

export function useCartItems(options: { comunaId?: number | null; enabled?: boolean } = {}) {
  const comunaId = options.comunaId ?? null

  return useQuery<Cart, Error>({
    queryKey: ['cart', comunaId],
    queryFn: () => getCart(comunaId),
    enabled: options.enabled,
    retry: 1,
    staleTime: 1000 * 60 * 2,
    refetchOnWindowFocus: false,
  })
}
