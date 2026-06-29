import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router'

import { login } from '../api/auth.api'

export function useLogin() {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate('/', { replace: true })
    },
  })
}
