import { useMutation, useQueryClient } from '@tanstack/react-query'

import { removeFromCart, type AddToCartInput } from '../api/cart.api'

export function useRemoveFromCart() {
  const queryClient = useQueryClient()

  return useMutation<unknown, Error, AddToCartInput>({
    mutationFn: removeFromCart,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cart'] })
    },
  })
}
