import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'

import { useCartStore } from '@/features/cart'

import { resetServerCart } from './handlers/cart'
import { resetContactHandlers } from './handlers/contact'
import { resetFavoritesHandlers } from './handlers/favorites'
import { resetPaymentHandlers } from './handlers/payments'
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

// jsdom does not implement these DOM APIs; Radix Select requires
// scrollIntoView on open and pointer-capture calls during pointer events.
Element.prototype.scrollIntoView = vi.fn()
Element.prototype.hasPointerCapture = vi.fn(() => false)
Element.prototype.setPointerCapture = vi.fn()
Element.prototype.releasePointerCapture = vi.fn()

export const server = setupServer(...handlers)

beforeAll(() =>
  server.listen({
    onUnhandledRequest: 'warn',
  }),
)

afterEach(() => {
  server.resetHandlers()
  resetServerCart()
  resetContactHandlers()
  resetFavoritesHandlers()
  resetPaymentHandlers()
  useCartStore.setState({ items: [], isOpen: false, mode: 'guest' })
  window.localStorage.clear()
  window.sessionStorage.clear()
})

afterAll(() => server.close())
