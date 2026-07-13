import { describe, expect, it } from 'vitest'

import { apiClient } from '@/lib/api-client'

describe('MSW debug 2', () => {
  it('intercepts products list without query', async () => {
    const { data, error, response } = await apiClient.GET('/api/products/')
    console.log('status', response?.status)
    console.log('data', data)
    console.log('error', error)
    expect(response?.status).toBe(200)
  })
})
