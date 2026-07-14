import { useMutation, useQueryClient } from '@tanstack/react-query'

import { updateCartItem, type UpdateCartItemInput } from '../api/cart.api'

export function useUpdateCartItem() {
  const queryClient = useQueryClient()

  return useMutation<unknown, Error, UpdateCartItemInput>({
    mutationFn: updateCartItem,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cart'] })
    },
  })
}
