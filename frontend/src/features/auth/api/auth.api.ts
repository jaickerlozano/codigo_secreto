import { apiClient } from '@/lib/api-client'
import type { components, paths } from '@/api/schema.d.ts'
import type {
  AuthApiError,
  LoginInput,
  LoginResponse,
  RegisterInput,
  RegisterResponse,
  UserMe,
} from '../types'

function extractErrorMessage(error: AuthApiError | undefined): string {
  if (error && typeof error === 'object') {
    if (typeof error.detail === 'string' && error.detail.length > 0) {
      return error.detail
    }
    if (typeof error.message === 'string' && error.message.length > 0) {
      return error.message
    }
  }
  return 'Ocurrió un error. Inténtalo de nuevo.'
}

export async function login(credentials: LoginInput): Promise<LoginResponse> {
  const { data, error } = await apiClient.POST('/api/auth/login/', {
    body: credentials as unknown as components['schemas']['TokenObtainPair'],
  })

  if (error || !data) {
    throw new Error(extractErrorMessage(error as AuthApiError | undefined))
  }

  return data
}

export async function registerUser(data: RegisterInput): Promise<RegisterResponse> {
  const { data: responseData, error } = await apiClient.POST('/api/auth/register/', {
    body: data,
  })

  if (error || !responseData) {
    throw new Error(extractErrorMessage(error as AuthApiError | undefined))
  }

  return responseData
}

export async function logoutUser(): Promise<
  paths['/api/auth/logout/']['post']['responses'][200]['content']['application/json']
> {
  const { data, error } = await apiClient.POST('/api/auth/logout/')

  if (error || !data) {
    throw new Error(extractErrorMessage(error as AuthApiError | undefined))
  }

  return data
}

export async function getMe(): Promise<UserMe | null> {
  const { data, error, response } = await apiClient.GET('/api/auth/me/')

  if (response.status === 401) {
    return null
  }

  if (error || !data) {
    throw new Error(extractErrorMessage(error as AuthApiError | undefined))
  }

  return data
}
