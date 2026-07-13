import { useMutation, useQueryClient } from '@tanstack/react-query'

import { logoutUser } from '../api/auth.api'

export function useLogout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: logoutUser,
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ['me'] })
    },
  })
}
