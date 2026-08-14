import type { ReactNode } from 'react'; import { QueryClientProvider } from '@tanstack/react-query'; import { render, renderHook, screen, waitFor } from '@testing-library/react'; import { http, HttpResponse } from 'msw'; import { describe, expect, it, vi } from 'vitest'

import { queryClient } from '@/lib/query-client'
import { server } from '@/test/setup'

import { guestQuoteQueryKey, shouldRetryGuestQuote } from '../cart/api/quote.api'
import { useGuestQuote } from '../cart/hooks/useGuestQuote'
import { OrderSummary } from './components/OrderSummary'
import { StepReview } from './components/steps/StepReview'

const quote = { items: [{ product_id: 1, product_name: 'Producto', quantity: 1, unit_price: 10000, line_total: 10000 }], subtotal: 10000, shipping_cost: 3500, total: 13500, revision: 'gq1.current' }
const data = { contact: { name: 'Guest', email: 'guest@example.com', phone: '+56', isGuest: true }, address: { regionId: 1, regionName: 'RM', comunaId: 1, comunaName: 'Providencia', address: 'Address' }, shipping: {}, payment: { method: 'webpay' as const }, termsAccepted: true }
const Wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={queryClient()}>{children}</QueryClientProvider>

describe('PR07 quote boundary', () => {
  it('canonicalizes keys, retries only transport/5xx, and cancels obsolete quotes', async () => {
    expect(guestQuoteQueryKey({ items: [{ product_id: 2, quantity: 1 }, { product_id: 1, quantity: 2 }] })).toEqual(['guest-quote', [[1, 2], [2, 1]], null]); expect(shouldRetryGuestQuote(0, new Error('transport'))).toBe(true); expect(shouldRetryGuestQuote(0, Object.assign(new Error(), { status: 400 }))).toBe(false)
    let aborted = false; let markStarted: () => void = () => undefined; const started = new Promise<void>((resolve) => { markStarted = () => resolve() })
    server.use(http.post('http://localhost:8000/api/orders/quote/', async ({ request }) => { markStarted(); request.signal.addEventListener('abort', () => { aborted = true }); await new Promise((resolve) => setTimeout(resolve, 20)); return HttpResponse.json(quote) }))
    const { result, rerender } = renderHook(({ id }: { id: number }) => useGuestQuote({ items: [{ product_id: id, quantity: 1 }] }), { initialProps: { id: 1 }, wrapper: Wrapper }); await started; rerender({ id: 2 }); await waitFor(() => expect(result.current.data?.revision).toBe(quote.revision)); expect(aborted).toBe(true)
  })

  it('keeps confirmation gated and exposes an accessible quote retry', () => {
    const retry = vi.fn(); render(<OrderSummary cart={{ items: [], mode: 'guest', subtotal: null, shippingCost: null, total: null, quoteIsLoading: false, quoteIsError: true, quoteError: new Error('Quote unavailable'), retryQuote: retry }} />)
    expect(screen.getByRole('alert').textContent).toContain('Quote unavailable')
    screen.getByRole('button', { name: 'Reintentar cálculo' }).click()
    expect(retry).toHaveBeenCalledOnce()
    render(<StepReview data={data} subtotal={null} shippingCost={null} total={null} quoteReady={false} onEditStep={vi.fn()} onTermsChange={vi.fn()} onBack={vi.fn()} onConfirm={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Confirmar pedido' }).hasAttribute('disabled')).toBe(true)
  })
})
