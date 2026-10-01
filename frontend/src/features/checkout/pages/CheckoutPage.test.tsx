import { QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useCart, type UseCartResult } from '@/features/cart'
import { useAuth } from '@/features/auth'
import { OrderCreationError } from '@/features/orders/api/orders.api'
import { useCreateOrder } from '@/features/orders/hooks/useCreateOrder'
import { queryClient } from '@/lib/query-client'

import { useCheckout, type UseCheckoutReturn } from '../hooks/useCheckout'
import { useInitiatePayment } from '../hooks/useInitiatePayment'
import type { CheckoutData } from '../types'
import { CheckoutLoadingState, CheckoutPage } from './CheckoutPage'

vi.mock('@/features/cart', () => ({ useCart: vi.fn() }))
vi.mock('@/features/auth', () => ({ useAuth: vi.fn() }))
vi.mock('@/features/orders/hooks/useCreateOrder', () => ({ useCreateOrder: vi.fn() }))
vi.mock('../hooks/useCheckout', () => ({ useCheckout: vi.fn() }))
vi.mock('../hooks/useInitiatePayment', () => ({ useInitiatePayment: vi.fn() }))

const checkoutData: CheckoutData = {
  contact: { name: '', email: '', phone: '', isGuest: true },
  address: {
    regionId: 0,
    regionName: '',
    comunaId: 0,
    comunaName: '',
    address: '',
  },
  shipping: {},
  payment: { method: 'webpay' },
  termsAccepted: true,
}

function checkoutState(
  overrides: Partial<UseCheckoutReturn> = {},
): UseCheckoutReturn {
  return {
    currentStep: 1,
    data: checkoutData,
    setContact: vi.fn(),
    setAddress: vi.fn(),
    setShipping: vi.fn(),
    setPayment: vi.fn(),
    setTermsAccepted: vi.fn(),
    nextStep: vi.fn(),
    prevStep: vi.fn(),
    goToStep: vi.fn(),
    ...overrides,
  }
}

describe('CheckoutPage', () => {
  beforeEach(() => {
    vi.mocked(useCheckout).mockReturnValue(checkoutState())
    vi.mocked(useCreateOrder).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateOrder>)
    vi.mocked(useInitiatePayment).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useInitiatePayment>)
  })

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

  it('scrolls to the top after each checkout step transition without scrolling on mount', () => {
    const client = queryClient()
    vi.mocked(useCheckout).mockReturnValue(checkoutState({ currentStep: 1 }))
    vi.mocked(useCart).mockReturnValue({
      mode: 'authenticated',
      items: [
        {
          product: {
            id: 1,
            name: 'Producto disponible',
            gradient: '',
            icon: '✦',
            availableStock: 2,
          },
          quantity: 1,
        },
      ],
      isLoading: false,
      error: null,
      retry: vi.fn(),
      addItem: vi.fn(),
      addItemWithQuantity: vi.fn(),
      removeItem: vi.fn(),
      updateQuantity: vi.fn(),
      clearCart: vi.fn(),
      totalItems: 1,
      subtotal: 1000,
      shippingCost: 0,
      total: 1000,
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
    } as unknown as UseCartResult)
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
    const scrollTo = vi.mocked(window.scrollTo)
    scrollTo.mockClear()
    const view = render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <CheckoutPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(scrollTo).not.toHaveBeenCalled()

    vi.mocked(useCheckout).mockReturnValue(checkoutState({ currentStep: 2 }))
    view.rerender(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <CheckoutPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    expect(scrollTo).toHaveBeenCalledTimes(1)

    vi.mocked(useCheckout).mockReturnValue(checkoutState({ currentStep: 4 }))
    view.rerender(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <CheckoutPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    expect(scrollTo).toHaveBeenCalledTimes(2)
    expect(scrollTo).toHaveBeenLastCalledWith({
      top: 0,
      left: 0,
      behavior: 'smooth',
    })
  })

  it('shows an accessible inventory block for an unavailable cart item', async () => {
    vi.mocked(useCart).mockReturnValue({
      mode: 'guest',
      items: [
        {
          product: {
            id: 1,
            name: 'Producto sin stock',
            gradient: '',
            icon: '✦',
            availableStock: 0,
          },
          quantity: 1,
        },
      ],
      isLoading: false,
      error: null,
      retry: vi.fn(),
      addItem: vi.fn(),
      addItemWithQuantity: vi.fn(),
      removeItem: vi.fn(),
      updateQuantity: vi.fn(),
      clearCart: vi.fn(),
      totalItems: 1,
      subtotal: 1000,
      shippingCost: null,
      total: null,
      freeShippingProgress: 0,
      freeShippingThreshold: 0,
      hasShippingDestination: false,
      quote: null,
      quoteInput: { items: [{ product_id: 1, quantity: 1 }] },
      quoteIsLoading: false,
      quoteIsError: false,
      quoteError: null,
      quoteIsStale: false,
      retryQuote: vi.fn(),
    } as unknown as UseCartResult)
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
        <MemoryRouter>
          <CheckoutPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect((await screen.findByRole('alert')).textContent).toContain(
      'No puedes continuar con el checkout',
    )
  })

  it('handles inventory_unavailable as a recoverable inline checkout error', async () => {
    const inventoryError = new OrderCreationError(
      'Inventory unavailable.',
      409,
      'inventory_unavailable',
    )
    const mutate = vi.fn(
      (
        _input: unknown,
        options?: { onError?: (error: Error) => void },
      ) => options?.onError?.(inventoryError),
    )
    vi.mocked(useCreateOrder).mockReturnValue({
      mutate,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateOrder>)
    vi.mocked(useCheckout).mockReturnValue(
      checkoutState({ currentStep: 4 }),
    )
    vi.mocked(useCart).mockReturnValue({
      mode: 'authenticated',
      items: [
        {
          product: {
            id: 1,
            name: 'Producto disponible',
            gradient: '',
            icon: '✦',
            availableStock: 2,
          },
          quantity: 1,
        },
      ],
      isLoading: false,
      error: null,
      retry: vi.fn(),
      addItem: vi.fn(),
      addItemWithQuantity: vi.fn(),
      removeItem: vi.fn(),
      updateQuantity: vi.fn(),
      clearCart: vi.fn(),
      totalItems: 1,
      subtotal: 1000,
      shippingCost: 0,
      total: 1000,
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
    } as unknown as UseCartResult)
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
        <MemoryRouter>
          <CheckoutPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await act(async () => {
      await userEvent.click(
        screen.getByRole('button', { name: 'Confirmar pedido' }),
      )
    })

    expect(mutate).toHaveBeenCalledOnce()
    expect(screen.getByRole('alert').textContent).toContain(
      'La disponibilidad cambió mientras confirmabas el pedido',
    )
    expect(
      screen.getByRole('button', { name: 'Confirmar pedido' }),
    ).toHaveProperty('disabled', true)
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
