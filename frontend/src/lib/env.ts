export const env = {
  API_URL: (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000',
  API_TIMEOUT_MS: Number(import.meta.env.VITE_API_TIMEOUT_MS ?? '10000'),
} as const
