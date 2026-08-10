import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'

import { useCartStore } from '@/features/cart'

import { resetServerCart } from './handlers/cart'
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
    onUnhandledRequest: 'warn',
  }),
)

afterEach(() => {
  server.resetHandlers()
  resetServerCart()
  useCartStore.setState({ items: [], isOpen: false, mode: 'guest' })
  window.localStorage.clear()
  window.sessionStorage.clear()
})

afterAll(() => server.close())
