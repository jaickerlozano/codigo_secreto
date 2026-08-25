import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { DispatchOptions } from '@/features/shipping/types'
import { queryClient } from '@/lib/query-client'

vi.mock('@/features/shipping/api/shipping.api', () => ({
  getDispatchOptions: vi.fn(),
}))

import { getDispatchOptions } from '@/features/shipping/api/shipping.api'

import { StepShipping } from './StepShipping'

const santiagoOptions: DispatchOptions = {
  comunaId: 1,
  mode: 'santiago',
  dates: ['2026-08-25', '2026-08-27'],
  shippingOption: null,
}
const regionalOptions: DispatchOptions = {
  comunaId: 3,
  mode: 'regional',
  dates: null,
  shippingOption: {
    shippingOptionId: 7,
    key: 'chilexpress',
    carrier: 'Chilexpress',
    minLeadDays: 2,
    maxLeadDays: 4,
  },
}

function renderShipping(
  overrides: Partial<Parameters<typeof StepShipping>[0]> = {}
) {
  const props = {
    comunaId: 1,
    destinationName: 'Santiago',
    destinationRegion: 'Región Metropolitana',
    shippingCost: 3500,
    quoteIsLoading: false,
    quoteIsError: false,
    quoteError: null,
    onRetryQuote: vi.fn(),
    selection: {},
    onSubmit: vi.fn(),
    onBack: vi.fn(),
    ...overrides,
  }
  const user = userEvent.setup()
  render(
    <QueryClientProvider client={queryClient()}>
      <StepShipping {...props} />
    </QueryClientProvider>
  )
  return { user, onSubmit: props.onSubmit as ReturnType<typeof vi.fn> }
}

const continueButton = () => screen.getByRole('button', { name: /Siguiente/ })
const isDisabled = (element: HTMLElement) => element.hasAttribute('disabled')

