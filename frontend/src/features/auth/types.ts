import type { paths } from '@/api/schema.d.ts'

export type LoginInput = paths['/api/auth/login/']['post']['requestBody']['content']['application/json']
export type LoginResponse = paths['/api/auth/login/']['post']['responses'][200]['content']['application/json']
export type LoginError = paths['/api/auth/login/']['post']['responses'][400]['content']['application/json']
