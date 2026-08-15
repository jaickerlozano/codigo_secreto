import type { components } from '@/api/schema.d.ts'
import { apiClient } from '@/lib/api-client'

export type ContactMessageInput = Pick<components['schemas']['ContactMessage'], 'name' | 'email' | 'subject' | 'body'>
export type ContactMessageResponse = components['schemas']['ContactMessageResponse']

export class ContactSubmitError extends Error {
  readonly fieldMessages: Record<string, string> | null
  readonly throttled: boolean
  constructor(message: string, fieldMessages: Record<string, string> | null = null, throttled = false) {
    super(message)
    this.name = 'ContactSubmitError'
    this.fieldMessages = fieldMessages
    this.throttled = throttled
  }
}

export function toContactSubmitError(error: unknown): ContactSubmitError {
  const fieldMessages: Record<string, string> = {}
  let detail: string | null = null
  if (typeof error === 'object' && error !== null) {
    for (const [key, value] of Object.entries(error)) {
      if (key === 'detail') detail = String(value)
      else if (Array.isArray(value) && value.length > 0) fieldMessages[key] = String(value[0])
    }
  }
  if (Object.keys(fieldMessages).length > 0) return new ContactSubmitError('Revisa los campos marcados.', fieldMessages)
  if (detail) return new ContactSubmitError(detail, null, true)
  return new ContactSubmitError('No pudimos enviar tu mensaje.')
}

export async function sendContactMessage(payload: ContactMessageInput): Promise<ContactMessageResponse> {
  // The generated request body type reuses the response schema whose
  // read-only fields (id/status/created_at) are required at the type level.
  const { data, error } = await apiClient.POST('/api/contact/', { body: payload as components['schemas']['ContactMessage'] })
  if (error || !data) throw toContactSubmitError(error)
  return data
}
