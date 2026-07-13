import { useMutation } from '@tanstack/react-query'

import { registerUser } from '../api/auth.api'
import type { RegisterInput } from '../types'

export function useRegister() {
  return useMutation({
    mutationFn: (data: RegisterInput) => registerUser(data),
  })
}
