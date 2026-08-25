import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { server } from '@/test/setup'

import { updateProfilePhone } from './auth.api'

describe('updateProfilePhone', () => {
  it('uses the generated PATCH contract and returns the refreshed account', async () => {
    server.use(http.patch('http://localhost:8000/api/auth/me/phone/', async ({ request }) => {
      expect(await request.json()).toEqual({ phone: '+56 9 1234 5678' })
      return HttpResponse.json({
        id: 1, first_name: 'María', last_name: 'González', email: 'maria@example.com',
        rut: null, phone: '+56 9 1234 5678', is_admin: false,
      })
    }))

    await expect(updateProfilePhone({ phone: '+56 9 1234 5678' })).resolves.toMatchObject({
      phone: '+56 9 1234 5678',
    })
  })
})
