import { apiClient } from '@/lib/api-client'
import type { LoginInput, LoginResponse } from '../types'

function extractErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'detail' in error && typeof error.detail === 'string') {
    return error.detail
  }
  return 'Error al iniciar sesión. Inténtalo de nuevo.'
}

export async function login(credentials: LoginInput): Promise<LoginResponse> {
  const { data, error } = await apiClient.POST('/api/auth/login/', {
    body: credentials,
  })

  if (error || !data) {
    throw new Error(extractErrorMessage(error))
  }

  return data
}
