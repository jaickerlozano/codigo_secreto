import type { components, paths } from '@/api/schema.d.ts'

export type LoginInput = Pick<
  components['schemas']['TokenObtainPair'],
  'email' | 'password'
>

export type LoginResponse = paths['/api/auth/login/']['post']['responses'][200]['content']['application/json']

// Schema generation only emits the 200 response for this endpoint; error
// responses are not exposed by drf-spectacular, so we keep a minimal manual
// fallback to surface backend error messages to the UI.
export type LoginError = {
  detail: string
  [key: string]: unknown
}
