import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { DispatchOptions } from '@/features/shipping/types'
import { queryClient } from '@/lib/query-client'

vi.mock('@/features/shipping/api/shipping.api', () => ({ getDispatchOptions: vi.fn() }))

import { getDispatchOptions } from '@/features/shipping/api/shipping.api'

import { StepShipping } from './StepShipping'

const options: DispatchOptions = { comunaId: 1, mode: 'santiago', dates: ['2026-08-25'], shippingOption: null }

function renderShipping(overrides: Partial<Parameters<typeof StepShipping>[0]> = {}) {
  vi.mocked(getDispatchOptions).mockResolvedValue(options)
  const props = { comunaId: 1, destinationName: 'Providencia', destinationRegion: 'Región Metropolitana', shippingCost: 3500, quoteIsLoading: false, quoteIsError: false, quoteError: null, onRetryQuote: vi.fn(), selection: {}, onSubmit: vi.fn(), onBack: vi.fn(), ...overrides }
  const user = userEvent.setup()
  render(<QueryClientProvider client={queryClient()}><StepShipping {...props} /></QueryClientProvider>)
  return { user }
}

const continueButton = () => screen.getByRole('button', { name: /Siguiente/ })
const byExactText = (text: string) => (_: string, node: Element | null) => node?.tagName === 'P' && node.textContent === text

describe('StepShipping (backend tariff)', () => {
  it('renders the backend tariff and destination context truthfully', () => {
    renderShipping()
    expect(screen.getByRole('group', { name: 'Envío' })).toBeDefined()
    expect(screen.getByText(byExactText('Envío a Providencia, Región Metropolitana'))).toBeDefined()
    expect(screen.getByText('$3.500')).toBeDefined()
    expect(screen.getByText('Calculada por Código Secreto')).toBeDefined()
  })

  it('shows Gratis and requires an explicit dispatch selection', async () => {
    const { user } = renderShipping({ shippingCost: 0 })
    expect(screen.getByText('Gratis')).toBeDefined()
    expect(continueButton().hasAttribute('disabled')).toBe(true)
    await user.click(await screen.findByRole('radio', { name: /25 de agosto/ }))
    expect(continueButton().hasAttribute('disabled')).toBe(false)
  })

  it('shows a loading status and blocks continue while the tariff is loading', () => {
    renderShipping({ quoteIsLoading: true })
    expect(screen.getByText('Calculando el costo de envío…')).toBeDefined()
    expect(continueButton().hasAttribute('disabled')).toBe(true)
    expect(screen.queryByText('$3.500')).toBeNull()
  })

  it('shows the tariff error with retry and blocks continue', async () => {
    const onRetry = vi.fn()
    const { user } = renderShipping({ quoteIsError: true, quoteError: new Error('No pudimos calcular el costo de envío.'), onRetryQuote: onRetry })
    expect(screen.getByRole('alert').textContent).toContain('No pudimos calcular el costo de envío.')
    expect(continueButton().hasAttribute('disabled')).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('blocks continue while no tariff is available', () => {
    renderShipping({ shippingCost: null, quoteIsLoading: false, quoteIsError: false, quoteError: null })
    expect(continueButton().hasAttribute('disabled')).toBe(true)
  })

  it('confirms the step via Siguiente and returns via Atrás', async () => {
    const onSubmit = vi.fn()
    const onBack = vi.fn()
    const { user } = renderShipping({ onSubmit, onBack })
    await user.click(await screen.findByRole('radio', { name: /25 de agosto/ }))
    await user.click(continueButton())
    expect(onSubmit).toHaveBeenCalledOnce()
    await user.click(screen.getByRole('button', { name: 'Atrás' }))
    expect(onBack).toHaveBeenCalledOnce()
  })
})
