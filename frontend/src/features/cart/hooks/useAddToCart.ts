import { useMutation, useQueryClient } from '@tanstack/react-query'

import { addToCart, type AddToCartInput } from '../api/cart.api'

export function useAddToCart() {
  const queryClient = useQueryClient()

  return useMutation<unknown, Error, AddToCartInput>({
    mutationFn: addToCart,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cart'] })
    },
  })
}