describe('StepShipping explicit dispatch selection', () => {
  it('renders backend Santiago dates and blocks continue until one is chosen', async () => {
    vi.mocked(getDispatchOptions).mockResolvedValue(santiagoOptions)
    const { user } = renderShipping()

    expect(
      await screen.findByRole('radio', { name: /25 de agosto/ })
    ).toBeDefined()
    expect(screen.getByRole('radio', { name: /27 de agosto/ })).toBeDefined()
    expect(isDisabled(continueButton())).toBe(true)

    await user.click(screen.getByRole('radio', { name: /25 de agosto/ }))
    expect(isDisabled(continueButton())).toBe(false)
  })

  it('submits the explicit Santiago standard selection', async () => {
    vi.mocked(getDispatchOptions).mockResolvedValue(santiagoOptions)
    const { user, onSubmit } = renderShipping()

    await user.click(await screen.findByRole('radio', { name: /25 de agosto/ }))
    await user.click(continueButton())

    expect(onSubmit).toHaveBeenCalledWith({
      deliveryKind: 'standard',
      requestedDispatchDate: '2026-08-25',
    })
  })

  it('offers a labeled special date and submits it as special delivery', async () => {
    vi.mocked(getDispatchOptions).mockResolvedValue(santiagoOptions)
    const { user, onSubmit } = renderShipping()

    await user.click(
      await screen.findByRole('radio', { name: 'Solicitar otra fecha' })
    )
    fireEvent.change(screen.getByLabelText('Fecha deseada'), {
      target: { value: '2026-09-01' },
    })

    expect(isDisabled(continueButton())).toBe(false)
    await user.click(continueButton())

    expect(onSubmit).toHaveBeenCalledWith({
      deliveryKind: 'special',
      requestedDispatchDate: '2026-09-01',
    })
  })

  it('requires explicit selection of the regional carrier card', async () => {
    vi.mocked(getDispatchOptions).mockResolvedValue(regionalOptions)
    const { user, onSubmit } = renderShipping({
      comunaId: 3,
      destinationName: 'Viña del Mar',
    })

    const card = await screen.findByRole('radio', { name: /Chilexpress/ })
    expect(screen.queryByText('$4.900')).toBeNull()
    expect(screen.getByText(/2–4 días hábiles/)).toBeDefined()
    expect(isDisabled(continueButton())).toBe(true)

    await user.click(card)
    expect(isDisabled(continueButton())).toBe(false)
    await user.click(continueButton())

    expect(onSubmit).toHaveBeenCalledWith({
      deliveryKind: 'standard',
      shippingOptionId: 7,
    })
  })

  it('renders and submits an available regional option without a dispatch profile', async () => {
    vi.mocked(getDispatchOptions).mockResolvedValue({
      comunaId: 9,
      mode: 'regional',
      dates: null,
      shippingOption: null,
    })
    const { onSubmit, user } = renderShipping({ comunaId: 9 })

    const regionalOption = await screen.findByRole('radio', {
      name: /Envío regional/,
    })
    expect(screen.getByText(/Detalles de transporte se confirmarán al despachar/)).toBeDefined()
    expect(screen.queryByText(/El envío no está disponible/)).toBeNull()
    await waitFor(() => expect(isDisabled(continueButton())).toBe(false))
    await user.click(regionalOption)
    await user.click(continueButton())
    expect(onSubmit).toHaveBeenCalledWith({ deliveryKind: 'standard' })
  })

  it('does not display stale destination labels or request dispatch without a resolved comuna', () => {
    vi.mocked(getDispatchOptions).mockClear()
    renderShipping({
      comunaId: null,
      destinationName: 'Viña del Mar',
      destinationRegion: 'Valparaíso',
    })

    expect(screen.queryByText('Viña del Mar')).toBeNull()
    expect(screen.queryByText('Valparaíso')).toBeNull()
    expect(vi.mocked(getDispatchOptions)).not.toHaveBeenCalled()
    expect(screen.getByText(/Selecciona una comuna/)).toBeDefined()
  })

  it('shows dispatch error with retry and recovers', async () => {
    vi.mocked(getDispatchOptions)
      .mockRejectedValueOnce(
        new Error('No pudimos cargar las opciones de envío.')
      )
      .mockResolvedValueOnce(santiagoOptions)
    const { user } = renderShipping()

    expect((await screen.findByRole('alert')).textContent).toContain(
      'No pudimos cargar las opciones de envío.'
    )
    expect(isDisabled(continueButton())).toBe(true)

    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(
      await screen.findByRole('radio', { name: /25 de agosto/ })
    ).toBeDefined()
  })

  it('keeps blocking and offers quote retry when the backend quote fails', async () => {
    vi.mocked(getDispatchOptions).mockResolvedValue(santiagoOptions)
    const onRetryQuote = vi.fn()
    const { user } = renderShipping({
      quoteIsError: true,
      quoteError: new Error('No pudimos calcular el costo de envío.'),
      onRetryQuote,
    })

    expect((await screen.findByRole('alert')).textContent).toContain(
      'No pudimos calcular el costo de envío.'
    )
    expect(isDisabled(continueButton())).toBe(true)

    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(onRetryQuote).toHaveBeenCalledOnce()
  })

  it('clears an invalidated selection and requires a new choice', async () => {
    vi.mocked(getDispatchOptions).mockResolvedValue({
      comunaId: 1,
      mode: 'santiago',
      dates: ['2026-08-27', '2026-08-29'],
      shippingOption: null,
    })
    renderShipping({
      selection: {
        deliveryKind: 'standard',
        requestedDispatchDate: '2026-08-25',
      },
    })

    expect(await screen.findByText(/ya no está disponible/)).toBeDefined()
    expect(isDisabled(continueButton())).toBe(true)
  })

  it('preserves a still-valid selection when returning to the step', async () => {
    vi.mocked(getDispatchOptions).mockResolvedValue(santiagoOptions)
    renderShipping({
      selection: {
        deliveryKind: 'standard',
        requestedDispatchDate: '2026-08-25',
      },
    })

    expect(
      await screen.findByRole('radio', { name: /25 de agosto/ })
    ).toBeDefined()
    expect(isDisabled(continueButton())).toBe(false)
  })

  it('confirms the step and returns via Atrás', async () => {
    vi.mocked(getDispatchOptions).mockResolvedValue(santiagoOptions)
    const onBack = vi.fn()
    const { user, onSubmit } = renderShipping({ onBack })

    await user.click(await screen.findByRole('radio', { name: /25 de agosto/ }))
    await user.click(screen.getByRole('button', { name: 'Atrás' }))
    expect(onBack).toHaveBeenCalledOnce()

    await user.click(continueButton())
    expect(onSubmit).toHaveBeenCalledOnce()
  })
})
