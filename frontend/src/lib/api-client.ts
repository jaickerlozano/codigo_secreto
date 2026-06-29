import createClient from 'openapi-fetch'

import type { paths } from '@/api/schema.d.ts'

import { csrfMiddleware } from './csrf'
import { env } from './env'

const client = createClient<paths>({
  baseUrl: env.API_URL,
  credentials: 'include',
})

client.use(csrfMiddleware)

export const apiClient = Object.freeze(client)
