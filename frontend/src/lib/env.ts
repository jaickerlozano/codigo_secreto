interface EnvironmentInput {
  readonly MODE?: string
  readonly VITE_API_URL?: string
  readonly VITE_API_TIMEOUT_MS?: string
}

const DEFAULT_API_URL = 'http://localhost:8000'
const DEFAULT_API_TIMEOUT_MS = 10_000

function parseTimeout(value: string | undefined): number {
  if (value === undefined || value.trim() === '') {
    return DEFAULT_API_TIMEOUT_MS
  }

  const timeout = Number(value)

  if (!Number.isInteger(timeout) || timeout <= 0) {
    throw new Error('VITE_API_TIMEOUT_MS must be a positive integer.')
  }

  return timeout
}

function isSecureApiUrl(value: string): boolean {
  try {
    const url = new URL(value)

    return (
      url.protocol === 'https:' &&
      url.hostname !== '' &&
      !url.username &&
      !url.password
    )
  } catch {
    return false
  }
}

export function resolveEnvironment(input: EnvironmentInput) {
  const apiUrl = input.VITE_API_URL?.trim()

  if (input.MODE === 'production') {
    if (!apiUrl || !isSecureApiUrl(apiUrl)) {
      throw new Error(
        'VITE_API_URL must be a public HTTPS URL without embedded credentials in production.'
      )
    }

    return {
      API_URL: apiUrl,
      API_TIMEOUT_MS: parseTimeout(input.VITE_API_TIMEOUT_MS),
    } as const
  }

  return {
    API_URL: apiUrl || DEFAULT_API_URL,
    API_TIMEOUT_MS: parseTimeout(input.VITE_API_TIMEOUT_MS),
  } as const
}

export const env = resolveEnvironment(import.meta.env)
