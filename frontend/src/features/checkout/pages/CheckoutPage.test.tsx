import { QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen, waitFor } from '@testing-library/react'
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

  describe('review edit journeys with the real checkout state hook', () => {
    const savedData: CheckoutData = {
      contact: { name: 'Juan Pérez', email: 'juan@example.com', phone: '+56 9 1234 5678', isGuest: true },
      address: { regionId: 13, regionName: 'Región Metropolitana', comunaId: 1, comunaName: 'Santiago', address: 'Calle 123', apartment: '301', postalCode: '1234567', notes: 'Portería' },
      shipping: { deliveryKind: 'standard', requestedDispatchDate: '2026-08-25' },
      payment: { method: 'webpay' },
      termsAccepted: true,
    }

    async function renderJourney(authenticated: boolean) {
      const actual = await vi.importActual<typeof import('../hooks/useCheckout')>('../hooks/useCheckout')
      let state!: UseCheckoutReturn
      vi.mocked(useCheckout).mockImplementation(() => {
        state = actual.useCheckout()
        return state
      })
      vi.mocked(useAuth).mockReturnValue({
        user: authenticated ? { id: 1, first_name: 'María', last_name: 'González', email: 'maria@example.com', rut: null, phone: '+56 9 1234 5678', is_admin: false } : null,
        isAuthenticated: authenticated, isLoading: false, authError: null, retryAuth: vi.fn(),
        isLoggingIn: false, loginError: null, login: vi.fn(), logout: vi.fn(),
      })
      vi.mocked(useCart).mockReturnValue({
        mode: authenticated ? 'authenticated' : 'guest',
        items: [{ product: { id: 1, name: 'Producto disponible', gradient: '', icon: '✦', availableStock: 2 }, quantity: 1 }],
        isLoading: false, error: null, retry: vi.fn(), addItem: vi.fn(), addItemWithQuantity: vi.fn(), removeItem: vi.fn(), updateQuantity: vi.fn(), clearCart: vi.fn(), totalItems: 1,
        subtotal: 1000, shippingCost: 3500, total: 4500, freeShippingProgress: 0, freeShippingThreshold: 0, hasShippingDestination: true,
        quote: null, quoteInput: { items: [] }, quoteIsLoading: false, quoteIsError: false, quoteError: null, quoteIsStale: false, retryQuote: vi.fn(),
      } as unknown as UseCartResult)
      render(<QueryClientProvider client={queryClient()}><MemoryRouter><CheckoutPage /></MemoryRouter></QueryClientProvider>)
      act(() => {
        state.setContact(savedData.contact)
        state.setAddress(savedData.address)
        state.setShipping(savedData.shipping)
        state.setPayment(savedData.payment)
        state.setTermsAccepted(true)
        state.goToStep(4)
      })
      await waitFor(() => expect(useCart).toHaveBeenLastCalledWith({ comunaId: 1 }))
      return { user: userEvent.setup(), state: () => state }
    }

    it.each([false, true])('retains data and clears repeated edit intent before normal Back/progression (authenticated=%s)', async (authenticated) => {
      const { user, state } = await renderJourney(authenticated)
      const next = () => user.click(screen.getByRole('button', { name: /Siguiente/ }))
      const finishToReview = async () => {
        await screen.findByRole('radio', { name: /25 de agosto/ })
        await waitFor(() => expect(screen.getByRole('button', { name: /Siguiente/ })).toHaveProperty('disabled', false))
        await next()
        await next()
        expect(screen.getByRole('heading', { name: 'Revisar y confirmar' })).toBeDefined()
      }
      const scrollTo = vi.mocked(window.scrollTo)
      scrollTo.mockClear()

      await user.click(screen.getByRole('button', { name: 'Editar Dirección' }))
      expect(state().currentStep).toBe(1)
      expect(screen.queryByRole('group', { name: 'Datos de contacto' })).toBeNull()
      expect(document.activeElement).toBe(screen.getByLabelText(/Calle y número/))
      expect(screen.getByLabelText(/Calle y número/)).toHaveProperty('value', savedData.address.address)
      expect(screen.getByLabelText(/Depto/)).toHaveProperty('value', savedData.address.apartment)
      expect(screen.getByLabelText(/Notas/)).toHaveProperty('value', savedData.address.notes)
      expect(scrollTo).toHaveBeenCalledOnce()
      await next()
      expect(state().data.shipping).toEqual(savedData.shipping)
      await finishToReview()

      await user.click(screen.getByRole('button', { name: 'Editar Contacto' }))
      const contactGroup = screen.getByRole('group', { name: 'Datos de contacto' })
      expect(state().currentStep).toBe(1)
      if (authenticated) {
        expect(document.activeElement).toBe(contactGroup)
        expect(screen.getByText('maria@example.com')).toBeDefined()
        expect(screen.queryByRole('textbox')).toBeNull()
      } else {
        expect(document.activeElement).toBe(screen.getByLabelText(/Nombre completo/))
        expect(screen.getByLabelText(/Email/)).toHaveProperty('value', savedData.contact.email)
        await user.type(screen.getByLabelText(/Nombre completo/), ' Editado')
      }
      await next()
      expect(document.activeElement).toBe(screen.getByLabelText(/Calle y número/))
      await next()
      await user.click(screen.getByRole('button', { name: 'Atrás' }))
      // Normal Back chooses the original default, not the most recent edit.
      expect(screen.getByRole('group', { name: authenticated ? 'Dirección de envío' : 'Datos de contacto' })).toBeDefined()
      if (!authenticated) {
        expect(screen.getByLabelText(/Nombre completo/)).toHaveProperty('value', 'Juan Pérez Editado')
        await next()
      }
      expect(screen.getByLabelText(/Calle y número/)).toHaveProperty('value', savedData.address.address)
      await next()
      await finishToReview()

      await user.click(screen.getByRole('button', { name: 'Editar Dirección' }))
      expect(document.activeElement).toBe(screen.getByLabelText(/Calle y número/))
      await next()
      await user.click(screen.getByRole('button', { name: 'Atrás' }))
      expect(screen.getByRole('group', { name: authenticated ? 'Dirección de envío' : 'Datos de contacto' })).toBeDefined()
      if (!authenticated) await next()
      await next()
      await finishToReview()

      await user.click(screen.getByRole('button', { name: 'Editar Envío' }))
      expect(state().currentStep).toBe(2)
      expect(screen.getByRole('group', { name: 'Envío' })).toBeDefined()
      await finishToReview()
      await user.click(screen.getByRole('button', { name: 'Editar Pago' }))
      expect(state().currentStep).toBe(3)
      expect(screen.getByRole('group', { name: 'Método de pago' })).toBeDefined()
      expect(screen.getByRole('radio', { name: /Webpay/ })).toHaveProperty('checked', true)
      expect(state().data.termsAccepted).toBe(true)
      expect(useCreateOrder().mutate).not.toHaveBeenCalled()
      expect(useInitiatePayment().mutate).not.toHaveBeenCalled()
    })

    it('preserves destination/quote invalidation when an edited address changes comuna', async () => {
      const { user, state } = await renderJourney(false)
      await user.click(screen.getByRole('button', { name: 'Editar Dirección' }))
      const comuna = screen.getByLabelText(/Comuna/)
      await waitFor(() => expect(comuna).toHaveProperty('disabled', false))
      await user.click(comuna)
      await user.click(await screen.findByRole('option', { name: 'Providencia' }))
      await user.click(screen.getByRole('button', { name: /Siguiente/ }))

      expect(state().data.address.comunaId).toBe(2)
      expect(state().data.contact).toEqual(savedData.contact)
      expect(state().data.shipping).toEqual({})
      expect(state().data.payment).toEqual(savedData.payment)
      expect(useCart).toHaveBeenLastCalledWith({ comunaId: 2 })
      expect(state().currentStep).toBe(2)
    })
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
