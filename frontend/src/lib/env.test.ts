import { describe, expect, it } from 'vitest'

import { resolveEnvironment } from './env'

describe('resolveEnvironment', () => {
  it.each([
    [
      'accepts a complete HTTPS production configuration',
      {
        MODE: 'production',
        VITE_API_URL: 'https://api.example.test',
        VITE_API_TIMEOUT_MS: '15000',
      },
      {
        API_URL: 'https://api.example.test',
        API_TIMEOUT_MS: 15000,
      },
    ],
    [
      'preserves the local fallback in development',
      {
        MODE: 'development',
      },
      {
        API_URL: 'http://localhost:8000',
        API_TIMEOUT_MS: 10000,
      },
    ],
    [
      'preserves the local fallback in test mode',
      {
        MODE: 'test',
        VITE_API_TIMEOUT_MS: '2500',
      },
      {
        API_URL: 'http://localhost:8000',
        API_TIMEOUT_MS: 2500,
      },
    ],
  ])('%s', (_description, input, expected) => {
    expect(resolveEnvironment(input)).toEqual(expected)
  })

  it.each([
    [
      'is missing',
      {
        MODE: 'production',
        VITE_API_TIMEOUT_MS: '10000',
      },
    ],
    [
      'uses HTTP',
      {
        MODE: 'production',
        VITE_API_URL: 'http://api.example.test',
        VITE_API_TIMEOUT_MS: '10000',
      },
    ],
  ])('rejects a production API URL that %s', (_description, input) => {
    expect(() => resolveEnvironment(input)).toThrow('VITE_API_URL')
  })

  it.each(['0', '-1', 'not-a-number'])(
    'rejects an invalid timeout of %s',
    (timeout) => {
      expect(() =>
        resolveEnvironment({
          MODE: 'production',
          VITE_API_URL: 'https://api.example.test',
          VITE_API_TIMEOUT_MS: timeout,
        })
      ).toThrow('VITE_API_TIMEOUT_MS')
    }
  )
})
