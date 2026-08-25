import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { useCart, type UseCartResult } from '@/features/cart'
import { useAuth } from '@/features/auth'
import { queryClient } from '@/lib/query-client'

import { CheckoutLoadingState, CheckoutPage } from './CheckoutPage'

vi.mock('@/features/cart', () => ({ useCart: vi.fn() }))
vi.mock('@/features/auth', () => ({ useAuth: vi.fn() }))

describe('CheckoutPage', () => {
  it('announces cart loading instead of rendering a blank page', () => {
    render(<CheckoutLoadingState />)

    expect(
      screen.getByRole('status', { name: 'Cargando checkout' }),
    ).toBeDefined()
    expect(screen.getByText('Cargando checkout...')).toBeDefined()
  })

  it('keeps checkout visible and offers retry when cart loading fails', async () => {
    const retry = vi.fn().mockResolvedValue(undefined)
    vi.mocked(useCart).mockReturnValue({
      mode: 'authenticated',
      items: [],
      isLoading: false,
      error: new Error('No se pudo cargar el carrito.'),
      retry,
      addItem: vi.fn(),
      addItemWithQuantity: vi.fn(),
      removeItem: vi.fn(),
      updateQuantity: vi.fn(),
      clearCart: vi.fn(),
      totalItems: 0,
      subtotal: 0,
      shippingCost: 0,
      total: 0,
      freeShippingProgress: 0,
      freeShippingThreshold: 0,
      hasShippingDestination: false,
      quote: null,
      quoteInput: { items: [] },
      quoteIsLoading: false,
      quoteIsError: false,
      quoteError: null,
      quoteIsStale: false,
      retryQuote: vi.fn(),
    } satisfies UseCartResult)
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      authError: null,
      retryAuth: vi.fn(),
      isLoggingIn: false,
      loginError: null,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <QueryClientProvider client={queryClient()}>
        <MemoryRouter initialEntries={['/checkout']}>
          <Routes>
            <Route path="/checkout" element={<CheckoutPage />} />
            <Route path="/" element={<div>Inicio</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect((await screen.findByRole('alert')).textContent).toContain(
      'No se pudo cargar el carrito.',
    )
    expect(screen.queryByText('Inicio')).toBeNull()
    screen.getByRole('button', { name: 'Reintentar carrito' }).click()
    expect(retry).toHaveBeenCalledOnce()
  })

  it('waits for auth resolution instead of flashing guest checkout controls', () => {
    vi.mocked(useCart).mockReturnValue({
      mode: 'guest', items: [{ product: { id: 1 }, quantity: 1 }], isLoading: false, error: null,
      retry: vi.fn(), addItem: vi.fn(), addItemWithQuantity: vi.fn(), removeItem: vi.fn(), updateQuantity: vi.fn(), clearCart: vi.fn(), totalItems: 1,
      subtotal: 1000, shippingCost: 0, total: 1000, freeShippingProgress: 0, freeShippingThreshold: 0,
      quote: null, quoteInput: { items: [] }, quoteIsLoading: false, quoteIsError: false, quoteError: null, quoteIsStale: false, retryQuote: vi.fn(),
    } as unknown as UseCartResult)
    vi.mocked(useAuth).mockReturnValue({
      user: null, isAuthenticated: false, isLoading: true, authError: null, retryAuth: vi.fn(),
      isLoggingIn: false, loginError: null, login: vi.fn(), logout: vi.fn(),
    })

    render(<QueryClientProvider client={queryClient()}><MemoryRouter><CheckoutPage /></MemoryRouter></QueryClientProvider>)

    expect(screen.getByRole('status', { name: 'Cargando checkout' })).toBeDefined()
    expect(screen.queryByText('Continuar como invitado')).toBeNull()
  })
})
