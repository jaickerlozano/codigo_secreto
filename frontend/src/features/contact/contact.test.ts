import { describe, expect, it } from 'vitest'

import { ContactSubmitError, toContactSubmitError } from './api/contact.api'
import { contactFormSchema } from './schemas/contact.schema'

const valid = { name: 'Cliente', email: 'cliente@example.com', subject: 'Consulta', body: 'Hola, tengo una consulta.' }

describe('contact schema', () => {
  it('accepts a valid message', () => {
    expect(contactFormSchema.safeParse(valid).success).toBe(true)
  })
  it('rejects every required field when empty', () => {
    const result = contactFormSchema.safeParse({ name: '', email: '', subject: '', body: '' })
    expect(result.success).toBe(false)
    if (!result.success) expect(result.error.issues.map((i) => i.path[0])).toEqual(expect.arrayContaining(['name', 'email', 'subject', 'body']))
  })
  it('rejects an invalid email', () => {
    expect(contactFormSchema.safeParse({ ...valid, email: 'no-es-email' }).success).toBe(false)
  })
  it('enforces the backend max lengths (name 120, subject 200)', () => {
    const result = contactFormSchema.safeParse({ ...valid, name: 'a'.repeat(121), subject: 'b'.repeat(201) })
    expect(result.success).toBe(false)
    if (!result.success) expect(result.error.issues.map((i) => i.path[0])).toEqual(expect.arrayContaining(['name', 'subject']))
  })
})

describe('toContactSubmitError', () => {
  it('maps DRF field validation errors to fieldMessages', () => {
    const err = toContactSubmitError({ email: ['Ingresa un email válido'], name: ['Este campo es obligatorio.'] })
    expect(err).toBeInstanceOf(ContactSubmitError)
    expect(err.fieldMessages).toEqual({ email: 'Ingresa un email válido', name: 'Este campo es obligatorio.' })
    expect(err.throttled).toBe(false)
  })
  it('maps a throttle detail response to a throttled error', () => {
    const err = toContactSubmitError({ detail: 'Demasiados intentos. Intenta nuevamente en 60 minutos.' })
    expect(err.throttled).toBe(true)
    expect(err.message).toBe('Demasiados intentos. Intenta nuevamente en 60 minutos.')
  })
  it('falls back to a generic message for unknown or non-object errors', () => {
    expect(toContactSubmitError('boom').message).toBe('No pudimos enviar tu mensaje.')
    expect(toContactSubmitError(undefined).message).toBe('No pudimos enviar tu mensaje.')
    expect(toContactSubmitError(null).message).toBe('No pudimos enviar tu mensaje.')
  })
})
