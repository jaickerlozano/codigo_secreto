import type { components, paths } from '@/api/schema.d.ts'

export type LoginInput = Pick<
  components['schemas']['TokenObtainPair'],
  'email' | 'password'
>

export type LoginResponse =
  paths['/api/auth/login/']['post']['responses'][200]['content']['application/json']

export type RegisterInput = components['schemas']['Register']

export type RegisterResponse =
  paths['/api/auth/register/']['post']['responses'][201]['content']['application/json']

export type UserMe = components['schemas']['UserMe']

// Schema generation only emits the 200 response for these endpoints; error
// responses are not exposed by drf-spectacular, so we keep a minimal manual
// fallback to surface backend error messages to the UI.
export type AuthApiError = {
  detail?: string
  message?: string
  [key: string]: unknown
}
