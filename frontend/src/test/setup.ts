import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'

import { handlers } from './handlers'

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

export const server = setupServer(...handlers)

beforeAll(() =>
  server.listen({
    onUnhandledRequest: 'error',
  }),
)

afterEach(() => server.resetHandlers())

afterAll(() => server.close())
