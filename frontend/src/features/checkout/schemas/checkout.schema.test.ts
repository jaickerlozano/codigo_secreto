import { describe, expect, it } from 'vitest'

import { contactSchema } from './checkout.schema'

const validContact = {
  name: 'Juan Pérez',
  email: 'juan@example.com',
  isGuest: true,
}

describe('contactSchema phone', () => {
  it.each([
    ['912345678', '+56 9 1234 5678'],
    ['9 1234 5678', '+56 9 1234 5678'],
    ['+56912345678', '+56 9 1234 5678'],
    ['+56 9 1234 5678', '+56 9 1234 5678'],
  ])(
    'normalizes %s to the canonical Chilean mobile format',
    (phone, expected) => {
      expect(contactSchema.parse({ ...validContact, phone }).phone).toBe(
        expected
      )
    }
  )

  it.each([
    '91234567',
    '9123456789',
    '+57 9 1234 5678',
    '+56 8 1234 5678',
    '812345678',
    '9 1234 567a',
    '+56 9 1234-5678',
  ])('rejects malformed or non-Chilean mobile input: %s', (phone) => {
    expect(contactSchema.safeParse({ ...validContact, phone }).success).toBe(
      false
    )
  })
})
