import { describe, expect, it } from 'vitest'

import { apiClient } from './api-client'
import { queryClient } from './query-client'

describe('apiClient', () => {
  it('is frozen to prevent accidental mutation', () => {
    expect(Object.isFrozen(apiClient)).toBe(true)
  })
})

describe('queryClient', () => {
  it('returns a new QueryClient instance', () => {
    const client = queryClient()

    expect(client).toBeDefined()
    expect(client.getQueryCache()).toBeDefined()
  })
})
